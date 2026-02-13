from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
from src.ai.agent import interpret_intent
import src.api.stock as stock_api
import src.api.debtor as debtor_api
import src.api.sales as sales_api

# --- MENU BUILDER ---
def get_main_menu():
    keyboard = [
        [
            InlineKeyboardButton("📊 Sales Today", callback_data="sales_today"),
            InlineKeyboardButton("📉 Sales Yesterday", callback_data="sales_yesterday")
        ],
        [
            InlineKeyboardButton("🏆 Top 5 Debtors", callback_data="top_debtors"),
            InlineKeyboardButton("👥 Customer List", callback_data="debtor_list")
        ],
        [
            InlineKeyboardButton("📦 Stock List", callback_data="stock_list"),
            InlineKeyboardButton("💡 Help", callback_data="help_info")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- COMMANDS ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🤖 *AutoCount AI Dashboard*\n"
        "Select an option below or type your request naturally.\n"
        "_(e.g., 'Check price of iPhone', 'Compare sales today vs last Monday')_"
    )
    await update.message.reply_text(welcome_text, reply_markup=get_main_menu(), parse_mode='Markdown')

# --- BUTTON HANDLER ---
async def handle_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() # Stop loading animation
    
    data = query.data
    
    if data == "sales_today":
        await execute_sales_report(update, context, "today")
    elif data == "sales_yesterday":
        await execute_sales_report(update, context, "yesterday")
    elif data == "top_debtors":
        await execute_top_debtors(update, context)
    elif data == "debtor_list":
        await execute_customer_list(update, context)
    elif data == "stock_list":
        await execute_stock_list(update, context)
    elif data == "help_info":
        help_text = (
            "💡 *How to use AutoCount AI*\n\n"
            "1. *Use the Buttons*: Click the menu options for quick reports.\n"
            "2. *Chat Naturally*:\n"
            "• 'Check stock for iPhone'\n"
            "• 'Who represents ABC Company?'\n"
            "• 'Sales for 25th Dec'\n"
            "• 'List top 5 debtors'"
        )
        await query.message.reply_text(help_text, parse_mode='Markdown')

# --- TEXT HANDLER ---
async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    status_msg = await update.message.reply_text("🤔 Thinking...")

    # 1. AI Logic
    intent_data = interpret_intent(user_text)
    intent = intent_data.get("intent")
    args = intent_data.get("args", {})

    print(f"🧠 Detected Intent: {intent} | Args: {args}")

    # 2. Routing
    try:
        if intent == "check_stock":
            item_code = args.get("item_code")
            # Logic for single item check
            item = stock_api.get_stock_item(item_code)
            if item:
                msg = (
                    f"📦 *{item.get('Description', item_code)}*\n"
                    f"🔢 Code: `{item.get('ItemCode')}`\n"
                    f"📊 Stock: {item.get('BalQty', 0)} {item.get('UOM', 'UNIT')}\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"💵 Price: RM {item.get('Price', 0.00):.2f}\n"
                    f"🛠 Cost: RM {item.get('Cost', 0.00):.2f}\n"
                    f"📂 Group: {item.get('ItemGroup', 'N/A')} | Type: {item.get('ItemType', 'N/A')}"
                )
                await context.bot.edit_message_text(chat_id=status_msg.chat_id, message_id=status_msg.message_id, text=msg, parse_mode='Markdown')
            else:
                await context.bot.edit_message_text(chat_id=status_msg.chat_id, message_id=status_msg.message_id, text=f"❌ Item '{item_code}' not found.")

        elif intent == "check_debtor_info":
            name = args.get("name")
            debtor = debtor_api.find_debtor(name)
            if debtor:
                msg = (
                    f"👤 *{debtor.get('CompanyName')}*\n"
                    f"🆔 `{debtor.get('DebtorCode')}`\n"
                    f"💰 Bal: RM {float(debtor.get('Balance', 0)):,.2f}\n"
                    f"📍 {debtor.get('Address', 'N/A')}\n"
                    f"📞 {debtor.get('Phone', 'N/A')} | 📠 {debtor.get('Fax', 'N/A')}\n"
                    f"💳 Limit: RM {float(debtor.get('CreditLimit', 0)):,.2f} | 📅 Term: {debtor.get('CreditTerm', 'N/A')}"
                )
                await context.bot.edit_message_text(chat_id=status_msg.chat_id, message_id=status_msg.message_id, text=msg, parse_mode='Markdown')
            else:
                await context.bot.edit_message_text(chat_id=status_msg.chat_id, message_id=status_msg.message_id, text=f"❌ Debtor '{name}' not found.")

        elif intent == "list_top_debtors":
            # Delete thinking message and send fresh report
            await context.bot.delete_message(chat_id=status_msg.chat_id, message_id=status_msg.message_id)
            await execute_top_debtors(update, context)

        elif intent == "check_sales":
             # Delete thinking message and send fresh report
            await context.bot.delete_message(chat_id=status_msg.chat_id, message_id=status_msg.message_id)
            date_text = args.get("date_text", "today")
            await execute_sales_report(update, context, date_text)

        elif intent == "list_customers":
             # Delete thinking message and send fresh report
            await context.bot.delete_message(chat_id=status_msg.chat_id, message_id=status_msg.message_id)
            await execute_customer_list(update, context)
            
        elif intent == "list_stock":
             # Delete thinking message and send fresh report
            await context.bot.delete_message(chat_id=status_msg.chat_id, message_id=status_msg.message_id)
            await execute_stock_list(update, context)

        else:
             await context.bot.edit_message_text(chat_id=status_msg.chat_id, message_id=status_msg.message_id, text="I'm not sure how to help with that. Try checking stock or sales.")
             
    except Exception as e:
        print(f"Handler Error: {e}")
        await context.bot.edit_message_text(chat_id=status_msg.chat_id, message_id=status_msg.message_id, text="⚠️ An error occurred while processing your request.")

# --- EXECUTION FUNCTIONS (Shared by Buttons & AI) ---

async def execute_sales_report(update, context, date_keyword):
    # Determine date
    target_date = datetime.now()
    title = "Today"
    if "yesterday" in date_keyword.lower():
        target_date = datetime.now() - timedelta(days=1)
        title = f"Yesterday ({target_date.strftime('%Y/%m/%d')})"
    
    date_str = target_date.strftime("%Y-%m-%d")
    
    # Message fallback for buttons vs text
    chat_id = update.effective_chat.id
    if update.callback_query:
        await update.callback_query.message.reply_text(f"📆 Fetching sales for {title}...")
    else:
        # If via text, the "Thinking" message handles the wait
        pass 

    data = sales_api.get_daily_sales(date_str)
    
    msg = (
        f"📅 *Sales: {title}*\n"
        f"💵 Revenue: RM {data['revenue']:,.2f}\n"
        f"🧾 Invoices: {data['count']}\n"
        f"(📈 vs Prev Day: RM {data['diff']:,.2f})"
    )
    await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode='Markdown')

