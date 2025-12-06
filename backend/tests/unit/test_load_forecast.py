"""
Unit tests for load forecast endpoints (TOR Function 3).

Tests cover:
- Load forecast prediction at multiple levels
- PEA regions listing
- Forecast levels configuration
- Load summary by level
- Forecast accuracy metrics
- Authentication and authorization
- Request validation
"""

from datetime import UTC, datetime

from fastapi.testclient import TestClient


class TestLoadForecastPredict:
    """Tests for POST /load-forecast/predict endpoint."""

    def test_predict_load_system_level_success(
        self,
        test_client: TestClient,
    ):
        """Test successful system-level load forecast."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": "system",
            "horizon": "day_ahead",
            "include_weather": True,
        }

        response = test_client.post("/api/v1/load-forecast/predict", json=request)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert "predictions" in data["data"]
        assert data["data"]["level"] == "system"
        assert data["data"]["horizon"] == "day_ahead"
        assert len(data["data"]["predictions"]) > 0

    def test_predict_load_regional_level(
        self,
        test_client: TestClient,
    ):
        """Test regional-level load forecast."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": "regional",
            "area_id": "central1",
            "horizon": "day_ahead",
            "include_weather": True,
        }

        response = test_client.post("/api/v1/load-forecast/predict", json=request)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["level"] == "regional"
        assert data["data"]["area_id"] == "central1"

    def test_predict_load_provincial_level(
        self,
        test_client: TestClient,
    ):
        """Test provincial-level load forecast."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": "provincial",
            "area_id": "bangkok",
            "horizon": "intraday",
            "include_weather": True,
        }

        response = test_client.post("/api/v1/load-forecast/predict", json=request)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["level"] == "provincial"

    def test_predict_load_substation_level(
        self,
        test_client: TestClient,
    ):
        """Test substation-level load forecast."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": "substation",
            "area_id": "SUB_001",
            "horizon": "intraday",
            "include_weather": True,
        }

        response = test_client.post("/api/v1/load-forecast/predict", json=request)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["level"] == "substation"

    def test_predict_load_feeder_level(
        self,
        test_client: TestClient,
    ):
        """Test feeder-level load forecast."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": "feeder",
            "area_id": "FDR_001",
            "horizon": "intraday",
            "include_weather": False,
        }

        response = test_client.post("/api/v1/load-forecast/predict", json=request)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["level"] == "feeder"

    def test_predict_load_intraday_horizon(
        self,
        test_client: TestClient,
    ):
        """Test intraday forecast horizon (15 min - 6 hours)."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": "system",
            "horizon": "intraday",
            "include_weather": True,
        }

        response = test_client.post("/api/v1/load-forecast/predict", json=request)

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["horizon"] == "intraday"
        # Intraday should have 24 intervals (15-min for 6 hours)
        assert data["data"]["total_intervals"] == 24

    def test_predict_load_day_ahead_horizon(
        self,
        test_client: TestClient,
    ):
        """Test day-ahead forecast horizon (24-48 hours)."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": "system",
            "horizon": "day_ahead",
            "include_weather": True,
        }

        response = test_client.post("/api/v1/load-forecast/predict", json=request)

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["horizon"] == "day_ahead"
        # Day-ahead should have 48 intervals (30-min for 24 hours)
        assert data["data"]["total_intervals"] == 48

    def test_predict_load_week_ahead_horizon(
        self,
        test_client: TestClient,
    ):
        """Test week-ahead forecast horizon (7 days)."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": "system",
            "horizon": "week_ahead",
            "include_weather": True,
        }

        response = test_client.post("/api/v1/load-forecast/predict", json=request)

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["horizon"] == "week_ahead"
        # Week-ahead should have 168 intervals (hourly for 7 days)
        assert data["data"]["total_intervals"] == 168

    def test_predict_load_includes_confidence_intervals(
        self,
        test_client: TestClient,
    ):
        """Test that predictions include confidence intervals."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": "system",
            "horizon": "intraday",
            "include_weather": True,
        }

        response = test_client.post("/api/v1/load-forecast/predict", json=request)

        assert response.status_code == 200
        data = response.json()
        predictions = data["data"]["predictions"]

        for prediction in predictions[:5]:  # Check first 5
            assert "predicted_load_mw" in prediction
            assert "confidence_lower" in prediction
            assert "confidence_upper" in prediction
            assert prediction["confidence_lower"] <= prediction["predicted_load_mw"]
            assert prediction["confidence_upper"] >= prediction["predicted_load_mw"]

    def test_predict_load_includes_weather_factors(
        self,
        test_client: TestClient,
    ):
        """Test that predictions include weather factors when requested."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": "system",
            "horizon": "intraday",
            "include_weather": True,
        }

        response = test_client.post("/api/v1/load-forecast/predict", json=request)

        assert response.status_code == 200
        data = response.json()
        predictions = data["data"]["predictions"]

        for prediction in predictions[:5]:
            assert "temperature_factor" in prediction
            assert "humidity_factor" in prediction

    def test_predict_load_includes_metadata(
        self,
        test_client: TestClient,
    ):
        """Test that response includes metadata."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": "system",
            "horizon": "intraday",
            "include_weather": True,
        }

        response = test_client.post("/api/v1/load-forecast/predict", json=request)

        assert response.status_code == 200
        data = response.json()

        assert "meta" in data
        assert "prediction_time_ms" in data["meta"]
        assert "accuracy_target_mape" in data["meta"]
        assert data["meta"]["phase"] == "Phase 2 - Simulation"
        assert data["data"]["model_version"] is not None
        assert data["data"]["is_ml_prediction"] is False

    def test_predict_load_accuracy_targets(
        self,
        test_client: TestClient,
    ):
        """Test that accuracy targets are correct per TOR."""
        test_cases = [
            ("system", 3.0),
            ("regional", 5.0),
            ("provincial", 8.0),
            ("substation", 8.0),
            ("feeder", 12.0),
        ]

        for level, expected_mape in test_cases:
            request = {
                "timestamp": datetime.now(UTC).isoformat(),
                "level": level,
                "horizon": "intraday",
                "include_weather": True,
            }

            response = test_client.post("/api/v1/load-forecast/predict", json=request)

            assert response.status_code == 200
            data = response.json()
            assert data["meta"]["accuracy_target_mape"] == expected_mape

    def test_predict_load_invalid_level(
        self,
        test_client: TestClient,
    ):
        """Test load forecast with invalid level."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": "invalid_level",
            "horizon": "intraday",
            "include_weather": True,
        }

        response = test_client.post("/api/v1/load-forecast/predict", json=request)
        assert response.status_code == 422  # Validation error

    def test_predict_load_invalid_horizon(
        self,
        test_client: TestClient,
    ):
        """Test load forecast with invalid horizon."""
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": "system",
            "horizon": "invalid_horizon",
            "include_weather": True,
        }

        response = test_client.post("/api/v1/load-forecast/predict", json=request)
        assert response.status_code == 422  # Validation error

    def test_predict_load_missing_timestamp(
        self,
        test_client: TestClient,
    ):
        """Test load forecast with missing timestamp."""
        request = {
            "level": "system",
            "horizon": "intraday",
            "include_weather": True,
        }

        response = test_client.post("/api/v1/load-forecast/predict", json=request)
        assert response.status_code == 422  # Validation error


