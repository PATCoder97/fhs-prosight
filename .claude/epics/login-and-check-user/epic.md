---
name: login-and-check-user
status: backlog
created: 2026-01-08T02:18:39Z
progress: 0%
prd: .claude/prds/login-and-check-user.md
github: https://github.com/PATCoder97/fhs-prosight/issues/1
---

# Epic: Login and Check User

## Overview

Hoàn thiện hệ thống OAuth authentication hiện tại bằng cách:
1. Sửa bugs trong luồng OAuth callbacks (GitHub + Google)
2. Thêm cột `localId` vào database để quản lý mã nhân viên
3. Thay đổi default role từ `"user"` sang `"guest"` cho users mới
4. Cải thiện JWT payload để bao gồm `localId` và `oauth_provider`
5. Thêm admin endpoints để quản lý `localId` và `role`
6. Đảm bảo backward compatibility và zero-downtime deployment

**Chiến lược kỹ thuật:** Tận dụng tối đa infrastructure hiện có, chỉ bổ sung và điều chỉnh những gì cần thiết để đáp ứng requirements mới.

## Architecture Decisions

### AD1: Database Migration với Alembic
**Quyết định:** Sử dụng Alembic để thêm cột `localId` vào bảng `users` hiện tại thay vì tạo bảng mới

**Lý do:**
- Giữ schema đơn giản, tránh phức tạp hóa với foreign keys
- Backward compatible - existing users sẽ có `localId = NULL`
- Dễ rollback nếu có vấn đề

**Trade-offs:**
- ✅ Đơn giản, ít code changes
- ✅ Query nhanh (không cần JOIN)
- ❌ Có thể duplicate localId cho nhiều users (by design)

### AD2: Tái sử dụng Function `get_or_create_user()`
**Quyết định:** Cập nhật function hiện có thay vì tạo mới

**Lý do:**
- Đã có logic check user exists/create new
- Chỉ cần điều chỉnh default role và thêm localId field
- Giữ code DRY

### AD3: Mở rộng JWT Payload
**Quyết định:** Thêm fields `localId` và `oauth_provider` vào JWT token

**Lý do:**
- Frontend cần biết localId để hiển thị
- oauth_provider giúp debug và analytics
- Không làm tăng token size quá nhiều

**Implementation:**
```python
# Trong core/jwt_handler.py
payload = {
    "user_id": user_id,
    "email": email,
    "role": role,
    "localId": localId,  # NEW
    "oauth_provider": provider,  # NEW
    "exp": expiration,
    "iat": issued_at
}
```

### AD4: Admin Endpoints cho LocalId Management
**Quyết định:** Tạo protected admin routes trong `routers/users.py`

**Lý do:**
- Tách biệt admin functions khỏi auth flow
- Tận dụng RBAC decorators đã có (`@require_roles(["admin"])`)
- RESTful design

## Technical Approach

### Backend Changes

#### 1. Database Schema Update
**File:** `backend/app/models/user.py`

**Changes:**
- Thêm cột `localId` (VARCHAR, nullable, indexed)
- Thêm unique constraint cho `(provider, social_id)` nếu chưa có
- Thay đổi default value của `role` từ `"user"` → `"guest"`

**Alembic Migration:**
```python
# alembic/versions/xxxx_add_localid_and_fix_role.py
def upgrade():
    # Add localId column
    op.add_column('users', sa.Column('localId', sa.String(50), nullable=True))
    op.create_index('idx_users_localid', 'users', ['localId'])

    # Change default role for NEW users (không ảnh hưởng existing users)
    op.alter_column('users', 'role', server_default='guest')

    # Ensure unique constraint for OAuth
    op.create_unique_constraint('uq_provider_social_id', 'users', ['provider', 'social_id'])

def downgrade():
    op.drop_constraint('uq_provider_social_id', 'users')
    op.alter_column('users', 'role', server_default='user')
    op.drop_index('idx_users_localid', 'users')
    op.drop_column('users', 'localId')
```

#### 2. Auth Service Updates
**File:** `backend/app/services/auth_service.py`

**Changes trong `get_or_create_user()`:**
```python
# Thay đổi default role
new_user = User(
    social_id=social_id,
    provider=provider,
    email=email,
    full_name=full_name,
    avatar=avatar,
    role="guest",  # CHANGED từ "user"
    localId=None,   # NEW field
    is_active=True,
    is_verified=False,
)
```

**Changes trong `handle_google_callback()` và `handle_github_callback()`:**
- Truyền thêm `localId` và `provider` vào `create_access_token()`
- Return `localId` trong response

#### 3. JWT Handler Updates
**File:** `backend/app/core/jwt_handler.py`

