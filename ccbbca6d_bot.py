ADMIN_ID = 7759804495
import sqlite3, logging, time, json, urllib.parse
from datetime import datetime
import telebot
from telebot import types

# ================== КОНФИГУРАЦИЯ ==================
TOKEN = "8624730170:AAHhr6HzfEr-UOA7uHAPEb-_2fzIehID31c"
OWNER_ID = 7759804495
DB_NAME = "shop_final_v8.db"

logging.basicConfig(level=logging.INFO)
bot = telebot.TeleBot(TOKEN)

try:
    BOT_USERNAME = bot.get_me().username
except:
    BOT_USERNAME = "resellers freefire"

# ================== БАЗА ДАННЫХ ==================
def init_db():
    with sqlite3.connect(DB_NAME) as c:
        c.execute("CREATE TABLE IF NOT EXISTS users (tg_id INTEGER PRIMARY KEY, phone TEXT, user TEXT, bal REAL DEFAULT 0, bonus REAL DEFAULT 0, sp REAL DEFAULT 0, buy_count INTEGER DEFAULT 0, lang TEXT DEFAULT 'ru', ban INTEGER DEFAULT 0, reg TEXT, referred_by INTEGER DEFAULT NULL)")
        c.execute("CREATE TABLE IF NOT EXISTS cats (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, description TEXT, photo TEXT, files TEXT DEFAULT '[]', tutor_file_id TEXT, tutor_text TEXT, tutor_type TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS prods (id INTEGER PRIMARY KEY AUTOINCREMENT, cat_id INTEGER, name TEXT, price REAL, desc TEXT, photo TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS keys (id INTEGER PRIMARY KEY AUTOINCREMENT, prod_id INTEGER, val TEXT, status TEXT DEFAULT 'free', owner INTEGER)")
        c.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, val TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT)")
        c.execute("INSERT OR IGNORE INTO settings (key, val) VALUES ('k_phone', '+77000000000'), ('k_name', 'Имя Ф.'), ('sup_link', '@admin')")
        c.execute("INSERT OR IGNORE INTO config (key, value) VALUES ('sub_required', '1'), ('sub_channels', '[]'), ('ref_reward_amount', '5')")
        c.commit()

def db(sql, params=(), commit=False, fetchone=False, fetchall=False):
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(sql, params)
        if commit: conn.commit()
        if fetchone: return cur.fetchone()
        if fetchall: return cur.fetchall()

def get_set(key): return db("SELECT val FROM settings WHERE key=?", (key,), fetchone=True)['val']
def get_config(key, default=None):
    res = db("SELECT value FROM config WHERE key=?", (key,), fetchone=True)
    return res['value'] if res else default
def set_config(key, value):
    db("UPDATE config SET value=? WHERE key=?", (str(value), key), commit=True)

init_db()

