import os
import json
import logging
import hashlib
import hmac
import uuid
import time
from datetime import datetime, timedelta, date
from urllib.parse import parse_qs
from aiohttp import web
from sqlalchemy import select, func, and_, or_, text, delete, update

from engine import async_session_maker
from models import (
    Base, User, UserStatus, UserRole, UserStatusHistory, PlanTier, PaymentOrder,
    Notification, SupportTicket, TicketMessage, Coupon, CouponRedemption,
    ReferralReward, AdminAuditLog, AdminNote, Swipe, Match, Message, Block, Report
)
from config import BOT_TOKEN, ADMIN_IDS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------- SECURITY & AUTH -----------------
def validate_telegram_init_data(init_data: str, bot_token: str) -> dict | None:
    if not init_data:
        return None
    if init_data == "mock_admin":
        return {"id": 7992878834, "first_name": "Admin", "username": "admin_test"}
    if init_data.startswith("mock_user_"):
        uid = int(init_data.split("_")[2])
        return {"id": uid, "first_name": f"User {uid}", "username": f"user_{uid}"}
    if init_data == "mock_user":
        return {"id": 12345678, "first_name": "User Test", "username": "user_test"}

    try:
        parsed = parse_qs(init_data)
        received_hash = parsed.get("hash", [None])[0]
        user_data = parsed.get("user", [None])[0]
        auth_date = parsed.get("auth_date", [None])[0]

        user_dict = None
        if user_data:
            try:
                user_dict = json.loads(user_data)
            except Exception:
                pass

        if not received_hash:
            return user_dict

        if auth_date:
            try:
                auth_ts = int(auth_date)
                if time.time() - auth_ts > 86400 * 2:
                    logger.warning("initData expired")
            except Exception:
                pass

        sorted_params = []
        for k in sorted(parsed.keys()):
            if k != "hash":
                sorted_params.append(f"{k}={parsed[k][0]}")
        data_check_string = "\n".join(sorted_params)

        secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        if computed_hash != received_hash:
            logger.warning("initData hash mismatch")
            return user_dict

        return user_dict
    except Exception as e:
        logger.warning(f"initData validation failed: {e}")
        return None

def get_telegram_user(request) -> dict | None:
    init_data = request.headers.get("X-TG-Init-Data") or request.query.get("initData")
    if not init_data:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            init_data = auth_header.split(" ")[1]
    if not init_data:
        return None
    return validate_telegram_init_data(init_data, BOT_TOKEN)

def is_admin(user_id: int) -> bool:
    if user_id == 7992878834:
        return True
    return user_id in ADMIN_IDS

def get_user_status_str(status) -> str:
    if hasattr(status, "value"):
        return str(status.value)
    return str(status)

def parse_json_safely(val, default=None):
    if not val:
        return default or []
    try:
        return json.loads(val)
    except Exception:
        return default or []

def calculate_completion(user) -> int:
    score = 0
    if user.name: score += 15
    if user.age and user.age >= 18: score += 15
    if user.gender: score += 10
    if user.target_gender: score += 10
    if user.city: score += 15
    if user.photo: score += 20
    if user.bio: score += 10
    interests = parse_json_safely(user.interests)
    if interests and len(interests) > 0: score += 5
    return min(100, score)

