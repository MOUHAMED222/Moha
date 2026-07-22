#MOHA | DEV
import asyncio
import os
import sys
import json
import sqlite3
import time
import random
import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from contextlib import asynccontextmanager

import aiosqlite
from telethon import TelegramClient, events, Button, functions, types
from telethon.sessions import StringSession
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    PhoneCodeExpiredError,
    FloodWaitError,
    RPCError,
)
from telethon.tl.types import (
    MessageEntityBold,
    MessageEntityItalic,
    MessageEntityCode,
    MessageEntityPre,
    MessageEntityTextUrl,
)

# ========== CONFIGURATION ==========
# These can be changed by the admin via the bot, but we set defaults here.
# For production, use environment variables or a config file.
BOT_TOKEN = "8776142375:AAFVWd1bDnTxTbD76EHM42My2hdbibGgxZc"  # Must be set
API_ID = 34819591  # Must be set
API_HASH = "4b9f4d8277c53505fb95bebfc93302e5"    # Must be set

# Default values (will be stored in DB and can be changed)
DEFAULT_WELCOME_PHOTO = "https://iili.io/fdqe0g4.md.jpg"
DEFAULT_WELCOME_MESSAGE = """
<b>مرحبًا بك في بوت النشر التلقائي الاحترافي!</b>

يمكنك من خلال هذا البوت:
• نشر تلقائي في القنوات والمجموعات
• إدارة حساباتك بسهولة
• استخدام الذكاء الاصطناعي
• وغيرها من الميزات الرائعة

<i>المطور: @U_1z4</i>
<i>قناة السورس: @SeroBots</i>
"""

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# ========== DATABASE ==========
DB_PATH = "bot_data.db"

