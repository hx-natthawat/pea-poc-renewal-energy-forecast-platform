"""
Unit tests for Redis cache service.

Tests caching for solar and voltage predictions.
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.core.cache import CacheConfig, RedisCache, get_cache

# =============================================================================
# Test CacheConfig
# =============================================================================


class TestCacheConfigExtended:
    """Extended tests for CacheConfig."""

    def test_default_solar_ttl(self):
        config = CacheConfig()
        assert config.solar_ttl == 300

    def test_default_voltage_ttl(self):
        config = CacheConfig()
        assert config.voltage_ttl == 60

    def test_default_enabled(self):
        config = CacheConfig()
        assert config.enabled is True

    def test_custom_values(self):
        config = CacheConfig(solar_ttl=600, voltage_ttl=120, enabled=False)
        assert config.solar_ttl == 600
        assert config.voltage_ttl == 120
        assert config.enabled is False


# =============================================================================
# Test RedisCache
# =============================================================================


class TestRedisCacheConnection:
    """Test Redis connection management."""

    @pytest.mark.asyncio
    async def test_connect_success(self):
        """Test successful Redis connection."""
        cache = RedisCache(url="redis://localhost:6379")

        with patch("app.core.cache.redis") as mock_redis:
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock(return_value=True)
            mock_redis.from_url.return_value = mock_client

            result = await cache.connect()

            assert result is True
            assert cache.is_connected is True

    @pytest.mark.asyncio
    async def test_connect_failure(self):
        """Test Redis connection failure."""
        cache = RedisCache(url="redis://localhost:6379")

        with patch("app.core.cache.redis") as mock_redis:
            mock_redis.from_url.side_effect = Exception("Connection refused")

            result = await cache.connect()

            assert result is False
            assert cache.is_connected is False

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test Redis disconnection."""
        cache = RedisCache(url="redis://localhost:6379")

        with patch("app.core.cache.redis") as mock_redis:
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock(return_value=True)
            mock_client.close = AsyncMock()
            mock_redis.from_url.return_value = mock_client

            await cache.connect()
            await cache.disconnect()

            assert cache.is_connected is False
            mock_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_already_connected(self):
        """Test that connect returns True when already connected."""
        cache = RedisCache(url="redis://localhost:6379")

        with patch("app.core.cache.redis") as mock_redis:
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock(return_value=True)
            mock_redis.from_url.return_value = mock_client

            # First connection
            await cache.connect()
            # Second connection should return True without reconnecting
            result = await cache.connect()

            assert result is True
            # Should only call from_url once
            assert mock_redis.from_url.call_count == 1


class TestRedisCacheKeyGeneration:
    """Test cache key generation."""

    def test_generate_key_consistent(self):
        """Test that same data generates same key."""
        cache = RedisCache(url="redis://localhost:6379")

        data1 = {"timestamp": "2025-01-15T10:00:00", "pyrano1": 800.0}
        data2 = {"timestamp": "2025-01-15T10:00:00", "pyrano1": 800.0}

        key1 = cache._generate_key("solar", data1)
        key2 = cache._generate_key("solar", data2)

        assert key1 == key2

    def test_generate_key_different_data(self):
        """Test that different data generates different keys."""
        cache = RedisCache(url="redis://localhost:6379")

        data1 = {"timestamp": "2025-01-15T10:00:00", "pyrano1": 800.0}
        data2 = {"timestamp": "2025-01-15T10:00:00", "pyrano1": 900.0}

        key1 = cache._generate_key("solar", data1)
        key2 = cache._generate_key("solar", data2)

        assert key1 != key2

    def test_generate_key_order_independent(self):
        """Test that key generation is order-independent."""
        cache = RedisCache(url="redis://localhost:6379")

        data1 = {"a": 1, "b": 2}
        data2 = {"b": 2, "a": 1}

        key1 = cache._generate_key("test", data1)
        key2 = cache._generate_key("test", data2)

        assert key1 == key2

    def test_generate_key_prefix(self):
        """Test that key includes correct prefix."""
        cache = RedisCache(url="redis://localhost:6379")

        key = cache._generate_key("solar", {"test": "data"})

        assert key.startswith("pea:solar:")


