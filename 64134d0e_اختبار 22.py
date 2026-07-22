from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)

TOKEN = "8833337494:AAEKql5c5VBuM4mzl-JHSfgtIhPkCJrhYfg"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton(
                text="⚠️ زر تجريبي",
                callback_data="test_button",
                style="danger"
            )
        ]
    ]

    await update.message.reply_html(
        "<b>مرحبًا بك في البوت</b>",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))

print("Bot Started...")
app.run_polling()