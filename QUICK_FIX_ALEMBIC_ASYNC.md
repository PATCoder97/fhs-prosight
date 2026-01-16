# 🔧 Quick Fix - Alembic Async/Sync Database URL Issue

## ❌ Problem

Khi deploy fullstack container, alembic migration bị lỗi:

```
sqlalchemy.exc.MissingGreenlet: greenlet_spawn has not been called;
can't call await_only() here. Was IO attempted in an unexpected place?
```

## 🔍 Root Cause

**Conflict giữa async và sync database drivers:**

1. **Backend Application** (FastAPI) cần **async driver**:
   - `DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db`
   - File: [backend/app/database/session.py:6](backend/app/database/session.py#L6)
   - Dùng `create_async_engine` với `postgresql+asyncpg://`

2. **Alembic Migrations** cần **sync driver**:
   - `sqlalchemy.url=postgresql://user:pass@host:port/db`
   - File: [backend/alembic/env.py](backend/alembic/env.py)
   - Alembic không hỗ trợ async connections

**Vấn đề:**
- `docker-compose.fullstack.yml` set `DATABASE_URL=postgresql+asyncpg://...`
- `alembic/env.py` sử dụng `DATABASE_URL` từ settings
- Alembic cố gắng dùng async driver → **FAILED**

## ✅ Solution

**Update [backend/alembic/env.py:24-30](backend/alembic/env.py#L24-L30):**

```python
# Override sqlalchemy.url with DATABASE_URL from environment variables
# This ensures alembic uses the same DB connection as the application
# Note: Alembic needs sync driver (postgresql://), not async (postgresql+asyncpg://)
if settings.DATABASE_URL:
    # Convert async URL to sync URL for alembic
    sync_database_url = settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')
    config.set_main_option("sqlalchemy.url", sync_database_url)
```

**Giải thích:**
- Đọc `DATABASE_URL` từ environment (với async driver `postgresql+asyncpg://`)
- Convert về sync driver `postgresql://` cho alembic
- Cả backend app và alembic đều dùng cùng DB credentials

## 🚀 Deploy Fix

### **Step 1: Wait for GitHub Actions Build**

```bash
# Check build status
https://github.com/PATCoder97/fhs-prosight/actions

# Wait for "Build and Push Fullstack Docker Image" workflow #10 to complete
# Expected: ~1-2 minutes
```

### **Step 2: Pull New Image**

```bash
# SSH vào CasaOS server
ssh user@your-server-ip

# Pull latest image (includes alembic fix)
docker pull patcoder97/prosight-fullstack:latest

# Expected output:
# latest: Pulling from patcoder97/prosight-fullstack
# Digest: sha256:...
# Status: Downloaded newer image for patcoder97/prosight-fullstack:latest
```

### **Step 3: Stop Current Containers**

```bash
cd ~/fhs-prosight

# Stop containers
docker-compose -f docker-compose.fullstack.yml down

# Expected output:
# [+] Running 3/3
#  ✔ Container tp75-fullstack  Removed
#  ✔ Container tp75-db         Removed
#  ✔ Network tp75-fhs_network  Removed
```

### **Step 4: Start Containers with New Image**

```bash
# Start containers (will use new image)
docker-compose -f docker-compose.fullstack.yml up -d

# Expected output:
# [+] Running 3/3
#  ✔ Network tp75-fhs_network  Created
#  ✔ Container tp75-db         Started
#  ✔ Container tp75-fullstack  Started
```

### **Step 5: Monitor Logs**

```bash
# Follow logs to see migration progress
docker logs -f tp75-fullstack

# Expected output (SUCCESSFUL):
# 🚀 Starting FHS HR Backend...
# ✓ DATABASE_URL: postgresql+asyncpg://tp75user:...@tp75-db:5432/tp75db
# ⏳ Waiting for database to be ready...
# ✓ Database is ready!
# ✓ Database connected successfully!
#
# 📦 Running database migrations...
# INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
# INFO  [alembic.runtime.migration] Will assume transactional DDL.
# INFO  [alembic.runtime.migration] Running upgrade  -> 0846970e5b1f, initial_schema_all_tables
# ✓ Database migrations completed successfully!
#
# 🌱 Seeding database...
# ✓ Database seeding completed successfully!
#
# ✓ All checks passed!
# 🌐 Starting Uvicorn server on 0.0.0.0:8001...
# INFO:     Started server process [1]
# INFO:     Waiting for application startup.
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
```

### **Step 6: Verify Deployment**

```bash
# 1. Check containers running
docker ps | grep tp75

# Expected:
# tp75-fullstack   Up X minutes   0.0.0.0:8001->8001/tcp
# tp75-db          Up X minutes   5432/tcp

# 2. Test frontend
curl http://localhost:8001

# Expected: HTML response with <!DOCTYPE html>

# 3. Test API health
curl http://localhost:8001/api/health

# Expected: {"status":"healthy"}

# 4. Verify migration applied
docker exec tp75-fullstack alembic current

# Expected: 0846970e5b1f (head)

# 5. Check database tables
docker exec tp75-db psql -U tp75user -d tp75db -c "\dt"

# Expected tables:
# alembic_version
# users
# employees
# evaluations
# dormitory_bills
# pidms_keys
```

## 📊 Technical Details

### **Database URL Formats**

| Component | Driver | URL Format | Usage |
|-----------|--------|------------|-------|
| **Backend App** | `asyncpg` | `postgresql+asyncpg://user:pass@host:port/db` | FastAPI async operations |
| **Alembic** | `psycopg2` | `postgresql://user:pass@host:port/db` | Sync migrations |
| **backend/database/session.py** | Auto-convert | Converts `postgresql://` → `postgresql+asyncpg://` | Backward compatibility |

### **Why This Works**

1. **Single Source of Truth:**
   - `DATABASE_URL` environment variable defines DB credentials
   - Both backend app and alembic read from same source

2. **Driver Conversion:**
   - Backend: Uses `DATABASE_URL` as-is (`postgresql+asyncpg://`)
   - Alembic: Converts to sync driver (`postgresql://`)

3. **No Hardcoding:**
   - No hardcoded DB URLs in code or config files
   - Easy to change DB credentials via environment variables

### **Files Modified**

- ✅ [backend/alembic/env.py](backend/alembic/env.py) - Convert async URL to sync for alembic
- ✅ [docker-compose.fullstack.yml](docker-compose.fullstack.yml) - Use `postgresql+asyncpg://` in DATABASE_URL
- ✅ [backend/app/database/session.py](backend/app/database/session.py) - Already has `.replace()` for backward compatibility

## 🔄 Alternative Solution (Not Recommended)

Nếu bạn muốn dùng separate environment variables:

```yaml
# docker-compose.fullstack.yml
environment:
  - POSTGRES_HOST=tp75-db
  - POSTGRES_PORT=5432
  - POSTGRES_USER=tp75user
  - POSTGRES_PASSWORD=tp75pass
  - POSTGRES_DATABASE=tp75db
  # Let backend construct DATABASE_URL automatically
```

```python
# backend/app/core/config.py
class Settings(BaseSettings):
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DATABASE: str

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DATABASE}"
```

**Nhưng giải pháp hiện tại (convert async → sync trong alembic) đơn giản hơn và không cần thay đổi nhiều.**

## 📝 Commits

```bash
53c8cbd - fix: convert async DATABASE_URL to sync for alembic migrations
ebc51aa - fix: use postgresql+asyncpg:// driver in DATABASE_URL for async SQLAlchemy
```

## 📞 Support

Nếu vẫn gặp lỗi:

1. **Check logs:** `docker logs tp75-fullstack --tail 100`
2. **Verify DATABASE_URL:** `docker exec tp75-fullstack env | grep DATABASE_URL`
3. **Check alembic config:** `docker exec tp75-fullstack cat /app/alembic.ini | grep sqlalchemy.url`
4. **Manual migration:** `docker exec tp75-fullstack alembic upgrade head`

---

**Last Updated:** 2026-01-16
**Fix Version:** `patcoder97/prosight-fullstack:latest` (after workflow #10)
**Status:** ✅ Ready to deploy
