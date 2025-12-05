"""
Unit tests for model retraining API models.

Tests request/response models for retraining endpoints.
"""

import pytest

from app.api.v1.endpoints.retraining import (
    DriftDetectionRequest,
    RetrainingEvaluationRequest,
    ABTestRequest,
    ModelPromotionRequest,
    RetrainingTriggerConfig,
)


class TestDriftDetectionRequest:
    """Test DriftDetectionRequest model."""

    def test_create_request(self):
        request = DriftDetectionRequest(
            model_type="solar",
            baseline_days=30,
            current_days=7,
        )
        assert request.model_type == "solar"
        assert request.baseline_days == 30
        assert request.current_days == 7

    def test_default_values(self):
        request = DriftDetectionRequest(model_type="voltage")
        assert request.baseline_days == 30
        assert request.current_days == 7
        assert request.features is None

    def test_with_features(self):
        request = DriftDetectionRequest(
            model_type="solar",
            features=["pyrano1", "ambtemp"]
        )
        assert request.features == ["pyrano1", "ambtemp"]


class TestRetrainingEvaluationRequest:
    """Test RetrainingEvaluationRequest model."""

    def test_create_request(self):
        request = RetrainingEvaluationRequest(
            model_type="solar",
        )
        assert request.model_type == "solar"
        assert request.force_check is False

    def test_force_check(self):
        request = RetrainingEvaluationRequest(
            model_type="voltage",
            force_check=True,
        )
        assert request.force_check is True


class TestABTestRequest:
    """Test ABTestRequest model."""

    def test_create_request(self):
        request = ABTestRequest(
            model_type="solar",
            champion_id="model_v1",
            challenger_id="model_v2",
            challenger_traffic_pct=20.0,
        )
        assert request.model_type == "solar"
        assert request.champion_id == "model_v1"
        assert request.challenger_id == "model_v2"
        assert request.challenger_traffic_pct == 20.0

    def test_default_traffic(self):
        request = ABTestRequest(
            model_type="solar",
            champion_id="model_v1",
            challenger_id="model_v2",
        )
        assert request.challenger_traffic_pct == 10.0


class TestModelPromotionRequest:
    """Test ModelPromotionRequest model."""

    def test_promote_request(self):
        request = ModelPromotionRequest(
            model_type="solar",
            action="promote",
        )
        assert request.action == "promote"

    def test_rollback_request(self):
        request = ModelPromotionRequest(
            model_type="solar",
            action="rollback",
            target_version="v1.0.0",
        )
        assert request.action == "rollback"
        assert request.target_version == "v1.0.0"


class TestRetrainingTriggerConfig:
    """Test RetrainingTriggerConfig model."""

    def test_default_values(self):
        config = RetrainingTriggerConfig()
        assert config.mape_threshold == 12.0
        assert config.mae_threshold_voltage == 2.5
        assert config.drift_score_threshold == 2.0
        assert config.max_days_without_retrain == 30
        assert config.consecutive_violations == 3

    def test_custom_values(self):
        config = RetrainingTriggerConfig(
            mape_threshold=15.0,
            mae_threshold_voltage=3.0,
            drift_score_threshold=2.5,
            max_days_without_retrain=60,
            consecutive_violations=5,
        )
        assert config.mape_threshold == 15.0
        assert config.mae_threshold_voltage == 3.0
