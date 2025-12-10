"""
Tests for the secrets management module.

Tests both Vault-enabled and fallback (environment variables) modes.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from app.core.secrets import (
    VaultClient,
    clear_secret_cache,
    get_database_secrets,
    get_keycloak_secrets,
    get_redis_secrets,
    get_secret,
)


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear the secret cache before each test."""
    clear_secret_cache()
    yield
    clear_secret_cache()


@pytest.fixture
def reset_vault_client():
    """Reset the global vault client."""
    import app.core.secrets as secrets_module

    original = secrets_module._vault_client
    secrets_module._vault_client = None
    yield
    secrets_module._vault_client = original


class TestVaultClient:
    """Tests for the VaultClient class."""

    def test_vault_disabled_by_default(self, reset_vault_client):
        """Vault should be disabled when VAULT_ENABLED is not set."""
        with patch.dict(os.environ, {}, clear=True):
            client = VaultClient()
            assert client.enabled is False

    def test_vault_enabled_when_configured(self, reset_vault_client):
        """Vault should be enabled when VAULT_ENABLED=true."""
        with patch.dict(os.environ, {"VAULT_ENABLED": "true"}, clear=True):
            client = VaultClient()
            assert client.enabled is True

    def test_vault_reads_config_from_env(self, reset_vault_client):
        """Vault should read configuration from environment variables."""
        env = {
            "VAULT_ENABLED": "true",
            "VAULT_ADDR": "http://custom-vault:8200",
            "VAULT_MOUNT_POINT": "custom-mount",
            "VAULT_ROLE": "custom-role",
        }
        with patch.dict(os.environ, env, clear=True):
            client = VaultClient()
            assert client._addr == "http://custom-vault:8200"
            assert client._mount_point == "custom-mount"
            assert client._role == "custom-role"


class TestGetSecret:
    """Tests for the get_secret function."""

    def test_returns_env_var_when_vault_disabled(self, reset_vault_client):
        """Should return environment variable when Vault is disabled."""
        with patch.dict(
            os.environ, {"VAULT_ENABLED": "false", "TEST_SECRET": "env_value"}
        ):
            result = get_secret("TEST_SECRET", default="default")
            assert result == "env_value"

    def test_returns_default_when_not_found(self, reset_vault_client):
        """Should return default value when secret is not found."""
        with patch.dict(os.environ, {"VAULT_ENABLED": "false"}, clear=True):
            result = get_secret("NONEXISTENT_SECRET", default="my_default")
            assert result == "my_default"

    def test_vault_takes_priority(self, reset_vault_client):
        """Vault secrets should take priority over environment variables."""
        mock_client = MagicMock()
        mock_client.enabled = True
        mock_client.read_secret.return_value = {"TEST_KEY": "vault_value"}

        with (
            patch("app.core.secrets.get_vault_client", return_value=mock_client),
            patch.dict(os.environ, {"TEST_KEY": "env_value"}),
        ):
            result = get_secret("TEST_KEY", secret_path="app")
            assert result == "vault_value"


class TestGetDatabaseSecrets:
    """Tests for database secrets retrieval."""

    def test_returns_env_secrets_when_vault_disabled(self, reset_vault_client):
        """Should return environment-based secrets when Vault is disabled."""
        env = {
            "VAULT_ENABLED": "false",
            "DB_USER": "test_user",
            "DB_PASSWORD": "test_pass",
            "DB_HOST": "test_host",
            "DB_PORT": "5432",
            "DB_NAME": "test_db",
            "DATABASE_URL": "postgresql://test@test:5432/test",
        }
        with patch.dict(os.environ, env):
            secrets = get_database_secrets()
            assert secrets["DB_USER"] == "test_user"
            assert secrets["DB_PASSWORD"] == "test_pass"
            assert secrets["DATABASE_URL"] == "postgresql://test@test:5432/test"

    def test_returns_vault_secrets_when_enabled(self, reset_vault_client):
        """Should return Vault secrets when enabled."""
        mock_client = MagicMock()
        mock_client.enabled = True
        mock_client.read_secret.return_value = {
            "DB_USER": "vault_user",
            "DB_PASSWORD": "vault_pass",
            "DB_HOST": "vault_host",
            "DB_PORT": "5432",
            "DB_NAME": "vault_db",
            "DATABASE_URL": "postgresql://vault@vault:5432/vault",
        }

        with patch("app.core.secrets.get_vault_client", return_value=mock_client):
            secrets = get_database_secrets()
            assert secrets["DB_USER"] == "vault_user"
            assert secrets["DATABASE_URL"] == "postgresql://vault@vault:5432/vault"


class TestGetRedisSecrets:
    """Tests for Redis secrets retrieval."""

    def test_returns_env_secrets_when_vault_disabled(self, reset_vault_client):
        """Should return environment-based Redis secrets when Vault is disabled."""
        env = {
            "VAULT_ENABLED": "false",
            "REDIS_HOST": "redis-host",
            "REDIS_PORT": "6379",
            "REDIS_PASSWORD": "redis-pass",
            "REDIS_URL": "redis://:redis-pass@redis-host:6379/0",
        }
        with patch.dict(os.environ, env):
            secrets = get_redis_secrets()
            assert secrets["REDIS_HOST"] == "redis-host"
            assert secrets["REDIS_PASSWORD"] == "redis-pass"


class TestGetKeycloakSecrets:
    """Tests for Keycloak secrets retrieval."""

    def test_returns_env_secrets_when_vault_disabled(self, reset_vault_client):
        """Should return environment-based Keycloak secrets when Vault is disabled."""
        env = {
            "VAULT_ENABLED": "false",
            "KEYCLOAK_URL": "http://keycloak:8080",
            "KEYCLOAK_REALM": "test-realm",
            "KEYCLOAK_CLIENT_ID": "test-client",
            "KEYCLOAK_CLIENT_SECRET": "test-secret",
        }
        with patch.dict(os.environ, env):
            secrets = get_keycloak_secrets()
            assert secrets["KEYCLOAK_URL"] == "http://keycloak:8080"
            assert secrets["KEYCLOAK_REALM"] == "test-realm"
            assert secrets["KEYCLOAK_CLIENT_SECRET"] == "test-secret"


class TestSecretsCaching:
    """Tests for secret caching behavior."""

    def test_secrets_are_cached(self, reset_vault_client):
        """Secrets should be cached after first retrieval."""
        with patch.dict(os.environ, {"VAULT_ENABLED": "false", "CACHED_KEY": "value1"}):
            result1 = get_secret("CACHED_KEY")
            assert result1 == "value1"

        # Change env var - cached value should still be returned
        with patch.dict(os.environ, {"VAULT_ENABLED": "false", "CACHED_KEY": "value2"}):
            result2 = get_secret("CACHED_KEY")
            assert result2 == "value1"  # Still cached

    def test_cache_can_be_cleared(self, reset_vault_client):
        """Cache should be clearable."""
        with patch.dict(os.environ, {"VAULT_ENABLED": "false", "CLEAR_KEY": "value1"}):
            result1 = get_secret("CLEAR_KEY")
            assert result1 == "value1"

        clear_secret_cache()

        with patch.dict(os.environ, {"VAULT_ENABLED": "false", "CLEAR_KEY": "value2"}):
            result2 = get_secret("CLEAR_KEY")
            assert result2 == "value2"  # New value after cache clear
