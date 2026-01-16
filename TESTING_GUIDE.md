# 🧪 Testing Guide - Fullstack Deployment

## ✅ What's Been Fixed

### Latest Fix (Just Now):
- ✅ **DATABASE_URL Flexibility** - Container can now start with POSTGRES_* variables only
- ✅ **get_database_url() method** - Auto-constructs DATABASE_URL from POSTGRES_* vars
- ✅ **Backward Compatible** - Works with both old (DATABASE_URL) and new (POSTGRES_*) configuration

### All Fixes:
1. ✅ Alembic uses environment variables (no hardcoded DB)
2. ✅ Single migration `0846970e5b1f` (clean DB init)
3. ✅ Async/sync driver handled correctly for alembic
4. ✅ DATABASE_URL auto-constructed from POSTGRES_* vars
5. ✅ Route guard protects all authenticated routes
6. ✅ Flexible DATABASE_URL configuration

---

## 🚀 Quick Test - Local Docker

### **Test 1: Start Containers with POSTGRES_* Variables**

```bash
# Pull latest image (wait for GitHub Actions workflow #13 to complete)
docker pull patcoder97/prosight-fullstack:latest

# Start containers
docker-compose -f docker-compose.fullstack.yml up -d

# Monitor logs (should NOT see any errors)
docker logs -f tp75-fullstack
```

**Expected Logs (SUCCESS):**

```
🚀 Starting FHS HR Backend...
✓ DATABASE_URL: postgresql+asyncpg://tp75user:***@tp75-db:5432/tp75db
⏳ Waiting for database to be ready...
✓ Database is ready!
✓ Database connected successfully!

📦 Running database migrations...
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 0846970e5b1f, initial_schema_all_tables
✓ Database migrations completed successfully!

🌱 Seeding database...
✓ Database seeding completed successfully!

✓ All checks passed!
🌐 Starting Uvicorn server on 0.0.0.0:8001...
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001
```

**If you see errors:**
```bash
# Check environment variables
docker exec tp75-fullstack env | grep POSTGRES

# Should output:
# POSTGRES_HOST=tp75-db
# POSTGRES_PORT=5432
# POSTGRES_USER=tp75user
# POSTGRES_PASSWORD=tp75pass_change_in_production
# POSTGRES_DATABASE=tp75db
```

---

## 🔐 Test 2: Route Guard Protection

### **Test 2.1: Access Homepage Without Login**

```bash
# Test frontend (should redirect to login)
curl -I http://localhost:8001/

# Or open in browser:
# http://localhost:8001/
```

**Expected Behavior:**
- If not logged in → Redirect to `/login`
- Browser should show login page

### **Test 2.2: Try to Access Dashboard Without Login**

```bash
# Open in browser:
# http://localhost:8001/dashboard
```

**Expected Behavior:**
- Redirect to `/login?returnUrl=/dashboard`
- After successful login → Redirect back to `/dashboard`

### **Test 2.3: Login with Google OAuth**

1. **Open:** `http://localhost:8001/login`
2. **Click:** "Login with Google"
3. **Expected:**
   - Redirect to Google OAuth page
   - After authorization → Redirect to `/api/auth/google/callback`
   - Set `access_token` cookie
   - Redirect to `/` (or `returnUrl` if specified)
4. **Verify Cookie:**
   - Open DevTools → Application → Cookies
   - Should see: `access_token=<jwt_token>`

### **Test 2.4: Access Dashboard After Login**

```bash
# Open in browser (should work now):
# http://localhost:8001/dashboard
```

**Expected Behavior:**
- Access granted (no redirect to login)
- Dashboard page loads successfully

### **Test 2.5: Try to Access Login Page While Logged In**

```bash
# Open in browser:
# http://localhost:8001/login
```

**Expected Behavior:**
- Redirect to `/` (already authenticated)

---

## 🧪 Test 3: Database Configuration

### **Test 3.1: Verify DATABASE_URL Construction**

