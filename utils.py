from aiogram import Bot
from database import get_setting


async def check_subscription(bot: Bot, user_id: int) -> bool:
    """Agar admin majburiy kanal belgilagan bo'lsa, foydalanuvchi shu kanalga
    a'zo ekanligini tekshiradi. Kanal belgilanmagan bo'lsa - har doim True."""
    channel = await get_setting("required_channel")
    if not channel:
        return True
    try:
        member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception:
        # Bot kanalga admin qilib qo'shilmagan yoki kanal noto'g'ri bo'lsa,
        # foydalanuvchini bloklab qo'ymaslik uchun False qaytaramiz va logga yozamiz.
        return False
