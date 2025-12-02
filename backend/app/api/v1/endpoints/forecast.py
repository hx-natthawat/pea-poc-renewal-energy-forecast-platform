"""
Forecast endpoints for solar power and voltage prediction.
"""

import time
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.ml import get_solar_inference

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
    data: Dict[str, Any]
    meta: Dict[str, Any]


class VoltageForecastRequest(BaseModel):
    """Request model for voltage prediction."""

    timestamp: datetime
    prosumer_ids: List[str]
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
    data: Dict[str, Any]


# =============================================================================
# Endpoints
# =============================================================================


@router.post("/solar", response_model=SolarForecastResponse)
async def predict_solar_power(request: SolarForecastRequest) -> SolarForecastResponse:
    """
    Predict solar power output.

    Takes environmental measurements and predicts power output for the specified
    horizon.

    **Target Accuracy (per TOR):**
    - MAPE < 10%
    - RMSE < 100 kW
    - R² > 0.95
    """
    start_time = time.time()

    # Get inference service
    inference = get_solar_inference()

    # Make prediction using trained model
    result = inference.predict(
        timestamp=request.timestamp,
        pyrano1=request.features.pyrano1,
        pyrano2=request.features.pyrano2,
        pvtemp1=request.features.pvtemp1,
        pvtemp2=request.features.pvtemp2,
        ambtemp=request.features.ambtemp,
        windspeed=request.features.windspeed,
    )

    prediction_time_ms = int((time.time() - start_time) * 1000)

    prediction = SolarPrediction(
        power_kw=result["power_kw"],
        confidence_lower=result["confidence_lower"],
        confidence_upper=result["confidence_upper"],
    )

    return SolarForecastResponse(
        status="success",
        data={
            "timestamp": request.timestamp.isoformat(),
            "station_id": request.station_id,
            "prediction": prediction.model_dump(),
            "model_version": result["model_version"],
            "is_ml_prediction": result["is_ml_prediction"],
        },
        meta={
            "prediction_time_ms": prediction_time_ms,
            "cached": False,
        },
    )


@router.post("/voltage", response_model=VoltageForecastResponse)
async def predict_voltage(request: VoltageForecastRequest) -> VoltageForecastResponse:
    """
    Predict voltage levels for prosumers.

    Takes prosumer IDs and predicts voltage levels, identifying potential
    violations.

    **Target Accuracy (per TOR):**
    - MAE < 2V
    - RMSE < 3V
    - R² > 0.90
    """
    # TODO: Implement actual ML model prediction
    # For now, return mock predictions

    # Prosumer phase mapping
    prosumer_phases = {
        "prosumer1": "A",
        "prosumer2": "A",
        "prosumer3": "A",
        "prosumer4": "B",
        "prosumer5": "B",
        "prosumer6": "B",
        "prosumer7": "C",
    }

    predictions = []
    for prosumer_id in request.prosumer_ids:
        phase = prosumer_phases.get(prosumer_id, "A")

        # Mock voltage around 230V nominal
        import random

        base_voltage = 230.0 + random.uniform(-5, 5)

        prediction = VoltagePrediction(
            prosumer_id=prosumer_id,
            phase=phase,
            predicted_voltage=round(base_voltage, 1),
            confidence_lower=round(base_voltage - 2, 1),
            confidence_upper=round(base_voltage + 2, 1),
            status="normal" if 218 <= base_voltage <= 242 else "warning",
            violation_probability=0.05,
        )
        predictions.append(prediction.model_dump())

    return VoltageForecastResponse(
        status="success",
        data={
            "timestamp": request.timestamp.isoformat(),
            "predictions": predictions,
            "model_version": "mock-v0.1.0",
        },
    )


@router.get("/solar/history")
async def get_solar_forecast_history(
    station_id: str = "POC_STATION_1",
    limit: int = 100,
) -> Dict[str, Any]:
    """
    Get historical solar power predictions for a station.
    """
    # TODO: Implement database query
    return {
        "status": "success",
        "data": {
            "station_id": station_id,
            "predictions": [],
            "count": 0,
        },
    }


@router.get("/voltage/prosumer/{prosumer_id}")
async def get_voltage_history(
    prosumer_id: str,
    limit: int = 100,
) -> Dict[str, Any]:
    """
    Get historical voltage predictions for a prosumer.
    """
    # TODO: Implement database query
    return {
        "status": "success",
        "data": {
            "prosumer_id": prosumer_id,
            "predictions": [],
            "count": 0,
        },
    }
