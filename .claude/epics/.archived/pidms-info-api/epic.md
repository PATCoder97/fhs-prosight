---
name: pidms-info-api
status: completed
created: 2026-01-12T07:12:00Z
updated: 2026-01-12T09:12:34Z
completed: 2026-01-12T09:12:34Z
progress: 100%
prd: .claude/prds/pidms-info-api.md
github: https://github.com/PATCoder97/fhs-prosight/issues/53
---

# Epic: pidms-info-api

## Overview

Implement a backend API system for managing Microsoft product license keys through PIDKey.com integration. This system enables IT administrators to validate keys, track activation counts, search inventory, and maintain centralized license management within the FHS ProSight platform.

**Core Capabilities:**
- External API integration with PIDKey.com for key validation
- Database storage of all key metadata (14 fields including remaining activations, blocked status)
- Fuzzy search across product types with filtering and pagination
- Bulk synchronization to keep activation counts current
- Admin-only authentication for security compliance

## Architecture Decisions

### 1. Integration Pattern: External HTTP Client
**Decision:** Create dedicated client in `integrations/pidkey_client.py` following existing FHSHRSClient pattern
**Rationale:**
- Separates external API concerns from business logic
- Reuses proven async httpx pattern from existing HRS integration
- Enables easy mocking for tests
- Centralizes error handling and retry logic

### 2. Data Model: Complete Field Mirroring
**Decision:** Store all 14 fields from PIDKey.com response without transformation
**Rationale:**
- Preserves data fidelity for future use cases
- Avoids data loss from field selection
- Enables accurate sync comparisons
- Minimal mapping logic reduces bugs

### 3. Search Strategy: SQL ILIKE with Indexes
**Decision:** Use PostgreSQL ILIKE for fuzzy product search with proper indexing
**Rationale:**
- Native database capability, no external search engine needed
- ILIKE on `prd` field handles partial matching ("Office" → "Office15_ProPlusVL_MAK")
- Indexes on prd, remaining, blocked ensure <100ms query times
- Sufficient for 10,000 key dataset

