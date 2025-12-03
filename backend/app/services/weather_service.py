"""Weather alert integration service for TMD and weather classification."""

import math
from datetime import datetime, timedelta
from typing import Optional

from loguru import logger

from app.models.schemas.weather import (
    AlertSeverity,
    WeatherAlert,
    WeatherCondition,
    WeatherConditionResponse,
)


class WeatherService:
    """Service for TMD weather alert integration and weather classification."""

    def __init__(self):
        """Initialize weather service."""
        # TMD API configuration (would be from settings in production)
        self.tmd_base_url = "https://data.tmd.go.th/api/v1"
        self.api_key = ""  # Would come from settings
        self.cache_ttl = 300  # 5 minutes
        self._cache: dict = {}
        self._cache_time: Optional[datetime] = None

        # Classification thresholds
        self.clear_sky_threshold = 0.7
        self.partly_cloudy_threshold = 0.5
        self.cloudy_threshold = 0.3

    async def get_current_alerts(
        self, region: Optional[str] = None
    ) -> list[WeatherAlert]:
        """
        Fetch current weather alerts from TMD.

        In production, this would call the TMD API.
        For now, returns simulated alerts based on conditions.

        Args:
            region: Optional region filter

        Returns:
            List of active weather alerts
        """
        # Check cache
        if self._is_cache_valid():
            alerts = self._cache.get("alerts", [])
            if region:
                alerts = [a for a in alerts if a.region == region]
            return alerts

        # In production, fetch from TMD API
        # For now, return empty or simulated alerts
        alerts = await self._generate_simulated_alerts()

        # Update cache
        self._cache["alerts"] = alerts
        self._cache_time = datetime.utcnow()

        if region:
            alerts = [a for a in alerts if a.region == region]

        return alerts

    async def get_weather_condition(
        self, latitude: float = 13.7563, longitude: float = 100.5018
    ) -> WeatherConditionResponse:
        """
        Get current weather condition for location.

        Args:
            latitude: Location latitude (default: Bangkok)
            longitude: Location longitude

        Returns:
            Current weather condition with details
        """
        # Calculate simulated weather based on time of day
        now = datetime.utcnow()
        hour = now.hour

        # Simulate clearness index based on time
        # Higher during midday, lower in morning/evening
        if 6 <= hour <= 18:
            base_clearness = 0.7 + 0.2 * math.sin((hour - 6) * math.pi / 12)
        else:
            base_clearness = 0.0

        # Add some randomness (in production, use actual data)
        import random

        clearness = max(0, min(1, base_clearness + random.uniform(-0.2, 0.1)))

        # Classify based on clearness
        condition = self._classify_by_clearness(clearness)

        return WeatherConditionResponse(
            condition=condition,
            clearness_index=clearness,
            cloud_cover_percent=(1 - clearness) * 100,
            precipitation_mm=0.0 if clearness > 0.3 else random.uniform(0, 5),
            wind_speed_kmh=random.uniform(5, 25),
            timestamp=now,
        )

    def classify_weather(
        self,
        clearness_index: Optional[float] = None,
        precipitation_mm: float = 0,
        wind_speed_kmh: float = 0,
        has_storm_alert: bool = False,
    ) -> WeatherCondition:
        """
        Classify weather condition from various inputs.

        Args:
            clearness_index: Measured/Clear sky irradiance ratio
            precipitation_mm: Current precipitation
            wind_speed_kmh: Wind speed
            has_storm_alert: Whether storm alert is active

        Returns:
            Weather condition classification
        """
        # Storm conditions override everything
        if has_storm_alert or wind_speed_kmh > 60 or precipitation_mm > 20:
            return WeatherCondition.STORM

        # Rain conditions
        if precipitation_mm > 1:
            return WeatherCondition.RAINY

        # Clearness-based classification
        if clearness_index is not None:
            return self._classify_by_clearness(clearness_index)

        # Default to partly cloudy if no data
        return WeatherCondition.PARTLY_CLOUDY

    def _classify_by_clearness(self, clearness_index: float) -> WeatherCondition:
        """Classify weather by clearness index."""
        if clearness_index >= self.clear_sky_threshold:
            return WeatherCondition.CLEAR
        elif clearness_index >= self.partly_cloudy_threshold:
            return WeatherCondition.PARTLY_CLOUDY
        elif clearness_index >= self.cloudy_threshold:
            return WeatherCondition.CLOUDY
        else:
            return WeatherCondition.RAINY

    def calculate_clear_sky_irradiance(
        self,
        latitude: float,
        longitude: float,
        timestamp: datetime,
        altitude: float = 0,
    ) -> float:
        """
        Calculate theoretical clear sky irradiance.

        Uses a simplified model based on solar position.

        Args:
            latitude: Location latitude in degrees
            longitude: Location longitude in degrees
            timestamp: Time for calculation
            altitude: Altitude in meters

        Returns:
            Clear sky irradiance in W/m²
        """
        # Day of year
        day_of_year = timestamp.timetuple().tm_yday

        # Solar declination (simplified)
        declination = 23.45 * math.sin(math.radians(360 * (284 + day_of_year) / 365))

        # Hour angle
        solar_noon = 12.0  # Simplified, would need longitude correction
        hour = timestamp.hour + timestamp.minute / 60
        hour_angle = 15 * (hour - solar_noon)

        # Solar elevation angle
        lat_rad = math.radians(latitude)
        dec_rad = math.radians(declination)
        ha_rad = math.radians(hour_angle)

        sin_elevation = math.sin(lat_rad) * math.sin(dec_rad) + math.cos(
            lat_rad
        ) * math.cos(dec_rad) * math.cos(ha_rad)

        elevation = math.degrees(math.asin(max(-1, min(1, sin_elevation))))

        if elevation <= 0:
            return 0.0

        # Air mass
        if elevation > 0:
            air_mass = 1 / math.sin(math.radians(elevation))
        else:
            air_mass = 40  # Very high for horizon

        # Clear sky irradiance (simplified Kasten model)
        solar_constant = 1361  # W/m²
        atmospheric_transmittance = 0.7

        irradiance = (
            solar_constant
            * math.pow(atmospheric_transmittance, air_mass)
            * math.sin(math.radians(elevation))
        )

        # Altitude correction (approx 10% per km)
        altitude_factor = 1 + 0.1 * (altitude / 1000)

        return max(0, irradiance * altitude_factor)

    async def _generate_simulated_alerts(self) -> list[WeatherAlert]:
        """Generate simulated alerts for demo purposes."""
        # In production, this would fetch from TMD API
        # For demo, occasionally return alerts based on time
        now = datetime.utcnow()

        alerts = []

        # Simulate occasional alerts
        if now.minute % 30 == 0:  # Every 30 minutes, potentially show alert
            alerts.append(
                WeatherAlert(
                    id=f"alert_{now.strftime('%Y%m%d%H%M')}",
                    timestamp=now,
                    condition=WeatherCondition.PARTLY_CLOUDY,
                    severity=AlertSeverity.INFO,
                    region="Central Thailand",
                    description="Scattered clouds expected in the afternoon",
                    expected_duration_minutes=120,
                    recommended_action="Monitor irradiance levels",
                )
            )

        return alerts

    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid."""
        if self._cache_time is None:
            return False
        return (datetime.utcnow() - self._cache_time).seconds < self.cache_ttl


# Singleton instance
weather_service = WeatherService()
