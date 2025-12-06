"""
API v1 Router - Aggregates all API endpoints.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    alerts,
    audit,
    comparison,
    data,
    dayahead,
    demand_forecast,
    demo,
    forecast,
    health,
    history,
    imbalance_forecast,
    load_forecast,
    monitoring,
    notifications,
    regions,
    retraining,
    topology,
    weather,
)
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

# Model retraining endpoints (v1.1.0)
api_router.include_router(
    retraining.router,
    prefix="/retraining",
    tags=["retraining"],
)

# Notification endpoints (v1.1.0)
api_router.include_router(
    notifications.router,
    prefix="/notifications",
    tags=["notifications"],
)

# Region endpoints (v1.1.0)
api_router.include_router(
    regions.router,
    prefix="/regions",
    tags=["regions"],
)

# Weather handling endpoints
api_router.include_router(
    weather.router,
    tags=["weather"],
)

# Audit log endpoints (TOR 7.1.6)
api_router.include_router(
    audit.router,
    prefix="/audit",
    tags=["audit"],
)

# Demo endpoints for stakeholder demonstrations
api_router.include_router(
    demo.router,
    tags=["demo"],
)

# Phase 2: Load Forecast endpoints (TOR Function 3)
api_router.include_router(
    load_forecast.router,
    prefix="/load-forecast",
    tags=["load-forecast", "phase2"],
)

# Phase 2: Demand Forecast endpoints (TOR Function 2)
api_router.include_router(
    demand_forecast.router,
    prefix="/demand-forecast",
    tags=["demand-forecast", "phase2"],
)

# Phase 2: Imbalance Forecast endpoints (TOR Function 4)
api_router.include_router(
    imbalance_forecast.router,
    prefix="/imbalance-forecast",
    tags=["imbalance-forecast", "phase2"],
)

# WebSocket endpoints for real-time updates
api_router.include_router(
    websocket_realtime.router,
    tags=["websocket"],
)
