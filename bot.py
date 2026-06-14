import asyncio
import logging
import os
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiohttp import web

API_TOKEN = '8971349135:AAFQA40bJf45vQwb7Oe3yxtfQ4R-cRciDCg'
ADMIN_ID = 6198817749

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Papkalarni yaratish
DATA_DIR = "users_data"
os.makedirs(DATA_DIR, dict_mode=0o777, exist_ok=True)

# Tizim fayllari yo'llari
COUNTER_FILE = os.path.join(DATA_DIR, "total_users.txt")
ID_MAP_FILE = os.path.join(DATA_DIR, "id_mapping.txt")

message_tracker = {}

# 📁 YORDAMCHI FUNKSIYALAR (FAYLLAR BILAN ISHLASH)
def get_total_users_count():
    if not os.path.exists(COUNTER_FILE):
        return 0
    with open(COUNTER_FILE, "r") as f:
        try:
            return int(f.read().strip())
        except:
            return 0

def increment_users_count():
    count = get_total_users_count() + 1
    with open(COUNTER_FILE, "w") as f:
        f.write(str(count))
    return count

def generate_unique_4digit_id(tg_id):
    # Avval berilgan ID bormi tekshirish
    if os.path.exists(ID_MAP_FILE):
        with open(ID_MAP_FILE, "r") as f:
            for line in f:
                if f"{tg_id}:" in line:
                    return line.strip().split(":")[1]
    
    # Yangi 4 xonali ID yaratish
    existing_ids = set()
    if os.path.exists(ID_MAP_FILE):
        with open(ID_MAP_FILE, "r") as f:
            for line in f:
                if ":" in line:
                    existing_ids.add(line.strip().split(":")[1])
                    
    while True:
        new_id = str(random.randint(1000, 9999))
        if new_id not in existing_ids:
            with open(ID_MAP_FILE, "a") as f:
                f.append(f"{tg_id}:{new_id}\n")
            return new_id

def save_user_txt(tg_id, info_dict):
    file_path = os.path.join(DATA_DIR, f"{tg_id}.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        for key, val in info_dict.items():
            f.write(f"{key}: {val}\n")

def read_user_txt(tg_id):
    file_path = os.path.join(DATA_DIR, f"{tg_id}.txt")
    if not os.path.exists(file_path):
        return {}
    data = {}
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if ": " in line:
                k, v = line.strip().split(": ", 1)
                data[k] = v
    return data

# ==================== HANDLERLAR ====================

@dp.message(Command("start"), F.from_user.id == ADMIN_ID)
async def admin_welcome(message: types.Message):
    await message.answer("👋 Salom Admin! Bot parallel Reply tizimida ishlamoqda.")

@dp.message(Command("start"), F.from_user.id != ADMIN_ID)
async def user_welcome(message: types.Message):
    tg_id = message.from_user.id
    existing_data = read_user_txt(tg_id)
    
    # Agar birinchi marta kirayotgan bo'lsa
    if not existing_data:
        user_number = increment_users_count()
        custom_id = generate_unique_4digit_id(tg_id)
        
        user_info = {
            "Nomeri": user_number,
            "Bot_ID": custom_id,
            "Telegram_ID": tg_id,
            "Ism": message.from_user.first_name or "Mavjud emas",
            "Familiya": message.from_user.last_name or "Mavjud emas",
            "Username": f"@{message.from_user.username}" if message.from_user.username else "Mavjud emas",
            "Telefon": "Ulashilmagan"
        }
        save_user_txt(tg_id, user_info)
    else:
        custom_id = existing_data.get("Bot_ID")
        user_number = existing_data.get("Nomeri")
    
    # Telefon so'rash tugmasi
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="📞 Telefon raqamni yuborish", request_contact=True))
    
    user_text = (
        f"Assalomu alaykum bizning Anonim nomlik bo'timizga xush kelibsiz \n"
        f"Sizning maxsus ID raqamingiz: {custom_id}\n\n"
        f"bu bot haqida:agar siz istalgan habar yozsangiz u adminga yani developer ,OTA ga boradi "
        f"u sizning yozgan habaringizni o'qiydi va javob yozadi agar siz botga spam bersangiz yoki "
        f"negativ habar yozsangiz telegram sizni bloklaydi shunki ushbu bot Telegtam bilan hamkorlikda qurilgan "
        f"OTA bilan maroqli suhbat tilaymiz!!!\n"
        f"!!!ogohlantirish<<ushbu loyiha 49.9% telegramniki>>\n\n"
        f"⚠️ Iltimos, bot to'liq ishlashi uchun quyidagi tugma orqali telefon raqamingizni yuboring:"
    )
    await message.answer(user_text, reply_markup=builder.as_markup(resize_keyboard=True))

