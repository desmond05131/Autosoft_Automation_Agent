from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
from src.ai.agent import interpret_intent
import src.api.stock as stock_api
import src.api.debtor as debtor_api
import src.api.sales as sales_api
import re

# --- MENU BUILDER ---
def get_main_menu():
    keyboard = [
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

# --- BUTTON HANDLER ---
async def handle_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            "**1. Use the Buttons:** Click the menu options for quick reports.\n"
            "**2. Chat Naturally:**\n"
            "• 'Check stock for iPhone'\n"
            "• 'Who represents ABC Company?'\n"
            "• 'Sales for 25th Dec'\n"
            "• 'Compare sales today vs last week'"
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