from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, exists, func, delete, cast, Date, case
from sqlalchemy import select, text, update
from sqlalchemy.orm import selectinload
from models import (
    User,
    Photo,
    UserGender,
    LookingForGender,
    Like,
    Match,
    ChatMessage,
    UserStatus,
    Report,
    ReportStatus,
    ReportCategory,
    Subscription,
    AdminLog,
    ActionType,
    VerificationRequest,
    VerificationStatus,
    PremiumPlan,
    BlockedUser, # Import BlockedUser
    Payment,
    SupportMessage,
    Gift, # Import Gift
    GiftType, # Import GiftType
    ProfileView, # Import ProfileView
    UserEvent,
    EventType,
)
from engine import async_session_maker
from config import ADMIN_IDS


# Premium tier daily quotas. None means unlimited.
DAILY_LIKE_LIMITS = {
    PremiumPlan.basic: 20,
    PremiumPlan.gold: 100,
    PremiumPlan.platinum: None,
}
DAILY_SUPER_LIKE_LIMITS = {
    PremiumPlan.basic: 0,
    PremiumPlan.gold: 3,
    PremiumPlan.platinum: 10,
}
BOOST_DURATION_MINUTES = 30


async def check_and_consume_like_quota(user_id: int, is_super_like: bool = False) -> tuple[bool, int | None]:
    """
    Checks the user's daily like/super-like quota, resetting it if a new day has started,
    and consumes one unit if allowed. Returns (allowed, remaining) where remaining is None
    when the plan has an unlimited quota.
    """
    try:
        async with async_session_maker() as session:
            user = await session.get(User, user_id)
            if not user:
                return False, 0

            now = datetime.now()
            if not user.daily_quota_reset_at or user.daily_quota_reset_at.date() < now.date():
                user.daily_likes_used = 0
                user.daily_super_likes_used = 0
                user.daily_quota_reset_at = now

            plan = user.premium_plan or PremiumPlan.basic
            if is_super_like:
                limit = DAILY_SUPER_LIKE_LIMITS.get(plan, 0)
                used = user.daily_super_likes_used
            else:
                limit = DAILY_LIKE_LIMITS.get(plan)
                used = user.daily_likes_used

            if limit is not None and used >= limit:
                await session.commit()
                return False, 0

            if is_super_like:
                user.daily_super_likes_used += 1
                remaining = None if limit is None else limit - user.daily_super_likes_used
            else:
                user.daily_likes_used += 1
                remaining = None if limit is None else limit - user.daily_likes_used

            await session.commit()
            return True, remaining
    except Exception as exc:
        import logging
        logging.warning(f"Database unavailable while checking like quota: {exc}")
        return True, None


async def activate_profile_boost(user_id: int) -> datetime | None:
    """Activates a temporary profile boost for premium users. Returns the expiry timestamp."""
    try:
        async with async_session_maker() as session:
            user = await session.get(User, user_id)
            if not user:
                return None

            expires_at = datetime.now() + timedelta(minutes=BOOST_DURATION_MINUTES)
            user.boost_active_until = expires_at
            await session.commit()
            return expires_at
    except Exception as exc:
        import logging
        logging.warning(f"Database unavailable while activating boost: {exc}")
        return None


async def create_user_profile(telegram_id: int, user_data: dict) -> User | None:
    """
    Foydalanuvchi ma'lumotlarini va rasmlarini ma'lumotlar bazasiga saqlaydi.
    Shu telegram_id uchun profil allaqachon mavjud bo'lsa (masalan, foydalanuvchi
    avval ro'yxatdan o'tgani aniqlanmay qayta ro'yxatdan o'tgan bo'lsa), xatolik
    chiqarish o'rniga mavjud yozuvni yangilaydi - profil hech qachon yo'qolmaydi
    yoki takroriy telegram_id sababli yaratilish xatoligiga uchramaydi.
    """
    try:
        async with async_session_maker() as session:
            result = await session.execute(select(User).where(User.telegram_id == telegram_id))
            target_user = result.scalar_one_or_none()
            # Toshkent shahri tanlanganda alohida shahar bosqichi bo'lmagani uchun region qiymati zaxira bo'ladi.
            city = user_data.get("city") or user_data.get("region")

            if target_user:
                target_user.name = user_data.get("name")
                target_user.age = user_data.get("age")
                target_user.gender = UserGender[user_data["gender"]]
                target_user.looking_for = LookingForGender[user_data["looking_for"]]
                target_user.city = city
                target_user.district = user_data.get("district")
                target_user.bio = user_data.get("bio")
                target_user.interests = ",".join(user_data.get("interests", []))
                target_user.language = user_data.get("language")
                target_user.status = UserStatus.active
                target_user.profile_approval_status = "pending"
                # Eski rasmlar o'rniga yangi yuklangan rasmlar saqlanadi.
                await session.execute(delete(Photo).where(Photo.user_id == target_user.id))
            else:
                target_user = User(
                    telegram_id=telegram_id,
                    name=user_data.get("name"),
                    age=user_data.get("age"),
                    gender=UserGender[user_data["gender"]],  # Enumga o'tkazish
                    looking_for=LookingForGender[user_data["looking_for"]],  # Enumga o'tkazish
                    city=city,
                    district=user_data.get("district"),
                    bio=user_data.get("bio"),
                    interests=",".join(user_data.get("interests", [])),
                    language=user_data.get("language"),
                    # Yangi profil har doim admin tasdig'ini kutadi.
                    profile_approval_status="pending",
                    # Boshqa maydonlar default qiymatlar bilan to'ldiriladi
                )
                session.add(target_user)

            await session.flush()  # target_user.id ni olish uchun

            # Rasmlarni saqlash
            photos = user_data.get("photos", [])
            for i, file_id in enumerate(photos):
                new_photo = Photo(
                    user_id=target_user.id,
                    file_id=file_id,
                    order=i + 1,
                    is_approved=False,  # Moderatsiya uchun dastlab tasdiqlanmagan
                )
                session.add(new_photo)

            await session.commit()
            await session.refresh(target_user)

            return target_user
    except Exception as exc:
        import logging
        logging.warning(f"Database unavailable while creating user profile: {exc}")
        return None