### 4. Sync Approach: Batch Processing with Error Isolation
**Decision:** Process keys in batches of 50, continue on individual failures
**Rationale:**
- Prevents timeout on large syncs (PIDKey.com has unknown rate limits)
- Isolates failures to individual keys (don't fail entire sync)
- Returns detailed error report for manual review
- Aligns with PIDKey.com API batch format

### 5. Authentication: Leverage Existing Admin System
**Decision:** Reuse existing admin role check from `app/core/security.py`
**Rationale:**
- No new auth code needed (zero cost)
- Consistent with other admin endpoints
- Already tested and deployed

## Technical Approach

### Backend Components

#### 1. PIDKey.com Integration Client (`integrations/pidkey_client.py`)
**Purpose:** HTTP wrapper for external API calls

**Key Methods:**
- `check_keys(keys: List[str]) -> List[dict]`: Validate keys against PIDKey.com
- `_format_keys(keys)`: Normalize keys with/without dashes to \r\n-separated format
- `_parse_response(json_array)`: Extract fields from API response
- Error handling: Retry 3x with exponential backoff, timeout 30s

**Dependencies:** httpx (async), logging

#### 2. Database Model (`models/pidms_key.py`)
**Purpose:** SQLAlchemy ORM model for pidms_keys table

**Schema:**
```python
class PIDMSKey(Base):
    __tablename__ = "pidms_keys"

    id: Mapped[int] = primary_key
    keyname: Mapped[str] = unique, indexed  # Without dashes
    keyname_with_dash: Mapped[str]
    prd: Mapped[str] = indexed              # Product code for search
    eid: Mapped[Optional[str]]
    is_key_type: Mapped[Optional[str]]
    is_retail: Mapped[Optional[int]]
    remaining: Mapped[int] = indexed        # Activation count
    blocked: Mapped[int] = indexed          # -1 or 1
    errorcode: Mapped[Optional[str]]
    sub: Mapped[Optional[str]]
    had_occurred: Mapped[Optional[int]]
    invalid: Mapped[Optional[int]]
    datetime_checked_done: Mapped[Optional[str]]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
```

**Indexes:** keyname (unique), prd, remaining, blocked

#### 3. Pydantic Schemas (`schemas/pidms.py`)
**Purpose:** Request/response validation

**Schemas:**
- `PIDMSKeyCheckRequest`: {"keys": str}  # Newline-separated
- `PIDMSKeyResponse`: Single key with all 14 fields + status
- `PIDMSCheckResponse`: {success, summary, results[]}
- `PIDMSSyncRequest`: {product_filter: Optional[str]}
- `PIDMSSyncResponse`: {success, summary, error_details[]}
- `PIDMSSearchParams`: Query params (product, min_remaining, max_remaining, blocked, page, page_size)
- `PIDMSSearchResponse`: {total, page, page_size, results[]}
- `PIDMSProductSummary`: {prd, key_count, total_remaining, avg_remaining, low_inventory}
- `PIDMSProductsResponse`: {products[]}

#### 4. Service Layer (`services/pidms_service.py`)
**Purpose:** Business logic orchestration

**Functions:**
```python
async def check_and_upsert_keys(db, keys_list, pidkey_client):
    """
    1. Call pidkey_client.check_keys(keys_list)
    2. For each key in response:
       - Query DB by keyname
       - If exists: UPDATE fields (upsert)
       - If new: INSERT new record
    3. Return summary: {new_keys, updated_keys, errors}
    """

async def sync_all_keys(db, pidkey_client, product_filter=None):
    """
    1. Fetch all keys from DB (optionally filtered by product)
    2. Batch keys into groups of 50
    3. For each batch: call check_and_upsert_keys()
    4. Aggregate results and errors
    5. Return sync summary
    """

async def search_keys(db, product, min_remaining, max_remaining, blocked, page, page_size):
    """
    1. Build query with filters:
       - product: WHERE prd ILIKE '%{product}%'
       - min_remaining: WHERE remaining >= min_remaining
       - max_remaining: WHERE remaining <= max_remaining
       - blocked: WHERE blocked == blocked
    2. Count total (for pagination)
    3. Apply ORDER BY prd, remaining DESC
    4. Apply LIMIT/OFFSET
    5. Return {total, page, page_size, results[]}
    """

async def get_product_summary(db):
    """
    1. GROUP BY prd
    2. Aggregate: COUNT(*), SUM(remaining), AVG(remaining)
    3. Flag low_inventory if total_remaining < 5
    4. Return products[]
    """
```

**Error Handling:** All functions use try/except with rollback on DB errors, log failures

#### 5. API Router (`routers/pidms.py`)
**Purpose:** FastAPI endpoints with admin auth

**Endpoints:**
```python
@router.post("/api/pidms/check", dependencies=[Depends(require_admin)])
async def check_keys(request: PIDMSKeyCheckRequest, db: AsyncSession):
    # Parse keys from request.keys (split by \r\n or \n)
    # Call service.check_and_upsert_keys()
    # Return PIDMSCheckResponse

@router.post("/api/pidms/sync", dependencies=[Depends(require_admin)])
async def sync_keys(request: PIDMSSyncRequest, db: AsyncSession):
    # Call service.sync_all_keys()
    # Return PIDMSSyncResponse

@router.get("/api/pidms/search", dependencies=[Depends(require_admin)])
async def search_keys(params: PIDMSSearchParams, db: AsyncSession):
    # Call service.search_keys()
    # Return PIDMSSearchResponse

@router.get("/api/pidms/products", dependencies=[Depends(require_admin)])
async def get_products(db: AsyncSession):
    # Call service.get_product_summary()
    # Return PIDMSProductsResponse
```

#### 6. Main App Registration (`main.py`)
**Purpose:** Register router

```python
from app.routers import pidms

app.include_router(pidms.router)
```

### Infrastructure

#### Database Migration
**Action:** Create Alembic migration for pidms_keys table

**Migration Script:**
```python
def upgrade():
    op.create_table(
        'pidms_keys',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('keyname', sa.String(255), unique=True, nullable=False),
        # ... 12 more columns
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now())
    )
    op.create_index('idx_pidms_keys_prd', 'pidms_keys', ['prd'])
    op.create_index('idx_pidms_keys_remaining', 'pidms_keys', ['remaining'])
    op.create_index('idx_pidms_keys_blocked', 'pidms_keys', ['blocked'])
```

#### Environment Configuration
**Action:** Add PIDKEY_API_KEY to .env

```bash
# .env
PIDKEY_API_KEY=nVHBz3RIsHpXHofLv3B89iFK8
```

**Load in settings:**
```python
# app/core/config.py
class Settings(BaseSettings):
    PIDKEY_API_KEY: str
    PIDKEY_BASE_URL: str = "https://pidkey.com/ajax/pidms_api"
```

## Implementation Strategy

### Simplified Approach
**Goal:** Minimize code by leveraging existing patterns

**Reuse Opportunities:**
1. **Integration Client Pattern:** Copy structure from `fhs_hrs_client.py` (async httpx, error handling, parsing)
2. **Service Layer Pattern:** Follow `dormitory_bill_service.py` structure (upsert logic, pagination, bulk operations)
3. **Router Pattern:** Reuse admin auth from `dormitory_bills.py` router
4. **Schema Pattern:** Follow `dormitory_bill.py` schema structure

**Simplifications:**
- No frontend (admin uses API directly or via tools like Postman/curl)
- No complex state management (stateless API)
- No installation tracking (out of scope per PRD)
- No cron job setup initially (manual sync via POST /sync)

### Development Phases

**Phase 1: Foundation (Core Infrastructure)**
- Create database model + migration
- Create Pydantic schemas
- Create PIDKey.com client with basic HTTP integration

**Phase 2: Core Functionality**
- Implement service layer (check_and_upsert, search, product_summary)
- Implement API router with 4 endpoints
- Register router in main.py

**Phase 3: Refinement**
- Add sync_all_keys functionality with batching
- Optimize database queries with proper indexes
- Add comprehensive error handling and logging

**Phase 4: Testing & Documentation**
- Manual testing with real PIDKey.com API
- Verify admin authentication works
- Document API endpoints in OpenAPI/Swagger

### Risk Mitigation

**Risk 1: PIDKey.com API Rate Limiting**
- Mitigation: Batch requests to 50 keys, implement exponential backoff
- Fallback: Return partial success with error details

**Risk 2: Database Performance**
- Mitigation: Proper indexes on prd, remaining, blocked columns
- Validation: Test with 10,000 keys, ensure <2s search times

**Risk 3: API Key Security**
- Mitigation: Store in environment variable, never log in responses
- Validation: Code review to ensure no API key leakage

## Tasks Created
- [ ] #54 - Create database model and migration for pidms_keys table (parallel: true)
- [ ] #55 - Create Pydantic schemas for all request/response types (parallel: true)
- [ ] #56 - Implement PIDKey.com integration client (parallel: true)
- [ ] #57 - Implement service layer core functions (parallel: false)
- [ ] #58 - Create API router with 4 endpoints (parallel: false)
- [ ] #59 - Register router in main.py and configure environment (parallel: false)
- [ ] #60 - Implement bulk sync functionality with batching (parallel: true)
- [ ] #61 - Test with real PIDKey.com API and verify all endpoints (parallel: true)
- [ ] #62 - Optimize queries and add comprehensive error handling (parallel: true)
- [ ] #63 - Documentation and deployment preparation (parallel: true)

**Total tasks:** 10
**Parallel tasks:** 7
**Sequential tasks:** 3
**Estimated total effort:** 35-44 hours (~5-6 days for 1 developer)
## Dependencies

### External Dependencies
- **PIDKey.com API:** Requires valid API key (user-provided: `nVHBz3RIsHpXHofLv3B89iFK8`)
  - Base URL: `https://pidkey.com/ajax/pidms_api`
  - Format: `?keys=KEY1\r\nKEY2&justgetdescription=0&apikey=xxxxx`
  - Risk: API downtime (mitigation: retry logic, graceful error messages)

### Internal Dependencies
- **Admin Authentication:** Already exists in `app/core/security.py` (zero implementation cost)
- **PostgreSQL Database:** Already configured with async SQLAlchemy
- **httpx Library:** Already in use for FHS HRS client integration
- **Alembic Migrations:** Already configured for database schema changes

### Team Dependencies
- **DevOps:** Configure PIDKEY_API_KEY environment variable in production/staging
- **Backend Team:** Implement all components (estimated: 1 developer, 5-7 days)

## Success Criteria (Technical)

### Performance Benchmarks
- [ ] PIDKey.com API calls complete within 30 seconds (timeout enforced)
- [ ] Search queries return within 2 seconds for 10,000 key dataset
- [ ] Database queries use indexes (verify with EXPLAIN ANALYZE)
- [ ] Batch sync of 200 keys completes within 2 minutes

### Quality Gates
- [ ] All endpoints require admin authentication (401 for non-admin users)
- [ ] PIDKEY_API_KEY never appears in logs or responses
- [ ] Database transactions are atomic (rollback on errors)
- [ ] Fuzzy search returns correct results (manual testing: "Office" → all Office products)

### Acceptance Criteria
- [ ] POST /api/pidms/check successfully imports new keys and updates existing keys
- [ ] GET /api/pidms/search supports partial product matching with pagination
- [ ] GET /api/pidms/products returns aggregated statistics grouped by product
- [ ] POST /api/pidms/sync updates all keys in batches without failure
- [ ] All 14 fields from PIDKey.com response are stored correctly in database

## Estimated Effort

### Overall Timeline
- **Total Development:** 5-7 days (1 backend developer)
- **Testing & Refinement:** 2-3 days
- **Total:** ~2 weeks to production-ready

### Task Effort Breakdown
| Task | Effort | Notes |
|------|--------|-------|
| Database model + migration | 0.5 day | Straightforward SQLAlchemy model |
| Pydantic schemas | 0.5 day | 8 schemas, follow existing patterns |
| PIDKey.com client | 1 day | HTTP integration, error handling, retry logic |
| Service layer | 2 days | Core business logic (upsert, search, aggregation) |
| API router | 1 day | 4 endpoints with admin auth |
| Bulk sync + batching | 1 day | Batch processing logic |
| Integration + testing | 2 days | Real API testing, edge cases |
| Documentation | 0.5 day | OpenAPI/Swagger, README |

### Critical Path Items
1. **PIDKey.com API Access:** Must have valid API key before development starts
2. **Database Migration:** Must run before testing endpoints
3. **Admin Auth Testing:** Verify existing admin system works with new endpoints

### Resource Requirements
- 1 Backend Developer (Python/FastAPI experience)
- Access to PIDKey.com API key
- PostgreSQL database (already available)
- Staging environment for testing

## Notes

**Optimization Opportunities:**
- Leverage existing patterns from dormitory_bill and fhs_hrs implementations (80% code reuse for structure)
- Use SQLAlchemy's bulk_insert_mappings for faster batch inserts if >1000 keys
- Consider Redis caching for product_summary endpoint (low priority, only if needed)

**Future Enhancements (Post-Epic):**
- Scheduled cron job for daily auto-sync
- Email notifications for low inventory products
- Frontend admin dashboard for visual key management
- Export to CSV/Excel functionality
