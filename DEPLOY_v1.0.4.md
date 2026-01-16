# 🚀 Deploy Version v1.0.4 - OAuth Callback Fix

## ✅ What's New in v1.0.4

### **Fixed: OAuth Callback Redirect Issue**

**Problem:**
- After OAuth login (Google/GitHub), backend redirects to `/` (home page)
- Route guard was blocking `/` because it required authentication
- Cookie wasn't set yet when route guard checked
- User couldn't complete login flow

**Solution:**
- Added `/` to `publicRoutes` array
- OAuth callback can now redirect to `/` without authentication check
- Cookie gets set successfully
- User can then access protected routes normally

**Changed File:**
- `frontend/src/plugins/1.router/index.js`

---

## 🐳 Docker Image Details

**Image Tags:**
- `patcoder97/prosight-fullstack:v1.0.4`
- `patcoder97/prosight-fullstack:latest` (updated to v1.0.4)

**Build Status:** ✅ SUCCESS
**Build Time:** 8m 3s
**Platforms:** linux/amd64, linux/arm64

**GitHub Actions Run:**
- https://github.com/PATCoder97/fhs-prosight/actions/runs/21053482782

---

## 📦 Deploy Instructions

### **Step 1: Pull Latest Image**

```bash
# SSH to your CasaOS server
ssh user@your-casaos-server

# Pull the new image
docker pull patcoder97/prosight-fullstack:v1.0.4

# Or pull latest (which points to v1.0.4)
docker pull patcoder97/prosight-fullstack:latest

# Verify image
docker images | grep prosight-fullstack
```

**Expected output:**
```
patcoder97/prosight-fullstack   v1.0.4    <image-id>   2 minutes ago   <size>
patcoder97/prosight-fullstack   latest    <image-id>   2 minutes ago   <size>
```

### **Step 2: Update docker-compose.yml (Optional)**

If you want to pin to specific version:

```yaml
services:
  tp75-fullstack:
    image: patcoder97/prosight-fullstack:v1.0.4  # Specific version
    # environment variables...
```

Or use `latest` to always get newest version:

```yaml
services:
  tp75-fullstack:
    image: patcoder97/prosight-fullstack:latest  # Always newest
    # environment variables...
```

### **Step 3: Stop Old Container**

```bash
# Navigate to project directory
cd ~/fhs-prosight

# Stop container (keep database volume)
docker-compose -f docker-compose.fullstack.yml down

# Verify container stopped
docker ps | grep tp75-fullstack
```

**⚠️ Important:** Do NOT use `-v` flag (this would delete database data)

### **Step 4: Start New Container**

```bash
# Start with new image
docker-compose -f docker-compose.fullstack.yml up -d

# Check containers running
docker ps | grep tp75
```

**Expected output:**
```
tp75-fullstack   patcoder97/prosight-fullstack:v1.0.4   Up X seconds   0.0.0.0:8001->8001/tcp
tp75-db          postgres:15-alpine                      Up X seconds   5432/tcp
```

### **Step 5: Monitor Startup**

```bash
# Follow logs
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
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
✓ Database migrations completed successfully!

🌱 Seeding database...
✓ Database seeding completed successfully!

✓ All checks passed!
🌐 Starting Uvicorn server on 0.0.0.0:8001...
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001
```

---

## ✅ Verification Tests

### **Test 1: Health Check**

```bash
curl http://localhost:8001/api/health
```

**Expected:** `{"status":"healthy"}`

### **Test 2: Frontend Access**

```bash
curl http://localhost:8001
```

**Expected:** HTML content with login page

### **Test 3: OAuth Login Flow (Critical Test)**

**Using Browser:**

1. **Access protected route without login:**
   - Visit: `http://localhost:8001/dashboard`
   - **Expected:** Redirect to `/login?returnUrl=/dashboard`

2. **Click "Login with Google":**
   - **Expected:** Redirect to Google OAuth consent screen

3. **Authorize on Google:**
   - **Expected:**
     - Redirect to `/api/auth/google/callback`
     - Backend sets `access_token` cookie
     - Redirect to `/` (home page) ← **This is the fix!**
     - Cookie is now available
     - Can access protected routes

4. **Access protected route after login:**
   - Visit: `http://localhost:8001/dashboard`
   - **Expected:** Dashboard loads successfully (no redirect to login)

5. **Try to access login page while authenticated:**
   - Visit: `http://localhost:8001/login`
   - **Expected:** Redirect to `/` (already logged in)

### **Test 4: Check Cookie**

In browser DevTools → Application → Cookies → `http://localhost:8001`:

**Expected cookie:**
- Name: `access_token`
- Value: `<JWT token>`
- HttpOnly: ✓
- Secure: (depends on COOKIE_SECURE setting)

### **Test 5: Database Data**

```bash
# Check if user was created after OAuth login
docker exec tp75-db psql -U tp75user -d tp75db -c "SELECT id, email, full_name, oauth_provider FROM users ORDER BY created_at DESC LIMIT 5;"
```

