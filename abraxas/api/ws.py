"""WebSocket publisher for real-time event broadcasting."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List

from fastapi import WebSocket


class WebSocketPublisher:
    """
    WebSocket publisher for broadcasting events to connected clients.
    Manages connections and handles broadcast with error recovery.
    """

    def __init__(self) -> None:
        """Initialize with empty connections list."""
        self._connections: List[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        """
        Accept and manage a WebSocket connection.

        Args:
            websocket: WebSocket connection to manage
        """
        await websocket.accept()
        async with self._lock:
            self._connections.append(websocket)

        try:
            # Keep connection alive, waiting for client disconnect
            while True:
                # Receive to detect disconnects (we don't process incoming messages)
                try:
                    await websocket.receive_text()
                except Exception:
                    break
        finally:
            await self.disconnect(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove a WebSocket connection.

        Args:
            websocket: WebSocket to remove
        """
        async with self._lock:
            if websocket in self._connections:
                self._connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """
        Broadcast a message to all connected clients.

        Args:
            message: Message dictionary to broadcast as JSON
        """
        if not self._connections:
            return

        message_json = json.dumps(message)
        disconnected = []

        async with self._lock:
            for ws in self._connections:
                try:
                    await ws.send_text(message_json)
                except Exception:
                    disconnected.append(ws)

            # Clean up disconnected clients
            for ws in disconnected:
                if ws in self._connections:
                    self._connections.remove(ws)

    def connection_count(self) -> int:
        """Return the number of active connections."""
        return len(self._connections)