@dp.message(F.contact)
async def get_user_contact(message: types.Message):
    tg_id = message.from_user.id
    existing_data = read_user_txt(tg_id)
    
    if existing_data:
        existing_data["Telefon"] = message.contact.phone_number
        save_user_txt(tg_id, existing_data)
        
        # Adminga to'liq ma'lumotni yuborish
        admin_alert = (
            f"🔔 **Yangi foydalanuvchi ro'yxatdan o'tdi!**\n\n"
            f"🔢 Nechinchi user: {existing_data.get('Nomeri')}-mijoz\n"
            f"🆔 Maxsus ID: {existing_data.get('Bot_ID')}\n"
            f"👤 Ism: {existing_data.get('Ism')}\n"
            f"👥 Familiya: {existing_data.get('Familiya')}\n"
            f"🌐 Username: {existing_data.get('Username')}\n"
            f"📞 Telefon: {message.contact.phone_number}\n"
            f"📱 Telegram ID: `{tg_id}`"
        )
        await bot.send_message(chat_id=ADMIN_ID, text=admin_alert)
        await message.answer("✅ Rahmat! Ma'lumotlaringiz tasdiqlandi. Endi anonim xabar yo'llashingiz mumkin.", reply_markup=types.ReplyKeyboardRemove())

# ADMIN JAVOB BERGANDA
@dp.message(F.from_user.id == ADMIN_ID, F.reply_to_message)
async def admin_reply_to_user(message: types.Message):
    reply_id = message.reply_to_message.message_id
    user_id = message_tracker.get(reply_id)
    
    if not user_id:
        await message.answer("❌ Xabar egasi topilmadi.")
        return
    try:
        await bot.copy_message(chat_id=user_id, from_chat_id=ADMIN_ID, message_id=message.message_id)
        await message.answer("✅ Javob yetkazildi.")
    except Exception:
        await message.answer("❌ Foydalanuvchi botni bloklagan.")

# USERDAN ADMINGA XABAR KELGANDA
@dp.message(F.from_user.id != ADMIN_ID)
async def forward_to_admin(message: types.Message):
    tg_id = message.from_user.id
    user_data = read_user_txt(tg_id)
    custom_id = user_data.get("Bot_ID", "Noma'lum")
    user_num = user_data.get("Nomeri", "?")
    
    # TXT faylga u nima deb yozganini qo'shib qo'yamiz (Log sifatida)
    file_path = os.path.join(DATA_DIR, f"{tg_id}.txt")
    if os.path.exists(file_path):
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"Xabar: {message.text or '[Media/Stiker]'}\n")

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🆔 ID nusxalash", callback_data=f"get_id_{tg_id}"))
    
    await bot.send_message(chat_id=ADMIN_ID, text=f"📩 **User №{user_num} (ID: {custom_id}) dan xabar:**")
    sent_msg = await bot.copy_message(chat_id=ADMIN_ID, from_chat_id=tg_id, message_id=message.message_id, reply_markup=builder.as_markup())
    
    message_tracker[sent_msg.message_id] = tg_id
    await message.answer("🤫 Xabaringiz anonim tarzda adminga yuborildi!")

@dp.callback_query(lambda c: c.data.startswith('get_id_'))
async def show_id_to_admin(callback_query: types.CallbackQuery):
    user_id = callback_query.data.split('_')[2]
    await callback_query.message.answer(f"👤 Haqiqiy TG ID: `{user_id}`")
    await callback_query.answer()

async def handle(request): return web.Response(text="Bot running")

async def main():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', 10000).start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
