# 🎯 Next Steps - Testing & Deployment Guide

## ✅ Đã hoàn thành

Tất cả code đã được commit và deploy thành công:
- ✅ 8 commits, all builds passed
- ✅ API Key authentication system
- ✅ Auto-update employee dormitory
- ✅ Comprehensive documentation
- ✅ Automated test script

---

## 🚀 Bước tiếp theo để Test & Deploy

### **Bước 1: Run Database Migration**

```bash
cd backend
alembic upgrade head
```

**Verify migration thành công:**
```bash
alembic current
# Expected: 0492c2f08470 (head)
```

**Kiểm tra bảng đã tạo:**
```sql
-- Connect to your database and run:
SHOW TABLES LIKE 'api_keys';
DESCRIBE api_keys;
```

---

### **Bước 2: Start Backend Server**

```bash
cd backend
uvicorn app.main:app --reload
```

Server sẽ chạy tại: http://localhost:8000

**Verify server started:**
- Mở browser: http://localhost:8000/docs
- Bạn sẽ thấy Swagger UI với các endpoints mới:
  - `/api/api-keys` (POST, GET, DELETE)
  - `/api/evaluations/upload` (with X-API-Key)
  - `/api/dormitory-bills/import` (with X-API-Key)

---

### **Bước 3: Tạo API Key (cần Admin JWT token)**

#### Option 1: Dùng Swagger UI (http://localhost:8000/docs)

1. Click vào endpoint `POST /api/api-keys`
2. Click "Try it out"
3. Click "Authorize" và nhập JWT token
4. Nhập request body:
```json
{
  "name": "HRS Import Service",
  "description": "API key for automated data imports",
  "scopes": ["evaluations:import", "dormitory-bills:import"],
  "expires_days": 365
}
```
5. Click "Execute"

#### Option 2: Dùng curl

```bash
curl -X POST "http://localhost:8000/api/api-keys" \
  -H "Authorization: Bearer YOUR_ADMIN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "HRS Import Service",
    "description": "API key for automated data imports",
    "scopes": ["evaluations:import", "dormitory-bills:import"],
    "expires_days": 365
  }'
```

**⚠️ IMPORTANT**: Save the `api_key` from response - it's only shown once!

Example response:
```json
{
  "api_key": "fhs_1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
  "key_info": {...}
}
```

---

### **Bước 4: Test API Key Authentication**

#### Test 1: Import Dormitory Bills

```bash
API_KEY="fhs_xxxxx..."  # Replace with your actual API key

curl -X POST "http://localhost:8000/api/dormitory-bills/import" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "bills": [
      {
        "employee_id": "VNW0018983",
        "term_code": "26A",
        "dorm_code": "A01",
        "factory_location": "North Wing",
        "elec_last_index": 1000.0,
        "elec_curr_index": 1250.0,
        "elec_usage": 250.0,
        "elec_amount": 1250000,
        "water_last_index": 500.0,
        "water_curr_index": 565.0,
        "water_usage": 65.0,
        "water_amount": 325000,
        "shared_fee": 100000,
        "management_fee": 200000,
        "total_amount": 1875000
      }
    ]
  }'
```

**Expected response:**
```json
{
  "success": true,
  "summary": {
    "total_records": 1,
    "created": 1,
    "updated": 0,
    "errors": 0,
    "employees_updated": 1  // ← Employee dorm_id được tự động update!
  },
  "error_details": []
}
```

#### Test 2: Verify Employee Dormitory Updated

```bash
# Check employee table
SELECT id, name_en, dorm_id FROM employees WHERE id = 'VNW0018983';
```

**Expected**: `dorm_id` should now be `'A01'`

---

### **Bước 5: Run Automated Test Suite**

```bash
cd backend

# Install dependencies if needed
pip install requests

# Run test script
python test_api_key_system.py --admin-token YOUR_ADMIN_JWT_TOKEN
```

**Expected output:**
```
🚀 API Key System Test Suite
============================================================
✅ API key created successfully!
✅ Found X API key(s)
✅ Import successful!
✅ Correctly rejected invalid API key (401)
✅ Correctly rejected missing API key (401)
✅ API key revoked successfully!

📊 Test Summary
============================================================
Total Tests: 6
Passed: 6
Failed: 0

🎉 All tests passed!
```

---

### **Bước 6: Test với Frontend (Optional)**

Nếu bạn muốn test từ frontend/Postman:

#### Headers cần thiết:
```
X-API-Key: fhs_xxxxx...
Content-Type: application/json (for JSON imports)
Content-Type: multipart/form-data (for file uploads)
```

