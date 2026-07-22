import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# تفعيل سجلات الأخطاء (Logging)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# دالة التعامل مع أمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    await update.message.reply_text(f"أهلاً بك {user_name}! البوت شغال ونشط حالياً على الاستضافة 🚀")

# دالة التعامل مع أمر /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أرسل لي أي رسالة نصية وسأقوم بالرد عليك مباشرة!")

# دالة للرد على الرسائل النصية العادية
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await update.message.reply_text(f"وصلتني رسالتك: {user_text}")

if __name__ == '__main__':
    # ⚠️ استبدل YOUR_TELEGRAM_BOT_TOKEN بالتوكن الخاص بك من BotFather
    TOKEN = "8546444968:AAFejAxd7ESvYNWLvFCWZG7993HmzhbMb8Y"

    # بناء التطبيق
    app = ApplicationBuilder().token(TOKEN).build()

    # إضافة الأوامر والتعامل مع الرسائل
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # تشغيل البوت
    print("البوت يعمل الآن...")
    app.run_polling()

