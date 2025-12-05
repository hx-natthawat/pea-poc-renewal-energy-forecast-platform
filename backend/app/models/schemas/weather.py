"""Weather handling schemas for extreme weather conditions."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class WeatherCondition(str, Enum):
    """Weather condition classification based on clearness index."""

    CLEAR = "clear"  # kt >= 0.7
    PARTLY_CLOUDY = "partly_cloudy"  # 0.5 <= kt < 0.7
    CLOUDY = "cloudy"  # 0.3 <= kt < 0.5
    RAINY = "rainy"  # kt < 0.3
    STORM = "storm"  # Extreme event flag


class AlertSeverity(str, Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class WeatherAlert(BaseModel):
    """Weather alert from TMD or detected by system."""

    id: str
    timestamp: datetime
    condition: WeatherCondition
    severity: AlertSeverity
    region: str
    description: str
    expected_duration_minutes: int
    recommended_action: str


class RampEvent(BaseModel):
    """Detected ramp rate event (sudden irradiance change)."""

    timestamp: datetime
    rate_percent: float = Field(description="Rate of change in percent")
    direction: str = Field(description="'up' or 'down'")
    current_irradiance: float = Field(description="Current irradiance in W/m²")
    previous_irradiance: float = Field(description="Previous irradiance in W/m²")


class CloudEvent(BaseModel):
    """Detected cloud shadow event."""

    start: datetime
    end: datetime
    duration_minutes: float
    min_clearness: float = Field(ge=0, le=1)
    avg_clearness: float = Field(ge=0, le=1)


class ProbabilisticForecast(BaseModel):
    """Probabilistic forecast with confidence intervals."""

    timestamp: datetime
    horizon_minutes: int
    point_forecast: float = Field(description="Best estimate (P50)")
    p10: float = Field(description="10th percentile (pessimistic)")
    p50: float = Field(description="50th percentile (median)")
    p90: float = Field(description="90th percentile (optimistic)")
    weather_condition: WeatherCondition
    clearness_index: float = Field(ge=0, le=1.5)
    variability_index: float = Field(ge=0)
    uncertainty_factor: float = Field(ge=1.0)
    is_high_uncertainty: bool
    model_version: str


class WeatherEventLog(BaseModel):
    """Logged weather event for post-event learning."""

    id: int
    timestamp: datetime
    event_type: str
    severity: AlertSeverity
    station_id: str
    min_irradiance: float | None = None
    max_irradiance: float | None = None
    min_clearness_index: float | None = None
    duration_minutes: int | None = None
    forecast_error_mape: float | None = None
    forecast_error_rmse: float | None = None
    tmd_alert_id: str | None = None


class RampRateStatus(BaseModel):
    """Current ramp rate monitoring status."""

    current_ramp_rate_percent: float
    threshold_percent: float
    is_alert: bool
    last_event: RampEvent | None = None
    timestamp: datetime


class WeatherConditionResponse(BaseModel):
    """Weather condition classification response."""

    condition: WeatherCondition
    clearness_index: float | None = None
    cloud_cover_percent: float | None = None
    precipitation_mm: float | None = None
    wind_speed_kmh: float | None = None
    timestamp: datetime


class UncertaintyConfig(BaseModel):
    """Uncertainty multiplier configuration by weather condition."""

    clear: float = 1.0
    partly_cloudy: float = 1.5
    cloudy: float = 2.0
    rainy: float = 3.0
    storm: float = 5.0

    def get_multiplier(self, condition: WeatherCondition) -> float:
        """Get uncertainty multiplier for a weather condition."""
        mapping = {
            WeatherCondition.CLEAR: self.clear,
            WeatherCondition.PARTLY_CLOUDY: self.partly_cloudy,
            WeatherCondition.CLOUDY: self.cloudy,
            WeatherCondition.RAINY: self.rainy,
            WeatherCondition.STORM: self.storm,
        }
        return mapping.get(condition, self.cloudy)
