# PIDMS Info API

API for managing Microsoft product license keys via PIDKey.com integration.

## Features

- ✅ Check and import product keys from PIDKey.com
- ✅ Search keys with fuzzy product matching
- ✅ View product inventory statistics
- ✅ Bulk sync all keys with PIDKey.com (batched)
- ✅ Admin-only authentication

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Router    │─────▶│   Service    │─────▶│ Integration │
│  (pidms.py) │      │   Layer      │      │   Client    │
└─────────────┘      └──────────────┘      └─────────────┘
                            │                      │
                            ▼                      ▼
                     ┌──────────────┐      ┌─────────────┐
                     │  PostgreSQL  │      │ PIDKey.com  │
                     │   Database   │      │     API     │
                     └──────────────┘      └─────────────┘
```

## Setup

### 1. Environment Configuration

Create `.env` file in `backend/` directory:

```bash
PIDKEY_API_KEY=your_api_key_here
PIDKEY_BASE_URL=https://pidkey.com/ajax/pidms_api
```

### 2. Database Migration

```bash
# Run migration
cd backend
alembic upgrade head

# Verify table created
psql -d fhs_prosight -c "\d pidms_keys"
```

### 3. Start Server

```bash
cd backend
uvicorn app.main:app --reload
```

Server starts on: http://localhost:8000

### 4. Access API Documentation

Open: http://localhost:8000/docs

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/pidms/check | Check and import keys |
| GET | /api/pidms/search | Search keys with filters |
| GET | /api/pidms/products | View product statistics |
| POST | /api/pidms/sync | Sync all keys with PIDKey.com |

All endpoints require admin authentication.

## Quick Start

### 1. Get Admin Token

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_password"}'
```

### 2. Import Your First Keys

```bash
export ADMIN_TOKEN="eyJ..."

curl -X POST http://localhost:8000/api/pidms/check \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "keys": "6NRGD-KHFCF-Y4TF7-PRWFD-YBF3H\r\n8NFMQ-FTF43-RQCKR-T473J-JFHB2"
  }'
```

### 3. Search for Office Keys

```bash
curl -X GET "http://localhost:8000/api/pidms/search?product=Office&min_remaining=100" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

## Usage Examples

See [USAGE.md](USAGE.md) for detailed examples.

## Performance

- **Search**: < 2 seconds for 10,000+ keys
- **Sync Batch**: < 30 seconds per 50 keys
- **Check**: < 5 seconds for 50 keys

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues.

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment checklist.

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with asyncpg
- **ORM**: SQLAlchemy 2.0 (async)
- **Migration**: Alembic
- **HTTP Client**: httpx (async)
- **Retry Logic**: Tenacity
- **Validation**: Pydantic v2
