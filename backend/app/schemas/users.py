from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
import re


class AssignLocalIdRequest(BaseModel):
    """Request schema for assigning localId to a user"""
    localId: str = Field(..., min_length=1, max_length=50)

    @field_validator('localId')
    @classmethod
    def validate_localId(cls, v: str) -> str:
        """Validate that localId contains only alphanumeric characters"""
        if not re.match(r'^[A-Za-z0-9]+$', v):
            raise ValueError('localId must contain only alphanumeric characters')
        return v


class UpdateRoleRequest(BaseModel):
    """Request schema for updating user role"""
    role: str = Field(..., pattern="^(guest|user|admin)$")


class UserResponse(BaseModel):
    """Response schema for user data"""
    id: int
    email: Optional[str]
    full_name: Optional[str]
    localId: Optional[str]
    role: str
    provider: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Response schema for list users endpoint"""
    users: List[UserResponse]
    total: int
    limit: int
    offset: int


class UserActionResponse(BaseModel):
    """Generic response for user update actions"""
    success: bool
    message: str
    user: UserResponse
