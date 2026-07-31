import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio.client import Redis

from config import BOT_TOKEN, REDIS_HOST, REDIS_PORT
import common
import registration
import menu
import editing
import admin

from engine import engine
from models import Base


async def main() -> None:
    """Botni ishga tushirish."""
    # Token mavjudligini tekshirish
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logging.error("Xatolik: Telegram bot tokeni topilmadi yoki o'rnatilmagan.")
        logging.error("Iltimos, .env fayliga o'z tokeningizni kiriting.")
        return

    # FSM uchun Redis storage'ni ishga tushirish
    redis = Redis(host=REDIS_HOST, port=REDIS_PORT)
    storage = RedisStorage(redis=redis)

    # Bot va Dispatcher obyektlarini yaratish
    bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
    dp = Dispatcher(storage=storage)

    # Routerlarni ulash
    dp.include_router(common.router)
    dp.include_router(registration.router)
    dp.include_router(menu.router)
    dp.include_router(editing.router)
    dp.include_router(admin.router)

    # Ma'lumotlar bazasi jadvallarini yaratish
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Botni ishga tushirish
    logging.info("Bot ishga tushmoqda...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi.")
