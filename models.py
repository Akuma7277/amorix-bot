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
    func
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class UserStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    BANNED = "BANNED"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String, nullable=True)
    status = Column(Enum(UserStatus, native_enum=False, values_callable=lambda x: [e.value for e in x]), default=UserStatus.DRAFT, nullable=False)
    
    # Registration columns
    name = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    city = Column(String, nullable=True)
    photo = Column(Text, nullable=True)
    bio = Column(Text, nullable=True)
    interests = Column(Text, nullable=True) # JSON list string e.g. ["🎮 Gaming", "🎵 Music"]
    terms_accepted = Column(Boolean, default=False)
    
    # Additional status flags
    is_verified = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    last_active_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

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
