"""
Unit tests for region API endpoints.

Tests region CRUD, hierarchy, stats, and access control.
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.core.security import CurrentUser
from app.models.domain.region import AccessLevel, Region, RegionType, UserRegionAccess


# Mock fixtures
@pytest.fixture
def mock_current_user():
    return CurrentUser(
        id="user-123",
        email="test@pea.co.th",
        username="testuser",
        name="Test User",
        roles=["admin"],
    )


@pytest.fixture
def sample_region():
    return Region(
        id="zone-north",
        name="North Zone",
        name_th="ภาคเหนือ",
        region_type=RegionType.ZONE,
        parent_id=None,
        latitude=18.7883,
        longitude=98.9853,
        timezone="Asia/Bangkok",
        power_plants_count=150,
        prosumers_count=45000,
        is_active=True,
        created_at=datetime(2025, 1, 1),
        updated_at=datetime(2025, 6, 1),
    )


@pytest.fixture
def sample_child_region():
    return Region(
        id="region-chiangmai",
        name="Chiang Mai Region",
        name_th="ภาคเชียงใหม่",
        region_type=RegionType.REGION,
        parent_id="zone-north",
        latitude=18.7883,
        longitude=98.9853,
        timezone="Asia/Bangkok",
        power_plants_count=50,
        prosumers_count=15000,
        is_active=True,
        created_at=datetime(2025, 1, 1),
        updated_at=datetime(2025, 6, 1),
    )


class TestRegionType:
    """Test RegionType enum."""

    def test_zone_type(self):
        assert RegionType.ZONE.value == "zone"

    def test_region_type(self):
        assert RegionType.REGION.value == "region"

    def test_district_type(self):
        assert RegionType.DISTRICT.value == "district"

    def test_station_type(self):
        assert RegionType.STATION.value == "station"

    def test_invalid_type(self):
        with pytest.raises(ValueError):
            RegionType("invalid")


class TestAccessLevel:
    """Test AccessLevel enum."""

    def test_read_level(self):
        assert AccessLevel.READ.value == "read"

    def test_write_level(self):
        assert AccessLevel.WRITE.value == "write"

    def test_admin_level(self):
        assert AccessLevel.ADMIN.value == "admin"


class TestRegionModel:
    """Test Region domain model."""

    def test_create_region(self, sample_region):
        assert sample_region.id == "zone-north"
        assert sample_region.name == "North Zone"
        assert sample_region.region_type == RegionType.ZONE

    def test_region_with_parent(self, sample_child_region):
        assert sample_child_region.parent_id == "zone-north"

    def test_region_defaults(self):
        region = Region(
            id="test",
            name="Test",
            name_th="ทดสอบ",
            region_type=RegionType.ZONE,
        )
        assert region.is_active is True
        assert region.power_plants_count == 0
        assert region.prosumers_count == 0


class TestUserRegionAccess:
    """Test UserRegionAccess model."""

    def test_create_access(self):
        access = UserRegionAccess(
            user_id="user-123",
            region_id="zone-north",
            access_level=AccessLevel.READ,
            granted_by="admin-user",
            granted_at=datetime(2025, 1, 1),
        )
        assert access.user_id == "user-123"
        assert access.region_id == "zone-north"
        assert access.access_level == AccessLevel.READ

    def test_access_with_expiry(self):
        access = UserRegionAccess(
            user_id="user-123",
            region_id="zone-north",
            access_level=AccessLevel.WRITE,
            granted_by="admin-user",
            granted_at=datetime(2025, 1, 1),
            expires_at=datetime(2025, 1, 1),
        )
        assert access.expires_at == datetime(2025, 1, 1)


class TestListRegions:
    """Test list_regions endpoint."""

    @pytest.mark.asyncio
    async def test_list_all_regions(self, sample_region):
        """Test listing all regions."""
        from app.api.v1.endpoints.regions import list_regions

        mock_service = MagicMock()
        mock_service.get_all_regions.return_value = [sample_region]

        result = await list_regions(
            region_type=None,
            parent_id=None,
            include_inactive=False,
            current_user=CurrentUser(id="user-1", roles=["admin"]),
            region_service=mock_service,
        )

        assert result["status"] == "success"
        assert len(result["data"]["regions"]) == 1
        assert result["data"]["regions"][0]["id"] == "zone-north"

    @pytest.mark.asyncio
    async def test_list_by_type(self, sample_region):
        """Test listing regions by type."""
        from app.api.v1.endpoints.regions import list_regions

        mock_service = MagicMock()
        mock_service.get_regions_by_type.return_value = [sample_region]

        result = await list_regions(
            region_type="zone",
            parent_id=None,
            include_inactive=False,
            current_user=CurrentUser(id="user-1", roles=["admin"]),
            region_service=mock_service,
        )

        assert result["status"] == "success"
        mock_service.get_regions_by_type.assert_called_once_with(RegionType.ZONE)

    @pytest.mark.asyncio
    async def test_list_by_parent(self, sample_child_region):
        """Test listing regions by parent."""
        from app.api.v1.endpoints.regions import list_regions

        mock_service = MagicMock()
        mock_service.get_child_regions.return_value = [sample_child_region]

        result = await list_regions(
            region_type=None,
            parent_id="zone-north",
            include_inactive=False,
            current_user=CurrentUser(id="user-1", roles=["admin"]),
            region_service=mock_service,
        )

        assert result["status"] == "success"
        mock_service.get_child_regions.assert_called_once_with("zone-north")

    @pytest.mark.asyncio
    async def test_list_invalid_type(self):
        """Test listing with invalid type."""
        from app.api.v1.endpoints.regions import list_regions

        mock_service = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await list_regions(
                region_type="invalid",
                parent_id=None,
                include_inactive=False,
                current_user=CurrentUser(id="user-1", roles=["admin"]),
                region_service=mock_service,
            )

        assert exc_info.value.status_code == 400


class TestGetRegion:
    """Test get_region endpoint."""

    @pytest.mark.asyncio
    async def test_get_region(self, sample_region):
        """Test getting a region by ID."""
        from app.api.v1.endpoints.regions import get_region

        mock_service = MagicMock()
        mock_service.get_region.return_value = sample_region

        result = await get_region(
            region_id="zone-north",
            current_user=CurrentUser(id="user-1", roles=["admin"]),
            region_service=mock_service,
        )

        assert result["status"] == "success"
        assert result["data"]["id"] == "zone-north"
        assert result["data"]["name"] == "North Zone"

    @pytest.mark.asyncio
    async def test_get_region_not_found(self):
        """Test getting non-existent region."""
        from app.api.v1.endpoints.regions import get_region

        mock_service = MagicMock()
        mock_service.get_region.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_region(
                region_id="non-existent",
                current_user=CurrentUser(id="user-1", roles=["admin"]),
                region_service=mock_service,
            )

        assert exc_info.value.status_code == 404


class TestGetRegionHierarchy:
    """Test get_region_hierarchy endpoint."""

    @pytest.mark.asyncio
    async def test_get_hierarchy(self, sample_region, sample_child_region):
        """Test getting region hierarchy."""
        from app.api.v1.endpoints.regions import get_region_hierarchy

        mock_service = MagicMock()
        mock_service.get_regions_by_type.return_value = [sample_region]
        mock_service.get_child_regions.side_effect = lambda parent_id: (
            [sample_child_region] if parent_id == "zone-north" else []
        )

        result = await get_region_hierarchy(
            current_user=CurrentUser(id="user-1", roles=["admin"]),
            region_service=mock_service,
        )

        assert result["status"] == "success"
        assert len(result["data"]["hierarchy"]) == 1
        assert result["data"]["hierarchy"][0]["id"] == "zone-north"


class TestGetRegionStats:
    """Test get_region_stats endpoint."""

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Test getting region stats."""
        from app.api.v1.endpoints.regions import get_region_stats

        mock_service = MagicMock()
        mock_service.get_region_stats.return_value = {
            "power_plants_count": 150,
            "prosumers_count": 45000,
        }

        result = await get_region_stats(
            region_id="zone-north",
            current_user=CurrentUser(id="user-1", roles=["admin"]),
            region_service=mock_service,
        )

        assert result["status"] == "success"
        assert result["data"]["power_plants_count"] == 150

    @pytest.mark.asyncio
    async def test_get_stats_not_found(self):
        """Test getting stats for non-existent region."""
        from app.api.v1.endpoints.regions import get_region_stats

        mock_service = MagicMock()
        mock_service.get_region_stats.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_region_stats(
                region_id="non-existent",
                current_user=CurrentUser(id="user-1", roles=["admin"]),
                region_service=mock_service,
            )

        assert exc_info.value.status_code == 404


