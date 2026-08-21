import enum
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    BigInteger,
    DateTime,
    Enum,
    Boolean,
    Float,
    func
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class UserStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    ACTIVE = "ACTIVE"
    APPROVED = "APPROVED"
    SUSPENDED = "SUSPENDED"
    REJECTED = "REJECTED"
    BANNED = "BANNED"
    DELETED = "DELETED"

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    MODERATOR = "MODERATOR"
    SUPPORT = "SUPPORT"
    USER = "USER"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String, nullable=True)
    role = Column(String(32), default="USER", nullable=False)
    status = Column(Enum(UserStatus, native_enum=False, values_callable=lambda x: [e.value for e in x]), default=UserStatus.DRAFT, nullable=False)
    
    # Financial / Points
    balance = Column(Float, default=0.0)
    bonus_points = Column(Integer, default=0)
    
    # Settings & Localization
    language = Column(String(10), default="uz", nullable=False)
    
    # Profile information
    name = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    city = Column(String, nullable=True)
    photo = Column(Text, nullable=True)
    bio = Column(Text, nullable=True)
    interests = Column(Text, nullable=True) # JSON list string e.g. ["🎮 Gaming", "🎵 Music"]
    terms_accepted = Column(Boolean, default=False)
    
    # Status flags
    is_verified = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    last_active_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class UserStatusHistory(Base):
    __tablename__ = "user_status_history"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    old_status = Column(String(32), nullable=False)
    new_status = Column(String(32), nullable=False)
    changed_by = Column(BigInteger, nullable=False) # Telegram ID of admin or system
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    type = Column(String(32), default="system", nullable=False) # system, account, security, match, message, admin
    title = Column(String(128), nullable=False)
    body = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    deep_link = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=func.now())

class SupportTicket(Base):
    __tablename__ = "support_tickets"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    subject = Column(String(128), nullable=False)
    category = Column(String(64), default="General", nullable=False)
    priority = Column(String(32), default="NORMAL", nullable=False) # LOW, NORMAL, HIGH, URGENT
    status = Column(String(32), default="OPEN", nullable=False) # OPEN, ANSWERED, CLOSED
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class TicketMessage(Base):
    __tablename__ = "ticket_messages"
    id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, nullable=False, index=True)
    sender_id = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

class AdminAuditLog(Base):
    __tablename__ = "admin_audit_logs"
    id = Column(Integer, primary_key=True)
    admin_id = Column(BigInteger, nullable=False, index=True)
    action = Column(String(64), nullable=False)
    target_type = Column(String(64), nullable=False)
    target_id = Column(Integer, nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

class AdminNote(Base):
    __tablename__ = "admin_notes"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    admin_id = Column(BigInteger, nullable=False)
    note = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())

class Swipe(Base):
    __tablename__ = "swipes"
    id = Column(Integer, primary_key=True)
    swiper_id = Column(Integer, nullable=False, index=True)
    swiped_id = Column(Integer, nullable=False, index=True)
    is_like = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=func.now())

class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True)
    user1_id = Column(Integer, nullable=False, index=True)
    user2_id = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, default=func.now())

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, nullable=False, index=True)
    sender_id = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())

class Block(Base):
    __tablename__ = "blocks"
    id = Column(Integer, primary_key=True)
    blocker_id = Column(Integer, nullable=False, index=True)
    blocked_id = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, default=func.now())

class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True)
    reporter_id = Column(Integer, nullable=False, index=True)
    reported_id = Column(Integer, nullable=False, index=True)
    reason = Column(String(64), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(32), default="OPEN", nullable=False) # OPEN, REVIEWING, RESOLVED, REJECTED
    created_at = Column(DateTime, default=func.now())
