import os
from dotenv import load_dotenv

# .env faylini yuklash
load_dotenv()


def build_database_url() -> str:
    """DATABASE_URL ni .env yoki alohida POSTGRES_* o'zgaruvchilaridan quradi."""
    explicit_url = os.getenv("DATABASE_URL")
    if explicit_url:
        return explicit_url

    postgres_user = os.getenv("POSTGRES_USER", "postgres")
    postgres_password = os.getenv("POSTGRES_PASSWORD", "postgres")
    postgres_host = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port = os.getenv("POSTGRES_PORT", "5432")
    postgres_db = os.getenv("POSTGRES_DB", "kairyx_db")
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

# Redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
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