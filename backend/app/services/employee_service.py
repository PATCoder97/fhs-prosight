from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from typing import Optional, Dict, List
from fastapi import HTTPException, status
import logging

from app.models.employee import Employee
from app.integrations import FHSHRSClient, FHSCovidClient
from app.utils.text_utils import parse_number, chuan_hoa_ten
from app.utils.date_utils import parse_date

logger = logging.getLogger(__name__)

# Initialize clients
hrs_client = FHSHRSClient()
covid_client = FHSCovidClient()


def _map_hrs_to_model(hrs_data: Dict) -> Dict:
    """Map HRS API data to Employee model fields

    Args:
        hrs_data: Dict from FHSHRSClient

    Returns:
        Dict with Employee model fields
    """
    return {
        "id": hrs_data.get("employee_id"),
        "name_tw": hrs_data.get("name_tw"),
        "name_en": chuan_hoa_ten(hrs_data.get("name_en", "")),
        "dob": parse_date(hrs_data.get("dob")),
        "start_date": parse_date(hrs_data.get("start_date")),
        "dept": hrs_data.get("dept"),
        "department_code": hrs_data.get("department_code"),
        "job_title": hrs_data.get("job_title"),
        "job_type": hrs_data.get("job_type"),
        "salary": parse_number(hrs_data.get("salary", "0")),
        "address1": hrs_data.get("address1"),
        "address2": hrs_data.get("address2"),
        "phone1": hrs_data.get("phone1"),
        "phone2": hrs_data.get("phone2"),
        "spouse_name": hrs_data.get("spouse_name"),
    }


def _map_covid_to_model(covid_data: Dict) -> Dict:
    """Map COVID API data to Employee model fields

    Note: COVID API has fewer fields than HRS.
    Only update fields that COVID API provides.

    Args:
        covid_data: Dict from FHSCovidClient

    Returns:
        Dict with Employee model fields (partial)
    """
    return {
        "id": covid_data.get("employee_id"),
        "name_tw": covid_data.get("name_tw"),
        "department_code": covid_data.get("department_code"),
        "phone1": covid_data.get("phone1"),
        "sex": covid_data.get("sex"),
        "identity_number": covid_data.get("identity_number"),
        "dob": parse_date(covid_data.get("dob")),
        "nationality": covid_data.get("nationality"),
    }


async def sync_employee_from_hrs(db: AsyncSession, emp_id: int) -> Employee:
    """Sync single employee from HRS API

    Args:
        db: Database session
        emp_id: Employee ID (e.g., 6204)

    Returns:
        Employee object

    Raises:
        HTTPException: If employee not found in API
    """
    # Fetch from API
    emp_data = await hrs_client.get_employee_info(emp_id)
    if not emp_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee {emp_id} not found in HRS API"
        )

    emp_id_str = emp_data["employee_id"]

    # Check if exists
    existing = await db.get(Employee, emp_id_str)

    if existing:
        # Update existing employee
        logger.info(f"Updating employee from HRS: {emp_id_str}")
        for key, value in _map_hrs_to_model(emp_data).items():
            if key != "id":  # Don't update primary key
                setattr(existing, key, value)
        employee = existing
    else:
        # Create new employee
        logger.info(f"Creating employee from HRS: {emp_id_str}")
        employee = Employee(**_map_hrs_to_model(emp_data))
        db.add(employee)

    await db.commit()
    await db.refresh(employee)
    return employee


async def sync_employee_from_covid(
    db: AsyncSession,
    emp_id: int,
    token: str
) -> Employee:
    """Sync single employee from COVID API

    Args:
        db: Database session
        emp_id: Employee ID (e.g., 6204)
        token: Bearer token for COVID API

    Returns:
        Employee object

    Raises:
        HTTPException: If employee not found or token invalid
    """
    # Fetch from API
    emp_data = await covid_client.get_user_info(emp_id, token)
    if not emp_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee {emp_id} not found in COVID API or invalid token"
        )

    emp_id_str = emp_data["employee_id"]

    # Check if exists
    existing = await db.get(Employee, emp_id_str)

    if existing:
        # Update only COVID API fields (merge, don't overwrite HRS data)
        logger.info(f"Updating employee from COVID: {emp_id_str}")
        covid_fields = _map_covid_to_model(emp_data)
        for key, value in covid_fields.items():
            if key != "id" and value is not None:  # Don't overwrite with None
                setattr(existing, key, value)
        employee = existing
    else:
        # Create new employee (rare case - usually HRS creates first)
        logger.info(f"Creating employee from COVID: {emp_id_str}")
        employee = Employee(**_map_covid_to_model(emp_data))
        db.add(employee)

    await db.commit()
    await db.refresh(employee)
    return employee


