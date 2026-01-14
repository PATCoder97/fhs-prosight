# 🚀 Fullstack Single-Container Deployment Guide

## 📋 Tổng quan

**GIẢI PHÁP MỚI - KHUYẾN NGHỊ:** Thay vì deploy riêng Backend và Frontend thành 2 containers, giờ bạn có thể deploy **1 container duy nhất** chứa cả Backend API và Frontend static files.

### **Lợi ích:**

✅ **Không còn vấn đề subdomain**
- Chỉ cần 1 domain duy nhất
- Không cần cấu hình COOKIE_DOMAIN
- Không cần X-Forwarded-Proto header detection

✅ **Không còn vấn đề CORS**
- Frontend và API cùng origin
- Cookies tự động work
- Không cần CORS configuration phức tạp

✅ **Đơn giản hơn**
- 1 container thay vì 2
- 1 image thay vì 2
- 1 port thay vì 2

✅ **Ít tài nguyên hơn**
- Chỉ cần 1.5GB RAM (thay vì 1.5GB cho 2 containers)
- Ít network overhead

✅ **Dễ deploy hơn**
- Chỉ cần 1 Docker Hub image
- Không cần cấu hình nginx proxy giữa frontend-backend
- Không cần lo về container networking

---

## 🏗️ Kiến trúc

### **Trước đây (2 containers):**
```
┌─────────────────────┐      ┌─────────────────────┐
│  Frontend (5173)    │──────│  Backend (8001)     │
│  - Nginx            │      │  - FastAPI          │
│  - Vue.js SPA       │      │  - Python           │
└─────────────────────┘      └─────────────────────┘
         │                            │
         └────────────────────────────┘
                     │
         ┌───────────────────────┐
         │  PostgreSQL (5432)    │
         └───────────────────────┘

❌ Vấn đề:
- Cần 2 subdomain (hrsfhs.tphomelab.io.vn + api.tphomelab.io.vn)
- CORS issues
- Cookie domain issues
- X-Forwarded-Proto detection
```

### **Bây giờ (1 container):**
```
┌─────────────────────────────────────┐
│  Fullstack Container (8001)         │
│  ┌───────────────────────────────┐  │
│  │  FastAPI Backend              │  │
│  │  - /api/*  → API endpoints    │  │
│  │  - /docs   → Swagger UI       │  │
│  │  - /redoc  → ReDoc            │  │
│  │  - /*      → Frontend SPA     │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │  Frontend Static Files        │  │
│  │  /app/static/                 │  │
│  │  - index.html                 │  │
│  │  - assets/ (JS, CSS, images)  │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
                 │
     ┌───────────────────────┐
     │  PostgreSQL (5432)    │
     └───────────────────────┘

✅ Lợi ích:
- Chỉ cần 1 domain (hrsfhs.tphomelab.io.vn)
- Không có CORS
- Cookies tự động work
- Đơn giản, dễ maintain
```

---

## 📦 Build và Deploy

### **Option 1: Sử dụng image từ Docker Hub (Khuyến nghị)**

GitHub Actions đang build image mới với fullstack architecture.

#### **Bước 1: Đợi build hoàn tất**

```bash
# Kiểm tra build status
https://github.com/PATCoder97/fhs-prosight/actions

# Đợi build xong (~15-20 phút do phải build cả frontend + backend)
```

#### **Bước 2: Deploy với docker-compose**

```bash
# SSH vào CasaOS server
ssh user@your-casaos-ip

# Clone/pull repo mới nhất
cd /path/to/fhs-prosight
git pull origin main

# Hoặc download file docker-compose.fullstack.yml
wget https://raw.githubusercontent.com/PATCoder97/fhs-prosight/main/docker-compose.fullstack.yml

# Pull image từ Docker Hub
docker pull patcoder97/prosight-fullstack:latest

# Deploy
docker-compose -f docker-compose.fullstack.yml up -d

# Xem logs
docker-compose -f docker-compose.fullstack.yml logs -f
```

