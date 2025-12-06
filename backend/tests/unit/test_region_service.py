"""
Unit tests for the region service.

Tests cover region CRUD, access control, and statistics.
"""

from datetime import datetime, timedelta

import pytest

from app.models.domain.region import (
    PEA_REGIONS,
    AccessLevel,
    Region,
    RegionType,
    UserRegionAccess,
    get_child_regions,
    get_region_by_id,
    get_region_hierarchy,
    get_regions_by_type,
)
from app.services.region_service import (
    RegionService,
    get_region_service,
)

# =============================================================================
# Region Domain Model Tests
# =============================================================================


class TestRegionDomainModel:
    """Tests for Region domain model."""

    def test_region_creation(self):
        """Test creating a region."""
        region = Region(
            id="test-region",
            name="Test Region",
            name_th="ภาคทดสอบ",
            region_type=RegionType.REGION,
        )
        assert region.id == "test-region"
        assert region.name == "Test Region"
        assert region.name_th == "ภาคทดสอบ"
        assert region.region_type == RegionType.REGION
        assert region.is_active is True

    def test_region_with_coordinates(self):
        """Test region with valid coordinates."""
        region = Region(
            id="test",
            name="Test",
            region_type=RegionType.STATION,
            latitude=13.7563,
            longitude=100.5018,
        )
        assert region.latitude == 13.7563
        assert region.longitude == 100.5018

    def test_region_invalid_latitude(self):
        """Test region with invalid latitude raises error."""
        with pytest.raises(ValueError, match="Latitude"):
            Region(
                id="test",
                name="Test",
                region_type=RegionType.REGION,
                latitude=100.0,  # Invalid
            )

    def test_region_invalid_longitude(self):
        """Test region with invalid longitude raises error."""
        with pytest.raises(ValueError, match="Longitude"):
            Region(
                id="test",
                name="Test",
                region_type=RegionType.REGION,
                longitude=200.0,  # Invalid
            )


class TestUserRegionAccess:
    """Tests for UserRegionAccess model."""

    def test_access_creation(self):
        """Test creating user region access."""
        access = UserRegionAccess(
            user_id="user1",
            region_id="central",
            access_level=AccessLevel.READ,
        )
        assert access.user_id == "user1"
        assert access.region_id == "central"
        assert access.access_level == AccessLevel.READ

    def test_access_can_read(self):
        """Test can_read for different access levels."""
        read_access = UserRegionAccess("u1", "r1", AccessLevel.READ)
        write_access = UserRegionAccess("u1", "r1", AccessLevel.WRITE)
        admin_access = UserRegionAccess("u1", "r1", AccessLevel.ADMIN)

        assert read_access.can_read() is True
        assert write_access.can_read() is True
        assert admin_access.can_read() is True

    def test_access_can_write(self):
        """Test can_write for different access levels."""
        read_access = UserRegionAccess("u1", "r1", AccessLevel.READ)
        write_access = UserRegionAccess("u1", "r1", AccessLevel.WRITE)
        admin_access = UserRegionAccess("u1", "r1", AccessLevel.ADMIN)

        assert read_access.can_write() is False
        assert write_access.can_write() is True
        assert admin_access.can_write() is True

    def test_access_is_admin(self):
        """Test is_admin for different access levels."""
        read_access = UserRegionAccess("u1", "r1", AccessLevel.READ)
        admin_access = UserRegionAccess("u1", "r1", AccessLevel.ADMIN)

        assert read_access.is_admin() is False
        assert admin_access.is_admin() is True

    def test_access_expiration(self):
        """Test access expiration check."""
        # Non-expired
        access1 = UserRegionAccess(
            "u1",
            "r1",
            AccessLevel.READ,
            expires_at=datetime.now() + timedelta(days=1),
        )
        assert access1.is_expired() is False

        # Expired
        access2 = UserRegionAccess(
            "u1",
            "r1",
            AccessLevel.READ,
            expires_at=datetime.now() - timedelta(days=1),
        )
        assert access2.is_expired() is True

        # No expiration
        access3 = UserRegionAccess("u1", "r1", AccessLevel.READ)
        assert access3.is_expired() is False


# =============================================================================
# PEA Regions Tests
# =============================================================================


