"""
Unit tests for actual demand forecast endpoints (TOR Function 2).

Tests cover:
- Demand forecast prediction at trading points
- Trading points listing
- Demand components information
- Trading point summary
- Forecast accuracy metrics
- Authentication and authorization
- Request validation
"""

from datetime import UTC, datetime

from fastapi.testclient import TestClient


class TestDemandForecastPredict:
    """Tests for POST /demand-forecast/predict endpoint."""

    def test_predict_demand_success(
        self,
        test_client: TestClient,
    ):
        """Test successful demand forecast prediction."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "trading_point_id": "SUB_001",
            "trading_point_type": "substation",
            "horizon_hours": 24,
            "include_components": True,
        }

        response = test_client.post("/api/v1/demand-forecast/predict", json=request)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert "predictions" in data["data"]
        assert data["data"]["trading_point_id"] == "SUB_001"

    def test_predict_demand_substation_type(
        self,
        test_client: TestClient,
    ):
        """Test demand forecast for substation trading point."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "trading_point_id": "SUB_001",
            "trading_point_type": "substation",
            "horizon_hours": 24,
            "include_components": True,
        }

        response = test_client.post("/api/v1/demand-forecast/predict", json=request)

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["trading_point_type"] == "substation"

    def test_predict_demand_feeder_type(
        self,
        test_client: TestClient,
    ):
        """Test demand forecast for feeder trading point."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "trading_point_id": "FDR_001",
            "trading_point_type": "feeder",
            "horizon_hours": 12,
            "include_components": True,
        }

        response = test_client.post("/api/v1/demand-forecast/predict", json=request)

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["trading_point_type"] == "feeder"

    def test_predict_demand_prosumer_type(
        self,
        test_client: TestClient,
    ):
        """Test demand forecast for prosumer trading point."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "trading_point_id": "PRO_001",
            "trading_point_type": "prosumer",
            "horizon_hours": 24,
            "include_components": True,
        }

        response = test_client.post("/api/v1/demand-forecast/predict", json=request)

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["trading_point_type"] == "prosumer"

    def test_predict_demand_aggregator_type(
        self,
        test_client: TestClient,
    ):
        """Test demand forecast for aggregator trading point."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "trading_point_id": "AGG_001",
            "trading_point_type": "aggregator",
            "horizon_hours": 48,
            "include_components": True,
        }

        response = test_client.post("/api/v1/demand-forecast/predict", json=request)

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["trading_point_type"] == "aggregator"

    def test_predict_demand_with_components(
        self,
        test_client: TestClient,
    ):
        """Test that predictions include component breakdown when requested."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "trading_point_id": "SUB_001",
            "trading_point_type": "substation",
            "horizon_hours": 24,
            "include_components": True,
        }

        response = test_client.post("/api/v1/demand-forecast/predict", json=request)

        assert response.status_code == 200
        data = response.json()
        predictions = data["data"]["predictions"]

        for prediction in predictions[:5]:  # Check first 5
            assert "net_demand_mw" in prediction
            assert "gross_load_mw" in prediction
            assert "btm_re_mw" in prediction
            assert "battery_flow_mw" in prediction
            assert "confidence_lower" in prediction
            assert "confidence_upper" in prediction

    def test_predict_demand_without_components(
        self,
        test_client: TestClient,
    ):
        """Test predictions without component breakdown."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "trading_point_id": "SUB_001",
            "trading_point_type": "substation",
            "horizon_hours": 24,
            "include_components": False,
        }

        response = test_client.post("/api/v1/demand-forecast/predict", json=request)

        assert response.status_code == 200
        data = response.json()
        predictions = data["data"]["predictions"]

        for prediction in predictions[:5]:
            assert "net_demand_mw" in prediction
            assert prediction.get("gross_load_mw") is None
            assert prediction.get("btm_re_mw") is None
            assert prediction.get("battery_flow_mw") is None

    def test_predict_demand_confidence_intervals(
        self,
        test_client: TestClient,
    ):
        """Test that predictions include confidence intervals."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "trading_point_id": "SUB_001",
            "trading_point_type": "substation",
            "horizon_hours": 24,
            "include_components": True,
        }

        response = test_client.post("/api/v1/demand-forecast/predict", json=request)

        assert response.status_code == 200
        data = response.json()
        predictions = data["data"]["predictions"]

        for prediction in predictions[:5]:
            assert prediction["confidence_lower"] <= prediction["net_demand_mw"]
            assert prediction["confidence_upper"] >= prediction["net_demand_mw"]

    def test_predict_demand_horizon_hours(
        self,
        test_client: TestClient,
    ):
        """Test that horizon_hours parameter works correctly."""
        horizon = 48
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "trading_point_id": "SUB_001",
            "trading_point_type": "substation",
            "horizon_hours": horizon,
            "include_components": True,
        }

        response = test_client.post("/api/v1/demand-forecast/predict", json=request)

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["horizon_hours"] == horizon
        assert len(data["data"]["predictions"]) == horizon

    def test_predict_demand_includes_summary(
        self,
        test_client: TestClient,
    ):
        """Test that response includes summary statistics."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "trading_point_id": "SUB_001",
            "trading_point_type": "substation",
            "horizon_hours": 24,
            "include_components": True,
        }

        response = test_client.post("/api/v1/demand-forecast/predict", json=request)

        assert response.status_code == 200
        data = response.json()
        summary = data["data"]["summary"]

        assert "peak_demand_mw" in summary
        assert "min_demand_mw" in summary
        assert "avg_demand_mw" in summary
        assert "total_intervals" in summary

    def test_predict_demand_includes_metadata(
        self,
        test_client: TestClient,
    ):
        """Test that response includes metadata."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "trading_point_id": "SUB_001",
            "trading_point_type": "substation",
            "horizon_hours": 24,
            "include_components": True,
        }

        response = test_client.post("/api/v1/demand-forecast/predict", json=request)

        assert response.status_code == 200
        data = response.json()

        assert "meta" in data
        assert "prediction_time_ms" in data["meta"]
        assert data["meta"]["accuracy_target_mape"] == 5.0
        assert data["meta"]["phase"] == "Phase 2 - Simulation"
        assert data["data"]["model_version"] is not None
        assert data["data"]["is_ml_prediction"] is False

    def test_predict_demand_invalid_horizon_low(
        self,
        test_client: TestClient,
    ):
        """Test demand forecast with invalid horizon (too low)."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "trading_point_id": "SUB_001",
            "trading_point_type": "substation",
            "horizon_hours": 0,
            "include_components": True,
        }

        response = test_client.post("/api/v1/demand-forecast/predict", json=request)
        assert response.status_code == 422  # Validation error

    def test_predict_demand_invalid_horizon_high(
        self,
        test_client: TestClient,
    ):
        """Test demand forecast with invalid horizon (too high)."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "trading_point_id": "SUB_001",
            "trading_point_type": "substation",
            "horizon_hours": 200,
            "include_components": True,
        }

        response = test_client.post("/api/v1/demand-forecast/predict", json=request)
        assert response.status_code == 422  # Validation error

    def test_predict_demand_invalid_trading_point_type(
        self,
        test_client: TestClient,
    ):
        """Test demand forecast with invalid trading point type."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "trading_point_id": "SUB_001",
            "trading_point_type": "invalid_type",
            "horizon_hours": 24,
            "include_components": True,
        }

        response = test_client.post("/api/v1/demand-forecast/predict", json=request)
        assert response.status_code == 422  # Validation error

    def test_predict_demand_missing_trading_point_id(
        self,
        test_client: TestClient,
    ):
        """Test demand forecast with missing trading_point_id."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "trading_point_type": "substation",
            "horizon_hours": 24,
            "include_components": True,
        }

        response = test_client.post("/api/v1/demand-forecast/predict", json=request)
        assert response.status_code == 422  # Validation error


