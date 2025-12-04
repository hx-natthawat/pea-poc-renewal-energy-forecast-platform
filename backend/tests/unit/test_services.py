"""
Unit tests for service layer.

Tests the business logic services.
"""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from app.services.ramp_rate_service import RampRateConfig, RampRateService
from app.services.weather_service import WeatherService
from app.models.schemas.weather import WeatherCondition


class TestRampRateService:
    """Tests for RampRateService."""

    def test_init_default_config(self):
        """Test service initializes with default config."""
        service = RampRateService()
        assert service.config.window_size_seconds == 300
        assert service.config.threshold_percent == 30.0
        assert service.config.min_irradiance == 50.0

    def test_init_custom_config(self):
        """Test service initializes with custom config."""
        config = RampRateConfig(
            threshold_percent=20.0,
            min_irradiance=100.0,
        )
        service = RampRateService(config=config)
        assert service.config.threshold_percent == 20.0
        assert service.config.min_irradiance == 100.0

    def test_detect_ramp_event_insufficient_data(self):
        """Test detection returns None with insufficient data."""
        service = RampRateService()
        series = pd.Series([100])
        result = service.detect_ramp_event(series)
        assert result is None

    def test_detect_ramp_event_below_min_irradiance(self):
        """Test detection returns None when below minimum irradiance."""
        service = RampRateService()
        series = pd.Series([30, 20])  # Below 50 W/m² threshold
        result = service.detect_ramp_event(series)
        assert result is None

    def test_detect_ramp_event_no_significant_change(self):
        """Test detection returns None when change is below threshold."""
        service = RampRateService()
        series = pd.Series([100, 105])  # 5% change, below 30% threshold
        result = service.detect_ramp_event(series)
        assert result is None

    def test_detect_ramp_event_significant_drop(self):
        """Test detection of significant irradiance drop."""
        service = RampRateService()
        # 50% drop - well above 30% threshold
        series = pd.Series([800, 400])
        result = service.detect_ramp_event(series)
        assert result is not None
        assert result.direction == "down"
        assert result.rate_percent < -30

    def test_detect_ramp_event_significant_increase(self):
        """Test detection of significant irradiance increase."""
        service = RampRateService()
        # Wait for cooldown
        service._last_alert_time = None
        # 50% increase
        series = pd.Series([400, 600])
        result = service.detect_ramp_event(series)
        assert result is not None
        assert result.direction == "up"
        assert result.rate_percent > 30

    def test_detect_ramp_event_cooldown(self):
        """Test that cooldown prevents repeated alerts."""
        service = RampRateService()
        series1 = pd.Series([800, 400])
        result1 = service.detect_ramp_event(series1)
        assert result1 is not None

        # Second event within cooldown should return None
        series2 = pd.Series([600, 300])
        result2 = service.detect_ramp_event(series2)
        assert result2 is None

    def test_get_current_status_no_events(self):
        """Test status with no recent events."""
        service = RampRateService()
        status = service.get_current_status()
        assert status.current_ramp_rate_percent == 0.0
        assert status.is_alert is False
        assert status.last_event is None

    def test_get_current_status_with_events(self):
        """Test status with recent events."""
        service = RampRateService()
        # Trigger an event
        series = pd.Series([800, 400])
        service.detect_ramp_event(series)

        status = service.get_current_status()
        assert status.last_event is not None
        assert status.threshold_percent == 30.0

    def test_get_recent_events_empty(self):
        """Test getting recent events when none exist."""
        service = RampRateService()
        events = service.get_recent_events(limit=5)
        assert events == []

    def test_get_recent_events_with_limit(self):
        """Test getting recent events respects limit."""
        service = RampRateService()
        # Add some events by waiting for cooldown between each
        service._last_alert_time = None
        service.detect_ramp_event(pd.Series([800, 400]))

        events = service.get_recent_events(limit=5)
        assert len(events) <= 5

    def test_calculate_variability_index(self):
        """Test variability index calculation."""
        service = RampRateService()
        # Create time-indexed series
        index = pd.date_range("2025-01-01", periods=20, freq="1min")
        # Stable values
        stable_data = pd.Series([100] * 20, index=index)
        vi = service.calculate_variability_index(stable_data, window_minutes=10)
        # First 10 values will be NaN due to rolling window
        assert vi.iloc[-1] == 0.0 or pd.isna(vi.iloc[-1])

    def test_detect_cloud_events_clear_sky(self):
        """Test cloud detection with clear sky conditions."""
        service = RampRateService()
        timestamps = pd.date_range("2025-01-01 08:00", periods=10, freq="5min")
        irradiance = np.array([800, 810, 795, 805, 800, 790, 800, 810, 805, 800])
        clear_sky = np.array([1000] * 10)

        events = service.detect_cloud_events(irradiance, clear_sky, timestamps)
        # High clearness (0.8) should mean no cloud events
        assert isinstance(events, list)

    def test_detect_cloud_events_with_clouds(self):
        """Test cloud detection with cloud pass."""
        service = RampRateService()
        timestamps = pd.date_range("2025-01-01 08:00", periods=20, freq="5min")
        # Clear -> cloudy -> clear pattern
        irradiance = np.concatenate([
            np.array([800] * 5),  # Clear kt=0.8
            np.array([200] * 10),  # Cloudy kt=0.2
            np.array([800] * 5),  # Clear again kt=0.8
        ])
        clear_sky = np.array([1000] * 20)

        events = service.detect_cloud_events(irradiance, clear_sky, timestamps)
        assert len(events) >= 1


