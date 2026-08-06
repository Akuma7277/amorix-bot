from datetime import datetime, timedelta
import logging
from aiogram import F, Router, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, InputMediaPhoto
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from reply import (
    get_admin_main_menu_keyboard, ADMIN_MENU_BUTTONS, get_main_menu_keyboard
)
from inline import get_moderation_keyboard, get_user_management_keyboard, get_report_keyboard, get_verification_moderation_keyboard, get_payment_moderation_keyboard, get_logs_view_keyboard, get_log_filter_keyboard, get_log_action_filter_keyboard, get_profile_approval_keyboard, get_manage_admins_keyboard, get_ban_duration_keyboard, get_delete_confirmation_keyboard
from states import AdminStates
from crud import (
    get_bot_statistics, get_user_by_telegram_id, get_unapproved_photo, get_all_active_user_telegram_ids, get_payment_statistics,
    find_user_by_id_or_telegram_id, set_user_status, ban_user_with_duration, lift_user_ban, delete_user_data,
    auto_lift_expired_ban, get_user_photos, get_pending_report, update_report_status, get_photo_by_id,
    get_user_by_id, get_pending_payment, update_payment_status, get_pending_verification_request,
    update_verification_request_status, create_admin_log, approve_photo, reject_photo, get_report_by_id,
    get_admin_logs, update_user_profile_field, is_admin_user, add_admin_by_telegram_id, remove_admin_by_telegram_id,
    get_dynamic_admins, set_setting, get_setting,
)
from models import UserStatus, ReportStatus, ActionType, VerificationStatus, PremiumPlan
from menu import PROFILE_VIEW_TEXTS, PREMIUM_MAIN_TEXT
from registration import ALL_INTERESTS

# ... (rest of the file) ...

router = Router()

LOGS_PAGE_SIZE = 10

UNAUTHORIZED_ACCESS_TEXT = {
    "uz": "Sizda admin paneliga kirish huquqi yo'q.",
    "ru": "У вас нет доступа к админ-панели.",
    "en": "You do not have access to the admin panel.",
}

STATISTICS_TEXT = {
    "uz": (
        "📊 <b>Bot statistikasi:</b>

"
        "Jami foydalanuvchilar: {total_users}
"
        "Bugun ro'yxatdan o'tganlar: {registered_today}
"
        "Faol foydalanuvchilar: {active_users}
"
        "Jami matchlar: {total_matches}
"
        "Premium foydalanuvchilar: {premium_users}"
    ),
    "ru": (
        "📊 <b>Статистика бота:</b>

"
        "Всего пользователей: {total_users}
"
        "Зарегистрировано сегодня: {registered_today}
"
        "Активных пользователей: {active_users}
"
        "Всего совпадений: {total_matches}
"
        "Премиум пользователи: {premium_users}"
    ),
    "en": (
        "📊 <b>Bot Statistics:</b>

"
        "Total users: {total_users}
"
        "Registered today: {registered_today}
"
        "Active users: {active_users}
"
        "Total matches: {total_matches}
"
        "Premium users: {premium_users}"
    ),
}

NO_PHOTOS_TO_MODERATE_TEXT = {
    "uz": "Hozircha moderatsiya uchun rasmlar yo'q. Asosiy menyuga qaytishingiz mumkin.",
    "ru": "На данный момент нет фотографий для модерации. Можете вернуться в главное меню.",
    "en": "There are no photos for moderation at the moment. You can return to the main menu.",
}

PHOTO_MODERATION_CAPTION = {
    "uz": "Foydalanuvchi: {user_name} (ID: {user_id})
Telegram ID: `{telegram_id}`",
    "ru": "Пользователь: {user_name} (ID: {user_id})
Telegram ID: `{telegram_id}`",
    "en": "User: {user_name} (ID: {user_id})
Telegram ID: `{telegram_id}`",
}

PHOTO_APPROVED_TEXT = {
    "uz": "✅ Rasm tasdiqlandi. Keyingisi ko'rsatilmoqda...",
    "ru": "✅ Фото одобрено. Показываю следующее...",
    "en": "✅ Photo approved. Showing next...",
}

PHOTO_REJECTED_TEXT = {
    "uz": "❌ Rasm rad etildi. Keyingisi ko'rsatilmoqda...",
    "ru": "❌ Фото отклонено. Показываю следующее...",
    "en": "❌ Photo rejected. Showing next...",
}

USER_BAN_WIP_TEXT = {
    "uz": "Foydalanuvchini bloklash funksiyasi ishlab chiqilmoqda.",
    "ru": "Функция блокировки пользователя в разработке.",
    "en": "User banning feature is under development.",
}

USER_SEARCH_PROMPT_TEXT = {
    "uz": "Foydalanuvchining Telegram ID yoki DB ID raqamini kiriting:",
    "ru": "Введите Telegram ID или ID базы данных пользователя:",
    "en": "Enter the user's Telegram ID or DB ID:",
}

USER_NOT_FOUND_TEXT = {
    "uz": "Bunday ID raqamli foydalanuvchi topilmadi.",
    "ru": "Пользователь с таким ID не найден.",
    "en": "User with this ID was not found.",
}

USER_BANNED_TEXT = "🚫 Foydalanuvchi bloklandi va endi botda ko'rinmaydi."
USER_UNBANNED_TEXT = "✅ Foydalanuvchi blokdan chiqarildi."
PROFILE_DELETED_TEXT = {
    "uz": "🗑 Profil butunlay o'chirildi.",
    "ru": "🗑 Профиль полностью удален.",
    "en": "🗑 The profile has been permanently deleted.",
}

USER_MANAGEMENT_TEXT = {
    "uz": "Foydalanuvchini boshqarish:",
    "ru": "Управление пользователем:",
    "en": "User management:",
}

BAN_NOTICE_TEXT = {
    "uz": "🚫 Sizning hisobingiz {until} sanasigacha vaqtincha bloklandi.",
    "ru": "🚫 Ваш аккаунт временно заблокирован до {until}.",
    "en": "🚫 Your account has been temporarily banned until {until}.",
}

BAN_NOTICE_PERMANENT_TEXT = {
    "uz": "🚫 Sizning hisobingiz doimiy ravishda bloklandi.",
    "ru": "🚫 Ваш аккаунт заблокирован навсегда.",
    "en": "🚫 Your account has been permanently banned.",
}

PROFILE_DELETED_NOTICE_TEXT = {
    "uz": "🗑 Sizning profilingiz administrator tomonidan o'chirildi. Qayta ro'yxatdan o'tish uchun /start buyrug'ini bosing.",
    "ru": "🗑 Ваш профиль был удален администратором. Чтобы зарегистрироваться заново, нажмите /start.",
    "en": "🗑 Your profile has been deleted by an administrator. Press /start to register again.",
}

REPORT_DETAILS_TEXT = {
    "uz": (
        "<b>❗️ Yangi shikoyat</b>

"
        "<b>Shikoyatchi:</b> {reporter_name} (ID: {reporter_id})
"
        "<b>Ayblanuvchi:</b> {reported_name} (ID: {reported_id})
"
        "<b>Sana:</b> {report_date}

"
        "<b>Kategoriya:</b> {category}
"
        "<b>Tavsif:</b>
{description}"
    ),
    "ru": (
        "<b>❗️ Новая жалоба</b>

"
        "<b>Жалобщик:</b> {reporter_name} (ID: {reporter_id})
"
        "<b>Обвиняемый:</b> {reported_name} (ID: {reported_id})
"
        "<b>Дата:</b> {report_date}

"
        "<b>Категория:</b> {category}
"
        "<b>Описание:</b>
{description}"
    ),
    "en": (
        "<b>❗️ New Report</b>

"
        "<b>Reporter:</b> {reporter_name} (ID: {reporter_id})
"
        "<b>Reported:</b> {reported_name} (ID: {reported_id})
"
        "<b>Date:</b> {report_date}

"
        "<b>Category:</b> {category}
"
        "<b>Description:</b>
{description}"
    ),
}

NO_REPORTS_TEXT = {
    "uz": "Hozircha ko'rib chiqilmagan shikoyatlar yo'q.",
    "ru": "На данный момент нет нерассмотренных жалоб.",
    "en": "There are no pending reports at the moment.",
}

REPORT_RESOLVED_TEXT = "✅ Shikoyat 'hal qilindi' deb belgilandi."
REPORT_REJECTED_TEXT = "❌ Shikoyat 'rad etildi' deb belgilandi."
REPORT_USER_BANNED_TEXT = "🚫 Foydalanuvchi bloklandi va shikoyat 'hal qilindi' deb belgilandi."

BROADCAST_MESSAGE_PROMPT = {
    "uz": "Barcha faol foydalanuvchilarga yubormoqchi bo'lgan xabaringizni kiriting:",
    "ru": "Введите сообщение, которое вы хотите отправить всем активным пользователям:",
    "en": "Enter the message you want to send to all active users:",
}

BROADCAST_CONFIRMATION_TEXT = {
    "uz": "Ushbu xabarni {user_count} ta foydalanuvchiga yuborishni tasdiqlaysizmi?

<b>Xabar:</b>
{message_text}",
    "ru": "Вы подтверждаете отправку этого сообщения {user_count} пользователям?

<b>Сообщение:</b>
{message_text}",
    "en": "Do you confirm sending this message to {user_count} users?

<b>Message:</b>
{message_text}",
}

