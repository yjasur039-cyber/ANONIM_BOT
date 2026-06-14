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
API_TOKEN = '8971349135:AAFQA40bJf45vQwb7Oe3yxtfQ4R-cRciDCg'[cite: 1]
REAL_ADMIN_ID = 6198817749  # Sening haqiqiy Telegram ID raqaming[cite: 1]

# 🎛 TOGGLE SWITCH: Admin rejimi holati (True - Yoniq/Ko'k, False - O'chiq/Qizil)
ADMIN_MODE = True 

# Logging (Bot ishini konsolda kuzatish uchun)
logging.basicConfig(level=logging.INFO)[cite: 1]

bot = Bot(token=API_TOKEN)[cite: 1]
dp = Dispatcher(storage=MemoryStorage())[cite: 1]

# FSM (Bot xotirasida holatlarni saqlash tizimi)
class AnonimChat(StatesGroup):[cite: 1]
    tanlov_kutish = State()[cite: 1]
    id_kutish = State()[cite: 1]
    url_kutish = State()[cite: 1]
    tel_kutish = State()[cite: 1]
    suhbat_faol = State()[cite: 1]

# Suhbatdoshlar mosligi uchun vaqtinchalik xotira
active_chats = {}[cite: 1]

# Admin boshqaruv tugmachasi (Toggle Switch)
def get_toggle_keyboard():
    builder = InlineKeyboardBuilder()
    if ADMIN_MODE:
        builder.row(types.InlineKeyboardButton(text="🔵 Admin Mode: ON (Siz Adminsiz)", callback_data="toggle_admin_mode"))
    else:
        builder.row(types.InlineKeyboardButton(text="🔴 Admin Mode: OFF (Siz Usersiz)", callback_data="toggle_admin_mode"))
    return builder.as_markup()

# Admin uchun asosiy klaviatura
def get_admin_keyboard():[cite: 1]
    buttons = [[cite: 1]
        [types.KeyboardButton(text="🆔 ID orqali ulanish")],[cite: 1]
        [types.KeyboardButton(text="🔗 Username (URL) orqali")],[cite: 1]
        [types.KeyboardButton(text="📞 Telefon raqam orqali")][cite: 1]
    ][cite: 1]
    return types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)[cite: 1]


# ==================== 🎛 TOGGLE HANDLER (REJIMNI O'ZGARTIRISH) ====================

@dp.callback_query(F.data == "toggle_admin_mode", F.from_user.id == REAL_ADMIN_ID)
async def toggle_admin_mode(callback_query: types.CallbackQuery, state: FSMContext):
    global ADMIN_MODE
    ADMIN_MODE = not ADMIN_MODE  # Holatni teskarisiga o'zgartiramiz (True <-> False)
    
    await state.clear()  # Har safar rejim o'zgarganda holatni tozalaymiz
    
    if ADMIN_MODE:
        await callback_query.message.answer(
            "🔵 **Admin Mode yoqildi!**\nEndi bot sizni ADMIN deb taniydi. Kimga yozishni tanlang:",
            reply_markup=get_admin_keyboard()
        )
    else:
        await callback_query.message.answer(
            "🔴 **Admin Mode o'chirildi!**\nEndi bot sizni ODDIY USER deb hisoblaydi. Istalgan xabarni yozib o'zingizni test qiling!",
            reply_markup=types.ReplyKeyboardRemove()
        )
    
    # Boshqaruv tugmasi matnini yangilab qo'yamiz
    await callback_query.message.edit_reply_markup(reply_markup=get_toggle_keyboard())
    await callback_query.answer()


# ==================== ADMIN BUYRUQLARI ====================

# Admin botga kirganda (Faqat haqiqiy admin uchun)
@dp.message(Command("start"), F.from_user.id == REAL_ADMIN_ID)[cite: 1]
async def admin_welcome(message: types.Message, state: FSMContext):[cite: 1]
    await state.clear()[cite: 1]
    
    # Start bosilganda rejimni almashtirish tugmasini chiqaramiz
    await message.answer(
        "👋 Salom Admin! Quyidagi tugma orqali o'z rolingizni boshqarishingiz mumkin:",
        reply_markup=get_toggle_keyboard()
    )
    
    if ADMIN_MODE:
        await message.answer([cite: 1]
            "Kimga yozmoqchisiz? Quyidagilardan birini tanlang:",[cite: 1]
            reply_markup=get_admin_keyboard()[cite: 1]
        )[cite: 1]
        await state.set_state(AnonimChat.tanlov_kutish)[cite: 1]


