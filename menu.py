from datetime import datetime, timedelta
from aiogram import F, Router, Bot
import logging
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from reply import MAIN_MENU_BUTTONS, get_main_menu_keyboard
from config import PAYMENT_CARD_NUMBER, ADMIN_IDS
from crud import (
    get_user_by_telegram_id,
    get_user_photos,
    get_profiles_for_user,
    add_like_and_check_match,
    get_user_by_id,
    get_user_matches,
    get_match_by_id,
    create_chat_message,
    update_user_profile_field,
    create_report,
    delete_user_data,
    create_verification_request,
    create_payment_record,
    get_users_who_liked_me, block_user, get_user_referrals, # Added for "Who Liked Me", User Blocking and Referral feature
    check_and_consume_like_quota, set_user_language, # Fix 12: Import set_user_language
    activate_profile_boost,
    create_support_message,
    get_all_admin_ids,
    DAILY_LIKE_LIMITS,
    DAILY_SUPER_LIKE_LIMITS,
    BOOST_DURATION_MINUTES,
    create_gift,
)
from states import MenuStates, EditingStates, ReportingStates, SettingsStates, VerificationStates, PremiumStates
from inline import ALL_INTERESTS # Qiziqishlar nomlarini olish uchun
from inline import ( # Fix 12: Import get_back_only_keyboard and Updated imports for gift feature
    get_search_keyboard, get_match_keyboard, get_chats_keyboard, get_profile_view_keyboard, get_edit_profile_keyboard,
    get_report_category_keyboard, get_settings_keyboard, get_confirm_delete_account_keyboard, get_language_keyboard,
    get_premium_plans_keyboard, get_premium_dashboard_keyboard, get_likes_keyboard, get_help_keyboard, get_payment_confirmation_keyboard,
    get_gift_type_keyboard, GIFT_BUTTON_TEXTS, get_back_only_keyboard
)
from models import ReportCategory, UserStatus, VerificationStatus, PremiumPlan # Import UserStatus
from common import MAIN_MENU_TEXTS, VERIFICATION_START_TEXT, VERIFICATION_SUBMITTED_TEXT, VERIFICATION_IN_PROGRESS_TEXT, VERIFICATION_ALREADY_VERIFIED_TEXT, NOT_REGISTERED_TEXTS # Import common texts

# Using RegistrationStates to clear state is not ideal, but works.
# Let's keep it for now. from app.states import RegistrationStates
from registration import EDIT_PROFILE_TEXTS # Import text from registration

router = Router()


def has_active_premium(user) -> bool:
    """Returns True if the user has a non-basic plan that has not expired yet."""
    return bool(
        user
        and user.premium_plan != PremiumPlan.basic
        and user.premium_expires_at
        and user.premium_expires_at > datetime.now()
    )

# Barcha menyu tugmalari matnlarini bitta ro'yxatga yig'ish
all_menu_buttons = []
for lang_buttons in MAIN_MENU_BUTTONS.values():
    all_menu_buttons.extend(lang_buttons.values())

HELP_MAIN_TEXT = {
    "uz": "Yordam bo'limi. Savollaringiz bormi?",
    "ru": "Раздел помощи. Есть вопросы?",
    "en": "Help section. Do you have any questions?",
}

FAQ_TEXT = {
    "uz": "Bu yerda tez-tez so'raladigan savollar bo'ladi.",
    "ru": "Здесь будут часто задаваемые вопросы.",
    "en": "Frequently asked questions will be here.",
}

CONTACT_SUPPORT_TEXT = {
    "uz": "Qo'llab-quvvatlash bilan bog'lanish uchun @admin ga yozing.",
    "ru": "Для связи с поддержкой пишите @admin.",
    "en": "To contact support, write to @admin.",
}

SEARCH_PROFILE_TEXTS = {
    "uz": (
        "<b>{name}</b>, {age}\n"
        "{city}, {district}\n\n"
        "<i>{bio}</i>{verification_checkmark}\n\n"
        "<b>Qiziqishlar:</b> {interests}"
    ),
    "ru": (
        "<b>{name}</b>, {age}\n"
        "{city}, {district}\n\n"
        "<i>{bio}</i>{verification_checkmark}\n\n"
        "<b>Интересы:</b> {interests}"
    ),
    "en": (
        "<b>{name}</b>, {age}\n"
        "{city}, {district}\n\n"
        "<i>{bio}</i>{verification_checkmark}\n\n"
        "<b>Interests:</b> {interests}"
    ),
}

NO_PROFILES_TEXTS = {
    "uz": "Afsuski, hozircha siz uchun mos anketalar topilmadi. Keyinroq qayta urinib ko'ring.",
    "ru": "К сожалению, подходящих анкет для вас пока не нашлось. Попробуйте позже.",
    "en": "Unfortunately, no suitable profiles were found for you at this time. Please try again later.",
}

NO_CHATS_TEXTS = {
    "uz": "Sizda hozircha faol suhbatlar yo'q.",
    "ru": "У вас пока нет активных чатов.",
    "en": "You have no active chats yet.",
}

CHATS_LIST_TEXTS = {
    "uz": "Suhbatlaringiz ro'yxati:",
    "ru": "Список ваших чатов:",
    "en": "Your list of chats:",
}

IN_CHAT_TEXTS = {
    "uz": "Siz <b>{name}</b> bilan suhbatdasiz. Xabarlaringizni yuborishingiz mumkin.\n\nSuhbatni yakunlash uchun /stopchat buyrug'ini bosing.",
    "ru": "Вы в чате с <b>{name}{verification_checkmark}</b>. Можете отправлять сообщения.\n\nЧтобы завершить чат, используйте команду /stopchat.",
    "en": "You are in a chat with <b>{name}{verification_checkmark}</b>. You can send your messages.\n\nTo end the chat, use the /stopchat command.",
}

STOP_CHAT_TEXTS = {
    "uz": "Suhbat yakunlandi. Asosiy menyu.",
    "ru": "Чат завершен. Главное меню.",
    "en": "Chat has ended. Main menu.",
}

REPORT_CATEGORY_PROMPT = {
    "uz": "Shikoyat sababini tanlang:",
    "ru": "Выберите причину жалобы:",
    "en": "Please choose the reason for the report:",
}

REPORT_DESCRIPTION_PROMPT = {
    "uz": "Iltimos, vaziyatni qisqacha tavsiflab bering:",
    "ru": "Пожалуйста, кратко опишите ситуацию:",
    "en": "Please briefly describe the situation:",
}

REPORT_SUCCESSFULLY_SENT = {
    "uz": "✅ Shikoyatingiz qabul qilindi. Moderatorlarimiz uni tez orada ko'rib chiqishadi. Qidiruv davom etmoqda...",
    "ru": "✅ Ваша жалоба принята. Наши модераторы рассмотрят ее в ближайшее время. Поиск продолжается...",
    "en": "✅ Your report has been submitted. Our moderators will review it shortly. Continuing search...",
}

SETTINGS_MAIN_TEXT = {
    "uz": "Sozlamalar menyusi. Kerakli bo'limni tanlang:",
    "ru": "Меню настроек. Выберите нужный раздел:",
    "en": "Settings menu. Select the desired section:",
}

PROFILE_HIDDEN_TEXT = {
    "uz": "✅ Profilingiz yashirildi. Endi siz qidiruvda ko'rinmaysiz.",
    "ru": "✅ Ваш профиль скрыт. Теперь вы не будете отображаться в поиске.",
    "en": "✅ Your profile is now hidden. You will no longer appear in search.",
}

PROFILE_SHOWN_TEXT = {
    "uz": "✅ Profilingiz ko'rsatildi. Endi siz qidiruvda ko'rinasiz.",
    "ru": "✅ Ваш профиль показан. Теперь вы будете отображаться в поиске.",
    "en": "✅ Your profile is now visible. You will appear in search.",
}

CHANGE_LANGUAGE_PROMPT = {
    "uz": "Iltimos, tilni tanlang:",
    "ru": "Пожалуйста, выберите язык:",
    "en": "Please choose a language:",
}

LANGUAGE_CHANGED_TEXT = {
    "uz": "✅ Til muvaffaqiyatli o'zgartirildi.",
    "ru": "✅ Язык успешно изменен.",
    "en": "✅ Language changed successfully.",
}

