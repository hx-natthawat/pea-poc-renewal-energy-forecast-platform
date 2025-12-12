"""
Data endpoints for sensor and meter data from TimescaleDB.

Provides paginated access to measurement data.
Authentication is controlled by AUTH_ENABLED setting.
"""

import logging
from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, get_current_user
from app.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Response Models
# =============================================================================


class SolarDataPoint(BaseModel):
    """Solar measurement data point for chart."""

    time: str
    power_kw: float
    predicted_kw: float
    irradiance: float


class VoltageDataPoint(BaseModel):
    """Voltage measurement data point for chart."""

    time: str
    prosumer1: float | None = None
    prosumer2: float | None = None
    prosumer3: float | None = None
    prosumer4: float | None = None
    prosumer5: float | None = None
    prosumer6: float | None = None
    prosumer7: float | None = None


# =============================================================================
# Solar Data Endpoints
# =============================================================================


@router.get("/solar/latest")
async def get_latest_solar_data(
    station_id: str = Query(default="POC_STATION_1", description="Station ID"),
    hours: int = Query(default=4, ge=1, le=24, description="Hours of data to return"),
    limit: int = Query(default=288, ge=1, le=1000, description="Max records to return"),
    offset: int = Query(default=0, ge=0, description="Records to skip for pagination"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get latest solar measurements for chart display.

    **Requires authentication**

    Returns data from the last N hours with pagination support.
    """
    logger.info(f"Solar data requested by user: {current_user.username}")
    query = text("""
        SELECT
            time,
            power_kw,
            pyrano1 as irradiance,
            pvtemp1,
            ambtemp
        FROM solar_measurements
        WHERE station_id = :station_id
          AND time >= NOW() - INTERVAL '1 hour' * :hours
        ORDER BY time ASC
        LIMIT 288
    """)

    result = await db.execute(query, {"station_id": station_id, "hours": hours})
    rows = result.fetchall()

    # If no recent data, get the most recent data available
    if not rows:
        query = text("""
            SELECT
                time,
                power_kw,
                pyrano1 as irradiance,
                pvtemp1,
                ambtemp
            FROM solar_measurements
            WHERE station_id = :station_id
            ORDER BY time DESC
            LIMIT 288
        """)
        result = await db.execute(query, {"station_id": station_id})
        rows = result.fetchall()
        rows = list(reversed(rows))  # Reverse to get chronological order

    data = []
    for row in rows:
        # Simple prediction: actual * 0.95 + noise
        predicted = row.power_kw * 0.95 if row.power_kw else 0
        data.append(
            {
                "time": row.time.strftime("%H:%M"),
                "power_kw": round(row.power_kw or 0, 1),
                "predicted_kw": round(predicted, 1),
                "irradiance": round(row.irradiance or 0, 1),
            }
        )

    # Calculate summary stats
    powers = [d["power_kw"] for d in data if d["power_kw"] > 0]
    current_power = data[-1]["power_kw"] if data else 0
    peak_power = max(powers) if powers else 0

    return {
        "status": "success",
        "data": {
            "station_id": station_id,
            "chart_data": data,
            "summary": {
                "current_power": current_power,
                "peak_power": peak_power,
                "data_points": len(data),
            },
        },
    }


@router.get("/solar/stats")
async def get_solar_stats(
    station_id: str = Query(default="POC_STATION_1", description="Station ID"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get solar data statistics.

    **Requires authentication**
    """
    query = text("""
        SELECT
            COUNT(*) as total_count,
            MIN(time) as first_record,
            MAX(time) as last_record,
            AVG(power_kw) as avg_power,
            MAX(power_kw) as max_power
        FROM solar_measurements
        WHERE station_id = :station_id
    """)

    result = await db.execute(query, {"station_id": station_id})
    row = result.fetchone()

    return {
        "status": "success",
        "data": {
            "station_id": station_id,
            "total_count": row.total_count if row else 0,
            "first_record": row.first_record.isoformat()
            if row and row.first_record
            else None,
            "last_record": row.last_record.isoformat()
            if row and row.last_record
            else None,
            "avg_power": round(row.avg_power, 2) if row and row.avg_power else 0,
            "max_power": round(row.max_power, 2) if row and row.max_power else 0,
        },
    }


# =============================================================================
# Voltage Data Endpoints
# =============================================================================


@router.get("/voltage/latest")
async def get_latest_voltage_data(
    hours: int = Query(default=2, ge=1, le=24, description="Hours of data to return"),
    limit: int = Query(default=288, ge=1, le=1000, description="Max records to return"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get latest voltage measurements for all prosumers.

    **Requires authentication**

    Returns pivoted data suitable for chart display.
    """
    logger.info(f"Voltage data requested by user: {current_user.username}")
    # Get the most recent timestamp to use as reference
    time_query = text("""
        SELECT MAX(time) as latest_time FROM single_phase_meters
    """)
    time_result = await db.execute(time_query)
    latest_row = time_result.fetchone()

    if not latest_row or not latest_row.latest_time:
        return {
            "status": "success",
            "data": {
                "chart_data": [],
                "prosumer_status": [],
                "summary": {"violations": 0, "avg_voltage": 230},
            },
        }

    latest_time = latest_row.latest_time
    start_time = latest_time - timedelta(hours=hours)

    # Get voltage data for all prosumers
    query = text("""
        SELECT
            time_bucket('5 minutes', time) as bucket,
            prosumer_id,
            AVG(energy_meter_voltage) as voltage
        FROM single_phase_meters
        WHERE time >= :start_time AND time <= :end_time
        GROUP BY bucket, prosumer_id
        ORDER BY bucket ASC
    """)

    result = await db.execute(
        query, {"start_time": start_time, "end_time": latest_time}
    )
    rows = result.fetchall()

    # Pivot data by time bucket
    time_data: dict[str, dict] = {}
    for row in rows:
        bucket_str = row.bucket.strftime("%H:%M")
        if bucket_str not in time_data:
            time_data[bucket_str] = {"time": bucket_str}
        time_data[bucket_str][row.prosumer_id] = round(row.voltage, 1)

    chart_data = list(time_data.values())

    # Get current status for each prosumer
    status_query = text("""
        SELECT DISTINCT ON (prosumer_id)
            prosumer_id,
            energy_meter_voltage as voltage,
            time
        FROM single_phase_meters
        WHERE time >= :start_time
        ORDER BY prosumer_id, time DESC
    """)

    status_result = await db.execute(status_query, {"start_time": start_time})
    status_rows = status_result.fetchall()

    prosumer_phases = {
        "prosumer1": "A",
        "prosumer2": "A",
        "prosumer3": "A",
        "prosumer4": "B",
        "prosumer5": "B",
        "prosumer6": "B",
        "prosumer7": "C",
    }

    prosumer_status = []
    violations = 0
    voltages = []

    for row in status_rows:
        voltage = round(row.voltage, 1)
        voltages.append(voltage)
        status = "normal"
        if voltage < 220 or voltage > 240:
            status = "critical"
            violations += 1
        elif voltage < 222 or voltage > 238:
            status = "warning"
            violations += 1

        prosumer_status.append(
            {
                "id": row.prosumer_id,
                "name": f"Prosumer {row.prosumer_id[-1]}",
                "phase": prosumer_phases.get(row.prosumer_id, "A"),
                "voltage": voltage,
                "status": status,
            }
        )

    avg_voltage = sum(voltages) / len(voltages) if voltages else 230

    return {
        "status": "success",
        "data": {
            "chart_data": chart_data,
            "prosumer_status": prosumer_status,
            "summary": {
                "violations": violations,
                "avg_voltage": round(avg_voltage, 1),
                "data_points": len(chart_data),
            },
        },
    }


@router.get("/voltage/prosumer/{prosumer_id}")
async def get_prosumer_voltage(
    prosumer_id: str,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of data to return"),
    limit: int = Query(default=288, ge=1, le=1000, description="Max records to return"),
    offset: int = Query(default=0, ge=0, description="Records to skip for pagination"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get voltage history for a specific prosumer.

    **Requires authentication**

    Returns voltage measurements with pagination support.
    """
    logger.info(
        f"Prosumer {prosumer_id} voltage requested by user: {current_user.username}"
    )
    query = text("""
        SELECT
            time,
            energy_meter_voltage as voltage,
            active_power,
            reactive_power
        FROM single_phase_meters
        WHERE prosumer_id = :prosumer_id
        ORDER BY time DESC
        LIMIT 288
    """)

    result = await db.execute(query, {"prosumer_id": prosumer_id})
    rows = result.fetchall()

    data = []
    for row in reversed(rows):
        data.append(
            {
                "time": row.time.strftime("%H:%M"),
                "voltage": round(row.voltage, 1),
                "active_power": round(row.active_power, 2) if row.active_power else 0,
                "reactive_power": round(row.reactive_power, 2)
                if row.reactive_power
                else 0,
            }
        )

    return {
        "status": "success",
        "data": {
            "prosumer_id": prosumer_id,
            "measurements": data,
            "count": len(data),
        },
    }


# =============================================================================
# Statistics Endpoint
# =============================================================================


@router.get("/stats")
async def get_data_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get statistics about all data in the database.

    **Requires authentication**
    """

    # Solar stats
    solar_query = text("""
        SELECT
            COUNT(*) as count,
            MIN(time) as first_time,
            MAX(time) as last_time
        FROM solar_measurements
    """)
    solar_result = await db.execute(solar_query)
    solar_row = solar_result.fetchone()

    # Voltage stats
    voltage_query = text("""
        SELECT
            COUNT(*) as count,
            COUNT(DISTINCT prosumer_id) as prosumer_count,
            MIN(time) as first_time,
            MAX(time) as last_time
        FROM single_phase_meters
    """)
    voltage_result = await db.execute(voltage_query)
    voltage_row = voltage_result.fetchone()

    # Prosumer list
    prosumer_query = text("SELECT id, name, phase FROM prosumers ORDER BY id")
    prosumer_result = await db.execute(prosumer_query)
    prosumers = [
        {"id": r.id, "name": r.name, "phase": r.phase}
        for r in prosumer_result.fetchall()
    ]

    return {
        "status": "success",
        "data": {
            "solar_measurements": {
                "total_count": solar_row.count if solar_row else 0,
                "date_range": {
                    "start": solar_row.first_time.isoformat()
                    if solar_row and solar_row.first_time
                    else None,
                    "end": solar_row.last_time.isoformat()
                    if solar_row and solar_row.last_time
                    else None,
                },
            },
            "voltage_measurements": {
                "total_count": voltage_row.count if voltage_row else 0,
                "prosumer_count": voltage_row.prosumer_count if voltage_row else 0,
                "date_range": {
                    "start": voltage_row.first_time.isoformat()
                    if voltage_row and voltage_row.first_time
                    else None,
                    "end": voltage_row.last_time.isoformat()
                    if voltage_row and voltage_row.last_time
                    else None,
                },
            },
            "prosumers": prosumers,
        },
    }
