"""
Kairyx Mini App - Complete REST API Server
Handles all dating operations and admin functions inside the Mini App.
"""
import hashlib
import hmac
import json
import logging
import os
from datetime import datetime, timedelta
from urllib.parse import parse_qs

from aiohttp import web
from sqlalchemy import select, and_, or_, func, update, delete
from sqlalchemy.orm import selectinload

from engine import async_session_maker
from models import (
    User, Photo, Like, Match, ChatMessage, Payment, VerificationRequest, BlockedUser, Notification, 
    UserStatus, VerificationStatus, PremiumPlan, RelationshipIntent,
    UserGender, LookingForGender
)
from config import BOT_TOKEN, ADMIN_IDS, DEV_MODE

logger = logging.getLogger(__name__)


def validate_telegram_init_data(init_data: str, bot_token: str) -> dict | None:
    """Telegram WebApp initData ni tekshiradi."""
    if not init_data:
        return None
    
    # Mock data for local testing
    if init_data == "mock_admin":
        return {"id": 7992878834, "first_name": "Admin", "username": "admin_test"}
    if init_data == "mock_user":
        return {"id": 12345678, "first_name": "User Test", "username": "user_test"}

    try:
        parsed = parse_qs(init_data)
        received_hash = parsed.get("hash", [None])[0]
        if not received_hash:
            return None

        # Remove hash and reconstruct data check string
        sorted_params = []
        for k in sorted(parsed.keys()):
            if k != "hash":
                sorted_params.append(f"{k}={parsed[k][0]}")
        data_check_string = "\n".join(sorted_params)

        secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        if computed_hash != received_hash:
            return None

        user_data = parsed.get("user", [None])[0]
        if user_data:
            return json.loads(user_data)
        return None
    except Exception as e:
        logger.warning(f"initData validation failed: {e}")
        return None


def get_telegram_user(request) -> dict | None:
    """Request-dan Telegram user ma'lumotlarini oladi."""
    init_data = request.headers.get("X-TG-Init-Data") or request.query.get("initData")
    # Also support authorization header
    if not init_data:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            init_data = auth_header.split(" ")[1]
            
    if not init_data:
        if DEV_MODE:
            # Fallback for dev mode only
            return {"id": 7992878834, "first_name": "Developer"}
        return None
        
    return validate_telegram_init_data(init_data, BOT_TOKEN)


def serialize_user(user: User, photos=None) -> dict:
    """User obyektini JSON-ga moslashtiradi."""
    return {
        "id": user.id,
        "telegram_id": user.telegram_id,
        "name": user.name,
        "age": user.age,
        "gender": user.gender.value if user.gender else None,
        "looking_for": user.looking_for.value if user.looking_for else None,
        "city": user.city,
        "district": user.district,
        "bio": user.bio,
        "interests": user.interests.split(",") if user.interests else [],
        "language": user.language,
        "status": user.status.value if user.status else None,
        "verification_status": user.verification_status.value if user.verification_status else None,
        "premium_plan": user.premium_plan.value if user.premium_plan else "Basic",
        "premium_expires_at": user.premium_expires_at.isoformat() if user.premium_expires_at else None,
        "is_premium": user.is_premium,
        "is_admin": user.is_admin or (user.telegram_id in ADMIN_IDS),
        "height": user.height,
        "is_invisible": user.is_invisible,
        "relationship_intent": user.relationship_intent.value if user.relationship_intent else None,
        "photos": [p.file_id for p in photos] if photos else []
    }


# ==========================================
# API ENDPOINTS
# ==========================================

async def handle_init(request):
    """GET /api/init - Foydalanuvchini tekshiradi va status qaytaradi."""
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({"status": "error", "message": "Unauthorized"}, status=401)
    
    async with async_session_maker() as session:
        # Check if user exists
        stmt = select(User).where(User.telegram_id == tg_user["id"])
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            return web.json_response({
                "registered": False,
                "user_status": "draft",
                "telegram_id": tg_user["id"],
                "name": tg_user.get("first_name", "")
            })
            
        # Get photos
        p_stmt = select(Photo).where(Photo.user_id == user.id).order_by(Photo.order)
        p_res = await session.execute(p_stmt)
        photos = p_res.scalars().all()
        
        user_status = user.status.name if user.status else "draft"
        
        return web.json_response({
            "registered": True,
            "user_status": user_status,
            "user": serialize_user(user, photos),
            "rejection_reason": user.rejection_reason if user.status == UserStatus.rejected else None
        })


async def handle_register(request):
    """POST /api/register - Yangi foydalanuvchi ro'yxatdan o'tishi."""
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({"status": "error", "message": "Unauthorized"}, status=401)
        
    try:
        data = await request.json()
        async with async_session_maker() as session:
            # Check existing
            stmt = select(User).where(User.telegram_id == tg_user["id"])
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                return web.json_response({"status": "error", "message": "Already registered"}, status=400)
                
            # Convert strings to Enums
            gender_enum = UserGender.male if data.get("gender") == "Erkak" else UserGender.female
            
            looking_for_map = {
                "Erkak": LookingForGender.male,
                "Ayol": LookingForGender.female,
                "Farqi yo'q": LookingForGender.any
            }
            looking_for_enum = looking_for_map.get(data.get("looking_for"), LookingForGender.any)
            
            intent_map = {
                "serious": RelationshipIntent.serious,
                "marriage": RelationshipIntent.marriage,
                "friendship": RelationshipIntent.friendship,
                "explore": RelationshipIntent.explore,
                "private": RelationshipIntent.private
            }
            intent_enum = intent_map.get(data.get("relationship_intent"), RelationshipIntent.explore)
            
            user = User(
                telegram_id=tg_user["id"],
                name=data.get("name"),
                age=int(data.get("age", 18)),
                gender=gender_enum,
                looking_for=looking_for_enum,
                city=data.get("city"),
                district=data.get("district", ""),
                bio=data.get("bio", ""),
                interests=",".join(data.get("interests", [])),
                language=data.get("language", "uz"),
                height=float(data.get("height")) if data.get("height") else None,
                relationship_intent=intent_enum,
                premium_plan=PremiumPlan.basic,
                status=UserStatus.pending_approval
            )
            
            session.add(user)
            await session.flush()
            
            # Save photos
            photo_urls = data.get("photos", [])
            for idx, photo_url in enumerate(photo_urls):
                photo = Photo(
                    user_id=user.id,
                    file_id=photo_url,  # Telegram file_id or link
                    order=idx + 1,
                    is_approved=True  # Auto approve for simplicity, or false
                )
                session.add(photo)
                
            await session.commit()
            return web.json_response({"status": "ok", "user_status": "pending_approval", "user": serialize_user(user)})
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def handle_profile(request):
    """GET /api/profile - Profil ma'lumotlarini olish."""
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({"status": "error", "message": "Unauthorized"}, status=401)
        
    async with async_session_maker() as session:
        stmt = select(User).where(User.telegram_id == tg_user["id"])
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            return web.json_response({"status": "error", "message": "User not found"}, status=404)
            
        p_stmt = select(Photo).where(Photo.user_id == user.id).order_by(Photo.order)
        p_res = await session.execute(p_stmt)
        photos = p_res.scalars().all()
        
        return web.json_response({"status": "ok", "user": serialize_user(user, photos)})


