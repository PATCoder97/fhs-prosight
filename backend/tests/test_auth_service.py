import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime

from app.services.auth_service import get_or_create_user
from app.models.user import User


class TestGetOrCreateUser:
    """Test get_or_create_user function"""

    @pytest.mark.asyncio
    async def test_create_new_user_with_default_values(self):
        """Test creating new user returns role='guest' and localId=None"""
        # Mock database session
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars().first.return_value = None  # User doesn't exist

        # Create a mock user that will be returned after db.add()
        mock_new_user = User(
            id=1,
            social_id="new_123",
            provider="google",
            email="newuser@example.com",
            full_name="New User",
            avatar="https://avatar.url",
            role="guest",
            localId=None,
            is_active=True,
            is_verified=False,
            created_at=datetime.utcnow()
        )

        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock(side_effect=lambda user: setattr(user, 'id', 1))

        # Patch AsyncSessionLocal to return our mock
        with patch('app.services.auth_service.AsyncSessionLocal') as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session

            # Mock the refresh to populate the user object
            async def mock_refresh(user):
                user.id = 1

            mock_session.refresh = mock_refresh

            user_data = await get_or_create_user(
                social_id="new_123",
                provider="google",
                email="newuser@example.com",
                full_name="New User",
                avatar="https://avatar.url"
            )

            # Verify new user has correct defaults
            assert user_data["social_id"] == "new_123"
            assert user_data["provider"] == "google"
            assert user_data["email"] == "newuser@example.com"
            assert user_data["role"] == "guest"  # Default role
            assert user_data["localId"] is None  # Default localId
            assert user_data["is_active"] is True
            assert user_data["is_verified"] is False

            # Verify database operations were called
            mock_session.execute.assert_called_once()
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_existing_user_preserves_role_and_localId(self):
        """Test retrieving existing user preserves their role and localId"""
        # Create existing user with specific role and localId
        existing_user = User(
            id=42,
            social_id="existing_456",
            provider="github",
            email="existing@example.com",
            full_name="Existing User",
            avatar="https://avatar2.url",
            role="user",  # NOT guest
            localId="VNW001",  # Has localId
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )

        # Mock database session
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars().first.return_value = existing_user

        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        with patch('app.services.auth_service.AsyncSessionLocal') as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session

            user_data = await get_or_create_user(
                social_id="existing_456",
                provider="github",
                email="existing@example.com",
                full_name="Existing User",
                avatar="https://avatar2.url"
            )

            # Verify existing data is preserved
            assert user_data["id"] == 42
            assert user_data["role"] == "user"  # Preserved, not 'guest'
            assert user_data["localId"] == "VNW001"  # Preserved
            assert user_data["is_verified"] is True  # Preserved

            # Verify last_login was updated
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_existing_user_without_localId(self):
        """Test existing user without localId returns localId=None"""
        existing_user = User(
            id=99,
            social_id="user_789",
            provider="google",
            email="user@example.com",
            full_name="User Without LocalId",
            avatar="https://avatar3.url",
            role="user",
            localId=None,  # No localId assigned yet
            is_active=True,
            is_verified=False,
            created_at=datetime.utcnow()
        )

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars().first.return_value = existing_user

        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        with patch('app.services.auth_service.AsyncSessionLocal') as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session

            user_data = await get_or_create_user(
                social_id="user_789",
                provider="google",
                email="user@example.com",
                full_name="User Without LocalId",
                avatar="https://avatar3.url"
            )

            assert user_data["localId"] is None
            assert user_data["role"] == "user"  # Existing role

    @pytest.mark.asyncio
    async def test_database_error_returns_fallback_user(self):
        """Test database connection error returns fallback user with id=0"""
        # Mock database to raise exception
        with patch('app.services.auth_service.AsyncSessionLocal') as mock_session_local:
            mock_session_local.side_effect = Exception("Database connection failed")

            user_data = await get_or_create_user(
                social_id="fallback_123",
                provider="google",
                email="fallback@example.com",
                full_name="Fallback User",
                avatar="https://avatar.url"
            )

            # Verify fallback user is returned
            assert user_data["id"] == 0  # Temporary ID
            assert user_data["social_id"] == "fallback_123"
            assert user_data["role"] == "guest"
            assert user_data["localId"] is None
            assert user_data["is_active"] is True

    @pytest.mark.asyncio
    async def test_update_last_login_for_existing_user(self):
        """Test that last_login timestamp is updated when user logs in"""
        old_login_time = datetime(2026, 1, 1, 0, 0, 0)
        existing_user = User(
            id=1,
            social_id="user_123",
            provider="google",
            email="user@example.com",
            full_name="User",
            avatar="https://avatar.url",
            role="user",
            localId="VNW001",
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow(),
            last_login=old_login_time
        )

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars().first.return_value = existing_user

        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        with patch('app.services.auth_service.AsyncSessionLocal') as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session

            before_call = datetime.utcnow()
            user_data = await get_or_create_user(
                social_id="user_123",
                provider="google",
                email="user@example.com",
                full_name="User",
                avatar="https://avatar.url"
            )

            # Verify last_login was updated to recent time
            assert existing_user.last_login >= before_call
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_with_different_providers(self):
        """Test creating users with different OAuth providers"""
        for provider in ["google", "github"]:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars().first.return_value = None  # New user

            mock_session.execute.return_value = mock_result
            mock_session.commit = AsyncMock()
            mock_session.refresh = AsyncMock()

            with patch('app.services.auth_service.AsyncSessionLocal') as mock_session_local:
                mock_session_local.return_value.__aenter__.return_value = mock_session

                user_data = await get_or_create_user(
                    social_id=f"{provider}_123",
                    provider=provider,
                    email=f"user@{provider}.com",
                    full_name=f"{provider.title()} User",
                    avatar=f"https://{provider}.com/avatar.jpg"
                )

                assert user_data["provider"] == provider
                assert user_data["role"] == "guest"
                assert user_data["localId"] is None
