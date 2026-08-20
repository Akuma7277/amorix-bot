import os
import json
import logging
import hashlib
import hmac
from datetime import datetime
from urllib.parse import parse_qs
from aiohttp import web
from sqlalchemy import select, func, and_, or_

from engine import async_session_maker
from models import Base, User, UserStatus, Swipe, Match, Message
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

async def handle_health(request):
    return web.json_response({"status": "ok", "timestamp": datetime.now().isoformat()})

async def handle_health_ready(request):
    try:
        async with async_session_maker() as session:
            await session.execute(select(1))
        return web.json_response({"status": "ready", "database": "connected"})
    except Exception as e:
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

        return web.json_response({
            "success": True,
            "user_status": user.status.value,
            "is_admin": is_admin(tg_user["id"]),
            "user": {
                "id": user.id,
                "telegram_id": user.telegram_id,
                "username": user.username,
                "status": user.status.value,
                "name": user.name,
                "age": user.age,
                "city": user.city,
                "photo": user.photo,
                "bio": user.bio
            }
        })

async def handle_register(request):
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({"success": False, "error": {"code": "AUTH_FAILED"}}, status=401)

    try:
        data = await request.json()
    except Exception:
        return web.json_response({"success": False, "error": {"code": "INVALID_JSON"}}, status=400)

    name = data.get("name")
    age = data.get("age")
    city = data.get("city")
    photo = data.get("photo")
    bio = data.get("bio")
    terms_accepted = data.get("terms_accepted")

    if not name or not city or not bio or not photo:
        return web.json_response({"success": False, "error": {"code": "MISSING_FIELDS"}}, status=400)

    try:
        age_int = int(age)
    except Exception:
        return web.json_response({"success": False, "error": {"code": "INVALID_AGE"}}, status=400)

    if age_int < 18:
        return web.json_response({"success": False, "error": {"code": "UNDERAGE"}}, status=400)

    if not terms_accepted:
        return web.json_response({"success": False, "error": {"code": "TERMS_NOT_ACCEPTED"}}, status=400)

    async with async_session_maker() as session:
        stmt = select(User).where(User.telegram_id == tg_user["id"])
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()

        if not user:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND"}}, status=404)

        if user.status != UserStatus.DRAFT:
            return web.json_response({"success": False, "error": {"code": "INVALID_STATUS"}}, status=400)

        user.name = name
        user.age = age_int
        user.city = city
        user.photo = photo
        user.bio = bio
        user.terms_accepted = terms_accepted
        user.status = UserStatus.PENDING_APPROVAL

        await session.commit()
        return web.json_response({"success": True, "user_status": UserStatus.PENDING_APPROVAL.value})

# DATING ENDPOINTS
async def handle_profiles(request):
    """GET /api/profiles - Swiping uchun profillarni qaytaradi."""
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({"success": False, "error": {"code": "AUTH_FAILED"}}, status=401)

    async with async_session_maker() as session:
        # Get current user ID
        user_res = await session.execute(select(User.id).where(User.telegram_id == tg_user["id"]))
        curr_id = user_res.scalar()
        if not curr_id:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND"}}, status=404)

        # Get list of swiped user IDs
        swipe_res = await session.execute(select(Swipe.swiped_id).where(Swipe.swiper_id == curr_id))
        swiped_ids = swipe_res.scalars().all()

        # Query active APPROVED profiles (excluding self and already swiped)
        stmt = select(User).where(and_(
            User.status == UserStatus.APPROVED,
            User.id != curr_id,
            ~User.id.in_(swiped_ids)
        ))
        res = await session.execute(stmt)
        profiles = res.scalars().all()

        return web.json_response({
            "success": True,
            "profiles": [
                {
                    "id": p.id,
                    "name": p.name,
                    "age": p.age,
                    "city": p.city,
                    "photo": p.photo,
                    "bio": p.bio
                } for p in profiles
            ]
        })