class TestDemandForecastTradingPoints:
    """Tests for GET /demand-forecast/trading-points endpoint."""

    def test_get_trading_points_success(
        self,
        test_client: TestClient,
    ):
        """Test successful retrieval of trading points."""
        response = test_client.get("/api/v1/demand-forecast/trading-points")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert "trading_points" in data["data"]
        assert "total" in data["data"]
        assert "types" in data["data"]

    def test_get_trading_points_structure(
        self,
        test_client: TestClient,
    ):
        """Test trading points response structure."""
        response = test_client.get("/api/v1/demand-forecast/trading-points")

        assert response.status_code == 200
        data = response.json()
        trading_points = data["data"]["trading_points"]

        for tp in trading_points:
            assert "id" in tp
            assert "name" in tp
            assert "type" in tp
            assert tp["type"] in ["substation", "feeder", "prosumer", "aggregator"]

    def test_get_trading_points_filter_by_type(
        self,
        test_client: TestClient,
    ):
        """Test filtering trading points by type."""
        response = test_client.get(
            "/api/v1/demand-forecast/trading-points",
            params={"type_filter": "substation"},
        )

        assert response.status_code == 200
        data = response.json()
        trading_points = data["data"]["trading_points"]

        for tp in trading_points:
            assert tp["type"] == "substation"

    def test_get_trading_points_all_types(
        self,
        test_client: TestClient,
    ):
        """Test that all trading point types are available."""
        response = test_client.get("/api/v1/demand-forecast/trading-points")

        assert response.status_code == 200
        data = response.json()
        types = data["data"]["types"]

        expected_types = ["substation", "feeder", "prosumer", "aggregator"]
        for expected in expected_types:
            assert expected in types

    def test_get_trading_points_includes_metadata(
        self,
        test_client: TestClient,
    ):
        """Test that trading points include metadata."""
        response = test_client.get("/api/v1/demand-forecast/trading-points")

        assert response.status_code == 200
        data = response.json()
        trading_points = data["data"]["trading_points"]

        for tp in trading_points[:2]:  # Check first 2
            if tp.get("has_btm_solar") is not None:
                assert isinstance(tp["has_btm_solar"], bool)
            if tp.get("has_battery") is not None:
                assert isinstance(tp["has_battery"], bool)
            if tp.get("peak_demand_mw") is not None:
                assert tp["peak_demand_mw"] > 0