DELETE_ACCOUNT_CONFIRM_TEXT = {
    "uz": "Hisobingizni o'chirishni tasdiqlaysizmi? Bu amalni qaytarib bo'lmaydi.",
    "ru": "Вы уверены, что хотите удалить свой аккаунт? Это действие необратимо.",
    "en": "Are you sure you want to delete your account? This action is irreversible.",
}

ACCOUNT_DELETED_TEXT = {
    "uz": "✅ Hisobingiz muvaffaqiyatli o'chirildi. Botdan foydalanganingiz uchun rahmat!",
    "ru": "✅ Ваш аккаунт успешно удален. Спасибо за использование бота!",
    "en": "✅ Your account has been successfully deleted. Thank you for using the bot!",
}

MATCH_NOTIFICATION_TEXTS = {
    "uz": "🎉 <b>Juftlik!</b>\n\nSiz <b>{name}</b> bilan bir-biringizga yoqdingiz. Suhbatni boshlashingiz mumkin!",
    "ru": "🎉 <b>Совпадение!</b>\n\nВы понравились друг другу с <b>{name}</b>. Можете начать общение!",
    "en": "🎉 <b>It's a Match!</b>\n\nYou and <b>{name}</b> liked each other. You can start chatting now!",
}

SUPER_LIKE_TEXTS = {
    "uz": "✨ Super like yuborildi! Bu sizning qiziqishingizni ko'rsatadi.",
    "ru": "✨ Супер-лайк отправлен! Это ярко показывает ваш интерес.",
    "en": "✨ Super like sent! This clearly shows your interest.",
}

SUPER_LIKE_NOTIFY_TEXTS = {
    "uz": "✨ {name} sizni super like bilan tanladi!",
    "ru": "✨ {name} отправил(а) вам супер-лайк!",
    "en": "✨ {name} sent you a super like!",
}

BLOCKED_USER_TEXTS = {
    "uz": "🚫 Foydalanuvchi bloklandi. U endi siz uchun ko'rinmaydi.",
    "ru": "🚫 Пользователь заблокирован. Он больше не будет отображаться для вас.",
    "en": "🚫 User blocked. They will no longer appear to you.",
}

PROFILE_VIEW_TEXTS = {
    "uz": (
        "<b>👤 Mening profilim:</b>\n\n"
        "<b>Ism:</b> {name}\n"
        "<b>Yosh:</b> {age}\n"
        "<b>Jins:</b> {gender}\n"
        "<b>Kimni qidiryapti:</b> {looking_for}\n"
        "<b>Shahar:</b> {city}, {district}\n"
        "<b>Qiziqishlar:</b> {interests}\n\n"
        "<b>Bio:</b>\n{bio}\n\n"
        "<b>Premium:</b> {premium_status}\n"
        "<b>Verifikatsiya:</b> {verification_status}{verification_checkmark}"
    ),
    "ru": (
        "<b>👤 Мой профиль:</b>\n\n"
        "<b>Имя:</b> {name}\n"
        "<b>Возраст:</b> {age}\n"
        "<b>Пол:</b> {gender}\n"
        "<b>Ищет:</b> {looking_for}\n"
        "<b>Город:</b> {city}, {district}\n"
        "<b>Интересы:</b> {interests}\n\n"
        "<b>О себе:</b>\n{bio}\n\n"
        "<b>Премиум:</b> {premium_status}\n"
        "<b>Верификация:</b> {verification_status}{verification_checkmark}"
    ),
    "en": (
        "<b>👤 My Profile:</b>\n\n"
        "<b>Name:</b> {name}\n"
        "<b>Age:</b> {age}\n"
        "<b>Gender:</b> {gender}\n"
        "<b>Looking for:</b> {looking_for}\n"
        "<b>City:</b> {city}, {district}\n"
        "<b>Interests:</b> {interests}\n\n"
        "<b>Bio:</b>\n{bio}{verification_checkmark}\n\n"
        "<b>Premium:</b> {premium_status}\n"
        "<b>Verification:</b> {verification_status}{verification_checkmark}"
    ),
}

NO_LIKES_TEXTS = {
    "uz": "Sizni hali hech kim yoqtirmagan. Qidiruvda faol bo'ling!",
    "ru": "Вас пока никто не лайкнул. Будьте активнее в поиске!",
    "en": "Nobody has liked you yet. Be more active in the search!",
}

PREMIUM_REQUIRED_TEXTS = {
    "uz": "Bu funksiya faqat premium foydalanuvchilar uchun mavjud. Premium obuna sotib olish uchun '⭐️ Premium' tugmasini bosing.",
    "ru": "Эта функция доступна только для премиум-пользователей. Нажмите '⭐️ Премиум', чтобы приобрести премиум-подписку.",
    "en": "This feature is only available for premium users. Click '⭐️ Premium' to purchase a premium subscription.",
}

LIKE_LIMIT_REACHED_TEXTS = {
    "uz": "❌ Bugungi kunlik layk limitingiz tugadi. Ko'proq layk uchun Premium sotib oling.",
    "ru": "❌ Ваш дневной лимит лайков исчерпан. Приобретите Premium для большего количества лайков.",
    "en": "❌ Your daily like limit is used up. Get Premium for more likes.",
}

SUPER_LIKE_LIMIT_REACHED_TEXTS = {
    "uz": "❌ Bugungi super like limitingiz tugadi (yoki bu funksiya Premium uchun). Premium sotib oling.",
    "ru": "❌ Ваш лимит супер-лайков на сегодня исчерпан (или это премиум-функция). Приобретите Premium.",
    "en": "❌ Your super like limit for today is used up (or this is a Premium feature). Get Premium.",
}

LIKES_LOCKED_TEXTS = {
    "uz": "🔒 {count} kishi sizni yoqtirdi! Ularni ko'rish uchun Premium obuna kerak.",
    "ru": "🔒 Вы понравились {count} пользователям! Чтобы увидеть их, нужна Premium-подписка.",
    "en": "🔒 {count} people liked you! Get Premium to see who they are.",
}

BOOST_ACTIVATED_TEXTS = {
    "uz": "🚀 Boost faollashtirildi! Profilingiz {minutes} daqiqa davomida qidiruvda birinchi bo'lib ko'rsatiladi.",
    "ru": "🚀 Буст активирован! Ваш профиль будет показываться первым в поиске в течение {minutes} минут.",
    "en": "🚀 Boost activated! Your profile will be shown first in search for {minutes} minutes.",
}

PREMIUM_DASHBOARD_TEXTS = {
    "uz": "⭐️ Sizda faol <b>{plan}</b> obuna bor.\nAmal qilish muddati: {expires_at}\n\nKunlik layklar: {like_limit}\nKunlik super-layklar: {super_like_limit}",
    "ru": "⭐️ У вас активна подписка <b>{plan}</b>.\nДействует до: {expires_at}\n\nЛайков в день: {like_limit}\nСупер-лайков в день: {super_like_limit}",
    "en": "⭐️ You have an active <b>{plan}</b> subscription.\nExpires at: {expires_at}\n\nDaily likes: {like_limit}\nDaily super likes: {super_like_limit}",
}

LIKES_VIEW_TEXTS = {
    "uz": "❤️ Sizni yoqtirgan foydalanuvchilar:",
    "ru": "❤️ Пользователи, которым вы понравились:",
    "en": "❤️ Users who liked you:",
}

LIKES_EMPTY_TEXTS = {
    "uz": "Hozircha sizni hech kim yoqtirmagan. Qidiruvda faol bo'ling!",
    "ru": "Пока вас никто не лайкнул. Будьте активнее в поиске!",
    "en": "Nobody has liked you yet. Be more active in the search!",
}