async def get_user_by_telegram_id(telegram_id: int) -> User | None:
    """Foydalanuvchini telegram ID orqali topadi."""
    try:
        async with async_session_maker() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            return result.scalar_one_or_none()
    except Exception as exc:
        import logging
        logging.warning(f"Database unavailable while fetching user: {exc}")
        return None


async def get_user_photos(user_id: int) -> list[Photo]:
    """Foydalanuvchining rasmlarini user_id orqali topadi."""
    try:
        async with async_session_maker() as session:
            result = await session.execute(
                select(Photo).where(Photo.user_id == user_id).order_by(Photo.order)
            )
            return result.scalars().all()
    except Exception as exc:
        import logging
        logging.warning(f"Database unavailable while fetching user photos: {exc}")
        return []


async def get_user_matches(user_id: int) -> list[Match]:
    """
    Fetches all active matches for a user.
    """
    try:
        async with async_session_maker() as session:
            result = await session.execute(
                select(Match).where(
                    or_(Match.user1_id == user_id, Match.user2_id == user_id),
                    Match.is_active == True
                ).order_by(Match.created_at.desc())
            )
            return result.scalars().all()
    except Exception as exc:
        import logging
        logging.warning(f"Database unavailable while fetching matches: {exc}")
        return []


async def unmatch_users(user1_id: int, user2_id: int) -> bool:
    """Deactivates a match between two users. Returns True if a match was deactivated, False otherwise."""
    async with async_session_maker() as session:
        # Find the match, ignoring which user is user1 or user2
        match_query = select(Match).where(
            or_(
                and_(Match.user1_id == user1_id, Match.user2_id == user2_id),
                and_(Match.user1_id == user2_id, Match.user2_id == user1_id)
            ),
            Match.is_active == True
        )
        result = await session.execute(match_query)
        match = result.scalar_one_or_none()

        if not match:
            return False

        match.is_active = False
        await session.commit()
        return True


async def get_user_by_id(user_id: int) -> User | None:
    """Finds a user by their primary key ID."""
    try:
        async with async_session_maker() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            return result.scalar_one_or_none()
    except Exception as exc:
        import logging
        logging.warning(f"Database unavailable while fetching user by id: {exc}")
        return None


async def update_last_seen(user_id: int):
    """Updates the user's last_activity timestamp to the current time."""
    async with async_session_maker() as session:
        await session.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_activity=datetime.now())
        )
        await session.commit()


async def get_online_status(user: User) -> str:
    """
    Returns a user-friendly string for the user's online status.
    'online', 'recently', or the date they were last active.
    """
    if not user.last_activity:
        return "never"  # Or some other default

    now = datetime.now()
    if user.last_activity > now - timedelta(minutes=5):
        return "online"
    elif user.last_activity > now - timedelta(hours=1):
        return "recently"
    else:
        return user.last_activity.strftime("%Y-%m-%d")


async def get_match_by_id(match_id: int) -> Match | None:
    """Finds a match by its primary key ID."""
    try:
        async with async_session_maker() as session:
            result = await session.execute(select(Match).where(Match.id == match_id))
            return result.scalar_one_or_none()
    except Exception as exc:
        import logging
        logging.warning(f"Database unavailable while fetching match: {exc}")
        return None


async def get_profiles_for_user(current_user: User, limit: int = 20) -> list[User]:
    """
    Fetches a list of suitable profiles for a given user.
    """
    async with async_session_maker() as session:
        # Get users that the current user has already liked
        liked_user_ids_query = select(Like.to_user_id).where(
            Like.from_user_id == current_user.id
        )
        liked_user_ids_result = await session.execute(liked_user_ids_query)
        seen_user_ids = liked_user_ids_result.scalars().all()
        
        # Get users that the current user has blocked or has been blocked by
        blocked_user_ids_query = select(BlockedUser.blocked_id).where(
            BlockedUser.blocker_id == current_user.id
        )
        blocked_by_user_ids_result = await session.execute(blocked_user_ids_query)
        blocked_user_ids = blocked_by_user_ids_result.scalars().all()

        # Base query to find other users
        query = select(User).where(
            User.id != current_user.id,
            User.status == UserStatus.active,
            User.id.notin_(seen_user_ids),
        )
        query = query.where(User.id.notin_(blocked_user_ids)) # Exclude blocked users

        # Gender filtering
        if current_user.looking_for != LookingForGender.any:
            query = query.where(User.gender == UserGender[current_user.looking_for.name])

        # Also filter based on the other person's preference
        query = query.where(
            or_(
                User.looking_for == LookingForGender[current_user.gender.name],
                User.looking_for == LookingForGender.any,
            )
        )

        # Ensure the user has at least one approved photo
        query = query.where(exists().where(and_(Photo.user_id == User.id, Photo.is_approved == True)))

        # Only show profiles that are admin-approved. NULL means a legacy profile
        # created before this feature existed, which is treated as already approved.
        query = query.where(
            or_(User.profile_approval_status == "approved", User.profile_approval_status.is_(None))
        )

        # Boosted profiles (active boost) are shown first, then random order
        now = datetime.now()
        is_boosted = case((and_(User.boost_active_until.isnot(None), User.boost_active_until > now), 1), else_=0)
        query = query.order_by(is_boosted.desc(), func.random()).limit(limit)

        result = await session.execute(query)
        return result.scalars().all()