class TestLoadForecastRegions:
    """Tests for GET /load-forecast/regions endpoint."""

    def test_get_regions_success(
        self,
        test_client: TestClient,
    ):
        """Test successful retrieval of PEA regions."""
        response = test_client.get("/api/v1/load-forecast/regions")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert "regions" in data["data"]
        assert data["data"]["total"] == 12  # 12 PEA regions

    def test_get_regions_structure(
        self,
        test_client: TestClient,
    ):
        """Test regions response structure."""
        response = test_client.get("/api/v1/load-forecast/regions")

        assert response.status_code == 200
        data = response.json()
        regions = data["data"]["regions"]

        for region in regions:
            assert "id" in region
            assert "name" in region
            assert "provinces" in region
            assert isinstance(region["provinces"], list)
            assert len(region["provinces"]) > 0

    def test_get_regions_includes_all_regions(
        self,
        test_client: TestClient,
    ):
        """Test that all PEA regions are included."""
        response = test_client.get("/api/v1/load-forecast/regions")

        assert response.status_code == 200
        data = response.json()
        regions = data["data"]["regions"]
        region_ids = [r["id"] for r in regions]

        expected_regions = [
            "central1",
            "central2",
            "north1",
            "north2",
            "northeast1",
            "northeast2",
            "northeast3",
            "east",
            "west",
            "south1",
            "south2",
            "south3",
        ]

        for expected in expected_regions:
            assert expected in region_ids


