---
name: sync-employee-info
status: backlog
created: 2026-01-09T02:11:35Z
progress: 0%
prd: .claude/prds/sync-employee-info.md
github: [Will be updated when synced to GitHub]
---

# Epic: Sync Employee Info

## Overview

Implement employee information management system that syncs data from FHS HRS and COVID APIs to local PostgreSQL database. System provides admin-only API endpoints for single/bulk sync, search, and CRUD operations on employee data. Architecture follows existing OAuth login pattern with similar structure (integrations → services → routers → schemas → models).

**Key Components:**
- 2 Integration Clients (HRS + COVID APIs)
- Employee database model (20+ fields)
- Service layer with sync logic
- 6 Admin REST API endpoints
- Search with filters and pagination

**Leverage Existing Patterns:**
- Reuse existing async database session pattern
- Follow OAuth client integration pattern
- Use existing admin authorization (require_role("admin"))
- Similar service → router → schema structure

---

## Architecture Decisions

### 1. **Integration Pattern: Reuse OAuth Client Approach**
**Decision:** Create `FHSHRSClient` and `FHSCovidClient` following same pattern as `GoogleAuthClient` and `GitHubAuthClient`

**Rationale:**
- Proven pattern already working in codebase
- Async HTTP client with httpx
- Error handling and retry logic established
- UTF-8 encoding handling for Chinese/Vietnamese text

**Implementation:**
- Base class with `_fetch_text()` helper method
- Single + bulk methods in each client
- Return None on error (no exceptions in clients)

### 2. **Database Model: Standalone Employee Table**
**Decision:** Create independent `employees` table with no foreign keys initially

**Rationale:**
- Dorms feature not yet implemented (dorm_id field as placeholder)
- Future: Link to users table via localId
- Indexes on search fields (department_code, identity_number)
- Unique constraint on identity_number (CMND/CCCD)

**Schema:**
```sql
employees (
  id VARCHAR(10) PRIMARY KEY,      -- VNW0006204
  name_tw, name_en,                -- Chinese + Vietnamese names
  dob, start_date,                 -- Dates
  dept, department_code,           -- Department info
  job_title, job_type, salary,     -- Job info
  address1, address2,              -- Addresses
  phone1, phone2,                  -- Contact
  spouse_name, nationality,        -- Personal
  identity_number UNIQUE,          -- CMND/CCCD
  sex, dorm_id,                    -- Gender + dorm
  created_at, updated_at           -- Audit timestamps
)
```

### 3. **Service Layer: Unified Sync Method**
**Decision:** Single `bulk_sync_employees()` method handles both HRS and COVID sources

**Rationale:**
- DRY principle - avoid duplicate code
- Source parameter determines which client to use
- Consistent error handling and result format
- Easy to add more sources in future

**Method Signature:**
```python
async def bulk_sync_employees(
    db: AsyncSession,
    from_id: int,
    to_id: int,
    source: Literal["hrs", "covid"],
    token: Optional[str] = None
) -> BulkSyncResponse
```

### 4. **API Design: REST with Admin-Only Access**
**Decision:** 6 endpoints under `/api/employees` with admin authorization

**Rationale:**
- Sensitive employee data requires admin access
- RESTful design: GET/POST/PUT/DELETE
- Pagination for search (skip/limit)
- Bulk operations return summary (success, failed, skipped counts)

**Endpoints:**
1. `POST /sync` - Single employee sync
2. `POST /bulk-sync` - Bulk sync (from_id to to_id)
3. `GET /search` - Search with filters
4. `GET /{emp_id}` - Get employee details
5. `PUT /{emp_id}` - Update employee
6. `DELETE /{emp_id}` - Delete employee

### 5. **Error Handling: Graceful Degradation**
**Decision:** Bulk sync continues on individual failures

**Rationale:**
- Some employee IDs may not exist
- External APIs may timeout for specific IDs
- Don't fail entire batch due to one error
- Return detailed error list for debugging

**Response Format:**
```json
{
  "total": 100,
  "success": 95,
  "failed": 3,
  "skipped": 2,
  "errors": [
    {"emp_id": 6203, "error": "Employee not found"},
    {"emp_id": 6207, "error": "API timeout"}
  ]
}
```

