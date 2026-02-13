import sys
import traceback
import os
import logging

# Setup basic logging immediately to catch startup errors
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    print("🚀 Initializing AIAA Agent...")
    print(f"📂 Current Working Directory: {os.getcwd()}")
    
    # 1. Test Imports (Common failure point)
    try:
        print("   Checking libraries...")
        import telegram
        import ollama
        import dotenv
        print("   ✅ Libraries found.")
    except ImportError as e:
        print("\n❌ CRITICAL ERROR: Library Missing!")
        print(f"   Missing Module: {e.name}")
        print("   Please run: pip install python-telegram-bot ollama python-dotenv requests")
        input("\nPress Enter to exit...")
        return

    # 2. Test Import Local Modules (Checks file structure)
    try:
        print("   Importing internal modules...")
        from src.config import Config
        from src.bot.handlers import start_command, handle_text_message
        from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
        print("   ✅ Internal modules found.")
    except ImportError as e:
        print(f"\n❌ CRITICAL ERROR: Code Structure Issue!")
        print(f"   Error: {e}")
        print("   Ensure your folder structure matches:")
        print("   AIAA_Core/")
        print("      main.py")
        print("      src/")
        print("         config.py")
        print("         __init__.py")
        input("\nPress Enter to exit...")
        return

    # 3. Validate Configuration (Checks .env)
    try:
        print("   Loading configuration...")
        Config.validate()
        print("   ✅ Configuration valid.")
    except ValueError as e:
        print(f"\n❌ CONFIGURATION ERROR: {e}")
        print("   Please check your .env file.")
        input("\nPress Enter to exit...")
        return

    # 4. Start the Bot
    try:
        print(f"🤖 Starting Bot with Token: {Config.TELEGRAM_TOKEN[:5]}...")
        application = ApplicationBuilder().token(Config.TELEGRAM_TOKEN).build()
        
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text_message))
        
        print("✅ Bot is polling! (Send a message on Telegram)")
        application.run_polling()
        
    except Exception as e:
        print(f"\n❌ RUNTIME ERROR: {e}")
        traceback.print_exc()
        input("\nPress Enter to exit...")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print("Fatal crash:")
        traceback.print_exc()
        input("Press Enter to exit...")