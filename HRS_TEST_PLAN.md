# HRS System - Test Plan

## 📋 Test Overview

**Test Date**: 2026-01-13
**System Version**: Latest (after bug fixes)
**Tester**: Claude & User

---

## ✅ Bug Fixes Verified

### 1. Backend AsyncIO Import Fix
- **Status**: ✅ Fixed
- **File**: `backend/app/integrations/fhs_hrs_client.py`
- **Fix**: Added `import asyncio` at line 1
- **Commit**: `c9cef60`

### 2. Year Bonus API Format Handling
- **Status**: ✅ Fixed
- **File**: `frontend/src/pages/year-bonus.vue`
- **Changes**:
  - Added `parseNumber()` function (lines 59-66)
  - Added `totalBonus` computed property (lines 78-83)
  - Updated labels and displays
- **Commit**: `05417f6`

### 3. Dashboard LocalId Field
- **Status**: ✅ Fixed
- **File**: `frontend/src/pages/hrs-dashboard.vue`
- **Changes**: Changed all `employee_id` → `localId` references
- **Commit**: `2a2b337`

---

## 🧪 Test Cases

### Prerequisites
- ✅ Backend running on `http://localhost:8001`
- ✅ Frontend running on `http://localhost:3000`
- ✅ Test user logged in: `user@example.com` / `user123`
- ✅ Test Employee ID: `VNW0014732`

---

### Test 1: HRS Dashboard
**Objective**: Verify dashboard auto-loads data using `localId` from localStorage

**Steps**:
1. Login as `user@example.com`
2. Navigate to `/hrs-dashboard`
3. Wait for auto-load

**Expected Results**:
- ✅ Dashboard loads without errors
- ✅ Current month salary displayed (if data exists)
- ✅ Latest achievement displayed (if data exists)
- ✅ Current year bonus displayed (if data exists)
- ✅ All 3 stat cards render correctly
- ✅ 2 detail cards (Salary Details, Achievements Overview) render
- ✅ 4 Quick Action buttons work
- ✅ Cards are clickable with hover effects

**API Calls Made** (check browser DevTools Network tab):
- `GET /api/hrs-data/salary/{localId}?year=2026&month=1`
- `GET /api/hrs-data/achievements/{localId}`
- `GET /api/hrs-data/year-bonus/{localId}/2026`

**Pass Criteria**: No console errors, data displays correctly or shows graceful "Chưa có dữ liệu"

---

### Test 2: Salary Page
**Objective**: Test salary lookup with Employee ID search

**Steps**:
1. Navigate to `/salary`
2. Enter Employee ID: `VNW0014732`
3. Select Year: `2025`, Month: `1`
4. Click "Tra Cứu"

**Expected Results**:
- ✅ Employee info displays (name, ID, avatar)
- ✅ 3 Summary cards show:
  - Thu Nhập (green)
  - Khấu Trừ (red)
  - Thực Lĩnh (primary)
- ✅ Income breakdown table displays (30+ fields)
- ✅ Deductions breakdown table displays
- ✅ All currency amounts formatted as VND
- ✅ No console errors

**API Call**:
- `GET /api/hrs-data/salary/VNW0014732?year=2025&month=1`

**Pass Criteria**: All salary data displays correctly with proper formatting

---

### Test 3: Salary History Page
**Objective**: Test multi-month salary lookup with trend analysis

**Steps**:
1. Navigate to `/salary-history`
2. Enter Employee ID: `VNW0014732`
3. Select Year: `2024`, From Month: `1`, To Month: `12`
4. Click "Tra Cứu"

**Expected Results**:
- ✅ Employee info displays
- ✅ 3 Trend Analysis cards show averages
- ✅ Highest/Lowest month comparison displays
- ✅ Monthly history table shows all months
- ✅ Trend indicators (↑↓) with % change
- ✅ Color-coded chips (green up, red down, yellow neutral)
- ✅ Average row in table footer
- ✅ All amounts formatted as VND

