import os
import sys
import logging
import asyncio
from aiogram import Bot, Dispatcher, Router
from aiogram.types import (
    Message,
    WebAppInfo,
    MenuButtonWebApp,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove
)
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN, WEBAPP_URL, ADMIN_IDS

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

router = Router()

def get_webapp_url() -> str:
    import time
    if not WEBAPP_URL:
        return ""
    t = int(time.time() // 60)
    return f"{WEBAPP_URL}&v={t}" if "?" in WEBAPP_URL else f"{WEBAPP_URL}?v={t}"

@router.message(Command("start"))
async def cmd_start(message: Message, bot: Bot):
    try:
        await bot.set_chat_menu_button(
            chat_id=message.chat.id,
            menu_button=MenuButtonWebApp(
                text="Kairyx App",
                web_app=WebAppInfo(url=get_webapp_url())
            )
        )
    except Exception as e:
        logger.warning(f"Error setting chat menu button: {e}")

    welcome_text = (
        "👋 Assalomu alaykum!\n\n"
        "💖 <b>Kairyx</b> — premium tanishuv ilovasiga xush kelibsiz.\n\n"
        "Barcha xizmatlar (tanishuv, profil, juftliklar, chat va admin boshqaruvi) to'liq Mini App ichida jamlangan.\n\n"
        "Ilovani ishga tushirish uchun quyidagi tugmani bosing: 👇"
    )

    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 Kairyx Mini App ni ochish", web_app=WebAppInfo(url=get_webapp_url()))]
    ])

    await message.answer(
        welcome_text,
        reply_markup=inline_kb,
        parse_mode=ParseMode.HTML
    )

@router.message()
async def all_other_messages(message: Message, bot: Bot):
    try:
        await bot.set_chat_menu_button(
            chat_id=message.chat.id,
            menu_button=MenuButtonWebApp(
                text="Kairyx App",
                web_app=WebAppInfo(url=get_webapp_url())
            )
        )
    except Exception:
        pass

    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 Mini App ni ochish", web_app=WebAppInfo(url=get_webapp_url()))]
    ])
    await message.answer(
        "Kairyx faqat Mini App orqali ishlaydi. Ilovani ochish uchun tugmani bosing:",
        reply_markup=inline_kb,
        parse_mode=ParseMode.HTML
    )

async def main() -> None:
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("Xatolik: Telegram bot tokeni topilmadi.")
        return

    from models import Base
    import engine as engine_module
    try:
        async with engine_module.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schema initialized.")
    except Exception as exc:
        logger.warning(f"Database setup warning: {exc}")
        try:
            engine_module.switch_to_sqlite_fallback(exc)
            async with engine_module.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.warning("SQLite fallback activated.")
        except Exception as fallback_exc:
            logger.warning(f"SQLite fallback setup warning: {fallback_exc}")

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    dp.include_router(router)

    from webapp.api import create_webapp_app
    from aiohttp import web
    webapp_app = create_webapp_app()
    runner = web.AppRunner(webapp_app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"REST API server successfully started on port {port}")

    logger.info("Bot polling started...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
