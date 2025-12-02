"""
Voltage Feature Engineering for Voltage Prediction.

Based on CLAUDE.md specifications for voltage prediction.
Target: MAE < 2V, RMSE < 3V, R² > 0.90
"""

import numpy as np
import pandas as pd


# Prosumer configuration from network topology
PROSUMER_CONFIG = {
    "prosumer1": {"phase": "A", "position": 3, "has_ev": True},
    "prosumer2": {"phase": "A", "position": 2, "has_ev": False},
    "prosumer3": {"phase": "A", "position": 1, "has_ev": False},
    "prosumer4": {"phase": "B", "position": 2, "has_ev": False},
    "prosumer5": {"phase": "B", "position": 3, "has_ev": True},
    "prosumer6": {"phase": "B", "position": 1, "has_ev": False},
    "prosumer7": {"phase": "C", "position": 1, "has_ev": True},
}


class VoltageFeatureEngineer:
    """Feature engineering for voltage prediction."""

    REQUIRED_COLUMNS = [
        "time",
        "prosumer_id",
        "active_power",
        "reactive_power",
        "energy_meter_current",
    ]

    TARGET_COLUMN = "energy_meter_voltage"

    def __init__(self, lag_periods: list[int] | None = None, rolling_windows: list[int] | None = None):
        """
        Initialize feature engineer.

        Args:
            lag_periods: List of lag periods (default: [1, 2, 3, 6])
            rolling_windows: List of window sizes (default: [6, 12])
        """
        self.lag_periods = lag_periods or [1, 2, 3, 6]
        self.rolling_windows = rolling_windows or [6, 12]
        self._feature_columns: list[str] = []

    def validate_data(self, df: pd.DataFrame) -> bool:
        """Validate that required columns are present."""
        missing = set(self.REQUIRED_COLUMNS) - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        return True

    def transform(self, df: pd.DataFrame, include_target: bool = True) -> pd.DataFrame:
        """
        Apply feature engineering transformations.

        Args:
            df: Input DataFrame with raw voltage data
            include_target: Whether to include target column in output

        Returns:
            DataFrame with engineered features
        """
        self.validate_data(df)
        df = df.copy()

        # Ensure time column is datetime
        if not pd.api.types.is_datetime64_any_dtype(df["time"]):
            df["time"] = pd.to_datetime(df["time"])

        # Sort by prosumer and time
        df = df.sort_values(["prosumer_id", "time"]).reset_index(drop=True)

        # === Temporal Features ===
        df["hour"] = df["time"].dt.hour
        df["minute"] = df["time"].dt.minute
        df["day_of_week"] = df["time"].dt.dayofweek
        df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)

        # Cyclical encoding for hour
        df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
        df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)

        # Time period indicators
        df["is_morning_peak"] = ((df["hour"] >= 7) & (df["hour"] <= 9)).astype(int)
        df["is_evening_peak"] = ((df["hour"] >= 18) & (df["hour"] <= 21)).astype(int)
        df["is_night"] = ((df["hour"] >= 0) & (df["hour"] <= 6)).astype(int)
        df["is_midday"] = ((df["hour"] >= 10) & (df["hour"] <= 14)).astype(int)

        # === Prosumer Features ===
        df["phase_A"] = (df["prosumer_id"].map(lambda x: PROSUMER_CONFIG.get(x, {}).get("phase")) == "A").astype(int)
        df["phase_B"] = (df["prosumer_id"].map(lambda x: PROSUMER_CONFIG.get(x, {}).get("phase")) == "B").astype(int)
        df["phase_C"] = (df["prosumer_id"].map(lambda x: PROSUMER_CONFIG.get(x, {}).get("phase")) == "C").astype(int)
        df["position"] = df["prosumer_id"].map(lambda x: PROSUMER_CONFIG.get(x, {}).get("position", 1))
        df["has_ev"] = df["prosumer_id"].map(lambda x: PROSUMER_CONFIG.get(x, {}).get("has_ev", False)).astype(int)

        # === Electrical Features ===
        # Power factor approximation
        df["apparent_power"] = np.sqrt(df["active_power"] ** 2 + df["reactive_power"] ** 2)
        df["power_factor"] = np.where(
            df["apparent_power"] > 0,
            df["active_power"] / df["apparent_power"],
            1.0
        )

        # Voltage drop indicator (position * power)
        df["voltage_drop_indicator"] = df["position"] * df["active_power"]

        # Load intensity
        df["load_intensity"] = df["energy_meter_current"] * df["position"]

        # === Lag Features (per prosumer) ===
        for lag in self.lag_periods:
            df[f"voltage_lag_{lag}"] = df.groupby("prosumer_id")[self.TARGET_COLUMN].shift(lag)
            df[f"power_lag_{lag}"] = df.groupby("prosumer_id")["active_power"].shift(lag)

        # === Rolling Statistics (per prosumer) ===
        for window in self.rolling_windows:
            df[f"voltage_rolling_mean_{window}"] = df.groupby("prosumer_id")[self.TARGET_COLUMN].transform(
                lambda x: x.rolling(window, min_periods=1).mean()
            )
            df[f"voltage_rolling_std_{window}"] = df.groupby("prosumer_id")[self.TARGET_COLUMN].transform(
                lambda x: x.rolling(window, min_periods=1).std().fillna(0)
            )
            df[f"power_rolling_mean_{window}"] = df.groupby("prosumer_id")["active_power"].transform(
                lambda x: x.rolling(window, min_periods=1).mean()
            )

        # === Rate of Change ===
        df["voltage_change"] = df.groupby("prosumer_id")[self.TARGET_COLUMN].diff()
        df["power_change"] = df.groupby("prosumer_id")["active_power"].diff()

        # Store feature columns
        self._feature_columns = self.get_feature_columns()

        # Select output columns
        output_cols = self._feature_columns.copy()
        if include_target and self.TARGET_COLUMN in df.columns:
            output_cols.append(self.TARGET_COLUMN)

        # Keep time and prosumer_id for reference
        output_cols = ["time", "prosumer_id"] + output_cols

        return df[output_cols]

    def get_feature_columns(self) -> list[str]:
        """Get list of feature column names (excludes time, prosumer_id, and target)."""
        base_features = [
            # Temporal
            "hour",
            "minute",
            "day_of_week",
            "is_weekend",
            "hour_sin",
            "hour_cos",
            "is_morning_peak",
            "is_evening_peak",
            "is_night",
            "is_midday",
            # Prosumer
            "phase_A",
            "phase_B",
            "phase_C",
            "position",
            "has_ev",
            # Electrical
            "active_power",
            "reactive_power",
            "energy_meter_current",
            "apparent_power",
            "power_factor",
            "voltage_drop_indicator",
            "load_intensity",
            # Rate of change
            "voltage_change",
            "power_change",
        ]

        # Add lag features
        for lag in self.lag_periods:
            base_features.append(f"voltage_lag_{lag}")
            base_features.append(f"power_lag_{lag}")

        # Add rolling features
        for window in self.rolling_windows:
            base_features.append(f"voltage_rolling_mean_{window}")
            base_features.append(f"voltage_rolling_std_{window}")
            base_features.append(f"power_rolling_mean_{window}")

        return base_features

    def prepare_train_data(self, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
        """
        Prepare data for training.

        Args:
            df: Raw voltage data

        Returns:
            Tuple of (X features, y target)
        """
        # Transform
        df_transformed = self.transform(df, include_target=True)

        # Drop rows with NaN (from lag/rolling features)
        df_clean = df_transformed.dropna()

        # Split features and target
        feature_cols = self.get_feature_columns()
        X = df_clean[feature_cols]
        y = df_clean[self.TARGET_COLUMN]

        return X, y
