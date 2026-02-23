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
from src.bot.handlers import (
    start_command, 
    handle_text_message, 
    handle_button_click,
    start_invoice_flow, receive_debtor, receive_item, receive_qty, complete_invoice, cancel_invoice, cancel_invoice_inline,
    INVOICE_DEBTOR, INVOICE_ITEM, INVOICE_QTY, INVOICE_CONFIRM,
    start_debtor_flow, receive_debtor_name, receive_debtor_phone, complete_debtor,
    DEBTOR_NAME, DEBTOR_PHONE, DEBTOR_CONFIRM
)

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
        Config.validate()
        application = ApplicationBuilder().token(Config.TELEGRAM_TOKEN).build()
        
        # --- REGISTER INVOICE WIZARD ---
        invoice_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(start_invoice_flow, pattern='^btn_create_invoice$')],
            states={
                # Allow text input OR clicking the inline buttons generated during the flow
                INVOICE_DEBTOR: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_debtor),
                    CallbackQueryHandler(receive_debtor, pattern='^sel_debtor_')
                ],
                INVOICE_ITEM: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_item),
                    CallbackQueryHandler(receive_item, pattern='^sel_item_')
                ],
                INVOICE_QTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_qty)],
                INVOICE_CONFIRM: [CallbackQueryHandler(complete_invoice, pattern='^inv_confirm_')]
            },
            fallbacks=[
                CommandHandler("cancel", cancel_invoice),
                CallbackQueryHandler(cancel_invoice_inline, pattern='^inv_cancel$')
            ]
        )
        application.add_handler(invoice_conv)

        # --- REGISTER DEBTOR WIZARD ---
        debtor_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(start_debtor_flow, pattern='^btn_create_debtor$')],
            states={
                DEBTOR_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_debtor_name)],
                DEBTOR_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_debtor_phone)],
                DEBTOR_CONFIRM: [CallbackQueryHandler(complete_debtor, pattern='^debtor_confirm_')]
            },
            fallbacks=[
                CommandHandler("cancel", cancel_invoice),
                CallbackQueryHandler(cancel_invoice_inline, pattern='^inv_cancel$')
            ]
        )
        application.add_handler(debtor_conv)
        
        # --- STANDARD HANDLERS ---
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CallbackQueryHandler(handle_button_click)) 
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text_message))
        
        print("🟢 Bot is polling...")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Critical Startup Error: {e}")