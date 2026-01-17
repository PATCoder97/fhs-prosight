# 🎨 API Keys Management UI - User Guide

## 📍 Truy cập Giao diện

### Điều kiện:
- ✅ Phải đăng nhập với tài khoản **Admin**
- ✅ Truy cập: **Quản Trị** → **Quản Lý API Keys**

### URL:
```
http://your-domain/api-keys
```

---

## 🎯 Các Tính năng Chính

### 1️⃣ **Xem Danh sách API Keys**

Giao diện hiển thị bảng với các thông tin:
- **Tên**: Tên API key và mô tả
- **Prefix**: Prefix để nhận diện (ví dụ: `fhs_1234`)
- **Scopes**: Các quyền truy cập (badges màu xanh)
- **Trạng thái**:
  - 🟢 **Hoạt động** - Key đang active
  - 🟡 **Đã hết hạn** - Key đã expire
  - 🔴 **Đã vô hiệu hóa** - Key đã bị revoke
- **Ngày tạo**: Thời điểm tạo key
- **Hết hạn**: Ngày hết hạn (hoặc "Không giới hạn")
- **Lần dùng cuối**: Timestamp sử dụng gần nhất
- **Hành động**: Nút vô hiệu hóa

---

### 2️⃣ **Tạo API Key Mới**

#### Bước 1: Click nút "Tạo API Key"
- Nút màu xanh ở góc trên bên phải
- Icon dấu `+`

#### Bước 2: Điền thông tin trong form

**Các trường bắt buộc:**

1. **Tên API Key** * (Required)
   - Ví dụ: `HRS Import Service`
   - Tên gợi nhớ để biết key dùng cho gì

2. **Mô tả** (Optional)
   - Ví dụ: `API key cho import tự động từ HRS`
   - Ghi chú chi tiết về mục đích sử dụng

3. **Scopes (Quyền truy cập)** * (Required)
   - Chọn ít nhất 1 scope
   - **Available scopes:**
     - ✅ `evaluations:import` - Import Đánh Giá (Evaluations)
     - ✅ `dormitory-bills:import` - Import Hóa Đơn KTX (Dormitory Bills)
   - Có thể chọn nhiều scopes

4. **Số ngày hết hạn** (Optional)
   - Default: 365 ngày
   - Để trống = không giới hạn
   - Ví dụ: `365` (1 năm), `30` (1 tháng)

#### Bước 3: Click "Tạo API Key"

---

### 3️⃣ **Nhận API Key (CHỈ HIỂN THỊ 1 LẦN!)**

Sau khi tạo thành công, sẽ hiện popup với:

⚠️ **LƯU Ý QUAN TRỌNG:**
```
API key chỉ hiển thị MỘT LẦN DUY NHẤT này.
Vui lòng copy và lưu vào nơi an toàn!
```

**API Key format:**
```
fhs_1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
```

**Actions:**
- 📋 **Copy button**: Click để copy vào clipboard
- ✅ **"Đã lưu, đóng"**: Đóng popup sau khi đã lưu key

**⚠️ SAU KHI ĐÓNG POPUP:**
- Không thể xem lại API key
- Phải tạo key mới nếu mất

---

### 4️⃣ **Sử dụng API Key**

**Cách sử dụng được hiển thị trong popup:**

```bash
# Add header vào request
X-API-Key: fhs_1234567890abcdef...
```

**Example:**
```bash
curl -X POST "http://your-domain/api/dormitory-bills/import" \
  -H "X-API-Key: fhs_xxxxx..." \
  -H "Content-Type: application/json" \
  -d '{"bills": [...]}'
```

---

### 5️⃣ **Vô hiệu hóa API Key**

#### Khi nào cần vô hiệu hóa:
- 🔴 Key bị lộ/compromise
- 🔴 Không còn sử dụng
- 🔴 Cần thay thế bằng key mới

#### Cách vô hiệu hóa:

