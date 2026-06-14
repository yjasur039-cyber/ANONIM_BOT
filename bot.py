import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web

# 🤖 Bot sozlamalari
API_TOKEN = '8971349135:AAFQA40bJf45vQwb7Oe3yxtfQ4R-cRciDCg'
ADMIN_ID = 6198817749  # ✅ Sizning Telegram ID raqamingiz

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Xabarlarni bog'lash uchun vaqtinchalik xotira (Qaysi xabar adminga borganda qaysi userdan kelganini eslab qoladi)
# Bu tizim Reply qilganda adashib ketmaslikni ta'minlaydi
message_tracker = {}

# ==================== ADMIN BUYRUQLARI ====================

@dp.message(Command("start"), F.from_user.id == ADMIN_ID)
async def admin_welcome(message: types.Message):
    await message.answer(
        "👋 Salom Admin! Bot mukammal **Reply (Javob berish)** rejimida ishlamoqda.\n\n"
        "**Qanday ishlaydi?**\n"
        "1. Foydalanuvchilar yozgan xabar senga keladi.\n"
        "2. O'sha xabarga **Reply (Javob berish)** qilib yozsang, javobing unga ANONIM tarzda boradi.\n"
        "3. Bir vaqtning o'zida cheksiz odam bilan parallel gaplashishingiz mumkin!\n\n"
        "🤖 _O'zingizni test qilish uchun ixtiyoriy xabar yozing, u o'zingizga tugma bilan qaytadi._"
    )

# ==================== XABARLARNI YO'NALTIRISH (REPLY BRIDGE) ====================

# ADMIN JAVOB BERGANDA (Admin biror xabarga REPLY qilganda)
@dp.message(F.from_user.id == ADMIN_ID, F.reply_to_message)
async def admin_reply_to_user(message: types.Message):
    reply_id = message.reply_to_message.message_id
    
    # Tracker xotirasidan ushbu xabar aslida qaysi userdan kelganini topamiz
    user_id = message_tracker.get(reply_id)
    
    if not user_id:
        await message.answer("❌ Kechirasiz, ushbu xabar egasini topib bo'lmadi (Balki bot qayta ishga tushgan yoki eski xabardir).")
        return
        
    try:
        # Admin javobini foydalanuvchiga yuborish (Klonlash)
        await bot.copy_message(chat_id=user_id, from_chat_id=ADMIN_ID, message_id=message.message_id)
        await message.answer("✅ Javobingiz muvaffaqiyatli yetkazildi.")
    except Exception:
        await message.answer("❌ Xabarni yuborib bo'lmadi. Foydalanuvchi botni bloklagan bo'lishi mumkin.")


# FOYDALANUVCHIDAN XABAR KELGANDA (Yoki admin o'zini test qilganda)
@dp.message()
async def forward_to_admin(message: types.Message):
    user_id = message.from_user.id
    
    # Inline tugma (ID ni nusxalash baribir kerak bo'lsa)
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="🆔 ID-ni nusxalash", callback_data=f"get_id_{user_id}")
    )
    
    # Adminga xabarni yuboramiz (Klonlab)
    sent_msg = await bot.copy_message(
        chat_id=ADMIN_ID, 
        from_chat_id=user_id, 
        message_id=message.message_id, 
        reply_markup=builder.as_markup()
    )
    
    # 💥 MUHIM: Kelgan yangi xabarning ID sini foydalanuvchi ID si bilan bog'lab trackerga saqlaymiz
    message_tracker[sent_msg.message_id] = user_id
    
    # Agar haqiqiy begona foydalanuvchi yozgan bo'lsa, unga bildirishnoma yuboramiz
    if user_id != ADMIN_ID:
        await message.answer("🤫 Xabaringiz anonim tarzda adminga yuborildi!")


# Admin inline-tugmani bosganda ID raqamini ko'rsatuvchi qism
@dp.callback_query(lambda c: c.data.startswith('get_id_'))
async def show_id_to_admin(callback_query: types.CallbackQuery):
    user_id = callback_query.data.split('_')[2]
    await callback_query.message.answer(f"👤 Foydalanuvchi ID raqami:\n`{user_id}`")
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
