---
name: evaluations-info-api
description: Employee evaluation management system with Excel import and search capabilities
status: backlog
created: 2026-01-10T09:03:21Z
---

# PRD: Employee Evaluations Management API

## Executive Summary

Build a comprehensive employee evaluation management system that allows administrators to import evaluation data from Excel files and enables authenticated users to search and view evaluation records. The system stores multi-level evaluation scores (department and management office) with reviewer comments and supports flexible querying by employee, term, and department.

**Key Features**:
- Excel file upload for bulk evaluation data import (admin only)
- Upsert logic based on term_code + employee_id
- Search API with filters (employee_id, term_code, dept_code)
- Multi-level evaluation tracking (初核/複核/核定 for both 部門 and 經理室)
- Authorization: Admin for upload, authenticated users for search (blocks guests)

## Business Context

### Problem Statement

Employee evaluation data is currently managed in Excel files and not accessible via API. HR and management need:
1. **Centralized storage**: Store evaluation records in database for reliable access
2. **Bulk updates**: Import monthly evaluation files without manual data entry
3. **Searchable data**: Query evaluations by employee, period, or department
4. **Audit trail**: Track who reviewed and approved evaluations at each level

### Target Users

1. **HR Administrators** (Primary)
   - Upload monthly evaluation Excel files
   - Update existing records when corrections are needed
   - Manage evaluation data lifecycle

2. **Employees** (Secondary)
   - View their own evaluation history
   - Check scores and comments from reviewers

3. **Managers** (Secondary)
   - Review team evaluations
   - Filter by department or period

4. **Excluded**: Guest users (read access blocked)

### Success Metrics

- Evaluation records successfully imported from Excel (>95% success rate)
- API response time < 500ms for search queries
- Zero data loss during upsert operations
- 100% authorization enforcement (guests blocked, admin-only upload)

## Requirements

### Functional Requirements

#### 1. Database Schema

**Table**: `evaluations`

**Fields**:
- **Evaluation Period** (Required):
  - `id`: Integer, primary key, auto-increment
  - `term_code`: String(10), nullable=False (format: 25, 251, 252, 25A, 25B, 25C)
  - `employee_id`: String(20), nullable=False (format: VNW0006204)

- **Employee Info** (Optional - can sync from user table):
  - `employee_name`: String(100)
  - `job_level`: String(50) (職等)
  - `nation`: String(10) (國籍: TW, VN, etc.)
  - `dept_code`: String(20) (部門代碼)
  - `dept_name`: String(200) (部門名稱)
  - `grade_code`: String(20) (職等六碼)
  - `grade_name`: String(100) (職等名稱)

- **Department Evaluation** (部門 - 初核/複核/核定):
  - `init_score`: String(20) (初核成績: 甲, 優, etc.)
  - `init_comment`: Text (初核評語)
  - `init_reviewer`: String(20) (初核主管 - employee_id)
  - `review_score`: String(20) (複核成績)
  - `review_comment`: Text (複核評語)
  - `review_reviewer`: String(20) (複核主管)
  - `final_score`: String(20) (核定成績)
  - `final_comment`: Text (核定評語)
  - `final_reviewer`: String(20) (核定主管)

- **Management Office Evaluation** (經理室 - 初核/複核/核定):
  - `mgr_init_score`: String(20) (經理室初核成績)
  - `mgr_init_comment`: Text (經理室初核評語)
  - `mgr_init_reviewer`: String(20) (經理室初核主管)
  - `mgr_review_score`: String(20) (經理室複核成績)
  - `mgr_review_comment`: Text (經理室複核評語)
  - `mgr_review_reviewer`: String(20) (經理室複核主管)
  - `mgr_final_score`: String(20) (經理室核定成績)
  - `mgr_final_comment`: Text (經理室核定評語)
  - `mgr_final_reviewer`: String(20) (經理室核定主管)

- **Additional Info**:
  - `leave_days`: Float (請假總日數, optional)
  - `created_at`: DateTime (auto-generated)
  - `updated_at`: DateTime (auto-updated)

**Constraints**:
- UniqueConstraint('term_code', 'employee_id', name='uq_evaluations_term_employee')

#### 2. Excel Import API

**Endpoint**: `POST /api/evaluations/upload`

**Authorization**: Admin only (requires admin role)