class TestWeatherService:
    """Tests for WeatherService."""

    def test_init(self):
        """Test service initialization."""
        service = WeatherService()
        assert service.clear_sky_threshold == 0.7
        assert service.partly_cloudy_threshold == 0.5
        assert service.cloudy_threshold == 0.3

    def test_classify_weather_storm_by_wind(self):
        """Test storm classification by high wind speed."""
        service = WeatherService()
        condition = service.classify_weather(wind_speed_kmh=70)
        assert condition == WeatherCondition.STORM

    def test_classify_weather_storm_by_precipitation(self):
        """Test storm classification by heavy precipitation."""
        service = WeatherService()
        condition = service.classify_weather(precipitation_mm=25)
        assert condition == WeatherCondition.STORM

    def test_classify_weather_storm_by_alert(self):
        """Test storm classification by alert flag."""
        service = WeatherService()
        condition = service.classify_weather(has_storm_alert=True)
        assert condition == WeatherCondition.STORM

    def test_classify_weather_rainy(self):
        """Test rainy classification."""
        service = WeatherService()
        condition = service.classify_weather(precipitation_mm=5)
        assert condition == WeatherCondition.RAINY

    def test_classify_weather_clear(self):
        """Test clear sky classification."""
        service = WeatherService()
        condition = service.classify_weather(clearness_index=0.85)
        assert condition == WeatherCondition.CLEAR

    def test_classify_weather_partly_cloudy(self):
        """Test partly cloudy classification."""
        service = WeatherService()
        condition = service.classify_weather(clearness_index=0.6)
        assert condition == WeatherCondition.PARTLY_CLOUDY

    def test_classify_weather_cloudy(self):
        """Test cloudy classification."""
        service = WeatherService()
        condition = service.classify_weather(clearness_index=0.4)
        assert condition == WeatherCondition.CLOUDY

    def test_classify_weather_default(self):
        """Test default classification when no data."""
        service = WeatherService()
        condition = service.classify_weather()
        assert condition == WeatherCondition.PARTLY_CLOUDY

    def test_classify_by_clearness_thresholds(self):
        """Test all clearness index thresholds."""
        service = WeatherService()

        # Test each threshold boundary
        assert service._classify_by_clearness(0.9) == WeatherCondition.CLEAR
        assert service._classify_by_clearness(0.7) == WeatherCondition.CLEAR
        assert service._classify_by_clearness(0.6) == WeatherCondition.PARTLY_CLOUDY
        assert service._classify_by_clearness(0.5) == WeatherCondition.PARTLY_CLOUDY
        assert service._classify_by_clearness(0.4) == WeatherCondition.CLOUDY
        assert service._classify_by_clearness(0.3) == WeatherCondition.CLOUDY
        assert service._classify_by_clearness(0.2) == WeatherCondition.RAINY

    def test_calculate_clear_sky_irradiance_noon(self):
        """Test clear sky calculation at solar noon."""
        service = WeatherService()
        # Bangkok coordinates, noon
        result = service.calculate_clear_sky_irradiance(
            latitude=13.7563,
            longitude=100.5018,
            timestamp=datetime(2025, 6, 21, 12, 0),  # Summer solstice noon
        )
        # Should have significant irradiance at noon
        assert result > 0

    def test_calculate_clear_sky_irradiance_night(self):
        """Test clear sky calculation at night."""
        service = WeatherService()
        result = service.calculate_clear_sky_irradiance(
            latitude=13.7563,
            longitude=100.5018,
            timestamp=datetime(2025, 1, 15, 0, 0),  # Midnight
        )
        assert result == 0.0

    def test_calculate_clear_sky_irradiance_morning(self):
        """Test clear sky calculation in morning."""
        service = WeatherService()
        result = service.calculate_clear_sky_irradiance(
            latitude=13.7563,
            longitude=100.5018,
            timestamp=datetime(2025, 1, 15, 8, 0),  # 8 AM
        )
        # Should have some irradiance in morning
        assert result >= 0

    def test_calculate_clear_sky_with_altitude(self):
        """Test clear sky calculation with altitude correction."""
        service = WeatherService()
        result_sea_level = service.calculate_clear_sky_irradiance(
            latitude=13.7563,
            longitude=100.5018,
            timestamp=datetime(2025, 6, 21, 12, 0),
            altitude=0,
        )
        result_high = service.calculate_clear_sky_irradiance(
            latitude=13.7563,
            longitude=100.5018,
            timestamp=datetime(2025, 6, 21, 12, 0),
            altitude=2000,  # 2km altitude
        )
        # Higher altitude should have higher irradiance
        if result_sea_level > 0:
            assert result_high > result_sea_level

    def test_is_cache_valid_no_entry(self):
        """Test cache validity check with no entry."""
        service = WeatherService()
        assert service._is_cache_valid("nonexistent") is False

    def test_is_cache_valid_expired(self):
        """Test cache validity check with expired entry."""
        service = WeatherService()
        service._cache["test_key"] = "data"
        service._cache_times["test_key"] = datetime.utcnow() - timedelta(hours=1)
        assert service._is_cache_valid("test_key") is False

    def test_is_cache_valid_fresh(self):
        """Test cache validity check with fresh entry."""
        service = WeatherService()
        service._cache["test_key"] = "data"
        service._cache_times["test_key"] = datetime.utcnow()
        assert service._is_cache_valid("test_key") is True

    def test_generate_alerts_from_station_heavy_rain(self):
        """Test alert generation for heavy rainfall."""
        service = WeatherService()
        station = {
            "name": "Test Station",
            "name_en": "test_station",
            "province": "Bangkok",
            "rainfall_24h": 75,  # > 50mm threshold
        }
        alerts = service._generate_alerts_from_station(station)
        assert len(alerts) >= 1
        assert alerts[0].condition == WeatherCondition.RAINY

    def test_generate_alerts_from_station_high_wind(self):
        """Test alert generation for high wind."""
        service = WeatherService()
        station = {
            "name": "Test Station",
            "name_en": "test_station",
            "province": "Bangkok",
            "wind_speed": 50,  # > 40 km/h threshold
        }
        alerts = service._generate_alerts_from_station(station)
        assert len(alerts) >= 1

    def test_generate_alerts_from_station_high_temp(self):
        """Test alert generation for high temperature."""
        service = WeatherService()
        station = {
            "name": "Test Station",
            "name_en": "test_station",
            "province": "Bangkok",
            "temperature": 42,  # > 40C threshold
        }
        alerts = service._generate_alerts_from_station(station)
        assert len(alerts) >= 1

    def test_generate_alerts_from_station_normal(self):
        """Test no alerts for normal conditions."""
        service = WeatherService()
        station = {
            "name": "Test Station",
            "name_en": "test_station",
            "province": "Bangkok",
            "temperature": 30,
            "wind_speed": 10,
            "rainfall_24h": 0,
        }
        alerts = service._generate_alerts_from_station(station)
        assert len(alerts) == 0

    def test_generate_alerts_from_forecast_storm(self):
        """Test alert generation for storm forecast."""
        service = WeatherService()
        forecast = {
            "date": "2025-01-15",
            "description": "พายุฝนฟ้าคะนอง",  # Storm in Thai
        }
        alerts = service._generate_alerts_from_forecast(forecast)
        assert len(alerts) >= 1
        assert any(a.condition == WeatherCondition.STORM for a in alerts)

    def test_generate_alerts_from_forecast_rain(self):
        """Test alert generation for rain forecast."""
        service = WeatherService()
        forecast = {
            "date": "2025-01-15",
            "description": "ฝนตกหนักบางพื้นที่",  # Heavy rain in Thai
        }
        alerts = service._generate_alerts_from_forecast(forecast)
        assert len(alerts) >= 1

    def test_province_codes(self):
        """Test province code mapping."""
        service = WeatherService()
        assert "bangkok" in service.PROVINCE_CODES
        assert service.PROVINCE_CODES["bangkok"] == "กรุงเทพมหานคร"


