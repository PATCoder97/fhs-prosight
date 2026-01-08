# Monitoring Guide - Login and Check User Feature

## Overview

This guide outlines the metrics, logs, and alerts to monitor after deploying the OAuth login system with role-based access control.

---

## Critical Metrics

### 1. Login Success Rate

**What to monitor:**
- Percentage of successful OAuth logins (Google + GitHub)
- Target: > 95%

**How to measure:**
```sql
-- Query login attempts vs successes
SELECT
    DATE(created_at) as date,
    COUNT(*) as total_logins,
    COUNT(*) FILTER (WHERE is_verified = true) as successful_logins,
    ROUND(100.0 * COUNT(*) FILTER (WHERE is_verified = true) / COUNT(*), 2) as success_rate
FROM users
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

**Alert conditions:**
- Success rate < 95% → Warning
- Success rate < 90% → Critical

---

### 2. API Response Time

**What to monitor:**
- OAuth callback endpoint response time
- JWT token validation time
- Admin endpoints response time

**Targets:**
- OAuth callback (p95): < 2 seconds
- Token validation (p99): < 100ms
- Admin endpoints (p95): < 500ms

**How to measure:**
```bash
# Using application logs
grep "OAuth callback" app.log | awk '{print $NF}' | sort -n | tail -5

# Using monitoring tool (Prometheus example)
rate(http_request_duration_seconds_sum[5m]) /
rate(http_request_duration_seconds_count[5m])
```

**Alert conditions:**
- p95 response time > 3 seconds → Warning
- p95 response time > 5 seconds → Critical

---

### 3. Error Rate

**What to monitor:**
- 500 errors (server errors)
- 401 errors (authentication failures)
- 403 errors (authorization failures)

**Targets:**
- 500 errors: 0 per hour
- 401 errors: < 5% of requests (some expected)
- 403 errors: < 2% of requests (expected for non-admin)

**How to measure:**
```bash
# Count errors in logs
grep "ERROR" app.log | wc -l

# By error code
grep " 500 " access.log | wc -l
grep " 401 " access.log | wc -l
grep " 403 " access.log | wc -l

# Error rate
total=$(wc -l < access.log)
errors=$(grep " 500 " access.log | wc -l)
echo "scale=2; $errors / $total * 100" | bc
```

**Alert conditions:**
- 500 errors > 10/hour → Critical
- Error rate increase > 50% → Warning

---

### 4. Database Performance

**What to monitor:**
- Query execution time
- Connection pool utilization
- Slow queries

**Targets:**
- Average query time: < 50ms
- Connection pool usage: < 80%
- No queries > 1 second

**How to measure:**
```sql
-- Slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
WHERE mean_time > 100
ORDER BY mean_time DESC
LIMIT 10;

-- Database connections
SELECT count(*) as connections,
       max_conn,
       ROUND(100.0 * count(*) / max_conn, 2) as usage_percent
FROM pg_stat_activity,
     (SELECT setting::int as max_conn FROM pg_settings WHERE name = 'max_connections') mc
GROUP BY max_conn;

-- Table-specific stats
SELECT schemaname, tablename, seq_scan, idx_scan,
       n_tup_ins, n_tup_upd, n_tup_del
FROM pg_stat_user_tables
WHERE tablename = 'users';
```

**Alert conditions:**
- Query time > 1 second → Warning
- Connection pool > 90% → Critical

---

### 5. New User Metrics

**What to monitor:**
- New user registrations per day
- Default role distribution (should be 'guest')
- LocalId assignment rate

**How to measure:**
```sql
-- New users per day
SELECT DATE(created_at) as date,
       COUNT(*) as new_users,
       COUNT(*) FILTER (WHERE role = 'guest') as guests,
       COUNT(*) FILTER (WHERE localId IS NOT NULL) as with_localId
FROM users
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Role distribution
SELECT role, COUNT(*) as count,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM users), 2) as percentage
FROM users
GROUP BY role;

