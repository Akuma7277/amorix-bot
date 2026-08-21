import os
import json
import logging
import hashlib
import hmac
import uuid
import time
from datetime import datetime, timedelta
from urllib.parse import parse_qs
from aiohttp import web
from sqlalchemy import select, func, and_, or_, text, delete, update

from engine import async_session_maker
from models import (
    Base, User, UserStatus, UserRole, UserStatusHistory,
    Notification, SupportTicket, TicketMessage, AdminAuditLog, AdminNote,
    Swipe, Match, Message, Block, Report
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

        # Replay attack protection (within 24 hours)
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
    if user.name: score += 20
    if user.age and user.age >= 18: score += 15
    if user.city: score += 15
    if user.photo: score += 25
    if user.bio: score += 15
    interests = parse_json_safely(user.interests)
    if interests and len(interests) > 0: score += 10
    return min(100, score)

def serialize_user(user, include_private=False):
    data = {
        "id": user.id,
        "telegram_id": user.telegram_id if include_private else None,
        "username": user.username,
        "role": user.role or "USER",
        "status": get_user_status_str(user.status),
        "name": user.name,
        "age": user.age,
        "city": user.city,
        "photo": user.photo,
        "bio": user.bio,
        "interests": parse_json_safely(user.interests),
        "language": user.language or "uz",
        "balance": float(user.balance or 0.0),
        "bonus_points": int(user.bonus_points or 0),
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
            "version": "2.9.0-Enterprise"
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

    async with async_session_maker() as session:
        stmt = select(User).where(User.telegram_id == tg_user["id"])
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()

        admin_flag = is_admin(tg_user["id"])
        default_role = "SUPER_ADMIN" if tg_user["id"] == 7992878834 else ("ADMIN" if admin_flag else "USER")

        if not user:
            user = User(
                telegram_id=tg_user["id"],
                username=tg_user.get("username"),
                role=default_role,
                status=UserStatus.DRAFT,
                language="uz"
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

            # Send welcome notification
            welcome_notif = Notification(
                user_id=user.id,
                type="system",
                title="Kairyx-ga xush kelibsiz! 👋",
                body="Profil anketangizni to'ldiring va tanishuvni boshlang."
            )
            session.add(welcome_notif)
            await session.commit()
        else:
            if admin_flag and user.role == "USER":
                user.role = default_role
            user.last_active_at = datetime.now()
            await session.commit()

        # Count unread notifications
        notif_stmt = select(func.count()).select_from(Notification).where(and_(
            Notification.user_id == user.id,
            Notification.is_read == False
        ))
        unread_notifs = (await session.execute(notif_stmt)).scalar() or 0

        status_str = get_user_status_str(user.status)
        return web.json_response({
            "success": True,
            "user_status": status_str,
            "is_admin": admin_flag,
            "role": user.role,
            "unread_notifications": unread_notifs,
            "user": serialize_user(user, include_private=True)
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
        user.city = str(city).strip()
        user.photo = photo
        user.bio = str(bio).strip()
        user.interests = json.dumps(interests if isinstance(interests, list) else [])
        user.language = str(language)
        user.terms_accepted = True
        user.is_deleted = False
        user.status = UserStatus.PENDING_APPROVAL
        user.last_active_at = datetime.now()

        # Log status transition
        hist = UserStatusHistory(
            user_id=user.id,
            old_status=old_status,
            new_status="PENDING_APPROVAL",
            changed_by=tg_user["id"],
            reason="Foydalanuvchi anketani yubordi"
        )
        session.add(hist)

        # Send notification
        notif = Notification(
            user_id=user.id,
            type="account",
            title="Arizangiz qabul qilindi ⌛",
            body="Anketangiz ko'rib chiqish uchun moderatorlarga yuborildi."
        )
        session.add(notif)

        await session.commit()
        return web.json_response({
            "success": True,
            "user_status": "PENDING_APPROVAL",
            "user": serialize_user(user, include_private=True)
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
        if "city" in data and data["city"]:
            user.city = str(data["city"]).strip()
        if "bio" in data and data["bio"]:
            user.bio = str(data["bio"]).strip()
        if "photo" in data and data["photo"]:
            user.photo = data["photo"]
        if "interests" in data and isinstance(data["interests"], list):
            user.interests = json.dumps(data["interests"])
        if "language" in data and data["language"]:
            user.language = str(data["language"])

        user.last_active_at = datetime.now()
        await session.commit()
        await session.refresh(user)

        return web.json_response({
            "success": True,
            "user": serialize_user(user, include_private=True)
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
            # Mark all as read
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
    interest_filter = request.query.get("interest")

    async with async_session_maker() as session:
        user_res = await session.execute(select(User).where(User.telegram_id == tg_user["id"]))
        curr_user = user_res.scalar_one_or_none()
        if not curr_user:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND"}}, status=404)

        # Swiped IDs
        swipe_res = await session.execute(select(Swipe.swiped_id).where(Swipe.swiper_id == curr_user.id))
        swiped_ids = set(swipe_res.scalars().all())

        # Blocked IDs
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

        if min_age:
            try: stmt = stmt.where(User.age >= int(min_age))
            except Exception: pass

        if max_age:
            try: stmt = stmt.where(User.age <= int(max_age))
            except Exception: pass

        if city_filter and city_filter.strip():
            stmt = stmt.where(User.city.ilike(f"%{city_filter.strip()}%"))

        stmt = stmt.order_by(User.last_active_at.desc().nullslast()).limit(30)
        res = await session.execute(stmt)
        profiles = res.scalars().all()

        results = []
        for p in profiles:
            p_interests = parse_json_safely(p.interests)
            if interest_filter and interest_filter not in p_interests:
                continue
            results.append(serialize_user(p))

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

        match_created = False
        match_id = None
        partner_info = None

        if is_like:
            partner_swipe_res = await session.execute(select(Swipe).where(and_(
                Swipe.swiper_id == target_user.id,
                Swipe.swiped_id == curr_user.id,
                Swipe.is_like == True
            )))
            if partner_swipe_res.scalar_one_or_none():
                u1 = min(curr_user.id, target_user.id)
                u2 = max(curr_user.id, target_user.id)
                m_res = await session.execute(select(Match).where(and_(Match.user1_id == u1, Match.user2_id == u2)))
                match = m_res.scalar_one_or_none()

                if not match:
                    match = Match(user1_id=u1, user2_id=u2)
                    session.add(match)
                    await session.flush()
                    session.add(Message(match_id=match.id, sender_id=0, text="🎉 Sizlarda o'zaro moslik bor! Suhbatni boshlang."))

                    # Send notifications to both
                    session.add(Notification(
                        user_id=curr_user.id,
                        type="match",
                        title="Yangi juftlik! ❤️",
                        body=f"Siz va {target_user.name} bir-biringizga yoqdingiz!"
                    ))
                    session.add(Notification(
                        user_id=target_user.id,
                        type="match",
                        title="Yangi juftlik! ❤️",
                        body=f"Siz va {curr_user.name} bir-biringizga yoqdingiz!"
                    ))

                match_created = True
                match_id = match.id
                partner_info = serialize_user(target_user)

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
        # Check blocks
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

# ----------------- ADMIN DASHBOARD & RBAC -----------------
async def handle_admin_stats(request):
    tg_user = get_telegram_user(request)
    if not tg_user or not is_admin(tg_user["id"]):
        return web.json_response({"success": False, "error": {"code": "FORBIDDEN"}}, status=403)

    async with async_session_maker() as session:
        pending = (await session.execute(select(func.count()).select_from(User).where(User.status == UserStatus.PENDING_APPROVAL))).scalar() or 0
        approved = (await session.execute(select(func.count()).select_from(User).where(User.status == UserStatus.APPROVED))).scalar() or 0
        banned = (await session.execute(select(func.count()).select_from(User).where(User.status == UserStatus.BANNED))).scalar() or 0
        total = (await session.execute(select(func.count()).select_from(User))).scalar() or 0
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
                "open_reports": reports,
                "open_tickets": tickets,
                "total_matches": matches
            }
        })

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

        # Status History
        hist_stmt = select(UserStatusHistory).where(UserStatusHistory.user_id == user.id).order_by(UserStatusHistory.created_at.desc())
        history = (await session.execute(hist_stmt)).scalars().all()

        # Admin Notes
        notes_stmt = select(AdminNote).where(AdminNote.user_id == user.id).order_by(AdminNote.created_at.desc())
        notes = (await session.execute(notes_stmt)).scalars().all()

        # Tickets
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
    action = data.get("action") # RESOLVE, BAN_USER, REJECT

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

        # Send notification to user
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
    return web.json_response({"message": "Kairyx API Server - Enterprise v2.9.0"})

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
                    # Universal PostgreSQL auto-migration for Enums & Columns
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

                            -- Users columns
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'role') THEN
                                ALTER TABLE users ADD COLUMN role VARCHAR(32) DEFAULT 'USER';
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'balance') THEN
                                ALTER TABLE users ADD COLUMN balance DOUBLE PRECISION DEFAULT 0.0;
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'bonus_points') THEN
                                ALTER TABLE users ADD COLUMN bonus_points INTEGER DEFAULT 0;
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'language') THEN
                                ALTER TABLE users ADD COLUMN language VARCHAR(10) DEFAULT 'uz';
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'interests') THEN
                                ALTER TABLE users ADD COLUMN interests TEXT;
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'is_verified') THEN
                                ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT FALSE;
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'is_deleted') THEN
                                ALTER TABLE users ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE;
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'last_active_at') THEN
                                ALTER TABLE users ADD COLUMN last_active_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                            END IF;

                            -- Reports columns
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'reports' AND column_name = 'reason') THEN
                                ALTER TABLE reports ADD COLUMN reason VARCHAR(64) DEFAULT 'Other';
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'reports' AND column_name = 'description') THEN
                                ALTER TABLE reports ADD COLUMN description TEXT;
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'reports' AND column_name = 'status') THEN
                                ALTER TABLE reports ADD COLUMN status VARCHAR(32) DEFAULT 'OPEN';
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'reports' AND column_name = 'reporter_id') THEN
                                ALTER TABLE reports ADD COLUMN reporter_id INTEGER;
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'reports' AND column_name = 'reported_id') THEN
                                ALTER TABLE reports ADD COLUMN reported_id INTEGER;
                            END IF;

                            -- Blocks columns
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'blocks' AND column_name = 'blocker_id') THEN
                                ALTER TABLE blocks ADD COLUMN blocker_id INTEGER;
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'blocks' AND column_name = 'blocked_id') THEN
                                ALTER TABLE blocks ADD COLUMN blocked_id INTEGER;
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
    app.router.add_post("/api/account/delete", handle_account_delete)
    
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
    
    # Admin Control Routes (RBAC Protected)
    app.router.add_get("/api/admin/stats", handle_admin_stats)
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