```bash
# Enter container shell
docker exec -it tp75-fullstack bash

# Test Python settings
python -c "
from app.core.config import settings
print('DATABASE_URL:', settings.get_database_url())
"

# Expected output:
# DATABASE_URL: postgresql+asyncpg://tp75user:tp75pass_change_in_production@tp75-db:5432/tp75db

# Exit container
exit
```

### **Test 3.2: Verify Alembic Migration**

```bash
# Check current migration version
docker exec tp75-fullstack alembic current

# Expected output:
# 0846970e5b1f (head)

# Verify migration history
docker exec tp75-fullstack alembic history

# Expected output:
# 0846970e5b1f (head) -> <base>, initial_schema_all_tables
```

### **Test 3.3: Verify Database Tables**

```bash
# List all tables
docker exec tp75-db psql -U tp75user -d tp75db -c "\dt"

# Expected tables:
#  Schema |      Name       | Type  |  Owner
# --------+-----------------+-------+----------
#  public | alembic_version | table | tp75user
#  public | dormitory_bills | table | tp75user
#  public | employees       | table | tp75user
#  public | evaluations     | table | tp75user
#  public | pidms_keys      | table | tp75user
#  public | users           | table | tp75user

# Check row counts
docker exec tp75-db psql -U tp75user -d tp75db -c "
SELECT
  'users' as table_name, COUNT(*) FROM users
UNION ALL
SELECT 'employees', COUNT(*) FROM employees
UNION ALL
SELECT 'evaluations', COUNT(*) FROM evaluations
UNION ALL
SELECT 'dormitory_bills', COUNT(*) FROM dormitory_bills
UNION ALL
SELECT 'pidms_keys', COUNT(*) FROM pidms_keys;
"
```

---

## 🌐 Test 4: API Endpoints

### **Test 4.1: Health Check**

```bash
curl http://localhost:8001/api/health

# Expected output:
# {"status":"healthy"}
```

### **Test 4.2: API Documentation**

```bash
# Open in browser:
# http://localhost:8001/docs

# Expected: Swagger UI with all API endpoints
```

### **Test 4.3: OAuth Login Endpoints**

```bash
# Test Google OAuth login endpoint (should redirect)
curl -I http://localhost:8001/api/auth/login/google

# Expected:
# HTTP/1.1 302 Found
# location: https://accounts.google.com/o/oauth2/v2/auth?...

# Test GitHub OAuth login endpoint (should redirect)
curl -I http://localhost:8001/api/auth/login/github

# Expected:
# HTTP/1.1 302 Found
# location: https://github.com/login/oauth/authorize?...
```

---

## 🔧 Test 5: Configuration Flexibility

### **Test 5.1: Test with POSTGRES_* Variables (Current Setup)**

Your current `docker-compose.fullstack.yml`:

```yaml
environment:
  - POSTGRES_HOST=tp75-db
  - POSTGRES_PORT=5432
  - POSTGRES_USER=tp75user
  - POSTGRES_PASSWORD=tp75pass_change_in_production
  - POSTGRES_DATABASE=tp75db
  # No DATABASE_URL needed!
```

**Status:** ✅ Should work (DATABASE_URL auto-constructed)

### **Test 5.2: Test with DATABASE_URL (Backward Compatible)**

You can also use this configuration:

```yaml
environment:
  - DATABASE_URL=postgresql+asyncpg://tp75user:tp75pass@tp75-db:5432/tp75db
  # POSTGRES_* variables optional when DATABASE_URL is provided
```

**Status:** ✅ Should also work (uses DATABASE_URL directly)

### **Test 5.3: Test with Mixed Configuration**

```yaml
environment:
  # DATABASE_URL takes priority if provided
  - DATABASE_URL=postgresql+asyncpg://user1:pass1@host1:5432/db1
  # These will be ignored:
  - POSTGRES_USER=user2
  - POSTGRES_PASSWORD=pass2
```

**Status:** ✅ Uses DATABASE_URL (ignores POSTGRES_* vars)

---

## 📊 Test Results Checklist

Run through this checklist:

