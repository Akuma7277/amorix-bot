from collections.abc import AsyncGenerator
from pathlib import Path
import logging
import socket
import tempfile

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from config import DATABASE_URL


_SQLITE_FALLBACK_PATH = Path(tempfile.gettempdir()) / "amorix_fallback.db"


def _build_sqlite_fallback_url() -> str:
    return f"sqlite+aiosqlite:///{_SQLITE_FALLBACK_PATH.resolve().as_posix()}"


def _database_host_is_resolvable(database_url: str) -> bool:
    try:
        url = make_url(database_url)
    except Exception:
        return False

    if url.drivername.startswith("sqlite"):
        return True

    if not url.host:
        return False

    try:
        socket.getaddrinfo(url.host, url.port or 5432)
        return True
    except OSError:
        return False


class _EmptyResult:
    def __init__(self, value=None):
        self._value = value

    def scalar_one_or_none(self):
        return self._value

    def scalars(self):
        return _EmptyScalars(self._value)

    @property
    def rowcount(self):
        return 0


class _EmptyScalars:
    def __init__(self, value=None):
        self._value = value

    def all(self):
        return [] if self._value is None else [self._value]

    def first(self):
        return self._value

    def one(self):
        return self._value


class _FallbackSession:
    def __init__(self, real_session: AsyncSession | None = None):
        self._real_session = real_session
        self._available = False

    async def __aenter__(self):
        if self._real_session is None:
            return self

        try:
            await self._real_session.__aenter__()
            self._available = True
            return self
        except Exception as exc:
            logging.warning("Database unavailable, using fallback session: %s", exc)
            self._available = False
            return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._real_session is not None and self._available:
            return await self._real_session.__aexit__(exc_type, exc, tb)
        return False

    def add(self, instance):
        if self._available and self._real_session is not None:
            return self._real_session.add(instance)
        return None

    async def flush(self):
        if self._available and self._real_session is not None:
            return await self._real_session.flush()
        return None

    async def commit(self):
        if self._available and self._real_session is not None:
            return await self._real_session.commit()
        return None

    async def rollback(self):
        if self._available and self._real_session is not None:
            return await self._real_session.rollback()
        return None

    async def refresh(self, instance):
        if self._available and self._real_session is not None:
            return await self._real_session.refresh(instance)
        return None

    async def execute(self, statement):
        if self._available and self._real_session is not None:
            return await self._real_session.execute(statement)
        return _EmptyResult()

    async def scalar(self, statement):
        if self._available and self._real_session is not None:
            return await self._real_session.scalar(statement)
        return None

    def scalars(self):
        if self._available and self._real_session is not None:
            return self._real_session.scalars()
        return _EmptyScalars()

    async def get(self, entity_type, ident, options=None):
        if self._available and self._real_session is not None:
            return await self._real_session.get(entity_type, ident, options=options)
        return None


class _SafeSessionMaker:
    def __init__(self, maker):
        self._maker = maker

    def set_maker(self, maker):
        self._maker = maker

    def __call__(self):
        if self._maker is None:
            logging.warning("Database unavailable, using fallback session factory.")
            return _FallbackSession()
        try:
            return _FallbackSession(self._maker())
        except Exception as exc:
            logging.warning("Database unavailable, using fallback session factory: %s", exc)
            return _FallbackSession()


# Asinxron engine va sessiya yaratuvchi (session maker)
if DATABASE_URL and _database_host_is_resolvable(DATABASE_URL):
    try:
        # Parol/login chiqarmasdan qaysi hostga ulanilayotganini logga yozamiz (DNS/timeout xatolarini tekshirish uchun).
        _db_url = make_url(DATABASE_URL)
        logging.info(
            f"Ma'lumotlar bazasiga ulanish manzili: {_db_url.host}:{_db_url.port}/{_db_url.database}"
        )
    except Exception:
        logging.warning("DATABASE_URL formatini aniqlab bo'lmadi.")

    _db_url = make_url(DATABASE_URL)
    if not _db_url.drivername.endswith("asyncpg"):
        _db_url = _db_url._replace(drivername="postgresql+asyncpg")

    engine = create_async_engine(
        _db_url,
        echo=False,
        pool_pre_ping=True,
    )
    _real_async_session_maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
else:
    if DATABASE_URL:
        logging.info("DATABASE_URL hosti yechilmayapti; SQLite fallback ishlatiladi.")
    else:
        logging.info("DATABASE_URL not configured. SQLite fallback ishlatiladi.")

    engine = create_async_engine(
        _build_sqlite_fallback_url(),
        echo=False,
        pool_pre_ping=True,
    )
    _real_async_session_maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

async_session_maker = _SafeSessionMaker(_real_async_session_maker)


def switch_to_sqlite_fallback(reason: Exception | str | None = None) -> None:
    global engine, _real_async_session_maker

    if reason:
        logging.warning("SQLite fallback yoqildi: %s", reason)

    engine = create_async_engine(
        _build_sqlite_fallback_url(),
        echo=False,
        pool_pre_ping=True,
    )
    _real_async_session_maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async_session_maker.set_maker(_real_async_session_maker)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session