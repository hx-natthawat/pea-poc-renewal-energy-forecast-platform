"""
API v1 Router - Aggregates all API endpoints.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import forecast, health, data, alerts
from app.api.v1.websocket import realtime as websocket_realtime

api_router = APIRouter()

# Health endpoints
api_router.include_router(
    health.router,
    tags=["health"],
)

# Forecast endpoints
api_router.include_router(
    forecast.router,
    prefix="/forecast",
    tags=["forecast"],
)

# Data ingestion endpoints
api_router.include_router(
    data.router,
    prefix="/data",
    tags=["data"],
)

# Alert management endpoints
api_router.include_router(
    alerts.router,
    prefix="/alerts",
    tags=["alerts"],
)

# WebSocket endpoints for real-time updates
api_router.include_router(
    websocket_realtime.router,
    tags=["websocket"],
)
