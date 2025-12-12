"""
WebSocket Connection Manager.

Manages WebSocket connections for real-time data broadcasting to clients.
Supports multiple channels: solar, voltage, alerts.
"""

import asyncio
from datetime import datetime
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    """
    Manages WebSocket connections and message broadcasting.

    Supports channel-based subscriptions for:
    - solar: Real-time solar power forecasts
    - voltage: Real-time voltage monitoring
    - alerts: System alerts and notifications
    """

    # Maximum connections per TOR 7.1.7: ≥300,000 consumers
    MAX_CONNECTIONS = 10000

    def __init__(self):
        # All active connections
        self.active_connections: list[WebSocket] = []
        # Channel subscriptions: {channel: [websocket, ...]}
        self.channel_subscriptions: dict[str, list[WebSocket]] = {
            "solar": [],
            "voltage": [],
            "alerts": [],
            "all": [],  # Receives all updates
        }
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, channels: list[str] | None = None):
        """
        Accept a new WebSocket connection and subscribe to channels.

        Args:
            websocket: The WebSocket connection
            channels: List of channels to subscribe to (default: ["all"])

        Returns:
            bool: True if connected, False if at capacity
        """
        # Check connection limit before accepting (DoS protection)
        if len(self.active_connections) >= self.MAX_CONNECTIONS:
            await websocket.close(code=1013, reason="Server at capacity")
            return False

        await websocket.accept()

        async with self._lock:
            self.active_connections.append(websocket)

            # Subscribe to requested channels
            if channels is None:
                channels = ["all"]

            for channel in channels:
                if channel in self.channel_subscriptions:
                    self.channel_subscriptions[channel].append(websocket)

    async def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection from all channels."""
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)

            # Remove from all channel subscriptions
            for channel in self.channel_subscriptions:
                if websocket in self.channel_subscriptions[channel]:
                    self.channel_subscriptions[channel].remove(websocket)

    async def subscribe(self, websocket: WebSocket, channel: str):
        """Subscribe a connection to a specific channel."""
        async with self._lock:
            if (
                channel in self.channel_subscriptions
                and websocket not in self.channel_subscriptions[channel]
            ):
                self.channel_subscriptions[channel].append(websocket)
                return True
        return False

    async def unsubscribe(self, websocket: WebSocket, channel: str):
        """Unsubscribe a connection from a specific channel."""
        async with self._lock:
            if (
                channel in self.channel_subscriptions
                and websocket in self.channel_subscriptions[channel]
            ):
                self.channel_subscriptions[channel].remove(websocket)
                return True
        return False

    async def send_personal_message(
        self, message: dict[str, Any], websocket: WebSocket
    ):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_json(message)
        except Exception:
            await self.disconnect(websocket)

    async def broadcast(self, message: dict[str, Any], channel: str = "all"):
        """
        Broadcast a message to all subscribers of a channel.

        Args:
            message: The message to broadcast (will be JSON serialized)
            channel: The channel to broadcast to
        """
        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.now().isoformat()

        # Get subscribers for this channel and "all" channel
        async with self._lock:
            subscribers = set(self.channel_subscriptions.get(channel, []))
            subscribers.update(self.channel_subscriptions.get("all", []))

        # Send to all subscribers
        disconnected = []
        for websocket in subscribers:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(websocket)

        # Clean up disconnected clients
        for websocket in disconnected:
            await self.disconnect(websocket)

    async def broadcast_solar_update(
        self,
        station_id: str,
        power_kw: float,
        irradiance: float,
        temperature: float,
        prediction: float | None = None,
    ):
        """Broadcast a solar power update."""
        message = {
            "type": "solar_update",
            "channel": "solar",
            "data": {
                "station_id": station_id,
                "power_kw": power_kw,
                "irradiance": irradiance,
                "temperature": temperature,
                "prediction": prediction,
            },
        }
        await self.broadcast(message, "solar")

    async def broadcast_voltage_update(
        self,
        prosumer_id: str,
        phase: str,
        voltage: float,
        status: str,
        prediction: float | None = None,
    ):
        """Broadcast a voltage update."""
        message = {
            "type": "voltage_update",
            "channel": "voltage",
            "data": {
                "prosumer_id": prosumer_id,
                "phase": phase,
                "voltage": voltage,
                "status": status,
                "prediction": prediction,
            },
        }
        await self.broadcast(message, "voltage")

    async def broadcast_alert(
        self,
        alert_type: str,
        severity: str,
        message_text: str,
        target_id: str | None = None,
        value: float | None = None,
    ):
        """Broadcast an alert."""
        message = {
            "type": "alert",
            "channel": "alerts",
            "data": {
                "alert_type": alert_type,
                "severity": severity,
                "message": message_text,
                "target_id": target_id,
                "value": value,
            },
        }
        await self.broadcast(message, "alerts")

    @property
    def connection_count(self) -> int:
        """Get the total number of active connections."""
        return len(self.active_connections)

    def get_channel_stats(self) -> dict[str, int]:
        """Get subscription counts for all channels."""
        return {
            channel: len(subscribers)
            for channel, subscribers in self.channel_subscriptions.items()
        }


# Global connection manager instance
manager = ConnectionManager()
