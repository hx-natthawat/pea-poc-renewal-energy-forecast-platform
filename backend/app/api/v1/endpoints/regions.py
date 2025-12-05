"""
Region API endpoints for multi-region support.

Provides region management, access control, and region-specific data.
Part of v1.1.0 Multi-Region Support feature (F003).
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.security import CurrentUser, get_current_user, require_roles
from app.models.domain.region import AccessLevel, Region, RegionType
from app.models.schemas.region import (
    RegionComparisonRequest,
    RegionCreate,
    RegionUpdate,
    UserRegionAccessCreate,
)
from app.services.region_service import RegionService, get_region_service

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Region CRUD Endpoints
# =============================================================================


@router.get("")
async def list_regions(
    region_type: str | None = Query(
        default=None,
        description="Filter by type: zone, region, district, station",
    ),
    parent_id: str | None = Query(
        default=None,
        description="Filter by parent region ID",
    ),
    include_inactive: bool = Query(default=False),
    current_user: CurrentUser = Depends(get_current_user),
    region_service: RegionService = Depends(get_region_service),
) -> dict[str, Any]:
    """
    List all regions.

    **Requires authentication**

    Optionally filter by type or parent region.
    """
    if region_type:
        try:
            rt = RegionType(region_type)
            regions = region_service.get_regions_by_type(rt)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid region type: {region_type}")
    elif parent_id:
        regions = region_service.get_child_regions(parent_id)
    else:
        regions = region_service.get_all_regions(include_inactive=include_inactive)

    return {
        "status": "success",
        "data": {
            "regions": [
                {
                    "id": r.id,
                    "name": r.name,
                    "name_th": r.name_th,
                    "region_type": r.region_type.value,
                    "parent_id": r.parent_id,
                    "latitude": r.latitude,
                    "longitude": r.longitude,
                    "power_plants_count": r.power_plants_count,
                    "prosumers_count": r.prosumers_count,
                    "is_active": r.is_active,
                }
                for r in regions
            ],
            "count": len(regions),
        },
    }


@router.get("/hierarchy")
async def get_region_hierarchy(
    current_user: CurrentUser = Depends(get_current_user),
    region_service: RegionService = Depends(get_region_service),
) -> dict[str, Any]:
    """
    Get the complete region hierarchy tree.

    **Requires authentication**

    Returns zones with nested regions, districts, and stations.
    """
    zones = region_service.get_regions_by_type(RegionType.ZONE)

    def build_tree(parent_id: str) -> list[dict]:
        children = region_service.get_child_regions(parent_id)
        return [
            {
                "id": c.id,
                "name": c.name,
                "name_th": c.name_th,
                "region_type": c.region_type.value,
                "children": build_tree(c.id),
            }
            for c in children
        ]

    hierarchy = [
        {
            "id": z.id,
            "name": z.name,
            "name_th": z.name_th,
            "region_type": z.region_type.value,
            "children": build_tree(z.id),
        }
        for z in zones
    ]

    return {
        "status": "success",
        "data": {
            "hierarchy": hierarchy,
        },
    }


@router.get("/{region_id}")
async def get_region(
    region_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    region_service: RegionService = Depends(get_region_service),
) -> dict[str, Any]:
    """
    Get a specific region by ID.

    **Requires authentication**
    """
    region = region_service.get_region(region_id)
    if not region:
        raise HTTPException(status_code=404, detail=f"Region {region_id} not found")

    return {
        "status": "success",
        "data": {
            "id": region.id,
            "name": region.name,
            "name_th": region.name_th,
            "region_type": region.region_type.value,
            "parent_id": region.parent_id,
            "latitude": region.latitude,
            "longitude": region.longitude,
            "timezone": region.timezone,
            "power_plants_count": region.power_plants_count,
            "prosumers_count": region.prosumers_count,
            "is_active": region.is_active,
            "created_at": region.created_at.isoformat() if region.created_at else None,
            "updated_at": region.updated_at.isoformat() if region.updated_at else None,
        },
    }


@router.post("")
async def create_region(
    request: RegionCreate,
    current_user: CurrentUser = Depends(require_roles(["admin"])),
    region_service: RegionService = Depends(get_region_service),
) -> dict[str, Any]:
    """
    Create a new region.

    **Requires roles:** admin
    """
    logger.info(f"Creating region {request.id} by {current_user.username}")

    try:
        region_type = RegionType(request.region_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid region type: {request.region_type}")

    region = Region(
        id=request.id,
        name=request.name,
        name_th=request.name_th,
        region_type=region_type,
        parent_id=request.parent_id,
        latitude=request.latitude,
        longitude=request.longitude,
        timezone=request.timezone,
    )

    try:
        created = region_service.create_region(region)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "status": "success",
        "data": {
            "id": created.id,
            "name": created.name,
            "message": "Region created successfully",
        },
    }


@router.put("/{region_id}")
async def update_region(
    region_id: str,
    request: RegionUpdate,
    current_user: CurrentUser = Depends(require_roles(["admin"])),
    region_service: RegionService = Depends(get_region_service),
) -> dict[str, Any]:
    """
    Update a region.

    **Requires roles:** admin
    """
    logger.info(f"Updating region {region_id} by {current_user.username}")

    updates = request.model_dump(exclude_unset=True)
    updated = region_service.update_region(region_id, updates)

    if not updated:
        raise HTTPException(status_code=404, detail=f"Region {region_id} not found")

    return {
        "status": "success",
        "data": {
            "id": updated.id,
            "name": updated.name,
            "message": "Region updated successfully",
        },
    }


@router.delete("/{region_id}")
async def delete_region(
    region_id: str,
    current_user: CurrentUser = Depends(require_roles(["admin"])),
    region_service: RegionService = Depends(get_region_service),
) -> dict[str, Any]:
    """
    Delete (deactivate) a region.

    **Requires roles:** admin

    Regions with child regions cannot be deleted.
    """
    logger.info(f"Deleting region {region_id} by {current_user.username}")

    try:
        deleted = region_service.delete_region(region_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not deleted:
        raise HTTPException(status_code=404, detail=f"Region {region_id} not found")

    return {
        "status": "success",
        "data": {
            "region_id": region_id,
            "message": "Region deleted successfully",
        },
    }


# =============================================================================
# Region Statistics & Dashboard
# =============================================================================


@router.get("/{region_id}/stats")
async def get_region_stats(
    region_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    region_service: RegionService = Depends(get_region_service),
) -> dict[str, Any]:
    """
    Get statistics for a region.

    **Requires authentication**

    Includes aggregated counts from child regions.
    """
    stats = region_service.get_region_stats(region_id)
    if not stats:
        raise HTTPException(status_code=404, detail=f"Region {region_id} not found")

    return {
        "status": "success",
        "data": stats,
    }


@router.get("/{region_id}/dashboard")
async def get_region_dashboard(
    region_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    region_service: RegionService = Depends(get_region_service),
) -> dict[str, Any]:
    """
    Get dashboard data for a region.

    **Requires authentication**

    Returns summary, hierarchy, and child regions.
    """
    dashboard = region_service.get_dashboard_data(region_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail=f"Region {region_id} not found")

    return {
        "status": "success",
        "data": dashboard,
    }


@router.post("/compare")
async def compare_regions(
    request: RegionComparisonRequest,
    current_user: CurrentUser = Depends(get_current_user),
    region_service: RegionService = Depends(get_region_service),
) -> dict[str, Any]:
    """
    Compare multiple regions by a metric.

    **Requires authentication**

    Supports metrics: power_plants_count, prosumers_count
    """
    comparison = region_service.compare_regions(
        region_ids=request.region_ids,
        metric=request.metric,
    )

    return {
        "status": "success",
        "data": {
            **comparison,
            "compared_at": datetime.now().isoformat(),
        },
    }


# =============================================================================
# Access Control Endpoints
# =============================================================================


@router.post("/{region_id}/access")
async def grant_region_access(
    region_id: str,
    request: UserRegionAccessCreate,
    current_user: CurrentUser = Depends(require_roles(["admin"])),
    region_service: RegionService = Depends(get_region_service),
) -> dict[str, Any]:
    """
    Grant a user access to a region.

    **Requires roles:** admin
    """
    logger.info(
        f"Granting {request.access_level} access to {request.user_id} "
        f"for region {region_id} by {current_user.username}"
    )

    try:
        access_level = AccessLevel(request.access_level)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid access level: {request.access_level}",
        )

    try:
        access = region_service.grant_access(
            user_id=request.user_id,
            region_id=region_id,
            access_level=access_level,
            granted_by=current_user.username,
            expires_at=request.expires_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "status": "success",
        "data": {
            "user_id": access.user_id,
            "region_id": access.region_id,
            "access_level": access.access_level.value,
            "granted_at": access.granted_at.isoformat(),
            "message": "Access granted successfully",
        },
    }


@router.delete("/{region_id}/access/{user_id}")
async def revoke_region_access(
    region_id: str,
    user_id: str,
    current_user: CurrentUser = Depends(require_roles(["admin"])),
    region_service: RegionService = Depends(get_region_service),
) -> dict[str, Any]:
    """
    Revoke a user's access to a region.

    **Requires roles:** admin
    """
    logger.info(
        f"Revoking access for {user_id} to region {region_id} "
        f"by {current_user.username}"
    )

    revoked = region_service.revoke_access(user_id, region_id)
    if not revoked:
        raise HTTPException(
            status_code=404,
            detail=f"No access found for user {user_id} to region {region_id}",
        )

    return {
        "status": "success",
        "data": {
            "user_id": user_id,
            "region_id": region_id,
            "message": "Access revoked successfully",
        },
    }


@router.get("/access/me")
async def get_my_regions(
    current_user: CurrentUser = Depends(get_current_user),
    region_service: RegionService = Depends(get_region_service),
) -> dict[str, Any]:
    """
    Get regions the current user has access to.

    **Requires authentication**
    """
    accesses = region_service.get_user_regions(current_user.user_id)

    return {
        "status": "success",
        "data": {
            "user_id": current_user.user_id,
            "regions": [
                {
                    "region_id": a.region_id,
                    "access_level": a.access_level.value,
                    "granted_at": a.granted_at.isoformat(),
                    "expires_at": a.expires_at.isoformat() if a.expires_at else None,
                }
                for a in accesses
            ],
            "count": len(accesses),
        },
    }


@router.get("/{region_id}/access/check")
async def check_region_access(
    region_id: str,
    access_level: str = Query(default="read"),
    current_user: CurrentUser = Depends(get_current_user),
    region_service: RegionService = Depends(get_region_service),
) -> dict[str, Any]:
    """
    Check if current user has access to a region.

    **Requires authentication**
    """
    try:
        required_level = AccessLevel(access_level)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid access level: {access_level}")

    has_access = region_service.check_access(
        user_id=current_user.user_id,
        region_id=region_id,
        required_level=required_level,
    )

    return {
        "status": "success",
        "data": {
            "region_id": region_id,
            "access_level": access_level,
            "has_access": has_access,
        },
    }
