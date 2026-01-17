"""
API Key Pydantic Schemas

Request/response validation schemas for API key management.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ApiKeyCreate(BaseModel):
    """Schema for creating a new API key."""
    name: str = Field(..., description="Friendly name for the API key", min_length=3, max_length=100)
    description: Optional[str] = Field(None, description="Purpose description", max_length=255)
    scopes: List[str] = Field(..., description="List of scopes (e.g., ['evaluations:import', 'dormitory-bills:import'])")
    expires_days: Optional[int] = Field(None, description="Number of days until expiration (null = never expires)", ge=1, le=365)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "HRS Import Service",
                "description": "API key for automated data imports from HRS system",
                "scopes": ["evaluations:import", "dormitory-bills:import"],
                "expires_days": 365
            }
        }


class ApiKeyResponse(BaseModel):
    """Schema for API key info (without the actual key)."""
    id: str = Field(..., description="API key hash (ID)")
    name: str = Field(..., description="Friendly name")
    description: Optional[str] = Field(None, description="Purpose description")
    key_prefix: str = Field(..., description="Key prefix for identification (e.g., 'fhs_1234')")
    scopes: str = Field(..., description="Comma-separated scopes")
    is_active: bool = Field(..., description="Whether key is active")
    created_by: Optional[str] = Field(None, description="Employee ID who created this key")
    created_at: datetime = Field(..., description="Creation timestamp")
    last_used_at: Optional[datetime] = Field(None, description="Last usage timestamp")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")

    class Config:
        from_attributes = True


class ApiKeyCreated(BaseModel):
    """Schema for newly created API key (includes actual key - shown only once)."""
    api_key: str = Field(..., description="The actual API key (save this - it won't be shown again!)")
    key_info: ApiKeyResponse = Field(..., description="API key information")

    class Config:
        json_schema_extra = {
            "example": {
                "api_key": "fhs_1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
                "key_info": {
                    "id": "hash123...",
                    "name": "HRS Import Service",
                    "description": "API key for automated data imports",
                    "key_prefix": "fhs_1234",
                    "scopes": "evaluations:import,dormitory-bills:import",
                    "is_active": True,
                    "created_by": "VNW0012345",
                    "created_at": "2026-01-17T01:00:00Z",
                    "last_used_at": None,
                    "expires_at": "2027-01-17T01:00:00Z"
                }
            }
        }


class ApiKeyListResponse(BaseModel):
    """Schema for listing API keys."""
    total: int = Field(..., description="Total number of API keys", ge=0)
    keys: List[ApiKeyResponse] = Field(..., description="List of API keys")