async def get_users_who_liked_me(user_id: int) -> list[User]:
    """
    Fetches users who have liked the given user and with whom there is no active match yet.
    """
    async with async_session_maker() as session:
        # Get IDs of users who liked the current user
        liker_ids_query = select(Like.from_user_id).where(Like.to_user_id == user_id)
        liker_ids_result = await session.execute(liker_ids_query)
        liker_ids = liker_ids_result.scalars().all()

        if not liker_ids:
            return []

        # Get IDs of users with whom the current user already has an active match
        matched_user1_ids_query = select(Match.user1_id).where(
            Match.user2_id == user_id, Match.is_active == True
        )
        matched_user1_ids_result = await session.execute(matched_user1_ids_query)
        matched_user1_ids = matched_user1_ids_result.scalars().all()

        matched_user2_ids_query = select(Match.user2_id).where(
            Match.user1_id == user_id, Match.is_active == True
        )
        matched_user2_ids_result = await session.execute(matched_user2_ids_query)
        matched_user2_ids = matched_user2_ids_result.scalars().all()

        matched_user_ids = set(matched_user1_ids + matched_user2_ids)

        # Filter out users who are already matched
        unmatched_liker_ids = [uid for uid in liker_ids if uid not in matched_user_ids]

        if not unmatched_liker_ids:
            return []

        # Fetch the user objects for the remaining likers
        users_query = (
            select(User)
            .where(User.id.in_(unmatched_liker_ids))
             # Ensure they have photos and are active
            .where(User.status == UserStatus.active)
            .where(exists().where(and_(Photo.user_id == User.id, Photo.is_approved == True)))
        )
        users_result = await session.execute(users_query)
        return users_result.scalars().all()


async def add_like_and_check_match(from_user_id: int, to_user_id: int, is_super_like: bool = False) -> Match | None:
    """
    Adds a like from one user to another and checks for a match.
    Returns the Match object if a match occurred, None otherwise.
    """
    async with async_session_maker() as session:
        # Prevent duplicate likes
        existing = await session.scalar(
            select(Like).where(
                Like.from_user_id == from_user_id,
                Like.to_user_id == to_user_id,
            )
        )

        if existing:
            return None

        new_like = Like(from_user_id=from_user_id, to_user_id=to_user_id, is_super_like=is_super_like)
        session.add(new_like)

        if is_super_like:
            await session.flush()

        # Check if the other user has already liked the current user
        reverse_like_exists = await session.scalar(
            select(exists().where(and_(Like.from_user_id == to_user_id, Like.to_user_id == from_user_id)))
        )

        if reverse_like_exists:
            new_match = Match(user1_id=from_user_id, user2_id=to_user_id)
            session.add(new_match)
            await session.commit()
            return new_match

        await session.commit()
        return None


async def remove_like(from_user_id: int, to_user_id: int) -> bool:
    """Removes a like from one user to another. Returns True if a like was removed, False otherwise."""
    async with async_session_maker() as session:
        result = await session.execute(
            delete(Like).where(
                and_(
                    Like.from_user_id == from_user_id,
                    Like.to_user_id == to_user_id
                )
            )
        )
        await session.commit()
        return result.rowcount > 0


async def create_chat_message(match_id: int, sender_id: int, text: str) -> ChatMessage:
    """
    Saves a new message to the database.
    """
    async with async_session_maker() as session:
        new_message = ChatMessage(
            match_id=match_id,
            sender_id=sender_id,
            text=text
        )
        session.add(new_message)
        await session.commit()
        return new_message


