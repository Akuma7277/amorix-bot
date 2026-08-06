import enum
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    BigInteger,
    DateTime,
    Enum,
    Float,
    Boolean,
    ForeignKey,
    func,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# Enums (kategoriyalar)
class UserGender(enum.Enum):
    male = "Erkak"
    female = "Ayol"

class LookingForGender(enum.Enum):
    male = "Erkak"
    female = "Ayol"
    any = "Farqi yo'q"

class UserStatus(enum.Enum):
    active = "Faol"
    inactive = "Nofaol"
    banned = "Bloklangan"

class VerificationStatus(enum.Enum):
    not_verified = "Tasdiqlanmagan"
    in_progress = "Jarayonda"
    verified = "Tasdiqlangan"
    rejected = "Rad etilgan"

class PremiumPlan(enum.Enum):
    basic = "Basic"
    gold = "Gold"
    platinum = "Platinum"

class ReportCategory(enum.Enum):
    fake_profile = "Soxta profil"
    inappropriate_content = "Nomaqbul kontent"
    spam = "Spam"
    insult = "Qo'pol muomala"
    other = "Boshqa"

class ReportStatus(enum.Enum):
    pending = "Kutilmoqda"
    resolved = "Hal qilindi"
    rejected = "Rad etildi"

# NEW ENUM FOR GIFTS
class GiftType(enum.Enum):
    flower = "Gul 💐"
    chocolate = "Shokolad 🍫"
    coffee = "Qahva ☕"
    bear = "O'yinchoq ayiq 🧸"
    heart = "Yurak ❤️"
class ActionType(enum.Enum):
    ban_user = "Foydalanuvchini bloklash"
    unban_user = "Foydalanuvchini blokdan chiqarish"
    approve_photo = "Rasmni tasdiqlash"
    reject_photo = "Rasmni rad etish"
    send_broadcast = "Broadcast yuborish"
    approve_verification = "Verifikatsiyani tasdiqlash"
    reject_verification = "Verifikatsiyani rad etish"
    resolve_report = "Shikoyatni hal qilish"
    reject_report = "Shikoyatni rad etish"
    confirm_payment = "To'lovni tasdiqlash"
    reject_payment = "To'lovni rad etish"
    approve_profile = "Profilni tasdiqlash"
    reject_profile = "Profilni rad etish"
    add_admin = "Admin qo'shildi"
    remove_admin = "Admin olib tashlandi"
    delete_profile = "Profilni o'chirish"
    update_user_language = "Foydalanuvchi tilini o'zgartirish"

# Jadvallar
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    name = Column(String(100))
    age = Column(Integer)
    gender = Column(Enum(UserGender))
    looking_for = Column(Enum(LookingForGender))
    city = Column(String(100))
    district = Column(String(100))
    bio = Column(Text)
    interests = Column(Text) # Qiziqishlar vergul bilan ajratilgan string sifatida
    language = Column(String(10))
    status = Column(Enum(UserStatus), default=UserStatus.active)
    # Muddatli ban uchun tugash sanasi. NULL + status=banned => doimiy ban.
    banned_until = Column(DateTime, nullable=True)
    verification_status = Column(Enum(VerificationStatus), default=VerificationStatus.not_verified)
    premium_plan = Column(Enum(PremiumPlan), default=PremiumPlan.basic)
    premium_expires_at = Column(DateTime)
    daily_likes_used = Column(Integer, default=0)
    daily_super_likes_used = Column(Integer, default=0)
    daily_quota_reset_at = Column(DateTime, nullable=True)
    boost_active_until = Column(DateTime, nullable=True)
    registered_at = Column(DateTime, server_default=func.now())
    last_activity = Column(DateTime, onupdate=func.now())
    referred_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    # Profil to'liq ro'yxatdan o'tgandan keyin admin tasdig'ini kutish holati.
    # Qiymatlar: "pending", "approved", "rejected". NULL = eski profillar (avtomatik tasdiqlangan deb hisoblanadi).
    profile_approval_status = Column(String(20), nullable=True)
    # ADMIN_IDS (.env) dagi asosiy adminlardan tashqari, bot orqali qo'shilgan qo'shimcha adminlar uchun.
    is_admin = Column(Boolean, default=False)
    height = Column(Float, nullable=True)  # new field
    is_invisible = Column(Boolean, default=False)  # new field

    @property
    def is_premium(self) -> bool:
        """Checks if the user has an active premium subscription."""
        if self.premium_expires_at and self.premium_expires_at > func.now():
            return True
        return False

