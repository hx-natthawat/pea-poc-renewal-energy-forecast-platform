"""
API Version Endpoints.

Provides information about available API versions, deprecation status,
and migration guides.
"""

from typing import Any

from fastapi import APIRouter

from app.core.versioning import (
    CURRENT_VERSION,
    LATEST_VERSION,
    APIVersion,
    create_versioned_response,
    get_version_info,
)

router = APIRouter()


@router.get("")
async def get_api_versions() -> dict[str, Any]:
    """
    Get information about all available API versions.

    Returns a list of API versions with their status and any deprecation info.
    """
    versions = [get_version_info(v).model_dump() for v in APIVersion]

    return create_versioned_response(
        data={
            "versions": versions,
            "current_version": CURRENT_VERSION.value,
            "latest_version": LATEST_VERSION.value,
        },
        version=APIVersion.V2,
        metadata={
            "migration_guide_url": "/api/v2/docs#migration",
        },
    )


@router.get("/{version}")
async def get_version_details(version: str) -> dict[str, Any]:
    """
    Get detailed information about a specific API version.

    Args:
        version: API version (e.g., "v1", "v2")

    Returns:
        Version details including status, deprecation info, and available endpoints.
    """
    try:
        api_version = APIVersion.from_string(version)
    except ValueError:
        return create_versioned_response(
            data={
                "error": "invalid_version",
                "message": f"Unknown API version: {version}",
                "available_versions": [v.value for v in APIVersion],
            },
            version=APIVersion.V2,
        )

    version_info = get_version_info(api_version)

    # Get available endpoints for this version
    endpoints = _get_endpoints_for_version(api_version)

    return create_versioned_response(
        data={
            "version": version_info.model_dump(),
            "endpoints": endpoints,
            "documentation_url": f"/api/{api_version.value}/docs",
            "openapi_url": f"/api/{api_version.value}/openapi.json",
        },
        version=APIVersion.V2,
    )


def _get_endpoints_for_version(version: APIVersion) -> list[dict[str, Any]]:
    """Get list of endpoints available in a specific API version."""
    # Define endpoints per version
    v1_endpoints = [
        {"path": "/health", "methods": ["GET"], "description": "Health check"},
        {"path": "/forecast/solar", "methods": ["POST"], "description": "Solar power forecast"},
        {"path": "/forecast/voltage", "methods": ["POST"], "description": "Voltage prediction"},
        {"path": "/data/solar", "methods": ["POST"], "description": "Submit solar data"},
        {"path": "/data/voltage", "methods": ["POST"], "description": "Submit voltage data"},
        {"path": "/alerts", "methods": ["GET", "POST"], "description": "Alert management"},
        {"path": "/topology/prosumers", "methods": ["GET"], "description": "Network topology"},
        {"path": "/comparison/{model_type}", "methods": ["GET"], "description": "Forecast comparison"},
        {"path": "/history/{model_type}", "methods": ["GET"], "description": "Historical analysis"},
        {"path": "/dayahead/{model_type}", "methods": ["GET"], "description": "Day-ahead forecast"},
        {"path": "/monitoring/metrics", "methods": ["GET"], "description": "Model metrics"},
        {"path": "/retraining/drift/analyze", "methods": ["POST"], "description": "Drift analysis"},
        {"path": "/notifications/send", "methods": ["POST"], "description": "Send notification"},
        {"path": "/regions", "methods": ["GET", "POST"], "description": "Region management"},
        {"path": "/weather/tmd/current", "methods": ["GET"], "description": "Current weather"},
    ]

    v2_endpoints = [
        {"path": "/health", "methods": ["GET"], "description": "Enhanced health check"},
        {"path": "/health/live", "methods": ["GET"], "description": "Liveness probe"},
        {"path": "/health/ready", "methods": ["GET"], "description": "Readiness probe"},
        {"path": "/version", "methods": ["GET"], "description": "API version info"},
        # Future v2 endpoints
        {"path": "/forecast", "methods": ["POST"], "description": "Unified forecast endpoint (planned)"},
        {"path": "/batch/forecast", "methods": ["POST"], "description": "Batch predictions (planned)"},
    ]

    if version == APIVersion.V1:
        return v1_endpoints
    elif version == APIVersion.V2:
        return v2_endpoints
    return []


@router.get("/migration/v1-to-v2")
async def get_migration_guide() -> dict[str, Any]:
    """
    Get migration guide from v1 to v2.

    Provides detailed guidance on migrating from v1 to v2 API.
    """
    return create_versioned_response(
        data={
            "title": "Migration Guide: v1 to v2",
            "overview": "This guide helps you migrate from API v1 to v2.",
            "breaking_changes": [
                {
                    "change": "Response format",
                    "description": "All responses now include api_version and data wrapper",
                    "v1_example": '{"status": "success", "power_kw": 1500}',
                    "v2_example": '{"api_version": "v2", "data": {"status": "success", "power_kw": 1500}}',
                },
                {
                    "change": "Error responses",
                    "description": "Errors now include error codes and structured details",
                    "v1_example": '{"detail": "Not found"}',
                    "v2_example": '{"api_version": "v2", "error": {"code": "NOT_FOUND", "message": "Resource not found", "details": {}}}',
                },
            ],
            "new_features": [
                {
                    "feature": "Field selection",
                    "description": "Request only the fields you need with ?fields=id,name,value",
                },
                {
                    "feature": "Cursor pagination",
                    "description": "More efficient pagination with cursor-based navigation",
                },
                {
                    "feature": "Batch operations",
                    "description": "Submit multiple predictions in a single request",
                },
                {
                    "feature": "Enhanced health checks",
                    "description": "Detailed component health with liveness/readiness probes",
                },
            ],
            "timeline": {
                "v2_release": "Planned",
                "v1_deprecation": "TBD (6 months after v2 release)",
                "v1_sunset": "TBD (12 months after v2 release)",
            },
        },
        version=APIVersion.V2,
    )