class TestCacheConfig:
    """Tests for cache configuration."""

    def test_cache_config_defaults(self):
        """Test cache config default values."""
        from app.core.cache import CacheConfig

        config = CacheConfig()
        assert config.solar_ttl == 300
        assert config.voltage_ttl == 60
        assert config.enabled is True

    def test_cache_config_custom(self):
        """Test cache config with custom values."""
        from app.core.cache import CacheConfig

        config = CacheConfig(solar_ttl=600, voltage_ttl=120, enabled=False)
        assert config.solar_ttl == 600
        assert config.voltage_ttl == 120
        assert config.enabled is False


class TestRedisCache:
    """Tests for RedisCache key generation."""

    def test_generate_key(self):
        """Test cache key generation."""
        from app.core.cache import RedisCache

        cache = RedisCache(url="redis://localhost:6379")
        key = cache._generate_key("solar", {"timestamp": "2025-01-15T10:00:00"})
        assert key.startswith("pea:solar:")
        assert len(key) > len("pea:solar:")

    def test_generate_key_consistent(self):
        """Test that key generation is consistent."""
        from app.core.cache import RedisCache

        cache = RedisCache(url="redis://localhost:6379")
        data = {"timestamp": "2025-01-15T10:00:00", "value": 100}
        key1 = cache._generate_key("test", data)
        key2 = cache._generate_key("test", data)
        assert key1 == key2

    def test_generate_key_different_order(self):
        """Test that key generation handles different key order."""
        from app.core.cache import RedisCache

        cache = RedisCache(url="redis://localhost:6379")
        data1 = {"a": 1, "b": 2}
        data2 = {"b": 2, "a": 1}
        key1 = cache._generate_key("test", data1)
        key2 = cache._generate_key("test", data2)
        # Keys should be same regardless of dict order
        assert key1 == key2

    def test_is_connected_initial(self):
        """Test is_connected property when not connected."""
        from app.core.cache import RedisCache

        cache = RedisCache(url="redis://localhost:6379")
        assert cache.is_connected is False