class TestPEARegions:
    """Tests for pre-defined PEA regions."""

    def test_pea_regions_exist(self):
        """Test that PEA regions are defined."""
        assert len(PEA_REGIONS) > 0
        assert "zone1" in PEA_REGIONS
        assert "central" in PEA_REGIONS
        assert "poc_station" in PEA_REGIONS

    def test_get_region_by_id(self):
        """Test getting a region by ID."""
        region = get_region_by_id("central")
        assert region is not None
        assert region.name == "Central Thailand"

    def test_get_region_by_id_not_found(self):
        """Test getting non-existent region."""
        region = get_region_by_id("nonexistent")
        assert region is None

    def test_get_regions_by_type(self):
        """Test getting regions by type."""
        zones = get_regions_by_type(RegionType.ZONE)
        assert len(zones) == 3  # zone1, zone2, zone3

        regions = get_regions_by_type(RegionType.REGION)
        assert len(regions) == 6  # central, east, north, northeast, south, west

    def test_get_child_regions(self):
        """Test getting child regions."""
        children = get_child_regions("zone1")
        assert len(children) == 2  # central, east

    def test_get_region_hierarchy(self):
        """Test getting region hierarchy."""
        hierarchy = get_region_hierarchy("poc_station")
        assert len(hierarchy) == 3  # zone1 -> central -> poc_station
        assert hierarchy[0].id == "zone1"
        assert hierarchy[1].id == "central"
        assert hierarchy[2].id == "poc_station"


# =============================================================================
# Region Service Tests
# =============================================================================


class TestRegionService:
    """Tests for RegionService class."""

    def test_service_initialization(self):
        """Test region service initializes with default config."""
        service = RegionService()
        assert service.config is not None
        assert len(service._regions) > 0

    def test_get_region(self):
        """Test getting a region."""
        service = RegionService()
        region = service.get_region("central")
        assert region is not None
        assert region.name == "Central Thailand"

    def test_get_all_regions(self):
        """Test getting all regions."""
        service = RegionService()
        regions = service.get_all_regions()
        assert len(regions) > 0

    def test_get_regions_by_type(self):
        """Test getting regions by type."""
        service = RegionService()
        zones = service.get_regions_by_type(RegionType.ZONE)
        assert len(zones) == 3

    def test_get_child_regions(self):
        """Test getting child regions."""
        service = RegionService()
        children = service.get_child_regions("zone1")
        assert len(children) == 2

    def test_get_region_hierarchy(self):
        """Test getting region hierarchy."""
        service = RegionService()
        hierarchy = service.get_region_hierarchy("poc_station")
        assert len(hierarchy) == 3

    def test_create_region(self):
        """Test creating a new region."""
        service = RegionService()
        region = Region(
            id="new-district",
            name="New District",
            region_type=RegionType.DISTRICT,
            parent_id="central",
        )
        created = service.create_region(region)
        assert created.id == "new-district"
        assert service.get_region("new-district") is not None

    def test_create_region_duplicate(self):
        """Test creating duplicate region fails."""
        service = RegionService()
        region = Region(
            id="central",
            name="Duplicate",
            region_type=RegionType.REGION,
        )
        with pytest.raises(ValueError, match="already exists"):
            service.create_region(region)

    def test_create_region_invalid_parent(self):
        """Test creating region with invalid parent fails."""
        service = RegionService()
        region = Region(
            id="orphan",
            name="Orphan",
            region_type=RegionType.DISTRICT,
            parent_id="nonexistent",
        )
        with pytest.raises(ValueError, match="not found"):
            service.create_region(region)

    def test_update_region(self):
        """Test updating a region."""
        service = RegionService()
        updated = service.update_region("central", {"name_th": "ภาคกลางใหม่"})
        assert updated is not None
        assert updated.name_th == "ภาคกลางใหม่"

    def test_update_region_not_found(self):
        """Test updating non-existent region."""
        service = RegionService()
        updated = service.update_region("nonexistent", {"name": "New"})
        assert updated is None

    def test_delete_region(self):
        """Test deleting (deactivating) a region."""
        service = RegionService()
        # Create a region without children
        service.create_region(
            Region(
                id="deletable",
                name="Deletable",
                region_type=RegionType.STATION,
                parent_id="central",
            )
        )
        deleted = service.delete_region("deletable")
        assert deleted is True
        assert service.get_region("deletable").is_active is False

    def test_delete_region_with_children(self):
        """Test deleting region with children fails."""
        service = RegionService()
        with pytest.raises(ValueError, match="child regions"):
            service.delete_region("zone1")


# =============================================================================
# Access Control Tests
# =============================================================================


