"""
Data ingestion endpoints for sensor and meter data.
"""

from datetime import datetime
from typing import Dict, Any, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()


# =============================================================================
# Request Models
# =============================================================================


class SolarMeasurement(BaseModel):
    """Solar measurement data point."""

    timestamp: datetime
    station_id: str = "POC_STATION_1"
    pvtemp1: float = Field(..., ge=-10, le=100)
    pvtemp2: float = Field(..., ge=-10, le=100)
    ambtemp: float = Field(..., ge=-10, le=60)
    pyrano1: float = Field(..., ge=0, le=1500)
    pyrano2: float = Field(..., ge=0, le=1500)
    windspeed: float = Field(..., ge=0, le=50)
    power_kw: float = Field(..., ge=0)


class SinglePhaseMeasurement(BaseModel):
    """Single-phase meter measurement."""

    timestamp: datetime
    prosumer_id: str
    active_power: float
    reactive_power: float
    voltage: float = Field(..., ge=0, le=300)
    current: float = Field(..., ge=0)


class ThreePhaseMeasurement(BaseModel):
    """Three-phase meter measurement."""

    timestamp: datetime
    meter_id: str = "TX_METER_01"
    phase_a: Dict[str, float]
    phase_b: Dict[str, float]
    phase_c: Dict[str, float]
    total_power: float


class BatchIngestRequest(BaseModel):
    """Batch data ingestion request."""

    data: List[Dict[str, Any]]


# =============================================================================
# Endpoints
# =============================================================================


@router.post("/solar")
async def ingest_solar_measurement(measurement: SolarMeasurement) -> Dict[str, Any]:
    """
    Ingest a single solar measurement data point.
    """
    # TODO: Implement database insertion
    return {
        "status": "success",
        "message": "Solar measurement ingested",
        "data": {
            "timestamp": measurement.timestamp.isoformat(),
            "station_id": measurement.station_id,
        },
    }


@router.post("/solar/batch")
async def ingest_solar_batch(request: BatchIngestRequest) -> Dict[str, Any]:
    """
    Ingest multiple solar measurements in batch.
    """
    # TODO: Implement batch database insertion
    return {
        "status": "success",
        "message": f"Ingested {len(request.data)} solar measurements",
        "count": len(request.data),
    }


@router.post("/meter/single-phase")
async def ingest_single_phase_measurement(
    measurement: SinglePhaseMeasurement,
) -> Dict[str, Any]:
    """
    Ingest a single-phase meter measurement.
    """
    # TODO: Implement database insertion
    return {
        "status": "success",
        "message": "Single-phase measurement ingested",
        "data": {
            "timestamp": measurement.timestamp.isoformat(),
            "prosumer_id": measurement.prosumer_id,
        },
    }


@router.post("/meter/three-phase")
async def ingest_three_phase_measurement(
    measurement: ThreePhaseMeasurement,
) -> Dict[str, Any]:
    """
    Ingest a three-phase meter measurement.
    """
    # TODO: Implement database insertion
    return {
        "status": "success",
        "message": "Three-phase measurement ingested",
        "data": {
            "timestamp": measurement.timestamp.isoformat(),
            "meter_id": measurement.meter_id,
        },
    }


@router.get("/stats")
async def get_data_statistics() -> Dict[str, Any]:
    """
    Get statistics about ingested data.
    """
    # TODO: Implement actual statistics query
    return {
        "status": "success",
        "data": {
            "solar_measurements": {
                "total_count": 0,
                "stations": [],
                "date_range": None,
            },
            "single_phase_meters": {
                "total_count": 0,
                "prosumers": [],
                "date_range": None,
            },
            "three_phase_meters": {
                "total_count": 0,
                "meters": [],
                "date_range": None,
            },
        },
    }
