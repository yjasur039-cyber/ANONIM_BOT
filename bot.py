import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web

# 🤖 Bot sozlamalari
API_TOKEN = '8971349135:AAFQA40bJf45vQwb7Oe3yxtfQ4R-cRciDCg'
REAL_ADMIN_ID = 6198817749  # Sening haqiqiy Telegram ID raqaming

# 🎛 TEST REJIMI UCHUN SOXTA FOYDALANUVCHINING ID RAQAMI
# Rejim OFF bo'lganda bot sizni mana shu ID bilan simulyatsiya qiladi
SOXTA_USER_ID = 999999999

# Global o'zgaruvchi: Admin rejimi (True - Yoniq/Ko'k, False - O'chiq/Qizil)
ADMIN_MODE = True 

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# FSM tizimi
class AnonimChat(StatesGroup):
    tanlov_kutish = State()
    id_kutish = State()
    url_kutish = State()
    tel_kutish = State()
    suhbat_faol = State()

# Suhbatlar xotirasi
active_chats = {}

# Admin boshqaruv tugmachasi (Toggle Switch)
def get_toggle_keyboard():
    builder = InlineKeyboardBuilder()
    if ADMIN_MODE:
        builder.row(types.InlineKeyboardButton(text="🔵 Admin Mode: ON (Siz Adminsiz)", callback_data="toggle_admin_mode"))
    else:
        builder.row(types.InlineKeyboardButton(text="🔴 Admin Mode: OFF (Siz Usersiz)", callback_data="toggle_admin_mode"))
    return builder.as_markup()

# Admin bosh menyu tugmalari
def get_admin_keyboard():
    buttons = [
        [types.KeyboardButton(text="🆔 ID orqali ulanish")],
        [types.KeyboardButton(text="🔗 Username (URL) orqali")],
        [types.KeyboardButton(text="📞 Telefon raqam orqali")]
    ]
    return types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


# ==================== 🎛 TOGGLE HANDLER (REJIMNI ALMASHTIRISH) ====================

@dp.callback_query(F.data == "toggle_admin_mode", F.from_user.id == REAL_ADMIN_ID)
async def toggle_admin_mode(callback_query: types.CallbackQuery, state: FSMContext):
    global ADMIN_MODE
    ADMIN_MODE = not ADMIN_MODE  # Rejimni teskarisiga o'zgartiramiz
    
    await state.clear()  # Holatlarni tozalaymiz chalkashlik bo'lmasligi uchun
    
    if ADMIN_MODE:
        await callback_query.message.answer(
            "🔵 **Admin Mode yoqildi!**\nBot endi sizni haqiqiy ADMIN deb taniydi. Kimga yozishni tanlang:",
            reply_markup=get_admin_keyboard()
        )
    else:
        await callback_query.message.answer(
            "🔴 **Admin Mode o'chirildi!**\nBot endi sizni ODDIY USER deb hisoblaydi.\n\n"
            "Istalgan matn, rasm yoki emojini yozib yuboring, bot sizni adminga yo'naltirgandek o'zingizga qaytaradi!",
            reply_markup=types.ReplyKeyboardRemove()
        )
    
    # Tugma ko'rinishini ham srazi yangilaymiz
    await callback_query.message.edit_reply_markup(reply_markup=get_toggle_keyboard())
    await callback_query.answer()


# ==================== ADMIN BUYRUQLARI (ON holatida) ====================

@dp.message(Command("start"), F.from_user.id == REAL_ADMIN_ID)
async def admin_welcome(message: types.Message, state: FSMContext):
    await state.clear()
    
    # Switch tugmasini har doim startda ko'rsatamiz
    await message.answer(
        "👋 Salom Admin! Quyidagi tugma orqali o'zingizni 'User' qilib test qilib ko'rishingiz mumkin:",
        reply_markup=get_toggle_keyboard()
    )
    
    if ADMIN_MODE:
        await message.answer(
            "Kimga yozmoqchisiz? Quyidagilardan birini tanlang:",
            reply_markup=get_admin_keyboard()
        )
        await state.set_state(AnonimChat.tanlov_kutish)


