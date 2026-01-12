# OAuth Login Implementation - Documentation

## Overview
This document provides complete documentation for the OAuth login implementation in the FHS ProSight frontend application.

## Architecture

### Flow Diagram
```
User clicks OAuth button
    ↓
Redirect to backend: /api/auth/login/{provider}
    ↓
Backend redirects to OAuth provider (Google/GitHub)
    ↓
User authorizes on provider
    ↓
Provider redirects to backend: /api/auth/{provider}/callback
    ↓
Backend processes OAuth code and exchanges for token
    ↓
Backend redirects to frontend: /auth-callback?access_token=...&user_id=...&user_role=...
    ↓
Frontend saves token + user data to localStorage
    ↓
Frontend routes based on role:
  - role != 'guest' → Home page (/)
  - role == 'guest' → Login page (/login)
```

## Components

### 1. AuthProvider.vue
**Location:** `frontend/src/views/pages/authentication/AuthProvider.vue`

**Purpose:** Displays OAuth login buttons for Google and GitHub

**Key Features:**
- Full-width button layout with provider icons
- Vietnamese labels
- Dark/light theme support
- Dynamic base URL from environment variables

**Code:**
```vue
const loginWithOAuth = provider => {
  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001'
  window.location.href = `${baseUrl}/api/auth/login/${provider.toLowerCase()}`
}
```

### 2. login.vue
**Location:** `frontend/src/pages/login.vue`

**Purpose:** Main login page with OAuth buttons and error handling

**Key Features:**
- Clean UI with only OAuth buttons (no email/password form)
- Vietnamese welcome message
- Error alert component with auto-dismiss
- Responsive design

**Error Handling:**
```javascript
const errorMessages = {
  access_denied: 'Bạn đã hủy đăng nhập. Vui lòng thử lại.',
  invalid_token: 'Token không hợp lệ. Vui lòng thử đăng nhập lại.',
  no_token: 'Không nhận được token. Vui lòng thử đăng nhập lại.',
  default: 'Đã xảy ra lỗi. Vui lòng thử lại.',
}
```

### 3. auth-callback.vue
**Location:** `frontend/src/pages/auth-callback.vue`

**Purpose:** Handles OAuth callback from backend

**Key Features:**
- Parses access_token and user data from URL parameters
- Validates JWT token format (3-part structure)
- Saves data to localStorage
- Implements role-based routing
- Error handling with redirect to login

**URL Parameters Expected:**
- `access_token` - JWT token from backend
- `user_id` - User's unique ID
- `user_role` - User's role (for routing logic)
- `user_email` - User's email address
- `user_full_name` - User's full name
- `user_avatar` - User's avatar URL
- `user_provider` - OAuth provider (google/github)

**localStorage Structure:**
```javascript
// access_token (string)
localStorage.setItem('access_token', 'eyJhbGc...')

// user (JSON string)
localStorage.setItem('user', JSON.stringify({
  id: '123',
  role: 'admin',
  email: 'user@example.com',
  full_name: 'John Doe',
  avatar: 'https://...',
  provider: 'google'
}))
```

## Configuration

### Environment Variables
**File:** `frontend/.env`

```env
# API Base URL for backend OAuth endpoints
VITE_API_BASE_URL=http://127.0.0.1:8001
```

**File:** `frontend/.env.example`

```env
# API Base URL
# Development: http://127.0.0.1:8001
# Staging: https://staging-api.fhs-prosight.com
# Production: https://api.fhs-prosight.com
VITE_API_BASE_URL=http://127.0.0.1:8001
```

## Backend Requirements

### Expected Endpoints

1. **OAuth Login Initiation:**
   - `GET /api/auth/login/google` - Redirects to Google OAuth
   - `GET /api/auth/login/github` - Redirects to GitHub OAuth

2. **OAuth Callback Handler:**
   - `GET /api/auth/google/callback` - Processes Google OAuth callback
   - `GET /api/auth/github/callback` - Processes GitHub OAuth callback

3. **Frontend Redirect Format:**
   After processing OAuth callback, backend should redirect to:
   ```
   http://localhost:3000/auth-callback?access_token={JWT}&user_id={ID}&user_role={ROLE}&user_email={EMAIL}&user_full_name={NAME}&user_avatar={AVATAR_URL}&user_provider={PROVIDER}
   ```

### Expected Response Data

Backend should provide these parameters in the callback URL:

