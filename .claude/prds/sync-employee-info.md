---
name: sync-employee-info
description: Sync employee information from FHS HRS and COVID APIs to local database with search and management capabilities
status: backlog
created: 2026-01-09T01:57:14Z
---

# PRD: Sync Employee Info

## Executive Summary

Hệ thống quản lý thông tin nhân viên tích hợp với FHS HRS API và FHS COVID API để đồng bộ, lưu trữ và tra cứu thông tin nhân viên. System cho phép admin sync thông tin nhân viên từ external APIs, lưu vào local database, và cung cấp các API endpoints để search và quản lý employee data.

**Value Proposition:**
- Centralized employee data management
- Real-time sync với FHS systems
- Fast search và filtering capabilities
- Foundation cho các features khác (dorm management, access control, etc.)

---

## Problem Statement

### Current Challenges:
1. **No Central Employee Database**: Thông tin nhân viên phân tán ở nhiều hệ thống (HRS, COVID Web, OAuth users)
2. **Manual Data Entry**: Admin phải manually assign localId cho users sau khi login
3. **No Employee Search**: Không có cách nào để search nhân viên theo name, department, dorm
4. **Data Inconsistency**: Thông tin nhân viên trong database không sync với HR system
5. **No Bulk Operations**: Không thể bulk import nhiều nhân viên cùng lúc

### Why Now?
- OAuth login system đã có (với localId field)
- Cần employee database làm foundation cho dorm management feature
- FHS đã cung cấp APIs (HRS + COVID) để lấy data
- Admin cần tool để manage employee info efficiently

---

## User Stories

### Persona 1: System Admin
**Goal:** Sync và manage employee data từ FHS systems

**User Stories:**
1. **As an admin**, I want to sync single employee by ID, so that I can quickly add new employee to system
   - **Acceptance Criteria:**
     - Nhập employee ID (VD: 6204)
     - System fetch từ HRS API
     - Nếu employee chưa tồn tại → create new record
     - Nếu đã tồn tại → update existing data
     - Return employee info hoặc error message

2. **As an admin**, I want to bulk sync employees (from_id to to_id), so that I can import many employees at once
   - **Acceptance Criteria:**
     - Nhập from_id, to_id, bearer token
     - System loop qua range và fetch từ COVID API
     - Skip invalid IDs (not found, error)
     - Return summary: success count, failed count, errors list
     - Process continues even if some IDs fail

3. **As an admin**, I want to search employees by name/department/dorm, so that I can find employees quickly
   - **Acceptance Criteria:**
     - Support filters: name (partial match), department_code, dorm_id
     - Support pagination (skip, limit)
     - Return list of employees matching criteria
     - Sort by employee ID

4. **As an admin**, I want to view employee details, so that I can see full employee information
   - **Acceptance Criteria:**
     - Nhập employee ID
     - Return all fields from database
     - Show last_updated timestamp
     - Show created_at timestamp

5. **As an admin**, I want to manually update employee info, so that I can correct mistakes or add missing data
   - **Acceptance Criteria:**
     - Update any field except ID
     - Validate data before update
     - Track updated_at timestamp
     - Return updated employee info

### Persona 2: Developer
**Goal:** Use employee API for other features

**User Stories:**
1. **As a developer**, I want to link OAuth users to employees by localId, so that users can see their employee info
2. **As a developer**, I want to check if employee exists before assigning dorm, so that only valid employees get dorms
3. **As a developer**, I want to get employee department info, so that I can implement department-based access control

---

## Requirements

### Functional Requirements

#### FR1: Integration Clients

**FR1.1: FHS HRS Client**
- Class: `FHSHRSClient` in `app/integrations/fhs_hrs_client.py`
- Base URL: `https://www.fhs.com.tw/ads/api/Furnace/rest/json/hr`

**Method 1: `async get_employee_info(emp_id: int) -> Optional[Dict]`**
  - Input: emp_id (int) - VD: 6204
  - Convert to: VNW00{emp_id:05d} - VD: VNW0006204
  - Endpoint: `s10/{emp_id_str}`
  - Parse response: 22 fields separated by "|"
  - Return dict with keys:
    ```python
    {
        "employee_id": str,
        "chinese_name": str,
        "vietnamese_name": str,  # Chuẩn hóa tên
        "date_of_birth": date,
        "date_of_joining": date,
        "department": str,
        "position": str,
        "date_of_appointment": date,
        "rank": str,
        "rank_start_date": date,
        "last_updated": date,
        "room_code": str,
        "effective_date": date,
        "basic_salary": int,
        "contract_date": date,
        "official_date": date,
        "exp_date": date,
        "current_address": str,
        "household_registration": str,
        "phone_1": str,
        "phone_2": str,
        "spouse_name": str,
    }
    ```
  - Error handling: Return None if error, log error message
  - Encoding: Force UTF-8

**Method 2: `async bulk_get_employees(from_id: int, to_id: int) -> List[Optional[Dict]]`**
  - Input: from_id (int), to_id (int) - VD: 6200, 6300
  - Loop từ from_id đến to_id
  - Call get_employee_info(emp_id) for each ID
  - Continue nếu individual ID fails (return None for that ID)
  - Return list of dicts (None for failed IDs)
  - No authentication required

**FR1.2: FHS COVID Client**
- Class: `FHSCovidClient` in `app/integrations/fhs_covid_client.py`
- Base URL: `https://www.fhs.com.tw/fhs_covid_api/api/reportVaccines/detail`

