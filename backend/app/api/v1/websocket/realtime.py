"""
Real-time WebSocket endpoints for PEA RE Forecast Platform.

Provides WebSocket connections for:
- Solar power real-time monitoring and forecasts
- Voltage level real-time monitoring
- Alert notifications
"""

import json
import logging
from datetime import datetime

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.api.v1.websocket.manager import manager
from app.ml import get_solar_inference, get_voltage_inference

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    channels: str = Query(
        default="all", description="Comma-separated channels: solar,voltage,alerts,all"
    ),
):
    """
    Main WebSocket endpoint for real-time data streaming.

    **Channels:**
    - `solar`: Solar power forecasts and measurements
    - `voltage`: Voltage monitoring data
    - `alerts`: System alerts and notifications
    - `all`: All updates (default)

    **Client Messages:**
    - `{"action": "subscribe", "channel": "solar"}`: Subscribe to a channel
    - `{"action": "unsubscribe", "channel": "voltage"}`: Unsubscribe from a channel
    - `{"action": "ping"}`: Keep-alive ping

    **Server Messages:**
    - `{"type": "solar_update", "data": {...}}`: Solar power update
    - `{"type": "voltage_update", "data": {...}}`: Voltage update
    - `{"type": "alert", "data": {...}}`: Alert notification
    - `{"type": "pong"}`: Ping response
    """
    # Parse channels from query parameter
    channel_list = [c.strip() for c in channels.split(",") if c.strip()]

    await manager.connect(websocket, channel_list)

    # Send connection confirmation
    await manager.send_personal_message(
        {
            "type": "connected",
            "message": "Connected to PEA RE Forecast Platform",
            "subscribed_channels": channel_list,
            "timestamp": datetime.now().isoformat(),
        },
        websocket,
    )

    try:
        while True:
            # Wait for client messages
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                action = message.get("action")

                if action == "subscribe":
                    channel = message.get("channel")
                    if channel:
                        success = await manager.subscribe(websocket, channel)
                        await manager.send_personal_message(
                            {
                                "type": "subscribed",
                                "channel": channel,
                                "success": success,
                            },
                            websocket,
                        )

                elif action == "unsubscribe":
                    channel = message.get("channel")
                    if channel:
                        success = await manager.unsubscribe(websocket, channel)
                        await manager.send_personal_message(
                            {
                                "type": "unsubscribed",
                                "channel": channel,
                                "success": success,
                            },
                            websocket,
                        )

                elif action == "ping":
                    await manager.send_personal_message(
                        {"type": "pong", "timestamp": datetime.now().isoformat()},
                        websocket,
                    )

                elif action == "get_status":
                    await manager.send_personal_message(
                        {
                            "type": "status",
                            "connections": manager.connection_count,
                            "channels": manager.get_channel_stats(),
                        },
                        websocket,
                    )

            except json.JSONDecodeError as e:
                logger.warning(f"WebSocket JSON decode error: {e}")
                await manager.send_personal_message(
                    {
                        "type": "error",
                        "message": "Invalid JSON",
                        "error_code": "INVALID_JSON",
                    },
                    websocket,
                )

    except WebSocketDisconnect:
        await manager.disconnect(websocket)


@router.websocket("/ws/solar")
async def solar_websocket(websocket: WebSocket):
    """
    Dedicated WebSocket for solar power monitoring.

    Automatically subscribes to the solar channel.
    """
    await manager.connect(websocket, ["solar"])

    await manager.send_personal_message(
        {
            "type": "connected",
            "channel": "solar",
            "message": "Connected to solar power monitoring",
            "timestamp": datetime.now().isoformat(),
        },
        websocket,
    )

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("action") == "ping":
                await manager.send_personal_message(
                    {"type": "pong", "timestamp": datetime.now().isoformat()},
                    websocket,
                )

            elif message.get("action") == "get_forecast":
                # Get a real-time forecast using current features
                features = message.get("features", {})
                if features:
                    inference = get_solar_inference()
                    result = inference.predict(
                        timestamp=datetime.now(),
                        pyrano1=features.get("pyrano1", 0),
                        pyrano2=features.get("pyrano2", 0),
                        pvtemp1=features.get("pvtemp1", 25),
                        pvtemp2=features.get("pvtemp2", 25),
                        ambtemp=features.get("ambtemp", 30),
                        windspeed=features.get("windspeed", 2),
                    )
                    await manager.send_personal_message(
                        {
                            "type": "forecast_result",
                            "data": result,
                            "timestamp": datetime.now().isoformat(),
                        },
                        websocket,
                    )

    except WebSocketDisconnect:
        await manager.disconnect(websocket)