**API Call**:
- `GET /api/hrs-data/salary/history/VNW0014732?year=2024&from_month=1&to_month=12`

**Pass Criteria**: Trend analysis is accurate, all months display correctly

---

### Test 4: Achievements Page
**Objective**: Test achievement history lookup

**Steps**:
1. Navigate to `/achievements`
2. Enter Employee ID: `VNW0014732`
3. Click "Tra Cứu"

**Expected Results**:
- ✅ Employee info displays
- ✅ Achievement cards grid displays
- ✅ Each card shows year and score
- ✅ Color-coded by score:
  - 優 (Yuu) = Success/Green
  - 良 (Ryou) = Info/Blue
  - 甲 (Kou) = Primary
  - 乙 (Otsu) = Warning/Orange
  - 丙 (Hei) = Error/Red
- ✅ Achievement table displays with icons
- ✅ Score legend shows Vietnamese translations
- ✅ Cards have hover effects

**API Call**:
- `GET /api/hrs-data/achievements/VNW0014732`

**Pass Criteria**: All achievements display with correct colors and translations

---

### Test 5: Year Bonus Page (Critical - Recent Bug Fix)
**Objective**: Test year bonus lookup with fixed API format handling

**Test Case 5.1**: Year with full data (2022)

**Steps**:
1. Navigate to `/year-bonus`
2. Enter Employee ID: `VNW0014732`
3. Select Year: `2022`
4. Click "Tra Cứu"

**Expected Results**:
- ✅ Employee info displays
- ✅ 4 Summary cards display:
  - Tổng Lương Cơ Bản: `7.205.600 ₫` (parsed from "7,205,600")
  - Tỷ Lệ Thưởng: `195.00%` (not `195.00%%`)
  - Tỷ Lệ BHTN: `100.00%` (not "Số Tháng")
  - Tổng Thưởng: `14.050.920 ₫` (calculated from tpnttt + tpntst)
- ✅ Bonus breakdown shows:
  - Thưởng Trước Tết: `14.050.920 ₫` (parsed from "14,050,920")
  - Thưởng Sau Tết: `0 ₫` (null handled correctly)
- ✅ Detail table displays all information
- ✅ Large summary at bottom shows total
- ✅ No console errors
- ✅ `parseNumber()` function works correctly
- ✅ `totalBonus` computed property calculates correctly

**API Response Verification**:
```json
{
  "employee_id": "VNW0014732",
  "employee_name": "Phan Anh Tuấn",
  "year": 2022,
  "bonus_data": {
    "tlcb": "7,205,600",      // Should parse to 7205600
    "stdltbtn": "100.00%",    // Display as-is
    "capbac": "優",           // Display as-is
    "tile": "195.00%",        // Display without extra %
    "stienthuong": "0",       // Ignore this
    "tpnttt": "14,050,920",   // Parse to 14050920
    "tpntst": null            // Handle as 0
  }
}
```

**Pass Criteria**:
- Numbers with commas parse correctly
- Percentages display without double %
- Total calculated as tpnttt + tpntst, NOT stienthuong
- Null values handled gracefully

**Test Case 5.2**: Year with no data

**Steps**:
1. Select Year: `2020` (unlikely to have data)
2. Click "Tra Cứu"

**Expected Results**:
- ✅ Shows error message: "Không có dữ liệu thưởng cho năm này"
- ✅ No crash or console errors

---

## 🔍 Integration Tests

### Test 6: Navigation Flow
**Steps**:
1. Start at HRS Dashboard
2. Click "Chi Tiết Lương" card → Should go to `/salary`
3. Go back, click "Thành Tích" card → Should go to `/achievements`
4. Go back, click "Thưởng Tết" card → Should go to `/year-bonus`
5. Test Quick Actions buttons (4 buttons)

**Pass Criteria**: All navigation works without errors

---

### Test 7: Role-Based Access Control
**Test 7.1**: User Role Access
**Steps**:
1. Login as `user@example.com` (role: user)
2. Check sidebar navigation
3. Try accessing all 5 HRS pages

**Expected**: All 5 pages accessible

