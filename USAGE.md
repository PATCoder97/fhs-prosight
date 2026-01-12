# PIDMS API Usage Guide

Complete guide for using the PIDMS API endpoints.

## Authentication

All endpoints require admin authentication.

### Get Admin Token

```bash
curl -X POST http://localhost:8000/api/auth/login   -H "Content-Type: application/json"   -d '{"username": "admin", "password": "your_password"}'
```

**Export token:**
```bash
export ADMIN_TOKEN="eyJ..."
```

---

## 1. Check and Import Product Keys

### Endpoint
```
POST /api/pidms/check
```

### Example: Import Multiple Keys

```bash
curl -X POST http://localhost:8000/api/pidms/check   -H "Authorization: Bearer $ADMIN_TOKEN"   -H "Content-Type: application/json"   -d '{
    "keys": "6NRGD-KHFCF-Y4TF7-PRWFD-YBF3H
8NFMQ-FTF43-RQCKR-T473J-JFHB2"
  }'
```

### Response

```json
{
  "success": true,
  "summary": {
    "total_keys": 2,
    "new_keys": 2,
    "updated_keys": 0,
    "errors": 0
  },
  "results": [...]
}
```

---

## 2. Search Product Keys

### Endpoint
```
GET /api/pidms/search
```

### Example: Search Office Products

```bash
curl -X GET "http://localhost:8000/api/pidms/search?product=Office&min_remaining=100"   -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Example: Find Low Inventory

```bash
curl -X GET "http://localhost:8000/api/pidms/search?max_remaining=50"   -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

## 3. View Product Statistics

### Endpoint
```
GET /api/pidms/products
```

### Example

```bash
curl -X GET "http://localhost:8000/api/pidms/products"   -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Response

```json
{
  "products": [
    {
      "prd": "Office15_ProPlusVL_MAK",
      "key_count": 45,
      "total_remaining": 98234,
      "avg_remaining": 2183.2,
      "low_inventory": false
    }
  ]
}
```

---

## 4. Sync All Keys

### Endpoint
```
POST /api/pidms/sync
```

### Example: Sync All

```bash
curl -X POST http://localhost:8000/api/pidms/sync   -H "Authorization: Bearer $ADMIN_TOKEN"   -H "Content-Type: application/json"   -d '{}'
```

### Example: Sync Only Office Products

```bash
curl -X POST http://localhost:8000/api/pidms/sync   -H "Authorization: Bearer $ADMIN_TOKEN"   -H "Content-Type: application/json"   -d '{"product_filter": "Office"}'
```

---

## Common Workflows

### Workflow 1: Initial Key Import

```bash
# Import keys
curl -X POST http://localhost:8000/api/pidms/check   -H "Authorization: Bearer $ADMIN_TOKEN"   -d '{"keys": "KEY1
KEY2
KEY3"}'

# Verify import
curl -X GET "http://localhost:8000/api/pidms/products"   -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Workflow 2: Daily Sync

```bash
# Sync all keys
curl -X POST http://localhost:8000/api/pidms/sync   -H "Authorization: Bearer $ADMIN_TOKEN"   -d '{}'

# Check low inventory
curl -X GET "http://localhost:8000/api/pidms/products"   -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

## Error Responses

### 401 Unauthorized
```json
{"detail": "Not authenticated"}
```

### 403 Forbidden
```json
{"detail": "Insufficient permissions"}
```

### 422 Validation Error
```json
{"detail": "No valid keys provided"}
```

### 503 Service Unavailable
```json
{"detail": "PIDKey.com API rate limit exceeded. Please try again later."}
```