### 6. **Text Encoding: Force UTF-8**
**Decision:** Explicitly set UTF-8 encoding on all HTTP responses

**Rationale:**
- Chinese names (陳玉俊) require proper encoding
- Vietnamese names with diacritics (Trần Ngọc Tuấn)
- FHS APIs may return incorrect encoding headers

**Implementation:**
```python
resp.encoding = "utf-8"  # Force encoding
```

---

## Technical Approach

### Backend Architecture

```
┌─────────────┐
│   Admin     │ JWT token (admin role)
│   Client    │
└──────┬──────┘
       │
       ↓
┌─────────────────────────────────┐
│  FastAPI Endpoints              │
│  /api/employees/*               │
│  - require_role("admin")        │
└──────┬──────────────────────────┘
       │
       ↓
┌─────────────────────────────────┐
│  Employee Service Layer         │
│  - sync_employee_from_hrs()     │
│  - sync_employee_from_covid()   │
│  - bulk_sync_employees()        │
│  - search_employees()           │
│  - CRUD operations              │
└──────┬────────────┬─────────────┘
       │            │
       ↓            ↓
┌─────────────┐  ┌──────────────┐
│  FHS HRS    │  │ FHS COVID    │
│  Client     │  │ Client       │
└─────────────┘  └──────────────┘
       │            │
       ↓            ↓
┌─────────────────────────────────┐
│  External FHS APIs              │
│  - HRS: 22 fields (no auth)     │
│  - COVID: fewer fields (token)  │
└─────────────────────────────────┘
       │
       ↓
┌─────────────────────────────────┐
│  PostgreSQL Database            │
│  - employees table              │
│  - indexes: dept_code, id_num   │
└─────────────────────────────────┘
```

### Data Flow

**Single Sync:**
1. Admin → POST /api/employees/sync {emp_id, source, token?}
2. Validate JWT + admin role
3. Call service: sync_employee_from_hrs() or sync_employee_from_covid()
4. Service → Client → External API
5. Parse response → Map to Employee model
6. Upsert to database (create or update)
7. Return Employee object

**Bulk Sync:**
1. Admin → POST /api/employees/bulk-sync {from_id, to_id, source, token?}
2. Validate JWT + admin role + token (if covid)
3. Call service: bulk_sync_employees()
4. Service → Client.bulk_get_*() → Loop IDs → External API
5. For each result: parse → map → upsert
6. Continue on errors, collect summary
7. Return {total, success, failed, skipped, errors[]}

**Search:**
1. Admin → GET /api/employees/search?name=x&dept=y
2. Validate JWT + admin role
3. Build SQL query with filters (ILIKE on names, exact match on dept)
4. Apply pagination (skip, limit)
5. Return list of employees

---

## Implementation Strategy

### Phase 1: Foundation (Database + Models)
**Goal:** Setup database schema and data models

**Tasks:**
1. Create Employee model in `app/models/employee.py`
2. Create Alembic migration for employees table
3. Run migration on dev database
4. Create Pydantic schemas in `app/schemas/employees.py`

**Deliverables:**
- Employee SQLAlchemy model
- Database migration file
- Request/Response schemas

**Risk Mitigation:**
- Test migration on dev before prod
- Verify UTF-8 encoding in database
- Validate unique constraint on identity_number

---

### Phase 2: Integration Clients
**Goal:** Implement HTTP clients for external APIs

**Tasks:**
1. Create FHSHRSClient with single + bulk methods
2. Create FHSCovidClient with single + bulk methods
3. Add utility functions (text parsing, date parsing, name normalization)
4. Test with real FHS APIs

**Deliverables:**
- `app/integrations/fhs_hrs_client.py`
- `app/integrations/fhs_covid_client.py`
- `app/utils/text_utils.py` (chuan_hoa_ten, parse_date, first_block)

**Risk Mitigation:**
- Mock external APIs in tests
- Handle timeout and retry logic
- Force UTF-8 encoding
- Test with Chinese and Vietnamese names

---

### Phase 3: Service Layer
**Goal:** Implement business logic for sync and CRUD

