"""
Email notification provider using SMTP.

Supports sending alert emails through configurable SMTP servers.
Part of v1.1.0 Enhanced Alerting System feature.
"""

import logging
import smtplib
import ssl
from dataclasses import dataclass, field
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


@dataclass
class EmailConfig:
    """Email provider configuration."""

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    from_email: str = ""
    from_name: str = "PEA RE Forecast Platform"
    use_tls: bool = True
    timeout_seconds: int = 30
    max_retries: int = 3


@dataclass
class EmailMessage:
    """Email message structure."""

    to: list[str]
    subject: str
    body_html: str
    body_text: str | None = None
    cc: list[str] = field(default_factory=list)
    bcc: list[str] = field(default_factory=list)
    reply_to: str | None = None
    headers: dict[str, str] = field(default_factory=dict)


@dataclass
class EmailResult:
    """Result of email send operation."""

    success: bool
    message_id: str | None = None
    error: str | None = None
    recipients_sent: list[str] = field(default_factory=list)
    recipients_failed: list[str] = field(default_factory=list)


class EmailProvider:
    """
    Email notification provider using SMTP.

    Supports:
    - TLS encryption
    - HTML and plain text emails
    - Multiple recipients (to, cc, bcc)
    - Retry on failure
    """

    def __init__(self, config: EmailConfig | None = None):
        """Initialize email provider with configuration."""
        self.config = config or EmailConfig()
        self._is_configured = bool(
            self.config.smtp_user and self.config.smtp_password
        )

    @property
    def is_configured(self) -> bool:
        """Check if provider is properly configured."""
        return self._is_configured

    def send(self, message: EmailMessage) -> EmailResult:
        """
        Send an email message.

        Args:
            message: EmailMessage object with recipients and content

        Returns:
            EmailResult with success status and any errors
        """
        if not self._is_configured:
            logger.warning("Email provider not configured, simulating send")
            return self._simulate_send(message)

        for attempt in range(self.config.max_retries):
            try:
                return self._send_smtp(message)
            except Exception as e:
                logger.error(f"Email send attempt {attempt + 1} failed: {e}")
                if attempt == self.config.max_retries - 1:
                    return EmailResult(
                        success=False,
                        error=str(e),
                        recipients_failed=message.to + message.cc + message.bcc,
                    )

        return EmailResult(success=False, error="Max retries exceeded")

    def _send_smtp(self, message: EmailMessage) -> EmailResult:
        """Send email via SMTP."""
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = message.subject
        msg["From"] = f"{self.config.from_name} <{self.config.from_email or self.config.smtp_user}>"
        msg["To"] = ", ".join(message.to)

        if message.cc:
            msg["Cc"] = ", ".join(message.cc)

        if message.reply_to:
            msg["Reply-To"] = message.reply_to

        # Add custom headers
        for key, value in message.headers.items():
            msg[key] = value

        # Add body parts
        if message.body_text:
            msg.attach(MIMEText(message.body_text, "plain", "utf-8"))
        msg.attach(MIMEText(message.body_html, "html", "utf-8"))

        # All recipients
        all_recipients = message.to + message.cc + message.bcc

        # Send via SMTP
        context = ssl.create_default_context() if self.config.use_tls else None

        with smtplib.SMTP(
            self.config.smtp_host,
            self.config.smtp_port,
            timeout=self.config.timeout_seconds,
        ) as server:
            if self.config.use_tls:
                server.starttls(context=context)

            server.login(self.config.smtp_user, self.config.smtp_password)
            server.sendmail(
                self.config.from_email or self.config.smtp_user,
                all_recipients,
                msg.as_string(),
            )

        logger.info(f"Email sent successfully to {len(all_recipients)} recipients")

        return EmailResult(
            success=True,
            message_id=msg.get("Message-ID"),
            recipients_sent=all_recipients,
        )

    def _simulate_send(self, message: EmailMessage) -> EmailResult:
        """Simulate email send for testing/unconfigured state."""
        all_recipients = message.to + message.cc + message.bcc
        logger.info(
            f"[SIMULATED] Email to {all_recipients}: {message.subject}"
        )
        return EmailResult(
            success=True,
            message_id="simulated-message-id",
            recipients_sent=all_recipients,
        )

    def send_alert(
        self,
        recipients: list[str],
        subject: str,
        body_html: str,
        body_text: str | None = None,
    ) -> EmailResult:
        """
        Convenience method to send an alert email.

        Args:
            recipients: List of email addresses
            subject: Email subject
            body_html: HTML body content
            body_text: Optional plain text body

        Returns:
            EmailResult
        """
        message = EmailMessage(
            to=recipients,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
        )
        return self.send(message)


# Singleton instance
_email_provider: EmailProvider | None = None


def get_email_provider() -> EmailProvider:
    """Get or create email provider instance."""
    global _email_provider
    if _email_provider is None:
        _email_provider = EmailProvider()
    return _email_provider


def configure_email_provider(config: EmailConfig) -> EmailProvider:
    """Configure the email provider with specific settings."""
    global _email_provider
    _email_provider = EmailProvider(config)
    return _email_provider
