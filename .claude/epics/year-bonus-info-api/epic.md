---
name: year-bonus-info-api
status: completed
created: 2026-01-10T07:07:32Z
progress: 100%
prd: .claude/prds/year-bonus-info-api.md
github: https://github.com/PATCoder97/fhs-prosight/issues/32
---

# Epic: Year Bonus Information API

## Overview

Extend the existing HRS data infrastructure to expose year-end bonus information (thưởng cuối năm) through a single REST API endpoint. This implementation follows the exact same architecture pattern as the recently completed salary and achievement APIs, maximizing code reuse and maintaining consistency.

**Key Technical Characteristics**:
- Single endpoint with 2 path parameters (employee_id, year)
- Parallel HRS API calls (pre-Tet + post-Tet bonuses) for optimal performance
- Pipe-delimited response parsing with exact field position mapping
- 100% code reuse from existing infrastructure (schemas, client, service, router patterns)

## Architecture Decisions

### 1. Code Reuse Strategy (Critical)
**Decision**: Extend existing files rather than creating new modules
**Rationale**:
- Salary and achievement APIs already established the pattern
- All infrastructure exists (`_fetch_text`, `_first_block`, authorization, employee lookup)
- Reduces maintenance burden and ensures consistency
- Minimizes code review and testing effort

### 2. Parallel API Calls
**Decision**: Use `asyncio.gather()` to call BEF and AFT endpoints simultaneously
**Rationale**:
- Reduces response time from ~2s to ~1s
- HRS API calls are independent (no data dependency)
- Already proven pattern in salary history API
- Graceful degradation with `return_exceptions=True`

### 3. Field Position Mapping
**Decision**: Use exact array index positions provided by user (not named fields from HRS)
**Rationale**:
- HRS API returns positional pipe-delimited data (no field names)
- User provided validated field positions from production data
- Risk: If HRS changes field order, API breaks (acceptable - would affect all HRS integrations)

### 4. Authorization Model
**Decision**: Reuse `require_authenticated_user` dependency (blocks guests)
**Rationale**:
- Same access pattern as salary API (all authenticated users view any employee)
- Consistent with existing security model
- No new authorization logic needed

### 5. Error Handling Strategy
**Decision**: Return partial data if one API call (BEF or AFT) fails
**Rationale**:
- Better UX than complete failure
- Users can still see available bonus data
- Logging captures failures for investigation
- Fields default to `None` for missing data

## Technical Approach

### Backend Services

**No Frontend Changes**: This is a pure backend API addition.

#### 1. Data Schema Layer (`backend/app/schemas/hrs_data.py`)
- Add `YearBonusData` model with 8 optional fields (mnv, tlcb, stdltbtn, capbac, tile, stienthuong, tpnttt, tpntst)
- Add `YearBonusResponse` model wrapping employee info + bonus data
- All fields Optional[str] to handle partial data gracefully
- Follow exact naming from user-provided code

#### 2. HRS Client Layer (`backend/app/integrations/fhs_hrs_client.py`)
- Add `get_year_bonus(emp_id: int, year: int) -> dict` async method
- Construct 2 paths:
  - BEF: `s19/VNW00{emp_id:05d}vkokvbefvkokv{year}`
  - AFT: `s19/VNW00{emp_id:05d}vkokvaftvkokv{year}`
- Use `asyncio.gather()` for parallel calls
- Parse BEF: split by `|`, extract fields [0,1,2,3,4,9,10]
- Parse AFT: split by `|`, extract last field [-1]
- Return dict with all 8 fields (or empty dict on total failure)

#### 3. Service Layer (`backend/app/services/hrs_data_service.py`)
- Add `get_employee_year_bonus(db: AsyncSession, emp_id: str, year: int) -> dict` async method
- Validate employee ID format (VNW00XXXXX)
- Validate year range (e.g., 2000-2030)
- Convert emp_id to numeric format (VNW0006204 → 6204)
- Call HRS client `get_year_bonus()`
- Lookup employee name from database (fallback to "Unknown")
- Return structured response matching YearBonusResponse schema
- Error handling: 400 (invalid format), 404 (no data), 503 (HRS unavailable)

#### 4. Router Layer (`backend/app/routers/hrs_data.py`)
- Add `GET /year-bonus/{employee_id}/{year}` endpoint
- Path parameters: employee_id (str), year (int)
- Response model: YearBonusResponse
- Authorization: `require_authenticated_user` dependency (blocks guests)
- OpenAPI documentation with examples
- Logging for all requests
- Update router docstring to list 7 total endpoints

### Infrastructure

**No infrastructure changes needed**:
- Uses existing `FHS_HRS_BASE_URL` environment variable
- No database migrations (read-only from Employee table)
- No new dependencies
- No deployment configuration changes

## Implementation Strategy

### Development Phases

