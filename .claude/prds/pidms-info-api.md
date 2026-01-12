---
name: pidms-info-api
description: API for managing product license keys via PIDKey.com integration with search, sync, and validation capabilities
status: complete
created: 2026-01-12T06:59:20Z
---

# PRD: pidms-info-api

## Executive Summary

The PIDMS (Product ID Management System) API provides a comprehensive solution for managing Microsoft Office and Windows product license keys by integrating with the PIDKey.com external API. This system enables administrators to check key validity, track activation counts, search for available keys, and maintain an up-to-date inventory of license keys within the FHS ProSight database.

**Key Value Propositions:**
- Centralized license key management with real-time validation
- Automatic synchronization with PIDKey.com to track remaining activations
- Fuzzy search capabilities to quickly find keys by product type
- Historical tracking of key status changes
- Admin-only access for security compliance

## Problem Statement

### Current Challenge
FHS currently lacks a centralized system to manage software license keys (Office, Windows products). This leads to:
- Manual tracking of license keys in spreadsheets
- No visibility into remaining activation counts
- Risk of using expired or blocked keys
- Difficulty finding available keys for specific products
- No audit trail of key usage and status changes

### Why Now?
As the organization scales, the number of license keys has grown significantly. Manual management is error-prone and time-consuming. Integration with PIDKey.com provides an authoritative source for key validation and activation tracking.

### Impact
Without this system:
- IT administrators waste time searching for valid keys
- Risk of software activation failures during deployments
- No compliance tracking for license usage
- Potential overspending on redundant license purchases

## User Stories

### Primary Persona: IT Administrator

**User Story 1: Key Validation and Import**
```
AS an IT administrator
I WANT to check a list of license keys against PIDKey.com
SO THAT I can import new keys or update existing keys with current activation counts
```

**Acceptance Criteria:**
- Can submit batch of keys (newline or comma-separated) to check endpoint
- System calls PIDKey.com API with proper formatting
- Response shows which keys are new vs. existing in database
- All PIDKey.com response fields are stored (keyname, prd, eid, remaining, blocked, etc.)
- Transaction is atomic (all or nothing on database errors)

**User Story 2: Product Type Search**
```
AS an IT administrator
I WANT to search for keys using partial product names
SO THAT I can quickly find available licenses for Office 2016, Windows 10, etc.
```

**Acceptance Criteria:**
- Search "Office" returns all Office15, Office16, Office19, OfficeProPlus keys
- Search "Standard" returns Office16_StandardVL_MAK, Windows10_StandardVL_MAK, etc.
- Results show key count and total remaining activations per product
- Can filter by remaining count (e.g., only show keys with >10 activations left)
- Supports pagination for large result sets

**User Story 3: Product Inventory Overview**
```
AS an IT administrator
I WANT to see all product types and their key statistics
SO THAT I can understand license inventory at a glance
```

**Acceptance Criteria:**
- Returns list of all unique product codes (prd field)
- Shows count of keys per product
- Shows total remaining activations per product
- Shows average remaining activations per product
- Identifies products with low inventory (< 5 remaining total)

**User Story 4: Bulk Synchronization**
```
AS an IT administrator
I WANT to sync all keys in the database with PIDKey.com
SO THAT activation counts stay current without manual checking
```

**Acceptance Criteria:**
- Fetches all keys from database
- Calls PIDKey.com API in batches (max 50 keys per request to avoid timeout)
- Updates remaining count, blocked status, and last_checked timestamp
- Returns summary of updated keys and any errors
- Can be scheduled via cron job or triggered manually

## Requirements

### Functional Requirements

#### FR1: External API Integration Client
- **Component:** `backend/app/integrations/pidkey_client.py`
- **Purpose:** HTTP client for PIDKey.com API
- **Capabilities:**
  - Format keys with or without dashes (normalize input)
  - Handle newline-separated key lists (\r\n)
  - Parse JSON response array
  - Handle API errors (rate limits, timeouts, invalid API key)
  - Configurable API key and base URL
  - Async implementation using httpx
  - Request timeout: 30 seconds
  - Retry logic: 3 attempts with exponential backoff