async def init_db():
    """Initialize database tables if they don't exist."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Users table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                session_string TEXT,
                phone TEXT,
                is_admin INTEGER DEFAULT 0,
                is_vip INTEGER DEFAULT 0,
                is_banned INTEGER DEFAULT 0,
                is_paid INTEGER DEFAULT 0,
                settings TEXT,  -- JSON
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Targets (groups/channels)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS targets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                target_id INTEGER,
                title TEXT,
                username TEXT,
                type TEXT CHECK(type IN ('group','channel')),
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        # Posts (saved messages for publishing)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                message_text TEXT,
                media_type TEXT,
                media_file_id TEXT,
                caption TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        # Auto-replies
        await db.execute("""
            CREATE TABLE IF NOT EXISTS auto_replies (
                user_id INTEGER PRIMARY KEY,
                messages TEXT,  -- JSON list
                sleep_time INTEGER DEFAULT 30,
                active INTEGER DEFAULT 0,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        # Group creation settings
        await db.execute("""
            CREATE TABLE IF NOT EXISTS group_creation (
                user_id INTEGER PRIMARY KEY,
                auto_create INTEGER DEFAULT 0,
                messages TEXT,  -- JSON list
                delay INTEGER DEFAULT 60,
                created_groups TEXT,  -- JSON list
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        # Global settings (admin config)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS global_settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        # Custom buttons (per user? We'll keep global for admin to add to all)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS custom_buttons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT UNIQUE,
                action TEXT
            )
        """)
        # Broadcast log
        await db.execute("""
            CREATE TABLE IF NOT EXISTS broadcast_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER,
                message TEXT,
                recipients INTEGER,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # User publish settings (which targets, active, delay, etc.)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS publish_settings (
                user_id INTEGER PRIMARY KEY,
                active INTEGER DEFAULT 0,
                target_type TEXT DEFAULT 'both',  -- 'groups', 'channels', 'both'
                delay INTEGER DEFAULT 30,
                last_post_time TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        await db.commit()

        # Insert default global settings if not present
        defaults = {
            "api_id": str(API_ID),
            "api_hash": API_HASH,
            "welcome_photo": DEFAULT_WELCOME_PHOTO,
            "welcome_message": DEFAULT_WELCOME_MESSAGE,
            "bot_token": BOT_TOKEN,
        }
        for key, value in defaults.items():
            await db.execute(
                "INSERT OR IGNORE INTO global_settings (key, value) VALUES (?, ?)",
                (key, value)
            )
        await db.commit()

async def get_global_setting(key: str) -> Optional[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT value FROM global_settings WHERE key = ?", (key,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def set_global_setting(key: str, value: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO global_settings (key, value) VALUES (?, ?)",
            (key, value)
        )
        await db.commit()

# ========== HELPER FUNCTIONS ==========
def parse_html(text: str) -> str:
    """Convert plain text with HTML-like tags to Telethon HTML formatting."""
    # Telethon supports HTML parsing directly, we'll just return text.
    # We'll use parse_mode='html' when sending.
    return text

def format_message_with_quote(text: str) -> str:
    """Wrap text in blockquote for better appearance."""
    return f"<blockquote>{text}</blockquote>"

def build_main_menu(user_id: int) -> List[List[Button]]:
    """Build the main inline keyboard for the user."""
    buttons = []
    # Row 1: two buttons
    buttons.append([
        Button.inline("📤 بدء النشر", data="start_publish"),
        Button.inline("⏹ ايقاف النشر", data="stop_publish"),
    ])
    # Row 2
    buttons.append([
        Button.inline("📋 مجموعاتي", data="list_groups"),
        Button.inline("📋 قنواتي", data="list_channels"),
    ])
    # Row 3
    buttons.append([
        Button.inline("➕ اضافة مجموعة", data="add_group"),
        Button.inline("➕ اضافة قناة", data="add_channel"),
    ])
    # Row 4
    buttons.append([
        Button.inline("✏️ تعيين رسالة النشر", data="set_post_message"),
        Button.inline("⏱ تعيين وقت التأخير", data="set_delay"),
    ])
    # Row 5
    buttons.append([
        Button.inline("🤖 الذكاء الاصطناعي", data="ai_chat"),
        Button.inline("🔄 الرد التلقائي", data="auto_reply_menu"),
    ])
    # Row 6
    buttons.append([
        Button.inline("🕒 الساعة", data="toggle_clock"),
        Button.inline("📊 الاحصائيات", data="my_stats"),
    ])
    # Row 7
    buttons.append([
        Button.inline("ℹ️ معلومات البوت", data="bot_info"),
        Button.inline("📢 قناة السورس", data="source_channel"),
    ])
    # Row 8
    buttons.append([
        Button.inline("🚪 تسجيل خروج", data="logout"),
    ])
    # If admin, add admin panel button
    if user_id in admin_cache or is_user_admin(user_id):
        buttons.append([Button.inline("👑 لوحة الادمن", data="admin_panel")])
    return buttons

def build_admin_menu() -> List[List[Button]]:
    """Build the admin panel keyboard."""
    buttons = [
        [Button.inline("👥 ادارة المستخدمين", data="admin_users")],
        [Button.inline("📁 ادارة الجلسات", data="admin_sessions")],
        [Button.inline("🏷 ادارة VIP", data="admin_vip")],
        [Button.inline("🚫 حظر/فك حظر", data="admin_ban")],
        [Button.inline("🔧 الاعدادات العامة", data="admin_settings")],
        [Button.inline("📢 اذاعة للجميع", data="admin_broadcast")],
        [Button.inline("📊 الاحصائيات العامة", data="admin_stats")],
        [Button.inline("🖼 تغيير صورة الواجهة", data="admin_welcome_photo")],
        [Button.inline("📝 تغيير رسالة الترحيب", data="admin_welcome_message")],
        [Button.inline("🔘 ادارة الازرار المخصصة", data="admin_buttons")],
        [Button.inline("💾 نسخ احتياطي", data="admin_backup")],
        [Button.inline("📂 استعادة", data="admin_restore")],
        [Button.inline("🔙 رجوع", data="back_to_main")],
    ]
    return buttons

# Cache for admin users to avoid DB queries
admin_cache = set()

async def is_user_admin(user_id: int) -> bool:
    if user_id in admin_cache:
        return True
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row and row[0] == 1:
                admin_cache.add(user_id)
                return True
    return False

async def get_user_session(user_id: int) -> Optional[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT session_string FROM users WHERE id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def get_user_targets(user_id: int, target_type: str = None) -> List[Dict]:
    """Get targets for user. target_type: 'group', 'channel', None for both."""
    async with aiosqlite.connect(DB_PATH) as db:
        query = "SELECT target_id, title, username, type FROM targets WHERE user_id = ? AND is_active = 1"
        params = [user_id]
        if target_type:
            query += " AND type = ?"
            params.append(target_type)
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [{"id": r[0], "title": r[1], "username": r[2], "type": r[3]} for r in rows]

async def get_publish_settings(user_id: int) -> Dict:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT active, target_type, delay FROM publish_settings WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return {"active": bool(row[0]), "target_type": row[1], "delay": row[2]}
            else:
                # Default
                await db.execute(
                    "INSERT INTO publish_settings (user_id, active, target_type, delay) VALUES (?, 0, 'both', 30)",
                    (user_id,)
                )
                await db.commit()
                return {"active": False, "target_type": "both", "delay": 30}

async def update_publish_settings(user_id: int, **kwargs):
    async with aiosqlite.connect(DB_PATH) as db:
        for key, value in kwargs.items():
            await db.execute(
                f"UPDATE publish_settings SET {key} = ? WHERE user_id = ?",
                (value, user_id)
            )
        await db.commit()

# ========== USER CLIENT MANAGEMENT ==========
user_clients: Dict[int, TelegramClient] = {}
publish_tasks: Dict[int, asyncio.Task] = {}
clock_tasks: Dict[int, asyncio.Task] = {}

async def get_user_client(user_id: int) -> Optional[TelegramClient]:
    """Get or create a TelegramClient for the user."""
    if user_id in user_clients:
        return user_clients[user_id]
    session_string = await get_user_session(user_id)
    if not session_string:
        return None
    # Get API_ID and API_HASH from global settings
    api_id = int(await get_global_setting("api_id") or 0)
    api_hash = await get_global_setting("api_hash") or ""
    if not api_id or not api_hash:
        logger.error("API_ID or API_HASH not set globally")
        return None
    client = TelegramClient(StringSession(session_string), api_id, api_hash)
    await client.start()
    user_clients[user_id] = client
    return client

async def remove_user_client(user_id: int):
    if user_id in user_clients:
        await user_clients[user_id].disconnect()
        del user_clients[user_id]
    if user_id in publish_tasks:
        publish_tasks[user_id].cancel()
        del publish_tasks[user_id]
    if user_id in clock_tasks:
        clock_tasks[user_id].cancel()
        del clock_tasks[user_id]

# ========== PUBLISHING LOOP ==========
async def publish_loop(user_id: int):
    """Background task that publishes to targets according to settings."""
    logger.info(f"Publish loop started for user {user_id}")
    try:
        while True:
            settings = await get_publish_settings(user_id)
            if not settings["active"]:
                break
            client = await get_user_client(user_id)
            if not client:
                logger.error(f"No client for user {user_id}, stopping publish")
                break
            # Get post message
            post = await get_current_post(user_id)
            if not post:
                await asyncio.sleep(30)
                continue
            targets = await get_user_targets(user_id, settings["target_type"] if settings["target_type"] != "both" else None)
            if not targets:
                await asyncio.sleep(30)
                continue
            for target in targets:
                if not settings["active"]:
                    break
                try:
                    await send_message_to_target(client, target["id"], post)
                    await asyncio.sleep(settings["delay"])
                except FloodWaitError as e:
                    logger.warning(f"Flood wait {e.seconds} for user {user_id}")
                    await asyncio.sleep(e.seconds)
                except Exception as e:
                    logger.error(f"Error sending to target {target['id']}: {e}")
                    await asyncio.sleep(10)
            # After one round, wait a bit before next round
            await asyncio.sleep(5)
    except asyncio.CancelledError:
        logger.info(f"Publish loop cancelled for user {user_id}")
    except Exception as e:
        logger.error(f"Publish loop error for user {user_id}: {e}")
    finally:
        if user_id in publish_tasks:
            del publish_tasks[user_id]
        # Update status to inactive
        await update_publish_settings(user_id, active=0)

async def send_message_to_target(client: TelegramClient, target_id: int, post: Dict):
    """Send a post to target using the user client."""
    text = post.get("message_text", "")
    media_type = post.get("media_type")
    media_file_id = post.get("media_file_id")
    caption = post.get("caption", "")
    if media_type and media_file_id:
        # We have a media, send it
        if media_type == "photo":
            await client.send_file(target_id, file=media_file_id, caption=caption or text, parse_mode="html")
        elif media_type == "video":
            await client.send_file(target_id, file=media_file_id, caption=caption or text, parse_mode="html")
        elif media_type == "document":
            await client.send_file(target_id, file=media_file_id, caption=caption or text, parse_mode="html")
        elif media_type == "sticker":
            await client.send_file(target_id, file=media_file_id)
        else:
            await client.send_message(target_id, text or caption, parse_mode="html")
    else:
        await client.send_message(target_id, text, parse_mode="html")

async def get_current_post(user_id: int) -> Optional[Dict]:
    """Get the latest saved post for the user."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT message_text, media_type, media_file_id, caption FROM posts WHERE user_id = ? ORDER BY id DESC LIMIT 1",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "message_text": row[0],
                    "media_type": row[1],
                    "media_file_id": row[2],
                    "caption": row[3],
                }
    return None

# ========== CLOCK FEATURE ==========
async def clock_loop(user_id: int):
    """Update profile first name with current time."""
    logger.info(f"Clock loop started for user {user_id}")
    try:
        client = await get_user_client(user_id)
        if not client:
            return
        while True:
            current_time = datetime.now().strftime("%H:%M:%S")
            try:
                await client(functions.account.UpdateProfileRequest(first_name=current_time))
                await asyncio.sleep(10)
            except Exception as e:
                logger.error(f"Clock error for user {user_id}: {e}")
                await asyncio.sleep(30)
    except asyncio.CancelledError:
        logger.info(f"Clock loop cancelled for user {user_id}")
    except Exception as e:
        logger.error(f"Clock loop error: {e}")

# ========== BOT INSTANCE ==========
bot = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# ========== COMMAND HANDLERS ==========
@bot.on(events.NewMessage(pattern="/start"))
async def start_handler(event):
    user_id = event.sender_id
    # Check if user is banned
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT is_banned FROM users WHERE id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row and row[0] == 1:
                await event.reply("🚫 أنت محظور من استخدام البوت.")
                return
    # Check if user has session
    session = await get_user_session(user_id)
    if not session:
        # Show login prompt
        await event.reply(
            "🔐 **يرجى تسجيل الدخول بحسابك لتتمكن من استخدام البوت.**\n\n"
            "اضغط على الزر أدناه لبدء عملية تسجيل الدخول.",
            buttons=[[Button.inline("🔑 تسجيل الدخول", data="login")]],
            parse_mode="markdown"
        )
        return
    # User already logged in, show main menu
    await show_main_menu(event, user_id)

async def show_main_menu(event, user_id):
    welcome_photo = await get_global_setting("welcome_photo") or DEFAULT_WELCOME_PHOTO
    welcome_message = await get_global_setting("welcome_message") or DEFAULT_WELCOME_MESSAGE
    # Check if user is admin
    is_admin = await is_user_admin(user_id)
    try:
        await event.reply(
            file=welcome_photo if welcome_photo.startswith("http") else None,
            message=format_message_with_quote(welcome_message),
            buttons=build_main_menu(user_id),
            parse_mode="html"
        )
    except Exception as e:
        logger.error(f"Error showing main menu: {e}")
        await event.reply(
            welcome_message,
            buttons=build_main_menu(user_id),
            parse_mode="html"
        )

# ========== CALLBACK QUERY HANDLER ==========
@bot.on(events.CallbackQuery)
async def callback_handler(event):
    user_id = event.sender_id
    data = event.data.decode("utf-8")
    logger.info(f"Callback from {user_id}: {data}")

    # Handle login flow
    if data == "login":
        await event.edit("📱 **يرجى إرسال رقم هاتفك مع مفتاح الدولة.**\nمثال: +1234567890")
        # Set state for user
        waiting_for[user_id] = "phone"
        return

    # Check if user is logged in
    session = await get_user_session(user_id)
    if not session and data != "login":
        await event.answer("يرجى تسجيل الدخول أولاً.", alert=True)
        return

    # Handle various callbacks
    if data == "back_to_main":
        await show_main_menu(event, user_id)
    elif data == "start_publish":
        await start_publishing(user_id, event)
    elif data == "stop_publish":
        await stop_publishing(user_id, event)
    elif data == "list_groups":
        await list_targets(user_id, event, "group")
    elif data == "list_channels":
        await list_targets(user_id, event, "channel")
    elif data == "add_group":
        await event.edit("📝 أرسل معرف المجموعة (مثال: @mygroup) أو رابطها.")
        waiting_for[user_id] = "add_group"
    elif data == "add_channel":
        await event.edit("📝 أرسل معرف القناة (مثال: @mychannel) أو رابطها.")
        waiting_for[user_id] = "add_channel"
    elif data == "set_post_message":
        await event.edit("📝 أرسل نص الرسالة التي تريد نشرها.\nيمكنك إرسال صورة، فيديو، مستند، أو ملصق أيضاً.")
        waiting_for[user_id] = "set_post"
    elif data == "set_delay":
        await event.edit("⏱ أرسل وقت التأخير بين كل رسالة (بالثواني).")
        waiting_for[user_id] = "set_delay"
    elif data == "ai_chat":
        await event.edit("🤖 مرحباً! أرسل رسالتك وسأرد عليك باستخدام الذكاء الاصطناعي.\nلإلغاء، أرسل /cancel")
        waiting_for[user_id] = "ai_chat"
    elif data == "auto_reply_menu":
        await show_auto_reply_menu(event, user_id)
    elif data == "toggle_clock":
        await toggle_clock(user_id, event)
    elif data == "my_stats":
        await show_my_stats(user_id, event)
    elif data == "bot_info":
        await show_bot_info(event)
    elif data == "source_channel":
        await event.edit("📢 **قناة السورس:** @SeroBots\n\n👨‍💻 **المطور:** @U_1z4")
    elif data == "logout":
        await logout_user(user_id, event)
    elif data == "admin_panel":
        if await is_user_admin(user_id):
            await event.edit("👑 **لوحة الأدمن**", buttons=build_admin_menu())
        else:
            await event.answer("ليس لديك صلاحية.", alert=True)
    # Admin submenus
    elif data.startswith("admin_"):
        await handle_admin_callbacks(event, user_id, data)
    else:
        await event.answer("زر غير معروف.", alert=True)

# ========== WAITING FOR USER INPUT ==========
waiting_for: Dict[int, str] = {}

@bot.on(events.NewMessage)
async def message_handler(event):
    user_id = event.sender_id
    text = event.text
    if text.startswith("/"):
        return

    # Check if user is banned
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT is_banned FROM users WHERE id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row and row[0] == 1:
                await event.reply("🚫 أنت محظور.")
                return

    # Handle states
    state = waiting_for.get(user_id)
    if not state:
        # If not waiting for anything, ignore
        return

    if state == "phone":
        phone = text.strip()
        if not phone.startswith("+"):
            await event.reply("⚠️ يجب أن يبدأ الرقم بـ + متبوعاً بمفتاح الدولة.")
            return
        # Store phone temporarily
        temp_data[user_id] = {"phone": phone}
        # Start login process
        await event.reply("📱 جاري إرسال رمز التحقق...")
        try:
            client = await create_temp_client(user_id)
            if client:
                # Send code request
                result = await client.send_code_request(phone)
                temp_data[user_id]["phone_code_hash"] = result.phone_code_hash
                await event.reply("✅ تم إرسال رمز التحقق. أرسله الآن.")
                waiting_for[user_id] = "code"
            else:
                await event.reply("❌ فشل إنشاء العميل. تأكد من الإعدادات.")
                waiting_for.pop(user_id, None)
        except Exception as e:
            logger.error(f"Login error for {user_id}: {e}")
            await event.reply(f"❌ خطأ: {str(e)}")
            waiting_for.pop(user_id, None)

    elif state == "code":
        code = text.strip()
        phone_data = temp_data.get(user_id, {})
        phone = phone_data.get("phone")
        phone_code_hash = phone_data.get("phone_code_hash")
        if not phone or not phone_code_hash:
            await event.reply("⚠️ يرجى البدء من جديد (/start).")
            waiting_for.pop(user_id, None)
            return
        # Complete login
        client = await get_temp_client(user_id)
        if not client:
            await event.reply("❌ انتهت الجلسة، حاول مجدداً.")
            waiting_for.pop(user_id, None)
            return
        try:
            await client.sign_in(phone, code, phone_code_hash=phone_code_hash)
            # Success
            session_string = client.session.save()
            # Save user
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute(
                    "INSERT OR REPLACE INTO users (id, session_string, phone) VALUES (?, ?, ?)",
                    (user_id, session_string, phone)
                )
                await db.commit()
            # Store client in cache
            user_clients[user_id] = client
            await event.reply("✅ **تم تسجيل الدخول بنجاح!**", parse_mode="markdown")
            await show_main_menu(event, user_id)
            waiting_for.pop(user_id, None)
            temp_data.pop(user_id, None)
        except SessionPasswordNeededError:
            await event.reply("🔐 حسابك محمي بكلمة مرور خطوتين. أرسل كلمة المرور.")
            waiting_for[user_id] = "2fa"
        except PhoneCodeInvalidError:
            await event.reply("❌ رمز التحقق غير صحيح. حاول مجدداً.")
        except PhoneCodeExpiredError:
            await event.reply("❌ انتهت صلاحية الرمز. أعد المحاولة.")
            waiting_for.pop(user_id, None)
        except Exception as e:
            logger.error(f"Sign in error: {e}")
            await event.reply(f"❌ خطأ: {str(e)}")
            waiting_for.pop(user_id, None)

    elif state == "2fa":
        password = text.strip()
        client = await get_temp_client(user_id)
        if not client:
            await event.reply("❌ انتهت الجلسة، حاول مجدداً.")
            waiting_for.pop(user_id, None)
            return
        try:
            await client.sign_in(password=password)
            session_string = client.session.save()
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute(
                    "INSERT OR REPLACE INTO users (id, session_string, phone) VALUES (?, ?, ?)",
                    (user_id, session_string, temp_data.get(user_id, {}).get("phone"))
                )
                await db.commit()
            user_clients[user_id] = client
            await event.reply("✅ **تم تسجيل الدخول بنجاح!**", parse_mode="markdown")
            await show_main_menu(event, user_id)
            waiting_for.pop(user_id, None)
            temp_data.pop(user_id, None)
        except Exception as e:
            logger.error(f"2FA error: {e}")
            await event.reply(f"❌ خطأ: {str(e)}")
            waiting_for.pop(user_id, None)

    elif state == "add_group":
        await add_target(user_id, text, "group", event)
        waiting_for.pop(user_id, None)
    elif state == "add_channel":
        await add_target(user_id, text, "channel", event)
        waiting_for.pop(user_id, None)
    elif state == "set_post":
        await save_post(user_id, event.message, event)
        waiting_for.pop(user_id, None)
    elif state == "set_delay":
        try:
            delay = int(text)
            if delay < 5:
                await event.reply("⚠️ أقل تأخير هو 5 ثواني.")
                return
            await update_publish_settings(user_id, delay=delay)
            await event.reply(f"✅ تم تعيين التأخير إلى {delay} ثانية.")
        except:
            await event.reply("⚠️ يرجى إدخال رقم صحيح.")
        waiting_for.pop(user_id, None)
    elif state == "ai_chat":
        if text == "/cancel":
            waiting_for.pop(user_id, None)
            await event.reply("🚫 تم إلغاء جلسة الذكاء الاصطناعي.")
            return
        await event.reply("🤖 جاري التفكير...")
        response = await chat_with_ai(text)
        await event.reply(response)
    # Add other states for auto-reply, etc.
    else:
        # Handle other states
        pass

# ========== TEMP CLIENT FOR LOGIN ==========
temp_clients: Dict[int, TelegramClient] = {}
temp_data: Dict[int, Dict] = {}

async def create_temp_client(user_id: int) -> Optional[TelegramClient]:
    api_id = int(await get_global_setting("api_id") or 0)
    api_hash = await get_global_setting("api_hash") or ""
    if not api_id or not api_hash:
        return None
    client = TelegramClient(StringSession(), api_id, api_hash)
    await client.connect()
    temp_clients[user_id] = client
    return client

async def get_temp_client(user_id: int) -> Optional[TelegramClient]:
    return temp_clients.get(user_id)

# ========== TARGET MANAGEMENT ==========
async def add_target(user_id: int, identifier: str, target_type: str, event):
    """Add a group or channel to user's targets."""
    try:
        client = await get_user_client(user_id)
        if not client:
            await event.reply("❌ لم يتم العثور على الجلسة. قم بتسجيل الدخول مجدداً.")
            return
        # Parse identifier
        if identifier.startswith("https://t.me/"):
            parts = identifier.split("/")
            identifier = parts[-1] if parts else identifier
        # Get entity
        try:
            if identifier.startswith("@"):
                entity = await client.get_entity(identifier)
            else:
                # Try as username without @
                entity = await client.get_entity(identifier)
        except ValueError:
            # Try as integer ID
            try:
                entity = await client.get_entity(int(identifier))
            except:
                await event.reply("❌ لم يتم العثور على المجموعة/القناة. تأكد من المعرف.")
                return
        # Determine type from entity
        if hasattr(entity, "broadcast") and entity.broadcast:
            actual_type = "channel"
        elif hasattr(entity, "megagroup") and entity.megagroup:
            actual_type = "group"
        else:
            actual_type = "group"  # fallback
        if actual_type != target_type:
            await event.reply(f"⚠️ المعرف ليس {target_type}اً، بل هو {actual_type}.")
            return
        # Save to database
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO targets (user_id, target_id, title, username, type) VALUES (?, ?, ?, ?, ?)",
                (user_id, entity.id, getattr(entity, "title", "غير معروف"), getattr(entity, "username", ""), actual_type)
            )
            await db.commit()
        await event.reply(f"✅ تمت إضافة {actual_type}: {entity.title or identifier}")
    except Exception as e:
        logger.error(f"Add target error: {e}")
        await event.reply(f"❌ خطأ: {str(e)}")

