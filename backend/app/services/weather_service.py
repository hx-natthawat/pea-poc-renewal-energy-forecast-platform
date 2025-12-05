"""Weather alert integration service for TMD and weather classification."""

import math
import random
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from typing import Any, ClassVar

import httpx
from loguru import logger

from app.core.config import settings
from app.models.schemas.weather import (
    AlertSeverity,
    WeatherAlert,
    WeatherCondition,
    WeatherConditionResponse,
)


class WeatherService:
    """Service for TMD weather alert integration and weather classification.

    Integrates with the Thai Meteorological Department (TMD) API:
    - WeatherToday: Daily weather measurements at 07:00
    - Weather3Hours: 3-hourly observations from 122-125 stations
    - WeatherForecast7Days: 7-day forecasts by province
    - WeatherForecastDaily: Daily forecasts

    API Documentation: https://data.tmd.go.th/api/index1.php
    """

    # Province codes for Thailand (subset for Central region)
    PROVINCE_CODES: ClassVar[dict[str, str]] = {
        "bangkok": "กรุงเทพมหานคร",
        "nonthaburi": "นนทบุรี",
        "pathum_thani": "ปทุมธานี",
        "samut_prakan": "สมุทรปราการ",
        "nakhon_pathom": "นครปฐม",
        "central": "ภาคกลาง",
    }

    def __init__(self):
        """Initialize weather service with TMD API configuration."""
        # TMD API configuration from settings
        self.tmd_base_url = settings.TMD_API_BASE_URL
        self.api_uid = settings.TMD_API_UID
        self.api_key = settings.TMD_API_KEY
        self.timeout = settings.TMD_API_TIMEOUT
        self.cache_ttl = settings.TMD_CACHE_TTL

        # HTTP client
        self._client: httpx.AsyncClient | None = None

        # Cache storage
        self._cache: dict[str, Any] = {}
        self._cache_times: dict[str, datetime] = {}

        # Classification thresholds
        self.clear_sky_threshold = 0.7
        self.partly_cloudy_threshold = 0.5
        self.cloudy_threshold = 0.3

        logger.info(f"WeatherService initialized with TMD API: {self.tmd_base_url}")

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                follow_redirects=True,
            )
        return self._client

    async def _call_tmd_api(
        self, endpoint: str, params: dict | None = None
    ) -> str | None:
        """
        Call TMD API endpoint.

        Args:
            endpoint: API endpoint (e.g., 'WeatherToday', 'WeatherForecast7Days')
            params: Additional query parameters

        Returns:
            XML response string or None if error
        """
        url = f"{self.tmd_base_url}/{endpoint}"

        # Add authentication params
        query_params = {
            "uid": self.api_uid,
            "ukey": self.api_key,
        }
        if params:
            query_params.update(params)

        try:
            client = await self._get_client()
            response = await client.get(url, params=query_params)
            response.raise_for_status()

            logger.debug(f"TMD API call successful: {endpoint}")
            return response.text

        except httpx.TimeoutException:
            logger.warning(f"TMD API timeout: {endpoint}")
            return None
        except httpx.HTTPStatusError as e:
            logger.warning(f"TMD API error {e.response.status_code}: {endpoint}")
            return None
        except Exception as e:
            logger.error(f"TMD API unexpected error: {endpoint} - {e}")
            return None

    def _parse_weather_today(self, xml_data: str) -> dict[str, Any]:
        """Parse WeatherToday API response."""
        try:
            root = ET.fromstring(xml_data)
            stations = []

            for station in root.findall(".//Station"):
                station_data = {
                    "name": station.findtext("StationNameThai", ""),
                    "name_en": station.findtext("StationNameEng", ""),
                    "province": station.findtext("Province", ""),
                    "lat": float(station.findtext("Latitude", "0") or 0),
                    "lon": float(station.findtext("Longitude", "0") or 0),
                    "temperature": float(station.findtext("Temperature", "0") or 0),
                    "humidity": float(station.findtext("Humidity", "0") or 0),
                    "pressure": float(station.findtext("Pressure", "0") or 0),
                    "rainfall_24h": float(station.findtext("Rainfall24Hr", "0") or 0),
                    "wind_speed": float(station.findtext("WindSpeed", "0") or 0),
                    "wind_direction": station.findtext("WindDirection", ""),
                }
                stations.append(station_data)

            return {"stations": stations, "timestamp": datetime.now(UTC)}

        except ET.ParseError as e:
            logger.error(f"Failed to parse WeatherToday XML: {e}")
            return {"stations": [], "timestamp": datetime.now(UTC)}

    def _parse_forecast_7days(self, xml_data: str) -> list[dict[str, Any]]:
        """Parse WeatherForecast7Days API response."""
        try:
            root = ET.fromstring(xml_data)
            forecasts = []

            for forecast in root.findall(".//Forecast"):
                forecast_data = {
                    "date": forecast.findtext("Date", ""),
                    "description": forecast.findtext("ForecastDesc", ""),
                    "temperature_min": float(forecast.findtext("MinTemp", "0") or 0),
                    "temperature_max": float(forecast.findtext("MaxTemp", "0") or 0),
                    "humidity_min": float(forecast.findtext("MinHumidity", "0") or 0),
                    "humidity_max": float(forecast.findtext("MaxHumidity", "0") or 0),
                }
                forecasts.append(forecast_data)

            return forecasts

        except ET.ParseError as e:
            logger.error(f"Failed to parse WeatherForecast7Days XML: {e}")
            return []

    async def get_tmd_weather_today(self) -> dict[str, Any]:
        """
        Get today's weather from all TMD stations.

        Returns:
            Dictionary with station weather data
        """
        cache_key = "weather_today"

        # Check cache
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]

        # Call TMD API
        xml_data = await self._call_tmd_api("WeatherToday")

        if xml_data:
            result = self._parse_weather_today(xml_data)
            self._cache[cache_key] = result
            self._cache_times[cache_key] = datetime.now(UTC)
            return result

        # Return cached or empty
        return self._cache.get(cache_key, {"stations": [], "timestamp": datetime.now(UTC)})

    async def get_tmd_forecast_7days(self, province: str = "กรุงเทพมหานคร") -> list[dict]:
        """
        Get 7-day forecast for a province from TMD.

        Args:
            province: Province name in Thai

        Returns:
            List of daily forecasts
        """
        cache_key = f"forecast_7days_{province}"

        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]

        xml_data = await self._call_tmd_api(
            "WeatherForecast7Days",
            params={"province": province}
        )

        if xml_data:
            result = self._parse_forecast_7days(xml_data)
            self._cache[cache_key] = result
            self._cache_times[cache_key] = datetime.now(UTC)
            return result

        return self._cache.get(cache_key, [])

    async def get_current_alerts(
        self, region: str | None = None
    ) -> list[WeatherAlert]:
        """
        Fetch current weather alerts from TMD.

        Checks TMD forecast data and generates alerts based on:
        - Heavy rainfall warnings
        - Storm warnings
        - Temperature extremes

        Args:
            region: Optional region filter

        Returns:
            List of active weather alerts
        """
        cache_key = f"alerts_{region or 'all'}"

        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]

        alerts: list[WeatherAlert] = []

        # Get today's weather data from TMD
        weather_data = await self.get_tmd_weather_today()

        for station in weather_data.get("stations", []):
            station_alerts = self._generate_alerts_from_station(station)
            alerts.extend(station_alerts)

        # Get forecast and check for warnings
        forecast = await self.get_tmd_forecast_7days()
        for daily in forecast[:2]:  # Check next 2 days
            forecast_alerts = self._generate_alerts_from_forecast(daily)
            alerts.extend(forecast_alerts)

        # Filter by region if specified
        if region:
            alerts = [a for a in alerts if region.lower() in a.region.lower()]

        # Cache results
        self._cache[cache_key] = alerts
        self._cache_times[cache_key] = datetime.now(UTC)

        return alerts

    def _generate_alerts_from_station(self, station: dict) -> list[WeatherAlert]:
        """Generate alerts from station weather data."""
        alerts = []
        now = datetime.now(UTC)

        # Heavy rainfall alert (>50mm/24h)
        if station.get("rainfall_24h", 0) > 50:
            alerts.append(WeatherAlert(
                id=f"rain_{station.get('name_en', 'station')}_{now.strftime('%Y%m%d')}",
                timestamp=now,
                condition=WeatherCondition.RAINY,
                severity=AlertSeverity.WARNING if station["rainfall_24h"] < 100 else AlertSeverity.CRITICAL,
                region=station.get("province", "Central Thailand"),
                description=f"Heavy rainfall: {station['rainfall_24h']:.1f}mm in 24 hours at {station.get('name', '')}",
                expected_duration_minutes=360,
                recommended_action="Expect reduced solar irradiance. Consider backup generation.",
            ))

        # High wind alert (>40 km/h)
        if station.get("wind_speed", 0) > 40:
            alerts.append(WeatherAlert(
                id=f"wind_{station.get('name_en', 'station')}_{now.strftime('%Y%m%d')}",
                timestamp=now,
                condition=WeatherCondition.STORM if station["wind_speed"] > 60 else WeatherCondition.CLOUDY,
                severity=AlertSeverity.WARNING if station["wind_speed"] < 60 else AlertSeverity.CRITICAL,
                region=station.get("province", "Central Thailand"),
                description=f"High winds: {station['wind_speed']:.1f} km/h at {station.get('name', '')}",
                expected_duration_minutes=180,
                recommended_action="Monitor panel stability and potential dust/debris impact.",
            ))

        # Extreme temperature alert (>40C affects panel efficiency)
        if station.get("temperature", 0) > 40:
            alerts.append(WeatherAlert(
                id=f"temp_{station.get('name_en', 'station')}_{now.strftime('%Y%m%d')}",
                timestamp=now,
                condition=WeatherCondition.CLEAR,
                severity=AlertSeverity.INFO,
                region=station.get("province", "Central Thailand"),
                description=f"High temperature: {station['temperature']:.1f}C - Reduced panel efficiency expected",
                expected_duration_minutes=240,
                recommended_action="Apply temperature derating to forecasts.",
            ))

        return alerts

    def _generate_alerts_from_forecast(self, forecast: dict) -> list[WeatherAlert]:
        """Generate alerts from forecast data."""
        alerts = []
        now = datetime.now(UTC)
        desc = forecast.get("description", "").lower()

        # Check for storm/thunderstorm in forecast
        storm_keywords = ["พายุ", "ฝนฟ้าคะนอง", "storm", "thunder", "ฟ้าผ่า"]
        if any(kw in desc for kw in storm_keywords):
            alerts.append(WeatherAlert(
                id=f"forecast_storm_{forecast.get('date', now.strftime('%Y%m%d'))}",
                timestamp=now,
                condition=WeatherCondition.STORM,
                severity=AlertSeverity.WARNING,
                region="Central Thailand",
                description=f"Storm forecast: {forecast.get('description', 'Thunderstorms expected')}",
                expected_duration_minutes=480,
                recommended_action="Prepare for significant irradiance variability.",
            ))

        # Heavy rain in forecast
        rain_keywords = ["ฝนตกหนัก", "ฝนตก", "heavy rain", "rain"]
        if any(kw in desc for kw in rain_keywords):
            alerts.append(WeatherAlert(
                id=f"forecast_rain_{forecast.get('date', now.strftime('%Y%m%d'))}",
                timestamp=now,
                condition=WeatherCondition.RAINY,
                severity=AlertSeverity.INFO,
                region="Central Thailand",
                description=f"Rain forecast: {forecast.get('description', 'Rain expected')}",
                expected_duration_minutes=360,
                recommended_action="Monitor irradiance levels.",
            ))

        return alerts

    async def get_weather_condition(
        self, latitude: float = 13.7563, longitude: float = 100.5018
    ) -> WeatherConditionResponse:
        """
        Get current weather condition for location.

        Uses TMD station data when available, falls back to simulation.

        Args:
            latitude: Location latitude (default: Bangkok)
            longitude: Location longitude

        Returns:
            Current weather condition with details
        """
        # Try to get real data from nearest TMD station
        weather_data = await self.get_tmd_weather_today()
        stations = weather_data.get("stations", [])

        nearest_station = None
        min_distance = float("inf")

        for station in stations:
            if station.get("lat") and station.get("lon"):
                dist = ((station["lat"] - latitude) ** 2 + (station["lon"] - longitude) ** 2) ** 0.5
                if dist < min_distance:
                    min_distance = dist
                    nearest_station = station

        if nearest_station and min_distance < 1.0:  # Within ~100km
            # Use real TMD data
            rainfall = nearest_station.get("rainfall_24h", 0)
            wind = nearest_station.get("wind_speed", 0)
            humidity = nearest_station.get("humidity", 50)

            # Estimate clearness from humidity and rainfall
            if rainfall > 10:
                clearness = 0.2
            elif rainfall > 0:
                clearness = 0.4
            elif humidity > 80:
                clearness = 0.5
            elif humidity > 60:
                clearness = 0.65
            else:
                clearness = 0.8

            condition = self.classify_weather(
                clearness_index=clearness,
                precipitation_mm=rainfall,
                wind_speed_kmh=wind,
            )

            return WeatherConditionResponse(
                condition=condition,
                clearness_index=clearness,
                cloud_cover_percent=(1 - clearness) * 100,
                precipitation_mm=rainfall,
                wind_speed_kmh=wind,
                timestamp=datetime.now(UTC),
            )

        # Fallback to simulation if no nearby station
        return await self._get_simulated_condition(latitude, longitude)

    async def _get_simulated_condition(
        self, latitude: float, longitude: float
    ) -> WeatherConditionResponse:
        """Generate simulated weather condition as fallback."""
        now = datetime.now(UTC)
        hour = now.hour

        # Simulate clearness index based on time
        if 6 <= hour <= 18:
            base_clearness = 0.7 + 0.2 * math.sin((hour - 6) * math.pi / 12)
        else:
            base_clearness = 0.0

        clearness = max(0, min(1, base_clearness + random.uniform(-0.2, 0.1)))
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
        clearness_index: float | None = None,
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
            Clear sky irradiance in W/m2
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
        air_mass = 1 / math.sin(math.radians(elevation)) if elevation > 0 else 40

        # Clear sky irradiance (simplified Kasten model)
        solar_constant = 1361  # W/m2
        atmospheric_transmittance = 0.7

        irradiance = (
            solar_constant
            * math.pow(atmospheric_transmittance, air_mass)
            * math.sin(math.radians(elevation))
        )

        # Altitude correction (approx 10% per km)
        altitude_factor = 1 + 0.1 * (altitude / 1000)

        return max(0, irradiance * altitude_factor)

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is still valid."""
        if cache_key not in self._cache_times:
            return False
        return (datetime.now(UTC) - self._cache_times[cache_key]).seconds < self.cache_ttl

    async def close(self):
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()


# Singleton instance
weather_service = WeatherService()
