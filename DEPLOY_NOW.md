# 🚀 Deploy Fullstack Container - Quick Start Guide

## ✅ Current Status

- ✅ Alembic hardcoded DB connection **FIXED** - now uses `DATABASE_URL` from environment
- ✅ Alembic migrations **RESET** - single comprehensive migration for all tables
- ✅ Fullstack Docker image **BUILT** - available on Docker Hub
- ✅ GitHub Actions **COMPLETED** - all builds successful

---

## 📦 Image Information

**Docker Hub Image:** `patcoder97/prosight-fullstack:latest`

**Latest Commits:**
```bash
e32623c - docs: add alembic migration reset summary
2eeeb72 - feat: reset alembic migrations to single initial schema
ffac0aa - fix: use DATABASE_URL from environment in alembic migrations
```

**Image Size:** ~1.5GB (includes Node.js frontend build + Python backend + dependencies)

---

## 🎯 Deployment Steps

### **Step 1: SSH vào CasaOS Server**

```bash
ssh user@your-casaos-server-ip
```

### **Step 2: Pull Latest Fullstack Image**

```bash
# Pull image mới nhất từ Docker Hub
docker pull patcoder97/prosight-fullstack:latest

# Verify image pulled successfully
docker images | grep prosight-fullstack
```

Expected output:
```
patcoder97/prosight-fullstack   latest    <image-id>   X minutes ago   1.5GB
```

### **Step 3: Download docker-compose.fullstack.yml**

```bash
# Tạo thư mục cho project
mkdir -p ~/fhs-prosight
cd ~/fhs-prosight

# Download docker-compose file
wget https://raw.githubusercontent.com/PATCoder97/fhs-prosight/main/docker-compose.fullstack.yml

# Hoặc nếu có git
git clone https://github.com/PATCoder97/fhs-prosight.git
cd fhs-prosight
```

### **Step 4: Configure Environment Variables**

Edit `docker-compose.fullstack.yml` và thay đổi các giá trị sau:

```yaml
environment:
  # Database - Thay password
  - POSTGRES_PASSWORD=your_strong_password_here_123456

  # OAuth - Thay credentials từ Google Cloud Console
  - GOOGLE_CLIENT_ID=123456789-abcdefg.apps.googleusercontent.com
  - GOOGLE_CLIENT_SECRET=GOCSPX-your_secret_here

  # OAuth - Thay credentials từ GitHub
  - GITHUB_CLIENT_ID=Iv1.your_github_client_id
  - GITHUB_CLIENT_SECRET=your_github_secret_here

  # PIDKey.com API - Thay API key
  - PIDKEY_API_KEY=your_pidkey_api_key_here

  # JWT Secret - Tạo secret key mới (ít nhất 32 ký tự)
  - SECRET_KEY=your_super_secret_key_minimum_32_characters_long

  # Cookie Settings (cho production HTTPS)
  - COOKIE_SECURE=true  # true nếu dùng HTTPS qua Cloudflare
```

**⚠️ IMPORTANT:** Cũng cần update password trong `DATABASE_URL`:
```yaml
- DATABASE_URL=postgresql+asyncpg://tp75user:your_strong_password_here_123456@tp75-db:5432/tp75db
```

### **Step 5: Deploy Containers**

```bash
# Deploy với docker-compose
docker-compose -f docker-compose.fullstack.yml up -d

# Check containers đang chạy
docker ps | grep tp75

# Expected output:
# tp75-fullstack   (fullstack container)
# tp75-db          (PostgreSQL database)
```

### **Step 6: Run Database Migration**

```bash
# Chờ 10-15 giây để container khởi động xong

# Run migration để tạo tables
docker exec tp75-fullstack alembic upgrade head

# Expected output:
# INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
# INFO  [alembic.runtime.migration] Will assume transactional DDL.
# INFO  [alembic.runtime.migration] Running upgrade  -> 0846970e5b1f, initial_schema_all_tables
```

### **Step 7: Verify Deployment**

```bash
# 1. Check logs
docker logs tp75-fullstack --tail 50

# Expected: No errors, should see:
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://0.0.0.0:8001

# 2. Test frontend (from server)
curl http://localhost:8001

# Expected: HTML response with <!DOCTYPE html>

# 3. Test API health endpoint
curl http://localhost:8001/api/health

# Expected: {"status": "healthy"}

# 4. Verify migration applied
docker exec tp75-fullstack alembic current

# Expected: 0846970e5b1f (head)

# 5. Check database tables created
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

1. Vào: https://console.cloud.google.com/apis/credentials
2. Chọn OAuth 2.0 Client ID của bạn
3. Thêm **Authorized redirect URIs:**

```
https://hrsfhs.tphomelab.io.vn/api/auth/google/callback
```

**Không cần thêm:**
- ❌ `http://` version (chỉ cần HTTPS)
- ❌ `api.tphomelab.io.vn` subdomain (không cần nữa với fullstack)

### **GitHub OAuth App**

1. Vào: https://github.com/settings/developers
2. Chọn OAuth App của bạn
3. Thêm **Authorization callback URL:**

```
https://hrsfhs.tphomelab.io.vn/api/auth/github/callback
```

---

## 🔧 Cloudflare Configuration

### **DNS Records**

Chỉ cần 1 DNS record duy nhất:

```
Type    Name        Content             Proxy Status
A       hrsfhs      YOUR_SERVER_IP      Proxied (🟠)
```

**Hoặc nếu dùng root domain:**
```
Type    Name    Content             Proxy Status
A       @       YOUR_SERVER_IP      Proxied (🟠)
```

### **SSL/TLS Settings**

