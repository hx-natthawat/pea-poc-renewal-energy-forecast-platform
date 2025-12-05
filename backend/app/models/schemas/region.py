"""
Region Pydantic schemas for API request/response validation.

Part of v1.1.0 Multi-Region Support feature (F003).
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RegionBase(BaseModel):
    """Base schema for region data."""

    name: str = Field(..., description="Region name in English")
    name_th: str | None = Field(default=None, description="Region name in Thai")
    region_type: str = Field(..., description="Type: zone, region, district, station")
    parent_id: str | None = Field(default=None, description="Parent region ID")
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    timezone: str = Field(default="Asia/Bangkok")


class RegionCreate(RegionBase):
    """Schema for creating a new region."""

    id: str = Field(..., description="Unique region identifier")


class RegionUpdate(BaseModel):
    """Schema for updating a region."""

    name: str | None = None
    name_th: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    is_active: bool | None = None


class RegionResponse(RegionBase):
    """Schema for region response."""

    id: str
    is_active: bool = True
    power_plants_count: int = 0
    prosumers_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class RegionWithChildren(RegionResponse):
    """Schema for region with its child regions."""

    children: list["RegionResponse"] = Field(default_factory=list)


class RegionHierarchy(BaseModel):
    """Schema for region hierarchy path."""

    path: list[RegionResponse]
    depth: int


class UserRegionAccessBase(BaseModel):
    """Base schema for user region access."""

    user_id: str
    region_id: str
    access_level: str = Field(..., description="Access level: read, write, admin")


class UserRegionAccessCreate(UserRegionAccessBase):
    """Schema for granting region access."""

    expires_at: datetime | None = None


class UserRegionAccessResponse(UserRegionAccessBase):
    """Schema for user region access response."""

    granted_by: str | None = None
    granted_at: datetime
    expires_at: datetime | None = None
    is_expired: bool = False

    model_config = {"from_attributes": True}


class RegionStatsResponse(BaseModel):
    """Schema for region statistics."""

    region_id: str
    region_name: str
    power_plants_count: int
    prosumers_count: int
    total_capacity_kw: float = 0.0
    active_alerts: int = 0
    avg_forecast_accuracy: float | None = None


class RegionComparisonRequest(BaseModel):
    """Schema for region comparison request."""

    region_ids: list[str] = Field(..., min_length=2, max_length=10)
    metric: str = Field(
        default="power_output",
        description="Metric to compare: power_output, forecast_accuracy, voltage_violations",
    )
    start_date: datetime | None = None
    end_date: datetime | None = None


class RegionComparisonResponse(BaseModel):
    """Schema for region comparison response."""

    metric: str
    regions: list[dict[str, Any]]
    comparison_period: dict[str, str]


class RegionDashboardResponse(BaseModel):
    """Schema for region-specific dashboard data."""

    region_id: str
    region_name: str
    region_name_th: str | None = None
    summary: dict[str, Any]
    power_plants: list[dict[str, Any]]
    recent_alerts: list[dict[str, Any]]
    forecast_accuracy: dict[str, float]
    last_updated: datetime
