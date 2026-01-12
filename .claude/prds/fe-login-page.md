---
name: fe-login-page
description: Trang đăng nhập OAuth (Google, GitHub) cho hệ thống nội bộ FHS ProSight
status: backlog
created: 2026-01-12T11:42:43Z
---

# PRD: Trang đăng nhập FHS ProSight với OAuth

## Executive Summary

Xây dựng trang đăng nhập cho hệ thống nội bộ FHS ProSight sử dụng OAuth authentication thông qua Google và GitHub. Trang đăng nhập sẽ thay thế hoàn toàn form đăng nhập truyền thống (email/password) bằng hai nút OAuth, giữ nguyên thiết kế Vuexy template hiện có.

**Mục tiêu chính:**
- Đơn giản hóa quy trình đăng nhập cho nhân viên nội bộ
- Tăng cường bảo mật thông qua OAuth providers
- Tích hợp với backend API có sẵn
- Duy trì trải nghiệm người dùng nhất quán với Vuexy design system

## Problem Statement

### Vấn đề hiện tại
Trang đăng nhập hiện tại (`frontend/src/pages/login.vue`) đang sử dụng form đăng nhập truyền thống với email/password, bao gồm nhiều tính năng không cần thiết cho hệ thống nội bộ như:
- Form nhập email/password thủ công
- Checkbox "Remember me"
- Link "Forgot Password"
- Link "Create an account"
- AuthProvider component hiển thị 4 social providers (Facebook, Twitter, GitHub, Google) nhưng chưa có chức năng thực tế

### Tại sao cần thay đổi ngay bây giờ?
1. **Bảo mật**: OAuth providers (Google, GitHub) cung cấp bảo mật tốt hơn so với việc quản lý mật khẩu nội bộ
2. **Trải nghiệm người dùng**: Nhân viên có thể đăng nhập nhanh chóng bằng tài khoản công ty (Google) hoặc tài khoản developer (GitHub) mà không cần nhớ thêm mật khẩu
3. **Backend đã sẵn sàng**: API endpoints OAuth đã được xây dựng ở backend, chỉ cần tích hợp frontend
4. **Đơn giản hóa**: Loại bỏ các tính năng không cần thiết (forgot password, create account) phù hợp với hệ thống nội bộ

## User Stories

### Persona: Nhân viên nội bộ FHS
**Background**: Nhân viên làm việc tại FHS, có tài khoản Google công ty và/hoặc GitHub cá nhân

**User Journey - Đăng nhập thành công:**
```
1. Nhân viên truy cập trang đăng nhập FHS ProSight
2. Nhìn thấy 2 nút: "Đăng nhập với Google" và "Đăng nhập với GitHub"
3. Click vào nút "Đăng nhập với Google"
4. Được chuyển hướng đến trang đăng nhập Google
5. Chọn tài khoản Google công ty
6. Google xác thực và chuyển hướng về FHS ProSight
7. Hệ thống nhận token, lưu vào localStorage
8. Tự động chuyển đến trang dashboard
9. Lần truy cập tiếp theo, nếu token còn hợp lệ, tự động đăng nhập
```

**Pain Points được giải quyết:**
- ❌ Không cần nhớ mật khẩu riêng cho hệ thống nội bộ
- ❌ Không cần quy trình reset mật khẩu
- ❌ Không cần tạo tài khoản mới (quản trị viên quản lý qua OAuth)
- ✅ Đăng nhập nhanh chóng bằng 1 click
- ✅ Sử dụng tài khoản đã có sẵn (Google/GitHub)

### Persona: Quản trị viên hệ thống
**Background**: Quản lý truy cập hệ thống, cấu hình OAuth settings

**User Journey - Cấu hình base URL:**
```
1. Quản trị viên tạo/sửa file .env trong frontend
2. Thêm biến VITE_API_BASE_URL=http://127.0.0.1:8001
3. Hệ thống tự động sử dụng base URL này cho các API calls
4. Có thể thay đổi base URL cho môi trường staging/production
```

**Pain Points được giải quyết:**
- ✅ Dễ dàng cấu hình API endpoint cho các môi trường khác nhau
- ✅ Tập trung quản lý cấu hình qua file .env
- ✅ Không cần hardcode URL trong code

