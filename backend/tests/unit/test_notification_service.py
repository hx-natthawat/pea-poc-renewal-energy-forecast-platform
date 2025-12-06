"""
Unit tests for the notification service.

Tests cover email provider, LINE provider, and the main notification service.
"""

from app.services.notification_service import (
    ALERT_TEMPLATES,
    NotificationChannel,
    NotificationConfig,
    NotificationLanguage,
    NotificationPriority,
    NotificationRequest,
    NotificationService,
    get_notification_service,
)
from app.services.providers.email_provider import (
    EmailConfig,
    EmailMessage,
    EmailProvider,
    get_email_provider,
)
from app.services.providers.line_provider import (
    LineConfig,
    LineMessage,
    LineProvider,
    get_line_provider,
)

# =============================================================================
# Email Provider Tests
# =============================================================================


class TestEmailProvider:
    """Tests for EmailProvider class."""

    def test_email_provider_initialization(self):
        """Test email provider initializes with default config."""
        provider = EmailProvider()
        assert provider.config is not None
        assert provider.config.smtp_host == "smtp.gmail.com"
        assert provider.config.smtp_port == 587

    def test_email_provider_unconfigured(self):
        """Test that unconfigured provider reports not configured."""
        config = EmailConfig(smtp_user="", smtp_password="")
        provider = EmailProvider(config)
        assert provider.is_configured is False

    def test_email_provider_configured(self):
        """Test that configured provider reports configured."""
        config = EmailConfig(smtp_user="user@test.com", smtp_password="password")
        provider = EmailProvider(config)
        assert provider.is_configured is True

    def test_email_simulate_send(self):
        """Test simulated email send for unconfigured provider."""
        provider = EmailProvider()  # Unconfigured
        message = EmailMessage(
            to=["test@example.com"],
            subject="Test Subject",
            body_html="<p>Test body</p>",
        )
        result = provider.send(message)
        assert result.success is True
        assert "simulated" in result.message_id.lower()
        assert "test@example.com" in result.recipients_sent

    def test_email_send_alert_convenience(self):
        """Test send_alert convenience method."""
        provider = EmailProvider()
        result = provider.send_alert(
            recipients=["test@example.com"],
            subject="Alert Test",
            body_html="<p>Alert content</p>",
        )
        assert result.success is True

    def test_email_message_with_cc_bcc(self):
        """Test email message with CC and BCC recipients."""
        provider = EmailProvider()
        message = EmailMessage(
            to=["main@example.com"],
            subject="Test",
            body_html="<p>Body</p>",
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
        )
        result = provider.send(message)
        assert "main@example.com" in result.recipients_sent
        assert "cc@example.com" in result.recipients_sent
        assert "bcc@example.com" in result.recipients_sent


# =============================================================================
# LINE Provider Tests
# =============================================================================


class TestLineProvider:
    """Tests for LineProvider class."""

    def test_line_provider_initialization(self):
        """Test LINE provider initializes with default config."""
        provider = LineProvider()
        assert provider.config is not None
        assert provider.config.timeout_seconds == 10
        assert provider.config.max_retries == 3

    def test_line_provider_unconfigured(self):
        """Test that unconfigured provider reports not configured."""
        config = LineConfig(access_token="")
        provider = LineProvider(config)
        assert provider.is_configured is False

    def test_line_provider_configured(self):
        """Test that configured provider reports configured."""
        config = LineConfig(access_token="test-token-123")
        provider = LineProvider(config)
        assert provider.is_configured is True

    def test_line_simulate_send(self):
        """Test simulated LINE send for unconfigured provider."""
        provider = LineProvider()  # Unconfigured
        message = LineMessage(message="Test notification")
        result = provider.send(message)
        assert result.success is True
        assert result.status_code == 200

    def test_line_send_alert_convenience(self):
        """Test send_alert convenience method."""
        provider = LineProvider()
        result = provider.send_alert(message="Test alert message")
        assert result.success is True

    def test_line_message_with_image(self):
        """Test LINE message with image attachment."""
        provider = LineProvider()
        message = LineMessage(
            message="Test with image",
            image_url="https://example.com/image.png",
        )
        result = provider.send(message)
        assert result.success is True

    def test_line_message_with_sticker(self):
        """Test LINE message with sticker."""
        provider = LineProvider()
        message = LineMessage(
            message="Test with sticker",
            sticker_package_id=1,
            sticker_id=1,
        )
        result = provider.send(message)
        assert result.success is True

    def test_line_build_payload(self):
        """Test LINE message payload building."""
        provider = LineProvider()
        message = LineMessage(
            message="Test message",
            image_url="https://example.com/img.png",
            sticker_package_id=1,
            sticker_id=2,
        )
        payload = provider._build_payload(message)
        assert payload["message"] == "Test message"
        assert "imageThumbnail" in payload
        assert "imageFullsize" in payload
        assert payload["stickerPackageId"] == 1
        assert payload["stickerId"] == 2


