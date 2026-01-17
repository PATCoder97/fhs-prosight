"""
API Key Service

Business logic for managing API keys.
"""

import logging
import secrets
import hashlib
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException

from app.models.api_key import ApiKey

logger = logging.getLogger(__name__)


def generate_api_key() -> tuple[str, str, str]:
    """
    Generate a new API key.

    Returns:
        tuple: (full_api_key, key_hash, key_prefix)
            - full_api_key: The actual key to give to user (fhs_xxxxx...)
            - key_hash: SHA256 hash to store in database
            - key_prefix: First 12 chars for identification
    """
    # Generate random 32 bytes (64 hex chars)
    random_part = secrets.token_hex(32)

    # Create API key with prefix
    full_key = f"fhs_{random_part}"

    # Hash the key for database storage
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()

    # Extract prefix for identification (first 12 chars)
    key_prefix = full_key[:12]

    return full_key, key_hash, key_prefix


async def create_api_key(
    db: AsyncSession,
    name: str,
    scopes: List[str],
    description: Optional[str] = None,
    expires_days: Optional[int] = None,
    created_by: Optional[str] = None
) -> dict:
    """
    Create a new API key.

    Args:
        db: Database session
        name: Friendly name for the key
        scopes: List of scopes (e.g., ["evaluations:import", "dormitory-bills:import"])
        description: Optional description
        expires_days: Number of days until expiration (None = never expires)
        created_by: Employee ID who created this key

    Returns:
        dict: {
            "api_key": str (the actual key - only shown once!),
            "key_info": ApiKey object
        }
    """
    logger.info(f"Creating API key: {name}")

    # Generate API key
    full_key, key_hash, key_prefix = generate_api_key()

    # Calculate expiration date
    expires_at = None
    if expires_days:
        expires_at = datetime.utcnow() + timedelta(days=expires_days)

    # Create database record
    api_key = ApiKey(
        id=key_hash,
        name=name,
        description=description,
        key_prefix=key_prefix,
        scopes=",".join(scopes),
        is_active=True,
        created_by=created_by,
        expires_at=expires_at
    )

    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    logger.info(f"API key created: {name} (prefix: {key_prefix})")

    return {
        "api_key": full_key,
        "key_info": api_key
    }


async def list_api_keys(
    db: AsyncSession,
    include_inactive: bool = False
) -> List[ApiKey]:
    """
    List all API keys.

    Args:
        db: Database session
        include_inactive: Whether to include inactive keys

    Returns:
        List of ApiKey objects
    """
    query = select(ApiKey)

    if not include_inactive:
        query = query.where(ApiKey.is_active == True)

    query = query.order_by(ApiKey.created_at.desc())

    result = await db.execute(query)
    return result.scalars().all()


async def get_api_key(
    db: AsyncSession,
    key_id: str
) -> Optional[ApiKey]:
    """
    Get API key by ID.

    Args:
        db: Database session
        key_id: API key hash (ID)

    Returns:
        ApiKey object or None
    """
    stmt = select(ApiKey).where(ApiKey.id == key_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def revoke_api_key(
    db: AsyncSession,
    key_id: str
) -> bool:
    """
    Revoke (deactivate) an API key.

    Args:
        db: Database session
        key_id: API key hash (ID)

    Returns:
        bool: True if revoked successfully

    Raises:
        HTTPException: 404 if key not found
    """
    api_key = await get_api_key(db, key_id)

    if not api_key:
        raise HTTPException(
            status_code=404,
            detail=f"API key not found: {key_id}"
        )

    api_key.is_active = False
    await db.commit()

    logger.info(f"API key revoked: {api_key.name} (prefix: {api_key.key_prefix})")
    return True


async def delete_api_key(
    db: AsyncSession,
    key_id: str
) -> bool:
    """
    Permanently delete an API key.

    Args:
        db: Database session
        key_id: API key hash (ID)

    Returns:
        bool: True if deleted successfully

    Raises:
        HTTPException: 404 if key not found
    """
    api_key = await get_api_key(db, key_id)

    if not api_key:
        raise HTTPException(
            status_code=404,
            detail=f"API key not found: {key_id}"
        )

    await db.delete(api_key)
    await db.commit()

    logger.info(f"API key deleted: {api_key.name} (prefix: {api_key.key_prefix})")
    return True