async def handle_profile_update(request):
    """POST /api/profile/update - Profilni yangilash."""
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({"status": "error", "message": "Unauthorized"}, status=401)
        
    try:
        data = await request.json()
        async with async_session_maker() as session:
            stmt = select(User).where(User.telegram_id == tg_user["id"])
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                return web.json_response({"status": "error", "message": "User not found"}, status=404)
                
            # Update fields
            if "name" in data: user.name = data["name"]
            if "age" in data: user.age = int(data["age"])
            if "city" in data: user.city = data["city"]
            if "district" in data: user.district = data["district"]
            if "bio" in data: user.bio = data["bio"]
            if "height" in data: user.height = float(data["height"]) if data["height"] else None
            if "interests" in data: user.interests = ",".join(data["interests"])
            if "is_invisible" in data: user.is_invisible = bool(data["is_invisible"])
            
            if "relationship_intent" in data:
                intent_map = {
                    "serious": RelationshipIntent.serious,
                    "marriage": RelationshipIntent.marriage,
                    "friendship": RelationshipIntent.friendship,
                    "explore": RelationshipIntent.explore,
                    "private": RelationshipIntent.private
                }
                user.relationship_intent = intent_map.get(data["relationship_intent"], user.relationship_intent)

            await session.commit()
            return web.json_response({"status": "ok", "user": serialize_user(user)})
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def handle_profiles(request):
    """GET /api/profiles - Swipe qilish uchun mos profillar ro'yxati."""
    try:
        tg_user, user = await require_approved_user(request)
    except web.HTTPException as ex:
        raise ex
        
    async with async_session_maker() as session:
            
        # Get profiles that current user has NOT liked or nope-d yet
        # Also respect gender preferences
        liked_stmt = select(Like.to_user_id).where(Like.from_user_id == user.id)
        liked_res = await session.execute(liked_stmt)
        exclude_ids = list(liked_res.scalars().all())
        exclude_ids.append(user.id)
        
        # Filter out users blocked by the current user
        blocked_stmt = select(BlockedUser.blocked_id).where(BlockedUser.blocker_id == user.id)
        blocked_res = await session.execute(blocked_stmt)
        exclude_ids.extend(blocked_res.scalars().all())
        
        # Filter out users who have blocked the current user
        blocked_by_stmt = select(BlockedUser.blocker_id).where(BlockedUser.blocked_id == user.id)
        blocked_by_res = await session.execute(blocked_by_stmt)
        exclude_ids.extend(blocked_by_res.scalars().all())
        
        q = select(User).where(
            and_(
                User.id.not_in(exclude_ids),
                User.status == UserStatus.active,
                User.is_invisible == False
            )
        )
        
        # Gender filter
        if user.looking_for == LookingForGender.male:
            q = q.where(User.gender == UserGender.male)
        elif user.looking_for == LookingForGender.female:
            q = q.where(User.gender == UserGender.female)
            
        # Parse query params
        min_age = int(request.query.get("min_age", 18))
        max_age = int(request.query.get("max_age", 100))
        filter_city = request.query.get("city", "").strip()
        filter_intent = request.query.get("intent", "").strip()
        online_only = request.query.get("online", "false").lower() == "true"
        verified_only = request.query.get("verified", "false").lower() == "true"
        quick = request.query.get("quick", "all").strip()

        # Apply age filter
        q = q.where(and_(User.age >= min_age, User.age <= max_age))

        # Apply city filter
        if filter_city:
            q = q.where(User.city == filter_city)

        # Apply intent filter
        if filter_intent:
            from models import RelationshipIntent
            try:
                q = q.where(User.relationship_intent == RelationshipIntent[filter_intent])
            except KeyError:
                pass

        # Apply online filter (active within 15 minutes)
        if online_only or quick == "online":
            from datetime import timedelta
            q = q.where(User.last_activity >= datetime.now() - timedelta(minutes=15))

        # Apply verified filter
        if verified_only or quick == "verified":
            from models import VerificationStatus
            q = q.where(User.verification_status == VerificationStatus.verified)

        # Apply quick Mening shahrim filter
        if quick == "city":
            q = q.where(User.city == user.city)

        q = q.order_by(func.random()).limit(20)
        q_res = await session.execute(q)
        profiles = q_res.scalars().all()
        
        serialized_profiles = []
        for p in profiles:
            p_photos_stmt = select(Photo).where(Photo.user_id == p.id).order_by(Photo.order)
            p_photos_res = await session.execute(p_photos_stmt)
            p_photos = p_photos_res.scalars().all()
            
            # Detailed compatibility score and breakdown
            score = 50
            reasons = []
            
            # City compatibility
            if p.city == user.city:
                score += 15
                reasons.append(f"Ikkalangiz ham {user.city}da yashaysiz")
                
            # Intent compatibility
            if p.relationship_intent and p.relationship_intent == user.relationship_intent:
                score += 15
                intent_vals = {
                    "serious": "jiddiy munosabat",
                    "marriage": "nikohga tayyorgarlik",
                    "friendship": "do\'stlik va suhbat",
                    "explore": "yangi insonlar bilan tanishish",
                    "private": "niyatini yashirish"
                }
                intent_name = intent_vals.get(p.relationship_intent.name, "o\'xshash maqsadlar")
                reasons.append(f"Ikkalangiz ham {intent_name} qidiryapsiz")
                
            # Interests compatibility
            p_interests = set(p.interests.split(",") if p.interests else [])
            u_interests = set(user.interests.split(",") if user.interests else [])
            common_interests = p_interests & u_interests
            if common_interests:
                interests_list = list(common_interests)[:3]
                score += len(common_interests) * 5
                reasons.append("Umumiy qiziqishlar bor: " + ", ".join(interests_list))
                
            # Language compatibility
            if p.language == user.language:
                score += 10
                lang_names = {"uz": "O\'zbek", "ru": "Rus", "en": "Ingliz"}
                lang_name = lang_names.get(p.language, p.language)
                reasons.append(f"Ikkalangiz ham {lang_name} tilida muloqot qilasiz")
                
            score = min(score, 99)
            
            p_dict = serialize_user(p, p_photos)
            p_dict["compatibility_score"] = score
            p_dict["compatibility"] = {
                "score": score,
                "reasons": reasons
            }
            serialized_profiles.append(p_dict)
            
        return web.json_response({"status": "ok", "profiles": serialized_profiles})


