---
name: dormitory-info-api
status: backlog
created: 2026-01-12T03:14:25Z
progress: 0%
prd: .claude/prds/dormitory-info-api.md
github: https://github.com/PATCoder97/fhs-prosight/issues/45
---

# Epic: Dormitory Billing Management API

## Overview

Build a dormitory billing management system that mirrors the proven architecture of the evaluations-info-api. The system will provide two REST endpoints: JSON bulk import (admin only) and search with filters (authenticated users). This implementation leverages the existing codebase patterns for authentication, database operations, and bulk processing to minimize development time while ensuring consistency.

**Key Technical Characteristics:**
- JSON-based bulk import (not Excel, simpler than evaluations API)
- Flat response structure (no nested objects, simpler than evaluations API)
- Bulk upsert operations using proven pattern from evaluations API
- 15 database fields tracking electricity, water, and fees
- Composite unique key: (employee_id, term_code, dorm_code)
- Default sort: term_code DESC, created_at DESC

## Architecture Decisions

### 1. Reuse Evaluations API Pattern
**Decision**: Copy and adapt the evaluations API structure for dormitory bills
**Rationale**:
- Evaluations API already implements bulk operations successfully
- Same authentication/authorization requirements (admin import, user search)
- Same database patterns (composite keys, upsert logic, FK to employees)
- Proven bulk insert optimization (100-1000x faster than row-by-row)
- Reduces development time from 12 hours to ~8 hours

**What to Reuse:**
- Service layer bulk operation pattern (fetch all → hashmap → separate inserts/updates)
- Router structure (POST /import, GET /search with same auth pattern)
- Schema validation pattern (Pydantic models)
- Error handling and logging approach

**What to Simplify:**
- JSON import instead of Excel (no openpyxl, no temp files, no column mapping)
- Flat response structure (no nested dept_evaluation/mgr_evaluation groups)
- Fewer fields (15 vs 30+ in evaluations)
- Simpler filters (exact match only, no prefix matching)

### 2. JSON Instead of Excel Upload
**Decision**: Accept JSON in request body, not Excel file upload
**Rationale**:
- Simpler implementation (no file handling, no openpyxl dependency)
- Easier testing and debugging (JSON is human-readable)
- Better for API-first approach (frontend can construct JSON directly)
- Consistent with REST best practices
- Facility management can export JSON from their system

### 3. Flat Response Structure
**Decision**: Return flat bill objects, no nested structures
**Rationale**:
- Billing data is naturally flat (all fields at same level)
- Simpler frontend consumption
- No transformation logic needed in service layer
- Easier to add/modify fields later

### 4. Search Filters
**Decision**: Use exact match for all filters, add amount range filter
**Rationale**:
- employee_id, term_code, dorm_code are discrete values (exact match makes sense)
- No need for prefix matching like dept_code in evaluations
- Amount range filter (min_amount, max_amount) useful for finding outliers
- Keeps query logic simple and fast

### 5. Database Constraints for Data Quality
**Decision**: Use CHECK constraints for business rules
**Rationale**:
- Database enforces curr_index >= last_index (prevents data entry errors)
- Database enforces amounts >= 0 (prevents negative bills)
- Fails fast at database level, clear error messages
- Cannot be bypassed by buggy application code

## Technical Approach

### Backend Services

**Database Model** (`backend/app/models/dormitory_bill.py`):
```python
class DormitoryBill(Base):
    __tablename__ = "dormitory_bills"

    bill_id = Column(BigInteger, primary_key=True, autoincrement=True)
    employee_id = Column(String(20), ForeignKey("employees.employee_id"), nullable=False, index=True)
    term_code = Column(String(10), nullable=False, index=True)
    dorm_code = Column(String(20), nullable=False, index=True)
    factory_location = Column(String(100))

    # Electricity
    elec_last_index = Column(Numeric(10, 2), default=0)
    elec_curr_index = Column(Numeric(10, 2), default=0)
    elec_usage = Column(Numeric(10, 2), default=0)
    elec_amount = Column(Numeric(15, 2), default=0)

    # Water
    water_last_index = Column(Numeric(10, 2), default=0)
    water_curr_index = Column(Numeric(10, 2), default=0)
    water_usage = Column(Numeric(10, 2), default=0)
    water_amount = Column(Numeric(15, 2), default=0)

    # Fees
    shared_fee = Column(Numeric(15, 2), default=0)
    management_fee = Column(Numeric(15, 2), default=0)
    total_amount = Column(Numeric(15, 2), default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Constraints
    __table_args__ = (
        UniqueConstraint('employee_id', 'term_code', 'dorm_code', name='uq_bill_entry'),
        CheckConstraint('elec_curr_index >= elec_last_index', name='chk_elec_index'),
        CheckConstraint('water_curr_index >= water_last_index', name='chk_water_index'),
        CheckConstraint('total_amount >= 0 AND elec_amount >= 0 AND water_amount >= 0', name='chk_amounts'),
        Index('idx_dormitory_bills_sort', 'term_code', 'created_at', postgresql_ops={'term_code': 'DESC', 'created_at': 'DESC'}),
    )
```

