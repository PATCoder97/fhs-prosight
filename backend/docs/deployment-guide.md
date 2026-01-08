# Deployment Guide - Login and Check User Feature

## Overview

This guide provides step-by-step instructions for deploying the OAuth login system with role-based access control and localId management to staging and production environments.

**Features Being Deployed:**
- Alembic migration: Add `localId` column, change default role to 'guest'
- OAuth callback handlers updated (Google + GitHub)
- JWT handler extended with localId and provider fields
- Admin endpoints for user management
- Role-based access control

---

## Pre-Deployment Checklist

### Code Verification
- [ ] All unit tests passing (`pytest tests/test_*.py`)
- [ ] All integration tests passing (`pytest tests/integration/`)
- [ ] Code reviewed and approved
- [ ] No pending code changes
- [ ] Git branch merged to main

### Environment Verification
- [ ] Staging environment accessible
- [ ] Production environment accessible
- [ ] Database credentials available
- [ ] OAuth credentials configured (Google, GitHub)
- [ ] Deployment permissions granted

### Team Communication
- [ ] Team notified of deployment window
- [ ] Deployment scheduled during low-traffic period
- [ ] Rollback plan communicated
- [ ] On-call engineer assigned

---

## Phase 1: Staging Deployment

### Step 1: Backup Staging Database

**Command:**
```bash
# Navigate to scripts directory
cd backend/scripts

# Run backup script
./backup_db.sh staging

# Verify backup created
ls -lh ../backups/staging_backup_*.sql
```

**Manual backup (alternative):**
```bash
pg_dump -h ktxn258.duckdns.org -p 6543 -U casaos casaos > staging_backup_$(date +%Y%m%d_%H%M%S).sql
```

**Verification:**
- [ ] Backup file exists
- [ ] Backup file size > 0
- [ ] Backup file readable

---

### Step 2: Deploy Code to Staging

**Commands:**
```bash
# SSH to staging server (or use CD/CD pipeline)
# ssh staging-server

# Navigate to project directory
cd /path/to/fhs-prosight/backend

# Pull latest code
git fetch origin
git checkout main
git pull origin main

# Verify correct branch
git log -1 --oneline

# Install/update dependencies
pip install -r requirements.txt

# Note: Don't restart service yet (migration first)
```

**Verification:**
- [ ] Correct git commit deployed
- [ ] Dependencies installed
- [ ] No file conflicts

---

### Step 3: Run Migration on Staging

**Commands:**
```bash
# Still in backend directory
# Activate virtual environment if needed
source venv/bin/activate

# Check current migration status
alembic current

# Run migration
alembic upgrade head

# Verify migration completed
alembic current
# Should show: 7b4280a50047 (head)
```

**Database Verification:**
```sql
-- Connect to database
psql -h ktxn258.duckdns.org -p 6543 -U casaos casaos

-- Check schema changes
\d users

-- Expected: localId column present
-- Expected: role default is 'guest'

-- Verify existing data unchanged
SELECT id, email, role, localId FROM users LIMIT 5;
-- Existing users should have their original roles, localId=NULL

-- Exit psql
\q
```

**Verification:**
- [ ] Migration status shows head
- [ ] `localId` column exists
- [ ] `role` default is 'guest'
- [ ] Existing users unchanged
- [ ] No migration errors in logs

---

### Step 4: Restart Staging Service

**Commands:**
```bash
# Restart backend API service
# (Adjust command based on your deployment method)

# Option 1: systemd
sudo systemctl restart backend-api

# Option 2: Docker
docker-compose restart backend

# Option 3: Manual
# pkill -f "uvicorn" && nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Check service status
sudo systemctl status backend-api
# or
docker-compose ps

# Check logs for errors
tail -n 50 /var/log/backend-api/app.log
# or
docker-compose logs backend --tail=50
```

**Verification:**
- [ ] Service started successfully
- [ ] No errors in startup logs
- [ ] API health endpoint responding

---

### Step 5: Run E2E Tests on Staging

**Use E2E Test Plan:**
Refer to `backend/docs/e2e-test-plan.md`

**Critical Test Scenarios:**

**Test 1: New User Google Login**
```bash
# Navigate to: https://staging.example.com/auth/login/google
# Complete OAuth flow
# Expected: role='guest', localId=null
```

**Test 2: Admin Assign LocalId**
```bash
# Get admin token
# Call: PUT /api/users/{user_id}/localId
# Body: {"localId": "VNW001"}
# Expected: 200 OK, success message
```

**Test 3: User Re-Login**
```bash
# User logs in again
# Expected: localId='VNW001' in response and JWT token
```

**Test 4: Health Check**
```bash
curl https://staging.example.com/api/health
# Expected: {"status": "healthy"}
```

**Verification:**
- [ ] All E2E tests pass
- [ ] No 500 errors
- [ ] OAuth flows work (Google + GitHub)
- [ ] Admin endpoints work
- [ ] JWT tokens valid

---

### Step 6: Monitor Staging Metrics

**Check for 1-2 hours:**

**API Metrics:**
```bash
# Response times
# Login success rate
# Error rate

# Use monitoring dashboard or:
tail -f /var/log/backend-api/app.log | grep -E "ERROR|WARNING"
```

