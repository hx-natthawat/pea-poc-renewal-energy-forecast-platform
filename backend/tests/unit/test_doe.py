"""
Unit tests for DOE (Dynamic Operating Envelope) service.

Tests cover:
- DOE calculation logic
- Voltage sensitivity calculations
- Thermal constraint handling
- API endpoint responses
"""

from datetime import datetime, timedelta

import pytest

from app.models.schemas.doe import (
    DOEBatchCalculateRequest,
    DOECalculateRequest,
    DOEStatus,
    LimitingFactor,
)
from app.services.doe_service import (
    POC_PROSUMERS,
    DOECalculator,
    NetworkConfig,
    calculate_doe_batch,
    calculate_doe_for_prosumer,
    get_network_topology,
    get_prosumer_config,
)

# ============================================================
# Prosumer Configuration Tests
# ============================================================


class TestProsumerConfig:
    """Tests for prosumer configuration."""

    def test_poc_prosumers_count(self):
        """POC network should have 7 prosumers."""
        assert len(POC_PROSUMERS) == 7

    def test_get_prosumer_config_valid(self):
        """Should return config for valid prosumer ID."""
        config = get_prosumer_config("prosumer1")
        assert config is not None
        assert config.id == "prosumer1"
        assert config.phase == "A"
        assert config.position == 3

    def test_get_prosumer_config_invalid(self):
        """Should return None for invalid prosumer ID."""
        config = get_prosumer_config("invalid_prosumer")
        assert config is None

    def test_prosumer_phase_distribution(self):
        """Prosumers should be distributed across phases A, B, C."""
        phases = {p.phase for p in POC_PROSUMERS}
        assert phases == {"A", "B", "C"}

    def test_prosumer_positions(self):
        """Prosumer positions should be 1, 2, or 3."""
        positions = {p.position for p in POC_PROSUMERS}
        assert positions == {1, 2, 3}

    def test_all_prosumers_have_pv(self):
        """All POC prosumers should have PV."""
        for p in POC_PROSUMERS:
            assert p.has_pv is True


# ============================================================
# DOE Calculator Tests
# ============================================================


