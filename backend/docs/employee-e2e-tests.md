# Employee E2E Test Plan

## Overview

End-to-end test plan for manually testing the employee synchronization and management feature in staging/production environments.

**Purpose:** Verify complete employee workflows work correctly with real external APIs and database.

**Environment:** Staging API
**Tester Role:** Admin user
**Duration:** ~2-3 hours for complete test suite

---

## Test Environment Setup

### Prerequisites

**1. Access:**
- [ ] Staging API URL: `https://staging-api.example.com`
- [ ] Admin account credentials
- [ ] Database access (read-only for verification)

**2. Tools:**
- [ ] cURL or Postman
- [ ] Database client (psql or DBeaver)
- [ ] Text editor for documenting results

**3. Test Data:**
- Test employee IDs: **6200-6210** (HRS API)
- COVID API test token: **[Obtain from FHS COVID admin]**

### Getting Admin JWT Token

```bash
# 1. Login via OAuth (Google/GitHub)
curl -X GET "https://staging-api.example.com/api/auth/google/login"

# 2. Complete OAuth flow in browser

# 3. Extract JWT token from callback
# Token will be in response or session cookie

# 4. Test token
export ADMIN_TOKEN="your_jwt_token_here"
curl -X GET "https://staging-api.example.com/api/users/me" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Verify role is "admin"
```

---

## Test Scenarios

### Scenario 1: Sync Single Employee from HRS

**Objective:** Verify basic employee sync from HRS API

**Test Steps:**

1. **Clean Test Data (if exists)**
   ```bash
   curl -X DELETE "https://staging-api.example.com/api/employees/VNW0006204" \
     -H "Authorization: Bearer $ADMIN_TOKEN"
   ```

2. **Sync Employee**
   ```bash
   curl -X POST "https://staging-api.example.com/api/employees/sync" \
     -H "Authorization: Bearer $ADMIN_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "emp_id": 6204,
       "source": "hrs"
     }' | jq '.'
   ```

3. **Verify Response**
   - Status code: **200 OK**
   - Response includes:
     - `id`: "VNW0006204"
     - `name_tw`: Chinese name (e.g., "陳玉俊")
     - `name_en`: Vietnamese name (e.g., "PHAN ANH TUẤN" or "Phan Anh Tuấn")
     - `department_code`: Department code
     - `job_title`: Job title
     - `salary`: Salary (integer)
     - `created_at`: Timestamp

4. **Verify in Database**
   ```sql
   SELECT id, name_tw, name_en, department_code, job_title, salary, created_at
   FROM employees
   WHERE id = 'VNW0006204';
   ```

**Expected Results:**
- ✅ API returns 200 OK
- ✅ Employee data complete (22 fields from HRS)
- ✅ Chinese name displays correctly (UTF-8)
- ✅ Vietnamese name normalized (capitalized)
- ✅ Salary parsed correctly (no commas)
- ✅ Database record created

**Test Result:** [ ] Pass  [ ] Fail

**Notes:**
_______________________________________

---

### Scenario 2: Sync Single Employee from COVID API

**Objective:** Verify employee sync from COVID API with token

**Test Steps:**

1. **Sync Employee with COVID Token**
   ```bash
   curl -X POST "https://staging-api.example.com/api/employees/sync" \
     -H "Authorization: Bearer $ADMIN_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "emp_id": 6204,
       "source": "covid",
       "token": "YOUR_COVID_API_TOKEN"
     }' | jq '.'
   ```

2. **Verify Response**
   - Status code: **200 OK**
   - Response includes COVID-specific fields:
     - `identity_number`: ID number
     - `nationality`: Nationality code (e.g., "VN")
     - `sex`: Gender (M/F)

3. **Verify Data Merge**
   ```sql
   SELECT id, name_tw, identity_number, nationality, sex, dept, job_title
   FROM employees
   WHERE id = 'VNW0006204';
   ```
   - HRS fields (dept, job_title) should remain unchanged
   - COVID fields (identity_number, nationality, sex) should be added/updated

**Expected Results:**
- ✅ API returns 200 OK
- ✅ COVID fields added to existing employee
- ✅ HRS fields not overwritten
- ✅ Data correctly merged

**Test Result:** [ ] Pass  [ ] Fail

**Notes:**
_______________________________________

---

### Scenario 3: Sync Without COVID Token (Error Handling)

**Objective:** Verify error handling when COVID token is missing

**Test Steps:**

1. **Attempt Sync Without Token**
   ```bash
   curl -X POST "https://staging-api.example.com/api/employees/sync" \
     -H "Authorization: Bearer $ADMIN_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "emp_id": 6204,
       "source": "covid"
     }'
   ```

