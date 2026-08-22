from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from typing import List, Optional
from i18n import t

# 14 Administrative Regions of Uzbekistan
UZBEK_REGIONS = {
    "Toshkent shahri": [
        "Yunusobod", "Chilonzor", "Mirzo Ulug'bek", "Mirobod", "Yakkasaroy", 
        "Shayxontohur", "Olmazor", "Uchtepa", "Sergeli", "Yashnobod", 
        "Bektemir", "Yangihayot"
    ],
    "Toshkent viloyati": [
        "Zangiota", "Qibray", "Toshkent t.", "Chirchiq", "Olmaliq", "Angren", 
        "Bekobod", "Ohangaron", "Parkent", "Bo'stonliq", "Yangiyo'l", "Chinoz", "Yuqorichirchiq"
    ],
    "Samarqand": [
        "Samarqand sh.", "Urgut", "Kattaqo'rg'on", "Pastdarg'om", "Bulung'ur", 
        "Jomboy", "Toyloq", "Payariq", "Ishtixon", "Narpay", "Oqdaryo"
    ],
    "Buxoro": [
        "Buxoro sh.", "G'ijduvon", "Kogon", "Jondor", "Vobkent", "Shofirkon", 
        "Qorako'l", "Romitan", "Peshku", "Olot"
    ],
    "Andijon": [
        "Andijon sh.", "Asaka", "Shahrixon", "Xo'jaobod", "Qo'rg'ontepa", 
        "Oltinko'l", "Baliqchi", "Izboskan", "Paxtaobod", "Marhamat"
    ],
    "Farg'ona": [
        "Farg'ona sh.", "Marg'ilon", "Qo'qon", "Quva", "Rishton", "Oltiariq", 
        "Beshariq", "Toshloq", "Uchko'prik", "Bog'dod", "Yozyovon"
    ],
    "Namangan": [
        "Namangan sh.", "Chust", "Pop", "Uchqo'rg'on", "Chortoq", "Kosonsoy", 
        "To'raqo'rg'on", "Yangiqo'rg'on", "Mingbuloq"
    ],
    "Qashqadaryo": [
        "Qarshi sh.", "Shahrisabz", "Kitob", "Koson", "Yakkabog'", "Chiroqchi", 
        "G'uzor", "Nishon", "Muborak", "Kasbi", "Dehqonobod"
    ],
    "Surxondaryo": [
        "Termiz sh.", "Denov", "Sherobod", "Sho'rchi", "Jarqo'rg'on", "Boysun", 
        "Sariosiyo", "Qumqo'rg'on", "Uzun", "Angor", "Muzrabot"
    ],
    "Xorazm": [
        "Urganch sh.", "Xiva", "Xonqa", "Hazorasp", "Gurlan", "Shovot", 
        "Qo'shko'pir", "Bog'ot", "Yangiariq"
    ],
    "Navoiy": [
        "Navoiy sh.", "Zarafshon", "Karmana", "Qiziltepa", "Xatirchi", 
        "Uchquduq", "Konimex", "Nurota"
    ],
    "Jizzax": [
        "Jizzax sh.", "Zomin", "G'allaorol", "Sharof Rashidov", "Zarbdor", 
        "Paxtakor", "Forish", "Baxmal", "Do'stlik"
    ],
    "Sirdaryo": [
        "Guliston sh.", "Yangiyer", "Shirin", "Sirdaryo t.", "Boyovut", 
        "Sayxunobod", "Sardoba", "Oqoltin"
    ],
    "Qoraqalpog'iston": [
        "Nukus sh.", "Xo'jayli", "To'rtko'l", "Beruniy", "Chimboy", 
        "Qo'ng'irot", "Ellikqal'a", "Amudaryo", "Mo'ynoq"
    ],
}

