"""
PEA RE Forecast Platform - Main Application Entry Point.

This is the FastAPI application entry point for the PEA Renewable Energy
Forecast Platform.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.api.v2.router import api_router as api_router_v2
from app.core.config import settings
from app.core.metrics import (
    PrometheusMiddleware,
    init_metrics,
    metrics_endpoint,
    set_model_loaded,
)
from app.core.middleware import SecurityHeadersMiddleware
from app.core.rate_limit import RateLimitConfig, RateLimitMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Application lifespan manager for startup/shutdown events."""
    # Startup
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # Initialize Prometheus metrics
    init_metrics(settings.APP_NAME, settings.APP_VERSION)

    # Set initial model status (will be updated when models are loaded)
    set_model_loaded("solar", "v1.0.0", False)
    set_model_loaded("voltage", "v1.0.0", False)

    # TODO: Initialize database connections
    # TODO: Initialize Redis connection
    # TODO: Load ML models
    yield
    # Shutdown
    print(f"Shutting down {settings.APP_NAME}")
    # TODO: Close database connections
    # TODO: Close Redis connection


app = FastAPI(
    title=settings.APP_NAME,
    description="PEA Renewable Energy Forecast Platform API",
    version=settings.APP_VERSION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    lifespan=lifespan,
)

# CORS middleware - explicit allow lists for security
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "X-Requested-With",
        "X-Request-ID",
    ],
    expose_headers=["X-Request-ID", "X-RateLimit-Remaining"],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Security headers middleware (OWASP best practices)
app.add_middleware(SecurityHeadersMiddleware)

# Prometheus metrics middleware
app.add_middleware(PrometheusMiddleware)

# Rate limiting middleware
rate_limit_config = RateLimitConfig(
    requests_per_minute=120,
    requests_per_second=20,
    exempt_paths=[
        "/metrics",
        "/api/v1/health",
        "/api/v1/docs",
        "/api/v1/openapi.json",
        "/api/v2/health",
        "/api/v2/health/live",
        "/api/v2/health/ready",
        "/api/v2/docs",
        "/api/v2/openapi.json",
    ],
)
app.add_middleware(RateLimitMiddleware, config=rate_limit_config)

# Include API routers
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
app.include_router(api_router_v2, prefix="/api/v2")

# Prometheus metrics endpoint
app.add_api_route(
    "/metrics", metrics_endpoint, methods=["GET"], include_in_schema=False
)


# Global exception handler to ensure CORS headers on errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions with proper JSON response and CORS headers."""
    import logging

    logger = logging.getLogger(__name__)
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)

    origin = request.headers.get("origin", "")
    headers = {}
    if origin in settings.CORS_ORIGINS:
        headers = {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
        }

    # Only expose error details in debug mode
    content = {"detail": "Internal server error"}
    if settings.DEBUG:
        content["error"] = str(exc)

    return JSONResponse(
        status_code=500,
        content=content,
        headers=headers,
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "api_versions": {
            "v1": {
                "status": "stable",
                "docs": f"{settings.API_V1_PREFIX}/docs",
                "health": f"{settings.API_V1_PREFIX}/health",
            },
            "v2": {
                "status": "beta",
                "docs": "/api/v2/docs",
                "health": "/api/v2/health",
            },
        },
        "docs": f"{settings.API_V1_PREFIX}/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
