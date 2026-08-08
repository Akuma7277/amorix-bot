import logging
from aiogram import F, Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.types import ReplyKeyboardRemove
from aiogram.filters import Command

from ai import generate_bio_with_ai
from inline import (
    get_accept_terms_keyboard,
    get_age_keyboard,
    get_city_keyboard,
    get_district_keyboard,
    get_bio_request_keyboard,
    get_gender_keyboard,
    get_language_keyboard,
    get_looking_for_keyboard,
    get_interests_keyboard,
    ALL_INTERESTS,
    get_relationship_intent_keyboard,
    get_photo_upload_done_keyboard,
    get_region_keyboard,
    get_review_keyboard,
    get_edit_profile_keyboard,
    get_ai_bio_confirmation_keyboard,
    get_profile_approval_keyboard,
    resolve_region_name,
    get_back_only_keyboard,
    is_tashkent_city_region,
)
from reply import get_main_menu_keyboard
from crud import create_user_profile, get_user_by_telegram_id, get_user_photos
from states import RegistrationStates, EditingStates
from common import MAIN_MENU_TEXTS
from config import ADMIN_IDS

router = Router()

# Turli tillar uchun matnlar
TERMS_TEXTS = {
    "uz": (
        "<b>Foydalanish shartlari va Maxfiylik siyosati</b>\n\n"
        "Botdan foydalanishdan oldin, iltimos, quyidagi shartlarga rozilik bildiring:\n"
        "- Siz 18 yoshdan kattasiz.\n"
        "- Nomaqbul kontent joylashtirmaysiz.\n"
        "- Boshqa foydalanuvchilarga hurmat bilan muomala qilasiz.\n\n"
        "Davom etish uchun 'Roziman' tugmasini bosing."
    ),
    "ru": (
        "<b>Условия использования и Политика конфиденциальности</b>\n\n"
        "Прежде чем использовать бота, пожалуйста, согласитесь со следующими условиями:\n"
        "- Вам больше 18 лет.\n"
        "- Вы не будете публиковать неприемлемый контент.\n"
        "- Вы будете уважительно относиться к другим пользователям.\n\n"
        "Нажмите 'Согласен', чтобы продолжить."
    ),
    "en": (
        "<b>Terms of Use and Privacy Policy</b>\n\n"
        "Before using the bot, please agree to the following terms:\n"
        "- You are over 18 years old.\n"
        "- You will not post inappropriate content.\n"
        "- You will treat other users with respect.\n\n"
        "Press 'I agree' to continue."
    ),
}

NEXT_STEP_TEXTS = {
    "uz": "Rahmat! Endi ismingizni kiriting.",
    "ru": "Спасибо! Теперь введите ваше имя.",
    "en": "Thank you! Now, please enter your name.",
}

AGE_REQUEST_TEXTS = {
    "uz": "Ajoyib! Endi yoshingizni tanlang. Bu sizni mos foydalanuvchilar bilan bog'lash uchun kerak.",
    "ru": "Отлично! Теперь выберите свой возраст. Это нужно для поиска подходящих пользователей.",
    "en": "Great! Now choose your age. This helps us find better matches for you.",
}

AGE_INVALID_TEXTS = {
    "uz": "Yoshingizni raqamlarda kiriting. Masalan: 25",
    "ru": "Введите ваш возраст цифрами. Например: 25",
    "en": "Please enter your age in numbers. For example: 25",
}

AGE_TOO_YOUNG_TEXTS = {
    "uz": "Kechirasiz, botdan faqat 18 yoshdan kattalar foydalanishi mumkin. Ro'yxatdan o'tish to'xtatildi.",
    "ru": "К сожалению, ботом могут пользоваться только лица старше 18 лет. Регистрация прекращена.",
    "en": "Sorry, only users over 18 can use the bot. Registration has been cancelled.",
}

GENDER_REQUEST_TEXTS = {
    "uz": "Tushunarli. Endi jinsingizni tanlang.",
    "ru": "Понятно. Теперь выберите ваш пол.",
    "en": "Got it. Now, please select your gender.",
}

HEIGHT_REQUEST_TEXTS = {
    "uz": "Bo'yingizni santimetrda kiriting (masalan, 175).",
    "ru": "Введите ваш рост в сантиметрах (например, 175).",
    "en": "Enter your height in centimeters (e.g., 175).",
}

HEIGHT_INVALID_TEXTS = {
    "uz": "Bo'yingizni to'g'ri raqamda kiriting (masalan, 175).",
    "ru": "Введите ваш рост корректным числом (например, 175).",
    "en": "Please enter your height as a valid number (e.g., 175).",
}

LOOKING_FOR_REQUEST_TEXTS = {
    "uz": "Kimni qidiryapsiz?",
    "ru": "Кого вы ищете?",
    "en": "Who are you looking for?",
}

INTENT_REQUEST_TEXTS = {
    "uz": "Maqsadingizni tanlang. Bu sizga mos suhbatdosh topishga yordam beradi.",
    "ru": "Выберите вашу цель. Это поможет найти вам подходящего собеседника.",
    "en": "Choose your intent. This will help find a suitable match for you.",
}

CITY_REQUEST_TEXTS = {
    "uz": "Ajoyib! Endi viloyatingizni tanlang.",
    "ru": "Отлично! Теперь выберите ваш регион.",
    "en": "Great! Now choose your region.",
}

