"""
Historical Analysis API endpoints.

Provides date range queries, aggregations, and export functionality
for solar and voltage measurement data.
"""

import csv
import io
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, get_current_user, require_roles
from app.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Enums and Models
# =============================================================================


class DataType(str, Enum):
    solar = "solar"
    voltage = "voltage"


class AggregationInterval(str, Enum):
    raw = "raw"
    minute_5 = "5m"
    minute_15 = "15m"
    hour = "1h"
    day = "1d"


class ExportFormat(str, Enum):
    json = "json"
    csv = "csv"


class DateRangeStats(BaseModel):
    """Statistics for a date range."""
    count: int
    avg: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    std: Optional[float] = None


class HistoricalDataPoint(BaseModel):
    """A single historical data point."""
    time: str
    value: float
    metadata: Optional[Dict[str, Any]] = None


class HistoricalResponse(BaseModel):
    """Response for historical data queries."""
    status: str
    data: Dict[str, Any]


# =============================================================================
# Helper Functions
# =============================================================================


def get_time_bucket(interval: AggregationInterval) -> str:
    """Convert aggregation interval to TimescaleDB time_bucket format."""
    mapping = {
        AggregationInterval.minute_5: "5 minutes",
        AggregationInterval.minute_15: "15 minutes",
        AggregationInterval.hour: "1 hour",
        AggregationInterval.day: "1 day",
    }
    return mapping.get(interval, "1 hour")


# =============================================================================
# Solar Historical Endpoints
# =============================================================================


