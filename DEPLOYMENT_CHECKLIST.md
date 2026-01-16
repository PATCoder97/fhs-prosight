# 🚀 Deployment Checklist - FHS ProSight Fullstack

## ✅ Pre-Deployment Verification

### **1. Docker Image Status**

- [x] Latest build successful: `v1.0.3`
- [x] GitHub Actions workflow operational
- [x] Docker Hub image available: `patcoder97/prosight-fullstack:v1.0.3`
- [x] Multi-platform support: `linux/amd64`, `linux/arm64`

**Verify:**
```bash
# Check Docker Hub
docker pull patcoder97/prosight-fullstack:v1.0.3
docker pull patcoder97/prosight-fullstack:latest

# Both should succeed
```

### **2. Code Status**

- [x] Database configuration fixed (auto-construct from POSTGRES_* vars)
- [x] Route guard protection implemented
- [x] Alembic migrations consolidated (single migration: `0846970e5b1f`)
- [x] Async/sync compatibility fixed
- [x] Tag-based build system operational
- [x] All documentation updated

**Current Commit:** `98c6da2` (docs: add tag-based build system success documentation)

### **3. Required Environment Variables**

Ensure these are configured in your deployment environment:

**Database Configuration:**
```bash
POSTGRES_HOST=tp75-db
POSTGRES_PORT=5432
POSTGRES_USER=tp75user
POSTGRES_PASSWORD=<your-secure-password>  # ⚠️ REQUIRED
POSTGRES_DATABASE=tp75db
```

**Security:**
```bash
SECRET_KEY=<your-32-character-secret>      # ⚠️ REQUIRED
ALGORITHM=HS256
```

**OAuth (Google):**
```bash
GOOGLE_CLIENT_ID=<your-google-client-id>         # ⚠️ REQUIRED
GOOGLE_CLIENT_SECRET=<your-google-client-secret> # ⚠️ REQUIRED
```

**OAuth (GitHub):**
```bash
GITHUB_CLIENT_ID=<your-github-client-id>         # ⚠️ REQUIRED
GITHUB_CLIENT_SECRET=<your-github-client-secret> # ⚠️ REQUIRED
```

**Optional:**
```bash
PIDKEY_API_KEY=<your-pidkey-api-key>      # Optional
COOKIE_SECURE=true                         # For HTTPS
COOKIE_DOMAIN=                             # Empty for same-origin
```

---

## 🎯 Deployment Steps

### **Step 1: Prepare Server**

```bash
# SSH to CasaOS server
ssh user@your-casaos-server

# Navigate to project directory
cd ~/fhs-prosight

# Pull latest code (optional, if using git)
git pull origin main
```

### **Step 2: Pull Latest Docker Image**

```bash
# Pull specific version (recommended)
docker pull patcoder97/prosight-fullstack:v1.0.3

# OR pull latest
docker pull patcoder97/prosight-fullstack:latest

# Verify image
docker images | grep prosight-fullstack
```

**Expected output:**
```
patcoder97/prosight-fullstack   v1.0.3    <image-id>   <timestamp>   <size>
patcoder97/prosight-fullstack   latest    <image-id>   <timestamp>   <size>
```

### **Step 3: Update docker-compose.fullstack.yml**

Edit the compose file to use the new image:

```yaml
services:
  tp75-fullstack:
    image: patcoder97/prosight-fullstack:v1.0.3  # Specific version
    # OR use: patcoder97/prosight-fullstack:latest
    environment:
      # Database
      - POSTGRES_HOST=tp75-db
      - POSTGRES_PORT=5432
      - POSTGRES_USER=tp75user
      - POSTGRES_PASSWORD=YOUR_PASSWORD_HERE     # ⚠️ CHANGE!
      - POSTGRES_DATABASE=tp75db

      # Security
      - SECRET_KEY=YOUR_SECRET_KEY_HERE          # ⚠️ CHANGE!
      - ALGORITHM=HS256

      # Google OAuth
      - GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID        # ⚠️ CHANGE!
      - GOOGLE_CLIENT_SECRET=YOUR_GOOGLE_SECRET       # ⚠️ CHANGE!

      # GitHub OAuth
      - GITHUB_CLIENT_ID=YOUR_GITHUB_CLIENT_ID        # ⚠️ CHANGE!
      - GITHUB_CLIENT_SECRET=YOUR_GITHUB_SECRET       # ⚠️ CHANGE!

      # Optional
      - PIDKEY_API_KEY=YOUR_PIDKEY_API_KEY      # Optional
      - COOKIE_SECURE=true
      - COOKIE_DOMAIN=
```

