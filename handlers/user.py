from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup

import config
import database as db
import keyboards as kb
from states import Registration
from utils import check_subscription

router = Router()


# ---------------------------------------------------------------------------
# /start
# ---------------------------------------------------------------------------

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    await show_start_menu(
        bot=bot,
        state=state,
        chat_id=message.chat.id,
        user_id=message.from_user.id,
        username=message.from_user.username or "",
        full_name=message.from_user.full_name or "",
        first_name=message.from_user.first_name or "",
    )


async def show_start_menu(bot: Bot, state: FSMContext, chat_id: int, user_id: int,
                           username: str, full_name: str, first_name: str):
    await state.clear()
    user = await db.get_user(user_id)

    if user and user["is_banned"]:
        await bot.send_message(chat_id, f"🚫 <b>Siz {config.BOT_NAME}dan foydalanish huquqidan mahrum qilingansiz.</b>")
        return

    if not await check_subscription(bot, user_id):
        channel = await db.get_setting("required_channel")
        await bot.send_message(
            chat_id,
            "📢 <b>Botdan foydalanish uchun quyidagi kanalga a'zo bo'ling</b>, "
            "so'ng \"Tekshirish\" tugmasini bosing:",
            reply_markup=kb.subscribe_kb(channel),
        )
        return

    if user and user["is_complete"]:
        await bot.send_message(
            chat_id,
            f"✅ <b>{config.BOT_NAME}ga xush kelibsiz, {first_name}!</b>\n\n"
            "Siz allaqachon ro'yxatdan o'tgansiz.",
            reply_markup=kb.main_menu_kb(),
        )
        return

    await start_registration_by_id(bot, state, chat_id, user_id, username, full_name)


async def start_registration_by_id(bot: Bot, state: FSMContext, chat_id: int,
                                    user_id: int, username: str, full_name: str):
    await db.create_or_reset_user(user_id, username, full_name)
    await state.set_state(Registration.gender)
    await bot.send_message(
        chat_id,
        f"💘 <b>{config.BOT_NAME}ga xush kelibsiz!</b>\n\n"
        "Bu yerda yangi do'stlar bilan tanishishingiz mumkin. "
        "Avval qisqacha anketa to'ldiramiz.\n\n"
        "<b>1-qadam.</b> Jinsingizni tanlang:",
        reply_markup=kb.gender_kb(),
    )


@router.callback_query(F.data == "check_sub")
async def cb_check_sub(callback: CallbackQuery, state: FSMContext, bot: Bot):
    if not await check_subscription(bot, callback.from_user.id):
        await callback.answer("❌ Siz hali kanalga a'zo bo'lmadingiz.", show_alert=True)
        return
    await callback.answer("✅ Rahmat!")
    await callback.message.delete()
    await show_start_menu(
        bot=bot,
        state=state,
        chat_id=callback.message.chat.id,
        user_id=callback.from_user.id,
        username=callback.from_user.username or "",
        full_name=callback.from_user.full_name or "",
        first_name=callback.from_user.first_name or "",
    )