**Request**:
- Content-Type: multipart/form-data
- File: Excel file (.xlsx, .xls)

**Excel Column Mapping**:
```python
EXCEL_COLUMN_MAPPING = {
    "評核年月": "term_code",
    "工號": "employee_id",
    "姓名": "employee_name",
    "職等": "job_level",
    "國籍": "nation",
    "部門代碼": "dept_code",
    "部門名稱": "dept_name",
    "職等六碼": "grade_code",
    "職等名稱": "grade_name",
    "初核成績": "init_score",
    "初核評語": "init_comment",
    "初核主管": "init_reviewer",
    "複核成績": "review_score",
    "複核評語": "review_comment",
    "複核主管": "review_reviewer",
    "核定成績": "final_score",
    "核定評語": "final_comment",
    "核定主管": "final_reviewer",
    "經理室初核成績": "mgr_init_score",
    "經理室初核評語": "mgr_init_comment",
    "經理室初核主管": "mgr_init_reviewer",
    "經理室複核成績": "mgr_review_score",
    "經理室複核評語": "mgr_review_comment",
    "經理室複核主管": "mgr_review_reviewer",
    "經理室核定成績": "mgr_final_score",
    "經理室核定評語": "mgr_final_comment",
    "經理室核定主管": "mgr_final_reviewer",
    "請假總日數": "leave_days",
}
```

**Business Logic**:
- Read Excel file row by row
- For each row:
  - Check if (term_code, employee_id) exists in database
  - If exists: UPDATE existing record
  - If not exists: INSERT new record
- Validate required fields: term_code, employee_id
- Return summary: {created: X, updated: Y, errors: []}

**Response 200**:
```json
{
  "success": true,
  "summary": {
    "total_rows": 150,
    "created": 120,
    "updated": 30,
    "errors": 0
  },
  "error_details": []
}
```

**Error Responses**:
- 400: Invalid file format or missing required columns
- 401: Unauthorized (no token)
- 403: Forbidden (not admin)
- 413: File too large
- 500: Server error during processing

#### 3. Search Evaluations API

**Endpoint**: `GET /api/evaluations/search`

**Authorization**: Authenticated users only (blocks guest)

**Query Parameters** (all optional):
- `employee_id`: Filter by specific employee ID (exact match)
- `term_code`: Filter by evaluation period (exact match, e.g., '25B')
- `dept_code`: Filter by department code (starts with, e.g., '78' matches '7800', '7810')
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 50, max: 100)

**Response 200**:
```json
{
  "total": 250,
  "page": 1,
  "page_size": 50,
  "results": [
    {
      "id": 1,
      "term_code": "25B",
      "employee_id": "VNW0018983",
      "employee_name": "阮氏幸",
      "job_level": "基層人員",
      "nation": "VN",
      "dept_code": "7800",
      "dept_name": "冶金技術部物理試驗處處務室",
      "grade_code": "MZD01P",
      "grade_name": "助理管理師",
      "dept_evaluation": {
        "init": {"score": "甲", "comment": "", "reviewer": "VNW0004635"},
        "review": {"score": "甲", "comment": "", "reviewer": null},
        "final": {"score": "甲", "comment": "", "reviewer": "VNW0003380"}
      },
      "mgr_evaluation": {
        "init": {"score": "甲", "comment": "", "reviewer": "VNW0013364"},
        "review": {"score": "甲", "comment": "", "reviewer": "VNW0004740"},
        "final": {"score": "甲", "comment": "", "reviewer": "VNW0001140"}
      },
      "leave_days": 0.125,
      "created_at": "2026-01-10T09:00:00Z",
      "updated_at": "2026-01-10T09:00:00Z"
    }
  ]
}
```

**Error Responses**:
- 401: Unauthorized (no token)
- 403: Forbidden (guest user)
- 422: Invalid query parameters

### Non-Functional Requirements

#### Performance
- Excel file upload: Support up to 1000 rows in < 30 seconds
- Search API: Response time < 500ms
- Database: Index on (term_code, employee_id, dept_code)

#### Security
- Admin-only upload endpoint (JWT with role check)
- Block guest users from search endpoint
- Validate Excel file size (max 10MB)
- Sanitize Excel data to prevent injection attacks

#### Reliability
- Transaction-based upsert (rollback on error)
- Detailed error logging for failed rows
- Retry logic for database deadlocks

