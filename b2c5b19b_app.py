# -*- coding: utf-8 -*-
"""
Twist Music Bot - Telegram Edition
----------------------------------
بوت تيليجرام لـ Twist Music
- تصميم شيك وجميل
- إشعار المالك بكل شخص يدخل أو يفعل من البوت
"""

import json
import logging
import uuid
from datetime import datetime

import requests
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ParseMode, ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

# ======================= الإعدادات =======================
BOT_TOKEN = "8800125719:AAGprZgyjybKOfZ3Yect6NQwqphaOHuJiUQ"
OWNER_ID = 7793874038  # الاي دي بتاع المالك والمتحكم الكامل

# حالات المحادثة
PHONE, OTP = range(2)

# تخزين جلسات المستخدمين
user_sessions = {}

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ======================= واجهة الإشعار للمالك =======================
def owner_notify_text(user, action, extra=""):
    """ينشئ نص إشعار جميل للمالك ببيانات الشخص"""
    uid = user.id if user else "?"
    uname = (
        f"@{user.username}" if user and user.username else (user.first_name if user else "—")
    )
    first = user.first_name if user else "—"
    last = user.last_name if user else "—"
    lang = user.language_code if user else "—"

    text = (
        "🔔 <b>إشعار جديد من البوت</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>الاسم:</b> {first} {last}\n"
        f"🆔 <b>المعرف:</b> {uname}\n"
        f"🔢 <b>الاي دي:</b> <code>{uid}</code>\n"
        f"🌐 <b>اللغة:</b> {lang}\n"
        f"🕒 <b>الوقت:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"⚡ <b>الإجراء:</b> {action}\n"
    )
    if extra:
        text += f"📝 <b>تفاصيل:</b> {extra}\n"
    text += "━━━━━━━━━━━━━━━━━━"
    return text


async def notify_owner(context: ContextTypes.DEFAULT_TYPE, user, action, extra=""):
    """يرسل إشعار للمالك بأمان"""
    try:
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=owner_notify_text(user, action, extra),
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        logger.error(f"فشل إرسال إشعار للمالك: {e}")


