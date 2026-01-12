# PIDMS API Troubleshooting

Common issues and solutions for the PIDMS API.

## Common Issues

### 1. "Invalid PIDKey.com API key"

**Symptoms:**
- 500 error when calling `/check` or `/sync`
- Error message: "Invalid PIDKey.com API key"

**Cause:** 
- PIDKEY_API_KEY environment variable not set or incorrect

**Solution:**
```bash
# Check .env file exists
ls backend/.env

# Verify API key is set
cat backend/.env | grep PIDKEY_API_KEY

# Value should match your PIDKey.com account API key
# Restart server after updating .env
```

---

### 2. "PIDKey.com API timeout"

**Symptoms:**
- 504 Gateway Timeout error
- Slow response times
- Error message: "PIDKey.com API timeout"

**Cause:** 
- Network issues
- PIDKey.com service slow or down
- Firewall blocking outbound HTTPS

**Solution:**
```bash
# Check internet connectivity
ping 8.8.8.8

# Verify PIDKey.com is accessible
curl -I https://pidkey.com

# Check firewall rules allow HTTPS to pidkey.com
# Retry request (automatic retry logic in place)
```

---

### 3. "Rate limited by PIDKey.com"

**Symptoms:**
- 503 Service Unavailable error
- Error message: "PIDKey.com API rate limit exceeded"

**Cause:** 
- Too many requests to PIDKey.com API in short time
- Daily/hourly quota exceeded

**Solution:**
- Wait for retry-after period (shown in error message)
- Reduce batch size in sync operations
- Space out check operations
- Contact PIDKey.com to increase rate limits
- Consider upgrading PIDKey.com subscription

**Prevention:**
```bash
# Don't sync too frequently
# Recommended: Once per day during off-peak hours

# Use product filter to sync subsets
curl -X POST http://localhost:8000/api/pidms/sync \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"product_filter": "Office16"}'
```

---

### 4. "Search query slow (>2s)"

**Symptoms:**
- Search endpoint takes >2 seconds to respond
- Database CPU usage high

**Cause:** 
- Missing indexes
- Large dataset without proper indexing
- Database statistics out of date

**Solution:**
```sql
-- Verify indexes exist
\d pidms_keys

-- Should see:
-- idx_pidms_keys_keyname
-- idx_pidms_keys_prd
-- idx_pidms_keys_remaining
-- idx_pidms_keys_blocked

-- If missing, run migration again
-- alembic upgrade head

-- Update table statistics
ANALYZE pidms_keys;

-- Check query plan
EXPLAIN ANALYZE
SELECT * FROM pidms_keys
WHERE prd ILIKE '%Office%'
  AND remaining >= 100
ORDER BY prd, remaining DESC
LIMIT 50;

-- Should show "Index Scan" not "Seq Scan"
```

---

### 5. "401 Unauthorized"

**Symptoms:**
- All API requests return 401
- Error message: "Not authenticated"

**Cause:** 
- Missing Authorization header
- Invalid or expired token

**Solution:**
```bash
# Login again to get fresh token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_password"}'

# Export token
export ADMIN_TOKEN="eyJ..."

# Verify token is being sent
curl -v -X GET "http://localhost:8000/api/pidms/products" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Should see "Authorization: Bearer eyJ..." in request headers
```

---

### 6. "403 Forbidden"

**Symptoms:**
- API requests return 403
- Error message: "Insufficient permissions"

**Cause:** 
- User is not an admin
- Token valid but user lacks admin role

**Solution:**
```sql
-- Check user role in database
SELECT id, username, role FROM users WHERE username = 'your_username';

-- Should show role = 'admin'

-- If not admin, grant admin role
UPDATE users SET role = 'admin' WHERE username = 'your_username';
```

---

### 7. "No valid keys provided"

**Symptoms:**
- 422 Validation Error on `/check`
- Error message: "No valid keys provided"

**Cause:** 
- Empty keys string
- Keys not properly formatted

**Solution:**
```bash
# Ensure keys field is not empty
curl -X POST http://localhost:8000/api/pidms/check \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "keys": "6NRGD-KHFCF-Y4TF7-PRWFD-YBF3H"
  }'

# Keys can be separated by \r\n or \n
# Both with dashes and without dashes work
```

