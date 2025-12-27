"""
Permission decorators for role-based access control
Usage: @require_roles(["admin", "mod"])
"""
from functools import wraps
from fastapi import HTTPException, status, Depends
from typing import List, Callable


def require_roles(allowed_roles: List[str]):
    """
    Decorator to require specific roles for an endpoint
    
    Args:
        allowed_roles: List of allowed roles (e.g., ["admin", "mod", "user"])
        
    Usage:
        @router.get("/admin-only")
        @require_roles(["admin"])
        async def admin_endpoint(current_user = Depends(get_current_user)):
            return {"message": "Admin access"}
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract current_user from kwargs
            current_user = kwargs.get("current_user")
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            user_role = current_user.get("role")
            if user_role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required roles: {', '.join(allowed_roles)}. Your role: {user_role}",
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_admin(func: Callable) -> Callable:
    """Quick decorator for admin-only endpoints"""
    return require_roles(["admin"])(func)


def require_mod(func: Callable) -> Callable:
    """Quick decorator for moderator and admin endpoints"""
    return require_roles(["admin", "mod"])(func)


def require_auth(func: Callable) -> Callable:
    """Quick decorator for authenticated users (any role)"""
    return require_roles(["user", "mod", "admin"])(func)
