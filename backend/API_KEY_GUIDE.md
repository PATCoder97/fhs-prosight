# API Key Authentication Guide

## Overview

The FHS Pro Sight system now supports API key authentication for import endpoints. This allows external systems (like HRS) to import data without requiring user login credentials.

## Features

- **Scope-based access control**: API keys can be limited to specific operations
- **Expiration dates**: Keys can be set to expire after a specified period
- **Activity tracking**: Last usage timestamp is recorded
- **Revocation**: Keys can be deactivated without deletion for audit purposes
- **Secure storage**: Keys are hashed (SHA256) in the database

## Available Scopes

| Scope | Description | Endpoint |
|-------|-------------|----------|
| `evaluations:import` | Import evaluation data from Excel | `POST /api/evaluations/upload` |
| `dormitory-bills:import` | Import dormitory billing data from JSON | `POST /api/dormitory-bills/import` |

## Creating an API Key

### Prerequisites
- Admin role required
- Authenticated session

### Step 1: Create API Key (Admin Only)

**Request:**
```bash
POST /api/api-keys
Content-Type: application/json
Authorization: Bearer <your-jwt-token>

{
  "name": "HRS Import Service",
  "description": "API key for automated data imports from HRS system",
  "scopes": ["evaluations:import", "dormitory-bills:import"],
  "expires_days": 365
}
```

**Response:**
```json
{
  "api_key": "fhs_1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
  "key_info": {
    "id": "hash123...",
    "name": "HRS Import Service",
    "key_prefix": "fhs_1234",
    "scopes": "evaluations:import,dormitory-bills:import",
    "is_active": true,
    "created_by": "VNW0012345",
    "created_at": "2026-01-17T01:00:00Z",
    "last_used_at": null,
    "expires_at": "2027-01-17T01:00:00Z"
  }
}
```

⚠️ **Important**: The actual API key (`api_key` field) is only shown ONCE. Save it securely - it cannot be retrieved later.

## Using an API Key

### Method 1: Using curl

```bash
# Upload evaluation Excel file
curl -X POST "http://your-domain/api/evaluations/upload" \
  -H "X-API-Key: fhs_1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef" \
  -F "file=@evaluations.xlsx"

# Import dormitory bills
curl -X POST "http://your-domain/api/dormitory-bills/import" \
  -H "X-API-Key: fhs_1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef" \
  -H "Content-Type: application/json" \
  -d '{
    "bills": [
      {
        "employee_id": "VNW0012345",
        "term_code": "25A",
        "dorm_code": "A01",
        "factory_location": "North Wing",
        "elec_amount": 1249000,
        "water_amount": 327500,
        "shared_fee": 100000,
        "management_fee": 200000,
        "total_amount": 1876500
      }
    ]
  }'
```

### Method 2: Using Python

```python
import requests

API_KEY = "fhs_1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
BASE_URL = "http://your-domain/api"

# Upload evaluations
with open('evaluations.xlsx', 'rb') as f:
    response = requests.post(
        f"{BASE_URL}/evaluations/upload",
        headers={"X-API-Key": API_KEY},
        files={"file": f}
    )
    print(response.json())

# Import dormitory bills
bills_data = {
    "bills": [
        {
            "employee_id": "VNW0012345",
            "term_code": "25A",
            "dorm_code": "A01",
            "total_amount": 1876500
            # ... other fields
        }
    ]
}

response = requests.post(
    f"{BASE_URL}/dormitory-bills/import",
    headers={"X-API-Key": API_KEY},
    json=bills_data
)
print(response.json())
```

### Method 3: Using JavaScript/Node.js

