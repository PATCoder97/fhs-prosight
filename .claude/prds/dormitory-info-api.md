---
name: dormitory-info-api
description: Dormitory billing management API with JSON import and search capabilities
status: backlog
created: 2026-01-12T03:03:10Z
---

# PRD: Dormitory Billing Management API

## Executive Summary

Build a dormitory billing management system that enables bulk import via JSON and flexible search capabilities. The system stores detailed billing information for employee dormitory usage, including electricity, water, and management fees, with support for upsert operations based on composite keys (employee_id, term_code, dorm_code).

**Key Value Propositions:**
- Streamlined bulk billing data import via JSON API
- Comprehensive search with multiple filters and pagination
- Automated bill calculation tracking (electricity, water, fees)
- Role-based access control (admin import, authenticated search)

## Problem Statement

### Current Challenges
- Manual dormitory billing management is time-consuming and error-prone
- No centralized system to track employee dormitory fees across multiple periods
- Difficulty in searching and analyzing billing data by room, employee, or period
- Need for automated import process to handle bulk billing updates

### Why Now?
- Growing number of employees using company dormitories
- Need for transparent billing system for employees to verify their charges
- Integration with existing HR system (employees table via employee_id FK)
- Foundation for future payroll deduction integration

## User Stories

### Primary Personas

**1. Admin (Dormitory Manager)**
- Role: Manages dormitory billing data
- Goals: Import/update billing data efficiently, ensure accuracy
- Pain points: Manual data entry, handling duplicate records

**2. Authenticated Employee**
- Role: Regular employee using dormitory
- Goals: Search and verify their own bills, understand charges
- Pain points: Lack of visibility into billing details

**3. HR Manager**
- Role: Oversees employee benefits and facilities
- Goals: Access comprehensive billing reports, analyze trends
- Pain points: No centralized query system

### User Journeys

#### Journey 1: Admin Imports Monthly Bills
```
1. Admin receives billing data from facility management team (JSON format)
2. Admin logs into system with admin credentials
3. Admin calls POST /api/dormitory-bills/import with JSON payload
4. System validates data (employee_id exists, amounts are valid)
5. System performs bulk upsert (update existing, insert new)
6. System returns summary: {created: 120, updated: 30, errors: 2}
7. Admin reviews error details and fixes data issues
```

#### Journey 2: Employee Searches Their Bills
```
1. Employee logs into system
2. Employee navigates to dormitory bills section
3. Employee enters search criteria (employee_id, term_code)
4. System returns paginated results with all billing details
5. Employee reviews electricity usage, water usage, and total charges
6. Employee can filter by specific term or room
```

#### Journey 3: HR Manager Analyzes Billing Trends
```
1. HR Manager logs in with authenticated account
2. HR Manager searches bills by term_code (e.g., "25A")
3. System returns all bills for that period
4. HR Manager uses pagination to browse through records
5. HR Manager can filter by total_amount range to identify outliers
```

## Requirements

### Functional Requirements

#### FR1: JSON Bulk Import (Admin Only)
**Endpoint:** `POST /api/dormitory-bills/import`

**Request Body:**
```json
{
  "bills": [
    {
      "employee_id": "VNW0012345",
      "term_code": "25A",
      "dorm_code": "A01",
      "factory_location": "North Wing",
      "elec_last_index": 100.5,
      "elec_curr_index": 150.3,
      "elec_usage": 49.8,
      "elec_amount": 249000,
      "water_last_index": 50.2,
      "water_curr_index": 65.7,
      "water_usage": 15.5,
      "water_amount": 77500,
      "shared_fee": 50000,
      "management_fee": 100000,
      "total_amount": 476500
    }
  ]
}
```