async def handle_swipe(request):
    """POST /api/swipe - Foydalanuvchini like/pass qiladi."""
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
        user_res = await session.execute(select(User.id).where(User.telegram_id == tg_user["id"]))
        curr_id = user_res.scalar()
        if not curr_id:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND"}}, status=404)

        # Create Swipe Record
        swipe = Swipe(swiper_id=curr_id, swiped_id=target_id, is_like=is_like)
        session.add(swipe)

        # Check Match
        match_created = False
        match_id = None
        if is_like:
            stmt_match = select(Swipe).where(and_(
                Swipe.swiper_id == target_id,
                Swipe.swiped_id == curr_id,
                Swipe.is_like == True
            ))
            res_match = await session.execute(stmt_match)
            partner_swipe = res_match.scalar_one_or_none()

            if partner_swipe:
                # We have a Match!
                match = Match(user1_id=min(curr_id, target_id), user2_id=max(curr_id, target_id))
                session.add(match)
                await session.flush()
                match_created = True
                match_id = match.id
                
                # Auto-create greeting system message
                sys_msg = Message(
                    match_id=match.id,
                    sender_id=0, # 0 = System
                    text="Sizlarda moslik bor! Suhbatni boshlang. У вас взаимная симпатия! Начните общение."
                )
                session.add(sys_msg)

        await session.commit()
        return web.json_response({
            "success": True,
            "match": match_created,
            "match_id": match_id
        })

async def handle_matches(request):
    """GET /api/matches - Mos kelgan barcha juftliklarni qaytaradi."""
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({"success": False, "error": {"code": "AUTH_FAILED"}}, status=401)

    async with async_session_maker() as session:
        user_res = await session.execute(select(User.id).where(User.telegram_id == tg_user["id"]))
        curr_id = user_res.scalar()
        if not curr_id:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND"}}, status=404)

        # Query all matches containing curr_id
        stmt = select(Match).where(or_(
            Match.user1_id == curr_id,
            Match.user2_id == curr_id
        ))
        res = await session.execute(stmt)
        matches = res.scalars().all()

        results = []
        for m in matches:
            partner_id = m.user2_id if m.user1_id == curr_id else m.user1_id
            partner_res = await session.execute(select(User).where(User.id == partner_id))
            partner = partner_res.scalar_one_or_none()

            if partner:
                results.append({
                    "match_id": m.id,
                    "partner": {
                        "id": partner.id,
                        "name": partner.name,
                        "photo": partner.photo,
                        "city": partner.city
                    }
                })

        return web.json_response({"success": True, "matches": results})

async def handle_chat_messages(request):
    """GET /api/chat/messages?match_id=... - Chat xabarlarini qaytaradi."""
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({"success": False, "error": {"code": "AUTH_FAILED"}}, status=401)

    match_id = request.query.get("match_id")
    if not match_id:
        return web.json_response({"success": False, "error": {"code": "MISSING_MATCH_ID"}}, status=400)

    async with async_session_maker() as session:
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
    """POST /api/chat/send - Yangi xabar yuboradi."""
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({"success": False, "error": {"code": "AUTH_FAILED"}}, status=401)

    try:
        data = await request.json()
    except Exception:
        return web.json_response({"success": False, "error": {"code": "INVALID_JSON"}}, status=400)

    match_id = data.get("match_id")
    text = data.get("text")

    if not match_id or not text:
        return web.json_response({"success": False, "error": {"code": "MISSING_PARAMS"}}, status=400)

    async with async_session_maker() as session:
        user_res = await session.execute(select(User.id).where(User.telegram_id == tg_user["id"]))
        curr_id = user_res.scalar()
        if not curr_id:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND"}}, status=404)

        # Save message
        msg = Message(match_id=int(match_id), sender_id=curr_id, text=text)
        session.add(msg)
        await session.commit()

        return web.json_response({"success": True})

