# Employee Feature Deployment Guide

## Overview

Deployment guide for the employee synchronization and management feature. This document covers staging and production deployment procedures, rollback plans, and health checks.

**Feature:** Employee sync from FHS HRS and COVID APIs
**Components:** Database migration, API endpoints, integration clients
**Dependencies:** PostgreSQL, Alembic, FastAPI

---

## Pre-Deployment Checklist

Before deploying to any environment, verify:

### Code Quality
- [ ] All unit tests passing: `pytest tests/test_*.py -v`
- [ ] All integration tests passing: `pytest tests/integration/ -v`
- [ ] Code reviewed and approved (Pull Request merged)
- [ ] No critical security vulnerabilities
- [ ] Linting passed: `pylint app/` or `flake8 app/`

### Infrastructure
- [ ] Database backup created and verified
- [ ] Environment variables configured
- [ ] Access to FHS APIs verified (HRS and COVID)
- [ ] Database connection tested
- [ ] Sufficient disk space (check: `df -h`)
- [ ] Application logs accessible

### Documentation
- [ ] API usage guide reviewed
- [ ] Deployment steps documented
- [ ] Rollback plan prepared
- [ ] Team notified of deployment window

---

## Environment Variables

Add these variables to your `.env` file or environment configuration:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@host:port/dbname

# FHS HRS API
FHS_HRS_BASE_URL=https://www.fhs.com.tw/ads/api/Furnace/rest/json/hr

# FHS COVID API
FHS_COVID_API_BASE_URL=https://www.fhs.com.tw/fhs_covid_api/api/reportVaccines/detail

# JWT Secret (already configured)
SECRET_KEY=your-secret-key-here

# CORS (update if needed)
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]
```

### Environment-Specific Values

**Staging:**
```bash
DATABASE_URL=postgresql+asyncpg://user:password@staging-db.example.com:5432/fhs_prosight_staging
```

**Production:**
```bash
DATABASE_URL=postgresql+asyncpg://user:password@prod-db.example.com:5432/fhs_prosight_prod
```

---

## Staging Deployment

### Step 1: Backup Database

Create a timestamped backup before any changes:

```bash
# PostgreSQL backup
pg_dump -h staging-db.example.com -U db_user -d fhs_prosight_staging \
  -F c -b -v -f "backup_staging_$(date +%Y%m%d_%H%M%S).dump"

# Verify backup
pg_restore --list backup_staging_TIMESTAMP.dump | head -20

# Alternative: SQL format
pg_dump -h staging-db.example.com -U db_user -d fhs_prosight_staging \
  > "backup_staging_$(date +%Y%m%d_%H%M%S).sql"
```

**Store backup securely** (e.g., AWS S3, network storage).

### Step 2: Deploy Code

Pull latest code and install dependencies:

```bash
# Navigate to application directory
cd /var/www/fhs-prosight-backend

# Pull latest code from main branch
git fetch origin
git checkout main
git pull origin main

# Verify correct commit
git log -1 --oneline

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
pip install -r requirements.txt --upgrade

# Verify critical packages
pip show fastapi sqlalchemy alembic httpx
```

### Step 3: Run Database Migration

Apply the employee table migration:

```bash
# Check current migration state
alembic current

# Review pending migrations
alembic history

# Run migration (upgrade to head)
alembic upgrade head

# Verify migration applied
alembic current
# Should show: beb7f4fa17b3 (head)

# Verify employees table created
psql -h staging-db.example.com -U db_user -d fhs_prosight_staging \
  -c "\d employees"

# Check table structure
psql -h staging-db.example.com -U db_user -d fhs_prosight_staging \
  -c "SELECT column_name, data_type, is_nullable
      FROM information_schema.columns
      WHERE table_name = 'employees'
      ORDER BY ordinal_position;"
```

### Step 4: Restart Application

Restart the FastAPI application service:

```bash
# Using systemd
sudo systemctl restart fhs-prosight-backend

# Check service status
sudo systemctl status fhs-prosight-backend

