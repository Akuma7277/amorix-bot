from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, exists, func, delete, cast, Date
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
)
from engine import async_session_maker
 

async def create_user_profile(telegram_id: int, user_data: dict) -> User:
    """
    Foydalanuvchi ma'lumotlarini va rasmlarini ma'lumotlar bazasiga saqlaydi.
    """
    async with async_session_maker() as session:
        # User obyektini yaratish
        new_user = User(
            telegram_id=telegram_id,
            name=user_data.get("name"),
            age=user_data.get("age"),
            gender=UserGender[user_data["gender"]],  # Enumga o'tkazish
            looking_for=LookingForGender[user_data["looking_for"]],  # Enumga o'tkazish
            city=user_data.get("city"),
            district=user_data.get("district"),
            bio=user_data.get("bio"),
            interests=",".join(user_data.get("interests", [])),
            language=user_data.get("language"),
            # Boshqa maydonlar default qiymatlar bilan to'ldiriladi
        )
        session.add(new_user)
        await session.flush()  # new_user.id ni olish uchun

        # Rasmlarni saqlash
        photos = user_data.get("photos", [])
        for i, file_id in enumerate(photos):
            new_photo = Photo(
                user_id=new_user.id,
                file_id=file_id,
                order=i + 1,
                is_approved=False,  # Moderatsiya uchun dastlab tasdiqlanmagan
            )
            session.add(new_photo)

        await session.commit()
        await session.refresh(new_user)

        return new_user


async def get_user_by_telegram_id(telegram_id: int) -> User | None:
    """Foydalanuvchini telegram ID orqali topadi."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()


async def get_user_photos(user_id: int) -> list[Photo]:
    """Foydalanuvchining rasmlarini user_id orqali topadi."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(Photo).where(Photo.user_id == user_id).order_by(Photo.order)
        )
        return result.scalars().all()


async def get_user_matches(user_id: int) -> list[Match]:
    """
    Fetches all active matches for a user.
    """
    async with async_session_maker() as session:
        result = await session.execute(
            select(Match).where(
                or_(Match.user1_id == user_id, Match.user2_id == user_id),
                Match.is_active == True
            ).order_by(Match.created_at.desc())
        )
        return result.scalars().all()


async def get_user_by_id(user_id: int) -> User | None:
    """Finds a user by their primary key ID."""
    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()


async def get_match_by_id(match_id: int) -> Match | None:
    """Finds a match by its primary key ID."""
    async with async_session_maker() as session:
        result = await session.execute(select(Match).where(Match.id == match_id))
        return result.scalar_one_or_none()


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
            User.status == "active",
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

        # Add limit and random order
        query = query.order_by(func.random()).limit(limit)

        result = await session.execute(query)
        return result.scalars().all()


async def add_like_and_check_match(from_user_id: int, to_user_id: int) -> Match | None:
    """
    Adds a like from one user to another and checks for a match.
    Returns the Match object if a match occurred, None otherwise.
    """
    async with async_session_maker() as session:
        new_like = Like(from_user_id=from_user_id, to_user_id=to_user_id)
        session.add(new_like)

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


async def update_user_profile_field(user_id: int, field: str, value: any):
    """Updates a specific field for a user."""
    async with async_session_maker() as session:
        user = await session.get(User, user_id)
        if user:
            setattr(user, field, value)
            await session.commit()
            return True
        return False


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
            select(func.count(User.id)).where(User.status != "banned")
        )

        # Total matches
        total_matches = await session.scalar(select(func.count(Match.id)))

        # Premium users
        premium_users = await session.scalar(
            select(func.count(User.id)).where(User.premium_plan != "basic")
        )

        return {
            "total_users": total_users,
            "registered_today": registered_today,
            "active_users": active_users,
            "total_matches": total_matches,
            "premium_users": premium_users,
        }


# Placeholder for delete_user_data, assuming it will be implemented to remove all user-related data
async def delete_user_data(user_id: int) -> bool:
    """Deletes all data associated with a user."""
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
        # Delete the user itself
        await session.execute(delete(User).where(User.id == user_id))
        await session.commit()
        return True


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


async def update_user_language(user_id: int, new_language: str):
    """Updates a user's language in the database."""
    async with async_session_maker() as session:
        await session.execute(
            update(User)
            .where(User.id == user_id)
            .values(language=new_language)
        )
        await session.commit()