# ================== МУЛЬТИЯЗЫЧНОСТЬ ==================
T = {
    'ru': {
        'b_cat': "🛒 Товары",
        'b_prof': "👤 Профиль",
        'b_top': "💲 Пополнить Баланс",
        'b_info': "ℹ️ Информация",
        'b_sup': "👨‍💻 Поддержка",
        'b_lang': "🌍 Язык",
        'req_contact': "📱 Для использования бота необходимо отправить свой контакт. Нажмите кнопку ниже 👇",
        'btn_contact': "📱 Отправить контакт",
        'main_menu': "Главное меню:",
        'prof': "👤 Профиль:\n➖➖➖➖➖➖➖➖➖➖\n🔑 Мой ID: {id}\n👤 Мой логин: {user}\n➖➖➖➖➖➖➖➖➖➖\n💸 Мой баланс: {bal:g} 〒\n🎁 Мои бонусы: {bonus:g} 〒\n➖➖➖➖➖➖➖➖➖➖\n🛒 Количество покупок: {buy_count} шт\n💲 Сумма покупок: {sp:g} 〒",
        'info_msg': "Выберите нужную кнопку",
        'sup_msg': "👨‍💻 По всем вопросам писать: {sup}",
        'top_msg1': "💲Выберите Способ Оплаты:\n\nВы хотите пополнить баланс?\nНиже представлены способы пополнения баланса.",
        'top_msg2': "💳 Введите сумму пополнения (цифрами в 〒):",
        'top_msg3': "💳 ОПЛАТА KASPI\n➖➖➖➖➖➖➖➖➖➖\nПереведите {amt:g} 〒 по реквизитам:\n📞 {phone} ({name})\n\n📸 Отправьте скриншот чека сюда:",
        'top_wait': "⏳ Чек отправлен! Ожидайте зачисления.",
        'cat_msg': "🛒 Каталог товаров\n➖➖➖➖➖➖➖➖➖➖\nВыберите категорию ниже 👇",
        'cat_empty': "😔 Вы еще ничего не купили.",
        'my_purch': "🎁 ВАШИ ПОКУПКИ:\n➖➖➖➖➖➖➖➖➖➖\n",
        'prod_cat': "📁 Категория: {cat}\n➖➖➖➖➖➖➖➖➖➖\nВыберите нужный товар:",
        'prod_info': "📦 Товар: {name}\n➖➖➖➖➖➖➖➖➖➖\n📝 Описание:\n{desc}\n\n➖➖➖➖➖➖➖➖➖➖\n💸 Цена: {price:g} 〒\n📊 В наличии: {count} шт.",
        'buy_ok': "✅ УСПЕШНАЯ ПОКУПКА!\n➖➖➖➖➖➖➖➖➖➖\n📦 Товар: {name}\n💸 Списано: {price:g} 〒\n➖➖➖➖➖➖➖➖➖➖\n🔑 Ваш товар:\n{key}\n➖➖➖➖➖➖➖➖➖➖\nСпасибо за покупку! Товар также сохранен в разделе 'Мои покупки'.",
        'err_digit': "❌ Ошибка: ожидалась сумма цифрами.",
        'err_stock': "❌ Товар закончился!",
        'err_bal': "❌ Недостаточно средств на балансе!",
        'btn_buy': "🛒 Купить ({price:g} 〒)",
        'btn_no_stock': "❌ Нет в наличии",
        'btn_back': "🔙 Назад",
        'btn_my': "🎁 Мои покупки",
        'btn_in_shop': "🔙 В магазин",
        'sub_required_msg': "⚠️ <b>Міндетті жазылым!</b>\n\nБотты қолдануды жалғастыру үшін алдымен төмендегі каналдарға жазылуыңыз қажет.\n\nШарттарды орындап, «✅ Растау» батырмасын басыңыз:",
        'sub_not_all_msg': "❌ <b>Сіз барлық каналдарға тіркелмедіңіз!</b>\n\nӨтініш, шарттарды орындап, төмендегі «✅ Растау» батырмасын қайта басыңыз:",
        'btn_sub_confirm': "✅ Растау",
        'btn_referral': "👥 Рефералдар",
        'referral_info': "👥 <b>СЕРІКТЕСТІК БАҒДАРЛАМА</b>\n ➖ ➖ ➖ ➖ ➖ ➖ ➖ ➖ ➖\nДостарыңызды шақырып, сілтемеңіз арқылы кірген әрбір жаңа қолданушы үшін <b>+{reward} 〒</b> алыңыз!\n\n🔗 <b>Сіздің шақыру сілтемеңіз:</b>\n<code>https://t.me/{bot_username}?start=ref_{user_id}</code>\n ➖ ➖ ➖ ➖ ➖ ➖ ➖ ➖ ➖\n📊 <b>Сіздің статистикаңыз:</b>\n• 👥 Шақырылды: {ref_count} адам\n• 💰 Табысыңыз: {ref_earned} 〒",
        'btn_share': "🔗 Достарды шақыру",
        'btn_adm_sub_settings': "📢 Міндетті жазылымдар",
        'sub_settings_title': "📢 <b>Міндетті жазылу баптаулары (Настройка обязательной подписки)</b>\n\nБұл жерде сіз пайдаланушылар ботқа кірмес бұрын тіркелуі тиіс Telegram каналдарын реттей аласыз.\n\n⚠️ <b>МАҢЫЗДЫ:</b> Тексеру жүйесі дұрыс жұмыс істеуі үшін бот бұл каналдарда міндетті түрде <b>Әкімші (Администратор)</b> құқығына ие болуы қажет!",
        'sub_status_on': "🟢 Жазылым күйі: ҚОСУЛЫ (ВКЛ)",
        'sub_status_off': "🔴 Жазылым күйі: ӨШІРУЛІ (ВЫКЛ)",
        'btn_sub_add': "➕ Канал қосу",
        'btn_sub_del': "🗑️ Өшіру",
        'sub_add_chan_id': "📢 Канал қосу (Шарт 1/3):\n\nКаналдың <b>ID</b>-ін (мысалы: <code>-100123456789</code>) немесе <b>Юзернеймін</b> (мысалы: <code>@channel_username</code>) жіберіңіз:\n\n<i>(Бот бұл каналда міндетті түрде Әкімші болуы тиіс)</i>",
        'sub_add_chan_link': "📢 Канал сілтемесі (Шарт 2/3):\n\nКаналға өту сілтемесін жіберіңіз (мысалы: <code>https://t.me/invite_link</code> немесе <code>https://t.me/channel_username</code>):",
        'sub_add_chan_name': "📢 Батырма атауы (Шарт 3/3):\n\nПайдаланушыға батырмада көрсетілетін мәтінді жазыңыз (мысалы: <code>📢 Жазылу / Подписаться 1</code>):",
        'sub_chan_added': "✅ Канал сәтті қосылды!",
        'sub_chan_deleted': "🗑️ Канал өшірілді!",
        'btn_adm_ref_reward': "👥 Реферал сыйақысы",
        'ref_reward_current': "👥 <b>Реферал шақыру баптауы</b>\n\nҚазіргі бір адам шақырғанда берілетін сома: <b>{reward} 〒</b>\n\nЖаңа сыйақы сомасын енгізіңіз (тек бүтін санмен, 〒):",
        'ref_reward_updated': "✅ Реферал сыйақысы сәтті өзгертілді: {reward} 〒",
        'btn_cat_files': "📁 Файлдар",
        'btn_cat_tutor': "📖 Туториал",
        'no_files': "Категорияда файл жоқ.",
        'no_tutor': "Категорияда тутор жоқ.",
        'file_added': "✅ Файл сәтті қосылды!",
        'tutor_added': "✅ Тутор сәтті қосылды!",
        'file_deleted': "🗑️ Файлдар өшірілді!",
        'tutor_deleted': "🗑️ Тутор өшірілді!",
        'btn_del_files': "🗑️ Барлық файлдарды өшіру",
        'btn_del_tutor': "🗑️ Туторды өшіру",
        'cat_files_prompt': "Қай категорияға файл қосасыз:",
        'cat_tutor_prompt': "Қай категорияға тутор қосасыз:",
        'send_file_prompt': "Файл жіберіңіз:",
        'send_tutor_prompt': "Тутор фото немесе видео ретінде жіберіңіз:",
    },
    'kz': {
        'b_cat': "🛒 Тауарлар",
        'b_prof': "👤 Профиль",
        'b_top': "💲 Теңгерімді толтыру",
        'b_info': "ℹ️ Ақпарат",
        'b_sup': "👨‍💻 Қолдау",
        'b_lang': "🌍 Тіл",
        'req_contact': "📱 Ботты пайдалану үшін контактіңізді жіберу қажет. Төмендегі батырманы басыңыз 👇",
        'btn_contact': "📱 Контакт жіберу",
        'main_menu': "Басты мәзір:",
        'prof': "👤 Профиль:\n➖➖➖➖➖➖➖➖➖➖\n🔑 Менің ID: {id}\n👤 Менің логинім: {user}\n➖➖➖➖➖➖➖➖➖➖\n💸 Менің теңгерімім: {bal:g} 〒\n🎁 Менің бонустарым: {bonus:g} 〒\n➖➖➖➖➖➖➖➖➖➖\n🛒 Сатып алулар саны: {buy_count} дана\n💲 Сатып алу сомасы: {sp:g} 〒",
        'info_msg': "Қажетті батырманы таңдаңыз",
        'sup_msg': "👨‍💻 Барлық сұрақтар бойынша жазыңыз: {sup}",
        'top_msg1': "💲Төлем әдісін таңдаңыз:\n\nТеңгерімді толтырғыңыз келе ме?\nТөменде толтыру әдістері көрсетілген.",
        'top_msg2': "💳 Толтыру сомасын енгізіңіз (цифрмен 〒):",
        'top_msg3': "💳 KASPI ТӨЛЕМ\n➖➖➖➖➖➖➖➖➖➖\nРеквизиттер бойынша {amt:g} 〒 аударыңыз:\n📞 {phone} ({name})\n\n📸 Түбіртек скриншотын осында жіберіңіз:",
        'top_wait': "⏳ Түбіртек жіберілді! Түсуін күтіңіз.",
        'cat_msg': "🛒 Тауарлар каталогы\n➖➖➖➖➖➖➖➖➖➖\nТөменнен санатты таңдаңыз 👇",
        'cat_empty': "😔 Сіз әлі ештеңе сатып алмадыңыз.",
        'my_purch': "🎁 СІЗДІҢ САТЫП АЛУЛАРЫҢЫЗ:\n➖➖➖➖➖➖➖➖➖➖\n",
        'prod_cat': "📁 Санат: {cat}\n➖➖➖➖➖➖➖➖➖➖\nҚажетті тауарды таңдаңыз:",
        'prod_info': "📦 Тауар: {name}\n➖➖➖➖➖➖➖➖➖➖\n📝 Сипаттама:\n{desc}\n\n➖➖➖➖➖➖➖➖➖➖\n💸 Бағасы: {price:g} 〒\n📊 Қолжетімді: {count} дана.",
        'buy_ok': "✅ СӘТТІ САТЫП АЛУ!\n➖➖➖➖➖➖➖➖➖➖\n📦 Тауар: {name}\n💸 Жұмсалды: {price:g} 〒\n➖➖➖➖➖➖➖➖➖➖\n🔑 Сіздің тауарыңыз:\n{key}\n➖➖➖➖➖➖➖➖➖➖\nСатып алғаныңызға рахмет! Тауар 'Менің сатып алуларым' бөлімінде сақталды.",
        'err_digit': "❌ Қате: сома цифрмен күтілді.",
        'err_stock': "❌ Тауар таусылды!",
        'err_bal': "❌ Теңгерімде қаражат жеткіліксіз!",
        'btn_buy': "🛒 Сатып алу ({price:g} 〒)",
        'btn_no_stock': "❌ Қолжетімді емес",
        'btn_back': "🔙 Артқа",
        'btn_my': "🎁 Сатып алуларым",
        'btn_in_shop': "🔙 Дүкенге",
        'sub_required_msg': "⚠️ <b>Міндетті жазылым!</b>\n\nБотты қолдануды жалғастыру үшін алдымен төмендегі каналдарға жазылуыңыз қажет.\n\nШарттарды орындап, «✅ Растау» батырмасын басыңыз:",
        'sub_not_all_msg': "❌ <b>Сіз барлық каналдарға тіркелмедіңіз!</b>\n\nӨтініш, шарттарды орындап, төмендегі «✅ Растау» батырмасын қайта басыңыз:",
        'btn_sub_confirm': "✅ Растау",
        'btn_referral': "👥 Рефералдар",
        'referral_info': "👥 <b>СЕРІКТЕСТІК БАҒДАРЛАМА</b>\n ➖ ➖ ➖ ➖ ➖ ➖ ➖ ➖ ➖\nДостарыңызды шақырып, сілтемеңіз арқылы кірген әрбір жаңа қолданушы үшін <b>+{reward} 〒</b> алыңыз!\n\n🔗 <b>Сіздің шақыру сілтемеңіз:</b>\n<code>https://t.me/{bot_username}?start=ref_{user_id}</code>\n ➖ ➖ ➖ ➖ ➖ ➖ ➖ ➖ ➖\n📊 <b>Сіздің статистикаңыз:</b>\n• 👥 Шақырылды: {ref_count} адам\n• 💰 Табысыңыз: {ref_earned} 〒",
        'btn_share': "🔗 Достарды шақыру",
        'btn_adm_sub_settings': "📢 Міндетті жазылымдар",
        'sub_settings_title': "📢 <b>Міндетті жазылу баптаулары (Настройка обязательной подписки)</b>\n\nБұл жерде сіз пайдаланушылар ботқа кірмес бұрын тіркелуі тиіс Telegram каналдарын реттей аласыз.\n\n⚠️ <b>МАҢЫЗДЫ:</b> Тексеру жүйесі дұрыс жұмыс істеуі үшін бот бұл каналдарда міндетті түрде <b>Әкімші (Администратор)</b> құқығына ие болуы қажет!",
        'sub_status_on': "🟢 Жазылым күйі: ҚОСУЛЫ (ВКЛ)",
        'sub_status_off': "🔴 Жазылым күйі: ӨШІРУЛІ (ВЫКЛ)",
        'btn_sub_add': "➕ Канал қосу",
        'btn_sub_del': "🗑️ Өшіру",
        'sub_add_chan_id': "📢 Канал қосу (Шарт 1/3):\n\nКаналдың <b>ID</b>-ін (мысалы: <code>-100123456789</code>) немесе <b>Юзернеймін</b> (мысалы: <code>@channel_username</code>) жіберіңіз:\n\n<i>(Бот бұл каналда міндетті түрде Әкімші болуы тиіс)</i>",
        'sub_add_chan_link': "📢 Канал сілтемесі (Шарт 2/3):\n\nКаналға өту сілтемесін жіберіңіз (мысалы: <code>https://t.me/invite_link</code> немесе <code>https://t.me/channel_username</code>):",
        'sub_add_chan_name': "📢 Батырма атауы (Шарт 3/3):\n\nПайдаланушыға батырмада көрсетілетін мәтінді жазыңыз (мысалы: <code>📢 Жазылу / Подписаться 1</code>):",
        'sub_chan_added': "✅ Канал сәтті қосылды!",
        'sub_chan_deleted': "🗑️ Канал өшірілді!",
        'btn_adm_ref_reward': "👥 Реферал сыйақысы",
        'ref_reward_current': "👥 <b>Реферал шақыру баптауы</b>\n\nҚазіргі бір адам шақырғанда берілетін сома: <b>{reward} 〒</b>\n\nЖаңа сыйақы сомасын енгізіңіз (тек бүтін санмен, 〒):",
        'ref_reward_updated': "✅ Реферал сыйақысы сәтті өзгертілді: {reward} 〒",
        'btn_cat_files': "📁 Файлдар",
        'btn_cat_tutor': "📖 Туториал",
        'no_files': "Категорияда файл жоқ.",
        'no_tutor': "Категорияда тутор жоқ.",
        'file_added': "✅ Файл сәтті қосылды!",
        'tutor_added': "✅ Тутор сәтті қосылды!",
        'file_deleted': "🗑️ Файлдар өшірілді!",
        'tutor_deleted': "🗑️ Тутор өшірілді!",
        'btn_del_files': "🗑️ Барлық файлдарды өшіру",
        'btn_del_tutor': "🗑️ Туторды өшіру",
        'cat_files_prompt': "Қай категорияға файл қосасыз:",
        'cat_tutor_prompt': "Қай категорияға тутор қосасыз:",
        'send_file_prompt': "Файл жіберіңіз:",
        'send_tutor_prompt': "Тутор фото немесе видео ретінде жіберіңіз:",
    },
    'en': {
        'b_cat': "🛒 Products",
        'b_prof': "👤 Profile",
        'b_top': "💲 Top-up Balance",
        'b_info': "ℹ️ Information",
        'b_sup': "👨‍💻 Support",
        'b_lang': "🌍 Language",
        'req_contact': "📱 To use the bot, you need to send your contact. Click the button below 👇",
        'btn_contact': "📱 Send contact",
        'main_menu': "Main menu:",
        'prof': "👤 Profile:\n➖➖➖➖➖➖➖➖➖➖\n🔑 My ID: {id}\n👤 My login: {user}\n➖➖➖➖➖➖➖➖➖➖\n💸 My balance: {bal:g} 〒\n🎁 My bonuses: {bonus:g} 〒\n➖➖➖➖➖➖➖➖➖➖\n🛒 Purchases count: {buy_count} pcs\n💲 Total spent: {sp:g} 〒",
        'info_msg': "Choose the required button",
        'sup_msg': "👨‍💻 For all questions contact: {sup}",
        'top_msg1': "💲Choose Payment Method:\n\nDo you want to top up your balance?\nBelow are the top-up methods.",
        'top_msg2': "💳 Enter top-up amount (in 〒):",
        'top_msg3': "💳 KASPI PAYMENT\n➖➖➖➖➖➖➖➖➖➖\nTransfer {amt:g} 〒 to the details:\n📞 {phone} ({name})\n\n📸 Send the receipt screenshot here:",
        'top_wait': "⏳ Receipt sent! Please wait for the credit.",
        'cat_msg': "🛒 Product Catalog\n➖➖➖➖➖➖➖➖➖➖\nChoose a category below 👇",
        'cat_empty': "😔 You haven't bought anything yet.",
        'my_purch': "🎁 YOUR PURCHASES:\n➖➖➖➖➖➖➖➖➖➖\n",
        'prod_cat': "📁 Category: {cat}\n➖➖➖➖➖➖➖➖➖➖\nChoose a product:",
        'prod_info': "📦 Product: {name}\n➖➖➖➖➖➖➖➖➖➖\n📝 Description:\n{desc}\n\n➖➖➖➖➖➖➖➖➖➖\n💸 Price: {price:g} 〒\n📊 In stock: {count} pcs.",
        'buy_ok': "✅ SUCCESSFUL PURCHASE!\n➖➖➖➖➖➖➖➖➖➖\n📦 Product: {name}\n💸 Spent: {price:g} 〒\n➖➖➖➖➖➖➖➖➖➖\n🔑 Your product:\n{key}\n➖➖➖➖➖➖➖➖➖➖\nThank you for your purchase! The item is saved in 'My purchases'.",
        'err_digit': "❌ Error: amount expected in digits.",
        'err_stock': "❌ Out of stock!",
        'err_bal': "❌ Insufficient funds!",
        'btn_buy': "🛒 Buy ({price:g} 〒)",
        'btn_no_stock': "❌ Out of stock",
        'btn_back': "🔙 Back",
        'btn_my': "🎁 My purchases",
        'btn_in_shop': "🔙 To shop",
        'sub_required_msg': "⚠️ <b>Required subscription!</b>\n\nTo continue using the bot, you must subscribe to the following channels.\n\nFollow the conditions and press «✅ Confirm»:",
        'sub_not_all_msg': "❌ <b>You haven't subscribed to all channels!</b>\n\nPlease follow the conditions and press «✅ Confirm» again:",
        'btn_sub_confirm': "✅ Confirm",
        'btn_referral': "👥 Referrals",
        'referral_info': "👥 <b>REFERRAL PROGRAM</b>\n ➖ ➖ ➖ ➖ ➖ ➖ ➖ ➖ ➖\nInvite friends and get <b>+{reward} 〒</b> for each new user who registers via your link!\n\n🔗 <b>Your referral link:</b>\n<code>https://t.me/{bot_username}?start=ref_{user_id}</code>\n ➖ ➖ ➖ ➖ ➖ ➖ ➖ ➖ ➖\n📊 <b>Your statistics:</b>\n• 👥 Invited: {ref_count} people\n• 💰 Earned: {ref_earned} 〒",
        'btn_share': "🔗 Invite friends",
        'btn_adm_sub_settings': "📢 Required subscriptions",
        'sub_settings_title': "📢 <b>Required subscription settings</b>\n\nHere you can manage Telegram channels that users must subscribe to before using the bot.\n\n⚠️ <b>IMPORTANT:</b> For the check to work properly, the bot must be an <b>Administrator</b> in these channels!",
        'sub_status_on': "🟢 Status: ON",
        'sub_status_off': "🔴 Status: OFF",
        'btn_sub_add': "➕ Add channel",
        'btn_sub_del': "🗑️ Delete",
        'sub_add_chan_id': "📢 Add channel (Step 1/3):\n\nSend channel <b>ID</b> (e.g. <code>-100123456789</code>) or <b>Username</b> (e.g. <code>@channel_username</code>):\n\n<i>(Bot must be Administrator in this channel)</i>",
        'sub_add_chan_link': "📢 Channel link (Step 2/3):\n\nSend the link to the channel (e.g. <code>https://t.me/invite_link</code> or <code>https://t.me/channel_username</code>):",
        'sub_add_chan_name': "📢 Button name (Step 3/3):\n\nSend the text that will be shown on the button (e.g. <code>📢 Subscribe</code>):",
        'sub_chan_added': "✅ Channel successfully added!",
        'sub_chan_deleted': "🗑️ Channel deleted!",
        'btn_adm_ref_reward': "👥 Referral reward",
        'ref_reward_current': "👥 <b>Referral reward settings</b>\n\nCurrent reward for one referral: <b>{reward} 〒</b>\n\nEnter the new reward amount (integer, 〒):",
        'ref_reward_updated': "✅ Referral reward successfully updated: {reward} 〒",
        'btn_cat_files': "📁 Files",
        'btn_cat_tutor': "📖 Tutorial",
        'no_files': "No files in this category.",
        'no_tutor': "No tutorial in this category.",
        'file_added': "✅ File successfully added!",
        'tutor_added': "✅ Tutorial successfully added!",
        'file_deleted': "🗑️ Files deleted!",
        'tutor_deleted': "🗑️ Tutorial deleted!",
        'btn_del_files': "🗑️ Delete all files",
        'btn_del_tutor': "🗑️ Delete tutorial",
        'cat_files_prompt': "Which category to add files to:",
        'cat_tutor_prompt': "Which category to add tutorial to:",
        'send_file_prompt': "Send a file:",
        'send_tutor_prompt': "Send tutorial as photo or video:",
    }
}

