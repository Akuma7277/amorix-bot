from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from config import DATABASE_URL

# Asinxron engine yaratish
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Dasturlash jarayonida SQL so'rovlarni ko'rish uchun. Production'da False qilish kerak.
)

# Asinxron sessiya yaratuvchi (session maker)
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session