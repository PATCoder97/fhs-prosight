# 🍪 Subdomain Cookie Setup Guide

## 📋 Vấn đề

Khi sử dụng subdomain riêng cho API và Frontend:
- **API**: `api.tphomelab.io.vn`
- **Frontend**: `tphomelab.io.vn`

Cookies được set bởi API subdomain (`api.tphomelab.io.vn`) **KHÔNG** tự động accessible từ root domain (`tphomelab.io.vn`), gây ra lỗi authentication failed sau OAuth callback.

## ✅ Giải pháp: COOKIE_DOMAIN

Backend đã được cập nhật để hỗ trợ `COOKIE_DOMAIN` parameter, cho phép cookies được share giữa các subdomain.

---

## 🔧 Cấu hình

### **Option 1: Sử dụng chung domain (Khuyến nghị)**

Cả API và Frontend cùng truy cập qua một domain duy nhất:
- **Frontend**: `https://tphomelab.io.vn`
- **Backend API**: `https://tphomelab.io.vn/api` (Nginx proxy)

**Cấu hình:**
```env
COOKIE_DOMAIN=
# Leave empty - cookies work on same domain
```

**Ưu điểm:**
- ✅ Đơn giản, không cần COOKIE_DOMAIN
- ✅ Bảo mật hơn (cookies không leak sang subdomain khác)
- ✅ Nginx tự động proxy `/api` requests đến backend

**Nhược điểm:**
- ❌ Cần cấu hình Nginx/Cloudflare Tunnel phức tạp hơn

---

### **Option 2: Subdomain riêng với COOKIE_DOMAIN**

API và Frontend ở subdomain khác nhau:
- **Frontend**: `https://tphomelab.io.vn`
- **Backend API**: `https://api.tphomelab.io.vn`

**Cấu hình:**
```env
COOKIE_DOMAIN=.tphomelab.io.vn
# Note: Leading dot (.) is REQUIRED for subdomain wildcard
```

**Ưu điểm:**
- ✅ API và Frontend tách biệt hoàn toàn
- ✅ Dễ scale (API có thể deploy riêng server)
- ✅ Dễ cấu hình Cloudflare Tunnel

**Nhược điểm:**
- ⚠️ Cookies được share với TẤT CẢ subdomain (*.tphomelab.io.vn)
- ⚠️ Potential security risk nếu có subdomain khác không tin cậy

---

## 📝 Cách cấu hình chi tiết

### **1. Update Backend Environment Variables**

#### **Nếu dùng Docker Compose:**

Sửa file `docker-compose.prod.yml`:

```yaml
services:
  tp75-api:
    environment:
      # ... other vars ...

      # Frontend & Cookie Settings
      - FRONTEND_URL=https://tphomelab.io.vn
      - COOKIE_SECURE=true  # MUST be true for HTTPS
      - COOKIE_DOMAIN=.tphomelab.io.vn  # Add this line
```

#### **Nếu dùng .env file:**

Tạo/sửa file `backend/.env`:

```env
# Frontend & Cookie Settings
FRONTEND_URL=https://tphomelab.io.vn
COOKIE_SECURE=true
COOKIE_DOMAIN=.tphomelab.io.vn
```

---

### **2. Deploy Backend mới**

GitHub Actions đang build backend image mới với COOKIE_DOMAIN support.

**Theo dõi build:**
```bash
# GitHub Actions
https://github.com/PATCoder97/fhs-prosight/actions

# Hoặc dùng gh CLI
gh run list --limit 3
```

**Sau khi build xong (~6 phút):**

```bash
# SSH vào server
ssh user@your-server-ip

# Pull image mới
docker pull patcoder97/prosight-backend:dev

# Cập nhật environment variables
# Option A: Sửa docker-compose.prod.yml (như trên)
nano docker-compose.prod.yml

# Option B: Set env var trực tiếp khi restart
docker stop tp75-api
docker rm tp75-api
docker run -d \
  --name tp75-api \
  --network tp75-fhs_network \
  -p 8001:8001 \
  -e COOKIE_DOMAIN=.tphomelab.io.vn \
  -e FRONTEND_URL=https://tphomelab.io.vn \
  -e COOKIE_SECURE=true \
  # ... other env vars ...
  patcoder97/prosight-backend:dev

# Option C: Dùng docker-compose (Khuyến nghị)
docker-compose -f docker-compose.prod.yml up -d
```

