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

    # Include all functional routers in proper order
    dp.include_router(common.router)
    dp.include_router(registration.router)
    dp.include_router(menu.router)
    dp.include_router(admin.router)
    dp.include_router(editing.router)

    # Start REST API Webapp Server in background
    from webapp.api import create_webapp_app
    from aiohttp import web
    webapp_app = create_webapp_app()
    runner = web.AppRunner(webapp_app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"REST API server successfully started on port {port}")

    logger.info("Bot polling started with selection-based registration and instant access...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
