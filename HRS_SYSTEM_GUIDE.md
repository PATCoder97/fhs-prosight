# FHS ProSight - HRS System Documentation

## 📋 Tổng Quan

Hệ thống HRS (Human Resources System) được tích hợp vào FHS ProSight để quản lý và tra cứu dữ liệu nhân sự. Hệ thống bao gồm 5 trang chính với đầy đủ tính năng tra cứu lương, thành tích, và thưởng.

## 🎯 Các Trang Đã Hoàn Thành

### 1. **HRS Dashboard** (`/hrs-dashboard`)
**Mục đích**: Trang tổng quan hiển thị overview của tất cả dữ liệu nhân sự

**Features**:
- ✅ 3 Quick Stat Cards:
  - Lương tháng hiện tại
  - Thành tích gần nhất
  - Thưởng Tết năm hiện tại
- ✅ Chi tiết lương (Thu nhập, Khấu trừ, Thực lĩnh)
- ✅ Lịch sử thành tích (4 năm gần nhất)
- ✅ Quick Actions với 4 nút navigate nhanh
- ✅ Auto-load data khi vào trang
- ✅ Clickable cards với hover effects
- ✅ Xử lý graceful khi không có data

**API Calls**:
- `GET /api/hrs-data/salary/{employee_id}?year={year}&month={month}`
- `GET /api/hrs-data/achievements/{employee_id}`
- `GET /api/hrs-data/year-bonus/{employee_id}/{year}`

**Screenshot**: Dashboard với 3 stat cards + 2 detail cards + quick actions

---

### 2. **Salary Page** (`/salary`)
**Mục đích**: Tra cứu lương chi tiết theo tháng

**Features**:
- ✅ Search form: Employee ID, Year, Month
- ✅ Hiển thị thông tin nhân viên (avatar, name, ID)
- ✅ Summary cards (Thu nhập, Khấu trừ, Thực lĩnh)
- ✅ Chi tiết thu nhập (30+ fields):
  - Lương cơ bản, thưởng, phụ cấp
  - Overtime, night shift, holiday pay
  - Housing, meal, transport allowances
- ✅ Chi tiết khấu trừ:
  - BHXH, BHYT, BHTN
  - Thuế TNCN
  - Phí ký túc xá, công đoàn
- ✅ Vietnamese currency formatting
- ✅ Color-coded sections (green=income, red=deductions)

**API Call**:
```
GET /api/hrs-data/salary/{employee_id}?year={year}&month={month}
```

**Response Structure**:
```json
{
  "employee_id": "VNW0014732",
  "employee_name": "NGUYEN VAN A",
  "period": { "year": 2025, "month": 1 },
  "summary": {
    "tong_tien_cong": 15000000.0,
    "tong_tien_tru": 3000000.0,
    "thuc_linh": 12000000.0
  },
  "income": { /* 30+ fields */ },
  "deductions": { /* 10+ fields */ }
}
```

---

### 3. **Salary History Page** (`/salary-history`)
**Mục đích**: Xem lịch sử lương nhiều tháng với phân tích xu hướng

**Features**:
- ✅ Search form: Employee ID, Year, From Month, To Month
- ✅ Trend Analysis Cards:
  - Thu nhập trung bình/tháng
  - Khấu trừ trung bình/tháng
  - Thực lĩnh trung bình/tháng
- ✅ Highest/Lowest Month Comparison
- ✅ Monthly History Table với:
  - Thu nhập, Khấu trừ, Thực lĩnh từng tháng
  - Trend indicators (↑↓) với % thay đổi so với tháng trước
  - Color-coded trend chips (green up, red down, yellow neutral)
- ✅ Average row ở table footer
- ✅ Responsive design

**API Call**:
```
GET /api/hrs-data/salary/history/{employee_id}?year={year}&from_month={from}&to_month={to}
```

**Response Structure**:
```json
{
  "employee_id": "VNW0014732",
  "employee_name": "NGUYEN VAN A",
  "period": { "year": 2024, "month": "1-12" },
  "months": [
    {
      "month": 1,
      "summary": { "tong_tien_cong": 15000000, "tong_tien_tru": 3000000, "thuc_linh": 12000000 },
      "income": { /* ... */ },
      "deductions": { /* ... */ }
    }
  ],
  "trend": {
    "average_income": 15500000.0,
    "average_deductions": 3100000.0,
    "average_net": 12400000.0,
    "highest_month": { /* ... */ },
    "lowest_month": { /* ... */ }
  }
}
```

---

### 4. **Achievements Page** (`/achievements`)
**Mục đích**: Tra cứu lịch sử đánh giá/thành tích nhân viên

**Features**:
- ✅ Search form: Employee ID
- ✅ Employee info display
- ✅ Achievement Cards Grid:
  - Card cho mỗi năm với icon, năm, score
  - Color-coded theo điểm (優=success, 良=info, 甲=primary, 乙=warning, 丙=error)
  - Hover effects (transform + shadow)
- ✅ Achievement Table với:
  - Năm, Score chip, Vietnamese label
  - Icons khác nhau cho mỗi score level