**Business Logic:**
- Validate all employee_id values exist in employees table
- Validate numeric fields (amounts >= 0, curr_index >= last_index)
- Calculate usage if not provided: `elec_usage = elec_curr_index - elec_last_index`
- Calculate total if not provided: `total_amount = elec_amount + water_amount + shared_fee + management_fee`
- Upsert based on composite key (employee_id, term_code, dorm_code)
- If record exists: UPDATE all fields, set updated_at = NOW()
- If record is new: INSERT, set created_at = NOW()
- Use bulk operations for performance (similar to evaluations API optimization)

**Response:**
```json
{
  "success": true,
  "summary": {
    "total_records": 150,
    "created": 120,
    "updated": 30,
    "errors": 0
  },
  "error_details": []
}
```

**Error Handling:**
- 400: Invalid JSON format, missing required fields
- 403: Non-admin user attempting import
- 422: Validation errors (invalid employee_id, negative amounts)
- 500: Database errors

#### FR2: Search Bills (Authenticated Users)
**Endpoint:** `GET /api/dormitory-bills/search`

**Query Parameters:**
- `employee_id` (optional): Exact match filter (e.g., "VNW0012345")
- `term_code` (optional): Exact match filter (e.g., "25A")
- `dorm_code` (optional): Exact match filter (e.g., "A01")
- `min_amount` (optional): Minimum total_amount filter (e.g., 100000)
- `max_amount` (optional): Maximum total_amount filter (e.g., 500000)
- `page` (required): Page number, default 1, min 1
- `page_size` (required): Items per page, default 50, min 1, max 100

**Business Logic:**
- All authenticated users can search all bills (no restriction by employee_id)
- Apply filters conditionally (only if provided)
- Default sort: term_code DESC, created_at DESC
- Pagination using LIMIT/OFFSET
- Count total matching records before pagination

**Response:**
```json
{
  "total": 250,
  "page": 1,
  "page_size": 50,
  "results": [
    {
      "bill_id": 1234,
      "employee_id": "VNW0012345",
      "term_code": "25A",
      "dorm_code": "A01",
      "factory_location": "North Wing",
      "elec_last_index": 100.5,
      "elec_curr_index": 150.3,
      "elec_usage": 49.8,
      "elec_amount": 249000,
      "water_last_index": 50.2,
      "water_curr_index": 65.7,
      "water_usage": 15.5,
      "water_amount": 77500,
      "shared_fee": 50000,
      "management_fee": 100000,
      "total_amount": 476500,
      "created_at": "2026-01-12T03:00:00Z",
      "updated_at": null
    }
  ]
}
```

**Error Handling:**
- 403: Guest user attempting search
- 422: Invalid pagination parameters (page < 1, page_size > 100)
- 500: Database errors

### Non-Functional Requirements

#### NFR1: Performance
- Bulk import: Process 1000+ records in < 5 seconds using bulk INSERT/UPDATE
- Search: Return results in < 500ms for typical queries
- Database indexes on: employee_id, term_code, dorm_code, created_at
- Composite index on (term_code DESC, created_at DESC) for default sort

#### NFR2: Data Integrity
- Foreign key constraint: employee_id REFERENCES employees(employee_id)
- Unique constraint: (employee_id, term_code, dorm_code)
- Check constraints:
  - elec_curr_index >= elec_last_index
  - water_curr_index >= water_last_index
  - All amount fields >= 0
- Nullable updated_at (only set on updates)

#### NFR3: Security
- Admin authorization required for import endpoint (require_role("admin"))
- Authenticated user authorization for search (require_authenticated_user)
- Guest users blocked from all endpoints (403 Forbidden)
- Input validation to prevent SQL injection
- Rate limiting on import endpoint (max 10 requests/minute per user)

#### NFR4: Scalability
- Support up to 100,000 bill records per year
- Handle concurrent imports from multiple admins
- Efficient pagination for large result sets

#### NFR5: Maintainability
- Follow existing codebase patterns (similar to evaluations API)
- Comprehensive logging for imports and searches
- Clear error messages for validation failures
- OpenAPI documentation for all endpoints

## Success Criteria