# ======================= كلاس API بتاع Twist =======================
class TwistMusicAPI:
    def __init__(self):
        self.base_url = "https://api.twistmena.com/music"
        self.device_id = "AP3A.240905.015.A2"
        self.tg_device_id = ""
        self.session_id = str(uuid.uuid4())
        self.token = None
        self.access_token = None
        self.tg_token = None
        self.refresh_token = None
        self.balance = 0
        self.phone = None
        self.monthly_used = 0

    def get_headers(self, extra=None):
        headers = {
            "user-agent": "Twist-Mobile/11.2.10 (Android; 15; Infinix X6885; music; ar-EG)",
            "app_version": "11.2.10",
            "appversion": "11.2.10",
            "channel": "mobileapp",
            "platform": "android",
            "accept": "application/json",
            "accept-language": "ar",
            "content-type": "application/json",
            "device_id": self.device_id,
            "tgdeviceid": self.tg_device_id,
            "sessionid": self.session_id,
            "host": "api.twistmena.com",
            "connection": "keep-alive",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if self.access_token:
            headers["access-token"] = self.access_token
        if self.tg_token:
            headers["tg-token"] = self.tg_token
        if self.refresh_token:
            headers["tg-refresh-token"] = self.refresh_token
        if extra:
            headers.update(extra)
        return headers

    def format_phone(self, phone):
        phone = phone.strip().replace(" ", "").replace("+", "")
        if phone.startswith("0"):
            return "20" + phone[1:]
        if phone.startswith("20"):
            return phone
        return "20" + phone

    def send_otp(self, phone):
        formatted = self.format_phone(phone)
        url = f"{self.base_url}/Dlogin/sendCode"
        payload = {"dial": formatted}
        try:
            r = requests.post(url, json=payload, headers=self.get_headers(), timeout=30)
            if r.status_code == 200:
                self.phone = formatted
                return True, "✅ تم إرسال كود التحقق بنجاح!"
            return False, "❌ فشل إرسال الكود"
        except Exception:
            return False, "❌ خطأ في الاتصال"

    def verify_otp(self, code):
        if not self.phone:
            return False, "❌ لم يتم إرسال كود بعد!"
        url = f"{self.base_url}/Dlogin/verify"
        payload = {
            "dial": self.phone,
            "verifyCode": code,
            "socialServiceName": "",
            "socialServiceToken": "",
        }
        try:
            r = requests.post(url, json=payload, headers=self.get_headers(), timeout=30)
            if r.status_code == 200:
                d = r.json()
                self.token = d.get("token")
                self.access_token = d.get("accessToken")
                self.tg_token = d.get("tgToken")
                self.refresh_token = d.get("refreshToken")
                self.get_balance()
                return True, "✅ تم تسجيل الدخول بنجاح!"
            return False, "❌ كود غير صحيح!"
        except Exception:
            return False, "❌ خطأ في الاتصال"

    def get_balance(self):
        if not self.token:
            return 0
        url = f"{self.base_url}/user/loyalty/balance/details"
        try:
            r = requests.get(url, headers=self.get_headers(), timeout=30)
            if r.status_code == 200:
                self.balance = r.json().get("balance", 0)
                return self.balance
            return 0
        except Exception:
            return 0

    def complete_tasks(self):
        if not self.token:
            return False, "❌ يجب تسجيل الدخول أولاً!"
        url = f"{self.base_url}/user/loyalty/achievements/v2"
        try:
            r = requests.get(url, headers=self.get_headers(), timeout=30)
            if r.status_code != 200:
                return False, "❌ فشل جلب المهام"
            d = r.json()
            badges = d.get("badges", [])
            completed = 0
            points = 0
            for cat in badges:
                for task in cat.get("badges", []):
                    if not task.get("rewarded"):
                        aurl = f"{self.base_url}/loyalty/action/{task.get('id')}"
                        requests.post(aurl, headers=self.get_headers(), timeout=30)
                        completed += 1
                        points += task.get("reward", {}).get("points", 0)
            self.get_balance()
            return True, f"✅ تم إنجاز {completed} مهمة\n💰 ربحت {points} كوينز"
        except Exception:
            return False, "❌ حدث خطأ أثناء تنفيذ المهام"

    def redeem_units(self, package_id):
        if not self.token:
            return False, "❌ يجب تسجيل الدخول أولاً!"
        packages = {
            "1": "EAND_50_UNITS_ID_9",
            "2": "EAND_100_UNITS_ID_10",
            "3": "EAND_150_UNITS_ID_11",
            "4": "EAND_300_UNITS_ID_12",
            "5": "EAND_500_UNITS_ID_13",
            "6": "EAND_750_UNITS_ID_14",
            "7": "EAND_1000_UNITS_ID_15",
        }
        costs = {"1": 100, "2": 200, "3": 300, "4": 600, "5": 1000, "6": 1500, "7": 2000}
        units = {"1": 50, "2": 100, "3": 150, "4": 300, "5": 500, "6": 750, "7": 1000}

        if self.monthly_used + units[package_id] > 2000:
            return False, "⚠️ تم تجاوز الحد الشهري!\nالحد الأقصى 2000 وحدة شهرياً"
        if self.balance < costs.get(package_id, 0):
            return False, "⚠️ رصيدك غير كافٍ!"
        url = f"{self.base_url}/loyalty/redeem/{packages.get(package_id)}"
        try:
            r = requests.post(url, headers=self.get_headers(), timeout=30)
            if r.status_code == 200:
                self.monthly_used += units[package_id]
                self.get_balance()
                return True, f"✅ تم استبدال {units[package_id]} وحدة بنجاح!"
            return False, "❌ فشل الاستبدال"
        except Exception:
            return False, "❌ خطأ في الاتصال"


# ======================= القوائم والتصميم =======================
PACKAGES_INFO = {
    "1": ("50 وحدة", "100 كوينز"),
    "2": ("100 وحدة", "200 كوينز"),
    "3": ("150 وحدة", "300 كوينز"),
    "4": ("300 وحدة", "600 كوينز"),
    "5": ("500 وحدة", "1000 كوينز"),
    "6": ("750 وحدة", "1500 كوينز"),
    "7": ("1000 وحدة", "2000 كوينز"),
}


def start_keyboard():
    kb = [[InlineKeyboardButton("🚀 بدء تسجيل الدخول", callback_data="start_login")]]
    return InlineKeyboardMarkup(kb)


def packages_keyboard():
    kb = []
    for pid in ["1", "2", "3", "4", "5", "6", "7"]:
        label, cost = PACKAGES_INFO[pid]
        kb.append([InlineKeyboardButton(f"🎁 {label} — {cost}", callback_data=f"redeem_{pid}")])
    kb.append([InlineKeyboardButton("🔄 إعادة تسجيل الدخول", callback_data="restart")])
    kb.append([InlineKeyboardButton("❌ خروج", callback_data="exit")])
    return InlineKeyboardMarkup(kb)


def after_keyboard():
    kb = [
        [InlineKeyboardButton("🎁 استبدال المزيد", callback_data="more_redeem")],
        [InlineKeyboardButton("🔄 حساب جديد", callback_data="restart")],
        [InlineKeyboardButton("❌ خروج", callback_data="exit")],
    ]
    return InlineKeyboardMarkup(kb)


# ======================= معالجات البوت =======================
WELCOME_TEXT = (
    "🎵 <b>أهلاً بك في بوت Twist Music</b> 🎵\n"
    "━━━━━━━━━━━━━━━━━━\n"
    "🔄 <b>اقسم نقاطك لوحدات وباقات</b>\n"
    "✅ <b>نظام آمن وموثوق</b>\n"
    "━━━━━━━━━━━━━━━━━━\n"
    "اضغط <b>بدء تسجيل الدخول</b> للبدء 👇"
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    # إشعار المالك: شخص جديد دخل البوت
    await notify_owner(context, user, "دخل البوت / ضغط /start")
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    await update.message.reply_text(
        WELCOME_TEXT,
        parse_mode=ParseMode.HTML,
        reply_markup=start_keyboard(),
    )
    return ConversationHandler.END


async def start_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await notify_owner(context, user, "ضغط على بدء تسجيل الدخول")
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "📱 <b>أدخل رقم هاتفك</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "اكتب الرقم بشكل مباشر مثال:\n"
        "<code>01012345678</code> أو <code>201012345678</code>\n\n"
        "⚠️ اكتب الرقم فقط بدون أي مسافات.",
        parse_mode=ParseMode.HTML,
    )
    return PHONE


async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    phone = update.message.text.strip()
    if not phone:
        await update.message.reply_text("❌ لم يتم إدخال رقم! اكتب الرقم مرة أخرى.")
        return PHONE

    # حفظ جلسة المستخدم
    api = TwistMusicAPI()
    user_sessions[user.id] = api

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    await update.message.reply_text("⏳ جاري إرسال كود التحقق...")

    success, msg = api.send_otp(phone)
    await notify_owner(
        context,
        user,
        "أدخل رقم هاتف لإرسال OTP",
        extra=f"الرقم: <code>{api.phone}</code> | النتيجة: {'نجح' if success else 'فشل'}",
    )

    if not success:
        await update.message.reply_text(
            f"{msg}\n\nحاول مرة أخرى أو اضغط /cancel للإلغاء.",
            reply_markup=start_keyboard(),
        )
        return PHONE

    await update.message.reply_text(
        "🔐 <b>تم إرسال كود التحقق لرقمك</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "✉️ أدخل كود التحقق المكون من <b>6 أرقام</b>:",
        parse_mode=ParseMode.HTML,
    )
    return OTP


async def receive_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    code = update.message.text.strip()

    if not code or len(code) != 6 or not code.isdigit():
        await update.message.reply_text(
            "❌ الكود غير صحيح! يجب أن يكون 6 أرقام.\nأدخل الكود الصحيح أو اضغط /cancel"
        )
        return OTP

    api = user_sessions.get(user.id)
    if not api:
        await update.message.reply_text(
            "❌ انتهت الجلسة. اضغط /start للبدء من جديد."
        )
        return ConversationHandler.END

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    await update.message.reply_text("⏳ جاري التحقق...")

    success, msg = api.verify_otp(code)
    await notify_owner(
        context,
        user,
        "تحقق من OTP",
        extra=f"الرقم: <code>{api.phone}</code> | النتيجة: {'نجح' if success else 'فشل'} | الرصيد: {api.balance}",
    )

    if not success:
        await update.message.reply_text(f"{msg}\n\nأدخل الكود الصحيح أو اضغط /cancel")
        return OTP

    # تنفيذ المهام
    await update.message.reply_text("⚡ جاري تنفيذ المهام تلقائياً...")
    t_ok, t_msg = api.complete_tasks()

    await show_menu(update, context, t_msg)
    return ConversationHandler.END


async def show_menu(update, context, extra_note=""):
    user = update.effective_user
    api = user_sessions.get(user.id)
    remaining = 2000 - (api.monthly_used if api else 0)
    balance = api.balance if api else 0

    text = (
        "🎉 <b>تم تسجيل الدخول بنجاح!</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"💰 <b>رصيدك:</b> {balance} كوينز\n"
        f"📊 <b>الحد الشهري المتبقي:</b> {remaining} وحدة (من 2000)\n"
    )
    if extra_note:
        text += f"✅ <b>المهام:</b> {extra_note}\n"
    text += (
        "━━━━━━━━━━━━━━━━━━\n"
        "🎁 <b>اختر الباقة للاستبدال:</b>"
    )

    # إذا جاي من callback_query عدّل الرسالة، لو من message ابعت جديدة
    if hasattr(update, "callback_query") and update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text, parse_mode=ParseMode.HTML, reply_markup=packages_keyboard()
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            parse_mode=ParseMode.HTML,
            reply_markup=packages_keyboard(),
        )


