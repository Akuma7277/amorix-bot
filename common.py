import logging
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart
from aiogram.types import (
    Message, 
    WebAppInfo, 
    MenuButtonWebApp, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    ReplyKeyboardRemove
)
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode

from reply import get_webapp_url

router = Router()

def get_webapp_inline_keyboard() -> InlineKeyboardMarkup:
    """Mini Appni to'g'ridan-to'g'ri ochuvchi inline tugma"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💖 Kairyx Mini App ni ochish", web_app=WebAppInfo(url=get_webapp_url()))]
    ])

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    """/start buyrug'i: Pastki klaviaturani tozalab, Mini Appni ochishni taklif qiladi."""
    await state.clear()
    
    # Set chat menu button (Kairyx App)
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

    welcome_text = (
        "💖 <b>Kairyx</b> — premium tanishuv ilovasiga xush kelibsiz!\n\n"
        "Barcha xizmatlar (tanishuv, profillar, chatlar, like'lar, VIP obuna va boshqaruv) to'liq <b>Mini App</b> ichida ishlaydi.\n\n"
        "Ilovani ishga tushirish uchun quyidagi tugmani bosing: 👇"
    )

    # 1. Remove any legacy reply keyboard from user screen
    # 2. Provide the WebApp inline button
    await message.answer(
        text=welcome_text,
        reply_markup=get_webapp_inline_keyboard(),
        parse_mode=ParseMode.HTML
    )

@router.message()
async def all_other_messages(message: Message, bot: Bot):
    """Har qanday boshqa xabar kelganda pastki menyuni tozalab, Mini App tugmasini ko'rsatadi."""
    try:
        await bot.set_chat_menu_button(
            chat_id=message.chat.id,
            menu_button=MenuButtonWebApp(
                text="Kairyx App",
                web_app=WebAppInfo(url=get_webapp_url())
            )
        )
    except Exception:
        pass

    await message.answer(
        text="✨ Kairyx to'liq <b>Mini App</b> orqali ishlaydi.\nIlovani ochish uchun quyidagi tugmani bosing: 👇",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode=ParseMode.HTML
    )
    await message.answer(
        text="👇",
        reply_markup=get_webapp_inline_keyboard()
    )
