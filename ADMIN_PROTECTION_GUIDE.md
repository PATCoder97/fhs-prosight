# Admin Protection System - Complete Implementation Guide

## 🎯 Overview

This guide documents the complete admin protection and role-based access control (RBAC) system implemented in the FHS ProSight application.

## 📊 User Roles

The system supports three user roles with different access levels:

| Role | Access Level | Description |
|------|-------------|-------------|
| **guest** | Limited | Can only access `/welcome` page. Must request upgrade to access app features. |
| **user** | Standard | Full access to application features except admin-only pages. |
| **admin** | Full | Complete access including user management and system configuration. |

## 🏗️ Architecture

### Three-Layer Defense Strategy

```
Layer 1: Global Middleware (auth.global.js)
   ↓ Intercepts ALL route changes
   ↓ Checks authentication and role requirements
   ↓ Redirects unauthorized access attempts

Layer 2: Page-Level Composables
   ↓ useGuestProtection() - Blocks guest users
   ↓ useAdminProtection() - Allows only admins
   ↓ Runs on component mount

Layer 3: Backend API Protection
   ↓ require_role() dependency injection
   ↓ Validates JWT tokens
   ↓ Enforces role requirements on endpoints
```

## 📁 Key Files

### Frontend

#### 1. Middleware - Global Auth Guard
**File:** [frontend/src/middleware/auth.global.js](frontend/src/middleware/auth.global.js)

Runs on every route change:
- Checks if user is authenticated
- Validates user role against route requirements
- Handles redirects for unauthorized access

```javascript
// Public routes (no auth required)
const publicRoutes = ['/login', '/auth-callback', '/welcome']

// Admin-only routes
const adminRoutes = ['/user-manager']
```

#### 2. Composables - Page Protection

**File:** [frontend/src/composables/useGuestProtection.js](frontend/src/composables/useGuestProtection.js)

Protects regular pages from guest users:
```javascript
import { useGuestProtection } from '@/composables/useGuestProtection'
useGuestProtection()  // Add to any page that guests shouldn't access
```

**File:** [frontend/src/composables/useAdminProtection.js](frontend/src/composables/useAdminProtection.js)

Restricts pages to admin users only:
```javascript
import { useAdminProtection } from '@/composables/useAdminProtection'
useAdminProtection()  // Add to admin-only pages
```

#### 3. User Manager Page
**File:** [frontend/src/pages/user-manager.vue](frontend/src/pages/user-manager.vue)

Admin dashboard for managing users:
- View all registered users
- Update user roles (guest → user → admin)
- Filter by email, provider, localId
- Real-time updates via API integration

### Backend

#### 1. User Management API
**File:** [backend/app/routers/users.py](backend/app/routers/users.py)

Endpoints:
- `GET /users` - List all users (admin only)
- `PUT /users/{user_id}/role` - Update user role (admin only)
- `PUT /users/{user_id}/localId` - Assign localId (admin only)

#### 2. Security Module
**File:** [backend/app/core/security.py](backend/app/core/security.py)

```python
from app.core.security import require_role

@router.get("/admin-endpoint")
async def admin_only(current_user: dict = Depends(require_role("admin"))):
    # Only admins can access this endpoint
    pass
```

## 🔐 Access Control Matrix

| User Role | `/login` | `/welcome` | `/` (home) | `/second-page` | `/user-manager` |
|-----------|----------|------------|------------|----------------|-----------------|
| **No auth** | ✅ Access | ❌ → /login | ❌ → /login | ❌ → /login | ❌ → /login |
| **Guest** | ❌ → /welcome | ✅ Access | ❌ → /welcome | ❌ → /welcome | ❌ → /welcome |
| **User** | ❌ → / | ❌ → / | ✅ Access | ✅ Access | ❌ → / + alert |
| **Admin** | ❌ → / | ❌ → / | ✅ Access | ✅ Access | ✅ Access |

## 🚀 How to Use

### Protecting a New Page

