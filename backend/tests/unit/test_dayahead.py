"""
Unit tests for day-ahead forecast endpoints.

Tests the /api/v1/dayahead endpoints.
"""

import pytest
from fastapi.testclient import TestClient


class TestSolarDayAhead:
    """Tests for GET /api/v1/dayahead/solar"""

    def test_get_solar_day_ahead(self, test_client: TestClient):
        """Test getting solar day-ahead forecast."""
        response = test_client.get("/api/v1/dayahead/solar")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "forecast_date" in data["data"]
        assert "hourly_forecasts" in data["data"]
        assert "summary" in data["data"]

    def test_solar_day_ahead_24_hours(self, test_client: TestClient):
        """Test that solar forecast has 24 hourly entries."""
        response = test_client.get("/api/v1/dayahead/solar")

        assert response.status_code == 200
        hourly = response.json()["data"]["hourly_forecasts"]
        assert len(hourly) == 24

    def test_solar_day_ahead_with_date(self, test_client: TestClient):
        """Test solar day-ahead with specific date."""
        response = test_client.get(
            "/api/v1/dayahead/solar",
            params={"target_date": "2025-01-15"}
        )

        assert response.status_code == 200
        assert response.json()["data"]["forecast_date"] == "2025-01-15"

    def test_solar_day_ahead_hourly_structure(self, test_client: TestClient):
        """Test hourly forecast structure."""
        response = test_client.get("/api/v1/dayahead/solar")

        assert response.status_code == 200
        hourly = response.json()["data"]["hourly_forecasts"]
        for entry in hourly:
            assert "hour" in entry
            assert "timestamp" in entry
            assert "predicted_power_kw" in entry
            assert "confidence_lower" in entry
            assert "confidence_upper" in entry

    def test_solar_day_ahead_summary(self, test_client: TestClient):
        """Test summary includes required stats."""
        response = test_client.get("/api/v1/dayahead/solar")

        assert response.status_code == 200
        summary = response.json()["data"]["summary"]
        assert "total_energy_kwh" in summary
        assert "peak_power_kw" in summary
        assert "peak_hour" in summary


class TestVoltageDayAhead:
    """Tests for GET /api/v1/dayahead/voltage"""

    def test_get_voltage_day_ahead(self, test_client: TestClient):
        """Test getting voltage day-ahead forecast."""
        response = test_client.get("/api/v1/dayahead/voltage")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "prosumer_forecasts" in data["data"]

    def test_voltage_day_ahead_with_prosumer(self, test_client: TestClient):
        """Test voltage day-ahead for specific prosumer."""
        response = test_client.get(
            "/api/v1/dayahead/voltage",
            params={"prosumer_id": "prosumer1"}
        )

        assert response.status_code == 200

    def test_voltage_day_ahead_summary(self, test_client: TestClient):
        """Test voltage summary includes violation info."""
        response = test_client.get("/api/v1/dayahead/voltage")

        assert response.status_code == 200
        summary = response.json()["data"]["summary"]
        assert "total_prosumers" in summary
        assert "voltage_limits" in summary


class TestDayAheadReport:
    """Tests for GET /api/v1/dayahead/report"""

    def test_get_report_json(self, test_client: TestClient):
        """Test getting day-ahead report in JSON format."""
        response = test_client.get(
            "/api/v1/dayahead/report",
            params={"format": "json"}
        )

        assert response.status_code == 200

    def test_get_report_html(self, test_client: TestClient):
        """Test getting day-ahead report in HTML format."""
        response = test_client.get(
            "/api/v1/dayahead/report",
            params={"format": "html"}
        )

        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")


class TestForecastSchedule:
    """Tests for GET /api/v1/dayahead/schedule"""

    def test_list_schedules(self, test_client: TestClient):
        """Test listing forecast schedules."""
        response = test_client.get("/api/v1/dayahead/schedule")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "schedules" in data["data"]

    def test_schedule_structure(self, test_client: TestClient):
        """Test schedule entry structure."""
        response = test_client.get("/api/v1/dayahead/schedule")

        assert response.status_code == 200
        schedules = response.json()["data"]["schedules"]
        for schedule in schedules:
            assert "id" in schedule
            assert "forecast_type" in schedule
            assert "cron" in schedule
            assert "enabled" in schedule
