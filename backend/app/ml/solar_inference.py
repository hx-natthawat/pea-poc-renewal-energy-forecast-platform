"""
Solar Power Prediction Inference Service.

Loads the trained XGBoost/GradientBoosting model and provides prediction interface.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class SolarInference:
    """Solar power prediction inference service."""

    def __init__(self, model_path: str | Path | None = None):
        """
        Initialize inference service.

        Args:
            model_path: Path to trained model file. If None, uses default path.
        """
        self.model = None
        self.feature_columns: list[str] = []
        self.lag_periods: list[int] = []
        self.rolling_windows: list[int] = []
        self.metrics: dict[str, Any] = {}
        self.version = "not_loaded"
        self._is_loaded = False

        # Default model path
        if model_path is None:
            model_path = Path(__file__).parent.parent.parent.parent / "ml" / "models" / "solar_xgb_v1.joblib"

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
            self.lag_periods = artifact.get("lag_periods", [1, 2, 3, 6, 12])
            self.rolling_windows = artifact.get("rolling_windows", [6, 12, 24])
            self.metrics = artifact.get("metrics", {})
            self.version = artifact.get("version", "v1.0.0")
            self._is_loaded = True
            logger.info(f"Loaded solar model: {self.version}")
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
        pyrano1: float,
        pyrano2: float,
        pvtemp1: float,
        pvtemp2: float,
        ambtemp: float,
        windspeed: float,
    ) -> pd.DataFrame:
        """
        Create feature vector for prediction.

        Note: For real-time prediction, we don't have lag/rolling features from history.
        We use approximations based on current values.
        """
        # Temporal features
        hour = timestamp.hour
        minute = timestamp.minute
        day_of_week = timestamp.weekday()
        day_of_year = timestamp.timetuple().tm_yday
        month = timestamp.month

        hour_sin = np.sin(2 * np.pi * hour / 24)
        hour_cos = np.cos(2 * np.pi * hour / 24)
        doy_sin = np.sin(2 * np.pi * day_of_year / 365)
        doy_cos = np.cos(2 * np.pi * day_of_year / 365)
        is_peak_hour = 1 if 10 <= hour <= 14 else 0
        is_daylight = 1 if 6 <= hour <= 18 else 0

        # Derived features
        pyrano_avg = (pyrano1 + pyrano2) / 2
        pyrano_diff = abs(pyrano1 - pyrano2)
        pvtemp_avg = (pvtemp1 + pvtemp2) / 2
        pvtemp_diff = abs(pvtemp1 - pvtemp2)
        temp_delta = pvtemp_avg - ambtemp
        temp_efficiency = 1 - 0.004 * max(0, pvtemp_avg - 25)
        clear_sky_index = min(1.0, max(0.0, pyrano_avg / 1000.0))

        # Rate of change (use 0 for single point prediction)
        pyrano_change = 0.0
        temp_change = 0.0

        # Create base features dict
        features = {
            "hour": hour,
            "minute": minute,
            "day_of_week": day_of_week,
            "day_of_year": day_of_year,
            "month": month,
            "hour_sin": hour_sin,
            "hour_cos": hour_cos,
            "doy_sin": doy_sin,
            "doy_cos": doy_cos,
            "is_peak_hour": is_peak_hour,
            "is_daylight": is_daylight,
            "pyrano1": pyrano1,
            "pyrano2": pyrano2,
            "pvtemp1": pvtemp1,
            "pvtemp2": pvtemp2,
            "ambtemp": ambtemp,
            "windspeed": windspeed,
            "pyrano_avg": pyrano_avg,
            "pyrano_diff": pyrano_diff,
            "pvtemp_avg": pvtemp_avg,
            "pvtemp_diff": pvtemp_diff,
            "temp_delta": temp_delta,
            "temp_efficiency": temp_efficiency,
            "clear_sky_index": clear_sky_index,
            "pyrano_change": pyrano_change,
            "temp_change": temp_change,
        }

        # Add lag features (use current value as approximation)
        for lag in self.lag_periods:
            features[f"pyrano_avg_lag_{lag}"] = pyrano_avg
            features[f"power_lag_{lag}"] = pyrano_avg * 4.0  # Approximate

        # Add rolling features (use current value as approximation)
        for window in self.rolling_windows:
            features[f"pyrano_avg_rolling_mean_{window}"] = pyrano_avg
            features[f"pyrano_avg_rolling_std_{window}"] = 10.0  # Approximate std
            features[f"temp_delta_rolling_mean_{window}"] = temp_delta

        # Create DataFrame with correct column order
        df = pd.DataFrame([features])

        # Ensure all required columns exist
        for col in self.feature_columns:
            if col not in df.columns:
                df[col] = 0.0

        return pd.DataFrame(df[self.feature_columns])

    def predict(
        self,
        timestamp: datetime,
        pyrano1: float,
        pyrano2: float,
        pvtemp1: float,
        pvtemp2: float,
        ambtemp: float,
        windspeed: float,
    ) -> dict[str, Any]:
        """
        Predict solar power output.

        Args:
            timestamp: Prediction timestamp
            pyrano1: Irradiance sensor 1 (W/m²)
            pyrano2: Irradiance sensor 2 (W/m²)
            pvtemp1: PV temperature 1 (°C)
            pvtemp2: PV temperature 2 (°C)
            ambtemp: Ambient temperature (°C)
            windspeed: Wind speed (m/s)

        Returns:
            Dictionary with prediction results
        """
        if not self._is_loaded:
            # Fallback to simple estimation if model not loaded
            avg_irradiance = (pyrano1 + pyrano2) / 2
            power_kw = avg_irradiance * 4.0
            return {
                "power_kw": round(power_kw, 2),
                "confidence_lower": round(power_kw * 0.85, 2),
                "confidence_upper": round(power_kw * 1.15, 2),
                "model_version": "fallback-linear",
                "is_ml_prediction": False,
            }

        # Create features
        X = self._create_features(
            timestamp, pyrano1, pyrano2, pvtemp1, pvtemp2, ambtemp, windspeed
        )

        # Predict
        if self.model is None:
            raise RuntimeError("Model not loaded")
        power_kw = float(self.model.predict(X)[0])

        # Ensure non-negative
        power_kw = max(0.0, power_kw)

        # Calculate confidence interval (approximate based on CV metrics)
        cv_rmse = self.metrics.get("rmse", 40.0)
        confidence_lower = max(0.0, power_kw - 1.96 * cv_rmse)
        confidence_upper = power_kw + 1.96 * cv_rmse

        return {
            "power_kw": round(power_kw, 2),
            "confidence_lower": round(confidence_lower, 2),
            "confidence_upper": round(confidence_upper, 2),
            "model_version": self.version,
            "is_ml_prediction": True,
        }


# Singleton instance
_solar_inference: SolarInference | None = None


def get_solar_inference() -> SolarInference:
    """Get or create solar inference instance."""
    global _solar_inference
    if _solar_inference is None:
        _solar_inference = SolarInference()
    return _solar_inference
