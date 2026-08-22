import logging
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, WebAppInfo, MenuButtonWebApp
from aiogram.fsm.context import FSMContext

from crud import get_user_by_telegram_id
from states import RegistrationStates
from inline import get_language_keyboard
from reply import get_main_menu_keyboard, get_webapp_url
from i18n import t

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    """/start buyrug'i: Ro'yxatdan o'tgan bo'lsa asosiy menyuni, bo'lmasa til tanlashni ko'rsatadi."""
    await state.clear()
    
    # Set chat menu button
    try:
        await bot.set_chat_menu_button(
            chat_id=message.chat.id,
            menu_button=MenuButtonWebApp(
                text="Kairyx App",
                web_app=WebAppInfo(url=get_webapp_url())
            )
        )
    except Exception as e:
        logging.warning(f"Error setting chat menu button: {e}")

    telegram_id = message.from_user.id
    user = await get_user_by_telegram_id(telegram_id)

    # If user already completed registration
    if user and user.name and user.status.value in ["ACTIVE", "APPROVED", "active", "approved"]:
        lang = user.language or "uz"
        badge = " ✅" if user.is_verified else ""
        
        welcome_text = (
            f"✨ <b>Assalomu alaykum, {user.name}{badge}!</b>\n\n"
            f"{t('registration_success', lang)}"
        )
        await message.answer(
            text=welcome_text,
            reply_markup=get_main_menu_keyboard(lang),
            parse_mode="HTML"
        )
        return

    # If new user -> start registration with language choice
    await state.set_state(RegistrationStates.choosing_language)
    await message.answer(
        text=(
            "✨ <b>AMORIX / KAIRYX</b>\n\n"
            "🇺🇿 <b>Muloqot tilini tanlang:</b>\n"
            "🇷🇺 <b>Выберите язык общения:</b>\n"
            "🇬🇧 <b>Choose your language:</b>"
        ),
        reply_markup=get_language_keyboard(),
        parse_mode="HTML"
    )