BROADCAST_SENT_SUCCESS = {
    "uz": "✅ Xabar muvaffaqiyatli yuborildi!",
    "ru": "✅ Сообщение успешно отправлено!",
    "en": "✅ Message sent successfully!",
}

BROADCAST_CANCELLED = {
    "uz": "Broadcast bekor qilindi.",
    "ru": "Рассылка отменена.",
    "en": "Broadcast cancelled.",
}

TARIFFS_PAYMENTS_TEXT = {
    "uz": (
        "💰 <b>Tariflar va to'lovlar statistikasi:</b>

"
        "Jami premium obunalar: {total_premium_subscriptions}
"
        "Faol obunalar: {active_subscriptions}
"
        "Jami tushum (yakunlangan to'lovlar): {total_revenue} UZS"
    ),
    "ru": (
        "💰 <b>Статистика тарифов и платежей:</b>

"
        "Всего премиум подписок: {total_premium_subscriptions}
"
        "Активных подписок: {active_subscriptions}
"
        "Общий доход (завершенные платежи): {total_revenue} UZS"
    ),
    "en": (
        "💰 <b>Tariffs and Payments Statistics:</b>

"
        "Total premium subscriptions: {total_premium_subscriptions}
"
        "Active subscriptions: {active_subscriptions}
"
        "Total revenue (completed payments): {total_revenue} UZS"
    ),
}

VERIFICATION_MODERATION_CAPTION = {
    "uz": "Foydalanuvchi: {user_name} (ID: {user_id})
Telegram ID: `{telegram_id}`
So'rov yuborilgan sana: {request_date}",
    "ru": "Пользователь: {user_name} (ID: {user_id})
Telegram ID: `{telegram_id}`
Дата запроса: {request_date}",
    "en": "User: {user_name} (ID: {user_id})
Telegram ID: `{telegram_id}`
Request date: {request_date}",
}

NO_VERIFICATIONS_TO_MODERATE_TEXT = {
    "uz": "Hozircha moderatsiya uchun verifikatsiya so'rovlari yo'q.",
    "ru": "На данный момент нет запросов на верификацию для модерации.",
    "en": "There are no verification requests for moderation at the moment.",
}

VERIFICATION_APPROVED_TEXT = "✅ Verifikatsiya tasdiqlandi."
VERIFICATION_REJECTED_TEXT = "❌ Verifikatsiya rad etildi."

USER_NOTIFIED_VERIFIED_TEXT = {
    "uz": "🎉 Tabriklaymiz! Sizning hisobingiz muvaffaqiyatli tasdiqlandi (verifikatsiya qilindi).",
    "ru": "🎉 Поздравляем! Ваш аккаунт успешно верифицирован.",
    "en": "🎉 Congratulations! Your account has been successfully verified.",
}

USER_NOTIFIED_REJECTED_TEXT = {
    "uz": "😔 Afsuski, sizning verifikatsiya so'rovingiz rad etildi. Sabab: hujjat sifati past yoki ma'lumotlar mos kelmadi. Iltimos, qayta urinib ko'ring.",
    "ru": "😔 К сожалению, ваш запрос на верификацию был отклонен. Причина: низкое качество документа или несоответствие данных. Пожалуйста, попробуйте еще раз.",
    "en": "😔 Unfortunately, your verification request was rejected. Reason: low document quality or mismatched information. Please try again.",
}

PAYMENT_MODERATION_TEXT = {
    "uz": (
        "<b>💳 Yangi to'lov so'rovi</b>

"
        "<b>Foydalanuvchi:</b> {user_name} (ID: {user_id})
"
        "<b>Telegram ID:</b> `{telegram_id}`
"
        "<b>Sana:</b> {payment_date}

"
        "<b>Tarif:</b> {plan_name}
"
        "<b>Summa:</b> {amount} UZS"
    ),
    "ru": (
        "<b>💳 Новый запрос на оплату</b>

"
        "<b>Пользователь:</b> {user_name} (ID: {user_id})
"
        "<b>Telegram ID:</b> `{telegram_id}`
"
        "<b>Дата:</b> {payment_date}

"
        "<b>Тариф:</b> {plan_name}
"
        "<b>Сумма:</b> {amount} UZS"
    ),
    "en": (
        "<b>💳 New Payment Request</b>

"
        "<b>User:</b> {user_name} (ID: {user_id})
"
        "<b>Telegram ID:</b> `{telegram_id}`
"
        "<b>Date:</b> {payment_date}

"
        "<b>Plan:</b> {plan_name}
"
        "<b>Amount:</b> {amount} UZS"
    ),
}

NO_PENDING_PAYMENTS_TEXT = {
    "uz": "Hozircha ko'rib chiqilmagan to'lovlar yo'q.",
    "ru": "На данный момент нет ожидающих платежей.",
    "en": "There are no pending payments at the moment.",
}

PAYMENT_APPROVED_TEXT = "✅ To'lov tasdiqlandi."
PAYMENT_REJECTED_TEXT = "❌ To'lov rad etildi."

USER_NOTIFIED_PAYMENT_REJECTED_TEXT = {
    "uz": "😔 Afsuski, sizning to'lovingiz tasdiqlanmadi. Premium statusingiz bekor qilindi. Qo'shimcha ma'lumot uchun, iltimos, qo'llab-quvvatlash xizmatiga murojaat qiling.",
    "ru": "😔 К сожалению, ваш платеж не был подтвержден. Ваш премиум-статус был отменен. Для получения дополнительной информации, пожалуйста, свяжитесь со службой поддержки.",
    "en": "😔 Unfortunately, your payment was not confirmed. Your premium status has been revoked. For more information, please contact support.",
}

LOGS_HEADER_TEXT = {
    "uz": "📝 <b>Admin Harakatlari Loglari (Sahifa {current_page}/{total_pages})</b>

",
    "ru": "📝 <b>Логи Действий Администраторов (Страница {current_page}/{total_pages})</b>

",
    "en": "📝 <b>Admin Action Logs (Page {current_page}/{total_pages})</b>

",
}

LOG_ENTRY_TEXT = {
    "uz": "<b>ID:</b> {log_id} | <b>Sana:</b> {date}
<b>Admin ID:</b> {admin_id}
<b>Harakat:</b> {action}
<b>Target User ID:</b> {target_user_id}
<b>Izoh:</b> {comment}
",
    "ru": "<b>ID:</b> {log_id} | <b>Дата:</b> {date}
<b>ID Админа:</b> {admin_id}
<b>Действие:</b> {action}
<b>ID Целевого Пользователя:</b> {target_user_id}
<b>Комментарий:</b> {comment}
",
    "en": "<b>ID:</b> {log_id} | <b>Date:</b> {date}
<b>Admin ID:</b> {admin_id}
<b>Action:</b> {action}
<b>Target User ID:</b> {target_user_id}
<b>Comment:</b> {comment}
",
}

NO_LOGS_TEXT = {
    "uz": "Hozircha loglar mavjud emas.",
    "ru": "Логи пока отсутствуют.",
    "en": "No logs available yet.",
}

FILTER_MENU_TEXT = {
    "uz": "Loglarni qanday filtrlashni tanlang:",
    "ru": "Выберите, как фильтровать логи:",
    "en": "Choose how to filter logs:",
}

FILTER_BY_DATE_PROMPT = {
    "uz": "Sana bo'yicha filtrlash uchun sanani `YYYY-MM-DD` formatida kiriting (masalan, `2024-07-29`):",
    "ru": "Для фильтрации по дате введите дату в формате `YYYY-MM-DD` (например, `2024-07-29`):",
    "en": "To filter by date, enter the date in `YYYY-MM-DD` format (e.g., `2024-07-29`):",
}

INVALID_DATE_FORMAT_TEXT = {
    "uz": "Sana formati noto'g'ri. Iltimos, `YYYY-MM-DD` formatida kiriting.",
    "ru": "Неверный формат даты. Пожалуйста, введите в формате `YYYY-MM-DD`.",
    "en": "Invalid date format. Please enter in `YYYY-MM-DD` format.",
}

INVALID_TELEGRAM_ID_TEXT = { # Error 1: Define INVALID_TELEGRAM_ID_TEXT
    "uz": "Iltimos, faqat raqam (Telegram ID) yuboring.",
    "ru": "Пожалуйста, отправьте только число (Telegram ID).",
    "en": "Please send only a number (Telegram ID).",
}

FILTER_BY_ACTION_PROMPT = {
    "uz": "Harakat turi bo'yicha filtrlash uchun quyidagilardan birini tanlang:",
    "ru": "Для фильтрации по типу действия выберите один из следующих:",
    "en": "To filter by action type, choose one of the following:",
}

FILTERS_CLEARED_TEXT = {
    "uz": "🧹 Filtrlash tozalandi.",
    "ru": "🧹 Фильтры очищены.",
    "en": "🧹 Filters cleared.",
}

ADMIN_PANEL_RETURN_TEXT = {
    "uz": "Admin paneliga qaytish:",
    "ru": "Возврат в админ-панель:",
    "en": "Returning to admin panel:",
}



