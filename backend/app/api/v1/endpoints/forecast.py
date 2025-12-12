"""
Forecast endpoints for solar power and voltage prediction.

Includes Redis caching for improved performance.
Authentication is controlled by AUTH_ENABLED setting.
"""

import logging
import time
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import get_cache
from app.core.security import CurrentUser, get_current_user, require_roles
from app.db.session import get_db
from app.ml import get_solar_inference, get_voltage_inference

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Request/Response Models
# =============================================================================


class SolarFeatures(BaseModel):
    """Solar measurement features for prediction."""

    pyrano1: float = Field(..., ge=0, le=1500, description="Irradiance sensor 1 (W/m²)")
    pyrano2: float = Field(..., ge=0, le=1500, description="Irradiance sensor 2 (W/m²)")
    pvtemp1: float = Field(..., ge=-10, le=100, description="PV temp sensor 1 (°C)")
    pvtemp2: float = Field(..., ge=-10, le=100, description="PV temp sensor 2 (°C)")
    ambtemp: float = Field(..., ge=-10, le=60, description="Ambient temperature (°C)")
    windspeed: float = Field(..., ge=0, le=50, description="Wind speed (m/s)")


class SolarForecastRequest(BaseModel):
    """Request model for solar power forecast."""

    timestamp: datetime
    station_id: str = "POC_STATION_1"
    horizon_minutes: int = Field(default=60, ge=5, le=1440)
    features: SolarFeatures


class SolarPrediction(BaseModel):
    """Solar power prediction result."""

    power_kw: float
    confidence_lower: float
    confidence_upper: float


class SolarForecastResponse(BaseModel):
    """Response model for solar power forecast."""

    status: str
    data: dict[str, Any]
    meta: dict[str, Any]


class VoltageForecastRequest(BaseModel):
    """Request model for voltage prediction."""

    timestamp: datetime
    prosumer_ids: list[str]
    horizon_minutes: int = Field(default=15, ge=5, le=60)


class VoltagePrediction(BaseModel):
    """Voltage prediction for a single prosumer."""

    prosumer_id: str
    phase: str
    predicted_voltage: float
    confidence_lower: float
    confidence_upper: float
    status: str  # normal, warning, critical
    violation_probability: float


class VoltageForecastResponse(BaseModel):
    """Response model for voltage prediction."""

    status: str
    data: dict[str, Any]
    meta: dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# Endpoints
# =============================================================================


@router.post("/solar", response_model=SolarForecastResponse)
async def predict_solar_power(
    request: SolarForecastRequest,
    current_user: CurrentUser = Depends(
        require_roles(["admin", "operator", "analyst", "api"])
    ),
) -> SolarForecastResponse:
    """
    Predict solar power output.

    Takes environmental measurements and predicts power output for the specified
    horizon. Results are cached in Redis for 5 minutes.

    **Requires roles:** admin, operator, analyst, or api

    **Target Accuracy (per TOR):**
    - MAPE < 10%
    - RMSE < 100 kW
    - R² > 0.95
    """
    logger.info(f"Solar prediction requested by user: {current_user.username}")
    start_time = time.time()

    # Prepare features dict for caching
    features_dict = {
        "pyrano1": request.features.pyrano1,
        "pyrano2": request.features.pyrano2,
        "pvtemp1": request.features.pvtemp1,
        "pvtemp2": request.features.pvtemp2,
        "ambtemp": request.features.ambtemp,
        "windspeed": request.features.windspeed,
    }

    # Try to get from cache first
    cache = await get_cache()
    cached_result = await cache.get_solar_prediction(request.timestamp, features_dict)

    if cached_result:
        prediction_time_ms = int((time.time() - start_time) * 1000)
        return SolarForecastResponse(
            status="success",
            data=cached_result,
            meta={
                "prediction_time_ms": prediction_time_ms,
                "cached": True,
            },
        )

    # Get inference service
    inference = get_solar_inference()

    # Make prediction using trained model with error handling
    try:
        result = inference.predict(
            timestamp=request.timestamp,
            pyrano1=request.features.pyrano1,
            pyrano2=request.features.pyrano2,
            pvtemp1=request.features.pvtemp1,
            pvtemp2=request.features.pvtemp2,
            ambtemp=request.features.ambtemp,
            windspeed=request.features.windspeed,
        )
    except RuntimeError as e:
        logger.error(f"Solar model error: {e}")
        raise HTTPException(
            status_code=503,
            detail="Solar prediction service temporarily unavailable. Model not loaded.",
        )
    except Exception as e:
        logger.error(f"Solar prediction failed: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=503,
            detail="Solar prediction service error. Please retry.",
        )

    prediction_time_ms = int((time.time() - start_time) * 1000)

    prediction = SolarPrediction(
        power_kw=result["power_kw"],
        confidence_lower=result["confidence_lower"],
        confidence_upper=result["confidence_upper"],
    )

    response_data = {
        "timestamp": request.timestamp.isoformat(),
        "station_id": request.station_id,
        "prediction": prediction.model_dump(),
        "model_version": result["model_version"],
        "is_ml_prediction": result["is_ml_prediction"],
    }

    # Cache the result
    await cache.set_solar_prediction(request.timestamp, features_dict, response_data)

    return SolarForecastResponse(
        status="success",
        data=response_data,
        meta={
            "prediction_time_ms": prediction_time_ms,
            "cached": False,
        },
    )


