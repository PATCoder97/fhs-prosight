---
name: fe-login-page
status: backlog
created: 2026-01-12T12:00:28Z
progress: 0%
prd: .claude/prds/fe-login-page.md
github: https://github.com/PATCoder97/fhs-prosight/issues/65
---

# Epic: Trang đăng nhập OAuth cho FHS ProSight

## Overview

Thay thế form đăng nhập truyền thống (email/password) bằng OAuth authentication qua Google và GitHub cho hệ thống nội bộ FHS ProSight. Epic này tập trung vào việc cập nhật UI components hiện có (Vuexy template), tích hợp với backend OAuth APIs đã có sẵn, và xử lý OAuth callback flow để lưu token vào localStorage.

**Phương pháp kỹ thuật chính:**
- Tận dụng Vuexy template và Vuetify components có sẵn
- Cập nhật AuthProvider.vue component để chỉ hiển thị Google/GitHub buttons
- Đơn giản hóa login.vue bằng cách xóa form fields không cần thiết
- Sử dụng window.location.href để redirect đến backend OAuth endpoints
- Xử lý callback với Vue Router và localStorage

## Architecture Decisions

### 1. Component Strategy: Modify Existing vs Create New
**Decision**: Cập nhật `AuthProvider.vue` component có sẵn thay vì tạo component mới

**Rationale**:
- AuthProvider.vue đã có sẵn cấu trúc cho OAuth buttons (Facebook, Twitter, GitHub, Google)
- Chỉ cần xóa Facebook/Twitter và thay đổi layout từ icon buttons → full-width buttons
- Giảm thiểu code mới, tận dụng styling và theme integration có sẵn
- Vuexy template đã có dark/light mode support built-in

**Alternative Rejected**: Tạo component mới OAuthButtons.vue
- Lý do bỏ: Tạo duplicate code, phải re-implement theme integration

### 2. OAuth Redirect Approach
**Decision**: Sử dụng `window.location.href` để full-page redirect đến backend OAuth endpoints

**Rationale**:
- OAuth flow yêu cầu full redirect để provider có thể authenticate user
- Backend đã implement OAuth endpoints và callback handling
- Đơn giản, không cần popup hoặc iframe (tránh popup blockers)

**Implementation**:
```javascript
const handleGoogleLogin = () => {
  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001'
  window.location.href = `${baseUrl}/api/auth/login/google`
}
```

### 3. Token Storage Strategy
**Decision**: Sử dụng localStorage với key `auth_token`

**Rationale**:
- PRD requirement: localStorage (không dùng cookies/sessionStorage)
- Đơn giản, dễ debug
- Token persists qua browser refresh
- Compatible với existing Vuexy auth patterns

**Security consideration**:
- XSS risk được chấp nhận vì đây là internal app
- Production phải dùng HTTPS để bảo vệ token in transit

### 4. State Management
**Decision**: Không sử dụng Pinia store, sử dụng localStorage trực tiếp

**Rationale**:
- Giảm complexity cho simple use case
- Token chỉ cần lưu/đọc/xóa - không cần reactive state management
- Nếu cần mở rộng sau, dễ dàng migrate sang Pinia

**Alternative Rejected**: Tạo auth store với Pinia
- Lý do bỏ: Over-engineering cho yêu cầu đơn giản

### 5. Callback Route Handling
**Decision**: Tạo route `/auth/callback` riêng để xử lý OAuth callback

**Rationale**:
- Tách biệt logic callback khỏi login page
- Dễ debug và test
- Backend có thể redirect đến URL cố định

**Implementation Pattern**:
```javascript
// router/index.js
{
  path: '/auth/callback',
  component: () => import('@/pages/auth-callback.vue'),
  meta: { layout: 'blank', public: true }
}
```

### 6. Environment Configuration
**Decision**: Sử dụng Vite environment variables với `.env` file

**Rationale**:
- Vite built-in support cho `import.meta.env`
- Dễ cấu hình cho dev/staging/production
- Fallback về localhost cho development

## Technical Approach

### Frontend Components

#### 1. AuthProvider.vue Update
**Current State**: Icon buttons cho 4 providers (Facebook, Twitter, GitHub, Google)

**Changes Needed**:
```vue
<script setup>
const authProviders = [
  {
    name: 'Google',
    icon: 'tabler-brand-google-filled',
    color: '#db4437',
    action: () => loginWithOAuth('google')
  },
  {
    name: 'GitHub',
    icon: 'tabler-brand-github-filled',
    color: '#272727',
    colorInDark: '#fff',
    action: () => loginWithOAuth('github')
  }
]

const loginWithOAuth = (provider) => {
  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001'
  window.location.href = `${baseUrl}/api/auth/login/${provider}`
}
</script>

<template>
  <div class="d-flex flex-column gap-4">
    <VBtn
      v-for="provider in authProviders"
      :key="provider.name"
      block
      size="large"
      @click="provider.action"
    >
      <VIcon :icon="provider.icon" start />
      Đăng nhập với {{ provider.name }}
    </VBtn>
  </div>
</template>
```