@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    if not await is_admin_user(message.from_user.id):
        user = await get_user_by_telegram_id(message.from_user.id)
        # Use a default language if the user is not in the database
        language = "uz"
        if user:
            language = user.language
        await message.answer(UNAUTHORIZED_ACCESS_TEXT[language])
        return

    await state.clear()  # Admin paneliga kirishda oldingi holatlarni tozalash
    user = await get_user_by_telegram_id(message.from_user.id)
    language = user.language if user else "uz"

    await message.answer(
        "🛡️ Admin paneliga xush kelibsiz. Bu yerda foydalanuvchilar, to'lovlar, moderatorlik va broadcastlarni boshqarishingiz mumkin.",
        reply_markup=get_admin_main_menu_keyboard(language)
    )
    await state.set_state(AdminStates.main_menu)


@router.callback_query(F.data == "admin_back_to_main_menu")
async def admin_back_to_main_menu_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = user.language if user else "uz"
    
    # Try to delete the previous message, if it fails, just ignore it.
    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        "🛡️ Asosiy menyu.",
        reply_markup=get_admin_main_menu_keyboard(language)
    )
    await callback.answer()




@router.message(AdminStates.main_menu, F.text == ADMIN_MENU_BUTTONS["uz"]["statistics"])
@router.message(AdminStates.main_menu, F.text == ADMIN_MENU_BUTTONS["ru"]["statistics"])
@router.message(AdminStates.main_menu, F.text == ADMIN_MENU_BUTTONS["en"]["statistics"])
async def show_statistics(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    language = user.language if user else "uz"

    stats = await get_bot_statistics()
    stats_text = STATISTICS_TEXT[language].format(**stats)

    await message.answer(stats_text, reply_markup=get_admin_main_menu_keyboard(language))
    # No need to set a state here, it's a one-off view.
    # await state.set_state(AdminStates.statistics) # Statistikani ko'rsatish holatiga o'tish


async def show_photo_for_moderation(message: Message, state: FSMContext):
    """Yangi tasdiqlanmagan rasmni moderatsiya uchun ko'rsatadi."""
    user = await get_user_by_telegram_id(message.from_user.id)
    language = user.language if user else "uz"

    photo_to_moderate = await get_unapproved_photo()

    if not photo_to_moderate:
        await message.answer(NO_PHOTOS_TO_MODERATE_TEXT[language])
        await state.set_state(AdminStates.main_menu)
        return

    caption = PHOTO_MODERATION_CAPTION[language].format(
        user_name=photo_to_moderate.user.name,
        user_id=photo_to_moderate.user.id,
        telegram_id=photo_to_moderate.user.telegram_id
    )

    await message.answer_photo(
        photo=photo_to_moderate.file_id,
        caption=caption,
        reply_markup=get_moderation_keyboard(
            language=language,
            photo_id=photo_to_moderate.id,
            user_id=photo_to_moderate.user.id
        )
    )
    await state.set_state(AdminStates.photo_moderation)


@router.message(AdminStates.main_menu, F.text == ADMIN_MENU_BUTTONS["uz"]["photo_moderation"])
@router.message(AdminStates.main_menu, F.text == ADMIN_MENU_BUTTONS["ru"]["photo_moderation"])
@router.message(AdminStates.main_menu, F.text == ADMIN_MENU_BUTTONS["en"]["photo_moderation"])
async def start_photo_moderation(message: Message, state: FSMContext):
    await show_photo_for_moderation(message, state)


@router.callback_query(AdminStates.photo_moderation, F.data.startswith("mod_approve_"))
async def approve_photo_handler(callback: CallbackQuery, state: FSMContext):
    photo_id = int(callback.data.split("_")[-1])
    admin_user = await get_user_by_telegram_id(callback.from_user.id)
    language = admin_user.language if admin_user else "uz"
    photo = await get_photo_by_id(photo_id)
    if photo:
        await approve_photo(photo_id)
        await create_admin_log(
            admin_id=callback.from_user.id,
            action=ActionType.approve_photo,
            target_user_id=photo.user_id,
            comment=f"Photo ID: {photo_id}"
        )
    await callback.answer(PHOTO_APPROVED_TEXT[language])
    await callback.message.delete()
    await show_photo_for_moderation(callback.message, state)


@router.callback_query(AdminStates.photo_moderation, F.data.startswith("mod_reject_"))
async def reject_photo_handler(callback: CallbackQuery, state: FSMContext):
    photo_id = int(callback.data.split("_")[-1])
    admin_user = await get_user_by_telegram_id(callback.from_user.id)
    language = admin_user.language if admin_user else "uz"
    photo = await get_photo_by_id(photo_id)
    if photo:
        await reject_photo(photo_id)
        await create_admin_log(
            admin_id=callback.from_user.id,
            action=ActionType.reject_photo,
            target_user_id=photo.user_id,
            comment=f"Photo ID: {photo_id}"
        )
    await callback.answer(PHOTO_REJECTED_TEXT[language])
    await callback.message.delete()
    await show_photo_for_moderation(callback.message, state)


@router.callback_query(AdminStates.photo_moderation, F.data.startswith("mod_ban_"))
async def ban_user_from_moderation_handler(callback: CallbackQuery, state: FSMContext):
    data_parts = callback.data.split("_")
    user_id = int(data_parts[2])
    photo_id = int(data_parts[3])

    await set_user_status(user_id, UserStatus.banned)
    await reject_photo(photo_id) # Also reject the problematic photo
    await create_admin_log(
        admin_id=callback.from_user.id,
        action=ActionType.ban_user,
        target_user_id=user_id,
        comment=f"Banned from photo moderation. Photo ID: {photo_id}"
    )

    await callback.answer(USER_BANNED_TEXT, show_alert=True)
    await callback.message.delete()
    await show_photo_for_moderation(callback.message, state)


@router.message(AdminStates.main_menu, F.text == ADMIN_MENU_BUTTONS["uz"]["users"])
@router.message(AdminStates.main_menu, F.text == ADMIN_MENU_BUTTONS["ru"]["users"])
@router.message(AdminStates.main_menu, F.text == ADMIN_MENU_BUTTONS["en"]["users"])
async def user_management_start(message: Message, state: FSMContext):
    await state.clear()
    user = await get_user_by_telegram_id(message.from_user.id)
    language = user.language if user else "uz"
    await message.answer(USER_SEARCH_PROMPT_TEXT[language], reply_markup=ReplyKeyboardRemove())
    await state.set_state(AdminStates.waiting_for_user_id)


@router.message(AdminStates.waiting_for_user_id, F.text)
async def find_user_handler(message: Message, state: FSMContext):
    admin_user = await get_user_by_telegram_id(message.from_user.id)
    language = admin_user.language if admin_user else "uz"

    try:
        int(message.text.strip())
    except ValueError:
        await message.answer(INVALID_TELEGRAM_ID_TEXT[language])
        return

    user_to_view = await find_user_by_id_or_telegram_id(message.text)

    if not user_to_view:
        await message.answer(USER_NOT_FOUND_TEXT[language])
        return

    interest_keys = user_to_view.interests.split(",") if user_to_view.interests else []
    interest_names = [
        ALL_INTERESTS[key.strip()].get(language, ALL_INTERESTS[key.strip()]["uz"])
        for key in interest_keys
        if key.strip() in ALL_INTERESTS
    ]

    # Re-use the profile view text from the menu handler
    profile_text = PROFILE_VIEW_TEXTS.get(language, PROFILE_VIEW_TEXTS["uz"]).format(
        name=user_to_view.name,
        age=user_to_view.age,
        gender=user_to_view.gender.value,
        looking_for=user_to_view.looking_for.value,
        city=user_to_view.city,
        district=user_to_view.district,
        interests=", ".join(interest_names) if interest_names else "Kiritilmagan",
        bio=user_to_view.bio or "Kiritilmagan",
        premium_status=user_to_view.premium_plan.value,
        verification_status=user_to_view.verification_status.value,
        verification_checkmark=" ✅" if user_to_view.verification_status == VerificationStatus.verified else "",
    )

    photos = await get_user_photos(user_to_view.id)
    # Reflect a live ban status in case a temporary ban has already expired.
    user_to_view = await auto_lift_expired_ban(user_to_view)
    is_banned = user_to_view.status == UserStatus.banned
    keyboard = get_user_management_keyboard(language, user_to_view.id, is_banned)

    if not photos:
        await message.answer(profile_text, reply_markup=keyboard)
    elif len(photos) == 1:
        await message.answer_photo(photo=photos[0].file_id, caption=profile_text, reply_markup=keyboard)
    else:
        media_group = []
        for i, photo in enumerate(photos):
            # Caption is only supported for the first item in a media group
            if i == 0:
                media_group.append(InputMediaPhoto(media=photo.file_id, caption=profile_text))
            else:
                media_group.append(InputMediaPhoto(media=photo.file_id))
        await message.answer_media_group(media=media_group)
        await message.answer(USER_MANAGEMENT_TEXT[language], reply_markup=keyboard)

    await state.set_state(AdminStates.viewing_user)


@router.callback_query(AdminStates.viewing_user, F.data.regexp(r"^manage_ban_\d+$"))
async def ban_user_handler(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split("_")[-1])
    admin_user = await get_user_by_telegram_id(callback.from_user.id)
    language = admin_user.language if admin_user else "uz"
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=get_ban_duration_keyboard(language, user_id))