#### Maintainability
- Follow existing HRS API patterns (same codebase structure)
- Reuse authorization dependencies (require_admin, require_authenticated_user)
- Use SQLAlchemy ORM for database operations

### Out of Scope

- **Excel export**: Not building download/export functionality
- **Real-time sync**: Not syncing with external HR systems
- **Evaluation workflow**: Not building approval/rejection workflows
- **Email notifications**: Not sending notifications on upload
- **Data visualization**: Not building charts or dashboards
- **Tests and documentation**: Per user request, skip these

## Technical Specifications

### Architecture

**Files to Create/Modify** (7 files):
1. `backend/app/models/evaluation.py` - New SQLAlchemy model
2. `backend/app/schemas/evaluation.py` - New Pydantic schemas
3. `backend/app/services/evaluation_service.py` - New service layer
4. `backend/app/routers/evaluations.py` - New router
5. `backend/alembic/versions/xxx_add_evaluations_table.py` - New migration
6. `backend/app/main.py` - Register new router
7. `backend/requirements.txt` - Add openpyxl for Excel parsing

### Database Migration

**Create migration**:
```bash
alembic revision -m "Add evaluations table"
```

**Migration content**:
- Create `evaluations` table with all fields
- Add unique constraint on (term_code, employee_id)
- Add indexes on term_code, employee_id, dept_code
- Add created_at, updated_at timestamps

### Excel Processing

**Library**: openpyxl (Python library for Excel reading)

**Processing Flow**:
1. Receive uploaded file (multipart/form-data)
2. Save to temp location
3. Open with openpyxl
4. Read header row, validate required columns exist
5. For each data row:
   - Map columns using EXCEL_COLUMN_MAPPING
   - Validate required fields (term_code, employee_id)
   - Check if record exists (SELECT by term_code + employee_id)
   - If exists: UPDATE, else: INSERT
   - Track created/updated count
6. Return summary with counts
7. Delete temp file

### API Endpoints Summary

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| /api/evaluations/upload | POST | Admin only | Upload Excel file to import/update evaluations |
| /api/evaluations/search | GET | Authenticated (no guest) | Search evaluations with filters |

## Implementation Plan

### Task Breakdown

1. **Task 1**: Create Evaluation model and migration
   - File: `backend/app/models/evaluation.py`
   - File: `backend/alembic/versions/xxx_add_evaluations_table.py`
   - Run migration to create table
   - Effort: 2 hours

2. **Task 2**: Create Pydantic schemas
   - File: `backend/app/schemas/evaluation.py`
   - EvaluationBase, EvaluationCreate, EvaluationResponse, SearchResponse
   - Effort: 1 hour

3. **Task 3**: Implement Excel upload service
   - File: `backend/app/services/evaluation_service.py`
   - Excel parsing with openpyxl
   - Upsert logic (check exists → update/insert)
   - Effort: 3 hours

4. **Task 4**: Create upload endpoint
   - File: `backend/app/routers/evaluations.py`
   - POST /upload with admin authorization
   - File handling with multipart/form-data
   - Effort: 2 hours

5. **Task 5**: Implement search service
   - File: `backend/app/services/evaluation_service.py`
   - Query building with filters (employee_id, term_code, dept_code)
   - Pagination logic
   - Effort: 2 hours

6. **Task 6**: Create search endpoint
   - File: `backend/app/routers/evaluations.py`
   - GET /search with authenticated user check
   - Response formatting
   - Effort: 1 hour

7. **Task 7**: Register router and add dependency
   - File: `backend/app/main.py`
   - File: `backend/requirements.txt`
   - Add openpyxl dependency
   - Effort: 1 hour

**Total Effort**: 12 hours (~1.5 days)

**No tests or documentation** (per user request)

## Data Models

### Pydantic Schemas