async def handle_swipe(request):
    """POST /api/swipe - Layk yoki Nope amali."""
    try:
        tg_user, user = await require_approved_user(request)
    except web.HTTPException as ex:
        raise ex
        
    try:
        data = await request.json()
        target_id = int(data.get("target_id"))
        action = data.get("action")  # "like", "nope", "superlike"
        
        async with async_session_maker() as session:
                
            if action in ["like", "superlike"]:
                # Add Like
                is_super = (action == "superlike")
                like_record = Like(
                    from_user_id=user.id,
                    to_user_id=target_id,
                    is_super_like=is_super
                )
                session.add(like_record)
                
                # Check for Match
                match_stmt = select(Like).where(
                    and_(
                        Like.from_user_id == target_id,
                        Like.to_user_id == user.id
                    )
                )
                match_res = await session.execute(match_stmt)
                mutual_like = match_res.scalar_one_or_none()
                
                if mutual_like:
                    # Check if Match already exists
                    existing_match_stmt = select(Match).where(
                        and_(
                            Match.user1_id == min(user.id, target_id),
                            Match.user2_id == max(user.id, target_id)
                        )
                    )
                    existing_match_res = await session.execute(existing_match_stmt)
                    existing_match = existing_match_res.scalar_one_or_none()
                    
                    target_user = await session.get(User, target_id)
                    
                    if not existing_match:
                        match = Match(
                            user1_id=min(user.id, target_id),
                            user2_id=max(user.id, target_id),
                            is_active=True
                        )
                        session.add(match)
                        
                        # Create Notification in DB
                        n1 = Notification(
                            user_id=user.id,
                            title="Yangi moslik (Match)! 💖",
                            text=f"Tabriklaymiz! Sizda {target_user.name if target_user else 'kimdir'} bilan o\'zaro moslik paydo bo\'ldi. Suhbatni boshlang!",
                            type="match"
                        )
                        n2 = Notification(
                            user_id=target_id,
                            title="Yangi moslik (Match)! 💖",
                            text=f"Tabriklaymiz! Sizda {user.name} bilan o\'zaro moslik paydo bo\'ldi. Suhbatni boshlang!",
                            type="match"
                        )
                        session.add_all([n1, n2])
                        await session.commit()
                        
                        # Send Telegram notifications
                        if target_user and target_user.telegram_id:
                            await send_bot_notification(
                                target_user.telegram_id,
                                f"Tabriklaymiz! Sizda {user.name} bilan o\'zaro moslik (Match) paydo bo\'ldi! 💖\n\nSuhbatni boshlash uchun Kairyx App-ni oching!"
                            )
                        await send_bot_notification(
                            user.telegram_id,
                            f"Tabriklaymiz! Sizda {target_user.name if target_user else 'kimdir'} bilan o\'zaro moslik (Match) paydo bo\'ldi! 💖\n\nSuhbatni boshlash uchun Kairyx App-ni oching!"
                        )
                    
                    return web.json_response({
                        "status": "ok", 
                        "match": True, 
                        "partner_name": target_user.name if target_user else "Kimdir"
                    })
                    
            await session.commit()
            return web.json_response({"status": "ok", "match": False})
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def handle_matches(request):
    """GET /api/matches - Matchlar ro'yxati va oxirgi xabarlar."""
    try:
        tg_user, user = await require_approved_user(request)
    except web.HTTPException as ex:
        raise ex
        
    async with async_session_maker() as session:
            
        m_stmt = select(Match).where(
            and_(
                or_(Match.user1_id == user.id, Match.user2_id == user.id),
                Match.is_active == True
            )
        )
        m_res = await session.execute(m_stmt)
        matches = m_res.scalars().all()
        
        serialized_matches = []
        for m in matches:
            partner_id = m.user2_id if m.user1_id == user.id else m.user1_id
            partner = await session.get(User, partner_id)
            if not partner:
                continue
                
            p_photos_stmt = select(Photo).where(Photo.user_id == partner.id).order_by(Photo.order)
            p_photos_res = await session.execute(p_photos_stmt)
            p_photos = p_photos_res.scalars().all()
            
            # Get last message
            msg_stmt = select(ChatMessage).where(ChatMessage.match_id == m.id).order_by(ChatMessage.created_at.desc()).limit(1)
            msg_res = await session.execute(msg_stmt)
            last_msg = msg_res.scalar_one_or_none()
            
            # Get unread count
            unread_stmt = select(func.count(ChatMessage.id)).where(
                and_(
                    ChatMessage.match_id == m.id,
                    ChatMessage.sender_id != user.id,
                    ChatMessage.is_read == False
                )
            )
            unread_count = await session.scalar(unread_stmt)
            
            serialized_matches.append({
                "id": m.id,
                "partner": serialize_user(partner, p_photos),
                "last_message": last_msg.text if last_msg else "Suhbatni boshlang...",
                "last_message_time": last_msg.created_at.isoformat() if last_msg else None,
                "unread_count": unread_count or 0
            })
            
        return web.json_response({"status": "ok", "matches": serialized_matches})


