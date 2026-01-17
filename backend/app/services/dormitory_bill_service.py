"""
Dormitory Bill Service

Business logic for dormitory billing operations including bulk import and search.
"""

import logging
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from fastapi import HTTPException

from app.models.dormitory_bill import DormitoryBill
from app.models.employee import Employee

logger = logging.getLogger(__name__)


async def import_bills(db: AsyncSession, bills: List[Dict]) -> dict:
    """
    Import dormitory bills with bulk upsert logic.

    Args:
        db: Database session
        bills: List of bill dictionaries from JSON

    Returns:
        {
            "success": bool,
            "summary": {"total_records": int, "created": int, "updated": int, "errors": int},
            "error_details": [{"row": int, "error": str}]
        }
    """
    total_records = len(bills)
    created_count = 0
    updated_count = 0
    error_count = 0
    error_details = []

    logger.info(f"Starting import of {total_records} bills")

    try:
        # Step 1: Parse and validate all bills
        valid_bills = []
        for idx, bill_data in enumerate(bills, start=1):
            try:
                # Validate required fields
                if not bill_data.get("employee_id") or not bill_data.get("term_code") or not bill_data.get("dorm_code"):
                    error_count += 1
                    error_details.append({
                        "row": idx,
                        "error": "Missing required fields: employee_id, term_code, or dorm_code"
                    })
                    continue

                valid_bills.append((idx, bill_data))

            except Exception as e:
                error_count += 1
                error_details.append({"row": idx, "error": str(e)})
                logger.warning(f"Row {idx} validation error: {e}")

        logger.info(f"Validated {len(valid_bills)} bills, {error_count} errors")

        if not valid_bills:
            return {
                "success": False,
                "summary": {"total_records": total_records, "created": 0, "updated": 0, "errors": error_count},
                "error_details": error_details
            }

        # Step 2: Validate all employee_id values exist (bulk query)
        employee_ids = list(set(bill_data["employee_id"] for _, bill_data in valid_bills))
        stmt = select(Employee.id).where(Employee.id.in_(employee_ids))
        result = await db.execute(stmt)
        existing_employee_ids = set(row[0] for row in result.fetchall())

        # Filter out bills with invalid employee_id
        validated_bills = []
        for idx, bill_data in valid_bills:
            if bill_data["employee_id"] not in existing_employee_ids:
                error_count += 1
                error_details.append({
                    "row": idx,
                    "error": f"Employee ID '{bill_data['employee_id']}' does not exist"
                })
            else:
                validated_bills.append((idx, bill_data))

        logger.info(f"Employee validation: {len(validated_bills)} valid, {error_count} total errors")

        if not validated_bills:
            return {
                "success": False,
                "summary": {"total_records": total_records, "created": 0, "updated": 0, "errors": error_count},
                "error_details": error_details
            }

        # Step 3: Fetch all existing bills in ONE query
        composite_keys = [(bill_data["employee_id"], bill_data["term_code"], bill_data["dorm_code"])
                          for _, bill_data in validated_bills]

        conditions = []
        for emp_id, term, dorm in composite_keys:
            conditions.append(
                (DormitoryBill.employee_id == emp_id) &
                (DormitoryBill.term_code == term) &
                (DormitoryBill.dorm_code == dorm)
            )

        stmt = select(DormitoryBill).where(or_(*conditions))
        result = await db.execute(stmt)
        existing_bills = result.scalars().all()

        # Create hashmap of existing bills
        existing_map = {
            (bill.employee_id, bill.term_code, bill.dorm_code): bill
            for bill in existing_bills
        }

        logger.info(f"Found {len(existing_map)} existing bills to update")

        # Step 4: Separate into inserts vs updates
        bills_to_insert = []

        for idx, bill_data in validated_bills:
            key = (bill_data["employee_id"], bill_data["term_code"], bill_data["dorm_code"])

            if key in existing_map:
                # UPDATE existing bill
                existing_bill = existing_map[key]
                for field, value in bill_data.items():
                    setattr(existing_bill, field, value)
                updated_count += 1
            else:
                # INSERT new bill
                new_bill = DormitoryBill(**bill_data)
                bills_to_insert.append(new_bill)
                created_count += 1

        # Step 5: Bulk insert new bills
        if bills_to_insert:
            db.add_all(bills_to_insert)
            logger.info(f"Bulk inserting {len(bills_to_insert)} new bills")

        # Step 6: Update employee dorm_id for all bills (both new and updated)
        # Create a mapping of employee_id -> latest dorm_code from the import
        employee_dorm_updates = {}
        for idx, bill_data in validated_bills:
            emp_id = bill_data["employee_id"]
            dorm_code = bill_data["dorm_code"]
            # Keep the latest dorm_code for each employee
            employee_dorm_updates[emp_id] = dorm_code

        # Fetch all employees that need dorm_id updates
        stmt = select(Employee).where(Employee.id.in_(list(employee_dorm_updates.keys())))
        result = await db.execute(stmt)
        employees_to_update = result.scalars().all()

        # Update dorm_id for each employee
        updated_employees = 0
        for employee in employees_to_update:
            new_dorm_code = employee_dorm_updates[employee.id]
            if employee.dorm_id != new_dorm_code:
                employee.dorm_id = new_dorm_code
                updated_employees += 1

        logger.info(f"Updated dorm_id for {updated_employees} employees")

        # Step 7: Commit all changes
        await db.commit()
        logger.info(f"Import complete: {created_count} created, {updated_count} updated, {error_count} errors, {updated_employees} employees updated")

        return {
            "success": True,
            "summary": {
                "total_records": total_records,
                "created": created_count,
                "updated": updated_count,
                "errors": error_count,
                "employees_updated": updated_employees
            },
            "error_details": error_details
        }

    except Exception as e:
        await db.rollback()
        logger.error(f"Import failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


async def search_bills(
    db: AsyncSession,
    employee_id: Optional[str] = None,
    term_code: Optional[str] = None,
    dorm_code: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    page: int = 1,
    page_size: int = 50
) -> dict:
    """
    Search dormitory bills with filters and pagination.

    Args:
        db: Database session
        employee_id: Exact match filter (e.g., 'VNW0012345')
        term_code: Exact match filter (e.g., '25A')
        dorm_code: Exact match filter (e.g., 'A01')
        min_amount: Minimum total_amount filter
        max_amount: Maximum total_amount filter
        page: Page number (1-indexed)
        page_size: Items per page (1-100)

    Returns:
        {
            "total": int,
            "page": int,
            "page_size": int,
            "results": List[DormitoryBillResponse]
        }
    """
    # Validate pagination
    if page < 1:
        raise HTTPException(status_code=422, detail="Page number must be >= 1")
    if page_size < 1 or page_size > 100:
        raise HTTPException(status_code=422, detail="Page size must be between 1 and 100")

    logger.info(f"Searching bills: employee_id={employee_id}, term_code={term_code}, dorm_code={dorm_code}, min_amount={min_amount}, max_amount={max_amount}, page={page}, page_size={page_size}")

    # Build query with filters
    query = select(DormitoryBill)

    if employee_id:
        query = query.where(DormitoryBill.employee_id == employee_id)
    if term_code:
        query = query.where(DormitoryBill.term_code == term_code)
    if dorm_code:
        query = query.where(DormitoryBill.dorm_code == dorm_code)
    if min_amount is not None:
        query = query.where(DormitoryBill.total_amount >= min_amount)
    if max_amount is not None:
        query = query.where(DormitoryBill.total_amount <= max_amount)

    # Count total (before pagination)
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    # Apply sort (term_code DESC, created_at DESC)
    query = query.order_by(DormitoryBill.term_code.desc(), DormitoryBill.created_at.desc())

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    # Execute query
    result = await db.execute(query)
    bills = result.scalars().all()

    logger.info(f"Search complete: found {total} total, returning {len(bills)} results")

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "results": bills
    }
