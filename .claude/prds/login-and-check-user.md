---
name: login-and-check-user
description: Hoàn thiện hệ thống OAuth login với auto role checking và quản lý localId
status: backlog
created: 2026-01-08T01:50:29Z
---

# PRD: Login and Check User

## Executive Summary

Dự án này nhằm cải thiện và hoàn thiện hệ thống xác thực OAuth hiện tại (GitHub + Google), sửa các lỗi trong luồng OAuth, và thêm tính năng tự động kiểm tra vai trò người dùng. Hệ thống sẽ tự động tạo user mới với role `guest` khi đăng nhập lần đầu, đồng thời hỗ trợ quản lý `localId` (mã nhân viên) để liên kết nhiều OAuth accounts của cùng một người.

**Giá trị cốt lõi:**
- Tăng tỷ lệ đăng nhập thành công
- Trải nghiệm người dùng mượt mà hơn với OAuth
- Tự động hóa việc phân quyền cho user mới
- Quản lý danh tính nhân viên thống nhất qua nhiều OAuth providers

## Problem Statement

### Vấn đề hiện tại
1. **Lỗi trong luồng OAuth:** Có bugs trong quá trình callback và xử lý token từ GitHub/Google OAuth
2. **Thiếu auto role assignment:** User mới không được tự động gán role, gây khó khăn trong quản lý quyền
3. **Không có cơ chế check user trong DB:** Thiếu logic kiểm tra user đã tồn tại hay chưa trước khi tạo mới
4. **Quản lý localId thủ công:** Không có cơ chế tự động liên kết OAuth account với mã nhân viên (localId)
5. **Trải nghiệm đăng nhập chưa tối ưu:** User không hiểu rõ vai trò/quyền hạn của mình sau khi đăng nhập

### Tại sao quan trọng ngay bây giờ?
- Hệ thống đã có sẵn OAuth integration nhưng chưa hoàn chỉnh
- Cần nền tảng authentication vững chắc trước khi mở rộng tính năng
- User experience kém sẽ ảnh hưởng đến adoption rate
- Security risks nếu không quản lý role/permissions đúng cách

## User Stories

### Persona 1: Người dùng cuối (End User)

**User Story 1: Đăng nhập lần đầu**
```
Là một nhân viên mới
Tôi muốn đăng nhập bằng tài khoản Google/GitHub của công ty
Để có thể truy cập hệ thống mà không cần tạo password mới

Acceptance Criteria:
- Click nút "Login with Google/GitHub"
- Redirect đến OAuth provider để xác thực
- Sau khi xác thực thành công, tự động tạo account với role 'guest'
- Nhận được JWT token và redirect về dashboard
- Thấy thông báo rõ ràng về quyền hạn hiện tại (guest)
```

**User Story 2: Đăng nhập lần tiếp theo**
```
Là người dùng đã có account
Tôi muốn đăng nhập nhanh chóng
Để tiếp tục sử dụng hệ thống với quyền hạn của mình

Acceptance Criteria:
- Click "Login with Google/GitHub" (provider đã dùng trước đó)
- Xác thực OAuth thành công
- Hệ thống tìm thấy user trong DB dựa trên oauth_provider + oauth_id
- Nhận JWT token với đầy đủ thông tin: user_id, role, localId (nếu có)
- Redirect về dashboard với quyền tương ứng với role
```

**User Story 3: Nhân viên có localId**
```
Là nhân viên đã được gán mã VNW0014732
Tôi muốn đăng nhập bằng cả Google và GitHub
Để linh hoạt sử dụng tài khoản nào tiện hơn

Acceptance Criteria:
- Đăng nhập lần đầu bằng Google → tạo user A với localId=NULL, role='guest'
- Admin gán localId='VNW0014732' và role='employee' cho user A
- Đăng nhập lần đầu bằng GitHub → tạo user B riêng biệt với role='guest'
- Admin có thể gán cùng localId='VNW0014732' cho user B
- Cả 2 accounts độc lập nhưng đều thuộc về nhân viên VNW0014732
```

