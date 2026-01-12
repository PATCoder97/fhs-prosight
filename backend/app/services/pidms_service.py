"""
PIDMS Service Layer

Business logic for PIDMS (Product ID Management System) operations.
Orchestrates database operations and external API calls for key management.
"""

import logging
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException

from app.models.pidms_key import PIDMSKey
from app.integrations.pidkey_client import PIDKeyClient

logger = logging.getLogger(__name__)


async def check_and_upsert_keys(
    db: AsyncSession,
    keys_list: List[str],
    pidkey_client: PIDKeyClient
) -> dict:
    """
    Check keys against PIDKey.com and upsert to database.

    Calls PIDKey.com API to validate keys, then inserts new keys or updates
    existing ones in the database. All operations are atomic.

    Args:
        db: Database session
        keys_list: List of product keys (with or without dashes)
        pidkey_client: PIDKey.com API client instance

    Returns:
        {
            "success": bool,
            "summary": {"total_keys": int, "new_keys": int, "updated_keys": int, "errors": int},
            "results": [{"keyname": str, "status": str, "prd": str, "remaining": int}]
        }

    Raises:
        HTTPException: If API call or database operation fails
    """
    try:
        # Step 1: Call PIDKey.com API
        logger.info(f"Checking {len(keys_list)} keys against PIDKey.com API")
        api_response = await pidkey_client.check_keys(keys_list)

        total_keys = len(api_response)
        new_keys = 0
        updated_keys = 0
        errors = 0
        results = []

        # Step 2: Bulk fetch existing keys (optimization)
        keynames = [data.get("keyname") for data in api_response if data.get("keyname")]
        stmt = select(PIDMSKey).where(PIDMSKey.keyname.in_(keynames))
        result = await db.execute(stmt)
        existing_keys_map = {key.keyname: key for key in result.scalars().all()}

        logger.info(f"Found {len(existing_keys_map)} existing keys in database")

        # Step 3: Upsert each key
        new_key_objects = []
        for key_data in api_response:
            keyname = key_data.get("keyname")
            if not keyname:
                logger.warning(f"Skipping key with missing keyname: {key_data}")
                errors += 1
                continue

            if keyname in existing_keys_map:
                # UPDATE existing key
                existing_key = existing_keys_map[keyname]
                for field, value in key_data.items():
                    if hasattr(existing_key, field):
                        setattr(existing_key, field, value)
                updated_keys += 1
                status = "updated"
            else:
                # INSERT new key
                new_key = PIDMSKey(**key_data)
                new_key_objects.append(new_key)
                new_keys += 1
                status = "new"

            results.append({
                "keyname": keyname,
                "keyname_with_dash": key_data.get("keyname_with_dash"),
                "status": status,
                "prd": key_data.get("prd"),
                "remaining": key_data.get("remaining")
            })

        # Bulk insert new keys
        if new_key_objects:
            db.add_all(new_key_objects)

        await db.commit()

        logger.info(
            f"Check complete: {new_keys} new, {updated_keys} updated, {errors} errors"
        )

        return {
            "success": True,
            "summary": {
                "total_keys": total_keys,
                "new_keys": new_keys,
                "updated_keys": updated_keys,
                "errors": errors
            },
            "results": results
        }

    except Exception as e:
        await db.rollback()
        logger.error(f"check_and_upsert_keys failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to check keys: {str(e)}")


async def search_keys(
    db: AsyncSession,
    product: Optional[str] = None,
    min_remaining: Optional[int] = None,
    max_remaining: Optional[int] = None,
    blocked: Optional[int] = None,
    page: int = 1,
    page_size: int = 50
) -> dict:
    """
    Search keys with fuzzy product matching and filters.

    Supports partial product name matching (e.g., "Office" matches all Office products),
    filtering by remaining activations, blocked status, and pagination.

    Args:
        db: Database session
        product: Partial product name for fuzzy matching (case-insensitive)
        min_remaining: Minimum remaining activation count
        max_remaining: Maximum remaining activation count
        blocked: Blocked status filter (-1=not blocked, 1=blocked)
        page: Page number (1-indexed)
        page_size: Items per page (1-100)

    Returns:
        {
            "total": int,
            "page": int,
            "page_size": int,
            "results": List[PIDMSKey]
        }

    Raises:
        HTTPException: If pagination parameters are invalid
    """
    # Validate pagination
    if page < 1:
        raise HTTPException(status_code=422, detail="Page must be >= 1")
    if page_size < 1 or page_size > 100:
        raise HTTPException(status_code=422, detail="Page size must be 1-100")

    logger.info(
        f"Searching keys: product={product}, min_remaining={min_remaining}, "
        f"max_remaining={max_remaining}, blocked={blocked}, page={page}, page_size={page_size}"
    )

    # Build query with filters
    query = select(PIDMSKey)

    if product:
        query = query.where(PIDMSKey.prd.ilike(f"%{product}%"))
    if min_remaining is not None:
        query = query.where(PIDMSKey.remaining >= min_remaining)
    if max_remaining is not None:
        query = query.where(PIDMSKey.remaining <= max_remaining)
    if blocked is not None:
        query = query.where(PIDMSKey.blocked == blocked)

    # Count total (before pagination)
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    # Apply sorting and pagination
    query = query.order_by(PIDMSKey.prd, PIDMSKey.remaining.desc())
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    # Execute query
    result = await db.execute(query)
    keys = result.scalars().all()

    logger.info(f"Search complete: found {total} total, returning {len(keys)} results")

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "results": keys
    }


async def get_product_summary(db: AsyncSession) -> dict:
    """
    Get aggregated statistics grouped by product type.

    Returns statistics for each unique product code including key count,
    total remaining activations, average remaining, and low inventory flag.

    Args:
        db: Database session

    Returns:
        {
            "products": [
                {
                    "prd": str,
                    "key_count": int,
                    "total_remaining": int,
                    "avg_remaining": float,
                    "low_inventory": bool
                }
            ]
        }
    """
    logger.info("Generating product summary statistics")

    stmt = select(
        PIDMSKey.prd,
        func.count(PIDMSKey.id).label("key_count"),
        func.sum(PIDMSKey.remaining).label("total_remaining"),
        func.avg(PIDMSKey.remaining).label("avg_remaining")
    ).group_by(PIDMSKey.prd)

    result = await db.execute(stmt)
    rows = result.all()

    products = []
    for row in rows:
        total_remaining = int(row.total_remaining or 0)
        products.append({
            "prd": row.prd,
            "key_count": row.key_count,
            "total_remaining": total_remaining,
            "avg_remaining": round(row.avg_remaining or 0, 2),
            "low_inventory": total_remaining < 5
        })

    logger.info(f"Product summary complete: {len(products)} product types")

    return {"products": products}
