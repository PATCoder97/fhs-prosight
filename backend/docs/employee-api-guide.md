# Employee API Usage Guide

## Overview

Employee synchronization and management system with 6 REST API endpoints. Sync employee data from FHS HRS and COVID APIs, search, update, and manage employee records.

**Base URL:** `http://localhost:8000/api`
**OpenAPI Docs:** `http://localhost:8000/docs`

## Authentication

All employee endpoints require **admin role**. Include JWT token in Authorization header:

```http
Authorization: Bearer {your_admin_jwt_token}
```

### Getting an Admin Token

1. Login via OAuth (Google/GitHub)
2. Admin user will receive JWT token with `role: "admin"`
3. Use token in all employee API requests

## Endpoints

### 1. Sync Single Employee

Sync single employee from HRS or COVID API.

**Endpoint:** `POST /api/employees/sync`

**Request Body:**
```json
{
  "emp_id": 6204,
  "source": "hrs",
  "token": null
}
```

**Parameters:**
- `emp_id` (integer, required): Employee ID (e.g., 6204)
- `source` (string, required): Data source ("hrs" or "covid")
- `token` (string, optional): Bearer token (required for COVID source)

**Response (200 OK):**
```json
{
  "id": "VNW0006204",
  "name_tw": "陳玉俊",
  "name_en": "Phan Anh Tuấn",
  "dob": "1997-04-20",
  "start_date": "2019-08-05",
  "dept": "冶金技術部",
  "department_code": "7410",
  "job_title": "工程師",
  "job_type": "正式",
  "salary": 7205600,
  "address1": "台灣",
  "phone1": "0123456789",
  "identity_number": null,
  "nationality": null,
  "sex": null,
  "dorm_id": null,
  "created_at": "2026-01-09T09:00:00Z",
  "updated_at": null
}
```

**cURL Example (HRS):**
```bash
curl -X POST "http://localhost:8000/api/employees/sync" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "emp_id": 6204,
    "source": "hrs"
  }'
```

**cURL Example (COVID):**
```bash
curl -X POST "http://localhost:8000/api/employees/sync" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "emp_id": 6204,
    "source": "covid",
    "token": "YOUR_COVID_API_TOKEN"
  }'
```

**Python Example:**
```python
import httpx
import asyncio

async def sync_employee():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/employees/sync",
            json={"emp_id": 6204, "source": "hrs"},
            headers={"Authorization": "Bearer YOUR_ADMIN_TOKEN"}
        )

        if response.status_code == 200:
            employee = response.json()
            print(f"Synced: {employee['id']} - {employee['name_en']}")
        else:
            print(f"Error: {response.status_code} - {response.text}")

asyncio.run(sync_employee())
```

**Error Responses:**
- `400 Bad Request`: Invalid source or missing token for COVID
- `403 Forbidden`: Admin role required
- `404 Not Found`: Employee not found in external API
- `422 Validation Error`: Invalid request body

---

### 2. Bulk Sync Employees

Sync multiple employees in a range (from_id to to_id).

**Endpoint:** `POST /api/employees/bulk-sync`

**Request Body:**
```json
{
  "from_id": 6200,
  "to_id": 6210,
  "source": "hrs",
  "token": null
}
```

**Parameters:**
- `from_id` (integer, required): Starting employee ID
- `to_id` (integer, required): Ending employee ID (inclusive)
- `source` (string, required): Data source ("hrs" or "covid")
- `token` (string, optional): Bearer token (required for COVID source)

**Validation:**
- `to_id` must be >= `from_id`
- Range limit: Maximum 1000 employees per request

**Response (200 OK):**
```json
{
  "total": 11,
  "success": 9,
  "failed": 1,
  "skipped": 1,
  "errors": [
    {
      "emp_id": 6207,
      "error": "Employee not found in HRS API"
    }
  ]
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/employees/bulk-sync" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "from_id": 6200,
    "to_id": 6210,
    "source": "hrs"
  }'
```

