"""
PEA RE Forecast Platform - Main Application Entry Point.

This is the FastAPI application entry point for the PEA Renewable Energy
Forecast Platform.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import HTMLResponse, JSONResponse

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
    from app.core.cache import cache
    from app.db.session import engine

    # Startup
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # Initialize Prometheus metrics
    init_metrics(settings.APP_NAME, settings.APP_VERSION)

    # Set initial model status (will be updated when models are loaded)
    set_model_loaded("solar", "v1.0.0", False)
    set_model_loaded("voltage", "v1.0.0", False)

    # Initialize Redis connection (optional - graceful degradation if unavailable)
    try:
        await cache.connect()
        print("Redis cache connected")
    except Exception as e:
        print(f"Redis cache unavailable (will operate without cache): {e}")

    # Database connection pool is lazy-initialized by SQLAlchemy
    # No explicit connection needed here

    yield

    # Shutdown
    print(f"Shutting down {settings.APP_NAME}")

    # Close Redis connection
    try:
        await cache.disconnect()
        print("Redis cache disconnected")
    except Exception:
        pass

    # Dispose database engine
    try:
        await engine.dispose()
        print("Database connections closed")
    except Exception:
        pass


app = FastAPI(
    title=settings.APP_NAME,
    description="PEA Renewable Energy Forecast Platform API",
    version=settings.APP_VERSION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=None,  # Disable default, use custom endpoint
    redoc_url=None,  # Disable default, use custom endpoint
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


# Custom Swagger UI with alternative CDN (unpkg.com instead of jsdelivr.net)
@app.get(f"{settings.API_V1_PREFIX}/docs", include_in_schema=False)
async def custom_swagger_ui_html() -> HTMLResponse:
    """Custom Swagger UI using unpkg.com CDN (more reliable in some networks)."""
    return get_swagger_ui_html(
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        title=f"{settings.APP_NAME} - Swagger UI",
        swagger_js_url="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css",
    )


@app.get(f"{settings.API_V1_PREFIX}/redoc", include_in_schema=False)
async def custom_redoc_html() -> HTMLResponse:
    """Custom ReDoc using unpkg.com CDN."""
    return get_redoc_html(
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        title=f"{settings.APP_NAME} - ReDoc",
        redoc_js_url="https://unpkg.com/redoc@2.1.3/bundles/redoc.standalone.js",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
