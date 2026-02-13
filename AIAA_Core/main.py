import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from src.config import Config
from src.bot.handlers import start_command, handle_text_message, handle_button_click

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    print("========================================")
    print("🚀  AIAA AGENT - STARTING UP")
    print("========================================")

    try:
        Config.validate()
        print(f"✅ Configuration Loaded. Bot Token: {Config.TELEGRAM_TOKEN[:5]}******")

        application = ApplicationBuilder().token(Config.TELEGRAM_TOKEN).build()
        
        # --- HANDLERS ---
        application.add_handler(CommandHandler("start", start_command))
        # Add this line for buttons:
        application.add_handler(CallbackQueryHandler(handle_button_click)) 
        # Add this line for text:
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text_message))
        
        print("🟢 Bot is polling... (Go to Telegram)")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Critical Startup Error: {e}")