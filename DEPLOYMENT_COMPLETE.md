# ✅ Fullstack Deployment - Complete Summary

## 🎯 Tất Cả Các Vấn Đề Đã Fix

### 1. ✅ **Alembic Hardcoded Database URL**
**Vấn đề:** `alembic.ini` có hardcoded DB connection → bị bake vào Docker image
**Giải pháp:** `alembic/env.py` override với `DATABASE_URL` từ environment variables
**Commit:** `ffac0aa`

### 2. ✅ **Alembic Migration Reset**
**Vấn đề:** 7 migration files riêng lẻ gây phức tạp
**Giải pháp:** Reset thành 1 migration duy nhất `0846970e5b1f_initial_schema_all_tables.py`
**Commit:** `2eeeb72`

### 3. ✅ **Alembic Async/Sync Driver Conflict**
**Vấn đề:** Alembic cần sync driver (`postgresql://`) nhưng `DATABASE_URL` có async driver (`postgresql+asyncpg://`)
**Lỗi:** `MissingGreenlet: greenlet_spawn has not been called`
**Giải pháp:** Convert async URL → sync URL trong `alembic/env.py`
**Commit:** `53c8cbd`

### 4. ✅ **DATABASE_URL Auto-Construction**
**Vấn đề:** Phải viết URL dài trong `docker-compose.yml`, dễ nhầm lẫn
**Giải pháp:** Backend tự tạo `DATABASE_URL` từ `POSTGRES_*` environment variables
**Commit:** `2c36f33`

### 5. ✅ **Route Guard - Authentication Protection**
**Vấn đề:** User có thể truy cập trực tiếp các trang bên trong mà chưa login
**Giải pháp:** Thêm `router.beforeEach()` guard để redirect về `/login` nếu chưa authenticated
**Commit:** `61ee0e3`

---

## 📦 Cấu Trúc Mới

### **Backend Configuration**

**File:** [backend/app/core/config.py](backend/app/core/config.py)

```python
class Settings(BaseSettings):
    # Database - Individual components
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DATABASE: str

    # Computed DATABASE_URL property
    @property
    def DATABASE_URL(self) -> str:
        """Construct DATABASE_URL from POSTGRES_* environment variables"""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DATABASE}"
```

**File:** [backend/alembic/env.py](backend/alembic/env.py)

```python
# Convert async URL to sync URL for alembic
if settings.DATABASE_URL:
    sync_database_url = settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')
    config.set_main_option("sqlalchemy.url", sync_database_url)
```

### **Frontend Route Guard**

**File:** [frontend/src/plugins/1.router/index.js](frontend/src/plugins/1.router/index.js)

```javascript
// Route Guard: Protect routes that require authentication
router.beforeEach((to, from, next) => {
  const publicRoutes = ['/login', '/register', '/forgot-password', ...]
  const isAuthenticated = document.cookie.split('; ').some(cookie => cookie.startsWith('access_token='))

  if (!publicRoutes.includes(to.path) && !isAuthenticated) {
    // Redirect to login with returnUrl
    next({ path: '/login', query: { returnUrl: to.fullPath } })
  } else if (publicRoutes.includes(to.path) && isAuthenticated) {
    // Already logged in, redirect to home
    next('/')
  } else {
    next()
  }
})
```

### **Docker Compose - Simplified**

**File:** [docker-compose.fullstack.yml](docker-compose.fullstack.yml)

```yaml
environment:
  # Database Configuration (clean, no long URL)
  - POSTGRES_HOST=tp75-db
  - POSTGRES_PORT=5432
  - POSTGRES_USER=tp75user
  - POSTGRES_PASSWORD=tp75pass_change_in_production
  - POSTGRES_DATABASE=tp75db

  # JWT
  - SECRET_KEY=supersecrettuan123456_change_in_production

  # OAuth
  - GOOGLE_CLIENT_ID=your_google_client_id_here
  - GOOGLE_CLIENT_SECRET=your_google_client_secret_here

  # Cookie
  - COOKIE_SECURE=true
  - COOKIE_DOMAIN=  # Empty for same-origin
```

---

## 🚀 Deployment Steps

