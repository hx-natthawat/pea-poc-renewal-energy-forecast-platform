"""
API v2 Module.

This module contains the v2 API endpoints with improved features:
- Enhanced response schemas with better typing
- Improved error handling with error codes
- Batch operations support
- GraphQL-style field selection
- Pagination improvements
"""

from app.api.v2.router import api_router

__all__ = ["api_router"]
