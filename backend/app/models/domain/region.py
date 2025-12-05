"""
Region domain models for multi-region support.

Defines regions, zones, and user access control for data isolation.
Part of v1.1.0 Multi-Region Support feature (F003).
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class RegionType(str, Enum):
    """Types of regions in the hierarchy."""

    ZONE = "zone"
    REGION = "region"
    DISTRICT = "district"
    STATION = "station"


class AccessLevel(str, Enum):
    """Access levels for region permissions."""

    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


@dataclass
class Region:
    """
    Region entity representing a geographical area.

    Supports hierarchical structure:
    Zone > Region > District > Station
    """

    id: str
    name: str
    region_type: RegionType
    name_th: str | None = None
    parent_id: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    timezone: str = "Asia/Bangkok"
    is_active: bool = True
    power_plants_count: int = 0
    prosumers_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate region data."""
        if self.latitude is not None and not (-90 <= self.latitude <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        if self.longitude is not None and not (-180 <= self.longitude <= 180):
            raise ValueError("Longitude must be between -180 and 180")


@dataclass
class UserRegionAccess:
    """
    User access permission for a region.

    Controls what regions a user can view/modify.
    """

    user_id: str
    region_id: str
    access_level: AccessLevel
    granted_by: str | None = None
    granted_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime | None = None

    def is_expired(self) -> bool:
        """Check if access has expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    def can_read(self) -> bool:
        """Check if user has read access."""
        return self.access_level in [AccessLevel.READ, AccessLevel.WRITE, AccessLevel.ADMIN]

    def can_write(self) -> bool:
        """Check if user has write access."""
        return self.access_level in [AccessLevel.WRITE, AccessLevel.ADMIN]

    def is_admin(self) -> bool:
        """Check if user has admin access."""
        return self.access_level == AccessLevel.ADMIN


# PEA Region Hierarchy (as per TOR)
PEA_REGIONS = {
    "zone1": Region(
        id="zone1",
        name="Zone 1 - Central & East",
        name_th="ภาค 1 - กลาง และ ตะวันออก",
        region_type=RegionType.ZONE,
        latitude=13.7563,
        longitude=100.5018,
    ),
    "zone2": Region(
        id="zone2",
        name="Zone 2 - North & Northeast",
        name_th="ภาค 2 - เหนือ และ ตะวันออกเฉียงเหนือ",
        region_type=RegionType.ZONE,
        latitude=18.7883,
        longitude=98.9853,
    ),
    "zone3": Region(
        id="zone3",
        name="Zone 3 - South & West",
        name_th="ภาค 3 - ใต้ และ ตะวันตก",
        region_type=RegionType.ZONE,
        latitude=7.8804,
        longitude=98.3923,
    ),
    "central": Region(
        id="central",
        name="Central Thailand",
        name_th="ภาคกลาง",
        region_type=RegionType.REGION,
        parent_id="zone1",
        latitude=14.0208,
        longitude=100.5253,
    ),
    "east": Region(
        id="east",
        name="Eastern Thailand",
        name_th="ภาคตะวันออก",
        region_type=RegionType.REGION,
        parent_id="zone1",
        latitude=13.3611,
        longitude=100.9847,
    ),
    "north": Region(
        id="north",
        name="Northern Thailand",
        name_th="ภาคเหนือ",
        region_type=RegionType.REGION,
        parent_id="zone2",
        latitude=18.7883,
        longitude=98.9853,
    ),
    "northeast": Region(
        id="northeast",
        name="Northeastern Thailand",
        name_th="ภาคตะวันออกเฉียงเหนือ",
        region_type=RegionType.REGION,
        parent_id="zone2",
        latitude=15.2290,
        longitude=104.8561,
    ),
    "south": Region(
        id="south",
        name="Southern Thailand",
        name_th="ภาคใต้",
        region_type=RegionType.REGION,
        parent_id="zone3",
        latitude=7.8804,
        longitude=98.3923,
    ),
    "west": Region(
        id="west",
        name="Western Thailand",
        name_th="ภาคตะวันตก",
        region_type=RegionType.REGION,
        parent_id="zone3",
        latitude=14.0234,
        longitude=99.5328,
    ),
    # POC Station (from TOR)
    "poc_station": Region(
        id="poc_station",
        name="POC Station",
        name_th="สถานีทดสอบสาธิต",
        region_type=RegionType.STATION,
        parent_id="central",
        latitude=13.7563,
        longitude=100.5018,
        power_plants_count=1,
        prosumers_count=7,
    ),
}


def get_region_by_id(region_id: str) -> Region | None:
    """Get a region by its ID."""
    return PEA_REGIONS.get(region_id)


def get_regions_by_type(region_type: RegionType) -> list[Region]:
    """Get all regions of a specific type."""
    return [r for r in PEA_REGIONS.values() if r.region_type == region_type]


def get_child_regions(parent_id: str) -> list[Region]:
    """Get all child regions of a parent region."""
    return [r for r in PEA_REGIONS.values() if r.parent_id == parent_id]


def get_region_hierarchy(region_id: str) -> list[Region]:
    """Get the full hierarchy path from root to the specified region."""
    hierarchy = []
    current = get_region_by_id(region_id)

    while current:
        hierarchy.insert(0, current)
        if current.parent_id:
            current = get_region_by_id(current.parent_id)
        else:
            break

    return hierarchy