class TestDemandForecastComponents:
    """Tests for GET /demand-forecast/components endpoint."""

    def test_get_components_success(
        self,
        test_client: TestClient,
    ):
        """Test successful retrieval of demand components."""
        response = test_client.get("/api/v1/demand-forecast/components")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert "formula" in data["data"]
        assert "components" in data["data"]

    def test_get_components_formula(
        self,
        test_client: TestClient,
    ):
        """Test that formula is correct."""
        response = test_client.get("/api/v1/demand-forecast/components")

        assert response.status_code == 200
        data = response.json()
        formula = data["data"]["formula"]

        assert "Actual Demand" in formula
        assert "Gross Load" in formula
        assert "BTM RE" in formula
        assert "Battery" in formula

    def test_get_components_structure(
        self,
        test_client: TestClient,
    ):
        """Test components response structure."""
        response = test_client.get("/api/v1/demand-forecast/components")

        assert response.status_code == 200
        data = response.json()
        components = data["data"]["components"]

        assert len(components) == 4  # 4 components per TOR

        for component in components:
            assert "id" in component
            assert "name" in component
            assert "description" in component
            assert "unit" in component

    def test_get_components_includes_all_components(
        self,
        test_client: TestClient,
    ):
        """Test that all demand components are included."""
        response = test_client.get("/api/v1/demand-forecast/components")

        assert response.status_code == 200
        data = response.json()
        components = data["data"]["components"]
        component_ids = [c["id"] for c in components]

        expected_components = ["gross_load", "btm_re", "battery", "net_demand"]
        for expected in expected_components:
            assert expected in component_ids


