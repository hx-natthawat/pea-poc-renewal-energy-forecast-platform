"""
Pytest configuration and fixtures for PEA RE Forecast Platform tests.

This module provides:
- Test database setup
- FastAPI test client
- Mock authentication
- Sample data fixtures
"""

import asyncio
import os
from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

# Set test environment before importing app modules
os.environ["APP_ENV"] = "test"
os.environ["AUTH_ENABLED"] = "false"
# Use asyncpg driver for async SQLAlchemy
os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://postgres:postgres@localhost:5433/pea_forecast"
)

# Import app modules after setting environment
from app.core.security import CurrentUser, get_current_user
from app.main import app

# =============================================================================
# Event Loop Configuration
# =============================================================================


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# Mock Authentication Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def mock_admin_user() -> CurrentUser:
    """Mock admin user for testing."""
    return CurrentUser(
        id="test-admin-001",
        email="admin@test.pea.co.th",
        name="Test Admin",
        username="test_admin",
        roles=["admin", "operator", "analyst", "viewer"],
    )


@pytest.fixture
def mock_operator_user() -> CurrentUser:
    """Mock operator user for testing."""
    return CurrentUser(
        id="test-operator-001",
        email="operator@test.pea.co.th",
        name="Test Operator",
        username="test_operator",
        roles=["operator", "viewer"],
    )


@pytest.fixture
def mock_analyst_user() -> CurrentUser:
    """Mock analyst user for testing."""
    return CurrentUser(
        id="test-analyst-001",
        email="analyst@test.pea.co.th",
        name="Test Analyst",
        username="test_analyst",
        roles=["analyst", "viewer"],
    )


@pytest.fixture
def mock_viewer_user() -> CurrentUser:
    """Mock viewer user for testing."""
    return CurrentUser(
        id="test-viewer-001",
        email="viewer@test.pea.co.th",
        name="Test Viewer",
        username="test_viewer",
        roles=["viewer"],
    )


@pytest.fixture
def mock_api_user() -> CurrentUser:
    """Mock API service account for testing."""
    return CurrentUser(
        id="test-api-001",
        email="api@test.pea.co.th",
        name="Test API",
        username="test_api",
        roles=["api"],
    )


# =============================================================================
# Client Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def test_client(mock_admin_user: CurrentUser) -> Generator[TestClient]:
    """Create a synchronous test client with mock authentication.

    Uses session scope to avoid lifespan issues when running multiple tests.
    """

    def override_get_current_user():
        return mock_admin_user

    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def unauthenticated_client() -> Generator[TestClient]:
    """Create a test client without authentication.

    Uses session scope to avoid lifespan issues when running multiple tests.
    """
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


# =============================================================================
# Sample Data Fixtures
# =============================================================================


@pytest.fixture
def sample_solar_features() -> dict:
    """Sample solar measurement features."""
    return {
        "pyrano1": 850.5,
        "pyrano2": 842.3,
        "pvtemp1": 45.2,
        "pvtemp2": 44.8,
        "ambtemp": 32.5,
        "windspeed": 2.3,
    }


@pytest.fixture
def sample_solar_request(sample_solar_features: dict) -> dict:
    """Sample solar forecast request."""
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "station_id": "POC_STATION_1",
        "horizon_minutes": 60,
        "features": sample_solar_features,
    }


@pytest.fixture
def sample_voltage_request() -> dict:
    """Sample voltage forecast request."""
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "prosumer_ids": ["prosumer1", "prosumer2", "prosumer3"],
        "horizon_minutes": 15,
    }


@pytest.fixture
def sample_prosumer_ids() -> list:
    """List of all prosumer IDs."""
    return [
        "prosumer1",
        "prosumer2",
        "prosumer3",
        "prosumer4",
        "prosumer5",
        "prosumer6",
        "prosumer7",
    ]


@pytest.fixture
def sample_prosumer_config() -> dict:
    """Prosumer configuration mapping."""
    return {
        "prosumer1": {"phase": "A", "position": 3, "has_pv": True, "has_ev": True},
        "prosumer2": {"phase": "A", "position": 2, "has_pv": True, "has_ev": False},
        "prosumer3": {"phase": "A", "position": 1, "has_pv": True, "has_ev": False},
        "prosumer4": {"phase": "B", "position": 2, "has_pv": True, "has_ev": False},
        "prosumer5": {"phase": "B", "position": 3, "has_pv": True, "has_ev": True},
        "prosumer6": {"phase": "B", "position": 1, "has_pv": True, "has_ev": False},
        "prosumer7": {"phase": "C", "position": 1, "has_pv": True, "has_ev": True},
    }


# =============================================================================
# Voltage Limit Fixtures
# =============================================================================


@pytest.fixture
def voltage_limits() -> dict:
    """Voltage limits for validation testing."""
    return {
        "nominal": 230.0,
        "upper_limit": 242.0,  # +5%
        "lower_limit": 218.0,  # -5%
        "warning_upper": 238.0,
        "warning_lower": 222.0,
    }


# =============================================================================
# ML Model Fixtures
# =============================================================================


@pytest.fixture
def mock_solar_prediction() -> dict:
    """Mock solar prediction result."""
    return {
        "power_kw": 3542.5,
        "confidence_lower": 3380.2,
        "confidence_upper": 3704.8,
        "model_version": "solar-test-v1.0.0",
        "is_ml_prediction": True,
    }


@pytest.fixture
def mock_voltage_prediction() -> dict:
    """Mock voltage prediction result."""
    return {
        "predicted_voltage": 232.5,
        "confidence_lower": 230.5,
        "confidence_upper": 234.5,
        "phase": "A",
        "status": "normal",
        "model_version": "voltage-test-v1.0.0",
        "is_ml_prediction": True,
    }


# =============================================================================
# Timestamp Fixtures
# =============================================================================


@pytest.fixture
def current_timestamp() -> datetime:
    """Current timestamp for tests."""
    return datetime.now(UTC)


@pytest.fixture
def past_timestamp() -> datetime:
    """Timestamp from 24 hours ago."""
    return datetime.now(UTC) - timedelta(hours=24)


@pytest.fixture
def future_timestamp() -> datetime:
    """Timestamp 1 hour in the future."""
    return datetime.now(UTC) + timedelta(hours=1)