**Python Example:**
```python
import httpx
import asyncio

async def bulk_sync():
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(
            "http://localhost:8000/api/employees/bulk-sync",
            json={
                "from_id": 6200,
                "to_id": 6299,
                "source": "hrs"
            },
            headers={"Authorization": "Bearer YOUR_ADMIN_TOKEN"}
        )

        result = response.json()
        print(f"Total: {result['total']}")
        print(f"Success: {result['success']}")
        print(f"Failed: {result['failed']}")
        print(f"Skipped: {result['skipped']}")

        if result['errors']:
            print("\nErrors:")
            for error in result['errors']:
                print(f"  - Employee {error['emp_id']}: {error['error']}")

asyncio.run(bulk_sync())
```

**Performance Note:**
- Bulk sync processes employees sequentially
- Average: ~1.5 seconds per employee
- 100 employees ≈ 2-3 minutes
- Consider using async tasks for large batches

---

### 3. Search Employees

Search employees with filters and pagination.

**Endpoint:** `GET /api/employees/search`

**Query Parameters:**
- `name` (string, optional): Search in name_tw or name_en (case-insensitive, partial match)
- `department_code` (string, optional): Exact match on department code
- `dorm_id` (string, optional): Exact match on dormitory ID
- `skip` (integer, optional, default: 0): Pagination offset
- `limit` (integer, optional, default: 100, max: 1000): Results per page

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "VNW0006204",
      "name_tw": "陳玉俊",
      "name_en": "Phan Anh Tuấn",
      "department_code": "7410",
      "job_title": "工程師",
      ...
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 100
}
```

**cURL Examples:**

Search by name:
```bash
curl -X GET "http://localhost:8000/api/employees/search?name=陳玉" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

Search by department:
```bash
curl -X GET "http://localhost:8000/api/employees/search?department_code=7410" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

Search with pagination:
```bash
curl -X GET "http://localhost:8000/api/employees/search?skip=0&limit=50" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

**Python Example:**
```python
import httpx
import asyncio

async def search_employees():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/employees/search",
            params={
                "name": "陳",
                "department_code": "7410",
                "skip": 0,
                "limit": 10
            },
            headers={"Authorization": "Bearer YOUR_ADMIN_TOKEN"}
        )

        data = response.json()
        print(f"Found {data['total']} employees")

        for emp in data['items']:
            print(f"  - {emp['id']}: {emp['name_tw']} ({emp['name_en']})")

asyncio.run(search_employees())
```

---

### 4. Get Employee by ID

Retrieve single employee by ID.

**Endpoint:** `GET /api/employees/{emp_id}`

**Path Parameters:**
- `emp_id` (string, required): Employee ID (e.g., "VNW0006204")

**Response (200 OK):**
```json
{
  "id": "VNW0006204",
  "name_tw": "陳玉俊",
  "name_en": "Phan Anh Tuấn",
  "dob": "1997-04-20",
  "department_code": "7410",
  ...
}
```

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/api/employees/VNW0006204" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

**Python Example:**
```python
import httpx
import asyncio

async def get_employee(emp_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://localhost:8000/api/employees/{emp_id}",
            headers={"Authorization": "Bearer YOUR_ADMIN_TOKEN"}
        )

        if response.status_code == 200:
            employee = response.json()
            print(f"Employee: {employee['name_en']}")
            print(f"Department: {employee['dept']}")
            print(f"Job Title: {employee['job_title']}")
        elif response.status_code == 404:
            print(f"Employee {emp_id} not found")

asyncio.run(get_employee("VNW0006204"))
```

**Error Responses:**
- `403 Forbidden`: Admin role required
- `404 Not Found`: Employee ID doesn't exist

---

### 5. Update Employee

Update employee information.

**Endpoint:** `PUT /api/employees/{emp_id}`

