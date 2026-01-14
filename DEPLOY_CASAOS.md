# 🚀 Hướng dẫn Deploy trên CasaOS

## 📋 Tổng quan

Stack này bao gồm:
- **Backend API** (FastAPI + Python) - Port 8001
- **Frontend Web UI** (Vue.js + Nginx) - Port 5173
- **PostgreSQL Database** - Internal only

## 🎯 Yêu cầu

- CasaOS đã cài đặt
- Docker và Docker Compose
- Kết nối internet để pull images từ Docker Hub

## 📦 Images sử dụng

- Backend: `patcoder97/prosight-backend:dev`
- Frontend: `patcoder97/prosight-frontend:dev`
- Database: `postgres:16-alpine`

---

## 🔧 Cách 1: Deploy bằng CasaOS App Store (Khuyến nghị)

### Bước 1: Import vào CasaOS

1. Mở CasaOS Dashboard
2. Vào **App Store** → Click **Import**
3. Paste nội dung file `docker-compose.prod.yml` vào
4. Click **Install**

### Bước 2: Cấu hình Environment Variables

⚠️ **QUAN TRỌNG**: Trước khi install, bạn cần thay thế các placeholder sau:

```yaml
# OAuth Credentials - Lấy từ Google Cloud Console & GitHub Settings
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GITHUB_CLIENT_ID=your_github_client_id_here
GITHUB_CLIENT_SECRET=your_github_client_secret_here

# PIDKey API - Lấy từ pidkey.com
PIDKEY_API_KEY=your_pidkey_api_key_here

# JWT Secret - Tạo random string mạnh cho production
SECRET_KEY=supersecrettuan123456_change_in_production
```

### Bước 3: Khởi động

Sau khi install, CasaOS sẽ tự động:
1. Pull images từ Docker Hub
2. Tạo network `tp75-fhs_network`
3. Khởi động PostgreSQL database
4. Chạy database migrations (Backend)
5. Khởi động Backend API
6. Khởi động Frontend Web UI

### Bước 4: Truy cập

- **Frontend Web UI**: `http://your-casaos-ip:5173`
- **Backend API Docs**: `http://your-casaos-ip:8001/docs`
- **Backend API ReDoc**: `http://your-casaos-ip:8001/redoc`

---

## 🔧 Cách 2: Deploy bằng Docker Compose CLI

### Bước 1: Download docker-compose.prod.yml

```bash
# SSH vào CasaOS server
ssh user@your-casaos-ip

# Download file
wget https://raw.githubusercontent.com/PATCoder97/fhs-prosight/main/docker-compose.prod.yml

# Hoặc clone repo
git clone https://github.com/PATCoder97/fhs-prosight.git
cd fhs-prosight
```

### Bước 2: Tạo file .env (Tùy chọn)

Tạo file `.env` để quản lý credentials dễ hơn:

```bash
# Tạo file .env
nano .env
```

Nội dung file `.env`:

```env
# Database
POSTGRES_USER=tp75user
POSTGRES_PASSWORD=tp75pass_change_this
POSTGRES_DATABASE=tp75db

# OAuth
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GITHUB_CLIENT_ID=your_github_client_id_here
GITHUB_CLIENT_SECRET=your_github_client_secret_here

# JWT
SECRET_KEY=your_super_secret_key_at_least_32_characters_long
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# PIDKey API
PIDKEY_API_KEY=your_pidkey_api_key_here

# Frontend
FRONTEND_URL=http://your-casaos-ip:5173
```

### Bước 3: Deploy

```bash
# Deploy với docker-compose
docker-compose -f docker-compose.prod.yml up -d

# Hoặc nếu dùng file .env
docker-compose --env-file .env -f docker-compose.prod.yml up -d
```

### Bước 4: Kiểm tra logs

```bash
# Xem logs của tất cả services
docker-compose -f docker-compose.prod.yml logs -f

# Xem logs của từng service
docker-compose -f docker-compose.prod.yml logs -f tp75-api
docker-compose -f docker-compose.prod.yml logs -f tp75-web
docker-compose -f docker-compose.prod.yml logs -f tp75-db
```

---

## 🔍 Kiểm tra trạng thái

### Kiểm tra containers đang chạy

```bash
docker ps | grep tp75
```

Bạn sẽ thấy 3 containers:
- `tp75-api` - Backend API
- `tp75-web` - Frontend Web UI
- `tp75-db` - PostgreSQL Database

### Kiểm tra health

```bash
# Backend health check
curl http://localhost:8001/health

# Frontend health check
curl http://localhost:5173
```

### Kiểm tra database

```bash
# Truy cập PostgreSQL
docker exec -it tp75-db psql -U tp75user -d tp75db

# List tables
\dt

# Exit
\q
```

---

## 🔄 Update stack

### Update images mới nhất