**Changes:**
```python
def create_access_token(
    user_id: str,
    full_name: str,
    role: str,
    localId: str = None,  # NEW param
    provider: str = None,  # NEW param
    scope: str = "access",
) -> str:
    payload = {
        "user_id": user_id,
        "full_name": full_name,
        "role": role,
        "localId": localId,  # NEW
        "oauth_provider": provider,  # NEW
        "scope": scope,
        "exp": expiration_time,
        "iat": current_time,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")
```

#### 4. Admin User Management Routes
**File:** `backend/app/routers/users.py`

**New Endpoints:**
```python
@router.put("/users/{user_id}/localId")
@require_roles(["admin"])
async def assign_local_id(
    user_id: int,
    localId: str,
    current_user: dict = Depends(get_current_user)
):
    """Admin assigns localId to user"""
    # Update user.localId in DB
    # Return updated user

@router.put("/users/{user_id}/role")
@require_roles(["admin"])
async def update_user_role(
    user_id: int,
    role: str,  # "guest", "user", "admin"
    current_user: dict = Depends(get_current_user)
):
    """Admin updates user role"""
    # Validate role value
    # Update user.role in DB
    # Return updated user

@router.get("/users")
@require_roles(["admin"])
async def list_users(
    localId: Optional[str] = None,
    provider: Optional[str] = None,
    email: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Admin lists users with filters"""
    # Query users with filters
    # Return paginated list
```

#### 5. Schema Updates
**File:** `backend/app/schemas/auth.py`

**Changes:**
```python
class SocialLoginUser(BaseModel):
    id: int
    social_id: str
    provider: str
    email: str
    full_name: Optional[str]
    avatar: Optional[str]
    role: str
    localId: Optional[str] = None  # NEW field
    is_active: bool
    is_verified: bool
    is_new_user: bool = False

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: SocialLoginUser
```

### Testing Strategy

#### Unit Tests
**Files to create:**
- `tests/test_auth_service.py` - Test `get_or_create_user()` với localId
- `tests/test_jwt_handler.py` - Test JWT payload có localId
- `tests/test_migrations.py` - Test Alembic migration up/down

**Key test cases:**
1. New user → role = "guest", localId = NULL
2. Existing user → giữ nguyên role và localId
3. JWT token có đầy đủ fields: user_id, role, localId, oauth_provider
4. Admin có thể assign/update localId
5. Admin có thể change role: guest → user → admin

#### Integration Tests
**Files to create:**
- `tests/integration/test_oauth_flow.py`

**Key scenarios:**
1. Full OAuth flow (mock GitHub/Google API)
2. User đăng nhập lần đầu → tạo user mới với role="guest"
3. User đăng nhập lần 2 → nhận đúng thông tin từ DB
4. Admin assign localId → user nhận được localId trong token mới
5. Multiple users có cùng localId

#### E2E Tests (Manual on Staging)
1. Đăng nhập GitHub → verify role="guest" trong token
2. Đăng nhập Google → verify role="guest" trong token
3. Admin gán localId cho user → user re-login thấy localId mới
4. Admin thay đổi role → user re-login có quyền mới

### Performance Considerations

1. **Database Index:**
   - Index trên `localId` để query nhanh: `SELECT * FROM users WHERE localId = ?`
   - Composite unique index: `(provider, social_id)` đảm bảo không duplicate

2. **JWT Token Size:**
   - Thêm 2 fields (localId, oauth_provider) tăng ~50 bytes
   - Vẫn trong giới hạn khuyến nghị (<1KB)

3. **Query Optimization:**
   - Existing query đã optimal: `WHERE social_id = ? AND provider = ?`
   - Không cần thêm JOIN hay subquery

### Security Considerations

1. **Backward Compatibility:**
   - Existing users giữ nguyên role hiện tại (không force về "guest")
   - Migration không modify existing data, chỉ add column

2. **Admin Authorization:**
   - Tất cả admin endpoints yêu cầu `role = "admin"`
   - Validate localId format trước khi save (alphanumeric, max 50 chars)
   - Validate role value (chỉ accept: "guest", "user", "admin")

3. **Rate Limiting:**
   - Giữ nguyên rate limit cho `/auth/*/callback`: 10 req/min/IP
   - Thêm rate limit cho admin endpoints: 30 req/min/user

## Implementation Strategy

### Phase 1: Database Migration (Sprint 1 - Week 1)
**Goal:** Thêm `localId` column và fix role default

**Tasks:**
1. Tạo Alembic migration script
2. Test migration trên local dev DB
3. Test rollback (downgrade)
4. Deploy migration lên staging
5. Verify existing users không bị ảnh hưởng

**Success Criteria:**
- ✅ Migration chạy thành công trên staging
- ✅ Rollback hoạt động đúng
- ✅ Existing users vẫn login được bình thường
- ✅ Index được tạo và query performance OK

