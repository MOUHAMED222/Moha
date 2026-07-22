import asyncio
import aiohttp
import json
import logging
import os
import re
import sqlite3
import sys
import signal
import urllib.parse
from datetime import datetime
from io import BytesIO
from typing import Optional, Dict, Any, List, Union
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import yt_dlp
import instaloader
from bs4 import BeautifulSoup
from user_agent import generate_user_agent

# ================================
# CONFIGURATION
# ================================

TOKEN = "8833337494:AAHYSG1_fkjdDnEsHdvuwRZs3_XvJ_IqyUQ"
CHANNEL_USERNAME = "@forzd9"
CHANNEL_USERNAME2 = "@forzd9"
DEVELOPER_IDS = [6891530912]

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TOKEN}"

# ================================
# LOGGING
# ================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ================================
# CONSTANTS FOR EXTERNAL APIS
# ================================

TIKTOK_API_URL = "https://tiksave.io/api/ajaxSearch"
TIKTOK_HEADERS = {
    'authority': 'tiksave.io',
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9,ar-IQ;q=0.8,ar;q=0.7',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'origin': 'https://tiksave.io',
    'referer': 'https://tiksave.io/ar',
    'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
    'sec-ch-ua-mobile': '?1',
    'sec-ch-ua-platform': '"Android"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': generate_user_agent(),
    'x-requested-with': 'XMLHttpRequest',
}
TIKTOK_COOKIES = {
    '__gads': 'ID=845d6f69a383b47d:T=1753115039:RT=1753777189:S=ALNI_MZ5mo4zUsj-FGlikaQuoQ4_swmsAw',
    '__gpi': 'UID=000010f3a3509093:T=1753115039:RT=1753777189:S=ALNI_MYygG_4blpkyQSIgGe4X14XjLOv_A',
    '__eoi': 'ID=f988b7216243e3f9:T=1753115039:RT=1753777189:S=AA-AfjaaFPzIIsO8HLZKRQPpo5H_',
    'FCNEC': '%5B%5B%22AKsRol_DFZW-z9Bos6qXwGfO8Q5J58PDhfHvyYmhEhiH_YoMOq4xyT_w_UAqYzh9EZDicGKtVO2YdT96aKCyE-6wO0HnG4tshKgcaw846Q46khC5rq-e0BMBYFBSXcTwPuhBnMw16CGjkEBIuJA9kx7kb17k5UHIZQ%3D%3D%22%5D%5D',
}

PINTEREST_IMG_API = "https://api.pinterestdl.io/api/image"
PINTEREST_API_URL = "https://everyweb.net/wp-json/aio-dl/video-data/"
PINTEREST_TOKEN = "0d8a45597e998fd21242b74089fac11b70dd1499a2ba25ad3b6100238811eafd"
PINTEREST_HASH = "aHR0cHM6Ly9waW4uaXQvNmp0RVZPRkdz1024YWlvLWRs"
PINTEREST_HEADERS = {
    'authority': 'everyweb.net',
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9,ar-IQ;q=0.8,ar;q=0.7',
    'content-type': 'application/x-www-form-urlencoded',
    'origin': 'https://everyweb.net',
    'referer': 'https://everyweb.net/pinterest/',
    'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
    'sec-ch-ua-mobile': '?1',
    'sec-ch-ua-platform': '"Android"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
}
PINTEREST_COOKIES = {
    '_lscache_vary': 'cd11052a02ea53c97b30994ffef5a4b1',
    '_ga_7P1TVF9P7M': 'GS2.1.s1753736522$o1$g0$t1753736522$j60$l0$h0',
    '_ga': 'GA1.1.30758253.1753736522',
    'pll_language': 'ar',
    '__gads': 'ID=e510112a91dffb7c:T=1753736524:RT=1753736524:S=ALNI_MZ3sbceLB32rKNPnoWCLYi6ccl2Xg',
    '__gpi': 'UID=0000111a4db6b81c:T=1753736524:RT=1753736524:S=ALNI_Ma6vm88YHiW8LcyOlTWXlmafYoqTw',
    '__eoi': 'ID=c2055eef46b6fba0:T=1753736524:RT=1753736524:S=AA-Afjatkw_ngmHHvPIurkUp7l9N',
    'FCNEC': '%5B%5B%22AKsRol9AtNttuHht9OxvvFO9Ok96J2IaZLpQu-5py1E6tFSwu2yhdbdoM53f1SzURfR4XU24wRX_AdkxfZ_gu117p4Yr0dxw9EhKPsSc6C3ZPVOaVqfs4Gfe0yUGxrj0brm30K13UfO86KxL-lCngteOv-aGd8p9SA%3D%3D%22%5D%5D',
}

FB_API_URL = "https://fbdownloader.to/api/ajaxSearch"
FB_HEADERS = {
    'authority': 'fbdownloader.to',
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9,ar-IQ;q=0.8,ar;q=0.7',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'origin': 'https://fbdownloader.to',
    'referer': 'https://fbdownloader.to/ar',
    'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
    'sec-ch-ua-mobile': '?1',
    'sec-ch-ua-platform': '"Android"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
    'x-requested-with': 'XMLHttpRequest',
}
FB_COOKIES = {'fpestid': 'TQyMQylz-gvL1kHeSpoed1DZBd_-Y4YBDU4rVgQYEKy2H3fz6rzKpilTTsGNsyjM8XNppw'}

SNAP_SMART_API_URL = "https://samrt-loader.com/kydwon/api/addfile"
SNAP_SMART_COOKIES = {'myCookieConsent': 'true', 'PHPSESSID': 'lruvkc8ljl99ks5imuc3fsca9u'}
SNAP_SMART_HEADERS = {
    'authority': 'samrt-loader.com',
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en-US,en;q=0.9,ar-IQ;q=0.8,ar;q=0.7',
    'content-type': 'application/json',
    'origin': 'https://samrt-loader.com',
    'referer': 'https://samrt-loader.com/ar/snapchat',
    'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
    'sec-ch-ua-mobile': '?1',
    'sec-ch-ua-platform': '"Android"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
}