**Path Parameters:**
- `emp_id` (string, required): Employee ID (e.g., "VNW0006204")

**Request Body (partial update):**
```json
{
  "job_title": "Senior Engineer",
  "salary": 9000000,
  "phone1": "0987654321",
  "dorm_id": "DORM001"
}
```

**Note:** Only fields provided in request body will be updated. Primary key (`id`) cannot be updated.

**Response (200 OK):**
```json
{
  "id": "VNW0006204",
  "name_tw": "陳玉俊",
  "name_en": "Phan Anh Tuấn",
  "job_title": "Senior Engineer",
  "salary": 9000000,
  "phone1": "0987654321",
  "dorm_id": "DORM001",
  "updated_at": "2026-01-09T09:30:00Z",
  ...
}
```

**cURL Example:**
```bash
curl -X PUT "http://localhost:8000/api/employees/VNW0006204" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "job_title": "Senior Engineer",
    "salary": 9000000
  }'
```

**Python Example:**
```python
import httpx
import asyncio

async def update_employee(emp_id: str, updates: dict):
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"http://localhost:8000/api/employees/{emp_id}",
            json=updates,
            headers={"Authorization": "Bearer YOUR_ADMIN_TOKEN"}
        )

        if response.status_code == 200:
            employee = response.json()
            print(f"Updated: {employee['id']}")
            print(f"New job title: {employee['job_title']}")
        elif response.status_code == 404:
            print(f"Employee {emp_id} not found")

asyncio.run(update_employee("VNW0006204", {
    "job_title": "Lead Engineer",
    "salary": 10000000
}))
```

**Error Responses:**
- `403 Forbidden`: Admin role required
- `404 Not Found`: Employee ID doesn't exist
- `422 Validation Error`: Invalid field values

---

### 6. Delete Employee

Delete employee record.

**Endpoint:** `DELETE /api/employees/{emp_id}`

**Path Parameters:**
- `emp_id` (string, required): Employee ID (e.g., "VNW0006204")

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Employee VNW0006204 deleted"
}
```

**Response (200 OK, not found):**
```json
{
  "success": false,
  "message": "Employee VNW9999999 not found"
}
```

**cURL Example:**
```bash
curl -X DELETE "http://localhost:8000/api/employees/VNW0006204" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

**Python Example:**
```python
import httpx
import asyncio

async def delete_employee(emp_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"http://localhost:8000/api/employees/{emp_id}",
            headers={"Authorization": "Bearer YOUR_ADMIN_TOKEN"}
        )

        result = response.json()
        if result['success']:
            print(f"Deleted: {emp_id}")
        else:
            print(f"Not found: {emp_id}")

asyncio.run(delete_employee("VNW0006204"))
```

**Error Responses:**
- `403 Forbidden`: Admin role required

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Common Causes | Action |
|------|---------|---------------|--------|
| 200 | OK | Request successful | Process response |
| 400 | Bad Request | Invalid source, missing token | Check request parameters |
| 401 | Unauthorized | Invalid/expired JWT token | Refresh authentication |
| 403 | Forbidden | Non-admin user | Admin role required |
| 404 | Not Found | Employee ID doesn't exist | Verify employee ID |
| 422 | Validation Error | Invalid request body | Check field types/values |
| 500 | Internal Server Error | Server error | Check server logs |
| 503 | Service Unavailable | External API down | Retry later |

### Error Response Format

```json
{
  "detail": "Error message describing the issue"
}
```

### Common Error Scenarios

**1. Missing COVID Token**
```json
// Request
POST /api/employees/sync
{
  "emp_id": 6204,
  "source": "covid"
  // Missing token
}

// Response: 400 Bad Request
{
  "detail": "Token required for COVID source"
}
```

**2. Non-Admin Access**
```json
// Response: 403 Forbidden
{
  "detail": "Admin role required"
}
```

**3. Employee Not Found**
```json
// Response: 404 Not Found
{
  "detail": "Employee 9999 not found in HRS API"
}
```

