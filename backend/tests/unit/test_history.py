"""
Unit tests for historical analysis API endpoints.

Tests the date range queries, aggregations, and export functionality.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.endpoints.history import (
    AggregationInterval,
    DataType,
    DateRangeStats,
    ExportFormat,
    HistoricalDataPoint,
    HistoricalResponse,
    get_time_bucket,
    router,
)
from app.core.security import CurrentUser

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def app():
    """Create a test FastAPI app with the history router."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/history")
    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Create a mock current user."""
    return CurrentUser(
        id="test-user-123",
        username="testuser",
        email="test@example.com",
        roles=["admin", "analyst"],
    )


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    session = AsyncMock()
    return session


# =============================================================================
# Test Enums
# =============================================================================


class TestDataType:
    """Test DataType enum."""

    def test_solar_type(self):
        assert DataType.solar.value == "solar"

    def test_voltage_type(self):
        assert DataType.voltage.value == "voltage"


class TestAggregationInterval:
    """Test AggregationInterval enum."""

    def test_raw_interval(self):
        assert AggregationInterval.raw.value == "raw"

    def test_5m_interval(self):
        assert AggregationInterval.minute_5.value == "5m"

    def test_15m_interval(self):
        assert AggregationInterval.minute_15.value == "15m"

    def test_1h_interval(self):
        assert AggregationInterval.hour.value == "1h"

    def test_1d_interval(self):
        assert AggregationInterval.day.value == "1d"


class TestExportFormat:
    """Test ExportFormat enum."""

    def test_json_format(self):
        assert ExportFormat.json.value == "json"

    def test_csv_format(self):
        assert ExportFormat.csv.value == "csv"


# =============================================================================
# Test Helper Functions
# =============================================================================


class TestGetTimeBucket:
    """Test get_time_bucket helper function."""

    def test_5m_bucket(self):
        result = get_time_bucket(AggregationInterval.minute_5)
        assert result == "5 minutes"

    def test_15m_bucket(self):
        result = get_time_bucket(AggregationInterval.minute_15)
        assert result == "15 minutes"

    def test_1h_bucket(self):
        result = get_time_bucket(AggregationInterval.hour)
        assert result == "1 hour"

    def test_1d_bucket(self):
        result = get_time_bucket(AggregationInterval.day)
        assert result == "1 day"

    def test_raw_bucket_returns_default(self):
        result = get_time_bucket(AggregationInterval.raw)
        assert result == "1 hour"


# =============================================================================
# Test Models
# =============================================================================


class TestDateRangeStats:
    """Test DateRangeStats model."""

    def test_create_with_all_fields(self):
        stats = DateRangeStats(
            count=100,
            avg=50.5,
            min=10.0,
            max=90.0,
            std=15.2,
        )
        assert stats.count == 100
        assert stats.avg == 50.5
        assert stats.min == 10.0
        assert stats.max == 90.0
        assert stats.std == 15.2

    def test_create_with_required_only(self):
        stats = DateRangeStats(count=50)
        assert stats.count == 50
        assert stats.avg is None
        assert stats.min is None
        assert stats.max is None
        assert stats.std is None


class TestHistoricalDataPoint:
    """Test HistoricalDataPoint model."""

    def test_create_with_all_fields(self):
        point = HistoricalDataPoint(
            time="2025-01-15T10:00:00",
            value=123.45,
            metadata={"source": "sensor1"},
        )
        assert point.time == "2025-01-15T10:00:00"
        assert point.value == 123.45
        assert point.metadata == {"source": "sensor1"}

    def test_create_with_required_only(self):
        point = HistoricalDataPoint(time="2025-01-15T10:00:00", value=50.0)
        assert point.time == "2025-01-15T10:00:00"
        assert point.value == 50.0
        assert point.metadata is None


class TestHistoricalResponse:
    """Test HistoricalResponse model."""

    def test_create_response(self):
        response = HistoricalResponse(
            status="success",
            data={"count": 10, "items": []},
        )
        assert response.status == "success"
        assert response.data == {"count": 10, "items": []}


# =============================================================================
# Test Solar History Endpoints
# =============================================================================


class TestGetSolarHistory:
    """Test get_solar_history endpoint."""

    @pytest.mark.asyncio
    async def test_solar_history_raw_data(self, mock_db, mock_user):
        """Test solar history with raw data interval."""
        from app.api.v1.endpoints.history import get_solar_history

        # Mock database response
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda _, i: [
            datetime(2025, 1, 15, 10, 0, 0),
            1500.0,
            800.0,
            795.0,
            45.0,
            44.5,
            32.0,
            2.5,
        ][i]

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row]
        mock_result.scalar.return_value = 100

        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch(
            "app.api.v1.endpoints.history.get_current_user", return_value=mock_user
        ):
            result = await get_solar_history(
                start_date=datetime(2025, 1, 1),
                end_date=datetime(2025, 1, 31),
                station_id="POC_STATION_1",
                interval=AggregationInterval.raw,
                limit=1000,
                offset=0,
                db=mock_db,
                current_user=mock_user,
            )

        assert result["status"] == "success"
        assert "data_points" in result["data"]
        assert result["data"]["station_id"] == "POC_STATION_1"

    @pytest.mark.asyncio
    async def test_solar_history_aggregated_data(self, mock_db, mock_user):
        """Test solar history with hourly aggregation."""
        from app.api.v1.endpoints.history import get_solar_history

        mock_row = MagicMock()
        mock_row.__getitem__ = lambda _, i: [
            datetime(2025, 1, 15, 10, 0, 0),
            1400.0,
            1200.0,
            1600.0,
            750.0,
            33.0,
            12,
        ][i]

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row]
        mock_result.scalar.return_value = 50

        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await get_solar_history(
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 31),
            station_id="POC_STATION_1",
            interval=AggregationInterval.hour,
            limit=1000,
            offset=0,
            db=mock_db,
            current_user=mock_user,
        )

        assert result["status"] == "success"
        assert result["data"]["interval"] == "1h"


class TestGetSolarSummary:
    """Test get_solar_summary endpoint."""

    @pytest.mark.asyncio
    async def test_solar_summary(self, mock_db, mock_user):
        """Test solar summary endpoint."""
        from app.api.v1.endpoints.history import get_solar_summary

        # Mock stats result
        stats_row = MagicMock()
        stats_row.__getitem__ = lambda _, i: [
            100,
            1500.0,
            0.0,
            3000.0,
            500.0,
            12000.0,
            750.0,
            32.0,
        ][i]

        # Mock hourly result
        hourly_row = MagicMock()
        hourly_row.__getitem__ = lambda _, i: [10.0, 1200.0, 20][i]

        # Mock daily result
        daily_row = MagicMock()
        daily_row.__getitem__ = lambda _, i: [
            datetime(2025, 1, 15).date(),
            1400.0,
            2800.0,
            8400.0,
        ][i]

        stats_result = MagicMock()
        stats_result.fetchone.return_value = stats_row

        hourly_result = MagicMock()
        hourly_result.fetchall.return_value = [hourly_row]

        daily_result = MagicMock()
        daily_result.fetchall.return_value = [daily_row]

        mock_db.execute = AsyncMock(
            side_effect=[stats_result, hourly_result, daily_result]
        )

        result = await get_solar_summary(
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 31),
            station_id="POC_STATION_1",
            db=mock_db,
            current_user=mock_user,
        )

        assert result["status"] == "success"
        assert "statistics" in result["data"]
        assert "hourly_distribution" in result["data"]
        assert "daily_aggregates" in result["data"]


# =============================================================================
# Test Voltage History Endpoints
# =============================================================================


class TestGetVoltageHistory:
    """Test get_voltage_history endpoint."""

    @pytest.mark.asyncio
    async def test_voltage_history_raw_data(self, mock_db, mock_user):
        """Test voltage history with raw data interval."""
        from app.api.v1.endpoints.history import get_voltage_history

        mock_row = MagicMock()
        mock_row.__getitem__ = lambda _, i: [
            datetime(2025, 1, 15, 10, 0, 0),
            "prosumer1",
            "A",
            230.5,
            2.5,
            0.5,
        ][i]

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row]
        mock_result.scalar.return_value = 100

        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await get_voltage_history(
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 31),
            prosumer_id="prosumer1",
            phase="A",
            interval=AggregationInterval.raw,
            limit=1000,
            offset=0,
            db=mock_db,
            current_user=mock_user,
        )

        assert result["status"] == "success"
        assert result["data"]["filters"]["prosumer_id"] == "prosumer1"
        assert result["data"]["filters"]["phase"] == "A"

    @pytest.mark.asyncio
    async def test_voltage_history_aggregated(self, mock_db, mock_user):
        """Test voltage history with hourly aggregation."""
        from app.api.v1.endpoints.history import get_voltage_history

        mock_row = MagicMock()
        mock_row.__getitem__ = lambda _, i: [
            datetime(2025, 1, 15, 10, 0, 0),
            "prosumer1",
            "A",
            230.0,
            228.0,
            232.0,
            2.3,
            12,
        ][i]

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row]
        mock_result.scalar.return_value = 50

        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await get_voltage_history(
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 31),
            prosumer_id=None,
            phase=None,
            interval=AggregationInterval.hour,
            limit=1000,
            offset=0,
            db=mock_db,
            current_user=mock_user,
        )

        assert result["status"] == "success"
        assert result["data"]["interval"] == "1h"


class TestGetVoltageSummary:
    """Test get_voltage_summary endpoint."""

    @pytest.mark.asyncio
    async def test_voltage_summary(self, mock_db, mock_user):
        """Test voltage summary endpoint."""
        from app.api.v1.endpoints.history import get_voltage_summary

        # Mock prosumer result
        prosumer_row = MagicMock()
        prosumer_row.__getitem__ = lambda _, i: [
            "prosumer1",
            "A",
            "Prosumer 1",
            100,
            230.0,
            225.0,
            235.0,
            2.5,
            2,
        ][i]

        # Mock phase result
        phase_row = MagicMock()
        phase_row.__getitem__ = lambda _, i: ["A", 300, 229.5, 220.0, 240.0, 5][i]

        # Mock overall result
        overall_row = MagicMock()
        overall_row.__getitem__ = lambda _, i: [1000, 230.0, 215.0, 245.0, 10][i]

        prosumer_result = MagicMock()
        prosumer_result.fetchall.return_value = [prosumer_row]

        phase_result = MagicMock()
        phase_result.fetchall.return_value = [phase_row]

        overall_result = MagicMock()
        overall_result.fetchone.return_value = overall_row

        mock_db.execute = AsyncMock(
            side_effect=[prosumer_result, phase_result, overall_result]
        )

        result = await get_voltage_summary(
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 31),
            db=mock_db,
            current_user=mock_user,
        )

        assert result["status"] == "success"
        assert "by_prosumer" in result["data"]
        assert "by_phase" in result["data"]
        assert "overall" in result["data"]


# =============================================================================
# Test Export Endpoints
# =============================================================================


class TestExportHistoricalData:
    """Test export_historical_data endpoint."""

    @pytest.mark.asyncio
    async def test_export_solar_csv(self, mock_db, mock_user):
        """Test export solar data as CSV."""
        from app.api.v1.endpoints.history import export_historical_data

        mock_row = MagicMock()
        mock_row.__getitem__ = lambda _, i: [
            datetime(2025, 1, 15, 10, 0, 0),
            "POC_STATION_1",
            1500.0,
            800.0,
            795.0,
            45.0,
            44.5,
            32.0,
            2.5,
        ][i]

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row]

        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await export_historical_data(
            data_type=DataType.solar,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 31),
            format=ExportFormat.csv,
            station_id="POC_STATION_1",
            prosumer_id=None,
            db=mock_db,
            current_user=mock_user,
        )

        assert result.media_type == "text/csv"
        assert "attachment" in result.headers["Content-Disposition"]

    @pytest.mark.asyncio
    async def test_export_solar_json(self, mock_db, mock_user):
        """Test export solar data as JSON."""
        from app.api.v1.endpoints.history import export_historical_data

        mock_row = MagicMock()
        mock_row.__getitem__ = lambda _, i: [
            datetime(2025, 1, 15, 10, 0, 0),
            "POC_STATION_1",
            1500.0,
            800.0,
            795.0,
            45.0,
            44.5,
            32.0,
            2.5,
        ][i]

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row]

        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await export_historical_data(
            data_type=DataType.solar,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 31),
            format=ExportFormat.json,
            station_id="POC_STATION_1",
            prosumer_id=None,
            db=mock_db,
            current_user=mock_user,
        )

        assert result.media_type == "application/json"

    @pytest.mark.asyncio
    async def test_export_voltage_csv(self, mock_db, mock_user):
        """Test export voltage data as CSV."""
        from app.api.v1.endpoints.history import export_historical_data

        mock_row = MagicMock()
        mock_row.__getitem__ = lambda _, i: [
            datetime(2025, 1, 15, 10, 0, 0),
            "prosumer1",
            230.5,
            2.5,
            0.5,
            10.5,
        ][i]

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row]

        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await export_historical_data(
            data_type=DataType.voltage,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 31),
            format=ExportFormat.csv,
            station_id="POC_STATION_1",
            prosumer_id="prosumer1",
            db=mock_db,
            current_user=mock_user,
        )

        assert result.media_type == "text/csv"
        assert "voltage_export" in result.headers["Content-Disposition"]