### Persona 2: Quản trị viên (Admin)

**User Story 4: Quản lý localId và roles**
```
Là admin
Tôi muốn gán mã nhân viên (localId) và thay đổi role cho users
Để quản lý quyền truy cập một cách có hệ thống

Acceptance Criteria:
- Xem danh sách users với thông tin: email, oauth_provider, current role, localId
- Có thể search/filter users theo localId, email, provider
- Gán/cập nhật localId cho user (VD: VNW0014732)
- Thay đổi role: guest → user → admin
- Xem tất cả OAuth accounts có cùng localId
```

### Pain Points được giải quyết
- ❌ User phải tạo và nhớ thêm password → ✅ Chỉ cần Google/GitHub account
- ❌ Không biết mình có quyền gì → ✅ Hiển thị rõ role và permissions
- ❌ Admin phải manually tạo account → ✅ Auto-create với role 'guest'
- ❌ Khó liên kết nhiều OAuth accounts → ✅ Dùng localId để nhận diện

## Requirements

### Functional Requirements

#### FR1: OAuth Authentication Flow
- **FR1.1:** Hỗ trợ đăng nhập qua GitHub OAuth
- **FR1.2:** Hỗ trợ đăng nhập qua Google OAuth
- **FR1.3:** OAuth callback xử lý thành công, lấy được `oauth_id` và email từ provider
- **FR1.4:** Redirect về frontend với JWT token sau khi xác thực thành công
- **FR1.5:** Xử lý error cases: OAuth denied, network errors, invalid state

#### FR2: User Check và Auto-Creation
- **FR2.1:** Khi nhận OAuth callback, kiểm tra DB xem user đã tồn tại chưa
  - Query: `SELECT * FROM users WHERE oauth_provider = ? AND oauth_id = ?`
- **FR2.2:** Nếu user chưa tồn tại:
  - Tạo user mới với thông tin từ OAuth (email, name, avatar_url)
  - Gán role mặc định = `'guest'`
  - localId = NULL
  - Lưu vào DB
- **FR2.3:** Nếu user đã tồn tại:
  - Lấy thông tin user từ DB (bao gồm role, localId)
  - Cập nhật last_login timestamp (optional)

#### FR3: JWT Token Generation
- **FR3.1:** Backend tự tạo JWT token (KHÔNG dùng OAuth token)
- **FR3.2:** JWT payload bao gồm:
  ```json
  {
    "user_id": "uuid",
    "email": "user@example.com",
    "role": "guest|user|admin",
    "localId": "VNW0014732" // nullable
    "oauth_provider": "github|google",
    "exp": timestamp,
    "iat": timestamp
  }
  ```
- **FR3.3:** Token expiration: 24 hours (configurable)
- **FR3.4:** Token signing algorithm: HS256 hoặc RS256

#### FR4: Role-Based Access Control
- **FR4.1:** Mọi protected endpoints check JWT token và role
- **FR4.2:** Roles hierarchy:
  - `guest`: Quyền đọc cơ bản, không thể modify data
  - `user`: Quyền CRUD trên tài nguyên của mình
  - `admin`: Full access
- **FR4.3:** Decorator `@require_role("user")` hoặc `@require_permission("write:users")`
- **FR4.4:** Frontend hiển thị role và permissions của user hiện tại

#### FR5: LocalId Management
- **FR5.1:** Admin có thể gán/cập nhật localId cho users
- **FR5.2:** LocalId format: alphanumeric, VD: VNW0014732, EMP001
- **FR5.3:** Nhiều users (khác oauth_provider) có thể có cùng localId
- **FR5.4:** Query users theo localId: `SELECT * FROM users WHERE localId = ?`
- **FR5.5:** Hiển thị tất cả OAuth accounts của một localId

