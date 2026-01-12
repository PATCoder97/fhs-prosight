---
name: evaluations-info-api
status: completed
created: 2026-01-10T09:07:37Z
updated: 2026-01-12T00:27:16Z
progress: 100%
prd: .claude/prds/evaluations-info-api.md
github: https://github.com/PATCoder97/fhs-prosight/issues/37
merged_at: 2026-01-12T00:27:16Z
---

# Epic: Employee Evaluations Management API

## Overview

Build a complete employee evaluation management system that enables Excel-based bulk imports and flexible search capabilities. This system stores multi-level evaluation data (department + management office reviews) with support for upsert operations based on composite keys (term_code, employee_id).

**Key Technical Characteristics**:
- Excel file processing with openpyxl library (27-column mapping)
- Transaction-based upsert logic (UPDATE if exists, INSERT if new)
- Two REST endpoints: POST /upload (admin only), GET /search (authenticated)
- 30+ database fields tracking dual-level evaluations (初核/複核/核定)
- Pagination support for search results (50 per page default)

## Architecture Decisions

### 1. Database Design
**Decision**: Single `evaluations` table with all fields, unique constraint on (term_code, employee_id)
**Rationale**:
- Evaluation data is flat (no normalized relationships needed)
- Composite unique key ensures no duplicate records per term/employee
- Indexes on term_code, employee_id, dept_code optimize search queries
- SQLAlchemy ORM handles upsert logic with session.merge() or manual SELECT→UPDATE/INSERT

### 2. Excel Processing Library
**Decision**: Use openpyxl for Excel file parsing
**Rationale**:
- Industry-standard Python library for .xlsx files
- Read-only mode is memory-efficient for large files
- Direct cell access with column mapping
- No external service dependencies (serverless processing)

### 3. Upsert Strategy
**Decision**: Check existence first, then UPDATE or INSERT within transaction
**Rationale**:
- PostgreSQL/MySQL native UPSERT (ON CONFLICT) not available in all SQLAlchemy versions
- Manual approach gives clear control over created vs updated counts
- Transaction ensures atomicity (all rows succeed or rollback)
- Logging per-row operations aids debugging

### 4. Authorization Model
**Decision**: Admin-only upload, authenticated-only search (blocks guests)
**Rationale**:
- Upload modifies data → requires elevated privileges (admin role)
- Search is read-only → allow all authenticated users (employees viewing evaluations)
- Consistent with existing HRS API authorization patterns (require_admin, require_authenticated_user)
- Guest blocking prevents public exposure of evaluation data

### 5. Response Structure for Search
**Decision**: Nested structure with dept_evaluation and mgr_evaluation groups
**Rationale**:
- Better UX than 18 flat fields (init/review/final × 2 × 3 subfields)
- Matches logical grouping in business domain (department vs management office)
- Easier for frontend to render in grouped tables/cards
- Aligns with PRD's sample response format

### 6. File Upload Handling
**Decision**: Save uploaded file to temp location, process, then delete
**Rationale**:
- openpyxl requires file on disk (cannot read from bytes stream efficiently)
- Temp file cleanup prevents storage bloat
- FastAPI's UploadFile provides streaming interface
- Error handling ensures cleanup even on failure

## Technical Approach

### Backend Services

**No Frontend Changes**: This is a pure backend API addition.

#### 1. Database Model Layer (`backend/app/models/evaluation.py`)
- Create `Evaluation` SQLAlchemy model with 30+ fields
- Define unique constraint: `UniqueConstraint('term_code', 'employee_id', name='uq_evaluations_term_employee')`
- Add indexes: `Index('ix_evaluations_term_code', 'term_code')`, `Index('ix_evaluations_employee_id', 'employee_id')`, `Index('ix_evaluations_dept_code', 'dept_code')`
- Include timestamps: `created_at`, `updated_at` (server_default, onupdate)
- All fields nullable except `term_code` and `employee_id`

