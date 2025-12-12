"""Unit tests for demo endpoints."""

import pytest

from app.api.v1.endpoints.demo import (
    get_demo_credentials,
    get_demo_scenarios,
    get_demo_status,
    get_demo_summary,
    reset_demo_alerts,
)


@pytest.mark.asyncio
async def test_get_demo_status():
    """Test demo status endpoint."""
    result = await get_demo_status()

    assert result["status"] == "ready"
    assert result["environment"] == "demo"
    assert "services" in result
    assert "data" in result


@pytest.mark.asyncio
async def test_get_demo_credentials():
    """Test demo credentials endpoint."""
    result = await get_demo_credentials()

    assert "users" in result
    assert len(result["users"]) == 4
    assert result["users"][0]["role"] == "Administrator"


@pytest.mark.asyncio
async def test_get_demo_scenarios():
    """Test demo scenarios endpoint."""
    result = await get_demo_scenarios()

    assert "scenarios" in result
    assert len(result["scenarios"]) == 5
    assert result["scenarios"][0]["name"] == "Solar Power Forecasting"


@pytest.mark.asyncio
async def test_get_demo_summary():
    """Test demo summary endpoint."""
    result = await get_demo_summary()

    assert result["title"] == "PEA RE Forecast Platform - Demo Briefing"
    assert result["version"] == "v1.1.0"
    assert "status" in result
    assert "credentials" in result
    assert "scenarios" in result
    assert "tor_compliance" in result


@pytest.mark.asyncio
async def test_reset_demo_alerts():
    """Test reset demo alerts endpoint."""
    result = await reset_demo_alerts()

    assert result["status"] == "success"
    assert "alerts_created" in result
    assert result["alerts_created"]["critical"] == 2
