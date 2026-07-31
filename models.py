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
    verification_status = Column(Enum(VerificationStatus), default=VerificationStatus.not_verified)
    premium_plan = Column(Enum(PremiumPlan), default=PremiumPlan.basic)
    premium_expires_at = Column(DateTime)
    registered_at = Column(DateTime, server_default=func.now())
    last_activity = Column(DateTime, onupdate=func.now())

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