#### **Bước 3: Truy cập**

```bash
# Frontend Web UI
http://your-server-ip:8001

# Backend API Docs
http://your-server-ip:8001/docs

# Backend API ReDoc
http://your-server-ip:8001/redoc
```

---

### **Option 2: Build local (Nếu muốn customize)**

```bash
# Clone repo
git clone https://github.com/PATCoder97/fhs-prosight.git
cd fhs-prosight

# Build fullstack image
docker build -f Dockerfile.fullstack -t patcoder97/prosight-fullstack:latest .

# Deploy
docker-compose -f docker-compose.fullstack.yml up -d
```

**⚠️ Lưu ý:** Build local mất ~15-20 phút do phải:
1. Install frontend dependencies (npm install)
2. Build frontend (npm run build)
3. Install backend dependencies (pip install)
4. Copy frontend build artifacts vào backend static folder

---

## 🔧 Configuration

### **Environment Variables cần thay đổi:**

Edit file `docker-compose.fullstack.yml`:

```yaml
services:
  tp75-fullstack:
    environment:
      # Database - Thay password
      - POSTGRES_PASSWORD=your_strong_password_here

      # OAuth - Thay credentials
      - GOOGLE_CLIENT_ID=your_google_client_id
      - GOOGLE_CLIENT_SECRET=your_google_client_secret
      - GITHUB_CLIENT_ID=your_github_client_id
      - GITHUB_CLIENT_SECRET=your_github_client_secret

      # PIDKey.com API - Thay API key
      - PIDKEY_API_KEY=your_pidkey_api_key

      # JWT Secret - Thay secret key
      - SECRET_KEY=your_super_secret_key_at_least_32_characters

      # Cookie Settings (cho production HTTPS)
      - COOKIE_SECURE=true  # true nếu dùng HTTPS

      # KHÔNG CẦN các biến sau nữa:
      # - FRONTEND_URL (không cần vì cùng origin)
      # - COOKIE_DOMAIN (không cần vì cùng domain)
```

### **Google Cloud Console - OAuth Redirect URIs:**

Bây giờ chỉ cần 1 redirect URI đơn giản:

```
Authorized redirect URIs:
✅ https://hrsfhs.tphomelab.io.vn/api/auth/google/callback

Không cần thêm:
❌ https://api.tphomelab.io.vn/api/auth/google/callback (subdomain riêng)
❌ http://hrsfhs.tphomelab.io.vn/api/auth/google/callback (fallback HTTP)
```

---

## 🌐 Cloudflare Configuration

### **DNS Records:**

Chỉ cần 1 record duy nhất:

```
Type    Name    Content             Proxy
A       @       YOUR_SERVER_IP      Proxied (orange cloud)

HOẶC

A       hrs     YOUR_SERVER_IP      Proxied (orange cloud)
```

**Không cần:**
- ❌ `api` subdomain record
- ❌ Multiple DNS records

### **SSL/TLS Settings:**

```
Encryption mode: Full (hoặc Full strict)
Always Use HTTPS: ON
```

### **Cloudflare Tunnel (Nếu dùng):**

```yaml
# config.yml
tunnel: YOUR_TUNNEL_ID
credentials-file: /path/to/credentials.json

ingress:
  # Chỉ cần 1 hostname
  - hostname: hrsfhs.tphomelab.io.vn
    service: http://localhost:8001

  - service: http_status:404
```

---

## 🔄 Migration từ 2-container sang 1-container

Nếu bạn đang chạy setup cũ (2 containers), hãy migrate như sau:

### **Bước 1: Backup data**

```bash
# Backup database
docker exec tp75-db pg_dump -U tp75user tp75db > backup_$(date +%Y%m%d).sql
```

### **Bước 2: Stop containers cũ**

