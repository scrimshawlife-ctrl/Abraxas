"""Bridge between event bus and WebSocket for real-time updates."""

from __future__ import annotations

import asyncio
from typing import Any, Dict

from abraxas.api.ws import WebSocketPublisher
from abraxas.events.bus import EventBus


def wire_bus_to_ws(bus: EventBus, ws_pub: WebSocketPublisher) -> None:
    """
    Wire event bus to WebSocket publisher.

    Events published to the bus are forwarded to all WebSocket clients.
    Assumes FastAPI event loop is running; uses create_task for async dispatch.

    Args:
        bus: Event bus to subscribe to
        ws_pub: WebSocket publisher to broadcast events
    """

    def _mk_handler(event_type: str):
        """Create handler for specific event type."""

        def handler(payload: Dict[str, Any]) -> None:
            """Forward event to WebSocket clients."""
            try:
                # Create async task to broadcast (non-blocking)
                asyncio.create_task(ws_pub.broadcast({"type": event_type, "payload": payload}))
            except RuntimeError:
                # No event loop running (e.g., during testing)
                pass

        return handler

    # Subscribe to standard event types
    for event_type in ("compression", "correlation", "oracle", "lexicon", "error"):
        bus.subscribe(event_type, _mk_handler(event_type))
