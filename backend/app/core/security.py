from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from typing import Optional, Union
from datetime import datetime
import hashlib
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.jwt_handler import verify_token

security = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


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


async def verify_api_key(
    api_key: str,
    db: AsyncSession,
    required_scope: Optional[str] = None
) -> dict:
    """
    Verify API key and check if it has required scope.

    Args:
        api_key: The API key to verify
        db: Database session
        required_scope: Required scope (e.g., "evaluations:import")

    Returns:
        dict: API key info if valid

    Raises:
        HTTPException: 401 if invalid, 403 if insufficient scope
    """
    from app.models.api_key import ApiKey

    # Hash the API key to look it up
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    # Query database for this key
    stmt = select(ApiKey).where(ApiKey.id == key_hash)
    result = await db.execute(stmt)
    api_key_obj = result.scalar_one_or_none()

    # Check if key exists
    if not api_key_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )

    # Check if key is active
    if not api_key_obj.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is inactive"
        )

    # Check if key is expired
    if api_key_obj.expires_at and api_key_obj.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has expired"
        )

    # Check scope if required
    if required_scope:
        scopes = [s.strip() for s in api_key_obj.scopes.split(",")]
        if required_scope not in scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"API key does not have required scope: {required_scope}"
            )

    # Update last_used_at
    api_key_obj.last_used_at = datetime.utcnow()
    await db.commit()

    return {
        "key_id": api_key_obj.id,
        "key_name": api_key_obj.name,
        "scopes": scopes
    }


def require_api_key(required_scope: str):
    """
    Dependency factory for endpoints that require API key authentication.

    Usage:
        @router.post("/import")
        async def import_data(
            api_key_info: dict = Depends(require_api_key("evaluations:import")),
            db: AsyncSession = Depends(get_db)
        ):
            ...
    """
    async def api_key_checker(
        api_key: Optional[str] = Depends(api_key_header)
    ) -> dict:
        # Import here to avoid circular dependency
        from app.database.session import get_db

        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key required. Provide via X-API-Key header.",
                headers={"WWW-Authenticate": "ApiKey"}
            )

        # Get database session
        async for db in get_db():
            result = await verify_api_key(api_key, db, required_scope)
            return result

    return api_key_checker


async def get_current_user_or_api_key(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    api_key: Optional[str] = Depends(api_key_header)
) -> Union[dict, None]:
    """
    Try to authenticate with either JWT token OR API key.
    This allows endpoints to accept both authentication methods.

    Priority:
    1. API Key (X-API-Key header)
    2. JWT Token (Authorization header or cookie)

    Returns:
        dict: User info from JWT or API key info
        None: If neither authentication method is provided
    """
    # Try API key first
    if api_key:
        from app.database.session import get_db
        async for db in get_db():
            try:
                return await verify_api_key(api_key, db)
            except HTTPException:
                pass  # Fall through to JWT
            break

    # Try JWT token
    try:
        return await get_current_user(request, credentials)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide either JWT token or API key.",
            headers={"WWW-Authenticate": "Bearer, ApiKey"}
        )


def require_api_key_or_admin(required_scope: Optional[str] = None):
    """
    Dependency factory that accepts EITHER:
    - API key with required scope
    - Admin user with JWT token

    This is useful for import endpoints that should be accessible via:
    1. External API calls using API keys
    2. Admin users via web UI using JWT tokens

    Usage:
        @router.post("/import")
        async def import_data(
            auth_info: dict = Depends(require_api_key_or_admin("evaluations:import")),
            db: AsyncSession = Depends(get_db)
        ):
            ...
    """
    async def auth_checker(
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
        api_key: Optional[str] = Depends(api_key_header)
    ) -> dict:
        from app.database.session import get_db

        # Try API key first
        if api_key:
            async for db in get_db():
                try:
                    api_key_info = await verify_api_key(api_key, db, required_scope)
                    return {
                        "auth_type": "api_key",
                        "key_id": api_key_info["key_id"],
                        "key_name": api_key_info["key_name"],
                        "scopes": api_key_info["scopes"]
                    }
                except HTTPException:
                    pass  # Fall through to JWT
                break

        # Try JWT token - must be admin
        try:
            user = await get_current_user(request, credentials)
            if user.get("role") != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin role required for this operation"
                )
            return {
                "auth_type": "jwt",
                "user_id": user.get("localId"),
                "email": user.get("email"),
                "role": user.get("role")
            }
        except HTTPException:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required. Provide either API key or admin JWT token.",
                headers={"WWW-Authenticate": "Bearer, ApiKey"}
            )

    return auth_checker

