from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from states import EditingStates
from crud import (
    get_user_by_telegram_id,
    update_user_profile_field,
    update_user_photos,
)
from reply import get_main_menu_keyboard # Import get_main_menu_keyboard
from inline import get_interests_keyboard, get_photo_upload_done_keyboard # Import get_interests_keyboard, get_photo_upload_done_keyboard
from registration import NAME_INVALID_TEXTS, CITY_INVALID_TEXTS, DISTRICT_INVALID_TEXTS, BIO_TOO_LONG_TEXTS # Import validation texts

router = Router()

EDIT_REQUEST_TEXTS = {
    "uz": {
        "name": "Yangi ismingizni kiriting:",
        "bio": "O'zingiz haqingizda yangi ma'lumotni kiriting:",
        "city": "Yangi shahringizni kiriting:",
        "district": "Yangi tumaningizni kiriting:",
    },
    "ru": {
        "name": "Введите ваше новое имя:",
        "bio": "Введите новую информацию о себе:",
        "city": "Введите ваш новый город:",
        "district": "Введите ваш новый район:",
    },
    "en": {
        "name": "Enter your new name:",
        "bio": "Enter your new bio:",
        "city": "Enter your new city:",
        "district": "Enter your new district:",
    },
}

UPDATE_SUCCESS_TEXT = {
    "uz": "✅ Ma'lumot muvaffaqiyatli yangilandi! Profilingizni ko'rish uchun '👤 Mening profilim' tugmasini bosing.",
    "ru": "✅ Информация успешно обновлена! Нажмите '👤 Мой профиль', чтобы просмотреть свой профиль.",
    "en": "✅ Information updated successfully! Press '👤 My Profile' to view your profile.",
}

EDIT_INTERESTS_TEXT = {
    "uz": "Qiziqishlaringizni yangilang:",
    "ru": "Обновите ваши интересы:",
    "en": "Update your interests:",
}

