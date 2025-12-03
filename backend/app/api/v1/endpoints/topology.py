"""
Network topology endpoints for the low-voltage distribution network.

Provides prosumer topology data with real-time voltage overlays.
Authentication is controlled by AUTH_ENABLED setting.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, get_current_user
from app.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Response Models
# =============================================================================


class ProsumerNode(BaseModel):
    """Prosumer node in the network topology."""

    id: str
    name: str
    phase: str
    position: int
    has_pv: bool
    has_ev: bool
    has_battery: bool = False
    pv_capacity_kw: Optional[float] = None
    current_voltage: Optional[float] = None
    voltage_status: str = "unknown"  # normal, warning, critical, unknown
    active_power: Optional[float] = None
    reactive_power: Optional[float] = None


class PhaseGroup(BaseModel):
    """Group of prosumers on a single phase."""

    phase: str
    prosumers: List[ProsumerNode]
    avg_voltage: Optional[float] = None
    total_power: Optional[float] = None


class TransformerNode(BaseModel):
    """Transformer node at the head of the network."""

    id: str = "TX_50KVA_01"
    name: str = "Distribution Transformer"
    capacity_kva: float = 50.0
    voltage_primary: float = 22000.0
    voltage_secondary: float = 400.0
    phases: List[str] = ["A", "B", "C"]


class TopologyResponse(BaseModel):
    """Network topology response."""

    status: str
    data: Dict[str, Any]


# =============================================================================
# Constants
# =============================================================================


VOLTAGE_NOMINAL = 230.0
VOLTAGE_UPPER_LIMIT = 242.0  # +5%
VOLTAGE_LOWER_LIMIT = 218.0  # -5%
VOLTAGE_WARNING_UPPER = 238.0
VOLTAGE_WARNING_LOWER = 222.0


def get_voltage_status(voltage: Optional[float]) -> str:
    """Determine voltage status based on limits."""
    if voltage is None:
        return "unknown"
    if voltage < VOLTAGE_LOWER_LIMIT or voltage > VOLTAGE_UPPER_LIMIT:
        return "critical"
    if voltage < VOLTAGE_WARNING_LOWER or voltage > VOLTAGE_WARNING_UPPER:
        return "warning"
    return "normal"


# =============================================================================
# Endpoints
# =============================================================================


@router.get("/")
async def get_network_topology(
    include_voltage: bool = Query(default=True, description="Include real-time voltage data"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> TopologyResponse:
    """
    Get the complete network topology with prosumer information.

    **Requires authentication**

    Returns:
    - Transformer information
    - Prosumer nodes organized by phase
    - Optional real-time voltage overlay
    """
    logger.info(f"Network topology requested by user: {current_user.username}")

    # Get prosumer configuration
    prosumer_query = text("""
        SELECT id, name, phase, position_in_phase, has_pv, has_ev, has_battery, pv_capacity_kw
        FROM prosumers
        ORDER BY phase, position_in_phase
    """)

    result = await db.execute(prosumer_query)
    prosumer_rows = result.fetchall()

    # Get latest voltage data if requested
    voltage_data = {}
    if include_voltage:
        voltage_query = text("""
            SELECT DISTINCT ON (prosumer_id)
                prosumer_id,
                energy_meter_voltage as voltage,
                active_power,
                reactive_power,
                time
            FROM single_phase_meters
            ORDER BY prosumer_id, time DESC
        """)

        voltage_result = await db.execute(voltage_query)
        for row in voltage_result.fetchall():
            voltage_data[row.prosumer_id] = {
                "voltage": row.voltage,
                "active_power": row.active_power,
                "reactive_power": row.reactive_power,
                "time": row.time,
            }

    # Build prosumer nodes
    prosumers_by_phase: Dict[str, List[ProsumerNode]] = {"A": [], "B": [], "C": []}

    for row in prosumer_rows:
        voltage_info = voltage_data.get(row.id, {})
        current_voltage = voltage_info.get("voltage")

        node = ProsumerNode(
            id=row.id,
            name=row.name,
            phase=row.phase,
            position=row.position_in_phase,
            has_pv=row.has_pv,
            has_ev=row.has_ev,
            has_battery=row.has_battery or False,
            pv_capacity_kw=row.pv_capacity_kw,
            current_voltage=round(current_voltage, 1) if current_voltage else None,
            voltage_status=get_voltage_status(current_voltage),
            active_power=round(voltage_info.get("active_power", 0) or 0, 2),
            reactive_power=round(voltage_info.get("reactive_power", 0) or 0, 2),
        )

        if row.phase in prosumers_by_phase:
            prosumers_by_phase[row.phase].append(node)

    # Build phase groups
    phases = []
    for phase_id in ["A", "B", "C"]:
        prosumers = prosumers_by_phase[phase_id]
        voltages = [p.current_voltage for p in prosumers if p.current_voltage is not None]
        powers = [p.active_power for p in prosumers if p.active_power is not None]

        phase_group = PhaseGroup(
            phase=phase_id,
            prosumers=[p.model_dump() for p in prosumers],
            avg_voltage=round(sum(voltages) / len(voltages), 1) if voltages else None,
            total_power=round(sum(powers), 2) if powers else None,
        )
        phases.append(phase_group.model_dump())

    # Build transformer info
    transformer = TransformerNode()

    # Count statistics
    total_prosumers = len(prosumer_rows)
    prosumers_with_pv = sum(1 for r in prosumer_rows if r.has_pv)
    prosumers_with_ev = sum(1 for r in prosumer_rows if r.has_ev)

    # Voltage statistics
    all_voltages = [v["voltage"] for v in voltage_data.values() if v.get("voltage")]
    critical_count = sum(1 for v in all_voltages if get_voltage_status(v) == "critical")
    warning_count = sum(1 for v in all_voltages if get_voltage_status(v) == "warning")

    return TopologyResponse(
        status="success",
        data={
            "transformer": transformer.model_dump(),
            "phases": phases,
            "summary": {
                "total_prosumers": total_prosumers,
                "prosumers_with_pv": prosumers_with_pv,
                "prosumers_with_ev": prosumers_with_ev,
                "voltage_stats": {
                    "avg_voltage": round(sum(all_voltages) / len(all_voltages), 1) if all_voltages else None,
                    "min_voltage": round(min(all_voltages), 1) if all_voltages else None,
                    "max_voltage": round(max(all_voltages), 1) if all_voltages else None,
                    "critical_count": critical_count,
                    "warning_count": warning_count,
                },
            },
            "limits": {
                "nominal": VOLTAGE_NOMINAL,
                "upper_limit": VOLTAGE_UPPER_LIMIT,
                "lower_limit": VOLTAGE_LOWER_LIMIT,
                "warning_upper": VOLTAGE_WARNING_UPPER,
                "warning_lower": VOLTAGE_WARNING_LOWER,
            },
        },
    )


@router.get("/prosumer/{prosumer_id}")
async def get_prosumer_details(
    prosumer_id: str,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of history"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> TopologyResponse:
    """
    Get detailed information for a specific prosumer.

    **Requires authentication**

    Returns prosumer configuration and recent voltage/power history.
    """
    logger.info(f"Prosumer {prosumer_id} details requested by user: {current_user.username}")

    # Get prosumer config
    config_query = text("""
        SELECT id, name, phase, position_in_phase, has_pv, has_ev, has_battery, pv_capacity_kw
        FROM prosumers
        WHERE id = :prosumer_id
    """)

    result = await db.execute(config_query, {"prosumer_id": prosumer_id})
    row = result.fetchone()

    if not row:
        return TopologyResponse(
            status="error",
            data={"message": f"Prosumer {prosumer_id} not found"},
        )

    # Get recent measurements
    measurements_query = text("""
        SELECT
            time,
            energy_meter_voltage as voltage,
            active_power,
            reactive_power,
            energy_meter_current as current
        FROM single_phase_meters
        WHERE prosumer_id = :prosumer_id
        ORDER BY time DESC
        LIMIT 288
    """)

    measurements_result = await db.execute(measurements_query, {"prosumer_id": prosumer_id})
    measurements = []

    for m in reversed(measurements_result.fetchall()):
        measurements.append({
            "time": m.time.strftime("%H:%M") if m.time else None,
            "voltage": round(m.voltage, 1) if m.voltage else None,
            "active_power": round(m.active_power, 2) if m.active_power else None,
            "reactive_power": round(m.reactive_power, 2) if m.reactive_power else None,
            "current": round(m.current, 2) if m.current else None,
        })

    # Get current status
    current_voltage = measurements[-1]["voltage"] if measurements else None

    return TopologyResponse(
        status="success",
        data={
            "prosumer": {
                "id": row.id,
                "name": row.name,
                "phase": row.phase,
                "position": row.position_in_phase,
                "has_pv": row.has_pv,
                "has_ev": row.has_ev,
                "has_battery": row.has_battery or False,
                "pv_capacity_kw": row.pv_capacity_kw,
                "current_voltage": current_voltage,
                "voltage_status": get_voltage_status(current_voltage),
            },
            "measurements": measurements,
            "count": len(measurements),
        },
    )


@router.get("/phases/{phase}")
async def get_phase_details(
    phase: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> TopologyResponse:
    """
    Get detailed information for a specific phase.

    **Requires authentication**

    Returns all prosumers on the phase with current voltage data.
    """
    if phase.upper() not in ["A", "B", "C"]:
        return TopologyResponse(
            status="error",
            data={"message": f"Invalid phase: {phase}. Must be A, B, or C"},
        )

    phase = phase.upper()
    logger.info(f"Phase {phase} details requested by user: {current_user.username}")

    # Get prosumers on this phase
    query = text("""
        SELECT
            p.id,
            p.name,
            p.phase,
            p.position_in_phase,
            p.has_pv,
            p.has_ev,
            m.energy_meter_voltage as voltage,
            m.active_power,
            m.time
        FROM prosumers p
        LEFT JOIN LATERAL (
            SELECT energy_meter_voltage, active_power, time
            FROM single_phase_meters
            WHERE prosumer_id = p.id
            ORDER BY time DESC
            LIMIT 1
        ) m ON true
        WHERE p.phase = :phase
        ORDER BY p.position_in_phase
    """)

    result = await db.execute(query, {"phase": phase})
    rows = result.fetchall()

    prosumers = []
    voltages = []
    powers = []

    for row in rows:
        voltage = row.voltage
        if voltage:
            voltages.append(voltage)
        if row.active_power:
            powers.append(row.active_power)

        prosumers.append({
            "id": row.id,
            "name": row.name,
            "position": row.position_in_phase,
            "has_pv": row.has_pv,
            "has_ev": row.has_ev,
            "current_voltage": round(voltage, 1) if voltage else None,
            "voltage_status": get_voltage_status(voltage),
            "active_power": round(row.active_power, 2) if row.active_power else None,
            "last_update": row.time.isoformat() if row.time else None,
        })

    return TopologyResponse(
        status="success",
        data={
            "phase": phase,
            "prosumers": prosumers,
            "count": len(prosumers),
            "summary": {
                "avg_voltage": round(sum(voltages) / len(voltages), 1) if voltages else None,
                "min_voltage": round(min(voltages), 1) if voltages else None,
                "max_voltage": round(max(voltages), 1) if voltages else None,
                "total_power": round(sum(powers), 2) if powers else None,
            },
        },
    )
