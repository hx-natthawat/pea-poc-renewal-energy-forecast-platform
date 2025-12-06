"""
Unit tests for notification API endpoints.

Tests notification models and endpoints.
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints.notifications import (
    NotificationPreferencesRequest,
    SendNotificationRequest,
    TestNotificationRequest,
)
from app.core.security import CurrentUser
from app.services.notification_service import (
    NotificationChannel,
    NotificationLanguage,
    NotificationPriority,
    NotificationResult,
)


class TestSendNotificationRequest:
    """Test SendNotificationRequest model."""

    def test_create_request(self):
        """Test creating a notification request."""
        request = SendNotificationRequest(
            alert_id="alert-123",
            alert_type="voltage_violation",
            severity="warning",
            recipients=["user@example.com"],
            channels=["email", "dashboard"],
            template_name="voltage_violation",
            language="th",
            data={"voltage": 245.0},
            priority="high",
        )
        assert request.alert_id == "alert-123"
        assert request.alert_type == "voltage_violation"
        assert request.severity == "warning"
        assert request.recipients == ["user@example.com"]
        assert request.channels == ["email", "dashboard"]
        assert request.template_name == "voltage_violation"
        assert request.language == "th"
        assert request.priority == "high"

    def test_default_values(self):
        """Test default values."""
        request = SendNotificationRequest(
            alert_id="alert-123",
            alert_type="test",
            recipients=["user@example.com"],
            template_name="test",
        )
        assert request.severity == "warning"
        assert request.channels == ["dashboard"]
        assert request.language == "th"
        assert request.priority == "normal"
        assert request.data == {}


class TestNotificationPreferencesRequest:
    """Test NotificationPreferencesRequest model."""

    def test_create_preferences(self):
        """Test creating preferences."""
        prefs = NotificationPreferencesRequest(
            email_enabled=True,
            line_enabled=False,
            dashboard_enabled=True,
            preferred_language="en",
            quiet_hours_start=22,
            quiet_hours_end=8,
        )
        assert prefs.email_enabled is True
        assert prefs.line_enabled is False
        assert prefs.preferred_language == "en"
        assert prefs.quiet_hours_start == 22
        assert prefs.quiet_hours_end == 8

    def test_default_preferences(self):
        """Test default preferences."""
        prefs = NotificationPreferencesRequest()
        assert prefs.email_enabled is True
        assert prefs.line_enabled is True
        assert prefs.dashboard_enabled is True
        assert prefs.preferred_language == "th"
        assert prefs.quiet_hours_start is None
        assert prefs.quiet_hours_end is None


class TestTestNotificationRequest:
    """Test TestNotificationRequest model."""

    def test_create_test_request(self):
        """Test creating a test notification request."""
        request = TestNotificationRequest(
            channel="email",
            recipient="test@example.com",
        )
        assert request.channel == "email"
        assert request.recipient == "test@example.com"

    def test_optional_recipient(self):
        """Test optional recipient."""
        request = TestNotificationRequest(channel="line")
        assert request.channel == "line"
        assert request.recipient is None


class TestNotificationChannel:
    """Test NotificationChannel enum."""

    def test_email_channel(self):
        assert NotificationChannel.EMAIL.value == "email"

    def test_line_channel(self):
        assert NotificationChannel.LINE.value == "line"

    def test_dashboard_channel(self):
        assert NotificationChannel.DASHBOARD.value == "dashboard"


class TestNotificationLanguage:
    """Test NotificationLanguage enum."""

    def test_thai_language(self):
        assert NotificationLanguage.TH.value == "th"

    def test_english_language(self):
        assert NotificationLanguage.EN.value == "en"


class TestNotificationPriority:
    """Test NotificationPriority enum."""

    def test_low_priority(self):
        assert NotificationPriority.LOW.value == "low"

    def test_normal_priority(self):
        assert NotificationPriority.NORMAL.value == "normal"

    def test_high_priority(self):
        assert NotificationPriority.HIGH.value == "high"

    def test_critical_priority(self):
        assert NotificationPriority.CRITICAL.value == "critical"


class TestSendNotification:
    """Test send_notification endpoint."""

    @pytest.mark.asyncio
    async def test_send_notification_success(self):
        """Test sending notification successfully."""
        from app.api.v1.endpoints.notifications import send_notification

        mock_service = MagicMock()
        mock_result = MagicMock(spec=NotificationResult)
        mock_result.success = True
        mock_result.alert_id = "alert-123"
        mock_result.channels_sent = [NotificationChannel.DASHBOARD]
        mock_result.channels_failed = []
        mock_result.errors = []
        mock_result.sent_at = datetime(2025, 1, 1)
        mock_service.send.return_value = mock_result

        request = SendNotificationRequest(
            alert_id="alert-123",
            alert_type="voltage_violation",
            recipients=["user@example.com"],
            channels=["dashboard"],
            template_name="voltage_violation",
        )

        result = await send_notification(
            request=request,
            background_tasks=MagicMock(),
            current_user=CurrentUser(id="admin-1", username="admin", roles=["admin"]),
            notification_service=mock_service,
        )

        assert result["status"] == "success"
        assert result["data"]["alert_id"] == "alert-123"
        assert "dashboard" in result["data"]["channels_sent"]

    @pytest.mark.asyncio
    async def test_send_notification_invalid_channel(self):
        """Test sending notification with invalid channel."""
        from app.api.v1.endpoints.notifications import send_notification

        mock_service = MagicMock()

        request = SendNotificationRequest(
            alert_id="alert-123",
            alert_type="test",
            recipients=["user@example.com"],
            channels=["invalid_channel"],
            template_name="test",
        )

        with pytest.raises(HTTPException) as exc_info:
            await send_notification(
                request=request,
                background_tasks=MagicMock(),
                current_user=CurrentUser(
                    id="admin-1", username="admin", roles=["admin"]
                ),
                notification_service=mock_service,
            )

        assert exc_info.value.status_code == 400


class TestGetDashboardNotifications:
    """Test get_dashboard_notifications endpoint."""

    @pytest.mark.asyncio
    async def test_get_notifications(self):
        """Test getting dashboard notifications."""
        from app.api.v1.endpoints.notifications import get_dashboard_notifications

        mock_service = MagicMock()
        mock_service.get_dashboard_notifications.return_value = [
            {"id": "1", "message": "Test", "read": False},
            {"id": "2", "message": "Test 2", "read": True},
        ]

        result = await get_dashboard_notifications(
            limit=50,
            unread_only=False,
            current_user=CurrentUser(id="user-1", roles=["viewer"]),
            notification_service=mock_service,
        )

        assert result["status"] == "success"
        assert result["data"]["count"] == 2
        assert result["data"]["unread_count"] == 1


class TestMarkNotificationRead:
    """Test mark_notification_read endpoint."""

    @pytest.mark.asyncio
    async def test_mark_read_success(self):
        """Test marking notification as read."""
        from app.api.v1.endpoints.notifications import mark_notification_read

        mock_service = MagicMock()
        mock_service.mark_notification_read.return_value = True

        result = await mark_notification_read(
            notification_id="notification-123",
            current_user=CurrentUser(id="user-1", roles=["viewer"]),
            notification_service=mock_service,
        )

        assert result["status"] == "success"
        assert result["data"]["notification_id"] == "notification-123"
        assert result["data"]["read"] is True

    @pytest.mark.asyncio
    async def test_mark_read_not_found(self):
        """Test marking non-existent notification."""
        from app.api.v1.endpoints.notifications import mark_notification_read

        mock_service = MagicMock()
        mock_service.mark_notification_read.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            await mark_notification_read(
                notification_id="non-existent",
                current_user=CurrentUser(id="user-1", roles=["viewer"]),
                notification_service=mock_service,
            )

        assert exc_info.value.status_code == 404


class TestGetAvailableTemplates:
    """Test get_available_templates endpoint."""

    @pytest.mark.asyncio
    async def test_get_templates(self):
        """Test getting available templates."""
        from app.api.v1.endpoints.notifications import get_available_templates

        result = await get_available_templates(
            current_user=CurrentUser(id="user-1", roles=["viewer"]),
        )

        assert result["status"] == "success"
        assert "templates" in result["data"]
        assert "count" in result["data"]


class TestGetAvailableChannels:
    """Test get_available_channels endpoint."""

    @pytest.mark.asyncio
    async def test_get_channels(self):
        """Test getting available channels."""
        from app.api.v1.endpoints.notifications import get_available_channels

        mock_service = MagicMock()
        mock_service.config.email_enabled = True
        mock_service.config.line_enabled = True
        mock_service.config.dashboard_enabled = True
        mock_service.email_provider.is_configured = True
        mock_service.line_provider.is_configured = False

        result = await get_available_channels(
            current_user=CurrentUser(id="user-1", roles=["viewer"]),
            notification_service=mock_service,
        )

        assert result["status"] == "success"
        assert len(result["data"]["channels"]) == 3

        email_channel = next(
            c for c in result["data"]["channels"] if c["name"] == "email"
        )
        assert email_channel["enabled"] is True
        assert email_channel["configured"] is True

        line_channel = next(
            c for c in result["data"]["channels"] if c["name"] == "line"
        )
        assert line_channel["configured"] is False


class TestSendTestNotification:
    """Test send_test_notification endpoint."""

    @pytest.mark.asyncio
    async def test_send_test_success(self):
        """Test sending test notification successfully."""
        from app.api.v1.endpoints.notifications import send_test_notification

        mock_service = MagicMock()
        mock_result = MagicMock(spec=NotificationResult)
        mock_result.success = True
        mock_result.errors = []
        mock_service.send.return_value = mock_result

        request = TestNotificationRequest(
            channel="dashboard",
            recipient="test@example.com",
        )

        result = await send_test_notification(
            request=request,
            current_user=CurrentUser(
                id="admin-1",
                username="admin",
                email="admin@example.com",
                roles=["admin"],
            ),
            notification_service=mock_service,
        )

        assert result["status"] == "success"
        assert result["data"]["channel"] == "dashboard"
        assert result["data"]["success"] is True

    @pytest.mark.asyncio
    async def test_send_test_failure(self):
        """Test sending test notification that fails."""
        from app.api.v1.endpoints.notifications import send_test_notification

        mock_service = MagicMock()
        mock_result = MagicMock(spec=NotificationResult)
        mock_result.success = False
        mock_result.errors = ["Connection failed"]
        mock_service.send.return_value = mock_result

        request = TestNotificationRequest(
            channel="email",
        )

        result = await send_test_notification(
            request=request,
            current_user=CurrentUser(
                id="admin-1",
                username="admin",
                roles=["admin"],
            ),
            notification_service=mock_service,
        )

        assert result["status"] == "failed"
        assert result["data"]["success"] is False
        assert "Connection failed" in result["data"]["errors"]
