#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# بوت إدارة الاشتراكات (pyTelegramBotAPI) - By: Radwan

import sys, time, logging, sqlite3, hashlib, json, urllib.request, functools, traceback
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import telebot
from telebot import types
from apscheduler.schedulers.background import BackgroundScheduler

# ─── إعدادات (عدّل القيم دي مباشرة) ─────────────────────────
BOT_TOKEN       = "8237399405:AAFA08ZHMqBvKnRDAgAsOeToRNspI-2gnXU"   # ← من BotFather
ADMIN_ID        = 654471191              # ← الـ ID بتاعك
GROUP_ID        = -1002935801335
ADMIN_PASS      = "263200"
PRICE_PER_MONTH = 15
GEMINI_API_KEY  = "YOUR_GEMINI_API_KEY_HERE"   # ← من aistudio.google.com
GEMINI_MODEL    = "gemini-2.5-flash"

VODAFONE_CASH = "01098624825"
QR_IMAGE_PATH = "vodafone_qr.jpg"
DB_PATH       = "subscriptions.db"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# ─── صياد أخطاء احتياطي لكل الـ Handlers ────────────────────
def safe_handler(func):
    @functools.wraps(func)
    def wrapper(update_obj, *args, **kwargs):
        try:
            return func(update_obj, *args, **kwargs)
        except Exception as e:
            err = traceback.format_exc()
            logger.error(f"Handler error in {func.__name__}: {e}")
            print(f"❌ خطأ في {func.__name__}:\n{err}", flush=True)
            try:
                with open("error.log", "a", encoding="utf-8") as f:
                    f.write(err + "\n" + "="*50 + "\n")
            except Exception:
                pass
            try:
                bot.send_message(
                    ADMIN_ID,
                    f"⚠️ *حصل خطأ غير متوقع في البوت:*\n`{func.__name__}`\n`{str(e)[:300]}`\n\n_By: Radwan_"
                )
            except Exception:
                pass
    return wrapper

def full_name(user):
    if not user:
        return ""
    return f"{user.first_name or ''} {(user.last_name or '')}".strip()

# ─── سياق الـ AI ────────────────────────────────────────────
AI_SYSTEM_PROMPT = f"""أنت "مساعد رضوان" 🤖 — المساعد الذكي الرسمي لبوت إدارة الاشتراكات ده.
انت لست بوت ردود جاهزة، انت فاهم المشروع بالكامل وبتتكلم من فهمك وذكائك الخاص،
زي موظف خدمة عملاء محترف وذكي: ودود وفيه روح خفيفة (إيموشن أو اتنين براحتك، من غير إفراط)،
بس في نفس الوقت واثق من نفسه ودقيق في المعلومة، مش بس بيكرر جمل محفوظة.

لما حد يسألك أي سؤال، فكر في إجابته بنفسك بناءً على فهمك للمشروع تحت، وجاوب بأسلوبك،
مش بنفس الكلام اللي هنا حرفياً. خليك مرن: لو السؤال بسيط جاوب باختصار، لو محتاج توضيح أكتر اشرح أكتر.

═══ معلومات كاملة عن المشروع ═══

💰 الأسعار والاشتراك:
- السعر: {PRICE_PER_MONTH} جنيه في الشهر، والاشتراك يكون من شهر واحد لحد 12 شهر.
- يقدر يجدد الاشتراك في أي وقت حتى قبل ما ينتهي، ويتضاف على الفترة المتبقية.

📲 طرق الدفع:
- فودافون كاش على الرقم: {VODAFONE_CASH}
- أو QR Code فودافون كاش (البوت بيبعته أثناء عملية الدفع) — ملحوظة: الكود مكتوب عليه 15 جنيه ثابت، فهو مناسب أساساً لاشتراك شهر واحد بدون خصم.

🔄 خطوات الاشتراك بالتفصيل:
1. المستخدم يضغط زر "اشتراك" من القائمة الرئيسية
2. يختار عدد الأشهر (1-12)
3. ممكن يستخدم كوبون خصم أو نقاطه (لو متوفرة) قبل الدفع
4. يدفع المبلغ النهائي على فودافون كاش
5. يبعت صورة إيصال الدفع للبوت
6. الطلب يروح للأدمن للمراجعة، وبعد الموافقة يوصله رابط دعوة للجروب صالح لمرة واحدة بس وبينتهي تلقائياً بعد الاستخدام أو بعد 24 ساعة

🎟 الكوبونات:
- نوعين: نسبة خصم % أو مبلغ ثابت بالجنيه
- الأدمن هو اللي بيتحكم في الكوبونات (إنشاء، تعديل، إيقاف) وعدد مرات الاستخدام المسموحة

⭐ نظام النقاط:
- كل دعوة لصاحب (عن طريق رابط الدعوة الشخصي) = نقاط لك وله الاتنين (القيمة بيحددها الأدمن)
- لما تجمع عدد معين من النقاط (بيحدده الأدمن) تقدر تستبدلها بشهر اشتراك مجاني
- المستخدم يقدر يشوف نقاطه ورابط دعوته من القائمة الرئيسية في أي وقت

⏰ انتهاء الاشتراك:
- البوت بيبعت تنبيه قبل انتهاء الاشتراك بـ 5 أيام
- لو الاشتراك انتهى من غير تجديد، العضو بيتم إزالته من الجروب تلقائياً

═══ أسلوبك في الرد ═══
- جاوب من فهمك للمشروع، بثقة وبشكل مباشر، كأنك جزء من الفريق فعلاً
- اقترح التواصل مع الأدمن فقط في الحالات دي: مشكلة فعلية في الدفع محتاجة تدخل بشري، نزاع أو شكوى، طلب استرجاع فلوس، أو أي مشكلة تقنية فعلية في حسابه
- متقولش "في مشكلة" أو "كلم الأدمن" كرد عام لمجرد إنك مش عارف التفاصيل الدقيقة — استنتج من السياق وجاوب بإجابة منطقية ومفيدة
- ردودك مركزة لكن غنية بالمعلومة، مش سطحية

═══ قدراتك الحقيقية ═══
إنت مدعوم بنموذج ذكاء اصطناعي قوي جداً، فإنت مش مقصور على أسئلة البوت بس.
لو حد طلب منك مساعدة في حاجة تانية، ساعده فعلاً بنفس الكفاءة، زي:
- كتابة وتصحيح ومراجعة كود برمجي بأي لغة
- تنظيم وتلخيص شغله أو مهامه اليومية
- كتابة أو تحرير نصوص ورسائل
- شرح أي موضوع أو الإجابة على أسئلة عامة
- أي مهمة فكرية تانية يحتاجها
خليك مفيد فعلاً في الحاجة المطلوبة، مش بس بتحول كل سؤال لموضوع الاشتراك.

ملحوظة: عندك حد أقصى 5 رسائل في اليوم لكل مستخدم (تقدر تقول ده لو حد سأل عن الموضوع)."""

