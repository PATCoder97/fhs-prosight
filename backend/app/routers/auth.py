from fastapi import APIRouter, Request
from app.services.auth_service import get_google_auth_url, handle_google_callback
from app.schemas.auth import GoogleLoginResponse, SocialLoginUser

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/login/google")
async def login_google(request: Request) -> dict:
    """Get Google OAuth login URL"""
    return await get_google_auth_url(request)

@router.get("/google/callback", response_model=GoogleLoginResponse)
async def google_callback(request: Request) -> GoogleLoginResponse:
    """Handle Google OAuth callback and return user info with tokens"""
    user = await handle_google_callback(request)
    return user
