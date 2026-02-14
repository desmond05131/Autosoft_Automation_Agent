import logging
import sys

from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler, 
    filters,
    ConversationHandler
)
from src.config import Config
# Import the new invoice flow handlers
from src.bot.handlers import (
    start_command, 
    handle_text_message, 
    handle_button_click,
    start_invoice_flow,
    receive_debtor,
    receive_item,
    receive_qty,
    complete_invoice,
    cancel_invoice,
    INVOICE_DEBTOR,
    INVOICE_ITEM,
    INVOICE_QTY,
    INVOICE_CONFIRM
)

# 1. Setup Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
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
        
        # 4. Define Conversation Handler for Invoices
        invoice_conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(start_invoice_flow, pattern='^btn_create_invoice$')],
            states={
                INVOICE_DEBTOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_debtor)],
                INVOICE_ITEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_item)],
                INVOICE_QTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_qty)],
                INVOICE_CONFIRM: [CallbackQueryHandler(complete_invoice, pattern='^inv_confirm_')]
            },
            fallbacks=[CommandHandler("cancel", cancel_invoice)]
        )

        # 5. Register Handlers
        # IMPORTANT: Add ConversationHandler FIRST so it captures text during the flow
        application.add_handler(invoice_conv_handler)
        
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CallbackQueryHandler(handle_button_click)) 
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text_message))
        
        print("🟢 Bot is polling... (Go to Telegram)")
        
        # 6. Run
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Critical Startup Error: {e}")
        print("\n❌ CRITICAL ERROR: See log above.")
        input("Press Enter to close...")