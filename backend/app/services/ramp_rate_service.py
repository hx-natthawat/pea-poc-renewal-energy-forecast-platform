"""Ramp rate detection service for cloud shadow and rapid irradiance changes."""

from dataclasses import dataclass
from datetime import UTC, datetime

import numpy as np
import pandas as pd
from loguru import logger

from app.models.schemas.weather import CloudEvent, RampEvent, RampRateStatus


@dataclass
class RampRateConfig:
    """Configuration for ramp rate detection."""

    window_size_seconds: int = 300  # 5 minutes
    threshold_percent: float = 30.0  # 30% change triggers alert
    min_irradiance: float = 50.0  # W/m² minimum for detection
    alert_cooldown_seconds: int = 60  # Minimum time between alerts


class RampRateService:
    """Service for detecting rapid irradiance changes (cloud shadows, storms)."""

    def __init__(self, config: RampRateConfig | None = None):
        """Initialize ramp rate service."""
        self.config = config or RampRateConfig()
        self._last_alert_time: datetime | None = None
        self._recent_events: list[RampEvent] = []
        self._max_recent_events = 100

    def detect_ramp_event(
        self, irradiance_series: pd.Series
    ) -> RampEvent | None:
        """
        Detect sudden changes in irradiance indicating cloud shadow.

        Args:
            irradiance_series: Time-indexed irradiance values (W/m²)

        Returns:
            RampEvent if detected, None otherwise
        """
        if len(irradiance_series) < 2:
            return None

        current = irradiance_series.iloc[-1]
        previous = irradiance_series.iloc[-2]

        # Skip if below minimum irradiance (nighttime or very cloudy)
        if previous < self.config.min_irradiance:
            return None

        # Calculate rate of change
        rate_of_change = (current - previous) / previous * 100

        # Check if exceeds threshold
        if abs(rate_of_change) >= self.config.threshold_percent:
            # Check cooldown
            if self._is_in_cooldown():
                logger.debug("Ramp event detected but in cooldown period")
                return None

            self._last_alert_time = datetime.now(UTC)

            event = RampEvent(
                timestamp=irradiance_series.index[-1]
                if hasattr(irradiance_series.index[-1], "isoformat")
                else datetime.now(UTC),
                rate_percent=rate_of_change,
                direction="down" if rate_of_change < 0 else "up",
                current_irradiance=float(current),
                previous_irradiance=float(previous),
            )

            # Store recent event
            self._recent_events.append(event)
            if len(self._recent_events) > self._max_recent_events:
                self._recent_events = self._recent_events[-self._max_recent_events :]

            logger.info(
                f"Ramp event detected: {rate_of_change:.1f}% "
                f"({previous:.0f} -> {current:.0f} W/m²)"
            )

            return event

        return None

    def detect_cloud_events(
        self,
        irradiance: np.ndarray,
        clear_sky: np.ndarray,
        timestamps: pd.DatetimeIndex,
    ) -> list[CloudEvent]:
        """
        Detect cloud shadow events using clearness index.

        Clearness Index (kt) = Measured / Clear Sky

        Classifications:
        - kt >= 0.7: Clear sky
        - 0.5 <= kt < 0.7: Partly cloudy
        - 0.3 <= kt < 0.5: Cloudy
        - kt < 0.3: Heavy clouds/rain

        Args:
            irradiance: Measured irradiance values (W/m²)
            clear_sky: Theoretical clear sky irradiance (W/m²)
            timestamps: Corresponding timestamps

        Returns:
            List of detected cloud events
        """
        # Calculate clearness index
        with np.errstate(divide="ignore", invalid="ignore"):
            kt = np.where(clear_sky > 0, irradiance / clear_sky, 0)

        events = []
        in_cloud = False
        event_start_idx: int | None = None

        for i, (_t, k) in enumerate(zip(timestamps, kt, strict=False)):
            # Enter cloud event when kt drops below 0.5
            if k < 0.5 and not in_cloud:
                in_cloud = True
                event_start_idx = i

            # Exit cloud event when kt rises above 0.7
            elif k >= 0.7 and in_cloud:
                in_cloud = False
                if event_start_idx is not None:
                    event_kt = kt[event_start_idx:i]
                    duration = (timestamps[i] - timestamps[event_start_idx]).total_seconds() / 60

                    if duration >= 1:  # Minimum 1 minute duration
                        events.append(
                            CloudEvent(
                                start=timestamps[event_start_idx],
                                end=timestamps[i],
                                duration_minutes=duration,
                                min_clearness=float(np.min(event_kt)),
                                avg_clearness=float(np.mean(event_kt)),
                            )
                        )

        return events

    def calculate_variability_index(
        self, irradiance: pd.Series, window_minutes: int = 10
    ) -> pd.Series:
        """
        Calculate variability index for irradiance data.

        VI = std(G) / mean(G) over rolling window

        Interpretation:
        - VI < 0.1: Stable conditions
        - 0.1 <= VI < 0.3: Moderate variability
        - VI >= 0.3: High variability (cloud events likely)

        Args:
            irradiance: Irradiance time series
            window_minutes: Rolling window size in minutes

        Returns:
            Variability index series
        """
        window = f"{window_minutes}min"
        rolling_mean: pd.Series = irradiance.rolling(window).mean()  # type: ignore[assignment]
        rolling_std: pd.Series = irradiance.rolling(window).std()  # type: ignore[assignment]

        # Avoid division by zero
        return rolling_std / rolling_mean.replace(0, np.nan)

    def get_current_status(
        self, current_irradiance: float | None = None
    ) -> RampRateStatus:
        """
        Get current ramp rate monitoring status.

        Args:
            current_irradiance: Current irradiance reading (optional)

        Returns:
            Current ramp rate status
        """
        # Calculate current ramp rate from recent events
        current_rate = 0.0
        if len(self._recent_events) >= 1:
            last_event = self._recent_events[-1]
            # Check if last event is recent (within last 5 minutes)
            if (datetime.now(UTC) - last_event.timestamp).total_seconds() < 300:
                current_rate = last_event.rate_percent

        is_alert = abs(current_rate) >= self.config.threshold_percent

        return RampRateStatus(
            current_ramp_rate_percent=current_rate,
            threshold_percent=self.config.threshold_percent,
            is_alert=is_alert,
            last_event=self._recent_events[-1] if self._recent_events else None,
            timestamp=datetime.now(UTC),
        )

    def get_recent_events(self, limit: int = 10) -> list[RampEvent]:
        """Get recent ramp rate events."""
        return self._recent_events[-limit:]

    def _is_in_cooldown(self) -> bool:
        """Check if still in alert cooldown period."""
        if self._last_alert_time is None:
            return False

        elapsed = (datetime.now(UTC) - self._last_alert_time).seconds
        return elapsed < self.config.alert_cooldown_seconds


# Singleton instance
ramp_rate_service = RampRateService()