def get_btn(key): return [T['ru'][key], T['kz'][key], T['en'][key]]

# ================== УПРАВЛЕНИЕ СОСТОЯНИЯМИ ==================
user_states = {}
def set_state(user_id, state_name, data=None):
    if data is None: data = {}
    user_states[user_id] = {'state': state_name, 'data': data}
def get_state(user_id):
    return user_states.get(user_id, {})
def clear_state(user_id):
    if user_id in user_states: del user_states[user_id]

# ================== КЛАВИАТУРЫ ==================
def lang_kb():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("🇷🇺 Русский", callback_data="l_ru"))
    kb.add(types.InlineKeyboardButton("🇰🇿 Қазақша", callback_data="l_kz"))
    kb.add(types.InlineKeyboardButton("🇬🇧 English", callback_data="l_en"))
    return kb

def contact_kb(lang):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(types.KeyboardButton(T[lang]['btn_contact'], request_contact=True))
    return kb

def main_kb(lang, user_id):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        types.KeyboardButton(T[lang]['b_cat']),
        types.KeyboardButton(T[lang]['b_prof']),
        types.KeyboardButton(T[lang]['b_top']),
        types.KeyboardButton(T[lang]['b_info']),
        types.KeyboardButton(T[lang]['b_sup']),
        types.KeyboardButton(T[lang]['b_lang']),
        types.KeyboardButton(T[lang]['btn_referral'])
    ]
    if int(user_id) == int(OWNER_ID):
        buttons.append(types.KeyboardButton("👑 Админ Панель"))
        kb.row(buttons[0], buttons[1])
        kb.row(buttons[2])
        kb.row(buttons[3], buttons[4])
        kb.row(buttons[5], buttons[6])
        kb.row(buttons[7])
    else:
        kb.row(buttons[0], buttons[1])
        kb.row(buttons[2])
        kb.row(buttons[3], buttons[4])
        kb.row(buttons[5], buttons[6])
    return kb

def adm_main_kb():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("📦 Управление товарами", callback_data="a_items"),
        types.InlineKeyboardButton("🔍 Поиск пользователя", callback_data="a_user"),
        types.InlineKeyboardButton("📢 Рассылка", callback_data="a_mail"),
        types.InlineKeyboardButton("⚙️ Настройки", callback_data="a_settings")
    )
    return kb

def adm_items_kb():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("📁 Добавить Категорию", callback_data="a_cat"),
        types.InlineKeyboardButton("🗑 Удалить Кат.", callback_data="a_del_cat")
    )
    kb.add(
        types.InlineKeyboardButton("📦 Добавить Товар", callback_data="a_prod"),
        types.InlineKeyboardButton("🗑 Удалить Товар", callback_data="a_del_prod")
    )
    kb.add(
        types.InlineKeyboardButton("✏️ Редактировать Товар", callback_data="a_edit_prod")
    )
    kb.add(
        types.InlineKeyboardButton("🔑 Залить Ключи", callback_data="a_keys")
    )
    kb.add(
        types.InlineKeyboardButton("📁 Файлы категории", callback_data="a_cat_files"),
        types.InlineKeyboardButton("📖 Тутор категории", callback_data="a_cat_tutor")
    )
    kb.add(
        types.InlineKeyboardButton("🔙 Назад", callback_data="a_back")
    )
    return kb

def adm_set_kb():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("✏️ Изменить Kaspi Номер", callback_data="set_kp"),
        types.InlineKeyboardButton("✏️ Изменить Kaspi Имя", callback_data="set_kn"),
        types.InlineKeyboardButton("✏️ Изменить Поддержку", callback_data="set_sup"),
        types.InlineKeyboardButton("📢 Міндетті жазылымдар", callback_data="adm_sub_settings"),
        types.InlineKeyboardButton("👥 Реферал сыйақысы", callback_data="adm_ref_reward"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="a_back")
    )
    return kb

# ================== ПОДПИСКА ==================
def get_sub_channels():
    try:
        channels = json.loads(get_config('sub_channels', '[]'))
        return channels if isinstance(channels, list) else []
    except:
        return []

def set_sub_channels(channels):
    set_config('sub_channels', json.dumps(channels))

def is_user_subscribed(user_id):
    if get_config('sub_required') != '1':
        return True
    channels = get_sub_channels()
    if not channels:
        return True
    for chan in channels:
        chan_id = chan.get('id')
        if not chan_id:
            continue
        try:
            member = bot.get_chat_member(chan_id, user_id)
            if member.status in ['left', 'kicked']:
                return False
        except:
            return False
    return True

def send_subscription_prompt(chat_id, lang, is_warn=False):
    markup = types.InlineKeyboardMarkup()
    channels = get_sub_channels()
    for idx, chan in enumerate(channels, 1):
        btn_name = chan.get('name', f"Канал {idx}")
        markup.row(types.InlineKeyboardButton(text=btn_name, url=chan.get('link')))
    markup.row(types.InlineKeyboardButton(text=T[lang]['btn_sub_confirm'], callback_data="user_sub_check"))
    msg_key = 'sub_not_all_msg' if is_warn else 'sub_required_msg'
    bot.send_message(chat_id, T[lang][msg_key], parse_mode="HTML", reply_markup=markup)

def check_subscription(chat_id):
    if int(chat_id) == int(OWNER_ID):
        return True
    if is_user_subscribed(chat_id):
        return True
    user = db("SELECT lang FROM users WHERE tg_id=?", (chat_id,), fetchone=True)
    lang = user['lang'] if user else 'ru'
    send_subscription_prompt(chat_id, lang, is_warn=False)
    return False

# ================== ФАЙЛЫ И ТУТОР ==================
def get_category_files(cat_id):
    res = db("SELECT files FROM cats WHERE id=?", (cat_id,), fetchone=True)
    if res and res['files']:
        try:
            return json.loads(res['files'])
        except:
            return []
    return []

def set_category_files(cat_id, files):
    db("UPDATE cats SET files=? WHERE id=?", (json.dumps(files), cat_id), commit=True)