REFERRAL_TEXTS = {
    "uz": (
        "🎁 <b>Do'stlarni taklif qilish!</b>\n\n"
        "Sizning shaxsiy referal havolangiz: <code>https://t.me/{bot_username}?start=ref_{user_id}</code>\n\n"
        "Bu havola orqali ro'yxatdan o'tgan har bir do'stingiz uchun siz bonus olasiz (bu funksiya hozircha ishlab chiqilmoqda)!\n\n"
        "Siz taklif qilgan do'stlar soni: <b>{referral_count}</b>"
    ),
    "ru": (
        "🎁 <b>Пригласить друзей!</b>\n\n"
        "Ваша личная реферальная ссылка: <code>https://t.me/{bot_username}?start=ref_{user_id}</code>\n\n"
        "За каждого друга, зарегистрировавшегося по этой ссылке, вы получите бонус (эта функция пока в разработке)!\n\n"
        "Количество приглашенных друзей: <b>{referral_count}</b>"
    ),
    "en": (
        "🎁 <b>Refer Friends!</b>\n\n"
        "Your personal referral link: <code>https://t.me/{bot_username}?start=ref_{user_id}</code>\n\n"
        "You will receive a bonus for every friend who registers using this link (this feature is currently under development)!\n\n"
        "Number of referred friends: <b>{referral_count}</b>"
    ),
}

PREMIUM_MAIN_TEXT = {
    "uz": "⭐️ KAIRYX Premium imkoniyatlari bilan tanishing. Quyidagi tariflardan birini tanlang:",
    "ru": "⭐️ Ознакомьтесь с возможностями KAIRYX Premium. Выберите один из тарифов:",
    "en": "⭐️ Explore KAIRYX Premium features. Choose one of the plans below:",
}

PREMIUM_BENEFITS_TEXT = {
    "uz": (
        "Premium bilan siz:\n"
        "• ko'proq profil ko'rasiz\n"
        "• ko'proq like olish imkoniyatiga ega bo'lasiz\n"
        "• profilingiz ustun ko'rinadi"
    ),
    "ru": (
        "С Premium вы:\n"
        "• видите больше профилей\n"
        "• получаете больше лайков\n"
        "• ваш профиль выглядит заметнее"
    ),
    "en": (
        "With Premium you can:\n"
        "• see more profiles\n"
        "• receive more likes\n"
        "• stand out better in the app"
    ),
}

PAYMENT_INSTRUCTIONS_TEXT = {
    "uz": (
        "Siz <b>{plan_name}</b> tarifini tanladingiz.\n\n"
        "To'lov miqdori: <b>{amount} UZS</b>\n\n"
        "Iltimos, quyidagi karta raqamiga to'lovni amalga oshiring:\n"
        "<code>{card_number}</code>\n\n"
        "To'lovni amalga oshirganingizdan so'ng, '✅ To'lov qildim' tugmasini bosing. "
        "To'lovingiz tez orada tekshiriladi va tasdiqlanadi."
    ),
    "ru": (
        "Вы выбрали тариф <b>{plan_name}</b>.\n\n"
        "Сумма к оплате: <b>{amount} UZS</b>\n\n"
        "Пожалуйста, произведите оплату на следующий номер карты:\n"
        "<code>{card_number}</code>\n\n"
        "После совершения платежа, нажмите кнопку '✅ Я оплатил'. "
        "Ваш платеж будет проверен и подтвержден в ближайшее время."
    ),
    "en": (
        "You have selected the <b>{plan_name}</b> plan.\n\n"
        "Amount to pay: <b>{amount} UZS</b>\n\n"
        "Please make the payment to the following card number:\n"
        "<code>{card_number}</code>\n\n"
        "After making the payment, press the '✅ I have paid' button. "
        "Your payment will be checked and confirmed shortly."
    ),
}

PAYMENT_CONFIRMED_TEXT = {
    "uz": "✅ To'lovingiz qabul qilindi. Premium obuna aktivlashtirish jarayoni boshlanmoqda. Tez orada sizga xabar beriladi.",
    "ru": "✅ Ваш платеж принят. Процесс активации премиум-подписки начат. Скоро вы получите уведомление.",
    "en": "✅ Your payment was received. The premium activation process has started. You will be notified shortly.",
}

PREMIUM_ALREADY_ACTIVE_TEXT = {
    "uz": "Sizda allaqachon faol premium obuna mavjud.",
    "ru": "У вас уже есть активная премиум-подписка.",
    "en": "You already have an active premium subscription.",
}

# NEW GIFT RELATED TEXTS
GIFT_CHOOSE_TYPE_TEXTS = {
    "uz": "Qanday sovg'a yubormoqchisiz?",
    "ru": "Какой подарок вы хотите отправить?",
    "en": "What kind of gift do you want to send?",
}

GIFT_ENTER_MESSAGE_TEXTS = {
    "uz": "Sovg'a bilan birga xabar yubormoqchimisiz? (Ixtiyoriy, 200 belgidan oshmasin)",
    "ru": "Хотите отправить сообщение вместе с подарком? (Необязательно, не более 200 символов)",
    "en": "Do you want to send a message with the gift? (Optional, max 200 characters)",
}

GIFT_CONFIRM_TEXTS = {
    "uz": "Siz <b>{receiver_name}</b> ga <b>{gift_type_emoji}</b> sovg'asini yubormoqchisiz.\n\n{message_text}\n\nTasdiqlaysizmi?",
    "ru": "Вы собираетесь отправить <b>{receiver_name}</b> <b>{gift_type_emoji}</b>.\n\n{message_text}\n\nПодтверждаете?",
    "en": "You are about to send <b>{receiver_name}</b> a <b>{gift_type_emoji}</b>.\n\n{message_text}\n\nConfirm?",
}

GIFT_SENT_SUCCESS_TEXTS = {
    "uz": "✅ Sovg'a <b>{receiver_name}</b> ga muvaffaqiyatli yuborildi!",
    "ru": "✅ Подарок успешно отправлен <b>{receiver_name}</b>!",
    "en": "✅ Gift successfully sent to <b>{receiver_name}</b>!",
}

GIFT_RECEIVED_NOTIFICATION_TEXTS = {
    "uz": "🎁 Sizga <b>{sender_name}</b> dan <b>{gift_type_emoji}</b> sovg'asi keldi!\n\n{message_text}",
    "ru": "🎁 Вам пришел <b>{gift_type_emoji}</b> от <b>{sender_name}</b>!\n\n{message_text}",
    "en": "🎁 You received a <b>{gift_type_emoji}</b> from <b>{sender_name}</b>!\n\n{message_text}",
}

GIFT_MESSAGE_TOO_LONG_TEXTS = {
    "uz": "Xabar juda uzun. Iltimos, 200 belgidan oshmasin.",
    "ru": "Сообщение слишком длинное. Пожалуйста, не более 200 символов.",
    "en": "Message is too long. Please keep it under 200 characters.",
}

# Plan details
PREMIUM_PLANS = {
    "gold": {"name": "Gold", "price": 30000, "duration_days": 30},
    "platinum": {"name": "Platinum", "price": 75000, "duration_days": 90},
}

@router.message(F.text == MAIN_MENU_BUTTONS["uz"]["my_profile"])
@router.message(F.text == MAIN_MENU_BUTTONS["ru"]["my_profile"])
@router.message(F.text == MAIN_MENU_BUTTONS["en"]["my_profile"])
async def show_my_profile(message: Message, state: FSMContext):
    await state.clear()  # Har ehtimolga qarshi FSM holatini tozalash

    user = await get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer(NOT_REGISTERED_TEXTS.get(language, NOT_REGISTERED_TEXTS["uz"]))
        return

    language = user.language or "uz"
    verification_checkmark = " ✅" if user.verification_status == VerificationStatus.verified else ""

    photos = await get_user_photos(user.id)

    # Qiziqishlar nomlarini olish
    interest_keys = user.interests.split(",") if user.interests else []
    interest_names = [
        ALL_INTERESTS[key.strip()].get(language, ALL_INTERESTS[key.strip()]["uz"])
        for key in interest_keys
        if key.strip() in ALL_INTERESTS
    ]

    profile_text = PROFILE_VIEW_TEXTS.get(language, PROFILE_VIEW_TEXTS["uz"]).format(
        name=user.name,
        age=user.age,
        gender=user.gender.value,  # Enum qiymatini olish
        looking_for=user.looking_for.value,  # Enum qiymatini olish
        city=user.city,
        district=user.district,
        interests=", ".join(interest_names) if interest_names else "Kiritilmagan",
        bio=user.bio if user.bio else "Kiritilmagan",
        premium_status=user.premium_plan.value,
        verification_status=user.verification_status.value,
        verification_checkmark=verification_checkmark,
    )

    if photos:
        # Birinchi rasmni caption bilan yuboramiz
        await message.answer_photo(
            photo=photos[0].file_id,
            caption=profile_text,
            reply_markup=get_profile_view_keyboard(language),
        )
        # Agar bir nechta rasm bo'lsa, qolganlarini alohida yuborish mumkin
        # for photo in photos[1:]:
        #     await message.answer_photo(photo=photo.file_id)
    else:
        await message.answer(
            profile_text, reply_markup=get_profile_view_keyboard(language)
        )


