from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.ai.agent import interpret_intent
import src.api.stock as stock_api
import src.api.debtor as debtor_api
import src.api.sales as sales_api

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responds to /start"""
    welcome_text = (
        "🤖 *AutoCount AI Dashboard*\n"
        "Select an option below or type your request naturally.\n"
        "_(e.g., 'Check price of iPhone', 'Compare sales today vs last Monday')_"
    )
    # Example of the inline buttons you requested
    keyboard = [
        [InlineKeyboardButton("📊 Daily Sales", callback_data="btn_sales_today")],
        [InlineKeyboardButton("🏆 Top Debtors", callback_data="btn_top_debtors")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes natural language text."""
    user_text = update.message.text
    status_msg = await update.message.reply_text("🤔 Thinking...")

    # 1. Ask AI for Intent
    ai_result = interpret_intent(user_text)
    intent = ai_result.get("intent")
    args = ai_result.get("args", {})

    response_text = "I'm not sure how to help with that."

    # 2. Route to correct API function
    if intent == "check_stock":
        item_code = args.get("item_code")
        await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=status_msg.message_id, text=f"🔎 Checking stock '{item_code}'...")
        
        item = stock_api.get_stock_item(item_code)
        if item:
            response_text = (
                f"📦 *Stock Info*\n"
                f"🔢 Code: `{item.get('ItemCode')}`\n"
                f"📊 Stock: {item.get('BalQty', 0)} {item.get('UOM', 'UNIT')}\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"💵 Price: RM {item.get('Price', 0.00):.2f}"
            )
        else:
            response_text = f"❌ Item '{item_code}' not found."

    elif intent == "check_top_debtors":
        limit = int(args.get("limit", 5))
        await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=status_msg.message_id, text=f"📉 Fetching Top {limit} Debtors...")
        
        debtors = debtor_api.get_outstanding_debtors()
        top_debtors = debtors[:limit]
        
        if top_debtors:
            response_text = f"🏆 *Top {limit} Debtors*\n"
            for d in top_debtors:
                response_text += f"• {d.get('CompanyName')}: RM {float(d.get('Balance', 0)):,.2f}\n"
        else:
            response_text = "✅ No outstanding debtors found."

    elif intent == "check_sales":
        # Simplified for brevity; logic to parse date needed in real app
        date_str = args.get("date_text", "today")
        # You would add date parsing logic here usually
        await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=status_msg.message_id, text=f"📆 Fetching sales for {date_str}...")
        
        dashboard = sales_api.get_daily_sales_dashboard() # Defaults to today
        response_text = (
            f"📅 *Sales Dashboard: {dashboard['date']}*\n"
            f"💵 Revenue: RM {dashboard['revenue']:,.2f}\n"
            f"🧾 Invoices: {dashboard['count']}"
        )

    # 3. Send Final Reply
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id, 
        message_id=status_msg.message_id, 
        text=response_text, 
        parse_mode='Markdown'
    )
