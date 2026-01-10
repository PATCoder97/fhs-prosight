# PRD: Year Bonus Information API

## Executive Summary

Add REST API endpoint to view employee year-end bonus information from HRS system. This feature extends the existing HRS data infrastructure to expose year bonus data (thưởng cuối năm), which includes both pre-Tet and post-Tet bonus payments.

**Key Requirements**:
- Single endpoint: `GET /api/hrs-data/year-bonus/{employee_id}/{year}`
- Authorization: Same as salary API (allow all authenticated users, block guests)
- Data source: HRS API endpoint `s19` (2 parallel calls for pre-Tet and post-Tet bonuses)
- No tests or documentation required (per user request)

## Business Context

### Problem Statement

Employees need to view their year-end bonus information, which is paid in two installments (before Tet and after Tet). This data currently exists in the HRS system but is not accessible via API.

### Target Users

- **Primary**: All employees (view any employee's bonus - same access as salary API)
- **Excluded**: Guest users (blocked)

### Success Metrics

- API successfully retrieves and combines both pre-Tet and post-Tet bonus data
- Response time < 2 seconds (parallel API calls)
- 100% code reuse from existing salary/achievement infrastructure

## Requirements

### Functional Requirements

1. **Single Endpoint**: `GET /api/hrs-data/year-bonus/{employee_id}/{year}`
   - Path parameters: employee_id (e.g., VNW0006204), year (e.g., 2024)
   - Returns combined bonus data from both pre-Tet and post-Tet payments
   - Response includes employee info + bonus details

2. **Authorization**: Same model as salary API
   - All authenticated users can view any employee's bonuses
   - Guest users are blocked (403 Forbidden)

3. **Data Retrieval**: Call 2 HRS API endpoints in parallel
   - Pre-Tet: `s19/{employee_id}vkokvbefvkokv{year}`
   - Post-Tet: `s19/{employee_id}vkokvaftvkokv{year}`
   - Parse pipe-delimited format (11+ fields for BEF, last field for AFT)

### Non-Functional Requirements

- **Performance**: Parallel API calls to minimize latency
- **Reliability**: Graceful error handling for HRS API failures
- **Maintainability**: Follow existing patterns from salary/achievement APIs
- **Security**: JWT authentication, role-based authorization

### Out of Scope

- Tests and documentation (per user request)
- Historical bonus trend analysis
- Multiple year queries (single year only)
- Bonus calculation or aggregation logic

## Technical Specifications

### API Endpoint

**Endpoint**: `GET /api/hrs-data/year-bonus/{employee_id}/{year}`

**Authorization**: Bearer token (blocks guest users)

**Path Parameters**:
- `employee_id`: Employee ID (e.g., VNW0006204)
- `year`: Year (e.g., 2024)

**Response 200**:
```json
{
  "employee_id": "VNW0006204",
  "employee_name": "PHAN ANH TUẤN",
  "year": 2024,
  "bonus_data": {
    "mnv": "VNW0006204",
    "tlcb": "15000000",
    "stdltbtn": "12",
    "capbac": "Senior",
    "tile": "100",
    "stienthuong": "5000000",
    "tpnttt": "2500000",
    "tpntst": "2500000"
  }
}
```

**Field Mapping** (from HRS API):
- Pre-Tet bonus (BEF) - 11 fields minimum:
  - `mnv`: Mã nhân viên (field 0)
  - `tlcb`: Tổng lương cơ bản (field 1)
  - `stdltbtn`: Số tháng đóng BHTN (field 2)
  - `capbac`: Cấp bậc (field 3)
  - `tile`: Tỷ lệ (field 4)
  - `stienthuong`: Số tiền thưởng (field 9)
  - `tpnttt`: Thưởng phần NT trước Tết (field 10)
- Post-Tet bonus (AFT) - last field:
  - `tpntst`: Thưởng phần NT sau Tết (last field)

**Error Responses**:
- `400`: Invalid employee ID or year format
- `401`: Unauthorized (missing or invalid token)
- `403`: Forbidden (guest user)
- `404`: No bonus data found for specified year
- `503`: HRS API unavailable

### HRS API Integration

**Base URL**: `FHS_HRS_BASE_URL` (from environment)

**Endpoints**:
1. Pre-Tet: `s19/VNW00{emp_id:05d}vkokvbefvkokv{year}`
2. Post-Tet: `s19/VNW00{emp_id:05d}vkokvaftvkokv{year}`

**Method**: Parallel async calls using `asyncio.gather()`

**Response Format**: Pipe-delimited text (e.g., `field1|field2|field3|...`)

**Parsing Logic**:
- Use existing `_first_block()` helper to handle duplicate data
- Split by `|` delimiter
- Validate field count (BEF needs ≥11 fields)
- Handle missing/malformed data gracefully

### Architecture

**Files to Modify** (4 files, similar to achievement API):
1. `backend/app/schemas/hrs_data.py` - Add YearBonusResponse schema
2. `backend/app/integrations/fhs_hrs_client.py` - Add get_year_bonus() method
3. `backend/app/services/hrs_data_service.py` - Add get_employee_year_bonus() service
4. `backend/app/routers/hrs_data.py` - Add GET /year-bonus/{employee_id}/{year} endpoint

**Pattern**: Follow exact same structure as salary and achievement APIs (100% code reuse)

### Data Models

**Pydantic Schema**:
```python
class YearBonusData(BaseModel):
    """Year bonus data fields."""
    mnv: Optional[str] = Field(None, description="Mã nhân viên")
    tlcb: Optional[str] = Field(None, description="Tổng lương cơ bản")
    stdltbtn: Optional[str] = Field(None, description="Số tháng đóng BHTN")
    capbac: Optional[str] = Field(None, description="Cấp bậc")
    tile: Optional[str] = Field(None, description="Tỷ lệ")
    stienthuong: Optional[str] = Field(None, description="Số tiền thưởng")
    tpnttt: Optional[str] = Field(None, description="Thưởng phần NT trước Tết")
    tpntst: Optional[str] = Field(None, description="Thưởng phần NT sau Tết")

class YearBonusResponse(BaseModel):
    """Response model for year bonus queries."""
    employee_id: str = Field(..., description="Employee ID")
    employee_name: str = Field(..., description="Employee name")
    year: int = Field(..., description="Bonus year")
    bonus_data: YearBonusData = Field(..., description="Bonus details")
```

## Implementation Plan

### Task Breakdown

1. **Task 1**: Add Pydantic schemas (YearBonusData, YearBonusResponse)
   - File: `backend/app/schemas/hrs_data.py`
   - Effort: 1 hour

2. **Task 2**: Extend HRS client with year bonus retrieval
   - File: `backend/app/integrations/fhs_hrs_client.py`
   - Add `get_year_bonus(emp_id, year)` method
   - Parallel API calls for BEF and AFT
   - Effort: 2 hours

3. **Task 3**: Implement service layer for year bonus queries
   - File: `backend/app/services/hrs_data_service.py`
   - Add `get_employee_year_bonus(db, emp_id, year)` method
   - Employee name lookup, validation, error handling
   - Effort: 2 hours

4. **Task 4**: Create REST API endpoint
   - File: `backend/app/routers/hrs_data.py`
   - Add `GET /year-bonus/{employee_id}/{year}` endpoint
   - Authorization with `require_authenticated_user` (blocks guests)
   - Effort: 2 hours

**Total Effort**: 7 hours (~1 day)

**No tests or documentation** (per user request - skip Task 5)

### Dependencies

- Existing HRS client infrastructure (`_fetch_text`, `_first_block`)
- Existing authorization system (`require_authenticated_user`)
- Employee model for name lookup
- FastAPI router (`/api/hrs-data`)

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| HRS API returns incomplete data (< 11 fields for BEF) | High | Validate field count, log warnings, return partial data with None values |
| One of the two API calls fails (BEF or AFT) | Medium | Use `return_exceptions=True` in gather(), return partial data |
| Year parameter validation needed | Low | Validate year range (e.g., 2000-2030) in service layer |
| Field position changes in HRS API | High | Follow exact field positions provided by user, add error logging |

## Success Criteria

- [x] Single endpoint successfully returns combined bonus data
- [x] Parallel API calls complete in < 2 seconds
- [x] Authorization blocks guest users (403)
- [x] Error handling for all edge cases (400, 401, 403, 404, 503)
- [x] Employee name lookup from database works
- [x] Code follows existing patterns (100% consistency with salary/achievement APIs)
- [x] No breaking changes to existing endpoints

## Deployment Notes

- No database migrations required
- No environment variable changes (uses existing `FHS_HRS_BASE_URL`)
- No new dependencies
- Backward compatible with existing HRS data endpoints

## Appendix

### Sample HRS API Response

**Pre-Tet (BEF)**:
```
VNW0006204|15000000|12|Senior|100|field5|field6|field7|field8|5000000|2500000o|o...
```

**Post-Tet (AFT)**:
```
field1|field2|...|2500000o|o...
```

### Field Positions (Critical - Must Follow Exactly)

**Pre-Tet (BEF)** - Index positions:
- [0]: mnv
- [1]: tlcb
- [2]: stdltbtn
- [3]: capbac
- [4]: tile
- [9]: stienthuong
- [10]: tpnttt

**Post-Tet (AFT)**:
- [-1]: tpntst (last field)

### Authorization Matrix

| Role | Access |
|------|--------|
| User | ✅ View any employee's bonus |
| Admin | ✅ View any employee's bonus |
| Guest | ❌ Blocked (403) |
| Unauthenticated | ❌ Blocked (401) |