# View recent logs
sudo journalctl -u fhs-prosight-backend -n 50 --no-pager

# Alternative: Using supervisor
sudo supervisorctl restart fhs-prosight-backend
sudo supervisorctl status fhs-prosight-backend

# Alternative: Manual restart
pkill -f "uvicorn app.main:app"
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > logs/app.log 2>&1 &
```

### Step 5: Health Checks

Verify deployment success:

```bash
# 1. Check application health
curl http://staging-api.example.com/health
# Expected: {"status": "healthy"}

# 2. Check OpenAPI docs accessible
curl -I http://staging-api.example.com/docs
# Expected: HTTP/1.1 200 OK

# 3. Test employee sync endpoint (requires admin token)
curl -X POST "http://staging-api.example.com/api/employees/sync" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"emp_id": 6204, "source": "hrs"}'
# Expected: 200 OK with employee data

# 4. Verify employee in database
psql -h staging-db.example.com -U db_user -d fhs_prosight_staging \
  -c "SELECT id, name_tw, name_en FROM employees WHERE id='VNW0006204';"

# 5. Test search endpoint
curl -X GET "http://staging-api.example.com/api/employees/search?limit=1" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
# Expected: 200 OK with employee list
```

### Step 6: Smoke Tests

Run quick manual tests:

1. **Sync single employee** (HRS source)
2. **Search for employee** (by name)
3. **Get employee details** (by ID)
4. **Update employee** (job title)
5. **Verify update persisted** (get again)

### Step 7: Monitoring

Monitor for errors after deployment:

```bash
# Watch application logs
tail -f /var/www/fhs-prosight-backend/logs/app.log

# Watch system logs
sudo journalctl -u fhs-prosight-backend -f

# Check for errors
grep -i error /var/www/fhs-prosight-backend/logs/app.log | tail -20

# Monitor database connections
psql -h staging-db.example.com -U db_user -d fhs_prosight_staging \
  -c "SELECT count(*) FROM pg_stat_activity WHERE datname='fhs_prosight_staging';"
```

---

## Production Deployment

Production deployment follows the same steps as staging, but with **additional caution**.

### Pre-Production Checklist

- [ ] Staging deployment successful and verified
- [ ] Feature tested thoroughly in staging environment
- [ ] Stakeholders notified of deployment window
- [ ] Rollback plan reviewed
- [ ] Production database backup verified
- [ ] Change request approved (if required)

### Production Deployment Steps

Follow staging steps with these modifications:

**Step 1 - Backup:**
```bash
# Create production backup
pg_dump -h prod-db.example.com -U db_user -d fhs_prosight_prod \
  -F c -b -v -f "backup_prod_$(date +%Y%m%d_%H%M%S).dump"

# IMPORTANT: Verify backup immediately
pg_restore --list backup_prod_TIMESTAMP.dump | wc -l
# Should show number of objects

# Test restore to temporary database (optional but recommended)
createdb -h prod-db.example.com -U db_user test_restore
pg_restore -h prod-db.example.com -U db_user -d test_restore backup_prod_TIMESTAMP.dump
dropdb -h prod-db.example.com -U db_user test_restore
```

**Step 2-4:** Same as staging (use production URLs and credentials)

**Step 5 - Health Checks:**
```bash
# Use production URLs
curl https://api.fhs-prosight.com/health
curl https://api.fhs-prosight.com/docs

# Test with production admin token
curl -X POST "https://api.fhs-prosight.com/api/employees/sync" \
  -H "Authorization: Bearer PROD_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"emp_id": 6204, "source": "hrs"}'
```

**Step 6 - Monitoring:**
Monitor production logs for at least 1 hour after deployment:

```bash
# Watch for errors
tail -f /var/www/fhs-prosight-backend/logs/app.log | grep -i "error\|exception"

# Monitor API response times
# (use APM tool like New Relic, Datadog, or custom monitoring)

