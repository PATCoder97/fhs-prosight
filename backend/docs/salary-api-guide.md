# Salary API Usage Guide

## Overview

The Salary API provides read-only access to employee salary information from the FHS HRS system. Employees can view their own salary data, while administrators can view any employee's salary.

**Base URL:** `/api/hrs-data/`

**Features:**
- View current or specific month salary
- View salary history with trend analysis (multiple months)
- Admin: view any employee's salary
- Structured response: summary + income breakdown + deduction breakdown
- Real-time data (no caching, queries HRS API directly)

**Data Privacy:**
- Users can only access their own salary data
- Admin role required to access other employees' salary data
- All endpoints require JWT authentication

## Authentication

All endpoints require JWT authentication. Include your token in the Authorization header:

```bash
Authorization: Bearer {your_jwt_token}
```

**Roles:**
- **User:** Can view only their own salary
- **Admin:** Can view any employee's salary

**How to get a token:**
1. Login via Google/GitHub OAuth: `GET /auth/login/google` or `GET /auth/login/github`
2. Complete OAuth flow to receive JWT token
3. Use token in Authorization header for all API calls

## Endpoints

### 1. GET /api/hrs-data/salary

View your own salary for current month or specific month.

**Authorization:** User (any role)

**Query Parameters:**
- `year` (optional): Year (2000-2100), defaults to current year
- `month` (optional): Month (1-12), defaults to current month

**Response:** `SalaryResponse` (200 OK)

