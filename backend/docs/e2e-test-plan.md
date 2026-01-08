# E2E Test Plan - Login and Check User

## Overview

This document provides end-to-end test scenarios for the OAuth login system with role-based access control and localId management.

## Prerequisites

### Environment Setup
- **Staging environment** deployed with latest code
- **Database** accessible (PostgreSQL at ktxn258.duckdns.org:6543)
- **OAuth credentials** configured:
  - Google OAuth Client ID and Secret
  - GitHub OAuth Client ID and Secret

### Test Accounts
- **Google account**: test@example.com (or create test account)
- **GitHub account**: testuser (or create test account)
- **Admin account**: Manually created in database with role='admin'

### Tools
- Web browser (Chrome/Firefox recommended)
- **Postman** or **curl** for API testing
- **Database client** (psql, DBeaver, etc.) for SQL verification
- **JWT decoder** (jwt.io or browser extension)

---

## Test Scenarios

### Scenario 1: New User Google Login

**Objective**: Verify new user can login via Google OAuth and receives correct default values.

#### Steps:
1. Open browser and navigate to: `https://staging.example.com/auth/login/google`
2. Authenticate with Google test account
3. Get redirected to `/auth/google/callback`
4. Receive JSON response with access_token and user data

#### Expected Results:
- [ ] HTTP Status: `200 OK`
- [ ] Response has `access_token` field (JWT string)
- [ ] Response has `token_type`: `"bearer"`
- [ ] `user.email` matches Google account email
- [ ] `user.role` = `"guest"` (default for new users)
- [ ] `user.localId` = `null` (no localId assigned yet)
- [ ] `user.provider` = `"google"`
- [ ] `user.is_active` = `true`
- [ ] `user.is_verified` = `false`

#### JWT Token Verification:
1. Copy `access_token` from response
2. Decode at https://jwt.io
3. Verify payload contains:
   - `user_id`: (integer as string)
   - `role`: `"guest"`
   - `localId`: `null` or not present
   - `oauth_provider`: `"google"`
   - `exp`: expiration timestamp (future)
   - `scope`: `"access"`

#### Database Verification:
```sql
SELECT id, email, role, localId, provider, is_active
FROM users
WHERE email = 'test@example.com';
```

**Expected:**
- 1 row returned
- `role` = 'guest'
- `localId` = NULL
- `provider` = 'google'

---

### Scenario 2: GitHub OAuth New User Login

**Objective**: Verify GitHub OAuth works similarly to Google.

#### Steps:
1. Navigate to: `https://staging.example.com/auth/login/github`
2. Authorize with GitHub test account
3. Receive callback response

#### Expected Results:
- [ ] HTTP Status: `200 OK`
- [ ] `user.provider` = `"github"`
- [ ] `user.role` = `"guest"`
- [ ] `user.localId` = `null`
- [ ] JWT token has `oauth_provider` = `"github"`

---

### Scenario 3: Admin Assigns LocalId

**Objective**: Verify admin can assign localId to a user.

#### Prerequisites:
- User from Scenario 1 exists (user_id = X)
- Admin account with JWT token

#### Steps:
1. Login as admin to get admin token
2. Call API:
   ```bash
   curl -X PUT https://staging.example.com/api/users/X/localId \
     -H "Authorization: Bearer {admin_token}" \
     -H "Content-Type: application/json" \
     -d '{"localId": "VNW001"}'
   ```

#### Expected Results:
- [ ] HTTP Status: `200 OK`
- [ ] Response: `{"success": true, "message": "...", "user": {...}}`
- [ ] `user.localId` = `"VNW001"`
- [ ] Success message confirms assignment

#### Database Verification:
```sql
SELECT localId FROM users WHERE id = X;
```
**Expected:** `VNW001`

#### Negative Test:
- Non-admin user tries same request:
  - [ ] HTTP Status: `403 Forbidden`
  - [ ] Error message: "Insufficient permissions"

---

### Scenario 4: User Re-Login After LocalId Assignment

**Objective**: Verify user receives localId after admin assigns it.

#### Steps:
1. User from Scenario 1 logs out (discard old token)
2. User logs in again via Google OAuth
3. Receive new JWT token

