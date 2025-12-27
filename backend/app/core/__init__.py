"""
Core module - Configuration, security, JWT, and permissions
"""
from app.core.config import settings
from app.core.jwt_handler import create_access_token, verify_token
from app.core.security import (
    get_current_user,
    get_current_user_from_db,
    check_role,
)

__all__ = [
    "settings",
    "create_access_token",
    "verify_token",
    "get_current_user",
    "get_current_user_from_db",
    "check_role",
]
