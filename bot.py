import logging
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler
)

from config import TOKEN, DATA_DIR, PRODUCTS_FILE, TABLES_FILE, ORDERS_FILE, ADMINS_FILE
from config import ADD_PRODUCT, ADD_TABLE, EDIT_PRODUCT, EDIT_TABLE, INPUT_QTY



# Conversation states
ADD_PRODUCT, ADD_TABLE, EDIT_PRODUCT, EDIT_TABLE, INPUT_QTY = range(5)

# Data storage
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

PRODUCTS_FILE = os.path.join(DATA_DIR, "products.json")
TABLES_FILE = os.path.join(DATA_DIR, "tables.json")
ORDERS_FILE = os.path.join(DATA_DIR, "orders.json")
ADMINS_FILE = os.path.join(DATA_DIR, "admins.json")

# Initialize logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Myanmar language texts
TEXTS = {
    "welcome": "🍜 KK စားသောက်ဆိုင်\nကြိုဆိုပါသည်",
    "select_table": "ကျေးဇူးပြု၍ စားပွဲရွေးချယ်ပါ",
    "no_tables": "⚠️ စားပွဲမရှိသေးပါ\nအက်မင်မှ စားပွဲထည့်သွင်းပေးပါ",
    "add_table": "➕ စားပွဲအသစ်ထည့်ရန်",
    "back_home": "🔙 မူလစာမျက်နှာ",
    "table_status_available": "🟢",
    "table_status_unavailable": "🔴",
    "no_products": "⚠️ ကုန်ပစ္စည်းမရှိသေးပါ\nအက်မင်မှ ကုန်ပစ္စည်းထည့်သွင်းပေးပါ",
    "back_to_tables": "🔙 စားပွဲစာရင်းသို့",
    "select_product": "မှာယူလိုသော ကုန်ပစ္စည်းကိုရွေးချယ်ပါ",
    "view_cart": "🛒 လှည်းကြည့်ရန်",
    "add_product": "➕ ကုန်အသစ်ထည့်ရန်",
    "select_quantity": "ကျေးဇူးပြု၍ အရေအတွက်ရွေးချယ်ပါ",
    "product_added": "✅ {} (အရေအတွက်: {}) ကို လှည်းထဲသို့ထည့်ပြီးပါပြီ",
    "empty_cart": "🛒 သင့်လှည်းထဲတွင် ပစ္စည်းမရှိသေးပါ",
    "submit_order": "✅ အမှာတင်ပြရန်",
    "edit_cart": "✏️ ပြင်ဆင်ရန်",
    "clear_cart": "🗑 လှည်းရှင်းရန်",
    "order_submitted": "✅ မှာယူမှုအောင်မြင်စွာတင်ပြီးပါပြီ!\n\nအက်မင်မှအတည်ပြုပါမည်",
    "admin_settings": "⚙️ အက်မင်စီမံခန့်ခွဲမှု",
    "product_management": "📦 ကုန်ပစ္စည်းစီမံခန့်ခွဲမှု",
    "table_management": "🪑 စားပွဲစီမံခန့်ခွဲမှု",
    "sales_report": "📊 အရောင်းစာရင်း",
    "add_product_prompt": "📝 ကုန်ပစ္စည်းအသစ်ထည့်သွင်းရန်\n\nကျေးဇူးပြု၍ အောက်ပါပုံစံအတိုင်း ရေးပေးပါ:\nအမည်, ဈေးနှုန်း, အရေအတွက်\n\nဥပမာ: ထမင်းသုပ်, 2000, 50\n\nမပြင်လိုပါက /cancel ရိုက်ထည့်ပါ",
    "invalid_format": "❌ ပုံစံမှားယွင်းနေပါသည်!\n\nကျေးဇူးပြု၍ အောက်ပါပုံစံအတိုင်း ပြန်ရေးပေးပါ:\nအမည်, ဈေးနှုန်း, အရေအတွက်\n\nဥပမာ: ထမင်းသုပ်, 2000, 50\n\nမပြင်လိုပါက /cancel ရိုက်ထည့်ပါ",
    "product_added_success": "✅ {} ကို အောင်မြင်စွာထည့်သွင်းပြီးပါပြီ!",
    "operation_cancelled": "❌ လုပ်ဆောင်မှုကိုဖျက်သိမ်းလိုက်ပါပြီ",
    "new_order_notification": "📦 အသစ်မှာယူမှု (စားပွဲ: {})\n\n{}\n\n💰 စုစုပေါင်း: {} Ks\n⏰ အချိန်: {}",
    "cancel_order": "❌ ပယ်ဖျက်ရန်",
    "bot_added_as_admin": "🤖 Bot ကို Admin အဖြစ်ခန့်အပ်ပြီးပါပြီ!\n\nကျေးဇူးပြု၍ Bot ကို Group Admin အဖြစ်ခန့်အပ်ပေးပါ။"
}

