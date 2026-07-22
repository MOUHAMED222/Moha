
#!/usr/bin/env python3

import asyncio
import json
import logging
import os
import random
import sqlite3
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

from telegram import (
    Bot,
    Chat,
    ChatMember,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    InputMediaVideo,
    Message,
    Update,
    User,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    ChatMemberHandler,
)

BOT_TOKEN = "8619402064:AAEhoWpJKTsntij_8Zfzh_xwk1th1xgVBwU"
OWNER_ID = [6891530912, 1995454152]
CHANNEL_LINK = "https://t.me/forzd9"
GROUP_LINK = "https://t.me/maamihooo"
SUPPORT_LINK = "https://t.me/mouhamed_ma"
DEVELOPER_LINK = "https://t.me/mouhamed_ma"
WELCOME_IMAGE_URL = "https://d.top4top.io/p_38534mjfh0.jpg"
DEFAULT_WELCOME_MESSAGE = (
    "🌟 مرحباً بك في البوت 🌟\n"
    "هذا البوت مخصص لإدارة المجموعات بشكل احترافي.\n"
    "يمكنك استخدام الأزرار للتنقل."
)
VERSES = [
    "﴿ إِنَّ اللَّهَ وَمَلَائِكَتَهُ يُصَلُّونَ عَلَى النَّبِيِّ ۚ يَا أَيُّهَا الَّذِينَ آمَنُوا صَلُّوا عَلَيْهِ وَسَلِّمُوا تَسْلِيمًا ﴾ [الأحزاب: 56]",
    "﴿ وَمَا تَوْفِيقِي إِلَّا بِاللَّهِ ۚ عَلَيْهِ تَوَكَّلْتُ وَإِلَيْهِ أُنِيبُ ﴾ [هود: 88]",
    "﴿ رَبِّ اشْرَحْ لِي صَدْرِي * وَيَسِّرْ لِي أَمْرِي * وَاحْلُلْ عُقْدَةً مِنْ لِسَانِي * يَفْقَهُوا قَوْلِي ﴾ [طه: 25-28]",
    "﴿ وَقُلْ رَبِّ زِدْنِي عِلْمًا ﴾ [طه: 114]",
    "﴿ إِنَّ مَعَ الْعُسْرِ يُسْرًا ﴾ [الشرح: 6]",
]
DB_FILE = "bot_database.db"
KEYWORDS_FILE = "keywords.txt"
KEYWORDS_DIR = "keywords"
PAGE_SIZE = 8

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

class StyledButton:
    @staticmethod
    def create(
        text: str,
        callback_data: str = None,
        style: str = "secondary",
        url: Optional[str] = None,
    ) -> InlineKeyboardButton:
        if url:
            return InlineKeyboardButton(text=text, url=url)
        return InlineKeyboardButton(text=text, callback_data=callback_data)

class Database:
    def __init__(self, db_file: str = DB_FILE):
        self.db_file = db_file
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_file, check_same_thread=False)

    def _init_db(self):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    joined_date TEXT,
                    is_bot BOOLEAN DEFAULT 0,
                    is_admin BOOLEAN DEFAULT 0,
                    is_owner BOOLEAN DEFAULT 0,
                    is_banned BOOLEAN DEFAULT 0,
                    last_activity TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS groups (
                    chat_id INTEGER PRIMARY KEY,
                    chat_title TEXT,
                    chat_username TEXT,
                    added_date TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    is_bot_admin BOOLEAN DEFAULT 0,
                    members_count INTEGER DEFAULT 0
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    user_id INTEGER PRIMARY KEY,
                    can_manage_replies BOOLEAN DEFAULT 0,
                    can_manage_groups BOOLEAN DEFAULT 0,
                    can_manage_admins BOOLEAN DEFAULT 0,
                    can_broadcast BOOLEAN DEFAULT 0,
                    can_view_stats BOOLEAN DEFAULT 0,
                    can_manage_settings BOOLEAN DEFAULT 0,
                    can_backup BOOLEAN DEFAULT 0,
                    added_by INTEGER,
                    added_date TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auto_replies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword TEXT NOT NULL,
                    reply_type TEXT DEFAULT 'text',
                    reply_content TEXT,
                    caption TEXT,
                    parse_mode TEXT DEFAULT 'HTML',
                    is_active BOOLEAN DEFAULT 1,
                    created_by INTEGER,
                    created_date TEXT,
                    last_used TEXT,
                    use_count INTEGER DEFAULT 0
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS forced_channels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id INTEGER NOT NULL UNIQUE,
                    channel_username TEXT,
                    channel_title TEXT,
                    added_by INTEGER,
                    added_date TEXT,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT,
                    target_id TEXT,
                    details TEXT,
                    timestamp TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS backups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    backup_file TEXT,
                    created_at TEXT,
                    created_by INTEGER,
                    size INTEGER
                )
            """)
            for owner in OWNER_ID:
                cursor.execute(
                    "INSERT OR IGNORE INTO admins (user_id, added_by, added_date) VALUES (?, ?, ?)",
                    (owner, owner, datetime.now().isoformat())
                )
                cursor.execute("""
                    UPDATE admins SET
                        can_manage_replies = 1,
                        can_manage_groups = 1,
                        can_manage_admins = 1,
                        can_broadcast = 1,
                        can_view_stats = 1,
                        can_manage_settings = 1,
                        can_backup = 1
                    WHERE user_id = ?
                """, (owner,))
                cursor.execute(
                    "INSERT OR IGNORE INTO users (user_id, is_owner, joined_date) VALUES (?, ?, ?)",
                    (owner, 1, datetime.now().isoformat())
                )
            conn.commit()
            logger.info("قاعدة البيانات جاهزة.")

    def get_or_create_user(self, user: User) -> Dict:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user.id,))
            row = cursor.fetchone()
            if row:
                cursor.execute(
                    "UPDATE users SET last_activity = ? WHERE user_id = ?",
                    (datetime.now().isoformat(), user.id)
                )
                conn.commit()
                return self._row_to_dict_user(row)
            now = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO users (
                    user_id, username, first_name, last_name, joined_date, is_bot, last_activity
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user.id, user.username, user.first_name, user.last_name, now, user.is_bot, now))
            conn.commit()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user.id,))
            row = cursor.fetchone()
            return self._row_to_dict_user(row)

    def _row_to_dict_user(self, row) -> Dict:
        return {
            "user_id": row[0],
            "username": row[1],
            "first_name": row[2],
            "last_name": row[3],
            "joined_date": row[4],
            "is_bot": row[5],
            "is_admin": row[6],
            "is_owner": row[7],
            "is_banned": row[8],
            "last_activity": row[9],
        }

    def add_group(self, chat: Chat) -> bool:
        with self._connect() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO groups (
                        chat_id, chat_title, chat_username, added_date, is_active
                    ) VALUES (?, ?, ?, ?, ?)
                """, (chat.id, chat.title, chat.username, now, 1))
                conn.commit()
                return True
            except Exception as e:
                logger.error(f"خطأ في إضافة مجموعة: {e}")
                return False

    def get_all_groups(self) -> List[Dict]:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM groups ORDER BY added_date DESC")
            rows = cursor.fetchall()
            return [self._row_to_dict_group(row) for row in rows]

    def get_active_groups(self) -> List[Dict]:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM groups WHERE is_active = 1 ORDER BY added_date DESC")
            rows = cursor.fetchall()
            return [self._row_to_dict_group(row) for row in rows]

    def get_group(self, chat_id: int) -> Optional[Dict]:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM groups WHERE chat_id = ?", (chat_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_dict_group(row)
            return None

    def update_group_active(self, chat_id: int, active: bool) -> bool:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE groups SET is_active = ? WHERE chat_id = ?",
                (1 if active else 0, chat_id)
            )
            conn.commit()
            return True

    def delete_group(self, chat_id: int) -> bool:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM groups WHERE chat_id = ?", (chat_id,))
            conn.commit()
            return True

    def _row_to_dict_group(self, row) -> Dict:
        return {
            "chat_id": row[0],
            "chat_title": row[1],
            "chat_username": row[2],
            "added_date": row[3],
            "is_active": row[4],
            "is_bot_admin": row[5],
            "members_count": row[6],
        }

    def is_admin(self, user_id: int) -> bool:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM admins WHERE user_id = ?", (user_id,))
            return cursor.fetchone() is not None

    def get_admin_permissions(self, user_id: int) -> Dict:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM admins WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if not row:
                return {}
            return {
                "user_id": row[0],
                "can_manage_replies": bool(row[1]),
                "can_manage_groups": bool(row[2]),
                "can_manage_admins": bool(row[3]),
                "can_broadcast": bool(row[4]),
                "can_view_stats": bool(row[5]),
                "can_manage_settings": bool(row[6]),
                "can_backup": bool(row[7]),
                "added_by": row[8],
                "added_date": row[9],
            }

    def add_admin(self, user_id: int, added_by: int, permissions: Dict[str, bool] = None) -> bool:
        if permissions is None:
            permissions = {
                "can_manage_replies": False,
                "can_manage_groups": False,
                "can_manage_admins": False,
                "can_broadcast": False,
                "can_view_stats": False,
                "can_manage_settings": False,
                "can_backup": False,
            }
        with self._connect() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO admins (
                        user_id, can_manage_replies, can_manage_groups, can_manage_admins,
                        can_broadcast, can_view_stats, can_manage_settings, can_backup,
                        added_by, added_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    1 if permissions.get("can_manage_replies", False) else 0,
                    1 if permissions.get("can_manage_groups", False) else 0,
                    1 if permissions.get("can_manage_admins", False) else 0,
                    1 if permissions.get("can_broadcast", False) else 0,
                    1 if permissions.get("can_view_stats", False) else 0,
                    1 if permissions.get("can_manage_settings", False) else 0,
                    1 if permissions.get("can_backup", False) else 0,
                    added_by,
                    now,
                ))
                conn.commit()
                return True
            except Exception as e:
                logger.error(f"خطأ في إضافة أدمن: {e}")
                return False

    def remove_admin(self, user_id: int) -> bool:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
            conn.commit()
            return True

    def get_all_admins(self) -> List[Dict]:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM admins")
            rows = cursor.fetchall()
            return [{
                "user_id": row[0],
                "can_manage_replies": bool(row[1]),
                "can_manage_groups": bool(row[2]),
                "can_manage_admins": bool(row[3]),
                "can_broadcast": bool(row[4]),
                "can_view_stats": bool(row[5]),
                "can_manage_settings": bool(row[6]),
                "can_backup": bool(row[7]),
                "added_by": row[8],
                "added_date": row[9],
            } for row in rows]

    def add_reply(self, keyword: str, reply_type: str, reply_content: str,
                  caption: str = "", parse_mode: str = "HTML", created_by: int = OWNER_ID) -> bool:
        with self._connect() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            try:
                cursor.execute("""
                    INSERT INTO auto_replies (
                        keyword, reply_type, reply_content, caption, parse_mode,
                        created_by, created_date, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (keyword.lower(), reply_type, reply_content, caption, parse_mode, created_by, now, 1))
                conn.commit()
                return True
            except Exception as e:
                logger.error(f"خطأ في إضافة رد: {e}")
                return False

    def add_reply_bulk(self, keywords: List[str], reply_type: str, reply_content: str,
                       caption: str = "", parse_mode: str = "HTML", created_by: int = OWNER_ID) -> bool:
        success = True
        for kw in keywords:
            if not self.add_reply(kw, reply_type, reply_content, caption, parse_mode, created_by):
                success = False
        return success

    def get_reply_by_keyword(self, keyword: str) -> Optional[Dict]:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM auto_replies WHERE keyword = ? AND is_active = 1",
                (keyword.lower(),)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_dict_reply(row)
            return None

    def get_all_replies(self, active_only: bool = False) -> List[Dict]:
        with self._connect() as conn:
            cursor = conn.cursor()
            if active_only:
                cursor.execute("SELECT * FROM auto_replies WHERE is_active = 1 ORDER BY keyword")
            else:
                cursor.execute("SELECT * FROM auto_replies ORDER BY keyword")
            rows = cursor.fetchall()
            return [self._row_to_dict_reply(row) for row in rows]

    def update_reply(self, reply_id: int, data: Dict) -> bool:
        with self._connect() as conn:
            cursor = conn.cursor()
            set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
            values = list(data.values()) + [reply_id]
            query = f"UPDATE auto_replies SET {set_clause} WHERE id = ?"
            try:
                cursor.execute(query, values)
                conn.commit()
                return True
            except Exception as e:
                logger.error(f"خطأ في تحديث رد: {e}")
                return False

    def delete_reply(self, reply_id: int) -> bool:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM auto_replies WHERE id = ?", (reply_id,))
            conn.commit()
            return True

    def toggle_reply_active(self, reply_id: int, active: bool) -> bool:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE auto_replies SET is_active = ? WHERE id = ?",
                (1 if active else 0, reply_id)
            )
            conn.commit()
            return True

    def increment_reply_usage(self, reply_id: int):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE auto_replies SET use_count = use_count + 1, last_used = ? WHERE id = ?",
                (datetime.now().isoformat(), reply_id)
            )
            conn.commit()

    def _row_to_dict_reply(self, row) -> Dict:
        return {
            "id": row[0],
            "keyword": row[1],
            "reply_type": row[2],
            "reply_content": row[3],
            "caption": row[4],
            "parse_mode": row[5],
            "is_active": bool(row[6]),
            "created_by": row[7],
            "created_date": row[8],
            "last_used": row[9],
            "use_count": row[10],
        }

    def add_forced_channel(self, channel_id: int, username: str, title: str, added_by: int) -> bool:
        with self._connect() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            try:
                cursor.execute("""
                    INSERT INTO forced_channels (
                        channel_id, channel_username, channel_title, added_by, added_date, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (channel_id, username, title, added_by, now, 1))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                logger.warning("القناة موجودة بالفعل.")
                return False
            except Exception as e:
                logger.error(f"خطأ في إضافة قناة إجبارية: {e}")
                return False

    def remove_forced_channel(self, channel_id: int) -> bool:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM forced_channels WHERE channel_id = ?", (channel_id,))
            conn.commit()
            return True

    def get_forced_channels(self, active_only: bool = True) -> List[Dict]:
        with self._connect() as conn:
            cursor = conn.cursor()
            if active_only:
                cursor.execute("SELECT * FROM forced_channels WHERE is_active = 1")
            else:
                cursor.execute("SELECT * FROM forced_channels")
            rows = cursor.fetchall()
            return [{
                "id": row[0],
                "channel_id": row[1],
                "channel_username": row[2],
                "channel_title": row[3],
                "added_by": row[4],
                "added_date": row[5],
                "is_active": bool(row[6]),
            } for row in rows]

    def toggle_forced_channel(self, channel_id: int, active: bool) -> bool:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE forced_channels SET is_active = ? WHERE channel_id = ?",
                (1 if active else 0, channel_id)
            )
            conn.commit()
            return True

    def get_setting(self, key: str, default: str = "") -> str:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                return row[0]
            return default

    def set_setting(self, key: str, value: str) -> bool:
        with self._connect() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
                (key, value, now)
            )
            conn.commit()
            return True

    def add_log(self, user_id: int, action: str, target_id: str = "", details: str = ""):
        with self._connect() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            cursor.execute(
                "INSERT INTO logs (user_id, action, target_id, details, timestamp) VALUES (?, ?, ?, ?, ?)",
                (user_id, action, target_id, details, now)
            )
            conn.commit()

    def get_logs(self, limit: int = 100) -> List[Dict]:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM logs ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [{
                "id": row[0],
                "user_id": row[1],
                "action": row[2],
                "target_id": row[3],
                "details": row[4],
                "timestamp": row[5],
            } for row in rows]

    def get_stats(self) -> Dict:
        with self._connect() as conn:
            cursor = conn.cursor()
            users_count = cursor.execute("SELECT COUNT(*) FROM users WHERE is_bot = 0").fetchone()[0]
            groups_count = cursor.execute("SELECT COUNT(*) FROM groups").fetchone()[0]
            active_groups = cursor.execute("SELECT COUNT(*) FROM groups WHERE is_active = 1").fetchone()[0]
            replies_count = cursor.execute("SELECT COUNT(*) FROM auto_replies WHERE is_active = 1").fetchone()[0]
            forced_channels = cursor.execute("SELECT COUNT(*) FROM forced_channels WHERE is_active = 1").fetchone()[0]
            return {
                "users": users_count,
                "groups": groups_count,
                "active_groups": active_groups,
                "replies": replies_count,
                "forced_channels": forced_channels,
            }

    def create_backup(self, backup_file: str, created_by: int) -> bool:
        try:
            import shutil
            shutil.copy2(self.db_file, backup_file)
            size = os.path.getsize(backup_file)
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO backups (backup_file, created_at, created_by, size) VALUES (?, ?, ?, ?)",
                    (backup_file, datetime.now().isoformat(), created_by, size)
                )
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"خطأ في إنشاء نسخة احتياطية: {e}")
            return False

    def get_backups(self) -> List[Dict]:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM backups ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [{
                "id": row[0],
                "backup_file": row[1],
                "created_at": row[2],
                "created_by": row[3],
                "size": row[4],
            } for row in rows]

    def restore_backup(self, backup_file: str) -> bool:
        try:
            import shutil
            shutil.copy2(backup_file, self.db_file)
            return True
        except Exception as e:
            logger.error(f"خطأ في استعادة النسخة: {e}")
            return False

