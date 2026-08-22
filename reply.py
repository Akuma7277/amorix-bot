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

MAIN_MENU_BUTTONS = {
    "uz": {
        "search": "🔍 Qidirish",
        "my_profile": "👤 Mening profilim",
        "likes": "❤️ Menga yoqqanlar",
        "chats": "💬 Suhbatlarim",
        "premium": "⭐ Premium / VIP",
        "referrals": "🎁 Referrals",
        "referrals": "🎁 Taklif qilish",
        "mini_app": "📱 Mini App ni ochish",
        "settings": "⚙️ Sozlamalar",
        "help": "ℹ️ Qoidalar va Yordam",
    },
    "ru": {
        "search": "🔍 Поиск",
        "my_profile": "👤 Мой профиль",
        "likes": "❤️ Кому я нравлюсь",
        "chats": "💬 Мои диалоги",
        "premium": "⭐ Премиум / VIP",
        "referrals": "🎁 Рефералы",
        "mini_app": "📱 Открыть Mini App",
        "settings": "⚙️ Настройки",
        "help": "ℹ️ Помощь и Правила",
    },
    "en": {
        "search": "🔍 Search",
        "my_profile": "👤 My Profile",
        "likes": "❤️ Who Liked Me",
        "chats": "💬 My Chats",
        "premium": "⭐ Premium / VIP",
        "referrals": "🎁 Referrals",
        "referrals": "🎁 Taklif qilish",
        "mini_app": "📱 Open Mini App",
        "settings": "⚙️ Settings",
        "help": "ℹ️ Rules & Help",
    },
}

CHAT_ACTION_BUTTONS = {
    "uz": {
        "security": "🛡️ Xavfsizlik",
        "block": "🚫 Bloklash",
        "report": "🚩 Shikoyat qilish",
        "end_chat": "⏹ Suhbatni yakunlash",
    },
    "ru": {
        "security": "🛡️ Безопасность",
        "block": "🚫 Заблокировать",
        "report": "🚩 Пожаловаться",
        "end_chat": "⏹ Завершить чат",
    },
    "en": {
        "security": "🛡️ Security",
        "block": "🚫 Block",
        "report": "🚩 Report",
        "end_chat": "⏹ End Chat",
    },
}

ADMIN_MENU_BUTTONS = {
    "uz": {
        "statistics": "📊 Statistika",
        "photo_moderation": "🖼 Fotosuratlar moderatsiyasi",
        "users": "👥 Foydalanuvchilar",
        "reports": "❗️ Shikoyatlar",
        "verification_moderation": "✅ Verifikatsiya",
        "payment_moderation": "💳 To'lovlar moderatsiyasi",
        "broadcast": "📢 Broadcast",
        "tariffs_payments": "💰 Tarif/to'lovlar",
        "logs": "📝 Loglar",
        "manage_admins": "👮 Adminlarni boshqarish",
        "mandatory_channel": "📎 Majburiy kanal",
        "districts": "🏙 Tumanlar",
    },
    "ru": {
        "statistics": "📊 Статистика",
        "photo_moderation": "🖼 Модерация фото",
        "users": "👥 Пользователи",
        "reports": "❗️ Жалобы",
        "verification_moderation": "✅ Верификация",
        "payment_moderation": "💳 Модерация платежей",
        "broadcast": "📢 Рассылка",
        "tariffs_payments": "💰 Тарифы/платежи",
        "logs": "📝 Логи",
        "manage_admins": "👮 Управление админами",
        "mandatory_channel": "📎 Обязательный канал",
        "districts": "🏙 Районы",
    },
    "en": {
        "statistics": "📊 Statistics",
        "photo_moderation": "🖼 Photo Moderation",
        "users": "👥 Users",
        "reports": "❗️ Reports",
        "verification_moderation": "✅ Verification",
        "payment_moderation": "💳 Payment Moderation",
        "broadcast": "📢 Broadcast",
        "tariffs_payments": "💰 Tariffs/Payments",
        "logs": "📝 Logs",
        "manage_admins": "👮 Manage Admins",
        "mandatory_channel": "📎 Mandatory Channel",
        "districts": "🏙 Districts",
    },
}

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

def get_chat_keyboard(lang: str = "uz") -> ReplyKeyboardMarkup:
    """Suhbat ichidagi amallar uchun reply keyboard"""
    texts = CHAT_ACTION_BUTTONS.get(lang, CHAT_ACTION_BUTTONS["uz"])
    buttons = [
        [KeyboardButton(text=texts["security"])],
        [KeyboardButton(text=texts["block"]), KeyboardButton(text=texts["report"])],
        [KeyboardButton(text=texts["end_chat"])],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_admin_main_menu_keyboard(lang: str = "uz") -> ReplyKeyboardMarkup:
    """Admin paneli uchun reply keyboard"""
    texts = ADMIN_MENU_BUTTONS.get(lang, ADMIN_MENU_BUTTONS["uz"])
    buttons = [
        [KeyboardButton(text=texts["statistics"]), KeyboardButton(text=texts["verification_moderation"])],
        [KeyboardButton(text=texts["payment_moderation"]), KeyboardButton(text=texts["reports"])],
        [KeyboardButton(text=texts["users"]), KeyboardButton(text=texts["broadcast"])],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