async def list_targets(user_id: int, event, target_type: str):
    targets = await get_user_targets(user_id, target_type)
    if not targets:
        await event.edit(f"📭 لا توجد {target_type}ات مسجلة.")
        return
    text = f"📋 **{target_type.capitalize()}اتك:**\n\n"
    for t in targets:
        text += f"• {t['title']} ({t['username'] or 'لا يوجد'})\n"
    await event.edit(text, parse_mode="markdown")

# ========== POST MANAGEMENT ==========
async def save_post(user_id: int, message, event):
    """Save the message (text or media) as the post to publish."""
    text = message.text or ""
    media_type = None
    media_file_id = None
    caption = message.caption or ""
    if message.photo:
        media_type = "photo"
        media_file_id = message.photo.id
    elif message.video:
        media_type = "video"
        media_file_id = message.video.id
    elif message.document:
        media_type = "document"
        media_file_id = message.document.id
    elif message.sticker:
        media_type = "sticker"
        media_file_id = message.sticker.id
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO posts (user_id, message_text, media_type, media_file_id, caption) VALUES (?, ?, ?, ?, ?)",
            (user_id, text, media_type, media_file_id, caption)
        )
        await db.commit()
    await event.reply("✅ تم حفظ الرسالة. سيتم استخدامها في النشر التلقائي.")