ALL_INTERESTS = {
    "gaming": {"uz": "🎮 Gaming", "ru": "🎮 Гейминг", "en": "🎮 Gaming"},
    "music": {"uz": "🎵 Musiqa", "ru": "🎵 Музыка", "en": "🎵 Music"},
    "fitness": {"uz": "🏋️ Fitnes", "ru": "🏋️ Фитнес", "en": "🏋️ Fitness"},
    "travel": {"uz": "✈️ Sayohat", "ru": "✈️ Путешествия", "en": "✈️ Travel"},
    "books": {"uz": "📚 Kitoblar", "ru": "📚 Книги", "en": "📚 Books"},
    "movies": {"uz": "🎬 Kinolar", "ru": "🎬 Кино", "en": "🎬 Movies"},
    "sport": {"uz": "⚽ Sport", "ru": "⚽ Спорт", "en": "⚽ Sports"},
    "tech": {"uz": "💻 Texnologiya", "ru": "💻 Технологии", "en": "💻 Tech"},
    "cooking": {"uz": "🍳 Pazandachilik", "ru": "🍳 Кулинария", "en": "🍳 Cooking"},
    "art": {"uz": "🎨 San'at", "ru": "🎨 Искусство", "en": "🎨 Art"},
    "photo": {"uz": "📸 Suratga olish", "ru": "📸 Фотография", "en": "📸 Photography"},
    "coffee": {"uz": "☕ Qahva", "ru": "☕ Кофе", "en": "☕ Coffee"},
}

def get_language_keyboard() -> InlineKeyboardMarkup:
    """Til tanlash klaviaturasi"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz")],
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")],
    ])

def get_terms_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    """Qoidalarga rozilik klaviaturasi"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_accept_terms", lang), callback_data="accept_terms")],
        [InlineKeyboardButton(text=t("btn_back", lang), callback_data="reg_back_language")],
    ])

def get_back_keyboard(callback_data: str, lang: str = "uz") -> InlineKeyboardMarkup:
    """Faqat orqaga tugmasi"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_back", lang), callback_data=callback_data)],
    ])

def get_age_selection_keyboard(lang: str = "uz", page: int = 0) -> InlineKeyboardMarkup:
    """Yoshni tanlash uchun inline klaviatura (18 yoshdan 65+ gacha)"""
    # 12 ta yosh har bir sahifada
    base_age = 18 + (page * 12)
    ages = [base_age + i for i in range(12) if (base_age + i) <= 70]
    
    rows = []
    # 3 tadan joylashtirish
    for i in range(0, len(ages), 3):
        chunk = ages[i:i+3]
        rows.append([
            InlineKeyboardButton(text=f"🎂 {age}", callback_data=f"age_{age}") for age in chunk
        ])
    
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️ 18-29", callback_data=f"agepage_{page-1}"))
    if (base_age + 12) <= 70:
        nav_row.append(InlineKeyboardButton(text="30+ ➡️", callback_data=f"agepage_{page+1}"))
    if nav_row:
        rows.append(nav_row)
        
    rows.append([InlineKeyboardButton(text=t("btn_back", lang), callback_data="reg_back_name")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_gender_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    """Jinsni tanlash klaviaturasi"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("gender_male", lang), callback_data="gender_MALE")],
        [InlineKeyboardButton(text=t("gender_female", lang), callback_data="gender_FEMALE")],
        [InlineKeyboardButton(text=t("gender_other", lang), callback_data="gender_OTHER")],
        [InlineKeyboardButton(text=t("btn_back", lang), callback_data="reg_back_age")],
    ])