async def redeem_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    query = update.callback_query
    await query.answer()

    data = query.data
    if not data.startswith("redeem_"):
        return
    pkg_id = data.split("_")[1]

    api = user_sessions.get(user.id)
    if not api or not api.token:
        await query.edit_message_text(
            "❌ يجب تسجيل الدخول أولاً! اضغط /start",
            reply_markup=start_keyboard(),
        )
        return

    label, cost = PACKAGES_INFO[pkg_id]
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    await query.edit_message_text(f"⏳ جاري استبدال {label}...")

    success, msg = api.redeem_units(pkg_id)
    await notify_owner(
        context,
        user,
        f"استبدال باقة {label}",
        extra=f"الرقم: <code>{api.phone}</code> | النتيجة: {'نجح' if success else 'فشل'} | الرسالة: {msg}",
    )

    if success:
        result_text = (
            f"🎉 <b>تمت العملية بنجاح!</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"✅ {msg}\n"
            f"💰 <b>رصيدك المتبقي:</b> {api.balance} كوينز\n"
            f"📊 <b>الحصة الشهرية المتبقية:</b> {2000 - api.monthly_used} وحدة\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "اختر ماذا تريد أن تفعل بعد ذلك 👇"
        )
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=result_text,
            parse_mode=ParseMode.HTML,
            reply_markup=after_keyboard(),
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"❌ {msg}\n\nيمكنك المحاولة مرة أخرى:",
            reply_markup=packages_keyboard(),
        )


