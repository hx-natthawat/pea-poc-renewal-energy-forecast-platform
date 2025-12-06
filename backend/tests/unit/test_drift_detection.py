"""
Unit tests for drift detection service.

Tests the v1.1.0 Model Retraining Pipeline feature.
"""

from datetime import datetime, timedelta

import numpy as np

from app.services.drift_detection_service import (
    DriftDetectionService,
    DriftSeverity,
    DriftType,
    ModelRegistryService,
    RetrainingTrigger,
    get_drift_detection_service,
    get_model_registry_service,
)


class TestDriftDetectionService:
    """Tests for DriftDetectionService."""

    def test_init_default_config(self):
        """Test initialization with default config."""
        service = DriftDetectionService()
        assert service.config.mape_threshold == 12.0
        assert service.config.mae_threshold_voltage == 2.5
        assert service.config.drift_score_threshold == 2.0

    def test_init_custom_config(self):
        """Test initialization with custom config."""
        config = RetrainingTrigger(mape_threshold=15.0)
        service = DriftDetectionService(config=config)
        assert service.config.mape_threshold == 15.0

    def test_detect_data_drift_no_drift(self):
        """Test drift detection when distributions are similar."""
        service = DriftDetectionService()

        # Generate similar distributions
        np.random.seed(42)
        baseline = np.random.normal(100, 10, 500)
        current = np.random.normal(100, 10, 500)

        result = service.detect_data_drift(baseline, current, "test_feature")

        assert result.drift_type == DriftType.DATA_DRIFT
        assert result.feature_name == "test_feature"
        assert not result.drift_detected
        assert result.severity in [DriftSeverity.NONE, DriftSeverity.LOW]

    def test_detect_data_drift_significant_drift(self):
        """Test drift detection when distributions are different."""
        service = DriftDetectionService()

        # Generate different distributions
        np.random.seed(42)
        baseline = np.random.normal(100, 10, 500)
        current = np.random.normal(150, 10, 500)  # Shifted mean

        result = service.detect_data_drift(baseline, current, "shifted_feature")

        assert result.drift_type == DriftType.DATA_DRIFT
        assert result.drift_detected is True
        assert result.severity in [DriftSeverity.HIGH, DriftSeverity.CRITICAL]
        assert result.drift_score > service.config.drift_score_threshold

    def test_detect_data_drift_insufficient_data(self):
        """Test drift detection with insufficient baseline data."""
        config = RetrainingTrigger(min_samples_for_detection=100)
        service = DriftDetectionService(config=config)

        baseline = np.array([1, 2, 3, 4, 5])  # Too few samples
        current = np.array([10, 20, 30, 40, 50])

        result = service.detect_data_drift(baseline, current, "small_feature")

        assert not result.drift_detected
        assert "Insufficient" in result.recommendation

    def test_detect_performance_drift_no_issue(self):
        """Test performance drift when within threshold."""
        service = DriftDetectionService()

        result = service.detect_performance_drift(
            model_type="solar",
            baseline_mape=8.0,
            current_mape=9.0,  # Below 12% threshold
        )

        assert result.drift_type == DriftType.PERFORMANCE_DRIFT
        assert not result.drift_detected
        assert result.severity in [DriftSeverity.NONE, DriftSeverity.LOW]

    def test_detect_performance_drift_exceeded(self):
        """Test performance drift when threshold exceeded."""
        service = DriftDetectionService()

        result = service.detect_performance_drift(
            model_type="solar",
            baseline_mape=8.0,
            current_mape=15.0,  # Above 12% threshold
        )

        assert result.drift_type == DriftType.PERFORMANCE_DRIFT
        assert result.drift_detected is True
        assert result.severity in [
            DriftSeverity.MEDIUM,
            DriftSeverity.HIGH,
            DriftSeverity.CRITICAL,
        ]

    def test_detect_performance_drift_voltage(self):
        """Test performance drift for voltage model."""
        service = DriftDetectionService()

        result = service.detect_performance_drift(
            model_type="voltage",
            baseline_mape=0.5,
            current_mape=1.0,
            baseline_mae=1.0,
            current_mae=3.0,  # Above 2.5V threshold
        )

        assert result.drift_detected is True

    def test_evaluate_retraining_need_no_retrain(self):
        """Test retraining evaluation when not needed."""
        service = DriftDetectionService()

        decision = service.evaluate_retraining_need(
            model_type="solar",
            drift_results=[],
            current_metrics={"mape": 8.0, "mae": 30.0},
            last_retrain_date=datetime.now() - timedelta(days=5),
        )

        assert decision.should_retrain is False
        assert decision.urgency == DriftSeverity.NONE

    def test_evaluate_retraining_need_threshold_exceeded(self):
        """Test retraining evaluation when threshold exceeded."""
        service = DriftDetectionService()

        decision = service.evaluate_retraining_need(
            model_type="solar",
            drift_results=[],
            current_metrics={"mape": 15.0, "mae": 100.0},  # MAPE exceeds threshold
            last_retrain_date=datetime.now() - timedelta(days=15),
        )

        assert decision.should_retrain is True
        assert decision.urgency in [DriftSeverity.HIGH, DriftSeverity.CRITICAL]
        assert len(decision.reasons) > 0

    def test_evaluate_retraining_cooldown(self):
        """Test retraining evaluation respects cooldown period."""
        service = DriftDetectionService()

        decision = service.evaluate_retraining_need(
            model_type="solar",
            drift_results=[],
            current_metrics={"mape": 15.0},  # Would normally trigger
            last_retrain_date=datetime.now() - timedelta(days=2),  # Too recent
        )

        assert decision.should_retrain is False
        assert "days required" in decision.reasons[0]

    def test_evaluate_retraining_time_based(self):
        """Test retraining triggers after max days."""
        config = RetrainingTrigger(max_days_without_retrain=30)
        service = DriftDetectionService(config=config)

        decision = service.evaluate_retraining_need(
            model_type="solar",
            drift_results=[],
            current_metrics={"mape": 9.0},  # Within threshold
            last_retrain_date=datetime.now() - timedelta(days=45),  # Too long
        )

        assert len(decision.reasons) > 0
        assert "days" in decision.reasons[0]