def get_category_tutor(cat_id):
    res = db("SELECT tutor_file_id, tutor_text, tutor_type FROM cats WHERE id=?", (cat_id,), fetchone=True)
    if res:
        return {
            'file_id': res['tutor_file_id'],
            'text': res['tutor_text'],
            'type': res['tutor_type']
        }
    return None

def set_category_tutor(cat_id, file_id, text, media_type):
    db("UPDATE cats SET tutor_file_id=?, tutor_text=?, tutor_type=? WHERE id=?", (file_id, text, media_type, cat_id), commit=True)

def delete_category_tutor(cat_id):
    db("UPDATE cats SET tutor_file_id=NULL, tutor_text=NULL, tutor_type=NULL WHERE id=?", (cat_id,), commit=True)

def send_media(chat_id, file_id, media_type, caption):
    try:
        if media_type == 'photo':
            bot.send_photo(chat_id, file_id, caption=caption, parse_mode="HTML")
        elif media_type == 'video':
            bot.send_video(chat_id, file_id, caption=caption, parse_mode="HTML")
        elif media_type == 'document':
            bot.send_document(chat_id, file_id, caption=caption, parse_mode="HTML")
        elif media_type == 'animation':
            bot.send_animation(chat_id, file_id, caption=caption, parse_mode="HTML")
        else:
            bot.send_message(chat_id, caption, parse_mode="HTML")
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка отправки медиа: {e}")

# ================== СОСТОЯНИЯ ДЛЯ АДМИНКИ ФАЙЛОВ/ТУТОРА ==================
STATE_ADMIN_CAT_FILES_WAIT_FILE = 'adm_cat_files_wait_file'
STATE_ADMIN_CAT_TUTOR_WAIT_MEDIA = 'adm_cat_tutor_wait_media'

# ==============================================================================
# 1. РЕГИСТРАЦИЯ
# ==============================================================================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    clear_state(user_id)
    
    # Обработка реферальной ссылки
    if message.text and ' ' in message.text:
        try:
            ref_param = message.text.split()[1]
            if ref_param.startswith('ref_'):
                referrer_id = int(ref_param.split('_')[1])
                if referrer_id != user_id:
                    u = db("SELECT * FROM users WHERE tg_id=?", (user_id,), fetchone=True)
                    if not u:
                        db("INSERT INTO users (tg_id, user, reg) VALUES (?, ?, ?)", 
                           (user_id, message.from_user.username, datetime.now().strftime("%d.%m.%Y")), commit=True)
                        db("UPDATE users SET referred_by=? WHERE tg_id=?", (referrer_id, user_id), commit=True)
                        reward = int(get_config('ref_reward_amount', '5'))
                        db("UPDATE users SET bal=bal+?, referrals_count=referrals_count+1 WHERE tg_id=?", (reward, referrer_id), commit=True)
                        try:
                            bot.send_message(referrer_id, f"👥 Сіздің шақыру сілтемеңіз арқылы жаңа пайдаланушы тіркелді! Балансыңызға +{reward} 〒 қосылды.")
                        except:
                            pass
        except:
            pass

    u = db("SELECT * FROM users WHERE tg_id=?", (user_id,), fetchone=True)
    username = message.from_user.username or "Без логина"
    if not u:
        db("INSERT INTO users (tg_id, user, reg) VALUES (?, ?, ?)", 
           (user_id, username, datetime.now().strftime("%d.%m.%Y")), commit=True)
        bot.send_message(user_id, "🌍 Выберите язык / Тілді таңдаңыз / Choose language:", reply_markup=lang_kb())
    elif not u['lang']:
        bot.send_message(user_id, "🌍 Выберите язык / Тілді таңдаңыз / Choose language:", reply_markup=lang_kb())
    elif not u['phone']:
        bot.send_message(user_id, T[u['lang']]['req_contact'], reply_markup=contact_kb(u['lang']))
        set_state(user_id, 'phone')
    else:
        if u['ban']: return
        if not check_subscription(user_id):
            return
        bot.send_message(user_id, T[u['lang']]['main_menu'], reply_markup=main_kb(u['lang'], user_id))

@bot.callback_query_handler(func=lambda call: call.data.startswith("l_"))
def set_lang(call):
    user_id = call.from_user.id
    lang = call.data.split("_")[1]
    db("UPDATE users SET lang=? WHERE tg_id=?", (lang, user_id), commit=True)
    bot.delete_message(user_id, call.message.message_id)
    u = db("SELECT * FROM users WHERE tg_id=?", (user_id,), fetchone=True)
    if not u['phone']:
        bot.send_message(user_id, T[lang]['req_contact'], reply_markup=contact_kb(lang))
        set_state(user_id, 'phone')
    else:
        if not check_subscription(user_id):
            return
        bot.send_message(user_id, T[lang]['main_menu'], reply_markup=main_kb(lang, user_id))

@bot.message_handler(content_types=['contact'], func=lambda m: get_state(m.from_user.id).get('state') == 'phone')
def get_contact(message):
    user_id = message.from_user.id
    phone = message.contact.phone_number
    db("UPDATE users SET phone=? WHERE tg_id=?", (phone, user_id), commit=True)
    clear_state(user_id)
    u = db("SELECT lang FROM users WHERE tg_id=?", (user_id,), fetchone=True)
    lang = u['lang'] if u and u['lang'] else 'ru'
    bot.send_message(user_id, "✅", reply_markup=types.ReplyKeyboardRemove())
    if not check_subscription(user_id):
        return
    bot.send_message(user_id, T[lang]['main_menu'], reply_markup=main_kb(lang, user_id))

@bot.message_handler(func=lambda m: get_state(m.from_user.id).get('state') == 'phone')
def fallback_contact(message):
    user_id = message.from_user.id
    if message.text == "👑 Админ Панель":
        clear_state(user_id)
        adm_panel_btn(message)
        return
    u = db("SELECT lang FROM users WHERE tg_id=?", (user_id,), fetchone=True)
    lang = u['lang'] if u and u['lang'] else 'ru'
    bot.send_message(user_id, T[lang]['req_contact'], reply_markup=contact_kb(lang))

@bot.message_handler(func=lambda m: m.text == "👑 Админ Панель")
def adm_panel_btn(message):
    user_id = message.from_user.id
    if int(user_id) != int(OWNER_ID):
        bot.send_message(user_id, "⛔️ Ошибка доступа!")
        return
    users = db('SELECT COUNT(*) FROM users', fetchone=True)[0]
    bot.send_message(user_id, f"👑 <b>АДМИН ПАНЕЛЬ</b>\nВсего юзеров: {users}", reply_markup=adm_main_kb(), parse_mode="HTML")

# ==============================================================================
# 2. ПРОФИЛЬ, ИНФО, БАЛАНС
# ==============================================================================
@bot.message_handler(func=lambda m: m.text in get_btn('b_lang'))
def change_lang_btn(message):
    user_id = message.from_user.id
    clear_state(user_id)
    if not check_subscription(user_id):
        return
    bot.send_message(user_id, "🌍 Выберите язык / Тілді таңдаңыз / Choose language:", reply_markup=lang_kb())

@bot.message_handler(func=lambda m: m.text in get_btn('b_prof'))
def prof_btn(message):
    user_id = message.from_user.id
    clear_state(user_id)
    if not check_subscription(user_id):
        return
    u = db("SELECT * FROM users WHERE tg_id=?", (user_id,), fetchone=True)
    username = f"@{u['user']}" if u['user'] != "Без логина" else "Нет логина"
    bot.send_message(user_id, T[u['lang']]['prof'].format(id=u['tg_id'], user=username, bal=u['bal'], bonus=u['bonus'], buy_count=u['buy_count'], sp=u['sp']))

@bot.message_handler(func=lambda m: m.text in get_btn('b_info'))
def info_btn(message):
    user_id = message.from_user.id
    clear_state(user_id)
    if not check_subscription(user_id):
        return
    u = db("SELECT lang FROM users WHERE tg_id=?", (user_id,), fetchone=True)
    lang = u['lang']
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("📖 Правила", callback_data="dummy_btn"),
        types.InlineKeyboardButton("👨‍💻 Поддержка", url=get_set('sup_link').replace('@', 'https://t.me/'))
    )
    kb.add(
        types.InlineKeyboardButton("👨‍👩‍👧‍👦 Чат", callback_data="dummy_btn"),
        types.InlineKeyboardButton("💬 Отзывы", callback_data="dummy_btn")
    )
    kb.add(types.InlineKeyboardButton("📦 Пользовательское соглашение", callback_data="dummy_btn"))
    bot.send_message(user_id, T[lang]['info_msg'], reply_markup=kb)

@bot.message_handler(func=lambda m: m.text in get_btn('b_sup'))
def sup_btn(message):
    user_id = message.from_user.id
    clear_state(user_id)
    if not check_subscription(user_id):
        return
    u = db("SELECT lang FROM users WHERE tg_id=?", (user_id,), fetchone=True)
    bot.send_message(user_id, T[u['lang']]['sup_msg'].format(sup=get_set('sup_link')))

@bot.message_handler(func=lambda m: m.text in get_btn('b_top'))
def topup_menu(message):
    user_id = message.from_user.id
    clear_state(user_id)
    if not check_subscription(user_id):
        return
    u = db("SELECT lang FROM users WHERE tg_id=?", (user_id,), fetchone=True)
    lang = u['lang']
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("🇺🇸 CRYPTO-BOT", callback_data="dummy_btn"),
        types.InlineKeyboardButton("🇰🇿 KASPI BANK", callback_data="pay_kaspi"),
        types.InlineKeyboardButton("🇷🇺 YOUMONEY", callback_data="dummy_btn"),
        types.InlineKeyboardButton("💳 АКТИВИРОВАТЬ КУПОН", callback_data="dummy_btn")
    )
    bot.send_message(user_id, T[lang]['top_msg1'], reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data == "dummy_btn")
def dummy_alert(call):
    bot.answer_callback_query(call.id, "⏳ Временно недоступно / В разработке", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "pay_kaspi")
def pay_kaspi_start(call):
    user_id = call.from_user.id
    if not check_subscription(user_id):
        return
    u = db("SELECT lang FROM users WHERE tg_id=?", (user_id,), fetchone=True)
    lang = u['lang']
    bot.send_message(user_id, T[lang]['top_msg2'])
    set_state(user_id, 'top_amt', {'lang': lang})

@bot.message_handler(func=lambda m: get_state(m.from_user.id).get('state') == 'top_amt')
def topup_amt(message):
    user_id = message.from_user.id
    state = get_state(user_id)
    lang = state['data']['lang']
    if not message.text or not message.text.replace('.', '', 1).isdigit():
        clear_state(user_id)
        bot.send_message(user_id, T[lang]['err_digit'])
        return
    amt = float(message.text)
    state['data']['amt'] = amt
    bot.send_message(user_id, T[lang]['top_msg3'].format(amt=amt, phone=get_set('k_phone'), name=get_set('k_name')))
    set_state(user_id, 'top_rec', state['data'])