CITY_SELECTION_TEXTS = {
    "uz": "Yaxshi. Endi shaharingizni tanlang.",
    "ru": "Хорошо. Теперь выберите ваш город.",
    "en": "Good. Now choose your city.",
}

DISTRICT_REQUEST_TEXTS = {
    "uz": "Yaxshi. Endi tumaningizni tanlang.",
    "ru": "Хорошо. Теперь выберите ваш район.",
    "en": "Good. Now choose your district.",
}

INTERESTS_REQUEST_TEXTS = {
    "uz": "Deyarli tayyor! O'zingizni qiziqtirgan bir nechta mashg'ulotlarni tanlang.",
    "ru": "Почти готово! Выберите несколько интересующих вас занятий.",
    "en": "Almost there! Choose a few interests that fit you.",
}

BIO_REQUEST_TEXTS = {
    "uz": "Ajoyib! Endi o'zingiz haqingizda qisqacha bio yozing. Bu boshqalarga sizni tanishtirishga yordam beradi.",
    "ru": "Отлично! Теперь напишите короткое био о себе. Это поможет другим узнать вас.",
    "en": "Great! Write a short bio about yourself. This helps others get to know you.",
}

AI_BIO_GENERATING_TEXTS = {
    "uz": "✨ AI yordamida bio yaratilmoqda, iltimos, kuting...",
    "ru": "✨ Генерирую био с помощью ИИ, пожалуйста, подождите...",
    "en": "✨ Generating bio with AI, please wait...",
}

AI_BIO_RESULT_TEXTS = {
    "uz": "Mana siz uchun yaratilgan bio varianti. Ma'qulmi yoki boshqa variant yarataymi?",
    "ru": "Вот вариант био, сгенерированный для вас. Вам нравится или сгенерировать другой вариант?",
    "en": "Here is a bio generated for you. Do you like it, or should I generate another one?",
}

AI_BIO_ERROR_TEXTS = {
    "uz": "Xatolik yuz berdi. Bio yaratib bo'lmadi. Iltimos, o'zingiz kiriting yoki keyinroq urinib ko'ring.",
    "ru": "Произошла ошибка. Не удалось сгенерировать био. Пожалуйста, введите его вручную или попробуйте позже.",
    "en": "An error occurred. Failed to generate bio. Please enter it manually or try again later.",
}

INTERESTS_MIN_ERROR_TEXTS = {
    "uz": "Iltimos, kamida bitta qiziqishni tanlang.",
    "ru": "Пожалуйста, выберите хотя бы одно увлечение.",
    "en": "Please select at least one interest.",
}

PHOTO_REQUEST_TEXTS = {
    "uz": "So'nggi qadam! O'zingizning kamida bitta rasmingizni yuboring (ko'pi bilan 5 ta). Bu sizning profilingiz bo'ladi.",
    "ru": "Последний шаг! Отправьте хотя бы одну свою фотографию (максимум 5). Это будет ваш профиль.",
    "en": "Final step! Send at least one photo of yourself (up to 5). This will be your profile.",
}

BIO_TOO_LONG_TEXTS = {
    "uz": "Bio matni juda uzun. Iltimos, 500 belgidan oshmasin.",
    "ru": "Текст биографии слишком длинный. Пожалуйста, не превышайте 500 символов.",
    "en": "The bio is too long. Please keep it under 500 characters.",
}

PHOTO_UPLOAD_SUCCESS_TEXTS = {
    "uz": "Rasm yuklandi. Yana rasm yuborishingiz (jami 5 tagacha) yoki 'Rasmlar tayyor' tugmasini bosishingiz mumkin.",
    "ru": "Фотография загружена. Вы можете отправить еще (до 5 всего) или нажать кнопку 'Фотографии готовы'.",
    "en": "Photo uploaded. You can send more (up to 5 total) or click 'Photos done'.",
}

PHOTO_LIMIT_EXCEEDED_TEXTS = {
    "uz": "Siz maksimal rasm soniga (5 ta) yetdingiz. Iltimos, 'Rasmlar tayyor' tugmasini bosing.",
    "ru": "Вы достигли максимального количества фотографий (5). Пожалуйста, нажмите кнопку 'Фотографии готовы'.",
    "en": "You have uploaded the maximum number of photos (5). Please click 'Photos done'.",
}

PHOTO_MIN_ERROR_TEXTS = {
    "uz": "Iltimos, kamida bitta rasm yuklang.",
    "ru": "Пожалуйста, загрузите хотя бы одну фотографию.",
    "en": "Please upload at least one photo.",
}

PROFILE_PREVIEW_TEXTS = {
    "uz": (
        "<b>Sizning profilingiz:</b>\n\n"
        "<b>Ism:</b> {name}\n"
        "<b>Yosh:</b> {age}\n"
        "<b>Bo'y:</b> {height} sm\n"
        "<b>Shahar:</b> {city}, {district}\n"
        "<b>Niyat:</b> {relationship_intent}\n"
        "<b>Qiziqishlar:</b> {interests}\n\n"
        "<b>Bio:</b>\n{bio}\n\n"
        "Ma'lumotlar to'g'riligini tasdiqlang."
    ),
    "ru": (
        "<b>Ваш профиль:</b>\n\n"
        "<b>Имя:</b> {name}\n"
        "<b>Возраст:</b> {age}\n"
        "<b>Рост:</b> {height} см\n"
        "<b>Город:</b> {city}, {district}\n"
        "<b>Интересы:</b> {interests}\n\n"
        "<b>О себе:</b>\n{bio}\n\n"
        "Подтвердите правильность данных."
    ),
    "en": (
        "<b>Your profile:</b>\n\n"
        "<b>Name:</b> {name}\n"
        "<b>Age:</b> {age}\n"
        "<b>Height:</b> {height} cm\n"
        "<b>City:</b> {city}, {district}\n"
        "<b>Intent:</b> {relationship_intent}\n"
        "<b>Interests:</b> {interests}\n\n"
        "<b>Bio:</b>\n{bio}\n\n"
        "Please confirm that the information is correct."
    ),
}

