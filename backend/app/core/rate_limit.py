"""
Rate Limiting Middleware for PEA RE Forecast Platform.

Provides:
- Token bucket rate limiting
- Redis-based distributed rate limiting (when available)
- Per-client IP or API key limiting
- Configurable limits per endpoint
"""

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    # Requests per minute
    requests_per_minute: int = 60
    # Requests per second (burst)
    requests_per_second: int = 10
    # Window size in seconds for sliding window
    window_size: int = 60
    # Whether to use Redis for distributed rate limiting
    use_redis: bool = False
    # Exempt paths from rate limiting
    exempt_paths: list = field(default_factory=lambda: ["/metrics", "/api/v1/health"])
    # Higher limits for authenticated users
    authenticated_multiplier: float = 2.0


class TokenBucket:
    """Token bucket rate limiter for a single client."""

    def __init__(self, rate: float, capacity: int):
        """
        Initialize token bucket.

        Args:
            rate: Tokens per second to add
            capacity: Maximum tokens in bucket
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()

    async def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from the bucket.

        Returns True if tokens were consumed, False if rate limited.
        """
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_update
            self.last_update = now

            # Add tokens based on elapsed time
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    @property
    def remaining(self) -> int:
        """Get remaining tokens."""
        return int(self.tokens)


class InMemoryRateLimiter:
    """In-memory rate limiter using token buckets."""

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.buckets: Dict[str, TokenBucket] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    async def start(self):
        """Start the cleanup task."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self):
        """Stop the cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

    async def _cleanup_loop(self):
        """Periodically clean up stale buckets."""
        while True:
            await asyncio.sleep(300)  # Clean every 5 minutes
            async with self._lock:
                # Remove buckets that are at full capacity (inactive)
                to_remove = [
                    key
                    for key, bucket in self.buckets.items()
                    if bucket.remaining >= bucket.capacity
                ]
                for key in to_remove:
                    del self.buckets[key]

    async def is_allowed(
        self, client_id: str, is_authenticated: bool = False
    ) -> tuple[bool, int, int]:
        """
        Check if request is allowed.

        Returns:
            Tuple of (allowed, remaining, reset_after)
        """
        async with self._lock:
            if client_id not in self.buckets:
                # Calculate rate based on config
                rate = self.config.requests_per_minute / 60.0
                capacity = self.config.requests_per_second

                if is_authenticated:
                    rate *= self.config.authenticated_multiplier
                    capacity = int(capacity * self.config.authenticated_multiplier)

                self.buckets[client_id] = TokenBucket(rate=rate, capacity=capacity)

            bucket = self.buckets[client_id]
            allowed = await bucket.consume()
            remaining = bucket.remaining
            reset_after = int(
                (bucket.capacity - remaining) / bucket.rate
            )  # Seconds until full

            return allowed, remaining, reset_after


class RedisRateLimiter:
    """Redis-based rate limiter for distributed systems."""

    def __init__(self, config: RateLimitConfig, redis_client):
        self.config = config
        self.redis = redis_client

    async def is_allowed(
        self, client_id: str, is_authenticated: bool = False
    ) -> tuple[bool, int, int]:
        """
        Check if request is allowed using Redis sliding window.

        Returns:
            Tuple of (allowed, remaining, reset_after)
        """
        now = int(time.time())
        window_start = now - self.config.window_size
        key = f"rate_limit:{client_id}"

        limit = self.config.requests_per_minute
        if is_authenticated:
            limit = int(limit * self.config.authenticated_multiplier)

        pipe = self.redis.pipeline()

        # Remove old entries outside the window
        pipe.zremrangebyscore(key, 0, window_start)
        # Count current entries in window
        pipe.zcard(key)
        # Add current request
        pipe.zadd(key, {f"{now}:{time.time_ns()}": now})
        # Set expiry on the key
        pipe.expire(key, self.config.window_size)

        results = await pipe.execute()
        current_count = results[1]

        remaining = max(0, limit - current_count - 1)
        reset_after = self.config.window_size

        if current_count >= limit:
            return False, 0, reset_after

        return True, remaining, reset_after


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware for FastAPI."""

    def __init__(self, app, config: Optional[RateLimitConfig] = None):
        super().__init__(app)
        self.config = config or RateLimitConfig()
        self.limiter = InMemoryRateLimiter(self.config)
        self._started = False

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Start limiter on first request
        if not self._started:
            await self.limiter.start()
            self._started = True

        # Skip rate limiting for exempt paths
        if any(request.url.path.startswith(path) for path in self.config.exempt_paths):
            return await call_next(request)

        # Get client identifier
        client_id = self._get_client_id(request)

        # Check if user is authenticated (from JWT token)
        is_authenticated = self._is_authenticated(request)

        # Check rate limit
        allowed, remaining, reset_after = await self.limiter.is_allowed(
            client_id, is_authenticated
        )

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Try again in {reset_after} seconds.",
                    "retry_after": reset_after,
                },
                headers={
                    "X-RateLimit-Limit": str(self.config.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_after),
                    "Retry-After": str(reset_after),
                },
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.config.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_after)

        return response

    def _get_client_id(self, request: Request) -> str:
        """Get client identifier from request."""
        # Check for API key first
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api_key:{api_key}"

        # Check for authenticated user
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # Use a hash of the token as identifier
            token = auth_header[7:]
            return f"token:{hash(token)}"

        # Fall back to client IP
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        return f"ip:{client_ip}"

    def _is_authenticated(self, request: Request) -> bool:
        """Check if request is authenticated."""
        auth_header = request.headers.get("Authorization")
        return bool(auth_header and auth_header.startswith("Bearer "))


# Rate limit decorator for specific endpoints
def rate_limit(requests_per_minute: int = 30, requests_per_second: int = 5):
    """
    Decorator to apply custom rate limits to specific endpoints.

    Usage:
        @router.get("/expensive-endpoint")
        @rate_limit(requests_per_minute=10, requests_per_second=2)
        async def expensive_endpoint():
            ...
    """

    def decorator(func: Callable) -> Callable:
        # Store rate limit config on the function
        func._rate_limit = {
            "requests_per_minute": requests_per_minute,
            "requests_per_second": requests_per_second,
        }
        return func

    return decorator


# Endpoint-specific rate limits
ENDPOINT_LIMITS = {
    "/api/v1/forecast/solar": {"requests_per_minute": 120, "requests_per_second": 20},
    "/api/v1/forecast/voltage": {"requests_per_minute": 120, "requests_per_second": 20},
    "/api/v1/data/ingest": {"requests_per_minute": 30, "requests_per_second": 5},
    "/api/v1/dayahead": {"requests_per_minute": 60, "requests_per_second": 10},
}