### Phase 2: Auth Flow Updates (Sprint 1 - Week 1-2)
**Goal:** Update auth service và JWT handler

**Tasks:**
1. Update User model với `localId` field
2. Modify `get_or_create_user()` để handle localId
3. Update JWT handler để include localId, provider
4. Update schemas (SocialLoginUser, LoginResponse)
5. Update OAuth callbacks (Google, GitHub)
6. Test OAuth flow end-to-end

**Success Criteria:**
- ✅ New users có role = "guest"
- ✅ JWT token chứa localId (nullable) và oauth_provider
- ✅ Existing users login vẫn nhận được token đúng
- ✅ Unit tests pass

### Phase 3: Admin User Management (Sprint 2 - Week 3)
**Goal:** Thêm admin endpoints để quản lý users

**Tasks:**
1. Tạo endpoints: PUT /users/{id}/localId, PUT /users/{id}/role, GET /users
2. Implement business logic: validate input, update DB
3. Add permission checks (@require_roles(["admin"]))
4. Write unit tests cho admin endpoints
5. Test integration với real database

**Success Criteria:**
- ✅ Admin có thể assign localId cho users
- ✅ Admin có thể change role (guest ↔ user ↔ admin)
- ✅ Non-admin users không access được endpoints
- ✅ Input validation hoạt động đúng

### Phase 4: Testing & Bug Fixes (Sprint 2 - Week 4)
**Goal:** Comprehensive testing và fix issues

**Tasks:**
1. Integration tests cho full OAuth flows
2. Manual E2E testing trên staging
3. Performance testing (JWT validation, DB queries)
4. Security audit (role checks, input validation)
5. Fix bugs phát hiện trong testing
6. Update documentation

**Success Criteria:**
- ✅ All tests pass (unit + integration)
- ✅ No breaking changes cho existing users
- ✅ Performance meets NFRs (<100ms token validation, <2s OAuth flow)
- ✅ Security audit pass

### Phase 5: Deployment (Sprint 3 - Week 5)
**Goal:** Deploy lên production

**Tasks:**
1. Final review code changes
2. Backup production database
3. Run migration trên production
4. Deploy updated backend code
5. Monitor logs và metrics
6. Smoke test critical flows
7. Rollback plan ready

**Success Criteria:**
- ✅ Zero downtime deployment
- ✅ No errors in production logs
- ✅ Login success rate > 95%
- ✅ All existing users login successfully

## Task Breakdown Preview

Dự kiến tạo **8 tasks** chính:

- [ ] **Task 1:** Tạo Alembic migration để thêm `localId` column và fix role default
- [ ] **Task 2:** Update User model và auth service cho localId support
- [ ] **Task 3:** Extend JWT handler để include localId và oauth_provider
- [ ] **Task 4:** Update OAuth callback handlers (Google + GitHub)
- [ ] **Task 5:** Thêm admin endpoints: assign localId, update role, list users
- [ ] **Task 6:** Viết unit tests cho auth flow và JWT changes
- [ ] **Task 7:** Viết integration tests và E2E test plan
- [ ] **Task 8:** Deploy migration + code lên staging, verify, deploy production

## Dependencies

### External Dependencies
1. **PostgreSQL Database** - Version >= 12, connection stable
2. **Alembic** - Version >= 1.8 for migrations
3. **GitHub OAuth API** - Existing integration, no changes needed
4. **Google OAuth API** - Existing integration, no changes needed

### Internal Dependencies
1. **Existing User model** - Will be modified to add `localId`
2. **Auth service** - Will update `get_or_create_user()` function
3. **JWT utilities** - Will extend payload structure
4. **RBAC decorators** - Will reuse for admin endpoints
5. **Database session management** - Will reuse existing AsyncSessionLocal

### Code Files to Modify
- `backend/app/models/user.py` - Add localId field
- `backend/app/services/auth_service.py` - Update get_or_create_user
- `backend/app/core/jwt_handler.py` - Extend payload
- `backend/app/schemas/auth.py` - Add localId to schemas
- `backend/app/routers/users.py` - Add admin endpoints
- `alembic/versions/xxxx_add_localid.py` - NEW migration file

### Code Files to Create
- `alembic/versions/xxxx_add_localid_and_fix_role.py` - Migration script
- `tests/test_auth_localid.py` - Unit tests
- `tests/integration/test_oauth_with_localid.py` - Integration tests

## Success Criteria (Technical)

### Performance Benchmarks
1. **OAuth Callback Processing:** < 2s end-to-end (p95)
   - Measurement: Log timestamp từ callback start → JWT return

2. **JWT Token Validation:** < 100ms (p99)
   - Measurement: Time to verify + decode token

3. **Database Query (user lookup):** < 50ms (p95)
   - Measurement: `SELECT * FROM users WHERE provider = ? AND social_id = ?`

