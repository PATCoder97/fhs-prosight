# Role-Based Navigation Menu - Implementation Guide

## 🎯 Overview

Bạn đã có hệ thống navigation menu với phân quyền dựa trên role của user. Menu "Admin" chỉ hiển thị cho user có role = "admin".

## ✅ Đã Hoàn Thành

### 1. **Composable để Filter Navigation** ✅

**File:** [frontend/src/composables/useNavigation.js](frontend/src/composables/useNavigation.js)

Composable này filter navigation items dựa trên `requireRole` property:

```javascript
import { useNavigation } from '@/composables/useNavigation'

const { filterNavByRole } = useNavigation()
const filteredNavItems = computed(() => filterNavByRole(navItems))
```

**Cách hoạt động:**
- Đọc user từ localStorage
- Check `requireRole` của mỗi navigation item
- Loại bỏ items user không có quyền xem
- Hỗ trợ nested children (submenu)

### 2. **Updated Navigation Files** ✅

**Horizontal Navigation:** [frontend/src/navigation/horizontal/index.js](frontend/src/navigation/horizontal/index.js:12-23)

**Vertical Navigation:** [frontend/src/navigation/vertical/index.js](frontend/src/navigation/vertical/index.js:12-23)

Đã thêm menu Admin với structure:

```javascript
{
  title: 'Admin',
  icon: { icon: 'tabler-shield-lock' },
  requireRole: 'admin', // 👈 Chỉ admin mới thấy
  children: [
    {
      title: 'User Manager',
      to: { name: 'user-manager' },
      icon: { icon: 'tabler-users-group' },
    },
  ],
}
```

### 3. **Updated Layout Components** ✅

**Vertical Layout:** [frontend/src/layouts/components/DefaultLayoutWithVerticalNav.vue](frontend/src/layouts/components/DefaultLayoutWithVerticalNav.vue:16-22)

**Horizontal Layout:** [frontend/src/layouts/components/DefaultLayoutWithHorizontalNav.vue](frontend/src/layouts/components/DefaultLayoutWithHorizontalNav.vue:15-21)

Cả 2 layouts đã được update để sử dụng `filteredNavItems` thay vì `navItems` trực tiếp.

## 📊 Navigation Visibility Matrix

| User Role | Home | Second Page | Admin Menu | User Manager |
|-----------|------|-------------|------------|--------------|
| **No auth** | ❌ Login | ❌ Login | ❌ Hidden | ❌ Login |
| **Guest** | ❌ Welcome | ❌ Welcome | ❌ Hidden | ❌ Welcome |
| **User** | ✅ Show | ✅ Show | ❌ Hidden | ❌ Blocked |
| **Admin** | ✅ Show | ✅ Show | ✅ Show | ✅ Access |

## 🎨 Visual Changes

### Before (All Users)
```
┌─────────────────────────┐
│ 🏠 Home                 │
│ 📄 Second page          │
└─────────────────────────┘
```

### After (Admin Only)
```
┌─────────────────────────┐
│ 🏠 Home                 │
│ 📄 Second page          │
│ 🛡️ Admin               │ ← Chỉ admin thấy
│   └ 👥 User Manager     │
└─────────────────────────┘
```

### After (Regular User / Guest)
```
┌─────────────────────────┐
│ 🏠 Home                 │
│ 📄 Second page          │
└─────────────────────────┘
(Menu Admin bị ẩn hoàn toàn)
```

## 🚀 Cách Sử Dụng

### Thêm Menu Item Mới Với Role Requirement

**Example 1: Menu chỉ cho Admin**

```javascript
// navigation/horizontal/index.js
{
  title: 'System Settings',
  to: { name: 'system-settings' },
  icon: { icon: 'tabler-settings' },
  requireRole: 'admin', // 👈 Chỉ admin
}
```

**Example 2: Menu cho nhiều roles**

```javascript
{
  title: 'Reports',
  icon: { icon: 'tabler-report' },
  requireRole: ['user', 'admin'], // 👈 Array of roles
  children: [
    {
      title: 'Sales Report',
      to: { name: 'sales-report' },
    },
  ],
}
```

**Example 3: Menu không có yêu cầu role**

```javascript
{
  title: 'Public Page',
  to: { name: 'public' },
  icon: { icon: 'tabler-world' },
  // Không có requireRole = tất cả đều thấy
}
```

### Thêm Submenu Vào Admin Section

```javascript
// navigation/horizontal/index.js
{
  title: 'Admin',
  icon: { icon: 'tabler-shield-lock' },
  requireRole: 'admin',
  children: [
    {
      title: 'User Manager',
      to: { name: 'user-manager' },
      icon: { icon: 'tabler-users-group' },
    },
    // 👇 Thêm submenu mới ở đây
    {
      title: 'System Logs',
      to: { name: 'system-logs' },
      icon: { icon: 'tabler-file-text' },
    },
    {
      title: 'Settings',
      to: { name: 'admin-settings' },
      icon: { icon: 'tabler-settings' },
    },
  ],
}
```

## 🧪 Testing Guide

### Test 1: Admin User Login

1. Login với admin account
2. Kiểm tra navigation menu
3. **Expected:**
   - ✅ Thấy menu "Admin" với icon 🛡️
   - ✅ Click vào thấy submenu "User Manager"
   - ✅ Click "User Manager" navigate đến `/user-manager`

### Test 2: Regular User Login

