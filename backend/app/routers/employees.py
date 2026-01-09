from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.security import require_role
from app.database.session import get_db
from app.services import employee_service
from app.schemas.employees import (
    SyncEmployeeRequest,
    BulkSyncRequest,
    EmployeeResponse,
    EmployeeListResponse,
    BulkSyncResponse,
    UpdateEmployeeRequest,
    DeleteResponse
)

router = APIRouter(prefix="/employees", tags=["employees"])


@router.post("/sync", response_model=EmployeeResponse, status_code=status.HTTP_200_OK)
async def sync_single_employee(
    request: SyncEmployeeRequest,
    current_user: dict = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Sync single employee from HRS or COVID API.

    Requires: role = 'admin'

    Args:
        request: SyncEmployeeRequest with emp_id, source, and optional token
        current_user: Current authenticated admin user
        db: Database session

    Returns:
        EmployeeResponse with synced employee data

    Raises:
        400: Invalid source or missing token for COVID
        403: User is not admin
        404: Employee not found in external API
    """
    if request.source == "hrs":
        employee = await employee_service.sync_employee_from_hrs(db, request.emp_id)
    elif request.source == "covid":
        if not request.token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token required for COVID source"
            )
        employee = await employee_service.sync_employee_from_covid(
            db, request.emp_id, request.token
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid source: {request.source}. Must be 'hrs' or 'covid'"
        )

    return employee


@router.post("/bulk-sync", response_model=BulkSyncResponse, status_code=status.HTTP_200_OK)
async def bulk_sync_employees(
    request: BulkSyncRequest,
    current_user: dict = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Bulk sync employees from HRS or COVID API.

    Syncs employees from from_id to to_id (inclusive).
    Continues on individual failures.

    Requires: role = 'admin'

    Args:
        request: BulkSyncRequest with from_id, to_id, source, and optional token
        current_user: Current authenticated admin user
        db: Database session

    Returns:
        BulkSyncResponse with summary: {total, success, failed, skipped, errors}

    Raises:
        400: Invalid source, missing token, or invalid range
        403: User is not admin
    """
    result = await employee_service.bulk_sync_employees(
        db,
        from_id=request.from_id,
        to_id=request.to_id,
        source=request.source,
        token=request.token
    )

    return result


@router.get("/search", response_model=EmployeeListResponse, status_code=status.HTTP_200_OK)
async def search_employees(
    name: Optional[str] = Query(None, description="Search in name_tw or name_en (case-insensitive)"),
    department_code: Optional[str] = Query(None, description="Filter by department code"),
    dorm_id: Optional[str] = Query(None, description="Filter by dorm ID"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max number of records to return"),
    current_user: dict = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Search employees with filters and pagination.

    Requires: role = 'admin'

    Args:
        name: Search in name_tw or name_en (partial match, case-insensitive)
        department_code: Exact match on department_code
        dorm_id: Exact match on dorm_id
        skip: Pagination offset (default: 0)
        limit: Max results (default: 100, max: 1000)
        current_user: Current authenticated admin user
        db: Database session

    Returns:
        EmployeeListResponse with items, total, skip, limit

    Raises:
        403: User is not admin
    """
    employees = await employee_service.search_employees(
        db,
        name=name,
        department_code=department_code,
        dorm_id=dorm_id,
        skip=skip,
        limit=limit
    )

    # Get total count with same filters (for pagination)
    # For now, return len(employees) as total (can be optimized with COUNT query)
    total = len(employees)

    return EmployeeListResponse(
        items=employees,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{emp_id}", response_model=EmployeeResponse, status_code=status.HTTP_200_OK)
async def get_employee(
    emp_id: str,
    current_user: dict = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Get employee by ID.

    Requires: role = 'admin'

    Args:
        emp_id: Employee ID (e.g., "VNW0006204")
        current_user: Current authenticated admin user
        db: Database session

    Returns:
        EmployeeResponse with employee data

    Raises:
        403: User is not admin
        404: Employee not found
    """
    employee = await employee_service.get_employee_by_id(db, emp_id)

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee {emp_id} not found"
        )

    return employee


@router.put("/{emp_id}", response_model=EmployeeResponse, status_code=status.HTTP_200_OK)
async def update_employee(
    emp_id: str,
    request: UpdateEmployeeRequest,
    current_user: dict = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Update employee data.

    Requires: role = 'admin'

    Args:
        emp_id: Employee ID (e.g., "VNW0006204")
        request: UpdateEmployeeRequest with fields to update
        current_user: Current authenticated admin user
        db: Database session

    Returns:
        EmployeeResponse with updated employee data

    Raises:
        403: User is not admin
        404: Employee not found
        422: Validation error
    """
    # Convert request to dict, excluding None values
    update_data = request.dict(exclude_unset=True)

    employee = await employee_service.update_employee(db, emp_id, update_data)

    return employee


@router.delete("/{emp_id}", response_model=DeleteResponse, status_code=status.HTTP_200_OK)
async def delete_employee(
    emp_id: str,
    current_user: dict = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete employee.

    Requires: role = 'admin'

    Args:
        emp_id: Employee ID (e.g., "VNW0006204")
        current_user: Current authenticated admin user
        db: Database session

    Returns:
        DeleteResponse with success status and message

    Raises:
        403: User is not admin
        404: Employee not found
    """
    deleted = await employee_service.delete_employee(db, emp_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee {emp_id} not found"
        )

    return DeleteResponse(
        success=True,
        message=f"Employee {emp_id} deleted successfully"
    )
