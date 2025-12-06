"""
Security middleware for the PEA RE Forecast Platform.

Implements security headers per TOR 7.1.6 and OWASP best practices.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds security headers to all responses.

    Headers implemented:
    - Strict-Transport-Security (HSTS) - forces HTTPS in production
    - X-Frame-Options - prevents clickjacking
    - X-Content-Type-Options - prevents MIME sniffing
    - X-XSS-Protection - enables XSS filtering
    - Referrer-Policy - controls referrer information
    - Content-Security-Policy - restricts resource loading
    - Permissions-Policy - controls browser features
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and add security headers to response."""
        response = await call_next(request)

        # X-Frame-Options: Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # X-Content-Type-Options: Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # X-XSS-Protection: Enable XSS filtering (legacy, but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer-Policy: Control referrer information sent with requests
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions-Policy: Disable unnecessary browser features
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), "
            "camera=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(), "
            "payment=(), "
            "usb=()"
        )

        # HSTS: Force HTTPS in production (not in development)
        if settings.APP_ENV == "production":
            # max-age=31536000 = 1 year
            # includeSubDomains ensures all subdomains also use HTTPS
            # preload allows submission to browser preload lists
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        # Content-Security-Policy: Restrict resource loading
        # Note: This is a permissive policy suitable for an API
        # Frontend apps should have stricter CSP
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline'",  # For Swagger UI
            "style-src 'self' 'unsafe-inline'",  # For Swagger UI
            "img-src 'self' data: https:",
            "font-src 'self' data:",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]

        # In development, allow connections to localhost
        if settings.APP_ENV != "production":
            csp_directives[5] = "connect-src 'self' http://localhost:* ws://localhost:*"

        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # Cache-Control for API responses (no caching by default)
        # Individual endpoints can override this
        if "Cache-Control" not in response.headers:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"

        return response
