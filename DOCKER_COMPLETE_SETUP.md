# FHS ProSight - Complete Docker & CI/CD Setup ✅

## 📦 Tổng quan hoàn chỉnh

Dự án đã được setup đầy đủ với Docker và CI/CD pipeline tự động build images lên Docker Hub.

## 🏗️ Cấu trúc hoàn chỉnh

```
fhs-prosight/
├── backend/
│   ├── Dockerfile              ✅ Multi-stage Python build
│   └── .dockerignore           ✅ Optimized ignore rules
│
├── frontend/
│   ├── Dockerfile              ✅ Multi-stage Node + Nginx
│   ├── nginx.conf              ✅ Production config
│   └── .dockerignore           ✅ Optimized ignore rules
│
├── scripts/                    ✅ Management utilities
│   ├── check-docker-env.sh     # Environment validator
│   ├── deploy.sh               # Auto deployment
│   ├── backup-db.sh            # Database backup
│   ├── restore-db.sh           # Database restore
│   ├── health-monitor.sh       # Service monitoring
│   └── README.md               # Scripts docs
│
├── .github/workflows/          ✅ CI/CD Pipeline
│   ├── main.yml                # Auto build & push to Docker Hub
│   └── README.md               # Workflow documentation
│
├── docker-compose.yml          ✅ Development (build locally)
├── docker-compose.prod.yml     ✅ Production (use Docker Hub images)
├── Makefile                    ✅ Command shortcuts
├── .env.example                ✅ Environment template
├── .dockerignore               ✅ Root ignore rules
│
└── Documentation
    ├── DOCKER_SETUP.md         ✅ Complete setup guide
    ├── DOCKER_QUICK_REFERENCE.md ✅ Quick commands cheat sheet
    ├── DOCKER_HUB_DEPLOYMENT.md  ✅ Production deployment guide
    └── README.md (this file)   ✅ Overview
```

## 🚀 3 Cách Deployment

### 1️⃣ Development (Build locally)

```bash
# Check environment
./scripts/check-docker-env.sh

# Deploy
./scripts/deploy.sh

# Or use Makefile
make up-build
make logs
```

### 2️⃣ Production (Docker Hub images)

```bash
# Pull pre-built images
docker-compose -f docker-compose.prod.yml pull

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Monitor
./scripts/health-monitor.sh
```

### 3️⃣ Manual Docker Run

```bash
# Pull images
docker pull patcoder97/fhs-backend:latest
docker pull patcoder97/fhs-frontend:latest

# Create network
docker network create fhs-network

# Run backend
docker run -d --name fhs-backend \
  --network fhs-network \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/firebase_credentials.json:/app/firebase_credentials.json:ro \
  patcoder97/fhs-backend:latest

# Run frontend
docker run -d --name fhs-frontend \
  --network fhs-network \
  -p 80:80 \
  patcoder97/fhs-frontend:latest
```

## 🔄 CI/CD Pipeline (GitHub Actions)

### Tự động build khi:

1. **Push to main với [build]**
   ```bash
   git commit -m "feat: new feature [build]"
   git push origin main
   # → Builds: patcoder97/fhs-backend:dev, patcoder97/fhs-frontend:dev
   ```

2. **Create Git Tag**
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   # → Builds: patcoder97/fhs-backend:v1.0.0 + latest
   #           patcoder97/fhs-frontend:v1.0.0 + latest
   ```

3. **Manual Trigger**
   - GitHub → Actions → Run workflow

### Setup Required (One-time)

GitHub Repository → Settings → Secrets → Add:
- `DOCKERHUB_USERNAME`: Your Docker Hub username
- `DOCKERHUB_TOKEN`: Your Docker Hub access token

## 📊 Docker Images

### Backend Image
- **Name**: `patcoder97/fhs-backend`
- **Base**: Python 3.11-slim
- **Size**: ~400-500MB
- **Platform**: linux/amd64, linux/arm64

### Frontend Image
- **Name**: `patcoder97/fhs-frontend`
- **Base**: Nginx Alpine
- **Size**: ~25-30MB
- **Platform**: linux/amd64, linux/arm64

### Available Tags
- `latest` - Production stable
- `v1.0.0` - Specific version
- `dev` - Development builds

## 🛠️ Quick Commands Reference

### Makefile Shortcuts

```bash
make help              # Show all commands
make up-build          # Build and start
make down              # Stop services
make logs              # View logs
make shell-backend     # Enter backend container
make shell-frontend    # Enter frontend container
make clean             # Remove containers
make health            # Check health status
```

### Docker Compose

```bash
# Development (build locally)
docker-compose up -d --build
docker-compose logs -f
docker-compose down