### Metrics
1. **Import Success Rate:** > 95% of valid records imported without errors
2. **Search Performance:** Average response time < 500ms
3. **User Adoption:** > 80% of dormitory users search their bills monthly
4. **Data Accuracy:** Zero duplicate records (enforced by unique constraint)

### Acceptance Criteria
- Admin can import 1000+ bills via JSON in single request
- System correctly upserts records (updates existing, inserts new)
- All authenticated users can search bills with filters
- Pagination works correctly (no duplicates, accurate counts)
- Guest users are blocked (403 response)
- Bills sorted by term_code DESC by default
- Total amount range filter works correctly

## Technical Specifications

### Database Schema

```sql
CREATE TABLE dormitory_bills (
    bill_id BIGSERIAL PRIMARY KEY,

    -- Foreign key to employees table
    employee_id VARCHAR(20) NOT NULL REFERENCES employees(employee_id),

    -- Term code (25, 25A, 25B, 251, 252, etc.)
    term_code VARCHAR(10) NOT NULL,

    -- Room code (A01, B02, P001, etc.)
    dorm_code VARCHAR(20) NOT NULL,

    -- Factory location/wing
    factory_location VARCHAR(100),

    -- Electricity billing
    elec_last_index NUMERIC(10, 2) DEFAULT 0,
    elec_curr_index NUMERIC(10, 2) DEFAULT 0,
    elec_usage NUMERIC(10, 2) DEFAULT 0,
    elec_amount NUMERIC(15, 2) DEFAULT 0,

    -- Water billing
    water_last_index NUMERIC(10, 2) DEFAULT 0,
    water_curr_index NUMERIC(10, 2) DEFAULT 0,
    water_usage NUMERIC(10, 2) DEFAULT 0,
    water_amount NUMERIC(15, 2) DEFAULT 0,

    -- Additional fees
    shared_fee NUMERIC(15, 2) DEFAULT 0,
    management_fee NUMERIC(15, 2) DEFAULT 0,

    -- Total amount
    total_amount NUMERIC(15, 2) DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NULL,

    -- Constraints
    CONSTRAINT uq_bill_entry UNIQUE (employee_id, term_code, dorm_code),
    CONSTRAINT chk_elec_index CHECK (elec_curr_index >= elec_last_index),
    CONSTRAINT chk_water_index CHECK (water_curr_index >= water_last_index),
    CONSTRAINT chk_amounts CHECK (
        total_amount >= 0 AND
        elec_amount >= 0 AND
        water_amount >= 0 AND
        shared_fee >= 0 AND
        management_fee >= 0
    )
);

-- Indexes for performance
CREATE INDEX idx_dormitory_bills_employee_id ON dormitory_bills(employee_id);
CREATE INDEX idx_dormitory_bills_term_code ON dormitory_bills(term_code);
CREATE INDEX idx_dormitory_bills_dorm_code ON dormitory_bills(dorm_code);
CREATE INDEX idx_dormitory_bills_total_amount ON dormitory_bills(total_amount);
CREATE INDEX idx_dormitory_bills_sort ON dormitory_bills(term_code DESC, created_at DESC);
```

### API Architecture

**Technology Stack:**
- FastAPI for REST API framework
- SQLAlchemy ORM with AsyncSession
- Alembic for database migrations
- Pydantic for request/response validation
- Python asyncio for async operations

**File Structure:**
```
backend/
├── app/
│   ├── models/
│   │   └── dormitory_bill.py          # SQLAlchemy model
│   ├── schemas/
│   │   └── dormitory_bill.py          # Pydantic schemas
│   ├── services/
│   │   └── dormitory_bill_service.py  # Business logic
│   ├── routers/
│   │   └── dormitory_bills.py         # API endpoints
│   └── main.py                        # Register router
├── alembic/
│   └── versions/
│       └── xxx_add_dormitory_bills_table.py
```