#### Example Postman Collection:

**Request 1: Import Dormitory Bills**
- Method: POST
- URL: `http://localhost:8000/api/dormitory-bills/import`
- Headers: `X-API-Key: fhs_xxxxx...`
- Body (JSON):
```json
{
  "bills": [...]
}
```

**Request 2: Upload Evaluations**
- Method: POST
- URL: `http://localhost:8000/api/evaluations/upload`
- Headers: `X-API-Key: fhs_xxxxx...`
- Body (form-data):
  - Key: `file`
  - Type: File
  - Value: [Select .xlsx file]

---

## 🐛 Troubleshooting

### Issue 1: Migration fails with "Table already exists"

**Solution:**
```bash
# Check current migration version
alembic current

# If already at 0492c2f08470, migration already ran
# If not, try:
alembic upgrade head
```

### Issue 2: "Invalid API key" error

**Check:**
- API key format: should be `fhs_` + 64 hex characters (total 68 chars)
- API key is active (check `is_active` in database)
- API key not expired (check `expires_at`)

### Issue 3: "Insufficient scope" error

**Solution:**
Create a new API key with correct scopes:
```json
{
  "scopes": ["evaluations:import", "dormitory-bills:import"]
}
```

### Issue 4: Cannot get Admin JWT token

**Solution:**
1. Login as admin user via `/api/auth/login`
2. Get JWT token from response or cookie
3. Use this token to create API keys

---

## 📦 Production Deployment

### Docker Deployment (Automatic)

Migration sẽ tự động chạy khi container start (xem `start.sh`):

```bash
# Build and deploy
docker-compose up -d --build

# Check logs
docker logs fhs-backend

# Verify migration
docker exec -it fhs-backend alembic current
```

### Manual Production Setup

1. **Set environment variables:**
```bash
export DATABASE_URL="postgresql://..."
export SECRET_KEY="your-secret-key"
```

2. **Run migration:**
```bash
alembic upgrade head
```

3. **Start server:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

4. **Create production API keys:**
```bash
curl -X POST "https://your-domain.com/api/api-keys" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production HRS Import",
    "scopes": ["evaluations:import", "dormitory-bills:import"],
    "expires_days": 365
  }'
```

5. **Share API key with HRS team:**
- Send API key via secure channel (NOT email/Slack!)
- Use password manager or encrypted messaging
- Provide documentation: [API_KEY_QUICKSTART.md](./backend/API_KEY_QUICKSTART.md)

---

## 🔐 Security Checklist

Before going to production:

- [ ] Run database migration
- [ ] Create production API keys (with expiration dates)
- [ ] Store API keys in secure vault (not in code!)
- [ ] Test all import endpoints with API keys
- [ ] Verify employee dormitory auto-update works
- [ ] Enable HTTPS in production
- [ ] Set up monitoring for API key usage
- [ ] Document API keys for HRS team
- [ ] Set up alerts for expired keys
- [ ] Review API key permissions regularly

---

## 📚 Documentation References

| Document | Description | Location |
|----------|-------------|----------|
| Quick Start Guide | Fast reference for common tasks | [API_KEY_QUICKSTART.md](./backend/API_KEY_QUICKSTART.md) |
| Full API Guide | Detailed documentation + examples | [API_KEY_GUIDE.md](./backend/API_KEY_GUIDE.md) |
| Migration Guide | Database migration instructions | [MIGRATION_GUIDE.md](./backend/MIGRATION_GUIDE.md) |
| Project Summary | Complete feature overview | [PROJECT_UPDATE_SUMMARY.md](./PROJECT_UPDATE_SUMMARY.md) |
| Test Script | Automated testing | [test_api_key_system.py](./backend/test_api_key_system.py) |

---

## 📞 Support

Nếu gặp vấn đề:

1. Check logs: `docker logs fhs-backend` hoặc `uvicorn` output
2. Check migration status: `alembic current`
3. Review documentation above
4. Check GitHub issues
5. Contact system administrator

---

## 🎉 Summary

**Current Status:**
- ✅ All code committed and deployed
- ✅ All GitHub Actions passed
- ✅ Documentation complete
- ✅ Test script ready

**To Go Live:**
1. Run migration: `alembic upgrade head`
2. Test locally with test script
3. Create production API keys
4. Share with HRS team
5. Monitor usage

**You're ready to deploy!** 🚀

---

Last updated: 2026-01-17 01:35:00 UTC