```javascript
{
  access_token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  user_id: "12345",
  user_role: "admin",  // or "employee", "guest", etc.
  user_email: "user@example.com",
  user_full_name: "John Doe",
  user_avatar: "https://avatars.githubusercontent.com/...",
  user_provider: "google"  // or "github"
}
```

## Routing Logic

### Role-Based Navigation

```javascript
if (userRole && userRole !== 'guest') {
  router.push('/')  // Home page for authenticated users
} else {
  router.push('/login')  // Back to login for guests
}
```

### Route Configuration

**Path:** `/auth-callback`

**Meta:**
- `layout: 'blank'` - No navigation/sidebar
- `public: true` - Accessible without authentication

## Error Handling

### Error Types

1. **access_denied** - User cancelled OAuth authorization
2. **invalid_token** - Token format is invalid (not 3-part JWT)
3. **no_token** - No token received from backend
4. **default** - Any other error

### Error Flow

```
Error occurs
    ↓
Redirect to /login with error query param
    ↓
Login page displays Vietnamese error message
    ↓
Auto-dismiss after 5 seconds
```

## Security Considerations

1. **JWT Validation:** Basic structure validation (3-part token)
2. **Environment Variables:** .env file in .gitignore
3. **No Sensitive Data:** No hardcoded credentials
4. **Error Messages:** User-friendly without exposing internals

## Testing

### Manual Test Cases

See GitHub Issue #72 for complete testing guide.

**Quick Test:**
1. Start backend server
2. Start frontend dev server
3. Navigate to `/login`
4. Click OAuth button
5. Complete authorization
6. Verify redirect to home page
7. Check localStorage in DevTools

### Verification Commands

```javascript
// Check localStorage
localStorage.getItem('access_token')
JSON.parse(localStorage.getItem('user'))

// Expected output
{
  id: "...",
  role: "admin",
  email: "...",
  full_name: "...",
  avatar: "...",
  provider: "google"
}
```

## Troubleshooting

### Common Issues

1. **"No token received" error**
   - Check backend is running on correct port
   - Verify VITE_API_BASE_URL is correct
   - Check backend redirect URL is correct

2. **"Invalid token" error**
   - Verify backend returns valid JWT format
   - Check token has 3 parts (header.payload.signature)

3. **OAuth redirect fails**
   - Verify OAuth credentials configured in backend
   - Check callback URLs in Google Cloud Console / GitHub OAuth App
   - Ensure backend callback handlers are working

4. **Dark mode button colors wrong**
   - Check Vuetify theme configuration
   - Verify icon colors in AuthProvider.vue

## Files Modified

```
frontend/
├── .env                    # Environment configuration (gitignored)
├── .env.example            # Environment template
├── .gitignore              # Added .env
├── src/
│   ├── pages/
│   │   ├── login.vue       # Simplified to OAuth-only
│   │   └── auth-callback.vue  # OAuth callback handler (NEW)
│   └── views/
│       └── pages/
│           └── authentication/
│               └── AuthProvider.vue  # Google + GitHub buttons only
```

## Git Commits

- **8c25762** - Initial OAuth implementation
- **8c70ff3** - Error handling and UX polish
- **ec20351** - Full user data handling and role-based routing
- **c01fa68** - ESLint formatting

## GitHub Issues

- **Epic #65** - fe-login-page
- **Task #66** - Environment Configuration ✅
- **Task #67** - Update AuthProvider Component ✅
- **Task #68** - Simplify Login Page UI ✅
- **Task #69** - Create OAuth Callback Handler Page ✅
- **Task #70** - Add OAuth Callback Route to Router ✅
- **Task #71** - Error Handling & UX Polish ✅
- **Task #72** - Manual Testing & QA ⏳
- **Task #73** - Code Review & Cleanup ✅

## Next Steps

1. **Manual Testing (Task #72):**
   - Start backend server
   - Test Google OAuth flow
   - Test GitHub OAuth flow
   - Verify role-based routing
   - Check localStorage data

2. **Production Deployment:**
   - Update VITE_API_BASE_URL for staging/production
   - Verify OAuth callback URLs configured
   - Test on production environment

3. **Future Enhancements:**
   - Add token refresh logic
   - Implement auto-logout on token expiry
   - Add more OAuth providers if needed
   - Enhance error handling with retry logic

---

**Last Updated:** 2026-01-12
**Status:** Implementation Complete, Testing Pending
