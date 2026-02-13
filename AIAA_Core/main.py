import logging
import sys

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from src.config import Config
from src.bot.handlers import start_command, handle_text_message, handle_button_click

# 1. Setup Logging - ONLY show INFO for our app, WARNING for libraries
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
# Silence the noisy libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    print("========================================")
    print("🚀  AIAA AGENT - STARTING UP")
    print("========================================")

    try:
        # 2. Validate Config
        Config.validate()
        print(f"✅ Configuration Loaded.")
        print(f"🤖 Bot Token: {Config.TELEGRAM_TOKEN[:5]}******")
        print(f"🧠 AI Model: {Config.OLLAMA_MODEL}")
        print(f"🔗 API URL: {Config.API_BASE_URL}")

        # 3. Build Bot Application
        application = ApplicationBuilder().token(Config.TELEGRAM_TOKEN).build()
        
        # 4. Register Handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CallbackQueryHandler(handle_button_click)) 
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text_message))
        
        print("🟢 Bot is polling... (Go to Telegram)")
        
        # 5. Run
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Critical Startup Error: {e}")
        print("\n❌ CRITICAL ERROR: See log above.")
        input("Press Enter to close...")