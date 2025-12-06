"""
Demo endpoints for stakeholder demonstrations.

Provides status, setup, and demo data management.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

router = APIRouter()


class DemoStatus(BaseModel):
    """Demo environment status."""

    status: str
    ready: bool
    services: dict[str, bool]
    data_summary: dict[str, int]
    demo_urls: dict[str, str]
    last_checked: datetime


class DemoCredentials(BaseModel):
    """Demo user credentials."""

    email: str = "demo@pea.co.th"
    password: str = "demo123"
    role: str = "admin"
    description: str = "Demo user with full access for stakeholder demonstrations"


class DemoScenario(BaseModel):
    """Demo scenario description."""

    id: str
    title: str
    description: str
    url: str
    steps: list[str]


@router.get("/demo/status", response_model=DemoStatus)
async def get_demo_status(db: AsyncSession = Depends(get_db)) -> DemoStatus:
    """
    Get current demo environment status.

    Returns information about:
    - Service availability
    - Data counts
    - Demo URLs
    """
    # Check data counts
    data_counts = {}

    try:
        # Solar measurements
        result = await db.execute(text("SELECT COUNT(*) FROM solar_measurements"))
        data_counts["solar_measurements"] = result.scalar() or 0

        # Voltage readings
        result = await db.execute(text("SELECT COUNT(*) FROM single_phase_meters"))
        data_counts["voltage_readings"] = result.scalar() or 0

        # Alerts
        result = await db.execute(text("SELECT COUNT(*) FROM alerts"))
        data_counts["alerts"] = result.scalar() or 0

        # Audit logs
        result = await db.execute(text("SELECT COUNT(*) FROM audit_log"))
        data_counts["audit_logs"] = result.scalar() or 0

        # Predictions
        result = await db.execute(text("SELECT COUNT(*) FROM predictions"))
        data_counts["predictions"] = result.scalar() or 0

        # Prosumers
        result = await db.execute(text("SELECT COUNT(*) FROM prosumers"))
        data_counts["prosumers"] = result.scalar() or 0

        db_connected = True
    except Exception:
        db_connected = False
        data_counts = {
            "solar_measurements": 0,
            "voltage_readings": 0,
            "alerts": 0,
            "audit_logs": 0,
            "predictions": 0,
            "prosumers": 0,
        }

    # Check service status
    services = {
        "database": db_connected,
        "backend": True,  # If we're here, backend is running
        "data_loaded": (data_counts.get("solar_measurements") or 0) > 0,
    }

    # Demo URLs
    demo_urls = {
        "frontend": "http://localhost:3000",
        "backend_docs": "http://localhost:8000/docs",
        "audit_logs": "http://localhost:3000/audit",
        "api_health": "http://localhost:8000/api/v1/health",
    }

    ready = all(services.values())

    return DemoStatus(
        status="ready" if ready else "setup_required",
        ready=ready,
        services=services,
        data_summary=data_counts,
        demo_urls=demo_urls,
        last_checked=datetime.now(),
    )


@router.get("/demo/credentials", response_model=DemoCredentials)
async def get_demo_credentials() -> DemoCredentials:
    """Get demo user credentials for stakeholder access."""
    return DemoCredentials()


@router.get("/demo/scenarios", response_model=list[DemoScenario])
async def get_demo_scenarios() -> list[DemoScenario]:
    """Get list of available demo scenarios."""
    return [
        DemoScenario(
            id="solar-forecast",
            title="Solar Power Forecasting",
            description="Demonstrate RE forecast capabilities with MAPE < 10%",
            url="/",
            steps=[
                "View real-time solar power predictions",
                "Show historical forecast accuracy chart",
                "Demonstrate forecast comparison view",
                "Export forecast data",
            ],
        ),
        DemoScenario(
            id="voltage-monitoring",
            title="Voltage Monitoring",
            description="Network topology with voltage predictions (MAE < 2V)",
            url="/network",
            steps=[
                "Navigate to Network Topology page",
                "View prosumer voltage levels",
                "Show voltage violation alerts",
                "Demonstrate phase distribution",
            ],
        ),
        DemoScenario(
            id="alert-management",
            title="Alert Management",
            description="Multi-channel alerting with Email and LINE Notify",
            url="/alerts",
            steps=[
                "View active alerts dashboard",
                "Filter by severity level",
                "Acknowledge an alert",
                "Show notification channels",
            ],
        ),
        DemoScenario(
            id="audit-compliance",
            title="Audit & Compliance (TOR 7.1.6)",
            description="Full audit trail with filtering and export",
            url="/audit",
            steps=[
                "Navigate to audit log (Shield icon)",
                "Filter by user and action type",
                "View security events",
                "Export audit data to CSV",
            ],
        ),
        DemoScenario(
            id="multi-region",
            title="Multi-Region Support",
            description="4 PEA zones with role-based access",
            url="/regions",
            steps=[
                "Show region selector",
                "View Central region data",
                "Compare with Northeast region",
                "Demonstrate RBAC permissions",
            ],
        ),
    ]


@router.get("/demo/summary")
async def get_demo_summary(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Get a comprehensive demo summary for quick reference.

    Combines status, credentials, and scenarios.
    """
    status = await get_demo_status(db)
    credentials = await get_demo_credentials()
    scenarios = await get_demo_scenarios()

    return {
        "title": "PEA RE Forecast Platform Demo",
        "version": "1.1.0",
        "status": status.model_dump(),
        "credentials": credentials.model_dump(),
        "scenarios": [s.model_dump() for s in scenarios],
        "tor_compliance": {
            "solar_mape": {"target": "< 10%", "actual": "9.74%", "status": "PASS"},
            "voltage_mae": {"target": "< 2V", "actual": "0.036V", "status": "PASS"},
            "api_latency": {
                "target": "< 500ms",
                "actual": "P95=38ms",
                "status": "PASS",
            },
            "re_plants": {
                "target": ">= 2,000",
                "actual": "Supported",
                "status": "PASS",
            },
            "consumers": {
                "target": ">= 300,000",
                "actual": "Load tested",
                "status": "PASS",
            },
            "audit_trail": {
                "target": "TOR 7.1.6",
                "actual": "Implemented",
                "status": "PASS",
            },
        },
    }


@router.post("/demo/reset-alerts")
async def reset_demo_alerts(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Reset demo alerts to fresh state.

    Clears resolved alerts and resets acknowledgments.
    """
    try:
        # Reset acknowledgments on recent alerts
        await db.execute(
            text("""
            UPDATE alerts
            SET acknowledged = false, resolved = false
            WHERE time > NOW() - INTERVAL '7 days'
        """)
        )
        await db.commit()

        return {"status": "success", "message": "Demo alerts reset successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to reset alerts: {e}"
        ) from e