**Tasks:**
1. Create employee_service.py with all methods:
   - sync_employee_from_hrs()
   - sync_employee_from_covid()
   - bulk_sync_employees() (unified for both sources)
   - search_employees()
   - get_employee_by_id()
   - update_employee()
   - delete_employee()

**Deliverables:**
- `app/services/employee_service.py`
- Comprehensive error handling
- Database transaction management

**Risk Mitigation:**
- Test upsert logic (create vs update)
- Validate data before database write
- Log all errors with context

---

### Phase 4: API Endpoints
**Goal:** Expose REST APIs for admin access

**Tasks:**
1. Create employees router in `app/routers/employees.py`
2. Implement 6 endpoints:
   - POST /api/employees/sync
   - POST /api/employees/bulk-sync
   - GET /api/employees/search
   - GET /api/employees/{emp_id}
   - PUT /api/employees/{emp_id}
   - DELETE /api/employees/{emp_id}
3. Register router in main.py
4. Add OpenAPI documentation

**Deliverables:**
- Complete REST API
- Swagger UI documentation
- Admin authorization on all endpoints

**Risk Mitigation:**
- Validate all inputs with Pydantic
- Test authorization (403 for non-admin)
- Test pagination limits

---

### Phase 5: Testing & Documentation
**Goal:** Comprehensive test coverage and docs

**Tasks:**
1. Unit tests for:
   - Integration clients (mocked HTTP)
   - Service layer (mocked database)
   - Utility functions
2. Integration tests for:
   - API endpoints (full request/response)
   - Database operations
3. Documentation:
   - API usage guide
   - Deployment guide
   - E2E test plan

**Deliverables:**
- Test coverage > 80%
- 40+ test cases
- Complete documentation

**Risk Mitigation:**
- Test with real API responses (recorded)
- Test error scenarios
- Test UTF-8 encoding edge cases

---

## Task Breakdown Preview

High-level task categories (aim for ≤10 tasks):

1. **Database Setup**
   - Create Employee model, migration, schemas
   - Run migration on dev/staging/prod

2. **Integration Clients**
   - Implement FHSHRSClient (single + bulk)
   - Implement FHSCovidClient (single + bulk)
   - Add utility functions for parsing

3. **Service Layer**
   - Implement employee_service.py (all 7 methods)
   - Handle sync logic, CRUD, search

4. **API Endpoints**
   - Create employees router with 6 endpoints
   - Add admin authorization
   - Register in main.py

5. **Unit Tests**
   - Test clients, services, utilities
   - Mock external dependencies

6. **Integration Tests**
   - Test API endpoints end-to-end
   - Test database operations

7. **Documentation**
   - API documentation
   - Deployment guide
   - E2E test plan

**Total Tasks: 7 major tasks** (can be broken down further if needed)

---

## Dependencies

