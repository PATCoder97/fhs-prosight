# FHS ProSight - Docker Quick Reference

## 🚀 Quick Start

```bash
# 1. Kiểm tra môi trường
./scripts/check-docker-env.sh

# 2. Deploy
./scripts/deploy.sh

# 3. Truy cập
# Frontend: http://localhost:80
# Backend:  http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## 📁 Cấu trúc Docker Images

### Backend Image
- **Base**: Python 3.11-slim
- **Framework**: FastAPI
- **Port**: 8000
- **Health check**: `/health` endpoint

### Frontend Image
- **Base**: Node 18 (builder) + Nginx Alpine (runtime)
- **Framework**: Vue.js 3
- **Port**: 80
- **Features**: Gzip, caching, API proxy

## 🛠️ Lệnh Thường Dùng

### Development

```bash
# Start với Makefile
make up-build          # Build và start
make logs              # Xem logs
make shell-backend     # Vào backend container
make shell-frontend    # Vào frontend container

# Start với docker-compose
docker-compose up -d --build
docker-compose logs -f
docker-compose exec backend bash
docker-compose exec frontend sh
```

### Monitoring

```bash
# Health check
make health

# Resource usage
make stats

# Continuous monitoring
./scripts/health-monitor.sh 30
```

### Database

```bash
# Backup
./scripts/backup-db.sh

# Restore
./scripts/restore-db.sh backups/fhs_prosight_backup_*.sql.gz

# List backups
ls -lh backups/
```

### Cleanup

```bash
make down              # Stop services
make clean             # Stop và xóa containers
make prune             # Xóa tất cả (cẩn thận!)
```

## 📦 Image Sizes (Estimated)

- Backend: ~400-500MB (Python + dependencies)
- Frontend: ~25-30MB (Nginx + static files)

## 🔧 Troubleshooting

### Container không start

```bash
# Xem logs
docker-compose logs [service_name]

# Kiểm tra environment
docker-compose exec backend env

# Rebuild từ đầu
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Database connection lỗi

```bash
# Test connection từ backend
docker-compose exec backend python -c "from app.database.session import engine; print(engine.url)"

# Kiểm tra .env
cat .env | grep DB_
```

### Frontend không kết nối backend

```bash
# Kiểm tra network
docker network inspect fhs-prosight_fhs-network

# Test từ frontend
docker-compose exec frontend ping backend

# Xem Nginx config
docker-compose exec frontend cat /etc/nginx/conf.d/default.conf
```

## 📚 Documentation

- [DOCKER_SETUP.md](DOCKER_SETUP.md) - Hướng dẫn chi tiết
- [scripts/README.md](scripts/README.md) - Scripts documentation
- [.env.example](.env.example) - Environment template

## 🔄 Workflow

### Development Workflow

1. **Check environment** → `./scripts/check-docker-env.sh`
2. **Deploy** → `./scripts/deploy.sh`
3. **Monitor** → `./scripts/health-monitor.sh`
4. **Develop** → Edit code, auto-rebuild if needed
5. **Check logs** → `make logs`

### Production Workflow

1. **Backup DB** → `./scripts/backup-db.sh`
2. **Pull code** → `git pull origin main`
3. **Deploy** → `./scripts/deploy.sh`
4. **Verify** → `make health`
5. **Monitor** → `./scripts/health-monitor.sh 60`

## 🔐 Security Checklist

- [ ] `.env` file không được commit
- [ ] `firebase_credentials.json` không được commit
- [ ] Containers chạy với non-root user (TODO)
- [ ] Images được scan security vulnerabilities
- [ ] Resource limits được set (CPU, Memory)
- [ ] Secrets được manage qua Docker secrets (production)
- [ ] Base images được update thường xuyên

## 📊 Monitoring Endpoints

- **Backend Health**: http://localhost:8000/health
- **Frontend**: http://localhost:80/
- **API Docs**: http://localhost:8000/docs
- **Redoc**: http://localhost:8000/redoc

## 🆘 Support

Nếu gặp vấn đề:

1. Đọc logs: `make logs`
2. Kiểm tra health: `make health`
3. Xem troubleshooting trong [DOCKER_SETUP.md](DOCKER_SETUP.md)
4. Check scripts documentation: [scripts/README.md](scripts/README.md)

---

**Last Update**: 2026-01-14
**Version**: 1.0.0
