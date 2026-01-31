"""Simple event bus for pub/sub messaging."""

from __future__ import annotations

from typing import Any, Callable, Dict, List


class EventBus:
    """
    Simple pub/sub event bus.
    Thread-safe for basic use cases; handlers execute synchronously.
    """

    def __init__(self) -> None:
        """Initialize event bus with empty handlers."""
        self._handlers: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}

    def subscribe(self, event_type: str, handler: Callable[[Dict[str, Any]], None]) -> None:
        """
        Subscribe to an event type.

        Args:
            event_type: Event type identifier
            handler: Callback function that receives event payload
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: Callable[[Dict[str, Any]], None]) -> None:
        """
        Unsubscribe from an event type.

        Args:
            event_type: Event type identifier
            handler: Handler to remove
        """
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
            except ValueError:
                pass  # Handler not found, ignore

    def publish(self, event_type: str, payload: Dict[str, Any]) -> None:
        """
        Publish an event to all subscribers.

        Args:
            event_type: Event type identifier
            payload: Event data
        """
        handlers = self._handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(payload)
            except Exception as e:
                # Log error but don't crash
                print(f"Error in event handler for {event_type}: {e}")

    def clear(self) -> None:
        """Clear all event handlers."""
        self._handlers.clear()
