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

# =========================================================================
# CONSTANTS FOR BACKWARD COMPATIBILITY
# =========================================================================
MAIN_MENU_TEXTS = {
    "uz": "Bosh menyu. Kerakli bo'limni tanlang:",
    "ru": "Главное меню. Выберите нужный раздел:",
    "en": "Main menu. Please select a section:",
}
NOT_REGISTERED_TEXTS = {
    "uz": "Siz hali ro'yxatdan o'tmagansiz. Iltimos, /start buyrug'ini bosing.",
    "ru": "Вы еще не зарегистрированы. Пожалуйста, нажмите команду /start.",
    "en": "You are not registered yet. Please press the /start command.",
}
VERIFICATION_START_TEXT = {
    "uz": "Hisobingizni tasdiqlash uchun hujjat rasmini yuboring.",
    "ru": "Для верификации вашего аккаунта отправьте фото документа.",
    "en": "To verify your account, please send a document photo.",
}
VERIFICATION_SUBMITTED_TEXT = {
    "uz": "Hujjat qabul qilindi. Tez orada ko'rib chiqiladi.",
    "ru": "Документ принят. Скоро будет рассмотрен.",
    "en": "Document submitted. It will be reviewed shortly.",
}
VERIFICATION_IN_PROGRESS_TEXT = {
    "uz": "Verifikatsiya so'rovi allaqachon ko'rib chiqilmoqda.",
    "ru": "Запрос на верификацию уже рассматривается.",
    "en": "Verification request is already under review.",
}
VERIFICATION_ALREADY_VERIFIED_TEXT = {
    "uz": "Hisobingiz allaqachon verifikatsiya qilingan ✅",
    "ru": "Ваш аккаунт уже верифицирован ✅",
    "en": "Your account is already verified ✅",
}
ICEBREAKER_QUESTIONS = [
    "Eng sevimli filmingiz qaysi?",
    "Bo'sh vaqtingizda nima bilan shug'ullanasiz?",
    "Qaysi shaharga sayohat qilishni xohlardingiz?"
]
SECURITY_INFO_TEXTS = {
    "uz": "Xavfsizlik: begonalarga shaxsiy karta ma'lumotlaringizni bermang.",
    "ru": "Безопасность: никогда не передавайте личные данные карты.",
    "en": "Safety: never share sensitive financial details.",
}
EDIT_PROFILE_TEXTS = {
    "uz": "Qaysi ma'lumotni o'zgartirmoqchisiz?",
    "ru": "Какие данные вы хотите изменить?",
    "en": "Which field do you want to edit?",
}

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
