---
issue: 6
analyzed: 2026-01-08T10:35:00Z
complexity: medium
streams: 3
---

# Analysis: Issue #6 - Thêm admin endpoints

## Task Overview

Tạo protected admin endpoints để quản lý users:
- PUT /users/{user_id}/localId - Admin assign/update localId
- PUT /users/{user_id}/role - Admin thay đổi role
- GET /users - Admin list users với filters

Tất cả endpoints require role = "admin" và có input validation.

## Complexity Assessment

**Overall: Medium** (1 file, 3 endpoints, security concerns)

- Estimated effort: 4-5 hours
- Security-critical (admin-only operations)
- Input validation required
- Depends on Issue #5 (OAuth flow completed)

## Work Streams

### Stream 1: Create Users Router and Schemas
**Agent:** General-purpose
**Can start:** Immediately
**Depends on:** Issue #5 completed

**Scope:**
- Create `backend/app/routers/users.py` file
- Define Pydantic request/response schemas
- Setup router with proper tags

**Files:**
- `backend/app/routers/users.py` (CREATE)
- `backend/app/schemas/users.py` (CREATE - for request/response models)

**Steps:**
1. Create users.py router file
2. Create schemas for AssignLocalIdRequest, UpdateRoleRequest
3. Add input validators (localId alphanumeric, role enum)
4. Setup APIRouter with prefix="/users"

### Stream 2: Implement Admin Endpoints
**Agent:** General-purpose
**Can start:** After Stream 1
**Depends on:** Stream 1 completion

**Scope:**
- Implement PUT /users/{user_id}/localId
- Implement PUT /users/{user_id}/role
- Implement GET /users (with filters and pagination)
- Add authorization checks (admin only)

**Files:**
- `backend/app/routers/users.py` (MODIFY)

**Steps:**
1. Implement assign_local_id endpoint:
   - Check admin role
   - Validate user exists
   - Update localId in database
   - Return success response
2. Implement update_user_role endpoint:
   - Check admin role
   - Validate user exists
   - Prevent self-demotion
   - Update role in database
3. Implement list_users endpoint:
   - Check admin role
   - Build query with filters (localId, provider, email)
   - Add pagination (limit, offset)
   - Return users list with total count

### Stream 3: Register Router in Main App
**Agent:** General-purpose
**Can start:** After Stream 2
**Depends on:** Stream 2 completion

**Scope:**
- Import and register users router in main FastAPI app
- Verify endpoints are accessible

**Files:**
- `backend/app/main.py` (MODIFY)

**Steps:**
1. Import users router
2. Add router to app with app.include_router()
3. Verify routes are registered

## Parallel Opportunities

Streams must run sequentially:
- Stream 2 depends on Stream 1 (router setup)
- Stream 3 depends on Stream 2 (endpoints implementation)

## Coordination Notes

- This task is independent and doesn't conflict with other tasks
- Issue #7 (tests) depends on this being completed
- Work in worktree: ../epic-login-and-check-user/

## Next Steps

1. Start Stream 1 (Create Users Router)
2. Start Stream 2 (Implement Endpoints)
3. Start Stream 3 (Register Router)
4. Commit with format: `Issue #6: <change>`
