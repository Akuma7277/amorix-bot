import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select, update, delete, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from engine import async_session_maker
from models import (
    User,
    UserStatus,
    UserRole,
    PlanTier,
    Swipe,
    Match,
    Message,
    Block,
    Report,
    PaymentOrder,
    PaymentStatus,
    Notification,
    AdminAuditLog,
)
from config import ADMIN_IDS

logger = logging.getLogger(__name__)

# =========================================================================
# USER CRUD
# =========================================================================

async def get_user_by_telegram_id(telegram_id: int) -> Optional[User]:
    """Telegram ID orqali foydalanuvchini oladi."""
    try:
        async with async_session_maker() as session:
            stmt = select(User).where(User.telegram_id == telegram_id)
            res = await session.execute(stmt)
            return res.scalar_one_or_none()
    except Exception as e:
        logger.warning(f"get_user_by_telegram_id ({telegram_id}) xatosi: {e}")
        return None

async def get_user_by_id(user_id: int) -> Optional[User]:
    """Ichki User ID orqali foydalanuvchini oladi."""
    try:
        async with async_session_maker() as session:
            stmt = select(User).where(User.id == user_id)
            res = await session.execute(stmt)
            return res.scalar_one_or_none()
    except Exception as e:
        logger.warning(f"get_user_by_id ({user_id}) xatosi: {e}")
        return None

async def create_user_profile(telegram_id: int, user_data: dict) -> Optional[User]:
    """
    Foydalanuvchi anketasini yaratadi yoki mavjud bo'lsa yangilaydi.
    Foydalanuvchi darhol ACTIVE maqomiga ega bo'ladi (admin tasdiqlashini kutmasdan).
    """
    try:
        async with async_session_maker() as session:
            stmt = select(User).where(User.telegram_id == telegram_id)
            res = await session.execute(stmt)
            user = res.scalar_one_or_none()

            city = user_data.get("city") or user_data.get("region") or "Toshkent shahri"
            interests_val = user_data.get("interests", [])
            if isinstance(interests_val, list):
                interests_json = json.dumps(interests_val)
            else:
                interests_json = str(interests_val)

            photos = user_data.get("photos", [])
            photo_url = photos[0] if photos else user_data.get("photo")

            if not user:
                user = User(
                    telegram_id=telegram_id,
                    username=user_data.get("username"),
                    name=user_data.get("name"),
                    age=user_data.get("age", 20),
                    city=city,
                    gender=user_data.get("gender", "OTHER").upper(),
                    target_gender=user_data.get("looking_for", "ANY").upper(),
                    photo=photo_url,
                    bio=user_data.get("bio", ""),
                    interests=interests_json,
                    language=user_data.get("language", "uz"),
                    status=UserStatus.ACTIVE,
                    is_verified=False,
                    terms_accepted=True,
                    last_active_at=datetime.now(),
                )
                session.add(user)
            else:
                user.name = user_data.get("name", user.name)
                user.age = user_data.get("age", user.age)
                user.city = city
                user.gender = user_data.get("gender", user.gender).upper()
                user.target_gender = user_data.get("looking_for", user.target_gender).upper()
                if photo_url:
                    user.photo = photo_url
                user.bio = user_data.get("bio", user.bio)
                user.interests = interests_json
                user.language = user_data.get("language", user.language)
                user.status = UserStatus.ACTIVE
                user.terms_accepted = True
                user.last_active_at = datetime.now()

            await session.commit()
            await session.refresh(user)
            return user
    except Exception as e:
        logger.error(f"create_user_profile xatosi: {e}")
        return None

