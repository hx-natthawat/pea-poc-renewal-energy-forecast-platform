"""
Unit tests for security module.

Tests authentication, authorization, and JWT handling.
"""

from app.core.security import (
    CurrentUser,
    JWKSClient,
    TokenPayload,
    require_admin,
    require_analyst,
    require_api,
    require_operator,
    require_roles,
    require_viewer,
)


class TestCurrentUser:
    """Test CurrentUser model."""

    def test_create_user(self):
        """Test creating a user with all fields."""
        user = CurrentUser(
            id="user-123",
            email="test@example.com",
            username="testuser",
            roles=["admin", "analyst"],
        )
        assert user.id == "user-123"
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.roles == ["admin", "analyst"]

    def test_create_user_minimal(self):
        """Test creating a user with only required fields."""
        user = CurrentUser(id="user-123")
        assert user.id == "user-123"
        assert user.email is None
        assert user.username is None
        assert user.roles == []

    def test_create_user_with_name(self):
        """Test creating a user with name field."""
        user = CurrentUser(
            id="user-123",
            name="Test User",
        )
        assert user.name == "Test User"

    def test_user_with_empty_roles(self):
        """Test user with empty roles list."""
        user = CurrentUser(id="user-123", roles=[])
        assert user.roles == []

    def test_user_with_multiple_roles(self):
        """Test user with multiple roles."""
        user = CurrentUser(
            id="user-123",
            roles=["admin", "operator", "analyst", "viewer"],
        )
        assert len(user.roles) == 4
        assert "admin" in user.roles


class TestTokenPayload:
    """Test TokenPayload model."""

    def test_create_token_payload(self):
        """Test creating a token payload with all fields."""
        payload = TokenPayload(
            sub="user-123",
            exp=1234567890,
            iat=1234567800,
            email="test@example.com",
            name="Test User",
            preferred_username="testuser",
        )
        assert payload.sub == "user-123"
        assert payload.exp == 1234567890
        assert payload.iat == 1234567800
        assert payload.email == "test@example.com"
        assert payload.name == "Test User"
        assert payload.preferred_username == "testuser"

    def test_create_token_payload_minimal(self):
        """Test creating a token payload with only required fields."""
        payload = TokenPayload(
            sub="user-123",
            exp=1234567890,
            iat=1234567800,
        )
        assert payload.sub == "user-123"
        assert payload.email is None
        assert payload.realm_access is None

    def test_token_payload_with_realm_access(self):
        """Test token payload with realm access roles."""
        payload = TokenPayload(
            sub="user-123",
            exp=1234567890,
            iat=1234567800,
            realm_access={"roles": ["admin", "user"]},
        )
        assert payload.realm_access == {"roles": ["admin", "user"]}


class TestJWKSClient:
    """Test JWKSClient."""

    def test_client_initialization(self):
        """Test JWKS client initialization."""
        client = JWKSClient()
        assert client._jwks is None
        assert client._last_fetch is None

    def test_get_key_no_jwks(self):
        """Test get_key when JWKS is not loaded."""
        client = JWKSClient()
        result = client.get_key("some-key-id")
        assert result is None

    def test_get_key_with_matching_key(self):
        """Test get_key with a matching key ID."""
        client = JWKSClient()
        client._jwks = {
            "keys": [
                {
                    "kid": "key-123",
                    "kty": "RSA",
                    "use": "sig",
                    "n": "test-n-value",
                    "e": "AQAB",
                }
            ]
        }
        result = client.get_key("key-123")
        assert result is not None
        assert result["kid"] == "key-123"
        assert result["kty"] == "RSA"
        assert result["use"] == "sig"

    def test_get_key_no_matching_key(self):
        """Test get_key when key ID doesn't match."""
        client = JWKSClient()
        client._jwks = {
            "keys": [
                {
                    "kid": "key-123",
                    "kty": "RSA",
                    "n": "test-n",
                    "e": "AQAB",
                }
            ]
        }
        result = client.get_key("different-key")
        assert result is None

    def test_get_key_default_use(self):
        """Test get_key returns default 'sig' for use field."""
        client = JWKSClient()
        client._jwks = {
            "keys": [
                {
                    "kid": "key-123",
                    "kty": "RSA",
                    "n": "test-n",
                    "e": "AQAB",
                    # No 'use' field
                }
            ]
        }
        result = client.get_key("key-123")
        assert result["use"] == "sig"


class TestRequireRoles:
    """Test require_roles dependency."""

    def test_require_roles_returns_callable(self):
        """Test that require_roles returns a callable."""
        checker = require_roles(["admin"])
        assert callable(checker)

    def test_require_roles_empty_list(self):
        """Test require_roles with empty list."""
        checker = require_roles([])
        assert callable(checker)

    def test_require_roles_multiple_roles(self):
        """Test require_roles with multiple roles."""
        checker = require_roles(["admin", "operator", "analyst"])
        assert callable(checker)


class TestConvenienceDependencies:
    """Test convenience role dependencies."""

    def test_require_admin_is_callable(self):
        """Test require_admin is callable."""
        assert callable(require_admin)

    def test_require_operator_is_callable(self):
        """Test require_operator is callable."""
        assert callable(require_operator)

    def test_require_analyst_is_callable(self):
        """Test require_analyst is callable."""
        assert callable(require_analyst)

    def test_require_viewer_is_callable(self):
        """Test require_viewer is callable."""
        assert callable(require_viewer)

    def test_require_api_is_callable(self):
        """Test require_api is callable."""
        assert callable(require_api)
