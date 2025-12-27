from fastapi import APIRouter, Request
from app.services.auth_service import get_google_auth_url, handle_google_callback, handle_github_callback, get_github_auth_url
from app.schemas.auth import LoginResponse, SocialLoginUser

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login/google")
async def login_google(request: Request) -> dict:
    """Get Google OAuth login URL"""
    return await get_google_auth_url(request)


@router.get("/google/callback", response_model=LoginResponse)
async def google_callback(request: Request) -> LoginResponse:
    """Handle Google OAuth callback and return user info with tokens"""
    user = await handle_google_callback(request)
    return user

@router.get("/login/github")
async def github_login(request: Request):
    redirect_uri = request.url_for("github_callback")
    return await get_github_auth_url(request)

@router.get("/github/callback")
async def github_callback(request: Request):
    return await handle_github_callback(request)