import os
import sys
import logging
import asyncio
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    WebAppInfo,
    MenuButtonWebApp,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from sqlalchemy import select, func

from config import BOT_TOKEN, WEBAPP_URL, ADMIN_IDS
from engine import async_session_maker
from models import User, UserStatus

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

router = Router()

def is_admin(user_id: int) -> bool:
    if user_id == 7992878834:
        return True
    return user_id in ADMIN_IDS

def get_webapp_url() -> str:
    import time
    if not WEBAPP_URL:
        return ""
    t = int(time.time() // 60)
    return f"{WEBAPP_URL}&v={t}" if "?" in WEBAPP_URL else f"{WEBAPP_URL}?v={t}"

def get_main_reply_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="📱 Mini App ni ochish", web_app=WebAppInfo(url=get_webapp_url()))],
        [KeyboardButton(text="👤 Profilim"), KeyboardButton(text="🔄 Statusim")],
        [KeyboardButton(text="ℹ️ Qoidalar va Yordam")]
    ]
    if is_admin(user_id):
        keyboard.append([KeyboardButton(text="📊 Statistika"), KeyboardButton(text="⏳ Kutilayotgan arizalar")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

@router.message(Command("start"))
async def cmd_start(message: Message, bot: Bot):
    try:
        await bot.set_chat_menu_button(
            chat_id=message.chat.id,
            menu_button=MenuButtonWebApp(
                text="Kairyx App",
                web_app=WebAppInfo(url=get_webapp_url())
            )
        )
    except Exception as e:
        logger.warning(f"Error setting chat menu button: {e}")

    user_id = message.from_user.id
    first_name = message.from_user.first_name or "Foydalanuvchi"
    admin_badge = " 🛡️ (Admin)" if is_admin(user_id) else ""
    
    welcome_text = (
        f"👋 Assalomu alaykum, <b>{first_name}</b>{admin_badge}!\n\n"
        "💖 <b>Kairyx</b> — premium tanishuv platformasiga xush kelibsiz.\n\n"
        "Quyidagi menyu orqali ilovani ochishingiz yoki profilingizni boshqarishingiz mumkin:\n"
        "• <b>Mini App ni ochish</b> — to'liq interaktiv tanishuv ilovasi\n"
        "• <b>Profilim</b> — shaxsiy anketangizni ko'rish\n"
        "• <b>Statusim</b> — arizangiz holatini tekshirish\n"
    )
    if is_admin(user_id):
        welcome_text += "\n🛡️ <b>Admin buyruqlari:</b>\n• /stats — Umumiy statistika\n• /pending — Kutilayotgan arizalar"

    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔥 Kairyx Mini App ni ochish", web_app=WebAppInfo(url=get_webapp_url()))]
    ])

    await message.answer(
        welcome_text,
        reply_markup=get_main_reply_keyboard(user_id),
        parse_mode=ParseMode.HTML
    )
    await message.answer(
        "📱 Ilovani ishga tushirish uchun quyidagi tugmani bosing:",
        reply_markup=inline_kb,
        parse_mode=ParseMode.HTML
    )

@router.message(F.text == "👤 Profilim")
@router.message(Command("profile"))
async def cmd_profile(message: Message):
    user_id = message.from_user.id
    async with async_session_maker() as session:
        stmt = select(User).where(User.telegram_id == user_id)
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()

        if not user or user.status == UserStatus.DRAFT:
            await message.answer(
                "ℹ️ Siz hali profilingizni to'liq to'ldirmagansiz.\n"
                "Iltimos, <b>Mini App</b>ga kirib anketangizni to'ldiring.",
                parse_mode=ParseMode.HTML
            )
            return

        status_icon = {
            UserStatus.PENDING_APPROVAL: "⏳ Tekshiruvda",
            UserStatus.APPROVED: "✅ Tasdiqlangan",
            UserStatus.REJECTED: "❌ Rad etilgan",
            UserStatus.BANNED: "⛔ Bloklangan"
        }.get(user.status, str(user.status))

        text = (
            "👤 <b>Sizning profilingiz:</b>\n\n"
            f"• <b>Ism:</b> {user.name or 'Kiritilmagan'}\n"
            f"• <b>Yosh:</b> {user.age or 'Kiritilmagan'}\n"
            f"• <b>Shahar:</b> {user.city or 'Kiritilmagan'}\n"
            f"• <b>Holat:</b> {status_icon}\n"
            f"• <b>Haqingizda:</b> {user.bio or 'Mavjud emas'}"
        )
        await message.answer(text, parse_mode=ParseMode.HTML)

