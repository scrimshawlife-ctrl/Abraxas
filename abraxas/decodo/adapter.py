"""Adapter to convert Decodo events to ResonanceFrames."""

from __future__ import annotations

from datetime import datetime

from abraxas.core.resonance_frame import ResonanceFrame
from abraxas.decodo.models import DecodoEvent, DecodoStream


class DecodoAdapter:
    """Converts Decodo events to ResonanceFrames for Abraxas processing."""

    @staticmethod
    def event_to_frame(event: DecodoEvent) -> ResonanceFrame:
        """Convert a single Decodo event to a ResonanceFrame."""
        return ResonanceFrame(
            event_id=event.event_id,
            ts=event.timestamp,
            source=f"decodo:{event.source_type}",
            text=event.content,
            meta={
                "source_url": event.source_url,
                "source_type": event.source_type,
                **event.metadata,
            },
        )

    @staticmethod
    def stream_to_frames(stream: DecodoStream) -> list[ResonanceFrame]:
        """
        Convert all events in a stream to ResonanceFrames.

        Returns frames in deterministic order: sorted by (timestamp, event_id).
        """
        frames = [DecodoAdapter.event_to_frame(event) for event in stream.events]

        # Deterministic sort
        frames.sort(key=ResonanceFrame.sort_key)

        return frames

    @staticmethod
    def events_to_frames(events: list[DecodoEvent]) -> list[ResonanceFrame]:
        """Convert a list of events to ResonanceFrames with deterministic ordering."""
        frames = [DecodoAdapter.event_to_frame(event) for event in events]
        frames.sort(key=ResonanceFrame.sort_key)
        return frames