# ========== PUBLISHING CONTROLS ==========
async def start_publishing(user_id: int, event):
    settings = await get_publish_settings(user_id)
    if settings["active"]:
        await event.answer("النشر مفعل بالفعل.", alert=True)
        return
    # Check if there is a post and targets
    post = await get_current_post(user_id)
    targets = await get_user_targets(user_id)
    if not post:
        await event.answer("⚠️ يرجى تعيين رسالة النشر أولاً.", alert=True)
        return
    if not targets:
        await event.answer("⚠️ يرجى إضافة مجموعة أو قناة أولاً.", alert=True)
        return
    # Start loop
    await update_publish_settings(user_id, active=1)
    task = asyncio.create_task(publish_loop(user_id))
    publish_tasks[user_id] = task
    await event.answer("✅ تم بدء النشر التلقائي.", alert=True)
    await event.edit("✅ تم بدء النشر التلقائي.", buttons=build_main_menu(user_id))

async def stop_publishing(user_id: int, event):
    await update_publish_settings(user_id, active=0)
    if user_id in publish_tasks:
        publish_tasks[user_id].cancel()
        del publish_tasks[user_id]
    await event.answer("⏹ تم إيقاف النشر.", alert=True)
    await event.edit("⏹ تم إيقاف النشر.", buttons=build_main_menu(user_id))

