"""
Unit tests for health check endpoints.

Tests cover:
- Liveness probe
- Readiness probe
"""

from fastapi.testclient import TestClient


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
