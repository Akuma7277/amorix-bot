from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InputMediaPhoto

import config
import database as db
import keyboards as kb
from states import AdminStates

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer(f"🛠 <b>{config.BOT_NAME} — Admin panel</b>", reply_markup=kb.admin_menu_kb())


@router.callback_query(F.data == "adm:back")
async def adm_back(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await state.clear()
    await callback.answer()
    await callback.message.edit_text(f"🛠 <b>{config.BOT_NAME} — Admin panel</b>", reply_markup=kb.admin_menu_kb())


# ---------------------------------------------------------------------------
# Statistika
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "adm:stats")
async def adm_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    stats = await db.get_stats()
    channel = await db.get_setting("required_channel")
    text = (
        "📊 <b>Statistika</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{stats['total']}</b>\n"
        f"👨 Erkaklar: <b>{stats['male']}</b>\n"
        f"👩 Ayollar: <b>{stats['female']}</b>\n"
        f"🆕 Bugun qo'shilgan: <b>{stats['today']}</b>\n"
        f"🚫 Bloklanganlar: <b>{stats['banned']}</b>\n\n"
        f"📺 Majburiy kanal: <b>{channel or 'o‘rnatilmagan'}</b>"
    )
    await callback.answer()
    await callback.message.edit_text(text, reply_markup=kb.admin_back_kb())


