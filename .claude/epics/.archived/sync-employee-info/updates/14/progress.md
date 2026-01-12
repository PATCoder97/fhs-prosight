---
issue: 14
task: Service layer - Employee sync, CRUD, and search operations
started: 2026-01-09T04:15:04Z
completed: 2026-01-09T04:19:00Z
status: completed
---

# Issue #14 Progress: Service Layer

## Summary

Successfully implemented employee service layer with 7 core methods for sync, search, and CRUD operations.

## Completed Work

### Service Methods Implemented ✅

**File:** `backend/app/services/employee_service.py` (377 lines)

#### 1. Sync Methods

**sync_employee_from_hrs(db, emp_id)**
- Fetches from FHS HRS API
- Maps 22 fields to Employee model
- Upsert pattern (create or update)
- Uses utility functions for parsing
- Returns Employee object
- Raises HTTPException if not found

**sync_employee_from_covid(db, emp_id, token)**
- Fetches from FHS COVID API with bearer token
- Maps partial fields (COVID has fewer than HRS)
- Merges with existing data (doesn't overwrite HRS fields)
- Upsert to database
- Returns Employee object

**bulk_sync_employees(db, from_id, to_id, source, token?)**
- Unified method for both HRS and COVID sources
- Routes to appropriate client based on source parameter
- Processes each employee: fetch → map → upsert
- Continues on individual failures (graceful degradation)
- Commits after each successful sync
- Returns summary: {total, success, failed, skipped, errors[]}

#### 2. Search & CRUD Methods

**search_employees(db, name?, dept_code?, dorm_id?, skip, limit)**
- ILIKE search on name_tw OR name_en (case-insensitive)
- Exact match filters: department_code, dorm_id
- Pagination with skip/limit
- Ordered by employee ID
- Returns list of Employee objects

**get_employee_by_id(db, emp_id)**
- Query by primary key
- Returns Employee or None

**update_employee(db, emp_id, update_data)**
- Updates employee fields from dict
- Cannot update primary key
- Sets updated_at timestamp
- Raises HTTPException if not found
- Returns updated Employee

**delete_employee(db, emp_id)**
- Deletes by primary key
- Returns True if deleted, False if not found

### Helper Functions ✅

**_map_hrs_to_model(hrs_data)**
- Maps HRS API response → Employee model fields
- Uses parse_date() for date fields
- Uses parse_number() for salary
- Uses chuan_hoa_ten() for Vietnamese name normalization

**_map_covid_to_model(covid_data)**
- Maps COVID API response → Employee model fields (partial)
- Returns only fields that COVID API provides

### Client Initialization ✅

- Module-level client instances: `hrs_client`, `covid_client`
- Follows existing auth_service pattern

## Commits

- `2b632e4` - Issue #14: Implement employee service layer

## Files Created

- `backend/app/services/employee_service.py` (377 lines)

## Acceptance Criteria Status

### Sync Methods
- [x] sync_employee_from_hrs() - Fetch, map, upsert, return Employee
- [x] sync_employee_from_covid() - Fetch with token, merge, upsert
- [x] bulk_sync_employees() - Unified for both sources, graceful errors

### Search & CRUD
- [x] search_employees() - ILIKE on names, exact on dept/dorm, pagination
- [x] get_employee_by_id() - Query by PK
- [x] update_employee() - Update fields, validate, return Employee
- [x] delete_employee() - Delete by PK, return bool

### Implementation Quality
- [x] Async methods with AsyncSession
- [x] Transaction management (commit/rollback)
- [x] Error handling with HTTPException
- [x] Logging for debugging
- [x] UTF-8 support via utility functions
- [x] Follows existing service pattern

## Dependencies Met

- ✅ #12: Database setup (Employee model, schemas)
- ✅ #13: Integration clients (FHSHRSClient, FHSCovidClient)

## Next Steps

Task #14 is complete. This enables:
- #15: API endpoints (depends on #14 ✅) - **Can start now**
- #16: Unit tests (parallel, depends on #12 ✅, #13 ✅, #14 ✅) - **Can start now**

Ready for API endpoint implementation and testing.
