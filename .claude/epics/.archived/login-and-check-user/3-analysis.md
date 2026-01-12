---
issue: 3
analyzed: 2026-01-08T03:07:06Z
complexity: simple
streams: 2
---

# Analysis: Issue #3 - Update User model và auth service

## Task Overview

Update User model và auth service để support localId field:
- Add localId field to SQLAlchemy model
- Change default role to "guest"
- Update get_or_create_user() to return localId
- Ensure backward compatibility

## Complexity Assessment

**Overall: Simple** (2 files, straightforward changes)

- Estimated effort: 2-3 hours
- Clear requirements
- Depends on Issue #2 (migration) - ✅ Completed

## Work Streams

### Stream 1: User Model Update
**Agent:** General-purpose
**Can start:** Immediately (Issue #2 completed)
**Depends on:** Issue #2 migration

**Scope:**
- Update User model with localId field
- Change default role to "guest"

**Files:**
- `backend/app/models/user.py` (MODIFY)

**Steps:**
1. Read current User model
2. Add localId = Column(String(50), nullable=True, index=True)
3. Change role default from "user" to "guest"
4. Commit changes

### Stream 2: Auth Service Update
**Agent:** General-purpose
**Can start:** After Stream 1
**Depends on:** Stream 1 completion

**Scope:**
- Update get_or_create_user() function
- Ensure localId is returned in response dict
- Handle both existing and new users

**Files:**
- `backend/app/services/auth_service.py` (MODIFY)

**Steps:**
1. Read current auth_service.py
2. Update get_or_create_user() to include localId in return dict
3. Ensure new users get role="guest", localId=None
4. Ensure existing users preserve their role and localId
5. Test function logic
6. Commit changes

## Parallel Opportunities

Streams must run sequentially:
- Stream 2 depends on Stream 1 (model must be updated first)

## Coordination Notes

- This task conflicts with #4 and #5 (all modify auth service)
- Must complete before starting #4
- Work in worktree: ../epic-login-and-check-user/

## Next Steps

1. Start Stream 1 (User Model Update)
2. Start Stream 2 (Auth Service Update)
3. Test with existing auth flow
4. Commit with format: `Issue #3: <change>`