def load_data(filename, default={"data": []}):
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading {filename}: {e}")
    return default

def save_data(data, filename):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving {filename}: {e}")

products = load_data(PRODUCTS_FILE)
tables = load_data(TABLES_FILE)
orders = load_data(ORDERS_FILE)
admins = load_data(ADMINS_FILE, {"admins": [], "group_id": None})

def is_admin(user_id):
    return user_id in admins["admins"]

def is_admin_group(chat_id):
    return chat_id == admins["group_id"]

def is_private_chat(chat_id):
    return chat_id > 0

def get_product_by_id(product_id):
    for product in products["data"]:
        if str(product["id"]) == str(product_id):
            return product
    return None

def get_table_by_id(table_id):
    for table in tables["data"]:
        if str(table["id"]) == str(table_id):
            return table
    return None

def get_current_order(user_id, create_if_not_exists=False):
    for order in orders["data"]:
        if order["user_id"] == user_id and not order.get("submitted", False):
            return order
    
    if create_if_not_exists:
        new_order = {
            "id": len(orders["data"]) + 1,
            "user_id": user_id,
            "items": {},
            "submitted": False,
            "timestamp": datetime.now().isoformat()
        }
        orders["data"].append(new_order)
        return new_order
    return None

async def track_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.new_chat_members:
        for member in update.message.new_chat_members:
            if member.id == context.bot.id:
                group_id = update.message.chat.id
                added_by = update.message.from_user.id
                
                admins["admins"] = [added_by]
                admins["group_id"] = group_id
                save_data(admins, ADMINS_FILE)
                
                await context.bot.send_message(
                    chat_id=group_id,
                    text=TEXTS["bot_added_as_admin"],
                    reply_markup=ReplyKeyboardRemove()
                )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if is_admin_group(chat_id) or (is_private_chat(chat_id) and is_admin(user_id)):
        buttons = [
            [InlineKeyboardButton("🍽️ စားပွဲများ", callback_data='select_table')],
            [InlineKeyboardButton("⚙️ အက်မင်စီမံမှု", callback_data='admin_settings')]
        ]
    else:
        buttons = [
            [InlineKeyboardButton("🍽️ စားပွဲများ", callback_data='select_table')]
        ]
    
    await update.message.reply_text(
        TEXTS["welcome"],
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def show_tables(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    tables_data = tables.get("data", [])
    
    if not tables_data:
        await query.edit_message_text(TEXTS["no_tables"])
        return
    
    buttons = []
    for table in tables_data:
        status = TEXTS["table_status_available"] if table.get("status", "available") == "available" else TEXTS["table_status_unavailable"]
        buttons.append([
            InlineKeyboardButton(
                f"{table['name']} {status}",
                callback_data=f"table_{table['id']}"
            )
        ])
    
    if is_admin(query.from_user.id):
        buttons.append([
            InlineKeyboardButton(TEXTS["add_table"], callback_data='add_table')
        ])
    
    buttons.append([
        InlineKeyboardButton(TEXTS["back_home"], callback_data='back_to_start')
    ])
    
    await query.edit_message_text(
        TEXTS["select_table"],
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, table_id: str):
    query = update.callback_query
    await query.answer()
    
    context.user_data['current_table'] = table_id
    
    products_data = [p for p in products.get("data", []) if p.get("stock", 0) > 0]
    
    if not products_data:
        await query.edit_message_text(
            TEXTS["no_products"],
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(TEXTS["back_to_tables"], callback_data='back_to_tables')]
            ])
        )
        return
    
    buttons = []
    row = []
    for i, product in enumerate(products_data):
        row.append(InlineKeyboardButton(
            f"{product['name']} - {product['price']} Ks",
            callback_data=f"product_{product['id']}"
        ))
        if (i + 1) % 2 == 0:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    
    buttons.append([
        InlineKeyboardButton(TEXTS["view_cart"], callback_data='view_cart'),
        InlineKeyboardButton(TEXTS["back_to_tables"], callback_data='back_to_tables')
    ])
    
    if is_admin(query.from_user.id):
        buttons.append([
            InlineKeyboardButton(TEXTS["add_product"], callback_data='add_product')
        ])
    
    await query.edit_message_text(
        TEXTS["select_product"],
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def select_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    product_id = query.data.split('_')[1]
    product = get_product_by_id(product_id)
    
    if not product:
        await query.edit_message_text("❌ ကုန်ပစ္စည်းမတွေ့ပါ")
        return
    
    context.user_data['current_product'] = product_id
    
    buttons = [
        [InlineKeyboardButton(str(i), callback_data=f"qty_{i}") for i in range(1, 6)],
        [InlineKeyboardButton("🔙 နောက်သို့", callback_data='back_to_menu')]
    ]
    
    await query.edit_message_text(
        f"{TEXTS['select_quantity']}\n\n"
        f"ကုန်ပစ္စည်း: {product['name']}\n"
        f"ဈေးနှုန်း: {product['price']} Ks",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    qty = int(query.data.split('_')[1])
    user_id = query.from_user.id
    product_id = context.user_data['current_product']
    table_id = context.user_data['current_table']
    
    product = get_product_by_id(product_id)
    if not product:
        await query.edit_message_text("❌ ကုန်ပစ္စည်းမတွေ့ပါ")
        return
    
    current_order = get_current_order(user_id, create_if_not_exists=True)
    if product_id in current_order['items']:
        current_order['items'][product_id] += qty
    else:
        current_order['items'][product_id] = qty
    
    save_data(orders, ORDERS_FILE)
    
    await query.edit_message_text(
        TEXTS["product_added"].format(product['name'], qty),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(TEXTS["view_cart"], callback_data='view_cart')],
            [InlineKeyboardButton("🔙 မနူးအူဆိုင်မျက်နှာ", callback_data='back_to_menu')]
        ])
    )

