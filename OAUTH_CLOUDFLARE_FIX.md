# 🔧 OAuth + Cloudflare Troubleshooting Guide

## 🐛 Vấn đề gặp phải

### Lỗi 1: `redirect_uri_mismatch` từ Google OAuth

**Triệu chứng:**
- Truy cập `https://api.tphomelab.io.vn/api/auth/login/google`
- Google báo lỗi: "Error 400: redirect_uri_mismatch"
- Request details hiển thị: `redirect_uri=http://api.tphomelab.io.vn/...` (HTTP thay vì HTTPS)

**Nguyên nhân:**
Backend nhận request từ Cloudflare qua HTTP (vì Cloudflare terminate SSL), nên `request.url_for()` tạo redirect URI với scheme `http://` thay vì `https://`.

### Lỗi 2: Frontend hardcode `localhost:8001`

**Triệu chứng:**
- Nút "Đăng nhập với Google" redirect đến `http://localhost:8001/api/auth/login/google`
- Không hoạt động khi deploy trên domain khác

**Nguyên nhân:**
Frontend được build với `VITE_API_BASE_URL=http://localhost:8001/api` hardcoded vào bundle, không thể thay đổi runtime.

---

## ✅ Giải pháp đã implement

### Fix 1: Backend - Detect HTTPS từ X-Forwarded-Proto header

**Files đã sửa:**
- `backend/app/integrations/google_auth_client.py`
- `backend/app/integrations/github_auth_client.py`

**Thay đổi:**
```python
def _get_redirect_uri(self, request):
    """
    Generate correct redirect URI with proper scheme (http/https).
    Handles reverse proxy scenarios (Cloudflare, nginx, etc.)
    """
    # Get base redirect URI from FastAPI
    redirect_uri = str(request.url_for("google_callback"))

    # Check if behind reverse proxy with HTTPS
    # Cloudflare and most reverse proxies set X-Forwarded-Proto header
    forwarded_proto = request.headers.get("x-forwarded-proto")
    if forwarded_proto == "https":
        redirect_uri = redirect_uri.replace("http://", "https://")

    return redirect_uri
```

**Commit:** `c66f02d` - fix: handle HTTPS redirect URIs behind reverse proxy for OAuth

### Fix 2: Frontend - Sử dụng relative paths trong production

**Files đã sửa:**
- `frontend/src/utils/api.js`
- `frontend/src/composables/useApi.js`
- `frontend/src/views/pages/authentication/AuthProvider.vue`

**Thay đổi:**
```javascript
// Runtime API base URL detection
function getApiBaseUrl() {
  // Production: Use relative path /api which nginx will proxy to backend
  if (import.meta.env.PROD) {
    return '/api'
  }
  // Development: Use VITE_API_BASE_URL or localhost
  return import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001/api'
}
```

**Lợi ích:**
- Frontend tự động sử dụng domain hiện tại (không cần rebuild cho mỗi domain)
- `/api` được nginx proxy đến backend container qua docker network
- Hoạt động với bất kỳ domain nào: localhost, tphomelab.io.vn, casaos IP, etc.

**Commit:** `2652db3` - fix: use relative API paths in production for proper domain handling

---

## 🚀 Deploy các fixes

### Option 1: Deploy từ Docker Hub (Khuyến nghị)

Đợi GitHub Actions build xong (~12-18 phút), sau đó:

```bash
# 1. Pull images mới nhất
docker pull patcoder97/prosight-backend:dev
docker pull patcoder97/prosight-frontend:dev

# 2. Restart containers
docker restart tp75-api tp75-web

# Hoặc nếu dùng docker-compose
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

### Option 2: Build local ngay lập tức

Nếu muốn test ngay không đợi GitHub Actions:

```bash
# Build backend
cd backend
docker build -t patcoder97/prosight-backend:dev .

# Build frontend
cd ../frontend
docker build -t patcoder97/prosight-frontend:dev .

# Restart containers
docker restart tp75-api tp75-web
```

---

## 🔍 Verify fixes đã hoạt động

### Test 1: Kiểm tra backend OAuth redirect URI

```bash
# Truy cập qua HTTPS domain
curl -I https://api.tphomelab.io.vn/api/auth/login/google

# Kiểm tra response header Location
# Phải chứa: redirect_uri=https://api.tphomelab.io.vn/api/auth/google/callback
```

### Test 2: Kiểm tra frontend sử dụng relative path

1. Mở browser DevTools (F12)
2. Truy cập `https://tphomelab.io.vn` (hoặc frontend domain của bạn)
3. Click nút "Đăng nhập với Google"
4. Kiểm tra URL redirect: phải là `https://tphomelab.io.vn/api/auth/login/google` (không có localhost)

### Test 3: OAuth flow hoàn chỉnh

1. Click "Đăng nhập với Google"
2. Chọn tài khoản Google
3. Cho phép quyền truy cập
4. Phải redirect về `https://tphomelab.io.vn/auth-callback` và login thành công

---

## 📋 Google Cloud Console Configuration

Đảm bảo đã thêm tất cả redirect URIs cần thiết:

```
Authorized redirect URIs:
✅ http://127.0.0.1:8001/api/auth/google/callback       (Local dev)
✅ http://localhost:8001/api/auth/google/callback       (Local dev)
✅ https://api.tphomelab.io.vn/api/auth/google/callback (Production HTTPS)
✅ http://api.tphomelab.io.vn/api/auth/google/callback  (Production HTTP fallback)
```

**Note:** Thay đổi có thể mất 5 phút - vài giờ để Google cập nhật.

---

## 🌐 Cloudflare Configuration

