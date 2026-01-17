# API Key Quick Start Guide

## 🚀 Tạo API Key (Admin)

### 1. Đăng nhập với tài khoản Admin

### 2. Tạo API Key mới

```bash
curl -X POST "http://localhost:8000/api/api-keys" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "HRS Import Service",
    "description": "API key cho import tự động từ HRS",
    "scopes": ["evaluations:import", "dormitory-bills:import"],
    "expires_days": 365
  }'
```

**Response:**
```json
{
  "api_key": "fhs_1234567890abcdef...",
  "key_info": {...}
}
```

⚠️ **LƯU Ý**: API key chỉ hiển thị 1 lần duy nhất! Lưu ngay vào nơi an toàn.

---

## 📤 Sử dụng API Key để Import Dữ liệu

### Import Dormitory Bills

```bash
curl -X POST "http://localhost:8000/api/dormitory-bills/import" \
  -H "X-API-Key: fhs_1234567890abcdef..." \
  -H "Content-Type: application/json" \
  -d '{
    "bills": [
      {
        "employee_id": "VNW0012345",
        "term_code": "25A",
        "dorm_code": "A01",
        "total_amount": 1876500
      }
    ]
  }'
```

**Tính năng tự động**: Khi import bills, hệ thống sẽ tự động cập nhật `dorm_id` trong bảng `employees`!

### Upload Evaluations

```bash
curl -X POST "http://localhost:8000/api/evaluations/upload" \
  -H "X-API-Key: fhs_1234567890abcdef..." \
  -F "file=@evaluations.xlsx"
```

---

## 🔐 Quản lý API Keys (Admin)

### Xem danh sách API keys

```bash
curl "http://localhost:8000/api/api-keys" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Vô hiệu hóa API key

```bash
curl -X DELETE "http://localhost:8000/api/api-keys/{key_id}" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Xóa vĩnh viễn API key

```bash
curl -X DELETE "http://localhost:8000/api/api-keys/{key_id}/permanent" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 📋 Available Scopes

| Scope | Endpoint | Mô tả |
|-------|----------|-------|
| `evaluations:import` | `POST /api/evaluations/upload` | Import dữ liệu đánh giá từ Excel |
| `dormitory-bills:import` | `POST /api/dormitory-bills/import` | Import hóa đơn KTX từ JSON |

---

## 🛡️ Best Practices

✅ Lưu API key ở biến môi trường, không commit vào Git
✅ Sử dụng `expires_days` để key tự động hết hạn
✅ Chỉ cấp scope cần thiết (principle of least privilege)
✅ Revoke key ngay khi phát hiện bị lộ
✅ Định kỳ rotate keys (tạo mới, xóa cũ)

---

## 📖 Full Documentation

Xem file [API_KEY_GUIDE.md](./API_KEY_GUIDE.md) để biết thêm chi tiết và ví dụ code Python/JavaScript.

---

## ❓ Troubleshooting

### Lỗi: "Invalid API key"
- Kiểm tra lại API key có đúng không
- Key phải có format: `fhs_xxxxxxxx...` (68 ký tự)

### Lỗi: "API key does not have required scope"
- API key không có quyền cho endpoint này
- Tạo key mới với scope phù hợp

### Lỗi: "API key has expired"
- Key đã hết hạn
- Tạo key mới với admin account

---

## 📞 Support

Liên hệ admin hoặc raise issue trên GitHub repository.