async def get_chat_messages(match_id: int, limit: int = 50) -> list[ChatMessage]:
    """
    Fetches the chat history for a given match, ordered from oldest to newest.
    """
    async with async_session_maker() as session:
        result = await session.execute(
            select(ChatMessage)
            .where(ChatMessage.match_id == match_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
        )
        return result.scalars().all()


async def mark_messages_as_read(match_id: int, user_id: int):
    """Marks all messages in a match as read for a specific user."""
    async with async_session_maker() as session:
        await session.execute(
            update(ChatMessage)
            .where(
                and_(
                    ChatMessage.match_id == match_id,
                    ChatMessage.sender_id != user_id,  # Mark messages sent by the other person
                    ChatMessage.is_read == False
                )
            )
            .values(is_read=True)
        )
        await session.commit()


async def get_unread_count(user_id: int) -> int:
    """
    Counts the total number of unread messages for a user across all their active matches.
    """
    async with async_session_maker() as session:
        # First, get all active match IDs for the user
        matches_result = await session.execute(
            select(Match.id).where(
                or_(Match.user1_id == user_id, Match.user2_id == user_id),
                Match.is_active == True
            )
        )
        match_ids = matches_result.scalars().all()

        if not match_ids:
            return 0

        # Then, count unread messages in those matches that were not sent by the user
        unread_count_result = await session.scalar(
            select(func.count(ChatMessage.id))
            .where(
                and_(
                    ChatMessage.match_id.in_(match_ids),
                    ChatMessage.sender_id != user_id,
                    ChatMessage.is_read == False
                )
            )
        )
        return unread_count_result or 0


async def get_user_chats(user_id: int) -> list[dict]:
    """
    Fetches all active chats for a user, including the other user's info and the last message.
    """
    async with async_session_maker() as session:
        # Subquery for the last message in each match
        last_message_sq = (
            select(
                ChatMessage.match_id,
                ChatMessage.text,
                ChatMessage.created_at,
                func.row_number()
                .over(partition_by=ChatMessage.match_id, order_by=ChatMessage.created_at.desc())
                .label("row_num"),
            )
            .alias("last_message_sq")
        )

        last_message = select(
            last_message_sq.c.match_id,
            last_message_sq.c.text,
            last_message_sq.c.created_at,
        ).where(last_message_sq.c.row_num == 1).alias("last_message")

        # Main query to get matches and join with other user and last message
        result = await session.execute(
            select(
                Match,
                User,
                last_message.c.text.label("last_message_text"),
                last_message.c.created_at.label("last_message_at"),
            )
            .join(
                User,
                # Join User on the condition that it's the OTHER user in the match
                case(
                    (Match.user1_id == user_id, User.id == Match.user2_id),
                    else_= (User.id == Match.user1_id),
                ),
            )
            .outerjoin(last_message, Match.id == last_message.c.match_id)
            .where(
                or_(Match.user1_id == user_id, Match.user2_id == user_id),
                Match.is_active == True,
            )
            .order_by(last_message.c.created_at.desc().nullslast(), Match.created_at.desc())
        )

        chats = []
        for match, other_user, last_text, last_at in result.all():
            chats.append({
                "match": match,
                "other_user": other_user,
                "last_message_text": last_text,
                "last_message_at": last_at,
            })
        return chats


async def update_user_profile_field(user_id: int, field: str, value: any) -> bool:
    """Updates a specific field for a user."""
    async with async_session_maker() as session:
        user = await session.get(User, user_id)
        if user:
            setattr(user, field, value)
            await session.commit()
            return True
        return False


async def is_admin_user(telegram_id: int) -> bool:
    """Checks if a telegram user is an admin: either listed in ADMIN_IDS (.env) or granted via the bot."""
    if telegram_id in ADMIN_IDS:
        return True
    user = await get_user_by_telegram_id(telegram_id)
    return bool(user and user.is_admin)


async def add_admin_by_telegram_id(telegram_id: int) -> User | None:
    """Grants bot-level admin rights to an already-registered user. Returns None if the user doesn't exist."""
    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if not user:
            return None
        user.is_admin = True
        await session.commit()
        await session.refresh(user)
        return user


async def remove_admin_by_telegram_id(telegram_id: int) -> User | None:
    """Revokes bot-granted admin rights from a user. Returns None if the user doesn't exist."""
    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if not user:
            return None
        user.is_admin = False
        await session.commit()
        await session.refresh(user)
        return user


async def get_dynamic_admins() -> list[User]:
    """Fetches all users granted admin rights via the bot (not the primary ADMIN_IDS env admins)."""
    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.is_admin == True))
        return result.scalars().all()


async def get_all_admin_ids() -> list[int]:
    """
    Fetches all admin Telegram IDs, combining static ADMIN_IDS from config
    and dynamic admins from the database.
    """
    dynamic_admins = await get_dynamic_admins()
    dynamic_admin_ids = [admin.telegram_id for admin in dynamic_admins]
    
    # Combine and remove duplicates
    all_admin_ids = set(ADMIN_IDS)
    all_admin_ids.update(dynamic_admin_ids)
    
    return list(all_admin_ids)



async def create_support_message(user_id: int, message: str) -> SupportMessage:
    """Persists a user's complaint/suggestion message sent to admins."""
    async with async_session_maker() as session:
        new_message = SupportMessage(user_id=user_id, message=message)
        session.add(new_message)
        await session.commit()
        await session.refresh(new_message)
        return new_message


async def create_admin_log(admin_id: int, action: ActionType, target_user_id: int | None = None, comment: str | None = None) -> AdminLog:
    """Admin harakatlarini jurnalga yozadi."""
    async with async_session_maker() as session:
        log_entry = AdminLog(
            admin_id=admin_id,
            action_type=action,
            target_user_id=target_user_id,
            comment=comment,
        )
        session.add(log_entry)
        await session.commit()
        await session.refresh(log_entry)
        return log_entry