class TestRedisCacheSolarPrediction:
    """Test solar prediction caching."""

    @pytest.mark.asyncio
    async def test_get_solar_prediction_cache_hit(self):
        """Test getting cached solar prediction."""
        cache = RedisCache(url="redis://localhost:6379")

        with patch("app.core.cache.redis") as mock_redis:
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock(return_value=True)
            mock_client.get = AsyncMock(return_value=json.dumps({"power_kw": 1500.0}))
            mock_redis.from_url.return_value = mock_client

            await cache.connect()

            result = await cache.get_solar_prediction(
                timestamp=datetime(2025, 1, 15, 10, 0, 0),
                features={"pyrano1": 800.0},
            )

            assert result is not None
            assert result["power_kw"] == 1500.0

    @pytest.mark.asyncio
    async def test_get_solar_prediction_cache_miss(self):
        """Test cache miss for solar prediction."""
        cache = RedisCache(url="redis://localhost:6379")

        with patch("app.core.cache.redis") as mock_redis:
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock(return_value=True)
            mock_client.get = AsyncMock(return_value=None)
            mock_redis.from_url.return_value = mock_client

            await cache.connect()

            result = await cache.get_solar_prediction(
                timestamp=datetime(2025, 1, 15, 10, 0, 0),
                features={"pyrano1": 800.0},
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_set_solar_prediction(self):
        """Test setting solar prediction in cache."""
        cache = RedisCache(url="redis://localhost:6379")

        with patch("app.core.cache.redis") as mock_redis:
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock(return_value=True)
            mock_client.setex = AsyncMock(return_value=True)
            mock_redis.from_url.return_value = mock_client

            await cache.connect()

            result = await cache.set_solar_prediction(
                timestamp=datetime(2025, 1, 15, 10, 0, 0),
                features={"pyrano1": 800.0},
                prediction={"power_kw": 1500.0},
            )

            assert result is True
            mock_client.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_solar_prediction_disabled_cache(self):
        """Test solar prediction when cache is disabled."""
        cache = RedisCache(url="redis://localhost:6379")
        cache.config.enabled = False

        result = await cache.get_solar_prediction(
            timestamp=datetime(2025, 1, 15, 10, 0, 0),
            features={"pyrano1": 800.0},
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_solar_prediction_not_connected(self):
        """Test solar prediction when not connected."""
        cache = RedisCache(url="redis://localhost:6379")

        result = await cache.get_solar_prediction(
            timestamp=datetime(2025, 1, 15, 10, 0, 0),
            features={"pyrano1": 800.0},
        )

        assert result is None


class TestRedisCacheVoltagePrediction:
    """Test voltage prediction caching."""

    @pytest.mark.asyncio
    async def test_get_voltage_prediction_cache_hit(self):
        """Test getting cached voltage prediction."""
        cache = RedisCache(url="redis://localhost:6379")

        with patch("app.core.cache.redis") as mock_redis:
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock(return_value=True)
            mock_client.get = AsyncMock(return_value=json.dumps({"voltage": 230.5}))
            mock_redis.from_url.return_value = mock_client

            await cache.connect()

            result = await cache.get_voltage_prediction(
                timestamp=datetime(2025, 1, 15, 10, 0, 0),
                prosumer_id="prosumer1",
            )

            assert result is not None
            assert result["voltage"] == 230.5

    @pytest.mark.asyncio
    async def test_set_voltage_prediction(self):
        """Test setting voltage prediction in cache."""
        cache = RedisCache(url="redis://localhost:6379")

        with patch("app.core.cache.redis") as mock_redis:
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock(return_value=True)
            mock_client.setex = AsyncMock(return_value=True)
            mock_redis.from_url.return_value = mock_client

            await cache.connect()

            result = await cache.set_voltage_prediction(
                timestamp=datetime(2025, 1, 15, 10, 0, 0),
                prosumer_id="prosumer1",
                prediction={"voltage": 230.5},
            )

            assert result is True


class TestRedisCacheOperations:
    """Test cache operations."""

    @pytest.mark.asyncio
    async def test_clear_all(self):
        """Test clearing all cache entries."""
        cache = RedisCache(url="redis://localhost:6379")

        with patch("app.core.cache.redis") as mock_redis:
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock(return_value=True)
            mock_client.keys = AsyncMock(
                return_value=["pea:solar:123", "pea:voltage:456"]
            )
            mock_client.delete = AsyncMock(return_value=2)
            mock_redis.from_url.return_value = mock_client

            await cache.connect()

            result = await cache.clear_all()

            assert result == 2

    @pytest.mark.asyncio
    async def test_clear_all_empty(self):
        """Test clearing cache when empty."""
        cache = RedisCache(url="redis://localhost:6379")

        with patch("app.core.cache.redis") as mock_redis:
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock(return_value=True)
            mock_client.keys = AsyncMock(return_value=[])
            mock_redis.from_url.return_value = mock_client

            await cache.connect()

            result = await cache.clear_all()

            assert result == 0

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Test getting cache statistics."""
        cache = RedisCache(url="redis://localhost:6379")

        with patch("app.core.cache.redis") as mock_redis:
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock(return_value=True)
            mock_client.info = AsyncMock(
                return_value={"keyspace_hits": 100, "keyspace_misses": 20}
            )
            mock_client.keys = AsyncMock(return_value=["pea:solar:123"])
            mock_redis.from_url.return_value = mock_client

            await cache.connect()

            stats = await cache.get_stats()

            assert stats["connected"] is True
            assert stats["hits"] == 100
            assert stats["misses"] == 20
            assert stats["total_keys"] == 1

    @pytest.mark.asyncio
    async def test_get_stats_not_connected(self):
        """Test getting stats when not connected."""
        cache = RedisCache(url="redis://localhost:6379")

        stats = await cache.get_stats()

        assert stats["connected"] is False
        assert stats["enabled"] is True


class TestGetCacheFunction:
    """Test get_cache utility function."""

    @pytest.mark.asyncio
    async def test_get_cache_connects_if_needed(self):
        """Test that get_cache connects if not connected."""
        with patch("app.core.cache.cache") as mock_cache:
            mock_cache.is_connected = False
            mock_cache.connect = AsyncMock(return_value=True)

            await get_cache()

            mock_cache.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_cache_returns_cache(self):
        """Test that get_cache returns the cache instance."""
        with patch("app.core.cache.cache") as mock_cache:
            mock_cache.is_connected = True

            result = await get_cache()

            assert result == mock_cache
