"""
Security utilities for JWT token verification and current user extraction
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from app.core.jwt_handler import verify_token
from app.models import User
from app.database.session import AsyncSessionLocal
from sqlalchemy import select

security = HTTPBearer()


async def get_current_user(
    credentials = Depends(security),
) -> dict:
    """
    Extract and verify JWT token from request header
    Returns token payload with user info
    
    Args:
        credentials: HTTP Bearer token from Authorization header
        
    Returns:
        dict: Token payload containing user_id, role, etc.
        
    Raises:
        HTTPException: 401 if token is invalid or expired
    """
    token = credentials.credentials
    payload = verify_token(token, required_scope="access")
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload


async def get_current_user_from_db(
    current_user: dict = Depends(get_current_user),
) -> User:
    """
    Get current user from database using token payload
    Ensures user is still active
    
    Args:
        current_user: Token payload from get_current_user
        
    Returns:
        User: User object from database
        
    Raises:
        HTTPException: 401 if user not found or inactive, 403 if not verified
    """
    try:
        async with AsyncSessionLocal() as db:
            user_id = int(current_user.get("user_id"))
            
            stmt = select(User).where(User.id == user_id)
            result = await db.execute(stmt)
            user = result.scalars().first()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User account is inactive",
                )
            
            return user
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )


def check_role(required_roles: list[str]):
    """
    Factory function to create role-checking dependency
    
    Args:
        required_roles: List of allowed roles (e.g., ["admin", "mod"])
        
    Returns:
        Callable: Dependency function to use in route
    """
    async def role_checker(
        current_user: dict = Depends(get_current_user),
    ) -> dict:
        """
        Check if current user has required role
        
        Args:
            current_user: Token payload from get_current_user
            
        Returns:
            dict: Token payload if role check passes
            
        Raises:
            HTTPException: 403 if user doesn't have required role
        """
        user_role = current_user.get("role")
        
        if user_role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(required_roles)}",
            )
        
        return current_user
    
    return role_checker


async def check_permissions(
    required_roles: list[str] = None,
) -> callable:
    """
    Helper function to check multiple conditions
    """
    async def permission_checker(
        current_user: dict = Depends(get_current_user),
    ) -> dict:
        if required_roles:
            user_role = current_user.get("role")
            if user_role not in required_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required roles: {', '.join(required_roles)}",
                )
        
        return current_user
    
    return permission_checker
