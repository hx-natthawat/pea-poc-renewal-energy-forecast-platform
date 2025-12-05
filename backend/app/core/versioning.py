"""
API Versioning Support Module.

Provides version negotiation, deprecation notices, and migration utilities.
Supports both URL-based (/api/v1, /api/v2) and header-based versioning.
"""

import logging
from collections.abc import Callable
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class APIVersion(str, Enum):
    """Supported API versions."""

    V1 = "v1"
    V2 = "v2"

    @classmethod
    def from_string(cls, version: str) -> "APIVersion":
        """Parse version string to enum."""
        version = version.lower().strip()
        version = version if version.startswith("v") else f"v{version}"

        try:
            return cls(version)
        except ValueError:
            raise ValueError(f"Unsupported API version: {version}")

    @property
    def is_deprecated(self) -> bool:
        """Check if this version is deprecated."""
        return self in DEPRECATED_VERSIONS

    @property
    def deprecation_date(self) -> datetime | None:
        """Get deprecation date if deprecated."""
        return DEPRECATION_DATES.get(self)

    @property
    def sunset_date(self) -> datetime | None:
        """Get sunset (removal) date if deprecated."""
        return SUNSET_DATES.get(self)


# Version lifecycle configuration
CURRENT_VERSION = APIVersion.V1
LATEST_VERSION = APIVersion.V1  # Will be V2 when V2 is ready
DEPRECATED_VERSIONS: set[APIVersion] = set()  # No deprecated versions yet

# Deprecation and sunset dates (to be set when v2 launches)
DEPRECATION_DATES: dict[APIVersion, datetime] = {}
SUNSET_DATES: dict[APIVersion, datetime] = {}


class DeprecationInfo(BaseModel):
    """Deprecation information model."""

    deprecated: bool = False
    deprecation_date: str | None = None
    sunset_date: str | None = None
    message: str | None = None
    migration_guide_url: str | None = None


class VersionInfo(BaseModel):
    """API version information."""

    version: str
    status: str  # "current", "latest", "deprecated", "sunset"
    deprecation: DeprecationInfo | None = None


def get_version_info(version: APIVersion) -> VersionInfo:
    """Get detailed information about an API version."""
    if version.is_deprecated:
        status = "deprecated"
        deprecation = DeprecationInfo(
            deprecated=True,
            deprecation_date=version.deprecation_date.isoformat() if version.deprecation_date else None,
            sunset_date=version.sunset_date.isoformat() if version.sunset_date else None,
            message=f"API {version.value} is deprecated. Please migrate to {LATEST_VERSION.value}.",
            migration_guide_url=f"/api/{LATEST_VERSION.value}/docs#migration",
        )
    elif version == LATEST_VERSION:
        status = "latest"
        deprecation = None
    else:
        status = "current"
        deprecation = None

    return VersionInfo(
        version=version.value,
        status=status,
        deprecation=deprecation,
    )


def add_deprecation_headers(response: JSONResponse, version: APIVersion) -> JSONResponse:
    """Add deprecation headers to response if version is deprecated."""
    if version.is_deprecated:
        response.headers["Deprecation"] = "true"
        if version.deprecation_date:
            response.headers["Deprecation-Date"] = version.deprecation_date.isoformat()
        if version.sunset_date:
            response.headers["Sunset"] = version.sunset_date.strftime("%a, %d %b %Y %H:%M:%S GMT")
        response.headers["Link"] = f'</api/{LATEST_VERSION.value}/docs>; rel="successor-version"'

    # Always add API version header
    response.headers["X-API-Version"] = version.value
    return response


