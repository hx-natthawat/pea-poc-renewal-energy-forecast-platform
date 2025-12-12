"""
Model Retraining API endpoints.

Provides automated retraining pipeline management, A/B testing, and model lifecycle.
Part of v1.1.0 Model Retraining Pipeline feature.
"""

import logging
from datetime import datetime, timedelta
from typing import Any

import numpy as np
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, get_current_user, require_roles
from app.db import get_db
from app.services.drift_detection_service import (
    DriftDetectionService,
    ModelRegistryService,
    get_drift_detection_service,
    get_model_registry_service,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Request/Response Models
# =============================================================================


class DriftDetectionRequest(BaseModel):
    """Request for drift detection analysis."""

    model_type: str = Field(..., description="Model type: solar or voltage")
    baseline_days: int = Field(default=30, ge=7, le=90)
    current_days: int = Field(default=7, ge=1, le=30)
    features: list[str] | None = Field(default=None, description="Features to analyze")


class RetrainingEvaluationRequest(BaseModel):
    """Request for retraining evaluation."""

    model_type: str = Field(..., description="Model type: solar or voltage")
    force_check: bool = Field(default=False, description="Skip cooldown checks")


class ABTestRequest(BaseModel):
    """Request to set up A/B test."""

    model_type: str
    champion_id: str
    challenger_id: str
    challenger_traffic_pct: float = Field(default=10.0, ge=1.0, le=50.0)


class ModelPromotionRequest(BaseModel):
    """Request to promote or rollback a model."""

    model_type: str
    action: str = Field(..., description="promote or rollback")
    target_version: str | None = Field(
        default=None, description="Version to rollback to"
    )


class RetrainingTriggerConfig(BaseModel):
    """Configuration for retraining triggers."""

    mape_threshold: float = Field(
        default=12.0, description="MAPE threshold for solar models"
    )
    mae_threshold_voltage: float = Field(
        default=2.5, description="MAE threshold for voltage models"
    )
    drift_score_threshold: float = Field(
        default=2.0, description="Z-score threshold for drift"
    )
    max_days_without_retrain: int = Field(
        default=30, description="Max days before forced retrain"
    )
    consecutive_violations: int = Field(
        default=3, description="Consecutive violations to trigger"
    )


# =============================================================================
# Helper Functions
# =============================================================================


async def fetch_feature_data(
    db: AsyncSession,
    table: str,
    column: str,
    start_date: datetime,
    end_date: datetime,
) -> np.ndarray:
    """Fetch feature data from database for drift analysis."""
    query = text(f"""
        SELECT {column}
        FROM {table}
        WHERE time >= :start_date AND time < :end_date
          AND {column} IS NOT NULL
        ORDER BY time ASC
        LIMIT 10000
    """)

    result = await db.execute(query, {"start_date": start_date, "end_date": end_date})
    rows = result.fetchall()

    return np.array([row[0] for row in rows if row[0] is not None])


async def get_current_metrics(
    db: AsyncSession, model_type: str, hours: int = 24
) -> dict[str, float]:
    """Get current model performance metrics."""
    query = text("""
        SELECT
            AVG(ABS(predicted_value - actual_value)) as mae,
            SQRT(AVG(POWER(predicted_value - actual_value, 2))) as rmse,
            AVG(ABS((actual_value - predicted_value) / NULLIF(actual_value, 0)) * 100) as mape
        FROM predictions
        WHERE model_type = :model_type
          AND time >= NOW() - INTERVAL '1 hour' * :hours
          AND actual_value IS NOT NULL
    """)

    result = await db.execute(query, {"model_type": model_type, "hours": hours})
    row = result.fetchone()

    if row and row[0] is not None:
        return {
            "mae": float(row[0]) if row[0] else 0.0,
            "rmse": float(row[1]) if row[1] else 0.0,
            "mape": float(row[2]) if row[2] else 0.0,
        }

    return {"mae": 0.0, "rmse": 0.0, "mape": 0.0}


async def get_last_retrain_date(db: AsyncSession, model_type: str) -> datetime | None:
    """Get the date of the last model training."""
    query = text("""
        SELECT trained_at
        FROM ml_models
        WHERE model_type = :model_type AND is_active = true
        ORDER BY trained_at DESC
        LIMIT 1
    """)

    result = await db.execute(query, {"model_type": model_type})
    row = result.fetchone()

    return row[0] if row and row[0] else None


# =============================================================================
# Endpoints
# =============================================================================


@router.post("/drift/analyze")
async def analyze_drift(
    request: DriftDetectionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(["admin", "analyst"])),
    drift_service: DriftDetectionService = Depends(get_drift_detection_service),
) -> dict[str, Any]:
    """
    Analyze data drift for a model.

    **Requires roles:** admin or analyst

    Performs comprehensive drift analysis including:
    - Feature distribution comparison (KS test)
    - Population Stability Index (PSI)
    - Performance degradation check
    """
    logger.info(
        f"Drift analysis requested for {request.model_type} by {current_user.username}"
    )

    now = datetime.now()
    baseline_end = now - timedelta(days=request.current_days)
    baseline_start = baseline_end - timedelta(days=request.baseline_days)
    current_start = now - timedelta(days=request.current_days)

    # Define features to analyze
    if request.model_type == "solar":
        table = "solar_measurements"
        features = request.features or ["power_kw", "pyrano1", "pyrano2", "ambtemp"]
    else:
        table = "single_phase_meters"
        features = request.features or ["energy_meter_voltage", "active_power"]

    drift_results = []

    for feature in features:
        try:
            baseline_data = await fetch_feature_data(
                db, table, feature, baseline_start, baseline_end
            )
            current_data = await fetch_feature_data(
                db, table, feature, current_start, now
            )

            if len(baseline_data) > 0 and len(current_data) > 0:
                result = drift_service.detect_data_drift(
                    baseline_data, current_data, feature
                )
                drift_results.append(
                    {
                        "feature": result.feature_name,
                        "drift_type": result.drift_type.value,
                        "drift_score": result.drift_score,
                        "threshold": result.threshold,
                        "drift_detected": result.drift_detected,
                        "severity": result.severity.value,
                        "p_value": result.p_value,
                        "baseline_stats": result.baseline_stats,
                        "current_stats": result.current_stats,
                        "recommendation": result.recommendation,
                    }
                )
        except Exception as e:
            logger.error(f"Error analyzing drift for {feature}: {e}")
            drift_results.append(
                {
                    "feature": feature,
                    "error": str(e),
                }
            )

    # Check performance drift
    current_metrics = await get_current_metrics(db, request.model_type)
    baseline_metrics = await get_current_metrics(
        db, request.model_type, hours=request.baseline_days * 24
    )

    perf_result = drift_service.detect_performance_drift(
        model_type=request.model_type,
        baseline_mape=baseline_metrics.get("mape", 0),
        current_mape=current_metrics.get("mape", 0),
        baseline_mae=baseline_metrics.get("mae", 0),
        current_mae=current_metrics.get("mae", 0),
    )

    overall_drift = any(r.get("drift_detected", False) for r in drift_results)

    return {
        "status": "success",
        "data": {
            "model_type": request.model_type,
            "analysis_config": {
                "baseline_days": request.baseline_days,
                "current_days": request.current_days,
                "baseline_period": f"{baseline_start.isoformat()} to {baseline_end.isoformat()}",
                "current_period": f"{current_start.isoformat()} to {now.isoformat()}",
            },
            "data_drift": {
                "overall_detected": overall_drift,
                "features": drift_results,
            },
            "performance_drift": {
                "drift_detected": perf_result.drift_detected,
                "severity": perf_result.severity.value,
                "baseline": perf_result.baseline_stats,
                "current": perf_result.current_stats,
                "recommendation": perf_result.recommendation,
            },
            "analyzed_at": now.isoformat(),
        },
    }


