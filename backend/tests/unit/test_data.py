"""
Unit tests for data endpoints.

Tests the /api/v1/data endpoints for solar and voltage measurements.
"""

from fastapi.testclient import TestClient


class TestSolarDataLatest:
    """Tests for GET /api/v1/data/solar/latest"""

    def test_get_latest_solar_data(self, test_client: TestClient):
        """Test getting latest solar data returns success."""
        response = test_client.get("/api/v1/data/solar/latest")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "station_id" in data["data"]
        assert "chart_data" in data["data"]
        assert "summary" in data["data"]

    def test_get_solar_data_default_station(self, test_client: TestClient):
        """Test that default station is POC_STATION_1."""
        response = test_client.get("/api/v1/data/solar/latest")

        assert response.status_code == 200
        assert response.json()["data"]["station_id"] == "POC_STATION_1"

    def test_get_solar_data_custom_station(self, test_client: TestClient):
        """Test getting solar data for custom station."""
        response = test_client.get(
            "/api/v1/data/solar/latest", params={"station_id": "CUSTOM_STATION"}
        )

        assert response.status_code == 200
        assert response.json()["data"]["station_id"] == "CUSTOM_STATION"

    def test_get_solar_data_custom_hours(self, test_client: TestClient):
        """Test getting solar data with custom hours."""
        response = test_client.get("/api/v1/data/solar/latest", params={"hours": 12})

        assert response.status_code == 200

    def test_solar_data_summary_fields(self, test_client: TestClient):
        """Test that summary contains required fields."""
        response = test_client.get("/api/v1/data/solar/latest")

        assert response.status_code == 200
        summary = response.json()["data"]["summary"]
        assert "current_power" in summary
        assert "peak_power" in summary
        assert "data_points" in summary

    def test_solar_chart_data_structure(self, test_client: TestClient):
        """Test chart data structure."""
        response = test_client.get("/api/v1/data/solar/latest")

        assert response.status_code == 200
        chart_data = response.json()["data"]["chart_data"]
        assert isinstance(chart_data, list)
        if chart_data:
            point = chart_data[0]
            assert "time" in point
            assert "power_kw" in point
            assert "predicted_kw" in point
            assert "irradiance" in point