@router.callback_query(AdminStates.viewing_user, F.data.startswith("manage_ban_cancel_"))
async def cancel_ban_duration_handler(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split("_")[-1])
    admin_user = await get_user_by_telegram_id(callback.from_user.id)
    language = admin_user.language if admin_user else "uz"
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=get_user_management_keyboard(language, user_id, is_banned=False))


@router.callback_query(AdminStates.viewing_user, F.data.startswith("manage_ban_apply_"))
async def apply_ban_duration_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    _, _, _, user_id_str, duration_token = callback.data.split("_")
    user_id = int(user_id_str)
    duration_days = None if duration_token == "perm" else int(duration_token)

    admin_user = await get_user_by_telegram_id(callback.from_user.id)
    language = admin_user.language if admin_user else "uz"

    await ban_user_with_duration(user_id, duration_days)
    await create_admin_log(
        admin_id=callback.from_user.id,
        action=ActionType.ban_user,
        target_user_id=user_id,
        comment=f"Ban muddati: {duration_days} kun" if duration_days else "Ban muddati: doimiy"
    )

    banned_user = await get_user_by_id(user_id)
    if banned_user:
        notice_language = banned_user.language or "uz"
        if banned_user.banned_until:
            outcome_text = BAN_NOTICE_TEXT.get(notice_language, BAN_NOTICE_TEXT["uz"]).format(
                until=banned_user.banned_until.strftime("%Y-%m-%d %H:%M")
            )
        else:
            outcome_text = BAN_NOTICE_PERMANENT_TEXT.get(notice_language, BAN_NOTICE_PERMANENT_TEXT["uz"])
        try:
            await bot.send_message(chat_id=banned_user.telegram_id, text=outcome_text)
        except Exception as exc:
            logging.warning(f"Foydalanuvchi {banned_user.telegram_id} ga ban haqida xabar berib bo'lmadi: {exc}")

    await callback.answer(USER_BANNED_TEXT)
    await callback.message.edit_reply_markup(reply_markup=get_user_management_keyboard(language, user_id, is_banned=True))


@router.callback_query(AdminStates.viewing_user, F.data.startswith("manage_unban_"))
async def unban_user_handler(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split("_")[-1])
    admin_user = await get_user_by_telegram_id(callback.from_user.id)
    language = admin_user.language if admin_user else "uz"
    await lift_user_ban(user_id)
    await create_admin_log(
        admin_id=callback.from_user.id,
        action=ActionType.unban_user,
        target_user_id=user_id
    )
    await callback.answer(USER_UNBANNED_TEXT)
    await callback.message.edit_reply_markup(reply_markup=get_user_management_keyboard(language, user_id, is_banned=False))


@router.callback_query(AdminStates.viewing_user, F.data.startswith("manage_delete_prompt_"))
async def prompt_delete_profile_handler(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split("_")[-1])
    admin_user = await get_user_by_telegram_id(callback.from_user.id)
    language = admin_user.language if admin_user else "uz"
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=get_delete_confirmation_keyboard(language, user_id))


@router.callback_query(AdminStates.viewing_user, F.data.startswith("manage_delete_cancel_"))
async def cancel_delete_profile_handler(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split("_")[-1])
    admin_user = await get_user_by_telegram_id(callback.from_user.id)
    language = admin_user.language if admin_user else "uz"
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=get_user_management_keyboard(language, user_id, is_banned=False))


@router.callback_query(AdminStates.viewing_user, F.data.startswith("manage_delete_confirm_"))
async def confirm_delete_profile_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    user_id = int(callback.data.split("_")[-1])
    admin_user = await get_user_by_telegram_id(callback.from_user.id)
    language = admin_user.language if admin_user else "uz"

    user_to_delete = await get_user_by_id(user_id)
    telegram_id_to_notify = user_to_delete.telegram_id if user_to_delete else None
    notify_language = (user_to_delete.language if user_to_delete else None) or "uz"

    deleted = await delete_user_data(user_id)

    if deleted:
        # delete_user_data() also removes AdminLog rows whose target_user_id points at this user,
        # so logging with target_user_id=user_id here would erase this very entry. Log with
        # target_user_id=None and keep the deleted user's telegram_id in the comment instead.
        await create_admin_log(
            admin_id=callback.from_user.id,
            action=ActionType.delete_profile,
            target_user_id=None,
            comment=f"O'chirilgan foydalanuvchi: telegram_id={telegram_id_to_notify}",
        )

    await callback.answer(
        PROFILE_DELETED_TEXT.get(language, PROFILE_DELETED_TEXT["uz"]) if deleted else USER_NOT_FOUND_TEXT.get(language, USER_NOT_FOUND_TEXT["uz"]),
        show_alert=True,
    )
    await callback.message.edit_reply_markup(reply_markup=None)

    if deleted and telegram_id_to_notify:
        try:
            await bot.send_message(
                chat_id=telegram_id_to_notify,
                text=PROFILE_DELETED_NOTICE_TEXT.get(notify_language, PROFILE_DELETED_NOTICE_TEXT["uz"]),
            )
        except Exception as exc:
            logging.warning(f"Foydalanuvchi {telegram_id_to_notify} ga profil o'chirilgani haqida xabar berib bo'lmadi: {exc}")


async def show_report_for_moderation(message: Message, state: FSMContext):
    admin_user = await get_user_by_telegram_id(message.from_user.id)
    language = admin_user.language if admin_user else "uz"

    report = await get_pending_report()

    if not report:
        await message.answer(NO_REPORTS_TEXT[language])
        await state.set_state(AdminStates.main_menu)
        return

    report_text = REPORT_DETAILS_TEXT[language].format(
        reporter_name=report.reporter.name,
        reporter_id=report.reporter.id,
        reported_name=report.reported.name,
        reported_id=report.reported.id,
        report_date=report.created_at.strftime('%Y-%m-%d %H:%M'),
        category=report.category.value,
        description=report.description
    )

    await message.answer(
        report_text,
        reply_markup=get_report_keyboard(
            language=language,
            report_id=report.id,
            reported_user_id=report.reported.id
        )
    )
    await state.set_state(AdminStates.report_moderation)


@router.message(AdminStates.main_menu, F.text == ADMIN_MENU_BUTTONS["uz"]["reports"])
@router.message(AdminStates.main_menu, F.text == ADMIN_MENU_BUTTONS["ru"]["reports"])
@router.message(AdminStates.main_menu, F.text == ADMIN_MENU_BUTTONS["en"]["reports"])
async def reports_start(message: Message, state: FSMContext):
    await show_report_for_moderation(message, state)


@router.callback_query(AdminStates.report_moderation, F.data.startswith("report_resolve_"))
async def resolve_report_handler(callback: CallbackQuery, state: FSMContext):
    report_id = int(callback.data.split("_")[-1])
    report = await get_report_by_id(report_id)
    if report:
        await update_report_status(report_id, ReportStatus.resolved)
        await create_admin_log(
            admin_id=callback.from_user.id,
            action=ActionType.resolve_report,
            target_user_id=report.reported_id,
            comment=f"Report ID: {report_id}")
    await callback.answer(REPORT_RESOLVED_TEXT)
    await callback.message.delete()
    await show_report_for_moderation(callback.message, state)


@router.callback_query(AdminStates.report_moderation, F.data.startswith("report_reject_"))
async def reject_report_handler(callback: CallbackQuery, state: FSMContext):
    report_id = int(callback.data.split("_")[-1])
    report = await get_report_by_id(report_id)
    if report:
        await update_report_status(report_id, ReportStatus.rejected)
        await create_admin_log(
            admin_id=callback.from_user.id,
            action=ActionType.reject_report,
            target_user_id=report.reported_id,
            comment=f"Report ID: {report_id}")
    await callback.answer(REPORT_REJECTED_TEXT)
    await callback.message.delete()
    await show_report_for_moderation(callback.message, state)


@router.callback_query(AdminStates.report_moderation, F.data.startswith("report_ban_"))
async def ban_from_report_handler(callback: CallbackQuery, state: FSMContext):
    _, _, reported_user_id, report_id = callback.data.split("_")
    reported_user_id = int(reported_user_id)
    report_id = int(report_id)

    await set_user_status(reported_user_id, UserStatus.banned)
    await update_report_status(report_id, ReportStatus.resolved)
    await create_admin_log(
        admin_id=callback.from_user.id,
        action=ActionType.ban_user,
        target_user_id=reported_user_id,
        comment=f"Banned from report. Report ID: {report_id}"
    )
    
    await callback.answer(REPORT_USER_BANNED_TEXT, show_alert=True)
    await callback.message.delete()
    await show_report_for_moderation(callback.message, state)


