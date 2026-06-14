import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web  # Render tekin serveri porti uchun

# 🤖 Bot sozlamalari
API_TOKEN = '8971349135:AAFQA40bJf45vQwb7Oe3yxtfQ4R-cRciDCg'
ADMIN_ID = 6198817749  # ✅ Sizning Telegram ID raqamingiz

# Logging (Bot ishini konsolda kuzatish uchun)
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# FSM (Bot xotirasida holatlarni saqlash tizimi)
class AnonimChat(StatesGroup):
    tanlov_kutish = State()
    id_kutish = State()
    url_kutish = State()
    tel_kutish = State()
    suhbat_faol = State()

# Suhbatdoshlar mosligi uchun vaqtinchalik xotira
active_chats = {}

# 🛠️ KLAVIATURA (Admin uchun tanlov tugmalari)
def get_admin_keyboard():
    buttons = [
        [types.KeyboardButton(text="🆔 ID orqali ulanish")],
        [types.KeyboardButton(text="🔗 Username (URL) orqali")],
        [types.KeyboardButton(text="📞 Telefon raqam orqali")]
    ]
    return types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


# ==================== ADMIN BUYRUQLARI ====================

# Admin botga kirganda
@dp.message(Command("start"), F.from_user.id == ADMIN_ID)
async def admin_welcome(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 Salom Admin! Siz mutlaqo anonim rejimdasiz.\n"
        "Kimga yozmoqchisiz? Quyidagilardan birini tanlang:",
        reply_markup=get_admin_keyboard()
    )
    await state.set_state(AnonimChat.tanlov_kutish)

# Admin tanlov qilganda
@dp.message(AnonimChat.tanlov_kutish, F.from_user.id == ADMIN_ID)
async def admin_choice(message: types.Message, state: FSMContext):
    matn = message.text
    
    if "🆔 ID" in matn:
        await message.answer("Suhbatdoshning Telegram **ID raqamini** yozing:", reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(AnonimChat.id_kutish)
    elif "🔗 Username" in matn:
        await message.answer("Suhbatdoshning **Username (yoki URL)** manzilini yozing (Masalan: @username):", reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(AnonimChat.url_kutish)
    elif "📞 Telefon" in matn:
        await message.answer("Suhbatdoshning **Telefon raqamini** kiriting (Masalan: +998901234567):", reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(AnonimChat.tel_kutish)
    else:
        await message.answer("Iltimos, pastdagi tugmalardan birini tanlang.")

# ID kiritilganda ulanish
@dp.message(AnonimChat.id_kutish, F.from_user.id == ADMIN_ID)
async def connect_by_id(message: types.Message, state: FSMContext):
    target_id = message.text.strip()
    
    if not target_id.isdigit():
        await message.answer("❌ ID faqat raqamlardan iborat bo'lishi kerak. Qayta kiriting:")
        return
        
    target_id = int(target_id)
    
    try:
        # Foydalanuvchi botga start bosganini tekshirish uchun "typing" yuboramiz
        await bot.send_chat_action(chat_id=target_id, action="typing")
        
        # Aloqani ulash
        await state.update_data(current_target=target_id)
        active_chats[target_id] = ADMIN_ID
        
        await message.answer(f"✅ Ulanish muvaffaqiyatli! (ID: {target_id})\nEndi nima yozsangiz unga ANONIM tarzda boradi.\n\nSuhbatni tugatish uchun /stop deb yozing.")
        await state.set_state(AnonimChat.suhbat_faol)
        
    except Exception:
        await message.answer("❌ Bu foydalanuvchi botga ulanmagan yoki ID xato.\nEslatma: Bot birinchi bo'lib begona odamga yozolmaydi. U odam botga kirib /start bosgan bo'lishi shart.\n\nQayta urinish uchun /start bosing.")
        await state.clear()

# Username yoki Telefon raqami kiritilganda (Telegram API cheklovi)
@dp.message(AnonimChat.url_kutish, F.from_user.id == ADMIN_ID)
@dp.message(AnonimChat.tel_kutish, F.from_user.id == ADMIN_ID)
async def connect_by_other(message: types.Message, state: FSMContext):
    await message.answer(
        "⚠️ **Telegram API Cheklovi:**\n"
        "Botlar to'g'ridan-to'g'ri telefon raqami yoki begona Username orqali odam topa olmaydi.\n\n"
        "Suhbat boshlash uchun baribir o'sha odamning **Raqamli ID'si** kerak bo'ladi.\n"
        "Iltimos, maqsadli foydalanuvchining ID raqamini topib, /start buyrug'i orqali qayta urining."
    )
    await state.clear()

# Suhbatni tugatish buyrug'i
@dp.message(Command("stop"), AnonimChat.suhbat_faol, F.from_user.id == ADMIN_ID)
async def stop_chat(message: types.Message, state: FSMContext):
    data = await state.get_data()
    target_id = data.get("current_target")
    
    if target_id in active_chats:
        del active_chats[target_id]
        
    await state.clear()
    await message.answer("📴 Suhbat yakunlandi. Yangi suhbat boshlash uchun /start bosing.", reply_markup=get_admin_keyboard())


# ==================== XABARLARNI YO'NALTIRISH (BRIDGE) ====================

# Admindan foydalanuvchiga (Klonlab yuborish)
@dp.message(AnonimChat.suhbat_faol, F.from_user.id == ADMIN_ID)
async def forward_from_admin(message: types.Message, state: FSMContext):
    data = await state.get_data()
    target_id = data.get("current_target")
    
    try:
        # copy_message xabarni klonlaydi (Sizning profilingiz mutlaqo yashirin qoladi)
        await bot.copy_message(chat_id=target_id, from_chat_id=ADMIN_ID, message_id=message.message_id)
    except Exception:
        await message.answer(f"❌ Xabarni yuborib bo'lmadi. Suhbatdosh botni bloklagan bo'lishi mumkin.")

# Foydalanuvchidan Adminga
@dp.message(F.from_user.id != ADMIN_ID)
async def forward_to_admin(message: types.Message):
    user_id = message.from_user.id
    
    if user_id in active_chats:
        await bot.send_message(chat_id=ADMIN_ID, text=f"📩 **[Suhbatdosh ID: {user_id}]:**")
        await bot.copy_message(chat_id=ADMIN_ID, from_chat_id=user_id, message_id=message.message_id)
    else:
        await message.answer("🤫 Bu maxfiy anonim bot. Hozircha siz bilan hech kim aloqaga chiqqani yo'q.")


# ==================== RENDER TEKIN PORTI VA BOTNI ISHGA TUSHIRISH ====================

# Render tekin xizmati so'raydigan mini veb-sahifa funksiyasi
async def handle(request):
    return web.Response(text="Bot is running completely free on Render!")

async def main():
    print("🚀 Bot muvaffaqiyatli ishga tushdi...")
    
    # Render tekin serverini aldaydigan orqa fon portini yoqamiz
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 10000)
    asyncio.create_task(site.start())
    
    # Bot pollingini ishga tushirish
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot to'xtatildi.")
