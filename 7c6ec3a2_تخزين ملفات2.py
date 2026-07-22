#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
import sqlite3
import os
import random
import string
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    Message, CallbackQuery
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, ContextTypes, filters
)
from telegram.constants import ParseMode

BOT_TOKEN = "8833337494:AAH9e7f6PWrhsHiFa2Ju8gbXhf1Cc58NYo8"
OWNER_ID = 6891530912
STORAGE_CHANNEL_ID = -1004280898981
OWNER_PHOTO = "https://d.top4top.io/p_38534mjfh0.jpg"
DB_FILE = "files.db"
ITEMS_PER_PAGE = 10

FOLDERS = [
    "Images",
    "Videos",
    "Audio",
    "Documents",
    "Archives",
    "APK",
    "Programs",
    "Code",
    "Fonts",
    "Other"
]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_database() -> None:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT NOT NULL,
            file_unique_id TEXT,
            name TEXT NOT NULL,
            original_name TEXT NOT NULL,
            type TEXT NOT NULL,
            size INTEGER NOT NULL,
            upload_date TIMESTAMP NOT NULL,
            last_update TIMESTAMP NOT NULL,
            folder TEXT NOT NULL,
            description TEXT,
            tags TEXT,
            pinned INTEGER DEFAULT 0,
            views INTEGER DEFAULT 0,
            message_id INTEGER NOT NULL,
            channel_id TEXT NOT NULL,
            deleted INTEGER DEFAULT 0,
            deleted_at TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            version_number INTEGER NOT NULL,
            file_id_tg TEXT NOT NULL,
            file_unique_id TEXT,
            name TEXT NOT NULL,
            size INTEGER NOT NULL,
            upload_date TIMESTAMP NOT NULL,
            message_id INTEGER NOT NULL,
            channel_id TEXT NOT NULL,
            FOREIGN KEY(file_id) REFERENCES files(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS share_tokens (
            token TEXT PRIMARY KEY,
            file_id INTEGER NOT NULL,
            expiry TIMESTAMP NOT NULL,
            FOREIGN KEY(file_id) REFERENCES files(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_name ON files(name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_folder ON files(folder)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_deleted ON files(deleted)")

    conn.commit()
    conn.close()
    logger.info("Database initialized successfully.")

def get_category_by_extension(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext in ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'):
        return "Images"
    elif ext in ('.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm'):
        return "Videos"
    elif ext in ('.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma'):
        return "Audio"
    elif ext in ('.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.rtf', '.odt', '.ods'):
        return "Documents"
    elif ext in ('.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz'):
        return "Archives"
    elif ext == '.apk':
        return "APK"
    elif ext in ('.exe', '.msi', '.sh', '.bat', '.cmd', '.jar'):
        return "Programs"
    elif ext in ('.py', '.js', '.java', '.c', '.cpp', '.go', '.rb', '.php', '.html', '.css', '.json', '.xml'):
        return "Code"
    elif ext in ('.ttf', '.otf', '.woff', '.woff2', '.eot'):
        return "Fonts"
    else:
        return "Other"

def format_file_number(file_id: int) -> str:
    return f"#{file_id:06d}"

def format_file_size(size: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"

def escape_markdown(text: str) -> str:
    if not text:
        return ""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f"\\{char}")
    return text

def escape_outside_backticks(text: str) -> str:
    parts = text.split('`')
    result = []
    for i, part in enumerate(parts):
        if i % 2 == 0:
            result.append(escape_markdown(part))
        else:
            result.append(part)
    return '`'.join(result)

def format_blockquote(text: str) -> str:
    escaped = escape_outside_backticks(text)
    lines = escaped.split('\n')
    return '\n'.join(f"> {line}" for line in lines)

def format_file_info(file: Dict) -> str:
    number = format_file_number(file['id'])
    name = escape_markdown(file['name'])
    original = escape_markdown(file['original_name'])
    file_type = file['type']
    size = format_file_size(file['size'])
    folder = file['folder']
    upload = file['upload_date']
    last = file['last_update']
    pinned = "✅ مثبت" if file['pinned'] else "❌ غير مثبت"
    views = file['views']
    desc = escape_markdown(file['description']) if file['description'] else "لا يوجد وصف"
    tags = escape_markdown(file['tags']) if file['tags'] else "لا يوجد وسوم"

    upload_dt = datetime.fromisoformat(upload)
    last_dt = datetime.fromisoformat(last)
    upload_str = upload_dt.strftime('%Y-%m-%d %H:%M')
    last_str = last_dt.strftime('%Y-%m-%d %H:%M')

    lines = [
        f"📁 *رقم الملف:* `{number}`",
        f"📄 *الاسم الحالي:* `{name}`",
        f"📎 *الاسم الأصلي:* `{original}`",
        f"🏷️ *النوع:* `{file_type}`",
        f"📦 *الحجم:* `{size}`",
        f"📂 *المجلد:* `{folder}`",
        f"📅 *تاريخ الرفع:* `{upload_str}`",
        f"🔄 *آخر تحديث:* `{last_str}`",
        f"⭐ *الحالة:* {pinned}",
        f"📝 *الوصف:*\n`{desc}`",
        f"🏷️ *الوسوم:* `{tags}`",
        f"👁️ *عدد المشاهدات:* `{views}`"
    ]
    return format_blockquote("\n".join(lines))

def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID

async def safe_edit(query: CallbackQuery, text: str, reply_markup: InlineKeyboardMarkup = None, parse_mode: str = ParseMode.MARKDOWN_V2) -> None:
    try:
        if query.message.photo or query.message.document or query.message.video or query.message.audio:
            await query.edit_message_caption(
                caption=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        else:
            await query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
    except Exception as e:
        logger.error(f"Safe edit failed: {e}")
        await query.message.reply_text(text, reply_markup=reply_markup, parse_mode=None)

(WAITING_FOR_UPLOAD,
 WAITING_FOR_RENAME,
 WAITING_FOR_DESCRIPTION,
 WAITING_FOR_TAGS,
 WAITING_FOR_SEARCH,
 WAITING_FOR_REPLACE) = range(6)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user or not is_owner(user.id):
        await update.message.reply_text("🚫 هذا البوت خاص بالمالك فقط")
        return
    await send_main_menu(update, context)

async def send_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, edit: bool = False) -> None:
    text = format_blockquote(
        "🌟 *مرحباً أيها المالك!*\n\n"
        "📦 هذا البوت لإدارة وتخزين ملفاتك بشكل احترافي.\n"
        "👇 اختر أحد الخيارات أدناه:"
    )

    keyboard = [
        [
            InlineKeyboardButton("📤 رفع ملف", callback_data="menu_upload", style="success"),
            InlineKeyboardButton("📂 عرض الملفات", callback_data="menu_list", style="success")
        ],
        [
            InlineKeyboardButton("🔍 بحث", callback_data="menu_search", style="danger"),
            InlineKeyboardButton("⭐ المثبتات", callback_data="menu_pinned", style="danger")
        ],
        [
            InlineKeyboardButton("📊 الإحصائيات", callback_data="menu_stats", style="primary"),
            InlineKeyboardButton("🗑️ سلة المحذوفات", callback_data="menu_trash", style="primary")
        ],
        [
            InlineKeyboardButton("⚙️ إعدادات", callback_data="menu_settings", style="success")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if OWNER_PHOTO:
        if edit and update.callback_query:
            await update.callback_query.edit_message_caption(
                caption=text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN_V2
            )
        else:
            await update.message.reply_photo(
                photo=OWNER_PHOTO,
                caption=text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN_V2
            )
    else:
        if edit and update.callback_query:
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN_V2
            )
        else:
            await update.message.reply_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN_V2
            )

async def send_main_menu_edit(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = format_blockquote(
        "🌟 *مرحباً أيها المالك!*\n\n"
        "📦 هذا البوت لإدارة وتخزين ملفاتك بشكل احترافي.\n"
        "👇 اختر أحد الخيارات أدناه:"
    )

    keyboard = [
        [
            InlineKeyboardButton("📤 رفع ملف", callback_data="menu_upload", style="success"),
            InlineKeyboardButton("📂 عرض الملفات", callback_data="menu_list", style="success")
        ],
        [
            InlineKeyboardButton("🔍 بحث", callback_data="menu_search", style="danger"),
            InlineKeyboardButton("⭐ المثبتات", callback_data="menu_pinned", style="danger")
        ],
        [
            InlineKeyboardButton("📊 الإحصائيات", callback_data="menu_stats", style="primary"),
            InlineKeyboardButton("🗑️ سلة المحذوفات", callback_data="menu_trash", style="primary")
        ],
        [
            InlineKeyboardButton("⚙️ إعدادات", callback_data="menu_settings", style="success")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if OWNER_PHOTO:
        await query.edit_message_caption(
            caption=text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN_V2
        )
    else:
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN_V2
        )

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if not query.from_user or not is_owner(query.from_user.id):
        await safe_edit(query, "🚫 هذا البوت خاص بالمالك فقط")
        return

    data = query.data
    if data == "menu_upload":
        await start_upload(query, context)
    elif data == "menu_list":
        await list_files(query, context, page=1)
    elif data == "menu_search":
        await start_search(query, context)
    elif data == "menu_pinned":
        await list_pinned(query, context)
    elif data == "menu_stats":
        await show_stats(query, context)
    elif data == "menu_trash":
        await list_trash(query, context)
    elif data == "menu_settings":
        await show_settings(query, context)
    elif data == "menu_home":
        context.user_data.pop('state', None)
        context.user_data.pop('rename_file_id', None)
        context.user_data.pop('replace_file_id', None)
        context.user_data.pop('desc_file_id', None)
        context.user_data.pop('tags_file_id', None)
        await send_main_menu_edit(query, context)

async def start_upload(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = format_blockquote("📤 *رفع ملف جديد*\n\n📎 أرسل الملف الذي تريد تخزينه. يمكنك إرسال صور، فيديو، صوت، مستند، أو أي ملف آخر.")
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="menu_home", style="danger")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await safe_edit(query, text, reply_markup)
    context.user_data['state'] = WAITING_FOR_UPLOAD
    logger.info(f"Upload state set for user {query.from_user.id}")

async def handle_upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("handle_upload called")
    user = update.effective_user
    if not user or not is_owner(user.id):
        logger.warning(f"Non-owner {user.id if user else 'unknown'} tried to upload")
        return

    if context.user_data.get('state') != WAITING_FOR_UPLOAD:
        logger.info(f"Upload ignored, state={context.user_data.get('state')}")
        await update.message.reply_text("⚠️ يرجى الضغط على زر 'رفع ملف' أولاً.")
        return

    message = update.message
    file_obj = None
    file_name = None
    file_size = None

    if message.document:
        file_obj = message.document
        file_name = file_obj.file_name
        file_size = file_obj.file_size
    elif message.photo:
        photo = message.photo[-1]
        file_obj = photo
        file_name = f"photo_{photo.file_unique_id}.jpg"
        file_size = photo.file_size
    elif message.video:
        file_obj = message.video
        file_name = file_obj.file_name or f"video_{file_obj.file_unique_id}.mp4"
        file_size = file_obj.file_size
    elif message.audio:
        file_obj = message.audio
        file_name = file_obj.file_name or f"audio_{file_obj.file_unique_id}.mp3"
        file_size = file_obj.file_size
    elif message.voice:
        file_obj = message.voice
        file_name = f"voice_{file_obj.file_unique_id}.ogg"
        file_size = file_obj.file_size
    elif message.video_note:
        file_obj = message.video_note
        file_name = f"video_note_{file_obj.file_unique_id}.mp4"
        file_size = file_obj.file_size
    else:
        await message.reply_text("⚠️ نوع الملف غير مدعوم. يرجى إرسال ملف، صورة، فيديو، أو صوت.")
        return

    if not file_obj:
        await message.reply_text("⚠️ لم أتمكن من استلام الملف.")
        return

    try:
        forwarded = await context.bot.forward_message(
            chat_id=STORAGE_CHANNEL_ID,
            from_chat_id=message.chat_id,
            message_id=message.message_id
        )

        if forwarded.document:
            tg_file_id = forwarded.document.file_id
            tg_file_unique_id = forwarded.document.file_unique_id
        elif forwarded.photo:
            tg_file_id = forwarded.photo[-1].file_id
            tg_file_unique_id = forwarded.photo[-1].file_unique_id
        elif forwarded.video:
            tg_file_id = forwarded.video.file_id
            tg_file_unique_id = forwarded.video.file_unique_id
        elif forwarded.audio:
            tg_file_id = forwarded.audio.file_id
            tg_file_unique_id = forwarded.audio.file_unique_id
        elif forwarded.voice:
            tg_file_id = forwarded.voice.file_id
            tg_file_unique_id = forwarded.voice.file_unique_id
        elif forwarded.video_note:
            tg_file_id = forwarded.video_note.file_id
            tg_file_unique_id = forwarded.video_note.file_unique_id
        else:
            await message.reply_text("⚠️ تعذر استخراج معرف الملف.")
            return

        folder = get_category_by_extension(file_name)
        conn = get_db_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO files
            (file_id, file_unique_id, name, original_name, type, size, upload_date, last_update, folder, description, tags, pinned, views, message_id, channel_id, deleted)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            tg_file_id, tg_file_unique_id, file_name, file_name,
            folder, file_size, now, now, folder,
            "", "", 0, 0, forwarded.message_id,
            str(STORAGE_CHANNEL_ID), 0
        ))
        file_id = cursor.lastrowid
        conn.commit()
        conn.close()

        number = format_file_number(file_id)
        await message.reply_text(
            format_blockquote(
                f"✅ *تم رفع الملف بنجاح!*\n\n"
                f"📌 *رقم الملف:* `{number}`\n"
                f"📄 *الاسم:* `{file_name}`\n"
                f"📂 *المجلد:* `{folder}`\n"
                f"📦 *الحجم:* {format_file_size(file_size)}"
            ),
            parse_mode=ParseMode.MARKDOWN_V2
        )

        context.user_data.pop('state', None)
        await send_main_menu_edit_from_message(message, context)

    except Exception as e:
        logger.error(f"Upload error: {e}", exc_info=True)
        await message.reply_text(f"⚠️ حدث خطأ أثناء رفع الملف: {e}")

async def send_main_menu_edit_from_message(message: Message, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = format_blockquote(
        "🌟 *مرحباً أيها المالك!*\n\n"
        "📦 هذا البوت لإدارة وتخزين ملفاتك بشكل احترافي.\n"
        "👇 اختر أحد الخيارات أدناه:"
    )

    keyboard = [
        [
            InlineKeyboardButton("📤 رفع ملف", callback_data="menu_upload", style="success"),
            InlineKeyboardButton("📂 عرض الملفات", callback_data="menu_list", style="success")
        ],
        [
            InlineKeyboardButton("🔍 بحث", callback_data="menu_search", style="danger"),
            InlineKeyboardButton("⭐ المثبتات", callback_data="menu_pinned", style="danger")
        ],
        [
            InlineKeyboardButton("📊 الإحصائيات", callback_data="menu_stats", style="primary"),
            InlineKeyboardButton("🗑️ سلة المحذوفات", callback_data="menu_trash", style="primary")
        ],
        [
            InlineKeyboardButton("⚙️ إعدادات", callback_data="menu_settings", style="success")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if OWNER_PHOTO:
        await message.reply_photo(
            photo=OWNER_PHOTO,
            caption=text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN_V2
        )
    else:
        await message.reply_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN_V2
        )

async def list_files(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, page: int = 1,
                     search_query: str = None, pinned_only: bool = False, trash: bool = False) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()

    conditions = []
    params = []
    if pinned_only:
        conditions.append("pinned = 1")
    if trash:
        conditions.append("deleted = 1")
    else:
        conditions.append("deleted = 0")
    if search_query:
        conditions.append("(name LIKE ? OR original_name LIKE ?)")
        params.extend([f"%{search_query}%", f"%{search_query}%"])

    where_clause = " AND ".join(conditions) if conditions else ""
    if where_clause:
        where_clause = "WHERE " + where_clause

    cursor.execute(f"SELECT COUNT(*) as total FROM files {where_clause}", params)
    total = cursor.fetchone()['total']

    offset = (page - 1) * ITEMS_PER_PAGE
    cursor.execute(f"""
        SELECT id, name, original_name, type, folder, pinned, views, upload_date
        FROM files
        {where_clause}
        ORDER BY id DESC
        LIMIT ? OFFSET ?
    """, params + [ITEMS_PER_PAGE, offset])
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        text = format_blockquote("📭 *لا توجد ملفات.*")
        keyboard = [[InlineKeyboardButton("🏠 الرئيسية", callback_data="menu_home", style="danger")]]
        await safe_edit(query, text, InlineKeyboardMarkup(keyboard))
        return

    keyboard = []
    for row in rows:
        number = format_file_number(row['id'])
        name = row['name']
        if len(name) > 20:
            name = name[:18] + "…"
        button_text = f"{number} - {name}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"file_{row['id']}")])

    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"list_page_{page-1}", style="danger"))
    if offset + ITEMS_PER_PAGE < total:
        nav_buttons.append(InlineKeyboardButton("➡️ التالي", callback_data=f"list_page_{page+1}", style="success"))

    nav_buttons.append(InlineKeyboardButton("🏠 الرئيسية", callback_data="menu_home", style="danger"))

    if not trash and not pinned_only and not search_query:
        keyboard.append(nav_buttons)
    else:
        back_data = "menu_list"
        if trash:
            back_data = "menu_trash"
        elif pinned_only:
            back_data = "menu_pinned"
        elif search_query:
            back_data = "menu_search"
        keyboard.append(nav_buttons + [InlineKeyboardButton("🔙 رجوع", callback_data=back_data, style="danger")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    if trash:
        title = "🗑️ *سلة المحذوفات*"
    elif pinned_only:
        title = "⭐ *الملفات المثبتة*"
    elif search_query:
        title = f"🔍 *نتائج البحث عن:* `{search_query}`"
    else:
        title = "📁 *قائمة الملفات*"

    text = format_blockquote(
        f"{title}\n"
        f"📄 الصفحة {page} من {((total - 1) // ITEMS_PER_PAGE) + 1} | إجمالي {total} ملف"
    )

    await safe_edit(query, text, reply_markup)

    context.user_data['list_context'] = {
        'page': page,
        'search': search_query,
        'pinned': pinned_only,
        'trash': trash,
        'total': total
    }

async def list_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if not query.from_user or not is_owner(query.from_user.id):
        await safe_edit(query, "🚫 هذا البوت خاص بالمالك فقط")
        return

    data = query.data
    if data.startswith("list_page_"):
        page = int(data.split("_")[2])
        ctx = context.user_data.get('list_context', {})
        search = ctx.get('search')
        pinned = ctx.get('pinned', False)
        trash = ctx.get('trash', False)
        await list_files(query, context, page=page, search_query=search, pinned_only=pinned, trash=trash)

async def file_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if not query.from_user or not is_owner(query.from_user.id):
        await safe_edit(query, "🚫 هذا البوت خاص بالمالك فقط")
        return

    data = query.data
    if not data.startswith("file_"):
        return
    file_id = int(data.split("_")[1])

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM files WHERE id = ?", (file_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        await safe_edit(query, "⚠️ الملف غير موجود.")
        return

    file_dict = dict(row)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE files SET views = views + 1 WHERE id = ?", (file_id,))
    conn.commit()
    conn.close()
    file_dict['views'] += 1

    info_text = format_file_info(file_dict)

    keyboard = [
        [
            InlineKeyboardButton("⬇️ تنزيل", callback_data=f"action_download_{file_id}", style="success"),
            InlineKeyboardButton("👁️ معاينة", callback_data=f"action_preview_{file_id}", style="success")
        ],
        [
            InlineKeyboardButton("✏️ إعادة تسمية", callback_data=f"action_rename_{file_id}", style="danger"),
            InlineKeyboardButton("🔄 استبدال", callback_data=f"action_replace_{file_id}", style="danger")
        ],
        [
            InlineKeyboardButton("📂 نقل", callback_data=f"action_move_{file_id}", style="primary"),
            InlineKeyboardButton("📝 تعديل الوصف", callback_data=f"action_desc_{file_id}", style="primary")
        ],
        [
            InlineKeyboardButton("🏷️ تعديل الوسوم", callback_data=f"action_tags_{file_id}", style="success"),
            InlineKeyboardButton("⭐ تثبيت", callback_data=f"action_pin_{file_id}", style="danger")
        ],
        [
            InlineKeyboardButton("🔗 رابط مشاركة", callback_data=f"action_share_{file_id}", style="success"),
            InlineKeyboardButton("📋 نسخ المعرف", callback_data=f"action_copy_{file_id}", style="success")
        ],
        [
            InlineKeyboardButton("📜 الإصدارات", callback_data=f"action_versions_{file_id}", style="danger"),
            InlineKeyboardButton("🗑️ حذف", callback_data=f"action_delete_{file_id}", style="danger")
        ],
        [
            InlineKeyboardButton("🔙 رجوع", callback_data=f"action_back_{file_id}", style="primary"),
            InlineKeyboardButton("🏠 الرئيسية", callback_data="menu_home", style="primary")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        if OWNER_PHOTO:
            await query.message.reply_photo(
                photo=OWNER_PHOTO,
                caption=info_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN_V2
            )
            try:
                await query.delete_message()
            except Exception:
                pass
        else:
            await safe_edit(query, info_text, reply_markup)
    except Exception as e:
        logger.error(f"Error in file_info sending: {e}")
        if OWNER_PHOTO:
            await query.message.reply_photo(
                photo=OWNER_PHOTO,
                caption=info_text,
                reply_markup=reply_markup,
                parse_mode=None
            )
        else:
            await query.message.reply_text(
                text=info_text,
                reply_markup=reply_markup,
                parse_mode=None
            )
        try:
            await query.delete_message()
        except Exception:
            pass

async def action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if not query.from_user or not is_owner(query.from_user.id):
        await safe_edit(query, "🚫 هذا البوت خاص بالمالك فقط")
        return

    data = query.data
    parts = data.split("_")
    action = parts[1]
    file_id = int(parts[2]) if len(parts) > 2 else None

    if action == "download":
        await download_file(query, context, file_id)
    elif action == "preview":
        await preview_file(query, context, file_id)
    elif action == "rename":
        await start_rename(query, context, file_id)
    elif action == "replace":
        await start_replace(query, context, file_id)
    elif action == "move":
        await start_move(query, context, file_id)
    elif action == "desc":
        await start_description(query, context, file_id)
    elif action == "tags":
        await start_tags(query, context, file_id)
    elif action == "pin":
        await toggle_pin(query, context, file_id)
    elif action == "share":
        await generate_share_link(query, context, file_id)
    elif action == "copy":
        await copy_file_id(query, context, file_id)
    elif action == "versions":
        await show_versions(query, context, file_id)
    elif action == "delete":
        await confirm_delete(query, context, file_id)
    elif action == "back":
        await back_to_list(query, context, file_id)

async def download_file(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, file_id: int) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT file_id, name FROM files WHERE id = ?", (file_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        await safe_edit(query, "⚠️ الملف غير موجود.")
        return

    try:
        await context.bot.send_document(
            chat_id=query.from_user.id,
            document=row['file_id'],
            filename=row['name'],
            caption=f"📥 تنزيل الملف: {row['name']}"
        )
        await safe_edit(query, "✅ تم إرسال الملف.")
    except Exception as e:
        await safe_edit(query, f"⚠️ خطأ في التنزيل: {e}")

async def preview_file(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, file_id: int) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT file_id, name, type FROM files WHERE id = ?", (file_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        await safe_edit(query, "⚠️ الملف غير موجود.")
        return

    try:
        if row['type'] in ["Images", "Videos", "Audio"]:
            if row['type'] == "Images":
                await context.bot.send_photo(chat_id=query.from_user.id, photo=row['file_id'])
            elif row['type'] == "Videos":
                await context.bot.send_video(chat_id=query.from_user.id, video=row['file_id'])
            elif row['type'] == "Audio":
                await context.bot.send_audio(chat_id=query.from_user.id, audio=row['file_id'])
            await safe_edit(query, "✅ تم إرسال المعاينة.")
        else:
            await safe_edit(query, "⚠️ هذا النوع لا يدعم المعاينة المباشرة.")
    except Exception as e:
        await safe_edit(query, f"⚠️ خطأ في المعاينة: {e}")

async def start_rename(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, file_id: int) -> None:
    text = format_blockquote("✏️ *إعادة تسمية الملف*\n\n📝 أرسل الاسم الجديد للملف (مع الامتداد).")
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data=f"action_back_{file_id}", style="primary")]]
    await safe_edit(query, text, InlineKeyboardMarkup(keyboard))
    context.user_data['rename_file_id'] = file_id
    context.user_data['state'] = WAITING_FOR_RENAME

async def handle_rename(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("handle_rename called")
    user = update.effective_user
    if not user or not is_owner(user.id):
        return
    if context.user_data.get('state') != WAITING_FOR_RENAME:
        return

    file_id = context.user_data.get('rename_file_id')
    if not file_id:
        await update.message.reply_text("⚠️ حدث خطأ: لم يتم تحديد ملف.")
        return

    new_name = update.message.text.strip()
    if not new_name:
        await update.message.reply_text("⚠️ الاسم لا يمكن أن يكون فارغاً.")
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE files SET name = ?, last_update = ? WHERE id = ?",
                   (new_name, datetime.now().isoformat(), file_id))
    conn.commit()
    conn.close()

    await update.message.reply_text(
        format_blockquote(f"✅ *تم تغيير الاسم بنجاح!*\n📛 الاسم الجديد: `{new_name}`"),
        parse_mode=ParseMode.MARKDOWN_V2
    )

    context.user_data.pop('rename_file_id', None)
    context.user_data.pop('state', None)
    await file_info_from_message(update.message, context, file_id)

async def start_replace(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, file_id: int) -> None:
    text = format_blockquote("🔄 *استبدال الملف*\n\n📎 أرسل الملف الجديد ليحل محل الملف الحالي.\n📂 سيتم حفظ نسخة من الملف القديم في الإصدارات.")
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data=f"action_back_{file_id}", style="primary")]]
    await safe_edit(query, text, InlineKeyboardMarkup(keyboard))
    context.user_data['replace_file_id'] = file_id
    context.user_data['state'] = WAITING_FOR_REPLACE

async def handle_replace(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("handle_replace called")
    user = update.effective_user
    if not user or not is_owner(user.id):
        return
    if context.user_data.get('state') != WAITING_FOR_REPLACE:
        return

    file_id = context.user_data.get('replace_file_id')
    if not file_id:
        await update.message.reply_text("⚠️ حدث خطأ: لم يتم تحديد ملف.")
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM files WHERE id = ?", (file_id,))
    old_row = cursor.fetchone()
    if not old_row:
        await update.message.reply_text("⚠️ الملف الأصلي غير موجود.")
        context.user_data.pop('replace_file_id', None)
        context.user_data.pop('state', None)
        return

    message = update.message
    file_obj = None
    file_name = None
    file_size = None
    if message.document:
        file_obj = message.document
        file_name = file_obj.file_name
        file_size = file_obj.file_size
    elif message.photo:
        photo = message.photo[-1]
        file_obj = photo
        file_name = f"photo_{photo.file_unique_id}.jpg"
        file_size = photo.file_size
    elif message.video:
        file_obj = message.video
        file_name = file_obj.file_name or f"video_{file_obj.file_unique_id}.mp4"
        file_size = file_obj.file_size
    elif message.audio:
        file_obj = message.audio
        file_name = file_obj.file_name or f"audio_{file_obj.file_unique_id}.mp3"
        file_size = file_obj.file_size
    elif message.voice:
        file_obj = message.voice
        file_name = f"voice_{file_obj.file_unique_id}.ogg"
        file_size = file_obj.file_size
    else:
        await update.message.reply_text("⚠️ نوع الملف غير مدعوم.")
        return

    if not file_obj:
        await update.message.reply_text("⚠️ لم أتمكن من استلام الملف.")
        return

    try:
        forwarded = await context.bot.forward_message(
            chat_id=STORAGE_CHANNEL_ID,
            from_chat_id=message.chat_id,
            message_id=message.message_id
        )

        if forwarded.document:
            new_tg_file_id = forwarded.document.file_id
            new_tg_unique = forwarded.document.file_unique_id
        elif forwarded.photo:
            new_tg_file_id = forwarded.photo[-1].file_id
            new_tg_unique = forwarded.photo[-1].file_unique_id
        elif forwarded.video:
            new_tg_file_id = forwarded.video.file_id
            new_tg_unique = forwarded.video.file_unique_id
        elif forwarded.audio:
            new_tg_file_id = forwarded.audio.file_id
            new_tg_unique = forwarded.audio.file_unique_id
        elif forwarded.voice:
            new_tg_file_id = forwarded.voice.file_id
            new_tg_unique = forwarded.voice.file_unique_id
        else:
            await update.message.reply_text("⚠️ تعذر استخراج معرف الملف الجديد.")
            return

        cursor.execute("SELECT MAX(version_number) FROM versions WHERE file_id = ?", (file_id,))
        max_ver = cursor.fetchone()[0]
        new_ver = (max_ver or 0) + 1

        cursor.execute("""
            INSERT INTO versions
            (file_id, version_number, file_id_tg, file_unique_id, name, size, upload_date, message_id, channel_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            file_id,
            new_ver,
            old_row['file_id'],
            old_row['file_unique_id'],
            old_row['name'],
            old_row['size'],
            old_row['upload_date'],
            old_row['message_id'],
            old_row['channel_id']
        ))

        now = datetime.now().isoformat()
        cursor.execute("""
            UPDATE files
            SET file_id = ?, file_unique_id = ?, name = ?, original_name = ?, size = ?, last_update = ?, message_id = ?, channel_id = ?
            WHERE id = ?
        """, (
            new_tg_file_id, new_tg_unique, file_name, file_name,
            file_size, now, forwarded.message_id, str(STORAGE_CHANNEL_ID),
            file_id
        ))

        conn.commit()
        conn.close()

        await update.message.reply_text(
            format_blockquote(f"✅ *تم استبدال الملف بنجاح!*\n📌 الرقم: {format_file_number(file_id)}\n📛 الاسم الجديد: `{file_name}`"),
            parse_mode=ParseMode.MARKDOWN_V2
        )

        context.user_data.pop('replace_file_id', None)
        context.user_data.pop('state', None)
        await file_info_from_message(update.message, context, file_id)

    except Exception as e:
        logger.error(f"Replace error: {e}", exc_info=True)
        await update.message.reply_text(f"⚠️ حدث خطأ أثناء الاستبدال: {e}")

async def start_move(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, file_id: int) -> None:
    keyboard = []
    for folder in FOLDERS:
        emoji = ""
        if folder == "Images":
            emoji = "🖼️ "
        elif folder == "Videos":
            emoji = "🎬 "
        elif folder == "Audio":
            emoji = "🎵 "
        elif folder == "Documents":
            emoji = "📄 "
        elif folder == "Archives":
            emoji = "🗂️ "
        elif folder == "APK":
            emoji = "📱 "
        elif folder == "Programs":
            emoji = "💻 "
        elif folder == "Code":
            emoji = "💾 "
        elif folder == "Fonts":
            emoji = "🔤 "
        else:
            emoji = "📁 "
        keyboard.append([InlineKeyboardButton(f"{emoji}{folder}", callback_data=f"move_folder_{folder}_{file_id}")])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data=f"action_back_{file_id}", style="primary")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await safe_edit(query, format_blockquote("📂 *اختر المجلد الجديد:*"), reply_markup)

async def move_folder_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if not query.from_user or not is_owner(query.from_user.id):
        await safe_edit(query, "🚫 هذا البوت خاص بالمالك فقط")
        return

    data = query.data
    parts = data.split("_")
    if len(parts) < 4:
        return
    folder = parts[2]
    file_id = int(parts[3])

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE files SET folder = ?, last_update = ? WHERE id = ?",
                   (folder, datetime.now().isoformat(), file_id))
    conn.commit()
    conn.close()

    await safe_edit(query, format_blockquote(f"✅ *تم نقل الملف إلى المجلد:* `{folder}`"))
    await file_info_from_message(query.message, context, file_id)

async def start_description(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, file_id: int) -> None:
    text = format_blockquote("📝 *تعديل الوصف*\n\n✏️ أرسل الوصف الجديد للملف (يمكن أن يكون متعدد الأسطر).")
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data=f"action_back_{file_id}", style="primary")]]
    await safe_edit(query, text, InlineKeyboardMarkup(keyboard))
    context.user_data['desc_file_id'] = file_id
    context.user_data['state'] = WAITING_FOR_DESCRIPTION

async def handle_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("handle_description called")
    user = update.effective_user
    if not user or not is_owner(user.id):
        return
    if context.user_data.get('state') != WAITING_FOR_DESCRIPTION:
        return

    file_id = context.user_data.get('desc_file_id')
    if not file_id:
        await update.message.reply_text("⚠️ حدث خطأ.")
        return

    desc = update.message.text.strip()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE files SET description = ?, last_update = ? WHERE id = ?",
                   (desc, datetime.now().isoformat(), file_id))
    conn.commit()
    conn.close()

    await update.message.reply_text(
        format_blockquote("✅ *تم تحديث الوصف بنجاح!*"),
        parse_mode=ParseMode.MARKDOWN_V2
    )

    context.user_data.pop('desc_file_id', None)
    context.user_data.pop('state', None)
    await file_info_from_message(update.message, context, file_id)

async def start_tags(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, file_id: int) -> None:
    text = format_blockquote("🏷️ *تعديل الوسوم*\n\n📝 أرسل الوسوم الجديدة مفصولة بفواصل (مثال: عمل, مهم, مشروع).")
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data=f"action_back_{file_id}", style="primary")]]
    await safe_edit(query, text, InlineKeyboardMarkup(keyboard))
    context.user_data['tags_file_id'] = file_id
    context.user_data['state'] = WAITING_FOR_TAGS

async def handle_tags(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("handle_tags called")
    user = update.effective_user
    if not user or not is_owner(user.id):
        return
    if context.user_data.get('state') != WAITING_FOR_TAGS:
        return

    file_id = context.user_data.get('tags_file_id')
    if not file_id:
        await update.message.reply_text("⚠️ حدث خطأ.")
        return

    tags = update.message.text.strip()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE files SET tags = ?, last_update = ? WHERE id = ?",
                   (tags, datetime.now().isoformat(), file_id))
    conn.commit()
    conn.close()

    await update.message.reply_text(
        format_blockquote("✅ *تم تحديث الوسوم بنجاح!*"),
        parse_mode=ParseMode.MARKDOWN_V2
    )

    context.user_data.pop('tags_file_id', None)
    context.user_data.pop('state', None)
    await file_info_from_message(update.message, context, file_id)

async def toggle_pin(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, file_id: int) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT pinned FROM files WHERE id = ?", (file_id,))
    row = cursor.fetchone()
    if not row:
        await safe_edit(query, "⚠️ الملف غير موجود.")
        conn.close()
        return
    current = row['pinned']
    new_val = 1 if current == 0 else 0
    cursor.execute("UPDATE files SET pinned = ? WHERE id = ?", (new_val, file_id))
    conn.commit()
    conn.close()

    status = "مثبت ✅" if new_val else "غير مثبت ❌"
    await safe_edit(query, format_blockquote(f"✅ *تم تغيير حالة التثبيت:* {status}"))
    await file_info_from_message(query.message, context, file_id)

async def generate_share_link(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, file_id: int) -> None:
    token = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    expiry = datetime.now() + timedelta(days=1)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO share_tokens (token, file_id, expiry) VALUES (?, ?, ?)",
                   (token, file_id, expiry.isoformat()))
    conn.commit()
    conn.close()

    username = context.bot.username
    if username:
        link = f"https://t.me/{username}?start=share_{token}"
        link_text = f"🔗 الرابط: `{link}`"
    else:
        link_text = "⚠️ البوت ليس لديه معرف (username)، لا يمكن إنشاء رابط. استخدم الأمر:\n/start share_" + token

    await safe_edit(query, format_blockquote(
        f"🔗 *رابط المشاركة المؤقت*\n\n"
        f"{link_text}\n"
        f"⏳ ينتهي الصلاحية: `{expiry.strftime('%Y-%m-%d %H:%M')}`"
    ))

async def start_with_share(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if not args:
        await start(update, context)
        return
    if args[0].startswith("share_"):
        token = args[0][6:]
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT file_id, expiry FROM share_tokens WHERE token = ?", (token,))
        row = cursor.fetchone()
        if not row:
            await update.message.reply_text("⚠️ رابط غير صالح أو منتهي الصلاحية.")
            conn.close()
            return
        expiry = datetime.fromisoformat(row['expiry'])
        if datetime.now() > expiry:
            await update.message.reply_text("⚠️ انتهت صلاحية الرابط.")
            conn.close()
            return
        file_id = row['file_id']
        cursor.execute("SELECT file_id, name FROM files WHERE id = ?", (file_id,))
        file_row = cursor.fetchone()
        conn.close()
        if not file_row:
            await update.message.reply_text("⚠️ الملف غير موجود.")
            return
        try:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=file_row['file_id'],
                filename=file_row['name'],
                caption=f"📄 تم المشاركة: {file_row['name']}"
            )
        except Exception as e:
            await update.message.reply_text(f"⚠️ خطأ في إرسال الملف: {e}")

async def copy_file_id(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, file_id: int) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT file_id, file_unique_id FROM files WHERE id = ?", (file_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        await safe_edit(query, "⚠️ الملف غير موجود.")
        return

    await safe_edit(query, format_blockquote(
        f"📋 *معرف الملف*\n\n"
        f"`{row['file_id']}`\n\n"
        f"🆔 المعرف الفريد: `{row['file_unique_id']}`"
    ))

async def show_versions(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, file_id: int) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, version_number, name, size, upload_date, file_id_tg
        FROM versions
        WHERE file_id = ?
        ORDER BY version_number DESC
    """, (file_id,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await safe_edit(query, format_blockquote("📜 *لا توجد إصدارات سابقة لهذا الملف.*"))
        return

    text_lines = ["📜 *الإصدارات السابقة:*\n"]
    for row in rows:
        version_num = row['version_number']
        name = row['name']
        size = format_file_size(row['size'])
        date = datetime.fromisoformat(row['upload_date']).strftime('%Y-%m-%d %H:%M')
        text_lines.append(f"📌 الإصدار {version_num} - `{name}` - {size} - {date}")
    text = format_blockquote("\n".join(text_lines))

    keyboard = []
    for row in rows:
        v_id = row['id']
        keyboard.append([
            InlineKeyboardButton(f"⬇️ تحميل الإصدار {row['version_number']}", callback_data=f"version_download_{v_id}"),
            InlineKeyboardButton(f"🔄 استعادة {row['version_number']}", callback_data=f"version_restore_{v_id}")
        ])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data=f"action_back_{file_id}", style="primary")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await safe_edit(query, text, reply_markup)

async def version_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if not query.from_user or not is_owner(query.from_user.id):
        await safe_edit(query, "🚫 هذا البوت خاص بالمالك فقط")
        return

    data = query.data
    parts = data.split("_")
    action = parts[1]
    version_id = int(parts[2])

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM versions WHERE id = ?", (version_id,))
    version_row = cursor.fetchone()
    if not version_row:
        await safe_edit(query, "⚠️ الإصدار غير موجود.")
        conn.close()
        return
    file_id = version_row['file_id']

    if action == "download":
        try:
            await context.bot.send_document(
                chat_id=query.from_user.id,
                document=version_row['file_id_tg'],
                filename=version_row['name'],
                caption=f"📥 تنزيل الإصدار {version_row['version_number']}"
            )
            await safe_edit(query, "✅ تم إرسال الإصدار.")
        except Exception as e:
            await safe_edit(query, f"⚠️ خطأ: {e}")
    elif action == "restore":
        cursor.execute("SELECT * FROM files WHERE id = ?", (file_id,))
        current_row = cursor.fetchone()
        if not current_row:
            await safe_edit(query, "⚠️ الملف الحالي غير موجود.")
            conn.close()
            return

        cursor.execute("SELECT MAX(version_number) FROM versions WHERE file_id = ?", (file_id,))
        max_version = cursor.fetchone()[0] or 0
        new_version = max_version + 1

        cursor.execute("""
            INSERT INTO versions
            (file_id, version_number, file_id_tg, file_unique_id, name, size, upload_date, message_id, channel_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            file_id, new_version,
            current_row['file_id'], current_row['file_unique_id'],
            current_row['name'], current_row['size'],
            current_row['upload_date'], current_row['message_id'],
            current_row['channel_id']
        ))

        now = datetime.now().isoformat()
        cursor.execute("""
            UPDATE files
            SET file_id = ?, file_unique_id = ?, name = ?, size = ?, last_update = ?, message_id = ?, channel_id = ?
            WHERE id = ?
        """, (
            version_row['file_id_tg'], version_row['file_unique_id'],
            version_row['name'], version_row['size'], now,
            version_row['message_id'], version_row['channel_id'],
            file_id
        ))

        conn.commit()
        conn.close()

        await safe_edit(query, format_blockquote(f"✅ *تم استعادة الإصدار {version_row['version_number']} بنجاح!*"))
        await file_info_from_message(query.message, context, file_id)

async def confirm_delete(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, file_id: int) -> None:
    keyboard = [
        [
            InlineKeyboardButton("✅ نعم، احذف", callback_data=f"confirm_delete_yes_{file_id}", style="primary"),
            InlineKeyboardButton("❌ إلغاء", callback_data=f"confirm_delete_no_{file_id}", style="primary")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await safe_edit(query, format_blockquote("⚠️ *هل أنت متأكد من حذف هذا الملف؟*\n🗑️ سيتم نقله إلى سلة المحذوفات."), reply_markup)

async def confirm_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if not query.from_user or not is_owner(query.from_user.id):
        await safe_edit(query, "🚫 هذا البوت خاص بالمالك فقط")
        return

    data = query.data
    parts = data.split("_")
    if len(parts) < 4:
        return
    action = parts[2]
    file_id = int(parts[3])

    if action == "no":
        await safe_edit(query, "❌ تم إلغاء الحذف.")
        await file_info_from_message(query.message, context, file_id)
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE files SET deleted = 1, deleted_at = ? WHERE id = ?",
                   (datetime.now().isoformat(), file_id))
    conn.commit()
    conn.close()

    await safe_edit(query, format_blockquote("🗑️ *تم نقل الملف إلى سلة المحذوفات.*"))
    await list_trash(query, context)

async def list_trash(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE) -> None:
    await list_files(query, context, page=1, trash=True)

async def restore_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if not query.from_user or not is_owner(query.from_user.id):
        await safe_edit(query, "🚫 هذا البوت خاص بالمالك فقط")
        return

    data = query.data
    if not data.startswith("restore_file_"):
        return
    file_id = int(data.split("_")[2])

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE files SET deleted = 0, deleted_at = NULL WHERE id = ?", (file_id,))
    conn.commit()
    conn.close()

    await safe_edit(query, format_blockquote("✅ *تم استعادة الملف من سلة المحذوفات.*"))
    await list_trash(query, context)

async def permanent_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if not query.from_user or not is_owner(query.from_user.id):
        await safe_edit(query, "🚫 هذا البوت خاص بالمالك فقط")
        return

    data = query.data
    if not data.startswith("permanent_delete_"):
        return
    file_id = int(data.split("_")[2])

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM versions WHERE file_id = ?", (file_id,))
    cursor.execute("DELETE FROM share_tokens WHERE file_id = ?", (file_id,))
    cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
    conn.commit()
    conn.close()

    await safe_edit(query, format_blockquote("🗑️ *تم حذف الملف نهائياً.*"))
    await list_trash(query, context)

async def list_pinned(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE) -> None:
    await list_files(query, context, page=1, pinned_only=True)

async def start_search(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = format_blockquote("🔍 *بحث*\n\n📝 أرسل الكلمة أو جزء من اسم الملف للبحث.")
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="menu_home", style="primary")]]
    await safe_edit(query, text, InlineKeyboardMarkup(keyboard))
    context.user_data['state'] = WAITING_FOR_SEARCH

async def handle_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("handle_search called")
    user = update.effective_user
    if not user or not is_owner(user.id):
        return
    if context.user_data.get('state') != WAITING_FOR_SEARCH:
        return

    query_text = update.message.text.strip()
    if not query_text:
        await update.message.reply_text("⚠️ الرجاء إدخال نص للبحث.")
        return

    await send_search_results(update.message, context, query_text, page=1)
    context.user_data.pop('state', None)

async def send_search_results(message: Message, context: ContextTypes.DEFAULT_TYPE, query: str, page: int) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) as total FROM files
        WHERE deleted = 0 AND (name LIKE ? OR original_name LIKE ?)
    """, (f"%{query}%", f"%{query}%"))
    total = cursor.fetchone()['total']

    if total == 0:
        await message.reply_text(
            format_blockquote(f"🔍 *لا توجد نتائج للبحث عن:* `{query}`"),
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return

    offset = (page - 1) * ITEMS_PER_PAGE
    cursor.execute("""
        SELECT id, name, original_name, type, folder, pinned, views, upload_date
        FROM files
        WHERE deleted = 0 AND (name LIKE ? OR original_name LIKE ?)
        ORDER BY id DESC
        LIMIT ? OFFSET ?
    """, (f"%{query}%", f"%{query}%", ITEMS_PER_PAGE, offset))
    rows = cursor.fetchall()
    conn.close()

    keyboard = []
    for row in rows:
        number = format_file_number(row['id'])
        name = row['name']
        if len(name) > 20:
            name = name[:18] + "…"
        button_text = f"{number} - {name}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"file_{row['id']}")])

    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"search_page_{page-1}_{query}", style="primary"))
    if offset + ITEMS_PER_PAGE < total:
        nav_buttons.append(InlineKeyboardButton("➡️ التالي", callback_data=f"search_page_{page+1}_{query}", style="primary"))
    nav_buttons.append(InlineKeyboardButton("🏠 الرئيسية", callback_data="menu_home", style="primary"))
    keyboard.append(nav_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard)

    text = format_blockquote(
        f"🔍 *نتائج البحث عن:* `{query}`\n"
        f"📄 الصفحة {page} من {((total - 1) // ITEMS_PER_PAGE) + 1} | إجمالي {total} نتيجة"
    )

    await message.reply_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN_V2
    )

async def search_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if not query.from_user or not is_owner(query.from_user.id):
        await safe_edit(query, "🚫 هذا البوت خاص بالمالك فقط")
        return

    data = query.data
    parts = data.split("_", 3)
    if len(parts) < 4:
        return
    page = int(parts[2])
    search_query = parts[3]

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) as total FROM files
        WHERE deleted = 0 AND (name LIKE ? OR original_name LIKE ?)
    """, (f"%{search_query}%", f"%{search_query}%"))
    total = cursor.fetchone()['total']

    offset = (page - 1) * ITEMS_PER_PAGE
    cursor.execute("""
        SELECT id, name, original_name, type, folder, pinned, views, upload_date
        FROM files
        WHERE deleted = 0 AND (name LIKE ? OR original_name LIKE ?)
        ORDER BY id DESC
        LIMIT ? OFFSET ?
    """, (f"%{search_query}%", f"%{search_query}%", ITEMS_PER_PAGE, offset))
    rows = cursor.fetchall()
    conn.close()

    keyboard = []
    for row in rows:
        number = format_file_number(row['id'])
        name = row['name']
        if len(name) > 20:
            name = name[:18] + "…"
        button_text = f"{number} - {name}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"file_{row['id']}")])

    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"search_page_{page-1}_{search_query}", style="primary"))
    if offset + ITEMS_PER_PAGE < total:
        nav_buttons.append(InlineKeyboardButton("➡️ التالي", callback_data=f"search_page_{page+1}_{search_query}", style="primary"))
    nav_buttons.append(InlineKeyboardButton("🏠 الرئيسية", callback_data="menu_home", style="primary"))
    keyboard.append(nav_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard)

    text = format_blockquote(
        f"🔍 *نتائج البحث عن:* `{search_query}`\n"
        f"📄 الصفحة {page} من {((total - 1) // ITEMS_PER_PAGE) + 1} | إجمالي {total} نتيجة"
    )

    await safe_edit(query, text, reply_markup)

async def back_to_list(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, file_id: int) -> None:
    ctx = context.user_data.get('list_context', {})
    if ctx:
        page = ctx.get('page', 1)
        search = ctx.get('search')
        pinned = ctx.get('pinned', False)
        trash = ctx.get('trash', False)
        await list_files(query, context, page=page, search_query=search, pinned_only=pinned, trash=trash)
    else:
        await list_files(query, context, page=1)

async def file_info_from_message(message: Message, context: ContextTypes.DEFAULT_TYPE, file_id: int) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM files WHERE id = ?", (file_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        await message.reply_text("⚠️ الملف غير موجود.")
        return

    file_dict = dict(row)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE files SET views = views + 1 WHERE id = ?", (file_id,))
    conn.commit()
    conn.close()
    file_dict['views'] += 1

    info_text = format_file_info(file_dict)

    keyboard = [
        [
            InlineKeyboardButton("⬇️ تنزيل", callback_data=f"action_download_{file_id}", style="primary"),
            InlineKeyboardButton("👁️ معاينة", callback_data=f"action_preview_{file_id}", style="primary")
        ],
        [
            InlineKeyboardButton("✏️ إعادة تسمية", callback_data=f"action_rename_{file_id}", style="primary"),
            InlineKeyboardButton("🔄 استبدال", callback_data=f"action_replace_{file_id}", style="primary")
        ],
        [
            InlineKeyboardButton("📂 نقل", callback_data=f"action_move_{file_id}", style="primary"),
            InlineKeyboardButton("📝 تعديل الوصف", callback_data=f"action_desc_{file_id}", style="primary")
        ],
        [
            InlineKeyboardButton("🏷️ تعديل الوسوم", callback_data=f"action_tags_{file_id}", style="primary"),
            InlineKeyboardButton("⭐ تثبيت", callback_data=f"action_pin_{file_id}", style="primary")
        ],
        [
            InlineKeyboardButton("🔗 رابط مشاركة", callback_data=f"action_share_{file_id}", style="primary"),
            InlineKeyboardButton("📋 نسخ المعرف", callback_data=f"action_copy_{file_id}", style="primary")
        ],
        [
            InlineKeyboardButton("📜 الإصدارات", callback_data=f"action_versions_{file_id}", style="primary"),
            InlineKeyboardButton("🗑️ حذف", callback_data=f"action_delete_{file_id}", style="primary")
        ],
        [
            InlineKeyboardButton("🔙 رجوع", callback_data=f"action_back_{file_id}", style="primary"),
            InlineKeyboardButton("🏠 الرئيسية", callback_data="menu_home", style="primary")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        if OWNER_PHOTO:
            await message.reply_photo(
                photo=OWNER_PHOTO,
                caption=info_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN_V2
            )
        else:
            await message.reply_text(
                text=info_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN_V2
            )
    except Exception as e:
        logger.error(f"Error in file_info_from_message: {e}")
        if OWNER_PHOTO:
            await message.reply_photo(
                photo=OWNER_PHOTO,
                caption=info_text,
                reply_markup=reply_markup,
                parse_mode=None
            )
        else:
            await message.reply_text(
                text=info_text,
                reply_markup=reply_markup,
                parse_mode=None
            )

async def show_stats(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM files WHERE deleted = 0")
    total_files = cursor.fetchone()[0]

    cursor.execute("SELECT folder, COUNT(*) FROM files WHERE deleted = 0 GROUP BY folder")
    folder_counts = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM files WHERE deleted = 0 AND pinned = 1")
    pinned_count = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(size) FROM files WHERE deleted = 0")
    total_size = cursor.fetchone()[0] or 0

    cursor.execute("SELECT name, size FROM files WHERE deleted = 0 ORDER BY size DESC LIMIT 1")
    largest = cursor.fetchone()

    cursor.execute("SELECT name, views FROM files WHERE deleted = 0 ORDER BY views DESC LIMIT 1")
    most_viewed = cursor.fetchone()

    cursor.execute("SELECT name, upload_date FROM files WHERE deleted = 0 ORDER BY upload_date DESC LIMIT 1")
    latest = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) FROM files WHERE deleted = 1")
    trash_count = cursor.fetchone()[0]

    conn.close()

    lines = [
        "📊 *الإحصائيات*",
        f"📁 *إجمالي الملفات:* {total_files}",
        f"⭐ *المثبتات:* {pinned_count}",
        f"🗑️ *سلة المحذوفات:* {trash_count}",
        f"💾 *المساحة المستخدمة:* {format_file_size(total_size)}",
    ]

    if largest:
        lines.append(f"📦 *أكبر ملف:* `{largest['name']}` ({format_file_size(largest['size'])})")
    if most_viewed:
        lines.append(f"👁️ *الأكثر مشاهدة:* `{most_viewed['name']}` ({most_viewed['views']} مشاهدة)")
    if latest:
        date = datetime.fromisoformat(latest['upload_date']).strftime('%Y-%m-%d %H:%M')
        lines.append(f"🆕 *أحدث ملف:* `{latest['name']}` ({date})")

    lines.append("\n📂 *التوزيع حسب المجلدات:*")
    for folder, count in folder_counts:
        lines.append(f"- {folder}: {count} ملف")

    text = format_blockquote("\n".join(lines))
    keyboard = [[InlineKeyboardButton("🏠 الرئيسية", callback_data="menu_home", style="primary")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await safe_edit(query, text, reply_markup)

async def show_settings(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = format_blockquote(
        "⚙️ *الإعدادات*\n\n"
        "🔧 هنا يمكنك ضبط بعض الخيارات.\n"
        "📌 حالياً لا توجد إعدادات قابلة للتغيير."
    )
    keyboard = [[InlineKeyboardButton("🏠 الرئيسية", callback_data="menu_home", style="primary")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await safe_edit(query, text, reply_markup)

async def handle_direct_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user or not is_owner(user.id):
        return

    if context.user_data.get('state') is not None:
        return

    text = update.message.text.strip()
    if not text:
        return

    match = re.search(r'#?(\d+)', text)
    if match:
        file_num = int(match.group(1))
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM files WHERE id = ? AND deleted = 0", (file_num,))
        row = cursor.fetchone()
        conn.close()
        if row:
            await file_info_from_message(update.message, context, file_num)
            return

    await send_search_results(update.message, context, text, page=1)

def main() -> None:
    init_database()

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("start", start_with_share))

    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(menu_callback, pattern="^menu_"),
            CallbackQueryHandler(action_callback, pattern="^action_"),
            CallbackQueryHandler(move_folder_callback, pattern="^move_folder_"),
            CallbackQueryHandler(confirm_delete_callback, pattern="^confirm_delete_"),
            CallbackQueryHandler(restore_file, pattern="^restore_file_"),
            CallbackQueryHandler(permanent_delete, pattern="^permanent_delete_"),
            CallbackQueryHandler(version_action, pattern="^version_"),
            CallbackQueryHandler(list_page_callback, pattern="^list_page_"),
            CallbackQueryHandler(search_page_callback, pattern="^search_page_"),
            CallbackQueryHandler(file_info, pattern="^file_"),
        ],
        states={
            WAITING_FOR_RENAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_rename)
            ],
            WAITING_FOR_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_description)
            ],
            WAITING_FOR_TAGS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_tags)
            ],
            WAITING_FOR_SEARCH: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search)
            ],
            WAITING_FOR_REPLACE: [
                MessageHandler(filters.ALL, handle_replace)
            ],
        },
        fallbacks=[
            CommandHandler("start", start),
            CallbackQueryHandler(menu_callback, pattern="^menu_home$"),
        ],
        allow_reentry=True
    )

    application.add_handler(conv_handler)

    async def file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        if not user or not is_owner(user.id):
            return
        message = update.message
        if not (message.document or message.photo or message.video or message.audio or message.voice or message.video_note):
            return
        state = context.user_data.get('state')
        if state == WAITING_FOR_UPLOAD:
            await handle_upload(update, context)
        elif state == WAITING_FOR_REPLACE:
            await handle_replace(update, context)
        else:
            await message.reply_text("⚠️ استخدم الأزرار للتفاعل مع البوت.")

    application.add_handler(MessageHandler(filters.ALL, file_handler))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_direct_input))

    logger.info("Bot started polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()