def ask_ai(user_message: str, history: list = []) -> str:
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"

        contents = []
        for msg in history[-6:]:
            role = "model" if msg["role"] == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        contents.append({"role": "user", "parts": [{"text": user_message}]})

        payload = {
            "system_instruction": {"parts": [{"text": AI_SYSTEM_PROMPT}]},
            "contents": contents,
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 700}
        }
        data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            result = json.loads(resp.read().decode())
            return result["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        logger.error(f"AI error: {e}")
        return "معلش يا صاحبي 🙏 فيه مشكلة صغيرة دلوقتي، جرب تاني كمان شوية أو كلم الأدمن مباشرة."

# ─── قاعدة البيانات ─────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS members (
            user_id     INTEGER PRIMARY KEY,
            username    TEXT,
            full_name   TEXT,
            months      INTEGER DEFAULT 0,
            start_date  TEXT,
            end_date    TEXT,
            points      INTEGER DEFAULT 0,
            ref_code    TEXT UNIQUE,
            referred_by INTEGER,
            notified_5d INTEGER DEFAULT 0,
            active      INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS coupons (
            code        TEXT PRIMARY KEY,
            type        TEXT,
            value       REAL,
            max_uses    INTEGER DEFAULT 1,
            used        INTEGER DEFAULT 0,
            active      INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS pending_payments (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER,
            username    TEXT,
            full_name   TEXT,
            months      INTEGER,
            amount      REAL,
            discount    REAL DEFAULT 0,
            coupon_used TEXT,
            points_used INTEGER DEFAULT 0,
            screenshot  TEXT,
            ts          TEXT
        );
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        );
        CREATE TABLE IF NOT EXISTS ai_history (
            user_id INTEGER PRIMARY KEY,
            history TEXT DEFAULT '[]'
        );
        CREATE TABLE IF NOT EXISTS ai_usage (
            user_id INTEGER PRIMARY KEY,
            date    TEXT,
            count   INTEGER DEFAULT 0
        );
        INSERT OR IGNORE INTO settings VALUES ('points_per_referral','3');
        INSERT OR IGNORE INTO settings VALUES ('points_for_month','50');
    """)
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_setting(key):
    conn = get_db()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else None

def set_setting(key, value):
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO settings VALUES (?,?)", (key, str(value)))
    conn.commit()
    conn.close()

def get_member(user_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM members WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def ensure_member(user_id, username, fname):
    conn = get_db()
    ref_code = hashlib.md5(str(user_id).encode()).hexdigest()[:8].upper()
    conn.execute("""
        INSERT OR IGNORE INTO members (user_id, username, full_name, ref_code)
        VALUES (?,?,?,?)
    """, (user_id, username or "", fname or "", ref_code))
    conn.commit()
    conn.close()

def add_subscription(user_id, months):
    conn = get_db()
    member = conn.execute("SELECT * FROM members WHERE user_id=?", (user_id,)).fetchone()
    now = datetime.now()
    if member and member["end_date"] and datetime.strptime(member["end_date"], "%Y-%m-%d") > now:
        end = datetime.strptime(member["end_date"], "%Y-%m-%d") + timedelta(days=30 * months)
    else:
        end = now + timedelta(days=30 * months)
    conn.execute("""
        UPDATE members SET months=months+?, start_date=?, end_date=?, active=1, notified_5d=0
        WHERE user_id=?
    """, (months, now.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"), user_id))
    conn.commit()
    conn.close()
    return end

def remove_member(user_id):
    conn = get_db()
    conn.execute("UPDATE members SET active=0, end_date=NULL WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def get_coupon(code):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM coupons WHERE code=? AND active=1 AND used<max_uses", (code,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def use_coupon(code):
    conn = get_db()
    conn.execute("UPDATE coupons SET used=used+1 WHERE code=?", (code,))
    conn.commit()
    conn.close()

def add_points(user_id, pts):
    conn = get_db()
    conn.execute("UPDATE members SET points=points+? WHERE user_id=?", (pts, user_id))
    conn.commit()
    conn.close()

def deduct_points(user_id, pts):
    conn = get_db()
    conn.execute("UPDATE members SET points=MAX(0,points-?) WHERE user_id=?", (pts, user_id))
    conn.commit()
    conn.close()

def get_ai_history(user_id):
    conn = get_db()
    row = conn.execute("SELECT history FROM ai_history WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return json.loads(row["history"]) if row else []

def save_ai_history(user_id, history):
    history = history[-10:]
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO ai_history (user_id, history) VALUES (?,?)",
        (user_id, json.dumps(history))
    )
    conn.commit()
    conn.close()

AI_DAILY_LIMIT = 5

def check_and_increment_ai_usage(user_id):
    today = datetime.now(ZoneInfo("Africa/Cairo")).strftime("%Y-%m-%d")
    conn = get_db()
    row = conn.execute("SELECT * FROM ai_usage WHERE user_id=?", (user_id,)).fetchone()
    if not row or row["date"] != today:
        conn.execute("INSERT OR REPLACE INTO ai_usage (user_id, date, count) VALUES (?,?,1)", (user_id, today))
        conn.commit()
        conn.close()
        return True, AI_DAILY_LIMIT - 1
    if row["count"] >= AI_DAILY_LIMIT:
        conn.close()
        return False, 0
    new_count = row["count"] + 1
    conn.execute("UPDATE ai_usage SET count=? WHERE user_id=?", (new_count, user_id))
    conn.commit()
    conn.close()
    return True, AI_DAILY_LIMIT - new_count

# ─── حالة المستخدمين ─────────────────────────────────────────
user_state: dict[int, str] = {}
temp: dict[int, dict] = {}

def get_temp(uid):
    return temp.setdefault(uid, {})

# ─── قوائم وأزرار ────────────────────────────────────────────
def main_menu_kb():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("💳 اشتراك", callback_data="subscribe"))
    kb.add(types.InlineKeyboardButton("⭐ نقاطي", callback_data="my_points"))
    kb.add(types.InlineKeyboardButton("🔗 رابط الدعوة", callback_data="ref_link"))
    kb.add(types.InlineKeyboardButton("🤖 مساعد ذكي", callback_data="ai_help"))
    return kb

def admin_menu_kb():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("➕ إضافة عضو", callback_data="adm_add"),
        types.InlineKeyboardButton("🗑 حذف عضو", callback_data="adm_del"),
    )
    kb.add(
        types.InlineKeyboardButton("🔄 تجديد اشتراك", callback_data="adm_renew"),
        types.InlineKeyboardButton("🎟 الكوبونات", callback_data="adm_coupons"),
    )
    kb.add(
        types.InlineKeyboardButton("⭐ إعدادات النقاط", callback_data="adm_points"),
        types.InlineKeyboardButton("📢 إذاعة", callback_data="adm_broadcast"),
    )
    kb.add(types.InlineKeyboardButton("📋 قائمة الأعضاء", callback_data="adm_list"))
    return kb

# ─── أوامر أساسية ───────────────────────────────────────────
@bot.message_handler(commands=["start"])
@safe_handler
def start_cmd(message):
    user = message.from_user
    user_state.pop(user.id, None)
    temp.pop(user.id, None)
    ensure_member(user.id, user.username, full_name(user))

    parts = message.text.split(maxsplit=1)
    if len(parts) > 1:
        ref_code = parts[1].strip()
        conn = get_db()
        referrer = conn.execute("SELECT user_id FROM members WHERE ref_code=?", (ref_code,)).fetchone()
        me = conn.execute("SELECT referred_by FROM members WHERE user_id=?", (user.id,)).fetchone()
        if referrer and referrer["user_id"] != user.id and (not me or not me["referred_by"]):
            conn.execute("UPDATE members SET referred_by=? WHERE user_id=?", (referrer["user_id"], user.id))
            conn.commit()
        conn.close()

    bot.send_message(
        message.chat.id,
        f"👋 *أهلاً {user.first_name}!*\n\n"
        f"مرحباً في بوت الاشتراكات.\nاختر ما تريد من القائمة:\n\n_By: Radwan_",
        reply_markup=main_menu_kb()
    )

@bot.message_handler(commands=["admin"])
@safe_handler
def admin_cmd(message):
    uid = message.from_user.id
    if uid == ADMIN_ID:
        bot.send_message(message.chat.id, "🛠 *لوحة تحكم الأدمن*\nاختر العملية:", reply_markup=admin_menu_kb())
    else:
        user_state[uid] = "ADMIN_PASS_STATE"
        bot.send_message(message.chat.id, "🔐 أدخل كلمة مرور الأدمن:")

# ─── Callback Queries ───────────────────────────────────────
@bot.callback_query_handler(func=lambda call: True)
@safe_handler
def callbacks(call):
    uid = call.from_user.id
    data = call.data

    if data == "back_start":
        user_state.pop(uid, None)
        bot.edit_message_text(
            f"👋 *أهلاً {call.from_user.first_name}!*\n\nاختر ما تريد:\n\n_By: Radwan_",
            call.message.chat.id, call.message.message_id,
            reply_markup=main_menu_kb()
        )
        return bot.answer_callback_query(call.id)

    if data == "ai_help":
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_start"))
        bot.edit_message_text(
            "🤖 *المساعد الذكي*\n\nأهلاً! اكتب سؤالك في أي وقت وأنا هرد عليك فوراً 😊\n\n_By: Radwan_",
            call.message.chat.id, call.message.message_id, reply_markup=kb
        )
        return bot.answer_callback_query(call.id)

    if data == "my_points":
        member = get_member(uid)
        pts = member["points"] if member else 0
        pfm = int(get_setting("points_for_month") or 50)
        ppr = int(get_setting("points_per_referral") or 3)
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_start"))
        bot.edit_message_text(
            f"⭐ *نقاطك الحالية: {pts}*\n\n"
            f"• {pfm} نقطة = شهر مجاني 🎁\n"
            f"• كل دعوة تجيبلك {ppr} نقطة\n\n_By: Radwan_",
            call.message.chat.id, call.message.message_id, reply_markup=kb
        )
        return bot.answer_callback_query(call.id)

    if data == "ref_link":
        member = get_member(uid)
        me = bot.get_me()
        ref_link = f"https://t.me/{me.username}?start={member['ref_code']}"
        ppr = int(get_setting("points_per_referral") or 3)
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_start"))
        bot.edit_message_text(
            f"🔗 *رابط الدعوة الخاص بك:*\n`{ref_link}`\n\n"
            f"كل صاحب يشترك عن طريقك = +{ppr} نقاط لك وله!\n\n_By: Radwan_",
            call.message.chat.id, call.message.message_id, reply_markup=kb
        )
        return bot.answer_callback_query(call.id)

    if data == "subscribe":
        kb = types.InlineKeyboardMarkup(row_width=3)
        for i in range(1, 13, 3):
            row = []
            for j in range(i, min(i+3, 13)):
                price = j * PRICE_PER_MONTH
                row.append(types.InlineKeyboardButton(f"{j}م - {price}ج", callback_data=f"sub_months_{j}"))
            kb.row(*row)
        kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_start"))
        bot.edit_message_text(
            f"📅 *اختر عدد الأشهر:*\n_(السعر {PRICE_PER_MONTH} جنيه/شهر)_\n\n_By: Radwan_",
            call.message.chat.id, call.message.message_id, reply_markup=kb
        )
        return bot.answer_callback_query(call.id)

    if data.startswith("sub_months_"):
        months = int(data.split("_")[-1])
        t = get_temp(uid)
        t["sub_months"] = months
        t["sub_price"] = months * PRICE_PER_MONTH
        t["sub_coupon"] = None
        t["sub_discount"] = 0
        t["sub_points_used"] = 0

        member = get_member(uid)
        pts = member["points"] if member else 0
        pfm = int(get_setting("points_for_month") or 50)

        text = (
            f"💳 *ملخص الاشتراك:*\n📅 المدة: {months} شهر\n"
            f"💰 السعر: {months * PRICE_PER_MONTH} جنيه\n\n"
            f"هل عندك *كوبون خصم* أو تريد استخدام *نقاطك ({pts} نقطة)*؟\n\n_By: Radwan_"
        )
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🎟 عندي كوبون", callback_data="enter_coupon"))
        if pts >= pfm:
            kb.add(types.InlineKeyboardButton(f"⭐ استخدم {pfm} نقطة (شهر مجاني)", callback_data="use_points"))
        kb.add(types.InlineKeyboardButton("✅ متابعة بدون خصم", callback_data="no_discount"))
        kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="subscribe"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
        return bot.answer_callback_query(call.id)

    if data == "enter_coupon":
        user_state[uid] = "AWAITING_COUPON_CODE"
        bot.edit_message_text("🎟 أرسل *كود الكوبون*:\n\n_By: Radwan_", call.message.chat.id, call.message.message_id)
        return bot.answer_callback_query(call.id)

    if data == "use_points":
        member = get_member(uid)
        pfm = int(get_setting("points_for_month") or 50)
        pts = member["points"] if member else 0
        if pts < pfm:
            return bot.answer_callback_query(call.id, "❌ نقاطك مش كافية!", show_alert=True)
        t = get_temp(uid)
        t["sub_points_used"] = pfm
        months = t.get("sub_months", 1)
        base = months * PRICE_PER_MONTH
        discount = PRICE_PER_MONTH
        final = max(0, base - discount)
        t["sub_discount"] = discount
        t["sub_price"] = final
        send_payment_info(call, final, discount)
        return bot.answer_callback_query(call.id)

    if data == "no_discount":
        t = get_temp(uid)
        final = t.get("sub_price", 0)
        send_payment_info(call, final, 0)
        return bot.answer_callback_query(call.id)

    if data == "coupon_confirmed":
        t = get_temp(uid)
        final = t.get("sub_price", 0)
        discount = t.get("sub_discount", 0)
        send_payment_info(call, final, discount)
        return bot.answer_callback_query(call.id)

    if data.startswith("pay_approve_") or data.startswith("pay_reject_"):
        handle_payment_decision(call)
        return

    if data == "adm_back":
        user_state.pop(uid, None)
        bot.edit_message_text("🛠 *لوحة تحكم الأدمن*\nاختر العملية:", call.message.chat.id, call.message.message_id, reply_markup=admin_menu_kb())
        return bot.answer_callback_query(call.id)

    if data == "adm_add":
        user_state[uid] = "ADD_MEMBER_ID"
        bot.edit_message_text("➕ أدخل *ID المستخدم* المراد إضافته:", call.message.chat.id, call.message.message_id)
        return bot.answer_callback_query(call.id)

    if data == "adm_del":
        user_state[uid] = "DEL_MEMBER_ID"
        bot.edit_message_text("🗑 أدخل *ID المستخدم* المراد حذفه:", call.message.chat.id, call.message.message_id)
        return bot.answer_callback_query(call.id)

    if data == "adm_renew":
        user_state[uid] = "RENEW_MEMBER_ID"
        bot.edit_message_text("🔄 أدخل *ID المستخدم*:", call.message.chat.id, call.message.message_id)
        return bot.answer_callback_query(call.id)

    if data == "adm_list":
        conn = get_db()
        rows = conn.execute("SELECT * FROM members WHERE active=1 ORDER BY end_date").fetchall()
        conn.close()
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="adm_back"))
        if not rows:
            bot.edit_message_text("📋 لا يوجد أعضاء نشطين.", call.message.chat.id, call.message.message_id, reply_markup=kb)
            return bot.answer_callback_query(call.id)
        text = "📋 *الأعضاء النشطين:*\n\n"
        for r in rows:
            text += (f"👤 {r['full_name']} (@{r['username']})\n🆔 `{r['user_id']}`\n"
                     f"📅 ينتهي: {r['end_date']}\n⭐ نقاط: {r['points']}\n──────────────\n")
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
        return bot.answer_callback_query(call.id)

    if data == "adm_coupons":
        conn = get_db()
        rows = conn.execute("SELECT * FROM coupons WHERE active=1").fetchall()
        conn.close()
        text = "🎟 *إدارة الكوبونات*\n\n"
        if rows:
            for r in rows:
                text += f"• `{r['code']}` - {r['type']} - قيمة: {r['value']} - استُخدم: {r['used']}/{r['max_uses']}\n"
        else:
            text += "لا توجد كوبونات.\n"
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("➕ إضافة كوبون", callback_data="adm_coup_add"),
            types.InlineKeyboardButton("🗑 حذف كوبون", callback_data="adm_coup_del"),
        )
        kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="adm_back"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
        return bot.answer_callback_query(call.id)

    if data == "adm_coup_add":
        user_state[uid] = "ADD_COUPON_CODE"
        bot.edit_message_text("🎟 أدخل *كود الكوبون*:", call.message.chat.id, call.message.message_id)
        return bot.answer_callback_query(call.id)

    if data == "adm_coup_del":
        user_state[uid] = "DEL_COUPON_CODE"
        bot.edit_message_text("🗑 أدخل *كود الكوبون* للحذف:", call.message.chat.id, call.message.message_id)
        return bot.answer_callback_query(call.id)

    if data.startswith("coup_type_"):
        t = get_temp(uid)
        t["coup_type"] = "percent" if "percent" in data else "fixed"
        lbl = "النسبة (مثلاً 20 = 20%)" if t["coup_type"] == "percent" else "المبلغ بالجنيه"
        user_state[uid] = "ADD_COUPON_VALUE"
        bot.edit_message_text(f"💰 أدخل {lbl}:", call.message.chat.id, call.message.message_id)
        return bot.answer_callback_query(call.id)

    if data == "adm_points":
        ppr = get_setting("points_per_referral")
        pfm = get_setting("points_for_month")
        text = f"⭐ *إعدادات النقاط*\n\n• نقاط لكل دعوة: *{ppr}*\n• نقاط لشهر مجاني: *{pfm}*"
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("✏️ تغيير نقاط الدعوة", callback_data="pts_set_ref"),
            types.InlineKeyboardButton("✏️ نقاط الشهر المجاني", callback_data="pts_set_month"),
        )
        kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="adm_back"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
        return bot.answer_callback_query(call.id)

    if data == "pts_set_ref":
        user_state[uid] = "SET_POINTS_PER_REF"
        bot.edit_message_text("⭐ أدخل عدد النقاط لكل دعوة:", call.message.chat.id, call.message.message_id)
        return bot.answer_callback_query(call.id)

    if data == "pts_set_month":
        user_state[uid] = "SET_POINTS_FOR_MONTH"
        bot.edit_message_text("⭐ أدخل عدد النقاط للشهر المجاني:", call.message.chat.id, call.message.message_id)
        return bot.answer_callback_query(call.id)

    if data == "adm_broadcast":
        user_state[uid] = "BROADCAST_TEXT"
        bot.edit_message_text("📢 أرسل الرسالة التي تريد إذاعتها:", call.message.chat.id, call.message.message_id)
        return bot.answer_callback_query(call.id)

    bot.answer_callback_query(call.id)

# ─── دفع: عرض تفاصيل الدفع + QR ─────────────────────────────
def send_payment_info(call, final, discount):
    uid = call.from_user.id
    t = get_temp(uid)
    months = t.get("sub_months", 1)
    base = months * PRICE_PER_MONTH
    text = f"💳 *تفاصيل الدفع:*\n📅 المدة: {months} شهر\n💰 الإجمالي: {base} جنيه\n"
    if discount:
        text += f"🎁 الخصم: {discount} جنيه\n"
    text += (
        f"💵 *المطلوب دفعه: {final} جنيه*\n\n━━━━━━━━━━━━━━━\n"
        f"📲 *طرق الدفع:*\n• فودافون كاش: `{VODAFONE_CASH}`\n"
        f"• أو سكان QR Code فودافون كاش (الصورة الجاية ⬇️)\n━━━━━━━━━━━━━━━\n"
        f"📸 بعد الدفع أرسل *صورة الإيصال* هنا\n\n_By: Radwan_"
    )
    t["awaiting_screenshot"] = True
    t["sub_final"] = final
    t["sub_discount_final"] = discount
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id)

    qr_caption = ("📷 *سكان الكود وادفع مباشرة من فودافون كاش*\n"
                  "_(ملحوظة: الكود مكتوب عليه 15 جنيه فقط، مناسب لو المطلوب دفعه = 15 جنيه)_")
    try:
        with open(QR_IMAGE_PATH, "rb") as qr:
            bot.send_photo(uid, photo=qr, caption=qr_caption)
    except FileNotFoundError:
        logger.warning("QR image not found, skipping.")
    except Exception as e:
        logger.error(f"Error sending QR image: {e}")

# ─── موافقة / رفض الدفع ────────────────────────────────────
def handle_payment_decision(call):
    data = call.data
    action = "approve" if data.startswith("pay_approve_") else "reject"
    pay_id = int(data.split("_")[-1])

    conn = get_db()
    pay = conn.execute("SELECT * FROM pending_payments WHERE id=?", (pay_id,)).fetchone()
    conn.close()
    if not pay:
        return bot.answer_callback_query(call.id, "⚠️ الطلب مش موجود.", show_alert=True)

    uid = pay["user_id"]
    months = pay["months"]

    if action == "approve":
        ensure_member(uid, pay["username"], pay["full_name"])
        end = add_subscription(uid, months)
        if pay["coupon_used"]:
            use_coupon(pay["coupon_used"])
        if pay["points_used"] > 0:
            deduct_points(uid, pay["points_used"])
        try:
            expire_ts = int((datetime.now() + timedelta(hours=24)).timestamp())
            link_obj = bot.create_chat_invite_link(GROUP_ID, expire_date=expire_ts, member_limit=1)
            bot.send_message(
                uid,
                f"✅ *تم قبول اشتراكك!*\n📅 ينتهي في: {end.strftime('%Y-%m-%d')}\n\n"
                f"🔗 رابط الانضمام (مرة واحدة فقط):\n{link_obj.invite_link}\n\n_By: Radwan_"
            )
        except Exception as e:
            logger.error(f"Invite link error: {e}")
        member = get_member(uid)
        if member and member["referred_by"]:
            ppr = int(get_setting("points_per_referral") or 3)
            add_points(member["referred_by"], ppr)
            add_points(uid, ppr)
            try:
                bot.send_message(member["referred_by"], f"⭐ حصلت على {ppr} نقاط لأن صاحبك اشترك!\n_By: Radwan_")
            except Exception:
                pass
        caption = f"✅ *تمت الموافقة!*\nالعضو: {pay['full_name']} (`{uid}`)"
    else:
        try:
            bot.send_message(uid, "❌ *تم رفض طلبك.*\nتأكد من صحة الإيصال وأعد المحاولة.\n\n_By: Radwan_")
        except Exception:
            pass
        caption = f"❌ *تم رفض الطلب!*\nالعضو: {pay['full_name']} (`{uid}`)"

    conn2 = get_db()
    conn2.execute("DELETE FROM pending_payments WHERE id=?", (pay_id,))
    conn2.commit()
    conn2.close()

    try:
        bot.edit_message_caption(caption, call.message.chat.id, call.message.message_id)
    except Exception:
        try:
            bot.edit_message_text(caption, call.message.chat.id, call.message.message_id)
        except Exception:
            pass
    bot.answer_callback_query(call.id)

# ─── استقبال الصور (إيصال) ──────────────────────────────────
@bot.message_handler(content_types=["photo"])
@safe_handler
def receive_photo(message):
    uid = message.from_user.id
    t = get_temp(uid)

    if t.get("awaiting_screenshot"):
        user = message.from_user
        t["awaiting_screenshot"] = False
        months = t.get("sub_months", 1)
        final = t.get("sub_final", months * PRICE_PER_MONTH)
        discount = t.get("sub_discount_final", 0)
        coupon = t.get("sub_coupon")
        pts_used = t.get("sub_points_used", 0)
        photo_id = message.photo[-1].file_id

        conn = get_db()
        cur = conn.execute(
            """INSERT INTO pending_payments
               (user_id,username,full_name,months,amount,discount,coupon_used,points_used,screenshot,ts)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (user.id, user.username or "", full_name(user), months, final, discount,
             coupon, pts_used, photo_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        pay_id = cur.lastrowid
        conn.commit()
        conn.close()

        kb = types.InlineKeyboardMarkup()
        kb.add(
            types.InlineKeyboardButton("✅ موافقة", callback_data=f"pay_approve_{pay_id}"),
            types.InlineKeyboardButton("❌ رفض", callback_data=f"pay_reject_{pay_id}"),
        )
        caption = (
            f"💳 *طلب اشتراك جديد!*\n\n👤 الاسم: {full_name(user)}\n🆔 ID: `{user.id}`\n"
            f"📛 يوزر: @{user.username or 'لا يوجد'}\n📅 الأشهر: {months}\n💰 المبلغ: {final} جنيه\n"
        )
        if discount:
            caption += f"🎁 الخصم: {discount} جنيه\n"
        if coupon:
            caption += f"🎟 كوبون: `{coupon}`\n"
        if pts_used:
            caption += f"⭐ نقاط مستخدمة: {pts_used}\n"

        try:
            bot.send_photo(ADMIN_ID, photo=photo_id, caption=caption, reply_markup=kb)
        except Exception as e:
            logger.error(f"Error notifying admin: {e}")

        bot.send_message(message.chat.id, "✅ *تم استقبال طلبك!*\nسيتم مراجعته وتفعيل اشتراكك قريباً.\n\n_By: Radwan_")
        return

    try:
        bot.send_photo(
            ADMIN_ID, photo=message.photo[-1].file_id,
            caption=(f"🖼 *صورة من مستخدم:*\n👤 {full_name(message.from_user)} "
                     f"(@{message.from_user.username or 'لا يوجد'})\n🆔 `{uid}`\n\n_By: Radwan_")
        )
    except Exception:
        pass

# ─── رصد الجروب ─────────────────────────────────────────────
@bot.message_handler(func=lambda m: m.chat.id == GROUP_ID, content_types=["text"])
@safe_handler
def group_message_spy(message):
    user = message.from_user
    if not user:
        return
    try:
        bot.send_message(
            ADMIN_ID,
            f"💬 *رسالة في الجروب:*\n👤 {full_name(user)} (@{user.username or 'لا يوجد'})\n"
            f"🆔 `{user.id}`\n💬 {message.text}\n\n_By: Radwan_"
        )
    except Exception:
        pass

# ─── استقبال النصوص (إدمن / كوبون / AI) ─────────────────────
@bot.message_handler(func=lambda m: m.chat.type == "private" and not m.text.startswith("/"), content_types=["text"])
@safe_handler
def handle_text(message):
    uid = message.from_user.id
    text = message.text.strip()
    state = user_state.get(uid)

    if state == "ADMIN_PASS_STATE":
        user_state.pop(uid, None)
        if text == ADMIN_PASS:
            bot.send_message(message.chat.id, "🛠 *لوحة تحكم الأدمن*\nاختر العملية:", reply_markup=admin_menu_kb())
        else:
            bot.send_message(message.chat.id, "❌ كلمة المرور غلط!")
        return

    if state == "ADD_MEMBER_ID":
        try:
            get_temp(uid)["add_id"] = int(text)
            user_state[uid] = "ADD_MEMBER_MONTHS"
            bot.send_message(message.chat.id, "📅 كام شهر؟")
        except ValueError:
            bot.send_message(message.chat.id, "❌ ID غلط، حاول تاني:")
        return

    if state == "ADD_MEMBER_MONTHS":
        try:
            months = int(text)
            target_id = get_temp(uid)["add_id"]
            try:
                cm = bot.get_chat_member(GROUP_ID, target_id)
                uname, fname_ = cm.user.username or "", full_name(cm.user)
            except Exception:
                uname, fname_ = "", ""
            ensure_member(target_id, uname, fname_)
            end = add_subscription(target_id, months)
            try:
                expire_ts = int((datetime.now() + timedelta(hours=24)).timestamp())
                link_obj = bot.create_chat_invite_link(GROUP_ID, expire_date=expire_ts, member_limit=1)
                bot.send_message(
                    target_id,
                    f"✅ *تم تفعيل اشتراكك!*\n📅 ينتهي في: {end.strftime('%Y-%m-%d')}\n\n"
                    f"🔗 رابط الانضمام (صالح مرة واحدة فقط):\n{link_obj.invite_link}\n\n_By: Radwan_"
                )
            except Exception as e:
                logger.error(f"Error sending invite: {e}")
            bot.send_message(message.chat.id, f"✅ تم إضافة العضو {target_id} بنجاح!\n📅 ينتهي: {end.strftime('%Y-%m-%d')}")
        except ValueError:
            bot.send_message(message.chat.id, "❌ رقم غلط:")
            return
        user_state.pop(uid, None)
        return

    if state == "DEL_MEMBER_ID":
        try:
            target_id = int(text)
            remove_member(target_id)
            try:
                bot.ban_chat_member(GROUP_ID, target_id)
                bot.unban_chat_member(GROUP_ID, target_id)
            except Exception:
                pass
            try:
                bot.send_message(target_id, "❌ *تم إلغاء اشتراكك.*\nللتجديد تواصل مع الأدمن.\n\n_By: Radwan_")
            except Exception:
                pass
            bot.send_message(message.chat.id, f"✅ تم حذف العضو {target_id}")
        except ValueError:
            bot.send_message(message.chat.id, "❌ ID غلط:")
            return
        user_state.pop(uid, None)
        return

    if state == "RENEW_MEMBER_ID":
        try:
            get_temp(uid)["renew_id"] = int(text)
            user_state[uid] = "RENEW_MONTHS"
            bot.send_message(message.chat.id, "📅 كام شهر تجديد؟")
        except ValueError:
            bot.send_message(message.chat.id, "❌ ID غلط:")
        return

    if state == "RENEW_MONTHS":
        try:
            months = int(text)
            target_id = get_temp(uid)["renew_id"]
            member = get_member(target_id)
            if not member:
                bot.send_message(message.chat.id, "❌ العضو مش موجود في قاعدة البيانات!")
                user_state.pop(uid, None)
                return
            end = add_subscription(target_id, months)
            try:
                bot.send_message(target_id, f"✅ *تم تجديد اشتراكك!*\n📅 ينتهي في: {end.strftime('%Y-%m-%d')}\n\n_By: Radwan_")
            except Exception:
                pass
            bot.send_message(message.chat.id, f"✅ تم تجديد اشتراك {target_id} حتى {end.strftime('%Y-%m-%d')}")
        except ValueError:
            bot.send_message(message.chat.id, "❌ رقم غلط:")
            return
        user_state.pop(uid, None)
        return

    if state == "ADD_COUPON_CODE":
        get_temp(uid)["coup_code"] = text.upper()
        kb = types.InlineKeyboardMarkup()
        kb.add(
            types.InlineKeyboardButton("نسبة %", callback_data="coup_type_percent"),
            types.InlineKeyboardButton("مبلغ ثابت", callback_data="coup_type_fixed"),
        )
        bot.send_message(message.chat.id, "نوع الخصم؟", reply_markup=kb)
        return

    if state == "ADD_COUPON_VALUE":
        try:
            get_temp(uid)["coup_value"] = float(text)
            user_state[uid] = "ADD_COUPON_USES"
            bot.send_message(message.chat.id, "🔢 عدد مرات الاستخدام؟ (0 = غير محدود)")
        except ValueError:
            bot.send_message(message.chat.id, "❌ رقم غلط:")
        return

    if state == "ADD_COUPON_USES":
        try:
            uses = int(text)
            uses = 999999 if uses == 0 else uses
            t = get_temp(uid)
            conn = get_db()
            conn.execute(
                "INSERT OR REPLACE INTO coupons (code,type,value,max_uses) VALUES (?,?,?,?)",
                (t["coup_code"], t["coup_type"], t["coup_value"], uses)
            )
            conn.commit()
            conn.close()
            bot.send_message(message.chat.id, f"✅ تم إضافة الكوبون `{t['coup_code']}` بنجاح!")
        except ValueError:
            bot.send_message(message.chat.id, "❌ رقم غلط:")
            return
        user_state.pop(uid, None)
        return

    if state == "DEL_COUPON_CODE":
        code = text.upper()
        conn = get_db()
        conn.execute("UPDATE coupons SET active=0 WHERE code=?", (code,))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, f"✅ تم حذف الكوبون `{code}`")
        user_state.pop(uid, None)
        return

    if state == "SET_POINTS_PER_REF":
        try:
            v = int(text)
            set_setting("points_per_referral", v)
            bot.send_message(message.chat.id, f"✅ نقاط الدعوة = {v}")
        except ValueError:
            bot.send_message(message.chat.id, "❌ رقم غلط:")
            return
        user_state.pop(uid, None)
        return

    if state == "SET_POINTS_FOR_MONTH":
        try:
            v = int(text)
            set_setting("points_for_month", v)
            bot.send_message(message.chat.id, f"✅ نقاط الشهر المجاني = {v}")
        except ValueError:
            bot.send_message(message.chat.id, "❌ رقم غلط:")
            return
        user_state.pop(uid, None)
        return

    if state == "BROADCAST_TEXT":
        conn = get_db()
        users = conn.execute("SELECT user_id FROM members").fetchall()
        conn.close()
        ok = fail = 0
        for u in users:
            try:
                bot.copy_message(u["user_id"], message.chat.id, message.message_id)
                ok += 1
            except Exception:
                fail += 1
            time.sleep(0.05)
        bot.send_message(message.chat.id, f"📢 *اكتملت الإذاعة!*\n✅ نجح: {ok}\n❌ فشل: {fail}")
        user_state.pop(uid, None)
        return

    if state == "AWAITING_COUPON_CODE":
        user_state.pop(uid, None)
        code = text.upper()
        coupon = get_coupon(code)
        t = get_temp(uid)
        months = t.get("sub_months", 1)
        base = months * PRICE_PER_MONTH
        if not coupon:
            bot.send_message(message.chat.id, "❌ الكوبون غلط أو منتهي!\n\n_By: Radwan_")
            return
        if coupon["type"] == "percent":
            discount = round(base * coupon["value"] / 100, 2)
        else:
            discount = coupon["value"]
        final = max(0, base - discount)
        t["sub_coupon"] = code
        t["sub_discount"] = discount
        t["sub_price"] = final
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("✅ متابعة", callback_data="coupon_confirmed"))
        bot.send_message(
            message.chat.id,
            f"✅ *كوبون صالح!*\n💰 السعر الأصلي: {base} جنيه\n🎟 الخصم: {discount} جنيه\n"
            f"💳 المطلوب: *{final} جنيه*\n\n_By: Radwan_",
            reply_markup=kb
        )
        return

    # ── غير ذلك → المساعد الذكي (AI) ──
    allowed, remaining = check_and_increment_ai_usage(uid)
    if not allowed:
        bot.send_message(
            message.chat.id,
            "⏳ *وصلت للحد الأقصى (5 رسائل) للمساعد الذكي اليوم.*\n"
            "جرب تاني بكرة، أو لو الموضوع مهم كلم الأدمن مباشرة.\n\n_By: Radwan_"
        )
        return

    bot.send_chat_action(message.chat.id, "typing")
    history = get_ai_history(uid)
    reply = ask_ai(text, history)
    history.append({"role": "user", "content": text})
    history.append({"role": "assistant", "content": reply})
    save_ai_history(uid, history)

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("❌ إنهاء المحادثة", callback_data="back_start"))
    bot.send_message(message.chat.id, f"🤖 {reply}\n\n_({remaining} رسائل متبقية اليوم)_\n\n_By: Radwan_", reply_markup=kb)

    try:
        bot.send_message(
            ADMIN_ID,
            f"💬 *رسالة مستخدم:*\n👤 {full_name(message.from_user)} "
            f"(@{message.from_user.username or 'لا يوجد'})\n🆔 `{uid}`\n💬 {text}\n"
            f"🤖 رد الـ AI: {reply}\n\n_By: Radwan_"
        )
    except Exception:
        pass