class Photo(Base):
    __tablename__ = "photos"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_id = Column(String, nullable=False)
    order = Column(Integer, default=1)
    is_approved = Column(Boolean, default=False)
    uploaded_at = Column(DateTime, server_default=func.now())

    user = relationship("User")

class Like(Base):
    __tablename__ = "likes"
    id = Column(Integer, primary_key=True)
    from_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    to_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_super_like = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True)
    user1_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user2_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    is_active = Column(Boolean, default=True)

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    text = Column(Text)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True)
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reported_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category = Column(Enum(ReportCategory))
    description = Column(Text)
    status = Column(Enum(ReportStatus), default=ReportStatus.pending)
    created_at = Column(DateTime, server_default=func.now())

    reporter = relationship("User", foreign_keys=[reporter_id])
    reported = relationship("User", foreign_keys=[reported_id])

class AdminLog(Base):
    __tablename__ = "admin_logs"
    id = Column(Integer, primary_key=True)
    admin_id = Column(BigInteger, nullable=False)
    action_type = Column(Enum(ActionType))
    target_user_id = Column(Integer, ForeignKey("users.id"))
    comment = Column(Text)
    created_at = Column(DateTime, server_default=func.now())


class Setting(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True)
    key = Column(String(50), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)


class BlockedUser(Base):
    __tablename__ = "blocked_users"
    id = Column(Integer, primary_key=True)
    blocker_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    blocked_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tariff = Column(String(50), nullable=False)  # Basic, Gold, Platinum
    price = Column(Float, nullable=False)
    start_date = Column(DateTime, server_default=func.now())
    end_date = Column(DateTime)
    status = Column(String(50))  # active, expired, cancelled

    user = relationship("User")


class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String(100))
    payment_system = Column(String(50))  # Payme, Click, Uzcard/Humo
    transaction_id = Column(String(100), unique=True)
    status = Column(String(50))  # pending, completed, failed
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User")


class VerificationRequest(Base):
    __tablename__ = "verification_requests"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_id = Column(String, nullable=False)
    status = Column(Enum(ReportStatus), default=ReportStatus.pending)
    created_at = Column(DateTime, server_default=func.now())
    reviewed_at = Column(DateTime)
    reviewed_by = Column(BigInteger) # Admin telegram_id

    user = relationship("User")

# NEW GIFT MODEL
class Gift(Base):
    __tablename__ = "gifts"
    id = Column(Integer, primary_key=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    gift_type = Column(Enum(GiftType), nullable=False)
    message = Column(Text, nullable=True)
    sent_at = Column(DateTime, server_default=func.now())
    is_read = Column(Boolean, default=False)

    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])


class SupportMessage(Base):
    __tablename__ = "support_messages"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(20), default="pending")  # pending, read
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User")


class ProfileView(Base):
    __tablename__ = "profile_views"
    id = Column(Integer, primary_key=True)
    viewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    viewed_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    timestamp = Column(DateTime, server_default=func.now())

    viewer = relationship("User", foreign_keys=[viewer_id])
    viewed = relationship("User", foreign_keys=[viewed_id])


class EventType(enum.Enum):
    app_start = "Ilovani ishga tushirish"
    profile_view = "Profilni ko'rish"
    like = "Layk bosish"
    super_like = "Super-layk bosish"
    match = "Moslik (match)"
    chat_message = "Xabar yuborish"
    premium_purchase = "Premium sotib olish"


class UserEvent(Base):
    __tablename__ = "user_events"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_type = Column(Enum(EventType), nullable=False)
    details = Column(Text, nullable=True) # e.g., viewed_user_id, match_id
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User")