class TestRegionAccessControl:
    """Tests for region access control."""

    def test_grant_access(self):
        """Test granting access to a region."""
        service = RegionService()
        access = service.grant_access(
            user_id="user1",
            region_id="central",
            access_level=AccessLevel.READ,
            granted_by="admin",
        )
        assert access.user_id == "user1"
        assert access.region_id == "central"
        assert access.access_level == AccessLevel.READ

    def test_grant_access_invalid_region(self):
        """Test granting access to invalid region fails."""
        service = RegionService()
        with pytest.raises(ValueError, match="not found"):
            service.grant_access("user1", "nonexistent", AccessLevel.READ)

    def test_revoke_access(self):
        """Test revoking access."""
        service = RegionService()
        service.grant_access("user1", "central", AccessLevel.READ)
        revoked = service.revoke_access("user1", "central")
        assert revoked is True

    def test_revoke_access_not_found(self):
        """Test revoking non-existent access."""
        service = RegionService()
        revoked = service.revoke_access("user1", "central")
        assert revoked is False

    def test_get_user_regions(self):
        """Test getting user's accessible regions."""
        service = RegionService()
        service.grant_access("user1", "central", AccessLevel.READ)
        service.grant_access("user1", "east", AccessLevel.WRITE)
        accesses = service.get_user_regions("user1")
        assert len(accesses) == 2

    def test_check_access_read(self):
        """Test checking read access."""
        service = RegionService()
        service.grant_access("user1", "central", AccessLevel.READ)
        assert service.check_access("user1", "central", AccessLevel.READ) is True
        assert service.check_access("user1", "central", AccessLevel.WRITE) is False

    def test_check_access_write(self):
        """Test checking write access."""
        service = RegionService()
        service.grant_access("user1", "central", AccessLevel.WRITE)
        assert service.check_access("user1", "central", AccessLevel.READ) is True
        assert service.check_access("user1", "central", AccessLevel.WRITE) is True
        assert service.check_access("user1", "central", AccessLevel.ADMIN) is False

    def test_check_access_admin(self):
        """Test checking admin access."""
        service = RegionService()
        service.grant_access("user1", "central", AccessLevel.ADMIN)
        assert service.check_access("user1", "central", AccessLevel.READ) is True
        assert service.check_access("user1", "central", AccessLevel.WRITE) is True
        assert service.check_access("user1", "central", AccessLevel.ADMIN) is True

    def test_get_accessible_regions(self):
        """Test getting accessible regions for a user."""
        service = RegionService()
        service.grant_access("user1", "central", AccessLevel.WRITE)
        service.grant_access("user1", "east", AccessLevel.READ)

        read_regions = service.get_accessible_regions("user1", AccessLevel.READ)
        assert len(read_regions) == 2

        write_regions = service.get_accessible_regions("user1", AccessLevel.WRITE)
        assert len(write_regions) == 1
        assert write_regions[0].id == "central"


# =============================================================================
# Statistics Tests
# =============================================================================


class TestRegionStatistics:
    """Tests for region statistics."""

    def test_get_region_stats(self):
        """Test getting region statistics."""
        service = RegionService()
        stats = service.get_region_stats("poc_station")
        assert stats["region_id"] == "poc_station"
        assert stats["region_name"] == "POC Station"
        assert "power_plants_count" in stats
        assert "prosumers_count" in stats

    def test_get_region_stats_not_found(self):
        """Test getting stats for non-existent region."""
        service = RegionService()
        stats = service.get_region_stats("nonexistent")
        assert stats == {}

    def test_get_all_stats(self):
        """Test getting all region statistics."""
        service = RegionService()
        all_stats = service.get_all_stats()
        assert len(all_stats) > 0

    def test_compare_regions(self):
        """Test comparing regions."""
        service = RegionService()
        comparison = service.compare_regions(
            region_ids=["central", "east", "north"],
            metric="power_plants_count",
        )
        assert comparison["metric"] == "power_plants_count"
        assert len(comparison["regions"]) == 3
        assert "total" in comparison

    def test_get_dashboard_data(self):
        """Test getting dashboard data."""
        service = RegionService()
        dashboard = service.get_dashboard_data("poc_station")
        assert dashboard["region_id"] == "poc_station"
        assert "summary" in dashboard
        assert "hierarchy" in dashboard
        assert "coordinates" in dashboard

    def test_get_dashboard_data_not_found(self):
        """Test getting dashboard for non-existent region."""
        service = RegionService()
        dashboard = service.get_dashboard_data("nonexistent")
        assert dashboard == {}


# =============================================================================
# Singleton Tests
# =============================================================================


class TestSingletonInstances:
    """Tests for singleton pattern implementations."""

    def test_region_service_singleton(self):
        """Test region service singleton returns same instance."""
        service1 = get_region_service()
        service2 = get_region_service()
        assert service1 is service2
