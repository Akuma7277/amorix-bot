import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio.client import Redis

from config import BOT_TOKEN, REDIS_HOST, REDIS_PORT
from common import router as common_router
from registration import router as registration_router
from menu import router as menu_router
from editing import router as editing_router
from admin import router as admin_router

from engine import engine
from models import Base


async def main() -> None:
    """Botni ishga tushirish."""
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logging.error("Xatolik: Telegram bot tokeni topilmadi yoki o'rnatilmagan.")
        logging.error("Iltimos, .env fayliga o'z tokeningizni kiriting.")
        return

    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        redis = Redis.from_url(redis_url)
    else:
        redis = Redis(host=REDIS_HOST, port=REDIS_PORT)
    storage = RedisStorage(redis=redis)

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    dp = Dispatcher(storage=storage)

    dp.include_router(common_router)
    dp.include_router(registration_router)
    dp.include_router(menu_router)
    dp.include_router(editing_router)
    dp.include_router(admin_router)

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as exc:
        logging.warning(f"Database setup warning: {exc}")

    logging.info("Bot ishga tushmoqda...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi.")
