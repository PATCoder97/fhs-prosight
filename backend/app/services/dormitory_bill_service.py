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

        # Step 6: Commit all changes
        await db.commit()
        logger.info(f"Import complete: {created_count} created, {updated_count} updated, {error_count} errors")

        return {
            "success": True,
            "summary": {
                "total_records": total_records,
                "created": created_count,
                "updated": updated_count,
                "errors": error_count
            },
            "error_details": error_details
        }

    except Exception as e:
        await db.rollback()
        logger.error(f"Import failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")
