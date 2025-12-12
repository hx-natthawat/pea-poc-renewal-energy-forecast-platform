"""
Alert management endpoints for voltage violations and system notifications.

Authentication is controlled by AUTH_ENABLED setting.
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, get_current_user, require_roles
from app.db import get_db
from app.ml import get_voltage_inference

logger = logging.getLogger(__name__)

router = APIRouter()


# Voltage limits per TOR
VOLTAGE_NOMINAL = 230.0
VOLTAGE_UPPER_LIMIT = 242.0  # +5%
VOLTAGE_LOWER_LIMIT = 218.0  # -5%
VOLTAGE_WARNING_UPPER = 238.0
VOLTAGE_WARNING_LOWER = 222.0


class Alert(BaseModel):
    """Alert model."""

    id: int | None = None
    time: datetime
    alert_type: str
    severity: str  # info, warning, critical
    target_id: str
    message: str
    current_value: float | None = None
    threshold_value: float | None = None
    acknowledged: bool = False
    resolved: bool = False


class AlertResponse(BaseModel):
    """Alert response model."""

    status: str
    data: dict[str, Any]


class VoltageCheckRequest(BaseModel):
    """Request to check voltage for violations."""

    timestamp: datetime = Field(default_factory=datetime.now)
    prosumer_ids: list[str] = Field(
        default=[
            "prosumer1",
            "prosumer2",
            "prosumer3",
            "prosumer4",
            "prosumer5",
            "prosumer6",
            "prosumer7",
        ]
    )


class AlertStats(BaseModel):
    """Alert statistics."""

    total: int
    critical: int
    warning: int
    info: int
    unacknowledged: int


@router.get("/")
async def get_alerts(
    severity: str | None = None,
    acknowledged: bool | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> AlertResponse:
    """
    Get recent alerts from the database.
    """
    query = text("""
        SELECT id, time, alert_type, severity, target_id, message,
               current_value, threshold_value, acknowledged, resolved
        FROM alerts
        WHERE resolved = false
        ORDER BY time DESC
        LIMIT :limit
    """)

    result = await db.execute(query, {"limit": limit})
    rows = result.fetchall()

    alerts = []
    for row in rows:
        alerts.append(
            {
                "id": row.id,
                "time": row.time.isoformat(),
                "alert_type": row.alert_type,
                "severity": row.severity,
                "target_id": row.target_id,
                "message": row.message,
                "current_value": row.current_value,
                "threshold_value": row.threshold_value,
                "acknowledged": row.acknowledged,
                "resolved": row.resolved,
            }
        )

    return AlertResponse(
        status="success",
        data={
            "alerts": alerts,
            "count": len(alerts),
        },
    )


@router.get("/stats")
async def get_alert_stats(
    hours: int = Query(default=24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> AlertResponse:
    """
    Get alert statistics for the specified time period.
    """
    query = text("""
        SELECT
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE severity = 'critical') as critical,
            COUNT(*) FILTER (WHERE severity = 'warning') as warning,
            COUNT(*) FILTER (WHERE severity = 'info') as info,
            COUNT(*) FILTER (WHERE acknowledged = false) as unacknowledged
        FROM alerts
        WHERE time >= NOW() - INTERVAL '1 hour' * :hours
    """)

    result = await db.execute(query, {"hours": hours})
    row = result.fetchone()

    stats = {
        "total": row.total if row else 0,
        "critical": row.critical if row else 0,
        "warning": row.warning if row else 0,
        "info": row.info if row else 0,
        "unacknowledged": row.unacknowledged if row else 0,
    }

    return AlertResponse(
        status="success",
        data={
            "stats": stats,
            "period_hours": hours,
        },
    )


@router.post("/check-voltage")
async def check_voltage_violations(
    request: VoltageCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(["admin", "operator", "api"])),
) -> AlertResponse:
    """
    Check for voltage violations using ML predictions and create alerts.
    """
    inference = get_voltage_inference()
    alerts_created = []
    prediction_errors = []

    for prosumer_id in request.prosumer_ids:
        try:
            result = inference.predict(
                timestamp=request.timestamp,
                prosumer_id=prosumer_id,
            )
        except Exception as e:
            logger.error(
                f"Voltage prediction failed for {prosumer_id}: {type(e).__name__}: {e}"
            )
            prediction_errors.append(prosumer_id)
            continue

        voltage = result["predicted_voltage"]
        status = result["status"]

        # Determine if alert needed
        if status in ["warning", "critical"]:
            severity = status
            if voltage > VOLTAGE_NOMINAL:
                alert_type = "overvoltage"
                threshold = (
                    VOLTAGE_UPPER_LIMIT
                    if status == "critical"
                    else VOLTAGE_WARNING_UPPER
                )
                message = f"High voltage detected at {prosumer_id}: {voltage:.1f}V (threshold: {threshold}V)"
            else:
                alert_type = "undervoltage"
                threshold = (
                    VOLTAGE_LOWER_LIMIT
                    if status == "critical"
                    else VOLTAGE_WARNING_LOWER
                )
                message = f"Low voltage detected at {prosumer_id}: {voltage:.1f}V (threshold: {threshold}V)"

            # Insert alert into database
            insert_query = text("""
                INSERT INTO alerts (time, alert_type, severity, target_id, message, current_value, threshold_value)
                VALUES (:time, :alert_type, :severity, :target_id, :message, :current_value, :threshold_value)
                RETURNING id
            """)

            try:
                result = await db.execute(
                    insert_query,
                    {
                        "time": request.timestamp,
                        "alert_type": alert_type,
                        "severity": severity,
                        "target_id": prosumer_id,
                        "message": message,
                        "current_value": voltage,
                        "threshold_value": threshold,
                    },
                )
                await db.commit()
                alert_id = result.scalar()

                alerts_created.append(
                    {
                        "id": alert_id,
                        "prosumer_id": prosumer_id,
                        "alert_type": alert_type,
                        "severity": severity,
                        "voltage": voltage,
                        "message": message,
                    }
                )
            except Exception as e:
                # Rollback failed transaction and continue checking other prosumers
                await db.rollback()
                logger.error(
                    f"Failed to insert alert for {prosumer_id}: {type(e).__name__}: {e}"
                )

    return AlertResponse(
        status="success",
        data={
            "alerts_created": alerts_created,
            "count": len(alerts_created),
            "timestamp": request.timestamp.isoformat(),
            "prediction_errors": prediction_errors if prediction_errors else None,
        },
    )


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(["admin", "operator"])),
) -> AlertResponse:
    """
    Acknowledge an alert.
    """
    query = text("""
        UPDATE alerts SET acknowledged = true
        WHERE id = :alert_id
        RETURNING id, target_id, severity
    """)

    result = await db.execute(query, {"alert_id": alert_id})
    await db.commit()
    row = result.fetchone()

    if not row:
        return AlertResponse(
            status="error", data={"message": f"Alert {alert_id} not found"}
        )

    return AlertResponse(
        status="success",
        data={
            "alert_id": row.id,
            "target_id": row.target_id,
            "acknowledged": True,
        },
    )


@router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(["admin", "operator"])),
) -> AlertResponse:
    """
    Resolve an alert.
    """
    query = text("""
        UPDATE alerts SET resolved = true, acknowledged = true
        WHERE id = :alert_id
        RETURNING id, target_id
    """)

    result = await db.execute(query, {"alert_id": alert_id})
    await db.commit()
    row = result.fetchone()

    if not row:
        return AlertResponse(
            status="error", data={"message": f"Alert {alert_id} not found"}
        )

    return AlertResponse(
        status="success",
        data={
            "alert_id": row.id,
            "target_id": row.target_id,
            "resolved": True,
        },
    )


@router.get("/summary")
async def get_alert_summary(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> AlertResponse:
    """
    Get a summary of current system alert status.
    """
    # Get unresolved alert counts by prosumer
    query = text("""
        SELECT
            target_id,
            severity,
            COUNT(*) as count,
            MAX(current_value) as max_voltage,
            MIN(current_value) as min_voltage
        FROM alerts
        WHERE resolved = false
        GROUP BY target_id, severity
        ORDER BY target_id
    """)

    result = await db.execute(query)
    rows = result.fetchall()

    by_prosumer = {}
    for row in rows:
        if row.target_id not in by_prosumer:
            by_prosumer[row.target_id] = {"critical": 0, "warning": 0, "info": 0}
        by_prosumer[row.target_id][row.severity] = row.count

    # Get overall status
    total_critical = sum(p.get("critical", 0) for p in by_prosumer.values())
    total_warning = sum(p.get("warning", 0) for p in by_prosumer.values())

    if total_critical > 0:
        overall_status = "critical"
    elif total_warning > 0:
        overall_status = "warning"
    else:
        overall_status = "normal"

    return AlertResponse(
        status="success",
        data={
            "overall_status": overall_status,
            "by_prosumer": by_prosumer,
            "total_critical": total_critical,
            "total_warning": total_warning,
        },
    )


@router.get("/timeline")
async def get_alert_timeline(
    hours: int = Query(default=24, ge=1, le=168, description="Hours of history"),
    interval: str = Query(default="1h", description="Bucket interval: 15m, 1h, 6h, 1d"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> AlertResponse:
    """
    Get alert timeline data for dashboard visualization.

    **Requires authentication**

    Returns alerts bucketed by time interval for timeline charts.
    """
    logger.info(f"Alert timeline requested by user: {current_user.username}")

    # Map interval string to SQL interval
    interval_map = {
        "15m": "15 minutes",
        "1h": "1 hour",
        "6h": "6 hours",
        "1d": "1 day",
    }
    sql_interval = interval_map.get(interval, "1 hour")

    query = text(f"""
        SELECT
            time_bucket('{sql_interval}', time) AS bucket,
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE severity = 'critical') AS critical,
            COUNT(*) FILTER (WHERE severity = 'warning') AS warning,
            COUNT(*) FILTER (WHERE severity = 'info') AS info,
            array_agg(DISTINCT target_id) AS affected_prosumers
        FROM alerts
        WHERE time >= NOW() - INTERVAL '{hours} hours'
        GROUP BY bucket
        ORDER BY bucket ASC
    """)

    result = await db.execute(query)
    rows = result.fetchall()

    timeline = []
    for row in rows:
        timeline.append(
            {
                "time": row.bucket.isoformat() if row.bucket else None,
                "total": row.total,
                "critical": row.critical,
                "warning": row.warning,
                "info": row.info,
                "affected_prosumers": row.affected_prosumers or [],
            }
        )

    return AlertResponse(
        status="success",
        data={
            "timeline": timeline,
            "period_hours": hours,
            "interval": interval,
            "count": len(timeline),
        },
    )


@router.get("/prosumer/{prosumer_id}")
async def get_prosumer_alerts(
    prosumer_id: str,
    hours: int = Query(default=24, ge=1, le=168),
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> AlertResponse:
    """
    Get alerts for a specific prosumer.

    **Requires authentication**
    """
    logger.info(f"Alerts for {prosumer_id} requested by user: {current_user.username}")

    query = text("""
        SELECT id, time, alert_type, severity, target_id, message,
               current_value, threshold_value, acknowledged, resolved
        FROM alerts
        WHERE target_id = :prosumer_id
          AND time >= NOW() - INTERVAL '1 hour' * :hours
        ORDER BY time DESC
        LIMIT :limit
    """)

    result = await db.execute(
        query, {"prosumer_id": prosumer_id, "hours": hours, "limit": limit}
    )
    rows = result.fetchall()

    alerts = []
    for row in rows:
        alerts.append(
            {
                "id": row.id,
                "time": row.time.isoformat(),
                "alert_type": row.alert_type,
                "severity": row.severity,
                "target_id": row.target_id,
                "message": row.message,
                "current_value": row.current_value,
                "threshold_value": row.threshold_value,
                "acknowledged": row.acknowledged,
                "resolved": row.resolved,
            }
        )

    return AlertResponse(
        status="success",
        data={
            "prosumer_id": prosumer_id,
            "alerts": alerts,
            "count": len(alerts),
            "period_hours": hours,
        },
    )
