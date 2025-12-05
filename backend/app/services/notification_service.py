"""
Notification Service for multi-channel alert delivery.

Orchestrates email and LINE notifications with template rendering,
user preferences, and delivery tracking.
Part of v1.1.0 Enhanced Alerting System feature.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.services.providers.email_provider import (
    EmailConfig,
    EmailProvider,
    EmailResult,
    get_email_provider,
)
from app.services.providers.line_provider import (
    LineConfig,
    LineProvider,
    LineResult,
    get_line_provider,
)

logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    """Available notification channels."""

    EMAIL = "email"
    LINE = "line"
    DASHBOARD = "dashboard"
    WEBHOOK = "webhook"


class NotificationPriority(str, Enum):
    """Notification priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationLanguage(str, Enum):
    """Supported notification languages."""

    EN = "en"
    TH = "th"


@dataclass
class NotificationConfig:
    """Notification service configuration."""

    templates_dir: str = "app/templates/alerts"
    default_language: NotificationLanguage = NotificationLanguage.TH
    default_channels: list[NotificationChannel] = field(
        default_factory=lambda: [NotificationChannel.DASHBOARD]
    )
    email_enabled: bool = True
    line_enabled: bool = True
    dashboard_enabled: bool = True


@dataclass
class NotificationRequest:
    """Request to send a notification."""

    alert_id: str
    alert_type: str
    severity: str
    recipients: list[str]
    channels: list[NotificationChannel]
    template_name: str
    language: NotificationLanguage = NotificationLanguage.TH
    data: dict[str, Any] = field(default_factory=dict)
    priority: NotificationPriority = NotificationPriority.NORMAL


@dataclass
class NotificationResult:
    """Result of notification delivery."""

    success: bool
    alert_id: str
    channels_sent: list[NotificationChannel] = field(default_factory=list)
    channels_failed: list[NotificationChannel] = field(default_factory=list)
    errors: dict[str, str] = field(default_factory=dict)
    sent_at: datetime = field(default_factory=datetime.now)


