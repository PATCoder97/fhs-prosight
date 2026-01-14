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
├── scripts/                # Utility scripts
│   ├── check-docker-env.sh # Environment checker
│   ├── deploy.sh           # Quick deployment
│   ├── backup-db.sh        # Database backup
│   ├── restore-db.sh       # Database restore
│   ├── health-monitor.sh   # Service monitoring
│   └── README.md           # Scripts documentation
├── docker-compose.yml      # Orchestration file
├── Makefile               # Docker commands shortcuts
├── .env.example           # Environment template
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

### Quick Start với Scripts (Khuyến nghị)

```bash
# 1. Kiểm tra môi trường trước khi build
./scripts/check-docker-env.sh

# 2. Deploy nhanh (build + start services)
./scripts/deploy.sh

# 3. Monitor services (optional)
./scripts/health-monitor.sh
```

### Quick Start với Makefile

```bash
# Xem tất cả commands
make help

# Build và start services
make up-build

# Xem logs
make logs

# Stop services
make down
```

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

## Utility Scripts

Dự án cung cấp các scripts tiện ích trong thư mục `scripts/`:

### 1. check-docker-env.sh - Kiểm tra môi trường

```bash
./scripts/check-docker-env.sh
```

Kiểm tra:
- Docker và Docker Compose installation
- Docker daemon status
- File .env và các biến môi trường bắt buộc
- firebase_credentials.json
- Dockerfiles và docker-compose.yml
- Disk space

### 2. deploy.sh - Deploy nhanh

```bash
./scripts/deploy.sh
```

Tự động:
- Pull code mới nhất
- Stop containers hiện tại
- Build images (no cache)
- Start services
- Health check
- Hiển thị status

### 3. backup-db.sh - Backup database

```bash
./scripts/backup-db.sh
```

Tính năng:
- Tạo backup với timestamp
- Nén file (gzip)
- Tự động cleanup (giữ 7 backups gần nhất)
- Output: `backups/fhs_prosight_backup_YYYYMMDD_HHMMSS.sql.gz`

### 4. restore-db.sh - Restore database

```bash
./scripts/restore-db.sh backups/fhs_prosight_backup_20260114_120000.sql.gz
```

**CẢNH BÁO**: Sẽ overwrite database hiện tại!

### 5. health-monitor.sh - Monitor services

```bash
# Check mỗi 30 giây (default)
./scripts/health-monitor.sh

# Custom interval (60 giây)
./scripts/health-monitor.sh 60
```

Giám sát:
- Container status
- HTTP health endpoints
- Resource usage (CPU, Memory, Network)
- Alert khi có failures

Chi tiết xem [scripts/README.md](scripts/README.md)

## Makefile Commands

Sử dụng Makefile để đơn giản hóa Docker operations:

```bash
# Xem tất cả commands
make help

# Build và deployment
make build              # Build all images
make build-backend      # Build backend only
make build-frontend     # Build frontend only
make up                 # Start services
make up-build           # Build and start
make down               # Stop services

# Logs và monitoring
make logs               # View all logs
make logs-backend       # View backend logs
make logs-frontend      # View frontend logs
make ps                 # Show containers
make stats              # Resource usage

# Shell access
make shell-backend      # Enter backend container
make shell-frontend     # Enter frontend container

# Maintenance
make restart            # Restart all services
make restart-backend    # Restart backend only
make restart-frontend   # Restart frontend only
make clean              # Stop and remove containers
make prune              # Clean Docker system
make test               # Run backend tests
make health             # Check service health
```

## Database Management

### Backup Strategy

```bash
# Manual backup trước khi deploy
./scripts/backup-db.sh

# Scheduled backup (crontab example)
# Daily backup lúc 2 AM
0 2 * * * cd /path/to/fhs-prosight && ./scripts/backup-db.sh
```

### Restore Workflow

```bash
# 1. List available backups
ls -lh backups/

# 2. Stop services
docker-compose down

# 3. Restore database
./scripts/restore-db.sh backups/fhs_prosight_backup_20260114_120000.sql.gz

# 4. Start services
docker-compose up -d
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
