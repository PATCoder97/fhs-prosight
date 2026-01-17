"""
Evaluations API Router.

Provides 2 endpoints:
1. POST /upload - Upload Excel file to import evaluations (admin only)
2. GET /search - Search evaluations with filters (authenticated users)
"""

import logging
import tempfile
import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.schemas.evaluation import UploadSummary, SearchResponse
from app.services import evaluation_service
from app.database.session import get_db
from app.core.security import require_role, require_authenticated_user, require_api_key

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/evaluations",
    tags=["evaluations"]
)


@router.post(
    "/upload",
    response_model=UploadSummary,
    summary="Upload evaluation Excel file",
    description="Upload Excel file to import/update employee evaluations (requires API key with 'evaluations:import' scope)"
)
async def upload_evaluations(
    file: UploadFile = File(..., description="Excel file (.xlsx or .xls)"),
    api_key_info: dict = Depends(require_api_key("evaluations:import")),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload evaluation data from Excel file.

    **Access:** Requires API key with 'evaluations:import' scope

    **Authentication:**
    - Provide API key via X-API-Key header
    - Example: X-API-Key: fhs_1234567890abcdef...

    **File Requirements:**
    - Format: .xlsx or .xls
    - Max size: 10MB
    - Required columns: 評核年月, 工號

    **Response:**
    - 200: Upload summary with created/updated counts
    - 400: Invalid file format or missing required columns
    - 403: Forbidden (not admin)
    - 413: File too large (>10MB)
    - 500: Processing error

    **Example Response:**
    ```json
    {
      "success": true,
      "summary": {
        "total_rows": 150,
        "created": 120,
        "updated": 30,
        "errors": 0
      },
      "error_details": []
    }
    ```
    """
    logger.info(f"Uploading evaluation file: {file.filename}")

    # Validate file extension
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required"
        )

    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Only .xlsx and .xls files are accepted."
        )

    # Validate file size (max 10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    file_content = await file.read()
    file_size = len(file_content)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is 10MB, but file is {file_size / 1024 / 1024:.2f}MB"
        )

    if file_size == 0:
        raise HTTPException(
            status_code=400,
            detail="Empty file uploaded"
        )

    # Create temp file
    temp_file = None
    temp_path = None

    try:
        # Create temporary file with proper extension
        suffix = '.xlsx' if file.filename.lower().endswith('.xlsx') else '.xls'
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        temp_path = temp_file.name

        # Write uploaded content to temp file
        temp_file.write(file_content)
        temp_file.close()

        logger.info(f"Processing Excel file: {temp_path} ({file_size} bytes)")

        # Call service to process Excel
        result = await evaluation_service.upload_evaluations_from_excel(db, temp_path)

        logger.info(f"Upload complete: {result['summary']}")
        return result

    except HTTPException:
        # Re-raise HTTP exceptions from service layer
        raise

    except Exception as e:
        logger.error(f"Unexpected error during Excel upload: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process Excel file: {str(e)}"
        )

    finally:
        # Clean up temp file
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
                logger.debug(f"Cleaned up temp file: {temp_path}")
            except Exception as e:
                logger.warning(f"Failed to delete temp file {temp_path}: {e}")


@router.get(
    "/search",
    response_model=SearchResponse,
    summary="Search evaluation records",
    description="Search employee evaluations with filters and pagination (authenticated users)"
)
async def search_evaluations_endpoint(
    employee_id: Optional[str] = Query(None, description="Filter by employee ID (exact match, e.g., 'VNW0018983')"),
    term_code: Optional[str] = Query(None, description="Filter by term code (exact match, e.g., '25B')"),
    dept_code: Optional[str] = Query(None, description="Filter by department code (prefix match, e.g., '78' matches '7800', '7810')"),
    page: int = Query(1, ge=1, description="Page number (1-indexed, default: 1)"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page (default: 50, max: 100)"),
    current_user: dict = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Search evaluation records with flexible filters.

    **Access:** Authenticated users only (blocks guest users)

    **Query Parameters:**
    - employee_id: Exact match on employee ID (e.g., 'VNW0018983')
    - term_code: Exact match on evaluation term (e.g., '25B')
    - dept_code: Prefix match on department code (e.g., '78' matches '7800', '7810', '7899')
    - page: Page number starting from 1
    - page_size: Number of records per page (1-100)

    **Response:**
    - 200: Paginated search results with nested evaluation groups
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
          "id": 1,
          "term_code": "25B",
          "employee_id": "VNW0018983",
          "employee_name": "Nguyen Van A",
          "dept_code": "7800",
          "dept_name": "IT Department",
          "dept_evaluation": {
            "init": {"score": "甲", "comment": "Good performance", "reviewer": "MGR001"},
            "review": {"score": "優", "comment": "Excellent", "reviewer": "MGR002"},
            "final": {"score": "優", "comment": "Approved", "reviewer": "MGR003"}
          },
          "mgr_evaluation": {
            "init": {"score": "甲", "comment": "...", "reviewer": "..."},
            "review": {"score": "...", "comment": "...", "reviewer": "..."},
            "final": {"score": "...", "comment": "...", "reviewer": "..."}
          },
          "leave_days": 2.5
        }
      ]
    }
    ```
    """
    logger.info(f"User {current_user.get('localId')} searching evaluations: employee_id={employee_id}, term_code={term_code}, dept_code={dept_code}, page={page}, page_size={page_size}")

    try:
        # Call service layer
        result = await evaluation_service.search_evaluations(
            db=db,
            employee_id=employee_id,
            term_code=term_code,
            dept_code=dept_code,
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
            detail=f"Failed to search evaluations: {str(e)}"
        )