EDIT_PHOTOS_TEXT = {
    "uz": "Eski rasmlaringiz o'chiriladi. Yangi rasmlaringizni yuboring (1 tadan 5 tagacha).",
    "ru": "Ваши старые фотографии будут удалены. Отправьте новые фотографии (от 1 до 5).",
    "en": "Your old photos will be deleted. Send your new photos (from 1 to 5).",
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

INTERESTS_MIN_ERROR_TEXTS = {
    "uz": "Iltimos, kamida bitta qiziqishni tanlang.",
    "ru": "Пожалуйста, выберите хотя бы одно увлечение.",
    "en": "Please select at least one interest.",
}

CANCEL_EDIT_TEXTS = {
    "uz": "Tahrirlash bekor qilindi. Asosiy menyu.",
    "ru": "Редактирование отменено. Главное меню.",
    "en": "Editing cancelled. Main menu.",
}


@router.callback_query(EditingStates.choosing_field, F.data.startswith("edit_field_"))
async def request_new_field_value(callback: CallbackQuery, state: FSMContext):
    field_to_edit = callback.data.split("_")[-1]
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = user.language or "uz"

    state_map = {
        "name": EditingStates.editing_name,
        "bio": EditingStates.editing_bio,
        "city": EditingStates.editing_city,
        "interests": EditingStates.editing_interests,
        "photos": EditingStates.editing_photos,
    }

    if field_to_edit in state_map:
        await state.set_state(state_map[field_to_edit])

        if field_to_edit == "interests":
            current_interests = user.interests.split(',') if user.interests else []
            await state.update_data(selected_interests=current_interests, language=language)
            await callback.message.edit_text(
                EDIT_INTERESTS_TEXT[language],
                reply_markup=get_interests_keyboard(language, current_interests)
            )
        elif field_to_edit == "photos":
            await state.update_data(new_photos=[], language=language)
            await callback.message.edit_text(EDIT_PHOTOS_TEXT[language])
        else:
            await callback.message.edit_text(EDIT_REQUEST_TEXTS[language][field_to_edit])
        await callback.answer()



async def process_new_text_value(message: Message, state: FSMContext, field_name: str, value: str, next_state: EditingStates = None, next_prompt_field: str = None):
    user = await get_user_by_telegram_id(message.from_user.id)
    language = user.language or "uz"

    await update_user_profile_field(user.id, field_name, value)

    if next_state:
        await state.set_state(next_state)
        await message.answer(EDIT_REQUEST_TEXTS[language][next_prompt_field])
    else:
        await state.clear()
        await message.answer(UPDATE_SUCCESS_TEXT[language])
        # Asosiy menyuni ko'rsatish uchun alohida xabar yuborish yaxshiroq
        await message.answer("Asosiy menyu:", reply_markup=get_main_menu_keyboard(language))


@router.message(EditingStates.editing_name, F.text)
async def process_new_name(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    language = user.language or "uz"
    name = message.text.strip()

    if not (2 <= len(name) <= 50 and all(c.isalpha() or c.isspace() or c == '-' for c in name)):
        await message.answer(NAME_INVALID_TEXTS.get(language, NAME_INVALID_TEXTS["uz"]))
        return
    
    await process_new_text_value(message, state, "name", name)


@router.message(EditingStates.editing_bio, F.text)
async def process_new_bio(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    language = user.language or "uz"
    bio = message.text.strip()

    if len(bio) > 500:
        await message.answer(BIO_TOO_LONG_TEXTS.get(language, BIO_TOO_LONG_TEXTS["uz"]))
        return
    
    await process_new_text_value(message, state, "bio", bio)


@router.message(EditingStates.editing_city, F.text)
async def process_new_city(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    language = user.language or "uz"
    city = message.text.strip()

    if not (2 <= len(city) <= 100 and all(c.isalpha() or c.isspace() or c == '-' for c in city)):
        await message.answer(CITY_INVALID_TEXTS.get(language, CITY_INVALID_TEXTS["uz"]))
        return
    
    await process_new_text_value(message, state, "city", city, next_state=EditingStates.editing_district, next_prompt_field="district")


@router.message(EditingStates.editing_district, F.text)
async def process_new_district(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    language = user.language or "uz"
    district = message.text.strip()

    if not (2 <= len(district) <= 100 and all(c.isalpha() or c.isspace() or c == '-' for c in district)):
        await message.answer(DISTRICT_INVALID_TEXTS.get(language, DISTRICT_INVALID_TEXTS["uz"]))
        return
    
    await process_new_text_value(message, state, "district", district, next_state=None, next_prompt_field=None)


@router.callback_query(EditingStates.editing_interests, F.data.startswith("interest_"))
async def edit_interest_selected(callback: CallbackQuery, state: FSMContext):
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


@router.callback_query(EditingStates.editing_interests, F.data == "interests_done")
async def edit_interests_done(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = user.language or "uz"
    selected_interests = data.get("selected_interests", [])

    if not selected_interests:
        await callback.answer(INTERESTS_MIN_ERROR_TEXTS[language], show_alert=True)
        return

    await update_user_profile_field(user.id, "interests", ",".join(selected_interests))

    await state.clear()
    await callback.message.edit_text(UPDATE_SUCCESS_TEXT[language])
    await callback.message.answer("Asosiy menyu:", reply_markup=get_main_menu_keyboard(language))
    await callback.answer()


@router.message(EditingStates.editing_photos, F.photo)
async def edit_photo_uploaded(message: Message, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")
    new_photos = data.get("new_photos", [])

    if len(new_photos) >= 5:
        await message.answer(PHOTO_LIMIT_EXCEEDED_TEXTS[language])
        return

    file_id = message.photo[-1].file_id
    new_photos.append(file_id)
    await state.update_data(new_photos=new_photos)

    await message.answer(
        PHOTO_UPLOAD_SUCCESS_TEXTS[language],
        reply_markup=get_photo_upload_done_keyboard(language),
    )


@router.callback_query(EditingStates.editing_photos, F.data == "photos_done")
async def edit_photos_done(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = user.language or "uz"
    new_photos = data.get("new_photos", [])

    if not new_photos:
        await callback.answer(PHOTO_MIN_ERROR_TEXTS[language], show_alert=True)
        return

    await update_user_photos(user.id, new_photos)

    await state.clear()
    await callback.message.edit_text(UPDATE_SUCCESS_TEXT[language])
    await callback.message.answer("Asosiy menyu:", reply_markup=get_main_menu_keyboard(language))
    await callback.answer()


@router.callback_query(EditingStates.choosing_field, F.data == "back_to_profile")
async def back_to_profile_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = user.language or "uz"
    await callback.message.delete()
    await callback.message.answer(
        CANCEL_EDIT_TEXTS.get(language, CANCEL_EDIT_TEXTS["uz"]),
        reply_markup=get_main_menu_keyboard(language)
    )
    await callback.answer()