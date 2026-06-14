import asyncio
import logging
import os
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiohttp import web

# 🤖 Bot sozlamalari
API_TOKEN = '8971349135:AAFQA40bJf45vQwb7Oe3yxtfQ4R-cRciDCg'
ADMIN_ID = 6198817749  
CHANNEL_ID = "@A_ToolsX"  # ✅ Majburiy obuna kanalingiz username'i

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# 📁 Ma'lumotlarni saqlash papkasi
DATA_DIR = "users_data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

COUNTER_FILE = os.path.join(DATA_DIR, "total_users.txt")
ID_MAP_FILE = os.path.join(DATA_DIR, "id_mapping.txt")

message_tracker = {}

# 📁 BAZA FUNKSIYALARI
def get_total_users_count():
    if not os.path.exists(COUNTER_FILE): return 0
    with open(COUNTER_FILE, "r") as f:
        try: return int(f.read().strip())
        except: return 0

def increment_users_count():
    count = get_total_users_count() + 1
    with open(COUNTER_FILE, "w") as f: f.write(str(count))
    return count

def generate_unique_4digit_id(tg_id):
    if os.path.exists(ID_MAP_FILE):
        with open(ID_MAP_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if f"{tg_id}:" in line: return line.strip().split(":")[1]
    
    existing_ids = set()
    if os.path.exists(ID_MAP_FILE):
        with open(ID_MAP_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if ":" in line: existing_ids.add(line.strip().split(":")[1])
                    
    while True:
        new_id = str(random.randint(1000, 9999))
        if new_id not in existing_ids:
            with open(ID_MAP_FILE, "a", encoding="utf-8") as f: f.write(f"{tg_id}:{new_id}\n")
            return new_id

def save_user_info_to_txt(tg_id, info):
    file_path = os.path.join(DATA_DIR, f"{tg_id}.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        for k, v in info.items(): f.write(f"{k}: {v}\n")

def read_user_info_from_txt(tg_id):
    file_path = os.path.join(DATA_DIR, f"{tg_id}.txt")
    if not os.path.exists(file_path): return {}
    info = {}
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if ": " in line:
                k, v = line.strip().split(": ", 1)
                info[k] = v
    return info

# 🔄 KANALGA OBUNANI TEKSHIRISH FUNKSIYASI
async def check_subscription(user_id: int) -> bool:
    if user_id == ADMIN_ID: return True  # Adminni tekshirmaymiz
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if member.status in ["member", "administrator", "creator"]:
            return True
        return False
    except Exception:
        return False

# ==================== HANDLERLAR ====================

# ADMIN START BOSGANDA
@dp.message(Command("start"), F.from_user.id == ADMIN_ID)
async def admin_welcome(message: types.Message):
    await message.answer(
        "👋 **Salom Admin (OTA)! Bot parallel Reply tizimida muvaffaqiyatli ishlamoqda.**\n\n"
        "Userlar yozgan xabarlarga shunchaki **Reply** qilib javob yozishingiz mumkin."
    )

# USER START BOSGANDA (YOKI TEKSHIRISH TUGMASI BOSILGANDA)
@dp.message(Command("start"), F.from_user.id != ADMIN_ID)
async def user_welcome(message: types.Message):
    tg_id = message.from_user.id
    
    # 📢 1. Kanalga a'zolikni tekshiramiz
    is_subscribed = await check_subscription(tg_id)
    if not is_subscribed:
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🚀 Kanalga a'zo bo'lish", url="https://t.me/A_ToolsX"))
        builder.row(types.InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_sub"))
        
        await message.answer(
            "🚀 To use this bot, you must join our channel:\nhttps://t.me/A_ToolsX",
            reply_markup=builder.as_markup()
        )
        return

    # 📁 2. Agar a'zo bo'lgan bo'lsa ma'lumotlarini rasmiylashtiramiz
    user_data = read_user_info_from_txt(tg_id)
    if not user_data:
        user_num = increment_users_count()
        custom_id = generate_unique_4digit_id(tg_id)
        
        user_data = {
            "Nechinchi_User": user_num,
            "Maxsus_Bot_ID": custom_id,
            "Telegram_ID": tg_id,
            "Ism": message.from_user.first_name or "Kiritilmagan",
            "Familiya": message.from_user.last_name or "Kiritilmagan",
            "Username": f"@{message.from_user.username}" if message.from_user.username else "Mavjud emas",
            "Telefon": "Ulashilmagan (Kutilmoqda)"
        }
        save_user_info_to_txt(tg_id, user_data)
    else:
        custom_id = user_data.get("Maxsus_Bot_ID")

    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="📞 Telefon raqamni yuborish", request_contact=True))
    
    welcome_text = (
        "Assalomu alaykum bizning Anonim nomlik bo'timizga xush kelibsiz \n"
        f"Sizning maxsus tizimdagi ID raqamingiz: {custom_id}\n\n"
        "bu bot haqida:agar siz istalgan habar yozsangiz u adminga yani developer ,OTA ga boradi "
        "u sizning yozgan habaringizni o'qiydi va javob yozadi agar siz botga spam bersangiz yoki "
        "negativ habar yozsangiz telegram sizni bloklaydi shunki ushbu bot Telegtam bilan hamkorlikda qurilgan "
        "OTA bilan maroqli suhbat tilaymiz!!!\n"
        "!!!ogohlantirish<<ushbu loyiha 49.9% telegramniki>>\n\n"
        "⚠️ Davom etish uchun pastdagi tugma orqali telefon raqamingizni tasdiqlang:"
    )
    await message.answer(welcome_text, reply_markup=builder.as_markup(resize_keyboard=True))

# OBUNANI TEKSHIRISH TUGMASI (CALLBACK)
@dp.callback_query(F.data == "check_sub")
async def callback_check_sub(callback: types.CallbackQuery):
    tg_id = callback.from_user.id
    is_subscribed = await check_subscription(tg_id)
    
    if is_subscribed:
        await callback.message.delete()  # Eski xabarni o'chirish
        # Start xabarini qaytadan chaqiramiz
        user_data = read_user_info_from_txt(tg_id)
        if not user_data:
            user_num = increment_users_count()
            custom_id = generate_unique_4digit_id(tg_id)
            user_data = {
                "Nechinchi_User": user_num,
                "Maxsus_Bot_ID": custom_id,
                "Telegram_ID": tg_id,
                "Ism": callback.from_user.first_name or "Kiritilmagan",
                "Familiya": callback.from_user.last_name or "Kiritilmagan",
                "Username": f"@{callback.from_user.username}" if callback.from_user.username else "Mavjud emas",
                "Telefon": "Ulashilmagan (Kutilmoqda)"
            }
            save_user_info_to_txt(tg_id, user_data)
        else:
            custom_id = user_data.get("Maxsus_Bot_ID")

        builder = ReplyKeyboardBuilder()
        builder.row(types.KeyboardButton(text="📞 Telefon raqamni yuborish", request_contact=True))
        
        welcome_text = (
            "Assalomu alaykum bizning Anonim nomlik bo'timizga xush kelibsiz \n"
            f"Sizning maxsus tizimdagi ID raqamingiz: {custom_id}\n\n"
            "bu bot haqida:agar siz istalgan habar yozsangiz u adminga yani developer ,OTA ga boradi...\n"
            "⚠️ Davom etish uchun pastdagi tugma orqali telefon raqamingizni tasdiqlang:"
        )
        await callback.message.answer(welcome_text, reply_markup=builder.as_markup(resize_keyboard=True))
    else:
        await callback.answer("❌ Siz hali ham kanalga a'zo bo'lmadingiz!", show_alert=True)

# FOYDALANUVCHI TELEFON RAQAMINI YUBORGANDA
@dp.message(F.contact, F.from_user.id != ADMIN_ID)
async def get_user_phone(message: types.Message):
    tg_id = message.from_user.id
    user_data = read_user_info_from_txt(tg_id)
    
    if user_data:
        phone = message.contact.phone_number
        user_data["Telefon"] = phone
        save_user_info_to_txt(tg_id, user_data)
        
        admin_alert = (
            f"🔔 **Yangi foydalanuvchi ro'yxatdan o'tdi!**\n\n"
            f"🔢 Mijoz tartibi: {user_data.get('Nechinchi_User')}-user\n"
            f"🆔 Berilgan ID: {user_data.get('Maxsus_Bot_ID')}\n"
            f"👤 Ism: {user_data.get('Ism')}\n"
            f"📞 Telefon: {phone}\n"
            f"📱 Haqiqiy TG ID: `{tg_id}`"
        )
        await bot.send_message(chat_id=ADMIN_ID, text=admin_alert)
        await message.answer("✅ Telefon raqamingiz tasdiqlandi. Endi anonim xabar yuborishingiz mumkin.", reply_markup=types.ReplyKeyboardRemove())

# ADMIN JAVOB BERGANDA (REPLY)
@dp.message(F.from_user.id == ADMIN_ID, F.reply_to_message)
async def admin_reply(message: types.Message):
    reply_id = message.reply_to_message.message_id
    user_id = message_tracker.get(reply_id)
    
    if not user_id:
        await message.answer("❌ Kechirasiz, xabar egasi topilmadi.")
        return
    try:
        await bot.copy_message(chat_id=user_id, from_chat_id=ADMIN_ID, message_id=message.message_id)
        await message.answer("✅ Javobingiz foydalanuvchiga yetkazildi.")
    except Exception:
        await message.answer("❌ Xabarni yuborib bo'lmadi.")

# USERDAN ADMINGA XABAR KELGANDA
@dp.message(F.from_user.id != ADMIN_ID)
async def forward_to_admin(message: types.Message):
    tg_id = message.from_user.id
    
    # Kanalga a'zolikni har safar xabar yozganda ham tekshirish (Xavfsizlik uchun)
    if not await check_subscription(tg_id):
        await message.answer("⚠️ Botdan foydalanish uchun avval kanalga a'zo bo'ling: /start")
        return

    user_data = read_user_info_from_txt(tg_id)
    if not user_data:
        await message.answer("⚠️ Iltimos, avval /start buyrug'ini bosing.")
        return
        
    custom_id = user_data.get("Maxsus_Bot_ID", "Noma'lum")
    user_num = user_data.get("Nechinchi_User", "?")
    
    # Faylga gapini log qilish
    file_path = os.path.join(DATA_DIR, f"{tg_id}.txt")
    if os.path.exists(file_path):
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"Xabari: {message.text or '[Media]'}\n")
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🆔 TG ID nusxalash", callback_data=f"get_id_{tg_id}"))
    
    await bot.send_message(chat_id=ADMIN_ID, text=f"📩 **User №{user_num} (ID: {custom_id}) dan xabar:**")
    sent_msg = await bot.copy_message(chat_id=ADMIN_ID, from_chat_id=tg_id, message_id=message.message_id, reply_markup=builder.as_markup())
    
    message_tracker[sent_msg.message_id] = tg_id
    await message.answer("🤫 Xabaringiz anonim tarzda adminga yuborildi!")

@dp.callback_query(lambda c: c.data.startswith('get_id_'))
async def show_id_to_admin(callback_query: types.CallbackQuery):
    user_id = callback_query.data.split('_')[2]
    await callback_query.message.answer(f"👤 Haqiqiy TG ID:\n`{user_id}`")
    await callback_query.answer()

# ==================== RENDER START ====================
async def handle(request): return web.Response(text="Bot is running!")

async def main():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', 10000).start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
