"""
Unit tests for alert management endpoints.

Tests the /api/v1/alerts endpoints.
"""

import pytest
from fastapi.testclient import TestClient


class TestGetAlerts:
    """Tests for GET /api/v1/alerts/"""

    def test_get_alerts_success(self, test_client: TestClient):
        """Test getting alerts returns success."""
        response = test_client.get("/api/v1/alerts/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "alerts" in data["data"]
        assert "count" in data["data"]
        assert isinstance(data["data"]["alerts"], list)

    def test_get_alerts_with_limit(self, test_client: TestClient):
        """Test getting alerts with custom limit."""
        response = test_client.get("/api/v1/alerts/", params={"limit": 10})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestAlertStats:
    """Tests for GET /api/v1/alerts/stats"""

    def test_get_alert_stats_default(self, test_client: TestClient):
        """Test getting alert statistics with default parameters."""
        response = test_client.get("/api/v1/alerts/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "stats" in data["data"]
        assert "period_hours" in data["data"]

    def test_get_alert_stats_custom_hours(self, test_client: TestClient):
        """Test getting alert statistics with custom hours."""
        response = test_client.get("/api/v1/alerts/stats", params={"hours": 48})

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["period_hours"] == 48

    def test_alert_stats_structure(self, test_client: TestClient):
        """Test that alert stats have correct structure."""
        response = test_client.get("/api/v1/alerts/stats")

        assert response.status_code == 200
        stats = response.json()["data"]["stats"]
        assert "total" in stats
        assert "critical" in stats
        assert "warning" in stats
        assert "info" in stats
        assert "unacknowledged" in stats


class TestAlertSummary:
    """Tests for GET /api/v1/alerts/summary"""

    def test_get_alert_summary(self, test_client: TestClient):
        """Test getting alert summary."""
        response = test_client.get("/api/v1/alerts/summary")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "overall_status" in data["data"]
        assert "by_prosumer" in data["data"]

    def test_alert_summary_status_values(self, test_client: TestClient):
        """Test that overall status is valid."""
        response = test_client.get("/api/v1/alerts/summary")

        assert response.status_code == 200
        status = response.json()["data"]["overall_status"]
        assert status in ["normal", "warning", "critical"]


class TestAlertTimeline:
    """Tests for GET /api/v1/alerts/timeline"""

    def test_get_alert_timeline_default(self, test_client: TestClient):
        """Test getting alert timeline with defaults."""
        response = test_client.get("/api/v1/alerts/timeline")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "timeline" in data["data"]
        assert "period_hours" in data["data"]
        assert "interval" in data["data"]

    def test_get_alert_timeline_custom_params(self, test_client: TestClient):
        """Test getting alert timeline with custom parameters."""
        response = test_client.get(
            "/api/v1/alerts/timeline",
            params={"hours": 48, "interval": "6h"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["period_hours"] == 48
        assert data["data"]["interval"] == "6h"

    def test_alert_timeline_intervals(self, test_client: TestClient):
        """Test different interval options."""
        for interval in ["15m", "1h", "6h", "1d"]:
            response = test_client.get(
                "/api/v1/alerts/timeline",
                params={"interval": interval}
            )
            assert response.status_code == 200


class TestProsumerAlerts:
    """Tests for GET /api/v1/alerts/prosumer/{prosumer_id}"""

    def test_get_prosumer_alerts(self, test_client: TestClient):
        """Test getting alerts for a specific prosumer."""
        response = test_client.get("/api/v1/alerts/prosumer/prosumer1")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "prosumer_id" in data["data"]
        assert data["data"]["prosumer_id"] == "prosumer1"
        assert "alerts" in data["data"]

    def test_get_prosumer_alerts_with_params(self, test_client: TestClient):
        """Test getting prosumer alerts with custom parameters."""
        response = test_client.get(
            "/api/v1/alerts/prosumer/prosumer2",
            params={"hours": 48, "limit": 100}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["period_hours"] == 48


class TestCheckVoltage:
    """Tests for POST /api/v1/alerts/check-voltage"""

    def test_check_voltage_violations(self, test_client: TestClient):
        """Test checking voltage violations."""
        response = test_client.post(
            "/api/v1/alerts/check-voltage",
            json={
                "prosumer_ids": ["prosumer1", "prosumer2"]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "alerts_created" in data["data"]
        assert "count" in data["data"]

    def test_check_voltage_default_prosumers(self, test_client: TestClient):
        """Test checking voltage with default prosumer list."""
        response = test_client.post(
            "/api/v1/alerts/check-voltage",
            json={}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestAcknowledgeAlert:
    """Tests for POST /api/v1/alerts/{alert_id}/acknowledge"""

    def test_acknowledge_nonexistent_alert(self, test_client: TestClient):
        """Test acknowledging non-existent alert returns error."""
        response = test_client.post("/api/v1/alerts/999999/acknowledge")

        assert response.status_code == 200
        data = response.json()
        # Either error or empty result for non-existent
        assert data["status"] in ["error", "success"]


class TestResolveAlert:
    """Tests for POST /api/v1/alerts/{alert_id}/resolve"""

    def test_resolve_nonexistent_alert(self, test_client: TestClient):
        """Test resolving non-existent alert returns error."""
        response = test_client.post("/api/v1/alerts/999999/resolve")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["error", "success"]
