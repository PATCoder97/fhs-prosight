# Stream 1 Progress: User Model Update

## Status: COMPLETED

## Changes Made

### File: `backend/app/models/user.py`

1. Added `localId` field:
   - Type: `Column(String(50), nullable=True, index=True)`
   - Purpose: Employee identification
   - Indexed for faster queries

2. Changed default role:
   - Old: `default="user"`
   - New: `default="guest"`
   - Updated comment to reflect new role hierarchy

## Commit

- Commit hash: c07a940
- Message: "Issue #3: Add localId field to User model and change default role to guest"

## Backward Compatibility

- Existing users keep their current role (no forced updates)
- Existing users will have `localId = NULL` from migration
- New users will have `role = "guest"` and `localId = None` by default

## Next Steps

- Proceed to Stream 2: Update auth service to support localId field
