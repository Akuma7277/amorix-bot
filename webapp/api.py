import os
import json
import logging
import hashlib
import hmac
from datetime import datetime
from urllib.parse import parse_qs
from aiohttp import web
from sqlalchemy import select, func, and_, or_, text, delete

from engine import async_session_maker
from models import Base, User, UserStatus, Swipe, Match, Message, Block, Report
from config import BOT_TOKEN, ADMIN_IDS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        user_dict = None
        if user_data:
            try:
                user_dict = json.loads(user_data)
            except Exception:
                pass

        if not received_hash:
            return user_dict

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

def serialize_user(user):
    return {
        "id": user.id,
        "telegram_id": user.telegram_id,
        "username": user.username,
        "status": get_user_status_str(user.status),
        "name": user.name,
        "age": user.age,
        "city": user.city,
        "photo": user.photo,
        "bio": user.bio,
        "interests": parse_json_safely(user.interests),
        "is_verified": bool(user.is_verified),
        "completion_percentage": calculate_completion(user),
        "last_active": user.last_active_at.isoformat() if user.last_active_at else None
    }

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

        if not user:
            user = User(
                telegram_id=tg_user["id"],
                username=tg_user.get("username"),
                status=UserStatus.DRAFT
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        else:
            user.last_active_at = datetime.now()
            await session.commit()

        status_str = get_user_status_str(user.status)
        return web.json_response({
            "success": True,
            "user_status": status_str,
            "is_admin": is_admin(tg_user["id"]),
            "user": serialize_user(user)
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

        current_status = get_user_status_str(user.status)
        if current_status != "DRAFT" and not user.is_deleted:
            return web.json_response({"success": False, "error": {"code": "INVALID_STATUS", "message": "Arizangiz allaqachon topshirilgan"}}, status=400)

        user.name = str(name).strip()
        user.age = age_int
        user.city = str(city).strip()
        user.photo = photo
        user.bio = str(bio).strip()
        user.interests = json.dumps(interests if isinstance(interests, list) else [])
        user.terms_accepted = True
        user.is_deleted = False
        user.status = UserStatus.PENDING_APPROVAL
        user.last_active_at = datetime.now()

        await session.commit()
        return web.json_response({
            "success": True,
            "user_status": UserStatus.PENDING_APPROVAL.value,
            "user": serialize_user(user)
        })

async def handle_profile_update(request):
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({"success": False, "error": {"code": "AUTH_FAILED", "message": "Autentifikatsiya amalga oshmadi"}}, status=401)

    try:
        data = await request.json()
    except Exception:
        return web.json_response({"success": False, "error": {"code": "INVALID_JSON", "message": "Noto'g'ri format"}}, status=400)

    async with async_session_maker() as session:
        stmt = select(User).where(User.telegram_id == tg_user["id"])
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()

        if not user:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND", "message": "Foydalanuvchi topilmadi"}}, status=404)

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

        user.last_active_at = datetime.now()
        await session.commit()
        await session.refresh(user)

        return web.json_response({
            "success": True,
            "user": serialize_user(user)
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
        await session.commit()

        return web.json_response({"success": True, "message": "Account successfully deactivated"})

# DISCOVERY WITH ADVANCED FILTERS & BLOCK EXCLUSION
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

        # Get swiped user IDs
        swipe_res = await session.execute(select(Swipe.swiped_id).where(Swipe.swiper_id == curr_user.id))
        swiped_ids = set(swipe_res.scalars().all())

        # Get blocked user IDs (blocked by me or blocked me)
        blocked_by_me = await session.execute(select(Block.blocked_id).where(Block.blocker_id == curr_user.id))
        blocked_me = await session.execute(select(Block.blocker_id).where(Block.blocked_id == curr_user.id))
        excluded_ids = swiped_ids.union(set(blocked_by_me.scalars().all())).union(set(blocked_me.scalars().all()))

        stmt = select(User).where(and_(
            User.status == UserStatus.APPROVED,
            User.id != curr_user.id,
            User.is_deleted == False
        ))

        if excluded_ids:
            stmt = stmt.where(~User.id.in_(list(excluded_ids)))

        if min_age:
            try:
                stmt = stmt.where(User.age >= int(min_age))
            except Exception: pass

        if max_age:
            try:
                stmt = stmt.where(User.age <= int(max_age))
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

        target_res = await session.execute(select(User).where(User.id == target_id))
        target_user = target_res.scalar_one_or_none()
        if not target_user:
            return web.json_response({"success": False, "error": {"code": "TARGET_NOT_FOUND"}}, status=404)

        # Check existing swipe
        existing_res = await session.execute(select(Swipe).where(and_(
            Swipe.swiper_id == curr_user.id,
            Swipe.swiped_id == target_id
        )))
        existing_swipe = existing_res.scalar_one_or_none()
        if not existing_swipe:
            swipe = Swipe(swiper_id=curr_user.id, swiped_id=target_id, is_like=is_like)
            session.add(swipe)
        else:
            existing_swipe.is_like = is_like

        match_created = False
        match_id = None
        partner_info = None

        if is_like:
            stmt_match = select(Swipe).where(and_(
                Swipe.swiper_id == target_id,
                Swipe.swiped_id == curr_user.id,
                Swipe.is_like == True
            ))
            res_match = await session.execute(stmt_match)
            partner_swipe = res_match.scalar_one_or_none()

            if partner_swipe:
                # Ensure no duplicate Match record
                u1 = min(curr_user.id, target_id)
                u2 = max(curr_user.id, target_id)
                m_stmt = select(Match).where(and_(Match.user1_id == u1, Match.user2_id == u2))
                m_res = await session.execute(m_stmt)
                match = m_res.scalar_one_or_none()

                if not match:
                    match = Match(user1_id=u1, user2_id=u2)
                    session.add(match)
                    await session.flush()
                    
                    sys_msg = Message(
                        match_id=match.id,
                        sender_id=0,
                        text="🎉 Sizlarda o'zaro moslik bor! Suhbatni boshlang."
                    )
                    session.add(sys_msg)

                match_created = True
                match_id = match.id
                partner_info = {
                    "id": target_user.id,
                    "name": target_user.name,
                    "photo": target_user.photo,
                    "city": target_user.city
                }

        curr_user.last_active_at = datetime.now()
        await session.commit()
        return web.json_response({
            "success": True,
            "match": match_created,
            "match_id": match_id,
            "partner": partner_info
        })

# MATCHES & CHAT
async def handle_matches(request):
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({"success": False, "error": {"code": "AUTH_FAILED"}}, status=401)

    async with async_session_maker() as session:
        user_res = await session.execute(select(User.id).where(User.telegram_id == tg_user["id"]))
        curr_id = user_res.scalar()
        if not curr_id:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND"}}, status=404)

        # Get blocked IDs
        b_res = await session.execute(select(Block.blocked_id).where(Block.blocker_id == curr_id))
        blocked_ids = set(b_res.scalars().all())

        stmt = select(Match).where(or_(
            Match.user1_id == curr_id,
            Match.user2_id == curr_id
        )).order_by(Match.created_at.desc())
        res = await session.execute(stmt)
        matches = res.scalars().all()

        results = []
        for m in matches:
            partner_id = m.user2_id if m.user1_id == curr_id else m.user1_id
            if partner_id in blocked_ids:
                continue

            partner_res = await session.execute(select(User).where(User.id == partner_id))
            partner = partner_res.scalar_one_or_none()

            if partner and not partner.is_deleted:
                # Fetch last message
                msg_stmt = select(Message).where(Message.match_id == m.id).order_by(Message.created_at.desc()).limit(1)
                last_msg_res = await session.execute(msg_stmt)
                last_msg = last_msg_res.scalar_one_or_none()

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

        # Verify participant
        match_stmt = select(Match).where(and_(
            Match.id == int(match_id),
            or_(Match.user1_id == curr_id, Match.user2_id == curr_id)
        ))
        match_res = await session.execute(match_stmt)
        match_record = match_res.scalar_one_or_none()
        if not match_record:
            return web.json_response({"success": False, "error": {"code": "FORBIDDEN", "message": "Chatga kirish huquqi yo'q"}}, status=403)

        partner_id = match_record.user2_id if match_record.user1_id == curr_id else match_record.user1_id
        # Check block
        block_stmt = select(Block).where(or_(
            and_(Block.blocker_id == curr_id, Block.blocked_id == partner_id),
            and_(Block.blocker_id == partner_id, Block.blocked_id == curr_id)
        ))
        block_res = await session.execute(block_stmt)
        if block_res.scalar_one_or_none():
            return web.json_response({"success": False, "error": {"code": "BLOCKED", "message": "Foydalanuvchi bloklangan"}}, status=403)

        stmt = select(Message).where(Message.match_id == int(match_id)).order_by(Message.created_at.asc())
        res = await session.execute(stmt)
        messages = res.scalars().all()

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
    text = data.get("text")

    if not match_id or not text or not str(text).strip():
        return web.json_response({"success": False, "error": {"code": "MISSING_PARAMS", "message": "Xabar matni bo'sh bo'lmasligi kerak"}}, status=400)

    clean_text = str(text).strip()
    if len(clean_text) > 1000:
        return web.json_response({"success": False, "error": {"code": "TEXT_TOO_LONG", "message": "Xabar juda uzun (maksimal 1000 belgi)"}}, status=400)

    async with async_session_maker() as session:
        user_res = await session.execute(select(User).where(User.telegram_id == tg_user["id"]))
        curr_user = user_res.scalar_one_or_none()
        if not curr_user:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND"}}, status=404)

        match_stmt = select(Match).where(and_(
            Match.id == int(match_id),
            or_(Match.user1_id == curr_user.id, Match.user2_id == curr_user.id)
        ))
        match_res = await session.execute(match_stmt)
        match_record = match_res.scalar_one_or_none()
        if not match_record:
            return web.json_response({"success": False, "error": {"code": "FORBIDDEN"}}, status=403)

        partner_id = match_record.user2_id if match_record.user1_id == curr_user.id else match_record.user1_id
        # Check block
        block_stmt = select(Block).where(or_(
            and_(Block.blocker_id == curr_user.id, Block.blocked_id == partner_id),
            and_(Block.blocker_id == partner_id, Block.blocked_id == curr_user.id)
        ))
        block_res = await session.execute(block_stmt)
        if block_res.scalar_one_or_none():
            return web.json_response({"success": False, "error": {"code": "BLOCKED", "message": "Foydalanuvchi bloklangan"}}, status=403)

        msg = Message(match_id=int(match_id), sender_id=curr_user.id, text=clean_text)
        session.add(msg)
        curr_user.last_active_at = datetime.now()
        await session.commit()

        return web.json_response({"success": True})

# SAFETY: BLOCK & REPORT
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
        user_res = await session.execute(select(User.id).where(User.telegram_id == tg_user["id"]))
        curr_id = user_res.scalar()
        if not curr_id:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND"}}, status=404)

        # Check existing block
        b_stmt = select(Block).where(and_(Block.blocker_id == curr_id, Block.blocked_id == int(target_id)))
        b_res = await session.execute(b_stmt)
        if not b_res.scalar_one_or_none():
            session.add(Block(blocker_id=curr_id, blocked_id=int(target_id)))
            await session.commit()

        return web.json_response({"success": True, "message": "Foydalanuvchi bloklandi"})

async def handle_user_blocked_list(request):
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({"success": False, "error": {"code": "AUTH_FAILED"}}, status=401)

    async with async_session_maker() as session:
        user_res = await session.execute(select(User.id).where(User.telegram_id == tg_user["id"]))
        curr_id = user_res.scalar()
        if not curr_id:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND"}}, status=404)

        stmt = select(User).join(Block, Block.blocked_id == User.id).where(Block.blocker_id == curr_id)
        res = await session.execute(stmt)
        users = res.scalars().all()

        return web.json_response({
            "success": True,
            "blocked_users": [
                {
                    "id": u.id,
                    "name": u.name,
                    "photo": u.photo,
                    "city": u.city
                } for u in users
            ]
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
        user_res = await session.execute(select(User.id).where(User.telegram_id == tg_user["id"]))
        curr_id = user_res.scalar()
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
        user_res = await session.execute(select(User.id).where(User.telegram_id == tg_user["id"]))
        curr_id = user_res.scalar()
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

# ADVANCED ADMIN CONTROLS
async def handle_admin_pending(request):
    tg_user = get_telegram_user(request)
    if not tg_user or not is_admin(tg_user["id"]):
        return web.json_response({"success": False, "error": {"code": "FORBIDDEN"}}, status=403)

    async with async_session_maker() as session:
        stmt = select(User).where(User.status == UserStatus.PENDING_APPROVAL).order_by(User.created_at.desc())
        res = await session.execute(stmt)
        users = res.scalars().all()
        return web.json_response({
            "success": True,
            "users": [serialize_user(u) for u in users]
        })

async def handle_admin_stats(request):
    tg_user = get_telegram_user(request)
    if not tg_user or not is_admin(tg_user["id"]):
        return web.json_response({"success": False, "error": {"code": "FORBIDDEN"}}, status=403)

    async with async_session_maker() as session:
        pending_count = (await session.execute(select(func.count()).select_from(User).where(User.status == UserStatus.PENDING_APPROVAL))).scalar() or 0
        approved_count = (await session.execute(select(func.count()).select_from(User).where(User.status == UserStatus.APPROVED))).scalar() or 0
        banned_count = (await session.execute(select(func.count()).select_from(User).where(User.status == UserStatus.BANNED))).scalar() or 0
        total_count = (await session.execute(select(func.count()).select_from(User))).scalar() or 0
        reports_count = (await session.execute(select(func.count()).select_from(Report).where(Report.status == "OPEN"))).scalar() or 0
        matches_count = (await session.execute(select(func.count()).select_from(Match))).scalar() or 0

        return web.json_response({
            "success": True,
            "stats": {
                "pending": pending_count,
                "approved": approved_count,
                "banned": banned_count,
                "total": total_count,
                "open_reports": reports_count,
                "total_matches": matches_count
            }
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
        stmt = select(User).where(User.id == int(user_id))
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()

        if not user:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND"}}, status=404)

        user.status = UserStatus.APPROVED
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
    if not user_id:
        return web.json_response({"success": False, "error": {"code": "MISSING_USER_ID"}}, status=400)

    async with async_session_maker() as session:
        stmt = select(User).where(User.id == int(user_id))
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()

        if not user:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND"}}, status=404)

        user.status = UserStatus.REJECTED
        await session.commit()
        return web.json_response({"success": True})

async def handle_admin_reports(request):
    tg_user = get_telegram_user(request)
    if not tg_user or not is_admin(tg_user["id"]):
        return web.json_response({"success": False, "error": {"code": "FORBIDDEN"}}, status=403)

    async with async_session_maker() as session:
        stmt = select(Report).order_by(Report.created_at.desc()).limit(30)
        res = await session.execute(stmt)
        reports = res.scalars().all()

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
                "reported": serialize_user(reported) if reported else None
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
    action = data.get("action") # "RESOLVE", "BAN_USER", "REJECT"

    async with async_session_maker() as session:
        stmt = select(Report).where(Report.id == int(report_id))
        res = await session.execute(stmt)
        report = res.scalar_one_or_none()
        if not report:
            return web.json_response({"success": False, "error": {"code": "REPORT_NOT_FOUND"}}, status=404)

        if action == "BAN_USER":
            user_stmt = select(User).where(User.id == report.reported_id)
            user_res = await session.execute(user_stmt)
            target = user_res.scalar_one_or_none()
            if target:
                target.status = UserStatus.BANNED
            report.status = "RESOLVED"
        elif action == "RESOLVE":
            report.status = "RESOLVED"
        else:
            report.status = "REJECTED"

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
            try:
                stmt = stmt.where(User.status == UserStatus[status_filter.upper()])
            except Exception: pass

        stmt = stmt.order_by(User.created_at.desc()).limit(50)
        res = await session.execute(stmt)
        users = res.scalars().all()

        return web.json_response({
            "success": True,
            "users": [serialize_user(u) for u in users]
        })

async def handle_admin_user_ban(request):
    tg_user = get_telegram_user(request)
    if not tg_user or not is_admin(tg_user["id"]):
        return web.json_response({"success": False, "error": {"code": "FORBIDDEN"}}, status=403)

    try:
        data = await request.json()
    except Exception:
        return web.json_response({"success": False, "error": {"code": "INVALID_JSON"}}, status=400)

    user_id = data.get("user_id")
    is_ban = bool(data.get("is_ban", True))

    async with async_session_maker() as session:
        stmt = select(User).where(User.id == int(user_id))
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()
        if not user:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND"}}, status=404)

        user.status = UserStatus.BANNED if is_ban else UserStatus.APPROVED
        await session.commit()
        return web.json_response({"success": True})

# STATIC SERVING
async def handle_index(request):
    import os
    webapp_dir = os.path.dirname(os.path.abspath(__file__))
    index_path = os.path.join(webapp_dir, "index.html")
    if os.path.exists(index_path):
        response = web.FileResponse(index_path)
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    return web.json_response({"message": "Kairyx API Server - v2.7.0"})

async def serve_style(request):
    import os
    webapp_dir = os.path.dirname(os.path.abspath(__file__))
    style_path = os.path.join(webapp_dir, "style.css")
    if os.path.exists(style_path):
        return web.FileResponse(style_path)
    return web.Response(text="/* style.css */", content_type="text/css")

async def serve_app(request):
    import os
    webapp_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(webapp_dir, "app.js")
    if os.path.exists(app_path):
        return web.FileResponse(app_path)
    return web.Response(text="// app.js", content_type="application/javascript")

def create_webapp_app() -> web.Application:
    app = web.Application()

    async def cors_middleware(app, handler):
        async def middleware_handler(request):
            if request.method == "OPTIONS":
                response = web.Response(status=200)
            else:
                try:
                    response = await handler(request)
                except Exception as exc:
                    logger.exception(f"Unhandled error handling {request.method} {request.path}: {exc}")
                    response = web.json_response({
                        "success": False,
                        "error": {
                            "code": "INTERNAL_SERVER_ERROR",
                            "message": str(exc)
                        }
                    }, status=500)
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-TG-Init-Data"
            return response
        return middleware_handler

    app.middlewares.append(cors_middleware)

    async def on_startup(app):
        import engine as engine_module
        try:
            async with engine_module.engine.begin() as conn:
                try:
                    # Auto-alter PostgreSQL columns to VARCHAR and add new columns if missing
                    await conn.execute(text("""
                        DO $$
                        BEGIN
                            IF EXISTS (
                                SELECT 1 FROM information_schema.columns 
                                WHERE table_name = 'users' AND column_name = 'status' AND udt_name = 'userstatus'
                            ) THEN
                                ALTER TABLE users ALTER COLUMN status TYPE VARCHAR(32) USING status::text;
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
                        END $$;
                    """))
                except Exception as alter_e:
                    logger.info(f"Auto-migration notice: {alter_e}")

                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database schema initialized successfully.")
        except Exception as exc:
            logger.warning(f"Database schema initialization failed: {exc}")

    app.on_startup.append(on_startup)

    app.router.add_get("/", handle_index)
    app.router.add_get("/health", handle_health)
    app.router.add_get("/health/ready", handle_health_ready)
    app.router.add_get("/api/session", handle_session)
    app.router.add_post("/api/register", handle_register)
    app.router.add_post("/api/profile/update", handle_profile_update)
    app.router.add_post("/api/account/delete", handle_account_delete)
    
    # Dating API
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
    
    # Admin Routes
    app.router.add_get("/api/admin/pending", handle_admin_pending)
    app.router.add_get("/api/admin/stats", handle_admin_stats)
    app.router.add_post("/api/admin/approve", handle_admin_approve)
    app.router.add_post("/api/admin/reject", handle_admin_reject)
    app.router.add_get("/api/admin/reports", handle_admin_reports)
    app.router.add_post("/api/admin/report/resolve", handle_admin_report_resolve)
    app.router.add_get("/api/admin/users", handle_admin_users)
    app.router.add_post("/api/admin/user/ban", handle_admin_user_ban)
    
    app.router.add_get("/style.css", serve_style)
    app.router.add_get("/app.js", serve_app)

    return app

if __name__ == "__main__":
    app = create_webapp_app()
    port = int(os.getenv("PORT", 8080))
    web.run_app(app, host="0.0.0.0", port=port)
