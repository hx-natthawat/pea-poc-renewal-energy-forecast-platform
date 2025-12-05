"""Weather API endpoints for extreme weather handling."""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Query
from loguru import logger

from app.models.schemas.weather import (
    WeatherCondition,
    WeatherEventLog,
)
from app.services.ramp_rate_service import ramp_rate_service
from app.services.weather_service import weather_service

router = APIRouter(prefix="/weather", tags=["weather"])


@router.get("/alerts", response_model=dict)
async def get_weather_alerts(
    region: str | None = Query(None, description="Filter by region"),
    severity: str | None = Query(
        None, description="Filter by severity (info, warning, critical)"
    ),
):
    """
    Get current weather alerts from TMD.

    Returns active weather alerts for the specified region.
    Weather alerts help operators prepare for extreme conditions
    that may affect solar power generation.
    """
    try:
        alerts = await weather_service.get_current_alerts(region=region)

        if severity:
            alerts = [a for a in alerts if a.severity.value == severity]

        return {
            "status": "success",
            "data": {
                "alerts": [a.model_dump() for a in alerts],
                "count": len(alerts),
                "timestamp": datetime.now(UTC).isoformat(),
            },
        }
    except Exception as e:
        logger.error(f"Error fetching weather alerts: {e}")
        return {
            "status": "success",
            "data": {
                "alerts": [],
                "count": 0,
                "timestamp": datetime.now(UTC).isoformat(),
                "message": "Weather alert service temporarily unavailable",
            },
        }


@router.get("/condition", response_model=dict)
async def get_weather_condition(
    latitude: float = Query(default=13.7563, description="Location latitude"),
    longitude: float = Query(default=100.5018, description="Location longitude"),
):
    """
    Get current weather condition for location.

    Returns classified weather condition (clear, cloudy, rainy, etc.)
    along with relevant meteorological data.

    Default location is Bangkok, Thailand.
    """
    try:
        condition = await weather_service.get_weather_condition(
            latitude=latitude, longitude=longitude
        )

        return {
            "status": "success",
            "data": condition.model_dump(),
        }
    except Exception as e:
        logger.error(f"Error getting weather condition: {e}")
        return {
            "status": "success",
            "data": {
                "condition": WeatherCondition.PARTLY_CLOUDY.value,
                "timestamp": datetime.now(UTC).isoformat(),
                "message": "Using default weather condition",
            },
        }


@router.get("/ramp-rate/current", response_model=dict)
async def get_current_ramp_rate(
    station_id: str = Query(default="POC_STATION_1", description="Station ID"),
):
    """
    Get current ramp rate monitoring status.

    Returns the latest ramp rate detection results including:
    - Current rate of change in irradiance
    - Whether an alert threshold is exceeded
    - Last detected ramp event
    """
    try:
        status = ramp_rate_service.get_current_status()

        return {
            "status": "success",
            "data": {
                "current_ramp_rate_percent": status.current_ramp_rate_percent,
                "threshold_percent": status.threshold_percent,
                "is_alert": status.is_alert,
                "last_event": status.last_event.model_dump()
                if status.last_event
                else None,
                "station_id": station_id,
                "timestamp": status.timestamp.isoformat(),
            },
        }
    except Exception as e:
        logger.error(f"Error getting ramp rate status: {e}")
        return {
            "status": "success",
            "data": {
                "current_ramp_rate_percent": 0.0,
                "threshold_percent": 30.0,
                "is_alert": False,
                "last_event": None,
                "station_id": station_id,
                "timestamp": datetime.now(UTC).isoformat(),
            },
        }


@router.get("/ramp-rate/events", response_model=dict)
async def get_ramp_rate_events(
    limit: int = Query(default=10, ge=1, le=100, description="Number of events"),
):
    """
    Get recent ramp rate events.

    Returns a list of detected rapid irradiance change events.
    These events indicate cloud shadow passages or sudden weather changes.
    """
    try:
        events = ramp_rate_service.get_recent_events(limit=limit)

        return {
            "status": "success",
            "data": {
                "events": [e.model_dump() for e in events],
                "count": len(events),
                "timestamp": datetime.now(UTC).isoformat(),
            },
        }
    except Exception as e:
        logger.error(f"Error getting ramp rate events: {e}")
        return {
            "status": "success",
            "data": {
                "events": [],
                "count": 0,
                "timestamp": datetime.now(UTC).isoformat(),
            },
        }


