"""
API Key Model

Model for managing API keys used for external integrations and import endpoints.
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.sql import func
from app.core.database import Base


class ApiKey(Base):
    __tablename__ = "api_keys"

    # Primary Key
    id = Column(String(64), primary_key=True, index=True)  # API key hash

    # Key Info
    name = Column(String(100), nullable=False)  # Friendly name (e.g., "HRS Import Service")
    description = Column(String(255), nullable=True)  # Purpose description
    key_prefix = Column(String(16), nullable=False, index=True)  # First 8 chars for identification

    # Permissions
    scopes = Column(String(255), nullable=False)  # Comma-separated: "evaluations:import,dormitory-bills:import"

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Audit
    created_by = Column(String(10), nullable=True)  # Employee ID who created this key
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Optional expiration

    def __repr__(self):
        return f"<ApiKey(name={self.name}, prefix={self.key_prefix}, active={self.is_active})>"