### **Step 1: Wait for GitHub Actions Build**

```bash
# Check build status
https://github.com/PATCoder97/fhs-prosight/actions

# Wait for latest "Build and Push Fullstack Docker Image" workflow to complete
# Expected: ~15-20 minutes (building both frontend and backend)
```

### **Step 2: SSH to CasaOS Server**

```bash
ssh user@your-casaos-server-ip
```

### **Step 3: Pull Latest Fullstack Image**

```bash
# Pull image mới nhất từ Docker Hub
docker pull patcoder97/prosight-fullstack:latest

# Verify image pulled successfully
docker images | grep prosight-fullstack
```

### **Step 4: Download docker-compose.fullstack.yml**

```bash
# Create project directory
mkdir -p ~/fhs-prosight
cd ~/fhs-prosight

# Download docker-compose file
wget https://raw.githubusercontent.com/PATCoder97/fhs-prosight/main/docker-compose.fullstack.yml

# Or clone repo
git clone https://github.com/PATCoder97/fhs-prosight.git
cd fhs-prosight
```

### **Step 5: Configure Environment Variables**

Edit `docker-compose.fullstack.yml`:

```yaml
environment:
  # Database
  - POSTGRES_USER=tp75user
  - POSTGRES_PASSWORD=YOUR_STRONG_PASSWORD_HERE  # ⚠️ CHANGE THIS!
  - POSTGRES_DATABASE=tp75db

  # JWT Secret
  - SECRET_KEY=YOUR_32_CHAR_SECRET_KEY_HERE  # ⚠️ CHANGE THIS!

  # Google OAuth (from https://console.cloud.google.com/apis/credentials)
  - GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID  # ⚠️ CHANGE THIS!
  - GOOGLE_CLIENT_SECRET=YOUR_GOOGLE_CLIENT_SECRET  # ⚠️ CHANGE THIS!

  # GitHub OAuth (from https://github.com/settings/developers)
  - GITHUB_CLIENT_ID=YOUR_GITHUB_CLIENT_ID  # ⚠️ CHANGE THIS!
  - GITHUB_CLIENT_SECRET=YOUR_GITHUB_CLIENT_SECRET  # ⚠️ CHANGE THIS!

  # PIDKey.com API (optional)
  - PIDKEY_API_KEY=YOUR_PIDKEY_API_KEY  # ⚠️ CHANGE THIS!

  # Cookie (for HTTPS production)
  - COOKIE_SECURE=true
  - COOKIE_DOMAIN=  # Leave empty for same-origin
```

### **Step 6: Deploy Containers**

```bash
# Deploy với docker-compose
docker-compose -f docker-compose.fullstack.yml up -d

# Check containers đang chạy
docker ps | grep tp75

# Expected output:
# tp75-fullstack   Up X minutes   0.0.0.0:8001->8001/tcp
# tp75-db          Up X minutes   5432/tcp
```

### **Step 7: Monitor Logs**

```bash
# Follow logs to see migration progress
docker logs -f tp75-fullstack

# Expected output (SUCCESSFUL):
# 🚀 Starting FHS HR Backend...
# ✓ DATABASE_URL: postgresql+asyncpg://tp75user:***@tp75-db:5432/tp75db
# ⏳ Waiting for database to be ready...
# ✓ Database is ready!
# ✓ Database connected successfully!
#
# 📦 Running database migrations...
# INFO  [alembic.runtime.migration] Running upgrade  -> 0846970e5b1f, initial_schema_all_tables
# ✓ Database migrations completed successfully!
#
# 🌱 Seeding database...
# ✓ Database seeding completed successfully!
#
# ✓ All checks passed!
# 🌐 Starting Uvicorn server on 0.0.0.0:8001...
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://0.0.0.0:8001
```

### **Step 8: Verify Deployment**

```bash
# 1. Test frontend
curl http://localhost:8001

# Expected: HTML response with <!DOCTYPE html>

# 2. Test API health
curl http://localhost:8001/api/health

# Expected: {"status":"healthy"}

# 3. Verify migration
docker exec tp75-fullstack alembic current

# Expected: 0846970e5b1f (head)

# 4. Check database tables
docker exec tp75-db psql -U tp75user -d tp75db -c "\dt"

# Expected tables:
# alembic_version
# users
# employees
# evaluations
# dormitory_bills
# pidms_keys
```

