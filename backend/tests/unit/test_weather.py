"""
Unit tests for weather handling endpoints.

Tests cover:
- Weather alerts from TMD
- Weather condition classification
- Ramp rate monitoring
- Clear sky irradiance calculation
- Weather event logging
"""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient


class TestWeatherAlerts:
    """Tests for weather alerts endpoint."""

    def test_get_weather_alerts_success(self, test_client: TestClient):
        """Test successful retrieval of weather alerts."""
        response = test_client.get("/api/v1/weather/alerts")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert "alerts" in data["data"]
        assert "count" in data["data"]
        assert "timestamp" in data["data"]

    def test_get_weather_alerts_with_region_filter(self, test_client: TestClient):
        """Test weather alerts filtered by region."""
        response = test_client.get(
            "/api/v1/weather/alerts",
            params={"region": "Central Thailand"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_get_weather_alerts_with_severity_filter(self, test_client: TestClient):
        """Test weather alerts filtered by severity."""
        for severity in ["info", "warning", "critical"]:
            response = test_client.get(
                "/api/v1/weather/alerts",
                params={"severity": severity},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"


class TestWeatherCondition:
    """Tests for weather condition endpoint."""

    def test_get_weather_condition_default_location(self, test_client: TestClient):
        """Test weather condition for default Bangkok location."""
        response = test_client.get("/api/v1/weather/condition")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert "condition" in data["data"]

    def test_get_weather_condition_with_coordinates(self, test_client: TestClient):
        """Test weather condition with custom coordinates."""
        response = test_client.get(
            "/api/v1/weather/condition",
            params={"latitude": 13.7563, "longitude": 100.5018},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_weather_condition_valid_values(self, test_client: TestClient):
        """Test that weather condition returns valid enum values."""
        response = test_client.get("/api/v1/weather/condition")

        assert response.status_code == 200
        data = response.json()
        valid_conditions = ["clear", "partly_cloudy", "cloudy", "rainy", "storm"]
        assert data["data"]["condition"] in valid_conditions


class TestRampRateMonitoring:
    """Tests for ramp rate monitoring endpoints."""

    def test_get_current_ramp_rate(self, test_client: TestClient):
        """Test current ramp rate status."""
        response = test_client.get("/api/v1/weather/ramp-rate/current")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert "current_ramp_rate_percent" in data["data"]
        assert "threshold_percent" in data["data"]
        assert "is_alert" in data["data"]
        assert "timestamp" in data["data"]

    def test_ramp_rate_threshold_value(self, test_client: TestClient):
        """Test that ramp rate threshold is reasonable."""
        response = test_client.get("/api/v1/weather/ramp-rate/current")

        assert response.status_code == 200
        data = response.json()
        # Default threshold should be 30%
        assert data["data"]["threshold_percent"] == 30.0

    def test_get_ramp_rate_events(self, test_client: TestClient):
        """Test ramp rate events history."""
        response = test_client.get("/api/v1/weather/ramp-rate/events")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "events" in data["data"]
        assert "count" in data["data"]

    def test_get_ramp_rate_events_with_limit(self, test_client: TestClient):
        """Test ramp rate events with limit parameter."""
        response = test_client.get(
            "/api/v1/weather/ramp-rate/events",
            params={"limit": 5},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["data"]["events"]) <= 5


class TestClearSkyIrradiance:
    """Tests for clear sky irradiance calculation."""

    def test_get_clear_sky_irradiance_default(self, test_client: TestClient):
        """Test clear sky irradiance with default parameters."""
        response = test_client.get("/api/v1/weather/clear-sky")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "clear_sky_irradiance" in data["data"]
        assert "unit" in data["data"]
        assert data["data"]["unit"] == "W/m²"

    def test_get_clear_sky_irradiance_with_coordinates(self, test_client: TestClient):
        """Test clear sky irradiance with custom coordinates."""
        response = test_client.get(
            "/api/v1/weather/clear-sky",
            params={
                "latitude": 13.7563,
                "longitude": 100.5018,
                "altitude": 10,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "clear_sky_irradiance" in data["data"]
        assert data["data"]["latitude"] == 13.7563
        assert data["data"]["longitude"] == 100.5018
        assert data["data"]["altitude"] == 10

    def test_clear_sky_irradiance_non_negative(self, test_client: TestClient):
        """Test that clear sky irradiance is non-negative."""
        response = test_client.get("/api/v1/weather/clear-sky")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["clear_sky_irradiance"] >= 0


class TestUncertaintyFactors:
    """Tests for uncertainty factor configuration."""

    def test_get_uncertainty_factors(self, test_client: TestClient):
        """Test retrieval of uncertainty factors."""
        response = test_client.get("/api/v1/weather/uncertainty-factors")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "factors" in data["data"]

    def test_uncertainty_factors_all_conditions(self, test_client: TestClient):
        """Test that all weather conditions have factors."""
        response = test_client.get("/api/v1/weather/uncertainty-factors")

        assert response.status_code == 200
        factors = response.json()["data"]["factors"]

        expected_conditions = ["clear", "partly_cloudy", "cloudy", "rainy", "storm"]
        for condition in expected_conditions:
            assert condition in factors
            assert factors[condition] >= 1.0  # Multipliers should be >= 1

    def test_uncertainty_factors_ordering(self, test_client: TestClient):
        """Test that uncertainty increases with adverse weather."""
        response = test_client.get("/api/v1/weather/uncertainty-factors")

        assert response.status_code == 200
        factors = response.json()["data"]["factors"]

        # Uncertainty should increase: clear < partly_cloudy < cloudy < rainy < storm
        assert factors["clear"] <= factors["partly_cloudy"]
        assert factors["partly_cloudy"] <= factors["cloudy"]
        assert factors["cloudy"] <= factors["rainy"]
        assert factors["rainy"] <= factors["storm"]


class TestWeatherClassification:
    """Tests for weather classification endpoint."""

    def test_classify_weather_clear(self, test_client: TestClient):
        """Test classification of clear weather."""
        response = test_client.post(
            "/api/v1/weather/classify",
            params={
                "clearness_index": 0.8,
                "precipitation_mm": 0,
                "wind_speed_kmh": 10,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["condition"] == "clear"

    def test_classify_weather_rainy(self, test_client: TestClient):
        """Test classification of rainy weather."""
        response = test_client.post(
            "/api/v1/weather/classify",
            params={
                "clearness_index": 0.2,
                "precipitation_mm": 5,
                "wind_speed_kmh": 15,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["condition"] == "rainy"

    def test_classify_weather_storm(self, test_client: TestClient):
        """Test classification of storm weather."""
        response = test_client.post(
            "/api/v1/weather/classify",
            params={
                "precipitation_mm": 25,
                "wind_speed_kmh": 70,
                "has_storm_alert": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["condition"] == "storm"

    def test_classify_weather_returns_inputs(self, test_client: TestClient):
        """Test that classification returns input values."""
        response = test_client.post(
            "/api/v1/weather/classify",
            params={
                "clearness_index": 0.6,
                "precipitation_mm": 2,
                "wind_speed_kmh": 20,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "inputs" in data["data"]
        assert data["data"]["inputs"]["clearness_index"] == 0.6
        assert data["data"]["inputs"]["precipitation_mm"] == 2
        assert data["data"]["inputs"]["wind_speed_kmh"] == 20


class TestWeatherEvents:
    """Tests for historical weather events endpoint."""

    def test_get_weather_events_default(self, test_client: TestClient):
        """Test retrieval of weather events with defaults."""
        response = test_client.get("/api/v1/weather/events")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "events" in data["data"]
        assert "count" in data["data"]
        assert "start_date" in data["data"]
        assert "end_date" in data["data"]

    def test_get_weather_events_with_limit(self, test_client: TestClient):
        """Test weather events with limit."""
        response = test_client.get(
            "/api/v1/weather/events",
            params={"limit": 50},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_get_weather_events_with_type_filter(self, test_client: TestClient):
        """Test weather events filtered by type."""
        response = test_client.get(
            "/api/v1/weather/events",
            params={"event_type": "storm"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