@bot.message_handler(content_types=['photo'], func=lambda m: get_state(m.from_user.id).get('state') == 'top_rec')
def topup_rec(message):
    user_id = message.from_user.id
    state = get_state(user_id)
    lang = state['data']['lang']
    amt = state['data']['amt']
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("✅ Принять", callback_data=f"adm_ok_{user_id}_{amt}"),
        types.InlineKeyboardButton("❌ Отклонить", callback_data=f"adm_no_{user_id}")
    )
    bot.send_photo(OWNER_ID, message.photo[-1].file_id, caption=f"🚨 <b>ЧЕК KASPI</b>\nОт: @{message.from_user.username} (<code>{user_id}</code>)\nСумма: <b>{amt:g} 〒</b>", reply_markup=kb, parse_mode="HTML")
    bot.send_message(user_id, T[lang]['top_wait'])
    clear_state(user_id)

# ==============================================================================
# 3. МАГАЗИН
# ==============================================================================
@bot.message_handler(func=lambda m: m.text in get_btn('b_cat'))
def catalog_main(message):
    user_id = message.from_user.id
    clear_state(user_id)
    if not check_subscription(user_id):
        return
    u = db("SELECT lang FROM users WHERE tg_id=?", (user_id,), fetchone=True)
    lang = u['lang']
    cats = db("SELECT * FROM cats", fetchall=True)
    kb = types.InlineKeyboardMarkup(row_width=1)
    for c in cats:
        kb.add(types.InlineKeyboardButton(f"📁 {c['name']}", callback_data=f"c_{c['id']}"))
    kb.add(types.InlineKeyboardButton(T[lang]['btn_my'], callback_data="my_purchases"))
    bot.send_message(user_id, T[lang]['cat_msg'], reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_catalog")
def back_to_catalog_call(call):
    user_id = call.from_user.id
    if not check_subscription(user_id):
        return
    u = db("SELECT lang FROM users WHERE tg_id=?", (user_id,), fetchone=True)
    lang = u['lang']
    cats = db("SELECT * FROM cats", fetchall=True)
    kb = types.InlineKeyboardMarkup(row_width=1)
    for cat in cats:
        kb.add(types.InlineKeyboardButton(f"📁 {cat['name']}", callback_data=f"c_{cat['id']}"))
    kb.add(types.InlineKeyboardButton(T[lang]['btn_my'], callback_data="my_purchases"))
    bot.edit_message_text(T[lang]['cat_msg'], user_id, call.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data == "my_purchases")
def my_purch_call(call):
    user_id = call.from_user.id
    if not check_subscription(user_id):
        return
    u = db("SELECT lang FROM users WHERE tg_id=?", (user_id,), fetchone=True)
    lang = u['lang']
    keys = db("SELECT p.name, k.val FROM keys k JOIN prods p ON k.prod_id = p.id WHERE k.owner=?", (user_id,), fetchall=True)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(T[lang]['btn_back'], callback_data="back_to_catalog"))
    if not keys:
        bot.edit_message_text(T[lang]['cat_empty'], user_id, call.message.message_id, reply_markup=kb)
        return
    res = T[lang]['my_purch']
    for idx, key in enumerate(keys, 1):
        res += f"{idx}. {key['name']}\nДанные: {key['val']}\n➖➖➖➖➖➖➖➖➖➖\n"
    bot.edit_message_text(res, user_id, call.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("c_"))
def prods_menu(call):
    user_id = call.from_user.id
    if not check_subscription(user_id):
        return
    u = db("SELECT lang FROM users WHERE tg_id=?", (user_id,), fetchone=True)
    lang = u['lang']
    cat_id = call.data.split("_")[1]
    cat = db("SELECT name, files, tutor_file_id, tutor_text, tutor_type FROM cats WHERE id=?", (cat_id,), fetchone=True)
    prods = db("SELECT * FROM prods WHERE cat_id=?", (cat_id,), fetchall=True)
    
    kb = types.InlineKeyboardMarkup(row_width=1)
    for p in prods:
        kb.add(types.InlineKeyboardButton(f"{p['name']} | {p['price']:g} 〒", callback_data=f"p_{p['id']}"))
    
    files = json.loads(cat['files']) if cat['files'] else []
    if files:
        kb.add(types.InlineKeyboardButton(T[lang]['btn_cat_files'], callback_data=f"cat_files_{cat_id}"))
    else:
        kb.add(types.InlineKeyboardButton(T[lang]['btn_cat_files'] + " ❌", callback_data=f"cat_files_{cat_id}"))
    
    if cat['tutor_file_id']:
        kb.add(types.InlineKeyboardButton(T[lang]['btn_cat_tutor'], callback_data=f"cat_tutor_{cat_id}"))
    else:
        kb.add(types.InlineKeyboardButton(T[lang]['btn_cat_tutor'] + " ❌", callback_data=f"cat_tutor_{cat_id}"))
    
    kb.add(types.InlineKeyboardButton(T[lang]['btn_back'], callback_data="back_to_catalog"))
    bot.edit_message_text(T[lang]['prod_cat'].format(cat=cat['name']), user_id, call.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_files_"))
def cat_files_handler(call):
    user_id = call.from_user.id
    cat_id = call.data.split("_")[2]
    u = db("SELECT lang FROM users WHERE tg_id=?", (user_id,), fetchone=True)
    lang = u['lang']
    files = get_category_files(cat_id)
    if not files:
        bot.answer_callback_query(call.id, T[lang]['no_files'], show_alert=True)
        return
    for f in files:
        send_media(user_id, f['file_id'], f['type'], f.get('text', ''))
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_tutor_"))
def cat_tutor_handler(call):
    user_id = call.from_user.id
    cat_id = call.data.split("_")[2]
    u = db("SELECT lang FROM users WHERE tg_id=?", (user_id,), fetchone=True)
    lang = u['lang']
    tutor = get_category_tutor(cat_id)
    if not tutor or not tutor['file_id']:
        bot.answer_callback_query(call.id, T[lang]['no_tutor'], show_alert=True)
        return
    send_media(user_id, tutor['file_id'], tutor['type'], tutor.get('text', ''))
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("p_"))
def prod_info(call):
    user_id = call.from_user.id
    if not check_subscription(user_id):
        return
    u = db("SELECT lang FROM users WHERE tg_id=?", (user_id,), fetchone=True)
    lang = u['lang']
    p_id = call.data.split("_")[1]
    p = db("SELECT * FROM prods WHERE id=?", (p_id,), fetchone=True)
    count = db("SELECT COUNT(*) as cnt FROM keys WHERE prod_id=? AND status='free'", (p_id,), fetchone=True)['cnt']
    kb = types.InlineKeyboardMarkup(row_width=1)
    if count > 0:
        kb.add(types.InlineKeyboardButton(T[lang]['btn_buy'].format(price=p['price']), callback_data=f"buy_{p['id']}"))
    else:
        kb.add(types.InlineKeyboardButton(T[lang]['btn_no_stock'], callback_data="dummy_btn"))
    kb.add(types.InlineKeyboardButton(T[lang]['btn_back'], callback_data=f"c_{p['cat_id']}"))
    bot.edit_message_text(T[lang]['prod_info'].format(name=p['name'], desc=p['desc'], price=p['price'], count=count), user_id, call.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def process_buy(call):
    user_id = call.from_user.id
    if not check_subscription(user_id):
        return
    u = db("SELECT * FROM users WHERE tg_id=?", (user_id,), fetchone=True)
    lang = u['lang']
    p_id = call.data.split("_")[1]
    p = db("SELECT * FROM prods WHERE id=?", (p_id,), fetchone=True)
    key = db("SELECT * FROM keys WHERE prod_id=? AND status='free' LIMIT 1", (p['id'],), fetchone=True)
    if not key:
        bot.answer_callback_query(call.id, T[lang]['err_stock'], show_alert=True)
        return
    if u['bal'] < p['price']:
        bot.answer_callback_query(call.id, T[lang]['err_bal'], show_alert=True)
        return
    db("UPDATE users SET bal=bal-?, sp=sp+?, buy_count=buy_count+1 WHERE tg_id=?", (p['price'], p['price'], user_id), commit=True)
    db("UPDATE keys SET status='sold', owner=? WHERE id=?", (user_id, key['id']), commit=True)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(T[lang]['btn_in_shop'], callback_data="back_to_catalog"))
    bot.edit_message_text(T[lang]['buy_ok'].format(name=p['name'], price=p['price'], key=key['val']), user_id, call.message.message_id, reply_markup=kb)
    try:
        bot.send_message(OWNER_ID, f"🛒 Покупка!\nПользователь: @{u['user']} (ID: {u['tg_id']})\nТовар: {p['name']}\nСумма: {p['price']:g} 〒")
    except: pass

# ==============================================================================
# 4. АДМИН ПАНЕЛЬ
# ==============================================================================
@bot.callback_query_handler(func=lambda call: call.data == "a_back")
def adm_back(call):
    user_id = call.from_user.id
    clear_state(user_id)
    users = db('SELECT COUNT(*) FROM users', fetchone=True)[0]
    bot.edit_message_text(f"👑 <b>АДМИН ПАНЕЛЬ</b>\nВсего юзеров: {users}", user_id, call.message.message_id, reply_markup=adm_main_kb(), parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "a_items")
def adm_items(call):
    user_id = call.from_user.id
    bot.edit_message_text("📦 <b>УПРАВЛЕНИЕ ТОВАРАМИ</b>", user_id, call.message.message_id, reply_markup=adm_items_kb(), parse_mode="HTML")

# --- ДОБАВИТЬ КАТЕГОРИЮ ---
@bot.callback_query_handler(func=lambda call: call.data == "a_cat")
def ac1(call):
    user_id = call.from_user.id
    bot.send_message(user_id, "Название новой категории:")
    set_state(user_id, 'cat_name')

@bot.message_handler(func=lambda m: get_state(m.from_user.id).get('state') == 'cat_name')
def ac2(message):
    user_id = message.from_user.id
    db("INSERT INTO cats (name) VALUES (?)", (message.text,), commit=True)
    bot.send_message(user_id, "✅ Категория добавлена!")
    clear_state(user_id)

# --- УДАЛИТЬ КАТЕГОРИЮ ---
@bot.callback_query_handler(func=lambda call: call.data == "a_del_cat")
def delc_1(call):
    user_id = call.from_user.id
    cats = db("SELECT * FROM cats", fetchall=True)
    kb = types.InlineKeyboardMarkup(row_width=1)
    for cat in cats:
        kb.add(types.InlineKeyboardButton(cat['name'], callback_data=f"delc_{cat['id']}"))
    kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="a_items"))
    bot.edit_message_text("Выберите категорию для удаления (все товары в ней тоже удалятся!):", user_id, call.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("delc_"))
