"""Simple event bus for pub/sub within Abraxas."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Dict, List


class EventBus:
    """
    Simple synchronous event bus for internal pub/sub.

    Events are published by topic and delivered to all subscribers.
    """

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable[[Any], None]]] = defaultdict(list)

    def subscribe(self, topic: str, handler: Callable[[Any], None]) -> None:
        """
        Subscribe to a topic.

        Args:
            topic: Topic name
            handler: Callback function to receive payloads
        """
        self._subscribers[topic].append(handler)

    def publish(self, topic: str, payload: Any) -> None:
        """
        Publish payload to all subscribers of a topic.

        Args:
            topic: Topic name
            payload: Data to send to subscribers
        """
        for handler in self._subscribers[topic]:
            try:
                handler(payload)
            except Exception:
                # Swallow exceptions to prevent one subscriber from breaking others
                # In production, add logging here
                pass

    def unsubscribe(self, topic: str, handler: Callable[[Any], None]) -> None:
        """
        Unsubscribe a handler from a topic.

        Args:
            topic: Topic name
            handler: Handler to remove
        """
        if handler in self._subscribers[topic]:
            self._subscribers[topic].remove(handler)

    def clear(self, topic: str) -> None:
        """
        Clear all subscribers for a topic.

        Args:
            topic: Topic name
        """
        self._subscribers[topic].clear()