@router.callback_query(F.data == "edit_profile_menu")
async def edit_profile_menu_handler(callback: CallbackQuery, state: FSMContext):
    """'✉️ Tahrirlash' tugmasi - 'Mening profilim' ekranidan profilni tahrirlash bo'limiga o'tadi."""
    user = await get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer(NOT_REGISTERED_TEXTS["uz"], show_alert=True)
        return
    language = user.language or "uz"

    await state.set_state(EditingStates.choosing_field)
    if callback.message.photo:
        await callback.message.edit_caption(
            caption=EDIT_PROFILE_TEXTS.get(language, EDIT_PROFILE_TEXTS["uz"]),
            reply_markup=get_edit_profile_keyboard(language),
        )
    else:
        await callback.message.edit_text(
            EDIT_PROFILE_TEXTS.get(language, EDIT_PROFILE_TEXTS["uz"]),
            reply_markup=get_edit_profile_keyboard(language),
        )
    await callback.answer()


async def show_next_profile(message: Message | CallbackQuery, state: FSMContext):
    """Shows the next profile from the search queue."""
    data = await state.get_data()
    language = data.get("user_language", "uz")
    profiles_ids = data.get("profiles", [])

    if not profiles_ids:
        (message.message if isinstance(message, CallbackQuery) else message).answer( # Fix 11: Handle Message | CallbackQuery type
            NO_PROFILES_TEXTS.get(language, NO_PROFILES_TEXTS["uz"]),
            reply_markup=get_main_menu_keyboard(language)
        )
        await state.clear()
        return

    next_profile_id = profiles_ids.pop(0)
    await state.update_data(profiles=profiles_ids)

    profile_user = await get_user_by_id(next_profile_id)
    if not profile_user:
        # This user might have been deleted/banned, skip to the next one.
        await show_next_profile(message, state) # Recursive call.
        return

    photos = await get_user_photos(profile_user.id) # Fix 11: Ensure photos are fetched
    if not photos: # Should not happen due to DB query, but for safety
        await show_next_profile(message, state) # Recursive call
        return

    interest_keys = profile_user.interests.split(",") if profile_user.interests else []
    interest_names = [
        ALL_INTERESTS[key.strip()].get(language, ALL_INTERESTS[key.strip()]["uz"])
        for key in interest_keys
        if key.strip() in ALL_INTERESTS
    ]

    verification_checkmark = " ✅" if profile_user.verification_status == VerificationStatus.verified else ""
    profile_text = SEARCH_PROFILE_TEXTS.get(language, SEARCH_PROFILE_TEXTS["uz"]).format(
        name=profile_user.name,
        age=profile_user.age,
        city=profile_user.city,
        district=profile_user.district,
        interests=", ".join(interest_names) if interest_names else "Yo'q",
        bio=profile_user.bio,
        verification_checkmark=verification_checkmark,
    )

    (message.message if isinstance(message, CallbackQuery) else message).answer_photo( # Fix 11: Handle Message | CallbackQuery type
        photo=photos[0].file_id,
        caption=profile_text,
        reply_markup=get_search_keyboard(language, target_user_id=profile_user.id)
    )


async def show_next_liked_profile(message: Message | CallbackQuery, state: FSMContext):
    """Shows the next profile from the 'who liked me' queue."""
    data = await state.get_data()
    language = data.get("user_language", "uz")
    liked_profiles_ids = data.get("liked_profiles", [])

    msg_to_answer = message if isinstance(message, Message) else message.message

    if not liked_profiles_ids:
        await msg_to_answer.answer(
            NO_LIKES_TEXTS.get(language, NO_LIKES_TEXTS["uz"]),
            reply_markup=get_main_menu_keyboard(language),
        )
        await state.clear()
        if isinstance(message, CallbackQuery): await message.message.delete()
        return

    next_profile_id = liked_profiles_ids.pop(0)
    await state.update_data(liked_profiles=liked_profiles_ids)

    profile_user = await get_user_by_id(next_profile_id)
    if not profile_user or not await get_user_photos(profile_user.id):
        await show_next_liked_profile(message, state)
        return

    photos = await get_user_photos(profile_user.id)
    interest_keys = profile_user.interests.split(",") if profile_user.interests else []
    interest_names = [
        ALL_INTERESTS[key.strip()].get(language, ALL_INTERESTS[key.strip()]["uz"])
        for key in interest_keys if key.strip() in ALL_INTERESTS
    ]
    verification_checkmark = " ✅" if profile_user.verification_status == VerificationStatus.verified else ""

    profile_text = SEARCH_PROFILE_TEXTS.get(language, SEARCH_PROFILE_TEXTS["uz"]).format(
        name=profile_user.name, age=profile_user.age, city=profile_user.city, # Fix 11: Ensure profile_text is formatted
        district=profile_user.district, interests=", ".join(interest_names) or "Yo'q",
        bio=profile_user.bio, verification_checkmark=verification_checkmark
    )

    if isinstance(message, CallbackQuery):
        await message.message.delete()

    (message.message if isinstance(message, CallbackQuery) else message).answer_photo( # Fix 11: Handle Message | CallbackQuery type
        photo=photos[0].file_id,
        caption=profile_text,
        reply_markup=get_likes_keyboard(language, target_user_id=profile_user.id),
    )