### External Dependencies
1. **FHS HRS API** (https://www.fhs.com.tw/ads/api/Furnace/rest/json/hr)
   - Status: Available
   - Auth: None required
   - Provides: 22 fields per employee

2. **FHS COVID API** (https://www.fhs.com.tw/fhs_covid_api/api/reportVaccines/detail)
   - Status: Available
   - Auth: Bearer token (admin must provide)
   - Provides: Basic employee info (fewer fields)
   - Risk: Token expiration (admin must refresh)

### Internal Dependencies
1. **OAuth Login System** ✅ Completed
   - Admin role-based access control
   - JWT authentication
   - require_role("admin") dependency

2. **Database Infrastructure** ✅ Completed
   - PostgreSQL (ktxn258.duckdns.org:6543)
   - Alembic migrations
   - Async SQLAlchemy sessions

3. **Existing Patterns** ✅ Available
   - Integration client pattern (Google/GitHub OAuth)
   - Service layer pattern (auth_service.py)
   - Router pattern (users.py, auth.py)
   - Schema pattern (auth.py schemas)

### Future Dependencies
- **Dorms Feature** (not yet implemented)
  - dorm_id field is placeholder
  - Will become foreign key when dorms table created

---

## Success Criteria (Technical)

### Performance Benchmarks
- ✅ Single sync: < 3 seconds (p95)
- ✅ Bulk sync: < 1.5 seconds per employee (p95)
- ✅ Search query: < 500ms for 100 records (p95)
- ✅ Get by ID: < 100ms

### Quality Gates
- ✅ Test coverage > 80%
- ✅ All unit tests pass
- ✅ All integration tests pass
- ✅ No critical security vulnerabilities
- ✅ Code follows project standards

### Acceptance Criteria
- ✅ Admin can sync single employee from HRS (no token)
- ✅ Admin can sync single employee from COVID (with token)
- ✅ Admin can bulk sync 100+ employees (both sources)
- ✅ Bulk sync continues on individual failures
- ✅ Admin can search employees by name/department/dorm
- ✅ Admin can view full employee details
- ✅ Admin can update employee info
- ✅ Non-admin users get 403 Forbidden
- ✅ Chinese and Vietnamese names display correctly
- ✅ Identity_number unique constraint enforced
- ✅ Sync success rate > 90% (excluding non-existent IDs)

### Data Quality
- ✅ 0 duplicate identity_numbers
- ✅ 0 data corruption incidents
- ✅ UTF-8 encoding correct for all text fields
- ✅ All required fields populated (id, name)

---

## Estimated Effort

### Overall Timeline
**Total: 10-12 working days** (2 sprints)

### Breakdown by Phase
1. **Database Setup:** 1-2 days
   - Model + migration + schemas
   - Test on dev database

2. **Integration Clients:** 2-3 days
   - HRS client (22 fields parsing)
   - COVID client (bearer token handling)
   - UTF-8 encoding + retry logic

3. **Service Layer:** 2-3 days
   - Sync methods (single + bulk)
   - CRUD operations
   - Search with filters

4. **API Endpoints:** 2 days
   - 6 REST endpoints
   - Authorization + validation

5. **Testing:** 2 days
   - Unit tests (mocked)
   - Integration tests (full stack)

6. **Documentation:** 1 day
   - API docs
   - Deployment guide

### Resource Requirements
- **1 Backend Developer** (full-time)
- **Database Access** (PostgreSQL dev/staging/prod)
- **FHS API Access** (HRS + COVID APIs)
- **Admin Bearer Token** (for COVID API testing)

### Critical Path Items
1. ⚠️ **External API Dependencies**
   - FHS APIs must be available and stable
   - Token expiration handling

2. ⚠️ **UTF-8 Encoding**
   - Critical for Chinese/Vietnamese names
   - Must test thoroughly

3. ⚠️ **Bulk Sync Performance**
   - 100+ employees = 100+ API calls
   - May need rate limiting or background jobs

---

## Risk Assessment

### High Priority Risks

**Risk 1: External API Downtime**
- Impact: HIGH - Cannot sync employees
- Probability: MEDIUM
- Mitigation:
  - Implement retry logic (3 attempts)
  - Cache employee data locally
  - Graceful error messages to admin

**Risk 2: Token Expiration (COVID API)**
- Impact: HIGH - Bulk sync fails midway
- Probability: HIGH
- Mitigation:
  - Validate token before starting bulk sync
  - Clear error message when token expires
  - Document token refresh process

**Risk 3: UTF-8 Encoding Issues**
- Impact: MEDIUM - Corrupted names
- Probability: MEDIUM
- Mitigation:
  - Force UTF-8 on all responses
  - Test with real Chinese/Vietnamese data
  - Database collation: utf8mb4

### Medium Priority Risks

**Risk 4: Performance Degradation**
- Impact: MEDIUM - Slow sync/search
- Probability: LOW
- Mitigation:
  - Indexes on search fields
  - Pagination required
  - Monitor query performance

**Risk 5: Data Inconsistency**
- Impact: MEDIUM - Out of sync data
- Probability: MEDIUM
- Mitigation:
  - Track updated_at timestamp
  - Provide re-sync functionality
  - External API overrides local data

---

## Next Steps

After epic creation, run: `/pm:epic-decompose sync-employee-info`

This will:
1. Break down into 7-10 specific tasks
2. Assign task IDs and dependencies
3. Create GitHub issues
4. Setup git worktree for development

---

**Epic Status:** Ready for decomposition
**Dependencies:** All internal dependencies met (OAuth, DB, patterns)
**External Dependencies:** FHS APIs available
**Risk Level:** Medium (external APIs + encoding)
**Estimated Effort:** 10-12 days (1 developer)
