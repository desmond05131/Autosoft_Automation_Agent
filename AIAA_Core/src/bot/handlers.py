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

    # Call the routing logic
    await route_request(update, context, user_text, status_msg)

async def handle_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks."""
    query = update.callback_query
    await query.answer() # Acknowledge the click so the loading circle stops

    # Map buttons to natural language intents
    fake_prompt = ""
    if query.data == "btn_sales_today":
        fake_prompt = "sales today"
    elif query.data == "btn_top_debtors":
        fake_prompt = "top 5 debtors"
    
    # Reuse the same logic as text messages
    status_msg = await query.message.reply_text("🤔 Fetching data...")
    await route_request(update, context, fake_prompt, status_msg)

async def route_request(update: Update, context, text_prompt, status_msg):
    """Shared logic for both Text and Buttons"""
    ai_result = interpret_intent(text_prompt)
    intent = ai_result.get("intent")
    args = ai_result.get("args", {})

    response_text = "I'm not sure how to help with that."

    if intent == "check_stock":
        item_code = args.get("item_code")
        await context.bot.edit_message_text(chat_id=status_msg.chat_id, message_id=status_msg.message_id, text=f"🔎 Checking stock '{item_code}'...")
        
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
        await context.bot.edit_message_text(chat_id=status_msg.chat_id, message_id=status_msg.message_id, text=f"📉 Fetching Top {limit} Debtors...")
        
        debtors = debtor_api.get_outstanding_debtors()
        top_debtors = debtors[:limit]
        
        if top_debtors:
            response_text = f"🏆 *Top {limit} Debtors*\n"
            for d in top_debtors:
                response_text += f"• {d.get('CompanyName')}: RM {float(d.get('Balance', 0)):,.2f}\n"
        else:
            response_text = "✅ No outstanding debtors found."

    elif intent == "check_sales":
        date_str = args.get("date_text", "today")
        await context.bot.edit_message_text(chat_id=status_msg.chat_id, message_id=status_msg.message_id, text=f"📆 Fetching sales for {date_str}...")
        
        dashboard = sales_api.get_daily_sales_dashboard()
        response_text = (
            f"📅 *Sales Dashboard: {dashboard['date']}*\n"
            f"💵 Revenue: RM {dashboard['revenue']:,.2f}\n"
            f"🧾 Invoices: {dashboard['count']}"
        )
    
    # Unknown intent
    elif intent == "unknown":
        response_text = "I understood your request, but I don't have a tool for that yet."

    # Final Reply
    await context.bot.edit_message_text(
        chat_id=status_msg.chat_id, 
        message_id=status_msg.message_id, 
        text=response_text, 
        parse_mode='Markdown'
    )