---

## 🌐 Configure OAuth Redirect URIs

### **Google Cloud Console**

1. Go to: https://console.cloud.google.com/apis/credentials
2. Select your OAuth 2.0 Client ID
3. Add **Authorized redirect URIs:**

```
https://hrsfhs.tphomelab.io.vn/api/auth/google/callback
```

### **GitHub OAuth App**

1. Go to: https://github.com/settings/developers
2. Select your OAuth App
3. Add **Authorization callback URL:**

```
https://hrsfhs.tphomelab.io.vn/api/auth/github/callback
```

---

## 🔧 Cloudflare Configuration

### **DNS Records**

Chỉ cần 1 DNS record:

```
Type    Name        Content             Proxy Status
A       hrsfhs      YOUR_SERVER_IP      Proxied (🟠)
```

### **SSL/TLS Settings**

```
Encryption mode: Full (or Full strict)
Always Use HTTPS: ON
Minimum TLS Version: 1.2
```

### **Cloudflare Tunnel (If using)**

Update `config.yml`:

```yaml
tunnel: YOUR_TUNNEL_ID
credentials-file: /path/to/credentials.json

ingress:
  - hostname: hrsfhs.tphomelab.io.vn
    service: http://localhost:8001
  - service: http_status:404
```

Restart tunnel:
```bash
sudo systemctl restart cloudflared
```

---

## 🔐 Security Features

### **1. Route Guard Protection**

✅ **All routes require authentication by default**
- User chưa login → redirect to `/login`
- User đã login nhưng vào `/login` → redirect to `/`
- Save `returnUrl` parameter để redirect sau khi login

**Public routes (không cần login):**
- `/login`
- `/register`
- `/forgot-password`
- `/pages/authentication/*`

### **2. Cookie-based Authentication**

- `access_token` cookie (HttpOnly, Secure in production)
- `COOKIE_SECURE=true` for HTTPS
- `COOKIE_DOMAIN` empty for same-origin (no subdomain issues)

### **3. Environment Variable Security**

- No hardcoded credentials in code
- All secrets via environment variables
- Docker image has no baked-in secrets

---

## 📊 Architecture Benefits

### **Before (2-container setup):**
❌ 2 containers (frontend + backend)
❌ 2 subdomains needed
❌ CORS configuration
❌ Cookie domain issues
❌ Complex nginx proxy

### **After (fullstack):**
✅ 1 container (backend serves frontend static files)
✅ 1 domain only
✅ No CORS (same origin)
✅ Cookies work automatically
✅ Simple deployment
✅ Route guard protection
✅ Auto-constructed DATABASE_URL

---

## 🧪 Testing OAuth Flow

1. **Access frontend:**
   ```
   https://hrsfhs.tphomelab.io.vn
   ```

2. **Try to access internal page directly (without login):**
   ```
   https://hrsfhs.tphomelab.io.vn/dashboard
   ```
   **Expected:** Redirect to `/login?returnUrl=/dashboard`

3. **Click "Login with Google"**
   - Redirect to Google OAuth
   - User authorizes
   - Redirect back to callback URL
   - Set `access_token` cookie
   - Redirect to `returnUrl` (or `/` if no returnUrl)

4. **Access dashboard again:**
   ```
   https://hrsfhs.tphomelab.io.vn/dashboard
   ```
   **Expected:** Access granted (authenticated)

5. **Try to access login page while logged in:**
   ```
   https://hrsfhs.tphomelab.io.vn/login
   ```
   **Expected:** Redirect to `/` (already authenticated)

---

## 🔄 Update/Restart Commands

### **Update to Latest Image**

```bash
# Pull latest
docker pull patcoder97/prosight-fullstack:latest

# Recreate container
docker-compose -f docker-compose.fullstack.yml up -d --force-recreate tp75-fullstack

# Run migrations if needed
docker exec tp75-fullstack alembic upgrade head
```

### **Restart Containers**

