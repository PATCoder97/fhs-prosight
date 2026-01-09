---
name: salary-info-api
description: API endpoints for viewing employee salary and HRS data (payroll, bonuses, evaluations) with real-time queries from FHS HRS API
status: backlog
created: 2026-01-09T09:43:26Z
---

# PRD: Salary Info API

## Executive Summary

Build a REST API system for employees to view their salary information and other HRS data (quarterly bonuses, Tet bonuses, annual evaluations) by querying FHS HRS API in real-time. The system provides read-only access with optimized response structure (summary + detailed breakdown by income/deductions). No database storage required - all data fetched on-demand from HRS API.

**Value Proposition:**
- Employees can self-service view their salary details anytime
- Transparent salary breakdown (income, deductions, net pay)
- Foundation for future HRS data features (bonuses, evaluations)
- Minimal infrastructure (no DB, just API pass-through)

---

## Problem Statement

### Current Pain Points
1. **No Self-Service Access:** Employees cannot view their salary information online, must request from HR
2. **Lack of Transparency:** Employees don't understand salary breakdown (why is net pay X?)
3. **Manual Processes:** HR spends time answering salary inquiries
4. **Data Silos:** HRS API exists but not exposed to employees

### Why Now?
- Employee sync feature (#sync-employee-info) is complete
- HRS API integration client already implemented
- OAuth authentication system in place
- Demand from employees for salary transparency

### Target Users
- **Primary:** Regular employees (role: "user") - view their own salary
- **Secondary:** Admin users - can view any employee's salary (for HR support)

---

## User Stories

### Employee (Primary User)

**Story 1: View Current Month Salary**
```
As an employee,
I want to view my current month's salary details,
So that I can see my expected pay and understand the breakdown.
```

**Acceptance Criteria:**
- Can call GET `/api/hrs-data/salary` without params → returns current month
- Response shows summary: total income, total deductions, net pay
- Response shows detailed breakdown: income items (basic salary, bonuses, allowances)
- Response shows detailed breakdown: deduction items (insurance, taxes, dorm fees)
- All amounts in VND (integer)
- UTF-8 support for Vietnamese field names

**Story 2: View Specific Month Salary**
```
As an employee,
I want to view my salary for a specific month (e.g., December 2024),
So that I can review past salary or prepare tax documents.
```

**Acceptance Criteria:**
- Can call GET `/api/hrs-data/salary?year=2024&month=12`
- System validates year/month (1-12, reasonable year range)
- Returns 404 if salary data not found for that month
- Same response structure as Story 1

**Story 3: View Salary History with Trend**
```
As an employee,
I want to view my salary history for multiple months,
So that I can see trends (increases/decreases) over time.
```

**Acceptance Criteria:**
- Can call GET `/api/hrs-data/salary?year=2024` → returns all 12 months of 2024
- Response includes array of monthly salary data
- Response includes trend analysis: month-over-month changes
- Performance: < 5 seconds for 12 months (12 API calls to HRS)

**Story 4: Understand Why Salary Changed**
```
As an employee,
I want to see why my salary changed from last month,
So that I can understand fluctuations (e.g., bonus added, deduction changed).
```

**Acceptance Criteria:**
- Trend analysis shows which fields increased/decreased
- Clear labeling of changes (e.g., "Thưởng năng suất +500,000")
- Percentage change shown for major fields

### Admin (Secondary User)

**Story 5: View Any Employee's Salary (Support)**
```
As an admin,
I want to view any employee's salary details,
So that I can help them understand their payroll or troubleshoot issues.
```

**Acceptance Criteria:**
- Can call GET `/api/hrs-data/salary/{employee_id}?year=2024&month=12`
- Admin can specify any employee_id
- Same response structure as employee view
- Audit log: admin access recorded

---

## Requirements

### Functional Requirements

#### FR1: Salary Query API
- **Endpoint:** `GET /api/hrs-data/salary`
- **Authentication:** Required (JWT)
- **Authorization:**
  - Regular user: can only query their own salary (emp_id from JWT)
  - Admin: can query any employee's salary (specify emp_id in path or query)
- **Query Parameters:**
  - `year` (optional, default: current year): YYYY format
  - `month` (optional, default: current month): 1-12
  - `employee_id` (optional, admin only): Employee ID to query
- **Response Format:**
  ```json
  {
    "employee_id": "VNW0006204",
    "employee_name": "Phan Anh Tuấn",
    "period": {
      "year": 2024,
      "month": 12
    },
    "summary": {
      "tong_tien_cong": 15000000,
      "tong_tien_tru": 3331510,
      "thuc_linh": 11668490
    },
    "income": {
      "luong_co_ban": 7205600,
      "thuong_nang_suat": 2000000,
      "thuong_tet": 0,
      "tro_cap_com": 660000,
      "tro_cap_di_lai": 500000,
      "thuong_chuyen_can": 200000,
      "phu_cap_truc_ban": 0,
      "phu_cap_ngon_ngu": 0,
      "phu_cap_dac_biet": 0,
      "phu_cap_chuyen_nganh": 0,
      "phu_cap_tac_nghiep": 0,
      "phu_cap_khu_vuc": 0,
      "phu_cap_tc_dot_xuat": 0,
      "phu_cap_ngay_nghi": 0,
      "phu_cap_tc_khan_cap": 0,
      "phu_cap_chuc_vu": 0,
      "tro_cap_phong": 0,
      "phat_bu": 0,
      "thuong_cong_viec": 0,
      "phi_khac": 0,
      "cong": 22.0,
      "tien_dong_phuc": 0,
      "tro_cap_com2": 0,
      "tro_cap_dt": 0,
      "tro_cap_nghi": 0,
      "phu_cap_tc_le": 0,
      "phu_cap_ca": 0,
      "phu_cap_tc2": 0,
      "phu_cap_nghi2": 0,
      "phu_cap_tc_kc": 0,
      "phu_cap_tc_dem": 0
    },
    "deductions": {
      "bhxh": 1032448,
      "bh_that_nghiep": 129056,
      "bhyt": 193584,
      "ky_tuc_xa": 1937822,
      "tien_com": 0,
      "dong_phuc": 0,
      "cong_doan": 38600,
      "khac": 0,
      "nghi_phep": 0,
      "thue_thu_nhap": 0
    }
  }
  ```

#### FR2: Salary History API
- **Endpoint:** `GET /api/hrs-data/salary/history`
- **Query Parameters:**
  - `year` (optional, default: current year): Get all 12 months
  - `from_month` (optional): Start month (1-12)
  - `to_month` (optional): End month (1-12)
- **Response Format:**
  ```json
  {
    "employee_id": "VNW0006204",
    "employee_name": "Phan Anh Tuấn",
    "period": {
      "year": 2024,
      "from_month": 1,
      "to_month": 12
    },
    "months": [
      {
        "month": 1,
        "summary": { ... },
        "income": { ... },
        "deductions": { ... }
      },
      // ... 11 more months
    ],
    "trend": {
      "average_income": 14500000,
      "average_deductions": 3200000,
      "average_net": 11300000,
      "highest_month": { "month": 12, "net": 15000000 },
      "lowest_month": { "month": 2, "net": 10000000 },
      "changes": [
        {
          "from_month": 11,
          "to_month": 12,
          "field": "thuong_nang_suat",
          "change": 500000,
          "percentage": 25.0,
          "direction": "increase"
        }
      ]
    }
  }
  ```

#### FR3: Admin Query Any Employee
- **Endpoint:** `GET /api/hrs-data/salary/{employee_id}`
- **Authorization:** Admin only
- **Path Parameters:**
  - `employee_id`: Employee ID to query (e.g., "VNW0006204" or just "6204")
- **Query Parameters:** Same as FR1 (year, month)
- **Response:** Same structure as FR1

#### FR4: Error Handling
- **HRS API Down/Timeout:**
  - Return 503 Service Unavailable
  - Error message: "Hệ thống HRS tạm thời không khả dụng. Vui lòng thử lại sau."
- **Employee Not Found in HRS:**
  - Return 404 Not Found
  - Error message: "Không tìm thấy dữ liệu lương cho nhân viên {emp_id} tháng {year}-{month}"
- **Invalid Month/Year:**
  - Return 422 Validation Error
  - Error message: "Tháng phải từ 1-12, năm phải từ 2020-2030"
- **Unauthorized Access:**
  - Return 403 Forbidden
  - Error message: "Bạn không có quyền xem lương của nhân viên này"

### Non-Functional Requirements

#### NFR1: Performance
- **Single Month Query:** < 2 seconds (1 HRS API call)
- **Multi-Month Query (12 months):** < 5 seconds (12 parallel HRS API calls)
- **Concurrent Requests:** Support 100 concurrent users

#### NFR2: Security
- **Authentication:** JWT token required for all endpoints
- **Authorization:**
  - User can only view their own salary (emp_id from JWT token)
  - Admin can view any employee's salary
- **No Data Storage:** Salary data NOT stored in database (security best practice)
- **Audit Logging:** Log all salary queries (who, when, which employee) for compliance

#### NFR3: Availability
- **Dependency:** FHS HRS API availability (external dependency)
- **Graceful Degradation:** If HRS API fails, return clear error message
- **No Retry Logic:** Don't retry failed HRS API calls (avoid cascading delays)

#### NFR4: Data Accuracy
- **Real-Time:** Always fetch fresh data from HRS API
- **No Caching:** Do NOT cache salary data (privacy + accuracy)
- **Field Validation:** Validate HRS API response has 45+ fields before parsing

---

## Success Criteria

### Measurable Outcomes

1. **Adoption Rate:**
   - Target: 70% of employees view their salary within first month
   - Measure: Track unique users calling salary endpoints

2. **Reduced HR Inquiries:**
   - Target: 50% reduction in salary-related questions to HR
   - Measure: Track HR ticket volume before/after

3. **API Performance:**
   - Target: 95% of requests complete within 2 seconds (single month)
   - Measure: Monitor API response times (p95)

4. **Error Rate:**
   - Target: < 1% of requests return errors (excluding HRS API downtime)
   - Measure: Track 4xx/5xx error rates

5. **User Satisfaction:**
   - Target: 80% satisfaction score for salary transparency
   - Measure: User survey after 1 month

### Key Metrics (KPIs)

- **Daily Active Users:** Track daily salary queries
- **HRS API Uptime:** Monitor external dependency
- **Response Time:** Track p50, p95, p99 latency
- **Error Rate:** Track by error type (403, 404, 503)
- **Data Completeness:** % of responses with all 45+ fields parsed correctly

---

## Constraints & Assumptions

### Technical Constraints
1. **HRS API Dependency:** Cannot function if HRS API is down (external dependency)
2. **No Caching:** Cannot cache salary data (security requirement)
3. **HRS API Rate Limits:** Unknown if HRS API has rate limits (need to monitor)
4. **Response Format:** Locked to HRS API's pipe-delimited format (45+ fields)

### Business Constraints
1. **No Historical Storage:** Cannot query salary data older than HRS API retains
2. **Real-Time Only:** Cannot provide salary projections or estimates

### Assumptions
1. HRS API returns salary data for at least 12 months of history
2. HRS API response format (pipe-delimited, 45 fields) remains stable
3. Employee ID format remains VNW00XXXXX
4. JWT tokens include employee_id claim for authorization
5. Employees have basic understanding of salary components (no explanation feature in v1)

---

## Out of Scope

**Explicitly NOT building in this version:**

1. **Salary Data Storage:** No database table for salary records
2. **Salary PDF Export:** No download payslip as PDF (may add in v2)
3. **Salary Comparison with Peers:** No anonymized salary benchmarking
4. **Salary Projections:** No "what if" calculations or future estimates
5. **Salary Notifications:** No alerts for salary changes or payment dates
6. **Mobile App:** API only, no dedicated mobile app
7. **Offline Access:** Cannot view salary without internet (real-time only)
8. **Salary Edits:** Read-only, cannot modify salary data via API
9. **Multi-Currency:** VND only, no foreign currency support
10. **Quarterly Bonuses/Tet Bonuses/Annual Evaluations:** Separate endpoints (future features under `/api/hrs-data/`)

---

## Dependencies

### External Dependencies
1. **FHS HRS API:**
   - URL: `https://www.fhs.com.tw/ads/api/Furnace/rest/json/hr`
   - Endpoint: `s16/{employee_id}vkokv{year}-{month}`
   - Authentication: None (internal network)
   - Availability: Unknown SLA

2. **HRS Client:**
   - Already implemented: `FHSHRSClient.get_salary_data(emp_id, year, month)`
   - Returns parsed dictionary with 45+ salary fields
   - Returns None on error (404, timeout, invalid format)

### Internal Dependencies
1. **Employee Sync Feature (#sync-employee-info):**
   - Need employee_id → name mapping
   - Use existing Employee model for name lookup

2. **Authentication System:**
   - JWT token with employee_id claim
   - OAuth login (Google/GitHub)
   - Role-based authorization (user, admin)

3. **Utility Functions:**
   - `parse_number()`: Parse numbers with commas
   - `first_block()`: Extract first block from HRS response

---

## Technical Approach

### Router Structure
**File:** `backend/app/routers/hrs_data.py`

**Endpoints:**
1. `GET /api/hrs-data/salary` - Get own salary (current month or specific month)
2. `GET /api/hrs-data/salary/history` - Get salary history with trend
3. `GET /api/hrs-data/salary/{employee_id}` - Admin: Get any employee's salary

**Future Endpoints (out of scope for v1):**
- `GET /api/hrs-data/bonus/quarterly` - Quarterly bonuses
- `GET /api/hrs-data/bonus/tet` - Tet bonuses
- `GET /api/hrs-data/evaluation/annual` - Annual performance evaluations

### Service Layer
**File:** `backend/app/services/hrs_data_service.py`

**Methods:**
1. `get_employee_salary(db, emp_id, year, month)` → SalaryResponse
   - Call `hrs_client.get_salary_data(emp_id, year, month)`
   - Transform to structured response (summary + income + deductions)
   - Calculate totals: `tong_tien_cong`, `tong_tien_tru`, `thuc_linh`
   - Lookup employee name from Employee model

2. `get_salary_history(db, emp_id, year, from_month, to_month)` → SalaryHistoryResponse
   - Call `get_employee_salary()` for each month in range
   - Parallelize API calls using `asyncio.gather()`
   - Calculate trend: average, highest, lowest, month-over-month changes
   - Return array of monthly data + trend analysis

3. `calculate_trend(monthly_data)` → TrendAnalysis
   - Compute average income/deductions/net
   - Find highest/lowest months
   - Detect significant changes (> 10% or > 500,000 VND)
   - Return structured trend object

### Response Optimization

**Current Implementation (your code):**
```python
return {
    "tien_phat_thuc_te": _parse_number(fields[43]),
    "tong_tien_cong": _parse_number(fields[32]),
    # ... 43 more fields
}
```

**Optimized Implementation:**
```python
def _parse_salary_response(fields: List[str]) -> dict:
    """Parse HRS salary response into structured format"""

    # Parse all income fields
    income = {
        "luong_co_ban": _parse_number(fields[44]),
        "thuong_nang_suat": _parse_number(fields[2]),
        "thuong_tet": _parse_number(fields[3]),
        # ... all income fields
    }

    # Parse all deduction fields
    deductions = {
        "bhxh": _parse_number(fields[33]),
        "bh_that_nghiep": _parse_number(fields[34]),
        "bhyt": _parse_number(fields[35]),
        # ... all deduction fields
    }

    # Calculate totals
    tong_tien_cong = _parse_number(fields[32])
    tong_tien_tru = sum(deductions.values())
    thuc_linh = _parse_number(fields[43])

    # Verify calculation (sanity check)
    expected_net = tong_tien_cong - tong_tien_tru
    if abs(expected_net - thuc_linh) > 100:  # Allow 100 VND rounding error
        logger.warning(
            f"Salary calculation mismatch: expected {expected_net}, got {thuc_linh}"
        )

    return {
        "summary": {
            "tong_tien_cong": tong_tien_cong,
            "tong_tien_tru": tong_tien_tru,
            "thuc_linh": thuc_linh
        },
        "income": income,
        "deductions": deductions
    }
```

### Schemas
**File:** `backend/app/schemas/hrs_data.py`

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date

# Summary
class SalarySummary(BaseModel):
    tong_tien_cong: int = Field(..., description="Total income (VND)")
    tong_tien_tru: int = Field(..., description="Total deductions (VND)")
    thuc_linh: int = Field(..., description="Net pay (VND)")

# Income breakdown
class SalaryIncome(BaseModel):
    luong_co_ban: int = Field(0, description="Basic salary")
    thuong_nang_suat: int = Field(0, description="Productivity bonus")
    thuong_tet: int = Field(0, description="Tet bonus")
    tro_cap_com: int = Field(0, description="Meal allowance")
    # ... all 32 income fields

# Deductions breakdown
class SalaryDeductions(BaseModel):
    bhxh: int = Field(0, description="Social insurance")
    bh_that_nghiep: int = Field(0, description="Unemployment insurance")
    bhyt: int = Field(0, description="Health insurance")
    ky_tuc_xa: int = Field(0, description="Dormitory fees")
    # ... all 10 deduction fields

# Period
class SalaryPeriod(BaseModel):
    year: int = Field(..., ge=2020, le=2030)
    month: int = Field(..., ge=1, le=12)

# Single month response
class SalaryResponse(BaseModel):
    employee_id: str
    employee_name: str
    period: SalaryPeriod
    summary: SalarySummary
    income: SalaryIncome
    deductions: SalaryDeductions

# Monthly data for history
class MonthlySalary(BaseModel):
    month: int
    summary: SalarySummary
    income: SalaryIncome
    deductions: SalaryDeductions

# Trend change
class SalaryChange(BaseModel):
    from_month: int
    to_month: int
    field: str
    change: int
    percentage: float
    direction: str  # "increase" or "decrease"

# Trend analysis
class SalaryTrend(BaseModel):
    average_income: int
    average_deductions: int
    average_net: int
    highest_month: dict  # {"month": 12, "net": 15000000}
    lowest_month: dict
    changes: List[SalaryChange]

# History response
class SalaryHistoryResponse(BaseModel):
    employee_id: str
    employee_name: str
    period: dict  # {"year": 2024, "from_month": 1, "to_month": 12}
    months: List[MonthlySalary]
    trend: SalaryTrend
```

### Authorization Logic

```python
def get_current_employee_id(current_user: dict) -> str:
    """Extract employee_id from JWT token"""
    # Assuming JWT has localId or employee_id claim
    return current_user.get("localId") or current_user.get("employee_id")

def can_view_salary(current_user: dict, target_emp_id: str) -> bool:
    """Check if user can view target employee's salary"""
    # Admin can view any
    if current_user.get("role") == "admin":
        return True

    # User can only view their own
    current_emp_id = get_current_employee_id(current_user)
    return current_emp_id == target_emp_id
```

---

## Implementation Phases

### Phase 1: Core Salary Query (MVP)
**Scope:** Single month salary query for own employee

**Tasks:**
1. Create `hrs_data.py` router with GET `/api/hrs-data/salary`
2. Create `hrs_data_service.py` with `get_employee_salary()`
3. Optimize `get_salary_data()` in HRS client to return structured response
4. Create Pydantic schemas (SalaryResponse, SalarySummary, Income, Deductions)
5. Implement authorization (user can only view own salary)
6. Add error handling (503, 404, 403, 422)
7. Unit tests for service layer
8. Integration tests for API endpoint

**Estimated Effort:** 1-2 days

### Phase 2: Salary History & Trend
**Scope:** Multi-month query with trend analysis

**Tasks:**
1. Add GET `/api/hrs-data/salary/history`
2. Implement `get_salary_history()` with parallel API calls
3. Implement `calculate_trend()` for trend analysis
4. Create SalaryHistoryResponse schema
5. Performance optimization (parallel queries, timeout handling)
6. Tests for history and trend calculation

**Estimated Effort:** 1 day

### Phase 3: Admin Query
**Scope:** Admin can view any employee's salary

**Tasks:**
1. Add GET `/api/hrs-data/salary/{employee_id}`
2. Implement admin authorization check
3. Add audit logging for admin queries
4. Tests for admin access

**Estimated Effort:** 0.5 days

### Phase 4: Documentation & Deployment
**Scope:** Production-ready documentation

**Tasks:**
1. API usage guide (similar to employee-api-guide.md)
2. Update deployment guide
3. E2E test plan
4. Performance testing (load test with 100 concurrent users)

**Estimated Effort:** 0.5 days

**Total Estimated Effort:** 4-5 days

---

## Future Enhancements (Backlog)

1. **Quarterly Bonuses API:** GET `/api/hrs-data/bonus/quarterly?year=2024&quarter=4`
2. **Tet Bonuses API:** GET `/api/hrs-data/bonus/tet?year=2024`
3. **Annual Performance Evaluations:** GET `/api/hrs-data/evaluation/annual?year=2024`
4. **Salary PDF Export:** GET `/api/hrs-data/salary/pdf?year=2024&month=12` → Download payslip
5. **Salary Notifications:** Email when salary is paid or changes
6. **Salary Comparison:** Anonymized benchmarking within department/company
7. **Caching Layer:** Redis cache for 1 hour to reduce HRS API load
8. **WebSocket Real-Time:** Push salary updates when HRS publishes new data

---

## Risk Assessment

### High Risks

1. **HRS API Downtime:**
   - **Impact:** Users cannot view salary
   - **Mitigation:** Clear error messages, retry suggestions, monitor HRS API uptime
   - **Probability:** Medium (external dependency)

2. **HRS API Format Changes:**
   - **Impact:** Parsing breaks, all requests fail
   - **Mitigation:** Field validation, comprehensive error handling, alerting on parse failures
   - **Probability:** Low (stable API)

### Medium Risks

3. **Performance with 12-Month Queries:**
   - **Impact:** Slow response times, user frustration
   - **Mitigation:** Parallel API calls, timeout limits, consider caching in future
   - **Probability:** Medium

4. **Privacy Concerns:**
   - **Impact:** Salary data exposed to wrong users
   - **Mitigation:** Strict authorization checks, audit logging, no data storage
   - **Probability:** Low (with proper auth)

### Low Risks

5. **HRS API Rate Limits:**
   - **Impact:** API calls rejected
   - **Mitigation:** Monitor for rate limit errors, implement backoff if needed
   - **Probability:** Low (internal API, likely no limits)

---

## Open Questions

1. **HRS API SLA:** What is the uptime guarantee for FHS HRS API?
2. **Data Retention:** How many months of salary history does HRS API retain?
3. **Rate Limits:** Does HRS API have rate limits? What are they?
4. **Field Definitions:** Can we get official documentation of all 45 salary fields?
5. **Rounding Rules:** How does HRS calculate rounding (tong_tien_cong - tong_tien_tru ≠ thuc_linh)?
6. **Future Fields:** Will HRS API add new fields? How will we handle backward compatibility?
7. **Employee ID Format:** Will VNW00XXXXX format change in future?

---

## Appendix

### A. HRS API Response Example

**Endpoint:** `s16/VNW0006204vkokv2024-12`

**Raw Response:**
```
field1|field2|2000000|0|660000|500000|200000|0|0|0|0|0|0|0|0|0|0|0|0|0|0|22|0|0|0|0|0|0|0|0|0|0|15000000|1032448|129056|193584|1937822|0|0|38600|0|0|0|11668490|7205600
```

**Parsed Fields (45 total):**
- fields[0-1]: Unknown/metadata
- fields[2]: Thưởng năng suất (2,000,000)
- fields[3]: Thưởng Tết (0)
- fields[4-31]: Income fields (allowances, bonuses)
- fields[32]: Tổng tiền công (15,000,000)
- fields[33-42]: Deduction fields (insurance, taxes, fees)
- fields[43]: Thực lĩnh (11,668,490)
- fields[44]: Lương cơ bản (7,205,600)

### B. Field Mapping Reference

**Income Fields (32 fields):**
| Field Index | Vietnamese Name | English Name |
|-------------|-----------------|--------------|
| 44 | Lương cơ bản | Basic salary |
| 2 | Thưởng năng suất | Productivity bonus |
| 3 | Thưởng Tết | Tet bonus |
| 4 | Trợ cấp cơm | Meal allowance |
| 5 | Trợ cấp đi lại | Transportation allowance |
| 6 | Thưởng chuyên cần | Attendance bonus |
| 7-31 | Various allowances | Various allowances |

**Deduction Fields (10 fields):**
| Field Index | Vietnamese Name | English Name |
|-------------|-----------------|--------------|
| 33 | BHXH | Social insurance |
| 34 | BH thất nghiệp | Unemployment insurance |
| 35 | BHYT | Health insurance |
| 36 | Ký túc xá | Dormitory fees |
| 37 | Tiền cơm | Meal fees |
| 38 | Đồng phục | Uniform fees |
| 39 | Công đoàn | Union fees |
| 40 | Khác | Other deductions |
| 41 | Nghỉ phép | Leave deductions |
| 42 | Thuế thu nhập | Income tax |

### C. Sample API Responses

**GET /api/hrs-data/salary?year=2024&month=12**
```json
{
  "employee_id": "VNW0006204",
  "employee_name": "Phan Anh Tuấn",
  "period": {
    "year": 2024,
    "month": 12
  },
  "summary": {
    "tong_tien_cong": 15000000,
    "tong_tien_tru": 3331510,
    "thuc_linh": 11668490
  },
  "income": {
    "luong_co_ban": 7205600,
    "thuong_nang_suat": 2000000,
    "thuong_tet": 0,
    "tro_cap_com": 660000,
    "tro_cap_di_lai": 500000,
    "thuong_chuyen_can": 200000,
    "phu_cap_truc_ban": 0,
    "cong": 22.0
  },
  "deductions": {
    "bhxh": 1032448,
    "bh_that_nghiep": 129056,
    "bhyt": 193584,
    "ky_tuc_xa": 1937822,
    "cong_doan": 38600,
    "thue_thu_nhap": 0
  }
}
```

---

## Sign-Off

**Product Manager:** [Your Name]
**Date:** 2026-01-09

**Reviewers:**
- [ ] Engineering Lead
- [ ] Security Team
- [ ] HR Department
- [ ] Legal/Compliance
