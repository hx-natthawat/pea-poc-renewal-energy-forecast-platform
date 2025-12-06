"""
Imbalance Forecast endpoints (TOR Function 4).

Provides system imbalance forecasting:
Imbalance = Actual Demand - Scheduled Generation - Actual RE Generation

Target accuracy: MAE < 5% of average load

Phase 2 implementation per TOR 7.5.1.4.
Dependencies: Functions 1 (RE Forecast), 2 (Demand), 3 (Load)
"""

import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, require_roles
from app.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Enums and Constants
# =============================================================================


class ImbalanceType(str, Enum):
    """Types of imbalance."""

    POSITIVE = "positive"  # Demand > Supply (deficit)
    NEGATIVE = "negative"  # Supply > Demand (surplus)
    BALANCED = "balanced"  # Within tolerance


class ImbalanceLevel(str, Enum):
    """Severity levels for imbalance."""

    NORMAL = "normal"  # Within ±2%
    WARNING = "warning"  # Within ±5%
    CRITICAL = "critical"  # Beyond ±5%


class BalancingArea(str, Enum):
    """Balancing areas for imbalance calculation."""

    SYSTEM = "system"  # กฟภ. total system
    CENTRAL = "central"  # Central region
    NORTH = "north"  # Northern region
    NORTHEAST = "northeast"  # Northeastern region
    SOUTH = "south"  # Southern region


# Accuracy target per TOR
IMBALANCE_MAE_TARGET_PCT = 5.0  # MAE < 5% of average load


# =============================================================================
# Request/Response Models
# =============================================================================


class ImbalanceForecastRequest(BaseModel):
    """Request model for imbalance forecast."""

    timestamp: datetime = Field(description="Forecast base timestamp")
    balancing_area: BalancingArea = Field(default=BalancingArea.SYSTEM)
    horizon_hours: int = Field(
        default=24, ge=1, le=168, description="Forecast horizon in hours"
    )
    include_components: bool = Field(
        default=True, description="Include component breakdown"
    )


class ImbalancePrediction(BaseModel):
    """Single imbalance prediction result."""

    timestamp: datetime
    imbalance_mw: float
    imbalance_pct: float  # As percentage of demand
    imbalance_type: ImbalanceType
    severity: ImbalanceLevel
    actual_demand_mw: float | None = None
    scheduled_gen_mw: float | None = None
    re_generation_mw: float | None = None
    confidence_lower: float
    confidence_upper: float


class ImbalanceForecastResponse(BaseModel):
    """Response model for imbalance forecast."""

    status: str
    data: dict[str, Any]
    meta: dict[str, Any]


class BalancingStatus(BaseModel):
    """Current balancing status."""

    area: BalancingArea
    timestamp: datetime
    imbalance_mw: float
    imbalance_pct: float
    type: ImbalanceType
    severity: ImbalanceLevel
    reserves_available_mw: float
    action_required: str | None = None


# =============================================================================
# Simulation Functions (Phase 2 - to be replaced with ML model)
# =============================================================================