# ========== AUTO-REPLY ==========
async def show_auto_reply_menu(event, user_id):
    buttons = [
        [Button.inline("➕ إضافة كليشة", data="auto_add")],
        [Button.inline("🗑 حذف كليشة", data="auto_remove")],
        [Button.inline("📋 عرض الكلايش", data="auto_list")],
        [Button.inline("⏱ تعيين وقت النشر", data="auto_set_time")],
        [Button.inline("▶️ تفعيل", data="auto_enable")],
        [Button.inline("⏹ إيقاف", data="auto_disable")],
        [Button.inline("🔙 رجوع", data="back_to_main")],
    ]
    await event.edit("🔄 **الرد التلقائي**", buttons=buttons)

# ========== CLOCK ==========
async def toggle_clock(user_id: int, event):
    if user_id in clock_tasks and not clock_tasks[user_id].done():
        clock_tasks[user_id].cancel()
        del clock_tasks[user_id]
        await event.answer("⏹ تم إيقاف الساعة.", alert=True)
    else:
        task = asyncio.create_task(clock_loop(user_id))
        clock_tasks[user_id] = task
        await event.answer("✅ تم تفعيل الساعة.", alert=True)

# ========== STATS ==========
async def show_my_stats(user_id: int, event):
    targets = await get_user_targets(user_id)
    posts = 0
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM posts WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            posts = row[0] if row else 0
    text = f"""
📊 **إحصائياتك**
• عدد المجموعات/القنوات: {len(targets)}
• عدد الرسائل المحفوظة: {posts}
• حالة النشر: {'مفعل' if (await get_publish_settings(user_id))['active'] else 'غير مفعل'}
• وقت التأخير: {(await get_publish_settings(user_id))['delay']} ثانية
    """
    await event.edit(text, parse_mode="markdown")

