---
issue: 8
analyzed: 2026-01-08T11:50:00Z
complexity: medium
streams: 3
---

# Analysis: Issue #8 - Integration tests và E2E test plan

## Task Overview

Tạo integration tests và E2E test plan để verify:
- Full OAuth flows (Google + GitHub) end-to-end
- Admin workflows (assign localId, update role)
- Multiple users với cùng localId
- Performance và security requirements

## Complexity Assessment

**Overall: Medium** (2 integration test files + 1 E2E plan)

- Estimated effort: 4-5 hours
- Integration tests với real DB operations
- Mock OAuth APIs
- Depends on Issue #7 (unit tests)

## Work Streams

### Stream 1: OAuth Flow Integration Tests
**Agent:** General-purpose
**Can start:** Immediately
**Depends on:** Issue #7 completed

**Scope:**
- Test Google OAuth new user flow
- Test GitHub OAuth existing user flow
- Test multiple OAuth accounts same localId
- Mock OAuth API responses

**Files:**
- `backend/tests/integration/__init__.py` (CREATE)
- `backend/tests/integration/test_oauth_flow.py` (CREATE)

**Steps:**
1. Create integration test directory
2. Write Google OAuth test (new user)
3. Write GitHub OAuth test (existing user)
4. Test multiple accounts same localId
5. Mock OAuth API calls properly

### Stream 2: Admin Workflow Integration Tests
**Agent:** General-purpose
**Can start:** Immediately (parallel with Stream 1)
**Depends on:** Issue #7 completed

**Scope:**
- Test assign localId workflow
- Test update role workflow
- Test user re-login after changes
- Test JWT token updates

**Files:**
- `backend/tests/integration/test_admin_workflow.py` (CREATE)

**Steps:**
1. Write assign localId workflow test
2. Write update role workflow test
3. Test re-login after admin changes
4. Verify JWT token contains updated data

### Stream 3: E2E Test Plan Documentation
**Agent:** General-purpose
**Can start:** Immediately (parallel with Streams 1, 2)
**Depends on:** None

**Scope:**
- Document all E2E test scenarios
- Step-by-step instructions
- Expected results
- SQL verification queries
- Performance and security tests

**Files:**
- `backend/docs/e2e-test-plan.md` (CREATE)

**Steps:**
1. Document OAuth login scenarios
2. Document admin workflows
3. Document security testing
4. Document performance testing
5. Document rollback testing

## Parallel Opportunities

All streams can run in parallel:
- Stream 1, 2, 3 are independent

## Coordination Notes

- Integration tests use real database (in-memory SQLite for tests)
- OAuth APIs are mocked (no real Google/GitHub calls)
- Work in worktree: ../epic-login-and-check-user/

## Next Steps

1. Start all streams in parallel
2. Run integration tests to verify
3. Commit with format: `Issue #8: <change>`
