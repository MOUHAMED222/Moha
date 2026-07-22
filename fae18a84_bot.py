import nest_asyncio
nest_asyncio.apply()
import logging
import sqlite3
import asyncio
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
    ConversationHandler
)

TOKEN = "8810136232:AAFeliDJ2HIPr_avNx-OTrLO1DR6xOMPlxI"
OWNER_ID = 300714964

CHANNEL_USERNAME = "@tmxl5" 
CHANNEL_URL = "https://t.me/tmxl5"

(
    WAITING_FOR_MEDIA, 
    WAITING_FOR_TIMER, 
    WAITING_FOR_BROADCAST, 
    WAITING_FOR_WELCOME_TEXT,
    WAITING_FOR_DELETE_ID,
    WAITING_FOR_ADD_ADMIN,
    WAITING_FOR_REMOVE_ADMIN,
    WAITING_FOR_DISABLE_LINK,
    WAITING_FOR_ENABLE_LINK
) = range(9)

def init_db():
    conn = sqlite3.connect("bot_media.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS media (
            id TEXT PRIMARY KEY,
            file_id TEXT NOT NULL,
            media_type TEXT NOT NULL,
            caption TEXT,
            delete_time INTEGER NOT NULL,
            status INTEGER DEFAULT 1,
            creator_name TEXT,
            creator_user TEXT,
            creator_id INTEGER
        )
    ''')
    cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)')
    cursor.execute('CREATE TABLE IF NOT EXISTS admins (user_id INTEGER PRIMARY KEY)')
    cursor.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('welcome_text', ?)", 
                   ("أهلاً بك في البوت الرسمي! 👋\n\n📌 للحصول على المحتوى المخصص، يرجى الضغط على الروابط المنشورة داخل القناة.",))
    conn.commit()
    conn.close()

init_db()

def is_admin(user_id):
    if user_id == OWNER_ID:
        return True
    conn = sqlite3.connect("bot_media.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM admins WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return True if res else False

def add_user(user_id):
    conn = sqlite3.connect("bot_media.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def get_welcome_text():
    conn = sqlite3.connect("bot_media.db")
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'welcome_text'")
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else "أهلاً بك!"

def set_welcome_text(new_text):
    conn = sqlite3.connect("bot_media.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE settings SET value = ? WHERE key = 'welcome_text'", (new_text,))
    conn.commit()
    conn.close()

async def check_subscription(user_id, context):
    if is_admin(user_id):
        return True
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
    except Exception:
        return True
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    args = context.args

    add_user(user_id)

    is_subscribed = await check_subscription(user_id, context)
    if not is_subscribed:
        keyboard = [
            [InlineKeyboardButton("📢 اشترك بالقناة أولاً", url=CHANNEL_URL)],
            [InlineKeyboardButton("✅ تأكيد الاشتراك", callback_data=f"check_sub_{args[0] if args else 'none'}")]
        ]
        await update.message.reply_text(
            "⚠️ عذراً عزيزي، يجب عليك الاشتراك بقناة البوت أولاً لتتمكن من استخدام الخدمة!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if args:
        await send_temporary_media(chat_id, args[0], context)
        return

    await show_main_menu(update, context)

async def check_sub_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data.replace("check_sub_", "")

    if await check_subscription(user_id, context):
        await query.message.delete()
        if data != "none":
            await send_temporary_media(query.message.chat_id, data, context)
        else:
            await show_main_menu(update, context)
    else:
        await query.message.reply_text("❌ لم تشترك بالقناة بعد! اشترك ثم اضغط تأكيد.")

async def send_temporary_media(chat_id, media_id, context):
    conn = sqlite3.connect("bot_media.db")
    cursor = conn.cursor()
    cursor.execute("SELECT file_id, media_type, caption, delete_time, status FROM media WHERE id = ?", (media_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        file_id, media_type, caption, delete_time, status = result
        if status == 0:
            await context.bot.send_message(chat_id=chat_id, text="⚠️ هذا الرابط معطل حالياً من قبل الإدارة.")
            return

        if media_type == "photo":
            sent_msg = await context.bot.send_photo(chat_id=chat_id, photo=file_id, caption=caption)
        elif media_type == "video":
            sent_msg = await context.bot.send_video(chat_id=chat_id, video=file_id, caption=caption)
        else:
            sent_msg = await context.bot.send_message(chat_id=chat_id, text=caption or "المحتوى المطلوب")

        warning_msg = await context.bot.send_message(
            chat_id=chat_id, 
            text=f"⏳ سيتم حذف هذا المحتوى تلقائياً بعد {delete_time} ثانية."
        )

        await asyncio.sleep(delete_time)
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=sent_msg.message_id)
            await context.bot.delete_message(chat_id=chat_id, message_id=warning_msg.message_id)
        except Exception:
            pass
    else:
        await context.bot.send_message(chat_id=chat_id, text="❌ هذا الرابط غير صالح أو تم حذفه.")
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    welcome_text = get_welcome_text()

conn = sqlite3.connect("bot_media.db")
cursor = conn.cursor()

cursor.execute("SELECT value FROM settings WHERE key='welcome_photo'")
photo = cursor.fetchone()

cursor.execute("SELECT value FROM settings WHERE key='welcome_caption'")
caption = cursor.fetchone()

conn.close()
    
    if is_admin(user_id):
        keyboard = [
            [InlineKeyboardButton("توليد رابط", callback_data="btn_add")],
            [InlineKeyboardButton("اذاعة", callback_data="btn_broadcast")],
            [InlineKeyboardButton("اضافة مشرف", callback_data="btn_add_admin"), InlineKeyboardButton("حذف مشرف", callback_data="btn_remove_admin")],
            [InlineKeyboardButton("قائمة المشرفين", callback_data="btn_list_admins")],
            [InlineKeyboardButton("حذف رابط", callback_data="btn_delete"), InlineKeyboardButton("تعطيل الرابط", callback_data="btn_disable_link")],
            [InlineKeyboardButton("احياء رابط", callback_data="btn_enable_link"), InlineKeyboardButton("تصفير جميع الروابط", callback_data="btn_clear_all")],
            [InlineKeyboardButton("عدد المستخدمين", callback_data="btn_stats")],
            [InlineKeyboardButton("تعديل start", callback_data="btn_edit_welcome")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        msg_text = "⚙️ **لوحة التحكم**"
    else:
        keyboard = [[InlineKeyboardButton("📢 زيارة القناة", url=CHANNEL_URL)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
msg_text = welcome_text

if photo:
    if update.callback_query:
        await update.callback_query.message.reply_photo(
            photo=photo[0],
            caption=caption[0] if caption else "",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_photo(
            photo=photo[0],
            caption=caption[0] if caption else "",
            reply_markup=reply_markup
        )
    return

    if update.callback_query:
        await update.callback_query.message.reply_text(msg_text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(msg_text, reply_markup=reply_markup, parse_mode="Markdown")

async def add_media_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query: await query.answer()
    await context.bot.send_message(chat_id=update.effective_chat.id, text="📸 أرسل الآن الصورة أو الفيديو المطلوب:")
    return WAITING_FOR_MEDIA

async def receive_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if message.photo:
        context.user_data['file_id'] = message.photo[-1].file_id
        context.user_data['media_type'] = "photo"
    elif message.video:
        context.user_data['file_id'] = message.video.file_id
        context.user_data['media_type'] = "video"
    else:
        await update.message.reply_text("❌ يرجى إرسال صورة أو فيديو فقط.")
        return WAITING_FOR_MEDIA

    context.user_data['caption'] = message.caption or ""
    await update.message.reply_text("⏱ أدخل وقت الحذف بالثواني (مثال: 10):")
    return WAITING_FOR_TIMER

async def receive_timer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text.strip().translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
    if not text.isdigit():
        await update.message.reply_text("❌ أدخل رقماً صحيحاً بالثواني.")
        return WAITING_FOR_TIMER

    delete_time = int(text)
    media_id = str(uuid.uuid4())[:8]

    creator_name = user.full_name
    creator_user = f"@{user.username}" if user.username else "لا يوجد"
    creator_id = user.id

    conn = sqlite3.connect("bot_media.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO media (id, file_id, media_type, caption, delete_time, status, creator_name, creator_user, creator_id) VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?)",
        (media_id, context.user_data['file_id'], context.user_data['media_type'], context.user_data['caption'], delete_time, creator_name, creator_user, creator_id)
    )
    conn.commit()
    conn.close()

    bot_username = (await context.bot.get_me()).username
    share_link = f"https://t.me/{bot_username}?start={media_id}"

    info_msg = f"تم انشاء رابط جديد:\n{share_link}\n\nالمنشئ: {creator_name}\nاليوزر: {creator_user}\nالايدي: `{creator_id}`"
    keyboard = [
        [InlineKeyboardButton("عرض المحتوى", callback_data=f"preview_{media_id}")],
        [InlineKeyboardButton("تعطيل الرابط", callback_data=f"disable_{media_id}")]
    ]

    await update.message.reply_text(info_msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    context.user_data.clear()
    return ConversationHandler.END

async def preview_or_disable(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("preview_"):
        media_id = data.replace("preview_", "")
        await send_temporary_media(query.message.chat_id, media_id, context)
    elif data.startswith("disable_"):
        media_id = data.replace("disable_", "")
        conn = sqlite3.connect("bot_media.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE media SET status = 0 WHERE id = ?", (media_id,))
        conn.commit()
        conn.close()
        await query.message.reply_text("✅ تم تعطيل الرابط بنجاح!")

async def add_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("👤 أرسل الـ User ID الخاص بالمشرف الجديد:")
    return WAITING_FOR_ADD_ADMIN

async def receive_add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
    if not text.isdigit():
        await update.message.reply_text("❌ أرسل ID صحيح.")
        return WAITING_FOR_ADD_ADMIN

    new_admin_id = int(text)
    conn = sqlite3.connect("bot_media.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (new_admin_id,))
    conn.commit()
    conn.close()

    await update.message.reply_text(f"✅ تم إضافة المشرف `{new_admin_id}` بنجاح!", parse_mode="Markdown")
    return ConversationHandler.END

async def remove_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("❌ أرسل الـ User ID الخاص بالمشرف لإزالته:")
    return WAITING_FOR_REMOVE_ADMIN

async def receive_remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
    if not text.isdigit():
        await update.message.reply_text("❌ أرسل ID صحيح.")
        return WAITING_FOR_REMOVE_ADMIN

    target_id = int(text)
    conn = sqlite3.connect("bot_media.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM admins WHERE user_id = ?", (target_id,))
    conn.commit()
    conn.close()

    await update.message.reply_text(f"✅ تم حذف المشرف `{target_id}` بنجاح!", parse_mode="Markdown")
    return ConversationHandler.END

async def list_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    conn = sqlite3.connect("bot_media.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM admins")
    admins = cursor.fetchall()
    conn.close()

    text = f"👑 **المالك الأساسي:** `{OWNER_ID}`\n\n👥 **قائمة المشرفين:**\n"
    if admins:
        for idx, adm in enumerate(admins, 1):
            text += f"{idx}. `{adm[0]}`\n"
    else:
        text += "لا يوجد مشرفين مضافين حالياً."

    await query.message.reply_text(text, parse_mode="Markdown")

async def disable_link_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("⚠️ أرسل كود الرابط المراد تعطيله:")
    return WAITING_FOR_DISABLE_LINK

async def receive_disable_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link_id = update.message.text.strip()
    conn = sqlite3.connect("bot_media.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE media SET status = 0 WHERE id = ?", (link_id,))
    conn.commit()
    conn.close()
    await update.message.reply_text("✅ تم تعطيل الرابط!")
    return ConversationHandler.END

async def enable_link_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("🔄 أرسل كود الرابط المراد إحياؤه/تفعيله:")
    return WAITING_FOR_ENABLE_LINK

async def receive_enable_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link_id = update.message.text.strip()
    conn = sqlite3.connect("bot_media.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE media SET status = 1 WHERE id = ?", (link_id,))
    conn.commit()
    conn.close()
    await update.message.reply_text("✅ تم إحياء/تفعيل الرابط بنجاح!")
    return ConversationHandler.END

async def clear_all_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    conn = sqlite3.connect("bot_media.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM media")
    conn.commit()
    conn.close()

    await query.message.reply_text("🔥 تم تصفير وحذف جميع الروابط المخزنة بنجاح!")

async def delete_media_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("🗑️ أرسل كود الملف (ID) الذي تريد حذفه النهائي:")
    return WAITING_FOR_DELETE_ID

async def receive_delete_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    media_id = update.message.text.strip()
    conn = sqlite3.connect("bot_media.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM media WHERE id = ?", (media_id,))
    rows = cursor.rowcount
    conn.commit()
    conn.close()

    if rows > 0:
        await update.message.reply_text("✅ تم حذف المحتوى بنجاح!")
    else:
        await update.message.reply_text("❌ لم يتم العثور على رابط بهذا الكود.")
    return ConversationHandler.END

async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("📢 أرسل الرسالة لتوزيعها على جميع المستخدمين:")
    return WAITING_FOR_BROADCAST

async def receive_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    broadcast_msg = update.message.text
    conn = sqlite3.connect("bot_media.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    conn.close()

    success, failed = 0, 0
    for u in users:
        try:
            await context.bot.send_message(chat_id=u[0], text=broadcast_msg)
            success += 1
        except Exception: 
            failed += 1

    await update.message.reply_text(f"✅ اكتملت الإذاعة!\n\nنجاح: {success}\nفشل: {failed}")
    return ConversationHandler.END

async def edit_welcome_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("⚙️ أرسل كليشة الترحيب الجديدة للـ start:")
    return WAITING_FOR_WELCOME_TEXT

async def receive_welcome_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect("bot_media.db")
    cursor = conn.cursor()

    if update.message.text:
        cursor.execute("REPLACE INTO settings (key,value) VALUES('welcome_type','text')")
        cursor.execute("REPLACE INTO settings (key,value) VALUES('welcome_text',?)", (update.message.text,))

    elif update.message.photo:
        cursor.execute("REPLACE INTO settings (key,value) VALUES('welcome_type','photo')")
        cursor.execute("REPLACE INTO settings (key,value) VALUES('welcome_file',?)", (update.message.photo[-1].file_id,))
        cursor.execute("REPLACE INTO settings (key,value) VALUES('welcome_caption',?)", (update.message.caption or "",))

    elif update.message.video:
        cursor.execute("REPLACE INTO settings (key,value) VALUES('welcome_type','video')")
        cursor.execute("REPLACE INTO settings (key,value) VALUES('welcome_file',?)", (update.message.video.file_id,))
        cursor.execute("REPLACE INTO settings (key,value) VALUES('welcome_caption',?)", (update.message.caption or "",))

    elif update.message.animation:
        cursor.execute("REPLACE INTO settings (key,value) VALUES('welcome_type','animation')")
        cursor.execute("REPLACE INTO settings (key,value) VALUES('welcome_file',?)", (update.message.animation.file_id,))
        cursor.execute("REPLACE INTO settings (key,value) VALUES('welcome_caption',?)", (update.message.caption or "",))

    elif update.message.document:
        cursor.execute("REPLACE INTO settings (key,value) VALUES('welcome_type','document')")
        cursor.execute("REPLACE INTO settings (key,value) VALUES('welcome_file',?)", (update.message.document.file_id,))
        cursor.execute("REPLACE INTO settings (key,value) VALUES('welcome_caption',?)", (update.message.caption or "",))

    elif update.message.audio:
        cursor.execute("REPLACE INTO settings (key,value) VALUES('welcome_type','audio')")
        cursor.execute("REPLACE INTO settings (key,value) VALUES('welcome_file',?)", (update.message.audio.file_id,))
        cursor.execute("REPLACE INTO settings (key,value) VALUES('welcome_caption',?)", (update.message.caption or "",))

    elif update.message.voice:
        cursor.execute("REPLACE INTO settings (key,value) VALUES('welcome_type','voice')")
        cursor.execute("REPLACE INTO settings (key,value) VALUES('welcome_file',?)", (update.message.voice.file_id,))

    elif update.message.video_note:
        cursor.execute("REPLACE INTO settings (key,value) VALUES('welcome_type','video_note')")
        cursor.execute("REPLACE INTO settings (key,value) VALUES('welcome_file',?)", (update.message.video_note.file_id,))

    else:
        await update.message.reply_text("❌ أرسل نص أو أي نوع من الوسائط.")
        conn.close()
        return WAITING_FOR_WELCOME_TEXT

    conn.commit()
    conn.close()

    await update.message.reply_text("✅ تم حفظ رسالة الـ Start بنجاح.")
    return ConversationHandler.END

        conn = sqlite3.connect("bot_media.db")
        cursor = conn.cursor()
        cursor.execute("REPLACE INTO settings (key,value) VALUES('welcome_photo',?)",(file_id,))
        cursor.execute("REPLACE INTO settings (key,value) VALUES('welcome_caption',?)",(caption,))
        conn.commit()
        conn.close()

        await update.message.reply_text("✅ تم حفظ صورة الـ Start.")
        return ConversationHandler.END

    elif update.message.text:
        conn = sqlite3.connect("bot_media.db")
        cursor = conn.cursor()
        cursor.execute("REPLACE INTO settings (key,value) VALUES('welcome_text',?)",(update.message.text,))
        conn.commit()
        conn.close()

        await update.message.reply_text("✅ تم حفظ نص الـ Start.")
        return ConversationHandler.END

    await update.message.reply_text("❌ أرسل صورة أو نص فقط.")
    return WAITING_FOR_WELCOME_TEXT

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    conn = sqlite3.connect("bot_media.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    u_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM media")
    m_count = cursor.fetchone()[0]
    conn.close()

    await query.message.reply_text(f"📊 **عدد المستخدمين الإجمالي:** {u_count}\n📂 **إجمالي الروابط:** {m_count}", parse_mode="Markdown")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("تم إلغاء العملية.")
    return ConversationHandler.END

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    add_h = ConversationHandler(
        entry_points=[CommandHandler("add", add_media_start), CallbackQueryHandler(add_media_start, pattern="^btn_add$")],
        states={
            WAITING_FOR_MEDIA: [MessageHandler(filters.PHOTO | filters.VIDEO, receive_media)],
            WAITING_FOR_TIMER: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_timer)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    del_h = ConversationHandler(
        entry_points=[CallbackQueryHandler(delete_media_start, pattern="^btn_delete$")],
        states={WAITING_FOR_DELETE_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_delete_id)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    bc_h = ConversationHandler(
        entry_points=[CallbackQueryHandler(broadcast_start, pattern="^btn_broadcast$")],
        states={WAITING_FOR_BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_broadcast)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    wel_h = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_welcome_start, pattern="^btn_edit_welcome$")],
        states={WAITING_FOR_WELCOME_TEXT: MessageHandler((filters.TEXT | filters.PHOTO) & ~filters.COMMAND, receive_welcome_text)
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    add_admin_h = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_admin_start, pattern="^btn_add_admin$")],
        states={WAITING_FOR_ADD_ADMIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_add_admin)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    rem_admin_h = ConversationHandler(
        entry_points=[CallbackQueryHandler(remove_admin_start, pattern="^btn_remove_admin$")],
        states={WAITING_FOR_REMOVE_ADMIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_remove_admin)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    dis_h = ConversationHandler(
        entry_points=[CallbackQueryHandler(disable_link_start, pattern="^btn_disable_link$")],
        states={WAITING_FOR_DISABLE_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_disable_link)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    ena_h = ConversationHandler(
        entry_points=[CallbackQueryHandler(enable_link_start, pattern="^btn_enable_link$")],
        states={WAITING_FOR_ENABLE_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_enable_link)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_sub_callback, pattern="^check_sub_"))
    app.add_handler(CallbackQueryHandler(preview_or_disable, pattern="^(preview_|disable_)"))
    app.add_handler(add_h)
    app.add_handler(del_h)
    app.add_handler(bc_h)
    app.add_handler(wel_h)
    app.add_handler(add_admin_h)
    app.add_handler(rem_admin_h)
    app.add_handler(dis_h)
    app.add_handler(ena_h)
    app.add_handler(CallbackQueryHandler(list_admins, pattern="^btn_list_admins$"))
    app.add_handler(CallbackQueryHandler(clear_all_links, pattern="^btn_clear_all$"))
    app.add_handler(CallbackQueryHandler(show_stats, pattern="^btn_stats$"))

    print("تم تشغيل البوت بنجاح...")
    app.run_polling()
