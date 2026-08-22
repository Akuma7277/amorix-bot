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

# =========================================================================
# COMPATIBILITY & ADMIN EXTENSIONS
# =========================================================================

BOOST_DURATION_MINUTES = 30

async def get_unapproved_photo():
    return None

async def get_all_active_user_telegram_ids() -> List[int]:
    try:
        async with async_session_maker() as session:
            stmt = select(User.telegram_id).where(User.status.in_([UserStatus.ACTIVE, UserStatus.APPROVED]))
            res = await session.execute(stmt)
            return list(res.scalars().all())
    except Exception:
        return []

async def get_payment_statistics() -> Dict[str, Any]:
    return {"total_amount": 0, "approved_count": 0, "pending_count": 0}

async def find_user_by_id_or_telegram_id(query: int | str) -> Optional[User]:
    try:
        val = int(query)
        async with async_session_maker() as session:
            stmt = select(User).where(or_(User.id == val, User.telegram_id == val))
            res = await session.execute(stmt)
            return res.scalar_one_or_none()
    except Exception:
        return None

async def set_user_status(user_id: int, status: UserStatus) -> bool:
    try:
        async with async_session_maker() as session:
            stmt = select(User).where(User.id == user_id)
            res = await session.execute(stmt)
            u = res.scalar_one_or_none()
            if u:
                u.status = status
                await session.commit()
                return True
            return False
    except Exception:
        return False

async def ban_user_with_duration(user_id: int, days: Optional[int], admin_id: int, reason: str = "") -> bool:
    return await set_user_status(user_id, UserStatus.BANNED)

async def lift_user_ban(user_id: int, admin_id: int) -> bool:
    return await set_user_status(user_id, UserStatus.ACTIVE)

async def delete_user_data(user_id: int) -> bool:
    try:
        async with async_session_maker() as session:
            stmt = select(User).where(User.id == user_id)
            res = await session.execute(stmt)
            u = res.scalar_one_or_none()
            if u:
                u.is_deleted = True
                u.status = UserStatus.DELETED
                await session.commit()
                return True
            return False
    except Exception:
        return False

async def auto_lift_expired_ban():
    pass

async def get_pending_report():
    return None

async def update_report_status(report_id: int, status: str, admin_id: int):
    pass

async def get_photo_by_id(photo_id: int):
    return None

async def get_pending_payment():
    return None

async def update_payment_status(payment_id: int, status: str, admin_id: int):
    pass

async def get_pending_verification_request():
    return None

async def update_verification_request_status(req_id: int, status: str, admin_id: int):
    pass

async def create_admin_log(admin_id: int, action: str, comment: str = "", user_id: Optional[int] = None):
    pass

async def approve_photo(photo_id: int, admin_id: int):
    pass

async def reject_photo(photo_id: int, admin_id: int, reason: str = ""):
    pass

async def get_report_by_id(report_id: int):
    return None

async def get_admin_logs(limit: int = 10, offset: int = 0):
    return []

async def update_user_profile_field(user_id: int, field: str, value: Any) -> bool:
    try:
        async with async_session_maker() as session:
            stmt = select(User).where(User.id == user_id)
            res = await session.execute(stmt)
            u = res.scalar_one_or_none()
            if u and hasattr(u, field):
                setattr(u, field, value)
                await session.commit()
                return True
            return False
    except Exception:
        return False

def is_admin_user(telegram_id: int) -> bool:
    return telegram_id in ADMIN_IDS

async def add_admin_by_telegram_id(admin_id: int, added_by: int) -> bool:
    if admin_id not in ADMIN_IDS:
        ADMIN_IDS.append(admin_id)
    return True

async def remove_admin_by_telegram_id(admin_id: int, removed_by: int) -> bool:
    if admin_id in ADMIN_IDS:
        ADMIN_IDS.remove(admin_id)
    return True

async def get_dynamic_admins():
    return ADMIN_IDS

async def set_setting(key: str, value: str):
    pass

async def get_setting(key: str, default: str = "") -> str:
    return default

# Match & Chat helpers
async def add_like_and_check_match(from_user_id: int, to_user_id: int, is_super: bool = False) -> Tuple[bool, Optional[Match]]:
    return False, None

async def get_user_matches(user_id: int) -> List[Any]:
    return []

async def get_match_by_id(match_id: int):
    return None

async def create_chat_message(match_id: int, sender_id: int, text: str):
    return None

def calculate_profile_completion(user: User) -> int:
    score = 40
    if user.photo: score += 30
    if user.bio: score += 15
    if user.interests: score += 15
    return min(score, 100)

def calculate_compatibility_score(u1_id: int, u2_id: int) -> int:
    return 88

def get_compatibility_reasons(u1_id: int, u2_id: int) -> str:
    return "Umumiy qiziqishlar va bir xil maqsad"

def get_trust_badges(user: User) -> str:
    return "✅ Tasdiqlangan" if user.is_verified else "Yangi"

def get_next_completion_step(user: User) -> str:
    return "Rasm yuklang"

async def create_report(from_user_id: int, to_user_id: int, category: str, description: str = ""):
    return None

async def get_users_who_liked_me_full(user_id: int):
    return []

async def unmatch_users(u1: int, u2: int):
    pass

async def is_user_blocked(u1: int, u2: int) -> bool:
    return False

async def log_user_event(user_id: int, event_type: str, details: str = ""):
    pass

async def create_verification_request(user_id: int, photo_id: str):
    return None

async def create_payment_record(user_id: int, plan: str, amount: float, receipt: str):
    return None

async def get_users_who_liked_me(user_id: int):
    return []

async def block_user(blocker: int, blocked: int):
    pass

async def get_user_referrals(user_id: int):
    return []

async def check_and_consume_like_quota(user_id: int, is_super: bool = False):
    return True, 50

async def mark_messages_as_read(match_id: int, user_id: int):
    pass

async def activate_profile_boost(user_id: int):
    return True

async def is_boost_active(user_id: int) -> bool:
    return False

async def get_all_admin_ids() -> List[int]:
    return ADMIN_IDS

def get_online_status(user: User) -> str:
    return "🟢 Onlayn"

async def create_gift(sender_id: int, receiver_id: int, gift_type: str, message: str = ""):
    return None

async def get_boost_remaining_minutes(user_id: int) -> int:
    return 0

async def create_support_message(user_id: int, text: str):
    return None

async def set_primary_photo(user_id: int, photo_id: int):
    return True

async def delete_photo(photo_id: int, user_id: int):
    return True

async def add_photo(user_id: int, file_id: str):
    return None
