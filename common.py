from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
 
from crud import get_user_by_telegram_id
from states import RegistrationStates
from inline import get_language_keyboard
from reply import get_main_menu_keyboard

router = Router()

MAIN_MENU_TEXTS = {
    "uz": "Bosh menyu. Kerakli bo'limni tanlang:",
    "ru": "Главное меню. Выберите нужный раздел:",
    "en": "Main menu. Please select a section:",
}

VERIFICATION_START_TEXT = {
    "uz": "Hisobingizni tasdiqlash uchun shaxsingizni tasdiqlovchi hujjat (pasport yoki ID karta) rasmini yuboring. Ma'lumotlaringiz maxfiy saqlanadi.",
    "ru": "Для верификации вашего аккаунта, пожалуйста, отправьте фотографию вашего документа, удостоверяющего личность (паспорт или ID-карта). Ваши данные будут сохранены конфиденциально.",
    "en": "To verify your account, please send a photo of your identity document (passport or ID card). Your data will be kept confidential.",
}

VERIFICATION_SUBMITTED_TEXT = {
    "uz": "✅ Hujjatingiz qabul qilindi va ko'rib chiqish uchun yuborildi. Natija haqida sizga xabar beramiz.",
    "ru": "✅ Ваш документ принят и отправлен на рассмотрение. Мы сообщим вам о результате.",
    "en": "✅ Your document has been received and submitted for review. We will notify you of the result.",
}

VERIFICATION_IN_PROGRESS_TEXT = {
    "uz": "Sizning oldingi so'rovingiz hali ham ko'rib chiqilmoqda. Iltimos, natijani kuting.",
    "ru": "Ваш предыдущий запрос все еще находится на рассмотрении. Пожалуйста, ожидайте результата.",
    "en": "Your previous request is still under review. Please wait for the result.",
}

VERIFICATION_ALREADY_VERIFIED_TEXT = {
    "uz": "Sizning hisobingiz allaqachon tasdiqlangan.",
    "ru": "Ваш аккаунт уже верифицирован.",
    "en": "Your account is already verified.",
}

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """/start komandasi uchun handler"""
    await state.clear() # Har ehtimolga qarshi oldingi holatlarni tozalash

    user = await get_user_by_telegram_id(message.from_user.id)

    if user:
        # Foydalanuvchi ro'yxatdan o'tgan
        language = user.language or "uz"
        await message.answer(
            MAIN_MENU_TEXTS.get(language, MAIN_MENU_TEXTS["uz"]),
            reply_markup=get_main_menu_keyboard(language)
        )
    else:
        # Foydalanuvchi ro'yxatdan o'tmagan
        await message.answer(
            "Tilni tanlang / Выберите язык / Choose a language:",
            reply_markup=get_language_keyboard()
        )
        await state.set_state(RegistrationStates.choosing_language)