async def show_bot_info(event):
    info = """
ℹ️ **معلومات البوت**

• الإصدار: 2.0
• المطور: @U_1z4
• قناة السورس: @SeroBots

مميزات البوت:
• النشر التلقائي في القنوات والمجموعات
• دعم الوسائط المتعددة
• الذكاء الاصطناعي
• الرد التلقائي
• ادارة الحسابات
• نظام VIP والأدمن
    """
    await event.edit(info, parse_mode="markdown")

# ========== LOGOUT ==========
async def logout_user(user_id: int, event):
    await remove_user_client(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM users WHERE id = ?", (user_id,))
        await db.commit()
    await event.edit("🚪 تم تسجيل الخروج بنجاح.", buttons=[[Button.inline("🔑 تسجيل الدخول", data="login")]])

# ========== ADMIN HANDLERS ==========
async def handle_admin_callbacks(event, user_id, data):
    if not await is_user_admin(user_id):
        await event.answer("ليس لديك صلاحية.", alert=True)
        return

    if data == "admin_users":
        await show_admin_users(event)
    elif data == "admin_sessions":
        await show_admin_sessions(event)
    elif data == "admin_vip":
        await show_admin_vip(event)
    elif data == "admin_ban":
        await show_admin_ban(event)
    elif data == "admin_settings":
        await show_admin_settings(event)
    elif data == "admin_broadcast":
        await event.edit("📢 أرسل رسالة الإذاعة (نص أو وسائط).")
        waiting_for[user_id] = "admin_broadcast"
    elif data == "admin_stats":
        await show_admin_stats(event)
    elif data == "admin_welcome_photo":
        await event.edit("🖼 أرسل صورة جديدة للواجهة.")
        waiting_for[user_id] = "admin_welcome_photo"
    elif data == "admin_welcome_message":
        await event.edit("📝 أرسل نص رسالة الترحيب الجديدة (يمكنك استخدام HTML).")
        waiting_for[user_id] = "admin_welcome_message"
    elif data == "admin_buttons":
        await show_admin_buttons(event)
    elif data == "admin_backup":
        await create_backup(event)
    elif data == "admin_restore":
        await event.edit("📂 أرسل ملف JSON للاستعادة.")
        waiting_for[user_id] = "admin_restore"

async def show_admin_users(event):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id, phone, is_admin, is_vip, is_banned FROM users") as cursor:
            rows = await cursor.fetchall()
            text = "👥 **المستخدمون:**\n\n"
            for row in rows:
                text += f"• ID: {row[0]}, Phone: {row[1]}, Admin: {row[2]}, VIP: {row[3]}, Banned: {row[4]}\n"
    await event.edit(text, parse_mode="markdown", buttons=[[Button.inline("🔙 رجوع", data="admin_panel")]])

async def show_admin_sessions(event):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id, phone FROM users") as cursor:
            rows = await cursor.fetchall()
            text = "📁 **الجلسات النشطة:**\n\n"
            for row in rows:
                text += f"• {row[0]} - {row[1]}\n"
    await event.edit(text, parse_mode="markdown", buttons=[
        [Button.inline("🗑 حذف جلسة", data="admin_delete_session")],
        [Button.inline("🔙 رجوع", data="admin_panel")],
    ])

async def show_admin_vip(event):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id, phone FROM users WHERE is_vip=1") as cursor:
            rows = await cursor.fetchall()
            text = "🏷 **مستخدمون VIP:**\n\n"
            for row in rows:
                text += f"• {row[0]} - {row[1]}\n"
            if not rows:
                text += "لا يوجد أعضاء VIP."
    await event.edit(text, parse_mode="markdown", buttons=[
        [Button.inline("➕ تفعيل VIP", data="admin_add_vip")],
        [Button.inline("❌ حذف VIP", data="admin_remove_vip")],
        [Button.inline("🔙 رجوع", data="admin_panel")],
    ])

async def show_admin_ban(event):
    await event.edit("🚫 **حظر/فك حظر**\n\nأرسل ID المستخدم مع الأمر:\n/ban <id>\n/unban <id>")

async def show_admin_settings(event):
    api_id = await get_global_setting("api_id") or "غير مضبوط"
    api_hash = await get_global_setting("api_hash") or "غير مضبوط"
    bot_token = await get_global_setting("bot_token") or "غير مضبوط"
    text = f"""
🔧 **الإعدادات العامة**
• API_ID: {api_id}
• API_HASH: {api_hash}
• BOT_TOKEN: {bot_token}
    """
    await event.edit(text, parse_mode="markdown", buttons=[
        [Button.inline("✏️ تغيير API_ID", data="admin_set_api_id")],
        [Button.inline("✏️ تغيير API_HASH", data="admin_set_api_hash")],
        [Button.inline("🔙 رجوع", data="admin_panel")],
    ])

async def show_admin_stats(event):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as c1:
            users_count = (await c1.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM users WHERE is_admin=1") as c2:
            admin_count = (await c2.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM users WHERE is_vip=1") as c3:
            vip_count = (await c3.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM users WHERE is_banned=1") as c4:
            banned_count = (await c4.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM targets") as c5:
            targets_count = (await c5.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM posts") as c6:
            posts_count = (await c6.fetchone())[0]
    text = f"""
📊 **الإحصائيات العامة**
• المستخدمون: {users_count}
• الأدمن: {admin_count}
• VIP: {vip_count}
• المحظورون: {banned_count}
• الوجهات: {targets_count}
• الرسائل المحفوظة: {posts_count}
    """
    await event.edit(text, parse_mode="markdown", buttons=[[Button.inline("🔙 رجوع", data="admin_panel")]])

async def show_admin_buttons(event):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id, label FROM custom_buttons") as cursor:
            rows = await cursor.fetchall()
            text = "🔘 **الأزرار المخصصة:**\n\n"
            for row in rows:
                text += f"• {row[1]} (ID: {row[0]})\n"
            if not rows:
                text += "لا توجد أزرار مخصصة."
    await event.edit(text, parse_mode="markdown", buttons=[
        [Button.inline("➕ إضافة زر", data="admin_add_button")],
        [Button.inline("🗑 حذف زر", data="admin_remove_button")],
        [Button.inline("🔙 رجوع", data="admin_panel")],
    ])

# ========== BACKUP ==========
async def create_backup(event):
    # Backup all tables to JSON
    backup_data = {}
    async with aiosqlite.connect(DB_PATH) as db:
        tables = ["users", "targets", "posts", "auto_replies", "group_creation", "global_settings", "custom_buttons", "publish_settings"]
        for table in tables:
            async with db.execute(f"SELECT * FROM {table}") as cursor:
                rows = await cursor.fetchall()
                # Get column names
                columns = [description[0] for description in cursor.description]
                backup_data[table] = [dict(zip(columns, row)) for row in rows]
    # Save to file
    with open("backup.json", "w", encoding="utf-8") as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2)
    # Send file
    await event.reply(file="backup.json")
    await event.edit("✅ تم إنشاء النسخة الاحتياطية.")

# ========== AI CHAT ==========
async def chat_with_ai(message: str) -> str:
    try:
        payload = {"device_id": "32430D60C2DF1529",
                  "order_id": "",
                  "product_id": "",
                  "purchase_token": "",
                  "subscription_id": ""}

        headers = {
            'User-Agent': "Chat Smith Android, Version 4.0.5(1032)",
            'Accept': "application/json",
            'Accept-Encoding': "gzip",
            'Content-Type': "application/json",
            'x-vulcan-application-id': "com.smartwidgetlabs.chatgpt",
            'x-vulcan-request-id': "9149487891757681852694",
            'content-type': "application/json; charset=utf-8"}
        
        re = requests.post("https://api.vulcanlabs.co/smith-auth/api/v1/token", data=json.dumps(payload), headers=headers).json()
        tok = re["AccessToken"]

        payload = {
            "model": "gpt-4o-mini",
            "user": "32430D60C2DF1529",
            "messages": [{"role": "user", "content": message}],
            "max_tokens": 1000,
            "nsfw_check": True
        }

        headers.update({
            'x-auth-token': "challenge_token",
            'authorization': f"Bearer {tok}",
            'x-vulcan-request-id': "9149487891757681854021",
        })

        res = requests.post("https://api.vulcanlabs.co/smith-v2/api/v7/chat_android", data=json.dumps(payload), headers=headers).json()
        return res["choices"][0]["Message"]["content"]
    except Exception as e:
        return f"❌ خطأ في الذكاء الاصطناعي: {str(e)}"

# ========== MAIN ==========
async def main():
    await init_db()
    logger.info("Bot started, initializing...")
    await bot.start()
    logger.info(f"Bot running as @{(await bot.get_me()).username}")
    await bot.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())