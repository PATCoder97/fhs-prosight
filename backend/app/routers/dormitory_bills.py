"""
Dormitory Bills API Router

REST API endpoints for dormitory billing operations.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.dormitory_bill import (
    DormitoryBillImport,
    DormitorySearchResponse as SearchResponse,
    DormitoryImportSummary as ImportSummary
)
from app.services import dormitory_bill_service
from app.database.session import get_db
from app.core.security import require_role, require_authenticated_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/dormitory-bills",
    tags=["dormitory-bills"]
)


@router.post(
    "/import",
    response_model=ImportSummary,
    summary="Import dormitory bills from JSON",
    description="Bulk import dormitory billing data from JSON (admin only)"
)
async def import_dormitory_bills(
    request: DormitoryBillImport,
    current_user: dict = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Import dormitory bills with bulk upsert logic.

    **Access:** Admin only

    **Request Body:**
    JSON array of bills with required fields:
    - employee_id (required): Employee ID
    - term_code (required): Billing term code
    - dorm_code (required): Room code
    - All other billing fields (electricity, water, fees)

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
        "errors": 0
      },
      "error_details": []
    }
    ```
    """
    logger.info(f"Admin {current_user.get('localId')} importing {len(request.bills)} bills")

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
