
# IH_PY 
# -*- coding: utf-8 -*-
"""
بوت استضافة متكامل مع جميع الميزات المطلوبة (1-24)
تم التحديث: 2026-07-16 - تحسين شامل لتجربة المستخدم (UX)
تم إصلاح مشكلة رفع الملفات (إنشاء مجلد لكل مشروع)
تم تحسين تثبيت المكتبات: فقط المستوردة في الملف الرئيسي أو requirements.txt
تم تعديل الأزرار لتعديل الرسالة الحالية بدلاً من إرسال جديدة
تم إزالة جميع الإيموجي
تم فصل أزرار المطور عن أزرار المستخدم
"""

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import subprocess
import os
import signal
import sqlite3
import re
import requests
import zipfile
import shutil
import html
import logging
import time
import json
from datetime import datetime, timedelta
import concurrent.futures
import threading
import sys
import io
import py_compile
import psutil
from telebot.apihelper import ApiTelegramException
import venv
import tempfile
import hashlib
import stat
import fnmatch
import schedule
from queue import Queue
import random
import string

# ============================================================
#                    الإعدادات العامة
# ============================================================

TOKEN = 'tok'
ADMIN_ID = 111
DEVELOPER_CHANNEL = 'https://t.me/ihn_4'

# إعدادات مراقبة الموارد
RESOURCE_MONITOR_CONFIG = {
    'cpu_percent': 80.0,
    'ram_percent': 85.0,
    'disk_percent': 90.0,
    'check_interval': 60,
    'cooldown_seconds': 300,
}
resource_last_alert = {'cpu': 0, 'ram': 0, 'disk': 0}
resource_usage = {'cpu': 0.0, 'ram': 0.0, 'disk': 0.0}

# إعدادات إعادة التشغيل
RESTART_CONFIG = {
    'max_attempts': 5,
    'interval_seconds': 60,
    'cooldown_minutes': 10,
}

# إعدادات النسخ الاحتياطي
BACKUP_CONFIG = {
    'max_backups': 5,
    'auto_backup_interval_hours': 24,
}

# إعدادات الحدود الافتراضية
DEFAULT_RESOURCE_LIMITS = {
    'cpu_percent': 80,
    'ram_mb': 512,
    'storage_mb': 1024,
    'max_processes': 1,
}

# إعدادات الطرفية
TERMINAL_TIMEOUT = 60
TERMINAL_LOG_FILE = 'terminal_commands.log'
FORBIDDEN_COMMANDS = ['rm -rf /', 'dd if=', 'mkfs', 'shutdown', 'reboot', 'killall', 'pkill', 'chmod 777', 'chown']

# إعدادات الإشعارات
NOTIFICATIONS_ENABLED = True

# ============================================================
#                    التهيئة الأساسية
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger('HostingBot')

bot = telebot.TeleBot(TOKEN, parse_mode='HTML')

# الإيموجي - تم إزالة جميع الرموز التعبيرية واستبدالها بنصوص وصفية
EMOJI = {
    'success': '[OK]',
    'error': '[ERROR]',
    'warning': '[WARN]',
    'info': '[INFO]',
    'notif': '[NOTIF]',
    'wait': '[WAIT]',
    'running': '[RUN]',
    'stopped': '[STOP]',
}

# دعم الألوان
COLOR_MAP = {
    'red': {"@type": "linearColor", "top_color": 0xFFEE4444, "bottom_color": 0xFFCC2222},
    'orange': {"@type": "linearColor", "top_color": 0xFFFF8800, "bottom_color": 0xFFDD6600},
    'purple': {"@type": "linearColor", "top_color": 0xFF9B59B6, "bottom_color": 0xFF7D3C98},
    'green': {"@type": "linearColor", "top_color": 0xFF27AE60, "bottom_color": 0xFF1E8449},
    'blue': {"@type": "linearColor", "top_color": 0xFF2E86C1, "bottom_color": 0xFF1A5276},
}

# ============================================================
#                    قالب الرسائل الموحد
# ============================================================

def build_message(title, content, footer=None, header_extra=None):
    """
    بناء رسالة موحدة مع Header و Footer.
    """
    header = f"<b>{title}</b>"
    if header_extra:
        header += f"\n{header_extra}"
    body = content
    if footer is None:
        footer = "استخدم الأزرار للتنقل."
    full_text = f"{header}\n\n{body}\n\n<blockquote>{footer}</blockquote>"
    return full_text

def send_formatted_message(chat_id, title, content, buttons=None, edit=False, message_id=None, footer=None, header_extra=None):
    """
    إرسال أو تعديل رسالة باستخدام القالب الموحد.
    """
    text = build_message(title, content, footer, header_extra)
    return send_msg(chat_id, text, buttons, edit, message_id)

def send_msg(chat_id, text, buttons=None, edit=False, message_id=None):
    try:
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        if buttons:
            payload["reply_markup"] = build_markup(buttons)
        if edit and message_id:
            payload["message_id"] = message_id
            resp = requests.post(f"https://api.telegram.org/bot{TOKEN}/editMessageText", data=payload, timeout=10)
            if resp.json().get("ok"):
                return None
            else:
                # إذا فشل التعديل، نحاول حذف وإرسال جديدة (في حالات نادرة)
                try:
                    bot.delete_message(chat_id, message_id)
                except:
                    pass
                del payload["message_id"]
                resp2 = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data=payload, timeout=10)
                return resp2.json().get("result")
        else:
            resp = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data=payload, timeout=10)
            return resp.json().get("result")
    except Exception as e:
        logger.error(f"خطأ في send_msg: {e}")
        return None

def create_btn(text, callback=None, url=None, color=None):
    btn = {"text": text}
    if callback:
        btn["callback_data"] = callback
        if color and color in COLOR_MAP:
            btn["color"] = COLOR_MAP[color]
    elif url:
        btn["url"] = url
    else:
        btn["callback_data"] = "noop"
    return btn

def build_markup(buttons_grid):
    if not buttons_grid:
        return None
    keyboard = []
    for row in buttons_grid:
        row_list = []
        for btn in row:
            if isinstance(btn, dict):
                row_list.append(btn)
            else:
                row_list.append({"text": btn.text, "callback_data": btn.callback_data})
        keyboard.append(row_list)
    return json.dumps({"inline_keyboard": keyboard})

def safe_delete_message(chat_id, message_id):
    try:
        bot.delete_message(chat_id, message_id)
        return True
    except:
        return False

# ============================================================
#                    دوال مساعدة UI/UX
# ============================================================

def get_progress_bar(percentage, length=10):
    filled = int(percentage / 100 * length)
    bar = "█" * filled + "░" * (length - filled)
    return f"[{bar}] {percentage:.1f}%"

def format_size(size_bytes):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def format_time(seconds):
    if seconds < 60:
        return f"{seconds:.0f} ث"
    if seconds < 3600:
        return f"{seconds/60:.1f} د"
    if seconds < 86400:
        return f"{seconds/3600:.1f} س"
    return f"{seconds/86400:.1f} يوم"

def paginate_items(items, page, per_page=10):
    total = len(items)
    start = page * per_page
    end = min(start + per_page, total)
    page_items = items[start:end]
    total_pages = (total + per_page - 1) // per_page
    return page_items, total_pages, start, end

def add_navigation_buttons(buttons, callback_prefix, page, total_pages, back_callback=None, home_callback='main_menu'):
    nav_row = []
    if page > 0:
        nav_row.append(create_btn("السابق", callback=f"{callback_prefix}_{page-1}", color='blue'))
    if page < total_pages - 1:
        nav_row.append(create_btn("التالي", callback=f"{callback_prefix}_{page+1}", color='blue'))
    if nav_row:
        buttons.append(nav_row)
    # أزرار الرجوع والرئيسية
    bottom_row = []
    if back_callback:
        bottom_row.append(create_btn("رجوع", callback=back_callback, color='blue'))
    bottom_row.append(create_btn("الرئيسية", callback=home_callback, color='blue'))
    buttons.append(bottom_row)
    return buttons

# متغيرات الجلسة لتذكر الصفحات والفرز
user_session = {}

def get_user_session(user_id):
    if user_id not in user_session:
        user_session[user_id] = {
            'last_page': 'main_menu',
            'filters': {},
            'sort': {'by': 'name', 'order': 'asc'},
            'current_path': None,
            'current_bot': None,
            'current_archive': None,
        }
    return user_session[user_id]

def update_user_session(user_id, key, value):
    session = get_user_session(user_id)
    session[key] = value

# ============================================================
#                    قاعدة البيانات
# ============================================================

DB_PATH = 'hosting_v11.db'
_local = threading.local()

def get_conn():
    if not hasattr(_local, 'conn') or _local.conn is None:
        _local.conn = sqlite3.connect(DB_PATH)
        _local.conn.row_factory = sqlite3.Row
    return _local.conn

def get_cursor():
    conn = get_conn()
    if not hasattr(_local, 'cursor') or _local.cursor is None:
        _local.cursor = conn.cursor()
    return _local.cursor

def _init_db():
    c = get_conn()
    # الجداول الأساسية
    c.execute('''CREATE TABLE IF NOT EXISTS bots 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                   user_id INTEGER, 
                   file_path TEXT, 
                   original_name TEXT, 
                   main_file TEXT,
                   pid INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS banned_users 
                  (user_id INTEGER PRIMARY KEY, 
                   banned_at TEXT,
                   reason TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                  (user_id INTEGER PRIMARY KEY,
                   first_name TEXT,
                   username TEXT,
                   start_count INTEGER DEFAULT 1,
                   first_start TEXT,
                   last_start TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS unban_log 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   user_id INTEGER,
                   unbanned_by INTEGER,
                   unbanned_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS restart_attempts 
                  (bot_id INTEGER,
                   attempt_time TEXT,
                   PRIMARY KEY (bot_id, attempt_time))''')
    # الجداول الجديدة
    c.execute('''CREATE TABLE IF NOT EXISTS envs 
                  (bot_id INTEGER PRIMARY KEY,
                   venv_path TEXT,
                   python_path TEXT,
                   created_at TEXT,
                   last_used TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS schedules 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   bot_id INTEGER,
                   action TEXT,
                   schedule_type TEXT,
                   schedule_time TEXT,
                   next_run TEXT,
                   enabled INTEGER DEFAULT 1,
                   created_by INTEGER,
                   created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS resource_limits 
                  (bot_id INTEGER PRIMARY KEY,
                   cpu_percent INTEGER DEFAULT 80,
                   ram_mb INTEGER DEFAULT 512,
                   storage_mb INTEGER DEFAULT 1024,
                   max_processes INTEGER DEFAULT 1,
                   updated_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS archived_projects 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   bot_id INTEGER,
                   archive_path TEXT,
                   archived_at TEXT,
                   archived_by INTEGER,
                   original_path TEXT,
                   status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS audit_log 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   timestamp TEXT,
                   user_id INTEGER,
                   bot_id INTEGER,
                   action TEXT,
                   details TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS backup_logs 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   bot_id INTEGER,
                   backup_path TEXT,
                   timestamp TEXT,
                   status TEXT,
                   details TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS update_logs 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   bot_id INTEGER,
                   old_version TEXT,
                   new_version TEXT,
                   timestamp TEXT,
                   status TEXT,
                   details TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS health_checks 
                  (bot_id INTEGER,
                   check_time TEXT,
                   status TEXT,
                   response_time REAL,
                   details TEXT,
                   PRIMARY KEY (bot_id, check_time))''')
    c.execute('''CREATE TABLE IF NOT EXISTS resource_usage_history 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   bot_id INTEGER,
                   timestamp TEXT,
                   cpu REAL,
                   ram REAL,
                   storage REAL,
                   network_rx REAL,
                   network_tx REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS notifications_settings 
                  (user_id INTEGER PRIMARY KEY,
                   enabled INTEGER DEFAULT 1,
                   last_modified TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS admins 
                  (user_id INTEGER PRIMARY KEY,
                   permissions TEXT,
                   added_by INTEGER,
                   added_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS file_operations 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   bot_id INTEGER,
                   operation TEXT,
                   source_path TEXT,
                   dest_path TEXT,
                   timestamp TEXT,
                   status TEXT)''')
    c.commit()

_init_db()

def ensure_table_columns():
    try:
        c = get_conn()
        for table in ['bots']:
            cur = c.execute(f"PRAGMA table_info({table})")
            existing = {row[1] for row in cur.fetchall()}
            required = {'id', 'user_id', 'file_path', 'original_name', 'main_file', 'pid'}
            for col in required:
                if col not in existing:
                    if col == 'pid':
                        c.execute(f'ALTER TABLE {table} ADD COLUMN {col} INTEGER DEFAULT 0')
                    else:
                        c.execute(f'ALTER TABLE {table} ADD COLUMN {col} TEXT')
                    c.commit()
    except Exception as e:
        logger.error(f"خطأ في تحديث الجداول: {e}")
ensure_table_columns()

# ============================================================
#                    دوال مساعدة
# ============================================================

def register_user_start(user_id, first_name, username):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c = get_cursor()
    c.execute('SELECT start_count FROM users WHERE user_id = ?', (user_id,))
    row = c.fetchone()
    if row:
        c.execute('UPDATE users SET start_count = start_count+1, last_start=?, first_name=?, username=? WHERE user_id=?',
                  (now, first_name, username, user_id))
    else:
        c.execute('INSERT INTO users (user_id, first_name, username, start_count, first_start, last_start) VALUES (?,?,?,1,?,?)',
                  (user_id, first_name, username, now, now))
    get_conn().commit()

def is_user_banned(user_id):
    c = get_cursor()
    c.execute('SELECT 1 FROM banned_users WHERE user_id=?', (user_id,))
    return c.fetchone() is not None

def ban_user(user_id, reason=None):
    c = get_cursor()
    c.execute('INSERT OR IGNORE INTO banned_users (user_id, banned_at, reason) VALUES (?, ?, ?)',
              (user_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), reason))
    get_conn().commit()

def unban_user(user_id):
    c = get_cursor()
    c.execute('DELETE FROM banned_users WHERE user_id=?', (user_id,))
    get_conn().commit()

def get_banned_users():
    c = get_cursor()
    c.execute('SELECT user_id, banned_at, reason FROM banned_users ORDER BY banned_at DESC')
    return c.fetchall()

def get_total_users():
    c = get_cursor()
    c.execute('SELECT COUNT(*) FROM users')
    return c.fetchone()[0]

def get_banned_count():
    c = get_cursor()
    c.execute('SELECT COUNT(*) FROM banned_users')
    return c.fetchone()[0]

def get_active_users():
    return get_total_users() - get_banned_count()

def get_unban_count():
    c = get_cursor()
    c.execute('SELECT COUNT(*) FROM unban_log')
    return c.fetchone()[0]

def get_users_list():
    c = get_cursor()
    c.execute('SELECT user_id, first_name, username, start_count, first_start, last_start FROM users ORDER BY last_start DESC')
    return c.fetchall()

def get_all_users():
    c = get_cursor()
    c.execute('SELECT user_id FROM users')
    return [row[0] for row in c.fetchall()]

def log_unban(user_id, admin_id):
    c = get_cursor()
    c.execute('INSERT INTO unban_log (user_id, unbanned_by, unbanned_at) VALUES (?, ?, ?)',
              (user_id, admin_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    get_conn().commit()

def get_token_and_username(file_path):
    token = "غير موجود"
    bot_user = "غير معروف"
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                match = re.search(r'(?:TOKEN\s*=\s*["\']?)(\d{8,10}:[A-Za-z0-9_-]{35})', content)
                if not match:
                    match = re.search(r'(\d{8,10}:[A-Za-z0-9_-]{35})', content)
                if match:
                    token = match.group(1)
                    try:
                        res = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=5).json()
                        if res.get('ok'):
                            bot_user = "@" + res['result']['username']
                    except:
                        pass
    except:
        pass
    return token, bot_user

def is_process_running(pid):
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except:
        return False

def get_py_files_from_directory(directory):
    py_files = []
    ignore_dirs = {'__pycache__', '.git', '.idea', 'venv', 'env', 'lib', 'include', 'bin'}
    ignore_files = {'README.md', 'README.txt', 'LICENSE', 'LICENSE.txt', 'requirements.txt'}
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for file in files:
            if file.endswith('.py') and file not in ignore_files:
                full = os.path.join(root, file)
                rel = os.path.relpath(full, directory)
                py_files.append(rel)
    return py_files

def safe_extract_zip(zip_path, extract_dir):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        if zip_ref.testzip():
            raise ValueError("الملف مضغوط بكلمة مرور أو تالف.")
        extract_dir_abs = os.path.abspath(extract_dir)
        # إنشاء المجلد مسبقاً لتجنب مشاكل المسار
        os.makedirs(extract_dir, exist_ok=True)
        for member in zip_ref.namelist():
            # استخدام normpath لتجنب مشاكل / و \
            member_path = os.path.abspath(os.path.join(extract_dir, os.path.normpath(member)))
            if not member_path.startswith(extract_dir_abs + os.sep):
                raise ValueError(f"مسار غير آمن داخل ZIP: {member}")
        zip_ref.extractall(extract_dir)

def download_telegram_file_large(file_id, dest_path, chat_id=None, status_msg_id=None):
    try:
        file_info = bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
        # التأكد من وجود المجلد الوجهة
        os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)
        with requests.get(file_url, stream=True, timeout=300) as r:
            r.raise_for_status()
            total = int(r.headers.get('content-length', 0))
            downloaded = 0
            with open(dest_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=65536):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if chat_id and status_msg_id and total:
                        percent = (downloaded / total) * 100
                        if int(percent) % 10 == 0:
                            progress = get_progress_bar(percent)
                            send_msg(chat_id, f"[WAIT] تنزيل الملف...\n{progress}", edit=True, message_id=status_msg_id)
        return True
    except requests.exceptions.RequestException as e:
        # إعادة محاولة واحدة في حال فشل الشبكة
        time.sleep(2)
        try:
            r = requests.get(file_url, stream=True, timeout=300)
            r.raise_for_status()
            total = int(r.headers.get('content-length', 0))
            downloaded = 0
            with open(dest_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=65536):
                    f.write(chunk)
                    downloaded += len(chunk)
            return True
        except Exception as e2:
            raise RuntimeError(f"فشل تنزيل الملف بعد المحاولة: {str(e2)[:150]}")
    except Exception as e:
        raise RuntimeError(f"فشل تنزيل الملف: {str(e)[:150]}")

def safe_filename(name):
    # استبدال الأحرف غير المسموح بها في أنظمة الملفات
    return re.sub(r'[\\/*?:"<>|]', '_', name)

def send_admin_notification(user_id, first_name, username, file_name, file_type):
    content = (
        f"<b>المستخدم:</b> {first_name}\n"
        f"<b>المعرف:</b> <code>{user_id}</code>\n"
        f"<b>يوزر:</b> {f'@{username}' if username else 'لا يوجد'}\n"
        f"<b>اسم الملف:</b> <code>{file_name}</code>\n"
        f"<b>نوع الملف:</b> {file_type}\n"
        f"<b>الوقت:</b> <code>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</code>"
    )
    send_formatted_message(ADMIN_ID, "[NOTIF] تم رفع ملف جديد", content, footer="تم الرفع بواسطة المستخدم.")

# ============================================================
#                    دوال البيئات الافتراضية
# ============================================================

def create_venv(bot_id, project_path):
    venv_path = os.path.join(project_path, 'venv')
    if os.path.exists(venv_path):
        shutil.rmtree(venv_path, ignore_errors=True)
    try:
        builder = venv.EnvBuilder(with_pip=True)
        builder.create(venv_path)
        if sys.platform == 'win32':
            python_path = os.path.join(venv_path, 'Scripts', 'python.exe')
        else:
            python_path = os.path.join(venv_path, 'bin', 'python')
        c = get_cursor()
        c.execute('INSERT OR REPLACE INTO envs (bot_id, venv_path, python_path, created_at, last_used) VALUES (?,?,?,?,?)',
                  (bot_id, venv_path, python_path, datetime.now().isoformat(), datetime.now().isoformat()))
        get_conn().commit()
        log_audit(0, bot_id, 'create_venv', f'تم إنشاء بيئة افتراضية في {venv_path}')
        return python_path
    except Exception as e:
        logger.error(f"فشل إنشاء البيئة الافتراضية للبوت {bot_id}: {e}")
        return None

def get_python_path(bot_id, project_path):
    c = get_cursor()
    c.execute('SELECT python_path FROM envs WHERE bot_id=?', (bot_id,))
    row = c.fetchone()
    if row and os.path.exists(row[0]):
        return row[0]
    else:
        return create_venv(bot_id, project_path)

# ============================================================
#                    دوال تثبيت المكتبات
# ============================================================

BUILTIN_MODULES = set(sys.builtin_module_names)

def analyze_imports(file_path):
    imports = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        pattern = re.compile(r'^\s*(?:import|from)\s+([a-zA-Z0-9_]+)', re.MULTILINE)
        for match in pattern.finditer(content):
            module = match.group(1)
            if module not in BUILTIN_MODULES and not module.startswith('_'):
                imports.add(module)
    except Exception as e:
        logger.warning(f"فشل تحليل imports في {file_path}: {e}")
    return list(imports)

def get_imports_from_file(file_path):
    """
    تحليل ملف واحد واستخراج المكتبات المستوردة (غير المضمنة).
    """
    return analyze_imports(file_path)

def install_libraries_in_venv(bot_id, project_path, libraries, chat_id=None, status_msg_id=None):
    python_path = get_python_path(bot_id, project_path)
    if not python_path:
        return {'status': 'error', 'message': 'تعذر إنشاء البيئة الافتراضية'}
    report = {'total': 0, 'installed': [], 'failed': [], 'already': []}
    total = len(libraries)
    report['total'] = total
    for i, lib in enumerate(libraries, 1):
        if chat_id and status_msg_id:
            progress = get_progress_bar((i/total)*100)
            send_msg(chat_id, f"[WAIT] تثبيت المكتبات...\n{progress}\n({i}/{total}) {lib}", edit=True, message_id=status_msg_id)
        try:
            result = subprocess.run(
                [python_path, '-m', 'pip', 'install', lib],
                capture_output=True, text=True, timeout=120, cwd=project_path
            )
            if result.returncode == 0:
                report['installed'].append(lib)
            else:
                check = subprocess.run([python_path, '-m', 'pip', 'show', lib], capture_output=True, timeout=10)
                if check.returncode == 0:
                    report['already'].append(lib)
                else:
                    report['failed'].append({'name': lib, 'reason': result.stderr[-200:]})
        except Exception as e:
            report['failed'].append({'name': lib, 'reason': str(e)})
    c = get_cursor()
    c.execute('UPDATE envs SET last_used=? WHERE bot_id=?', (datetime.now().isoformat(), bot_id))
    get_conn().commit()
    return report