@router.message(AdminStates.main_menu, F.text == ADMIN_MENU_BUTTONS["uz"]["broadcast"])
@router.message(AdminStates.main_menu, F.text == ADMIN_MENU_BUTTONS["ru"]["broadcast"])
@router.message(AdminStates.main_menu, F.text == ADMIN_MENU_BUTTONS["en"]["broadcast"])
async def start_broadcast(message: Message, state: FSMContext):
    admin_user = await get_user_by_telegram_id(message.from_user.id)
    language = admin_user.language if admin_user else "uz"

    await message.answer(BROADCAST_MESSAGE_PROMPT[language], reply_markup=ReplyKeyboardRemove())
    await state.set_state(AdminStates.waiting_for_broadcast_message)


@router.message(AdminStates.waiting_for_broadcast_message, F.text)
async def receive_broadcast_message(message: Message, state: FSMContext):
    admin_user = await get_user_by_telegram_id(message.from_user.id)
    language = admin_user.language if admin_user else "uz"

    broadcast_text = message.text
    await state.update_data(broadcast_text=broadcast_text)

    active_user_ids = await get_all_active_user_telegram_ids()
    user_count = len(active_user_ids)

    confirmation_text = BROADCAST_CONFIRMATION_TEXT[language].format(
        user_count=user_count,
        message_text=broadcast_text
    )

    confirm_keyboard_texts = {
        "uz": {"confirm": "✅ Tasdiqlash", "cancel": "❌ Bekor qilish"},
        "ru": {"confirm": "✅ Подтвердить", "cancel": "❌ Отмена"},
        "en": {"confirm": "✅ Confirm", "cancel": "❌ Cancel"},
    }
    texts = confirm_keyboard_texts.get(language, confirm_keyboard_texts["uz"])
    # Inline keyboard for confirmation
    confirm_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=texts["confirm"], callback_data="confirm_broadcast")],
        [InlineKeyboardButton(text=texts["cancel"], callback_data="cancel_broadcast")]
    ])

    await message.answer(confirmation_text, reply_markup=confirm_keyboard)
    await state.set_state(AdminStates.confirming_broadcast)


@router.callback_query(AdminStates.confirming_broadcast, F.data == "confirm_broadcast")
async def confirm_and_send_broadcast(callback: CallbackQuery, state: FSMContext, bot: Bot):
    admin_user = await get_user_by_telegram_id(callback.from_user.id)
    language = admin_user.language if admin_user else "uz"
    data = await state.get_data()
    broadcast_text = data.get("broadcast_text")

    active_user_ids = await get_all_active_user_telegram_ids()

    for user_telegram_id in active_user_ids:
        try:
            await bot.send_message(chat_id=user_telegram_id, text=broadcast_text)
        except Exception as e:
            logging.warning(f"Could not send broadcast to user {user_telegram_id}. Reason: {e}")
    await create_admin_log(
        admin_id=callback.from_user.id,
        action=ActionType.send_broadcast,
        comment=f"Sent to {len(active_user_ids)} users. Message: {broadcast_text[:100]}..."
    )

    await callback.message.edit_text(BROADCAST_SENT_SUCCESS[language])
    await state.clear()
    await callback.message.answer(ADMIN_PANEL_RETURN_TEXT[language], reply_markup=get_admin_main_menu_keyboard(language))


@router.callback_query(AdminStates.confirming_broadcast, F.data == "cancel_broadcast")
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext):
    admin_user = await get_user_by_telegram_id(callback.from_user.id)
    language = admin_user.language if admin_user else "uz"
    await callback.message.edit_text(BROADCAST_CANCELLED[language])
    await state.clear()
    await callback.message.answer(ADMIN_PANEL_RETURN_TEXT[language], reply_markup=get_admin_main_menu_keyboard(language))


@router.message(AdminStates.main_menu, F.text == ADMIN_MENU_BUTTONS["uz"]["tariffs_payments"])
@router.message(AdminStates.main_menu, F.text == ADMIN_MENU_BUTTONS["ru"]["tariffs_payments"])
@router.message(AdminStates.main_menu, F.text == ADMIN_MENU_BUTTONS["en"]["tariffs_payments"])
async def show_tariffs_payments_stats(message: Message, state: FSMContext):
    admin_user = await get_user_by_telegram_id(message.from_user.id)
    language = admin_user.language if admin_user else "uz"

    stats = await get_payment_statistics()
    stats_text = TARIFFS_PAYMENTS_TEXT[language].format(**stats)

    await message.answer(stats_text, reply_markup=get_admin_main_menu_keyboard(language))


async def show_verification_for_moderation(message: Message, state: FSMContext):
    """Shows a pending verification request for moderation."""
    admin_user = await get_user_by_telegram_id(message.from_user.id)
    language = admin_user.language if admin_user else "uz"

    request = await get_pending_verification_request()

    if not request:
        await message.answer(NO_VERIFICATIONS_TO_MODERATE_TEXT[language])
        await state.set_state(AdminStates.main_menu)
        return

    caption = VERIFICATION_MODERATION_CAPTION[language].format(
        user_name=request.user.name,
        user_id=request.user.id,
        telegram_id=request.user.telegram_id,
        request_date=request.created_at.strftime('%Y-%m-%d %H:%M')
    )

    await message.answer_photo(
        photo=request.file_id,
        caption=caption,
        reply_markup=get_verification_moderation_keyboard(
            language=language,
            request_id=request.id
        )
    )
    await state.set_state(AdminStates.verification_moderation)


@router.message(AdminStates.main_menu, F.text == ADMIN_MENU_BUTTONS["uz"]["verification_moderation"])
@router.message(AdminStates.main_menu, F.text == ADMIN_MENU_BUTTONS["ru"]["verification_moderation"])
@router.message(AdminStates.main_menu, F.text == ADMIN_MENU_BUTTONS["en"]["verification_moderation"])
async def start_verification_moderation(message: Message, state: FSMContext):
    await show_verification_for_moderation(message, state)


@router.callback_query(AdminStates.verification_moderation, F.data.startswith("verif_approve_"))
async def approve_verification_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    request_id = int(callback.data.split("_")[-1])
    
    updated_request = await update_verification_request_status(request_id, ReportStatus.resolved, callback.from_user.id)
    await callback.answer(VERIFICATION_APPROVED_TEXT)
    
    if updated_request:
        await create_admin_log(
            admin_id=callback.from_user.id,
            action=ActionType.approve_verification,
            target_user_id=updated_request.user_id,
            comment=f"Verification request ID: {request_id}"
        )
        user_lang = updated_request.user.language or "uz"
        try:
            await bot.send_message(
                chat_id=updated_request.user.telegram_id,
                text=USER_NOTIFIED_VERIFIED_TEXT.get(user_lang, USER_NOTIFIED_VERIFIED_TEXT["uz"])
            )
        except Exception as e:
            logging.warning(f"Could not send verification approval to user {updated_request.user.telegram_id}. Reason: {e}")

    await callback.message.delete()
    await show_verification_for_moderation(callback.message, state)


@router.callback_query(AdminStates.verification_moderation, F.data.startswith("verif_reject_"))
async def reject_verification_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    request_id = int(callback.data.split("_")[-1])
    updated_request = await update_verification_request_status(request_id, ReportStatus.rejected, callback.from_user.id)
    await callback.answer(VERIFICATION_REJECTED_TEXT)
    if updated_request:
        await create_admin_log(
            admin_id=callback.from_user.id,
            action=ActionType.reject_verification,
            target_user_id=updated_request.user_id,
            comment=f"Verification request ID: {request_id}"
        )
        user_lang = updated_request.user.language or "uz"
        try:
            await bot.send_message(
                chat_id=updated_request.user.telegram_id,
                text=USER_NOTIFIED_REJECTED_TEXT.get(user_lang, USER_NOTIFIED_REJECTED_TEXT["uz"])
            )
        except Exception as e:
            logging.warning(f"Could not send verification rejection to user {updated_request.user.telegram_id}. Reason: {e}")
    await callback.message.delete()
    await show_verification_for_moderation(callback.message, state)


async def show_payment_for_moderation(message: Message, state: FSMContext):
    """Shows a pending payment for moderation."""
    admin_user = await get_user_by_telegram_id(message.from_user.id)
    language = admin_user.language if admin_user else "uz"

    payment = await get_pending_payment()

    if not payment:
        await message.answer(NO_PENDING_PAYMENTS_TEXT[language])
        await state.set_state(AdminStates.main_menu)
        return

    text = PAYMENT_MODERATION_TEXT[language].format(
        user_name=payment.user.name,
        user_id=payment.user.id,
        telegram_id=payment.user.telegram_id,
        payment_date=payment.created_at.strftime('%Y-%m-%d %H:%M'),
        plan_name=payment.description,
        amount=f"{payment.amount:,.0f}".replace(",", " ")
    )

    await message.answer(
        text,
        reply_markup=get_payment_moderation_keyboard(language, payment.id)
    )
    await state.set_state(AdminStates.payment_moderation)


@router.message(AdminStates.main_menu, F.text == ADMIN_MENU_BUTTONS["uz"]["payment_moderation"])
@router.message(AdminStates.main_menu, F.text == ADMIN_MENU_BUTTONS["ru"]["payment_moderation"])
@router.message(AdminStates.main_menu, F.text == ADMIN_MENU_BUTTONS["en"]["payment_moderation"])
async def start_payment_moderation(message: Message, state: FSMContext):
    await show_payment_for_moderation(message, state)


