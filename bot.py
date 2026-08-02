import asyncio
import logging
import os
import sys
import tempfile
import time
import urllib.parse
import uuid

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramConflictError
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio.client import Redis
from sqlalchemy import inspect as sa_inspect, text

from config import BOT_TOKEN, REDIS_HOST, REDIS_PORT
from common import router as common_router, BanCheckMiddleware
from registration import router as registration_router
from menu import router as menu_router
from editing import router as editing_router
from admin import router as admin_router

import engine as engine_module
from models import Base


def _describe_column_default(column) -> str:
    """Builds a ' DEFAULT ...' SQL clause from a column's Python-side default, if any."""
    if column.default is None or not getattr(column.default, "is_scalar", False):
        return ""

    value = column.default.arg
    if isinstance(value, bool):
        return f" DEFAULT {str(value).upper()}"
    if isinstance(value, (int, float)):
        return f" DEFAULT {value}"
    if isinstance(value, str):
        return f" DEFAULT '{value.replace(chr(39), chr(39) * 2)}'"
    return ""


def _build_add_column_ddl(table_name: str, column, dialect) -> str:
    column_type = column.type.compile(dialect=dialect)
    default_clause = _describe_column_default(column)
    return f'ALTER TABLE "{table_name}" ADD COLUMN "{column.name}" {column_type}{default_clause}'


async def run_lightweight_migrations() -> None:
    """
    Adds columns declared on the models but missing from the database tables.
    This project has no migration tool (e.g. Alembic), so this keeps deployed
    databases in sync with model changes such as the premium quota/boost columns.
    """
    if engine_module.engine is None:
        return

    try:
        async with engine_module.engine.begin() as conn:
            def _inspect_columns(sync_conn):
                inspector = sa_inspect(sync_conn)
                return {
                    table_name: {col["name"] for col in inspector.get_columns(table_name)}
                    for table_name in inspector.get_table_names()
                }

            existing_columns = await conn.run_sync(_inspect_columns)

            for table in Base.metadata.sorted_tables:
                table_columns = existing_columns.get(table.name)
                if table_columns is None:
                    continue
                for column in table.columns:
                    if column.name in table_columns:
                        continue
                    ddl = _build_add_column_ddl(table.name, column, engine_module.engine.dialect)
                    logging.info(f"Applying lightweight migration: {ddl}")
                    await conn.execute(text(ddl))
    except Exception as exc:
        logging.warning(f"Lightweight migration warning: {exc}")


_FILE_LOCK_HANDLES: dict[str, str] = {}


