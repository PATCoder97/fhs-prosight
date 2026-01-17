"""
Dormitory Bills API Router

REST API endpoints for dormitory billing operations.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.schemas.dormitory_bill import (
    DormitoryBillImport,
    SearchResponse,
    ImportSummary
)
from app.services import dormitory_bill_service
from app.database.session import get_db
from app.core.security import require_role, require_authenticated_user, require_api_key_or_admin

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/dormitory-bills",
    tags=["dormitory-bills"]
)


@router.post(
    "/import",
    response_model=ImportSummary,
    summary="Import dormitory bills from JSON",
    description="Bulk import dormitory billing data from JSON (requires API key with 'dormitory-bills:import' scope OR admin token)"
)
async def import_dormitory_bills(
    request: DormitoryBillImport,
    auth_info: dict = Depends(require_api_key_or_admin("dormitory-bills:import")),
    db: AsyncSession = Depends(get_db)
):
    """
    Import dormitory bills with bulk upsert logic.

    **Access:** Requires EITHER:
    - API key with 'dormitory-bills:import' scope (for external integrations)
    - Admin user with JWT token (for web UI)

    **Authentication Methods:**
    1. API Key: Provide via X-API-Key header
       - Example: X-API-Key: fhs_1234567890abcdef...
    2. JWT Token: Provide via Authorization header or HttpOnly cookie
       - Example: Authorization: Bearer eyJhbGc...
       - Must have admin role

    **Request Body:**
    JSON array of bills with required fields:
    - employee_id (required): Employee ID
    - term_code (required): Billing term code
    - dorm_code (required): Room code
    - All other billing fields (electricity, water, fees)

    **Automatic Updates:**
    - When bills are imported, the system automatically updates the `dorm_id` field
      in the employees table with the corresponding `dorm_code` from the bill.
    - This ensures employee dormitory information is always synchronized with billing data.

    **Response:**
    - 200: Import summary with created/updated counts
    - 400: Invalid JSON format
    - 403: Forbidden (not admin)
    - 422: Validation errors (invalid employee_id, negative amounts)
    - 500: Server error

    **Example Request:**
    ```json
    {
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
    ```

    **Example Response:**
    ```json
    {
      "success": true,
      "summary": {
        "total_records": 150,
        "created": 120,
        "updated": 30,
        "errors": 0,
        "employees_updated": 145
      },
      "error_details": []
    }
    ```
    """
    logger.info(f"Importing {len(request.bills)} bills (auth: {auth_info.get('auth_type')})")

    try:
        # Convert Pydantic models to dicts for service layer
        bills_data = [bill.model_dump() for bill in request.bills]

        # Call service layer
        result = await dormitory_bill_service.import_bills(db, bills_data)

        logger.info(f"Import complete: {result['summary']}")
        return result

    except HTTPException:
        # Re-raise HTTP exceptions from service layer
        raise

    except Exception as e:
        logger.error(f"Unexpected error during import: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to import bills: {str(e)}"
        )

@router.get(
    "/search",
    response_model=SearchResponse,
    summary="Search dormitory bills",
    description="Search dormitory billing records with filters and pagination (authenticated users)"
)
async def search_dormitory_bills(
    employee_id: Optional[str] = Query(None, description="Filter by employee ID (exact match, e.g., 'VNW0012345')"),
    term_code: Optional[str] = Query(None, description="Filter by term code (exact match, e.g., '25A')"),
    dorm_code: Optional[str] = Query(None, description="Filter by room code (exact match, e.g., 'A01')"),
    min_amount: Optional[float] = Query(None, ge=0, description="Minimum total amount filter (VND)"),
    max_amount: Optional[float] = Query(None, ge=0, description="Maximum total amount filter (VND)"),
    page: int = Query(1, ge=1, description="Page number (1-indexed, default: 1)"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page (default: 50, max: 100)"),
    current_user: dict = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Search dormitory bills with flexible filters.

    **Access:** Authenticated users only (blocks guest users)

    **Query Parameters:**
    - employee_id: Exact match on employee ID (e.g., 'VNW0012345')
    - term_code: Exact match on billing term (e.g., '25A')
    - dorm_code: Exact match on room code (e.g., 'A01')
    - min_amount: Minimum total amount (VND)
    - max_amount: Maximum total amount (VND)
    - page: Page number starting from 1
    - page_size: Number of records per page (1-100)

    **Response:**
    - 200: Paginated search results
    - 403: Forbidden (guest user not allowed)
    - 422: Invalid query parameters (page < 1 or page_size > 100)
    - 500: Server error

    **Example Response:**
    ```json
    {
      "total": 250,
      "page": 1,
      "page_size": 50,
      "results": [
        {
          "bill_id": 1234,
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
          "total_amount": 1876500,
          "created_at": "2026-01-12T03:00:00Z",
          "updated_at": null
        }
      ]
    }
    ```
    """
    logger.info(f"User {current_user.get('localId')} searching bills: employee_id={employee_id}, term_code={term_code}, dorm_code={dorm_code}, min_amount={min_amount}, max_amount={max_amount}, page={page}, page_size={page_size}")

    try:
        # Call service layer
        result = await dormitory_bill_service.search_bills(
            db=db,
            employee_id=employee_id,
            term_code=term_code,
            dorm_code=dorm_code,
            min_amount=min_amount,
            max_amount=max_amount,
            page=page,
            page_size=page_size
        )

        logger.info(f"Search complete: returned {len(result['results'])} results (total: {result['total']})")
        return result

    except HTTPException:
        # Re-raise HTTP exceptions from service layer
        raise

    except Exception as e:
        logger.error(f"Unexpected error during search: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search bills: {str(e)}"
        )
