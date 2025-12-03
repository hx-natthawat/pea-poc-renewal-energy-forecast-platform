"""
Prometheus Metrics Module for PEA RE Forecast Platform.

Provides:
- HTTP request metrics (count, latency)
- ML model inference metrics
- Database connection metrics
- Business metrics (predictions, alerts)
"""

import time
from functools import wraps
from typing import Callable

from fastapi import Request, Response
from prometheus_client import Counter, Gauge, Histogram, Info, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse


# =============================================================================
# Application Info
# =============================================================================

APP_INFO = Info(
    "pea_forecast_app",
    "PEA RE Forecast Platform application information",
)

# =============================================================================
# HTTP Request Metrics
# =============================================================================

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests currently being processed",
    ["method", "endpoint"],
)

# =============================================================================
# ML Model Metrics
# =============================================================================

ML_PREDICTIONS_TOTAL = Counter(
    "ml_predictions_total",
    "Total ML predictions made",
    ["model_type", "model_version"],
)

ML_INFERENCE_DURATION_SECONDS = Histogram(
    "ml_inference_duration_seconds",
    "ML model inference duration in seconds",
    ["model_type"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)

ML_PREDICTION_VALUES = Histogram(
    "ml_prediction_values",
    "Distribution of prediction values",
    ["model_type"],
    buckets=(0, 100, 500, 1000, 2000, 3000, 4000, 5000),  # For solar kW
)

ML_MODEL_LOADED = Gauge(
    "ml_model_loaded",
    "Whether ML model is loaded (1) or not (0)",
    ["model_type", "model_version"],
)

ML_MAPE = Gauge(
    "ml_model_mape",
    "Current MAPE for the model",
    ["model_type"],
)

ML_MAE = Gauge(
    "ml_model_mae",
    "Current MAE for the model",
    ["model_type"],
)

# =============================================================================
# Database Metrics
# =============================================================================

DB_CONNECTIONS_ACTIVE = Gauge(
    "db_connections_active",
    "Number of active database connections",
)

DB_CONNECTIONS_POOL_SIZE = Gauge(
    "db_connections_pool_size",
    "Database connection pool size",
)

DB_QUERY_DURATION_SECONDS = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["query_type"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
)

# =============================================================================
# Redis/Cache Metrics
# =============================================================================

CACHE_HITS_TOTAL = Counter(
    "cache_hits_total",
    "Total cache hits",
    ["cache_type"],
)

CACHE_MISSES_TOTAL = Counter(
    "cache_misses_total",
    "Total cache misses",
    ["cache_type"],
)

# =============================================================================
# WebSocket Metrics
# =============================================================================

WEBSOCKET_CONNECTIONS_ACTIVE = Gauge(
    "websocket_connections_active",
    "Number of active WebSocket connections",
)

WEBSOCKET_MESSAGES_SENT = Counter(
    "websocket_messages_sent_total",
    "Total WebSocket messages sent",
    ["message_type"],
)

# =============================================================================
# Alert Metrics
# =============================================================================

ALERTS_ACTIVE = Gauge(
    "alerts_active",
    "Number of active alerts",
    ["severity"],
)

ALERTS_CREATED_TOTAL = Counter(
    "alerts_created_total",
    "Total alerts created",
    ["alert_type", "severity"],
)

# =============================================================================
# Data Ingestion Metrics
# =============================================================================

DATA_POINTS_INGESTED = Counter(
    "data_points_ingested_total",
    "Total data points ingested",
    ["data_type", "source"],
)

DATA_INGESTION_ERRORS = Counter(
    "data_ingestion_errors_total",
    "Total data ingestion errors",
    ["data_type", "error_type"],
)


# =============================================================================
# Middleware
# =============================================================================


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to collect HTTP request metrics."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip metrics endpoint to avoid recursion
        if request.url.path == "/metrics":
            return await call_next(request)

        method = request.method
        # Normalize path to avoid high cardinality
        path = self._normalize_path(request.url.path)

        # Track in-progress requests
        HTTP_REQUESTS_IN_PROGRESS.labels(method=method, endpoint=path).inc()

        start_time = time.perf_counter()
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            raise e
        finally:
            # Record metrics
            duration = time.perf_counter() - start_time
            HTTP_REQUESTS_TOTAL.labels(
                method=method, endpoint=path, status_code=status_code
            ).inc()
            HTTP_REQUEST_DURATION_SECONDS.labels(method=method, endpoint=path).observe(
                duration
            )
            HTTP_REQUESTS_IN_PROGRESS.labels(method=method, endpoint=path).dec()

        return response

    def _normalize_path(self, path: str) -> str:
        """Normalize path to reduce cardinality."""
        # Replace IDs and dynamic segments
        parts = path.split("/")
        normalized = []
        for part in parts:
            # Replace UUIDs
            if len(part) == 36 and part.count("-") == 4:
                normalized.append("{id}")
            # Replace numeric IDs
            elif part.isdigit():
                normalized.append("{id}")
            # Replace prosumer IDs like prosumer1, prosumer2
            elif part.startswith("prosumer") and part[8:].isdigit():
                normalized.append("{prosumer_id}")
            else:
                normalized.append(part)
        return "/".join(normalized)


# =============================================================================
# Decorator for tracking inference time
# =============================================================================


def track_inference_time(model_type: str):
    """Decorator to track ML inference time."""

    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            result = await func(*args, **kwargs)
            duration = time.perf_counter() - start_time
            ML_INFERENCE_DURATION_SECONDS.labels(model_type=model_type).observe(
                duration
            )
            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            duration = time.perf_counter() - start_time
            ML_INFERENCE_DURATION_SECONDS.labels(model_type=model_type).observe(
                duration
            )
            return result

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# =============================================================================
# Utility Functions
# =============================================================================


def record_prediction(
    model_type: str, model_version: str, predicted_value: float
) -> None:
    """Record a prediction metric."""
    ML_PREDICTIONS_TOTAL.labels(
        model_type=model_type, model_version=model_version
    ).inc()
    ML_PREDICTION_VALUES.labels(model_type=model_type).observe(predicted_value)


def set_model_loaded(model_type: str, model_version: str, is_loaded: bool) -> None:
    """Set model loaded status."""
    ML_MODEL_LOADED.labels(model_type=model_type, model_version=model_version).set(
        1 if is_loaded else 0
    )


def set_model_accuracy(model_type: str, mape: float = None, mae: float = None) -> None:
    """Set model accuracy metrics."""
    if mape is not None:
        ML_MAPE.labels(model_type=model_type).set(mape)
    if mae is not None:
        ML_MAE.labels(model_type=model_type).set(mae)


def record_cache_hit(cache_type: str = "redis") -> None:
    """Record a cache hit."""
    CACHE_HITS_TOTAL.labels(cache_type=cache_type).inc()


def record_cache_miss(cache_type: str = "redis") -> None:
    """Record a cache miss."""
    CACHE_MISSES_TOTAL.labels(cache_type=cache_type).inc()


def set_websocket_connections(count: int) -> None:
    """Set active WebSocket connection count."""
    WEBSOCKET_CONNECTIONS_ACTIVE.set(count)


def record_websocket_message(message_type: str) -> None:
    """Record a WebSocket message sent."""
    WEBSOCKET_MESSAGES_SENT.labels(message_type=message_type).inc()


def record_alert_created(alert_type: str, severity: str) -> None:
    """Record an alert creation."""
    ALERTS_CREATED_TOTAL.labels(alert_type=alert_type, severity=severity).inc()


def set_active_alerts(severity: str, count: int) -> None:
    """Set active alert count by severity."""
    ALERTS_ACTIVE.labels(severity=severity).set(count)


def record_data_ingestion(data_type: str, source: str, count: int = 1) -> None:
    """Record data ingestion."""
    DATA_POINTS_INGESTED.labels(data_type=data_type, source=source).inc(count)


def record_ingestion_error(data_type: str, error_type: str) -> None:
    """Record data ingestion error."""
    DATA_INGESTION_ERRORS.labels(data_type=data_type, error_type=error_type).inc()


# =============================================================================
# Metrics Endpoint Handler
# =============================================================================


async def metrics_endpoint() -> StarletteResponse:
    """Generate Prometheus metrics output."""
    return StarletteResponse(
        content=generate_latest(),
        media_type="text/plain; charset=utf-8",
    )


def init_metrics(app_name: str, app_version: str) -> None:
    """Initialize application info metrics."""
    APP_INFO.info(
        {
            "app_name": app_name,
            "app_version": app_version,
        }
    )