**Pydantic Schemas:**
```python
class DormitoryBillBase(BaseModel):
    employee_id: str
    term_code: str
    dorm_code: str
    factory_location: Optional[str] = None
    elec_last_index: float = 0
    elec_curr_index: float = 0
    elec_usage: float = 0
    elec_amount: float = 0
    water_last_index: float = 0
    water_curr_index: float = 0
    water_usage: float = 0
    water_amount: float = 0
    shared_fee: float = 0
    management_fee: float = 0
    total_amount: float = 0

class DormitoryBillImport(BaseModel):
    bills: List[DormitoryBillBase]

class DormitoryBillResponse(DormitoryBillBase):
    bill_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

class SearchResponse(BaseModel):
    total: int
    page: int
    page_size: int
    results: List[DormitoryBillResponse]

class ImportSummary(BaseModel):
    success: bool
    summary: dict
    error_details: List[dict]
```

### Performance Optimization

**Bulk Import Strategy:**
1. Parse JSON and validate all records
2. Fetch all existing records in ONE query using OR conditions on composite keys
3. Create hashmap of existing records by (employee_id, term_code, dorm_code)
4. Separate records into inserts vs updates
5. Bulk insert using `db.add_all()` - single INSERT with multiple VALUES
6. Updates tracked automatically by SQLAlchemy session
7. Single commit at the end

Expected performance: 100-1000x faster than row-by-row processing

## Constraints & Assumptions

### Technical Constraints
- Must integrate with existing employees table via employee_id FK
- Must follow existing authentication/authorization patterns
- Must use PostgreSQL database (BIGSERIAL, NUMERIC types)
- Must maintain backwards compatibility with existing API patterns

### Business Constraints
- Only admin users can import/modify billing data
- Historical bills cannot be deleted (audit trail requirement)
- Term codes follow existing convention (25, 25A, 25B, 251, 252)

### Assumptions
- Employee records exist before bill import (FK constraint enforced)
- Billing data provided by facility management is accurate
- Users understand term_code convention
- JSON import format is consistent and validated before upload

## Out of Scope

Explicitly NOT included in this PRD:

1. **Export functionality** - No Excel/CSV export endpoint
2. **Statistics/Analytics API** - No aggregation endpoints (sum by term, average by room, etc.)
3. **Bill deletion** - No DELETE endpoint (audit trail preservation)
4. **Email notifications** - No automated bill notifications to employees
5. **Payment integration** - No payment processing or payroll deduction
6. **File upload** - JSON only, no file upload endpoint
7. **Bill approval workflow** - No multi-stage approval process
8. **Historical data migration** - No automatic migration of legacy billing data
9. **Real-time meter reading integration** - Manual data import only
10. **Mobile app** - Web API only, no mobile-specific features

## Dependencies

### External Dependencies
- **employees table:** Must exist with employee_id as unique key
- **Authentication system:** require_role("admin"), require_authenticated_user
- **Database:** PostgreSQL 12+ with asyncpg driver
- **Libraries:** openpyxl (already installed), SQLAlchemy, Alembic, Pydantic

### Internal Team Dependencies
- **Backend team:** API implementation
- **Database team:** Migration execution, index optimization
- **DevOps team:** Deployment, monitoring setup
- **QA team:** Test data preparation, validation testing

### Timeline Dependencies
- Must complete after employees table is stable
- Should complete before next billing cycle (end of month)
- No dependency on frontend implementation (API-first approach)

## Implementation Phases

### Phase 1: Database & Models (Estimated: 2 hours)
- Create Alembic migration for dormitory_bills table
- Implement SQLAlchemy model with all constraints
- Add indexes for performance
- Run migration on development database

### Phase 2: Core Service Layer (Estimated: 4 hours)
- Implement bulk import service with upsert logic
- Implement search service with filters and pagination
- Add validation logic (employee_id exists, amounts valid)
- Optimize with bulk operations (single SELECT, bulk INSERT)