#### 2. Database Migration (`backend/alembic/versions/xxx_add_evaluations_table.py`)
- Generate migration: `alembic revision -m "Add evaluations table"`
- Create table with all columns
- Add unique constraint and indexes
- Run migration: `alembic upgrade head`

#### 3. Pydantic Schemas Layer (`backend/app/schemas/evaluation.py`)
- Add `EvaluationLevel` model (score, comment, reviewer) - reusable for init/review/final
- Add `EvaluationGroup` model (init, review, final) - reusable for dept/mgr
- Add `EvaluationResponse` model with nested dept_evaluation and mgr_evaluation
- Add `SearchResponse` model with pagination (total, page, page_size, results)
- Add `UploadSummary` model (success, summary dict, error_details list)
- Use Optional[] for all nullable fields

#### 4. Service Layer - Upload (`backend/app/services/evaluation_service.py`)
- Add `upload_evaluations_from_excel(db: AsyncSession, file_path: str) -> dict` async method
- Open Excel file with openpyxl (read_only=True)
- Validate header row contains all required columns (評核年月, 工號)
- For each data row:
  - Map columns using EXCEL_COLUMN_MAPPING dictionary
  - Validate term_code and employee_id not empty
  - Check if record exists: `SELECT id FROM evaluations WHERE term_code=X AND employee_id=Y`
  - If exists: UPDATE with new values, increment `updated` counter
  - If not exists: INSERT new record, increment `created` counter
  - Handle errors: catch exceptions, append to error_details list
- Commit transaction
- Return dict: {success: True, summary: {total_rows, created, updated, errors}, error_details: [...]}

#### 5. Service Layer - Search (`backend/app/services/evaluation_service.py`)
- Add `search_evaluations(db: AsyncSession, employee_id: str, term_code: str, dept_code: str, page: int, page_size: int) -> dict` async method
- Build query: `SELECT * FROM evaluations`
- Apply filters:
  - If employee_id: `WHERE employee_id = employee_id`
  - If term_code: `WHERE term_code = term_code`
  - If dept_code: `WHERE dept_code LIKE 'dept_code%'` (starts with)
- Count total results (before pagination)
- Apply pagination: `LIMIT page_size OFFSET (page-1)*page_size`
- Transform results to nested structure (group init/review/final fields)
- Return dict: {total, page, page_size, results: [...]}

#### 6. Router Layer (`backend/app/routers/evaluations.py`)
- Add `POST /upload` endpoint
  - Request: `file: UploadFile = File(...)`
  - Authorization: `require_admin` dependency (blocks non-admin)
  - Business logic:
    1. Validate file extension (.xlsx, .xls)
    2. Save to temp file: `tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')`
    3. Call `evaluation_service.upload_evaluations_from_excel(db, temp_path)`
    4. Delete temp file: `os.unlink(temp_path)`
    5. Return UploadSummary
  - Response model: UploadSummary
  - Error handling: 400 (invalid file), 403 (not admin), 413 (file too large), 500 (processing error)

- Add `GET /search` endpoint
  - Query parameters: employee_id, term_code, dept_code, page, page_size
  - Authorization: `require_authenticated_user` dependency (blocks guest)
  - Call `evaluation_service.search_evaluations(...)`
  - Response model: SearchResponse
  - Error handling: 403 (guest), 422 (invalid params)

#### 7. Main App Integration (`backend/app/main.py`)
- Import evaluations router: `from app.routers import evaluations`
- Register router: `app.include_router(evaluations.router, prefix="/api/evaluations", tags=["evaluations"])`

#### 8. Dependencies (`backend/requirements.txt`)
- Add `openpyxl>=3.1.0` for Excel file processing

### Infrastructure

**Database**:
- New table: `evaluations` (will be created via Alembic migration)
- No changes to existing tables

**Environment Variables**:
- No new environment variables needed (reuses existing DB connection)

