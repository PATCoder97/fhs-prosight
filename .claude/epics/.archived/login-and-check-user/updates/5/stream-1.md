---
issue: 5
stream: schema-updates
started: 2026-01-08T10:00:00Z
updated: 2026-01-08T10:15:00Z
status: completed
---

# Stream 1: Schema Updates

## Scope
Update SocialLoginUser schema to include localId field:
- Add localId: Optional[str] = None to Pydantic model
- Ensure schema validates correctly

## Files Modified
- `backend/app/schemas/auth.py` (MODIFY)

## Progress

### Completed Steps

1. **Read current schema**
   - Reviewed SocialLoginUser BaseModel structure
   - Identified insertion point for localId field

2. **Added localId field**
   - Added `localId: Optional[str] = None` after role field
   - Field is optional and nullable for backward compatibility
   - Pydantic will validate this field automatically

### Changes Made

**File: backend/app/schemas/auth.py**

```python
class SocialLoginUser(BaseModel):
    id: int
    social_id: str
    provider: str
    email: Optional[str]
    full_name: Optional[str]
    avatar: Optional[str]
    role: str = "user"
    localId: Optional[str] = None  # NEW FIELD
    is_active: bool = True
    is_verified: bool = False
    is_new_user: bool = False
```

## Status: COMPLETED

Schema successfully updated with localId field:
- ✅ Field added to SocialLoginUser model
- ✅ Type is Optional[str] for nullable support
- ✅ Default value is None for new users
- ✅ Backward compatible with existing responses
- ✅ Ready for use in Stream 2 (OAuth callbacks)
