"""FastAPI application with WebSocket endpoint for Abraxas."""

from __future__ import annotations

try:
    from fastapi import FastAPI, WebSocket
except ImportError:
    FastAPI = None  # type: ignore
    WebSocket = None  # type: ignore

from abraxas.api.ws import WebSocketPublisher
from abraxas.events.bus import EventBus

# Create FastAPI app if available
if FastAPI is not None:
    app = FastAPI(title="Abraxas API", version="1.0.0")
else:
    app = None  # type: ignore

# Global event bus and WebSocket publisher
bus = EventBus()
ws_pub = WebSocketPublisher()


if app is not None:

    @app.websocket("/ws")
    async def ws_endpoint(websocket: WebSocket) -> None:
        """
        WebSocket endpoint for real-time event streaming.

        Clients can connect to ws://host:port/ws to receive events.
        """
        await ws_pub.connect(websocket)

    @app.get("/healthz")
    async def healthz() -> dict:
        """Health check endpoint."""
        return {"status": "ok"}

    @app.get("/api/ws/connections")
    async def ws_connections() -> dict:
        """Get WebSocket connection count."""
        return {"count": ws_pub.connection_count()}


# Bridge: publish any bus events to websocket clients
# Example subscription patterns (to be wired in actual runtime):
# bus.subscribe("compression", lambda p: asyncio.create_task(ws_pub.broadcast({"type":"compression","payload":p})))
# bus.subscribe("oracle", lambda p: asyncio.create_task(ws_pub.broadcast({"type":"oracle","payload":p})))
