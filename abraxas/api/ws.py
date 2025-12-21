"""WebSocket publisher for real-time event broadcasting."""

from __future__ import annotations

import json
from typing import Any, List

try:
    from fastapi import WebSocket
except ImportError:
    WebSocket = None  # type: ignore


class WebSocketPublisher:
    """
    Manages WebSocket connections and broadcasts events.

    Requires:
    - fastapi package
    """

    def __init__(self) -> None:
        self._connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """
        Accept and manage a WebSocket connection.

        Args:
            websocket: FastAPI WebSocket instance
        """
        if WebSocket is None:
            raise RuntimeError("fastapi not installed")

        await websocket.accept()
        self._connections.append(websocket)

        try:
            # Keep connection alive and handle incoming messages
            while True:
                data = await websocket.receive_text()
                # Echo back or handle client messages if needed
                await websocket.send_text(f"Echo: {data}")
        except Exception:
            # Connection closed or error
            pass
        finally:
            if websocket in self._connections:
                self._connections.remove(websocket)

    async def broadcast(self, message: Any) -> None:
        """
        Broadcast message to all connected WebSocket clients.

        Args:
            message: Message to broadcast (will be JSON-serialized if dict/list)
        """
        if isinstance(message, (dict, list)):
            text = json.dumps(message)
        else:
            text = str(message)

        # Remove dead connections
        dead = []
        for ws in self._connections:
            try:
                await ws.send_text(text)
            except Exception:
                dead.append(ws)

        for ws in dead:
            self._connections.remove(ws)

    def connection_count(self) -> int:
        """Return number of active connections."""
        return len(self._connections)
