from pydantic import BaseModel
from typing import Optional


class SocialLoginUser(BaseModel):
    id: int
    social_id: str
    provider: str  # "google" or "github"
    email: Optional[str]
    full_name: Optional[str]
    avatar: Optional[str]
    role: str = "user"
    localId: Optional[str] = None
    is_active: bool = True
    is_verified: bool = False
    is_new_user: bool = False

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: SocialLoginUser
