import logging
from aiogram import Router, BaseMiddleware
from aiogram.filters import CommandStart
from aiogram.types import Message, TelegramObject, Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, WebAppInfo, MenuButtonWebApp, CallbackQuery
from aiogram import F
from aiogram import Router, BaseMiddleware, Bot
from aiogram.fsm.context import FSMContext
 
from aiogram.enums import ChatMemberStatus

from crud import get_user_by_telegram_id, auto_lift_expired_ban, get_channel_check_settings
from states import RegistrationStates
from inline import get_language_keyboard, get_subscribe_keyboard
from reply import get_main_menu_keyboard
from config import WEBAPP_URL

def get_webapp_url() -> str:
    """Telegram keshini tozalash uchun dinamik havola (har daqiqa yangilanadi)"""
    import time
    if not WEBAPP_URL:
        return ""
    t = int(time.time() // 60)
    return f"{WEBAPP_URL}&v={t}" if "?" in WEBAPP_URL else f"{WEBAPP_URL}?v={t}"

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

    # Auto set Chat Menu Button
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

    # Beautiful bilingual Uzbek / Russian start message
    bilingual_start_text = (
        "🇺🇿 <b>Kairyx premium tanishuv ilovasiga xush kelibsiz!</b> 💖\n\n"
        "Kairyx — bu sizga mos va sifatli insonlarni xavfsiz topishga yordam beradigan premium muloqot maydonidir. "
        "Ilovadan foydalanish va o\'z juftingizni izlashni boshlash uchun pastdagi <b>'Kairyx App' (Menu)</b> tugmasini bosing.\n\n"
        "➖➖➖➖➖➖➖➖➖➖➖➖\n\n"
        "🇷🇺 <b>Добро пожаловать в премиум-приложение знакомств Kairyx!</b> 💖\n\n"
        "Kairyx — это премиальная платформа, которая поможет вам безопасно найти подходящих и качественных людей. "
        "Чтобы открыть приложение и начать поиск, нажмите кнопку <b>'Kairyx App' (Menu)</b> внизу."
    )

    if message.from_user.id == 7992878834:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📱 Mini App ni ochish", web_app=WebAppInfo(url=get_webapp_url()))],
            [InlineKeyboardButton(text="🔑 Admin Panelga kirish", callback_data="admin_enter_from_start")]
        ])
        await message.answer(
            bilingual_start_text + "\n\n🔑 <b>Admin panelga kirish:</b> /admin",
            reply_markup=keyboard
        )
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📱 Mini App ni ochish", web_app=WebAppInfo(url=get_webapp_url()))]
        ])
        await message.answer(
            bilingual_start_text,
            reply_markup=keyboard
        )
    # Always remove old reply keyboard
    try:
        await message.answer(".", reply_markup=ReplyKeyboardRemove())
    except Exception:
        pass


@router.callback_query(F.data == "admin_enter_from_start")
async def admin_enter_from_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != 7992878834:
        await callback.answer("Sizda admin paneliga kirish huquqi yo\'q.", show_alert=True)
        return
        
    await state.clear()
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = user.language if user else "uz"
    
    from reply import get_admin_main_menu_keyboard
    from states import AdminStates
    
    # Open admin panel inside Mini App via web_app link  
    admin_webapp_url = get_webapp_url()
    admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🛡️ Admin Panelni Mini App'da ochish",
            web_app=WebAppInfo(url=admin_webapp_url + ("&" if "?" in admin_webapp_url else "?") + "admin=1")
        )],
        [InlineKeyboardButton(text="📋 Bot Admin Menu", callback_data="admin_bot_menu")]
    ])
    
    await callback.message.answer(
        "🛡️ <b>Admin Panel</b>\n\nMini App'da admin bo\'limini ochish uchun quyidagi tugmani bosing, yoki bot admin menyusini oching:",
        reply_markup=admin_keyboard
    )
    await callback.answer()