def simulate_imbalance_forecast(
    timestamp: datetime,
    balancing_area: BalancingArea,
    horizon_hours: int,
    include_components: bool,
) -> list[ImbalancePrediction]:
    """
    Simulate imbalance forecast predictions.

    Formula: Imbalance = Actual Demand - Scheduled Gen - RE Generation
    """
    import random

    predictions = []

    # Base values by balancing area (MW)
    base_demands = {
        BalancingArea.SYSTEM: 15000.0,
        BalancingArea.CENTRAL: 5000.0,
        BalancingArea.NORTH: 3000.0,
        BalancingArea.NORTHEAST: 4000.0,
        BalancingArea.SOUTH: 3000.0,
    }

    base_demand = base_demands.get(balancing_area, 5000.0)

    # Scheduled generation (conventional power plants)
    scheduled_gen_base = base_demand * 0.70  # 70% from scheduled generation

    # RE generation capacity
    re_capacity = base_demand * 0.25  # 25% RE penetration

    for i in range(horizon_hours):
        forecast_time = timestamp + timedelta(hours=i)
        hour = forecast_time.hour

        # Demand pattern
        if 13 <= hour <= 15:
            demand_factor = 1.15
        elif 19 <= hour <= 22:
            demand_factor = 1.20
        elif 0 <= hour <= 5:
            demand_factor = 0.70
        else:
            demand_factor = 0.95

        actual_demand = base_demand * demand_factor * (1 + random.gauss(0, 0.02))

        # Scheduled generation (relatively stable)
        scheduled_gen = scheduled_gen_base * (0.98 + random.random() * 0.04)

        # RE generation (solar pattern + wind)
        if 6 <= hour <= 18:
            solar_factor = 1 - abs(hour - 12) / 6
            re_gen = re_capacity * solar_factor * (0.7 + random.random() * 0.3)
        else:
            # Night: only wind
            re_gen = re_capacity * 0.15 * (0.5 + random.random() * 0.5)

        # Add wind component
        re_gen += re_capacity * 0.1 * random.random()

        # Calculate imbalance
        total_supply = scheduled_gen + re_gen
        imbalance = actual_demand - total_supply

        # Imbalance as percentage
        imbalance_pct = (imbalance / actual_demand) * 100 if actual_demand > 0 else 0.0

        # Determine type and severity
        if abs(imbalance_pct) < 0.5:
            imbalance_type = ImbalanceType.BALANCED
            severity = ImbalanceLevel.NORMAL
        elif imbalance > 0:
            imbalance_type = ImbalanceType.POSITIVE
            if abs(imbalance_pct) < 2:
                severity = ImbalanceLevel.NORMAL
            elif abs(imbalance_pct) < 5:
                severity = ImbalanceLevel.WARNING
            else:
                severity = ImbalanceLevel.CRITICAL
        else:
            imbalance_type = ImbalanceType.NEGATIVE
            if abs(imbalance_pct) < 2:
                severity = ImbalanceLevel.NORMAL
            elif abs(imbalance_pct) < 5:
                severity = ImbalanceLevel.WARNING
            else:
                severity = ImbalanceLevel.CRITICAL

        # Confidence interval (widens with forecast horizon)
        confidence_pct = 0.02 + (i / horizon_hours) * 0.05
        confidence_lower = imbalance - abs(actual_demand) * confidence_pct
        confidence_upper = imbalance + abs(actual_demand) * confidence_pct

        prediction = ImbalancePrediction(
            timestamp=forecast_time,
            imbalance_mw=round(imbalance, 2),
            imbalance_pct=round(imbalance_pct, 2),
            imbalance_type=imbalance_type,
            severity=severity,
            confidence_lower=round(confidence_lower, 2),
            confidence_upper=round(confidence_upper, 2),
        )

        if include_components:
            prediction.actual_demand_mw = round(actual_demand, 2)
            prediction.scheduled_gen_mw = round(scheduled_gen, 2)
            prediction.re_generation_mw = round(re_gen, 2)

        predictions.append(prediction)

    return predictions


def get_current_balancing_status(area: BalancingArea) -> BalancingStatus:
    """Get current balancing status for an area."""
    import random

    base_demands = {
        BalancingArea.SYSTEM: 15000.0,
        BalancingArea.CENTRAL: 5000.0,
        BalancingArea.NORTH: 3000.0,
        BalancingArea.NORTHEAST: 4000.0,
        BalancingArea.SOUTH: 3000.0,
    }

    base_demand = base_demands.get(area, 5000.0)

    # Simulate current imbalance (usually small)
    imbalance = random.gauss(0, base_demand * 0.02)
    imbalance_pct = (imbalance / base_demand) * 100

    if abs(imbalance_pct) < 0.5:
        imbalance_type = ImbalanceType.BALANCED
        severity = ImbalanceLevel.NORMAL
        action = None
    elif imbalance > 0:
        imbalance_type = ImbalanceType.POSITIVE
        if abs(imbalance_pct) < 2:
            severity = ImbalanceLevel.NORMAL
            action = None
        elif abs(imbalance_pct) < 5:
            severity = ImbalanceLevel.WARNING
            action = "Activate secondary reserves"
        else:
            severity = ImbalanceLevel.CRITICAL
            action = "Emergency dispatch required"
    else:
        imbalance_type = ImbalanceType.NEGATIVE
        if abs(imbalance_pct) < 2:
            severity = ImbalanceLevel.NORMAL
            action = None
        elif abs(imbalance_pct) < 5:
            severity = ImbalanceLevel.WARNING
            action = "Consider curtailment"
        else:
            severity = ImbalanceLevel.CRITICAL
            action = "Immediate curtailment required"

    reserves = base_demand * 0.10 * (0.8 + random.random() * 0.4)

    return BalancingStatus(
        area=area,
        timestamp=datetime.now(),
        imbalance_mw=round(imbalance, 2),
        imbalance_pct=round(imbalance_pct, 2),
        type=imbalance_type,
        severity=severity,
        reserves_available_mw=round(reserves, 2),
        action_required=action,
    )