@router.callback_query(AdminStates.payment_moderation, F.data.startswith("payment_approve_"))
async def approve_payment_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    payment_id = int(callback.data.split("_")[-1])

    payment = await update_payment_status(payment_id, "completed")
    await callback.answer(PAYMENT_APPROVED_TEXT)

    if payment:
        plan_name = payment.description or "Gold"
        plan_key = "gold" if "Gold" in plan_name else "platinum"
        duration_days = 30 if plan_key == "gold" else 90
        new_expiry_date = datetime.now() + timedelta(days=duration_days)

        await update_user_profile_field(payment.user_id, "premium_plan", PremiumPlan[plan_key])
        await update_user_profile_field(payment.user_id, "premium_expires_at", new_expiry_date)

        await create_admin_log(
            admin_id=callback.from_user.id,
            action=ActionType.confirm_payment,
            target_user_id=payment.user_id,
            comment=f"Payment ID: {payment_id}, Amount: {payment.amount}"
        )

        user = await get_user_by_id(payment.user_id)
        if user:
            user_lang = user.language or "uz"
            try:
                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=PAYMENT_APPROVED_TEXT + f"

{PREMIUM_MAIN_TEXT.get(user_lang, PREMIUM_MAIN_TEXT['uz'])}",
                )
            except Exception as exc:
                logging.warning(f"Could not notify user {user.telegram_id} about premium activation: {exc}")

    await callback.message.delete()
    await show_payment_for_moderation(callback.message, state)


async def format_log_message(logs: list, page: int, total_count: int, language: str, filters: dict) -> tuple[str, InlineKeyboardMarkup]:
    if total_count == 0:
        keyboard = get_logs_view_keyboard(language, 0, 0)
        return NO_LOGS_TEXT[language], keyboard

    total_pages = (total_count + LOGS_PAGE_SIZE - 1) // LOGS_PAGE_SIZE
    header = LOGS_HEADER_TEXT[language].format(current_page=page + 1, total_pages=total_pages)

    filter_texts = []
    if filters.get("log_filter_date"):
        filter_texts.append(f"Sana: {filters['log_filter_date'].strftime('%Y-%m-%d')}")
    if filters.get("log_filter_action"):
        filter_texts.append(f"Harakat: {filters['log_filter_action'].value}")
    
    if filter_texts:
        header += "<i>Faol filtrlar: " + ", ".join(filter_texts) + "</i>

"
    
    log_entries = []
    for log in logs:
        log_entries.append(
            LOG_ENTRY_TEXT[language].format(
                log_id=log.id,
                date=log.created_at.strftime('%Y-%m-%d %H:%M'),
                admin_id=log.admin_id,
                action=log.action_type.value,
                target_user_id=log.target_user_id or "N/A",
                comment=log.comment or "Yo'q"
            )
        )
    
    full_text = header + "
".join(log_entries)
    keyboard = get_logs_view_keyboard(language, page, total_pages)
    
    return full_text, keyboard


async def show_logs_page(message_or_callback: Message | CallbackQuery, state: FSMContext, page: int = 0):
    admin_user = await get_user_by_telegram_id(message_or_callback.from_user.id)
    language = admin_user.language if admin_user else "uz"
    
    data = await state.get_data()
    filter_date = data.get("log_filter_date")
    filter_action = data.get("log_filter_action")
    
    offset = page * LOGS_PAGE_SIZE
    logs, total_count = await get_admin_logs(
        limit=LOGS_PAGE_SIZE, 
        offset=offset,
        filter_date=filter_date,
        filter_action=filter_action
    )
    
    filters = {"log_filter_date": filter_date, "log_filter_action": filter_action}
    text, keyboard = await format_log_message(logs, page, total_count, language, filters)
    
    if isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.message.edit_text(text, reply_markup=keyboard)
        await message_or_callback.answer()
    else:
        await message_or_callback.answer(text, reply_markup=keyboard)
    
    await state.set_state(AdminStates.viewing_logs)


@router.message(AdminStates.main_menu, F.text == ADMIN_MENU_BUTTONS["uz"]["logs"])
@router.message(AdminStates.main_menu, F.text == ADMIN_MENU_BUTTONS["ru"]["logs"])
@router.message(AdminStates.main_menu, F.text == ADMIN_MENU_BUTTONS["en"]["logs"])
async def start_viewing_logs(message: Message, state: FSMContext):
    await show_logs_page(message, state, page=0)


@router.callback_query(AdminStates.viewing_logs, F.data.startswith("logs_page_"))
async def logs_page_handler(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split("_")[-1])
    await show_logs_page(callback, state, page=page)


@router.callback_query(AdminStates.viewing_logs, F.data == "logs_filter_menu")
async def logs_filter_menu_handler(callback: CallbackQuery, state: FSMContext):
    admin_user = await get_user_by_telegram_id(callback.from_user.id)
    language = admin_user.language if admin_user else "uz"
    await callback.message.edit_text(
        FILTER_MENU_TEXT[language],
        reply_markup=get_log_filter_keyboard(language)
    )
    await state.set_state(AdminStates.choosing_log_filter)
    await callback.answer()


@router.callback_query(AdminStates.choosing_log_filter, F.data == "logs_back_to_view")
async def logs_back_to_view_handler(callback: CallbackQuery, state: FSMContext):
    await show_logs_page(callback, state, page=0)


@router.callback_query(AdminStates.choosing_log_filter, F.data == "logs_filter_action")
async def logs_filter_by_action_start(callback: CallbackQuery, state: FSMContext):
    admin_user = await get_user_by_telegram_id(callback.from_user.id)
    language = admin_user.language if admin_user else "uz"
    await callback.message.edit_text(
        FILTER_BY_ACTION_PROMPT[language],
        reply_markup=get_log_action_filter_keyboard(language)
    )
    await state.set_state(AdminStates.choosing_log_action)
    await callback.answer()


@router.callback_query(AdminStates.choosing_log_action, F.data.startswith("log_action_"))
async def logs_filter_by_action_select(callback: CallbackQuery, state: FSMContext):
    action_name = callback.data.split("_")[-1]
    action_enum = ActionType[action_name]
    await state.update_data(log_filter_action=action_enum)
    await show_logs_page(callback, state, page=0)


@router.callback_query(AdminStates.choosing_log_action, F.data == "logs_back_to_filter_menu")
async def logs_back_to_filter_menu_handler(callback: CallbackQuery, state: FSMContext):
    await logs_filter_menu_handler(callback, state)


@router.callback_query(AdminStates.choosing_log_filter, F.data == "logs_filter_date")
async def logs_filter_by_date_start(callback: CallbackQuery, state: FSMContext):
    admin_user = await get_user_by_telegram_id(callback.from_user.id)
    language = admin_user.language if admin_user else "uz"
    await callback.message.edit_text(FILTER_BY_DATE_PROMPT[language], reply_markup=None)
    await state.set_state(AdminStates.entering_log_date)
    await callback.answer()


@router.message(AdminStates.entering_log_date, F.text)
async def logs_filter_by_date_enter(message: Message, state: FSMContext):
    admin_user = await get_user_by_telegram_id(message.from_user.id)
    language = admin_user.language if admin_user else "uz"
    try:
        date_obj = datetime.strptime(message.text, "%Y-%m-%d").date()
        await state.update_data(log_filter_date=date_obj)
        await show_logs_page(message, state, page=0)
    except ValueError:
        await message.answer(INVALID_DATE_FORMAT_TEXT[language])


@router.callback_query(AdminStates.choosing_log_filter, F.data == "logs_filter_clear")
async def logs_clear_filters_handler(callback: CallbackQuery, state: FSMContext):
    admin_user = await get_user_by_telegram_id(callback.from_user.id)
    language = admin_user.language if admin_user else "uz"
    await state.update_data(log_filter_date=None, log_filter_action=None)
    await callback.answer(FILTERS_CLEARED_TEXT[language])
    await show_logs_page(callback, state, page=0)


@router.callback_query(AdminStates.payment_moderation, F.data.startswith("payment_reject_"))
async def reject_payment_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    payment_id = int(callback.data.split("_")[-1])
    payment = await update_payment_status(payment_id, "rejected")
    await callback.answer(PAYMENT_REJECTED_TEXT)

    if payment:
        # Log the action
        await create_admin_log(
            admin_id=callback.from_user.id,
            action=ActionType.reject_payment,
            target_user_id=payment.user_id,
            comment=f"Payment ID: {payment_id}"
        )
        
        # Revert premium status given prematurely
        await update_user_profile_field(payment.user_id, "premium_plan", PremiumPlan.basic)
        await update_user_profile_field(payment.user_id, "premium_expires_at", None)
        
        # Notify the user
        user = await get_user_by_id(payment.user_id)
        if user:
            user_lang = user.language or "uz"
            try:
                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=USER_NOTIFIED_PAYMENT_REJECTED_TEXT.get(user_lang, USER_NOTIFIED_PAYMENT_REJECTED_TEXT["uz"])
                )
            except Exception as e:
                logging.warning(f"Error notifying user {user.telegram_id} about payment rejection: {e}")

    await callback.message.delete()
    await show_payment_for_moderation(callback.message, state)


