"""
Secrets management with HashiCorp Vault support.

This module provides a unified interface for loading secrets from:
1. HashiCorp Vault (when VAULT_ENABLED=true)
2. Environment variables (fallback)

TOR Requirement: 7.1.6 - Key Management per TOR Table 2
"""

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class VaultClient:
    """HashiCorp Vault client wrapper."""

    def __init__(self) -> None:
        self._client = None
        self._enabled = os.getenv("VAULT_ENABLED", "false").lower() == "true"
        self._addr = os.getenv("VAULT_ADDR", "http://vault:8200")
        self._mount_point = os.getenv("VAULT_MOUNT_POINT", "pea-forecast")
        self._role = os.getenv("VAULT_ROLE", "pea-forecast-backend")

    @property
    def enabled(self) -> bool:
        """Check if Vault is enabled."""
        return self._enabled

    def _get_client(self):
        """Get or create Vault client."""
        if self._client is not None:
            return self._client

        try:
            import hvac

            self._client = hvac.Client(url=self._addr)

            # Try Kubernetes auth first (for K8s deployments)
            jwt_path = Path("/var/run/secrets/kubernetes.io/serviceaccount/token")
            if jwt_path.exists():
                jwt = jwt_path.read_text()
                self._client.auth.kubernetes.login(role=self._role, jwt=jwt)
                logger.info("Authenticated to Vault using Kubernetes auth")
            # Fall back to token auth (for development)
            elif os.getenv("VAULT_TOKEN"):
                self._client.token = os.getenv("VAULT_TOKEN")
                logger.info("Authenticated to Vault using token")
            else:
                logger.warning("No Vault authentication method available")
                return None

            if not self._client.is_authenticated():
                logger.error("Failed to authenticate to Vault")
                return None

            return self._client

        except ImportError:
            logger.warning("hvac package not installed, Vault disabled")
            self._enabled = False
            return None
        except Exception as e:
            logger.error(f"Failed to connect to Vault: {e}")
            return None

    def read_secret(self, path: str) -> dict[str, Any] | None:
        """
        Read a secret from Vault.

        Args:
            path: Secret path (e.g., 'database', 'redis', 'app')

        Returns:
            Secret data dict or None if not found
        """
        if not self._enabled:
            return None

        client = self._get_client()
        if client is None:
            return None

        try:
            response = client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point=self._mount_point,
            )
            return response.get("data", {}).get("data", {})
        except Exception as e:
            logger.error(f"Failed to read secret from Vault: {path} - {e}")
            return None


# Global Vault client instance
_vault_client: VaultClient | None = None


def get_vault_client() -> VaultClient:
    """Get the global Vault client instance."""
    global _vault_client
    if _vault_client is None:
        _vault_client = VaultClient()
    return _vault_client


@lru_cache(maxsize=32)
def get_secret(key: str, default: str = "", secret_path: str = "app") -> str:
    """
    Get a secret value from Vault or environment variables.

    Priority:
    1. Vault (if enabled and secret exists)
    2. Environment variable
    3. Default value

    Args:
        key: Secret key name
        default: Default value if not found
        secret_path: Vault secret path (default: 'app')

    Returns:
        Secret value
    """
    vault = get_vault_client()

    # Try Vault first
    if vault.enabled:
        secrets = vault.read_secret(secret_path)
        if secrets and key in secrets:
            logger.debug(f"Loaded secret {key} from Vault")
            return secrets[key]

    # Fall back to environment variable
    env_value = os.getenv(key)
    if env_value is not None:
        logger.debug(f"Loaded secret {key} from environment")
        return env_value

    logger.debug(f"Using default for secret {key}")
    return default


def get_database_secrets() -> dict[str, str]:
    """Get all database-related secrets."""
    vault = get_vault_client()

    if vault.enabled:
        secrets = vault.read_secret("database")
        if secrets:
            return {
                "DB_USER": secrets.get("DB_USER", "postgres"),
                "DB_PASSWORD": secrets.get("DB_PASSWORD", "postgres"),
                "DB_HOST": secrets.get("DB_HOST", "localhost"),
                "DB_PORT": secrets.get("DB_PORT", "5433"),
                "DB_NAME": secrets.get("DB_NAME", "pea_forecast"),
                "DATABASE_URL": secrets.get("DATABASE_URL", ""),
            }

    # Fall back to environment
    return {
        "DB_USER": os.getenv("DB_USER", "postgres"),
        "DB_PASSWORD": os.getenv("DB_PASSWORD", "postgres"),
        "DB_HOST": os.getenv("DB_HOST", "localhost"),
        "DB_PORT": os.getenv("DB_PORT", "5433"),
        "DB_NAME": os.getenv("DB_NAME", "pea_forecast"),
        "DATABASE_URL": os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://postgres:postgres@localhost:5433/pea_forecast",
        ),
    }


def get_redis_secrets() -> dict[str, str]:
    """Get all Redis-related secrets."""
    vault = get_vault_client()

    if vault.enabled:
        secrets = vault.read_secret("redis")
        if secrets:
            return {
                "REDIS_HOST": secrets.get("REDIS_HOST", "localhost"),
                "REDIS_PORT": secrets.get("REDIS_PORT", "6379"),
                "REDIS_PASSWORD": secrets.get("REDIS_PASSWORD", ""),
                "REDIS_URL": secrets.get("REDIS_URL", "redis://localhost:6379/0"),
            }

    # Fall back to environment
    return {
        "REDIS_HOST": os.getenv("REDIS_HOST", "localhost"),
        "REDIS_PORT": os.getenv("REDIS_PORT", "6379"),
        "REDIS_PASSWORD": os.getenv("REDIS_PASSWORD", ""),
        "REDIS_URL": os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    }


def get_keycloak_secrets() -> dict[str, str]:
    """Get all Keycloak-related secrets."""
    vault = get_vault_client()

    if vault.enabled:
        secrets = vault.read_secret("keycloak")
        if secrets:
            return {
                "KEYCLOAK_URL": secrets.get("KEYCLOAK_URL", "http://localhost:8080"),
                "KEYCLOAK_REALM": secrets.get("KEYCLOAK_REALM", "pea-forecast"),
                "KEYCLOAK_CLIENT_ID": secrets.get(
                    "KEYCLOAK_CLIENT_ID", "pea-forecast-web"
                ),
                "KEYCLOAK_CLIENT_SECRET": secrets.get("KEYCLOAK_CLIENT_SECRET", ""),
            }

    # Fall back to environment
    return {
        "KEYCLOAK_URL": os.getenv("KEYCLOAK_URL", "http://localhost:8080"),
        "KEYCLOAK_REALM": os.getenv("KEYCLOAK_REALM", "pea-forecast"),
        "KEYCLOAK_CLIENT_ID": os.getenv("KEYCLOAK_CLIENT_ID", "pea-forecast-web"),
        "KEYCLOAK_CLIENT_SECRET": os.getenv("KEYCLOAK_CLIENT_SECRET", ""),
    }


def clear_secret_cache() -> None:
    """Clear the secret cache (useful for testing)."""
    get_secret.cache_clear()
