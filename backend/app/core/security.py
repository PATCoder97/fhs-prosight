from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from app.core.jwt_handler import verify_token

security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> dict:
    """
    Extract and verify JWT token from Authorization header OR HttpOnly cookie.
    Returns the decoded token payload (user info).

    Priority:
    1. Authorization header (Bearer token)
    2. HttpOnly cookie (access_token)

    Raises:
        HTTPException: 401 if token is invalid, expired, or not found
    """
    token = None

    # ✅ 1. Ưu tiên token từ Authorization header
    if credentials:
        token = credentials.credentials

    # ✅ 2. Fallback: lấy token từ cookie
    if not token:
        token = request.cookies.get("access_token")

    # ❌ Không có token ở cả header lẫn cookie
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_role(required_role: str):
    """
    Decorator factory to check if current user has required role.

    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(current_user: dict = Depends(require_role("admin"))):
            ...
    """
    async def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        user_role = current_user.get("role")

        if user_role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}"
            )

        return current_user

    return role_checker


async def require_authenticated_user(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Check if user is authenticated and has a valid role (not guest).

    Blocks:
    - Unauthenticated users (no token) → 401
    - Guest users (role = "guest") → 403

    Allows:
    - Any authenticated user with role (user, admin, etc.)

    Usage:
        @router.get("/salary/{employee_id}")
        async def get_salary(current_user: dict = Depends(require_authenticated_user)):
            ...
    """
    user_role = current_user.get("role")

    # Block guest users
    if user_role == "guest":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Guest users cannot access salary information. Please sign in with a valid account."
        )

    # Block users without a role
    if not user_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User role is required to access this resource."
        )

    return current_user