**Test 7.2**: Guest Access Block
**Steps**:
1. Logout
2. Try accessing `/hrs-dashboard` directly

**Expected**: Redirected to login page

---

## 🐛 Error Handling Tests

### Test 8: Invalid Employee ID
**Steps**:
1. Go to `/salary`
2. Enter invalid Employee ID: `INVALID123`
3. Click "Tra Cứu"

**Expected**: Error message displays, no crash

---

### Test 9: Network Error Simulation
**Steps**:
1. Stop backend server
2. Try loading HRS Dashboard
3. Try searching for salary

**Expected**:
- Graceful error messages
- No uncaught exceptions
- User-friendly Vietnamese error text

---

### Test 10: Empty Data Handling
**Steps**:
1. Search for employee with no data
2. Verify empty states display

**Expected**:
- "Chưa có dữ liệu" messages
- Icons and friendly text
- No blank/broken UI

---

## 📱 Responsive Design Tests

### Test 11: Mobile View
**Steps**:
1. Open DevTools, set to iPhone 12 size
2. Navigate through all 5 pages
3. Test forms and tables

**Expected**:
- All pages responsive
- Forms stack vertically
- Tables scroll horizontally
- Buttons full-width on mobile

---

## ⚡ Performance Tests

### Test 12: Load Time
**Metrics to Check**:
- Dashboard initial load: < 2s
- API response times: < 500ms
- Page transitions: Instant

### Test 13: Bundle Sizes (from latest build)
```
hrs-dashboard.js:   10.60 kB → 3.25 kB gzipped ✅
salary-history.js:  11.64 kB → 3.56 kB gzipped ✅
year-bonus.js:      11.08 kB → 3.23 kB gzipped ✅
achievements.js:     8.51 kB → 2.80 kB gzipped ✅
salary.js:          12.72 kB → 3.72 kB gzipped ✅
```

**Total**: ~55 kB → ~16.5 kB gzipped ✅

---

## 🎯 Regression Tests

### Test 14: Previous Functionality
Verify previous features still work:
- ✅ User login/logout
- ✅ Admin user manager
- ✅ Navigation menus
- ✅ Role filtering in menus

---

## 📊 Test Results Summary

### Critical Tests (Must Pass)
- [ ] Test 1: HRS Dashboard loads with localId
- [ ] Test 5.1: Year Bonus 2022 displays correctly
- [ ] Test 5: parseNumber() handles commas
- [ ] Test 5: totalBonus calculation correct
- [ ] Test 7: Role-based access works

### Important Tests
- [ ] Test 2: Salary page works
- [ ] Test 3: Salary history with trends
- [ ] Test 4: Achievements display
- [ ] Test 6: Navigation flow
- [ ] Test 8-10: Error handling

### Nice to Have
- [ ] Test 11: Mobile responsive
- [ ] Test 12-13: Performance metrics
- [ ] Test 14: No regressions

---

## 🚀 Ready to Test

**Backend Start Command**:
```bash
cd backend
uvicorn app.main:app --reload --port 8001
```

**Frontend**: Already built and running

**Test Employee IDs**:
- Primary: `VNW0014732` (has data for 2022)
- User's localId: (stored in localStorage after login)

---

## 📝 Test Notes

**Known Good Test Data**:
- Employee: `VNW0014732` - Phan Anh Tuấn
- Year 2022 Bonus Data:
  - Base Salary: 7,205,600 ₫
  - Bonus Rate: 195.00%
  - BHTN Rate: 100.00%
  - Pre-Tet: 14,050,920 ₫
  - Post-Tet: null (0 ₫)
  - Total: 14,050,920 ₫

**What Changed in Bug Fixes**:
1. Backend can now call year-bonus endpoint (asyncio import)
2. Year bonus page handles comma-separated numbers
3. Year bonus page calculates total correctly
4. Dashboard uses correct user field (localId)

---

**Status**: 🟡 Ready for Manual Testing

All code fixes are complete and committed. System is ready for comprehensive testing to verify all functionality works as expected.
