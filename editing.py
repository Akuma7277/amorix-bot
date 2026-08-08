from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton

from ai import generate_bio_with_ai
from crud import get_user_by_telegram_id, update_user_profile_field, get_user_photos, set_primary_photo, delete_photo, add_photo
from inline import (
    get_region_keyboard,
    get_photo_management_keyboard,
    get_edit_profile_keyboard,
    get_city_keyboard,
    get_district_keyboard,
    get_interests_keyboard,
    get_bio_request_keyboard,
    get_ai_bio_confirmation_keyboard,
    get_photo_upload_done_keyboard,
    is_tashkent_city_region,
    get_back_only_keyboard,
    resolve_region_name,
    ALL_INTERESTS,
)
from menu import show_my_profile
from states import EditingStates, MenuStates
from registration import (
    HEIGHT_INVALID_TEXTS,
    NAME_INVALID_TEXTS,
    EDIT_PROFILE_TEXTS,
    AGE_INVALID_TEXTS,
    AGE_TOO_YOUNG_TEXTS,
    BIO_TOO_LONG_TEXTS,
    AI_BIO_GENERATING_TEXTS,
    AI_BIO_RESULT_TEXTS,
    AI_BIO_ERROR_TEXTS,
    INTERESTS_MIN_ERROR_TEXTS,
    PHOTO_LIMIT_EXCEEDED_TEXTS,
    PHOTO_UPLOAD_SUCCESS_TEXTS,
    PHOTO_MIN_ERROR_TEXTS,
)

NEW_INTEREST_PROMPT_TEXTS = {
    "uz": "Yangi qiziqishingiz nomini kiriting (masalan, 'Dasturlash'):",
    "ru": "Введите название вашего нового интереса (например, 'Программирование'):",
    "en": "Enter the name of your new interest (e.g., 'Programming'):",
}

NEW_INTEREST_ADDED_TEXTS = {
    "uz": "✅ Yangi qiziqish qo'shildi va tanlandi. Yana qo'shishingiz yoki 'Tayyor' tugmasini bosishingiz mumkin.",
    "ru": "✅ Новый интерес добавлен и выбран. Можете добавить еще или нажать 'Готово'.",
    "en": "✅ New interest added and selected. You can add more or press 'Done'.",
}

NEW_INTEREST_EXISTS_TEXTS = {
    "uz": "Bu qiziqish allaqachon mavjud.",
    "ru": "Этот интерес уже существует.",
    "en": "This interest already exists.",
}

router = Router()

