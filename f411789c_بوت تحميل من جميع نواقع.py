# Colored by 𝙰𝙿𝙾 𝙵𝙰𝚁𝙴𝚂 (@i_mmx)
import asyncio
import aiohttp
import aiosqlite
import json
import logging
import os
import re
import signal
import time
import urllib.parse
from datetime import datetime
from io import BytesIO
from typing import Optional, Dict, Any, List, Tuple
from collections import defaultdict
import ssl

import yt_dlp
import instaloader
from bs4 import BeautifulSoup
from user_agent import generate_user_agent
import requests

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.constants import ParseMode

TOKEN = "8319377737:AAE0-C_6xyS8GmmaTKukvgSG_nSdu5zeqKQ"
DEVELOPER_IDS = [6891530912]

DEFAULT_MESSAGES = {
    "welcome": "🌟 <b>مرحباً بك في بوت التحميل الشامل</b>\n\n📥 يمكنك تحميل المحتوى من جميع منصات التواصل الاجتماعي\n🔹 بدون حقوق أو علامات مائية\n\n👇 اختر المنصة التي تريد التحميل منها:",
    "subscribe": "⚠️ <b>يجب الاشتراك في القنوات التالية لاستخدام البوت</b>\n\n{channels_list}\n\nبعد الاشتراك، اضغط زر التحقق.",
    "subscribe_success": "✅ تم تفعيل البوت بنجاح!",
    "platform_prompt": "📥 أرسل رابط {platform_name}:",
    "loading": "⏳ جاري معالجة الرابط...",
    "download_success": "✅ تم التحميل بأعلى دقة",
    "download_fail": "❌ تعذر تحميل المحتوى من {platform_name}.",
    "error": "❌ حدث خطأ أثناء التحميل.",
    "platform_disabled": "⚠️ هذه المنصة معطلة حالياً.",
    "maintenance": "🛠️ البوت في وضع الصيانة حالياً. يرجى المحاولة لاحقاً.",
}

DEFAULT_PLATFORMS = [
    {"id": "youtube", "name": "يوتيوب", "icon": "🎬", "enabled": True, "visible": True, "order": 1},
    {"id": "facebook", "name": "فيسبوك", "icon": "📘", "enabled": True, "visible": True, "order": 2},
    {"id": "instagram", "name": "انستجرام", "icon": "📸", "enabled": True, "visible": True, "order": 3},
    {"id": "pinterest", "name": "بينتيريست", "icon": "📌", "enabled": True, "visible": True, "order": 4},
    {"id": "tiktok", "name": "تيك توك", "icon": "🎵", "enabled": True, "visible": True, "order": 5},
    {"id": "snapchat", "name": "سناب شات", "icon": "👻", "enabled": True, "visible": True, "order": 6},
]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

DB_PATH = "bot_data.db"