1. Login với user account (role: 'user')
2. Kiểm tra navigation menu
3. **Expected:**
   - ❌ KHÔNG thấy menu "Admin"
   - ✅ Chỉ thấy "Home" và "Second page"

### Test 3: Guest User Login

1. Login với guest account
2. Kiểm tra navigation menu
3. **Expected:**
   - ❌ KHÔNG thấy menu "Admin"
   - ✅ Chỉ thấy "Home" và "Second page"
   - ⚠️ Bị redirect về `/welcome` khi click vào bất kỳ menu nào

### Test 4: Role Change Real-time

1. Login as regular user (không thấy Admin menu)
2. Admin promote user lên admin role via User Manager
3. User logout và login lại
4. **Expected:**
   - ✅ Bây giờ thấy menu "Admin"

## 🔧 Advanced Configuration

### Custom Role Logic

Nếu bạn cần logic phức tạp hơn (ví dụ: manager role):

```javascript
// composables/useNavigation.js - hasRequiredRole function
const hasRequiredRole = (requiredRole, userRole) => {
  if (!requiredRole) return true

  // Custom logic: manager cũng thấy được user menu
  if (requiredRole === 'user' && userRole === 'manager') {
    return true
  }

  if (Array.isArray(requiredRole)) {
    return requiredRole.includes(userRole)
  }

  return requiredRole === userRole
}
```

### Hide Specific Items for Certain Roles

```javascript
// navigation/horizontal/index.js
{
  title: 'Training',
  to: { name: 'training' },
  icon: { icon: 'tabler-school' },
  requireRole: ['user', 'manager'], // Admin KHÔNG thấy
}
```

### Conditional Children Based on Role

```javascript
{
  title: 'Reports',
  icon: { icon: 'tabler-report' },
  children: [
    {
      title: 'My Reports',
      to: { name: 'my-reports' },
      // All users can see
    },
    {
      title: 'All Reports',
      to: { name: 'all-reports' },
      requireRole: 'admin', // Only admin sees this child
    },
  ],
}
```

## 🎯 Key Features

### 1. **Reactive Navigation**
- Navigation tự động update khi user role thay đổi
- Sử dụng `computed()` để auto re-render

### 2. **Nested Children Support**
- Filter đệ quy cho submenu
- Parent menu tự động ẩn nếu không có children visible

### 3. **Multiple Role Support**
- `requireRole: 'admin'` - Single role
- `requireRole: ['user', 'admin']` - Multiple roles

### 4. **No Role = Public**
- Items không có `requireRole` property sẽ hiện cho tất cả

## 📋 Complete Example

```javascript
// navigation/horizontal/index.js - Full example
export default [
  // Public - tất cả đều thấy
  {
    title: 'Home',
    to: { name: 'root' },
    icon: { icon: 'tabler-smart-home' },
  },

  // Authenticated users (user + admin)
  {
    title: 'Dashboard',
    to: { name: 'dashboard' },
    icon: { icon: 'tabler-dashboard' },
    requireRole: ['user', 'admin'],
  },

  // Admin only
  {
    title: 'Admin',
    icon: { icon: 'tabler-shield-lock' },
    requireRole: 'admin',
    children: [
      {
        title: 'User Manager',
        to: { name: 'user-manager' },
        icon: { icon: 'tabler-users-group' },
      },
      {
        title: 'System Logs',
        to: { name: 'system-logs' },
        icon: { icon: 'tabler-file-text' },
      },
    ],
  },
]
```

## 🔍 Debugging

### Check Current User Role

```javascript
// Browser console
const user = JSON.parse(localStorage.getItem('user'))
console.log('Current user role:', user?.role)
```

### Check Filtered Navigation

```javascript
// In component
import { useNavigation } from '@/composables/useNavigation'
import navItems from '@/navigation/horizontal'

const { filterNavByRole } = useNavigation()
const filtered = filterNavByRole(navItems)
console.log('Filtered nav items:', filtered)
```

## ⚡ Performance

- **Computed caching**: Navigation chỉ re-calculate khi cần
- **Lightweight filter**: O(n) complexity
- **No API calls**: Chỉ đọc localStorage

## 🔐 Security Notes

⚠️ **IMPORTANT:** Navigation hiding chỉ là UX, KHÔNG phải security!

- ✅ **Good:** Ẩn menu để improve UX
- ❌ **Bad:** Dựa vào navigation hiding để protect routes

**Phải có cả 3 layers:**
1. Navigation filtering (UX) ← Đã có
2. Middleware protection (Frontend) ← Đã có
3. Backend API protection (Security) ← Đã có

## 📚 Related Files

| File | Purpose |
|------|---------|
| [useNavigation.js](frontend/src/composables/useNavigation.js) | Navigation filtering logic |
| [horizontal/index.js](frontend/src/navigation/horizontal/index.js) | Horizontal nav config |
| [vertical/index.js](frontend/src/navigation/vertical/index.js) | Vertical nav config |
| [DefaultLayoutWithVerticalNav.vue](frontend/src/layouts/components/DefaultLayoutWithVerticalNav.vue) | Vertical layout |
| [DefaultLayoutWithHorizontalNav.vue](frontend/src/layouts/components/DefaultLayoutWithHorizontalNav.vue) | Horizontal layout |
| [auth.global.js](frontend/src/middleware/auth.global.js) | Route protection |

---

**Status:** ✅ Production Ready
**Last Updated:** 2026-01-13