# Check error rate
# Alert if error rate > 5% of requests
```

---

## Rollback Plan

If issues are detected after deployment, follow this rollback procedure:

### Quick Rollback (Code Only)

If database migration succeeded but application has bugs:

```bash
# 1. Revert to previous code version
cd /var/www/fhs-prosight-backend
git log --oneline -5  # Find previous commit
git checkout <previous-commit-sha>

# 2. Reinstall dependencies (if needed)
pip install -r requirements.txt

# 3. Restart application
sudo systemctl restart fhs-prosight-backend

# 4. Verify rollback
curl http://api.example.com/health
```

### Full Rollback (Code + Database)

If database migration caused issues:

```bash
# 1. Rollback database migration
alembic downgrade -1  # Rollback one migration
alembic current       # Verify

# Alternative: Rollback to specific version
alembic downgrade bef7f4fa17b3  # Previous migration ID

# 2. Verify employees table removed/reverted
psql -h db-host -U db_user -d dbname -c "\dt employees"
# Should show: "Did not find any relation named 'employees'"

# 3. Rollback code (see Quick Rollback above)

# 4. Restart application

# 5. Verify rollback successful
```

### Database Restore (Last Resort)

If rollback fails, restore from backup:

```bash
# WARNING: This will lose all data changes since backup!

# 1. Stop application
sudo systemctl stop fhs-prosight-backend

# 2. Drop and recreate database
psql -h db-host -U postgres -c "DROP DATABASE fhs_prosight_prod;"
psql -h db-host -U postgres -c "CREATE DATABASE fhs_prosight_prod OWNER db_user;"

# 3. Restore from backup
pg_restore -h db-host -U db_user -d fhs_prosight_prod backup_prod_TIMESTAMP.dump

# 4. Verify data restored
psql -h db-host -U db_user -d fhs_prosight_prod -c "SELECT COUNT(*) FROM users;"

# 5. Restart application
sudo systemctl start fhs-prosight-backend
```

### Post-Rollback Actions

After rollback:
1. Document reason for rollback
2. Investigate root cause
3. Fix issues in development
4. Re-test in staging
5. Schedule new deployment

---

## Troubleshooting

### Common Issues

#### 1. Migration Fails

**Error:** `alembic upgrade head` fails

**Solution:**
```bash
# Check current state
alembic current

# Check history
alembic history --verbose

# Try manual migration inspection
alembic upgrade head --sql > migration.sql
less migration.sql  # Review SQL

# If table already exists
psql -c "\d employees"  # Check if table exists
# May need to mark migration as complete: alembic stamp head
```

#### 2. Application Won't Start

**Error:** Service fails to start after deployment

**Solution:**
```bash
# Check logs
sudo journalctl -u fhs-prosight-backend -n 100

# Common causes:
# - Import errors (missing dependencies)
pip list | grep -E "fastapi|sqlalchemy|alembic"

# - Database connection issues
psql -h db-host -U db_user -d dbname -c "SELECT 1;"

# - Port already in use
lsof -i :8000
kill <pid>  # If needed

# - Environment variables missing
cat .env | grep -E "DATABASE_URL|SECRET_KEY"
```

#### 3. External API Not Accessible

**Error:** Employee sync fails with connection timeout

**Solution:**
```bash
# Test HRS API
curl -v "https://www.fhs.com.tw/ads/api/Furnace/rest/json/hr/s10/VNW0006204"

# Test COVID API
curl -v "https://www.fhs.com.tw/fhs_covid_api/api/reportVaccines/detail?isFHS=true&userName=VNW0006204" \
  -H "Authorization: Bearer TEST_TOKEN"

# Check firewall rules
# Ensure server can access external APIs

# Check DNS resolution
nslookup www.fhs.com.tw

# Check network connectivity
ping www.fhs.com.tw
```

#### 4. Database Connection Issues

**Error:** `psycopg2.OperationalError: could not connect`

**Solution:**
```bash
# Test database connection
psql -h db-host -U db_user -d dbname

# Check connection string format
# postgresql+asyncpg://user:password@host:port/dbname

# Check if database accepts connections
psql -h db-host -U postgres -c "SHOW max_connections;"