# ---------------------------------------------------------------------------
# Foydalanuvchilar ro'yxati
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("adm:users:"))
async def adm_users(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    offset = int(callback.data.split(":")[2])
    users = await db.get_users_page(offset, limit=10)
    next_users = await db.get_users_page(offset + 10, limit=1)
    await callback.answer()
    if not users and offset == 0:
        await callback.message.edit_text("Hozircha ro'yxatdan o'tgan foydalanuvchi yo'q.", reply_markup=kb.admin_back_kb())
        return
    await callback.message.edit_text(
        f"👥 <b>Foydalanuvchilar</b> ({offset + 1}-{offset + len(users)})",
        reply_markup=kb.users_page_kb(users, offset, bool(next_users)),
    )


@router.callback_query(F.data.startswith("adm:view:"))
async def adm_view_user(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    telegram_id = int(callback.data.split(":")[2])
    user = await db.get_user(telegram_id)
    if not user:
        await callback.answer("Foydalanuvchi topilmadi.", show_alert=True)
        return
    photos = await db.get_photos(telegram_id)
    caption = (
        f"👤 <b>{user['full_name']}</b> (@{user['username'] or '—'})\n"
        f"🆔 ID: <code>{user['telegram_id']}</code>\n"
        f"📱 Tel: <code>{user['phone']}</code>\n"
        f"🚻 Jinsi: <b>{user['gender']}</b>\n"
        f"🎂 Yoshi: <b>{user['age']}</b>\n"
        f"📏 Bo'yi: <b>{user['height']} sm</b>\n"
        f"⚖️ Vazni: <b>{user['weight']} kg</b>\n"
        f"📍 Manzil: <b>{user['region']}, {user['district']}</b>\n"
        f"💬 <i>{user['bio']}</i>\n\n"
        f"Holati: {'🚫 Bloklangan' if user['is_banned'] else '✅ Faol'}"
    )
    await callback.answer()
    if photos:
        media = [InputMediaPhoto(media=photos[0], caption=caption)]
        for p in photos[1:]:
            media.append(InputMediaPhoto(media=p))
        await callback.message.answer_media_group(media)
        await callback.message.answer(
            "Amallar:", reply_markup=kb.user_detail_kb(telegram_id, bool(user["is_banned"]))
        )
    else:
        await callback.message.answer(caption, reply_markup=kb.user_detail_kb(telegram_id, bool(user["is_banned"])))


@router.callback_query(F.data.startswith("adm:ban:"))
async def adm_ban(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    telegram_id = int(callback.data.split(":")[2])
    await db.ban_user(telegram_id)
    await callback.answer("🚫 Bloklandi.")
    await callback.message.edit_reply_markup(reply_markup=kb.user_detail_kb(telegram_id, True))


@router.callback_query(F.data.startswith("adm:unban:"))
async def adm_unban(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    telegram_id = int(callback.data.split(":")[2])
    await db.unban_user(telegram_id)
    await callback.answer("✅ Blokdan chiqarildi.")
    await callback.message.edit_reply_markup(reply_markup=kb.user_detail_kb(telegram_id, False))


# ---------------------------------------------------------------------------
# Xabar yuborish (Broadcast)
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "adm:broadcast")
async def adm_broadcast_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await callback.answer()
    await state.set_state(AdminStates.waiting_broadcast)
    await callback.message.edit_text(
        "📢 Barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni yuboring "
        "(matn, rasm, video — istalgan turda).\n\nBekor qilish uchun /admin bosing."
    )


@router.message(AdminStates.waiting_broadcast)
async def adm_broadcast_send(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    users = await db.get_all_active_users()
    sent, failed = 0, 0
    status_msg = await message.answer(f"⏳ Yuborilmoqda... 0/{len(users)}")

    for i, uid in enumerate(users, start=1):
        try:
            await bot.copy_message(chat_id=uid, from_chat_id=message.chat.id, message_id=message.message_id)
            sent += 1
        except Exception:
            failed += 1
        if i % 25 == 0:
            try:
                await status_msg.edit_text(f"⏳ Yuborilmoqda... {i}/{len(users)}")
            except Exception:
                pass

    await status_msg.edit_text(
        f"✅ <b>Broadcast tugadi</b>\n\nYuborildi: {sent}\nMuvaffaqiyatsiz: {failed}",
        reply_markup=kb.admin_back_kb(),
    )


# ---------------------------------------------------------------------------
# Majburiy kanal sozlash
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "adm:channel")
async def adm_channel_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await callback.answer()
    await state.set_state(AdminStates.waiting_channel)
    await callback.message.edit_text(
        "📺 Kanal <b>username</b>ini yuboring (masalan: <code>@mening_kanalim</code>).\n\n"
        "⚠️ Diqqat: bot o'sha kanalga <b>admin</b> qilib qo'shilgan bo'lishi kerak, "
        "aks holda a'zolikni tekshira olmaydi.\n\nBekor qilish uchun /admin bosing."
    )


@router.message(AdminStates.waiting_channel)
async def adm_channel_save(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    username = (message.text or "").strip()
    if not username.startswith("@"):
        await message.answer("⚠️ Username @ bilan boshlanishi kerak. Masalan: @mening_kanalim")
        return
    try:
        chat = await bot.get_chat(username)
        await bot.get_chat_member(chat_id=username, user_id=bot.id)
    except Exception as e:
        await message.answer(
            "❌ Kanal topilmadi yoki bot u yerga admin qilib qo'shilmagan.\n"
            f"Xatolik: <code>{e}</code>"
        )
        return

    await db.set_setting("required_channel", username)
    await state.clear()
    await message.answer(
        f"✅ Majburiy kanal o'rnatildi: <b>{chat.title}</b> ({username})",
        reply_markup=kb.admin_back_kb(),
    )


@router.callback_query(F.data == "adm:channel_remove")
async def adm_channel_remove(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await db.delete_setting("required_channel")
    await callback.answer("🗑 O'chirildi.")
    await callback.message.edit_text("Majburiy kanal talabi bekor qilindi.", reply_markup=kb.admin_back_kb())

@router.callback_query(F.data == "adm:reports")
async def adm_reports(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer()

    reports = await db.get_reports()

    await callback.answer()

    if not reports:
        await callback.message.edit_text(
            "✅ Hozircha shikoyatlar yo'q.",
            reply_markup=kb.admin_back_kb()
        )
        return

    for r in reports[:10]:
        text = (
            f"🚫 <b>Shikoyat</b>\n\n"
            f"🆔 ID: {r['id']}\n"
            f"👤 Kim yubordi: <code>{r['from_user']}</code>\n"
            f"🚨 Kim haqida: <code>{r['to_user']}</code>\n"
            f"📝 Sabab: {r['reason']}\n"
            f"📅 Sana: {r['created_at']}"
        )

        await callback.message.answer(
            text,
            reply_markup=kb.user_detail_kb(
                r["to_user"],
                False
            )
        )

    await callback.message.answer(
        "⬅️ Orqaga",
        reply_markup=kb.admin_back_kb()
    )

@router.callback_query(F.data == "adm:payments")
async def adm_payments(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer()

    payments = await db.get_pending_payments()

    if not payments:
        await callback.answer("Yangi to'lovlar yo'q.")
        return

    await callback.answer()

    for payment in payments:
        text = (
            "💎 <b>Yangi Premium to'lov</b>\n\n"
            f"🆔 ID: <code>{payment['payment_id']}</code>\n"
            f"👤 User: <code>{payment['user_id']}</code>\n"
            f"📦 Tarif: <b>{payment['tariff']}</b>\n"
            f"💰 Summa: <b>{payment['amount']:,} so'm</b>\n"
            f"📅 Sana: {payment['created_at']}\n"
        )

        if payment["receipt_file"]:
            await callback.message.answer_photo(
                photo=payment["receipt_file"],
                caption=text,
                reply_markup=kb.payment_action_kb(payment["payment_id"])
            )
        else:
            await callback.message.answer(
                text,
                reply_markup=kb.payment_action_kb(payment["payment_id"])
            )

@router.callback_query(F.data.startswith("approve_payment:"))
async def approve_payment(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer()

    payment_id = callback.data.split(":")[1]

    payment = await db.get_payment(payment_id)

    if not payment:
        await callback.answer("To'lov topilmadi.", show_alert=True)
        return

    await db.update_payment_status(payment_id, "approved")

    days = 30

    await db.activate_premium(
        user_id=payment["user_id"],
        premium_type=payment["tariff"],
        days=days
    )

    await callback.bot.send_message(
        payment["user_id"],
        f"""
🎉 <b>Premium faollashtirildi!</b>

💎 Tarif: <b>{payment['tariff']}</b>
⏳ Muddat: <b>{days} kun</b>

Amorix Premium xizmatlaridan foydalanishingiz mumkin.
"""
    )

    await callback.answer("✅ Premium berildi")


@router.callback_query(F.data.startswith("reject_payment:"))
async def reject_payment(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer()

    payment_id = callback.data.split(":")[1]

    await db.update_payment_status(
        payment_id,
        "rejected"
    )

    await callback.answer("❌ To'lov rad qilindi")