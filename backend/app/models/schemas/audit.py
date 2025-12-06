"""
Audit Log Pydantic schemas for API request/response validation.

Per TOR 7.1.6 requirement for access logs and audit trail.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class AuditLogEntry(BaseModel):
    """Schema for audit log entry response."""

    id: int
    time: datetime
    user_id: str | None = None
    user_email: str | None = None
    user_ip: str | None = None
    action: str
    resource_type: str | None = None
    resource_id: str | None = None
    request_method: str | None = None
    request_path: str | None = None
    request_body: dict | None = None
    response_status: int | None = None
    user_agent: str | None = None
    session_id: str | None = None

    model_config = {"from_attributes": True}


class AuditLogFilter(BaseModel):
    """Schema for audit log filtering parameters."""

    user_id: str | None = Field(default=None, description="Filter by user ID")
    user_email: str | None = Field(default=None, description="Filter by user email")
    action: str | None = Field(
        default=None, description="Filter by action: read, create, update, delete"
    )
    resource_type: str | None = Field(
        default=None,
        description="Filter by resource type: forecast, alerts, data, etc.",
    )
    resource_id: str | None = Field(default=None, description="Filter by resource ID")
    request_method: str | None = Field(
        default=None, description="Filter by HTTP method: GET, POST, PUT, DELETE"
    )
    response_status: int | None = Field(
        default=None, description="Filter by HTTP status code"
    )
    start_date: datetime | None = Field(
        default=None, description="Start date for filtering"
    )
    end_date: datetime | None = Field(
        default=None, description="End date for filtering"
    )
    user_ip: str | None = Field(default=None, description="Filter by IP address")


class AuditLogStats(BaseModel):
    """Schema for audit log summary statistics."""

    total_requests: int
    unique_users: int
    successful_requests: int
    failed_requests: int
    actions_breakdown: dict[str, int]
    resources_breakdown: dict[str, int]
    top_users: list[dict[str, int]]
    error_rate: float
    period_start: datetime
    period_end: datetime


class AuditLogExport(BaseModel):
    """Schema for audit log export request."""

    format: str = Field(default="csv", description="Export format: csv, json")
    filters: AuditLogFilter | None = Field(
        default=None, description="Optional filters to apply"
    )
    include_request_body: bool = Field(
        default=False, description="Include request body in export"
    )


class AuditLogResponse(BaseModel):
    """Generic response wrapper for audit endpoints."""

    status: str
    data: dict


class UserActivitySummary(BaseModel):
    """Schema for user activity summary."""

    user_id: str
    user_email: str | None = None
    total_requests: int
    last_activity: datetime
    actions_breakdown: dict[str, int]
    most_accessed_resources: list[dict[str, int]]
    failed_requests: int
    avg_requests_per_day: float
