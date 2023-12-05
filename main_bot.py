from telegram.ext import Updater, PicklePersistence
from destinations import destination_conversation_handler
from database import get_destinations, add_destination_to_db, delete_destination_from_db

TOKEN = "TU_TOKEN_DE_TELEGRAM"
updater = Updater(token=TOKEN, persistence=PicklePersistence(filename='campaign_bot_data.pickle'))
dispatcher = updater.dispatcher

# Configuración de la base de datos SQLite (puedes mover esto a database.py si prefieres)
# ...

# Resto del código del bot

# ...

# Configurar manejadores para el menú de administración de destinos
dispatcher.add_handler(destination_conversation_handler)

# Resto del código del bot

# ...

updater.start_polling()
updater.idle()