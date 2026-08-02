from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from models import UserStatus, ReportCategory, VerificationStatus, PremiumPlan, ActionType


UZBEK_REGIONS = {
    "Andijon": ["Andijon", "Asaka", "Baliqchi", "Bo'z", "Izboskan", "Jalaquduq", "Marhamat", "Oltinko'l", "Paxtaobod", "Shahrixon", "Xonobod", "Qo'rg'ontepa"],
    "Buxoro": ["Buxoro", "G'ijduvon", "Jondor", "Kogon", "Qorako'l", "Qorovulbozor", "Peshku", "Romitan", "Shofirkon", "Vobkent", "Olot"],
    "Farg'ona": ["Farg'ona", "Beshariq", "Bog'dod", "Dang'ara", "Furqat", "Qo'shtepa", "Rishton", "So'x", "Toshloq", "Uchko'prik", "Yozyovon", "Quva"],
    "Jizzax": ["Jizzax", "Arnasoy", "Baxmal", "G'allakor", "Mirzacho'l", "Paxtakor", "Yangiobod", "Zomin", "Forish", "Do'stlik"],
    "Namangan": ["Namangan", "Chortoq", "Chust", "Kosonsoy", "Mingbuloq", "Naryn", "Pop", "Turakurgan", "Uchqo'rg'on", "Yangikurgan"],
    "Navoiy": ["Navoiy", "Karmana", "Konimex", "Qiziltepa", "Tomdi", "Uchkuduq", "Xatirchi", "Zarafshon", "Navbahor"],
    "Qashqadaryo": ["Qarshi", "Chiroqchi", "Dehqonobod", "G'uzor", "Kasbi", "Kitob", "Koson", "Mirishkor", "Muborak", "Nishon", "Shahrisabz", "Yakkabog'", "Kamashi"],
    "Qoraqalpog'iston": ["Nukus", "Amudaryo", "Beruniy", "Bo'zatov", "Chimboy", "Ellikqal'a", "Kegeyli", "Mo'ynoq", "Qonliko'l", "Qo'ng'irot", "Shumanay", "Taxtako'pir", "To'rtko'l", "Xo'jayli"],
    "Samarqand": ["Samarqand", "Bulung'ur", "Ishtixon", "Jomboy", "Kattaqo'rg'on", "Koshrabot", "Narpay", "Nurobod", "Oqdaryo", "Paxtachi", "Payariq", "Toyloq", "Urgut", "Chetsy"],
    "Sirdaryo": ["Guliston", "Boyovut", "Hazorasp", "Mirzaobod", "Sayxun", "Sardoba", "Shirin", "Yangiyer", "Yovon", "Baxt"],
    "Surxondaryo": ["Termiz", "Angor", "Bandixon", "Boysun", "Denov", "Jarqo'rg'on", "Muzrabot", "Qiziriq", "Sariosiyo", "Sherobod", "Sho'rchi", "Uzun", "Oltinsoy"],
    "Toshkent viloyati": ["Bekobod", "Bo'stonliq", "Chinoz", "Qibray", "Ohangaron", "Oqqo'rg'on", "Parkent", "Piskent", "Toshkent", "Yangiyo'l", "Yuqorichirchiq", "Zangiota", "Boka"],
    "Toshkent shahri": ["Yunusobod", "Mirobod", "Chilonzor", "Mirzo Ulug'bek", "Olmazor", "Shayxontohur", "Yakkasaroy", "Bektemir", "Yashnobod", "Sergeli", "Maksim Gorkiy", "Yangihayot", "Beshyog'och"],
    "Xorazm": ["Urganch", "Bog'ot", "Gurlan", "Hazorasp", "Khiva", "Qoshkopir", "Shovot", "Yangibozor", "Yangiariq", "Xonqa"],
}

UZBEK_CITIES = {
    "Andijon": ["Andijon", "Asaka", "Shahrixon", "Xonobod"],
    "Buxoro": ["Buxoro", "Kogon", "Qorovulbozor", "Olot"],
    "Farg'ona": ["Farg'ona", "Qo'shtepa", "Quva", "Rishton"],
    "Jizzax": ["Jizzax", "Zomin", "Forish", "Yangiobod"],
    "Namangan": ["Namangan", "Chortoq", "Chust", "Kosonsoy"],
    "Navoiy": ["Navoiy", "Zarafshon", "Karmana", "Qiziltepa"],
    "Qashqadaryo": ["Qarshi", "Shahrisabz", "Kitob", "Koson"],
    "Qoraqalpog'iston": ["Nukus", "Xo'jayli", "Qo'ng'irot", "To'rtko'l"],
    "Samarqand": ["Samarqand", "Urgut", "Kattaqo'rg'on", "Bulung'ur"],
    "Sirdaryo": ["Guliston", "Yangiyer", "Shirin", "Boyovut"],
    "Surxondaryo": ["Termiz", "Sherobod", "Denov", "Boysun"],
    "Toshkent viloyati": ["Toshkent", "Bekobod", "Yangiyo'l", "Parkent"],
    "Toshkent shahri": ["Toshkent", "Yunusobod", "Olmazor", "Chilonzor"],
    "Xorazm": ["Urganch", "Khiva", "Xonqa", "Shovot"],
}