async def handle_chat_messages(request):
    """GET /api/chat/messages - Chat xabarlari ro'yxati."""
    try:
        tg_user, user = await require_approved_user(request)
    except web.HTTPException as ex:
        raise ex
        
    match_id = int(request.query.get("match_id", 0))
    async with async_session_maker() as session:
            
        match = await session.get(Match, match_id)
        if not match or (match.user1_id != user.id and match.user2_id != user.id):
            return web.json_response({"status": "error", "message": "Access denied"}, status=403)
            
        # Mark messages as read
        from sqlalchemy import update
        await session.execute(
            update(ChatMessage)
            .where(
                and_(
                    ChatMessage.match_id == match_id,
                    ChatMessage.sender_id != user.id,
                    ChatMessage.is_read == False
                )
            )
            .values(is_read=True)
        )
        await session.commit()
            
        msg_stmt = select(ChatMessage).where(ChatMessage.match_id == match_id).order_by(ChatMessage.created_at.asc())
        msg_res = await session.execute(msg_stmt)
        messages = msg_res.scalars().all()
        
        serialized_messages = [{
            "id": msg.id,
            "sender_id": msg.sender_id,
            "text": msg.text,
            "is_my_message": msg.sender_id == user.id,
            "created_at": msg.created_at.isoformat()
        } for msg in messages]
        
        # Check typing status
        import time
        is_partner_typing = False
        typing_state = TYPING_STATES.get(match_id)
        if typing_state:
            partner_id = match.user2_id if match.user1_id == user.id else match.user1_id
            if typing_state["user_id"] == partner_id and time.time() - typing_state["timestamp"] < 4:
                is_partner_typing = True
        
        return web.json_response({
            "status": "ok", 
            "messages": serialized_messages,
            "partner_typing": is_partner_typing
        })


async def handle_chat_send(request):
    """POST /api/chat/send - Xabar yuborish."""
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({"status": "error", "message": "Unauthorized"}, status=401)
        
    try:
        data = await request.json()
        match_id = int(data.get("match_id"))
        text = data.get("text")
        
        async with async_session_maker() as session:
            stmt = select(User).where(User.telegram_id == tg_user["id"])
            res = await session.execute(stmt)
            user = res.scalar_one_or_none()
            
            if not user:
                return web.json_response({"status": "error", "message": "User not found"}, status=404)
                
            match = await session.get(Match, match_id)
            if not match or (match.user1_id != user.id and match.user2_id != user.id):
                return web.json_response({"status": "error", "message": "Access denied"}, status=403)
                
            message = ChatMessage(
                match_id=match_id,
                sender_id=user.id,
                text=text,
                is_read=False
            )
            session.add(message)
            await session.commit()
            
            return web.json_response({
                "status": "ok", 
                "message": {
                    "id": message.id,
                    "sender_id": message.sender_id,
                    "text": message.text,
                    "is_my_message": True,
                    "created_at": message.created_at.isoformat()
                }
            })
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def handle_referrals(request):
    """GET /api/referrals - Referrallar ro'yxati."""
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({"status": "error", "message": "Unauthorized"}, status=401)
        
    async with async_session_maker() as session:
        stmt = select(User).where(User.telegram_id == tg_user["id"])
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()
        
        if not user:
            return web.json_response({"status": "error", "message": "User not found"}, status=404)
            
        ref_stmt = select(User).where(User.referred_by_id == user.id)
        ref_res = await session.execute(ref_stmt)
        referrals = ref_res.scalars().all()
        
        return web.json_response({
            "status": "ok",
            "count": len(referrals),
            "bonus_points": len(referrals) * 1000,
            "referrals": [serialize_user(r) for r in referrals]
        })


async def handle_buy_premium(request):
    """POST /api/premium/buy - Premium reja sotib olish (to'lov yaratish)."""
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({"status": "error", "message": "Unauthorized"}, status=401)
        
    try:
        data = await request.json()
        plan = data.get("plan")
        amount = 49900.0 if plan == "gold" else 89900.0
        receipt = data.get("receipt", "")
        
        async with async_session_maker() as session:
            stmt = select(User).where(User.telegram_id == tg_user["id"])
            res = await session.execute(stmt)
            user = res.scalar_one_or_none()
            
            if not user:
                return web.json_response({"status": "error", "message": "User not found"}, status=404)
                
            payment = Payment(
                user_id=user.id,
                amount=amount,
                description=f"Premium {plan.capitalize()} Obunasi",
                payment_system="Telegram WebApp Payment",
                transaction_id=receipt or f"TX_{user.id}_{int(datetime.now().timestamp())}",
                status="pending"
            )
            session.add(payment)
            await session.commit()
            
            return web.json_response({
                "status": "ok", 
                "message": "To'lov cheki yuborildi. Admin tasdiqlagach faollashadi.",
                "payment_id": payment.id
            })
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500)


# ==========================================
# ADMIN ENDPOINTS (Faqat adminlar uchun)
# ==========================================

async def check_admin_access(request, session) -> bool:
    """Admin huquqini tekshiradi (7992878834 yoki ADMIN_IDS)."""
    tg_user = get_telegram_user(request)
    if not tg_user:
        return False
        
    allowed_ids = [7992878834] + list(ADMIN_IDS)
    if tg_user["id"] in allowed_ids:
        return True
        
    # Check is_admin field in db
    stmt = select(User).where(User.telegram_id == tg_user["id"])
    res = await session.execute(stmt)
    user = res.scalar_one_or_none()
    return user is not None and (user.is_admin or user.telegram_id in allowed_ids)




# ===== TYPING STATE DICTIONARY & APIS =====
import time
TYPING_STATES = {}

