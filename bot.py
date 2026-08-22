import os
import sys
import logging
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN, WEBAPP_URL, ADMIN_IDS
import common
import registration
import menu
import admin
import editing

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

async def start_bot_polling(bot: Bot, dp: Dispatcher):
    try:
        logger.info("Starting Telegram Bot Polling...")
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Telegram polling error: {e}")

async def main() -> None:
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

    # Start REST API Webapp Server first
    from webapp.api import create_webapp_app
    from aiohttp import web
    webapp_app = create_webapp_app()
    runner = web.AppRunner(webapp_app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"REST API server successfully started on port {port}")

    if BOT_TOKEN and BOT_TOKEN != "YOUR_BOT_TOKEN_HERE":
        bot = Bot(
            token=BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        dp = Dispatcher()

        # Include all functional routers in proper order
        dp.include_router(common.router)
        dp.include_router(registration.router)
        dp.include_router(menu.router)
        dp.include_router(admin.router)
        dp.include_router(editing.router)

        polling_task = asyncio.create_task(start_bot_polling(bot, dp))
        await polling_task
    else:
        logger.warning("No BOT_TOKEN found, running API server in standalone mode.")
        while True:
            await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
