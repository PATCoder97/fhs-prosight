from pydantic import BaseModel
from typing import Optional


class SocialLoginUser(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    avatar: Optional[str]
    role: str = "user"
    is_new_user: bool = False


class GoogleLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: SocialLoginUser
