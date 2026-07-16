from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from states import PremiumStates

import keyboards as kb
import database as db
import aiosqlite

router = Router()


TARIFFS = {
    "silver": {
        "name": "🥈 Silver",
        "price": 19000,
        "days": 30,
    },
    "gold": {
        "name": "🥇 Gold",
        "price": 39000,
        "days": 30,
    },
    "diamond": {
        "name": "💎 Diamond",
        "price": 59000,
        "days": 30,
    },
}


@router.callback_query(F.data == "premium")
async def premium_menu(callback: CallbackQuery):
    await callback.answer()

    text = (
        "💎 <b>AMORIX Premium</b>\n\n"
        "Tarifni tanlang:"
    )

    await callback.message.answer(
        text,
        reply_markup=kb.premium_kb()
    )

@router.callback_query(F.data.startswith("buy_"))
async def buy_tariff(callback: CallbackQuery, state: FSMContext):
    tariff_key = callback.data.replace("buy_", "")

    tariff = TARIFFS.get(tariff_key)

    if not tariff:
        await callback.answer("Tarif topilmadi", show_alert=True)
        return

    payment_id = await db.create_payment(
        user_id=callback.from_user.id,
        tariff=tariff["name"],
        amount=tariff["price"]
    )
    
    await state.update_data(payment_id=payment_id)
    await state.set_state(PremiumStates.waiting_receipt)

    await callback.message.answer(
"📸 To'lov chekini yuboring."
    )

    await callback.answer()

    await callback.message.answer(
        f"""
💎 <b>{tariff['name']}</b>

💰 Narxi: <b>{tariff['price']:,} so'm</b>
⏳ Muddat: <b>{tariff['days']} kun</b>

🆔 To'lov ID:
<code>{payment_id}</code>

💳 To'lov uchun karta:
<code>9860600433476527</code>

To'lov qilgandan keyin 📸 chekni yuboring.
"""
    )

@router.message(PremiumStates.waiting_receipt)
async def receive_receipt(message: Message, state: FSMContext):

    if not message.photo:
        await message.answer(
            "📸 Iltimos, chek rasmini yuboring."
        )
        return

    photo_id = message.photo[-1].file_id

    data = await state.get_data()

    payment_id = data.get("payment_id")

    if not payment_id:
        await message.answer(
            "❌ To'lov topilmadi. Qaytadan urinib ko'ring."
        )
        await state.clear()
        return

    async with aiosqlite.connect(db.DB_PATH) as conn:
        await conn.execute(
            """
            UPDATE payments
            SET receipt_file = ?
            WHERE payment_id = ?
            """,
            (photo_id, payment_id)
        )
        await conn.commit()

    await state.clear()

    await message.answer(
        "✅ Chek qabul qilindi.\n\n"
        "⏳ To'lov tekshirilmoqda."
    )