@router.post("/voltage", response_model=VoltageForecastResponse)
async def predict_voltage(
    request: VoltageForecastRequest,
    current_user: CurrentUser = Depends(
        require_roles(["admin", "operator", "analyst", "api"])
    ),
) -> VoltageForecastResponse:
    """
    Predict voltage levels for prosumers.

    Takes prosumer IDs and predicts voltage levels, identifying potential
    violations. Results are cached in Redis for 1 minute per prosumer.

    **Requires roles:** admin, operator, analyst, or api

    **Target Accuracy (per TOR):**
    - MAE < 2V
    - RMSE < 3V
    - R² > 0.90
    """
    logger.info(f"Voltage prediction requested by user: {current_user.username}")
    start_time = time.time()

    # Get cache and inference service
    cache = await get_cache()
    inference = get_voltage_inference()

    # Validate prosumer IDs (per TOR network topology: 7 prosumers)
    from app.ml.voltage_inference import PROSUMER_CONFIG

    valid_ids = set(PROSUMER_CONFIG.keys())
    invalid_ids = [pid for pid in request.prosumer_ids if pid not in valid_ids]
    if invalid_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid prosumer IDs: {invalid_ids}. Valid IDs: {list(valid_ids)}",
        )

    predictions = []
    model_version = "not_loaded"
    cache_hits = 0

    for prosumer_id in request.prosumer_ids:
        # Try cache first
        cached = await cache.get_voltage_prediction(request.timestamp, prosumer_id)

        if cached:
            predictions.append(cached)
            model_version = cached.get("model_version", model_version)
            cache_hits += 1
            continue

        # Make prediction using trained model with error handling
        try:
            result = inference.predict(
                timestamp=request.timestamp,
                prosumer_id=prosumer_id,
            )
        except RuntimeError as e:
            logger.error(f"Voltage model error for {prosumer_id}: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"Voltage prediction service unavailable for {prosumer_id}. Model not loaded.",
            )
        except Exception as e:
            logger.error(
                f"Voltage prediction failed for {prosumer_id}: {type(e).__name__}: {e}"
            )
            raise HTTPException(
                status_code=503,
                detail=f"Voltage prediction error for {prosumer_id}. Please retry.",
            )

        model_version = result["model_version"]

        prediction = VoltagePrediction(
            prosumer_id=prosumer_id,
            phase=result["phase"],
            predicted_voltage=result["predicted_voltage"],
            confidence_lower=result["confidence_lower"],
            confidence_upper=result["confidence_upper"],
            status=result["status"],
            violation_probability=0.1 if result["status"] != "normal" else 0.02,
        )
        prediction_dict = prediction.model_dump()

        # Cache the result
        await cache.set_voltage_prediction(
            request.timestamp, prosumer_id, prediction_dict
        )

        predictions.append(prediction_dict)

    prediction_time_ms = int((time.time() - start_time) * 1000)

    return VoltageForecastResponse(
        status="success",
        data={
            "timestamp": request.timestamp.isoformat(),
            "predictions": predictions,
            "model_version": model_version,
            "is_ml_prediction": inference.is_loaded,
        },
        meta={
            "prediction_time_ms": prediction_time_ms,
            "cache_hits": cache_hits,
            "total_predictions": len(request.prosumer_ids),
        },
    )