async def bulk_sync_employees(
    db: AsyncSession,
    from_id: int,
    to_id: int,
    source: str,
    token: Optional[str] = None
) -> Dict:
    """Bulk sync employees from HRS or COVID API

    Args:
        db: Database session
        from_id: Starting employee ID
        to_id: Ending employee ID
        source: "hrs" or "covid"
        token: Bearer token (required for COVID)

    Returns:
        Dict with summary: {total, success, failed, skipped, errors}
    """
    total = to_id - from_id + 1
    success = 0
    failed = 0
    skipped = 0
    errors = []

    # Fetch from appropriate client
    if source == "hrs":
        logger.info(f"Bulk sync from HRS: {from_id} to {to_id}")
        results = await hrs_client.bulk_get_employees(from_id, to_id)
    elif source == "covid":
        if not token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token is required for COVID API"
            )
        logger.info(f"Bulk sync from COVID: {from_id} to {to_id}")
        results = await covid_client.bulk_get_users(from_id, to_id, token)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid source: {source}. Must be 'hrs' or 'covid'"
        )

    # Process each result
    for idx, emp_data in enumerate(results):
        current_emp_id = from_id + idx

        if emp_data is None:
            # API returned None (employee not found or error)
            skipped += 1
            logger.debug(f"Skipped employee {current_emp_id}: No data from API")
            continue

        try:
            # Map to model
            if source == "hrs":
                mapped_data = _map_hrs_to_model(emp_data)
            else:  # covid
                mapped_data = _map_covid_to_model(emp_data)

            emp_id_str = mapped_data["id"]

            # Upsert
            existing = await db.get(Employee, emp_id_str)

            if existing:
                # Update
                for key, value in mapped_data.items():
                    if key != "id":
                        # For COVID, only update if value is not None
                        if source == "covid" and value is None:
                            continue
                        setattr(existing, key, value)
            else:
                # Create
                new_employee = Employee(**mapped_data)
                db.add(new_employee)

            await db.commit()
            success += 1
            logger.debug(f"Successfully synced employee {emp_id_str}")

        except Exception as e:
            # Log error but continue with other employees
            failed += 1
            error_msg = str(e)
            errors.append({"emp_id": current_emp_id, "error": error_msg})
            logger.error(f"Failed to sync employee {current_emp_id}: {error_msg}")
            # Rollback this transaction
            await db.rollback()

    return {
        "total": total,
        "success": success,
        "failed": failed,
        "skipped": skipped,
        "errors": errors
    }


async def count_employees(
    db: AsyncSession,
    name: Optional[str] = None,
    department_code: Optional[str] = None,
    dorm_id: Optional[str] = None
) -> int:
    """Count total employees matching filters

    Args:
        db: Database session
        name: Search in name_tw or name_en (case-insensitive, partial match)
        department_code: Exact match on department_code
        dorm_id: Exact match on dorm_id

    Returns:
        Total count of matching employees
    """
    query = select(func.count()).select_from(Employee)

    # Apply same filters as search
    if name:
        query = query.where(
            or_(
                Employee.name_tw.ilike(f"%{name}%"),
                Employee.name_en.ilike(f"%{name}%")
            )
        )

    if department_code:
        query = query.where(Employee.department_code == department_code)

    if dorm_id:
        query = query.where(Employee.dorm_id == dorm_id)

    result = await db.execute(query)
    return result.scalar_one()


async def search_employees(
    db: AsyncSession,
    name: Optional[str] = None,
    department_code: Optional[str] = None,
    dorm_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Employee]:
    """Search employees with filters

    Args:
        db: Database session
        name: Search in name_tw or name_en (case-insensitive, partial match)
        department_code: Exact match on department_code
        dorm_id: Exact match on dorm_id
        skip: Offset for pagination
        limit: Max results

    Returns:
        List of Employee objects
    """
    query = select(Employee)

    # Apply filters
    if name:
        # Search in both name_tw and name_en (case-insensitive)
        query = query.where(
            or_(
                Employee.name_tw.ilike(f"%{name}%"),
                Employee.name_en.ilike(f"%{name}%")
            )
        )

    if department_code:
        query = query.where(Employee.department_code == department_code)

    if dorm_id:
        query = query.where(Employee.dorm_id == dorm_id)

    # Order and paginate
    query = query.order_by(Employee.id).offset(skip).limit(limit)

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_employee_by_id(db: AsyncSession, emp_id: str) -> Optional[Employee]:
    """Get employee by ID

    Args:
        db: Database session
        emp_id: Employee ID (e.g., "VNW0006204")

    Returns:
        Employee object or None
    """
    return await db.get(Employee, emp_id)


async def update_employee(
    db: AsyncSession,
    emp_id: str,
    update_data: Dict
) -> Employee:
    """Update employee data

    Args:
        db: Database session
        emp_id: Employee ID
        update_data: Dict with fields to update

    Returns:
        Updated Employee object

    Raises:
        HTTPException: If employee not found
    """
    employee = await db.get(Employee, emp_id)

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee {emp_id} not found"
        )

    # Update fields
    for key, value in update_data.items():
        if key != "id" and hasattr(employee, key):  # Don't update primary key
            setattr(employee, key, value)

    await db.commit()
    await db.refresh(employee)
    return employee


async def delete_employee(db: AsyncSession, emp_id: str) -> bool:
    """Delete employee

    Args:
        db: Database session
        emp_id: Employee ID

    Returns:
        True if deleted, False if not found
    """
    employee = await db.get(Employee, emp_id)

    if not employee:
        return False

    await db.delete(employee)
    await db.commit()
    return True
