import logging
import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from src.config import Config
from src.bot.handlers import start_command, handle_text_message

# 1. Setup Logging
# This ensures you see errors and info in the black console window
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    try:
        # 2. Validate Environment Variables
        print("⚙️ Loading Configuration...")
        Config.validate()
        print("✅ Configuration Loaded Successfully.")

        print("🚀 Starting AIAA Agent...")
        print("   (Press Ctrl+C to stop)")

        # 3. Build Bot Application
        application = ApplicationBuilder().token(Config.TELEGRAM_TOKEN).build()
        
        # 4. Register Handlers (The commands the bot understands)
        # /start command
        application.add_handler(CommandHandler("start", start_command))
        
        # All other text messages
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text_message))
        
        # 5. Run the Bot
        application.run_polling()
        
    except ValueError as e:
        logger.error(f"Configuration Error: {e}")
        input("❌ Configuration failed. Press Enter to exit...")
    except Exception as e:
        logger.error(f"Critical Error: {e}")
        # This input() keeps the window open if it crashes so you can read the error
        input("❌ An error occurred. Press Enter to exit...")