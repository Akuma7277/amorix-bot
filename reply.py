from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

MAIN_MENU_BUTTONS = {
    "uz": {
        "search": "🔍 Qidirish",
        "my_profile": "👤 Mening profilim",
        "likes": "❤️ Menga yoqqanlar",
        "chats": "💬 Suhbatlarim",
        "premium": "⭐️ Premium",
        "referrals": "🎁 Do'stlarni taklif qilish",
        "settings": "⚙️ Sozlamalar",
        "help": "❓ Yordam",
        "mini_app": "📱 Mini App",
    },
    "ru": {
        "search": "🔍 Поиск",
        "my_profile": "👤 Мой профиль",
        "likes": "❤️ Лайки",
        "chats": "💬 Мои чаты",
        "premium": "⭐️ Премиум",
        "referrals": "🎁 Пригласить друзей",
        "settings": "⚙️ Настройки",
        "help": "❓ Помощь",
        "mini_app": "📱 Mini App",
    },
    "en": {
        "search": "🔍 Search",
        "my_profile": "👤 My Profile",
        "likes": "❤️ Likes",
        "chats": "💬 My Chats",
        "premium": "⭐️ Premium",
        "referrals": "🎁 Refer Friends",
        "settings": "⚙️ Settings",
        "help": "❓ Help",
        "mini_app": "📱 Mini App",
    },
}

def get_main_menu_keyboard(language: str = "uz") -> ReplyKeyboardMarkup:
    """Asosiy menyu uchun reply keyboard yaratadi."""
    texts = MAIN_MENU_BUTTONS.get(language, MAIN_MENU_BUTTONS["uz"])
    buttons = [
        [KeyboardButton(text=texts["search"]), KeyboardButton(text=texts["my_profile"])],
        [KeyboardButton(text=texts["likes"]), KeyboardButton(text=texts["chats"])],
        [KeyboardButton(text=texts["premium"])],
        [KeyboardButton(text=texts["referrals"])],
        [KeyboardButton(text=texts["settings"]), KeyboardButton(text=texts["help"])],
        [KeyboardButton(text=texts["mini_app"])],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


CHAT_ACTION_BUTTONS = {
    "uz": {
        "security": "🛡️ Xavfsizlik",
        "block": "🚫 Bloklash",
        "report": "⚑ Shikoyat qilish",
        "end_chat": "⏹ Suhbatni yakunlash",
    },
    "ru": {
        "security": "🛡️ Безопасность",
        "block": "🚫 Заблокировать",
        "report": "⚑ Пожаловаться",
        "end_chat": "⏹ Завершить чат",
    },
    "en": {
        "security": "🛡️ Security",
        "block": "🚫 Block",
        "report": "⚑ Report",
        "end_chat": "⏹ End Chat",
    },
}


ADMIN_MENU_BUTTONS = {
    "uz": {
        "statistics": "📊 Statistika",
        "photo_moderation": "🖼️ Fotosuratlar moderatsiyasi",
        "users": "👥 Foydalanuvchilar",
        "reports": "❗️ Shikoyatlar",
        "verification_moderation": "✅ Verifikatsiya",
        "payment_moderation": "💳 To'lovlar moderatsiyasi",
        "broadcast": "📢 Broadcast",
        "tariffs_payments": "💰 Tarif/to'lovlar",
        "logs": "📝 Loglar",
        "manage_admins": "👮 Adminlarni boshqarish",
        "mandatory_channel": "📎 Majburiy kanal",
        "districts": "🏘️ Tumanlar",
    },
    "ru": {
        "statistics": "📊 Статистика",
        "photo_moderation": "🖼️ Модерация фото",
        "users": "👥 Пользователи",
        "reports": "❗️ Жалобы",
        "verification_moderation": "✅ Верификация",
        "payment_moderation": "💳 Модерация платежей",
        "broadcast": "📢 Рассылка",
        "tariffs_payments": "💰 Тарифы/платежи",
        "logs": "📝 Логи",
        "manage_admins": "👮 Управление админами",
        "mandatory_channel": "📎 Обязательный канал",
        "districts": "🏘️ Районы",
    },
    "en": {
        "statistics": "📊 Statistics",
        "photo_moderation": "🖼️ Photo Moderation",
        "users": "👥 Users",
        "reports": "❗️ Reports",
        "verification_moderation": "✅ Verification",
        "payment_moderation": "💳 Payment Moderation",
        "broadcast": "📢 Broadcast",
        "tariffs_payments": "💰 Tariffs/Payments",
        "logs": "📝 Logs",
        "manage_admins": "👮 Manage Admins",
        "mandatory_channel": "📎 Mandatory Channel",
        "districts": "🏘️ Districts",
    },
}


def get_admin_main_menu_keyboard(language: str = "uz") -> ReplyKeyboardMarkup:
    """Admin paneli uchun reply keyboard yaratadi."""
    texts = ADMIN_MENU_BUTTONS.get(language, ADMIN_MENU_BUTTONS["uz"])
    buttons = [
        [KeyboardButton(text=texts["statistics"]), KeyboardButton(text=texts["photo_moderation"])],
        [KeyboardButton(text=texts["users"]), KeyboardButton(text=texts["reports"])],
        [KeyboardButton(text=texts["verification_moderation"]), KeyboardButton(text=texts["payment_moderation"])],
        [KeyboardButton(text=texts["broadcast"]), KeyboardButton(text=texts["tariffs_payments"])],
        [KeyboardButton(text=texts["logs"]), KeyboardButton(text=texts["manage_admins"])],
        [KeyboardButton(text=texts["mandatory_channel"]), KeyboardButton(text=texts["districts"])],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def get_chat_keyboard(language: str = "uz") -> ReplyKeyboardMarkup:
    """Suhbat ichidagi amallar uchun reply keyboard yaratadi."""
    texts = CHAT_ACTION_BUTTONS.get(language, CHAT_ACTION_BUTTONS["uz"])
    buttons = [
        [KeyboardButton(text=texts["security"])],
        [KeyboardButton(text=texts["block"]), KeyboardButton(text=texts["report"])],
        [KeyboardButton(text=texts["end_chat"])],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)