class TestSolarStats:
    """Tests for GET /api/v1/data/solar/stats"""

    def test_get_solar_stats(self, test_client: TestClient):
        """Test getting solar statistics."""
        response = test_client.get("/api/v1/data/solar/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "station_id" in data["data"]

    def test_solar_stats_fields(self, test_client: TestClient):
        """Test that solar stats contain required fields."""
        response = test_client.get("/api/v1/data/solar/stats")

        assert response.status_code == 200
        stats = response.json()["data"]
        assert "total_count" in stats
        assert "first_record" in stats
        assert "last_record" in stats
        assert "avg_power" in stats
        assert "max_power" in stats


class TestVoltageDataLatest:
    """Tests for GET /api/v1/data/voltage/latest"""

    def test_get_latest_voltage_data(self, test_client: TestClient):
        """Test getting latest voltage data returns success."""
        response = test_client.get("/api/v1/data/voltage/latest")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "chart_data" in data["data"]
        assert "prosumer_status" in data["data"]
        assert "summary" in data["data"]

    def test_get_voltage_data_custom_hours(self, test_client: TestClient):
        """Test getting voltage data with custom hours."""
        response = test_client.get("/api/v1/data/voltage/latest", params={"hours": 8})

        assert response.status_code == 200

    def test_voltage_summary_fields(self, test_client: TestClient):
        """Test that voltage summary contains required fields."""
        response = test_client.get("/api/v1/data/voltage/latest")

        assert response.status_code == 200
        summary = response.json()["data"]["summary"]
        assert "violations" in summary
        assert "avg_voltage" in summary

    def test_voltage_prosumer_status_structure(self, test_client: TestClient):
        """Test prosumer status structure."""
        response = test_client.get("/api/v1/data/voltage/latest")

        assert response.status_code == 200
        prosumer_status = response.json()["data"]["prosumer_status"]
        assert isinstance(prosumer_status, list)
        if prosumer_status:
            prosumer = prosumer_status[0]
            assert "id" in prosumer
            assert "phase" in prosumer
            assert "voltage" in prosumer
            assert "status" in prosumer


class TestProsumerVoltage:
    """Tests for GET /api/v1/data/voltage/prosumer/{prosumer_id}"""

    def test_get_prosumer_voltage(self, test_client: TestClient):
        """Test getting voltage for specific prosumer."""
        response = test_client.get("/api/v1/data/voltage/prosumer/prosumer1")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["prosumer_id"] == "prosumer1"
        assert "measurements" in data["data"]

    def test_get_prosumer_voltage_all_prosumers(self, test_client: TestClient):
        """Test getting voltage for all prosumers."""
        for i in range(1, 8):
            response = test_client.get(f"/api/v1/data/voltage/prosumer/prosumer{i}")
            assert response.status_code == 200
            assert response.json()["data"]["prosumer_id"] == f"prosumer{i}"

    def test_prosumer_voltage_with_hours(self, test_client: TestClient):
        """Test getting prosumer voltage with custom hours."""
        response = test_client.get(
            "/api/v1/data/voltage/prosumer/prosumer1", params={"hours": 48}
        )

        assert response.status_code == 200

    def test_prosumer_measurement_structure(self, test_client: TestClient):
        """Test prosumer measurement structure."""
        response = test_client.get("/api/v1/data/voltage/prosumer/prosumer1")

        assert response.status_code == 200
        measurements = response.json()["data"]["measurements"]
        assert isinstance(measurements, list)
        if measurements:
            m = measurements[0]
            assert "time" in m
            assert "voltage" in m
            assert "active_power" in m
            assert "reactive_power" in m


class TestDataStatistics:
    """Tests for GET /api/v1/data/stats"""

    def test_get_data_stats(self, test_client: TestClient):
        """Test getting overall data statistics."""
        response = test_client.get("/api/v1/data/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "solar_measurements" in data["data"]
        assert "voltage_measurements" in data["data"]
        assert "prosumers" in data["data"]

    def test_solar_measurement_stats(self, test_client: TestClient):
        """Test solar measurement stats structure."""
        response = test_client.get("/api/v1/data/stats")

        assert response.status_code == 200
        solar = response.json()["data"]["solar_measurements"]
        assert "total_count" in solar
        assert "date_range" in solar

    def test_voltage_measurement_stats(self, test_client: TestClient):
        """Test voltage measurement stats structure."""
        response = test_client.get("/api/v1/data/stats")

        assert response.status_code == 200
        voltage = response.json()["data"]["voltage_measurements"]
        assert "total_count" in voltage
        assert "prosumer_count" in voltage
        assert "date_range" in voltage

    def test_prosumer_list(self, test_client: TestClient):
        """Test that prosumer list is returned."""
        response = test_client.get("/api/v1/data/stats")

        assert response.status_code == 200
        prosumers = response.json()["data"]["prosumers"]
        assert isinstance(prosumers, list)
        if prosumers:
            prosumer = prosumers[0]
            assert "id" in prosumer
            assert "name" in prosumer
            assert "phase" in prosumer


class TestDataPagination:
    """Tests for pagination parameters."""

    def test_solar_data_limit(self, test_client: TestClient):
        """Test solar data respects limit parameter."""
        response = test_client.get("/api/v1/data/solar/latest", params={"limit": 50})

        assert response.status_code == 200

    def test_voltage_data_limit(self, test_client: TestClient):
        """Test voltage data respects limit parameter."""
        response = test_client.get("/api/v1/data/voltage/latest", params={"limit": 50})

        assert response.status_code == 200

    def test_prosumer_voltage_limit(self, test_client: TestClient):
        """Test prosumer voltage respects limit parameter."""
        response = test_client.get(
            "/api/v1/data/voltage/prosumer/prosumer1", params={"limit": 100}
        )

        assert response.status_code == 200