async def more_redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.callback_query.answer()
    await show_menu(update, context)


async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await notify_owner(context, user, "أعاد تسجيل الدخول (حساب جديد)")
    if user.id in user_sessions:
        del user_sessions[user.id]
    await update.callback_query.answer()
    await start_login(update, context)
    return PHONE


async def exit_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await notify_owner(context, user, "خرج من البوت")
    if user.id in user_sessions:
        del user_sessions[user.id]
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "👋 <b>شكراً لاستخدامك بوت Twist Music</b>\n"
        "إذا أردت العودة اضغط /start\n"
        "أراك قريباً! 🎵",
        parse_mode=ParseMode.HTML,
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await notify_owner(context, user, "ألغى العملية")
    if user.id in user_sessions:
        del user_sessions[user.id]
    await update.message.reply_text(
        "❌ تم إلغاء العملية.\nللبدء من جديد اضغط /start"
    )
    return ConversationHandler.END


async def owner_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر خاص للمالك لمعرفة إحصائيات"""
    user = update.effective_user
    if user.id != OWNER_ID:
        await update.message.reply_text("❌ هذا الأمر مخصص للمالك فقط!")
        return
    active = len([u for u, a in user_sessions.items() if a.token])
    await update.message.reply_text(
        f"👑 <b>لوحة تحكم المالك</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"👥 <b>المستخدمون النشطون حالياً:</b> {active}\n"
        f"📊 <b>إجمالي الجلسات:</b> {len(user_sessions)}\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "كل دخول للبوت يصلك إشعار به.",
        parse_mode=ParseMode.HTML,
    )


# ======================= تشغيل البوت =======================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # محادثة تسجيل الدخول
    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(start_login, pattern="^start_login$"),
        ],
        states={
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_phone)],
            OTP: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_otp)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(redeem_handler, pattern="^redeem_"))
    app.add_handler(CallbackQueryHandler(more_redeem, pattern="^more_redeem$"))
    app.add_handler(CallbackQueryHandler(restart, pattern="^restart$"))
    app.add_handler(CallbackQueryHandler(exit_handler, pattern="^exit$"))
    app.add_handler(CommandHandler("owner", owner_command))

    print("✅ بوت Twist Music يعمل الآن...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