@router.get("/events", response_model=dict)
async def get_weather_events(
    start_date: datetime | None = Query(None, description="Start date"),
    end_date: datetime | None = Query(None, description="End date"),
    event_type: str | None = Query(
        None, description="Event type (storm, heavy_rain, cloud_event)"
    ),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum events"),
):
    """
    Get historical weather events for analysis and learning.

    Returns logged weather events that can be used for:
    - Post-event analysis
    - Model retraining
    - Performance review
    """
    if start_date is None:
        start_date = datetime.now(UTC) - timedelta(days=30)
    if end_date is None:
        end_date = datetime.now(UTC)

    # In production, this would query the weather_events table
    # For now, return simulated data structure
    events: list[WeatherEventLog] = []

    return {
        "status": "success",
        "data": {
            "events": [e.model_dump() for e in events],
            "count": len(events),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        },
    }


@router.get("/clear-sky", response_model=dict)
async def get_clear_sky_irradiance(
    latitude: float = Query(default=13.7563, description="Location latitude"),
    longitude: float = Query(default=100.5018, description="Location longitude"),
    altitude: float = Query(default=0, description="Altitude in meters"),
    timestamp: datetime | None = Query(None, description="Time for calculation"),
):
    """
    Calculate theoretical clear sky irradiance.

    Returns the expected solar irradiance under clear sky conditions.
    Used as reference for calculating clearness index.
    """
    if timestamp is None:
        timestamp = datetime.now(UTC)

    try:
        clear_sky = weather_service.calculate_clear_sky_irradiance(
            latitude=latitude,
            longitude=longitude,
            timestamp=timestamp,
            altitude=altitude,
        )

        return {
            "status": "success",
            "data": {
                "clear_sky_irradiance": round(clear_sky, 2),
                "unit": "W/m²",
                "latitude": latitude,
                "longitude": longitude,
                "altitude": altitude,
                "timestamp": timestamp.isoformat(),
            },
        }
    except Exception as e:
        logger.error(f"Error calculating clear sky irradiance: {e}")
        return {
            "status": "error",
            "message": str(e),
        }


@router.get("/uncertainty-factors", response_model=dict)
async def get_uncertainty_factors():
    """
    Get uncertainty multipliers for different weather conditions.

    These factors are used to widen confidence intervals
    during adverse weather conditions.
    """
    return {
        "status": "success",
        "data": {
            "factors": {
                "clear": 1.0,
                "partly_cloudy": 1.5,
                "cloudy": 2.0,
                "rainy": 3.0,
                "storm": 5.0,
            },
            "description": "Multipliers applied to forecast uncertainty bands",
        },
    }


@router.post("/classify", response_model=dict)
async def classify_weather(
    clearness_index: float | None = Query(
        None, ge=0, le=1.5, description="Clearness index (measured/clear_sky)"
    ),
    precipitation_mm: float = Query(default=0, ge=0, description="Precipitation in mm"),
    wind_speed_kmh: float = Query(default=0, ge=0, description="Wind speed in km/h"),
    has_storm_alert: bool = Query(default=False, description="Storm alert active"),
):
    """
    Classify weather condition from input parameters.

    Useful for testing weather classification logic
    or when direct sensor data is available.
    """
    condition = weather_service.classify_weather(
        clearness_index=clearness_index,
        precipitation_mm=precipitation_mm,
        wind_speed_kmh=wind_speed_kmh,
        has_storm_alert=has_storm_alert,
    )

    return {
        "status": "success",
        "data": {
            "condition": condition.value,
            "inputs": {
                "clearness_index": clearness_index,
                "precipitation_mm": precipitation_mm,
                "wind_speed_kmh": wind_speed_kmh,
                "has_storm_alert": has_storm_alert,
            },
            "timestamp": datetime.now(UTC).isoformat(),
        },
    }
