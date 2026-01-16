# ✅ Alembic Migration Reset - Summary

## 🎯 What Was Done

### 1. **Fixed Hardcoded Database Connection Issue**

**Problem Found:**
- `backend/alembic.ini` had hardcoded connection: `postgresql://casaos:casaos@ktxn258.duckdns.org:6543/casaos`
- This would be baked into Docker image, ignoring environment variables

**Solution:**
- Updated `backend/alembic/env.py` to override with `DATABASE_URL` from environment:
```python
# Import settings to get DATABASE_URL from environment
from app.core.config import settings

# Override sqlalchemy.url with DATABASE_URL from environment variables
if settings.DATABASE_URL:
    config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
```

- Updated `backend/alembic.ini` to use UTF-8 encoding and safe default:
```ini
output_encoding = utf-8
sqlalchemy.url = postgresql://tp75user:tp75pass@localhost:5432/tp75db
```

### 2. **Reset Alembic Migrations to Single Initial Schema**

**Before:** 7 separate migration files
- `9a0ea82c4ee9_initial_schema.py`
- `7b4280a50047_add_localid_and_fix_role_default.py`
- `beb7f4fa17b3_add_employees_table.py`
- `12f90a9790c8_add_evaluations_table.py`
- `43e6802dc765_add_pidms_keys_table.py`
- `341081d9ee36_create_pidms_keys_table.py`
- `d00945f93f23_add_dormitory_bills_table.py`

**After:** 1 comprehensive migration file
- `0846970e5b1f_initial_schema_all_tables.py`

**Benefits:**
- ✅ Clean migration history for new deployments
- ✅ Single migration easier to maintain
- ✅ Avoids migration conflicts on fresh databases
- ✅ Better for Docker containers (fast DB initialization)

### 3. **Updated Alembic to Import All Models**

Updated `backend/alembic/env.py` to import all models for autogenerate:
```python
# Import the Base and ALL models (important for autogenerate)
from app.models.user import Base
from app.models import user, employee, evaluation, dormitory_bill, pidms_key
```

This ensures alembic can detect all tables when generating migrations.

---

## 📋 Migration Details

The new single migration `0846970e5b1f_initial_schema_all_tables.py` creates:

### **Table: `users`**
- OAuth authentication (Google, GitHub)
- `localId` for FHS employee linking
- Role-based access control (admin, user, viewer)
- Indexes: email, id, localId, social_id

### **Table: `employees`**
- Synced from FHS HRS API
- Personal info, job details, salary
- Department and identity tracking
- Indexes: id, department_code, identity_number

### **Table: `evaluations`**
- Employee performance evaluations
- Linked to employees by `employee_id`
- Term-based tracking
- Indexes: employee_id, term_code, dept_code

### **Table: `dormitory_bills`**
- Employee housing charges
- Linked to employees by `employee_id`
- Term and dorm tracking
- Indexes: employee_id, term_code, dorm_code, total_amount
- Special index: `idx_dormitory_bills_sort` (term_code DESC, created_at DESC)

### **Table: `pidms_keys`**
- License key management for PIDKey.com integration
- Tracks remaining/blocked/used keys
- Indexes: keyname, prd, remaining, blocked

---

## 🚀 Deployment Impact

### **For Fresh Deployments (Recommended)**

When deploying fullstack container to a new database:

```bash
# 1. Pull latest fullstack image (will be built by GitHub Actions)
docker pull patcoder97/prosight-fullstack:latest

# 2. Deploy with docker-compose
docker-compose -f docker-compose.fullstack.yml up -d

# 3. Run migration (inside container)
docker exec tp75-fullstack alembic upgrade head

# Expected output:
# INFO  [alembic.runtime.migration] Running upgrade  -> 0846970e5b1f, initial_schema_all_tables
```

### **For Existing Deployments**

If you already have data in the old database:

#### **Option 1: Keep Old Data (Manual Migration)**

```bash
# 1. Backup existing data
docker exec tp75-db pg_dump -U tp75user tp75db > backup_$(date +%Y%m%d).sql

# 2. The old database still works with the new code
# No action needed - old migrations are removed from code but DB state is preserved
```

#### **Option 2: Fresh Start (Clean Database)**

```bash
# 1. Backup data if needed
docker exec tp75-db pg_dump -U tp75user tp75db > backup_$(date +%Y%m%d).sql

# 2. Drop and recreate database
docker exec tp75-db psql -U tp75user -d postgres -c "DROP DATABASE tp75db;"
docker exec tp75-db psql -U tp75user -d postgres -c "CREATE DATABASE tp75db;"

# 3. Run new migration
docker exec tp75-fullstack alembic upgrade head
```

---

## 🔍 Verification

After deployment, verify migration applied correctly:

```bash
# Check alembic version
docker exec tp75-fullstack alembic current

# Expected output:
# 0846970e5b1f (head)

# Check tables created
docker exec tp75-db psql -U tp75user -d tp75db -c "\dt"

# Expected tables:
# alembic_version
# users
# employees
# evaluations
# dormitory_bills
# pidms_keys
```

---

## 📝 Files Changed

### **Modified:**
1. `backend/alembic.ini` - Fixed encoding, removed hardcoded connection
2. `backend/alembic/env.py` - Import all models, use DATABASE_URL from environment

### **Deleted (7 files):**
1. `backend/alembic/versions/9a0ea82c4ee9_initial_schema.py`
2. `backend/alembic/versions/7b4280a50047_add_localid_and_fix_role_default.py`
3. `backend/alembic/versions/beb7f4fa17b3_add_employees_table.py`
4. `backend/alembic/versions/12f90a9790c8_add_evaluations_table.py`
5. `backend/alembic/versions/43e6802dc765_add_pidms_keys_table.py`
6. `backend/alembic/versions/341081d9ee36_create_pidms_keys_table.py`
7. `backend/alembic/versions/d00945f93f23_add_dormitory_bills_table.py`

### **Created (1 file):**
1. `backend/alembic/versions/0846970e5b1f_initial_schema_all_tables.py`

---

## 🎉 Commits

```bash
ffac0aa - fix: use DATABASE_URL from environment in alembic migrations
2eeeb72 - feat: reset alembic migrations to single initial schema
```

---

## ⚡ Next Steps

1. **Wait for GitHub Actions to build fullstack image** (~18-20 minutes)
   - Check: https://github.com/PATCoder97/fhs-prosight/actions

2. **Deploy fullstack container:**
   ```bash
   docker pull patcoder97/prosight-fullstack:latest
   docker-compose -f docker-compose.fullstack.yml up -d
   ```

3. **Run migration:**
   ```bash
   docker exec tp75-fullstack alembic upgrade head
   ```

4. **Verify deployment:**
   ```bash
   # Check frontend
   curl http://localhost:8001

   # Check API
   curl http://localhost:8001/api/health

   # Check migration
   docker exec tp75-fullstack alembic current
   ```

---

**Last Updated:** 2026-01-16
**Migration ID:** `0846970e5b1f`
**Status:** ✅ Ready for deployment