@router.websocket("/ws/voltage")
async def voltage_websocket(websocket: WebSocket):
    """
    Dedicated WebSocket for voltage monitoring.

    Automatically subscribes to the voltage channel.
    """
    await manager.connect(websocket, ["voltage"])

    await manager.send_personal_message(
        {
            "type": "connected",
            "channel": "voltage",
            "message": "Connected to voltage monitoring",
            "timestamp": datetime.now().isoformat(),
        },
        websocket,
    )

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("action") == "ping":
                await manager.send_personal_message(
                    {"type": "pong", "timestamp": datetime.now().isoformat()},
                    websocket,
                )

            elif message.get("action") == "get_prediction":
                prosumer_id = message.get("prosumer_id")
                if prosumer_id:
                    inference = get_voltage_inference()
                    result = inference.predict(
                        timestamp=datetime.now(),
                        prosumer_id=prosumer_id,
                    )
                    await manager.send_personal_message(
                        {
                            "type": "prediction_result",
                            "data": result,
                            "timestamp": datetime.now().isoformat(),
                        },
                        websocket,
                    )

    except WebSocketDisconnect:
        await manager.disconnect(websocket)


@router.websocket("/ws/alerts")
async def alerts_websocket(websocket: WebSocket):
    """
    Dedicated WebSocket for alert notifications.

    Automatically subscribes to the alerts channel.
    """
    await manager.connect(websocket, ["alerts"])

    await manager.send_personal_message(
        {
            "type": "connected",
            "channel": "alerts",
            "message": "Connected to alert notifications",
            "timestamp": datetime.now().isoformat(),
        },
        websocket,
    )

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("action") == "ping":
                await manager.send_personal_message(
                    {"type": "pong", "timestamp": datetime.now().isoformat()},
                    websocket,
                )

    except WebSocketDisconnect:
        await manager.disconnect(websocket)


# Utility function for broadcasting from other parts of the application
async def broadcast_solar_data(
    station_id: str,
    power_kw: float,
    irradiance: float,
    temperature: float,
    prediction: float | None = None,
):
    """
    Broadcast solar data to all connected clients.

    Call this from data ingestion or scheduled tasks.
    """
    await manager.broadcast_solar_update(
        station_id=station_id,
        power_kw=power_kw,
        irradiance=irradiance,
        temperature=temperature,
        prediction=prediction,
    )


async def broadcast_voltage_data(
    prosumer_id: str,
    phase: str,
    voltage: float,
    status: str,
    prediction: float | None = None,
):
    """
    Broadcast voltage data to all connected clients.

    Call this from data ingestion or scheduled tasks.
    """
    await manager.broadcast_voltage_update(
        prosumer_id=prosumer_id,
        phase=phase,
        voltage=voltage,
        status=status,
        prediction=prediction,
    )


async def broadcast_alert_notification(
    alert_type: str,
    severity: str,
    message: str,
    target_id: str | None = None,
    value: float | None = None,
):
    """
    Broadcast an alert to all connected clients.

    Call this from alert service or monitoring tasks.
    """
    await manager.broadcast_alert(
        alert_type=alert_type,
        severity=severity,
        message_text=message,
        target_id=target_id,
        value=value,
    )