@router.callback_query(F.data == "restart_reg")
async def cb_restart(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await callback.answer()
    await start_registration_by_id(
        bot=bot,
        state=state,
        chat_id=callback.message.chat.id,
        user_id=callback.from_user.id,
        username=callback.from_user.username or "",
        full_name=callback.from_user.full_name or "",
    )


@router.callback_query(F.data == "my_profile")
async def cb_my_profile(callback: CallbackQuery):
    await callback.answer()
    await send_profile_card(callback.message, callback.from_user.id)


async def send_profile_card(message: Message, telegram_id: int):
    user = await db.get_user(telegram_id)

    if not user or not user["is_complete"]:
        await message.answer("Profil topilmadi.")
        return

    photos = await db.get_photos(telegram_id)

    caption = (
        f"👤 <b>{user['full_name']}</b>\n\n"
        f"🚻 Jinsi: <b>{user['gender']}</b>\n"
        f"🎂 Yoshi: <b>{user['age']}</b>\n"
        f"📏 Bo'yi: <b>{user['height']} sm</b>\n"
        f"⚖️ Vazni: <b>{user['weight']} kg</b>\n"
        f"📍 Manzil: <b>{user['region']}, {user['district']}</b>\n\n"
        f"💬 <i>{user['bio']}</i>"
    )

    if photos:
        await message.answer_photo(
            photo=photos[0],
            caption=caption,
            reply_markup=kb.profile_kb(telegram_id)
        )
    else:
        await message.answer(
            caption,
            reply_markup=kb.profile_kb(telegram_id)
        )
    

# ---------------------------------------------------------------------------
# Ro'yxatdan o'tish bosqichlari
# ---------------------------------------------------------------------------

@router.callback_query(Registration.gender, F.data.startswith("gender:"))
async def reg_gender(callback: CallbackQuery, state: FSMContext):
    gender = callback.data.split(":", 1)[1]
    await db.update_user_field(callback.from_user.id, "gender", gender)
    await state.set_state(Registration.phone)
    await callback.answer()
    await callback.message.edit_text(f"Jinsi: <b>{gender}</b> ✅")
    await callback.message.answer(
        "<b>2-qadam.</b> Telefon raqamingizni yuboring.\n"
        "Pastdagi tugmani bosing 👇",
        reply_markup=kb.phone_kb(),
    )


@router.message(Registration.phone, F.contact)
async def reg_phone(message: Message, state: FSMContext):
    if message.contact.user_id != message.from_user.id:
        await message.answer("⚠️ Iltimos, <b>o'zingizning</b> raqamingizni yuboring.")
        return
    await db.update_user_field(message.from_user.id, "phone", message.contact.phone_number)
    await state.set_state(Registration.region)
    await message.answer("Raqam qabul qilindi ✅", reply_markup=kb.remove_kb())
    await message.answer(
        "<b>3-qadam.</b> Yashash viloyatingizni tanlang:",
        reply_markup=kb.region_kb(),
    )


@router.message(Registration.phone)
async def reg_phone_invalid(message: Message):
    await message.answer(
        "⚠️ Iltimos, telefon raqamingizni faqat <b>\"📱 Raqamimni yuborish\"</b> "
        "tugmasi orqali yuboring."
    )


@router.callback_query(Registration.region, F.data.startswith("region:"))
async def reg_region(callback: CallbackQuery, state: FSMContext):
    region = callback.data.split(":", 1)[1]
    await db.update_user_field(callback.from_user.id, "region", region)
    await state.set_state(Registration.district)
    await callback.answer()
    await callback.message.edit_text(
        f"Viloyat: <b>{region}</b> ✅\n\n"
        "<b>4-qadam.</b> Tuman/shahringizni tanlang:",
        reply_markup=kb.district_kb(region),
    )


@router.callback_query(Registration.district, F.data == "back_to_region")
async def reg_back_to_region(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Registration.region)
    await callback.answer()
    await callback.message.edit_text(
        "<b>3-qadam.</b> Yashash viloyatingizni tanlang:",
        reply_markup=kb.region_kb(),
    )


@router.callback_query(Registration.district, F.data.startswith("district:"))
async def reg_district(callback: CallbackQuery, state: FSMContext):
    district = callback.data.split(":", 1)[1]
    await db.update_user_field(callback.from_user.id, "district", district)
    await state.set_state(Registration.age)
    await callback.answer()
    await callback.message.edit_text(f"Manzil: <b>{district}</b> ✅")
    await callback.message.answer("<b>5-qadam.</b> Yoshingizni raqamda kiriting (masalan: 24):")


@router.message(Registration.age)
async def reg_age(message: Message, state: FSMContext):
    text = message.text.strip() if message.text else ""
    if not text.isdigit():
        await message.answer("⚠️ Iltimos, yoshingizni faqat raqamda kiriting (masalan: 24).")
        return
    age = int(text)
    if age < config.MIN_AGE:
        await state.clear()
        await message.answer(
            f"🚫 Kechirasiz, botdan faqat <b>{config.MIN_AGE} yosh</b>dan katta "
            "foydalanuvchilar ro'yxatdan o'ta oladi."
        )
        return
    if age > config.MAX_AGE:
        await message.answer(f"⚠️ Yoshni {config.MIN_AGE}-{config.MAX_AGE} oralig'ida kiriting.")
        return
    await db.update_user_field(message.from_user.id, "age", age)
    await state.set_state(Registration.height)
    await message.answer("<b>6-qadam.</b> Bo'yingizni sm da kiriting (masalan: 175):")


@router.message(Registration.height)
async def reg_height(message: Message, state: FSMContext):
    text = message.text.strip() if message.text else ""
    if not text.isdigit() or not (config.MIN_HEIGHT <= int(text) <= config.MAX_HEIGHT):
        await message.answer(
            f"⚠️ Iltimos, bo'yingizni {config.MIN_HEIGHT}-{config.MAX_HEIGHT} sm "
            "oralig'ida, faqat raqamda kiriting."
        )
        return
    await db.update_user_field(message.from_user.id, "height", int(text))
    await state.set_state(Registration.weight)
    await message.answer("<b>7-qadam.</b> Vazningizni kg da kiriting (masalan: 65):")


@router.message(Registration.weight)
async def reg_weight(message: Message, state: FSMContext):
    text = message.text.strip() if message.text else ""
    if not text.isdigit() or not (config.MIN_WEIGHT <= int(text) <= config.MAX_WEIGHT):
        await message.answer(
            f"⚠️ Iltimos, vazningizni {config.MIN_WEIGHT}-{config.MAX_WEIGHT} kg "
            "oralig'ida, faqat raqamda kiriting."
        )
        return
    await db.update_user_field(message.from_user.id, "weight", int(text))
    await state.set_state(Registration.photos)
    await message.answer(
        f"<b>8-qadam.</b> Kamida <b>{config.MIN_PHOTOS} ta</b> rasm yuboring "
        f"(ko'pi bilan {config.MAX_PHOTOS} ta)."
    )


@router.message(Registration.photos, F.photo)
async def reg_photo(message: Message, state: FSMContext):
    count = await db.count_photos(message.from_user.id)
    if count >= config.MAX_PHOTOS:
        await message.answer(
            f"Siz allaqachon {config.MAX_PHOTOS} ta rasm yubordingiz. Davom eting 👇",
            reply_markup=kb.photos_done_kb(),
        )
        return

    await db.add_photo(message.from_user.id, message.photo[-1].file_id)
    count += 1

    if count < config.MIN_PHOTOS:
        left = config.MIN_PHOTOS - count
        await message.answer(f"Rasm qabul qilindi ✅ ({count}/{config.MIN_PHOTOS}). Yana {left} ta rasm yuboring.")
    elif count < config.MAX_PHOTOS:
        await message.answer(
            f"Rasm qabul qilindi ✅ ({count}/{config.MAX_PHOTOS}). "
            "Yana rasm yuborishingiz mumkin yoki davom eting 👇",
            reply_markup=kb.photos_done_kb(),
        )
    else:
        await message.answer(
            f"Rasm qabul qilindi ✅ ({count}/{config.MAX_PHOTOS}). Endi davom etamiz 👇",
            reply_markup=kb.photos_done_kb(),
        )


@router.message(Registration.photos)
async def reg_photo_invalid(message: Message):
    count = await db.count_photos(message.from_user.id)
    if count >= config.MIN_PHOTOS:
        await message.answer(
            "📷 Rasm yuboring yoki davom etish uchun tugmani bosing 👇",
            reply_markup=kb.photos_done_kb(),
        )
    else:
        await message.answer("📷 Iltimos, rasm (surat) ko'rinishida yuboring.")


@router.callback_query(Registration.photos, F.data == "photos_done")
async def reg_photos_done(callback: CallbackQuery, state: FSMContext):
    count = await db.count_photos(callback.from_user.id)
    if count < config.MIN_PHOTOS:
        await callback.answer(f"Kamida {config.MIN_PHOTOS} ta rasm kerak.", show_alert=True)
        return
    await callback.answer()
    await state.set_state(Registration.bio)
    await callback.message.edit_text(f"Rasmlar qabul qilindi ✅ ({count} ta)")
    await callback.message.answer(
        "<b>9-qadam.</b> O'zingiz haqingizda 2-3 og'iz gap yozing "
        "(qiziqishlaringiz, kim bilan tanishmoqchisiz va h.k.):"
    )


@router.message(Registration.bio)
async def reg_bio(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if len(text) < config.MIN_BIO_LEN:
        await message.answer(f"⚠️ Biroz batafsilroq yozing (kamida {config.MIN_BIO_LEN} ta belgi).")
        return
    if len(text) > config.MAX_BIO_LEN:
        await message.answer(f"⚠️ Iltimos, {config.MAX_BIO_LEN} ta belgidan oshmasin.")
        return

    await db.update_user_field(message.from_user.id, "bio", text)
    await db.update_user_field(message.from_user.id, "is_complete", 1)
    await state.clear()

    await message.answer(
        f"🎉 <b>Tabriklaymiz! {config.BOT_NAME}da ro'yxatdan muvaffaqiyatli o'tdingiz.</b>\n\n"
        "Sizning anketangiz:"
    )
    await send_profile_card(message, message.from_user.id)
    await message.answer("Quyidagi menyudan foydalanishingiz mumkin:", reply_markup=kb.main_menu_kb())


@router.message(Command("profile"))
async def cmd_profile(message: Message):
    if not await db.is_registration_complete(message.from_user.id):
        await message.answer("Siz hali ro'yxatdan o'tmagansiz. /start ni bosing.")
        return
    await send_profile_card(message, message.from_user.id)



# ---------------------------------------------------------------------------
# Zaxira handler: eskirgan yoki mos kelmagan tugma bosilganda
# ---------------------------------------------------------------------------

@router.message(Command("profile"))
async def cmd_profile(message: Message):
    if not await db.is_registration_complete(message.from_user.id):
        await message.answer("Siz hali ro'yxatdan o'tmagansiz. /start ni bosing.")
        return
    await send_profile_card(message, message.from_user.id)


@router.callback_query(F.data == "start_search")
async def start_search(callback: CallbackQuery):
    await callback.answer()

    profile = await db.get_random_profile(callback.from_user.id)

    if not profile:
        await callback.message.answer(
            "😔 Hozircha sizga ko'rsatadigan foydalanuvchi topilmadi."
        )
        return

    photos = await db.get_photos(profile["telegram_id"])

    caption = (
        f"👤 <b>{profile['full_name']}</b>\n\n"
        f"🚻 {profile['gender']}\n"
        f"🎂 {profile['age']} yosh\n"
        f"📍 {profile['region']}, {profile['district']}\n\n"
        f"💬 {profile['bio']}"
    )

    if photos:
        await callback.message.answer_photo(
            photo=photos[0],
            caption=caption,
            reply_markup=kb.profile_kb(profile["telegram_id"])
        )
    else:
        await callback.message.answer(
            caption,
            reply_markup=kb.profile_kb(profile["telegram_id"])
        )


@router.callback_query(F.data.startswith("like_"))
async def like_profile(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[1])

    await callback.answer("❤️ Like yuborildi!")

    # Like saqlash
    await db.add_like(
        from_user=callback.from_user.id,
        to_user=user_id
    )

    # O'zaro like tekshirish
    is_match = await db.check_match(
        callback.from_user.id,
        user_id
    )

        if is_match:
        await db.add_match(
            callback.from_user.id,
            user_id
        )

        await db.set_chat(
            callback.from_user.id,
            user_id
        )

        await db.set_chat(
            user_id,
            callback.from_user.id
        )

        match_text = (
            "🎉 <b>Tabriklaymiz! Sizlarda moslik topildi ❤️</b>\n\n"
            "Endi bir-biringiz bilan anonim chat qilishingiz mumkin 💬"
        )

        my_photos = await db.get_photos(user_id)

        if my_photos:
            await callback.message.answer_photo(
                photo=my_photos[0],
                caption=match_text
            )
        else:
            await callback.message.answer(
                match_text
            )

        partner_photos = await db.get_photos(
            callback.from_user.id
        )

        if partner_photos:
            await callback.bot.send_photo(
                user_id,
                photo=partner_photos[0],
                caption=match_text
            )
        else:
            await callback.bot.send_message(
                user_id,
                match_text
            )

    else:
        await callback.message.answer(
            f"❤️ Siz {user_id} profiliga like bosdingiz."
        )


@router.callback_query(F.data == "next_profile")
async def next_profile(callback: CallbackQuery):
    await callback.answer()
    await start_search(callback)


@router.callback_query(F.data.startswith("chat_"))
async def start_chat(callback: CallbackQuery):
    await callback.answer()

    await callback.message.answer(
        "💬 Chat boshlandi.\n"
        "Endi yozgan xabarlaringiz unga yuboriladi."
    )


@router.message(F.text)
async def relay_message(message: Message):
    partner_id = await db.get_chat_partner(
        message.from_user.id
    )

    if not partner_id:
        return

    await message.bot.send_message(
        partner_id,
        f"💬 {message.text}"
    )