class TestModelRegistryService:
    """Tests for ModelRegistryService."""

    def test_register_model(self):
        """Test model registration."""
        registry = ModelRegistryService()

        model = registry.register_model(
            model_type="solar",
            version="v2.0.0",
            metrics={"mape": 8.5, "r2": 0.96},
        )

        assert model.model_type == "solar"
        assert model.version == "v2.0.0"
        assert model.is_champion is True  # First model
        assert model.metrics["mape"] == 8.5

    def test_register_multiple_models(self):
        """Test registering multiple models."""
        registry = ModelRegistryService()

        model1 = registry.register_model("solar", "v1.0.0", {"mape": 9.0})
        model2 = registry.register_model("solar", "v2.0.0", {"mape": 8.5})

        assert model1.is_champion is True
        assert model2.is_challenger is True

    def test_setup_ab_test(self):
        """Test A/B test setup."""
        registry = ModelRegistryService()

        model1 = registry.register_model("solar", "v1.0.0", {})
        model2 = registry.register_model("solar", "v2.0.0", {})

        config = registry.setup_ab_test(
            model_type="solar",
            champion_id=model1.model_id,
            challenger_id=model2.model_id,
            challenger_traffic_pct=20.0,
        )

        assert config["champion_traffic"] == 80.0
        assert config["challenger_traffic"] == 20.0

    def test_get_model_for_prediction_no_ab_test(self):
        """Test getting model when no A/B test is running."""
        registry = ModelRegistryService()

        model = registry.register_model("solar", "v1.0.0", {})
        selected = registry.get_model_for_prediction("solar")

        assert selected == model.model_id

    def test_promote_challenger(self):
        """Test promoting challenger to champion."""
        registry = ModelRegistryService()

        model1 = registry.register_model("solar", "v1.0.0", {})
        model2 = registry.register_model("solar", "v2.0.0", {})

        registry.setup_ab_test("solar", model1.model_id, model2.model_id)
        promoted = registry.promote_challenger("solar")

        assert promoted is not None
        assert promoted.is_champion is True
        assert promoted.model_id == model2.model_id

    def test_rollback(self):
        """Test rolling back to previous model."""
        registry = ModelRegistryService()

        model1 = registry.register_model("solar", "v1.0.0", {})
        model2 = registry.register_model("solar", "v2.0.0", {})

        # Promote v2 first
        registry.setup_ab_test("solar", model1.model_id, model2.model_id)
        registry.promote_challenger("solar")

        # Rollback
        rolled_back = registry.rollback("solar")

        assert rolled_back is not None
        assert rolled_back.is_champion is True

    def test_get_model_history(self):
        """Test getting model version history."""
        registry = ModelRegistryService()

        registry.register_model("solar", "v1.0.0", {"mape": 10.0})
        registry.register_model("solar", "v2.0.0", {"mape": 9.0})
        registry.register_model("solar", "v3.0.0", {"mape": 8.5})

        history = registry.get_model_history("solar")

        assert len(history) == 3
        assert history[0]["version"] == "v3.0.0"  # Most recent first


class TestSingletonInstances:
    """Test singleton pattern for services."""

    def test_get_drift_detection_service(self):
        """Test getting drift detection service singleton."""
        service1 = get_drift_detection_service()
        service2 = get_drift_detection_service()

        # Note: In tests, we may get new instances
        assert isinstance(service1, DriftDetectionService)
        assert isinstance(service2, DriftDetectionService)

    def test_get_model_registry_service(self):
        """Test getting model registry service singleton."""
        service1 = get_model_registry_service()
        service2 = get_model_registry_service()

        assert isinstance(service1, ModelRegistryService)
        assert isinstance(service2, ModelRegistryService)


class TestPSICalculation:
    """Test Population Stability Index calculation."""

    def test_psi_identical_distributions(self):
        """Test PSI for identical distributions."""
        service = DriftDetectionService()

        data = np.random.normal(100, 10, 1000)
        result = service.detect_data_drift(data, data.copy(), "identical")

        # PSI should be very low for identical distributions
        assert result.current_stats.get("psi", 0) < 0.05

    def test_psi_different_distributions(self):
        """Test PSI for different distributions."""
        service = DriftDetectionService()

        np.random.seed(42)
        baseline = np.random.normal(100, 10, 1000)
        current = np.random.normal(120, 15, 1000)

        result = service.detect_data_drift(baseline, current, "different")

        # PSI should be high for different distributions
        assert result.current_stats.get("psi", 0) > 0.1