async def update_user_photos(user_id: int, new_photo_file_ids: list[str]):
    """Deletes all old photos for a user and adds new ones."""
    async with async_session_maker() as session:
        # Delete old photos
        await session.execute(delete(Photo).where(Photo.user_id == user_id))

        # Add new photos
        for i, file_id in enumerate(new_photo_file_ids):
            new_photo = Photo(
                user_id=user_id,
                file_id=file_id,
                order=i + 1,
                is_approved=False,  # Needs re-moderation
            )
            session.add(new_photo)
        await session.commit()


async def set_primary_photo(user_id: int, photo_id: int) -> bool:
    """Sets a specific photo as the user's primary (first) photo."""
    async with async_session_maker() as session:
        # First, find the target photo and ensure it belongs to the user and is approved
        target_photo = await session.get(Photo, photo_id)
        if not target_photo or target_photo.user_id != user_id or not target_photo.is_approved:
            return False
        
        # Set all other photos for this user to have order > 1
        await session.execute(
            update(Photo)
            .where(and_(Photo.user_id == user_id, Photo.id != photo_id))
            .values(order=Photo.order + 1)
        )
        
        # Set the target photo's order to 1
        target_photo.order = 1
        
        await session.commit()
        return True


async def create_report(reporter_id: int, reported_id: int, category: ReportCategory, description: str) -> Report:
    """Creates a new report in the database."""
    async with async_session_maker() as session:
        new_report = Report(
            reporter_id=reporter_id,
            reported_id=reported_id,
            category=category,
            description=description,
        )
        session.add(new_report)
        await session.commit()
        return new_report


async def get_unapproved_photo() -> Photo | None:
    """Fetches a single unapproved photo with its user."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(Photo)
            .where(Photo.is_approved == False)
            .options(selectinload(Photo.user))
            .order_by(Photo.uploaded_at)
            .limit(1)
        )
        return result.scalar_one_or_none()


async def get_photo_by_id(photo_id: int) -> Photo | None:
    """Fetches a photo by its ID."""
    async with async_session_maker() as session:
        return await session.get(Photo, photo_id, options=[selectinload(Photo.user)])


async def approve_photo(photo_id: int) -> bool:
    """Approves a photo."""
    async with async_session_maker() as session:
        photo = await session.get(Photo, photo_id)
        if photo:
            photo.is_approved = True
            await session.commit()
            return True
        return False


async def reject_photo(photo_id: int) -> bool:
    """Rejects (deletes) a photo."""
    async with async_session_maker() as session:
        await session.execute(delete(Photo).where(Photo.id == photo_id))
        await session.commit()
        return True


async def delete_photo(photo_id: int) -> bool:
    """Deletes a single photo by its ID."""
    async with async_session_maker() as session:
        result = await session.execute(
            delete(Photo).where(Photo.id == photo_id)
        )
        await session.commit()
        return result.rowcount > 0


async def get_pending_report() -> Report | None:
    """Fetches a single pending report with its related users."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(Report)
            .where(Report.status == ReportStatus.pending)
            .options(
                selectinload(Report.reporter),
                selectinload(Report.reported)
            )
            .order_by(Report.created_at)
            .limit(1)
        )
        return result.scalar_one_or_none()


async def get_all_reports(status: ReportStatus | None = None, page: int = 1, page_size: int = 10) -> tuple[list[Report], int]:
    """Fetches all reports with pagination and optional status filtering."""
    async with async_session_maker() as session:
        query = select(Report).options(
            selectinload(Report.reporter),
            selectinload(Report.reported)
        )
        count_query = select(func.count(Report.id))

        if status:
            query = query.where(Report.status == status)
            count_query = count_query.where(Report.status == status)

        total_count = await session.scalar(count_query) or 0
        
        offset = (page - 1) * page_size
        query = query.order_by(Report.created_at.desc()).offset(offset).limit(page_size)
        
        result = await session.execute(query)
        reports = result.scalars().all()
        
        return reports, total_count


async def get_user_report_count(user_id: int) -> int:
    """Counts how many times a user has been reported."""
    async with async_session_maker() as session:
        count = await session.scalar(
            select(func.count(Report.id)).where(Report.reported_id == user_id)
        )
        return count or 0


async def get_report_by_id(report_id: int) -> Report | None:
    """Fetches a report by its ID with related users."""
    async with async_session_maker() as session:
        return await session.get(Report, report_id, options=[selectinload(Report.reporter), selectinload(Report.reported)])


async def update_report_status(report_id: int, status: ReportStatus) -> bool:
    """Updates a report's status."""
    async with async_session_maker() as session:
        report = await session.get(Report, report_id)
        if report:
            report.status = status
            await session.commit()
            return True
        return False


async def set_user_status(user_id: int, status: UserStatus) -> bool:
    """Updates a user's status (e.g., to ban or unban)."""
    async with async_session_maker() as session:
        user = await session.get(User, user_id)
        if user:
            user.status = status
            await session.commit()
            return True
        return False


async def ban_user_with_duration(user_id: int, duration_days: int | None) -> bool:
    """Foydalanuvchini bloklaydi. duration_days=None bo'lsa, ban doimiy bo'ladi."""
    async with async_session_maker() as session:
        user = await session.get(User, user_id)
        if not user:
            return False
        user.status = UserStatus.banned
        user.banned_until = (datetime.now() + timedelta(days=duration_days)) if duration_days else None
        await session.commit()
        return True