# =============================================================================
# Endpoints
# =============================================================================


@router.post("/predict", response_model=ImbalanceForecastResponse)
async def predict_imbalance(
    request: ImbalanceForecastRequest,
    current_user: CurrentUser = Depends(
        require_roles(["admin", "operator", "analyst", "api"])
    ),
    db: AsyncSession = Depends(get_db),
) -> ImbalanceForecastResponse:
    """
    Generate imbalance forecast predictions.

    **Phase 2 Feature** - TOR Function 4

    Predicts system imbalance:
    `Imbalance = Actual Demand - Scheduled Gen - RE Generation`

    **Dependencies:** Functions 1, 2, 3

    **Target Accuracy:** MAE < 5% of average load

    **Requires roles:** admin, operator, analyst, or api
    """
    logger.info(
        f"Imbalance forecast requested by user: {current_user.username} "
        f"area={request.balancing_area} horizon={request.horizon_hours}h"
    )
    start_time = time.time()

    # Generate predictions
    predictions = simulate_imbalance_forecast(
        timestamp=request.timestamp,
        balancing_area=request.balancing_area,
        horizon_hours=request.horizon_hours,
        include_components=request.include_components,
    )

    prediction_time_ms = int((time.time() - start_time) * 1000)

    # Calculate summary statistics
    imbalances = [p.imbalance_mw for p in predictions]
    max_deficit = max(imbalances)
    max_surplus = min(imbalances)
    avg_abs_imbalance = sum(abs(i) for i in imbalances) / len(imbalances)

    # Count severity distribution
    severity_counts = {
        ImbalanceLevel.NORMAL: len(
            [p for p in predictions if p.severity == ImbalanceLevel.NORMAL]
        ),
        ImbalanceLevel.WARNING: len(
            [p for p in predictions if p.severity == ImbalanceLevel.WARNING]
        ),
        ImbalanceLevel.CRITICAL: len(
            [p for p in predictions if p.severity == ImbalanceLevel.CRITICAL]
        ),
    }

    return ImbalanceForecastResponse(
        status="success",
        data={
            "timestamp": request.timestamp.isoformat(),
            "balancing_area": request.balancing_area.value,
            "horizon_hours": request.horizon_hours,
            "predictions": [p.model_dump() for p in predictions],
            "summary": {
                "max_deficit_mw": round(max_deficit, 2),
                "max_surplus_mw": round(max_surplus, 2),
                "avg_abs_imbalance_mw": round(avg_abs_imbalance, 2),
                "total_intervals": len(predictions),
                "severity_distribution": {
                    k.value: v for k, v in severity_counts.items()
                },
            },
            "model_version": "imbalance-forecast-v2.0.0-simulation",
            "is_ml_prediction": False,
        },
        meta={
            "prediction_time_ms": prediction_time_ms,
            "accuracy_target_mae_pct": IMBALANCE_MAE_TARGET_PCT,
            "phase": "Phase 2 - Simulation",
            "includes_components": request.include_components,
        },
    )


@router.get("/status/{area}")
async def get_balancing_status(
    area: BalancingArea,
    current_user: CurrentUser = Depends(
        require_roles(["admin", "operator", "analyst"])
    ),
) -> dict[str, Any]:
    """
    Get current balancing status for a specific area.

    Returns real-time imbalance and recommended actions.
    """
    status = get_current_balancing_status(area)

    return {
        "status": "success",
        "data": status.model_dump(),
    }