#### FR2: Database Model
- **Component:** `backend/app/models/pidms_key.py`
- **Table Name:** `pidms_keys`
- **Fields (from PIDKey.com response):**
  - `id` (Primary Key, auto-increment)
  - `keyname` (string, unique index, without dashes: "6NRGDKHFCFY4TF7PRWFDYBF3H")
  - `keyname_with_dash` (string, display format: "6NRGD-KHFCF-Y4TF7-PRWFD-YBF3H")
  - `prd` (string, product code: "Office15_ProPlusVL_MAK", indexed for search)
  - `eid` (string, enterprise ID)
  - `is_key_type` (string, key type identifier)
  - `is_retail` (integer, 1=retail, 2=volume license)
  - `remaining` (integer, activation count, indexed for filtering)
  - `blocked` (integer, -1=not blocked, 1=blocked, indexed)
  - `errorcode` (string, nullable, error from PIDKey.com)
  - `sub` (string, subscription code)
  - `had_occurred` (integer, occurrence flag)
  - `invalid` (integer, 0=valid, 1=invalid)
  - `datetime_checked_done` (string, last check timestamp from PIDKey.com)
  - `created_at` (timestamp, when first inserted)
  - `updated_at` (timestamp, when last updated)

- **Indexes:**
  - Unique index on `keyname`
  - Index on `prd` for product search
  - Index on `remaining` for filtering
  - Index on `blocked` for status filtering

#### FR3: Service Layer
- **Component:** `backend/app/services/pidms_service.py`
- **Functions:**
  - `check_and_upsert_keys(db, keys_list, api_client)`: Call PIDKey.com, compare with DB, insert/update
  - `sync_all_keys(db, api_client)`: Batch sync all existing keys
  - `search_keys(db, product_filter, min_remaining, max_remaining, blocked_status, page, page_size)`: Fuzzy search with filters
  - `get_product_summary(db)`: Group by product and aggregate statistics
  - `get_key_by_keyname(db, keyname)`: Retrieve single key details

#### FR4: API Router
- **Component:** `backend/app/routers/pidms.py`
- **Endpoints:**

**POST /api/pidms/check**
- **Description:** Check keys against PIDKey.com and import/update in database
- **Request Body:**
  ```json
  {
    "keys": "6NRGD-KHFCF-Y4TF7-PRWFD-YBF3H\r\n8NFMQ-FTF43-RQCKR-T473J-JFHB2"
  }
  ```
- **Response:**
  ```json
  {
    "success": true,
    "summary": {
      "total_keys": 2,
      "new_keys": 1,
      "updated_keys": 1,
      "errors": 0
    },
    "results": [
      {
        "keyname": "6NRGDKHFCFY4TF7PRWFDYBF3H",
        "status": "updated",
        "prd": "Office15_ProPlusVL_MAK",
        "remaining": 2185
      }
    ]
  }
  ```

**POST /api/pidms/sync**
- **Description:** Sync all keys in database with PIDKey.com
- **Request Body:** None (or optional filter by product)
- **Response:**
  ```json
  {
    "success": true,
    "summary": {
      "total_synced": 150,
      "updated": 147,
      "errors": 3
    },
    "error_details": [
      {"keyname": "XXXXX", "error": "API timeout"}
    ]
  }
  ```

**GET /api/pidms/search**
- **Description:** Search keys with fuzzy product matching and filters
- **Query Parameters:**
  - `product` (optional): Partial match on prd field (e.g., "Office")
  - `min_remaining` (optional): Minimum activation count
  - `max_remaining` (optional): Maximum activation count
  - `blocked` (optional): Filter by blocked status (-1, 1)
  - `page` (default: 1)
  - `page_size` (default: 50, max: 100)
- **Response:**
  ```json
  {
    "total": 245,
    "page": 1,
    "page_size": 50,
    "results": [
      {
        "id": 123,
        "keyname_with_dash": "6NRGD-KHFCF-Y4TF7-PRWFD-YBF3H",
        "prd": "Office15_ProPlusVL_MAK",
        "remaining": 2185,
        "blocked": -1,
        "datetime_checked_done": "1/12/2026 1:48:27 PM (GMT+7)"
      }
    ]
  }
  ```

