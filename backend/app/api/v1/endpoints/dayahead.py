"""
Day-Ahead Forecast API endpoints.

Provides 24-hour forecast generation, scheduling, and report export.
"""

import io
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, get_current_user, require_roles
from app.db import get_db
from app.ml import get_solar_inference, get_voltage_inference

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Models
# =============================================================================


class ForecastType(str, Enum):
    solar = "solar"
    voltage = "voltage"


class HourlyForecast(BaseModel):
    """Hourly forecast data point."""
    hour: int
    timestamp: str
    predicted_value: float
    confidence_lower: float
    confidence_upper: float
    conditions: Optional[Dict[str, Any]] = None


class DayAheadForecastResponse(BaseModel):
    """Response for day-ahead forecast."""
    status: str
    data: Dict[str, Any]


class ForecastSchedule(BaseModel):
    """Scheduled forecast job configuration."""
    forecast_type: ForecastType
    target_date: str
    station_id: Optional[str] = "POC_STATION_1"
    prosumer_ids: Optional[List[str]] = None
    created_at: str
    status: str


# =============================================================================
# Endpoints
# =============================================================================


@router.get("/solar")
async def get_solar_day_ahead_forecast(
    target_date: Optional[str] = Query(
        default=None,
        description="Target date (YYYY-MM-DD). Defaults to tomorrow."
    ),
    station_id: str = Query(default="POC_STATION_1", description="Station ID"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Generate 24-hour day-ahead solar power forecast.

    **Requires authentication**

    Uses historical patterns and weather data to predict hourly power output
    for the next day.
    """
    logger.info(f"Day-ahead solar forecast requested by {current_user.username}")

    # Parse target date
    if target_date:
        forecast_date = datetime.strptime(target_date, "%Y-%m-%d").date()
    else:
        forecast_date = (datetime.now() + timedelta(days=1)).date()

    # Get historical averages for each hour from the database
    hourly_avg_query = text("""
        SELECT
            EXTRACT(HOUR FROM time) as hour,
            AVG(power_kw) as avg_power,
            STDDEV(power_kw) as std_power,
            AVG(pyrano1) as avg_irradiance,
            AVG(ambtemp) as avg_temp
        FROM solar_measurements
        WHERE station_id = :station_id
        GROUP BY EXTRACT(HOUR FROM time)
        ORDER BY hour
    """)

    result = await db.execute(hourly_avg_query, {"station_id": station_id})
    historical_data = {int(row[0]): row for row in result.fetchall()}

    # Get inference service for ML predictions
    inference = get_solar_inference()

    hourly_forecasts = []
    total_energy = 0.0
    peak_hour = 0
    peak_power = 0.0

    for hour in range(24):
        timestamp = datetime.combine(forecast_date, datetime.min.time().replace(hour=hour))

        # Use ML model if available, else use historical average
        if inference.is_loaded and hour in historical_data:
            hist = historical_data[hour]
            result = inference.predict(
                timestamp=timestamp,
                pyrano1=hist[3] or 0,  # avg_irradiance
                pyrano2=hist[3] or 0,
                pvtemp1=35.0,  # Assume typical values
                pvtemp2=35.0,
                ambtemp=hist[4] or 30,  # avg_temp
                windspeed=2.0,
            )
            predicted_power = result["power_kw"]
            confidence_lower = result["confidence_lower"]
            confidence_upper = result["confidence_upper"]
        elif hour in historical_data:
            hist = historical_data[hour]
            predicted_power = hist[1] or 0  # avg_power
            std = hist[2] or 0  # std_power
            confidence_lower = max(0, predicted_power - 1.96 * std)
            confidence_upper = predicted_power + 1.96 * std
        else:
            # No historical data - use solar curve approximation
            if 6 <= hour <= 18:
                # Simple solar curve: peaks at noon
                solar_factor = max(0, 1 - abs(hour - 12) / 6)
                predicted_power = 3000 * solar_factor  # Assume 3MW peak
                confidence_lower = predicted_power * 0.8
                confidence_upper = predicted_power * 1.2
            else:
                predicted_power = 0
                confidence_lower = 0
                confidence_upper = 0

        # Round values
        predicted_power = round(predicted_power, 1)
        confidence_lower = round(confidence_lower, 1)
        confidence_upper = round(confidence_upper, 1)

        # Track statistics
        total_energy += predicted_power  # kWh (hourly)
        if predicted_power > peak_power:
            peak_power = predicted_power
            peak_hour = hour

        hourly_forecasts.append({
            "hour": hour,
            "timestamp": timestamp.isoformat(),
            "predicted_power_kw": predicted_power,
            "confidence_lower": confidence_lower,
            "confidence_upper": confidence_upper,
            "conditions": {
                "irradiance": historical_data.get(hour, [None] * 5)[3],
                "temperature": historical_data.get(hour, [None] * 5)[4],
            } if hour in historical_data else None,
        })

    return {
        "status": "success",
        "data": {
            "forecast_date": str(forecast_date),
            "station_id": station_id,
            "generated_at": datetime.now().isoformat(),
            "model_version": inference.model_version if inference.is_loaded else "historical_avg",
            "hourly_forecasts": hourly_forecasts,
            "summary": {
                "total_energy_kwh": round(total_energy, 1),
                "peak_power_kw": peak_power,
                "peak_hour": peak_hour,
                "generation_hours": sum(1 for f in hourly_forecasts if f["predicted_power_kw"] > 0),
            },
        },
    }


@router.get("/voltage")
async def get_voltage_day_ahead_forecast(
    target_date: Optional[str] = Query(
        default=None,
        description="Target date (YYYY-MM-DD). Defaults to tomorrow."
    ),
    prosumer_id: Optional[str] = Query(default=None, description="Filter by prosumer ID"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Generate 24-hour day-ahead voltage forecast for prosumers.

    **Requires authentication**

    Predicts hourly voltage levels and identifies potential violations.
    """
    logger.info(f"Day-ahead voltage forecast requested by {current_user.username}")

    # Parse target date
    if target_date:
        forecast_date = datetime.strptime(target_date, "%Y-%m-%d").date()
    else:
        forecast_date = (datetime.now() + timedelta(days=1)).date()

    # Get prosumer list
    prosumer_query = text("SELECT id, name, phase FROM prosumers ORDER BY id")
    prosumer_result = await db.execute(prosumer_query)
    prosumers = [{"id": r[0], "name": r[1], "phase": r[2]} for r in prosumer_result.fetchall()]

    if prosumer_id:
        prosumers = [p for p in prosumers if p["id"] == prosumer_id]

    # Get historical voltage patterns
    hourly_query = text("""
        SELECT
            prosumer_id,
            EXTRACT(HOUR FROM time) as hour,
            AVG(energy_meter_voltage) as avg_voltage,
            STDDEV(energy_meter_voltage) as std_voltage,
            MIN(energy_meter_voltage) as min_voltage,
            MAX(energy_meter_voltage) as max_voltage
        FROM single_phase_meters
        GROUP BY prosumer_id, EXTRACT(HOUR FROM time)
        ORDER BY prosumer_id, hour
    """)

    result = await db.execute(hourly_query)
    historical_data: Dict[str, Dict[int, Any]] = {}
    for row in result.fetchall():
        pid = row[0]
        hour = int(row[1])
        if pid not in historical_data:
            historical_data[pid] = {}
        historical_data[pid][hour] = {
            "avg": row[2],
            "std": row[3],
            "min": row[4],
            "max": row[5],
        }

    # Get inference service
    inference = get_voltage_inference()

    prosumer_forecasts = []
    total_violations = 0

    for prosumer in prosumers:
        pid = prosumer["id"]
        hourly_forecasts = []
        violations_count = 0

        for hour in range(24):
            timestamp = datetime.combine(forecast_date, datetime.min.time().replace(hour=hour))

            # Get prediction
            if inference.is_loaded:
                result = inference.predict(timestamp=timestamp, prosumer_id=pid)
                predicted_voltage = result["predicted_voltage"]
                confidence_lower = result["confidence_lower"]
                confidence_upper = result["confidence_upper"]
            elif pid in historical_data and hour in historical_data[pid]:
                hist = historical_data[pid][hour]
                predicted_voltage = hist["avg"] or 230
                std = hist["std"] or 2
                confidence_lower = predicted_voltage - 1.96 * std
                confidence_upper = predicted_voltage + 1.96 * std
            else:
                # Default nominal
                predicted_voltage = 230
                confidence_lower = 225
                confidence_upper = 235

            # Round values
            predicted_voltage = round(predicted_voltage, 1)
            confidence_lower = round(confidence_lower, 1)
            confidence_upper = round(confidence_upper, 1)

            # Check for violations
            status = "normal"
            if predicted_voltage < 218 or predicted_voltage > 242:
                status = "critical"
                violations_count += 1
            elif predicted_voltage < 222 or predicted_voltage > 238:
                status = "warning"

            hourly_forecasts.append({
                "hour": hour,
                "timestamp": timestamp.isoformat(),
                "predicted_voltage": predicted_voltage,
                "confidence_lower": confidence_lower,
                "confidence_upper": confidence_upper,
                "status": status,
            })

        total_violations += violations_count

        # Calculate prosumer summary
        voltages = [f["predicted_voltage"] for f in hourly_forecasts]
        prosumer_forecasts.append({
            "prosumer_id": pid,
            "name": prosumer["name"],
            "phase": prosumer["phase"],
            "hourly_forecasts": hourly_forecasts,
            "summary": {
                "avg_voltage": round(sum(voltages) / len(voltages), 1),
                "min_voltage": min(voltages),
                "max_voltage": max(voltages),
                "violation_hours": violations_count,
            },
        })

    return {
        "status": "success",
        "data": {
            "forecast_date": str(forecast_date),
            "generated_at": datetime.now().isoformat(),
            "model_version": inference.model_version if inference.is_loaded else "historical_avg",
            "prosumer_forecasts": prosumer_forecasts,
            "summary": {
                "total_prosumers": len(prosumers),
                "total_violation_hours": total_violations,
                "voltage_limits": {
                    "nominal": 230,
                    "lower_critical": 218,
                    "upper_critical": 242,
                    "lower_warning": 222,
                    "upper_warning": 238,
                },
            },
        },
    }


@router.get("/report")
async def generate_day_ahead_report(
    target_date: Optional[str] = Query(
        default=None,
        description="Target date (YYYY-MM-DD). Defaults to tomorrow."
    ),
    format: str = Query(default="json", description="Report format: json or html"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(["admin", "analyst", "operator"])),
) -> Response:
    """
    Generate comprehensive day-ahead forecast report.

    **Requires roles:** admin, analyst, or operator

    Combines solar and voltage forecasts into a single report.
    """
    logger.info(f"Day-ahead report requested by {current_user.username}")

    # Parse target date
    if target_date:
        forecast_date = datetime.strptime(target_date, "%Y-%m-%d").date()
    else:
        forecast_date = (datetime.now() + timedelta(days=1)).date()

    # Get solar forecast
    solar_query = text("""
        SELECT
            EXTRACT(HOUR FROM time) as hour,
            AVG(power_kw) as avg_power
        FROM solar_measurements
        GROUP BY EXTRACT(HOUR FROM time)
        ORDER BY hour
    """)
    solar_result = await db.execute(solar_query)
    solar_data = {int(r[0]): round(r[1] or 0, 1) for r in solar_result.fetchall()}

    # Get voltage forecast
    voltage_query = text("""
        SELECT
            prosumer_id,
            AVG(energy_meter_voltage) as avg_voltage
        FROM single_phase_meters
        GROUP BY prosumer_id
    """)
    voltage_result = await db.execute(voltage_query)
    voltage_data = {r[0]: round(r[1] or 230, 1) for r in voltage_result.fetchall()}

    report_data = {
        "report_type": "Day-Ahead Forecast Report",
        "forecast_date": str(forecast_date),
        "generated_at": datetime.now().isoformat(),
        "generated_by": current_user.username,
        "solar_forecast": {
            "station_id": "POC_STATION_1",
            "total_energy_kwh": sum(solar_data.values()),
            "peak_power_kw": max(solar_data.values()) if solar_data else 0,
            "hourly_forecast": [
                {"hour": h, "power_kw": solar_data.get(h, 0)} for h in range(24)
            ],
        },
        "voltage_forecast": {
            "prosumers": [
                {"prosumer_id": pid, "avg_voltage": v} for pid, v in voltage_data.items()
            ],
            "overall_avg_voltage": round(sum(voltage_data.values()) / len(voltage_data), 1) if voltage_data else 230,
        },
        "recommendations": [],
    }

    # Add recommendations based on forecasts
    if report_data["solar_forecast"]["peak_power_kw"] > 4000:
        report_data["recommendations"].append({
            "type": "solar_high",
            "message": "High solar generation expected. Monitor for voltage rise.",
            "severity": "info",
        })

    avg_voltage = report_data["voltage_forecast"]["overall_avg_voltage"]
    if avg_voltage > 235:
        report_data["recommendations"].append({
            "type": "voltage_high",
            "message": f"Average voltage {avg_voltage}V trending high. Consider reactive power compensation.",
            "severity": "warning",
        })
    elif avg_voltage < 225:
        report_data["recommendations"].append({
            "type": "voltage_low",
            "message": f"Average voltage {avg_voltage}V trending low. Monitor load conditions.",
            "severity": "warning",
        })

    if format == "html":
        # Generate HTML report
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Day-Ahead Forecast Report - {forecast_date}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #74045F; }}
        h2 {{ color: #5A0349; border-bottom: 2px solid #D4A43D; padding-bottom: 5px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #74045F; color: white; }}
        .warning {{ background-color: #FEF3C7; }}
        .info {{ background-color: #DBEAFE; }}
        .summary {{ background-color: #F3F4F6; padding: 15px; border-radius: 8px; margin: 20px 0; }}
    </style>
</head>
<body>
    <h1>PEA RE Forecast Platform</h1>
    <h2>Day-Ahead Forecast Report</h2>
    <p><strong>Forecast Date:</strong> {forecast_date}</p>
    <p><strong>Generated:</strong> {report_data['generated_at']}</p>
    <p><strong>Generated By:</strong> {report_data['generated_by']}</p>

    <div class="summary">
        <h3>Solar Forecast Summary</h3>
        <p>Total Energy: <strong>{report_data['solar_forecast']['total_energy_kwh']:.1f} kWh</strong></p>
        <p>Peak Power: <strong>{report_data['solar_forecast']['peak_power_kw']:.1f} kW</strong></p>
    </div>

    <div class="summary">
        <h3>Voltage Forecast Summary</h3>
        <p>Average Voltage: <strong>{report_data['voltage_forecast']['overall_avg_voltage']:.1f} V</strong></p>
        <p>Prosumers Monitored: <strong>{len(report_data['voltage_forecast']['prosumers'])}</strong></p>
    </div>

    {"".join(f'<div class="{r["severity"]}"><strong>{r["type"]}:</strong> {r["message"]}</div>' for r in report_data['recommendations'])}

    <h2>Hourly Solar Forecast</h2>
    <table>
        <tr><th>Hour</th><th>Power (kW)</th></tr>
        {"".join(f'<tr><td>{h["hour"]:02d}:00</td><td>{h["power_kw"]:.1f}</td></tr>' for h in report_data['solar_forecast']['hourly_forecast'])}
    </table>

    <footer style="margin-top: 40px; color: #666; font-size: 12px;">
        <p>PEA RE Forecast Platform - การไฟฟ้าส่วนภูมิภาค</p>
    </footer>
</body>
</html>
"""
        return Response(
            content=html_content,
            media_type="text/html",
            headers={"Content-Disposition": f"attachment; filename=dayahead_report_{forecast_date}.html"},
        )
    else:
        import json
        return Response(
            content=json.dumps(report_data, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=dayahead_report_{forecast_date}.json"},
        )


@router.get("/schedule")
async def list_forecast_schedules(
    current_user: CurrentUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    List scheduled day-ahead forecast jobs.

    **Requires authentication**

    Shows configured automatic forecast generation schedules.
    """
    # For POC, return mock schedule data
    # In production, this would query a scheduling database/service
    schedules = [
        {
            "id": "schedule-solar-daily",
            "forecast_type": "solar",
            "cron": "0 18 * * *",  # 6 PM daily
            "description": "Daily solar day-ahead forecast",
            "station_id": "POC_STATION_1",
            "enabled": True,
            "last_run": (datetime.now() - timedelta(hours=6)).isoformat(),
            "next_run": (datetime.now() + timedelta(hours=18)).isoformat(),
        },
        {
            "id": "schedule-voltage-daily",
            "forecast_type": "voltage",
            "cron": "0 18 * * *",  # 6 PM daily
            "description": "Daily voltage day-ahead forecast",
            "enabled": True,
            "last_run": (datetime.now() - timedelta(hours=6)).isoformat(),
            "next_run": (datetime.now() + timedelta(hours=18)).isoformat(),
        },
    ]

    return {
        "status": "success",
        "data": {
            "schedules": schedules,
            "count": len(schedules),
        },
    }
