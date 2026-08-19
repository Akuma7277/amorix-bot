import logging
from aiogram import Router, BaseMiddleware
from aiogram.filters import CommandStart
from aiogram.types import Message, TelegramObject, Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, WebAppInfo, MenuButtonWebApp
from aiogram import Router, BaseMiddleware, Bot
from aiogram.fsm.context import FSMContext
 
from aiogram.enums import ChatMemberStatus

from crud import get_user_by_telegram_id, auto_lift_expired_ban, get_channel_check_settings
from states import RegistrationStates
from inline import get_language_keyboard, get_subscribe_keyboard
from reply import get_main_menu_keyboard
from config import WEBAPP_URL
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

SECURITY_INFO_TEXTS = {
    "uz": (
        "🛡️ <b>Xavfsiz tanishuv qoidalari</b>\n\n"
        "• Karta raqamingiz, SMS kodlaringiz va parollaringizni hech kimga yubormang.\n"
        "• Birinchi uchrashuvni jamoat joyida (kafe, park) o'tkazing.\n"
        "• Shubhali holatda yoki nomaqbul xatti-harakat kuzatsangiz, foydalanuvchini darhol bloklang va shikoyat qiling."
    ),
    "ru": (
        "🛡️ <b>Правила безопасных знакомств</b>\n\n"
        "• Никогда не отправляйте номер своей карты, SMS-коды и пароли.\n"
        "• Первую встречу проводите в общественном месте (кафе, парк).\n"
        "• В случае подозрительной ситуации или неприемлемого поведения немедленно заблокируйте пользователя и подайте жалобу."
    ),
    "en": (
        "🛡️ <b>Safe Dating Rules</b>\n\n"
        "• Never send your card number, SMS codes, or passwords.\n"
        "• Hold the first meeting in a public place (cafe, park).\n"
        "• In case of suspicious activity or inappropriate behavior, block the user immediately and file a report."
    ),
}

ICEBREAKER_QUESTIONS = {
    "uz": [
        "Dam olish kunini qanday o‘tkazishni yoqtirasiz?",
        "Sizni oxirgi marta nima ilhomlantirdi?",
        "Birga borishni xohlagan joyingiz qayer?",
        "Hayotingizdagi eng kulgili voqea qaysi?",
        "Agar istalgan joyga sayohat qila olganingizda, qayerga borardingiz?",
    ],
    "ru": [
        "Как вы любите проводить выходные?",
        "Что вдохновило вас в последний раз?",
        "Куда бы вы хотели отправиться вместе?",
        "Какой самый смешной случай был в вашей жизни?",
        "Если бы вы могли путешествовать куда угодно, куда бы вы поехали?",
    ],
    "en": [
        "How do you like to spend your weekends?",
        "What inspired you recently?",
        "Where would you like to travel together?",
        "What's the funniest thing that has ever happened to you?",
        "If you could travel anywhere, where would you go?",
    ],
}

MUST_SUBSCRIBE_TEXTS = {
    "uz": "Botdan to'liq foydalanish uchun, iltimos, bizning kanalimizga obuna bo'ling. Keyin \"✅ Obuna bo'ldim\" tugmasini bosing.",
    "ru": "Чтобы получить полный доступ к боту, пожалуйста, подпишитесь на наш канал. Затем нажмите кнопку \"✅ Я подписался\".",
    "en": "To get full access to the bot, please subscribe to our channel. Then press the \"✅ I'm subscribed\" button.",
}

EDIT_PROFILE_TEXTS = {
    "uz": "Qaysi ma'lumotni tahrirlamoqchisiz?",
    "ru": "Какую информацию вы хотите отредактировать?",
    "en": "Which information do you want to edit?",
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
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    """/start komandasi uchun handler - Mini Appni ochadi"""
    await state.clear()

    user = await get_user_by_telegram_id(message.from_user.id)
    language = user.language if user else "uz"

    # Auto set Chat Menu Button if WEBAPP_URL is set
    if WEBAPP_URL:
        try:
            await bot.set_chat_menu_button(
                chat_id=message.chat.id,
                menu_button=MenuButtonWebApp(
                    text="Amorix App",
                    web_app=WebAppInfo(url=WEBAPP_URL)
                )
            )
        except Exception as e:
            logging.warning(f"Error setting chat menu button: {e}")

    start_text = {
        "uz": "Amorix premium tanishuv ilovasiga xush kelibsiz! 💖\n\nIlovadan foydalanish uchun quyidagi tugmani bosing va Mini Appni oching:" if WEBAPP_URL else "Amorix premium tanishuv ilovasiga xush kelibsiz! 💖\n\nMini App hali sozlanmagan. Iltimos, keyinroq urinib ko'ring.",
        "ru": "Добро пожаловать в premium-dating Amorix! 💖\n\nЧтобы открыть приложение, нажмите кнопку ниже:" if WEBAPP_URL else "Добро пожаловать в premium-dating Amorix! 💖\n\nMini App еще не настроен. Пожалуйста, попробуйте позже.",
        "en": "Welcome to Amorix premium dating! 💖\n\nTo open the app, press the button below:" if WEBAPP_URL else "Welcome to Amorix premium dating! 💖\n\nMini App is not configured yet. Please try again later.",
    }

    if WEBAPP_URL:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📱 Mini App ni ochish", web_app=WebAppInfo(url=WEBAPP_URL))]
        ])
        reply_kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📱 Mini App", web_app=WebAppInfo(url=WEBAPP_URL))]
            ],
            resize_keyboard=True
        )
    else:
        keyboard = None
        reply_kb = None

    await message.answer(
        start_text.get(language, start_text["uz"]),
        reply_markup=reply_kb if reply_kb else ReplyKeyboardRemove()
    )


@router.message()
async def all_other_messages(message: Message, bot: Bot):
    """Barcha boshqa xabarlarni Mini Appga yo'naltiradi"""
    user = await get_user_by_telegram_id(message.from_user.id)
    language = user.language if user else "uz"

    if WEBAPP_URL:
        try:
            await bot.set_chat_menu_button(
                chat_id=message.chat.id,
                menu_button=MenuButtonWebApp(
                    text="Amorix App",
                    web_app=WebAppInfo(url=WEBAPP_URL)
                )
            )
        except Exception:
            pass

    redirect_text = {
        "uz": "Amorix faqat Mini App orqali ishlaydi. Ilovani ochish uchun pastdagi tugmani bosing: 📱" if WEBAPP_URL else "Mini App hali sozlanmagan. Iltimos, keyinroq urinib ko'ring.",
        "ru": "Amorix работает только через Mini App. Нажмите кнопку ниже, чтобы открыть приложение: 📱" if WEBAPP_URL else "Mini App еще не настроен. Пожалуйста, попробуйте позже.",
        "en": "Amorix only works via Mini App. Press the button below to open the app: 📱" if WEBAPP_URL else "Mini App is not configured yet. Please try again later.",
    }

    if WEBAPP_URL:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📱 Mini App ni ochish", web_app=WebAppInfo(url=WEBAPP_URL))]
        ])
        reply_kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📱 Mini App", web_app=WebAppInfo(url=WEBAPP_URL))]
            ],
            resize_keyboard=True
        )
    else:
        keyboard = None
        reply_kb = None

    await message.answer(
        redirect_text.get(language, redirect_text["uz"]),
        reply_markup=reply_kb if reply_kb else ReplyKeyboardRemove()
    )