"""
Solar Feature Engineering for RE Forecast.

Based on CLAUDE.md specifications for solar power prediction.
Target: MAPE < 10%, RMSE < 100 kW, R² > 0.95
"""

import numpy as np
import pandas as pd


class SolarFeatureEngineer:
    """Feature engineering for RE Forecast (solar power prediction)."""

    REQUIRED_COLUMNS = [
        "time",
        "pyrano1",
        "pyrano2",
        "pvtemp1",
        "pvtemp2",
        "ambtemp",
        "windspeed",
    ]

    TARGET_COLUMN = "power_kw"

    def __init__(self, lag_periods: list[int] | None = None, rolling_windows: list[int] | None = None):
        """
        Initialize feature engineer.

        Args:
            lag_periods: List of lag periods for lag features (default: [1, 2, 3, 6, 12])
            rolling_windows: List of window sizes for rolling features (default: [6, 12, 24])
        """
        self.lag_periods = lag_periods or [1, 2, 3, 6, 12]
        self.rolling_windows = rolling_windows or [6, 12, 24]
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
            df: Input DataFrame with raw solar data
            include_target: Whether to include target column in output

        Returns:
            DataFrame with engineered features
        """
        self.validate_data(df)
        df = df.copy()

        # Ensure time column is datetime
        if not pd.api.types.is_datetime64_any_dtype(df["time"]):
            df["time"] = pd.to_datetime(df["time"])

        # Sort by time
        df = df.sort_values("time").reset_index(drop=True)

        # === Temporal Features ===
        df["hour"] = df["time"].dt.hour
        df["minute"] = df["time"].dt.minute
        df["day_of_week"] = df["time"].dt.dayofweek
        df["day_of_year"] = df["time"].dt.dayofyear
        df["month"] = df["time"].dt.month

        # Cyclical encoding for hour (captures daily pattern)
        df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
        df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)

        # Cyclical encoding for day of year (captures seasonal pattern)
        df["doy_sin"] = np.sin(2 * np.pi * df["day_of_year"] / 365)
        df["doy_cos"] = np.cos(2 * np.pi * df["day_of_year"] / 365)

        # Peak hour indicator (10:00 - 14:00 is typically peak solar)
        df["is_peak_hour"] = ((df["hour"] >= 10) & (df["hour"] <= 14)).astype(int)

        # Daylight indicator (6:00 - 18:00)
        df["is_daylight"] = ((df["hour"] >= 6) & (df["hour"] <= 18)).astype(int)

        # === Derived Sensor Features ===
        # Average irradiance from two sensors
        df["pyrano_avg"] = (df["pyrano1"] + df["pyrano2"]) / 2
        df["pyrano_diff"] = abs(df["pyrano1"] - df["pyrano2"])
        df["pyrano_max"] = df[["pyrano1", "pyrano2"]].max(axis=1)
        df["pyrano_min"] = df[["pyrano1", "pyrano2"]].min(axis=1)

        # Average PV temperature
        df["pvtemp_avg"] = (df["pvtemp1"] + df["pvtemp2"]) / 2
        df["pvtemp_diff"] = abs(df["pvtemp1"] - df["pvtemp2"])

        # Temperature delta (PV vs ambient) - indicates heating from sunlight
        df["temp_delta"] = df["pvtemp_avg"] - df["ambtemp"]

        # Temperature efficiency factor (higher temp = lower efficiency)
        # PV efficiency drops ~0.4% per degree above 25°C
        df["temp_efficiency"] = 1 - 0.004 * np.maximum(0, df["pvtemp_avg"] - 25)

        # Clear sky index approximation (actual irradiance vs expected max)
        # Max theoretical irradiance ~1000 W/m² at noon
        df["clear_sky_index"] = df["pyrano_avg"] / 1000.0
        df["clear_sky_index"] = df["clear_sky_index"].clip(0, 1)

        # === Physics-Based Power Estimation Features ===
        # Theoretical power = Irradiance * Area * Efficiency * Temperature Factor
        # Using normalized irradiance as proxy
        df["theoretical_power"] = df["pyrano_avg"] * df["temp_efficiency"]
        df["theoretical_power_squared"] = df["theoretical_power"] ** 2

        # Irradiance squared (captures non-linear relationship)
        df["pyrano_squared"] = df["pyrano_avg"] ** 2 / 1000.0  # Scale down

        # Wind cooling effect on panels
        df["wind_cooling"] = df["windspeed"] * df["temp_delta"]

        # Irradiance stability (sensor agreement indicates clear sky)
        df["irradiance_stability"] = 1 - (df["pyrano_diff"] / (df["pyrano_avg"] + 1))
        df["irradiance_stability"] = df["irradiance_stability"].clip(0, 1)

        # Power density indicator
        df["power_density"] = df["pyrano_avg"] * df["is_peak_hour"]

        # Morning/afternoon asymmetry
        df["is_morning"] = ((df["hour"] >= 6) & (df["hour"] < 12)).astype(int)
        df["is_afternoon"] = ((df["hour"] >= 12) & (df["hour"] <= 18)).astype(int)

        # === Lag Features ===
        for lag in self.lag_periods:
            df[f"pyrano_avg_lag_{lag}"] = df["pyrano_avg"].shift(lag)
            df[f"power_lag_{lag}"] = df[self.TARGET_COLUMN].shift(lag) if self.TARGET_COLUMN in df.columns else np.nan

        # === Rolling Statistics ===
        for window in self.rolling_windows:
            df[f"pyrano_avg_rolling_mean_{window}"] = df["pyrano_avg"].rolling(window, min_periods=1).mean()
            df[f"pyrano_avg_rolling_std_{window}"] = df["pyrano_avg"].rolling(window, min_periods=1).std().fillna(0)
            df[f"temp_delta_rolling_mean_{window}"] = df["temp_delta"].rolling(window, min_periods=1).mean()

        # === Rate of Change Features ===
        df["pyrano_change"] = df["pyrano_avg"].diff()
        df["temp_change"] = df["pvtemp_avg"].diff()

        # Store feature columns
        self._feature_columns = self.get_feature_columns()

        # Select output columns
        output_cols = self._feature_columns.copy()
        if include_target and self.TARGET_COLUMN in df.columns:
            output_cols.append(self.TARGET_COLUMN)

        # Keep time for reference
        output_cols = ["time"] + output_cols

        return df[output_cols]

    def get_feature_columns(self) -> list[str]:
        """Get list of feature column names (excludes time and target)."""
        base_features = [
            # Temporal
            "hour",
            "minute",
            "day_of_week",
            "day_of_year",
            "month",
            "hour_sin",
            "hour_cos",
            "doy_sin",
            "doy_cos",
            "is_peak_hour",
            "is_daylight",
            "is_morning",
            "is_afternoon",
            # Raw sensors
            "pyrano1",
            "pyrano2",
            "pvtemp1",
            "pvtemp2",
            "ambtemp",
            "windspeed",
            # Derived
            "pyrano_avg",
            "pyrano_diff",
            "pyrano_max",
            "pyrano_min",
            "pvtemp_avg",
            "pvtemp_diff",
            "temp_delta",
            "temp_efficiency",
            "clear_sky_index",
            # Physics-based
            "theoretical_power",
            "theoretical_power_squared",
            "pyrano_squared",
            "wind_cooling",
            "irradiance_stability",
            "power_density",
            # Rate of change
            "pyrano_change",
            "temp_change",
        ]

        # Add lag features
        for lag in self.lag_periods:
            base_features.append(f"pyrano_avg_lag_{lag}")
            base_features.append(f"power_lag_{lag}")

        # Add rolling features
        for window in self.rolling_windows:
            base_features.append(f"pyrano_avg_rolling_mean_{window}")
            base_features.append(f"pyrano_avg_rolling_std_{window}")
            base_features.append(f"temp_delta_rolling_mean_{window}")

        return base_features

    def prepare_train_data(self, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
        """
        Prepare data for training by applying transforms and handling missing values.

        Args:
            df: Raw solar data

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