SNAPCHAT_API_URL = "https://snapinsta.app/action.php"
SNAPCHAT_HEADERS = {
    'authority': 'snapinsta.app',
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'origin': 'https://snapinsta.app',
    'referer': 'https://snapinsta.app/',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
}

YOUTUBE_API_URL = "https://ytstream-download-youtube-videos.p.rapidapi.com/dl"
YOUTUBE_HEADERS = {
    "x-rapidapi-host": "ytstream-download-youtube-videos.p.rapidapi.com",
    "x-rapidapi-key": "ccbf5c7fb7mshe66aa640fe34327p188362jsn8c8ef10771d3"
}

INSTALOADER = instaloader.Instaloader()

# ================================
# DATABASE (SYNC, WRAPPED IN ASYNC)
# ================================

def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY,
                  username TEXT,
                  first_name TEXT,
                  last_name TEXT,
                  date_added TEXT,
                  first_time INTEGER DEFAULT 1,
                  banned INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

def add_user_sync(user):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute("SELECT first_time FROM users WHERE user_id = ?", (user['id'],))
        existing = c.fetchone()
        if existing:
            c.execute('''UPDATE users SET
                         username=?, first_name=?, last_name=?
                         WHERE user_id=?''',
                     (user.get('username'), user.get('first_name'),
                      user.get('last_name'), user['id']))
            first_time = existing[0]
        else:
            c.execute('''INSERT INTO users
                         (user_id, username, first_name, last_name, date_added, first_time)
                         VALUES (?, ?, ?, ?, ?, 1)''',
                     (user['id'], user.get('username'), user.get('first_name'),
                      user.get('last_name'), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            first_time = 1
        conn.commit()
        return first_time
    except Exception as e:
        logger.error(f"DB add_user error: {e}")
        return 0
    finally:
        conn.close()

def mark_user_as_old_sync(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute("UPDATE users SET first_time = 0 WHERE user_id = ?", (user_id,))
        conn.commit()
    except Exception as e:
        logger.error(f"DB mark_user_as_old error: {e}")
    finally:
        conn.close()

def get_all_users_sync():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute("SELECT user_id FROM users WHERE banned = 0")
        return [r[0] for r in c.fetchall()]
    except Exception as e:
        logger.error(f"DB get_all_users error: {e}")
        return []
    finally:
        conn.close()

def get_user_count_sync():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute("SELECT COUNT(*) FROM users WHERE banned = 0")
        return c.fetchone()[0]
    except Exception as e:
        logger.error(f"DB get_user_count error: {e}")
        return 0
    finally:
        conn.close()

def get_banned_users_sync():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute("SELECT user_id FROM users WHERE banned = 1")
        return [r[0] for r in c.fetchall()]
    except Exception as e:
        logger.error(f"DB get_banned_users error: {e}")
        return []
    finally:
        conn.close()

def ban_user_sync(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute("UPDATE users SET banned = 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"DB ban_user error: {e}")
        return False
    finally:
        conn.close()

def unban_user_sync(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute("UPDATE users SET banned = 0 WHERE user_id = ?", (user_id,))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"DB unban_user error: {e}")
        return False
    finally:
        conn.close()

def is_user_banned_sync(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute("SELECT banned FROM users WHERE user_id = ?", (user_id,))
        r = c.fetchone()
        return r[0] == 1 if r else False
    except Exception as e:
        logger.error(f"DB is_user_banned error: {e}")
        return False
    finally:
        conn.close()

def get_user_stats_sync():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute("SELECT COUNT(*) FROM users WHERE banned = 0")
        active = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM users WHERE banned = 1")
        banned = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM users WHERE date(date_added) = date('now')")
        new_today = c.fetchone()[0]
        c.execute("SELECT date_added FROM users ORDER BY date_added LIMIT 1")
        first = c.fetchone()
        first_date = first[0] if first else "غير معروف"
        return {
            'active_users': active,
            'banned_users': banned,
            'total_users': active + banned,
            'new_today': new_today,
            'first_user_date': first_date
        }
    except Exception as e:
        logger.error(f"DB get_user_stats error: {e}")
        return None
    finally:
        conn.close()

# ================================
# HELPER FUNCTIONS (SYNC, WRAPPED IN ASYNC)
# ================================

def safe_filename_from_url(url: str, default: str) -> str:
    try:
        tail = urllib.parse.urlparse(url).path.split('/')[-1]
        if not tail:
            return default
        if '.' not in tail:
            return f"{tail}.bin"
        return tail
    except:
        return default

def download_bytes_sync(url: str, timeout: int = 20) -> bytes:
    r = requests.get(url, stream=True, timeout=timeout)
    r.raise_for_status()
    return r.content

def extract_youtube_id(url: str) -> Optional[str]:
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'youtu.be\/([0-9A-Za-z_-]{11})',
        r'embed\/([0-9A-Za-z_-]{11})'
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None

# ================================
# ASYNC TELEGRAM API HELPERS
# ================================

class TelegramAPI:
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        self.base = TELEGRAM_API_URL

    async def _post(self, method: str, **kwargs):
        url = f"{self.base}/{method}"
        async with self.session.post(url, **kwargs) as resp:
            return await resp.json()

    def _wrap_text(self, text: str, parse_mode: str = None) -> str:
        if parse_mode == 'HTML' and not text.startswith('<blockquote>'):
            return f"<blockquote>{text}</blockquote>"
        return text

    async def send_message(self, chat_id, text, parse_mode=None, reply_markup=None):
        text = self._wrap_text(text, parse_mode)
        payload = {'chat_id': chat_id, 'text': text}
        if parse_mode:
            payload['parse_mode'] = parse_mode
        if reply_markup:
            if hasattr(reply_markup, 'to_dict'):
                payload['reply_markup'] = json.dumps(reply_markup.to_dict())
            else:
                payload['reply_markup'] = json.dumps(reply_markup)
        return await self._post('sendMessage', json=payload)

    async def send_video(self, chat_id, video, caption=None, supports_streaming=True,
                         width=None, height=None, duration=None, reply_markup=None):
        if caption:
            caption = self._wrap_text(caption, 'HTML')
        if isinstance(video, str):
            payload = {
                'chat_id': chat_id,
                'video': video,
                'supports_streaming': supports_streaming
            }
            if caption: payload['caption'] = caption
            if width: payload['width'] = width
            if height: payload['height'] = height
            if duration: payload['duration'] = duration
            if reply_markup:
                if hasattr(reply_markup, 'to_dict'):
                    payload['reply_markup'] = json.dumps(reply_markup.to_dict())
                else:
                    payload['reply_markup'] = json.dumps(reply_markup)
            return await self._post('sendVideo', json=payload)
        else:
            data = {'chat_id': chat_id, 'supports_streaming': 'true'}
            if caption: data['caption'] = caption
            if width: data['width'] = str(width)
            if height: data['height'] = str(height)
            if duration: data['duration'] = str(duration)
            if reply_markup:
                if hasattr(reply_markup, 'to_dict'):
                    data['reply_markup'] = json.dumps(reply_markup.to_dict())
                else:
                    data['reply_markup'] = json.dumps(reply_markup)
            files = {'video': video}
            return await self._post('sendVideo', data=data, files=files)

    async def send_document(self, chat_id, document, caption=None, filename=None, reply_markup=None):
        if caption:
            caption = self._wrap_text(caption, 'HTML')
        if isinstance(document, bytes):
            data = {'chat_id': chat_id}
            if caption: data['caption'] = caption
            if reply_markup:
                if hasattr(reply_markup, 'to_dict'):
                    data['reply_markup'] = json.dumps(reply_markup.to_dict())
                else:
                    data['reply_markup'] = json.dumps(reply_markup)
            files = {'document': (filename or 'file.bin', BytesIO(document))}
            return await self._post('sendDocument', data=data, files=files)
        else:
            data = {'chat_id': chat_id}
            if caption: data['caption'] = caption
            if reply_markup:
                if hasattr(reply_markup, 'to_dict'):
                    data['reply_markup'] = json.dumps(reply_markup.to_dict())
                else:
                    data['reply_markup'] = json.dumps(reply_markup)
            files = {'document': document}
            return await self._post('sendDocument', data=data, files=files)

    async def delete_message(self, chat_id, message_id):
        return await self._post('deleteMessage', json={'chat_id': chat_id, 'message_id': message_id})

    async def edit_message_text(self, chat_id, message_id, text, parse_mode=None, reply_markup=None):
        text = self._wrap_text(text, parse_mode)
        payload = {'chat_id': chat_id, 'message_id': message_id, 'text': text}
        if parse_mode:
            payload['parse_mode'] = parse_mode
        if reply_markup:
            if hasattr(reply_markup, 'to_dict'):
                payload['reply_markup'] = json.dumps(reply_markup.to_dict())
            else:
                payload['reply_markup'] = json.dumps(reply_markup)
        return await self._post('editMessageText', json=payload)

    async def get_chat_member(self, chat_id, user_id):
        return await self._post('getChatMember', json={'chat_id': chat_id, 'user_id': user_id})

    async def answer_callback_query(self, callback_query_id, text=None, show_alert=False):
        payload = {'callback_query_id': callback_query_id}
        if text:
            payload['text'] = text
        if show_alert:
            payload['show_alert'] = show_alert
        return await self._post('answerCallbackQuery', json=payload)

    async def get_updates(self, offset=None, timeout=30):
        params = {'timeout': timeout}
        if offset:
            params['offset'] = offset
        return await self._post('getUpdates', params=params)

# ================================
# BOT CLASS
# ================================

class DownloadBot:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.api: Optional[TelegramAPI] = None
        self.admin_actions = {}
        init_db()
        self.instaloader = instaloader.Instaloader()
        self.running = True
        self.style_emoji = {
            'success': '✅',
            'danger': '❌',
            'primary': '🔵'
        }

    async def start(self):
        self.session = aiohttp.ClientSession()
        self.api = TelegramAPI(self.session)
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        logger.info("Received shutdown signal")
        self.running = False

    async def run(self):
        await self.start()
        offset = None
        logger.info("Bot started...")
        while self.running:
            try:
                updates = await self.api.get_updates(offset)
                if updates.get('ok'):
                    for u in updates.get('result', []):
                        offset = u['update_id'] + 1
                        await self.process_update(u)
                else:
                    logger.error(f"GetUpdates error: {updates}")
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Main loop error: {e}")
                await asyncio.sleep(5)
        await self.session.close()
        logger.info("Bot stopped.")

    # ============================
    # UPDATE PROCESSING
    # ============================

    async def process_update(self, update):
        if 'message' in update:
            await self._handle_message(update['message'])
        elif 'callback_query' in update:
            await self._handle_callback(update['callback_query'])

    async def _handle_message(self, message):
        chat_id = message['chat']['id']
        user = message.get('from', {})
        text = message.get('text', '').strip()
        message_id = message.get('message_id')

        # Admin numeric input for ban/unban
        if user['id'] in DEVELOPER_IDS and text.isdigit():
            action = self.admin_actions.get(chat_id)
            if action == 'ban':
                await self._ban_user(chat_id, user['id'], text)
                del self.admin_actions[chat_id]
                return
            elif action == 'unban':
                await self._unban_user(chat_id, user['id'], text)
                del self.admin_actions[chat_id]
                return

        # Commands
        if text.startswith('/start'):
            await self._start(user, chat_id)
        elif text.startswith('/send'):
            args = text.split()[1:]
            await self._send_command(user, chat_id, args)
        elif text.startswith('/admin'):
            await self._admin_panel(chat_id, user['id'])
        else:
            await self._handle_url(user, chat_id, text, message_id)

    async def _handle_callback(self, callback_query):
        data = callback_query.get('data', '')
        chat_id = callback_query['message']['chat']['id']
        user_id = callback_query['from']['id']
        await self.api.answer_callback_query(callback_query['id'])

        if data.startswith('broadcast_'):
            await self._broadcast_confirmation(callback_query, data)
        elif data.startswith('download_') or data == 'back_to_main' or data == 'admin_panel':
            await self._main_button_click(callback_query, data)
        elif data.startswith('platform_'):
            platform = data.replace('platform_', '')
            await self._platform_selection(callback_query, platform)
        elif data.startswith('admin_'):
            await self._admin_button_click(callback_query, data)
            if data == 'admin_ban':
                self.admin_actions[chat_id] = 'ban'
            elif data == 'admin_unban':
                self.admin_actions[chat_id] = 'unban'
            elif data == 'admin_cancel':
                if chat_id in self.admin_actions:
                    del self.admin_actions[chat_id]

    # ============================
    # SUBSCRIPTION & USER CHECK
    # ============================

    async def _check_subscription(self, user_id):
        try:
            r1 = await self.api.get_chat_member(CHANNEL_USERNAME, user_id)
            if not r1.get('ok'): return False
            s1 = r1['result']['status']
            if s1 not in ('member', 'administrator', 'creator'): return False

            r2 = await self.api.get_chat_member(CHANNEL_USERNAME2, user_id)
            if not r2.get('ok'): return False
            s2 = r2['result']['status']
            if s2 not in ('member', 'administrator', 'creator'): return False
            return True
        except Exception as e:
            logger.error(f"Subscription check error for {user_id}: {e}")
            return False

    async def _send_subscription_message(self, chat_id):
        msg = (
            "⚠️ <b>يجب الاشتراك في القناتين لاستخدام البوت</b>\n\n"
            f"📢 القناة الأولى: {CHANNEL_USERNAME}\n"
            f"📢 القناة الثانية: {CHANNEL_USERNAME2}\n\n"
            "بعد الاشتراك، اضغط /start لإعادة التفعيل."
        )
        await self.api.send_message(chat_id, msg, parse_mode='HTML')

    # ============================
    # COMMAND HANDLERS
    # ============================

    async def _start(self, user, chat_id):
        if await self._is_banned(user['id']):
            await self.api.send_message(chat_id, "⛔ تم حظرك من استخدام البوت.")
            return
        if not await self._check_subscription(user['id']):
            await self._send_subscription_message(chat_id)
            return

        first_time = await asyncio.to_thread(add_user_sync, user)
        if first_time == 1:
            await self._notify_new_user(user)
            await asyncio.to_thread(mark_user_as_old_sync, user['id'])

        welcome = (
            "🌟 <b>مرحباً بك في بوت التحميل الشامل</b>\n\n"
            "📥 يمكنك تحميل المحتوى من جميع منصات التواصل الاجتماعي\n"
            "🔹 بدون حقوق أو علامات مائية\n\n"
            "👇 اختر المنصة التي تريد التحميل منها:"
        )
        keyboard = self._main_keyboard()
        await self.api.send_message(chat_id, welcome, parse_mode='HTML', reply_markup=keyboard)

    async def _send_command(self, user, chat_id, args):
        if user['id'] not in DEVELOPER_IDS:
            await self.api.send_message(chat_id, "⛔ هذا الأمر للمطورين فقط.")
            return
        if not args:
            await self.api.send_message(chat_id, "✏️ يرجى كتابة الرسالة بعد الأمر /send")
            return
        msg = ' '.join(args)
        keyboard = self._broadcast_keyboard(msg)
        await self.api.send_message(chat_id, f"📢 هل تريد إرسال هذه الرسالة لجميع المستخدمين؟\n\n{msg}", reply_markup=keyboard)

    async def _admin_panel(self, chat_id, user_id):
        if user_id not in DEVELOPER_IDS:
            await self.api.send_message(chat_id, "⛔ هذا الأمر للمطورين فقط.")
            return
        keyboard = self._admin_keyboard()
        await self.api.send_message(chat_id, "👑 <b>لوحة تحكم الأدمن</b>", parse_mode='HTML', reply_markup=keyboard)

    # ============================
    # ADMIN PANEL ACTIONS
    # ============================

    async def _admin_stats(self, chat_id, user_id):
        if user_id not in DEVELOPER_IDS: return
        stats = await asyncio.to_thread(get_user_stats_sync)
        if stats:
            text = (
                "📊 <b>إحصائيات البوت</b>\n\n"
                f"👤 المستخدمين النشطين: <code>{stats['active_users']}</code>\n"
                f"🚫 المحظورين: <code>{stats['banned_users']}</code>\n"
                f"📈 الإجمالي: <code>{stats['total_users']}</code>\n"
                f"🆕 الجدد اليوم: <code>{stats['new_today']}</code>\n"
                f"📅 أول مستخدم: <code>{stats['first_user_date']}</code>"
            )
            await self.api.send_message(chat_id, text, parse_mode='HTML')
        else:
            await self.api.send_message(chat_id, "❌ حدث خطأ في جلب الإحصائيات.")

    async def _admin_ban(self, chat_id, user_id):
        if user_id not in DEVELOPER_IDS: return
        await self.api.send_message(chat_id, "🔨 أرسل <b>ايدي</b> المستخدم الذي تريد حظره.\n(يمكنك الحصول عليه من @userinfobot)", parse_mode='HTML')

    async def _admin_unban(self, chat_id, user_id):
        if user_id not in DEVELOPER_IDS: return
        await self.api.send_message(chat_id, "🔓 أرسل <b>ايدي</b> المستخدم الذي تريد فك حظره.", parse_mode='HTML')

    async def _admin_banned_list(self, chat_id, user_id):
        if user_id not in DEVELOPER_IDS: return
        banned = await asyncio.to_thread(get_banned_users_sync)
        if banned:
            part = "\n".join(str(uid) for uid in banned[:50])
            msg = f"🚫 <b>المستخدمون المحظورون</b>\n\n{part}"
            if len(banned) > 50:
                msg += f"\n\n... و {len(banned) - 50} آخرين"
            await self.api.send_message(chat_id, msg, parse_mode='HTML')
        else:
            await self.api.send_message(chat_id, "✅ لا يوجد مستخدمين محظورين.")

    async def _ban_user(self, chat_id, admin_id, target_id_str):
        if admin_id not in DEVELOPER_IDS: return
        try:
            target_id = int(target_id_str)
            if target_id in DEVELOPER_IDS:
                await self.api.send_message(chat_id, "⛔ لا يمكن حظر المطورين.")
                return
            if await asyncio.to_thread(ban_user_sync, target_id):
                await self.api.send_message(chat_id, f"✅ تم حظر المستخدم <code>{target_id}</code>", parse_mode='HTML')
            else:
                await self.api.send_message(chat_id, "❌ حدث خطأ في الحظر.")
        except ValueError:
            await self.api.send_message(chat_id, "❌ ايدي غير صالح.")

    async def _unban_user(self, chat_id, admin_id, target_id_str):
        if admin_id not in DEVELOPER_IDS: return
        try:
            target_id = int(target_id_str)
            if await asyncio.to_thread(unban_user_sync, target_id):
                await self.api.send_message(chat_id, f"✅ تم فك حظر المستخدم <code>{target_id}</code>", parse_mode='HTML')
            else:
                await self.api.send_message(chat_id, "❌ حدث خطأ في فك الحظر.")
        except ValueError:
            await self.api.send_message(chat_id, "❌ ايدي غير صالح.")

    async def _broadcast_confirmation(self, callback_query, data):
        chat_id = callback_query['message']['chat']['id']
        msg_id = callback_query['message']['message_id']
        if data == 'broadcast_no':
            await self.api.edit_message_text(chat_id, msg_id, "❌ تم إلغاء الإرسال الشامل.")
            return
        if data.startswith('broadcast_yes_'):
            msg = data[13:]
            users = await asyncio.to_thread(get_all_users_sync)
            total = len(users)
            success = 0
            fail = 0
            await self.api.edit_message_text(chat_id, msg_id, "⏳ جاري الإرسال...")
            for uid in users:
                try:
                    await self.api.send_message(uid, msg)
                    success += 1
                    await asyncio.sleep(0.5)
                except Exception as e:
                    fail += 1
                    logger.error(f"Broadcast fail to {uid}: {e}")
            result = (
                f"✅ تم الانتهاء من الإرسال الشامل\n\n"
                f"👥 المجموع: <code>{total}</code>\n"
                f"✅ نجح: <code>{success}</code>\n"
                f"❌ فشل: <code>{fail}</code>"
            )
            await self.api.edit_message_text(chat_id, msg_id, result, parse_mode='HTML')

    # ============================
    # KEYBOARD BUILDERS (with style)
    # ============================

    def _build_button(self, btn_def: dict) -> InlineKeyboardButton:
        # btn_def: { 'text': str, 'callback_data' or 'url': str, 'style': 'success'|'danger'|'primary' (optional) }
        text = btn_def['text']
        style = btn_def.get('style')
        if style and style in self.style_emoji:
            text = f"{self.style_emoji[style]} {text}"
        if 'callback_data' in btn_def:
            return InlineKeyboardButton(text, callback_data=btn_def['callback_data'])
        elif 'url' in btn_def:
            return InlineKeyboardButton(text, url=btn_def['url'])
        else:
            raise ValueError("Button must have either callback_data or url")

    def _main_keyboard(self):
        rows = [
            [
                {'text': 'يوتيوب', 'callback_data': 'download_youtube', 'style': 'primary'},
                {'text': 'فيسبوك', 'callback_data': 'download_facebook', 'style': 'primary'}
            ],
            [
                {'text': 'انستجرام', 'callback_data': 'download_instagram', 'style': 'primary'},
                {'text': 'بينتيريست', 'callback_data': 'download_pinterest', 'style': 'primary'}
            ],
            [
                {'text': 'تيك توك', 'callback_data': 'download_tiktok', 'style': 'primary'},
                {'text': 'سناب شات', 'callback_data': 'download_snapchat', 'style': 'primary'}
            ],
            [
                {'text': 'المطور', 'url': 'https://t.me/mouhamed_ma', 'style': 'success'},
                {'text': 'القناة', 'url': 'https://t.me/forzd9', 'style': 'success'}
            ]
        ]
        if DEVELOPER_IDS:
            rows.append([{'text': 'لوحة الأدمن', 'callback_data': 'admin_panel', 'style': 'danger'}])
        keyboard = []
        for row in rows:
            keyboard.append([self._build_button(btn) for btn in row])
        return InlineKeyboardMarkup(keyboard)

    def _admin_keyboard(self):
        rows = [
            [
                {'text': 'الإحصائيات', 'callback_data': 'admin_stats', 'style': 'primary'},
                {'text': 'بث للجميع', 'callback_data': 'admin_broadcast', 'style': 'primary'}
            ],
            [
                {'text': 'حظر', 'callback_data': 'admin_ban', 'style': 'danger'},
                {'text': 'فك حظر', 'callback_data': 'admin_unban', 'style': 'success'}
            ],
            [
                {'text': 'المحظورين', 'callback_data': 'admin_banned_list', 'style': 'danger'},
                {'text': 'إلغاء', 'callback_data': 'admin_cancel', 'style': 'danger'}
            ]
        ]
        keyboard = []
        for row in rows:
            keyboard.append([self._build_button(btn) for btn in row])
        return InlineKeyboardMarkup(keyboard)

    def _broadcast_keyboard(self, message):
        rows = [
            [{'text': 'نعم', 'callback_data': f'broadcast_yes_{message}', 'style': 'success'}],
            [{'text': 'لا', 'callback_data': 'broadcast_no', 'style': 'danger'}]
        ]
        keyboard = []
        for row in rows:
            keyboard.append([self._build_button(btn) for btn in row])
        return InlineKeyboardMarkup(keyboard)

    # ============================
    # BUTTON HANDLERS
    # ============================

    async def _main_button_click(self, callback_query, data):
        chat_id = callback_query['message']['chat']['id']
        msg_id = callback_query['message']['message_id']
        if data == 'admin_panel':
            await self._admin_panel(chat_id, callback_query['from']['id'])
            return
        if data.startswith('download_'):
            platform = data.replace('download_', '')
            msg = {
                'youtube': '🎬 أرسل رابط <b>يوتيوب</b> للتحميل:',
                'facebook': '📘 أرسل رابط <b>فيسبوك</b> للتحميل:',
                'instagram': '📸 أرسل رابط <b>انستجرام</b> للتحميل:',
                'pinterest': '📌 أرسل رابط <b>بينتيريست</b> للتحميل:',
                'tiktok': '🎵 أرسل رابط <b>تيك توك</b> للتحميل:',
                'snapchat': '👻 أرسل رابط <b>سناب شات</b> للتحميل:'
            }.get(platform, '')
            if msg:
                await self.api.edit_message_text(chat_id, msg_id, msg, parse_mode='HTML')
        elif data == 'back_to_main':
            welcome = (
                "🌟 <b>مرحباً بك في بوت التحميل الشامل</b>\n\n"
                "📥 تحميل بدون حقوق أو علامات مائية\n"
                "👇 اختر المنصة:"
            )
            keyboard = self._main_keyboard()
            await self.api.edit_message_text(chat_id, msg_id, welcome, parse_mode='HTML', reply_markup=keyboard)

    async def _platform_selection(self, callback_query, platform):
        # Not used directly as platform selection is now integrated in main buttons
        pass

    async def _admin_button_click(self, callback_query, data):
        chat_id = callback_query['message']['chat']['id']
        user_id = callback_query['from']['id']
        if data == 'admin_stats':
            await self._admin_stats(chat_id, user_id)
        elif data == 'admin_broadcast':
            await self.api.send_message(chat_id, "📣 أرسل الرسالة التي تريد بثها لجميع المستخدمين.")
        elif data == 'admin_ban':
            await self._admin_ban(chat_id, user_id)
        elif data == 'admin_unban':
            await self._admin_unban(chat_id, user_id)
        elif data == 'admin_banned_list':
            await self._admin_banned_list(chat_id, user_id)
        elif data == 'admin_cancel':
            await self.api.delete_message(chat_id, callback_query['message']['message_id'])

    # ============================
    # NOTIFICATIONS
    # ============================

    async def _notify_new_user(self, user):
        count = await asyncio.to_thread(get_user_count_sync)
        text = (
            "🆕 <b>مستخدم جديد</b>\n\n"
            f"🆔 الايدي: <code>{user['id']}</code>\n"
            f"👤 الاسم: {user.get('first_name', 'غير معروف')} {user.get('last_name', '')}\n"
            f"📛 اليوزر: @{user.get('username', 'لا يوجد')}\n"
            f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"👥 العدد الكلي: <code>{count}</code>"
        )
        for dev in DEVELOPER_IDS:
            try:
                await self.api.send_message(dev, text, parse_mode='HTML')
            except Exception as e:
                logger.error(f"Failed to notify dev {dev}: {e}")

    # ============================
    # BAN CHECK
    # ============================

    async def _is_banned(self, user_id):
        return await asyncio.to_thread(is_user_banned_sync, user_id)

    # ============================
    # URL ROUTER
    # ============================

    async def _handle_url(self, user, chat_id, text, message_id):
        if await self._is_banned(chat_id):
            await self.api.send_message(chat_id, "⛔ تم حظرك من استخدام البوت.")
            return
        if not await self._check_subscription(chat_id):
            await self._send_subscription_message(chat_id)
            return
        if not text.startswith(('http://', 'https://')):
            return

        try:
            low = text.lower()
            if "tiktok.com" in low:
                await self._tiktok(chat_id, text)
            elif "pin.it" in low or "pinterest.com" in low:
                await self._pinterest(chat_id, text)
            elif "facebook.com" in low:
                await self._facebook(chat_id, text)
            elif "instagram.com" in low:
                await self._instagram(chat_id, text)
            elif "snapchat.com" in low:
                await self._snapchat(chat_id, text)
            elif "youtube.com" in low or "youtu.be" in low:
                await self._youtube(chat_id, text)
            else:
                await self.api.send_message(
                    chat_id,
                    "⚠️ الرابط غير مدعوم.\n\n"
                    "الروابط المدعومة:\n"
                    "• TikTok\n• Instagram\n• Facebook\n• YouTube\n• Pinterest\n• Snapchat"
                )
        except Exception as e:
            logger.error(f"Router error for user {chat_id}: {e}")

    # ============================
    # PLATFORM DOWNLOADERS
    # ============================

    async def _show_loading(self, chat_id):
        resp = await self.api.send_message(chat_id, "⏳ جارٍ التحميل، يرجى الانتظار...")
        return resp.get('result', {}).get('message_id')

    async def _finish_loading(self, chat_id, msg_id):
        if msg_id:
            try:
                await self.api.delete_message(chat_id, msg_id)
            except:
                pass

    async def _tiktok(self, chat_id, url):
        loading_id = await self._show_loading(chat_id)
        try:
            data = {'q': url, 'lang': 'ar'}
            async with self.session.post(
                TIKTOK_API_URL,
                cookies=TIKTOK_COOKIES,
                headers=TIKTOK_HEADERS,
                data=data,
                timeout=aiohttp.ClientTimeout(total=20)
            ) as resp:
                resp.raise_for_status()
                json_data = await resp.json()
                html_content = json_data.get("data")
                if not html_content:
                    raise ValueError("No data")
                soup = BeautifulSoup(html_content, 'html.parser')
                video_tag = soup.find('video')
                video_url = video_tag.get('data-src') if video_tag else None
                if video_url:
                    await self._finish_loading(chat_id, loading_id)
                    await self.api.send_video(chat_id, video_url, caption="✅ تم التحميل بأعلى دقة")
                else:
                    await self._finish_loading(chat_id, loading_id)
                    await self.api.send_message(chat_id, "❌ تعذر تحميل الفيديو من تيك توك.")
        except Exception as e:
            logger.error(f"TikTok error: {e}")
            await self._finish_loading(chat_id, loading_id)
            await self.api.send_message(chat_id, "❌ حدث خطأ أثناء التحميل.")

    async def _pinterest(self, chat_id, url):
        loading_id = await self._show_loading(chat_id)
        try:
            # Try image first
            headers_img = {
                'authority': 'api.pinterestdl.io',
                'accept': '*/*',
                'accept-language': 'en-US,en;q=0.9,ar-IQ;q=0.8,ar;q=0.7',
                'origin': 'https://pinterestdl.io',
                'referer': 'https://pinterestdl.io/',
                'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
                'sec-ch-ua-mobile': '?1',
                'sec-ch-ua-platform': '"Android"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
            }
            async with self.session.get(
                PINTEREST_IMG_API,
                params={'url': url},
                headers=headers_img,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    img_url = data.get('imageUrl')
                    if img_url:
                        content = await asyncio.to_thread(download_bytes_sync, img_url, 25)
                        fname = safe_filename_from_url(img_url, "pinterest.jpg")
                        await self._finish_loading(chat_id, loading_id)
                        await self.api.send_document(chat_id, content, caption="✅ تم التحميل بأعلى دقة", filename=fname)
                        return

            # Video fallback
            data_form = {'url': url, 'token': PINTEREST_TOKEN, 'hash': PINTEREST_HASH}
            async with self.session.post(
                PINTEREST_API_URL,
                cookies=PINTEREST_COOKIES,
                headers=PINTEREST_HEADERS,
                data=data_form,
                timeout=aiohttp.ClientTimeout(total=20)
            ) as resp:
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
                            await self._finish_loading(chat_id, loading_id)
                            await self.api.send_video(chat_id, video_url, caption="✅ تم التحميل بأعلى دقة")
                            return

            await self._finish_loading(chat_id, loading_id)
            await self.api.send_message(chat_id, "❌ تعذر تحميل المحتوى من بينتيريست.")
        except Exception as e:
            logger.error(f"Pinterest error: {e}")
            await self._finish_loading(chat_id, loading_id)
            await self.api.send_message(chat_id, "❌ حدث خطأ أثناء التحميل.")

    async def _facebook(self, chat_id, url):
        loading_id = await self._show_loading(chat_id)
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
            async with self.session.post(
                FB_API_URL,
                cookies=FB_COOKIES,
                headers=FB_HEADERS,
                data=data,
                timeout=aiohttp.ClientTimeout(total=20)
            ) as resp:
                resp.raise_for_status()
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
                    await self._finish_loading(chat_id, loading_id)
                    await self.api.send_video(chat_id, video_url, caption="✅ تم التحميل بأعلى دقة")
                else:
                    await self._finish_loading(chat_id, loading_id)
                    await self.api.send_message(chat_id, "❌ تعذر تحميل الفيديو من فيسبوك.")
        except Exception as e:
            logger.error(f"Facebook error: {e}")
            await self._finish_loading(chat_id, loading_id)
            await self.api.send_message(chat_id, "❌ حدث خطأ أثناء التحميل.")

    async def _instagram(self, chat_id, url):
        loading_id = await self._show_loading(chat_id)
        try:
            ydl_opts = {
                'format': 'best',
                'quiet': True,
                'outtmpl': 'instagram_%(id)s.%(ext)s',
                'socket_timeout': 15,
                'no_check_certificate': True,
            }
            # Run yt-dlp in thread
            def dl():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if 'entries' in info:
                        info = info['entries'][0]
                    if info.get('duration', 0) > 0:
                        ydl.download([url])
                        filename = ydl.prepare_filename(info)
                        return filename, info
                    else:
                        img_url = info['url']
                        content = download_bytes_sync(img_url, 25)
                        return content, None
            result = await asyncio.to_thread(dl)
            await self._finish_loading(chat_id, loading_id)
            if isinstance(result, tuple):
                if isinstance(result[0], str):
                    filename, info = result
                    with open(filename, 'rb') as f:
                        await self.api.send_video(
                            chat_id,
                            f,
                            caption="✅ تم التحميل بأعلى دقة",
                            width=info.get('width'),
                            height=info.get('height'),
                            duration=info.get('duration')
                        )
                    os.remove(filename)
                else:
                    content, _ = result
                    fname = safe_filename_from_url(url, "instagram.jpg")
                    await self.api.send_document(chat_id, content, caption="✅ تم التحميل بأعلى دقة", filename=fname)
            else:
                raise ValueError("Unexpected result")
        except yt_dlp.DownloadError as e:
            logger.warning(f"Instagram yt-dlp fallback: {e}")
            # Fallback to instaloader
            try:
                shortcode = re.search(r'/p/([^/]+)', url) or re.search(r'/reel/([^/]+)', url)
                if shortcode:
                    post = await asyncio.to_thread(
                        instaloader.Post.from_shortcode,
                        INSTALOADER.context,
                        shortcode.group(1)
                    )
                    if post.is_video:
                        await self._finish_loading(chat_id, loading_id)
                        await self.api.send_video(chat_id, post.video_url, caption="✅ تم التحميل بأعلى دقة")
                    else:
                        content = await asyncio.to_thread(download_bytes_sync, post.url, 25)
                        fname = safe_filename_from_url(post.url, "instagram.jpg")
                        await self._finish_loading(chat_id, loading_id)
                        await self.api.send_document(chat_id, content, caption="✅ تم التحميل بأعلى دقة", filename=fname)
                    return
            except Exception as ee:
                logger.error(f"Instagram fallback error: {ee}")
            await self._finish_loading(chat_id, loading_id)
            await self.api.send_message(chat_id, "❌ تعذر تحميل المحتوى من انستجرام.")
        except Exception as e:
            logger.error(f"Instagram error: {e}")
            await self._finish_loading(chat_id, loading_id)
            await self.api.send_message(chat_id, "❌ حدث خطأ أثناء التحميل.")

    async def _snapchat(self, chat_id, url):
        loading_id = await self._show_loading(chat_id)
        try:
            # Try smart-loader first
            payload = {'file_name': url}
            try:
                async with self.session.post(
                    SNAP_SMART_API_URL,
                    cookies=SNAP_SMART_COOKIES,
                    headers=SNAP_SMART_HEADERS,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=20)
                ) as resp:
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
                            await self._finish_loading(chat_id, loading_id)
                            await self.api.send_video(chat_id, video_url, caption="✅ تم التحميل بأعلى دقة")
                            return
            except Exception:
                pass

            # Fallback to snapinsta
            data = {'url': url, 'action': 'post'}
            async with self.session.post(
                SNAPCHAT_API_URL,
                headers=SNAPCHAT_HEADERS,
                data=data,
                timeout=aiohttp.ClientTimeout(total=20)
            ) as resp:
                resp.raise_for_status()
                json_data = await resp.json()
                if json_data.get('status') == 'success' and 'url' in json_data:
                    video_url = json_data['url']
                    await self._finish_loading(chat_id, loading_id)
                    await self.api.send_video(chat_id, video_url, caption="✅ تم التحميل بأعلى دقة")
                    return

            await self._finish_loading(chat_id, loading_id)
            await self.api.send_message(chat_id, "❌ تعذر تحميل المحتوى من سناب شات.")
        except Exception as e:
            logger.error(f"Snapchat error: {e}")
            await self._finish_loading(chat_id, loading_id)
            await self.api.send_message(chat_id, "❌ حدث خطأ أثناء التحميل.")

    async def _youtube(self, chat_id, url):
        loading_id = await self._show_loading(chat_id)
        try:
            ydl_opts = {
                'format': 'best',
                'quiet': True,
                'outtmpl': 'youtube_%(id)s.%(ext)s',
                'socket_timeout': 15,
                'no_check_certificate': True,
            }
            def dl():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    ydl.download([url])
                    filename = ydl.prepare_filename(info)
                    return filename, info
            filename, info = await asyncio.to_thread(dl)
            await self._finish_loading(chat_id, loading_id)
            with open(filename, 'rb') as f:
                await self.api.send_video(
                    chat_id,
                    f,
                    caption="✅ تم التحميل بأعلى دقة",
                    width=info.get('width'),
                    height=info.get('height'),
                    duration=info.get('duration')
                )
            os.remove(filename)
        except yt_dlp.DownloadError as e:
            logger.warning(f"YouTube yt-dlp fallback: {e}")
            # RapidAPI fallback
            try:
                video_id = extract_youtube_id(url)
                if video_id:
                    api_url = f"{YOUTUBE_API_URL}?id={video_id}"
                    async with self.session.get(
                        api_url,
                        headers=YOUTUBE_HEADERS,
                        timeout=aiohttp.ClientTimeout(total=20)
                    ) as resp:
                        resp.raise_for_status()
                        data = await resp.json()
                        if data.get('status') != 'fail' and 'formats' in data and len(data['formats']) > 0:
                            video_url = data['formats'][0]['url']
                            await self._finish_loading(chat_id, loading_id)
                            await self.api.send_video(chat_id, video_url, caption="✅ تم التحميل بأعلى دقة")
                            return
            except Exception as e2:
                logger.error(f"YouTube fallback error: {e2}")
            await self._finish_loading(chat_id, loading_id)
            await self.api.send_message(chat_id, "❌ تعذر تحميل الفيديو من يوتيوب.")
        except Exception as e:
            logger.error(f"YouTube error: {e}")
            await self._finish_loading(chat_id, loading_id)
            await self.api.send_message(chat_id, "❌ حدث خطأ أثناء التحميل.")


async def main():
    bot = DownloadBot()
    try:
        await bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")

if __name__ == "__main__":
    asyncio.run(main())