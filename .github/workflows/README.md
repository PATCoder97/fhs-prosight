# GitHub Actions - Docker Build Workflow

## Tổng quan

Workflow này tự động build và push 2 Docker images (Backend và Frontend) lên Docker Hub.

## Images được build

1. **Backend Image**: `patcoder97/fhs-backend`
   - Base: Python 3.11-slim
   - Framework: FastAPI
   - Platform: linux/amd64, linux/arm64

2. **Frontend Image**: `patcoder97/fhs-frontend`
   - Base: Node 18 + Nginx Alpine
   - Framework: Vue.js 3
   - Platform: linux/amd64, linux/arm64

## Trigger Conditions

Workflow sẽ chạy khi:

### 1. Manual Trigger (Workflow Dispatch)
Bấm nút "Run workflow" trên GitHub Actions tab.

### 2. Push to Main với [build]
Commit message chứa từ khóa `[build]`:
```bash
git commit -m "feat: add new feature [build]"
git push origin main
```

### 3. Tag Release
Tạo tag với prefix `v`:
```bash
git tag v1.0.0
git push origin v1.0.0
```

## Image Tags

### Development Build (Push to main với [build])
- Backend: `patcoder97/fhs-backend:dev`
- Frontend: `patcoder97/fhs-frontend:dev`

### Release Build (Git tag)
- Backend: `patcoder97/fhs-backend:v1.0.0`, `patcoder97/fhs-backend:latest`
- Frontend: `patcoder97/fhs-frontend:v1.0.0`, `patcoder97/fhs-frontend:latest`

## Setup Requirements

### GitHub Secrets

Cần setup 2 secrets trong GitHub repository:

1. **DOCKERHUB_USERNAME**
   - Path: Settings → Secrets and variables → Actions → New repository secret
   - Value: Docker Hub username của bạn (vd: `patcoder97`)

2. **DOCKERHUB_TOKEN**
   - Path: Settings → Secrets and variables → Actions → New repository secret
   - Value: Docker Hub access token

#### Cách tạo Docker Hub Access Token:

1. Đăng nhập Docker Hub: https://hub.docker.com
2. Account Settings → Security → New Access Token
3. Name: `github-actions`
4. Permissions: `Read, Write, Delete`
5. Copy token và paste vào GitHub secret

## Usage Examples

### 1. Development Build

```bash
# Commit với [build] keyword
git add .
git commit -m "feat: update frontend UI [build]"
git push origin main

# Workflow sẽ tự động build và push images với tag 'dev'
```

Sau khi build xong, pull images:
```bash
docker pull patcoder97/fhs-backend:dev
docker pull patcoder97/fhs-frontend:dev
```

### 2. Production Release

```bash
# Tạo git tag
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# Workflow sẽ tự động build và push images với tag 'v1.0.0' và 'latest'
```

Sau khi build xong, pull images:
```bash
docker pull patcoder97/fhs-backend:latest
docker pull patcoder97/fhs-frontend:latest

# Hoặc specific version
docker pull patcoder97/fhs-backend:v1.0.0
docker pull patcoder97/fhs-frontend:v1.0.0
```

### 3. Manual Trigger

1. Vào GitHub repository
2. Actions tab
3. Chọn workflow "Build and Push Docker Images to Docker Hub"
4. Click "Run workflow"
5. Chọn branch (thường là `main`)
6. Click "Run workflow" button

## Workflow Features

### Parallel Jobs
Backend và Frontend builds chạy parallel để tiết kiệm thời gian.

### Multi-platform Support
Build cho cả `linux/amd64` (x86_64) và `linux/arm64` (ARM).

### Build Cache
Sử dụng Docker registry cache để tăng tốc độ build:
- Cache được lưu tại: `patcoder97/fhs-backend:buildcache` và `patcoder97/fhs-frontend:buildcache`
- Giảm thời gian build từ 10-15 phút xuống 2-3 phút (builds tiếp theo)

### Docker Metadata
Tự động generate tags và labels dựa trên:
- Git tags
- Branch names
- Commit messages

## Deployment với Images từ Docker Hub

### Development

```bash
# Pull dev images
docker pull patcoder97/fhs-backend:dev
docker pull patcoder97/fhs-frontend:dev

# Chạy với docker-compose (chỉnh sửa docker-compose.yml)
services:
  backend:
    image: patcoder97/fhs-backend:dev
    # ... other configs

  frontend:
    image: patcoder97/fhs-frontend:dev
    # ... other configs
```

### Production

```bash
# Pull production images
docker pull patcoder97/fhs-backend:latest
docker pull patcoder97/fhs-frontend:latest

# Chạy với docker-compose
services:
  backend:
    image: patcoder97/fhs-backend:latest
    # ... other configs

  frontend:
    image: patcoder97/fhs-frontend:latest
    # ... other configs
```

## Monitoring Workflow

### Check Workflow Status

1. GitHub repository → Actions tab
2. Xem danh sách workflow runs
3. Click vào run để xem chi tiết logs

### Workflow Failed?

Common issues:

1. **Docker Hub credentials invalid**
   - Kiểm tra secrets: `DOCKERHUB_USERNAME` và `DOCKERHUB_TOKEN`
   - Regenerate Docker Hub token nếu cần

2. **Build errors**
   - Xem logs của step "Build and push Backend/Frontend image"
   - Kiểm tra Dockerfile syntax
   - Test build locally: `docker build -f backend/Dockerfile ./backend`

3. **Platform not supported**
   - Đảm bảo base images support multi-platform
   - Check QEMU setup trong workflow

## Best Practices

1. **Use semantic versioning for tags**
   ```bash
   git tag v1.0.0    # Major release
   git tag v1.0.1    # Patch release
   git tag v1.1.0    # Minor release
   ```

2. **Test locally before pushing**
   ```bash
   # Build locally
   docker build -f backend/Dockerfile ./backend -t test-backend
   docker build -f frontend/Dockerfile ./frontend -t test-frontend

   # Test run
   docker run -p 8000:8000 test-backend
   docker run -p 80:80 test-frontend
   ```

3. **Use [build] keyword sparingly**
   - Chỉ dùng khi thực sự cần build images
   - Tránh trigger workflow không cần thiết

4. **Monitor Docker Hub storage**
   - Free tier: 1 private repo, unlimited public repos
   - Check image sizes và cleanup old images nếu cần

## Troubleshooting

### Docker Hub Rate Limit

Free tier: 100 pulls/6 hours, 200 pulls/6 hours (authenticated)

Solution:
- Authenticate: `docker login`
- Use paid plan
- Use GitHub Container Registry (ghcr.io)

### Build Timeout

GitHub Actions timeout: 6 hours/job

Solution:
- Optimize Dockerfile (multi-stage builds)
- Use build cache
- Reduce dependencies

### Large Image Sizes

Solution:
- Use slim/alpine base images ✓ (already implemented)
- Remove unnecessary files in .dockerignore ✓ (already implemented)
- Multi-stage builds ✓ (already implemented)
- Combine RUN commands to reduce layers

---

**Last Update**: 2026-01-14
**Workflow Version**: 2.0.0