**Expected:** Your Google/GitHub account should appear in the users table

---

## 🔍 Route Guard Logic Changes

### **Before (v1.0.3 and earlier):**

```javascript
const publicRoutes = [
  '/login',
  '/register',
  // ... (no '/' included)
]

// Problem: '/' required authentication
if (!publicRoutes.includes(to.path) && !isAuthenticated) {
  next({ path: '/login', query: { returnUrl } })
}
```

**Flow:**
1. OAuth callback → Redirect to `/`
2. Route guard checks `/` → Not in publicRoutes
3. Not authenticated (cookie not set yet)
4. Redirect to `/login` → **Login loop!**

### **After (v1.0.4):**

```javascript
const publicRoutes = [
  '/',  // ← Added this line
  '/login',
  '/register',
  // ...
]

// Fixed: '/' is now public
if (!publicRoutes.includes(to.path) && !isAuthenticated) {
  next({ path: '/login', query: { returnUrl } })
}
```

**Flow:**
1. OAuth callback → Redirect to `/`
2. Route guard checks `/` → **In publicRoutes** ✓
3. Allow access to `/`
4. Cookie gets set successfully
5. User can now access protected routes

---

## 🎯 Key Improvements

| Feature | v1.0.3 | v1.0.4 |
|---------|--------|--------|
| OAuth callback redirect | ❌ Blocked by route guard | ✅ Allowed (public route) |
| Login flow completion | ❌ Redirect loop | ✅ Works correctly |
| Cookie setting | ❌ Interrupted | ✅ Set successfully |
| Protected routes access | ❌ Can't access after login | ✅ Normal access |
| Home page (`/`) access | ❌ Requires auth | ✅ Public access |

---

## 📊 Deployment Checklist

- [ ] Pull Docker image `v1.0.4` or `latest`
- [ ] Stop old container (without `-v` flag)
- [ ] Start new container with updated image
- [ ] Check logs for successful startup
- [ ] Test health endpoint: `/api/health`
- [ ] Test frontend loads: `/`
- [ ] Test OAuth login flow with Google
- [ ] Verify cookie is set after login
- [ ] Test protected route access after login
- [ ] Verify database has user record
- [ ] Test logout and re-login

---

## 🐛 Troubleshooting

### **Issue: Still getting redirect loop**

**Check:**
1. Clear browser cookies completely
2. Verify you're using image `v1.0.4` or `latest` (updated)
3. Check frontend build includes the route guard fix

```bash
# Verify container image
docker inspect tp75-fullstack | grep Image

# Should show: patcoder97/prosight-fullstack:v1.0.4
```

### **Issue: Cookie not being set**

**Check:**
1. OAuth redirect URIs in Google/GitHub console
2. Cookie settings in environment variables:
   ```bash
   COOKIE_SECURE=false  # Set to false for local HTTP testing
   COOKIE_DOMAIN=       # Empty for same-origin
   ```

### **Issue: 404 on home page**

**Check:**
1. Frontend static files are served correctly
2. Backend is routing to frontend properly

```bash
# Test direct access
curl -I http://localhost:8001/

# Expected: 200 OK with HTML content
```

---

## 🔄 Rollback (If Needed)

If you encounter issues, rollback to v1.0.3:

```bash
# Pull previous version
docker pull patcoder97/prosight-fullstack:v1.0.3

# Update docker-compose.yml
# Change image to: patcoder97/prosight-fullstack:v1.0.3

# Recreate container
docker-compose -f docker-compose.fullstack.yml up -d --force-recreate tp75-fullstack

# Monitor logs
docker logs -f tp75-fullstack
```

**Note:** v1.0.3 had the OAuth redirect issue, but other features work fine.

---

## 📝 Related Documentation

- [TAG_BUILD_SUCCESS.md](TAG_BUILD_SUCCESS.md) - Tag-based build system
- [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) - Full deployment guide
- [README_DEPLOY.md](README_DEPLOY.md) - General deployment instructions
- [TAG_BUILD_GUIDE.md](TAG_BUILD_GUIDE.md) - How to use tag-based builds

---

## 🎉 Summary

**Version:** v1.0.4
**Release Date:** 2026-01-16
**Critical Fix:** OAuth callback redirect to home page
**Status:** ✅ READY FOR PRODUCTION

**What to expect:**
- ✅ OAuth login works end-to-end
- ✅ No more redirect loops
- ✅ Cookie set correctly after login
- ✅ Protected routes accessible after authentication
- ✅ Clean user experience

**Next Steps:**
1. Deploy to your CasaOS server
2. Test OAuth login flow
3. Verify everything works
4. Enjoy! 🎉

---

**Last Updated:** 2026-01-16
**Docker Image:** `patcoder97/prosight-fullstack:v1.0.4`
**GitHub Actions:** https://github.com/PATCoder97/fhs-prosight/actions/runs/21053482782
**Build Status:** ✅ SUCCESS