async def lift_user_ban(user_id: int) -> bool:
    """Foydalanuvchini blokdan chiqaradi va ban muddatini tozalaydi."""
    async with async_session_maker() as session:
        user = await session.get(User, user_id)
        if not user:
            return False
        user.status = UserStatus.active
        user.banned_until = None
        await session.commit()
        return True


async def auto_lift_expired_ban(user: User) -> User:
    """Muddatli ban muddati o'tgan bo'lsa, avtomatik ravishda blokdan chiqaradi."""
    if user.status != UserStatus.banned or user.banned_until is None or user.banned_until > datetime.now():
        return user

    await lift_user_ban(user.id)
    user.status = UserStatus.active
    user.banned_until = None
    return user


async def find_user_by_id_or_telegram_id(identifier: str) -> User | None:
    """Finds a user by their DB ID or Telegram ID."""
    if not identifier.isdigit():
        return None

    user_id = int(identifier)

    async with async_session_maker() as session:
        # Search by Telegram ID first, as it's more common for admins to have
        result = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = result.scalar_one_or_none()

        if user:
            return user

        # If not found, search by primary key ID
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()


async def get_bot_statistics() -> dict:
    """
    Returns various statistics about the bot's users and activity.
    """
    async with async_session_maker() as session:
        # Total registered users
        total_users = await session.scalar(select(func.count(User.id)))

        # Registered today
        today = func.current_date()
        registered_today = await session.scalar(
            select(func.count(User.id)).where(cast(User.registered_at, Date) == today)
        )

        # Active users (e.g., last 24 hours, or simply not banned)
        # For simplicity, let's count non-banned users for now.
        active_users = await session.scalar(
            select(func.count(User.id)).where(User.status != UserStatus.banned)
        )

        # Total matches
        total_matches = await session.scalar(select(func.count(Match.id)))

        # Premium users
        premium_users = await session.scalar(
            select(func.count(User.id)).where(User.premium_plan != PremiumPlan.basic)
        )

        return {
            "total_users": total_users,
            "registered_today": registered_today,
            "active_users": active_users,
            "total_matches": total_matches,
            "premium_users": premium_users,
        }

async def get_all_active_user_telegram_ids() -> list[int]:
    """Fetches all telegram IDs of active users for broadcasting."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(User.telegram_id).where(User.status == UserStatus.active)
        )
        return result.scalars().all()

# Placeholder for delete_user_data, assuming it will be implemented to remove all user-related data
async def delete_user_data(user_id: int) -> bool:
    """Deletes all data associated with a user."""
    try:
        async with async_session_maker() as session:
            # Delete photos
            await session.execute(delete(Photo).where(Photo.user_id == user_id))
            # Delete verification requests
            await session.execute(delete(VerificationRequest).where(VerificationRequest.user_id == user_id))
            # Delete likes where user is from_user or to_user
            await session.execute(delete(Like).where(or_(Like.from_user_id == user_id, Like.to_user_id == user_id)))
            # Delete matches where user is user1 or user2
            await session.execute(delete(Match).where(or_(Match.user1_id == user_id, Match.user2_id == user_id)))
            # Delete chat messages where user is sender
            await session.execute(delete(ChatMessage).where(ChatMessage.sender_id == user_id))
            # Delete blocks made by or to the user
            await session.execute(delete(BlockedUser).where(or_(BlockedUser.blocker_id == user_id, BlockedUser.blocked_id == user_id)))
            # Delete payments and subscriptions
            await session.execute(delete(Payment).where(Payment.user_id == user_id))
            await session.execute(delete(Subscription).where(Subscription.user_id == user_id))
            # Delete reports where user is reporter or reported
            await session.execute(delete(Report).where(or_(Report.reporter_id == user_id, Report.reported_id == user_id)))
            # Delete support messages sent by the user
            await session.execute(delete(SupportMessage).where(SupportMessage.user_id == user_id))
            # Delete gifts sent by or to the user
            await session.execute(delete(Gift).where(or_(Gift.sender_id == user_id, Gift.receiver_id == user_id)))
            # Admin logs reference target_user_id via a FK, so they must go before the user row.
            await session.execute(delete(AdminLog).where(AdminLog.target_user_id == user_id))
            # Delete the user itself
            await session.execute(delete(User).where(User.id == user_id))
            await session.commit()
            return True
    except Exception as exc:
        import logging
        logging.warning(f"Foydalanuvchi ma'lumotlarini o'chirishda xatolik (user_id={user_id}): {exc}")
        return False



async def get_payment_statistics() -> dict:
    """
    Returns statistics about premium plans and payments.
    This is a placeholder and needs actual implementation based on Subscription and Payment models.
    """
    async with async_session_maker() as session:
        total_premium_subscriptions = await session.scalar(select(func.count(Subscription.id)))
        active_subscriptions = await session.scalar(select(func.count(Subscription.id)).where(Subscription.end_date > datetime.now()))
        # Sum of completed payments, assuming 'amount' is in UZS
        total_revenue = await session.scalar(select(func.sum(Payment.amount)).where(Payment.status == "completed"))
        
        return {
            "total_premium_subscriptions": total_premium_subscriptions or 0,
            "active_subscriptions": active_subscriptions or 0,
            "total_revenue": total_revenue or 0.0,
        }


async def has_active_premium(user_id: int) -> bool:
    """Checks if the user has an active, non-basic premium plan."""
    async with async_session_maker() as session:
        user = await session.get(User, user_id)
        if not user:
            return False
        
        # Check for a non-basic plan and an expiration date in the future
        return (
            user.premium_plan is not None and
            user.premium_plan != PremiumPlan.basic and
            user.premium_expires_at is not None and
            user.premium_expires_at > datetime.now()
        )


async def create_subscription(user_id: int, plan: PremiumPlan, duration_days: int) -> Subscription | None:
    """Creates a new subscription and updates the user's premium status."""
    async with async_session_maker() as session:
        user = await session.get(User, user_id)
        if not user:
            return None

        start_date = datetime.now()
        end_date = start_date + timedelta(days=duration_days)

        new_subscription = Subscription(
            user_id=user_id,
            plan_name=plan.value,
            start_date=start_date,
            end_date=end_date,
            is_active=True
        )
        session.add(new_subscription)

        # Update user's premium status
        user.premium_plan = plan
        user.premium_expires_at = end_date

        await session.commit()
        return new_subscription


