# Complete System Testing Guide

## 🎯 Overview

This guide will help you test the complete authentication, admin protection, and role-based navigation system.

## 🚀 Quick Start

### Start the Servers

```bash
# Terminal 1: Backend
cd backend
python -m uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

**URLs:**
- Frontend: http://localhost:5173/ (or check terminal for actual port)
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 🧪 Test Scenarios

### Scenario 1: Guest User Flow

**Purpose:** Test guest user restrictions and welcome page

**Steps:**
1. Login with OAuth (Google/GitHub)
2. If this is your first login, you'll be assigned role: `guest`
3. Expected behavior:
   - ✅ Redirected to `/welcome` page
   - ✅ Can ONLY access `/welcome`
   - ✅ Trying to access `/` → redirected back to `/welcome`
   - ✅ Trying to access `/second-page` → redirected back to `/welcome`
   - ✅ Navigation menu shows only "Home" and "Second page" (no Admin menu)
   - ⚠️ Clicking any menu item redirects to `/welcome`

**Manual role upgrade (for testing):**
```bash
# Use backend API or database to change role from 'guest' to 'user'
curl -X PUT http://localhost:8000/users/{user_id}/role \
  -H "Cookie: access_token=<admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"role": "user"}'
```

---

### Scenario 2: Regular User Flow

**Purpose:** Test standard user access and restrictions

**Setup:**
- Ensure user has role: `user` in database

**Steps:**
1. Login with OAuth
2. Expected behavior:
   - ✅ Redirected to `/` (home page)
   - ✅ Can access `/` and `/second-page`
   - ✅ Navigation shows "Home" and "Second page"
   - ❌ NO "Admin" menu visible
   - ❌ Trying to access `/user-manager` directly:
     - Shows alert: "⚠️ Bạn không có quyền truy cập trang này"
     - Redirected to `/`

**Test Navigation:**
```
Visible Menu Items:
├─ 🏠 Home (clickable, works)
└─ 📄 Second page (clickable, works)

Hidden Menu Items:
└─ 🛡️ Admin (COMPLETELY HIDDEN)
```

---

### Scenario 3: Admin User Flow

**Purpose:** Test full admin access and user management

**Setup:**
- Ensure user has role: `admin` in database

**Steps:**
1. Login with OAuth
2. Expected behavior:
   - ✅ Redirected to `/` (home page)
   - ✅ Can access all pages: `/`, `/second-page`, `/user-manager`
   - ✅ Navigation shows "Home", "Second page", AND "Admin"
   - ✅ Admin menu expands to show "User Manager"

**Test Navigation:**
```
Visible Menu Items:
├─ 🏠 Home (clickable, works)
├─ 📄 Second page (clickable, works)
└─ 🛡️ Admin (clickable, expands)
    └─ 👥 User Manager (clickable, works)
```

**Test User Manager Page:**
1. Click Admin → User Manager
2. Expected features:
   - ✅ Table shows all registered users
   - ✅ Each user shows: email, full name, role, provider, localId
   - ✅ Click menu (⋮) next to any user
   - ✅ Can change role: Admin / User / Guest
   - ✅ Changes save to database
   - ✅ Success message appears

---

### Scenario 4: Role-Based Navigation Visibility

**Purpose:** Verify navigation filtering works correctly

**Test Matrix:**

| User Role | Home | Second Page | Admin Menu | User Manager Link |
|-----------|------|-------------|------------|-------------------|
| **guest** | Visible but redirects | Visible but redirects | Hidden | Hidden |
| **user** | ✅ Visible & Works | ✅ Visible & Works | ❌ Hidden | Hidden |
| **admin** | ✅ Visible & Works | ✅ Visible & Works | ✅ Visible | ✅ Visible |

**How to Test:**
1. Login as each role type
2. Inspect navigation menu
3. Try clicking each menu item
4. Verify expected behavior

---

### Scenario 5: Direct URL Access Protection

**Purpose:** Test that middleware protects routes even with direct URL access

**Test Cases:**

**Case 1: Guest tries `/user-manager`**
```
1. Login as guest
2. Type in browser: http://localhost:5173/user-manager
3. Expected: Redirect to /welcome
4. Console log: "Guest user trying to access admin page..."
```

**Case 2: Regular user tries `/user-manager`**
```
1. Login as user
2. Type in browser: http://localhost:5173/user-manager
3. Expected: Alert + redirect to /
4. Console log: "Non-admin user trying to access admin page..."
```

**Case 3: Admin accesses `/user-manager`**
```
1. Login as admin
2. Type in browser: http://localhost:5173/user-manager
3. Expected: Page loads successfully
```

---

### Scenario 6: API Endpoint Protection

**Purpose:** Verify backend API enforces role requirements

**Test with curl:**

**Test 1: Get users list (Admin only)**
```bash
# Without auth - should fail
curl -X GET http://localhost:8000/users

