"""
Application configuration using Pydantic Settings.

All configuration is loaded from environment variables with sensible defaults
for local development.
"""

from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
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

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]

    # Authentication (Keycloak)
    KEYCLOAK_URL: str = "http://localhost:8080"
    KEYCLOAK_REALM: str = "pea-forecast"
    KEYCLOAK_CLIENT_ID: str = "pea-forecast-api"
    KEYCLOAK_CLIENT_SECRET: str = ""

    # ML Models
    MODEL_REGISTRY_PATH: str = "/app/models"

    # Logging
    LOG_LEVEL: str = "INFO"


settings = Settings()