async def cancel_subscription(user_id: int) -> bool:
    """Cancels a user's active subscription."""
    async with async_session_maker() as session:
        user = await session.get(User, user_id)
        if not user:
            return False

        # Find the latest active subscription and deactivate it
        sub_result = await session.execute(
            select(Subscription)
            .where(Subscription.user_id == user_id, Subscription.is_active == True)
            .order_by(Subscription.start_date.desc())
        )
        active_sub = sub_result.scalar_one_or_none()

        if active_sub:
            active_sub.is_active = False
            active_sub.end_date = datetime.now()

        # Revert user to basic plan
        user.premium_plan = PremiumPlan.basic
        user.premium_expires_at = None

        await session.commit()
        return True

async def renew_subscription(user_id: int, plan: PremiumPlan, duration_days: int) -> Subscription | None:
    """Renews or upgrades a user's subscription."""
    async with async_session_maker() as session:
        user = await session.get(User, user_id)
        if not user:
            return None

        # If user has an existing active subscription, extend its end date
        # Otherwise, treat it as a new subscription
        current_end_date = user.premium_expires_at if user.premium_expires_at and user.premium_expires_at > datetime.now() else datetime.now()
        
        new_end_date = current_end_date + timedelta(days=duration_days)

        # Deactivate old subscriptions for this user
        await session.execute(
            update(Subscription)
            .where(Subscription.user_id == user_id)
            .values(is_active=False)
        )

        # Create a new subscription record for the renewal
        new_subscription = Subscription(
            user_id=user_id,
            plan_name=plan.value,
            start_date=datetime.now(),
            end_date=new_end_date,
            is_active=True
        )
        session.add(new_subscription)
        
        # Update user's premium status
        user.premium_plan = plan
        user.premium_expires_at = new_end_date

        await session.commit()
        return new_subscription


async def log_profile_view(viewer_id: int, viewed_id: int):
    """Logs that a user has viewed another user's profile."""
    # Prevent users from logging views of their own profile
    if viewer_id == viewed_id:
        return

    async with async_session_maker() as session:
        new_view = ProfileView(viewer_id=viewer_id, viewed_id=viewed_id)
        session.add(new_view)
        await session.commit()


async def get_profile_viewers(user_id: int, limit: int = 20) -> list[User]:
    """
    Fetches a list of users who have recently viewed the given user's profile.
    This is a premium feature.
    """
    async with async_session_maker() as session:
        # Get recent, unique viewer IDs
        subquery = (
            select(ProfileView.viewer_id)
            .where(ProfileView.viewed_id == user_id)
            .distinct()
            .order_by(func.max(ProfileView.timestamp).desc())
            .group_by(ProfileView.viewer_id)
            .limit(limit)
        ).alias("recent_viewers")

        # Fetch the full user objects for these viewers
        result = await session.execute(
            select(User).join(subquery, User.id == subquery.c.viewer_id)
        )
        return result.scalars().all()


async def log_user_event(user_id: int, event_type: EventType, details: str | None = None):
    """Logs a specific user event for analytics."""
    async with async_session_maker() as session:
        new_event = UserEvent(
            user_id=user_id,
            event_type=event_type,
            details=details,
        )
        session.add(new_event)
        await session.commit()


async def get_daily_active_users(target_date: date) -> int:
    """Counts the number of unique users who were active on a specific date."""
    async with async_session_maker() as session:
        count = await session.scalar(
            select(func.count(func.distinct(UserEvent.user_id)))
            .where(cast(UserEvent.created_at, Date) == target_date)
        )
        return count or 0


async def block_user(blocker_id: int, blocked_id: int) -> BlockedUser:
    """Blocks a user."""
    async with async_session_maker() as session:
        new_block = BlockedUser(blocker_id=blocker_id, blocked_id=blocked_id)
        session.add(new_block)
        await session.commit()
        return new_block


async def unblock_user(blocker_id: int, blocked_id: int) -> bool:
    """Unblocks a user."""
    async with async_session_maker() as session:
        result = await session.execute(
            delete(BlockedUser).where(
                and_(BlockedUser.blocker_id == blocker_id, BlockedUser.blocked_id == blocked_id)
            )
        )
        await session.commit()
        return result.rowcount > 0


