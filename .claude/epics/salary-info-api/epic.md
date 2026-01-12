---
name: salary-info-api
status: completed
created: 2026-01-09T09:53:53Z
progress: 100%
prd: .claude/prds/salary-info-api.md
github: https://github.com/PATCoder97/fhs-prosight/issues/19
---

# Epic: Salary Info API

## Overview

Implement read-only API endpoints for employees to view salary information by querying FHS HRS API in real-time. System provides optimized response structure (summary + income + deductions breakdown) with no database storage required. Built on router pattern `/api/hrs-data/` to accommodate future HRS features (bonuses, evaluations).

**Key Components:**
- Optimize existing `get_salary_data()` in HRS client
- New service layer for salary queries and trend analysis
- 3 REST API endpoints (salary query, history, admin view)
- Pydantic schemas for structured responses
- Authorization: users view own salary, admins view any

**Leverage Existing Patterns:**
- Reuse `FHSHRSClient` (already implemented in #sync-employee-info)
- Follow same router → service → client pattern
- Use existing JWT authorization (`require_role()`)
- Similar to employee endpoints structure

---

## Architecture Decisions

### 1. **No Database Storage (Real-Time Query Only)**
**Decision:** Fetch salary data on-demand from HRS API, do NOT store in database

**Rationale:**
- **Security:** Salary data is sensitive, storing increases breach risk
- **Simplicity:** No schema design, migrations, or sync jobs needed
- **Accuracy:** Always fresh data, no stale/out-of-sync issues
- **Compliance:** Reduces data retention obligations

**Trade-offs:**
- Performance depends on HRS API availability/speed
- Cannot query salary if HRS API is down
- No offline access

**Implementation:**
- Direct pass-through from HRS API to response
- No caching layer (future enhancement if needed)
- Clear error messages when HRS unavailable

### 2. **Router Structure: `/api/hrs-data/`**
**Decision:** Create new router `hrs_data.py` instead of extending `employees.py`

**Rationale:**
- **Separation of Concerns:** Employee CRUD vs HRS data viewing are different domains
- **Future-Proof:** HRS router will include bonuses, evaluations, other HR data
- **Authorization Difference:** Employee endpoints are admin-only, salary endpoints are user-accessible
- **API Clarity:** `/api/hrs-data/salary` is more intuitive than `/api/employees/{id}/salary`

**Endpoints:**
- `GET /api/hrs-data/salary` - View own salary (current or specific month)
- `GET /api/hrs-data/salary/history` - View salary history with trend
- `GET /api/hrs-data/salary/{employee_id}` - Admin: view any employee's salary

**Future Endpoints (out of scope):**
- `GET /api/hrs-data/bonus/quarterly`
- `GET /api/hrs-data/bonus/tet`
- `GET /api/hrs-data/evaluation/annual`

### 3. **Optimized Response Structure**
**Decision:** Transform flat 45-field HRS response into structured 3-part response

**Current HRS API Response (flat):**
```python
{
  "tien_phat_thuc_te": 11668490,
  "tong_tien_cong": 15000000,
  "luong_co_ban": 7205600,
  "thuong_nang_suat": 2000000,
  # ... 41 more fields
}
```

**Optimized Response (structured):**
```json
{
  "summary": {
    "tong_tien_cong": 15000000,
    "tong_tien_tru": 3331510,
    "thuc_linh": 11668490
  },
  "income": { /* 32 income fields */ },
  "deductions": { /* 10 deduction fields */ }
}
```

**Rationale:**
- **User Experience:** Users want to see net pay first, then details
- **Frontend Flexibility:** Frontend can show summary card + expandable details
- **Validation:** Can verify `tong_tien_cong - tong_tien_tru = thuc_linh`
- **Analytics:** Easier to track which income/deduction categories are most significant

### 4. **Authorization Model**
**Decision:** Users can view own salary, admins can view any employee's salary

**Rationale:**
- **Self-Service:** Most common use case is employees checking their own pay
- **Privacy:** Employees should NOT see others' salaries (unlike admin-only employee CRUD)
- **Support:** Admins need access to help employees troubleshoot salary questions

**Implementation:**
```python
def can_view_salary(current_user: dict, target_emp_id: str) -> bool:
    if current_user["role"] == "admin":
        return True
    return current_user["localId"] == target_emp_id
```

**Endpoints:**
- `/api/hrs-data/salary` (no emp_id) → returns current user's salary
- `/api/hrs-data/salary/{employee_id}` → admin only

---

## Technical Approach

### Backend Services

#### 1. HRS Client Enhancement

**File:** `backend/app/integrations/fhs_hrs_client.py` (existing)

**Current Implementation:**
```python
async def get_salary_data(self, emp_id: int, year: int, month: int) -> Optional[dict]:
    """Returns flat dict with 45+ fields"""
```

**Enhancement Needed:**
- Keep existing method signature (backward compatible)
- Return structured response: `{"summary": {...}, "income": {...}, "deductions": {...}}`
- Add field validation (ensure 45+ fields before parsing)
- Add calculation verification (sanity check on totals)

**New Code:**
```python
def _parse_salary_response(fields: List[str]) -> dict:
    """Parse HRS salary response into structured format"""

    # Parse income fields (32 fields)
    income = {
        "luong_co_ban": _parse_number(fields[44]),
        "thuong_nang_suat": _parse_number(fields[2]),
        # ... all income fields
    }

    # Parse deduction fields (10 fields)
    deductions = {
        "bhxh": _parse_number(fields[33]),
        "bh_that_nghiep": _parse_number(fields[34]),
        # ... all deduction fields
    }

    # Calculate totals
    tong_tien_cong = _parse_number(fields[32])
    tong_tien_tru = sum(deductions.values())
    thuc_linh = _parse_number(fields[43])

    # Verify calculation
    expected_net = tong_tien_cong - tong_tien_tru
    if abs(expected_net - thuc_linh) > 100:
        logger.warning(f"Salary calc mismatch: {expected_net} vs {thuc_linh}")

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

#### 2. Service Layer

**File:** `backend/app/services/hrs_data_service.py` (new)

**Methods:**

1. **get_employee_salary(db, emp_id, year, month)**
   - Call `hrs_client.get_salary_data()`
   - Lookup employee name from Employee model
   - Return SalaryResponse with employee info + period + salary data

2. **get_salary_history(db, emp_id, year, from_month, to_month)**
   - Call `get_employee_salary()` for each month in range
   - Use `asyncio.gather()` for parallel API calls
   - Calculate trend: average, highest, lowest, significant changes
   - Return SalaryHistoryResponse with monthly data + trend

3. **calculate_trend(monthly_data)**
   - Compute averages (income, deductions, net)
   - Find highest/lowest months
   - Detect month-over-month changes > 10% or > 500K VND
   - Return TrendAnalysis object

**Example:**
```python
async def get_employee_salary(
    db: AsyncSession,
    emp_id: str,
    year: int,
    month: int
) -> dict:
    # Convert emp_id format: VNW0006204 → 6204
    emp_num = int(emp_id.replace("VNW00", ""))

    # Query HRS API
    salary_data = await hrs_client.get_salary_data(emp_num, year, month)
    if not salary_data:
        raise HTTPException(404, f"Salary not found for {emp_id} {year}-{month}")

    # Lookup employee name
    employee = await db.get(Employee, emp_id)
    emp_name = employee.name_en if employee else "Unknown"

    # Return structured response
    return {
        "employee_id": emp_id,
        "employee_name": emp_name,
        "period": {"year": year, "month": month},
        **salary_data  # summary, income, deductions
    }
```

#### 3. API Router

**File:** `backend/app/routers/hrs_data.py` (new)

**Endpoints:**

```python
router = APIRouter(prefix="/hrs-data", tags=["hrs-data"])

@router.get("/salary", response_model=SalaryResponse)
async def get_own_salary(
    year: int = Query(None),
    month: int = Query(None),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's salary for specific month or current month"""
    emp_id = current_user["localId"]

    # Default to current month
    if not year or not month:
        now = datetime.now()
        year = year or now.year
        month = month or now.month

    return await hrs_data_service.get_employee_salary(db, emp_id, year, month)


@router.get("/salary/history", response_model=SalaryHistoryResponse)
async def get_salary_history(
    year: int = Query(...),
    from_month: int = Query(1, ge=1, le=12),
    to_month: int = Query(12, ge=1, le=12),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get salary history with trend analysis"""
    emp_id = current_user["localId"]
    return await hrs_data_service.get_salary_history(
        db, emp_id, year, from_month, to_month
    )


@router.get("/salary/{employee_id}", response_model=SalaryResponse)
async def get_employee_salary_admin(
    employee_id: str,
    year: int = Query(...),
    month: int = Query(...),
    current_user: dict = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """Admin: Get any employee's salary"""
    return await hrs_data_service.get_employee_salary(
        db, employee_id, year, month
    )
```

#### 4. Pydantic Schemas

**File:** `backend/app/schemas/hrs_data.py` (new)

**Schemas:**
- `SalarySummary`: tong_tien_cong, tong_tien_tru, thuc_linh
- `SalaryIncome`: 32 income fields (luong_co_ban, thuong, phu_cap, etc.)
- `SalaryDeductions`: 10 deduction fields (bhxh, bhyt, taxes, fees, etc.)
- `SalaryPeriod`: year, month
- `SalaryResponse`: employee_id, employee_name, period, summary, income, deductions
- `MonthlySalary`: month, summary, income, deductions
- `SalaryChange`: from_month, to_month, field, change, percentage, direction
- `SalaryTrend`: average_income, average_deductions, average_net, highest, lowest, changes
- `SalaryHistoryResponse`: employee_id, employee_name, period, months[], trend

---

## Implementation Strategy

### Development Approach

**Sequential Implementation (not parallel):**
1. Enhance HRS client (optimize response structure)
2. Build service layer (salary query + trend)
3. Create API endpoints
4. Add tests
5. Documentation

**Why Sequential:**
- Tasks are dependent (service depends on client, router depends on service)
- Single developer can complete sequentially faster than parallel overhead
- Small enough scope (4-5 days) that parallelization doesn't help

### Risk Mitigation

1. **HRS API Dependency:**
   - Risk: HRS API down during development/testing
   - Mitigation: Mock HRS responses in tests, test with real API last

2. **Performance (12-Month Queries):**
   - Risk: 12 sequential API calls = slow response
   - Mitigation: Use `asyncio.gather()` for parallel calls, add timeout

3. **Field Mapping Errors:**
   - Risk: Misunderstand which field index maps to which salary component
   - Mitigation: Validate with sample employee data, cross-reference with HR

### Testing Approach

**Unit Tests:**
- Test `_parse_salary_response()` with mock field data
- Test `calculate_trend()` with sample monthly data
- Test authorization logic (`can_view_salary()`)

**Integration Tests:**
- Test each endpoint with mocked HRS client
- Test authorization (user can only view own, admin can view any)
- Test error handling (HRS down, invalid month, employee not found)

**Manual Testing:**
- Test with real HRS API (1-2 employees)
- Verify calculation: tong_tien_cong - tong_tien_tru = thuc_linh
- Verify UTF-8 encoding (Vietnamese field names)

---

## Task Breakdown Preview

### Proposed Tasks (5 tasks total)

1. **Schemas & Models** (S)
   - Create `backend/app/schemas/hrs_data.py`
   - 9 Pydantic schemas: SalarySummary, Income, Deductions, Period, Response, Monthly, Change, Trend, History
   - No database models needed (read-only from API)

2. **Enhance HRS Client** (M)
   - Optimize `get_salary_data()` in `fhs_hrs_client.py`
   - Add `_parse_salary_response()` helper
   - Transform flat response → structured (summary + income + deductions)
   - Add field validation and calculation verification
   - Backward compatible (same method signature)

3. **Service Layer** (M)
   - Create `backend/app/services/hrs_data_service.py`
   - Implement `get_employee_salary(db, emp_id, year, month)`
   - Implement `get_salary_history(db, emp_id, year, from_month, to_month)`
   - Implement `calculate_trend(monthly_data)`
   - Parallel API calls with `asyncio.gather()`

4. **API Endpoints** (M)
   - Create `backend/app/routers/hrs_data.py`
   - Implement 3 endpoints: `/salary`, `/salary/history`, `/salary/{employee_id}`
   - Authorization: user (own salary) vs admin (any employee)
   - Register router in `main.py`
   - Error handling (503, 404, 403, 422)

5. **Tests & Documentation** (M)
   - Unit tests for service layer (trend calculation, parsing)
   - Integration tests for API endpoints (auth, errors, responses)
   - API usage guide (similar to employee-api-guide.md)
   - Update deployment guide (no new migrations, just router)

**Total Estimated Effort:** 4-5 days

**Why Only 5 Tasks:**
- No database schema (no migration task)
- Reusing existing HRS client (just enhance, not build from scratch)
- Reusing existing auth system (no auth setup task)
- Simple CRUD-like pattern (no complex algorithms)

---

## Dependencies

### External Dependencies

1. **FHS HRS API:**
   - Salary endpoint: `s16/{employee_id}vkokv{year}-{month}`
   - Already validated in #sync-employee-info epic
   - Returns 45+ pipe-delimited fields

2. **Existing HRS Client:**
   - `FHSHRSClient` already implemented
   - Has `get_salary_data()` method (needs optimization)
   - Has utility functions: `_parse_number()`, `_first_block()`

### Internal Dependencies

1. **Employee Sync Feature (#sync-employee-info):**
   - ✅ Completed and merged to main
   - Need Employee model for name lookup
   - Need `localId` claim in JWT for authorization

2. **Authentication System:**
   - ✅ OAuth login (Google/GitHub)
   - ✅ JWT with `localId` and `role` claims
   - ✅ `require_role()` and `get_current_user()` dependencies

3. **Database:**
   - Need Employee table for name lookup only
   - No new tables/migrations required

### Prerequisite Work

**Must Complete Before Starting:**
1. ✅ Merge #sync-employee-info to main (DONE)
2. ✅ Verify JWT tokens include `localId` claim (DONE)
3. ✅ Test HRS API salary endpoint accessibility (validation needed)

**No Blockers:**
- All prerequisites complete or validatable quickly
- Can start implementation immediately

---

## Success Criteria (Technical)

### Performance Benchmarks

1. **Single Month Query:** < 2 seconds (p95)
   - 1 HRS API call + DB lookup + response formatting

2. **Multi-Month Query (12 months):** < 5 seconds (p95)
   - 12 parallel HRS API calls + trend calculation

3. **Concurrent Users:** Support 100 simultaneous salary queries
   - No database writes, only reads (low contention)

### Quality Gates

1. **Code Quality:**
   - All new code follows existing patterns (employee sync)
   - Pydantic schemas for all responses
   - Type hints on all methods
   - Logging for HRS API calls and errors

2. **Test Coverage:**
   - Unit tests: > 80% coverage for service layer
   - Integration tests: All 3 endpoints with auth/error cases
   - Manual test with real HRS API: 2+ employees

3. **Security:**
   - Authorization checks on all endpoints
   - Users cannot access others' salaries
   - Audit logging for admin salary queries
   - No salary data stored in database

4. **Documentation:**
   - API usage guide with cURL examples
   - OpenAPI docs generated automatically
   - Response format documented with field descriptions

### Acceptance Criteria

From PRD user stories:

1. ✅ Employee can view current month salary (`GET /salary`)
2. ✅ Employee can view specific month salary (`GET /salary?year=2024&month=12`)
3. ✅ Employee can view salary history with trend (`GET /salary/history?year=2024`)
4. ✅ Admin can view any employee's salary (`GET /salary/{employee_id}`)
5. ✅ Response shows summary (total income, deductions, net)
6. ✅ Response shows detailed income breakdown (32 fields)
7. ✅ Response shows detailed deduction breakdown (10 fields)
8. ✅ Trend analysis shows month-over-month changes
9. ✅ Error handling when HRS API down (503)
10. ✅ Error handling when salary not found (404)

---

## Estimated Effort

### Task Breakdown

| Task | Size | Estimated Hours | Dependencies |
|------|------|-----------------|--------------|
| 1. Schemas & Models | S | 2-3 hours | None |
| 2. Enhance HRS Client | M | 4-6 hours | Task 1 |
| 3. Service Layer | M | 6-8 hours | Task 2 |
| 4. API Endpoints | M | 4-6 hours | Task 3 |
| 5. Tests & Docs | M | 6-8 hours | Task 4 |

**Total:** 22-31 hours (≈ 3-4 days)

### Resource Requirements

**Developer:** 1 backend developer
- Familiar with FastAPI, Pydantic, async/await
- Knows existing codebase structure from #sync-employee-info

**Tools/Infrastructure:**
- Access to FHS HRS API (internal network)
- Staging environment for testing
- Admin JWT token for testing admin endpoints

### Critical Path

```
Schemas (3h) → HRS Client (6h) → Service (8h) → Endpoints (6h) → Tests (8h)
```

**Total Critical Path:** 31 hours (4 days)

**No Parallel Opportunities:**
- All tasks are sequential dependencies
- Single developer = no parallelization benefit

### Recommended Timeline

**Day 1:** Tasks 1-2 (Schemas + HRS Client optimization)
**Day 2:** Task 3 (Service layer with trend calculation)
**Day 3:** Task 4 (API endpoints + router registration)
**Day 4:** Task 5 (Tests + documentation)

**Buffer:** 1 day for bug fixes, edge cases, performance tuning

**Total:** 4-5 days including buffer

---

## Future Enhancements (Out of Scope)

These features are mentioned in PRD but intentionally excluded from v1:

1. **Caching Layer:**
   - Redis cache for 1 hour to reduce HRS API load
   - Would improve performance but adds complexity
   - Wait for user demand data before implementing

2. **PDF Payslip Export:**
   - Download salary as PDF (`GET /salary/pdf`)
   - Requires PDF generation library + template design
   - Separate epic if needed

3. **Additional HRS Data Endpoints:**
   - `/hrs-data/bonus/quarterly` - Quarterly bonuses
   - `/hrs-data/bonus/tet` - Tet bonuses
   - `/hrs-data/evaluation/annual` - Annual evaluations
   - These use same pattern, can add incrementally

4. **Salary Notifications:**
   - Email when salary is paid or changes
   - Requires notification system (out of scope)

5. **Advanced Analytics:**
   - Salary comparison with peers (anonymized)
   - Salary projections/estimates
   - Requires more complex logic

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| HRS API downtime during testing | Medium | High | Use mocked responses for most tests |
| Field mapping errors | Low | High | Validate with HR, test with real data |
| Performance issues (12 months) | Medium | Medium | Parallel API calls, add timeout |
| Authorization bugs | Low | Critical | Comprehensive auth tests, manual verification |
| HRS API format change | Low | High | Field validation, error alerts |

---

## Questions for Stakeholders

Before starting implementation, clarify:

1. **HRS API SLA:** What is uptime guarantee? Who to contact if down?
2. **Data Retention:** How many months does HRS API retain salary data?
3. **Field Definitions:** Can we get official documentation of all 45 fields?
4. **Testing:** Can we use real employee IDs for testing? Any privacy concerns?
5. **Audit Requirements:** Do admin salary queries need to be logged? For how long?

---

## Notes

**Simplifications Made:**
- No database storage (reduces scope significantly)
- Reuse existing HRS client (just enhance, not rewrite)
- Only 3 endpoints (not 6+ like employee CRUD)
- No PDF export (can add later if needed)
- No caching (can add if performance becomes issue)

**Leverage from #sync-employee-info:**
- FHSHRSClient infrastructure
- Employee model for name lookup
- JWT authentication and authorization
- Router/service/schema pattern
- Error handling patterns

**Why This is Simpler than Employee Sync:**
- Read-only (no writes, no data validation complexity)
- No database schema design or migrations
- No bulk operations (just single employee queries)
- No data merging from multiple sources
- Integration client already exists

**Estimated Complexity:** Medium (simpler than employee sync)
- Employee Sync: 7 tasks, 7 days → Salary API: 5 tasks, 4-5 days

---

## Tasks Created

- [ ] #20 - Create Pydantic schemas for salary data responses (parallel: false)
- [ ] #21 - Enhance HRS client to return structured salary data (parallel: false, depends_on: [20])
- [ ] #22 - Implement service layer for salary queries and trend analysis (parallel: false, depends_on: [21])
- [ ] #23 - Create REST API endpoints for salary queries (parallel: false, depends_on: [22])
- [ ] #24 - Add tests and documentation for salary API (parallel: false, depends_on: [23])

**Total tasks:** 5
**Parallel tasks:** 0 (all sequential)
**Sequential tasks:** 5
**Estimated total effort:** 22-31 hours (≈ 3-4 working days)
