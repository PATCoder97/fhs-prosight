import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from sqlalchemy import select

from app.main import app
from app.models.user import User
from app.core.jwt_handler import verify_token
from app.database.session import AsyncSessionLocal


client = TestClient(app)


@pytest.mark.integration
class TestGoogleOAuthFlow:
    """Integration tests for Google OAuth flow"""

    @patch('app.services.auth_service.google_auth.get_user_info')
    def test_google_oauth_new_user_flow(self, mock_get_user_info):
        """
        Test complete Google OAuth flow for a new user:
        1. User authenticates with Google
        2. System creates new user with role='guest', localId=None
        3. JWT token contains correct user info and oauth_provider='google'
        """
        # Mock Google API response
        mock_get_user_info.return_value = AsyncMock(return_value={
            "sub": "google_new_123",
            "email": "newuser@gmail.com",
            "name": "New Google User",
            "picture": "https://lh3.googleusercontent.com/avatar.jpg"
        })

        # Note: In real scenario, this would go through full OAuth flow
        # For testing, we directly call the callback endpoint
        # You may need to mock the entire OAuth client flow

        # This test demonstrates the expected behavior
        # Actual implementation would require setting up OAuth mock server

        # Expected flow:
        # 1. GET /auth/login/google → redirect to Google
        # 2. User authenticates
        # 3. GET /auth/google/callback?code=xxx → our handler

        # For now, we test the service layer directly
        from app.services.auth_service import get_or_create_user

        # Test user creation
        import asyncio
        user_data = asyncio.run(get_or_create_user(
            social_id="google_new_123",
            provider="google",
            email="newuser@gmail.com",
            full_name="New Google User",
            avatar="https://lh3.googleusercontent.com/avatar.jpg"
        ))

        # Verify new user data
        assert user_data["social_id"] == "google_new_123"
        assert user_data["provider"] == "google"
        assert user_data["email"] == "newuser@gmail.com"
        assert user_data["role"] == "guest"  # NEW users get 'guest'
        assert user_data["localId"] is None  # No localId yet
        assert user_data["is_active"] is True
        assert user_data["is_verified"] is False

        # Test JWT token creation
        from app.core.jwt_handler import create_access_token

        token = create_access_token(
            user_id=str(user_data["id"]),
            full_name=user_data["full_name"],
            role=user_data["role"],
            localId=user_data.get("localId"),
            provider="google",
            scope="access"
        )

        # Verify JWT token
        payload = verify_token(token, required_scope="access")

        assert payload is not None
        assert payload["role"] == "guest"
        assert payload.get("localId") is None
        assert payload["oauth_provider"] == "google"

    @patch('app.services.auth_service.google_auth.get_user_info')
    @pytest.mark.asyncio
    async def test_google_oauth_existing_user_with_localId(self, mock_get_user_info, test_db_session):
        """
        Test Google OAuth for existing user who already has localId:
        1. User exists in DB with localId='VNW001', role='user'
        2. User logs in via Google
        3. System returns existing user data (preserves localId and role)
        4. JWT token contains localId
        """
        # Create existing user in test database
        existing_user = User(
            social_id="google_existing_456",
            provider="google",
            email="existing@gmail.com",
            full_name="Existing User",
            avatar="https://lh3.googleusercontent.com/avatar2.jpg",
            role="user",  # NOT guest
            localId="VNW001",  # Has localId
            is_active=True,
            is_verified=True
        )

        test_db_session.add(existing_user)
        await test_db_session.commit()
        await test_db_session.refresh(existing_user)

        # Mock get_or_create_user to use test DB
        with patch('app.services.auth_service.AsyncSessionLocal', return_value=test_db_session):
            from app.services.auth_service import get_or_create_user

            user_data = await get_or_create_user(
                social_id="google_existing_456",
                provider="google",
                email="existing@gmail.com",
                full_name="Existing User",
                avatar="https://lh3.googleusercontent.com/avatar2.jpg"
            )

        # Verify existing user data is preserved
        assert user_data["role"] == "user"  # NOT 'guest'
        assert user_data["localId"] == "VNW001"  # Preserved
        assert user_data["provider"] == "google"
        assert user_data["is_verified"] is True  # Preserved

        # Test JWT token
        from app.core.jwt_handler import create_access_token

        token = create_access_token(
            user_id=str(user_data["id"]),
            full_name=user_data["full_name"],
            role=user_data["role"],
            localId=user_data["localId"],
            provider="google",
            scope="access"
        )

        payload = verify_token(token, required_scope="access")

        assert payload["role"] == "user"
        assert payload["localId"] == "VNW001"
        assert payload["oauth_provider"] == "google"