-- LocalId coverage
SELECT
    COUNT(*) FILTER (WHERE localId IS NOT NULL) as with_localId,
    COUNT(*) FILTER (WHERE localId IS NULL) as without_localId,
    ROUND(100.0 * COUNT(*) FILTER (WHERE localId IS NOT NULL) / COUNT(*), 2) as coverage_percent
FROM users;
```

**Expected:**
- New users should have role = 'guest' (100%)
- LocalId NULL for new users (until admin assigns)

---

## Log Monitoring

### Application Logs

**Location:** `/var/log/backend-api/app.log` or via Docker logs

**Key patterns to monitor:**

**1. OAuth Errors**
```bash
# Google OAuth errors
grep "google.*error" app.log -i | tail -20

# GitHub OAuth errors
grep "github.*error" app.log -i | tail -20

# Token errors
grep "token.*error" app.log -i | tail -20
```

**2. Database Errors**
```bash
# Connection errors
grep "database.*connection.*error" app.log -i

# Query errors
grep "sqlalchemy.*error" app.log -i

# Migration errors
grep "alembic.*error" app.log -i
```

**3. Authorization Errors**
```bash
# Admin endpoint access attempts
grep "403.*users" app.log

# Role check failures
grep "Insufficient permissions" app.log
```

**4. Validation Errors**
```bash
# Invalid localId format
grep "localId.*alphanumeric" app.log

# Invalid role
grep "role.*must be" app.log
```

### Access Logs

**Location:** `/var/log/nginx/access.log` or API gateway logs

**Key patterns:**

```bash
# Request volume
awk '{print $4}' access.log | cut -d: -f1-2 | uniq -c

# Status code distribution
awk '{print $9}' access.log | sort | uniq -c | sort -rn

# Slowest endpoints
awk '{print $7, $NF}' access.log | sort -k2 -rn | head -20