async def execute_top_debtors(update, context):
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id=chat_id, text="📉 Fetching Top 5 Debtors...")
    
    debtors = debtor_api.get_top_debtors(5)
    
    if not debtors:
        await context.bot.send_message(chat_id=chat_id, text="✅ No outstanding debtors found.")
        return

    msg = "🏆 *Top 5 Debtors*\n"
    for d in debtors:
        msg += f"• {d['CompanyName']}: RM {d['Balance']:,.2f}\n"
    
    await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode='Markdown')

async def execute_customer_list(update, context):
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id=chat_id, text="👥 Fetching Customer List...")
    
    customers = debtor_api.get_all_debtors(limit=20)
    msg = "👥 *Customer Directory*\n"
    for c in customers:
        msg += f"• `{c['DebtorCode']}` {c['CompanyName']}\n"
        
    await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode='Markdown')

async def execute_stock_list(update, context):
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id=chat_id, text="📦 Fetching Stock List...")
    
    # Assuming we fetch a small list for display
    items = stock_api.get_all_stock(limit=20)
    
    msg = "📦 *Stock Catalog*\n"
    for i in items:
        # Robustly handle missing keys
        desc = i.get('Description', i.get('ItemCode', 'Unknown'))
        qty = i.get('BalQty', 0.0)
        msg += f"• {desc} : {qty}\n"
        
    await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode='Markdown')