# Production (Docker Hub images)
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.prod.yml logs -f
```

### Scripts

```bash
./scripts/check-docker-env.sh    # Validate environment
./scripts/deploy.sh              # Auto deploy
./scripts/backup-db.sh           # Backup database
./scripts/restore-db.sh <file>   # Restore database
./scripts/health-monitor.sh      # Monitor services
```

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| [DOCKER_SETUP.md](DOCKER_SETUP.md) | Complete Docker setup guide |
| [DOCKER_QUICK_REFERENCE.md](DOCKER_QUICK_REFERENCE.md) | Quick commands cheat sheet |
| [DOCKER_HUB_DEPLOYMENT.md](DOCKER_HUB_DEPLOYMENT.md) | Production deployment guide |
| [scripts/README.md](scripts/README.md) | Scripts documentation |
| [.github/workflows/README.md](.github/workflows/README.md) | CI/CD workflow guide |

## 🎯 Recommended Workflow

### For Developers

```bash
# 1. First time setup
cp .env.example .env
# Edit .env with your credentials

# 2. Check environment
./scripts/check-docker-env.sh

# 3. Start development
make up-build

# 4. View logs
make logs

# 5. Make changes, then rebuild
make restart

# 6. Commit with [build] to trigger CI/CD
git commit -m "feat: new feature [build]"
git push
```

### For Production Deployment

```bash
# 1. Backup database first
./scripts/backup-db.sh

# 2. Pull latest images from Docker Hub
docker-compose -f docker-compose.prod.yml pull

# 3. Deploy
docker-compose -f docker-compose.prod.yml up -d

# 4. Verify health
make health

# 5. Monitor
./scripts/health-monitor.sh 60
```

### For Release

```bash
# 1. Test everything locally
make up-build
make test

# 2. Create git tag
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# 3. GitHub Actions auto builds and pushes to Docker Hub

# 4. Deploy on production server
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

## 🔐 Security Checklist

- [x] Separate Dockerfiles for backend and frontend
- [x] Multi-stage builds to reduce image size
- [x] .dockerignore to exclude sensitive files
- [x] Health checks configured
- [x] Resource limits in production compose
- [x] Logging rotation configured
- [x] Build cache optimization
- [x] Multi-platform support (amd64, arm64)
- [ ] Non-root user in containers (TODO)
- [ ] Docker secrets for production (TODO)
- [ ] Image vulnerability scanning (TODO)

## 📈 Performance Features

- ✅ Multi-stage Docker builds
- ✅ Layer caching optimization
- ✅ Registry cache for CI/CD
- ✅ Gzip compression (Frontend)
- ✅ Static file caching (Frontend)
- ✅ Parallel job execution (CI/CD)
- ✅ Multi-platform builds

## 🆘 Troubleshooting

### Quick Fixes

```bash
# Container won't start
docker logs fhs-backend
docker logs fhs-frontend

# Port already in use
docker-compose down
sudo netstat -tuln | grep :8000

# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d

# Database connection error
docker exec fhs-backend env | grep DB_
```

### Common Issues

See detailed troubleshooting in:
- [DOCKER_SETUP.md](DOCKER_SETUP.md#troubleshooting)
- [DOCKER_HUB_DEPLOYMENT.md](DOCKER_HUB_DEPLOYMENT.md#troubleshooting)

## 🔗 Useful Links

- **Docker Hub Backend**: https://hub.docker.com/r/patcoder97/fhs-backend
- **Docker Hub Frontend**: https://hub.docker.com/r/patcoder97/fhs-frontend
- **GitHub Repository**: https://github.com/PATCoder97/fhs-prosight
- **GitHub Actions**: https://github.com/PATCoder97/fhs-prosight/actions

## 📞 Support

If you encounter issues:

1. Check logs: `make logs`
2. Verify health: `make health`
3. Review documentation in this directory
4. Check GitHub Actions workflow status
5. Create issue on GitHub

## ✨ What's Next?

Suggested improvements:

1. **Security Enhancements**
   - Add non-root user to Dockerfiles
   - Implement Docker secrets
   - Set up vulnerability scanning

2. **Monitoring**
   - Add Prometheus metrics
   - Set up Grafana dashboards
   - Configure alerts

3. **Orchestration**
   - Kubernetes manifests
   - Helm charts
   - Docker Swarm stack

4. **CI/CD Enhancements**
   - Automated testing in pipeline
   - Staging environment
   - Automated rollback

---

**Setup Complete!** 🎉

**Last Update**: 2026-01-14
**Version**: 1.0.0
**Tác giả**: TP75
