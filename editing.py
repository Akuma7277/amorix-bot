from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from ai import generate_bio_with_ai
from crud import get_user_by_telegram_id, update_user_profile_field, update_user_photos
from inline import (
    get_region_keyboard,
    get_city_keyboard,
    get_district_keyboard,
    get_interests_keyboard,
    get_bio_request_keyboard,
    get_ai_bio_confirmation_keyboard,
    get_photo_upload_done_keyboard,
    is_tashkent_city_region,
    resolve_region_name,
    ALL_INTERESTS,
)
from menu import show_my_profile
from states import EditingStates
from registration import (
    NAME_INVALID_TEXTS,
    BIO_TOO_LONG_TEXTS,
    AI_BIO_GENERATING_TEXTS,
    AI_BIO_RESULT_TEXTS,
    AI_BIO_ERROR_TEXTS,
    INTERESTS_MIN_ERROR_TEXTS,
    PHOTO_LIMIT_EXCEEDED_TEXTS,
    PHOTO_UPLOAD_SUCCESS_TEXTS,
    PHOTO_MIN_ERROR_TEXTS,
)

router = Router()

EDIT_FIELD_PROMPTS = {
    "uz": {
        "name": "Yangi ismingizni kiriting:",
        "bio": "O'zingiz haqingizda yangi ma'lumot kiriting (maksimum 500 belgi):",
        "city": "Yangi viloyatingizni tanlang:",
        "city_selection": "Yangi shahringizni tanlang:",
        "district": "Yangi tumaningizni tanlang:",
        "interests": "Qiziqishlaringizni qayta tanlang:",
        "photos": "Yangi rasmlaringizni yuboring (eskilar o'chiriladi, maksimum 5 ta). Rasmlar tayyor bo'lgach, '✅ Rasmlar tayyor' tugmasini bosing.",
    },
    "ru": {
        "name": "Введите ваше новое имя:",
        "bio": "Введите новую информацию о себе (максимум 500 символов):",
        "city": "Выберите ваш новый регион:",
        "city_selection": "Выберите ваш новый город:",
        "district": "Выберите ваш новый район:",
        "interests": "Выберите ваши интересы заново:",
        "photos": "Отправьте ваши новые фотографии (старые будут удалены, максимум 5). Когда закончите, нажмите '✅ Фотографии готовы'.",
    },
    "en": {
        "name": "Enter your new name:",
        "bio": "Enter a new bio about yourself (max 500 characters):",
        "city": "Select your new region:",
        "city_selection": "Select your new city:",
        "district": "Select your new district:",
        "interests": "Re-select your interests:",
        "photos": "Send your new photos (old ones will be deleted, max 5). When done, press '✅ Photos done'.",
    },
}

FIELD_UPDATED_TEXTS = {
    "uz": "✅ Ma'lumot muvaffaqiyatli yangilandi.",
    "ru": "✅ Информация успешно обновлена.",
    "en": "✅ Information updated successfully.",
}

PHOTOS_MODERATION_NOTICE = {
    "uz": "Rasmlaringiz moderatsiyadan o'tgandan so'ng profilingizda ko'rinadi.",
    "ru": "Ваши фотографии появятся в профиле после прохождения модерации.",
    "en": "Your photos will appear in your profile after they have been moderated.",
}


@router.callback_query(EditingStates.choosing_field, F.data == "back_to_profile")
async def back_to_profile_view(callback: CallbackQuery, state: FSMContext):
    """Handles returning to the main profile view from the edit menu."""
    await callback.message.delete()
    await show_my_profile(callback.message, state)
    await callback.answer()


