"""
AMORIX / KAIRYX — Multi-Language Localization System (i18n)
Supports Uzbek (uz), Russian (ru), English (en) with TashDate-inspired minimalist UX.
"""

from typing import Any, Dict

MESSAGES: Dict[str, Dict[str, str]] = {
    # ------------------ LANGUAGE SELECTION ------------------
    "choose_language": {
        "uz": "🌐 <b>Muloqot tilini tanlang:</b>",
        "ru": "🌐 <b>Выберите язык общения:</b>",
        "en": "🌐 <b>Choose your language:</b>",
    },
    
    # ------------------ TERMS & CONDITIONS ------------------
    "terms_title": {
        "uz": (
            "📜 <b>Foydalanish Qoidalari</b>\n\n"
            "• Faqat 18 yoshdan oshgan shaxslar uchun.\n"
            "• Haqiqiy fotosurat va ma'lumotlar talab qilinadi.\n"
            "• Spam, behayo materiallar va haqorat qat'iyan taqiqlanadi.\n\n"
            "<i>Davom etish orqali qoidalarga rozilik bildirasiz.</i>"
        ),
        "ru": (
            "📜 <b>Правила использования</b>\n\n"
            "• Сервис строго для лиц старше 18 лет.\n"
            "• Требуются реальные фотографии и данные.\n"
            "• Спам, оскорбления и непристойный контент запрещены.\n\n"
            "<i>Продолжая, вы принимаете правила сообщества.</i>"
        ),
        "en": (
            "📜 <b>Terms of Service</b>\n\n"
            "• Strictly for users 18 years and older.\n"
            "• Real photos and genuine identity are required.\n"
            "• Spam, harassment, and explicit content are strictly prohibited.\n\n"
            "<i>By continuing, you accept these terms.</i>"
        ),
    },
    "btn_accept_terms": {
        "uz": "✅ Roziman",
        "ru": "✅ Принимаю",
        "en": "✅ I Agree",
    },
    "btn_back": {
        "uz": "◀️ Orqaga",
        "ru": "◀️ Назад",
        "en": "◀️ Back",
    },
    "btn_skip": {
        "uz": "⏭️ O'tkazib yuborish",
        "ru": "⏭️ Пропустить",
        "en": "⏭️ Skip",
    },
    "btn_done": {
        "uz": "➡️ Davom etish",
        "ru": "➡️ Продолжить",
        "en": "➡️ Continue",
    },

    # ------------------ REGISTRATION STEPS ------------------
    "ask_name": {
        "uz": "✨ <b>Ismingizni kiriting:</b>\n<i>(Masalan: Sarvar)</i>",
        "ru": "✨ <b>Введите ваше имя:</b>\n<i>(Например: Сарвар)</i>",
        "en": "✨ <b>Enter your name:</b>\n<i>(e.g. Alex)</i>",
    },
    "invalid_name": {
        "uz": "⚠️ Iltimos, haqiqiy ismingizni kiriting (2 tadan 30 tagacha belgi):",
        "ru": "⚠️ Пожалуйста, введите корректное имя (от 2 до 30 символов):",
        "en": "⚠️ Please enter a valid name (2 to 30 characters):",
    },
    "ask_birth_year": {
        "uz": "🎂 <b>Tug'ilgan yilingizni tanlang:</b>",
        "ru": "🎂 <b>Выберите год рождения:</b>",
        "en": "🎂 <b>Select your birth year:</b>",
    },
    "ask_age": {
        "uz": "🎂 <b>Yoshingizni tanlang:</b>",
        "ru": "🎂 <b>Выберите ваш возраст:</b>",
        "en": "🎂 <b>Select your age:</b>",
    },
    "invalid_age": {
        "uz": "⚠️ Siz 18 yoshdan oshgan bo'lishingiz kerak.",
        "ru": "⚠️ Вам должно быть не менее 18 лет.",
        "en": "⚠️ You must be at least 18 years old.",
    },
    "ask_gender": {
        "uz": "🚻 <b>Jinsingizni tanlang:</b>",
        "ru": "🚻 <b>Укажите ваш пол:</b>",
        "en": "🚻 <b>Select your gender:</b>",
    },
    "gender_male": {
        "uz": "👨 Erkak",
        "ru": "👨 Мужской",
        "en": "👨 Male",
    },
    "gender_female": {
        "uz": "👩 Ayol",
        "ru": "👩 Женский",
        "en": "👩 Female",
    },
    "gender_other": {
        "uz": "🌈 Noma'lum",
        "ru": "🌈 Другой",
        "en": "🌈 Other",
    },
    "ask_height": {
        "uz": "📏 <b>Bo'yingizni tanlang (sm):</b>",
        "ru": "📏 <b>Укажите ваш рост (см):</b>",
        "en": "📏 <b>Select your height (cm):</b>",
    },
    "ask_looking_for": {
        "uz": "🔍 <b>Kimni qidiryapsiz?</b>",
        "ru": "🔍 <b>Кого вы ищете?</b>",
        "en": "🔍 <b>Who are you looking for?</b>",
    },
    "target_female": {
        "uz": "👩 Ayollarni",
        "ru": "👩 Девушек",
        "en": "👩 Women",
    },
    "target_male": {
        "uz": "👨 Erkaklarni",
        "ru": "👨 Парней",
        "en": "👨 Men",
    },
    "target_any": {
        "uz": "🌈 Hammani",
        "ru": "🌈 Не важно",
        "en": "🌈 Anyone",
    },
    "ask_intent": {
        "uz": "🎯 <b>Tanishuvdan maqsadingiz nima?</b>",
        "ru": "🎯 <b>Какова ваша цель знакомства?</b>",
        "en": "🎯 <b>What is your dating goal?</b>",
    },
    "intent_serious": {
        "uz": "💍 Jiddiy munosabat",
        "ru": "💍 Серьёзные отношения",
        "en": "💍 Serious relationship",
    },
    "intent_chat": {
        "uz": "💬 Do'stlik va suhbat",
        "ru": "💬 Общение и дружба",
        "en": "💬 Chat & Friendship",
    },
    "intent_dating": {
        "uz": "☕ Uchrashuv / Romantika",
        "ru": "☕ Романтические встречи",
        "en": "☕ Casual dating",
    },
    "intent_unsure": {
        "uz": "🔮 Hali bilmayman",
        "ru": "🔮 Пока не знаю",
        "en": "🔮 Not sure yet",
    },
    "ask_region": {
        "uz": "📍 <b>Qaysi viloyat / shahardansiz?</b>",
        "ru": "📍 <b>Из какого вы региона / города?</b>",
        "en": "📍 <b>Which region / city are you from?</b>",
    },
    "ask_district": {
        "uz": "🏙️ <b>Tumanni tanlang ({region}):</b>",
        "ru": "🏙️ <b>Выберите район ({region}):</b>",
        "en": "🏙️ <b>Select district ({region}):</b>",
    },
    "ask_interests": {
        "uz": (
            "🎨 <b>Qiziqishlaringizni tanlang:</b>\n"
            "<i>(Bir nechta tanlab, so'ng 'Davom etish'ni bosing)</i>"
        ),
        "ru": (
            "🎨 <b>Выберите ваши интересы:</b>\n"
            "<i>(Выберите несколько и нажмите 'Продолжить')</i>"
        ),
        "en": (
            "🎨 <b>Select your interests:</b>\n"
            "<i>(Select multiple then tap 'Continue')</i>"
        ),
    },
    "ask_bio": {
        "uz": (
            "✍️ <b>O'zingiz haqingizda yozing:</b>\n"
            "<i>Qiziqishlaringiz, fe'l-atvoringiz yoki kimni qidirayotganingiz haqida qisqacha ma'lumot qoldiring.</i>\n\n"
            "✨ <i>Yoki AI yordamida avtomatik yarating:</i>"
        ),
        "ru": (
            "✍️ <b>Расскажите о себе:</b>\n"
            "<i>Кратко опишите ваши увлечения, характер или кого вы ищете.</i>\n\n"
            "✨ <i>Или сгенерируйте автоматически с помощью AI:</i>"
        ),
        "en": (
            "✍️ <b>Write about yourself:</b>\n"
            "<i>Briefly describe your hobbies, personality, or what you seek.</i>\n\n"
            "✨ <i>Or generate one automatically using AI:</i>"
        ),
    },
    "btn_generate_ai_bio": {
        "uz": "✨ AI bilan yaratish",
        "ru": "✨ Создать с AI",
        "en": "✨ Generate with AI",
    },
    "ask_photo": {
        "uz": (
            "📸 <b>Profil rasmingizni yuboring:</b>\n"
            "<i>Yuzingiz aniq ko'ringan sifatli fotosurat yuboring.</i>"
        ),
        "ru": (
            "📸 <b>Отправьте фото для профиля:</b>\n"
            "<i>Загрузите качественную фотографию, где хорошо видно лицо.</i>"
        ),
        "en": (
            "📸 <b>Upload your profile photo:</b>\n"
            "<i>Please send a clear photo where your face is well visible.</i>"
        ),
    },
    "photo_uploaded": {
        "uz": "✅ Rasm qabul qilindi. Yana rasm yuborishingiz yoki 'Davom etish'ni bosishingiz mumkin.",
        "ru": "✅ Фото принято. Вы можете отправить ещё или нажать 'Продолжить'.",
        "en": "✅ Photo accepted. You can send more or tap 'Continue'.",
    },

    # ------------------ PROFILE PREVIEW & REVIEW ------------------
    "profile_preview_title": {
        "uz": "📋 <b>Sizning anketangiz:</b>",
        "ru": "📋 <b>Ваша анкета:</b>",
        "en": "📋 <b>Your profile preview:</b>",
    },
    "btn_confirm_profile": {
        "uz": "✅ Tasdiqlash va Boshlash",
        "ru": "✅ Подтвердить и Начать",
        "en": "✅ Confirm & Start",
    },
    "btn_edit_profile": {
        "uz": "✏️ Tahrirlash",
        "ru": "✏️ Редактировать",
        "en": "✏️ Edit",
    },

    # ------------------ REGISTRATION SUCCESS (INSTANT ACCESS) ------------------
    "registration_success": {
        "uz": (
            "🎉 <b>Tabriklaymiz! Ro'yxatdan muvaffaqiyatli o'tdingiz.</b>\n\n"
            "Profilingiz faollashtirildi. Siz hoziroq yangi insonlar bilan tanishishni boshlashingiz mumkin!\n\n"
            "Pastdagi menyudan foydalaning yoki 📱 <b>Mini App</b>ni oching."
        ),
        "ru": (
            "🎉 <b>Поздравляем! Регистрация успешно завершена.</b>\n\n"
            "Ваш профиль активирован. Вы можете прямо сейчас начинать знакомиться!\n\n"
            "Используйте меню ниже или откройте 📱 <b>Mini App</b>."
        ),
        "en": (
            "🎉 <b>Congratulations! Registration completed successfully.</b>\n\n"
            "Your profile is active. You can start meeting people right away!\n\n"
            "Use the menu below or open the 📱 <b>Mini App</b>."
        ),
    },

    # ------------------ MAIN MENU BUTTONS (REPLY KEYBOARD) ------------------
    "menu_search": {
        "uz": "🔍 Qidirish",
        "ru": "🔍 Поиск",
        "en": "🔍 Search",
    },
    "menu_my_profile": {
        "uz": "👤 Mening profilim",
        "ru": "👤 Мой профиль",
        "en": "👤 My Profile",
    },
    "menu_likes": {
        "uz": "❤️ Menga yoqqanlar",
        "ru": "❤️ Кому я нравлюсь",
        "en": "❤️ Who Liked Me",
    },
    "menu_chats": {
        "uz": "💬 Suhbatlarim",
        "ru": "💬 Мои диалоги",
        "en": "💬 My Chats",
    },
    "menu_premium": {
        "uz": "⭐ Premium / VIP",
        "ru": "⭐ Премиум / VIP",
        "en": "⭐ Premium / VIP",
    },
    "menu_mini_app": {
        "uz": "📱 Mini App ni ochish",
        "ru": "📱 Открыть Mini App",
        "en": "📱 Open Mini App",
    },
    "menu_settings": {
        "uz": "⚙️ Sozlamalar",
        "ru": "⚙️ Настройки",
        "en": "⚙️ Settings",
    },
    "menu_help": {
        "uz": "ℹ️ Qoidalar va Yordam",
        "ru": "ℹ️ Помощь и Правила",
        "en": "ℹ️ Rules & Help",
    },

    # ------------------ ADMIN NOTIFICATION & VERIFICATION ------------------
    "admin_new_profile_notice": {
        "uz": (
            "🆕 <b>Yangi profil ro'yxatdan o'tdi</b>\n\n"
            "👤 Ism: <b>{name}</b> (ID: {user_id})\n"
            "🎂 Yosh: {age}\n"
            "📍 Manzil: {city}, {district}\n"
            "🚻 Jinsi: {gender} (Qidiruv: {looking_for})\n"
            "🎯 Maqsad: {intent}\n"
            "📝 Bio: <i>{bio}</i>\n"
            "🌐 Til: {lang}\n"
            "🆔 TG: <code>{telegram_id}</code>\n\n"
            "<i>Foydalanuvchi allaqachon botdan to'liq foydalanmoqda. Ushbu anketaga ✅ Verifikatsiya nishonini berishni xohlaysizmi?</i>"
        ),
        "ru": (
            "🆕 <b>Новая анкета зарегистрирована</b>\n\n"
            "👤 Имя: <b>{name}</b> (ID: {user_id})\n"
            "🎂 Возраст: {age}\n"
            "📍 Город: {city}, {district}\n"
            "🚻 Пол: {gender} (Поиск: {looking_for})\n"
            "🎯 Цель: {intent}\n"
            "📝 О себе: <i>{bio}</i>\n"
            "🌐 Язык: {lang}\n"
            "🆔 TG: <code>{telegram_id}</code>\n\n"
            "<i>Пользователь уже имеет полный доступ. Выдать галочку верификации ✅?</i>"
        ),
        "en": (
            "🆕 <b>New profile registered</b>\n\n"
            "👤 Name: <b>{name}</b> (ID: {user_id})\n"
            "🎂 Age: {age}\n"
            "📍 Location: {city}, {district}\n"
            "🚻 Gender: {gender} (Looking for: {looking_for})\n"
            "🎯 Goal: {intent}\n"
            "📝 Bio: <i>{bio}</i>\n"
            "🌐 Lang: {lang}\n"
            "🆔 TG: <code>{telegram_id}</code>\n\n"
            "<i>User already has full bot access. Grant verification badge ✅?</i>"
        ),
    },
    "btn_admin_verify": {
        "uz": "✅ Verifikatsiya berish",
        "ru": "✅ Верифицировать",
        "en": "✅ Grant Verified Badge",
    },
    "btn_admin_reject_verify": {
        "uz": "❌ Rad etish",
        "ru": "❌ Отклонить",
        "en": "❌ Reject",
    },
    "user_verified_congrats": {
        "uz": "🎉 <b>Tabriklaymiz!</b>\nProfilingiz administrator tomonidan muvaffaqiyatli verifikatsiya qilindi va profilingizga ✅ nishoni berildi!",
        "ru": "🎉 <b>Поздравляем!</b>\nВаш профиль был успешно верифицирован администратором и получил знак подлинности ✅!",
        "en": "🎉 <b>Congratulations!</b>\nYour profile has been verified by an admin and received the verified badge ✅!",
    },
    "user_unverified_notice": {
        "uz": "ℹ️ Profilingiz verifikatsiyasi bekor qilindi.",
        "ru": "ℹ️ Верификация вашего профиля была отменена.",
        "en": "ℹ️ Verification badge removed from your profile.",
    },
}

def t(key: str, lang: str = "uz", **kwargs: Any) -> str:
    """Returns localized message string with safe fallback to Uzbek and optional keyword interpolation."""
    lang_dict = MESSAGES.get(key, {})
    raw = lang_dict.get(lang) or lang_dict.get("uz") or f"[{key}]"
    if kwargs:
        try:
            return raw.format(**kwargs)
        except Exception:
            return raw
    return raw