class TestGetRegionDashboard:
    """Test get_region_dashboard endpoint."""

    @pytest.mark.asyncio
    async def test_get_dashboard(self):
        """Test getting region dashboard."""
        from app.api.v1.endpoints.regions import get_region_dashboard

        mock_service = MagicMock()
        mock_service.get_dashboard_data.return_value = {
            "region": {"id": "zone-north", "name": "North Zone"},
            "stats": {"power_plants_count": 150},
        }

        result = await get_region_dashboard(
            region_id="zone-north",
            current_user=CurrentUser(id="user-1", roles=["admin"]),
            region_service=mock_service,
        )

        assert result["status"] == "success"
        assert result["data"]["region"]["id"] == "zone-north"

    @pytest.mark.asyncio
    async def test_get_dashboard_not_found(self):
        """Test getting dashboard for non-existent region."""
        from app.api.v1.endpoints.regions import get_region_dashboard

        mock_service = MagicMock()
        mock_service.get_dashboard_data.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_region_dashboard(
                region_id="non-existent",
                current_user=CurrentUser(id="user-1", roles=["admin"]),
                region_service=mock_service,
            )

        assert exc_info.value.status_code == 404


class TestCompareRegions:
    """Test compare_regions endpoint."""

    @pytest.mark.asyncio
    async def test_compare_regions(self):
        """Test comparing regions."""
        from app.api.v1.endpoints.regions import compare_regions
        from app.models.schemas.region import RegionComparisonRequest

        mock_service = MagicMock()
        mock_service.compare_regions.return_value = {
            "metric": "power_plants_count",
            "regions": [
                {"id": "zone-north", "value": 150},
                {"id": "zone-south", "value": 120},
            ],
        }

        request = RegionComparisonRequest(
            region_ids=["zone-north", "zone-south"],
            metric="power_plants_count",
        )

        result = await compare_regions(
            request=request,
            current_user=CurrentUser(id="user-1", roles=["admin"]),
            region_service=mock_service,
        )

        assert result["status"] == "success"
        assert "compared_at" in result["data"]