**File Storage**:
- Temporary file storage for Excel uploads (OS temp directory)
- Files deleted immediately after processing

**Authorization**:
- Reuse existing `require_admin` dependency for upload
- Reuse existing `require_authenticated_user` dependency for search
- No new auth logic needed

## Implementation Strategy

### Development Phases

**Single Phase Implementation** (7 sequential tasks):
1. Model + Migration → 2. Schemas → 3. Upload Service → 4. Upload Endpoint → 5. Search Service → 6. Search Endpoint → 7. Integration

**Rationale**: Tasks have strict dependencies (database → schemas → services → endpoints)

### Risk Mitigation

| Risk | Mitigation Strategy |
|------|---------------------|
| Excel file corrupted or invalid format | Validate file extension first, catch openpyxl exceptions, return 400 with clear error |
| Missing required columns in Excel | Read header row first, check for "評核年月" and "工號", return 400 if missing |
| Large Excel files (>1000 rows) timeout | Process rows sequentially (no batch), increase endpoint timeout to 60s, log progress |
| Duplicate rows in Excel (same term+employee) | Last row wins (UPDATE overwrites), log warning in summary |
| Database deadlock during upsert | Use transaction with retry logic, process rows in consistent order (sorted by term_code) |
| Unauthorized upload attempts | Enforce `require_admin` in dependency, log unauthorized attempts, return 403 |

### Testing Approach

**Per user request: No tests or documentation**

Manual testing only:
- Upload Excel with 100+ rows, verify created/updated counts
- Test upsert: upload same file twice, verify second upload updates (not creates)
- Test search filters: employee_id exact match, term_code exact match, dept_code prefix match
- Test pagination: page=1, page=2, verify no duplicates
- Test admin authorization: upload with non-admin user → 403
- Test guest blocking: search with guest token → 403
- Test invalid file: upload .txt file → 400
- Test missing columns: upload Excel without "工號" → 400

## Task Breakdown Preview

7 tasks total (database → schemas → services → endpoints → integration):

- [ ] **Task 1: Create database model and migration** - Evaluation SQLAlchemy model, Alembic migration, run migration (~2 hours)
- [ ] **Task 2: Create Pydantic schemas** - EvaluationLevel, EvaluationGroup, EvaluationResponse, SearchResponse, UploadSummary (~1 hour)
- [ ] **Task 3: Implement Excel upload service** - Parse Excel with openpyxl, upsert logic, error handling (~3 hours)
- [ ] **Task 4: Create upload endpoint** - POST /upload with admin auth, file handling, temp file cleanup (~2 hours)
- [ ] **Task 5: Implement search service** - Query building with filters, pagination, nested response transformation (~2 hours)
- [ ] **Task 6: Create search endpoint** - GET /search with authenticated user check, query params validation (~1 hour)
- [ ] **Task 7: Register router and add dependencies** - Update main.py, add openpyxl to requirements.txt (~1 hour)

**Total new code**: ~600-700 lines across 7 files

## Dependencies

### External Dependencies
- openpyxl library (to be added to requirements.txt)
- PostgreSQL/MySQL database (existing)

### Internal Dependencies
- FastAPI router infrastructure (existing)
- SQLAlchemy AsyncSession (existing)
- Authorization dependencies: require_admin, require_authenticated_user (existing)
- Database connection pool (existing)

### Prerequisite Work
None - all infrastructure exists from previous HRS APIs (salary, achievement, year-bonus)

## Success Criteria (Technical)

### Performance
- [ ] Excel upload with 1000 rows completes in < 30 seconds
- [ ] Search API response time < 500ms (without network latency)
- [ ] No memory leaks during large file processing
- [ ] Database indexes used for search queries (verify with EXPLAIN)

