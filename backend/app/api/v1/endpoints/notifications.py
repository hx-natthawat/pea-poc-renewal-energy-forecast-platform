"""
Notification API endpoints.

Provides multi-channel notification delivery, user preferences,
and notification management.
Part of v1.1.0 Enhanced Alerting System feature.
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.security import CurrentUser, get_current_user, require_roles
from app.services.notification_service import (
    NotificationChannel,
    NotificationLanguage,
    NotificationPriority,
    NotificationRequest,
    NotificationService,
    get_notification_service,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Request/Response Models
# =============================================================================


class SendNotificationRequest(BaseModel):
    """Request to send a notification."""

    alert_id: str = Field(..., description="Unique alert identifier")
    alert_type: str = Field(..., description="Type of alert (voltage_violation, etc.)")
    severity: str = Field(default="warning", description="Alert severity")
    recipients: list[str] = Field(..., description="Email addresses for delivery")
    channels: list[str] = Field(
        default=["dashboard"],
        description="Notification channels: email, line, dashboard",
    )
    template_name: str = Field(..., description="Template to use for rendering")
    language: str = Field(default="th", description="Language: en or th")
    data: dict[str, Any] = Field(default_factory=dict, description="Template data")
    priority: str = Field(default="normal", description="Priority level")


class NotificationPreferencesRequest(BaseModel):
    """User notification preferences."""

    email_enabled: bool = True
    line_enabled: bool = True
    dashboard_enabled: bool = True
    preferred_language: str = "th"
    quiet_hours_start: int | None = Field(
        default=None, ge=0, le=23, description="Quiet hours start (0-23)"
    )
    quiet_hours_end: int | None = Field(
        default=None, ge=0, le=23, description="Quiet hours end (0-23)"
    )
    alert_types_email: list[str] = Field(
        default_factory=lambda: ["voltage_violation", "storm_warning"],
        description="Alert types to receive via email",
    )
    alert_types_line: list[str] = Field(
        default_factory=lambda: ["storm_warning", "critical"],
        description="Alert types to receive via LINE",
    )


class TestNotificationRequest(BaseModel):
    """Request to send a test notification."""

    channel: str = Field(..., description="Channel to test: email or line")
    recipient: str | None = Field(default=None, description="Test recipient")


# =============================================================================
# In-memory user preferences (replace with database in production)
# =============================================================================

_user_preferences: dict[str, dict] = {}


# =============================================================================
# Endpoints
# =============================================================================


@router.post("/send")
async def send_notification(
    request: SendNotificationRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser = Depends(require_roles(["admin", "operator"])),
    notification_service: NotificationService = Depends(get_notification_service),
) -> dict[str, Any]:
    """
    Send a notification through specified channels.

    **Requires roles:** admin or operator

    Sends notifications via email, LINE, and/or dashboard based on request.
    """
    logger.info(
        f"Notification request from {current_user.username}: "
        f"alert_id={request.alert_id}, channels={request.channels}"
    )

    # Convert string channels to enum
    try:
        channels = [NotificationChannel(ch) for ch in request.channels]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid channel: {e}")

    # Convert string language to enum
    try:
        language = NotificationLanguage(request.language)
    except ValueError:
        language = NotificationLanguage.TH

    # Convert string priority to enum
    try:
        priority = NotificationPriority(request.priority)
    except ValueError:
        priority = NotificationPriority.NORMAL

    # Create notification request
    notification_request = NotificationRequest(
        alert_id=request.alert_id,
        alert_type=request.alert_type,
        severity=request.severity,
        recipients=request.recipients,
        channels=channels,
        template_name=request.template_name,
        language=language,
        data=request.data,
        priority=priority,
    )

    # Send notification (could be async via background_tasks for email/LINE)
    result = notification_service.send(notification_request)

    return {
        "status": "success" if result.success else "partial_failure",
        "data": {
            "alert_id": result.alert_id,
            "channels_sent": [ch.value for ch in result.channels_sent],
            "channels_failed": [ch.value for ch in result.channels_failed],
            "errors": result.errors,
            "sent_at": result.sent_at.isoformat(),
        },
    }


@router.get("/dashboard")
async def get_dashboard_notifications(
    limit: int = 50,
    unread_only: bool = False,
    current_user: CurrentUser = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
) -> dict[str, Any]:
    """
    Get notifications for dashboard display.

    **Requires authentication**

    Returns recent notifications for the dashboard widget.
    """
    notifications = notification_service.get_dashboard_notifications(
        limit=limit,
        unread_only=unread_only,
    )

    return {
        "status": "success",
        "data": {
            "notifications": notifications,
            "count": len(notifications),
            "unread_count": sum(1 for n in notifications if not n.get("read")),
        },
    }


@router.post("/dashboard/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
) -> dict[str, Any]:
    """
    Mark a dashboard notification as read.

    **Requires authentication**
    """
    success = notification_service.mark_notification_read(notification_id)

    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")

    return {
        "status": "success",
        "data": {
            "notification_id": notification_id,
            "read": True,
        },
    }


@router.get("/preferences")
async def get_notification_preferences(
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get current user's notification preferences.

    **Requires authentication**
    """
    user_id = current_user.user_id

    # Get preferences or return defaults
    preferences = _user_preferences.get(user_id, {
        "email_enabled": True,
        "line_enabled": True,
        "dashboard_enabled": True,
        "preferred_language": "th",
        "quiet_hours_start": None,
        "quiet_hours_end": None,
        "alert_types_email": ["voltage_violation", "storm_warning"],
        "alert_types_line": ["storm_warning", "critical"],
    })

    return {
        "status": "success",
        "data": {
            "user_id": user_id,
            "preferences": preferences,
        },
    }