---

### **3. Verify Cookie Domain**

#### **Test 1: Kiểm tra cookie được set với correct domain**

1. Mở browser DevTools (F12) → Application → Cookies
2. Truy cập: `https://api.tphomelab.io.vn/api/auth/login/google`
3. Login với Google
4. Sau khi redirect về frontend, kiểm tra cookie:

**Expected:**
```
Name: access_token
Domain: .tphomelab.io.vn  ✅ (có dấu chấm ở đầu)
Path: /
Secure: true
HttpOnly: true
SameSite: Lax
```

**Nếu KHÔNG có COOKIE_DOMAIN:**
```
Name: access_token
Domain: api.tphomelab.io.vn  ❌ (không có dấu chấm, chỉ work trên api subdomain)
```

#### **Test 2: Frontend có thể đọc cookie**

1. Sau OAuth callback, frontend redirect về `https://tphomelab.io.vn/auth-callback`
2. Kiểm tra DevTools → Application → Cookies trên `tphomelab.io.vn`
3. Cookie `access_token` phải hiển thị với domain `.tphomelab.io.vn`

#### **Test 3: API calls từ frontend thành công**

```bash
# Từ frontend (tphomelab.io.vn), call API
curl https://tphomelab.io.vn/api/auth/me \
  -H "Cookie: access_token=YOUR_TOKEN" \
  --cookie-jar -

# Hoặc từ browser console
fetch('/api/auth/me', { credentials: 'include' })
  .then(r => r.json())
  .then(console.log)
```

**Expected:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "User Name",
  ...
}
```

---

## 🌐 Cloudflare Configuration

### **DNS Records**

```
Type    Name    Content             Proxy
A       @       YOUR_SERVER_IP      Proxied (orange cloud)
A       api     YOUR_SERVER_IP      Proxied (orange cloud)
```

### **SSL/TLS Settings**

- **Encryption mode**: Full hoặc Full (strict)
- **Always Use HTTPS**: On
- **Automatic HTTPS Rewrites**: On

### **Cloudflare Tunnel (Alternative)**

Nếu dùng Cloudflare Tunnel thay vì expose ports:

```yaml
# config.yml
tunnel: YOUR_TUNNEL_ID
credentials-file: /path/to/credentials.json

ingress:
  # Frontend
  - hostname: tphomelab.io.vn
    service: http://localhost:5173

  # Backend API
  - hostname: api.tphomelab.io.vn
    service: http://localhost:8001

  - service: http_status:404
```

---

## 🔒 Security Considerations

### **COOKIE_DOMAIN với wildcard subdomain**

⚠️ **Lưu ý quan trọng:**

Khi set `COOKIE_DOMAIN=.tphomelab.io.vn`, cookie sẽ accessible từ:
- ✅ `tphomelab.io.vn`
- ✅ `api.tphomelab.io.vn`
- ⚠️ `ANYTHING.tphomelab.io.vn` (bất kỳ subdomain nào!)

**Rủi ro:**
- Nếu bạn có subdomain khác không tin cậy (VD: `test.tphomelab.io.vn` do người khác control)
- Subdomain đó có thể đọc được authentication cookie
- **Giải pháp:** Chỉ tạo subdomain tin cậy hoặc dùng domain riêng cho các service không tin cậy

### **COOKIE_SECURE flag**

⚠️ **Bắt buộc với HTTPS:**

Khi dùng HTTPS, **PHẢI** set:
```env
COOKIE_SECURE=true
```

Nếu không, browser sẽ không gửi cookie qua HTTPS requests.

**Development local (HTTP):**
```env
COOKIE_SECURE=false  # Only for localhost testing
```

---

## 🐛 Troubleshooting

### Issue: Cookie không được set sau OAuth callback

**Checklist:**
1. ✅ Backend đã rebuild với code mới? `docker images | grep prosight-backend`
2. ✅ Environment variable đã set? `docker exec tp75-api env | grep COOKIE_DOMAIN`
3. ✅ COOKIE_SECURE=true nếu dùng HTTPS?
4. ✅ Domain có dấu chấm ở đầu? `.tphomelab.io.vn` (không phải `tphomelab.io.vn`)

**Debug:**
```bash
# Kiểm tra backend logs
docker logs tp75-api --tail 100 | grep -i cookie

