---
name: achievement-info-api
description: API endpoint for viewing employee achievements/evaluations across years
status: draft
created: 2026-01-10T01:07:25Z
updated: 2026-01-10T01:07:25Z
priority: medium
tags: [api, hrs-integration, achievements, evaluations]
---

# PRD: Achievement Info API

## Executive Summary

Provide employees with the ability to view their performance evaluations/achievements across multiple years through a simple REST API endpoint. The data is retrieved in real-time from the HRS system and parsed from a pipe-delimited format into structured JSON.

## Problem Statement

### Current State
- Employees cannot view their historical performance evaluation scores
- Achievement data exists in the HRS system but is not accessible through the application
- No visibility into multi-year performance trends

### Desired State
- Employees can view their achievement/evaluation history across all available years
- Data is presented in a clean, structured JSON format
- Real-time access to current HRS data without local storage

### Impact
- **Users**: Gain visibility into their performance history
- **HR**: Reduced requests for historical evaluation data
- **System**: Minimal implementation effort by leveraging existing HRS integration

## User Stories

### Story 1: View Own Achievements
**As an** authenticated employee
**I want to** view my performance evaluations across all years
**So that** I can review my historical performance and track my progress

**Acceptance Criteria:**
- I can call GET endpoint with my authentication token
- I receive a list of achievements with year and score
- Data is sorted by year (most recent first)
- If I'm a guest user, I receive a 403 Forbidden error

### Story 2: View Other Employee Achievements (Admin/Manager)
**As an** authenticated non-guest user
**I want to** view any employee's achievement history
**So that** I can review their performance for management purposes

**Acceptance Criteria:**
- I can specify employee_id in the request
- I receive their achievement history if it exists
- Guest users are blocked from this functionality
- I receive 404 if employee has no achievement data

## Requirements

### Functional Requirements

#### FR1: Single GET Endpoint
- **Endpoint**: `GET /api/hrs-data/achievements/{employee_id}` (optional path parameter)
- **Query**: If no employee_id in path, use authenticated user's ID
- **Response**: List of achievements with year and score
- **Format**: JSON matching schema below

#### FR2: HRS API Integration
- **Endpoint**: `s11/VNW00{emp_id:05d}` (HRS API)
- **Format**: Pipe-delimited response: `2024|甲o|o2023|甲o|o2022|優o|o`
- **Parsing**: Extract year and score from each block
- **Validation**: Year > 1990, score non-empty

#### FR3: Authorization
- **Authenticated users**: Can view own achievements
- **Non-guest users**: Can view any employee's achievements
- **Guest users**: Blocked with 403 Forbidden
- **Unauthenticated**: 401 Unauthorized

#### FR4: Response Schema
```json
{
  "employee_id": "VNW0006204",
  "employee_name": "PHAN ANH TUẤN",
  "achievements": [
    {"year": "2024", "score": "甲"},
    {"year": "2023", "score": "甲"},
    {"year": "2022", "score": "優"}
  ]
}
```

### Non-Functional Requirements

#### NFR1: Performance
- Response time < 2 seconds for typical requests
- HRS API timeout handling (max 10 seconds)

#### NFR2: Reliability
- Graceful handling of HRS API failures (503 Service Unavailable)
- Clear error messages for missing data (404 Not Found)

#### NFR3: Security
- JWT token validation for all requests
- Role-based authorization (block guests)
- No caching of sensitive achievement data

#### NFR4: Maintainability
- Reuse existing HRS client integration
- Add to existing hrs-data router (not new router)
- Follow existing patterns from salary API

## Technical Requirements

### API Design

#### Endpoint 1: Get Own Achievements
```
GET /api/hrs-data/achievements
Authorization: Bearer <jwt_token>

Response 200:
{
  "employee_id": "VNW0006204",
  "employee_name": "PHAN ANH TUẤN",
  "achievements": [
    {"year": "2024", "score": "甲"},
    {"year": "2023", "score": "甲"}
  ]
}

Response 401: Unauthorized (no token)
Response 403: Forbidden (guest user)
Response 404: No achievement data found
Response 503: HRS API unavailable
```

#### Endpoint 2: Get Employee Achievements
```
GET /api/hrs-data/achievements/{employee_id}
Authorization: Bearer <jwt_token>

Response 200: Same as above
Response 400: Invalid employee ID format
Response 401: Unauthorized (no token)
Response 403: Forbidden (guest user)
Response 404: No achievement data found
Response 503: HRS API unavailable
```

### Data Models

#### Achievement Schema (Pydantic)
```python
class Achievement(BaseModel):
    year: str
    score: str

class AchievementResponse(BaseModel):
    employee_id: str
    employee_name: str
    achievements: List[Achievement]
```

### Integration Points

#### HRS Client Extension
```python
async def get_achievement_data(self, emp_id: int) -> List[dict]:
    """
    Fetch achievement data from HRS API.

    Args:
        emp_id: Employee numeric ID (e.g., 6204)

    Returns:
        List of {"year": str, "score": str}

    Raises:
        Exception: If HRS API fails
    """
    path = f"s11/VNW00{emp_id:05d}"
    raw_text = await self._fetch_text(path)

    results = []
    for block in _split_blocks(raw_text):
        try:
            parts = block.split("|")
            if len(parts) >= 2:
                year = int(parts[0])
                score = parts[1].strip()
                if year > 1990 and score:
                    results.append({"year": str(year), "score": score})
        except (ValueError, IndexError):
            continue

    return sorted(results, key=lambda x: x["year"], reverse=True)
```

