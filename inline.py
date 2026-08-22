import calendar
from datetime import datetime
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from typing import List, Optional
from i18n import t, MONTH_NAMES

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

# =========================================================================
# DATE OF BIRTH (YEAR -> MONTH -> DAY) STEP-BY-STEP CALENDAR SELECTOR
# =========================================================================

def get_birth_year_keyboard(lang: str = "uz", page: int = 0) -> InlineKeyboardMarkup:
    """Tug'ilgan yilni tanlash klaviaturasi (18 yoshdan katta bo'lgan yillar)"""
    current_year = datetime.now().year
    max_year = current_year - 18 # Masalan 2026 - 18 = 2008
    
    # 12 yillik sahifalar
    start_year = max_year - (page * 12)
    years = [start_year - i for i in range(12) if (start_year - i) >= 1960]
    
    rows = []
    for i in range(0, len(years), 3):
        chunk = years[i:i+3]
        rows.append([
            InlineKeyboardButton(text=f"🎂 {y}", callback_data=f"byear_{y}") for y in chunk
        ])
        
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️ Keyingiroq", callback_data=f"byearpage_{page-1}"))
    if (start_year - 12) >= 1960:
        nav_row.append(InlineKeyboardButton(text="Oldingiroq ➡️", callback_data=f"byearpage_{page+1}"))
    if nav_row:
        rows.append(nav_row)
        
    rows.append([InlineKeyboardButton(text=t("btn_back", lang), callback_data="reg_back_name")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_birth_month_keyboard(year: int, lang: str = "uz") -> InlineKeyboardMarkup:
    """Tug'ilgan oyni tanlash klaviaturasi (1-12 oylar)"""
    rows = []
    months = list(range(1, 13))
    for i in range(0, 12, 3):
        chunk = months[i:i+3]
        row = []
        for m in chunk:
            m_name = MONTH_NAMES[m].get(lang, MONTH_NAMES[m]["uz"])
            row.append(InlineKeyboardButton(text=m_name, callback_data=f"bmonth_{year}_{m}"))
        rows.append(row)
        
    rows.append([InlineKeyboardButton(text=t("btn_back", lang), callback_data="reg_back_to_year")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_birth_day_keyboard(year: int, month: int, lang: str = "uz") -> InlineKeyboardMarkup:
    """Tug'ilgan kunni tanlash klaviaturasi (1..28/30/31 kunlar jadvali)"""
    _, num_days = calendar.monthrange(year, month)
    days = list(range(1, num_days + 1))
    
    rows = []
    for i in range(0, len(days), 7):
        chunk = days[i:i+7]
        rows.append([
            InlineKeyboardButton(text=str(d), callback_data=f"bday_{year}_{month}_{d}") for d in chunk
        ])
        
    rows.append([InlineKeyboardButton(text=t("btn_back", lang), callback_data=f"reg_back_to_month_{year}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_age_selection_keyboard(lang: str = "uz", page: int = 0) -> InlineKeyboardMarkup:
    """Tezkor yosh tanlash muqobili"""
    return get_birth_year_keyboard(lang=lang, page=page)

# =========================================================================
# GENDER, HEIGHT, LOOKING FOR & INTENT
# =========================================================================

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

def get_settings_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    """Sozlamalar klaviaturasi"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_change_language", lang), callback_data="settings_change_lang")],
    ])

def get_moderation_keyboard(photo_id: int, user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"mod_appr_{photo_id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"mod_rej_{photo_id}")
        ]
    ])

def get_user_management_keyboard(user_id: int, is_banned: bool = False) -> InlineKeyboardMarkup:
    ban_btn = InlineKeyboardButton(text="🔓 Bandan chiqarish", callback_data=f"unban_{user_id}") if is_banned else InlineKeyboardButton(text="🔨 Bloklash", callback_data=f"ban_{user_id}")
    return InlineKeyboardMarkup(inline_keyboard=[
        [ban_btn],
        [InlineKeyboardButton(text="🗑 Profilni o'chirish", callback_data=f"del_user_{user_id}")]
    ])

def get_report_keyboard(report_id: int, reporter_id: int, reported_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ko'rib chiqildi", callback_data=f"rep_res_{report_id}"),
            InlineKeyboardButton(text="❌ Asossiz", callback_data=f"rep_dism_{report_id}")
        ]
    ])

def get_verification_moderation_keyboard(req_id: int, user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash (Verify)", callback_data=f"verify_user_{user_id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"unverify_user_{user_id}")
        ]
    ])

def get_payment_moderation_keyboard(payment_id: int, user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"pay_appr_{payment_id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"pay_rej_{payment_id}")
        ]
    ])

def get_logs_view_keyboard(page: int, total_pages: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="◀️", callback_data=f"logspage_{page-1}"),
            InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"),
            InlineKeyboardButton(text="▶️", callback_data=f"logspage_{page+1}")
        ]
    ])

def get_log_filter_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Barchasi", callback_data="filter_all")]
    ])

def get_log_action_filter_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Barchasi", callback_data="action_all")]
    ])

def get_profile_approval_keyboard(lang: str, user_id: int) -> InlineKeyboardMarkup:
    return get_admin_verification_keyboard(user_id, lang)

def get_manage_admins_keyboard(admins: list) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Admin qo'shish", callback_data="add_admin")]
    ])

def get_ban_duration_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1 kun", callback_data=f"bandur_{user_id}_1"),
            InlineKeyboardButton(text="7 kun", callback_data=f"bandur_{user_id}_7"),
            InlineKeyboardButton(text="Doimiy", callback_data=f"bandur_{user_id}_perm")
        ]
    ])

def get_delete_confirmation_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha, o'chirish", callback_data=f"conf_del_{user_id}"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_del")
        ]
    ])

def get_search_keyboard(user_id: int, is_super_like: bool = False) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👎", callback_data=f"pass_{user_id}"),
            InlineKeyboardButton(text="❤️ Like", callback_data=f"like_{user_id}"),
            InlineKeyboardButton(text="⭐ Super", callback_data=f"superlike_{user_id}")
        ]
    ])

def get_match_keyboard(match_id: int, user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Xabar yozish", callback_data=f"chat_{match_id}")],
        [InlineKeyboardButton(text="🔍 Qidirishda davom etish", callback_data="skip_profile")]
    ])

def get_chats_keyboard(chats: list) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_to_menu")]
    ])

def get_profile_view_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Tahrirlash", callback_data="edit_profile_menu")],
        [InlineKeyboardButton(text="📱 Mini App", web_app=WebAppInfo(url=f"{WEBAPP_URL}"))]
    ])

def get_edit_profile_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ism", callback_data="edit_name"), InlineKeyboardButton(text="Bio", callback_data="edit_bio")],
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_to_profile")]
    ])

def get_report_category_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Spam", callback_data=f"repcat_{user_id}_spam")],
        [InlineKeyboardButton(text="Behayo rasm", callback_data=f"repcat_{user_id}_nsfw")],
        [InlineKeyboardButton(text="◀️ Bekor qilish", callback_data="cancel_report")]
    ])

def get_confirm_delete_account_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑 Ha, o'chirish", callback_data="confirm_delete_acc")],
        [InlineKeyboardButton(text="◀️ Bekor qilish", callback_data="cancel_delete_acc")]
    ])

def get_premium_plans_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ VIP Obuna", callback_data="plan_vip")],
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_to_menu")]
    ])

def get_premium_dashboard_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Obuna bo'lish", callback_data="plan_vip")]
    ])

def get_likes_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❤️ Like qaytarish", callback_data=f"like_back_{user_id}")],
        [InlineKeyboardButton(text="➡️ Keyingisi", callback_data="skip_liked_profile")]
    ])

def get_help_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 Mini App", web_app=WebAppInfo(url=f"{WEBAPP_URL}"))]
    ])

def get_payment_confirmation_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ To'lov qildim", callback_data=f"paid_{order_id}")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_pay")]
    ])

def get_gift_type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌹 Gul", callback_data="gift_rose")],
        [InlineKeyboardButton(text="❤️ Yurak", callback_data="gift_heart")]
    ])

def get_back_only_keyboard(lang: str = "uz", callback_data: str = "back_to_menu") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data=callback_data)]
    ])

def get_advanced_search_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Qidirish", callback_data="adv_search_start")]
    ])

def get_region_keyboard() -> InlineKeyboardMarkup:
    return get_regions_keyboard()

def get_webapp_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 Mini App", web_app=WebAppInfo(url=f"{WEBAPP_URL}"))]
    ])

def get_photo_management_keyboard(photos: list, lang: str = "uz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Rasm qo'shish", callback_data="add_photo")],
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_to_profile")]
    ])

def get_city_keyboard(region: str, lang: str = "uz") -> InlineKeyboardMarkup:
    return get_districts_keyboard(region, lang)

def get_district_keyboard(city: str, lang: str = "uz") -> InlineKeyboardMarkup:
    return get_districts_keyboard(city, lang)

def get_bio_request_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    return get_bio_prompt_keyboard(lang)

def get_ai_bio_confirmation_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Qabul qilish", callback_data="ai_bio_accept")],
        [InlineKeyboardButton(text="🔄 Qayta yaratish", callback_data="generate_bio_ai")]
    ])

def is_tashkent_city_region(region: str) -> bool:
    return region == "Toshkent shahri"

def resolve_region_name(region: str) -> str:
    return region
