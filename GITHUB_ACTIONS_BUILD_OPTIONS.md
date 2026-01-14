# GitHub Actions - Build Options Quick Reference

## 🎯 Tùy chọn Build

### 1️⃣ Manual Trigger (Workflow Dispatch)

**Vào GitHub Actions:**
1. Repository → Actions tab
2. Click "Build and Push Docker Images to Docker Hub"
3. Click "Run workflow"
4. Chọn build target:
   - **both** (default) - Build cả 2 images
   - **backend** - Chỉ build backend
   - **frontend** - Chỉ build frontend
5. Click "Run workflow"

### 2️⃣ Commit Message Keywords

#### Build cả 2 images:
```bash
git commit -m "feat: update both services [build]"
# hoặc
git commit -m "feat: new feature [build:all]"
git push origin main
```

#### Build chỉ Backend:
```bash
git commit -m "fix: backend API bug [build:backend]"
git push origin main
```

#### Build chỉ Frontend:
```bash
git commit -m "feat: update UI [build:frontend]"
git push origin main
```

### 3️⃣ Git Tags (Always build both)

```bash
git tag v1.0.0
git push origin v1.0.0
# → Builds both backend:v1.0.0 + latest
#           and frontend:v1.0.0 + latest
```

## 📊 Trigger Matrix

| Trigger | Backend | Frontend | Keyword |
|---------|---------|----------|---------|
| `[build]` | ✅ | ✅ | Build both |
| `[build:all]` | ✅ | ✅ | Build both |
| `[build:backend]` | ✅ | ❌ | Backend only |
| `[build:frontend]` | ❌ | ✅ | Frontend only |
| `v*` tag | ✅ | ✅ | Release |
| Manual: both | ✅ | ✅ | User choice |
| Manual: backend | ✅ | ❌ | User choice |
| Manual: frontend | ❌ | ✅ | User choice |

## 💡 Use Cases

### Backend Code Changes Only
```bash
# Fix bug in API
git commit -m "fix: resolve authentication issue [build:backend]"
git push origin main
# ⚡ Saves time - only builds backend (~8-10 min)
```

### Frontend Code Changes Only
```bash
# Update UI components
git commit -m "feat: add new dashboard widget [build:frontend]"
git push origin main
# ⚡ Saves time - only builds frontend (~5-7 min)
```

### Both Changed
```bash
# Full stack feature
git commit -m "feat: implement user profile feature [build:all]"
git push origin main
# 🚀 Builds both in parallel (~10-12 min total)
```

### Release
```bash
# Production release
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
# 🎉 Full release with versioned tags
```

## ⏱️ Build Time Comparison

| Scenario | Time (approx) | GitHub Actions Minutes |
|----------|---------------|------------------------|
| Backend only | ~6 min | ~6 min |
| Frontend only | ~12 min | ~12 min |
| Both (parallel) | ~12 min | ~18 min total (both jobs) |

**Note**:
- First build takes longer. Subsequent builds use cache and are faster.
- Backend build is faster due to Python dependencies caching.
- Frontend build includes npm dependencies + icon building + production build.

## 🔍 Check Build Status

1. GitHub → Actions tab
2. Click on the workflow run
3. See which jobs ran:
   - Green checkmark ✅ = Success
   - Red X ❌ = Failed
   - Gray circle - = Skipped (not triggered)

## 📦 Docker Hub Images

After build completes:
- Backend: https://hub.docker.com/r/patcoder97/prosight-backend
- Frontend: https://hub.docker.com/r/patcoder97/prosight-frontend

### Available Tags:
- `dev` - Latest development build from main branch
- `latest` - Latest stable release (from version tags)
- `v1.0.0`, `v1.0.1`, etc. - Specific version tags

## 🆘 Troubleshooting

### Both jobs skipped?
- Check if commit message has correct keyword
- Verify it's pushed to `main` branch

### Job failed?
- Click on failed job to see logs
- Common issues:
  - Docker Hub credentials invalid
  - Dockerfile syntax error
  - Build context path incorrect

### Want to rebuild without new commit?
- Use manual trigger (workflow_dispatch)
- Select the target you want to rebuild

---

**Quick Commands:**

```bash
# Backend only
git commit -m "fix: update API [build:backend]" && git push

# Frontend only
git commit -m "feat: new UI [build:frontend]" && git push

# Both
git commit -m "feat: full feature [build:all]" && git push

# Release
git tag v1.0.0 && git push origin v1.0.0
```

**Last Update**: 2026-01-14