@router.callback_query(F.data == "admin_bot_menu")
async def admin_bot_menu_handler(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != 7992878834:
        await callback.answer("Sizda admin paneliga kirish huquqi yo\'q.", show_alert=True)
        return
    
    await state.clear()
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = user.language if user else "uz"
    
    from reply import get_admin_main_menu_keyboard
    from states import AdminStates
    
    await callback.message.answer(
        "🛡️ Admin paneliga xush kelibsiz. Bu yerda foydalanuvchilar, to\'lovlar, moderatorlik va broadcastlarni boshqarishingiz mumkin.",
        reply_markup=get_admin_main_menu_keyboard(language)
    )
    await state.set_state(AdminStates.main_menu)
    await callback.answer()


@router.message()
async def all_other_messages(message: Message, bot: Bot):
    """Barcha boshqa xabarlarni Mini Appga yo'naltiradi"""
    user = await get_user_by_telegram_id(message.from_user.id)
    language = user.language if user else "uz"

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

    redirect_text = {
        "uz": "Kairyx faqat Mini App orqali ishlaydi. Ilovani ochish uchun pastdagi 'Kairyx App' (Menu) tugmasini bosing: 📱",
        "ru": "Kairyx работает только через Mini App. Нажмите кнопку 'Kairyx App' (Menu) внизу, чтобы открыть приложение: 📱",
        "en": "Kairyx only works via Mini App. Press the 'Kairyx App' (Menu) button below to open the app: 📱",
    }

    await message.answer(
        redirect_text.get(language, redirect_text["uz"]),
        reply_markup=ReplyKeyboardRemove()
    )


class ApprovalCheckMiddleware(BaseMiddleware):
    """Tasdiqlanmagan foydalanuvchilarning handlerga yetib borishini to'xtatadi."""

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

        state: FSMContext = data.get("state")
        if state:
            current_state = await state.get_state()
            if current_state and current_state.startswith("RegistrationStates"):
                return await handler(event, data)

        user = await get_user_by_telegram_id(telegram_user.id)
        if user is None:
            return await handler(event, data)

        # Adminlar har doim o'tadi
        if telegram_user.id == 7992878834:
            return await handler(event, data)

        if user.status == UserStatus.active:
            return await handler(event, data)

        if user.status == UserStatus.pending_approval:
            text_map = {
                "uz": "⏳ Sizning profilingiz hali ham moderatorlarimiz tomonidan tekshirilmoqda. Iltimos, tasdiqlashni kuting.",
                "ru": "⏳ Ваш профиль все еще находится на модерации. Пожалуйста, ожидайте подтверждения.",
                "en": "⏳ Your profile is still under review. Please wait for confirmation."
            }
            lang = user.language or "uz"
            msg = text_map.get(lang, text_map["uz"])
            
            from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
            reply_kb = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="📱 Mini App", web_app=WebAppInfo(url=get_webapp_url()))]
                ],
                resize_keyboard=True
            )
            
            if event.message:
                await reply_target.answer(msg, reply_markup=reply_kb)
            else:
                await reply_target.message.answer(msg, reply_markup=reply_kb)
                await reply_target.answer()
            return None

        if user.status == UserStatus.rejected:
            text_map = {
                "uz": f"❌ Sizning profilingiz rad etilgan.\n\nSababi: {user.rejection_reason or 'Keltirilmagan'}\n\nIltimos, Mini App ga kirib ma\'lumotlarni qaytadan yuboring.",
                "ru": f"❌ Ваш профиль был отклонен.\n\nПричина: {user.rejection_reason or 'Не указана'}\n\nПожалуйста, откройте Mini App и отправьте данные заново.",
                "en": f"❌ Your profile has been rejected.\n\nReason: {user.rejection_reason or 'Not specified'}\n\nPlease open the Mini App and resubmit your details."
            }
            lang = user.language or "uz"
            msg = text_map.get(lang, text_map["uz"])
            
            from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
            reply_kb = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="📱 Mini App", web_app=WebAppInfo(url=get_webapp_url()))]
                ],
                resize_keyboard=True
            )
            
            if event.message:
                await reply_target.answer(msg, reply_markup=reply_kb)
            else:
                await reply_target.message.answer(msg, reply_markup=reply_kb)
                await reply_target.answer()
            return None

        return await handler(event, data)