- ✅ Score Legend giải thích thang điểm:
  - 優 (Yuu) = Xuất Sắc
  - 良 (Ryou) = Tốt
  - 甲 (Kou) = Khá
  - 乙 (Otsu) = Trung Bình
  - 丙 (Hei) = Yếu

**API Call**:
```
GET /api/hrs-data/achievements/{employee_id}
```

**Response Structure**:
```json
{
  "employee_id": "VNW0014732",
  "employee_name": "NGUYEN VAN A",
  "achievements": [
    { "year": "2024", "score": "優" },
    { "year": "2023", "score": "良" },
    { "year": "2022", "score": "甲" }
  ]
}
```

---

### 5. **Year Bonus Page** (`/year-bonus`)
**Mục đích**: Tra cứu thưởng Tết (pre-Tet + post-Tet)

**Features**:
- ✅ Search form: Employee ID, Year
- ✅ Employee info với rank badge
- ✅ 4 Summary Cards:
  - Tổng lương cơ bản
  - Tỷ lệ thưởng (%)
  - Số tháng đóng BHTN
  - Tổng thưởng
- ✅ Bonus Breakdown Cards:
  - Thưởng trước Tết (Phần 1) - Green
  - Thưởng sau Tết (Phần 2) - Blue
- ✅ Detailed Information Table
- ✅ Large Total Bonus Summary Display

**API Call**:
```
GET /api/hrs-data/year-bonus/{employee_id}/{year}
```

**Response Structure**:
```json
{
  "employee_id": "VNW0014732",
  "employee_name": "NGUYEN VAN A",
  "year": 2024,
  "bonus_data": {
    "mnv": "VNW0014732",
    "tlcb": "15000000",        // Tổng lương cơ bản
    "stdltbtn": "12",          // Số tháng đóng BHTN
    "capbac": "Senior",        // Cấp bậc
    "tile": "100",             // Tỷ lệ (%)
    "stienthuong": "5000000",  // Tổng thưởng
    "tpnttt": "2500000",       // Thưởng phần NT trước Tết
    "tpntst": "2500000"        // Thưởng phần NT sau Tết
  }
}
```

---

## 🔐 Security & Access Control

### Role-Based Access
Tất cả 5 trang HRS được bảo vệ bởi:
- ✅ `useGuestProtection()` - Chặn guest users
- ✅ `requireRole: ['user', 'admin']` - Chỉ user và admin có quyền truy cập
- ✅ Auto-redirect to login nếu không có quyền

### Navigation Menu
Tất cả trang đều được thêm vào:
- ✅ Vertical Navigation (sidebar)
- ✅ Horizontal Navigation (top menu)
- ✅ Menu items chỉ hiện với user/admin roles

---

## 🎨 UI/UX Features

### Common Features (Tất cả trang)
- ✅ Vietnamese localization
- ✅ Currency formatting (VND)
- ✅ Responsive design (mobile-first)
- ✅ Loading states với VProgressCircular
- ✅ Error handling với VAlert
- ✅ Empty state với friendly messages
- ✅ Consistent color scheme (Vuetify 3)
- ✅ Icon usage (Tabler Icons)

### Dashboard-Specific
- ✅ Clickable cards với hover effects
- ✅ Quick navigation buttons
- ✅ Auto-load data on mount
- ✅ Graceful degradation (missing data)

### Achievements-Specific
- ✅ Color-coded score chips
- ✅ Card hover effects (transform + shadow)
- ✅ Score legend with Vietnamese translations

### Salary History-Specific
- ✅ Trend indicators với % và icons
- ✅ Highest/Lowest month comparison
- ✅ Average row in footer

---

## 🛠️ Technical Stack

### Frontend
- **Framework**: Vue 3 (Composition API)
- **UI Library**: Vuetify 3
- **Icons**: Tabler Icons
- **Routing**: Vue Router
- **API Client**: Custom `$api` wrapper

### Backend
- **Framework**: FastAPI
- **Database**: PostgreSQL (AsyncSession)
- **ORM**: SQLAlchemy
- **HRS Integration**: Custom FHSHRSClient
- **Authentication**: JWT + HttpOnly Cookies

---

## 📝 Backend Bug Fixes

### Fixed Issues
1. ✅ **Missing asyncio import** (`fhs_hrs_client.py`)
   - Lỗi: `name 'asyncio' is not defined`
   - Fix: Thêm `import asyncio` vào đầu file
   - Commit: `c9cef60`

---

## 🚀 Git Commits History

```bash
a55ecee feat: add HRS Dashboard with overview of all employee data
c9cef60 fix: add missing asyncio import in fhs_hrs_client
4bb90a4 feat: add salary-history page with trend analysis
383ed07 feat: add year-bonus page for Tet bonus lookup
0860a5c feat: add achievements page with employee evaluation history
6723e85 fix: align search button with input fields using flex align-end
1574b43 fix: align search button height with input fields (56px)
ccbce9f chore: remove hint text from Employee ID field for cleaner UI
3261ccd feat: update salary page to support employee ID search
27a2609 feat: add salary viewing page with HRS API integration
```

