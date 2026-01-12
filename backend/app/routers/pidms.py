"""
PIDMS API Router

REST API endpoints for PIDMS (Product ID Management System) operations.
Provides key validation, search, product statistics, and synchronization.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.security import require_role
from app.core.config import settings
from app.database.session import get_db
from app.schemas.pidms import (
    PIDMSKeyCheckRequest,
    PIDMSCheckResponse,
    PIDMSSearchResponse,
    PIDMSProductsResponse,
    PIDMSSyncRequest,
    PIDMSSyncResponse,
)
from app.services import pidms_service
from app.integrations.pidkey_client import PIDKeyClient

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/pidms",
    tags=["pidms"]
)


def get_pidkey_client() -> PIDKeyClient:
    """Dependency to get PIDKey.com client instance."""
    return PIDKeyClient(
        api_key=settings.PIDKEY_API_KEY,
        base_url=settings.PIDKEY_BASE_URL
    )


@router.post(
    "/check",
    response_model=PIDMSCheckResponse,
    summary="Check and import product keys",
    description="Validate product keys against PIDKey.com and import/update in database (admin only)"
)
async def check_keys(
    request: PIDMSKeyCheckRequest,
    current_user: dict = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
    client: PIDKeyClient = Depends(get_pidkey_client)
):
    """
    Check product keys against PIDKey.com and import/update in database.

    **Access:** Admin only

    **Request Body:**
    - keys: Newline or comma-separated list of product keys (with or without dashes)

    **Response:**
    - 200: Check summary with new/updated counts and detailed results
    - 403: Forbidden (not admin)
    - 422: Validation errors (no valid keys provided)
    - 500: Server error (API failure, database error)

    **Example Request:**
    ```json
    {
      "keys": "6NRGD-KHFCF-Y4TF7-PRWFD-YBF3H\\r\\n8NFMQ-FTF43-RQCKR-T473J-JFHB2"
    }
    ```

    **Example Response:**
    ```json
    {
      "success": true,
      "summary": {
        "total_keys": 2,
        "new_keys": 1,
        "updated_keys": 1,
        "errors": 0
      },
      "results": [
        {
          "keyname": "6NRGDKHFCFY4TF7PRWFDYBF3H",
          "keyname_with_dash": "6NRGD-KHFCF-Y4TF7-PRWFD-YBF3H",
          "status": "updated",
          "prd": "Office15_ProPlusVL_MAK",
          "remaining": 2185
        }
      ]
    }
    ```
    """
    # Parse keys from request (split by \r\n or \n)
    keys_list = [k.strip() for k in request.keys.replace("\\r\\n", "\n").split("\n") if k.strip()]

    if not keys_list:
        raise HTTPException(status_code=422, detail="No valid keys provided")

    logger.info(f"Admin {current_user.get('email')} checking {len(keys_list)} keys")

    result = await pidms_service.check_and_upsert_keys(db, keys_list, client)
    return result


@router.get(
    "/search",
    response_model=PIDMSSearchResponse,
    summary="Search product keys",
    description="Search keys with fuzzy product matching and filters (admin only)"
)
async def search_keys(
    product: Optional[str] = Query(None, description="Partial product name match (e.g., 'Office')"),
    min_remaining: Optional[int] = Query(None, ge=0, description="Minimum activations remaining"),
    max_remaining: Optional[int] = Query(None, ge=0, description="Maximum activations remaining"),
    blocked: Optional[int] = Query(None, description="Blocked status (-1=not blocked, 1=blocked)"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page (max 100)"),
    current_user: dict = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Search product keys with fuzzy matching and filters.

    **Access:** Admin only

    **Query Parameters:**
    - product: Partial product name (case-insensitive, e.g., 'Office' matches all Office products)
    - min_remaining: Minimum remaining activation count
    - max_remaining: Maximum remaining activation count
    - blocked: Filter by blocked status (-1 or 1)
    - page: Page number (default: 1)
    - page_size: Items per page (default: 50, max: 100)

    **Response:**
    - 200: Paginated search results
    - 403: Forbidden (not admin)
    - 422: Validation errors (invalid pagination)

    **Example Request:**
    ```
    GET /api/pidms/search?product=Office&min_remaining=100&page=1&page_size=10
    ```

    **Example Response:**
    ```json
    {
      "total": 87,
      "page": 1,
      "page_size": 10,
      "results": [
        {
          "id": 1,
          "keyname": "6NRGDKHFCFY4TF7PRWFDYBF3H",
          "keyname_with_dash": "6NRGD-KHFCF-Y4TF7-PRWFD-YBF3H",
          "prd": "Office15_ProPlusVL_MAK",
          "remaining": 2185,
          "blocked": -1
        }
      ]
    }
    ```
    """
    logger.info(f"Admin {current_user.get('email')} searching keys: product={product}")

    result = await pidms_service.search_keys(
        db, product, min_remaining, max_remaining, blocked, page, page_size
    )
    return result


@router.get(
    "/products",
    response_model=PIDMSProductsResponse,
    summary="Get product statistics",
    description="Get all product types with aggregated statistics (admin only)"
)
async def get_products(
    current_user: dict = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all product types with aggregated statistics.

    **Access:** Admin only

    **Response:**
    - 200: List of all product types with statistics
    - 403: Forbidden (not admin)

    **Example Response:**
    ```json
    {
      "products": [
        {
          "prd": "Office15_ProPlusVL_MAK",
          "key_count": 45,
          "total_remaining": 98234,
          "avg_remaining": 2183.2,
          "low_inventory": false
        },
        {
          "prd": "Office16_StandardVL_MAK",
          "key_count": 12,
          "total_remaining": 345,
          "avg_remaining": 28.75,
          "low_inventory": true
        }
      ]
    }
    ```
    """
    logger.info(f"Admin {current_user.get('email')} requesting product summary")

    result = await pidms_service.get_product_summary(db)
    return result


@router.post(
    "/sync",
    response_model=PIDMSSyncResponse,
    summary="Sync all keys with PIDKey.com",
    description="Sync all keys in database with PIDKey.com (admin only)"
)
async def sync_keys(
    request: PIDMSSyncRequest,
    current_user: dict = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
    client: PIDKeyClient = Depends(get_pidkey_client)
):
    """
    Sync all keys in database with PIDKey.com.

    **Access:** Admin only

    **Request Body:**
    - product_filter: Optional filter to sync only specific product type

    **Response:**
    - 200: Sync summary with total_synced, updated, and error counts
    - 403: Forbidden (not admin)
    - 500: Server error (API failure, database error)

    **Example Request:**
    ```json
    {
      "product_filter": "Office"
    }
    ```

    **Example Response:**
    ```json
    {
      "success": true,
      "summary": {
        "total_synced": 150,
        "updated": 145,
        "errors": 5
      },
      "error_details": [
        {
          "keyname": "XXXXX-XXXXX-XXXXX-XXXXX-XXXXX",
          "error": "Batch 3 sync failed: Timeout"
        }
      ]
    }
    ```
    """
    logger.info(f"Admin {current_user.get('email')} requested sync (filter: {request.product_filter or 'all'})")

    result = await pidms_service.sync_all_keys(db, client, request.product_filter)
    return result