**cURL Example:**
```bash
# Current month
curl -X GET "http://localhost:8000/api/hrs-data/salary" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Specific month
curl -X GET "http://localhost:8000/api/hrs-data/salary?year=2024&month=12" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Python Example:**
```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.get(
        "http://localhost:8000/api/hrs-data/salary",
        params={"year": 2024, "month": 12},
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code == 200:
        salary = response.json()
        print(f"Net salary: {salary['summary']['thuc_linh']:,} VND")
        print(f"Total income: {salary['summary']['tong_tien_cong']:,} VND")
        print(f"Total deductions: {salary['summary']['tong_tien_tru']:,} VND")
    elif response.status_code == 404:
        print("Salary not found for this period")
```

**Response Example:**
```json
{
  "employee_id": "VNW0006204",
  "employee_name": "PHAN ANH TUẤN",
  "period": {
    "year": 2024,
    "month": 12
  },
  "summary": {
    "tong_tien_cong": 15000000.0,
    "tong_tien_tru": 3331510.0,
    "thuc_linh": 11668490.0
  },
  "income": {
    "luong_co_ban": 7205600.0,
    "thuong_nang_suat": 2000000.0,
    "phu_cap_chuc_vu": 1500000.0,
    "tro_cap_com": 660000.0,
    "tro_cap_di_lai": 440000.0
  },
  "deductions": {
    "bhxh": 1080840.0,
    "bhyt": 144112.0,
    "bh_that_nghiep": 72056.0,
    "thue_thu_nhap": 2034502.0
  }
}
```

**Error Responses:**
- `401 Unauthorized`: Missing or invalid JWT token
- `404 Not Found`: Salary not found for specified period
- `503 Service Unavailable`: HRS API unavailable

---

### 2. GET /api/hrs-data/salary/history

View your salary history with trend analysis for multiple months.

**Authorization:** User (any role)

**Query Parameters:**
- `year` (required): Year (2000-2100)
- `from_month` (optional): Start month (1-12), default 1
- `to_month` (optional): End month (1-12), default 12

**Response:** `SalaryHistoryResponse` (200 OK)

**cURL Example:**
```bash
# Full year (Jan-Dec)
curl -X GET "http://localhost:8000/api/hrs-data/salary/history?year=2024" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Partial year (Jan-Jun)
curl -X GET "http://localhost:8000/api/hrs-data/salary/history?year=2024&from_month=1&to_month=6" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Single quarter (Q1)
curl -X GET "http://localhost:8000/api/hrs-data/salary/history?year=2024&from_month=1&to_month=3" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Python Example:**
```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.get(
        "http://localhost:8000/api/hrs-data/salary/history",
        params={"year": 2024, "from_month": 1, "to_month": 12},
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code == 200:
        history = response.json()
        print(f"Average net salary: {history['trend']['average_net']:,.0f} VND")
        print(f"Highest month: {history['trend']['highest_month']['month']}")
        print(f"Lowest month: {history['trend']['lowest_month']['month']}")

        if history['trend']['significant_changes']:
            print("\nSignificant changes detected:")
            for change in history['trend']['significant_changes']:
                direction = "↑" if change['direction'] == "increase" else "↓"
                print(f"  Month {change['from_month']} → {change['to_month']}: "
                      f"{direction} {change['change']:,.0f} VND ({change['percentage']:.1f}%)")
```

**Response Example:**
```json
{
  "employee_id": "VNW0006204",
  "employee_name": "PHAN ANH TUẤN",
  "period": {
    "year": 2024,
    "month": "1-12"
  },
  "months": [
    {
      "month": 1,
      "summary": {
        "tong_tien_cong": 15000000.0,
        "tong_tien_tru": 3000000.0,
        "thuc_linh": 12000000.0
      },
      "income": {
        "luong_co_ban": 7205600.0,
        "thuong_nang_suat": 2000000.0
      },
      "deductions": {
        "bhxh": 1080840.0,
        "bhyt": 144112.0
      }
    },
    {
      "month": 2,
      "summary": {
        "tong_tien_cong": 15500000.0,
        "tong_tien_tru": 3100000.0,
        "thuc_linh": 12400000.0
      },
      "income": {},
      "deductions": {}
    }
    // ... more months
  ],
  "trend": {
    "average_income": 15500000.0,
    "average_deductions": 3100000.0,
    "average_net": 12400000.0,
    "highest_month": {
      "month": 12,
      "summary": {
        "tong_tien_cong": 17000000.0,
        "tong_tien_tru": 3400000.0,
        "thuc_linh": 13600000.0
      },
      "income": {},
      "deductions": {}
    },
    "lowest_month": {
      "month": 1,
      "summary": {
        "tong_tien_cong": 15000000.0,
        "tong_tien_tru": 3000000.0,
        "thuc_linh": 12000000.0
      },
      "income": {},
      "deductions": {}
    },
    "significant_changes": [
      {
        "from_month": 3,
        "to_month": 4,
        "field": "thuc_linh",
        "change": 2000000.0,
        "percentage": 16.67,
        "direction": "increase"
      }
    ]
  }
}
```

**Error Responses:**
- `401 Unauthorized`: Missing or invalid JWT token
- `404 Not Found`: No salary data found for any month in range
- `422 Validation Error`: Invalid month range (from_month > to_month)
- `503 Service Unavailable`: HRS API unavailable

---

### 3. GET /api/hrs-data/salary/{employee_id}

**Admin only:** View any employee's salary for a specific month.

**Authorization:** Admin role required

**Path Parameters:**
- `employee_id` (required): Employee ID (e.g., VNW0006204)

**Query Parameters:**
- `year` (required): Year (2000-2100)
- `month` (required): Month (1-12)

**Response:** `SalaryResponse` (200 OK)

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/api/hrs-data/salary/VNW0006204?year=2024&month=12" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

**Python Example:**
```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.get(
        "http://localhost:8000/api/hrs-data/salary/VNW0006204",
        params={"year": 2024, "month": 12},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    if response.status_code == 200:
        salary = response.json()
        print(f"Employee: {salary['employee_name']}")
        print(f"Net salary: {salary['summary']['thuc_linh']:,} VND")
    elif response.status_code == 403:
        print("Access denied: Admin role required")
    elif response.status_code == 404:
        print("Employee or salary not found")
```

**Response Example:**
```json
{
  "employee_id": "VNW0006204",
  "employee_name": "PHAN ANH TUẤN",
  "period": {
    "year": 2024,
    "month": 12
  },
  "summary": {
    "tong_tien_cong": 15000000.0,
    "tong_tien_tru": 3331510.0,
    "thuc_linh": 11668490.0
  },
  "income": {},
  "deductions": {}
}
```

**Error Responses:**
- `400 Bad Request`: Invalid employee ID format
- `401 Unauthorized`: Missing or invalid JWT token
- `403 Forbidden`: User is not admin (insufficient permissions)
- `404 Not Found`: Employee not found or salary not available
- `503 Service Unavailable`: HRS API unavailable

---

## Data Structure

### Summary (Tóm tắt lương)

The `summary` object contains 3 fields that summarize the salary calculation:

| Field | Description | Type |
|-------|-------------|------|
| `tong_tien_cong` | Total income (sum of all income fields) | float |
| `tong_tien_tru` | Total deductions (sum of all deduction fields) | float |
| `thuc_linh` | Net salary (tong_tien_cong - tong_tien_tru) | float |

**Note:** Small rounding differences (<100 VND) are acceptable due to HRS system calculations.

### Income (Thu nhập) - 32 Fields

The `income` object contains detailed breakdown of all income components. Common fields include:

| Field | Description | Vietnamese |
|-------|-------------|------------|
| `luong_co_ban` | Basic salary | Lương cơ bản |
| `thuong_nang_suat` | Performance bonus | Thưởng năng suất |
| `thuong_tet` | Tet bonus | Thưởng Tết |
| `phu_cap_chuc_vu` | Position allowance | Phụ cấp chức vụ |
| `tro_cap_com` | Meal allowance | Trợ cấp cơm |
| `tro_cap_di_lai` | Transportation allowance | Trợ cấp đi lại |
| `thuong_chuyen_can` | Attendance bonus | Thưởng chuyên cần |
| `phu_cap_ngon_ngu` | Language allowance | Phụ cấp ngôn ngữ |

**All income fields default to 0.0 if not provided by HRS API.**

For complete list of 32 income fields, see schema documentation.

### Deductions (Các khoản khấu trừ) - 10 Fields

The `deductions` object contains all deduction components:

| Field | Description | Vietnamese |
|-------|-------------|------------|
| `bhxh` | Social insurance | BHXH |
| `bhyt` | Health insurance | BHYT |
| `bh_that_nghiep` | Unemployment insurance | BH thất nghiệp |
| `thue_thu_nhap` | Income tax | Thuế thu nhập |
| `cong_doan` | Union fee | Công đoàn |
| `tien_com` | Meal deduction | Tiền cơm |
| `dong_phuc` | Uniform deduction | Đồng phục |
| `ky_tuc_xa` | Dormitory fee | Ký túc xá |
| `khac` | Other deductions | Khác |
| `nghi_phep` | Leave deduction | Nghỉ phép |

**All deduction fields default to 0.0 if not provided by HRS API.**

---

## Trend Analysis

When querying salary history, the API automatically calculates trend analysis to help identify patterns and significant changes.

### Trend Components

**Averages:**
- `average_income`: Average monthly total income
- `average_deductions`: Average monthly total deductions
- `average_net`: Average monthly net salary

**Extremes:**
- `highest_month`: Month with highest net salary (includes full salary data)
- `lowest_month`: Month with lowest net salary (includes full salary data)

**Significant Changes:**

The API detects month-over-month changes that meet either condition:
- Percentage change > 10%
- Absolute change > 500,000 VND

Each significant change includes:
- `from_month`: Previous month
- `to_month`: Current month
- `field`: Field that changed (always "thuc_linh")
- `change`: Absolute change amount (VND)
- `percentage`: Percentage change
- `direction`: "increase" or "decrease"

**Example Use Cases:**
- Identify bonus months (Tet, performance bonuses)
- Track salary adjustments
- Detect anomalies or errors
- Analyze income patterns

---

## Authorization Model

### User Role (Default)
- Can access: Own salary data only
- Endpoints available:
  - `GET /salary` (own)
  - `GET /salary/history` (own)

### Admin Role
- Can access: All salary data
- Endpoints available:
  - `GET /salary` (own)
  - `GET /salary/history` (own)
  - `GET /salary/{employee_id}` (any employee)

**Security Note:** The API automatically determines employee ID from JWT token's `localId` field for non-admin users. Admins must specify employee ID explicitly.

---

## Best Practices

### 1. Caching Recommendations

Salary data is relatively static (changes monthly). Consider caching:

```python
import httpx
from datetime import datetime, timedelta

class SalaryClient:
    def __init__(self):
        self.cache = {}
        self.cache_duration = timedelta(hours=1)

    async def get_salary(self, token, year, month):
        cache_key = f"{year}-{month}"

        # Check cache
        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if datetime.now() - cached_time < self.cache_duration:
                return cached_data

        # Fetch from API
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://localhost:8000/api/hrs-data/salary",
                params={"year": year, "month": month},
                headers={"Authorization": f"Bearer {token}"}
            )
            data = response.json()

        # Cache result
        self.cache[cache_key] = (data, datetime.now())
        return data
```

**Cache Duration Recommendations:**
- Current month: 1 hour (data may update during month)
- Past months: 24 hours or longer (data is final)
- Future months: No caching (will return 404)

### 2. Error Handling

Always handle common errors gracefully:

```python
async def fetch_salary_safe(client, token, year, month):
    try:
        response = await client.get(
            "http://localhost:8000/api/hrs-data/salary",
            params={"year": year, "month": month},
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            print(f"No salary data for {year}-{month:02d}")
            return None
        elif response.status_code == 401:
            print("Authentication failed. Please login again.")
            return None
        elif response.status_code == 503:
            print("HRS service temporarily unavailable. Please try again later.")
            return None
        else:
            print(f"Unexpected error: {response.status_code}")
            return None

    except httpx.TimeoutException:
        print("Request timeout. HRS API may be slow.")
        return None
    except httpx.NetworkError:
        print("Network error. Check your connection.")
        return None
```

### 3. Parallel Queries

For fetching multiple months, use the `/salary/history` endpoint instead of multiple individual calls:

**❌ Don't do this:**
```python
# Inefficient: 12 sequential API calls
salaries = []
for month in range(1, 13):
    salary = await get_salary(token, 2024, month)
    salaries.append(salary)
```

**✅ Do this instead:**
```python
# Efficient: Single API call with parallel HRS queries
history = await get_salary_history(token, 2024, 1, 12)
salaries = history['months']
trend = history['trend']
```

### 4. Rate Limiting

Be mindful of API load. Recommended limits:
- Max 10 requests per minute per user
- Max 100 requests per hour per user
- Use caching to reduce unnecessary calls

---

## Troubleshooting

### Q: Getting 404 for old months?
**A:** HRS API may not retain salary data beyond a certain period (typically 2-3 years). Contact HR for historical data needs.

### Q: Calculation doesn't match (tong_tien_cong - tong_tien_tru ≠ thuc_linh)?
**A:** Small differences (<100 VND) are acceptable due to rounding in HRS system. Check application logs for warnings if difference is larger.

### Q: Getting 503 errors?
**A:** HRS API may be temporarily unavailable or under maintenance. Wait a few minutes and retry. If issue persists, contact system administrator.

### Q: Salary shows "Unknown" for employee_name?
**A:** Employee record not found in local database. This doesn't affect salary data. Admin can sync employee info using `POST /api/employees/sync`.

### Q: Why does history endpoint skip some months?
**A:** HRS API may not have salary data for certain months (e.g., unpaid leave, new hire). The API returns all available data and calculates trends based on available months only.

### Q: Can I query future months?
**A:** No. Attempting to query future months will return 404. The API only provides historical and current month data.

### Q: Significant changes detected incorrectly?
**A:** Review the thresholds (10% or 500K VND). Some legitimate salary variations (bonuses, allowance changes) may trigger alerts. This is by design to help identify important changes.

---

## API Versioning

Current version: **v1** (no version prefix in URL)

**Breaking changes will be announced via:**
- Email notification to all developers
- 30-day deprecation notice
- New version prefix (e.g., `/api/v2/hrs-data/`)

---

## Related Documentation

- [Employee API Guide](./employee-api-guide.md) - Employee data management
- [Deployment Guide](./deployment-guide.md) - Deployment instructions
- [Testing Guide](./how-to-run-tests.md) - Running tests
- [Authentication Guide](../README.md) - OAuth login flow

---

## Support

For API issues or questions:
- Create GitHub issue: [fhs-prosight/issues](https://github.com/PATCoder97/fhs-prosight/issues)
- Contact: System Administrator
- Check logs: `backend/logs/app.log`

---

**Last Updated:** 2026-01-09
**API Version:** v1
**Document Version:** 1.0.0
