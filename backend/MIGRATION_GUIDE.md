# Database Migration Guide - API Keys Table

## 📋 Tổng quan

Migration này tạo bảng `api_keys` để hỗ trợ API key authentication cho các endpoint import.

**Migration ID**: `0492c2f08470_add_api_keys_table`

---

## 🚀 Chạy Migration

### Bước 1: Kiểm tra trạng thái migration hiện tại

```bash
cd backend
alembic current
```

### Bước 2: Xem preview migration sẽ chạy

```bash
alembic history
```

Kết quả:
```
0846970e5b1f -> 0492c2f08470 (head), add_api_keys_table
<base> -> 0846970e5b1f, initial_schema_all_tables
```

### Bước 3: Chạy migration

```bash
# Upgrade to latest version
alembic upgrade head
```

Hoặc upgrade cụ thể migration này:
```bash
alembic upgrade 0492c2f08470
```

### Bước 4: Verify migration thành công

```bash
# Check current version
alembic current

# Expected output:
# 0492c2f08470 (head)
```

---

## 📊 Cấu trúc bảng `api_keys`

```sql
CREATE TABLE api_keys (
    id VARCHAR(64) PRIMARY KEY,              -- SHA256 hash của API key
    name VARCHAR(100) NOT NULL,              -- Tên gọi (e.g., "HRS Import Service")
    description VARCHAR(255),                -- Mô tả mục đích sử dụng
    key_prefix VARCHAR(16) NOT NULL,         -- Prefix để nhận diện (e.g., "fhs_1234")
    scopes VARCHAR(255) NOT NULL,            -- Phạm vi quyền (comma-separated)
    is_active BOOLEAN NOT NULL DEFAULT 1,    -- Trạng thái active/revoked
    created_by VARCHAR(10),                  -- Employee ID người tạo
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_used_at DATETIME,                   -- Lần sử dụng cuối
    expires_at DATETIME                      -- Ngày hết hạn (NULL = không hết hạn)
);

-- Indexes
CREATE INDEX ix_api_keys_id ON api_keys(id);
CREATE INDEX ix_api_keys_key_prefix ON api_keys(key_prefix);
```

---

## 🔄 Rollback Migration (nếu cần)

Nếu cần quay lại version trước:

```bash
# Downgrade về version trước đó
alembic downgrade 0846970e5b1f

# Hoặc downgrade 1 step
alembic downgrade -1
```

⚠️ **Cảnh báo**: Downgrade sẽ xóa bảng `api_keys` và tất cả dữ liệu trong đó!

---

## ✅ Kiểm tra sau Migration

### 1. Verify bảng đã được tạo

Kết nối vào database và chạy:

```sql
-- Check if table exists
SHOW TABLES LIKE 'api_keys';

-- Check table structure
DESCRIBE api_keys;

-- Check indexes
SHOW INDEX FROM api_keys;
```

### 2. Test tạo API key

```bash
# Start server
cd backend
uvicorn app.main:app --reload

# Create test API key (need admin JWT token)
curl -X POST "http://localhost:8000/api/api-keys" \
  -H "Authorization: Bearer YOUR_ADMIN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Key",
    "scopes": ["evaluations:import"],
    "expires_days": 30
  }'
```

### 3. Test sử dụng API key

```bash
# Get the api_key from previous response
API_KEY="fhs_xxxxx..."

# Test import endpoint
curl -X POST "http://localhost:8000/api/evaluations/upload" \
  -H "X-API-Key: $API_KEY" \
  -F "file=@test_evaluations.xlsx"
```

---

## 🐛 Troubleshooting

### Lỗi: "Target database is not up to date"

```bash
# Solution: Upgrade to head first
alembic upgrade head
```

### Lỗi: "Can't locate revision identified by..."

```bash
# Solution: Check alembic history
alembic history

# Reset to base (careful - this drops all tables!)
# alembic downgrade base
# alembic upgrade head
```

### Lỗi: "sqlalchemy.exc.OperationalError: (1050, "Table 'api_keys' already exists")"

Bảng đã tồn tại. Có 2 cách xử lý:

**Cách 1**: Skip migration này (không khuyến khích)
```bash
alembic stamp 0492c2f08470
```

**Cách 2**: Xóa bảng và chạy lại migration (mất dữ liệu!)
```sql
DROP TABLE api_keys;
```
Sau đó chạy lại:
```bash
alembic upgrade head
```

---

## 📝 Migration trong Docker

Nếu deploy bằng Docker, migration sẽ tự động chạy khi container start (xem `start.sh`).

Để chạy manual trong container:

```bash
# Exec into container
docker exec -it fhs-backend bash

# Run migration
alembic upgrade head
```

---

## 🔍 Kiểm tra Migration Log

```bash
# View alembic log
alembic show 0492c2f08470

# View SQL that will be executed (without running)
alembic upgrade 0492c2f08470 --sql
```

---

## 📚 References

- Alembic Documentation: https://alembic.sqlalchemy.org/
- FastAPI + Alembic Guide: https://fastapi.tiangolo.com/tutorial/sql-databases/
- Migration file: `backend/alembic/versions/0492c2f08470_add_api_keys_table.py`

---

## ✨ Sau khi Migration thành công

1. ✅ Bảng `api_keys` đã được tạo
2. ✅ Có thể tạo API keys qua admin endpoint
3. ✅ Có thể sử dụng API keys để import dữ liệu
4. ✅ System ready for production!

**Next steps**: Xem [API_KEY_QUICKSTART.md](./API_KEY_QUICKSTART.md) để bắt đầu sử dụng.