**GET /api/pidms/products**
- **Description:** Get all product types with statistics
- **Response:**
  ```json
  {
    "products": [
      {
        "prd": "Office15_ProPlusVL_MAK",
        "key_count": 45,
        "total_remaining": 98234,
        "avg_remaining": 2183,
        "low_inventory": false
      },
      {
        "prd": "Office16_StandardVL_MAK",
        "key_count": 12,
        "total_remaining": 345,
        "avg_remaining": 28,
        "low_inventory": true
      }
    ]
  }
  ```

#### FR5: Schema Definitions
- **Component:** `backend/app/schemas/pidms.py`
- **Schemas:**
  - `PIDMSKeyCheckRequest`: Input for /check endpoint
  - `PIDMSKeyResponse`: Single key response
  - `PIDMSCheckResponse`: Check endpoint response
  - `PIDMSSyncResponse`: Sync endpoint response
  - `PIDMSSearchResponse`: Search endpoint response with pagination
  - `PIDMSProductSummary`: Product statistics
  - `PIDMSProductsResponse`: Products endpoint response

### Non-Functional Requirements

#### NFR1: Performance
- PIDKey.com API calls must timeout after 30 seconds
- Batch operations process max 50 keys per request
- Search queries return within 2 seconds for datasets up to 10,000 keys
- Database queries use proper indexes for sub-100ms response time

#### NFR2: Security
- All endpoints require admin authentication (role: "admin")
- PIDKey.com API key stored in environment variable (PIDKEY_API_KEY)
- Never expose PIDKey.com API key in responses or logs
- Validate and sanitize all user input
- Use parameterized queries to prevent SQL injection

#### NFR3: Reliability
- Implement retry logic for transient PIDKey.com API failures
- Database transactions are atomic (rollback on error)
- Log all API calls to PIDKey.com with request/response for debugging
- Gracefully handle API rate limits (429 status)

#### NFR4: Scalability
- Support up to 10,000 keys in database
- Pagination required for all list endpoints
- Bulk sync runs in background (async task) for >100 keys
- Database indexes on search columns

#### NFR5: Maintainability
- Follow existing project structure (integrations, services, routers, models, schemas)
- Comprehensive logging using Python logging module
- Type hints for all functions
- Docstrings following Google style guide
- Unit tests for service layer logic

## Success Criteria

### Measurable Outcomes

1. **API Integration Success Rate**: >95% successful calls to PIDKey.com (excluding invalid keys)
2. **Search Performance**: <2 seconds for fuzzy search queries
3. **Data Accuracy**: 100% of PIDKey.com response fields stored correctly
4. **Admin Adoption**: All IT admins (5 users) actively use the system within 2 weeks
5. **Key Inventory Visibility**: Zero "key not found" incidents during software deployments

### Key Metrics

- Number of keys managed in database
- Average search time
- PIDKey.com API success rate
- Number of sync operations per week
- Number of low-inventory alerts triggered

## Constraints & Assumptions

### Technical Constraints
- PIDKey.com API has rate limits (unknown, must handle 429 responses)
- API key format: `keys=KEY1\r\nKEY2&justgetdescription=0&apikey=xxxxx`
- Maximum keys per request: Unknown (recommend 50 for safety)
- Response format: JSON array of objects

### Business Constraints
- Only admin users can access PIDMS endpoints
- No modification of keys via API (read-only from PIDKey.com)
- PIDKey.com API key provided by user (must be configured in .env)

### Assumptions
- PIDKey.com API is stable and available 24/7
- All keys in PIDKey.com are legitimate Microsoft licenses
- Remaining count from PIDKey.com is accurate and real-time
- Keys can have dashes or no dashes (client normalizes both formats)

## Out of Scope

### Explicitly NOT Building