@router.message(F.text == "🔄 Statusim")
@router.message(Command("status"))
async def cmd_status(message: Message):
    user_id = message.from_user.id
    async with async_session_maker() as session:
        stmt = select(User).where(User.telegram_id == user_id)
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()

        if not user or user.status == UserStatus.DRAFT:
            await message.answer(
                "📝 <b>Holatingiz: Ro'yxatdan o'tilmagan (Draft)</b>\n"
                "Ilovadan foydalanish uchun Mini Appni ochib anketani to'ldiring.",
                parse_mode=ParseMode.HTML
            )
        elif user.status == UserStatus.PENDING_APPROVAL:
            await message.answer(
                "⏳ <b>Holatingiz: Tekshiruvda (Pending)</b>\n"
                "Arizangiz adminlar tomonidan ko'rib chiqilmoqda. Tasdiqlangach darhol xabar beramiz.",
                parse_mode=ParseMode.HTML
            )
        elif user.status == UserStatus.APPROVED:
            await message.answer(
                "✅ <b>Holatingiz: Tasdiqlangan (Active)</b>\n"
                "Profilingiz faol! Mini Appga kirib boshqalar bilan tanishishingiz va chatlashishingiz mumkin.",
                parse_mode=ParseMode.HTML
            )
        elif user.status == UserStatus.REJECTED:
            await message.answer(
                "❌ <b>Holatingiz: Rad etilgan</b>\n"
                "Arizangiz qabul qilinmadi.",
                parse_mode=ParseMode.HTML
            )
        else:
            await message.answer(f"Holatingiz: {user.status}", parse_mode=ParseMode.HTML)

@router.message(F.text == "ℹ️ Qoidalar va Yordam")
@router.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "ℹ️ <b>Kairyx Tanishuv Ilovasi haqida:</b>\n\n"
        "1. <b>Foydalanish yoshi:</b> 18 yoshdan katta bo'lish shart.\n"
        "2. <b>Anketa:</b> Haqiqiy ism, yosh va shahar kiritilishi lozim.\n"
        "3. <b>O'zaro moslik:</b> Ikkala tomon bir-biriga Like bossa, Match (Juftlik) hosil bo'ladi va bepul chat ochiladi.\n"
        "4. <b>Xavfsizlik:</b> Spam, haqorat va firibgarlik taqiqlanadi."
    )
    await message.answer(help_text, parse_mode=ParseMode.HTML)

# ADMIN COMMANDS
@router.message(F.text == "📊 Statistika")
@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Ushbu buyruq faqat adminlar uchun.")
        return

    async with async_session_maker() as session:
        res_total = await session.execute(select(func.count()).select_from(User))
        total_users = res_total.scalar() or 0

        res_pending = await session.execute(select(func.count()).select_from(User).where(User.status == UserStatus.PENDING_APPROVAL))
        pending_users = res_pending.scalar() or 0

        res_approved = await session.execute(select(func.count()).select_from(User).where(User.status == UserStatus.APPROVED))
        approved_users = res_approved.scalar() or 0

        stats_text = (
            "📊 <b>Kairyx Platformasi Statistikasi:</b>\n\n"
            f"• Jami a'zolar: <b>{total_users}</b> ta\n"
            f"• Tasdiqlanganlar: <b>{approved_users}</b> ta\n"
            f"• Kutilayotgan arizalar: <b>{pending_users}</b> ta\n"
        )
        await message.answer(stats_text, parse_mode=ParseMode.HTML)