# Expected: 401 Unauthorized

# With user token - should fail
curl -X GET http://localhost:8000/users \
  -H "Cookie: access_token=<user_token>"

# Expected: 403 Forbidden

# With admin token - should work
curl -X GET http://localhost:8000/users \
  -H "Cookie: access_token=<admin_token>"

# Expected: 200 OK with user list
```

**Test 2: Update user role (Admin only)**
```bash
curl -X PUT http://localhost:8000/users/123/role \
  -H "Cookie: access_token=<admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"role": "admin"}'

# Expected: 200 OK
```

---

### Scenario 7: Role Change Real-time Effect

**Purpose:** Test that role changes take effect properly

**Steps:**
1. Login as regular user (role: 'user')
2. Note: Admin menu is NOT visible
3. Have an admin change your role to 'admin' via User Manager
4. Logout and login again
5. Expected: Admin menu is NOW visible

**Alternative without logout:**
```javascript
// In browser console, force refresh user data
const response = await fetch('/auth/me')
const userData = await response.json()
localStorage.setItem('user', JSON.stringify(userData))
window.location.reload()
```

---

## 🔍 Debugging Tools

### Check Current User Role

**Browser Console:**
```javascript
// Check stored user
const user = JSON.parse(localStorage.getItem('user'))
console.log('Current user:', user)
console.log('Role:', user?.role)
```

### Check Navigation Filtering

**Browser Console:**
```javascript
// Import and test filter
import { useNavigation } from '@/composables/useNavigation'

const { filterNavByRole } = useNavigation()
const navItems = [/* your nav items */]
const filtered = filterNavByRole(navItems)
console.log('Filtered navigation:', filtered)
```

### Monitor Middleware Actions

**Check Browser Console for logs:**
- `"No user found, redirecting to login"`
- `"Guest user detected, redirecting to welcome page"`
- `"Non-admin user trying to access admin page..."`
- `"Guest user trying to access admin page..."`

### Check API Responses

**Browser DevTools → Network Tab:**
1. Filter by "Fetch/XHR"
2. Click on `/users` request
3. Check:
   - Status code (200, 401, 403)
   - Response body
   - Cookie headers

---

## 🎨 Visual Verification Checklist

### Login Page
- [ ] Shows OAuth provider buttons (Google, GitHub)
- [ ] Clicking provider redirects to OAuth page
- [ ] After OAuth, redirects to callback handler

### Welcome Page (Guest only)
- [ ] Shows welcome message
- [ ] Shows instructions to request access
- [ ] Trying to navigate away redirects back

### Home Page (User + Admin)
- [ ] Loads successfully
- [ ] Shows user info in profile dropdown
- [ ] Navigation menu renders correctly

### User Manager Page (Admin only)
- [ ] Table displays all users
- [ ] Role badges show correct colors
- [ ] Menu button (⋮) opens role selector
- [ ] Role changes trigger API call
- [ ] Success/error messages appear

### Navigation Menu
- [ ] Guest: Only sees public items (but redirects on click)
- [ ] User: Sees Home + Second page (no Admin)
- [ ] Admin: Sees Home + Second page + Admin menu
- [ ] Admin menu expands to show User Manager
- [ ] Icons render correctly (🏠 🛡️ 👥)

---

## 🚨 Common Issues & Solutions

### Issue 1: "Admin menu visible to regular user"

**Possible Causes:**
- Navigation filtering not applied
- Layout component not using `filteredNavItems`

**Debug:**
```javascript
// Check if filtering is active
console.log(filteredNavItems.value)
```

**Solution:**
- Verify layout uses `:nav-items="filteredNavItems"`
- Check console for errors

### Issue 2: "Can access /user-manager directly despite not being admin"

**Possible Causes:**
- Middleware not running
- Route not in `adminRoutes` array

**Debug:**
- Check browser console for middleware logs
- Verify middleware file exists: `src/middleware/auth.global.js`

**Solution:**
```javascript
// Ensure route is in adminRoutes
const adminRoutes = ['/user-manager']
```

### Issue 3: "Role change doesn't take effect"

**Possible Causes:**
- User data cached in localStorage
- Token not refreshed

**Solution:**
1. Logout and login again, OR
2. Force refresh user data (see Scenario 7)

### Issue 4: "API returns 401 even with valid token"

**Possible Causes:**
- Cookie not sent with request
- Token expired
- Backend not running

**Debug:**
```bash
# Check if backend is running
curl http://localhost:8000/health