# --- Edit Name ---
@router.callback_query(EditingStates.choosing_field, F.data == "edit_field_name")
async def edit_name_start(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = user.language or "uz"
    await state.set_state(EditingStates.editing_name)
    await callback.message.delete()
    await callback.message.answer(EDIT_FIELD_PROMPTS[language]["name"])
    await callback.answer()


@router.message(EditingStates.editing_name, F.text)
async def edit_name_finish(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    language = user.language or "uz"
    new_name = message.text.strip()

    if not (2 <= len(new_name) <= 50 and all(c.isalpha() or c.isspace() or c == '-' for c in new_name)):
        await message.answer(NAME_INVALID_TEXTS.get(language, NAME_INVALID_TEXTS["uz"]))
        return

    await update_user_profile_field(user.id, "name", new_name)
    await message.answer(FIELD_UPDATED_TEXTS[language])
    await show_my_profile(message, state)


# --- Edit Bio ---
@router.callback_query(EditingStates.choosing_field, F.data == "edit_field_bio")
async def edit_bio_start(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = user.language or "uz"
    await state.set_state(EditingStates.editing_bio)
    await callback.message.delete()
    await callback.message.answer(
        EDIT_FIELD_PROMPTS[language]["bio"],
        reply_markup=get_bio_request_keyboard(language, back_callback="back_to_profile")
    )
    await callback.answer()


@router.callback_query(EditingStates.editing_bio, F.data == "generate_bio_ai")
async def edit_generate_bio_handler(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = user.language or "uz"

    await callback.message.edit_text(AI_BIO_GENERATING_TEXTS.get(language, AI_BIO_GENERATING_TEXTS["uz"]))
    await callback.answer()

    interest_keys = user.interests.split(',') if user.interests else []
    interest_names = [ALL_INTERESTS[key].get(language, ALL_INTERESTS[key]['uz']) for key in interest_keys if key in ALL_INTERESTS]
    ai_user_data = {
        "name": user.name,
        "age": user.age,
        "city": user.city,
        "interests_names": interest_names,
    }

    generated_bio = await generate_bio_with_ai(ai_user_data, language)

    if not generated_bio or generated_bio.startswith("Afsuski"):
        await callback.message.edit_text(
            generated_bio or AI_BIO_ERROR_TEXTS.get(language, AI_BIO_ERROR_TEXTS["uz"]),
            reply_markup=get_bio_request_keyboard(language, "back_to_profile")
        )
        await state.set_state(EditingStates.editing_bio)
        return

    await state.update_data(generated_bio=generated_bio)
    await state.set_state(EditingStates.confirming_ai_bio)

    await callback.message.edit_text(
        f"<i>{generated_bio}</i>\n\n{AI_BIO_RESULT_TEXTS.get(language, AI_BIO_RESULT_TEXTS['uz'])}",
        reply_markup=get_ai_bio_confirmation_keyboard(language, back_callback="back_to_bio_edit")
    )

@router.message(EditingStates.editing_bio, F.text)
async def edit_bio_finish(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    language = user.language or "uz"
    new_bio = message.text

    if len(new_bio) > 500:
        await message.answer(BIO_TOO_LONG_TEXTS[language])
        return

    await update_user_profile_field(user.id, "bio", new_bio)
    await message.answer(FIELD_UPDATED_TEXTS[language])
    await show_my_profile(message, state)


@router.callback_query(EditingStates.confirming_ai_bio, F.data == "back_to_bio_edit")
async def back_to_bio_edit(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = user.language or "uz"
    await state.set_state(EditingStates.editing_bio)
    await callback.message.edit_text(
        EDIT_FIELD_PROMPTS[language]["bio"],
        reply_markup=get_bio_request_keyboard(language, back_callback="back_to_profile")
    )
    await callback.answer()


@router.callback_query(EditingStates.confirming_ai_bio, F.data == "ai_bio_regenerate")
async def edit_regenerate_bio_handler(callback: CallbackQuery, state: FSMContext):
    await edit_generate_bio_handler(callback, state)


@router.callback_query(EditingStates.confirming_ai_bio, F.data == "ai_bio_accept")
async def accept_ai_bio_for_edit_handler(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = user.language or "uz"
    data = await state.get_data()
    generated_bio = data.get("generated_bio")

    if len(generated_bio) > 500:
        await callback.answer(BIO_TOO_LONG_TEXTS[language], show_alert=True)
        await state.set_state(EditingStates.editing_bio)
        await callback.message.edit_text(
            EDIT_FIELD_PROMPTS[language]["bio"],
            reply_markup=get_bio_request_keyboard(language, back_callback="back_to_profile")
        )
        return

    await update_user_profile_field(user.id, "bio", generated_bio)
    # In editing flow, we don't have a photo on the screen to edit caption for.
    # So we delete the message and show the profile.
    await callback.message.delete()
    await callback.message.answer(FIELD_UPDATED_TEXTS[language])
    await show_my_profile(callback.message, state)
    await callback.answer()

# --- Edit City/District ---
@router.callback_query(EditingStates.choosing_field, F.data == "edit_field_city")
async def edit_city_start(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = user.language or "uz"
    await state.set_state(EditingStates.editing_city)
    await callback.message.delete()
    await callback.message.answer(
        EDIT_FIELD_PROMPTS[language]["city"],
        reply_markup=get_region_keyboard(language),
    )
    await callback.answer()


@router.callback_query(EditingStates.editing_city, F.data.startswith("region_"))
async def edit_region_selected(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = user.language or "uz"
    region_name = resolve_region_name(callback.data.split("_", 1)[1])
    await state.update_data(edit_region=region_name)

    if is_tashkent_city_region(region_name):
        await state.set_state(EditingStates.editing_district)
        await callback.message.edit_text(
            EDIT_FIELD_PROMPTS[language]["district"],
            reply_markup=get_district_keyboard(region_name, language, back_callback="edit_back_to_region_selection"),
        )
    else:
        await callback.message.edit_text(
            EDIT_FIELD_PROMPTS[language]["city_selection"],
            reply_markup=get_city_keyboard(region_name, language, back_callback="edit_back_to_region_selection"),
        )
    await callback.answer()


@router.callback_query(EditingStates.editing_city, F.data.startswith("city_"))
async def edit_city_selected(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = user.language or "uz"
    city_name = callback.data.split("_", 1)[1].replace("_", " ").title()
    data = await state.get_data()
    region_name = data.get("edit_region")

    await state.update_data(edit_city=city_name)
    await state.set_state(EditingStates.editing_district)
    await callback.message.edit_text(
        EDIT_FIELD_PROMPTS[language]["district"],
        reply_markup=get_district_keyboard(region_name, language, back_callback="edit_back_to_city_selection"),
    )
    await callback.answer()


@router.callback_query(EditingStates.editing_district, F.data.startswith("district_"))
async def edit_district_selected(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = user.language or "uz"
    district_name = callback.data.split("_", 1)[1].replace("_", " ").title()
    data = await state.get_data()
    city_name = data.get("edit_city") or data.get("edit_region") # Toshkent sh. uchun

    await update_user_profile_field(user.id, "city", city_name)
    await update_user_profile_field(user.id, "district", district_name)

    await callback.message.delete()
    await callback.message.answer(FIELD_UPDATED_TEXTS[language])
    await show_my_profile(callback.message, state)


# --- Edit Interests ---
@router.callback_query(EditingStates.choosing_field, F.data == "edit_field_interests")
async def edit_interests_start(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = user.language or "uz"
    current_interests = user.interests.split(",") if user.interests else []

    await state.set_state(EditingStates.editing_interests)
    await state.update_data(edit_interests=current_interests)
    await callback.message.delete()
    await callback.message.answer( # The comment "Error 7: Add back_callback" was misleading, the back_callback is already there.
        EDIT_FIELD_PROMPTS[language]["interests"],
        reply_markup=get_interests_keyboard(language, current_interests, back_callback="back_to_profile"),
    )
    await callback.answer()


@router.callback_query(EditingStates.editing_interests, F.data.startswith("interest_"))
async def edit_interest_selected(callback: CallbackQuery, state: FSMContext):
    interest_key = callback.data.split("_")[1]
    data = await state.get_data()
    language = data.get("language", "uz")
    selected_interests = data.get("edit_interests", [])

    if interest_key in selected_interests:
        selected_interests.remove(interest_key)
    else:
        selected_interests.append(interest_key)

    await state.update_data(edit_interests=selected_interests)
    await callback.message.edit_reply_markup(
        reply_markup=get_interests_keyboard(language, selected_interests, back_callback="back_to_profile") # Error 7: Add back_callback
    )
    await callback.answer()


@router.callback_query(EditingStates.editing_interests, F.data == "interests_done")
async def edit_interests_finish(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = user.language or "uz"
    data = await state.get_data()
    selected_interests = data.get("edit_interests", [])

    if not selected_interests:
        await callback.answer(INTERESTS_MIN_ERROR_TEXTS[language], show_alert=True)
        return

    await update_user_profile_field(user.id, "interests", ",".join(selected_interests))
    await callback.message.delete()
    await callback.message.answer(FIELD_UPDATED_TEXTS[language])
    await show_my_profile(callback.message, state)


@router.callback_query(EditingStates.editing_city, F.data == "edit_back_to_region_selection")
async def edit_back_to_region_selection(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = user.language or "uz"
    await state.set_state(EditingStates.editing_city)
    await callback.message.edit_text(
        EDIT_FIELD_PROMPTS[language]["city"],
        reply_markup=get_region_keyboard(language),
    )
    await callback.answer()


@router.callback_query(EditingStates.editing_district, F.data == "edit_back_to_city_selection")
async def edit_back_to_city_selection(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = user.language or "uz"
    data = await state.get_data()
    region_name = data.get("edit_region")

    if is_tashkent_city_region(region_name):
        await state.set_state(EditingStates.editing_district)
        await callback.message.edit_text(
            EDIT_FIELD_PROMPTS[language]["district"],
            reply_markup=get_district_keyboard(region_name, language, back_callback="edit_back_to_region_selection"),
        )
    else:
        await state.set_state(EditingStates.editing_city)
        await callback.message.edit_text(
            EDIT_FIELD_PROMPTS[language]["city_selection"],
            reply_markup=get_city_keyboard(region_name, language, back_callback="edit_back_to_region_selection"),
        )
    await callback.answer()


@router.callback_query(EditingStates.editing_interests, F.data == "back_to_profile")
async def edit_interests_back_to_profile(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await show_my_profile(callback.message, state)
    await callback.answer()
    await show_my_profile(callback.message, state)


# --- Edit Photos ---
@router.callback_query(EditingStates.choosing_field, F.data == "edit_field_photos")
async def edit_photos_start(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = user.language or "uz"
    await state.set_state(EditingStates.editing_photos)
    await state.update_data(edit_photos=[]) # Start with an empty list
    await callback.message.delete() # Delete the profile view
    await callback.message.answer(
        EDIT_FIELD_PROMPTS[language]["photos"],
        reply_markup=get_photo_upload_done_keyboard(language),
    )
    await callback.answer()


@router.message(EditingStates.editing_photos, F.photo)
async def edit_photo_uploaded(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    language = user.language or "uz"
    data = await state.get_data()
    uploaded_photos = data.get("edit_photos", [])

    if len(uploaded_photos) >= 5:
        await message.answer(PHOTO_LIMIT_EXCEEDED_TEXTS[language])
        return

    file_id = message.photo[-1].file_id
    uploaded_photos.append(file_id)
    await state.update_data(edit_photos=uploaded_photos)

    await message.answer(PHOTO_UPLOAD_SUCCESS_TEXTS[language])


@router.callback_query(EditingStates.editing_photos, F.data == "photos_done")
async def edit_photos_finish(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = user.language or "uz"
    data = await state.get_data()
    new_photos = data.get("edit_photos", [])

    if not new_photos:
        await callback.answer(PHOTO_MIN_ERROR_TEXTS[language], show_alert=True)
        return

    await update_user_photos(user.id, new_photos)
    await callback.message.answer(FIELD_UPDATED_TEXTS[language])
    await callback.message.answer(PHOTOS_MODERATION_NOTICE[language])
    await show_my_profile(callback.message, state)