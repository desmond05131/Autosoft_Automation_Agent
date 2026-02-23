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
DEBTOR_NAME, DEBTOR_PHONE, DEBTOR_CONFIRM = range(4, 7)

# --- MENU BUILDER ---
def get_main_menu():
    keyboard = [
        [
            InlineKeyboardButton("➕ Create Invoice", callback_data="btn_create_invoice"),
            InlineKeyboardButton("➕ Create Debtor", callback_data="btn_create_debtor")
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
    """Step 1: Init Wizard -> List Top 5 Debtors or Ask for Input"""
    query = update.callback_query
    await query.answer()
    
    # Fetch top debtors for quick selection
    debtors = debtor_api.get_debtor_outstanding(5)
    keyboard = []
    if debtors:
        for d in debtors:
            code = d.get('AccNo', 'Unknown')
            name = d.get('CompanyName', '')
            keyboard.append([InlineKeyboardButton(f"🏢 {code} ({name})", callback_data=f"sel_debtor_{code}")])
    keyboard.append([InlineKeyboardButton("➕ Create Debtor", callback_data="btn_create_debtor")])
    keyboard.append([InlineKeyboardButton("❌ Cancel Wizard", callback_data="inv_cancel")])
    
    msg = (
        "🧾 **New Invoice Wizard (Step 1/3)**\n\n"
        "Select a frequent Debtor below, or **type a name/code to search**."
    )
    await query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return INVOICE_DEBTOR

async def receive_debtor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 2: Save Debtor -> List Top 5 Items or Ask for Input"""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        user_input = query.data.replace("sel_debtor_", "")
        await query.message.edit_text(f"✅ Selected Debtor: `{user_input}`", parse_mode='Markdown')
        message_obj = query.message
    else:
        user_input = update.message.text.strip()
        message_obj = update.message
        
    context.user_data['inv_debtor'] = user_input
    
    # Fetch top items for quick selection
    items = stock_api.get_stock_list(5)
    keyboard = []
    if items:
        for i in items:
            code = i.get('ItemCode', 'Unknown')
            desc = i.get('Description', code)
            price = float(i.get('Price', 0.0))
            keyboard.append([InlineKeyboardButton(f"🛒 {desc} (RM {price:,.2f})", callback_data=f"sel_item_{code}")])

    keyboard.append([InlineKeyboardButton("❌ Cancel Wizard", callback_data="inv_cancel")])

    msg = (
        f"✅ Customer: `{user_input}`\n\n"
        "📦 **Step 2/3: Select Item**\n"
        "Select a popular item below or **type a product name/code to search**."
    )
    await message_obj.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return INVOICE_ITEM

async def receive_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 3: Save Item & Price -> Ask Qty"""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        item_code = query.data.replace("sel_item_", "")
        await query.message.edit_text(f"✅ Selected Item: `{item_code}`", parse_mode='Markdown')
        message_obj = query.message
    else:
        item_code = update.message.text.strip()
        message_obj = update.message
        
    await message_obj.reply_text("🔍 Checking item details...")
    
    item_profile = stock_api.get_stock_profile(item_code)
    
    if item_profile:
        desc = item_profile.get("Description") or item_profile.get("Desc2") or item_code
        price = float(item_profile.get("Price", 0.0))
        if price == 0.0 and "RecPrice" in item_profile:
             price = float(item_profile["RecPrice"])
        
        context.user_data['inv_item'] = item_profile.get("ItemCode", item_code)
        context.user_data['inv_desc'] = desc
        context.user_data['inv_price'] = price
        
        await message_obj.reply_text(
            f"✅ Item found: **{desc}**\n"
            f"💵 Price: RM {price:,.2f}\n\n"
            "Step 3/3: How many **Quantity**?"
        )
    else:
        context.user_data['inv_item'] = item_code
        context.user_data['inv_desc'] = "Unknown Item"
        context.user_data['inv_price'] = 0.0
        
        await message_obj.reply_text(
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

    debtor = context.user_data['inv_debtor']
    item = context.user_data['inv_item']
    desc = context.user_data['inv_desc']
    price = context.user_data['inv_price']
    total = qty * price

    keyboard = [
        [InlineKeyboardButton("✅ Confirm Invoice", callback_data="inv_confirm_yes")],
        [InlineKeyboardButton("❌ Cancel", callback_data="inv_cancel")]
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
            
    return ConversationHandler.END

async def cancel_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Operation cancelled.", reply_markup=get_main_menu())
    return ConversationHandler.END

async def cancel_invoice_inline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles inline cancel buttons during Conversation states"""
    query = update.callback_query
    await query.answer()
    await query.message.edit_text("❌ Operation cancelled.")
    return ConversationHandler.END

# --- DEBTOR WIZARD HANDLERS ---
async def start_debtor_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("🆕 **New Customer Wizard**\n\nStep 1/2: Please enter the **Company/Customer Name**.")
    return DEBTOR_NAME

async def receive_debtor_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    context.user_data['new_debtor_name'] = user_input
    await update.message.reply_text(f"✅ Name set to: `{user_input}`\n\nStep 2/2: Please enter the **Contact Number**.\n*(Type 'skip' if not applicable)*")
    return DEBTOR_PHONE

async def receive_debtor_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    context.user_data['new_debtor_phone'] = "" if phone.lower() == 'skip' else phone
    name = context.user_data['new_debtor_name']
    phone_display = context.user_data['new_debtor_phone'] or "N/A"

    keyboard = [
        [InlineKeyboardButton("✅ Confirm Creation", callback_data="debtor_confirm_yes")],
        [InlineKeyboardButton("❌ Cancel", callback_data="inv_cancel")]
    ]
    
    msg = f"📝 **Confirm Customer Details**\n━━━━━━━━━━━━━━━━━━\n🏢 Name: `{name}`\n📞 Phone: `{phone_display}`\n━━━━━━━━━━━━━━━━━━\nCreate this customer now?"
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return DEBTOR_CONFIRM

async def complete_debtor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "debtor_confirm_yes":
        await query.message.edit_text("⏳ Sending data to AutoCount...")
        res = debtor_api.create_debtor(context.user_data['new_debtor_name'], context.user_data['new_debtor_phone'])
        if res['success']:
            await query.message.edit_text(f"✅ **Success!**\nCustomer Created! AutoCount Account No: `{res['acc_no']}`", parse_mode='Markdown')
        else:
            await query.message.edit_text(f"❌ **Failed**\nError: {res.get('error')}", parse_mode='Markdown')
    return ConversationHandler.END


# --- STANDARD HANDLERS ---
async def handle_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles standard menu buttons (non-wizard) AND Fast-Track buttons"""
    query = update.callback_query
    await query.answer()
    data = query.data
    
    # Fast-Track Handlers
    if data == 'fast_inv_yes':
        await query.message.edit_text("⏳ Sending data to AutoCount...")
        res = invoice_api.create_invoice(
            debtor_code=context.user_data.get('inv_debtor'),
            item_code=context.user_data.get('inv_item'),
            qty=context.user_data.get('inv_qty'),
            unit_price=context.user_data.get('inv_price')
        )
        if res['success']:
            await query.message.edit_text(f"✅ **Success!**\nInvoice Created: `{res['doc_no']}`", parse_mode='Markdown')
        else:
            await query.message.edit_text(f"❌ **Failed**\nError: {res.get('error')}", parse_mode='Markdown')

    elif data == 'fast_inv_no':
        await query.message.edit_text("❌ Fast-Track invoice cancelled.")

    # Main Menu Read-Only Handlers
    elif data == 'btn_sales_today':
        target_date = datetime.now().strftime("%Y/%m/%d")
        s = sales_api.get_sales_dashboard(target_date)
        if s:
            icon = "📈" if s['sales'] >= s['prev_sales'] else "📉"
            msg = f"📊 **Sales Dashboard: Today**\n💵 Revenue: RM {s['sales']:,.2f}\n🧾 Invoices: {s['count']}\n({icon} vs Prev Day: RM {s['prev_sales']:,.2f})"
            await query.message.reply_text(msg, parse_mode='Markdown')
        else:
            await query.message.reply_text("❌ No data for today.")

    elif data == 'btn_sales_yesterday':
        target_date = (datetime.now() - timedelta(days=1)).strftime("%Y/%m/%d")
        s = sales_api.get_sales_dashboard(target_date)
        if s:
            msg = f"📉 **Sales: Yesterday ({s['date']})**\n💵 Revenue: RM {s['sales']:,.2f}\n🧾 Invoices: {s['count']}"
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
        msg = "💡 **How to use AutoCount AI**\n\n**1. Chat:** Type 'Invoice for TechCorp for 5 Apple' or 'Sales today'."
        await query.message.reply_text(msg, parse_mode='Markdown')


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    # AI Processing
    status_msg = await update.message.reply_text("🤔 Thinking...")
    intent_data = interpret_intent(user_text)
    intent = intent_data.get("intent")
    args = intent_data.get("args", {})
    
    await context.bot.delete_message(chat_id=status_msg.chat_id, message_id=status_msg.message_id)

    # --- FAST TRACK INVOICE ---
    if intent == "create_invoice_fast":
        debtor = args.get("debtor")
        item = args.get("item")
        qty = args.get("qty", 1)
        
        if not debtor or not item:
            await update.message.reply_text("❌ Please specify debtor and item. (e.g. 'Invoice for Alpha for 5 Apple')")
            return
            
        try:
            qty = float(qty)
        except ValueError:
            qty = 1.0

        await update.message.reply_text(f"⚡ Fast Track: Preparing invoice for `{debtor}`...")
        
        i = stock_api.get_stock_profile(item)
        if i:
            desc = i.get("Description") or i.get("Desc2") or item
            price = float(i.get("Price", 0.0))
            if price == 0.0 and "RecPrice" in i:
                 price = float(i.get("RecPrice", 0.0))
            item_code = i.get("ItemCode", item)
        else:
            desc = "Unknown Item"
            price = 0.0
            item_code = item
            
        total = qty * price
        
        # Save to context for the global confirm handler to read
        context.user_data['inv_debtor'] = debtor
        context.user_data['inv_item'] = item_code
        context.user_data['inv_desc'] = desc
        context.user_data['inv_price'] = price
        context.user_data['inv_qty'] = qty
        
        keyboard = [
            [InlineKeyboardButton("✅ Confirm Invoice", callback_data="fast_inv_yes")],
            [InlineKeyboardButton("❌ Cancel", callback_data="fast_inv_no")]
        ]
        
        msg = (
            "⚡ **Fast-Track Invoice Details**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"👤 Customer: `{debtor}`\n"
            f"📦 Item: {desc} (`{item_code}`)\n"
            f"🔢 Qty: {qty} x RM {price:,.2f}\n"
            f"💵 **Total: RM {total:,.2f}**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Create this invoice now?"
        )
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    # --- READ ONLY INTENTS ---
    elif intent == "compare_sales":
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

    elif intent == "profile_debtor":
        kw = args.get("keyword")
        d = debtor_api.get_debtor_profile(kw)
        if d:
            # Format the debtor details nicely
            balance = d.get('show_bal', 0.0)
            credit_limit = d.get('CreditLimit', 0.0)
            phone = d.get('Phone1', 'N/A')
            term = d.get('CreditTerm', 'N/A')
            
            msg = (
                f"🏢 **Customer Profile: {d['CompanyName']}**\n"
                f"🆔 Code: `{d['AccNo']}`\n"
                f"📞 Phone: {phone}\n"
                f"💰 Balance: RM {balance:,.2f}\n"
                f"💳 Limit: RM {credit_limit:,.2f}\n"
                f"📅 Term: {term}"
            )
            await update.message.reply_text(msg, parse_mode='Markdown')
        else:
            await update.message.reply_text(f"❌ Customer '{kw}' not found.")

    else:
        await start_command(update, context)