"""
Audit log endpoints for access logs and audit trail.

Per TOR 7.1.6 requirement for comprehensive audit logging.
All endpoints require authentication (admin role for most operations).
"""

import csv
import io
import json
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, require_roles
from app.db import get_db
from app.models.schemas.audit import (
    AuditLogExport,
    AuditLogFilter,
    AuditLogResponse,
)
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/logs")
async def get_audit_logs(
    user_id: str | None = Query(default=None, description="Filter by user ID"),
    user_email: str | None = Query(default=None, description="Filter by user email"),
    action: str | None = Query(default=None, description="Filter by action type"),
    resource_type: str | None = Query(
        default=None, description="Filter by resource type"
    ),
    resource_id: str | None = Query(default=None, description="Filter by resource ID"),
    request_method: str | None = Query(
        default=None, description="Filter by HTTP method"
    ),
    response_status: int | None = Query(
        default=None, description="Filter by status code"
    ),
    user_ip: str | None = Query(default=None, description="Filter by IP address"),
    start_date: datetime | None = Query(default=None, description="Start date"),
    end_date: datetime | None = Query(default=None, description="End date"),
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=100, ge=1, le=1000, description="Max records to return"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(["admin"])),
) -> AuditLogResponse:
    """
    Get audit logs with optional filtering.

    **Requires admin role**

    Query parameters allow filtering by:
    - User (ID or email)
    - Action type (read, create, update, delete)
    - Resource type and ID
    - HTTP method and status
    - Date range
    - IP address

    Returns paginated results ordered by time descending.
    """
    logger.info(f"Audit logs requested by admin: {current_user.username}")

    filters = AuditLogFilter(
        user_id=user_id,
        user_email=user_email,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        request_method=request_method,
        response_status=response_status,
        user_ip=user_ip,
        start_date=start_date,
        end_date=end_date,
    )

    audit_service = AuditService()
    logs = await audit_service.get_logs(db, filters, skip, limit)

    return AuditLogResponse(
        status="success",
        data={
            "logs": [log.model_dump() for log in logs],
            "count": len(logs),
            "skip": skip,
            "limit": limit,
            "filters": filters.model_dump(exclude_none=True),
        },
    )


@router.get("/logs/{log_id}")
async def get_audit_log_by_id(
    log_id: int,
    time: datetime = Query(
        ..., description="Timestamp of the log entry (for partitioning)"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(["admin"])),
) -> AuditLogResponse:
    """
    Get a single audit log entry by ID.

    **Requires admin role**

    Due to TimescaleDB hypertable partitioning, both the ID and
    approximate timestamp are required.
    """
    logger.info(f"Audit log {log_id} requested by admin: {current_user.username}")

    audit_service = AuditService()
    log = await audit_service.get_log_by_id(db, log_id, time)

    if not log:
        raise HTTPException(
            status_code=404, detail=f"Audit log entry {log_id} not found"
        )

    return AuditLogResponse(status="success", data={"log": log.model_dump()})


@router.get("/users/{user_id}/activity")
async def get_user_activity(
    user_id: str,
    days: int = Query(default=30, ge=1, le=365, description="Days of history"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(["admin"])),
) -> AuditLogResponse:
    """
    Get activity summary for a specific user.

    **Requires admin role**

    Returns:
    - Total requests
    - Last activity timestamp
    - Breakdown by action type
    - Most accessed resources
    - Failed request count
    - Average requests per day
    """
    logger.info(
        f"User activity for {user_id} requested by admin: {current_user.username}"
    )

    audit_service = AuditService()
    activity = await audit_service.get_user_activity(db, user_id, days)

    if not activity:
        raise HTTPException(
            status_code=404,
            detail=f"No activity found for user {user_id} in the last {days} days",
        )

    return AuditLogResponse(
        status="success",
        data={
            "activity": activity.model_dump(),
            "period_days": days,
        },
    )


@router.get("/stats")
async def get_audit_stats(
    start_date: datetime | None = Query(
        default=None, description="Start date (defaults to 7 days ago)"
    ),
    end_date: datetime | None = Query(
        default=None, description="End date (defaults to now)"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(["admin"])),
) -> AuditLogResponse:
    """
    Get summary statistics for audit logs.

    **Requires admin role**

    Returns aggregate statistics including:
    - Total requests
    - Unique users
    - Success/failure counts
    - Breakdown by action and resource type
    - Top users by activity
    - Error rate
    """
    logger.info(f"Audit stats requested by admin: {current_user.username}")

    # Default to last 7 days
    if not end_date:
        end_date = datetime.now()
    if not start_date:
        start_date = end_date - timedelta(days=7)

    audit_service = AuditService()
    stats = await audit_service.get_stats(db, start_date, end_date)

    return AuditLogResponse(
        status="success",
        data={"stats": stats.model_dump()},
    )