@router.get("/solar")
async def get_solar_history(
    start_date: datetime = Query(..., description="Start date (ISO format)"),
    end_date: datetime = Query(..., description="End date (ISO format)"),
    station_id: str = Query(default="POC_STATION_1", description="Station ID"),
    interval: AggregationInterval = Query(default=AggregationInterval.hour, description="Aggregation interval"),
    limit: int = Query(default=1000, ge=1, le=10000, description="Max records"),
    offset: int = Query(default=0, ge=0, description="Records to skip"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get historical solar measurements for a date range.

    **Requires authentication**

    Supports various aggregation intervals for different analysis needs.
    """
    logger.info(f"Solar history requested by {current_user.username}: {start_date} to {end_date}")

    if interval == AggregationInterval.raw:
        # Raw data query
        query = text("""
            SELECT
                time,
                power_kw,
                pyrano1,
                pyrano2,
                pvtemp1,
                pvtemp2,
                ambtemp,
                windspeed
            FROM solar_measurements
            WHERE station_id = :station_id
              AND time >= :start_date
              AND time <= :end_date
            ORDER BY time ASC
            LIMIT :limit OFFSET :offset
        """)
    else:
        # Aggregated data query
        bucket = get_time_bucket(interval)
        query = text(f"""
            SELECT
                time_bucket('{bucket}', time) as bucket,
                AVG(power_kw) as avg_power,
                MIN(power_kw) as min_power,
                MAX(power_kw) as max_power,
                AVG(pyrano1) as avg_irradiance,
                AVG(ambtemp) as avg_temp,
                COUNT(*) as sample_count
            FROM solar_measurements
            WHERE station_id = :station_id
              AND time >= :start_date
              AND time <= :end_date
            GROUP BY bucket
            ORDER BY bucket ASC
            LIMIT :limit OFFSET :offset
        """)

    result = await db.execute(
        query,
        {
            "station_id": station_id,
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit,
            "offset": offset,
        },
    )
    rows = result.fetchall()

    # Count total records
    count_query = text("""
        SELECT COUNT(*) FROM solar_measurements
        WHERE station_id = :station_id
          AND time >= :start_date
          AND time <= :end_date
    """)
    count_result = await db.execute(
        count_query,
        {"station_id": station_id, "start_date": start_date, "end_date": end_date},
    )
    total_count = count_result.scalar() or 0

    # Format response
    if interval == AggregationInterval.raw:
        data_points = [
            {
                "time": row[0].isoformat() if row[0] else None,
                "power_kw": round(row[1], 2) if row[1] else None,
                "irradiance": round(row[2], 1) if row[2] else None,
                "irradiance_2": round(row[3], 1) if row[3] else None,
                "pv_temp_1": round(row[4], 1) if row[4] else None,
                "pv_temp_2": round(row[5], 1) if row[5] else None,
                "ambient_temp": round(row[6], 1) if row[6] else None,
                "wind_speed": round(row[7], 2) if row[7] else None,
            }
            for row in rows
        ]
    else:
        data_points = [
            {
                "time": row[0].isoformat() if row[0] else None,
                "avg_power": round(row[1], 2) if row[1] else None,
                "min_power": round(row[2], 2) if row[2] else None,
                "max_power": round(row[3], 2) if row[3] else None,
                "avg_irradiance": round(row[4], 1) if row[4] else None,
                "avg_temp": round(row[5], 1) if row[5] else None,
                "sample_count": row[6],
            }
            for row in rows
        ]

    return {
        "status": "success",
        "data": {
            "station_id": station_id,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "interval": interval.value,
            "data_points": data_points,
            "pagination": {
                "count": len(data_points),
                "total": total_count,
                "limit": limit,
                "offset": offset,
            },
        },
    }


@router.get("/solar/summary")
async def get_solar_summary(
    start_date: datetime = Query(..., description="Start date (ISO format)"),
    end_date: datetime = Query(..., description="End date (ISO format)"),
    station_id: str = Query(default="POC_STATION_1", description="Station ID"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get summary statistics for solar data in a date range.

    **Requires authentication**

    Returns aggregated metrics including totals, averages, and distributions.
    """
    logger.info(f"Solar summary requested by {current_user.username}")

    # Overall statistics
    stats_query = text("""
        SELECT
            COUNT(*) as total_count,
            AVG(power_kw) as avg_power,
            MIN(power_kw) as min_power,
            MAX(power_kw) as max_power,
            STDDEV(power_kw) as std_power,
            SUM(power_kw * 5 / 60) as total_energy_kwh,
            AVG(pyrano1) as avg_irradiance,
            AVG(ambtemp) as avg_temp
        FROM solar_measurements
        WHERE station_id = :station_id
          AND time >= :start_date
          AND time <= :end_date
    """)

    result = await db.execute(
        stats_query,
        {"station_id": station_id, "start_date": start_date, "end_date": end_date},
    )
    stats_row = result.fetchone()

    # Hourly distribution
    hourly_query = text("""
        SELECT
            EXTRACT(HOUR FROM time) as hour,
            AVG(power_kw) as avg_power,
            COUNT(*) as count
        FROM solar_measurements
        WHERE station_id = :station_id
          AND time >= :start_date
          AND time <= :end_date
        GROUP BY EXTRACT(HOUR FROM time)
        ORDER BY hour
    """)

    hourly_result = await db.execute(
        hourly_query,
        {"station_id": station_id, "start_date": start_date, "end_date": end_date},
    )
    hourly_rows = hourly_result.fetchall()

    hourly_distribution = [
        {"hour": int(row[0]), "avg_power": round(row[1], 2) if row[1] else 0, "count": row[2]}
        for row in hourly_rows
    ]

    # Daily aggregates
    daily_query = text("""
        SELECT
            DATE(time) as day,
            AVG(power_kw) as avg_power,
            MAX(power_kw) as peak_power,
            SUM(power_kw * 5 / 60) as energy_kwh
        FROM solar_measurements
        WHERE station_id = :station_id
          AND time >= :start_date
          AND time <= :end_date
        GROUP BY DATE(time)
        ORDER BY day
    """)

    daily_result = await db.execute(
        daily_query,
        {"station_id": station_id, "start_date": start_date, "end_date": end_date},
    )
    daily_rows = daily_result.fetchall()

    daily_aggregates = [
        {
            "date": row[0].isoformat() if row[0] else None,
            "avg_power": round(row[1], 2) if row[1] else 0,
            "peak_power": round(row[2], 2) if row[2] else 0,
            "energy_kwh": round(row[3], 2) if row[3] else 0,
        }
        for row in daily_rows
    ]

    return {
        "status": "success",
        "data": {
            "station_id": station_id,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "statistics": {
                "total_measurements": stats_row[0] if stats_row else 0,
                "avg_power_kw": round(stats_row[1], 2) if stats_row and stats_row[1] else 0,
                "min_power_kw": round(stats_row[2], 2) if stats_row and stats_row[2] else 0,
                "max_power_kw": round(stats_row[3], 2) if stats_row and stats_row[3] else 0,
                "std_power_kw": round(stats_row[4], 2) if stats_row and stats_row[4] else 0,
                "total_energy_kwh": round(stats_row[5], 2) if stats_row and stats_row[5] else 0,
                "avg_irradiance": round(stats_row[6], 1) if stats_row and stats_row[6] else 0,
                "avg_temperature": round(stats_row[7], 1) if stats_row and stats_row[7] else 0,
            },
            "hourly_distribution": hourly_distribution,
            "daily_aggregates": daily_aggregates,
        },
    }


# =============================================================================
# Voltage Historical Endpoints
# =============================================================================


@router.get("/voltage")
async def get_voltage_history(
    start_date: datetime = Query(..., description="Start date (ISO format)"),
    end_date: datetime = Query(..., description="End date (ISO format)"),
    prosumer_id: Optional[str] = Query(default=None, description="Filter by prosumer ID"),
    phase: Optional[str] = Query(default=None, description="Filter by phase (A, B, C)"),
    interval: AggregationInterval = Query(default=AggregationInterval.hour, description="Aggregation interval"),
    limit: int = Query(default=1000, ge=1, le=10000, description="Max records"),
    offset: int = Query(default=0, ge=0, description="Records to skip"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get historical voltage measurements for a date range.

    **Requires authentication**

    Can filter by prosumer ID or phase.
    """
    logger.info(f"Voltage history requested by {current_user.username}: {start_date} to {end_date}")

    # Build WHERE clause
    where_conditions = ["m.time >= :start_date", "m.time <= :end_date"]
    params: Dict[str, Any] = {"start_date": start_date, "end_date": end_date, "limit": limit, "offset": offset}

    if prosumer_id:
        where_conditions.append("m.prosumer_id = :prosumer_id")
        params["prosumer_id"] = prosumer_id

    if phase:
        where_conditions.append("p.phase = :phase")
        params["phase"] = phase

    where_clause = " AND ".join(where_conditions)

    if interval == AggregationInterval.raw:
        query = text(f"""
            SELECT
                m.time,
                m.prosumer_id,
                p.phase,
                m.energy_meter_voltage as voltage,
                m.active_power,
                m.reactive_power
            FROM single_phase_meters m
            JOIN prosumers p ON m.prosumer_id = p.id
            WHERE {where_clause}
            ORDER BY m.time ASC, m.prosumer_id
            LIMIT :limit OFFSET :offset
        """)
    else:
        bucket = get_time_bucket(interval)
        query = text(f"""
            SELECT
                time_bucket('{bucket}', m.time) as bucket,
                m.prosumer_id,
                p.phase,
                AVG(m.energy_meter_voltage) as avg_voltage,
                MIN(m.energy_meter_voltage) as min_voltage,
                MAX(m.energy_meter_voltage) as max_voltage,
                AVG(m.active_power) as avg_power,
                COUNT(*) as sample_count
            FROM single_phase_meters m
            JOIN prosumers p ON m.prosumer_id = p.id
            WHERE {where_clause}
            GROUP BY bucket, m.prosumer_id, p.phase
            ORDER BY bucket ASC, m.prosumer_id
            LIMIT :limit OFFSET :offset
        """)

    result = await db.execute(query, params)
    rows = result.fetchall()

    # Count total
    count_params = {k: v for k, v in params.items() if k not in ("limit", "offset")}
    count_query = text(f"""
        SELECT COUNT(*) FROM single_phase_meters m
        JOIN prosumers p ON m.prosumer_id = p.id
        WHERE {where_clause}
    """)
    count_result = await db.execute(count_query, count_params)
    total_count = count_result.scalar() or 0

    # Format response
    if interval == AggregationInterval.raw:
        data_points = [
            {
                "time": row[0].isoformat() if row[0] else None,
                "prosumer_id": row[1],
                "phase": row[2],
                "voltage": round(row[3], 1) if row[3] else None,
                "active_power": round(row[4], 2) if row[4] else None,
                "reactive_power": round(row[5], 2) if row[5] else None,
            }
            for row in rows
        ]
    else:
        data_points = [
            {
                "time": row[0].isoformat() if row[0] else None,
                "prosumer_id": row[1],
                "phase": row[2],
                "avg_voltage": round(row[3], 1) if row[3] else None,
                "min_voltage": round(row[4], 1) if row[4] else None,
                "max_voltage": round(row[5], 1) if row[5] else None,
                "avg_power": round(row[6], 2) if row[6] else None,
                "sample_count": row[7],
            }
            for row in rows
        ]

    return {
        "status": "success",
        "data": {
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "filters": {
                "prosumer_id": prosumer_id,
                "phase": phase,
            },
            "interval": interval.value,
            "data_points": data_points,
            "pagination": {
                "count": len(data_points),
                "total": total_count,
                "limit": limit,
                "offset": offset,
            },
        },
    }


@router.get("/voltage/summary")
async def get_voltage_summary(
    start_date: datetime = Query(..., description="Start date (ISO format)"),
    end_date: datetime = Query(..., description="End date (ISO format)"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get summary statistics for voltage data in a date range.

    **Requires authentication**

    Returns per-prosumer and per-phase aggregated metrics.
    """
    logger.info(f"Voltage summary requested by {current_user.username}")

    # Per-prosumer statistics
    prosumer_query = text("""
        SELECT
            m.prosumer_id,
            p.phase,
            p.name,
            COUNT(*) as count,
            AVG(m.energy_meter_voltage) as avg_voltage,
            MIN(m.energy_meter_voltage) as min_voltage,
            MAX(m.energy_meter_voltage) as max_voltage,
            STDDEV(m.energy_meter_voltage) as std_voltage,
            SUM(CASE WHEN m.energy_meter_voltage < 218 OR m.energy_meter_voltage > 242 THEN 1 ELSE 0 END) as violations
        FROM single_phase_meters m
        JOIN prosumers p ON m.prosumer_id = p.id
        WHERE m.time >= :start_date AND m.time <= :end_date
        GROUP BY m.prosumer_id, p.phase, p.name
        ORDER BY m.prosumer_id
    """)

    result = await db.execute(
        prosumer_query,
        {"start_date": start_date, "end_date": end_date},
    )
    prosumer_rows = result.fetchall()

    prosumer_stats = [
        {
            "prosumer_id": row[0],
            "phase": row[1],
            "name": row[2],
            "measurements": row[3],
            "avg_voltage": round(row[4], 1) if row[4] else None,
            "min_voltage": round(row[5], 1) if row[5] else None,
            "max_voltage": round(row[6], 1) if row[6] else None,
            "std_voltage": round(row[7], 2) if row[7] else None,
            "violations": row[8],
        }
        for row in prosumer_rows
    ]

    # Per-phase statistics
    phase_query = text("""
        SELECT
            p.phase,
            COUNT(*) as count,
            AVG(m.energy_meter_voltage) as avg_voltage,
            MIN(m.energy_meter_voltage) as min_voltage,
            MAX(m.energy_meter_voltage) as max_voltage,
            SUM(CASE WHEN m.energy_meter_voltage < 218 OR m.energy_meter_voltage > 242 THEN 1 ELSE 0 END) as violations
        FROM single_phase_meters m
        JOIN prosumers p ON m.prosumer_id = p.id
        WHERE m.time >= :start_date AND m.time <= :end_date
        GROUP BY p.phase
        ORDER BY p.phase
    """)

    phase_result = await db.execute(
        phase_query,
        {"start_date": start_date, "end_date": end_date},
    )
    phase_rows = phase_result.fetchall()

    phase_stats = [
        {
            "phase": row[0],
            "measurements": row[1],
            "avg_voltage": round(row[2], 1) if row[2] else None,
            "min_voltage": round(row[3], 1) if row[3] else None,
            "max_voltage": round(row[4], 1) if row[4] else None,
            "violations": row[5],
        }
        for row in phase_rows
    ]

    # Overall statistics
    overall_query = text("""
        SELECT
            COUNT(*) as total_count,
            AVG(energy_meter_voltage) as avg_voltage,
            MIN(energy_meter_voltage) as min_voltage,
            MAX(energy_meter_voltage) as max_voltage,
            SUM(CASE WHEN energy_meter_voltage < 218 OR energy_meter_voltage > 242 THEN 1 ELSE 0 END) as violations
        FROM single_phase_meters
        WHERE time >= :start_date AND time <= :end_date
    """)

    overall_result = await db.execute(
        overall_query,
        {"start_date": start_date, "end_date": end_date},
    )
    overall_row = overall_result.fetchone()

    return {
        "status": "success",
        "data": {
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "overall": {
                "total_measurements": overall_row[0] if overall_row else 0,
                "avg_voltage": round(overall_row[1], 1) if overall_row and overall_row[1] else None,
                "min_voltage": round(overall_row[2], 1) if overall_row and overall_row[2] else None,
                "max_voltage": round(overall_row[3], 1) if overall_row and overall_row[3] else None,
                "total_violations": overall_row[4] if overall_row else 0,
            },
            "by_prosumer": prosumer_stats,
            "by_phase": phase_stats,
        },
    }


# =============================================================================
# Export Endpoints
# =============================================================================


@router.get("/export")
async def export_historical_data(
    data_type: DataType = Query(..., description="Type of data to export"),
    start_date: datetime = Query(..., description="Start date (ISO format)"),
    end_date: datetime = Query(..., description="End date (ISO format)"),
    format: ExportFormat = Query(default=ExportFormat.csv, description="Export format"),
    station_id: str = Query(default="POC_STATION_1", description="Station ID (for solar)"),
    prosumer_id: Optional[str] = Query(default=None, description="Prosumer ID (for voltage)"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(["admin", "analyst"])),
) -> Response:
    """
    Export historical data as CSV or JSON.

    **Requires roles:** admin or analyst

    Downloads a file with the requested data.
    """
    logger.info(f"Data export requested by {current_user.username}: {data_type.value}")

    if data_type == DataType.solar:
        query = text("""
            SELECT
                time,
                station_id,
                power_kw,
                pyrano1,
                pyrano2,
                pvtemp1,
                pvtemp2,
                ambtemp,
                windspeed
            FROM solar_measurements
            WHERE station_id = :station_id
              AND time >= :start_date
              AND time <= :end_date
            ORDER BY time ASC
            LIMIT 50000
        """)
        result = await db.execute(
            query,
            {"station_id": station_id, "start_date": start_date, "end_date": end_date},
        )
        rows = result.fetchall()
        columns = ["time", "station_id", "power_kw", "pyrano1", "pyrano2", "pvtemp1", "pvtemp2", "ambtemp", "windspeed"]
        filename = f"solar_export_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"

    else:  # voltage
        where_clause = "time >= :start_date AND time <= :end_date"
        params: Dict[str, Any] = {"start_date": start_date, "end_date": end_date}
        if prosumer_id:
            where_clause += " AND prosumer_id = :prosumer_id"
            params["prosumer_id"] = prosumer_id

        query = text(f"""
            SELECT
                time,
                prosumer_id,
                energy_meter_voltage,
                active_power,
                reactive_power,
                energy_meter_current
            FROM single_phase_meters
            WHERE {where_clause}
            ORDER BY time ASC, prosumer_id
            LIMIT 50000
        """)
        result = await db.execute(query, params)
        rows = result.fetchall()
        columns = ["time", "prosumer_id", "voltage", "active_power", "reactive_power", "current"]
        filename = f"voltage_export_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"

    if format == ExportFormat.csv:
        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(columns)
        for row in rows:
            writer.writerow([
                row[0].isoformat() if hasattr(row[0], 'isoformat') else row[0],
                *row[1:],
            ])
        content = output.getvalue()
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}.csv"},
        )
    else:
        # Generate JSON
        import json
        data = [
            {columns[i]: (row[i].isoformat() if hasattr(row[i], 'isoformat') else row[i]) for i in range(len(columns))}
            for row in rows
        ]
        content = json.dumps({"data": data, "count": len(data)}, indent=2)
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}.json"},
        )
