"""
Unit tests for forecast comparison endpoints.

Tests the /api/v1/comparison endpoints.
"""

from fastapi.testclient import TestClient


class TestSolarComparison:
    """Tests for GET /api/v1/comparison/solar"""

    def test_get_solar_comparison(self, test_client: TestClient):
        """Test getting solar forecast comparison."""
        response = test_client.get("/api/v1/comparison/solar")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "station_id" in data["data"]
        assert "model_type" in data["data"]
        assert data["data"]["model_type"] == "solar"

    def test_solar_comparison_with_station(self, test_client: TestClient):
        """Test solar comparison with specific station."""
        response = test_client.get(
            "/api/v1/comparison/solar", params={"station_id": "POC_STATION_1"}
        )

        assert response.status_code == 200
        assert response.json()["data"]["station_id"] == "POC_STATION_1"

    def test_solar_comparison_with_hours(self, test_client: TestClient):
        """Test solar comparison with custom hours."""
        response = test_client.get("/api/v1/comparison/solar", params={"hours": 48})

        assert response.status_code == 200
        assert response.json()["data"]["period_hours"] == 48

    def test_solar_comparison_includes_metrics(self, test_client: TestClient):
        """Test that comparison includes accuracy metrics."""
        response = test_client.get("/api/v1/comparison/solar")

        assert response.status_code == 200
        metrics = response.json()["data"]["metrics"]
        assert "mae" in metrics
        assert "rmse" in metrics
        assert "bias" in metrics

    def test_solar_comparison_includes_targets(self, test_client: TestClient):
        """Test that comparison includes TOR targets."""
        response = test_client.get("/api/v1/comparison/solar")

        assert response.status_code == 200
        targets = response.json()["data"]["targets"]
        assert "mape" in targets
        assert targets["mape"]["target"] == 10.0  # TOR requirement


class TestVoltageComparison:
    """Tests for GET /api/v1/comparison/voltage"""

    def test_get_voltage_comparison(self, test_client: TestClient):
        """Test getting voltage forecast comparison."""
        response = test_client.get("/api/v1/comparison/voltage")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["model_type"] == "voltage"

    def test_voltage_comparison_with_prosumer(self, test_client: TestClient):
        """Test voltage comparison for specific prosumer."""
        response = test_client.get(
            "/api/v1/comparison/voltage", params={"prosumer_id": "prosumer1"}
        )

        assert response.status_code == 200
        assert response.json()["data"]["prosumer_id"] == "prosumer1"

    def test_voltage_comparison_includes_targets(self, test_client: TestClient):
        """Test that voltage comparison includes TOR targets."""
        response = test_client.get("/api/v1/comparison/voltage")

        assert response.status_code == 200
        targets = response.json()["data"]["targets"]
        assert "mae" in targets
        assert targets["mae"]["target"] == 2.0  # TOR requirement


class TestComparisonSummary:
    """Tests for GET /api/v1/comparison/summary"""

    def test_get_comparison_summary(self, test_client: TestClient):
        """Test getting comparison summary."""
        response = test_client.get("/api/v1/comparison/summary")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "solar" in data["data"]
        assert "voltage" in data["data"]
        assert "overall_status" in data["data"]

    def test_summary_includes_both_models(self, test_client: TestClient):
        """Test that summary includes both model metrics."""
        response = test_client.get("/api/v1/comparison/summary")

        assert response.status_code == 200
        data = response.json()["data"]
        assert "metrics" in data["solar"]
        assert "metrics" in data["voltage"]

    def test_summary_overall_status(self, test_client: TestClient):
        """Test overall status is valid."""
        response = test_client.get("/api/v1/comparison/summary")

        assert response.status_code == 200
        status = response.json()["data"]["overall_status"]
        assert status in ["passing", "failing"]