### SSL/TLS Settings

**Khuyến nghị:** SSL/TLS encryption mode = **Full** hoặc **Full (strict)**

- ❌ **Flexible**: Cloudflare ↔ Origin dùng HTTP (không an toàn)
- ✅ **Full**: Cloudflare ↔ Origin dùng HTTPS (self-signed cert OK)
- ✅ **Full (strict)**: Cloudflare ↔ Origin dùng HTTPS (valid cert required)

### Headers forwarded by Cloudflare

Cloudflare tự động forward các headers sau:
- `X-Forwarded-Proto`: `https` hoặc `http`
- `X-Forwarded-For`: Client IP
- `X-Real-IP`: Client IP
- `CF-Connecting-IP`: Cloudflare client IP

Backend đã được cấu hình để detect `X-Forwarded-Proto` header.

### Always Use HTTPS

**Khuyến nghị:** Enable "Always Use HTTPS" trong Cloudflare

Settings → SSL/TLS → Edge Certificates → Always Use HTTPS: **On**

Điều này đảm bảo:
- HTTP requests tự động redirect sang HTTPS
- `X-Forwarded-Proto` header luôn là `https`

---

## 🐛 Troubleshooting

### Issue: Vẫn bị `redirect_uri_mismatch` sau khi deploy

**Checklist:**
1. ✅ Đã pull/build image mới? `docker images | grep prosight-backend`
2. ✅ Đã restart container? `docker ps | grep tp75-api`
3. ✅ Cloudflare forwarding `X-Forwarded-Proto`? Check logs: `docker logs tp75-api | grep forwarded`
4. ✅ Google Cloud Console đã cập nhật? Đợi thêm 10-30 phút

**Debug command:**
```bash
# Kiểm tra request headers backend nhận được
docker logs tp75-api --tail 100 | grep -i "x-forwarded"
```

### Issue: Frontend vẫn redirect đến localhost

**Checklist:**
1. ✅ Đã pull/build frontend image mới? `docker images | grep prosight-frontend`
2. ✅ Đã restart container? `docker ps | grep tp75-web`
3. ✅ Clear browser cache và hard reload (Ctrl+Shift+R)
4. ✅ Kiểm tra browser console có errors?

**Debug:**
```bash
# Kiểm tra frontend bundle có relative path không
docker exec tp75-web grep -r "localhost:8001" /usr/share/nginx/html/assets/

# Nếu vẫn có localhost:8001 → image chưa rebuild
```

### Issue: Nginx không proxy /api requests

**Checklist:**
1. ✅ Backend container đang chạy? `docker ps | grep tp75-api`
2. ✅ Cả 2 containers cùng network? `docker network inspect tp75-fhs_network`
3. ✅ Nginx config đúng? `docker exec tp75-web cat /etc/nginx/conf.d/default.conf`

**Fix:**
```bash
# Kiểm tra nginx logs
docker logs tp75-web

# Reload nginx config
docker exec tp75-web nginx -s reload
```

---

## 📊 Architecture Overview

```
User Browser (HTTPS)
    ↓
Cloudflare Proxy
    ↓ (HTTP, X-Forwarded-Proto: https)
Frontend Container (nginx:5173)
    ↓ /api/* → proxy_pass
Backend Container (uvicorn:8001)
    ↓
PostgreSQL Container (postgres:5432)
```

**Request Flow:**
1. User truy cập `https://tphomelab.io.vn`
2. Cloudflare terminate SSL, forward HTTP request với `X-Forwarded-Proto: https`
3. Nginx nhận request, serve static files hoặc proxy `/api/*` đến backend
4. Backend detect `X-Forwarded-Proto: https`, tạo OAuth redirect URI với HTTPS
5. User redirect đến Google OAuth với correct HTTPS callback URL

---

## 📝 Environment Variables Reference

### Backend (.env hoặc docker-compose)

```env
# OAuth Credentials
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GITHUB_CLIENT_ID=your_github_client_id_here
GITHUB_CLIENT_SECRET=your_github_client_secret_here

# Frontend URL (for cookie redirect after OAuth)
FRONTEND_URL=https://tphomelab.io.vn

# Cookie Settings
COOKIE_SECURE=true  # Set true nếu dùng HTTPS
```

### Frontend (.env - chỉ dùng khi dev local)

```env
# Development only - Production sẽ tự động dùng relative path
VITE_API_BASE_URL=http://localhost:8001/api
```

---

## 🎯 Quick Reference

| Scenario | Frontend URL | Backend API URL | OAuth Callback URL |
|----------|--------------|-----------------|-------------------|
| Local Dev | http://localhost:5173 | http://localhost:8001/api | http://localhost:8001/api/auth/google/callback |
| CasaOS HTTP | http://192.168.1.100:5173 | http://192.168.1.100:8001/api | http://192.168.1.100:8001/api/auth/google/callback |
| Production HTTPS | https://tphomelab.io.vn | https://tphomelab.io.vn/api | https://api.tphomelab.io.vn/api/auth/google/callback |

**Note:** Production frontend tự động dùng relative path `/api`, nginx sẽ proxy đến backend.

---

## 🆘 Liên hệ hỗ trợ

- GitHub Issues: https://github.com/PATCoder97/fhs-prosight/issues
- Docker Hub Backend: https://hub.docker.com/r/patcoder97/prosight-backend
- Docker Hub Frontend: https://hub.docker.com/r/patcoder97/prosight-frontend

---

**Last Updated**: 2026-01-14
**Fixes Commits:**
- Backend: `c66f02d` + `4229390`
- Frontend: `2652db3` + `b5caa6f`
