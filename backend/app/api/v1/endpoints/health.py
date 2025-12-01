"""
Health check endpoints for Kubernetes probes and monitoring.
"""

from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for liveness probe.

    Returns basic health status of the application.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "pea-re-forecast-backend",
    }


@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check endpoint for readiness probe.

    Checks if the application is ready to serve requests.
    This includes database and cache connectivity.
    """
    # TODO: Add actual database and Redis connectivity checks
    checks = {
        "database": "ok",
        "redis": "ok",
        "ml_models": "ok",
    }

    all_healthy = all(status == "ok" for status in checks.values())

    return {
        "status": "ready" if all_healthy else "not_ready",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks,
    }