class TestCreateRegion:
    """Test create_region endpoint."""

    @pytest.mark.asyncio
    async def test_create_region(self, sample_region):
        """Test creating a region."""
        from app.api.v1.endpoints.regions import create_region
        from app.models.schemas.region import RegionCreate

        mock_service = MagicMock()
        mock_service.create_region.return_value = sample_region

        request = RegionCreate(
            id="zone-north",
            name="North Zone",
            name_th="ภาคเหนือ",
            region_type="zone",
        )

        result = await create_region(
            request=request,
            current_user=CurrentUser(id="admin-1", username="admin", roles=["admin"]),
            region_service=mock_service,
        )

        assert result["status"] == "success"
        assert result["data"]["id"] == "zone-north"

    @pytest.mark.asyncio
    async def test_create_region_invalid_type(self):
        """Test creating region with invalid type."""
        from app.api.v1.endpoints.regions import create_region
        from app.models.schemas.region import RegionCreate

        mock_service = MagicMock()

        request = RegionCreate(
            id="zone-north",
            name="North Zone",
            name_th="ภาคเหนือ",
            region_type="invalid",
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_region(
                request=request,
                current_user=CurrentUser(
                    id="admin-1", username="admin", roles=["admin"]
                ),
                region_service=mock_service,
            )

        assert exc_info.value.status_code == 400


class TestUpdateRegion:
    """Test update_region endpoint."""

    @pytest.mark.asyncio
    async def test_update_region(self, sample_region):
        """Test updating a region."""
        from app.api.v1.endpoints.regions import update_region
        from app.models.schemas.region import RegionUpdate

        sample_region.name = "Updated North Zone"
        mock_service = MagicMock()
        mock_service.update_region.return_value = sample_region

        request = RegionUpdate(name="Updated North Zone")

        result = await update_region(
            region_id="zone-north",
            request=request,
            current_user=CurrentUser(id="admin-1", username="admin", roles=["admin"]),
            region_service=mock_service,
        )

        assert result["status"] == "success"
        assert result["data"]["name"] == "Updated North Zone"

    @pytest.mark.asyncio
    async def test_update_region_not_found(self):
        """Test updating non-existent region."""
        from app.api.v1.endpoints.regions import update_region
        from app.models.schemas.region import RegionUpdate

        mock_service = MagicMock()
        mock_service.update_region.return_value = None

        request = RegionUpdate(name="Updated Name")

        with pytest.raises(HTTPException) as exc_info:
            await update_region(
                region_id="non-existent",
                request=request,
                current_user=CurrentUser(
                    id="admin-1", username="admin", roles=["admin"]
                ),
                region_service=mock_service,
            )

        assert exc_info.value.status_code == 404


class TestDeleteRegion:
    """Test delete_region endpoint."""

    @pytest.mark.asyncio
    async def test_delete_region(self):
        """Test deleting a region."""
        from app.api.v1.endpoints.regions import delete_region

        mock_service = MagicMock()
        mock_service.delete_region.return_value = True

        result = await delete_region(
            region_id="zone-north",
            current_user=CurrentUser(id="admin-1", username="admin", roles=["admin"]),
            region_service=mock_service,
        )

        assert result["status"] == "success"
        assert result["data"]["region_id"] == "zone-north"

    @pytest.mark.asyncio
    async def test_delete_region_not_found(self):
        """Test deleting non-existent region."""
        from app.api.v1.endpoints.regions import delete_region

        mock_service = MagicMock()
        mock_service.delete_region.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            await delete_region(
                region_id="non-existent",
                current_user=CurrentUser(
                    id="admin-1", username="admin", roles=["admin"]
                ),
                region_service=mock_service,
            )

        assert exc_info.value.status_code == 404


class TestGrantRegionAccess:
    """Test grant_region_access endpoint."""

    @pytest.mark.asyncio
    async def test_grant_access(self):
        """Test granting access to a region."""
        from app.api.v1.endpoints.regions import grant_region_access
        from app.models.schemas.region import UserRegionAccessCreate

        access = UserRegionAccess(
            user_id="user-456",
            region_id="zone-north",
            access_level=AccessLevel.READ,
            granted_by="admin-user",
            granted_at=datetime(2025, 1, 1),
        )

        mock_service = MagicMock()
        mock_service.grant_access.return_value = access

        request = UserRegionAccessCreate(
            user_id="user-456",
            region_id="zone-north",
            access_level="read",
        )

        result = await grant_region_access(
            region_id="zone-north",
            request=request,
            current_user=CurrentUser(id="admin-1", username="admin", roles=["admin"]),
            region_service=mock_service,
        )

        assert result["status"] == "success"
        assert result["data"]["user_id"] == "user-456"

    @pytest.mark.asyncio
    async def test_grant_access_invalid_level(self):
        """Test granting access with invalid level."""
        from app.api.v1.endpoints.regions import grant_region_access
        from app.models.schemas.region import UserRegionAccessCreate

        mock_service = MagicMock()

        request = UserRegionAccessCreate(
            user_id="user-456",
            region_id="zone-north",
            access_level="invalid",
        )

        with pytest.raises(HTTPException) as exc_info:
            await grant_region_access(
                region_id="zone-north",
                request=request,
                current_user=CurrentUser(
                    id="admin-1", username="admin", roles=["admin"]
                ),
                region_service=mock_service,
            )

        assert exc_info.value.status_code == 400


class TestRevokeRegionAccess:
    """Test revoke_region_access endpoint."""

    @pytest.mark.asyncio
    async def test_revoke_access(self):
        """Test revoking access to a region."""
        from app.api.v1.endpoints.regions import revoke_region_access

        mock_service = MagicMock()
        mock_service.revoke_access.return_value = True

        result = await revoke_region_access(
            region_id="zone-north",
            user_id="user-456",
            current_user=CurrentUser(id="admin-1", username="admin", roles=["admin"]),
            region_service=mock_service,
        )

        assert result["status"] == "success"
        assert result["data"]["user_id"] == "user-456"

    @pytest.mark.asyncio
    async def test_revoke_access_not_found(self):
        """Test revoking non-existent access."""
        from app.api.v1.endpoints.regions import revoke_region_access

        mock_service = MagicMock()
        mock_service.revoke_access.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            await revoke_region_access(
                region_id="zone-north",
                user_id="user-456",
                current_user=CurrentUser(
                    id="admin-1", username="admin", roles=["admin"]
                ),
                region_service=mock_service,
            )

        assert exc_info.value.status_code == 404


class TestCheckRegionAccess:
    """Test check_region_access endpoint."""

    @pytest.mark.asyncio
    async def test_check_access(self):
        """Test checking access to a region."""
        from app.api.v1.endpoints.regions import check_region_access

        mock_service = MagicMock()
        mock_service.check_access.return_value = True

        result = await check_region_access(
            region_id="zone-north",
            access_level="read",
            current_user=CurrentUser(id="user-1", roles=["admin"]),
            region_service=mock_service,
        )

        assert result["status"] == "success"
        assert result["data"]["has_access"] is True

    @pytest.mark.asyncio
    async def test_check_access_invalid_level(self):
        """Test checking access with invalid level."""
        from app.api.v1.endpoints.regions import check_region_access

        mock_service = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await check_region_access(
                region_id="zone-north",
                access_level="invalid",
                current_user=CurrentUser(id="user-1", roles=["admin"]),
                region_service=mock_service,
            )

        assert exc_info.value.status_code == 400