async def verify_user(user_id: int, admin_telegram_id: int, is_verified: bool = True) -> Optional[User]:
    """
    Admin post-moderatsiyasi: Foydalanuvchiga is_verified nishonini beradi yoki bekor qiladi.
    Bu foydalanuvchining botdan foydalanishini cheklamaydi.
    """
    try:
        async with async_session_maker() as session:
            stmt = select(User).where(User.id == user_id)
            res = await session.execute(stmt)
            user = res.scalar_one_or_none()
            if not user:
                return None

            user.is_verified = is_verified
            user.last_active_at = datetime.now()

            audit = AdminAuditLog(
                admin_id=admin_telegram_id,
                action="VERIFY_USER" if is_verified else "UNVERIFY_USER",
                target_type="USER",
                target_id=user.id,
                new_value=f"is_verified={is_verified}"
            )
            session.add(audit)
            await session.commit()
            await session.refresh(user)
            return user
    except Exception as e:
        logger.warning(f"verify_user ({user_id}) xatosi: {e}")
        return None

async def set_user_language(user_id: int, language: str) -> bool:
    """Foydalanuvchi tilini yangilaydi."""
    try:
        async with async_session_maker() as session:
            stmt = select(User).where(User.id == user_id)
            res = await session.execute(stmt)
            user = res.scalar_one_or_none()
            if user:
                user.language = language
                await session.commit()
                return True
            return False
    except Exception as e:
        logger.warning(f"set_user_language xatosi: {e}")
        return False

# =========================================================================
# PHOTO & MEDIA HELPERS
# =========================================================================

class PhotoMock:
    def __init__(self, file_id: str):
        self.file_id = file_id

async def get_user_photos(user_id: int) -> List[PhotoMock]:
    """Foydalanuvchi rasmlarini qaytaradi."""
    try:
        async with async_session_maker() as session:
            stmt = select(User).where(User.id == user_id)
            res = await session.execute(stmt)
            user = res.scalar_one_or_none()
            if user and user.photo:
                return [PhotoMock(user.photo)]
            return []
    except Exception:
        return []

# =========================================================================
# SEARCH & MATCHES
# =========================================================================

async def get_profiles_for_user(current_user: User, limit: int = 20) -> List[User]:
    """Mos foydalanuvchilar anketalarini oladi."""
    try:
        async with async_session_maker() as session:
            # All swiped users
            swiped_subquery = select(Swipe.target_id).where(Swipe.user_id == current_user.id).scalar_subquery()
            
            # All blocked users
            blocked_subquery = select(Block.blocked_id).where(Block.blocker_id == current_user.id).scalar_subquery()

            query = select(User).where(
                User.id != current_user.id,
                User.status.in_([UserStatus.ACTIVE, UserStatus.APPROVED]),
                User.is_deleted == False,
                User.id.notin_(swiped_subquery),
                User.id.notin_(blocked_subquery),
            )

            # Target gender filtering
            if current_user.target_gender and current_user.target_gender != "ANY":
                query = query.where(User.gender == current_user.target_gender)

            query = query.order_by(User.last_active_at.desc()).limit(limit)
            res = await session.execute(query)
            return list(res.scalars().all())
    except Exception as e:
        logger.warning(f"get_profiles_for_user xatosi: {e}")
        return []

# =========================================================================
# STATISTICS & ADMIN HELPERS
# =========================================================================

async def get_bot_statistics() -> Dict[str, Any]:
    """Admin statistikalarini hisoblaydi."""
    try:
        async with async_session_maker() as session:
            total_users = await session.scalar(select(func.count(User.id))) or 0
            active_users = await session.scalar(select(func.count(User.id)).where(User.status.in_([UserStatus.ACTIVE, UserStatus.APPROVED]))) or 0
            premium_users = await session.scalar(select(func.count(User.id)).where(User.is_premium == True)) or 0
            total_matches = await session.scalar(select(func.count(Match.id))) or 0
            verified_users = await session.scalar(select(func.count(User.id)).where(User.is_verified == True)) or 0

            return {
                "total_users": total_users,
                "active_users": active_users,
                "premium_users": premium_users,
                "total_matches": total_matches,
                "verified_users": verified_users,
            }
    except Exception as e:
        logger.warning(f"get_bot_statistics xatosi: {e}")
        return {
            "total_users": 0, "active_users": 0, "premium_users": 0,
            "total_matches": 0, "verified_users": 0
        }