```python
class EvaluationLevel(BaseModel):
    """Single evaluation level (init/review/final)."""
    score: Optional[str] = None
    comment: Optional[str] = None
    reviewer: Optional[str] = None

class EvaluationGroup(BaseModel):
    """Evaluation group (dept or mgr)."""
    init: EvaluationLevel
    review: EvaluationLevel
    final: EvaluationLevel

class EvaluationResponse(BaseModel):
    """Response model for evaluation record."""
    id: int
    term_code: str
    employee_id: str
    employee_name: Optional[str]
    job_level: Optional[str]
    nation: Optional[str]
    dept_code: Optional[str]
    dept_name: Optional[str]
    grade_code: Optional[str]
    grade_name: Optional[str]
    dept_evaluation: EvaluationGroup
    mgr_evaluation: EvaluationGroup
    leave_days: Optional[float]
    created_at: datetime
    updated_at: datetime

class SearchResponse(BaseModel):
    """Paginated search response."""
    total: int
    page: int
    page_size: int
    results: List[EvaluationResponse]

class UploadSummary(BaseModel):
    """Upload result summary."""
    success: bool
    summary: dict
    error_details: List[dict]
```

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Excel file corruption or invalid format | High | Validate file format before processing, return clear error messages |
| Large Excel files (>1000 rows) timeout | Medium | Process in batches, add progress tracking, increase timeout to 60s |
| Duplicate data in Excel (same term_code + employee_id) | Medium | Last row wins, log warning in summary |
| Missing required columns in Excel | High | Validate header row first, return 400 if columns missing |
| Database deadlock during bulk upsert | Low | Use transactions, retry on deadlock, process rows sequentially |
| Unauthorized users uploading files | High | Enforce admin-only check in dependency, return 403 if not admin |

## Success Criteria

- [x] Database table created with all fields and constraints
- [x] Excel upload successfully imports 100+ rows in < 30s
- [x] Upsert logic correctly updates existing records
- [x] Admin-only authorization enforced on upload endpoint
- [x] Search API returns filtered results with pagination
- [x] Guest users blocked from search endpoint (403)
- [x] All error cases handled (400, 401, 403, 413, 500)
- [x] No data loss during upsert operations

## Deployment Notes

- **Database migration**: Run `alembic upgrade head` to create table
- **New dependency**: Add `openpyxl>=3.1.0` to requirements.txt
- **Backward compatible**: No changes to existing endpoints
- **File upload limits**: Configure max file size in nginx/uvicorn

## Appendix

### Sample Excel Data

**Header Row**:
```
評核年月 | 工號 | 姓名 | 職等 | 國籍 | 部門代碼 | 部門名稱 | 職等六碼 | 職等名稱 | 初核成績 | 初核評語 | 初核主管 | 複核成績 | 複核評語 | 複核主管 | 核定成績 | 核定評語 | 核定主管 | 經理室初核成績 | 經理室初核評語 | 經理室初核主管 | 經理室複核成績 | 經理室複核評語 | 經理室複核主管 | 經理室核定成績 | 經理室核定評語 | 經理室核定主管 | 請假總日數
```

**Sample Row 1**:
```
25B | VNW0018983 | 阮氏幸 | 基層人員 | VN | 7800 | 冶金技術部物理試驗處處務室 | MZD01P | 助理管理師 | 甲 | | VNW0004635 | 甲 | | | 甲 | | VNW0003380 | 甲 | | VNW0013364 | 甲 | | VNW0004740 | 甲 | | VNW0001140 | 0.125
```

**Sample Row 2**:
```
25B | VNW0011603 | 阮文芳 | 基層人員 | VN | 7810 | 冶金技術部物理試驗處金相物理試驗課 | IECBLP | 物理檢驗技術員 | 優 | 本月完成審核共1305個力學試驗數據，及時率100% | VNW0004677 | 優 | 本月完成審核共1305個力學試驗數據，及時率100% | | 優 | 本月完成審核共1305個力學試驗數據，及時率100% | VNW0003380 | 優 | 本月完成審核共1305個力學試驗數據，及時率100% | VNW0013364 | 優 | 本月完成審核共1305個力學試驗數據，及時率100% | VNW0004740 | 優 | 本月完成審核共1305個力學試驗數據，及時率100% | VNW0001140 | 0
```

### Authorization Matrix

| Endpoint | User | Admin | Guest |
|----------|------|-------|-------|
| POST /upload | ❌ Forbidden | ✅ Allowed | ❌ Forbidden |
| GET /search | ✅ Allowed | ✅ Allowed | ❌ Blocked (403) |

### Term Code Format

- **Format**: `25`, `251`, `252`, `25A`, `25B`, `25C`
- **Pattern**: Number (25) + optional suffix (1, 2, A, B, C)
- **Meaning**: Evaluation period (year + month/quarter identifier)
