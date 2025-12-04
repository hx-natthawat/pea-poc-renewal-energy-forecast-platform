"""
LINE Notify notification provider.

Supports sending alert notifications through LINE Notify API.
Popular messaging platform in Thailand for instant mobile alerts.
Part of v1.1.0 Enhanced Alerting System feature.
"""

import logging
from dataclasses import dataclass, field
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


# LINE Notify API endpoint
LINE_NOTIFY_API = "https://notify-api.line.me/api/notify"


@dataclass
class LineConfig:
    """LINE Notify provider configuration."""

    access_token: str = ""
    timeout_seconds: int = 10
    max_retries: int = 3


@dataclass
class LineMessage:
    """LINE notification message structure."""

    message: str
    image_url: Optional[str] = None
    image_thumbnail: Optional[str] = None
    sticker_package_id: Optional[int] = None
    sticker_id: Optional[int] = None
    notification_disabled: bool = False


@dataclass
class LineResult:
    """Result of LINE notification send operation."""

    success: bool
    status_code: Optional[int] = None
    error: Optional[str] = None
    rate_limit_remaining: Optional[int] = None
    rate_limit_reset: Optional[int] = None


class LineProvider:
    """
    LINE Notify notification provider.

    Supports:
    - Text messages
    - Image attachments (URL)
    - LINE stickers
    - Rate limit tracking
    """

    def __init__(self, config: Optional[LineConfig] = None):
        """Initialize LINE provider with configuration."""
        self.config = config or LineConfig()
        self._is_configured = bool(self.config.access_token)

    @property
    def is_configured(self) -> bool:
        """Check if provider is properly configured."""
        return self._is_configured

    async def send_async(self, message: LineMessage) -> LineResult:
        """
        Send a LINE notification asynchronously.

        Args:
            message: LineMessage object with content

        Returns:
            LineResult with success status and rate limit info
        """
        if not self._is_configured:
            logger.warning("LINE provider not configured, simulating send")
            return self._simulate_send(message)

        for attempt in range(self.config.max_retries):
            try:
                return await self._send_notify(message)
            except Exception as e:
                logger.error(f"LINE send attempt {attempt + 1} failed: {e}")
                if attempt == self.config.max_retries - 1:
                    return LineResult(
                        success=False,
                        error=str(e),
                    )

        return LineResult(success=False, error="Max retries exceeded")

    def send(self, message: LineMessage) -> LineResult:
        """
        Send a LINE notification synchronously.

        Args:
            message: LineMessage object with content

        Returns:
            LineResult with success status and rate limit info
        """
        if not self._is_configured:
            logger.warning("LINE provider not configured, simulating send")
            return self._simulate_send(message)

        for attempt in range(self.config.max_retries):
            try:
                return self._send_notify_sync(message)
            except Exception as e:
                logger.error(f"LINE send attempt {attempt + 1} failed: {e}")
                if attempt == self.config.max_retries - 1:
                    return LineResult(
                        success=False,
                        error=str(e),
                    )

        return LineResult(success=False, error="Max retries exceeded")

    async def _send_notify(self, message: LineMessage) -> LineResult:
        """Send notification via LINE Notify API (async)."""
        headers = {
            "Authorization": f"Bearer {self.config.access_token}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = self._build_payload(message)

        async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
            response = await client.post(
                LINE_NOTIFY_API,
                headers=headers,
                data=data,
            )

        return self._parse_response(response)

    def _send_notify_sync(self, message: LineMessage) -> LineResult:
        """Send notification via LINE Notify API (sync)."""
        headers = {
            "Authorization": f"Bearer {self.config.access_token}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = self._build_payload(message)

        with httpx.Client(timeout=self.config.timeout_seconds) as client:
            response = client.post(
                LINE_NOTIFY_API,
                headers=headers,
                data=data,
            )

        return self._parse_response(response)

    def _build_payload(self, message: LineMessage) -> dict:
        """Build the API payload from message."""
        data = {"message": message.message}

        if message.image_url:
            data["imageThumbnail"] = message.image_thumbnail or message.image_url
            data["imageFullsize"] = message.image_url

        if message.sticker_package_id and message.sticker_id:
            data["stickerPackageId"] = message.sticker_package_id
            data["stickerId"] = message.sticker_id

        if message.notification_disabled:
            data["notificationDisabled"] = "true"

        return data

    def _parse_response(self, response: httpx.Response) -> LineResult:
        """Parse LINE API response."""
        rate_limit_remaining = response.headers.get("X-RateLimit-Remaining")
        rate_limit_reset = response.headers.get("X-RateLimit-Reset")

        if response.status_code == 200:
            logger.info("LINE notification sent successfully")
            return LineResult(
                success=True,
                status_code=response.status_code,
                rate_limit_remaining=int(rate_limit_remaining) if rate_limit_remaining else None,
                rate_limit_reset=int(rate_limit_reset) if rate_limit_reset else None,
            )

        # Handle errors
        error_messages = {
            400: "Bad request - invalid parameters",
            401: "Invalid access token",
            500: "LINE server error",
        }

        error = error_messages.get(
            response.status_code,
            f"Unknown error: {response.status_code}",
        )

        logger.error(f"LINE notification failed: {error}")

        return LineResult(
            success=False,
            status_code=response.status_code,
            error=error,
            rate_limit_remaining=int(rate_limit_remaining) if rate_limit_remaining else None,
            rate_limit_reset=int(rate_limit_reset) if rate_limit_reset else None,
        )

    def _simulate_send(self, message: LineMessage) -> LineResult:
        """Simulate LINE send for testing/unconfigured state."""
        logger.info(f"[SIMULATED] LINE notification: {message.message[:50]}...")
        return LineResult(
            success=True,
            status_code=200,
            rate_limit_remaining=1000,
        )

    def send_alert(self, message: str, image_url: Optional[str] = None) -> LineResult:
        """
        Convenience method to send a simple alert.

        Args:
            message: Alert message text
            image_url: Optional image URL to attach

        Returns:
            LineResult
        """
        line_message = LineMessage(
            message=message,
            image_url=image_url,
        )
        return self.send(line_message)

    async def send_alert_async(
        self, message: str, image_url: Optional[str] = None
    ) -> LineResult:
        """
        Convenience method to send a simple alert asynchronously.

        Args:
            message: Alert message text
            image_url: Optional image URL to attach

        Returns:
            LineResult
        """
        line_message = LineMessage(
            message=message,
            image_url=image_url,
        )
        return await self.send_async(line_message)


# Singleton instance
_line_provider: Optional[LineProvider] = None


def get_line_provider() -> LineProvider:
    """Get or create LINE provider instance."""
    global _line_provider
    if _line_provider is None:
        _line_provider = LineProvider()
    return _line_provider


def configure_line_provider(config: LineConfig) -> LineProvider:
    """Configure the LINE provider with specific settings."""
    global _line_provider
    _line_provider = LineProvider(config)
    return _line_provider
