"""
Unit tests for audit log endpoints.

Tests the /api/v1/audit endpoints per TOR 7.1.6 requirements.
"""

from datetime import datetime, timedelta

from fastapi.testclient import TestClient


class TestGetAuditLogs:
    """Tests for GET /api/v1/audit/logs"""

    def test_get_audit_logs_success(self, test_client: TestClient):
        """Test getting audit logs returns success."""
        response = test_client.get("/api/v1/audit/logs")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "logs" in data["data"]
        assert "count" in data["data"]
        assert isinstance(data["data"]["logs"], list)

    def test_get_audit_logs_with_pagination(self, test_client: TestClient):
        """Test getting audit logs with pagination parameters."""
        response = test_client.get(
            "/api/v1/audit/logs", params={"skip": 10, "limit": 50}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["skip"] == 10
        assert data["data"]["limit"] == 50

    def test_get_audit_logs_with_user_filter(self, test_client: TestClient):
        """Test filtering audit logs by user ID."""
        response = test_client.get(
            "/api/v1/audit/logs", params={"user_id": "test-user-123"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "user_id" in data["data"]["filters"]

    def test_get_audit_logs_with_action_filter(self, test_client: TestClient):
        """Test filtering audit logs by action type."""
        response = test_client.get("/api/v1/audit/logs", params={"action": "read"})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["filters"]["action"] == "read"

    def test_get_audit_logs_with_resource_filter(self, test_client: TestClient):
        """Test filtering audit logs by resource type."""
        response = test_client.get(
            "/api/v1/audit/logs", params={"resource_type": "forecast"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["filters"]["resource_type"] == "forecast"

    def test_get_audit_logs_with_date_range(self, test_client: TestClient):
        """Test filtering audit logs by date range."""
        start_date = (datetime.now() - timedelta(days=7)).isoformat()
        end_date = datetime.now().isoformat()

        response = test_client.get(
            "/api/v1/audit/logs",
            params={"start_date": start_date, "end_date": end_date},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_get_audit_logs_with_status_filter(self, test_client: TestClient):
        """Test filtering audit logs by response status."""
        response = test_client.get(
            "/api/v1/audit/logs", params={"response_status": 200}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["filters"]["response_status"] == 200

    def test_get_audit_logs_limit_validation(self, test_client: TestClient):
        """Test that limit parameter is validated."""
        response = test_client.get("/api/v1/audit/logs", params={"limit": 2000})

        # Should return validation error or cap at max
        assert response.status_code in [200, 422]

    def test_get_audit_logs_with_multiple_filters(self, test_client: TestClient):
        """Test combining multiple filters."""
        response = test_client.get(
            "/api/v1/audit/logs",
            params={
                "action": "create",
                "resource_type": "forecast",
                "request_method": "POST",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestGetAuditLogById:
    """Tests for GET /api/v1/audit/logs/{log_id}"""

    def test_get_audit_log_by_id_requires_time(self, test_client: TestClient):
        """Test that getting log by ID requires time parameter."""
        response = test_client.get("/api/v1/audit/logs/1")

        # Should fail without time parameter (for hypertable partitioning)
        assert response.status_code == 422

    def test_get_audit_log_by_id_with_time(self, test_client: TestClient):
        """Test getting audit log by ID with time parameter."""
        time = datetime.now().isoformat()
        response = test_client.get("/api/v1/audit/logs/1", params={"time": time})

        # Will return 404 if log doesn't exist, or 200 if it does
        assert response.status_code in [200, 404]

    def test_get_audit_log_by_id_not_found(self, test_client: TestClient):
        """Test getting non-existent audit log."""
        time = (datetime.now() - timedelta(days=365)).isoformat()
        response = test_client.get("/api/v1/audit/logs/999999", params={"time": time})

        # Should return 404 for non-existent log
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data


class TestGetUserActivity:
    """Tests for GET /api/v1/audit/users/{user_id}/activity"""

    def test_get_user_activity_default_period(self, test_client: TestClient):
        """Test getting user activity with default period."""
        response = test_client.get("/api/v1/audit/users/test-user/activity")

        # Will return 404 if no activity, or 200 if activity exists
        assert response.status_code in [200, 404]

    def test_get_user_activity_custom_period(self, test_client: TestClient):
        """Test getting user activity with custom period."""
        response = test_client.get(
            "/api/v1/audit/users/test-user/activity", params={"days": 7}
        )

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert data["data"]["period_days"] == 7

    def test_get_user_activity_structure(self, test_client: TestClient):
        """Test user activity response structure when activity exists."""
        response = test_client.get("/api/v1/audit/users/test-user/activity")

        if response.status_code == 200:
            data = response.json()
            activity = data["data"]["activity"]
            assert "user_id" in activity
            assert "total_requests" in activity
            assert "last_activity" in activity
            assert "actions_breakdown" in activity
            assert "most_accessed_resources" in activity
            assert "failed_requests" in activity
            assert "avg_requests_per_day" in activity

    def test_get_user_activity_days_validation(self, test_client: TestClient):
        """Test days parameter validation."""
        response = test_client.get(
            "/api/v1/audit/users/test-user/activity", params={"days": 400}
        )

        # Should return validation error for days > 365
        assert response.status_code == 422


class TestGetAuditStats:
    """Tests for GET /api/v1/audit/stats"""

    def test_get_audit_stats_default_period(self, test_client: TestClient):
        """Test getting audit stats with default period (7 days)."""
        response = test_client.get("/api/v1/audit/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "stats" in data["data"]

    def test_get_audit_stats_custom_period(self, test_client: TestClient):
        """Test getting audit stats with custom date range."""
        start_date = (datetime.now() - timedelta(days=30)).isoformat()
        end_date = datetime.now().isoformat()

        response = test_client.get(
            "/api/v1/audit/stats",
            params={"start_date": start_date, "end_date": end_date},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_audit_stats_structure(self, test_client: TestClient):
        """Test that audit stats have correct structure."""
        response = test_client.get("/api/v1/audit/stats")

        assert response.status_code == 200
        stats = response.json()["data"]["stats"]
        assert "total_requests" in stats
        assert "unique_users" in stats
        assert "successful_requests" in stats
        assert "failed_requests" in stats
        assert "actions_breakdown" in stats
        assert "resources_breakdown" in stats
        assert "top_users" in stats
        assert "error_rate" in stats
        assert "period_start" in stats
        assert "period_end" in stats

    def test_audit_stats_error_rate_calculation(self, test_client: TestClient):
        """Test that error rate is calculated correctly."""
        response = test_client.get("/api/v1/audit/stats")

        assert response.status_code == 200
        stats = response.json()["data"]["stats"]
        error_rate = stats["error_rate"]

        # Error rate should be between 0 and 100
        assert 0 <= error_rate <= 100
        assert isinstance(error_rate, int | float)


class TestExportAuditLogs:
    """Tests for POST /api/v1/audit/export"""

    def test_export_audit_logs_csv(self, test_client: TestClient):
        """Test exporting audit logs to CSV format."""
        response = test_client.post(
            "/api/v1/audit/export",
            json={"format": "csv", "include_request_body": False},
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "audit_logs_" in response.headers["content-disposition"]

    def test_export_audit_logs_json(self, test_client: TestClient):
        """Test exporting audit logs to JSON format."""
        response = test_client.post("/api/v1/audit/export", json={"format": "json"})

        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]
        assert "audit_logs_" in response.headers["content-disposition"]

    def test_export_audit_logs_with_filters(self, test_client: TestClient):
        """Test exporting audit logs with filters applied."""
        start_date = (datetime.now() - timedelta(days=7)).isoformat()
        end_date = datetime.now().isoformat()

        response = test_client.post(
            "/api/v1/audit/export",
            json={
                "format": "csv",
                "filters": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "action": "read",
                },
            },
        )

        assert response.status_code == 200

    def test_export_audit_logs_with_request_body(self, test_client: TestClient):
        """Test exporting with request body included."""
        response = test_client.post(
            "/api/v1/audit/export",
            json={"format": "csv", "include_request_body": True},
        )

        assert response.status_code == 200

    def test_export_audit_logs_invalid_format(self, test_client: TestClient):
        """Test that invalid export format returns error."""
        response = test_client.post("/api/v1/audit/export", json={"format": "xml"})

        assert response.status_code == 400
        data = response.json()
        assert "Unsupported export format" in data["detail"]


class TestGetRecentAuditLogs:
    """Tests for GET /api/v1/audit/recent"""

    def test_get_recent_audit_logs_default(self, test_client: TestClient):
        """Test getting recent logs with default parameters."""
        response = test_client.get("/api/v1/audit/recent")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "logs" in data["data"]
        assert data["data"]["period_hours"] == 24

    def test_get_recent_audit_logs_custom_hours(self, test_client: TestClient):
        """Test getting recent logs with custom hours."""
        response = test_client.get("/api/v1/audit/recent", params={"hours": 48})

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["period_hours"] == 48

    def test_get_recent_audit_logs_custom_limit(self, test_client: TestClient):
        """Test getting recent logs with custom limit."""
        response = test_client.get(
            "/api/v1/audit/recent", params={"hours": 12, "limit": 50}
        )

        assert response.status_code == 200


class TestGetAuditTimeline:
    """Tests for GET /api/v1/audit/timeline"""

    def test_get_audit_timeline_default(self, test_client: TestClient):
        """Test getting audit timeline with defaults."""
        response = test_client.get("/api/v1/audit/timeline")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "timeline" in data["data"]
        assert "period_hours" in data["data"]
        assert "interval" in data["data"]

    def test_get_audit_timeline_custom_interval(self, test_client: TestClient):
        """Test getting timeline with different intervals."""
        intervals = ["15m", "1h", "6h", "1d"]

        for interval in intervals:
            response = test_client.get(
                "/api/v1/audit/timeline", params={"interval": interval}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["interval"] == interval

    def test_audit_timeline_structure(self, test_client: TestClient):
        """Test timeline data structure."""
        response = test_client.get("/api/v1/audit/timeline")

        assert response.status_code == 200
        timeline = response.json()["data"]["timeline"]

        if len(timeline) > 0:
            bucket = timeline[0]
            assert "time" in bucket
            assert "total_requests" in bucket
            assert "unique_users" in bucket
            assert "failed_requests" in bucket
            assert "success_rate" in bucket
            assert "actions" in bucket


class TestGetSecurityEvents:
    """Tests for GET /api/v1/audit/security-events"""

    def test_get_security_events_default(self, test_client: TestClient):
        """Test getting security events with defaults."""
        response = test_client.get("/api/v1/audit/security-events")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "events" in data["data"]
        assert "count" in data["data"]
        assert "period_hours" in data["data"]

    def test_get_security_events_custom_hours(self, test_client: TestClient):
        """Test getting security events with custom period."""
        response = test_client.get(
            "/api/v1/audit/security-events", params={"hours": 48}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["period_hours"] == 48

    def test_security_events_structure(self, test_client: TestClient):
        """Test security events data structure."""
        response = test_client.get("/api/v1/audit/security-events")

        assert response.status_code == 200
        events = response.json()["data"]["events"]

        if len(events) > 0:
            event = events[0]
            assert "time" in event
            assert "user_ip" in event
            assert "response_status" in event
            assert "attempts_from_ip" in event
            assert "severity" in event
            assert "event_type" in event
            assert event["event_type"] == "failed_authentication"
            assert event["severity"] in ["warning", "critical"]


class TestAuditLogFiltering:
    """Integration tests for complex filtering scenarios"""

    def test_filter_by_ip_address(self, test_client: TestClient):
        """Test filtering by IP address."""
        response = test_client.get(
            "/api/v1/audit/logs", params={"user_ip": "192.168.1.1"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_filter_by_http_method(self, test_client: TestClient):
        """Test filtering by HTTP method."""
        methods = ["GET", "POST", "PUT", "DELETE"]

        for method in methods:
            response = test_client.get(
                "/api/v1/audit/logs", params={"request_method": method}
            )

            assert response.status_code == 200

    def test_combined_filters(self, test_client: TestClient):
        """Test combining multiple complex filters."""
        start_date = (datetime.now() - timedelta(days=1)).isoformat()

        response = test_client.get(
            "/api/v1/audit/logs",
            params={
                "action": "create",
                "resource_type": "forecast",
                "start_date": start_date,
                "response_status": 201,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestAuditLogPagination:
    """Tests for pagination behavior"""

    def test_pagination_first_page(self, test_client: TestClient):
        """Test getting first page of results."""
        response = test_client.get(
            "/api/v1/audit/logs", params={"skip": 0, "limit": 10}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["logs"]) <= 10

    def test_pagination_second_page(self, test_client: TestClient):
        """Test getting second page of results."""
        response = test_client.get(
            "/api/v1/audit/logs", params={"skip": 10, "limit": 10}
        )

        assert response.status_code == 200

    def test_pagination_large_skip(self, test_client: TestClient):
        """Test pagination with large skip value."""
        response = test_client.get(
            "/api/v1/audit/logs", params={"skip": 1000, "limit": 10}
        )

        assert response.status_code == 200
        data = response.json()
        # Should return empty if beyond available data
        assert isinstance(data["data"]["logs"], list)