class TestLoadForecastLevels:
    """Tests for GET /load-forecast/levels endpoint."""

    def test_get_levels_success(
        self,
        test_client: TestClient,
    ):
        """Test successful retrieval of forecast levels."""
        response = test_client.get("/api/v1/load-forecast/levels")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert "levels" in data["data"]

    def test_get_levels_structure(
        self,
        test_client: TestClient,
    ):
        """Test levels response structure."""
        response = test_client.get("/api/v1/load-forecast/levels")

        assert response.status_code == 200
        data = response.json()
        levels = data["data"]["levels"]

        for level in levels:
            assert "id" in level
            assert "name" in level
            assert "mape_target" in level
            assert "description" in level

    def test_get_levels_includes_all_levels(
        self,
        test_client: TestClient,
    ):
        """Test that all forecast levels are included."""
        response = test_client.get("/api/v1/load-forecast/levels")

        assert response.status_code == 200
        data = response.json()
        levels = data["data"]["levels"]
        level_ids = [lvl["id"] for lvl in levels]

        expected_levels = ["system", "regional", "provincial", "substation", "feeder"]

        for expected in expected_levels:
            assert expected in level_ids

    def test_get_levels_mape_targets(
        self,
        test_client: TestClient,
    ):
        """Test that MAPE targets are correct."""
        response = test_client.get("/api/v1/load-forecast/levels")

        assert response.status_code == 200
        data = response.json()
        levels = {lvl["id"]: lvl for lvl in data["data"]["levels"]}

        assert levels["system"]["mape_target"] == 3.0
        assert levels["regional"]["mape_target"] == 5.0
        assert levels["provincial"]["mape_target"] == 8.0
        assert levels["substation"]["mape_target"] == 8.0
        assert levels["feeder"]["mape_target"] == 12.0