# OAuth endpoints specifically
grep "/auth/" access.log | awk '{print $7}' | sort | uniq -c
```

---

## Alerts Configuration

### Alert Rules (Example for Prometheus/Grafana)

```yaml
groups:
  - name: login_system_alerts
    interval: 1m
    rules:
      # Login success rate
      - alert: LowLoginSuccessRate
        expr: login_success_rate < 0.95
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Login success rate below 95%"

      - alert: CriticalLoginFailures
        expr: login_success_rate < 0.90
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Login success rate critically low"

      # Response time
      - alert: SlowOAuthCallback
        expr: histogram_quantile(0.95, rate(oauth_callback_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "OAuth callback p95 > 2 seconds"

      # Error rate
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High rate of 5xx errors"

      # Database
      - alert: DatabaseConnectionPoolHigh
        expr: database_connections_usage > 0.80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Database connection pool usage > 80%"
```

### Email/Slack Notifications

**Critical alerts:**
- Login success rate < 90%
- 500 errors > 10/hour
- Database connection pool > 90%
- API completely down

**Warning alerts:**
- Login success rate < 95%
- Response time > 2x normal
- Database connection pool > 80%

---

## Dashboard Recommendations

### Key Metrics Dashboard

**Panel 1: Login Overview**
- Total logins (24h)
- Success rate (%)
- Login by provider (Google vs GitHub)
- New users vs returning users

**Panel 2: Performance**
- API response time (p50, p95, p99)
- OAuth callback time
- Token validation time
- Database query time

**Panel 3: Errors**
- Error rate by status code
- Top errors (last 1 hour)
- Failed login attempts
- Authorization failures

**Panel 4: User Metrics**
- Total users
- Users by role (guest/user/admin)
- Users with localId assigned
- Active users (last 24h)

### Sample Grafana Dashboard JSON

```json
{
  "dashboard": {
    "title": "OAuth Login System",
    "panels": [
      {
        "title": "Login Success Rate",
        "targets": [
          {
            "expr": "rate(login_success_total[5m]) / rate(login_attempts_total[5m])"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Response Time (p95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))"
          }
        ],
        "type": "graph"
      }
    ]
  }
}
```

---

## Incident Response

### Incident Severity Levels

**P0 - Critical (Immediate Response)**
- Login completely broken (success rate < 50%)
- Database down
- API returning 500s for all requests
- Data corruption detected

**P1 - High (Response within 1 hour)**
- Login success rate < 90%
- Major performance degradation (>5x slow)
- High error rate (>5% of requests)

**P2 - Medium (Response within 4 hours)**
- Login success rate 90-95%
- Moderate performance issues
- Single provider (Google or GitHub) failing

**P3 - Low (Response within 24 hours)**
- Minor performance degradation
- Isolated errors
- Non-critical feature issues

### Incident Response Checklist

**When alert fires:**

1. **Acknowledge**
   - [ ] Acknowledge alert in monitoring system
   - [ ] Notify team in Slack/Teams

2. **Assess**
   - [ ] Check dashboard for impact scope
   - [ ] Review recent deployments
   - [ ] Check error logs
   - [ ] Determine severity level

3. **Mitigate**
   - [ ] If P0/P1: Consider rollback
   - [ ] If database issue: Check connections, queries
   - [ ] If OAuth issue: Check provider status
   - [ ] If performance: Check resource usage

4. **Communicate**
   - [ ] Update status page (if applicable)
   - [ ] Notify stakeholders
   - [ ] Provide regular updates

5. **Resolve**
   - [ ] Apply fix or rollback
   - [ ] Verify fix with tests
   - [ ] Monitor for 30 minutes

6. **Document**
   - [ ] Write incident report
   - [ ] Document root cause
   - [ ] Create follow-up tasks

---

## Post-Deployment Monitoring Schedule

### First Hour
- [ ] Monitor logs every 5 minutes
- [ ] Check error rate
- [ ] Verify OAuth logins working
- [ ] Check database performance

### First 24 Hours
- [ ] Monitor logs every hour
- [ ] Check success metrics
- [ ] Review slow queries
- [ ] Verify new users have correct role

### First Week
- [ ] Daily metrics review
- [ ] Weekly performance report
- [ ] User feedback collection
- [ ] Optimization opportunities

---

## Useful Queries

### Quick Health Check
```sql
-- Overall system health
SELECT
    'Total Users' as metric, COUNT(*)::text as value FROM users
UNION ALL
SELECT 'Active Today', COUNT(DISTINCT id)::text FROM users WHERE last_login::date = CURRENT_DATE
UNION ALL
SELECT 'New Today', COUNT(*)::text FROM users WHERE created_at::date = CURRENT_DATE
UNION ALL
SELECT 'With LocalId', COUNT(*)::text FROM users WHERE localId IS NOT NULL
UNION ALL
SELECT 'Admins', COUNT(*)::text FROM users WHERE role = 'admin';
```

### Performance Analysis
```sql
-- Slowest queries (requires pg_stat_statements)
SELECT
    substring(query, 1, 100) as query_preview,
    calls,
    ROUND(total_time::numeric, 2) as total_ms,
    ROUND(mean_time::numeric, 2) as avg_ms,
    ROUND((100 * total_time / SUM(total_time) OVER ())::numeric, 2) as percent
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;
```

### OAuth Activity
```sql
-- Login activity by provider
SELECT
    provider,
    DATE(last_login) as date,
    COUNT(*) as logins
FROM users
WHERE last_login >= NOW() - INTERVAL '7 days'
GROUP BY provider, DATE(last_login)
ORDER BY date DESC, provider;
```

---

## Contacts

**On-Call Engineer:** [Name] - [Phone]
**DevOps Team:** [Email]
**Monitoring Dashboard:** [URL]
**Incident Management:** [URL]
