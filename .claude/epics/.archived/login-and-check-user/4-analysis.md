---
issue: 4
analyzed: 2026-01-08T06:00:44Z
complexity: simple
streams: 1
---

# Analysis: Issue #4 - Extend JWT handler

## Task Overview

Extend JWT handler to include localId and oauth_provider in tokens:
- Add localId and provider parameters to create_access_token()
- Include fields in JWT payload
- Ensure backward compatibility with old tokens
- Update verify_token() to handle missing fields

## Complexity Assessment

**Overall: Simple** (1 file, clear requirements)

- Estimated effort: 2-3 hours
- Single file modification
- Well-defined changes
- Depends on Issue #3 - ✅ Completed

## Work Streams

### Stream 1: JWT Handler Extension
**Agent:** General-purpose
**Can start:** Immediately (Issue #3 completed)
**Depends on:** Issue #3

**Scope:**
- Extend create_access_token() with new parameters
- Update verify_token() for backward compatibility
- Add proper type hints and documentation

**Files:**
- `backend/app/core/jwt_handler.py` (MODIFY)

**Steps:**
1. Read current jwt_handler.py
2. Add localId and provider parameters to create_access_token()
3. Conditionally add fields to payload (only if not None)
4. Update verify_token() to set defaults for missing fields
5. Test token creation and verification
6. Commit changes

**Key Changes:**
- create_access_token() signature: add `localId: Optional[str] = None, provider: Optional[str] = None`
- Payload: conditionally include localId and oauth_provider
- verify_token(): set localId=None and oauth_provider=None for old tokens

## Parallel Opportunities

None - single stream task.

## Coordination Notes

- Conflicts with #3 and #5 (same file area)
- Must complete before #5 (OAuth callbacks need this)
- Work in worktree: ../epic-login-and-check-user/

## Next Steps

1. Start Stream 1 (JWT Handler Extension)
2. Test with sample tokens
3. Commit: `Issue #4: <change>`
