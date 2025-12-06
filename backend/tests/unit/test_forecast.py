"""
Unit tests for forecast endpoints.

Tests cover:
- Solar power prediction
- Voltage prediction
- History endpoints
- Cache statistics
- Authentication and authorization
"""

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.core.security import CurrentUser


class TestSolarForecast:
    """Tests for solar forecast endpoint."""

    def test_solar_forecast_success(
        self,
        test_client: TestClient,
        sample_solar_request: dict,
    ):
        """Test successful solar power prediction."""
        response = test_client.post(
            "/api/v1/forecast/solar",
            json=sample_solar_request,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert "prediction" in data["data"]
        assert "power_kw" in data["data"]["prediction"]
        assert data["data"]["prediction"]["power_kw"] >= 0

    def test_solar_forecast_with_high_irradiance(
        self,
        test_client: TestClient,
    ):
        """Test solar forecast with high irradiance values."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "station_id": "POC_STATION_1",
            "horizon_minutes": 60,
            "features": {
                "pyrano1": 1200.0,  # High irradiance
                "pyrano2": 1180.0,
                "pvtemp1": 55.0,
                "pvtemp2": 54.0,
                "ambtemp": 35.0,
                "windspeed": 1.5,
            },
        }

        response = test_client.post("/api/v1/forecast/solar", json=request)

        assert response.status_code == 200
        data = response.json()
        # High irradiance should produce higher power
        assert data["data"]["prediction"]["power_kw"] > 0

    def test_solar_forecast_with_zero_irradiance(
        self,
        test_client: TestClient,
    ):
        """Test solar forecast with zero irradiance (nighttime)."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "station_id": "POC_STATION_1",
            "horizon_minutes": 60,
            "features": {
                "pyrano1": 0.0,  # Zero irradiance
                "pyrano2": 0.0,
                "pvtemp1": 25.0,
                "pvtemp2": 25.0,
                "ambtemp": 25.0,
                "windspeed": 2.0,
            },
        }

        response = test_client.post("/api/v1/forecast/solar", json=request)

        assert response.status_code == 200
        data = response.json()
        # Zero irradiance should produce zero or very low power
        assert data["data"]["prediction"]["power_kw"] >= 0

    def test_solar_forecast_invalid_irradiance(
        self,
        test_client: TestClient,
    ):
        """Test solar forecast with invalid irradiance values."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "station_id": "POC_STATION_1",
            "horizon_minutes": 60,
            "features": {
                "pyrano1": -100.0,  # Invalid negative value
                "pyrano2": 800.0,
                "pvtemp1": 45.0,
                "pvtemp2": 45.0,
                "ambtemp": 30.0,
                "windspeed": 2.0,
            },
        }

        response = test_client.post("/api/v1/forecast/solar", json=request)
        assert response.status_code == 422  # Validation error

    def test_solar_forecast_includes_confidence_interval(
        self,
        test_client: TestClient,
        sample_solar_request: dict,
    ):
        """Test that solar forecast includes confidence intervals."""
        response = test_client.post(
            "/api/v1/forecast/solar",
            json=sample_solar_request,
        )

        assert response.status_code == 200
        data = response.json()
        prediction = data["data"]["prediction"]

        assert "confidence_lower" in prediction
        assert "confidence_upper" in prediction
        assert prediction["confidence_lower"] <= prediction["power_kw"]
        assert prediction["confidence_upper"] >= prediction["power_kw"]

    def test_solar_forecast_includes_metadata(
        self,
        test_client: TestClient,
        sample_solar_request: dict,
    ):
        """Test that solar forecast includes metadata."""
        response = test_client.post(
            "/api/v1/forecast/solar",
            json=sample_solar_request,
        )

        assert response.status_code == 200
        data = response.json()

        assert "meta" in data
        assert "prediction_time_ms" in data["meta"]
        assert "cached" in data["meta"]
        assert "model_version" in data["data"]


class TestVoltageForecast:
    """Tests for voltage forecast endpoint."""

    def test_voltage_forecast_success(
        self,
        test_client: TestClient,
        sample_voltage_request: dict,
    ):
        """Test successful voltage prediction."""
        response = test_client.post(
            "/api/v1/forecast/voltage",
            json=sample_voltage_request,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "predictions" in data["data"]
        assert len(data["data"]["predictions"]) == len(
            sample_voltage_request["prosumer_ids"]
        )

    def test_voltage_forecast_all_prosumers(
        self,
        test_client: TestClient,
        sample_prosumer_ids: list,
    ):
        """Test voltage prediction for all prosumers."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "prosumer_ids": sample_prosumer_ids,
            "horizon_minutes": 15,
        }

        response = test_client.post("/api/v1/forecast/voltage", json=request)

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["predictions"]) == 7  # All 7 prosumers

    def test_voltage_forecast_single_prosumer(
        self,
        test_client: TestClient,
    ):
        """Test voltage prediction for a single prosumer."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "prosumer_ids": ["prosumer1"],
            "horizon_minutes": 15,
        }

        response = test_client.post("/api/v1/forecast/voltage", json=request)

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["predictions"]) == 1

    def test_voltage_forecast_includes_phase(
        self,
        test_client: TestClient,
        sample_voltage_request: dict,
    ):
        """Test that voltage forecast includes phase information."""
        response = test_client.post(
            "/api/v1/forecast/voltage",
            json=sample_voltage_request,
        )

        assert response.status_code == 200
        data = response.json()

        for prediction in data["data"]["predictions"]:
            assert "phase" in prediction
            assert prediction["phase"] in ["A", "B", "C"]

    def test_voltage_forecast_includes_status(
        self,
        test_client: TestClient,
        sample_voltage_request: dict,
    ):
        """Test that voltage forecast includes status."""
        response = test_client.post(
            "/api/v1/forecast/voltage",
            json=sample_voltage_request,
        )

        assert response.status_code == 200
        data = response.json()

        for prediction in data["data"]["predictions"]:
            assert "status" in prediction
            assert prediction["status"] in ["normal", "warning", "critical"]

    def test_voltage_within_limits(
        self,
        test_client: TestClient,
        sample_voltage_request: dict,
        voltage_limits: dict,
    ):
        """Test that predicted voltages are within reasonable limits."""
        response = test_client.post(
            "/api/v1/forecast/voltage",
            json=sample_voltage_request,
        )

        assert response.status_code == 200
        data = response.json()

        for prediction in data["data"]["predictions"]:
            voltage = prediction["predicted_voltage"]
            # Voltage should be in a reasonable range (200-260V)
            assert 200 <= voltage <= 260


class TestForecastHistory:
    """Tests for forecast history endpoints."""

    @pytest.mark.skipif(
        True,  # Skip if database is not available
        reason="Requires database connection",
    )
    def test_solar_history_success(
        self,
        test_client: TestClient,
    ):
        """Test solar forecast history endpoint."""
        response = test_client.get("/api/v1/forecast/solar/history")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "predictions" in data["data"]
        assert "count" in data["data"]
        assert "total" in data["data"]

    @pytest.mark.skipif(
        True,  # Skip if database is not available
        reason="Requires database connection",
    )
    def test_solar_history_with_pagination(
        self,
        test_client: TestClient,
    ):
        """Test solar history with pagination parameters."""
        response = test_client.get(
            "/api/v1/forecast/solar/history",
            params={"limit": 10, "offset": 0},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["limit"] == 10
        assert data["data"]["offset"] == 0

    @pytest.mark.skipif(
        True,  # Skip if database is not available
        reason="Requires database connection",
    )
    def test_voltage_history_success(
        self,
        test_client: TestClient,
    ):
        """Test voltage forecast history endpoint."""
        response = test_client.get("/api/v1/forecast/voltage/prosumer/prosumer1")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["prosumer_id"] == "prosumer1"

    @pytest.mark.skipif(
        True,  # Skip if database is not available
        reason="Requires database connection",
    )
    def test_voltage_history_with_pagination(
        self,
        test_client: TestClient,
    ):
        """Test voltage history with pagination parameters."""
        response = test_client.get(
            "/api/v1/forecast/voltage/prosumer/prosumer1",
            params={"limit": 10, "offset": 0},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["limit"] == 10
        assert data["data"]["offset"] == 0


class TestCacheStats:
    """Tests for cache statistics endpoint."""

    def test_cache_stats_admin_access(
        self,
        test_client: TestClient,
        mock_admin_user: CurrentUser,
    ):
        """Test that admin can access cache stats."""
        response = test_client.get("/api/v1/forecast/cache/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data


class TestForecastAuthentication:
    """Tests for forecast endpoint authentication."""

    def test_solar_forecast_without_auth_when_disabled(
        self,
        test_client: TestClient,
        sample_solar_request: dict,
    ):
        """Test solar forecast works when auth is disabled (default)."""
        # Auth is disabled by default in development
        response = test_client.post(
            "/api/v1/forecast/solar",
            json=sample_solar_request,
        )
        assert response.status_code == 200

    def test_voltage_forecast_without_auth_when_disabled(
        self,
        test_client: TestClient,
        sample_voltage_request: dict,
    ):
        """Test voltage forecast works when auth is disabled (default)."""
        response = test_client.post(
            "/api/v1/forecast/voltage",
            json=sample_voltage_request,
        )
        assert response.status_code == 200


class TestForecastValidation:
    """Tests for request validation."""

    def test_solar_missing_features(
        self,
        test_client: TestClient,
    ):
        """Test solar forecast with missing features."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "station_id": "POC_STATION_1",
            "horizon_minutes": 60,
            "features": {
                "pyrano1": 800.0,
                # Missing other required fields
            },
        }

        response = test_client.post("/api/v1/forecast/solar", json=request)
        assert response.status_code == 422

    def test_voltage_empty_prosumer_list(
        self,
        test_client: TestClient,
    ):
        """Test voltage forecast with empty prosumer list."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "prosumer_ids": [],
            "horizon_minutes": 15,
        }

        response = test_client.post("/api/v1/forecast/voltage", json=request)
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["predictions"] == []

    def test_solar_invalid_horizon(
        self,
        test_client: TestClient,
        sample_solar_features: dict,
    ):
        """Test solar forecast with invalid horizon."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "station_id": "POC_STATION_1",
            "horizon_minutes": 10000,  # Too large
            "features": sample_solar_features,
        }

        response = test_client.post("/api/v1/forecast/solar", json=request)
        assert response.status_code == 422