def _slugify(value: str) -> str:
    return value.lower().replace("'", "").replace(" ", "_")


def resolve_region_name(value: str) -> str:
    if not value:
        return ""

    normalized = value.strip().replace("_", " ").replace("-", " ")
    region_lookup = {region_name.casefold(): region_name for region_name in UZBEK_REGIONS.keys()}
    return region_lookup.get(normalized.casefold(), value.strip())


def is_tashkent_city_region(region_name: str) -> bool:
    return resolve_region_name(region_name).casefold() == "toshkent shahri"


def get_language_keyboard():
    buttons = [
        [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz")],
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


ACCEPT_BUTTON_TEXTS = {
    "uz": "✅ Roziman",
    "ru": "✅ Согласен",
    "en": "✅ I agree",
}


def get_accept_terms_keyboard(language: str = "uz"):
    button_text = ACCEPT_BUTTON_TEXTS.get(language, ACCEPT_BUTTON_TEXTS["uz"])
    buttons = [[InlineKeyboardButton(text=button_text, callback_data="accept_terms")]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


GENDER_BUTTON_TEXTS = {
    "uz": {"male": "👨 Erkak", "female": "👩 Ayol"},
    "ru": {"male": "👨 Мужчина", "female": "👩 Женщина"},
    "en": {"male": "👨 Male", "female": "👩 Female"},
}


def get_gender_keyboard(language: str = "uz"):
    texts = GENDER_BUTTON_TEXTS.get(language, GENDER_BUTTON_TEXTS["uz"])
    buttons = [
        [
            InlineKeyboardButton(text=texts["male"], callback_data="gender_male"),
            InlineKeyboardButton(text=texts["female"], callback_data="gender_female"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


LOOKING_FOR_BUTTON_TEXTS = {
    "uz": {"male": "👨 Erkakni", "female": "👩 Ayolni", "any": "🚻 Farqi yo'q"},
    "ru": {"male": "👨 Мужчину", "female": "👩 Женщину", "any": "🚻 Неважно"},
    "en": {"male": "👨 A man", "female": "👩 A woman", "any": "🚻 Anyone"},
}


def get_looking_for_keyboard(language: str = "uz"):
    texts = LOOKING_FOR_BUTTON_TEXTS.get(language, LOOKING_FOR_BUTTON_TEXTS["uz"])
    buttons = [
        [
            InlineKeyboardButton(text=texts["male"], callback_data="looking_for_male"),
            InlineKeyboardButton(text=texts["female"], callback_data="looking_for_female"),
        ],
        [InlineKeyboardButton(text=texts["any"], callback_data="looking_for_any")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_region_keyboard(language: str = "uz"):
    buttons = []
    for region_name in UZBEK_REGIONS.keys():
        buttons.append([InlineKeyboardButton(text=region_name, callback_data=f"region_{_slugify(region_name)}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_city_keyboard(region_name: str, language: str = "uz"):
    cities = UZBEK_CITIES.get(region_name, [])
    buttons = []
    for city_name in cities:
        buttons.append([InlineKeyboardButton(text=city_name, callback_data=f"city_{_slugify(city_name)}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_district_keyboard(region_name: str, language: str = "uz"):
    districts = UZBEK_REGIONS.get(region_name, [])
    buttons = []
    for district_name in districts:
        buttons.append([InlineKeyboardButton(text=district_name, callback_data=f"district_{_slugify(district_name)}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_age_keyboard(language: str = "uz"):
    buttons = []
    ages = list(range(18, 61))
    for index in range(0, len(ages), 4):
        row = []
        for age in ages[index:index + 4]:
            row.append(InlineKeyboardButton(text=str(age), callback_data=f"age_{age}"))
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="✅ Tanlash", callback_data="age_done")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


ALL_INTERESTS = {
    "sport": {"uz": "Sport", "ru": "Спорт", "en": "Sport"},
    "music": {"uz": "Musiqa", "ru": "Музыка", "en": "Music"},
    "travel": {"uz": "Sayohat", "ru": "Путешествия", "en": "Travel"},
    "books": {"uz": "Kitoblar", "ru": "Книги", "en": "Books"},
    "movies": {"uz": "Kinolar", "ru": "Фильмы", "en": "Movies"},
    "cooking": {"uz": "Pazandachilik", "ru": "Кулинария", "en": "Cooking"},
    "gaming": {"uz": "O'yinlar", "ru": "Игры", "en": "Gaming"},
    "art": {"uz": "San'at", "ru": "Искусство", "en": "Art"},
    "nature": {"uz": "Tabiat", "ru": "Природа", "en": "Nature"},
    "technology": {"uz": "Texnologiya", "ru": "Технологии", "en": "Technology"},
}

DONE_BUTTON_TEXTS = {
    "uz": "✅ Tayyor",
    "ru": "✅ Готово",
    "en": "✅ Done",
}


def get_interests_keyboard(language: str = "uz", selected_interests: list = None):
    if selected_interests is None:
        selected_interests = []

    buttons = []
    row = []
    for interest_key, translations in ALL_INTERESTS.items():
        text = translations.get(language, translations["uz"])
        if interest_key in selected_interests:
            text = f"✅ {text}"
        row.append(InlineKeyboardButton(text=text, callback_data=f"interest_{interest_key}"))
        if len(row) == 2:  # Har qatorda 2 ta tugma
            buttons.append(row)
            row = []
    if row:  # Oxirgi qatorni qo'shish
        buttons.append(row)

    buttons.append([InlineKeyboardButton(text=DONE_BUTTON_TEXTS.get(language, DONE_BUTTON_TEXTS["uz"]), callback_data="interests_done")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


PHOTO_DONE_BUTTON_TEXTS = {
    "uz": "✅ Rasmlar tayyor",
    "ru": "✅ Фотографии готовы",
    "en": "✅ Photos done",
}


def get_photo_upload_done_keyboard(language: str = "uz"):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=PHOTO_DONE_BUTTON_TEXTS.get(language, PHOTO_DONE_BUTTON_TEXTS["uz"]), callback_data="photos_done")]])


REVIEW_BUTTON_TEXTS = {
    "uz": {"confirm": "✅ Tasdiqlash", "edit": "✏️ Tahrirlash"},
    "ru": {"confirm": "✅ Подтвердить", "edit": "✏️ Редактировать"},
    "en": {"confirm": "✅ Confirm", "edit": "✏️ Edit"},
}


def get_review_keyboard(language: str = "uz"):
    texts = REVIEW_BUTTON_TEXTS.get(language, REVIEW_BUTTON_TEXTS["uz"])
    buttons = [
        [
            InlineKeyboardButton(text=texts["confirm"], callback_data="confirm_profile"),
            InlineKeyboardButton(text=texts["edit"], callback_data="edit_profile"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


SEARCH_BUTTON_TEXTS = {
    "uz": {"like": "❤️ Yoqdi", "super_like": "✨ Super like", "skip": "➡️ O'tkazib yuborish", "report": "❗️ Shikoyat", "block": "🚫 Bloklash"},
    "ru": {"like": "❤️ Нравится", "super_like": "✨ Супер-лайк", "skip": "➡️ Пропустить", "report": "❗️ Жалоба", "block": "🚫 Заблокировать"},
    "en": {"like": "❤️ Like", "super_like": "✨ Super like", "skip": "➡️ Skip", "report": "❗️ Report", "block": "🚫 Block"},
}


def get_search_keyboard(language: str = "uz", target_user_id: int = 0):
    texts = SEARCH_BUTTON_TEXTS.get(language, SEARCH_BUTTON_TEXTS["uz"])
    buttons = [
        [
            InlineKeyboardButton(text=texts["like"], callback_data=f"like_{target_user_id}"),
            InlineKeyboardButton(text=texts["super_like"], callback_data=f"super_like_{target_user_id}"),
        ],
        [
            InlineKeyboardButton(text=texts["skip"], callback_data="skip_profile"),
            InlineKeyboardButton(text=texts["block"], callback_data=f"block_{target_user_id}"),
        ],
        [InlineKeyboardButton(text=texts["report"], callback_data=f"report_{target_user_id}")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


LIKES_BUTTON_TEXTS = {
    "uz": {"like_back": "❤️ Javoban yoqdi", "skip": "➡️ O'tkazib yuborish", "report": "❗️ Shikoyat"},
    "ru": {"like_back": "❤️ Нравится в ответ", "skip": "➡️ Пропустить", "report": "❗️ Жалоба"},
    "en": {"like_back": "❤️ Like back", "skip": "➡️ Skip", "report": "❗️ Report"},
}


def get_likes_keyboard(language: str = "uz", target_user_id: int = 0):
    texts = LIKES_BUTTON_TEXTS.get(language, LIKES_BUTTON_TEXTS["uz"])
    buttons = [
        [
            InlineKeyboardButton(text=texts["like_back"], callback_data=f"like_back_{target_user_id}"),
            InlineKeyboardButton(text=texts["skip"], callback_data="skip_liked_profile"),
        ],
        [InlineKeyboardButton(text=texts["report"], callback_data=f"report_{target_user_id}")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


CHAT_BUTTON_TEXTS = {
    "uz": "💬 Suhbatni boshlash",
    "ru": "💬 Начать чат",
    "en": "💬 Start Chat",
}


def get_match_keyboard(language: str = "uz", match_id: int = 0):
    text = CHAT_BUTTON_TEXTS.get(language, CHAT_BUTTON_TEXTS["uz"])
    buttons = [
        [InlineKeyboardButton(text=text, callback_data=f"start_chat_{match_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


ADMIN_DASHBOARD_BUTTON_TEXTS = {
    "uz": {
        "stats": "📊 Statistika",
        "users": "👥 Foydalanuvchilar",
        "payments": "💳 To'lovlar",
        "broadcast": "📢 Broadcast",
    },
    "ru": {
        "stats": "📊 Статистика",
        "users": "👥 Пользователи",
        "payments": "💳 Платежи",
        "broadcast": "📢 Рассылка",
    },
    "en": {
        "stats": "📊 Statistics",
        "users": "👥 Users",
        "payments": "💳 Payments",
        "broadcast": "📢 Broadcast",
    },
}


def get_admin_dashboard_keyboard(language: str = "uz"):
    texts = ADMIN_DASHBOARD_BUTTON_TEXTS.get(language, ADMIN_DASHBOARD_BUTTON_TEXTS["uz"])
    buttons = [
        [
            InlineKeyboardButton(text=texts["stats"], callback_data="admin_stats"),
            InlineKeyboardButton(text=texts["users"], callback_data="admin_users"),
        ],
        [
            InlineKeyboardButton(text=texts["payments"], callback_data="admin_payments"),
            InlineKeyboardButton(text=texts["broadcast"], callback_data="admin_broadcast"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_chats_keyboard(language: str = "uz", chats: list[tuple[int, str, VerificationStatus]] = None):
    """
    Creates an inline keyboard with a list of active chats.
    """
    if chats is None:
        chats = []
    
    buttons = []
    for match_id, partner_name, verification_status in chats:
        checkmark = " ✅" if verification_status == VerificationStatus.verified else ""
        buttons.append([InlineKeyboardButton(text=f"💬 {partner_name}{checkmark}", callback_data=f"open_chat_{match_id}")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


EDIT_PROFILE_BUTTON_TEXTS = {
    "uz": {
        "name": "Ism",
        "bio": "Bio",
        "city": "Shahar",
        "interests": "Qiziqishlar",
        "photos": "Rasmlar",
        "back": "⬅️ Orqaga",
    },
    "ru": {
        "name": "Имя",
        "bio": "О себе",
        "city": "Город",
        "interests": "Интересы",
        "photos": "Фотографии",
        "back": "⬅️ Назад",
    },
    "en": {
        "name": "Name",
        "bio": "Bio",
        "city": "City",
        "interests": "Interests",
        "photos": "Photos",
        "back": "⬅️ Back",
    },
}


def get_edit_profile_keyboard(language: str = "uz"):
    texts = EDIT_PROFILE_BUTTON_TEXTS.get(language, EDIT_PROFILE_BUTTON_TEXTS["uz"])
    buttons = [
        [InlineKeyboardButton(text=texts["name"], callback_data="edit_field_name")],
        [InlineKeyboardButton(text=texts["bio"], callback_data="edit_field_bio")],
        [InlineKeyboardButton(text=texts["city"], callback_data="edit_field_city")],
        [InlineKeyboardButton(text=texts["interests"], callback_data="edit_field_interests")],
        [InlineKeyboardButton(text=texts["photos"], callback_data="edit_field_photos")],
        [InlineKeyboardButton(text=texts["back"], callback_data="back_to_profile")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


PROFILE_VIEW_BUTTON_TEXTS = {
    "uz": {"edit": "✏️ Tahrirlash"},
    "ru": {"edit": "✏️ Редактировать"},
    "en": {"edit": "✏️ Edit"},
}


def get_profile_view_keyboard(language: str = "uz"):
    texts = PROFILE_VIEW_BUTTON_TEXTS.get(language, PROFILE_VIEW_BUTTON_TEXTS["uz"])
    buttons = [
        [InlineKeyboardButton(text=texts["edit"], callback_data="edit_profile_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


USER_MANAGEMENT_BUTTON_TEXTS = {
    "uz": {"ban": "🚫 Bloklash", "unban": "✅ Blokdan chiqarish", "back": "⬅️ Orqaga"},
    "ru": {"ban": "🚫 Заблокировать", "unban": "✅ Разблокировать", "back": "⬅️ Назад"},
    "en": {"ban": "🚫 Ban", "unban": "✅ Unban", "back": "⬅️ Back"},
}


def get_user_management_keyboard(language: str, user_id: int, is_banned: bool):
    texts = USER_MANAGEMENT_BUTTON_TEXTS.get(language, USER_MANAGEMENT_BUTTON_TEXTS["uz"])
    buttons = []

    if is_banned:
        buttons.append(
            InlineKeyboardButton(text=texts["unban"], callback_data=f"manage_unban_{user_id}")
        )
    else:
        buttons.append(
            InlineKeyboardButton(text=texts["ban"], callback_data=f"manage_ban_{user_id}")
        )
    
    return InlineKeyboardMarkup(inline_keyboard=[buttons])


MODERATION_BUTTON_TEXTS = {
    "uz": {"approve": "✅ Tasdiqlash", "reject": "❌ Rad etish", "ban": "🚫 Bloklash (Foydalanuvchi)"},
    "ru": {"approve": "✅ Одобрить", "reject": "❌ Отклонить", "ban": "🚫 Заблокировать (Пользователя)"},
    "en": {"approve": "✅ Approve", "reject": "❌ Reject", "ban": "🚫 Ban (User)"},
}


def get_moderation_keyboard(language: str = "uz", photo_id: int = 0, user_id: int = 0):
    texts = MODERATION_BUTTON_TEXTS.get(language, MODERATION_BUTTON_TEXTS["uz"])
    buttons = [
        [
            InlineKeyboardButton(text=texts["approve"], callback_data=f"mod_approve_{photo_id}"),
            InlineKeyboardButton(text=texts["reject"], callback_data=f"mod_reject_{photo_id}"),
        ],
        [InlineKeyboardButton(text=texts["ban"], callback_data=f"mod_ban_{user_id}_{photo_id}")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


REPORT_ACTION_BUTTON_TEXTS = {
    "uz": {"resolve": "✅ Hal qilindi", "reject": "❌ Rad etish", "ban": "🚫 Ayblanuvchini bloklash"},
    "ru": {"resolve": "✅ Решено", "reject": "❌ Отклонить", "ban": "🚫 Заблокировать обвиняемого"},
    "en": {"resolve": "✅ Resolved", "reject": "❌ Reject", "ban": "🚫 Ban Reported User"},
}


def get_report_keyboard(language: str, report_id: int, reported_user_id: int):
    texts = REPORT_ACTION_BUTTON_TEXTS.get(language, REPORT_ACTION_BUTTON_TEXTS["uz"])
    buttons = [
        [
            InlineKeyboardButton(text=texts["resolve"], callback_data=f"report_resolve_{report_id}"),
            InlineKeyboardButton(text=texts["reject"], callback_data=f"report_reject_{report_id}"),
        ],
        [InlineKeyboardButton(text=texts["ban"], callback_data=f"report_ban_{reported_user_id}_{report_id}")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


REPORT_CATEGORY_BUTTON_TEXTS = {
    "uz": {
        "fake_profile": "Soxta profil",
        "inappropriate_content": "Nomaqbul kontent",
        "spam": "Spam",
        "insult": "Qo'pol muomala",
        "other": "Boshqa",
    },
    "ru": {
        "fake_profile": "Фейковый профиль",
        "inappropriate_content": "Неприемлемый контент",
        "spam": "Спам",
        "insult": "Оскорбление",
        "other": "Другое",
    },
    "en": {
        "fake_profile": "Fake Profile",
        "inappropriate_content": "Inappropriate Content",
        "spam": "Spam",
        "insult": "Insult",
        "other": "Other",
    },
}

def get_report_category_keyboard(language: str = "uz"):
    texts = REPORT_CATEGORY_BUTTON_TEXTS.get(language, REPORT_CATEGORY_BUTTON_TEXTS["uz"])
    buttons = [
        [InlineKeyboardButton(text=texts[category.name], callback_data=f"report_category_{category.name}")]
        for category in ReportCategory
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


HELP_BUTTON_TEXTS = {
    "uz": {
        "faq": "Savollar va Javoblar",
        "contact_support": "Texnik yordam",
        "message_admin": "✉️ Admin'ga xabar yozish",
        "back": "⬅️ Orqaga",
    },
    "ru": {
        "faq": "Часто задаваемые вопросы",
        "contact_support": "Техническая поддержка",
        "message_admin": "✉️ Написать администратору",
        "back": "⬅️ Назад",
    },
    "en": {
        "faq": "Frequently Asked Questions",
        "contact_support": "Contact Support",
        "message_admin": "✉️ Message the admin",
        "back": "⬅️ Back",
    },
}

def get_help_keyboard(language: str = "uz"):
    texts = HELP_BUTTON_TEXTS.get(language, HELP_BUTTON_TEXTS["uz"])
    buttons = [
        [InlineKeyboardButton(text=texts["faq"], callback_data="help_faq")],
        [InlineKeyboardButton(text=texts["contact_support"], callback_data="help_contact_support")],
        [InlineKeyboardButton(text=texts["message_admin"], callback_data="help_message_admin")],
        [InlineKeyboardButton(text=texts["back"], callback_data="help_back_to_main_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

VERIFICATION_MODERATION_BUTTON_TEXTS = {
    "uz": {"approve": "✅ Tasdiqlash", "reject": "❌ Rad etish"},
    "ru": {"approve": "✅ Одобрить", "reject": "❌ Отклонить"},
    "en": {"approve": "✅ Approve", "reject": "❌ Reject"},
}

def get_verification_moderation_keyboard(language: str, request_id: int):
    texts = VERIFICATION_MODERATION_BUTTON_TEXTS.get(language, VERIFICATION_MODERATION_BUTTON_TEXTS["uz"])
    buttons = [
        [
            InlineKeyboardButton(text=texts["approve"], callback_data=f"verif_approve_{request_id}"),
            InlineKeyboardButton(text=texts["reject"], callback_data=f"verif_reject_{request_id}"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


SETTINGS_BUTTON_TEXTS = {
    "uz": {
        "hide_profile": "👤 Profilni yashirish",
        "show_profile": "✅ Profilni ko'rsatish",
        "change_language": "🌐 Tilni o'zgartirish",
        "verify_account": "✅ Hisobni tasdiqlash",
        "delete_account": "🗑️ Hisobni o'chirish",
        "back": "⬅️ Orqaga",
    },
    "ru": {
        "hide_profile": "👤 Скрыть профиль",
        "show_profile": "✅ Показать профиль",
        "change_language": "🌐 Изменить язык",
        "verify_account": "✅ Верифицировать аккаунт",
        "delete_account": "🗑️ Удалить аккаунт",
        "back": "⬅️ Назад",
    },
    "en": {
        "hide_profile": "👤 Hide Profile",
        "show_profile": "✅ Show Profile",
        "change_language": "🌐 Change Language",
        "verify_account": "✅ Verify Account",
        "delete_account": "🗑️ Delete Account",
        "back": "⬅️ Back",
    },
}


def get_settings_keyboard(language: str = "uz", is_profile_hidden: bool = False, verification_status: str = "not_verified"):
    texts = SETTINGS_BUTTON_TEXTS.get(language, SETTINGS_BUTTON_TEXTS["uz"])
    buttons = []

    if is_profile_hidden:
        buttons.append([InlineKeyboardButton(text=texts["show_profile"], callback_data="settings_show_profile")])
    else:
        buttons.append([InlineKeyboardButton(text=texts["hide_profile"], callback_data="settings_hide_profile")])

    if verification_status in [VerificationStatus.not_verified.name, VerificationStatus.rejected.name]:
        buttons.append([InlineKeyboardButton(text=texts["verify_account"], callback_data="settings_verify_account")])

    buttons.append([InlineKeyboardButton(text=texts["change_language"], callback_data="settings_change_language")])
    buttons.append([InlineKeyboardButton(text=texts["delete_account"], callback_data="settings_delete_account")])
    buttons.append([InlineKeyboardButton(text=texts["back"], callback_data="settings_back_to_main_menu")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


CONFIRM_DELETE_BUTTON_TEXTS = {
    "uz": {"yes": "✅ Ha, o'chirish", "no": "❌ Yo'q, bekor qilish"},
    "ru": {"yes": "✅ Да, удалить", "no": "❌ Нет, отменить"},
    "en": {"yes": "✅ Yes, delete", "no": "❌ No, cancel"},
}


def get_confirm_delete_account_keyboard(language: str = "uz"):
    texts = CONFIRM_DELETE_BUTTON_TEXTS.get(language, CONFIRM_DELETE_BUTTON_TEXTS["uz"])
    buttons = [
        [InlineKeyboardButton(text=texts["yes"], callback_data="confirm_delete_yes")],
        [InlineKeyboardButton(text=texts["no"], callback_data="confirm_delete_no")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


PREMIUM_PLAN_BUTTON_TEXTS = {
    "uz": {
        "gold": "⭐️ Gold (30 kun) - 30,000 UZS",
        "platinum": "💎 Platinum (90 kun) - 75,000 UZS",
        "back": "⬅️ Orqaga",
    },
    "ru": {
        "gold": "⭐️ Gold (30 дней) - 30,000 UZS",
        "platinum": "💎 Platinum (90 дней) - 75,000 UZS",
        "back": "⬅️ Назад",
    },
    "en": {
        "gold": "⭐️ Gold (30 days) - 30,000 UZS",
        "platinum": "💎 Platinum (90 days) - 75,000 UZS",
        "back": "⬅️ Back",
    },
}


def get_premium_plans_keyboard(language: str = "uz"):
    texts = PREMIUM_PLAN_BUTTON_TEXTS.get(language, PREMIUM_PLAN_BUTTON_TEXTS["uz"])
    buttons = [
        [InlineKeyboardButton(text=texts["gold"], callback_data="premium_plan_gold")],
        [InlineKeyboardButton(text=texts["platinum"], callback_data="premium_plan_platinum")],
        [InlineKeyboardButton(text=texts["back"], callback_data="premium_back_to_main_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


PREMIUM_DASHBOARD_BUTTON_TEXTS = {
    "uz": {"boost": "🚀 Profilni Boost qilish (30 daq.)"},
    "ru": {"boost": "🚀 Буст профиля (30 мин.)"},
    "en": {"boost": "🚀 Boost profile (30 min.)"},
}


def get_premium_dashboard_keyboard(language: str = "uz"):
    texts = PREMIUM_DASHBOARD_BUTTON_TEXTS.get(language, PREMIUM_DASHBOARD_BUTTON_TEXTS["uz"])
    buttons = [
        [InlineKeyboardButton(text=texts["boost"], callback_data="activate_boost")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


PAYMENT_CONFIRMATION_TEXTS = {
    "uz": {"confirm": "✅ To'lov qildim"},
    "ru": {"confirm": "✅ Я оплатил"},
    "en": {"confirm": "✅ I have paid"},
}

def get_payment_confirmation_keyboard(language: str, plan: str):
    texts = PAYMENT_CONFIRMATION_TEXTS.get(language, PAYMENT_CONFIRMATION_TEXTS["uz"])
    buttons = [
        [InlineKeyboardButton(text=texts["confirm"], callback_data=f"payment_confirm_{plan}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


PAYMENT_MODERATION_BUTTON_TEXTS = {
    "uz": {"approve": "✅ Tasdiqlash", "reject": "❌ Rad etish"},
    "ru": {"approve": "✅ Одобрить", "reject": "❌ Отклонить"},
    "en": {"approve": "✅ Approve", "reject": "❌ Reject"},
}

def get_payment_moderation_keyboard(language: str, payment_id: int):
    texts = PAYMENT_MODERATION_BUTTON_TEXTS.get(language, PAYMENT_MODERATION_BUTTON_TEXTS["uz"])
    buttons = [
        [
            InlineKeyboardButton(text=texts["approve"], callback_data=f"payment_approve_{payment_id}"),
            InlineKeyboardButton(text=texts["reject"], callback_data=f"payment_reject_{payment_id}"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


LOGS_PAGINATION_TEXTS = {
    "uz": {"prev": "⬅️ Oldingisi", "next": "Keyingisi ➡️"},
    "ru": {"prev": "⬅️ Назад", "next": "Вперед ➡️"},
    "en": {"prev": "⬅️ Previous", "next": "Next ➡️"},
}

def get_logs_view_keyboard(language: str, current_page: int, total_pages: int):
    texts = LOGS_PAGINATION_TEXTS.get(language, LOGS_PAGINATION_TEXTS["uz"])
    filter_text = {"uz": "🔍 Filtr", "ru": "🔍 Фильтр", "en": "🔍 Filter"}.get(language, "🔍 Filtr")
    
    buttons = []
    pagination_row = []
    if current_page > 0:
        pagination_row.append(InlineKeyboardButton(text=texts["prev"], callback_data=f"logs_page_{current_page - 1}"))
    if current_page < total_pages - 1:
        pagination_row.append(InlineKeyboardButton(text=texts["next"], callback_data=f"logs_page_{current_page + 1}"))
    
    if pagination_row:
        buttons.append(pagination_row)
        
    buttons.append([InlineKeyboardButton(text=filter_text, callback_data="logs_filter_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


LOG_FILTER_KEYBOARD_TEXTS = {
    "uz": {
        "by_action": "Harakat turi bo'yicha",
        "by_date": "Sana bo'yicha",
        "clear": "🧹 Filtrlarni tozalash",
        "back": "⬅️ Loglarga qaytish"
    },
    "ru": {
        "by_action": "По типу действия",
        "by_date": "По дате",
        "clear": "🧹 Очистить фильтры",
        "back": "⬅️ Назад к логам"
    },
    "en": {
        "by_action": "By Action Type",
        "by_date": "By Date",
        "clear": "🧹 Clear Filters",
        "back": "⬅️ Back to Logs"
    },
}

def get_log_filter_keyboard(language: str):
    texts = LOG_FILTER_KEYBOARD_TEXTS.get(language, LOG_FILTER_KEYBOARD_TEXTS["uz"])
    buttons = [
        [InlineKeyboardButton(text=texts["by_action"], callback_data="logs_filter_action")],
        [InlineKeyboardButton(text=texts["by_date"], callback_data="logs_filter_date")],
        [InlineKeyboardButton(text=texts["clear"], callback_data="logs_filter_clear")],
        [InlineKeyboardButton(text=texts["back"], callback_data="logs_back_to_view")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_log_action_filter_keyboard(language: str):
    back_text = {"uz": "⬅️ Orqaga", "ru": "⬅️ Назад", "en": "⬅️ Back"}.get(language, "⬅️ Orqaga")
    buttons = []
    row = []
    for action in ActionType:
        row.append(InlineKeyboardButton(text=action.value, callback_data=f"log_action_{action.name}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text=back_text, callback_data="logs_back_to_filter_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


PROFILE_APPROVAL_BUTTON_TEXTS = {
    "uz": {"approve": "✅ Tasdiqlash", "reject": "❌ Rad etish"},
    "ru": {"approve": "✅ Одобрить", "reject": "❌ Отклонить"},
    "en": {"approve": "✅ Approve", "reject": "❌ Reject"},
}

def get_profile_approval_keyboard(language: str, user_id: int):
    """Admin uchun: yangi ro'yxatdan o'tgan profilni tasdiqlash/rad etish tugmalari."""
    texts = PROFILE_APPROVAL_BUTTON_TEXTS.get(language, PROFILE_APPROVAL_BUTTON_TEXTS["uz"])
    buttons = [
        [
            InlineKeyboardButton(text=texts["approve"], callback_data=f"approve_profile_{user_id}"),
            InlineKeyboardButton(text=texts["reject"], callback_data=f"reject_profile_{user_id}"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


MANAGE_ADMINS_BUTTON_TEXTS = {
    "uz": {"add": "➕ Admin qo'shish", "remove_prefix": "❌"},
    "ru": {"add": "➕ Добавить админа", "remove_prefix": "❌"},
    "en": {"add": "➕ Add admin", "remove_prefix": "❌"},
}

def get_manage_admins_keyboard(language: str, admins: list[tuple[int, str]]):
    """Admin uchun: bot orqali qo'shilgan qo'shimcha adminlar ro'yxati + boshqarish tugmalari."""
    texts = MANAGE_ADMINS_BUTTON_TEXTS.get(language, MANAGE_ADMINS_BUTTON_TEXTS["uz"])
    buttons = [
        [
            InlineKeyboardButton(
                text=f"{texts['remove_prefix']} {name} ({telegram_id})",
                callback_data=f"admin_remove_{telegram_id}",
            )
        ]
        for telegram_id, name in admins
    ]
    buttons.append([InlineKeyboardButton(text=texts["add"], callback_data="admin_add_new")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)