---

## 📊 Build Status

### Latest Build
✅ **Build Successful** (54.94s)

### Generated Assets
```
- hrs-dashboard-C81qcDI7.js    (10.62 kB → 3.26 kB gzipped)
- salary-history-ChO13pKt.js   (11.64 kB → 3.56 kB gzipped)
- year-bonus-BebibtB6.js        (10.99 kB → 3.18 kB gzipped)
- achievements-FLo3cfbk.js      (8.51 kB → 2.80 kB gzipped)
- salary-CG1gxs4l.js            (12.72 kB → 3.72 kB gzipped)
```

Total: ~55 kB → ~16.5 kB gzipped

---

## 🧪 Testing Guide

### 1. Login
- User: `user@example.com` / Password: `user123`
- Role: `user` (có quyền truy cập HRS)

### 2. Test HRS Dashboard
1. Navigate to `/hrs-dashboard`
2. Verify auto-load data hiển thị:
   - Current month salary
   - Latest achievement
   - Current year bonus
3. Click vào cards → Navigate đến detail pages

### 3. Test Salary Page
1. Navigate to `/salary`
2. Nhập Employee ID: `VNW0014732`
3. Chọn Year: `2025`, Month: `1`
4. Click "Tra Cứu"
5. Verify hiển thị:
   - Summary cards (thu nhập, khấu trừ, thực lĩnh)
   - Income breakdown table
   - Deductions breakdown table

### 4. Test Salary History
1. Navigate to `/salary-history`
2. Nhập Employee ID: `VNW0014732`
3. Chọn Year: `2024`, From: `1`, To: `12`
4. Click "Tra Cứu"
5. Verify:
   - Trend analysis cards
   - Highest/lowest month comparison
   - Monthly history table với trend %

### 5. Test Achievements
1. Navigate to `/achievements`
2. Nhập Employee ID: `VNW0014732`
3. Click "Tra Cứu"
4. Verify:
   - Achievement cards grid
   - Achievement table
   - Score legend

### 6. Test Year Bonus
1. Navigate to `/year-bonus`
2. Nhập Employee ID: `VNW0014732`
3. Chọn Year: `2024`
4. Click "Tra Cứu"
5. Verify:
   - Summary cards (base salary, rate, months, total)
   - Bonus breakdown (pre-Tet + post-Tet)
   - Detail table

---

## 📁 File Structure

```
frontend/src/
├── pages/
│   ├── hrs-dashboard.vue      # HRS Dashboard (overview)
│   ├── salary.vue             # Salary lookup
│   ├── salary-history.vue     # Salary history with trends
│   ├── achievements.vue       # Achievement history
│   └── year-bonus.vue         # Year bonus (Tet bonus)
├── navigation/
│   ├── vertical/index.js      # Sidebar navigation
│   └── horizontal/index.js    # Top menu navigation
└── composables/
    └── useGuestProtection.js  # Guest protection hook

backend/app/
├── routers/
│   └── hrs_data.py            # HRS API endpoints
├── services/
│   └── hrs_data_service.py    # HRS business logic
├── integrations/
│   └── fhs_hrs_client.py      # HRS API client (FIXED)
└── schemas/
    └── hrs_data.py            # Response schemas
```

---

## 🎯 Next Steps (Optional)

### Feature Enhancements
1. **Charts & Graphs**
   - Add salary trend line chart (Chart.js/ApexCharts)
   - Add achievement score pie chart
   - Add bonus comparison bar chart

2. **Export Functions**
   - Export salary to PDF
   - Export salary history to Excel
   - Print-friendly views

3. **Advanced Features**
   - Salary comparison (year-over-year)
   - Bonus calculator
   - Achievement statistics

4. **Performance**
   - Add caching for frequently accessed data
   - Implement pagination for large datasets
   - Lazy loading for images/charts

### Deployment
1. Push code to GitHub
2. Deploy backend to production server
3. Deploy frontend to Vercel/Netlify
4. Setup CI/CD pipeline
5. Configure production environment variables

---

## 📞 Support

Nếu gặp vấn đề với HRS system, vui lòng:
1. Kiểm tra backend logs (`uvicorn` console)
2. Kiểm tra frontend console (browser DevTools)
3. Verify API endpoints hoạt động (Postman/curl)
4. Restart backend nếu có code changes

**Backend restart command**:
```bash
cd backend
uvicorn app.main:app --reload --port 8001
```

---

## ✅ Completion Status

- ✅ HRS Dashboard (Overview)
- ✅ Salary Page (Monthly lookup)
- ✅ Salary History Page (Multi-month + trends)
- ✅ Achievements Page (Evaluation history)
- ✅ Year Bonus Page (Tet bonus)
- ✅ Navigation Integration
- ✅ Role-based Access Control
- ✅ Backend Bug Fixes (asyncio import)
- ✅ Build Verification
- ✅ Documentation

**Status**: 🎉 **100% Complete**

---

Generated: 2026-01-13
Author: Claude (with Co-Authored-By: Claude <noreply@anthropic.com>)
