---
issue: 7
analyzed: 2026-01-08T11:05:00Z
complexity: medium
streams: 4
---

# Analysis: Issue #7 - Viết unit tests

## Task Overview

Viết comprehensive unit tests để cover:
- get_or_create_user() function với localId support
- JWT token creation/validation với localId và oauth_provider
- Admin endpoints (assign localId, update role, list users)
- Role checking và authorization
- Input validation

Target: > 80% test coverage

## Complexity Assessment

**Overall: Medium** (3 test files, mocking required)

- Estimated effort: 5-6 hours
- Test setup với pytest, pytest-asyncio
- Mock database và dependencies
- Depends on Issue #6 (admin endpoints)

## Work Streams

### Stream 1: Test Setup and Configuration
**Agent:** General-purpose
**Can start:** Immediately
**Depends on:** Issue #6 completed

**Scope:**
- Create tests directory structure
- Create conftest.py with fixtures
- Setup pytest configuration
- Create test database fixtures

**Files:**
- `backend/tests/__init__.py` (CREATE)
- `backend/tests/conftest.py` (CREATE)
- `backend/pytest.ini` (CREATE)

**Steps:**
1. Create tests directory
2. Write conftest.py with:
   - Test database fixture
   - Admin user fixture
   - Regular user fixture
   - JWT token fixtures
3. Create pytest.ini configuration

### Stream 2: JWT Handler Tests
**Agent:** General-purpose
**Can start:** After Stream 1
**Depends on:** Stream 1 completion

**Scope:**
- Test create_access_token() with localId and provider
- Test create_access_token() without localId (backward compat)
- Test verify_token() with new fields
- Test verify_token() with old tokens
- Test token expiration

**Files:**
- `backend/tests/test_jwt_handler.py` (CREATE)

**Steps:**
1. Test token creation with all fields
2. Test token creation without optional fields
3. Test token verification
4. Test backward compatibility
5. Test expiration handling

### Stream 3: Auth Service Tests
**Agent:** General-purpose
**Can start:** After Stream 1
**Depends on:** Stream 1 completion

**Scope:**
- Test get_or_create_user() creates new user correctly
- Test get_or_create_user() retrieves existing user
- Test new user has role='guest', localId=None
- Test existing user preserves role and localId
- Mock database operations

**Files:**
- `backend/tests/test_auth_service.py` (CREATE)

**Steps:**
1. Test new user creation
2. Test existing user retrieval
3. Test default values (guest role, null localId)
4. Test preserving existing data

### Stream 4: Admin Endpoints Tests
**Agent:** General-purpose
**Can start:** After Stream 1
**Depends on:** Stream 1 completion

**Scope:**
- Test PUT /users/{id}/localId as admin
- Test PUT /users/{id}/localId as non-admin (403)
- Test PUT /users/{id}/role as admin
- Test PUT /users/{id}/role validation
- Test PUT /users/{id}/role self-demotion prevention
- Test GET /users as admin
- Test GET /users with filters
- Test GET /users as non-admin (403)

**Files:**
- `backend/tests/test_admin_endpoints.py` (CREATE)

**Steps:**
1. Test assign localId endpoint
2. Test update role endpoint
3. Test list users endpoint
4. Test authorization (403 for non-admin)
5. Test input validation
6. Test filters and pagination

## Parallel Opportunities

After Stream 1 completes:
- Stream 2, 3, 4 can run in parallel (independent test files)

## Coordination Notes

- All tests depend on Stream 1 (test setup)
- Tests use mocked database (no real DB required)
- Work in worktree: ../epic-login-and-check-user/

## Next Steps

1. Start Stream 1 (Test Setup)
2. Start Streams 2, 3, 4 in parallel (after Stream 1)
3. Run tests to verify all pass
4. Commit with format: `Issue #7: <change>`