#### 2. login.vue Simplification
**Current State**: Full login form với email/password/remember me/forgot password/create account

**Changes**:
- Xóa: VForm, input fields, checkbox, links (lines 90-150)
- Giữ: Logo, welcome message, layout structure, illustration
- Thêm: Subtitle hướng dẫn, AuthProvider component

**Result**: Clean UI chỉ với welcome message và 2 OAuth buttons

#### 3. Auth Callback Page (NEW)
**File**: `frontend/src/pages/auth-callback.vue`

**Purpose**: Handle OAuth redirect callback, parse token, save to localStorage, redirect to dashboard

```vue
<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

onMounted(() => {
  // Parse token from URL (query or fragment)
  const urlParams = new URLSearchParams(window.location.search)
  const hashParams = new URLSearchParams(window.location.hash.substring(1))

  const token = urlParams.get('token') || hashParams.get('token')
  const error = urlParams.get('error')

  if (error) {
    // Handle error: redirect to login with error message
    router.push({ path: '/login', query: { error } })
    return
  }

  if (token) {
    // Validate JWT format (basic check)
    if (token.split('.').length === 3) {
      localStorage.setItem('auth_token', token)
      router.push('/dashboard') // or wherever user should go
    } else {
      router.push({ path: '/login', query: { error: 'invalid_token' } })
    }
  } else {
    router.push({ path: '/login', query: { error: 'no_token' } })
  }
})
</script>

<template>
  <div class="d-flex align-center justify-center" style="min-height: 100vh;">
    <VProgressCircular indeterminate color="primary" />
    <span class="ml-4">Đang xử lý đăng nhập...</span>
  </div>
</template>
```

### Backend Services

**Note**: Backend đã được implement, không cần thay đổi

**Expected Endpoints**:
- `GET /api/auth/login/google` - Redirects to Google OAuth consent screen
- `GET /api/auth/login/github` - Redirects to GitHub OAuth authorization
- Backend handles callback từ OAuth providers và redirect về frontend với token

**Callback Format Assumption**:
```
http://localhost:5173/auth/callback?token=<JWT_TOKEN>
```

### Infrastructure

#### Environment Configuration
**Development**:
```env
# frontend/.env
VITE_API_BASE_URL=http://127.0.0.1:8001
```

**Staging/Production**:
```env
VITE_API_BASE_URL=https://api.fhs-prosight.com
```

#### File Changes Summary
```
Modified:
- frontend/src/pages/login.vue (simplify UI)
- frontend/src/views/pages/authentication/AuthProvider.vue (update buttons)
- frontend/.env.example (add VITE_API_BASE_URL example)

Created:
- frontend/.env (local config)
- frontend/src/pages/auth-callback.vue (OAuth callback handler)

Optional (if needed):
- frontend/src/composables/useAuth.js (auth utilities)
- frontend/src/utils/token.js (token validation helpers)
```

## Implementation Strategy

### Development Phases

**Phase 1: Configuration & Setup**
- Tạo `.env` file với API base URL
- Update `.env.example` với documentation
- Verify backend endpoints hoạt động

**Phase 2: UI Updates**
- Update AuthProvider.vue: xóa Facebook/Twitter, thay đổi layout
- Update login.vue: xóa form fields, giữ layout
- Test UI trên dark/light mode

**Phase 3: OAuth Integration**
- Tạo auth-callback.vue page
- Add route `/auth/callback` vào router
- Implement token parsing và localStorage logic
- Add error handling

**Phase 4: Testing & Polish**
- Test complete OAuth flow với Google và GitHub
- Test error scenarios
- Verify responsive design
- ESLint cleanup

### Risk Mitigation

**Risk 1: Backend OAuth endpoints chưa sẵn sàng**
- Mitigation: Test endpoints trước khi bắt đầu
- Fallback: Mock OAuth flow cho development

**Risk 2: Token format không match expectations**
- Mitigation: Liên hệ backend team để confirm JWT format
- Test case: Validate token có 3 parts (header.payload.signature)

**Risk 3: OAuth callback URL mismatch**
- Mitigation: Confirm với backend team về exact callback URL
- Document: Frontend expect `/auth/callback?token=...`

**Risk 4: Popup blockers**
- Mitigation: Sử dụng full-page redirect (không dùng popup)
- User education: Nếu bị block, cho phép popups

### Testing Approach

**Manual Testing Checklist**:
1. Google OAuth flow end-to-end
2. GitHub OAuth flow end-to-end
3. Token persistence sau browser refresh
4. Error handling (user cancels, network error)
5. Dark/light mode UI
6. Responsive design (mobile/tablet/desktop)
7. Browser compatibility (Chrome, Firefox, Safari, Edge)

**No Automated Tests**: PRD states manual testing only

## Task Breakdown Preview

Epic này sẽ được break down thành **8 tasks chính**:

- [ ] **Task 1: Environment Configuration**
  - Tạo `.env` và `.env.example` với VITE_API_BASE_URL
  - Document configuration cho dev/staging/production

