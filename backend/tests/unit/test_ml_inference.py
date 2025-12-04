"""
Unit tests for ML inference modules.

Tests the solar and voltage prediction inference services.
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from app.ml.solar_inference import SolarInference, get_solar_inference
from app.ml.voltage_inference import (
    PROSUMER_CONFIG,
    VoltageInference,
    get_voltage_inference,
)


class TestSolarInference:
    """Tests for SolarInference class."""

    def test_init_without_model_file(self):
        """Test initialization when model file doesn't exist."""
        inference = SolarInference(model_path="/nonexistent/path/model.joblib")
        assert inference.is_loaded is False
        assert inference.version == "not_loaded"

    def test_is_loaded_property(self):
        """Test is_loaded property."""
        inference = SolarInference(model_path="/nonexistent/path/model.joblib")
        assert inference.is_loaded is False

    def test_predict_fallback(self):
        """Test prediction falls back to linear estimation when no model."""
        inference = SolarInference(model_path="/nonexistent/path/model.joblib")
        result = inference.predict(
            timestamp=datetime(2025, 1, 15, 12, 0),
            pyrano1=800.0,
            pyrano2=810.0,
            pvtemp1=45.0,
            pvtemp2=44.0,
            ambtemp=32.0,
            windspeed=2.5,
        )

        assert "power_kw" in result
        assert "confidence_lower" in result
        assert "confidence_upper" in result
        assert result["model_version"] == "fallback-linear"
        assert result["is_ml_prediction"] is False
        # Check reasonable power output
        assert result["power_kw"] > 0

    def test_predict_fallback_confidence_interval(self):
        """Test fallback prediction includes proper confidence intervals."""
        inference = SolarInference(model_path="/nonexistent/path/model.joblib")
        result = inference.predict(
            timestamp=datetime(2025, 1, 15, 12, 0),
            pyrano1=800.0,
            pyrano2=800.0,
            pvtemp1=45.0,
            pvtemp2=45.0,
            ambtemp=32.0,
            windspeed=2.0,
        )

        # Confidence interval should be 15% around prediction
        assert result["confidence_lower"] < result["power_kw"]
        assert result["confidence_upper"] > result["power_kw"]

    def test_predict_low_irradiance(self):
        """Test prediction with low irradiance (nighttime)."""
        inference = SolarInference(model_path="/nonexistent/path/model.joblib")
        result = inference.predict(
            timestamp=datetime(2025, 1, 15, 2, 0),  # 2 AM
            pyrano1=0.0,
            pyrano2=0.0,
            pvtemp1=25.0,
            pvtemp2=25.0,
            ambtemp=25.0,
            windspeed=1.0,
        )

        # Should have zero or near-zero power at night
        assert result["power_kw"] == 0.0

    def test_predict_high_irradiance(self):
        """Test prediction with high irradiance (peak sun)."""
        inference = SolarInference(model_path="/nonexistent/path/model.joblib")
        result = inference.predict(
            timestamp=datetime(2025, 1, 15, 12, 0),  # Noon
            pyrano1=1000.0,
            pyrano2=1000.0,
            pvtemp1=50.0,
            pvtemp2=50.0,
            ambtemp=35.0,
            windspeed=3.0,
        )

        # Should have high power at peak sun
        assert result["power_kw"] > 0

    def test_create_features_structure(self):
        """Test that _create_features creates proper DataFrame."""
        inference = SolarInference(model_path="/nonexistent/path/model.joblib")
        # Set minimal feature columns for testing
        inference.feature_columns = ["hour", "pyrano1", "pyrano_avg"]
        inference.lag_periods = [1]
        inference.rolling_windows = [6]

        df = inference._create_features(
            timestamp=datetime(2025, 1, 15, 12, 30),
            pyrano1=800.0,
            pyrano2=810.0,
            pvtemp1=45.0,
            pvtemp2=44.0,
            ambtemp=32.0,
            windspeed=2.5,
        )

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert "hour" in df.columns
        assert "pyrano1" in df.columns
        assert "pyrano_avg" in df.columns

    def test_create_features_temporal(self):
        """Test temporal feature creation."""
        inference = SolarInference(model_path="/nonexistent/path/model.joblib")
        inference.feature_columns = ["hour", "is_peak_hour", "is_daylight"]
        inference.lag_periods = []
        inference.rolling_windows = []

        # Peak hour test (12:00)
        df_peak = inference._create_features(
            timestamp=datetime(2025, 1, 15, 12, 0),
            pyrano1=800.0,
            pyrano2=800.0,
            pvtemp1=45.0,
            pvtemp2=45.0,
            ambtemp=32.0,
            windspeed=2.0,
        )
        assert df_peak["is_peak_hour"].iloc[0] == 1
        assert df_peak["is_daylight"].iloc[0] == 1

        # Night test (2:00)
        df_night = inference._create_features(
            timestamp=datetime(2025, 1, 15, 2, 0),
            pyrano1=0.0,
            pyrano2=0.0,
            pvtemp1=25.0,
            pvtemp2=25.0,
            ambtemp=25.0,
            windspeed=1.0,
        )
        assert df_night["is_peak_hour"].iloc[0] == 0
        assert df_night["is_daylight"].iloc[0] == 0