db = Database()
app = None
file_keyword_map = {}

def is_owner(user_id: int) -> bool:
    return user_id in OWNER_ID

def is_admin_user(user_id: int) -> bool:
    return db.is_admin(user_id) or is_owner(user_id)

def has_permission(user_id: int, perm: str) -> bool:
    if is_owner(user_id):
        return True
    perms = db.get_admin_permissions(user_id)
    return perms.get(perm, False)

def format_blockquote(text: str, parse_mode: str = None) -> Tuple[str, str]:
    return f"<blockquote>{text}</blockquote>", ParseMode.HTML

def get_back_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("رجوع", callback_data="back_to_previous", style="primary")]
    ])

def get_main_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            StyledButton.create("القناة الخاصة", url=CHANNEL_LINK, style="primary"),
            StyledButton.create("المجموعة", url=GROUP_LINK, style="primary"),
        ],
        [
            StyledButton.create("الدعم", url=SUPPORT_LINK, style="info"),
            StyledButton.create("المطور", url=DEVELOPER_LINK, style="info"),
        ],
        [
            StyledButton.create("إضافة في مجموعة", callback_data="add_to_group", style="success"),
            StyledButton.create("لوحة الأدمن", callback_data="admin_panel", style="danger"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)

def get_admin_panel_keyboard(user_id: int) -> InlineKeyboardMarkup:
    buttons = []
    row = []
    if has_permission(user_id, "can_manage_replies") or is_owner(user_id):
        row.append(StyledButton.create("إدارة الردود", callback_data="admin_replies", style="primary"))
    if has_permission(user_id, "can_manage_groups") or is_owner(user_id):
        row.append(StyledButton.create("إدارة المجموعات", callback_data="admin_groups", style="primary"))
    if row:
        buttons.append(row)
        row = []
    if has_permission(user_id, "can_manage_admins") or is_owner(user_id):
        row.append(StyledButton.create("إدارة الأدمن", callback_data="admin_admins", style="primary"))
    if has_permission(user_id, "can_broadcast") or is_owner(user_id):
        row.append(StyledButton.create("نشر رسالة", callback_data="admin_broadcast", style="primary"))
    if row:
        buttons.append(row)
        row = []
    if has_permission(user_id, "can_view_stats") or is_owner(user_id):
        row.append(StyledButton.create("الإحصائيات", callback_data="admin_stats", style="info"))
    if has_permission(user_id, "can_manage_settings") or is_owner(user_id):
        row.append(StyledButton.create("الإعدادات", callback_data="admin_settings", style="secondary"))
    if row:
        buttons.append(row)
        row = []
    if has_permission(user_id, "can_backup") or is_owner(user_id):
        row.append(StyledButton.create("النسخ الاحتياطي", callback_data="admin_backup", style="secondary"))
    if has_permission(user_id, "can_view_stats") or is_owner(user_id):
        row.append(StyledButton.create("سجل العمليات", callback_data="admin_logs", style="info"))
    if row:
        buttons.append(row)
        row = []
    buttons.append([
        StyledButton.create("الاشتراك الإجباري", callback_data="forced_subscription", style="warning"),
        StyledButton.create("الرجوع للقائمة الرئيسية", callback_data="main_menu", style="secondary"),
    ])
    return InlineKeyboardMarkup(buttons)

def get_back_button_with_callback() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [StyledButton.create("رجوع", callback_data="back_to_previous", style="secondary")]
    ])

def format_verse() -> str:
    return random.choice(VERSES)

def get_private_verse() -> str:
    return random.choice(VERSES)

def get_group_verse() -> str:
    return random.choice(VERSES)

async def edit_message_safely(
    query,
    text: str,
    reply_markup: InlineKeyboardMarkup = None,
    parse_mode: str = ParseMode.HTML
):
    formatted_text, new_parse_mode = format_blockquote(text, parse_mode)
    message = query.message

    if len(formatted_text) > 900 and (message.photo or message.video or message.audio or message.document):
        await query.message.reply_text(
            text=formatted_text,
            reply_markup=reply_markup,
            parse_mode=new_parse_mode
        )
        try:
            await query.message.delete()
        except Exception:
            pass
        return

    if message.photo or message.video or message.audio or message.document:
        try:
            await query.edit_message_caption(
                caption=formatted_text[:1020],
                reply_markup=reply_markup,
                parse_mode=new_parse_mode
            )
        except Exception as e:
            if "Media_caption_too_long" in str(e):
                await query.message.reply_text(
                    text=formatted_text,
                    reply_markup=reply_markup,
                    parse_mode=new_parse_mode
                )
                try:
                    await query.message.delete()
                except Exception:
                    pass
            else:
                raise
    else:
        await query.edit_message_text(
            text=formatted_text,
            reply_markup=reply_markup,
            parse_mode=new_parse_mode
        )

def load_keywords_from_file(file_path: str = KEYWORDS_FILE) -> Dict[str, str]:
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.read().strip().splitlines()
        if not lines:
            return {}
        result = {}
        for line in lines:
            if '|' not in line:
                continue
            keywords_part, reply = line.split('|', 1)
            keywords = [kw.strip().lower() for kw in keywords_part.split(',') if kw.strip()]
            reply = reply.strip()
            if keywords and reply:
                for kw in keywords:
                    result[kw] = reply
        return result
    except Exception as e:
        logger.error(f"خطأ في قراءة ملف الكلمات: {e}")
        return {}