#### Expected Results:
- [ ] `user.localId` = `"VNW001"` (now present in response)
- [ ] `user.role` = `"guest"` (still guest, unchanged)
- [ ] JWT token payload has `"localId": "VNW001"`

#### JWT Verification:
Decode new token → verify `localId` field is now `"VNW001"`

---

### Scenario 5: Admin Updates User Role

**Objective**: Verify admin can promote user from guest to user.

#### Steps:
1. Admin calls:
   ```bash
   curl -X PUT https://staging.example.com/api/users/X/role \
     -H "Authorization: Bearer {admin_token}" \
     -H "Content-Type: application/json" \
     -d '{"role": "user"}'
   ```

#### Expected Results:
- [ ] HTTP Status: `200 OK`
- [ ] Response: `{"success": true, "message": "Role updated: guest → user", ...}`
- [ ] `user.role` = `"user"`

#### Database Verification:
```sql
SELECT role FROM users WHERE id = X;
```
**Expected:** `user`

#### User Re-Login:
1. User logs in again
2. New JWT token has `"role": "user"` in payload

---

### Scenario 6: Multiple OAuth Accounts Same Person

**Objective**: Verify one person can have both Google and GitHub accounts with same localId.

#### Steps:
1. User logs in via Google → user_id = A
2. Admin assigns `localId = "VNW002"` to user A
3. **Same person** logs in via GitHub → user_id = B (different record)
4. Admin assigns `localId = "VNW002"` to user B

#### Expected Results:
- [ ] Two separate user records created (different providers)
- [ ] Both have `localId = "VNW002"`

#### Database Verification:
```sql
SELECT id, provider, email, localId
FROM users
WHERE localId = 'VNW002';
```

**Expected:**
- 2 rows returned
- One with `provider = 'google'`
- One with `provider = 'github'`
- Both have `localId = 'VNW002'`

---

### Scenario 7: Admin Cannot Demote Themselves

**Objective**: Verify security check prevents admin self-demotion.

#### Steps:
1. Admin logged in with user_id = ADMIN_ID
2. Admin tries to change their own role:
   ```bash
   curl -X PUT https://staging.example.com/api/users/ADMIN_ID/role \
     -H "Authorization: Bearer {admin_token}" \
     -d '{"role": "user"}'
   ```

#### Expected Results:
- [ ] HTTP Status: `400 Bad Request`
- [ ] Error message: "Cannot demote yourself from admin role"

---

### Scenario 8: List Users with Filters

**Objective**: Verify admin can list and filter users.

#### Steps:
1. Admin calls:
   ```bash
   curl -X GET "https://staging.example.com/api/users?limit=10&offset=0" \
     -H "Authorization: Bearer {admin_token}"
   ```

#### Expected Results:
- [ ] HTTP Status: `200 OK`
- [ ] Response: `{"users": [...], "total": N, "limit": 10, "offset": 0}`
- [ ] `users` array contains user objects

#### Filter Tests:

**Filter by localId:**
```bash
curl -X GET "https://staging.example.com/api/users?localId=VNW001" \
  -H "Authorization: Bearer {admin_token}"
```
- [ ] Only users with `localId = "VNW001"` returned

**Filter by provider:**
```bash
curl -X GET "https://staging.example.com/api/users?provider=google" \
  -H "Authorization: Bearer {admin_token}"
```
- [ ] Only Google OAuth users returned

**Filter by email:**
```bash
curl -X GET "https://staging.example.com/api/users?email=test" \
  -H "Authorization: Bearer {admin_token}"
```
- [ ] Users with email containing "test" returned (case-insensitive)

#### Negative Test:
- Non-admin tries to list users:
  - [ ] HTTP Status: `403 Forbidden`

---

### Scenario 9: Input Validation Tests

**Objective**: Verify validation errors are returned correctly.

#### Test 9.1: Invalid LocalId Format
```bash
curl -X PUT https://staging.example.com/api/users/X/localId \
  -H "Authorization: Bearer {admin_token}" \
  -d '{"localId": "VNW-001!@#"}'
```

**Expected:**
- [ ] HTTP Status: `422 Unprocessable Entity`
- [ ] Error: "localId must contain only alphanumeric characters"

