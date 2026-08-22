import logging
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InputMediaPhoto, ReplyKeyboardRemove

from states import RegistrationStates, EditingStates
from inline import (
    get_language_keyboard,
    get_terms_keyboard,
    get_back_keyboard,
    get_age_selection_keyboard,
    get_gender_keyboard,
    get_height_selection_keyboard,
    get_looking_for_keyboard,
    get_intent_keyboard,
    get_regions_keyboard,
    get_districts_keyboard,
    get_interests_keyboard,
    get_bio_prompt_keyboard,
    get_photo_upload_done_keyboard,
    get_review_keyboard,
    get_admin_verification_keyboard,
    ALL_INTERESTS,
    UZBEK_REGIONS,
)
from reply import get_main_menu_keyboard
from i18n import t
from crud import create_user_profile, get_user_by_telegram_id, get_user_photos
from config import ADMIN_IDS

router = Router()

# =========================================================================
# 1. CANCEL HANDLER
# =========================================================================
@router.message(Command("cancel"), RegistrationStates())
async def cancel_registration(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Ro'yxatdan o'tish bekor qilindi. Qaytadan boshlash uchun /start bosing.")

# =========================================================================
# 2. LANGUAGE SELECTION
# =========================================================================
@router.callback_query(RegistrationStates.choosing_language, F.data.startswith("lang_"))
async def language_chosen(callback: CallbackQuery, state: FSMContext):
    lang = callback.data.split("_")[1] # uz, ru, en
    await state.update_data(language=lang)
    await state.set_state(RegistrationStates.accepting_terms)
    
    await callback.message.edit_text(
        text=t("terms_title", lang),
        reply_markup=get_terms_keyboard(lang),
        parse_mode="HTML"
    )
    await callback.answer()

# =========================================================================
# 3. TERMS & CONDITIONS
# =========================================================================
@router.callback_query(RegistrationStates.accepting_terms, F.data == "reg_back_language")
async def back_to_language(callback: CallbackQuery, state: FSMContext):
    await state.set_state(RegistrationStates.choosing_language)
    await callback.message.edit_text(
        text=t("choose_language", "uz"),
        reply_markup=get_language_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(RegistrationStates.accepting_terms, F.data == "accept_terms")
async def terms_accepted(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "uz")
    await state.update_data(terms_accepted=True)
    await state.set_state(RegistrationStates.entering_name)

    await callback.message.edit_text(
        text=t("ask_name", lang),
        reply_markup=get_back_keyboard("reg_back_terms", lang),
        parse_mode="HTML"
    )
    await callback.answer()

# =========================================================================
# 4. NAME (FREE TEXT)
# =========================================================================
@router.callback_query(RegistrationStates.entering_name, F.data == "reg_back_terms")
async def back_to_terms(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "uz")
    await state.set_state(RegistrationStates.accepting_terms)
    await callback.message.edit_text(
        text=t("terms_title", lang),
        reply_markup=get_terms_keyboard(lang),
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(RegistrationStates.entering_name, F.text)
async def name_entered(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "uz")
    name = message.text.strip()
    
    if len(name) < 2 or len(name) > 30:
        await message.answer(
            text=t("invalid_name", lang),
            reply_markup=get_back_keyboard("reg_back_terms", lang),
            parse_mode="HTML"
        )
        return

    await state.update_data(name=name)
    await state.set_state(RegistrationStates.entering_age)
    
    await message.answer(
        text=t("ask_age", lang),
        reply_markup=get_age_selection_keyboard(lang, page=0),
        parse_mode="HTML"
    )

# =========================================================================
# 5. AGE SELECTION (INLINE BUTTONS)
# =========================================================================
@router.callback_query(RegistrationStates.entering_age, F.data == "reg_back_name")
async def back_to_name(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "uz")
    await state.set_state(RegistrationStates.entering_name)
    await callback.message.edit_text(
        text=t("ask_name", lang),
        reply_markup=get_back_keyboard("reg_back_terms", lang),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(RegistrationStates.entering_age, F.data.startswith("agepage_"))
async def age_page_changed(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "uz")
    page = int(callback.data.split("_")[1])
    await callback.message.edit_reply_markup(
        reply_markup=get_age_selection_keyboard(lang, page=page)
    )
    await callback.answer()

@router.callback_query(RegistrationStates.entering_age, F.data.startswith("age_"))
async def age_selected(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "uz")
    age = int(callback.data.split("_")[1])
    
    await state.update_data(age=age)
    await state.set_state(RegistrationStates.choosing_gender)
    
    await callback.message.edit_text(
        text=t("ask_gender", lang),
        reply_markup=get_gender_keyboard(lang),
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(RegistrationStates.entering_age, F.text)
async def age_text_entered(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "uz")
    try:
        age = int(message.text.strip())
        if age < 18 or age > 99:
            await message.answer(t("invalid_age", lang), reply_markup=get_age_selection_keyboard(lang, 0))
            return
    except ValueError:
        await message.answer(t("invalid_age", lang), reply_markup=get_age_selection_keyboard(lang, 0))
        return

    await state.update_data(age=age)
    await state.set_state(RegistrationStates.choosing_gender)
    await message.answer(
        text=t("ask_gender", lang),
        reply_markup=get_gender_keyboard(lang),
        parse_mode="HTML"
    )

# =========================================================================
# 6. GENDER SELECTION (INLINE BUTTONS)
# =========================================================================
@router.callback_query(RegistrationStates.choosing_gender, F.data == "reg_back_age")
async def back_to_age(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "uz")
    await state.set_state(RegistrationStates.entering_age)
    await callback.message.edit_text(
        text=t("ask_age", lang),
        reply_markup=get_age_selection_keyboard(lang, page=0),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(RegistrationStates.choosing_gender, F.data.startswith("gender_"))
async def gender_chosen(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "uz")
    gender = callback.data.split("_")[1] # MALE, FEMALE, OTHER
    
    await state.update_data(gender=gender)
    await state.set_state(RegistrationStates.entering_height)
    
    await callback.message.edit_text(
        text=t("ask_height", lang),
        reply_markup=get_height_selection_keyboard(lang),
        parse_mode="HTML"
    )
    await callback.answer()

# =========================================================================
# 7. HEIGHT SELECTION (INLINE BUTTONS)
# =========================================================================
@router.callback_query(RegistrationStates.entering_height, F.data == "reg_back_gender")
async def back_to_gender(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "uz")
    await state.set_state(RegistrationStates.choosing_gender)
    await callback.message.edit_text(
        text=t("ask_gender", lang),
        reply_markup=get_gender_keyboard(lang),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(RegistrationStates.entering_height, F.data.startswith("height_"))
async def height_selected(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "uz")
    h_val = callback.data.split("_")[1]
    
    height_num = None
    if h_val != "skip":
        if "-" in h_val:
            parts = h_val.split("-")
            height_num = (int(parts[0]) + int(parts[1])) // 2
        else:
            try:
                height_num = int(h_val)
            except ValueError:
                height_num = None

    await state.update_data(height=height_num)
    await state.set_state(RegistrationStates.choosing_looking_for)
    
    await callback.message.edit_text(
        text=t("ask_looking_for", lang),
        reply_markup=get_looking_for_keyboard(lang),
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(RegistrationStates.entering_height, F.text)
async def height_text_entered(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "uz")
    try:
        h = int(message.text.strip())
        if 100 <= h <= 250:
            await state.update_data(height=h)
    except ValueError:
        pass

    await state.set_state(RegistrationStates.choosing_looking_for)
    await message.answer(
        text=t("ask_looking_for", lang),
        reply_markup=get_looking_for_keyboard(lang),
        parse_mode="HTML"
    )

# =========================================================================
# 8. LOOKING FOR SELECTION (INLINE BUTTONS)
# =========================================================================
@router.callback_query(RegistrationStates.choosing_looking_for, F.data == "reg_back_height")
async def back_to_height(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "uz")
    await state.set_state(RegistrationStates.entering_height)
    await callback.message.edit_text(
        text=t("ask_height", lang),
        reply_markup=get_height_selection_keyboard(lang),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(RegistrationStates.choosing_looking_for, F.data.startswith("looking_for_"))
async def looking_for_chosen(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "uz")
    target = callback.data.split("_")[2] # FEMALE, MALE, ANY
    
    await state.update_data(looking_for=target)
    await state.set_state(RegistrationStates.choosing_intent)
    
    await callback.message.edit_text(
        text=t("ask_intent", lang),
        reply_markup=get_intent_keyboard(lang),
        parse_mode="HTML"
    )
    await callback.answer()

# =========================================================================
# 9. DATING GOAL / INTENT SELECTION (INLINE BUTTONS)
# =========================================================================
@router.callback_query(RegistrationStates.choosing_intent, F.data == "reg_back_looking_for")
async def back_to_looking_for(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "uz")
    await state.set_state(RegistrationStates.choosing_looking_for)
    await callback.message.edit_text(
        text=t("ask_looking_for", lang),
        reply_markup=get_looking_for_keyboard(lang),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(RegistrationStates.choosing_intent, F.data.startswith("intent_"))
async def intent_chosen(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "uz")
    intent_val = callback.data.replace("intent_", "")
    
    await state.update_data(relationship_intent=intent_val)
    await state.set_state(RegistrationStates.entering_city)
    
    await callback.message.edit_text(
        text=t("ask_region", lang),
        reply_markup=get_regions_keyboard(lang),
        parse_mode="HTML"
    )
    await callback.answer()

# =========================================================================
# 10. REGION & DISTRICT SELECTION (INLINE BUTTONS)
# =========================================================================
@router.callback_query(RegistrationStates.entering_city, F.data == "reg_back_intent")
async def back_to_intent(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "uz")
    await state.set_state(RegistrationStates.choosing_intent)
    await callback.message.edit_text(
        text=t("ask_intent", lang),
        reply_markup=get_intent_keyboard(lang),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(RegistrationStates.entering_city, F.data.startswith("region_"))
async def region_selected(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "uz")
    region_name = callback.data.replace("region_", "")
    
    await state.update_data(city=region_name, region=region_name)
    await state.set_state(RegistrationStates.entering_district)
    
    await callback.message.edit_text(
        text=t("ask_district", lang, region=region_name),
        reply_markup=get_districts_keyboard(region_name, lang),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(RegistrationStates.entering_district, F.data == "reg_back_region")
async def back_to_region(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "uz")
    await state.set_state(RegistrationStates.entering_city)
    await callback.message.edit_text(
        text=t("ask_region", lang),
        reply_markup=get_regions_keyboard(lang),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(RegistrationStates.entering_district, F.data.startswith("district_"))
async def district_selected(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "uz")
    district_name = callback.data.replace("district_", "")
    
    await state.update_data(district=district_name, interests=[])
    await state.set_state(RegistrationStates.choosing_interests)
    
    await callback.message.edit_text(
        text=t("ask_interests", lang),
        reply_markup=get_interests_keyboard(lang, selected_interests=[]),
        parse_mode="HTML"
    )
    await callback.answer()

# =========================================================================
# 11. INTERESTS MULTI-SELECT (INLINE BUTTONS)
# =========================================================================
@router.callback_query(RegistrationStates.choosing_interests, F.data == "reg_back_district")
async def back_to_district(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "uz")
    region_name = data.get("city", "Toshkent shahri")
    await state.set_state(RegistrationStates.entering_district)
    await callback.message.edit_text(
        text=t("ask_district", lang, region=region_name),
        reply_markup=get_districts_keyboard(region_name, lang),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(RegistrationStates.choosing_interests, F.data.startswith("interest_"))
async def interest_toggled(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "uz")
    interest_key = callback.data.replace("interest_", "")
    
    selected = data.get("interests", [])
    if interest_key in selected:
        selected.remove(interest_key)
    else:
        selected.append(interest_key)
        
    await state.update_data(interests=selected)
    await callback.message.edit_reply_markup(
        reply_markup=get_interests_keyboard(lang, selected_interests=selected)
    )
    await callback.answer()

@router.callback_query(RegistrationStates.choosing_interests, F.data == "interests_done")
async def interests_done(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "uz")
    
    await state.set_state(RegistrationStates.entering_bio)
    await callback.message.edit_text(
        text=t("ask_bio", lang),
        reply_markup=get_bio_prompt_keyboard(lang),
        parse_mode="HTML"
    )
    await callback.answer()

# =========================================================================
# 12. BIO (FREE TEXT OR AI GENERATION)
# =========================================================================
@router.callback_query(RegistrationStates.entering_bio, F.data == "reg_back_interests")
async def back_to_interests(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "uz")
    selected = data.get("interests", [])
    await state.set_state(RegistrationStates.choosing_interests)
    await callback.message.edit_text(
        text=t("ask_interests", lang),
        reply_markup=get_interests_keyboard(lang, selected_interests=selected),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(RegistrationStates.entering_bio, F.data == "generate_bio_ai")
async def generate_bio_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "uz")
    
    from ai import generate_dating_bio
    await callback.answer("✨ AI bio tayyorlamoqda...")
    
    name = data.get("name", "User")
    age = data.get("age", 20)
    interests = data.get("interests", [])
    intent = data.get("relationship_intent", "serious")
    
    generated_bio = await generate_dating_bio(name=name, age=age, interests=interests, intent=intent, lang=lang)
    await state.update_data(bio=generated_bio)
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    ai_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Shu bio ma'qul", callback_data="ai_bio_accept")],
        [InlineKeyboardButton(text="🔄 Boshqa variant", callback_data="generate_bio_ai")],
        [InlineKeyboardButton(text=t("btn_back", lang), callback_data="reg_back_interests")],
    ])
    
    await callback.message.edit_text(
        text=f"✨ <b>AI tomonidan yaratilgan bio:</b>\n\n<i>\"{generated_bio}\"</i>",
        reply_markup=ai_kb,
        parse_mode="HTML"
    )

@router.callback_query(RegistrationStates.entering_bio, F.data == "ai_bio_accept")
async def accept_ai_bio_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "uz")
    await state.set_state(RegistrationStates.uploading_photos)
    await state.update_data(photos=[])
    
    await callback.message.edit_text(
        text=t("ask_photo", lang),
        reply_markup=get_back_keyboard("reg_back_bio", lang),
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(RegistrationStates.entering_bio, F.text)
async def bio_entered(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "uz")
    bio = message.text.strip()
    
    await state.update_data(bio=bio, photos=[])
    await state.set_state(RegistrationStates.uploading_photos)
    
    await message.answer(
        text=t("ask_photo", lang),
        reply_markup=get_back_keyboard("reg_back_bio", lang),
        parse_mode="HTML"
    )

# =========================================================================
# 13. PHOTO UPLOADING
# =========================================================================
@router.callback_query(RegistrationStates.uploading_photos, F.data == "reg_back_bio")
async def back_to_bio(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "uz")
    await state.set_state(RegistrationStates.entering_bio)
    await callback.message.edit_text(
        text=t("ask_bio", lang),
        reply_markup=get_bio_prompt_keyboard(lang),
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(RegistrationStates.uploading_photos, F.photo)
async def photo_uploaded(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "uz")
    
    file_id = message.photo[-1].file_id
    photos = data.get("photos", [])
    photos.append(file_id)
    await state.update_data(photos=photos)
    
    await message.answer(
        text=t("photo_uploaded", lang),
        reply_markup=get_photo_upload_done_keyboard(lang, count=len(photos)),
        parse_mode="HTML"
    )

# =========================================================================
# 14. PROFILE REVIEW & INSTANT ACCESS
# =========================================================================
@router.callback_query(RegistrationStates.uploading_photos, F.data == "photos_done")
async def photos_done(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "uz")
    photos = data.get("photos", [])
    
    if not photos:
        await callback.answer("Iltimos, kamida bitta fotosurat yuboring.", show_alert=True)
        return
        
    await state.set_state(RegistrationStates.reviewing_profile)
    
    # Format TashDate style profile card
    interest_labels = [ALL_INTERESTS[k].get(lang, k) for k in data.get("interests", []) if k in ALL_INTERESTS]
    district_str = f", {data.get('district')}" if data.get("district") else ""
    height_str = f"{data.get('height')} sm" if data.get("height") else "-"
    
    card_caption = t(
        "profile_card",
        lang,
        name=data.get("name"),
        badge="",
        age=data.get("age"),
        city=data.get("city"),
        district_text=district_str,
        height_text=height_str,
        intent_text=t(f"intent_{data.get('relationship_intent', 'serious').lower()}", lang) if f"intent_{data.get('relationship_intent', 'serious').lower()}" in t.__globals__["MESSAGES"] else data.get("relationship_intent", "-"),
        interests_text=", ".join(interest_labels) if interest_labels else "-",
        bio=data.get("bio", "-")
    )
    
    await callback.message.delete()
    await callback.message.answer_photo(
        photo=photos[0],
        caption=f"{t('profile_preview_title', lang)}\n\n{card_caption}",
        reply_markup=get_review_keyboard(lang),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(RegistrationStates.reviewing_profile, F.data == "confirm_profile")
async def profile_confirmed(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    lang = data.get("language", "uz")
    telegram_id = callback.from_user.id
    
    # 1. Create / activate user profile in database with instant active access
    new_user = await create_user_profile(telegram_id, data)
    await state.clear()
    
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer()
    
    # 2. Immediately send success text & Main Menu reply keyboard (NO WAITING FOR ADMIN!)
    await callback.message.answer(
        text=t("registration_success", lang),
        reply_markup=get_main_menu_keyboard(lang),
        parse_mode="HTML"
    )
    
    # 3. Post-moderation: Notify admins in background with verification buttons
    if new_user:
        await notify_admins_about_new_profile(bot, new_user.id, data, lang)

@router.callback_query(RegistrationStates.reviewing_profile, F.data == "edit_profile")
async def profile_edit(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "uz")
    await state.set_state(RegistrationStates.entering_name)
    await callback.message.delete()
    await callback.message.answer(
        text=t("ask_name", lang),
        reply_markup=get_back_keyboard("reg_back_terms", lang),
        parse_mode="HTML"
    )
    await callback.answer()

# =========================================================================
# 15. ADMIN POST-MODERATION NOTIFICATION (TASK 3)
# =========================================================================
async def notify_admins_about_new_profile(bot: Bot, user_id: int, user_data: dict, lang: str):
    """Adminlarga yangi profil haqida post-moderatsiya xabarini yuboradi (Verifikatsiya nishoni uchun)."""
    photos = user_data.get("photos", [])
    first_photo = photos[0] if photos else None
    
    notice_text = t(
        "admin_new_profile_notice",
        "uz",
        name=user_data.get("name"),
        user_id=user_id,
        age=user_data.get("age"),
        city=user_data.get("city"),
        district=user_data.get("district", "-"),
        gender=user_data.get("gender"),
        looking_for=user_data.get("looking_for"),
        intent=user_data.get("relationship_intent", "-"),
        bio=user_data.get("bio", "-"),
        lang=user_data.get("language", "uz"),
        telegram_id=user_data.get("telegram_id") or "-"
    )
    
    keyboard = get_admin_verification_keyboard(user_id, "uz")
    
    for admin_id in ADMIN_IDS:
        try:
            if first_photo:
                await bot.send_photo(
                    chat_id=admin_id,
                    photo=first_photo,
                    caption=notice_text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            else:
                await bot.send_message(
                    chat_id=admin_id,
                    text=notice_text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
        except Exception as exc:
            logging.warning(f"Failed to notify admin {admin_id}: {exc}")