**Method 1: `async get_user_info(emp_id: int, token: str) -> Optional[Dict]`**
  - Input: emp_id (int), Bearer token (str)
  - Convert to: VNW00{emp_id:05d}
  - Query params: `?isFHS=true&isFull=false&userName={emp_id_str}`
  - Headers: Authorization: Bearer {token}
  - Return dict with keys:
    ```python
    {
        "userName": str,           # VNW0006204
        "fullName": str,          # 陳玉俊
        "departmentCode": str,    # 7410
        "departmentName": str,
        "companyCode": str,       # LG
        "phone": str,
        "sex": str,               # 男/女
        "identityNumber": str,    # CMND/CCCD
        "birthday": str,          # ISO date
        "nationality": str,       # VN
    }
    ```
  - Error handling: Return None if error (không raise exception)
  - Requires valid bearer token

**Method 2: `async bulk_get_users(from_id: int, to_id: int, token: str) -> List[Optional[Dict]]`**
  - Input: from_id (int), to_id (int), Bearer token (str) - VD: 6200, 6300, "eyJ..."
  - Loop từ from_id đến to_id
  - Call get_user_info(emp_id, token) for each ID
  - Continue nếu individual ID fails (return None for that ID)
  - Return list of dicts (None for failed IDs)
  - Requires valid bearer token (same token for all requests)

#### FR2: Database Model

