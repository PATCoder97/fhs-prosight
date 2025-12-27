from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Enum, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Social Login Info
    social_id = Column(String(255), unique=True, index=True, nullable=False)  # sub from Google or id from GitHub
    provider = Column(String(50), nullable=False)  # "google" or "github"

    # User Info
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    avatar = Column(String(500), nullable=True)

    # User Settings
    role = Column(String(50), default="user", nullable=False)  # "user", "admin", "manager", etc.
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, provider={self.provider})>"
