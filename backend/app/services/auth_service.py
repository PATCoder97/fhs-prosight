from app.integrations import GoogleAuthClient, GitHubAuthClient
from app.schemas import LoginResponse, SocialLoginUser
from app.core.jwt_handler import create_access_token, verify_token
from app.core.config import settings
from app.models import User
from app.database.session import AsyncSessionLocal
from sqlalchemy import select
from datetime import datetime
from fastapi.responses import RedirectResponse
from fastapi import HTTPException


google_auth = GoogleAuthClient()
github_auth = GitHubAuthClient()


async def get_or_create_user(social_id: str, provider: str, email: str, full_name: str, avatar: str) -> dict:
    """Get existing user or create new one"""
    try:
        async with AsyncSessionLocal() as db:
            # Đảm bảo email không null (đặc biệt cho github)
            if not email:
                email = f"{provider}_{social_id}@no-email.local"
            
            # Check if user exists by social_id
            stmt = select(User).where(
                (User.social_id == social_id) & (User.provider == provider)
            )
            result = await db.execute(stmt)
            user = result.scalars().first()
            
            if user:
                # Update last_login
                user.last_login = datetime.utcnow()
                await db.commit()
                await db.refresh(user)
                return {
                    "id": user.id,
                    "social_id": user.social_id,
                    "provider": user.provider,
                    "email": user.email,
                    "full_name": user.full_name,
                    "avatar": user.avatar,
                    "role": user.role,
                    "localId": user.localId,
                    "is_active": user.is_active,
                    "is_verified": user.is_verified,
                }
            
            # Create new user
            new_user = User(
                social_id=social_id,
                provider=provider,
                email=email,
                full_name=full_name,
                avatar=avatar,
                role="guest",
                localId=None,
                is_active=True,
                is_verified=False,
            )
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            return {
                "id": new_user.id,
                "social_id": new_user.social_id,
                "provider": new_user.provider,
                "email": new_user.email,
                "full_name": new_user.full_name,
                "avatar": new_user.avatar,
                "role": new_user.role,
                "localId": new_user.localId,
                "is_active": new_user.is_active,
                "is_verified": new_user.is_verified,
            }
    except Exception as e:
        # Fallback nếu database không available - tạo user object tạm thời
        print(f"Database error: {e}. Using fallback user creation.")
        return {
            "id": 0,  # Temporary ID
            "social_id": social_id,
            "provider": provider,
            "email": email,
            "full_name": full_name,
            "avatar": avatar,
            "role": "guest",
            "localId": None,
            "is_active": True,
            "is_verified": False,
        }



async def get_google_auth_url(request):
    return await google_auth.get_authorization_url(request)


async def get_github_auth_url(request):
    return await github_auth.get_authorization_url(request)


async def handle_google_callback(request) -> RedirectResponse:
    userinfo = await google_auth.get_user_info(request)

    social_id = userinfo.get("sub")
    email = userinfo.get("email")
    full_name = userinfo.get("name")
    avatar = userinfo.get("picture")

    # Get or create user in database
    user_data = await get_or_create_user(
        social_id=social_id,
        provider="google",
        email=email,
        full_name=full_name,
        avatar=avatar,
    )

    # Tạo token truy cập
    access_token = create_access_token(
        user_id=str(user_data["id"]),
        full_name=user_data["full_name"],
        role=user_data["role"],
        localId=user_data.get("localId"),
        provider="google",
        scope="access",
    )

    # Create redirect response with HttpOnly cookie
    # Redirect to auth-callback page instead of home
    response = RedirectResponse(url=f"{settings.FRONTEND_URL}/auth-callback")

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
    )

    return response


async def handle_github_callback(request) -> RedirectResponse:
    userinfo = await github_auth.get_user_info(request)

    social_id = str(userinfo.get("id"))
    email = userinfo.get("email")
    full_name = userinfo.get("name")
    avatar = userinfo.get("avatar_url")

    # Get or create user in database
    user_data = await get_or_create_user(
        social_id=social_id,
        provider="github",
        email=email,
        full_name=full_name,
        avatar=avatar,
    )

    # Tạo token truy cập
    access_token = create_access_token(
        user_id=str(user_data["id"]),
        full_name=user_data["full_name"],
        role=user_data["role"],
        localId=user_data.get("localId"),
        provider="github",
        scope="access",
    )

    # Create redirect response with HttpOnly cookie
    # Redirect to auth-callback page instead of home
    response = RedirectResponse(url=f"{settings.FRONTEND_URL}/auth-callback")

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
    )

    return response


async def get_current_user(access_token: str) -> SocialLoginUser:
    """
    Get current user information from access token

    Args:
        access_token: JWT access token from HttpOnly cookie

    Returns:
        SocialLoginUser: User information

    Raises:
        HTTPException: If token is invalid or user not found
    """
    # Verify token
    payload = verify_token(access_token, required_scope="access")

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("user_id")

    try:
        async with AsyncSessionLocal() as db:
            # Get user from database
            stmt = select(User).where(User.id == int(user_id))
            result = await db.execute(stmt)
            user = result.scalars().first()

            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            # Return user info
            return SocialLoginUser(
                id=user.id,
                social_id=user.social_id,
                provider=user.provider,
                email=user.email,
                full_name=user.full_name,
                avatar=user.avatar,
                role=user.role,
                localId=user.localId,
                is_active=user.is_active,
                is_verified=user.is_verified,
                is_new_user=False,
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
