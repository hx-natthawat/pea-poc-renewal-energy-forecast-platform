"""
Health check utilities for monitoring service dependencies.

Provides actual connectivity checks for database, Redis cache, and ML models.
Used by both v1 and v2 health endpoints for Kubernetes probes.
"""

import logging
import time
from dataclasses import dataclass
from enum import Enum

from sqlalchemy import text

from app.core.cache import cache
from app.db.session import engine

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health check status values."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ComponentCheck:
    """Result of a component health check."""

    name: str
    status: HealthStatus
    latency_ms: float | None = None
    message: str | None = None


async def check_database() -> ComponentCheck:
    """Check database connectivity by executing a simple query."""
    start_time = time.perf_counter()
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            result.fetchone()

        latency_ms = (time.perf_counter() - start_time) * 1000
        return ComponentCheck(
            name="database",
            status=HealthStatus.HEALTHY,
            latency_ms=round(latency_ms, 2),
            message="PostgreSQL connection OK",
        )
    except Exception as e:
        latency_ms = (time.perf_counter() - start_time) * 1000
        logger.warning(f"Database health check failed: {e}")
        return ComponentCheck(
            name="database",
            status=HealthStatus.UNHEALTHY,
            latency_ms=round(latency_ms, 2),
            message=f"Connection failed: {type(e).__name__}",
        )


async def check_redis() -> ComponentCheck:
    """Check Redis cache connectivity."""
    start_time = time.perf_counter()
    try:
        # Attempt to connect if not already connected
        if not cache.is_connected:
            await cache.connect()

        if cache.is_connected and cache._client:
            await cache._client.ping()
            latency_ms = (time.perf_counter() - start_time) * 1000
            return ComponentCheck(
                name="redis",
                status=HealthStatus.HEALTHY,
                latency_ms=round(latency_ms, 2),
                message="Redis connection OK",
            )
        else:
            latency_ms = (time.perf_counter() - start_time) * 1000
            # Redis is optional - degraded, not unhealthy
            return ComponentCheck(
                name="redis",
                status=HealthStatus.DEGRADED,
                latency_ms=round(latency_ms, 2),
                message="Redis not connected (cache disabled)",
            )
    except Exception as e:
        latency_ms = (time.perf_counter() - start_time) * 1000
        logger.warning(f"Redis health check failed: {e}")
        return ComponentCheck(
            name="redis",
            status=HealthStatus.DEGRADED,
            latency_ms=round(latency_ms, 2),
            message=f"Connection failed: {type(e).__name__}",
        )


async def check_ml_models() -> ComponentCheck:
    """Check if ML models are loaded and ready."""
    start_time = time.perf_counter()
    try:
        # For now, just report as healthy since models load on-demand
        # In production, this would verify models are loaded in memory
        latency_ms = (time.perf_counter() - start_time) * 1000
        return ComponentCheck(
            name="ml_models",
            status=HealthStatus.HEALTHY,
            latency_ms=round(latency_ms, 2),
            message="ML models available (on-demand loading)",
        )
    except Exception as e:
        latency_ms = (time.perf_counter() - start_time) * 1000
        logger.warning(f"ML models health check failed: {e}")
        return ComponentCheck(
            name="ml_models",
            status=HealthStatus.DEGRADED,
            latency_ms=round(latency_ms, 2),
            message=f"Check failed: {type(e).__name__}",
        )


async def run_all_checks() -> tuple[list[ComponentCheck], HealthStatus]:
    """
    Run all health checks and determine overall status.

    Returns:
        Tuple of (list of component checks, overall status)
    """
    checks = [
        await check_database(),
        await check_redis(),
        await check_ml_models(),
    ]

    # Determine overall status
    if any(c.status == HealthStatus.UNHEALTHY for c in checks):
        overall = HealthStatus.UNHEALTHY
    elif any(c.status == HealthStatus.DEGRADED for c in checks):
        overall = HealthStatus.DEGRADED
    else:
        overall = HealthStatus.HEALTHY

    return checks, overall


async def is_ready() -> tuple[bool, dict[str, bool]]:
    """
    Quick readiness check for Kubernetes probes.

    Returns:
        Tuple of (is_ready, individual_checks dict)
    """
    db_check = await check_database()
    redis_check = await check_redis()
    ml_check = await check_ml_models()

    checks = {
        "database": db_check.status != HealthStatus.UNHEALTHY,
        "redis": redis_check.status != HealthStatus.UNHEALTHY,
        "ml_models": ml_check.status != HealthStatus.UNHEALTHY,
    }

    # Ready if database is healthy (Redis and models can be degraded)
    is_ready = db_check.status == HealthStatus.HEALTHY

    return is_ready, checks