2. **Verify Error Response**
   - Status code: **400 Bad Request**
   - Error message: "Token required for COVID source" (or similar)

**Expected Results:**
- ✅ API returns 400 Bad Request
- ✅ Error message clear and actionable
- ✅ No database changes made

**Test Result:** [ ] Pass  [ ] Fail

---

### Scenario 4: Sync Non-Existent Employee (Error Handling)

**Objective:** Verify error when employee doesn't exist in external API

**Test Steps:**

1. **Attempt Sync with Invalid ID**
   ```bash
   curl -X POST "https://staging-api.example.com/api/employees/sync" \
     -H "Authorization: Bearer $ADMIN_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "emp_id": 9999,
       "source": "hrs"
     }'
   ```

2. **Verify Error Response**
   - Status code: **404 Not Found**
   - Error message: "Employee 9999 not found in HRS API" (or similar)

**Expected Results:**
- ✅ API returns 404 Not Found
- ✅ Error message indicates employee not found
- ✅ No database record created

**Test Result:** [ ] Pass  [ ] Fail

---

### Scenario 5: Bulk Sync Employees

**Objective:** Verify bulk sync of multiple employees

**Test Steps:**

1. **Clean Test Data**
   ```bash
   for id in {6200..6210}; do
     curl -X DELETE "https://staging-api.example.com/api/employees/VNW000$id" \
       -H "Authorization: Bearer $ADMIN_TOKEN"
   done
   ```

2. **Bulk Sync 11 Employees**
   ```bash
   curl -X POST "https://staging-api.example.com/api/employees/bulk-sync" \
     -H "Authorization: Bearer $ADMIN_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "from_id": 6200,
       "to_id": 6210,
       "source": "hrs"
     }' | jq '.'
   ```

3. **Verify Summary Response**
   - Status code: **200 OK**
   - Response includes:
     - `total`: 11
     - `success`: Number of successful syncs
     - `failed`: Number of failed syncs
     - `skipped`: Number of skipped (not found) employees
     - `errors`: Array of error details (if any)

4. **Verify in Database**
   ```sql
   SELECT COUNT(*) FROM employees
   WHERE id BETWEEN 'VNW0006200' AND 'VNW0006210';
   ```
   - Count should match `success` count from API response

5. **Monitor Performance**
   - Record start and end time
   - Calculate duration
   - Expected: ~1-2 seconds per employee (11 employees ≈ 15-25 seconds)

**Expected Results:**
- ✅ API returns 200 OK
- ✅ Summary counts correct (total = success + failed + skipped)
- ✅ Successful employees stored in database
- ✅ Errors array has details for failed employees
- ✅ Performance acceptable (< 30 seconds for 11 employees)

**Test Result:** [ ] Pass  [ ] Fail

**Performance:** _______ seconds

**Notes:**
_______________________________________

---

### Scenario 6: Bulk Sync with Invalid Range (Error Handling)

**Objective:** Verify validation of bulk sync range

**Test Steps:**

1. **Attempt Invalid Range (to_id < from_id)**
   ```bash
   curl -X POST "https://staging-api.example.com/api/employees/bulk-sync" \
     -H "Authorization: Bearer $ADMIN_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "from_id": 6210,
       "to_id": 6200,
       "source": "hrs"
     }'
   ```

2. **Verify Validation Error**
   - Status code: **422 Unprocessable Entity**
   - Error indicates `to_id` must be >= `from_id`

**Expected Results:**
- ✅ API returns 422 Validation Error
- ✅ Error message explains validation issue
- ✅ No database changes made

**Test Result:** [ ] Pass  [ ] Fail

---

### Scenario 7: Search Employees by Name

**Objective:** Verify employee search functionality

**Test Steps:**

1. **Ensure Test Data Exists**
   - Sync employee from Scenario 1 if needed

2. **Search by Chinese Name (Partial Match)**
   ```bash
   curl -X GET "https://staging-api.example.com/api/employees/search?name=陳玉" \
     -H "Authorization: Bearer $ADMIN_TOKEN" | jq '.'
   ```

3. **Verify Search Results**
   - Status code: **200 OK**
   - Response includes:
     - `items`: Array of matching employees
     - `total`: Total count
     - `skip`: 0
     - `limit`: 100 (default)
   - At least one employee with Chinese name containing "陳玉"

4. **Search by Vietnamese Name**
   ```bash
   curl -X GET "https://staging-api.example.com/api/employees/search?name=Phan" \
     -H "Authorization: Bearer $ADMIN_TOKEN" | jq '.'
   ```

5. **Verify Case-Insensitive Search**
   - Search should match regardless of case (ILIKE)