@router.message(F.text.in_([MAIN_MENU_BUTTONS["uz"]["likes"], MAIN_MENU_BUTTONS["ru"]["likes"], MAIN_MENU_BUTTONS["en"]["likes"]]))
async def show_who_liked_me(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer(NOT_REGISTERED_TEXTS.get(language, NOT_REGISTERED_TEXTS["uz"]))
        return
    language = user.language or "uz"

    liked_users = await get_users_who_liked_me(user.id)
    if not liked_users:
        await message.answer(LIKES_EMPTY_TEXTS.get(language, LIKES_EMPTY_TEXTS["uz"]))
        return

    if not has_active_premium(user):
        await message.answer(
            LIKES_LOCKED_TEXTS.get(language, LIKES_LOCKED_TEXTS["uz"]).format(count=len(liked_users)),
            reply_markup=get_premium_plans_keyboard(language),
        )
        return

    liked_user_ids = [u.id for u in liked_users]
    await state.set_state(MenuStates.viewing_likes)
    await state.update_data(liked_profiles=liked_user_ids, user_language=language)
    await message.answer(LIKES_VIEW_TEXTS.get(language, LIKES_VIEW_TEXTS["uz"]))
    await show_next_liked_profile(message, state)


@router.callback_query(MenuStates.viewing_likes, F.data.startswith("like_back_"))
async def like_back_handler(callback: CallbackQuery, state: FSMContext):
    target_user_id = int(callback.data.split("_")[-1])
    await callback.answer()
    current_user = await get_user_by_telegram_id(callback.from_user.id)

    match = await add_like_and_check_match(from_user_id=current_user.id, to_user_id=target_user_id)

    if match:
        target_user = await get_user_by_id(target_user_id)
        current_user_lang = current_user.language or "uz"
        text_for_current = MATCH_NOTIFICATION_TEXTS.get(current_user_lang, MATCH_NOTIFICATION_TEXTS["uz"]).format(name=target_user.name)
        await callback.bot.send_message(chat_id=current_user.telegram_id, text=text_for_current, reply_markup=get_match_keyboard(current_user_lang, match.id))
        target_user_lang = target_user.language or "uz"
        text_for_target = MATCH_NOTIFICATION_TEXTS.get(target_user_lang, MATCH_NOTIFICATION_TEXTS["uz"]).format(name=current_user.name)
        await callback.bot.send_message(chat_id=target_user.telegram_id, text=text_for_target, reply_markup=get_match_keyboard(target_user_lang, match.id))

    await show_next_liked_profile(callback, state)


@router.callback_query(MenuStates.viewing_likes, F.data == "skip_liked_profile")
async def skip_liked_profile_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await show_next_liked_profile(callback, state)


@router.message(F.text == MAIN_MENU_BUTTONS["uz"]["search"])
@router.message(F.text == MAIN_MENU_BUTTONS["ru"]["search"])
@router.message(F.text == MAIN_MENU_BUTTONS["en"]["search"])
async def start_search(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer(NOT_REGISTERED_TEXTS.get(language, NOT_REGISTERED_TEXTS["uz"]))
        return

    language = user.language or "uz"
    await message.answer("🔍 Mos anketalar qidirilmoqda...", reply_markup=get_main_menu_keyboard(language))

    profiles = await get_profiles_for_user(user)

    if not profiles:
        await message.answer(NO_PROFILES_TEXTS.get(language, NO_PROFILES_TEXTS["uz"]))
        return

    profile_ids = [p.id for p in profiles]
    await state.set_state(MenuStates.searching)
    await state.update_data(profiles=profile_ids, user_language=language)

    await show_next_profile(message, state)


@router.callback_query(MenuStates.searching, F.data == "skip_profile")
async def skip_profile_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await show_next_profile(callback.message, state)
    await callback.answer()


@router.callback_query(MenuStates.searching, F.data.startswith("like_"))
async def like_profile_handler(callback: CallbackQuery, state: FSMContext):
    target_user_id = int(callback.data.split("_")[1])
    current_user = await get_user_by_telegram_id(callback.from_user.id)
    language = current_user.language or "uz"

    allowed, _ = await check_and_consume_like_quota(current_user.id, is_super_like=False)
    if not allowed:
        await callback.answer(LIKE_LIMIT_REACHED_TEXTS.get(language, LIKE_LIMIT_REACHED_TEXTS["uz"]), show_alert=True)
        return

    match = await add_like_and_check_match(from_user_id=current_user.id, to_user_id=target_user_id)

    await callback.answer()
    await callback.message.delete()
    await show_next_profile(callback.message, state)

    if match:
        target_user = await get_user_by_id(target_user_id)
        current_user_lang = current_user.language or "uz"
        text_for_current = MATCH_NOTIFICATION_TEXTS.get(current_user_lang, MATCH_NOTIFICATION_TEXTS["uz"]).format(name=target_user.name)
        await callback.bot.send_message(
            chat_id=current_user.telegram_id,
            text=text_for_current,
            reply_markup=get_match_keyboard(current_user_lang, match.id)
        )

        target_user_lang = target_user.language or "uz"
        text_for_target = MATCH_NOTIFICATION_TEXTS.get(target_user_lang, MATCH_NOTIFICATION_TEXTS["uz"]).format(name=current_user.name)
        await callback.bot.send_message(
            chat_id=target_user.telegram_id,
            text=text_for_target,
            reply_markup=get_match_keyboard(target_user_lang, match.id)
        )


@router.callback_query(MenuStates.searching, F.data.startswith("super_like_"))
async def super_like_profile_handler(callback: CallbackQuery, state: FSMContext):
    target_user_id = int(callback.data.split("_")[2])
    current_user = await get_user_by_telegram_id(callback.from_user.id)
    language = current_user.language or "uz"

    allowed, _ = await check_and_consume_like_quota(current_user.id, is_super_like=True)
    if not allowed:
        await callback.answer(SUPER_LIKE_LIMIT_REACHED_TEXTS.get(language, SUPER_LIKE_LIMIT_REACHED_TEXTS["uz"]), show_alert=True)
        return

    match = await add_like_and_check_match(from_user_id=current_user.id, to_user_id=target_user_id, is_super_like=True)
    await callback.answer(SUPER_LIKE_TEXTS.get(language, SUPER_LIKE_TEXTS["uz"]))
    await callback.message.delete()
    await show_next_profile(callback.message, state)

    target_user = await get_user_by_id(target_user_id)
    if target_user:
        try:
            await callback.bot.send_message(
                chat_id=target_user.telegram_id,
                text=SUPER_LIKE_NOTIFY_TEXTS.get(language, SUPER_LIKE_NOTIFY_TEXTS["uz"]).format(name=current_user.name or "Foydalanuvchi"),
            )
        except Exception as exc:
            logging.warning(f"Could not notify user about super-like: {exc}")


@router.callback_query(MenuStates.searching, F.data.startswith("block_"))
async def block_user_handler(callback: CallbackQuery, state: FSMContext):
    target_user_id = int(callback.data.split("_")[1])
    current_user = await get_user_by_telegram_id(callback.from_user.id)
    language = current_user.language or "uz"

    await block_user(blocker_id=current_user.id, blocked_id=target_user_id)
    await callback.answer(BLOCKED_USER_TEXTS.get(language, BLOCKED_USER_TEXTS["uz"]))
    await callback.message.delete()
    await show_next_profile(callback.message, state)


@router.callback_query(MenuStates.searching, F.data.startswith("report_"))
async def report_user_start(callback: CallbackQuery, state: FSMContext):
    reported_user_id = int(callback.data.split("_")[1])
    
    current_user = await get_user_by_telegram_id(callback.from_user.id)
    language = current_user.language or "uz"

    # Save the current search state before switching to reporting state
    search_data = await state.get_data()

    await state.set_state(ReportingStates.choosing_category)
    await state.update_data(
        reported_user_id=reported_user_id,
        reporter_user_id=current_user.id,
        search_data=search_data # Save previous state data
    )

    await callback.message.edit_text(
        text=REPORT_CATEGORY_PROMPT.get(language, REPORT_CATEGORY_PROMPT["uz"]),
        reply_markup=get_report_category_keyboard(language)
    )
    await callback.answer()


@router.callback_query(ReportingStates.choosing_category, F.data.startswith("report_category_"))
async def report_category_chosen(callback: CallbackQuery, state: FSMContext):
    category_name = callback.data.split("_")[-1]
    
    language = (await get_user_by_telegram_id(callback.from_user.id)).language or "uz"

    await state.update_data(category=category_name)
    await state.set_state(ReportingStates.entering_description)

    await callback.message.edit_text(
        text=REPORT_DESCRIPTION_PROMPT.get(language, REPORT_DESCRIPTION_PROMPT["uz"])
    )
    await callback.answer()


@router.message(ReportingStates.entering_description, F.text)
async def report_description_entered(message: Message, state: FSMContext):
    data = await state.get_data()
    language = (await get_user_by_telegram_id(message.from_user.id)).language or "uz"

    await create_report(
        reporter_id=data.get("reporter_user_id"),
        reported_id=data.get("reported_user_id"),
        category=ReportCategory[data.get("category")],
        description=message.text
    )

    await message.answer(REPORT_SUCCESSFULLY_SENT.get(language, REPORT_SUCCESSFULLY_SENT["uz"]))
    
    # Restore search state and continue
    search_data = data.get("search_data", {})
    await state.set_state(MenuStates.searching)
    await state.set_data(search_data)
    await show_next_profile(message, state)


# NEW GIFT HANDLERS
@router.callback_query(MenuStates.searching, F.data.startswith("gift_"))
async def start_gift_flow(callback: CallbackQuery, state: FSMContext):
    target_user_id = int(callback.data.split("_")[1])
    current_user = await get_user_by_telegram_id(callback.from_user.id)
    language = current_user.language or "uz"

    # Store target user ID and current search data
    search_data = await state.get_data()
    await state.update_data(
        target_user_id=target_user_id,
        original_search_data=search_data,
    )

    await state.set_state(MenuStates.choosing_gift_type)
    await callback.message.edit_text(
        GIFT_CHOOSE_TYPE_TEXTS.get(language, GIFT_CHOOSE_TYPE_TEXTS["uz"]),
        reply_markup=get_gift_type_keyboard(language, back_callback="gift_back_to_search")
    )
    await callback.answer()


@router.callback_query(MenuStates.choosing_gift_type, F.data == "gift_back_to_search")
async def gift_back_to_search_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    language = (await get_user_by_telegram_id(callback.from_user.id)).language or "uz"
    original_search_data = data.get("original_search_data", {})
    
    await state.set_state(MenuStates.searching)
    await state.set_data(original_search_data)
    await callback.message.delete() # Delete the gift menu
    await show_next_profile(callback.message, state) # Show the profile again
    await callback.answer()


@router.callback_query(MenuStates.choosing_gift_type, F.data.startswith("gift_type_"))
async def gift_type_chosen(callback: CallbackQuery, state: FSMContext):
    gift_type_name = callback.data.split("_")[2]
    
    language = (await get_user_by_telegram_id(callback.from_user.id)).language or "uz"

    await state.update_data(gift_type=gift_type_name)
    await state.set_state(MenuStates.entering_gift_message)

    await callback.message.edit_text(
        GIFT_ENTER_MESSAGE_TEXTS.get(language, GIFT_ENTER_MESSAGE_TEXTS["uz"]),
        reply_markup=get_back_only_keyboard(language, "gift_back_to_choose_type")
    )
    await callback.answer()


@router.callback_query(MenuStates.entering_gift_message, F.data == "gift_back_to_choose_type")
async def gift_back_to_choose_type_handler(callback: CallbackQuery, state: FSMContext):
    language = (await get_user_by_telegram_id(callback.from_user.id)).language or "uz"
    await state.set_state(MenuStates.choosing_gift_type)
    await callback.message.edit_text(
        GIFT_CHOOSE_TYPE_TEXTS.get(language, GIFT_CHOOSE_TYPE_TEXTS["uz"]),
        reply_markup=get_gift_type_keyboard(language, back_callback="gift_back_to_search")
    )
    await callback.answer()


@router.message(MenuStates.entering_gift_message, F.text)
async def gift_message_entered(message: Message, state: FSMContext):
    data = await state.get_data()
    language = (await get_user_by_telegram_id(message.from_user.id)).language or "uz"
    
    gift_message = message.text
    if len(gift_message) > 200:
        await message.answer(GIFT_MESSAGE_TOO_LONG_TEXTS.get(language, GIFT_MESSAGE_TOO_LONG_TEXTS["uz"]))
        return

    await state.update_data(gift_message=gift_message)
    await state.set_state(MenuStates.confirming_gift)

    target_user_id = data.get("target_user_id")
    target_user = await get_user_by_id(target_user_id)
    gift_type_name = data.get("gift_type")
    gift_type_emoji = GIFT_BUTTON_TEXTS.get(language, GIFT_BUTTON_TEXTS["uz"]).get(gift_type_name, "")

    confirm_text = GIFT_CONFIRM_TEXTS.get(language, GIFT_CONFIRM_TEXTS["uz"]).format(
        receiver_name=target_user.name,
        gift_type_emoji=gift_type_emoji,
        message_text=f"<b>Xabar:</b> <i>{gift_message}</i>" if gift_message else "Xabar yo'q."
    )
    
    confirm_keyboard_texts = {
        "uz": {"confirm": "✅ Yuborish", "cancel": "❌ Bekor qilish"},
        "ru": {"confirm": "✅ Отправить", "cancel": "❌ Отмена"},
        "en": {"confirm": "✅ Send", "cancel": "❌ Cancel"},
    }
    texts = confirm_keyboard_texts.get(language, confirm_keyboard_texts["uz"]) # Error 8: The back button was missing here.
    confirm_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=texts["confirm"], callback_data="gift_confirm_send")],
        [InlineKeyboardButton(text=texts["cancel"], callback_data="gift_cancel_send")],
        get_back_only_keyboard(language, "gift_back_to_message_entry").inline_keyboard[0] # Add back button
    ])
    
    await message.answer(confirm_text, reply_markup=confirm_keyboard)


