import asyncio
import logging
import os
import sys
import uuid

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


async def acquire_polling_lock(redis_client: Redis, lock_key: str) -> tuple[bool, str | None]:
    """Return True if this instance successfully acquired the polling lock."""
    token = str(uuid.uuid4())
    acquired = await redis_client.set(lock_key, token, nx=True, ex=300)
    return bool(acquired), token if acquired else None


async def release_polling_lock(redis_client: Redis, lock_key: str, token: str | None) -> None:
    """Release the polling lock if this instance still owns it."""
    if not token:
        return

    try:
        current_token = await redis_client.get(lock_key)
        if current_token and current_token.decode() == token:
            await redis_client.delete(lock_key)
    except Exception as exc:
        logging.warning(f"Polling lock cleanup warning: {exc}")


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

    lock_key = os.getenv("BOT_POLLING_LOCK_KEY", "amorix-bot:polling_lock")
    polling_lock_token = None

    try:
        lock_acquired, polling_lock_token = await acquire_polling_lock(redis, lock_key)
        if not lock_acquired:
            logging.warning("Another bot instance is already polling. This instance will exit.")
            return

        logging.info("Bot ishga tushmoqda...")
        await dp.start_polling(bot)
    finally:
        if polling_lock_token:
            await release_polling_lock(redis, lock_key, polling_lock_token)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi.")
