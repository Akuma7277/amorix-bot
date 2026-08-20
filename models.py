import enum
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    BigInteger,
    DateTime,
    Enum,
    func
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class UserStatus(enum.Enum):
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
    status = Column(Enum(UserStatus), default=UserStatus.DRAFT, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
