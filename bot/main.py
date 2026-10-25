from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from config import config
from bot.handlers import (
    cmd_start, cmd_status, cmd_inventario, cmd_keto, cmd_pausar, cmd_posponer, cmd_reportesemanal,
    handle_callback_query, handle_voice_message, handle_text_message
)

def create_telegram_app():
    """Crea e inicializa la aplicación de Telegram Bot."""
    token = config.TELEGRAM_BOT_TOKEN
    if not token or "TU_TELEGRAM" in token:
        print("[WARNING]: Telegram Bot Token no configurado en .env. El bot correrá en modo simulación.")
        return None

    app = ApplicationBuilder().token(token).build()

    # Comandos
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("inventario", cmd_inventario))
    app.add_handler(CommandHandler("keto", cmd_keto))
    app.add_handler(CommandHandler("pausar", cmd_pausar))
    app.add_handler(CommandHandler("posponer", cmd_posponer))
    app.add_handler(CommandHandler("reportesemanal", cmd_reportesemanal))


    # Callback Query (Botones)
    app.add_handler(CallbackQueryHandler(handle_callback_query))

    # Mensajes de texto libres (Atendidos por la IA de Gemini)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    # Notas de voz (Audio)
    app.add_handler(MessageHandler(filters.VOICE, handle_voice_message))

    return app