@router.get("/solar/history")
async def get_solar_forecast_history(
    station_id: str = Query(default="POC_STATION_1", description="Station ID"),
    limit: int = Query(default=100, ge=1, le=1000, description="Max records to return"),
    offset: int = Query(default=0, ge=0, description="Records to skip for pagination"),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Get historical solar power predictions for a station.

    **Requires authentication**

    Returns predictions with pagination support.
    """
    logger.info(f"Solar history requested by user: {current_user.username}")

    # Query predictions from database
    query = text("""
        SELECT
            time,
            target_id,
            predicted_value,
            confidence_lower,
            confidence_upper,
            actual_value,
            model_version
        FROM predictions
        WHERE model_type = 'solar'
          AND (target_id = :station_id OR target_id IS NULL)
        ORDER BY time DESC
        LIMIT :limit OFFSET :offset
    """)

    result = await db.execute(
        query,
        {"station_id": station_id, "limit": limit, "offset": offset},
    )
    rows = result.fetchall()

    # Count total records
    count_query = text("""
        SELECT COUNT(*) FROM predictions
        WHERE model_type = 'solar'
          AND (target_id = :station_id OR target_id IS NULL)
    """)
    count_result = await db.execute(count_query, {"station_id": station_id})
    total_count = count_result.scalar() or 0

    predictions = [
        {
            "timestamp": row[0].isoformat() if row[0] else None,
            "station_id": row[1] or station_id,
            "predicted_power_kw": row[2],
            "confidence_lower": row[3],
            "confidence_upper": row[4],
            "actual_power_kw": row[5],
            "model_version": row[6],
        }
        for row in rows
    ]

    return {
        "status": "success",
        "data": {
            "station_id": station_id,
            "predictions": predictions,
            "count": len(predictions),
            "total": total_count,
            "limit": limit,
            "offset": offset,
        },
    }


@router.get("/voltage/prosumer/{prosumer_id}")
async def get_voltage_history(
    prosumer_id: str,
    limit: int = Query(default=100, ge=1, le=1000, description="Max records to return"),
    offset: int = Query(default=0, ge=0, description="Records to skip for pagination"),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Get historical voltage predictions for a prosumer.

    **Requires authentication**

    Returns predictions with pagination support.
    """
    logger.info(
        f"Voltage history for {prosumer_id} requested by user: {current_user.username}"
    )

    # Query predictions from database
    query = text("""
        SELECT
            time,
            target_id,
            predicted_value,
            confidence_lower,
            confidence_upper,
            actual_value,
            model_version
        FROM predictions
        WHERE model_type = 'voltage'
          AND target_id = :prosumer_id
        ORDER BY time DESC
        LIMIT :limit OFFSET :offset
    """)

    result = await db.execute(
        query,
        {"prosumer_id": prosumer_id, "limit": limit, "offset": offset},
    )
    rows = result.fetchall()

    # Count total records
    count_query = text("""
        SELECT COUNT(*) FROM predictions
        WHERE model_type = 'voltage'
          AND target_id = :prosumer_id
    """)
    count_result = await db.execute(count_query, {"prosumer_id": prosumer_id})
    total_count = count_result.scalar() or 0

    predictions = [
        {
            "timestamp": row[0].isoformat() if row[0] else None,
            "prosumer_id": row[1],
            "predicted_voltage": row[2],
            "confidence_lower": row[3],
            "confidence_upper": row[4],
            "actual_voltage": row[5],
            "model_version": row[6],
        }
        for row in rows
    ]

    return {
        "status": "success",
        "data": {
            "prosumer_id": prosumer_id,
            "predictions": predictions,
            "count": len(predictions),
            "total": total_count,
            "limit": limit,
            "offset": offset,
        },
    }


@router.get("/cache/stats")
async def get_cache_stats(
    current_user: CurrentUser = Depends(require_roles(["admin"])),
) -> dict[str, Any]:
    """
    Get cache statistics for monitoring.

    **Requires role:** admin

    Returns information about cache hits, misses, and configuration.
    """
    cache = await get_cache()
    stats = await cache.get_stats()
    return {
        "status": "success",
        "data": stats,
    }
