"""
Service layer for HRS data queries and trend analysis.

This module provides business logic for:
1. Single month salary queries with employee info lookup
2. Multi-month salary history with parallel API calls
3. Trend analysis (averages, highest/lowest, significant changes)
4. Employee achievement/evaluation data queries
"""

import asyncio
import logging
from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.models.employee import Employee
from app.integrations.fhs_hrs_client import FHSHRSClient

logger = logging.getLogger(__name__)


async def get_employee_salary(
    db: AsyncSession,
    emp_id: str,
    year: int,
    month: int
) -> dict:
    """
    Get employee salary for specific month.

    Args:
        db: Database session
        emp_id: Employee ID (e.g., "VNW0006204")
        year: Year (e.g., 2024)
        month: Month (1-12)

    Returns:
        dict matching SalaryResponse schema:
        {
            "employee_id": str,
            "employee_name": str,
            "period": {"year": int, "month": int},
            "summary": {...},
            "income": {...},
            "deductions": {...}
        }

    Raises:
        HTTPException(400): Invalid employee ID format
        HTTPException(404): Salary not found
        HTTPException(503): HRS API unavailable
    """
    # Convert emp_id format: VNW0006204 → 6204
    try:
        emp_num = int(emp_id.replace("VNW00", ""))
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid employee ID format: {emp_id}"
        )

    # Query HRS API
    logger.info(f"Fetching salary for {emp_id} ({year}-{month:02d})")
    hrs_client = FHSHRSClient()

    try:
        salary_data = await hrs_client.get_salary_data(emp_num, year, month)
    except Exception as e:
        logger.error(f"HRS API error for {emp_id}: {e}")
        raise HTTPException(
            status_code=503,
            detail="HRS API unavailable"
        )

    if not salary_data:
        raise HTTPException(
            status_code=404,
            detail=f"Salary not found for employee {emp_id} in {year}-{month:02d}"
        )

    # Lookup employee name from database
    employee = await db.get(Employee, emp_id)
    emp_name = employee.name_en if employee else "Unknown"

    if not employee:
        logger.warning(f"Employee {emp_id} not found in database, using 'Unknown'")

    # Return structured response
    return {
        "employee_id": emp_id,
        "employee_name": emp_name,
        "period": {"year": year, "month": month},
        **salary_data  # Includes: summary, income, deductions
    }


async def get_salary_history(
    db: AsyncSession,
    emp_id: str,
    year: int,
    from_month: int,
    to_month: int
) -> dict:
    """
    Get employee salary history with trend analysis.

    Args:
        db: Database session
        emp_id: Employee ID (e.g., "VNW0006204")
        year: Year (e.g., 2024)
        from_month: Start month (1-12)
        to_month: End month (1-12)

    Returns:
        dict matching SalaryHistoryResponse schema:
        {
            "employee_id": str,
            "employee_name": str,
            "period": {"year": int, "month": f"{from_month}-{to_month}"},
            "months": [MonthlySalary],
            "trend": SalaryTrend
        }

    Raises:
        HTTPException(400): Invalid employee ID format
        HTTPException(422): Invalid month range
        HTTPException(404): No salary data found for any month
        HTTPException(503): HRS API unavailable
    """
    # Validate month range
    if from_month > to_month:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid month range: from_month ({from_month}) > to_month ({to_month})"
        )

    if not (1 <= from_month <= 12 and 1 <= to_month <= 12):
        raise HTTPException(
            status_code=422,
            detail=f"Month must be between 1-12: from_month={from_month}, to_month={to_month}"
        )

    # Convert emp_id format: VNW0006204 → 6204
    try:
        emp_num = int(emp_id.replace("VNW00", ""))
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid employee ID format: {emp_id}"
        )

    # Lookup employee name (once, not per month)
    employee = await db.get(Employee, emp_id)
    emp_name = employee.name_en if employee else "Unknown"

    # Fetch salary for all months in parallel
    logger.info(
        f"Fetching salary history for {emp_id} "
        f"({year}-{from_month:02d} to {year}-{to_month:02d})"
    )

    month_range = range(from_month, to_month + 1)
    hrs_client = FHSHRSClient()

    # Parallel API calls using asyncio.gather()
    tasks = [
        hrs_client.get_salary_data(emp_num, year, month)
        for month in month_range
    ]

    try:
        results = await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        logger.error(f"Critical error during parallel salary fetch: {e}")
        raise HTTPException(
            status_code=503,
            detail="HRS API unavailable"
        )

    # Process results
    monthly_data = []
    for month, result in zip(month_range, results):
        if isinstance(result, Exception):
            logger.error(f"Error fetching salary for {emp_id} {year}-{month:02d}: {result}")
            continue

        if result is None:
            logger.warning(f"No salary data for {emp_id} {year}-{month:02d}")
            continue

        monthly_data.append({
            "month": month,
            "summary": result["summary"],
            "income": result["income"],
            "deductions": result["deductions"]
        })

    # Require at least one successful month
    if not monthly_data:
        raise HTTPException(
            status_code=404,
            detail=f"No salary data found for employee {emp_id} in {year}"
        )

    # Calculate trend analysis
    trend = calculate_trend(monthly_data)

    logger.info(
        f"Fetched {len(monthly_data)} months for {emp_id}. "
        f"Average net: {trend['average_net']:,.0f} VND"
    )

    return {
        "employee_id": emp_id,
        "employee_name": emp_name,
        "period": {"year": year, "month": f"{from_month}-{to_month}"},
        "months": monthly_data,
        "trend": trend
    }


