---
issue: 6
started: 2026-01-08T10:35:00Z
updated: 2026-01-08T11:00:00Z
status: completed
---

# Issue #6: Add Admin Endpoints Implementation

## Scope

Create protected admin endpoints for user management:
- PUT /users/{user_id}/localId - Assign/update localId
- PUT /users/{user_id}/role - Update user role
- GET /users - List users with filters and pagination

## Files Created

1. **backend/app/core/security.py**
   - `get_current_user()` dependency - Extract and verify JWT from Authorization header
   - `require_role()` decorator factory - Check user has required role
   - HTTPBearer security scheme

2. **backend/app/routers/users.py**
   - `PUT /{user_id}/localId` - Admin assign localId endpoint
   - `PUT /{user_id}/role` - Admin update role endpoint
   - `GET /` - Admin list users endpoint with filters

3. **backend/app/schemas/users.py**
   - `AssignLocalIdRequest` - Validation for localId (alphanumeric only, max 50 chars)
   - `UpdateRoleRequest` - Validation for role (must be guest/user/admin)
   - `UserResponse` - User data response model
   - `UserListResponse` - Paginated user list response
   - `UserActionResponse` - Generic action response with user data

## Files Modified

1. **backend/app/main.py**
   - Imported users router
   - Registered users router with /api prefix

2. **backend/app/schemas/__init__.py**
   - Exported all user-related schemas

## Implementation Details

### Security Layer (security.py)

**get_current_user():**
- Extracts JWT token from Authorization: Bearer header
- Verifies token using verify_token() from jwt_handler
- Returns decoded payload (user info)
- Raises 401 if token invalid/expired

**require_role():**
- Decorator factory that checks user role
- Usage: `Depends(require_role("admin"))`
- Returns user payload if role matches
- Raises 403 if insufficient permissions

### Endpoint 1: Assign LocalId

**Route:** `PUT /api/users/{user_id}/localId`

**Authorization:** Admin only (403 if not admin)

**Request Body:**
```json
{
  "localId": "VNW0014732"
}
```

**Validation:**
- localId: 1-50 chars, alphanumeric only
- Regex: `^[A-Za-z0-9]+$`

**Response:**
```json
{
  "success": true,
  "message": "LocalId 'VNW0014732' assigned to user example@email.com",
  "user": {
    "id": 123,
    "email": "example@email.com",
    "full_name": "User Name",
    "localId": "VNW0014732",
    "role": "user",
    "provider": "google",
    "is_active": true,
    "created_at": "2026-01-08T10:00:00Z"
  }
}
```

**Error Cases:**
- 404: User not found
- 400: Invalid localId format
- 403: Not admin

### Endpoint 2: Update Role

**Route:** `PUT /api/users/{user_id}/role`

**Authorization:** Admin only (403 if not admin)

**Request Body:**
```json
{
  "role": "admin"
}
```

**Validation:**
- role: Must be one of ["guest", "user", "admin"]
- Pattern: `^(guest|user|admin)$`

**Safety Check:**
- Prevents admin from demoting themselves
- Returns 400 if admin tries to change own role to non-admin

**Response:**
```json
{
  "success": true,
  "message": "Role updated: user → admin",
  "user": { ... }
}
```

**Error Cases:**
- 404: User not found
- 400: Self-demotion attempt, invalid role
- 403: Not admin

### Endpoint 3: List Users

**Route:** `GET /api/users`

**Authorization:** Admin only (403 if not admin)

**Query Parameters:**
- `localId` (optional): Filter by exact localId match
- `provider` (optional): Filter by OAuth provider (google/github)
- `email` (optional): Filter by email (partial match, case-insensitive)
- `limit` (default: 50): Max results per page
- `offset` (default: 0): Number of results to skip

**Example Request:**
```
GET /api/users?provider=google&limit=20&offset=0
```

**Response:**
```json
{
  "users": [
    {
      "id": 1,
      "email": "user1@example.com",
      "full_name": "User One",
      "localId": "VNW001",
      "role": "user",
      "provider": "google",
      "is_active": true,
      "created_at": "2026-01-01T00:00:00Z"
    },
    ...
  ],
  "total": 150,
  "limit": 20,
  "offset": 0
}
```

**Features:**
- Filters can be combined (AND logic)
- Email filter uses ILIKE for case-insensitive partial match
- Total count reflects filtered results (not all users)
- Pagination with limit/offset

**Error Cases:**
- 403: Not admin

## Commit Details

**Commit hash:** 10fb699
**Message:** Issue #6: Add admin endpoints for user management

## Status: COMPLETED

All acceptance criteria met:
- ✅ Endpoint PUT /users/{user_id}/localId created
- ✅ Endpoint PUT /users/{user_id}/role created
- ✅ Endpoint GET /users created
- ✅ All endpoints require admin role (via require_role decorator)
- ✅ Non-admin users receive 403 Forbidden
- ✅ Input validation: localId alphanumeric, max 50 chars
- ✅ Input validation: role must be guest/user/admin
- ✅ Error messages are clear and descriptive
- ✅ List users has pagination (limit, offset)
- ✅ List users has filters (localId, provider, email)
- ✅ Prevent self-demotion from admin
- ✅ Code has docstrings and type hints
- ✅ All schemas use Pydantic validation
- ✅ Router registered in main app

Ready for testing in Issue #7.