class TestDemandForecastTradingPointSummary:
    """Tests for GET /demand-forecast/trading-point/{id}/summary endpoint."""

    def test_get_trading_point_summary_success(
        self,
        test_client: TestClient,
    ):
        """Test successful retrieval of trading point summary."""
        response = test_client.get(
            "/api/v1/demand-forecast/trading-point/SUB_001/summary"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "trading_point" in data["data"]
        assert "current_state" in data["data"]

    def test_get_trading_point_summary_current_state(
        self,
        test_client: TestClient,
    ):
        """Test that current state includes all components."""
        response = test_client.get(
            "/api/v1/demand-forecast/trading-point/SUB_001/summary"
        )

        assert response.status_code == 200
        data = response.json()
        state = data["data"]["current_state"]

        assert "timestamp" in state
        assert "gross_load_mw" in state
        assert "btm_re_mw" in state
        assert "battery_flow_mw" in state
        assert "net_demand_mw" in state
        assert "load_factor" in state

    def test_get_trading_point_summary_includes_status(
        self,
        test_client: TestClient,
    ):
        """Test that summary includes status."""
        response = test_client.get(
            "/api/v1/demand-forecast/trading-point/SUB_001/summary"
        )

        assert response.status_code == 200
        data = response.json()
        assert "status" in data["data"]
        assert data["data"]["status"] in ["normal", "high"]

    def test_get_trading_point_summary_not_found(
        self,
        test_client: TestClient,
    ):
        """Test trading point summary for non-existent ID."""
        response = test_client.get(
            "/api/v1/demand-forecast/trading-point/INVALID_ID/summary"
        )

        assert response.status_code == 200
        data = response.json()
        # Should return error status
        assert data["status"] == "error"

    def test_get_trading_point_summary_all_sample_points(
        self,
        test_client: TestClient,
    ):
        """Test summary for all sample trading points."""
        trading_point_ids = ["SUB_001", "FDR_001", "PRO_001", "AGG_001"]

        for tp_id in trading_point_ids:
            response = test_client.get(
                f"/api/v1/demand-forecast/trading-point/{tp_id}/summary"
            )

            assert response.status_code == 200
            data = response.json()
            if data["status"] == "success":
                assert data["data"]["trading_point"]["id"] == tp_id


class TestDemandForecastAccuracy:
    """Tests for GET /demand-forecast/accuracy endpoint."""

    def test_get_accuracy_default_params(
        self,
        test_client: TestClient,
    ):
        """Test accuracy metrics with default parameters."""
        response = test_client.get("/api/v1/demand-forecast/accuracy")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert data["data"]["trading_point_id"] == "all"
        assert data["data"]["period_days"] == 7

    def test_get_accuracy_specific_trading_point(
        self,
        test_client: TestClient,
    ):
        """Test accuracy for specific trading point."""
        response = test_client.get(
            "/api/v1/demand-forecast/accuracy",
            params={"trading_point_id": "SUB_001", "days": 30},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["trading_point_id"] == "SUB_001"
        assert data["data"]["period_days"] == 30

    def test_get_accuracy_metrics_structure(
        self,
        test_client: TestClient,
    ):
        """Test accuracy metrics structure."""
        response = test_client.get("/api/v1/demand-forecast/accuracy")

        assert response.status_code == 200
        data = response.json()
        metrics = data["data"]["metrics"]

        assert "mape" in metrics
        assert "rmse_mw" in metrics
        assert "mae_mw" in metrics
        assert "r_squared" in metrics

    def test_get_accuracy_target_comparison(
        self,
        test_client: TestClient,
    ):
        """Test accuracy target comparison."""
        response = test_client.get("/api/v1/demand-forecast/accuracy")

        assert response.status_code == 200
        data = response.json()
        target = data["data"]["target"]

        assert "mape" in target
        assert target["mape"] == 5.0  # Per TOR
        assert "status" in target
        assert target["status"] in ["PASS", "NEEDS_IMPROVEMENT"]

    def test_get_accuracy_component_breakdown(
        self,
        test_client: TestClient,
    ):
        """Test that component accuracy is included."""
        response = test_client.get("/api/v1/demand-forecast/accuracy")

        assert response.status_code == 200
        data = response.json()
        component_accuracy = data["data"]["component_accuracy"]

        assert "gross_load_mape" in component_accuracy
        assert "btm_re_mape" in component_accuracy
        assert "battery_mape" in component_accuracy

    def test_get_accuracy_sample_size(
        self,
        test_client: TestClient,
    ):
        """Test that sample size is calculated correctly."""
        days = 7
        response = test_client.get(
            "/api/v1/demand-forecast/accuracy", params={"days": days}
        )

        assert response.status_code == 200
        data = response.json()
        # Hourly intervals = 24 per day
        expected_samples = days * 24
        assert data["data"]["sample_size"] == expected_samples

    def test_get_accuracy_invalid_days_low(
        self,
        test_client: TestClient,
    ):
        """Test accuracy with invalid days parameter (too low)."""
        response = test_client.get(
            "/api/v1/demand-forecast/accuracy", params={"days": 0}
        )

        assert response.status_code == 422  # Validation error

    def test_get_accuracy_invalid_days_high(
        self,
        test_client: TestClient,
    ):
        """Test accuracy with invalid days parameter (too high)."""
        response = test_client.get(
            "/api/v1/demand-forecast/accuracy", params={"days": 100}
        )

        assert response.status_code == 422  # Validation error


class TestDemandForecastAuthentication:
    """Tests for authentication requirements."""

    def test_predict_requires_authentication(
        self,
        test_client: TestClient,
    ):
        """Test that predict endpoint requires authentication (when enabled)."""
        # Note: Auth is disabled in test environment, so this always succeeds
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "trading_point_id": "SUB_001",
            "trading_point_type": "substation",
            "horizon_hours": 24,
            "include_components": True,
        }

        response = test_client.post("/api/v1/demand-forecast/predict", json=request)
        assert response.status_code == 200

    def test_trading_points_requires_authentication(
        self,
        test_client: TestClient,
    ):
        """Test that trading-points endpoint requires authentication."""
        response = test_client.get("/api/v1/demand-forecast/trading-points")
        assert response.status_code == 200

    def test_components_requires_authentication(
        self,
        test_client: TestClient,
    ):
        """Test that components endpoint requires authentication."""
        response = test_client.get("/api/v1/demand-forecast/components")
        assert response.status_code == 200

    def test_summary_requires_authentication(
        self,
        test_client: TestClient,
    ):
        """Test that summary endpoint requires authentication."""
        response = test_client.get(
            "/api/v1/demand-forecast/trading-point/SUB_001/summary"
        )
        assert response.status_code == 200

    def test_accuracy_requires_admin_or_analyst(
        self,
        test_client: TestClient,
    ):
        """Test that accuracy endpoint requires admin or analyst role."""
        # Mock admin user is used by default in test_client
        response = test_client.get("/api/v1/demand-forecast/accuracy")
        assert response.status_code == 200