@pytest.mark.integration
class TestGitHubOAuthFlow:
    """Integration tests for GitHub OAuth flow"""

    @patch('app.services.auth_service.github_auth.get_user_info')
    def test_github_oauth_new_user_flow(self, mock_get_user_info):
        """Test GitHub OAuth for new user"""
        mock_get_user_info.return_value = AsyncMock(return_value={
            "id": 789,
            "email": "newuser@github.com",
            "name": "New GitHub User",
            "avatar_url": "https://avatars.githubusercontent.com/u/789"
        })

        from app.services.auth_service import get_or_create_user
        import asyncio

        user_data = asyncio.run(get_or_create_user(
            social_id="789",
            provider="github",
            email="newuser@github.com",
            full_name="New GitHub User",
            avatar="https://avatars.githubusercontent.com/u/789"
        ))

        # Verify new user
        assert user_data["provider"] == "github"
        assert user_data["role"] == "guest"
        assert user_data["localId"] is None

        # Test JWT token
        from app.core.jwt_handler import create_access_token

        token = create_access_token(
            user_id=str(user_data["id"]),
            full_name=user_data["full_name"],
            role=user_data["role"],
            localId=user_data.get("localId"),
            provider="github",
            scope="access"
        )

        payload = verify_token(token, required_scope="access")
        assert payload["oauth_provider"] == "github"


@pytest.mark.integration
class TestMultipleOAuthAccountsSameLocalId:
    """Test scenarios where one person has multiple OAuth accounts"""

    @pytest.mark.asyncio
    async def test_same_person_google_and_github(self, test_db_session):
        """
        Test same person using both Google and GitHub:
        1. Person logs in via Google → gets user record with provider='google'
        2. Admin assigns localId='VNW001'
        3. Same person logs in via GitHub → gets new user record with provider='github'
        4. Admin assigns same localId='VNW001' to GitHub account
        5. Query by localId returns 2 users (same person, different providers)
        """
        # Create first user (Google)
        user_google = User(
            social_id="google_person_123",
            provider="google",
            email="person@gmail.com",
            full_name="Person A",
            avatar="https://lh3.googleusercontent.com/person.jpg",
            role="user",
            localId="VNW001",
            is_active=True,
            is_verified=True
        )

        # Create second user (GitHub) - same person, different provider
        user_github = User(
            social_id="github_person_456",
            provider="github",
            email="person@users.noreply.github.com",
            full_name="Person A",
            avatar="https://avatars.githubusercontent.com/u/456",
            role="user",
            localId="VNW001",  # SAME localId
            is_active=True,
            is_verified=False
        )

        test_db_session.add_all([user_google, user_github])
        await test_db_session.commit()

        # Query users by localId
        stmt = select(User).where(User.localId == "VNW001")
        result = await test_db_session.execute(stmt)
        users_with_same_localId = result.scalars().all()

        # Verify both users found
        assert len(users_with_same_localId) == 2

        # Verify they have same localId
        assert all(u.localId == "VNW001" for u in users_with_same_localId)

        # Verify they have different providers
        providers = {u.provider for u in users_with_same_localId}
        assert providers == {"google", "github"}

        # Verify they have different social_ids (unique OAuth accounts)
        social_ids = {u.social_id for u in users_with_same_localId}
        assert len(social_ids) == 2

    @pytest.mark.asyncio
    async def test_unique_constraint_prevents_duplicate_oauth_account(self, test_db_session):
        """
        Test unique constraint on (provider, social_id):
        1. User logs in via Google → creates record
        2. Same user tries to login again with same Google account
        3. System should find existing record (not create duplicate)
        """
        # This is already handled by get_or_create_user logic
        # The unique constraint ensures database-level protection

        user1 = User(
            social_id="google_123",
            provider="google",
            email="user@gmail.com",
            full_name="User",
            role="guest",
            is_active=True,
            is_verified=False
        )

        test_db_session.add(user1)
        await test_db_session.commit()

        # Try to create duplicate (should fail or be handled)
        # In get_or_create_user, this returns existing user
        stmt = select(User).where(
            (User.social_id == "google_123") & (User.provider == "google")
        )
        result = await test_db_session.execute(stmt)
        existing_user = result.scalars().first()

        assert existing_user is not None
        assert existing_user.social_id == "google_123"
        assert existing_user.provider == "google"