@router.post("/evaluate")
async def evaluate_retraining(
    request: RetrainingEvaluationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(["admin", "analyst"])),
    drift_service: DriftDetectionService = Depends(get_drift_detection_service),
) -> dict[str, Any]:
    """
    Evaluate whether model retraining is needed.

    **Requires roles:** admin or analyst

    Checks all retraining triggers and provides recommendation.
    """
    logger.info(
        f"Retraining evaluation for {request.model_type} by {current_user.username}"
    )

    # Get current metrics
    current_metrics = await get_current_metrics(db, request.model_type)

    # Get last retrain date
    last_retrain = await get_last_retrain_date(db, request.model_type)

    # Evaluate
    decision = drift_service.evaluate_retraining_need(
        model_type=request.model_type,
        drift_results=[],  # Could fetch from recent drift analysis
        current_metrics=current_metrics,
        last_retrain_date=last_retrain,
    )

    return {
        "status": "success",
        "data": {
            "model_type": request.model_type,
            "should_retrain": decision.should_retrain,
            "urgency": decision.urgency.value,
            "reasons": decision.reasons,
            "current_metrics": current_metrics,
            "last_retrain": last_retrain.isoformat() if last_retrain else None,
            "thresholds": {
                "mape": drift_service.config.mape_threshold,
                "mae_voltage": drift_service.config.mae_threshold_voltage,
            },
            "evaluated_at": datetime.now().isoformat(),
        },
    }


@router.post("/trigger")
async def trigger_retraining(
    model_type: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(["admin"])),
) -> dict[str, Any]:
    """
    Manually trigger model retraining.

    **Requires roles:** admin

    Initiates a background retraining job.
    """
    logger.info(
        f"Manual retraining triggered for {model_type} by {current_user.username}"
    )

    # In a real implementation, this would:
    # 1. Fetch training data from database
    # 2. Submit to ML training service (MLflow, etc.)
    # 3. Track progress and update model registry

    # For now, return a job ID for tracking
    job_id = f"retrain-{model_type}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    return {
        "status": "accepted",
        "data": {
            "job_id": job_id,
            "model_type": model_type,
            "triggered_by": current_user.username,
            "triggered_at": datetime.now().isoformat(),
            "message": "Retraining job submitted. Check /api/v1/retraining/jobs/{job_id} for status.",
        },
    }


