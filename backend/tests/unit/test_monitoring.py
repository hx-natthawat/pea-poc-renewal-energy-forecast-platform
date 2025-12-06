"""
Unit tests for model monitoring endpoints.

Tests the /api/v1/monitoring endpoints.
"""

from fastapi.testclient import TestClient


class TestModelHealth:
    """Tests for GET /api/v1/monitoring/health"""

    def test_get_model_health(self, test_client: TestClient):
        """Test getting model health status."""
        response = test_client.get("/api/v1/monitoring/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "models" in data["data"]
        assert "overall_healthy" in data["data"]

    def test_model_health_includes_both_types(self, test_client: TestClient):
        """Test that health includes solar and voltage models."""
        response = test_client.get("/api/v1/monitoring/health")

        assert response.status_code == 200
        models = response.json()["data"]["models"]
        model_types = [m["model_type"] for m in models]
        assert "solar" in model_types
        assert "voltage" in model_types

    def test_model_health_structure(self, test_client: TestClient):
        """Test model health entry structure."""
        response = test_client.get("/api/v1/monitoring/health")

        assert response.status_code == 200
        models = response.json()["data"]["models"]
        for model in models:
            assert "model_type" in model
            assert "model_version" in model
            assert "is_healthy" in model
            assert "accuracy_status" in model


class TestModelPerformance:
    """Tests for GET /api/v1/monitoring/performance/{model_type}"""

    def test_get_solar_performance(self, test_client: TestClient):
        """Test getting solar model performance."""
        response = test_client.get("/api/v1/monitoring/performance/solar")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["model_type"] == "solar"

    def test_get_voltage_performance(self, test_client: TestClient):
        """Test getting voltage model performance."""
        response = test_client.get("/api/v1/monitoring/performance/voltage")

        assert response.status_code == 200
        assert response.json()["data"]["model_type"] == "voltage"

    def test_performance_with_days(self, test_client: TestClient):
        """Test performance with custom days."""
        response = test_client.get(
            "/api/v1/monitoring/performance/solar", params={"days": 14}
        )

        assert response.status_code == 200
        assert response.json()["data"]["analysis_period"]["days"] == 14

    def test_performance_includes_targets(self, test_client: TestClient):
        """Test that performance includes TOR targets."""
        response = test_client.get("/api/v1/monitoring/performance/solar")

        assert response.status_code == 200
        targets = response.json()["data"]["targets"]
        assert "mape" in targets


class TestDriftDetection:
    """Tests for GET /api/v1/monitoring/drift/{model_type}"""

    def test_detect_solar_drift(self, test_client: TestClient):
        """Test drift detection for solar model."""
        response = test_client.get("/api/v1/monitoring/drift/solar")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "overall_drift_detected" in data["data"]
        assert "drift_indicators" in data["data"]

    def test_detect_voltage_drift(self, test_client: TestClient):
        """Test drift detection for voltage model."""
        response = test_client.get("/api/v1/monitoring/drift/voltage")

        assert response.status_code == 200

    def test_drift_indicator_structure(self, test_client: TestClient):
        """Test drift indicator structure."""
        response = test_client.get("/api/v1/monitoring/drift/solar")

        assert response.status_code == 200
        indicators = response.json()["data"]["drift_indicators"]
        for indicator in indicators:
            assert "feature" in indicator
            assert "drift_score" in indicator
            assert "drift_detected" in indicator
            assert "threshold" in indicator


class TestPredictionAccuracy:
    """Tests for GET /api/v1/monitoring/predictions/accuracy"""

    def test_get_solar_accuracy(self, test_client: TestClient):
        """Test getting solar prediction accuracy."""
        response = test_client.get(
            "/api/v1/monitoring/predictions/accuracy", params={"model_type": "solar"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["model_type"] == "solar"

    def test_get_voltage_accuracy(self, test_client: TestClient):
        """Test getting voltage prediction accuracy."""
        response = test_client.get(
            "/api/v1/monitoring/predictions/accuracy", params={"model_type": "voltage"}
        )

        assert response.status_code == 200

    def test_accuracy_with_hours(self, test_client: TestClient):
        """Test accuracy with custom hours."""
        response = test_client.get(
            "/api/v1/monitoring/predictions/accuracy",
            params={"model_type": "solar", "hours": 48},
        )

        assert response.status_code == 200
        # Just verify it returns successfully with the hours param


class TestListModels:
    """Tests for GET /api/v1/monitoring/models"""

    def test_list_models(self, test_client: TestClient):
        """Test listing registered models."""
        response = test_client.get("/api/v1/monitoring/models")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "models" in data["data"]
        assert "count" in data["data"]
