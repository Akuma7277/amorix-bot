import logging
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from aiogram.filters import Command

from inline import (
    get_accept_terms_keyboard,
    get_age_keyboard,
    get_city_keyboard,
    get_district_keyboard,
    get_gender_keyboard,
    get_looking_for_keyboard,
    get_interests_keyboard,
    ALL_INTERESTS,
    get_photo_upload_done_keyboard,
    get_region_keyboard,
    get_review_keyboard,
    get_edit_profile_keyboard,
    resolve_region_name,
    is_tashkent_city_region,
)
from reply import get_main_menu_keyboard
from crud import create_user_profile
from states import RegistrationStates, EditingStates
from common import MAIN_MENU_TEXTS

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

LOOKING_FOR_REQUEST_TEXTS = {
    "uz": "Kimni qidiryapsiz?",
    "ru": "Кого вы ищете?",
    "en": "Who are you looking for?",
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

REVIEW_PROFILE_TEXTS = {
    "uz": "Ajoyib! Ro'yxatdan o'tish jarayoni yakunlandi. Endi profilingizni ko'rib chiqishingiz va tasdiqlashingiz mumkin.",
    "ru": "Отлично! Процесс регистрации завершен. Теперь вы можете просмотреть и подтвердить свой профиль.",
    "en": "Great! Registration is complete. Now you can review and confirm your profile.",
}

PROFILE_PREVIEW_TEXTS = {
    "uz": (
        "<b>Sizning profilingiz:</b>\n\n"
        "<b>Ism:</b> {name}\n"
        "<b>Yosh:</b> {age}\n"
        "<b>Shahar:</b> {city}, {district}\n"
        "<b>Qiziqishlar:</b> {interests}\n\n"
        "<b>Bio:</b>\n{bio}\n\n"
        "Ma'lumotlar to'g'riligini tasdiqlang."
    ),
    "ru": (
        "<b>Ваш профиль:</b>\n\n"
        "<b>Имя:</b> {name}\n"
        "<b>Возраст:</b> {age}\n"
        "<b>Город:</b> {city}, {district}\n"
        "<b>Интересы:</b> {interests}\n\n"
        "<b>О себе:</b>\n{bio}\n\n"
        "Подтвердите правильность данных."
    ),
    "en": (
        "<b>Your profile:</b>\n\n"
        "<b>Name:</b> {name}\n"
        "<b>Age:</b> {age}\n"
        "<b>City:</b> {city}, {district}\n"
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
        text=terms_text, reply_markup=get_accept_terms_keyboard(language)
    )
    await callback.answer()
    await state.set_state(RegistrationStates.accepting_terms)


@router.callback_query(RegistrationStates.accepting_terms, F.data == "accept_terms")
async def terms_accepted(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")

    next_step_text = NEXT_STEP_TEXTS.get(language, NEXT_STEP_TEXTS["uz"])

    await callback.message.edit_text(next_step_text)
    await callback.answer()
    await state.set_state(RegistrationStates.entering_name)


@router.message(RegistrationStates.entering_name, F.text)
async def name_entered(message: Message, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")
    name = message.text.strip()

    if not (2 <= len(name) <= 50 and all(c.isalpha() or c.isspace() or c == '-' for c in name)):
        await message.answer(NAME_INVALID_TEXTS.get(language, NAME_INVALID_TEXTS["uz"]))
        return
    
    await state.update_data(name=name)

    await message.answer(AGE_REQUEST_TEXTS.get(language, AGE_REQUEST_TEXTS["uz"]))
    await state.set_state(RegistrationStates.entering_age)


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
        reply_markup=get_gender_keyboard(language),
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
        reply_markup=get_gender_keyboard(language),
    )
    await callback.answer()
    await state.set_state(RegistrationStates.choosing_gender)


@router.callback_query(RegistrationStates.choosing_gender, F.data.startswith("gender_"))
async def gender_chosen(callback: CallbackQuery, state: FSMContext):
    gender = callback.data.split("_")[1]
    await state.update_data(gender=gender)

    data = await state.get_data()
    language = data.get("language", "uz")

    await callback.message.edit_text(
        text=LOOKING_FOR_REQUEST_TEXTS.get(language, LOOKING_FOR_REQUEST_TEXTS["uz"]),
        reply_markup=get_looking_for_keyboard(language),
    )
    await callback.answer()
    await state.set_state(RegistrationStates.choosing_looking_for)


@router.callback_query(
    RegistrationStates.choosing_looking_for, F.data.startswith("looking_for_")
)
async def looking_for_chosen(callback: CallbackQuery, state: FSMContext):
    looking_for = callback.data.split("_")[2]
    await state.update_data(looking_for=looking_for)

    data = await state.get_data()
    language = data.get("language", "uz")

    await callback.message.edit_text(
        text=CITY_REQUEST_TEXTS.get(language, CITY_REQUEST_TEXTS["uz"]),
        reply_markup=get_region_keyboard(language),
    )
    await callback.answer()
    await state.set_state(RegistrationStates.entering_city)


@router.callback_query(RegistrationStates.entering_city, F.data.startswith("region_"))
async def region_selected(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")
    region_name = resolve_region_name(callback.data.split("_", 1)[1])

    await state.update_data(region=region_name)
    if is_tashkent_city_region(region_name):
        await callback.message.edit_text(
            text=DISTRICT_REQUEST_TEXTS.get(language, DISTRICT_REQUEST_TEXTS["uz"]),
            reply_markup=get_district_keyboard(region_name, language),
        )
        await callback.answer()
        await state.set_state(RegistrationStates.entering_district)
        return

    await callback.message.edit_text(
        text=CITY_SELECTION_TEXTS.get(language, CITY_SELECTION_TEXTS["uz"]),
        reply_markup=get_city_keyboard(region_name, language),
    )
    await callback.answer()
    await state.set_state(RegistrationStates.choosing_city)


@router.callback_query(RegistrationStates.choosing_city, F.data.startswith("city_"))
async def city_selected(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")
    city_name = callback.data.split("_", 1)[1].replace("_", " ").title()
    region_name = data.get("region")

    await state.update_data(city=city_name)
    await callback.message.edit_text(
        text=DISTRICT_REQUEST_TEXTS.get(language, DISTRICT_REQUEST_TEXTS["uz"]),
        reply_markup=get_district_keyboard(region_name or city_name, language),
    )
    await callback.answer()
    await state.set_state(RegistrationStates.entering_district)


@router.message(RegistrationStates.entering_city, F.text)
async def city_entered(message: Message, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")
    city = message.text.strip()

    if not (2 <= len(city) <= 100 and all(c.isalpha() or c.isspace() or c == '-' for c in city)):
        await message.answer(CITY_INVALID_TEXTS.get(language, CITY_INVALID_TEXTS["uz"]))
        return

    await state.update_data(city=city)

    await message.answer(DISTRICT_REQUEST_TEXTS.get(language, DISTRICT_REQUEST_TEXTS["uz"])) # DISTRICT_REQUEST_TEXTS was missing
    await state.set_state(RegistrationStates.entering_district)


@router.callback_query(RegistrationStates.entering_district, F.data.startswith("district_"))
async def district_selected(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")
    district = callback.data.split("_", 1)[1].replace("_", " ").title()

    await state.update_data(district=district)
    await callback.message.edit_text(
        text=INTERESTS_REQUEST_TEXTS.get(language, INTERESTS_REQUEST_TEXTS["uz"]),
        reply_markup=get_interests_keyboard(language),
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
        reply_markup=get_interests_keyboard(language),
    )
    await state.set_state(RegistrationStates.choosing_interests)


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
        reply_markup=get_interests_keyboard(language, selected_interests)
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
        text=BIO_REQUEST_TEXTS.get(language, BIO_REQUEST_TEXTS["uz"])
    )
    await callback.answer()
    await state.set_state(RegistrationStates.entering_bio)
    await state.update_data(interests=selected_interests) # Finalize for create_user_profile


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
        reply_markup=get_photo_upload_done_keyboard(language),
    )
    await state.set_state(RegistrationStates.uploading_photos)


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
        reply_markup=get_photo_upload_done_keyboard(language),
    )


@router.message(RegistrationStates.uploading_photos, ~F.photo)
async def photo_upload_invalid_message(message: Message, state: FSMContext):
    """Foydalanuvchi rasm o'rniga boshqa turdagi xabar yuborganda"""
    data = await state.get_data()
    language = data.get("language", "uz")
    await message.answer(
        PHOTO_REQUEST_TEXTS.get(language, PHOTO_REQUEST_TEXTS["uz"]),
        reply_markup=get_photo_upload_done_keyboard(language) if data.get("photos") else None
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
        await create_user_profile(telegram_id, data)
    except Exception as e:
        logging.error(f"Foydalanuvchi {telegram_id} uchun profil yaratishda xatolik: {e}")
        await callback.message.answer("Profilingizni yaratishda xatolik yuz berdi. Iltimos, /start buyrug'ini bosib qayta urinib ko'ring.", reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return

    # Qiziqishlar nomlarini olish
    interest_keys = data.get("interests", [])
    interest_names = [ALL_INTERESTS[key].get(language, ALL_INTERESTS[key]['uz']) for key in interest_keys]

    caption_text = PROFILE_PREVIEW_TEXTS.get(language, PROFILE_PREVIEW_TEXTS["uz"]).format(
        name=data.get("name"),
        age=data.get("age"),
        city=data.get("city"),
        district=data.get("district"),
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


@router.callback_query(RegistrationStates.reviewing_profile, F.data == "confirm_profile")
async def profile_confirmed(callback: CallbackQuery, state: FSMContext):
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