PROFILE_APPROVED_USER_TEXT = {
    "uz": "✅ Tabriklaymiz! Profilingiz administrator tomonidan tasdiqlandi va endi qidiruvda ko'rinadi.",
    "ru": "✅ Поздравляем! Ваш профиль одобрен администратором и теперь виден в поиске.",
    "en": "✅ Congratulations! Your profile has been approved by the administrator and is now visible in search.",
}

PROFILE_REJECTED_USER_TEXT = {
    "uz": "❌ Afsuski, profilingiz administrator tomonidan rad etildi. Iltimos, "Mening profilim" bo'limida ma'lumotlaringizni tahrirlab qayta yuboring.",
    "ru": "❌ К сожалению, ваш профиль отклонен администратором. Пожалуйста, отредактируйте данные в разделе «Мой профиль» и отправьте снова.",
    "en": "❌ Unfortunately, your profile was rejected by the administrator. Please edit your details under "My Profile" and resubmit.",
}


@router.callback_query(F.data.startswith("approve_profile_"))
async def approve_profile_handler(callback: CallbackQuery, bot: Bot):
    if not await is_admin_user(callback.from_user.id):
        await callback.answer(UNAUTHORIZED_ACCESS_TEXT["uz"], show_alert=True)
        return

    user_id = int(callback.data.split("_")[-1])
    user = await get_user_by_id(user_id)
    if not user:
        await callback.answer(USER_NOT_FOUND_TEXT["uz"], show_alert=True)
        return

    await update_user_profile_field(user_id, "profile_approval_status", "approved")
    await create_admin_log(
        admin_id=callback.from_user.id,
        action=ActionType.approve_profile,
        target_user_id=user_id,
    )
    await callback.answer("✅ Profil tasdiqlandi.")

    if callback.message.photo:
        await callback.message.edit_caption(caption=f"{callback.message.caption}

✅ TASDIQLANDI", reply_markup=None)
    else:
        await callback.message.edit_text(f"{callback.message.text}

✅ TASDIQLANDI", reply_markup=None)

    user_lang = user.language or "uz"
    try:
        await bot.send_message(
            chat_id=user.telegram_id,
            text=PROFILE_APPROVED_USER_TEXT.get(user_lang, PROFILE_APPROVED_USER_TEXT["uz"]),
        )
    except Exception as exc:
        logging.warning(f"Could not notify user {user.telegram_id} about profile approval: {exc}")


# Fix 2: Localize MANAGE_ADMINS_HEADER_TEXT
MANAGE_ADMINS_HEADER_TEXT = {
    "uz": "👮 <b>Adminlar ro'yxati</b>

Qo'shimcha admin qo'shish yoki olib tashlash uchun tugmalardan foydalaning.

<i>Eslatma: asosiy adminlar (.env dagi ADMIN_IDS) shu yerdan olib tashlanmaydi.</i>",
    "ru": "👮 <b>Список администраторов</b>

Используйте кнопки для добавления или удаления дополнительных администраторов.

<i>Примечание: основные администраторы (из ADMIN_IDS в .env) не могут быть удалены здесь.</i>",
    "en": "👮 <b>Admin List</b>

Use the buttons to add or remove additional administrators.

<i>Note: primary admins (from ADMIN_IDS in .env) cannot be removed here.</i>",
}

ADD_ADMIN_PROMPT_TEXT = {"uz": "Yangi adminning Telegram ID raqamini yuboring.
(Foydalanuvchi botdan avval /start bilan ro'yxatdan o'tgan bo'lishi kerak.)", "ru": "Отправьте Telegram ID нового администратора.
(Пользователь должен быть зарегистрирован в боте, нажав /start.)", "en": "Send the Telegram ID of the new admin.
(The user must have registered with the bot by pressing /start first.)"}
ADMIN_ADDED_TEXT = {"uz": "✅ Admin muvaffaqiyatli qo'shildi.", "ru": "✅ Администратор успешно добавлен.", "en": "✅ Admin successfully added."}
ADMIN_REMOVED_TEXT = {"uz": "✅ Admin olib tashlandi.", "ru": "✅ Администратор удален.", "en": "✅ Admin removed."}
ADMIN_NOT_FOUND_FOR_PROMOTION_TEXT = {"uz": "Bunday foydalanuvchi topilmadi. U avval botda /start bosib ro'yxatdan o'tgan bo'lishi kerak.", "ru": "Пользователь не найден. Он должен быть зарегистрирован в боте, нажав /start.", "en": "User not found. They must have registered with the bot by pressing /start first."}

@router.callback_query(F.data.startswith("reject_profile_"))
async def reject_profile_handler(callback: CallbackQuery, bot: Bot):
    if not await is_admin_user(callback.from_user.id):
        await callback.answer(UNAUTHORIZED_ACCESS_TEXT["uz"], show_alert=True)
        return

    user_id = int(callback.data.split("_")[-1])
    user = await get_user_by_id(user_id)
    if not user:
        await callback.answer(USER_NOT_FOUND_TEXT["uz"], show_alert=True)
        return
    user_lang = user.language or "uz"
    try:
        await bot.send_message(
            chat_id=user.telegram_id,
            text=PROFILE_REJECTED_USER_TEXT.get(user_lang, PROFILE_REJECTED_USER_TEXT["uz"]),
        )
    except Exception as exc:
        logging.warning(f"Could not notify user {user.telegram_id} about profile rejection: {exc}")
    
    await update_user_profile_field(user_id, "profile_approval_status", "rejected")
    await create_admin_log(
        admin_id=callback.from_user.id,
        action=ActionType.reject_profile,
        target_user_id=user_id,
    )
    await callback.answer("❌ Profil rad etildi.")

    if callback.message.photo:
        # Check if caption is not None before appending
        current_caption = callback.message.caption if callback.message.caption else ""
        await callback.message.edit_caption(caption=f"{current_caption}

❌ RAD ETILDI", reply_markup=None)
    else:
        # Check if text is not None before appending
        current_text = callback.message.text if callback.message.text else ""
        await callback.message.edit_text(f"{current_text}

❌ RAD ETILDI", reply_markup=None)


async def show_manage_admins(message: Message, state: FSMContext):
    admin_user = await get_user_by_telegram_id(message.from_user.id)
    language = admin_user.language if admin_user else "uz"
    dynamic_admins = await get_dynamic_admins()
    keyboard = get_manage_admins_keyboard(language, [(admin.telegram_id, admin.name or str(admin.telegram_id)) for admin in dynamic_admins])
    await message.answer(MANAGE_ADMINS_HEADER_TEXT[language], reply_markup=keyboard)
    await state.set_state(AdminStates.viewing_admins)


@router.message(AdminStates.main_menu, F.text == ADMIN_MENU_BUTTONS["uz"]["mandatory_channel"])
@router.message(AdminStates.main_menu, F.text == ADMIN_MENU_BUTTONS["ru"]["mandatory_channel"])
@router.message(AdminStates.main_menu, F.text == ADMIN_MENU_BUTTONS["en"]["mandatory_channel"])
async def mandatory_channel_handler(message: Message, state: FSMContext):
    is_enabled = await get_setting("force_subscribe_channel") == "true"
    channel_id = await get_setting("subscribe_channel_id")

    text = f"Majburiy kanal holati: {'✅ Yoqilgan' if is_enabled else '❌ O''chirilgan'}
"
    if is_enabled and channel_id:
        text += f"Kanal: {channel_id}"

    buttons = [
        [InlineKeyboardButton(text="Yoqish/O'zgartirish", callback_data="set_channel_on")],
        [InlineKeyboardButton(text="O'chirish", callback_data="set_channel_off")],
        [InlineKeyboardButton(text="Ortga", callback_data="admin_back_to_main_menu")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(text, reply_markup=keyboard)
    await state.set_state(AdminStates.setting_channel)


@router.callback_query(AdminStates.setting_channel, F.data == "set_channel_on")
async def set_channel_on_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Majburiy obuna uchun kanalning userneymini kiriting (masalan, @kanal_nomi).")
    await state.set_state(AdminStates.waiting_for_channel_id)
    await callback.answer()


@router.message(AdminStates.waiting_for_channel_id, F.text)
async def channel_id_received_handler(message: Message, state: FSMContext):
    channel_id = message.text
    if not channel_id.startswith('@'):
        await message.answer("Kanal userneymi @ belgisi bilan boshlanishi kerak.")
        return

    await set_setting("force_subscribe_channel", "true")
    await set_setting("subscribe_channel_id", channel_id)

    await message.answer(f"Majburiy kanal {channel_id} ga o'rnatildi va yoqildi.")
    await state.set_state(AdminStates.main_menu)

@router.callback_query(AdminStates.setting_channel, F.data == "set_channel_off")
async def set_channel_off_handler(callback: CallbackQuery, state: FSMContext):
    await set_setting("force_subscribe_channel", "false")
    await callback.message.edit_text("Majburiy obuna o'chirildi.")
    await state.set_state(AdminStates.main_menu)
    await callback.answer()


@router.message(AdminStates.main_menu, F.text == ADMIN_MENU_BUTTONS["uz"]["districts"])
@router.message(AdminStates.main_menu, F.text == ADMIN_MENU_BUTTONS["ru"]["districts"])
@router.message(AdminStates.main_menu, F.text == ADMIN_MENU_BUTTONS["en"]["districts"])
async def manage_districts_handler(message: Message, state: FSMContext):
    districts_str = await get_setting("districts", "")
    districts = [d.strip() for d in districts_str.split(",") if d.strip()]

    text = "Mavjud tumanlar:

"
    if districts:
        text += "
".join(f"- {d}" for d in districts)
    else:
        text += "Tumanlar ro'yxati bo'sh."

    buttons = [
        [InlineKeyboardButton(text="Qo'shish", callback_data="add_district")],
        [InlineKeyboardButton(text="O'chirish", callback_data="remove_district")],
        [InlineKeyboardButton(text="Ortga", callback_data="admin_back_to_main_menu")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(text, reply_markup=keyboard)
    await state.set_state(AdminStates.managing_districts)

@router.callback_query(AdminStates.managing_districts, F.data == "add_district")
async def add_district_prompt_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Yangi tuman nomini kiriting:")
    await state.set_state(AdminStates.waiting_for_district_to_add)
    await callback.answer()

@router.message(AdminStates.waiting_for_district_to_add, F.text)
async def add_district_received_handler(message: Message, state: FSMContext):
    new_district = message.text.strip()
    districts_str = await get_setting("districts", "")
    districts = [d.strip() for d in districts_str.split(",") if d.strip()]

    if new_district not in districts:
        districts.append(new_district)
        await set_setting("districts", ",".join(districts))
        await message.answer(f"'{new_district}' tumani qo'shildi.")
    else:
        await message.answer(f"'{new_district}' tumani ro'yxatda mavjud.")

    await state.set_state(AdminStates.main_menu)

@router.callback_query(AdminStates.managing_districts, F.data == "remove_district")
async def remove_district_prompt_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("O'chirish uchun tuman nomini kiriting:")
    await state.set_state(AdminStates.waiting_for_district_to_remove)
    await callback.answer()

@router.message(AdminStates.waiting_for_district_to_remove, F.text)
async def remove_district_received_handler(message: Message, state: FSMContext):
    district_to_remove = message.text.strip()
    districts_str = await get_setting("districts", "")
    districts = [d.strip() for d in districts_str.split(",") if d.strip()]

    if district_to_remove in districts:
        districts.remove(district_to_remove)
        await set_setting("districts", ",".join(districts))
        await message.answer(f"'{district_to_remove}' tumani o'chirildi.")
    else:
        await message.answer(f"'{district_to_remove}' tumani ro'yxatda topilmadi.")

    await state.set_state(AdminStates.main_menu)

@router.message(AdminStates.main_menu, F.text == ADMIN_MENU_BUTTONS["uz"]["manage_admins"])
@router.message(AdminStates.main_menu, F.text == ADMIN_MENU_BUTTONS["ru"]["manage_admins"])
@router.message(AdminStates.main_menu, F.text == ADMIN_MENU_BUTTONS["en"]["manage_admins"])
async def manage_admins_start(message: Message, state: FSMContext):
    await show_manage_admins(message, state)


@router.callback_query(AdminStates.viewing_admins, F.data == "admin_add_new")
async def prompt_add_admin(callback: CallbackQuery, state: FSMContext):
    admin_user = await get_user_by_telegram_id(callback.from_user.id)
    language = admin_user.language if admin_user else "uz"
    await state.set_state(AdminStates.waiting_for_admin_id_to_add)
    await callback.message.edit_text(ADD_ADMIN_PROMPT_TEXT[language], reply_markup=None)
    await callback.answer()


@router.message(AdminStates.waiting_for_admin_id_to_add, F.text)
async def add_admin_received(message: Message, state: FSMContext):
    admin_user = await get_user_by_telegram_id(message.from_user.id)
    language = admin_user.language if admin_user else "uz"
    if not message.text.strip().lstrip("-").isdigit():
        await message.answer(INVALID_TELEGRAM_ID_TEXT[language])
        return

    telegram_id = int(message.text.strip())
    new_admin = await add_admin_by_telegram_id(telegram_id)
    if not new_admin:
        await message.answer(ADMIN_NOT_FOUND_FOR_PROMOTION_TEXT[language])
        return

    await create_admin_log(
        admin_id=message.from_user.id,
        action=ActionType.add_admin,
        target_user_id=new_admin.id,
        comment=f"Telegram ID: {telegram_id}",
    )
    await message.answer(ADMIN_ADDED_TEXT[language])
    await show_manage_admins(message, state)


@router.callback_query(AdminStates.viewing_admins, F.data.startswith("admin_remove_"))
async def remove_admin_handler(callback: CallbackQuery, state: FSMContext):
    telegram_id = int(callback.data.split("_")[-1])
    removed_admin = await remove_admin_by_telegram_id(telegram_id)
    admin_user = await get_user_by_telegram_id(callback.from_user.id)
    language = admin_user.language if admin_user else "uz"
    if removed_admin:
        await create_admin_log(
            admin_id=callback.from_user.id,
            action=ActionType.remove_admin,
            target_user_id=removed_admin.id,
            comment=f"Telegram ID: {telegram_id}",
        )
    await callback.answer(ADMIN_REMOVED_TEXT[language])
    await callback.message.delete()
    await show_manage_admins(callback.message, state)


CHANNEL_CHECK_SET_SUCCESS_TEXT = {
    "uz": "✅ Kanalga majburiy obuna sozlamalari o'rnatildi.",
    "ru": "✅ Настройки принудительной подписки на канал установлены.",
    "en": "✅ Forced channel subscription settings have been set.",
}

CHANNEL_CHECK_SET_USAGE_TEXT = {
    "uz": "Noto'g'ri format. Foydalanish: /set_channel_check <on|off> [@channel_id]",
    "ru": "Неверный формат. Используйте: /set_channel_check <on|off> [@channel_id]",
    "en": "Invalid format. Usage: /set_channel_check <on|off> [@channel_id]",
}

@router.message(Command("set_channel_check"))
async def set_channel_check_handler(message: Message):
    """Handles the /set_channel_check command for admins."""
    if not await is_admin_user(message.from_user.id):
        user = await get_user_by_telegram_id(message.from_user.id)
        language = user.language if user else "uz"
        await message.answer(UNAUTHORIZED_ACCESS_TEXT[language])
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer(CHANNEL_CHECK_SET_USAGE_TEXT["uz"])
        return

    status = parts[1].lower()
    channel_id = parts[2] if len(parts) > 2 else None

    if status not in ["on", "off"]:
        await message.answer(CHANNEL_CHECK_SET_USAGE_TEXT["uz"])
        return

    if status == "on" and not channel_id:
        await message.answer(CHANNEL_CHECK_SET_USAGE_TEXT["uz"])
        return
        
    await set_setting("force_subscribe_channel", str(status == "on").lower())
    if channel_id:
        await set_setting("subscribe_channel_id", channel_id)

    await message.answer(CHANNEL_CHECK_SET_SUCCESS_TEXT["uz"])

@router.message(Command("addadmin"))
async def add_admin_command(message: Message):
    if not await is_admin_user(message.from_user.id):
        user = await get_user_by_telegram_id(message.from_user.id)
        language = "uz"
        if user:
            language = user.language
        await message.answer(UNAUTHORIZED_ACCESS_TEXT.get(language, "Sizda admin paneliga kirish huquqi yo'q."))
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Foydalanish: /addadmin <telegram_id>")
        return

    try:
        telegram_id = int(parts[1])
    except ValueError:
        await message.answer("Telegram ID raqam bo'lishi kerak.")
        return

    new_admin = await add_admin_by_telegram_id(telegram_id)
    if not new_admin:
        await message.answer(ADMIN_NOT_FOUND_FOR_PROMOTION_TEXT.get("uz"))
        return

    await create_admin_log(
        admin_id=message.from_user.id,
        action=ActionType.add_admin,
        target_user_id=new_admin.id,
        comment=f"Telegram ID: {telegram_id}",
    )
    await message.answer(ADMIN_ADDED_TEXT.get("uz"))


@router.message(Command("deladmin"))
async def del_admin_command(message: Message):
    if not await is_admin_user(message.from_user.id):
        user = await get_user_by_telegram_id(message.from_user.id)
        language = "uz"
        if user:
            language = user.language
        await message.answer(UNAUTHORIZED_ACCESS_TEXT.get(language, "Sizda admin paneliga kirish huquqi yo'q."))
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Foydalanish: /deladmin <telegram_id>")
        return

    try:
        telegram_id = int(parts[1])
    except ValueError:
        await message.answer("Telegram ID raqam bo'lishi kerak.")
        return

    # Prevent removing primary admins
    from config import ADMIN_IDS
    if telegram_id in ADMIN_IDS:
        await message.answer("Asosiy adminni bu buyruq bilan o'chirib bo'lmaydi.")
        return

    removed_admin = await remove_admin_by_telegram_id(telegram_id)
    if not removed_admin:
        await message.answer("Bunday admin topilmadi yoki u asosiy admin emas.")
        return

    await create_admin_log(
        admin_id=message.from_user.id,
        action=ActionType.remove_admin,
        target_user_id=removed_admin.id,
        comment=f"Telegram ID: {telegram_id}",
    )
    await message.answer(ADMIN_REMOVED_TEXT.get("uz"))
