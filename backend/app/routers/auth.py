from fastapi import APIRouter, Request
from app.services.auth_service import get_google_auth_url, handle_google_callback

router = APIRouter()

@router.get("/login/google")
async def login_google(request: Request):
    return await get_google_auth_url(request)

@router.get("/auth/google/callback")
async def google_callback(request: Request):
    user = await handle_google_callback(request)
    return user
