"""
Voltage Prediction Inference Service.

Loads the trained RandomForest model and provides prediction interface.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# Prosumer configuration
PROSUMER_CONFIG = {
    "prosumer1": {"phase": "A", "position": 3, "has_ev": True},
    "prosumer2": {"phase": "A", "position": 2, "has_ev": False},
    "prosumer3": {"phase": "A", "position": 1, "has_ev": False},
    "prosumer4": {"phase": "B", "position": 2, "has_ev": False},
    "prosumer5": {"phase": "B", "position": 3, "has_ev": True},
    "prosumer6": {"phase": "B", "position": 1, "has_ev": False},
    "prosumer7": {"phase": "C", "position": 1, "has_ev": True},
}


class VoltageInference:
    """Voltage prediction inference service."""

    def __init__(self, model_path: str | Path | None = None):
        """Initialize inference service."""
        self.model = None
        self.feature_columns: list[str] = []
        self.metrics: dict[str, Any] = {}
        self.version = "not_loaded"
        self._is_loaded = False

        if model_path is None:
            model_path = Path(__file__).parent.parent.parent.parent / "ml" / "models" / "voltage_rf_v1.joblib"

        self.model_path = Path(model_path)
        self._load_model()

    def _load_model(self) -> bool:
        """Load model from disk."""
        if not self.model_path.exists():
            logger.warning(f"Model file not found: {self.model_path}")
            return False

        try:
            artifact = joblib.load(self.model_path)
            self.model = artifact["model"]
            self.feature_columns = artifact["feature_columns"]
            self.metrics = artifact.get("metrics", {})
            self.version = artifact.get("version", "v1.0.0")
            self._is_loaded = True
            logger.info(f"Loaded voltage model: {self.version}")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False

    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._is_loaded

    def _create_features(
        self,
        timestamp: datetime,
        prosumer_id: str,
        active_power: float = 1.0,
        reactive_power: float = 0.1,
        current: float = 4.0,
    ) -> pd.DataFrame:
        """Create feature vector for prediction."""
        config = PROSUMER_CONFIG.get(prosumer_id, {"phase": "A", "position": 1, "has_ev": False})

        hour = timestamp.hour
        minute = timestamp.minute
        day_of_week = timestamp.weekday()

        features = {
            # Temporal
            "hour": hour,
            "minute": minute,
            "day_of_week": day_of_week,
            "is_weekend": 1 if day_of_week >= 5 else 0,
            "hour_sin": np.sin(2 * np.pi * hour / 24),
            "hour_cos": np.cos(2 * np.pi * hour / 24),
            "is_morning_peak": 1 if 7 <= hour <= 9 else 0,
            "is_evening_peak": 1 if 18 <= hour <= 21 else 0,
            "is_night": 1 if 0 <= hour <= 6 else 0,
            "is_midday": 1 if 10 <= hour <= 14 else 0,
            # Prosumer
            "phase_A": 1 if config["phase"] == "A" else 0,
            "phase_B": 1 if config["phase"] == "B" else 0,
            "phase_C": 1 if config["phase"] == "C" else 0,
            "position": config["position"],
            "has_ev": 1 if config["has_ev"] else 0,
            # Electrical
            "active_power": active_power,
            "reactive_power": reactive_power,
            "energy_meter_current": current,
            "apparent_power": np.sqrt(active_power**2 + reactive_power**2),
            "power_factor": active_power / max(np.sqrt(active_power**2 + reactive_power**2), 0.01),
            "voltage_drop_indicator": int(config["position"]) * active_power,
            "load_intensity": current * int(config["position"]),
            # Rate of change (use 0 for single point)
            "voltage_change": 0.0,
            "power_change": 0.0,
        }

        # Lag features (use nominal voltage ~228V as approximation)
        base_voltage = 230 - int(config["position"]) * 1.5
        for lag in [1, 2, 3, 6]:
            features[f"voltage_lag_{lag}"] = base_voltage
            features[f"power_lag_{lag}"] = active_power

        # Rolling features
        for window in [6, 12]:
            features[f"voltage_rolling_mean_{window}"] = base_voltage
            features[f"voltage_rolling_std_{window}"] = 1.0
            features[f"power_rolling_mean_{window}"] = active_power

        df = pd.DataFrame([features])

        for col in self.feature_columns:
            if col not in df.columns:
                df[col] = 0.0

        return pd.DataFrame(df[self.feature_columns])

    def predict(
        self,
        timestamp: datetime,
        prosumer_id: str,
        active_power: float = 1.0,
        reactive_power: float = 0.1,
        current: float = 4.0,
    ) -> dict[str, Any]:
        """
        Predict voltage level for a prosumer.

        Args:
            timestamp: Prediction timestamp
            prosumer_id: Prosumer identifier
            active_power: Active power (kW)
            reactive_power: Reactive power (kVAR)
            current: Current (A)

        Returns:
            Dictionary with prediction results
        """
        config = PROSUMER_CONFIG.get(prosumer_id, {"phase": "A", "position": 1, "has_ev": False})

        if not self._is_loaded:
            # Fallback to simple estimation
            base_voltage = 230.0 - int(config["position"]) * 1.5
            return {
                "predicted_voltage": round(base_voltage, 1),
                "confidence_lower": round(base_voltage - 3, 1),
                "confidence_upper": round(base_voltage + 3, 1),
                "phase": config["phase"],
                "status": "normal",
                "model_version": "fallback",
                "is_ml_prediction": False,
            }

        X = self._create_features(timestamp, prosumer_id, active_power, reactive_power, current)
        if self.model is None:
            raise RuntimeError("Model not loaded")
        predicted_voltage = float(self.model.predict(X)[0])

        # Calculate confidence based on CV metrics
        cv_mae = self.metrics.get("mae", 0.6)
        confidence_lower = predicted_voltage - 1.96 * cv_mae
        confidence_upper = predicted_voltage + 1.96 * cv_mae

        # Determine status
        if predicted_voltage < 218 or predicted_voltage > 242:
            status = "critical"
        elif predicted_voltage < 222 or predicted_voltage > 238:
            status = "warning"
        else:
            status = "normal"

        return {
            "predicted_voltage": round(predicted_voltage, 1),
            "confidence_lower": round(confidence_lower, 1),
            "confidence_upper": round(confidence_upper, 1),
            "phase": config["phase"],
            "status": status,
            "model_version": self.version,
            "is_ml_prediction": True,
        }


# Singleton instance
_voltage_inference: VoltageInference | None = None


def get_voltage_inference() -> VoltageInference:
    """Get or create voltage inference instance."""
    global _voltage_inference
    if _voltage_inference is None:
        _voltage_inference = VoltageInference()
    return _voltage_inference
