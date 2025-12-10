"""
Unit tests for health check endpoints and health module.

Tests cover:
- Liveness probe
- Readiness probe
- Health check utility functions
"""

import pytest
from fastapi.testclient import TestClient

from app.core.health import (
    ComponentCheck,
    HealthStatus,
    check_database,
    check_ml_models,
    check_redis,
    is_ready,
    run_all_checks,
)


class TestHealthModule:
    """Tests for health check utility functions."""

    @pytest.mark.asyncio
    async def test_check_database_returns_component_check(self):
        """Test check_database returns ComponentCheck."""
        result = await check_database()
        assert isinstance(result, ComponentCheck)
        assert result.name == "database"
        assert result.status in [HealthStatus.HEALTHY, HealthStatus.UNHEALTHY]
        assert result.latency_ms is not None

    @pytest.mark.asyncio
    async def test_check_redis_returns_component_check(self):
        """Test check_redis returns ComponentCheck with graceful degradation."""
        result = await check_redis()
        assert isinstance(result, ComponentCheck)
        assert result.name == "redis"
        # Redis can be healthy or degraded (not unhealthy)
        assert result.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
        assert result.latency_ms is not None

    @pytest.mark.asyncio
    async def test_check_ml_models_returns_component_check(self):
        """Test check_ml_models returns ComponentCheck."""
        result = await check_ml_models()
        assert isinstance(result, ComponentCheck)
        assert result.name == "ml_models"
        assert result.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
        assert result.latency_ms is not None

    @pytest.mark.asyncio
    async def test_run_all_checks_returns_list_and_status(self):
        """Test run_all_checks returns all component checks and overall status."""
        checks, overall_status = await run_all_checks()
        assert isinstance(checks, list)
        assert len(checks) == 3  # database, redis, ml_models
        assert all(isinstance(c, ComponentCheck) for c in checks)
        assert overall_status in [
            HealthStatus.HEALTHY,
            HealthStatus.DEGRADED,
            HealthStatus.UNHEALTHY,
        ]

    @pytest.mark.asyncio
    async def test_is_ready_returns_tuple(self):
        """Test is_ready returns tuple of bool and dict."""
        ready, checks = await is_ready()
        assert isinstance(ready, bool)
        assert isinstance(checks, dict)
        assert "database" in checks
        assert "redis" in checks
        assert "ml_models" in checks
        assert all(isinstance(v, bool) for v in checks.values())

    def test_health_status_enum_values(self):
        """Test HealthStatus enum has expected values."""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"

    def test_component_check_dataclass(self):
        """Test ComponentCheck dataclass fields."""
        check = ComponentCheck(
            name="test",
            status=HealthStatus.HEALTHY,
            latency_ms=1.5,
            message="Test OK",
        )
        assert check.name == "test"
        assert check.status == HealthStatus.HEALTHY
        assert check.latency_ms == 1.5
        assert check.message == "Test OK"


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_liveness_probe(self, test_client: TestClient):
        """Test liveness probe returns OK."""
        response = test_client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_liveness_includes_timestamp(self, test_client: TestClient):
        """Test liveness probe includes timestamp."""
        response = test_client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data

    def test_readiness_probe(self, test_client: TestClient):
        """Test readiness probe returns component status."""
        response = test_client.get("/api/v1/ready")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["ready", "not_ready"]

    def test_readiness_checks_components(self, test_client: TestClient):
        """Test readiness probe checks key components."""
        response = test_client.get("/api/v1/ready")

        assert response.status_code == 200
        data = response.json()
        assert "checks" in data
        assert isinstance(data["checks"], dict)
        assert "database" in data["checks"]
        assert "redis" in data["checks"]
        assert "ml_models" in data["checks"]

    def test_readiness_includes_timestamp(self, test_client: TestClient):
        """Test readiness probe includes timestamp."""
        response = test_client.get("/api/v1/ready")

        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data

    def test_health_no_auth_required(self, unauthenticated_client: TestClient):
        """Test that health endpoints don't require authentication."""
        response = unauthenticated_client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestHealthResponseFormat:
    """Tests for health response format consistency."""

    def test_health_response_structure(self, test_client: TestClient):
        """Test health response has expected structure."""
        response = test_client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()

        # Standard health response fields
        assert "status" in data
        assert data["status"] in ["healthy", "unhealthy", "degraded"]

    def test_ready_response_structure(self, test_client: TestClient):
        """Test readiness response has expected structure."""
        response = test_client.get("/api/v1/ready")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert "timestamp" in data
