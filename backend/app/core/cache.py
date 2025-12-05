"""
Redis cache service for forecast predictions.

Provides caching for ML predictions to improve response times.
Solar forecasts can be cached because they depend on deterministic
input features (timestamp, irradiance, temperature, etc).
"""

import hashlib
import json
import logging
from datetime import datetime

import redis.asyncio as redis
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheConfig(BaseModel):
    """Cache configuration."""

    # Default TTL in seconds (5 minutes for solar, 1 minute for voltage)
    solar_ttl: int = 300
    voltage_ttl: int = 60
    enabled: bool = True


class RedisCache:
    """Redis-based cache for ML predictions."""

    def __init__(self, url: str = settings.REDIS_URL):
        self.url = url
        self._client: redis.Redis | None = None
        self.config = CacheConfig()
        self._connected = False

    async def connect(self) -> bool:
        """Connect to Redis."""
        if self._client is not None:
            return self._connected

        try:
            self._client = redis.from_url(
                self.url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # Test connection
            await self._client.ping()
            self._connected = True
            logger.info("Connected to Redis cache")
            return True
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Cache disabled.")
            self._connected = False
            return False

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._client:
            await self._client.close()
            self._client = None
            self._connected = False

    @property
    def is_connected(self) -> bool:
        """Check if connected to Redis."""
        return self._connected and self._client is not None

    def _generate_key(self, prefix: str, data: dict) -> str:
        """Generate a cache key from input data."""
        # Sort keys for consistent hashing
        sorted_data = json.dumps(data, sort_keys=True, default=str)
        hash_value = hashlib.md5(sorted_data.encode()).hexdigest()[:16]
        return f"pea:{prefix}:{hash_value}"

    async def get_solar_prediction(
        self,
        timestamp: datetime,
        features: dict,
    ) -> dict | None:
        """Get cached solar prediction."""
        if not self.is_connected or not self.config.enabled:
            return None

        try:
            # Round timestamp to nearest 5 minutes for better cache hit rate
            rounded_ts = timestamp.replace(
                minute=(timestamp.minute // 5) * 5,
                second=0,
                microsecond=0,
            )

            cache_data = {
                "timestamp": rounded_ts.isoformat(),
                **features,
            }
            key = self._generate_key("solar", cache_data)

            if self._client is None:
                return None
            cached = await self._client.get(key)
            if cached:
                logger.debug(f"Cache hit for solar prediction: {key}")
                return json.loads(cached)
            return None
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None

    async def set_solar_prediction(
        self,
        timestamp: datetime,
        features: dict,
        prediction: dict,
    ) -> bool:
        """Cache solar prediction result."""
        if not self.is_connected or not self.config.enabled or self._client is None:
            return False

        try:
            rounded_ts = timestamp.replace(
                minute=(timestamp.minute // 5) * 5,
                second=0,
                microsecond=0,
            )

            cache_data = {
                "timestamp": rounded_ts.isoformat(),
                **features,
            }
            key = self._generate_key("solar", cache_data)

            await self._client.setex(
                key,
                self.config.solar_ttl,
                json.dumps(prediction),
            )
            logger.debug(f"Cached solar prediction: {key}")
            return True
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
            return False

    async def get_voltage_prediction(
        self,
        timestamp: datetime,
        prosumer_id: str,
    ) -> dict | None:
        """Get cached voltage prediction."""
        if not self.is_connected or not self.config.enabled:
            return None

        try:
            # Round timestamp to nearest minute
            rounded_ts = timestamp.replace(second=0, microsecond=0)

            cache_data = {
                "timestamp": rounded_ts.isoformat(),
                "prosumer_id": prosumer_id,
            }
            key = self._generate_key("voltage", cache_data)

            if self._client is None:
                return None
            cached = await self._client.get(key)
            if cached:
                logger.debug(f"Cache hit for voltage prediction: {key}")
                return json.loads(cached)
            return None
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None

    async def set_voltage_prediction(
        self,
        timestamp: datetime,
        prosumer_id: str,
        prediction: dict,
    ) -> bool:
        """Cache voltage prediction result."""
        if not self.is_connected or not self.config.enabled or self._client is None:
            return False

        try:
            rounded_ts = timestamp.replace(second=0, microsecond=0)

            cache_data = {
                "timestamp": rounded_ts.isoformat(),
                "prosumer_id": prosumer_id,
            }
            key = self._generate_key("voltage", cache_data)

            await self._client.setex(
                key,
                self.config.voltage_ttl,
                json.dumps(prediction),
            )
            logger.debug(f"Cached voltage prediction: {key}")
            return True
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
            return False

    async def clear_all(self) -> int:
        """Clear all cache entries. Returns count of deleted keys."""
        if not self.is_connected or self._client is None:
            return 0

        try:
            keys = await self._client.keys("pea:*")
            if keys:
                return await self._client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Cache clear error: {e}")
            return 0

    async def get_stats(self) -> dict:
        """Get cache statistics."""
        if not self.is_connected or self._client is None:
            return {"connected": False, "enabled": self.config.enabled}

        try:
            info = await self._client.info("stats")
            keys = await self._client.keys("pea:*")
            return {
                "connected": True,
                "enabled": self.config.enabled,
                "total_keys": len(keys),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "solar_ttl": self.config.solar_ttl,
                "voltage_ttl": self.config.voltage_ttl,
            }
        except Exception as e:
            logger.warning(f"Cache stats error: {e}")
            return {"connected": False, "error": str(e)}


# Global cache instance
cache = RedisCache()


async def get_cache() -> RedisCache:
    """Get the global cache instance, connecting if needed."""
    if not cache.is_connected:
        await cache.connect()
    return cache