async def handle_chat_typing(request):
    """POST /api/chat/typing - User typing state notification."""
    try:
        tg_user, user = await require_approved_user(request)
    except web.HTTPException as ex:
        raise ex
    
    try:
        data = await request.json()
        match_id = int(data.get("match_id"))
        
        TYPING_STATES[match_id] = {
            "user_id": user.id,
            "timestamp": time.time()
        }
        return web.json_response({"status": "ok"})
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def handle_chat_icebreaker(request):
    """GET /api/chat/icebreaker - Generate 3 suhbat boshlash taklifi based on mutual interests."""
    try:
        tg_user, user = await require_approved_user(request)
    except web.HTTPException as ex:
        raise ex
        
    match_id = int(request.query.get("match_id", 0))
    async with async_session_maker() as session:
        match = await session.get(Match, match_id)
        if not match or (match.user1_id != user.id and match.user2_id != user.id):
            return web.json_response({"status": "error", "message": "Access denied"}, status=403)
            
        partner_id = match.user2_id if match.user1_id == user.id else match.user1_id
        partner = await session.get(User, partner_id)
        
        # Find common interests
        p_interests = set(partner.interests.split(",") if partner.interests else [])
        u_interests = set(user.interests.split(",") if user.interests else [])
        common = list(p_interests & u_interests)
        
        # Fallbacks
        icebreakers = [
            "Salom! Profilingiz juda qiziqarli ko'rindi. Nimalar bilan bandsiz?",
            "Salom! Tanishganimdan xursandman. Bugungi kuningiz qanday o'tmoqda?",
            "Salom! Ikkalamizda ham qiziqarli moslik chiqdi. Keling, yaqinroq tanishamiz!"
        ]
        
        # If there are common interests, customize
        if common:
            interest = common[0].strip()
            icebreakers = [
                f"Salom! Ikkalamiz ham \'{interest}\'ga qiziqar ekanmiz. Qachondan beri shug\'ullanasiz?",
                f"Salom! Mosligimiz uchun tabriklayman. Profilingizda \'{interest}\'ni ko\'rdim, men ham shuni yaxshi ko\'raman!",
                f"Salom! Suhbatimizni nimadan boshlasak ekan? \'{interest}\' haqida gaplashamizlarmi? 😊"
            ]
            
        return web.json_response({"status": "ok", "icebreakers": icebreakers})




async def handle_user_block(request):
    """POST /api/user/block - Foydalanuvchini bloklash."""
    try:
        tg_user, user = await require_approved_user(request)
    except web.HTTPException as ex:
        raise ex
        
    try:
        data = await request.json()
        blocked_id = int(data.get("blocked_id"))
        
        async with async_session_maker() as session:
            # Check if block record already exists
            stmt = select(BlockedUser).where(
                and_(BlockedUser.blocker_id == user.id, BlockedUser.blocked_id == blocked_id)
            )
            res = await session.execute(stmt)
            existing = res.scalar_one_or_none()
            
            if not existing:
                block_record = BlockedUser(
                    blocker_id=user.id,
                    blocked_id=blocked_id
                )
                session.add(block_record)
            
            # Delete any active matches between these two users
            match_stmt = select(Match).where(
                or_(
                    and_(Match.user1_id == user.id, Match.user2_id == blocked_id),
                    and_(Match.user1_id == blocked_id, Match.user2_id == user.id)
                )
            )
            match_res = await session.execute(match_stmt)
            match = match_res.scalar_one_or_none()
            if match:
                await session.delete(match)
                
            await session.commit()
            return web.json_response({"status": "ok"})
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def handle_user_report(request):
    """POST /api/user/report - Foydalanuvchi ustidan shikoyat yuborish."""
    try:
        tg_user, user = await require_approved_user(request)
    except web.HTTPException as ex:
        raise ex
        
    try:
        data = await request.json()
        reported_id = int(data.get("reported_id"))
        category_str = data.get("category", "other")
        desc = data.get("description", "").strip()
        
        from models import Report, ReportCategory
        try:
            category = ReportCategory[category_str]
        except KeyError:
            category = ReportCategory.other
            
        async with async_session_maker() as session:
            report_record = Report(
                reporter_id=user.id,
                reported_id=reported_id,
                category=category,
                description=desc
            )
            session.add(report_record)
            await session.commit()
            return web.json_response({"status": "ok"})
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500)




async def handle_notifications(request):
    """GET /api/notifications - Foydalanuvchi bildirishnomalari ro'yxati."""
    try:
        tg_user, user = await require_approved_user(request)
    except web.HTTPException as ex:
        raise ex
        
    async with async_session_maker() as session:
        stmt = select(Notification).where(Notification.user_id == user.id).order_by(Notification.created_at.desc()).limit(50)
        res = await session.execute(stmt)
        notifications = res.scalars().all()
        
        unread_stmt = select(func.count(Notification.id)).where(
            and_(Notification.user_id == user.id, Notification.is_read == False)
        )
        unread_count = await session.scalar(unread_stmt)
        
        serialized = [{
            "id": n.id,
            "title": n.title,
            "text": n.text,
            "type": n.type,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat()
        } for n in notifications]
        
        return web.json_response({
            "status": "ok",
            "notifications": serialized,
            "unread_count": unread_count or 0
        })


async def handle_notifications_read(request):
    """POST /api/notifications/read - Barcha bildirishnomalarni o'qilgan deb belgilash."""
    try:
        tg_user, user = await require_approved_user(request)
    except web.HTTPException as ex:
        raise ex
        
    async with async_session_maker() as session:
        from sqlalchemy import update
        await session.execute(
            update(Notification)
            .where(and_(Notification.user_id == user.id, Notification.is_read == False))
            .values(is_read=True)
        )
        await session.commit()
        return web.json_response({"status": "ok"})




async def send_bot_notification(telegram_id: int, message_text: str):
    """Safar bot orqali foydalanuvchiga xabar yuborish."""
    from aiogram import Bot
    from config import BOT_TOKEN
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        return
    try:
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(chat_id=telegram_id, text=message_text)
        await bot.session.close()
    except Exception as e:
        import logging
        logging.warning(f"Error sending bot notification to {telegram_id}: {e}")




