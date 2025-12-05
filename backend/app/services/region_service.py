"""
Region Service for multi-region data management.

Provides region CRUD operations, access control, and data isolation.
Part of v1.1.0 Multi-Region Support feature (F003).
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.models.domain.region import (
    PEA_REGIONS,
    AccessLevel,
    Region,
    RegionType,
    UserRegionAccess,
)

logger = logging.getLogger(__name__)


@dataclass
class RegionServiceConfig:
    """Configuration for region service."""

    enable_caching: bool = True
    cache_ttl_seconds: int = 300
    default_access_level: AccessLevel = AccessLevel.READ
    allow_cross_region_access: bool = False


class RegionService:
    """
    Service for managing regions and data isolation.

    Features:
    - Region CRUD operations
    - User access control
    - Region hierarchy navigation
    - Cross-region data aggregation
    - Region-filtered queries
    """

    def __init__(self, config: RegionServiceConfig | None = None):
        """Initialize region service."""
        self.config = config or RegionServiceConfig()

        # In-memory storage (replace with database in production)
        self._regions: dict[str, Region] = dict(PEA_REGIONS)
        self._user_access: dict[str, list[UserRegionAccess]] = {}
        self._region_stats: dict[str, dict] = {}

    # =========================================================================
    # Region CRUD Operations
    # =========================================================================

    def get_region(self, region_id: str) -> Region | None:
        """Get a region by ID."""
        return self._regions.get(region_id)

    def get_all_regions(self, include_inactive: bool = False) -> list[Region]:
        """Get all regions."""
        regions = list(self._regions.values())
        if not include_inactive:
            regions = [r for r in regions if r.is_active]
        return regions

    def get_regions_by_type(self, region_type: RegionType) -> list[Region]:
        """Get all regions of a specific type."""
        return [
            r for r in self._regions.values()
            if r.region_type == region_type and r.is_active
        ]

    def get_child_regions(self, parent_id: str) -> list[Region]:
        """Get all child regions of a parent."""
        return [
            r for r in self._regions.values()
            if r.parent_id == parent_id and r.is_active
        ]

    def get_region_hierarchy(self, region_id: str) -> list[Region]:
        """Get the full hierarchy path to a region."""
        hierarchy = []
        current = self.get_region(region_id)

        while current:
            hierarchy.insert(0, current)
            if current.parent_id:
                current = self.get_region(current.parent_id)
            else:
                break

        return hierarchy

    def create_region(self, region: Region) -> Region:
        """Create a new region."""
        if region.id in self._regions:
            raise ValueError(f"Region {region.id} already exists")

        # Validate parent exists if specified
        if region.parent_id and region.parent_id not in self._regions:
            raise ValueError(f"Parent region {region.parent_id} not found")

        self._regions[region.id] = region
        logger.info(f"Created region: {region.id}")
        return region

    def update_region(
        self,
        region_id: str,
        updates: dict[str, Any],
    ) -> Region | None:
        """Update a region."""
        region = self.get_region(region_id)
        if not region:
            return None

        # Apply updates
        for key, value in updates.items():
            if hasattr(region, key) and value is not None:
                setattr(region, key, value)

        region.updated_at = datetime.now()
        logger.info(f"Updated region: {region_id}")
        return region

    def delete_region(self, region_id: str) -> bool:
        """Soft delete a region (mark as inactive)."""
        region = self.get_region(region_id)
        if not region:
            return False

        # Check for child regions
        children = self.get_child_regions(region_id)
        if children:
            raise ValueError(
                f"Cannot delete region with {len(children)} child regions"
            )

        region.is_active = False
        region.updated_at = datetime.now()
        logger.info(f"Deleted region: {region_id}")
        return True

    # =========================================================================
    # Access Control
    # =========================================================================

    def grant_access(
        self,
        user_id: str,
        region_id: str,
        access_level: AccessLevel,
        granted_by: str | None = None,
        expires_at: datetime | None = None,
    ) -> UserRegionAccess:
        """Grant user access to a region."""
        region = self.get_region(region_id)
        if not region:
            raise ValueError(f"Region {region_id} not found")

        access = UserRegionAccess(
            user_id=user_id,
            region_id=region_id,
            access_level=access_level,
            granted_by=granted_by,
            expires_at=expires_at,
        )

        if user_id not in self._user_access:
            self._user_access[user_id] = []

        # Remove existing access for this region
        self._user_access[user_id] = [
            a for a in self._user_access[user_id]
            if a.region_id != region_id
        ]

        self._user_access[user_id].append(access)
        logger.info(f"Granted {access_level} access to {user_id} for region {region_id}")
        return access

    def revoke_access(self, user_id: str, region_id: str) -> bool:
        """Revoke user access to a region."""
        if user_id not in self._user_access:
            return False

        original_count = len(self._user_access[user_id])
        self._user_access[user_id] = [
            a for a in self._user_access[user_id]
            if a.region_id != region_id
        ]

        revoked = len(self._user_access[user_id]) < original_count
        if revoked:
            logger.info(f"Revoked access for {user_id} to region {region_id}")
        return revoked

    def get_user_regions(self, user_id: str) -> list[UserRegionAccess]:
        """Get all regions a user has access to."""
        accesses = self._user_access.get(user_id, [])
        # Filter out expired access
        return [a for a in accesses if not a.is_expired()]

    def check_access(
        self,
        user_id: str,
        region_id: str,
        required_level: AccessLevel = AccessLevel.READ,
    ) -> bool:
        """Check if user has required access level to a region."""
        accesses = self.get_user_regions(user_id)

        for access in accesses:
            if access.region_id == region_id:
                if required_level == AccessLevel.READ:
                    return access.can_read()
                elif required_level == AccessLevel.WRITE:
                    return access.can_write()
                elif required_level == AccessLevel.ADMIN:
                    return access.is_admin()

        return False

    def get_accessible_regions(
        self,
        user_id: str,
        required_level: AccessLevel = AccessLevel.READ,
    ) -> list[Region]:
        """Get all regions a user can access at the required level."""
        accesses = self.get_user_regions(user_id)
        accessible_region_ids = set()

        for access in accesses:
            if (required_level == AccessLevel.READ and access.can_read()) or (required_level == AccessLevel.WRITE and access.can_write()) or (required_level == AccessLevel.ADMIN and access.is_admin()):
                accessible_region_ids.add(access.region_id)

        return [
            r for r in self._regions.values()
            if r.id in accessible_region_ids and r.is_active
        ]

    # =========================================================================
    # Region Statistics
    # =========================================================================

    def get_region_stats(self, region_id: str) -> dict[str, Any]:
        """Get statistics for a region."""
        region = self.get_region(region_id)
        if not region:
            return {}

        # Include child region stats
        children = self.get_child_regions(region_id)
        child_power_plants = sum(c.power_plants_count for c in children)
        child_prosumers = sum(c.prosumers_count for c in children)

        return {
            "region_id": region.id,
            "region_name": region.name,
            "region_name_th": region.name_th,
            "region_type": region.region_type.value,
            "power_plants_count": region.power_plants_count + child_power_plants,
            "prosumers_count": region.prosumers_count + child_prosumers,
            "child_regions_count": len(children),
            "is_active": region.is_active,
        }

    def get_all_stats(self) -> list[dict[str, Any]]:
        """Get statistics for all active regions."""
        return [
            self.get_region_stats(r.id)
            for r in self._regions.values()
            if r.is_active
        ]

    def compare_regions(
        self,
        region_ids: list[str],
        metric: str = "power_plants_count",
    ) -> dict[str, Any]:
        """Compare multiple regions by a metric."""
        results = []

        for region_id in region_ids:
            stats = self.get_region_stats(region_id)
            if stats:
                results.append({
                    "region_id": region_id,
                    "region_name": stats.get("region_name"),
                    "value": stats.get(metric, 0),
                })

        # Sort by value descending
        results.sort(key=lambda x: x["value"], reverse=True)

        return {
            "metric": metric,
            "regions": results,
            "total": sum(r["value"] for r in results),
        }

    # =========================================================================
    # Dashboard Data
    # =========================================================================

    def get_dashboard_data(self, region_id: str) -> dict[str, Any]:
        """Get dashboard data for a specific region."""
        region = self.get_region(region_id)
        if not region:
            return {}

        stats = self.get_region_stats(region_id)
        children = self.get_child_regions(region_id)

        return {
            "region_id": region.id,
            "region_name": region.name,
            "region_name_th": region.name_th,
            "region_type": region.region_type.value,
            "summary": {
                "power_plants": stats.get("power_plants_count", 0),
                "prosumers": stats.get("prosumers_count", 0),
                "child_regions": len(children),
            },
            "hierarchy": [
                {"id": r.id, "name": r.name, "type": r.region_type.value}
                for r in self.get_region_hierarchy(region_id)
            ],
            "children": [
                {"id": c.id, "name": c.name, "type": c.region_type.value}
                for c in children
            ],
            "coordinates": {
                "latitude": region.latitude,
                "longitude": region.longitude,
            },
            "last_updated": datetime.now().isoformat(),
        }


# Singleton instance
_region_service: RegionService | None = None


def get_region_service() -> RegionService:
    """Get or create region service instance."""
    global _region_service
    if _region_service is None:
        _region_service = RegionService()
    return _region_service


def configure_region_service(config: RegionServiceConfig) -> RegionService:
    """Configure the region service with specific settings."""
    global _region_service
    _region_service = RegionService(config)
    return _region_service
