# app/core/jwt_handler.py
"""
JWT Token Handler - Generate & Verify tokens
Support both access token và pre_auth token
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from app.core.config import settings

logger = logging.getLogger(__name__)


def create_access_token(
    user_id: str,
    role: str,
    full_name: str = None,
    expires_delta: Optional[timedelta] = None,
    scope: str = "access"
) -> str:
    """
    Tạo JWT token
    
    Args:
        user_id: User ID
        role: User role (admin, user, etc)
        full_name: Full name (optional)
        expires_delta: Token lifetime
        scope: Token scope ("access" hoặc "pre_auth")
        
    Returns:
        str: Encoded JWT token
    """
    if expires_delta is None:
        if scope == "pre_auth":
            # Pre-auth token tồn tại 5 phút
            expires_delta = timedelta(minutes=5)
        else:
            # Access token tồn tại 24 giờ
            expires_delta = timedelta(hours=24)
    
    expire = datetime.utcnow() + expires_delta
    
    payload = {
        "user_id": user_id,
        "role": role,
        "scope": scope,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "bearer"
    }
    
    if full_name:
        payload["full_name"] = full_name
    
    encoded_jwt = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    logger.info(f"Created {scope} token for user {user_id}")
    return encoded_jwt


def verify_token(token: str, required_scope: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Xác thực JWT token
    
    Args:
        token: JWT token string
        required_scope: Required scope ("access" hoặc "pre_auth")
        
    Returns:
        dict: Token payload nếu valid, None nếu invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        # Check scope nếu cần
        if required_scope and payload.get("scope") != required_scope:
            logger.warning(f"Token scope mismatch. Expected {required_scope}, got {payload.get('scope')}")
            return None
        
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None


def get_token_payload(token: str) -> Optional[Dict[str, Any]]:
    """
    Lấy payload từ token (không verify expiry, dùng cho debug)
    
    Args:
        token: JWT token string
        
    Returns:
        dict: Token payload
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": False}
        )
        return payload
    except Exception as e:
        logger.error(f"Error decoding token: {e}")
        return None