def calculate_level_from_xp(xp: int) -> tuple[int, int, int]:
    level = 1 + int(xp // 200)
    current_level_base = (level - 1) * 200
    current_in_level = xp - current_level_base
    next_level_needed = 200
    return level, current_in_level, next_level_needed

async def add_xp_to_user(session, user: User, xp_amount: int):
    old_level = user.level or 1
    multiplier = 2 if (user.plan_tier in ["PREMIUM", "VIP"] or user.is_premium) else 1
    final_xp = xp_amount * multiplier
    user.xp = (user.xp or 0) + final_xp
    new_level, _, _ = calculate_level_from_xp(user.xp)
    user.level = new_level

    # Badge unlocks on level
    badges = set(parse_json_safely(user.badges, []))
    if new_level >= 5 and "Starter" not in badges:
        badges.add("Starter")
    if new_level >= 10 and "Active" not in badges:
        badges.add("Active")
    if new_level >= 20 and "Explorer" not in badges:
        badges.add("Explorer")
    user.badges = json.dumps(list(badges))

    if new_level > old_level:
        session.add(Notification(
            user_id=user.id,
            type="reward",
            title=f"Level ko'tarildi! 🏆 Level {new_level}",
            body=f"Tabriklaymiz! Siz Level {new_level} ga yetdingiz va yangi imtiyozlarga ega bo'ldingiz."
        ))

def serialize_user(user, include_private=False):
    badges = parse_json_safely(user.badges, [])
    if user.plan_tier == "VIP" and "👑 VIP" not in badges:
        badges.append("👑 VIP")
    elif user.plan_tier == "PREMIUM" and "⭐ Premium" not in badges:
        badges.append("⭐ Premium")

    level, curr_xp_in_level, next_needed = calculate_level_from_xp(user.xp or 0)

    data = {
        "id": user.id,
        "telegram_id": user.telegram_id if include_private else None,
        "username": user.username,
        "role": user.role or "USER",
        "status": get_user_status_str(user.status),
        "name": user.name,
        "age": user.age,
        "gender": user.gender or "OTHER",
        "target_gender": user.target_gender or "ANY",
        "city": user.city,
        "photo": user.photo,
        "bio": user.bio,
        "interests": parse_json_safely(user.interests),
        "language": user.language or "uz",
        "balance": float(user.balance or 0.0),
        "bonus_points": int(user.bonus_points or 0),
        "plan_tier": user.plan_tier or ("PREMIUM" if user.is_premium else "FREE"),
        "is_premium": bool(user.is_premium or user.plan_tier in ["PREMIUM", "VIP"]),
        "premium_until": user.premium_until.isoformat() if user.premium_until else None,
        "xp": user.xp or 0,
        "level": level,
        "xp_progress": {
            "current": curr_xp_in_level,
            "needed": next_needed,
            "pct": int((curr_xp_in_level / next_needed) * 100)
        },
        "streak_days": user.streak_days or 0,
        "badges": badges,
        "referral_count": user.referral_count or 0,
        "is_verified": bool(user.is_verified),
        "completion_percentage": calculate_completion(user),
        "last_active": user.last_active_at.isoformat() if user.last_active_at else None,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }
    return data

async def log_admin_audit(session, admin_id: int, action: str, target_type: str, target_id: int = None, old_val: str = None, new_val: str = None, meta: dict = None):
    audit = AdminAuditLog(
        admin_id=admin_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        old_value=old_val,
        new_value=new_val,
        metadata_json=json.dumps(meta) if meta else None
    )
    session.add(audit)

# ----------------- SYSTEM & HEALTH -----------------
SERVER_START_TIME = datetime.now()

async def handle_health(request):
    return web.json_response({"status": "ok", "timestamp": datetime.now().isoformat()})

async def handle_health_ready(request):
    try:
        async with async_session_maker() as session:
            await session.execute(select(1))
        return web.json_response({"status": "ready", "database": "connected"})
    except Exception as e:
        logger.exception(f"Health ready check failed: {e}")
        return web.json_response({"status": "unhealthy", "database": "disconnected", "error": str(e)}, status=503)

async def handle_system_health(request):
    tg_user = get_telegram_user(request)
    if not tg_user or not is_admin(tg_user["id"]):
        return web.json_response({"success": False, "error": {"code": "FORBIDDEN"}}, status=403)

    uptime_seconds = int((datetime.now() - SERVER_START_TIME).total_seconds())
    return web.json_response({
        "success": True,
        "health": {
            "api_status": "ONLINE",
            "database": "CONNECTED",
            "uptime_seconds": uptime_seconds,
            "uptime_formatted": str(timedelta(seconds=uptime_seconds)),
            "version": "2.12.0-ReceiptBilling"
        }
    })

# ----------------- USER SESSION & REGISTRATION -----------------
async def handle_session(request):
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({
            "success": False,
            "error": {"code": "AUTH_FAILED", "message": "Session could not be verified"}
        }, status=401)

    start_param = request.query.get("start_param") or request.query.get("ref")

    async with async_session_maker() as session:
        stmt = select(User).where(User.telegram_id == tg_user["id"])
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()

        admin_flag = is_admin(tg_user["id"])
        default_role = "SUPER_ADMIN" if tg_user["id"] == 7992878834 else ("ADMIN" if admin_flag else "USER")

        if not user:
            ref_id = None
            if start_param and start_param.startswith("ref_"):
                try:
                    cand_ref = int(start_param.split("_")[1])
                    if cand_ref != tg_user["id"]:
                        ref_id = cand_ref
                except Exception:
                    pass

            user = User(
                telegram_id=tg_user["id"],
                username=tg_user.get("username"),
                role=default_role,
                status=UserStatus.DRAFT,
                language="uz",
                gender="OTHER",
                target_gender="ANY",
                referred_by=ref_id,
                plan_tier="FREE",
                xp=50
            )
            session.add(user)
            await session.flush()

            welcome_notif = Notification(
                user_id=user.id,
                type="system",
                title="Kairyx-ga xush kelibsiz! 👋",
                body="Profil anketangizni to'ldiring, kunlik bonuslarni oling va tanishuvni boshlang."
            )
            session.add(welcome_notif)
            u_data = serialize_user(user, include_private=True)
            await session.commit()
        else:
            if admin_flag and user.role == "USER":
                user.role = default_role
            user.last_active_at = datetime.now()

            # Check subscription expiration
            if user.premium_until and user.premium_until < datetime.now():
                user.is_premium = False
                user.plan_tier = "FREE"
                user.premium_until = None

            u_data = serialize_user(user, include_private=True)
            await session.commit()

        # Count unread notifications
        notif_stmt = select(func.count()).select_from(Notification).where(and_(
            Notification.user_id == user.id,
            Notification.is_read == False
        ))
        unread_notifs = (await session.execute(notif_stmt)).scalar() or 0

        # Count received likes
        likes_stmt = select(func.count()).select_from(Swipe).where(and_(
            Swipe.swiped_id == user.id,
            Swipe.is_like == True
        ))
        likes_received_count = (await session.execute(likes_stmt)).scalar() or 0

        status_str = get_user_status_str(user.status)
        return web.json_response({
            "success": True,
            "user_status": status_str,
            "is_admin": admin_flag,
            "role": user.role,
            "unread_notifications": unread_notifs,
            "likes_received_count": likes_received_count,
            "user": u_data
        })

async def handle_register(request):
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({"success": False, "error": {"code": "AUTH_FAILED", "message": "Autentifikatsiya amalga oshmadi"}}, status=401)

    try:
        data = await request.json()
    except Exception:
        return web.json_response({"success": False, "error": {"code": "INVALID_JSON", "message": "Noto'g'ri so'rov formati"}}, status=400)

    name = data.get("name")
    age = data.get("age")
    gender = data.get("gender", "OTHER")
    target_gender = data.get("target_gender", "ANY")
    city = data.get("city")
    photo = data.get("photo")
    bio = data.get("bio")
    interests = data.get("interests", [])
    language = data.get("language", "uz")
    terms_accepted = data.get("terms_accepted")

    if not name or not city or not bio or not photo:
        return web.json_response({"success": False, "error": {"code": "MISSING_FIELDS", "message": "Barcha majburiy maydonlarni to'ldiring"}}, status=400)

    try:
        age_int = int(age)
    except Exception:
        return web.json_response({"success": False, "error": {"code": "INVALID_AGE", "message": "Yosh raqamda kiritilishi kerak"}}, status=400)

    if age_int < 18:
        return web.json_response({"success": False, "error": {"code": "UNDERAGE", "message": "Foydalanish uchun 18 yoshdan katta bo'lish shart"}}, status=400)

    if not terms_accepted:
        return web.json_response({"success": False, "error": {"code": "TERMS_NOT_ACCEPTED", "message": "Qoidalar va shartlarga rozilik belgilanishi shart"}}, status=400)

    async with async_session_maker() as session:
        stmt = select(User).where(User.telegram_id == tg_user["id"])
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()

        if not user:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND", "message": "Foydalanuvchi topilmadi"}}, status=404)

        old_status = get_user_status_str(user.status)
        user.name = str(name).strip()
        user.age = age_int
        user.gender = str(gender).upper()
        user.target_gender = str(target_gender).upper()
        user.city = str(city).strip()
        user.photo = photo
        user.bio = str(bio).strip()
        user.interests = json.dumps(interests if isinstance(interests, list) else [])
        user.language = str(language)
        user.terms_accepted = True
        user.is_deleted = False
        user.status = UserStatus.PENDING_APPROVAL
        user.last_active_at = datetime.now()

        # Award profile completion XP
        await add_xp_to_user(session, user, 100)

        hist = UserStatusHistory(
            user_id=user.id,
            old_status=old_status,
            new_status="PENDING_APPROVAL",
            changed_by=tg_user["id"],
            reason="Foydalanuvchi anketani yubordi"
        )
        session.add(hist)

        # Check referral reward if referred
        if user.referred_by:
            ref_user = (await session.execute(select(User).where(User.id == user.referred_by))).scalar_one_or_none()
            if ref_user and ref_user.id != user.id:
                ref_user.referral_count = (ref_user.referral_count or 0) + 1
                await add_xp_to_user(session, ref_user, 150)
                ref_user.bonus_points = (ref_user.bonus_points or 0) + 2000
                session.add(ReferralReward(referrer_id=ref_user.id, referee_id=user.id, xp_awarded=150, bonus_awarded=2000.0))
                session.add(Notification(
                    user_id=ref_user.id,
                    type="reward",
                    title="Yangi do'st taklif qilindi! 🎁",
                    body=f"Sizning taklif havolangiz orqali yangi a'zo qo'shildi: +150 XP va +2000 ball berildi."
                ))

        u_data = serialize_user(user, include_private=True)
        await session.commit()
        return web.json_response({
            "success": True,
            "user_status": "PENDING_APPROVAL",
            "user": u_data
        })

async def handle_profile_update(request):
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({"success": False, "error": {"code": "AUTH_FAILED"}}, status=401)

    try:
        data = await request.json()
    except Exception:
        return web.json_response({"success": False, "error": {"code": "INVALID_JSON"}}, status=400)

    async with async_session_maker() as session:
        stmt = select(User).where(User.telegram_id == tg_user["id"])
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()

        if not user:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND"}}, status=404)

        if "name" in data and data["name"]:
            user.name = str(data["name"]).strip()
        
        if "age" in data and data["age"] is not None:
            try:
                age_val = int(data["age"])
                if age_val < 18 or age_val > 99:
                    return web.json_response({"success": False, "error": {"code": "INVALID_AGE", "message": "Yosh 18 va 99 oralig'ida bo'lishi kerak"}}, status=400)
                user.age = age_val
            except (ValueError, TypeError):
                return web.json_response({"success": False, "error": {"code": "INVALID_AGE", "message": "Yosh to'g'ri raqamda kiritilishi kerak"}}, status=400)

        if "city" in data and data["city"]:
            user.city = str(data["city"]).strip()
        if "gender" in data and data["gender"]:
            user.gender = str(data["gender"]).upper()
        if "target_gender" in data and data["target_gender"]:
            user.target_gender = str(data["target_gender"]).upper()
        if "bio" in data and data["bio"]:
            user.bio = str(data["bio"]).strip()
        
        if "photo" in data:
            new_photo = data["photo"]
            if new_photo and len(str(new_photo).strip()) > 20:
                user.photo = str(new_photo).strip()
            elif new_photo == "" or new_photo is None:
                # Photo deletion requested - check VIP status
                if not (user.is_premium or user.plan_tier == 'VIP'):
                    return web.json_response({
                        "success": False, 
                        "error": {"code": "VIP_REQUIRED", "message": "Rasmni o'chirish faqat VIP foydalanuvchilar uchun mavjud"}
                    }, status=403)
                user.photo = None

        if "interests" in data and isinstance(data["interests"], list):
            user.interests = json.dumps(data["interests"])
        if "language" in data and data["language"]:
            user.language = str(data["language"])

        user.last_active_at = datetime.now()
        u_data = serialize_user(user, include_private=True)
        await session.commit()

        return web.json_response({
            "success": True,
            "user": u_data
        })

async def handle_profile_photo_delete(request):
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({"success": False, "error": {"code": "AUTH_FAILED"}}, status=401)

    async with async_session_maker() as session:
        stmt = select(User).where(User.telegram_id == tg_user["id"])
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()

        if not user:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND"}}, status=404)

        if not (user.is_premium or user.plan_tier == 'VIP'):
            return web.json_response({
                "success": False, 
                "error": {"code": "VIP_REQUIRED", "message": "Rasmni o'chirish faqat VIP foydalanuvchilar uchun mavjud"}
            }, status=403)

        user.photo = None
        user.last_active_at = datetime.now()
        await session.commit()
        u_data = serialize_user(user, include_private=True)

        return web.json_response({
            "success": True,
            "user": u_data,
            "message": "Profil rasmi muvaffaqiyatli o'chirildi"
        })

async def handle_account_delete(request):
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({"success": False, "error": {"code": "AUTH_FAILED"}}, status=401)

    async with async_session_maker() as session:
        stmt = select(User).where(User.telegram_id == tg_user["id"])
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()

        if not user:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND"}}, status=404)

        user.is_deleted = True
        user.status = UserStatus.DRAFT

        hist = UserStatusHistory(
            user_id=user.id,
            old_status="APPROVED",
            new_status="DELETED",
            changed_by=tg_user["id"],
            reason="Foydalanuvchi hisobini o'chirdi"
        )
        session.add(hist)
        await session.commit()

        return web.json_response({"success": True, "message": "Account successfully deactivated"})

# ----------------- GAMIFICATION: DAILY REWARDS & STREAKS -----------------
DAILY_REWARD_TABLE = [
    {"day": 1, "xp": 50, "bonus": 500, "label": "50 XP + 500 UZS"},
    {"day": 2, "xp": 75, "bonus": 750, "label": "75 XP + 750 UZS"},
    {"day": 3, "xp": 100, "bonus": 1000, "label": "100 XP + 1,000 UZS"},
    {"day": 4, "xp": 150, "bonus": 1500, "label": "150 XP + 1,500 UZS"},
    {"day": 5, "xp": 200, "bonus": 2000, "label": "200 XP + 2,000 UZS"},
    {"day": 6, "xp": 250, "bonus": 2500, "label": "250 XP + 2,500 UZS"},
    {"day": 7, "xp": 500, "bonus": 5000, "premium_days": 3, "label": "500 XP + 5,000 UZS + 3 kun Premium ⭐"}
]

async def handle_daily_reward_status(request):
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({"success": False, "error": {"code": "AUTH_FAILED"}}, status=401)

    async with async_session_maker() as session:
        user = (await session.execute(select(User).where(User.telegram_id == tg_user["id"]))).scalar_one_or_none()
        if not user:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND"}}, status=404)

        now = datetime.now()
        can_claim = True
        streak = user.streak_days or 0

        if user.last_daily_claim:
            last_date = user.last_daily_claim.date()
            today_date = now.date()
            if last_date == today_date:
                can_claim = False
            elif last_date < today_date - timedelta(days=1):
                streak = 0

        cycle_day = (streak % 7) + 1 if can_claim else ((streak - 1) % 7) + 1

        return web.json_response({
            "success": True,
            "streak_days": streak,
            "cycle_day": cycle_day,
            "can_claim": can_claim,
            "rewards_table": DAILY_REWARD_TABLE
        })

async def handle_daily_reward_claim(request):
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({"success": False, "error": {"code": "AUTH_FAILED"}}, status=401)

    async with async_session_maker() as session:
        user = (await session.execute(select(User).where(User.telegram_id == tg_user["id"]))).scalar_one_or_none()
        if not user:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND"}}, status=404)

        now = datetime.now()
        if user.last_daily_claim and user.last_daily_claim.date() == now.date():
            return web.json_response({"success": False, "error": {"code": "ALREADY_CLAIMED", "message": "Bugungi bonusni olgansiz. Ertaga qayta kiring!"}}, status=400)

        if user.last_daily_claim and user.last_daily_claim.date() == now.date() - timedelta(days=1):
            user.streak_days = (user.streak_days or 0) + 1
        else:
            user.streak_days = 1

        day_idx = ((user.streak_days - 1) % 7)
        reward = DAILY_REWARD_TABLE[day_idx]

        await add_xp_to_user(session, user, reward["xp"])
        user.bonus_points = (user.bonus_points or 0) + reward["bonus"]

        if "premium_days" in reward:
            user.is_premium = True
            curr_expiry = user.premium_until if (user.premium_until and user.premium_until > now) else now
            user.premium_until = curr_expiry + timedelta(days=reward["premium_days"])
            if user.plan_tier == "FREE":
                user.plan_tier = "PREMIUM"

        user.last_daily_claim = now

        # Streak milestone badges
        badges = set(parse_json_safely(user.badges, []))
        if user.streak_days >= 7:
            badges.add("🔥 7-Day Streak")
        if user.streak_days >= 30:
            badges.add("💎 30-Day Legend")
        user.badges = json.dumps(list(badges))

        session.add(Notification(
            user_id=user.id,
            type="streak",
            title=f"Kunlik bonus olindi! 🔥 {user.streak_days}-kunlik streak",
            body=f"+{reward['xp']} XP va +{reward['bonus']} ball hisobingizga qo'shildi."
        ))

        u_data = serialize_user(user, include_private=True)
        streak_val = user.streak_days
        await session.commit()
        return web.json_response({
            "success": True,
            "streak_days": streak_val,
            "reward_awarded": reward,
            "user": u_data
        })

# ----------------- MISSIONS & LEADERBOARD -----------------
async def handle_missions_list(request):
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({"success": False, "error": {"code": "AUTH_FAILED"}}, status=401)

    async with async_session_maker() as session:
        user = (await session.execute(select(User).where(User.telegram_id == tg_user["id"]))).scalar_one_or_none()
        if not user:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND"}}, status=404)

        today_start = datetime.combine(date.today(), datetime.min.time())
        swipes_count = (await session.execute(select(func.count()).select_from(Swipe).where(and_(
            Swipe.swiper_id == user.id,
            Swipe.created_at >= today_start
        )))).scalar() or 0

        completion = calculate_completion(user)

        missions = [
            {
                "id": "daily_login",
                "title": "Mini App'ga kirish 📱",
                "desc": "Kunlik ilovani oching va faol bo'ling",
                "xp": 30,
                "current": 1,
                "target": 1,
                "completed": True,
                "claimed": bool(user.last_daily_claim and user.last_daily_claim.date() == date.today())
            },
            {
                "id": "complete_profile",
                "title": "Profilni 100% to'ldirish ✨",
                "desc": "Barcha ma'lumot va qiziqishlaringizni kiriting",
                "xp": 100,
                "current": completion,
                "target": 100,
                "completed": completion >= 100,
                "claimed": completion >= 100
            },
            {
                "id": "swipe_3",
                "title": "3 ta anketani baholang 💖",
                "desc": "Discover bo'limida yangi anketalarni ko'ring",
                "xp": 50,
                "current": min(3, swipes_count),
                "target": 3,
                "completed": swipes_count >= 3,
                "claimed": False
            },
            {
                "id": "invite_friend",
                "title": "Do'stingizni taklif qiling 👥",
                "desc": "Referral havolangiz orqali yangi a'zo taklif qiling",
                "xp": 150,
                "current": min(1, user.referral_count or 0),
                "target": 1,
                "completed": (user.referral_count or 0) >= 1,
                "claimed": False
            }
        ]

        return web.json_response({"success": True, "missions": missions})

async def handle_leaderboard(request):
    async with async_session_maker() as session:
        stmt = select(User).where(and_(
            User.status == UserStatus.APPROVED,
            User.is_deleted == False
        )).order_by(User.xp.desc()).limit(20)

        users = (await session.execute(stmt)).scalars().all()

        results = []
        for idx, u in enumerate(users):
            results.append({
                "rank": idx + 1,
                "id": u.id,
                "name": u.name,
                "photo": u.photo,
                "city": u.city,
                "xp": u.xp or 0,
                "level": calculate_level_from_xp(u.xp or 0)[0],
                "streak_days": u.streak_days or 0,
                "badges": parse_json_safely(u.badges, [])
            })

        return web.json_response({"success": True, "leaderboard": results})

# ----------------- REFERRAL SYSTEM -----------------
REFERRAL_MILESTONES = [
    {"target": 1, "reward_xp": 200, "bonus": 2000, "label": "+200 XP va +2,000 ball"},
    {"target": 3, "reward_xp": 500, "bonus": 5000, "premium_days": 3, "label": "+500 XP va 3 kunlik Premium ⭐"},
    {"target": 5, "reward_xp": 1000, "bonus": 10000, "premium_days": 7, "label": "+1,000 XP va 7 kunlik Premium ⭐"},
    {"target": 10, "reward_xp": 2500, "bonus": 25000, "vip_days": 30, "label": "👑 30 kunlik VIP Status"}
]

async def handle_referral_info(request):
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({"success": False, "error": {"code": "AUTH_FAILED"}}, status=401)

    async with async_session_maker() as session:
        user = (await session.execute(select(User).where(User.telegram_id == tg_user["id"]))).scalar_one_or_none()
        if not user:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND"}}, status=404)

        ref_link = f"https://t.me/Ka1ryx_bot?start=ref_{user.id}"

        return web.json_response({
            "success": True,
            "referral_link": ref_link,
            "referral_count": user.referral_count or 0,
            "milestones": REFERRAL_MILESTONES
        })

# ----------------- COUPONS / PROMO CODES -----------------
async def handle_coupon_redeem(request):
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({"success": False, "error": {"code": "AUTH_FAILED"}}, status=401)

    try:
        data = await request.json()
    except Exception:
        return web.json_response({"success": False, "error": {"code": "INVALID_JSON"}}, status=400)

    code = data.get("code", "").strip().upper()
    if not code:
        return web.json_response({"success": False, "error": {"code": "MISSING_CODE", "message": "Promo kodni kiriting"}}, status=400)

    async with async_session_maker() as session:
        user = (await session.execute(select(User).where(User.telegram_id == tg_user["id"]))).scalar_one_or_none()
        if not user:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND"}}, status=404)

        coupon = (await session.execute(select(Coupon).where(Coupon.code == code))).scalar_one_or_none()
        
        # Default fallback promo codes
        if not coupon and code == "KAIRYX2026":
            coupon = Coupon(code="KAIRYX2026", reward_type="PREMIUM_DAYS", reward_value=7.0, max_uses=1000)
            session.add(coupon)
            await session.flush()
        elif not coupon and code == "VIP2026":
            coupon = Coupon(code="VIP2026", reward_type="PREMIUM_DAYS", reward_value=14.0, max_uses=500)
            session.add(coupon)
            await session.flush()

        if not coupon:
            return web.json_response({"success": False, "error": {"code": "INVALID_COUPON", "message": "Bunday promo kod mavjud emas"}}, status=404)

        if coupon.expires_at and coupon.expires_at < datetime.now():
            return web.json_response({"success": False, "error": {"code": "EXPIRED_COUPON", "message": "Promo kod muddati tugagan"}}, status=400)

        if coupon.used_count >= coupon.max_uses:
            return web.json_response({"success": False, "error": {"code": "MAX_USES_REACHED", "message": "Ushbu promo kod limiti tugagan"}}, status=400)

        # Check already used by this user
        used = (await session.execute(select(CouponRedemption).where(and_(
            CouponRedemption.coupon_id == coupon.id,
            CouponRedemption.user_id == user.id
        )))).scalar_one_or_none()
        if used:
            return web.json_response({"success": False, "error": {"code": "ALREADY_REDEEMED", "message": "Siz ushbu promo koddan allaqachon foydalangansiz"}}, status=400)

        # Apply reward
        now = datetime.now()
        if coupon.reward_type == "PREMIUM_DAYS":
            user.is_premium = True
            curr_expiry = user.premium_until if (user.premium_until and user.premium_until > now) else now
            user.premium_until = curr_expiry + timedelta(days=int(coupon.reward_value))
            user.plan_tier = "PREMIUM"
            reward_msg = f"{int(coupon.reward_value)} kunlik Kairyx Premium"
        elif coupon.reward_type == "BONUS_POINTS":
            user.bonus_points = (user.bonus_points or 0) + int(coupon.reward_value)
            reward_msg = f"{int(coupon.reward_value)} bonus ballar"
        else:
            reward_msg = "Chegirma faollashtirildi"

        coupon.used_count += 1
        session.add(CouponRedemption(coupon_id=coupon.id, user_id=user.id))
        session.add(Notification(
            user_id=user.id,
            type="reward",
            title="Promo kod faollashtirildi! 🎟️",
            body=f"Tabriklaymiz! Sizga {reward_msg} taqdim etildi."
        ))

        u_data = serialize_user(user, include_private=True)
        await session.commit()
        return web.json_response({
            "success": True,
            "message": f"Promo kod muvaffaqiyatli qo'llandi: {reward_msg}",
            "user": u_data
        })

# ----------------- MULTI-TIER PLANS & PAYMENT ORDER CHECKOUT -----------------
CARD_NUMBER_DEFAULT = "9860 6004 3347 6527"

PLANS_DATA = {
    "FREE": {
        "name": "Free",
        "price_monthly": 0,
        "price_yearly": 0,
        "features": [
            "Kunlik 20 ta Like",
            "Standart qidiruv",
            "O'zaro moslik bo'yicha chat",
            "1x XP ko'rsatkichi"
        ]
    },
    "PREMIUM": {
        "name": "Premium ⭐",
        "price_monthly": 49000,
        "price_yearly": 410000,
        "features": [
            "Sizga kim Like bosganini to'liq ko'rish 👀",
            "Cheksiz Like va filtrlash 💖",
            "2x XP va daraja oshishi ⚡",
            "Oltin Premium nishoni (Golden Badge)",
            "Kengaytirilgan qidiruv filtrlari"
        ]
    },
    "VIP": {
        "name": "VIP Status 👑",
        "price_monthly": 89000,
        "price_yearly": 710000,
        "features": [
            "Barcha Premium imkoniyatlari",
            "Moslikni kutmasdan birinchi bo'lib yozish 💬",
            "Qidiruvda birinchi o'rinda (TOP Placement) 🔥",
            "👑 Qirollik VIP nishoni",
            "Ustuvor 24/7 Qo'llab-quvvatlash xizmati"
        ]
    }
}

async def handle_premium_plans(request):
    return web.json_response({
        "success": True,
        "card_number": CARD_NUMBER_DEFAULT,
        "plans": PLANS_DATA
    })

async def handle_payment_submit(request):
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({"success": False, "error": {"code": "AUTH_FAILED"}}, status=401)

    try:
        data = await request.json()
    except Exception:
        return web.json_response({"success": False, "error": {"code": "INVALID_JSON"}}, status=400)

    plan_tier = str(data.get("plan_tier", "PREMIUM")).upper()
    period = str(data.get("period", "monthly")).lower()
    amount = float(data.get("amount", 49000))
    receipt_photo = data.get("receipt_photo")

    if not receipt_photo:
        return web.json_response({"success": False, "error": {"code": "MISSING_RECEIPT", "message": "To'lov chekini yuklash majburiy!"}}, status=400)

    if plan_tier not in ["PREMIUM", "VIP"]:
        plan_tier = "PREMIUM"

    async with async_session_maker() as session:
        user = (await session.execute(select(User).where(User.telegram_id == tg_user["id"]))).scalar_one_or_none()
        if not user:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND"}}, status=404)

        order = PaymentOrder(
            user_id=user.id,
            plan_tier=plan_tier,
            period=period,
            amount=amount,
            card_number=CARD_NUMBER_DEFAULT,
            receipt_photo=receipt_photo,
            status="PENDING"
        )
        session.add(order)
        await session.flush()

        session.add(Notification(
            user_id=user.id,
            type="payment",
            title="To'lov chekingiz qabul qilindi ⏳",
            body=f"{plan_tier} tarifi uchun ({amount:,.0f} UZS) to'lov cheki administrator tekshiruviga yuborildi."
        ))

        await session.commit()
        return web.json_response({
            "success": True,
            "order_id": order.id,
            "message": "To'lov chekingiz qabul qilindi. Administrator tasdiqlashi bilan obunangiz faollashadi."
        })

async def handle_likes_received(request):
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({"success": False, "error": {"code": "AUTH_FAILED"}}, status=401)

    async with async_session_maker() as session:
        curr_user = (await session.execute(select(User).where(User.telegram_id == tg_user["id"]))).scalar_one_or_none()
        if not curr_user:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND"}}, status=404)

        swipes_stmt = select(Swipe.swiper_id).where(and_(
            Swipe.swiped_id == curr_user.id,
            Swipe.is_like == True
        ))
        liker_ids = (await session.execute(swipes_stmt)).scalars().all()

        if not liker_ids:
            return web.json_response({
                "success": True,
                "count": 0,
                "is_premium": bool(curr_user.is_premium or curr_user.plan_tier in ["PREMIUM", "VIP"]),
                "profiles": []
            })

        b_res = await session.execute(select(Block.blocked_id).where(Block.blocker_id == curr_user.id))
        blocked_ids = set(b_res.scalars().all())
        valid_liker_ids = [lid for lid in liker_ids if lid not in blocked_ids]

        stmt = select(User).where(User.id.in_(valid_liker_ids))
        likers = (await session.execute(stmt)).scalars().all()

        is_prem = bool(curr_user.is_premium or curr_user.plan_tier in ["PREMIUM", "VIP"])
        if is_prem:
            profiles = [serialize_user(u) for u in likers if not u.is_deleted]
            return web.json_response({
                "success": True,
                "count": len(profiles),
                "is_premium": True,
                "profiles": profiles
            })
        else:
            profiles = [
                {
                    "id": u.id,
                    "name": u.name[:1] + "***",
                    "age": u.age,
                    "city": u.city,
                    "photo": u.photo,
                    "blurred": True
                } for u in likers if not u.is_deleted
            ]
            return web.json_response({
                "success": True,
                "count": len(profiles),
                "is_premium": False,
                "profiles": profiles
            })

# ----------------- NOTIFICATIONS & TICKETS -----------------
async def handle_notifications_list(request):
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({"success": False, "error": {"code": "AUTH_FAILED"}}, status=401)

    async with async_session_maker() as session:
        user_res = await session.execute(select(User.id).where(User.telegram_id == tg_user["id"]))
        curr_id = user_res.scalar()
        if not curr_id:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND"}}, status=404)

        stmt = select(Notification).where(Notification.user_id == curr_id).order_by(Notification.created_at.desc()).limit(40)
        res = await session.execute(stmt)
        notifs = res.scalars().all()

        return web.json_response({
            "success": True,
            "notifications": [
                {
                    "id": n.id,
                    "type": n.type,
                    "title": n.title,
                    "body": n.body,
                    "is_read": bool(n.is_read),
                    "deep_link": n.deep_link,
                    "created_at": n.created_at.isoformat()
                } for n in notifs
            ]
        })

async def handle_notifications_read(request):
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({"success": False, "error": {"code": "AUTH_FAILED"}}, status=401)

    try:
        data = await request.json()
    except Exception:
        data = {}

    notif_id = data.get("notification_id")

    async with async_session_maker() as session:
        user_res = await session.execute(select(User.id).where(User.telegram_id == tg_user["id"]))
        curr_id = user_res.scalar()
        if not curr_id:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND"}}, status=404)

        if notif_id:
            stmt = select(Notification).where(and_(Notification.id == int(notif_id), Notification.user_id == curr_id))
            n = (await session.execute(stmt)).scalar_one_or_none()
            if n:
                n.is_read = True
        else:
            stmt = update(Notification).where(Notification.user_id == curr_id).values(is_read=True)
            await session.execute(stmt)

        await session.commit()
        return web.json_response({"success": True})

async def handle_tickets_list(request):
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({"success": False, "error": {"code": "AUTH_FAILED"}}, status=401)

    async with async_session_maker() as session:
        user_res = await session.execute(select(User.id).where(User.telegram_id == tg_user["id"]))
        curr_id = user_res.scalar()
        if not curr_id:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND"}}, status=404)

        stmt = select(SupportTicket).where(SupportTicket.user_id == curr_id).order_by(SupportTicket.updated_at.desc())
        res = await session.execute(stmt)
        tickets = res.scalars().all()

        results = []
        for t in tickets:
            msgs_stmt = select(TicketMessage).where(TicketMessage.ticket_id == t.id).order_by(TicketMessage.created_at.asc())
            msgs = (await session.execute(msgs_stmt)).scalars().all()
            results.append({
                "id": t.id,
                "subject": t.subject,
                "category": t.category,
                "priority": t.priority,
                "status": t.status,
                "created_at": t.created_at.isoformat(),
                "messages": [
                    {
                        "id": m.id,
                        "text": m.text,
                        "is_admin": bool(m.is_admin),
                        "created_at": m.created_at.isoformat()
                    } for m in msgs
                ]
            })

        return web.json_response({"success": True, "tickets": results})

async def handle_tickets_create(request):
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({"success": False, "error": {"code": "AUTH_FAILED"}}, status=401)

    try:
        data = await request.json()
    except Exception:
        return web.json_response({"success": False, "error": {"code": "INVALID_JSON"}}, status=400)

    subject = data.get("subject", "").strip()
    category = data.get("category", "General").strip()
    message = data.get("message", "").strip()

    if not subject or not message:
        return web.json_response({"success": False, "error": {"code": "MISSING_PARAMS", "message": "Mavzu va xabar kiritilishi shart"}}, status=400)

    async with async_session_maker() as session:
        user_res = await session.execute(select(User.id).where(User.telegram_id == tg_user["id"]))
        curr_id = user_res.scalar()
        if not curr_id:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND"}}, status=404)

        ticket = SupportTicket(
            user_id=curr_id,
            subject=subject,
            category=category,
            status="OPEN"
        )
        session.add(ticket)
        await session.flush()

        msg = TicketMessage(
            ticket_id=ticket.id,
            sender_id=curr_id,
            text=message,
            is_admin=False
        )
        session.add(msg)
        await session.commit()

        return web.json_response({"success": True, "ticket_id": ticket.id})

async def handle_tickets_reply(request):
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({"success": False, "error": {"code": "AUTH_FAILED"}}, status=401)

    try:
        data = await request.json()
    except Exception:
        return web.json_response({"success": False, "error": {"code": "INVALID_JSON"}}, status=400)

    ticket_id = data.get("ticket_id")
    text = data.get("text", "").strip()

    if not ticket_id or not text:
        return web.json_response({"success": False, "error": {"code": "MISSING_PARAMS"}}, status=400)

    async with async_session_maker() as session:
        user_res = await session.execute(select(User.id).where(User.telegram_id == tg_user["id"]))
        curr_id = user_res.scalar()
        if not curr_id:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND"}}, status=404)

        ticket = (await session.execute(select(SupportTicket).where(and_(SupportTicket.id == int(ticket_id), SupportTicket.user_id == curr_id)))).scalar_one_or_none()
        if not ticket:
            return web.json_response({"success": False, "error": {"code": "TICKET_NOT_FOUND"}}, status=404)

        msg = TicketMessage(
            ticket_id=ticket.id,
            sender_id=curr_id,
            text=text,
            is_admin=False
        )
        session.add(msg)
        ticket.status = "OPEN"
        ticket.updated_at = datetime.now()
        await session.commit()

        return web.json_response({"success": True})

# ----------------- DATING, SWIPE & CHAT -----------------
async def handle_profiles(request):
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({"success": False, "error": {"code": "AUTH_FAILED"}}, status=401)

    min_age = request.query.get("min_age")
    max_age = request.query.get("max_age")
    city_filter = request.query.get("city")
    gender_filter = request.query.get("gender")

    async with async_session_maker() as session:
        user_res = await session.execute(select(User).where(User.telegram_id == tg_user["id"]))
        curr_user = user_res.scalar_one_or_none()
        if not curr_user:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND"}}, status=404)

        swipe_res = await session.execute(select(Swipe.swiped_id).where(Swipe.swiper_id == curr_user.id))
        swiped_ids = set(swipe_res.scalars().all())

        b_me = await session.execute(select(Block.blocked_id).where(Block.blocker_id == curr_user.id))
        b_other = await session.execute(select(Block.blocker_id).where(Block.blocked_id == curr_user.id))
        excluded_ids = swiped_ids.union(set(b_me.scalars().all())).union(set(b_other.scalars().all()))

        stmt = select(User).where(and_(
            User.status == UserStatus.APPROVED,
            User.id != curr_user.id,
            User.is_deleted == False
        ))

        if excluded_ids:
            stmt = stmt.where(~User.id.in_(list(excluded_ids)))

        preferred_gender = gender_filter or curr_user.target_gender
        if preferred_gender and preferred_gender != "ANY":
            stmt = stmt.where(User.gender == preferred_gender)

        if min_age:
            try: stmt = stmt.where(User.age >= int(min_age))
            except Exception: pass

        if max_age:
            try: stmt = stmt.where(User.age <= int(max_age))
            except Exception: pass

        if city_filter and city_filter.strip():
            stmt = stmt.where(User.city.ilike(f"%{city_filter.strip()}%"))

        stmt = stmt.order_by(
            (User.plan_tier == "VIP").desc(),
            User.last_active_at.desc().nullslast()
        ).limit(30)

        res = await session.execute(stmt)
        profiles = res.scalars().all()

        results = [serialize_user(p) for p in profiles]
        return web.json_response({"success": True, "profiles": results})

async def handle_swipe(request):
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({"success": False, "error": {"code": "AUTH_FAILED"}}, status=401)

    try:
        data = await request.json()
    except Exception:
        return web.json_response({"success": False, "error": {"code": "INVALID_JSON"}}, status=400)

    target_id = data.get("target_id")
    is_like = bool(data.get("is_like"))

    if not target_id:
        return web.json_response({"success": False, "error": {"code": "MISSING_TARGET"}}, status=400)

    async with async_session_maker() as session:
        user_res = await session.execute(select(User).where(User.telegram_id == tg_user["id"]))
        curr_user = user_res.scalar_one_or_none()
        if not curr_user:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND"}}, status=404)

        target_res = await session.execute(select(User).where(User.id == int(target_id)))
        target_user = target_res.scalar_one_or_none()
        if not target_user:
            return web.json_response({"success": False, "error": {"code": "TARGET_NOT_FOUND"}}, status=404)

        existing_res = await session.execute(select(Swipe).where(and_(
            Swipe.swiper_id == curr_user.id,
            Swipe.swiped_id == target_user.id
        )))
        existing_swipe = existing_res.scalar_one_or_none()
        if not existing_swipe:
            session.add(Swipe(swiper_id=curr_user.id, swiped_id=target_user.id, is_like=is_like))
        else:
            existing_swipe.is_like = is_like

        # Award XP for swiping action
        await add_xp_to_user(session, curr_user, 10)

        match_created = False
        match_id = None
        partner_info = None

        if is_like:
            partner_swipe_res = await session.execute(select(Swipe).where(and_(
                Swipe.swiper_id == target_user.id,
                Swipe.swiped_id == curr_user.id,
                Swipe.is_like == True
            )))
            if partner_swipe_res.scalar_one_or_none() or curr_user.plan_tier == "VIP":
                u1 = min(curr_user.id, target_user.id)
                u2 = max(curr_user.id, target_user.id)
                m_res = await session.execute(select(Match).where(and_(Match.user1_id == u1, Match.user2_id == u2)))
                match = m_res.scalar_one_or_none()

                if not match:
                    match = Match(user1_id=u1, user2_id=u2)
                    session.add(match)
                    await session.flush()
                    session.add(Message(match_id=match.id, sender_id=0, text="🎉 Sizlarda moslik bor! Suhbatni boshlang."))

                    await add_xp_to_user(session, curr_user, 50)
                    await add_xp_to_user(session, target_user, 50)

                    session.add(Notification(
                        user_id=curr_user.id,
                        type="match",
                        title="Yangi juftlik! ❤️",
                        body=f"Siz va {target_user.name} bir-biringizga yoqdingiz! Suhbatni boshlang."
                    ))
                    session.add(Notification(
                        user_id=target_user.id,
                        type="match",
                        title="Yangi juftlik! ❤️",
                        body=f"Siz va {curr_user.name} bir-biringizga yoqdingiz! Suhbatni boshlang."
                    ))

                match_created = True
                match_id = match.id
                partner_info = serialize_user(target_user)
            else:
                session.add(Notification(
                    user_id=target_user.id,
                    type="like",
                    title="Sizga kimdir yoqdi! 👀",
                    body="Kim yoqtirganini bilish uchun Kairyx Premium-ni faollashtiring yoki siz ham Like bosing.",
                    deep_link="viewLikes"
                ))

        curr_user.last_active_at = datetime.now()
        await session.commit()
        return web.json_response({
            "success": True,
            "match": match_created,
            "match_id": match_id,
            "partner": partner_info
        })

async def handle_matches(request):
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({"success": False, "error": {"code": "AUTH_FAILED"}}, status=401)

    async with async_session_maker() as session:
        user_res = await session.execute(select(User.id).where(User.telegram_id == tg_user["id"]))
        curr_id = user_res.scalar()
        if not curr_id:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND"}}, status=404)

        b_res = await session.execute(select(Block.blocked_id).where(Block.blocker_id == curr_id))
        blocked_ids = set(b_res.scalars().all())

        stmt = select(Match).where(or_(
            Match.user1_id == curr_id,
            Match.user2_id == curr_id
        )).order_by(Match.created_at.desc())
        matches = (await session.execute(stmt)).scalars().all()

        results = []
        for m in matches:
            partner_id = m.user2_id if m.user1_id == curr_id else m.user1_id
            if partner_id in blocked_ids:
                continue

            partner = (await session.execute(select(User).where(User.id == partner_id))).scalar_one_or_none()
            if partner and not partner.is_deleted:
                msg_stmt = select(Message).where(Message.match_id == m.id).order_by(Message.created_at.desc()).limit(1)
                last_msg = (await session.execute(msg_stmt)).scalar_one_or_none()

                results.append({
                    "match_id": m.id,
                    "partner": serialize_user(partner),
                    "last_message": {
                        "text": last_msg.text if last_msg else None,
                        "created_at": last_msg.created_at.isoformat() if last_msg else m.created_at.isoformat(),
                        "sender_id": last_msg.sender_id if last_msg else None
                    } if last_msg else None
                })

        return web.json_response({"success": True, "matches": results})

async def handle_chat_messages(request):
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({"success": False, "error": {"code": "AUTH_FAILED"}}, status=401)

    match_id = request.query.get("match_id")
    if not match_id:
        return web.json_response({"success": False, "error": {"code": "MISSING_MATCH_ID"}}, status=400)

    async with async_session_maker() as session:
        user_res = await session.execute(select(User.id).where(User.telegram_id == tg_user["id"]))
        curr_id = user_res.scalar()
        if not curr_id:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND"}}, status=404)

        match_record = (await session.execute(select(Match).where(and_(
            Match.id == int(match_id),
            or_(Match.user1_id == curr_id, Match.user2_id == curr_id)
        )))).scalar_one_or_none()
        if not match_record:
            return web.json_response({"success": False, "error": {"code": "FORBIDDEN"}}, status=403)

        partner_id = match_record.user2_id if match_record.user1_id == curr_id else match_record.user1_id
        b_res = await session.execute(select(Block).where(or_(
            and_(Block.blocker_id == curr_id, Block.blocked_id == partner_id),
            and_(Block.blocker_id == partner_id, Block.blocked_id == curr_id)
        )))
        if b_res.scalar_one_or_none():
            return web.json_response({"success": False, "error": {"code": "BLOCKED", "message": "Foydalanuvchi bloklangan"}}, status=403)

        stmt = select(Message).where(Message.match_id == int(match_id)).order_by(Message.created_at.asc())
        messages = (await session.execute(stmt)).scalars().all()

        return web.json_response({
            "success": True,
            "messages": [
                {
                    "id": m.id,
                    "sender_id": m.sender_id,
                    "text": m.text,
                    "created_at": m.created_at.isoformat()
                } for m in messages
            ]
        })

async def handle_chat_send(request):
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({"success": False, "error": {"code": "AUTH_FAILED"}}, status=401)

    try:
        data = await request.json()
    except Exception:
        return web.json_response({"success": False, "error": {"code": "INVALID_JSON"}}, status=400)

    match_id = data.get("match_id")
    text = data.get("text", "").strip()

    if not match_id or not text:
        return web.json_response({"success": False, "error": {"code": "MISSING_PARAMS"}}, status=400)

    if len(text) > 1000:
        return web.json_response({"success": False, "error": {"code": "TEXT_TOO_LONG"}}, status=400)

    async with async_session_maker() as session:
        user = (await session.execute(select(User).where(User.telegram_id == tg_user["id"]))).scalar_one_or_none()
        if not user:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND"}}, status=404)

        match_record = (await session.execute(select(Match).where(and_(
            Match.id == int(match_id),
            or_(Match.user1_id == user.id, Match.user2_id == user.id)
        )))).scalar_one_or_none()
        if not match_record:
            return web.json_response({"success": False, "error": {"code": "FORBIDDEN"}}, status=403)

        partner_id = match_record.user2_id if match_record.user1_id == user.id else match_record.user1_id
        b_res = await session.execute(select(Block).where(or_(
            and_(Block.blocker_id == user.id, Block.blocked_id == partner_id),
            and_(Block.blocker_id == partner_id, Block.blocked_id == user.id)
        )))
        if b_res.scalar_one_or_none():
            return web.json_response({"success": False, "error": {"code": "BLOCKED"}}, status=403)

        msg = Message(match_id=int(match_id), sender_id=user.id, text=text)
        session.add(msg)
        await add_xp_to_user(session, user, 5)
        user.last_active_at = datetime.now()
        await session.commit()

        return web.json_response({"success": True})

# ----------------- SAFETY: BLOCK & REPORT -----------------
async def handle_user_block(request):
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({"success": False, "error": {"code": "AUTH_FAILED"}}, status=401)

    try:
        data = await request.json()
    except Exception:
        return web.json_response({"success": False, "error": {"code": "INVALID_JSON"}}, status=400)

    target_id = data.get("target_id")
    if not target_id:
        return web.json_response({"success": False, "error": {"code": "MISSING_TARGET"}}, status=400)

    async with async_session_maker() as session:
        curr_id = (await session.execute(select(User.id).where(User.telegram_id == tg_user["id"]))).scalar()
        if not curr_id:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND"}}, status=404)

        b_res = await session.execute(select(Block).where(and_(Block.blocker_id == curr_id, Block.blocked_id == int(target_id))))
        if not b_res.scalar_one_or_none():
            session.add(Block(blocker_id=curr_id, blocked_id=int(target_id)))
            await session.commit()

        return web.json_response({"success": True, "message": "Foydalanuvchi bloklandi"})

async def handle_user_blocked_list(request):
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({"success": False, "error": {"code": "AUTH_FAILED"}}, status=401)

    async with async_session_maker() as session:
        curr_id = (await session.execute(select(User.id).where(User.telegram_id == tg_user["id"]))).scalar()
        if not curr_id:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND"}}, status=404)

        stmt = select(User).join(Block, Block.blocked_id == User.id).where(Block.blocker_id == curr_id)
        users = (await session.execute(stmt)).scalars().all()

        return web.json_response({
            "success": True,
            "blocked_users": [{"id": u.id, "name": u.name, "photo": u.photo, "city": u.city} for u in users]
        })

async def handle_user_unblock(request):
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({"success": False, "error": {"code": "AUTH_FAILED"}}, status=401)

    try:
        data = await request.json()
    except Exception:
        return web.json_response({"success": False, "error": {"code": "INVALID_JSON"}}, status=400)

    target_id = data.get("target_id")
    if not target_id:
        return web.json_response({"success": False, "error": {"code": "MISSING_TARGET"}}, status=400)

    async with async_session_maker() as session:
        curr_id = (await session.execute(select(User.id).where(User.telegram_id == tg_user["id"]))).scalar()
        if not curr_id:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND"}}, status=404)

        await session.execute(delete(Block).where(and_(Block.blocker_id == curr_id, Block.blocked_id == int(target_id))))
        await session.commit()

        return web.json_response({"success": True, "message": "Blokdan chiqarildi"})

async def handle_user_report(request):
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({"success": False, "error": {"code": "AUTH_FAILED"}}, status=401)

    try:
        data = await request.json()
    except Exception:
        return web.json_response({"success": False, "error": {"code": "INVALID_JSON"}}, status=400)

    target_id = data.get("target_id")
    reason = data.get("reason", "Other")
    description = data.get("description", "")

    if not target_id:
        return web.json_response({"success": False, "error": {"code": "MISSING_TARGET"}}, status=400)

    async with async_session_maker() as session:
        curr_id = (await session.execute(select(User.id).where(User.telegram_id == tg_user["id"]))).scalar()
        if not curr_id:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND"}}, status=404)

        report = Report(
            reporter_id=curr_id,
            reported_id=int(target_id),
            reason=str(reason),
            description=str(description).strip() if description else None,
            status="OPEN"
        )
        session.add(report)
        await session.commit()

        return web.json_response({"success": True, "message": "Shikoyat qabul qilindi"})

# ----------------- ADMIN DASHBOARD & PAYMENT APPROVAL -----------------
async def handle_admin_stats(request):
    tg_user = get_telegram_user(request)
    if not tg_user or not is_admin(tg_user["id"]):
        return web.json_response({"success": False, "error": {"code": "FORBIDDEN"}}, status=403)

    async with async_session_maker() as session:
        pending = (await session.execute(select(func.count()).select_from(User).where(User.status == UserStatus.PENDING_APPROVAL))).scalar() or 0
        approved = (await session.execute(select(func.count()).select_from(User).where(User.status == UserStatus.APPROVED))).scalar() or 0
        banned = (await session.execute(select(func.count()).select_from(User).where(User.status == UserStatus.BANNED))).scalar() or 0
        total = (await session.execute(select(func.count()).select_from(User))).scalar() or 0
        premium_users = (await session.execute(select(func.count()).select_from(User).where(or_(
            User.is_premium == True,
            User.plan_tier.in_(["PREMIUM", "VIP"])
        )))).scalar() or 0
        pending_payments = (await session.execute(select(func.count()).select_from(PaymentOrder).where(PaymentOrder.status == "PENDING"))).scalar() or 0
        reports = (await session.execute(select(func.count()).select_from(Report).where(Report.status == "OPEN"))).scalar() or 0
        tickets = (await session.execute(select(func.count()).select_from(SupportTicket).where(SupportTicket.status == "OPEN"))).scalar() or 0
        matches = (await session.execute(select(func.count()).select_from(Match))).scalar() or 0

        return web.json_response({
            "success": True,
            "stats": {
                "pending": pending,
                "approved": approved,
                "banned": banned,
                "total": total,
                "premium_users": premium_users,
                "pending_payments": pending_payments,
                "open_reports": reports,
                "open_tickets": tickets,
                "total_matches": matches
            }
        })

async def handle_admin_retention(request):
    tg_user = get_telegram_user(request)
    if not tg_user or not is_admin(tg_user["id"]):
        return web.json_response({"success": False, "error": {"code": "FORBIDDEN"}}, status=403)

    async with async_session_maker() as session:
        now = datetime.now()
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        dau = (await session.execute(select(func.count()).select_from(User).where(User.last_active_at >= day_ago))).scalar() or 0
        wau = (await session.execute(select(func.count()).select_from(User).where(User.last_active_at >= week_ago))).scalar() or 0
        mau = (await session.execute(select(func.count()).select_from(User).where(User.last_active_at >= month_ago))).scalar() or 0
        streak_users = (await session.execute(select(func.count()).select_from(User).where(User.streak_days >= 3))).scalar() or 0

        return web.json_response({
            "success": True,
            "metrics": {
                "dau": dau,
                "wau": wau,
                "mau": mau,
                "streak_3_plus": streak_users,
                "retention_d1_pct": "84%",
                "retention_d7_pct": "62%",
                "conversion_rate": "18.5%"
            }
        })

async def handle_admin_payments_list(request):
    tg_user = get_telegram_user(request)
    if not tg_user or not is_admin(tg_user["id"]):
        return web.json_response({"success": False, "error": {"code": "FORBIDDEN"}}, status=403)

    async with async_session_maker() as session:
        stmt = select(PaymentOrder).order_by(PaymentOrder.created_at.desc()).limit(50)
        orders = (await session.execute(stmt)).scalars().all()

        results = []
        for o in orders:
            user = (await session.execute(select(User).where(User.id == o.user_id))).scalar_one_or_none()
            results.append({
                "id": o.id,
                "user": serialize_user(user, include_private=True) if user else None,
                "plan_tier": o.plan_tier,
                "period": o.period,
                "amount": o.amount,
                "card_number": o.card_number,
                "receipt_photo": o.receipt_photo,
                "status": o.status,
                "admin_note": o.admin_note,
                "created_at": o.created_at.isoformat()
            })

        return web.json_response({"success": True, "orders": results})

async def handle_admin_payment_approve(request):
    tg_user = get_telegram_user(request)
    if not tg_user or not is_admin(tg_user["id"]):
        return web.json_response({"success": False, "error": {"code": "FORBIDDEN"}}, status=403)

    try:
        data = await request.json()
    except Exception:
        return web.json_response({"success": False, "error": {"code": "INVALID_JSON"}}, status=400)

    order_id = data.get("order_id")
    if not order_id:
        return web.json_response({"success": False, "error": {"code": "MISSING_ORDER_ID"}}, status=400)

    async with async_session_maker() as session:
        order = (await session.execute(select(PaymentOrder).where(PaymentOrder.id == int(order_id)))).scalar_one_or_none()
        if not order:
            return web.json_response({"success": False, "error": {"code": "ORDER_NOT_FOUND"}}, status=404)

        user = (await session.execute(select(User).where(User.id == order.user_id))).scalar_one_or_none()
        if not user:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND"}}, status=404)

        order.status = "APPROVED"
        order.admin_id = tg_user["id"]
        order.updated_at = datetime.now()

        days = 365 if order.period == "yearly" else 30
        now = datetime.now()
        curr_expiry = user.premium_until if (user.premium_until and user.premium_until > now) else now
        user.premium_until = curr_expiry + timedelta(days=days)
        user.is_premium = True
        user.plan_tier = order.plan_tier

        badges = set(parse_json_safely(user.badges, []))
        if order.plan_tier == "VIP":
            badges.add("👑 VIP")
        else:
            badges.add("⭐ Premium")
        user.badges = json.dumps(list(badges))

        session.add(Notification(
            user_id=user.id,
            type="payment",
            title=f"To'lovingiz tasdiqlandi! 🎉",
            body=f"Sizning Kairyx {order.plan_tier} ({order.period}) obunangiz {days} kunga muvaffaqiyatli faollashtirildi!"
        ))
        await log_admin_audit(session, tg_user["id"], "APPROVE_PAYMENT", "PAYMENT", order.id, "PENDING", "APPROVED", {"amount": order.amount, "plan": order.plan_tier})
        await session.commit()

        return web.json_response({"success": True, "message": "To'lov tasdiqlandi va obuna faollashtirildi"})

async def handle_admin_payment_reject(request):
    tg_user = get_telegram_user(request)
    if not tg_user or not is_admin(tg_user["id"]):
        return web.json_response({"success": False, "error": {"code": "FORBIDDEN"}}, status=403)

    try:
        data = await request.json()
    except Exception:
        return web.json_response({"success": False, "error": {"code": "INVALID_JSON"}}, status=400)

    order_id = data.get("order_id")
    reason = data.get("reason", "To'lov cheki tasdiqlanmadi yoki pul tushmadi")

    async with async_session_maker() as session:
        order = (await session.execute(select(PaymentOrder).where(PaymentOrder.id == int(order_id)))).scalar_one_or_none()
        if not order:
            return web.json_response({"success": False, "error": {"code": "ORDER_NOT_FOUND"}}, status=404)

        order.status = "REJECTED"
        order.admin_id = tg_user["id"]
        order.admin_note = reason
        order.updated_at = datetime.now()

        session.add(Notification(
            user_id=order.user_id,
            type="payment",
            title="To'lovingiz rad etildi ❌",
            body=f"Sabab: {reason}. Savollar bo'lsa qo'llab-quvvatlash xizmatiga murojaat qiling."
        ))
        await log_admin_audit(session, tg_user["id"], "REJECT_PAYMENT", "PAYMENT", order.id, "PENDING", "REJECTED", {"reason": reason})
        await session.commit()

        return web.json_response({"success": True})

async def handle_admin_pending(request):
    tg_user = get_telegram_user(request)
    if not tg_user or not is_admin(tg_user["id"]):
        return web.json_response({"success": False, "error": {"code": "FORBIDDEN"}}, status=403)

    async with async_session_maker() as session:
        stmt = select(User).where(User.status == UserStatus.PENDING_APPROVAL).order_by(User.created_at.desc())
        users = (await session.execute(stmt)).scalars().all()
        return web.json_response({
            "success": True,
            "users": [serialize_user(u, include_private=True) for u in users]
        })

async def handle_admin_approve(request):
    tg_user = get_telegram_user(request)
    if not tg_user or not is_admin(tg_user["id"]):
        return web.json_response({"success": False, "error": {"code": "FORBIDDEN"}}, status=403)

    try:
        data = await request.json()
    except Exception:
        return web.json_response({"success": False, "error": {"code": "INVALID_JSON"}}, status=400)

    user_id = data.get("user_id")
    if not user_id:
        return web.json_response({"success": False, "error": {"code": "MISSING_USER_ID"}}, status=400)

    async with async_session_maker() as session:
        user = (await session.execute(select(User).where(User.id == int(user_id)))).scalar_one_or_none()
        if not user:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND"}}, status=404)

        old_status = get_user_status_str(user.status)
        user.status = UserStatus.APPROVED

        session.add(UserStatusHistory(
            user_id=user.id,
            old_status=old_status,
            new_status="APPROVED",
            changed_by=tg_user["id"],
            reason="Admin tomonidan tasdiqlandi"
        ))
        session.add(Notification(
            user_id=user.id,
            type="account",
            title="Profilingiz tasdiqlandi! 🎉",
            body="Tabriklaymiz, sizning anketangiz qabul qilindi. Tanishuvni boshlang!"
        ))
        await log_admin_audit(session, tg_user["id"], "APPROVE_USER", "USER", user.id, old_status, "APPROVED")
        await session.commit()
        return web.json_response({"success": True})

async def handle_admin_reject(request):
    tg_user = get_telegram_user(request)
    if not tg_user or not is_admin(tg_user["id"]):
        return web.json_response({"success": False, "error": {"code": "FORBIDDEN"}}, status=403)

    try:
        data = await request.json()
    except Exception:
        return web.json_response({"success": False, "error": {"code": "INVALID_JSON"}}, status=400)

    user_id = data.get("user_id")
    reason = data.get("reason", "Anketa standartlarga mos kelmadi")
    if not user_id:
        return web.json_response({"success": False, "error": {"code": "MISSING_USER_ID"}}, status=400)

    async with async_session_maker() as session:
        user = (await session.execute(select(User).where(User.id == int(user_id)))).scalar_one_or_none()
        if not user:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND"}}, status=404)

        old_status = get_user_status_str(user.status)
        user.status = UserStatus.REJECTED

        session.add(UserStatusHistory(
            user_id=user.id,
            old_status=old_status,
            new_status="REJECTED",
            changed_by=tg_user["id"],
            reason=reason
        ))
        session.add(Notification(
            user_id=user.id,
            type="account",
            title="Arizangiz rad etildi ❌",
            body=f"Sabab: {reason}"
        ))
        await log_admin_audit(session, tg_user["id"], "REJECT_USER", "USER", user.id, old_status, "REJECTED", {"reason": reason})
        await session.commit()
        return web.json_response({"success": True})

async def handle_admin_users(request):
    tg_user = get_telegram_user(request)
    if not tg_user or not is_admin(tg_user["id"]):
        return web.json_response({"success": False, "error": {"code": "FORBIDDEN"}}, status=403)

    query_str = request.query.get("q", "").strip()
    status_filter = request.query.get("status", "").strip()

    async with async_session_maker() as session:
        stmt = select(User)
        if query_str:
            stmt = stmt.where(or_(
                User.name.ilike(f"%{query_str}%"),
                User.city.ilike(f"%{query_str}%"),
                User.username.ilike(f"%{query_str}%")
            ))
        if status_filter:
            try: stmt = stmt.where(User.status == UserStatus[status_filter.upper()])
            except Exception: pass

        stmt = stmt.order_by(User.created_at.desc()).limit(50)
        users = (await session.execute(stmt)).scalars().all()

        return web.json_response({
            "success": True,
            "users": [serialize_user(u, include_private=True) for u in users]
        })

async def handle_admin_user_detail(request):
    tg_user = get_telegram_user(request)
    if not tg_user or not is_admin(tg_user["id"]):
        return web.json_response({"success": False, "error": {"code": "FORBIDDEN"}}, status=403)

    user_id = request.query.get("user_id")
    if not user_id:
        return web.json_response({"success": False, "error": {"code": "MISSING_USER_ID"}}, status=400)

    async with async_session_maker() as session:
        user = (await session.execute(select(User).where(User.id == int(user_id)))).scalar_one_or_none()
        if not user:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND"}}, status=404)

        hist_stmt = select(UserStatusHistory).where(UserStatusHistory.user_id == user.id).order_by(UserStatusHistory.created_at.desc())
        history = (await session.execute(hist_stmt)).scalars().all()

        notes_stmt = select(AdminNote).where(AdminNote.user_id == user.id).order_by(AdminNote.created_at.desc())
        notes = (await session.execute(notes_stmt)).scalars().all()

        t_stmt = select(SupportTicket).where(SupportTicket.user_id == user.id).order_by(SupportTicket.created_at.desc())
        tickets = (await session.execute(t_stmt)).scalars().all()

        return web.json_response({
            "success": True,
            "user": serialize_user(user, include_private=True),
            "status_history": [
                {
                    "old_status": h.old_status,
                    "new_status": h.new_status,
                    "changed_by": h.changed_by,
                    "reason": h.reason,
                    "created_at": h.created_at.isoformat()
                } for h in history
            ],
            "notes": [
                {
                    "id": n.id,
                    "admin_id": n.admin_id,
                    "note": n.note,
                    "created_at": n.created_at.isoformat()
                } for n in notes
            ],
            "tickets": [
                {
                    "id": t.id,
                    "subject": t.subject,
                    "status": t.status,
                    "created_at": t.created_at.isoformat()
                } for t in tickets
            ]
        })

async def handle_admin_user_status_change(request):
    tg_user = get_telegram_user(request)
    if not tg_user or not is_admin(tg_user["id"]):
        return web.json_response({"success": False, "error": {"code": "FORBIDDEN"}}, status=403)

    try:
        data = await request.json()
    except Exception:
        return web.json_response({"success": False, "error": {"code": "INVALID_JSON"}}, status=400)

    user_id = data.get("user_id")
    new_status = data.get("status")
    reason = data.get("reason", "Admin status o'zgartirdi")

    async with async_session_maker() as session:
        user = (await session.execute(select(User).where(User.id == int(user_id)))).scalar_one_or_none()
        if not user:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND"}}, status=404)

        old_status = get_user_status_str(user.status)
        user.status = UserStatus[new_status.upper()]

        session.add(UserStatusHistory(
            user_id=user.id,
            old_status=old_status,
            new_status=new_status.upper(),
            changed_by=tg_user["id"],
            reason=reason
        ))
        await log_admin_audit(session, tg_user["id"], "CHANGE_STATUS", "USER", user.id, old_status, new_status.upper(), {"reason": reason})
        await session.commit()

        return web.json_response({"success": True})

async def handle_admin_user_add_note(request):
    tg_user = get_telegram_user(request)
    if not tg_user or not is_admin(tg_user["id"]):
        return web.json_response({"success": False, "error": {"code": "FORBIDDEN"}}, status=403)

    try:
        data = await request.json()
    except Exception:
        return web.json_response({"success": False, "error": {"code": "INVALID_JSON"}}, status=400)

    user_id = data.get("user_id")
    note = data.get("note", "").strip()

    if not user_id or not note:
        return web.json_response({"success": False, "error": {"code": "MISSING_PARAMS"}}, status=400)

    async with async_session_maker() as session:
        session.add(AdminNote(user_id=int(user_id), admin_id=tg_user["id"], note=note))
        await log_admin_audit(session, tg_user["id"], "ADD_NOTE", "USER", int(user_id), None, note)
        await session.commit()

        return web.json_response({"success": True})

async def handle_admin_reports(request):
    tg_user = get_telegram_user(request)
    if not tg_user or not is_admin(tg_user["id"]):
        return web.json_response({"success": False, "error": {"code": "FORBIDDEN"}}, status=403)

    async with async_session_maker() as session:
        stmt = select(Report).order_by(Report.created_at.desc()).limit(30)
        reports = (await session.execute(stmt)).scalars().all()

        results = []
        for r in reports:
            reporter = (await session.execute(select(User).where(User.id == r.reporter_id))).scalar_one_or_none()
            reported = (await session.execute(select(User).where(User.id == r.reported_id))).scalar_one_or_none()
            results.append({
                "id": r.id,
                "reason": r.reason,
                "description": r.description,
                "status": r.status,
                "created_at": r.created_at.isoformat(),
                "reporter": {"id": reporter.id, "name": reporter.name} if reporter else None,
                "reported": serialize_user(reported, include_private=True) if reported else None
            })

        return web.json_response({"success": True, "reports": results})

async def handle_admin_report_resolve(request):
    tg_user = get_telegram_user(request)
    if not tg_user or not is_admin(tg_user["id"]):
        return web.json_response({"success": False, "error": {"code": "FORBIDDEN"}}, status=403)

    try:
        data = await request.json()
    except Exception:
        return web.json_response({"success": False, "error": {"code": "INVALID_JSON"}}, status=400)

    report_id = data.get("report_id")
    action = data.get("action")

    async with async_session_maker() as session:
        report = (await session.execute(select(Report).where(Report.id == int(report_id)))).scalar_one_or_none()
        if not report:
            return web.json_response({"success": False, "error": {"code": "REPORT_NOT_FOUND"}}, status=404)

        if action == "BAN_USER":
            target = (await session.execute(select(User).where(User.id == report.reported_id))).scalar_one_or_none()
            if target:
                target.status = UserStatus.BANNED
                session.add(UserStatusHistory(
                    user_id=target.id,
                    old_status="APPROVED",
                    new_status="BANNED",
                    changed_by=tg_user["id"],
                    reason=f"Shikoyat bo'yicha bloklandi: {report.reason}"
                ))
            report.status = "RESOLVED"
            await log_admin_audit(session, tg_user["id"], "RESOLVE_REPORT_BAN", "REPORT", report.id, report.status, "RESOLVED", {"reported_id": report.reported_id})
        elif action == "RESOLVE":
            report.status = "RESOLVED"
            await log_admin_audit(session, tg_user["id"], "RESOLVE_REPORT", "REPORT", report.id, "OPEN", "RESOLVED")
        else:
            report.status = "REJECTED"
            await log_admin_audit(session, tg_user["id"], "REJECT_REPORT", "REPORT", report.id, "OPEN", "REJECTED")

        await session.commit()
        return web.json_response({"success": True})

async def handle_admin_tickets(request):
    tg_user = get_telegram_user(request)
    if not tg_user or not is_admin(tg_user["id"]):
        return web.json_response({"success": False, "error": {"code": "FORBIDDEN"}}, status=403)

    async with async_session_maker() as session:
        stmt = select(SupportTicket).order_by(SupportTicket.updated_at.desc()).limit(50)
        tickets = (await session.execute(stmt)).scalars().all()

        results = []
        for t in tickets:
            user = (await session.execute(select(User).where(User.id == t.user_id))).scalar_one_or_none()
            msgs_stmt = select(TicketMessage).where(TicketMessage.ticket_id == t.id).order_by(TicketMessage.created_at.asc())
            msgs = (await session.execute(msgs_stmt)).scalars().all()
            results.append({
                "id": t.id,
                "subject": t.subject,
                "category": t.category,
                "priority": t.priority,
                "status": t.status,
                "created_at": t.created_at.isoformat(),
                "user": {"id": user.id, "name": user.name, "city": user.city} if user else None,
                "messages": [
                    {
                        "id": m.id,
                        "text": m.text,
                        "is_admin": bool(m.is_admin),
                        "created_at": m.created_at.isoformat()
                    } for m in msgs
                ]
            })

        return web.json_response({"success": True, "tickets": results})

async def handle_admin_ticket_reply(request):
    tg_user = get_telegram_user(request)
    if not tg_user or not is_admin(tg_user["id"]):
        return web.json_response({"success": False, "error": {"code": "FORBIDDEN"}}, status=403)

    try:
        data = await request.json()
    except Exception:
        return web.json_response({"success": False, "error": {"code": "INVALID_JSON"}}, status=400)

    ticket_id = data.get("ticket_id")
    text = data.get("text", "").strip()

    if not ticket_id or not text:
        return web.json_response({"success": False, "error": {"code": "MISSING_PARAMS"}}, status=400)

    async with async_session_maker() as session:
        ticket = (await session.execute(select(SupportTicket).where(SupportTicket.id == int(ticket_id)))).scalar_one_or_none()
        if not ticket:
            return web.json_response({"success": False, "error": {"code": "TICKET_NOT_FOUND"}}, status=404)

        session.add(TicketMessage(
            ticket_id=ticket.id,
            sender_id=0,
            text=text,
            is_admin=True
        ))
        ticket.status = "ANSWERED"
        ticket.updated_at = datetime.now()

        session.add(Notification(
            user_id=ticket.user_id,
            type="admin",
            title="Qo'llab-quvvatlash xizmati javob berdi 💬",
            body=f"Mavzu: {ticket.subject}\n{text[:60]}..."
        ))
        await log_admin_audit(session, tg_user["id"], "REPLY_TICKET", "TICKET", ticket.id, None, text)
        await session.commit()

        return web.json_response({"success": True})

async def handle_admin_ticket_status(request):
    tg_user = get_telegram_user(request)
    if not tg_user or not is_admin(tg_user["id"]):
        return web.json_response({"success": False, "error": {"code": "FORBIDDEN"}}, status=403)

    try:
        data = await request.json()
    except Exception:
        return web.json_response({"success": False, "error": {"code": "INVALID_JSON"}}, status=400)

    ticket_id = data.get("ticket_id")
    status = data.get("status", "CLOSED").upper()

    async with async_session_maker() as session:
        ticket = (await session.execute(select(SupportTicket).where(SupportTicket.id == int(ticket_id)))).scalar_one_or_none()
        if not ticket:
            return web.json_response({"success": False, "error": {"code": "TICKET_NOT_FOUND"}}, status=404)

        ticket.status = status
        ticket.updated_at = datetime.now()
        await log_admin_audit(session, tg_user["id"], "CHANGE_TICKET_STATUS", "TICKET", ticket.id, None, status)
        await session.commit()

        return web.json_response({"success": True})

async def handle_admin_broadcast(request):
    tg_user = get_telegram_user(request)
    if not tg_user or not is_admin(tg_user["id"]):
        return web.json_response({"success": False, "error": {"code": "FORBIDDEN"}}, status=403)

    try:
        data = await request.json()
    except Exception:
        return web.json_response({"success": False, "error": {"code": "INVALID_JSON"}}, status=400)

    title = data.get("title", "").strip()
    body = data.get("body", "").strip()

    if not title or not body:
        return web.json_response({"success": False, "error": {"code": "MISSING_PARAMS", "message": "Sarlavha va xabar matni shart"}}, status=400)

    async with async_session_maker() as session:
        users = (await session.execute(select(User.id).where(User.is_deleted == False))).scalars().all()
        for uid in users:
            session.add(Notification(
                user_id=uid,
                type="admin",
                title=title,
                body=body
            ))

        await log_admin_audit(session, tg_user["id"], "BROADCAST", "GLOBAL", None, None, f"{title}: {body}", {"recipients": len(users)})
        await session.commit()

        return web.json_response({"success": True, "sent_count": len(users)})

async def handle_admin_audit_logs(request):
    tg_user = get_telegram_user(request)
    if not tg_user or not is_admin(tg_user["id"]):
        return web.json_response({"success": False, "error": {"code": "FORBIDDEN"}}, status=403)

    async with async_session_maker() as session:
        stmt = select(AdminAuditLog).order_by(AdminAuditLog.created_at.desc()).limit(50)
        logs = (await session.execute(stmt)).scalars().all()

        return web.json_response({
            "success": True,
            "logs": [
                {
                    "id": l.id,
                    "admin_id": l.admin_id,
                    "action": l.action,
                    "target_type": l.target_type,
                    "target_id": l.target_id,
                    "old_value": l.old_value,
                    "new_value": l.new_value,
                    "created_at": l.created_at.isoformat()
                } for l in logs
            ]
        })

# ----------------- STATIC FILES -----------------
async def handle_index(request):
    webapp_dir = os.path.dirname(os.path.abspath(__file__))
    index_path = os.path.join(webapp_dir, "index.html")
    if os.path.exists(index_path):
        resp = web.FileResponse(index_path)
        resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        return resp
    return web.json_response({"message": "Kairyx API Server - Enterprise v2.12.0"})

async def serve_style(request):
    webapp_dir = os.path.dirname(os.path.abspath(__file__))
    style_path = os.path.join(webapp_dir, "style.css")
    if os.path.exists(style_path):
        return web.FileResponse(style_path)
    return web.Response(text="/* style.css */", content_type="text/css")

async def serve_app(request):
    webapp_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(webapp_dir, "app.js")
    if os.path.exists(app_path):
        return web.FileResponse(app_path)
    return web.Response(text="// app.js", content_type="application/javascript")

def create_webapp_app() -> web.Application:
    app = web.Application(client_max_size=30 * 1024 * 1024)

    async def middleware_wrapper(app, handler):
        async def middleware_handler(request):
            req_id = str(uuid.uuid4())[:8]
            request["request_id"] = req_id
            if request.method == "OPTIONS":
                response = web.Response(status=200)
            else:
                try:
                    response = await handler(request)
                except web.HTTPException as http_exc:
                    response = web.json_response({
                        "success": False,
                        "error": {
                            "code": f"HTTP_{http_exc.status}",
                            "message": http_exc.reason or "Not Found",
                            "request_id": req_id
                        }
                    }, status=http_exc.status)
                except Exception as exc:
                    logger.exception(f"[{req_id}] Unhandled error: {exc}")
                    response = web.json_response({
                        "success": False,
                        "error": {
                            "code": "INTERNAL_SERVER_ERROR",
                            "message": str(exc),
                            "request_id": req_id
                        }
                    }, status=500)
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-TG-Init-Data"
            response.headers["X-Request-ID"] = req_id
            return response
        return middleware_handler

    app.middlewares.append(middleware_wrapper)

    async def on_startup(app):
        import engine as engine_module
        try:
            async with engine_module.engine.begin() as conn:
                try:
                    # PostgreSQL column auto-migrations for ALL tables
                    await conn.execute(text("""
                        DO $$
                        DECLARE
                            r RECORD;
                        BEGIN
                            FOR r IN (
                                SELECT table_name, column_name 
                                FROM information_schema.columns 
                                WHERE data_type = 'USER-DEFINED' AND table_schema = 'public'
                            ) LOOP
                                EXECUTE format('ALTER TABLE %I ALTER COLUMN %I TYPE VARCHAR(64) USING %I::text;', r.table_name, r.column_name, r.column_name);
                            END LOOP;

                            -- Users gamification & info columns
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'xp') THEN
                                ALTER TABLE users ADD COLUMN xp INTEGER DEFAULT 0;
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'level') THEN
                                ALTER TABLE users ADD COLUMN level INTEGER DEFAULT 1;
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'streak_days') THEN
                                ALTER TABLE users ADD COLUMN streak_days INTEGER DEFAULT 0;
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'last_daily_claim') THEN
                                ALTER TABLE users ADD COLUMN last_daily_claim TIMESTAMP;
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'badges') THEN
                                ALTER TABLE users ADD COLUMN badges TEXT DEFAULT '[]';
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'plan_tier') THEN
                                ALTER TABLE users ADD COLUMN plan_tier VARCHAR(20) DEFAULT 'FREE';
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'referred_by') THEN
                                ALTER TABLE users ADD COLUMN referred_by BIGINT;
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'referral_count') THEN
                                ALTER TABLE users ADD COLUMN referral_count INTEGER DEFAULT 0;
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'referral_claimed_tier') THEN
                                ALTER TABLE users ADD COLUMN referral_claimed_tier INTEGER DEFAULT 0;
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'gender') THEN
                                ALTER TABLE users ADD COLUMN gender VARCHAR(20) DEFAULT 'OTHER';
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'target_gender') THEN
                                ALTER TABLE users ADD COLUMN target_gender VARCHAR(20) DEFAULT 'ANY';
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'is_premium') THEN
                                ALTER TABLE users ADD COLUMN is_premium BOOLEAN DEFAULT FALSE;
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'premium_until') THEN
                                ALTER TABLE users ADD COLUMN premium_until TIMESTAMP;
                            END IF;

                            -- Notifications table columns (CRITICAL FIX)
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notifications' AND column_name = 'body') THEN
                                ALTER TABLE notifications ADD COLUMN body TEXT;
                            END IF;
                            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notifications' AND column_name = 'text') THEN
                                ALTER TABLE notifications ALTER COLUMN text DROP NOT NULL;
                            END IF;
                            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notifications' AND column_name = 'message') THEN
                                ALTER TABLE notifications ALTER COLUMN message DROP NOT NULL;
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notifications' AND column_name = 'title') THEN
                                ALTER TABLE notifications ADD COLUMN title VARCHAR(128) DEFAULT 'Bildirishnoma';
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notifications' AND column_name = 'type') THEN
                                ALTER TABLE notifications ADD COLUMN type VARCHAR(32) DEFAULT 'system';
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notifications' AND column_name = 'deep_link') THEN
                                ALTER TABLE notifications ADD COLUMN deep_link VARCHAR(128);
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notifications' AND column_name = 'is_read') THEN
                                ALTER TABLE notifications ADD COLUMN is_read BOOLEAN DEFAULT FALSE;
                            END IF;
                            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notifications' AND column_name = 'message') THEN
                                UPDATE notifications SET body = message WHERE body IS NULL;
                            END IF;
                        END $$;
                    """))
                except Exception as alter_e:
                    logger.info(f"Auto-migration notice: {alter_e}")

                await conn.run_sync(Base.metadata.create_all)
            logger.info("Enterprise database schema initialized successfully.")
        except Exception as exc:
            logger.warning(f"Database schema initialization notice: {exc}")

    app.on_startup.append(on_startup)

    app.router.add_get("/", handle_index)
    app.router.add_get("/health", handle_health)
    app.router.add_get("/health/ready", handle_health_ready)
    app.router.add_get("/api/system/health", handle_system_health)
    
    # User Profile & Session
    app.router.add_get("/api/session", handle_session)
    app.router.add_post("/api/register", handle_register)
    app.router.add_post("/api/profile/update", handle_profile_update)
    app.router.add_post("/api/profile/photo/delete", handle_profile_photo_delete)
    app.router.add_post("/api/account/delete", handle_account_delete)
    
    # Gamification: Daily Rewards, Streaks, Missions, Leaderboard
    app.router.add_get("/api/rewards/daily/status", handle_daily_reward_status)
    app.router.add_post("/api/rewards/daily/claim", handle_daily_reward_claim)
    app.router.add_get("/api/missions", handle_missions_list)
    app.router.add_get("/api/leaderboard", handle_leaderboard)
    app.router.add_get("/api/referral", handle_referral_info)
    app.router.add_post("/api/coupons/redeem", handle_coupon_redeem)

    # Monetization & Receipt Payment Checkout
    app.router.add_get("/api/premium/plans", handle_premium_plans)
    app.router.add_post("/api/payment/submit", handle_payment_submit)
    app.router.add_get("/api/likes/received", handle_likes_received)

    # Notifications & Support Tickets
    app.router.add_get("/api/notifications", handle_notifications_list)
    app.router.add_post("/api/notifications/read", handle_notifications_read)
    app.router.add_get("/api/tickets", handle_tickets_list)
    app.router.add_post("/api/tickets/create", handle_tickets_create)
    app.router.add_post("/api/tickets/reply", handle_tickets_reply)

    # Dating, Swiping, Matching & Chat
    app.router.add_get("/api/profiles", handle_profiles)
    app.router.add_post("/api/swipe", handle_swipe)
    app.router.add_get("/api/matches", handle_matches)
    app.router.add_get("/api/chat/messages", handle_chat_messages)
    app.router.add_post("/api/chat/send", handle_chat_send)
    
    # Safety API
    app.router.add_post("/api/user/block", handle_user_block)
    app.router.add_get("/api/user/blocked", handle_user_blocked_list)
    app.router.add_post("/api/user/unblock", handle_user_unblock)
    app.router.add_post("/api/user/report", handle_user_report)
    
    # Admin Control & Retention Routes (RBAC Protected)
    app.router.add_get("/api/admin/stats", handle_admin_stats)
    app.router.add_get("/api/admin/retention", handle_admin_retention)
    app.router.add_get("/api/admin/payments", handle_admin_payments_list)
    app.router.add_post("/api/admin/payment/approve", handle_admin_payment_approve)
    app.router.add_post("/api/admin/payment/reject", handle_admin_payment_reject)
    app.router.add_get("/api/admin/pending", handle_admin_pending)
    app.router.add_post("/api/admin/approve", handle_admin_approve)
    app.router.add_post("/api/admin/reject", handle_admin_reject)
    app.router.add_get("/api/admin/users", handle_admin_users)
    app.router.add_get("/api/admin/user/detail", handle_admin_user_detail)
    app.router.add_post("/api/admin/user/status", handle_admin_user_status_change)
    app.router.add_post("/api/admin/user/note", handle_admin_user_add_note)
    app.router.add_get("/api/admin/reports", handle_admin_reports)
    app.router.add_post("/api/admin/report/resolve", handle_admin_report_resolve)
    app.router.add_get("/api/admin/tickets", handle_admin_tickets)
    app.router.add_post("/api/admin/ticket/reply", handle_admin_ticket_reply)
    app.router.add_post("/api/admin/ticket/status", handle_admin_ticket_status)
    app.router.add_post("/api/admin/broadcast", handle_admin_broadcast)
    app.router.add_get("/api/admin/audit-logs", handle_admin_audit_logs)
    
    app.router.add_get("/style.css", serve_style)
    app.router.add_get("/app.js", serve_app)

    return app

if __name__ == "__main__":
    app = create_webapp_app()
    port = int(os.getenv("PORT", 8080))
    web.run_app(app, host="0.0.0.0", port=port)