# Check current connections
psql -h db-host -U db_user -d dbname \
  -c "SELECT count(*) FROM pg_stat_activity;"

# Restart PostgreSQL if needed (with caution!)
sudo systemctl restart postgresql
```

---

## Performance Considerations

### Database Indexes

The migration creates these indexes:
- `idx_employees_department_code` on `department_code`
- `idx_employees_identity_number` on `identity_number` (unique)

Verify indexes exist:
```sql
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'employees';
```

### Query Performance

Monitor slow queries:
```sql
-- Enable slow query logging (as superuser)
ALTER DATABASE fhs_prosight_prod SET log_min_duration_statement = 1000;

-- Check slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
WHERE query LIKE '%employees%'
ORDER BY mean_time DESC
LIMIT 10;
```

### Bulk Sync Performance

Expected performance:
- **Single sync:** ~1-2 seconds per employee
- **Bulk sync (100 employees):** ~2-4 minutes
- **Bulk sync (1000 employees):** ~20-40 minutes

Optimize bulk operations:
- Process during off-peak hours
- Use async/background tasks for large batches
- Monitor API rate limits

---

## Monitoring and Alerts

### Recommended Metrics

1. **API Response Times**
   - Sync endpoint: < 2 seconds (p95)
   - Search endpoint: < 500ms (p95)
   - Get/Update/Delete: < 200ms (p95)

2. **Error Rates**
   - Overall error rate: < 1%
   - 5xx errors: < 0.1%

3. **Database**
   - Connection pool utilization: < 80%
   - Query response time: < 100ms (p95)
   - Table size growth: Monitor weekly

4. **External APIs**
   - HRS API availability: > 99%
   - COVID API availability: > 99%

### Log Monitoring

Key log patterns to monitor:

```bash
# Critical errors
grep "ERROR" logs/app.log | tail -20

# Failed syncs
grep "Failed to sync employee" logs/app.log

# Database errors
grep "sqlalchemy" logs/app.log | grep -i error

# API timeouts
grep "timeout" logs/app.log -i
```

---

## Security Considerations

### API Access

- All employee endpoints require **admin role**
- JWT tokens should be rotated regularly
- Use HTTPS in production (always)
- Implement rate limiting on sync endpoints

### Database Security

```sql
-- Grant minimal permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON employees TO app_user;
REVOKE ALL ON employees FROM PUBLIC;

-- Audit employee data access
CREATE TABLE employee_audit_log (
    id SERIAL PRIMARY KEY,
    action VARCHAR(10),
    employee_id VARCHAR(10),
    changed_by VARCHAR(100),
    changed_at TIMESTAMP DEFAULT NOW()
);
```

### Sensitive Data

Employee records contain sensitive information:
- Personal data (DOB, identity number)
- Salary information
- Contact details

Ensure compliance with data protection regulations.

---

## Maintenance

### Regular Tasks

**Weekly:**
- Review error logs
- Check database size growth
- Monitor API performance

**Monthly:**
- Update dependencies (security patches)
- Review and archive old logs
- Validate database backups

**Quarterly:**
- Re-sync employee data from HRS
- Update documentation
- Review and optimize queries

### Database Vacuum

Periodically vacuum employees table:

```sql
-- Analyze table statistics
ANALYZE employees;

-- Vacuum to reclaim space
VACUUM ANALYZE employees;

-- Check table size
SELECT pg_size_pretty(pg_total_relation_size('employees'));
```

---

## Related Documentation

- [API Usage Guide](./employee-api-guide.md) - How to use employee endpoints
- [E2E Test Plan](./employee-e2e-tests.md) - Manual testing scenarios

---

## Support Contacts

**Development Team:**
- Backend Lead: [Name]
- Database Admin: [Name]

**External Dependencies:**
- FHS HRS API: [Contact]
- FHS COVID API: [Contact]

**Emergency Contacts:**
- On-call Engineer: [Phone]
- DevOps Team: [Slack Channel]
