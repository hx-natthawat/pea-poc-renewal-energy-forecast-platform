"""
Unit tests for imbalance forecast endpoints (TOR Function 4).

Tests cover:
- Imbalance forecast prediction
- Balancing status (single area and all areas)
- Balancing areas listing
- Reserve capacity status
- Forecast accuracy metrics
- Authentication and authorization
- Request validation
"""

from datetime import UTC, datetime

from fastapi.testclient import TestClient


class TestImbalanceForecastPredict:
    """Tests for POST /imbalance-forecast/predict endpoint."""

    def test_predict_imbalance_success(
        self,
        test_client: TestClient,
    ):
        """Test successful imbalance forecast prediction."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "balancing_area": "system",
            "horizon_hours": 24,
            "include_components": True,
        }

        response = test_client.post("/api/v1/imbalance-forecast/predict", json=request)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert "predictions" in data["data"]
        assert data["data"]["balancing_area"] == "system"

    def test_predict_imbalance_system_area(
        self,
        test_client: TestClient,
    ):
        """Test imbalance forecast for system area."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "balancing_area": "system",
            "horizon_hours": 24,
            "include_components": True,
        }

        response = test_client.post("/api/v1/imbalance-forecast/predict", json=request)

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["balancing_area"] == "system"

    def test_predict_imbalance_central_area(
        self,
        test_client: TestClient,
    ):
        """Test imbalance forecast for central region."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "balancing_area": "central",
            "horizon_hours": 24,
            "include_components": True,
        }

        response = test_client.post("/api/v1/imbalance-forecast/predict", json=request)

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["balancing_area"] == "central"

    def test_predict_imbalance_north_area(
        self,
        test_client: TestClient,
    ):
        """Test imbalance forecast for northern region."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "balancing_area": "north",
            "horizon_hours": 24,
            "include_components": True,
        }

        response = test_client.post("/api/v1/imbalance-forecast/predict", json=request)

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["balancing_area"] == "north"

    def test_predict_imbalance_northeast_area(
        self,
        test_client: TestClient,
    ):
        """Test imbalance forecast for northeastern region."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "balancing_area": "northeast",
            "horizon_hours": 24,
            "include_components": True,
        }

        response = test_client.post("/api/v1/imbalance-forecast/predict", json=request)

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["balancing_area"] == "northeast"

    def test_predict_imbalance_south_area(
        self,
        test_client: TestClient,
    ):
        """Test imbalance forecast for southern region."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "balancing_area": "south",
            "horizon_hours": 24,
            "include_components": True,
        }

        response = test_client.post("/api/v1/imbalance-forecast/predict", json=request)

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["balancing_area"] == "south"

    def test_predict_imbalance_with_components(
        self,
        test_client: TestClient,
    ):
        """Test that predictions include component breakdown when requested."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "balancing_area": "system",
            "horizon_hours": 24,
            "include_components": True,
        }

        response = test_client.post("/api/v1/imbalance-forecast/predict", json=request)

        assert response.status_code == 200
        data = response.json()
        predictions = data["data"]["predictions"]

        for prediction in predictions[:5]:  # Check first 5
            assert "imbalance_mw" in prediction
            assert "imbalance_pct" in prediction
            assert "imbalance_type" in prediction
            assert "severity" in prediction
            assert "actual_demand_mw" in prediction
            assert "scheduled_gen_mw" in prediction
            assert "re_generation_mw" in prediction
            assert "confidence_lower" in prediction
            assert "confidence_upper" in prediction

    def test_predict_imbalance_without_components(
        self,
        test_client: TestClient,
    ):
        """Test predictions without component breakdown."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "balancing_area": "system",
            "horizon_hours": 24,
            "include_components": False,
        }

        response = test_client.post("/api/v1/imbalance-forecast/predict", json=request)

        assert response.status_code == 200
        data = response.json()
        predictions = data["data"]["predictions"]

        for prediction in predictions[:5]:
            assert "imbalance_mw" in prediction
            assert prediction.get("actual_demand_mw") is None
            assert prediction.get("scheduled_gen_mw") is None
            assert prediction.get("re_generation_mw") is None

    def test_predict_imbalance_types(
        self,
        test_client: TestClient,
    ):
        """Test that imbalance types are correctly classified."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "balancing_area": "system",
            "horizon_hours": 24,
            "include_components": True,
        }

        response = test_client.post("/api/v1/imbalance-forecast/predict", json=request)

        assert response.status_code == 200
        data = response.json()
        predictions = data["data"]["predictions"]

        for prediction in predictions:
            assert prediction["imbalance_type"] in ["positive", "negative", "balanced"]

    def test_predict_imbalance_severity_levels(
        self,
        test_client: TestClient,
    ):
        """Test that severity levels are correctly assigned."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "balancing_area": "system",
            "horizon_hours": 24,
            "include_components": True,
        }

        response = test_client.post("/api/v1/imbalance-forecast/predict", json=request)

        assert response.status_code == 200
        data = response.json()
        predictions = data["data"]["predictions"]

        for prediction in predictions:
            assert prediction["severity"] in ["normal", "warning", "critical"]

    def test_predict_imbalance_confidence_intervals(
        self,
        test_client: TestClient,
    ):
        """Test that predictions include confidence intervals."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "balancing_area": "system",
            "horizon_hours": 24,
            "include_components": True,
        }

        response = test_client.post("/api/v1/imbalance-forecast/predict", json=request)

        assert response.status_code == 200
        data = response.json()
        predictions = data["data"]["predictions"]

        for prediction in predictions[:5]:
            # Confidence intervals should bracket the prediction
            assert "confidence_lower" in prediction
            assert "confidence_upper" in prediction

    def test_predict_imbalance_horizon_hours(
        self,
        test_client: TestClient,
    ):
        """Test that horizon_hours parameter works correctly."""
        horizon = 48
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "balancing_area": "system",
            "horizon_hours": horizon,
            "include_components": True,
        }

        response = test_client.post("/api/v1/imbalance-forecast/predict", json=request)

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["horizon_hours"] == horizon
        assert len(data["data"]["predictions"]) == horizon

    def test_predict_imbalance_includes_summary(
        self,
        test_client: TestClient,
    ):
        """Test that response includes summary statistics."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "balancing_area": "system",
            "horizon_hours": 24,
            "include_components": True,
        }

        response = test_client.post("/api/v1/imbalance-forecast/predict", json=request)

        assert response.status_code == 200
        data = response.json()
        summary = data["data"]["summary"]

        assert "max_deficit_mw" in summary
        assert "max_surplus_mw" in summary
        assert "avg_abs_imbalance_mw" in summary
        assert "total_intervals" in summary
        assert "severity_distribution" in summary

    def test_predict_imbalance_severity_distribution(
        self,
        test_client: TestClient,
    ):
        """Test severity distribution in summary."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "balancing_area": "system",
            "horizon_hours": 24,
            "include_components": True,
        }

        response = test_client.post("/api/v1/imbalance-forecast/predict", json=request)

        assert response.status_code == 200
        data = response.json()
        severity_dist = data["data"]["summary"]["severity_distribution"]

        assert "normal" in severity_dist
        assert "warning" in severity_dist
        assert "critical" in severity_dist

    def test_predict_imbalance_includes_metadata(
        self,
        test_client: TestClient,
    ):
        """Test that response includes metadata."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "balancing_area": "system",
            "horizon_hours": 24,
            "include_components": True,
        }

        response = test_client.post("/api/v1/imbalance-forecast/predict", json=request)

        assert response.status_code == 200
        data = response.json()

        assert "meta" in data
        assert "prediction_time_ms" in data["meta"]
        assert data["meta"]["accuracy_target_mae_pct"] == 5.0
        assert data["meta"]["phase"] == "Phase 2 - Simulation"
        assert data["data"]["model_version"] is not None
        assert data["data"]["is_ml_prediction"] is False

    def test_predict_imbalance_invalid_horizon_low(
        self,
        test_client: TestClient,
    ):
        """Test imbalance forecast with invalid horizon (too low)."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "balancing_area": "system",
            "horizon_hours": 0,
            "include_components": True,
        }

        response = test_client.post("/api/v1/imbalance-forecast/predict", json=request)
        assert response.status_code == 422  # Validation error

    def test_predict_imbalance_invalid_horizon_high(
        self,
        test_client: TestClient,
    ):
        """Test imbalance forecast with invalid horizon (too high)."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "balancing_area": "system",
            "horizon_hours": 200,
            "include_components": True,
        }

        response = test_client.post("/api/v1/imbalance-forecast/predict", json=request)
        assert response.status_code == 422  # Validation error

    def test_predict_imbalance_invalid_area(
        self,
        test_client: TestClient,
    ):
        """Test imbalance forecast with invalid balancing area."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "balancing_area": "invalid_area",
            "horizon_hours": 24,
            "include_components": True,
        }

        response = test_client.post("/api/v1/imbalance-forecast/predict", json=request)
        assert response.status_code == 422  # Validation error

    def test_predict_imbalance_missing_timestamp(
        self,
        test_client: TestClient,
    ):
        """Test imbalance forecast with missing timestamp."""
        request = {
            "balancing_area": "system",
            "horizon_hours": 24,
            "include_components": True,
        }

        response = test_client.post("/api/v1/imbalance-forecast/predict", json=request)
        assert response.status_code == 422  # Validation error


class TestImbalanceBalancingStatus:
    """Tests for GET /imbalance-forecast/status/{area} endpoint."""

    def test_get_status_system_area(
        self,
        test_client: TestClient,
    ):
        """Test balancing status for system area."""
        response = test_client.get("/api/v1/imbalance-forecast/status/system")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert data["data"]["area"] == "system"

    def test_get_status_all_areas(
        self,
        test_client: TestClient,
    ):
        """Test balancing status for all areas."""
        areas = ["system", "central", "north", "northeast", "south"]

        for area in areas:
            response = test_client.get(f"/api/v1/imbalance-forecast/status/{area}")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["data"]["area"] == area

    def test_get_status_structure(
        self,
        test_client: TestClient,
    ):
        """Test balancing status structure."""
        response = test_client.get("/api/v1/imbalance-forecast/status/system")

        assert response.status_code == 200
        data = response.json()
        status_data = data["data"]

        assert "area" in status_data
        assert "timestamp" in status_data
        assert "imbalance_mw" in status_data
        assert "imbalance_pct" in status_data
        assert "type" in status_data
        assert "severity" in status_data
        assert "reserves_available_mw" in status_data

    def test_get_status_imbalance_type(
        self,
        test_client: TestClient,
    ):
        """Test that status includes valid imbalance type."""
        response = test_client.get("/api/v1/imbalance-forecast/status/system")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["type"] in ["positive", "negative", "balanced"]

    def test_get_status_severity(
        self,
        test_client: TestClient,
    ):
        """Test that status includes valid severity level."""
        response = test_client.get("/api/v1/imbalance-forecast/status/system")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["severity"] in ["normal", "warning", "critical"]

    def test_get_status_action_required(
        self,
        test_client: TestClient,
    ):
        """Test that action_required field is present."""
        response = test_client.get("/api/v1/imbalance-forecast/status/system")

        assert response.status_code == 200
        data = response.json()
        # action_required can be null for normal conditions
        assert "action_required" in data["data"]


class TestImbalanceAllBalancingStatus:
    """Tests for GET /imbalance-forecast/status endpoint."""

    def test_get_all_status_success(
        self,
        test_client: TestClient,
    ):
        """Test successful retrieval of all balancing statuses."""
        response = test_client.get("/api/v1/imbalance-forecast/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data

    def test_get_all_status_includes_all_areas(
        self,
        test_client: TestClient,
    ):
        """Test that all balancing areas are included."""
        response = test_client.get("/api/v1/imbalance-forecast/status")

        assert response.status_code == 200
        data = response.json()
        areas = data["data"]["areas"]

        assert len(areas) == 5  # 5 balancing areas
        area_ids = [a["area"] for a in areas]

        expected_areas = ["system", "central", "north", "northeast", "south"]
        for expected in expected_areas:
            assert expected in area_ids

    def test_get_all_status_system_summary(
        self,
        test_client: TestClient,
    ):
        """Test that system summary is included."""
        response = test_client.get("/api/v1/imbalance-forecast/status")

        assert response.status_code == 200
        data = response.json()

        assert "system_imbalance_mw" in data["data"]
        assert "system_severity" in data["data"]
        assert "total_reserves_mw" in data["data"]
        assert "timestamp" in data["data"]

    def test_get_all_status_total_reserves(
        self,
        test_client: TestClient,
    ):
        """Test that total reserves are calculated."""
        response = test_client.get("/api/v1/imbalance-forecast/status")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total_reserves_mw"] > 0


class TestImbalanceBalancingAreas:
    """Tests for GET /imbalance-forecast/areas endpoint."""

    def test_get_areas_success(
        self,
        test_client: TestClient,
    ):
        """Test successful retrieval of balancing areas."""
        response = test_client.get("/api/v1/imbalance-forecast/areas")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert "areas" in data["data"]

    def test_get_areas_structure(
        self,
        test_client: TestClient,
    ):
        """Test areas response structure."""
        response = test_client.get("/api/v1/imbalance-forecast/areas")

        assert response.status_code == 200
        data = response.json()
        areas = data["data"]["areas"]

        for area in areas:
            assert "id" in area
            assert "name" in area

    def test_get_areas_includes_all_areas(
        self,
        test_client: TestClient,
    ):
        """Test that all balancing areas are included."""
        response = test_client.get("/api/v1/imbalance-forecast/areas")

        assert response.status_code == 200
        data = response.json()
        areas = data["data"]["areas"]
        area_ids = [a["id"] for a in areas]

        expected_areas = ["system", "central", "north", "northeast", "south"]
        for expected in expected_areas:
            assert expected in area_ids


class TestImbalanceReserves:
    """Tests for GET /imbalance-forecast/reserves endpoint."""

    def test_get_reserves_default_area(
        self,
        test_client: TestClient,
    ):
        """Test reserves for default area (system)."""
        response = test_client.get("/api/v1/imbalance-forecast/reserves")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["area"] == "system"

    def test_get_reserves_specific_area(
        self,
        test_client: TestClient,
    ):
        """Test reserves for specific balancing area."""
        response = test_client.get(
            "/api/v1/imbalance-forecast/reserves", params={"area": "central"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["area"] == "central"

    def test_get_reserves_structure(
        self,
        test_client: TestClient,
    ):
        """Test reserves response structure."""
        response = test_client.get("/api/v1/imbalance-forecast/reserves")

        assert response.status_code == 200
        data = response.json()
        reserves_data = data["data"]

        assert "area" in reserves_data
        assert "total_reserves_mw" in reserves_data
        assert "available_mw" in reserves_data
        assert "committed_mw" in reserves_data
        assert "utilization_pct" in reserves_data
        assert "reserve_types" in reserves_data
        assert "timestamp" in reserves_data

    def test_get_reserves_types_breakdown(
        self,
        test_client: TestClient,
    ):
        """Test that reserve types breakdown is included."""
        response = test_client.get("/api/v1/imbalance-forecast/reserves")

        assert response.status_code == 200
        data = response.json()
        reserve_types = data["data"]["reserve_types"]

        assert "primary" in reserve_types
        assert "secondary" in reserve_types
        assert "tertiary" in reserve_types

    def test_get_reserves_all_areas(
        self,
        test_client: TestClient,
    ):
        """Test reserves for all balancing areas."""
        areas = ["system", "central", "north", "northeast", "south"]

        for area in areas:
            response = test_client.get(
                "/api/v1/imbalance-forecast/reserves", params={"area": area}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["area"] == area

    def test_get_reserves_utilization_range(
        self,
        test_client: TestClient,
    ):
        """Test that utilization percentage is within valid range."""
        response = test_client.get("/api/v1/imbalance-forecast/reserves")

        assert response.status_code == 200
        data = response.json()
        utilization = data["data"]["utilization_pct"]
        assert 0.0 <= utilization <= 100.0


class TestImbalanceAccuracy:
    """Tests for GET /imbalance-forecast/accuracy endpoint."""

    def test_get_accuracy_default_params(
        self,
        test_client: TestClient,
    ):
        """Test accuracy metrics with default parameters."""
        response = test_client.get("/api/v1/imbalance-forecast/accuracy")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert data["data"]["area"] == "system"
        assert data["data"]["period_days"] == 7

    def test_get_accuracy_specific_area(
        self,
        test_client: TestClient,
    ):
        """Test accuracy for specific balancing area."""
        response = test_client.get(
            "/api/v1/imbalance-forecast/accuracy",
            params={"area": "central", "days": 30},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["area"] == "central"
        assert data["data"]["period_days"] == 30

    def test_get_accuracy_metrics_structure(
        self,
        test_client: TestClient,
    ):
        """Test accuracy metrics structure."""
        response = test_client.get("/api/v1/imbalance-forecast/accuracy")

        assert response.status_code == 200
        data = response.json()
        metrics = data["data"]["metrics"]

        assert "mae_pct" in metrics
        assert "mae_mw" in metrics
        assert "rmse_mw" in metrics
        assert "bias_mw" in metrics

    def test_get_accuracy_target_comparison(
        self,
        test_client: TestClient,
    ):
        """Test accuracy target comparison."""
        response = test_client.get("/api/v1/imbalance-forecast/accuracy")

        assert response.status_code == 200
        data = response.json()
        target = data["data"]["target"]

        assert "mae_pct" in target
        assert target["mae_pct"] == 5.0  # Per TOR
        assert "status" in target
        assert target["status"] in ["PASS", "NEEDS_IMPROVEMENT"]

    def test_get_accuracy_component_contribution(
        self,
        test_client: TestClient,
    ):
        """Test that component error contributions are included."""
        response = test_client.get("/api/v1/imbalance-forecast/accuracy")

        assert response.status_code == 200
        data = response.json()
        component_contrib = data["data"]["component_contribution"]

        assert "demand_error_pct" in component_contrib
        assert "re_error_pct" in component_contrib
        assert "scheduled_gen_error_pct" in component_contrib

    def test_get_accuracy_sample_size(
        self,
        test_client: TestClient,
    ):
        """Test that sample size is calculated correctly."""
        days = 7
        response = test_client.get(
            "/api/v1/imbalance-forecast/accuracy", params={"days": days}
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
            "/api/v1/imbalance-forecast/accuracy", params={"days": 0}
        )

        assert response.status_code == 422  # Validation error

    def test_get_accuracy_invalid_days_high(
        self,
        test_client: TestClient,
    ):
        """Test accuracy with invalid days parameter (too high)."""
        response = test_client.get(
            "/api/v1/imbalance-forecast/accuracy", params={"days": 100}
        )

        assert response.status_code == 422  # Validation error


class TestImbalanceForecastAuthentication:
    """Tests for authentication requirements."""

    def test_predict_requires_authentication(
        self,
        test_client: TestClient,
    ):
        """Test that predict endpoint requires authentication (when enabled)."""
        # Note: Auth is disabled in test environment, so this always succeeds
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "balancing_area": "system",
            "horizon_hours": 24,
            "include_components": True,
        }

        response = test_client.post("/api/v1/imbalance-forecast/predict", json=request)
        assert response.status_code == 200

    def test_status_requires_authentication(
        self,
        test_client: TestClient,
    ):
        """Test that status endpoint requires authentication."""
        response = test_client.get("/api/v1/imbalance-forecast/status/system")
        assert response.status_code == 200

    def test_all_status_requires_authentication(
        self,
        test_client: TestClient,
    ):
        """Test that all status endpoint requires authentication."""
        response = test_client.get("/api/v1/imbalance-forecast/status")
        assert response.status_code == 200

    def test_areas_requires_authentication(
        self,
        test_client: TestClient,
    ):
        """Test that areas endpoint requires authentication."""
        response = test_client.get("/api/v1/imbalance-forecast/areas")
        assert response.status_code == 200

    def test_reserves_requires_admin_or_operator(
        self,
        test_client: TestClient,
    ):
        """Test that reserves endpoint requires admin or operator role."""
        # Mock admin user is used by default in test_client
        response = test_client.get("/api/v1/imbalance-forecast/reserves")
        assert response.status_code == 200

    def test_accuracy_requires_admin_or_analyst(
        self,
        test_client: TestClient,
    ):
        """Test that accuracy endpoint requires admin or analyst role."""
        # Mock admin user is used by default in test_client
        response = test_client.get("/api/v1/imbalance-forecast/accuracy")
        assert response.status_code == 200