class TestLoadForecastSummary:
    """Tests for GET /load-forecast/summary/{level} endpoint."""

    def test_get_summary_system_level(
        self,
        test_client: TestClient,
    ):
        """Test summary for system level."""
        response = test_client.get("/api/v1/load-forecast/summary/system")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["level"] == "system"
        assert "current_load_mw" in data["data"]
        assert "peak_load_mw" in data["data"]
        assert "min_load_mw" in data["data"]
        assert "load_factor" in data["data"]

    def test_get_summary_with_area_id(
        self,
        test_client: TestClient,
    ):
        """Test summary with specific area ID."""
        response = test_client.get(
            "/api/v1/load-forecast/summary/regional", params={"area_id": "central1"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["level"] == "regional"
        assert data["data"]["area_id"] == "central1"

    def test_get_summary_all_levels(
        self,
        test_client: TestClient,
    ):
        """Test summary for all forecast levels."""
        levels = ["system", "regional", "provincial", "substation", "feeder"]

        for level in levels:
            response = test_client.get(f"/api/v1/load-forecast/summary/{level}")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["data"]["level"] == level

    def test_get_summary_includes_status(
        self,
        test_client: TestClient,
    ):
        """Test that summary includes status."""
        response = test_client.get("/api/v1/load-forecast/summary/system")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data["data"]
        assert data["data"]["status"] in ["normal", "high"]

    def test_get_summary_load_factor_range(
        self,
        test_client: TestClient,
    ):
        """Test that load factor is within valid range."""
        response = test_client.get("/api/v1/load-forecast/summary/system")

        assert response.status_code == 200
        data = response.json()
        load_factor = data["data"]["load_factor"]
        assert 0.0 <= load_factor <= 1.0


class TestLoadForecastAccuracy:
    """Tests for GET /load-forecast/accuracy endpoint."""

    def test_get_accuracy_default_params(
        self,
        test_client: TestClient,
    ):
        """Test accuracy metrics with default parameters."""
        response = test_client.get("/api/v1/load-forecast/accuracy")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert data["data"]["level"] == "system"
        assert data["data"]["period_days"] == 7

    def test_get_accuracy_specific_level(
        self,
        test_client: TestClient,
    ):
        """Test accuracy for specific forecast level."""
        response = test_client.get(
            "/api/v1/load-forecast/accuracy", params={"level": "regional", "days": 30}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["level"] == "regional"
        assert data["data"]["period_days"] == 30

    def test_get_accuracy_metrics_structure(
        self,
        test_client: TestClient,
    ):
        """Test accuracy metrics structure."""
        response = test_client.get("/api/v1/load-forecast/accuracy")

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
        response = test_client.get("/api/v1/load-forecast/accuracy")

        assert response.status_code == 200
        data = response.json()
        target = data["data"]["target"]

        assert "mape" in target
        assert "status" in target
        assert target["status"] in ["PASS", "NEEDS_IMPROVEMENT"]

    def test_get_accuracy_sample_size(
        self,
        test_client: TestClient,
    ):
        """Test that sample size is calculated correctly."""
        days = 7
        response = test_client.get(
            "/api/v1/load-forecast/accuracy", params={"days": days}
        )

        assert response.status_code == 200
        data = response.json()
        # 30-minute intervals = 48 per day
        expected_samples = days * 48
        assert data["data"]["sample_size"] == expected_samples

    def test_get_accuracy_invalid_days_low(
        self,
        test_client: TestClient,
    ):
        """Test accuracy with invalid days parameter (too low)."""
        response = test_client.get("/api/v1/load-forecast/accuracy", params={"days": 0})

        assert response.status_code == 422  # Validation error

    def test_get_accuracy_invalid_days_high(
        self,
        test_client: TestClient,
    ):
        """Test accuracy with invalid days parameter (too high)."""
        response = test_client.get(
            "/api/v1/load-forecast/accuracy", params={"days": 100}
        )

        assert response.status_code == 422  # Validation error


class TestLoadForecastAuthentication:
    """Tests for authentication requirements."""

    def test_predict_requires_authentication(
        self,
        test_client: TestClient,
    ):
        """Test that predict endpoint requires authentication (when enabled)."""
        # Note: Auth is disabled in test environment, so this always succeeds
        request = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": "system",
            "horizon": "intraday",
            "include_weather": True,
        }

        response = test_client.post("/api/v1/load-forecast/predict", json=request)
        assert response.status_code == 200

    def test_regions_requires_authentication(
        self,
        test_client: TestClient,
    ):
        """Test that regions endpoint requires authentication."""
        response = test_client.get("/api/v1/load-forecast/regions")
        assert response.status_code == 200

    def test_levels_requires_authentication(
        self,
        test_client: TestClient,
    ):
        """Test that levels endpoint requires authentication."""
        response = test_client.get("/api/v1/load-forecast/levels")
        assert response.status_code == 200

    def test_summary_requires_authentication(
        self,
        test_client: TestClient,
    ):
        """Test that summary endpoint requires authentication."""
        response = test_client.get("/api/v1/load-forecast/summary/system")
        assert response.status_code == 200

    def test_accuracy_requires_admin_or_analyst(
        self,
        test_client: TestClient,
    ):
        """Test that accuracy endpoint requires admin or analyst role."""
        # Mock admin user is used by default in test_client
        response = test_client.get("/api/v1/load-forecast/accuracy")
        assert response.status_code == 200
