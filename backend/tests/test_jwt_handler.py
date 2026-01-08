import pytest
import jwt
from datetime import datetime, timedelta

from app.core.jwt_handler import create_access_token, verify_token
from app.core.config import settings


class TestCreateAccessToken:
    """Test create_access_token function"""

    def test_create_token_with_all_fields(self):
        """Test JWT token includes all fields: user_id, role, localId, oauth_provider"""
        token = create_access_token(
            user_id="123",
            full_name="Test User",
            role="user",
            localId="VNW001",
            provider="google",
            scope="access"
        )

        # Token should be a non-empty string
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

        # Decode token to verify payload
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

        assert payload["user_id"] == "123"
        assert payload["full_name"] == "Test User"
        assert payload["role"] == "user"
        assert payload["localId"] == "VNW001"
        assert payload["oauth_provider"] == "google"
        assert payload["scope"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_create_token_without_localId(self):
        """Test JWT token works without localId (backward compatible)"""
        token = create_access_token(
            user_id="456",
            full_name="User Without LocalId",
            role="guest",
            scope="access"
        )

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

        assert payload["user_id"] == "456"
        assert payload["role"] == "guest"
        # localId and provider should not be in payload when None
        assert "localId" not in payload or payload.get("localId") is None
        assert "oauth_provider" not in payload or payload.get("oauth_provider") is None

    def test_create_token_with_localId_without_provider(self):
        """Test token can have localId without provider"""
        token = create_access_token(
            user_id="789",
            full_name="User",
            role="user",
            localId="VNW002",
            scope="access"
        )

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

        assert payload["localId"] == "VNW002"
        assert "oauth_provider" not in payload or payload.get("oauth_provider") is None

    def test_create_token_expiration(self):
        """Test token has correct expiration time"""
        token = create_access_token(
            user_id="123",
            full_name="Test",
            role="user",
            scope="access"
        )

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

        # Check expiration is in the future
        exp = datetime.fromtimestamp(payload["exp"])
        now = datetime.utcnow()

        assert exp > now
        # Should be approximately ACCESS_TOKEN_EXPIRE_MINUTES in the future
        expected_exp = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        time_diff = abs((exp - expected_exp).total_seconds())
        assert time_diff < 60  # Within 1 minute tolerance

    def test_create_token_custom_expiration(self):
        """Test token with custom expiration delta"""
        custom_delta = timedelta(hours=2)
        token = create_access_token(
            user_id="123",
            full_name="Test",
            role="user",
            expires_delta=custom_delta,
            scope="access"
        )

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

        exp = datetime.fromtimestamp(payload["exp"])
        now = datetime.utcnow()
        expected_exp = now + custom_delta

        time_diff = abs((exp - expected_exp).total_seconds())
        assert time_diff < 60


class TestVerifyToken:
    """Test verify_token function"""

    def test_verify_valid_token(self):
        """Test verifying a valid token returns correct payload"""
        token = create_access_token(
            user_id="123",
            full_name="Test User",
            role="admin",
            localId="ADM001",
            provider="google",
            scope="access"
        )

        payload = verify_token(token, required_scope="access")

        assert payload is not None
        assert payload["user_id"] == "123"
        assert payload["role"] == "admin"
        assert payload["localId"] == "ADM001"
        assert payload["oauth_provider"] == "google"

    def test_verify_token_without_localId(self):
        """Test verifying token without localId adds None values"""
        # Create token without localId/provider
        manual_payload = {
            "user_id": "456",
            "full_name": "User",
            "role": "guest",
            "scope": "access",
            "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
            "iat": int(datetime.utcnow().timestamp()),
        }

        token = jwt.encode(manual_payload, settings.SECRET_KEY, algorithm="HS256")

        payload = verify_token(token, required_scope="access")

        assert payload is not None
        assert payload["user_id"] == "456"
        assert payload["role"] == "guest"
        # verify_token should add None for missing fields
        assert payload.get("localId") is None
        assert payload.get("oauth_provider") is None

    def test_verify_old_token_format(self):
        """Test old tokens (without localId field) still verify successfully"""
        # Simulate old token format
        old_payload = {
            "user_id": "old_user_123",
            "full_name": "Old User",
            "role": "user",
            "scope": "access",
            "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
            "iat": int(datetime.utcnow().timestamp()),
        }

        old_token = jwt.encode(old_payload, settings.SECRET_KEY, algorithm="HS256")

        # Should still verify successfully
        payload = verify_token(old_token, required_scope="access")

        assert payload is not None
        assert payload["user_id"] == "old_user_123"
        assert payload["role"] == "user"
        # Missing fields should be set to None
        assert payload.get("localId") is None
        assert payload.get("oauth_provider") is None

    def test_verify_expired_token(self):
        """Test expired token returns None"""
        # Create token that expired 1 hour ago
        expired_payload = {
            "user_id": "123",
            "full_name": "Test",
            "role": "user",
            "scope": "access",
            "exp": int((datetime.utcnow() - timedelta(hours=1)).timestamp()),
            "iat": int((datetime.utcnow() - timedelta(hours=2)).timestamp()),
        }

        expired_token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm="HS256")

        payload = verify_token(expired_token, required_scope="access")

        assert payload is None

    def test_verify_invalid_token(self):
        """Test invalid token returns None"""
        invalid_token = "invalid.token.here"

        payload = verify_token(invalid_token, required_scope="access")

        assert payload is None

    def test_verify_wrong_secret(self):
        """Test token signed with wrong secret returns None"""
        wrong_secret_token = jwt.encode(
            {
                "user_id": "123",
                "role": "user",
                "scope": "access",
                "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
            },
            "wrong_secret_key",
            algorithm="HS256"
        )

        payload = verify_token(wrong_secret_token, required_scope="access")

        assert payload is None

    def test_verify_wrong_scope(self):
        """Test token with wrong scope returns None"""
        token = create_access_token(
            user_id="123",
            full_name="Test",
            role="user",
            scope="refresh"  # Different scope
        )

        payload = verify_token(token, required_scope="access")

        # Should return None because scope doesn't match
        assert payload is None

    def test_verify_correct_scope(self):
        """Test token with correct scope verifies successfully"""
        token = create_access_token(
            user_id="123",
            full_name="Test",
            role="user",
            scope="refresh"
        )

        payload = verify_token(token, required_scope="refresh")

        assert payload is not None
        assert payload["user_id"] == "123"
        assert payload["scope"] == "refresh"
