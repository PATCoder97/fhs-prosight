---
name: achievement-info-api
status: completed
created: 2026-01-10T01:10:04Z
progress: 100%
prd: .claude/prds/achievement-info-api.md
github: https://github.com/PATCoder97/fhs-prosight/issues/25
---

# Epic: Achievement Info API

## Overview

Add achievement/evaluation viewing capability to the existing HRS data API by extending current infrastructure. This is a minimal-scope implementation that reuses all existing patterns from the salary API: same router, same service structure, same authorization model, and same HRS client integration approach.

**Key Principle**: Maximum code reuse, minimal new code. This is an incremental enhancement, not a new feature.

## Architecture Decisions

### AD1: Extend Existing Router (No New Router)
**Decision**: Add 2 new endpoints to `backend/app/routers/hrs_data.py`
**Rationale**:
- Achievements are HRS data, same as salary
- Same authorization requirements (block guests)
- Avoids router proliferation
- Maintains consistent API structure under `/api/hrs-data`

### AD2: Reuse Authorization Pattern
**Decision**: Use existing `require_authenticated_user` dependency
**Rationale**:
- Identical authorization rules as salary endpoints
- Already implemented and tested
- Blocks guests (403), allows authenticated users
- Zero new security code needed

### AD3: Extend HRS Client (Not New Integration)
**Decision**: Add `get_achievement_data()` method to existing `FHSHRSClient`
**Rationale**:
- Same HRS API source, different endpoint path
- Reuse existing `_fetch_text()` infrastructure
- Consistent error handling patterns
- Single integration point to maintain

### AD4: No Database Storage
**Decision**: Real-time queries only, no local caching/storage
**Rationale**:
- Achievement data changes infrequently
- Simplifies implementation (no migrations)
- Consistent with salary API approach
- Reduces data synchronization complexity

### AD5: Minimal Schema Extension
**Decision**: Add 2 simple Pydantic models to existing `hrs_data.py` schema file
**Rationale**:
- `Achievement` (2 fields: year, score)
- `AchievementResponse` (3 fields: employee_id, employee_name, achievements)
- Much simpler than salary schemas (32+ fields)
- Follows established schema patterns

## Technical Approach

### Backend Services

#### HRS Client Extension (`app/integrations/fhs_hrs_client.py`)
**New Method**:
```python
async def get_achievement_data(self, emp_id: int) -> List[dict]
```

**Implementation**:
- Path: `s11/VNW00{emp_id:05d}`
- Parse pipe-delimited response: `2024|甲o|o2023|甲o|o`
- Extract blocks using `_split_blocks()` helper
- Validate: year > 1990, score non-empty
- Return sorted list (descending by year)

**Parsing Logic** (provided by user):
```python
for block in _split_blocks(raw_text):
    parts = block.split("|")
    if len(parts) >= 2:
        year = int(parts[0])
        score = parts[1].strip()
        if year > 1990 and score:
            results.append({"year": str(year), "score": score})
```

**Lines of code**: ~30 lines (method + helper)

#### Schema Extension (`app/schemas/hrs_data.py`)
**New Models**:
```python
class Achievement(BaseModel):
    year: str = Field(..., description="Evaluation year")
    score: str = Field(..., description="Achievement score (甲, 優, etc.)")

class AchievementResponse(BaseModel):
    employee_id: str
    employee_name: str
    achievements: List[Achievement]
```

**Lines of code**: ~20 lines

#### Service Layer (`app/services/hrs_data_service.py`)
**New Method**:
```python
async def get_employee_achievements(db: AsyncSession, emp_id: str) -> dict
```

**Logic** (mirrors `get_employee_salary` pattern):
1. Convert employee ID: VNW0006204 → 6204 (reuse existing pattern)
2. Call `hrs_client.get_achievement_data(emp_num)`
3. Lookup employee name from database (reuse Employee model query)
4. Return structured response matching `AchievementResponse`
5. Error handling: 400 (invalid ID), 404 (no data), 503 (HRS unavailable)

**Lines of code**: ~50 lines

#### Router Extension (`app/routers/hrs_data.py`)
**New Endpoints**:

1. `GET /api/hrs-data/achievements` - View own achievements
   - Authorization: `Depends(get_current_user)` (same as own salary)
   - Extract emp_id from current_user
   - Call service layer
   - Return `AchievementResponse`

2. `GET /api/hrs-data/achievements/{employee_id}` - View any employee
   - Authorization: `Depends(require_authenticated_user)` (same as salary history)
   - Call service layer with path parameter
   - Return `AchievementResponse`

**Lines of code**: ~60 lines (both endpoints with docs)

### Frontend Components

**Not Required**: This epic is backend API only. Frontend integration is out of scope.

### Infrastructure

**No Changes Required**:
- No new dependencies
- No database migrations
- No environment variables
- No deployment configuration changes

## Implementation Strategy

### Single-Phase Approach

Given the minimal scope and maximum code reuse, this can be implemented as a single cohesive task rather than multiple phases:

**All-in-One Implementation**:
1. Add schemas (20 lines)
2. Extend HRS client (30 lines)
3. Add service method (50 lines)
4. Add router endpoints (60 lines)
5. Add tests (unit + integration)
6. Update API documentation

**Why Single Phase**:
- Total new code: ~160 lines
- All components tightly coupled
- No external dependencies between steps
- Can be completed in one session
- Easier to test as complete feature

**Testing Strategy**:
- Unit tests for `_split_blocks()` parsing
- Unit tests for `get_employee_achievements()` service
- Integration tests for both endpoints (auth, errors, success)
- Follow exact patterns from salary API tests