class NotificationService:
    """
    Multi-channel notification service.

    Features:
    - Template-based message rendering (Jinja2)
    - Bilingual support (Thai/English)
    - Multiple delivery channels (Email, LINE, Dashboard)
    - Priority-based delivery
    - Delivery tracking
    """

    def __init__(
        self,
        config: NotificationConfig | None = None,
        email_provider: EmailProvider | None = None,
        line_provider: LineProvider | None = None,
    ):
        """Initialize notification service."""
        self.config = config or NotificationConfig()
        self.email_provider = email_provider or get_email_provider()
        self.line_provider = line_provider or get_line_provider()

        # Initialize template engine
        templates_path = Path(self.config.templates_dir)
        self._jinja_env: Environment | None = None
        if templates_path.exists():
            self._jinja_env = Environment(
                loader=FileSystemLoader(str(templates_path)),
                autoescape=select_autoescape(["html", "xml"]),
            )
        else:
            logger.warning(f"Templates directory not found: {templates_path}")

        # In-memory notification log (for dashboard delivery)
        self._dashboard_notifications: list[dict] = []

    def send(self, request: NotificationRequest) -> NotificationResult:
        """
        Send notification through specified channels.

        Args:
            request: NotificationRequest with recipients and content

        Returns:
            NotificationResult with delivery status per channel
        """
        result = NotificationResult(
            success=True,
            alert_id=request.alert_id,
        )

        # Render templates
        subject, body_html, body_text, line_message = self._render_templates(
            request.template_name,
            request.language,
            request.data,
        )

        # Send through each channel
        for channel in request.channels:
            try:
                if channel == NotificationChannel.EMAIL and self.config.email_enabled:
                    email_result = self._send_email(
                        request.recipients,
                        subject,
                        body_html,
                        body_text,
                    )
                    if email_result.success:
                        result.channels_sent.append(channel)
                    else:
                        result.channels_failed.append(channel)
                        result.errors[channel.value] = email_result.error or "Unknown error"

                elif channel == NotificationChannel.LINE and self.config.line_enabled:
                    line_result = self._send_line(line_message)
                    if line_result.success:
                        result.channels_sent.append(channel)
                    else:
                        result.channels_failed.append(channel)
                        result.errors[channel.value] = line_result.error or "Unknown error"

                elif channel == NotificationChannel.DASHBOARD and self.config.dashboard_enabled:
                    self._send_dashboard(request, body_text)
                    result.channels_sent.append(channel)

            except Exception as e:
                logger.error(f"Failed to send via {channel}: {e}")
                result.channels_failed.append(channel)
                result.errors[channel.value] = str(e)

        # Overall success if at least one channel succeeded
        result.success = len(result.channels_sent) > 0

        return result

    def _render_templates(
        self,
        template_name: str,
        language: NotificationLanguage,
        data: dict[str, Any],
    ) -> tuple[str, str, str, str]:
        """
        Render notification templates.

        Returns:
            Tuple of (subject, body_html, body_text, line_message)
        """
        # Add common context
        context = {
            **data,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "language": language.value,
        }

        # Try to load templates
        if self._jinja_env:
            try:
                # Email HTML template
                html_template = self._jinja_env.get_template(
                    f"{template_name}_{language.value}.html"
                )
                body_html = html_template.render(**context)

                # Email text template
                text_template = self._jinja_env.get_template(
                    f"{template_name}_{language.value}.txt"
                )
                body_text = text_template.render(**context)

                # Subject from template or generate
                subject = self._get_subject(template_name, language, data)

                # LINE message (shorter format)
                line_message = self._format_line_message(template_name, language, data)

                return subject, body_html, body_text, line_message

            except Exception as e:
                logger.warning(f"Template rendering failed: {e}, using fallback")

        # Fallback rendering
        return self._render_fallback(template_name, language, data)

    def _render_fallback(
        self,
        template_name: str,
        language: NotificationLanguage,
        data: dict[str, Any],
    ) -> tuple[str, str, str, str]:
        """Fallback template rendering when templates not available."""
        templates = ALERT_TEMPLATES.get(template_name, {})
        template = templates.get(language.value, templates.get("en", {}))

        subject = template.get("subject", "PEA Alert").format(**data)
        body = template.get("body", "Alert: {alert_type}").format(**data)

        body_html = f"<html><body><pre>{body}</pre></body></html>"
        line_message = template.get("line", body[:200])

        if isinstance(line_message, str):
            line_message = line_message.format(**data)

        return subject, body_html, body, line_message

    def _get_subject(
        self,
        template_name: str,
        language: NotificationLanguage,
        data: dict[str, Any],
    ) -> str:
        """Get email subject for template."""
        subjects = {
            "voltage_violation": {
                "en": "Alert: Voltage Limit Exceeded at {prosumer_id}",
                "th": "แจ้งเตือน: แรงดันไฟฟ้าเกินขีดจำกัด ที่ {prosumer_id}",
            },
            "solar_forecast_deviation": {
                "en": "Alert: Solar Forecast Deviation Detected",
                "th": "แจ้งเตือน: ค่าพยากรณ์พลังงานแสงอาทิตย์เบี่ยงเบน",
            },
            "ramp_rate_exceeded": {
                "en": "Alert: Rapid Power Change Detected",
                "th": "แจ้งเตือน: ตรวจพบการเปลี่ยนแปลงกำลังไฟฟ้าอย่างรวดเร็ว",
            },
            "storm_warning": {
                "en": "Critical: Storm Warning Active",
                "th": "วิกฤต: แจ้งเตือนพายุ",
            },
            "model_drift_detected": {
                "en": "Alert: Model Performance Drift Detected",
                "th": "แจ้งเตือน: ตรวจพบการเบี่ยงเบนของโมเดล",
            },
        }

        template_subjects = subjects.get(template_name, {})
        subject_template = template_subjects.get(
            language.value,
            template_subjects.get("en", "PEA Alert"),
        )

        return subject_template.format(**data)

    def _format_line_message(
        self,
        template_name: str,
        language: NotificationLanguage,
        data: dict[str, Any],
    ) -> str:
        """Format message for LINE (shorter format)."""
        templates = ALERT_TEMPLATES.get(template_name, {})
        template = templates.get(language.value, templates.get("en", {}))
        line_template = template.get("line", "Alert: {alert_type}")
        return line_template.format(**data)

    def _send_email(
        self,
        recipients: list[str],
        subject: str,
        body_html: str,
        body_text: str,
    ) -> EmailResult:
        """Send email notification."""
        return self.email_provider.send_alert(
            recipients=recipients,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
        )

    def _send_line(self, message: str) -> LineResult:
        """Send LINE notification."""
        return self.line_provider.send_alert(message=message)

    def _send_dashboard(
        self,
        request: NotificationRequest,
        body: str,
    ) -> None:
        """Store notification for dashboard delivery via WebSocket."""
        notification = {
            "id": request.alert_id,
            "type": request.alert_type,
            "severity": request.severity,
            "message": body,
            "priority": request.priority.value,
            "timestamp": datetime.now().isoformat(),
            "read": False,
        }
        self._dashboard_notifications.append(notification)
        logger.info(f"Dashboard notification stored: {request.alert_id}")

    def get_dashboard_notifications(
        self,
        limit: int = 50,
        unread_only: bool = False,
    ) -> list[dict]:
        """Get notifications for dashboard display."""
        notifications = self._dashboard_notifications
        if unread_only:
            notifications = [n for n in notifications if not n.get("read")]
        return sorted(
            notifications,
            key=lambda x: x["timestamp"],
            reverse=True,
        )[:limit]

    def mark_notification_read(self, notification_id: str) -> bool:
        """Mark a notification as read."""
        for notification in self._dashboard_notifications:
            if notification["id"] == notification_id:
                notification["read"] = True
                return True
        return False


