import os
from dotenv import load_dotenv

load_dotenv()

# BotFather'dan olingan token (.env faylida saqlanadi)
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Admin bo'la oladigan Telegram ID'lar ro'yxati (vergul bilan ajratilgan)
ADMIN_IDS = [
    int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()
]

# Ma'lumotlar bazasi fayli
DB_PATH = os.getenv("DB_PATH", "bot_database.db")

# Botning ko'rinadigan nomi (xabarlarda ishlatiladi)
BOT_NAME = "AMORIX"

# Ro'yxatdan o'tish qoidalari
MIN_AGE = 18          # Kichik yoshdagilarni himoya qilish uchun minimal yosh
MAX_AGE = 70
MIN_HEIGHT = 120       # sm
MAX_HEIGHT = 230
MIN_WEIGHT = 30        # kg
MAX_WEIGHT = 200
MIN_PHOTOS = 2         # kamida shuncha rasm
MAX_PHOTOS = 5         # ko'pi bilan shuncha rasm
MIN_BIO_LEN = 10
MAX_BIO_LEN = 500
