import telebot
import os
import time

# التوكن الجديد الخاص بك
API_TOKEN = '8381281831:AAE6RoiofMQINpAlbBr5wB1mlnOANqVQSXo'
bot = telebot.TeleBot(API_TOKEN)

working_dir = os.path.expanduser("~")
user_data = {}

# رابط صورة الترحيب
WELCOME_IMAGE = "https://ik.imagekit.io/apkqvdjhg/Screenshot_20260123_204501.jpg"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    name = message.from_user.first_name
    # نص الرسالة: كل خطوة في اقتباس منفرد + خط سميك
    welcome_text = (
        f"**أهــلاً بـك يـا {name} فـي بوت وضــع غــلاف للــملـفـات مـثل الصــوره 👆🏻**\n\n"
        "**الـخطـوات :**\n"
        "> **• أرسل الملف أولاً ❤️‍🔥**\n"
        "> **• أرسل صـوره الغلاف ❤️‍🔥**\n"
        "> **• أرسـل رسـاله للـوضع مـع الملــف بأي تنــسيـق تريــده ❤️‍🔥**\n\n"
        "**هـيا ارســل الــملف الآن 🌱**"
    )
    
    try:
        # استخدام MarkdownV2 لدعم الاقتباسات المنفصلة
        bot.send_photo(message.chat.id, WELCOME_IMAGE, caption=welcome_text, parse_mode='MarkdownV2')
    except Exception as e:
        bot.send_message(message.chat.id, welcome_text, parse_mode='MarkdownV2')

# 1. استقبال الملف
@bot.message_handler(content_types=['document'])
def handle_docs(message):
    user_data[message.chat.id] = {
        'file_id': message.document.file_id, 
        'file_name': message.document.file_name,
        'step': 'waiting_photo'
    }
    bot.reply_to(message, "✅ **تم استلام الملف**\n\n🖼️ الآن أرسل **صورة الغلاف** (JPG).", parse_mode='Markdown')

# 2. استقبال الصورة
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    if chat_id not in user_data or user_data[chat_id]['step'] != 'waiting_photo':
        bot.reply_to(message, "⚠️ يرجى إرسال الملف أولاً!")
        return
        
    user_data[chat_id]['photo_id'] = message.photo[-1].file_id
    user_data[chat_id]['step'] = 'waiting_caption'
    bot.reply_to(message, "✅ **تم حفظ الغلاف**\n\n✍️ أرسل الآن **الرسالة والوصف** المنسق للملف.", parse_mode='Markdown')

# 3. استقبال الوصف والإرسال النهائي
@bot.message_handler(func=lambda message: message.chat.id in user_data and user_data[message.chat.id]['step'] == 'waiting_caption')
def handle_final_step(message):
    chat_id = message.chat.id
    data = user_data[chat_id]
    
    status_msg = bot.send_message(chat_id, "⏳ **جاري المعالجة...**", parse_mode='Markdown')

    temp_file = os.path.join(working_dir, data['file_name'])
    temp_thumb = os.path.join(working_dir, f"thumb_{chat_id}.jpg")

    try:
        file_info = bot.get_file(data['file_id'])
        photo_info = bot.get_file(data['photo_id'])
        
        with open(temp_file, 'wb') as f:
            f.write(bot.download_file(file_info.file_path))
        with open(temp_thumb, 'wb') as f:
            f.write(bot.download_file(photo_info.file_path))

        with open(temp_file, 'rb') as doc, open(temp_thumb, 'rb') as thumb:
            bot.send_document(
                chat_id, 
                doc, 
                thumbnail=thumb, 
                caption=message.text, 
                caption_entities=message.entities
            )

        bot.delete_message(chat_id, status_msg.message_id)
        bot.send_message(chat_id, "✨ **تم الانتهاء بنجاح!**", parse_mode='Markdown')

    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ: {e}")
    
    finally:
        if os.path.exists(temp_file): os.remove(temp_file)
        if os.path.exists(temp_thumb): os.remove(temp_thumb)
        del user_data[chat_id]

# تشغيل البوت مع إعادة الاتصال التلقائي
while True:
    try:
        print("🚀 البوت يعمل الآن بالتوكن الجديد...")
        bot.infinity_polling(timeout=20, long_polling_timeout=10)
    except Exception as e:
        print(f"🔄 محاولة اتصال: {e}")
        time.sleep(5)