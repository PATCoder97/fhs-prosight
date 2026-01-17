"""
Dormitory Bill Pydantic Schemas

Request/response validation schemas for dormitory bills API.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class DormitoryBillBase(BaseModel):
    """Base schema for dormitory bill."""
    employee_id: str = Field(..., description="Employee ID (e.g., VNW0012345)", min_length=1)
    term_code: str = Field(..., description="Billing term code (e.g., 25A)", min_length=1)
    dorm_code: str = Field(..., description="Dormitory room code (e.g., A01)", min_length=1)
    factory_location: Optional[str] = Field(None, description="Factory location/wing")

    # Electricity
    elec_last_index: float = Field(0, ge=0, description="Previous electricity meter reading")
    elec_curr_index: float = Field(0, ge=0, description="Current electricity meter reading")
    elec_usage: float = Field(0, ge=0, description="Electricity usage (kWh)")
    elec_amount: float = Field(0, ge=0, description="Electricity bill amount (VND)")

    # Water
    water_last_index: float = Field(0, ge=0, description="Previous water meter reading")
    water_curr_index: float = Field(0, ge=0, description="Current water meter reading")
    water_usage: float = Field(0, ge=0, description="Water usage (m³)")
    water_amount: float = Field(0, ge=0, description="Water bill amount (VND)")

    # Fees
    shared_fee: float = Field(0, ge=0, description="Shared facility fee (VND)")
    management_fee: float = Field(0, ge=0, description="Management fee (VND)")
    total_amount: float = Field(0, ge=0, description="Total bill amount (VND)")

    class Config:
        json_schema_extra = {
            "example": {
                "employee_id": "VNW0012345",
                "term_code": "25A",
                "dorm_code": "A01",
                "factory_location": "North Wing Building A",
                "elec_last_index": 1000.5,
                "elec_curr_index": 1250.3,
                "elec_usage": 249.8,
                "elec_amount": 1249000,
                "water_last_index": 500.2,
                "water_curr_index": 565.7,
                "water_usage": 65.5,
                "water_amount": 327500,
                "shared_fee": 100000,
                "management_fee": 200000,
                "total_amount": 1876500
            }
        }


class DormitoryBillImport(BaseModel):
    """Schema for bulk import request."""
    bills: List[DormitoryBillBase] = Field(..., description="Array of bills to import", min_length=1)

    class Config:
        json_schema_extra = {
            "example": {
                "bills": [
                    {
                        "employee_id": "VNW0012345",
                        "term_code": "25A",
                        "dorm_code": "A01",
                        "factory_location": "North Wing",
                        "elec_last_index": 1000.5,
                        "elec_curr_index": 1250.3,
                        "elec_usage": 249.8,
                        "elec_amount": 1249000,
                        "water_last_index": 500.2,
                        "water_curr_index": 565.7,
                        "water_usage": 65.5,
                        "water_amount": 327500,
                        "shared_fee": 100000,
                        "management_fee": 200000,
                        "total_amount": 1876500
                    }
                ]
            }
        }


class DormitoryBillResponse(DormitoryBillBase):
    """Schema for API response (includes database fields)."""
    bill_id: int = Field(..., description="Unique bill ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        from_attributes = True


class SearchResponse(BaseModel):
    """Schema for paginated search results."""
    total: int = Field(..., description="Total matching records", ge=0)
    page: int = Field(..., description="Current page number", ge=1)
    page_size: int = Field(..., description="Items per page", ge=1, le=100)
    results: List[DormitoryBillResponse] = Field(..., description="Bill records")


class ImportSummary(BaseModel):
    """Schema for import operation summary."""
    success: bool = Field(..., description="Whether import succeeded")
    summary: dict = Field(..., description="Summary statistics (total_records, created, updated, errors, employees_updated)")
    error_details: List[dict] = Field(default_factory=list, description="List of errors with row numbers")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "summary": {
                    "total_records": 150,
                    "created": 120,
                    "updated": 30,
                    "errors": 0,
                    "employees_updated": 145
                },
                "error_details": []
            }
        }