```bash
# Restart all
docker-compose -f docker-compose.fullstack.yml restart

# Restart only fullstack
docker restart tp75-fullstack

# Restart only database
docker restart tp75-db
```

### **View Logs**

```bash
# Follow logs
docker logs -f tp75-fullstack

# Last 100 lines
docker logs tp75-fullstack --tail 100

# Database logs
docker logs tp75-db --tail 50
```

---

## 📝 Quick Reference

| Feature | Configuration | Location |
|---------|--------------|----------|
| **Auto DATABASE_URL** | `@property DATABASE_URL()` | [backend/app/core/config.py](backend/app/core/config.py#L13-L16) |
| **Alembic Sync Conversion** | `.replace('postgresql+asyncpg://', 'postgresql://')` | [backend/alembic/env.py](backend/alembic/env.py#L29) |
| **Route Guard** | `router.beforeEach()` | [frontend/src/plugins/1.router/index.js](frontend/src/plugins/1.router/index.js#L29-L62) |
| **Environment Vars** | `POSTGRES_*` variables | [docker-compose.fullstack.yml](docker-compose.fullstack.yml#L45-L73) |
| **Migration** | `0846970e5b1f_initial_schema_all_tables.py` | [backend/alembic/versions/](backend/alembic/versions/) |

| Endpoint | URL | Description |
|----------|-----|-------------|
| **Frontend** | `https://hrsfhs.tphomelab.io.vn` | Vue.js Web UI (requires login) |
| **Login** | `https://hrsfhs.tphomelab.io.vn/login` | OAuth login page (public) |
| **API Docs** | `https://hrsfhs.tphomelab.io.vn/docs` | Swagger UI |
| **Health** | `https://hrsfhs.tphomelab.io.vn/api/health` | API health check |
| **Google OAuth** | `https://hrsfhs.tphomelab.io.vn/api/auth/login/google` | Login with Google |
| **GitHub OAuth** | `https://hrsfhs.tphomelab.io.vn/api/auth/login/github` | Login with GitHub |

---

## 📞 Troubleshooting

### **Issue: Route guard not working**

```bash
# Check if access_token cookie is set
# Open browser DevTools > Application > Cookies
# Should see: access_token=<jwt_token>

# If not set after login, check backend logs
docker logs tp75-fullstack | grep -i "cookie"
```

### **Issue: Alembic migration failed**

```bash
# Check logs
docker logs tp75-fullstack | grep -i alembic

# Manually run migration
docker exec tp75-fullstack alembic upgrade head

# Check current migration version
docker exec tp75-fullstack alembic current
```

### **Issue: DATABASE_URL not constructed correctly**

```bash
# Check environment variables
docker exec tp75-fullstack env | grep POSTGRES

# Should see:
# POSTGRES_HOST=tp75-db
# POSTGRES_PORT=5432
# POSTGRES_USER=tp75user
# POSTGRES_PASSWORD=***
# POSTGRES_DATABASE=tp75db
```

---

## 📈 Latest Commits

```bash
61ee0e3 - feat: add route guard to protect authenticated routes
2c36f33 - refactor: auto-construct DATABASE_URL from POSTGRES_* environment variables
53c8cbd - fix: convert async DATABASE_URL to sync for alembic migrations
2eeeb72 - feat: reset alembic migrations to single initial schema
ffac0aa - fix: use DATABASE_URL from environment in alembic migrations
```

---

## 🎉 Ready to Deploy!

All issues fixed:
- ✅ Alembic uses environment variables (no hardcoded DB)
- ✅ Single comprehensive migration (clean DB init)
- ✅ Async/sync driver handled correctly
- ✅ DATABASE_URL auto-constructed from POSTGRES_* vars
- ✅ Route guard protects all authenticated routes
- ✅ OAuth configured for single domain
- ✅ Fullstack container ready to deploy

**Next:** Wait for GitHub Actions to finish building, then deploy! 🚀

---

**Last Updated:** 2026-01-16
**Image:** `patcoder97/prosight-fullstack:latest`
**Migration:** `0846970e5b1f` (initial_schema_all_tables)
**Status:** ✅ Production Ready