#### Test 9.2: LocalId Too Long
```bash
curl -X PUT https://staging.example.com/api/users/X/localId \
  -H "Authorization: Bearer {admin_token}" \
  -d '{"localId": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"}'  # 51 chars
```

**Expected:**
- [ ] HTTP Status: `422 Unprocessable Entity`
- [ ] Error about length

#### Test 9.3: Invalid Role
```bash
curl -X PUT https://staging.example.com/api/users/X/role \
  -H "Authorization: Bearer {admin_token}" \
  -d '{"role": "superadmin"}'
```

**Expected:**
- [ ] HTTP Status: `422 Unprocessable Entity`
- [ ] Error: role must be one of guest/user/admin

---

### Scenario 10: Performance Testing

**Objective**: Verify system meets performance requirements.

#### Test 10.1: OAuth Callback Response Time

**Tools:** Apache Bench or Postman Collection Runner

**Test:**
- Simulate 100 OAuth callbacks
- Measure p95 and p99 response times

**Expected:**
- [ ] p95 < 2 seconds
- [ ] p99 < 3 seconds

#### Test 10.2: JWT Token Validation

**Test:**
- Create 1000 valid JWT tokens
- Validate each token (call protected endpoint)
- Measure validation time

**Expected:**
- [ ] p99 < 100ms per validation

---

### Scenario 11: Security Testing

**Objective**: Verify security controls are effective.

#### Test 11.1: Expired Token
1. Create JWT token with expiration in the past
2. Try to access protected endpoint

**Expected:**
- [ ] HTTP Status: `401 Unauthorized`
- [ ] Error: "Invalid authentication credentials"

#### Test 11.2: Invalid Token
1. Use random string as token
2. Try to access protected endpoint

**Expected:**
- [ ] HTTP Status: `401 Unauthorized`

#### Test 11.3: Wrong Scope
1. Create token with `scope = "refresh"`
2. Try to access endpoint requiring `scope = "access"`

**Expected:**
- [ ] HTTP Status: `401 Unauthorized`

#### Test 11.4: No Authorization Header
1. Call admin endpoint without `Authorization` header

**Expected:**
- [ ] HTTP Status: `403 Forbidden`

---

### Scenario 12: Database Migration Rollback

**Objective**: Verify migration can be safely rolled back.

#### Steps:
1. **Backup database:**
   ```bash
   pg_dump -h ktxn258.duckdns.org -p 6543 -U casaos casaos > backup.sql
   ```

2. **Check current migration:**
   ```bash
   cd backend
   alembic current
   ```

3. **Rollback migration:**
   ```bash
   alembic downgrade -1
   ```

4. **Verify schema changes reverted:**
   ```sql
   \d users
   ```
   - [ ] `localId` column NOT present
   - [ ] `role` default is 'user' (not 'guest')
   - [ ] Unique constraint `uq_provider_social_id` NOT present

5. **Re-apply migration:**
   ```bash
   alembic upgrade head
   ```

6. **Verify schema restored:**
   - [ ] `localId` column present
   - [ ] `role` default is 'guest'
   - [ ] Unique constraint present

---

## Test Execution Checklist

### Pre-Test
- [ ] Staging environment deployed
- [ ] Database accessible
- [ ] Test accounts created
- [ ] Admin account ready
- [ ] Tools installed (curl, Postman, psql)

### During Test
- [ ] Document all results
- [ ] Screenshot any failures
- [ ] Record response times
- [ ] Save SQL query results

### Post-Test
- [ ] All scenarios passed
- [ ] No P0/P1 bugs found
- [ ] Performance requirements met
- [ ] Security controls verified
- [ ] Rollback tested successfully

---

## Bug Report Template

If issues found during testing:

**Title:** [Component] Brief description

**Severity:** P0 (Critical) | P1 (High) | P2 (Medium) | P3 (Low)

**Steps to Reproduce:**
1. ...
2. ...

**Expected Result:**
...

**Actual Result:**
...

**Environment:**
- Staging URL: ...
- Database: ...
- Browser: ...

**Screenshots/Logs:**
...

---

## Sign-Off

**Tester:** _______________
**Date:** _______________
**Result:** PASS / FAIL
**Notes:** _______________