#### FR6: Database Schema
- **FR6.1:** Bảng `users` với các cột:
  - `id` (UUID, PK)
  - `localId` (VARCHAR, nullable, indexed)
  - `oauth_provider` (VARCHAR: 'github' | 'google')
  - `oauth_id` (VARCHAR: ID từ OAuth provider)
  - `email` (VARCHAR)
  - `name` (VARCHAR)
  - `avatar_url` (VARCHAR, nullable)
  - `role` (VARCHAR, default 'guest')
  - `created_at` (TIMESTAMP)
  - `updated_at` (TIMESTAMP)
- **FR6.2:** UNIQUE constraint: `(oauth_provider, oauth_id)`
- **FR6.3:** INDEX: `localId` cho query nhanh
- **FR6.4:** Alembic migration scripts (up + down)

### Non-Functional Requirements

#### NFR1: Performance
- **NFR1.1:** Token validation < 100ms
- **NFR1.2:** OAuth callback processing < 2s (end-to-end)
- **NFR1.3:** DB query cho user lookup có index, < 50ms
- **NFR1.4:** JWT signing/verification < 10ms

#### NFR2: Security
- **NFR2.1:** HTTPS only cho tất cả OAuth redirects
- **NFR2.2:** JWT secret được lưu trong environment variables, không commit vào code
- **NFR2.3:** OAuth state parameter để prevent CSRF
- **NFR2.4:** Token stored securely (httpOnly cookies hoặc secure storage)
- **NFR2.5:** Rate limiting cho login endpoints: 10 requests/minute/IP
- **NFR2.6:** Log tất cả login attempts (success + failed)

#### NFR3: Scalability
- **NFR3.1:** Hỗ trợ PostgreSQL connection pooling
- **NFR3.2:** Stateless JWT để dễ scale horizontally
- **NFR3.3:** Cache user permissions trong token để giảm DB queries

#### NFR4: Maintainability
- **NFR4.1:** Code tuân thủ structure folder hiện tại: `app/api/routes/`, `app/core/`, `app/db/`
- **NFR4.2:** Backward compatible - không breaking changes cho users hiện tại
- **NFR4.3:** Alembic migrations phải reversible (có downgrade)
- **NFR4.4:** Comprehensive logging cho debugging
- **NFR4.5:** Unit tests coverage > 80% cho OAuth flows và role checking

#### NFR5: Usability
- **NFR5.1:** Error messages rõ ràng, hướng dẫn user cách fix
- **NFR5.2:** Hiển thị role/permissions của user ngay sau login
- **NFR5.3:** OAuth consent screen có branding của ứng dụng

## Success Criteria

### Measurable Outcomes

1. **Tỷ lệ đăng nhập thành công:**
   - Target: > 95% OAuth login attempts thành công
   - Baseline hiện tại: (cần đo)
   - Measurement: Log success/failed ratio trong 30 ngày

2. **User comprehension của roles:**
   - Target: 100% users thấy role của mình sau login
   - Measurement: Frontend hiển thị role badge/indicator
   - Survey: > 80% users hiểu quyền hạn của mình

3. **Auto role assignment:**
   - Target: 100% users mới được tự động gán role 'guest'
   - Measurement: DB query tất cả users created sau deployment
   - Verify: Không có user nào với role = NULL

4. **LocalId coverage:**
   - Target: > 70% active users được gán localId trong 3 tháng
   - Measurement: COUNT(users WHERE localId IS NOT NULL) / COUNT(users)

5. **Performance:**
   - OAuth flow completion time: < 2s (p95)
   - Token validation: < 100ms (p99)
   - Zero downtime deployment

### Key Metrics (KPIs)

- **Login Success Rate:** (Successful logins / Total login attempts) × 100
- **Average Login Time:** Time from OAuth start to token received
- **Role Distribution:** % of users in each role (guest, user, admin)
- **LocalId Adoption:** % of users with localId assigned
- **Error Rate:** OAuth errors / Total OAuth attempts
- **Token Expiry Issues:** Number of "token expired" errors per day