def delc_2(call):
    user_id = call.from_user.id
    cid = call.data.split("_")[1]
    db("DELETE FROM cats WHERE id=?", (cid,), commit=True)
    db("DELETE FROM prods WHERE cat_id=?", (cid,), commit=True)
    bot.edit_message_text("✅ Категория и все ее товары удалены!", user_id, call.message.message_id, reply_markup=adm_items_kb())

# --- ДОБАВИТЬ ТОВАР ---
@bot.callback_query_handler(func=lambda call: call.data == "a_prod")
def ap1(call):
    user_id = call.from_user.id
    kb = types.InlineKeyboardMarkup(row_width=1)
    for cat in db("SELECT * FROM cats", fetchall=True):
        kb.add(types.InlineKeyboardButton(cat['name'], callback_data=f"sc_{cat['id']}"))
    bot.send_message(user_id, "В какую категорию добавить товар?", reply_markup=kb)
    set_state(user_id, 'p_cat')

@bot.callback_query_handler(func=lambda call: get_state(call.from_user.id).get('state') == 'p_cat' and call.data.startswith("sc_"))
def ap2(call):
    user_id = call.from_user.id
    cid = call.data.split("_")[1]
    set_state(user_id, 'p_name', {'cid': cid})
    bot.send_message(user_id, "Название товара:")

@bot.message_handler(func=lambda m: get_state(m.from_user.id).get('state') == 'p_name')
def ap3(message):
    user_id = message.from_user.id
    state = get_state(user_id)
    state['data']['n'] = message.text
    set_state(user_id, 'p_price', state['data'])
    bot.send_message(user_id, "Цена (только цифры):")

@bot.message_handler(func=lambda m: get_state(m.from_user.id).get('state') == 'p_price')
def ap4(message):
    user_id = message.from_user.id
    try:
        price = float(message.text)
    except:
        clear_state(user_id)
        bot.send_message(user_id, "❌ Ошибка: цена должна быть цифрой! Начни заново.")
        return
    state = get_state(user_id)
    state['data']['p'] = price
    set_state(user_id, 'p_desc', state['data'])
    bot.send_message(user_id, "Описание товара:")

@bot.message_handler(func=lambda m: get_state(m.from_user.id).get('state') == 'p_desc')
def ap5(message):
    user_id = message.from_user.id
    state = get_state(user_id)
    data = state['data']
    db("INSERT INTO prods (cat_id, name, price, desc) VALUES (?, ?, ?, ?)", (data['cid'], data['n'], data['p'], message.text), commit=True)
    bot.send_message(user_id, "✅ Товар успешно добавлен!")
    clear_state(user_id)

# --- УДАЛИТЬ ТОВАР ---
@bot.callback_query_handler(func=lambda call: call.data == "a_del_prod")
def delp_1(call):
    user_id = call.from_user.id
    cats = db("SELECT * FROM cats", fetchall=True)
    kb = types.InlineKeyboardMarkup(row_width=1)
    for cat in cats:
        kb.add(types.InlineKeyboardButton(cat['name'], callback_data=f"delpc_{cat['id']}"))
    kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="a_items"))
    bot.edit_message_text("Из какой категории удалить товар?", user_id, call.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("delpc_"))
def delp_2(call):
    user_id = call.from_user.id
    cid = call.data.split("_")[1]
    prods = db("SELECT * FROM prods WHERE cat_id=?", (cid,), fetchall=True)
    kb = types.InlineKeyboardMarkup(row_width=1)
    for p in prods:
        kb.add(types.InlineKeyboardButton(p['name'], callback_data=f"delp_{p['id']}"))
    kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="a_del_prod"))
    bot.edit_message_text("Какой товар удалить?", user_id, call.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("delp_"))
def delp_3(call):
    user_id = call.from_user.id
    pid = call.data.split("_")[1]
    db("DELETE FROM prods WHERE id=?", (pid,), commit=True)
    bot.edit_message_text("✅ Товар удален!", user_id, call.message.message_id, reply_markup=adm_items_kb())

# --- РЕДАКТИРОВАТЬ ТОВАР ---
@bot.callback_query_handler(func=lambda call: call.data == "a_edit_prod")
def ep_1(call):
    user_id = call.from_user.id
    cats = db("SELECT * FROM cats", fetchall=True)
    kb = types.InlineKeyboardMarkup(row_width=1)
    for cat in cats:
        kb.add(types.InlineKeyboardButton(cat['name'], callback_data=f"epc_{cat['id']}"))
    kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="a_items"))
    bot.edit_message_text("Категория товара для редактирования:", user_id, call.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("epc_"))
def ep_2(call):
    user_id = call.from_user.id
    cid = call.data.split("_")[1]
    prods = db("SELECT * FROM prods WHERE cat_id=?", (cid,), fetchall=True)
    kb = types.InlineKeyboardMarkup(row_width=1)
    for p in prods:
        kb.add(types.InlineKeyboardButton(p['name'], callback_data=f"ep_{p['id']}"))
    kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="a_edit_prod"))
    bot.edit_message_text("Выберите товар:", user_id, call.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("ep_"))
def ep_3(call):
    user_id = call.from_user.id
    pid = call.data.split("_")[1]
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("📝 Название", callback_data=f"edit_n_{pid}"),
        types.InlineKeyboardButton("💸 Цену", callback_data=f"edit_p_{pid}"),
        types.InlineKeyboardButton("📄 Описание", callback_data=f"edit_d_{pid}"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="a_items")
    )
    bot.edit_message_text("Что изменить у товара?", user_id, call.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_"))
def ep_4(call):
    user_id = call.from_user.id
    _, what, pid = call.data.split("_")
    set_state(user_id, 'edit_prod_val', {'epid': pid, 'what': what})
    if what == 'n': msg = "Введите новое название:"
    elif what == 'p': msg = "Введите новую цену (цифрами):"
    elif what == 'd': msg = "Введите новое описание:"
    bot.send_message(user_id, msg)

@bot.message_handler(func=lambda m: get_state(m.from_user.id).get('state') == 'edit_prod_val')
def ep_5(message):
    user_id = message.from_user.id
    state = get_state(user_id)
    what = state['data']['what']
    pid = state['data']['epid']
    if what == 'n':
        db("UPDATE prods SET name=? WHERE id=?", (message.text, pid), commit=True)
    elif what == 'p':
        try:
            val = float(message.text)
        except:
            bot.send_message(user_id, "❌ Цена должна быть цифрой!")
            return
        db("UPDATE prods SET price=? WHERE id=?", (val, pid), commit=True)
    elif what == 'd':
        db("UPDATE prods SET desc=? WHERE id=?", (message.text, pid), commit=True)
    bot.send_message(user_id, "✅ Товар успешно обновлен!")
    clear_state(user_id)

# --- ОСТАЛЬНАЯ АДМИНКА ---
@bot.callback_query_handler(func=lambda call: call.data == "a_keys")
def ak1(call):
    user_id = call.from_user.id
    kb = types.InlineKeyboardMarkup(row_width=1)
    for p in db("SELECT * FROM prods", fetchall=True):
        kb.add(types.InlineKeyboardButton(p['name'], callback_data=f"sp_{p['id']}"))
    bot.send_message(user_id, "В какой товар залить ключи?", reply_markup=kb)
    set_state(user_id, 'k_prod')

@bot.callback_query_handler(func=lambda call: get_state(call.from_user.id).get('state') == 'k_prod' and call.data.startswith("sp_"))
def ak2(call):
    user_id = call.from_user.id
    pid = call.data.split("_")[1]
    set_state(user_id, 'k_val', {'pid': pid})
    bot.send_message(user_id, "Скинь ключи (каждый с новой строки):")

@bot.message_handler(func=lambda m: get_state(m.from_user.id).get('state') == 'k_val')
def ak3(message):
    user_id = message.from_user.id
    state = get_state(user_id)
    pid = state['data']['pid']
    for k in message.text.split("\n"):
        if k.strip():
            db("INSERT INTO keys (prod_id, val) VALUES (?, ?)", (pid, k.strip()), commit=True)
    bot.send_message(user_id, "✅ Ключи успешно залиты!")
    clear_state(user_id)

# --- НАСТРОЙКИ ---
@bot.callback_query_handler(func=lambda call: call.data == "a_settings")
def adm_settings(call):
    user_id = call.from_user.id
    t = f"⚙️ <b>НАСТРОЙКИ БОТА</b>\n\n📞 Kaspi: <code>{get_set('k_phone')}</code>\n👤 Имя: <b>{get_set('k_name')}</b>\n👨‍💻 Саппорт: <b>{get_set('sup_link')}</b>"
    bot.edit_message_text(t, user_id, call.message.message_id, reply_markup=adm_set_kb(), parse_mode="HTML")

# --- ИЗМЕНЕНИЕ НОМЕРА KASPI ---
@bot.callback_query_handler(func=lambda call: call.data == "set_kp")
def s_kp(call):
    user_id = call.from_user.id
    bot.send_message(user_id, "Введите новый номер Kaspi:")
    set_state(user_id, 'set_kphone')

@bot.message_handler(func=lambda m: get_state(m.from_user.id).get('state') == 'set_kphone')
def s_kp2(message):
    user_id = message.from_user.id
    db("UPDATE settings SET val=? WHERE key='k_phone'", (message.text,), commit=True)
    bot.send_message(user_id, "✅ Номер Kaspi обновлен!")
    clear_state(user_id)

@bot.callback_query_handler(func=lambda call: call.data == "set_kn")
def s_kn(call):
    user_id = call.from_user.id
    bot.send_message(user_id, "Введите новое имя Kaspi:")
    set_state(user_id, 'set_kname')

@bot.message_handler(func=lambda m: get_state(m.from_user.id).get('state') == 'set_kname')
def s_kn2(message):
    user_id = message.from_user.id
    db("UPDATE settings SET val=? WHERE key='k_name'", (message.text,), commit=True)
    bot.send_message(user_id, "✅ Имя Kaspi обновлено!")
    clear_state(user_id)

@bot.callback_query_handler(func=lambda call: call.data == "set_sup")
def s_sup(call):
    user_id = call.from_user.id
    bot.send_message(user_id, "Введите ссылку на поддержку:")
    set_state(user_id, 'set_sup')

@bot.message_handler(func=lambda m: get_state(m.from_user.id).get('state') == 'set_sup')
def s_sup2(message):
    user_id = message.from_user.id
    db("UPDATE settings SET val=? WHERE key='sup_link'", (message.text,), commit=True)
    bot.send_message(user_id, "✅ Поддержка обновлена!")
    clear_state(user_id)

# ================== НАСТРОЙКИ ПОДПИСКИ (АДМИН) ==================
@bot.callback_query_handler(func=lambda call: call.data == "adm_sub_settings")
def adm_sub_settings_callback(call):
    adm_sub_settings(call)

def adm_sub_settings(chat_id_or_call, send_new=False):
    if isinstance(chat_id_or_call, types.CallbackQuery):
        call = chat_id_or_call
        user_id = call.from_user.id
        message_id = call.message.message_id
        chat_id = user_id
        is_callback = True
    else:
        chat_id = chat_id_or_call
        user_id = chat_id
        message_id = None
        is_callback = False
        send_new = True
    
    lang = db("SELECT lang FROM users WHERE tg_id=?", (user_id,), fetchone=True)['lang']
    markup = types.InlineKeyboardMarkup()
    sub_enabled = get_config('sub_required') == '1'
    status_text = T[lang]['sub_status_on'] if sub_enabled else T[lang]['sub_status_off']
    markup.add(types.InlineKeyboardButton(text=status_text, callback_data="adm_sub_toggle"))
    channels = get_sub_channels()
    for idx, chan in enumerate(channels):
        chan_name = chan.get('name', f"Канал {idx+1}")
        markup.row(
            types.InlineKeyboardButton(text=f"🔗 {chan_name}", url=chan.get('link', '#')),
            types.InlineKeyboardButton(text=T[lang]['btn_sub_del'], callback_data=f"adm_sub_del_{idx}")
        )
    markup.add(types.InlineKeyboardButton(text=T[lang]['btn_sub_add'], callback_data="adm_sub_add"))
    markup.add(types.InlineKeyboardButton(text="🔙 Назад", callback_data="a_back"))
    text = T[lang]['sub_settings_title']
    
    if send_new or not is_callback:
        bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)
    else:
        bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "adm_sub_toggle")