### Quality
- [ ] All 7 files created/modified successfully
- [ ] No breaking changes to existing endpoints
- [ ] Upsert logic correctly updates existing records (no duplicates)
- [ ] Error handling for all edge cases (400, 401, 403, 413, 422, 500)
- [ ] Temp files cleaned up even on errors (try/finally block)

### Security
- [ ] Admin-only upload enforced (non-admin → 403)
- [ ] Guest users blocked from search (403)
- [ ] JWT authentication enforced on both endpoints
- [ ] Excel data sanitized (no SQL injection via column values)
- [ ] File size validation (max 10MB)

### Functional
- [ ] Excel parsing maps all 27 columns correctly
- [ ] Upsert based on (term_code, employee_id) works correctly
- [ ] Search filters work: employee_id (exact), term_code (exact), dept_code (prefix)
- [ ] Pagination returns correct total count and page results
- [ ] Nested response structure matches PRD (dept_evaluation, mgr_evaluation)
- [ ] Upload summary includes created/updated/errors counts
- [ ] Error details list specific rows that failed

## Estimated Effort

**Total**: 12 hours (~1.5 days)

Breakdown:
- Task 1 (Model + Migration): 2 hours
- Task 2 (Schemas): 1 hour
- Task 3 (Upload Service): 3 hours
- Task 4 (Upload Endpoint): 2 hours
- Task 5 (Search Service): 2 hours
- Task 6 (Search Endpoint): 1 hour
- Task 7 (Integration): 1 hour

**Critical Path**: Sequential execution (Task 1 → 2 → 3 → 4 → 5 → 6 → 7)

**Resource Requirements**: 1 backend developer familiar with FastAPI, SQLAlchemy, and Excel processing

**No parallel work possible** due to strict layer dependencies

## Notes

### Code Reuse Opportunities
- Reuse authorization dependencies (require_admin, require_authenticated_user) from existing HRS APIs
- Follow same service layer pattern as salary/achievement/year-bonus APIs
- Use existing database session management (get_db dependency)
- Leverage FastAPI's File upload handling (same as other file uploads)

### Simplifications Applied
- Skip tests and documentation (per user request)
- Single table design (no joins needed)
- Manual upsert logic (not using database-specific UPSERT syntax for portability)
- Sequential row processing (no parallelization needed for <1000 rows)
- No Excel export (upload only)
- No workflow/approval system (direct database insert/update)

### Key Differences from Previous HRS APIs
- **Data Source**: Excel upload (not HRS API calls)
- **Authorization**: Two-tier (admin for upload, authenticated for search) vs single-tier
- **Data Structure**: Nested evaluation groups (dept/mgr) vs flat fields
- **Operation Type**: Write + Read (upload + search) vs Read-only
- **Dependencies**: Requires openpyxl (new dependency)
- **File Count**: 7 files (includes new model/migration) vs 4 files for previous APIs

### Excel Column Mapping Reference
Total 27 columns mapped from Chinese headers to English database fields:
- Evaluation period: 評核年月 → term_code
- Employee info: 工號 → employee_id, 姓名 → employee_name, etc. (7 fields)
- Dept evaluation: 初核成績 → init_score, etc. (9 fields)
- Mgr evaluation: 經理室初核成績 → mgr_init_score, etc. (9 fields)
- Additional: 請假總日數 → leave_days

## Tasks Created

- [ ] #38 - Create database model and migration for evaluations table (parallel: false)
- [ ] #39 - Create Pydantic schemas for evaluation API (parallel: false)
- [ ] #40 - Implement Excel upload service with upsert logic (parallel: false)
- [ ] #41 - Create upload endpoint with admin authorization (parallel: false)
- [ ] #42 - Implement search service with filters and pagination (parallel: true)
- [ ] #43 - Create search endpoint with authenticated user authorization (parallel: false)
- [ ] #44 - Register router and add openpyxl dependency (parallel: false)

Total tasks: 7
Parallel tasks: 1
Sequential tasks: 6
Estimated total effort: 12 hours (~1.5 days)
