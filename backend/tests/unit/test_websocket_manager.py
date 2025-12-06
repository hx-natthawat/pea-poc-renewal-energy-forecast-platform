"""
Unit tests for WebSocket connection manager.

Tests the connection manager, channel subscriptions, and broadcasting.
"""

from unittest.mock import AsyncMock

import pytest

from app.api.v1.websocket.manager import ConnectionManager


class TestConnectionManager:
    """Test ConnectionManager class."""

    def test_init(self):
        """Test manager initialization."""
        manager = ConnectionManager()
        assert manager.active_connections == []
        assert "solar" in manager.channel_subscriptions
        assert "voltage" in manager.channel_subscriptions
        assert "alerts" in manager.channel_subscriptions
        assert "all" in manager.channel_subscriptions

    def test_connection_count_empty(self):
        """Test connection count when empty."""
        manager = ConnectionManager()
        assert manager.connection_count == 0

    def test_get_channel_stats_empty(self):
        """Test channel stats when empty."""
        manager = ConnectionManager()
        stats = manager.get_channel_stats()
        assert stats["solar"] == 0
        assert stats["voltage"] == 0
        assert stats["alerts"] == 0
        assert stats["all"] == 0

    @pytest.mark.asyncio
    async def test_connect_default_channel(self):
        """Test connecting with default channel."""
        manager = ConnectionManager()
        ws = AsyncMock()

        await manager.connect(ws, None)

        assert ws in manager.active_connections
        assert ws in manager.channel_subscriptions["all"]
        ws.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_specific_channels(self):
        """Test connecting with specific channels."""
        manager = ConnectionManager()
        ws = AsyncMock()

        await manager.connect(ws, ["solar", "voltage"])

        assert ws in manager.active_connections
        assert ws in manager.channel_subscriptions["solar"]
        assert ws in manager.channel_subscriptions["voltage"]
        assert ws not in manager.channel_subscriptions["alerts"]

    @pytest.mark.asyncio
    async def test_connect_invalid_channel(self):
        """Test connecting with invalid channel (ignored)."""
        manager = ConnectionManager()
        ws = AsyncMock()

        await manager.connect(ws, ["invalid_channel"])

        assert ws in manager.active_connections
        # Invalid channel is simply ignored

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnecting a client."""
        manager = ConnectionManager()
        ws = AsyncMock()

        await manager.connect(ws, ["solar", "all"])
        assert ws in manager.active_connections

        await manager.disconnect(ws)

        assert ws not in manager.active_connections
        assert ws not in manager.channel_subscriptions["solar"]
        assert ws not in manager.channel_subscriptions["all"]

    @pytest.mark.asyncio
    async def test_disconnect_not_connected(self):
        """Test disconnecting a client that wasn't connected."""
        manager = ConnectionManager()
        ws = AsyncMock()

        # Should not raise
        await manager.disconnect(ws)

    @pytest.mark.asyncio
    async def test_subscribe(self):
        """Test subscribing to a channel."""
        manager = ConnectionManager()
        ws = AsyncMock()
        await manager.connect(ws, ["all"])

        result = await manager.subscribe(ws, "solar")

        assert result is True
        assert ws in manager.channel_subscriptions["solar"]

    @pytest.mark.asyncio
    async def test_subscribe_already_subscribed(self):
        """Test subscribing when already subscribed."""
        manager = ConnectionManager()
        ws = AsyncMock()
        await manager.connect(ws, ["solar"])

        result = await manager.subscribe(ws, "solar")

        # Should not add duplicate, returns False when already subscribed
        assert result is False
        assert manager.channel_subscriptions["solar"].count(ws) == 1

    @pytest.mark.asyncio
    async def test_subscribe_invalid_channel(self):
        """Test subscribing to invalid channel."""
        manager = ConnectionManager()
        ws = AsyncMock()
        await manager.connect(ws, ["all"])

        result = await manager.subscribe(ws, "invalid")

        assert result is False

    @pytest.mark.asyncio
    async def test_unsubscribe(self):
        """Test unsubscribing from a channel."""
        manager = ConnectionManager()
        ws = AsyncMock()
        await manager.connect(ws, ["solar", "voltage"])

        result = await manager.unsubscribe(ws, "solar")

        assert result is True
        assert ws not in manager.channel_subscriptions["solar"]
        assert ws in manager.channel_subscriptions["voltage"]

    @pytest.mark.asyncio
    async def test_unsubscribe_not_subscribed(self):
        """Test unsubscribing when not subscribed."""
        manager = ConnectionManager()
        ws = AsyncMock()
        await manager.connect(ws, ["voltage"])

        result = await manager.unsubscribe(ws, "solar")

        assert result is False

    @pytest.mark.asyncio
    async def test_unsubscribe_invalid_channel(self):
        """Test unsubscribing from invalid channel."""
        manager = ConnectionManager()
        ws = AsyncMock()
        await manager.connect(ws, ["all"])

        result = await manager.unsubscribe(ws, "invalid")

        assert result is False

    @pytest.mark.asyncio
    async def test_send_personal_message(self):
        """Test sending a message to specific client."""
        manager = ConnectionManager()
        ws = AsyncMock()
        await manager.connect(ws, ["all"])

        message = {"type": "test", "data": "hello"}
        await manager.send_personal_message(message, ws)

        ws.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_send_personal_message_error_disconnects(self):
        """Test that send error triggers disconnect."""
        manager = ConnectionManager()
        ws = AsyncMock()
        ws.send_json.side_effect = Exception("Connection lost")
        await manager.connect(ws, ["all"])

        await manager.send_personal_message({"test": "data"}, ws)

        # Client should be disconnected
        assert ws not in manager.active_connections

    @pytest.mark.asyncio
    async def test_broadcast(self):
        """Test broadcasting to channel."""
        manager = ConnectionManager()
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        await manager.connect(ws1, ["solar"])
        await manager.connect(ws2, ["voltage"])

        await manager.broadcast({"type": "test"}, "solar")

        ws1.send_json.assert_called_once()
        ws2.send_json.assert_not_called()

    @pytest.mark.asyncio
    async def test_broadcast_adds_timestamp(self):
        """Test that broadcast adds timestamp if missing."""
        manager = ConnectionManager()
        ws = AsyncMock()
        await manager.connect(ws, ["solar"])

        await manager.broadcast({"type": "test"}, "solar")

        call_args = ws.send_json.call_args[0][0]
        assert "timestamp" in call_args

    @pytest.mark.asyncio
    async def test_broadcast_preserves_timestamp(self):
        """Test that broadcast preserves existing timestamp."""
        manager = ConnectionManager()
        ws = AsyncMock()
        await manager.connect(ws, ["solar"])

        await manager.broadcast(
            {"type": "test", "timestamp": "2025-01-01T00:00:00"}, "solar"
        )

        call_args = ws.send_json.call_args[0][0]
        assert call_args["timestamp"] == "2025-01-01T00:00:00"

    @pytest.mark.asyncio
    async def test_broadcast_includes_all_subscribers(self):
        """Test that 'all' channel subscribers receive broadcasts."""
        manager = ConnectionManager()
        ws_solar = AsyncMock()
        ws_all = AsyncMock()
        await manager.connect(ws_solar, ["solar"])
        await manager.connect(ws_all, ["all"])

        await manager.broadcast({"type": "test"}, "solar")

        ws_solar.send_json.assert_called_once()
        ws_all.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_handles_disconnected_clients(self):
        """Test that broadcast handles clients that disconnect during broadcast."""
        manager = ConnectionManager()
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        ws2.send_json.side_effect = Exception("Disconnected")
        await manager.connect(ws1, ["solar"])
        await manager.connect(ws2, ["solar"])

        await manager.broadcast({"type": "test"}, "solar")

        # ws2 should be disconnected
        assert ws2 not in manager.active_connections
        # ws1 should still be connected
        assert ws1 in manager.active_connections

    @pytest.mark.asyncio
    async def test_broadcast_solar_update(self):
        """Test broadcasting solar update."""
        manager = ConnectionManager()
        ws = AsyncMock()
        await manager.connect(ws, ["solar"])

        await manager.broadcast_solar_update(
            station_id="STATION_1",
            power_kw=1500.5,
            irradiance=850.0,
            temperature=35.2,
            prediction=1480.0,
        )

        ws.send_json.assert_called_once()
        call_args = ws.send_json.call_args[0][0]
        assert call_args["type"] == "solar_update"
        assert call_args["channel"] == "solar"
        assert call_args["data"]["station_id"] == "STATION_1"
        assert call_args["data"]["power_kw"] == 1500.5
        assert call_args["data"]["irradiance"] == 850.0
        assert call_args["data"]["temperature"] == 35.2
        assert call_args["data"]["prediction"] == 1480.0

    @pytest.mark.asyncio
    async def test_broadcast_solar_update_no_prediction(self):
        """Test broadcasting solar update without prediction."""
        manager = ConnectionManager()
        ws = AsyncMock()
        await manager.connect(ws, ["solar"])

        await manager.broadcast_solar_update(
            station_id="STATION_1",
            power_kw=1500.5,
            irradiance=850.0,
            temperature=35.2,
        )

        call_args = ws.send_json.call_args[0][0]
        assert call_args["data"]["prediction"] is None

    @pytest.mark.asyncio
    async def test_broadcast_voltage_update(self):
        """Test broadcasting voltage update."""
        manager = ConnectionManager()
        ws = AsyncMock()
        await manager.connect(ws, ["voltage"])

        await manager.broadcast_voltage_update(
            prosumer_id="prosumer1",
            phase="A",
            voltage=232.5,
            status="normal",
            prediction=231.0,
        )

        ws.send_json.assert_called_once()
        call_args = ws.send_json.call_args[0][0]
        assert call_args["type"] == "voltage_update"
        assert call_args["channel"] == "voltage"
        assert call_args["data"]["prosumer_id"] == "prosumer1"
        assert call_args["data"]["phase"] == "A"
        assert call_args["data"]["voltage"] == 232.5
        assert call_args["data"]["status"] == "normal"
        assert call_args["data"]["prediction"] == 231.0

    @pytest.mark.asyncio
    async def test_broadcast_voltage_update_no_prediction(self):
        """Test broadcasting voltage update without prediction."""
        manager = ConnectionManager()
        ws = AsyncMock()
        await manager.connect(ws, ["voltage"])

        await manager.broadcast_voltage_update(
            prosumer_id="prosumer1",
            phase="A",
            voltage=232.5,
            status="normal",
        )

        call_args = ws.send_json.call_args[0][0]
        assert call_args["data"]["prediction"] is None

    @pytest.mark.asyncio
    async def test_broadcast_alert(self):
        """Test broadcasting alert."""
        manager = ConnectionManager()
        ws = AsyncMock()
        await manager.connect(ws, ["alerts"])

        await manager.broadcast_alert(
            alert_type="voltage_violation",
            severity="warning",
            message_text="Voltage exceeded threshold",
            target_id="prosumer1",
            value=245.0,
        )

        ws.send_json.assert_called_once()
        call_args = ws.send_json.call_args[0][0]
        assert call_args["type"] == "alert"
        assert call_args["channel"] == "alerts"
        assert call_args["data"]["alert_type"] == "voltage_violation"
        assert call_args["data"]["severity"] == "warning"
        assert call_args["data"]["message"] == "Voltage exceeded threshold"
        assert call_args["data"]["target_id"] == "prosumer1"
        assert call_args["data"]["value"] == 245.0

    @pytest.mark.asyncio
    async def test_broadcast_alert_minimal(self):
        """Test broadcasting alert with minimal info."""
        manager = ConnectionManager()
        ws = AsyncMock()
        await manager.connect(ws, ["alerts"])

        await manager.broadcast_alert(
            alert_type="system",
            severity="info",
            message_text="System maintenance scheduled",
        )

        call_args = ws.send_json.call_args[0][0]
        assert call_args["data"]["target_id"] is None
        assert call_args["data"]["value"] is None

    @pytest.mark.asyncio
    async def test_multiple_connections(self):
        """Test managing multiple connections."""
        manager = ConnectionManager()
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        ws3 = AsyncMock()

        await manager.connect(ws1, ["solar"])
        await manager.connect(ws2, ["voltage"])
        await manager.connect(ws3, ["solar", "voltage"])

        assert manager.connection_count == 3
        stats = manager.get_channel_stats()
        assert stats["solar"] == 2
        assert stats["voltage"] == 2