**Risk Mitigation**:
- Reuse eliminates architectural risk
- Parsing logic provided by user (tested)
- Authorization already battle-tested
- HRS client patterns proven

## Task Breakdown Preview

Given the emphasis on minimal tasks (≤10), this epic will have **5 tasks**:

1. **Extend HRS Client** - Add `get_achievement_data()` method and parsing logic
2. **Add Schemas** - Create Achievement and AchievementResponse models
3. **Implement Service Layer** - Add `get_employee_achievements()` method
4. **Create API Endpoints** - Add 2 endpoints to hrs_data router
5. **Add Tests and Documentation** - Unit tests, integration tests, API guide

Each task is small (1-3 hours), self-contained, and follows existing patterns.

## Dependencies

### Internal Dependencies (All Existing)
- HRS client base class: `app/integrations/fhs_hrs_client.py` ✓
- Authorization functions: `app/core/security.py` (require_authenticated_user) ✓
- Employee model: `app/models/employee.py` ✓
- HRS data router: `app/routers/hrs_data.py` ✓
- HRS data service: `app/services/hrs_data_service.py` ✓
- HRS data schemas: `app/schemas/hrs_data.py` ✓

### External Dependencies
- HRS API endpoint `s11/VNW00{emp_id:05d}` (production system)
- Database for employee name lookup (already connected)

### No New Dependencies
- Zero new Python packages
- Zero new infrastructure
- Zero database changes
- Zero configuration changes

## Success Criteria (Technical)

### Performance
- [ ] Response time < 2 seconds (typical case)
- [ ] HRS API timeout handled (max 10 seconds)
- [ ] No performance degradation on existing salary endpoints

### Reliability
- [ ] Graceful HRS API failure handling (503 with clear message)
- [ ] Missing data returns 404 (not 500)
- [ ] Invalid employee ID returns 400 (not crash)
- [ ] UTF-8 encoding handles Japanese characters (甲, 優)

### Security
- [ ] JWT validation required for all requests (401 if missing)
- [ ] Guest users blocked with 403 Forbidden
- [ ] Non-guest authenticated users can access (200)
- [ ] No data leakage in error messages

### Quality
- [ ] Unit test coverage > 90% for new code
- [ ] Integration tests for both endpoints
- [ ] All tests pass (no regressions)
- [ ] OpenAPI documentation auto-generated
- [ ] Follows existing code style (Black, pylint)

### Functional
- [ ] Authenticated users can view own achievements (endpoint 1)
- [ ] Authenticated non-guest users can view any employee (endpoint 2)
- [ ] Data sorted by year (descending)
- [ ] Employee names resolved from database
- [ ] Empty results handled gracefully (404 or empty list)

## Estimated Effort

### By Task
1. HRS Client Extension: 2 hours
2. Schema Models: 1 hour
3. Service Layer: 2 hours
4. API Endpoints: 2 hours
5. Tests + Documentation: 3 hours

**Total**: 10 hours (~1.5 days for one developer)

### Critical Path
All tasks are sequential:
- Schemas must exist before service
- Service must exist before endpoints
- Endpoints must exist before tests

**No parallelization opportunity** due to tight coupling.

### Resource Requirements
- 1 backend developer (Python/FastAPI experience)
- Access to HRS API staging environment (for testing)
- Code review from team lead

### Assumptions
- HRS API endpoint `s11` is already available
- Sample test data available for validation
- No breaking changes to existing salary API
- No frontend work required (backend only)

## Comparison with Salary API

To emphasize code reuse:

| Aspect | Salary API | Achievement API | Reuse % |
|--------|-----------|-----------------|---------|
| Router file | hrs_data.py | hrs_data.py | 100% |
| Service file | hrs_data_service.py | hrs_data_service.py | 100% |
| Schema file | hrs_data.py | hrs_data.py | 100% |
| HRS client | fhs_hrs_client.py | fhs_hrs_client.py | 100% |
| Authorization | require_authenticated_user | require_authenticated_user | 100% |
| Employee lookup | Employee model | Employee model | 100% |
| Error handling | HTTPException patterns | HTTPException patterns | 100% |
| Testing patterns | pytest + mocking | pytest + mocking | 100% |

**New Code**: Only parsing logic and 2 endpoints. Everything else is reuse.

## Open Questions (Resolved)

All questions from PRD have been resolved with assumptions:

1. **Caching**: No (real-time only)
2. **Score validation**: No (accept any non-empty string)
3. **Year sorting**: Yes (descending, most recent first)
4. **Year filtering**: No (return all available years)
5. **Endpoint structure**: 2 endpoints (own + by employee_id)
6. **Authorization**: Same as salary (block guests)

No user input needed - proceed with implementation.

## Tasks Created
- [ ] #27 - Add Pydantic schemas for achievement data (parallel: false)
- [ ] #28 - Extend HRS client with achievement data retrieval (parallel: false)
- [ ] #29 - Implement service layer for achievement queries (parallel: false)
- [ ] #30 - Create REST API endpoints for achievement queries (parallel: false)
- [ ] #31 - Add tests and documentation for achievement API (parallel: false)

**Total tasks**: 5
**Parallel tasks**: 0
**Sequential tasks**: 5
**Estimated total effort**: 10 hours (~1.5 days)

**Critical Path**: All tasks are sequential. Task 001 and 002 can technically run in parallel, but the effort is minimal (1-2 hours each), so sequential execution is simpler.