class TestVoltageInference:
    """Tests for VoltageInference class."""

    def test_init_without_model_file(self):
        """Test initialization when model file doesn't exist."""
        inference = VoltageInference(model_path="/nonexistent/path/model.joblib")
        assert inference.is_loaded is False
        assert inference.version == "not_loaded"

    def test_prosumer_config_structure(self):
        """Test prosumer configuration is correct."""
        assert "prosumer1" in PROSUMER_CONFIG
        assert "phase" in PROSUMER_CONFIG["prosumer1"]
        assert "position" in PROSUMER_CONFIG["prosumer1"]
        assert "has_ev" in PROSUMER_CONFIG["prosumer1"]

    def test_prosumer_phases(self):
        """Test all prosumers have valid phases."""
        valid_phases = {"A", "B", "C"}
        for prosumer_id, config in PROSUMER_CONFIG.items():
            assert config["phase"] in valid_phases

    def test_prosumer_positions(self):
        """Test all prosumers have valid positions (1-3)."""
        for prosumer_id, config in PROSUMER_CONFIG.items():
            assert 1 <= config["position"] <= 3

    def test_predict_fallback(self):
        """Test prediction falls back when no model loaded."""
        inference = VoltageInference(model_path="/nonexistent/path/model.joblib")
        result = inference.predict(
            timestamp=datetime(2025, 1, 15, 12, 0),
            prosumer_id="prosumer1",
            active_power=1.5,
            reactive_power=0.2,
            current=6.0,
        )

        assert "predicted_voltage" in result
        assert "confidence_lower" in result
        assert "confidence_upper" in result
        assert result["model_version"] == "fallback"
        assert result["is_ml_prediction"] is False
        assert result["phase"] == "A"  # prosumer1 is on phase A

    def test_predict_fallback_voltage_range(self):
        """Test fallback prediction gives reasonable voltage."""
        inference = VoltageInference(model_path="/nonexistent/path/model.joblib")
        result = inference.predict(
            timestamp=datetime(2025, 1, 15, 12, 0),
            prosumer_id="prosumer1",
        )

        # Voltage should be within acceptable range (218-242V)
        assert 210 <= result["predicted_voltage"] <= 245

    def test_predict_all_prosumers(self):
        """Test prediction for all configured prosumers."""
        inference = VoltageInference(model_path="/nonexistent/path/model.joblib")

        for prosumer_id in PROSUMER_CONFIG.keys():
            result = inference.predict(
                timestamp=datetime(2025, 1, 15, 12, 0),
                prosumer_id=prosumer_id,
            )
            assert "predicted_voltage" in result
            assert result["phase"] == PROSUMER_CONFIG[prosumer_id]["phase"]

    def test_predict_unknown_prosumer(self):
        """Test prediction for unknown prosumer uses default config."""
        inference = VoltageInference(model_path="/nonexistent/path/model.joblib")
        result = inference.predict(
            timestamp=datetime(2025, 1, 15, 12, 0),
            prosumer_id="unknown_prosumer",
        )

        assert "predicted_voltage" in result
        # Should use default phase A, position 1

    def test_create_features_structure(self):
        """Test that _create_features creates proper DataFrame."""
        inference = VoltageInference(model_path="/nonexistent/path/model.joblib")
        inference.feature_columns = ["hour", "phase_A", "position"]

        df = inference._create_features(
            timestamp=datetime(2025, 1, 15, 12, 0),
            prosumer_id="prosumer1",
        )

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert "hour" in df.columns
        assert "phase_A" in df.columns
        assert "position" in df.columns

    def test_create_features_phase_encoding(self):
        """Test phase one-hot encoding."""
        inference = VoltageInference(model_path="/nonexistent/path/model.joblib")
        inference.feature_columns = ["phase_A", "phase_B", "phase_C"]

        # Test Phase A prosumer
        df_a = inference._create_features(
            timestamp=datetime(2025, 1, 15, 12, 0),
            prosumer_id="prosumer1",  # Phase A
        )
        assert df_a["phase_A"].iloc[0] == 1
        assert df_a["phase_B"].iloc[0] == 0
        assert df_a["phase_C"].iloc[0] == 0

        # Test Phase B prosumer
        df_b = inference._create_features(
            timestamp=datetime(2025, 1, 15, 12, 0),
            prosumer_id="prosumer4",  # Phase B
        )
        assert df_b["phase_A"].iloc[0] == 0
        assert df_b["phase_B"].iloc[0] == 1
        assert df_b["phase_C"].iloc[0] == 0

        # Test Phase C prosumer
        df_c = inference._create_features(
            timestamp=datetime(2025, 1, 15, 12, 0),
            prosumer_id="prosumer7",  # Phase C
        )
        assert df_c["phase_A"].iloc[0] == 0
        assert df_c["phase_B"].iloc[0] == 0
        assert df_c["phase_C"].iloc[0] == 1

    def test_create_features_temporal(self):
        """Test temporal feature creation."""
        inference = VoltageInference(model_path="/nonexistent/path/model.joblib")
        inference.feature_columns = [
            "is_morning_peak",
            "is_evening_peak",
            "is_weekend",
        ]

        # Morning peak (8 AM Monday)
        df_morning = inference._create_features(
            timestamp=datetime(2025, 1, 13, 8, 0),  # Monday
            prosumer_id="prosumer1",
        )
        assert df_morning["is_morning_peak"].iloc[0] == 1
        assert df_morning["is_weekend"].iloc[0] == 0

        # Evening peak (7 PM)
        df_evening = inference._create_features(
            timestamp=datetime(2025, 1, 13, 19, 0),
            prosumer_id="prosumer1",
        )
        assert df_evening["is_evening_peak"].iloc[0] == 1

        # Weekend
        df_weekend = inference._create_features(
            timestamp=datetime(2025, 1, 11, 12, 0),  # Saturday
            prosumer_id="prosumer1",
        )
        assert df_weekend["is_weekend"].iloc[0] == 1

    def test_create_features_electrical(self):
        """Test electrical feature calculation."""
        inference = VoltageInference(model_path="/nonexistent/path/model.joblib")
        inference.feature_columns = ["apparent_power", "power_factor", "active_power"]

        df = inference._create_features(
            timestamp=datetime(2025, 1, 15, 12, 0),
            prosumer_id="prosumer1",
            active_power=3.0,
            reactive_power=4.0,
            current=10.0,
        )

        # Apparent power = sqrt(3^2 + 4^2) = 5
        assert abs(df["apparent_power"].iloc[0] - 5.0) < 0.01

        # Power factor = 3/5 = 0.6
        assert abs(df["power_factor"].iloc[0] - 0.6) < 0.01


