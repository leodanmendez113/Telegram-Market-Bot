from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CallbackContext, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from database import get_destinations, add_destination_to_db, delete_destination_from_db

MANAGE_DESTINATIONS, ADD_DESTINATION, DELETE_DESTINATION = range(8, 11)

def manage_destinations(update: Update, context: CallbackContext) -> int:
    keyboard = [
        [InlineKeyboardButton("Agregar Destino", callback_data='add_destination')],
        [InlineKeyboardButton("Listar Destinos", callback_data='list_destinations')],
        [InlineKeyboardButton("Eliminar Destino", callback_data='delete_destination')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Selecciona una opción:', reply_markup=reply_markup)
    return MANAGE_DESTINATIONS

def handle_destination_selection(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    destination_action = query.data

    if destination_action == 'add_destination':
        update.message.reply_text('Por favor, proporciona el ID del grupo o canal que deseas agregar como destino.')
        return ADD_DESTINATION
    elif destination_action == 'list_destinations':
        destinations = get_destinations()
        if destinations:
            update.message.reply_text(f"Destinos actuales:\n{', '.join(destinations)}")
        else:
            update.message.reply_text("No hay destinos configurados.")
    elif destination_action == 'delete_destination':
        update.message.reply_text('Por favor, proporciona el ID del grupo o canal que deseas eliminar como destino.')
        return DELETE_DESTINATION

    return ConversationHandler.END

def add_destination(update: Update, context: CallbackContext) -> int:
    destination_id = update.message.text
    add_destination_to_db(destination_id)
    update.message.reply_text(f"Destino {destination_id} agregado exitosamente.")
    return ConversationHandler.END

def delete_destination(update: Update, context: CallbackContext) -> int:
    destination_id = update.message.text
    delete_destination_from_db(destination_id)
    update.message.reply_text(f"Destino {destination_id} eliminado exitosamente.")
    return ConversationHandler.END

destination_conversation_handler = ConversationHandler(
    entry_points=[CommandHandler('manage_destinations', manage_destinations)],
    states={
        MANAGE_DESTINATIONS: [CallbackQueryHandler(handle_destination_selection, pattern='^(add_destination|list_destinations|delete_destination)$')],
        ADD_DESTINATION: [MessageHandler(Filters.text & ~Filters.command, add_destination)],
        DELETE_DESTINATION: [MessageHandler(Filters.text & ~Filters.command, delete_destination)],
    },
    fallbacks=[],
)