class VersionNegotiator:
    """Handles API version negotiation from requests."""

    ACCEPT_VERSION_HEADER = "Accept-Version"
    API_VERSION_HEADER = "X-API-Version"

    @classmethod
    def get_version_from_request(cls, request: Request) -> APIVersion | None:
        """
        Extract API version from request.

        Priority:
        1. URL path (e.g., /api/v1/...)
        2. Accept-Version header
        3. X-API-Version header
        4. Default to current version
        """
        # Check URL path
        path = request.url.path
        for version in APIVersion:
            if f"/api/{version.value}/" in path or path.startswith(f"/api/{version.value}"):
                return version

        # Check Accept-Version header
        accept_version = request.headers.get(cls.ACCEPT_VERSION_HEADER)
        if accept_version:
            try:
                return APIVersion.from_string(accept_version)
            except ValueError:
                pass

        # Check X-API-Version header
        api_version = request.headers.get(cls.API_VERSION_HEADER)
        if api_version:
            try:
                return APIVersion.from_string(api_version)
            except ValueError:
                pass

        return CURRENT_VERSION


def deprecated_endpoint(
    deprecated_in: str,
    removed_in: str | None = None,
    alternative: str | None = None,
    message: str | None = None,
) -> Callable:
    """
    Decorator to mark an endpoint as deprecated.

    Usage:
        @deprecated_endpoint(
            deprecated_in="v2",
            removed_in="v3",
            alternative="/api/v2/new-endpoint"
        )
        async def old_endpoint():
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)

            # Log deprecation warning
            logger.warning(
                f"Deprecated endpoint called: {func.__name__}. "
                f"Deprecated in {deprecated_in}"
                + (f", will be removed in {removed_in}" if removed_in else "")
            )

            return result

        # Add deprecation metadata (using setattr for pyrefly compatibility)
        setattr(wrapper, "__deprecated__", True)  # noqa: B010
        setattr(wrapper, "__deprecated_in__", deprecated_in)  # noqa: B010
        setattr(wrapper, "__removed_in__", removed_in)  # noqa: B010
        setattr(wrapper, "__alternative__", alternative)  # noqa: B010
        setattr(wrapper, "__deprecation_message__", message or f"This endpoint is deprecated since {deprecated_in}" + (f" and will be removed in {removed_in}" if removed_in else "") + (f". Use {alternative} instead." if alternative else "."))  # noqa: B010

        return wrapper

    return decorator


def version_specific(
    min_version: str | None = None,
    max_version: str | None = None,
) -> Callable:
    """
    Decorator to restrict endpoint to specific API versions.

    Usage:
        @version_specific(min_version="v2")
        async def v2_only_endpoint():
            ...

        @version_specific(max_version="v1")
        async def v1_only_endpoint():
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, request: Request | None = None, **kwargs):
            if request:
                current_version = VersionNegotiator.get_version_from_request(request)
                if current_version is None:
                    current_version = APIVersion.V1  # Default to V1

                if min_version:
                    min_ver = APIVersion.from_string(min_version)
                    if min_ver is not None and list(APIVersion).index(current_version) < list(APIVersion).index(min_ver):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"This endpoint requires API version {min_version} or higher",
                        )

                if max_version:
                    max_ver = APIVersion.from_string(max_version)
                    if max_ver is not None and list(APIVersion).index(current_version) > list(APIVersion).index(max_ver):
                        raise HTTPException(
                            status_code=status.HTTP_410_GONE,
                            detail=f"This endpoint is not available in API version {current_version.value}",
                        )

            return await func(*args, request=request, **kwargs)

        return wrapper

    return decorator


# Response wrapper for consistent versioned responses
class VersionedResponse(BaseModel):
    """Standard versioned API response."""

    api_version: str
    data: Any
    metadata: dict[str, Any] | None = None
    deprecation: DeprecationInfo | None = None


def create_versioned_response(
    data: Any,
    version: APIVersion,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a versioned response with appropriate metadata."""
    response = {
        "api_version": version.value,
        "data": data,
    }

    if metadata:
        response["metadata"] = metadata

    if version.is_deprecated:
        response["deprecation"] = DeprecationInfo(
            deprecated=True,
            deprecation_date=version.deprecation_date.isoformat() if version.deprecation_date else None,
            sunset_date=version.sunset_date.isoformat() if version.sunset_date else None,
            message=f"API {version.value} is deprecated. Please migrate to {LATEST_VERSION.value}.",
        ).model_dump()

    return response