4. **Admin Endpoints:** < 200ms (p95)
   - Measurement: Time to update localId/role

### Quality Gates
1. **Unit Test Coverage:** > 80% cho auth-related code
2. **Integration Tests:** All critical flows pass
3. **Migration Success:** 100% success rate trên staging + production
4. **Zero Breaking Changes:** Existing users login successfully
5. **Backward Compatibility:** Old JWT tokens (without localId) vẫn valid cho đến khi expire

### Acceptance Criteria
1. ✅ User đăng nhập lần đầu → role = "guest", localId = NULL
2. ✅ User đăng nhập lần 2+ → nhận đúng role và localId từ DB
3. ✅ JWT token có fields: user_id, role, localId, oauth_provider, exp, iat
4. ✅ Admin assign localId → user nhận được trong token tiếp theo
5. ✅ Admin change role → user permissions update accordingly
6. ✅ Multiple users có thể có cùng localId (different oauth_provider)
7. ✅ Database có index trên localId, query performance tốt
8. ✅ Migration có downgrade script, tested successfully

## Estimated Effort

### Overall Timeline
- **Sprint 1 (Weeks 1-2):** Database migration + Auth flow updates
- **Sprint 2 (Weeks 3-4):** Admin endpoints + Testing
- **Sprint 3 (Week 5):** Deployment + Monitoring

**Total:** ~3-4 tuần (với 1-2 developers)

### Resource Requirements
- **Backend Developer:** 1-2 người (full-time)
- **Database Admin:** Review migration scripts (2-3 hours)
- **QA Engineer:** Testing auth flows (1 week part-time)
- **DevOps:** Deployment support (1 day)

### Critical Path Items
1. **Database Migration** - Phải hoàn thành trước khi deploy code changes
2. **JWT Payload Update** - Breaking change nếu không handle backward compatibility
3. **Testing on Staging** - Phải verify thoroughly trước production
4. **Backup & Rollback Plan** - Ready trước khi deploy production

### Risk Buffer
- Thêm 20% buffer cho unexpected bugs
- Thêm 1 week cho bug fixes sau production deployment
- Keep rollback plan ready trong 2 tuần đầu sau deploy

## Notes

### Cải tiến so với thiết kế ban đầu
Thiết kế này đơn giản hóa implementation bằng cách:
1. **Tái sử dụng tối đa code hiện có** - Không tạo services/utilities mới không cần thiết
2. **Minimize database changes** - Chỉ add 1 column, không restructure
3. **Leverage existing RBAC** - Dùng decorators có sẵn cho admin endpoints
4. **Backward compatible** - Không breaking changes, old tokens vẫn hoạt động

### Những gì không làm (Out of Scope)
- ❌ Không tạo bảng riêng cho LocalId/Employee
- ❌ Không auto-link accounts based on email
- ❌ Không làm frontend UI (chỉ API)
- ❌ Không thêm MFA/2FA
- ❌ Không implement session management UI

### Future Enhancements
- **v2.0:** Auto-link multiple OAuth accounts của cùng email
- **v2.0:** Frontend admin dashboard để quản lý users
- **v3.0:** Audit logs cho admin actions
- **v3.0:** Bulk import localId từ CSV/HR system

## Tasks Created
- [ ] #2 - Tạo Alembic migration để thêm localId và fix role default (parallel: true, depends: [], ~?h)
- [ ] #3 - Update User model và auth service cho localId support (parallel: false, depends: [2], ~?h)
- [ ] #4 - Extend JWT handler để include localId và oauth_provider (parallel: false, depends: [3], ~?h)
- [ ] #5 - Update OAuth callback handlers (Google + GitHub) (parallel: false, depends: [3, 4], ~?h)
- [ ] #6 - Thêm admin endpoints - assign localId, update role, list users (parallel: true, depends: [5], ~?h)
- [ ] #7 - Viết unit tests cho auth flow và JWT changes (parallel: true, depends: [6], ~?h)
- [ ] #8 - Viết integration tests và E2E test plan (parallel: true, depends: [7], ~?h)
- [ ] #9 - Deploy migration + code lên staging, verify, deploy production (parallel: false, depends: [8], ~?h)

**Total tasks:** 8
**Parallel tasks:** 4 (2, 6, 7, 8)
**Sequential tasks:** 4 (3, 4, 5, 9)
**Estimated total effort:** 28-37 hours (~3.5-5 days với 1 developer, hoặc 2-3 weeks với testing và review)

**Critical Path:** #2 → #3 → #4 → #5 → #6 → #7 → #8 → #9

**Parallelization opportunities:**
- Tasks #6, #7, #8 có thể chạy song song sau khi #5 hoàn thành
- Task #2 có thể bắt đầu ngay lập tức