def _acquire_file_lock(lock_path: str) -> tuple[bool, str | None, str | None]:
    """Acquire a filesystem-based lock for this process."""
    lock_dir = os.path.dirname(lock_path) or "."
    os.makedirs(lock_dir, exist_ok=True)

    token = str(uuid.uuid4())
    try:
        fd = os.open(lock_path, os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        try:
            if time.time() - os.path.getmtime(lock_path) > 300:
                os.remove(lock_path)
                fd = os.open(lock_path, os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o600)
            else:
                return False, None, None
        except FileNotFoundError:
            fd = os.open(lock_path, os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o600)
        except OSError as exc:
            logging.warning(f"Unable to acquire polling lock file: {exc}")
            return False, None, None
    except OSError as exc:
        logging.warning(f"Unable to open polling lock file: {exc}")
        return False, None, None

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(token)
            handle.flush()
    except OSError as exc:
        logging.warning(f"Unable to write polling lock file: {exc}")
        return False, None, None

    return True, token, lock_path


def _release_file_lock(token: str | None) -> None:
    """Release a filesystem lock for the provided token."""
    if not token:
        return

    lock_path = _FILE_LOCK_HANDLES.pop(token, None)
    if not lock_path:
        return

    try:
        os.remove(lock_path)
    except FileNotFoundError:
        return
    except OSError as exc:
        logging.warning(f"Polling lock cleanup warning: {exc}")


async def acquire_polling_lock(
    redis_client: Redis | None,
    lock_key: str,
    lock_path: str | None = None,
) -> tuple[bool, str | None]:
    """Return True if this instance successfully acquired the polling lock."""
    if redis_client is not None:
        token = str(uuid.uuid4())
        try:
            acquired = await redis_client.set(lock_key, token, nx=True, ex=300)
            return bool(acquired), token if acquired else None
        except Exception as exc:
            logging.warning(f"Polling lock unavailable: {exc}")

    file_lock_path = lock_path or os.getenv(
        "BOT_POLLING_LOCK_FILE",
        os.path.join(tempfile.gettempdir(), "kairyx-bot.lock"),
    )
    acquired, token, handle = await asyncio.to_thread(_acquire_file_lock, file_lock_path)
    if acquired and token:
        _FILE_LOCK_HANDLES[token] = file_lock_path
        return True, token
    return False, None


async def release_polling_lock(
    redis_client: Redis | None,
    lock_key: str,
    token: str | None,
    lock_path: str | None = None,
) -> None:
    """Release the polling lock if this instance still owns it."""
    if not token:
        return

    if redis_client is not None:
        try:
            current_token = await redis_client.get(lock_key)
            if current_token and current_token.decode() == token:
                await redis_client.delete(lock_key)
        except Exception as exc:
            logging.warning(f"Polling lock cleanup warning: {exc}")
        return

    await asyncio.to_thread(_release_file_lock, token)


async def main() -> None:
    """Botni ishga tushirish."""
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logging.error("Xatolik: Telegram bot tokeni topilmadi yoki o'rnatilmagan.")
        logging.error("Iltimos, .env fayliga o'z tokeningizni kiriting.")
        return

    redis_client: Redis | None = None
    storage = MemoryStorage()

    redis_url = os.getenv("REDIS_URL")
    redis_host = os.getenv("REDIS_HOST")
    if redis_url:
        parsed_redis = urllib.parse.urlsplit(redis_url)
        logging.info(
            f"Redis-ga ulanish manzili: {parsed_redis.hostname}:{parsed_redis.port or REDIS_PORT}"
        )
        redis_client = Redis.from_url(redis_url)
        try:
            await redis_client.ping()
            storage = RedisStorage(redis=redis_client)
            logging.info("Redis storage connected.")
        except Exception as exc:
            logging.warning(f"Redis unavailable, falling back to MemoryStorage: {exc}")
            redis_client = None
            storage = MemoryStorage()
    elif redis_host and redis_host not in {"localhost", "127.0.0.1", "0.0.0.0"}:
        logging.info(f"Redis-ga ulanish manzili: {redis_host}:{REDIS_PORT}")
        try:
            redis_client = Redis(host=redis_host, port=REDIS_PORT)
            await redis_client.ping()
            storage = RedisStorage(redis=redis_client)
            logging.info("Redis storage connected.")
        except Exception as exc:
            logging.warning(f"Redis unavailable, falling back to MemoryStorage: {exc}")
            redis_client = None
            storage = MemoryStorage()
    else:
        logging.info("Redis not configured; using MemoryStorage.")

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    dp = Dispatcher(storage=storage)

    dp.update.outer_middleware(BanCheckMiddleware())

    dp.include_router(common_router)
    dp.include_router(registration_router)
    dp.include_router(menu_router)
    dp.include_router(editing_router)
    dp.include_router(admin_router)

    try:
        async with engine_module.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as exc:
        logging.warning(f"Database setup warning: {exc}")
        try:
            engine_module.switch_to_sqlite_fallback(exc)
            async with engine_module.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logging.warning("SQLite fallback aktivlashtirildi.")
        except Exception as fallback_exc:
            logging.warning(f"SQLite fallback setup warning: {fallback_exc}")

    await run_lightweight_migrations()

    lock_key = os.getenv("BOT_POLLING_LOCK_KEY", "kairyx-bot:polling_lock")
    polling_lock_token = None

    try:
        lock_acquired, polling_lock_token = await acquire_polling_lock(redis_client, lock_key, os.getenv("BOT_POLLING_LOCK_FILE"))
        if not lock_acquired:
            logging.warning(
                "Another bot instance is already polling or the local lock is busy. "
                "This instance will exit to prevent Telegram conflicts."
            )
            return

        logging.info("Bot ishga tushmoqda...")
        try:
            await dp.start_polling(bot)
        except TelegramConflictError as exc:
            logging.error("Telegram polling conflict detected: %s", exc)
            logging.error("This usually means another bot instance is already polling. Exiting this instance cleanly.")
            return
    finally:
        if polling_lock_token:
            await release_polling_lock(redis_client, lock_key, polling_lock_token)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi.")
