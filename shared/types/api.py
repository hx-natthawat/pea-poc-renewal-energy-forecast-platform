"""
Shared API types for PEA RE Forecast Platform.

These types are shared between backend, frontend (via codegen), and ML services.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# =============================================================================
# Solar Forecast Types
# =============================================================================


class SolarFeatures(BaseModel):
    """Input features for solar power prediction."""

    pyrano1: float = Field(..., ge=0, le=1500, description="Irradiance sensor 1 (W/m²)")
    pyrano2: float = Field(..., ge=0, le=1500, description="Irradiance sensor 2 (W/m²)")
    pvtemp1: float = Field(..., ge=-10, le=100, description="PV temp sensor 1 (°C)")
    pvtemp2: float = Field(..., ge=-10, le=100, description="PV temp sensor 2 (°C)")
    ambtemp: float = Field(..., ge=-10, le=60, description="Ambient temperature (°C)")
    windspeed: float = Field(..., ge=0, le=50, description="Wind speed (m/s)")


class SolarPrediction(BaseModel):
    """Solar power prediction result."""

    power_kw: float
    confidence_lower: float
    confidence_upper: float


class SolarForecastRequest(BaseModel):
    """Request for solar power forecast."""

    timestamp: datetime
    station_id: str = "POC_STATION_1"
    horizon_minutes: int = Field(default=60, ge=5, le=1440)
    features: SolarFeatures


class SolarForecastResponse(BaseModel):
    """Response for solar power forecast."""

    status: str
    data: Dict[str, Any]
    meta: Dict[str, Any]


# =============================================================================
# Voltage Prediction Types
# =============================================================================


class VoltagePrediction(BaseModel):
    """Voltage prediction for a single prosumer."""

    prosumer_id: str
    phase: str
    predicted_voltage: float
    confidence_lower: float
    confidence_upper: float
    status: str  # normal, warning, critical
    violation_probability: float


class VoltageForecastRequest(BaseModel):
    """Request for voltage prediction."""

    timestamp: datetime
    prosumer_ids: List[str]
    horizon_minutes: int = Field(default=15, ge=5, le=60)


class VoltageForecastResponse(BaseModel):
    """Response for voltage prediction."""

    status: str
    data: Dict[str, Any]


# =============================================================================
# Common Types
# =============================================================================


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    timestamp: str
    service: str


class ProsumerInfo(BaseModel):
    """Prosumer information."""

    id: str
    name: str
    phase: str
    position_in_phase: int
    has_pv: bool
    has_ev: bool
    has_battery: bool
    pv_capacity_kw: Optional[float]