# Alert templates (fallback when file templates not available)
ALERT_TEMPLATES = {
    "voltage_violation": {
        "en": {
            "subject": "Alert: Voltage Limit Exceeded at {prosumer_id}",
            "body": """
VOLTAGE VIOLATION ALERT

Location: {prosumer_id}
Current Voltage: {voltage} V
Threshold: {threshold} V
Time: {timestamp}

Please investigate and take corrective action.

--
PEA RE Forecast Platform
            """,
            "line": """
Voltage Alert

{prosumer_id}: {voltage}V (limit: {threshold}V)
Time: {timestamp}
""",
        },
        "th": {
            "subject": "แจ้งเตือน: แรงดันไฟฟ้าเกินขีดจำกัด ที่ {prosumer_id}",
            "body": """
แจ้งเตือนแรงดันไฟฟ้าเกินขีดจำกัด

สถานที่: {prosumer_id}
แรงดันปัจจุบัน: {voltage} V
ขีดจำกัด: {threshold} V
เวลา: {timestamp}

กรุณาตรวจสอบและดำเนินการแก้ไข

--
แพลตฟอร์มพยากรณ์พลังงานหมุนเวียน กฟภ.
            """,
            "line": """
แจ้งเตือนแรงดัน

{prosumer_id}: {voltage}V (จำกัด: {threshold}V)
เวลา: {timestamp}
""",
        },
    },
    "solar_forecast_deviation": {
        "en": {
            "subject": "Alert: Solar Forecast Deviation",
            "body": """
SOLAR FORECAST DEVIATION ALERT

Station: {station_id}
Predicted: {predicted_kw} kW
Actual: {actual_kw} kW
Deviation: {deviation_pct}%
Time: {timestamp}

The forecast model may need recalibration.

--
PEA RE Forecast Platform
            """,
            "line": """
Solar Forecast Alert

Station: {station_id}
Deviation: {deviation_pct}%
Predicted: {predicted_kw} kW
Actual: {actual_kw} kW
""",
        },
        "th": {
            "subject": "แจ้งเตือน: ค่าพยากรณ์พลังงานแสงอาทิตย์เบี่ยงเบน",
            "body": """
แจ้งเตือนค่าพยากรณ์เบี่ยงเบน

สถานี: {station_id}
ค่าพยากรณ์: {predicted_kw} kW
ค่าจริง: {actual_kw} kW
ความเบี่ยงเบน: {deviation_pct}%
เวลา: {timestamp}

โมเดลอาจต้องปรับเทียบใหม่

--
แพลตฟอร์มพยากรณ์พลังงานหมุนเวียน กฟภ.
            """,
            "line": """
แจ้งเตือนพยากรณ์

สถานี: {station_id}
ความเบี่ยงเบน: {deviation_pct}%
พยากรณ์: {predicted_kw} kW
จริง: {actual_kw} kW
""",
        },
    },
    "ramp_rate_exceeded": {
        "en": {
            "subject": "Alert: Rapid Power Change Detected",
            "body": """
RAMP RATE ALERT

Station: {station_id}
Ramp Rate: {ramp_rate}% in {time_window} minutes
Direction: {direction}
Time: {timestamp}

Rapid irradiance change detected. Consider conservative forecasting.

--
PEA RE Forecast Platform
            """,
            "line": """
Ramp Rate Alert

{station_id}: {ramp_rate}% ({direction})
{time_window} min window
""",
        },
        "th": {
            "subject": "แจ้งเตือน: ตรวจพบการเปลี่ยนแปลงกำลังไฟฟ้าอย่างรวดเร็ว",
            "body": """
แจ้งเตือน Ramp Rate

สถานี: {station_id}
อัตราการเปลี่ยนแปลง: {ramp_rate}% ใน {time_window} นาที
ทิศทาง: {direction}
เวลา: {timestamp}

ตรวจพบการเปลี่ยนแปลงความเข้มแสงอย่างรวดเร็ว

--
แพลตฟอร์มพยากรณ์พลังงานหมุนเวียน กฟภ.
            """,
            "line": """
แจ้งเตือน Ramp Rate

{station_id}: {ramp_rate}% ({direction})
ใน {time_window} นาที
""",
        },
    },
    "storm_warning": {
        "en": {
            "subject": "CRITICAL: Storm Warning Active",
            "body": """
STORM WARNING - CRITICAL ALERT

Region: {region}
Severity: {severity}
Expected Duration: {duration_hours} hours
Description: {description}

Recommended Actions:
- Enable conservative forecasting mode
- Increase uncertainty bounds
- Alert grid operators

--
PEA RE Forecast Platform
            """,
            "line": """
STORM WARNING

Region: {region}
Severity: {severity}
Duration: {duration_hours} hrs
""",
        },
        "th": {
            "subject": "วิกฤต: แจ้งเตือนพายุ",
            "body": """
แจ้งเตือนพายุ - ระดับวิกฤต

ภูมิภาค: {region}
ความรุนแรง: {severity}
ระยะเวลาคาดการณ์: {duration_hours} ชั่วโมง
รายละเอียด: {description}

คำแนะนำ:
- เปิดใช้โหมดพยากรณ์แบบระมัดระวัง
- เพิ่มขอบเขตความไม่แน่นอน
- แจ้งเตือนผู้ควบคุมระบบ

--
แพลตฟอร์มพยากรณ์พลังงานหมุนเวียน กฟภ.
            """,
            "line": """
แจ้งเตือนพายุ

ภูมิภาค: {region}
ความรุนแรง: {severity}
ระยะเวลา: {duration_hours} ชม.
""",
        },
    },
    "model_drift_detected": {
        "en": {
            "subject": "Alert: Model Performance Drift",
            "body": """
MODEL DRIFT ALERT

Model Type: {model_type}
Drift Type: {drift_type}
Severity: {severity}
Current MAPE: {current_mape}%
Threshold: {threshold}%

Recommended Action: {recommendation}

--
PEA RE Forecast Platform
            """,
            "line": """
Model Drift Alert

{model_type}: {drift_type}
MAPE: {current_mape}% (threshold: {threshold}%)
""",
        },
        "th": {
            "subject": "แจ้งเตือน: ตรวจพบการเบี่ยงเบนของโมเดล",
            "body": """
แจ้งเตือนการเบี่ยงเบนของโมเดล

ประเภทโมเดล: {model_type}
ประเภทการเบี่ยงเบน: {drift_type}
ความรุนแรง: {severity}
MAPE ปัจจุบัน: {current_mape}%
ขีดจำกัด: {threshold}%

คำแนะนำ: {recommendation}

--
แพลตฟอร์มพยากรณ์พลังงานหมุนเวียน กฟภ.
            """,
            "line": """
แจ้งเตือนโมเดล

{model_type}: {drift_type}
MAPE: {current_mape}% (จำกัด: {threshold}%)
""",
        },
    },
}


# Singleton instance
_notification_service: NotificationService | None = None


def get_notification_service() -> NotificationService:
    """Get or create notification service instance."""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service


def configure_notification_service(
    config: NotificationConfig | None = None,
    email_config: EmailConfig | None = None,
    line_config: LineConfig | None = None,
) -> NotificationService:
    """Configure the notification service with specific settings."""
    global _notification_service

    email_provider = None
    line_provider = None

    if email_config:
        email_provider = EmailProvider(email_config)

    if line_config:
        line_provider = LineProvider(line_config)

    _notification_service = NotificationService(
        config=config,
        email_provider=email_provider,
        line_provider=line_provider,
    )

    return _notification_service
