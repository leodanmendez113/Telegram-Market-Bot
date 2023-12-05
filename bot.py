from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters, ConversationHandler, PicklePersistence, CallbackQueryHandler
import sqlite3
from datetime import datetime, timedelta

# Configuración del bot y token (reemplaza 'TU_TOKEN_DE_TELEGRAM' con tu token real)
TOKEN = "TU_TOKEN_DE_TELEGRAM"
updater = Updater(token=TOKEN, persistence=PicklePersistence(filename='campaign_bot_data.pickle'))
dispatcher = updater.dispatcher

# Configuración de la base de datos SQLite
conn = sqlite3.connect('campaigns.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS campaigns (
        id INTEGER PRIMARY KEY,
        chat_id INTEGER,
        message TEXT,
        interval_minutes INTEGER,
        limit_date TEXT,
        admin_id INTEGER,
        moderators TEXT,
        sent_count INTEGER DEFAULT 0,
        like_count INTEGER DEFAULT 0,
        dislike_count INTEGER DEFAULT 0,
        photo_id TEXT,
        description TEXT,
        username TEXT
    )
''')
conn.commit()

# Estados para el manejo de la conversación
GROUP, PHOTO, DESCRIPTION, USERNAME, SCHEDULE, LIMIT_DATE = range(6)

# Comandos del bot

# Comando de inicio
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("¡Hola! Soy el bot de campañas publicitarias. Puedes usar /new_campaign para crear una nueva campaña.")

# Comando para iniciar una nueva campaña
def new_campaign(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Por favor, proporciona el ID del grupo o canal al que enviar la campaña.')
    return GROUP

# Guardar el ID del grupo y pasar al siguiente estado
def save_group(update: Update, context: CallbackContext) -> int:
    group_id = update.message.text
    context.user_data['group_id'] = int(group_id)
    update.message.reply_text('Perfecto. Ahora, por favor, utiliza el comando /set_campaign_photo para establecer la foto de la campaña.')
    return PHOTO

# Nuevo estado para establecer la foto de la campaña
def set_campaign_photo(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Por favor, envía la foto para la campaña.')
    return PHOTO

# Guardar la foto y pasar al siguiente estado
def save_campaign_photo(update: Update, context: CallbackContext) -> int:
    photo_file = update.message.photo[-1].file_id
    context.user_data['photo_id'] = photo_file
    update.message.reply_text('Ahora, por favor, proporciona el texto descriptivo para la campaña.')
    return DESCRIPTION

# Guardar la descripción y pasar al siguiente estado
def save_campaign_description(update: Update, context: CallbackContext) -> int:
    description = update.message.text
    context.user_data['description'] = description
    update.message.reply_text('Por último, proporciona el nombre de usuario al que se refiere la campaña.')
    return USERNAME

# Guardar el nombre de usuario y pasar al siguiente estado
def save_campaign_username(update: Update, context: CallbackContext) -> int:
    username = update.message.text
    context.user_data['username'] = username
    update.message.reply_text('Campaña configurada exitosamente. ¿Deseas programar la campaña? (Sí/No)')
    return SCHEDULE

# Nuevo estado para programar la campaña
def schedule_campaign(update: Update, context: CallbackContext) -> int:
    response = update.message.text.lower()
    if response == 'sí':
        update.message.reply_text('Por favor, proporciona la fecha límite para la campaña (formato: YYYY-MM-DD HH:mm).')
        return LIMIT_DATE
    else:
        context.user_data['limit_date'] = None
        context.user_data['scheduled'] = True
        update.message.reply_text('Campaña configurada exitosamente.')
        return ConversationHandler.END

# Guardar la fecha límite y finalizar la conversación
def save_limit_date(update: Update, context: CallbackContext) -> int:
    limit_date_str = update.message.text
    try:
        limit_date = datetime.strptime(limit_date_str, '%Y-%m-%d %H:%M')
        context.user_data['limit_date'] = limit_date
        context.user_data['scheduled'] = True
        update.message.reply_text('Campaña configurada exitosamente.')
    except ValueError:
        update.message.reply_text('Formato de fecha incorrecto. Utiliza el formato: YYYY-MM-DD HH:mm.')
    return ConversationHandler.END

# Comando para cancelar la configuración de la campaña
def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Configuración de la campaña cancelada.')
    return ConversationHandler.END

# Función para enviar mensajes de la campaña con foto y descripción
def send_campaign_messages(context: CallbackContext) -> None:
    now = datetime.now()
    campaigns = cursor.execute('SELECT * FROM campaigns WHERE limit_date > ?',
                              (now.strftime('%Y-%m-%d %H:%M'),)).fetchall()
    for campaign in campaigns:
        remaining_time = (campaign[4] - now).total_seconds()
        if remaining_time <= 0:
            # Crear mensaje único con foto, descripción, botón de contacto y botones de contador
            media = InputMediaPhoto(media=campaign[11], caption=f"{campaign[2]}\n\nUsuario referido: {campaign[12]}",
                                    parse_mode='Markdown')
            keyboard = [[InlineKeyboardButton("Like 👍", callback_data=f'like_{campaign[0]}'),
                         InlineKeyboardButton("Dislike 👎", callback_data=f'dislike_{campaign[0]}')],
                        [InlineKeyboardButton("Contactar", url=f"https://t.me/{campaign[12]}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            context.bot.send_media_group(chat_id=campaign[1], media=[media], reply_markup=reply_markup)
            cursor.execute('UPDATE campaigns SET sent_count = sent_count + 1 WHERE id = ?', (campaign[0],))
            conn.commit()

# Nueva función para manejar la retroalimentación (like o dislike)
def handle_feedback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    feedback_type, campaign_id = query.data.split('_')
    cursor.execute(f'UPDATE campaigns SET {feedback_type}_count = {feedback_type}_count + 1 WHERE id = ?', (int(campaign_id),))
    conn.commit()
    query.answer(f'Tu {feedback_type} ha sido registrado. ¡Gracias!')

# Configurar manejadores de comandos
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('new_campaign', new_campaign))
dispatcher.add_handler(CommandHandler('cancel', cancel))

# Configurar manejadores para campañas
dispatcher.add_handler(ConversationHandler(
    entry_points=[CommandHandler('new_campaign', new_campaign)],
    states={
        GROUP: [MessageHandler(Filters.text & ~Filters.command, save_group)],
        PHOTO: [MessageHandler(Filters.photo & ~Filters.command, save_campaign_photo)],
        DESCRIPTION: [MessageHandler(Filters.text & ~Filters.command, save_campaign_description)],
        USERNAME: [MessageHandler(Filters.text & ~Filters.command, save_campaign_username)],
        SCHEDULE: [MessageHandler(Filters.text & ~Filters.command, schedule_campaign)],
        LIMIT_DATE: [MessageHandler(Filters.text & ~Filters.command, save_limit_date)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
))

# Configurar manejadores para retroalimentación (like o dislike)
dispatcher.add_handler(CallbackQueryHandler(handle_feedback, pattern='^(like|dislike)_\d+$'))

# Tarea programada para enviar campañas
updater.job_queue.run_repeating(send_campaign_messages, interval=60, first=0)

# Iniciar el bot
updater.start_polling()
updater.idle()