def calculate_trend(monthly_data: List[dict]) -> dict:
    """
    Calculate salary trend analysis from monthly data.

    Args:
        monthly_data: List of {month, summary, income, deductions}

    Returns:
        dict matching SalaryTrend schema:
        {
            "average_income": float,
            "average_deductions": float,
            "average_net": float,
            "highest_month": MonthlySalary,
            "lowest_month": MonthlySalary,
            "significant_changes": [SalaryChange]
        }
    """
    if not monthly_data:
        return None

    # Calculate averages
    total_income = sum(m["summary"]["tong_tien_cong"] for m in monthly_data)
    total_deductions = sum(m["summary"]["tong_tien_tru"] for m in monthly_data)
    total_net = sum(m["summary"]["thuc_linh"] for m in monthly_data)
    count = len(monthly_data)

    avg_income = total_income / count
    avg_deductions = total_deductions / count
    avg_net = total_net / count

    # Find highest and lowest net salary months
    sorted_by_net = sorted(
        monthly_data,
        key=lambda m: m["summary"]["thuc_linh"],
        reverse=True
    )
    highest_month = sorted_by_net[0]
    lowest_month = sorted_by_net[-1]

    # Detect significant month-over-month changes
    significant_changes = []
    sorted_by_month = sorted(monthly_data, key=lambda m: m["month"])

    for i in range(1, len(sorted_by_month)):
        prev = sorted_by_month[i - 1]
        curr = sorted_by_month[i]

        prev_net = prev["summary"]["thuc_linh"]
        curr_net = curr["summary"]["thuc_linh"]
        change = curr_net - prev_net
        percentage = (change / prev_net * 100) if prev_net != 0 else 0

        # Significant if: >10% change OR >500K VND change
        if abs(percentage) > 10 or abs(change) > 500000:
            significant_changes.append({
                "from_month": prev["month"],
                "to_month": curr["month"],
                "field": "thuc_linh",
                "change": change,
                "percentage": percentage,
                "direction": "increase" if change > 0 else "decrease"
            })

    return {
        "average_income": avg_income,
        "average_deductions": avg_deductions,
        "average_net": avg_net,
        "highest_month": highest_month,
        "lowest_month": lowest_month,
        "significant_changes": significant_changes
    }


async def get_employee_achievements(
    db: AsyncSession,
    emp_id: str
) -> dict:
    """
    Get employee achievement/evaluation data.

    Args:
        db: Database session
        emp_id: Employee ID (e.g., "VNW0006204")

    Returns:
        dict matching AchievementResponse schema:
        {
            "employee_id": str,
            "employee_name": str,
            "achievements": [{"year": str, "score": str}]
        }

    Raises:
        HTTPException(400): Invalid employee ID format
        HTTPException(404): No achievement data found
        HTTPException(503): HRS API unavailable
    """
    # Convert emp_id format: VNW0006204 → 6204
    try:
        emp_num = int(emp_id.replace("VNW00", ""))
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid employee ID format: {emp_id}"
        )

    # Query HRS API
    logger.info(f"Fetching achievements for {emp_id}")
    hrs_client = FHSHRSClient()

    try:
        achievement_data = await hrs_client.get_achievement_data(emp_num)
    except Exception as e:
        logger.error(f"HRS API error for {emp_id}: {e}")
        raise HTTPException(
            status_code=503,
            detail="HRS API unavailable"
        )

    if not achievement_data:
        raise HTTPException(
            status_code=404,
            detail=f"No achievement data found for employee {emp_id}"
        )

    # Lookup employee name from database
    employee = await db.get(Employee, emp_id)
    emp_name = employee.name_en if employee else "Unknown"

    if not employee:
        logger.warning(f"Employee {emp_id} not found in database, using 'Unknown'")

    # Return structured response
    return {
        "employee_id": emp_id,
        "employee_name": emp_name,
        "achievements": achievement_data
    }
