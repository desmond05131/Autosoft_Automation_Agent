from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from datetime import datetime, timedelta
from src.ai.agent import interpret_intent
import src.api.stock as stock_api
import src.api.debtor as debtor_api
import src.api.sales as sales_api
import src.api.invoice as invoice_api
import re

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

# --- INVOICE FLOW HANDLERS ---

async def start_invoice_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 1: User clicks Create Invoice -> Ask for Debtor Code"""
    query = update.callback_query
    await query.answer()
    
    await query.message.reply_text(
        "🧾 **New Invoice Wizard**\n\n"
        "Step 1/3: Please enter the **Debtor Code**.\n"
        "*(e.g., 300-A001 or just type a name to search)*"
    )
    return INVOICE_DEBTOR

async def receive_debtor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 2: Save Debtor -> Ask for Item"""
    user_input = update.message.text.strip()
    
    # Optional: Logic to search debtor if they typed a name instead of code
    # For now, we assume they typed a code or we verify it roughly
    context.user_data['inv_debtor'] = user_input
    
    await update.message.reply_text(
        f"✅ Debtor set to: `{user_input}`\n\n"
        "Step 2/3: Please enter the **Item Code**."
    )
    return INVOICE_ITEM

async def receive_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 3: Save Item & Fetch Price -> Ask for Quantity"""
    item_code = update.message.text.strip()
    
    # Verify item and fetch default price
    await update.message.reply_text("🔍 Checking item details...")
    item_details = stock_api.get_stock_profile(item_code)
    
    if item_details:
        price = item_details.get("Price", 0.0)
        desc = item_details.get("Description", item_code)
        
        context.user_data['inv_item'] = item_details.get("ItemCode", item_code)
        context.user_data['inv_price'] = price
        context.user_data['inv_desc'] = desc
        
        await update.message.reply_text(
            f"✅ Item found: **{desc}**\n"
            f"💵 Unit Price: RM {price:,.2f}\n\n"
            "Step 3/3: How many **Quantity**?"
        )
        return INVOICE_QTY
    else:
        # Fallback if item not found, ask user to re-enter or proceed with raw code
        await update.message.reply_text(
            f"⚠️ Item `{item_code}` not found in catalog, but we can try to use it.\n"
            "Please enter the **Quantity** to proceed (Price will be 0)."
        )
        context.user_data['inv_item'] = item_code
        context.user_data['inv_price'] = 0.0
        context.user_data['inv_desc'] = "Unknown Item"
        return INVOICE_QTY

async def receive_qty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 4: Calc Totals -> Show Confirm Button"""
    qty_text = update.message.text.strip()
    
    try:
        qty = float(qty_text)
        context.user_data['inv_qty'] = qty
    except ValueError:
        await update.message.reply_text("❌ Invalid number. Please enter a numeric Quantity (e.g., 10).")
        return INVOICE_QTY # Stay in same state

    # Prepare Confirmation Summary
    debtor = context.user_data['inv_debtor']
    item = context.user_data['inv_item']
    desc = context.user_data['inv_desc']
    price = context.user_data['inv_price']
    total = qty * price
    
    confirm_kb = [
        [
            InlineKeyboardButton("✅ Confirm Invoice", callback_data="inv_confirm_yes"),
            InlineKeyboardButton("❌ Cancel", callback_data="inv_confirm_no")
        ]
    ]
    
    msg = (
        "📝 **Confirm Invoice Details**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"👤 Customer: `{debtor}`\n"
        f"📦 Item: {desc} (`{item}`)\n"
        f"🔢 Qty: {qty} x RM {price:,.2f}\n"
        f"💵 **Total: RM {total:,.2f}**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Create this invoice now?"
    )
    
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(confirm_kb), parse_mode='Markdown')
    return INVOICE_CONFIRM

async def complete_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Final Step: Call API or Cancel"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "inv_confirm_yes":
        await query.message.edit_text("⏳ Sending data to AutoCount...")
        
        # Call API
        result = invoice_api.create_invoice(
            debtor_code=context.user_data['inv_debtor'],
            item_code=context.user_data['inv_item'],
            qty=context.user_data['inv_qty'],
            unit_price=context.user_data['inv_price']
        )
        
        if result['success']:
            await query.message.edit_text(f"✅ **Success!**\nInvoice created: `{result['doc_no']}`", parse_mode='Markdown')
        else:
            await query.message.edit_text(f"❌ **Failed**\nError: {result.get('error')}", parse_mode='Markdown')
            
    else:
        await query.message.edit_text("❌ Invoice creation cancelled.")
        
    return ConversationHandler.END

async def cancel_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Abort conversation"""
    await update.message.reply_text("❌ Operation cancelled.", reply_markup=get_main_menu())
    return ConversationHandler.END


# --- STANDARD BUTTON HANDLER ---
async def handle_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles main menu buttons (READ-ONLY functions)"""
    query = update.callback_query
    # Note: We DON'T answer() here immediately if we pass through logic, 
    # but for simple buttons we do.
    
    data = query.data
    
    # If it's the Create Invoice button, it shouldn't be handled here directly 
    # if using ConversationHandler entry_points. 
    # However, sometimes it's cleaner to handle mixed logic.
    # For this setup, ConversationHandler filters will catch 'btn_create_invoice' 
    # BEFORE this function if configured correctly in main.py.
    
    await query.answer()
    
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
            "**1. Create Invoice:** Click the button and follow the steps.\n"
            "**2. Check Data:** Click reports for quick views.\n"
            "**3. Chat Naturally:**\n"
            "• 'Check stock for iPhone'\n"
            "• 'Sales for 25th Dec'\n"
        )
        await query.message.reply_text(msg, parse_mode='Markdown')

