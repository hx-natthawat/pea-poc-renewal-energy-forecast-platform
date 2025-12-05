"""
API v2 Router - Next-generation API endpoints.

Improvements over v1:
- Consistent response format with metadata
- Field selection (GraphQL-style)
- Improved pagination with cursors
- Batch operations
- Better error codes
"""

from fastapi import APIRouter

from app.api.v2.endpoints import health, version

api_router = APIRouter()

# Health and version endpoints
api_router.include_router(
    health.router,
    tags=["health"],
)

api_router.include_router(
    version.router,
    prefix="/version",
    tags=["version"],
)

# Future endpoints will be added here as v2 development progresses
# from app.api.v2.endpoints import forecast, data, alerts, etc.