#### Option 1: Regular Page (Block Guests Only)

```vue
<!-- pages/my-feature.vue -->
<script setup>
import { useGuestProtection } from '@/composables/useGuestProtection'

// Protect from guest users
useGuestProtection()

// Your page logic
</script>

<template>
  <div>
    <VCard title="My Feature">
      <!-- Content accessible to user + admin -->
    </VCard>
  </div>
</template>
```

#### Option 2: Admin-Only Page

**Step 1:** Add route to middleware
```javascript
// frontend/src/middleware/auth.global.js
const adminRoutes = ['/user-manager', '/system-settings']  // Add new route
```

**Step 2:** Use composable in page
```vue
<!-- pages/system-settings.vue -->
<script setup>
import { useAdminProtection } from '@/composables/useAdminProtection'

// Only admins can access
useAdminProtection()

// Your admin page logic
</script>

<template>
  <div>
    <VCard title="System Settings">
      <!-- Admin-only content -->
    </VCard>
  </div>
</template>
```

### Creating Protected API Endpoints

```python
from fastapi import APIRouter, Depends
from app.core.security import require_role

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/sensitive-data")
async def get_sensitive_data(
    current_user: dict = Depends(require_role("admin"))
):
    """
    Only admins can call this endpoint
    current_user will contain: { user_id, email, role }
    """
    return {"data": "secret"}

@router.post("/update-settings")
async def update_settings(
    settings: dict,
    current_user: dict = Depends(require_role("admin"))
):
    """Admin-only settings update"""
    # Implementation
    pass
```

## 🧪 Testing Guide

### Test Scenario 1: Guest User Access

```bash
# 1. Login as guest user
# 2. Try to access protected pages

Expected Results:
- ✅ Can access /welcome
- ❌ Redirected from / to /welcome
- ❌ Redirected from /second-page to /welcome
- ❌ Redirected from /user-manager to /welcome
```

### Test Scenario 2: Regular User Access

```bash
# 1. Login as regular user (role: user)
# 2. Navigate to different pages

Expected Results:
- ✅ Can access / (home)
- ✅ Can access /second-page
- ❌ Blocked from /user-manager with alert
- ❌ Redirected from /welcome to /
```

### Test Scenario 3: Admin User Access

```bash
# 1. Login as admin user
# 2. Access all pages

Expected Results:
- ✅ Can access / (home)
- ✅ Can access /second-page
- ✅ Can access /user-manager
- ✅ Can update user roles
- ❌ Redirected from /welcome to /
```

### Test Scenario 4: API Protection

```bash
# Test with curl
curl -X GET http://localhost:8000/users \
  -H "Cookie: access_token=<token>"

# Expected:
# - Admin token: 200 OK with user list
# - User token: 403 Forbidden
# - No token: 401 Unauthorized
```

## 🛠️ User Role Management

### Via User Manager Page (UI)

1. Login as admin
2. Navigate to `/user-manager`
3. Click menu (⋮) next to user
4. Select new role: Admin / User / Guest
5. Confirm update

### Via API

```bash
# Update user role
curl -X PUT http://localhost:8000/users/123/role \
  -H "Cookie: access_token=<admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"role": "admin"}'

# Response:
{
  "success": true,
  "message": "Role updated: user → admin",
  "user": {
    "id": 123,
    "email": "user@example.com",
    "role": "admin",
    ...
  }
}
```

### Via Database (Direct)

```sql
-- PostgreSQL
UPDATE users
SET role = 'admin', updated_at = NOW()
WHERE email = 'user@example.com';
```

## 🔧 Configuration

### Adding More Roles

1. Update User model enum (if using strict validation)
2. Add role to middleware checks
3. Create corresponding composable if needed
4. Update backend `require_role()` logic

Example:
```javascript
// frontend/src/middleware/auth.global.js
const managerRoutes = ['/reports', '/analytics']
const isManagerRoute = managerRoutes.some(route => to.path.startsWith(route))

if (isManagerRoute && !['manager', 'admin'].includes(user.role)) {
  return navigateTo('/')
}
```

