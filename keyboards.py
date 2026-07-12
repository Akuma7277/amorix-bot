from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from locations import get_regions, get_districts


def gender_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👨 Erkak", callback_data="gender:Erkak"),
            InlineKeyboardButton(text="👩 Ayol", callback_data="gender:Ayol"),
        ]
    ])


def phone_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Raqamimni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def region_kb() -> InlineKeyboardMarkup:
    regions = get_regions()
    rows = []
    for i in range(0, len(regions), 2):
        chunk = regions[i:i + 2]
        rows.append([
            InlineKeyboardButton(text=r, callback_data=f"region:{r}") for r in chunk
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def district_kb(region: str) -> InlineKeyboardMarkup:
    districts = get_districts(region)
    rows = []
    for i in range(0, len(districts), 2):
        chunk = districts[i:i + 2]
        rows.append([
            InlineKeyboardButton(text=d, callback_data=f"district:{d}") for d in chunk
        ])
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga (viloyat)", callback_data="back_to_region")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def photos_done_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Tugatdim, davom etish", callback_data="photos_done")]
    ])


def remove_kb():
    from aiogram.types import ReplyKeyboardRemove
    return ReplyKeyboardRemove()


def subscribe_kb(channel_username: str) -> InlineKeyboardMarkup:
    link = channel_username if channel_username.startswith("http") else f"https://t.me/{channel_username.lstrip('@')}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📺 Kanalga o'tish", url=link)],
        [InlineKeyboardButton(text="✅ A'zo bo'ldim, tekshirish", callback_data="check_sub")],
    ])

def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💘 Tanishuvni boshlash", callback_data="start_search")],
            [InlineKeyboardButton(text="❤️ Menga like bosganlar", callback_data="likes_me")],
            [InlineKeyboardButton(text="👤 Profilim", callback_data="my_profile")],
            [InlineKeyboardButton(text="🔄 Qaytadan ro'yxatdan o'tish", callback_data="restart_reg")],
        ]
    )



# ---------- Admin klaviaturalari ----------

def admin_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Statistika", callback_data="adm:stats")],
        [InlineKeyboardButton(text="👥 Foydalanuvchilar", callback_data="adm:users:0")],
        [InlineKeyboardButton(text="📢 Xabar yuborish (broadcast)", callback_data="adm:broadcast")],
        [InlineKeyboardButton(text="📺 Majburiy kanal sozlash", callback_data="adm:channel")],
        [InlineKeyboardButton(text="🗑 Majburiy kanalni o'chirish", callback_data="adm:channel_remove")],
    ])


def admin_back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Admin panelga qaytish", callback_data="adm:back")]
    ])


def users_page_kb(users: list, offset: int, has_more: bool) -> InlineKeyboardMarkup:
    rows = []
    for u in users:
        label = f"{u['full_name'] or u['username'] or u['telegram_id']} — {u['district'] or ''}"
        rows.append([InlineKeyboardButton(text=label[:60], callback_data=f"adm:view:{u['telegram_id']}")])

    nav = []
    if offset > 0:
        nav.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"adm:users:{max(offset-10,0)}"))
    if has_more:
        nav.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"adm:users:{offset+10}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton(text="⬅️ Admin panelga qaytish", callback_data="adm:back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def user_detail_kb(telegram_id: int, is_banned: bool) -> InlineKeyboardMarkup:
    ban_btn = (
        InlineKeyboardButton(text="✅ Blokdan chiqarish", callback_data=f"adm:unban:{telegram_id}")
        if is_banned else
        InlineKeyboardButton(text="🚫 Bloklash", callback_data=f"adm:ban:{telegram_id}")
    )
    return InlineKeyboardMarkup(inline_keyboard=[
        [ban_btn],
        [InlineKeyboardButton(text="⬅️ Ro'yxatga qaytish", callback_data="adm:users:0")],
    ])

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def profile_kb(user_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️",
                    callback_data=f"prev_photo_{user_id}"
                ),
                InlineKeyboardButton(
                    text="📸 Rasmlar",
                    callback_data=f"photos_{user_id}"
                ),
                InlineKeyboardButton(
                    text="➡️",
                    callback_data=f"next_photo_{user_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❤️ Like",
                    callback_data=f"like_{user_id}"
                ),
                InlineKeyboardButton(
                    text="💌 Xabar yuborish",
                    callback_data=f"message_{user_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⏭ Keyingi",
                    callback_data="start_search"
                )
            ]
        ]
    )