**FR2.1: Employee Table**
- Table name: `employees`
- File: `app/models/employee.py`
- Schema:
```python
class Employee(Base):
    __tablename__ = "employees"

    # Primary Key
    id = Column(String(10), primary_key=True, index=True)  # VNW0006204

    # Names
    name_tw = Column(String(100))      # Chinese name
    name_en = Column(String(100))      # Vietnamese name

    # Dates
    dob = Column(Date, nullable=True)         # Date of birth
    start_date = Column(Date, nullable=True)  # Date of joining

    # Job Info
    dept = Column(String(100))                    # Department name (display)
    department_code = Column(String(8), index=True)  # Department code (for search)
    job_title = Column(String(100))               # Position
    job_type = Column(String(100))                # Job type

    # Salary & Personal
    salary = Column(Integer, default=0)
    address1 = Column(String(200))  # Current address
    address2 = Column(String(200))  # Household registration
    phone1 = Column(String(20))
    phone2 = Column(String(20))

    # Family & Legal
    spouse_name = Column(String(100), nullable=True)
    nationality = Column(String(20))
    identity_number = Column(String(32), unique=True, index=True)  # CMND/CCCD
    sex = Column(String(8))  # Male/Female or 男/女

    # Dormitory
    dorm_id = Column(String(20), nullable=True)
    # Future: ForeignKey("dorms.id") when dorms table exists

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

- Indexes:
  - Primary: `id`
  - Secondary: `department_code`, `identity_number`
- Constraints:
  - `identity_number` UNIQUE (không trùng CMND/CCCD)
  - `id` format: VNW00XXXXX

**FR2.2: Alembic Migration**
- Create migration: `add_employees_table`
- Include all columns above
- Add indexes
- Reversible (downgrade drops table)

#### FR3: Service Layer

**FR3.1: Employee Service**
- File: `app/services/employee_service.py`

**Method 1: `sync_employee_from_hrs(db, emp_id: int) -> Employee`**
- Fetch từ FHSHRSClient
- Map fields từ HRS response → Employee model
- If employee exists: update all fields
- If not exists: create new
- Commit to database
- Return Employee object
- Raise HTTPException if API error

**Method 2: `sync_employee_from_covid(db, emp_id: int, token: str) -> Employee`**
- Fetch từ FHSCovidClient
- Map fields từ COVID response → Employee model
- If employee exists: update (merge with existing data)
- If not exists: create new
- Note: COVID API có fewer fields than HRS
- Commit to database
- Return Employee object
- Raise HTTPException if API error or invalid token

**Method 3: `bulk_sync_employees(db, from_id: int, to_id: int, source: str, token: Optional[str] = None) -> Dict`**
- Input:
  - from_id, to_id: Range of employee IDs
  - source: "hrs" hoặc "covid"
  - token: Required nếu source="covid", optional nếu source="hrs"
- Logic:
  - If source == "hrs": call FHSHRSClient.bulk_get_employees(from_id, to_id)
  - If source == "covid": call FHSCovidClient.bulk_get_users(from_id, to_id, token)
  - For each result: sync to database (create or update)
  - Continue nếu individual ID fails (don't stop entire process)
- Collect results:
  ```python
  {
      "total": int,          # to_id - from_id + 1
      "success": int,        # Số employees synced thành công
      "failed": int,         # Số employees failed
      "skipped": int,        # Số IDs không có data (None)
      "errors": [            # List chi tiết errors
          {
              "emp_id": int,
              "error": str,
          }
      ]
  }
  ```
- Commit after each successful sync (không wait till end)
- Return summary dict

**Method 4: `search_employees(db, name, department_code, dorm_id, skip, limit) -> List[Employee]`**
- Build query with filters:
  - `name`: ILIKE search on name_tw OR name_en
  - `department_code`: Exact match
  - `dorm_id`: Exact match
- Apply pagination: offset(skip).limit(limit)
- Order by: id ASC
- Return list of Employee objects

**Method 5: `get_employee_by_id(db, emp_id: str) -> Optional[Employee]`**
- Query by primary key
- Return Employee or None

**Method 6: `update_employee(db, emp_id: str, update_data: Dict) -> Employee`**
- Get employee by ID
- Update fields from update_data dict
- Validate data
- Cannot update `id` (primary key)
- Update `updated_at` timestamp
- Commit
- Return updated Employee

**Method 7: `delete_employee(db, emp_id: str) -> bool`**
- Delete employee by ID
- Return True if deleted, False if not found
- Note: Có thể không cần delete, chỉ cần deactivate

#### FR4: API Endpoints

**File:** `app/routers/employees.py`

**Endpoint 1: POST /api/employees/sync**
```python
@router.post("/sync", response_model=EmployeeResponse)
async def sync_single_employee(
    request: SyncEmployeeRequest,  # { emp_id: int, source: "hrs" | "covid", token?: str }
    current_user: dict = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Sync single employee from external API.

    - emp_id: Employee ID (int) VD: 6204
    - source: "hrs" (không cần token) hoặc "covid" (cần token)
    - token: Bearer token (required nếu source="covid")

    Returns: Employee object
    """
```

**Endpoint 2: POST /api/employees/bulk-sync**
```python
@router.post("/bulk-sync", response_model=BulkSyncResponse)
async def bulk_sync_employees(
    request: BulkSyncRequest,  # { from_id: int, to_id: int, source: "hrs" | "covid", token?: str }
    current_user: dict = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Bulk sync employees from external APIs.

    - from_id: Starting employee ID (VD: 6200)
    - to_id: Ending employee ID (VD: 6300)
    - source: "hrs" (không cần token) hoặc "covid" (cần token)
    - token: Bearer token (required nếu source="covid")

    Returns: { total, success, failed, skipped, errors: [...] }

    Note: HRS API trả về nhiều fields hơn COVID API
    """
```

**Endpoint 3: GET /api/employees/search**
```python
@router.get("/search", response_model=EmployeeListResponse)
async def search_employees(
    name: Optional[str] = None,
    department_code: Optional[str] = None,
    dorm_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Search employees với filters và pagination.

    Query params:
    - name: Tìm theo tên (partial match, name_tw hoặc name_en)
    - department_code: Lọc theo mã bộ phận
    - dorm_id: Lọc theo ID ký túc xá
    - skip: Số records bỏ qua (default: 0)
    - limit: Số records tối đa (default: 100, max: 1000)

    Returns: { items: [Employee], total: int, skip: int, limit: int }
    """
```

**Endpoint 4: GET /api/employees/{emp_id}**
```python
@router.get("/{emp_id}", response_model=EmployeeResponse)
async def get_employee(
    emp_id: str,  # VNW0006204
    current_user: dict = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Get employee by ID.

    Returns: Employee object hoặc 404 nếu không tìm thấy
    """
```

**Endpoint 5: PUT /api/employees/{emp_id}**
```python
@router.put("/{emp_id}", response_model=EmployeeResponse)
async def update_employee(
    emp_id: str,
    request: UpdateEmployeeRequest,
    current_user: dict = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Update employee info manually.

    Request body: Partial employee data (chỉ update fields được gửi)
    Cannot update: id (primary key)

    Returns: Updated employee object
    """
```

**Endpoint 6: DELETE /api/employees/{emp_id}**
```python
@router.delete("/{emp_id}", response_model=DeleteResponse)
async def delete_employee(
    emp_id: str,
    current_user: dict = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete employee from database.

    Note: Consider soft delete (status field) thay vì hard delete

    Returns: { success: bool, message: str }
    """
```

#### FR5: Schemas (Pydantic Models)

**File:** `app/schemas/employees.py`

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime

# Request Schemas
class SyncEmployeeRequest(BaseModel):
    emp_id: int = Field(..., ge=1, description="Employee ID (VD: 6204)")
    source: str = Field(..., pattern="^(hrs|covid)$", description="hrs hoặc covid")
    token: Optional[str] = Field(None, description="Bearer token (required cho covid)")

class BulkSyncRequest(BaseModel):
    from_id: int = Field(..., ge=1, description="Starting employee ID")
    to_id: int = Field(..., ge=1, description="Ending employee ID")
    source: str = Field(..., pattern="^(hrs|covid)$", description="hrs hoặc covid")
    token: Optional[str] = Field(None, min_length=10, description="Bearer token (required cho covid)")

    @validator('to_id')
    def validate_range(cls, v, values):
        if 'from_id' in values and v < values['from_id']:
            raise ValueError('to_id must be >= from_id')
        if 'from_id' in values and v - values['from_id'] > 1000:
            raise ValueError('Range too large (max: 1000)')
        return v

    @validator('token')
    def validate_token_required_for_covid(cls, v, values):
        if 'source' in values and values['source'] == 'covid' and not v:
            raise ValueError('token is required when source is covid')
        return v

class UpdateEmployeeRequest(BaseModel):
    name_tw: Optional[str] = None
    name_en: Optional[str] = None
    dob: Optional[date] = None
    start_date: Optional[date] = None
    dept: Optional[str] = None
    department_code: Optional[str] = None
    job_title: Optional[str] = None
    job_type: Optional[str] = None
    salary: Optional[int] = None
    address1: Optional[str] = None
    address2: Optional[str] = None
    phone1: Optional[str] = None
    phone2: Optional[str] = None
    spouse_name: Optional[str] = None
    nationality: Optional[str] = None
    identity_number: Optional[str] = None
    sex: Optional[str] = None
    dorm_id: Optional[str] = None

# Response Schemas
class EmployeeResponse(BaseModel):
    id: str
    name_tw: Optional[str]
    name_en: Optional[str]
    dob: Optional[date]
    start_date: Optional[date]
    dept: Optional[str]
    department_code: Optional[str]
    job_title: Optional[str]
    job_type: Optional[str]
    salary: int
    address1: Optional[str]
    address2: Optional[str]
    phone1: Optional[str]
    phone2: Optional[str]
    spouse_name: Optional[str]
    nationality: Optional[str]
    identity_number: Optional[str]
    sex: Optional[str]
    dorm_id: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class EmployeeListResponse(BaseModel):
    items: List[EmployeeResponse]
    total: int
    skip: int
    limit: int

class BulkSyncResponse(BaseModel):
    total: int
    success: int
    failed: int
    skipped: int  # Số IDs không có data (None from API)
    errors: List[dict]  # [{ emp_id: int, error: str }]

class DeleteResponse(BaseModel):
    success: bool
    message: str
```

#### FR6: Utilities

**FR6.1: Name Normalization**
- Function: `chuan_hoa_ten(name: str) -> str`
- File: `app/utils/text_utils.py`
- Purpose: Chuẩn hóa tên tiếng Việt (VD: capitalize, remove extra spaces)

**FR6.2: Date Parsing**
- Function: `parse_date(date_str: str) -> Optional[date]`
- File: `app/utils/date_utils.py`
- Purpose: Parse date strings từ HRS API (handle multiple formats)

**FR6.3: Number Parsing**
- Function: `parse_number(num_str: str) -> int`
- File: `app/utils/text_utils.py`
- Purpose: Parse salary và numeric fields

**FR6.4: Block Parsing**
- Function: `first_block(raw_text: str) -> str`
- File: `app/utils/text_utils.py`
- Purpose: Extract first data block từ HRS API response

---

### Non-Functional Requirements

#### NFR1: Performance
- **Response Time:**
  - Single sync: < 3 seconds (API call + database write)
  - Bulk sync: < 1 second per employee (parallel processing if possible)
  - Search: < 500ms for queries returning up to 100 records
  - Get by ID: < 100ms

- **Throughput:**
  - Support bulk sync up to 1000 employees per request
  - Max range per bulk sync: 1000 IDs

- **Database:**
  - Index on `department_code`, `identity_number` for fast search
  - Use prepared statements để prevent SQL injection

#### NFR2: Reliability
- **Error Handling:**
  - Graceful degradation: Bulk sync continues nếu individual IDs fail
  - Detailed error messages in logs
  - Validation errors return 422 với clear messages
  - API errors from external sources logged và returned to client

- **Data Integrity:**
  - Unique constraint on `identity_number`
  - Foreign key constraints (when dorms table exists)
  - Transaction rollback nếu database error

- **Retry Logic:**
  - Retry failed HTTP requests (max 3 times) với exponential backoff
  - Timeout: 30 seconds per API call

#### NFR3: Security
- **Authentication:**
  - All endpoints require JWT token
  - Only admin role can access employee endpoints
  - Bearer token for COVID API validated before use

- **Authorization:**
  - Use `require_role("admin")` dependency
  - Future: Department admins can only see their department

- **Data Protection:**
  - Sensitive fields: identity_number, salary, addresses
  - Log access to employee data for audit
  - Do not expose bearer token in logs

- **Input Validation:**
  - Pydantic schemas validate all inputs
  - SQL injection prevention via SQLAlchemy ORM
  - XSS prevention (sanitize text inputs)

#### NFR4: Scalability
- **Database:**
  - Indexes on search fields
  - Pagination required for list endpoints
  - Connection pooling (AsyncSessionLocal)

- **API:**
  - Rate limiting on bulk sync endpoint (future)
  - Background jobs for very large imports (future)

#### NFR5: Maintainability
- **Code Structure:**
  - Follow existing project structure (integrations, services, routers, schemas, models)
  - Clear separation of concerns
  - Type hints on all functions

- **Logging:**
  - Log all API calls to external systems
  - Log all database operations (create/update/delete)
  - Log errors with full traceback

- **Documentation:**
  - Docstrings on all classes and methods
  - API endpoint documentation (OpenAPI/Swagger)
  - README section for employee sync feature

#### NFR6: Compatibility
- **Encoding:**
  - Force UTF-8 for all text data (Chinese, Vietnamese)
  - Handle Vietnamese diacritics correctly

- **Date Formats:**
  - Parse multiple date formats từ HRS API
  - Return ISO 8601 dates in API responses

- **Backward Compatibility:**
  - Không break existing OAuth user system
  - `localId` field in users table có thể link đến employee.id

---

## Success Criteria

### Quantitative Metrics

1. **Sync Success Rate:**
   - Single sync: > 95% success rate
   - Bulk sync: > 90% overall success rate (some IDs may not exist)

2. **Performance:**
   - Single sync: < 3 seconds (p95)
   - Search with filters: < 500ms (p95)
   - Bulk sync: < 1.5 seconds per employee (p95)

3. **Data Accuracy:**
   - 100% of synced employees have required fields (id, name)
   - 0 duplicate identity_numbers
   - 0 data corruption incidents

4. **API Availability:**
   - Employee endpoints: > 99% uptime
   - External API failures do not crash system

### Qualitative Goals

1. **Admin Experience:**
   - Admin can sync 100 employees in < 3 minutes
   - Clear error messages when sync fails
   - Easy to find employees via search

2. **Developer Experience:**
   - Clear API documentation
   - Easy to integrate employee data into other features
   - Reusable service methods

3. **Code Quality:**
   - Test coverage > 80%
   - No critical security vulnerabilities
   - Follows project coding standards

---

## Constraints & Assumptions

### Constraints

1. **Technical:**
   - Must use existing tech stack (FastAPI, SQLAlchemy, PostgreSQL)
   - Must follow existing project structure
   - Cannot modify external APIs (FHS HRS, COVID)

2. **External Dependencies:**
   - FHS HRS API uptime (không control được)
   - FHS COVID API requires valid bearer token
   - Bearer token có thể expire (admin phải refresh)

3. **Resource:**
   - Single developer implementation
   - No dedicated QA team (rely on automated tests)

4. **Security:**
   - Only admin role can access employee endpoints
   - Cannot expose employee data to non-admin users (yet)

### Assumptions

1. **Data Quality:**
   - FHS APIs return consistent data formats
   - Employee IDs are sequential (có thể có gaps)
   - identity_number is unique across all employees

2. **Business Logic:**
   - Admin will manually trigger sync (không auto-sync daily)
   - Existing employee data can be overwritten by sync
   - No approval workflow needed for sync

3. **Infrastructure:**
   - Database has enough storage for ~10,000 employees
   - Network connection to FHS APIs is stable
   - Server timezone is UTC

4. **Future Plans:**
   - Dorms table sẽ được tạo sau (dorm_id là placeholder)
   - Department-based access control sẽ được thêm sau
   - OAuth users sẽ được link đến employees via localId

---

## Out of Scope

**Explicitly NOT included in this PRD:**

1. **Auto-sync Scheduled Jobs:**
   - No cron jobs để auto-sync daily
   - Admin phải manually trigger sync

2. **Employee Self-Service:**
   - Employees cannot view/update their own info
   - No employee portal

3. **Advanced Access Control:**
   - Department admins cannot manage their department
   - No row-level security

4. **Dorm Management:**
   - dorm_id field exists nhưng dorm features out of scope
   - Dorms table chưa được tạo

5. **OAuth User Linking:**
   - Không auto-link OAuth users to employees
   - Admin phải manually assign localId (existing feature)

6. **Audit Trail:**
   - No detailed audit log (who changed what when)
   - Only track updated_at timestamp

7. **Export/Import:**
   - No Excel export/import
   - No CSV export

8. **Employee Photos:**
   - No avatar/photo field
   - No file upload

9. **Advanced Search:**
   - No full-text search
   - No fuzzy matching
   - No search by salary range, date range

10. **Notifications:**
    - No email/Slack notifications when sync complete
    - No alerts when sync fails

---

## Dependencies

### External Dependencies

1. **FHS HRS API**
   - URL: https://www.fhs.com.tw/ads/api/Furnace/rest/json/hr
   - Status: Available
   - Auth: None required
   - SLA: Unknown (external system)

2. **FHS COVID API**
   - URL: https://www.fhs.com.tw/fhs_covid_api/api/reportVaccines/detail
   - Status: Available
   - Auth: Bearer token (admin must provide)
   - SLA: Unknown (external system)
   - Note: Token có thể expire, admin phải refresh

### Internal Dependencies

1. **OAuth Login System** (Completed)
   - Users table có localId field
   - JWT authentication working
   - Admin role-based access control

2. **Database Migration Tool** (Completed)
   - Alembic configured
   - Can create new tables and indexes

3. **Admin Endpoints Pattern** (Completed)
   - `require_role("admin")` dependency exists
   - Admin endpoints pattern established in users.py

### Technical Dependencies

1. **Python Packages:**
   - httpx (async HTTP client) - already installed
   - sqlalchemy (ORM) - already installed
   - alembic (migrations) - already installed
   - pydantic (validation) - already installed

2. **Database:**
   - PostgreSQL (ktxn258.duckdns.org:6543)
   - Async driver: asyncpg - already installed

### Future Dependencies

1. **Dorms Feature** (Future)
   - dorm_id will become foreign key when dorms table exists
   - Employee-dorm relationship

2. **Advanced RBAC** (Future)
   - Department-based access control
   - Employee self-service portal

---

## Technical Design Notes

### Architecture

```
┌─────────────┐
│   Admin     │
│   Client    │
└──────┬──────┘
       │ JWT token (admin role)
       ↓
┌─────────────────────────────────┐
│    FastAPI Endpoints            │
│  /api/employees/*               │
│  - require_role("admin")        │
└──────┬──────────────────────────┘
       │
       ↓
┌─────────────────────────────────┐
│   Employee Service Layer        │
│  - sync_employee_from_hrs()     │
│  - sync_employee_from_covid()   │
│  - bulk_sync_employees()        │
│  - search_employees()           │
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
│  - HRS API (no auth)            │
│  - COVID API (bearer token)     │
└─────────────────────────────────┘
       │
       ↓
┌─────────────────────────────────┐
│   PostgreSQL Database           │
│   - employees table             │
│   - indexes on search fields    │
└─────────────────────────────────┘
```

### Data Flow: Single Sync

```
1. Admin → POST /api/employees/sync { emp_id: 6204, source: "hrs" }
2. Endpoint validates JWT + admin role
3. Call employee_service.sync_employee_from_hrs(db, 6204)
4. Service calls fhs_hrs_client.get_employee_info(6204)
5. Client: GET https://.../s10/VNW0006204
6. Client parses response (22 fields)
7. Service checks if employee exists in DB
8. If exists: UPDATE, else: INSERT
9. Commit transaction
10. Return Employee object to endpoint
11. Endpoint returns 200 OK with employee JSON
```

### Data Flow: Bulk Sync

```
1. Admin → POST /api/employees/bulk-sync { from_id: 6200, to_id: 6300, source: "hrs" (or "covid"), token?: "..." }
2. Endpoint validates JWT + admin role
3. Validate: if source="covid", token must be provided
4. Call employee_service.bulk_sync_employees(db, 6200, 6300, source, token)
5. Service:
   a. If source="hrs": call hrs_client.bulk_get_employees(6200, 6300)
   b. If source="covid": call covid_client.bulk_get_users(6200, 6300, token)
6. For each result in list:
   a. If result is None: increment skipped_count
   b. Try: sync to database (create or update)
   c. Success: increment success_count
   d. Fail: increment failed_count, append to errors list
7. Return summary: { total: 101, success: 90, failed: 6, skipped: 5, errors: [...] }
8. Endpoint returns 200 OK with summary JSON
```

### Database Schema

```sql
CREATE TABLE employees (
    id VARCHAR(10) PRIMARY KEY,  -- VNW0006204
    name_tw VARCHAR(100),
    name_en VARCHAR(100),
    dob DATE,
    start_date DATE,
    dept VARCHAR(100),
    department_code VARCHAR(8),
    job_title VARCHAR(100),
    job_type VARCHAR(100),
    salary INTEGER DEFAULT 0,
    address1 VARCHAR(200),
    address2 VARCHAR(200),
    phone1 VARCHAR(20),
    phone2 VARCHAR(20),
    spouse_name VARCHAR(100),
    nationality VARCHAR(20),
    identity_number VARCHAR(32) UNIQUE,
    sex VARCHAR(8),
    dorm_id VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_employees_department_code ON employees(department_code);
CREATE INDEX idx_employees_identity_number ON employees(identity_number);
```

### Error Handling Strategy

1. **External API Errors:**
   - Timeout after 30s
   - Retry up to 3 times với exponential backoff
   - Log full error details
   - Return HTTPException 503 Service Unavailable

2. **Database Errors:**
   - Rollback transaction
   - Log error with traceback
   - Return HTTPException 500 Internal Server Error

3. **Validation Errors:**
   - Pydantic validates input
   - Return HTTPException 422 Unprocessable Entity
   - Include field-level error messages

4. **Authentication Errors:**
   - Invalid JWT → 401 Unauthorized
   - Non-admin role → 403 Forbidden

5. **Bulk Sync Errors:**
   - Continue processing even if individual IDs fail
   - Collect all errors in list
   - Return partial success với error details

---

## Implementation Phases

### Phase 1: Foundation (Days 1-2)
- [ ] Create Employee model (app/models/employee.py)
- [ ] Create Alembic migration (add employees table)
- [ ] Run migration on dev database
- [ ] Create employee schemas (app/schemas/employees.py)
- [ ] Create utility functions (text_utils, date_utils)

### Phase 2: Integration Clients (Days 3-4)
- [ ] Implement FHSHRSClient (app/integrations/fhs_hrs_client.py)
  - [ ] Method: get_employee_info(emp_id) - single employee
  - [ ] Method: bulk_get_employees(from_id, to_id) - bulk sync
- [ ] Test HRS API calls với real IDs (single + bulk)
- [ ] Implement FHSCovidClient (app/integrations/fhs_covid_client.py)
  - [ ] Method: get_user_info(emp_id, token) - single employee
  - [ ] Method: bulk_get_users(from_id, to_id, token) - bulk sync
- [ ] Test COVID API calls với bearer token (single + bulk)
- [ ] Handle encoding issues (UTF-8, Chinese, Vietnamese)

### Phase 3: Service Layer (Days 5-6)
- [ ] Implement sync_employee_from_hrs() - single sync from HRS
- [ ] Implement sync_employee_from_covid() - single sync from COVID
- [ ] Implement bulk_sync_employees(source="hrs" or "covid") - unified bulk sync
- [ ] Implement search_employees() - with filters
- [ ] Implement CRUD operations (get, update, delete)
- [ ] Add comprehensive error handling
- [ ] Test bulk sync với both sources (HRS + COVID)

### Phase 4: API Endpoints (Days 7-8)
- [ ] Create employees router (app/routers/employees.py)
- [ ] Implement POST /api/employees/sync
- [ ] Implement POST /api/employees/bulk-sync
- [ ] Implement GET /api/employees/search
- [ ] Implement GET /api/employees/{emp_id}
- [ ] Implement PUT /api/employees/{emp_id}
- [ ] Implement DELETE /api/employees/{emp_id}
- [ ] Register router in main.py

### Phase 5: Testing (Days 9-10)
- [ ] Unit tests for utility functions
- [ ] Unit tests for integration clients (mocked)
- [ ] Unit tests for service layer
- [ ] Integration tests for endpoints
- [ ] Test với real FHS APIs
- [ ] Test bulk sync với large ranges
- [ ] Test error scenarios
- [ ] Achieve > 80% test coverage

### Phase 6: Documentation & Deployment (Days 11-12)
- [ ] Write API documentation (OpenAPI/Swagger)
- [ ] Write deployment guide
- [ ] Update TESTING_GUIDE.md
- [ ] Create E2E test plan
- [ ] Run migration on staging
- [ ] Test on staging
- [ ] Deploy to production
- [ ] Monitor for 24 hours

**Total Estimated Time:** 12 working days

---

## Testing Strategy

### Unit Tests

1. **Models:**
   - Test Employee model creation
   - Test constraints (unique identity_number)

2. **Utilities:**
   - Test chuan_hoa_ten() với Vietnamese names
   - Test parse_date() với various formats
   - Test parse_number() với edge cases
   - Test first_block() với HRS response format

3. **Integration Clients:**
   - Mock httpx responses
   - Test get_employee_info() response parsing
   - Test get_user_info() với COVID API format
   - Test error handling (timeout, 404, 500)

4. **Service Layer:**
   - Mock database session
   - Test sync_employee_from_hrs() - create new
   - Test sync_employee_from_hrs() - update existing
   - Test bulk_sync_employees() - partial success
   - Test search_employees() với different filters

### Integration Tests

1. **API Endpoints:**
   - Test full request/response cycle
   - Test authentication (require admin)
   - Test authorization (non-admin gets 403)
   - Test input validation (422 errors)
   - Test error responses (404, 500, 503)

2. **Database:**
   - Test create employee
   - Test update employee
   - Test search với indexes
   - Test unique constraint violations

3. **External APIs:**
   - Test real calls to FHS HRS API (với valid IDs)
   - Test real calls to FHS COVID API (với token)
   - Test error handling khi APIs down

### E2E Tests

1. **Happy Path:**
   - Admin sync single employee from HRS
   - Admin bulk sync 10 employees from COVID
   - Admin search employees by department
   - Admin view employee details
   - Admin update employee info

2. **Error Scenarios:**
   - Sync with invalid employee ID (404)
   - Bulk sync với expired token (401)
   - Search với invalid filters
   - Update non-existent employee (404)

3. **Performance:**
   - Bulk sync 100 employees < 150 seconds
   - Search 1000 employees < 500ms

---

## Monitoring & Metrics

### Application Metrics

1. **Sync Operations:**
   - Total syncs (counter)
   - Sync success rate (gauge)
   - Sync duration (histogram)
   - Bulk sync batch size (histogram)

2. **API Performance:**
   - Request count by endpoint
   - Response time by endpoint (p50, p95, p99)
   - Error rate by status code

3. **External API Health:**
   - HRS API success rate
   - COVID API success rate
   - API response time

### Database Metrics

1. **Employee Data:**
   - Total employees count
   - New employees today
   - Updated employees today
   - Employees by department (top 10)

2. **Query Performance:**
   - Search query duration
   - Index usage statistics

### Logs

1. **Info Level:**
   - Employee synced: {emp_id}
   - Bulk sync started: {from_id} to {to_id}
   - Bulk sync completed: {success}/{total}

2. **Warning Level:**
   - Employee not found: {emp_id}
   - Duplicate identity_number: {identity_number}

3. **Error Level:**
   - External API error: {url} - {error}
   - Database error: {error}
   - Token expired: COVID API

---

## Risks & Mitigation

### Risk 1: External API Downtime
**Impact:** HIGH - Cannot sync employees
**Probability:** MEDIUM
**Mitigation:**
- Implement retry logic với exponential backoff
- Cache employee data locally
- Provide manual CSV import as fallback
- Monitor API uptime và alert admin

### Risk 2: Token Expiration
**Impact:** HIGH - Bulk sync fails midway
**Probability:** HIGH
**Mitigation:**
- Validate token before bulk sync
- Return clear error message về token expiration
- Document how to refresh token
- Future: Auto-refresh token mechanism

### Risk 3: Data Inconsistency
**Impact:** MEDIUM - Employee data out of sync
**Probability:** MEDIUM
**Mitigation:**
- Timestamp last sync (updated_at)
- Provide re-sync functionality
- Log all data changes for audit
- Merge strategy: external API data overrides local

### Risk 4: Performance Degradation
**Impact:** MEDIUM - Slow search/sync
**Probability:** LOW
**Mitigation:**
- Indexes on search fields
- Pagination on list endpoints
- Rate limiting on bulk sync
- Monitor query performance

### Risk 5: Encoding Issues
**Impact:** MEDIUM - Corrupted Chinese/Vietnamese text
**Probability:** MEDIUM
**Mitigation:**
- Force UTF-8 encoding
- Test with real Chinese and Vietnamese names
- Validate encoding in tests
- Document encoding requirements

### Risk 6: Duplicate Employees
**Impact:** LOW - Identity_number collision
**Probability:** LOW
**Mitigation:**
- Unique constraint on identity_number
- Handle constraint violation gracefully
- Log conflicts for admin review
- Provide UI to merge duplicates (future)

---

## Future Enhancements

**Not in scope for initial release, but planned for future:**

1. **Auto-sync Scheduled Jobs**
   - Daily cron job to sync all employees
   - Incremental sync (only changed records)

2. **Advanced Search**
   - Full-text search across all fields
   - Fuzzy matching for names
   - Search by salary range, date range

3. **Export/Import**
   - CSV export for Excel
   - Excel import for bulk updates
   - PDF report generation

4. **Employee Portal**
   - Employees can view their own info
   - Employees can update contact info
   - Link OAuth accounts to employee records

5. **Department Management**
   - Department admins role
   - Department-based access control
   - Department hierarchy

6. **Audit Trail**
   - Full history of all changes
   - Who changed what when
   - Rollback capability

7. **Notifications**
   - Email/Slack when sync completes
   - Alert when sync fails
   - Weekly summary reports

8. **Advanced Features**
   - Employee photos/avatars
   - Organizational chart
   - Employee directory with org structure
   - Integration với attendance system

---

## Success Checklist

**Before marking this PRD complete, verify:**

- [ ] All functional requirements documented
- [ ] All non-functional requirements specified
- [ ] Success criteria measurable
- [ ] Constraints and assumptions clear
- [ ] Out of scope items listed
- [ ] Dependencies identified
- [ ] Technical design outlined
- [ ] Implementation phases defined
- [ ] Testing strategy comprehensive
- [ ] Risks identified with mitigation
- [ ] Monitoring plan in place

**Ready for Epic Creation:**
- [ ] Requirements unambiguous
- [ ] No placeholder text
- [ ] Acceptance criteria clear
- [ ] Can be broken down into tasks

---

## Appendix

### A. API Examples

**Example 1: Sync Single Employee**
```bash
POST /api/employees/sync
Authorization: Bearer {admin_jwt_token}
Content-Type: application/json

{
  "emp_id": 6204,
  "source": "hrs"
}

# Response 200 OK
{
  "id": "VNW0006204",
  "name_tw": "陳玉俊",
  "name_en": "Chen Yu Jun",
  "department_code": "7410",
  "job_title": "Engineer",
  ...
}
```

**Example 2a: Bulk Sync from HRS API (no token required)**
```bash
POST /api/employees/bulk-sync
Authorization: Bearer {admin_jwt_token}
Content-Type: application/json

{
  "from_id": 6200,
  "to_id": 6210,
  "source": "hrs"
}

# Response 200 OK
{
  "total": 11,
  "success": 9,
  "failed": 1,
  "skipped": 1,
  "errors": [
    { "emp_id": 6207, "error": "API timeout" }
  ]
}
```

**Example 2b: Bulk Sync from COVID API (token required)**
```bash
POST /api/employees/bulk-sync
Authorization: Bearer {admin_jwt_token}
Content-Type: application/json

{
  "from_id": 6200,
  "to_id": 6210,
  "source": "covid",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}

# Response 200 OK
{
  "total": 11,
  "success": 8,
  "failed": 2,
  "skipped": 1,
  "errors": [
    { "emp_id": 6203, "error": "Employee not found" },
    { "emp_id": 6207, "error": "API timeout" }
  ]
}
```

**Example 3: Search Employees**
```bash
GET /api/employees/search?name=chen&department_code=7410&limit=20
Authorization: Bearer {admin_jwt_token}

# Response 200 OK
{
  "items": [
    {
      "id": "VNW0006204",
      "name_tw": "陳玉俊",
      "name_en": "Chen Yu Jun",
      "department_code": "7410",
      ...
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 20
}
```

### B. Database Queries

**Query 1: Find employees by department**
```sql
SELECT * FROM employees
WHERE department_code = '7410'
ORDER BY id;
```

**Query 2: Find employees without dorm**
```sql
SELECT * FROM employees
WHERE dorm_id IS NULL
ORDER BY start_date DESC;
```

**Query 3: Count employees by nationality**
```sql
SELECT nationality, COUNT(*) as count
FROM employees
GROUP BY nationality
ORDER BY count DESC;
```

### C. Error Codes

| Code | Message | Cause |
|------|---------|-------|
| 401 | Unauthorized | Invalid JWT token |
| 403 | Forbidden | Non-admin user |
| 404 | Employee not found | Invalid employee ID |
| 422 | Validation error | Invalid input data |
| 500 | Internal server error | Database error |
| 503 | Service unavailable | External API down |

### D. External API Response Examples

**HRS API Response (s10/VNW0006204):**
```
潘英俊|PHAN ANH TUẤN|19970420|20190805|冶金技術部物理試驗處產品應用與自動化課|系統改善工程師|20230101|基層主管一級|20230101|072|20240301|A0E11|20230101|7,205,600|20220101|20210805||河靜省奇英市奇連坊眷屬社區258房號|河靜省干祿縣同祿社松蓮村|0395000295|0394499884|鄧氏鳳o|o潘英俊|PHAN ANH TUẤN|19970420|20190805|冶金技...
```

**COVID API Response:**
```json
{
  "userName": "VNW0006204",
  "fullName": "陳玉俊",
  "departmentCode": "7410",
  "departmentName": "冶金技術部",
  "companyCode": "LG",
  "phone": null,
  "sex": "男",
  "identityNumber": "044090004970",
  "birthday": "1990-02-17T00:00:00",
  "nationality": "VN"
}
```

---

**END OF PRD**
