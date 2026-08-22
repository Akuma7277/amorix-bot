from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from typing import Optional
from i18n import t
from config import WEBAPP_URL

def get_webapp_url() -> str:
    import time
    if not WEBAPP_URL:
        return ""
    t_val = int(time.time() // 60)
    return f"{WEBAPP_URL}&v={t_val}" if "?" in WEBAPP_URL else f"{WEBAPP_URL}?v={t_val}"

def get_main_menu_keyboard(lang: str = "uz") -> ReplyKeyboardMarkup:
    """Asosiy menyu uchun TashDate-uslubidagi ixcham ReplyKeyboardMarkup"""
    buttons = [
        [
            KeyboardButton(text=t("menu_search", lang)),
            KeyboardButton(text=t("menu_my_profile", lang))
        ],
        [
            KeyboardButton(text=t("menu_likes", lang)),
            KeyboardButton(text=t("menu_chats", lang))
        ],
        [
            KeyboardButton(text=t("menu_premium", lang)),
            KeyboardButton(text=t("menu_mini_app", lang), web_app=WebAppInfo(url=get_webapp_url()))
        ],
        [
            KeyboardButton(text=t("menu_settings", lang)),
            KeyboardButton(text=t("menu_help", lang))
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
