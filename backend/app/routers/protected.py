"""
Protected endpoints demo - shows how to use role-based access control
This is a template for protected routes. You can copy patterns here to your actual routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import get_current_user, check_role, get_current_user_from_db
from app.models import User

router = APIRouter(prefix="/protected", tags=["protected-routes"])


# Example 1: Public endpoint (no auth required)
@router.get("/public")
async def public_endpoint():
    """
    Public endpoint - anyone can access
    No lock icon in Swagger
    """
    return {
        "message": "This is a public endpoint",
        "access": "Everyone",
    }


# Example 2: Authenticated endpoint (any role)
@router.get("/me")
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
):
    """
    Get current user info - requires valid JWT token
    Shows lock icon in Swagger - requires Bearer token
    Accessible by: user, mod, admin
    """
    return {
        "message": "You are authenticated!",
        "user_id": current_user.get("user_id"),
        "role": current_user.get("role"),
        "full_name": current_user.get("full_name"),
    }


# Example 3: User-only endpoint
@router.get("/user-area")
async def user_area(
    current_user: dict = Depends(check_role(["user"])),
):
    """
    User area - for regular users only
    Shows lock icon in Swagger - requires Bearer token with 'user' role
    Accessible by: user
    """
    return {
        "message": "Welcome to user area",
        "your_role": current_user.get("role"),
    }


# Example 4: Moderator+ endpoint
@router.get("/mod-panel")
async def mod_panel(
    current_user: dict = Depends(check_role(["mod", "admin"])),
):
    """
    Moderator panel - accessible by mod and admin
    Shows lock icon in Swagger - requires Bearer token with 'mod' or 'admin' role
    Accessible by: mod, admin
    """
    return {
        "message": "Welcome to moderator panel",
        "your_role": current_user.get("role"),
        "features": ["manage_users", "moderate_content"],
    }


# Example 5: Admin-only endpoint
@router.get("/admin-panel")
async def admin_panel(
    current_user: dict = Depends(check_role(["admin"])),
):
    """
    Admin panel - admin only
    Shows lock icon in Swagger - requires Bearer token with 'admin' role
    Accessible by: admin
    """
    return {
        "message": "Welcome to admin panel",
        "your_role": current_user.get("role"),
        "features": ["manage_all", "system_config", "user_roles"],
    }


# Example 6: Get user from database (with full user info)
@router.get("/profile")
async def get_user_profile(
    user: User = Depends(get_current_user_from_db),
):
    """
    Get full user profile from database
    Shows lock icon in Swagger - requires Bearer token
    Accessible by: user, mod, admin
    """
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "avatar": user.avatar,
        "role": user.role,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "provider": user.provider,
        "created_at": user.created_at,
        "last_login": user.last_login,
    }


# Example 7: Modify user role (admin only)
@router.post("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    new_role: str,
    current_user: dict = Depends(check_role(["admin"])),
):
    """
    Update user role - admin only endpoint
    Shows lock icon in Swagger - requires Bearer token with 'admin' role
    Accessible by: admin
    
    Args:
        user_id: User ID to update
        new_role: New role (user, mod, admin)
    """
    # Validate role
    valid_roles = ["user", "mod", "admin"]
    if new_role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}",
        )
    
    # In real implementation, update user role in database
    return {
        "message": f"User {user_id} role updated to {new_role}",
        "updated_by": current_user.get("user_id"),
        "updated_by_role": current_user.get("role"),
    }


# Example 8: List all users (mod+)
@router.get("/users")
async def list_users(
    current_user: dict = Depends(check_role(["mod", "admin"])),
):
    """
    List all users - moderator+ only
    Shows lock icon in Swagger - requires Bearer token with 'mod' or 'admin' role
    Accessible by: mod, admin
    """
    return {
        "message": "User list",
        "requested_by": current_user.get("user_id"),
        "requested_by_role": current_user.get("role"),
        "total_users": 0,  # In real implementation, query from DB
    }


@router.post("/test-token")
async def test_token_info(current_user: dict = Depends(get_current_user)):
    """
    Debug endpoint - shows complete token payload
    Shows lock icon in Swagger - requires Bearer token
    Accessible by: any authenticated user
    """
    return {
        "message": "Token information",
        "token_payload": current_user,
    }
