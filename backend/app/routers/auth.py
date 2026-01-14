from fastapi import APIRouter, Request, HTTPException, Cookie, Response
from fastapi.responses import RedirectResponse, JSONResponse
from typing import Optional
from app.services.auth_service import get_google_auth_url, handle_google_callback, handle_github_callback, get_github_auth_url, get_current_user
from app.schemas.auth import SocialLoginUser
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login/google")
async def login_google(request: Request) -> dict:
    """Get Google OAuth login URL"""
    return await get_google_auth_url(request)


@router.get("/google/callback")
async def google_callback(request: Request) -> RedirectResponse:
    """Handle Google OAuth callback and redirect with HttpOnly cookie"""
    return await handle_google_callback(request)

@router.get("/login/github")
async def github_login(request: Request):
    redirect_uri = request.url_for("github_callback")
    return await get_github_auth_url(request)

@router.get("/github/callback")
async def github_callback(request: Request) -> RedirectResponse:
    """Handle GitHub OAuth callback and redirect with HttpOnly cookie"""
    return await handle_github_callback(request)

@router.get("/me", response_model=SocialLoginUser)
async def get_me(access_token: Optional[str] = Cookie(None)) -> SocialLoginUser:
    """Get current user information from HttpOnly cookie"""
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = await get_current_user(access_token)
    return user

@router.post("/logout")
async def logout(response: Response):
    """Logout user by clearing HttpOnly cookie"""
    response = JSONResponse(content={"message": "Logged out successfully"})

    # Clear the access_token cookie with same settings used when setting it
    delete_config = {
        "key": "access_token",
        "path": "/",
        "httponly": True,
        "samesite": "lax"
    }

    # Add domain if configured (must match the domain used when setting cookie)
    # Only add domain parameter if it's not empty
    if settings.COOKIE_DOMAIN and settings.COOKIE_DOMAIN.strip():
        delete_config["domain"] = settings.COOKIE_DOMAIN

    response.delete_cookie(**delete_config)

    return response