def send_install_report(chat_id, report, title="تقرير تثبيت المكتبات"):
    content = (
        f"المجموع: <code>{report['total']}</code>\n"
        f"مثبتة: <code>{len(report['installed'])}</code>\n"
        f"مثبتة مسبقاً: <code>{len(report['already'])}</code>\n"
        f"فاشلة: <code>{len(report['failed'])}</code>"
    )
    if report['failed']:
        content += "\n\n<b>المكتبات الفاشلة:</b>\n"
        for item in report['failed']:
            content += f"└ {item['name']} — <i>{item['reason'][:100]}</i>\n"
    if report['installed']:
        content += "\n\n<b>المكتبات المثبتة:</b>\n"
        for lib in report['installed'][:20]:
            content += f"└ {lib}\n"
        if len(report['installed']) > 20:
            content += f"└ ... و {len(report['installed'])-20} أخرى"
    send_formatted_message(chat_id, "تقرير التثبيت", content)

# ============================================================
#                    دوال فحص المشروع
# ============================================================

def pre_run_check(project_path, main_file):
    issues = []
    if not os.path.exists(main_file):
        issues.append(f"الملف الرئيسي غير موجود: {main_file}")
    else:
        try:
            py_compile.compile(main_file, doraise=True)
        except py_compile.PyCompileError as e:
            issues.append(f"خطأ في الصياغة: {e}")
        if os.path.getsize(main_file) == 0:
            issues.append("الملف الرئيسي فارغ")
        token, _ = get_token_and_username(main_file)
        if token == "غير موجود":
            issues.append("لم يتم العثور على توكن في الملف")
    # فحص الملفات التالفة
    for root, _, files in os.walk(project_path):
        for f in files:
            if f.endswith('.py'):
                fp = os.path.join(root, f)
                try:
                    with open(fp, 'rb') as chk:
                        chk.read(1024)
                except:
                    issues.append(f"ملف تالف: {os.path.relpath(fp, project_path)}")
    return issues

# ============================================================
#                    دوال النسخ الاحتياطي
# ============================================================

def create_backup(bot_id, project_path, backup_type='manual'):
    backup_dir = f"backup_{bot_id}_{int(time.time())}"
    backup_path = os.path.join(os.getcwd(), backup_dir)
    try:
        shutil.copytree(project_path, backup_path, symlinks=False, ignore_dirs=['__pycache__', '.git', 'venv'])
        c = get_cursor()
        c.execute('INSERT INTO backup_logs (bot_id, backup_path, timestamp, status, details) VALUES (?,?,?,?,?)',
                  (bot_id, backup_path, datetime.now().isoformat(), 'success', f'نسخة {backup_type}'))
        get_conn().commit()
        cleanup_old_backups(bot_id)
        return backup_path
    except Exception as e:
        logger.error(f"فشل إنشاء النسخة الاحتياطية للبوت {bot_id}: {e}")
        return None

def cleanup_old_backups(bot_id):
    c = get_cursor()
    c.execute('SELECT id, backup_path FROM backup_logs WHERE bot_id=? ORDER BY timestamp DESC', (bot_id,))
    rows = c.fetchall()
    if len(rows) > BACKUP_CONFIG['max_backups']:
        for row in rows[BACKUP_CONFIG['max_backups']:]:
            try:
                if os.path.exists(row[1]):
                    shutil.rmtree(row[1], ignore_errors=True)
                c.execute('DELETE FROM backup_logs WHERE id=?', (row[0],))
                get_conn().commit()
            except Exception as e:
                logger.error(f"فشل حذف النسخة الاحتياطية القديمة {row[1]}: {e}")

def restore_backup(bot_id, backup_path, project_path):
    if not os.path.exists(backup_path):
        return False, "مسار النسخة غير موجود"
    main_files = [f for f in os.listdir(backup_path) if f.endswith('.py')]
    if not main_files:
        return False, "لا توجد ملفات بايثون في النسخة"
    try:
        if os.path.exists(project_path):
            shutil.rmtree(project_path, ignore_errors=True)
        shutil.copytree(backup_path, project_path)
        c = get_cursor()
        c.execute('UPDATE backup_logs SET status=?, details=? WHERE backup_path=?',
                  ('restored', f'تم الاسترجاع إلى {project_path}', backup_path))
        get_conn().commit()
        return True, "تم الاسترجاع بنجاح"
    except Exception as e:
        return False, str(e)

# ============================================================
#                    دوال الأرشفة
# ============================================================

def archive_project(bot_id, user_id):
    c = get_cursor()
    c.execute('SELECT file_path, pid, original_name FROM bots WHERE id=?', (bot_id,))
    res = c.fetchone()
    if not res:
        return False, "البوت غير موجود"
    path, pid, name = res
    if pid and is_process_running(pid):
        terminate_process(pid, force=True)
    archive_dir = os.path.join(os.getcwd(), 'archived')
    os.makedirs(archive_dir, exist_ok=True)
    archive_path = os.path.join(archive_dir, f"{name}_{bot_id}_{int(time.time())}")
    shutil.move(path, archive_path)
    c.execute('INSERT INTO archived_projects (bot_id, archive_path, archived_at, archived_by, original_path, status) VALUES (?,?,?,?,?,?)',
              (bot_id, archive_path, datetime.now().isoformat(), user_id, path, 'archived'))
    c.execute('DELETE FROM bots WHERE id=?', (bot_id,))
    get_conn().commit()
    log_audit(user_id, bot_id, 'archive', f'تمت أرشفة المشروع {name}')
    return True, f"تمت أرشفة المشروع {name}"

def restore_archived_project(archive_id, user_id):
    c = get_cursor()
    c.execute('SELECT bot_id, archive_path, original_path FROM archived_projects WHERE id=?', (archive_id,))
    res = c.fetchone()
    if not res:
        return False, "المشروع غير موجود في الأرشيف"
    bot_id, archive_path, original_path = res
    c.execute('SELECT id FROM bots WHERE id=?', (bot_id,))
    if c.fetchone():
        return False, "يوجد مشروع بنفس المعرف، قم بحذفه أولاً"
    shutil.move(archive_path, original_path)
    c.execute('INSERT INTO bots (id, user_id, file_path, original_name, main_file, pid) SELECT id, user_id, ?, original_name, main_file, 0 FROM archived_projects WHERE id=?',
              (original_path, archive_id))
    c.execute('UPDATE archived_projects SET status=? WHERE id=?', ('restored', archive_id))
    get_conn().commit()
    log_audit(user_id, bot_id, 'restore_archive', f'تمت استعادة المشروع من الأرشيف')
    return True, "تمت الاستعادة بنجاح"

# ============================================================
#                    دوال الجدولة
# ============================================================

def calculate_next_run(schedule_type, schedule_time):
    now = datetime.now()
    if schedule_type == 'once':
        return schedule_time
    elif schedule_type == 'daily':
        hour, minute = map(int, schedule_time.split(':'))
        next_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_time <= now:
            next_time += timedelta(days=1)
        return next_time.isoformat()
    elif schedule_type == 'hourly':
        minute = int(schedule_time)
        next_time = now.replace(minute=minute, second=0, microsecond=0)
        if next_time <= now:
            next_time += timedelta(hours=1)
        return next_time.isoformat()
    else:
        return None

def schedule_task(bot_id, action, schedule_type, schedule_time, created_by):
    next_run = calculate_next_run(schedule_type, schedule_time)
    if not next_run:
        return False, "نوع الجدولة غير صحيح"
    c = get_cursor()
    c.execute('INSERT INTO schedules (bot_id, action, schedule_type, schedule_time, next_run, enabled, created_by, created_at) VALUES (?,?,?,?,?,?,?,?)',
              (bot_id, action, schedule_type, schedule_time, next_run, 1, created_by, datetime.now().isoformat()))
    get_conn().commit()
    log_audit(created_by, bot_id, 'schedule_add', f'جدولة {action} في {schedule_time}')
    return True, "تمت إضافة الجدولة"

def run_scheduled_tasks():
    now = datetime.now().isoformat()
    c = get_cursor()
    c.execute('SELECT id, bot_id, action FROM schedules WHERE enabled=1 AND next_run <= ?', (now,))
    tasks = c.fetchall()
    for task_id, bot_id, action in tasks:
        if action == 'stop':
            c.execute('SELECT pid FROM bots WHERE id=?', (bot_id,))
            res = c.fetchone()
            if res and res[0]:
                terminate_process(res[0], force=True)
                c.execute('UPDATE bots SET pid=0 WHERE id=?', (bot_id,))
                get_conn().commit()
                log_audit(0, bot_id, 'schedule_stop', 'تم الإيقاف بواسطة الجدولة')
                send_notification(ADMIN_ID, f"[INFO] تم إيقاف البوت {bot_id} بواسطة الجدولة", 'info')
        elif action == 'start':
            # سيتم التعامل معه في run_bot_process
            pass
        elif action == 'restart':
            c.execute('SELECT pid FROM bots WHERE id=?', (bot_id,))
            res = c.fetchone()
            if res and res[0]:
                terminate_process(res[0], force=True)
                c.execute('UPDATE bots SET pid=0 WHERE id=?', (bot_id,))
                get_conn().commit()
        # تحديث next_run
        c.execute('SELECT schedule_type, schedule_time FROM schedules WHERE id=?', (task_id,))
        row = c.fetchone()
        if row:
            next_run = calculate_next_run(row[0], row[1])
            c.execute('UPDATE schedules SET next_run=? WHERE id=?', (next_run, task_id))
        get_conn().commit()

# ============================================================
#                    دوال حدود الموارد
# ============================================================

def set_resource_limits(bot_id, limits):
    c = get_cursor()
    c.execute('INSERT OR REPLACE INTO resource_limits (bot_id, cpu_percent, ram_mb, storage_mb, max_processes, updated_at) VALUES (?,?,?,?,?,?)',
              (bot_id, limits.get('cpu_percent', 80), limits.get('ram_mb', 512), limits.get('storage_mb', 1024),
               limits.get('max_processes', 1), datetime.now().isoformat()))
    get_conn().commit()
    log_audit(0, bot_id, 'set_limits', f'تم تعيين حدود: {limits}')

def get_resource_limits(bot_id):
    c = get_cursor()
    c.execute('SELECT * FROM resource_limits WHERE bot_id=?', (bot_id,))
    return c.fetchone()

def check_resource_limits(bot_id, pid):
    limits = get_resource_limits(bot_id)
    if not limits:
        return True, "لا توجد حدود"
    try:
        proc = psutil.Process(pid)
        cpu = proc.cpu_percent(interval=0.1)
        mem = proc.memory_info().rss / (1024 * 1024)
        c = get_cursor()
        c.execute('SELECT file_path FROM bots WHERE id=?', (bot_id,))
        res = c.fetchone()
        storage = 0
        if res:
            path = res[0]
            if os.path.exists(path):
                if os.path.isdir(path):
                    storage = sum(os.path.getsize(os.path.join(dirpath, f)) for dirpath, _, filenames in os.walk(path) for f in filenames) / (1024*1024)
                else:
                    storage = os.path.getsize(path) / (1024*1024)
        if cpu > limits['cpu_percent']:
            return False, f"تجاوز CPU: {cpu:.1f}% > {limits['cpu_percent']}%"
        if mem > limits['ram_mb']:
            return False, f"تجاوز RAM: {mem:.1f} MB > {limits['ram_mb']} MB"
        if storage > limits['storage_mb']:
            return False, f"تجاوز التخزين: {storage:.1f} MB > {limits['storage_mb']} MB"
        return True, "ضمن الحدود"
    except Exception as e:
        return True, f"خطأ في الفحص: {e}"

# ============================================================
#                    دوال Health Check
# ============================================================

def health_check(bot_id, pid, project_path):
    start_time = time.time()
    status = 'ok'
    details = ''
    try:
        if not is_process_running(pid):
            status = 'stopped'
            details = 'العملية متوقفة'
        else:
            c = get_cursor()
            c.execute('SELECT main_file FROM bots WHERE id=?', (bot_id,))
            res = c.fetchone()
            if res:
                main_file = os.path.join(project_path, res[0]) if res[0] else project_path
                token, _ = get_token_and_username(main_file)
                if token and token != "غير موجود":
                    try:
                        r = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=5)
                        if r.status_code != 200:
                            status = 'error'
                            details = f'API غير مستجيب: {r.status_code}'
                    except:
                        status = 'error'
                        details = 'تعذر الاتصال بـ API'
    except Exception as e:
        status = 'error'
        details = str(e)
    response_time = time.time() - start_time
    c = get_cursor()
    c.execute('INSERT INTO health_checks (bot_id, check_time, status, response_time, details) VALUES (?,?,?,?,?)',
              (bot_id, datetime.now().isoformat(), status, response_time, details))
    get_conn().commit()
    if status != 'ok':
        send_notification(ADMIN_ID, f"[WARN] البوت {bot_id} غير صحي: {details}", 'warning')
    return status, details

# ============================================================
#                    دوال الطرفية
# ============================================================

def execute_terminal_command_safe(command, timeout=60):
    for forbidden in FORBIDDEN_COMMANDS:
        if forbidden in command:
            return "", False, f"الأمر '{forbidden}' محظور"
    try:
        process = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, executable='/bin/bash'
        )
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            success = (process.returncode == 0)
            output = stdout if success else stderr
            if not output.strip():
                output = "(لا يوجد ناتج)"
            return output, success, None
        except subprocess.TimeoutExpired:
            process.kill()
            return "", False, f"انتهت المهلة ({timeout} ثانية)"
    except Exception as e:
        return "", False, str(e)

def log_terminal_command(user_id, command, success=True, output_preview=""):
    try:
        with open(TERMINAL_LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now().isoformat()} | USER:{user_id} | SUCCESS:{success} | CMD:{command[:200]} | OUT:{output_preview[:100]}\n")
    except:
        pass

# ============================================================
#                    دوال البحث المتقدم
# ============================================================

def advanced_search(query, search_type='all'):
    results = {}
    c = get_cursor()
    if search_type in ('all', 'bots'):
        c.execute("SELECT id, original_name, user_id, pid FROM bots WHERE original_name LIKE ? OR id LIKE ?",
                  (f"%{query}%", f"%{query}%"))
        results['bots'] = c.fetchall()
    if search_type in ('all', 'users'):
        c.execute("SELECT user_id, first_name, username FROM users WHERE user_id LIKE ? OR first_name LIKE ? OR username LIKE ?",
                  (f"%{query}%", f"%{query}%", f"%{query}%"))
        results['users'] = c.fetchall()
    if search_type in ('all', 'logs'):
        c.execute("SELECT id, timestamp, user_id, bot_id, action, details FROM audit_log WHERE action LIKE ? OR details LIKE ? ORDER BY timestamp DESC LIMIT 50",
                  (f"%{query}%", f"%{query}%"))
        results['logs'] = c.fetchall()
    return results

# ============================================================
#                    دوال الإحصائيات المتقدمة
# ============================================================

def get_advanced_stats():
    stats = {}
    stats['total_users'] = get_total_users()
    stats['banned'] = get_banned_count()
    stats['active'] = get_active_users()
    c = get_cursor()
    c.execute('SELECT COUNT(*) FROM bots')
    stats['total_bots'] = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM bots WHERE pid != 0')
    stats['running_bots'] = c.fetchone()[0]
    stats['stopped_bots'] = stats['total_bots'] - stats['running_bots']
    total_size = 0
    c.execute('SELECT file_path FROM bots')
    for (path,) in c.fetchall():
        if os.path.exists(path):
            try:
                if os.path.isdir(path):
                    size = sum(os.path.getsize(os.path.join(dirpath, f)) for dirpath, _, filenames in os.walk(path) for f in filenames)
                else:
                    size = os.path.getsize(path)
                total_size += size
            except:
                pass
    stats['storage_gb'] = total_size // (1024**3)
    c.execute('SELECT COUNT(*) FROM audit_log')
    stats['total_actions'] = c.fetchone()[0]
    c.execute('SELECT timestamp, user_id, bot_id, action FROM audit_log ORDER BY id DESC LIMIT 10')
    stats['recent_actions'] = c.fetchall()
    return stats

# ============================================================
#                    دوال إدارة المشرفين والصلاحيات
# ============================================================

def init_permissions():
    c = get_cursor()
    c.execute('INSERT OR IGNORE INTO admins (user_id, permissions, added_by, added_at) VALUES (?, ?, ?, ?)',
              (ADMIN_ID, json.dumps({
                  'manage_users': 1, 'manage_bots': 1, 'view_stats': 1,
                  'manage_files': 1, 'use_terminal': 1, 'manage_admins': 1
              }), ADMIN_ID, datetime.now().isoformat()))
    get_conn().commit()

def check_permission(user_id, permission):
    if user_id == ADMIN_ID:
        return True
    c = get_cursor()
    c.execute('SELECT permissions FROM admins WHERE user_id=?', (user_id,))
    row = c.fetchone()
    if not row:
        return False
    perms = json.loads(row[0])
    return perms.get(permission, 0) == 1

def add_admin(user_id, permissions, added_by):
    c = get_cursor()
    c.execute('INSERT OR REPLACE INTO admins (user_id, permissions, added_by, added_at) VALUES (?, ?, ?, ?)',
              (user_id, json.dumps(permissions), added_by, datetime.now().isoformat()))
    get_conn().commit()

def remove_admin(user_id):
    c = get_cursor()
    c.execute('DELETE FROM admins WHERE user_id=?', (user_id,))
    get_conn().commit()

def get_admins_list():
    c = get_cursor()
    c.execute('SELECT user_id, permissions, added_by, added_at FROM admins')
    return c.fetchall()

# ============================================================
#                    دوال الإشعارات
# ============================================================

def send_notification(user_id, message, notif_type='info'):
    if user_id == ADMIN_ID:
        try:
            bot.send_message(user_id, f"{EMOJI['notif']} {message}")
        except:
            pass
        return
    c = get_cursor()
    c.execute('SELECT enabled FROM notifications_settings WHERE user_id=?', (user_id,))
    row = c.fetchone()
    if row and row[0] == 1:
        try:
            bot.send_message(user_id, f"{EMOJI['notif']} {message}")
        except:
            pass

def toggle_notifications(user_id, enabled):
    c = get_cursor()
    c.execute('INSERT OR REPLACE INTO notifications_settings (user_id, enabled, last_modified) VALUES (?, ?, ?)',
              (user_id, 1 if enabled else 0, datetime.now().isoformat()))
    get_conn().commit()

# ============================================================
#                    دوال مراقبة الموارد
# ============================================================

def monitor_resources():
    while True:
        try:
            now = time.time()
            cpu = psutil.cpu_percent(interval=1)
            resource_usage['cpu'] = cpu
            if cpu >= RESOURCE_MONITOR_CONFIG['cpu_percent']:
                if now - resource_last_alert['cpu'] > RESOURCE_MONITOR_CONFIG['cooldown_seconds']:
                    resource_last_alert['cpu'] = now
                    msg = f"[WARN] تنبيه استهلاك CPU: {cpu:.1f}% (الحد: {RESOURCE_MONITOR_CONFIG['cpu_percent']}%)"
                    send_admin_message_safe(msg)
                    send_notification(ADMIN_ID, msg, 'warning')
            ram = psutil.virtual_memory()
            resource_usage['ram'] = ram.percent
            if ram.percent >= RESOURCE_MONITOR_CONFIG['ram_percent']:
                if now - resource_last_alert['ram'] > RESOURCE_MONITOR_CONFIG['cooldown_seconds']:
                    resource_last_alert['ram'] = now
                    msg = f"[WARN] تنبيه استهلاك RAM: {ram.percent:.1f}% (الحد: {RESOURCE_MONITOR_CONFIG['ram_percent']}%)"
                    send_admin_message_safe(msg)
                    send_notification(ADMIN_ID, msg, 'warning')
            disk = shutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            resource_usage['disk'] = disk_percent
            if disk_percent >= RESOURCE_MONITOR_CONFIG['disk_percent']:
                if now - resource_last_alert['disk'] > RESOURCE_MONITOR_CONFIG['cooldown_seconds']:
                    resource_last_alert['disk'] = now
                    msg = f"[WARN] تنبيه استهلاك القرص: {disk_percent:.1f}% (الحد: {RESOURCE_MONITOR_CONFIG['disk_percent']}%)"
                    send_admin_message_safe(msg)
                    send_notification(ADMIN_ID, msg, 'warning')
        except Exception as e:
            logger.error(f"خطأ في مراقبة الموارد: {e}")
        time.sleep(RESOURCE_MONITOR_CONFIG['check_interval'])

def send_admin_message_safe(text):
    try:
        bot.send_message(ADMIN_ID, f"{EMOJI['warning']} {text}", parse_mode='HTML')
    except:
        pass

# ============================================================
#                    دوال السجلات (Logs)
# ============================================================

def log_audit(user_id, bot_id, action, details=""):
    try:
        c = get_cursor()
        c.execute('INSERT INTO audit_log (timestamp, user_id, bot_id, action, details) VALUES (?,?,?,?,?)',
                  (datetime.now().isoformat(), user_id, bot_id, action, details))
        get_conn().commit()
    except Exception as e:
        logger.error(f"فشل تسجيل audit: {e}")

# ============================================================
#                    دوال إنهاء العملية وحذف الملفات
# ============================================================

def terminate_process(pid, force=False):
    if not pid:
        return True
    try:
        pgid = os.getpgid(pid)
        if force:
            os.killpg(pgid, signal.SIGKILL)
        else:
            os.killpg(pgid, signal.SIGTERM)
        time.sleep(0.5)
        return True
    except ProcessLookupError:
        return True
    except Exception as e:
        logger.error(f"فشل إنهاء العملية {pid}: {e}")
        return False

def delete_path_safely(path):
    if not os.path.exists(path):
        return True
    for attempt in range(3):
        try:
            if os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
            else:
                os.remove(path)
            return True
        except Exception as e:
            logger.warning(f"محاولة حذف {path} رقم {attempt+1} فشلت: {e}")
            time.sleep(0.5)
    return False

# ============================================================
#                    دوال تشغيل البوت (محسّنة)
# ============================================================

def check_syntax(file_path):
    try:
        py_compile.compile(file_path, doraise=True)
        return True
    except py_compile.PyCompileError as e:
        raise SyntaxError(f"خطأ في الصياغة: {e}")

def run_bot_process(bot_file, cwd=None, chat_id=None, status_msg_id=None, bot_id=None):
    if not os.path.isfile(bot_file):
        raise FileNotFoundError(f"الملف غير موجود: {bot_file}")
    if cwd is None:
        cwd = os.path.dirname(bot_file)
    if not os.path.isdir(cwd):
        raise NotADirectoryError(f"الدليل غير موجود: {cwd}")
    # فحص المشروع
    issues = pre_run_check(cwd, bot_file)
    if issues:
        raise Exception(f"مشاكل في المشروع: {', '.join(issues)}")
    # البيئة الافتراضية
    python_path = get_python_path(bot_id, cwd) if bot_id else sys.executable
    # تثبيت المكتبات
    if chat_id and status_msg_id:
        send_msg(chat_id, "[WAIT] جاري تثبيت المكتبات...", edit=True, message_id=status_msg_id)
    
    libs = []
    req_path = os.path.join(cwd, 'requirements.txt')
    if os.path.exists(req_path):
        with open(req_path, 'r') as f:
            libs = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        logger.info(f"تم تحميل المكتبات من requirements.txt: {libs}")
    else:
        # تحليل الملف الرئيسي فقط (وليس كل المشروع) لاستخراج المكتبات المستوردة
        imports = get_imports_from_file(bot_file)
        libs = list(set(imports))
        logger.info(f"تم تحليل الاستيرادات من الملف الرئيسي: {libs}")
    
    if libs:
        report = install_libraries_in_venv(bot_id, cwd, libs, chat_id, status_msg_id)
        if chat_id and status_msg_id:
            send_install_report(chat_id, report, "تقرير تثبيت المكتبات")
    else:
        if chat_id and status_msg_id:
            send_msg(chat_id, "[INFO] لا توجد مكتبات إضافية لتثبيتها.", edit=True, message_id=status_msg_id)
    
    # فحص الصياغة
    try:
        check_syntax(bot_file)
    except SyntaxError as e:
        raise
    # تشغيل
    log_path = os.path.join(cwd, os.path.basename(bot_file) + '.log')
    try:
        log_f = open(log_path, 'ab')
        log_f.write(f"\n----- تشغيل جديد {datetime.now().isoformat()} -----\n".encode('utf-8'))
        log_f.flush()
        proc = subprocess.Popen(
            [python_path, bot_file],
            start_new_session=True,
            stdout=log_f,
            stderr=subprocess.STDOUT,
            cwd=cwd
        )
        log_f.close()
        return proc.pid
    except Exception as e:
        logger.error(f"فشل تشغيل {bot_file}: {e}")
        raise