```
Encryption mode: Full (hoặc Full strict nếu có SSL cert trên server)
Always Use HTTPS: ON
Minimum TLS Version: 1.2
```

### **Cloudflare Tunnel (Nếu dùng)**

Update `config.yml`:

```yaml
tunnel: YOUR_TUNNEL_ID
credentials-file: /path/to/credentials.json

ingress:
  # Chỉ cần 1 hostname
  - hostname: hrsfhs.tphomelab.io.vn
    service: http://localhost:8001

  - service: http_status:404
```

Restart tunnel:
```bash
sudo systemctl restart cloudflared
```

---

## 🔍 Troubleshooting

### **Issue: Container không start**

```bash
# Xem logs
docker logs tp75-fullstack --tail 100

# Common issues:
# 1. Port 8001 đã được dùng?
sudo netstat -tulpn | grep 8001

# 2. Database chưa ready?
docker logs tp75-db --tail 50

# 3. Environment variables missing?
docker exec tp75-fullstack env | grep -E "GOOGLE|GITHUB|DATABASE"
```

### **Issue: Migration failed**

```bash
# Check alembic version
docker exec tp75-fullstack alembic current

# If shows old version, manually upgrade
docker exec tp75-fullstack alembic upgrade head

# If migration conflicts, reset database:
docker exec tp75-db psql -U tp75user -d postgres -c "DROP DATABASE tp75db;"
docker exec tp75-db psql -U tp75user -d postgres -c "CREATE DATABASE tp75db;"
docker exec tp75-fullstack alembic upgrade head
```

### **Issue: Frontend không load**

```bash
# Kiểm tra static files có tồn tại không
docker exec tp75-fullstack ls -la /app/static/

# Expected output:
# index.html
# assets/
# favicon.ico

# Nếu không có → Image chưa được build đúng
# Pull lại image:
docker pull patcoder97/prosight-fullstack:latest
docker-compose -f docker-compose.fullstack.yml up -d --force-recreate
```

### **Issue: OAuth không work**

```bash
# 1. Check redirect URI trong logs
docker logs tp75-fullstack | grep -i "redirect_uri"

# 2. Verify OAuth credentials
docker exec tp75-fullstack env | grep -E "GOOGLE_CLIENT|GITHUB_CLIENT"

# 3. Test OAuth endpoint
curl http://localhost:8001/api/auth/login/google

# Expected: 302 redirect to Google
```

---

## 📊 Monitoring

### **Check Container Status**

```bash
# Container health
docker ps | grep tp75

# Resource usage
docker stats tp75-fullstack tp75-db

# Logs (follow)
docker logs -f tp75-fullstack
```

### **Check Database**

```bash
# Connect to database
docker exec -it tp75-db psql -U tp75user -d tp75db

# Check table counts
SELECT 'users' as table_name, COUNT(*) FROM users
UNION ALL
SELECT 'employees', COUNT(*) FROM employees
UNION ALL
SELECT 'evaluations', COUNT(*) FROM evaluations
UNION ALL
SELECT 'dormitory_bills', COUNT(*) FROM dormitory_bills
UNION ALL
SELECT 'pidms_keys', COUNT(*) FROM pidms_keys;
```

---

## 🎉 Testing OAuth Flow

Sau khi deploy xong:

1. **Truy cập frontend:**
   ```
   https://hrsfhs.tphomelab.io.vn
   ```

2. **Click "Login with Google" hoặc "Login with GitHub"**

3. **Expected flow:**
   - Redirect to Google/GitHub OAuth page ✅
   - User authorizes app ✅
   - Redirect back to `https://hrsfhs.tphomelab.io.vn/api/auth/google/callback` ✅
   - Frontend receives access token via cookie ✅
   - User logged in successfully ✅

---

## 🔄 Update/Restart Containers

### **Update to Latest Image**

```bash
# Pull latest image
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
docker-compose -f docker-compose.fullstack.yml restart tp75-fullstack

# Restart only database
docker-compose -f docker-compose.fullstack.yml restart tp75-db
```

---

## 📝 Quick Reference

| Endpoint | URL | Description |
|----------|-----|-------------|
| Frontend | `https://hrsfhs.tphomelab.io.vn` | Vue.js Web UI |
| API Docs | `https://hrsfhs.tphomelab.io.vn/docs` | Swagger UI |
| API ReDoc | `https://hrsfhs.tphomelab.io.vn/redoc` | ReDoc API Docs |
| Health Check | `https://hrsfhs.tphomelab.io.vn/api/health` | API Health |
| Google OAuth | `https://hrsfhs.tphomelab.io.vn/api/auth/login/google` | Login with Google |
| GitHub OAuth | `https://hrsfhs.tphomelab.io.vn/api/auth/login/github` | Login with GitHub |

---

## 📞 Support

- **GitHub Issues:** https://github.com/PATCoder97/fhs-prosight/issues
- **Docker Hub:** https://hub.docker.com/r/patcoder97/prosight-fullstack
- **Documentation:**
  - [DEPLOY_FULLSTACK.md](./DEPLOY_FULLSTACK.md) - Comprehensive deployment guide
  - [ALEMBIC_RESET_SUMMARY.md](./ALEMBIC_RESET_SUMMARY.md) - Migration reset details
  - [OAUTH_CLOUDFLARE_FIX.md](./OAUTH_CLOUDFLARE_FIX.md) - OAuth troubleshooting

---

**Last Updated:** 2026-01-16
**Image:** `patcoder97/prosight-fullstack:latest`
**Migration:** `0846970e5b1f` (initial_schema_all_tables)
**Status:** ✅ Ready to deploy