## Constraints & Assumptions

### Constraints

#### Timeline
- **Sprint 1-2 (2-4 tuần):** Fix OAuth bugs + cải thiện UX đăng nhập
- **Sprint 3 (1-2 tuần):** Thêm auto role checking + DB migration với Alembic
- **Sprint 4 (1 tuần):** Testing + deployment + documentation

#### Technical
- **Backend:** FastAPI (hiện tại)
- **Database:** PostgreSQL với Alembic migrations
- **Authentication:** JWT tokens, OAuth2 (GitHub, Google)
- **Backward compatibility:** Không breaking changes cho users hiện tại
- **Folder structure:** Tuân thủ quy tắc hiện tại
  - Routes: `app/api/routes/auth.py`
  - Core logic: `app/core/security.py`, `app/core/oauth.py`
  - DB models: `app/db/models/user.py`
  - Migrations: `alembic/versions/`

#### Resources
- Development team: 1-2 backend developers
- Database admin cho review migrations
- QA cho testing OAuth flows
- DevOps cho deployment

#### Data
- User table cần migration để thêm cột `localId`
- Existing users: Cần data migration script để đảm bảo tương thích
- Rollback plan nếu migration fails

### Assumptions

1. **OAuth Providers:**
   - GitHub và Google OAuth APIs stable và available
   - OAuth client credentials (client_id, client_secret) đã được setup
   - Redirect URIs đã được whitelist ở OAuth providers

2. **User Behavior:**
   - Users có Google/GitHub account hợp lệ
   - Users accept OAuth permissions khi được yêu cầu
   - Majority users chỉ dùng 1 OAuth provider (không switch thường xuyên)

3. **Infrastructure:**
   - PostgreSQL database đang chạy ổn định
   - Environment variables được manage đúng cách
   - HTTPS đã được setup cho production

4. **Business Logic:**
   - Role 'guest' là mặc định cho tất cả users mới
   - Admin sẽ manually gán localId và upgrade role
   - LocalId format do HR department định nghĩa (VNW + 7 digits)

## Out of Scope

### Những gì KHÔNG làm trong version này

1. **Passwordless login:** Không hỗ trợ magic link, OTP qua SMS/email
2. **Thêm OAuth providers khác:** Không support Facebook, Twitter, Microsoft, Apple ID
3. **Email/Password authentication:** Không làm traditional login form
4. **Multi-factor Authentication (MFA/2FA):** Không implement trong version 1
5. **Auto-link accounts:** Không tự động merge nhiều OAuth accounts của cùng 1 email
6. **Session management UI:** Không có trang để user xem/revoke active sessions
7. **OAuth token refresh:** Chỉ dùng OAuth để xác thực ban đầu, không store/refresh OAuth tokens
8. **Forgot password flow:** Không cần vì không có password
9. **User profile editing:** Chỉ làm authentication, không làm profile management
10. **Mobile app authentication:** Chỉ focus vào web application
11. **SSO/SAML integration:** Không support enterprise SSO trong version này
12. **Audit logs UI:** Có logging nhưng không có dashboard để view logs

### Có thể làm ở version sau (Future Roadmap)

- **v2.0:** Thêm MFA/2FA cho enhanced security
- **v2.0:** Auto-link accounts based on verified email
- **v3.0:** Session management và device tracking
- **v3.0:** Thêm OAuth providers (Microsoft, Apple)

## Dependencies

### External Dependencies

1. **GitHub OAuth API**
   - API endpoint: `https://github.com/login/oauth/authorize`
   - Requirements: Client ID, Client Secret, Callback URL registered
   - Risk: API downtime → Mitigation: Error handling + retry logic

2. **Google OAuth API**
   - API endpoint: `https://accounts.google.com/o/oauth2/v2/auth`
   - Requirements: Google Cloud Project, OAuth credentials
   - Risk: Rate limiting → Mitigation: Request quota monitoring