**Expected Results:**
- ✅ API returns 200 OK
- ✅ Search finds matching employees
- ✅ Partial match works (substring)
- ✅ Case-insensitive search works
- ✅ UTF-8 characters handled correctly

**Test Result:** [ ] Pass  [ ] Fail

---

### Scenario 8: Search with Filters and Pagination

**Objective:** Verify advanced search with multiple filters

**Test Steps:**

1. **Search by Department**
   ```bash
   curl -X GET "https://staging-api.example.com/api/employees/search?department_code=7410" \
     -H "Authorization: Bearer $ADMIN_TOKEN" | jq '.'
   ```

2. **Verify Department Filter**
   - All results should have `department_code` = "7410"

3. **Search with Pagination**
   ```bash
   # Page 1 (first 2 results)
   curl -X GET "https://staging-api.example.com/api/employees/search?skip=0&limit=2" \
     -H "Authorization: Bearer $ADMIN_TOKEN" | jq '.items | length'

   # Page 2 (next 2 results)
   curl -X GET "https://staging-api.example.com/api/employees/search?skip=2&limit=2" \
     -H "Authorization: Bearer $ADMIN_TOKEN" | jq '.items | length'
   ```

4. **Verify Pagination**
   - Page 1 returns up to 2 items
   - Page 2 returns different items (no overlap)
   - `skip` and `limit` values correct in response

**Expected Results:**
- ✅ Department filter works correctly
- ✅ Pagination returns correct page size
- ✅ No duplicate results across pages
- ✅ Response includes pagination metadata

**Test Result:** [ ] Pass  [ ] Fail

---

### Scenario 9: Get Employee by ID

**Objective:** Verify retrieving single employee

**Test Steps:**

1. **Get Employee by ID**
   ```bash
   curl -X GET "https://staging-api.example.com/api/employees/VNW0006204" \
     -H "Authorization: Bearer $ADMIN_TOKEN" | jq '.'
   ```

2. **Verify Response**
   - Status code: **200 OK**
   - Complete employee data returned

3. **Get Non-Existent Employee**
   ```bash
   curl -X GET "https://staging-api.example.com/api/employees/VNW9999999" \
     -H "Authorization: Bearer $ADMIN_TOKEN"
   ```

4. **Verify 404 Response**
   - Status code: **404 Not Found**
   - Error message indicates employee not found

**Expected Results:**
- ✅ Valid ID returns employee data
- ✅ Invalid ID returns 404
- ✅ Error message clear

**Test Result:** [ ] Pass  [ ] Fail

---

### Scenario 10: Update Employee Information

**Objective:** Verify employee update functionality

**Test Steps:**

1. **Get Current Data**
   ```bash
   curl -X GET "https://staging-api.example.com/api/employees/VNW0006204" \
     -H "Authorization: Bearer $ADMIN_TOKEN" | jq '.job_title, .salary'
   ```

2. **Update Employee**
   ```bash
   curl -X PUT "https://staging-api.example.com/api/employees/VNW0006204" \
     -H "Authorization: Bearer $ADMIN_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "job_title": "Senior Software Engineer",
       "salary": 9500000,
       "phone1": "0912345678"
     }' | jq '.'
   ```

3. **Verify Update Response**
   - Status code: **200 OK**
   - Response shows updated values:
     - `job_title`: "Senior Software Engineer"
     - `salary`: 9500000
     - `phone1`: "0912345678"
   - Other fields unchanged

4. **Verify Update Persisted**
   ```bash
   curl -X GET "https://staging-api.example.com/api/employees/VNW0006204" \
     -H "Authorization: Bearer $ADMIN_TOKEN" | jq '.job_title, .salary, .phone1'
   ```

5. **Verify in Database**
   ```sql
   SELECT job_title, salary, phone1, updated_at
   FROM employees
   WHERE id = 'VNW0006204';
   ```
   - `updated_at` timestamp should be recent

**Expected Results:**
- ✅ Update successful (200 OK)
- ✅ Only specified fields updated
- ✅ Other fields unchanged
- ✅ Update persisted to database
- ✅ `updated_at` timestamp updated

**Test Result:** [ ] Pass  [ ] Fail

---

### Scenario 11: Delete Employee

**Objective:** Verify employee deletion

**Test Steps:**

1. **Create Test Employee**
   ```bash
   curl -X POST "https://staging-api.example.com/api/employees/sync" \
     -H "Authorization: Bearer $ADMIN_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"emp_id": 6205, "source": "hrs"}'
   ```