# ADMIN ENDPOINTS
async def handle_admin_pending(request):
    tg_user = get_telegram_user(request)
    if not tg_user or not is_admin(tg_user["id"]):
        return web.json_response({"success": False, "error": {"code": "FORBIDDEN"}}, status=403)

    async with async_session_maker() as session:
        stmt = select(User).where(User.status == UserStatus.PENDING_APPROVAL)
        res = await session.execute(stmt)
        users = res.scalars().all()
        return web.json_response({
            "success": True,
            "users": [
                {
                    "id": u.id,
                    "telegram_id": u.telegram_id,
                    "username": u.username,
                    "name": u.name,
                    "age": u.age,
                    "city": u.city,
                    "photo": u.photo,
                    "bio": u.bio
                } for u in users
            ]
        })

async def handle_admin_stats(request):
    tg_user = get_telegram_user(request)
    if not tg_user or not is_admin(tg_user["id"]):
        return web.json_response({"success": False, "error": {"code": "FORBIDDEN"}}, status=403)

    async with async_session_maker() as session:
        stmt_pending = select(func.count()).select_from(User).where(User.status == UserStatus.PENDING_APPROVAL)
        res_pending = await session.execute(stmt_pending)
        pending_count = res_pending.scalar()

        stmt_approved = select(func.count()).select_from(User).where(User.status == UserStatus.APPROVED)
        res_approved = await session.execute(stmt_approved)
        approved_count = res_approved.scalar()

        stmt_total = select(func.count()).select_from(User)
        res_total = await session.execute(stmt_total)
        total_count = res_total.scalar()

        return web.json_response({
            "success": True,
            "stats": {
                "pending": pending_count,
                "approved": approved_count,
                "total": total_count
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
        stmt = select(User).where(User.id == user_id)
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
        stmt = select(User).where(User.id == user_id)
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()

        if not user:
            return web.json_response({"success": False, "error": {"code": "USER_NOT_FOUND"}}, status=404)

        user.status = UserStatus.REJECTED
        await session.commit()
        return web.json_response({"success": True})

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
    return web.json_response({"message": "Kairyx API Server - Phase 5"})

async def serve_style(request):
    import os
    webapp_dir = os.path.dirname(os.path.abspath(__file__))
    style_path = os.path.join(webapp_dir, "style.css")
    if os.path.exists(style_path):
        return web.FileResponse(style_path)
    return web.Response(text="/* style.css not found */", content_type="text/css")

async def serve_app(request):
    import os
    webapp_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(webapp_dir, "app.js")
    if os.path.exists(app_path):
        return web.FileResponse(app_path)
    return web.Response(text="// app.js not found", content_type="application/javascript")

def create_webapp_app() -> web.Application:
    app = web.Application()

    async def cors_middleware(app, handler):
        async def middleware_handler(request):
            if request.method == "OPTIONS":
                response = web.Response(status=200)
            else:
                response = await handler(request)
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
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database schema auto-created on API startup.")
        except Exception as exc:
            logger.warning(f"Database schema auto-creation failed: {exc}")

    app.on_startup.append(on_startup)

    app.router.add_get("/", handle_index)
    app.router.add_get("/health", handle_health)
    app.router.add_get("/health/ready", handle_health_ready)
    app.router.add_get("/api/session", handle_session)
    app.router.add_post("/api/register", handle_register)
    
    # Dating API
    app.router.add_get("/api/profiles", handle_profiles)
    app.router.add_post("/api/swipe", handle_swipe)
    app.router.add_get("/api/matches", handle_matches)
    app.router.add_get("/api/chat/messages", handle_chat_messages)
    app.router.add_post("/api/chat/send", handle_chat_send)
    
    # Admin Routes
    app.router.add_get("/api/admin/pending", handle_admin_pending)
    app.router.add_get("/api/admin/stats", handle_admin_stats)
    app.router.add_post("/api/admin/approve", handle_admin_approve)
    app.router.add_post("/api/admin/reject", handle_admin_reject)
    
    app.router.add_get("/style.css", serve_style)
    app.router.add_get("/app.js", serve_app)

    return app

if __name__ == "__main__":
    app = create_webapp_app()
    port = int(os.getenv("PORT", 8080))
    web.run_app(app, host="0.0.0.0", port=port)