def load_all_keyword_files(keywords_dir: str = KEYWORDS_DIR) -> Dict[str, str]:
    result = {}
    if not os.path.exists(keywords_dir):
        return result
    try:
        for filename in os.listdir(keywords_dir):
            if not filename.endswith('.txt'):
                continue
            filepath = os.path.join(keywords_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = [line.strip() for line in f.readlines() if line.strip()]
                if not lines:
                    continue
                reply_key = os.path.splitext(filename)[0]
                for kw in lines:
                    kw_lower = kw.lower()
                    if kw_lower:
                        if kw_lower in result:
                            logger.warning(f"كلمة مكررة في الملفات: {kw_lower}")
                        result[kw_lower] = reply_key
            except Exception as e:
                logger.error(f"خطأ في قراءة الملف {filename}: {e}")
    except Exception as e:
        logger.error(f"خطأ في تحميل الملفات: {e}")
    return result

def save_keywords_to_file(keywords_map: Dict[str, str], file_path: str = KEYWORDS_FILE):
    try:
        reply_to_keywords = {}
        for kw, reply in keywords_map.items():
            if reply not in reply_to_keywords:
                reply_to_keywords[reply] = []
            reply_to_keywords[reply].append(kw)
        with open(file_path, 'w', encoding='utf-8') as f:
            for reply, keywords in reply_to_keywords.items():
                line = ", ".join(keywords) + " | " + reply
                f.write(line + "\n")
        return True
    except Exception as e:
        logger.error(f"خطأ في حفظ ملف الكلمات: {e}")
        return False

keyword_reply_map = load_keywords_from_file()
file_keyword_map = load_all_keyword_files()

async def reload_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_owner(user.id):
        formatted, _ = format_blockquote("⛔ هذا الأمر للمالك فقط.", ParseMode.HTML)
        await update.message.reply_text(formatted, parse_mode=ParseMode.HTML)
        return
    global keyword_reply_map, file_keyword_map
    keyword_reply_map = load_keywords_from_file()
    file_keyword_map = load_all_keyword_files()
    text_count = len(keyword_reply_map)
    file_count = len(file_keyword_map)
    formatted, _ = format_blockquote(
        f"✅ تم إعادة تحميل الكلمات بنجاح.\n"
        f"📝 من keywords.txt: {text_count} كلمة\n"
        f"📁 من ملفات TXT: {file_count} كلمة",
        ParseMode.HTML
    )
    await update.message.reply_text(formatted, parse_mode=ParseMode.HTML)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return
    db.get_or_create_user(user)
    if not await check_forced_subscription(update, context):
        return
    verse = get_private_verse()
    welcome_text = (
        f"<b>🌟 مرحباً بك في بوت إدارة المجموعات الاحترافي</b>\n\n"
        f"<blockquote>يوفر هذا البوت حلولاً متكاملة لإدارة مجموعاتك،\nمع ميزات متقدمة وسهولة في الاستخدام.</blockquote>\n\n"
        f"📖 <blockquote>{verse}</blockquote>\n\n"
        f"👤 <b>المطور:</b> <a href='{DEVELOPER_LINK}'>المطور</a>\n"
        f"📢 <b>القناة:</b> <a href='{CHANNEL_LINK}'>القناة</a>\n"
        f"👥 <b>المجموعة:</b> <a href='{GROUP_LINK}'>المجموعة</a>"
    )
    formatted_welcome, _ = format_blockquote(welcome_text, ParseMode.HTML)
    await update.message.reply_photo(
        photo=WELCOME_IMAGE_URL,
        caption=formatted_welcome,
        reply_markup=get_main_keyboard(),
        parse_mode=ParseMode.HTML,
    )

async def check_forced_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    if not user:
        return False
    channels = db.get_forced_channels(active_only=True)
    if not channels:
        return True
    not_subscribed = []
    bot = context.bot
    for ch in channels:
        try:
            member = await bot.get_chat_member(chat_id=ch["channel_id"], user_id=user.id)
            if member.status not in ["member", "administrator", "creator"]:
                not_subscribed.append(ch)
        except Exception as e:
            logger.error(f"خطأ في التحقق من عضوية {ch['channel_id']}: {e}")
            not_subscribed.append(ch)
    if not_subscribed:
        buttons = []
        for ch in not_subscribed:
            username = ch.get("channel_username", "")
            link = f"https://t.me/{username}" if username else f"https://t.me/{ch['channel_id']}"
            buttons.append([
                InlineKeyboardButton(
                    text=f"اشترك في {ch.get('channel_title', 'القناة')}",
                    url=link
                )
            ])
        buttons.append([
            StyledButton.create("تحقق من الاشتراك", callback_data="check_subscription", style="success")
        ])
        buttons.append([StyledButton.create("رجوع", callback_data="main_menu", style="secondary")])
        keyboard = InlineKeyboardMarkup(buttons)
        if update.callback_query:
            await update.callback_query.answer()
            await edit_message_safely(
                update.callback_query,
                "⚠️ أنت غير مشترك في القنوات الإجبارية التالية:\n"
                "يرجى الاشتراك ثم اضغط 'تحقق من الاشتراك'.",
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
        else:
            formatted, _ = format_blockquote(
                "⚠️ أنت غير مشترك في القنوات الإجبارية التالية:\n"
                "يرجى الاشتراك ثم اضغط 'تحقق من الاشتراك'.",
                ParseMode.HTML
            )
            await update.message.reply_text(
                formatted,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )
        return False
    return True

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await edit_message_safely(
        query,
        "<b>🌟 القائمة الرئيسية</b>\n"
        "يرجى اختيار أحد الخيارات المتاحة:",
        reply_markup=get_main_keyboard(),
        parse_mode=ParseMode.HTML
    )

async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await show_main_menu(update, context)

async def show_forced_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    channels = db.get_forced_channels(active_only=False)
    text = "<b>📢 إدارة الاشتراك الإجباري</b>\n\n"
    if channels:
        for ch in channels:
            status = "✅ مفعل" if ch["is_active"] else "❌ معطل"
            text += f"• {ch.get('channel_title', 'بدون عنوان')} (ID: {ch['channel_id']}) — {status}\n"
    else:
        text += "لا توجد قنوات إجبارية حالياً.\n"
    text += "\nاستخدم الأزرار لإدارة القنوات."
    buttons = [
        [StyledButton.create("➕ إضافة قناة", callback_data="add_forced_channel", style="success")],
        [StyledButton.create("🗑️ حذف قناة", callback_data="remove_forced_channel", style="danger")],
        [StyledButton.create("🔄 تبديل تفعيل قناة", callback_data="toggle_forced_channel", style="warning")],
        [StyledButton.create("رجوع", callback_data="admin_panel", style="secondary")],
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    await edit_message_safely(query, text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

async def forced_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    if not is_admin_user(user.id):
        await query.answer("⛔ ليس لديك صلاحية.", show_alert=True)
        return
    await query.answer()
    await show_forced_subscription(update, context)

async def add_forced_channel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["action"] = "add_forced_channel"
    context.user_data["previous_menu"] = "forced_subscription"
    await edit_message_safely(
        query,
        "<b>✏️ إضافة قناة إجبارية</b>\n\n"
        "أرسل معرف القناة الرقمي أو معرفها @username.\n"
        "مثال: -100123456789 أو @my_channel\n\n"
        "لإلغاء العملية اضغط /cancel.",
        reply_markup=get_back_button_with_callback(),
        parse_mode=ParseMode.HTML,
    )

async def remove_forced_channel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    channels = db.get_forced_channels(active_only=False)
    if not channels:
        await edit_message_safely(
            query,
            "لا توجد قنوات لحذفها.",
            reply_markup=get_back_button_with_callback(),
        )
        return
    buttons = []
    for ch in channels:
        buttons.append([
            InlineKeyboardButton(
                text=f"❌ {ch.get('channel_title', 'قناة')}",
                callback_data=f"del_forced_ch_{ch['channel_id']}"
            )
        ])
    buttons.append([
        StyledButton.create("رجوع", callback_data="forced_subscription", style="secondary")
    ])
    await edit_message_safely(
        query,
        "اختر القناة التي تريد حذفها:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )

async def delete_forced_channel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    if not is_admin_user(user.id):
        await query.answer("⛔ ليس لديك صلاحية.", show_alert=True)
        return
    channel_id = int(query.data.split("_")[-1])
    db.remove_forced_channel(channel_id)
    db.add_log(user.id, "حذف قناة إجبارية", str(channel_id), f"القناة {channel_id}")
    await query.answer("تم الحذف بنجاح ✅")
    await forced_subscription_callback(update, context)

async def toggle_forced_channel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    channels = db.get_forced_channels(active_only=False)
    if not channels:
        await edit_message_safely(
            query,
            "لا توجد قنوات.",
            reply_markup=get_back_button_with_callback(),
        )
        return
    buttons = []
    for ch in channels:
        status = "✅" if ch["is_active"] else "❌"
        buttons.append([
            InlineKeyboardButton(
                text=f"{status} {ch.get('channel_title', 'قناة')}",
                callback_data=f"toggle_forced_{ch['channel_id']}"
            )
        ])
    buttons.append([
        StyledButton.create("رجوع", callback_data="forced_subscription", style="secondary")
    ])
    await edit_message_safely(
        query,
        "اختر القناة لتبديل التفعيل:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )

async def toggle_forced_channel_exec(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    if not is_admin_user(user.id):
        await query.answer("⛔ ليس لديك صلاحية.", show_alert=True)
        return
    channel_id = int(query.data.split("_")[-1])
    channels = db.get_forced_channels(active_only=False)
    ch = next((c for c in channels if c["channel_id"] == channel_id), None)
    if ch:
        new_status = not ch["is_active"]
        db.toggle_forced_channel(channel_id, new_status)
        db.add_log(user.id, "تبديل تفعيل قناة إجبارية", str(channel_id), f"الحالة الجديدة: {new_status}")
        await query.answer("تم التبديل ✅")
    await toggle_forced_channel_callback(update, context)

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    await edit_message_safely(
        query,
        "<b>🔧 لوحة التحكم الإدارية</b>\n"
        "اختر القسم المناسب لإدارته:",
        reply_markup=get_admin_panel_keyboard(user.id),
        parse_mode=ParseMode.HTML,
    )

async def admin_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    if not is_admin_user(user.id):
        await query.answer("⛔ ليس لديك صلاحية.", show_alert=True)
        return
    await query.answer()
    await show_admin_panel(update, context)

async def show_admin_replies(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    query = update.callback_query
    all_replies = db.get_all_replies(active_only=False)
    total = len(all_replies)
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE) if total > 0 else 1

    if page < 0:
        page = 0
    if page >= total_pages:
        page = total_pages - 1

    start = page * PAGE_SIZE
    end = min(start + PAGE_SIZE, total)

    text = "<b>📝 إدارة الردود التلقائية</b>\n\n"
    if total == 0:
        text += "لا توجد ردود تلقائية حالياً.\n"
    else:
        page_replies = all_replies[start:end]
        for r in page_replies:
            status = "✅ مفعل" if r["is_active"] else "❌ معطل"
            text += f"• <b>{r['keyword']}</b> (ID: {r['id']}) — {status}\n"
        text += f"\nالصفحة {page+1} من {total_pages} (إجمالي {total} رد)"

    buttons = []
    row = []
    # أزرار الإجراءات لكل رد في الصفحة (تعديل، حذف، تبديل)
    for r in page_replies:
        buttons.append([
            InlineKeyboardButton(
                f"✏️ {r['keyword'][:10]}",
                callback_data=f"edit_reply_{r['id']}_{page}"
            ),
            InlineKeyboardButton(
                f"🗑️",
                callback_data=f"delete_reply_{r['id']}_{page}"
            ),
            InlineKeyboardButton(
                f"🔄",
                callback_data=f"toggle_reply_{r['id']}_{page}"
            ),
        ])

    # أزرار التنقل بين الصفحات
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅ السابق", callback_data=f"admin_replies_{page-1}", style="primary"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("التالي", callback_data=f"admin_replies_{page+1}", style="primary"))
    if nav_row:
        buttons.append(nav_row)

    # أزرار الإجراءات العامة
    buttons.append([StyledButton.create("➕ إضافة رد جديد", callback_data="add_reply_start", style="success")])
    buttons.append([StyledButton.create("🔙 رجوع كامل", callback_data="admin_panel", style="secondary")])

    await edit_message_safely(
        query,
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.HTML,
    )

async def admin_replies_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    if not has_permission(user.id, "can_manage_replies") and not is_owner(user.id):
        await query.answer("⛔ ليس لديك صلاحية.", show_alert=True)
        return
    await query.answer()
    page = 0
    data = query.data
    if data.startswith("admin_replies_"):
        try:
            page = int(data.split("_")[-1])
        except ValueError:
            page = 0
    await show_admin_replies(update, context, page)

async def add_reply_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["action"] = "add_reply_input"
    context.user_data["previous_menu"] = "admin_replies"
    context.user_data["page"] = 0
    await edit_message_safely(
        query,
        "<b>✏️ إضافة رد تلقائي جديد</b>\n\n"
        "أرسل كلمة مفتاحية واحدة، أو ارفع ملف TXT يحتوي على الكلمات المفتاحية (كل كلمة في سطر).\n"
        "لإلغاء العملية اضغط /cancel.",
        reply_markup=get_back_button_with_callback(),
        parse_mode=ParseMode.HTML,
    )

async def edit_reply_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    parts = data.split("_")
    reply_id = int(parts[2])
    page = int(parts[3]) if len(parts) > 3 else 0

    context.user_data["edit_reply_id"] = reply_id
    context.user_data["edit_page"] = page
    context.user_data["action"] = "edit_reply_keyword"
    context.user_data["previous_menu"] = "admin_replies"
    await edit_message_safely(
        query,
        "<b>✏️ تعديل رد تلقائي</b>\n\n"
        "أرسل الكلمة المفتاحية الجديدة، أو اكتب 'نفس' للإبقاء.\n"
        "ثم اتبع التعليمات.",
        reply_markup=get_back_button_with_callback(),
        parse_mode=ParseMode.HTML,
    )

async def delete_reply_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    parts = data.split("_")
    reply_id = int(parts[2])
    page = int(parts[3]) if len(parts) > 3 else 0

    user = query.from_user
    if not has_permission(user.id, "can_manage_replies") and not is_owner(user.id):
        await query.answer("⛔ ليس لديك صلاحية.", show_alert=True)
        return

    db.delete_reply(reply_id)
    db.add_log(user.id, "حذف رد", str(reply_id), f"الرد ID {reply_id}")
    await query.answer("تم الحذف ✅")
    await show_admin_replies(update, context, page)

async def delete_reply_exec(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # kept for compatibility, but we use delete_reply_start now
    pass

async def toggle_reply_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    parts = data.split("_")
    reply_id = int(parts[2])
    page = int(parts[3]) if len(parts) > 3 else 0

    user = query.from_user
    if not has_permission(user.id, "can_manage_replies") and not is_owner(user.id):
        await query.answer("⛔ ليس لديك صلاحية.", show_alert=True)
        return

    replies = db.get_all_replies(active_only=False)
    r = next((x for x in replies if x["id"] == reply_id), None)
    if r:
        new_status = not r["is_active"]
        db.toggle_reply_active(reply_id, new_status)
        db.add_log(user.id, "تبديل تفعيل رد", str(reply_id), f"الحالة: {new_status}")
        await query.answer("تم التبديل ✅")
    await show_admin_replies(update, context, page)

async def toggle_reply_exec(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass

async def show_admin_groups(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    query = update.callback_query
    groups = db.get_all_groups()
    total = len(groups)
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE) if total > 0 else 1

    if page < 0:
        page = 0
    if page >= total_pages:
        page = total_pages - 1

    start = page * PAGE_SIZE
    end = min(start + PAGE_SIZE, total)

    text = "<b>👥 إدارة المجموعات</b>\n\n"
    if total == 0:
        text += "لا توجد مجموعات مسجلة.\n"
    else:
        page_groups = groups[start:end]
        for g in page_groups:
            status = "🟢 مفعل" if g["is_active"] else "🔴 معطل"
            text += f"• {g.get('chat_title', 'بدون عنوان')} (ID: {g['chat_id']}) — {status}\n"
        text += f"\nالصفحة {page+1} من {total_pages} (إجمالي {total} مجموعة)"

    buttons = []
    for g in page_groups:
        buttons.append([
            InlineKeyboardButton(
                f"🔄 تبديل {g.get('chat_title', 'مجموعة')[:10]}",
                callback_data=f"toggle_group_{g['chat_id']}_{page}"
            ),
            InlineKeyboardButton(
                f"🗑️ حذف",
                callback_data=f"delete_group_{g['chat_id']}_{page}"
            ),
        ])

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅ السابق", callback_data=f"admin_groups_{page-1}", style="primary"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("التالي", callback_data=f"admin_groups_{page+1}", style="primary"))
    if nav_row:
        buttons.append(nav_row)

    buttons.append([StyledButton.create("🔙 رجوع كامل", callback_data="admin_panel", style="secondary")])

    await edit_message_safely(
        query,
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.HTML,
    )

async def admin_groups_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    if not has_permission(user.id, "can_manage_groups") and not is_owner(user.id):
        await query.answer("⛔ ليس لديك صلاحية.", show_alert=True)
        return
    await query.answer()
    page = 0
    data = query.data
    if data.startswith("admin_groups_"):
        try:
            page = int(data.split("_")[-1])
        except ValueError:
            page = 0
    await show_admin_groups(update, context, page)

async def toggle_group_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass

async def toggle_group_exec(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    data = query.data
    parts = data.split("_")
    chat_id = int(parts[2])
    page = int(parts[3]) if len(parts) > 3 else 0

    if not has_permission(user.id, "can_manage_groups") and not is_owner(user.id):
        await query.answer("⛔ ليس لديك صلاحية.", show_alert=True)
        return
    groups = db.get_all_groups()
    g = next((x for x in groups if x["chat_id"] == chat_id), None)
    if g:
        new_status = not g["is_active"]
        db.update_group_active(chat_id, new_status)
        db.add_log(user.id, "تبديل تفعيل مجموعة", str(chat_id), f"الحالة: {new_status}")
        await query.answer("تم التبديل ✅")
    await show_admin_groups(update, context, page)

async def delete_group_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass

async def delete_group_exec(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    data = query.data
    parts = data.split("_")
    chat_id = int(parts[2])
    page = int(parts[3]) if len(parts) > 3 else 0

    if not has_permission(user.id, "can_manage_groups") and not is_owner(user.id):
        await query.answer("⛔ ليس لديك صلاحية.", show_alert=True)
        return
    db.delete_group(chat_id)
    db.add_log(user.id, "حذف مجموعة", str(chat_id), "تم الحذف")
    await query.answer("تم الحذف ✅")
    await show_admin_groups(update, context, page)

async def list_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    groups = db.get_all_groups()
    if not groups:
        text = "لا توجد مجموعات."
    else:
        text = "<b>📋 قائمة المجموعات المسجلة:</b>\n\n"
        for g in groups[:50]:
            status = "🟢 مفعل" if g["is_active"] else "🔴 معطل"
            text += f"• {g.get('chat_title', 'بدون عنوان')} (ID: {g['chat_id']}) — {status}\n"
        if len(groups) > 50:
            text += f"\n... و{len(groups)-50} مجموعة أخرى."
    await edit_message_safely(
        query,
        text,
        reply_markup=get_back_button_with_callback(),
        parse_mode=ParseMode.HTML,
    )

async def show_admin_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    admins = db.get_all_admins()
    text = "<b>👤 إدارة الأدمن</b>\n\n"
    if admins:
        for a in admins:
            text += f"• {a['user_id']} (صلاحيات: {sum(1 for k,v in a.items() if k.startswith('can_') and v)})\n"
    else:
        text += "لا يوجد أدمن غير المالك.\n"
    buttons = [
        [StyledButton.create("➕ إضافة أدمن", callback_data="add_admin_start", style="success")],
        [StyledButton.create("🗑️ حذف أدمن", callback_data="remove_admin_start", style="danger")],
        [StyledButton.create("📋 عرض الأدمن", callback_data="list_admins", style="info")],
        [StyledButton.create("🔙 رجوع كامل", callback_data="admin_panel", style="secondary")],
    ]
    await edit_message_safely(
        query,
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.HTML,
    )

async def admin_admins_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    if not has_permission(user.id, "can_manage_admins") and not is_owner(user.id):
        await query.answer("⛔ ليس لديك صلاحية.", show_alert=True)
        return
    await query.answer()
    await show_admin_admins(update, context)

async def add_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["action"] = "add_admin_id"
    context.user_data["previous_menu"] = "admin_admins"
    await edit_message_safely(
        query,
        "<b>✏️ إضافة أدمن جديد</b>\n\n"
        "أرسل معرف المستخدم الرقمي.\n"
        "مثال: 123456789\n\n"
        "لإلغاء العملية اضغط /cancel.",
        reply_markup=get_back_button_with_callback(),
        parse_mode=ParseMode.HTML,
    )

async def remove_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    admins = db.get_all_admins()
    if not admins:
        await edit_message_safely(
            query,
            "لا يوجد أدمن لحذفهم.",
            reply_markup=get_back_button_with_callback(),
        )
        return
    buttons = []
    for a in admins:
        if a["user_id"] in OWNER_ID:
            continue
        buttons.append([
            InlineKeyboardButton(
                text=f"🗑️ {a['user_id']}",
                callback_data=f"remove_admin_{a['user_id']}"
            )
        ])
    buttons.append([
        StyledButton.create("رجوع", callback_data="admin_admins", style="secondary")
    ])
    await edit_message_safely(
        query,
        "اختر الأدمن لحذفه:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )

async def remove_admin_exec(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    if not has_permission(user.id, "can_manage_admins") and not is_owner(user.id):
        await query.answer("⛔ ليس لديك صلاحية.", show_alert=True)
        return
    target_id = int(query.data.split("_")[-1])
    if target_id in OWNER_ID:
        await query.answer("لا يمكن حذف المالك.", show_alert=True)
        return
    db.remove_admin(target_id)
    db.add_log(user.id, "حذف أدمن", str(target_id), "تم الحذف")
    await query.answer("تم الحذف ✅")
    await admin_admins_callback(update, context)

async def list_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    admins = db.get_all_admins()
    if not admins:
        text = "لا يوجد أدمن."
    else:
        text = "<b>👤 قائمة الأدمن:</b>\n\n"
        for a in admins:
            text += f"• {a['user_id']} (أضيف بواسطة: {a['added_by']})\n"
    await edit_message_safely(
        query,
        text,
        reply_markup=get_back_button_with_callback(),
        parse_mode=ParseMode.HTML,
    )

async def admin_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    if not has_permission(user.id, "can_view_stats") and not is_owner(user.id):
        await query.answer("⛔ ليس لديك صلاحية.", show_alert=True)
        return
    await query.answer()
    stats = db.get_stats()
    text = (
        "<b>📊 الإحصائيات العامة</b>\n\n"
        f"👥 المستخدمين: {stats['users']}\n"
        f"👥 المجموعات: {stats['groups']}\n"
        f"🟢 المجموعات النشطة: {stats['active_groups']}\n"
        f"📝 الردود النشطة: {stats['replies']}\n"
        f"📢 القنوات الإجبارية: {stats['forced_channels']}\n"
    )
    await edit_message_safely(
        query,
        text,
        reply_markup=get_back_button_with_callback(),
        parse_mode=ParseMode.HTML,
    )

async def admin_broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    if not has_permission(user.id, "can_broadcast") and not is_owner(user.id):
        await query.answer("⛔ ليس لديك صلاحية.", show_alert=True)
        return
    await query.answer()
    buttons = [
        [StyledButton.create("📨 نشر للجميع (خاص)", callback_data="broadcast_users", style="primary")],
        [StyledButton.create("📢 نشر للمجموعات", callback_data="broadcast_groups", style="primary")],
        [StyledButton.create("📢 نشر لمجموعة محددة", callback_data="broadcast_specific_group", style="primary")],
        [StyledButton.create("رجوع", callback_data="admin_panel", style="secondary")],
    ]
    await edit_message_safely(
        query,
        "<b>📨 لوحة النشر</b>\nاختر وجهة النشر:",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.HTML,
    )

async def broadcast_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["action"] = "broadcast_users"
    context.user_data["previous_menu"] = "admin_broadcast"
    await edit_message_safely(
        query,
        "<b>✏️ نشر للجميع (خاص)</b>\n\n"
        "أرسل الرسالة التي تريد نشرها لجميع المستخدمين.\n"
        "يمكنك استخدام HTML.\n\n"
        "لإلغاء العملية اضغط /cancel.",
        reply_markup=get_back_button_with_callback(),
        parse_mode=ParseMode.HTML,
    )

async def broadcast_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["action"] = "broadcast_groups"
    context.user_data["previous_menu"] = "admin_broadcast"
    await edit_message_safely(
        query,
        "<b>✏️ نشر للمجموعات</b>\n\n"
        "أرسل الرسالة التي تريد نشرها في جميع المجموعات النشطة.\n"
        "يمكنك استخدام HTML.\n\n"
        "لإلغاء العملية اضغط /cancel.",
        reply_markup=get_back_button_with_callback(),
        parse_mode=ParseMode.HTML,
    )

async def broadcast_specific_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    groups = db.get_active_groups()
    if not groups:
        await edit_message_safely(
            query,
            "لا توجد مجموعات نشطة.",
            reply_markup=get_back_button_with_callback(),
        )
        return
    buttons = []
    for g in groups[:30]:
        buttons.append([
            InlineKeyboardButton(
                text=f"📢 {g.get('chat_title', 'مجموعة')}",
                callback_data=f"broadcast_to_group_{g['chat_id']}"
            )
        ])
    if len(groups) > 30:
        buttons.append([InlineKeyboardButton("... المزيد", callback_data="dummy", style="primary")])
    buttons.append([
        StyledButton.create("رجوع", callback_data="admin_broadcast", style="secondary")
    ])
    await edit_message_safely(
        query,
        "اختر المجموعة التي تريد النشر فيها:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )

async def broadcast_to_group_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = int(query.data.split("_")[-1])
    context.user_data["broadcast_target_group"] = chat_id
    context.user_data["action"] = "broadcast_specific_group_msg"
    context.user_data["previous_menu"] = "admin_broadcast"
    await edit_message_safely(
        query,
        f"<b>✏️ نشر لمجموعة محددة</b>\n\n"
        f"أرسل الرسالة التي تريد نشرها في المجموعة (ID: {chat_id}).\n"
        "يمكنك استخدام HTML.\n\n"
        "لإلغاء العملية اضغط /cancel.",
        reply_markup=get_back_button_with_callback(),
        parse_mode=ParseMode.HTML,
    )

async def show_admin_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    text = (
        "<b>⚙️ الإعدادات العامة</b>\n\n"
        "يمكنك تعديل الروابط والنصوص الأساسية.\n"
        "التعديل هنا يغير الإعدادات العامة للبوت.\n\n"
        f"📢 القناة: {db.get_setting('channel_link', CHANNEL_LINK)}\n"
        f"👥 المجموعة: {db.get_setting('group_link', GROUP_LINK)}\n"
        f"🛡️ الدعم: {db.get_setting('support_link', SUPPORT_LINK)}\n"
        f"👨‍💻 المطور: {db.get_setting('developer_link', DEVELOPER_LINK)}\n"
        f"🖼️ صورة الترحيب: {db.get_setting('welcome_image', WELCOME_IMAGE_URL)}\n"
    )
    buttons = [
        [StyledButton.create("تعديل رابط القناة", callback_data="set_channel_link", style="primary")],
        [StyledButton.create("تعديل رابط المجموعة", callback_data="set_group_link", style="primary")],
        [StyledButton.create("تعديل رابط الدعم", callback_data="set_support_link", style="primary")],
        [StyledButton.create("تعديل رابط المطور", callback_data="set_developer_link", style="primary")],
        [StyledButton.create("تعديل صورة الترحيب", callback_data="set_welcome_image", style="primary")],
        [StyledButton.create("تعديل نص الترحيب", callback_data="set_welcome_text", style="primary")],
        [StyledButton.create("رجوع", callback_data="admin_panel", style="secondary")],
    ]
    await edit_message_safely(
        query,
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.HTML,
    )

async def admin_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    if not has_permission(user.id, "can_manage_settings") and not is_owner(user.id):
        await query.answer("⛔ ليس لديك صلاحية.", show_alert=True)
        return
    await query.answer()
    await show_admin_settings(update, context)

async def set_setting_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, setting_key: str):
    query = update.callback_query
    await query.answer()
    context.user_data["action"] = f"set_{setting_key}"
    context.user_data["previous_menu"] = "admin_settings"
    await edit_message_safely(
        query,
        f"<b>✏️ تعديل {setting_key}</b>\n\n"
        f"أرسل القيمة الجديدة.\n"
        "لإلغاء العملية اضغط /cancel.",
        reply_markup=get_back_button_with_callback(),
        parse_mode=ParseMode.HTML,
    )

async def set_channel_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await set_setting_callback(update, context, "channel_link")
async def set_group_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await set_setting_callback(update, context, "group_link")
async def set_support_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await set_setting_callback(update, context, "support_link")
async def set_developer_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await set_setting_callback(update, context, "developer_link")
async def set_welcome_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await set_setting_callback(update, context, "welcome_image")
async def set_welcome_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await set_setting_callback(update, context, "welcome_text")

async def show_admin_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    backups = db.get_backups()
    text = "<b>💾 النسخ الاحتياطي</b>\n\n"
    if backups:
        for b in backups[:5]:
            text += f"• {b['backup_file']} ({b['size']} بايت) — {b['created_at']}\n"
    else:
        text += "لا توجد نسخ احتياطية.\n"
    buttons = [
        [StyledButton.create("📤 إنشاء نسخة احتياطية", callback_data="create_backup", style="success")],
        [StyledButton.create("📥 استعادة نسخة", callback_data="restore_backup_start", style="warning")],
        [StyledButton.create("رجوع", callback_data="admin_panel", style="secondary")],
    ]
    await edit_message_safely(
        query,
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.HTML,
    )

async def admin_backup_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    if not has_permission(user.id, "can_backup") and not is_owner(user.id):
        await query.answer("⛔ ليس لديك صلاحية.", show_alert=True)
        return
    await query.answer()
    await show_admin_backup(update, context)

async def create_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    if not has_permission(user.id, "can_backup") and not is_owner(user.id):
        await query.answer("⛔ ليس لديك صلاحية.", show_alert=True)
        return
    backup_file = f"backup_{int(time.time())}.db"
    success = db.create_backup(backup_file, user.id)
    if success:
        db.add_log(user.id, "إنشاء نسخة احتياطية", backup_file, "تم الإنشاء")
        await query.answer("✅ تم إنشاء النسخة الاحتياطية بنجاح.", show_alert=True)
    else:
        await query.answer("❌ فشل في إنشاء النسخة.", show_alert=True)
    await admin_backup_callback(update, context)

async def restore_backup_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    backups = db.get_backups()
    if not backups:
        await edit_message_safely(
            query,
            "لا توجد نسخ للاستعادة.",
            reply_markup=get_back_button_with_callback(),
        )
        return
    buttons = []
    for b in backups[:5]:
        buttons.append([
            InlineKeyboardButton(
                text=f"📥 {b['backup_file']}",
                callback_data=f"restore_backup_{b['id']}"
            )
        ])
    buttons.append([
        StyledButton.create("رجوع", callback_data="admin_backup", style="secondary")
    ])
    await edit_message_safely(
        query,
        "اختر النسخة للاستعادة:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )

async def restore_backup_exec(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    if not has_permission(user.id, "can_backup") and not is_owner(user.id):
        await query.answer("⛔ ليس لديك صلاحية.", show_alert=True)
        return
    backup_id = int(query.data.split("_")[-1])
    backups = db.get_backups()
    b = next((x for x in backups if x["id"] == backup_id), None)
    if b:
        success = db.restore_backup(b["backup_file"])
        if success:
            db.add_log(user.id, "استعادة نسخة احتياطية", b["backup_file"], "تمت الاستعادة")
            await query.answer("✅ تم استعادة النسخة بنجاح.", show_alert=True)
        else:
            await query.answer("❌ فشل في الاستعادة.", show_alert=True)
    else:
        await query.answer("النسخة غير موجودة.", show_alert=True)
    await admin_backup_callback(update, context)

async def admin_logs_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    if not has_permission(user.id, "can_view_stats") and not is_owner(user.id):
        await query.answer("⛔ ليس لديك صلاحية.", show_alert=True)
        return
    await query.answer()
    logs = db.get_logs(limit=20)
    text = "<b>📜 سجل العمليات (آخر 20)</b>\n\n"
    if logs:
        for log in logs:
            text += f"• {log['timestamp']} | {log['user_id']} | {log['action']}\n"
    else:
        text += "لا توجد سجلات."
    await edit_message_safely(
        query,
        text,
        reply_markup=get_back_button_with_callback(),
        parse_mode=ParseMode.HTML,
    )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global keyword_reply_map, file_keyword_map
    user = update.effective_user
    if not user:
        return

    document = update.message.document
    if not document or not document.file_name.endswith('.txt'):
        formatted, _ = format_blockquote("❌ يرجى إرسال ملف نصي بصيغة .txt فقط.", ParseMode.HTML)
        await update.message.reply_text(formatted, parse_mode=ParseMode.HTML)
        return

    action = context.user_data.get("action")

    if action == "add_reply_input":
        try:
            file = await context.bot.get_file(document.file_id)
            file_path = f"temp_{int(time.time())}.txt"
            await file.download_to_drive(file_path)

            with open(file_path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]

            os.remove(file_path)

            if not lines:
                formatted, _ = format_blockquote("❌ الملف فارغ. يرجى إرسال ملف يحتوي على كلمات.", ParseMode.HTML)
                await update.message.reply_text(formatted, parse_mode=ParseMode.HTML)
                return

            if not os.path.exists(KEYWORDS_DIR):
                os.makedirs(KEYWORDS_DIR)

            original_name = document.file_name
            target_path = os.path.join(KEYWORDS_DIR, original_name)
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(lines))

            reply_key = os.path.splitext(original_name)[0]
            for kw in lines:
                kw_lower = kw.lower()
                if kw_lower:
                    file_keyword_map[kw_lower] = reply_key

            context.user_data["reply_keywords"] = lines
            context.user_data["reply_filename"] = reply_key

            context.user_data["action"] = "add_reply_type"
            context.user_data["previous_menu"] = "admin_replies"

            formatted, _ = format_blockquote(
                f"✅ تم استلام الملف وقراءة {len(lines)} كلمة.\n"
                "الآن اختر نوع الرد:\n"
                "أرسل:\n"
                "• <code>text</code> لنص\n"
                "• <code>photo</code> لصورة\n"
                "• <code>video</code> لفيديو\n"
                "• <code>audio</code> لصوت\n"
                "• <code>document</code> لملف\n\n"
                "مثال: text",
                ParseMode.HTML
            )
            await update.message.reply_text(formatted, reply_markup=get_back_button_with_callback(), parse_mode=ParseMode.HTML)

        except Exception as e:
            logger.error(f"خطأ في معالجة الملف: {e}")
            formatted, _ = format_blockquote(f"❌ حدث خطأ أثناء معالجة الملف: {e}", ParseMode.HTML)
            await update.message.reply_text(formatted, parse_mode=ParseMode.HTML)
        return

    if not is_owner(user.id):
        formatted, _ = format_blockquote("⛔ هذا الأمر للمالك فقط.", ParseMode.HTML)
        await update.message.reply_text(formatted, parse_mode=ParseMode.HTML)
        return

    try:
        file = await context.bot.get_file(document.file_id)
        file_path = f"temp_{int(time.time())}.txt"
        await file.download_to_drive(file_path)

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if '|' in content:
            new_map = load_keywords_from_file(file_path)
            if not new_map:
                formatted, _ = format_blockquote("❌ الملف فارغ أو غير صحيح. تأكد من التنسيق:\nكلمة1, كلمة2 | الرد", ParseMode.HTML)
                await update.message.reply_text(formatted, parse_mode=ParseMode.HTML)
                os.remove(file_path)
                return
            keyword_reply_map.update(new_map)
            count = len(new_map)
            save_keywords_to_file(keyword_reply_map)
            formatted, _ = format_blockquote(f"✅ تم تحديث الكلمات بنجاح. ({count} كلمة مفتاحية من الملف)", ParseMode.HTML)
            await update.message.reply_text(formatted, parse_mode=ParseMode.HTML)
            db.add_log(user.id, "تحديث الكلمات من ملف", document.file_name, f"{count} كلمة")
        else:
            lines = [line.strip() for line in content.splitlines() if line.strip()]
            if not lines:
                formatted, _ = format_blockquote("❌ الملف فارغ.", ParseMode.HTML)
                await update.message.reply_text(formatted, parse_mode=ParseMode.HTML)
                os.remove(file_path)
                return
            reply_key = os.path.splitext(document.file_name)[0]
            new_entries = {}
            for kw in lines:
                kw_lower = kw.lower()
                if kw_lower:
                    new_entries[kw_lower] = reply_key
            if os.path.exists(KEYWORDS_DIR):
                target_path = os.path.join(KEYWORDS_DIR, document.file_name)
                try:
                    with open(target_path, 'w', encoding='utf-8') as f:
                        f.write("\n".join(lines))
                    file_keyword_map.update(new_entries)
                    count = len(new_entries)
                    formatted, _ = format_blockquote(
                        f"✅ تم ربط الكلمات بالملف «{reply_key}» بنجاح.\n"
                        f"عدد الكلمات: {count}\n"
                        f"تم حفظ الملف في: {target_path}",
                        ParseMode.HTML
                    )
                    await update.message.reply_text(formatted, parse_mode=ParseMode.HTML)
                    db.add_log(user.id, "ربط كلمات من ملف", document.file_name, f"{count} كلمة -> {reply_key}")
                except Exception as e:
                    formatted, _ = format_blockquote(f"❌ فشل حفظ الملف: {e}", ParseMode.HTML)
                    await update.message.reply_text(formatted, parse_mode=ParseMode.HTML)
            else:
                formatted, _ = format_blockquote(
                    f"❌ المجلد {KEYWORDS_DIR} غير موجود. يرجى إنشاؤه أولاً.",
                    ParseMode.HTML
                )
                await update.message.reply_text(formatted, parse_mode=ParseMode.HTML)

        os.remove(file_path)

    except Exception as e:
        logger.error(f"خطأ في معالجة الملف: {e}")
        formatted, _ = format_blockquote(f"❌ حدث خطأ: {e}", ParseMode.HTML)
        await update.message.reply_text(formatted, parse_mode=ParseMode.HTML)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global keyword_reply_map, file_keyword_map
    user = update.effective_user
    if not user:
        return

    if not update.message:
        return

    text = update.message.text
    if not text:
        return

    if update.message.chat.type == "private":
        if not await check_forced_subscription(update, context):
            return

    action = context.user_data.get("action")

    if action == "add_forced_channel" and update.message:
        text = update.message.text.strip()
        try:
            if text.startswith("-100"):
                channel_id = int(text)
            elif text.startswith("@"):
                bot = context.bot
                try:
                    chat = await bot.get_chat(text)
                    channel_id = chat.id
                except Exception as e:
                    formatted, _ = format_blockquote(f"❌ تعذر العثور على القناة: {e}", ParseMode.HTML)
                    await update.message.reply_text(formatted, parse_mode=ParseMode.HTML)
                    context.user_data.pop("action", None)
                    return
            else:
                channel_id = int(text)
        except ValueError:
            formatted, _ = format_blockquote("❌ المعرف غير صحيح. أرسل ID رقمي أو معرف القناة @username.", ParseMode.HTML)
            await update.message.reply_text(formatted, parse_mode=ParseMode.HTML)
            return
        bot = context.bot
        try:
            chat = await bot.get_chat(channel_id)
            title = chat.title or "بدون عنوان"
            username = chat.username or ""
        except Exception as e:
            formatted, _ = format_blockquote(f"❌ لا يمكن الوصول للقناة: {e}", ParseMode.HTML)
            await update.message.reply_text(formatted, parse_mode=ParseMode.HTML)
            context.user_data.pop("action", None)
            return
        success = db.add_forced_channel(channel_id, username, title, user.id)
        if success:
            db.add_log(user.id, "إضافة قناة إجبارية", str(channel_id), f"القناة: {title}")
            formatted, _ = format_blockquote(f"✅ تمت إضافة القناة {title} بنجاح.", ParseMode.HTML)
            await update.message.reply_text(formatted, parse_mode=ParseMode.HTML)
        else:
            formatted, _ = format_blockquote("❌ فشل الإضافة (قد تكون موجودة).", ParseMode.HTML)
            await update.message.reply_text(formatted, parse_mode=ParseMode.HTML)
        context.user_data.pop("action", None)
        return

    if action == "add_reply_input" and update.message:
        keyword = update.message.text.strip()
        if not keyword:
            formatted, _ = format_blockquote("❌ الرجاء إدخال كلمة صالحة.", ParseMode.HTML)
            await update.message.reply_text(formatted, parse_mode=ParseMode.HTML)
            return
        context.user_data["reply_keywords"] = [keyword.lower()]
        context.user_data["action"] = "add_reply_type"
        context.user_data["previous_menu"] = "admin_replies"
        formatted, _ = format_blockquote(
            "✏️ اختر نوع الرد:\n"
            "أرسل:\n"
            "• <code>text</code> لنص\n"
            "• <code>photo</code> لصورة\n"
            "• <code>video</code> لفيديو\n"
            "• <code>audio</code> لصوت\n"
            "• <code>document</code> لملف\n\n"
            "مثال: text",
            ParseMode.HTML
        )
        await update.message.reply_text(formatted, reply_markup=get_back_button_with_callback(), parse_mode=ParseMode.HTML)
        return

    if action == "add_reply_type" and update.message:
        reply_type = update.message.text.strip().lower()
        if reply_type not in ["text", "photo", "video", "audio", "document"]:
            formatted, _ = format_blockquote("❌ نوع غير صحيح. اختر من القائمة.", ParseMode.HTML)
            await update.message.reply_text(formatted, parse_mode=ParseMode.HTML)
            return
        context.user_data["reply_type"] = reply_type
        context.user_data["action"] = "add_reply_content"
        formatted, _ = format_blockquote(
            "✏️ أرسل محتوى الرد:\n"
            "• للنص: أرسل النص\n"
            "• للصورة/الفيديو/الصوت/الملف: أرسل الملف أو معرف الملف أو رابط.\n\n"
            "يمكنك إضافة كابتشن بعد إرسال الملف.",
            ParseMode.HTML
        )
        await update.message.reply_text(formatted, reply_markup=get_back_button_with_callback(), parse_mode=ParseMode.HTML)
        return

    if action == "add_reply_content" and update.message:
        reply_type = context.user_data.get("reply_type", "text")
        content = update.message.text or ""
        caption = ""
        if update.message.photo:
            content = update.message.photo[-1].file_id
            caption = update.message.caption or ""
            reply_type = "photo"
        elif update.message.video:
            content = update.message.video.file_id
            caption = update.message.caption or ""
            reply_type = "video"
        elif update.message.audio:
            content = update.message.audio.file_id
            caption = update.message.caption or ""
            reply_type = "audio"
        elif update.message.document:
            content = update.message.document.file_id
            caption = update.message.caption or ""
            reply_type = "document"
        else:
            content = update.message.text or ""
            caption = ""
        if not content:
            formatted, _ = format_blockquote("❌ لم يتم إرسال محتوى صالح.", ParseMode.HTML)
            await update.message.reply_text(formatted, parse_mode=ParseMode.HTML)
            return

        keywords = context.user_data.get("reply_keywords", [])
        if not keywords:
            formatted, _ = format_blockquote("❌ لا توجد كلمات مفتاحية محفوظة.", ParseMode.HTML)
            await update.message.reply_text(formatted, parse_mode=ParseMode.HTML)
            context.user_data.pop("action", None)
            return

        success = db.add_reply_bulk(keywords, reply_type, content, caption, "HTML", user.id)
        if success:
            db.add_log(user.id, "إضافة رد تلقائي (مجموعة)", ", ".join(keywords), f"النوع: {reply_type}")
            formatted, _ = format_blockquote(f"✅ تم إضافة الرد لـ {len(keywords)} كلمة بنجاح.", ParseMode.HTML)
            await update.message.reply_text(formatted, parse_mode=ParseMode.HTML)
        else:
            formatted, _ = format_blockquote("❌ فشل في إضافة الرد.", ParseMode.HTML)
            await update.message.reply_text(formatted, parse_mode=ParseMode.HTML)

        context.user_data.pop("action", None)
        context.user_data.pop("reply_keywords", None)
        context.user_data.pop("reply_type", None)
        context.user_data.pop("reply_filename", None)
        return

    if action == "edit_reply_keyword" and update.message:
        keyword = update.message.text.strip()
        if keyword.lower() != "نفس":
            reply_id = context.user_data.get("edit_reply_id")
            if reply_id:
                db.update_reply(reply_id, {"keyword": keyword.lower()})
        context.user_data["action"] = "edit_reply_type"
        formatted, _ = format_blockquote(
            "✏️ أرسل النوع الجديد (text, photo, video, audio, document) أو 'نفس' للإبقاء.",
            ParseMode.HTML
        )
        await update.message.reply_text(formatted, reply_markup=get_back_button_with_callback(), parse_mode=ParseMode.HTML)
        return

    if action == "edit_reply_type" and update.message:
        reply_type = update.message.text.strip().lower()
        if reply_type != "نفس" and reply_type not in ["text", "photo", "video", "audio", "document"]:
            formatted, _ = format_blockquote("❌ نوع غير صحيح.", ParseMode.HTML)
            await update.message.reply_text(formatted, parse_mode=ParseMode.HTML)
            return
        reply_id = context.user_data.get("edit_reply_id")
        if reply_id and reply_type != "نفس":
            db.update_reply(reply_id, {"reply_type": reply_type})
        context.user_data["action"] = "edit_reply_content"
        formatted, _ = format_blockquote(
            "✏️ أرسل المحتوى الجديد أو 'نفس' للإبقاء.\n"
            "للنص: أرسل النص.\n"
            "للملفات: أرسل الملف.",
            ParseMode.HTML
        )
        await update.message.reply_text(formatted, reply_markup=get_back_button_with_callback(), parse_mode=ParseMode.HTML)
        return

    if action == "edit_reply_content" and update.message:
        content = update.message.text or ""
        caption = ""
        if update.message.photo:
            content = update.message.photo[-1].file_id
            caption = update.message.caption or ""
        elif update.message.video:
            content = update.message.video.file_id
            caption = update.message.caption or ""
        elif update.message.audio:
            content = update.message.audio.file_id
            caption = update.message.caption or ""
        elif update.message.document:
            content = update.message.document.file_id
            caption = update.message.caption or ""
        reply_id = context.user_data.get("edit_reply_id")
        if reply_id and content != "نفس":
            db.update_reply(reply_id, {"reply_content": content, "caption": caption})
        db.add_log(user.id, "تعديل رد", str(reply_id), "تم التعديل")
        formatted, _ = format_blockquote("✅ تم تعديل الرد بنجاح.", ParseMode.HTML)
        await update.message.reply_text(formatted, parse_mode=ParseMode.HTML)
        context.user_data.pop("action", None)
        context.user_data.pop("edit_reply_id", None)
        return

    if action == "broadcast_users" and update.message:
        msg_text = update.message.text or update.message.caption or ""
        if not msg_text:
            formatted, _ = format_blockquote("❌ الرسالة فارغة.", ParseMode.HTML)
            await update.message.reply_text(formatted, parse_mode=ParseMode.HTML)
            return
        with db._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users WHERE is_bot = 0")
            users = cursor.fetchall()
        count = 0
        bot = context.bot
        for u in users:
            try:
                formatted_msg, _ = format_blockquote(msg_text, ParseMode.HTML)
                await bot.send_message(chat_id=u[0], text=formatted_msg, parse_mode=ParseMode.HTML)
                count += 1
                await asyncio.sleep(0.05)
            except Exception as e:
                logger.error(f"فشل في إرسال النشر للمستخدم {u[0]}: {e}")
        db.add_log(user.id, "نشر للجميع", "all_users", f"تم الإرسال لـ {count} مستخدم")
        formatted, _ = format_blockquote(f"✅ تم إرسال النشر لـ {count} مستخدم.", ParseMode.HTML)
        await update.message.reply_text(formatted, parse_mode=ParseMode.HTML)
        context.user_data.pop("action", None)
        return

    if action == "broadcast_groups" and update.message:
        msg_text = update.message.text or update.message.caption or ""
        if not msg_text:
            formatted, _ = format_blockquote("❌ الرسالة فارغة.", ParseMode.HTML)
            await update.message.reply_text(formatted, parse_mode=ParseMode.HTML)
            return
        groups = db.get_active_groups()
        count = 0
        bot = context.bot
        for g in groups:
            try:
                formatted_msg, _ = format_blockquote(msg_text, ParseMode.HTML)
                await bot.send_message(chat_id=g["chat_id"], text=formatted_msg, parse_mode=ParseMode.HTML)
                count += 1
                await asyncio.sleep(0.05)
            except Exception as e:
                logger.error(f"فشل النشر للمجموعة {g['chat_id']}: {e}")
        db.add_log(user.id, "نشر للمجموعات", "all_groups", f"تم الإرسال لـ {count} مجموعة")
        formatted, _ = format_blockquote(f"✅ تم إرسال النشر لـ {count} مجموعة.", ParseMode.HTML)
        await update.message.reply_text(formatted, parse_mode=ParseMode.HTML)
        context.user_data.pop("action", None)
        return

    if action == "broadcast_specific_group_msg" and update.message:
        msg_text = update.message.text or update.message.caption or ""
        if not msg_text:
            formatted, _ = format_blockquote("❌ الرسالة فارغة.", ParseMode.HTML)
            await update.message.reply_text(formatted, parse_mode=ParseMode.HTML)
            return
        chat_id = context.user_data.get("broadcast_target_group")
        if not chat_id:
            formatted, _ = format_blockquote("❌ لم يتم تحديد مجموعة.", ParseMode.HTML)
            await update.message.reply_text(formatted, parse_mode=ParseMode.HTML)
            return
        bot = context.bot
        try:
            formatted_msg, _ = format_blockquote(msg_text, ParseMode.HTML)
            await bot.send_message(chat_id=chat_id, text=formatted_msg, parse_mode=ParseMode.HTML)
            db.add_log(user.id, "نشر لمجموعة محددة", str(chat_id), "تم الإرسال")
            formatted, _ = format_blockquote("✅ تم إرسال الرسالة.", ParseMode.HTML)
            await update.message.reply_text(formatted, parse_mode=ParseMode.HTML)
        except Exception as e:
            formatted, _ = format_blockquote(f"❌ فشل الإرسال: {e}", ParseMode.HTML)
            await update.message.reply_text(formatted, parse_mode=ParseMode.HTML)
        context.user_data.pop("action", None)
        context.user_data.pop("broadcast_target_group", None)
        return

    if action and action.startswith("set_"):
        setting_key = action.replace("set_", "")
        value = update.message.text.strip()
        if value:
            db.set_setting(setting_key, value)
            formatted, _ = format_blockquote(f"✅ تم تحديث {setting_key}.", ParseMode.HTML)
            await update.message.reply_text(formatted, parse_mode=ParseMode.HTML)
        else:
            formatted, _ = format_blockquote("❌ القيمة فارغة.", ParseMode.HTML)
            await update.message.reply_text(formatted, parse_mode=ParseMode.HTML)
        context.user_data.pop("action", None)
        return

    if action == "add_admin_id" and update.message:
        try:
            admin_id = int(update.message.text.strip())
        except ValueError:
            formatted, _ = format_blockquote("❌ المعرف غير صحيح. أرسل رقم ID فقط.", ParseMode.HTML)
            await update.message.reply_text(formatted, parse_mode=ParseMode.HTML)
            return
        if admin_id in OWNER_ID:
            formatted, _ = format_blockquote("❌ هذا هو المالك بالفعل.", ParseMode.HTML)
            await update.message.reply_text(formatted, parse_mode=ParseMode.HTML)
            return
        success = db.add_admin(admin_id, user.id, {
            "can_manage_replies": False,
            "can_manage_groups": False,
            "can_manage_admins": False,
            "can_broadcast": False,
            "can_view_stats": False,
            "can_manage_settings": False,
            "can_backup": False,
        })
        if success:
            db.add_log(user.id, "إضافة أدمن", str(admin_id), "تمت الإضافة")
            formatted, _ = format_blockquote("✅ تم إضافة الأدمن. يمكنك تعديل صلاحياته من لوحة الأدمن.", ParseMode.HTML)
            await update.message.reply_text(formatted, parse_mode=ParseMode.HTML)
        else:
            formatted, _ = format_blockquote("❌ فشل الإضافة.", ParseMode.HTML)
            await update.message.reply_text(formatted, parse_mode=ParseMode.HTML)
        context.user_data.pop("action", None)
        return

    keyword = text.strip().lower()
    keyword_reply_map = load_keywords_from_file()
    file_keyword_map = load_all_keyword_files()

    if keyword in keyword_reply_map:
        reply_content = keyword_reply_map[keyword]
        formatted_reply, _ = format_blockquote(reply_content, ParseMode.HTML)
        await update.message.reply_text(
            text=formatted_reply,
            parse_mode=ParseMode.HTML,
            reply_to_message_id=update.message.message_id
        )
        return

    if keyword in file_keyword_map:
        file_key = file_keyword_map[keyword]
        reply = db.get_reply_by_keyword(file_key)
        if reply:
            bot = context.bot
            chat_id = update.message.chat_id
            reply_type = reply["reply_type"]
            content = reply["reply_content"]
            caption = reply.get("caption", "")
            parse_mode = reply.get("parse_mode", "HTML")
            try:
                if reply_type == "text":
                    formatted_text, _ = format_blockquote(content, parse_mode)
                    await bot.send_message(
                        chat_id=chat_id,
                        text=formatted_text,
                        parse_mode=parse_mode,
                        reply_to_message_id=update.message.message_id,
                    )
                elif reply_type == "photo":
                    formatted_caption, _ = format_blockquote(caption, parse_mode)
                    await bot.send_photo(
                        chat_id=chat_id,
                        photo=content,
                        caption=formatted_caption,
                        parse_mode=parse_mode,
                        reply_to_message_id=update.message.message_id,
                    )
                elif reply_type == "video":
                    formatted_caption, _ = format_blockquote(caption, parse_mode)
                    await bot.send_video(
                        chat_id=chat_id,
                        video=content,
                        caption=formatted_caption,
                        parse_mode=parse_mode,
                        reply_to_message_id=update.message.message_id,
                    )
                elif reply_type == "audio":
                    formatted_caption, _ = format_blockquote(caption, parse_mode)
                    await bot.send_audio(
                        chat_id=chat_id,
                        audio=content,
                        caption=formatted_caption,
                        parse_mode=parse_mode,
                        reply_to_message_id=update.message.message_id,
                    )
                elif reply_type == "document":
                    formatted_caption, _ = format_blockquote(caption, parse_mode)
                    await bot.send_document(
                        chat_id=chat_id,
                        document=content,
                        caption=formatted_caption,
                        parse_mode=parse_mode,
                        reply_to_message_id=update.message.message_id,
                    )
                db.increment_reply_usage(reply["id"])
            except Exception as e:
                logger.error(f"خطأ في إرسال رد تلقائي: {e}")
        else:
            formatted_reply, _ = format_blockquote(file_key, ParseMode.HTML)
            await update.message.reply_text(
                text=formatted_reply,
                parse_mode=ParseMode.HTML,
                reply_to_message_id=update.message.message_id
            )
        return

    reply = db.get_reply_by_keyword(keyword)
    if reply:
        bot = context.bot
        chat_id = update.message.chat_id
        reply_type = reply["reply_type"]
        content = reply["reply_content"]
        caption = reply.get("caption", "")
        parse_mode = reply.get("parse_mode", "HTML")
        try:
            if reply_type == "text":
                formatted_text, _ = format_blockquote(content, parse_mode)
                await bot.send_message(
                    chat_id=chat_id,
                    text=formatted_text,
                    parse_mode=parse_mode,
                    reply_to_message_id=update.message.message_id,
                )
            elif reply_type == "photo":
                formatted_caption, _ = format_blockquote(caption, parse_mode)
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=content,
                    caption=formatted_caption,
                    parse_mode=parse_mode,
                    reply_to_message_id=update.message.message_id,
                )
            elif reply_type == "video":
                formatted_caption, _ = format_blockquote(caption, parse_mode)
                await bot.send_video(
                    chat_id=chat_id,
                    video=content,
                    caption=formatted_caption,
                    parse_mode=parse_mode,
                    reply_to_message_id=update.message.message_id,
                )
            elif reply_type == "audio":
                formatted_caption, _ = format_blockquote(caption, parse_mode)
                await bot.send_audio(
                    chat_id=chat_id,
                    audio=content,
                    caption=formatted_caption,
                    parse_mode=parse_mode,
                    reply_to_message_id=update.message.message_id,
                )
            elif reply_type == "document":
                formatted_caption, _ = format_blockquote(caption, parse_mode)
                await bot.send_document(
                    chat_id=chat_id,
                    document=content,
                    caption=formatted_caption,
                    parse_mode=parse_mode,
                    reply_to_message_id=update.message.message_id,
                )
            db.increment_reply_usage(reply["id"])
        except Exception as e:
            logger.error(f"خطأ في إرسال رد تلقائي: {e}")

async def add_to_group_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    if not is_admin_user(user.id):
        await query.answer("⛔ ليس لديك صلاحية.", show_alert=True)
        return
    await query.answer()
    bot_username = (await context.bot.get_me()).username
    invite_link = f"https://t.me/{bot_username}?startgroup=add"
    text = (
        "<b>🤖 إضافة البوت إلى مجموعة جديدة</b>\n\n"
        "اضغط على الرابط أدناه لدعوة البوت إلى مجموعة جديدة.\n"
        "بعد إضافة البوت، ارفعه مشرفاً مع جميع الصلاحيات.\n"
        "سيتم تفعيل البوت تلقائياً وستظهر رسالة الترحيب.\n\n"
        f'<a href="{invite_link}">اضغط هنا لدعوة البوت</a>\n\n'
        f"أو استخدم معرف البوت: @{bot_username}\n\n"
        "بعد إضافة البوت كأدمن، سيعمل تلقائياً."
    )
    await edit_message_safely(
        query,
        text,
        reply_markup=InlineKeyboardMarkup([
            [StyledButton.create("رابط الدعوة", url=invite_link, style="primary")],
            [StyledButton.create("✅ تمت الإضافة (تحقق)", callback_data="check_added_group", style="success")],
            [StyledButton.create("رجوع", callback_data="main_menu", style="danger")],
        ]),
        parse_mode=ParseMode.HTML,
    )

async def check_added_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        await edit_message_safely(
            query,
            "📢 تم التفعيل التلقائي\n\n"
            "عندما تضيف البوت إلى مجموعة وترفعه مشرفاً، سيرسل رسالة ترحيب تلقائياً.\n"
            "إذا لم تظهر الرسالة، تأكد من أن البوت مشرف في المجموعة.\n\n"
            "يمكنك أيضاً إعادة تشغيل البوت أو استخدام /start.",
            reply_markup=get_back_button_with_callback(),
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        logger.error(f"خطأ في check_added_group: {e}")

async def my_chat_member_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    my_chat_member = update.my_chat_member
    if not my_chat_member:
        return
    chat = my_chat_member.chat
    new_status = my_chat_member.new_chat_member.status
    if new_status in ["administrator", "member"]:
        if chat.type in ["group", "supergroup"]:
            db.add_group(chat)
            try:
                bot_member = await context.bot.get_chat_member(chat.id, context.bot.id)
                if bot_member.status == "administrator":
                    db.update_group_active(chat.id, True)
                    await send_welcome_message(update, context, chat.id)
                    db.add_log(context.bot.id, "تمت إضافة البوت لمجموعة", str(chat.id), chat.title)
                    for owner in OWNER_ID:
                        try:
                            await context.bot.send_message(
                                chat_id=owner,
                                text=f"✅ تم إضافة البوت إلى مجموعة {chat.title} (ID: {chat.id}) بنجاح."
                            )
                        except Exception as e:
                            logger.error(f"فشل إرسال إشعار للمالك {owner}: {e}")
                else:
                    db.update_group_active(chat.id, False)
                    try:
                        await context.bot.send_message(
                            chat.id,
                            "⚠️ يرجى رفع البوت مشرفاً لتفعيل جميع الميزات."
                        )
                    except Exception:
                        pass
            except Exception as e:
                logger.error(f"خطأ في معالجة عضوية البوت: {e}")

async def send_welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    bot = context.bot
    try:
        welcome_image = db.get_setting("welcome_image", WELCOME_IMAGE_URL)
        verse = get_group_verse()
        welcome_text = db.get_setting("welcome_text", DEFAULT_WELCOME_MESSAGE)
        message_text = (
            f"{welcome_text}\n\n"
            f"📖 {verse}\n\n"
            "🔹 <b>البوت جاهز للعمل</b> 🔹\n"
            "يمكنك استخدام الأوامر والردود التلقائية."
        )
        buttons = [
            [
                StyledButton.create("المطور", url=DEVELOPER_LINK, style="primary"),
                StyledButton.create("القناة", url=CHANNEL_LINK, style="primary"),
            ],
            [
                StyledButton.create("المجموعة", url=GROUP_LINK, style="primary"),
                StyledButton.create("الدعم", url=SUPPORT_LINK, style="primary"),
            ],
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        formatted_msg, _ = format_blockquote(message_text, ParseMode.HTML)
        await bot.send_photo(
            chat_id=chat_id,
            photo=welcome_image,
            caption=formatted_msg,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        logger.error(f"خطأ في إرسال رسالة الترحيب: {e}")
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=f"مرحباً! البوت جاهز.\n\n{format_verse()}",
            )
        except Exception:
            pass

async def check_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    await query.answer()
    if await check_forced_subscription(update, context):
        await edit_message_safely(
            query,
            "✅ تم التحقق من الاشتراك\nيمكنك الآن استخدام البوت.",
            reply_markup=get_main_keyboard(),
            parse_mode=ParseMode.HTML,
        )

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data:
        context.user_data.clear()
        formatted, _ = format_blockquote("❌ تم إلغاء العملية.", ParseMode.HTML)
        await update.message.reply_text(formatted, parse_mode=ParseMode.HTML)
    else:
        formatted, _ = format_blockquote("لا توجد عملية نشطة.", ParseMode.HTML)
        await update.message.reply_text(formatted, parse_mode=ParseMode.HTML)

async def back_to_previous(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    previous_menu = context.user_data.get("previous_menu", "admin_panel")
    context.user_data.pop("action", None)
    if previous_menu == "admin_replies":
        page = context.user_data.get("page", 0)
        await show_admin_replies(update, context, page)
    elif previous_menu == "admin_groups":
        page = context.user_data.get("page", 0)
        await show_admin_groups(update, context, page)
    elif previous_menu == "admin_admins":
        await show_admin_admins(update, context)
    elif previous_menu == "admin_settings":
        await show_admin_settings(update, context)
    elif previous_menu == "admin_backup":
        await show_admin_backup(update, context)
    elif previous_menu == "admin_broadcast":
        await admin_broadcast_callback(update, context)
    elif previous_menu == "forced_subscription":
        await show_forced_subscription(update, context)
    elif previous_menu == "main_menu":
        await show_main_menu(update, context)
    else:
        await show_admin_panel(update, context)

def main():
    global app
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    app = application

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(CommandHandler("reload", reload_command))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(
        filters.PHOTO | filters.VIDEO | filters.AUDIO,
        handle_text
    ))
    application.add_handler(MessageHandler(
        filters.Document.ALL,
        handle_document
    ))

    application.add_handler(ChatMemberHandler(my_chat_member_handler, ChatMemberHandler.CHAT_MEMBER))

    application.add_handler(CallbackQueryHandler(main_menu_callback, pattern="^main_menu$"))
    application.add_handler(CallbackQueryHandler(forced_subscription_callback, pattern="^forced_subscription$"))
    application.add_handler(CallbackQueryHandler(add_forced_channel_callback, pattern="^add_forced_channel$"))
    application.add_handler(CallbackQueryHandler(remove_forced_channel_callback, pattern="^remove_forced_channel$"))
    application.add_handler(CallbackQueryHandler(delete_forced_channel_callback, pattern="^del_forced_ch_"))
    application.add_handler(CallbackQueryHandler(toggle_forced_channel_callback, pattern="^toggle_forced_channel$"))
    application.add_handler(CallbackQueryHandler(toggle_forced_channel_exec, pattern="^toggle_forced_"))
    application.add_handler(CallbackQueryHandler(admin_panel_callback, pattern="^admin_panel$"))
    application.add_handler(CallbackQueryHandler(admin_replies_callback, pattern="^admin_replies(_\\d+)?$"))
    application.add_handler(CallbackQueryHandler(add_reply_start, pattern="^add_reply_start$"))
    application.add_handler(CallbackQueryHandler(edit_reply_start, pattern="^edit_reply_\\d+_\\d+$"))
    application.add_handler(CallbackQueryHandler(delete_reply_start, pattern="^delete_reply_\\d+_\\d+$"))
    application.add_handler(CallbackQueryHandler(toggle_reply_start, pattern="^toggle_reply_\\d+_\\d+$"))
    application.add_handler(CallbackQueryHandler(admin_groups_callback, pattern="^admin_groups(_\\d+)?$"))
    application.add_handler(CallbackQueryHandler(toggle_group_exec, pattern="^toggle_group_\\d+_\\d+$"))
    application.add_handler(CallbackQueryHandler(delete_group_exec, pattern="^delete_group_\\d+_\\d+$"))
    application.add_handler(CallbackQueryHandler(list_groups, pattern="^list_groups$"))
    application.add_handler(CallbackQueryHandler(admin_admins_callback, pattern="^admin_admins$"))
    application.add_handler(CallbackQueryHandler(add_admin_start, pattern="^add_admin_start$"))
    application.add_handler(CallbackQueryHandler(remove_admin_start, pattern="^remove_admin_start$"))
    application.add_handler(CallbackQueryHandler(remove_admin_exec, pattern="^remove_admin_"))
    application.add_handler(CallbackQueryHandler(list_admins, pattern="^list_admins$"))
    application.add_handler(CallbackQueryHandler(admin_stats_callback, pattern="^admin_stats$"))
    application.add_handler(CallbackQueryHandler(admin_broadcast_callback, pattern="^admin_broadcast$"))
    application.add_handler(CallbackQueryHandler(broadcast_users, pattern="^broadcast_users$"))
    application.add_handler(CallbackQueryHandler(broadcast_groups, pattern="^broadcast_groups$"))
    application.add_handler(CallbackQueryHandler(broadcast_specific_group, pattern="^broadcast_specific_group$"))
    application.add_handler(CallbackQueryHandler(broadcast_to_group_selected, pattern="^broadcast_to_group_"))
    application.add_handler(CallbackQueryHandler(admin_settings_callback, pattern="^admin_settings$"))
    application.add_handler(CallbackQueryHandler(set_channel_link, pattern="^set_channel_link$"))
    application.add_handler(CallbackQueryHandler(set_group_link, pattern="^set_group_link$"))
    application.add_handler(CallbackQueryHandler(set_support_link, pattern="^set_support_link$"))
    application.add_handler(CallbackQueryHandler(set_developer_link, pattern="^set_developer_link$"))
    application.add_handler(CallbackQueryHandler(set_welcome_image, pattern="^set_welcome_image$"))
    application.add_handler(CallbackQueryHandler(set_welcome_text, pattern="^set_welcome_text$"))
    application.add_handler(CallbackQueryHandler(admin_backup_callback, pattern="^admin_backup$"))
    application.add_handler(CallbackQueryHandler(create_backup, pattern="^create_backup$"))
    application.add_handler(CallbackQueryHandler(restore_backup_start, pattern="^restore_backup_start$"))
    application.add_handler(CallbackQueryHandler(restore_backup_exec, pattern="^restore_backup_"))
    application.add_handler(CallbackQueryHandler(admin_logs_callback, pattern="^admin_logs$"))
    application.add_handler(CallbackQueryHandler(add_to_group_callback, pattern="^add_to_group$"))
    application.add_handler(CallbackQueryHandler(check_added_group, pattern="^check_added_group$"))
    application.add_handler(CallbackQueryHandler(check_subscription_callback, pattern="^check_subscription$"))
    application.add_handler(CallbackQueryHandler(back_to_previous, pattern="^back_to_previous$"))

    print("✅ البوت يعمل...")
    application.run_polling()

if __name__ == "__main__":
    main()