**Service Layer** (`backend/app/services/dormitory_bill_service.py`):

Bulk Import Logic (copy from evaluations, adapt):
1. Parse JSON request body (bills array)
2. Validate all employee_id values exist in employees table
3. Fetch all existing bills in ONE query using OR conditions
4. Create hashmap: `{(employee_id, term_code, dorm_code): bill_object}`
5. Separate into inserts vs updates
6. Bulk insert with `db.add_all()`
7. Updates tracked by SQLAlchemy session
8. Single commit

Search Logic (similar to evaluations):
1. Build query with optional filters (exact match)
2. Add amount range filter if provided (min_amount, max_amount)
3. Count total before pagination
4. Apply sort: ORDER BY term_code DESC, created_at DESC
5. Apply pagination: LIMIT/OFFSET
6. Return flat bill objects (no transformation needed)

**API Endpoints** (`backend/app/routers/dormitory_bills.py`):
- POST /api/dormitory-bills/import - Admin only, accepts JSON array
- GET /api/dormitory-bills/search - Authenticated users, query params

### Infrastructure

**Migration Strategy:**
- Single Alembic migration to create dormitory_bills table
- Includes all indexes and constraints
- No data migration needed (new feature)

**Performance:**
- Expected: 1000+ bills imported in < 5 seconds
- Search response time: < 500ms
- Same bulk operation optimization as evaluations API

**Monitoring:**
- Log all import operations with summary stats
- Log search requests with filter usage
- Track error rates and response times

## Implementation Strategy

### Development Phases

**Phase 1: Foundation** (Copy & Adapt)
- Copy evaluations model → dormitory_bill model
- Simplify: remove nested fields, add billing fields
- Copy evaluations schemas → dormitory_bill schemas
- Simplify: flat structure, add amount fields

**Phase 2: Service Layer** (Reuse Pattern)
- Copy bulk import logic from evaluations service
- Adapt: JSON parsing instead of Excel
- Copy search logic from evaluations service
- Adapt: flat response, amount range filter

**Phase 3: API Layer** (Mirror Evaluations)
- Copy evaluations router structure
- Adapt: /dormitory-bills prefix, JSON body instead of file upload
- Keep: same auth pattern (admin/user), same error handling

**Phase 4: Integration** (Standard Process)
- Create Alembic migration
- Run migration
- Register router in main.py
- Test import and search

### Risk Mitigation

**Risk: Invalid employee_id in Import**
- Mitigation: Pre-validate all employee_id values before any DB operations
- Return detailed error list with row numbers

**Risk: Concurrent Import Conflicts**
- Mitigation: Database unique constraint + transaction isolation
- Let database handle race conditions

**Risk: Performance Degradation**
- Mitigation: Use proven bulk operations from evaluations
- Add database indexes on all search columns

### Testing Approach

**Unit Tests:**
- Service layer: bulk import with valid/invalid data
- Service layer: search with various filter combinations
- Validation: CHECK constraints enforced

**Integration Tests:**
- Import 100+ bills, verify created/updated counts
- Search with pagination, verify no duplicates
- Authorization: admin import, user search, guest blocked

**Performance Tests:**
- Import 1000+ bills, measure time (target < 5s)
- Search with filters, measure response time (target < 500ms)

## Task Breakdown Preview

High-level task categories (will be detailed during decomposition):