### Customizing Redirects

```javascript
// frontend/src/composables/useAdminProtection.js
if (user.role !== 'admin') {
  // Option 1: Show toast notification
  toast.error('Bạn không có quyền truy cập')

  // Option 2: Redirect to specific page
  router.push('/unauthorized')

  // Option 3: Show dialog
  showDialog({
    title: 'Access Denied',
    message: 'Please contact admin for access'
  })
}
```

## 📝 API Endpoints Reference

### Authentication
- `GET /auth/login/google` - Get Google OAuth URL
- `GET /auth/login/github` - Get GitHub OAuth URL
- `GET /auth/google/callback` - Handle Google OAuth callback
- `GET /auth/github/callback` - Handle GitHub OAuth callback
- `GET /auth/me` - Get current user info
- `POST /auth/logout` - Logout and clear cookie

### User Management (Admin Only)
- `GET /users` - List all users with filters
- `PUT /users/{user_id}/role` - Update user role
- `PUT /users/{user_id}/localId` - Assign localId

## 🔒 Security Best Practices

1. **Never trust frontend validation alone**
   - Always validate roles on backend
   - Use JWT tokens with role claims
   - Verify tokens on every protected endpoint

2. **Use HttpOnly cookies for tokens**
   - Prevents XSS attacks
   - Tokens not accessible via JavaScript
   - Already implemented in auth flow

3. **Prevent self-demotion**
   - Admins cannot demote themselves
   - Implemented in backend API

4. **Audit user role changes**
   - Log all role updates
   - Track who made the change
   - Timestamp for compliance

5. **Rate limiting on sensitive endpoints**
   - Prevent brute force attacks
   - Limit role update frequency
   - Consider implementing in future

## 🚨 Common Issues & Solutions

### Issue 1: User stuck on welcome page after role upgrade

**Cause:** Frontend localStorage has old user data

**Solution:**
```javascript
// Force refresh user data
const response = await $api('/auth/me')
localStorage.setItem('user', JSON.stringify(response))
window.location.reload()
```

### Issue 2: Admin routes not protected

**Cause:** Route not added to `adminRoutes` array

**Solution:**
```javascript
// frontend/src/middleware/auth.global.js
const adminRoutes = ['/user-manager', '/your-new-route']  // Add here
```

### Issue 3: API returns 403 for admin user

**Cause:** Token doesn't have updated role claim

**Solution:**
- User must logout and login again
- Or implement token refresh endpoint

## 📊 Monitoring & Logging

### Frontend Logs
```javascript
// Check browser console for auth flow
console.log('No user found, redirecting to login')
console.log('Guest user detected, redirecting to welcome page')
console.log('Non-admin user trying to access admin page...')
```

### Backend Logs
```python
# app/core/security.py logs token validation
# Check for 403/401 errors in API logs
```

## 🎓 Next Steps

1. **Add more admin features:**
   - User activity logs
   - Bulk role updates
   - User search and filters

2. **Enhance security:**
   - Add 2FA for admin accounts
   - Implement session timeout
   - Add IP whitelisting for admin routes

3. **Improve UX:**
   - Replace alert() with toast notifications
   - Add loading states
   - Implement optimistic UI updates

4. **Analytics:**
   - Track role changes
   - Monitor access patterns
   - Generate audit reports

## 📚 Related Documentation

- [OAuth Authentication Flow](backend/README.md)
- [API Documentation](backend/docs/api.md)
- [Database Schema](backend/docs/schema.md)
- [Deployment Guide](docs/deployment.md)

## 🤝 Support

For questions or issues:
1. Check this guide first
2. Review code comments in key files
3. Check browser console for frontend errors
4. Check API logs for backend errors
5. Contact development team

---

**Last Updated:** 2026-01-13
**Version:** 1.0.0
**Status:** ✅ Production Ready