def tail_log(log_path, n_lines=15, max_chars=800):
    try:
        with open(log_path, 'rb') as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            block = min(size, 8000)
            f.seek(size - block)
            data = f.read().decode('utf-8', errors='replace')
        text = "\n".join(data.splitlines()[-n_lines:])
        return text[-max_chars:] if len(text) > max_chars else text
    except Exception:
        return ""

# ============================================================
#                    دوال إعادة التشغيل التلقائي
# ============================================================

restart_attempts = {}
restart_lock = threading.Lock()

def log_restart_attempt(bot_id):
    now = time.time()
    with restart_lock:
        if bot_id not in restart_attempts:
            restart_attempts[bot_id] = []
        restart_attempts[bot_id].append(now)
        cutoff = now - RESTART_CONFIG['cooldown_minutes'] * 60
        restart_attempts[bot_id] = [t for t in restart_attempts[bot_id] if t > cutoff]

def get_recent_restart_count(bot_id):
    now = time.time()
    cutoff = now - RESTART_CONFIG['cooldown_minutes'] * 60
    with restart_lock:
        if bot_id not in restart_attempts:
            return 0
        return sum(1 for t in restart_attempts[bot_id] if t > cutoff)

# ============================================================
#                    مراقب البوتات (معدّل)
# ============================================================

def monitor_bots():
    while True:
        try:
            c = get_cursor()
            c.execute('SELECT id, file_path, pid, main_file, user_id, original_name FROM bots')
            bots = c.fetchall()
            for bot_id, file_path, pid, main_file, user_id, orig_name in bots:
                # Health Check
                if pid and is_process_running(pid):
                    health_check(bot_id, pid, file_path)
                    ok, msg = check_resource_limits(bot_id, pid)
                    if not ok:
                        send_notification(user_id, f"[WARN] البوت {orig_name} تجاوز الحدود: {msg}", 'warning')
                        terminate_process(pid, force=True)
                        c.execute('UPDATE bots SET pid=0 WHERE id=?', (bot_id,))
                        get_conn().commit()
                        log_audit(0, bot_id, 'resource_limit', f'تم إيقاف البوت بسبب {msg}')
                        continue
                # إعادة التشغيل التلقائي
                if pid and not is_process_running(pid):
                    attempts = get_recent_restart_count(bot_id)
                    if attempts >= RESTART_CONFIG['max_attempts']:
                        c.execute('UPDATE bots SET pid=0 WHERE id=?', (bot_id,))
                        get_conn().commit()
                        send_notification(user_id, f"[ERROR] البوت {orig_name} توقف بعد {attempts} محاولات إعادة تشغيل", 'error')
                        log_audit(0, bot_id, 'restart_failed', f'توقف بعد {attempts} محاولات')
                        continue
                    bot_file = os.path.join(file_path, main_file) if main_file else file_path
                    bot_file = os.path.abspath(bot_file)
                    if os.path.exists(bot_file):
                        try:
                            python_path = get_python_path(bot_id, file_path) or sys.executable
                            log_path = os.path.join(file_path, os.path.basename(bot_file) + '.log')
                            log_f = open(log_path, 'ab')
                            log_f.write(f"\n----- إعادة تشغيل {datetime.now().isoformat()} -----\n".encode('utf-8'))
                            log_f.flush()
                            proc = subprocess.Popen(
                                [python_path, bot_file],
                                start_new_session=True,
                                stdout=log_f,
                                stderr=subprocess.STDOUT,
                                cwd=file_path
                            )
                            log_f.close()
                            c.execute('UPDATE bots SET pid=? WHERE id=?', (proc.pid, bot_id))
                            get_conn().commit()
                            log_restart_attempt(bot_id)
                            send_notification(user_id, f"[INFO] تم إعادة تشغيل البوت {orig_name} تلقائياً", 'info')
                            log_audit(0, bot_id, 'auto_restart', 'إعادة تشغيل تلقائي')
                        except Exception as e:
                            logger.error(f"فشل إعادة تشغيل البوت {bot_id}: {e}")
                            send_notification(ADMIN_ID, f"[ERROR] فشل إعادة تشغيل البوت {orig_name}: {e}", 'error')
        except Exception as e:
            logger.error(f"Monitor error: {e}")
        time.sleep(30)

# ============================================================
#                    دوال مدير الملفات المتقدم (محسّن)
# ============================================================

def list_directory_advanced(path, relative_to=None, sort_by='name', sort_order='asc', filter_type='all'):
    items = []
    try:
        for item in os.listdir(path):
            full = os.path.join(path, item)
            is_dir = os.path.isdir(full)
            # تصفية حسب النوع
            if filter_type == 'dirs' and not is_dir:
                continue
            if filter_type == 'files' and is_dir:
                continue
            size = os.path.getsize(full) if not is_dir else 0
            mtime = os.path.getmtime(full)
            perms = oct(os.stat(full).st_mode)[-3:]
            items.append({
                'name': item,
                'is_dir': is_dir,
                'size': size,
                'path': full,
                'relative': os.path.relpath(full, relative_to) if relative_to else full,
                'mtime': datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M'),
                'perms': perms,
                'timestamp': mtime,
            })
        # فرز
        reverse = (sort_order == 'desc')
        if sort_by == 'name':
            items.sort(key=lambda x: x['name'].lower(), reverse=reverse)
        elif sort_by == 'size':
            items.sort(key=lambda x: x['size'], reverse=reverse)
        elif sort_by == 'mtime':
            items.sort(key=lambda x: x['timestamp'], reverse=reverse)
        elif sort_by == 'type':
            items.sort(key=lambda x: (not x['is_dir'], x['name'].lower()), reverse=reverse)
        return items
    except Exception as e:
        logger.error(f"خطأ في قراءة المجلد {path}: {e}")
        return []

def send_file_manager_advanced(chat_id, user_id, bot_id, current_path, message_id=None, page=0, sort_by='name', sort_order='asc', filter_type='all'):
    if not check_permission(user_id, 'manage_files'):
        send_formatted_message(chat_id, "صلاحية ممنوعة", "ليس لديك صلاحية للوصول إلى مدير الملفات.", footer="تواصل مع المطور.")
        return
    c = get_cursor()
    c.execute('SELECT file_path FROM bots WHERE id=?', (bot_id,))
    res = c.fetchone()
    if not res:
        send_formatted_message(chat_id, "خطأ", "البوت غير موجود.", footer="تأكد من المعرف.")
        return
    bot_path = res[0]
    if not current_path.startswith(bot_path):
        current_path = bot_path
    # تحديث الجلسة
    session = get_user_session(user_id)
    session['current_path'] = current_path
    session['current_bot'] = bot_id
    # جلب العناصر مع الفرز والتصفية
    items = list_directory_advanced(current_path, bot_path, sort_by, sort_order, filter_type)
    total_items = len(items)
    per_page = 10
    page_items, total_pages, start, end = paginate_items(items, page, per_page)
    
    content = f"المجلد: <code>{current_path}</code>\n"
    content += f"عدد العناصر: {total_items} (صفحة {page+1}/{total_pages})\n\n"
    if not items:
        content += "<i>المجلد فارغ</i>"
    else:
        for item in page_items:
            icon = "مجلد" if item['is_dir'] else "ملف"
            size_str = format_size(item['size'])
            content += f"{icon} {item['name']} <code>({size_str})</code> [{item['perms']}] {item['mtime']}\n"
    
    buttons = []
    # أزرار الفرز والتصفية
    sort_row = []
    sort_row.append(create_btn(f"فرز: {sort_by}", callback=f"fm_sort_{bot_id}_{sort_by}_{sort_order}", color='purple'))
    sort_row.append(create_btn(f"ترتيب: {'تصاعدي' if sort_order=='asc' else 'تنازلي'}", callback=f"fm_order_{bot_id}_{sort_by}_{sort_order}", color='purple'))
    buttons.append(sort_row)
    filter_row = []
    filter_row.append(create_btn(f"فلتر: {filter_type}", callback=f"fm_filter_{bot_id}_{filter_type}", color='purple'))
    buttons.append(filter_row)
    # أزرار التنقل
    nav_row = []
    if page > 0:
        nav_row.append(create_btn("السابق", callback=f"fm_page_{bot_id}_{page-1}_{sort_by}_{sort_order}_{filter_type}", color='blue'))
    if page < total_pages - 1:
        nav_row.append(create_btn("التالي", callback=f"fm_page_{bot_id}_{page+1}_{sort_by}_{sort_order}_{filter_type}", color='blue'))
    if nav_row:
        buttons.append(nav_row)
    # أزرار العمليات
    row = []
    row.append(create_btn("تحديث", callback=f"fm_refresh_{bot_id}_{os.path.relpath(current_path, bot_path)}", color='blue'))
    row.append(create_btn("أعلى", callback=f"fm_open_{bot_id}_{os.path.relpath(os.path.dirname(current_path), bot_path)}" if current_path != bot_path else "noop", color='blue'))
    buttons.append(row)
    buttons.append([
        create_btn("مجلد جديد", callback=f"fm_newdir_{bot_id}_{os.path.relpath(current_path, bot_path)}", color='purple'),
        create_btn("رفع ملف", callback=f"fm_upload_{bot_id}_{os.path.relpath(current_path, bot_path)}", color='green')
    ])
    buttons.append([
        create_btn("ضغط", callback=f"fm_compress_{bot_id}_{os.path.relpath(current_path, bot_path)}", color='orange'),
        create_btn("فك ضغط", callback=f"fm_extract_{bot_id}_{os.path.relpath(current_path, bot_path)}", color='purple')
    ])
    buttons.append([
        create_btn("بحث", callback=f"fm_search_{bot_id}_{os.path.relpath(current_path, bot_path)}", color='blue'),
        create_btn("معلومات", callback=f"fm_info_{bot_id}_{os.path.relpath(current_path, bot_path)}", color='blue')
    ])
    # أزرار الملفات (عرض أول 10 ملفات فقط)
    for item in page_items:
        if item['is_dir']:
            buttons.append([create_btn(f"مجلد {item['name']}", callback=f"fm_open_{bot_id}_{item['relative']}", color='purple')])
        else:
            buttons.append([
                create_btn(f"ملف {item['name']}", callback=f"fm_file_{bot_id}_{item['relative']}", color='blue'),
                create_btn("حذف", callback=f"fm_delete_{bot_id}_{item['relative']}", color='red'),
                create_btn("إعادة تسمية", callback=f"fm_rename_{bot_id}_{item['relative']}", color='orange'),
                create_btn("نسخ", callback=f"fm_copy_{bot_id}_{item['relative']}", color='green')
            ])
    buttons.append([create_btn("رجوع", callback=f"manage_{bot_id}", color='blue')])
    send_formatted_message(chat_id, "مدير الملفات المتقدم", content, buttons=buttons, edit=(message_id is not None), message_id=message_id, footer="اختر ملفاً أو مجلداً للتعامل معه. استخدم أزرار الفرز والتصفية.")

# ============================================================
#                    دوال محرر الأكواد المتقدم (محسّن)
# ============================================================

def edit_file_advanced(chat_id, user_id, bot_id, file_path, content=None, message_id=None):
    if not check_permission(user_id, 'manage_files'):
        send_formatted_message(chat_id, "صلاحية ممنوعة", "ليس لديك صلاحية لتعديل الملفات.", footer="تواصل مع المطور.")
        return
    c = get_cursor()
    c.execute('SELECT file_path FROM bots WHERE id=?', (bot_id,))
    res = c.fetchone()
    if not res:
        send_formatted_message(chat_id, "خطأ", "البوت غير موجود.", footer="تأكد من المعرف.")
        return
    bot_path = res[0]
    if not file_path.startswith(bot_path):
        send_formatted_message(chat_id, "خطأ", "مسار غير صالح.", footer="تأكد من المسار.")
        return
    if content is None:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            send_formatted_message(chat_id, "خطأ في القراءة", f"<code>{html.escape(str(e))}</code>", footer="تأكد من صلاحيات الملف.")
            return
    lines = content.split('\n')
    line_count = len(lines)
    # عرض مع ترقيم الأسطر وتلوين بسيط (HTML)
    max_line = len(str(line_count))
    numbered = ""
    for i, line in enumerate(lines, 1):
        num = str(i).rjust(max_line)
        # تلوين بسيط للكلمات المفتاحية
        highlighted = html.escape(line)
        for kw in ['import', 'def', 'class', 'if', 'else', 'for', 'while', 'return', 'try', 'except']:
            highlighted = highlighted.replace(kw, f'<b>{kw}</b>')
        numbered += f"{num}: {highlighted}\n"
    preview = numbered[:4000]
    if len(numbered) > 4000:
        preview += "\n... (المحتوى أطول، سيتم إرساله كامل عند الحفظ)"
    content_text = (
        f"الملف: <code>{os.path.basename(file_path)}</code>\n"
        f"المسار: <code>{file_path}</code>\n"
        f"عدد الأسطر: {line_count}\n\n"
        f"<pre>{preview}</pre>"
    )
    buttons = [
        [create_btn("تعديل", callback=f"editor_edit_{bot_id}_{os.path.relpath(file_path, bot_path)}", color='orange')],
        [create_btn("حفظ", callback=f"editor_save_{bot_id}_{os.path.relpath(file_path, bot_path)}", color='green')],
        [create_btn("فحص Syntax", callback=f"editor_check_{bot_id}_{os.path.relpath(file_path, bot_path)}", color='purple')],
        [create_btn("بحث واستبدال", callback=f"editor_search_{bot_id}_{os.path.relpath(file_path, bot_path)}", color='blue')],
        [create_btn("انتقال إلى سطر", callback=f"editor_goto_{bot_id}_{os.path.relpath(file_path, bot_path)}", color='orange')],
        [create_btn("رجوع", callback=f"fm_open_{bot_id}_{os.path.relpath(os.path.dirname(file_path), bot_path)}", color='blue')]
    ]
    send_formatted_message(chat_id, "محرر الأكواد المتقدم", content_text, buttons=buttons, edit=(message_id is not None), message_id=message_id, footer="استخدم الأزرار للتحكم في الملف.")

# ============================================================
#                    دوال العرض (لوحات التحكم) - محسّنة
# ============================================================

def show_admin_panel(chat_id, message_id=None, edit=False):
    buttons = [
        [create_btn('إحصائيات البوتات', callback='admin_stats', color='orange')],
        [create_btn('إحصائيات الخادم', callback='server_stats', color='orange')],
        [create_btn('إحصائيات متقدمة', callback='advanced_stats', color='purple')],
        [create_btn('إدارة الحظر', callback='ban_management', color='red')],
        [create_btn('إذاعة', callback='broadcast_start', color='purple')],
        [create_btn('إحصائيات المستخدمين', callback='user_stats', color='green')],
        [create_btn('الطرفية', callback='terminal_start', color='orange')],
        [create_btn('إدارة المشرفين', callback='admin_management', color='blue')],
        [create_btn('بحث متقدم', callback='search_panel', color='cyan')],
        [create_btn('إعدادات الإشعارات', callback='notif_settings', color='yellow')],
        [create_btn('المشاريع المؤرشفة', callback='archived_list', color='grey')],
        [create_btn('لوحة المستخدم', callback='user_panel', color='green')],  # زر للذهاب إلى لوحة المستخدم
    ]
    content = "مرحباً بك في لوحة المطور. اختر إحدى الأدوات الإدارية."
    send_formatted_message(chat_id, "لوحة المطور", content, buttons=buttons, edit=edit, message_id=message_id, footer="جميع الأزرار تفاعلية.")

def show_user_panel(chat_id, message_id=None, edit=False):
    buttons = [
        [create_btn('رفع ملف .py', callback='upload', color='green'), create_btn('رفع ZIP', callback='upload_zip', color='green')],
        [create_btn('قائمة بوتاتي', callback='list_my_bots', color='blue')],
        [create_btn('تثبيت مكتبة', callback='install_library', color='purple')],
        [create_btn('قناة المطور', url=DEVELOPER_CHANNEL)],
        # إذا كان المستخدم مطوراً، نضيف زر للرجوع إلى لوحة المطور
    ]
    # إذا كان المستخدم مطوراً، نضيف زر الرجوع إلى لوحة المطور
    if chat_id == ADMIN_ID:
        buttons.append([create_btn('رجوع إلى لوحة المطور', callback='main_menu', color='blue')])
    content = "مرحباً بك في لوحة المستخدم. يمكنك إدارة بوتاتك بسهولة."
    send_formatted_message(chat_id, "لوحة المستخدم", content, buttons=buttons, edit=edit, message_id=message_id, footer="اختر الإجراء المناسب.")

# ============================================================
#                    دالة إدارة البوت (مع تصحيح المسار)
# ============================================================

def display_bot_management(chat_id, user_id, bot_id, message_id=None, edit=False):
    c = get_cursor()
    c.execute('SELECT original_name, file_path, pid, main_file, user_id FROM bots WHERE id=?', (bot_id,))
    res = c.fetchone()
    if not res:
        send_formatted_message(chat_id, "خطأ", "البوت غير موجود.", footer="تأكد من المعرف.")
        return
    name, path, pid, main_file, owner = res
    if user_id != owner and user_id != ADMIN_ID:
        send_formatted_message(chat_id, "صلاحية ممنوعة", "ليس لديك صلاحية لهذا البوت.", footer="تواصل مع المطور.")
        return

    # التأكد من أن path هو مجلد
    if not os.path.isdir(path):
        # إذا كان path ملفاً، نستنتج المجلد ونعدل main_file إذا لزم الأمر
        dir_path = os.path.dirname(path)
        if os.path.isdir(dir_path):
            # نحدّث قاعدة البيانات لتصحيح المسار
            c.execute('UPDATE bots SET file_path=? WHERE id=?', (dir_path, bot_id))
            get_conn().commit()
            path = dir_path
            if main_file is None:
                # إذا لم يكن main_file محدداً، نستخدم اسم الملف الأصلي
                main_file = os.path.basename(path)
                c.execute('UPDATE bots SET main_file=? WHERE id=?', (main_file, bot_id))
                get_conn().commit()
        else:
            send_formatted_message(chat_id, "خطأ", "مسار البوت غير صحيح (ليس مجلداً).", footer="تحقق من التثبيت.")
            return

    # إذا كان main_file لا يزال None، حاول البحث عن ملف .py وحيد في المجلد
    if main_file is None:
        py_files = [f for f in os.listdir(path) if f.endswith('.py')]
        if py_files:
            main_file = py_files[0]
            c.execute('UPDATE bots SET main_file=? WHERE id=?', (main_file, bot_id))
            get_conn().commit()
        else:
            send_formatted_message(chat_id, "خطأ", "لا يوجد ملف .py رئيسي في هذا المشروع.", footer="أعد رفع المشروع.")
            return

    running = is_process_running(pid)
    status = f"{EMOJI['running']} يعمل" if running else f"{EMOJI['stopped']} متوقف"
    bot_file = os.path.join(path, main_file)
    token, bot_username = get_token_and_username(bot_file)
    content = (
        f"<b>اسم البوت:</b> {html.escape(name)}\n"
        f"<b>يوزر:</b> {bot_username if bot_username else 'غير معروف'}\n"
        f"<b>الحالة:</b> {status}\n"
        f"<b>الملف الرئيسي:</b> <code>{html.escape(main_file)}</code>\n"
        f"<b>المعرف:</b> <code>{bot_id}</code>"
    )
    # أزرار ديناميكية حسب الحالة
    buttons = []
    if running:
        buttons.append([create_btn('إيقاف', callback=f'stop_{bot_id}', color='red')])
    else:
        buttons.append([create_btn('تشغيل', callback=f'run_{bot_id}', color='green')])
    buttons.append([
        create_btn('تحديث الملف', callback=f'update_{bot_id}', color='orange'),
        create_btn('تحديث التوكن', callback=f'update_token_{bot_id}', color='purple')
    ])
    buttons.append([create_btn('تثبيت مكاتب', callback=f'install_lib_{bot_id}', color='purple')])
    buttons.append([create_btn('مدير الملفات المتقدم', callback=f'fm_advanced_{bot_id}', color='green')])
    buttons.append([create_btn('محرر الأكواد المتقدم', callback=f'editor_advanced_{bot_id}', color='purple')])
    buttons.append([create_btn('جدولة المهام', callback=f'schedule_{bot_id}', color='orange')])
    buttons.append([create_btn('حدود الموارد', callback=f'limits_{bot_id}', color='red')])
    buttons.append([create_btn('إحصائيات الموارد', callback=f'resource_stats_{bot_id}', color='blue')])
    buttons.append([create_btn('أرشفة المشروع', callback=f'archive_{bot_id}', color='grey')])
    buttons.append([create_btn('سجل العمليات', callback=f'audit_{bot_id}', color='yellow')])
    buttons.append([create_btn('نسخ احتياطي', callback=f'backup_{bot_id}', color='green')])
    buttons.append([create_btn('تحديث بدون توقف', callback=f'update_rolling_{bot_id}', color='orange')])
    buttons.append([create_btn('حذف', callback=f'del_{bot_id}', color='red')])
    buttons.append([create_btn('رجوع', callback='list_my_bots', color='blue')])
    send_formatted_message(chat_id, "إدارة البوت", content, buttons=buttons, edit=edit, message_id=message_id, footer="اختر الإجراء المناسب للبوت.")

# ============================================================
#                    دوال إدارة الحظر والعرض
# ============================================================

def show_ban_management(chat_id, message_id=None, edit=False):
    banned = get_banned_users()
    content = ""
    if banned:
        for uid, banned_at, reason in banned:
            content += f"محظور <code>{uid}</code> – {banned_at} {f'(سبب: {reason})' if reason else ''}\n"
    else:
        content = "لا يوجد محظورين."
    buttons = [[create_btn('حظر مستخدم', callback='ban_user_prompt', color='red')],
               [create_btn('فك حظر', callback='unban_user_prompt', color='green')],
               [create_btn('رجوع', callback='main_menu', color='blue')]]
    send_formatted_message(chat_id, "إدارة الحظر", content, buttons=buttons, edit=edit, message_id=message_id, footer="إدارة المستخدمين المحظورين.")