1. **Database Model & Migration** (2 hours)
   - Create DormitoryBill SQLAlchemy model with all constraints
   - Create Alembic migration with indexes
   - Run migration on dev database

2. **Pydantic Schemas** (1 hour)
   - Create request/response schemas
   - Add validation rules
   - Add OpenAPI examples

3. **Bulk Import Service** (2 hours)
   - Implement JSON parsing and validation
   - Implement bulk upsert logic (copy from evaluations)
   - Add employee_id FK validation

4. **Search Service** (1.5 hours)
   - Implement query building with filters
   - Add amount range filter logic
   - Implement pagination and sorting

5. **Import Endpoint** (1 hour)
   - Create POST /import with admin auth
   - Add request validation
   - Wire up to service layer

6. **Search Endpoint** (1 hour)
   - Create GET /search with auth
   - Add query parameter validation
   - Wire up to service layer

7. **Router Registration** (0.5 hours)
   - Register router in main.py
   - Test endpoints in OpenAPI docs

**Total Estimated Effort:** 9 hours (1.2 days)

## Dependencies

### Prerequisites (Must Exist)
- ✅ employees table with employee_id column
- ✅ Authentication system (require_role, require_authenticated_user)
- ✅ Database connection and session management
- ✅ Evaluations API (pattern to copy from)

### External Dependencies
- PostgreSQL 12+ with asyncpg driver
- SQLAlchemy 2.0+ with async support
- Alembic for migrations
- Pydantic 2.0+ for validation
- FastAPI for REST API

### No New Dependencies Needed
- Reuse existing libraries (no openpyxl needed for JSON)
- Reuse existing auth system
- Reuse existing database setup

## Success Criteria (Technical)

### Performance Benchmarks
- ✅ Import 1000 bills in < 5 seconds
- ✅ Search response time P95 < 500ms
- ✅ No N+1 query problems (single SELECT for existing records)
- ✅ Database indexes used (verify with EXPLAIN)

### Quality Gates
- ✅ All CHECK constraints pass (elec/water indexes, amounts >= 0)
- ✅ Unique constraint enforced (no duplicate bills)
- ✅ FK constraint enforced (invalid employee_id rejected)
- ✅ Admin-only import enforced (403 for non-admin)
- ✅ Guest users blocked (403 for all endpoints)

### Acceptance Criteria
- ✅ Can import 100+ bills via JSON in single request
- ✅ Upsert works correctly (updates existing, inserts new)
- ✅ Search with all filters works (employee_id, term_code, dorm_code, amount range)
- ✅ Pagination works (no duplicates, accurate total count)
- ✅ Default sort works (term_code DESC, created_at DESC)
- ✅ OpenAPI docs show both endpoints with examples

## Estimated Effort

**Total Development Time:** 9 hours (1.2 days)

**Breakdown:**
- Database & Models: 2 hours (20%)
- Service Layer: 3.5 hours (40%)
- API Endpoints: 2 hours (20%)
- Integration & Testing: 1.5 hours (20%)

**Confidence Level:** High
- Reusing proven patterns from evaluations API
- No new technologies or libraries
- Clear requirements with no ambiguity
- Small scope (2 endpoints, 1 table)

**Critical Path:**
1. Database model & migration (blocks everything)
2. Schemas (blocks service + endpoints)
3. Service layer (blocks endpoints)
4. Endpoints (blocks testing)

**Parallel Work Opportunities:**
- Import service and search service can be built in parallel
- Schemas can be designed while migration is being reviewed
- Testing can start once endpoints are complete

## Tasks Created
- [ ] #46 - Create database model and migration for dormitory_bills table (parallel: false)
- [ ] #47 - Create Pydantic schemas for dormitory bills API (parallel: false)
- [ ] #48 - Implement bulk import service with upsert logic (parallel: false)
- [ ] #49 - Implement search service with filters and pagination (parallel: true)
- [ ] #50 - Create import endpoint with admin authorization (parallel: false)
- [ ] #51 - Create search endpoint with authenticated user authorization (parallel: false)
- [ ] #52 - Register router and run database migration (parallel: false)

Total tasks: 7
Parallel tasks: 1
Sequential tasks: 6
Estimated total effort: 9 hours
