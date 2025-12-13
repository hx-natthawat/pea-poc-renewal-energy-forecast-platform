"""
DOE (Dynamic Operating Envelope) API Endpoints.

TOR Reference: 7.5.1.6
Provides real-time, time-varying export/import limits for DERs.
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.models.schemas.doe import (
    DOEBatchCalculateRequest,
    DOEBatchCalculateResponse,
    DOECalculateRequest,
    DOECalculateResponse,
    DOEHistoryResponse,
)
from app.services.doe_service import (
    calculate_doe_batch,
    calculate_doe_for_prosumer,
    get_network_topology,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================
# DOE Calculation Endpoints
# ============================================================


@router.post("/calculate", response_model=DOECalculateResponse)
async def calculate_doe(request: DOECalculateRequest) -> DOECalculateResponse:
    """
    Calculate DOE for a single prosumer.

    Returns the maximum export and import power limits
    that maintain all network constraints (voltage, thermal).

    TOR 7.5.1.6 Requirements:
    - Violation rate: < 1%
    - Update frequency: 5-15 minutes
    - Confidence: > 95%
    """
    try:
        response = await calculate_doe_for_prosumer(
            prosumer_id=request.prosumer_id,
            timestamp=request.timestamp,
            horizon_minutes=request.horizon_minutes,
        )
        return response
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"DOE calculation failed: {e}")
        raise HTTPException(status_code=500, detail="DOE calculation failed")


@router.post("/calculate/batch", response_model=DOEBatchCalculateResponse)
async def calculate_doe_batch_endpoint(
    request: DOEBatchCalculateRequest,
) -> DOEBatchCalculateResponse:
    """
    Calculate DOE for multiple prosumers (batch operation).

    Returns DOE limits for all specified prosumers,
    or all prosumers if none specified.
    """
    try:
        response = await calculate_doe_batch(
            prosumer_ids=request.prosumer_ids,
            timestamp=request.timestamp,
            horizon_minutes=request.horizon_minutes,
        )
        return response
    except Exception as e:
        logger.error(f"Batch DOE calculation failed: {e}")
        raise HTTPException(status_code=500, detail="Batch DOE calculation failed")


@router.get("/limits/{prosumer_id}", response_model=DOECalculateResponse)
async def get_current_doe_limits(
    prosumer_id: str,
    horizon_minutes: int = Query(15, ge=5, le=1440),
) -> DOECalculateResponse:
    """
    Get current DOE limits for a prosumer.

    This is a convenience endpoint for real-time monitoring.
    Equivalent to POST /calculate with default parameters.
    """
    try:
        response = await calculate_doe_for_prosumer(
            prosumer_id=prosumer_id,
            timestamp=datetime.now(),
            horizon_minutes=horizon_minutes,
        )
        return response
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get DOE limits: {e}")
        raise HTTPException(status_code=500, detail="Failed to get DOE limits")


@router.get("/limits", response_model=DOEBatchCalculateResponse)
async def get_all_doe_limits(
    horizon_minutes: int = Query(15, ge=5, le=1440),
) -> DOEBatchCalculateResponse:
    """
    Get current DOE limits for all prosumers.

    Returns a snapshot of DOE limits across the entire network.
    Useful for dashboard visualization.
    """
    try:
        response = await calculate_doe_batch(
            prosumer_ids=None,
            timestamp=datetime.now(),
            horizon_minutes=horizon_minutes,
        )
        return response
    except Exception as e:
        logger.error(f"Failed to get all DOE limits: {e}")
        raise HTTPException(status_code=500, detail="Failed to get DOE limits")


# ============================================================
# Network Topology Endpoints
# ============================================================


@router.get("/network/topology")
async def get_topology() -> dict[str, Any]:
    """
    Get network topology for DOE visualization.

    Returns the POC network model including:
    - Transformer specifications
    - Prosumer locations and configurations
    - Operating constraints (voltage, thermal)

    Note: Uses mock GIS data for POC. Replace with actual
    กฟภ. GIS data in production.
    """
    try:
        topology = await get_network_topology()
        return {"status": "success", "data": topology}
    except Exception as e:
        logger.error(f"Failed to get network topology: {e}")
        raise HTTPException(status_code=500, detail="Failed to get network topology")


@router.get("/network/constraints")
async def get_network_constraints() -> dict[str, Any]:
    """
    Get network operating constraints for DOE.

    Returns voltage and thermal limits per TOR specifications.
    """
    return {
        "status": "success",
        "data": {
            "voltage": {
                "nominal_v": 230,
                "upper_limit_v": 242,
                "lower_limit_v": 218,
                "tolerance_pct": 5,
                "standard": "Thailand PEA (±5%)",
            },
            "thermal": {
                "cable_max_current_a": 200,
                "transformer_max_current_a": 72.2,
                "safety_margin_pct": 15,
            },
            "doe": {
                "update_interval_minutes": 15,
                "forecast_horizon_max_minutes": 1440,
                "confidence_level": 0.95,
                "violation_target_pct": 1.0,
            },
        },
    }


# ============================================================
# Status & Metrics Endpoints
# ============================================================


@router.get("/status")
async def get_doe_status() -> dict[str, Any]:
    """
    Get DOE service status and summary metrics.

    Returns current system status and aggregate DOE metrics.
    """
    try:
        # Calculate current DOE for all prosumers
        batch_result = await calculate_doe_batch(
            prosumer_ids=None,
            timestamp=datetime.now(),
            horizon_minutes=15,
        )

        return {
            "status": "success",
            "service": "doe",
            "timestamp": datetime.now().isoformat(),
            "prosumer_count": batch_result.prosumer_count,
            "summary": batch_result.summary,
            "tor_compliance": {
                "function": "7.5.1.6 DOE",
                "status": "SIMULATION",
                "note": "Using mock GIS data. Replace with actual network model for production.",
                "targets": {
                    "violation_rate": "< 1%",
                    "update_frequency": "5-15 minutes",
                    "confidence": "> 95%",
                },
            },
        }
    except Exception as e:
        logger.error(f"Failed to get DOE status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get DOE status")


@router.get("/prosumers")
async def list_prosumers() -> dict[str, Any]:
    """
    List all prosumers available for DOE calculation.

    Returns the 7-prosumer POC network configuration.
    """
    from app.services.doe_service import POC_PROSUMERS

    return {
        "status": "success",
        "count": len(POC_PROSUMERS),
        "data": [
            {
                "id": p.id,
                "name": p.name,
                "phase": p.phase,
                "position": p.position,
                "position_label": ["near", "mid", "far"][p.position - 1],
                "has_pv": p.has_pv,
                "has_ev": p.has_ev,
                "pv_capacity_kw": p.pv_capacity_kw,
                "voltage_risk": "HIGH"
                if p.position == 3
                else ("MEDIUM" if p.position == 2 else "LOW"),
            }
            for p in POC_PROSUMERS
        ],
    }


# ============================================================
# Historical Data Endpoints (Placeholder)
# ============================================================


@router.get("/history/{prosumer_id}", response_model=DOEHistoryResponse)
async def get_doe_history(
    prosumer_id: str,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    limit: int = Query(100, ge=1, le=1000),
) -> DOEHistoryResponse:
    """
    Get historical DOE limits for a prosumer.

    Note: This is a placeholder. In production, DOE limits
    would be stored in TimescaleDB doe_limits hypertable.
    """
    # For now, return current DOE as single history point
    current_doe = await calculate_doe_for_prosumer(
        prosumer_id=prosumer_id,
        timestamp=datetime.now(),
        horizon_minutes=15,
    )

    now = datetime.now()

    return DOEHistoryResponse(
        prosumer_id=prosumer_id,
        start_time=start_time or now,
        end_time=end_time or now,
        count=1,
        data=[current_doe.data],
    )
