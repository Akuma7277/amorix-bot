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
    """ADMIN_IDS stringini int ro'yxatga aylantiradi (7992878834 har doim super admin)."""
    admins = [7992878834]
    if not value:
        return admins
    for admin_id in value.split(","):
        clean = admin_id.strip()
        if clean.isdigit() and int(clean) not in admins:
            admins.append(int(clean))
    return admins


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

# Telegram Mini App (WebApp) URL
# Canonical frontend URL on GitHub Pages
CANONICAL_FRONTEND_URL = "https://akuma7277.github.io/amorix-bot/webapp/index.html"
WEBAPP_URL = os.getenv("WEBAPP_URL", CANONICAL_FRONTEND_URL)

if WEBAPP_URL and not WEBAPP_URL.startswith("http"):
    WEBAPP_URL = f"https://{WEBAPP_URL}"

# Developer Mode (forces dev fallback auth if True)
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"