def adm_sub_toggle(call):
    user_id = call.from_user.id
    current = get_config('sub_required')
    new_val = '0' if current == '1' else '1'
    set_config('sub_required', new_val)
    bot.answer_callback_query(call.id, "✅ Статус изменен!")
    adm_sub_settings(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_sub_del_"))
def adm_sub_del(call):
    user_id = call.from_user.id
    idx = int(call.data.split("_")[3])
    channels = get_sub_channels()
    if 0 <= idx < len(channels):
        channels.pop(idx)
        set_sub_channels(channels)
        lang = db("SELECT lang FROM users WHERE tg_id=?", (user_id,), fetchone=True)['lang']
        bot.answer_callback_query(call.id, T[lang]['sub_chan_deleted'])
    adm_sub_settings(call)

@bot.callback_query_handler(func=lambda call: call.data == "adm_sub_add")
def adm_sub_add(call):
    user_id = call.from_user.id
    lang = db("SELECT lang FROM users WHERE tg_id=?", (user_id,), fetchone=True)['lang']
    bot.send_message(user_id, T[lang]['sub_add_chan_id'], parse_mode="HTML")
    set_state(user_id, 'adm_sub_add_id')

@bot.message_handler(func=lambda m: get_state(m.from_user.id).get('state') == 'adm_sub_add_id')
def adm_sub_add_id(message):
    user_id = message.from_user.id
    chan_id = message.text.strip()
    set_state(user_id, 'adm_sub_add_link', {'chan_id': chan_id})
    lang = db("SELECT lang FROM users WHERE tg_id=?", (user_id,), fetchone=True)['lang']
    bot.send_message(user_id, T[lang]['sub_add_chan_link'], parse_mode="HTML")

@bot.message_handler(func=lambda m: get_state(m.from_user.id).get('state') == 'adm_sub_add_link')
def adm_sub_add_link(message):
    user_id = message.from_user.id
    state = get_state(user_id)
    chan_id = state['data']['chan_id']
    chan_link = message.text.strip()
    set_state(user_id, 'adm_sub_add_name', {'chan_id': chan_id, 'chan_link': chan_link})
    lang = db("SELECT lang FROM users WHERE tg_id=?", (user_id,), fetchone=True)['lang']
    bot.send_message(user_id, T[lang]['sub_add_chan_name'], parse_mode="HTML")

@bot.message_handler(func=lambda m: get_state(m.from_user.id).get('state') == 'adm_sub_add_name')
def adm_sub_add_name(message):
    user_id = message.from_user.id
    state = get_state(user_id)
    chan_id = state['data']['chan_id']
    chan_link = state['data']['chan_link']
    chan_name = message.text.strip()
    channels = get_sub_channels()
    channels.append({'id': chan_id, 'link': chan_link, 'name': chan_name})
    set_sub_channels(channels)
    lang = db("SELECT lang FROM users WHERE tg_id=?", (user_id,), fetchone=True)['lang']
    bot.send_message(user_id, T[lang]['sub_chan_added'])
    clear_state(user_id)
    adm_sub_settings(user_id, send_new=True)

# ================== РЕФЕРАЛ СЫЙАҚЫСЫ (АДМИН) ==================
@bot.callback_query_handler(func=lambda call: call.data == "adm_ref_reward")
def adm_ref_reward(call):
    user_id = call.from_user.id
    lang = db("SELECT lang FROM users WHERE tg_id=?", (user_id,), fetchone=True)['lang']
    current = int(get_config('ref_reward_amount', '5'))
    bot.send_message(user_id, T[lang]['ref_reward_current'].format(reward=current), parse_mode="HTML")
    set_state(user_id, 'adm_ref_reward_set')

@bot.message_handler(func=lambda m: get_state(m.from_user.id).get('state') == 'adm_ref_reward_set')
def adm_ref_reward_set(message):
    user_id = message.from_user.id
    try:
        val = int(message.text.strip())
        if val < 0:
            raise ValueError
        set_config('ref_reward_amount', str(val))
        lang = db("SELECT lang FROM users WHERE tg_id=?", (user_id,), fetchone=True)['lang']
        bot.send_message(user_id, T[lang]['ref_reward_updated'].format(reward=val), parse_mode="HTML")
        clear_state(user_id)
    except:
        bot.send_message(user_id, "❌ Қате! Тек оң бүтін сан енгізіңіз.")

# ================== УПРАВЛЕНИЕ ФАЙЛАМИ КАТЕГОРИЙ (АДМИН) ==================
@bot.callback_query_handler(func=lambda call: call.data == "a_cat_files")
def adm_cat_files_choose(call):
    user_id = call.from_user.id
    cats = db("SELECT id, name FROM cats", fetchall=True)
    if not cats:
        bot.answer_callback_query(call.id, "❌ Категориялар жоқ!", show_alert=True)
        return
    kb = types.InlineKeyboardMarkup(row_width=1)
    for cat in cats:
        files = get_category_files(cat['id'])
        count = len(files)
        kb.add(types.InlineKeyboardButton(
            f"📁 {cat['name']} ({count} файл)",
            callback_data=f"adm_cat_files_show_{cat['id']}"
        ))
    kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="a_items"))
    bot.edit_message_text("📁 Категорияны таңдаңыз, оның файлдарын басқару үшін:", user_id, call.message.message_id, reply_markup=kb)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_cat_files_show_"))
def adm_cat_files_show(call):
    user_id = call.from_user.id
    cat_id = int(call.data.split("_")[-1])
    cat = db("SELECT name FROM cats WHERE id=?", (cat_id,), fetchone=True)
    if not cat:
        bot.answer_callback_query(call.id, "Категория табылмады!", show_alert=True)
        return
    files = get_category_files(cat_id)
    
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("➕ Файл қосу", callback_data=f"adm_cat_files_add_{cat_id}"),
        types.InlineKeyboardButton("🗑 Барлығын өшіру", callback_data=f"adm_cat_files_del_{cat_id}")
    )
    kb.add(types.InlineKeyboardButton("🔙 Артқа", callback_data="a_cat_files"))
    
    if files:
        text = f"📁 <b>{cat['name']}</b> – {len(files)} файл:\n"
        for i, f in enumerate(files, 1):
            text += f"{i}. {f.get('type', 'файл')}\n"
    else:
        text = f"📁 <b>{cat['name']}</b> – файлдар жоқ.\n\nТөменде «➕ Файл қосу» арқылы жаңа файл қоса аласыз."
    
    bot.edit_message_text(text, user_id, call.message.message_id, parse_mode="HTML", reply_markup=kb)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_cat_files_add_"))
def adm_cat_files_add(call):
    user_id = call.from_user.id
    cat_id = int(call.data.split("_")[-1])
    set_state(user_id, STATE_ADMIN_CAT_FILES_WAIT_FILE, {'cat_id': cat_id})
    bot.send_message(user_id, "📤 Файлды (сурет, құжат, видео) жіберіңіз. Қосымша мәтін жазсаңыз, ол файл сипаттамасы ретінде сақталады.")
    bot.answer_callback_query(call.id)

@bot.message_handler(content_types=['photo', 'document', 'video', 'animation'], 
                     func=lambda m: get_state(m.from_user.id).get('state') == STATE_ADMIN_CAT_FILES_WAIT_FILE)
def adm_cat_files_save_file(message):
    user_id = message.from_user.id
    state = get_state(user_id)
    cat_id = state['data'].get('cat_id')
    if not cat_id:
        clear_state(user_id)
        bot.send_message(user_id, "Қате, қайтадан бастаңыз.")
        return
    
    if message.content_type == 'photo':
        file_id = message.photo[-1].file_id
        media_type = 'photo'
    elif message.content_type == 'document':
        file_id = message.document.file_id
        media_type = 'document'
    elif message.content_type == 'video':
        file_id = message.video.file_id
        media_type = 'video'
    elif message.content_type == 'animation':
        file_id = message.animation.file_id
        media_type = 'animation'
    else:
        bot.send_message(user_id, "❌ Тек сурет, құжат, видео немесе GIF жіберіңіз.")
        return
    
    caption = message.caption or ""
    files = get_category_files(cat_id)
    files.append({'file_id': file_id, 'type': media_type, 'text': caption})
    set_category_files(cat_id, files)
    
    lang = db("SELECT lang FROM users WHERE tg_id=?", (user_id,), fetchone=True)['lang']
    bot.send_message(user_id, T[lang]['file_added'])
    clear_state(user_id)
    # Возврат к списку категорий
    class FakeCall:
        def __init__(self, user_id):
            self.from_user = type('obj', (object,), {'id': user_id})
            self.message = type('obj', (object,), {'message_id': None, 'chat': type('obj', (object,), {'id': user_id})})
            self.id = None
    adm_cat_files_choose(FakeCall(user_id))

@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_cat_files_del_"))
def adm_cat_files_del(call):
    user_id = call.from_user.id
    cat_id = int(call.data.split("_")[-1])
    set_category_files(cat_id, [])
    bot.answer_callback_query(call.id, "✅ Барлық файлдар өшірілді!")
    adm_cat_files_show(call)