### **Step 4: Stop Old Containers**

```bash
# Stop containers (keep database volume)
docker-compose -f docker-compose.fullstack.yml down

# Verify containers are stopped
docker ps | grep tp75
```

**Note:** Do NOT use `-v` flag (this would delete database data)

### **Step 5: Start New Containers**

```bash
# Start containers with new image
docker-compose -f docker-compose.fullstack.yml up -d

# Verify containers are running
docker ps | grep tp75
```

**Expected output:**
```
tp75-fullstack   patcoder97/prosight-fullstack:v1.0.3   Up X seconds   0.0.0.0:8001->8001/tcp
tp75-db          postgres:15-alpine                      Up X seconds   5432/tcp
```

### **Step 6: Monitor Startup**

```bash
# Follow container logs
docker logs -f tp75-fullstack
```

**Expected successful output:**
```
🚀 Starting FHS HR Backend...
✓ DATABASE_URL: postgresql+asyncpg://tp75user:***@tp75-db:5432/tp75db
⏳ Waiting for database to be ready...
✓ Database is ready!
✓ Database connected successfully!

📦 Running database migrations...
INFO  [alembic.runtime.migration] Running upgrade  -> 0846970e5b1f, initial_schema_all_tables
✓ Database migrations completed successfully!

🌱 Seeding database...
✓ Database seeding completed successfully!

✓ All checks passed!
🌐 Starting Uvicorn server on 0.0.0.0:8001...
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001
```

**⚠️ If you see errors, check:**
- Database connection (POSTGRES_* variables)
- Missing environment variables
- Database readiness

---

## 🔍 Post-Deployment Verification

### **Test 1: Health Check**

```bash
# API health endpoint
curl http://localhost:8001/api/health

# Expected: {"status":"healthy"}
```

### **Test 2: Frontend Access**

```bash
# Frontend (should serve login page)
curl http://localhost:8001

# Expected: HTML content with login page
```

### **Test 3: Database Migration**

```bash
# Check migration version
docker exec tp75-fullstack alembic current

# Expected: 0846970e5b1f (head)
```

### **Test 4: Database Tables**

```bash
# List database tables
docker exec tp75-db psql -U tp75user -d tp75db -c "\dt"

# Expected: 6 tables
#   users
#   employees
#   evaluations
#   evaluation_criteria
#   evaluation_scores
#   alembic_version
```

### **Test 5: Route Guard Protection**

Open browser and test:

1. **Unauthenticated Access:**
   - Visit: `http://localhost:8001/dashboard`
   - Expected: Redirect to `/login?returnUrl=/dashboard`

2. **Login Page:**
   - Visit: `http://localhost:8001/login`
   - Expected: Login page with Google/GitHub OAuth buttons

3. **OAuth Flow:**
   - Click "Login with Google"
   - Expected: Redirect to Google OAuth
   - After authorization: Redirect back to `/dashboard`

4. **Authenticated Access:**
   - Visit: `http://localhost:8001/dashboard`
   - Expected: Dashboard loads (no redirect)

5. **Login When Authenticated:**
   - Visit: `http://localhost:8001/login` (while logged in)
   - Expected: Redirect to `/` (already authenticated)

---

## ⚙️ OAuth Configuration

### **Google Cloud Console**

1. Go to: https://console.cloud.google.com/apis/credentials
2. Select your OAuth 2.0 Client ID
3. Add **Authorized redirect URIs:**
   ```
   https://hrsfhs.tphomelab.io.vn/api/auth/google/callback
   http://localhost:8001/api/auth/google/callback  (for local testing)
   ```
4. Click "Save"

### **GitHub OAuth App**

1. Go to: https://github.com/settings/developers
2. Select your OAuth App
3. Set **Authorization callback URL:**
   ```
   https://hrsfhs.tphomelab.io.vn/api/auth/github/callback
   http://localhost:8001/api/auth/github/callback  (for local testing)
   ```
4. Click "Update application"

---

## 🐛 Troubleshooting

### **Issue: Container won't start**

**Check logs:**
```bash
docker logs tp75-fullstack --tail 50
```

**Common issues:**
1. **Missing environment variables:**
   ```
   ValueError: Either DATABASE_URL or all of (POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DATABASE) must be provided
   ```
   **Fix:** Add all required `POSTGRES_*` variables to `docker-compose.fullstack.yml`

