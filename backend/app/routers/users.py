from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from typing import Optional

from app.core.security import require_role
from app.models.user import User
from app.database.session import AsyncSessionLocal
from app.schemas.users import (
    AssignLocalIdRequest,
    UpdateRoleRequest,
    UserResponse,
    UserListResponse,
    UserActionResponse
)

router = APIRouter(prefix="/users", tags=["users"])


@router.put("/{user_id}/localId", response_model=UserActionResponse)
async def assign_local_id(
    user_id: int,
    request: AssignLocalIdRequest,
    current_user: dict = Depends(require_role("admin"))
):
    """
    Admin assigns or updates localId for a user.

    Requires: role = 'admin'

    Args:
        user_id: Target user ID
        request: Request body containing localId
        current_user: Current authenticated admin user

    Returns:
        UserActionResponse with updated user data

    Raises:
        403: If user is not admin
        404: If target user not found
    """
    async with AsyncSessionLocal() as db:
        # Get user
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalars().first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )

        # Update localId
        user.localId = request.localId
        await db.commit()
        await db.refresh(user)

        return UserActionResponse(
            success=True,
            message=f"LocalId '{request.localId}' assigned to user {user.email}",
            user=UserResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                localId=user.localId,
                role=user.role,
                provider=user.provider,
                is_active=user.is_active,
                created_at=user.created_at
            )
        )


@router.put("/{user_id}/role", response_model=UserActionResponse)
async def update_user_role(
    user_id: int,
    request: UpdateRoleRequest,
    current_user: dict = Depends(require_role("admin"))
):
    """
    Admin updates user role.

    Requires: role = 'admin'
    Allowed roles: guest, user, admin

    Args:
        user_id: Target user ID
        request: Request body containing new role
        current_user: Current authenticated admin user

    Returns:
        UserActionResponse with updated user data

    Raises:
        403: If user is not admin
        404: If target user not found
        400: If admin tries to demote themselves
    """
    async with AsyncSessionLocal() as db:
        # Get user
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalars().first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )

        # Prevent self-demotion from admin
        current_user_id = int(current_user.get("user_id"))
        if user.id == current_user_id and request.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote yourself from admin role"
            )

        # Update role
        old_role = user.role
        user.role = request.role
        await db.commit()
        await db.refresh(user)

        return UserActionResponse(
            success=True,
            message=f"Role updated: {old_role} → {request.role}",
            user=UserResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                localId=user.localId,
                role=user.role,
                provider=user.provider,
                is_active=user.is_active,
                created_at=user.created_at
            )
        )


@router.get("", response_model=UserListResponse)
async def list_users(
    localId: Optional[str] = None,
    provider: Optional[str] = None,
    email: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(require_role("admin"))
):
    """
    Admin lists users with optional filters.

    Requires: role = 'admin'

    Args:
        localId: Filter by localId (exact match)
        provider: Filter by OAuth provider (exact match)
        email: Filter by email (partial match, case-insensitive)
        limit: Maximum number of results (default: 50)
        offset: Number of results to skip (default: 0)
        current_user: Current authenticated admin user

    Returns:
        UserListResponse with paginated user list

    Raises:
        403: If user is not admin
    """
    async with AsyncSessionLocal() as db:
        # Build query
        stmt = select(User)

        # Apply filters
        if localId:
            stmt = stmt.where(User.localId == localId)
        if provider:
            stmt = stmt.where(User.provider == provider)
        if email:
            stmt = stmt.where(User.email.ilike(f"%{email}%"))

        # Count total (before pagination)
        count_stmt = select(func.count(User.id))
        if localId:
            count_stmt = count_stmt.where(User.localId == localId)
        if provider:
            count_stmt = count_stmt.where(User.provider == provider)
        if email:
            count_stmt = count_stmt.where(User.email.ilike(f"%{email}%"))

        count_result = await db.execute(count_stmt)
        total = count_result.scalar()

        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)

        # Execute query
        result = await db.execute(stmt)
        users = result.scalars().all()

        return UserListResponse(
            users=[
                UserResponse(
                    id=u.id,
                    email=u.email,
                    full_name=u.full_name,
                    localId=u.localId,
                    role=u.role,
                    provider=u.provider,
                    is_active=u.is_active,
                    created_at=u.created_at
                )
                for u in users
            ],
            total=total,
            limit=limit,
            offset=offset
        )