```bash
# Pull images mới
docker-compose -f docker-compose.prod.yml pull

# Restart services
docker-compose -f docker-compose.prod.yml up -d

# Hoặc gộp 1 lệnh
docker-compose -f docker-compose.prod.yml pull && docker-compose -f docker-compose.prod.yml up -d
```

### Update từ Git

```bash
# Pull code mới nhất
git pull origin main

# Rebuild và restart
docker-compose -f docker-compose.prod.yml up -d --build
```

---

## 🗑️ Gỡ cài đặt

### Dừng tất cả services

```bash
docker-compose -f docker-compose.prod.yml down
```

### Xóa volumes (⚠️ Cảnh báo: Mất dữ liệu!)

```bash
# Xóa tất cả bao gồm volumes
docker-compose -f docker-compose.prod.yml down -v

# Xóa thủ công data folder
rm -rf /DATA/AppData/tp75-fhs
```

---

## 📊 Quản lý Database

### Backup Database

```bash
# Backup database
docker exec tp75-db pg_dump -U tp75user tp75db > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restore Database

```bash
# Restore từ backup
docker exec -i tp75-db psql -U tp75user -d tp75db < backup_20260114.sql
```

---

## 🔒 Bảo mật

### Checklist bảo mật trước khi deploy production:

- [ ] Đổi `POSTGRES_PASSWORD` thành password mạnh
- [ ] Đổi `SECRET_KEY` thành random string dài ít nhất 32 ký tự
- [ ] Thay thế OAuth credentials bằng credentials thực
- [ ] Thay thế PIDKey API key bằng key thực
- [ ] Set `COOKIE_SECURE=true` nếu dùng HTTPS
- [ ] Cập nhật `FRONTEND_URL` với domain thực
- [ ] Backup `.env` file ở nơi an toàn
- [ ] Không commit credentials vào Git

### Tạo SECRET_KEY mạnh

```bash
# Cách 1: Dùng openssl
openssl rand -hex 32

# Cách 2: Dùng Python
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

## 🐛 Troubleshooting

### Backend không khởi động được

```bash
# Kiểm tra logs
docker logs tp75-api

# Restart backend
docker restart tp75-api
```

**Lỗi thường gặp:**
- `Database not ready`: Đợi thêm 30s để PostgreSQL khởi động xong
- `alembic.ini not found`: Image cũ, cần pull image mới
- `Authentication failed`: Kiểm tra DATABASE_URL

### Frontend không truy cập được

```bash
# Kiểm tra logs
docker logs tp75-web

# Restart frontend
docker restart tp75-web
```

**Lỗi thường gặp:**
- `502 Bad Gateway`: Backend chưa sẵn sàng, đợi thêm
- `Connection refused`: Kiểm tra port 5173 có bị firewall block

### Database migration failed

```bash
# Kiểm tra database connection
docker exec tp75-api python -c "
from app.database.session import engine
import asyncio
asyncio.run(engine.connect())
"

# Chạy migration thủ công
docker exec tp75-api alembic upgrade head
```

---

## 📝 Environment Variables Reference

### Backend Environment Variables

| Variable | Mô tả | Mặc định | Bắt buộc |
|----------|-------|----------|----------|
| `DATABASE_URL` | PostgreSQL connection string | - | ✅ |
| `SECRET_KEY` | JWT secret key | - | ✅ |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT token expiration | 1440 | ❌ |
| `GOOGLE_CLIENT_ID` | Google OAuth Client ID | - | ⚠️* |
| `GOOGLE_CLIENT_SECRET` | Google OAuth Secret | - | ⚠️* |
| `GITHUB_CLIENT_ID` | GitHub OAuth Client ID | - | ⚠️* |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth Secret | - | ⚠️* |
| `PIDKEY_API_KEY` | PIDKey.com API Key | - | ⚠️* |
| `FHS_HRS_BASE_URL` | FHS HRS Integration URL | - | ⚠️* |
| `FRONTEND_URL` | Frontend URL for CORS | http://localhost:5173 | ❌ |
| `COOKIE_SECURE` | Use secure cookies | false | ❌ |

*⚠️ Cần thiết nếu sử dụng tính năng OAuth/API tương ứng

### Frontend Environment Variables

| Variable | Mô tả | Mặc định | Bắt buộc |
|----------|-------|----------|----------|
| `VITE_API_BASE_URL` | Backend API endpoint | http://localhost:8001/api | ❌ |

---

## 📞 Hỗ trợ

- GitHub Issues: https://github.com/PATCoder97/fhs-prosight/issues
- Docker Hub Backend: https://hub.docker.com/r/patcoder97/prosight-backend
- Docker Hub Frontend: https://hub.docker.com/r/patcoder97/prosight-frontend

---

**Last Updated**: 2026-01-14
