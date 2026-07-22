from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import asyncio

DEVELOPER_ID = 8382128254  # غيّر الرقم إلى الـ ID الخاص بك

messages = []
interval_minutes = 1
running = False
publish_task = None

def is_developer(update: Update):
    return update.effective_user.id == DEVELOPER_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_developer(update):
        return await update.message.reply_text("❌ غير مسموح لك باستخدام هذا البوت")
    
    keyboard = [
        [InlineKeyboardButton("➕ إضافة رسالة", callback_data="add")],
        [InlineKeyboardButton("⏱️ ضبط الوقت", callback_data="set")],
        [InlineKeyboardButton("🚀 بدء النشر", callback_data="publish")],
        [InlineKeyboardButton("⛔️ إيقاف النشر", callback_data="stop")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("لوحة التحكم:", reply_markup=reply_markup)

async def publisher(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    global running
    while running:
        for msg in messages:
            await context.bot.send_message(chat_id=chat_id, text=msg)
            await asyncio.sleep(interval_minutes * 60)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    global running, publish_task

    if not is_developer(update):
        return await query.edit_message_text("❌ غير مسموح لك باستخدام هذا البوت")

    if query.data == "add":
        await query.edit_message_text("اكتب الأمر هكذا:\n/add رسالتك هنا")
    elif query.data == "set":
        await query.edit_message_text("اكتب الأمر هكذا:\n/set عدد_الدقائق")
    elif query.data == "publish":
        if not running:
            running = True
            publish_task = asyncio.create_task(publisher(context, query.message.chat_id))
            await query.edit_message_text("بدأ النشر التلقائي 🚀")
    elif query.data == "stop":
        running = False
        if publish_task:
            publish_task.cancel()
        await query.edit_message_text("تم إيقاف النشر ⛔️")

async def add_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_developer(update):
        return await update.message.reply_text("❌ غير مسموح لك باستخدام هذا البوت")

    msg = " ".join(context.args)
    if msg:
        messages.append(msg)
        await update.message.reply_text(f"تمت إضافة الرسالة: {msg}")
    else:
        await update.message.reply_text("اكتب الرسالة بعد الأمر /add")

async def set_interval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_developer(update):
        return await update.message.reply_text("❌ غير مسموح لك باستخدام هذا البوت")

    global interval_minutes
    try:
        interval_minutes = int(context.args[0])
        await update.message.reply_text(f"تم ضبط الفترة الزمنية إلى {interval_minutes} دقيقة")
    except:
        await update.message.reply_text("استخدم الأمر هكذا: /set 5")

app = Application.builder().token("7985197674:AAED9KqfgtuUXlC6zzylSyuBPrk_EVZO8dI").build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(CommandHandler("add", add_message))
app.add_handler(CommandHandler("set", set_interval))

app.run_polling()