- [ ] **Task 2: Update AuthProvider Component**
  - Xóa Facebook/Twitter providers
  - Thay đổi layout: icon buttons → full-width buttons với text
  - Add click handlers cho OAuth redirect
  - Style buttons theo spec (colors, spacing)

- [ ] **Task 3: Simplify Login Page**
  - Xóa form fields (email, password, remember me, forgot password, create account)
  - Giữ layout structure (logo, welcome, illustration)
  - Update welcome message và thêm subtitle
  - Test responsive layout

- [ ] **Task 4: Create OAuth Callback Handler**
  - Tạo `auth-callback.vue` page
  - Parse token từ URL query/fragment params
  - Validate token format (basic JWT check)
  - Save token to localStorage
  - Redirect to dashboard hoặc handle errors

- [ ] **Task 5: Add Router Configuration**
  - Add `/auth/callback` route với layout blank và public meta
  - Verify routing hoạt động đúng

- [ ] **Task 6: Error Handling & UX Polish**
  - Display error messages trên login page nếu OAuth fails
  - Add loading states khi redirect
  - User-friendly error messages

- [ ] **Task 7: Testing**
  - Test Google OAuth complete flow
  - Test GitHub OAuth complete flow
  - Test error scenarios
  - Verify dark/light mode, responsive design
  - Cross-browser testing

- [ ] **Task 8: Code Review & Cleanup**
  - ESLint fixes
  - Remove unused code
  - Code review
  - Documentation

## Dependencies

### External Dependencies
1. **Backend OAuth APIs** (CRITICAL)
   - Status: Assumed ready
   - Endpoints: `/api/auth/login/google`, `/api/auth/login/github`
   - Owner: Backend team
   - Risk: HIGH - cannot proceed without working endpoints

2. **OAuth Provider Configuration** (CRITICAL)
   - Google Cloud Console: OAuth client ID configured
   - GitHub OAuth Apps: Application registered
   - Callback URLs properly configured
   - Risk: HIGH - 401/403 errors if misconfigured

### Internal Dependencies
1. **Vuexy Template** (READY)
   - Vuetify components: VBtn, VCard, VIcon
   - Tabler icons: tabler-brand-google-filled, tabler-brand-github-filled
   - Theme system: Dark/light mode
   - Risk: LOW

2. **Vue Router** (READY)
   - Need to verify router configuration
   - Add new route for callback
   - Risk: LOW

### No New Libraries Needed
- All dependencies already in package.json (Vue, Vuetify, Vue Router, jwt-decode)

## Success Criteria (Technical)

### Performance Benchmarks
- ✅ Login page load time: < 2 seconds
- ✅ OAuth redirect latency: < 100ms from button click
- ✅ Token storage operation: synchronous (no race conditions)
- ✅ Callback processing: < 500ms

### Quality Gates
- ✅ Zero ESLint errors
- ✅ Zero console errors in browser
- ✅ All manual test cases pass
- ✅ Code review approved
- ✅ Works in Chrome, Firefox, Safari, Edge (latest versions)

### Acceptance Criteria
1. User can click "Đăng nhập với Google" → redirects to Google → returns with token → lands on dashboard
2. User can click "Đăng nhập với GitHub" → redirects to GitHub → returns with token → lands on dashboard
3. Token persists in localStorage after browser refresh
4. Error messages display clearly if OAuth fails
5. UI looks good in both dark and light modes
6. Mobile/tablet/desktop layouts work correctly
7. No email/password form visible on login page

## Estimated Effort

### Overall Timeline
- **Setup & Config**: 0.5 days
- **UI Updates**: 1 day
- **OAuth Integration**: 1 day
- **Testing & Polish**: 1 day
- **Total**: 3.5 days (chưa tính buffer)

### Resource Requirements
- 1 Frontend Developer (Vue.js experience)
- Access to backend team for API verification
- Test accounts for Google and GitHub OAuth

### Critical Path Items
1. Backend API verification (BLOCKER nếu chưa sẵn sàng)
2. OAuth provider configuration (BLOCKER nếu chưa setup)
3. AuthProvider component update (CRITICAL - core UI)
4. Callback handler implementation (CRITICAL - core flow)

## Tasks Created
- [ ] #66 - Environment Configuration (parallel: true)
- [ ] #67 - Update AuthProvider Component (parallel: false)
- [ ] #68 - Simplify Login Page UI (parallel: false)
- [ ] #69 - Create OAuth Callback Handler Page (parallel: true)
- [ ] #70 - Add OAuth Callback Route to Router (parallel: false)
- [ ] #71 - Error Handling & UX Polish (parallel: false)
- [ ] #72 - Manual Testing & QA (parallel: false)
- [ ] #73 - Code Review & Cleanup (parallel: false)

**Total tasks**: 8
**Parallel tasks**: 2
**Sequential tasks**: 6
**Estimated total effort**: ~17.5 hours (~2.2 days)
---

**Epic Status**: Backlog
**Created**: 2026-01-12T12:00:28Z
**PRD Source**: `.claude/prds/fe-login-page.md`
**Tasks**: 8 tasks created and ready for implementation