---

### 8. "Database migration failed"

**Symptoms:**
- Error running `alembic upgrade head`
- Table pidms_keys doesn't exist

**Cause:** 
- Database connection issue
- Migration script error
- Conflicting migration

**Solution:**
```bash
# Check database connection
psql -d fhs_prosight -c "SELECT 1;"

# Check current migration version
cd backend
alembic current

# Check migration history
alembic history

# If stuck, try downgrade then upgrade
alembic downgrade -1
alembic upgrade head

# If still failing, check logs
tail -f logs/fhs-prosight.log
```

---

### 9. "Sync completed but keys not updated"

**Symptoms:**
- Sync returns success but activation counts unchanged
- No errors in response

**Cause:** 
- PIDKey.com data hasn't changed
- Keys already up-to-date

**Solution:**
```bash
# Check last sync time
psql -d fhs_prosight -c "SELECT keyname, remaining, updated_at FROM pidms_keys LIMIT 10;"

# If updated_at is recent, data is fresh
# PIDKey.com activation counts may not have changed

# Force check specific key
curl -X POST http://localhost:8000/api/pidms/check \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"keys": "6NRGD-KHFCF-Y4TF7-PRWFD-YBF3H"}'
```

---

### 10. "Server won't start - PIDKEY_API_KEY not set"

**Symptoms:**
- Server crashes on startup
- Error: "PIDKEY_API_KEY environment variable required"

**Cause:** 
- .env file missing or not loaded
- Environment variable not set

**Solution:**
```bash
# Create .env file if missing
cd backend
cat > .env << EOF
PIDKEY_API_KEY=your_api_key_here
PIDKEY_BASE_URL=https://pidkey.com/ajax/pidms_api
EOF

# Verify .env is in backend directory
ls -la .env

# Restart server
uvicorn app.main:app --reload
```

---

## Debugging Tools

### View Application Logs

```bash
# Real-time logs
tail -f logs/fhs-prosight.log

# Filter for PIDMS-related logs
tail -f logs/fhs-prosight.log | grep -i pidms

# Filter for errors
tail -f logs/fhs-prosight.log | grep -i error
```

### Database Queries

```sql
-- Count total keys
SELECT COUNT(*) FROM pidms_keys;

-- Count by product
SELECT prd, COUNT(*) FROM pidms_keys GROUP BY prd;

-- Find low inventory products
SELECT prd, SUM(remaining) as total FROM pidms_keys 
GROUP BY prd 
HAVING SUM(remaining) < 5;

-- Recently updated keys
SELECT keyname, prd, remaining, updated_at 
FROM pidms_keys 
ORDER BY updated_at DESC 
LIMIT 10;

-- Blocked keys
SELECT COUNT(*) FROM pidms_keys WHERE blocked = 1;
```

### API Health Check

```bash
# Server running?
curl http://localhost:8000/health

# Database connection?
psql -d fhs_prosight -c "SELECT 1;"

# PIDKey.com accessible?
curl -I https://pidkey.com
```

---

## Performance Optimization

### Slow Searches

```sql
-- Rebuild indexes
REINDEX TABLE pidms_keys;

-- Update statistics
ANALYZE pidms_keys;

-- Vacuum to reclaim space
VACUUM ANALYZE pidms_keys;
```

### Slow Syncs

```bash
# Reduce batch size (not currently configurable, but could be added)
# Sync subsets by product
curl -X POST http://localhost:8000/api/pidms/sync \
  -d '{"product_filter": "Office15"}'

curl -X POST http://localhost:8000/api/pidms/sync \
  -d '{"product_filter": "Office16"}'
```

---

## Getting Help

If issues persist:

1. Check server logs: `tail -f logs/fhs-prosight.log`
2. Check database logs: `tail -f /var/log/postgresql/postgresql.log`
3. Verify all environment variables set correctly
4. Test with Swagger UI: http://localhost:8000/docs
5. Contact support with:
   - Error message
   - Request that caused error
   - Relevant log entries
   - Database migration version (`alembic current`)
