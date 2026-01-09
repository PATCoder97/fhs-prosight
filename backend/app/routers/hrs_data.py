"""
HRS Data API Router.

Provides 4 endpoints for salary queries:
1. GET /salary - View own salary (authenticated users)
2. GET /salary/history - View salary history with trend (authenticated users)
3. GET /salary/history/{employee_id} - View any employee's salary history (authenticated users)
4. GET /salary/{employee_id} - View any employee's salary (authenticated users)
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.schemas.hrs_data import SalaryResponse, SalaryHistoryResponse
from app.services import hrs_data_service
from app.database.session import get_db
from app.core.security import get_current_user, require_role

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/hrs-data",
    tags=["hrs-data"]
)


@router.get(
    "/salary",
    response_model=SalaryResponse,
    summary="Get own salary",
    description="Get current user's salary for specific month (default: current month)"
)
async def get_own_salary(
    year: int = Query(None, ge=2000, le=2100, description="Year (default: current year)"),
    month: int = Query(None, ge=1, le=12, description="Month (default: current month)"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's salary for specific month.

    **Access:** Authenticated users (any role)

    **Query Parameters:**
    - year: Year (2000-2100), default to current year
    - month: Month (1-12), default to current month

    **Response:**
    - 200: Salary data returned
    - 404: Salary not found for specified month
    - 503: HRS API unavailable

    **Example:**
    ```
    GET /api/hrs-data/salary?year=2024&month=12
    ```
    """
    emp_id = current_user["localId"]

    # Default to current year/month
    if year is None or month is None:
        now = datetime.now()
        year = year or now.year
        month = month or now.month

    logger.info(f"User {emp_id} querying own salary: {year}-{month:02d}")

    try:
        salary = await hrs_data_service.get_employee_salary(
            db, emp_id, year, month
        )
        return salary
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting salary: {e}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="Failed to retrieve salary data. Please try again later."
        )


@router.get(
    "/salary/history",
    response_model=SalaryHistoryResponse,
    summary="Get salary history with trend",
    description="Get current user's salary history for specified month range with trend analysis"
)
async def get_salary_history(
    year: int = Query(..., ge=2000, le=2100, description="Year"),
    from_month: int = Query(1, ge=1, le=12, description="Start month (default: 1)"),
    to_month: int = Query(12, ge=1, le=12, description="End month (default: 12)"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's salary history with trend analysis.

    **Access:** Authenticated users (any role)

    **Query Parameters:**
    - year: Year (required)
    - from_month: Start month (1-12), default 1
    - to_month: End month (1-12), default 12

    **Response:**
    - 200: Salary history with trend analysis
    - 404: No salary data found for any month in range
    - 422: Invalid month range (from_month > to_month)
    - 503: HRS API unavailable

    **Example:**
    ```
    GET /api/hrs-data/salary/history?year=2024&from_month=1&to_month=12
    ```
    """
    emp_id = current_user["localId"]

    logger.info(
        f"User {emp_id} querying salary history: "
        f"{year}-{from_month:02d} to {year}-{to_month:02d}"
    )

    try:
        history = await hrs_data_service.get_salary_history(
            db, emp_id, year, from_month, to_month
        )
        return history
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting salary history: {e}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="Failed to retrieve salary history. Please try again later."
        )


@router.get(
    "/salary/history/{employee_id}",
    response_model=SalaryHistoryResponse,
    summary="Get employee salary history",
    description="Get any employee's salary history with trend analysis"
)
async def get_employee_salary_history(
    employee_id: str,
    year: int = Query(..., ge=2000, le=2100, description="Year"),
    from_month: int = Query(1, ge=1, le=12, description="Start month (default: 1)"),
    to_month: int = Query(12, ge=1, le=12, description="End month (default: 12)"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get any employee's salary history with trend analysis.

    **Access:** Authenticated users (any role)

    **Path Parameters:**
    - employee_id: Employee ID (e.g., VNW0006204)

    **Query Parameters:**
    - year: Year (required)
    - from_month: Start month (1-12), default 1
    - to_month: End month (1-12), default 12

    **Response:**
    - 200: Salary history with trend analysis
    - 400: Invalid employee ID format
    - 404: No salary data found for any month in range
    - 422: Invalid month range (from_month > to_month)
    - 503: HRS API unavailable

    **Example:**
    ```
    GET /api/hrs-data/salary/history/VNW0006204?year=2024&from_month=1&to_month=12
    ```
    """
    logger.info(
        f"User {current_user['localId']} querying salary history for {employee_id}: "
        f"{year}-{from_month:02d} to {year}-{to_month:02d}"
    )

    try:
        history = await hrs_data_service.get_salary_history(
            db, employee_id, year, from_month, to_month
        )
        return history
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error getting employee {employee_id} salary history: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=503,
            detail="Failed to retrieve salary history. Please try again later."
        )


@router.get(
    "/salary/{employee_id}",
    response_model=SalaryResponse,
    summary="Get employee salary",
    description="Get any employee's salary for specific month"
)
async def get_employee_salary(
    employee_id: str,
    year: int = Query(..., ge=2000, le=2100, description="Year"),
    month: int = Query(..., ge=1, le=12, description="Month"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get any employee's salary for specific month.

    **Access:** Authenticated users (any role)

    **Path Parameters:**
    - employee_id: Employee ID (e.g., VNW0006204)

    **Query Parameters:**
    - year: Year (required)
    - month: Month (1-12, required)

    **Response:**
    - 200: Salary data returned
    - 400: Invalid employee ID format
    - 404: Salary not found or employee doesn't exist
    - 503: HRS API unavailable

    **Example:**
    ```
    GET /api/hrs-data/salary/VNW0006204?year=2024&month=12
    ```
    """
    logger.info(
        f"User {current_user['localId']} querying salary for {employee_id}: "
        f"{year}-{month:02d}"
    )

    try:
        salary = await hrs_data_service.get_employee_salary(
            db, employee_id, year, month
        )
        return salary
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error getting employee {employee_id} salary: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=503,
            detail="Failed to retrieve salary data. Please try again later."
        )