3. **PostgreSQL Database**
   - Version: >= 12
   - Requirements: Connection string, credentials
   - Risk: Migration failures → Mitigation: Test migrations on staging first

4. **Alembic**
   - Version: >= 1.8
   - Requirements: Properly configured `alembic.ini`
   - Risk: Schema conflicts → Mitigation: Review migrations carefully

### Internal Dependencies

1. **Existing User Management Routes**
   - Location: `app/api/routes/users.py`
   - Dependency: Role checking decorators cần được update
   - Owner: Backend team

2. **JWT Utilities**
   - Location: `app/core/security.py`
   - Dependency: Cần extend JWT payload để include `localId`
   - Owner: Security team

3. **RBAC System**
   - Location: `app/core/permissions.py`
   - Dependency: Roles và permissions phải được define trước
   - Owner: Backend team

4. **Frontend Auth Components**
   - Location: Frontend codebase
   - Dependency: Frontend cần update để hiển thị role/localId
   - Owner: Frontend team
   - Coordination: API contract cần được agree trước

5. **Environment Configuration**
   - File: `.env`, `settings.py`
   - Dependency: OAuth credentials, JWT secret phải được setup
   - Owner: DevOps team

### Third-Party Libraries

- **FastAPI:** Web framework
- **SQLAlchemy:** ORM for database
- **Alembic:** Database migrations
- **PyJWT:** JWT token handling
- **httpx/requests:** HTTP client cho OAuth API calls
- **python-dotenv:** Environment variables management

## Implementation Notes

### Database Migration Plan

#### Migration 1: Add localId column
```sql
-- Up migration
ALTER TABLE users ADD COLUMN localId VARCHAR(50) NULL;
CREATE INDEX idx_users_localid ON users(localId);

-- Down migration
DROP INDEX idx_users_localid;
ALTER TABLE users DROP COLUMN localId;
```

#### Migration 2: Ensure unique oauth constraint
```sql
-- Up migration
CREATE UNIQUE INDEX idx_users_oauth_unique ON users(oauth_provider, oauth_id);

-- Down migration
DROP INDEX idx_users_oauth_unique;
```

### API Endpoints Overview

```
POST   /api/auth/github/login      - Redirect to GitHub OAuth
GET    /api/auth/github/callback   - Handle GitHub callback
POST   /api/auth/google/login      - Redirect to Google OAuth
GET    /api/auth/google/callback   - Handle Google callback
POST   /api/auth/logout            - Invalidate token (optional)
GET    /api/auth/me                - Get current user info
PUT    /api/admin/users/{id}/role  - Update user role (admin only)
PUT    /api/admin/users/{id}/localId - Assign localId (admin only)
```

### Testing Strategy

1. **Unit Tests:**
   - OAuth callback handler logic
   - JWT token creation/validation
   - Role checking decorators
   - User creation logic

2. **Integration Tests:**
   - Full OAuth flow (mock GitHub/Google APIs)
   - Database operations with transactions
   - Alembic migrations (up + down)

3. **E2E Tests:**
   - Real OAuth flow on staging environment
   - Role-based access to protected routes
   - Admin localId assignment flow

## Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| OAuth API downtime | High | Low | Graceful error handling, retry logic, status page |
| Database migration failure | High | Medium | Test on staging, backup before migration, rollback plan |
| JWT secret leaked | Critical | Low | Rotate secrets regularly, use secret management service |
| Performance degradation | Medium | Medium | Load testing, database indexing, query optimization |
| User confusion about roles | Medium | High | Clear UI messaging, onboarding tooltips, help documentation |

## Approval & Sign-off

- **Product Owner:** _______________ Date: ___________
- **Tech Lead:** _______________ Date: ___________
- **Security Review:** _______________ Date: ___________

---

**Document Version:** 1.0
**Last Updated:** 2026-01-08
**Next Review:** After Sprint 1 completion