```bash
# Stop cả stack cũ
docker-compose -f docker-compose.prod.yml down

# KHÔNG xóa volumes (-v) để giữ data
```

### **Bước 3: Deploy fullstack mới**

```bash
# Pull image mới
docker pull patcoder97/prosight-fullstack:latest

# Deploy với fullstack
docker-compose -f docker-compose.fullstack.yml up -d
```

### **Bước 4: Verify**

```bash
# Kiểm tra containers đang chạy
docker ps | grep tp75

# Expected:
# tp75-fullstack    (thay vì tp75-api + tp75-web)
# tp75-db

# Test frontend
curl http://localhost:8001

# Test API
curl http://localhost:8001/api/health

# Test OAuth
# Truy cập: http://localhost:8001/login
```

---

## 📊 So sánh 2 phương pháp

| Feature | 2-Container (Cũ) | 1-Container Fullstack (Mới) |
|---------|------------------|------------------------------|
| **Containers** | 3 (frontend + backend + db) | 2 (fullstack + db) |
| **Images** | 2 | 1 |
| **Ports** | 2 (5173 + 8001) | 1 (8001) |
| **Domains** | 2 (api.x.com + x.com) | 1 (x.com) |
| **CORS** | Cần config | Không cần |
| **Cookie Domain** | Cần config | Không cần |
| **X-Forwarded-Proto** | Cần detect | Không cần |
| **Memory** | ~1.5GB (512MB + 1GB + db) | ~1.5GB (1.5GB + db) |
| **Build Time** | ~18 phút (6+12) | ~18 phút (parallel) |
| **Complexity** | ⚠️ Cao | ✅ Thấp |
| **Recommended** | ❌ Không | ✅ Có |

---

## 🔍 Troubleshooting

### **Issue: Container không start**

```bash
# Xem logs
docker logs tp75-fullstack --tail 100

# Kiểm tra common issues:
# 1. Port 8001 đã được dùng?
sudo netstat -tulpn | grep 8001

# 2. Database chưa ready?
docker logs tp75-db --tail 50
```

### **Issue: Frontend không load**

```bash
# Kiểm tra static files có tồn tại không
docker exec tp75-fullstack ls -la /app/static/

# Expected:
# index.html
# assets/
# favicon.ico
# ...

# Nếu không có → Image chưa được build đúng
# Pull lại image hoặc rebuild
```

### **Issue: API không work**

```bash
# Test API endpoint
curl http://localhost:8001/api/health

# Kiểm tra logs
docker logs tp75-fullstack | grep -i error
```

---

## 📝 Files Structure

```
fhs-prosight/
├── Dockerfile.fullstack           # Fullstack Dockerfile
├── docker-compose.fullstack.yml   # Fullstack docker-compose
├── backend/
│   ├── app/
│   │   ├── main.py               # ✨ Updated: Serve static files
│   │   ├── routers/
│   │   └── ...
│   ├── start.sh
│   └── requirements.txt
└── frontend/
    ├── src/
    ├── package.json
    └── ...
```

---

## 🎯 Next Steps

1. **Đợi GitHub Actions build xong** (~18 phút)
2. **Pull image mới**: `docker pull patcoder97/prosight-fullstack:latest`
3. **Deploy**: `docker-compose -f docker-compose.fullstack.yml up -d`
4. **Cấu hình OAuth credentials** trong docker-compose.fullstack.yml
5. **Thêm OAuth redirect URI** vào Google Cloud Console
6. **Test OAuth flow**: `https://hrsfhs.tphomelab.io.vn/login`

---

## 📞 Hỗ trợ

- GitHub Issues: https://github.com/PATCoder97/fhs-prosight/issues
- Docker Hub: https://hub.docker.com/r/patcoder97/prosight-fullstack

---

**Last Updated**: 2026-01-14
**Image**: `patcoder97/prosight-fullstack:latest`
**Architecture**: Single-container fullstack (Backend + Frontend)
