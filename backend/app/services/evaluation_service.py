"""
Service layer for evaluation data management.

This module provides business logic for:
1. Excel file upload and import with upsert logic
2. Evaluation search with filters and pagination
3. Response transformation (flat DB rows → nested evaluation groups)
"""

import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
import openpyxl

from app.models.evaluation import Evaluation

logger = logging.getLogger(__name__)


# Excel column mapping (Chinese headers → English database fields)
EXCEL_COLUMN_MAPPING = {
    "評核年月": "term_code",
    "工號": "employee_id",
    "姓名": "employee_name",
    "職等": "job_level",
    "國籍": "nation",
    "部門代碼": "dept_code",
    "部門名稱": "dept_name",
    "職等六碼": "grade_code",
    "職等名稱": "grade_name",
    "初核成績": "init_score",
    "初核評語": "init_comment",
    "初核主管": "init_reviewer",
    "複核成績": "review_score",
    "複核評語": "review_comment",
    "複核主管": "review_reviewer",
    "核定成績": "final_score",
    "核定評語": "final_comment",
    "核定主管": "final_reviewer",
    "經理室初核成績": "mgr_init_score",
    "經理室初核評語": "mgr_init_comment",
    "經理室初核主管": "mgr_init_reviewer",
    "經理室複核成績": "mgr_review_score",
    "經理室複核評語": "mgr_review_comment",
    "經理室複核主管": "mgr_review_reviewer",
    "經理室核定成績": "mgr_final_score",
    "經理室核定評語": "mgr_final_comment",
    "經理室核定主管": "mgr_final_reviewer",
    "請假總日數": "leave_days",
}


async def upload_evaluations_from_excel(
    db: AsyncSession,
    file_path: str
) -> dict:
    """
    Parse Excel file and import/update evaluation records.

    Args:
        db: Database session
        file_path: Path to Excel file (.xlsx)

    Returns:
        dict with upload summary:
        {
            "success": True,
            "summary": {
                "total_rows": 150,
                "created": 120,
                "updated": 30,
                "errors": 0
            },
            "error_details": []
        }

    Raises:
        HTTPException(400): Invalid file format or missing required columns
        HTTPException(500): Unexpected processing error
    """
    logger.info(f"Starting Excel upload from: {file_path}")

    # Initialize counters
    total_rows = 0
    created_count = 0
    updated_count = 0
    error_count = 0
    error_details = []

    try:
        # Open Excel file (read-only mode for performance)
        workbook = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        sheet = workbook.active

        # Read header row
        header_row = next(sheet.iter_rows(min_row=1, max_row=1, values_only=True))
        headers = [str(cell).strip() if cell else "" for cell in header_row]

        # Validate required columns exist
        required_columns = ["評核年月", "工號"]
        missing_columns = [col for col in required_columns if col not in headers]
        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing_columns)}"
            )

        # Create column index mapping
        column_indices = {}
        for chinese_name, english_name in EXCEL_COLUMN_MAPPING.items():
            if chinese_name in headers:
                column_indices[english_name] = headers.index(chinese_name)

        logger.info(f"Mapped {len(column_indices)} columns from Excel")

        # Process data rows (starting from row 2)
        for row_num, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
            total_rows += 1

            try:
                # Extract data from row using column indices
                row_data = {}
                for english_name, col_idx in column_indices.items():
                    value = row[col_idx] if col_idx < len(row) else None

                    # Convert value to string (except leave_days which is float)
                    if value is not None:
                        if english_name == "leave_days":
                            try:
                                row_data[english_name] = float(value)
                            except (ValueError, TypeError):
                                row_data[english_name] = None
                        else:
                            row_data[english_name] = str(value).strip()
                    else:
                        row_data[english_name] = None

                # Validate required fields
                if not row_data.get("term_code") or not row_data.get("employee_id"):
                    error_count += 1
                    error_details.append({
                        "row": row_num,
                        "error": "Missing required fields: term_code or employee_id"
                    })
                    continue

                # Check if record exists
                stmt = select(Evaluation).where(
                    Evaluation.term_code == row_data["term_code"],
                    Evaluation.employee_id == row_data["employee_id"]
                )
                result = await db.execute(stmt)
                existing_record = result.scalar_one_or_none()

                if existing_record:
                    # UPDATE existing record
                    for key, value in row_data.items():
                        setattr(existing_record, key, value)
                    updated_count += 1
                    logger.debug(f"Row {row_num}: Updated {row_data['term_code']}/{row_data['employee_id']}")
                else:
                    # INSERT new record
                    new_record = Evaluation(**row_data)
                    db.add(new_record)
                    created_count += 1
                    logger.debug(f"Row {row_num}: Created {row_data['term_code']}/{row_data['employee_id']}")

            except Exception as e:
                error_count += 1
                error_details.append({
                    "row": row_num,
                    "error": str(e)
                })
                logger.warning(f"Row {row_num} error: {e}")
                continue

        # Commit all changes
        await db.commit()
        logger.info(f"Upload complete: {created_count} created, {updated_count} updated, {error_count} errors")

        return {
            "success": True,
            "summary": {
                "total_rows": total_rows,
                "created": created_count,
                "updated": updated_count,
                "errors": error_count
            },
            "error_details": error_details
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Excel upload failed: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process Excel file: {str(e)}"
        )