**Single Phase Implementation** (4 sequential tasks):
1. Schemas → 2. HRS Client → 3. Service → 4. Router

**Rationale**: Tasks have strict dependencies (each layer depends on previous layer)

### Risk Mitigation

| Risk | Mitigation Strategy |
|------|---------------------|
| HRS returns < 11 fields for BEF | Validate `len(bef_parts) >= 11` before parsing, log warning, return partial data |
| One API call fails (BEF or AFT) | `return_exceptions=True` in gather(), check `isinstance(result, str)`, continue with available data |
| Invalid year parameter | Validate year range (2000-2030) in service layer, return 400 if invalid |
| Field positions change in HRS | Add detailed error logging with raw response, fail fast with clear error message |

### Testing Approach

**Per user request: No tests or documentation**

Manual testing only:
- Test with known employee IDs and recent years
- Verify both BEF and AFT data present
- Test guest user blocked (403)
- Test invalid employee ID (400)
- Test future year with no data (404)

## Task Breakdown Preview

4 tasks total (matching achievement API pattern exactly):

- [ ] **Task 1: Add Pydantic schemas** - YearBonusData and YearBonusResponse models (~30 lines)
- [ ] **Task 2: Extend HRS client** - get_year_bonus() method with parallel API calls (~40 lines)
- [ ] **Task 3: Implement service layer** - get_employee_year_bonus() with validation and error handling (~60 lines)
- [ ] **Task 4: Create REST API endpoint** - GET /year-bonus/{employee_id}/{year} with authorization (~50 lines)

**Total new code**: ~180 lines across 4 files

## Dependencies

### External Dependencies
- HRS API endpoint `s19` must be available
- `FHS_HRS_BASE_URL` environment variable configured

### Internal Dependencies
- Employee model (existing)
- FHSHRSClient infrastructure (existing)
- `_fetch_text()` method (existing)
- `_first_block()` helper (existing)
- `require_authenticated_user` dependency (existing)
- FastAPI router `/api/hrs-data` (existing)

### Prerequisite Work
None - all infrastructure exists from salary and achievement APIs

## Success Criteria (Technical)

### Performance
- [ ] API response time < 2 seconds (parallel calls optimize this)
- [ ] No memory leaks or connection pool exhaustion
- [ ] Graceful degradation when one API call fails

### Quality
- [ ] All 4 files modified successfully
- [ ] No breaking changes to existing endpoints
- [ ] Code follows exact patterns from salary/achievement APIs
- [ ] Error handling for all edge cases (400, 401, 403, 404, 503)

### Security
- [ ] Guest users blocked with 403 Forbidden
- [ ] JWT authentication enforced
- [ ] No sensitive data logged (employee IDs only)

### Functional
- [ ] Returns combined BEF + AFT data in single response
- [ ] Employee name lookup works (with "Unknown" fallback)
- [ ] Field positions exactly match user specification
- [ ] Partial data returned if one API fails (not total failure)

## Estimated Effort

**Total**: 7 hours (~1 day)

Breakdown:
- Task 1 (Schemas): 1 hour
- Task 2 (HRS Client): 2 hours
- Task 3 (Service): 2 hours
- Task 4 (Router): 2 hours

**Critical Path**: Sequential execution (Task 1 → 2 → 3 → 4)

**Resource Requirements**: 1 backend developer familiar with FastAPI and existing HRS integration patterns

**No parallel work possible** due to strict layer dependencies

## Notes

### Code Reuse Opportunities
- Mirror achievement API structure exactly (both are single-year queries)
- Reuse all existing helpers (`_first_block`, `_fetch_text`)
- Reuse authorization pattern (same as salary API)
- Reuse employee lookup pattern (same as all HRS APIs)

### Simplifications Applied
- Skip tests and documentation (per user request)
- Single endpoint only (no history/trend analysis)
- Single year queries only (no date range)
- No database storage (read-only from Employee table)
- No new files created (extend existing 4 files)

### Key Differences from Achievement API
- **Parameters**: Achievement uses emp_id only, bonus uses emp_id + year
- **HRS Calls**: Achievement makes 1 call, bonus makes 2 parallel calls
- **Parsing**: Achievement uses `_split_blocks()` for multiple records, bonus uses `_first_block()` + positional indices
- **Response**: Achievement returns list of records, bonus returns single dict with 8 fields

## Tasks Created
- [ ] #33 - Add Pydantic schemas for year bonus data (parallel: false)
- [ ] #34 - Extend HRS client with year bonus retrieval (parallel: false)
- [ ] #35 - Implement service layer for year bonus queries (parallel: false)
- [ ] #36 - Create REST API endpoint for year bonus queries (parallel: false)

Total tasks: 4
Parallel tasks: 0
Sequential tasks: 4
Estimated total effort: 7 hours (~1 day)
