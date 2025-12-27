"""
User Management Router - Examples for managing user roles
Demonstrates how to use role-based access control in real endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from app.core.security import get_current_user, check_role, get_current_user_from_db
from app.models import User
from app.database.session import AsyncSessionLocal
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/users", tags=["user-management"])


class UserUpdate(BaseModel):
    """Schema for updating user"""
    role: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    
    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """User response schema"""
    id: int
    email: str
    full_name: Optional[str]
    avatar: Optional[str]
    role: str
    is_active: bool
    is_verified: bool
    provider: str
    
    class Config:
        from_attributes = True


# ==================== Public Routes ====================

@router.get("/", response_model=list[UserResponse])
async def list_all_users(
    skip: int = 0,
    limit: int = 100,
):
    """
    List all users (PUBLIC - no auth required)
    
    Use this for user directory, search, etc.
    """
    async with AsyncSessionLocal() as db:
        stmt = select(User).offset(skip).limit(limit)
        result = await db.execute(stmt)
        users = result.scalars().all()
        return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    """
    Get single user by ID (PUBLIC)
    """
    async with AsyncSessionLocal() as db:
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalars().first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found",
            )
        
        return user


# ==================== Moderator+ Routes ====================

@router.post("/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: int,
    new_role: str,
    current_user: dict = Depends(check_role(["mod", "admin"])),
):
    """
    Update user role - MOD+ only
    Shows lock icon in Swagger
    
    Args:
        user_id: User ID to update
        new_role: New role (user, mod, admin)
        
    Allowed roles: mod, admin
    """
    # Validate role
    valid_roles = ["user", "mod", "admin"]
    if new_role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}",
        )
    
    # Only admin can grant admin role
    if new_role == "admin" and current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can grant admin role",
        )
    
    async with AsyncSessionLocal() as db:
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalars().first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found",
            )
        
        old_role = user.role
        user.role = new_role
        await db.commit()
        await db.refresh(user)
        
        # Log the action
        print(f"User {user_id} role changed: {old_role} -> {new_role} by {current_user.get('user_id')}")
        
        return user


@router.post("/{user_id}/status")
async def update_user_status(
    user_id: int,
    is_active: bool,
    current_user: dict = Depends(check_role(["mod", "admin"])),
):
    """
    Activate/Deactivate user - MOD+ only
    
    Args:
        user_id: User ID
        is_active: True to activate, False to deactivate
    """
    async with AsyncSessionLocal() as db:
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalars().first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found",
            )
        
        user.is_active = is_active
        await db.commit()
        await db.refresh(user)
        
        return {
            "id": user.id,
            "email": user.email,
            "is_active": user.is_active,
            "updated_by": current_user.get("user_id"),
        }


# ==================== Admin-Only Routes ====================

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: dict = Depends(check_role(["admin"])),
):
    """
    Delete user - ADMIN only
    
    Args:
        user_id: User ID to delete
    """
    async with AsyncSessionLocal() as db:
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalars().first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found",
            )
        
        await db.delete(user)
        await db.commit()
        
        return {
            "message": f"User {user_id} deleted",
            "deleted_by": current_user.get("user_id"),
        }


@router.post("/verify/{user_id}")
async def verify_user_email(
    user_id: int,
    current_user: dict = Depends(check_role(["admin"])),
):
    """
    Verify user email - ADMIN only
    """
    async with AsyncSessionLocal() as db:
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalars().first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found",
            )
        
        user.is_verified = True
        await db.commit()
        await db.refresh(user)
        
        return {
            "id": user.id,
            "email": user.email,
            "is_verified": user.is_verified,
        }


@router.get("/stats/summary")
async def get_user_stats(
    current_user: dict = Depends(check_role(["admin"])),
):
    """
    Get user statistics - ADMIN only
    """
    async with AsyncSessionLocal() as db:
        # Total users
        total_users = await db.execute(select(User))
        total_count = len(total_users.scalars().all())
        
        # Users by role
        admin_users = await db.execute(select(User).where(User.role == "admin"))
        mod_users = await db.execute(select(User).where(User.role == "mod"))
        regular_users = await db.execute(select(User).where(User.role == "user"))
        
        return {
            "total_users": total_count,
            "admins": len(admin_users.scalars().all()),
            "mods": len(mod_users.scalars().all()),
            "users": len(regular_users.scalars().all()),
            "stats_requested_by": current_user.get("user_id"),
        }