async def view_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    current_order = get_current_order(user_id)
    
    if not current_order or not current_order.get('items'):
        await query.edit_message_text(TEXTS["empty_cart"])
        return
    
    message = "🛒 သင့်လှည်း:\n\n"
    total = 0
    
    for product_id, qty in current_order['items'].items():
        product = get_product_by_id(product_id)
        if product:
            item_total = product['price'] * qty
            total += item_total
            message += f"▪️ {product['name']} - {qty} x {product['price']} = {item_total} Ks\n"
    
    message += f"\n💰 စုစုပေါင်း: {total} Ks"
    
    buttons = [
        [InlineKeyboardButton(TEXTS["submit_order"], callback_data='submit_order')],
        [InlineKeyboardButton(TEXTS["edit_cart"], callback_data='edit_cart')],
        [InlineKeyboardButton(TEXTS["clear_cart"], callback_data='clear_cart')],
        [InlineKeyboardButton("🔙 နောက်သို့", callback_data='back_to_menu')]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def submit_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    current_order = get_current_order(user_id)
    
    if not current_order or not current_order.get('items'):
        await query.edit_message_text("❌ မှာယူမှုမရှိပါ")
        return
    
    table = get_table_by_id(context.user_data['current_table'])
    table_name = table['name'] if table else "Unknown"
    
    message = f"📦 အသစ်မှာယူမှု (စားပွဲ: {table_name})\n\n"
    total = 0
    
    for product_id, qty in current_order['items'].items():
        product = get_product_by_id(product_id)
        if product:
            item_total = product['price'] * qty
            total += item_total
            message += f"▪️ {product['name']} - {qty} x {product['price']} = {item_total} Ks\n"
            product['stock'] -= qty
    
    message += f"\n💰 စုစုပေါင်း: {total} Ks\n"
    message += f"⏰ အချိန်: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    current_order['submitted'] = True
    current_order['total'] = total
    current_order['completed_at'] = datetime.now().isoformat()
    
    save_data(products, PRODUCTS_FILE)
    save_data(orders, ORDERS_FILE)
    
    if admins.get("group_id"):
        cancel_button = InlineKeyboardButton(
            TEXTS["cancel_order"], 
            callback_data=f"cancel_{current_order['id']}"
        )
        await context.bot.send_message(
            chat_id=admins["group_id"],
            text=message,
            reply_markup=InlineKeyboardMarkup([[cancel_button]])
        )
    
    await query.edit_message_text(
        TEXTS["order_submitted"],
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 မူလစာမျက်နှာ", callback_data='back_to_start')]
        ])
    )