# Admin tanlov qilganda (Faqat REAL_ADMIN va ADMIN_MODE yoniq bo'lsa ishlaydi)
@dp.message(AnonimChat.tanlov_kutish, F.from_user.id == REAL_ADMIN_ID)[cite: 1]
async def admin_choice(message: types.Message, state: FSMContext):[cite: 1]
    if not ADMIN_MODE: 
        return  # Rejim o'chiq bo'lsa, xabarni o'tkazib yubormaydi
        
    matn = message.text[cite: 1]
    
    if "🆔 ID" in matn:[cite: 1]
        await message.answer("Suhbatdoshning Telegram **ID raqamini** yozing:", reply_markup=types.ReplyKeyboardRemove())[cite: 1]
        await state.set_state(AnonimChat.id_kutish)[cite: 1]
    elif "🔗 Username" in matn:[cite: 1]
        await message.answer("Suhbatdoshning **Username (yoki URL)** manzilini yozing (Masalan: @username):", reply_markup=types.ReplyKeyboardRemove())[cite: 1]
        await state.set_state(AnonimChat.url_kutish)[cite: 1]
    elif "📞 Telefon" in matn:[cite: 1]
        await message.answer("Suhbatdoshning **Telefon raqamini** kiriting (Masalan: +998901234567):", reply_markup=types.ReplyKeyboardRemove())[cite: 1]
        await state.set_state(AnonimChat.tel_kutish)[cite: 1]
    else:[cite: 1]
        await message.answer("Iltimos, pastdagi tugmalardan birini tanlang.")[cite: 1]


# ID kiritilganda ulanish
@dp.message(AnonimChat.id_kutish, F.from_user.id == REAL_ADMIN_ID)[cite: 1]
async def connect_by_id(message: types.Message, state: FSMContext):[cite: 1]
    if not ADMIN_MODE: 
        return
        
    target_id = message.text.strip()[cite: 1]
    
    if not target_id.isdigit():[cite: 1]
        await message.answer("❌ ID faqat raqamlardan iborat bo'lishi kerak. Qayta kiriting:")[cite: 1]
        return[cite: 1]
        
    target_id = int(target_id)[cite: 1]
    
    try:[cite: 1]
        await bot.send_chat_action(chat_id=target_id, action="typing")[cite: 1]
        
        await state.update_data(current_target=target_id)[cite: 1]
        active_chats[target_id] = REAL_ADMIN_ID[cite: 1]
        
        await message.answer(f"✅ Ulanish muvaffaqiyatli! (ID: {target_id})\nEndi nima yozsangiz unga ANONIM tarzda boradi.\n\nSuhbatni tugatish uchun /stop deb yozing.")[cite: 1]
        await state.set_state(AnonimChat.suhbat_faol)[cite: 1]
        
    except Exception:[cite: 1]
        await message.answer("❌ Bu foydalanuvchi botga ulanmagan yoki ID xato.\nEslatma: Bot birinchi bo'lib begona odamga yozolmaydi. U odam botga kirib /start bosgan bo'lishi shart.\n\nQayta urinish uchun /start bosing.")[cite: 1]
        await state.clear()[cite: 1]


# Username yoki Telefon raqami kiritilganda
@dp.message(AnonimChat.url_kutish, F.from_user.id == REAL_ADMIN_ID)[cite: 1]
@dp.message(AnonimChat.tel_kutish, F.from_user.id == REAL_ADMIN_ID)[cite: 1]
async def connect_by_other(message: types.Message, state: FSMContext):[cite: 1]
    await message.answer([cite: 1]
        "⚠️ **Telegram API Cheklovi:**\n"[cite: 1]
        "Botlar to'g'ridan-to'g'ri telefon raqami yoki begona Username orqali odam topa olmaydi.\n\n"[cite: 1]
        "Suhbat boshlash uchun baribir o'sha odamning **Raqamli ID'si** kerak bo'ladi.\n"[cite: 1]
        "Iltimos, maqsadli foydalanuvchining ID raqamini topib, /start buyrug'i orqali qayta urining."[cite: 1]
    )[cite: 1]
    await state.clear()[cite: 1]


# Suhbatni tugatish buyrug'i
@dp.message(Command("stop"), AnonimChat.suhbat_faol, F.from_user.id == REAL_ADMIN_ID)[cite: 1]
async def stop_chat(message: types.Message, state: FSMContext):[cite: 1]
    data = await state.get_data()[cite: 1]
    target_id = data.get("current_target")[cite: 1]
    
    if target_id in active_chats:[cite: 1]
        del active_chats[target_id][cite: 1]
        
    await state.clear()[cite: 1]
    await message.answer("📴 Suhbat yakunlandi. Yangi suhbat boshlash uchun /start bosing.", reply_markup=get_admin_keyboard())[cite: 1]


