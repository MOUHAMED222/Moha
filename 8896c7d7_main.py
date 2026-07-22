import logging
import sqlite3
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, LabeledPrice
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, PreCheckoutQueryHandler, filters

# ============ الإعدادات ============
BOT_TOKEN = '8792730780:AAGwn5EOQqF-jbNYwrmy71sp2c5-hYP6kF0'
DEVELOPER_ID = 8771830614
ADMIN_IDS = [8771830614]
DAILY_GIFT_POINTS = 100
REFERRAL_POINTS = 100
POINTS_PER_SUBSCRIBER = 30
MIN_SUBS_LIMIT = 50
MAX_SUBS_LIMIT = 1000
SUPPORT_USER = "@EF_TP"
CODES_CHANNEL = "@ET_PF"

# أسعار النجوم الجديدة بناءً على الصورة (1 نجمة = 120 نقطة)
STARS_CONFIG = [
    (120, 1),
    (240, 2),
    (600, 5),
    (1200, 10),
    (2400, 20),
    (6000, 50),
    (12000, 100),
    (30000, 250),
    (60000, 500),
    (120000, 1000)
]

# ============ تسجيل الأحداث ============
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ============ قاعدة البيانات ============
def get_db():
    conn = sqlite3.connect("bot.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            points INTEGER DEFAULT 0,
            invited_by INTEGER,
            daily_gift_last TEXT
        );
        CREATE TABLE IF NOT EXISTS channels (
            channel_id INTEGER PRIMARY KEY,
            channel_name TEXT,
            channel_username TEXT,
            invite_link TEXT,
            points_per_sub INTEGER DEFAULT 10,
            owner_id INTEGER,
            requested_subs INTEGER DEFAULT 0,
            current_subs INTEGER DEFAULT 0,
            is_service INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active'
        );
        CREATE TABLE IF NOT EXISTS subscriptions (
            user_id INTEGER,
            channel_id INTEGER,
            PRIMARY KEY (user_id, channel_id)
        );
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            channel_id INTEGER,
            channel_link TEXT,
            requested_subs INTEGER,
            current_subs INTEGER DEFAULT 0,
            points_spent INTEGER,
            status TEXT DEFAULT 'active',
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS gift_codes (
            code TEXT PRIMARY KEY,
            points INTEGER,
            usage_limit INTEGER,
            used_count INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS code_usage (
            user_id INTEGER,
            code TEXT,
            PRIMARY KEY (user_id, code)
        );
    ''')
    conn.commit()
    conn.close()

# ============ دوال قاعدة البيانات ============
def get_user(user_id):
    conn = get_db(); user = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone(); conn.close(); return user

def create_user(user_id, username=None, invited_by=None):
    conn = get_db(); conn.execute("INSERT OR IGNORE INTO users (user_id, username, invited_by) VALUES (?, ?, ?)", (user_id, username, invited_by)); conn.commit(); conn.close()

def update_points(user_id, amount):
    conn = get_db(); conn.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (amount, user_id)); conn.commit(); conn.close()

def get_total_users():
    conn = get_db(); count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]; conn.close(); return count

def get_completed_orders_count():
    conn = get_db(); count = conn.execute("SELECT COUNT(*) FROM orders WHERE status = 'completed'").fetchone()[0]; conn.close(); return count

def get_available_channels(user_id):
    conn = get_db(); channels = conn.execute("SELECT * FROM channels WHERE status = 'active' AND channel_id NOT IN (SELECT channel_id FROM subscriptions WHERE user_id = ?) AND owner_id != ?", (user_id, user_id)).fetchall(); conn.close(); return channels

def get_channel(channel_id):
    conn = get_db(); ch = conn.execute("SELECT * FROM channels WHERE channel_id = ?", (channel_id,)).fetchone(); conn.close(); return ch

def add_subscription(user_id, channel_id):
    conn = get_db(); conn.execute("INSERT OR IGNORE INTO subscriptions (user_id, channel_id) VALUES (?, ?)", (user_id, channel_id)); conn.commit(); conn.close()

def is_subscribed(user_id, channel_id):
    conn = get_db(); row = conn.execute("SELECT 1 FROM subscriptions WHERE user_id = ? AND channel_id = ?", (user_id, channel_id)).fetchone(); conn.close(); return row is not None

def get_gift_code(code):
    conn = get_db(); gc = conn.execute("SELECT * FROM gift_codes WHERE code = ?", (code,)).fetchone(); conn.close(); return gc

def has_used_code(user_id, code):
    conn = get_db(); row = conn.execute("SELECT 1 FROM code_usage WHERE user_id = ? AND code = ?", (user_id, code)).fetchone(); conn.close(); return row is not None

def use_gift_code(user_id, code):
    conn = get_db(); conn.execute("UPDATE gift_codes SET used_count = used_count + 1 WHERE code = ?", (code,)); conn.execute("INSERT OR IGNORE INTO code_usage (user_id, code) VALUES (?, ?)", (user_id, code)); conn.commit(); conn.close()

def add_channel_db(channel_id, channel_name, channel_username, invite_link, points_per_sub, owner_id=0, requested_subs=0, is_service=0):
    conn = get_db(); conn.execute("INSERT OR REPLACE INTO channels (channel_id, channel_name, channel_username, invite_link, points_per_sub, owner_id, requested_subs, current_subs, is_service, status) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, 'active')", (channel_id, channel_name, channel_username, invite_link, points_per_sub, owner_id, requested_subs, is_service)); conn.commit(); conn.close()

def add_order(user_id, channel_id, channel_link, requested_subs, points_spent):
    conn = get_db(); conn.execute("INSERT INTO orders (user_id, channel_id, channel_link, requested_subs, points_spent, created_at) VALUES (?, ?, ?, ?, ?, ?)", (user_id, channel_id, channel_link, requested_subs, points_spent, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))); conn.commit(); conn.close()

def increment_channel_subs(channel_id):
    conn = get_db(); conn.execute("UPDATE channels SET current_subs = current_subs + 1 WHERE channel_id = ?", (channel_id,)); channel = conn.execute("SELECT * FROM channels WHERE channel_id = ?", (channel_id,)).fetchone()
    if channel and channel["is_service"] == 1 and channel["current_subs"] >= channel["requested_subs"]:
        conn.execute("UPDATE channels SET status = 'completed' WHERE channel_id = ?", (channel_id,))
        conn.execute("UPDATE orders SET status = 'completed', current_subs = ? WHERE channel_id = ? AND status = 'active'", (channel["current_subs"], channel_id))
    conn.commit(); conn.close(); return channel

def get_user_orders(user_id):
    conn = get_db(); orders = conn.execute("SELECT * FROM orders WHERE user_id = ?", (user_id,)).fetchall(); conn.close(); return orders

def get_all_orders():
    conn = get_db(); orders = conn.execute("SELECT orders.*, users.username FROM orders LEFT JOIN users ON orders.user_id = users.user_id ORDER BY order_id DESC").fetchall(); conn.close(); return orders

def delete_channel_db(channel_id):
    conn = get_db(); conn.execute("DELETE FROM channels WHERE channel_id = ?", (channel_id,)); conn.commit(); conn.close()

def get_total_points():
    conn = get_db(); total = conn.execute("SELECT SUM(points) FROM users").fetchone()[0]; conn.close(); return total or 0

def set_daily_gift(user_id):
    conn = get_db(); conn.execute("UPDATE users SET daily_gift_last = ? WHERE user_id = ?", (datetime.now().strftime("%Y-%m-%d"), user_id)); conn.commit(); conn.close()

def get_referral_count(user_id):
    conn = get_db(); count = conn.execute("SELECT COUNT(*) FROM users WHERE invited_by = ?", (user_id,)).fetchone()[0]; conn.close(); return count

def add_gift_code_db(code, points, limit):
    conn = get_db(); conn.execute("INSERT OR REPLACE INTO gift_codes (code, points, usage_limit) VALUES (?, ?, ?)", (code, points, limit)); conn.commit(); conn.close()

# ============ القوالب الملونة الفائقة الاستقرار ============
def main_menu_keyboard(user_id):
    user = get_user(user_id); points = user["points"] if user else 0; completed = get_completed_orders_count()
    keyboard = [
        [InlineKeyboardButton(f"💰 رصيدك: {points} نقطة", callback_data="refresh_menu", style="success")],
        [InlineKeyboardButton("🎁 هدية يومية", callback_data="daily_gift", style="primary"), InlineKeyboardButton("🎉 دعوة أصدقاء", callback_data="invite", style="primary")],
        [InlineKeyboardButton("🔑 كود هدية", callback_data="gift_code", style="primary"), InlineKeyboardButton("📢 اشترك قناة", callback_data="subscribe", style="primary")],
        [InlineKeyboardButton("🚀 طلب خدمة", callback_data="service_menu", style="success")],
        [InlineKeyboardButton("🛒 شراء نقاط", callback_data="buy_menu", style="primary"), InlineKeyboardButton("🔄 تحويل نقاط", callback_data="transfer", style="primary")],
        [InlineKeyboardButton("📦 طلباتي", callback_data="my_orders", style="primary"), InlineKeyboardButton("📊 إحصائياتي", callback_data="stats", style="primary")],
        [InlineKeyboardButton("🔧 الدعم الفني", url=f"https://t.me/{SUPPORT_USER.replace('@', '')}", style="primary"), InlineKeyboardButton("📢 قناة الأكواد", url=f"https://t.me/{CODES_CHANNEL.replace('@', '')}", style="primary")],
        [InlineKeyboardButton(f"✅ طلبات مكتملة: {completed}", callback_data="completed", style="success")],
    ]
    if user_id == DEVELOPER_ID: keyboard.append([InlineKeyboardButton("👑 لوحة المطور", callback_data="dev_panel", style="danger")])
    return InlineKeyboardMarkup(keyboard)

def service_menu_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("👥 طلب مشتركين تليجرام", callback_data="service_telegram", style="primary")], [InlineKeyboardButton("🔙 رجوع", callback_data="main_menu", style="danger")]])

def buy_menu_keyboard():
    keyboard = []
    for pts, stars in STARS_CONFIG:
        keyboard.append([InlineKeyboardButton(f"{pts} نقطة ⬅️ ⭐ {stars}", callback_data=f"buy_stars_{pts}_{stars}", style="success")])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="main_menu", style="danger")])
    return InlineKeyboardMarkup(keyboard)

def developer_panel_keyboard():
    keyboard = [
        [InlineKeyboardButton("📢 إضافة قناة", callback_data="dev_addchannel", style="primary"), InlineKeyboardButton("🗑 إزالة قناة", callback_data="dev_delchannel", style="primary")],
        [InlineKeyboardButton("💰 إضافة نقاط", callback_data="dev_addpoints", style="success"), InlineKeyboardButton("💸 خصم نقاط", callback_data="dev_subpoints", style="danger")],
        [InlineKeyboardButton("🎁 إنشاء كود هدية", callback_data="dev_create_gift", style="success"), InlineKeyboardButton("📦 الطلبات", callback_data="dev_orders", style="primary")],
        [InlineKeyboardButton("📊 إحصائيات", callback_data="dev_info", style="primary"), InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="main_menu", style="danger")],
    ]
    return InlineKeyboardMarkup(keyboard)

def back_button_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="main_menu", style="danger")]])

# ============ دالة الاستجابة الفائقة (ثبات مطلق) ============
async def respond(update: Update, context: ContextTypes.DEFAULT_TYPE, text, reply_markup):
    user_id = update.effective_user.id
    if update.callback_query:
        try: await update.callback_query.message.delete()
        except: pass
    await context.bot.send_message(chat_id=user_id, text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

# ============ المعالجات ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id; username = update.effective_user.username; invited_by = None
    if context.args and context.args[0].startswith("ref_"):
        try:
            ref_id = int(context.args[0].replace("ref_", ""))
            if ref_id != user_id: invited_by = ref_id
        except: pass
    if not get_user(user_id):
        create_user(user_id, username, invited_by)
        if invited_by:
            update_points(invited_by, REFERRAL_POINTS); update_points(user_id, REFERRAL_POINTS)
            try: await context.bot.send_message(chat_id=invited_by, text=f"🎉 صديقك @{username or 'مستخدم جديد'} انضم عبر رابطك! حصلت على {REFERRAL_POINTS} نقطة.")
            except: pass
    user = get_user(user_id); total = get_total_users()
    text = f"🆔 <b>آيديك:</b> <code>{user_id}</code>\n💰 <b>رصيدك:</b> <code>{user['points']} نقطة</code>\n👥 <b>المستخدمون:</b> <code>{total:,}</code>\n━━━━━━━━━━━━━━━━━━\n\n✨ <b>يمكنك:</b>\n🎉 جمع النقاط بالدعوة والاشتراك\n🚀 شراء خدمات بنقاطك\n🛒 شحن النقاط بطرق متعددة\n🔄 تحويل نقاط لأصدقائك\n\n━━━━━━━━━━━━━━━━━━\n\n👇 <b>اختر من القائمة:</b>"
    await context.bot.send_message(chat_id=user_id, text=text, reply_markup=main_menu_keyboard(user_id), parse_mode=ParseMode.HTML)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; user_id = query.from_user.id; data = query.data
    
    if data == "main_menu" or data == "refresh_menu":
        user = get_user(user_id); total = get_total_users()
        text = f"🆔 <b>آيديك:</b> <code>{user_id}</code>\n💰 <b>رصيدك:</b> <code>{user['points']} نقطة</code>\n👥 <b>المستخدمون:</b> <code>{total:,}</code>\n━━━━━━━━━━━━━━━━━━\n\n✨ <b>يمكنك:</b>\n🎉 جمع النقاط بالدعوة والاشتراك\n🚀 شراء خدمات بنقاطك\n🛒 شحن النقاط بطرق متعددة\n🔄 تحويل نقاط لأصدقائك\n\n━━━━━━━━━━━━━━━━━━\n\n👇 <b>اختر من القائمة:</b>"
        await respond(update, context, text, main_menu_keyboard(user_id))
    elif data == "buy_menu":
        text = "💰 <b>كل نجمة = 120 نقطة</b>\n\n━━━━━━━━━━━━━━━━━━\n\n👇 <b>اختر عدد النجوم:</b>"
        await respond(update, context, text, buy_menu_keyboard())
    elif data.startswith("buy_stars_"):
        parts = data.split("_"); pts = int(parts[2]); stars = int(parts[3])
        title = f"شراء {pts} نقطة"; description = f"شحن {pts} نقطة في البوت"; payload = f"buy_{pts}"; currency = "XTR"
        prices = [LabeledPrice("النقاط", stars)]
        await context.bot.send_invoice(chat_id=user_id, title=title, description=description, payload=payload, provider_token="", currency=currency, prices=prices)
    elif data == "service_menu": await respond(update, context, "🚀 <b>قائمة الخدمات المتاحة:</b>\nاختر الخدمة المطلوبة:", service_menu_keyboard())
    elif data == "service_telegram":
        user = get_user(user_id); text = f"👥 <b>طلب مشتركين تليجرام</b>\n\n⚠️ يجب إضافة البوت مشرفاً في القناة أولاً مع صلاحية الدعوة.\n\n💰 التكلفة: {POINTS_PER_SUBSCRIBER} نقطة لكل مشترك\n💳 رصيدك الحالي: {user['points']} نقطة\n\n📝 أرسل يوزر قناتك (مثال: @mychannel):"
        context.user_data["state"] = "awaiting_channel_username"; await respond(update, context, text, back_button_keyboard())
    elif data == "daily_gift":
        user = get_user(user_id); today = datetime.now().strftime("%Y-%m-%d")
        if user["daily_gift_last"] == today: await respond(update, context, "⚠️ لقد حصلت على هديتك اليوم بالفعل. عد غداً!", back_button_keyboard())
        else:
            update_points(user_id, DAILY_GIFT_POINTS); set_daily_gift(user_id)
            await respond(update, context, f"🎁 حصلت على {DAILY_GIFT_POINTS} نقطة هدية يومية!", back_button_keyboard())
    elif data == "invite":
        bot_info = await context.bot.get_me(); invite_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"
        text = f"🎉 <b>دعوة أصدقاء</b>\n\n💰 ستحصل على {REFERRAL_POINTS} نقطة لكل صديق ينضم عبر رابطك.\n\n🔗 <b>رابط الدعوة الخاص بك:</b>\n<code>{invite_link}</code>"
        await respond(update, context, text, back_button_keyboard())
    elif data == "subscribe":
        channels = get_available_channels(user_id)
        if not channels: await respond(update, context, "❌ لا توجد قنوات متاحة للاشتراك حالياً.", back_button_keyboard())
        else:
            keyboard = []
            for ch in channels: keyboard.append([InlineKeyboardButton(f"📢 {ch['channel_name']} (+{ch['points_per_sub']} نقطة)", callback_data=f"sub_{ch['channel_id']}", style="primary")])
            keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="main_menu", style="danger")])
            await respond(update, context, "📢 اختر قناة للاشتراك وكسب النقاط:", InlineKeyboardMarkup(keyboard))
    elif data.startswith("sub_"):
        channel_id = int(data.replace("sub_", "")); channel = get_channel(channel_id)
        if not channel or channel["status"] != "active": await respond(update, context, "❌ هذه القناة لم تعد متاحة.", back_button_keyboard())
        else:
            try:
                member = await context.bot.get_chat_member(chat_id=channel_id, user_id=user_id)
                if member.status in ["member", "administrator", "creator"]:
                    if not is_subscribed(user_id, channel_id):
                        add_subscription(user_id, channel_id); update_points(user_id, channel["points_per_sub"]); increment_channel_subs(channel_id)
                        await respond(update, context, f"✅ تم! اشتركت في {channel['channel_name']} وحصلت على {channel['points_per_sub']} نقطة!", back_button_keyboard())
                    else: await respond(update, context, "⚠️ أنت مشترك بالفعل.", back_button_keyboard())
                else:
                    invite_link = channel["invite_link"] or f"https://t.me/{channel['channel_username']}"
                    keyboard = [[InlineKeyboardButton("📢 اشترك في القناة", url=invite_link, style="success")], [InlineKeyboardButton("✅ تحقق من اشتراكي", callback_data=f"sub_{channel_id}", style="primary")], [InlineKeyboardButton("🔙 رجوع", callback_data="main_menu", style="danger")]]
                    await respond(update, context, f"⚠️ يجب الاشتراك في قناة {channel['channel_name']} أولاً:", InlineKeyboardMarkup(keyboard))
            except: await respond(update, context, "❌ حدث خطأ. تأكد أن البوت مشرف في القناة.", back_button_keyboard())
    elif data == "gift_code": context.user_data["state"] = "awaiting_gift_code"; await respond(update, context, "🔑 أدخل كود الهدية:", back_button_keyboard())
    elif data == "transfer": context.user_data["state"] = "awaiting_transfer_id"; await respond(update, context, "🔄 أدخل آيدي المستخدم الذي تريد التحويل إليه:", back_button_keyboard())
    elif data == "stats":
        user = get_user(user_id); referrals = get_referral_count(user_id); orders = get_user_orders(user_id)
        await respond(update, context, f"📊 <b>إحصائياتك:</b>\n\n💰 رصيدك: {user['points']} نقطة\n👥 المدعوين: {referrals}\n📦 طلباتك: {len(orders)}", back_button_keyboard())
    elif data == "my_orders":
        orders = get_user_orders(user_id)
        if not orders: await respond(update, context, "📦 لم تقدم أي طلبات بعد.", back_button_keyboard())
        else:
            text = "📦 <b>طلباتك:</b>\n\n"
            for o in orders: text += f"• {o['channel_link']} - {o['requested_subs']} مشترك - {'✅ مكتمل' if o['status'] == 'completed' else f'⏳ {o['current_subs']}/{o['requested_subs']}'}\n"
            await respond(update, context, text, back_button_keyboard())
    elif data == "completed": await respond(update, context, f"✅ عدد الطلبات المكتملة: {get_completed_orders_count()}", back_button_keyboard())
    elif data == "dev_panel":
        if user_id != DEVELOPER_ID: return
        await respond(update, context, "👑 لوحة تحكم المطور:", developer_panel_keyboard())
    elif data == "dev_create_gift":
        if user_id != DEVELOPER_ID: return
        context.user_data["state"] = "dev_awaiting_gift_data"
        await respond(update, context, "🎁 <b>إنشاء كود هدية</b>\n\nأرسل بيانات الكود بالتنسيق التالي:\n(الكود | النقاط | عدد المرات)\n\nمثال:\nFREE100 | 100 | 50", InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="dev_panel", style="danger")]]))
    elif data == "dev_info":
        if user_id != DEVELOPER_ID: return
        total = get_total_users(); total_pts = get_total_points()
        await respond(update, context, f"👑 <b>معلومات البوت:</b>\n\n🤖 المطور: {DEVELOPER_ID}\n👥 المستخدمين: {total}\n💰 إجمالي النقاط: {total_pts}", developer_panel_keyboard())
    elif data == "dev_addchannel":
        if user_id != DEVELOPER_ID: return
        context.user_data["state"] = "dev_awaiting_addchannel"; await respond(update, context, "📢 إضافة قناة إجبارية\n\nأرسل يوزر القناة ونقاط الإشتراك:\n(يوزر القناة | النقاط)\n\nمثال:\n@mychannel | 10", InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="dev_panel", style="danger")]]))
    elif data == "dev_delchannel":
        if user_id != DEVELOPER_ID: return
        context.user_data["state"] = "dev_awaiting_delchannel"; await respond(update, context, "🗑 إزالة قناة إجبارية\n\nأرسل يوزر القناة المراد إزالتها:\n(مثال: @mychannel)", InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="dev_panel", style="danger")]]))
    elif data == "dev_addpoints":
        if user_id != DEVELOPER_ID: return
        context.user_data["state"] = "dev_awaiting_addpoints"; await respond(update, context, "💰 إضافة نقاط لمستخدم\n\nأرسل: آيدي المستخدم | عدد النقاط", InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="dev_panel", style="danger")]]))
    elif data == "dev_subpoints":
        if user_id != DEVELOPER_ID: return
        context.user_data["state"] = "dev_awaiting_subpoints"; await respond(update, context, "💸 خصم نقاط من مستخدم\n\nأرسل: آيدي المستخدم | عدد النقاط", InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="dev_panel", style="danger")]]))
    elif data == "dev_orders":
        if user_id != DEVELOPER_ID: return
        orders = get_all_orders(); text = "📦 <b>قائمة الطلبات (آخر 10):</b>\n\n"
        for o in orders[:10]:
            username = f"@{o['username']}" if o['username'] else f"ID:{o['user_id']}"
            text += f"• {username} | {o['channel_link']} | {o['requested_subs']} مشترك | {o['status']}\n"
        await respond(update, context, text, developer_panel_keyboard())

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    if query.invoice_payload.startswith("buy_"): await query.answer(ok=True)
    else: await query.answer(ok=False, error_message="حدث خطأ في العملية.")

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment = update.message.successful_payment; payload = payment.invoice_payload
    if payload.startswith("buy_"):
        pts = int(payload.replace("buy_", "")); user_id = update.effective_user.id
        update_points(user_id, pts)
        await update.message.reply_text(f"✅ تم بنجاح! تم شحن {pts:,} نقطة إلى حسابك. شكراً لك! ⭐", reply_markup=main_menu_keyboard(user_id))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id; text = update.message.text; state = context.user_data.get("state", "")
    if state == "awaiting_gift_code":
        context.user_data["state"] = ""; code = get_gift_code(text.strip())
        if not code or code["used_count"] >= code["usage_limit"] or has_used_code(user_id, text.strip()): await update.message.reply_text("❌ كود غير صالح أو مستخدم.", reply_markup=back_button_keyboard())
        else:
            use_gift_code(user_id, text.strip()); update_points(user_id, code["points"])
            await update.message.reply_text(f"🎉 تهانينا! حصلت على {code['points']} نقطة!", reply_markup=back_button_keyboard())
    elif state == "dev_awaiting_gift_data":
        context.user_data["state"] = ""
        try:
            p = [i.strip() for i in text.split("|")]; add_gift_code_db(p[0], int(p[1]), int(p[2]))
            await update.message.reply_text(f"✅ تم إنشاء كود الهدية:\n🎁 الكود: {p[0]}\n💰 النقاط: {p[1]}\n👥 المرات: {p[2]}", reply_markup=developer_panel_keyboard())
        except: await update.message.reply_text("❌ خطأ في البيانات.", reply_markup=developer_panel_keyboard())
    elif state == "awaiting_channel_username":
        context.user_data["state"] = ""; channel_input = text.strip().replace("@", "").replace("https://t.me/", "")
        try:
            chat = await context.bot.get_chat(f"@{channel_input}"); channel_id = chat.id; channel_name = chat.title or channel_input
            bot_me = await context.bot.get_me(); bot_member = await context.bot.get_chat_member(chat_id=channel_id, user_id=bot_me.id)
            if bot_member.status not in ["administrator", "creator"] or not (bot_member.can_invite_users or bot_member.status == "creator"): await update.message.reply_text("❌ البوت ليس مشرفاً أو لا يملك صلاحية الدعوة!", reply_markup=back_button_keyboard())
            else:
                context.user_data["state"] = "awaiting_subs_count"; context.user_data["service_channel_id"] = channel_id; context.user_data["service_channel_name"] = channel_name; context.user_data["service_channel_username"] = channel_input
                user = get_user(user_id); max_subs = user["points"] // POINTS_PER_SUBSCRIBER
                await update.message.reply_text(f"✅ تم التحقق!\n💰 رصيدك: {user['points']} نقطة\n👥 الحد الأقصى: {max_subs} مشترك\n📝 كم المطلوب؟", reply_markup=back_button_keyboard())
        except: await update.message.reply_text("❌ لم أتمكن من الوصول للقناة!", reply_markup=back_button_keyboard())
    elif state == "awaiting_subs_count":
        context.user_data["state"] = ""
        try:
            requested_subs = int(text.strip())
            if requested_subs < MIN_SUBS_LIMIT or requested_subs > MAX_SUBS_LIMIT:
                await update.message.reply_text(f"❌ يجب أن يكون عدد المشتركين بين {MIN_SUBS_LIMIT} و {MAX_SUBS_LIMIT}.", reply_markup=back_button_keyboard())
                return
            
            points_needed = requested_subs * POINTS_PER_SUBSCRIBER; user = get_user(user_id)
            if user["points"] < points_needed:
                await update.message.reply_text("❌ رصيدك غير كافي.", reply_markup=back_button_keyboard())
            else:
                channel_id = context.user_data["service_channel_id"]; channel_name = context.user_data["service_channel_name"]; channel_username = context.user_data["service_channel_username"]
                update_points(user_id, -points_needed); add_channel_db(channel_id, channel_name, channel_username, f"https://t.me/{channel_username}", POINTS_PER_SUBSCRIBER, user_id, requested_subs, 1); add_order(user_id, channel_id, f"@{channel_username}", requested_subs, points_needed)
                await update.message.reply_text("✅ تم استلام طلبك بنجاح!", reply_markup=back_button_keyboard())
        except: await update.message.reply_text("❌ أدخل رقماً صحيحاً.", reply_markup=back_button_keyboard())
    elif state == "awaiting_transfer_id":
        context.user_data["state"] = ""
        try:
            recipient_id = int(text.strip())
            if recipient_id == user_id or not get_user(recipient_id): await update.message.reply_text("❌ آيدي غير صالح.", reply_markup=back_button_keyboard())
            else: context.user_data["state"] = "awaiting_transfer_amount"; context.user_data["transfer_to"] = recipient_id; await update.message.reply_text("💰 أدخل عدد النقاط:", reply_markup=back_button_keyboard())
        except: await update.message.reply_text("❌ آيدي غير صالح.", reply_markup=back_button_keyboard())
    elif state == "awaiting_transfer_amount":
        context.user_data["state"] = ""
        try:
            amount = int(text.strip()); user = get_user(user_id)
            if amount <= 0 or user["points"] < amount: await update.message.reply_text("❌ رصيدك غير كافي.", reply_markup=back_button_keyboard())
            else:
                recipient_id = context.user_data.get("transfer_to"); update_points(user_id, -amount); update_points(recipient_id, amount)
                await update.message.reply_text(f"✅ تم تحويل {amount} نقطة!", reply_markup=back_button_keyboard())
                try: await context.bot.send_message(recipient_id, f"💰 حصلت على {amount} نقطة من {user_id}!")
                except: pass
        except: await update.message.reply_text("❌ أدخل رقماً صحيحاً.", reply_markup=back_button_keyboard())
    elif state == "dev_awaiting_addchannel":
        context.user_data["state"] = ""
        try:
            parts = [p.strip() for p in text.split("|")]; username = parts[0].replace("@", "").replace("https://t.me/", ""); pts = int(parts[1])
            chat = await context.bot.get_chat(f"@{username}"); add_channel_db(chat.id, chat.title, username, f"https://t.me/{username}", pts)
            await update.message.reply_text(f"✅ تمت إضافة القناة: {chat.title}", reply_markup=developer_panel_keyboard())
        except: await update.message.reply_text("❌ خطأ! تأكد من اليوزر وأن البوت مشرف في القناة.", reply_markup=developer_panel_keyboard())
    elif state == "dev_awaiting_delchannel":
        context.user_data["state"] = ""; username = text.strip().replace("@", "").replace("https://t.me/", "")
        try:
            chat = await context.bot.get_chat(f"@{username}"); delete_channel_db(chat.id)
            await update.message.reply_text(f"✅ تم حذف القناة بنجاح.", reply_markup=developer_panel_keyboard())
        except: await update.message.reply_text("❌ القناة غير موجودة.", reply_markup=developer_panel_keyboard())
    elif state == "dev_awaiting_addpoints":
        context.user_data["state"] = ""
        try:
            p = [i.strip() for i in text.split("|")]; update_points(int(p[0]), int(p[1]))
            await update.message.reply_text(f"✅ تم إضافة {p[1]} نقطة للمستخدم {p[0]}", reply_markup=developer_panel_keyboard())
        except: await update.message.reply_text("❌ خطأ في البيانات.", reply_markup=developer_panel_keyboard())
    elif state == "dev_awaiting_subpoints":
        context.user_data["state"] = ""
        try:
            p = [i.strip() for i in text.split("|")]; update_points(int(p[0]), -int(p[1]))
            await update.message.reply_text(f"✅ تم خصم {p[1]} نقطة من المستخدم {p[0]}", reply_markup=developer_panel_keyboard())
        except: await update.message.reply_text("❌ خطأ في البيانات.", reply_markup=developer_panel_keyboard())
    else: await update.message.reply_text("👇 استخدم القائمة:", reply_markup=main_menu_keyboard(user_id))

def main():
    init_db(); app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start)); app.add_handler(CallbackQueryHandler(button_handler)); app.add_handler(PreCheckoutQueryHandler(precheckout_callback)); app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback)); app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ البوت يعمل الآن..."); app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__": main()