class TestInferenceSingletons:
    """Tests for singleton pattern functions."""

    def test_get_solar_inference_returns_instance(self):
        """Test get_solar_inference returns an instance."""
        with patch("app.ml.solar_inference._solar_inference", None):
            inference = get_solar_inference()
            assert isinstance(inference, SolarInference)

    def test_get_voltage_inference_returns_instance(self):
        """Test get_voltage_inference returns an instance."""
        with patch("app.ml.voltage_inference._voltage_inference", None):
            inference = get_voltage_inference()
            assert isinstance(inference, VoltageInference)


class TestVoltageStatus:
    """Tests for voltage status determination."""

    def test_voltage_status_normal(self):
        """Test normal status for voltage in safe range."""
        inference = VoltageInference(model_path="/nonexistent/path/model.joblib")
        # Prosumer 6 is at position 1 (near transformer)
        # Base voltage = 230 - 1*1.5 = 228.5V (normal range)
        result = inference.predict(
            timestamp=datetime(2025, 1, 15, 12, 0),
            prosumer_id="prosumer6",
        )
        assert result["status"] == "normal"

    def test_voltage_confidence_bounds(self):
        """Test confidence bounds are reasonable."""
        inference = VoltageInference(model_path="/nonexistent/path/model.joblib")
        result = inference.predict(
            timestamp=datetime(2025, 1, 15, 12, 0),
            prosumer_id="prosumer1",
        )

        # Confidence interval should bracket the prediction
        assert result["confidence_lower"] < result["predicted_voltage"]
        assert result["confidence_upper"] > result["predicted_voltage"]


class TestMissingFeatureHandling:
    """Tests for handling missing features in models."""

    def test_solar_missing_feature_columns(self):
        """Test solar inference handles missing feature columns."""
        inference = SolarInference(model_path="/nonexistent/path/model.joblib")
        # Set feature columns that don't all exist in features dict
        inference.feature_columns = ["hour", "nonexistent_feature"]
        inference.lag_periods = []
        inference.rolling_windows = []

        df = inference._create_features(
            timestamp=datetime(2025, 1, 15, 12, 0),
            pyrano1=800.0,
            pyrano2=800.0,
            pvtemp1=45.0,
            pvtemp2=45.0,
            ambtemp=32.0,
            windspeed=2.0,
        )

        # Missing feature should be filled with 0.0
        assert "nonexistent_feature" in df.columns
        assert df["nonexistent_feature"].iloc[0] == 0.0

    def test_voltage_missing_feature_columns(self):
        """Test voltage inference handles missing feature columns."""
        inference = VoltageInference(model_path="/nonexistent/path/model.joblib")
        inference.feature_columns = ["hour", "nonexistent_feature"]

        df = inference._create_features(
            timestamp=datetime(2025, 1, 15, 12, 0),
            prosumer_id="prosumer1",
        )

        # Missing feature should be filled with 0.0
        assert "nonexistent_feature" in df.columns
        assert df["nonexistent_feature"].iloc[0] == 0.0
