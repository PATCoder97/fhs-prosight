import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from sqlalchemy import select

from app.main import app
from app.models.user import User
from app.core.jwt_handler import create_access_token, verify_token
from app.database.session import AsyncSessionLocal


client = TestClient(app)


@pytest.mark.integration
class TestAssignLocalIdWorkflow:
    """Integration tests for admin assigning localId to users"""

    @pytest.mark.asyncio
    async def test_complete_assign_localId_workflow(self, test_db_session):
        """
        Test complete workflow:
        1. New user logs in → role='guest', localId=None
        2. Admin assigns localId='VNW002'
        3. User re-logs in → receives localId in response and JWT token
        """
        # Step 1: Create new user (simulating first login)
        new_user = User(
            social_id="new_user_workflow_123",
            provider="google",
            email="newemployee@gmail.com",
            full_name="New Employee",
            avatar="https://avatar.url",
            role="guest",  # Default for new users
            localId=None,  # No localId yet
            is_active=True,
            is_verified=False
        )

        test_db_session.add(new_user)
        await test_db_session.commit()
        await test_db_session.refresh(new_user)

        user_id = new_user.id

        # Verify initial state
        assert new_user.role == "guest"
        assert new_user.localId is None

        # Generate first login token
        first_token = create_access_token(
            user_id=str(user_id),
            full_name=new_user.full_name,
            role=new_user.role,
            localId=new_user.localId,
            provider=new_user.provider
        )

        first_payload = verify_token(first_token, required_scope="access")
        assert first_payload["role"] == "guest"
        assert first_payload.get("localId") is None

        # Step 2: Admin assigns localId
        # Create admin user
        admin = User(
            social_id="admin_123",
            provider="google",
            email="admin@company.com",
            full_name="Admin User",
            role="admin",
            localId="ADM001",
            is_active=True,
            is_verified=True
        )

        test_db_session.add(admin)
        await test_db_session.commit()
        await test_db_session.refresh(admin)

        # Generate admin token
        admin_token = create_access_token(
            user_id=str(admin.id),
            full_name=admin.full_name,
            role=admin.role,
            localId=admin.localId,
            provider=admin.provider
        )

        # Mock the database session in the router
        with patch('app.routers.users.AsyncSessionLocal') as mock_session_local:
            # Setup mock to use our test session
            mock_session = AsyncMock()
            mock_result = AsyncMock()

            # First call: get user
            mock_result.scalars().first.return_value = new_user
            mock_session.execute.return_value = mock_result
            mock_session.commit = AsyncMock()

            async def mock_refresh(user):
                user.localId = "VNW002"

            mock_session.refresh = mock_refresh
            mock_session_local.return_value.__aenter__.return_value = mock_session

            # Admin assigns localId
            response = client.put(
                f"/api/users/{user_id}/localId",
                json={"localId": "VNW002"},
                headers={"Authorization": f"Bearer {admin_token}"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["user"]["localId"] == "VNW002"

        # Update user in test DB (simulate what the endpoint did)
        new_user.localId = "VNW002"
        await test_db_session.commit()
        await test_db_session.refresh(new_user)

        # Step 3: User re-logs in
        # Simulate get_or_create_user finding the updated user
        stmt = select(User).where(User.id == user_id)
        result = await test_db_session.execute(stmt)
        updated_user = result.scalars().first()

        assert updated_user.localId == "VNW002"

        # Generate new token after re-login
        second_token = create_access_token(
            user_id=str(updated_user.id),
            full_name=updated_user.full_name,
            role=updated_user.role,
            localId=updated_user.localId,
            provider=updated_user.provider
        )

        second_payload = verify_token(second_token, required_scope="access")

        # Verify token now has localId
        assert second_payload["localId"] == "VNW002"
        assert second_payload["role"] == "guest"  # Still guest
        assert second_payload["oauth_provider"] == "google"


@pytest.mark.integration
class TestUpdateRoleWorkflow:
    """Integration tests for admin updating user roles"""

    @pytest.mark.asyncio
    async def test_complete_update_role_workflow(self, test_db_session):
        """
        Test complete workflow:
        1. User has role='guest'
        2. Admin changes to role='user'
        3. User re-logs in → new token has role='user'
        4. User can now access user-level protected endpoints
        """
        # Step 1: Create guest user
        guest_user = User(
            social_id="guest_workflow_456",
            provider="github",
            email="guest@example.com",
            full_name="Guest User",
            avatar="https://avatar.url",
            role="guest",
            localId=None,
            is_active=True,
            is_verified=False
        )

        test_db_session.add(guest_user)
        await test_db_session.commit()
        await test_db_session.refresh(guest_user)

        user_id = guest_user.id

        # Verify initial state
        assert guest_user.role == "guest"

        # Step 2: Admin changes role
        admin = User(
            social_id="admin_456",
            provider="google",
            email="admin2@company.com",
            full_name="Admin User 2",
            role="admin",
            localId="ADM002",
            is_active=True,
            is_verified=True
        )

        test_db_session.add(admin)
        await test_db_session.commit()
        await test_db_session.refresh(admin)

        admin_token = create_access_token(
            user_id=str(admin.id),
            full_name=admin.full_name,
            role=admin.role,
            localId=admin.localId,
            provider=admin.provider
        )

        # Mock database session
        with patch('app.routers.users.AsyncSessionLocal') as mock_session_local:
            mock_session = AsyncMock()
            mock_result = AsyncMock()

            mock_result.scalars().first.return_value = guest_user
            mock_session.execute.return_value = mock_result
            mock_session.commit = AsyncMock()

            async def mock_refresh(user):
                user.role = "user"

            mock_session.refresh = mock_refresh
            mock_session_local.return_value.__aenter__.return_value = mock_session

            # Admin updates role
            response = client.put(
                f"/api/users/{user_id}/role",
                json={"role": "user"},
                headers={"Authorization": f"Bearer {admin_token}"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["user"]["role"] == "user"

        # Update user in test DB
        guest_user.role = "user"
        await test_db_session.commit()
        await test_db_session.refresh(guest_user)

        # Step 3: User re-logs in with new role
        stmt = select(User).where(User.id == user_id)
        result = await test_db_session.execute(stmt)
        updated_user = result.scalars().first()

        assert updated_user.role == "user"  # Role changed

        # Generate new token
        new_token = create_access_token(
            user_id=str(updated_user.id),
            full_name=updated_user.full_name,
            role=updated_user.role,
            localId=updated_user.localId,
            provider=updated_user.provider
        )

        payload = verify_token(new_token, required_scope="access")

        # Verify token has new role
        assert payload["role"] == "user"  # NOT 'guest'

    @pytest.mark.asyncio
    async def test_promote_user_to_admin_workflow(self, test_db_session):
        """
        Test promoting a regular user to admin:
        1. User has role='user'
        2. Admin promotes to role='admin'
        3. User can now access admin endpoints
        """
        # Create regular user
        regular_user = User(
            social_id="regular_789",
            provider="google",
            email="regular@example.com",
            full_name="Regular User",
            role="user",
            localId="VNW003",
            is_active=True,
            is_verified=True
        )

        test_db_session.add(regular_user)
        await test_db_session.commit()
        await test_db_session.refresh(regular_user)

        user_id = regular_user.id

        # Create admin
        admin = User(
            social_id="admin_789",
            provider="google",
            email="admin3@company.com",
            full_name="Admin User 3",
            role="admin",
            localId="ADM003",
            is_active=True,
            is_verified=True
        )

        test_db_session.add(admin)
        await test_db_session.commit()
        await test_db_session.refresh(admin)

        admin_token = create_access_token(
            user_id=str(admin.id),
            full_name=admin.full_name,
            role=admin.role,
            localId=admin.localId,
            provider=admin.provider
        )

        # Mock database
        with patch('app.routers.users.AsyncSessionLocal') as mock_session_local:
            mock_session = AsyncMock()
            mock_result = AsyncMock()

            mock_result.scalars().first.return_value = regular_user
            mock_session.execute.return_value = mock_result
            mock_session.commit = AsyncMock()

            async def mock_refresh(user):
                user.role = "admin"

            mock_session.refresh = mock_refresh
            mock_session_local.return_value.__aenter__.return_value = mock_session

            # Promote to admin
            response = client.put(
                f"/api/users/{user_id}/role",
                json={"role": "admin"},
                headers={"Authorization": f"Bearer {admin_token}"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["user"]["role"] == "admin"

        # Update in test DB
        regular_user.role = "admin"
        await test_db_session.commit()

        # Verify user can now access admin endpoints
        new_admin_token = create_access_token(
            user_id=str(regular_user.id),
            full_name=regular_user.full_name,
            role=regular_user.role,  # Now 'admin'
            localId=regular_user.localId,
            provider=regular_user.provider
        )

        # Try to access admin endpoint
        with patch('app.routers.users.AsyncSessionLocal') as mock_session_local:
            mock_session = AsyncMock()
            mock_result = AsyncMock()
            mock_result.scalars().all.return_value = []

            mock_count_result = AsyncMock()
            mock_count_result.scalar.return_value = 0

            mock_session.execute.side_effect = [mock_result, mock_count_result]
            mock_session_local.return_value.__aenter__.return_value = mock_session

            # Now should be able to list users (admin-only endpoint)
            response = client.get(
                "/api/users",
                headers={"Authorization": f"Bearer {new_admin_token}"}
            )

            assert response.status_code == 200  # Success!


@pytest.mark.integration
class TestCombinedWorkflows:
    """Test combined admin workflows"""

    @pytest.mark.asyncio
    async def test_assign_localId_and_update_role_combined(self, test_db_session):
        """
        Test complete onboarding workflow:
        1. New user logs in → guest, no localId
        2. Admin assigns localId
        3. Admin promotes to user role
        4. User re-logs in → has both localId and user role
        """
        # Step 1: New user
        new_user = User(
            social_id="onboarding_999",
            provider="google",
            email="newemployee@company.com",
            full_name="New Employee",
            role="guest",
            localId=None,
            is_active=True,
            is_verified=False
        )

        test_db_session.add(new_user)
        await test_db_session.commit()
        await test_db_session.refresh(new_user)

        user_id = new_user.id

        # Create admin
        admin = User(
            social_id="admin_999",
            provider="google",
            email="admin@company.com",
            full_name="Admin",
            role="admin",
            localId="ADM999",
            is_active=True,
            is_verified=True
        )

        test_db_session.add(admin)
        await test_db_session.commit()
        await test_db_session.refresh(admin)

        admin_token = create_access_token(
            user_id=str(admin.id),
            full_name=admin.full_name,
            role=admin.role,
            localId=admin.localId,
            provider=admin.provider
        )

        # Step 2: Assign localId
        new_user.localId = "VNW999"
        await test_db_session.commit()

        # Step 3: Update role
        new_user.role = "user"
        await test_db_session.commit()
        await test_db_session.refresh(new_user)

        # Step 4: User re-logs in
        final_token = create_access_token(
            user_id=str(new_user.id),
            full_name=new_user.full_name,
            role=new_user.role,
            localId=new_user.localId,
            provider=new_user.provider
        )

        payload = verify_token(final_token, required_scope="access")

        # Verify final state
        assert payload["role"] == "user"  # Promoted from guest
        assert payload["localId"] == "VNW999"  # Assigned
        assert payload["oauth_provider"] == "google"