1. **Key Purchase/Generation**: This system only manages existing keys, not procurement
2. **Installation Tracking**: Not tracking which keys are installed on which machines/users
3. **License Compliance Auditing**: Not enforcing license usage limits
4. **Multi-Tenant Support**: Single database for FHS organization only
5. **Key Assignment Workflow**: Not tracking which user/department owns which key
6. **Email Notifications**: No alerts when keys run low (future enhancement)
7. **Key Expiration Management**: Not tracking key expiration dates (PIDKey.com doesn't provide)
8. **Historical Trend Analysis**: Not storing time-series data of activation count changes
9. **Export to Excel/CSV**: Search results are JSON only (frontend can export if needed)

## Dependencies

### External Dependencies
- **PIDKey.com API**: Must have valid API key and API must be available
  - Endpoint: `https://pidkey.com/ajax/pidms_api`
  - Requires: API key parameter
  - Risk: API downtime or rate limiting (mitigation: retry logic + caching)

### Internal Dependencies
- **Authentication System**: Requires existing admin role checking (already implemented in `app/core/security.py`)
- **Database**: PostgreSQL with SQLAlchemy async support (already configured)
- **httpx Library**: For async HTTP requests (already in use for FHS HRS client)

### Team Dependencies
- **Backend Team**: Implements all components (client, service, router, models, schemas)
- **DevOps**: Configures PIDKEY_API_KEY environment variable in deployment

## Technical Architecture

### Component Diagram

```
┌─────────────┐
│   Admin UI  │ (Future: Frontend)
└──────┬──────┘
       │ HTTP (JSON)
       ▼
┌─────────────────────────────────────┐
│  FastAPI Router                     │
│  /api/pidms/check                   │
│  /api/pidms/sync                    │
│  /api/pidms/search                  │
│  /api/pidms/products                │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  PIDMS Service Layer                │
│  - check_and_upsert_keys()          │
│  - sync_all_keys()                  │
│  - search_keys()                    │
│  - get_product_summary()            │
└──────┬────────────┬─────────────────┘
       │            │
       │            ▼
       │      ┌─────────────────┐
       │      │ PIDKey Client   │
       │      │ (integrations)  │
       │      └────────┬────────┘
       │               │
       │               ▼
       │      ┌─────────────────┐
       │      │  PIDKey.com API │
       │      └─────────────────┘
       │
       ▼
┌─────────────────┐
│  Database       │
│  (pidms_keys)   │
└─────────────────┘
```

### File Structure

```
backend/app/
├── integrations/
│   ├── __init__.py
│   └── pidkey_client.py         # NEW: HTTP client for PIDKey.com API
├── models/
│   ├── __init__.py
│   └── pidms_key.py             # NEW: SQLAlchemy model for pidms_keys table
├── schemas/
│   ├── __init__.py
│   └── pidms.py                 # NEW: Pydantic schemas for request/response
├── services/
│   ├── __init__.py
│   └── pidms_service.py         # NEW: Business logic for key management
├── routers/
│   ├── __init__.py
│   └── pidms.py                 # NEW: FastAPI router with 4 endpoints
└── main.py                      # UPDATE: Register pidms router
```

## Database Schema

### Table: pidms_keys

```sql
CREATE TABLE pidms_keys (
    id SERIAL PRIMARY KEY,
    keyname VARCHAR(255) NOT NULL UNIQUE,
    keyname_with_dash VARCHAR(255) NOT NULL,
    prd VARCHAR(255) NOT NULL,
    eid VARCHAR(255),
    is_key_type VARCHAR(50),
    is_retail INTEGER,
    remaining INTEGER NOT NULL DEFAULT 0,
    blocked INTEGER NOT NULL DEFAULT -1,
    errorcode VARCHAR(255),
    sub VARCHAR(255),
    had_occurred INTEGER DEFAULT 0,
    invalid INTEGER DEFAULT 0,
    datetime_checked_done VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_pidms_keys_prd ON pidms_keys(prd);
CREATE INDEX idx_pidms_keys_remaining ON pidms_keys(remaining);
CREATE INDEX idx_pidms_keys_blocked ON pidms_keys(blocked);
```

## API Request/Response Examples

### Example 1: Check Keys (POST /api/pidms/check)

**Request:**
```bash
curl -X POST https://fhs-prosight.com/api/pidms/check \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "keys": "6NRGD-KHFCF-Y4TF7-PRWFD-YBF3H\r\n8NFMQ-FTF43-RQCKR-T473J-JFHB2"
  }'
```

**Response:**
```json
{
  "success": true,
  "summary": {
    "total_keys": 2,
    "new_keys": 1,
    "updated_keys": 1,
    "errors": 0
  },
  "results": [
    {
      "keyname": "6NRGDKHFCFY4TF7PRWFDYBF3H",
      "keyname_with_dash": "6NRGD-KHFCF-Y4TF7-PRWFD-YBF3H",
      "status": "updated",
      "prd": "Office15_ProPlusVL_MAK",
      "remaining": 2185,
      "blocked": -1
    },
    {
      "keyname": "8NFMQFTF43RQCKRT473JJFHB2",
      "keyname_with_dash": "8NFMQ-FTF43-RQCKR-T473J-JFHB2",
      "status": "new",
      "prd": "Office16_StandardVL_MAK",
      "remaining": 1994,
      "blocked": -1
    }
  ]
}
```

### Example 2: Search Keys (GET /api/pidms/search?product=Office&min_remaining=100)

**Request:**
```bash
curl -X GET "https://fhs-prosight.com/api/pidms/search?product=Office&min_remaining=100&page=1&page_size=10" \
  -H "Authorization: Bearer <admin_token>"
```

**Response:**
```json
{
  "total": 87,
  "page": 1,
  "page_size": 10,
  "results": [
    {
      "id": 1,
      "keyname": "6NRGDKHFCFY4TF7PRWFDYBF3H",
      "keyname_with_dash": "6NRGD-KHFCF-Y4TF7-PRWFD-YBF3H",
      "prd": "Office15_ProPlusVL_MAK",
      "eid": "XXXXX-02165-456-008091-03-1033-9200.0000-1002022",
      "is_retail": 2,
      "remaining": 2185,
      "blocked": -1,
      "datetime_checked_done": "1/12/2026 1:48:27 PM (GMT+7)",
      "created_at": "2026-01-12T06:30:15Z",
      "updated_at": "2026-01-12T06:48:27Z"
    }
  ]
}
```

## Implementation Plan

### Phase 1: Foundation (Week 1)
1. Create PIDKey.com client in `integrations/pidkey_client.py`
2. Create database model in `models/pidms_key.py`
3. Create Pydantic schemas in `schemas/pidms.py`
4. Run database migration to create `pidms_keys` table

### Phase 2: Core API (Week 2)
1. Implement service layer functions in `services/pidms_service.py`
2. Create FastAPI router with 4 endpoints in `routers/pidms.py`
3. Register router in `main.py`
4. Add admin authentication middleware

### Phase 3: Testing & Refinement (Week 3)
1. Unit tests for service layer
2. Integration tests for API endpoints
3. Manual testing with real PIDKey.com API
4. Performance optimization (indexes, query tuning)

### Phase 4: Documentation & Deployment
1. API documentation (OpenAPI/Swagger)
2. Admin user guide
3. Environment variable setup guide
4. Deploy to production

## Risk Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| PIDKey.com API downtime | High | Low | Implement retry logic, cache last known status, graceful degradation |
| API rate limiting | Medium | Medium | Batch requests, exponential backoff, queue system for large syncs |
| Invalid API key | High | Low | Validate API key on startup, clear error messages |
| Database performance with 10k+ keys | Medium | Medium | Proper indexing, query optimization, pagination enforcement |
| Duplicate key insertion race condition | Low | Low | Unique constraint on keyname, handle upsert atomically |

## Future Enhancements (Post-MVP)

1. **Installation Tracking**: Track which keys are assigned to which users/machines
2. **Email Alerts**: Notify admins when product inventory falls below threshold
3. **Historical Analytics**: Store time-series data to visualize activation trends
4. **Export Feature**: Export search results to CSV/Excel
5. **Scheduled Sync**: Cron job to auto-sync all keys daily
6. **Key Reservation**: Allow admins to "reserve" keys for upcoming deployments
7. **Multi-Product Dashboard**: Visual dashboard showing key inventory by product type

## Glossary

- **PIDKey.com**: External API service that validates Microsoft product keys and returns activation status
- **Product Code (prd)**: Identifier for license type (e.g., "Office15_ProPlusVL_MAK")
- **Remaining**: Number of activations left for a license key
- **Blocked**: Status flag indicating if key is blocked by Microsoft (-1 = not blocked, 1 = blocked)
- **EID**: Enterprise ID associated with the license key
- **Volume License (VL)**: Microsoft licensing program for organizations (is_retail=2)
- **Retail License**: Consumer license for individual use (is_retail=1)
- **MAK**: Multiple Activation Key (volume license type)