async def is_user_blocked(user_id: int, target_user_id: int) -> bool:
    """Checks if user_id has blocked target_user_id."""
    async with async_session_maker() as session:
        result = await session.scalar(select(exists().where(and_(BlockedUser.blocker_id == user_id, BlockedUser.blocked_id == target_user_id))))
        return result


async def create_verification_request(user_id: int, file_id: str) -> VerificationRequest:
    """Creates a new verification request and updates user status."""
    async with async_session_maker() as session:
        # Check if there is already a pending request
        existing_request = await session.scalar(
            select(VerificationRequest).where(
                VerificationRequest.user_id == user_id,
                VerificationRequest.status == ReportStatus.pending
            )
        )
        if existing_request:
            return existing_request # Or raise an exception

        new_request = VerificationRequest(user_id=user_id, file_id=file_id)
        session.add(new_request)

        user = await session.get(User, user_id)
        if user:
            user.verification_status = VerificationStatus.in_progress

        await session.commit()
        return new_request


async def get_pending_verification_request() -> VerificationRequest | None:
    """Fetches a single pending verification request with its user."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(VerificationRequest)
            .where(VerificationRequest.status == ReportStatus.pending)
            .options(selectinload(VerificationRequest.user))
            .order_by(VerificationRequest.created_at)
            .limit(1)
        )
        return result.scalar_one_or_none()


async def update_verification_request_status(request_id: int, new_status: ReportStatus, admin_id: int) -> VerificationRequest | None:
    """Approves or rejects a verification request and updates the user."""
    async with async_session_maker() as session:
        request = await session.get(VerificationRequest, request_id, options=[selectinload(VerificationRequest.user)])
        if not request:
            return None

        request.status = new_status
        request.reviewed_at = func.now()
        request.reviewed_by = admin_id

        if new_status == ReportStatus.resolved: # 'resolved' means approved
            request.user.verification_status = VerificationStatus.verified
        elif new_status == ReportStatus.rejected:
            request.user.verification_status = VerificationStatus.rejected

        await session.commit()
        await session.refresh(request)
        return request


async def create_payment_record(user_id: int, amount: float, plan_name: str, payment_system: str = "manual_card") -> Payment:
    """Creates a new payment record with a 'pending' status."""
    async with async_session_maker() as session:
        new_payment = Payment(
            user_id=user_id,
            amount=amount,
            description=plan_name,
            payment_system=payment_system,
            status="pending", # Admin needs to confirm this
            transaction_id=f"manual_{user_id}_{int(datetime.now().timestamp())}", # Generate a unique-ish ID
        )
        session.add(new_payment)
        await session.commit()
        return new_payment


async def get_pending_payment() -> Payment | None:
    """Fetches a single pending payment with its user."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(Payment)
            .where(Payment.status == "pending")
            .options(selectinload(Payment.user))
            .order_by(Payment.created_at)
            .limit(1)
        )
        return result.scalar_one_or_none()


async def update_payment_status(payment_id: int, new_status: str) -> Payment | None:
    """Updates a payment's status."""
    async with async_session_maker() as session:
        payment = await session.get(Payment, payment_id)
        if payment:
            payment.status = new_status
            await session.commit()
            await session.refresh(payment)
            return payment
        return None



async def get_admin_logs(
    limit: int = 10, 
    offset: int = 0, 
    filter_date: date | None = None, 
    filter_action: ActionType | None = None
) -> tuple[list[AdminLog], int]:
    """Fetches admin logs with pagination and filtering."""
    async with async_session_maker() as session:
        base_query = select(AdminLog)
        count_query = select(func.count(AdminLog.id))

        if filter_date:
            base_query = base_query.where(cast(AdminLog.created_at, Date) == filter_date)
            count_query = count_query.where(cast(AdminLog.created_at, Date) == filter_date)

        if filter_action:
            base_query = base_query.where(AdminLog.action_type == filter_action)
            count_query = count_query.where(AdminLog.action_type == filter_action)

        total_count = await session.scalar(count_query) or 0

        # Get paginated logs
        logs_query = (
            base_query
            .order_by(AdminLog.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await session.execute(logs_query)
        logs = result.scalars().all()
        return logs, total_count


async def _update_user_language(user_id: int, new_language: str):
    """Updates a user's language in the database."""
    async with async_session_maker() as session:
        await session.execute(
            update(User)
            .where(User.id == user_id)
            .values(language=new_language)
        )
        await session.commit()


async def update_user_language(admin_id: int, user_id: int, new_language: str):
    """
    Updates a user's language in the database and logs the admin action.
    This function should be called by admins to change a user's language.
    """
    await _update_user_language(user_id, new_language)
    await create_admin_log(
        admin_id=admin_id,
        action=ActionType.update_user_language,
        target_user_id=user_id,
        comment=f"User language updated to {new_language}"
    )


async def create_gift(sender_id: int, receiver_id: int, gift_type: GiftType, message: str | None = None) -> Gift:
    """Creates a new gift record in the database."""
    async with async_session_maker() as session:
        new_gift = Gift(
            sender_id=sender_id,
            receiver_id=receiver_id,
            gift_type=gift_type,
            message=message,
        )
        session.add(new_gift)
        await session.commit()
        await session.refresh(new_gift)
        return new_gift


async def get_user_referrals(user_id: int) -> list[User]:
    """Fetches all users referred by a specific user."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.referred_by_id == user_id)
        )
        return result.scalars().all()