2. **Verify Employee Exists**
   ```bash
   curl -X GET "https://staging-api.example.com/api/employees/VNW0006205" \
     -H "Authorization: Bearer $ADMIN_TOKEN"
   # Should return 200 OK
   ```

3. **Delete Employee**
   ```bash
   curl -X DELETE "https://staging-api.example.com/api/employees/VNW0006205" \
     -H "Authorization: Bearer $ADMIN_TOKEN" | jq '.'
   ```

4. **Verify Delete Response**
   - Status code: **200 OK**
   - Response: `{"success": true, "message": "Employee VNW0006205 deleted"}`

5. **Verify Employee Deleted**
   ```bash
   curl -X GET "https://staging-api.example.com/api/employees/VNW0006205" \
     -H "Authorization: Bearer $ADMIN_TOKEN"
   # Should return 404 Not Found
   ```

6. **Verify in Database**
   ```sql
   SELECT * FROM employees WHERE id = 'VNW0006205';
   # Should return 0 rows
   ```

7. **Delete Non-Existent Employee**
   ```bash
   curl -X DELETE "https://staging-api.example.com/api/employees/VNW9999999" \
     -H "Authorization: Bearer $ADMIN_TOKEN" | jq '.'
   ```

8. **Verify Not Found Response**
   - Status code: **200 OK**
   - Response: `{"success": false, "message": "Employee VNW9999999 not found"}`

**Expected Results:**
- ✅ Delete existing employee successful
- ✅ Employee no longer accessible via API
- ✅ Employee removed from database
- ✅ Delete non-existent returns success=false (not error)

**Test Result:** [ ] Pass  [ ] Fail

---

### Scenario 12: Authorization - Non-Admin Access

**Objective:** Verify non-admin users cannot access employee endpoints

**Test Steps:**

1. **Get Non-Admin Token**
   - Login as regular user (non-admin)
   - Extract JWT token

2. **Attempt Employee Sync as Non-Admin**
   ```bash
   curl -X POST "https://staging-api.example.com/api/employees/sync" \
     -H "Authorization: Bearer $NON_ADMIN_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"emp_id": 6204, "source": "hrs"}'
   ```

3. **Verify 403 Forbidden**
   - Status code: **403 Forbidden**
   - Error message: "Admin role required" (or similar)

4. **Test All Endpoints with Non-Admin Token**
   - POST /sync → 403
   - POST /bulk-sync → 403
   - GET /search → 403
   - GET /{emp_id} → 403
   - PUT /{emp_id} → 403
   - DELETE /{emp_id} → 403

**Expected Results:**
- ✅ All employee endpoints require admin role
- ✅ Non-admin access returns 403 Forbidden
- ✅ Error message indicates permission issue

**Test Result:** [ ] Pass  [ ] Fail

---

### Scenario 13: Performance - Bulk Sync 100 Employees

**Objective:** Verify performance with larger batch

**Test Steps:**

1. **Bulk Sync 100 Employees**
   ```bash
   # Record start time
   START_TIME=$(date +%s)

   curl -X POST "https://staging-api.example.com/api/employees/bulk-sync" \
     -H "Authorization: Bearer $ADMIN_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "from_id": 6200,
       "to_id": 6299,
       "source": "hrs"
     }' | jq '.'

   # Record end time
   END_TIME=$(date +%s)
   DURATION=$((END_TIME - START_TIME))
   echo "Duration: $DURATION seconds"
   ```

2. **Verify Summary**
   - Total: 100
   - Success rate: > 80%
   - Errors documented for failed employees

3. **Check Database**
   ```sql
   SELECT COUNT(*) FROM employees
   WHERE id BETWEEN 'VNW0006200' AND 'VNW0006299';
   ```

**Performance Targets:**
- ✅ Duration < 180 seconds (3 minutes)
- ✅ Success rate > 80%
- ✅ No API timeout errors
- ✅ Database has all successful employees

**Test Result:** [ ] Pass  [ ] Fail

**Actual Duration:** _______ seconds

**Success Rate:** _______ %

---

### Scenario 14: UTF-8 Character Handling

**Objective:** Verify Chinese and Vietnamese characters handled correctly

**Test Steps:**

1. **Sync Employee with Chinese Name**
   - Use employee with Chinese characters (e.g., 陳玉俊)

2. **Verify Chinese Characters**
   ```bash
   curl -X GET "https://staging-api.example.com/api/employees/VNW0006204" \
     -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.name_tw'
   ```
   - Chinese characters should display correctly (not garbled)

3. **Search with Chinese Characters**
   ```bash
   curl -X GET "https://staging-api.example.com/api/employees/search?name=陳玉" \
     -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.items[0].name_tw'
   ```