# Check API docs
open http://localhost:8000/docs
```

---

## 📊 Complete Test Checklist

### Frontend Tests
- [ ] Guest user confined to welcome page
- [ ] Regular user can access home and second page
- [ ] Regular user blocked from admin pages
- [ ] Admin can access all pages
- [ ] Navigation menu filters by role
- [ ] Direct URL access respects middleware
- [ ] Page-level composables work correctly

### Backend Tests
- [ ] `/users` endpoint requires admin role
- [ ] `/users/{id}/role` endpoint requires admin role
- [ ] Non-admin requests return 403
- [ ] Unauthenticated requests return 401
- [ ] Role changes persist to database

### Integration Tests
- [ ] Login flow works end-to-end
- [ ] OAuth callbacks handle correctly
- [ ] User data syncs between frontend/backend
- [ ] Role changes reflect in UI after login
- [ ] All three security layers work together

### UI/UX Tests
- [ ] Navigation menu smooth and responsive
- [ ] User Manager table renders properly
- [ ] Role change dropdown works
- [ ] Success/error messages appear
- [ ] Icons display correctly
- [ ] No console errors

---

## 🎯 Performance Checks

### Navigation Filtering Performance
```javascript
// Measure filter time
console.time('navigation-filter')
const filtered = filterNavByRole(navItems)
console.timeEnd('navigation-filter')
// Expected: < 1ms for typical nav (5-10 items)
```

### Page Load Performance
- Home page: < 500ms initial load
- User Manager: < 1s to load user list
- Navigation render: < 100ms

---

## 📝 Test Results Template

```markdown
## Test Session: [Date]
**Tester:** [Name]
**Environment:** Development

### Scenario 1: Guest User ✅ / ❌
- Welcome page: ✅
- Redirection: ✅
- Navigation: ✅
- Notes: [Any issues]

### Scenario 2: Regular User ✅ / ❌
- Home access: ✅
- Admin blocking: ✅
- Navigation: ✅
- Notes: [Any issues]

### Scenario 3: Admin User ✅ / ❌
- Full access: ✅
- User Manager: ✅
- Role updates: ✅
- Notes: [Any issues]

### Issues Found
1. [Issue description]
   - Steps to reproduce
   - Expected vs Actual
   - Screenshot/logs

### Overall Status
- [ ] All tests passed
- [ ] Some issues found (see above)
- [ ] Major issues - requires fixes
```

---

## 🎓 Next Steps After Testing

If all tests pass:
1. ✅ Commit all changes
2. ✅ Create pull request
3. ✅ Deploy to staging
4. ✅ Run tests again on staging
5. ✅ Deploy to production

If issues found:
1. Document in GitHub Issues
2. Prioritize by severity
3. Fix critical issues first
4. Re-test after fixes

---

**Happy Testing! 🚀**

For questions or issues, refer to:
- [ADMIN_PROTECTION_GUIDE.md](ADMIN_PROTECTION_GUIDE.md)
- [NAVIGATION_GUIDE.md](NAVIGATION_GUIDE.md)