# ─── مهمة انتهاء الاشتراكات ─────────────────────────────────
def check_expiry():
    try:
        _check_expiry_inner()
    except Exception:
        err = traceback.format_exc()
        logger.error(f"check_expiry job error: {err}")
        try:
            with open("error.log", "a", encoding="utf-8") as f:
                f.write(err + "\n" + "="*50 + "\n")
        except Exception:
            pass

def _check_expiry_inner():
    now = datetime.now()
    conn = get_db()
    members = conn.execute("SELECT * FROM members WHERE active=1 AND end_date IS NOT NULL").fetchall()
    conn.close()
    for m in members:
        try:
            end = datetime.strptime(m["end_date"], "%Y-%m-%d")
        except Exception:
            continue
        days_left = (end - now).days

        if 0 < days_left <= 5 and not m["notified_5d"]:
            try:
                bot.send_message(
                    m["user_id"],
                    f"⚠️ *تنبيه!* اشتراكك ينتهي خلال *{days_left} أيام* ({m['end_date']})\nجدد الآن!\n\n_By: Radwan_"
                )
                bot.send_message(
                    ADMIN_ID, f"⚠️ اشتراك *{m['full_name']}* (`{m['user_id']}`) ينتهي خلال {days_left} أيام\n_By: Radwan_"
                )
            except Exception:
                pass
            conn2 = get_db()
            conn2.execute("UPDATE members SET notified_5d=1 WHERE user_id=?", (m["user_id"],))
            conn2.commit()
            conn2.close()

        if days_left <= 0:
            try:
                bot.send_message(
                    m["user_id"],
                    "❌ *انتهى اشتراكك!*\nتم إزالتك من المجموعة.\nللتجديد تواصل معنا.\n\n_By: Radwan_"
                )
                bot.send_message(
                    ADMIN_ID, f"🔴 انتهى اشتراك *{m['full_name']}* (`{m['user_id']}`) - تم الحذف\n_By: Radwan_"
                )
            except Exception:
                pass
            try:
                bot.ban_chat_member(GROUP_ID, m["user_id"])
                bot.unban_chat_member(GROUP_ID, m["user_id"])
            except Exception:
                pass
            conn3 = get_db()
            conn3.execute("UPDATE members SET active=0, end_date=NULL WHERE user_id=?", (m["user_id"],))
            conn3.commit()
            conn3.close()

