# Docker Setup Guide - FHS ProSight

Hướng dẫn build và chạy ứng dụng FHS ProSight với Docker.

## Cấu trúc Docker

Dự án được chia thành 2 Docker images riêng biệt:

```
fhs-prosight/
├── backend/
│   ├── Dockerfile          # Backend image (Python FastAPI)
│   └── .dockerignore
├── frontend/
│   ├── Dockerfile          # Frontend image (Vue.js + Nginx)
│   ├── nginx.conf          # Nginx configuration
│   └── .dockerignore
├── docker-compose.yml      # Orchestration file
└── DOCKER_SETUP.md        # File này
```

## Yêu cầu

- Docker Engine 20.10+
- Docker Compose 2.0+
- File `.env` với các biến môi trường cần thiết

## Cấu hình môi trường

Tạo file `.env` ở thư mục root với nội dung:

```env
# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname
DB_HOST=your-db-host
DB_PORT=5432
DB_NAME=your-db-name
DB_USER=your-db-user
DB_PASSWORD=your-db-password

# Firebase
FIREBASE_SERVICE_ACCOUNT_PATH=/app/firebase_credentials.json
FIREBASE_API_KEY=your-firebase-api-key

# API Keys
PIDKEY_API_KEY=your-pidkey-api-key

# App Settings
SECRET_KEY=your-secret-key
ENVIRONMENT=production
CORS_ORIGINS=http://localhost:3000,http://localhost:80
```

## Cách sử dụng

### 1. Build và chạy tất cả services

```bash
# Build và start cả backend + frontend
docker-compose up -d --build

# Xem logs
docker-compose logs -f

# Xem logs của service cụ thể
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 2. Build từng service riêng lẻ

#### Backend

```bash
# Build backend image
cd backend
docker build -t fhs-backend:latest .

# Chạy backend container
docker run -d \
  --name fhs-backend \
  -p 8000:8000 \
  --env-file ../.env \
  -v $(pwd)/firebase_credentials.json:/app/firebase_credentials.json:ro \
  fhs-backend:latest
```

#### Frontend

```bash
# Build frontend image
cd frontend
docker build -t fhs-frontend:latest .

# Chạy frontend container
docker run -d \
  --name fhs-frontend \
  -p 80:80 \
  fhs-frontend:latest
```

### 3. Quản lý containers

```bash
# Dừng tất cả services
docker-compose down

# Dừng và xóa volumes
docker-compose down -v

# Restart services
docker-compose restart

# Restart service cụ thể
docker-compose restart backend
docker-compose restart frontend

# Xem trạng thái
docker-compose ps

# Xem resource usage
docker stats
```

### 4. Debugging

```bash
# Vào trong backend container
docker-compose exec backend bash

# Vào trong frontend container
docker-compose exec frontend sh

# Xem logs real-time
docker-compose logs -f --tail=100

# Kiểm tra health check
docker inspect fhs-backend | grep -A 10 Health
docker inspect fhs-frontend | grep -A 10 Health
```

## Ports

- **Frontend**: http://localhost:80
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Production Deployment

### Build optimized images

```bash
# Backend - Multi-stage build đã tối ưu
docker build -t fhs-backend:v1.0.0 ./backend

# Frontend - Multi-stage build với Nginx
docker build -t fhs-frontend:v1.0.0 ./frontend
```

### Push to registry (Docker Hub / AWS ECR / GCP GCR)

```bash
# Tag images
docker tag fhs-backend:v1.0.0 your-registry/fhs-backend:v1.0.0
docker tag fhs-frontend:v1.0.0 your-registry/fhs-frontend:v1.0.0

# Push to registry
docker push your-registry/fhs-backend:v1.0.0
docker push your-registry/fhs-frontend:v1.0.0
```

### Deploy với docker-compose trên server

```bash
# Pull images từ registry
docker-compose pull

# Start services
docker-compose up -d

# Scale services (nếu cần)
docker-compose up -d --scale backend=3
```

## Tối ưu hóa

### Backend Dockerfile

- ✅ Multi-stage build (builder + runtime)
- ✅ Python slim image để giảm kích thước
- ✅ Không cache pip packages
- ✅ Health check với curl
- ✅ Non-root user (nên thêm)

### Frontend Dockerfile

- ✅ Multi-stage build (Node builder + Nginx runtime)
- ✅ Alpine images cho kích thước nhỏ
- ✅ Gzip compression
- ✅ Static file caching
- ✅ API proxy tới backend
- ✅ Vue Router SPA support

## Troubleshooting

### Backend không start được

```bash
# Kiểm tra logs
docker-compose logs backend

# Kiểm tra environment variables
docker-compose exec backend env | grep DATABASE

# Kiểm tra database connection
docker-compose exec backend python -c "from app.database.session import engine; print(engine.url)"
```

### Frontend không load được

```bash
# Kiểm tra Nginx config
docker-compose exec frontend nginx -t

# Reload Nginx
docker-compose exec frontend nginx -s reload

# Kiểm tra static files
docker-compose exec frontend ls -la /usr/share/nginx/html
```

### Kết nối giữa frontend và backend bị lỗi

```bash
# Kiểm tra network
docker network inspect fhs-prosight_fhs-network

# Ping từ frontend sang backend
docker-compose exec frontend ping backend

# Kiểm tra proxy settings trong nginx.conf
docker-compose exec frontend cat /etc/nginx/conf.d/default.conf
```

## Clean up

```bash
# Xóa containers và networks
docker-compose down

# Xóa containers, networks, và volumes
docker-compose down -v

# Xóa images
docker rmi fhs-backend:latest fhs-frontend:latest

# Xóa tất cả unused resources
docker system prune -a
```

## Notes

- File `firebase_credentials.json` phải được đặt trong thư mục `backend/` trước khi build
- Backend container chạy với port 8000, frontend proxy API requests từ `/api/*` tới backend
- Frontend Nginx serve static files và handle Vue Router với SPA fallback
- Health checks được cấu hình cho cả 2 services để đảm bảo reliability

## Security Best Practices

1. Không commit file `.env` và `firebase_credentials.json` vào Git
2. Sử dụng Docker secrets cho production
3. Chạy containers với non-root user
4. Scan images với `docker scan` trước khi deploy
5. Giới hạn resources cho containers (CPU, Memory)
6. Sử dụng read-only filesystems khi có thể
7. Cập nhật base images thường xuyên

---

**Tác giả**: TP75
**Cập nhật**: 2026-01-14
