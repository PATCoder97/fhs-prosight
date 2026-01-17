"""
API Keys Management Router

REST API endpoints for managing API keys (admin only).
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.schemas.api_key import (
    ApiKeyCreate,
    ApiKeyCreated,
    ApiKeyResponse,
    ApiKeyListResponse
)
from app.services import api_key_service
from app.database.session import get_db
from app.core.security import require_role

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api-keys",
    tags=["api-keys"]
)


@router.post(
    "",
    response_model=ApiKeyCreated,
    summary="Create a new API key",
    description="Generate a new API key with specified scopes (admin only)"
)
async def create_api_key(
    request: ApiKeyCreate,
    current_user: dict = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new API key for external integrations.

    **Access:** Admin only

    **Available Scopes:**
    - `evaluations:import` - Import evaluation data
    - `dormitory-bills:import` - Import dormitory billing data

    **Important:**
    - The actual API key is only shown ONCE in this response
    - Save it securely - it cannot be retrieved later
    - Use the key in requests via `X-API-Key` header

    **Example Request:**
    ```json
    {
      "name": "HRS Import Service",
      "description": "API key for automated data imports",
      "scopes": ["evaluations:import", "dormitory-bills:import"],
      "expires_days": 365
    }
    ```

    **Example Response:**
    ```json
    {
      "api_key": "fhs_1234567890abcdef...",
      "key_info": {
        "id": "hash123...",
        "name": "HRS Import Service",
        "key_prefix": "fhs_1234",
        "scopes": "evaluations:import,dormitory-bills:import",
        "is_active": true,
        "created_at": "2026-01-17T01:00:00Z"
      }
    }
    ```
    """
    logger.info(f"Admin {current_user.get('localId')} creating API key: {request.name}")

    try:
        result = await api_key_service.create_api_key(
            db=db,
            name=request.name,
            scopes=request.scopes,
            description=request.description,
            expires_days=request.expires_days,
            created_by=current_user.get('localId')
        )

        logger.info(f"API key created: {result['key_info'].name}")
        return result

    except Exception as e:
        logger.error(f"Failed to create API key: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create API key: {str(e)}"
        )


@router.get(
    "",
    response_model=ApiKeyListResponse,
    summary="List all API keys",
    description="Get list of all API keys (admin only)"
)
async def list_api_keys(
    include_inactive: bool = False,
    current_user: dict = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    List all API keys.

    **Access:** Admin only

    **Query Parameters:**
    - include_inactive: Whether to include revoked/inactive keys (default: false)

    **Response:**
    - 200: List of API keys (without actual key values)
    - 403: Forbidden (not admin)
    """
    logger.info(f"Admin {current_user.get('localId')} listing API keys")

    try:
        keys = await api_key_service.list_api_keys(db, include_inactive)
        return {
            "total": len(keys),
            "keys": keys
        }

    except Exception as e:
        logger.error(f"Failed to list API keys: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list API keys: {str(e)}"
        )


@router.delete(
    "/{key_id}",
    summary="Revoke an API key",
    description="Deactivate an API key (admin only)"
)
async def revoke_api_key(
    key_id: str,
    current_user: dict = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Revoke (deactivate) an API key.

    **Access:** Admin only

    **Note:** This deactivates the key but keeps it in database for audit purposes.
    To permanently delete, use DELETE /api-keys/{key_id}/permanent

    **Response:**
    - 200: Key revoked successfully
    - 404: Key not found
    - 403: Forbidden (not admin)
    """
    logger.info(f"Admin {current_user.get('localId')} revoking API key: {key_id}")

    try:
        await api_key_service.revoke_api_key(db, key_id)
        return {"success": True, "message": f"API key {key_id} revoked"}

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to revoke API key: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to revoke API key: {str(e)}"
        )


@router.delete(
    "/{key_id}/permanent",
    summary="Permanently delete an API key",
    description="Permanently delete an API key from database (admin only)"
)
async def delete_api_key(
    key_id: str,
    current_user: dict = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Permanently delete an API key.

    **Access:** Admin only

    **Warning:** This permanently removes the key from database.
    Consider using revoke instead for audit trail.

    **Response:**
    - 200: Key deleted successfully
    - 404: Key not found
    - 403: Forbidden (not admin)
    """
    logger.info(f"Admin {current_user.get('localId')} permanently deleting API key: {key_id}")

    try:
        await api_key_service.delete_api_key(db, key_id)
        return {"success": True, "message": f"API key {key_id} permanently deleted"}

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to delete API key: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete API key: {str(e)}"
        )