# --- TEXT HANDLER ---
async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    # AI Processing
    status_msg = await update.message.reply_text("🤔 Thinking...")
    intent_data = interpret_intent(user_text)
    intent = intent_data.get("intent")
    args = intent_data.get("args", {})
    
    print(f"🧠 Intent: {intent} | Args: {args}")
    
    await context.bot.delete_message(chat_id=status_msg.chat_id, message_id=status_msg.message_id)

    # --- SALES HANDLERS ---
    if intent == "compare_sales":
        date1 = args.get("date1")
        date2 = args.get("date2")
        
        await update.message.reply_text(f"📊 Comparing {date1} vs {date2}...")
        s1 = sales_api.get_sales_dashboard(date1)
        s2 = sales_api.get_sales_dashboard(date2)
        
        if s1 and s2:
            diff = s1['sales'] - s2['sales']
            icon = "🟢" if diff >= 0 else "🔴"
            msg = (
                f"⚔️ **Sales Comparison**\n"
                f"📅 **{s1['date']}**: RM {s1['sales']:,.2f}\n"
                f"📅 **{s2['date']}**: RM {s2['sales']:,.2f}\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"Difference: {icon} RM {abs(diff):,.2f}"
            )
            await update.message.reply_text(msg, parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ Could not fetch data for one or both dates.")

    elif intent == "get_sales":
        target_date = args.get("date")
        await update.message.reply_text(f"📆 Fetching sales for {target_date}...")
        
        s = sales_api.get_sales_dashboard(target_date)
        if s:
            icon = "📈" if s['sales'] >= s['prev_sales'] else "📉"
            await update.message.reply_text(
                f"📅 **Sales: {s['date']}**\n"
                f"💵 Revenue: RM {s['sales']:,.2f}\n"
                f"🧾 Invoices: {s['count']}\n"
                f"({icon} vs Prev Day: RM {s['prev_sales']:,.2f})", 
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("❌ No sales data found for this date.")

    # --- DEBTOR HANDLERS ---
    elif intent == "list_debtors_outstanding":
        limit = args.get("limit", 5)
        await update.message.reply_text(f"📉 Fetching Top {limit} Debtors...")
        data = debtor_api.get_debtor_outstanding(limit)
        msg = f"🏆 **Top {len(data)} Debtors**\n" + "\n".join([f"• {d['CompanyName']}: RM {d['show_bal']:,.2f}" for d in data]) if data else "✅ No debt."
        await update.message.reply_text(msg, parse_mode='Markdown')

    elif intent == "list_all_debtors":
        await update.message.reply_text("📂 Fetching Customer Directory...")
        data = debtor_api.get_all_debtors(20)
        msg = "📂 **Customer List**\n" + "\n".join([f"• `{d['AccNo']}` {d['CompanyName']}" for d in data]) if data else "❌ No customers."
        await update.message.reply_text(msg, parse_mode='Markdown')

    elif intent == "profile_debtor":
        kw = args.get("keyword")
        await update.message.reply_text(f"🔍 Searching customer '{kw}'...")
        d = debtor_api.get_debtor_profile(kw)
        if d:
            addr = ", ".join(filter(None, [d.get(f'Address{i}') for i in range(1,5)] + [d.get('PostCode'), d.get('State')])) or "N/A"
            msg = (f"👤 **{d['CompanyName']}**\n🆔 `{d['AccNo']}`\n💰 Bal: RM {d['show_bal']:,.2f}\n"
                   f"📍 {addr}\n📞 {d.get('Phone1', 'N/A')} | 📠 {d.get('Fax1', 'N/A')}\n"
                   f"💳 Limit: RM {d.get('CreditLimit',0):,.2f} | 📅 Term: {d.get('DisplayTerm','N/A')}")
            await update.message.reply_text(msg, parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ Customer not found.")

    # --- STOCK HANDLERS ---
    elif intent == "list_all_stock":
        await update.message.reply_text("📦 Fetching Item Catalog...")
        data = stock_api.get_stock_list(20)
        msg = "📦 **Item Catalog**\n" + "\n".join([f"• `{i['ItemCode']}` {i['Description']}: **{i['show_qty']}**" for i in data]) if data else "❌ No items."
        await update.message.reply_text(msg, parse_mode='Markdown')

    elif intent == "profile_stock":
        kw = args.get("keyword")
        await update.message.reply_text(f"🔎 Checking stock '{kw}'...")
        i = stock_api.get_stock_profile(kw)
        if i:
            msg = (
                f"📦 **{i['Description']}**\n"
                f"🔢 Code: `{i['ItemCode']}`\n"
                f"📊 **Stock: {i['show_qty']} {i.get('UOM','UNIT')}**\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"💵 Price: RM {i.get('RefPrice', i.get('Price', 0.0)):,.2f}\n"
                f"🛠 Cost: RM {i.get('StdCost', 0.0):,.2f}\n"
                f"📂 Group: {i.get('ItemGroup', 'N/A')} | Type: {i.get('ItemType', 'N/A')}\n"
            )
            await update.message.reply_text(msg, parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ Item not found.")

    else:
        # Fallback to Menu
        await start_command(update, context)