# Kiểm tra environment variables
docker exec tp75-api printenv | grep COOKIE
```

### Issue: Frontend không nhận được cookie

**Checklist:**
1. ✅ Cookie domain khớp với domain frontend?
   - Frontend: `tphomelab.io.vn`
   - Cookie domain: `.tphomelab.io.vn` ✅
   - Cookie domain: `api.tphomelab.io.vn` ❌
2. ✅ Đã clear browser cookies cũ?
   - DevTools → Application → Cookies → Clear all
3. ✅ Browser console có errors?
   - Check for CORS errors
   - Check for SameSite warnings

**Test manually:**
```bash
# Set cookie manually để test
curl -v https://tphomelab.io.vn/api/auth/me \
  --cookie "access_token=YOUR_TOKEN"

# Kiểm tra response headers có Set-Cookie không
curl -v https://api.tphomelab.io.vn/api/auth/login/google 2>&1 | grep -i set-cookie
```

### Issue: Cookie bị reject bởi browser

**Common causes:**
- ❌ `COOKIE_SECURE=false` nhưng đang dùng HTTPS
- ❌ Domain không khớp (e.g., cookie domain `example.com` nhưng site là `www.example.com`)
- ❌ SameSite setting không đúng

**Fix:**
```env
# Production HTTPS
COOKIE_SECURE=true
COOKIE_DOMAIN=.tphomelab.io.vn

# Development HTTP (localhost only)
COOKIE_SECURE=false
COOKIE_DOMAIN=  # Leave empty for localhost
```

---

## 📊 Cookie Configuration Matrix

| Scenario | FRONTEND_URL | COOKIE_DOMAIN | COOKIE_SECURE | Cookie accessible from |
|----------|--------------|---------------|---------------|------------------------|
| **Local Dev** | http://localhost:5173 | (empty) | false | localhost only |
| **Same Domain** | https://tphomelab.io.vn | (empty) | true | tphomelab.io.vn only |
| **Subdomains** | https://tphomelab.io.vn | .tphomelab.io.vn | true | *.tphomelab.io.vn (all subdomains) |
| **API Subdomain** | https://api.tphomelab.io.vn | .tphomelab.io.vn | true | *.tphomelab.io.vn (all subdomains) |

---

## 🎯 Khuyến nghị cho production

### **Option A: Single Domain (Recommended for security)**

```
User → https://tphomelab.io.vn → Cloudflare
                                      ↓
                              Nginx (Port 80/443)
                                      ↓
                         ┌────────────┴────────────┐
                         ↓                         ↓
                   Frontend (5173)          Backend (8001)
                   (serve static)           (proxy /api/*)
```

**Config:**
```env
FRONTEND_URL=https://tphomelab.io.vn
COOKIE_DOMAIN=  # Empty
COOKIE_SECURE=true
```

### **Option B: Separate Subdomains (Recommended for scalability)**

```
User → https://tphomelab.io.vn → Cloudflare → Frontend (5173)
User → https://api.tphomelab.io.vn → Cloudflare → Backend (8001)
```

**Config:**
```env
FRONTEND_URL=https://tphomelab.io.vn
COOKIE_DOMAIN=.tphomelab.io.vn
COOKIE_SECURE=true
```

---

## 📞 Hỗ trợ

- GitHub Issues: https://github.com/PATCoder97/fhs-prosight/issues
- Docker Hub Backend: https://hub.docker.com/r/patcoder97/prosight-backend

---

**Last Updated**: 2026-01-14
**Feature Commit**: `79921ef` - feat: add COOKIE_DOMAIN support for subdomain cookie sharing
**Build Trigger**: `54f5cba` - trigger: rebuild backend with COOKIE_DOMAIN support
