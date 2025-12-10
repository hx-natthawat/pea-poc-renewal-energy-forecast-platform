"""
Health check endpoints for Kubernetes probes and monitoring.
"""

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter

from app.core.health import is_ready

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """
    Health check endpoint for liveness probe.

    Returns basic health status of the application.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "service": "pea-re-forecast-backend",
    }


@router.get("/ready")
async def readiness_check() -> dict[str, Any]:
    """
    Readiness check endpoint for readiness probe.

    Checks if the application is ready to serve requests.
    This includes database and cache connectivity.
    """
    ready, checks = await is_ready()

    # Convert bool checks to status strings for backward compatibility
    check_status = {
        name: "ok" if status else "error" for name, status in checks.items()
    }

    return {
        "status": "ready" if ready else "not_ready",
        "timestamp": datetime.now(UTC).isoformat(),
        "checks": check_status,
    }