def get_height_selection_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    """Bo'y uzunligini tanlash klaviaturasi"""
    heights = [
        "150-155", "156-160", "161-165", 
        "166-170", "171-175", "176-180", 
        "181-185", "186-190", "191-200"
    ]
    rows = []
    for i in range(0, len(heights), 3):
        chunk = heights[i:i+3]
        rows.append([
            InlineKeyboardButton(text=h, callback_data=f"height_{h}") for h in chunk
        ])
    rows.append([
        InlineKeyboardButton(text=t("btn_skip", lang), callback_data="height_skip"),
    ])
    rows.append([
        InlineKeyboardButton(text=t("btn_back", lang), callback_data="reg_back_gender"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_looking_for_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    """Kimni qidiryapsiz klaviaturasi"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("target_female", lang), callback_data="looking_for_FEMALE")],
        [InlineKeyboardButton(text=t("target_male", lang), callback_data="looking_for_MALE")],
        [InlineKeyboardButton(text=t("target_any", lang), callback_data="looking_for_ANY")],
        [InlineKeyboardButton(text=t("btn_back", lang), callback_data="reg_back_height")],
    ])

def get_intent_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    """Tanishuv maqsadini tanlash klaviaturasi"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("intent_serious", lang), callback_data="intent_SERIOUS_RELATIONSHIP")],
        [InlineKeyboardButton(text=t("intent_dating", lang), callback_data="intent_DATING")],
        [InlineKeyboardButton(text=t("intent_chat", lang), callback_data="intent_FRIENDSHIP_AND_CHAT")],
        [InlineKeyboardButton(text=t("intent_unsure", lang), callback_data="intent_NOT_SURE_YET")],
        [InlineKeyboardButton(text=t("btn_back", lang), callback_data="reg_back_looking_for")],
    ])

def get_regions_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    """O'zbekiston viloyatlari klaviaturasi"""
    regions = list(UZBEK_REGIONS.keys())
    rows = []
    for i in range(0, len(regions), 2):
        chunk = regions[i:i+2]
        rows.append([
            InlineKeyboardButton(text=f"📍 {r}", callback_data=f"region_{r}") for r in chunk
        ])
    rows.append([
        InlineKeyboardButton(text=t("btn_back", lang), callback_data="reg_back_intent"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_districts_keyboard(region: str, lang: str = "uz") -> InlineKeyboardMarkup:
    """Tanlangan viloyatning tumanlari klaviaturasi"""
    districts = UZBEK_REGIONS.get(region, ["Markaz"])
    rows = []
    for i in range(0, len(districts), 2):
        chunk = districts[i:i+2]
        rows.append([
            InlineKeyboardButton(text=d, callback_data=f"district_{d}") for d in chunk
        ])
    rows.append([
        InlineKeyboardButton(text=t("btn_back", lang), callback_data="reg_back_region"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_interests_keyboard(lang: str = "uz", selected_interests: Optional[List[str]] = None) -> InlineKeyboardMarkup:
    """Qiziqishlarni multi-tanlash klaviaturasi"""
    if selected_interests is None:
        selected_interests = []
    
    rows = []
    keys = list(ALL_INTERESTS.keys())
    for i in range(0, len(keys), 2):
        chunk = keys[i:i+2]
        btn_row = []
        for k in chunk:
            name = ALL_INTERESTS[k].get(lang, ALL_INTERESTS[k]["uz"])
            is_sel = k in selected_interests
            text = f"✓ {name}" if is_sel else name
            btn_row.append(InlineKeyboardButton(text=text, callback_data=f"interest_{k}"))
        rows.append(btn_row)
    
    if len(selected_interests) >= 1:
        rows.append([InlineKeyboardButton(text=f"{t('btn_done', lang)} ({len(selected_interests)}) ➡️", callback_data="interests_done")])
    
    rows.append([InlineKeyboardButton(text=t("btn_back", lang), callback_data="reg_back_district")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_bio_prompt_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    """Bio kiritish bosqichidagi AI va orqaga tugmalari"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_generate_ai_bio", lang), callback_data="generate_bio_ai")],
        [InlineKeyboardButton(text=t("btn_back", lang), callback_data="reg_back_interests")],
    ])

def get_photo_upload_done_keyboard(lang: str = "uz", count: int = 1) -> InlineKeyboardMarkup:
    """Rasm yuklangandan keyingi davom etish klaviaturasi"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"✅ {t('btn_done', lang)} ({count} ta rasm)", callback_data="photos_done")],
        [InlineKeyboardButton(text=t("btn_back", lang), callback_data="reg_back_bio")],
    ])

def get_review_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    """Anketani tasdiqlash klaviaturasi"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_confirm_profile", lang), callback_data="confirm_profile")],
        [InlineKeyboardButton(text=t("btn_edit_profile", lang), callback_data="edit_profile")],
    ])

def get_admin_verification_keyboard(user_id: int, lang: str = "uz") -> InlineKeyboardMarkup:
    """Admin uchun profilni verifikatsiya qilish klaviaturasi"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t("btn_admin_verify", lang), callback_data=f"verify_user_{user_id}"),
            InlineKeyboardButton(text=t("btn_admin_reject_verify", lang), callback_data=f"unverify_user_{user_id}"),
        ]
    ])
