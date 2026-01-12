# PIDMS API Deployment Checklist

Production deployment guide for PIDMS API.

## Pre-Deployment Verification

- [ ] All 10 tasks completed (54-63)
- [ ] Database migration tested (upgrade and downgrade)
- [ ] All endpoints tested with real PIDKey.com API
- [ ] Performance benchmarks met (search <2s, sync batch <30s)
- [ ] Error handling tested
- [ ] Admin authentication verified

---

## Environment Setup

### 1. Production Environment Variables

Create `backend/.env` file:

```bash
# Required
PIDKEY_API_KEY=your_production_api_key_here
PIDKEY_BASE_URL=https://pidkey.com/ajax/pidms_api
```

### 2. Verify Configuration

```bash
# Check .env file exists
ls -la backend/.env

# Verify required variables set
cd backend
python -c "from app.core.config import settings; assert settings.PIDKEY_API_KEY"
```

---

## Database Migration

### 1. Backup Database

**CRITICAL: Always backup before migration**

```bash
# Create backup
pg_dump fhs_prosight > backup_before_pidms_$(date +%Y%m%d_%H%M%S).sql

# Verify backup created
ls -lh backup_before_pidms_*.sql
```

### 2. Run Migration

```bash
cd backend

# Check current version
alembic current

# Run migration
alembic upgrade head

# Verify migration applied
alembic current
```

### 3. Verify Table Created

```sql
-- Connect to database
psql -d fhs_prosight

-- Check table exists
\d pidms_keys

-- Check indexes exist
\di pidms_keys*

-- Expected indexes:
-- pidms_keys_pkey (PRIMARY KEY)
-- idx_pidms_keys_keyname (UNIQUE)
-- idx_pidms_keys_prd
-- idx_pidms_keys_remaining
-- idx_pidms_keys_blocked

-- Verify empty table
SELECT COUNT(*) FROM pidms_keys;
```

---

## Application Deployment

### 1. Deploy Code

```bash
# Pull latest code
cd /path/to/fhs-prosight
git pull origin main

# Install dependencies
cd backend
pip install -r requirements.txt
```

### 2. Restart Application

```bash
# If using systemd
sudo systemctl restart fhs-prosight

# If running manually
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. Verify Server Running

```bash
# Check health endpoint
curl http://localhost:8000/health

# Check API docs accessible
curl -I http://localhost:8000/docs

# Check PIDMS endpoints registered
curl http://localhost:8000/openapi.json | grep pidms
```

---

## Post-Deployment Testing

### 1. Test Authentication

```bash
# Get admin token
ADMIN_TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login   -H "Content-Type: application/json"   -d '{"username": "admin", "password": "your_password"}'   | jq -r '.access_token')
```

### 2. Test POST /api/pidms/check

```bash
curl -X POST http://localhost:8000/api/pidms/check   -H "Authorization: Bearer $ADMIN_TOKEN"   -H "Content-Type: application/json"   -d '{"keys": "YOUR-REAL-KEY-HERE"}'

# Expected: 200 OK with summary showing new_keys: 1
```

### 3. Test GET /api/pidms/search

```bash
curl -X GET "http://localhost:8000/api/pidms/search?page=1&page_size=10"   -H "Authorization: Bearer $ADMIN_TOKEN"

# Expected: 200 OK with results
```

### 4. Test GET /api/pidms/products

```bash
curl -X GET "http://localhost:8000/api/pidms/products"   -H "Authorization: Bearer $ADMIN_TOKEN"

# Expected: 200 OK with products array
```

### 5. Test POST /api/pidms/sync

```bash
curl -X POST http://localhost:8000/api/pidms/sync   -H "Authorization: Bearer $ADMIN_TOKEN"   -H "Content-Type: application/json"   -d '{}'

# Expected: 200 OK with summary
```

### 6. Test Error Handling

```bash
# Test 401 - No token
curl -X GET "http://localhost:8000/api/pidms/products"
# Expected: 401 Unauthorized

# Test 422 - Invalid pagination
curl -X GET "http://localhost:8000/api/pidms/search?page=0"   -H "Authorization: Bearer $ADMIN_TOKEN"
# Expected: 422 Validation Error
```

---

## Rollback Plan

If deployment fails:

### 1. Rollback Database

```bash
# Restore from backup
psql -d fhs_prosight < backup_before_pidms_YYYYMMDD_HHMMSS.sql

# Or rollback migration only
cd backend
alembic downgrade -1
```

### 2. Rollback Code

```bash
# Revert to previous version
git checkout main
cd backend
pip install -r requirements.txt

# Restart application
sudo systemctl restart fhs-prosight
```

---

## Production Maintenance

### Daily Tasks

```bash
# Monitor logs for errors
tail -100 /var/log/fhs-prosight/fhs-prosight.log | grep -i error

# Check sync status
curl -X GET "http://localhost:8000/api/pidms/products"   -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Weekly Tasks

```bash
# Run full sync
curl -X POST http://localhost:8000/api/pidms/sync   -H "Authorization: Bearer $ADMIN_TOKEN"   -d '{}'

# Database maintenance
psql -d fhs_prosight -c "VACUUM ANALYZE pidms_keys;"

# Check database size
psql -d fhs_prosight -c "SELECT pg_size_pretty(pg_total_relation_size('pidms_keys'));"
```

---

## Security Checklist

- [ ] PIDKEY_API_KEY not committed to git
- [ ] .env file in .gitignore
- [ ] Database credentials secure
- [ ] Only admin users can access PIDMS endpoints
- [ ] HTTPS enabled (if public-facing)
- [ ] API rate limiting configured
- [ ] Logs do not contain sensitive data

---

## Success Criteria

Deployment is successful when:

- ✅ All 4 PIDMS endpoints return 200 OK with admin token
- ✅ Search query completes in < 2s
- ✅ Sync completes successfully
- ✅ No errors in application logs
- ✅ Database indexes verified
- ✅ Admin authentication working (401/403 for non-admin)
- ✅ Documentation accessible at /docs