REGISTRATION_COMPLETE_TEXTS = {
    "uz": "Tabriklaymiz! Siz ro'yxatdan muvaffaqiyatli o'tdingiz. Asosiy menyuga xush kelibsiz!",
    "ru": "Поздравляем! Вы успешно зарегистрировались. Добро пожаловать в главное меню!",
    "en": "Congratulations! You have successfully registered. Welcome to the main menu!",
}

EDIT_PROFILE_TEXTS = {
    "uz": "Qaysi ma'lumotni tahrirlamoqchisiz?",
    "ru": "Какую информацию вы хотите отредактировать?",
    "en": "Which information do you want to edit?",
}

CANCEL_TEXTS = {
    "uz": "Ro'yxatdan o'tish jarayoni bekor qilindi. Qayta boshlash uchun /start buyrug'ini bosing.",
    "ru": "Процесс регистрации отменен. Чтобы начать заново, введите команду /start.",
    "en": "The registration process has been cancelled. To start over, use the /start command.",
}

NAME_INVALID_TEXTS = {
    "uz": "Ismingiz kamida 2 va ko'pi bilan 50 belgidan iborat bo'lishi kerak. Faqat harflar, bo'sh joy va defis ishlatishingiz mumkin.",
    "ru": "Ваше имя должно содержать от 2 до 50 символов. Вы можете использовать только буквы, пробелы и дефисы.",
    "en": "Your name should be between 2 and 50 characters long. You can only use letters, spaces, and hyphens.",
}

CITY_INVALID_TEXTS = {
    "uz": "Shahar nomi kamida 2 va ko'pi bilan 100 belgidan iborat bo'lishi kerak. Faqat harflar, bo'sh joy va defis ishlatishingiz mumkin.",
    "ru": "Название города должно содержать от 2 до 100 символов. Вы можете использовать только буквы, пробелы и дефисы.",
    "en": "City name should be between 2 and 100 characters long. You can only use letters, spaces, and hyphens.",
}

DISTRICT_INVALID_TEXTS = {
    "uz": "Tuman nomi kamida 2 va ko'pi bilan 100 belgidan iborat bo'lishi kerak. Faqat harflar, bo'sh joy va defis ishlatishingiz mumkin.",
    "ru": "Название района должно содержать от 2 до 100 символов. Вы можете использовать только буквы, пробелы и дефисы.",
    "en": "District name should be between 2 and 100 characters long. You can only use letters, spaces, and hyphens.",
}


@router.message(Command("cancel"), RegistrationStates())
async def cancel_registration(message: Message, state: FSMContext):
    """Ro'yxatdan o'tish jarayonini bekor qiladi."""
    current_state = await state.get_state()
    if current_state is None:
        return

    data = await state.get_data()
    language = data.get("language", "uz")

    await state.clear()
    await message.answer(
        CANCEL_TEXTS.get(language, CANCEL_TEXTS["uz"]), reply_markup=ReplyKeyboardRemove()
    )

@router.callback_query(RegistrationStates.choosing_language, F.data.startswith("lang_"))
async def language_chosen(callback: CallbackQuery, state: FSMContext):
    language = callback.data.split("_")[1]
    await state.update_data(language=language)

    terms_text = TERMS_TEXTS.get(language, TERMS_TEXTS["uz"])

    await callback.message.edit_text(
        text=terms_text, reply_markup=get_accept_terms_keyboard(language, back_callback="reg_back_language")
    )
    await callback.answer()
    await state.set_state(RegistrationStates.accepting_terms)


@router.callback_query(RegistrationStates.accepting_terms, F.data == "reg_back_language")
async def back_to_language(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text="Tilni tanlang / Выберите язык / Choose a language:",
        reply_markup=get_language_keyboard(),
    )
    await callback.answer()
    await state.set_state(RegistrationStates.choosing_language)