### Phase 3: API Endpoints (Estimated: 3 hours)
- Create POST /import endpoint with admin authorization
- Create GET /search endpoint with authenticated user authorization
- Add Pydantic schemas for request/response validation
- Add comprehensive OpenAPI documentation

### Phase 4: Integration & Testing (Estimated: 3 hours)
- Register router in main.py
- Integration testing with real data
- Performance testing (1000+ records import)
- Authorization testing (admin, user, guest)

**Total Estimated Time:** 12 hours (1.5 days)

## Success Metrics & Monitoring

### KPIs to Track
1. **Import volume:** Number of bills imported per month
2. **Import success rate:** Percentage of records successfully imported
3. **Search usage:** Number of search requests per day
4. **Error rate:** Percentage of failed requests (target < 1%)
5. **Response time:** P95 latency for search endpoint (target < 500ms)

### Monitoring & Alerts
- Log all import operations with summary stats
- Alert on import failures > 5% error rate
- Monitor search query performance (slow queries > 1s)
- Track authorization failures (potential security issues)

### Post-Launch Review (After 1 Month)
- Review user adoption rate
- Analyze common search patterns
- Identify performance bottlenecks
- Gather user feedback for improvements

## Risks & Mitigation

### Risk 1: Invalid employee_id in Import Data
**Impact:** Import failures, data inconsistency
**Probability:** Medium
**Mitigation:** Pre-validate all employee_id values, return detailed error messages, support partial import success

### Risk 2: Large Dataset Performance Issues
**Impact:** Slow imports, timeout errors
**Probability:** Low (with bulk operations)
**Mitigation:** Use bulk insert/update, add database indexes, implement request timeout limits

### Risk 3: Concurrent Import Conflicts
**Impact:** Race conditions, duplicate records
**Probability:** Low
**Mitigation:** Database unique constraint enforcement, transaction isolation, optimistic locking

### Risk 4: Missing Authorization Checks
**Impact:** Security vulnerability, unauthorized data access
**Probability:** Very Low
**Mitigation:** Code review, security testing, follow existing auth patterns

## Appendix

### Sample JSON Import Payload
```json
{
  "bills": [
    {
      "employee_id": "VNW0012345",
      "term_code": "25A",
      "dorm_code": "A01",
      "factory_location": "North Wing Building A",
      "elec_last_index": 1000.5,
      "elec_curr_index": 1250.3,
      "elec_usage": 249.8,
      "elec_amount": 1249000,
      "water_last_index": 500.2,
      "water_curr_index": 565.7,
      "water_usage": 65.5,
      "water_amount": 327500,
      "shared_fee": 100000,
      "management_fee": 200000,
      "total_amount": 1876500
    },
    {
      "employee_id": "VNW0012346",
      "term_code": "25A",
      "dorm_code": "A02",
      "factory_location": "North Wing Building A",
      "elec_last_index": 800.0,
      "elec_curr_index": 950.5,
      "elec_usage": 150.5,
      "elec_amount": 752500,
      "water_last_index": 300.0,
      "water_curr_index": 340.2,
      "water_usage": 40.2,
      "water_amount": 201000,
      "shared_fee": 100000,
      "management_fee": 200000,
      "total_amount": 1253500
    }
  ]
}
```

### Sample Search Request
```
GET /api/dormitory-bills/search?term_code=25A&min_amount=1000000&max_amount=2000000&page=1&page_size=20
```

### Glossary
- **term_code:** Billing period identifier (e.g., "25" = year 2025, "25A" = Jan 2025, "251" = Q1 2025)
- **dorm_code:** Unique room identifier (e.g., "A01" = Building A Room 01)
- **bill_id:** Auto-generated unique identifier for each bill record
- **upsert:** Operation that updates if record exists, inserts if new
- **composite key:** Multiple columns used together to uniquely identify a record

---

**Document Version:** 1.0
**Last Updated:** 2026-01-12T03:03:10Z
**Status:** Ready for Implementation
