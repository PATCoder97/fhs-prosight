---
issue: 5
analyzed: 2026-01-08T06:07:48Z
complexity: medium
streams: 2
---

# Analysis: Issue #5 - Update OAuth callback handlers

## Task Overview

Update OAuth callback handlers to integrate all previous changes:
- Pass localId and provider to create_access_token()
- Update response schemas to include localId
- Ensure Google and GitHub callbacks return consistent format

## Complexity Assessment

**Overall: Medium** (2 files, integration work)

- Estimated effort: 3-4 hours
- Integrates changes from #2, #3, #4
- Two OAuth providers to update
- Schema updates needed
- Depends on #2, #3, #4 - ✅ All Completed

## Work Streams

### Stream 1: Schema Updates
**Agent:** General-purpose
**Can start:** Immediately
**Depends on:** Issues #2, #3, #4

**Scope:**
- Update SocialLoginUser schema to include localId field
- Ensure Pydantic model validates correctly

**Files:**
- `backend/app/schemas/auth.py` (MODIFY)

**Steps:**
1. Read current schemas
2. Add localId: Optional[str] = None to SocialLoginUser
3. Verify LoginResponse schema is compatible
4. Commit changes

### Stream 2: OAuth Callback Updates
**Agent:** General-purpose
**Can start:** After Stream 1
**Depends on:** Stream 1 completion

**Scope:**
- Update handle_google_callback() to pass localId and provider
- Update handle_github_callback() to pass localId and provider
- Ensure consistent response format

**Files:**
- `backend/app/services/auth_service.py` (MODIFY)

**Steps:**
1. Read current auth_service.py
2. Update handle_google_callback():
   - Pass localId=user_data.get("localId") to create_access_token()
   - Pass provider="google" to create_access_token()
   - Include localId in SocialLoginUser response
3. Update handle_github_callback():
   - Pass localId=user_data.get("localId") to create_access_token()
   - Pass provider="github" to create_access_token()
   - Include localId in SocialLoginUser response
4. Test integration
5. Commit changes

## Parallel Opportunities

Streams must run sequentially:
- Stream 2 depends on Stream 1 (schema must be updated first)

## Coordination Notes

- This task integrates all previous work (#2, #3, #4)
- Conflicts with #3 and #4 (same files)
- Must be done before #6 (testing)
- Work in worktree: ../epic-login-and-check-user/

## Next Steps

1. Start Stream 1 (Schema Updates)
2. Start Stream 2 (OAuth Callback Updates)
3. Test full OAuth flow
4. Commit with format: `Issue #5: <change>`
