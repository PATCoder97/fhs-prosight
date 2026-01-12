---
issue: 2
analyzed: 2026-01-08T02:40:32Z
complexity: simple
streams: 1
---

# Analysis: Issue #2 - Tạo Alembic migration

## Task Overview

Tạo Alembic migration script để:
- Thêm cột `localId` vào bảng `users`
- Thay đổi default role từ "user" → "guest"
- Thêm unique constraint cho OAuth accounts
- Viết downgrade để rollback

## Complexity Assessment

**Overall: Simple** (1 file, straightforward changes)

- Estimated effort: 2-3 hours
- Single file creation
- Well-defined requirements
- No dependencies on other tasks

## Work Streams

### Stream 1: Migration Implementation (Primary)
**Agent:** Bash
**Can start:** Immediately
**Depends on:** None

**Scope:**
- Create Alembic migration file
- Implement upgrade() function
- Implement downgrade() function
- Test migration up/down

**Files:**
- `alembic/versions/YYYYMMDD_HHMMSS_add_localid_and_fix_role.py` (CREATE)

**Steps:**
1. Check alembic current revision to get `down_revision`
2. Generate migration file with `alembic revision`
3. Write upgrade logic:
   - Add localId column (VARCHAR 50, nullable)
   - Create index on localId
   - Change role default to 'guest'
   - Add unique constraint (provider, social_id)
4. Write downgrade logic (reverse order)
5. Test: `alembic upgrade head`
6. Verify schema changes
7. Test: `alembic downgrade -1`
8. Verify rollback successful

**Acceptance Criteria:**
- Migration file created
- Upgrade/downgrade both work
- Existing users unchanged
- Ready for staging deployment

## Parallel Opportunities

None - this is a single-stream task.

## Risk Assessment

**Low Risk:**
- Migration is additive (no data loss)
- Backward compatible
- Easy to rollback
- Well-tested pattern

**Potential Issues:**
- May need to check if unique constraint already exists
- Migration file naming convention

## Coordination Notes

This task is independent and can be completed without coordination with other tasks.
Task #3 depends on this migration being completed and tested.

## Next Steps

1. Start Stream 1 (Migration Implementation)
2. Work in epic worktree: `../epic-login-and-check-user/`
3. Commit with format: `Issue #2: <specific change>`
4. Update progress in updates folder
