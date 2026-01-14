# Docker Hub Deployment Guide

Hướng dẫn deploy FHS ProSight sử dụng pre-built images từ Docker Hub.

## 📦 Docker Hub Images

- **Backend**: https://hub.docker.com/r/patcoder97/fhs-backend
- **Frontend**: https://hub.docker.com/r/patcoder97/fhs-frontend

## 🚀 Quick Deploy

### Option 1: Docker Compose với Pre-built Images

Tạo file `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  backend:
    image: patcoder97/fhs-backend:latest
    container_name: fhs-backend
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - DB_HOST=${DB_HOST}
      - DB_PORT=${DB_PORT}
      - DB_NAME=${DB_NAME}
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - FIREBASE_SERVICE_ACCOUNT_PATH=${FIREBASE_SERVICE_ACCOUNT_PATH}
      - FIREBASE_API_KEY=${FIREBASE_API_KEY}
      - PIDKEY_API_KEY=${PIDKEY_API_KEY}
      - SECRET_KEY=${SECRET_KEY}
      - ENVIRONMENT=${ENVIRONMENT:-production}
      - CORS_ORIGINS=${CORS_ORIGINS}
    volumes:
      - ./logs:/app/logs
      - ./firebase_credentials.json:/app/firebase_credentials.json:ro
    networks:
      - fhs-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  frontend:
    image: patcoder97/fhs-frontend:latest
    container_name: fhs-frontend
    restart: unless-stopped
    ports:
      - "80:80"
    depends_on:
      - backend
    networks:
      - fhs-network
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:80/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s

networks:
  fhs-network:
    driver: bridge
```

Deploy:

```bash
# 1. Tạo file .env
cp .env.example .env
# Edit .env với thông tin thực tế

# 2. Pull images
docker-compose -f docker-compose.prod.yml pull

# 3. Start services
docker-compose -f docker-compose.prod.yml up -d

# 4. Xem logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Option 2: Docker Run Commands

```bash
# Create network
docker network create fhs-network

# Pull images
docker pull patcoder97/fhs-backend:latest
docker pull patcoder97/fhs-frontend:latest

# Run backend
docker run -d \
  --name fhs-backend \
  --network fhs-network \
  -p 8000:8000 \
  -e DATABASE_URL="${DATABASE_URL}" \
  -e DB_HOST="${DB_HOST}" \
  -e DB_PORT="${DB_PORT}" \
  -e DB_NAME="${DB_NAME}" \
  -e DB_USER="${DB_USER}" \
  -e DB_PASSWORD="${DB_PASSWORD}" \
  -e FIREBASE_API_KEY="${FIREBASE_API_KEY}" \
  -e PIDKEY_API_KEY="${PIDKEY_API_KEY}" \
  -e SECRET_KEY="${SECRET_KEY}" \
  -e ENVIRONMENT="production" \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/firebase_credentials.json:/app/firebase_credentials.json:ro \
  --restart unless-stopped \
  patcoder97/fhs-backend:latest

# Run frontend
docker run -d \
  --name fhs-frontend \
  --network fhs-network \
  -p 80:80 \
  --restart unless-stopped \
  patcoder97/fhs-frontend:latest
```

## 📌 Image Tags

### Production (Stable)
```bash
# Latest stable version
docker pull patcoder97/fhs-backend:latest
docker pull patcoder97/fhs-frontend:latest

# Specific version
docker pull patcoder97/fhs-backend:v1.0.0
docker pull patcoder97/fhs-frontend:v1.0.0
```

### Development (Latest features)
```bash
# Development builds from main branch
docker pull patcoder97/fhs-backend:dev
docker pull patcoder97/fhs-frontend:dev
```

## 🔄 Update Strategy

### Rolling Update (Zero Downtime)

```bash
# 1. Pull new images
docker pull patcoder97/fhs-backend:latest
docker pull patcoder97/fhs-frontend:latest

# 2. Update backend (one at a time if scaled)
docker-compose -f docker-compose.prod.yml up -d --no-deps backend

# 3. Wait for health check
sleep 10
curl -f http://localhost:8000/health