def show_admin_stats(chat_id, message_id=None, edit=False):
    c = get_cursor()
    c.execute('SELECT id, user_id, original_name, main_file, pid FROM bots')
    all_bots = c.fetchall()
    total = len(all_bots)
    if total == 0:
        send_formatted_message(chat_id, "إحصائيات البوتات", "لا توجد بوتات مستضافة.", buttons=[[create_btn('رجوع', callback='main_menu', color='blue')]], edit=edit, message_id=message_id, footer="لا توجد بوتات.")
        return
    content = f"الإجمالي: <code>{total}</code>\n\n"
    buttons = []
    # Pagination
    page = 0
    per_page = 5
    page_items, total_pages, start, end = paginate_items(all_bots, page, per_page)
    for bot_id, user_id_, orig_name, main_file, pid in page_items:
        running = is_process_running(pid)
        status = f"{EMOJI['running']} يعمل" if running else f"{EMOJI['stopped']} متوقف"
        content += f"└ <b>{bot_id}</b> | {orig_name[:20]} | {status}\n"
        buttons.append([create_btn(f'حذف البوت {bot_id}', callback=f'admin_delete_{bot_id}', color='red')])
    add_navigation_buttons(buttons, 'admin_stats_page', page, total_pages, back_callback=None, home_callback='main_menu')
    send_formatted_message(chat_id, "إحصائيات البوتات", content, buttons=buttons, edit=edit, message_id=message_id, footer="جميع البوتات.")

def show_server_stats(chat_id, message_id=None, edit=False):
    disk_usage = shutil.disk_usage('/')
    total_disk = disk_usage.total // (1024**3)
    used_disk = disk_usage.used // (1024**3)
    free_disk = disk_usage.free // (1024**3)

    bot_dirs_size = 0
    c = get_cursor()
    c.execute('SELECT file_path FROM bots')
    for (path,) in c.fetchall():
        if os.path.exists(path):
            try:
                if os.path.isdir(path):
                    size = sum(os.path.getsize(os.path.join(dirpath, f)) for dirpath, _, filenames in os.walk(path) for f in filenames)
                else:
                    size = os.path.getsize(path)
                bot_dirs_size += size
            except:
                pass
    bot_dirs_size_gb = bot_dirs_size // (1024**3)

    c.execute('SELECT pid FROM bots')
    running = sum(1 for (pid,) in c.fetchall() if is_process_running(pid))

    try:
        mem = psutil.virtual_memory()
        total_ram = mem.total // (1024**3)
        used_ram = mem.used // (1024**3)
        free_ram = mem.free // (1024**3)
        ram_percent = mem.percent
    except:
        total_ram = used_ram = free_ram = ram_percent = 0

    uptime_seconds = None
    try:
        uptime_seconds = time.time() - psutil.boot_time()
    except:
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.read().split()[0])
        except:
            pass
    if uptime_seconds:
        uptime_str = format_time(uptime_seconds)
    else:
        uptime_str = "غير معروف"

    content = (
        f"المساحة:\n"
        f"└ الإجمالي: {total_disk} GB\n"
        f"└ المستخدم: {used_disk} GB\n"
        f"└ المتبقي: {free_disk} GB\n"
        f"حجم البوتات: {bot_dirs_size_gb} GB\n"
        f"البوتات العاملة: {running}\n"
        f"الذاكرة:\n"
        f"└ الإجمالي: {total_ram} GB\n"
        f"└ المستخدم: {used_ram} GB\n"
        f"└ النسبة: {ram_percent:.1f}%\n"
        f"Uptime: {uptime_str}"
    )
    buttons = [[create_btn('رجوع', callback='main_menu', color='blue')]]
    send_formatted_message(chat_id, "إحصائيات الخادم", content, buttons=buttons, edit=edit, message_id=message_id, footer="حالة الخادم.")

def show_advanced_stats(chat_id, user_id, message_id=None, edit=False):
    if not check_permission(user_id, 'view_stats'):
        send_formatted_message(chat_id, "صلاحية ممنوعة", "ليس لديك صلاحية لعرض الإحصائيات.", footer="تواصل مع المطور.")
        return
    stats = get_advanced_stats()
    content = (
        f"المستخدمون: {stats['total_users']} (نشطاء: {stats['active']}, محظورون: {stats['banned']})\n"
        f"البوتات: {stats['total_bots']} (عاملة: {stats['running_bots']}, متوقفة: {stats['stopped_bots']})\n"
        f"التخزين: {stats['storage_gb']} GB\n"
        f"إجمالي العمليات: {stats['total_actions']}\n\n"
        "<b>آخر العمليات:</b>\n"
    )
    for ts, uid, bid, action in stats['recent_actions']:
        content += f"└ {ts[:16]} | <code>{uid}</code> | البوت {bid} | {action}\n"
    buttons = [[create_btn("رجوع", callback="main_menu", color='blue')]]
    send_formatted_message(chat_id, "الإحصائيات المتقدمة", content, buttons=buttons, edit=edit, message_id=message_id, footer="إحصائيات شاملة.")

def show_admin_management(chat_id, user_id, message_id=None, edit=False):
    if not check_permission(user_id, 'manage_admins'):
        send_formatted_message(chat_id, "صلاحية ممنوعة", "ليس لديك صلاحية لإدارة المشرفين.", footer="تواصل مع المطور.")
        return
    admins = get_admins_list()
    content = ""
    for admin in admins:
        uid, perms, added_by, added_at = admin
        perms_dict = json.loads(perms)
        perm_list = [k for k, v in perms_dict.items() if v == 1]
        content += f"مشرف <code>{uid}</code>\n"
        content += f"   الصلاحيات: {', '.join(perm_list)}\n"
        content += f"   أضيف بواسطة: <code>{added_by}</code> في {added_at}\n\n"
    buttons = [
        [create_btn("إضافة مشرف", callback="admin_add_prompt", color='green')],
        [create_btn("حذف مشرف", callback="admin_remove_prompt", color='red')],
        [create_btn("رجوع", callback="main_menu", color='blue')]
    ]
    send_formatted_message(chat_id, "إدارة المشرفين", content or "لا يوجد مشرفين.", buttons=buttons, edit=edit, message_id=message_id, footer="إدارة صلاحيات المشرفين.")

# ============================================================
#                    معالجة الأزرار (Callback) - محسّن
# ============================================================

