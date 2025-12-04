"""
Unit tests for network topology endpoints.

Tests the /api/v1/topology endpoints.
"""

import pytest
from fastapi.testclient import TestClient


class TestGetNetworkTopology:
    """Tests for GET /api/v1/topology/"""

    def test_get_topology_success(self, test_client: TestClient):
        """Test getting network topology returns success."""
        response = test_client.get("/api/v1/topology/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "transformer" in data["data"]
        assert "phases" in data["data"]
        assert "summary" in data["data"]
        assert "limits" in data["data"]

    def test_get_topology_transformer_info(self, test_client: TestClient):
        """Test that transformer information is included."""
        response = test_client.get("/api/v1/topology/")

        assert response.status_code == 200
        transformer = response.json()["data"]["transformer"]
        assert "id" in transformer
        assert "capacity_kva" in transformer
        assert "voltage_primary" in transformer
        assert "voltage_secondary" in transformer

    def test_get_topology_phases(self, test_client: TestClient):
        """Test that all three phases are included."""
        response = test_client.get("/api/v1/topology/")

        assert response.status_code == 200
        phases = response.json()["data"]["phases"]
        assert len(phases) == 3
        phase_names = [p["phase"] for p in phases]
        assert "A" in phase_names
        assert "B" in phase_names
        assert "C" in phase_names

    def test_get_topology_without_voltage(self, test_client: TestClient):
        """Test getting topology without voltage data."""
        response = test_client.get(
            "/api/v1/topology/",
            params={"include_voltage": False}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_get_topology_voltage_limits(self, test_client: TestClient):
        """Test that voltage limits are correctly set per TOR."""
        response = test_client.get("/api/v1/topology/")

        assert response.status_code == 200
        limits = response.json()["data"]["limits"]
        assert limits["nominal"] == 230.0
        assert limits["upper_limit"] == 242.0  # +5%
        assert limits["lower_limit"] == 218.0  # -5%

    def test_get_topology_summary_stats(self, test_client: TestClient):
        """Test that summary statistics are included."""
        response = test_client.get("/api/v1/topology/")

        assert response.status_code == 200
        summary = response.json()["data"]["summary"]
        assert "total_prosumers" in summary
        assert "prosumers_with_pv" in summary
        assert "prosumers_with_ev" in summary
        assert "voltage_stats" in summary


class TestGetProsumerDetails:
    """Tests for GET /api/v1/topology/prosumer/{prosumer_id}"""

    def test_get_prosumer_details(self, test_client: TestClient):
        """Test getting prosumer details."""
        response = test_client.get("/api/v1/topology/prosumer/prosumer1")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "prosumer" in data["data"]
        assert "measurements" in data["data"]

    def test_get_prosumer_details_info(self, test_client: TestClient):
        """Test that prosumer info is correctly returned."""
        response = test_client.get("/api/v1/topology/prosumer/prosumer1")

        assert response.status_code == 200
        prosumer = response.json()["data"]["prosumer"]
        assert prosumer["id"] == "prosumer1"
        assert "phase" in prosumer
        assert "has_pv" in prosumer
        assert "has_ev" in prosumer
        assert "voltage_status" in prosumer

    def test_get_nonexistent_prosumer(self, test_client: TestClient):
        """Test getting non-existent prosumer returns error."""
        response = test_client.get("/api/v1/topology/prosumer/nonexistent")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert "not found" in data["data"]["message"]

    def test_get_prosumer_with_hours_param(self, test_client: TestClient):
        """Test getting prosumer with custom hours."""
        response = test_client.get(
            "/api/v1/topology/prosumer/prosumer2",
            params={"hours": 48}
        )

        assert response.status_code == 200


class TestGetPhaseDetails:
    """Tests for GET /api/v1/topology/phases/{phase}"""

    def test_get_phase_a_details(self, test_client: TestClient):
        """Test getting Phase A details."""
        response = test_client.get("/api/v1/topology/phases/A")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["phase"] == "A"
        assert "prosumers" in data["data"]
        assert "summary" in data["data"]

    def test_get_phase_b_details(self, test_client: TestClient):
        """Test getting Phase B details."""
        response = test_client.get("/api/v1/topology/phases/B")

        assert response.status_code == 200
        assert response.json()["data"]["phase"] == "B"

    def test_get_phase_c_details(self, test_client: TestClient):
        """Test getting Phase C details."""
        response = test_client.get("/api/v1/topology/phases/C")

        assert response.status_code == 200
        assert response.json()["data"]["phase"] == "C"

    def test_get_phase_lowercase(self, test_client: TestClient):
        """Test getting phase with lowercase letter."""
        response = test_client.get("/api/v1/topology/phases/a")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["phase"] == "A"

    def test_get_invalid_phase(self, test_client: TestClient):
        """Test getting invalid phase returns error."""
        response = test_client.get("/api/v1/topology/phases/X")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert "Invalid phase" in data["data"]["message"]

    def test_phase_prosumer_info(self, test_client: TestClient):
        """Test that phase prosumers have required info."""
        response = test_client.get("/api/v1/topology/phases/A")

        assert response.status_code == 200
        prosumers = response.json()["data"]["prosumers"]
        for prosumer in prosumers:
            assert "id" in prosumer
            assert "name" in prosumer
            assert "position" in prosumer
            assert "voltage_status" in prosumer

    def test_phase_summary_stats(self, test_client: TestClient):
        """Test that phase summary includes voltage stats."""
        response = test_client.get("/api/v1/topology/phases/A")

        assert response.status_code == 200
        summary = response.json()["data"]["summary"]
        assert "avg_voltage" in summary
        assert "min_voltage" in summary
        assert "max_voltage" in summary
        assert "total_power" in summary


class TestVoltageStatus:
    """Tests for voltage status classification."""

    def test_voltage_status_values(self, test_client: TestClient):
        """Test that voltage status is one of valid values."""
        response = test_client.get("/api/v1/topology/")

        assert response.status_code == 200
        phases = response.json()["data"]["phases"]
        valid_statuses = ["normal", "warning", "critical", "unknown"]

        for phase in phases:
            for prosumer in phase["prosumers"]:
                assert prosumer["voltage_status"] in valid_statuses