class Database:
    def __init__(self):
        self.conn = None

    async def init(self):
        self.conn = await aiosqlite.connect(DB_PATH)
        await self._create_tables()
        await self._init_defaults()

    async def _create_tables(self):
        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                date_added TEXT,
                first_time INTEGER DEFAULT 1,
                banned INTEGER DEFAULT 0,
                last_activity TEXT
            )
        ''')
        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY,
                permissions TEXT,
                added_by INTEGER,
                date_added TEXT
            )
        ''')
        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                title TEXT,
                enabled INTEGER DEFAULT 1,
                order_num INTEGER DEFAULT 0,
                added_by INTEGER,
                date_added TEXT
            )
        ''')
        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS platforms (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                icon TEXT,
                enabled INTEGER DEFAULT 1,
                visible INTEGER DEFAULT 1,
                order_num INTEGER DEFAULT 0
            )
        ''')
        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                platform TEXT,
                downloads INTEGER DEFAULT 0,
                errors INTEGER DEFAULT 0,
                requests INTEGER DEFAULT 0,
                UNIQUE(date, platform)
            )
        ''')
        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                user_id INTEGER,
                action TEXT,
                details TEXT
            )
        ''')
        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS user_states (
                user_id INTEGER PRIMARY KEY,
                state TEXT,
                data TEXT,
                updated_at TEXT
            )
        ''')
        await self.conn.commit()

    async def _init_defaults(self):
        for p in DEFAULT_PLATFORMS:
            await self.conn.execute(
                "INSERT OR IGNORE INTO platforms (id, name, icon, enabled, visible, order_num) VALUES (?, ?, ?, ?, ?, ?)",
                (p["id"], p["name"], p["icon"], 1 if p["enabled"] else 0, 1 if p["visible"] else 0, p["order"])
            )
        for key, value in DEFAULT_MESSAGES.items():
            await self.conn.execute(
                "INSERT OR IGNORE INTO messages (key, value) VALUES (?, ?)",
                (key, value)
            )
        settings = {
            "maintenance": "0",
            "maintenance_message": "🛠️ البوت في وضع الصيانة حالياً. يرجى المحاولة لاحقاً.",
            "rate_limit_seconds": "5",
            "max_requests_per_minute": "30",
            "welcome_image": "https://telegra.ph/file/your-image-link.jpg",
            "subscribe_image": "https://telegra.ph/file/your-image-link.jpg",
        }
        for k, v in settings.items():
            await self.conn.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (k, v)
            )
        for dev_id in DEVELOPER_IDS:
            await self.conn.execute(
                "INSERT OR IGNORE INTO admins (user_id, permissions, added_by, date_added) VALUES (?, ?, ?, ?)",
                (dev_id, json.dumps(["all"]), 0, datetime.now().isoformat())
            )
        await self.conn.commit()

    async def add_user(self, user: dict):
        await self.conn.execute(
            "INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, date_added, last_activity) VALUES (?, ?, ?, ?, COALESCE((SELECT date_added FROM users WHERE user_id=?), datetime('now')), datetime('now'))",
            (user['id'], user.get('username'), user.get('first_name'), user.get('last_name'), user['id'])
        )
        await self.conn.commit()

    async def get_user(self, user_id: int):
        cursor = await self.conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return await cursor.fetchone()

    async def get_all_users(self, banned=False):
        cursor = await self.conn.execute("SELECT user_id FROM users WHERE banned = ?", (1 if banned else 0,))
        rows = await cursor.fetchall()
        return [r[0] for r in rows]

    async def get_user_count(self, banned=False):
        cursor = await self.conn.execute("SELECT COUNT(*) FROM users WHERE banned = ?", (1 if banned else 0,))
        row = await cursor.fetchone()
        return row[0] if row else 0

    async def ban_user(self, user_id: int):
        await self.conn.execute("UPDATE users SET banned = 1 WHERE user_id = ?", (user_id,))
        await self.conn.commit()

    async def unban_user(self, user_id: int):
        await self.conn.execute("UPDATE users SET banned = 0 WHERE user_id = ?", (user_id,))
        await self.conn.commit()

    async def is_banned(self, user_id: int):
        cursor = await self.conn.execute("SELECT banned FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        return row and row[0] == 1

    async def update_user_activity(self, user_id: int):
        await self.conn.execute("UPDATE users SET last_activity = datetime('now') WHERE user_id = ?", (user_id,))
        await self.conn.commit()

    async def get_admins(self):
        cursor = await self.conn.execute("SELECT user_id, permissions FROM admins")
        rows = await cursor.fetchall()
        return [{"user_id": r[0], "permissions": json.loads(r[1])} for r in rows]

    async def add_admin(self, user_id: int, permissions: list, added_by: int):
        await self.conn.execute(
            "INSERT OR REPLACE INTO admins (user_id, permissions, added_by, date_added) VALUES (?, ?, ?, datetime('now'))",
            (user_id, json.dumps(permissions), added_by)
        )
        await self.conn.commit()

    async def remove_admin(self, user_id: int):
        await self.conn.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
        await self.conn.commit()

    async def is_admin(self, user_id: int):
        cursor = await self.conn.execute("SELECT user_id FROM admins WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        return row is not None

    async def get_admin_permissions(self, user_id: int):
        cursor = await self.conn.execute("SELECT permissions FROM admins WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        if row:
            return json.loads(row[0])
        return []

    async def get_channels(self, enabled_only=False):
        query = "SELECT id, username, title, enabled, order_num FROM channels ORDER BY order_num"
        if enabled_only:
            query = "SELECT id, username, title, enabled, order_num FROM channels WHERE enabled = 1 ORDER BY order_num"
        cursor = await self.conn.execute(query)
        rows = await cursor.fetchall()
        return [{"id": r[0], "username": r[1], "title": r[2], "enabled": r[3], "order": r[4]} for r in rows]

    async def add_channel(self, username: str, title: str, order: int, added_by: int):
        await self.conn.execute(
            "INSERT INTO channels (username, title, order_num, added_by, date_added) VALUES (?, ?, ?, ?, datetime('now'))",
            (username, title, order, added_by)
        )
        await self.conn.commit()

    async def update_channel(self, channel_id: int, username: str = None, title: str = None, enabled: bool = None, order: int = None):
        updates = []
        params = []
        if username is not None:
            updates.append("username = ?")
            params.append(username)
        if title is not None:
            updates.append("title = ?")
            params.append(title)
        if enabled is not None:
            updates.append("enabled = ?")
            params.append(1 if enabled else 0)
        if order is not None:
            updates.append("order_num = ?")
            params.append(order)
        if updates:
            params.append(channel_id)
            await self.conn.execute(f"UPDATE channels SET {', '.join(updates)} WHERE id = ?", params)
            await self.conn.commit()

    async def delete_channel(self, channel_id: int):
        await self.conn.execute("DELETE FROM channels WHERE id = ?", (channel_id,))
        await self.conn.commit()

    async def get_platforms(self, visible_only=False, enabled_only=False):
        query = "SELECT id, name, icon, enabled, visible, order_num FROM platforms"
        conditions = []
        params = []
        if visible_only:
            conditions.append("visible = 1")
        if enabled_only:
            conditions.append("enabled = 1")
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY order_num"
        cursor = await self.conn.execute(query, params)
        rows = await cursor.fetchall()
        return [{"id": r[0], "name": r[1], "icon": r[2], "enabled": bool(r[3]), "visible": bool(r[4]), "order": r[5]} for r in rows]

    async def update_platform(self, platform_id: str, **kwargs):
        updates = []
        params = []
        for key, value in kwargs.items():
            if key in ["name", "icon"]:
                updates.append(f"{key} = ?")
                params.append(value)
            elif key in ["enabled", "visible"]:
                updates.append(f"{key} = ?")
                params.append(1 if value else 0)
            elif key == "order":
                updates.append("order_num = ?")
                params.append(value)
        if updates:
            params.append(platform_id)
            await self.conn.execute(f"UPDATE platforms SET {', '.join(updates)} WHERE id = ?", params)
            await self.conn.commit()

    async def get_setting(self, key: str, default: str = None):
        cursor = await self.conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = await cursor.fetchone()
        return row[0] if row else default

    async def set_setting(self, key: str, value: str):
        await self.conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        await self.conn.commit()

    async def get_message(self, key: str, default: str = None):
        cursor = await self.conn.execute("SELECT value FROM messages WHERE key = ?", (key,))
        row = await cursor.fetchone()
        return row[0] if row else default

    async def set_message(self, key: str, value: str):
        await self.conn.execute("INSERT OR REPLACE INTO messages (key, value) VALUES (?, ?)", (key, value))
        await self.conn.commit()

    async def increment_download(self, platform: str):
        today = datetime.now().strftime("%Y-%m-%d")
        await self.conn.execute(
            "INSERT OR REPLACE INTO stats (date, platform, downloads, errors, requests) VALUES (?, ?, COALESCE((SELECT downloads FROM stats WHERE date=? AND platform=?), 0) + 1, COALESCE((SELECT errors FROM stats WHERE date=? AND platform=?), 0), COALESCE((SELECT requests FROM stats WHERE date=? AND platform=?), 0))",
            (today, platform, today, platform, today, platform, today, platform)
        )
        await self.conn.commit()

    async def increment_error(self, platform: str):
        today = datetime.now().strftime("%Y-%m-%d")
        await self.conn.execute(
            "INSERT OR REPLACE INTO stats (date, platform, downloads, errors, requests) VALUES (?, ?, COALESCE((SELECT downloads FROM stats WHERE date=? AND platform=?), 0), COALESCE((SELECT errors FROM stats WHERE date=? AND platform=?), 0) + 1, COALESCE((SELECT requests FROM stats WHERE date=? AND platform=?), 0))",
            (today, platform, today, platform, today, platform, today, platform)
        )
        await self.conn.commit()

    async def increment_request(self):
        today = datetime.now().strftime("%Y-%m-%d")
        await self.conn.execute(
            "INSERT OR REPLACE INTO stats (date, platform, downloads, errors, requests) VALUES (?, 'total', COALESCE((SELECT downloads FROM stats WHERE date=? AND platform='total'), 0), COALESCE((SELECT errors FROM stats WHERE date=? AND platform='total'), 0), COALESCE((SELECT requests FROM stats WHERE date=? AND platform='total'), 0) + 1)",
            (today, today, today, today)
        )
        await self.conn.commit()

    async def get_stats(self):
        cursor = await self.conn.execute("SELECT platform, SUM(downloads) FROM stats GROUP BY platform")
        rows = await cursor.fetchall()
        downloads = {r[0]: r[1] for r in rows}
        cursor = await self.conn.execute("SELECT SUM(errors) FROM stats")
        total_errors = (await cursor.fetchone())[0] or 0
        cursor = await self.conn.execute("SELECT SUM(requests) FROM stats WHERE platform = 'total'")
        total_requests = (await cursor.fetchone())[0] or 0
        return {"downloads": downloads, "errors": total_errors, "requests": total_requests}

    async def add_log(self, user_id: int, action: str, details: str = None):
        await self.conn.execute(
            "INSERT INTO logs (timestamp, user_id, action, details) VALUES (datetime('now'), ?, ?, ?)",
            (user_id, action, details)
        )
        await self.conn.commit()

    async def get_logs(self, limit=100):
        cursor = await self.conn.execute("SELECT timestamp, user_id, action, details FROM logs ORDER BY id DESC LIMIT ?", (limit,))
        rows = await cursor.fetchall()
        return [{"timestamp": r[0], "user_id": r[1], "action": r[2], "details": r[3]} for r in rows]

    async def set_user_state(self, user_id: int, state: str, data: dict = None):
        await self.conn.execute(
            "INSERT OR REPLACE INTO user_states (user_id, state, data, updated_at) VALUES (?, ?, ?, datetime('now'))",
            (user_id, state, json.dumps(data) if data else "{}")
        )
        await self.conn.commit()

    async def get_user_state(self, user_id: int):
        cursor = await self.conn.execute("SELECT state, data FROM user_states WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        if row:
            return {"state": row[0], "data": json.loads(row[1])}
        return None

    async def clear_user_state(self, user_id: int):
        await self.conn.execute("DELETE FROM user_states WHERE user_id = ?", (user_id,))
        await self.conn.commit()

    async def backup(self):
        tables = ["users", "admins", "channels", "platforms", "settings", "messages", "stats", "logs", "user_states"]
        backup = {}
        for table in tables:
            cursor = await self.conn.execute(f"SELECT * FROM {table}")
            rows = await cursor.fetchall()
            cols = [description[0] for description in cursor.description]
            backup[table] = [dict(zip(cols, row)) for row in rows]
        return backup

    async def restore(self, backup: dict):
        for table in backup.keys():
            await self.conn.execute(f"DELETE FROM {table}")
            if backup[table]:
                cols = list(backup[table][0].keys())
                placeholders = ','.join(['?' for _ in cols])
                for row in backup[table]:
                    values = [row.get(c) for c in cols]
                    await self.conn.execute(f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders})", values)
        await self.conn.commit()

class Downloader:
    def __init__(self, db: Database, session: aiohttp.ClientSession):
        self.db = db
        self.session = session
        self.instaloader = instaloader.Instaloader()
        self.ytdl_opts = {
            'format': 'best',
            'quiet': True,
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'socket_timeout': 15,
            'no_check_certificate': True,
            'extractor_args': {
                'youtube': {
                    'skip': ['hls', 'dash'],
                    'player_client': ['android'],
                }
            }
        }
        os.makedirs('downloads', exist_ok=True)

    async def _download_bytes(self, url: str, ssl_verify: bool = True) -> bytes:
        connector = None
        if not ssl_verify:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            connector = aiohttp.TCPConnector(ssl=ssl_context)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(url) as resp:
                resp.raise_for_status()
                return await resp.read()

    async def download_tiktok(self, url: str) -> Tuple[Optional[bytes], Optional[dict]]:
        try:
            # First attempt with tiksave.io
            data = {'q': url, 'lang': 'ar'}
            headers = {
                'authority': 'tiksave.io',
                'accept': '*/*',
                'accept-language': 'en-US,en;q=0.9,ar-IQ;q=0.8,ar;q=0.7',
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'origin': 'https://tiksave.io',
                'referer': 'https://tiksave.io/ar',
                'user-agent': generate_user_agent(),
                'x-requested-with': 'XMLHttpRequest',
            }
            async with self.session.post("https://tiksave.io/api/ajaxSearch", data=data, headers=headers) as resp:
                if resp.status != 200:
                    raise ValueError(f"HTTP {resp.status}")
                json_data = await resp.json()
                html_content = json_data.get("data")
                if not html_content:
                    raise ValueError("No data")
                soup = BeautifulSoup(html_content, 'html.parser')
                video_tag = soup.find('video')
                video_url = video_tag.get('data-src') if video_tag else None
                if video_url:
                    content = await self._download_bytes(video_url)
                    metadata = {
                        "filename": "tiktok_video.mp4",
                        "size": len(content),
                        "quality": "HD",
                        "duration": None,
                        "platform": "TikTok",
                        "publisher": None,
                        "views": None,
                        "likes": None,
                        "date": None,
                    }
                    return content, metadata
                # Try to find video in script tags
                scripts = soup.find_all('script')
                for script in scripts:
                    if script.string and 'video_url' in script.string:
                        match = re.search(r'video_url\s*:\s*"([^"]+)"', script.string)
                        if match:
                            video_url = match.group(1).replace('\\/', '/')
                            content = await self._download_bytes(video_url)
                            metadata = {
                                "filename": "tiktok_video.mp4",
                                "size": len(content),
                                "quality": "HD",
                                "duration": None,
                                "platform": "TikTok",
                                "publisher": None,
                                "views": None,
                                "likes": None,
                                "date": None,
                            }
                            return content, metadata
            # Second attempt with www.tiksave.io
            headers['authority'] = 'www.tiksave.io'
            headers['origin'] = 'https://www.tiksave.io'
            headers['referer'] = 'https://www.tiksave.io/ar'
            async with self.session.post("https://www.tiksave.io/api/ajaxSearch", data=data, headers=headers) as resp:
                if resp.status == 200:
                    json_data = await resp.json()
                    html_content = json_data.get("data")
                    if html_content:
                        soup = BeautifulSoup(html_content, 'html.parser')
                        video_tag = soup.find('video')
                        video_url = video_tag.get('data-src') if video_tag else None
                        if video_url:
                            content = await self._download_bytes(video_url)
                            metadata = {
                                "filename": "tiktok_video.mp4",
                                "size": len(content),
                                "quality": "HD",
                                "duration": None,
                                "platform": "TikTok",
                                "publisher": None,
                                "views": None,
                                "likes": None,
                                "date": None,
                            }
                            return content, metadata
            return None, None
        except Exception as e:
            logger.error(f"TikTok error: {e}")
            return None, None

    async def download_pinterest(self, url: str) -> Tuple[Optional[bytes], Optional[dict]]:
        try:
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                img_api = "https://api.pinterestdl.io/api/image"
                headers_img = {
                    'authority': 'api.pinterestdl.io',
                    'accept': '*/*',
                    'origin': 'https://pinterestdl.io',
                    'referer': 'https://pinterestdl.io/',
                    'user-agent': generate_user_agent(),
                }
                async with session.get(img_api, params={'url': url}, headers=headers_img) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        img_url = data.get('imageUrl')
                        if img_url:
                            content = await self._download_bytes(img_url, ssl_verify=False)
                            metadata = {
                                "filename": "pinterest_image.jpg",
                                "size": len(content),
                                "quality": "HD",
                                "duration": None,
                                "platform": "Pinterest",
                                "publisher": None,
                                "views": None,
                                "likes": None,
                                "date": None,
                            }
                            return content, metadata
            # Video fallback (using original session)
            video_api = "https://everyweb.net/wp-json/aio-dl/video-data/"
            token = "0d8a45597e998fd21242b74089fac11b70dd1499a2ba25ad3b6100238811eafd"
            hash_val = "aHR0cHM6Ly9waW4uaXQvNmp0RVZPRkdz1024YWlvLWRs"
            data_form = {'url': url, 'token': token, 'hash': hash_val}
            headers_video = {
                'authority': 'everyweb.net',
                'content-type': 'application/x-www-form-urlencoded',
                'origin': 'https://everyweb.net',
                'referer': 'https://everyweb.net/pinterest/',
                'user-agent': generate_user_agent(),
            }
            async with self.session.post(video_api, data=data_form, headers=headers_video) as resp:
                if resp.status == 200:
                    jd = await resp.json()
                    medias = jd.get('medias') or []
                    if medias:
                        candidate = None
                        for m in medias:
                            if m.get('quality') in ('hd', '720', '1080', '4k'):
                                candidate = m
                                break
                        if not candidate:
                            candidate = medias[0]
                        video_url = candidate.get('url')
                        if video_url:
                            content = await self._download_bytes(video_url)
                            metadata = {
                                "filename": "pinterest_video.mp4",
                                "size": len(content),
                                "quality": candidate.get('quality', 'HD'),
                                "duration": None,
                                "platform": "Pinterest",
                                "publisher": None,
                                "views": None,
                                "likes": None,
                                "date": None,
                            }
                            return content, metadata
            return None, None
        except Exception as e:
            logger.error(f"Pinterest error: {e}")
            return None, None

    async def download_facebook(self, url: str) -> Tuple[Optional[bytes], Optional[dict]]:
        try:
            data = {
                'k_exp': '1753825936',
                'k_token': '2ba09b483e6bd112275af34aa9fa4c2a9d53df34a934389b8086bcbffce0a515',
                'p': 'home',
                'q': url,
                'lang': 'ar',
                'v': 'v2',
                'w': '',
            }
            headers = {
                'authority': 'fbdownloader.to',
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'origin': 'https://fbdownloader.to',
                'referer': 'https://fbdownloader.to/ar',
                'user-agent': generate_user_agent(),
                'x-requested-with': 'XMLHttpRequest',
            }
            async with self.session.post("https://fbdownloader.to/api/ajaxSearch", data=data, headers=headers) as resp:
                json_data = await resp.json()
                if json_data.get('status') != 'ok':
                    raise ValueError("API status not ok")
                soup = BeautifulSoup(json_data['data'], 'html.parser')
                video_url = None
                for quality in ['720p (HD)', '360p (SD)']:
                    link = soup.find('a', {'title': f'Download {quality}'})
                    if link and 'href' in link.attrs:
                        video_url = link['href']
                        break
                if not video_url:
                    video_tag = soup.find('video')
                    if video_tag and 'src' in video_tag.attrs:
                        video_url = video_tag['src']
                if video_url:
                    content = await self._download_bytes(video_url)
                    metadata = {
                        "filename": "facebook_video.mp4",
                        "size": len(content),
                        "quality": "HD",
                        "duration": None,
                        "platform": "Facebook",
                        "publisher": None,
                        "views": None,
                        "likes": None,
                        "date": None,
                    }
                    return content, metadata
            return None, None
        except Exception as e:
            logger.error(f"Facebook error: {e}")
            return None, None

    async def download_instagram(self, url: str) -> Tuple[Optional[bytes], Optional[dict]]:
        try:
            ydl_opts = self.ytdl_opts.copy()
            ydl_opts['outtmpl'] = 'downloads/instagram_%(id)s.%(ext)s'
            def dl():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if 'entries' in info:
                        info = info['entries'][0]
                    # Check if it's a video by looking for formats with video codec
                    is_video = False
                    video_url = None
                    if 'formats' in info:
                        for f in info['formats']:
                            if f.get('vcodec') != 'none' and f.get('url'):
                                is_video = True
                                video_url = f['url']
                                break
                    if is_video and video_url:
                        # Download video using yt-dlp
                        ydl.download([url])
                        filename = ydl.prepare_filename(info)
                        with open(filename, 'rb') as f:
                            content = f.read()
                        os.remove(filename)
                        metadata = {
                            "filename": os.path.basename(filename),
                            "size": len(content),
                            "quality": info.get('format_note', 'HD'),
                            "duration": info.get('duration'),
                            "platform": "Instagram",
                            "publisher": info.get('uploader'),
                            "views": info.get('view_count'),
                            "likes": info.get('like_count'),
                            "date": info.get('upload_date'),
                        }
                        return content, metadata
                    else:
                        # It's an image, use the direct URL
                        img_url = info.get('url')
                        if not img_url:
                            img_url = info.get('thumbnails', [{}])[-1].get('url')
                        if img_url:
                            response = requests.get(img_url, timeout=20)
                            response.raise_for_status()
                            content = response.content
                            metadata = {
                                "filename": "instagram_image.jpg",
                                "size": len(content),
                                "quality": "HD",
                                "duration": None,
                                "platform": "Instagram",
                                "publisher": info.get('uploader'),
                                "views": None,
                                "likes": info.get('like_count'),
                                "date": info.get('upload_date'),
                            }
                            return content, metadata
                        else:
                            raise ValueError("No image URL found")
            return await asyncio.to_thread(dl)
        except Exception as e:
            logger.error(f"Instagram yt-dlp error: {e}")
            try:
                shortcode = re.search(r'/p/([^/]+)', url) or re.search(r'/reel/([^/]+)', url)
                if shortcode:
                    post = await asyncio.to_thread(
                        instaloader.Post.from_shortcode,
                        self.instaloader.context,
                        shortcode.group(1)
                    )
                    if post.is_video:
                        video_url = post.video_url
                        content = await self._download_bytes(video_url)
                        metadata = {
                            "filename": "instagram_video.mp4",
                            "size": len(content),
                            "quality": "HD",
                            "duration": post.video_duration,
                            "platform": "Instagram",
                            "publisher": post.owner_username,
                            "views": post.video_view_count,
                            "likes": post.likes,
                            "date": post.date_utc.isoformat(),
                        }
                        return content, metadata
                    else:
                        img_url = post.url
                        content = await self._download_bytes(img_url)
                        metadata = {
                            "filename": "instagram_image.jpg",
                            "size": len(content),
                            "quality": "HD",
                            "duration": None,
                            "platform": "Instagram",
                            "publisher": post.owner_username,
                            "views": None,
                            "likes": post.likes,
                            "date": post.date_utc.isoformat(),
                        }
                        return content, metadata
            except Exception as ee:
                logger.error(f"Instagram fallback error: {ee}")
            return None, None

    async def download_snapchat(self, url: str) -> Tuple[Optional[bytes], Optional[dict]]:
        try:
            # Try smart-loader first
            payload = {'file_name': url}
            headers = {
                'authority': 'samrt-loader.com',
                'accept': 'application/json',
                'content-type': 'application/json',
                'origin': 'https://samrt-loader.com',
                'referer': 'https://samrt-loader.com/ar/snapchat',
                'user-agent': generate_user_agent(),
            }
            async with self.session.post("https://samrt-loader.com/kydwon/api/addfile", json=payload, headers=headers) as resp:
                jd = await resp.json()
                if jd.get('success') and 'files' in jd:
                    video_url = None
                    for f in jd['files']:
                        if f.get('resolution_type') == 'mp4/hd' and f.get('file'):
                            video_url = f['file']
                            break
                    if not video_url:
                        for f in jd['files']:
                            if f.get('file'):
                                video_url = f['file']
                                break
                    if video_url:
                        content = await self._download_bytes(video_url)
                        if len(content) < 200000:  # less than 200KB likely not a real video
                            raise ValueError("Video too small")
                        metadata = {
                            "filename": "snapchat_video.mp4",
                            "size": len(content),
                            "quality": "HD",
                            "duration": None,
                            "platform": "Snapchat",
                            "publisher": None,
                            "views": None,
                            "likes": None,
                            "date": None,
                        }
                        return content, metadata
            # Fallback to snapinsta
            data = {'url': url, 'action': 'post'}
            headers2 = {
                'authority': 'snapinsta.app',
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'origin': 'https://snapinsta.app',
                'referer': 'https://snapinsta.app/',
                'user-agent': generate_user_agent(),
            }
            async with self.session.post("https://snapinsta.app/action.php", data=data, headers=headers2) as resp:
                json_data = await resp.json()
                if json_data.get('status') == 'success' and 'url' in json_data:
                    video_url = json_data['url']
                    content = await self._download_bytes(video_url)
                    if len(content) < 200000:
                        raise ValueError("Video too small")
                    metadata = {
                        "filename": "snapchat_video.mp4",
                        "size": len(content),
                        "quality": "HD",
                        "duration": None,
                        "platform": "Snapchat",
                        "publisher": None,
                        "views": None,
                        "likes": None,
                        "date": None,
                    }
                    return content, metadata
            return None, None
        except Exception as e:
            logger.error(f"Snapchat error: {e}")
            return None, None

    async def download_youtube(self, url: str) -> Tuple[Optional[bytes], Optional[dict]]:
        try:
            ydl_opts = self.ytdl_opts.copy()
            ydl_opts['outtmpl'] = 'downloads/youtube_%(id)s.%(ext)s'
            # Add cookies file if exists (optional)
            if os.path.exists('cookies.txt'):
                ydl_opts['cookiefile'] = 'cookies.txt'
            def dl():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    ydl.download([url])
                    filename = ydl.prepare_filename(info)
                    with open(filename, 'rb') as f:
                        content = f.read()
                    os.remove(filename)
                    metadata = {
                        "filename": os.path.basename(filename),
                        "size": len(content),
                        "quality": info.get('format_note', 'HD'),
                        "duration": info.get('duration'),
                        "platform": "YouTube",
                        "publisher": info.get('uploader'),
                        "views": info.get('view_count'),
                        "likes": info.get('like_count'),
                        "date": info.get('upload_date'),
                    }
                    return content, metadata
            return await asyncio.to_thread(dl)
        except Exception as e:
            logger.error(f"YouTube error: {e}")
            return None, None

class BotHandlers:
    def __init__(self, db: Database, downloader: Downloader):
        self.db = db
        self.downloader = downloader
        self.rate_limiter = defaultdict(list)

    async def _check_subscription_with_bot(self, user_id: int, bot) -> Tuple[bool, List[dict]]:
        channels = await self.db.get_channels(enabled_only=True)
        if not channels:
            return True, []
        not_subscribed = []
        for ch in channels:
            username = ch['username'].strip()
            if not username.startswith('@'):
                username = '@' + username
            try:
                member = await bot.get_chat_member(username, user_id)
                if member.status not in ['member', 'administrator', 'creator']:
                    not_subscribed.append(ch)
            except:
                not_subscribed.append(ch)
        return len(not_subscribed) == 0, not_subscribed

    async def _is_admin(self, user_id: int) -> bool:
        return await self.db.is_admin(user_id)

    async def _get_main_menu_keyboard(self, include_admin=False) -> InlineKeyboardMarkup:
        platforms = await self.db.get_platforms(visible_only=True, enabled_only=True)
        keyboard = []
        row = []
        for p in platforms:
            row.append(InlineKeyboardButton(f"{p['icon']} {p['name']}", callback_data=f"download_{p['id']}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        if include_admin:
            keyboard.append([InlineKeyboardButton("🔐 لوحة الأدمن", callback_data="admin_panel")])
        return InlineKeyboardMarkup(keyboard)

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        chat_id = update.effective_chat.id
        await self.db.add_user(user.to_dict())
        await self.db.update_user_activity(user.id)

        maintenance = await self.db.get_setting("maintenance", "0")
        if maintenance == "1":
            msg = await self.db.get_message("maintenance_message", DEFAULT_MESSAGES["maintenance"])
            await update.message.reply_text(f"<blockquote>{msg}</blockquote>", parse_mode=ParseMode.HTML)
            return

        subscribed, not_subscribed = await self._check_subscription_with_bot(user.id, context.bot)
        if not subscribed:
            channels = await self.db.get_channels(enabled_only=True)
            channels_list = "\n".join([f"📢 {ch['username']}" for ch in channels])
            sub_msg = await self.db.get_message("subscribe", DEFAULT_MESSAGES["subscribe"])
            sub_msg = sub_msg.format(channels_list=channels_list)
            keyboard = []
            for ch in channels:
                username = ch['username'].strip()
                if not username.startswith('@'):
                    username = '@' + username
                keyboard.append([InlineKeyboardButton(f"📢 {ch.get('title', username)}", url=f"https://t.me/{username[1:]}")])
            keyboard.append([InlineKeyboardButton("✅ اشتركت", callback_data="check_subscription")])
            image_url = await self.db.get_setting("subscribe_image", "https://telegra.ph/file/your-image-link.jpg")
            try:
                await update.message.reply_photo(photo=image_url, caption=f"<blockquote>{sub_msg}</blockquote>", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
            except:
                await update.message.reply_text(f"<blockquote>{sub_msg}</blockquote>", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
            return

        welcome_msg = await self.db.get_message("welcome", DEFAULT_MESSAGES["welcome"])
        keyboard = await self._get_main_menu_keyboard(include_admin=await self._is_admin(user.id))
        image_url = await self.db.get_setting("welcome_image", "https://telegra.ph/file/your-image-link.jpg")
        try:
            await update.message.reply_photo(photo=image_url, caption=f"<blockquote>{welcome_msg}</blockquote>", parse_mode=ParseMode.HTML, reply_markup=keyboard)
        except:
            await update.message.reply_text(f"<blockquote>{welcome_msg}</blockquote>", parse_mode=ParseMode.HTML, reply_markup=keyboard)

    async def check_subscription_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        chat_id = query.message.chat.id
        subscribed, _ = await self._check_subscription_with_bot(user_id, context.bot)
        if subscribed:
            sub_success = await self.db.get_message("subscribe_success", DEFAULT_MESSAGES["subscribe_success"])
            welcome_msg = await self.db.get_message("welcome", DEFAULT_MESSAGES["welcome"])
            keyboard = await self._get_main_menu_keyboard(include_admin=await self._is_admin(user_id))
            image_url = await self.db.get_setting("welcome_image", "https://telegra.ph/file/your-image-link.jpg")
            try:
                await query.edit_message_media(media=image_url, caption=f"<blockquote>{sub_success}\n\n{welcome_msg}</blockquote>", reply_markup=keyboard, parse_mode=ParseMode.HTML)
            except:
                await query.edit_message_text(f"<blockquote>{sub_success}\n\n{welcome_msg}</blockquote>", parse_mode=ParseMode.HTML, reply_markup=keyboard)
        else:
            await query.answer("❌ لم تشترك في جميع القنوات بعد.", show_alert=True)

    async def platform_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        chat_id = query.message.chat.id
        data = query.data
        platform_id = data.replace("download_", "")
        platforms = await self.db.get_platforms()
        platform = next((p for p in platforms if p['id'] == platform_id), None)
        if not platform:
            await query.answer("⚠️ المنصة غير موجودة.", show_alert=True)
            return
        if not platform['enabled']:
            await query.answer("⚠️ هذه المنصة معطلة حالياً.", show_alert=True)
            return
        await self.db.set_user_state(user_id, "waiting_url", {"platform": platform_id, "message_id": query.message.message_id})
        prompt = await self.db.get_message("platform_prompt", DEFAULT_MESSAGES["platform_prompt"])
        prompt = prompt.format(platform_name=platform['name'])
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]])
        await query.edit_message_text(f"<blockquote>{prompt}</blockquote>", parse_mode=ParseMode.HTML, reply_markup=keyboard)

    async def back_to_main_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        chat_id = query.message.chat.id
        await self.db.clear_user_state(user_id)
        welcome_msg = await self.db.get_message("welcome", DEFAULT_MESSAGES["welcome"])
        keyboard = await self._get_main_menu_keyboard(include_admin=await self._is_admin(user_id))
        image_url = await self.db.get_setting("welcome_image", "https://telegra.ph/file/your-image-link.jpg")
        try:
            await query.edit_message_media(media=image_url, caption=f"<blockquote>{welcome_msg}</blockquote>", reply_markup=keyboard, parse_mode=ParseMode.HTML)
        except:
            await query.edit_message_text(f"<blockquote>{welcome_msg}</blockquote>", parse_mode=ParseMode.HTML, reply_markup=keyboard)

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        chat_id = update.effective_chat.id
        text = update.message.text.strip()

        state = await self.db.get_user_state(user.id)
        if not state or state['state'] != 'waiting_url':
            return

        subscribed, _ = await self._check_subscription_with_bot(user.id, context.bot)
        if not subscribed:
            await update.message.reply_text("<blockquote>⚠️ يجب الاشتراك في القنوات أولاً.</blockquote>", parse_mode=ParseMode.HTML)
            return

        maintenance = await self.db.get_setting("maintenance", "0")
        if maintenance == "1":
            msg = await self.db.get_message("maintenance_message", DEFAULT_MESSAGES["maintenance"])
            await update.message.reply_text(f"<blockquote>{msg}</blockquote>", parse_mode=ParseMode.HTML)
            return

        if not text.startswith(('http://', 'https://')):
            await update.message.reply_text("<blockquote>⚠️ الرابط غير صحيح. يرجى إرسال رابط صحيح.</blockquote>", parse_mode=ParseMode.HTML)
            return

        try:
            await self._apply_rate_limit(user.id)
        except Exception as e:
            await update.message.reply_text(f"<blockquote>⚠️ {str(e)}</blockquote>", parse_mode=ParseMode.HTML)
            return

        platform_id = state['data']['platform']
        original_message_id = state['data']['message_id']

        try:
            await update.message.delete()
        except:
            pass

        loading_msg = await self.db.get_message("loading", DEFAULT_MESSAGES["loading"])
        await context.bot.edit_message_text(f"<blockquote>{loading_msg}</blockquote>", chat_id=chat_id, message_id=original_message_id, parse_mode=ParseMode.HTML)

        content, metadata = await self._download_content(platform_id, text)
        if content is None:
            await self.db.increment_error(platform_id)
            fail_msg = await self.db.get_message("download_fail", DEFAULT_MESSAGES["download_fail"])
            fail_msg = fail_msg.format(platform_name=platform_id.capitalize())
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]])
            await context.bot.edit_message_text(f"<blockquote>{fail_msg}</blockquote>", chat_id=chat_id, message_id=original_message_id, parse_mode=ParseMode.HTML, reply_markup=keyboard)
            await self.db.clear_user_state(user.id)
            return

        await self.db.increment_download(platform_id)

        caption = await self.db.get_message("download_success", DEFAULT_MESSAGES["download_success"])
        caption += "\n\n<blockquote>"
        if metadata:
            for key, value in metadata.items():
                if value:
                    caption += f"<b>{key.capitalize()}:</b> {value}\n"
        caption += "</blockquote>"

        if metadata and metadata.get('filename', '').lower().endswith(('.mp4', '.mov', '.avi')):
            await context.bot.send_video(chat_id, video=content, caption=caption, parse_mode=ParseMode.HTML)
        else:
            filename = metadata.get('filename', 'file.bin') if metadata else 'file.bin'
            await context.bot.send_document(chat_id, document=InputFile(BytesIO(content), filename=filename), caption=caption, parse_mode=ParseMode.HTML)

        await self.db.clear_user_state(user.id)
        welcome_msg = await self.db.get_message("welcome", DEFAULT_MESSAGES["welcome"])
        keyboard = await self._get_main_menu_keyboard(include_admin=await self._is_admin(user.id))
        image_url = await self.db.get_setting("welcome_image", "https://telegra.ph/file/your-image-link.jpg")
        try:
            await context.bot.edit_message_media(media=image_url, chat_id=chat_id, message_id=original_message_id, caption=f"<blockquote>{welcome_msg}</blockquote>", reply_markup=keyboard, parse_mode=ParseMode.HTML)
        except:
            await context.bot.edit_message_text(f"<blockquote>{welcome_msg}</blockquote>", chat_id=chat_id, message_id=original_message_id, parse_mode=ParseMode.HTML, reply_markup=keyboard)

    async def _download_content(self, platform_id: str, url: str) -> Tuple[Optional[bytes], Optional[dict]]:
        downloaders = {
            'tiktok': self.downloader.download_tiktok,
            'pinterest': self.downloader.download_pinterest,
            'facebook': self.downloader.download_facebook,
            'instagram': self.downloader.download_instagram,
            'snapchat': self.downloader.download_snapchat,
            'youtube': self.downloader.download_youtube,
        }
        if platform_id not in downloaders:
            return None, None
        try:
            return await downloaders[platform_id](url)
        except Exception as e:
            logger.error(f"Download error for {platform_id}: {e}")
            return None, None

    async def _apply_rate_limit(self, user_id: int):
        max_requests = int(await self.db.get_setting("max_requests_per_minute", "30"))
        now = time.time()
        timestamps = self.rate_limiter[user_id]
        timestamps = [t for t in timestamps if now - t < 60]
        if len(timestamps) >= max_requests:
            raise Exception("تجاوزت حد الطلبات المسموح به في الدقيقة. يرجى الانتظار.")
        timestamps.append(now)
        self.rate_limiter[user_id] = timestamps

    async def admin_panel_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        if not await self._is_admin(user_id):
            await query.answer("⛔ غير مصرح", show_alert=True)
            return
        keyboard = [
            [InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats")],
            [InlineKeyboardButton("👥 إدارة المستخدمين", callback_data="admin_users")],
            [InlineKeyboardButton("📢 الإذاعة", callback_data="admin_broadcast")],
            [InlineKeyboardButton("📋 المنصات", callback_data="admin_platforms")],
            [InlineKeyboardButton("📝 الرسائل", callback_data="admin_messages")],
            [InlineKeyboardButton("🔗 القنوات الإجبارية", callback_data="admin_channels")],
            [InlineKeyboardButton("👤 إدارة الأدمن", callback_data="admin_admins")],
            [InlineKeyboardButton("📜 السجلات", callback_data="admin_logs")],
            [InlineKeyboardButton("💾 النسخ الاحتياطي", callback_data="admin_backup")],
            [InlineKeyboardButton("🛠️ الصيانة", callback_data="admin_maintenance")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")],
        ]
        await query.edit_message_text("<blockquote>👑 <b>لوحة تحكم الأدمن</b></blockquote>", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))

    async def admin_stats_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        stats = await self.db.get_stats()
        total_users = await self.db.get_user_count()
        banned_users = await self.db.get_user_count(banned=True)
        text = f"<b>📊 الإحصائيات</b>\n\n"
        text += f"👥 المستخدمين: {total_users}\n"
        text += f"🚫 المحظورين: {banned_users}\n"
        text += f"📥 إجمالي التحميلات: {sum(stats['downloads'].values())}\n"
        text += f"❌ الأخطاء: {stats['errors']}\n"
        text += f"📩 الطلبات: {stats['requests']}\n\n"
        text += "<b>تحميلات كل منصة:</b>\n"
        for platform, count in stats['downloads'].items():
            text += f"• {platform}: {count}\n"
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]]
        await query.edit_message_text(f"<blockquote>{text}</blockquote>", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))

    async def admin_users_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        keyboard = [
            [InlineKeyboardButton("📋 قائمة المستخدمين", callback_data="admin_users_list")],
            [InlineKeyboardButton("🔨 حظر مستخدم", callback_data="admin_ban_user")],
            [InlineKeyboardButton("🔓 فك حظر مستخدم", callback_data="admin_unban_user")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")],
        ]
        await query.edit_message_text("<blockquote>👥 <b>إدارة المستخدمين</b></blockquote>", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))

    async def admin_ban_user_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        await self.db.set_user_state(user_id, "ban_user_wait", {})
        await query.edit_message_text("<blockquote>🔨 أرسل ايدي المستخدم الذي تريد حظره:</blockquote>", parse_mode=ParseMode.HTML)

    async def admin_unban_user_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        await self.db.set_user_state(user_id, "unban_user_wait", {})
        await query.edit_message_text("<blockquote>🔓 أرسل ايدي المستخدم الذي تريد فك حظره:</blockquote>", parse_mode=ParseMode.HTML)

    async def admin_users_list_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        users = await self.db.get_all_users()
        if users:
            text = "📋 <b>قائمة المستخدمين</b>\n\n"
            for uid in users[:50]:
                text += f"• {uid}\n"
            if len(users) > 50:
                text += f"\n... و {len(users)-50} آخرين"
        else:
            text = "لا يوجد مستخدمين."
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="admin_users")]]
        await query.edit_message_text(f"<blockquote>{text}</blockquote>", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))

    async def admin_broadcast_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        await self.db.set_user_state(user_id, "broadcast_wait", {})
        await query.edit_message_text("<blockquote>📢 أرسل الرسالة التي تريد إذاعتها (نص فقط):</blockquote>", parse_mode=ParseMode.HTML)

    async def admin_platforms_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        platforms = await self.db.get_platforms()
        keyboard = []
        for p in platforms:
            status = "✅" if p['enabled'] else "❌"
            keyboard.append([InlineKeyboardButton(f"{p['icon']} {p['name']} {status}", callback_data=f"admin_platform_toggle_{p['id']}")])
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")])
        await query.edit_message_text("<blockquote>📋 <b>إدارة المنصات</b>\nاضغط على زر المنصة لتفعيل/تعطيل.</blockquote>", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))

    async def admin_platform_toggle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        platform_id = query.data.replace("admin_platform_toggle_", "")
        platforms = await self.db.get_platforms()
        platform = next((p for p in platforms if p['id'] == platform_id), None)
        if platform:
            new_enabled = not platform['enabled']
            await self.db.update_platform(platform_id, enabled=new_enabled)
            await query.answer(f"تم {'تفعيل' if new_enabled else 'تعطيل'} المنصة")
            await self.admin_platforms_callback(update, context)

    async def admin_channels_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        channels = await self.db.get_channels()
        keyboard = []
        for ch in channels:
            status = "✅" if ch['enabled'] else "❌"
            keyboard.append([InlineKeyboardButton(f"{ch['username']} {status}", callback_data=f"admin_channel_toggle_{ch['id']}")])
        keyboard.append([InlineKeyboardButton("➕ إضافة قناة", callback_data="admin_channel_add")])
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")])
        await query.edit_message_text("<blockquote>🔗 <b>إدارة القنوات الإجبارية</b>\nاضغط على القناة لتفعيل/تعطيل.</blockquote>", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))

    async def admin_channel_toggle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        channel_id = int(query.data.replace("admin_channel_toggle_", ""))
        channels = await self.db.get_channels()
        ch = next((c for c in channels if c['id'] == channel_id), None)
        if ch:
            new_enabled = not ch['enabled']
            await self.db.update_channel(channel_id, enabled=new_enabled)
            await query.answer(f"تم {'تفعيل' if new_enabled else 'تعطيل'} القناة")
            await self.admin_channels_callback(update, context)

    async def admin_channel_add_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        await self.db.set_user_state(user_id, "add_channel_wait", {})
        await query.edit_message_text("<blockquote>➕ أرسل يوزر القناة في السطر الأول (بدون @) والعنوان في السطر الثاني:</blockquote>", parse_mode=ParseMode.HTML)

    async def admin_messages_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        cursor = await self.db.conn.execute("SELECT key FROM messages")
        rows = await cursor.fetchall()
        keyboard = []
        for row in rows:
            key = row[0]
            keyboard.append([InlineKeyboardButton(key, callback_data=f"admin_message_edit_{key}")])
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")])
        await query.edit_message_text("<blockquote>📝 <b>تعديل الرسائل</b>\nاختر الرسالة لتعديلها.</blockquote>", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))

    async def admin_message_edit_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        key = query.data.replace("admin_message_edit_", "")
        current = await self.db.get_message(key, "")
        user_id = query.from_user.id
        await self.db.set_user_state(user_id, "edit_message_wait", {"key": key})
        await query.edit_message_text(f"<blockquote>📝 تعديل الرسالة: <b>{key}</b>\n\nالحالي:\n{current}\n\nأرسل النص الجديد:</blockquote>", parse_mode=ParseMode.HTML)

    async def admin_admins_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        admins = await self.db.get_admins()
        keyboard = []
        for admin in admins:
            keyboard.append([InlineKeyboardButton(f"👤 {admin['user_id']}", callback_data=f"admin_admin_remove_{admin['user_id']}")])
        keyboard.append([InlineKeyboardButton("➕ إضافة أدمن", callback_data="admin_admin_add")])
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")])
        await query.edit_message_text("<blockquote>👤 <b>إدارة الأدمن</b>\nاضغط على أدمن لحذفه.</blockquote>", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))

    async def admin_admin_add_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        await self.db.set_user_state(user_id, "add_admin_wait", {})
        await query.edit_message_text("<blockquote>➕ أرسل ايدي المستخدم لإضافته كأدمن:</blockquote>", parse_mode=ParseMode.HTML)

    async def admin_admin_remove_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        target_id = int(query.data.replace("admin_admin_remove_", ""))
        await self.db.remove_admin(target_id)
        await query.answer("تم حذف الأدمن")
        await self.admin_admins_callback(update, context)

    async def admin_logs_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        logs = await self.db.get_logs(limit=50)
        text = "📜 <b>آخر السجلات</b>\n\n"
        for log in logs:
            text += f"🕒 {log['timestamp']} | User {log['user_id']} | {log['action']}\n"
            if log['details']:
                text += f"   {log['details']}\n"
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]]
        await query.edit_message_text(f"<blockquote>{text}</blockquote>", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))

    async def admin_backup_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        backup_data = await self.db.backup()
        json_str = json.dumps(backup_data, indent=2, default=str)
        await context.bot.send_document(chat_id=query.message.chat.id, document=InputFile(BytesIO(json_str.encode()), "backup.json"), caption="<blockquote>💾 نسخة احتياطية</blockquote>", parse_mode=ParseMode.HTML)
        await query.edit_message_text("<blockquote>تم إرسال النسخة الاحتياطية.</blockquote>", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]]))

    async def admin_maintenance_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        current = await self.db.get_setting("maintenance", "0")
        new_val = "0" if current == "1" else "1"
        await self.db.set_setting("maintenance", new_val)
        status = "🛠️ وضع الصيانة مفعل" if new_val == "1" else "✅ وضع الصيانة معطل"
        await query.edit_message_text(f"<blockquote>{status}\n\nيمكنك تغيير رسالة الصيانة من قسم الرسائل.</blockquote>", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]]))

    async def handle_admin_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return
        user = update.effective_user
        chat_id = update.effective_chat.id
        text = update.message.text.strip()
        state = await self.db.get_user_state(user.id)
        if not state:
            return
        if state['state'] == "broadcast_wait":
            users = await self.db.get_all_users()
            success = 0
            fail = 0
            for uid in users:
                try:
                    await context.bot.send_message(uid, f"<blockquote>{text}</blockquote>", parse_mode=ParseMode.HTML)
                    success += 1
                    await asyncio.sleep(0.05)
                except:
                    fail += 1
            await update.message.reply_text(f"<blockquote>📢 تم الإرسال:\n✅ نجح: {success}\n❌ فشل: {fail}</blockquote>", parse_mode=ParseMode.HTML)
            await self.db.clear_user_state(user.id)
            await self.admin_panel_callback(update, context)
        elif state['state'] == "edit_message_wait":
            key = state['data']['key']
            await self.db.set_message(key, text)
            await update.message.reply_text(f"<blockquote>✅ تم تحديث الرسالة <b>{key}</b></blockquote>", parse_mode=ParseMode.HTML)
            await self.db.clear_user_state(user.id)
            await self.admin_messages_callback(update, context)
        elif state['state'] == "ban_user_wait":
            try:
                target_id = int(text)
                await self.db.ban_user(target_id)
                await update.message.reply_text(f"<blockquote>✅ تم حظر المستخدم {target_id}</blockquote>", parse_mode=ParseMode.HTML)
            except:
                await update.message.reply_text("<blockquote>❌ ايدي غير صالح</blockquote>", parse_mode=ParseMode.HTML)
            await self.db.clear_user_state(user.id)
            await self.admin_users_callback(update, context)
        elif state['state'] == "unban_user_wait":
            try:
                target_id = int(text)
                await self.db.unban_user(target_id)
                await update.message.reply_text(f"<blockquote>✅ تم فك حظر المستخدم {target_id}</blockquote>", parse_mode=ParseMode.HTML)
            except:
                await update.message.reply_text("<blockquote>❌ ايدي غير صالح</blockquote>", parse_mode=ParseMode.HTML)
            await self.db.clear_user_state(user.id)
            await self.admin_users_callback(update, context)
        elif state['state'] == "add_channel_wait":
            parts = text.split('\n')
            if len(parts) >= 2:
                username = parts[0].strip()
                title = parts[1].strip()
                channels = await self.db.get_channels()
                order = max([c['order'] for c in channels]) + 1 if channels else 1
                await self.db.add_channel(username, title, order, user.id)
                await update.message.reply_text(f"<blockquote>✅ تم إضافة القناة {username}</blockquote>", parse_mode=ParseMode.HTML)
            else:
                await update.message.reply_text("<blockquote>❌ يرجى إرسال اليوزر في السطر الأول والعنوان في السطر الثاني</blockquote>", parse_mode=ParseMode.HTML)
            await self.db.clear_user_state(user.id)
            await self.admin_channels_callback(update, context)
        elif state['state'] == "add_admin_wait":
            try:
                target_id = int(text)
                await self.db.add_admin(target_id, ["all"], user.id)
                await update.message.reply_text(f"<blockquote>✅ تم إضافة الأدمن {target_id}</blockquote>", parse_mode=ParseMode.HTML)
            except:
                await update.message.reply_text("<blockquote>❌ ايدي غير صالح</blockquote>", parse_mode=ParseMode.HTML)
            await self.db.clear_user_state(user.id)
            await self.admin_admins_callback(update, context)

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.error(f"Update {update} caused error {context.error}")
        for dev in DEVELOPER_IDS:
            try:
                await context.bot.send_message(dev, f"❌ خطأ في البوت:\n{context.error}")
            except:
                pass

async def main():
    db = Database()
    await db.init()
    application = Application.builder().token(TOKEN).build()
    session = aiohttp.ClientSession()
    downloader = Downloader(db, session)
    handlers = BotHandlers(db, downloader)

    application.add_handler(CommandHandler("start", handlers.start_command))
    application.add_handler(CallbackQueryHandler(handlers.check_subscription_callback, pattern="^check_subscription$"))
    application.add_handler(CallbackQueryHandler(handlers.platform_callback, pattern="^download_"))
    application.add_handler(CallbackQueryHandler(handlers.back_to_main_callback, pattern="^back_to_main$"))
    application.add_handler(CallbackQueryHandler(handlers.admin_panel_callback, pattern="^admin_panel$"))
    application.add_handler(CallbackQueryHandler(handlers.admin_stats_callback, pattern="^admin_stats$"))
    application.add_handler(CallbackQueryHandler(handlers.admin_users_callback, pattern="^admin_users$"))
    application.add_handler(CallbackQueryHandler(handlers.admin_users_list_callback, pattern="^admin_users_list$"))
    application.add_handler(CallbackQueryHandler(handlers.admin_ban_user_callback, pattern="^admin_ban_user$"))
    application.add_handler(CallbackQueryHandler(handlers.admin_unban_user_callback, pattern="^admin_unban_user$"))
    application.add_handler(CallbackQueryHandler(handlers.admin_broadcast_callback, pattern="^admin_broadcast$"))
    application.add_handler(CallbackQueryHandler(handlers.admin_platforms_callback, pattern="^admin_platforms$"))
    application.add_handler(CallbackQueryHandler(handlers.admin_platform_toggle_callback, pattern="^admin_platform_toggle_"))
    application.add_handler(CallbackQueryHandler(handlers.admin_channels_callback, pattern="^admin_channels$"))
    application.add_handler(CallbackQueryHandler(handlers.admin_channel_toggle_callback, pattern="^admin_channel_toggle_"))
    application.add_handler(CallbackQueryHandler(handlers.admin_channel_add_callback, pattern="^admin_channel_add$"))
    application.add_handler(CallbackQueryHandler(handlers.admin_messages_callback, pattern="^admin_messages$"))
    application.add_handler(CallbackQueryHandler(handlers.admin_message_edit_callback, pattern="^admin_message_edit_"))
    application.add_handler(CallbackQueryHandler(handlers.admin_admins_callback, pattern="^admin_admins$"))
    application.add_handler(CallbackQueryHandler(handlers.admin_admin_add_callback, pattern="^admin_admin_add$"))
    application.add_handler(CallbackQueryHandler(handlers.admin_admin_remove_callback, pattern="^admin_admin_remove_"))
    application.add_handler(CallbackQueryHandler(handlers.admin_logs_callback, pattern="^admin_logs$"))
    application.add_handler(CallbackQueryHandler(handlers.admin_backup_callback, pattern="^admin_backup$"))
    application.add_handler(CallbackQueryHandler(handlers.admin_maintenance_callback, pattern="^admin_maintenance$"))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_text))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_admin_text))

    application.add_error_handler(handlers.error_handler)

    await application.initialize()
    await application.start()
    await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)

    try:
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()
        await session.close()
        await db.conn.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "already running" in str(e):
            loop = asyncio.get_event_loop()
            loop.run_until_complete(main())
        else:
            raise
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")