user_states = {}

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if is_user_banned(call.from_user.id):
        bot.answer_callback_query(call.id, "أنت محظور.", show_alert=True)
        return
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    data = call.data

    # منع الضغط المتكرر
    if user_states.get(f'processing_{user_id}', False):
        bot.answer_callback_query(call.id, "جاري تنفيذ عملية أخرى...", show_alert=True)
        return
    user_states[f'processing_{user_id}'] = True

    try:
        # تحديث الجلسة
        session = get_user_session(user_id)
        session['last_page'] = data

        if data == 'main_menu':
            if user_id == ADMIN_ID:
                show_admin_panel(chat_id, message_id=msg_id, edit=True)
            else:
                show_user_panel(chat_id, message_id=msg_id, edit=True)
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return

        # زر لوحة المستخدم (للمطور)
        if data == 'user_panel' and user_id == ADMIN_ID:
            show_user_panel(chat_id, message_id=msg_id, edit=True)
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return

        # ================== مدير الملفات المتقدم ==================
        if data.startswith('fm_advanced_'):
            bot_id = data.split('_')[2]
            c = get_cursor()
            c.execute('SELECT file_path FROM bots WHERE id=?', (bot_id,))
            res = c.fetchone()
            if res:
                send_file_manager_advanced(chat_id, user_id, bot_id, res[0], message_id=msg_id)
            else:
                send_formatted_message(chat_id, "خطأ", "البوت غير موجود.", footer="تأكد من المعرف.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return
        elif data.startswith('fm_open_'):
            parts = data.split('_')
            bot_id = parts[2]
            rel_path = '_'.join(parts[3:])
            c = get_cursor()
            c.execute('SELECT file_path FROM bots WHERE id=?', (bot_id,))
            res = c.fetchone()
            if res:
                base = res[0]
                full_path = os.path.join(base, rel_path)
                if os.path.isdir(full_path):
                    send_file_manager_advanced(chat_id, user_id, bot_id, full_path, msg_id)
                else:
                    send_formatted_message(chat_id, "خطأ", "ليس مجلداً.", footer="تأكد من المسار.")
            else:
                send_formatted_message(chat_id, "خطأ", "البوت غير موجود.", footer="تأكد من المعرف.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return
        elif data.startswith('fm_refresh_'):
            parts = data.split('_')
            bot_id = parts[2]
            rel_path = '_'.join(parts[3:])
            c = get_cursor()
            c.execute('SELECT file_path FROM bots WHERE id=?', (bot_id,))
            res = c.fetchone()
            if res:
                base = res[0]
                full_path = os.path.join(base, rel_path)
                send_file_manager_advanced(chat_id, user_id, bot_id, full_path, msg_id)
            bot.answer_callback_query(call.id, "تم التحديث.")
            user_states[f'processing_{user_id}'] = False
            return
        elif data.startswith('fm_delete_'):
            parts = data.split('_')
            bot_id = parts[2]
            rel_path = '_'.join(parts[3:])
            c = get_cursor()
            c.execute('SELECT file_path FROM bots WHERE id=?', (bot_id,))
            res = c.fetchone()
            if res:
                base = res[0]
                full_path = os.path.join(base, rel_path)
                if os.path.exists(full_path):
                    btns = [[create_btn("نعم، احذف", callback=f"fm_confirm_delete_{bot_id}_{rel_path}", color='red'),
                             create_btn("إلغاء", callback=f"fm_open_{bot_id}_{os.path.relpath(os.path.dirname(full_path), base)}", color='blue')]]
                    send_formatted_message(chat_id, "تأكيد الحذف", f"هل أنت متأكد من حذف <code>{rel_path}</code>؟", buttons=btns, edit=True, message_id=msg_id, footer="هذا الإجراء لا يمكن التراجع عنه.")
                else:
                    send_formatted_message(chat_id, "خطأ", "الملف أو المجلد غير موجود.", footer="تأكد من المسار.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return
        elif data.startswith('fm_confirm_delete_'):
            parts = data.split('_')
            bot_id = parts[3]
            rel_path = '_'.join(parts[4:])
            c = get_cursor()
            c.execute('SELECT file_path FROM bots WHERE id=?', (bot_id,))
            res = c.fetchone()
            if res:
                base = res[0]
                full_path = os.path.join(base, rel_path)
                try:
                    if os.path.isdir(full_path):
                        shutil.rmtree(full_path, ignore_errors=True)
                    else:
                        os.remove(full_path)
                    send_formatted_message(chat_id, "نجاح", f"تم حذف <code>{rel_path}</code> بنجاح.", footer="تم الحذف.")
                    send_file_manager_advanced(chat_id, user_id, bot_id, os.path.dirname(full_path), msg_id)
                except Exception as e:
                    send_formatted_message(chat_id, "خطأ", f"فشل الحذف: <code>{html.escape(str(e))}</code>", footer="تحقق من الصلاحيات.")
            bot.answer_callback_query(call.id, "تم الحذف")
            user_states[f'processing_{user_id}'] = False
            return
        elif data.startswith('fm_rename_'):
            parts = data.split('_')
            bot_id = parts[2]
            rel_path = '_'.join(parts[3:])
            user_states[user_id] = f'fm_rename_{bot_id}_{rel_path}'
            send_formatted_message(chat_id, "إعادة تسمية", f"أرسل الاسم الجديد لـ <code>{rel_path}</code>:", buttons=[[create_btn("إلغاء", callback=f"fm_open_{bot_id}_{os.path.dirname(rel_path)}", color='red')]], edit=True, message_id=msg_id, footer="اكتب الاسم الجديد وأرسله.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return
        elif data.startswith('fm_newdir_'):
            parts = data.split('_')
            bot_id = parts[2]
            rel_path = '_'.join(parts[3:])
            user_states[user_id] = f'fm_newdir_{bot_id}_{rel_path}'
            send_formatted_message(chat_id, "مجلد جديد", f"أرسل اسم المجلد الجديد داخل <code>{rel_path}</code>:", buttons=[[create_btn("إلغاء", callback=f"fm_open_{bot_id}_{rel_path}", color='red')]], edit=True, message_id=msg_id, footer="اكتب اسم المجلد وأرسله.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return
        elif data.startswith('fm_upload_'):
            parts = data.split('_')
            bot_id = parts[2]
            rel_path = '_'.join(parts[3:])
            user_states[user_id] = f'fm_upload_{bot_id}_{rel_path}'
            send_formatted_message(chat_id, "رفع ملف", f"أرسل الملف لرفعه إلى <code>{rel_path}</code>:", buttons=[[create_btn("إلغاء", callback=f"fm_open_{bot_id}_{rel_path}", color='red')]], edit=True, message_id=msg_id, footer="أرسل الملف كـ Document.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return
        elif data.startswith('fm_file_'):
            parts = data.split('_')
            bot_id = parts[2]
            rel_path = '_'.join(parts[3:])
            c = get_cursor()
            c.execute('SELECT file_path FROM bots WHERE id=?', (bot_id,))
            res = c.fetchone()
            if res:
                base = res[0]
                full_path = os.path.join(base, rel_path)
                if os.path.isfile(full_path) and full_path.endswith('.py'):
                    edit_file_advanced(chat_id, user_id, bot_id, full_path, message_id=msg_id)
                else:
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        if len(content) > 4000:
                            content = content[:4000] + "\n... (محذوف للطول)"
                        send_formatted_message(chat_id, "محتوى الملف", f"<pre>{html.escape(content)}</pre>", footer="استخدم محرر الأكواد للتعديل.", edit=True, message_id=msg_id)
                    except Exception as e:
                        send_formatted_message(chat_id, "خطأ", f"لا يمكن قراءة الملف: <code>{html.escape(str(e))}</code>", footer="تأكد من صلاحيات الملف.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return
        elif data.startswith('fm_copy_'):
            parts = data.split('_')
            bot_id = parts[2]
            rel_path = '_'.join(parts[3:])
            user_states[user_id] = f'fm_copy_{bot_id}_{rel_path}'
            send_formatted_message(chat_id, "نسخ", f"أرسل المسار الوجهة (نسبي من جذر المشروع) لنسخ <code>{rel_path}</code>:", buttons=[[create_btn("إلغاء", callback=f"fm_open_{bot_id}_{os.path.dirname(rel_path)}", color='red')]], edit=True, message_id=msg_id, footer="أدخل المسار النسبي، مثال: مجلد/ملف.py")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return
        elif data.startswith('fm_compress_'):
            parts = data.split('_')
            bot_id = parts[2]
            rel_path = '_'.join(parts[3:])
            c = get_cursor()
            c.execute('SELECT file_path FROM bots WHERE id=?', (bot_id,))
            res = c.fetchone()
            if res:
                base = res[0]
                target_path = os.path.join(base, rel_path)
                if os.path.exists(target_path):
                    try:
                        zip_name = f"{os.path.basename(target_path)}_{int(time.time())}.zip"
                        zip_path = os.path.join(os.path.dirname(target_path), zip_name)
                        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                            if os.path.isdir(target_path):
                                for root, _, files in os.walk(target_path):
                                    for f in files:
                                        file_path = os.path.join(root, f)
                                        arcname = os.path.relpath(file_path, os.path.dirname(target_path))
                                        zf.write(file_path, arcname)
                            else:
                                zf.write(target_path, os.path.basename(target_path))
                        send_formatted_message(chat_id, "نجاح", f"تم ضغط الملف/المجلد إلى <code>{zip_name}</code>", footer=f"الحجم: {format_size(os.path.getsize(zip_path))}", edit=True, message_id=msg_id)
                        send_file_manager_advanced(chat_id, user_id, bot_id, os.path.dirname(target_path))
                    except Exception as e:
                        send_formatted_message(chat_id, "خطأ", f"فشل الضغط: <code>{html.escape(str(e))}</code>", footer="تحقق من المساحة.")
                else:
                    send_formatted_message(chat_id, "خطأ", "الملف أو المجلد غير موجود.", footer="تأكد من المسار.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return
        elif data.startswith('fm_extract_'):
            parts = data.split('_')
            bot_id = parts[2]
            rel_path = '_'.join(parts[3:])
            c = get_cursor()
            c.execute('SELECT file_path FROM bots WHERE id=?', (bot_id,))
            res = c.fetchone()
            if res:
                base = res[0]
                zip_path = os.path.join(base, rel_path)
                if os.path.isfile(zip_path) and zip_path.endswith('.zip'):
                    try:
                        extract_dir = os.path.join(os.path.dirname(zip_path), os.path.splitext(os.path.basename(zip_path))[0])
                        os.makedirs(extract_dir, exist_ok=True)
                        safe_extract_zip(zip_path, extract_dir)
                        send_formatted_message(chat_id, "نجاح", f"تم فك الضغط إلى <code>{extract_dir}</code>", footer=f"عدد العناصر: {len(os.listdir(extract_dir))}", edit=True, message_id=msg_id)
                        send_file_manager_advanced(chat_id, user_id, bot_id, extract_dir)
                    except Exception as e:
                        send_formatted_message(chat_id, "خطأ", f"فشل فك الضغط: <code>{html.escape(str(e))}</code>", footer="تأكد من سلامة الملف.")
                else:
                    send_formatted_message(chat_id, "خطأ", "الملف ليس ZIP صالحاً.", footer="تأكد من الامتداد.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return
        elif data.startswith('fm_search_'):
            parts = data.split('_')
            bot_id = parts[2]
            rel_path = '_'.join(parts[3:])
            user_states[user_id] = f'fm_search_{bot_id}_{rel_path}'
            send_formatted_message(chat_id, "بحث", f"أرسل النص للبحث داخل <code>{rel_path}</code>:", buttons=[[create_btn("إلغاء", callback=f"fm_open_{bot_id}_{rel_path}", color='red')]], edit=True, message_id=msg_id, footer="أدخل النص المطلوب.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return
        elif data.startswith('fm_info_'):
            parts = data.split('_')
            bot_id = parts[2]
            rel_path = '_'.join(parts[3:])
            c = get_cursor()
            c.execute('SELECT file_path FROM bots WHERE id=?', (bot_id,))
            res = c.fetchone()
            if res:
                base = res[0]
                full_path = os.path.join(base, rel_path)
                if os.path.exists(full_path):
                    try:
                        stat_info = os.stat(full_path)
                        size = stat_info.st_size
                        mtime = datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                        ctime = datetime.fromtimestamp(stat_info.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
                        perms = oct(stat_info.st_mode)[-3:]
                        is_dir = os.path.isdir(full_path)
                        content = (
                            f"<b>الاسم:</b> {os.path.basename(full_path)}\n"
                            f"<b>النوع:</b> {'مجلد' if is_dir else 'ملف'}\n"
                            f"<b>الحجم:</b> {format_size(size)}\n"
                            f"<b>آخر تعديل:</b> {mtime}\n"
                            f"<b>تاريخ الإنشاء:</b> {ctime}\n"
                            f"<b>الأذونات:</b> {perms}\n"
                            f"<b>المسار:</b> <code>{full_path}</code>"
                        )
                        send_formatted_message(chat_id, "معلومات الملف", content, edit=True, message_id=msg_id, footer="تفاصيل الملف.")
                    except Exception as e:
                        send_formatted_message(chat_id, "خطأ", f"<code>{html.escape(str(e))}</code>", footer="حدث خطأ.")
                else:
                    send_formatted_message(chat_id, "خطأ", "الملف أو المجلد غير موجود.", footer="تأكد من المسار.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return
        # أزرار الفرز والتصفية في مدير الملفات
        elif data.startswith('fm_sort_'):
            parts = data.split('_')
            bot_id = parts[2]
            sort_by = parts[3]
            sort_order = parts[4] if len(parts) > 4 else 'asc'
            session = get_user_session(user_id)
            current_path = session.get('current_path', None)
            if current_path:
                send_file_manager_advanced(chat_id, user_id, bot_id, current_path, msg_id, page=0, sort_by=sort_by, sort_order=sort_order, filter_type=session.get('filter_type', 'all'))
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return
        elif data.startswith('fm_order_'):
            parts = data.split('_')
            bot_id = parts[2]
            sort_by = parts[3]
            sort_order = parts[4]
            new_order = 'desc' if sort_order == 'asc' else 'asc'
            session = get_user_session(user_id)
            current_path = session.get('current_path', None)
            if current_path:
                send_file_manager_advanced(chat_id, user_id, bot_id, current_path, msg_id, page=0, sort_by=sort_by, sort_order=new_order, filter_type=session.get('filter_type', 'all'))
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return
        elif data.startswith('fm_filter_'):
            parts = data.split('_')
            bot_id = parts[2]
            filter_type = parts[3]
            filter_map = {'all': 'all', 'dirs': 'dirs', 'files': 'files'}
            next_filter = {'all': 'dirs', 'dirs': 'files', 'files': 'all'}.get(filter_type, 'all')
            session = get_user_session(user_id)
            session['filter_type'] = next_filter
            current_path = session.get('current_path', None)
            if current_path:
                send_file_manager_advanced(chat_id, user_id, bot_id, current_path, msg_id, page=0, sort_by=session.get('sort_by', 'name'), sort_order=session.get('sort_order', 'asc'), filter_type=next_filter)
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return
        elif data.startswith('fm_page_'):
            parts = data.split('_')
            bot_id = parts[2]
            page = int(parts[3])
            sort_by = parts[4]
            sort_order = parts[5]
            filter_type = parts[6]
            session = get_user_session(user_id)
            current_path = session.get('current_path', None)
            if current_path:
                send_file_manager_advanced(chat_id, user_id, bot_id, current_path, msg_id, page=page, sort_by=sort_by, sort_order=sort_order, filter_type=filter_type)
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return

        # ================== محرر الأكواد المتقدم ==================
        elif data.startswith('editor_advanced_'):
            bot_id = data.split('_')[2]
            c = get_cursor()
            c.execute('SELECT file_path, main_file FROM bots WHERE id=?', (bot_id,))
            res = c.fetchone()
            if res:
                main_file = os.path.join(res[0], res[1]) if res[1] else res[0]
                edit_file_advanced(chat_id, user_id, bot_id, main_file, message_id=msg_id)
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return
        elif data.startswith('editor_edit_'):
            parts = data.split('_')
            bot_id = parts[2]
            rel_path = '_'.join(parts[3:])
            user_states[user_id] = f'editor_edit_{bot_id}_{rel_path}'
            send_formatted_message(chat_id, "تعديل الملف", f"أرسل المحتوى الجديد لـ <code>{rel_path}</code>:", buttons=[[create_btn("إلغاء", callback=f"editor_advanced_{bot_id}", color='red')]], edit=True, message_id=msg_id, footer="أرسل النص الجديد (سيتم استبدال المحتوى بالكامل).")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return
        elif data.startswith('editor_save_'):
            parts = data.split('_')
            bot_id = parts[2]
            rel_path = '_'.join(parts[3:])
            user_states[user_id] = f'editor_save_{bot_id}_{rel_path}'
            send_formatted_message(chat_id, "حفظ الملف", f"أرسل المحتوى الجديد لحفظه في <code>{rel_path}</code>:", buttons=[[create_btn("إلغاء", callback=f"editor_advanced_{bot_id}", color='red')]], edit=True, message_id=msg_id, footer="سيتم حفظ المحتوى كما هو.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return
        elif data.startswith('editor_check_'):
            parts = data.split('_')
            bot_id = parts[2]
            rel_path = '_'.join(parts[3:])
            c = get_cursor()
            c.execute('SELECT file_path FROM bots WHERE id=?', (bot_id,))
            res = c.fetchone()
            if res:
                base = res[0]
                full_path = os.path.join(base, rel_path)
                try:
                    check_syntax(full_path)
                    send_formatted_message(chat_id, "فحص الصياغة", "الملف سليم صياغياً.", edit=True, message_id=msg_id, footer="لا توجد أخطاء.")
                except SyntaxError as e:
                    send_formatted_message(chat_id, "خطأ في الصياغة", f"<code>{html.escape(str(e))}</code>", edit=True, message_id=msg_id, footer="قم بتصحيح الأخطاء.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return
        elif data.startswith('editor_search_'):
            parts = data.split('_')
            bot_id = parts[2]
            rel_path = '_'.join(parts[3:])
            user_states[user_id] = f'editor_search_{bot_id}_{rel_path}'
            send_formatted_message(chat_id, "بحث واستبدال", f"أرسل النص للبحث (مفصول بـ | للاستبدال):\nمثال: <code>نص قديم|نص جديد</code>", buttons=[[create_btn("إلغاء", callback=f"editor_advanced_{bot_id}", color='red')]], edit=True, message_id=msg_id, footer="أدخل النص.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return
        elif data.startswith('editor_goto_'):
            parts = data.split('_')
            bot_id = parts[2]
            rel_path = '_'.join(parts[3:])
            user_states[user_id] = f'editor_goto_{bot_id}_{rel_path}'
            send_formatted_message(chat_id, "انتقال إلى سطر", f"أرسل رقم السطر للانتقال إليه في <code>{rel_path}</code>:", buttons=[[create_btn("إلغاء", callback=f"editor_advanced_{bot_id}", color='red')]], edit=True, message_id=msg_id, footer="أدخل رقماً صحيحاً.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return

        # ================== الجدولة ==================
        elif data.startswith('schedule_'):
            bot_id = data.split('_')[1]
            user_states[user_id] = f'schedule_{bot_id}'
            btns = [
                [create_btn("تشغيل", callback=f"schedule_action_{bot_id}_start", color='green'),
                 create_btn("إيقاف", callback=f"schedule_action_{bot_id}_stop", color='red'),
                 create_btn("إعادة تشغيل", callback=f"schedule_action_{bot_id}_restart", color='orange')],
                [create_btn("مرة واحدة", callback=f"schedule_type_{bot_id}_once", color='blue'),
                 create_btn("يومي", callback=f"schedule_type_{bot_id}_daily", color='purple'),
                 create_btn("كل ساعة", callback=f"schedule_type_{bot_id}_hourly", color='green')],
                [create_btn("رجوع", callback=f"manage_{bot_id}", color='blue')]
            ]
            send_formatted_message(chat_id, "جدولة المهام", "اختر الإجراء ونوع الجدولة:", buttons=btns, edit=True, message_id=msg_id, footer="اختر الخيارات المناسبة.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return
        elif data.startswith('schedule_action_'):
            parts = data.split('_')
            bot_id = parts[2]
            action = parts[3]
            user_states[user_id] = f'schedule_{bot_id}_{action}'
            send_formatted_message(chat_id, "إدخال الوقت", f"أرسل الوقت (لـ 'مرة واحدة' بصيغة ISO، لـ 'يومي' بصيغة HH:MM، لـ 'كل ساعة' بصيغة MM):", buttons=[[create_btn("إلغاء", callback=f"schedule_{bot_id}", color='red')]], edit=True, message_id=msg_id, footer="مثال: 2026-07-20T15:30:00 أو 15:30 أو 30")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return
        elif data.startswith('schedule_type_'):
            parts = data.split('_')
            bot_id = parts[2]
            stype = parts[3]
            user_states[user_id] = f'schedule_{bot_id}_{stype}'
            send_formatted_message(chat_id, "إدخال الوقت", f"أرسل الوقت حسب نوع '{stype}':", buttons=[[create_btn("إلغاء", callback=f"schedule_{bot_id}", color='red')]], edit=True, message_id=msg_id, footer="أدخل الوقت المناسب.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return

        # ================== حدود الموارد ==================
        elif data.startswith('limits_'):
            bot_id = data.split('_')[1]
            c = get_cursor()
            limits = get_resource_limits(bot_id)
            if not limits:
                limits = {'cpu_percent': 80, 'ram_mb': 512, 'storage_mb': 1024, 'max_processes': 1}
            content = (
                f"<b>حدود الموارد الحالية للبوت {bot_id}</b>\n"
                f"CPU: {limits['cpu_percent']}%\n"
                f"RAM: {limits['ram_mb']} MB\n"
                f"التخزين: {limits['storage_mb']} MB\n"
                f"العمليات: {limits['max_processes']}\n\n"
                "أرسل الحدود الجديدة بصيغة:\n<code>cpu=80 ram=512 storage=1024 processes=1</code>"
            )
            user_states[user_id] = f'limits_set_{bot_id}'
            send_formatted_message(chat_id, "حدود الموارد", content, buttons=[[create_btn("إلغاء", callback=f"manage_{bot_id}", color='red')]], edit=True, message_id=msg_id, footer="أرسل القيم الجديدة.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return

        # ================== أرشفة ==================
        elif data.startswith('archive_'):
            bot_id = data.split('_')[1]
            # تأكيد
            btns = [[create_btn("نعم، أرشفة", callback=f"confirm_archive_{bot_id}", color='red'),
                     create_btn("إلغاء", callback=f"manage_{bot_id}", color='blue')]]
            send_formatted_message(chat_id, "تأكيد الأرشفة", f"هل أنت متأكد من أرشفة البوت {bot_id}؟", buttons=btns, edit=True, message_id=msg_id, footer="سيتم إيقاف البوت ونقل ملفاته.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return
        elif data.startswith('confirm_archive_'):
            bot_id = data.split('_')[2]
            ok, msg = archive_project(bot_id, user_id)
            if ok:
                send_formatted_message(chat_id, "نجاح", msg, edit=True, message_id=msg_id, footer="تمت الأرشفة.")
            else:
                send_formatted_message(chat_id, "خطأ", msg, edit=True, message_id=msg_id, footer="فشلت الأرشفة.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return

        # ================== سجل العمليات ==================
        elif data.startswith('audit_'):
            bot_id = data.split('_')[1]
            c = get_cursor()
            c.execute('SELECT timestamp, user_id, action, details FROM audit_log WHERE bot_id=? ORDER BY id DESC LIMIT 20', (bot_id,))
            rows = c.fetchall()
            if not rows:
                send_formatted_message(chat_id, "سجل العمليات", "لا توجد سجلات.", edit=True, message_id=msg_id, footer="لا توجد عمليات.")
                bot.answer_callback_query(call.id)
                user_states[f'processing_{user_id}'] = False
                return
            content = ""
            for ts, uid, action, details in rows:
                content += f"└ {ts[:16]} | <code>{uid}</code> | {action} | {details[:50]}\n"
            send_formatted_message(chat_id, f"سجل العمليات للبوت {bot_id}", content, edit=True, message_id=msg_id, footer="آخر 20 عملية.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return

        # ================== نسخ احتياطي ==================
        elif data.startswith('backup_'):
            bot_id = data.split('_')[1]
            c = get_cursor()
            c.execute('SELECT file_path FROM bots WHERE id=?', (bot_id,))
            res = c.fetchone()
            if res:
                backup_path = create_backup(bot_id, res[0], 'manual')
                if backup_path:
                    send_formatted_message(chat_id, "نجاح", f"تم إنشاء النسخة الاحتياطية في <code>{backup_path}</code>", edit=True, message_id=msg_id, footer="تم النسخ.")
                else:
                    send_formatted_message(chat_id, "خطأ", "فشل إنشاء النسخة الاحتياطية.", edit=True, message_id=msg_id, footer="تحقق من المساحة.")
            else:
                send_formatted_message(chat_id, "خطأ", "البوت غير موجود.", edit=True, message_id=msg_id, footer="تأكد من المعرف.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return

        # ================== تحديث بدون توقف ==================
        elif data.startswith('update_rolling_'):
            bot_id = data.split('_')[2]
            user_states[user_id] = f'update_rolling_{bot_id}'
            send_formatted_message(chat_id, "تحديث بدون توقف", "أرسل ملف ZIP الجديد للتحديث:", buttons=[[create_btn("إلغاء", callback=f"manage_{bot_id}", color='red')]], edit=True, message_id=msg_id, footer="أرسل الملف المضغوط.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return

        # ================== إحصائيات الموارد ==================
        elif data.startswith('resource_stats_'):
            bot_id = data.split('_')[2]
            c = get_cursor()
            c.execute('SELECT pid FROM bots WHERE id=?', (bot_id,))
            res = c.fetchone()
            if not res:
                send_formatted_message(chat_id, "خطأ", "البوت غير موجود.", edit=True, message_id=msg_id, footer="تأكد من المعرف.")
                bot.answer_callback_query(call.id)
                user_states[f'processing_{user_id}'] = False
                return
            pid = res[0]
            if not pid or not is_process_running(pid):
                send_formatted_message(chat_id, "معلومات", "البوت متوقف حالياً.", edit=True, message_id=msg_id, footer="لا توجد موارد.")
                bot.answer_callback_query(call.id)
                user_states[f'processing_{user_id}'] = False
                return
            try:
                proc = psutil.Process(pid)
                cpu = proc.cpu_percent(interval=0.5)
                mem = proc.memory_info().rss / (1024*1024)
                uptime = time.time() - proc.create_time()
                uptime_str = format_time(uptime)
                try:
                    net = proc.connections()
                    net_count = len(net)
                except:
                    net_count = 0
                # أشرطة تقدم
                cpu_bar = get_progress_bar(cpu)
                mem_percent = (mem / 512) * 100  # نسبة تقريبية
                mem_bar = get_progress_bar(min(mem_percent, 100))
                content = (
                    f"<b>استهلاك موارد البوت {bot_id}</b>\n"
                    f"CPU: {cpu:.1f}%\n{cpu_bar}\n"
                    f"RAM: {mem:.1f} MB\n{mem_bar}\n"
                    f"مدة التشغيل: {uptime_str}\n"
                    f"اتصالات الشبكة: {net_count}"
                )
                send_formatted_message(chat_id, "إحصائيات الموارد", content, edit=True, message_id=msg_id, footer="تحديث تلقائي.")
            except Exception as e:
                send_formatted_message(chat_id, "خطأ", f"<code>{html.escape(str(e))}</code>", edit=True, message_id=msg_id, footer="حدث خطأ.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return

        # ================== قائمة المشاريع المؤرشفة ==================
        elif data == 'archived_list':
            c = get_cursor()
            c.execute('SELECT id, bot_id, archive_path, archived_at, status FROM archived_projects ORDER BY id DESC')
            rows = c.fetchall()
            if not rows:
                send_formatted_message(chat_id, "المشاريع المؤرشفة", "لا توجد مشاريع مؤرشفة.", edit=True, message_id=msg_id, footer="لا يوجد شيء.")
                bot.answer_callback_query(call.id)
                user_states[f'processing_{user_id}'] = False
                return
            content = ""
            btns = []
            for aid, bid, apath, atime, status in rows:
                content += f"البوت {bid} | Archived: {atime[:16]} | الحالة: {status}\n"
                if status == 'archived':
                    btns.append([create_btn(f"استعادة البوت {bid}", callback=f"restore_archive_{aid}", color='green')])
            btns.append([create_btn("رجوع", callback="main_menu", color='blue')])
            send_formatted_message(chat_id, "المشاريع المؤرشفة", content, buttons=btns, edit=True, message_id=msg_id, footer="اختر مشروعاً للاستعادة.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return
        elif data.startswith('restore_archive_'):
            archive_id = data.split('_')[2]
            # تأكيد
            btns = [[create_btn("نعم، استعادة", callback=f"confirm_restore_{archive_id}", color='green'),
                     create_btn("إلغاء", callback="archived_list", color='red')]]
            send_formatted_message(chat_id, "تأكيد الاستعادة", f"هل أنت متأكد من استعادة المشروع رقم {archive_id}؟", buttons=btns, edit=True, message_id=msg_id, footer="سيتم استعادة المشروع إلى حالته السابقة.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return
        elif data.startswith('confirm_restore_'):
            archive_id = data.split('_')[2]
            ok, msg = restore_archived_project(archive_id, user_id)
            if ok:
                send_formatted_message(chat_id, "نجاح", msg, edit=True, message_id=msg_id, footer="تمت الاستعادة.")
            else:
                send_formatted_message(chat_id, "خطأ", msg, edit=True, message_id=msg_id, footer="فشلت الاستعادة.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return

        # ================== الميزات القديمة (المحسّنة) ==================
        # إحصائيات المستخدمين
        elif data == 'user_stats' and user_id == ADMIN_ID:
            total = get_total_users()
            banned = get_banned_count()
            active = get_active_users()
            unban_ops = get_unban_count()
            content = (
                f"الإجمالي: <code>{total}</code>\n"
                f"المحظورون: <code>{banned}</code>\n"
                f"النشطون: <code>{active}</code>\n"
                f"فك الحظر: <code>{unban_ops}</code>"
            )
            buttons = [[create_btn('قائمة المستخدمين', callback='users_list', color='purple')],
                       [create_btn('رجوع', callback='main_menu', color='blue')]]
            send_formatted_message(chat_id, "إحصائيات المستخدمين", content, buttons=buttons, edit=True, message_id=msg_id, footer="إحصائيات شاملة.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return

        elif data == 'users_list' and user_id == ADMIN_ID:
            users = get_users_list()
            if not users:
                send_formatted_message(chat_id, "قائمة المستخدمين", "لا يوجد مستخدمون.", buttons=[[create_btn('رجوع', callback='user_stats', color='blue')]], edit=True, message_id=msg_id, footer="لا يوجد مستخدمون.")
                bot.answer_callback_query(call.id)
                user_states[f'processing_{user_id}'] = False
                return
            # Pagination
            page = 0
            per_page = 10
            page_items, total_pages, start, end = paginate_items(users, page, per_page)
            content = f"إجمالي المستخدمين: {len(users)} (صفحة {page+1}/{total_pages})\n\n"
            for uid, fname, username, count, first_start, last_start in page_items:
                content += f"└ {uid} | {fname[:15]} | @{username if username else 'لايوجد'} | /start: {count} | آخر: {last_start}\n"
            buttons = []
            add_navigation_buttons(buttons, 'users_list_page', page, total_pages, back_callback='user_stats', home_callback='main_menu')
            send_formatted_message(chat_id, "قائمة المستخدمين", content, buttons=buttons, edit=True, message_id=msg_id, footer=f"إجمالي: {len(users)} مستخدم.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return

        elif data == 'server_stats' and user_id == ADMIN_ID:
            show_server_stats(chat_id, message_id=msg_id, edit=True)
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return

        elif data == 'ban_management' and user_id == ADMIN_ID:
            show_ban_management(chat_id, message_id=msg_id, edit=True)
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return

        elif data == 'ban_user_prompt' and user_id == ADMIN_ID:
            user_states[user_id] = 'waiting_for_ban_user_id'
            send_formatted_message(chat_id, "حظر مستخدم", "أرسل معرف المستخدم للحظر (مع سبب اختياري):\nمثال: <code>123456789 سبب التجاوز</code>", buttons=[[create_btn('إلغاء', callback='ban_management', color='red')]], edit=True, message_id=msg_id, footer="أدخل المعرف والسبب.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return

        elif data == 'unban_user_prompt' and user_id == ADMIN_ID:
            banned = get_banned_users()
            if not banned:
                bot.answer_callback_query(call.id, "لا يوجد محظورين", show_alert=True)
                show_ban_management(chat_id, message_id=msg_id, edit=True)
                user_states[f'processing_{user_id}'] = False
                return
            btns = []
            for uid, _, _ in banned:
                btns.append([create_btn(f'فك حظر {uid}', callback=f'unban_{uid}', color='green')])
            btns.append([create_btn('رجوع', callback='ban_management', color='blue')])
            send_formatted_message(chat_id, "فك الحظر", "اختر المستخدم:", buttons=btns, edit=True, message_id=msg_id, footer="اختر محظوراً.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return

        elif data.startswith('unban_') and user_id == ADMIN_ID:
            target = int(data.split('_')[1])
            unban_user(target)
            log_unban(target, user_id)
            bot.answer_callback_query(call.id, f"تم فك حظر {target}", show_alert=True)
            show_ban_management(chat_id, message_id=msg_id, edit=True)
            user_states[f'processing_{user_id}'] = False
            return

        elif data == 'admin_stats' and user_id == ADMIN_ID:
            show_admin_stats(chat_id, message_id=msg_id, edit=True)
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return

        elif data.startswith('admin_delete_') and user_id == ADMIN_ID:
            bot_id = data.split('_')[-1]
            btns = [[create_btn('نعم، احذف', callback=f'confirm_delete_{bot_id}', color='red')],
                    [create_btn('إلغاء', callback='admin_stats', color='blue')]]
            send_formatted_message(chat_id, "تأكيد الحذف", f"هل أنت متأكد من حذف البوت {bot_id}؟", buttons=btns, edit=True, message_id=msg_id, footer="هذا الإجراء لا يمكن التراجع عنه.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return

        elif data.startswith('confirm_delete_') and user_id == ADMIN_ID:
            bot_id = data.split('_')[-1]
            admin_delete_bot(bot_id, chat_id, msg_id)
            bot.answer_callback_query(call.id, "تم الحذف")
            user_states[f'processing_{user_id}'] = False
            return

        elif data == 'broadcast_start' and user_id == ADMIN_ID:
            user_states[user_id] = 'broadcast_waiting_msg'
            send_formatted_message(chat_id, "إذاعة", "أرسل محتوى الإذاعة الآن (نص / صورة / فيديو / ملف / صوت / متحرك)\nأو /cancel للإلغاء", buttons=[[create_btn('إلغاء', callback='main_menu', color='red')]], edit=True, message_id=msg_id, footer="أرسل المحتوى.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return

        elif data == 'broadcast_confirm' and user_id == ADMIN_ID:
            if user_states.get(user_id) != 'broadcast_confirm':
                bot.answer_callback_query(call.id, "انتهت الجلسة")
                user_states[f'processing_{user_id}'] = False
                return
            status_msg = send_msg(chat_id, f"{EMOJI['wait']} جاري الإرسال...")
            if status_msg:
                start_broadcast(chat_id, user_id, status_msg['message_id'])
            else:
                status_msg = send_msg(chat_id, f"{EMOJI['wait']} جاري الإرسال...")
                if status_msg:
                    start_broadcast(chat_id, user_id, status_msg['message_id'])
            bot.answer_callback_query(call.id, "بدء الإذاعة")
            user_states[f'processing_{user_id}'] = False
            return

        elif data == 'broadcast_cancel' and user_id == ADMIN_ID:
            user_states.pop(f'broadcast_data_{user_id}', None)
            user_states.pop(f'broadcast_users_{user_id}', None)
            user_states[user_id] = None
            send_formatted_message(chat_id, "إذاعة", "تم إلغاء الإذاعة.", buttons=[[create_btn('رجوع', callback='main_menu', color='blue')]], edit=True, message_id=msg_id, footer="تم الإلغاء.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return

        elif data == 'upload':
            user_states[user_id] = 'waiting_for_file'
            send_formatted_message(chat_id, "رفع ملف .py", "أرسل ملف .py الآن (الحد الأقصى 50 ميجابايت، وإلا استخدم رفع ZIP):", buttons=[[create_btn('إلغاء', callback='main_menu', color='red')]], edit=True, message_id=msg_id, footer="أرسل الملف.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return

        elif data == 'upload_zip':
            user_states[user_id] = 'waiting_for_zip'
            send_formatted_message(chat_id, "رفع ZIP", "أرسل ملف ZIP الآن:", buttons=[[create_btn('إلغاء', callback='main_menu', color='red')]], edit=True, message_id=msg_id, footer="أرسل الملف المضغوط.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return

        elif data == 'install_library':
            user_states[user_id] = 'waiting_for_library_name'
            send_formatted_message(chat_id, "تثبيت مكتبة",
                "أرسل مكتبة وحدة أو عدة مكتبات (وحدة بكل سطر)، مثال:\n\n"
                "<code>python-telegram-bot==20.7\ntelethon==1.34\npyrogram==2.0.106\n"
                "pysocks==1.7.1\npython-dotenv==1.0.0\naiohttp==3.9.0\ncryptography==41.0.7</code>",
                buttons=[[create_btn('إلغاء', callback='main_menu', color='red')]],
                edit=True, message_id=msg_id, footer="أدخل أسماء المكتبات."
            )
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return

        elif data == 'list_my_bots':
            c = get_cursor()
            c.execute('SELECT id, original_name FROM bots WHERE user_id=?', (user_id,))
            files = c.fetchall()
            if not files:
                bot.answer_callback_query(call.id, "لا توجد بوتات", show_alert=True)
                user_states[f'processing_{user_id}'] = False
                return
            btns = []
            for fid, name in files:
                btns.append([create_btn(f'بوت {name[:30]}', callback=f'manage_{fid}', color='purple')])
            btns.append([create_btn('رجوع', callback='main_menu', color='blue')])
            send_formatted_message(chat_id, "قائمة بوتاتي", f"إجمالي البوتات: <code>{len(files)}</code>", buttons=btns, edit=True, message_id=msg_id, footer="اختر بوتاً لإدارته.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return

        elif data.startswith('manage_'):
            fid = data.split('_')[1]
            display_bot_management(chat_id, user_id, fid, message_id=msg_id, edit=True)
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return

        elif data.startswith('install_lib_'):
            fid = data.split('_')[2]
            user_states[user_id] = f'waiting_for_library_for_bot_{fid}'
            send_formatted_message(chat_id, "تثبيت مكتبات للبوت", f"أرسل أسماء المكتبات (كل مكتبة في سطر) لتثبيتها للبوت {fid}:", buttons=[[create_btn('إلغاء', callback=f'manage_{fid}', color='red')]], edit=True, message_id=msg_id, footer="أدخل أسماء المكتبات.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return

        # ================== زر التشغيل المُعدّل (مع تصحيح المسار) ==================
        elif data.startswith('run_'):
            fid = data.split('_')[1]
            c = get_cursor()
            c.execute('SELECT file_path, pid, main_file, user_id FROM bots WHERE id=?', (fid,))
            res = c.fetchone()
            if not res or (user_id != res[3] and user_id != ADMIN_ID):
                bot.answer_callback_query(call.id, "غير مصرح")
                user_states[f'processing_{user_id}'] = False
                return
            path, pid, main_file, owner = res

            # التأكد من أن path هو مجلد
            if not os.path.isdir(path):
                # إذا كان path ملفاً، نستنتج المجلد
                dir_path = os.path.dirname(path)
                if os.path.isdir(dir_path):
                    c.execute('UPDATE bots SET file_path=? WHERE id=?', (dir_path, fid))
                    get_conn().commit()
                    path = dir_path
                    if main_file is None:
                        main_file = os.path.basename(path)
                        c.execute('UPDATE bots SET main_file=? WHERE id=?', (main_file, fid))
                        get_conn().commit()
                else:
                    bot.answer_callback_query(call.id, "مسار البوت غير صحيح")
                    user_states[f'processing_{user_id}'] = False
                    return

            # إذا كان main_file لا يزال None، حاول البحث عن ملف .py وحيد في المجلد
            if main_file is None:
                py_files = [f for f in os.listdir(path) if f.endswith('.py')]
                if py_files:
                    main_file = py_files[0]
                    c.execute('UPDATE bots SET main_file=? WHERE id=?', (main_file, fid))
                    get_conn().commit()
                else:
                    bot.answer_callback_query(call.id, "لا يوجد ملف .py رئيسي")
                    display_bot_management(chat_id, user_id, fid, message_id=msg_id, edit=True)
                    user_states[f'processing_{user_id}'] = False
                    return

            if is_process_running(pid):
                bot.answer_callback_query(call.id, "البوت يعمل بالفعل")
                display_bot_management(chat_id, user_id, fid, message_id=msg_id, edit=True)
                user_states[f'processing_{user_id}'] = False
                return

            bot_file = os.path.join(path, main_file)
            bot_file = os.path.abspath(bot_file)
            cwd = os.path.dirname(bot_file)  # سيكون مساوياً لـ path

            if not os.path.isfile(bot_file):
                bot.answer_callback_query(call.id, "الملف الرئيسي غير موجود")
                display_bot_management(chat_id, user_id, fid, message_id=msg_id, edit=True)
                user_states[f'processing_{user_id}'] = False
                return

            # إرسال رسالة انتظار (نستخدم رسالة جديدة مؤقتة، ثم سنعدل عليها)
            status_msg = send_msg(chat_id, f"{EMOJI['wait']} جاري تحضير البوت (تثبيت المكتبات)...")
            status_id = status_msg['message_id'] if status_msg else None
            try:
                pid_new = run_bot_process(bot_file, cwd=cwd, chat_id=chat_id, status_msg_id=status_id, bot_id=fid)
                c.execute('UPDATE bots SET pid=? WHERE id=?', (pid_new, fid))
                get_conn().commit()
                bot.answer_callback_query(call.id, "جاري التشغيل...")
                time.sleep(1.5)
                if not is_process_running(pid_new):
                    c.execute('UPDATE bots SET pid=0 WHERE id=?', (fid,))
                    get_conn().commit()
                    log_file = bot_file + '.log'
                    if os.path.exists(log_file):
                        log_tail = tail_log(log_file)
                        details = html.escape(log_tail) if log_tail else "لا يوجد سجل أخطاء."
                    else:
                        details = "لم يتم إنشاء ملف السجل."
                    send_formatted_message(chat_id, "فشل التشغيل", f"البوت انطفى مباشرة بعد التشغيل:\n\n<pre>{details}</pre>", edit=True, message_id=status_id, footer="تحقق من الأخطاء.")
                    display_bot_management(chat_id, user_id, fid, message_id=msg_id, edit=True)
                    user_states[f'processing_{user_id}'] = False
                    return
                token, bot_user = get_token_and_username(bot_file)
                if token and token != "غير موجود":
                    threading.Thread(target=send_bot_started_notification, args=(user_id, fid, token, bot_user), daemon=True).start()
                display_bot_management(chat_id, user_id, fid, message_id=msg_id, edit=True)
            except SyntaxError as e:
                bot.answer_callback_query(call.id, "خطأ في الصياغة")
                send_formatted_message(chat_id, "خطأ في الصياغة", f"<code>{html.escape(str(e))}</code>", edit=True, message_id=status_id, footer="قم بتصحيح الأخطاء.")
                display_bot_management(chat_id, user_id, fid, message_id=msg_id, edit=True)
            except Exception as e:
                bot.answer_callback_query(call.id, f"خطأ: {str(e)[:50]}")
                send_formatted_message(chat_id, "فشل التشغيل", f"<code>{html.escape(str(e))}</code>", edit=True, message_id=status_id, footer="حدث خطأ.")
                display_bot_management(chat_id, user_id, fid, message_id=msg_id, edit=True)
            user_states[f'processing_{user_id}'] = False
            return

        elif data.startswith('stop_'):
            fid = data.split('_')[1]
            c = get_cursor()
            c.execute('SELECT pid, user_id FROM bots WHERE id=?', (fid,))
            res = c.fetchone()
            if not res or (user_id != res[1] and user_id != ADMIN_ID):
                bot.answer_callback_query(call.id, "غير مصرح")
                user_states[f'processing_{user_id}'] = False
                return
            pid = res[0]
            if pid:
                terminate_process(pid, force=True)
                c.execute('UPDATE bots SET pid=0 WHERE id=?', (fid,))
                get_conn().commit()
            bot.answer_callback_query(call.id, "تم الإيقاف")
            display_bot_management(chat_id, user_id, fid, message_id=msg_id, edit=True)
            user_states[f'processing_{user_id}'] = False
            return

        elif data.startswith('update_') and not data.startswith('update_token_'):
            fid = data.split('_')[1]
            user_states[user_id] = f'waiting_for_update_{fid}'
            send_formatted_message(chat_id, "تحديث الملف", "أرسل ملف .py الجديد للتحديث:", buttons=[[create_btn('إلغاء', callback=f'manage_{fid}', color='red')]], edit=True, message_id=msg_id, footer="أرسل الملف الجديد.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return

        elif data.startswith('update_token_'):
            fid = data.split('_')[2]
            user_states[user_id] = f'waiting_for_token_{fid}'
            send_formatted_message(chat_id, "تحديث التوكن", "أرسل التوكن الجديد للبوت:", buttons=[[create_btn('إلغاء', callback=f'manage_{fid}', color='red')]], edit=True, message_id=msg_id, footer="أدخل التوكن الجديد.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return

        elif data.startswith('del_'):
            fid = data.split('_')[1]
            # تأكيد الحذف
            btns = [[create_btn("نعم، احذف", callback=f"confirm_delete_bot_{fid}", color='red'),
                     create_btn("إلغاء", callback=f"manage_{fid}", color='blue')]]
            send_formatted_message(chat_id, "تأكيد الحذف", f"هل أنت متأكد من حذف البوت {fid}؟", buttons=btns, edit=True, message_id=msg_id, footer="سيتم حذف جميع الملفات.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return
        elif data.startswith('confirm_delete_bot_'):
            fid = data.split('_')[3]
            c = get_cursor()
            c.execute('SELECT file_path, pid, main_file, user_id FROM bots WHERE id=?', (fid,))
            res = c.fetchone()
            if res and (user_id == res[3] or user_id == ADMIN_ID):
                path, pid, main_file, owner = res
                if pid:
                    if not terminate_process(pid, force=True):
                        bot.answer_callback_query(call.id, "فشل إيقاف العملية", show_alert=True)
                        user_states[f'processing_{user_id}'] = False
                        return
                if delete_path_safely(path):
                    c.execute('DELETE FROM bots WHERE id=?', (fid,))
                    get_conn().commit()
                    bot.answer_callback_query(call.id, "تم الحذف")
                    c.execute('SELECT id, original_name FROM bots WHERE user_id=?', (user_id,))
                    files = c.fetchall()
                    if not files:
                        send_formatted_message(chat_id, "لا توجد بوتات", "ليس لديك أي بوتات.", buttons=[[create_btn('رجوع', callback='main_menu', color='blue')]], edit=True, message_id=msg_id, footer="يمكنك رفع بوت جديد.")
                    else:
                        btns = []
                        for fid2, name in files:
                            btns.append([create_btn(f'بوت {name[:30]}', callback=f'manage_{fid2}', color='purple')])
                        btns.append([create_btn('رجوع', callback='main_menu', color='blue')])
                        send_formatted_message(chat_id, "قائمة بوتاتي", f"إجمالي البوتات: <code>{len(files)}</code>", buttons=btns, edit=True, message_id=msg_id, footer="اختر بوتاً لإدارته.")
                else:
                    bot.answer_callback_query(call.id, "فشل حذف الملفات", show_alert=True)
            else:
                bot.answer_callback_query(call.id, "غير مصرح", show_alert=True)
            user_states[f'processing_{user_id}'] = False
            return

        elif data.startswith('zip_page_'):
            page = int(data.split('_')[-1])
            show_py_files(chat_id, msg_id, user_id, page)
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return

        elif data == 'terminal_start' and user_id == ADMIN_ID:
            user_states[user_id] = 'waiting_for_terminal_command'
            send_formatted_message(chat_id, "الطرفية", "أرسل الأمر الذي تريد تنفيذه (يمكن أن يكون متعدد الأسطر).\nلإلغاء: أرسل /cancel", buttons=[[create_btn('إلغاء', callback='main_menu', color='red')]], edit=True, message_id=msg_id, footer="أدخل الأمر.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return

        # ================== أوامر جديدة للبحث والصلاحيات ==================
        elif data == 'search_panel':
            user_states[user_id] = 'search_panel'
            send_formatted_message(chat_id, "بحث متقدم", "أرسل كلمة البحث (bot:, user:, log:, all:)", buttons=[[create_btn('إلغاء', callback='main_menu', color='red')]], edit=True, message_id=msg_id, footer="مثال: bot:اسم البوت")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return

        elif data == 'admin_management':
            show_admin_management(chat_id, user_id, message_id=msg_id, edit=True)
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return

        elif data == 'notif_settings':
            c = get_cursor()
            c.execute('SELECT enabled FROM notifications_settings WHERE user_id=?', (user_id,))
            row = c.fetchone()
            enabled = row[0] if row else 1
            status = "مفعلة" if enabled else "معطلة"
            btns = [
                [create_btn("تفعيل", callback="notif_enable", color='green') if not enabled else create_btn("تعطيل", callback="notif_disable", color='red')],
                [create_btn("رجوع", callback="main_menu", color='blue')]
            ]
            send_formatted_message(chat_id, "إعدادات الإشعارات", f"الحالة: {status}", buttons=btns, edit=True, message_id=msg_id, footer="اختر الإعداد.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return

        elif data == 'notif_enable':
            toggle_notifications(user_id, True)
            send_formatted_message(chat_id, "إعدادات الإشعارات", "تم تفعيل الإشعارات.", buttons=[[create_btn("رجوع", callback="notif_settings", color='blue')]], edit=True, message_id=msg_id, footer="تم التفعيل.")
            bot.answer_callback_query(call.id, "تم التفعيل")
            user_states[f'processing_{user_id}'] = False
            return

        elif data == 'notif_disable':
            toggle_notifications(user_id, False)
            send_formatted_message(chat_id, "إعدادات الإشعارات", "تم تعطيل الإشعارات.", buttons=[[create_btn("رجوع", callback="notif_settings", color='blue')]], edit=True, message_id=msg_id, footer="تم التعطيل.")
            bot.answer_callback_query(call.id, "تم التعطيل")
            user_states[f'processing_{user_id}'] = False
            return

        elif data == 'advanced_stats':
            show_advanced_stats(chat_id, user_id, message_id=msg_id, edit=True)
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return

        # أزرار التنقل في القوائم المخصصة
        elif data.startswith('users_list_page_'):
            page = int(data.split('_')[-1])
            users = get_users_list()
            if not users:
                send_formatted_message(chat_id, "قائمة المستخدمين", "لا يوجد مستخدمون.", buttons=[[create_btn('رجوع', callback='user_stats', color='blue')]], edit=True, message_id=msg_id, footer="لا يوجد مستخدمون.")
                bot.answer_callback_query(call.id)
                user_states[f'processing_{user_id}'] = False
                return
            per_page = 10
            page_items, total_pages, start, end = paginate_items(users, page, per_page)
            content = f"إجمالي المستخدمين: {len(users)} (صفحة {page+1}/{total_pages})\n\n"
            for uid, fname, username, count, first_start, last_start in page_items:
                content += f"└ {uid} | {fname[:15]} | @{username if username else 'لايوجد'} | /start: {count} | آخر: {last_start}\n"
            buttons = []
            add_navigation_buttons(buttons, 'users_list_page', page, total_pages, back_callback='user_stats', home_callback='main_menu')
            send_formatted_message(chat_id, "قائمة المستخدمين", content, buttons=buttons, edit=True, message_id=msg_id, footer=f"إجمالي: {len(users)} مستخدم.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return

        elif data.startswith('admin_stats_page_'):
            page = int(data.split('_')[-1])
            c = get_cursor()
            c.execute('SELECT id, user_id, original_name, main_file, pid FROM bots')
            all_bots = c.fetchall()
            total = len(all_bots)
            if total == 0:
                send_formatted_message(chat_id, "إحصائيات البوتات", "لا توجد بوتات مستضافة.", buttons=[[create_btn('رجوع', callback='main_menu', color='blue')]], edit=True, message_id=msg_id, footer="لا توجد بوتات.")
                bot.answer_callback_query(call.id)
                user_states[f'processing_{user_id}'] = False
                return
            per_page = 5
            page_items, total_pages, start, end = paginate_items(all_bots, page, per_page)
            content = f"الإجمالي: <code>{total}</code> (صفحة {page+1}/{total_pages})\n\n"
            buttons = []
            for bot_id, user_id_, orig_name, main_file, pid in page_items:
                running = is_process_running(pid)
                status = f"{EMOJI['running']} يعمل" if running else f"{EMOJI['stopped']} متوقف"
                content += f"└ <b>{bot_id}</b> | {orig_name[:20]} | {status}\n"
                buttons.append([create_btn(f'حذف البوت {bot_id}', callback=f'admin_delete_{bot_id}', color='red')])
            add_navigation_buttons(buttons, 'admin_stats_page', page, total_pages, back_callback=None, home_callback='main_menu')
            send_formatted_message(chat_id, "إحصائيات البوتات", content, buttons=buttons, edit=True, message_id=msg_id, footer="جميع البوتات.")
            bot.answer_callback_query(call.id)
            user_states[f'processing_{user_id}'] = False
            return

        # أي بيانات أخرى غير معروفة
        else:
            bot.answer_callback_query(call.id, "خيار غير معروف")
            user_states[f'processing_{user_id}'] = False

    except Exception as e:
        logger.error(f"خطأ في callback_handler: {e}")
        bot.answer_callback_query(call.id, f"خطأ: {str(e)[:50]}", show_alert=True)
        user_states[f'processing_{user_id}'] = False

# ============================================================
#                    دوال حذف البوت (الأدمن)
# ============================================================

def admin_delete_bot(bot_id, chat_id, message_id):
    try:
        c = get_cursor()
        c.execute('SELECT user_id, file_path, pid, main_file, original_name FROM bots WHERE id = ?', (bot_id,))
        res = c.fetchone()
        if not res:
            send_formatted_message(chat_id, "خطأ", "البوت غير موجود.", edit=True, message_id=message_id, footer="تأكد من المعرف.")
            return False
        user_id, file_path, pid, main_file, orig_name = res

        if pid:
            if not terminate_process(pid, force=True):
                send_formatted_message(chat_id, "خطأ", "تعذر إنهاء العملية.", edit=True, message_id=message_id, footer="حاول مجدداً.")
                return False

        if not delete_path_safely(file_path):
            send_formatted_message(chat_id, "خطأ", "تعذر حذف الملفات.", edit=True, message_id=message_id, footer="تحقق من الصلاحيات.")
            return False

        c.execute('DELETE FROM bots WHERE id = ?', (bot_id,))
        get_conn().commit()
        send_formatted_message(chat_id, "نجاح", f"تم حذف البوت {bot_id}.", edit=True, message_id=message_id, footer="تم الحذف.")
        time.sleep(1)
        show_admin_stats(chat_id, message_id=message_id, edit=True)
        return True
    except Exception as e:
        send_formatted_message(chat_id, "خطأ", f"<code>{html.escape(str(e))}</code>", edit=True, message_id=message_id, footer="حدث خطأ.")
        return False

# ============================================================
#                    دوال الإذاعة
# ============================================================

def build_broadcast_data(message):
    ctype = message.content_type
    if ctype == 'text':
        return {'type': 'text', 'text': message.text}
    if ctype in ('photo', 'video', 'document', 'animation', 'audio', 'voice'):
        if ctype == 'photo':
            file_id = message.photo[-1].file_id
        else:
            file_id = getattr(message, ctype).file_id
        return {
            'type': ctype,
            'file_id': file_id,
            'caption': message.caption or "",
        }
    return None

def send_broadcast_to_user(uid, data):
    try:
        if data['type'] == 'text':
            bot.send_message(uid, data['text'], disable_web_page_preview=True)
        elif data['type'] == 'photo':
            bot.send_photo(uid, data['file_id'], caption=data.get('caption') or None)
        elif data['type'] == 'video':
            bot.send_video(uid, data['file_id'], caption=data.get('caption') or None)
        elif data['type'] == 'document':
            bot.send_document(uid, data['file_id'], caption=data.get('caption') or None)
        elif data['type'] == 'animation':
            bot.send_animation(uid, data['file_id'], caption=data.get('caption') or None)
        elif data['type'] == 'audio':
            bot.send_audio(uid, data['file_id'], caption=data.get('caption') or None)
        elif data['type'] == 'voice':
            bot.send_voice(uid, data['file_id'], caption=data.get('caption') or None)
        else:
            return 'other_error'
        return 'success'
    except Exception as e:
        error_msg = str(e).lower()
        if 'blocked' in error_msg or 'bot was blocked' in error_msg:
            return 'blocked'
        elif 'deactivated' in error_msg or 'user_deactivated' in error_msg:
            return 'deactivated'
        elif 'flood' in error_msg or 'too many requests' in error_msg:
            return 'flood_wait'
        else:
            return 'other_error'

def broadcast_worker(chat_id, admin_id, status_msg_id):
    data = user_states.get(f'broadcast_data_{admin_id}')
    users = user_states.get(f'broadcast_users_{admin_id}')
    if not data or not users:
        send_formatted_message(chat_id, "إذاعة", "انتهت الجلسة، أعد المحاولة.", edit=True, message_id=status_msg_id, footer="انتهت المهلة.")
        user_states[admin_id] = None
        user_states.pop(f'broadcast_data_{admin_id}', None)
        user_states.pop(f'broadcast_users_{admin_id}', None)
        return

    total = len(users)
    counters = {
        'success': 0,
        'blocked': 0,
        'deactivated': 0,
        'flood_wait': 0,
        'other_error': 0
    }
    counters_lock = threading.Lock()
    completed = 0
    last_update = 0

    def update_progress(force=False):
        nonlocal last_update
        if force or (completed - last_update) >= 10 or completed == total:
            with counters_lock:
                succ = counters['success']
                blk = counters['blocked']
                deact = counters['deactivated']
                flood = counters['flood_wait']
                other = counters['other_error']
            progress = get_progress_bar((completed/total)*100) if total > 0 else ""
            content = (
                f"التقدم: <code>{completed}/{total}</code>\n"
                f"{progress}\n"
                f"نجح: <code>{succ}</code>\n"
                f"محظور: <code>{blk}</code>\n"
                f"غير نشط: <code>{deact}</code>\n"
                f"Flood: <code>{flood}</code>\n"
                f"أخطاء أخرى: <code>{other}</code>"
            )
            send_formatted_message(chat_id, "جاري الإذاعة", content, edit=True, message_id=status_msg_id, footer="جارٍ الإرسال...")
            last_update = completed

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_user = {executor.submit(send_broadcast_to_user, uid, data): uid for uid in users}
        for future in concurrent.futures.as_completed(future_to_user):
            uid = future_to_user[future]
            try:
                result = future.result(timeout=10)
            except Exception:
                result = 'other_error'
            with counters_lock:
                counters[result] = counters.get(result, 0) + 1
            completed += 1
            if completed % 10 == 0 or completed == total:
                update_progress()
            time.sleep(0.08)

    with counters_lock:
        succ = counters['success']
        blk = counters['blocked']
        deact = counters['deactivated']
        flood = counters['flood_wait']
        other = counters['other_error']
    final_content = (
        f"الإجمالي: <code>{total}</code>\n"
        f"نجح: <code>{succ}</code>\n"
        f"محظور: <code>{blk}</code>\n"
        f"غير نشط: <code>{deact}</code>\n"
        f"Flood: <code>{flood}</code>\n"
        f"أخطاء أخرى: <code>{other}</code>"
    )
    send_formatted_message(chat_id, "تمت الإذاعة", final_content, buttons=[[create_btn('رجوع', callback='main_menu', color='blue')]], edit=True, message_id=status_msg_id, footer="اكتملت الإذاعة.")

    user_states.pop(f'broadcast_data_{admin_id}', None)
    user_states.pop(f'broadcast_users_{admin_id}', None)
    user_states[admin_id] = None

def start_broadcast(chat_id, admin_id, status_msg_id):
    threading.Thread(target=broadcast_worker, args=(chat_id, admin_id, status_msg_id), daemon=True).start()

def handle_broadcast_input(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if message.content_type == 'text' and message.text.strip() == '/cancel':
        user_states[user_id] = None
        user_states.pop(f'broadcast_data_{user_id}', None)
        user_states.pop(f'broadcast_users_{user_id}', None)
        send_formatted_message(chat_id, "إذاعة", "تم إلغاء الإذاعة.", footer="تم الإلغاء.")
        return

    data = build_broadcast_data(message)
    if data is None:
        send_formatted_message(chat_id, "خطأ", "نوع المحتوى غير مدعوم للإذاعة. أرسل نص، صورة، فيديو، ملف، صوت، أو متحرك (GIF).", footer="أنواع غير مدعومة.")
        return

    users = get_all_users()
    if not users:
        send_formatted_message(chat_id, "إذاعة", "لا يوجد مستخدمين لإذاعة الرسالة لهم", footer="لا يوجد مستخدمين.")
        user_states[user_id] = None
        return

    user_states[f'broadcast_data_{user_id}'] = data
    user_states[f'broadcast_users_{user_id}'] = users
    user_states[user_id] = 'broadcast_confirm'

    preview_label = {
        'text': 'نص', 'photo': 'صورة', 'video': 'فيديو', 'document': 'ملف',
        'animation': 'متحرك (GIF)', 'audio': 'صوت', 'voice': 'رسالة صوتية'
    }.get(data['type'], data['type'])

    content = (
        f"النوع: <code>{preview_label}</code>\n"
        f"عدد المستهدفين: <code>{len(users)}</code>\n\n"
        f"هل تريد المتابعة؟"
    )
    send_formatted_message(chat_id, "معاينة الإذاعة", content, buttons=[
        [create_btn('تأكيد الإرسال', callback='broadcast_confirm', color='green')],
        [create_btn('إلغاء', callback='broadcast_cancel', color='red')]
    ], footer="تأكيد أو إلغاء.")

def handle_broadcast_confirmation_text(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text.strip()
    if text == '/confirm':
        status_msg = send_msg(chat_id, f"{EMOJI['wait']} جاري الإرسال...")
        if status_msg:
            start_broadcast(chat_id, user_id, status_msg['message_id'])
    elif text == '/cancel':
        user_states.pop(f'broadcast_data_{user_id}', None)
        user_states.pop(f'broadcast_users_{user_id}', None)
        user_states[user_id] = None
        send_formatted_message(chat_id, "إذاعة", "تم إلغاء الإذاعة.", footer="تم الإلغاء.")
    else:
        send_formatted_message(chat_id, "خطأ", "استخدم الأزرار، أو أرسل /confirm للتأكيد أو /cancel للإلغاء", footer="إدخال غير صحيح.")

# ============================================================
#                    دالة إرسال إشعار تشغيل البوت
# ============================================================

def send_bot_started_notification(user_id, bot_id, token, bot_username):
    if not token or token == "غير موجود":
        logger.warning(f"لا يمكن إرسال إشعار تشغيل البوت {bot_id}، التوكن غير موجود.")
        return
    try:
        info_lines = [
            "معلومات البوت المستضاف",
            "==========================",
            f"اسم البوت: {bot_username or 'غير معروف'}",
            f"معرف البوت في قاعدة البيانات: {bot_id}",
            f"تاريخ التشغيل: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"تم التشغيل بواسطة: @sa9ibot (بوت الاستضافة)"
        ]
        info_text = "\n".join(info_lines)
        file_data = io.BytesIO(info_text.encode('utf-8'))
        file_data.name = f"bot_info_{bot_id}.txt"

        url = f"https://api.telegram.org/bot{token}/sendDocument"
        files = {'document': (file_data.name, file_data, 'text/plain')}
        caption = f"[OK] لقد تم تشغيل البوت بنجاح - المصدر @sa9ibot\n\nمعلومات البوت مرفقة."
        data = {'chat_id': user_id, 'caption': caption}
        response = requests.post(url, data=data, files=files, timeout=10)
        if response.status_code == 200:
            logger.info(f"تم إرسال إشعار تشغيل البوت {bot_id} إلى المستخدم {user_id}")
        else:
            logger.warning(f"فشل إرسال الإشعار: {response.text[:100]}")
    except Exception as e:
        logger.error(f"خطأ في إرسال إشعار تشغيل البوت: {e}")

# ============================================================
#                    دوال عرض ملفات .py
# ============================================================

def show_py_files(chat_id, msg_id, user_id, page=0):
    py_files = user_states.get(f'py_files_{user_id}')
    if not py_files:
        send_formatted_message(chat_id, "خطأ", "انتهت الجلسة، أعد المحاولة.", edit=True, message_id=msg_id, footer="انتهت المهلة.")
        return
    per_page = 10
    total = len(py_files)
    start = page * per_page
    end = min(start + per_page, total)
    if start >= total:
        page = 0
        start = 0
        end = min(per_page, total)
    btns = []
    for idx in range(start, end):
        btns.append([create_btn(f'ملف {py_files[idx][:40]}', callback=f'select_zip_main_{idx}', color='purple')])
    nav = []
    if page > 0:
        nav.append(create_btn('السابق', callback=f'zip_page_{page-1}', color='blue'))
    if end < total:
        nav.append(create_btn('التالي', callback=f'zip_page_{page+1}', color='blue'))
    if nav:
        btns.append(nav)
    btns.append([create_btn('إلغاء', callback='main_menu', color='red')])
    total_pages = (total - 1) // per_page + 1
    content = f"إجمالي الملفات: <code>{total}</code> (صفحة {page+1}/{total_pages})"
    send_formatted_message(chat_id, "اختيار الملف الرئيسي", content, buttons=btns, edit=True, message_id=msg_id, footer="اختر الملف الرئيسي للبوت.")
    user_states[f'zip_page_{user_id}'] = page

# ============================================================
#                    معالجة اختيار الملف الرئيسي
# ============================================================

@bot.callback_query_handler(func=lambda call: call.data.startswith('select_zip_main_'))
def select_zip_main(call):
    if is_user_banned(call.from_user.id):
        return
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    try:
        idx = int(call.data.split('_')[-1])
    except:
        bot.answer_callback_query(call.id, "خطأ")
        return
    py_files = user_states.get(f'py_files_{user_id}')
    zip_dir = user_states.get(f'zip_dir_{user_id}')
    zip_name = user_states.get(f'zip_name_{user_id}')
    if not py_files or not zip_dir:
        bot.answer_callback_query(call.id, "انتهت الجلسة")
        return
    if idx >= len(py_files):
        bot.answer_callback_query(call.id, "اختيار خاطئ")
        return
    main_file = py_files[idx]
    main_full = os.path.join(zip_dir, main_file)
    token, bot_user = get_token_and_username(main_full)

    req_path = os.path.join(zip_dir, 'requirements.txt')
    if os.path.exists(req_path):
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', req_path], capture_output=True, timeout=120)
        except:
            pass

    c = get_cursor()
    c.execute('INSERT INTO bots (user_id, file_path, original_name, main_file) VALUES (?,?,?,?)',
              (user_id, zip_dir, zip_name, main_file))
    get_conn().commit()
    fid = c.lastrowid

    for k in [f'zip_dir_{user_id}', f'zip_name_{user_id}', f'py_files_{user_id}', f'zip_page_{user_id}']:
        user_states.pop(k, None)
    user_states[user_id] = None

    send_formatted_message(chat_id, "تم الرفع", f"تم رفع <code>{zip_name}</code>\nالملف الرئيسي: <code>{main_file}</code>", buttons=[[create_btn('تشغيل', callback=f'run_{fid}', color='green')]], edit=True, message_id=msg_id, footer="اضغط تشغيل لبدء البوت.")
    send_admin_notification(user_id, call.from_user.first_name, call.from_user.username, f"{zip_name}.zip", 'ZIP')
    bot.answer_callback_query(call.id, "تم الرفع")

# ============================================================
#                    معالجة الملفات (رفع) - مع إنشاء مجلد لكل مشروع
# ============================================================

@bot.message_handler(content_types=['document', 'photo', 'video', 'animation', 'audio', 'voice'])
def handle_file(message):
    # معالجة الأخطاء العامة
    try:
        if is_user_banned(message.from_user.id):
            return
        user_id = message.from_user.id
        chat_id = message.chat.id
        state = user_states.get(user_id)

        # إذاعة (للمطور)
        if user_id == ADMIN_ID and state == 'broadcast_waiting_msg':
            handle_broadcast_input(message)
            return

        # رفع ملف في مدير الملفات المتقدم
        if state and state.startswith('fm_upload_'):
            parts = state.split('_')
            bot_id = parts[2]
            rel_path = '_'.join(parts[3:])
            if message.content_type != 'document':
                send_formatted_message(chat_id, "خطأ", "يرجى إرسال ملف.", footer="أرسل ملفاً.")
                user_states[user_id] = None
                return
            c = get_cursor()
            c.execute('SELECT file_path FROM bots WHERE id=?', (bot_id,))
            res = c.fetchone()
            if res:
                base = res[0]
                target_dir = os.path.join(base, rel_path)
                if not os.path.isdir(target_dir):
                    send_formatted_message(chat_id, "خطأ", "المسار ليس مجلداً.", footer="تأكد من المسار.")
                    user_states[user_id] = None
                    return
                file_info = bot.get_file(message.document.file_id)
                try:
                    downloaded = bot.download_file(file_info.file_path)
                    file_path = os.path.join(target_dir, message.document.file_name)
                    with open(file_path, 'wb') as f:
                        f.write(downloaded)
                    send_formatted_message(chat_id, "نجاح", f"تم رفع {message.document.file_name} بنجاح.", footer=f"الحجم: {format_size(len(downloaded))}")
                    send_file_manager_advanced(chat_id, user_id, bot_id, target_dir)
                except Exception as e:
                    send_formatted_message(chat_id, "خطأ", f"فشل الرفع: <code>{html.escape(str(e))}</code>", footer="تحقق من الملف.")
            user_states[user_id] = None
            return

        # تحديث بدون توقف (Rolling Update)
        if state and state.startswith('update_rolling_'):
            bot_id = state.split('_')[2]
            if message.content_type != 'document' or not message.document.file_name.endswith('.zip'):
                send_formatted_message(chat_id, "خطأ", "يجب أن يكون الملف ZIP.", footer="أرسل ملف ZIP.")
                user_states[user_id] = None
                return
            zip_path = f"temp_update_{bot_id}_{int(time.time())}.zip"
            try:
                file_info = bot.get_file(message.document.file_id)
                downloaded = bot.download_file(file_info.file_path)
                with open(zip_path, 'wb') as f:
                    f.write(downloaded)
                c = get_cursor()
                c.execute('SELECT file_path, main_file FROM bots WHERE id=?', (bot_id,))
                res = c.fetchone()
                if res:
                    project_path = res[0]
                    backup_path = create_backup(bot_id, project_path, 'rolling')
                    if not backup_path:
                        send_formatted_message(chat_id, "خطأ", "فشل إنشاء النسخة الاحتياطية", footer="تحقق من المساحة.")
                        os.remove(zip_path)
                        user_states[user_id] = None
                        return
                    extract_dir = f"temp_extract_{bot_id}_{int(time.time())}"
                    try:
                        safe_extract_zip(zip_path, extract_dir)
                        if os.path.exists(project_path):
                            shutil.rmtree(project_path, ignore_errors=True)
                        shutil.copytree(extract_dir, project_path)
                        shutil.rmtree(extract_dir, ignore_errors=True)
                        main_file = os.path.join(project_path, res[1]) if res[1] else project_path
                        pid_new = run_bot_process(main_file, cwd=project_path, bot_id=bot_id)
                        c.execute('UPDATE bots SET pid=? WHERE id=?', (pid_new, bot_id))
                        get_conn().commit()
                        send_formatted_message(chat_id, "نجاح", "تم التحديث بنجاح", footer="تم التحديث بدون توقف.")
                        log_audit(user_id, bot_id, 'rolling_update', 'تحديث ناجح')
                        send_notification(user_id, f"[OK] تم تحديث البوت {bot_id} بنجاح", 'success')
                    except Exception as e:
                        restore_backup(bot_id, backup_path, project_path)
                        send_formatted_message(chat_id, "خطأ", f"فشل التحديث، تم الاسترجاع: <code>{html.escape(str(e))}</code>", footer="تم الاسترجاع من النسخة الاحتياطية.")
                        log_audit(user_id, bot_id, 'rolling_update_fail', str(e))
                        send_notification(user_id, f"[ERROR] فشل تحديث البوت {bot_id}: {e}", 'error')
                    os.remove(zip_path)
            except Exception as e:
                send_formatted_message(chat_id, "خطأ", f"فشل: <code>{html.escape(str(e))}</code>", footer="حدث خطأ.")
            user_states[user_id] = None
            return

        # ========== رفع ملف عادي (.py) - إنشاء مجلد ==========
        if state == 'waiting_for_file':
            if message.content_type != 'document' or not message.document.file_name.endswith('.py'):
                send_formatted_message(chat_id, "خطأ", "يجب أن يكون الملف .py", footer="أرسل ملف .py.")
                return
            orig_name = message.document.file_name
            # إنشاء مجلد للمشروع
            project_dir = f"bot_{user_id}_{int(time.time())}"
            os.makedirs(project_dir, exist_ok=True)
            file_path = os.path.join(project_dir, orig_name)  # المسار الكامل للملف داخل المجلد

            status_msg = send_msg(chat_id, f"{EMOJI['wait']} جاري تنزيل الملف...")
            status_id = status_msg['message_id'] if status_msg else None

            try:
                download_telegram_file_large(message.document.file_id, file_path, chat_id, status_id)
            except Exception as e:
                if os.path.exists(project_dir):
                    shutil.rmtree(project_dir, ignore_errors=True)
                send_formatted_message(chat_id, "خطأ", f"فشل تنزيل الملف: <code>{html.escape(str(e))}</code>", edit=True, message_id=status_id, footer="حاول مجدداً.")
                user_states[user_id] = None
                return

            # بعد التنزيل، نقوم بإدراج المشروع في قاعدة البيانات مع main_file = orig_name
            c = get_cursor()
            c.execute('INSERT INTO bots (user_id, file_path, original_name, main_file) VALUES (?,?,?,?)',
                      (user_id, project_dir, orig_name, orig_name))  # file_path = المجلد، main_file = اسم الملف
            get_conn().commit()
            fid = c.lastrowid
            user_states[user_id] = None
            send_formatted_message(chat_id, "تم الرفع", f"تم رفع <code>{orig_name}</code>", buttons=[[create_btn('تشغيل', callback=f'run_{fid}', color='green')]], edit=True, message_id=status_id, footer="اضغط تشغيل لبدء البوت.")
            send_admin_notification(user_id, message.from_user.first_name, message.from_user.username, orig_name, '.py')
            return

        # رفع ZIP
        if state == 'waiting_for_zip':
            if message.content_type != 'document' or not message.document.file_name.endswith('.zip'):
                send_formatted_message(chat_id, "خطأ", "يجب أن يكون الملف .zip", footer="أرسل ملف ZIP.")
                return
            zip_name = message.document.file_name.replace('.zip', '')
            zip_path = f"temp_{user_id}_{int(time.time())}.zip"
            file_size_mb = (message.document.file_size or 0) / (1024 * 1024)
            status_msg = send_msg(chat_id, f"[WAIT] جاري استقبال الملف ({file_size_mb:.1f} MB)...")
            status_id = status_msg['message_id'] if status_msg else None
            try:
                download_telegram_file_large(message.document.file_id, zip_path, chat_id, status_id)
            except Exception as e:
                if os.path.exists(zip_path):
                    os.remove(zip_path)
                send_formatted_message(chat_id, "خطأ", f"فشل تنزيل الملف: <code>{html.escape(str(e))}</code>", edit=True, message_id=status_id, footer="حاول مجدداً.")
                user_states[user_id] = None
                return
            if not zipfile.is_zipfile(zip_path):
                os.remove(zip_path)
                send_formatted_message(chat_id, "خطأ", "الملف ليس ZIP صحيحاً.", edit=True, message_id=status_id, footer="تأكد من الملف.")
                user_states[user_id] = None
                return
            extract_dir = f"bot_{user_id}_{int(time.time())}"
            try:
                safe_extract_zip(zip_path, extract_dir)
                os.remove(zip_path)
            except Exception as e:
                shutil.rmtree(extract_dir, ignore_errors=True)
                if os.path.exists(zip_path):
                    os.remove(zip_path)
                send_formatted_message(chat_id, "خطأ", f"فشل استخراج ZIP: <code>{html.escape(str(e))}</code>", edit=True, message_id=status_id, footer="تأكد من سلامة الملف.")
                user_states[user_id] = None
                return
            py_files = get_py_files_from_directory(extract_dir)
            if not py_files:
                shutil.rmtree(extract_dir)
                send_formatted_message(chat_id, "خطأ", "لا توجد ملفات .py في ZIP", edit=True, message_id=status_id, footer="الملف لا يحتوي على كود.")
                user_states[user_id] = None
                return
            if len(py_files) == 1:
                main_file = py_files[0]
                main_full = os.path.join(extract_dir, main_file)
                token, bot_user = get_token_and_username(main_full)
                req_path = os.path.join(extract_dir, 'requirements.txt')
                if os.path.exists(req_path):
                    try:
                        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', req_path], capture_output=True, timeout=120)
                    except:
                        pass
                c = get_cursor()
                c.execute('INSERT INTO bots (user_id, file_path, original_name, main_file) VALUES (?,?,?,?)',
                          (user_id, extract_dir, zip_name, main_file))
                get_conn().commit()
                fid = c.lastrowid
                user_states[user_id] = None
                send_formatted_message(chat_id, "تم الرفع", f"تم رفع <code>{zip_name}</code>\nالملف الرئيسي: <code>{main_file}</code>", buttons=[[create_btn('تشغيل', callback=f'run_{fid}', color='green')]], edit=True, message_id=status_id, footer="اضغط تشغيل لبدء البوت.")
                send_admin_notification(user_id, message.from_user.first_name, message.from_user.username, f"{zip_name}.zip", 'ZIP')
                return
            user_states[f'zip_dir_{user_id}'] = extract_dir
            user_states[f'zip_name_{user_id}'] = zip_name
            user_states[f'py_files_{user_id}'] = py_files
            user_states[f'zip_page_{user_id}'] = 0
            user_states[user_id] = 'waiting_for_main_file'
            show_py_files(chat_id, message.message_id, user_id, 0)
            return

        # تحديث ملف بوت
        if state and state.startswith('waiting_for_update_'):
            fid = state.split('_')[-1]
            if message.content_type != 'document' or not message.document.file_name.endswith('.py'):
                send_formatted_message(chat_id, "خطأ", "الملف الجديد يجب أن يكون .py", footer="أرسل ملف .py.")
                return
            c = get_cursor()
            c.execute('SELECT file_path, pid, original_name, main_file FROM bots WHERE id=? AND user_id=?', (fid, user_id))
            res = c.fetchone()
            if not res:
                send_formatted_message(chat_id, "خطأ", "البوت غير موجود", footer="تأكد من المعرف.")
                user_states[user_id] = None
                return
            old_path, pid, old_name, main_file = res
            if is_process_running(pid):
                try:
                    terminate_process(pid, force=True)
                    c.execute('UPDATE bots SET pid=0 WHERE id=?', (fid,))
                    get_conn().commit()
                except:
                    pass
            if not delete_path_safely(old_path):
                send_formatted_message(chat_id, "خطأ", "فشل حذف الملف القديم، حاول مرة أخرى", footer="تحقق من الصلاحيات.")
                user_states[user_id] = None
                return
            new_name = message.document.file_name
            new_path = f"bot_{user_id}_{int(time.time())}_{safe_filename(new_name)}"
            try:
                file_info = bot.get_file(message.document.file_id)
                if file_info.file_size and file_info.file_size > 50 * 1024 * 1024:
                    raise ApiTelegramException("file_too_big", {"description": "file is too big"}, {})
                downloaded = bot.download_file(file_info.file_path)
            except ApiTelegramException as e:
                if "file is too big" in str(e).lower():
                    send_formatted_message(chat_id, "تحذير", "الملف كبير جداً، استخدم رفع مضغوط.", buttons=[[create_btn('رجوع', callback=f'manage_{fid}', color='blue')]], footer="استخدم ZIP.")
                    user_states[user_id] = None
                    return
                else:
                    raise
            except Exception as e:
                send_formatted_message(chat_id, "خطأ", f"فشل تنزيل الملف: <code>{html.escape(str(e))}</code>", footer="حاول مجدداً.")
                user_states[user_id] = None
                return
            with open(new_path, 'wb') as f:
                f.write(downloaded)
            c.execute('UPDATE bots SET file_path=?, original_name=?, main_file=? WHERE id=?',
                      (new_path, new_name, main_file, fid))
            get_conn().commit()
            user_states[user_id] = None
            send_formatted_message(chat_id, "نجاح", "تم تحديث الملف", buttons=[[create_btn('تشغيل', callback=f'run_{fid}', color='green')]], footer="اضغط تشغيل.")
            display_bot_management(chat_id, user_id, fid)
            return
    except Exception as e:
        logger.error(f"خطأ غير متوقع في handle_file: {e}")
        send_formatted_message(message.chat.id, "خطأ داخلي", f"حدث خطأ غير متوقع: <code>{html.escape(str(e))}</code>", footer="تم تسجيل الخطأ، حاول مجدداً.")
        user_states[message.from_user.id] = None

# ============================================================
#                    أوامر البوت (Start)
# ============================================================

@bot.message_handler(commands=['start'])
def start(message):
    if is_user_banned(message.from_user.id):
        bot.send_message(message.chat.id, f"{EMOJI['stop']} أنت محظور.")
        return
    user_id = message.from_user.id
    chat_id = message.chat.id
    register_user_start(user_id, message.from_user.first_name, message.from_user.username)

    if user_id == ADMIN_ID:
        show_admin_panel(chat_id)
    else:
        show_user_panel(chat_id)

# ============================================================
#                    معالجة الرسائل النصية
# ============================================================

@bot.message_handler(content_types=['text'])
def handle_text(message):
    if is_user_banned(message.from_user.id):
        return
    user_id = message.from_user.id
    chat_id = message.chat.id
    state = user_states.get(user_id)

    # ================== معالجة حالات الميزات الجديدة ==================

    # إعادة تسمية
    if state and state.startswith('fm_rename_'):
        parts = state.split('_')
        bot_id = parts[2]
        rel_path = '_'.join(parts[3:])
        new_name = message.text.strip()
        if not new_name:
            send_formatted_message(chat_id, "خطأ", "الاسم لا يمكن أن يكون فارغاً.", footer="أدخل اسماً صحيحاً.")
            user_states[user_id] = None
            return
        c = get_cursor()
        c.execute('SELECT file_path FROM bots WHERE id=?', (bot_id,))
        res = c.fetchone()
        if res:
            base = res[0]
            old_full = os.path.join(base, rel_path)
            new_full = os.path.join(os.path.dirname(old_full), new_name)
            try:
                os.rename(old_full, new_full)
                send_formatted_message(chat_id, "نجاح", f"تمت إعادة التسمية إلى <code>{new_name}</code>", footer="تم التحديث.")
                send_file_manager_advanced(chat_id, user_id, bot_id, os.path.dirname(new_full))
            except Exception as e:
                send_formatted_message(chat_id, "خطأ", f"فشلت: <code>{html.escape(str(e))}</code>", footer="تحقق من الصلاحيات.")
        user_states[user_id] = None
        return

    # مجلد جديد
    if state and state.startswith('fm_newdir_'):
        parts = state.split('_')
        bot_id = parts[2]
        rel_path = '_'.join(parts[3:])
        dir_name = message.text.strip()
        if not dir_name:
            send_formatted_message(chat_id, "خطأ", "اسم المجلد لا يمكن أن يكون فارغاً.", footer="أدخل اسماً صحيحاً.")
            user_states[user_id] = None
            return
        c = get_cursor()
        c.execute('SELECT file_path FROM bots WHERE id=?', (bot_id,))
        res = c.fetchone()
        if res:
            base = res[0]
            full_path = os.path.join(base, rel_path, dir_name)
            try:
                os.makedirs(full_path, exist_ok=True)
                send_formatted_message(chat_id, "نجاح", f"تم إنشاء المجلد <code>{dir_name}</code>", footer="تم الإنشاء.")
                send_file_manager_advanced(chat_id, user_id, bot_id, os.path.join(base, rel_path))
            except Exception as e:
                send_formatted_message(chat_id, "خطأ", f"فشل: <code>{html.escape(str(e))}</code>", footer="تحقق من الصلاحيات.")
        user_states[user_id] = None
        return

    # نسخ ملف
    if state and state.startswith('fm_copy_'):
        parts = state.split('_')
        bot_id = parts[2]
        rel_path = '_'.join(parts[3:])
        dest_rel = message.text.strip()
        if not dest_rel:
            send_formatted_message(chat_id, "خطأ", "المسار الوجهة مطلوب.", footer="أدخل مساراً صحيحاً.")
            user_states[user_id] = None
            return
        c = get_cursor()
        c.execute('SELECT file_path FROM bots WHERE id=?', (bot_id,))
        res = c.fetchone()
        if res:
            base = res[0]
            src = os.path.join(base, rel_path)
            dest = os.path.join(base, dest_rel)
            if os.path.exists(src):
                try:
                    if os.path.isdir(src):
                        shutil.copytree(src, dest, ignore_dirs=['__pycache__'])
                    else:
                        shutil.copy2(src, dest)
                    send_formatted_message(chat_id, "نجاح", f"تم النسخ إلى <code>{dest_rel}</code>", footer="تم النسخ.")
                    send_file_manager_advanced(chat_id, user_id, bot_id, os.path.dirname(dest))
                except Exception as e:
                    send_formatted_message(chat_id, "خطأ", f"فشل النسخ: <code>{html.escape(str(e))}</code>", footer="تحقق من المسار.")
            else:
                send_formatted_message(chat_id, "خطأ", "الملف/المجلد المصدر غير موجود", footer="تأكد من المسار.")
        user_states[user_id] = None
        return

    # بحث في مدير الملفات
    if state and state.startswith('fm_search_'):
        parts = state.split('_')
        bot_id = parts[2]
        rel_path = '_'.join(parts[3:])
        query = message.text.strip()
        if not query:
            send_formatted_message(chat_id, "خطأ", "أدخل نص البحث.", footer="أدخل نصاً.")
            user_states[user_id] = None
            return
        c = get_cursor()
        c.execute('SELECT file_path FROM bots WHERE id=?', (bot_id,))
        res = c.fetchone()
        if res:
            base = res[0]
            search_path = os.path.join(base, rel_path)
            if os.path.isdir(search_path):
                results = []
                for root, _, files in os.walk(search_path):
                    for f in files:
                        if query.lower() in f.lower():
                            rel = os.path.relpath(os.path.join(root, f), base)
                            results.append(rel)
                            if len(results) >= 50:
                                break
                    if len(results) >= 50:
                        break
                if results:
                    content = f"نتائج البحث عن '<b>{query}</b>':\n" + "\n".join(f"└ {r}" for r in results[:50])
                    if len(results) > 50:
                        content += f"\n... و {len(results)-50} نتيجة أخرى"
                    send_formatted_message(chat_id, "نتائج البحث", content, footer=f"عدد النتائج: {len(results)}")
                else:
                    send_formatted_message(chat_id, "نتائج البحث", "لا توجد نتائج", footer="لم يتم العثور على شيء.")
        user_states[user_id] = None
        return

    # محرر الأكواد - تعديل
    if state and state.startswith('editor_edit_'):
        parts = state.split('_')
        bot_id = parts[2]
        rel_path = '_'.join(parts[3:])
        new_content = message.text
        c = get_cursor()
        c.execute('SELECT file_path FROM bots WHERE id=?', (bot_id,))
        res = c.fetchone()
        if res:
            base = res[0]
            full_path = os.path.join(base, rel_path)
            backup = full_path + '.bak'
            try:
                shutil.copy2(full_path, backup)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                try:
                    check_syntax(full_path)
                    send_formatted_message(chat_id, "نجاح", "تم الحفظ والفحص بنجاح", footer="لا توجد أخطاء.")
                    edit_file_advanced(chat_id, user_id, bot_id, full_path)
                except SyntaxError as e:
                    shutil.copy2(backup, full_path)
                    send_formatted_message(chat_id, "خطأ في الصياغة", f"<code>{html.escape(str(e))}</code>", footer="تم الاسترجاع من النسخة الاحتياطية.")
                    edit_file_advanced(chat_id, user_id, bot_id, full_path)
                os.remove(backup)
            except Exception as e:
                send_formatted_message(chat_id, "خطأ", f"فشل: <code>{html.escape(str(e))}</code>", footer="حدث خطأ.")
        user_states[user_id] = None
        return

    # محرر الأكواد - حفظ
    if state and state.startswith('editor_save_'):
        parts = state.split('_')
        bot_id = parts[2]
        rel_path = '_'.join(parts[3:])
        new_content = message.text
        c = get_cursor()
        c.execute('SELECT file_path FROM bots WHERE id=?', (bot_id,))
        res = c.fetchone()
        if res:
            base = res[0]
            full_path = os.path.join(base, rel_path)
            try:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                send_formatted_message(chat_id, "نجاح", "تم الحفظ", footer="تم الحفظ.")
                edit_file_advanced(chat_id, user_id, bot_id, full_path)
            except Exception as e:
                send_formatted_message(chat_id, "خطأ", f"فشل: <code>{html.escape(str(e))}</code>", footer="حدث خطأ.")
        user_states[user_id] = None
        return

    # محرر الأكواد - بحث واستبدال
    if state and state.startswith('editor_search_'):
        parts = state.split('_')
        bot_id = parts[2]
        rel_path = '_'.join(parts[3:])
        query = message.text.strip()
        if '|' in query:
            find, replace = query.split('|', 1)
            c = get_cursor()
            c.execute('SELECT file_path FROM bots WHERE id=?', (bot_id,))
            res = c.fetchone()
            if res:
                base = res[0]
                full_path = os.path.join(base, rel_path)
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    new_content = content.replace(find, replace)
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    send_formatted_message(chat_id, "نجاح", f"تم استبدال '{find}' بـ '{replace}'", footer="تم الاستبدال.")
                    edit_file_advanced(chat_id, user_id, bot_id, full_path)
                except Exception as e:
                    send_formatted_message(chat_id, "خطأ", f"فشل: <code>{html.escape(str(e))}</code>", footer="حدث خطأ.")
        else:
            # بحث فقط
            c = get_cursor()
            c.execute('SELECT file_path FROM bots WHERE id=?', (bot_id,))
            res = c.fetchone()
            if res:
                base = res[0]
                full_path = os.path.join(base, rel_path)
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    matches = []
                    for i, line in enumerate(lines, 1):
                        if query in line:
                            matches.append((i, line.strip()))
                    if matches:
                        content = f"نتائج البحث عن '{query}':\n"
                        for num, line in matches[:20]:
                            content += f"{num}: {html.escape(line[:100])}\n"
                        send_formatted_message(chat_id, "نتائج البحث", content, footer=f"عدد النتائج: {len(matches)}")
                    else:
                        send_formatted_message(chat_id, "نتائج البحث", "لا توجد نتائج", footer="لم يتم العثور على شيء.")
                except Exception as e:
                    send_formatted_message(chat_id, "خطأ", f"خطأ: <code>{html.escape(str(e))}</code>", footer="حدث خطأ.")
        user_states[user_id] = None
        return

    # محرر الأكواد - انتقال إلى سطر
    if state and state.startswith('editor_goto_'):
        parts = state.split('_')
        bot_id = parts[2]
        rel_path = '_'.join(parts[3:])
        try:
            line_num = int(message.text.strip())
            c = get_cursor()
            c.execute('SELECT file_path FROM bots WHERE id=?', (bot_id,))
            res = c.fetchone()
            if res:
                base = res[0]
                full_path = os.path.join(base, rel_path)
                with open(full_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                if 1 <= line_num <= len(lines):
                    send_formatted_message(chat_id, "انتقال إلى سطر", f"السطر {line_num}: <code>{html.escape(lines[line_num-1][:200])}</code>", footer="عرض السطر.")
                else:
                    send_formatted_message(chat_id, "خطأ", "رقم سطر خارج النطاق", footer="أدخل رقماً صحيحاً.")
        except:
            send_formatted_message(chat_id, "خطأ", "رقم غير صحيح", footer="أدخل رقماً صحيحاً.")
        user_states[user_id] = None
        return

    # الجدولة
    if state and state.startswith('schedule_'):
        parts = state.split('_')
        if len(parts) == 4:
            bot_id = parts[1]
            action = parts[2]
            stype = parts[3]
            time_str = message.text.strip()
            c = get_cursor()
            c.execute('SELECT file_path FROM bots WHERE id=?', (bot_id,))
            if c.fetchone():
                ok, msg = schedule_task(bot_id, action, stype, time_str, user_id)
                if ok:
                    send_formatted_message(chat_id, "نجاح", msg, footer="تمت الجدولة.")
                else:
                    send_formatted_message(chat_id, "خطأ", msg, footer="فشلت الجدولة.")
            else:
                send_formatted_message(chat_id, "خطأ", "البوت غير موجود", footer="تأكد من المعرف.")
        user_states[user_id] = None
        return

    # حدود الموارد
    if state and state.startswith('limits_set_'):
        bot_id = state.split('_')[2]
        try:
            params = {}
            for part in message.text.split():
                if '=' in part:
                    k, v = part.split('=')
                    params[k] = int(v)
            limits = {
                'cpu_percent': params.get('cpu', 80),
                'ram_mb': params.get('ram', 512),
                'storage_mb': params.get('storage', 1024),
                'max_processes': params.get('processes', 1)
            }
            set_resource_limits(bot_id, limits)
            send_formatted_message(chat_id, "نجاح", "تم تعيين الحدود", footer="تم التحديث.")
        except:
            send_formatted_message(chat_id, "خطأ", "صيغة غير صحيحة. استخدم: <code>cpu=80 ram=512 storage=1024 processes=1</code>", footer="أدخل القيم بشكل صحيح.")
        user_states[user_id] = None
        return

    # البحث المتقدم
    if state == 'search_panel':
        query = message.text.strip()
        if not query:
            send_formatted_message(chat_id, "خطأ", "أدخل كلمة البحث.", footer="أدخل نصاً.")
            user_states[user_id] = None
            return
        if query.startswith('bot:'):
            results = advanced_search(query[4:].strip(), 'bots')
        elif query.startswith('user:'):
            results = advanced_search(query[5:].strip(), 'users')
        elif query.startswith('log:'):
            results = advanced_search(query[4:].strip(), 'logs')
        else:
            results = advanced_search(query, 'all')
        content = ""
        if 'bots' in results and results['bots']:
            content += "البوتات:\n"
            for bid, name, uid, pid in results['bots']:
                status = "يعمل" if is_process_running(pid) else "متوقف"
                content += f"└ {name} (ID:{bid}) - {status}\n"
        if 'users' in results and results['users']:
            content += "\nالمستخدمون:\n"
            for uid, fname, uname in results['users']:
                content += f"└ {uid} | {fname} | @{uname or 'لايوجد'}\n"
        if 'logs' in results and results['logs']:
            content += "\nالسجلات:\n"
            for lid, ts, uid, bid, action, details in results['logs'][:10]:
                content += f"└ {ts[:16]} | {action} | {details[:30]}\n"
        if not content:
            content = "لا توجد نتائج"
        send_formatted_message(chat_id, "نتائج البحث", content, footer="نتائج البحث.")
        user_states[user_id] = None
        return

    # ================== المعالجات القديمة ==================

    # إذاعة
    if user_id == ADMIN_ID and state == 'broadcast_waiting_msg':
        handle_broadcast_input(message)
        return
    if user_id == ADMIN_ID and state == 'broadcast_confirm':
        handle_broadcast_confirmation_text(message)
        return

    # حظر مستخدم
    if state == 'waiting_for_ban_user_id' and user_id == ADMIN_ID:
        parts = message.text.strip().split(maxsplit=1)
        try:
            target = int(parts[0])
        except:
            send_formatted_message(chat_id, "خطأ", "معرف غير صالح", footer="أدخل رقماً صحيحاً.")
            user_states[user_id] = None
            return
        reason = parts[1] if len(parts) > 1 else None
        if is_user_banned(target):
            send_formatted_message(chat_id, "معلومات", f"المستخدم {target} محظور بالفعل", footer="تم الحظر مسبقاً.")
        else:
            ban_user(target, reason)
            send_formatted_message(chat_id, "نجاح", f"تم حظر {target}", footer=f"السبب: {reason or 'غير محدد'}")
        user_states[user_id] = None
        show_ban_management(chat_id, message_id=message.message_id, edit=True)
        return

    # تثبيت مكتبة
    if state == 'waiting_for_library_name':
        raw = message.text.strip()
        libs = [l.strip() for l in raw.replace(',', '\n').splitlines() if l.strip()]
        if not libs:
            send_formatted_message(chat_id, "خطأ", "اسم المكتبة مطلوب", footer="أدخل اسماً.")
            user_states[user_id] = None
            return
        total = len(libs)
        status_msg = send_msg(chat_id, f"{EMOJI['wait']} جاري التثبيت (0/{total})...")
        status_id = status_msg['message_id'] if status_msg else None
        results = []
        for i, lib in enumerate(libs, start=1):
            safe_lib = html.escape(lib)
            if status_id:
                send_formatted_message(chat_id, "جاري التثبيت", f"({i}/{total}) <code>{safe_lib}</code>", edit=True, message_id=status_id, footer="جارٍ التثبيت...")
            try:
                result = subprocess.run([sys.executable, '-m', 'pip', 'install', lib], capture_output=True, text=True, timeout=120)
                if result.returncode == 0:
                    results.append(f"{EMOJI['success']} {safe_lib}")
                else:
                    results.append(f"{EMOJI['error']} {safe_lib}")
            except Exception as e:
                results.append(f"{EMOJI['error']} {safe_lib} ({html.escape(str(e)[:60])})")
        summary = "\n".join(results)
        final_content = f"اكتمل التثبيت ({total}):\n\n{summary}"
        send_formatted_message(chat_id, "تقرير التثبيت", final_content, edit=True, message_id=status_id, footer="تم التثبيت.")
        user_states[user_id] = None
        return

    # تثبيت مكتبة لبوت
    if state and state.startswith('waiting_for_library_for_bot_'):
        fid = state.split('_')[-1]
        raw = message.text.strip()
        libs = [l.strip() for l in raw.replace(',', '\n').splitlines() if l.strip()]
        if not libs:
            send_formatted_message(chat_id, "خطأ", "أدخل اسم مكتبة واحدة على الأقل.", footer="أدخل اسماً.")
            user_states[user_id] = None
            return
        total = len(libs)
        status_msg = send_msg(chat_id, f"{EMOJI['wait']} جاري تثبيت المكتبات للبوت {fid}...")
        status_id = status_msg['message_id'] if status_msg else None
        results = []
        for i, lib in enumerate(libs, start=1):
            safe_lib = html.escape(lib)
            if status_id:
                send_formatted_message(chat_id, "جاري التثبيت", f"({i}/{total}) <code>{safe_lib}</code>", edit=True, message_id=status_id, footer="جارٍ التثبيت...")
            try:
                result = subprocess.run([sys.executable, '-m', 'pip', 'install', lib], capture_output=True, text=True, timeout=120)
                if result.returncode == 0:
                    results.append(f"{EMOJI['success']} {safe_lib}")
                else:
                    results.append(f"{EMOJI['error']} {safe_lib}")
            except Exception as e:
                results.append(f"{EMOJI['error']} {safe_lib} ({html.escape(str(e)[:60])})")
        summary = "\n".join(results)
        final_content = f"اكتمل تثبيت المكتبات للبوت {fid}:\n\n{summary}"
        send_formatted_message(chat_id, "تقرير التثبيت", final_content, edit=True, message_id=status_id, footer="تم التثبيت.")
        user_states[user_id] = None
        display_bot_management(chat_id, user_id, fid)
        return

    # تحديث التوكن
    if state and state.startswith('waiting_for_token_'):
        fid = state.split('_')[-1]
        new_token = message.text.strip()
        if not re.match(r'^\d{8,10}:[A-Za-z0-9_-]{35}$', new_token):
            send_formatted_message(chat_id, "خطأ", "توكن غير صحيح", footer="تأكد من الصيغة.")
            user_states[user_id] = None
            return
        c = get_cursor()
        c.execute('SELECT file_path, pid, main_file FROM bots WHERE id=? AND user_id=?', (fid, user_id))
        res = c.fetchone()
        if not res:
            send_formatted_message(chat_id, "خطأ", "البوت غير موجود", footer="تأكد من المعرف.")
            user_states[user_id] = None
            return
        path, pid, main_file = res
        bot_file = os.path.join(path, main_file) if main_file else path
        try:
            with open(bot_file, 'r', encoding='utf-8') as f:
                content = f.read()
            old_token_match = re.search(r'\d{8,10}:[A-Za-z0-9_-]{35}', content)
            if old_token_match:
                content = content.replace(old_token_match.group(0), new_token)
                with open(bot_file, 'w', encoding='utf-8') as f:
                    f.write(content)
            else:
                send_formatted_message(chat_id, "خطأ", "لم يتم العثور على توكن قديم في الملف", footer="تأكد من الملف.")
                user_states[user_id] = None
                return
            if is_process_running(pid):
                try:
                    terminate_process(pid, force=True)
                    time.sleep(1)
                    pid_new = run_bot_process(bot_file, cwd=path, bot_id=fid)
                    c.execute('UPDATE bots SET pid=? WHERE id=?', (pid_new, fid))
                    get_conn().commit()
                    token, bot_user = get_token_and_username(bot_file)
                    if token and token != "غير موجود":
                        threading.Thread(target=send_bot_started_notification, args=(user_id, fid, token, bot_user), daemon=True).start()
                except:
                    c.execute('UPDATE bots SET pid=0 WHERE id=?', (fid,))
                    get_conn().commit()
            send_formatted_message(chat_id, "نجاح", "تم تحديث التوكن", footer="تم التحديث.")
        except Exception as e:
            send_formatted_message(chat_id, "خطأ", f"خطأ: <code>{html.escape(str(e))}</code>", footer="حدث خطأ.")
        user_states[user_id] = None
        display_bot_management(chat_id, user_id, fid)
        return

    # الطرفية
    if state == 'waiting_for_terminal_command' and user_id == ADMIN_ID:
        command = message.text.strip()
        if command.lower() == '/cancel':
            user_states[user_id] = None
            send_formatted_message(chat_id, "الطرفية", "تم إلغاء الطرفية", buttons=[[create_btn('رجوع', callback='main_menu', color='blue')]], footer="تم الإلغاء.")
            return
        if not command:
            send_formatted_message(chat_id, "خطأ", "الرجاء إدخال أمر صالح.", footer="أدخل أمراً.")
            return
        status_msg = send_msg(chat_id, f"{EMOJI['wait']} جاري تنفيذ الأمر...")
        status_id = status_msg['message_id'] if status_msg else None
        try:
            output, success, error = execute_terminal_command_safe(command, timeout=TERMINAL_TIMEOUT)
            log_terminal_command(user_id, command, success, output[:100] if output else "")
            if success:
                if len(output) > 3000:
                    try:
                        file_data = io.BytesIO(output.encode('utf-8'))
                        file_data.name = f"terminal_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                        bot.send_document(chat_id, file_data, caption="ناتج الأمر الطويل")
                        send_formatted_message(chat_id, "ناتج الطرفية", "تم إرسال الناتج الكامل كملف.", edit=True, message_id=status_id, footer="تم الإرسال.")
                    except Exception as e:
                        send_formatted_message(chat_id, "خطأ", f"فشل إرسال الملف: <code>{html.escape(str(e))}</code>", edit=True, message_id=status_id, footer="حدث خطأ.")
                else:
                    send_formatted_message(chat_id, "ناتج الطرفية", f"<pre>{html.escape(output[:3000])}</pre>", edit=True, message_id=status_id, footer="تم التنفيذ بنجاح.")
            else:
                send_formatted_message(chat_id, "ناتج الطرفية", f"<pre>{html.escape(error or output[:1000])}</pre>", edit=True, message_id=status_id, footer="فشل التنفيذ.")
        except Exception as e:
            log_terminal_command(user_id, command, False, str(e)[:100])
            send_formatted_message(chat_id, "خطأ", f"خطأ أثناء التنفيذ: <code>{html.escape(str(e))}</code>", edit=True, message_id=status_id, footer="حدث خطأ.")
        send_formatted_message(chat_id, "الطرفية", "اختر أمراً آخر أو أعد تشغيل الطرفية.", buttons=[[create_btn('رجوع', callback='main_menu', color='blue')]], footer="انتهى الأمر.")
        user_states[user_id] = None
        return

    # /cancel
    if message.text == '/cancel':
        zip_dir = user_states.get(f'zip_dir_{user_id}')
        if zip_dir and os.path.exists(zip_dir):
            shutil.rmtree(zip_dir, ignore_errors=True)
        user_states[user_id] = None
        for k in [f'zip_dir_{user_id}', f'zip_name_{user_id}', f'py_files_{user_id}', f'zip_page_{user_id}']:
            user_states.pop(k, None)
        send_formatted_message(chat_id, "إلغاء", "تم الإلغاء.", footer="تم الإلغاء.")
        return

# ============================================================
#                    الخدمات الخلفية
# ============================================================

def start_background_services():
    init_permissions()
    threading.Thread(target=monitor_bots, daemon=True).start()
    threading.Thread(target=monitor_resources, daemon=True).start()
    threading.Thread(target=cleanup_loop, daemon=True).start()
    # مراقب الجدولة
    def scheduler_loop():
        while True:
            try:
                run_scheduled_tasks()
            except Exception as e:
                logger.error(f"خطأ في الجدولة: {e}")
            time.sleep(60)
    threading.Thread(target=scheduler_loop, daemon=True).start()
    logger.info("تم تشغيل جميع الخدمات الخلفية.")

def cleanup_loop():
    while True:
        try:
            cleanup_temp_files()
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
        time.sleep(21600)

def cleanup_temp_files():
    now = time.time()
    for fname in os.listdir('.'):
        if fname.startswith('temp_') and os.path.isfile(fname):
            try:
                mtime = os.path.getmtime(fname)
                if now - mtime > 3600:
                    os.remove(fname)
            except:
                pass
    for d in os.listdir('.'):
        if d.startswith('backup_') and os.path.isdir(d):
            try:
                mtime = os.path.getmtime(d)
                if now - mtime > 7 * 86400:
                    shutil.rmtree(d, ignore_errors=True)
            except:
                pass
    # تنظيف البيئات الافتراضية القديمة غير المستخدمة
    c = get_cursor()
    c.execute('SELECT bot_id, venv_path, last_used FROM envs')
    for bot_id, venv_path, last_used in c.fetchall():
        try:
            if last_used:
                last = datetime.fromisoformat(last_used)
                if (datetime.now() - last).days > 30:
                    if os.path.exists(venv_path):
                        shutil.rmtree(venv_path, ignore_errors=True)
                    c.execute('DELETE FROM envs WHERE bot_id=?', (bot_id,))
                    get_conn().commit()
        except:
            pass

# ============================================================
#                    بدء البوت
# ============================================================

if __name__ == '__main__':
    logger.info("تم صنع هذا البوت مجانا للمشتركين في قناة @ih_py")
    try:
        test = requests.get(f"https://api.telegram.org/bot{TOKEN}/getMe", timeout=5)
        if test.status_code == 200 and test.json().get('ok'):
            logger.info("التوكن صحيح، بدء التشغيل...")
        else:
            logger.error("التوكن غير صالح")
            sys.exit(1)
    except:
        logger.error("لا يمكن الاتصال بـ Telegram API")
        sys.exit(1)
    start_background_services()
    try:
        bot.infinity_polling(timeout=30, long_polling_timeout=20)
    except Exception as e:
        logger.error(f"توقف البوت: {e}")
        time.sleep(5)
        os.execv(sys.executable, [sys.executable] + sys.argv)