EDIT_FIELD_PROMPTS = {
    "uz": {
        "name": "Yangi ismingizni kiriting:",
        "age": "Yangi yoshingizni kiriting:",
        "bio": "O'zingiz haqingizda yangi ma'lumot kiriting (maksimum 500 belgi):",
        "city": "Yangi viloyatingizni tanlang:",
        "city_selection": "Yangi shahringizni tanlang:",
        "district": "Yangi tumaningizni tanlang:",
        "interests": "Qiziqishlaringizni qayta tanlang:",
        "photos": "Rasmlaringizni boshqarish:",
        "height": "Yangi bo'yingizni kiriting (sm):",
    },
    "ru": {
        "name": "Введите ваше новое имя:",
        "age": "Введите ваш новый возраст:",
        "bio": "Введите новую информацию о себе (максимум 500 символов):",
        "city": "Выберите ваш новый регион:",
        "city_selection": "Выберите ваш новый город:",
        "district": "Выберите ваш новый район:",
        "interests": "Выберите ваши интересы заново:",
        "photos": "Управление вашими фотографиями:",
        "height": "Введите ваш новый рост (см):",
    },
    "en": {
        "name": "Enter your new name:",
        "age": "Enter your new age:",
        "bio": "Enter a new bio about yourself (max 500 characters):",
        "city": "Select your new region:",
        "city_selection": "Select your new city:",
        "district": "Select your new district:",
        "interests": "Re-select your interests:",
        "photos": "Manage your photos:",
        "height": "Enter your new height (cm):",
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


@router.callback_query(StateFilter(EditingStates, MenuStates), F.data == "back_to_profile")
async def back_to_profile_view(callback: CallbackQuery, state: FSMContext):
    """Handles returning to the main profile view from any editing step."""
    await state.clear()
    # If there's a message with media, it might be better to delete and resend
    if callback.message.photo or callback.message.video or callback.message.document:
        await callback.message.delete()
        await show_my_profile(callback.message, state)
    else:
        # If it's just text, we can try to edit it to avoid flicker
        try:
            # This is a bit of a hack, we call show_my_profile just to get the text and keyboard
            # But we don't await it here. Instead, we manually edit the message.
            # This is a conceptual issue. Let's stick to delete and resend for simplicity and reliability.
            await callback.message.delete()
            await show_my_profile(callback.message, state)
        except Exception:
            # Fallback if editing fails
            await callback.message.delete()
            await show_my_profile(callback.message, state)
            
    await callback.answer()

@router.callback_query(StateFilter(
    EditingStates.editing_name, 
    EditingStates.editing_age, 
    EditingStates.editing_height,
    EditingStates.editing_bio,
    EditingStates.editing_city,
    EditingStates.editing_district,
    EditingStates.editing_interests,
    EditingStates.adding_new_interest,
    EditingStates.confirming_ai_bio
), F.data == "back_to_edit_menu")
async def back_to_edit_menu(callback: CallbackQuery, state: FSMContext):
    """Returns to the main edit menu from a specific field edit."""
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = user.language or "uz"

    await state.set_state(EditingStates.choosing_field)
    
    edit_menu_text = EDIT_PROFILE_TEXTS.get(language, EDIT_PROFILE_TEXTS["uz"])
    edit_menu_keyboard = get_edit_profile_keyboard(language)

    # If coming from a photo-based message, edit caption. Otherwise edit text.
    # A more robust way is to delete and resend to handle all cases.
    await callback.message.delete()
    await callback.message.answer(edit_menu_text, reply_markup=edit_menu_keyboard)
    await callback.answer()


# --- Generic Field Edit Start ---
async def start_field_edit(callback: CallbackQuery, state: FSMContext, field_name: str, new_state: State, keyboard=None):
    """Generic function to start editing a simple text field."""
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = user.language or "uz"
    await state.set_state(new_state)
    prompt = EDIT_FIELD_PROMPTS[language][field_name]
    
    reply_markup = keyboard if keyboard else get_back_only_keyboard(language, "back_to_edit_menu")

    # To avoid errors with editing a photo to text or vice-versa, just delete and send a new one.
    if callback.message.text:
         await callback.message.edit_text(prompt, reply_markup=reply_markup)
    else:
        await callback.message.delete()
        await callback.message.answer(prompt, reply_markup=reply_markup)
        
    await callback.answer()

@router.callback_query(EditingStates.choosing_field, F.data == "edit_field_name")
async def edit_name_start(callback: CallbackQuery, state: FSMContext):
    await start_field_edit(callback, state, "name", EditingStates.editing_name)

@router.callback_query(EditingStates.choosing_field, F.data == "edit_field_age")
async def edit_age_start(callback: CallbackQuery, state: FSMContext):
    await start_field_edit(callback, state, "age", EditingStates.editing_age)

@router.callback_query(EditingStates.choosing_field, F.data == "edit_field_height")
async def edit_height_start(callback: CallbackQuery, state: FSMContext):
    await start_field_edit(callback, state, "height", EditingStates.editing_height)


# --- Field Edit Finish Handlers ---

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
    await state.clear()
    await show_my_profile(message, state)

@router.message(EditingStates.editing_age, F.text)
async def edit_age_finish(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    language = user.language or "uz"

    if not message.text.isdigit():
        await message.answer(AGE_INVALID_TEXTS.get(language, AGE_INVALID_TEXTS["uz"]))
        return

    new_age = int(message.text)
    if new_age < 18:
        await message.answer(AGE_TOO_YOUNG_TEXTS.get(language, AGE_TOO_YOUNG_TEXTS["uz"]))
        return

    await update_user_profile_field(user.id, "age", new_age)
    await message.answer(FIELD_UPDATED_TEXTS[language])
    await state.clear()
    await show_my_profile(message, state)

@router.message(EditingStates.editing_height, F.text)
async def edit_height_finish(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    language = user.language or "uz"

    try:
        new_height = int(message.text.replace(",", "."))
        if not 100 <= new_height <= 250:
            raise ValueError
    except (ValueError, TypeError):
        await message.answer(HEIGHT_INVALID_TEXTS.get(language, HEIGHT_INVALID_TEXTS["uz"]))
        return

    await update_user_profile_field(user.id, "height", new_height)
    await message.answer(FIELD_UPDATED_TEXTS[language])
    await state.clear()
    await show_my_profile(message, state)


# --- Edit Bio ---
@router.callback_query(EditingStates.choosing_field, F.data == "edit_field_bio")
async def edit_bio_start(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = user.language or "uz"
    keyboard = get_bio_request_keyboard(language, back_callback="back_to_edit_menu")
    await start_field_edit(callback, state, "bio", EditingStates.editing_bio, keyboard)

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
    await state.clear()
    await show_my_profile(message, state)

@router.callback_query(EditingStates.editing_bio, F.data == "generate_bio_ai")
async def edit_generate_bio_handler(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = user.language or "uz"

    await callback.message.edit_text(AI_BIO_GENERATING_TEXTS.get(language, AI_BIO_GENERATING_TEXTS["uz"]))
    await callback.answer()

    interest_keys = user.interests.split(',') if user.interests else []
    interest_names = [ALL_INTERESTS[key].get(language, ALL_INTERESTS[key]['uz']) for key in interest_keys if key in ALL_INTERESTS]
    ai_user_data = { "name": user.name, "age": user.age, "city": user.city, "interests_names": interest_names, "height": user.height }
    generated_bio = await generate_bio_with_ai(ai_user_data, language)

    if not generated_bio or "Afsuski" in generated_bio:
        await callback.message.edit_text(
            generated_bio or AI_BIO_ERROR_TEXTS.get(language, AI_BIO_ERROR_TEXTS["uz"]),
            reply_markup=get_bio_request_keyboard(language, "back_to_edit_menu")
        )
        await state.set_state(EditingStates.editing_bio)
        return

    await state.update_data(generated_bio=generated_bio)
    await state.set_state(EditingStates.confirming_ai_bio)

    await callback.message.edit_text(
        f"<i>{generated_bio}</i>\n\n{AI_BIO_RESULT_TEXTS.get(language, AI_BIO_RESULT_TEXTS['uz'])}",
        reply_markup=get_ai_bio_confirmation_keyboard(language, back_callback="back_to_edit_menu")
    )

@router.callback_query(EditingStates.confirming_ai_bio, F.data == "ai_bio_regenerate")
async def edit_regenerate_bio_handler(callback: CallbackQuery, state: FSMContext):
    await edit_generate_bio_handler(callback, state)

@router.callback_query(EditingStates.confirming_ai_bio, F.data == "ai_bio_accept")
async def accept_ai_bio_for_edit_handler(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = user.language or "uz"
    data = await state.get_data()
    generated_bio = data.get("generated_bio")

    await update_user_profile_field(user.id, "bio", generated_bio)
    await callback.message.delete()
    await callback.message.answer(FIELD_UPDATED_TEXTS[language])
    await state.clear()
    await show_my_profile(callback.message, state)
    await callback.answer()

# --- Edit City/District ---
@router.callback_query(EditingStates.choosing_field, F.data == "edit_field_city")
async def edit_city_start(callback: CallbackQuery, state: FSMContext):
    keyboard = get_region_keyboard(callback.from_user.language_code, back_callback="back_to_edit_menu")
    await start_field_edit(callback, state, "city", EditingStates.editing_city, keyboard)

@router.callback_query(EditingStates.editing_city, F.data.startswith("region_"))
async def edit_region_selected(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = user.language or "uz"
    region_name = resolve_region_name(callback.data.split("_", 1)[1])
    await state.update_data(edit_region=region_name)

    back_cb = "edit_field_city" # Special back callback to go to region selection
    if is_tashkent_city_region(region_name):
        await state.set_state(EditingStates.editing_district)
        prompt = EDIT_FIELD_PROMPTS[language]["district"]
        keyboard = get_district_keyboard(region_name, language, back_callback=back_cb)
    else:
        await state.set_state(EditingStates.editing_city) # Stay in city selection for city-based regions
        prompt = EDIT_FIELD_PROMPTS[language]["city_selection"]
        keyboard = get_city_keyboard(region_name, language, back_callback=back_cb)
    
    await callback.message.edit_text(prompt, reply_markup=keyboard)
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
    
    back_cb = f"region_{region_name.lower().replace(' ', '_')}" # Go back to city selection for this region
    await callback.message.edit_text(
        EDIT_FIELD_PROMPTS[language]["district"],
        reply_markup=get_district_keyboard(region_name, language, back_callback=back_cb),
    )
    await callback.answer()

@router.callback_query(EditingStates.editing_district, F.data.startswith("district_"))
async def edit_district_selected(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = user.language or "uz"
    district_name = callback.data.split("_", 1)[1].replace("_", " ").title()
    data = await state.get_data()
    city_name = data.get("edit_city") or data.get("edit_region") # For Tashkent City

    await update_user_profile_field(user.id, "city", city_name)
    await update_user_profile_field(user.id, "district", district_name)

    await callback.message.delete()
    await callback.message.answer(FIELD_UPDATED_TEXTS[language])
    await state.clear()
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
    await callback.message.answer(
        EDIT_FIELD_PROMPTS[language]["interests"],
        reply_markup=get_interests_keyboard(language, current_interests, back_callback="back_to_profile"),
    )
    await callback.answer()

@router.callback_query(EditingStates.editing_interests, F.data.startswith("interest_"))
async def edit_interest_selected(callback: CallbackQuery, state: FSMContext):
    interest_key = callback.data.split("_", 1)[1]
    data = await state.get_data()
    language = (await get_user_by_telegram_id(callback.from_user.id)).language or "uz"
    selected_interests = data.get("edit_interests", [])

    if interest_key in selected_interests:
        selected_interests.remove(interest_key)
    else:
        selected_interests.append(interest_key)

    await state.update_data(edit_interests=selected_interests)
    await callback.message.edit_reply_markup(
        reply_markup=get_interests_keyboard(language, selected_interests, back_callback="back_to_profile")
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

    await update_user_profile_field(user.id, "interests", ",".join(filter(None, selected_interests)))
    await callback.message.delete()
    await callback.message.answer(FIELD_UPDATED_TEXTS[language])
    await state.clear()
    await show_my_profile(callback.message, state)

@router.callback_query(EditingStates.editing_interests, F.data == "add_new_interest")
async def add_new_interest_start(callback: CallbackQuery, state: FSMContext):
    language = (await get_user_by_telegram_id(callback.from_user.id)).language or "uz"
    await state.set_state(EditingStates.adding_new_interest)
    await callback.message.edit_text(
        NEW_INTEREST_PROMPT_TEXTS.get(language, NEW_INTEREST_PROMPT_TEXTS["uz"]),
        reply_markup=get_back_only_keyboard(language, "back_to_edit_interests")
    )
    await callback.answer()

@router.callback_query(EditingStates.adding_new_interest, F.data == "back_to_edit_interests")
async def back_to_edit_interests_handler(callback: CallbackQuery, state: FSMContext):
    await edit_interests_start(callback, state) # Go back by re-triggering the start

@router.message(EditingStates.adding_new_interest, F.text)
async def add_new_interest_finish(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    language = user.language or "uz"
    new_interest_name = message.text.strip()
    
    if not (2 <= len(new_interest_name) <= 30):
        await message.answer("Qiziqish nomi 2 dan 30 gacha belgilardan iborat bo'lishi kerak.")
        return

    new_interest_key = new_interest_name.lower().replace(" ", "_")
    data = await state.get_data()
    selected_interests = data.get("edit_interests", [])

    if new_interest_key in ALL_INTERESTS or new_interest_key in selected_interests:
        await message.answer(NEW_INTEREST_EXISTS_TEXTS.get(language, NEW_INTEREST_EXISTS_TEXTS["uz"]))
        return

    selected_interests.append(new_interest_key)
    await state.update_data(edit_interests=selected_interests)
    await state.set_state(EditingStates.editing_interests)

    await message.answer(
        NEW_INTEREST_ADDED_TEXTS.get(language, NEW_INTEREST_ADDED_TEXTS["uz"]),
    )
    await message.answer(
        EDIT_FIELD_PROMPTS[language]["interests"],
        reply_markup=get_interests_keyboard(language, selected_interests, back_callback="back_to_profile")
    )


# --- Photo Management ---

async def show_photo_management_view(message: Message, state: FSMContext, user_id: int, photo_index: int = 0):
    user = await get_user_by_telegram_id(user_id)
    language = user.language or "uz"
    photos = await get_user_photos(user.id)

    # If user has no photos, jump straight to adding new ones
    if not photos:
        await state.set_state(EditingStates.adding_photo)
        prompt_text = "Sizda hali rasm yo'q. Iltimos, kamida bitta rasm yuboring (maksimum 5 ta)."
        # This message might have come from a callback, so delete first
        if isinstance(message, CallbackQuery):
            await message.message.delete()
            await message.message.answer(prompt_text, reply_markup=get_back_only_keyboard(language, "back_to_profile"))
        else:
            await message.answer(prompt_text, reply_markup=get_back_only_keyboard(language, "back_to_profile"))
        return

    photo_index = max(0, min(photo_index, len(photos) - 1))
    await state.update_data(photo_management_index=photo_index)

    current_photo = photos[photo_index]
    is_primary = current_photo.order == 1
    
    caption = (f"Rasm {photo_index + 1}/{len(photos)}\n"
               f"{'✅ Asosiy rasm' if is_primary else ''}\n"
               f"{'⏳ Moderatsiyada' if not current_photo.is_approved else '✅ Tasdiqlangan'}")

    keyboard = get_photo_management_keyboard(language, current_photo.id, photo_index, len(photos), is_primary)

    # If the current message is a text message, delete it and send a photo message.
    # If it's already a photo message, edit it.
    if isinstance(message, Message) and message.photo:
         await message.edit_media(media=InputMediaPhoto(media=current_photo.file_id, caption=caption), reply_markup=keyboard)
    else:
        # It's a callback query or a text message, delete and resend
        if isinstance(message, CallbackQuery):
            await message.message.delete()
            await message.message.answer_photo(photo=current_photo.file_id, caption=caption, reply_markup=keyboard)
        else:
            await message.delete()
            await message.answer_photo(photo=current_photo.file_id, caption=caption, reply_markup=keyboard)


@router.callback_query(EditingStates.choosing_field, F.data == "edit_field_photos")
async def edit_photos_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EditingStates.editing_photos)
    await show_photo_management_view(callback, state, callback.from_user.id)
    await callback.answer()

@router.callback_query(EditingStates.editing_photos, F.data.startswith("manage_photo_nav_"))
async def manage_photo_nav_handler(callback: CallbackQuery, state: FSMContext):
    direction = callback.data.split("_")[-1]
    data = await state.get_data()
    current_index = data.get("photo_management_index", 0)
    
    current_index += 1 if direction == "next" else -1
    
    await show_photo_management_view(callback, state, callback.from_user.id, photo_index=current_index)
    await callback.answer()

@router.callback_query(EditingStates.editing_photos, F.data.startswith("set_primary_"))
async def set_primary_photo_handler(callback: CallbackQuery, state: FSMContext):
    photo_id = int(callback.data.split("_")[-1])
    user = await get_user_by_telegram_id(callback.from_user.id)
    
    if await set_primary_photo(user.id, photo_id):
        await callback.answer("✅ Asosiy rasm o'zgartirildi.")
        data = await state.get_data()
        await show_photo_management_view(callback, state, user.id, photo_index=data.get("photo_management_index", 0))
    else:
        await callback.answer("❌ Xatolik yuz berdi.", show_alert=True)

@router.callback_query(EditingStates.editing_photos, F.data == "add_photo")
async def add_photo_start(callback: CallbackQuery, state: FSMContext):
    language = (await get_user_by_telegram_id(callback.from_user.id)).language or "uz"
    await state.set_state(EditingStates.adding_photo)
    await callback.message.delete()
    await callback.message.answer(
        "Yangi rasm yuboring (maksimum 5ta):",
        reply_markup=get_back_only_keyboard(language, "back_to_photo_management")
    )
    await callback.answer()

@router.message(EditingStates.adding_photo, F.photo)
async def add_photo_finish(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    language = user.language or "uz"
    
    if await add_photo(user.id, message.photo[-1].file_id):
        await message.answer(f"{PHOTO_UPLOAD_SUCCESS_TEXTS[language]}\n{PHOTOS_MODERATION_NOTICE[language]}")
    else:
        await message.answer(PHOTO_LIMIT_EXCEEDED_TEXTS[language])
        
    await state.set_state(EditingStates.editing_photos)
    photos = await get_user_photos(user.id)
    await show_photo_management_view(message, state, user.id, photo_index=len(photos)-1)

@router.callback_query(StateFilter(EditingStates.adding_photo, EditingStates.deleting_photo_confirmation), F.data == "back_to_photo_management")
async def back_to_photo_management_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EditingStates.editing_photos)
    data = await state.get_data()
    await show_photo_management_view(callback, state, callback.from_user.id, photo_index=data.get("photo_management_index", 0))
    await callback.answer()

@router.callback_query(EditingStates.editing_photos, F.data.startswith("delete_photo_prompt_"))
async def delete_photo_prompt_handler(callback: CallbackQuery, state: FSMContext):
    photo_id = int(callback.data.split("_")[-1])
    confirm_keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Ha, o'chirish", callback_data=f"delete_photo_confirm_{photo_id}"),
        InlineKeyboardButton(text="❌ Yo'q", callback_data="back_to_photo_management")
    ]])
    await state.set_state(EditingStates.deleting_photo_confirmation)
    await callback.message.edit_reply_markup(reply_markup=confirm_keyboard)
    await callback.answer("Shu rasmni o'chirishni tasdiqlaysizmi?")

@router.callback_query(EditingStates.deleting_photo_confirmation, F.data.startswith("delete_photo_confirm_"))
async def delete_photo_confirm_handler(callback: CallbackQuery, state: FSMContext):
    photo_id = int(callback.data.split("_")[-1])
    await state.set_state(EditingStates.editing_photos)
    if await delete_photo(photo_id):
        await callback.answer("🗑 Rasm o'chirildi.")
        await show_photo_management_view(callback, state, callback.from_user.id, photo_index=0)
    else:
        await callback.answer("❌ Yagona rasmni o'chirib bo'lmaydi.", show_alert=True)
        data = await state.get_data()
        await show_photo_management_view(callback, state, callback.from_user.id, photo_index=data.get("photo_management_index", 0))