# ==================== XABARLARNI YO'NALTIRISH (BRIDGE) ====================

# Admindan foydalanuvchiga (Faqat REAL_ADMIN va suhbat faol holatda bo'lsa)
@dp.message(AnonimChat.suhbat_faol, F.from_user.id == REAL_ADMIN_ID)[cite: 1]
async def forward_from_admin(message: types.Message, state: FSMContext):[cite: 1]
    if not ADMIN_MODE:
        # Agar admin o'zini USER rejimiga o'tkazgan bo'lsa, xabarni oddiy foydalanuvchi funksiyasiga otib yuboradi
        await forward_to_admin(message)
        return
        
    data = await state.get_data()[cite: 1]
    target_id = data.get("current_target")[cite: 1]
    
    try:[cite: 1]
        await bot.copy_message(chat_id=target_id, from_chat_id=REAL_ADMIN_ID, message_id=message.message_id)[cite: 1]
    except Exception:[cite: 1]
        await message.answer(f"❌ Xabarni yuborib bo'lmadi. Suhbatdosh botni bloklagan bo'lishi mumkin.")[cite: 1]


# Foydalanuvchidan Adminga (Yoki Admin o'zini USER rejimiga o'tkazganda)
@dp.message()[cite: 1]
async def forward_to_admin(message: types.Message):
    # Agar xabar haqiqiy adminning o'zidan kelayotgan bo'lsa VA Admin Mode yoqilgan bo'lsa, xabarni adminga yo'naltirmaydi
    if message.from_user.id == REAL_ADMIN_ID and ADMIN_MODE:
        return

    # Sening ajoyib taklifing: Agar ADMIN_MODE o'chiq bo'lsa sening ID-ingni 0 deb hisoblaydi!
    if message.from_user.id == REAL_ADMIN_ID and not ADMIN_MODE:
        user_id = 0
    else:
        user_id = message.from_user.id[cite: 1]
    
    # Inline tugma yaratamiz va ichiga yashirincha soxtalashtirilgan yoki asl user_id ni joylaymiz
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="🆔 ID-ni nusxalash", callback_data=f"get_id_{user_id}")
    )
    
    if user_id in active_chats:[cite: 1]
        await bot.send_message(chat_id=REAL_ADMIN_ID, text=f"📩 **[Suhbatdosh ID: {user_id}]:**")[cite: 1]
        await bot.copy_message(chat_id=REAL_ADMIN_ID, from_chat_id=message.from_user.id, message_id=message.message_id, reply_markup=builder.as_markup())
    else:
        # Agar admin u bilan hali suhbat boshlamagan bo'lsa ham xabarni tugma bilan adminga yuboradi
        await bot.send_message(chat_id=REAL_ADMIN_ID, text=f"🔔 **Yangi foydalanuvchidan anonim xabar keldi:**")
        await bot.copy_message(chat_id=REAL_ADMIN_ID, from_chat_id=message.from_user.id, message_id=message.message_id, reply_markup=builder.as_markup())
        await message.answer("🤫 Xabaringiz anonim tarzda adminga yuborildi!")


# Admin tugmani bosganda ID ni ko'rsatadigan qism
@dp.callback_query(lambda c: c.data.startswith('get_id_'))
async def show_id_to_admin(callback_query: types.CallbackQuery):
    user_id = callback_query.data.split('_')[2]
    await callback_query.message.answer(f"👤 Foydalanuvchi ID raqami:\n`{user_id}`\n\nUshbu ID-ni nusxalab, '🆔 ID orqali ulanish' tugmasi yordamida suhbat boshlashingiz mumkin.")
    await callback_query.answer()


# ==================== RENDER INTERFEKSI VA ISHGA TUSHIRISH ====================

async def handle(request):[cite: 1]
    return web.Response(text="Bot is running completely free on Render!")[cite: 1]

async def main():[cite: 1]
    print("🚀 Bot muvaffaqiyatli ishga tushdi...")[cite: 1]
    
    app = web.Application()[cite: 1]
    app.router.add_get('/', handle)[cite: 1]
    runner = web.AppRunner(app)[cite: 1]
    await runner.setup()[cite: 1]
    site = web.TCPSite(runner, '0.0.0.0', 10000)[cite: 1]
    asyncio.create_task(site.start())[cite: 1]
    
    await dp.start_polling(bot)[cite: 1]

if __name__ == '__main__':[cite: 1]
    try:[cite: 1]
        asyncio.run(main())[cite: 1]
    except (KeyboardInterrupt, SystemExit):[cite: 1]
        print("Bot to'xtatildi.")[cite: 1]
