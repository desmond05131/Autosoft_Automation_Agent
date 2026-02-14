from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from datetime import datetime, timedelta
from src.ai.agent import interpret_intent
import src.api.stock as stock_api
import src.api.debtor as debtor_api
import src.api.sales as sales_api
import src.api.invoice as invoice_api

# --- CONVERSATION STATES ---
INVOICE_DEBTOR, INVOICE_ITEM, INVOICE_QTY, INVOICE_CONFIRM = range(4)

# --- MENU BUILDER ---
def get_main_menu():
    keyboard = [
        [
            InlineKeyboardButton("➕ Create Invoice", callback_data="btn_create_invoice")
        ],
        [
            InlineKeyboardButton("📊 Today's Sales", callback_data="btn_sales_today"),
            InlineKeyboardButton("📉 Yesterday", callback_data="btn_sales_yesterday")
        ],
        [
            InlineKeyboardButton("🏆 Top Debtors", callback_data="btn_debtors_top"),
            InlineKeyboardButton("👥 Customer List", callback_data="btn_debtors_all")
        ],
        [
            InlineKeyboardButton("📦 Stock Catalog", callback_data="btn_stock_list"),
            InlineKeyboardButton("🔍 Help / Tips", callback_data="btn_help")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- COMMANDS ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🤖 **AutoCount AI Dashboard**\n"
        "Select an option below or type your request naturally.\n"
        "*(e.g., 'Check price of iPhone', 'Compare sales today vs last Monday')*"
    )
    await update.message.reply_text(welcome_text, reply_markup=get_main_menu(), parse_mode='Markdown')

# --- INVOICE WIZARD HANDLERS ---

async def start_invoice_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 1: Init Wizard -> Ask Debtor"""
    query = update.callback_query
    await query.answer()
    
    await query.message.reply_text(
        "🧾 **New Invoice Wizard**\n\n"
        "Step 1/3: Please enter the **Debtor Code**.\n"
        "*(e.g., 300-A001)*"
    )
    return INVOICE_DEBTOR

async def receive_debtor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 2: Save Debtor -> Ask Item"""
    user_input = update.message.text.strip()
    context.user_data['inv_debtor'] = user_input
    
    await update.message.reply_text(
        f"✅ Debtor set to: `{user_input}`\n\n"
        "Step 2/3: Please enter the **Item Code**."
    )
    return INVOICE_ITEM

async def receive_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 3: Save Item & Price -> Ask Qty"""
    item_code = update.message.text.strip()
    await update.message.reply_text("🔍 Checking item details...")
    
    # Fetch profile to get Description and Price
    item_profile = stock_api.get_stock_profile(item_code)
    
    if item_profile:
        # Use DB data
        desc = item_profile.get("Description") or item_profile.get("Desc2") or item_code
        price = float(item_profile.get("Price", 0.0))
        # Sometimes API returns price in different fields, verify if 0
        if price == 0.0 and "RecPrice" in item_profile:
             price = float(item_profile["RecPrice"])
        
        context.user_data['inv_item'] = item_profile.get("ItemCode", item_code)
        context.user_data['inv_desc'] = desc
        context.user_data['inv_price'] = price
        
        await update.message.reply_text(
            f"✅ Item found: **{desc}**\n"
            f"💵 Price: RM {price:,.2f}\n\n"
            "Step 3/3: How many **Quantity**?"
        )
    else:
        # Fallback if item not found (allow manual entry)
        context.user_data['inv_item'] = item_code
        context.user_data['inv_desc'] = "Unknown Item"
        context.user_data['inv_price'] = 0.0
        
        await update.message.reply_text(
            f"⚠️ Item `{item_code}` not found in catalog, but we will proceed.\n"
            "(Price set to RM 0.00)\n\n"
            "Step 3/3: How many **Quantity**?"
        )
    
    return INVOICE_QTY

async def receive_qty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 4: Calc Total -> Ask Confirmation"""
    qty_text = update.message.text.strip()
    try:
        qty = float(qty_text)
        context.user_data['inv_qty'] = qty
    except ValueError:
        await update.message.reply_text("❌ Invalid number. Please enter a number (e.g., 10).")
        return INVOICE_QTY

    # Summary Data
    debtor = context.user_data['inv_debtor']
    item = context.user_data['inv_item']
    desc = context.user_data['inv_desc']
    price = context.user_data['inv_price']
    total = qty * price

    # Buttons
    keyboard = [
        [InlineKeyboardButton("✅ Confirm Invoice", callback_data="inv_confirm_yes")],
        [InlineKeyboardButton("❌ Cancel", callback_data="inv_confirm_no")]
    ]
    
    msg = (
        "📝 **Confirm Invoice Details**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"👤 Customer: `{debtor}`\n"
        f"📦 Item: {desc}\n"
        f"🔢 Qty: {qty} x RM {price:,.2f}\n"
        f"💵 **Total: RM {total:,.2f}**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Create this invoice now?"
    )
    
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return INVOICE_CONFIRM

async def complete_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Final Action: Call API"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "inv_confirm_yes":
        await query.message.edit_text("⏳ Sending data to AutoCount...")
        
        res = invoice_api.create_invoice(
            debtor_code=context.user_data['inv_debtor'],
            item_code=context.user_data['inv_item'],
            qty=context.user_data['inv_qty'],
            unit_price=context.user_data['inv_price']
        )
        
        if res['success']:
            await query.message.edit_text(f"✅ **Success!**\nInvoice Created: `{res['doc_no']}`", parse_mode='Markdown')
        else:
            await query.message.edit_text(f"❌ **Failed**\nError: {res.get('error')}", parse_mode='Markdown')
            
    else:
        await query.message.edit_text("❌ Invoice creation cancelled.")
        
    return ConversationHandler.END

async def cancel_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Operation cancelled.", reply_markup=get_main_menu())
    return ConversationHandler.END

# --- STANDARD HANDLERS ---
async def handle_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles standard menu buttons (non-wizard)"""
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == 'btn_sales_today':
        target_date = datetime.now().strftime("%Y/%m/%d")
        s = sales_api.get_sales_dashboard(target_date)
        if s:
            icon = "📈" if s['sales'] >= s['prev_sales'] else "📉"
            msg = (
                f"📊 **Sales Dashboard: Today**\n"
                f"💵 Revenue: RM {s['sales']:,.2f}\n"
                f"🧾 Invoices: {s['count']}\n"
                f"({icon} vs Prev Day: RM {s['prev_sales']:,.2f})"
            )
            await query.message.reply_text(msg, parse_mode='Markdown')
        else:
            await query.message.reply_text("❌ No data for today.")

    elif data == 'btn_sales_yesterday':
        target_date = (datetime.now() - timedelta(days=1)).strftime("%Y/%m/%d")
        s = sales_api.get_sales_dashboard(target_date)
        if s:
            msg = (f"📉 **Sales: Yesterday ({s['date']})**\n"
                   f"💵 Revenue: RM {s['sales']:,.2f}\n"
                   f"🧾 Invoices: {s['count']}")
            await query.message.reply_text(msg, parse_mode='Markdown')

    elif data == 'btn_debtors_top':
        data = debtor_api.get_debtor_outstanding(5)
        msg = f"🏆 **Top 5 Debtors**\n" + "\n".join([f"• {d['CompanyName']}: RM {d['show_bal']:,.2f}" for d in data]) if data else "✅ No outstanding debt."
        await query.message.reply_text(msg, parse_mode='Markdown')

    elif data == 'btn_debtors_all':
        data = debtor_api.get_all_debtors(20)
        msg = "👥 **Customer Directory**\n" + "\n".join([f"• `{d['AccNo']}` {d['CompanyName']}" for d in data]) if data else "❌ No customers found."
        await query.message.reply_text(msg, parse_mode='Markdown')

    elif data == 'btn_stock_list':
        data = stock_api.get_stock_list(20)
        msg = "📦 **Stock Catalog**\n" + "\n".join([f"• `{i['ItemCode']}` {i['Description']}: **{i['show_qty']}**" for i in data]) if data else "❌ No items found."
        await query.message.reply_text(msg, parse_mode='Markdown')
        
    elif data == 'btn_help':
        msg = (
            "💡 **How to use AutoCount AI**\n\n"
            "**1. Create Invoice:** Click 'Create Invoice' in the menu.\n"
            "**2. Check Reports:** Click the dashboard buttons.\n"
            "**3. Chat:** Type 'Check stock for iPhone' or 'Sales today'."
        )
        await query.message.reply_text(msg, parse_mode='Markdown')

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    # AI Processing
    status_msg = await update.message.reply_text("🤔 Thinking...")
    intent_data = interpret_intent(user_text)
    intent = intent_data.get("intent")
    args = intent_data.get("args", {})
    
    await context.bot.delete_message(chat_id=status_msg.chat_id, message_id=status_msg.message_id)

    if intent == "compare_sales":
        date1 = args.get("date1")
        date2 = args.get("date2")
        s1 = sales_api.get_sales_dashboard(date1)
        s2 = sales_api.get_sales_dashboard(date2)
        if s1 and s2:
            diff = s1['sales'] - s2['sales']
            icon = "🟢" if diff >= 0 else "🔴"
            msg = f"⚔️ **Comparison**\n{s1['date']}: RM {s1['sales']:,.2f}\n{s2['date']}: RM {s2['sales']:,.2f}\nDiff: {icon} RM {abs(diff):,.2f}"
            await update.message.reply_text(msg, parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ Error fetching data.")

    elif intent == "get_sales":
        target_date = args.get("date")
        s = sales_api.get_sales_dashboard(target_date)
        if s:
            await update.message.reply_text(f"📅 **Sales {s['date']}**: RM {s['sales']:,.2f}", parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ No data.")

    elif intent == "list_debtors_outstanding":
        data = debtor_api.get_debtor_outstanding(args.get("limit", 5))
        msg = "🏆 **Top Debtors**\n" + "\n".join([f"• {d['CompanyName']}: RM {d['show_bal']:,.2f}" for d in data]) if data else "✅ No debt."
        await update.message.reply_text(msg, parse_mode='Markdown')

    elif intent == "profile_stock":
        kw = args.get("keyword")
        i = stock_api.get_stock_profile(kw)
        if i:
            msg = f"📦 **{i['Description']}**\nCode: `{i['ItemCode']}`\nQty: {i['show_qty']}\nPrice: RM {i.get('Price',0):,.2f}"
            await update.message.reply_text(msg, parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ Item not found.")

    else:
        await start_command(update, context)