# =============================================================================
# Notification Service Tests
# =============================================================================


class TestNotificationService:
    """Tests for NotificationService class."""

    def test_notification_service_initialization(self):
        """Test notification service initializes with default config."""
        service = NotificationService()
        assert service.config is not None
        assert service.config.default_language == NotificationLanguage.TH
        assert service.config.email_enabled is True
        assert service.config.line_enabled is True

    def test_notification_service_custom_config(self):
        """Test notification service with custom configuration."""
        config = NotificationConfig(
            default_language=NotificationLanguage.EN,
            email_enabled=False,
        )
        service = NotificationService(config=config)
        assert service.config.default_language == NotificationLanguage.EN
        assert service.config.email_enabled is False

    def test_send_dashboard_notification(self):
        """Test sending notification to dashboard channel."""
        service = NotificationService()
        request = NotificationRequest(
            alert_id="test-001",
            alert_type="voltage_violation",
            severity="warning",
            recipients=[],
            channels=[NotificationChannel.DASHBOARD],
            template_name="voltage_violation",
            data={
                "prosumer_id": "prosumer1",
                "voltage": 245.5,
                "threshold": 242.0,
                "timestamp": "2025-01-15 10:00:00",
            },
        )
        result = service.send(request)
        assert result.success is True
        assert NotificationChannel.DASHBOARD in result.channels_sent

    def test_send_email_notification(self):
        """Test sending notification via email channel."""
        service = NotificationService()
        request = NotificationRequest(
            alert_id="test-002",
            alert_type="voltage_violation",
            severity="warning",
            recipients=["test@example.com"],
            channels=[NotificationChannel.EMAIL],
            template_name="voltage_violation",
            data={
                "prosumer_id": "prosumer1",
                "voltage": 245.5,
                "threshold": 242.0,
                "timestamp": "2025-01-15 10:00:00",
            },
        )
        result = service.send(request)
        assert result.success is True
        assert NotificationChannel.EMAIL in result.channels_sent

    def test_send_line_notification(self):
        """Test sending notification via LINE channel."""
        service = NotificationService()
        request = NotificationRequest(
            alert_id="test-003",
            alert_type="storm_warning",
            severity="critical",
            recipients=[],
            channels=[NotificationChannel.LINE],
            template_name="storm_warning",
            data={
                "region": "Central Thailand",
                "severity": "high",
                "duration_hours": 2,
                "description": "Heavy thunderstorm expected",
            },
        )
        result = service.send(request)
        assert result.success is True
        assert NotificationChannel.LINE in result.channels_sent

    def test_send_multi_channel_notification(self):
        """Test sending notification to multiple channels."""
        service = NotificationService()
        request = NotificationRequest(
            alert_id="test-004",
            alert_type="voltage_violation",
            severity="critical",
            recipients=["test@example.com"],
            channels=[
                NotificationChannel.EMAIL,
                NotificationChannel.LINE,
                NotificationChannel.DASHBOARD,
            ],
            template_name="voltage_violation",
            data={
                "prosumer_id": "prosumer1",
                "voltage": 250.0,
                "threshold": 242.0,
                "timestamp": "2025-01-15 10:00:00",
            },
        )
        result = service.send(request)
        assert result.success is True
        assert len(result.channels_sent) == 3

    def test_dashboard_notification_storage(self):
        """Test that dashboard notifications are stored correctly."""
        service = NotificationService()
        request = NotificationRequest(
            alert_id="test-005",
            alert_type="ramp_rate_exceeded",
            severity="warning",
            recipients=[],
            channels=[NotificationChannel.DASHBOARD],
            template_name="ramp_rate_exceeded",
            data={
                "station_id": "station1",
                "ramp_rate": 35.5,
                "time_window": 5,
                "direction": "down",
                "timestamp": "2025-01-15 10:00:00",
            },
        )
        service.send(request)

        notifications = service.get_dashboard_notifications()
        assert len(notifications) >= 1
        assert any(n["id"] == "test-005" for n in notifications)

    def test_mark_notification_read(self):
        """Test marking a notification as read."""
        service = NotificationService()
        request = NotificationRequest(
            alert_id="test-006",
            alert_type="test",
            severity="info",
            recipients=[],
            channels=[NotificationChannel.DASHBOARD],
            template_name="voltage_violation",
            data={
                "prosumer_id": "test",
                "voltage": 230,
                "threshold": 242,
                "timestamp": "now",
            },
        )
        service.send(request)

        # Mark as read
        result = service.mark_notification_read("test-006")
        assert result is True

        # Verify it's marked as read
        notifications = service.get_dashboard_notifications(unread_only=True)
        assert not any(n["id"] == "test-006" for n in notifications)

    def test_get_unread_notifications_only(self):
        """Test filtering for unread notifications."""
        service = NotificationService()

        # Send notification
        request = NotificationRequest(
            alert_id="test-007",
            alert_type="test",
            severity="info",
            recipients=[],
            channels=[NotificationChannel.DASHBOARD],
            template_name="voltage_violation",
            data={
                "prosumer_id": "test",
                "voltage": 230,
                "threshold": 242,
                "timestamp": "now",
            },
        )
        service.send(request)

        # Get unread
        unread = service.get_dashboard_notifications(unread_only=True)
        assert any(n["id"] == "test-007" for n in unread)