@router.callback_query(MenuStates.confirming_gift, F.data == "gift_cancel_send")
async def gift_cancel_send_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    language = (await get_user_by_telegram_id(callback.from_user.id)).language or "uz"
    original_search_data = data.get("original_search_data", {})
    
    await state.set_state(MenuStates.searching)
    await state.set_data(original_search_data)
    await callback.message.delete() # Delete the gift confirmation message
    await show_next_profile(callback.message, state) # Show the profile again
    await callback.answer("Sovg'a yuborish bekor qilindi.")


@router.callback_query(MenuStates.confirming_gift, F.data == "gift_confirm_send")
async def gift_confirm_send_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    sender_user = await get_user_by_telegram_id(callback.from_user.id)
    language = sender_user.language or "uz"

    target_user_id = data.get("target_user_id")
    gift_type_name = data.get("gift_type")
    gift_message = data.get("gift_message")

    receiver_user = await get_user_by_id(target_user_id)
    if not receiver_user:
        await callback.answer("Xatolik: Sovg'a qabul qiluvchi foydalanuvchi topilmadi.", show_alert=True)
        await callback.message.delete()
        await show_next_profile(callback.message, state)
        return

    # Create gift record in DB
    await create_gift(
        sender_id=sender_user.id,
        receiver_id=receiver_user.id,
        gift_type=GiftType[gift_type_name],
        message=gift_message,
    )

    # Notify receiver
    gift_type_emoji = GIFT_BUTTON_TEXTS.get(receiver_user.language or "uz", GIFT_BUTTON_TEXTS["uz"]).get(gift_type_name, "")
    notification_text = GIFT_RECEIVED_NOTIFICATION_TEXTS.get(receiver_user.language or "uz", GIFT_RECEIVED_NOTIFICATION_TEXTS["uz"]).format(
        sender_name=sender_user.name,
        gift_type_emoji=gift_type_emoji,
        message_text=f"<b>Xabar:</b> <i>{gift_message}</i>" if gift_message else "Xabar yo'q."
    )
    try:
        await bot.send_message(chat_id=receiver_user.telegram_id, text=notification_text)
    except Exception as exc:
        logging.warning(f"Could not notify user {receiver_user.telegram_id} about received gift: {exc}")

    await callback.message.delete()
    await callback.message.answer(
        GIFT_SENT_SUCCESS_TEXTS.get(language, GIFT_SENT_SUCCESS_TEXTS["uz"]).format(receiver_name=receiver_user.name)
    )
    
    # Restore search state and continue
    original_search_data = data.get("original_search_data", {})
    await state.set_state(MenuStates.searching)
    await state.set_data(original_search_data)
    await show_next_profile(callback.message, state)
    await callback.answer()


@router.message(F.text == MAIN_MENU_BUTTONS["uz"]["referrals"])
@router.message(F.text == MAIN_MENU_BUTTONS["ru"]["referrals"])
@router.message(F.text == MAIN_MENU_BUTTONS["en"]["referrals"])
async def show_referral_info(message: Message, state: FSMContext, bot: Bot):
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer(NOT_REGISTERED_TEXTS.get(language, NOT_REGISTERED_TEXTS["uz"]))
        return
    language = user.language or "uz"

    referrals = await get_user_referrals(user.id)
    referral_count = len(referrals)

    bot_info = await bot.get_me()
    bot_username = bot_info.username

    referral_text = REFERRAL_TEXTS.get(language, REFERRAL_TEXTS["uz"]).format(
        bot_username=bot_username, user_id=user.id, referral_count=referral_count
    )
    await message.answer(referral_text)
    await state.set_state(MenuStates.viewing_referrals)


