"""FastAPI application with event bus and WebSocket support."""

from __future__ import annotations

from fastapi import FastAPI, WebSocket

from abraxas.api.routes import router as api_router
from abraxas.api.ws import WebSocketPublisher
from abraxas.api.ws_bridge import wire_bus_to_ws
from abraxas.events.bus import EventBus

# Create FastAPI app
app = FastAPI(
    title="Abraxas Oracle API",
    description="Deterministic oracle and lexicon API with real-time event streaming",
    version="1.0.0",
)

# Initialize event bus and WebSocket publisher
bus = EventBus()
ws_pub = WebSocketPublisher()

# Wire event bus to WebSocket publisher
wire_bus_to_ws(bus, ws_pub)

# Include API routes
app.include_router(api_router, prefix="/api")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time event streaming.

    Clients connect here to receive live updates for:
    - compression events
    - correlation events
    - oracle events
    - lexicon events
    - error events
    """
    await ws_pub.connect(websocket)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Abraxas Oracle API",
        "version": "1.0.0",
        "endpoints": {
            "lexicon_register": "POST /api/lexicons/register",
            "oracle_run": "POST /api/oracle/run",
            "oracle_get": "GET /api/oracle/{artifact_id}",
            "websocket": "WS /ws",
        },
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "websocket_connections": ws_pub.connection_count()}
