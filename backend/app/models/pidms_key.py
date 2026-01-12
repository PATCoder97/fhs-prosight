"""
PIDMS Key Model

Stores Microsoft product license keys from PIDKey.com API with activation tracking,
blocked status, and product information.
"""

from sqlalchemy import Column, Integer, String, DateTime, Index
from sqlalchemy.sql import func
from app.models.user import Base


class PIDMSKey(Base):
    """Microsoft product license key record from PIDKey.com."""

    __tablename__ = "pidms_keys"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Key Information (unique identifier)
    keyname = Column(String(255), unique=True, nullable=False, index=True)
    keyname_with_dash = Column(String(255), nullable=False)

    # Product Information
    prd = Column(String(255), nullable=False, index=True)  # Product code
    eid = Column(String(255), nullable=True)  # Enterprise ID
    is_key_type = Column(String(50), nullable=True)
    is_retail = Column(Integer, nullable=True)  # 1=retail, 2=volume license
    sub = Column(String(255), nullable=True)  # Subscription code

    # Activation Status
    remaining = Column(Integer, nullable=False, default=0, index=True)  # Remaining activations
    blocked = Column(Integer, nullable=False, default=-1, index=True)  # -1=not blocked, 1=blocked

    # Error Tracking
    errorcode = Column(String(255), nullable=True)
    had_occurred = Column(Integer, default=0)
    invalid = Column(Integer, default=0)

    # Last Check Information
    datetime_checked_done = Column(String(255), nullable=True)  # Timestamp from PIDKey.com

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Indexes for search performance
    __table_args__ = (
        Index('idx_pidms_keys_prd', 'prd'),
        Index('idx_pidms_keys_remaining', 'remaining'),
        Index('idx_pidms_keys_blocked', 'blocked'),
    )