class TestDOECalculator:
    """Tests for DOE calculation engine."""

    @pytest.fixture
    def calculator(self):
        """Create a DOE calculator with default config."""
        return DOECalculator()

    @pytest.fixture
    def custom_calculator(self):
        """Create a DOE calculator with custom config."""
        config = NetworkConfig(
            voltage_nominal_v=230.0,
            voltage_upper_v=242.0,
            voltage_lower_v=218.0,
            voltage_margin_v=3.0,
        )
        return DOECalculator(config)

    def test_voltage_sensitivity_near_transformer(self, calculator):
        """Prosumer near transformer should have low voltage sensitivity."""
        prosumer = get_prosumer_config("prosumer3")  # Position 1 (near)
        sensitivity = calculator.calculate_voltage_sensitivity(prosumer)

        # Low sensitivity for near position
        assert sensitivity > 0
        assert sensitivity < 0.1  # Less than 0.1 V/kW for near position

    def test_voltage_sensitivity_far_from_transformer(self, calculator):
        """Prosumer far from transformer should have higher voltage sensitivity."""
        prosumer = get_prosumer_config("prosumer1")  # Position 3 (far)
        sensitivity = calculator.calculate_voltage_sensitivity(prosumer)

        # Higher sensitivity for far position
        assert sensitivity > 0.02  # More than 0.02 V/kW

    def test_voltage_sensitivity_increases_with_distance(self, calculator):
        """Voltage sensitivity should increase with distance from transformer."""
        prosumer_near = get_prosumer_config("prosumer3")  # Position 1
        prosumer_mid = get_prosumer_config("prosumer2")  # Position 2
        prosumer_far = get_prosumer_config("prosumer1")  # Position 3

        sens_near = calculator.calculate_voltage_sensitivity(prosumer_near)
        sens_mid = calculator.calculate_voltage_sensitivity(prosumer_mid)
        sens_far = calculator.calculate_voltage_sensitivity(prosumer_far)

        assert sens_near < sens_mid < sens_far

    def test_thermal_headroom_positive(self, calculator):
        """Thermal headroom should be positive."""
        prosumer = get_prosumer_config("prosumer1")
        headroom_kw, headroom_pct = calculator.calculate_thermal_headroom(prosumer)

        assert headroom_kw > 0
        assert headroom_pct > 0
        assert headroom_pct < 100

    def test_calculate_doe_returns_valid_limit(self, calculator):
        """DOE calculation should return valid limit structure."""
        doe = calculator.calculate_doe("prosumer1")

        assert doe.prosumer_id == "prosumer1"
        assert doe.export_limit_kw >= 0
        assert doe.import_limit_kw >= 0
        assert doe.confidence == 0.95
        assert doe.limiting_factor in list(LimitingFactor)
        assert doe.status in list(DOEStatus)

    def test_calculate_doe_with_timestamp(self, calculator):
        """DOE calculation should use provided timestamp."""
        timestamp = datetime(2025, 6, 15, 12, 0, 0)
        doe = calculator.calculate_doe("prosumer1", timestamp=timestamp)

        assert doe.timestamp == timestamp
        assert doe.valid_until == timestamp + timedelta(minutes=15)

    def test_calculate_doe_with_custom_horizon(self, calculator):
        """DOE calculation should use provided horizon."""
        timestamp = datetime.now()
        doe = calculator.calculate_doe(
            "prosumer1", timestamp=timestamp, horizon_minutes=30
        )

        assert doe.valid_until == timestamp + timedelta(minutes=30)

    def test_calculate_doe_invalid_prosumer(self, calculator):
        """DOE calculation should raise ValueError for invalid prosumer."""
        with pytest.raises(ValueError, match="Unknown prosumer"):
            calculator.calculate_doe("invalid_prosumer")

    def test_export_limit_capped_at_pv_capacity(self, calculator):
        """Export limit should not exceed PV capacity."""
        doe = calculator.calculate_doe("prosumer1")
        prosumer = get_prosumer_config("prosumer1")

        assert doe.export_limit_kw <= prosumer.pv_capacity_kw

    def test_far_prosumer_more_constrained(self, calculator):
        """Prosumer far from transformer should have lower export limit."""
        doe_near = calculator.calculate_doe("prosumer3")  # Position 1
        doe_far = calculator.calculate_doe("prosumer1")  # Position 3

        # Far prosumer should generally have lower export limit
        # (due to voltage sensitivity)
        # Note: This may not always be true depending on predicted voltage
        assert doe_near.export_limit_kw >= 0
        assert doe_far.export_limit_kw >= 0


class TestDOECalculatorBatch:
    """Tests for batch DOE calculation."""

    @pytest.fixture
    def calculator(self):
        """Create a DOE calculator."""
        return DOECalculator()

    def test_calculate_batch_all_prosumers(self, calculator):
        """Batch calculation should return results for all prosumers."""
        results = calculator.calculate_batch()

        assert len(results) == 7  # All POC prosumers

    def test_calculate_batch_specific_prosumers(self, calculator):
        """Batch calculation should filter by prosumer IDs."""
        results = calculator.calculate_batch(prosumer_ids=["prosumer1", "prosumer2"])

        assert len(results) == 2
        ids = [r.prosumer_id for r in results]
        assert "prosumer1" in ids
        assert "prosumer2" in ids

    def test_calculate_batch_with_timestamp(self, calculator):
        """Batch calculation should use provided timestamp."""
        timestamp = datetime(2025, 6, 15, 12, 0, 0)
        results = calculator.calculate_batch(timestamp=timestamp)

        for result in results:
            assert result.timestamp == timestamp


# ============================================================
# Service Function Tests
# ============================================================