```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

const API_KEY = 'fhs_1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef';
const BASE_URL = 'http://your-domain/api';

// Upload evaluations
async function uploadEvaluations() {
  const form = new FormData();
  form.append('file', fs.createReadStream('evaluations.xlsx'));

  const response = await axios.post(
    `${BASE_URL}/evaluations/upload`,
    form,
    {
      headers: {
        'X-API-Key': API_KEY,
        ...form.getHeaders()
      }
    }
  );

  console.log(response.data);
}

// Import dormitory bills
async function importBills() {
  const response = await axios.post(
    `${BASE_URL}/dormitory-bills/import`,
    {
      bills: [
        {
          employee_id: 'VNW0012345',
          term_code: '25A',
          dorm_code: 'A01',
          total_amount: 1876500
          // ... other fields
        }
      ]
    },
    {
      headers: {
        'X-API-Key': API_KEY
      }
    }
  );

  console.log(response.data);
}
```

## Managing API Keys (Admin Only)

### List All API Keys

```bash
GET /api/api-keys
Authorization: Bearer <your-jwt-token>
```

### Revoke an API Key

```bash
DELETE /api/api-keys/{key_id}
Authorization: Bearer <your-jwt-token>
```

This deactivates the key but keeps it in database for audit purposes.

### Permanently Delete an API Key

```bash
DELETE /api/api-keys/{key_id}/permanent
Authorization: Bearer <your-jwt-token>
```

⚠️ This permanently removes the key from the database.

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Invalid API key"
}
```

### 403 Forbidden
```json
{
  "detail": "API key does not have required scope: evaluations:import"
}
```

### API Key Expired
```json
{
  "detail": "API key has expired"
}
```

### API Key Inactive
```json
{
  "detail": "API key is inactive"
}
```

## Security Best Practices

1. **Store API keys securely**: Never commit API keys to version control
2. **Use environment variables**: Store keys in environment variables or secure vaults
3. **Set expiration dates**: Use the `expires_days` parameter when creating keys
4. **Limit scopes**: Only grant the minimum required scopes
5. **Rotate keys regularly**: Create new keys and revoke old ones periodically
6. **Monitor usage**: Check the `last_used_at` field to detect unused or compromised keys
7. **Revoke immediately**: If a key is compromised, revoke it immediately

## Example: Automated Import Script

```python
#!/usr/bin/env python3
"""
Automated data import script for HRS system
"""
import os
import requests
from datetime import datetime

# Configuration
API_KEY = os.environ.get('FHS_API_KEY')
BASE_URL = os.environ.get('FHS_BASE_URL', 'http://your-domain/api')

def import_dormitory_bills(bills_file):
    """Import dormitory bills from JSON file"""
    with open(bills_file, 'r') as f:
        bills_data = json.load(f)

    response = requests.post(
        f"{BASE_URL}/dormitory-bills/import",
        headers={"X-API-Key": API_KEY},
        json=bills_data
    )

    if response.status_code == 200:
        result = response.json()
        print(f"✅ Import successful:")
        print(f"  - Total records: {result['summary']['total_records']}")
        print(f"  - Created: {result['summary']['created']}")
        print(f"  - Updated: {result['summary']['updated']}")
        print(f"  - Errors: {result['summary']['errors']}")
        print(f"  - Employees updated: {result['summary']['employees_updated']}")
    else:
        print(f"❌ Import failed: {response.text}")

if __name__ == '__main__':
    import_dormitory_bills('bills.json')
```

## Troubleshooting

### Issue: "API key required"
- **Solution**: Ensure you're including the `X-API-Key` header in your request

### Issue: "Invalid API key"
- **Solution**: Check that you're using the correct API key value
- The key should start with `fhs_` and be 68 characters long

### Issue: "Insufficient scope"
- **Solution**: The API key doesn't have the required scope for this endpoint
- Contact admin to create a new key with the correct scopes

### Issue: "API key has expired"
- **Solution**: The key has reached its expiration date
- Contact admin to create a new key

## Additional Features

### Automatic Employee Dormitory Update

When importing dormitory bills, the system automatically:
- Updates the `dorm_id` field in the `employees` table
- Syncs employee dormitory information with billing data
- Returns the count of updated employees in the response

This ensures employee records always reflect their current dormitory assignment.

## Support

For questions or issues with API keys, contact the system administrator or raise an issue in the project repository.
