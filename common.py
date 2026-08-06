from aiogram import Router, BaseMiddleware
from aiogram.filters import CommandStart
from aiogram.types import Message, TelegramObject, Update
from aiogram.fsm.context import FSMContext
 
from aiogram.enums import ChatMemberStatus

from crud import get_user_by_telegram_id, auto_lift_expired_ban, get_channel_check_settings
from states import RegistrationStates
from inline import get_language_keyboard, get_subscribe_keyboard
from reply import get_main_menu_keyboard
from models import UserStatus

router = Router()

MAIN_MENU_TEXTS = {
    "uz": "Bosh menyu. Kerakli bo'limni tanlang:",
    "ru": "Главное меню. Выберите нужный раздел:",
    "en": "Main menu. Please select a section:",
}

# Foydalanuvchi bazada topilmaganda (masalan, ro'yxatdan hali o'tmagan yoki
# ro'yxatdan o'tish tugallanmagan) ko'rsatiladigan umumiy xabar.
NOT_REGISTERED_TEXTS = {
    "uz": "Siz hali ro'yxatdan o'tmagansiz. Iltimos, /start buyrug'ini bosing.",
    "ru": "Вы еще не зарегистрированы. Пожалуйста, нажмите команду /start.",
    "en": "You are not registered yet. Please press the /start command.",
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

BANNED_USER_TEXTS = {
    "uz": "🚫 Siz botdan foydalanishdan vaqtincha chetlashtirilgansiz.\nMuddati: {until}",
    "ru": "🚫 Вы временно отстранены от использования бота.\nСрок действия: {until}",
    "en": "🚫 You have been temporarily suspended from using the bot.\nUntil: {until}",
}

BANNED_USER_PERMANENT_TEXTS = {
    "uz": "🚫 Siz botdan foydalanish huquqidan doimiy mahrum qilingansiz.",
    "ru": "🚫 Вы навсегда лишены права пользоваться ботом.",
    "en": "🚫 You have been permanently banned from using the bot.",
}

MUST_SUBSCRIBE_TEXTS = {
    "uz": "Botdan to'liq foydalanish uchun, iltimos, bizning kanalimizga obuna bo'ling. Keyin \"✅ Obuna bo'ldim\" tugmasini bosing.",
    "ru": "Чтобы получить полный доступ к боту, пожалуйста, подпишитесь на наш канал. Затем нажмите кнопку \"✅ Я подписался\".",
    "en": "To get full access to the bot, please subscribe to our channel. Then press the \"✅ I'm subscribed\" button.",
}


class BanCheckMiddleware(BaseMiddleware):
    """Bloklangan foydalanuvchilarning istalgan handlerga yetib borishini to'xtatadi."""

    async def __call__(self, handler, event: TelegramObject, data: dict):
        if not isinstance(event, Update):
            return await handler(event, data)

        telegram_user = None
        reply_target = None
        if event.message:
            telegram_user = event.message.from_user
            reply_target = event.message
        elif event.callback_query:
            telegram_user = event.callback_query.from_user
            reply_target = event.callback_query

        if telegram_user is None:
            return await handler(event, data)

        user = await get_user_by_telegram_id(telegram_user.id)
        if user is None or user.status != UserStatus.banned:
            return await handler(event, data)

        user = await auto_lift_expired_ban(user)
        if user.status != UserStatus.banned:
            return await handler(event, data)

        language = user.language or "uz"
        if user.banned_until:
            text = BANNED_USER_TEXTS.get(language, BANNED_USER_TEXTS["uz"]).format(
                until=user.banned_until.strftime("%Y-%m-%d %H:%M")
            )
        else:
            text = BANNED_USER_PERMANENT_TEXTS.get(language, BANNED_USER_PERMANENT_TEXTS["uz"])

        if event.message:
            await reply_target.answer(text)
        else:
            await reply_target.answer(text, show_alert=True)
        return None


class ChannelCheckMiddleware(BaseMiddleware):
    """Kanalga obunani tekshiradigan middleware."""
    async def __call__(self, handler, event: TelegramObject, data: dict):
        if not isinstance(event, Update):
            return await handler(event, data)

        telegram_user = None
        reply_target = None
        if event.message:
            telegram_user = event.message.from_user
            reply_target = event.message
        elif event.callback_query:
            telegram_user = event.callback_query.from_user
            reply_target = event.callback_query

        if telegram_user is None:
            return await handler(event, data)

        # /start komandasini o'tkazib yuborish
        if event.message and event.message.text and event.message.text.startswith('/start'):
            return await handler(event, data)

        settings = await get_channel_check_settings()
        if not settings or not settings.get("force_subscribe"):
            return await handler(event, data)

        channel_id = settings.get("channel_id")
        if not channel_id:
            return await handler(event, data)

        try:
            member = await data["bot"].get_chat_member(chat_id=channel_id, user_id=telegram_user.id)
            if member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
                return await handler(event, data)
        except Exception:
            # Agar kanal topilmasa yoki botda yetarli huquq bo'lmasa, cheklovni o'tkazib yuboramiz
            return await handler(event, data)

        user = await get_user_by_telegram_id(telegram_user.id)
        language = user.language if user else "uz"
        text = MUST_SUBSCRIBE_TEXTS.get(language, MUST_SUBSCRIBE_TEXTS["uz"])
        
        # getting channel link
        try:
            chat = await data["bot"].get_chat(channel_id)
            invite_link = chat.invite_link
            if event.message:
                await reply_target.answer(text, reply_markup=get_subscribe_keyboard(language, invite_link))
            else:
                await reply_target.message.answer(text, reply_markup=get_subscribe_keyboard(language, invite_link))
                await reply_target.answer()
            return None
        except Exception:
            if event.message:
                await reply_target.answer(text)
            else:
                await reply_target.message.answer(text)
                await reply_target.answer()
            return None


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