2. **Database not ready:**
   ```
   could not connect to server: Connection refused
   ```
   **Fix:** Wait for database to start, or check `tp75-db` container status

3. **Migration errors:**
   ```
   alembic.util.exc.CommandError
   ```
   **Fix:** Reset database (see below)

### **Issue: OAuth redirect_uri_mismatch**

**Error:**
```
Error 400: redirect_uri_mismatch
```

**Fix:**
1. Check OAuth redirect URIs in Google/GitHub console
2. Ensure they match your deployment domain
3. Update URIs if necessary

### **Issue: Route guard not working**

**Symptoms:**
- Can access `/dashboard` without login
- No redirect to `/login`

**Fix:**
1. Clear browser cookies
2. Verify route guard code is in frontend build
3. Check browser console for errors

### **Issue: Database migration fails**

**Reset database:**
```bash
# Drop and recreate database
docker exec tp75-db psql -U tp75user -d postgres -c "DROP DATABASE IF EXISTS tp75db;"
docker exec tp75-db psql -U tp75user -d postgres -c "CREATE DATABASE tp75db;"

# Restart fullstack container (will re-run migrations)
docker restart tp75-fullstack

# Monitor logs
docker logs -f tp75-fullstack
```

---

## 🔄 Update Procedures

### **To Update to New Version**

```bash
# Pull new image
docker pull patcoder97/prosight-fullstack:v1.0.4

# Update docker-compose.yml to use new version
vim docker-compose.fullstack.yml
# Change: image: patcoder97/prosight-fullstack:v1.0.4

# Recreate container
docker-compose -f docker-compose.fullstack.yml up -d --force-recreate tp75-fullstack

# Monitor logs
docker logs -f tp75-fullstack
```

### **To Rollback to Previous Version**

```bash
# Use specific older version
docker pull patcoder97/prosight-fullstack:v1.0.3

# Update docker-compose.yml
vim docker-compose.fullstack.yml
# Change: image: patcoder97/prosight-fullstack:v1.0.3

# Recreate container
docker-compose -f docker-compose.fullstack.yml up -d --force-recreate tp75-fullstack
```

---

## 📊 Success Criteria

Deployment is successful when ALL of the following are true:

- [ ] Containers start without errors
- [ ] Health check returns `{"status":"healthy"}`
- [ ] Frontend login page loads
- [ ] Database migration `0846970e5b1f` is current
- [ ] All 6 database tables exist
- [ ] Route guard redirects unauthenticated users to `/login`
- [ ] Google OAuth login flow works end-to-end
- [ ] GitHub OAuth login flow works end-to-end
- [ ] After login, can access protected routes
- [ ] `access_token` cookie is set after login
- [ ] Already-logged-in users can't access `/login` (redirect to `/`)
- [ ] No errors in container logs
- [ ] DATABASE_URL auto-constructed from `POSTGRES_*` variables

---

## 📞 Support

### **Documentation**

- [TAG_BUILD_SUCCESS.md](TAG_BUILD_SUCCESS.md) - Build system details
- [TAG_BUILD_GUIDE.md](TAG_BUILD_GUIDE.md) - Tag usage guide
- [README_DEPLOY.md](README_DEPLOY.md) - Full deployment guide
- [DEPLOYMENT_COMPLETE.md](DEPLOYMENT_COMPLETE.md) - Feature overview
- [TESTING_GUIDE.md](TESTING_GUIDE.md) - Testing procedures

### **Quick Commands**

```bash
# View logs
docker logs -f tp75-fullstack

# Restart services
docker-compose -f docker-compose.fullstack.yml restart

# Stop all
docker-compose -f docker-compose.fullstack.yml down

# Start all
docker-compose -f docker-compose.fullstack.yml up -d

# Check running containers
docker ps | grep tp75

# Check database tables
docker exec tp75-db psql -U tp75user -d tp75db -c "\dt"

# Check migration version
docker exec tp75-fullstack alembic current
```

---

## 🎉 Ready to Deploy!

**Current Status:**
- ✅ Docker image built and tested
- ✅ Tag-based build system operational
- ✅ All features implemented and working
- ✅ Documentation complete
- ✅ Deployment procedures documented

**Latest Image:**
- `patcoder97/prosight-fullstack:v1.0.3`
- `patcoder97/prosight-fullstack:latest`

**Next Action:**
Follow the deployment steps above to deploy to your CasaOS server.

---

**Last Updated:** 2026-01-16
**Version:** v1.0.3
**Status:** 🚀 READY FOR PRODUCTION DEPLOYMENT