**4. Validation Error**
```json
// Request
POST /api/employees/bulk-sync
{
  "from_id": 6210,
  "to_id": 6200  // to_id < from_id
}

// Response: 422 Validation Error
{
  "detail": [
    {
      "loc": ["body", "to_id"],
      "msg": "to_id must be >= from_id",
      "type": "value_error"
    }
  ]
}
```

---

## Data Models

### Employee Model

```python
{
  "id": str,                    # VNW0006204 (primary key)
  "name_tw": str | null,        # Chinese name: 陳玉俊
  "name_en": str | null,        # Vietnamese name: Phan Anh Tuấn
  "dob": date | null,           # Date of birth: 1997-04-20
  "start_date": date | null,    # Employment start date
  "dept": str | null,           # Department name (Chinese)
  "department_code": str | null, # Department code: 7410
  "job_title": str | null,      # Job title
  "job_type": str | null,       # Employment type
  "salary": int | null,         # Monthly salary (integer)
  "address1": str | null,       # Primary address
  "address2": str | null,       # Secondary address
  "phone1": str | null,         # Primary phone
  "phone2": str | null,         # Secondary phone
  "spouse_name": str | null,    # Spouse name
  "nationality": str | null,    # Nationality code: VN
  "identity_number": str | null, # ID number (unique)
  "sex": str | null,            # Gender: M/F
  "dorm_id": str | null,        # Dormitory ID
  "created_at": datetime,       # Record creation timestamp
  "updated_at": datetime | null # Last update timestamp
}
```

### Data Sources

**HRS API (22 fields):**
- Primary employee data source
- No authentication required
- Includes: names, dates, department, job, salary, addresses, phones, spouse

**COVID API (8 fields):**
- Secondary data source for health records
- Requires bearer token authentication
- Includes: names, department_code, phone1, sex, identity_number, dob, nationality
- Merges with existing HRS data (doesn't overwrite)

---

## Best Practices

### 1. Token Management
- Store admin JWT securely
- Refresh tokens before expiration
- Never commit tokens to version control

### 2. Bulk Operations
- Use bulk-sync for multiple employees (more efficient)
- Monitor errors array in bulk-sync response
- Retry failed employees individually if needed

### 3. Search Optimization
- Use specific filters (department_code, dorm_id) for faster queries
- Implement pagination for large result sets
- Cache frequently accessed data

### 4. Error Handling
- Always check response status codes
- Log errors for debugging
- Implement retry logic for transient errors (503)

### 5. Data Synchronization
- Sync from HRS first (primary source)
- Then sync from COVID to merge additional fields
- Re-sync periodically to keep data fresh

---

## Testing with Postman

### Import Collection

Create a Postman collection with these endpoints:

1. **Sync Single (HRS)**: POST `/api/employees/sync`
2. **Sync Single (COVID)**: POST `/api/employees/sync`
3. **Bulk Sync**: POST `/api/employees/bulk-sync`
4. **Search Employees**: GET `/api/employees/search`
5. **Get Employee**: GET `/api/employees/{emp_id}`
6. **Update Employee**: PUT `/api/employees/{emp_id}`
7. **Delete Employee**: DELETE `/api/employees/{emp_id}`

### Environment Variables

Set in Postman environment:
- `base_url`: `http://localhost:8000/api`
- `admin_token`: Your admin JWT token
- `test_emp_id`: `VNW0006204`

---

## Related Documentation

- [Deployment Guide](./employee-deployment.md) - Deployment procedures
- [E2E Test Plan](./employee-e2e-tests.md) - Manual testing scenarios
- [OpenAPI Docs](http://localhost:8000/docs) - Interactive API documentation

---

## Support

For issues or questions:
- Check server logs: `tail -f logs/backend.log`
- Review migration status: `alembic current`
- Verify database: `psql -c "SELECT COUNT(*) FROM employees"`
