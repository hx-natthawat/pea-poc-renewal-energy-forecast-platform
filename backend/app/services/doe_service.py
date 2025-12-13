"""
DOE (Dynamic Operating Envelope) Calculation Service.

Implements DOE calculation based on:
- TOR 7.5.1.6 requirements
- IEEE 1547-2018 standards
- ARENA/AEMO DOE best practices

Phase 1: Simplified voltage sensitivity method
Phase 2: Full power flow with Pandapower (future)
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.models.schemas.doe import (
    DOEBatchCalculateResponse,
    DOECalculateResponse,
    DOELimit,
    DOEStatus,
    LimitingFactor,
    VoltageConstraints,
)

logger = logging.getLogger(__name__)


# ============================================================
# Network Configuration (Mock GIS Data)
# ============================================================


@dataclass
class ProsumerConfig:
    """Prosumer configuration from network model."""

    id: str
    name: str
    phase: str
    position: int  # 1=near, 2=mid, 3=far from transformer
    has_pv: bool
    has_ev: bool
    pv_capacity_kw: float = 10.0


@dataclass
class NetworkConfig:
    """Network configuration for DOE calculations."""

    # Transformer
    tx_capacity_kva: float = 50.0
    tx_voltage_v: float = 400.0  # Secondary voltage (3-phase)
    tx_impedance_pu: float = 0.04

    # Cable parameters (95mm² Al)
    cable_r_ohm_per_km: float = 0.32
    cable_x_ohm_per_km: float = 0.08
    cable_max_current_a: float = 200.0
    segment_length_m: float = 50.0  # Per segment

    # Voltage constraints (Thailand PEA: ±5%)
    voltage_nominal_v: float = 230.0
    voltage_upper_v: float = 242.0  # +5%
    voltage_lower_v: float = 218.0  # -5%

    # Safety margins
    voltage_margin_v: float = 2.0  # 2V safety margin
    thermal_margin_pct: float = 15.0  # 15% thermal margin


# POC Network Prosumers (from TOR Appendix 6)
POC_PROSUMERS = [
    ProsumerConfig("prosumer1", "Prosumer 1", "A", 3, True, True, 10.0),
    ProsumerConfig("prosumer2", "Prosumer 2", "A", 2, True, False, 10.0),
    ProsumerConfig("prosumer3", "Prosumer 3", "A", 1, True, False, 10.0),
    ProsumerConfig("prosumer4", "Prosumer 4", "B", 2, True, False, 10.0),
    ProsumerConfig("prosumer5", "Prosumer 5", "B", 3, True, True, 10.0),
    ProsumerConfig("prosumer6", "Prosumer 6", "B", 1, True, False, 10.0),
    ProsumerConfig("prosumer7", "Prosumer 7", "C", 1, True, True, 10.0),
]


def get_prosumer_config(prosumer_id: str) -> ProsumerConfig | None:
    """Get prosumer configuration by ID."""
    for p in POC_PROSUMERS:
        if p.id == prosumer_id:
            return p
    return None


# ============================================================
# DOE Calculation Engine
# ============================================================


class DOECalculator:
    """
    DOE Calculator using simplified voltage sensitivity method.

    This is Phase 1 implementation. Phase 2 will use Pandapower
    for full AC power flow calculations.

    Method:
    1. Calculate voltage sensitivity (dV/dP) based on line impedance
    2. Determine voltage headroom from current voltage to limit
    3. Calculate max export/import before hitting voltage constraint
    4. Apply safety margin for forecast uncertainty
    """

    def __init__(self, config: NetworkConfig | None = None):
        """Initialize calculator with network configuration."""
        self.config = config or NetworkConfig()
        self.constraints = VoltageConstraints(
            nominal_v=self.config.voltage_nominal_v,
            upper_limit_v=self.config.voltage_upper_v,
            lower_limit_v=self.config.voltage_lower_v,
            safety_margin_v=self.config.voltage_margin_v,
        )

    def calculate_voltage_sensitivity(self, prosumer: ProsumerConfig) -> float:
        """
        Calculate voltage sensitivity dV/dP (V per kW).

        Based on simplified voltage drop formula:
        ΔV = (P·R + Q·X) / V

        For resistive networks (R >> X at LV):
        dV/dP ≈ R / V

        The sensitivity increases with distance from transformer.
        """
        # Distance-based impedance (cumulative from transformer)
        distance_km = (prosumer.position * self.config.segment_length_m) / 1000

        # Total resistance from transformer to prosumer
        r_total = distance_km * self.config.cable_r_ohm_per_km

        # Voltage sensitivity: V change per kW injected
        # dV/dP = R / V (simplified, ignoring Q)
        sensitivity = r_total / self.config.voltage_nominal_v * 1000  # V/kW

        return sensitivity

    def calculate_thermal_headroom(
        self, prosumer: ProsumerConfig
    ) -> tuple[float, float]:
        """
        Calculate thermal headroom for prosumer connection.

        Returns:
            (headroom_kw, headroom_pct): Available thermal capacity
        """
        # Assume current loading is 50% of capacity (baseline)
        baseline_loading_pct = 50.0

        # Available headroom
        available_pct = 100.0 - baseline_loading_pct - self.config.thermal_margin_pct

        # Convert to kW (single-phase: S = V * I)
        max_power_kva = (
            self.config.voltage_nominal_v * self.config.cable_max_current_a / 1000
        )
        headroom_kw = max_power_kva * (available_pct / 100.0)

        return headroom_kw, available_pct

    def get_predicted_voltage(
        self, prosumer: ProsumerConfig, timestamp: datetime
    ) -> float:
        """
        Get predicted voltage for prosumer at timestamp.

        In production, this would call the voltage prediction service.
        For now, simulate based on time of day and position.
        """
        hour = timestamp.hour

        # Base voltage (slightly above nominal during day due to solar)
        base_voltage = self.config.voltage_nominal_v

        # Solar effect: voltage rises during peak hours (10-14)
        if 10 <= hour <= 14:
            solar_effect = 5.0  # +5V during peak solar
        elif 6 <= hour <= 18:
            solar_effect = 2.0  # +2V during daylight
        else:
            solar_effect = -1.0  # -1V at night (higher load, lower voltage)

        # Position effect: end-of-feeder has higher voltage rise
        position_factor = prosumer.position / 3.0  # 0.33, 0.67, 1.0

        predicted_voltage = base_voltage + (solar_effect * position_factor)

        # Add small random variation (simulate real measurements)
        import random

        predicted_voltage += random.uniform(-0.5, 0.5)

        return round(predicted_voltage, 2)

    def calculate_doe(
        self,
        prosumer_id: str,
        timestamp: datetime | None = None,
        horizon_minutes: int = 15,
    ) -> DOELimit:
        """
        Calculate DOE for a single prosumer.

        Args:
            prosumer_id: Prosumer identifier
            timestamp: Calculation timestamp (default: now)
            horizon_minutes: Forecast horizon in minutes

        Returns:
            DOELimit with export/import limits
        """
        start_time = time.time()

        if timestamp is None:
            timestamp = datetime.now()

        # Get prosumer configuration
        prosumer = get_prosumer_config(prosumer_id)
        if prosumer is None:
            raise ValueError(f"Unknown prosumer: {prosumer_id}")

        # Calculate voltage sensitivity
        dv_dp = self.calculate_voltage_sensitivity(prosumer)

        # Get predicted voltage
        predicted_voltage = self.get_predicted_voltage(prosumer, timestamp)

        # Calculate voltage headroom (to upper limit)
        effective_upper = (
            self.constraints.upper_limit_v - self.constraints.safety_margin_v
        )
        voltage_headroom = effective_upper - predicted_voltage

        # Calculate max export before voltage violation
        # P_export_max = voltage_headroom / dV_dP
        if dv_dp > 0:
            export_limit_voltage = max(0, voltage_headroom / dv_dp)
        else:
            export_limit_voltage = prosumer.pv_capacity_kw

        # Calculate thermal headroom
        thermal_headroom_kw, thermal_headroom_pct = self.calculate_thermal_headroom(
            prosumer
        )

        # Export limit is minimum of voltage and thermal constraints
        export_limit_kw = min(export_limit_voltage, thermal_headroom_kw)

        # Apply safety margin (15%)
        export_limit_kw = export_limit_kw * (1 - self.config.thermal_margin_pct / 100)

        # Cap at PV capacity
        export_limit_kw = min(export_limit_kw, prosumer.pv_capacity_kw)
        export_limit_kw = max(0, export_limit_kw)

        # Import limit (less constrained, voltage drop helps)
        # During import, voltage drops which is generally acceptable
        import_limit_kw = thermal_headroom_kw * 1.5  # Higher import than export

        # Determine limiting factor
        if export_limit_voltage < thermal_headroom_kw:
            limiting_factor = LimitingFactor.VOLTAGE
        elif thermal_headroom_kw < export_limit_voltage:
            limiting_factor = LimitingFactor.THERMAL
        else:
            limiting_factor = LimitingFactor.NONE

        # Determine status
        if voltage_headroom < 2.0:
            status = DOEStatus.CRITICAL
        elif voltage_headroom < 5.0:
            status = DOEStatus.CONSTRAINED
        else:
            status = DOEStatus.NORMAL

        # Calculate elapsed time
        calc_time_ms = int((time.time() - start_time) * 1000)

        return DOELimit(
            prosumer_id=prosumer_id,
            timestamp=timestamp,
            valid_until=timestamp + timedelta(minutes=horizon_minutes),
            export_limit_kw=round(export_limit_kw, 2),
            import_limit_kw=round(import_limit_kw, 2),
            limiting_factor=limiting_factor,
            status=status,
            predicted_voltage_v=predicted_voltage,
            voltage_headroom_v=round(voltage_headroom, 2),
            thermal_headroom_pct=round(thermal_headroom_pct, 1),
            confidence=0.95,
            calculation_time_ms=calc_time_ms,
            model_version="doe-v1.0.0-sensitivity",
        )

    def calculate_batch(
        self,
        prosumer_ids: list[str] | None = None,
        timestamp: datetime | None = None,
        horizon_minutes: int = 15,
    ) -> list[DOELimit]:
        """
        Calculate DOE for multiple prosumers.

        Args:
            prosumer_ids: List of prosumer IDs (default: all)
            timestamp: Calculation timestamp
            horizon_minutes: Forecast horizon

        Returns:
            List of DOELimit for each prosumer
        """
        if prosumer_ids is None:
            prosumer_ids = [p.id for p in POC_PROSUMERS]

        results = []
        for pid in prosumer_ids:
            try:
                doe = self.calculate_doe(pid, timestamp, horizon_minutes)
                results.append(doe)
            except ValueError as e:
                logger.warning(f"Failed to calculate DOE for {pid}: {e}")

        return results


# ============================================================
# Service Functions (for API)
# ============================================================

# Global calculator instance
_calculator: DOECalculator | None = None


def get_calculator() -> DOECalculator:
    """Get or create DOE calculator instance."""
    global _calculator
    if _calculator is None:
        _calculator = DOECalculator()
    return _calculator


async def calculate_doe_for_prosumer(
    prosumer_id: str,
    timestamp: datetime | None = None,
    horizon_minutes: int = 15,
) -> DOECalculateResponse:
    """
    Calculate DOE for a single prosumer.

    Args:
        prosumer_id: Prosumer identifier
        timestamp: Calculation timestamp
        horizon_minutes: Forecast horizon

    Returns:
        DOECalculateResponse with calculated limit
    """
    calculator = get_calculator()
    doe_limit = calculator.calculate_doe(prosumer_id, timestamp, horizon_minutes)

    logger.info(
        f"DOE calculated for {prosumer_id}: "
        f"export={doe_limit.export_limit_kw}kW, "
        f"limiting={doe_limit.limiting_factor.value}"
    )

    return DOECalculateResponse(status="success", data=doe_limit)


async def calculate_doe_batch(
    prosumer_ids: list[str] | None = None,
    timestamp: datetime | None = None,
    horizon_minutes: int = 15,
) -> DOEBatchCalculateResponse:
    """
    Calculate DOE for all prosumers.

    Args:
        prosumer_ids: Specific prosumers (default: all)
        timestamp: Calculation timestamp
        horizon_minutes: Forecast horizon

    Returns:
        DOEBatchCalculateResponse with all limits
    """
    calculator = get_calculator()

    if timestamp is None:
        timestamp = datetime.now()

    doe_limits = calculator.calculate_batch(prosumer_ids, timestamp, horizon_minutes)

    # Calculate summary statistics
    export_limits = [d.export_limit_kw for d in doe_limits]
    summary = {
        "total_export_capacity_kw": round(sum(export_limits), 2),
        "avg_export_limit_kw": round(sum(export_limits) / len(export_limits), 2)
        if export_limits
        else 0,
        "min_export_limit_kw": round(min(export_limits), 2) if export_limits else 0,
        "max_export_limit_kw": round(max(export_limits), 2) if export_limits else 0,
        "constrained_count": sum(1 for d in doe_limits if d.status != DOEStatus.NORMAL),
        "voltage_limited_count": sum(
            1 for d in doe_limits if d.limiting_factor == LimitingFactor.VOLTAGE
        ),
        "thermal_limited_count": sum(
            1 for d in doe_limits if d.limiting_factor == LimitingFactor.THERMAL
        ),
    }

    logger.info(
        f"DOE batch calculated: {len(doe_limits)} prosumers, "
        f"total export={summary['total_export_capacity_kw']}kW"
    )

    return DOEBatchCalculateResponse(
        status="success",
        timestamp=timestamp,
        prosumer_count=len(doe_limits),
        data=doe_limits,
        summary=summary,
    )


async def get_network_topology() -> dict:
    """
    Get network topology for visualization.

    Returns mock GIS data for POC network.
    """
    return {
        "transformer": {
            "id": "TX_50KVA_01",
            "name": "POC Distribution Transformer",
            "rated_power_kva": 50,
            "primary_voltage_kv": 22,
            "secondary_voltage_v": 400,
        },
        "prosumers": [
            {
                "id": p.id,
                "name": p.name,
                "phase": p.phase,
                "position": p.position,
                "has_pv": p.has_pv,
                "has_ev": p.has_ev,
                "pv_capacity_kw": p.pv_capacity_kw,
            }
            for p in POC_PROSUMERS
        ],
        "constraints": {
            "voltage_nominal_v": 230,
            "voltage_upper_v": 242,
            "voltage_lower_v": 218,
            "thermal_limit_a": 200,
        },
    }