@router.message(F.text == "⏳ Kutilayotgan arizalar")
@router.message(Command("pending"))
async def cmd_pending(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Ushbu buyruq faqat adminlar uchun.")
        return

    async with async_session_maker() as session:
        stmt = select(User).where(User.status == UserStatus.PENDING_APPROVAL).limit(10)
        res = await session.execute(stmt)
        users = res.scalars().all()

        if not users:
            await message.answer("✅ Hozircha kutilayotgan arizalar yo'q!", parse_mode=ParseMode.HTML)
            return

        await message.answer(f"⏳ <b>Kutilayotgan arizalar ({len(users)} ta):</b>", parse_mode=ParseMode.HTML)

        for u in users:
            card_text = (
                f"👤 <b>{u.name or 'Noma`lum'}</b>, {u.age or '?'}\n"
                f"📍 <b>Shahar:</b> {u.city or 'Noma`lum'}\n"
                f"📝 <b>Bio:</b> {u.bio or 'Yo`q'}\n"
                f"🆔 <b>Telegram ID:</b> {u.telegram_id}"
            )
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"adm_app_{u.id}"),
                    InlineKeyboardButton(text="❌ Rad etish", callback_data=f"adm_rej_{u.id}")
                ]
            ])
            await message.answer(card_text, reply_markup=kb, parse_mode=ParseMode.HTML)

@router.callback_query(F.data.startswith("adm_app_"))
async def cb_approve(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    user_id = int(callback.data.split("_")[2])
    async with async_session_maker() as session:
        stmt = select(User).where(User.id == user_id)
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()

        if not user:
            await callback.answer("Foydalanuvchi topilmadi!", show_alert=True)
            return

        user.status = UserStatus.APPROVED
        await session.commit()

    old_text = callback.message.text or ""
    await callback.message.edit_text(
        f"{old_text}\n\n<b>✅ TASDIQLANDI (Admin: {callback.from_user.first_name})</b>",
        parse_mode=ParseMode.HTML
    )
    await callback.answer("Foydalanuvchi tasdiqlandi!")

@router.callback_query(F.data.startswith("adm_rej_"))
async def cb_reject(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    user_id = int(callback.data.split("_")[2])
    async with async_session_maker() as session:
        stmt = select(User).where(User.id == user_id)
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()

        if not user:
            await callback.answer("Foydalanuvchi topilmadi!", show_alert=True)
            return

        user.status = UserStatus.REJECTED
        await session.commit()

    old_text = callback.message.text or ""
    await callback.message.edit_text(
        f"{old_text}\n\n<b>❌ RAD ETILDI (Admin: {callback.from_user.first_name})</b>",
        parse_mode=ParseMode.HTML
    )
    await callback.answer("Foydalanuvchi rad etildi!")

@router.message()
async def all_other_messages(message: Message, bot: Bot):
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

    user_id = message.from_user.id
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 Mini App ni ochish", web_app=WebAppInfo(url=get_webapp_url()))]
    ])
    await message.answer(
        "Kairyx tanishuv platformasi menyusi:",
        reply_markup=get_main_reply_keyboard(user_id),
        parse_mode=ParseMode.HTML
    )
    await message.answer(
        "Ilovani ochish uchun pastdagi tugmani bosing:",
        reply_markup=inline_kb,
        parse_mode=ParseMode.HTML
    )

async def main() -> None:
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("Xatolik: Telegram bot tokeni topilmadi.")
        return

    from models import Base
    import engine as engine_module
    try:
        async with engine_module.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schema initialized.")
    except Exception as exc:
        logger.warning(f"Database setup warning: {exc}")
        try:
            engine_module.switch_to_sqlite_fallback(exc)
            async with engine_module.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.warning("SQLite fallback activated.")
        except Exception as fallback_exc:
            logger.warning(f"SQLite fallback setup warning: {fallback_exc}")

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    dp.include_router(router)

    from webapp.api import create_webapp_app
    from aiohttp import web
    webapp_app = create_webapp_app()
    runner = web.AppRunner(webapp_app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"REST API server successfully started on port {port}")

    logger.info("Bot polling started...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