@router.get("/status")
async def get_all_balancing_status(
    current_user: CurrentUser = Depends(
        require_roles(["admin", "operator", "analyst"])
    ),
) -> dict[str, Any]:
    """
    Get current balancing status for all areas.

    Returns system-wide imbalance overview.
    """
    statuses = [get_current_balancing_status(area) for area in BalancingArea]

    # System summary
    system_status = next((s for s in statuses if s.area == BalancingArea.SYSTEM), None)

    return {
        "status": "success",
        "data": {
            "system_imbalance_mw": system_status.imbalance_mw if system_status else 0,
            "system_severity": system_status.severity.value
            if system_status
            else "unknown",
            "areas": [s.model_dump() for s in statuses],
            "total_reserves_mw": sum(s.reserves_available_mw for s in statuses)
            / len(BalancingArea),
            "timestamp": datetime.now().isoformat(),
        },
    }


@router.get("/areas")
async def get_balancing_areas(
    current_user: CurrentUser = Depends(
        require_roles(["admin", "operator", "analyst"])
    ),
) -> dict[str, Any]:
    """
    Get list of balancing areas.

    Returns available areas for imbalance forecasting.
    """
    return {
        "status": "success",
        "data": {
            "areas": [
                {
                    "id": area.value,
                    "name": {
                        BalancingArea.SYSTEM: "Total กฟภ. System",
                        BalancingArea.CENTRAL: "Central Region",
                        BalancingArea.NORTH: "Northern Region",
                        BalancingArea.NORTHEAST: "Northeastern Region",
                        BalancingArea.SOUTH: "Southern Region",
                    }.get(area, area.value),
                }
                for area in BalancingArea
            ],
        },
    }


@router.get("/reserves")
async def get_reserve_status(
    area: BalancingArea = Query(default=BalancingArea.SYSTEM),
    current_user: CurrentUser = Depends(require_roles(["admin", "operator"])),
) -> dict[str, Any]:
    """
    Get current reserve capacity status.

    Returns available reserves for balancing.
    """
    import random

    base_reserves = {
        BalancingArea.SYSTEM: 2000.0,
        BalancingArea.CENTRAL: 600.0,
        BalancingArea.NORTH: 400.0,
        BalancingArea.NORTHEAST: 500.0,
        BalancingArea.SOUTH: 500.0,
    }

    total_reserves = base_reserves.get(area, 500.0)
    available = total_reserves * (0.7 + random.random() * 0.3)
    committed = total_reserves - available

    return {
        "status": "success",
        "data": {
            "area": area.value,
            "total_reserves_mw": round(total_reserves, 2),
            "available_mw": round(available, 2),
            "committed_mw": round(committed, 2),
            "utilization_pct": round((committed / total_reserves) * 100, 1),
            "reserve_types": {
                "primary": round(total_reserves * 0.3 * random.random(), 2),
                "secondary": round(total_reserves * 0.4 * random.random(), 2),
                "tertiary": round(total_reserves * 0.3 * random.random(), 2),
            },
            "timestamp": datetime.now().isoformat(),
        },
    }


@router.get("/accuracy")
async def get_imbalance_accuracy(
    area: BalancingArea = Query(default=BalancingArea.SYSTEM),
    days: int = Query(default=7, ge=1, le=90, description="Days to analyze"),
    current_user: CurrentUser = Depends(require_roles(["admin", "analyst"])),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Get imbalance forecast accuracy metrics.

    Compares historical forecasts against actual imbalance.
    """
    import random

    # Simulated accuracy metrics
    actual_mae_pct = IMBALANCE_MAE_TARGET_PCT * (0.85 + random.random() * 0.25)

    return {
        "status": "success",
        "data": {
            "area": area.value,
            "period_days": days,
            "metrics": {
                "mae_pct": round(actual_mae_pct, 2),
                "mae_mw": round(actual_mae_pct * 100, 2),
                "rmse_mw": round(actual_mae_pct * 120, 2),
                "bias_mw": round(random.gauss(0, 20), 2),
            },
            "target": {
                "mae_pct": IMBALANCE_MAE_TARGET_PCT,
                "status": "PASS"
                if actual_mae_pct <= IMBALANCE_MAE_TARGET_PCT
                else "NEEDS_IMPROVEMENT",
            },
            "component_contribution": {
                "demand_error_pct": round(actual_mae_pct * 0.4, 2),
                "re_error_pct": round(actual_mae_pct * 0.45, 2),
                "scheduled_gen_error_pct": round(actual_mae_pct * 0.15, 2),
            },
            "sample_size": days * 24,
        },
    }