async def admin_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    buttons = [
        [InlineKeyboardButton(TEXTS["product_management"], callback_data='manage_products')],
        [InlineKeyboardButton(TEXTS["table_management"], callback_data='manage_tables')],
        [InlineKeyboardButton(TEXTS["sales_report"], callback_data='view_reports')],
        [InlineKeyboardButton("🏠 မူလစာမျက်နှာ", callback_data='back_to_start')]
    ]
    
    await query.edit_message_text(
        TEXTS["admin_settings"],
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def manage_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    buttons = [
        [InlineKeyboardButton(TEXTS["add_product"], callback_data='add_product')],
        [InlineKeyboardButton("✏️ ကုန်ပစ္စည်းပြင်ဆင်ရန်", callback_data='edit_products')],
        [InlineKeyboardButton("🗑 ကုန်ပစ္စည်းဖျက်ရန်", callback_data='delete_products')],
        [InlineKeyboardButton("🔙 အက်မင်မီနူး", callback_data='admin_settings')]
    ]
    
    await query.edit_message_text(
        TEXTS["product_management"],
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def add_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        TEXTS["add_product_prompt"],
        reply_markup=ReplyKeyboardRemove()
    )
    
    return ADD_PRODUCT

async def save_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        name, price, stock = [x.strip() for x in update.message.text.split(',')]
        
        new_product = {
            "id": len(products["data"]) + 1,
            "name": name,
            "price": int(price),
            "stock": int(stock),
            "created_at": datetime.now().isoformat()
        }
        
        products["data"].append(new_product)
        save_data(products, PRODUCTS_FILE)
        
        await update.message.reply_text(
            TEXTS["product_added_success"].format(name),
            reply_markup=ReplyKeyboardRemove()
        )
        
        return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(
            TEXTS["invalid_format"],
            reply_markup=ReplyKeyboardRemove()
        )
        return ADD_PRODUCT

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        TEXTS["operation_cancelled"],
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

async def back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await start(update, context)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == 'select_table':
        await show_tables(update, context)
    elif data == 'admin_settings':
        await admin_settings(update, context)
    elif data.startswith('table_'):
        table_id = data.split('_')[1]
        await show_menu(update, context, table_id)
    elif data.startswith('product_'):
        await select_product(update, context)
    elif data.startswith('qty_'):
        await add_to_cart(update, context)
    elif data == 'view_cart':
        await view_cart(update, context)
    elif data == 'submit_order':
        await submit_order(update, context)
    elif data == 'back_to_start':
        await back_to_start(update, context)
    elif data == 'manage_products':
        await manage_products(update, context)
    elif data == 'add_product':
        await add_product(update, context)

def main():
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, track_chats))
    
    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(add_product, pattern="^add_product$")
        ],
        states={
            ADD_PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_product)]
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)]
    )
    
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(button_click))
    
    application.run_polling()

if __name__ == '__main__':
    main()