# =============================================================================
# Template Tests
# =============================================================================


class TestAlertTemplates:
    """Tests for alert template rendering."""

    def test_all_templates_have_both_languages(self):
        """Test that all templates have both English and Thai versions."""
        for template_name, lang_templates in ALERT_TEMPLATES.items():
            assert "en" in lang_templates, f"{template_name} missing English"
            assert "th" in lang_templates, f"{template_name} missing Thai"

    def test_all_templates_have_required_fields(self):
        """Test that all templates have subject, body, and line fields."""
        for template_name, lang_templates in ALERT_TEMPLATES.items():
            for lang, template in lang_templates.items():
                assert "subject" in template, f"{template_name}/{lang} missing subject"
                assert "body" in template, f"{template_name}/{lang} missing body"
                assert "line" in template, f"{template_name}/{lang} missing line"

    def test_voltage_violation_template_rendering(self):
        """Test voltage violation template renders correctly."""
        service = NotificationService()
        request = NotificationRequest(
            alert_id="test-template-1",
            alert_type="voltage_violation",
            severity="warning",
            recipients=["test@example.com"],
            channels=[NotificationChannel.EMAIL],
            template_name="voltage_violation",
            language=NotificationLanguage.EN,
            data={
                "prosumer_id": "PROSUMER-001",
                "voltage": 245.5,
                "threshold": 242.0,
                "timestamp": "2025-01-15 10:00:00",
            },
        )
        # The send will use fallback rendering
        result = service.send(request)
        assert result.success is True

    def test_storm_warning_template_thai(self):
        """Test storm warning template in Thai."""
        service = NotificationService()
        request = NotificationRequest(
            alert_id="test-template-2",
            alert_type="storm_warning",
            severity="critical",
            recipients=[],
            channels=[NotificationChannel.DASHBOARD],
            template_name="storm_warning",
            language=NotificationLanguage.TH,
            data={
                "region": "ภาคกลาง",
                "severity": "สูง",
                "duration_hours": 3,
                "description": "พายุฝนฟ้าคะนอง",
            },
        )
        result = service.send(request)
        assert result.success is True


# =============================================================================
# Singleton Tests
# =============================================================================


class TestSingletonInstances:
    """Tests for singleton pattern implementations."""

    def test_email_provider_singleton(self):
        """Test email provider singleton returns same instance."""
        provider1 = get_email_provider()
        provider2 = get_email_provider()
        assert provider1 is provider2

    def test_line_provider_singleton(self):
        """Test LINE provider singleton returns same instance."""
        provider1 = get_line_provider()
        provider2 = get_line_provider()
        assert provider1 is provider2

    def test_notification_service_singleton(self):
        """Test notification service singleton returns same instance."""
        service1 = get_notification_service()
        service2 = get_notification_service()
        assert service1 is service2


# =============================================================================
# Priority Tests
# =============================================================================


class TestNotificationPriority:
    """Tests for notification priority handling."""

    def test_notification_with_critical_priority(self):
        """Test sending notification with critical priority."""
        service = NotificationService()
        request = NotificationRequest(
            alert_id="test-priority-1",
            alert_type="storm_warning",
            severity="critical",
            recipients=[],
            channels=[NotificationChannel.DASHBOARD],
            template_name="storm_warning",
            priority=NotificationPriority.CRITICAL,
            data={
                "region": "Central",
                "severity": "critical",
                "duration_hours": 1,
                "description": "Severe storm",
            },
        )
        service.send(request)

        notifications = service.get_dashboard_notifications()
        notification = next(n for n in notifications if n["id"] == "test-priority-1")
        assert notification["priority"] == "critical"

    def test_notification_default_priority(self):
        """Test that default priority is normal."""
        request = NotificationRequest(
            alert_id="test-priority-2",
            alert_type="test",
            severity="info",
            recipients=[],
            channels=[NotificationChannel.DASHBOARD],
            template_name="voltage_violation",
            data={
                "prosumer_id": "test",
                "voltage": 230,
                "threshold": 242,
                "timestamp": "now",
            },
        )
        assert request.priority == NotificationPriority.NORMAL