**Database Metrics:**
```sql
-- Check query performance
SELECT * FROM pg_stat_statements WHERE query LIKE '%users%' ORDER BY total_time DESC LIMIT 10;

-- Check connection count
SELECT count(*) FROM pg_stat_activity;
```

**Verification:**
- [ ] No critical errors
- [ ] Response times normal
- [ ] Login success rate > 95%
- [ ] Database performance stable

---

## Phase 2: Production Deployment

### Pre-Production Checklist
- [ ] All staging tests passed
- [ ] Staging stable for 24+ hours
- [ ] Production deployment window confirmed
- [ ] Team standing by
- [ ] Rollback plan ready

---

### Step 1: Backup Production Database

**CRITICAL STEP - DO NOT SKIP**

**Commands:**
```bash
# Run backup script
cd backend/scripts
./backup_db.sh production

# Upload to cloud storage for safety
aws s3 cp ../backups/prod_backup_*.sql s3://your-bucket/backups/database/

# Or manually
pg_dump -h ktxn258.duckdns.org -p 6543 -U casaos casaos > prod_backup_$(date +%Y%m%d_%H%M%S).sql
```

**Verify Backup Integrity:**
```bash
# Test restore to temporary database
pg_restore --list prod_backup_*.sql
# Should list all tables without errors
```

**Verification:**
- [ ] Backup file created
- [ ] Backup uploaded to cloud
- [ ] Backup integrity verified
- [ ] Backup size reasonable (similar to previous backups)

---

### Step 2: Deploy Code to Production

**Commands:**
```bash
# SSH to production server
# ssh production-server

cd /path/to/fhs-prosight/backend

# Pull latest code
git fetch origin
git checkout main
git pull origin main

# Verify commit hash matches staging
git log -1 --oneline

# Install dependencies
pip install -r requirements.txt
```

**Verification:**
- [ ] Correct commit deployed
- [ ] Same commit as staging
- [ ] Dependencies installed

---

### Step 3: Run Migration on Production

**Commands:**
```bash
source venv/bin/activate

# Check current state
alembic current

# Run migration
alembic upgrade head

# Verify
alembic current
psql -h ktxn258.duckdns.org -p 6543 -U casaos casaos -c "\d users"
```

**Database Verification:**
```sql
-- Check localId column added
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'users' AND column_name = 'localId';
-- Expected: localId | character varying(50) | YES

-- Check role default
SELECT column_default
FROM information_schema.columns
WHERE table_name = 'users' AND column_name = 'role';
-- Expected: 'guest'::character varying

-- Verify existing users unchanged
SELECT COUNT(*) FROM users WHERE role != 'guest';
-- Should be > 0 (existing users keep their roles)
```

**Verification:**
- [ ] Migration completed successfully
- [ ] Schema changes applied
- [ ] Existing user data preserved
- [ ] No migration errors

---

### Step 4: Zero-Downtime Restart

**Option 1: Rolling Restart (Multiple Instances)**
```bash
# If using load balancer with multiple backend instances
# Restart instances one by one

# Instance 1
ssh backend-1
sudo systemctl restart backend-api
# Wait for health check
curl localhost:8000/health

# Instance 2
ssh backend-2
sudo systemctl restart backend-api
# etc...
```

**Option 2: Blue-Green Deployment**
```bash
# If using blue-green deployment
# Deploy to green environment
# Switch load balancer to green
# Keep blue as rollback
```

**Option 3: Graceful Reload**
```bash
# Single instance with graceful reload
sudo systemctl reload backend-api
# or
kill -HUP $(cat /var/run/backend-api.pid)
```

**Verification:**
- [ ] Service restarted
- [ ] No downtime detected
- [ ] Health check passes
- [ ] Existing connections handled gracefully

---

### Step 5: Smoke Tests on Production

**Critical Tests (Run Immediately):**

**Test 1: Health Check**
```bash
curl https://api.example.com/health
# Expected: 200 OK
```

**Test 2: Existing User Login**
```bash
# Use a real existing user account
# Login via Google OAuth
# Expected: Successful login, existing role preserved
```

**Test 3: Database Query**
```sql
-- Verify schema
SELECT COUNT(*) FROM users WHERE localId IS NULL;
-- Should be count of existing users

SELECT COUNT(*) FROM users WHERE role = 'guest';
-- Should be >= 0 (only new users after deployment)
```

**Test 4: Admin Endpoint (if admin exists)**
```bash
# Login as admin
# Try: GET /api/users
# Expected: 200 OK, list of users
```

**Verification:**
- [ ] All smoke tests pass
- [ ] Existing users can login
- [ ] No 500 errors
- [ ] API responding normally

---

## Phase 3: Post-Deployment Monitoring

### First Hour

**Monitor These Metrics:**
- [ ] Login success rate (should be > 95%)
- [ ] API error rate (should not increase)
- [ ] Response times (should be stable)
- [ ] Database performance (should be normal)

