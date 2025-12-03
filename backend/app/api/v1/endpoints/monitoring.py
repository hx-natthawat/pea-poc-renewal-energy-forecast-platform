"""
Model Monitoring API endpoints.

Provides model performance tracking, drift detection, and accuracy monitoring.
"""

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, get_current_user, require_roles
from app.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Models
# =============================================================================


class ModelType(str, Enum):
    solar = "solar"
    voltage = "voltage"


class MetricType(str, Enum):
    mape = "mape"
    mae = "mae"
    rmse = "rmse"
    r2 = "r2"
    bias = "bias"


class PerformanceMetric(BaseModel):
    """Performance metric for a time period."""
    period: str
    mape: Optional[float] = None
    mae: Optional[float] = None
    rmse: Optional[float] = None
    r2: Optional[float] = None
    bias: Optional[float] = None
    sample_count: int


class DriftIndicator(BaseModel):
    """Drift detection result."""
    feature: str
    drift_score: float
    drift_detected: bool
    baseline_mean: float
    current_mean: float
    threshold: float


class ModelHealth(BaseModel):
    """Model health status."""
    model_type: str
    model_version: str
    is_healthy: bool
    last_prediction: Optional[str] = None
    predictions_24h: int
    avg_latency_ms: float
    accuracy_status: str  # good, warning, degraded
    issues: List[str]


# =============================================================================
# Helper Functions
# =============================================================================


def calculate_metrics(predictions: List[float], actuals: List[float]) -> Dict[str, float]:
    """Calculate accuracy metrics."""
    if not predictions or not actuals or len(predictions) != len(actuals):
        return {}

    import numpy as np

    preds = np.array(predictions)
    acts = np.array(actuals)

    # Filter out zeros to avoid division errors
    valid_mask = acts != 0
    if not np.any(valid_mask):
        return {}

    preds_valid = preds[valid_mask]
    acts_valid = acts[valid_mask]

    # MAE
    mae = float(np.mean(np.abs(preds_valid - acts_valid)))

    # RMSE
    rmse = float(np.sqrt(np.mean((preds_valid - acts_valid) ** 2)))

    # MAPE
    mape = float(np.mean(np.abs((acts_valid - preds_valid) / acts_valid)) * 100)

    # R-squared
    ss_res = np.sum((acts_valid - preds_valid) ** 2)
    ss_tot = np.sum((acts_valid - np.mean(acts_valid)) ** 2)
    r2 = float(1 - (ss_res / ss_tot)) if ss_tot > 0 else 0

    # Bias
    bias = float(np.mean(preds_valid - acts_valid))

    return {
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "mape": round(mape, 2),
        "r2": round(r2, 4),
        "bias": round(bias, 4),
    }


# =============================================================================
# Endpoints
# =============================================================================


