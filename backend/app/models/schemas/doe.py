"""
DOE (Dynamic Operating Envelope) Pydantic Schemas.

Based on TOR 7.5.1.6 requirements and global DOE standards (IEEE 1547-2018, ARENA/AEMO).
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class LimitingFactor(str, Enum):
    """Constraint that limits the DOE value."""

    VOLTAGE = "voltage"
    THERMAL = "thermal"
    PROTECTION = "protection"
    TRANSFORMER = "transformer"
    NONE = "none"


class DOEStatus(str, Enum):
    """Status of DOE calculation."""

    NORMAL = "normal"
    CONSTRAINED = "constrained"
    CRITICAL = "critical"


# ============================================================
# Request Schemas
# ============================================================


class DOECalculateRequest(BaseModel):
    """Request to calculate DOE for a single prosumer."""

    prosumer_id: str = Field(..., description="Prosumer ID")
    timestamp: datetime | None = Field(
        None, description="Timestamp for calculation (default: now)"
    )
    horizon_minutes: int = Field(
        15, description="Forecast horizon in minutes", ge=5, le=1440
    )
    include_forecast: bool = Field(True, description="Include voltage/load forecasts")


class DOEBatchCalculateRequest(BaseModel):
    """Request to calculate DOE for all prosumers."""

    timestamp: datetime | None = Field(
        None, description="Timestamp for calculation (default: now)"
    )
    horizon_minutes: int = Field(
        15, description="Forecast horizon in minutes", ge=5, le=1440
    )
    prosumer_ids: list[str] | None = Field(
        None, description="Specific prosumers (default: all)"
    )


# ============================================================
# Response Schemas
# ============================================================


class DOELimit(BaseModel):
    """DOE limit for a single prosumer at a single time point."""

    prosumer_id: str = Field(..., description="Prosumer ID")
    timestamp: datetime = Field(..., description="Calculation timestamp")
    valid_until: datetime = Field(..., description="Validity end time")

    # Operating limits (kW)
    export_limit_kw: float = Field(..., description="Maximum export power (kW)", ge=0)
    import_limit_kw: float = Field(..., description="Maximum import power (kW)", ge=0)

    # Constraint information
    limiting_factor: LimitingFactor = Field(..., description="Binding constraint")
    status: DOEStatus = Field(DOEStatus.NORMAL, description="DOE status")

    # Predictions used
    predicted_voltage_v: float | None = Field(None, description="Predicted voltage (V)")
    voltage_headroom_v: float | None = Field(
        None, description="Voltage margin to limit (V)"
    )
    thermal_headroom_pct: float | None = Field(None, description="Thermal margin (%)")

    # Confidence
    confidence: float = Field(0.95, description="Confidence level", ge=0, le=1)

    # Metadata
    calculation_time_ms: int | None = Field(None, description="Calculation time (ms)")
    model_version: str = Field("doe-v1.0.0", description="DOE model version")


class DOECalculateResponse(BaseModel):
    """Response for single prosumer DOE calculation."""

    status: str = Field("success", description="Response status")
    data: DOELimit = Field(..., description="Calculated DOE limit")


class DOEBatchCalculateResponse(BaseModel):
    """Response for batch DOE calculation."""

    status: str = Field("success", description="Response status")
    timestamp: datetime = Field(..., description="Calculation timestamp")
    prosumer_count: int = Field(..., description="Number of prosumers calculated")
    data: list[DOELimit] = Field(..., description="DOE limits for all prosumers")
    summary: dict = Field(..., description="Summary statistics")


class DOEHistoryResponse(BaseModel):
    """Response for DOE history query."""

    prosumer_id: str
    start_time: datetime
    end_time: datetime
    count: int
    data: list[DOELimit]


# ============================================================
# Network Model Schemas
# ============================================================


class NetworkNode(BaseModel):
    """Network node/bus information."""

    id: str
    name: str
    node_type: str
    phase: str | None
    nominal_voltage_v: float
    prosumer_id: str | None
    distance_from_tx_m: float


class NetworkBranch(BaseModel):
    """Network branch/line information."""

    id: str
    name: str
    branch_type: str
    from_node_id: str
    to_node_id: str
    length_m: float
    r_ohm_per_km: float
    x_ohm_per_km: float
    max_current_a: float


class NetworkTransformer(BaseModel):
    """Transformer information."""

    id: str
    name: str
    rated_power_kva: float
    primary_voltage_kv: float
    secondary_voltage_v: float
    impedance_pu: float
    max_current_a: float


class NetworkTopologyResponse(BaseModel):
    """Complete network topology."""

    status: str = "success"
    transformer: NetworkTransformer
    nodes: list[NetworkNode]
    branches: list[NetworkBranch]
    constraints: dict


# ============================================================
# Constraint Schemas
# ============================================================


class VoltageConstraints(BaseModel):
    """Voltage constraint configuration."""

    nominal_v: float = Field(230.0, description="Nominal voltage (V)")
    upper_limit_v: float = Field(242.0, description="Upper limit (+5%)")
    lower_limit_v: float = Field(218.0, description="Lower limit (-5%)")
    safety_margin_v: float = Field(2.0, description="Safety margin (V)")


class ThermalConstraints(BaseModel):
    """Thermal constraint configuration."""

    cable_max_current_a: float = Field(200.0, description="Cable ampacity (A)")
    transformer_max_current_a: float = Field(
        72.2, description="Transformer max current (A)"
    )
    safety_margin_pct: float = Field(15.0, description="Safety margin (%)")


class DOEConstraints(BaseModel):
    """Complete DOE constraint configuration."""

    voltage: VoltageConstraints = Field(default_factory=VoltageConstraints)
    thermal: ThermalConstraints = Field(default_factory=ThermalConstraints)
    update_interval_minutes: int = Field(15, description="DOE update interval")