**Commands:**
```bash
# Watch logs in real-time
tail -f /var/log/backend-api/app.log | grep -E "ERROR|CRITICAL"

# Monitor login attempts
grep "OAuth callback" /var/log/backend-api/app.log | tail -n 20

# Check error rate
grep "ERROR" /var/log/backend-api/app.log | wc -l
```

### First 24 Hours

**Metrics to Track:**
- Login success rate
- New user registrations (role should be 'guest')
- Admin operations (assign localId, update role)
- JWT token validation errors
- Database query performance

**Alert Thresholds:**
- Login success rate < 90% → Investigate immediately
- Error rate increase > 50% → Investigate
- Response time > 3x normal → Investigate
- Database CPU > 80% → Investigate

---

## Rollback Procedures

### When to Rollback

**Trigger Rollback If:**
- Login success rate drops below 90%
- Critical errors spike (>10 errors/min)
- Data corruption detected
- Performance severely degraded
- Security vulnerability discovered

### Rollback Steps

**Step 1: Rollback Code**
```bash
ssh production-server
cd /path/to/fhs-prosight/backend

# Checkout previous version
git log --oneline -5  # Find previous commit
git checkout <previous-commit-hash>

# Restart service
sudo systemctl restart backend-api

# Verify rollback
curl https://api.example.com/health
```

**Step 2: Rollback Migration**
```bash
# Rollback database migration
alembic downgrade -1

# Verify schema reverted
psql -h ktxn258.duckdns.org -p 6543 -U casaos casaos -c "\d users"
# localId column should be gone
```

**Step 3: Verify Rollback**
```bash
# Test existing functionality
# Run smoke tests
# Check logs for errors
```

**Step 4: Restore from Backup (Last Resort)**
```bash
# Only if migration rollback fails
psql -h ktxn258.duckdns.org -p 6543 -U casaos casaos < prod_backup_TIMESTAMP.sql

# Verify restoration
psql -h ktxn258.duckdns.org -p 6543 -U casaos casaos -c "SELECT COUNT(*) FROM users;"
```

**Post-Rollback:**
- [ ] Announce rollback to team
- [ ] Document rollback reason
- [ ] Fix issue in code
- [ ] Re-test on staging
- [ ] Schedule new deployment

---

## Post-Deployment Report

**After deployment completes, document:**

### Deployment Summary
- Deployment date and time:
- Duration:
- Deployed by:
- Git commit hash:

### Results
- [ ] Staging deployment: SUCCESS / FAILED
- [ ] Production deployment: SUCCESS / FAILED
- [ ] All tests passed: YES / NO
- [ ] Rollback required: YES / NO

### Metrics
- Login success rate: ____%
- Average response time: ___ms
- Error rate: ___/min
- Downtime: ___min

### Issues Encountered
- List any issues and how they were resolved

### Next Steps
- List any follow-up actions needed

**Template:** See `backend/docs/post-deployment-report-template.md`

---

## Troubleshooting

### Common Issues

**Issue: Migration fails with "column already exists"**
```bash
# Solution: Check if migration already ran
alembic current
# If at head, no action needed

# If partially migrated, check database manually
psql -c "\d users"
```

**Issue: Service won't start after deployment**
```bash
# Check logs
tail -n 100 /var/log/backend-api/app.log

# Common causes:
# - Syntax error in code
# - Missing dependencies
# - Configuration error
# - Port already in use
```

**Issue: OAuth login fails**
```bash
# Verify OAuth credentials
# Check environment variables
echo $GOOGLE_CLIENT_ID
echo $GITHUB_CLIENT_ID

# Test OAuth endpoints
curl https://api.example.com/auth/login/google
```

**Issue: Admin endpoints return 500**
```bash
# Check database connection
psql -h ktxn258.duckdns.org -p 6543 -U casaos casaos -c "SELECT 1;"

# Check logs for specific error
grep "admin" /var/log/backend-api/app.log | grep ERROR
```

---

## Contact Information

**On-Call Engineers:**
- Primary: [Name] - [Phone]
- Secondary: [Name] - [Phone]

**Escalation:**
- Team Lead: [Name] - [Phone]
- DevOps: [Name] - [Phone]

**Resources:**
- Monitoring Dashboard: [URL]
- Error Tracking: [URL]
- Documentation: [URL]

---

## Appendix

### Environment Variables Required

```env
# Database
POSTGRES_HOST=ktxn258.duckdns.org
POSTGRES_PORT=6543
POSTGRES_USER=casaos
POSTGRES_PASSWORD=***
POSTGRES_DB=casaos

# OAuth
GOOGLE_CLIENT_ID=***
GOOGLE_CLIENT_SECRET=***
GITHUB_CLIENT_ID=***
GITHUB_CLIENT_SECRET=***

# JWT
SECRET_KEY=***
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### Migration Files

**Relevant migrations:**
- `9a0ea82c4ee9_initial_schema.py` - Initial schema
- `7b4280a50047_add_localid_and_fix_role_default.py` - Main migration

### Related Documentation

- E2E Test Plan: `backend/docs/e2e-test-plan.md`
- Monitoring Guide: `backend/docs/monitoring.md`
- Unit Tests: `backend/tests/test_*.py`
- Integration Tests: `backend/tests/integration/`
