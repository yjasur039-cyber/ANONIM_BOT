import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# Loggingni sozlaymiz (Render-da xatoliklarni ko'rish uchun shart)
logging.basicConfig(level=logging.INFO)

# --- ⚙️ SOZLAMALAR ---
# Token va Admin ID ni Render platformasidagi Environment Variables (muhit o'zgaruvchilari) ichiga kiriting.
# Agar topilmasa, pastdagi qo'shtirnoq ichiga yozib qo'yishingiz ham mumkin.
BOT_TOKEN = os.getenv("BOT_TOKEN", "BU_YERGA_BOT_TOKENINI_YOZING")
ADMIN_ID = int(os.getenv("ADMIN_ID", "BU_YERGA_TELEGRAM_ID_INGIZNI_YOZING"))

# Render uchun Webhook sozlamalari
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")  # Render o'zi avtomatik beradi
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 8080))

# Bot va Dispatcher ob'ektlarini yaratamiz
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# --- 📝 HANDLERLAR (BUYRUKLAR) ---

# /start buyrug'i uchun handler
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer(
            "👋 **Assalomu alaykum, Admin!**\n\nBu sizning anonim botingiz. Foydalanuvchilardan kelgan xabarlar shu yerga tushadi. "
            "Xabar ostidagi tugmani bosib, foydalanuvchi ID-sini osongina olishingiz mumkin.",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await message.answer(
            "👋 **Anonim botga xush kelibsiz!**\n\nAdminga yubormoqchi bo'lgan xabaringizni (matn, rasm yoki fikr) yozib yuboring. "
            "Sizning shaxsingiz mutlaqo yashirin qoladi! 🥷"
        )


# Anonim xabarlarni qabul qilib adminga yo'naltirish qismi
@dp.message()
async def handle_anonymous_message(message: types.Message):
    # Agar admin o'zi yozayotgan bo'lsa, xabarni o'ziga qayta yubormaydi
    if message.from_user.id == ADMIN_ID:
        await message.answer("⚠️ Bu sizning admin panelingiz. Foydalanuvchilarga javob berish uchun ularning ID-sidan foydalaning.")
        return

    # 1. Chiroyli Inline tugma yasaymiz va ichiga foydalanuvchi ID-sini berkitamiz
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text="🆔 ID-ni nusxalash", 
            callback_data=f"get_id_{message.from_user.id}"
        )
    )

    # 2. Xabarni turi bo'yicha adminga chiroyli qilib uzatamiz
    try:
        if message.text:
            await bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🥷 **Yangi anonim xabar:**\n\n{message.text}",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=builder.as_markup()
            )
        else:
            # Agar rasm, video yoki boshqa media bo'lsa, uni adminga caption (izoh) bilan yuboradi
            await message.copy_to(
                chat_id=ADMIN_ID,
                caption=f"🥷 **Yangi anonim media xabar!**",
                reply_markup=builder.as_markup()
            )
        
        # Foydalanuvchiga tasdiq xabari
        await message.answer("Xabaringiz anonim tarzda adminga yetkazildi! 🤫")
        
    except Exception as e:
        logging.error(f"Xabar yuborishda xatolik: {e}")
        await message.answer("❌ Xabar yuborishda xatolik yuz berdi. Keyinroq qayta urinib ko'ring.")


# 3. Admin tugmani bosganda ID-ni chiroyli xabar qilib chiqaradigan qism
@dp.callback_query(lambda c: c.data.startswith('get_id_'))
async def show_user_id_to_admin(callback_query: types.CallbackQuery):
    # callback_data ichidan user_id ni ajratib olamiz
    user_id = callback_query.data.split('_')[2]
    
    # Adminga ID-ni alohida xabar qilib yuboramiz. 
    # ` ` belgilari ichidagi ID ustiga bir marta bosa, avtomatik nusxalanadi (copy bo'ladi).
    await callback_query.message.answer(
        text=f"👤 **Foydalanuvchi ID raqami:**\n`{user_id}`\n\nUshbu ID-ni nusxalab, unga javob yuborishingiz mumkin.",
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Tugma muzlab qolmasligi uchun Telegramga javob qaytaramiz
    await callback_query.answer()


# --- 🚀 BOTNI ISHGA TUSHIRISH (RENDER & LOCAL) ---

async def on_startup(bot: Bot) -> None:
    if RENDER_EXTERNAL_URL:
        await bot.set_webhook(url=f"{RENDER_EXTERNAL_URL}{WEBHOOK_PATH}")
        logging.info(f"Webhook o'rnatildi: {RENDER_EXTERNAL_URL}{WEBHOOK_PATH}")
    else:
        logging.info("Bot lokal rejimda (Polling) ishga tushmoqda...")

def main():
    if RENDER_EXTERNAL_URL:
        # Render platformasida Webhook rejimida ishga tushirish
        app = web.Application()
        webhook_requests_handler = SimpleRequestHandler(
            dispatcher=dp,
            bot=bot
        )
        webhook_requests_handler.register(app, path=WEBHOOK_PATH)
        setup_application(app, dp, bot=bot)
        
        dp.startup.register(on_startup)
        web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)
    else:
        # Kompyuterda sinash uchun oddiy Polling rejimi
        dp.startup.register(on_startup)
        dp.run_polling(bot)

if __name__ == "__main__":
    main()