@router.message(F.text == MAIN_MENU_BUTTONS["uz"]["help"])
@router.message(F.text == MAIN_MENU_BUTTONS["ru"]["help"])
@router.message(F.text == MAIN_MENU_BUTTONS["en"]["help"])
async def help_main_menu(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer(NOT_REGISTERED_TEXTS.get(language, NOT_REGISTERED_TEXTS["uz"]))
        return
    language = user.language or "uz"

    await message.answer(
        HELP_MAIN_TEXT.get(language, HELP_MAIN_TEXT["uz"]),
        reply_markup=get_help_keyboard(language)
    )
    await state.set_state(MenuStates.viewing_help)


@router.callback_query(MenuStates.viewing_help, F.data == "help_faq")
async def show_faq(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = user.language or "uz"

    await callback.message.edit_text(
        FAQ_TEXT.get(language, FAQ_TEXT["uz"]),
        reply_markup=get_help_keyboard(language)
    )
    await callback.answer()


@router.callback_query(MenuStates.viewing_help, F.data == "help_contact_support")
async def show_contact_support(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = user.language or "uz"

    await callback.message.edit_text(
        CONTACT_SUPPORT_TEXT.get(language, CONTACT_SUPPORT_TEXT["uz"]),
        reply_markup=get_help_keyboard(language)
    )
    await callback.answer()


@router.callback_query(MenuStates.viewing_help, F.data == "help_back_to_main_menu")
async def help_back_to_main_menu_handler(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = user.language or "uz"
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        MAIN_MENU_TEXTS.get(language, MAIN_MENU_TEXTS["uz"]),
        reply_markup=get_main_menu_keyboard(language)
    )
    await callback.answer()

MESSAGE_ADMIN_PROMPT_TEXTS = {
    "uz": "✉️ Taklif yoki shikoyatingizni yozib yuboring. Xabaringiz to'g'ridan-to'g'ri administratorga yetkaziladi.",
    "ru": "✉️ Напишите ваше предложение или жалобу. Ваше сообщение будет напрямую передано администратору.",
    "en": "✉️ Write your suggestion or complaint. Your message will be sent directly to the administrator.",
}

MESSAGE_ADMIN_SENT_TEXTS = {
    "uz": "✅ Xabaringiz administratorga yuborildi. Tez orada bog'lanamiz!",
    "ru": "✅ Ваше сообщение отправлено администратору. Мы скоро свяжемся с вами!",
    "en": "✅ Your message has been sent to the administrator. We will contact you soon!",
}


@router.callback_query(MenuStates.viewing_help, F.data == "help_message_admin")
async def start_message_admin(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer(NOT_REGISTERED_TEXTS.get(language, NOT_REGISTERED_TEXTS["uz"]), show_alert=True)
        return
    language = user.language or "uz"

    await state.set_state(MenuStates.writing_to_admin)
    await callback.message.edit_text(MESSAGE_ADMIN_PROMPT_TEXTS.get(language, MESSAGE_ADMIN_PROMPT_TEXTS["uz"]))
    await callback.answer()


@router.message(MenuStates.writing_to_admin, F.text)
async def message_admin_received(message: Message, state: FSMContext, bot: Bot):
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user:
        await state.clear() # Clear state if user is not registered
        await message.answer(NOT_REGISTERED_TEXTS.get(language, NOT_REGISTERED_TEXTS["uz"]))
        return
    language = user.language or "uz"

    await create_support_message(user.id, message.text)

    username_part = f"@{message.from_user.username}" if message.from_user.username else "yo'q"
    notify_text = (
        f"✉️ <b>Yangi murojaat</b>\n\n"
        f"Foydalanuvchi: {user.name} (ID: {user.id})\n"
        f"Username: {username_part} | Telegram ID: {user.telegram_id}\n\n"
        f"Xabar:\n{message.text}"
    )
    admin_ids = await get_all_admin_ids()
    for admin_id in admin_ids:
        try:
            await bot.send_message(chat_id=admin_id, text=notify_text)
        except Exception as exc:
            logging.warning(f"Could not notify admin {admin_id} about support message: {exc}")

    await state.clear()
    await message.answer(
        MESSAGE_ADMIN_SENT_TEXTS.get(language, MESSAGE_ADMIN_SENT_TEXTS["uz"]),
        reply_markup=get_main_menu_keyboard(language)
    )

@router.message(F.text == MAIN_MENU_BUTTONS["uz"]["settings"])
@router.message(F.text == MAIN_MENU_BUTTONS["ru"]["settings"])
@router.message(F.text == MAIN_MENU_BUTTONS["en"]["settings"])
async def settings_main_menu(message: Message, state: FSMContext):
    await state.clear()
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer(NOT_REGISTERED_TEXTS["uz"])
        return
    language = user.language or "uz"

    await message.answer(
        SETTINGS_MAIN_TEXT.get(language, SETTINGS_MAIN_TEXT["uz"]),
        reply_markup=get_settings_keyboard(language, user.status == UserStatus.inactive, user.verification_status.name)
    )
    await state.set_state(SettingsStates.main_menu)


@router.callback_query(SettingsStates.main_menu, F.data == "settings_hide_profile")
async def hide_profile_handler(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = user.language or "uz"

    await update_user_profile_field(user.id, "status", UserStatus.inactive)
    await callback.message.edit_text(
        PROFILE_HIDDEN_TEXT.get(language, PROFILE_HIDDEN_TEXT["uz"]),
        reply_markup=get_settings_keyboard(language, is_profile_hidden=True, verification_status=user.verification_status.name)
    )
    await callback.answer()


@router.callback_query(SettingsStates.main_menu, F.data == "settings_show_profile")
async def show_profile_handler(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = user.language or "uz"

    await update_user_profile_field(user.id, "status", UserStatus.active)
    await callback.message.edit_text(
        PROFILE_SHOWN_TEXT.get(language, PROFILE_SHOWN_TEXT["uz"]),
        reply_markup=get_settings_keyboard(language, is_profile_hidden=False, verification_status=user.verification_status.name)
    )
    await callback.answer()


@router.callback_query(SettingsStates.main_menu, F.data == "settings_change_language")
async def change_language_start(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = user.language or "uz"

    await callback.message.edit_text(
        CHANGE_LANGUAGE_PROMPT.get(language, CHANGE_LANGUAGE_PROMPT["uz"]),
        reply_markup=get_language_keyboard()
    )
    await state.set_state(SettingsStates.choosing_language)
    await callback.answer()


@router.callback_query(SettingsStates.choosing_language, F.data.startswith("lang_"))
async def language_changed_from_settings(callback: CallbackQuery, state: FSMContext):
    new_language = callback.data.split("_")[1]
    user = await get_user_by_telegram_id(callback.from_user.id)

    await set_user_language(user.id, new_language)

    await callback.message.edit_text(
        LANGUAGE_CHANGED_TEXT.get(new_language, LANGUAGE_CHANGED_TEXT["uz"]),
        reply_markup=get_settings_keyboard(new_language, user.status == UserStatus.inactive, user.verification_status.name)
    )
    await state.set_state(SettingsStates.main_menu)
    await callback.answer()


@router.callback_query(SettingsStates.main_menu, F.data == "settings_delete_account")
async def delete_account_confirm(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = user.language or "uz"

    await callback.message.edit_text(
        DELETE_ACCOUNT_CONFIRM_TEXT.get(language, DELETE_ACCOUNT_CONFIRM_TEXT["uz"]),
        reply_markup=get_confirm_delete_account_keyboard(language)
    )
    await state.set_state(SettingsStates.confirm_delete_account)
    await callback.answer()


@router.callback_query(SettingsStates.confirm_delete_account, F.data == "confirm_delete_yes")
async def delete_account_handler(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = user.language or "uz"

    await delete_user_data(user.id)
    await state.clear()
    await callback.message.edit_text(ACCOUNT_DELETED_TEXT.get(language, ACCOUNT_DELETED_TEXT["uz"]))
    await callback.answer()


@router.callback_query(SettingsStates.confirm_delete_account, F.data == "confirm_delete_no")
@router.callback_query(SettingsStates.main_menu, F.data == "settings_back_to_main_menu")
@router.callback_query(F.data == "premium_back_to_main_menu")
async def settings_back_to_main_menu_handler(callback: CallbackQuery, state: FSMContext):
    # This handler is also used by premium menu's back button
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = user.language if user else "uz"
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        MAIN_MENU_TEXTS.get(language, MAIN_MENU_TEXTS["uz"]),
        reply_markup=get_main_menu_keyboard(language)
    )
    await callback.answer()


@router.callback_query(SettingsStates.main_menu, F.data == "settings_verify_account")
async def start_verification_handler(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = user.language or "uz"

    if user.verification_status == VerificationStatus.verified:
        await callback.answer(VERIFICATION_ALREADY_VERIFIED_TEXT.get(language, VERIFICATION_ALREADY_VERIFIED_TEXT["uz"]), show_alert=True)
        return
    if user.verification_status == VerificationStatus.in_progress:
        await callback.answer(VERIFICATION_IN_PROGRESS_TEXT.get(language, VERIFICATION_IN_PROGRESS_TEXT["uz"]), show_alert=True)
        return

    await state.set_state(VerificationStates.uploading_document)
    await callback.message.edit_text(VERIFICATION_START_TEXT.get(language, VERIFICATION_START_TEXT["uz"]))
    await callback.answer()

@router.message(VerificationStates.uploading_document, F.photo)
async def verification_document_uploaded(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    language = user.language or "uz"

    file_id = message.photo[-1].file_id
    await create_verification_request(user.id, file_id)

    await message.answer(
        VERIFICATION_SUBMITTED_TEXT.get(language, VERIFICATION_SUBMITTED_TEXT["uz"]),
        reply_markup=get_main_menu_keyboard(language)
    )
    await state.clear()

@router.message(VerificationStates.uploading_document, ~F.photo)
async def verification_document_invalid(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    language = user.language or "uz"
    await message.answer(VERIFICATION_START_TEXT.get(language, VERIFICATION_START_TEXT["uz"]))


@router.message(F.text == MAIN_MENU_BUTTONS["uz"]["chats"])
@router.message(F.text == MAIN_MENU_BUTTONS["ru"]["chats"])
@router.message(F.text == MAIN_MENU_BUTTONS["en"]["chats"])
async def my_chats_handler(message: Message, state: FSMContext):
    await state.clear()
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer(NOT_REGISTERED_TEXTS["uz"])
        return
    language = user.language or "uz"

    matches = await get_user_matches(user.id)

    if not matches:
        await message.answer(NO_CHATS_TEXTS.get(language, NO_CHATS_TEXTS["uz"]))
        return

    chats_data = []
    for match in matches:
        partner_id = match.user1_id if match.user1_id != user.id else match.user2_id
        partner = await get_user_by_id(partner_id)
        if partner:
            chats_data.append((match.id, partner.name, partner.verification_status))

    if not chats_data:
        await message.answer(NO_CHATS_TEXTS.get(language, NO_CHATS_TEXTS["uz"]))
        return

    await message.answer(
        CHATS_LIST_TEXTS.get(language, CHATS_LIST_TEXTS["uz"]),
        reply_markup=get_chats_keyboard(language, chats_data)
    )


@router.callback_query(F.data.startswith("start_chat_") | F.data.startswith("open_chat_"))
async def open_chat_handler(callback: CallbackQuery, state: FSMContext):
    match_id = int(callback.data.split("_")[-1])

    current_user = await get_user_by_telegram_id(callback.from_user.id)
    language = current_user.language or "uz"

    match = await get_match_by_id(match_id)
    if not match or (current_user.id not in [match.user1_id, match.user2_id]):
        await callback.answer("Bu suhbat topilmadi yoki faol emas.", show_alert=True)
        return

    partner_db_id = match.user1_id if match.user1_id != current_user.id else match.user2_id
    partner = await get_user_by_id(partner_db_id)
    verification_checkmark = " ✅" if partner.verification_status == VerificationStatus.verified else ""

    await state.set_state(MenuStates.in_chat)
    await state.update_data(
        match_id=match.id,
        partner_telegram_id=partner.telegram_id,
        current_user_id=current_user.id
    )

    await callback.message.answer( # Changed to pass verification_checkmark
        IN_CHAT_TEXTS.get(language, IN_CHAT_TEXTS["uz"]).format(name=partner.name, verification_checkmark=verification_checkmark),
        reply_markup=ReplyKeyboardRemove(),
    )
    await callback.answer()


@router.message(MenuStates.in_chat, Command("stopchat"))
async def stop_chat_handler(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    language = user.language or "uz"

    await state.clear()
    await message.answer(
        STOP_CHAT_TEXTS.get(language, STOP_CHAT_TEXTS["uz"]),
        reply_markup=get_main_menu_keyboard(language)
    )


@router.message(MenuStates.in_chat, F.text)
async def message_in_chat_handler(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    partner_telegram_id = data.get("partner_telegram_id")
    match_id = data.get("match_id")
    current_user_id = data.get("current_user_id")

    await create_chat_message(match_id=match_id, sender_id=current_user_id, text=message.text)

    try:
        await bot.send_message(chat_id=partner_telegram_id, text=message.text)
    except Exception as e:
        logging.warning(f"Error sending message to {partner_telegram_id} in chat {match_id}: {e}")
        await message.answer("Xabarni yuborib bo'lmadi. Suhbatdoshingiz botni tark etgan bo'lishi mumkin.")


@router.message(F.text == MAIN_MENU_BUTTONS["uz"]["premium"])
@router.message(F.text == MAIN_MENU_BUTTONS["ru"]["premium"])
@router.message(F.text == MAIN_MENU_BUTTONS["en"]["premium"])
async def premium_main_menu(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer(NOT_REGISTERED_TEXTS.get(language, NOT_REGISTERED_TEXTS["uz"]))
        return
    language = user.language or "uz"

    # Check if user already has an active premium plan
    if has_active_premium(user):
        like_limit = DAILY_LIKE_LIMITS.get(user.premium_plan)
        super_like_limit = DAILY_SUPER_LIKE_LIMITS.get(user.premium_plan)
        await message.answer(
            PREMIUM_DASHBOARD_TEXTS.get(language, PREMIUM_DASHBOARD_TEXTS["uz"]).format(
                plan=user.premium_plan.value,
                expires_at=user.premium_expires_at.strftime("%Y-%m-%d"),
                like_limit="♾️" if like_limit is None else like_limit,
                super_like_limit="♾️" if super_like_limit is None else super_like_limit,
            ),
            reply_markup=get_premium_dashboard_keyboard(language),
        )
        return

    await state.set_state(PremiumStates.choosing_plan)
    await message.answer(
        f"{PREMIUM_MAIN_TEXT.get(language, PREMIUM_MAIN_TEXT['uz'])}\n\n{PREMIUM_BENEFITS_TEXT.get(language, PREMIUM_BENEFITS_TEXT['uz'])}",
        reply_markup=get_premium_plans_keyboard(language)
    )


@router.callback_query(F.data == "activate_boost")
async def activate_boost_handler(callback: CallbackQuery):
    user = await get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer(NOT_REGISTERED_TEXTS.get(language, NOT_REGISTERED_TEXTS["uz"]), show_alert=True)
        return
    language = user.language or "uz"

    if not has_active_premium(user):
        await callback.answer(PREMIUM_REQUIRED_TEXTS.get(language, PREMIUM_REQUIRED_TEXTS["uz"]), show_alert=True)
        return

    expires_at = await activate_profile_boost(user.id)
    if expires_at:
        await callback.answer()
        await callback.message.answer(
            BOOST_ACTIVATED_TEXTS.get(language, BOOST_ACTIVATED_TEXTS["uz"]).format(minutes=BOOST_DURATION_MINUTES)
        )
    else:
        await callback.answer("Xatolik yuz berdi.", show_alert=True)


@router.callback_query(PremiumStates.choosing_plan, F.data.startswith("premium_plan_"))
async def select_premium_plan(callback: CallbackQuery, state: FSMContext):
    plan = callback.data.split("_")[-1] # gold or platinum
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = user.language or "uz"

    plan_details = PREMIUM_PLANS.get(plan)
    if not plan_details:
        await callback.answer("Tarif topilmadi.", show_alert=True)
        return

    await state.set_state(PremiumStates.confirming_payment)
    
    text = PAYMENT_INSTRUCTIONS_TEXT.get(language, PAYMENT_INSTRUCTIONS_TEXT["uz"]).format(
        plan_name=plan_details["name"],
        amount=f"{plan_details['price']:,}".replace(",", " "),
        card_number=PAYMENT_CARD_NUMBER
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_payment_confirmation_keyboard(language, plan)
    )
    await callback.answer()


@router.callback_query(PremiumStates.confirming_payment, F.data.startswith("payment_confirm_"))
async def confirm_payment(callback: CallbackQuery, state: FSMContext):
    plan = callback.data.split("_")[-1]
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = user.language or "uz"

    plan_details = PREMIUM_PLANS.get(plan)
    if not plan_details:
        await callback.answer("Tarif topilmadi.", show_alert=True)
        return

    await create_payment_record(user_id=user.id, amount=plan_details["price"], plan_name=plan_details["name"])

    await callback.message.edit_text(PAYMENT_CONFIRMED_TEXT.get(language, PAYMENT_CONFIRMED_TEXT["uz"]))
    await state.clear()
    await callback.answer()


@router.message(F.text.in_(set(all_menu_buttons)))  # Bu handler endi faqat boshqa tugmalar uchun ishlaydi
async def handle_other_menu_buttons(message: Message, state: FSMContext): # This handler is now a fallback
    """Fallback handler for any main menu buttons without a dedicated handler."""
    await message.answer(f"'{message.text}' bo'limi vaqtincha mavjud emas.")