# ─── نسخة احتياطية يومية لقاعدة البيانات ────────────────────
def backup_database():
    try:
        caption = f"📦 *نسخة احتياطية يومية*\n🗓 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n_By: Radwan_"
        with open(DB_PATH, "rb") as f:
            bot.send_document(ADMIN_ID, document=f, caption=caption)
        logger.info("Database backup sent successfully.")
    except Exception as e:
        logger.error(f"Backup error: {e}")

# ─── تشغيل البوت ────────────────────────────────────────────
def main():
    print("🔄 1) بدء تشغيل السكريبت...", flush=True)
    init_db()
    print("🔄 2) قاعدة البيانات جاهزة، بدء تشغيل الـ Scheduler...", flush=True)

    scheduler = BackgroundScheduler(timezone=ZoneInfo("Africa/Cairo"))
    scheduler.add_job(check_expiry, "interval", hours=1)
    scheduler.add_job(backup_database, "cron", hour=0, minute=0)
    scheduler.start()

    print("✅ البوت شغال (pyTelegramBotAPI) مع AI! - By: Radwan", flush=True)
    bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=30)

if __name__ == "__main__":
    try:
        main()
    except Exception:
        err = traceback.format_exc()
        print("❌❌❌ حصل خطأ:\n" + err, flush=True)
        try:
            with open("error.log", "a", encoding="utf-8") as f:
                f.write(err + "\n" + "="*50 + "\n")
        except Exception:
            pass
        raise