@dp.message(AnonimChat.tanlov_kutish, F.from_user.id == REAL_ADMIN_ID)
async def admin_choice(message: types.Message, state: FSMContext):
    if not ADMIN_MODE: 
        return  # Rejim OFF bo'lsa bu qism ishlamaydi va pastdagi universal handlerga o'tadi
        
    matn = message.text
    if "🆔 ID" in matn:
        await message.answer("Suhbatdoshning Telegram **ID raqamini** yozing:", reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(AnonimChat.id_kutish)
    elif "🔗 Username" in matn:
        await message.answer("Suhbatdoshning **Username (yoki URL)** manzilini yozing:", reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(AnonimChat.url_kutish)
    elif "📞 Telefon" in matn:
        await message.answer("Suhbatdoshning **Telefon raqamini** kiriting:", reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(AnonimChat.tel_kutish)


@dp.message(AnonimChat.id_kutish, F.from_user.id == REAL_ADMIN_ID)
async def connect_by_id(message: types.Message, state: FSMContext):
    if not ADMIN_MODE: return
    target_id = message.text.strip()
    
    if not target_id.isdigit():
        await message.answer("❌ ID faqat raqamlardan iborat bo'lishi kerak. Qayta kiriting:")
        return
        
    target_id = int(target_id)
    try:
        await bot.send_chat_action(chat_id=target_id, action="typing")
        await state.update_data(current_target=target_id)
        active_chats[target_id] = REAL_ADMIN_ID
        
        await message.answer(f"✅ Ulanish muvaffaqiyatli! (ID: {target_id})\nSuhbatni tugatish uchun /stop yozing.")
        await state.set_state(AnonimChat.suhbat_faol)
    except Exception:
        await message.answer("❌ Bu foydalanuvchi botga ulanmagan yoki ID xato.\nQayta urinish uchun /start bosing.")
        await state.clear()


@dp.message(AnonimChat.url_kutish, F.from_user.id == REAL_ADMIN_ID)
@dp.message(AnonimChat.tel_kutish, F.from_user.id == REAL_ADMIN_ID)
async def connect_by_other(message: types.Message, state: FSMContext):
    await message.answer(
        "⚠️ **Telegram API Cheklovi:**\n"
        "Botlar to'g'ridan-to'g'ri telefon raqami yoki begona Username orqali odam topa olmaydi.\n"
        "Suhbat boshlash uchun baribir o'sha odamning **Raqamli ID'si** kerak bo'ladi."
    )
    await state.clear()


@dp.message(Command("stop"), AnonimChat.suhbat_faol, F.from_user.id == REAL_ADMIN_ID)
async def stop_chat(message: types.Message, state: FSMContext):
    data = await state.get_data()
    target_id = data.get("current_target")
    if target_id in active_chats:
        del active_chats[target_id]
    await state.clear()
    await message.answer("📴 Suhbat yakunlandi.", reply_markup=get_admin_keyboard())


# ==================== XABARLARNI YO'NALTIRISH (BRIDGE) ====================

# Admindan foydalanuvchiga yuborish (Faqat ADMIN_MODE ON va suhbat faol bo'lsa)
@dp.message(AnonimChat.suhbat_faol, F.from_user.id == REAL_ADMIN_ID)
async def forward_from_admin(message: types.Message, state: FSMContext):
    if not ADMIN_MODE:
        return  # Agar rejim OFF bo'lsa, xabar pastdagi universal qabul qiluvchiga tushadi

    data = await state.get_data()
    target_id = data.get("current_target")
    try:
        await bot.copy_message(chat_id=target_id, from_chat_id=REAL_ADMIN_ID, message_id=message.message_id)
    except Exception:
        await message.answer(f"❌ Xabarni yuborib bo'lmadi. Foydalanuvchi botni bloklagan bo'lishi mumkin.")


# FOYDALANUVCHIDAN ADMINGA KELISHI (Yoki Admin o'zini USER qilgandagi universal qism)
@dp.message()
async def forward_to_admin(message: types.Message):
    # Agar xabar haqiqiy adminning o'zidan kelayotgan bo'lsa VA Admin Mode yoqilgan bo'lsa - hech narsa qilmaymiz
    if message.from_user.id == REAL_ADMIN_ID and ADMIN_MODE:
        return

    # MUKAMMAL TOGGLE MANTIQI:
    # Agar xabar haqiqiy admindan kelayotgan bo'lsa VA rejim OFF bo'lsa, uni SOXTA_USER deb hisoblaymiz
    if message.from_user.id == REAL_ADMIN_ID and not ADMIN_MODE:
        current_user_id = SOXTA_USER_ID
    else:
        current_user_id = message.from_user.id
    
    # Inline-tugma yaratamiz va simulyatsiya qilingan yoki real ID'ni unga yuklaymiz
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="🆔 ID-ni nusxalash", callback_data=f"get_id_{current_user_id}")
    )
    
    # Xabarni adminga yo'naltirish (Klonlash)
    if current_user_id in active_chats:
        await bot.send_message(chat_id=REAL_ADMIN_ID, text=f"📩 **[Suhbatdosh ID: {current_user_id}]:**")
        await bot.copy_message(chat_id=REAL_ADMIN_ID, from_chat_id=message.from_user.id, message_id=message.message_id, reply_markup=builder.as_markup())
    else:
        await bot.send_message(chat_id=REAL_ADMIN_ID, text=f"🔔 **Yangi foydalanuvchidan anonim xabar keldi:**")
        await bot.copy_message(chat_id=REAL_ADMIN_ID, from_chat_id=message.from_user.id, message_id=message.message_id, reply_markup=builder.as_markup())
        
        # Agar bu real boshqa odam bo'lsa unga javob beramiz, admin o'zini test qilayotgan bo'lsa ortiqcha matn qaytarmaymiz
        if message.from_user.id != REAL_ADMIN_ID:
            await message.answer("🤫 Xabaringiz anonim tarzda adminga yuborildi!")


# Admin inline-tugmani bosganda ID raqamini ko'rsatuvchi qism
@dp.callback_query(lambda c: c.data.startswith('get_id_'))
async def show_id_to_admin(callback_query: types.CallbackQuery):
    user_id = callback_query.data.split('_')[2]
    await callback_query.message.answer(f"👤 Foydalanuvchi ID raqami:\n`{user_id}`\n\nUshbu ID-ni nusxalab, '🆔 ID orqali ulanish' tugmasi yordamida suhbat boshlashingiz mumkin.")
    await callback_query.answer()


# ==================== RENDER INTERFEKSI VA ISHGA TUSHIRISH ====================

async def handle(request):
    return web.Response(text="Bot is running completely free on Render!")

async def main():
    print("🚀 Bot muvaffaqiyatli ishga tushdi...")
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 10000)
    asyncio.create_task(site.start())
    
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot to'xtatildi.")
