import os
from dotenv import load_dotenv

# .env faylini yuklash
load_dotenv()


def build_database_url() -> str | None:
    """
    DATABASE_URL ni .env yoki alohida POSTGRES_* / PG* o'zgaruvchilaridan quradi.
    Hech qanday konfiguratsiya topilmasa, None qaytaradi.
    """
    explicit_url = os.getenv("DATABASE_URL")
    if explicit_url and explicit_url.strip():
        return explicit_url

    postgres_host = (
        os.getenv("POSTGRES_HOST")
        or os.getenv("PGHOST")
    )
    if not postgres_host:
        return None

    # Localhost is not usable in Railway-style deployments; skip it unless the user explicitly wants it.
    if postgres_host in {"localhost", "127.0.0.1", "0.0.0.0"}:
        return None

    postgres_user = os.getenv("POSTGRES_USER") or os.getenv("PGUSER") or "postgres"
    postgres_password = os.getenv("POSTGRES_PASSWORD") or os.getenv("PGPASSWORD") or "postgres"
    postgres_port = os.getenv("POSTGRES_PORT") or os.getenv("PGPORT") or "5432"
    postgres_db = os.getenv("POSTGRES_DB") or os.getenv("PGDATABASE") or "kairyx_db"
    return f"postgresql+asyncpg://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"


def parse_admin_ids(value: str | None) -> list[int]:
    """ADMIN_IDS stringini int ro'yxatga aylantiradi."""
    if not value:
        return []
    return [int(admin_id.strip()) for admin_id in value.split(",") if admin_id.strip()]


# Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Ma'lumotlar bazasi (PostgreSQL)
DATABASE_URL = build_database_url()

# Redis (Railway/hosted env uchun faqat aniq konfiguratsiya bo'lsa ishlatiladi)
REDIS_HOST = os.getenv("REDIS_HOST") or os.getenv("REDIS_URL")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Adminlar
ADMIN_IDS_STR = os.getenv("ADMIN_IDS")
ADMIN_IDS = parse_admin_ids(ADMIN_IDS_STR)

# AI
AI_API_KEY = os.getenv("AI_API_KEY")

# To'lov uchun karta raqami (XAVFSIZ EMAS - FAQAT TEST UCHUN)
# WARNING: This is NOT a secure way to handle payments.
# This is a placeholder for a real payment gateway integration.
# Do NOT use this in a production environment.
PAYMENT_CARD_NUMBER = os.getenv("PAYMENT_CARD_NUMBER", "9860 6004 3347 6527")