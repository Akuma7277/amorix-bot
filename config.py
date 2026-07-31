import os
from dotenv import load_dotenv

# .env faylini yuklash
load_dotenv()

# Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Ma'lumotlar bazasi (PostgreSQL)
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB")

DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Adminlar
ADMIN_IDS_STR = os.getenv("ADMIN_IDS")
ADMIN_IDS = [int(admin_id) for admin_id in ADMIN_IDS_STR.split(",")] if ADMIN_IDS_STR else []

# AI
AI_API_KEY = os.getenv("AI_API_KEY")

# To'lov uchun karta raqami (XAVFSIZ EMAS - FAQAT TEST UCHUN)
# WARNING: This is NOT a secure way to handle payments.
# This is a placeholder for a real payment gateway integration.
# Do NOT use this in a production environment.
PAYMENT_CARD_NUMBER = os.getenv("PAYMENT_CARD_NUMBER", "9860 6004 3347 6527")