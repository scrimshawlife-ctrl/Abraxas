"""Data models for Decodo events and streams."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class DecodoEvent(BaseModel):
    """A single event from Decodo scraper."""

    event_id: str = Field(..., description="Unique event identifier")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_url: str = Field(..., description="Source URL scraped")
    source_type: str = Field(default="universal", description="Decodo target type")
    content: str = Field(..., description="Scraped content")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class DecodoStream(BaseModel):
    """A stream of Decodo events."""

    stream_id: str = Field(..., description="Stream identifier")
    events: list[DecodoEvent] = Field(default_factory=list)
    start_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

    def add_event(self, event: DecodoEvent) -> None:
        """Add event to stream."""
        self.events.append(event)

    def close(self) -> None:
        """Mark stream as closed."""
        self.end_time = datetime.now(timezone.utc)