@router.put("/preferences")
async def update_notification_preferences(
    preferences: NotificationPreferencesRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Update current user's notification preferences.

    **Requires authentication**
    """
    user_id = current_user.user_id

    # Store preferences
    _user_preferences[user_id] = {
        "email_enabled": preferences.email_enabled,
        "line_enabled": preferences.line_enabled,
        "dashboard_enabled": preferences.dashboard_enabled,
        "preferred_language": preferences.preferred_language,
        "quiet_hours_start": preferences.quiet_hours_start,
        "quiet_hours_end": preferences.quiet_hours_end,
        "alert_types_email": preferences.alert_types_email,
        "alert_types_line": preferences.alert_types_line,
        "updated_at": datetime.now().isoformat(),
    }

    logger.info(f"Updated notification preferences for user {user_id}")

    return {
        "status": "success",
        "data": {
            "user_id": user_id,
            "preferences": _user_preferences[user_id],
            "message": "Preferences updated successfully",
        },
    }


@router.post("/test")
async def send_test_notification(
    request: TestNotificationRequest,
    current_user: CurrentUser = Depends(require_roles(["admin"])),
    notification_service: NotificationService = Depends(get_notification_service),
) -> dict[str, Any]:
    """
    Send a test notification to verify channel configuration.

    **Requires roles:** admin

    Sends a test message through the specified channel.
    """
    logger.info(f"Test notification requested by {current_user.username} for {request.channel}")

    # Create test notification
    test_request = NotificationRequest(
        alert_id=f"test-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        alert_type="test",
        severity="info",
        recipients=[request.recipient or current_user.email or "test@pea.co.th"],
        channels=[NotificationChannel(request.channel)],
        template_name="voltage_violation",  # Use existing template
        language=NotificationLanguage.TH,
        data={
            "prosumer_id": "TEST-001",
            "voltage": 245.5,
            "threshold": 242.0,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
        priority=NotificationPriority.LOW,
    )

    result = notification_service.send(test_request)

    return {
        "status": "success" if result.success else "failed",
        "data": {
            "channel": request.channel,
            "success": result.success,
            "errors": result.errors,
            "message": (
                "Test notification sent successfully"
                if result.success
                else f"Test failed: {result.errors}"
            ),
        },
    }


@router.get("/channels")
async def get_available_channels(
    current_user: CurrentUser = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
) -> dict[str, Any]:
    """
    Get available notification channels and their configuration status.

    **Requires authentication**
    """
    return {
        "status": "success",
        "data": {
            "channels": [
                {
                    "name": "email",
                    "enabled": notification_service.config.email_enabled,
                    "configured": notification_service.email_provider.is_configured,
                    "description": "Email notifications via SMTP",
                },
                {
                    "name": "line",
                    "enabled": notification_service.config.line_enabled,
                    "configured": notification_service.line_provider.is_configured,
                    "description": "LINE Notify instant messaging",
                },
                {
                    "name": "dashboard",
                    "enabled": notification_service.config.dashboard_enabled,
                    "configured": True,
                    "description": "In-app dashboard notifications",
                },
            ],
        },
    }


@router.get("/templates")
async def get_available_templates(
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get available notification templates.

    **Requires authentication**
    """
    from app.services.notification_service import ALERT_TEMPLATES

    templates = []
    for name, lang_templates in ALERT_TEMPLATES.items():
        templates.append({
            "name": name,
            "languages": list(lang_templates.keys()),
            "description": name.replace("_", " ").title(),
        })

    return {
        "status": "success",
        "data": {
            "templates": templates,
            "count": len(templates),
        },
    }