# ================== УПРАВЛЕНИЕ ТУТОРОМ КАТЕГОРИЙ (АДМИН) ==================
@bot.callback_query_handler(func=lambda call: call.data == "a_cat_tutor")
def adm_cat_tutor_choose(call):
    user_id = call.from_user.id
    cats = db("SELECT id, name FROM cats", fetchall=True)
    if not cats:
        bot.answer_callback_query(call.id, "❌ Категориялар жоқ!", show_alert=True)
        return
    kb = types.InlineKeyboardMarkup(row_width=1)
    for cat in cats:
        tutor = get_category_tutor(cat['id'])
        has = "✅" if tutor and tutor['file_id'] else "❌"
        kb.add(types.InlineKeyboardButton(
            f"📖 {cat['name']} {has}",
            callback_data=f"adm_cat_tutor_show_{cat['id']}"
        ))
    kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="a_items"))
    bot.edit_message_text("📖 Категорияны таңдаңыз, оның туторын басқару үшін:", user_id, call.message.message_id, reply_markup=kb)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_cat_tutor_show_"))
def adm_cat_tutor_show(call):
    user_id = call.from_user.id
    cat_id = int(call.data.split("_")[-1])
    cat = db("SELECT name FROM cats WHERE id=?", (cat_id,), fetchone=True)
    if not cat:
        bot.answer_callback_query(call.id, "Категория табылмады!", show_alert=True)
        return
    tutor = get_category_tutor(cat_id)
    
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("➕ Тутор қосу/өзгерту", callback_data=f"adm_cat_tutor_add_{cat_id}"),
        types.InlineKeyboardButton("🗑 Туторды өшіру", callback_data=f"adm_cat_tutor_del_{cat_id}")
    )
    kb.add(types.InlineKeyboardButton("🔙 Артқа", callback_data="a_cat_tutor"))
    
    if tutor and tutor['file_id']:
        text = f"📖 <b>{cat['name']}</b> – тутор бар:\nТүрі: {tutor['type']}\n\nМәтін: {tutor.get('text', '')}"
    else:
        text = f"📖 <b>{cat['name']}</b> – тутор жоқ.\n\nТөменде «➕ Тутор қосу/өзгерту» арқылы жаңа тутор қоса аласыз."
    
    bot.edit_message_text(text, user_id, call.message.message_id, parse_mode="HTML", reply_markup=kb)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_cat_tutor_add_"))
def adm_cat_tutor_add(call):
    user_id = call.from_user.id
    cat_id = int(call.data.split("_")[-1])
    set_state(user_id, STATE_ADMIN_CAT_TUTOR_WAIT_MEDIA, {'cat_id': cat_id})
    bot.send_message(user_id, "📤 Туторды (сурет, видео немесе GIF) жіберіңіз. Қосымша мәтін жазсаңыз, ол тутор сипаттамасы ретінде сақталады.")
    bot.answer_callback_query(call.id)

@bot.message_handler(content_types=['photo', 'video', 'animation'], 
                     func=lambda m: get_state(m.from_user.id).get('state') == STATE_ADMIN_CAT_TUTOR_WAIT_MEDIA)
def adm_cat_tutor_save_media(message):
    user_id = message.from_user.id
    state = get_state(user_id)
    cat_id = state['data'].get('cat_id')
    if not cat_id:
        clear_state(user_id)
        bot.send_message(user_id, "Қате, қайтадан бастаңыз.")
        return
    
    if message.content_type == 'photo':
        file_id = message.photo[-1].file_id
        media_type = 'photo'
    elif message.content_type == 'video':
        file_id = message.video.file_id
        media_type = 'video'
    elif message.content_type == 'animation':
        file_id = message.animation.file_id
        media_type = 'animation'
    else:
        bot.send_message(user_id, "❌ Тутор ретінде тек сурет, видео немесе GIF жіберіңіз.")
        return
    
    caption = message.caption or ""
    set_category_tutor(cat_id, file_id, caption, media_type)
    
    lang = db("SELECT lang FROM users WHERE tg_id=?", (user_id,), fetchone=True)['lang']
    bot.send_message(user_id, T[lang]['tutor_added'])
    clear_state(user_id)
    class FakeCall:
        def __init__(self, user_id):
            self.from_user = type('obj', (object,), {'id': user_id})
            self.message = type('obj', (object,), {'message_id': None, 'chat': type('obj', (object,), {'id': user_id})})
            self.id = None
    adm_cat_tutor_choose(FakeCall(user_id))

@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_cat_tutor_del_"))
def adm_cat_tutor_del(call):
    user_id = call.from_user.id
    cat_id = int(call.data.split("_")[-1])
    delete_category_tutor(cat_id)
    bot.answer_callback_query(call.id, "✅ Тутор өшірілді!")
    adm_cat_tutor_show(call)

# ================== ПОИСК ПОЛЬЗОВАТЕЛЯ ==================
@bot.callback_query_handler(func=lambda call: call.data == "a_user")
def au1(call):
    user_id = call.from_user.id
    bot.send_message(user_id, "Введите ID пользователя:")
    set_state(user_id, 'find_u')

@bot.message_handler(func=lambda m: get_state(m.from_user.id).get('state') == 'find_u')
def au2(message):
    user_id = message.from_user.id
    if not message.text.isdigit():
        clear_state(user_id)
        bot.send_message(user_id, "❌ Ошибка: ID должен быть цифрами.")
        return
    u = db("SELECT * FROM users WHERE tg_id=?", (message.text,), fetchone=True)
    if not u:
        bot.send_message(user_id, "❌ Пользователь не найден.")
        clear_state(user_id)
        return
    set_state(user_id, 'a_ebal', {'tgt': u['tg_id']})
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("💰 Изменить баланс", callback_data="a_ebal"))
    bot.send_message(user_id, f"👤 @{u['user']}\n💰 {u['bal']:g} 〒", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data == "a_ebal")
def au3(call):
    user_id = call.from_user.id
    bot.send_message(user_id, "Введите сумму (с минусом чтобы отнять):")
    set_state(user_id, 'add_bal', get_state(user_id).get('data', {}))

@bot.message_handler(func=lambda m: get_state(m.from_user.id).get('state') == 'add_bal')
def au4(message):
    user_id = message.from_user.id
    try:
        val = float(message.text)
    except:
        bot.send_message(user_id, "❌ Введите цифру!")
        return
    tgt = get_state(user_id).get('data', {}).get('tgt')
    if not tgt:
        clear_state(user_id)
        return
    db("UPDATE users SET bal=bal+? WHERE tg_id=?", (val, tgt), commit=True)
    bot.send_message(user_id, "✅ Баланс обновлен!")
    clear_state(user_id)

# ================== ПРИНЯТИЕ ЧЕКОВ ==================
@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_ok_"))
def a_ok(call):
    user_id = call.from_user.id
    _, _, uid, amt = call.data.split("_")
    db("UPDATE users SET bal=bal+? WHERE tg_id=?", (float(amt), uid), commit=True)
    bot.edit_message_caption(caption=f"{call.message.caption}\n\n✅ <b>ОДОБРЕНО</b>", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="HTML")
    try:
        bot.send_message(uid, f"✅ Ваш баланс пополнен на {float(amt):g} 〒")
    except: pass

@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_no_"))
def a_no(call):
    _, _, uid = call.data.split("_")
    bot.edit_message_caption(caption=f"{call.message.caption}\n\n❌ <b>ОТКЛОНЕНО</b>", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="HTML")
    try:
        bot.send_message(uid, "❌ Ваш чек отклонен.")
    except: pass

# ================== РАССЫЛКА ==================
@bot.callback_query_handler(func=lambda call: call.data == "a_mail")
def am1(call):
    user_id = call.from_user.id
    bot.send_message(user_id, "Отправьте сообщение для рассылки:")
    set_state(user_id, 'broad')

@bot.message_handler(func=lambda m: get_state(m.from_user.id).get('state') == 'broad')
def am2(message):
    user_id = message.from_user.id
    users = db("SELECT tg_id FROM users", fetchall=True)
    success = 0
    for u in users:
        try:
            bot.copy_message(u['tg_id'], message.chat.id, message.message_id)
            success += 1
        except:
            pass
    bot.send_message(user_id, f"✅ Рассылка завершена! Отправлено: {success} юзерам.")
    clear_state(user_id)

# ================== ПРОВЕРКА ПОДПИСКИ (callback) ==================
@bot.callback_query_handler(func=lambda call: call.data == "user_sub_check")
def user_sub_check(call):
    user_id = call.from_user.id
    u = db("SELECT lang FROM users WHERE tg_id=?", (user_id,), fetchone=True)
    lang = u['lang'] if u else 'ru'
    if is_user_subscribed(user_id):
        bot.delete_message(user_id, call.message.message_id)
        bot.send_message(user_id, T[lang]['main_menu'], reply_markup=main_kb(lang, user_id))
    else:
        bot.answer_callback_query(call.id, T[lang]['sub_not_all_msg'].replace("<b>", "").replace("</b>", ""), show_alert=True)
        bot.delete_message(user_id, call.message.message_id)
        send_subscription_prompt(user_id, lang, is_warn=True)

# ================== РЕФЕРАЛЫ (пользователь) ==================
@bot.message_handler(func=lambda m: m.text in get_btn('btn_referral'))
def referral_handler(message):
    user_id = message.from_user.id
    if not check_subscription(user_id):
        return
    u = db("SELECT * FROM users WHERE tg_id=?", (user_id,), fetchone=True)
    if not u:
        return
    lang = u['lang']
    ref_count = db("SELECT COUNT(*) FROM users WHERE referred_by=?", (user_id,), fetchone=True)[0]
    ref_earned = 0  # Можно добавить отдельное поле, но пока оставляем
    reward = int(get_config('ref_reward_amount', '5'))
    bot_username = BOT_USERNAME
    share_url = f"https://t.me/{bot_username}?start=ref_{user_id}"
    share_text = urllib.parse.quote("Сәлем! Осы ботқа тіркеліп, тегін бонустар мен тауарларды ал! 🎁👇")
    full_share_link = f"tg://msg_url?url={share_url}&text={share_text}"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text=T[lang]['btn_share'], url=full_share_link))
    
    msg = T[lang]['referral_info'].format(
        reward=reward,
        bot_username=bot_username,
        user_id=user_id,
        ref_count=ref_count,
        ref_earned=ref_earned
    )
    bot.send_message(user_id, msg, parse_mode="HTML", reply_markup=markup)

# ==============================================================================
# ЗАПУСК БОТА
# ==============================================================================
print("\n" + "="*40)
print("✅ БОТ УСПЕШНО ЗАПУЩЕН И ГОТОВ К РАБОТЕ (telebot)!")
print("="*40 + "\n")
bot.polling(none_stop=True)
