---
issue: 5
stream: oauth-callback-updates
started: 2026-01-08T10:15:00Z
updated: 2026-01-08T10:30:00Z
status: completed
---

# Stream 2: OAuth Callback Updates

## Scope
Update OAuth callback handlers to integrate localId and provider:
- Modify handle_google_callback() to pass localId and provider
- Modify handle_github_callback() to pass localId and provider
- Ensure consistent response format

## Files Modified
- `backend/app/services/auth_service.py` (MODIFY)

## Progress

### Completed Steps

1. **Read current auth_service.py**
   - Reviewed handle_google_callback() implementation
   - Reviewed handle_github_callback() implementation

2. **Updated handle_google_callback()**
   - Added `localId=user_data.get("localId")` parameter to create_access_token()
   - Added `provider="google"` parameter to create_access_token()
   - Added `localId=user_data.get("localId")` to SocialLoginUser response

3. **Updated handle_github_callback()**
   - Added `localId=user_data.get("localId")` parameter to create_access_token()
   - Added `provider="github"` parameter to create_access_token()
   - Added `localId=user_data.get("localId")` to SocialLoginUser response

### Changes Made

**File: backend/app/services/auth_service.py**

**Google Callback:**
```python
# Tạo token truy cập
access_token = create_access_token(
    user_id=str(user_data["id"]),
    full_name=user_data["full_name"],
    role=user_data["role"],
    localId=user_data.get("localId"),  # NEW
    provider="google",  # NEW
    scope="access",
)

# Format response theo schema
user = SocialLoginUser(
    id=user_data["id"],
    social_id=user_data["social_id"],
    provider=user_data["provider"],
    email=user_data["email"],
    full_name=user_data["full_name"],
    avatar=user_data["avatar"],
    role=user_data["role"],
    localId=user_data.get("localId"),  # NEW
    is_active=user_data["is_active"],
    is_verified=user_data["is_verified"],
    is_new_user=user_data["id"] == 0,
)
```

**GitHub Callback:**
```python
# Tạo token truy cập
access_token = create_access_token(
    user_id=str(user_data["id"]),
    full_name=user_data["full_name"],
    role=user_data["role"],
    localId=user_data.get("localId"),  # NEW
    provider="github",  # NEW
    scope="access",
)

user = SocialLoginUser(
    id=user_data["id"],
    social_id=user_data["social_id"],
    provider=user_data["provider"],
    email=user_data["email"],
    full_name=user_data["full_name"],
    avatar=user_data["avatar"],
    role=user_data["role"],
    localId=user_data.get("localId"),  # NEW
    is_active=user_data["is_active"],
    is_verified=user_data["is_verified"],
    is_new_user=user_data["id"] == 0,
)
```

### Commit Details

**Commit hash:** 54b8b4d
**Message:** Issue #5: Update OAuth callback handlers to integrate localId and provider

## Status: COMPLETED

OAuth callbacks successfully updated:
- ✅ Google callback passes localId and provider="google" to JWT
- ✅ GitHub callback passes localId and provider="github" to JWT
- ✅ Both callbacks include localId in response
- ✅ Consistent response format between providers
- ✅ Integrates changes from Issues #2, #3, #4
- ✅ Changes committed to epic branch
- ✅ Ready for testing in Issue #6