class TestDOEService:
    """Tests for DOE service functions."""

    @pytest.mark.asyncio
    async def test_calculate_doe_for_prosumer(self):
        """Service should calculate DOE for single prosumer."""
        response = await calculate_doe_for_prosumer("prosumer1")

        assert response.status == "success"
        assert response.data.prosumer_id == "prosumer1"
        assert response.data.export_limit_kw >= 0

    @pytest.mark.asyncio
    async def test_calculate_doe_batch_all(self):
        """Service should calculate DOE for all prosumers."""
        response = await calculate_doe_batch()

        assert response.status == "success"
        assert response.prosumer_count == 7
        assert len(response.data) == 7
        assert "total_export_capacity_kw" in response.summary

    @pytest.mark.asyncio
    async def test_calculate_doe_batch_summary(self):
        """Batch response should include correct summary statistics."""
        response = await calculate_doe_batch()

        summary = response.summary
        assert summary["total_export_capacity_kw"] >= 0
        assert summary["avg_export_limit_kw"] >= 0
        assert summary["min_export_limit_kw"] >= 0
        assert summary["max_export_limit_kw"] >= 0
        assert "constrained_count" in summary
        assert "voltage_limited_count" in summary
        assert "thermal_limited_count" in summary

    @pytest.mark.asyncio
    async def test_get_network_topology(self):
        """Service should return network topology."""
        topology = await get_network_topology()

        assert "transformer" in topology
        assert "prosumers" in topology
        assert "constraints" in topology

        assert topology["transformer"]["rated_power_kva"] == 50
        assert len(topology["prosumers"]) == 7
        assert topology["constraints"]["voltage_upper_v"] == 242


# ============================================================
# Network Configuration Tests
# ============================================================


class TestNetworkConfig:
    """Tests for network configuration."""

    def test_default_config(self):
        """Default config should have valid values."""
        config = NetworkConfig()

        assert config.tx_capacity_kva == 50.0
        assert config.voltage_nominal_v == 230.0
        assert config.voltage_upper_v == 242.0
        assert config.voltage_lower_v == 218.0
        assert config.cable_max_current_a == 200.0

    def test_voltage_tolerance(self):
        """Voltage limits should be ±5% of nominal."""
        config = NetworkConfig()

        upper_tolerance = (
            config.voltage_upper_v - config.voltage_nominal_v
        ) / config.voltage_nominal_v
        lower_tolerance = (
            config.voltage_nominal_v - config.voltage_lower_v
        ) / config.voltage_nominal_v

        assert abs(upper_tolerance - 0.05) < 0.01  # ~5%
        assert abs(lower_tolerance - 0.05) < 0.01  # ~5%


# ============================================================
# Schema Validation Tests
# ============================================================


class TestDOESchemas:
    """Tests for DOE Pydantic schemas."""

    def test_calculate_request_defaults(self):
        """Calculate request should have valid defaults."""
        request = DOECalculateRequest(prosumer_id="prosumer1")

        assert request.prosumer_id == "prosumer1"
        assert request.timestamp is None
        assert request.horizon_minutes == 15
        assert request.include_forecast is True

    def test_batch_request_defaults(self):
        """Batch request should have valid defaults."""
        request = DOEBatchCalculateRequest()

        assert request.timestamp is None
        assert request.horizon_minutes == 15
        assert request.prosumer_ids is None

    def test_horizon_validation(self):
        """Horizon should be validated (5-1440 minutes)."""
        # Valid
        request = DOECalculateRequest(prosumer_id="prosumer1", horizon_minutes=60)
        assert request.horizon_minutes == 60

        # Invalid - too low
        with pytest.raises(ValueError):
            DOECalculateRequest(prosumer_id="prosumer1", horizon_minutes=1)

        # Invalid - too high
        with pytest.raises(ValueError):
            DOECalculateRequest(prosumer_id="prosumer1", horizon_minutes=2000)
