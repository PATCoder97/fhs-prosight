# 🏷️ Tag-Based Build System - Usage Guide

## 📋 Tổng Quan

GitHub Actions workflow giờ chỉ build Docker image khi commit message có **tag pattern** `[tag]`.

### **Lợi Ích:**
- ✅ Kiểm soát được khi nào build (không build mọi commit)
- ✅ Tiết kiệm CI/CD resources và thời gian
- ✅ Version control rõ ràng cho Docker images
- ✅ Tự động tag `latest` cho version releases

---

## 🎯 Cách Sử Dụng

### **Cú Pháp Commit Message:**

```bash
git commit -m "[tag] commit message here"
```

**Pattern:** Bất kỳ text nào trong dấu ngoặc vuông `[]` sẽ được sử dụng làm Docker image tag.

---

## 📦 Tag Types

### **1. Version Tags (Bắt Đầu Với 'v')**

Dùng cho production releases. Tự động tag thêm `latest`.

**Examples:**

```bash
# Version 1.0
git commit -m "[v1.0] feat: initial production release"
# → Builds and tags: v1.0 + latest

# Version 2.0
git commit -m "[v2.0] feat: major update with new features"
# → Builds and tags: v2.0 + latest

# Version 1.5.3
git commit -m "[v1.5.3] fix: critical bug fix"
# → Builds and tags: v1.5.3 + latest
```

**Docker Images Created:**
```
patcoder97/prosight-fullstack:v1.0
patcoder97/prosight-fullstack:latest  (points to v1.0)
```

### **2. Environment Tags**

Dùng cho các environments khác nhau. Chỉ tag với tên environment.

**Examples:**

```bash
# Development
git commit -m "[dev] feat: add new feature for testing"
# → Builds and tags: dev

# Staging
git commit -m "[staging] fix: bug fix for staging environment"
# → Builds and tags: staging

# UAT
git commit -m "[uat] refactor: code cleanup for user testing"
# → Builds and tags: uat
```

**Docker Images Created:**
```
patcoder97/prosight-fullstack:dev
patcoder97/prosight-fullstack:staging
patcoder97/prosight-fullstack:uat
```

### **3. Feature/Branch Tags**

Dùng cho feature branches hoặc experimental builds.

**Examples:**

```bash
# Feature branch
git commit -m "[feature-auth] feat: implement OAuth2 authentication"
# → Builds and tags: feature-auth

# Hotfix
git commit -m "[hotfix-db] fix: database connection issue"
# → Builds and tags: hotfix-db

# Experimental
git commit -m "[experimental] feat: testing new architecture"
# → Builds and tags: experimental
```

### **4. No Tag = No Build**

Commits without tags sẽ **KHÔNG** trigger build.

**Examples:**

```bash
# Documentation updates (no build needed)
git commit -m "docs: update README"
# → NO BUILD

# Minor fixes (no build needed)
git commit -m "fix: typo in comments"
# → NO BUILD

# Work in progress (no build needed)
git commit -m "WIP: still working on feature"
# → NO BUILD
```

---

## 🚀 Deployment Workflows

### **Production Release Workflow:**

```bash
# 1. Develop features on dev
git commit -m "[dev] feat: implement new dashboard"
git push
# → Builds: dev tag only

# 2. Test on staging
git commit -m "[staging] feat: dashboard ready for staging"
git push
# → Builds: staging tag only

# 3. Release to production
git commit -m "[v1.0] feat: dashboard production release"
git push
# → Builds: v1.0 + latest tags
```

**Deployment:**

```bash
# Development
docker pull patcoder97/prosight-fullstack:dev

# Staging
docker pull patcoder97/prosight-fullstack:staging

# Production (always use versioned tag for rollback capability)
docker pull patcoder97/prosight-fullstack:v1.0

# Or use latest (points to newest version)
docker pull patcoder97/prosight-fullstack:latest
```

### **Hotfix Workflow:**

```bash
# 1. Create hotfix
git commit -m "[hotfix-1.0.1] fix: critical security patch"
git push
# → Builds: hotfix-1.0.1 tag only

# 2. Test hotfix
docker pull patcoder97/prosight-fullstack:hotfix-1.0.1
# Test thoroughly

# 3. Release hotfix as new version
git commit -m "[v1.0.1] fix: security patch release"
git push
# → Builds: v1.0.1 + latest tags
```

---

## 📊 Tag Naming Conventions

### **Recommended Tag Patterns:**

| Tag Type | Pattern | Example | Use Case |
|----------|---------|---------|----------|
| **Version** | `v{major}.{minor}.{patch}` | `v1.0.0`, `v2.1.3` | Production releases |
| **Environment** | `{env}` | `dev`, `staging`, `uat` | Environment-specific builds |
| **Feature** | `feature-{name}` | `feature-auth`, `feature-api` | Feature branches |
| **Hotfix** | `hotfix-{version}` | `hotfix-1.0.1` | Emergency fixes |
| **Experimental** | `exp-{name}` | `exp-docker`, `exp-perf` | Experimental builds |

### **Version Numbering (Semantic Versioning):**

```
v{MAJOR}.{MINOR}.{PATCH}

MAJOR: Breaking changes (v1.0.0 → v2.0.0)
MINOR: New features, backward compatible (v1.0.0 → v1.1.0)
PATCH: Bug fixes (v1.0.0 → v1.0.1)
```

**Examples:**
- `v1.0.0` - Initial production release
- `v1.1.0` - Added route guard feature
- `v1.1.1` - Fixed route guard bug
- `v2.0.0` - Complete rewrite with breaking changes

---

## 🔍 Checking Build Status

### **GitHub Actions:**

```
https://github.com/PATCoder97/fhs-prosight/actions
```

**What to Look For:**

