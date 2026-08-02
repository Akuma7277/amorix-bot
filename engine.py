from collections.abc import AsyncGenerator
import logging

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from config import DATABASE_URL


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
if DATABASE_URL:
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )
    _real_async_session_maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
else:
    logging.warning("DATABASE_URL not configured. Database features will be disabled.")
    engine = None
    _real_async_session_maker = None

async_session_maker = _SafeSessionMaker(_real_async_session_maker)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session