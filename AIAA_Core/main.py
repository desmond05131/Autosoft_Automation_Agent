import logging
import sys

# 1. Standard Imports (Must be at the top)
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from src.config import Config
from src.bot.handlers import start_command, handle_text_message

# 2. Setup Logging
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
        # 3. Validate Config
        Config.validate()
        print(f"✅ Configuration Loaded. Bot Token: {Config.TELEGRAM_TOKEN[:5]}******")

        # 4. Build Bot Application
        application = ApplicationBuilder().token(Config.TELEGRAM_TOKEN).build()
        
        # 5. Register Handlers
        # Command: /start
        application.add_handler(CommandHandler("start", start_command))
        
        # Messages: Any text that is NOT a command
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text_message))
        
        print("🟢 Bot is polling... (Go to Telegram and type /start)")
        print("(Press Ctrl+C in this window to stop)")
        
        # 6. Run
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Critical Startup Error: {e}")
        print("\n❌ CRITICAL ERROR: See log above.")
        input("Press Enter to close...")