async def handle_upload_photo_general(request):
    """POST /api/upload-photo - Upload base64 image and return public URL (accessible during registration)."""
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({"status": "error", "message": "Unauthorized"}, status=401)
        
    try:
        data = await request.json()
        base64_data = data.get("image")
        if not base64_data:
            return web.json_response({"status": "error", "message": "No image data"}, status=400)
            
        if "," in base64_data:
            base64_data = base64_data.split(",")[1]
            
        image_bytes = base64.b64decode(base64_data)
        
        webapp_dir = os.path.dirname(os.path.abspath(__file__))
        uploads_dir = os.path.join(webapp_dir, "static", "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        
        filename = f"{uuid.uuid4()}.jpg"
        filepath = os.path.join(uploads_dir, filename)
        
        with open(filepath, "wb") as f:
            f.write(image_bytes)
            
        file_url = f"/static/uploads/{filename}"
        return web.json_response({"status": "ok", "url": file_url})
    except Exception as e:
        logger.error(f"Image upload error: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def require_approved_user(request) -> tuple:
    """Foydalanuvchini tekshiradi va faqat APPROVED (active) user uchun ruxsat beradi.
    Returns (tg_user, db_user) or raises web.HTTPForbidden."""
    tg_user = get_telegram_user(request)
    if not tg_user:
        raise web.HTTPUnauthorized(text='{"status":"error","message":"Unauthorized"}', content_type='application/json')
    
    async with async_session_maker() as session:
        stmt = select(User).where(User.telegram_id == tg_user["id"])
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user or user.status != UserStatus.active:
            user_status = user.status.name if user and user.status else "draft"
            raise web.HTTPForbidden(
                text=json.dumps({"status": "error", "message": "Access denied", "user_status": user_status}),
                content_type='application/json'
            )
        return tg_user, user


async def handle_admin_approve(request):
    """POST /api/admin/user/approve - Foydalanuvchini tasdiqlash."""
    try:
        data = await request.json()
        target_id = int(data.get("user_id"))
        
        async with async_session_maker() as session:
            if not await check_admin_access(request, session):
                return web.json_response({"status": "error", "message": "Access denied"}, status=403)
        
        from crud import approve_user_profile
        user = await approve_user_profile(target_id, get_telegram_user(request)["id"])
        if user:
            return web.json_response({"status": "ok", "message": "User approved", "user": serialize_user(user)})
        else:
            return web.json_response({"status": "error", "message": "User not found or not pending"}, status=400)
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def handle_admin_reject(request):
    """POST /api/admin/user/reject - Foydalanuvchini rad etish."""
    try:
        data = await request.json()
        target_id = int(data.get("user_id"))
        reason = data.get("reason", "").strip()
        
        if not reason:
            return web.json_response({"status": "error", "message": "Reason is required"}, status=400)
        
        async with async_session_maker() as session:
            if not await check_admin_access(request, session):
                return web.json_response({"status": "error", "message": "Access denied"}, status=403)
        
        from crud import reject_user_profile
        user = await reject_user_profile(target_id, get_telegram_user(request)["id"], reason)
        if user:
            return web.json_response({"status": "ok", "message": "User rejected", "user": serialize_user(user)})
        else:
            return web.json_response({"status": "error", "message": "User not found or not pending"}, status=400)
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def handle_admin_pending_users(request):
    """GET /api/admin/pending-users - Tasdiqlash kutayotgan foydalanuvchilar."""
    async with async_session_maker() as session:
        if not await check_admin_access(request, session):
            return web.json_response({"status": "error", "message": "Access denied"}, status=403)
    
    from crud import get_pending_users
    users = await get_pending_users()
    
    # Serialize with photos
    result = []
    for u in users:
        async with async_session_maker() as session:
            p_stmt = select(Photo).where(Photo.user_id == u.id).order_by(Photo.order)
            p_res = await session.execute(p_stmt)
            photos = p_res.scalars().all()
        result.append(serialize_user(u, photos))
    
    return web.json_response({"status": "ok", "users": result})


async def handle_registration_resubmit(request):
    """POST /api/registration/resubmit - Rad etilgan user profilni qayta yuborishi."""
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({"status": "error", "message": "Unauthorized"}, status=401)
    
    try:
        data = await request.json()
        async with async_session_maker() as session:
            stmt = select(User).where(User.telegram_id == tg_user["id"])
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user or user.status != UserStatus.rejected:
                return web.json_response({"status": "error", "message": "Not in rejected state"}, status=400)
        
        from crud import resubmit_registration
        updated = await resubmit_registration(user.id, data)
        if updated:
            return web.json_response({"status": "ok", "user_status": "pending_approval"})
        else:
            return web.json_response({"status": "error", "message": "Resubmit failed"}, status=500)
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def handle_admin_stats(request):
    """GET /api/admin/stats - Admin panel statistikasi."""
    async with async_session_maker() as session:
        if not await check_admin_access(request, session):
            return web.json_response({"status": "error", "message": "Access denied"}, status=403)
            
        # Jami foydalanuvchilar (draft va deleted siz)
        total_users = await session.scalar(
            select(func.count(User.id)).where(
                User.status.notin_([UserStatus.draft, UserStatus.deleted])
            )
        )
        approved_users = await session.scalar(
            select(func.count(User.id)).where(User.status == UserStatus.active)
        )
        pending_approval = await session.scalar(
            select(func.count(User.id)).where(User.status == UserStatus.pending_approval)
        )
        rejected_users = await session.scalar(
            select(func.count(User.id)).where(User.status == UserStatus.rejected)
        )
        banned_users = await session.scalar(
            select(func.count(User.id)).where(User.status == UserStatus.banned)
        )
        
        from sqlalchemy import Date, cast
        today = datetime.now().date()
        reg_today = await session.scalar(
            select(func.count(User.id)).where(cast(User.registered_at, Date) == today)
        )
        
        from models import PremiumPlan
        premium_users = await session.scalar(
            select(func.count(User.id)).where(
                and_(
                    User.premium_plan != PremiumPlan.basic,
                    User.premium_expires_at > datetime.now()
                )
            )
        )
        
        total_matches = await session.scalar(select(func.count(Match.id)))
        
        return web.json_response({
            "status": "ok",
            "stats": {
                "totalUsers": total_users or 0,
                "approvedUsers": approved_users or 0,
                "pendingApproval": pending_approval or 0,
                "rejectedUsers": rejected_users or 0,
                "activeUsers": approved_users or 0,
                "joinedToday": reg_today or 0,
                "premiumUsers": premium_users or 0
            }
        })


async def handle_admin_users(request):
    """GET /api/admin/users - Foydalanuvchilar ro'yxati (qidiruv bilan)."""
    search_query = request.query.get("search", "")
    async with async_session_maker() as session:
        if not await check_admin_access(request, session):
            return web.json_response({"status": "error", "message": "Access denied"}, status=403)
            
        q = select(User)
        if search_query:
            if search_query.isdigit():
                q = q.where(or_(User.id == int(search_query), User.telegram_id == int(search_query)))
            else:
                q = q.where(User.name.ilike(f"%{search_query}%"))
                
        q = q.limit(50)
        res = await session.execute(q)
        users = res.scalars().all()
        
        return web.json_response({
            "status": "ok",
            "users": [serialize_user(u) for u in users]
        })


async def handle_admin_user_action(request):
    """POST /api/admin/user/action - Foydalanuvchini bloklash yoki o'chirish."""
    try:
        data = await request.json()
        target_id = int(data.get("user_id"))
        action = data.get("action")  # "ban", "unban", "delete"
        
        async with async_session_maker() as session:
            if not await check_admin_access(request, session):
                return web.json_response({"status": "error", "message": "Access denied"}, status=403)
                
            user = await session.get(User, target_id)
            if not user:
                return web.json_response({"status": "error", "message": "User not found"}, status=404)
                
            if action == "ban":
                user.status = UserStatus.banned
                user.banned_until = datetime.now() + timedelta(days=365) # Permanent-ish
            elif action == "unban":
                user.status = UserStatus.active
                user.banned_until = None
            elif action == "delete":
                # Delete user photos, likes, matches, messages and then user
                await session.execute(delete(Photo).where(Photo.user_id == target_id))
                await session.execute(delete(Like).where(or_(Like.from_user_id == target_id, Like.to_user_id == target_id)))
                await session.execute(delete(Match).where(or_(Match.user1_id == target_id, Match.user2_id == target_id)))
                await session.execute(delete(User).where(User.id == target_id))
                
            await session.commit()
            return web.json_response({"status": "ok", "message": f"Action {action} completed successfully"})
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def handle_admin_payments(request):
    """GET /api/admin/payments - Kutilayotgan to'lovlar."""
    async with async_session_maker() as session:
        if not await check_admin_access(request, session):
            return web.json_response({"status": "error", "message": "Access denied"}, status=403)
            
        stmt = select(Payment).where(Payment.status == "pending").order_by(Payment.created_at.desc())
        res = await session.execute(stmt)
        payments = res.scalars().all()
        
        serialized_payments = []
        for p in payments:
            user = await session.get(User, p.user_id)
            serialized_payments.append({
                "id": p.id,
                "amount": p.amount,
                "description": p.description,
                "created_at": p.created_at.isoformat(),
                "receipt": p.transaction_id,
                "user": serialize_user(user) if user else None
            })
            
        return web.json_response({"status": "ok", "payments": serialized_payments})


async def handle_admin_payment_action(request):
    """POST /api/admin/payment/action - To'lovni tasdiqlash yoki rad etish."""
    try:
        data = await request.json()
        payment_id = int(data.get("payment_id"))
        action = data.get("action")  # "approve", "reject"
        
        async with async_session_maker() as session:
            if not await check_admin_access(request, session):
                return web.json_response({"status": "error", "message": "Access denied"}, status=403)
                
            payment = await session.get(Payment, payment_id)
            if not payment:
                return web.json_response({"status": "error", "message": "Payment not found"}, status=404)
                
            if action == "approve":
                payment.status = "completed"
                # Upgrade user to premium
                user = await session.get(User, payment.user_id)
                if user:
                    user.premium_plan = PremiumPlan.gold if "Gold" in (payment.description or "") else PremiumPlan.platinum
                    user.premium_expires_at = datetime.now() + timedelta(days=30)
                    user.is_premium = True
            else:
                payment.status = "failed"
                
            await session.commit()
            return web.json_response({"status": "ok", "message": f"Payment {action}d successfully"})
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def handle_admin_broadcast(request):
    """POST /api/admin/broadcast - Barcha faol foydalanuvchilarga xabar yuborish."""
    try:
        data = await request.json()
        text_message = data.get("message")
        
        async with async_session_maker() as session:
            if not await check_admin_access(request, session):
                return web.json_response({"status": "error", "message": "Access denied"}, status=403)
                
            # Get all active user telegram ids
            stmt = select(User.telegram_id).where(User.status == UserStatus.active)
            res = await session.execute(stmt)
            telegram_ids = res.scalars().all()
            
            # Send broadcast message via bot API
            # Since bot is initialized globally or dynamically, we import Bot
            from aiogram import Bot
            bot = Bot(token=BOT_TOKEN)
            
            sent_count = 0
            for tid in telegram_ids:
                try:
                    await bot.send_message(chat_id=tid, text=text_message)
                    sent_count += 1
                except Exception:
                    pass
            
            await bot.session.close()
            return web.json_response({"status": "ok", "message": f"Message sent to {sent_count} users"})
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500)




import base64
import uuid

async def handle_upload_photo(request):
    """POST /api/profile/upload-photo - Base64 rasm yuklash."""
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({"status": "error", "message": "Unauthorized"}, status=401)
        
    try:
        data = await request.json()
        base64_data = data.get("image")
        if not base64_data:
            return web.json_response({"status": "error", "message": "No image data"}, status=400)
            
        if "," in base64_data:
            base64_data = base64_data.split(",")[1]
            
        image_bytes = base64.b64decode(base64_data)
        
        webapp_dir = os.path.dirname(os.path.abspath(__file__))
        uploads_dir = os.path.join(webapp_dir, "static", "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        
        filename = f"{uuid.uuid4()}.jpg"
        filepath = os.path.join(uploads_dir, filename)
        
        with open(filepath, "wb") as f:
            f.write(image_bytes)
            
        file_url = f"/static/uploads/{filename}"
        
        async with async_session_maker() as session:
            stmt = select(User).where(User.telegram_id == tg_user["id"])
            res = await session.execute(stmt)
            user = res.scalar_one_or_none()
            
            if not user:
                return web.json_response({"status": "error", "message": "User not found"}, status=404)
                
            photo = Photo(user_id=user.id, file_id=file_url)
            session.add(photo)
            await session.commit()
            
            return web.json_response({
                "status": "ok",
                "photo_url": file_url
            })
    except Exception as e:
        logger.error(f"Upload photo error: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def handle_delete_profile(request):
    """POST /api/profile/delete - Hisobni o'chirish."""
    tg_user = get_telegram_user(request)
    if not tg_user:
        return web.json_response({"status": "error", "message": "Unauthorized"}, status=401)
        
    try:
        async with async_session_maker() as session:
            stmt = select(User).where(User.telegram_id == tg_user["id"])
            res = await session.execute(stmt)
            user = res.scalar_one_or_none()
            
            if not user:
                return web.json_response({"status": "error", "message": "User not found"}, status=404)
                
            await session.execute(delete(Photo).where(Photo.user_id == user.id))
            await session.execute(delete(Like).where(or_(Like.user_id == user.id, Like.target_id == user.id)))
            await session.execute(delete(Match).where(or_(Match.user1_id == user.id, Match.user2_id == user.id)))
            await session.execute(delete(Payment).where(Payment.user_id == user.id))
            await session.delete(user)
            await session.commit()
            
            return web.json_response({"status": "ok"})
    except Exception as e:
        logger.error(f"Delete profile error: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def handle_get_photo(request):
    """GET /api/photo/{file_id} - Telegram file_id-ni raster rasmga aylantiradi."""
    file_id = request.match_info.get("file_id")
    if not file_id:
        return web.Response(status=400)

    if file_id.startswith("http"):
        raise web.HTTPFound(file_id)

    try:
        from aiogram import Bot
        bot = Bot(token=BOT_TOKEN)
        file_info = await bot.get_file(file_id)
        file_path = file_info.file_path
        url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
        await bot.session.close()
        raise web.HTTPFound(url)
    except web.HTTPFound as redirect:
        raise redirect
    except Exception as e:
        logger.warning(f"Error serving file {file_id}: {e}")
        # Default fallback placeholder
        raise web.HTTPFound("https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=600&q=80")


async def handle_index(request):
    """GET / - Mini App HTML faylini yuklaydi."""
    import os
    webapp_dir = os.path.dirname(os.path.abspath(__file__))
    return web.FileResponse(os.path.join(webapp_dir, "index.html"))



async def serve_style(request):
    import os
    webapp_dir = os.path.dirname(os.path.abspath(__file__))
    return web.FileResponse(os.path.join(webapp_dir, "style.css"))


async def serve_app(request):
    import os
    webapp_dir = os.path.dirname(os.path.abspath(__file__))
    return web.FileResponse(os.path.join(webapp_dir, "app.js"))


def create_webapp_app() -> web.Application:
    """Mini App aiohttp ilovasini yaratadi."""
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

    # Routes
    app.router.add_get("/", handle_index)
    app.router.add_get("/api/photo/{file_id}", handle_get_photo)
    app.router.add_get("/api/init", handle_init)
    app.router.add_post("/api/register", handle_register)
    app.router.add_get("/api/profile", handle_profile)
    app.router.add_post("/api/profile/update", handle_profile_update)
    app.router.add_post("/api/profile/upload-photo", handle_upload_photo)
    app.router.add_post("/api/profile/delete", handle_delete_profile)
    app.router.add_get("/api/profiles", handle_profiles)
    app.router.add_post("/api/swipe", handle_swipe)
    app.router.add_get("/api/matches", handle_matches)
    app.router.add_get("/api/chat/messages", handle_chat_messages)
    app.router.add_post("/api/chat/send", handle_chat_send)
    app.router.add_get("/api/referrals", handle_referrals)
    app.router.add_post("/api/premium/buy", handle_buy_premium)
    
    # Admin API
    app.router.add_get("/api/admin/stats", handle_admin_stats)
    app.router.add_get("/api/admin/users", handle_admin_users)
    app.router.add_post("/api/admin/user/action", handle_admin_user_action)
    app.router.add_get("/api/admin/payments", handle_admin_payments)
    app.router.add_post("/api/admin/payment/action", handle_admin_payment_action)
    app.router.add_post("/api/admin/broadcast", handle_admin_broadcast)
    app.router.add_post("/api/admin/user/approve", handle_admin_approve)
    app.router.add_post("/api/admin/user/reject", handle_admin_reject)
    app.router.add_get("/api/admin/pending-users", handle_admin_pending_users)
    app.router.add_post("/api/registration/resubmit", handle_registration_resubmit)
    app.router.add_post("/api/chat/typing", handle_chat_typing)
    app.router.add_get("/api/chat/icebreaker", handle_chat_icebreaker)
    app.router.add_post("/api/user/block", handle_user_block)
    app.router.add_post("/api/user/report", handle_user_report)
    app.router.add_post("/api/upload-photo", handle_upload_photo_general)
    app.router.add_get("/api/notifications", handle_notifications)
    app.router.add_post("/api/notifications/read", handle_notifications_read)

    # Static assets
    import os
    webapp_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(os.path.join(webapp_dir, "static"), exist_ok=True)
    app.router.add_static("/static", os.path.join(webapp_dir, "static"), show_index=True)
    # Map static CSS/JS directly
    app.router.add_get("/style.css", serve_style)
    app.router.add_get("/app.js", serve_app)

    return app


if __name__ == "__main__":
    app = create_webapp_app()
    web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
