"""
Audit Service for managing access logs and audit trail.

Implements TOR 7.1.6 requirement for comprehensive audit logging.
"""

import logging
from datetime import datetime, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas.audit import (
    AuditLogEntry,
    AuditLogFilter,
    AuditLogStats,
    UserActivitySummary,
)

logger = logging.getLogger(__name__)


class AuditService:
    """
    Service for managing audit logs.

    Features:
    - Query audit logs with filtering
    - Get user activity summaries
    - Generate statistics
    - Create audit entries programmatically
    """

    @staticmethod
    async def get_logs(
        db: AsyncSession,
        filters: AuditLogFilter,
        skip: int = 0,
        limit: int = 100,
    ) -> list[AuditLogEntry]:
        """
        Get audit logs with optional filtering.

        Args:
            db: Database session
            filters: Filtering parameters
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return

        Returns:
            List of audit log entries
        """
        # Build WHERE clause dynamically
        where_conditions: list[str] = []
        params: dict[str, object] = {"skip": skip, "limit": limit}

        if filters.user_id:
            where_conditions.append("user_id = :user_id")
            params["user_id"] = filters.user_id

        if filters.user_email:
            where_conditions.append("user_email = :user_email")
            params["user_email"] = filters.user_email

        if filters.action:
            where_conditions.append("action = :action")
            params["action"] = filters.action

        if filters.resource_type:
            where_conditions.append("resource_type = :resource_type")
            params["resource_type"] = filters.resource_type

        if filters.resource_id:
            where_conditions.append("resource_id = :resource_id")
            params["resource_id"] = filters.resource_id

        if filters.request_method:
            where_conditions.append("request_method = :request_method")
            params["request_method"] = filters.request_method

        if filters.response_status:
            where_conditions.append("response_status = :response_status")
            params["response_status"] = filters.response_status

        if filters.user_ip:
            where_conditions.append("user_ip = :user_ip")
            params["user_ip"] = filters.user_ip

        if filters.start_date:
            where_conditions.append("time >= :start_date")
            params["start_date"] = filters.start_date

        if filters.end_date:
            where_conditions.append("time <= :end_date")
            params["end_date"] = filters.end_date

        where_clause = " AND ".join(where_conditions) if where_conditions else "TRUE"

        query = text(f"""
            SELECT id, time, user_id, user_email, user_ip, action,
                   resource_type, resource_id, request_method, request_path,
                   request_body, response_status, user_agent, session_id
            FROM audit_log
            WHERE {where_clause}
            ORDER BY time DESC
            OFFSET :skip
            LIMIT :limit
        """)

        result = await db.execute(query, params)
        rows = result.fetchall()

        logs = []
        for row in rows:
            logs.append(
                AuditLogEntry(
                    id=row.id,
                    time=row.time,
                    user_id=row.user_id,
                    user_email=row.user_email,
                    user_ip=str(row.user_ip) if row.user_ip else None,
                    action=row.action,
                    resource_type=row.resource_type,
                    resource_id=row.resource_id,
                    request_method=row.request_method,
                    request_path=row.request_path,
                    request_body=row.request_body,
                    response_status=row.response_status,
                    user_agent=row.user_agent,
                    session_id=row.session_id,
                )
            )

        return logs

    @staticmethod
    async def get_log_by_id(
        db: AsyncSession, log_id: int, time: datetime
    ) -> AuditLogEntry | None:
        """
        Get a single audit log entry by ID and time.

        Args:
            db: Database session
            log_id: The audit log ID
            time: The timestamp (needed for hypertable partitioning)

        Returns:
            Audit log entry or None if not found
        """
        query = text("""
            SELECT id, time, user_id, user_email, user_ip, action,
                   resource_type, resource_id, request_method, request_path,
                   request_body, response_status, user_agent, session_id
            FROM audit_log
            WHERE id = :log_id
              AND time::date = :time_date
            LIMIT 1
        """)

        result = await db.execute(query, {"log_id": log_id, "time_date": time.date()})
        row = result.fetchone()

        if not row:
            return None

        return AuditLogEntry(
            id=row.id,
            time=row.time,
            user_id=row.user_id,
            user_email=row.user_email,
            user_ip=str(row.user_ip) if row.user_ip else None,
            action=row.action,
            resource_type=row.resource_type,
            resource_id=row.resource_id,
            request_method=row.request_method,
            request_path=row.request_path,
            request_body=row.request_body,
            response_status=row.response_status,
            user_agent=row.user_agent,
            session_id=row.session_id,
        )

    @staticmethod
    async def get_user_activity(
        db: AsyncSession, user_id: str, days: int = 30
    ) -> UserActivitySummary | None:
        """
        Get activity summary for a specific user.

        Args:
            db: Database session
            user_id: User identifier
            days: Number of days to look back

        Returns:
            User activity summary or None if no activity found
        """
        start_date = datetime.now() - timedelta(days=days)

        # Get overall stats
        stats_query = text("""
            SELECT
                user_id,
                user_email,
                COUNT(*) as total_requests,
                MAX(time) as last_activity,
                COUNT(*) FILTER (WHERE response_status >= 400) as failed_requests
            FROM audit_log
            WHERE user_id = :user_id
              AND time >= :start_date
            GROUP BY user_id, user_email
        """)

        stats_result = await db.execute(
            stats_query, {"user_id": user_id, "start_date": start_date}
        )
        stats_row = stats_result.fetchone()

        if not stats_row:
            return None

        # Get actions breakdown
        actions_query = text("""
            SELECT action, COUNT(*) as count
            FROM audit_log
            WHERE user_id = :user_id
              AND time >= :start_date
            GROUP BY action
            ORDER BY count DESC
        """)

        actions_result = await db.execute(
            actions_query, {"user_id": user_id, "start_date": start_date}
        )
        actions_rows = actions_result.fetchall()
        actions_breakdown = {row.action: row.count for row in actions_rows}

        # Get most accessed resources
        resources_query = text("""
            SELECT resource_type, COUNT(*) as count
            FROM audit_log
            WHERE user_id = :user_id
              AND time >= :start_date
              AND resource_type IS NOT NULL
            GROUP BY resource_type
            ORDER BY count DESC
            LIMIT 10
        """)

        resources_result = await db.execute(
            resources_query, {"user_id": user_id, "start_date": start_date}
        )
        resources_rows = resources_result.fetchall()
        most_accessed_resources = [
            {"resource_type": row.resource_type, "count": row.count}
            for row in resources_rows
        ]

        # Calculate average requests per day
        total_requests = stats_row.total_requests
        avg_per_day = total_requests / days if days > 0 else 0

        return UserActivitySummary(
            user_id=stats_row.user_id,
            user_email=stats_row.user_email,
            total_requests=total_requests,
            last_activity=stats_row.last_activity,
            actions_breakdown=actions_breakdown,
            most_accessed_resources=most_accessed_resources,
            failed_requests=stats_row.failed_requests,
            avg_requests_per_day=round(avg_per_day, 2),
        )

    @staticmethod
    async def get_stats(
        db: AsyncSession, start_date: datetime, end_date: datetime
    ) -> AuditLogStats:
        """
        Get statistics for audit logs within a date range.

        Args:
            db: Database session
            start_date: Start of the period
            end_date: End of the period

        Returns:
            Audit log statistics
        """
        # Get overall stats
        overview_query = text("""
            SELECT
                COUNT(*) as total_requests,
                COUNT(DISTINCT user_id) as unique_users,
                COUNT(*) FILTER (WHERE response_status < 400) as successful_requests,
                COUNT(*) FILTER (WHERE response_status >= 400) as failed_requests
            FROM audit_log
            WHERE time >= :start_date
              AND time <= :end_date
        """)

        overview_result = await db.execute(
            overview_query, {"start_date": start_date, "end_date": end_date}
        )
        overview = overview_result.fetchone()

        # Get actions breakdown
        actions_query = text("""
            SELECT action, COUNT(*) as count
            FROM audit_log
            WHERE time >= :start_date
              AND time <= :end_date
            GROUP BY action
            ORDER BY count DESC
        """)

        actions_result = await db.execute(
            actions_query, {"start_date": start_date, "end_date": end_date}
        )
        actions_rows = actions_result.fetchall()
        actions_breakdown = {row.action: row.count for row in actions_rows}

        # Get resources breakdown
        resources_query = text("""
            SELECT resource_type, COUNT(*) as count
            FROM audit_log
            WHERE time >= :start_date
              AND time <= :end_date
              AND resource_type IS NOT NULL
            GROUP BY resource_type
            ORDER BY count DESC
        """)

        resources_result = await db.execute(
            resources_query, {"start_date": start_date, "end_date": end_date}
        )
        resources_rows = resources_result.fetchall()
        resources_breakdown = {row.resource_type: row.count for row in resources_rows}

        # Get top users
        top_users_query = text("""
            SELECT user_id, user_email, COUNT(*) as count
            FROM audit_log
            WHERE time >= :start_date
              AND time <= :end_date
              AND user_id IS NOT NULL
            GROUP BY user_id, user_email
            ORDER BY count DESC
            LIMIT 10
        """)

        top_users_result = await db.execute(
            top_users_query, {"start_date": start_date, "end_date": end_date}
        )
        top_users_rows = top_users_result.fetchall()
        top_users = [
            {
                "user_id": row.user_id,
                "user_email": row.user_email,
                "count": row.count,
            }
            for row in top_users_rows
        ]

        # Calculate error rate
        total = overview.total_requests if overview else 0
        failed = overview.failed_requests if overview else 0
        error_rate = (failed / total * 100) if total > 0 else 0.0

        return AuditLogStats(
            total_requests=total,
            unique_users=overview.unique_users if overview else 0,
            successful_requests=overview.successful_requests if overview else 0,
            failed_requests=failed,
            actions_breakdown=actions_breakdown,
            resources_breakdown=resources_breakdown,
            top_users=top_users,
            error_rate=round(error_rate, 2),
            period_start=start_date,
            period_end=end_date,
        )

    @staticmethod
    async def create_log_entry(
        db: AsyncSession,
        user_id: str | None,
        user_email: str | None,
        user_ip: str | None,
        action: str,
        resource_type: str | None,
        resource_id: str | None,
        request_method: str | None,
        request_path: str | None,
        request_body: dict | None,
        response_status: int | None,
        user_agent: str | None,
        session_id: str | None,
    ) -> AuditLogEntry:
        """
        Create a new audit log entry programmatically.

        This method can be used to manually create audit logs for
        special events not captured by middleware.

        Args:
            db: Database session
            user_id: User identifier
            user_email: User email
            user_ip: IP address
            action: Action performed
            resource_type: Type of resource accessed
            resource_id: ID of resource
            request_method: HTTP method
            request_path: Request path
            request_body: Request body (will be JSON serialized)
            response_status: HTTP status code
            user_agent: User agent string
            session_id: Session identifier

        Returns:
            Created audit log entry
        """
        import json

        query = text("""
            INSERT INTO audit_log (
                time, user_id, user_email, user_ip, action,
                resource_type, resource_id, request_method, request_path,
                request_body, response_status, user_agent, session_id
            ) VALUES (
                :time, :user_id, :user_email, :user_ip, :action,
                :resource_type, :resource_id, :request_method, :request_path,
                :request_body, :response_status, :user_agent, :session_id
            )
            RETURNING id, time
        """)

        result = await db.execute(
            query,
            {
                "time": datetime.now(),
                "user_id": user_id,
                "user_email": user_email,
                "user_ip": user_ip,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "request_method": request_method,
                "request_path": request_path,
                "request_body": json.dumps(request_body) if request_body else None,
                "response_status": response_status,
                "user_agent": user_agent,
                "session_id": session_id,
            },
        )
        await db.commit()

        row = result.fetchone()
        if row is None:
            raise ValueError("Failed to create audit log entry")

        return AuditLogEntry(
            id=row.id,
            time=row.time,
            user_id=user_id,
            user_email=user_email,
            user_ip=user_ip,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            request_method=request_method,
            request_path=request_path,
            request_body=request_body,
            response_status=response_status,
            user_agent=user_agent,
            session_id=session_id,
        )


# Singleton instance getter
_audit_service: AuditService | None = None


def get_audit_service() -> AuditService:
    """Get or create audit service instance."""
    global _audit_service
    if _audit_service is None:
        _audit_service = AuditService()
    return _audit_service
