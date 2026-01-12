"""
PIDMS API Pydantic Schemas

Request/response validation schemas for PIDMS (Product ID Management System) API endpoints.
Covers check, sync, search, and products operations.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class PIDMSKeyCheckRequest(BaseModel):
    """Request schema for checking/importing product keys."""
    keys: str = Field(
        ...,
        description="Newline or comma-separated list of product keys (with or without dashes)",
        min_length=1
    )


class PIDMSKeyResponse(BaseModel):
    """Response schema for a single product key with all fields from PIDKey.com API."""
    id: Optional[int] = None
    keyname: str = Field(..., description="Product key without dashes")
    keyname_with_dash: str = Field(..., description="Product key with dashes for display")
    prd: str = Field(..., description="Product code (e.g., Office15_ProPlusVL_MAK)")
    eid: Optional[str] = Field(None, description="Enterprise ID")
    is_key_type: Optional[str] = Field(None, description="Key type identifier")
    is_retail: Optional[int] = Field(None, description="1=retail, 2=volume license")
    remaining: int = Field(..., description="Remaining activation count")
    blocked: int = Field(..., description="-1=not blocked, 1=blocked")
    errorcode: Optional[str] = Field(None, description="Error code from PIDKey.com")
    sub: Optional[str] = Field(None, description="Subscription code")
    had_occurred: Optional[int] = Field(None, description="Occurrence flag")
    invalid: Optional[int] = Field(None, description="0=valid, 1=invalid")
    datetime_checked_done: Optional[str] = Field(None, description="Last check timestamp from PIDKey.com")
    created_at: Optional[datetime] = Field(None, description="Record creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Record update timestamp")
    status: Optional[str] = Field(None, description="Operation status: 'new' or 'updated'")

    class Config:
        from_attributes = True


class PIDMSCheckSummary(BaseModel):
    """Summary statistics for check/import operation."""
    total_keys: int = Field(..., description="Total keys processed")
    new_keys: int = Field(..., description="Number of new keys inserted")
    updated_keys: int = Field(..., description="Number of existing keys updated")
    errors: int = Field(..., description="Number of errors encountered")


class PIDMSCheckResponse(BaseModel):
    """Response schema for check/import endpoint."""
    success: bool = Field(..., description="Overall operation success status")
    summary: PIDMSCheckSummary
    results: List[PIDMSKeyResponse] = Field(..., description="Detailed results for each key")


class PIDMSSyncRequest(BaseModel):
    """Request schema for syncing all keys with PIDKey.com."""
    product_filter: Optional[str] = Field(
        None,
        description="Optional product filter (e.g., 'Office' to sync only Office products)"
    )


class PIDMSSyncSummary(BaseModel):
    """Summary statistics for sync operation."""
    total_synced: int = Field(..., description="Total keys synced")
    updated: int = Field(..., description="Number of keys updated")
    errors: int = Field(..., description="Number of errors encountered")


class PIDMSSyncErrorDetail(BaseModel):
    """Error detail for a failed key sync."""
    keyname: str = Field(..., description="Key that failed to sync")
    error: str = Field(..., description="Error message")


class PIDMSSyncResponse(BaseModel):
    """Response schema for sync endpoint."""
    success: bool = Field(..., description="Overall sync success status")
    summary: PIDMSSyncSummary
    error_details: List[PIDMSSyncErrorDetail] = Field(
        default_factory=list,
        description="Details of any errors encountered"
    )


class PIDMSSearchResponse(BaseModel):
    """Response schema for search endpoint with pagination."""
    total: int = Field(..., description="Total matching keys")
    page: int = Field(..., description="Current page number (1-indexed)")
    page_size: int = Field(..., description="Items per page")
    results: List[PIDMSKeyResponse] = Field(..., description="Matching keys for current page")


class PIDMSProductSummary(BaseModel):
    """Summary statistics for a single product type."""
    prd: str = Field(..., description="Product code")
    key_count: int = Field(..., description="Total number of keys for this product")
    total_remaining: int = Field(..., description="Sum of all remaining activations")
    avg_remaining: float = Field(..., description="Average remaining activations per key")
    low_inventory: bool = Field(..., description="True if total_remaining < 5")


class PIDMSProductsResponse(BaseModel):
    """Response schema for products endpoint."""
    products: List[PIDMSProductSummary] = Field(
        ...,
        description="List of all product types with statistics"
    )
