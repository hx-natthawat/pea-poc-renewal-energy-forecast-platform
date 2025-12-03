"""
API v1 Router - Aggregates all API endpoints.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import alerts, comparison, data, dayahead, forecast, health, history, monitoring, topology
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

# Network topology endpoints
api_router.include_router(
    topology.router,
    prefix="/topology",
    tags=["topology"],
)

# Forecast comparison endpoints
api_router.include_router(
    comparison.router,
    prefix="/comparison",
    tags=["comparison"],
)

# Historical analysis endpoints
api_router.include_router(
    history.router,
    prefix="/history",
    tags=["history"],
)

# Day-ahead forecast endpoints
api_router.include_router(
    dayahead.router,
    prefix="/dayahead",
    tags=["dayahead"],
)

# Model monitoring endpoints
api_router.include_router(
    monitoring.router,
    prefix="/monitoring",
    tags=["monitoring"],
)

# WebSocket endpoints for real-time updates
api_router.include_router(
    websocket_realtime.router,
    tags=["websocket"],
)
