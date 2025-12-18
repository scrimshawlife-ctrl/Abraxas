"""Resonance frame: core data structure for events flowing through Abraxas."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class ResonanceFrame(BaseModel):
    """
    A resonance frame represents a single event or message with metadata.

    This is the atomic unit of data that flows through the Abraxas pipeline.
    All derived fields must be deterministic and recomputable.
    """

    event_id: str = Field(..., description="Unique event identifier")
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Event timestamp")
    source: str = Field(..., description="Source system or channel")
    text: str = Field(..., description="Primary text content")
    meta: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    # Derived fields (must be deterministic)
    tokens: list[str] = Field(default_factory=list, description="Tokenized text (deterministic)")
    phonetic_signature: str | None = Field(default=None, description="Phonetic representation")
    features: dict[str, float] = Field(default_factory=dict, description="Extracted features")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

    def __hash__(self) -> int:
        """Hash based on immutable event_id."""
        return hash(self.event_id)

    def __eq__(self, other: object) -> bool:
        """Equality based on event_id."""
        if not isinstance(other, ResonanceFrame):
            return False
        return self.event_id == other.event_id

    @staticmethod
    def sort_key(frame: ResonanceFrame) -> tuple[datetime, str]:
        """Deterministic sort key: (timestamp, event_id)."""
        return (frame.ts, frame.event_id)
