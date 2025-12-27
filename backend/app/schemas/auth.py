from pydantic import BaseModel
from typing import Optional


class SocialLoginUser(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    avatar: Optional[str]
    provider: str = "google"
    role: str = "user"
    is_new_user: bool = False


class GoogleLoginResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int = 86400        # 24h
    scope: str = "access"
    user: SocialLoginUser
