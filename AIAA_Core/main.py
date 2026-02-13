import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from src.config import Config
from src.bot.handlers import start_command, handle_text_message

# Setup Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

if __name__ == '__main__':
    # Validate Environment
    Config.validate()
    
    print("🚀 Starting AIAA Agent...")
    
    # Build Bot Application
    application = ApplicationBuilder().token(Config.TELEGRAM_TOKEN).build()
    
    # Register Handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text_message))
    
    # Run
    application.run_polling()