1. **Tìm key cần vô hiệu hóa** trong bảng
2. **Click icon thùng rác** 🗑️ ở cột "Hành động"
3. **Xác nhận** trong popup:
   - Hiển thị tên key
   - Giải thích: "Key sẽ không thể sử dụng được nữa nhưng vẫn giữ lại trong database để audit"
4. **Click "Vô hiệu hóa"**

**Kết quả:**
- Trạng thái key chuyển thành 🔴 **Đã vô hiệu hóa**
- Key không thể dùng để authenticate
- Vẫn hiển thị trong danh sách (để audit)
- Icon thùng rác biến mất (không thể vô hiệu hóa lần 2)

---

## 🎨 Giao diện Screenshots

### Màn hình chính - Danh sách API Keys
```
┌─────────────────────────────────────────────────────────┐
│  Quản Lý API Keys                   [+ Tạo API Key]    │
│  Tạo và quản lý API keys cho external integrations     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Tên    │ Prefix │ Scopes │ Trạng thái │ ...    │   │
│  ├─────────────────────────────────────────────────┤   │
│  │ HRS    │fhs_1234│[eval...│ ✅ Hoạt động│ 🗑️   │   │
│  │ Import │        │[dorm...│            │        │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Dialog - Tạo API Key
```
┌──────────────────────────────────┐
│  Tạo API Key Mới           [×]   │
├──────────────────────────────────┤
│                                  │
│  Tên API Key *                   │
│  [HRS Import Service        ]   │
│                                  │
│  Mô tả                           │
│  [API key cho import tự động]   │
│                                  │
│  Scopes (Quyền truy cập) *       │
│  [✓ evaluations:import      ]   │
│  [✓ dormitory-bills:import  ]   │
│                                  │
│  Số ngày hết hạn                 │
│  [365                        ]   │
│                                  │
│         [Hủy]  [Tạo API Key]     │
└──────────────────────────────────┘
```

### Dialog - Hiển thị API Key (chỉ 1 lần)
```
┌────────────────────────────────────────┐
│  🎉 API Key đã được tạo!               │
├────────────────────────────────────────┤
│                                        │
│  ⚠️ LƯU Ý QUAN TRỌNG:                 │
│  API key chỉ hiển thị MỘT LẦN DUY     │
│  NHẤT này. Vui lòng copy và lưu vào   │
│  nơi an toàn!                          │
│                                        │
│  ┌──────────────────────────────────┐ │
│  │ fhs_1234567890abcdef...      [📋]│ │
│  └──────────────────────────────────┘ │
│                                        │
│  ℹ️ Cách sử dụng:                     │
│  Thêm header                           │
│  X-API-Key: fhs_1234...                │
│                                        │
│                  [Đã lưu, đóng]        │
└────────────────────────────────────────┘
```

---

## 🎨 Color Coding

### Trạng thái Badges:
- 🟢 **Hoạt động** (Success/Green) - Key đang active và valid
- 🟡 **Đã hết hạn** (Warning/Yellow) - Key đã qua ngày expires_at
- 🔴 **Đã vô hiệu hóa** (Error/Red) - Key đã bị revoke

### Scope Badges:
- 🔵 **Info/Blue** - Tất cả các scopes hiển thị màu xanh info

---

## 💡 Tips & Best Practices

### ✅ DO:
- ✅ **Đặt tên có ý nghĩa** cho API key (ví dụ: tên hệ thống/service sử dụng)
- ✅ **Copy và lưu key ngay** khi tạo (chỉ hiện 1 lần!)
- ✅ **Chọn scope tối thiểu** cần thiết (principle of least privilege)
- ✅ **Đặt expiration date** để key tự động hết hạn
- ✅ **Vô hiệu hóa ngay** nếu nghi ngờ key bị lộ
- ✅ **Check "Lần dùng cuối"** để phát hiện key không dùng

### ❌ DON'T:
- ❌ **Đóng popup** trước khi copy key
- ❌ **Share key** qua email/Slack không mã hóa
- ❌ **Commit key** vào Git repository
- ❌ **Để key không hết hạn** trong production
- ❌ **Cấp tất cả scopes** cho mọi key

---

## 🔔 Notifications

Giao diện có toast notifications cho các actions:

### Success (Green):
- ✅ "API key đã được tạo thành công!"
- ✅ "Đã copy vào clipboard!"
- ✅ "API key đã được vô hiệu hóa!"

### Error (Red):
- ❌ "Không thể tải danh sách API keys!"
- ❌ "Tạo API key thất bại!"
- ❌ "Vô hiệu hóa API key thất bại!"
- ❌ "Không thể copy!"

### Warning (Orange):
- ⚠️ "Vui lòng nhập tên API key!"
- ⚠️ "Vui lòng chọn ít nhất 1 scope!"

---

## 🔍 Search & Filtering

**Current version:** Hiển thị tất cả keys trong table
**Pagination:** 10 items per page (default)
**Sorting:** Click vào column header để sort

**Các columns có thể sort:**
- Tên
- Trạng thái
- Ngày tạo
- Hết hạn

---

## 🐛 Troubleshooting

### Issue: "Không thể tải danh sách API keys!"
**Nguyên nhân:**
- Backend API không response
- Không có quyền admin
- Network error

**Giải pháp:**
- Check console logs
- Verify admin role
- Check backend server status

### Issue: "Tạo API key thất bại!"
**Nguyên nhân:**
- Thiếu thông tin bắt buộc
- Backend validation error
- Database error

**Giải pháp:**
- Kiểm tra lại form (tên, scopes)
- Check backend logs
- Verify database connection

### Issue: Toast notification không hiện
**Nguyên nhân:**
- UI component lỗi
- Z-index conflict

**Giải pháp:**
- Refresh page
- Check browser console

---

## 📱 Responsive Design

Giao diện hoạt động tốt trên:
- 🖥️ **Desktop** (1920x1080+)
- 💻 **Laptop** (1366x768+)
- 📱 **Tablet** (768x1024+)
- 📱 **Mobile** (375x667+) - Table có horizontal scroll

---

## 🔐 Security

### Admin Protection:
- Sử dụng `useAdminProtection()` composable
- Auto redirect nếu không phải admin
- Check role ở cả frontend và backend

### API Key Display:
- Chỉ hiển thị **1 lần** khi tạo
- Không lưu plain text trong frontend state
- Khuyến khích user copy ngay

### Revoke:
- Soft delete (set `is_active = false`)
- Giữ lại record để audit trail
- Không thể undo sau khi revoke

---

## 🚀 Quick Start Checklist

Để bắt đầu sử dụng:

- [ ] 1. Login với tài khoản admin
- [ ] 2. Vào menu **Quản Trị** → **Quản Lý API Keys**
- [ ] 3. Click **"Tạo API Key"**
- [ ] 4. Điền form:
  - [ ] Tên (required)
  - [ ] Mô tả (optional)
  - [ ] Scopes (required, ít nhất 1)
  - [ ] Expiration (optional)
- [ ] 5. Click **"Tạo API Key"**
- [ ] 6. **COPY API key ngay lập tức!** ⚠️
- [ ] 7. Lưu key vào password manager/vault
- [ ] 8. Share với team qua kênh an toàn
- [ ] 9. Test key với import endpoint
- [ ] 10. Monitor "Lần dùng cuối" để tracking usage

---

## 📚 Related Documentation

- Backend API Documentation: [API_KEY_GUIDE.md](../../backend/API_KEY_GUIDE.md)
- Quick Start: [API_KEY_QUICKSTART.md](../../backend/API_KEY_QUICKSTART.md)
- Migration Guide: [MIGRATION_GUIDE.md](../../backend/MIGRATION_GUIDE.md)
- Testing: [test_api_key_system.py](../../backend/test_api_key_system.py)

---

## 📞 Support

Nếu gặp vấn đề với giao diện:
1. Check browser console (F12)
2. Verify admin permissions
3. Check backend API status
4. Contact system administrator

---

**Last updated:** 2026-01-17 01:45:00 UTC
**Version:** 1.0.0