4. **Verify Vietnamese Characters**
   ```bash
   curl -X GET "https://staging-api.example.com/api/employees/VNW0006204" \
     -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.name_en'
   ```
   - Vietnamese characters (Ấ, Ế, Ô, etc.) should display correctly

5. **Check Database Encoding**
   ```sql
   SELECT name_tw, name_en FROM employees WHERE id = 'VNW0006204';
   ```
   - Characters should display correctly in database client

**Expected Results:**
- ✅ Chinese characters preserved and displayed correctly
- ✅ Vietnamese characters preserved and displayed correctly
- ✅ No encoding issues in API responses
- ✅ Database stores UTF-8 correctly

**Test Result:** [ ] Pass  [ ] Fail

---

## Edge Cases and Error Scenarios

### Edge Case 1: Very Long Names

Test with employee having very long name (> 100 characters).

**Expected:** Handle gracefully or truncate.

### Edge Case 2: Special Characters in Names

Test with names containing special characters: `', ", -, .`

**Expected:** Characters properly escaped, no SQL injection.

### Edge Case 3: Concurrent Updates

Two admins update same employee simultaneously.

**Expected:** Last write wins, no data corruption.

### Edge Case 4: External API Timeout

Simulate HRS/COVID API being slow or down.

**Expected:** Graceful timeout, error message returned.

### Edge Case 5: Database Connection Lost

Simulate database connection loss during operation.

**Expected:** Proper error handling, rollback if in transaction.

---

## Test Summary

### Test Execution Checklist

- [ ] Scenario 1: Sync single (HRS)
- [ ] Scenario 2: Sync single (COVID)
- [ ] Scenario 3: COVID without token
- [ ] Scenario 4: Non-existent employee
- [ ] Scenario 5: Bulk sync (11 employees)
- [ ] Scenario 6: Invalid bulk range
- [ ] Scenario 7: Search by name
- [ ] Scenario 8: Search with filters/pagination
- [ ] Scenario 9: Get by ID
- [ ] Scenario 10: Update employee
- [ ] Scenario 11: Delete employee
- [ ] Scenario 12: Non-admin access
- [ ] Scenario 13: Bulk sync 100 employees
- [ ] Scenario 14: UTF-8 characters

### Results Summary

**Total Scenarios:** 14

**Passed:** _____ / 14

**Failed:** _____ / 14

**Blocked:** _____ / 14

### Critical Issues Found

| Issue # | Scenario | Description | Severity | Status |
|---------|----------|-------------|----------|--------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

### Performance Metrics

| Operation | Target | Actual | Pass/Fail |
|-----------|--------|--------|-----------|
| Sync single employee | < 2s | | |
| Bulk sync 11 employees | < 30s | | |
| Bulk sync 100 employees | < 180s | | |
| Search (no results) | < 500ms | | |
| Search (with results) | < 500ms | | |
| Get by ID | < 200ms | | |
| Update employee | < 200ms | | |
| Delete employee | < 200ms | | |

---

## Sign-Off

**Tester Name:** _______________________

**Test Date:** _______________________

**Environment:** _______________________

**Result:** [ ] Approved for Production  [ ] Needs Fixes

**Comments:**
_____________________________________________
_____________________________________________
_____________________________________________

---

## Related Documentation

- [API Usage Guide](./employee-api-guide.md) - API endpoint documentation
- [Deployment Guide](./employee-deployment.md) - Deployment procedures

---

## Appendix: SQL Verification Queries

### Check Employee Count
```sql
SELECT COUNT(*) as total_employees FROM employees;
```

### Check Recent Employees
```sql
SELECT id, name_tw, name_en, department_code, created_at
FROM employees
ORDER BY created_at DESC
LIMIT 10;
```

### Check Employees by Department
```sql
SELECT department_code, COUNT(*) as count
FROM employees
GROUP BY department_code
ORDER BY count DESC;
```

### Check for Duplicate Identity Numbers
```sql
SELECT identity_number, COUNT(*) as count
FROM employees
WHERE identity_number IS NOT NULL
GROUP BY identity_number
HAVING COUNT(*) > 1;
```

### Check Salary Distribution
```sql
SELECT
  MIN(salary) as min_salary,
  MAX(salary) as max_salary,
  AVG(salary) as avg_salary,
  COUNT(*) as employees_with_salary
FROM employees
WHERE salary IS NOT NULL;
```

### Check Data Completeness
```sql
SELECT
  COUNT(*) as total,
  COUNT(name_tw) as has_name_tw,
  COUNT(name_en) as has_name_en,
  COUNT(identity_number) as has_identity_number,
  COUNT(salary) as has_salary
FROM employees;
```