@router.callback_query(RegistrationStates.accepting_terms, F.data == "accept_terms")
async def terms_accepted(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")

    next_step_text = NEXT_STEP_TEXTS.get(language, NEXT_STEP_TEXTS["uz"])

    await callback.message.edit_text(
        next_step_text,
        reply_markup=get_back_only_keyboard(language, "reg_back_terms"),
    )
    await callback.answer()
    await state.set_state(RegistrationStates.entering_name)


@router.callback_query(RegistrationStates.entering_name, F.data == "reg_back_terms")
async def back_to_terms(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")

    await callback.message.edit_text(
        text=TERMS_TEXTS.get(language, TERMS_TEXTS["uz"]),
        reply_markup=get_accept_terms_keyboard(language, back_callback="reg_back_language"),
    )
    await callback.answer()
    await state.set_state(RegistrationStates.accepting_terms)


@router.message(RegistrationStates.entering_name, F.text)
async def name_entered(message: Message, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")
    name = message.text.strip()

    if not (2 <= len(name) <= 50 and all(c.isalpha() or c.isspace() or c == '-' for c in name)):
        await message.answer(NAME_INVALID_TEXTS.get(language, NAME_INVALID_TEXTS["uz"]))
        return
    
    await state.update_data(name=name)

    await message.answer(
        AGE_REQUEST_TEXTS.get(language, AGE_REQUEST_TEXTS["uz"]),
        reply_markup=get_back_only_keyboard(language, "reg_back_name"),
    )
    await state.set_state(RegistrationStates.entering_age)


@router.callback_query(RegistrationStates.entering_age, F.data == "reg_back_name")
async def back_to_name(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")

    await callback.message.edit_text(
        text=NEXT_STEP_TEXTS.get(language, NEXT_STEP_TEXTS["uz"]),
        reply_markup=get_back_only_keyboard(language, "reg_back_terms"),
    )
    await callback.answer()
    await state.set_state(RegistrationStates.entering_name)


@router.message(RegistrationStates.entering_age, F.text)
async def age_entered(message: Message, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")

    if not message.text.isdigit():
        await message.answer(AGE_INVALID_TEXTS.get(language, AGE_INVALID_TEXTS["uz"]))
        return

    age = int(message.text)
    if age < 18:
        await message.answer(AGE_TOO_YOUNG_TEXTS.get(language, AGE_TOO_YOUNG_TEXTS["uz"]))
        await state.clear()  # Jarayonni to'xtatish
        return

    await state.update_data(age=age)

    await message.answer(
        GENDER_REQUEST_TEXTS.get(language, GENDER_REQUEST_TEXTS["uz"]),
        reply_markup=get_gender_keyboard(language, back_callback="reg_back_age"),
    )
    await state.set_state(RegistrationStates.choosing_gender)


@router.callback_query(RegistrationStates.entering_age, F.data.startswith("age_"))
async def age_selected(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")
    age_text = callback.data.split("_", 1)[1]

    if age_text == "done":
        await callback.answer()
        return

    if not age_text.isdigit():
        await callback.answer(AGE_INVALID_TEXTS.get(language, AGE_INVALID_TEXTS["uz"]), show_alert=True)
        return

    age = int(age_text)
    if age < 18:
        await callback.answer(AGE_TOO_YOUNG_TEXTS.get(language, AGE_TOO_YOUNG_TEXTS["uz"]), show_alert=True)
        return

    await state.update_data(age=age)
    await callback.message.edit_text(
        text=GENDER_REQUEST_TEXTS.get(language, GENDER_REQUEST_TEXTS["uz"]),
        reply_markup=get_gender_keyboard(language, back_callback="reg_back_age"),
    )
    await callback.answer()
    await state.set_state(RegistrationStates.choosing_gender)


@router.callback_query(RegistrationStates.choosing_gender, F.data == "reg_back_age")
async def back_to_age(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")

    await callback.message.edit_text(
        text=AGE_REQUEST_TEXTS.get(language, AGE_REQUEST_TEXTS["uz"]),
        reply_markup=get_back_only_keyboard(language, "reg_back_name"),
    )
    await callback.answer()
    await state.set_state(RegistrationStates.entering_age)


@router.callback_query(RegistrationStates.choosing_gender, F.data.startswith("gender_"))
async def gender_chosen(callback: CallbackQuery, state: FSMContext):
    gender = callback.data.split("_")[1]
    await state.update_data(gender=gender)

    data = await state.get_data()
    language = data.get("language", "uz")

    await callback.message.edit_text(
        text=HEIGHT_REQUEST_TEXTS.get(language, HEIGHT_REQUEST_TEXTS["uz"]),
        reply_markup=get_back_only_keyboard(language, back_callback="reg_back_gender"),
    )
    await callback.answer()
    await state.set_state(RegistrationStates.entering_height)


@router.callback_query(RegistrationStates.entering_height, F.data == "reg_back_gender")
async def back_to_gender(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")

    await callback.message.edit_text(
        text=GENDER_REQUEST_TEXTS.get(language, GENDER_REQUEST_TEXTS["uz"]),
        reply_markup=get_gender_keyboard(language, back_callback="reg_back_age"),
    )
    await callback.answer()
    await state.set_state(RegistrationStates.choosing_gender)


@router.message(RegistrationStates.entering_height, F.text)
async def height_entered(message: Message, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")

    try:
        height = float(message.text.replace(",", "."))
        if not 100 < height < 250:
            raise ValueError
    except (ValueError, TypeError):
        await message.answer(HEIGHT_INVALID_TEXTS.get(language, HEIGHT_INVALID_TEXTS["uz"]))
        return

    await state.update_data(height=height)

    await message.answer(
        text=LOOKING_FOR_REQUEST_TEXTS.get(language, LOOKING_FOR_REQUEST_TEXTS["uz"]),
        reply_markup=get_looking_for_keyboard(language, back_callback="reg_back_height"),
    )
    await state.set_state(RegistrationStates.choosing_looking_for)


@router.callback_query(RegistrationStates.choosing_looking_for, F.data == "reg_back_height")
async def back_to_height(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")

    await callback.message.edit_text(
        text=HEIGHT_REQUEST_TEXTS.get(language, HEIGHT_REQUEST_TEXTS["uz"]),
        reply_markup=get_back_only_keyboard(language, back_callback="reg_back_gender"),
    )
    await callback.answer()
    await state.set_state(RegistrationStates.entering_height)


@router.callback_query(
    RegistrationStates.choosing_looking_for, F.data.startswith("looking_for_")
)
async def looking_for_chosen(callback: CallbackQuery, state: FSMContext):
    looking_for = callback.data.split("_")[2]
    await state.update_data(looking_for=looking_for)

    data = await state.get_data()
    language = data.get("language", "uz")

    await callback.message.edit_text(
        text=INTENT_REQUEST_TEXTS.get(language, INTENT_REQUEST_TEXTS["uz"]),
        reply_markup=get_relationship_intent_keyboard(language, back_callback="reg_back_looking_for"),
    )
    await callback.answer()
    await state.set_state(RegistrationStates.choosing_intent)


@router.callback_query(RegistrationStates.choosing_intent, F.data == "reg_back_looking_for")
async def back_to_looking_for_from_intent(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")

    await callback.message.edit_text(
        text=LOOKING_FOR_REQUEST_TEXTS.get(language, LOOKING_FOR_REQUEST_TEXTS["uz"]),
        reply_markup=get_looking_for_keyboard(language, back_callback="reg_back_height"),
    )
    await callback.answer()
    await state.set_state(RegistrationStates.choosing_looking_for)


@router.callback_query(RegistrationStates.choosing_intent, F.data.startswith("intent_"))
async def intent_chosen(callback: CallbackQuery, state: FSMContext):
    intent = callback.data.split("_")[1]
    await state.update_data(relationship_intent=intent)

    data = await state.get_data()
    language = data.get("language", "uz")

    await callback.message.edit_text(
        text=CITY_REQUEST_TEXTS.get(language, CITY_REQUEST_TEXTS["uz"]),
        reply_markup=get_region_keyboard(language, back_callback="reg_back_intent"),
    )
    await callback.answer()
    await state.set_state(RegistrationStates.entering_city)

@router.callback_query(RegistrationStates.entering_city, F.data == "reg_back_looking_for")
async def back_to_looking_for(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")

    await callback.message.edit_text(
        text=LOOKING_FOR_REQUEST_TEXTS.get(language, LOOKING_FOR_REQUEST_TEXTS["uz"]),
        reply_markup=get_looking_for_keyboard(language, back_callback="reg_back_height"),
    )
    await callback.answer()
    await state.set_state(RegistrationStates.choosing_looking_for)


@router.callback_query(RegistrationStates.entering_city, F.data == "reg_back_intent")
async def back_to_intent(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")

    await callback.message.edit_text(
        text=INTENT_REQUEST_TEXTS.get(language, INTENT_REQUEST_TEXTS["uz"]),
        reply_markup=get_relationship_intent_keyboard(language, back_callback="reg_back_looking_for"),
    )
    await callback.answer()
    await state.set_state(RegistrationStates.choosing_intent)


@router.callback_query(RegistrationStates.entering_city, F.data.startswith("region_"))
async def region_selected(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")
    region_name = resolve_region_name(callback.data.split("_", 1)[1])

    await state.update_data(region=region_name)
    if is_tashkent_city_region(region_name):
        await callback.message.edit_text(
            text=DISTRICT_REQUEST_TEXTS.get(language, DISTRICT_REQUEST_TEXTS["uz"]),
            reply_markup=get_district_keyboard(region_name, language, back_callback="reg_back_city_or_region"),
        )
        await callback.answer()
        await state.set_state(RegistrationStates.entering_district)
        return

    await callback.message.edit_text(
        text=CITY_SELECTION_TEXTS.get(language, CITY_SELECTION_TEXTS["uz"]),
        reply_markup=get_city_keyboard(region_name, language, back_callback="reg_back_region"),
    )
    await callback.answer()
    await state.set_state(RegistrationStates.choosing_city)


@router.callback_query(RegistrationStates.choosing_city, F.data == "reg_back_region")
async def back_to_region_from_city(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")

    await callback.message.edit_text(
        text=CITY_REQUEST_TEXTS.get(language, CITY_REQUEST_TEXTS["uz"]),
        reply_markup=get_region_keyboard(language, back_callback="reg_back_looking_for"),
    )
    await callback.answer()
    await state.set_state(RegistrationStates.entering_city)


@router.callback_query(RegistrationStates.choosing_city, F.data.startswith("city_"))
async def city_selected(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")
    city_name = callback.data.split("_", 1)[1].replace("_", " ").title()
    region_name = data.get("region")

    await state.update_data(city=city_name)
    await callback.message.edit_text(
        text=DISTRICT_REQUEST_TEXTS.get(language, DISTRICT_REQUEST_TEXTS["uz"]),
        reply_markup=get_district_keyboard(region_name or city_name, language, back_callback="reg_back_city_or_region"),
    )
    await callback.answer()
    await state.set_state(RegistrationStates.entering_district)


@router.callback_query(RegistrationStates.entering_district, F.data == "reg_back_city_or_region")
async def back_to_city_or_region(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")
    region_name = data.get("region")

    if data.get("city"):
        await callback.message.edit_text(
            text=CITY_SELECTION_TEXTS.get(language, CITY_SELECTION_TEXTS["uz"]),
            reply_markup=get_city_keyboard(region_name, language, back_callback="reg_back_region"),
        )
        await callback.answer()
        await state.set_state(RegistrationStates.choosing_city)
        return

    await callback.message.edit_text(
        text=CITY_REQUEST_TEXTS.get(language, CITY_REQUEST_TEXTS["uz"]),
        reply_markup=get_region_keyboard(language, back_callback="reg_back_looking_for"),
    )
    await callback.answer()
    await state.set_state(RegistrationStates.entering_city)


@router.message(RegistrationStates.entering_city, F.text)
async def city_entered(message: Message, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")
    city = message.text.strip()

    if not (2 <= len(city) <= 100 and all(c.isalpha() or c.isspace() or c == '-' for c in city)):
        await message.answer(CITY_INVALID_TEXTS.get(language, CITY_INVALID_TEXTS["uz"]))
        return

    await state.update_data(city=city)

    await message.answer(
        DISTRICT_REQUEST_TEXTS.get(language, DISTRICT_REQUEST_TEXTS["uz"]),
        reply_markup=get_back_only_keyboard(language, "reg_back_city_or_region"),
    )
    await state.set_state(RegistrationStates.entering_district)


@router.callback_query(RegistrationStates.entering_district, F.data.startswith("district_"))
async def district_selected(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")
    district = callback.data.split("_", 1)[1].replace("_", " ").title()

    await state.update_data(district=district)
    await callback.message.edit_text(
        text=INTERESTS_REQUEST_TEXTS.get(language, INTERESTS_REQUEST_TEXTS["uz"]),
        reply_markup=get_interests_keyboard(language, back_callback="reg_back_district"),
    )
    await callback.answer()
    await state.set_state(RegistrationStates.choosing_interests)


@router.message(RegistrationStates.entering_district, F.text)
async def district_entered(message: Message, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")
    district = message.text.strip()

    if not (2 <= len(district) <= 100 and all(c.isalpha() or c.isspace() or c == '-' for c in district)):
        await message.answer(DISTRICT_INVALID_TEXTS.get(language, DISTRICT_INVALID_TEXTS["uz"]))
        return

    await state.update_data(district=district)

    await message.answer(
        INTERESTS_REQUEST_TEXTS.get(language, INTERESTS_REQUEST_TEXTS["uz"]),
        reply_markup=get_interests_keyboard(language, back_callback="reg_back_district"),
    )
    await state.set_state(RegistrationStates.choosing_interests)


@router.callback_query(RegistrationStates.choosing_interests, F.data == "reg_back_district")
async def back_to_district(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")
    region_name = data.get("region")

    await callback.message.edit_text(
        text=DISTRICT_REQUEST_TEXTS.get(language, DISTRICT_REQUEST_TEXTS["uz"]),
        reply_markup=get_district_keyboard(region_name, language, back_callback="reg_back_city_or_region"),
    )
    await callback.answer()
    await state.set_state(RegistrationStates.entering_district)


@router.callback_query(RegistrationStates.choosing_interests, F.data.startswith("interest_"))
async def interest_selected(callback: CallbackQuery, state: FSMContext):
    interest_key = callback.data.split("_")[1]
    data = await state.get_data()
    language = data.get("language", "uz")
    selected_interests = data.get("selected_interests", [])

    if interest_key in selected_interests:
        selected_interests.remove(interest_key)
    else:
        selected_interests.append(interest_key)

    await state.update_data(selected_interests=selected_interests)

    await callback.message.edit_reply_markup(
        reply_markup=get_interests_keyboard(language, selected_interests, back_callback="reg_back_district")
    )
    await callback.answer()


@router.callback_query(RegistrationStates.choosing_interests, F.data == "interests_done")
async def interests_done(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")
    selected_interests = data.get("selected_interests", [])

    if not selected_interests:
        await callback.answer(INTERESTS_MIN_ERROR_TEXTS.get(language, INTERESTS_MIN_ERROR_TEXTS["uz"]), show_alert=True)
        return

    await callback.message.edit_text(
        text=BIO_REQUEST_TEXTS.get(language, BIO_REQUEST_TEXTS["uz"]),
        reply_markup=get_bio_request_keyboard(language, "reg_back_interests"),
    )
    await callback.answer()
    await state.set_state(RegistrationStates.entering_bio)
    await state.update_data(interests=selected_interests) # Finalize for create_user_profile


@router.callback_query(RegistrationStates.entering_bio, F.data == "reg_back_interests")
async def back_to_interests(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")
    selected_interests = data.get("selected_interests", [])

    await callback.message.edit_text(
        text=INTERESTS_REQUEST_TEXTS.get(language, INTERESTS_REQUEST_TEXTS["uz"]),
        reply_markup=get_interests_keyboard(language, selected_interests, back_callback="reg_back_district"),
    )
    await callback.answer()
    await state.set_state(RegistrationStates.choosing_interests)


@router.callback_query(RegistrationStates.entering_bio, F.data == "generate_bio_ai")
async def generate_bio_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")

    await callback.message.edit_text(AI_BIO_GENERATING_TEXTS.get(language, AI_BIO_GENERATING_TEXTS["uz"]))
    await callback.answer()

    interest_keys = data.get("interests", [])
    interest_names = [ALL_INTERESTS[key].get(language, ALL_INTERESTS[key]['uz']) for key in interest_keys]
    ai_user_data = {
        "name": data.get("name"),
        "age": data.get("age"),
        "height": data.get("height"),
        "city": data.get("city") or data.get("region"),
        "interests_names": interest_names,
    }

    generated_bio = await generate_bio_with_ai(ai_user_data, language)

    if not generated_bio or generated_bio.startswith("Afsuski"):
        await callback.message.edit_text(
            generated_bio or AI_BIO_ERROR_TEXTS.get(language, AI_BIO_ERROR_TEXTS["uz"]),
            reply_markup=get_bio_request_keyboard(language, "reg_back_interests")
        )
        await state.set_state(RegistrationStates.entering_bio)
        return

    await state.update_data(generated_bio=generated_bio)
    await state.set_state(RegistrationStates.confirming_ai_bio)

    await callback.message.edit_text(
        f"<i>{generated_bio}</i>\n\n{AI_BIO_RESULT_TEXTS.get(language, AI_BIO_RESULT_TEXTS['uz'])}",
        reply_markup=get_ai_bio_confirmation_keyboard(language, back_callback="reg_back_bio_from_ai")
    )


@router.callback_query(RegistrationStates.confirming_ai_bio, F.data == "reg_back_bio_from_ai")
async def back_to_bio_from_ai(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")
    await callback.message.edit_text(
        text=BIO_REQUEST_TEXTS.get(language, BIO_REQUEST_TEXTS["uz"]),
        reply_markup=get_bio_request_keyboard(language, "reg_back_interests"),
    )
    await callback.answer()
    await state.set_state(RegistrationStates.entering_bio)


@router.callback_query(RegistrationStates.confirming_ai_bio, F.data == "ai_bio_regenerate")
async def regenerate_bio_handler(callback: CallbackQuery, state: FSMContext):
    await generate_bio_handler(callback, state)


@router.callback_query(RegistrationStates.confirming_ai_bio, F.data == "ai_bio_accept")
async def accept_ai_bio_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")
    generated_bio = data.get("generated_bio")
    await state.update_data(bio=generated_bio)
    await callback.message.edit_text(PHOTO_REQUEST_TEXTS.get(language, PHOTO_REQUEST_TEXTS["uz"]), reply_markup=get_photo_upload_done_keyboard(language, back_callback="reg_back_bio"))
    await state.set_state(RegistrationStates.uploading_photos)
    await callback.answer()

@router.message(RegistrationStates.entering_bio, F.text)
async def bio_entered(message: Message, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")

    if len(message.text) > 500:
        await message.answer(BIO_TOO_LONG_TEXTS.get(language, BIO_TOO_LONG_TEXTS["uz"]))
        return

    await state.update_data(bio=message.text)

    await message.answer(
        PHOTO_REQUEST_TEXTS.get(language, PHOTO_REQUEST_TEXTS["uz"]),
        reply_markup=get_photo_upload_done_keyboard(language, back_callback="reg_back_bio"),
    )
    await state.set_state(RegistrationStates.uploading_photos)


@router.callback_query(RegistrationStates.uploading_photos, F.data == "reg_back_bio")
async def back_to_bio(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")

    await callback.message.edit_text(
        text=BIO_REQUEST_TEXTS.get(language, BIO_REQUEST_TEXTS["uz"]),
        reply_markup=get_back_only_keyboard(language, "reg_back_interests"),
    )
    await callback.answer()
    await state.set_state(RegistrationStates.entering_bio)


@router.message(RegistrationStates.uploading_photos, F.photo)
async def photo_uploaded(message: Message, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")
    uploaded_photos = data.get("photos", [])

    if len(uploaded_photos) >= 5:
        await message.answer(
            PHOTO_LIMIT_EXCEEDED_TEXTS.get(language, PHOTO_LIMIT_EXCEEDED_TEXTS["uz"])
        )
        return

    # Eng katta o'lchamdagi rasmni saqlaymiz
    file_id = message.photo[-1].file_id
    uploaded_photos.append(file_id)
    await state.update_data(photos=uploaded_photos)

    await message.answer(
        PHOTO_UPLOAD_SUCCESS_TEXTS.get(language, PHOTO_UPLOAD_SUCCESS_TEXTS["uz"]),
        reply_markup=get_photo_upload_done_keyboard(language, back_callback="reg_back_bio"),
    )


@router.message(RegistrationStates.uploading_photos, ~F.photo)
async def photo_upload_invalid_message(message: Message, state: FSMContext):
    """Foydalanuvchi rasm o'rniga boshqa turdagi xabar yuborganda"""
    data = await state.get_data()
    language = data.get("language", "uz")
    if data.get("photos"):
        keyboard = get_photo_upload_done_keyboard(language, back_callback="reg_back_bio")
    else:
        keyboard = get_back_only_keyboard(language, "reg_back_bio")
    await message.answer(
        PHOTO_REQUEST_TEXTS.get(language, PHOTO_REQUEST_TEXTS["uz"]),
        reply_markup=keyboard
    )


@router.callback_query(RegistrationStates.uploading_photos, F.data == "photos_done")
async def photos_done(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")
    uploaded_photos = data.get("photos", [])

    if not uploaded_photos:
        await callback.answer(
            PHOTO_MIN_ERROR_TEXTS.get(language, PHOTO_MIN_ERROR_TEXTS["uz"]),
            show_alert=True,
        )
        return

    # Barcha ma'lumotlarni bazaga saqlash
    telegram_id = callback.from_user.id
    try:
        new_user = await create_user_profile(telegram_id, data)
    except Exception as e:
        logging.error(f"Foydalanuvchi {telegram_id} uchun profil yaratishda xatolik: {e}")
        new_user = None

    if not new_user:
        logging.error(f"Foydalanuvchi {telegram_id} uchun profil yaratib bo'lmadi (baza bilan bog'lanishda muammo).")
        await callback.message.answer(
            "Profilingizni yaratishda xatolik yuz berdi. Iltimos, birozdan so'ng /start buyrug'ini bosib qaytadan urinib ko'ring.",
            reply_markup=ReplyKeyboardRemove(),
        )
        await state.clear()
        return

    # Qiziqishlar nomlarini olish
    interest_keys = data.get("interests", [])
    interest_names = [ALL_INTERESTS[key].get(language, ALL_INTERESTS[key]['uz']) for key in interest_keys]
    
    from inline import RELATIONSHIP_INTENT_TEXTS
    intent_key = data.get("relationship_intent")
    intent_text = "Noma'lum"
    if intent_key:
        lang_intents = RELATIONSHIP_INTENT_TEXTS.get(language, RELATIONSHIP_INTENT_TEXTS["uz"])
        intent_text = lang_intents.get(intent_key, "Noma'lum")

    caption_text = PROFILE_PREVIEW_TEXTS.get(language, PROFILE_PREVIEW_TEXTS["uz"]).format(
        name=data.get("name"),
        age=data.get("age"),
        height=data.get("height"),
        city=data.get("city"),
        district=data.get("district"),
        relationship_intent=intent_text,
        interests=", ".join(interest_names),
        bio=data.get("bio"),
    )

    first_photo_id = uploaded_photos[0]

    # Oldingi xabarni o'chirish
    await callback.message.delete()

    # Rasm va profil ma'lumotlarini yuborish
    await callback.message.answer_photo(
        photo=first_photo_id,
        caption=caption_text,
        reply_markup=get_review_keyboard(language)
    )

    await state.set_state(RegistrationStates.reviewing_profile)


NEW_PROFILE_ADMIN_NOTIFICATION_TEXT = (
    "🆕 <b>Yangi profil tasdiqlashni kutmoqda</b>\n\n"
    "👤 Ism: {name}\n"
    "🎂 Yosh: {age}\n"
    "📍 Manzil: {city}, {district}\n"
    "❤️ Qiziqishlar: {interests}\n"
    "📝 Bio: {bio}\n\n"
    "🆔 Telegram ID: {telegram_id}"
)


async def notify_admins_about_new_profile(bot: Bot, telegram_id: int) -> None:
    """Ro'yxatdan to'liq o'tgan yangi profil haqida barcha adminlarga tasdiqlash so'rovini yuboradi."""
    user = await get_user_by_telegram_id(telegram_id)
    if not user:
        logging.warning(f"Admin bildirishnomasi uchun foydalanuvchi topilmadi: {telegram_id}")
        return

    photos = await get_user_photos(user.id)
    interest_keys = user.interests.split(",") if user.interests else []
    interest_names = [
        ALL_INTERESTS[key].get("uz", ALL_INTERESTS[key]["uz"])
        for key in interest_keys
        if key in ALL_INTERESTS
    ]

    caption = NEW_PROFILE_ADMIN_NOTIFICATION_TEXT.format(
        name=user.name,
        age=user.age,
        city=user.city,
        district=user.district,
        interests=", ".join(interest_names) if interest_names else "Yo'q",
        bio=user.bio or "-",
        telegram_id=user.telegram_id,
    )
    keyboard = get_profile_approval_keyboard("uz", user.id)

    for admin_id in ADMIN_IDS:
        try:
            if photos:
                await bot.send_photo(chat_id=admin_id, photo=photos[0].file_id, caption=caption, reply_markup=keyboard)
            else:
                await bot.send_message(chat_id=admin_id, text=caption, reply_markup=keyboard)
        except Exception as exc:
            logging.warning(f"Admin {admin_id} ga yangi profil haqida xabar berib bo'lmadi: {exc}")


@router.callback_query(RegistrationStates.reviewing_profile, F.data == "confirm_profile")
async def profile_confirmed(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    language = data.get("language", "uz")

    # Klaviaturani olib tashlash
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer()

    await callback.message.answer(
        REGISTRATION_COMPLETE_TEXTS.get(language, REGISTRATION_COMPLETE_TEXTS["uz"])
    )
    # Asosiy menyuni ko'rsatish
    await callback.message.answer(
        MAIN_MENU_TEXTS.get(language, MAIN_MENU_TEXTS["uz"]),
        reply_markup=get_main_menu_keyboard(language)
    )
    await state.clear()

    await notify_admins_about_new_profile(bot, callback.from_user.id)


@router.callback_query(RegistrationStates.reviewing_profile, F.data == "edit_profile")
async def profile_edit(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")

    await state.set_state(EditingStates.choosing_field)
    await callback.message.edit_caption(
        caption=EDIT_PROFILE_TEXTS.get(language, EDIT_PROFILE_TEXTS["uz"]),
        reply_markup=get_edit_profile_keyboard(language)
    )
    await callback.answer()