- [ ] **Container starts successfully** (no errors in logs)
- [ ] **Database migrations applied** (`alembic current` shows `0846970e5b1f`)
- [ ] **All database tables created** (6 tables: users, employees, etc.)
- [ ] **Frontend loads** (`http://localhost:8001` shows login page)
- [ ] **Route guard works** (redirects to `/login` when not authenticated)
- [ ] **Google OAuth works** (login flow successful)
- [ ] **Access token cookie set** (visible in DevTools)
- [ ] **Authenticated routes accessible** (dashboard loads after login)
- [ ] **Login page redirect** (redirects to `/` when already logged in)
- [ ] **API health endpoint works** (`/api/health` returns healthy)
- [ ] **API docs accessible** (`/docs` loads Swagger UI)
- [ ] **DATABASE_URL auto-constructed** (from POSTGRES_* variables)

---

## 🐛 Troubleshooting

### **Issue: Container won't start (ValueError: Either DATABASE_URL or POSTGRES_* must be provided)**

**Cause:** Missing both DATABASE_URL and POSTGRES_* variables

**Fix:**
```yaml
environment:
  # Add these to docker-compose.fullstack.yml:
  - POSTGRES_HOST=tp75-db
  - POSTGRES_PORT=5432
  - POSTGRES_USER=tp75user
  - POSTGRES_PASSWORD=your_password_here
  - POSTGRES_DATABASE=tp75db
```

### **Issue: Route guard not redirecting to login**

**Cause:** Route guard checks for `access_token` cookie

**Fix:**
```bash
# Clear browser cookies and try again
# Or check browser DevTools → Application → Cookies
# Delete access_token cookie manually
```

### **Issue: OAuth callback redirect_uri_mismatch**

**Cause:** OAuth redirect URI not configured in Google/GitHub

**Fix:**
```
Google Cloud Console:
- Add: https://hrsfhs.tphomelab.io.vn/api/auth/google/callback

GitHub OAuth App:
- Add: https://hrsfhs.tphomelab.io.vn/api/auth/github/callback
```

### **Issue: Database migration fails**

**Cause:** Old migration state conflicts with new migration

**Fix:**
```bash
# Drop and recreate database
docker exec tp75-db psql -U tp75user -d postgres -c "DROP DATABASE tp75db;"
docker exec tp75-db psql -U tp75user -d postgres -c "CREATE DATABASE tp75db;"

# Restart container (will auto-run migrations)
docker restart tp75-fullstack

# Verify migration
docker exec tp75-fullstack alembic current
```

---

## 📝 GitHub Actions Status

Check current build status:
```
https://github.com/PATCoder97/fhs-prosight/actions
```

**Latest Workflows:**
- Workflow #13 (latest): "fix: make DATABASE_URL flexible" - **In Progress** ⏳
- Workflow #12: "feat: add route guard" - In Progress ⏳
- Workflow #11: "refactor: auto-construct DATABASE_URL" - Completed ✅

**When #13 completes:**
```bash
# Pull latest image
docker pull patcoder97/prosight-fullstack:latest

# Recreate container with new image
docker-compose -f docker-compose.fullstack.yml up -d --force-recreate tp75-fullstack

# Monitor logs
docker logs -f tp75-fullstack
```

---

## 🎉 Success Criteria

**You're ready for production when:**

1. ✅ All containers start without errors
2. ✅ Database migrations apply successfully
3. ✅ Route guard redirects unauthenticated users to login
4. ✅ OAuth login flow works end-to-end
5. ✅ Access token cookie is set after login
6. ✅ Authenticated routes are accessible
7. ✅ Login page redirects when already authenticated
8. ✅ API endpoints respond correctly
9. ✅ DATABASE_URL is auto-constructed from POSTGRES_* vars
10. ✅ No hardcoded credentials in code or logs

---

**Last Updated:** 2026-01-16
**Image:** `patcoder97/prosight-fullstack:latest` (after workflow #13)
**Status:** ✅ Ready to test (waiting for build to complete)