@router.get("/health")
async def get_model_health(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get health status for all models.

    **Requires authentication**

    Checks model availability, prediction latency, and accuracy status.
    """
    logger.info(f"Model health requested by {current_user.username}")

    health_status = []

    for model_type in ["solar", "voltage"]:
        # Get recent predictions count
        count_query = text("""
            SELECT COUNT(*)
            FROM predictions
            WHERE model_type = :model_type
              AND time >= NOW() - INTERVAL '24 hours'
        """)
        count_result = await db.execute(count_query, {"model_type": model_type})
        predictions_24h = count_result.scalar() or 0

        # Get latest prediction time
        latest_query = text("""
            SELECT MAX(time), AVG(prediction_time_ms)
            FROM predictions
            WHERE model_type = :model_type
        """)
        latest_result = await db.execute(latest_query, {"model_type": model_type})
        latest_row = latest_result.fetchone()

        last_prediction = latest_row[0].isoformat() if latest_row and latest_row[0] else None
        avg_latency = latest_row[1] if latest_row and latest_row[1] else 0

        # Get model version from ml_models table
        version_query = text("""
            SELECT version FROM ml_models
            WHERE model_type = :model_type AND is_active = true
            LIMIT 1
        """)
        version_result = await db.execute(version_query, {"model_type": model_type})
        version_row = version_result.fetchone()
        model_version = version_row[0] if version_row else "v1.0.0"

        # Determine health status
        issues = []
        accuracy_status = "good"

        if predictions_24h == 0:
            issues.append("No predictions in last 24 hours")
            accuracy_status = "degraded"
        elif predictions_24h < 100:
            issues.append("Low prediction volume")

        if avg_latency > 500:
            issues.append(f"High latency: {avg_latency:.0f}ms (target: <500ms)")
            accuracy_status = "warning" if accuracy_status == "good" else accuracy_status

        is_healthy = len(issues) == 0

        health_status.append({
            "model_type": model_type,
            "model_version": model_version,
            "is_healthy": is_healthy,
            "last_prediction": last_prediction,
            "predictions_24h": predictions_24h,
            "avg_latency_ms": round(avg_latency, 1) if avg_latency else 0,
            "accuracy_status": accuracy_status,
            "issues": issues,
        })

    return {
        "status": "success",
        "data": {
            "models": health_status,
            "overall_healthy": all(m["is_healthy"] for m in health_status),
            "checked_at": datetime.now().isoformat(),
        },
    }


@router.get("/performance/{model_type}")
async def get_model_performance(
    model_type: ModelType,
    days: int = Query(default=7, ge=1, le=90, description="Days to analyze"),
    interval: str = Query(default="1d", description="Aggregation interval: 1h, 6h, 1d"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get model performance metrics over time.

    **Requires authentication**

    Returns accuracy metrics aggregated by the specified interval.
    """
    logger.info(f"Performance metrics for {model_type.value} requested by {current_user.username}")

    # Map interval to time_bucket
    bucket_map = {"1h": "1 hour", "6h": "6 hours", "1d": "1 day"}
    bucket = bucket_map.get(interval, "1 day")

    query = text(f"""
        SELECT
            time_bucket('{bucket}', time) as bucket,
            COUNT(*) as count,
            AVG(predicted_value) as avg_predicted,
            AVG(actual_value) as avg_actual,
            AVG(ABS(predicted_value - actual_value)) as mae,
            SQRT(AVG(POWER(predicted_value - actual_value, 2))) as rmse
        FROM predictions
        WHERE model_type = :model_type
          AND time >= NOW() - INTERVAL ':days days'
          AND actual_value IS NOT NULL
        GROUP BY bucket
        ORDER BY bucket ASC
    """.replace(":days", str(days)))

    result = await db.execute(query, {"model_type": model_type.value})
    rows = result.fetchall()

    metrics_timeline = []
    for row in rows:
        if row[0] and row[1] > 0:
            # Calculate MAPE for this bucket
            avg_pred = row[2] or 0
            avg_act = row[3] or 0
            mape = abs((avg_act - avg_pred) / avg_act) * 100 if avg_act != 0 else 0

            metrics_timeline.append({
                "period": row[0].isoformat(),
                "sample_count": row[1],
                "mae": round(row[4], 4) if row[4] else None,
                "rmse": round(row[5], 4) if row[5] else None,
                "mape": round(mape, 2),
            })

    # Calculate overall metrics
    overall_query = text("""
        SELECT
            COUNT(*) as count,
            AVG(ABS(predicted_value - actual_value)) as mae,
            SQRT(AVG(POWER(predicted_value - actual_value, 2))) as rmse
        FROM predictions
        WHERE model_type = :model_type
          AND time >= NOW() - INTERVAL ':days days'
          AND actual_value IS NOT NULL
    """.replace(":days", str(days)))

    overall_result = await db.execute(overall_query, {"model_type": model_type.value})
    overall_row = overall_result.fetchone()

    # Define targets based on TOR
    targets = {
        "solar": {"mape": 10.0, "rmse": 100.0, "mae": None, "r2": 0.95},
        "voltage": {"mae": 2.0, "rmse": 3.0, "r2": 0.90},
    }

    return {
        "status": "success",
        "data": {
            "model_type": model_type.value,
            "analysis_period": {
                "days": days,
                "interval": interval,
                "start": (datetime.now() - timedelta(days=days)).isoformat(),
                "end": datetime.now().isoformat(),
            },
            "overall_metrics": {
                "total_predictions": overall_row[0] if overall_row else 0,
                "mae": round(overall_row[1], 4) if overall_row and overall_row[1] else None,
                "rmse": round(overall_row[2], 4) if overall_row and overall_row[2] else None,
            },
            "targets": targets.get(model_type.value, {}),
            "metrics_timeline": metrics_timeline,
        },
    }


@router.get("/drift/{model_type}")
async def detect_drift(
    model_type: ModelType,
    baseline_days: int = Query(default=30, ge=7, le=90, description="Baseline period (days)"),
    current_days: int = Query(default=7, ge=1, le=30, description="Current period (days)"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(["admin", "analyst"])),
) -> Dict[str, Any]:
    """
    Detect data drift by comparing baseline and current distributions.

    **Requires roles:** admin or analyst

    Compares feature distributions between baseline and current periods.
    """
    logger.info(f"Drift detection for {model_type.value} requested by {current_user.username}")

    drift_indicators = []

    if model_type == ModelType.solar:
        # Check drift in solar features
        features = ["power_kw", "pyrano1", "ambtemp"]
        table = "solar_measurements"
        feature_columns = {"power_kw": "power_kw", "pyrano1": "pyrano1", "ambtemp": "ambtemp"}
    else:
        # Check drift in voltage features
        features = ["voltage", "active_power"]
        table = "single_phase_meters"
        feature_columns = {"voltage": "energy_meter_voltage", "active_power": "active_power"}

    for feature in features:
        col = feature_columns.get(feature, feature)

        # Baseline statistics
        baseline_query = text(f"""
            SELECT AVG({col}) as mean, STDDEV({col}) as std
            FROM {table}
            WHERE time >= NOW() - INTERVAL ':baseline_days days'
              AND time < NOW() - INTERVAL ':current_days days'
        """.replace(":baseline_days", str(baseline_days)).replace(":current_days", str(current_days)))

        baseline_result = await db.execute(baseline_query)
        baseline_row = baseline_result.fetchone()

        # Current statistics
        current_query = text(f"""
            SELECT AVG({col}) as mean, STDDEV({col}) as std
            FROM {table}
            WHERE time >= NOW() - INTERVAL ':current_days days'
        """.replace(":current_days", str(current_days)))

        current_result = await db.execute(current_query)
        current_row = current_result.fetchone()

        if baseline_row and current_row and baseline_row[0] and current_row[0]:
            baseline_mean = baseline_row[0]
            baseline_std = baseline_row[1] or 1
            current_mean = current_row[0]

            # Calculate drift score (z-score of mean difference)
            drift_score = abs((current_mean - baseline_mean) / baseline_std)
            threshold = 2.0  # Standard threshold for drift detection

            drift_indicators.append({
                "feature": feature,
                "drift_score": round(drift_score, 3),
                "drift_detected": drift_score > threshold,
                "baseline_mean": round(baseline_mean, 2),
                "current_mean": round(current_mean, 2),
                "threshold": threshold,
            })

    overall_drift = any(d["drift_detected"] for d in drift_indicators)

    return {
        "status": "success",
        "data": {
            "model_type": model_type.value,
            "analysis_config": {
                "baseline_days": baseline_days,
                "current_days": current_days,
            },
            "overall_drift_detected": overall_drift,
            "drift_indicators": drift_indicators,
            "recommendations": [
                "Consider retraining the model with recent data" if overall_drift else "No action needed",
            ] if drift_indicators else [],
            "analyzed_at": datetime.now().isoformat(),
        },
    }


@router.get("/predictions/accuracy")
async def get_prediction_accuracy(
    model_type: ModelType = Query(..., description="Model type"),
    hours: int = Query(default=24, ge=1, le=168, description="Hours to analyze"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get detailed prediction accuracy breakdown.

    **Requires authentication**

    Returns accuracy analysis with error distribution.
    """
    logger.info(f"Prediction accuracy for {model_type.value} requested by {current_user.username}")

    query = text("""
        SELECT
            predicted_value,
            actual_value,
            ABS(predicted_value - actual_value) as error,
            time
        FROM predictions
        WHERE model_type = :model_type
          AND time >= NOW() - INTERVAL ':hours hours'
          AND actual_value IS NOT NULL
        ORDER BY time ASC
    """.replace(":hours", str(hours)))

    result = await db.execute(query, {"model_type": model_type.value})
    rows = result.fetchall()

    if not rows:
        return {
            "status": "success",
            "data": {
                "model_type": model_type.value,
                "message": "No predictions with actual values found",
                "predictions": [],
            },
        }

    predictions = []
    errors = []
    for row in rows:
        pred, act, err, time = row
        predictions.append({
            "time": time.isoformat() if time else None,
            "predicted": round(pred, 2) if pred else None,
            "actual": round(act, 2) if act else None,
            "error": round(err, 2) if err else None,
        })
        if err is not None:
            errors.append(err)

    # Error distribution
    import numpy as np
    errors_arr = np.array(errors)

    percentiles = {
        "p50": round(float(np.percentile(errors_arr, 50)), 2),
        "p90": round(float(np.percentile(errors_arr, 90)), 2),
        "p95": round(float(np.percentile(errors_arr, 95)), 2),
        "p99": round(float(np.percentile(errors_arr, 99)), 2),
    } if len(errors) > 0 else {}

    return {
        "status": "success",
        "data": {
            "model_type": model_type.value,
            "analysis_period_hours": hours,
            "total_predictions": len(predictions),
            "error_distribution": percentiles,
            "predictions": predictions[-100:],  # Return last 100 for visualization
        },
    }


@router.get("/models")
async def list_models(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    List all registered models.

    **Requires authentication**

    Returns model registry with versions and metrics.
    """
    query = text("""
        SELECT
            id, name, version, model_type, metrics,
            is_active, is_production, trained_at, created_at
        FROM ml_models
        ORDER BY model_type, created_at DESC
    """)

    result = await db.execute(query)
    rows = result.fetchall()

    models = []
    for row in rows:
        models.append({
            "id": row[0],
            "name": row[1],
            "version": row[2],
            "model_type": row[3],
            "metrics": row[4],
            "is_active": row[5],
            "is_production": row[6],
            "trained_at": row[7].isoformat() if row[7] else None,
            "created_at": row[8].isoformat() if row[8] else None,
        })

    return {
        "status": "success",
        "data": {
            "models": models,
            "count": len(models),
        },
    }
