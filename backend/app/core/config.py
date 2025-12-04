"""
Application configuration using Pydantic Settings.

All configuration is loaded from environment variables with sensible defaults
for local development.
"""

from typing import List

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),  # Check backend/.env first, then root
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "PEA RE Forecast Platform"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # API
    API_V1_PREFIX: str = "/api/v1"

    # Database (TimescaleDB on port 5433)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/pea_forecast"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # CORS - stored as comma-separated string, exposed as list
    CORS_ORIGINS_STR: str = "http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000,http://127.0.0.1:8000"

    @computed_field
    @property
    def CORS_ORIGINS(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.CORS_ORIGINS_STR.split(",") if origin.strip()]

    # Authentication (Keycloak)
    AUTH_ENABLED: bool = False  # Set to True to require authentication
    KEYCLOAK_URL: str = "http://localhost:8080"
    KEYCLOAK_REALM: str = "pea-forecast"
    KEYCLOAK_CLIENT_ID: str = "pea-forecast-web"
    KEYCLOAK_CLIENT_SECRET: str = ""
    JWT_ALGORITHM: str = "RS256"
    JWKS_CACHE_TTL: int = 3600  # 1 hour

    @computed_field
    @property
    def KEYCLOAK_ISSUER(self) -> str:
        """Get Keycloak issuer URL."""
        return f"{self.KEYCLOAK_URL}/realms/{self.KEYCLOAK_REALM}"

    @computed_field
    @property
    def KEYCLOAK_JWKS_URL(self) -> str:
        """Get Keycloak JWKS URL."""
        return f"{self.KEYCLOAK_URL}/realms/{self.KEYCLOAK_REALM}/protocol/openid-connect/certs"

    # ML Models
    MODEL_REGISTRY_PATH: str = "/app/models"

    # TMD (Thai Meteorological Department) API
    # Register at: https://data.tmd.go.th/nwpapi/register
    TMD_API_BASE_URL: str = "https://data.tmd.go.th/api"
    TMD_API_UID: str = "api"  # Public demo credentials
    TMD_API_KEY: str = "api12345"  # Public demo credentials
    TMD_API_TIMEOUT: int = 10  # seconds
    TMD_CACHE_TTL: int = 300  # 5 minutes

    # Logging
    LOG_LEVEL: str = "INFO"


settings = Settings()