#### Helper Function
```python
def _split_blocks(text: str) -> List[str]:
    """Split pipe-delimited text into blocks."""
    return [b for b in text.split("o|o") if b.strip()]
```

### Router Implementation
- **File**: `backend/app/routers/hrs_data.py` (extend existing)
- **Router prefix**: `/hrs-data` (already exists)
- **Tags**: `["hrs-data"]` (already exists)
- **Authorization**: `require_authenticated_user` dependency (already exists)

### Service Layer
- **File**: `backend/app/services/hrs_data_service.py` (extend existing)
- **Method**: `async def get_employee_achievements(db, emp_id) -> dict`
- **Logic**:
  1. Validate employee ID format
  2. Call HRS client to fetch achievement data
  3. Lookup employee name from database
  4. Return structured response

## Implementation Approach

### Phase 1: HRS Client Extension
1. Add `get_achievement_data()` method to `FHSHRSClient`
2. Add `_split_blocks()` helper function
3. Test parsing with sample HRS response

### Phase 2: Schemas
1. Create `Achievement` and `AchievementResponse` Pydantic models
2. Add to `backend/app/schemas/hrs_data.py`

### Phase 3: Service Layer
1. Create `get_employee_achievements()` in `hrs_data_service.py`
2. Handle employee ID conversion (VNW0006204 → 6204)
3. Lookup employee name from database
4. Error handling (400, 404, 503)

### Phase 4: API Endpoints
1. Add two GET endpoints to `hrs_data.py` router
2. Use `require_authenticated_user` dependency
3. Add OpenAPI documentation

### Phase 5: Testing
1. Unit tests for parsing logic
2. Unit tests for service layer
3. Integration tests for endpoints
4. Test error cases (invalid ID, no data, HRS failure)

### Phase 6: Documentation
1. API usage guide with examples
2. Update main API documentation

## Dependencies

### Internal Dependencies
- Existing HRS client (`app/integrations/fhs_hrs_client.py`)
- Existing authorization (`app/core/security.py`)
- Employee model (`app/models/employee.py`)
- Existing hrs-data router and service

### External Dependencies
- HRS API endpoint `s11/VNW00{emp_id:05d}`
- Database for employee name lookup

### No New Dependencies
- No new packages required
- No database migrations needed
- No infrastructure changes

## Success Criteria

### Must Have
- [ ] Authenticated users can view own achievements
- [ ] Non-guest users can view any employee's achievements
- [ ] Guest users are blocked with 403 error
- [ ] HRS API parsing works correctly for pipe-delimited format
- [ ] Employee names are looked up from database
- [ ] Error handling for all failure cases (400, 404, 503)
- [ ] OpenAPI documentation generated

### Nice to Have
- [ ] Caching of achievement data (optional, depends on update frequency)
- [ ] Filtering by year range (optional)
- [ ] Export to CSV/PDF (optional, future enhancement)

### Testing Requirements
- [ ] Unit tests for parsing logic (>90% coverage)
- [ ] Unit tests for service layer
- [ ] Integration tests for both endpoints
- [ ] Manual testing with real HRS API

## Timeline Estimate

- **Phase 1-2 (HRS + Schemas)**: 2-3 hours
- **Phase 3 (Service)**: 2-3 hours
- **Phase 4 (Endpoints)**: 1-2 hours
- **Phase 5 (Testing)**: 3-4 hours
- **Phase 6 (Documentation)**: 1-2 hours

**Total**: 9-14 hours (1-2 days)

## Risks and Mitigations

### Risk 1: HRS API Format Changes
**Impact**: High
**Probability**: Low
**Mitigation**: Add robust parsing with try/except, log parse failures

### Risk 2: Special Characters in Scores
**Impact**: Medium
**Probability**: Medium (Japanese characters like 甲, 優)
**Mitigation**: Use UTF-8 encoding, test with real data

### Risk 3: Missing Achievement Data
**Impact**: Low
**Probability**: Medium (new employees, old employees)
**Mitigation**: Return 404 with clear message, handle empty lists gracefully

## Open Questions

1. Should we cache achievement data? (Assumption: No, always real-time)
2. Should we validate score values? (Assumption: No, accept any non-empty string)
3. Should we sort by year? (Assumption: Yes, descending)
4. Should we support filtering by year range? (Assumption: No, return all years)

## Appendix

### Sample HRS Response
```
2024|甲o|o2023|甲o|o2022|優o|o2021|甲o|o
```

### Expected Parsed Output
```json
[
  {"year": "2024", "score": "甲"},
  {"year": "2023", "score": "甲"},
  {"year": "2022", "score": "優"},
  {"year": "2021", "score": "甲"}
]
```

### Authorization Matrix
| User Type       | Own Achievements | Others' Achievements |
|-----------------|------------------|----------------------|
| Unauthenticated | 401              | 401                  |
| Guest           | 403              | 403                  |
| User            | ✓ 200            | ✓ 200                |
| Admin           | ✓ 200            | ✓ 200                |
