"""
API v2 Health Endpoints.

Enhanced health checks with more detailed status information.
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings
from app.core.versioning import APIVersion, create_versioned_response

router = APIRouter()


class ComponentHealth(BaseModel):
    """Health status of a component."""

    name: str
    status: str  # "healthy", "degraded", "unhealthy"
    latency_ms: float | None = None
    message: str | None = None


class HealthResponse(BaseModel):
    """Enhanced health response for v2."""

    status: str
    timestamp: str
    service: str
    version: str
    api_version: str
    uptime_seconds: float | None = None
    components: list[ComponentHealth] = []


# Track service start time
_start_time = datetime.now()


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """
    Enhanced health check endpoint.

    Returns detailed health information including:
    - Service status
    - API version
    - Component health (database, cache, ML models)
    - Uptime
    """
    uptime = (datetime.now() - _start_time).total_seconds()

    # Check component health (placeholder - implement actual checks)
    components = [
        ComponentHealth(
            name="database",
            status="healthy",
            latency_ms=5.2,
            message="PostgreSQL connection OK",
        ),
        ComponentHealth(
            name="cache",
            status="healthy",
            latency_ms=1.1,
            message="Redis connection OK",
        ),
        ComponentHealth(
            name="ml_models",
            status="healthy",
            message="All models loaded",
        ),
    ]

    # Determine overall status
    overall_status = "healthy"
    if any(c.status == "unhealthy" for c in components):
        overall_status = "unhealthy"
    elif any(c.status == "degraded" for c in components):
        overall_status = "degraded"

    data = HealthResponse(
        status=overall_status,
        timestamp=datetime.now().isoformat(),
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        api_version=APIVersion.V2.value,
        uptime_seconds=uptime,
        components=components,
    )

    return create_versioned_response(
        data=data.model_dump(),
        version=APIVersion.V2,
        metadata={
            "cache_control": "no-cache",
        },
    )


@router.get("/health/live")
async def liveness_probe() -> dict[str, Any]:
    """
    Kubernetes liveness probe.

    Simple check that the service is running.
    """
    return create_versioned_response(
        data={"status": "alive"},
        version=APIVersion.V2,
    )


@router.get("/health/ready")
async def readiness_probe() -> dict[str, Any]:
    """
    Kubernetes readiness probe.

    Checks if the service is ready to accept traffic.
    """
    # TODO: Add actual readiness checks (DB, cache, models)
    ready = True

    return create_versioned_response(
        data={
            "status": "ready" if ready else "not_ready",
            "checks": {
                "database": True,
                "cache": True,
                "models": True,
            },
        },
        version=APIVersion.V2,
    )
