import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from sqlalchemy import select, func

from app.main import app
from app.models.user import User
from app.core.jwt_handler import create_access_token


client = TestClient(app)


class TestAssignLocalIdEndpoint:
    """Test PUT /api/users/{user_id}/localId endpoint"""

    def test_assign_localId_as_admin_success(self):
        """Test admin can successfully assign localId to a user"""
        # Create admin token
        admin_token = create_access_token(
            user_id="1",
            full_name="Admin User",
            role="admin",
            localId="ADM001",
            provider="google"
        )

        # Mock database
        mock_user = User(
            id=42,
            social_id="user_123",
            provider="google",
            email="user@example.com",
            full_name="Test User",
            role="user",
            localId=None,
            is_active=True,
            is_verified=False
        )

        with patch('app.routers.users.AsyncSessionLocal') as mock_session_local:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars().first.return_value = mock_user

            mock_session.execute.return_value = mock_result
            mock_session.commit = AsyncMock()
            mock_session.refresh = AsyncMock(side_effect=lambda u: setattr(u, 'localId', 'VNW001'))

            mock_session_local.return_value.__aenter__.return_value = mock_session

            response = client.put(
                "/api/users/42/localId",
                json={"localId": "VNW001"},
                headers={"Authorization": f"Bearer {admin_token}"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "assigned" in data["message"].lower()
            assert data["user"]["id"] == 42
            # Note: Mock refresh updated localId
            assert data["user"]["localId"] == "VNW001"

    def test_assign_localId_as_non_admin_forbidden(self):
        """Test non-admin user cannot assign localId (403 Forbidden)"""
        # Create regular user token
        user_token = create_access_token(
            user_id="2",
            full_name="Regular User",
            role="user",
            localId="VNW002",
            provider="google"
        )

        response = client.put(
            "/api/users/42/localId",
            json={"localId": "VNW001"},
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 403
        assert "admin" in response.json()["detail"].lower()

    def test_assign_localId_guest_user_forbidden(self):
        """Test guest user cannot assign localId"""
        guest_token = create_access_token(
            user_id="3",
            full_name="Guest User",
            role="guest",
            localId=None,
            provider="github"
        )

        response = client.put(
            "/api/users/42/localId",
            json={"localId": "VNW001"},
            headers={"Authorization": f"Bearer {guest_token}"}
        )

        assert response.status_code == 403

    def test_assign_localId_user_not_found(self):
        """Test assigning localId to non-existent user returns 404"""
        admin_token = create_access_token(
            user_id="1",
            full_name="Admin",
            role="admin"
        )

        with patch('app.routers.users.AsyncSessionLocal') as mock_session_local:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars().first.return_value = None  # User not found

            mock_session.execute.return_value = mock_result
            mock_session_local.return_value.__aenter__.return_value = mock_session

            response = client.put(
                "/api/users/999/localId",
                json={"localId": "VNW001"},
                headers={"Authorization": f"Bearer {admin_token}"}
            )

            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()

    def test_assign_localId_invalid_format(self):
        """Test assigning localId with invalid characters returns 422"""
        admin_token = create_access_token(
            user_id="1",
            full_name="Admin",
            role="admin"
        )

        # localId with special characters (invalid)
        response = client.put(
            "/api/users/42/localId",
            json={"localId": "VNW-001!@#"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 422  # Validation error

    def test_assign_localId_too_long(self):
        """Test assigning localId longer than 50 chars returns 422"""
        admin_token = create_access_token(
            user_id="1",
            full_name="Admin",
            role="admin"
        )

        response = client.put(
            "/api/users/42/localId",
            json={"localId": "A" * 51},  # 51 characters
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 422

    def test_assign_localId_without_auth(self):
        """Test endpoint without auth token returns 403"""
        response = client.put(
            "/api/users/42/localId",
            json={"localId": "VNW001"}
        )

        assert response.status_code == 403


class TestUpdateRoleEndpoint:
    """Test PUT /api/users/{user_id}/role endpoint"""

    def test_update_role_as_admin_success(self):
        """Test admin can update user role"""
        admin_token = create_access_token(
            user_id="1",
            full_name="Admin",
            role="admin"
        )

        mock_user = User(
            id=42,
            social_id="user_123",
            provider="google",
            email="user@example.com",
            full_name="Test User",
            role="guest",
            localId=None,
            is_active=True,
            is_verified=False
        )

        with patch('app.routers.users.AsyncSessionLocal') as mock_session_local:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars().first.return_value = mock_user

            mock_session.execute.return_value = mock_result
            mock_session.commit = AsyncMock()
            mock_session.refresh = AsyncMock(side_effect=lambda u: setattr(u, 'role', 'user'))

            mock_session_local.return_value.__aenter__.return_value = mock_session

            response = client.put(
                "/api/users/42/role",
                json={"role": "user"},
                headers={"Authorization": f"Bearer {admin_token}"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "updated" in data["message"].lower()
            assert data["user"]["role"] == "user"

    def test_update_role_invalid_value(self):
        """Test updating role with invalid value returns 422"""
        admin_token = create_access_token(
            user_id="1",
            full_name="Admin",
            role="admin"
        )

        response = client.put(
            "/api/users/42/role",
            json={"role": "superadmin"},  # Invalid role
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 422  # Validation error

    def test_update_role_allowed_values(self):
        """Test only guest, user, admin roles are accepted"""
        admin_token = create_access_token(
            user_id="1",
            full_name="Admin",
            role="admin"
        )

        allowed_roles = ["guest", "user", "admin"]

        for role in allowed_roles:
            mock_user = User(
                id=42,
                social_id="user_123",
                provider="google",
                email="user@example.com",
                full_name="Test User",
                role="guest",
                is_active=True,
                is_verified=False
            )

            with patch('app.routers.users.AsyncSessionLocal') as mock_session_local:
                mock_session = AsyncMock()
                mock_result = MagicMock()
                mock_result.scalars().first.return_value = mock_user

                mock_session.execute.return_value = mock_result
                mock_session.commit = AsyncMock()
                mock_session.refresh = AsyncMock()

                mock_session_local.return_value.__aenter__.return_value = mock_session

                response = client.put(
                    "/api/users/42/role",
                    json={"role": role},
                    headers={"Authorization": f"Bearer {admin_token}"}
                )

                assert response.status_code == 200

    def test_prevent_self_demotion(self):
        """Test admin cannot demote themselves from admin role"""
        admin_token = create_access_token(
            user_id="1",
            full_name="Admin",
            role="admin"
        )

        # Mock admin trying to demote themselves
        admin_user = User(
            id=1,  # Same ID as token
            social_id="admin_123",
            provider="google",
            email="admin@example.com",
            full_name="Admin",
            role="admin",
            localId="ADM001",
            is_active=True,
            is_verified=True
        )

        with patch('app.routers.users.AsyncSessionLocal') as mock_session_local:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars().first.return_value = admin_user

            mock_session.execute.return_value = mock_result
            mock_session_local.return_value.__aenter__.return_value = mock_session

            response = client.put(
                "/api/users/1/role",
                json={"role": "user"},  # Trying to demote
                headers={"Authorization": f"Bearer {admin_token}"}
            )

            assert response.status_code == 400
            assert "demote" in response.json()["detail"].lower()

    def test_update_role_as_non_admin_forbidden(self):
        """Test non-admin cannot update roles"""
        user_token = create_access_token(
            user_id="2",
            full_name="User",
            role="user"
        )

        response = client.put(
            "/api/users/42/role",
            json={"role": "admin"},
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 403


class TestListUsersEndpoint:
    """Test GET /api/users endpoint"""

    def test_list_users_as_admin(self):
        """Test admin can list all users"""
        admin_token = create_access_token(
            user_id="1",
            full_name="Admin",
            role="admin"
        )

        mock_users = [
            User(id=1, social_id="1", provider="google", email="user1@example.com",
                 full_name="User 1", role="user", localId="VNW001", is_active=True, is_verified=False),
            User(id=2, social_id="2", provider="github", email="user2@example.com",
                 full_name="User 2", role="guest", localId=None, is_active=True, is_verified=False),
        ]

        with patch('app.routers.users.AsyncSessionLocal') as mock_session_local:
            mock_session = AsyncMock()

            # Mock users query
            mock_result = MagicMock()
            mock_result.scalars().all.return_value = mock_users

            # Mock count query
            mock_count_result = MagicMock()
            mock_count_result.scalar.return_value = 2

            mock_session.execute.side_effect = [mock_result, mock_count_result]
            mock_session_local.return_value.__aenter__.return_value = mock_session

            response = client.get(
                "/api/users",
                headers={"Authorization": f"Bearer {admin_token}"}
            )

            assert response.status_code == 200
            data = response.json()
            assert "users" in data
            assert "total" in data
            assert data["total"] == 2
            assert len(data["users"]) == 2

    def test_list_users_as_non_admin_forbidden(self):
        """Test non-admin cannot list users"""
        user_token = create_access_token(
            user_id="2",
            full_name="User",
            role="user"
        )

        response = client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 403

    def test_list_users_with_localId_filter(self):
        """Test filtering users by localId"""
        admin_token = create_access_token(
            user_id="1",
            full_name="Admin",
            role="admin"
        )

        mock_users = [
            User(id=1, social_id="1", provider="google", email="user1@example.com",
                 full_name="User 1", role="user", localId="VNW001", is_active=True, is_verified=False),
        ]

        with patch('app.routers.users.AsyncSessionLocal') as mock_session_local:
            mock_session = AsyncMock()

            mock_result = MagicMock()
            mock_result.scalars().all.return_value = mock_users

            mock_count_result = MagicMock()
            mock_count_result.scalar.return_value = 1

            mock_session.execute.side_effect = [mock_result, mock_count_result]
            mock_session_local.return_value.__aenter__.return_value = mock_session

            response = client.get(
                "/api/users?localId=VNW001",
                headers={"Authorization": f"Bearer {admin_token}"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 1

    def test_list_users_with_pagination(self):
        """Test pagination with limit and offset"""
        admin_token = create_access_token(
            user_id="1",
            full_name="Admin",
            role="admin"
        )

        with patch('app.routers.users.AsyncSessionLocal') as mock_session_local:
            mock_session = AsyncMock()

            mock_result = MagicMock()
            mock_result.scalars().all.return_value = []

            mock_count_result = MagicMock()
            mock_count_result.scalar.return_value = 100

            mock_session.execute.side_effect = [mock_result, mock_count_result]
            mock_session_local.return_value.__aenter__.return_value = mock_session

            response = client.get(
                "/api/users?limit=10&offset=20",
                headers={"Authorization": f"Bearer {admin_token}"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["limit"] == 10
            assert data["offset"] == 20
            assert data["total"] == 100

    def test_list_users_with_provider_filter(self):
        """Test filtering users by OAuth provider"""
        admin_token = create_access_token(
            user_id="1",
            full_name="Admin",
            role="admin"
        )

        with patch('app.routers.users.AsyncSessionLocal') as mock_session_local:
            mock_session = AsyncMock()

            mock_result = MagicMock()
            mock_result.scalars().all.return_value = []

            mock_count_result = MagicMock()
            mock_count_result.scalar.return_value = 0

            mock_session.execute.side_effect = [mock_result, mock_count_result]
            mock_session_local.return_value.__aenter__.return_value = mock_session

            response = client.get(
                "/api/users?provider=github",
                headers={"Authorization": f"Bearer {admin_token}"}
            )

            assert response.status_code == 200

    def test_list_users_with_email_filter(self):
        """Test filtering users by email (partial match)"""
        admin_token = create_access_token(
            user_id="1",
            full_name="Admin",
            role="admin"
        )

        with patch('app.routers.users.AsyncSessionLocal') as mock_session_local:
            mock_session = AsyncMock()

            mock_result = MagicMock()
            mock_result.scalars().all.return_value = []

            mock_count_result = MagicMock()
            mock_count_result.scalar.return_value = 0

            mock_session.execute.side_effect = [mock_result, mock_count_result]
            mock_session_local.return_value.__aenter__.return_value = mock_session

            response = client.get(
                "/api/users?email=example.com",
                headers={"Authorization": f"Bearer {admin_token}"}
            )

            assert response.status_code == 200