## Requirements

### Functional Requirements

#### FR1: OAuth Login Buttons
- **FR1.1**: Hiển thị 2 nút đăng nhập với thiết kế rõ ràng:
  - Nút "Đăng nhập với Google" với icon Google và màu sắc brand (#db4437)
  - Nút "Đăng nhập với GitHub" với icon GitHub và màu sắc phù hợp (#272727 light mode, #fff dark mode)
- **FR1.2**: Nút phải responsive, hoạt động tốt trên cả desktop và mobile
- **FR1.3**: Sử dụng Vuetify components và icons từ Tabler (đã có sẵn trong Vuexy)
- **FR1.4**: Hover state và loading state rõ ràng

#### FR2: OAuth Flow Integration
- **FR2.1**: Click nút Google → redirect đến `{API_BASE_URL}/api/auth/login/google`
- **FR2.2**: Click nút GitHub → redirect đến `{API_BASE_URL}/api/auth/login/github`
- **FR2.3**: Xử lý OAuth callback khi provider redirect về
- **FR2.4**: Parse query parameters để lấy token từ URL callback
- **FR2.5**: Validate token format trước khi lưu

#### FR3: Token Management
- **FR3.1**: Lưu token vào localStorage với key `auth_token` (hoặc tên phù hợp)
- **FR3.2**: Tự động redirect đến trang dashboard sau khi đăng nhập thành công
- **FR3.3**: Hiển thị error message nếu callback thất bại
- **FR3.4**: Clear localStorage nếu token invalid

#### FR4: Base URL Configuration
- **FR4.1**: Tạo biến môi trường `VITE_API_BASE_URL` trong file `.env`
- **FR4.2**: Sử dụng `import.meta.env.VITE_API_BASE_URL` để lấy base URL
- **FR4.3**: Fallback về `http://127.0.0.1:8001` nếu không có trong .env
- **FR4.4**: Cập nhật `.env.example` với ví dụ cấu hình

#### FR5: UI/UX Update
- **FR5.1**: Xóa các phần tử đăng nhập truyền thống:
  - Input field email/username (lines 93-101)
  - Input field password (lines 104-113)
  - Checkbox "Remember me" (line 116-119)
  - Link "Forgot Password?" (lines 120-125)
  - Button "Login" submit (lines 128-133)
  - Section "New on our platform? Create an account" (lines 136-150)
- **FR5.2**: Giữ nguyên:
  - Logo và title (lines 32-39)
  - Layout 2 cột (illustration bên trái, form bên phải)
  - Background và styling
  - VCard container và cấu trúc
  - Welcome message "Welcome to FHS ProSight! 👋🏻"
  - Divider "or" (lines 152-159) - có thể giữ hoặc xóa tùy thiết kế
- **FR5.3**: Thêm mới:
  - 2 nút OAuth lớn, rõ ràng với icon và text
  - Subtitle hướng dẫn: "Vui lòng đăng nhập bằng tài khoản Google hoặc GitHub"
  - Loading state khi click nút OAuth

#### FR6: OAuth Buttons Design
- **FR6.1**: Tạo 2 nút OAuth với thiết kế đẹp mắt:
  - **Google Button**:
    - Icon: `tabler-brand-google-filled`
    - Text: "Đăng nhập với Google"
    - Color: #db4437 (light mode), #db4437 (dark mode)
    - Full width button với border radius phù hợp Vuexy
  - **GitHub Button**:
    - Icon: `tabler-brand-github-filled`
    - Text: "Đăng nhập với GitHub"
    - Color: #272727 (light mode), #fff text + dark background (dark mode)
    - Full width button với border radius phù hợp Vuexy
- **FR6.2**: Button spacing: gap 16px giữa 2 nút
- **FR6.3**: Thêm click handlers để redirect đến OAuth endpoints
- **FR6.4**: Hover effects và ripple animation (Vuetify default)

### Non-Functional Requirements

#### NFR1: Performance
- **NFR1.1**: Trang login load trong < 2 giây
- **NFR1.2**: OAuth redirect phải xảy ra ngay lập tức khi click (< 100ms)
- **NFR1.3**: Token storage phải đồng bộ (synchronous) để tránh race conditions

#### NFR2: Security
- **NFR2.1**: Không lưu thông tin nhạy cảm ngoài token
- **NFR2.2**: Sử dụng HTTPS trong production (cấu hình base URL)
- **NFR2.3**: Validate token format (JWT) trước khi lưu
- **NFR2.4**: Implement CSRF protection nếu backend yêu cầu
- **NFR2.5**: Không log token ra console trong production

#### NFR3: Browser Compatibility
- **NFR3.1**: Hỗ trợ Chrome, Firefox, Safari, Edge (phiên bản mới nhất)
- **NFR3.2**: localStorage phải available (fallback message nếu không)
- **NFR3.3**: Popup blocker handling cho OAuth flow

#### NFR4: Maintainability
- **NFR4.1**: Code phải tuân thủ ESLint rules hiện tại của Vuexy
- **NFR4.2**: Sử dụng Vue 3 Composition API (setup script)
- **NFR4.3**: TypeScript types cho token và config
- **NFR4.4**: Comments cho các phần logic phức tạp

#### NFR5: Responsive Design
- **NFR5.1**: Hoạt động tốt trên mobile (< 768px)
- **NFR5.2**: Buttons có kích thước touch-friendly (min 44x44px)
- **NFR5.3**: Text readable trên mọi kích thước màn hình

## Success Criteria

### Measurable Outcomes

1. **Functional Success:**
   - ✅ 100% nhân viên có thể đăng nhập thành công qua Google hoặc GitHub
   - ✅ 0 errors trong OAuth flow khi test với 10+ accounts
   - ✅ Token được lưu và persist qua browser refresh

2. **User Experience:**
   - ✅ Thời gian đăng nhập trung bình < 5 giây (từ lúc click đến vào dashboard)
   - ✅ UI đơn giản, rõ ràng - không có confusion về cách đăng nhập
   - ✅ Dark mode và light mode đều hiển thị tốt

3. **Code Quality:**
   - ✅ Pass tất cả ESLint checks
   - ✅ Không có console errors trong browser
   - ✅ Code review approved bởi senior developer

### Key Metrics & KPIs

- **Login Success Rate**: > 99%
- **Average Login Time**: < 5 seconds
- **OAuth Callback Success Rate**: > 98%
- **Token Storage Success Rate**: 100%
- **Browser Compatibility**: 100% trên Chrome, Firefox, Safari, Edge latest
- **Mobile Usability**: 100% tester có thể đăng nhập thành công trên mobile

## Constraints & Assumptions

### Technical Constraints
1. **Backend API Endpoints cố định:**
   - `/api/auth/login/google` - phải giữ nguyên format
   - `/api/auth/login/github` - phải giữ nguyên format
   - Backend chịu trách nhiệm redirect về frontend với token

2. **Vuexy Template:**
   - Phải sử dụng Vuetify components có sẵn
   - Phải giữ nguyên design system và styling
   - Không được thay đổi layout chính (2-column với illustration)

3. **Browser localStorage:**
   - Dựa vào localStorage để lưu token
   - Không sử dụng cookies hoặc sessionStorage

### Assumptions
1. **Backend giả định:**
   - OAuth endpoints đã hoàn thiện và tested
   - Backend sẽ redirect về frontend URL với token trong query params hoặc fragment
   - Token format là JWT hợp lệ
   - Backend handle OAuth errors và redirect về login với error message

2. **User giả định:**
   - Tất cả nhân viên có tài khoản Google công ty hoặc GitHub
   - Users hiểu cách sử dụng OAuth (quen thuộc với "Sign in with Google")
   - Users có quyền truy cập vào email/GitHub từ thiết bị làm việc

3. **Infrastructure giả định:**
   - Development: `http://127.0.0.1:8001`
   - Production sẽ có HTTPS base URL
   - DNS và routing đã được cấu hình đúng

### Resource Limitations
- **Timeline**: Không có deadline cụ thể, nhưng ưu tiên hoàn thành nhanh
- **Team**: 1 frontend developer
- **Testing**: Manual testing, chưa có automated E2E tests

## Out of Scope

Những gì **KHÔNG** nằm trong scope của PRD này:

### ❌ Không implement
1. **Email/Password Login:**
   - Không giữ lại form đăng nhập truyền thống
   - Không có "Forgot Password" flow
   - Không có "Create Account" flow

2. **Other OAuth Providers:**
   - Không implement Facebook OAuth
   - Không implement Twitter OAuth
   - Chỉ Google và GitHub

3. **User Management:**
   - Không có trang đăng ký user mới
   - Không có trang quản lý profile
   - Admin quản lý users qua backend/database

4. **Advanced Features:**
   - Không có Remember Me (token persistence đã đủ)
   - Không có "Stay logged in" option
   - Không có multi-account switching
   - Không có biometric authentication

5. **Token Refresh:**
   - Không implement automatic token refresh trong scope này
   - Token expiration handling sẽ làm sau (redirect về login khi expired)

6. **Analytics & Monitoring:**
   - Không track login metrics
   - Không có logging/monitoring trong scope này

## Dependencies

### External Dependencies

1. **Backend API:**
   - **Owner**: Backend team
   - **Status**: Assumed completed
   - **Endpoints needed:**
     - `GET /api/auth/login/google` - Redirect to Google OAuth
     - `GET /api/auth/login/github` - Redirect to GitHub OAuth
     - Callback handling and token generation
   - **Risk**: Nếu backend chưa sẵn sàng → không thể test OAuth flow

2. **OAuth Providers:**
   - **Google OAuth**: Google Cloud Console configuration
   - **GitHub OAuth**: GitHub OAuth Apps configuration
   - **Risk**: Nếu OAuth apps chưa được setup → 401/403 errors

3. **Environment Variables:**
   - `.env` file với `VITE_API_BASE_URL`
   - DevOps team cần setup cho staging/production
   - **Risk**: Misconfiguration → wrong API endpoints

### Internal Dependencies

1. **Vuexy Template:**
   - **Components**: VBtn, VCard, VRow, VCol, VIcon
   - **Icons**: Tabler icons (tabler-brand-google-filled, tabler-brand-github-filled)
   - **Theme**: Dark/light mode support
   - **Status**: Already integrated
   - **Risk**: Low - template đã sẵn sàng

2. **Vue Router:**
   - Routing config để handle OAuth callback
   - Redirect logic sau khi đăng nhập thành công
   - **Status**: Assumed configured
   - **Risk**: Cần verify routing setup

3. **Pinia Store (optional):**
   - Có thể cần auth store để quản lý token và user state
   - **Status**: To be determined during implementation
   - **Risk**: Low - có thể dùng localStorage trực tiếp

### Third-party Libraries

1. **Already in package.json:**
   - `vue`: 3.5.14 ✅
   - `vue-router`: 4.5.1 ✅
   - `vuetify`: 3.8.5 ✅
   - `pinia`: 3.0.2 ✅
   - `@vueuse/core`: 10.11.1 ✅ (có thể dùng cho localStorage utilities)

2. **May need to add:**
   - `jwt-decode`: 4.0.0 ✅ (already in dependencies - dùng để validate JWT)

## Technical Specifications

### File Structure
```
frontend/
├── src/
│   ├── pages/
│   │   └── login.vue                          # ⚠️ Cần modify
│   ├── views/
│   │   └── pages/
│   │       └── authentication/
│   │           └── AuthProvider.vue           # ⚠️ Cần modify
│   ├── composables/                           # 🆕 Có thể cần tạo
│   │   └── useAuth.js                         # OAuth logic
│   ├── config/                                # 🆕 Có thể cần tạo
│   │   └── api.js                             # API base URL config
│   └── utils/                                 # 🆕 Có thể cần tạo
│       └── token.js                           # Token utilities
├── .env                                       # 🆕 Cần tạo
└── .env.example                               # ⚠️ Cần update
```

### API Integration Details

#### OAuth Redirect Flow
```javascript
// Click Google button → Redirect to:
window.location.href = `${API_BASE_URL}/api/auth/login/google`

// Backend processes OAuth
// Backend redirects back to:
// http://localhost:5173/auth/callback?token=eyJhbGc...
// OR
// http://localhost:5173/auth/callback#token=eyJhbGc...
```

#### Expected Backend Response Format
```javascript
// Option 1: Query parameter
GET /auth/callback?token=<JWT_TOKEN>

// Option 2: Fragment
GET /auth/callback#token=<JWT_TOKEN>

// Option 3: Error
GET /auth/callback?error=access_denied&error_description=User+cancelled
```

#### Token Storage
```javascript
// Lưu token
localStorage.setItem('auth_token', token)

// Đọc token
const token = localStorage.getItem('auth_token')

// Xóa token (logout)
localStorage.removeItem('auth_token')
```

### Implementation Checklist

#### Phase 1: Setup & Configuration
- [ ] Tạo file `.env` với `VITE_API_BASE_URL=http://127.0.0.1:8001`
- [ ] Cập nhật `.env.example` với example configuration
- [ ] Tạo `src/config/api.js` để export base URL
- [ ] Tạo `src/utils/token.js` với helper functions

#### Phase 2: Create OAuth Buttons Component
- [ ] Tạo component OAuth buttons mới hoặc cập nhật AuthProvider.vue
- [ ] Giữ lại chỉ Google và GitHub trong authProviders array
- [ ] Thay đổi từ icon buttons → full-width buttons với icon + text
- [ ] Style buttons: Google (#db4437), GitHub (#272727/white)
- [ ] Thêm click handlers để redirect to OAuth endpoints
- [ ] Add loading state khi đang redirect
- [ ] Test dark/light mode styling

#### Phase 3: Update Login Page
- [ ] Xóa các input fields: email/username (lines 93-101), password (lines 104-113)
- [ ] Xóa checkbox "Remember me" (lines 116-119)
- [ ] Xóa link "Forgot Password?" (lines 120-125)
- [ ] Xóa button "Login" submit (lines 128-133)
- [ ] Xóa section "Create an account" (lines 136-150)
- [ ] Giữ nguyên VCard, VRow, VCol structure
- [ ] Giữ nguyên welcome message "Welcome to FHS ProSight! 👋🏻"
- [ ] Thêm subtitle: "Vui lòng đăng nhập bằng tài khoản Google hoặc GitHub"
- [ ] Thay AuthProvider component bằng 2 nút OAuth mới
- [ ] Có thể xóa divider "or" (lines 152-159) vì không còn cần
- [ ] Test responsive layout trên mobile/tablet/desktop

#### Phase 4: OAuth Callback Handling
- [ ] Tạo route `/auth/callback` trong router
- [ ] Parse token từ URL (query params hoặc fragment)
- [ ] Validate token format (JWT)
- [ ] Lưu token vào localStorage
- [ ] Redirect đến dashboard
- [ ] Handle errors và hiển thị message

#### Phase 5: Testing
- [ ] Test Google OAuth flow
- [ ] Test GitHub OAuth flow
- [ ] Test token persistence (refresh browser)
- [ ] Test dark/light mode
- [ ] Test responsive design (mobile/tablet/desktop)
- [ ] Test error scenarios (user cancels, network error)

#### Phase 6: Polish
- [ ] Loading states khi redirect
- [ ] Error messages user-friendly
- [ ] ESLint cleanup
- [ ] Code review
- [ ] Documentation

## Next Steps

Sau khi PRD này được approve:

1. **Kickoff Meeting:**
   - Review PRD với team
   - Clarify backend API contract (callback URL format, token format)
   - Confirm OAuth apps đã được setup (Google Cloud, GitHub Apps)

2. **Create Epic:**
   - Run `/pm:prd-parse fe-login-page` để tạo implementation epic
   - Break down thành issues/tasks cụ thể
   - Estimate effort

3. **Development:**
   - Setup môi trường development
   - Implement theo checklist
   - Test với real OAuth providers

4. **Review & Deploy:**
   - Code review
   - QA testing
   - Deploy lên staging
   - Production deployment

---

**Created**: 2026-01-12T11:42:43Z
**Status**: Backlog
**Owner**: TBD
**Priority**: High (core authentication feature)