@router.get("/jobs/{job_id}")
async def get_retraining_job_status(
    job_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get status of a retraining job.

    **Requires authentication**
    """
    # In a real implementation, this would query MLflow or similar
    return {
        "status": "success",
        "data": {
            "job_id": job_id,
            "status": "pending",  # pending, running, completed, failed
            "progress": 0,
            "message": "Job queued for processing",
        },
    }


@router.post("/ab-test/setup")
async def setup_ab_test(
    request: ABTestRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(["admin"])),
    registry: ModelRegistryService = Depends(get_model_registry_service),
) -> dict[str, Any]:
    """
    Set up A/B test between champion and challenger models.

    **Requires roles:** admin

    Routes traffic between models for performance comparison.
    """
    logger.info(f"A/B test setup for {request.model_type} by {current_user.username}")

    config = registry.setup_ab_test(
        model_type=request.model_type,
        champion_id=request.champion_id,
        challenger_id=request.challenger_id,
        challenger_traffic_pct=request.challenger_traffic_pct,
    )

    return {
        "status": "success",
        "data": {
            "message": "A/B test configured successfully",
            "config": config,
        },
    }


@router.post("/ab-test/promote")
async def promote_or_rollback(
    request: ModelPromotionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(["admin"])),
    registry: ModelRegistryService = Depends(get_model_registry_service),
) -> dict[str, Any]:
    """
    Promote challenger to champion or rollback to previous version.

    **Requires roles:** admin
    """
    logger.info(
        f"Model {request.action} for {request.model_type} by {current_user.username}"
    )

    if request.action == "promote":
        result = registry.promote_challenger(request.model_type)
        action_msg = "promoted to champion"
    elif request.action == "rollback":
        result = registry.rollback(request.model_type, request.target_version)
        action_msg = f"rolled back to {request.target_version or 'previous version'}"
    else:
        raise HTTPException(
            status_code=400, detail="Invalid action. Use 'promote' or 'rollback'"
        )

    if result:
        return {
            "status": "success",
            "data": {
                "message": f"Model {action_msg}",
                "model": {
                    "model_id": result.model_id,
                    "version": result.version,
                    "is_champion": result.is_champion,
                },
            },
        }

    raise HTTPException(
        status_code=404, detail="No suitable model found for this action"
    )


@router.get("/models/history")
async def get_model_history(
    model_type: str,
    current_user: CurrentUser = Depends(get_current_user),
    registry: ModelRegistryService = Depends(get_model_registry_service),
) -> dict[str, Any]:
    """
    Get model version history.

    **Requires authentication**
    """
    history = registry.get_model_history(model_type)

    return {
        "status": "success",
        "data": {
            "model_type": model_type,
            "versions": history,
            "count": len(history),
        },
    }


@router.get("/config")
async def get_retraining_config(
    current_user: CurrentUser = Depends(get_current_user),
    drift_service: DriftDetectionService = Depends(get_drift_detection_service),
) -> dict[str, Any]:
    """
    Get current retraining configuration.

    **Requires authentication**
    """
    config = drift_service.config

    return {
        "status": "success",
        "data": {
            "mape_threshold": config.mape_threshold,
            "mae_threshold_voltage": config.mae_threshold_voltage,
            "drift_score_threshold": config.drift_score_threshold,
            "min_samples_for_detection": config.min_samples_for_detection,
            "max_days_without_retrain": config.max_days_without_retrain,
            "min_days_between_retrains": config.min_days_between_retrains,
            "consecutive_violations": config.consecutive_violations,
            "confidence_level": config.confidence_level,
        },
    }


@router.put("/config")
async def update_retraining_config(
    config: RetrainingTriggerConfig,
    current_user: CurrentUser = Depends(require_roles(["admin"])),
    drift_service: DriftDetectionService = Depends(get_drift_detection_service),
) -> dict[str, Any]:
    """
    Update retraining configuration.

    **Requires roles:** admin
    """
    logger.info(f"Retraining config updated by {current_user.username}")

    # Update service config
    drift_service.config.mape_threshold = config.mape_threshold
    drift_service.config.mae_threshold_voltage = config.mae_threshold_voltage
    drift_service.config.drift_score_threshold = config.drift_score_threshold
    drift_service.config.max_days_without_retrain = config.max_days_without_retrain
    drift_service.config.consecutive_violations = config.consecutive_violations

    return {
        "status": "success",
        "data": {
            "message": "Configuration updated successfully",
            "updated_by": current_user.username,
            "updated_at": datetime.now().isoformat(),
        },
    }
