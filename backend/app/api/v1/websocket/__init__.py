"""
WebSocket module for real-time data updates.
"""

from app.api.v1.websocket.manager import ConnectionManager
from app.api.v1.websocket.realtime import router

__all__ = ["ConnectionManager", "router"]
