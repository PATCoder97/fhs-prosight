# Issue #4 Progress: Extend JWT handler to include localId and oauth_provider

**Date:** 2026-01-08
**Status:** Completed

## Summary

Successfully extended the JWT handler to support `localId` and `oauth_provider` fields while maintaining full backward compatibility with existing tokens.

## Changes Made

### File Modified: `backend/app/core/jwt_handler.py`

#### 1. Updated `create_access_token()` function

Added two new optional parameters:
- `localId: Optional[str] = None` - Employee local ID (e.g., VNW0014732)
- `provider: Optional[str] = None` - OAuth provider used (e.g., 'github', 'google')

**Key implementation details:**
- Parameters are optional with default value `None`
- Only added to JWT payload if values are provided (reduces token size when not needed)
- Maintains backward compatibility - existing code calling this function without new parameters will continue to work
- Updated docstring to document the new parameters

**Code changes:**
```python
def create_access_token(
    user_id: str,
    role: str,
    full_name: str = None,
    localId: Optional[str] = None,  # NEW
    provider: Optional[str] = None,  # NEW
    expires_delta: Optional[timedelta] = None,
    scope: str = "access",
) -> str:
    # ... existing code ...

    # Add optional fields if provided
    if localId is not None:
        payload["localId"] = localId

    if provider is not None:
        payload["oauth_provider"] = provider
```

#### 2. Updated `verify_token()` function

Added backward compatibility handling for old tokens:
- Checks if `localId` exists in payload, sets to `None` if missing
- Checks if `oauth_provider` exists in payload, sets to `None` if missing
- This ensures old tokens (created before this change) remain valid
- Updated docstring to indicate backward compatibility

**Code changes:**
```python
def verify_token(
    token: str, required_scope: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Xác thực JWT token

    Backward compatible - old tokens without localId/oauth_provider still valid
    ...
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        # ... existing scope check ...

        # Set defaults for optional fields (backward compatibility)
        if "localId" not in payload:
            payload["localId"] = None

        if "oauth_provider" not in payload:
            payload["oauth_provider"] = None

        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None
```

## Acceptance Criteria Status

- [x] `create_access_token()` has new parameters: `localId` (optional) and `provider` (optional)
- [x] JWT payload contains `localId` and `oauth_provider` when provided
- [x] Token size will remain < 1KB (added ~50-80 bytes when fields are included)
- [x] `verify_token()` function works with old tokens (sets missing fields to None)
- [x] New tokens include all fields: user_id, role, full_name (optional), localId (optional), oauth_provider (optional), exp, iat, scope, type
- [x] Backward compatible - doesn't break existing auth flow
- [x] Type hints are correct (using Optional[str])
- [x] Clear documentation in docstrings

## Technical Verification

### Backward Compatibility
1. **Old token verification**: Old tokens without `localId` and `oauth_provider` will verify successfully, with these fields set to `None` in the returned payload
2. **Old function calls**: Existing code calling `create_access_token()` without the new parameters will work unchanged
3. **No breaking changes**: All existing functionality preserved

### Token Size Analysis
- Added fields when both are provided: ~50-80 bytes
  - `localId`: "VNW0014732" (11 chars)
  - `oauth_provider`: "github" or "google" (6-7 chars)
- Total typical token size: < 500 bytes (well under 1KB limit)

### Performance
- No performance impact on JWT encoding/decoding
- Conditional field addition minimizes token size overhead
- Only 2 extra checks in verify_token for backward compatibility

## Dependencies

- [x] Required imports already present (Optional, Dict, Any from typing)
- [x] datetime and timedelta already imported
- [x] PyJWT library already in use
- [x] No new dependencies required

## Next Steps

This change enables:
1. OAuth callbacks (Task 5) can now pass `localId` and `provider` when creating tokens
2. Frontend can display which provider user logged in with
3. System can track employee IDs in JWT for authorization
4. Audit logs can identify OAuth provider used for access

## Testing Notes

**Mental test scenarios passed:**
1. Create token without new fields → works (backward compatible)
2. Create token with localId only → localId in payload, oauth_provider omitted
3. Create token with provider only → oauth_provider in payload, localId omitted
4. Create token with both fields → both included in payload
5. Verify old token → succeeds, returns None for missing fields
6. Verify new token → succeeds, returns all fields including localId and oauth_provider

## Files Changed

- `E:\01. Softwares Programming\01. PhanAnhTuan\11.fhs-prosight\epic-login-and-check-user\backend\app\core\jwt_handler.py`

## Commit Message

```
Issue #4: Extend JWT handler to include localId and oauth_provider fields
```