1. **Workflow Name:** "Build and Push Fullstack Docker Image"
2. **Job 1:** "Check if build should trigger"
   - Shows detected tag
   - Shows if it's a version tag
3. **Job 2:** "Build Fullstack Image" (only if tag found)
   - Shows Docker tags being created

### **Example Workflow Output:**

```
✓ Check if build should trigger
  Commit message: [v1.0] feat: initial production release
  Build tag found: v1.0
  This is a version tag - will also tag as 'latest'

✓ Build Fullstack Image (Backend + Frontend)
  Tagging as: v1.0 and latest
  Image pushed with tags: patcoder97/prosight-fullstack:v1.0,patcoder97/prosight-fullstack:latest
```

---

## 📦 Docker Hub Tags

### **View All Tags:**

```
https://hub.docker.com/r/patcoder97/prosight-fullstack/tags
```

**Expected Tags:**

```
patcoder97/prosight-fullstack:latest      (newest version release)
patcoder97/prosight-fullstack:v1.0        (version 1.0)
patcoder97/prosight-fullstack:v1.1        (version 1.1)
patcoder97/prosight-fullstack:dev         (development build)
patcoder97/prosight-fullstack:staging     (staging build)
```

### **Pull Specific Tag:**

```bash
# Pull latest production version
docker pull patcoder97/prosight-fullstack:latest

# Pull specific version (recommended for production)
docker pull patcoder97/prosight-fullstack:v1.0

# Pull development version
docker pull patcoder97/prosight-fullstack:dev

# Pull staging version
docker pull patcoder97/prosight-fullstack:staging
```

---

## 🔄 Updating docker-compose.yml

### **Option 1: Use Specific Version (Recommended)**

```yaml
services:
  tp75-fullstack:
    image: patcoder97/prosight-fullstack:v1.0  # Specific version
```

**Pros:**
- ✅ Predictable deployments
- ✅ Easy rollback to previous versions
- ✅ No surprises from auto-updates

### **Option 2: Use Latest**

```yaml
services:
  tp75-fullstack:
    image: patcoder97/prosight-fullstack:latest  # Always newest version
```

**Pros:**
- ✅ Always get latest features/fixes
- ❌ May have breaking changes
- ❌ Harder to rollback

### **Option 3: Environment-Specific**

```yaml
# Development
services:
  tp75-fullstack:
    image: patcoder97/prosight-fullstack:dev

# Staging
services:
  tp75-fullstack:
    image: patcoder97/prosight-fullstack:staging

# Production
services:
  tp75-fullstack:
    image: patcoder97/prosight-fullstack:v1.0
```

---

## 🎯 Best Practices

### **1. Always Tag Version Releases:**

```bash
# ✅ Good
git commit -m "[v1.0] feat: production-ready release"

# ❌ Bad (no tag = no build)
git commit -m "feat: production-ready release"
```

### **2. Use Semantic Versioning:**

```bash
# ✅ Good
git commit -m "[v1.0.0] feat: initial release"
git commit -m "[v1.1.0] feat: add new feature"
git commit -m "[v1.1.1] fix: bug fix"
git commit -m "[v2.0.0] feat: breaking changes"

# ❌ Bad (inconsistent)
git commit -m "[version1] feat: initial release"
git commit -m "[1.1] feat: add new feature"
```

### **3. Document What Changes:**

```bash
# ✅ Good (descriptive)
git commit -m "[v1.0] feat: add route guard protection and OAuth integration"

# ❌ Bad (vague)
git commit -m "[v1.0] updates"
```

### **4. Test Before Releasing:**

```bash
# 1. Build dev/staging first
git commit -m "[dev] feat: new feature"
# Test thoroughly

# 2. Then release as version
git commit -m "[v1.1] feat: new feature production release"
```

---

## 🐛 Troubleshooting

### **Issue: Build didn't trigger**

**Cause:** No tag in commit message

**Fix:**
```bash
# Check your commit message
git log -1 --pretty=%B

# Should see: [tag] commit message
# If not, amend commit:
git commit --amend -m "[v1.0] your commit message"
git push --force-with-lease
```

### **Issue: Wrong tag was used**

**Fix:**
```bash
# Amend last commit with correct tag
git commit --amend -m "[correct-tag] your commit message"
git push --force-with-lease
```

### **Issue: Build failed**

**Check:**
1. GitHub Actions logs
2. Docker build errors
3. Make sure Dockerfile.fullstack exists

---

## 📝 Quick Reference

| Action | Command | Result |
|--------|---------|--------|
| **Production release** | `git commit -m "[v1.0] feat: ..."` | Tags: `v1.0`, `latest` |
| **Dev build** | `git commit -m "[dev] feat: ..."` | Tag: `dev` |
| **Staging build** | `git commit -m "[staging] feat: ..."` | Tag: `staging` |
| **Hotfix** | `git commit -m "[hotfix-1.0.1] fix: ..."` | Tag: `hotfix-1.0.1` |
| **No build** | `git commit -m "docs: update README"` | No build |

---

## 🎉 Example: Complete Release Flow

```bash
# 1. Feature development
git checkout -b feature-dashboard
git commit -m "[dev] feat: implement dashboard UI"
git push
# → Builds: dev tag

# 2. Staging test
git checkout main
git merge feature-dashboard
git commit -m "[staging] feat: dashboard ready for testing"
git push
# → Builds: staging tag

# 3. Production release
git commit -m "[v1.1.0] feat: dashboard feature release"
git push
# → Builds: v1.1.0 + latest tags

# 4. Deploy to production
ssh user@server
docker pull patcoder97/prosight-fullstack:v1.1.0
docker-compose up -d
```

---

**Last Updated:** 2026-01-16
**Current Version:** `v1.0`
**Workflow:** Tag-based builds enabled
