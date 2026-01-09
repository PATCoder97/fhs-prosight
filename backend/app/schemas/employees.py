from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import date, datetime


# Request Schemas
class SyncEmployeeRequest(BaseModel):
    """Request schema for syncing a single employee"""
    emp_id: int = Field(..., ge=1, description="Employee ID (e.g., 6204)")
    source: str = Field(..., pattern="^(hrs|covid)$", description="Data source: hrs or covid")
    token: Optional[str] = Field(None, description="Bearer token (required for covid)")

    @field_validator('token')
    @classmethod
    def validate_token_for_covid(cls, v: Optional[str], info) -> Optional[str]:
        """Validate that token is provided when source is covid"""
        if hasattr(info, 'data') and info.data.get('source') == 'covid' and not v:
            raise ValueError('token is required when source is covid')
        return v


class BulkSyncRequest(BaseModel):
    """Request schema for bulk syncing employees"""
    from_id: int = Field(..., ge=1, description="Starting employee ID")
    to_id: int = Field(..., ge=1, description="Ending employee ID")
    source: str = Field(..., pattern="^(hrs|covid)$", description="Data source: hrs or covid")
    token: Optional[str] = Field(None, min_length=10, description="Bearer token (required for covid)")

    @field_validator('to_id')
    @classmethod
    def validate_range(cls, v: int, info) -> int:
        """Validate that to_id >= from_id and range <= 1000"""
        if hasattr(info, 'data'):
            from_id = info.data.get('from_id')
            if from_id is not None:
                if v < from_id:
                    raise ValueError('to_id must be >= from_id')
                if v - from_id > 1000:
                    raise ValueError('Range too large (max: 1000 employees)')
        return v

    @field_validator('token')
    @classmethod
    def validate_token_required_for_covid(cls, v: Optional[str], info) -> Optional[str]:
        """Validate that token is provided when source is covid"""
        if hasattr(info, 'data') and info.data.get('source') == 'covid' and not v:
            raise ValueError('token is required when source is covid')
        return v


class UpdateEmployeeRequest(BaseModel):
    """Request schema for updating employee data"""
    name_tw: Optional[str] = Field(None, max_length=100)
    name_en: Optional[str] = Field(None, max_length=100)
    dob: Optional[date] = None
    start_date: Optional[date] = None
    dept: Optional[str] = Field(None, max_length=100)
    department_code: Optional[str] = Field(None, max_length=8)
    job_title: Optional[str] = Field(None, max_length=100)
    job_type: Optional[str] = Field(None, max_length=100)
    salary: Optional[int] = Field(None, ge=0)
    address1: Optional[str] = Field(None, max_length=200)
    address2: Optional[str] = Field(None, max_length=200)
    phone1: Optional[str] = Field(None, max_length=20)
    phone2: Optional[str] = Field(None, max_length=20)
    spouse_name: Optional[str] = Field(None, max_length=100)
    nationality: Optional[str] = Field(None, max_length=20)
    identity_number: Optional[str] = Field(None, max_length=32)
    sex: Optional[str] = Field(None, max_length=8)
    dorm_id: Optional[str] = Field(None, max_length=20)


# Response Schemas
class EmployeeResponse(BaseModel):
    """Response schema for employee data"""
    id: str
    name_tw: Optional[str]
    name_en: Optional[str]
    dob: Optional[date]
    start_date: Optional[date]
    dept: Optional[str]
    department_code: Optional[str]
    job_title: Optional[str]
    job_type: Optional[str]
    salary: Optional[int]
    address1: Optional[str]
    address2: Optional[str]
    phone1: Optional[str]
    phone2: Optional[str]
    spouse_name: Optional[str]
    nationality: Optional[str]
    identity_number: Optional[str]
    sex: Optional[str]
    dorm_id: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class EmployeeListResponse(BaseModel):
    """Response schema for list employees endpoint"""
    items: List[EmployeeResponse]
    total: int
    skip: int
    limit: int


class BulkSyncResponse(BaseModel):
    """Response schema for bulk sync operation"""
    total: int = Field(..., description="Total employees in range")
    success: int = Field(..., description="Successfully synced")
    failed: int = Field(..., description="Failed to sync")
    skipped: int = Field(..., description="Skipped (no data from API)")
    errors: List[dict] = Field(default_factory=list, description="Error details: [{emp_id: int, error: str}]")


class DeleteResponse(BaseModel):
    """Response schema for delete operation"""
    success: bool
    message: str