# 4. Update frontend
docker-compose -f docker-compose.prod.yml up -d --no-deps frontend

# 5. Verify
curl -f http://localhost:80/
```

### Blue-Green Deployment

```bash
# 1. Start new version with different ports
docker run -d \
  --name fhs-backend-green \
  --network fhs-network \
  -p 8001:8000 \
  ... \
  patcoder97/fhs-backend:latest

# 2. Test new version
curl http://localhost:8001/health

# 3. Switch traffic (update Nginx/Load Balancer)

# 4. Stop old version
docker stop fhs-backend
docker rm fhs-backend
```

## 🛡️ Production Best Practices

### 1. Use Specific Version Tags

❌ **Bad** (unstable):
```yaml
image: patcoder97/fhs-backend:latest
```

✅ **Good** (stable):
```yaml
image: patcoder97/fhs-backend:v1.0.0
```

### 2. Health Checks

Always configure health checks:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### 3. Resource Limits

```yaml
services:
  backend:
    image: patcoder97/fhs-backend:latest
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### 4. Logging

```yaml
services:
  backend:
    image: patcoder97/fhs-backend:latest
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 5. Secrets Management

Use Docker secrets (Swarm) or environment files:

```bash
# .env.prod (never commit!)
DATABASE_URL=postgresql://...
SECRET_KEY=super-secret-key-here
```

## 🔍 Monitoring

### Check Running Containers

```bash
docker ps
docker stats
```

### View Logs

```bash
# All logs
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker logs fhs-backend -f
docker logs fhs-frontend -f

# Last 100 lines
docker logs fhs-backend --tail 100
```

### Health Status

```bash
# Backend
curl http://localhost:8000/health

# Frontend
curl http://localhost:80/

# Container health
docker inspect fhs-backend | grep -A 10 Health
```

## 🚨 Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs fhs-backend

# Check if port is in use
netstat -tuln | grep 8000

# Inspect container
docker inspect fhs-backend
```

### Image Pull Failed

```bash
# Login to Docker Hub
docker login

# Manual pull
docker pull patcoder97/fhs-backend:latest

# Check image exists
docker images | grep fhs
```

### Database Connection Error

```bash
# Test from backend container
docker exec fhs-backend env | grep DB_

# Test database connection
docker exec fhs-backend python -c "from app.database.session import engine; print(engine.url)"
```

## 📊 Performance Optimization

### Enable Logging to File

```yaml
volumes:
  - ./logs:/app/logs
```

### Use Volume Mounts for Static Assets

```yaml
frontend:
  volumes:
    - ./static:/usr/share/nginx/html/static:ro
```

### Configure Nginx Caching

Frontend image already includes:
- Gzip compression
- Static file caching (1 year)
- Security headers

## 🔐 Security Checklist

- [ ] Use specific version tags (not `latest`)
- [ ] Set resource limits
- [ ] Configure health checks
- [ ] Use read-only volumes where possible
- [ ] Don't expose unnecessary ports
- [ ] Use secrets for sensitive data
- [ ] Enable Docker Content Trust
- [ ] Scan images for vulnerabilities
- [ ] Keep images updated
- [ ] Use non-root user (TODO in Dockerfiles)

## 📝 Maintenance

### Regular Updates

```bash
# Weekly: Pull latest images
docker pull patcoder97/fhs-backend:latest
docker pull patcoder97/fhs-frontend:latest

# Monthly: Clean up unused images
docker image prune -a

# Backup before update
./scripts/backup-db.sh
```

### Cleanup Old Images

```bash
# Remove unused images
docker image prune -a

# Remove specific old version
docker rmi patcoder97/fhs-backend:v0.9.0
```

## 🌐 Multi-Server Deployment

### Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.prod.yml fhs-stack

# Scale services
docker service scale fhs-stack_backend=3
```

### Kubernetes

See `k8s/` directory for Kubernetes manifests (if available).

## 📞 Support

- GitHub Issues: https://github.com/PATCoder97/fhs-prosight/issues
- Docker Hub: https://hub.docker.com/u/patcoder97

---

**Last Update**: 2026-01-14
**Version**: 1.0.0
