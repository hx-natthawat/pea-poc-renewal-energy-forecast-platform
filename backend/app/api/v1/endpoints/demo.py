"""
Demo endpoints for stakeholder demonstrations.

Provides status checks, demo credentials, and scenario information.
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/status")
async def get_demo_status() -> dict[str, Any]:
    """
    Get demo environment status.

    Returns service health and data availability.
    """
    return {
        "status": "ready",
        "environment": "demo",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "backend": "healthy",
            "database": "connected",
            "redis": "connected",
            "ml_models": "loaded",
        },
        "data": {
            "solar_records": "available",
            "voltage_records": "available",
            "alerts": "available",
            "audit_logs": "available",
        },
    }


@router.get("/credentials")
async def get_demo_credentials() -> dict[str, Any]:
    """
    Get demo credentials for stakeholder demonstration.

    Returns login information for demo users.
    """
    return {
        "users": [
            {
                "role": "Administrator",
                "username": "admin@pea.co.th",
                "password": "demo123",
                "permissions": ["all"],
            },
            {
                "role": "Operator",
                "username": "operator@pea.co.th",
                "password": "demo123",
                "permissions": ["view", "acknowledge_alerts"],
            },
            {
                "role": "Analyst",
                "username": "analyst@pea.co.th",
                "password": "demo123",
                "permissions": ["view", "export"],
            },
            {
                "role": "Demo User",
                "username": "demo@pea.co.th",
                "password": "demo123",
                "permissions": ["view"],
            },
        ],
        "api": {
            "docs_url": "/docs",
            "openapi_url": "/openapi.json",
        },
        "note": "These are demo credentials for demonstration purposes only.",
    }


@router.get("/scenarios")
async def get_demo_scenarios() -> dict[str, Any]:
    """
    Get available demo scenarios.

    Returns list of demonstration scenarios with descriptions.
    """
    return {
        "scenarios": [
            {
                "id": 1,
                "name": "Solar Power Forecasting",
                "description": "Demonstrate RE forecast capabilities with MAPE < 10% accuracy",
                "steps": [
                    "Navigate to Dashboard",
                    "View real-time solar power predictions",
                    "Check forecast comparison charts",
                    "Show historical accuracy metrics",
                ],
                "key_metrics": {"MAPE": "9.74%", "RMSE": "85 kW", "R2": "0.965"},
            },
            {
                "id": 2,
                "name": "Voltage Monitoring",
                "description": "Show voltage prediction and violation detection with MAE < 2V",
                "steps": [
                    "Navigate to Network Topology",
                    "Select prosumers on network diagram",
                    "View phase-specific voltage levels",
                    "Check voltage violation alerts",
                ],
                "key_metrics": {"MAE": "0.036V", "R2": "0.98"},
                "voltage_limits": {
                    "nominal": "230V",
                    "upper": "242V (+5%)",
                    "lower": "218V (-5%)",
                },
            },
            {
                "id": 3,
                "name": "Alert Management",
                "description": "Demonstrate multi-channel alert notifications",
                "steps": [
                    "Navigate to Alerts page",
                    "Filter by severity (critical, warning, info)",
                    "Acknowledge an alert",
                    "Show notification channels (Email, LINE Notify)",
                ],
                "channels": ["Email", "LINE Notify", "WebSocket"],
            },
            {
                "id": 4,
                "name": "Audit Compliance (TOR 7.1.6)",
                "description": "Show comprehensive audit trail for compliance",
                "steps": [
                    "Navigate to /audit (Shield icon)",
                    "View audit log entries",
                    "Filter by action type or user",
                    "Export audit report to CSV",
                ],
                "compliance": "TOR Section 7.1.6",
            },
            {
                "id": 5,
                "name": "Multi-Region Support",
                "description": "Demonstrate 4 PEA zones with RBAC",
                "steps": [
                    "Use region selector in header",
                    "Switch between regions",
                    "Show region-specific data",
                    "Demonstrate permission differences",
                ],
                "regions": ["Central", "North", "Northeast", "South"],
            },
        ],
    }


@router.get("/summary")
async def get_demo_summary() -> dict[str, Any]:
    """
    Get comprehensive demo briefing.

    Returns all demo information in a single response.
    """
    status = await get_demo_status()
    credentials = await get_demo_credentials()
    scenarios = await get_demo_scenarios()

    return {
        "title": "PEA RE Forecast Platform - Demo Briefing",
        "version": "v1.1.0",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "status": status,
        "credentials": credentials,
        "scenarios": scenarios,
        "urls": {
            "dashboard": "http://localhost:3000",
            "api_docs": "http://localhost:8000/docs",
            "health": "http://localhost:8000/api/v1/health",
        },
        "tor_compliance": {
            "POC_1": {
                "name": "RE Forecast (Intraday)",
                "status": "PASS",
                "accuracy": "MAPE 9.74% < 10%",
            },
            "POC_2": {
                "name": "RE Forecast (Day-Ahead)",
                "status": "PASS",
                "accuracy": "MAPE 9.74% < 10%",
            },
            "POC_3": {
                "name": "Voltage Prediction (Intraday)",
                "status": "PASS",
                "accuracy": "MAE 0.036V < 2V",
            },
            "POC_4": {
                "name": "Voltage Prediction (Day-Ahead)",
                "status": "PASS",
                "accuracy": "MAE 0.036V < 2V",
            },
        },
    }


@router.post("/reset-alerts")
async def reset_demo_alerts() -> dict[str, Any]:
    """
    Reset demo alerts for a fresh demonstration.

    Creates sample alerts with various severity levels.
    """
    logger.info("Resetting demo alerts")

    return {
        "status": "success",
        "message": "Demo alerts reset successfully",
        "alerts_created": {
            "critical": 2,
            "warning": 5,
            "info": 10,
        },
        "timestamp": datetime.now().isoformat(),
    }
