---
issue: 17
analyzed: 2026-01-09T06:01:03Z
complexity: medium
streams: 2
---

# Issue #17 Analysis: Integration Tests

## Overview
Create comprehensive integration tests for all 6 employee API endpoints with end-to-end testing including authentication, authorization, validation, and database operations.

## Work Streams

### Stream A: Endpoint Integration Tests
**Agent Type**: general-purpose
**Status**: Can start immediately
**Estimated Effort**: 4-6 hours

**Scope:**
- File: `backend/tests/integration/test_employee_endpoints.py`
- 25+ tests covering all 6 endpoints
- Test authentication (401) and authorization (403)
- Test validation (422) and not found (404)
- Test success cases (200)

**Tests Required:**
1. POST /api/employees/sync (6 tests)
   - Success from HRS (admin)
   - Success from COVID with token (admin)
   - COVID without token (400)
   - Non-admin access (403)
   - Invalid employee ID (404)
   - Invalid source (400)

2. POST /api/employees/bulk-sync (5 tests)
   - Success from HRS (admin)
   - Success from COVID with token (admin)
   - Invalid range (422)
   - Non-admin access (403)
   - Returns correct summary

3. GET /api/employees/search (6 tests)
   - Search by name (ILIKE)
   - Search by department_code
   - Search by dorm_id
   - Pagination (skip, limit)
   - Non-admin access (403)
   - Returns EmployeeListResponse

4. GET /api/employees/{emp_id} (3 tests)
   - Get existing employee (200)
   - Get non-existent (404)
   - Non-admin access (403)

5. PUT /api/employees/{emp_id} (4 tests)
   - Update success (200)
   - Update non-existent (404)
   - Non-admin access (403)
   - Invalid data (422)

6. DELETE /api/employees/{emp_id} (3 tests)
   - Delete existing (200)
   - Delete non-existent (200, success=false)
   - Non-admin access (403)

**Fixtures Needed:**
- admin_token: Generate admin JWT
- user_token: Generate non-admin JWT
- test_db: Database session with rollback
- sample_employee: Create test employee

### Stream B: Workflow Integration Tests
**Agent Type**: general-purpose
**Status**: Can start immediately (parallel with A)
**Estimated Effort**: 2-3 hours

**Scope:**
- File: `backend/tests/integration/test_employee_workflows.py`
- 5+ tests covering complete workflows
- Test realistic user scenarios

**Tests Required:**
1. Complete lifecycle: sync → get → update → search → delete
2. Bulk sync → search shows all employees
3. Update employee → get shows updated data
4. Sync existing employee → updates data (no duplicate)
5. Multiple syncs from different sources (HRS then COVID)

**Shared Dependencies:**
- Same fixtures as Stream A (can reuse via conftest.py)
- Both streams need integration test directory

## Dependencies

**External:**
- Task #15 completed ✅
- Test database available ✅
- Admin JWT authentication working ✅

**Internal:**
- Both streams need `backend/tests/integration/` directory
- Both streams need `backend/tests/conftest.py` for shared fixtures

## Coordination

**Parallel Execution:**
- Stream A and B can work simultaneously
- Both will create fixtures in conftest.py (may need coordination)
- Suggest: Stream A creates conftest.py first, Stream B reuses

**File Ownership:**
- Stream A: test_employee_endpoints.py, conftest.py (owns)
- Stream B: test_employee_workflows.py, conftest.py (reads)

## Success Criteria

- [ ] 30+ integration tests total (25+ endpoints, 5+ workflows)
- [ ] All tests pass with real database
- [ ] Database rollback works (no test data persists)
- [ ] Tests cover all 6 endpoints
- [ ] Tests cover auth/authz/validation/errors
- [ ] Test execution time < 30 seconds
- [ ] conftest.py with shared fixtures

## Execution Strategy

**Recommended Approach:**
1. Stream A starts first, creates directory structure and conftest.py
2. Stream B starts in parallel, waits for conftest.py if needed
3. Both streams work independently on their test files
4. Both commit when complete

**Alternative (Simpler):**
- Work sequentially: Stream A → Stream B
- Avoids coordination complexity