@router.post("/export")
async def export_audit_logs(
    export_request: AuditLogExport,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(["admin"])),
) -> StreamingResponse:
    """
    Export audit logs to CSV or JSON format.

    **Requires admin role**

    Request body:
    ```json
    {
      "format": "csv",
      "filters": {
        "start_date": "2024-01-01T00:00:00Z",
        "end_date": "2024-01-31T23:59:59Z"
      },
      "include_request_body": false
    }
    ```

    Returns a file download with the filtered audit logs.
    """
    logger.info(
        f"Audit log export ({export_request.format}) requested by admin: {current_user.username}"
    )

    filters = export_request.filters or AuditLogFilter()
    audit_service = AuditService()

    # Get all matching logs (with a reasonable limit)
    logs = await audit_service.get_logs(db, filters, skip=0, limit=10000)

    if export_request.format == "csv":
        # Generate CSV
        output = io.StringIO()
        fieldnames = [
            "id",
            "time",
            "user_id",
            "user_email",
            "user_ip",
            "action",
            "resource_type",
            "resource_id",
            "request_method",
            "request_path",
            "response_status",
            "user_agent",
            "session_id",
        ]

        if export_request.include_request_body:
            fieldnames.append("request_body")

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for log in logs:
            row = {
                "id": log.id,
                "time": log.time.isoformat(),
                "user_id": log.user_id or "",
                "user_email": log.user_email or "",
                "user_ip": log.user_ip or "",
                "action": log.action,
                "resource_type": log.resource_type or "",
                "resource_id": log.resource_id or "",
                "request_method": log.request_method or "",
                "request_path": log.request_path or "",
                "response_status": log.response_status or "",
                "user_agent": log.user_agent or "",
                "session_id": log.session_id or "",
            }

            if export_request.include_request_body:
                row["request_body"] = (
                    json.dumps(log.request_body) if log.request_body else ""
                )

            writer.writerow(row)

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            },
        )

    elif export_request.format == "json":
        # Generate JSON
        data = {
            "export_date": datetime.now().isoformat(),
            "exported_by": current_user.username,
            "filters": filters.model_dump(exclude_none=True),
            "count": len(logs),
            "logs": [log.model_dump() for log in logs],
        }

        json_str = json.dumps(data, indent=2, default=str)

        return StreamingResponse(
            iter([json_str]),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            },
        )

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported export format: {export_request.format}",
        )


@router.get("/recent")
async def get_recent_audit_logs(
    hours: int = Query(default=24, ge=1, le=168, description="Hours of history"),
    limit: int = Query(default=100, ge=1, le=1000, description="Max records"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(["admin"])),
) -> AuditLogResponse:
    """
    Get recent audit logs from the last N hours.

    **Requires admin role**

    Convenience endpoint for quick access to recent activity.
    Returns logs ordered by time descending.
    """
    logger.info(f"Recent audit logs requested by admin: {current_user.username}")

    start_date = datetime.now() - timedelta(hours=hours)
    filters = AuditLogFilter(start_date=start_date)

    audit_service = AuditService()
    logs = await audit_service.get_logs(db, filters, skip=0, limit=limit)

    return AuditLogResponse(
        status="success",
        data={
            "logs": [log.model_dump() for log in logs],
            "count": len(logs),
            "period_hours": hours,
        },
    )


@router.get("/timeline")
async def get_audit_timeline(
    hours: int = Query(default=24, ge=1, le=168, description="Hours of history"),
    interval: str = Query(default="1h", description="Bucket interval: 15m, 1h, 6h, 1d"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(["admin"])),
) -> AuditLogResponse:
    """
    Get audit log timeline data for visualization.

    **Requires admin role**

    Returns bucketed data showing request patterns over time.
    Useful for dashboard charts and trend analysis.
    """
    logger.info(f"Audit timeline requested by admin: {current_user.username}")

    # Map interval string to SQL interval
    interval_map = {
        "15m": "15 minutes",
        "1h": "1 hour",
        "6h": "6 hours",
        "1d": "1 day",
    }
    sql_interval = interval_map.get(interval, "1 hour")

    from sqlalchemy import text

    query = text(f"""
        SELECT
            time_bucket('{sql_interval}', time) AS bucket,
            COUNT(*) AS total_requests,
            COUNT(DISTINCT user_id) AS unique_users,
            COUNT(*) FILTER (WHERE response_status >= 400) AS failed_requests,
            array_agg(DISTINCT action) AS actions
        FROM audit_log
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
                "total_requests": row.total_requests,
                "unique_users": row.unique_users,
                "failed_requests": row.failed_requests,
                "success_rate": round(
                    (
                        (row.total_requests - row.failed_requests)
                        / row.total_requests
                        * 100
                    )
                    if row.total_requests > 0
                    else 0,
                    2,
                ),
                "actions": row.actions or [],
            }
        )

    return AuditLogResponse(
        status="success",
        data={
            "timeline": timeline,
            "period_hours": hours,
            "interval": interval,
            "count": len(timeline),
        },
    )


@router.get("/security-events")
async def get_security_events(
    hours: int = Query(default=24, ge=1, le=168, description="Hours of history"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(["admin"])),
) -> AuditLogResponse:
    """
    Get security-related events (failed auth, suspicious activity).

    **Requires admin role**

    Filters audit logs for security-relevant events:
    - Failed authentication (401, 403)
    - Multiple failures from same IP
    - Unusual access patterns
    """
    logger.info(f"Security events requested by admin: {current_user.username}")

    start_date = datetime.now() - timedelta(hours=hours)

    # Get failed authentication attempts
    from sqlalchemy import text

    query = text("""
        SELECT
            time,
            user_id,
            user_email,
            user_ip,
            request_path,
            response_status,
            COUNT(*) OVER (PARTITION BY user_ip) as attempts_from_ip
        FROM audit_log
        WHERE time >= :start_date
          AND response_status IN (401, 403)
        ORDER BY time DESC
        LIMIT 100
    """)

    result = await db.execute(query, {"start_date": start_date})
    rows = result.fetchall()

    events = []
    for row in rows:
        severity = "critical" if row.attempts_from_ip >= 10 else "warning"
        events.append(
            {
                "time": row.time.isoformat(),
                "user_id": row.user_id,
                "user_email": row.user_email,
                "user_ip": str(row.user_ip) if row.user_ip else None,
                "request_path": row.request_path,
                "response_status": row.response_status,
                "attempts_from_ip": row.attempts_from_ip,
                "severity": severity,
                "event_type": "failed_authentication",
            }
        )

    return AuditLogResponse(
        status="success",
        data={
            "events": events,
            "count": len(events),
            "period_hours": hours,
        },
    )
