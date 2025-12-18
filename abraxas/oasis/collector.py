"""OAS Collector: converts Decodo events to ResonanceFrames for OAS pipeline."""

from __future__ import annotations

from abraxas.core.resonance_frame import ResonanceFrame
from abraxas.decodo.adapter import DecodoAdapter
from abraxas.decodo.models import DecodoEvent


class OASCollector:
    """
    Collects and normalizes data for OAS pipeline.

    Converts Decodo events to ResonanceFrames with deterministic ordering.
    """

    def __init__(self):
        self.adapter = DecodoAdapter()

    def collect_from_events(self, events: list[DecodoEvent]) -> list[ResonanceFrame]:
        """
        Collect ResonanceFrames from Decodo events.

        Returns frames in deterministic order: sorted by (timestamp, event_id).
        """
        frames = self.adapter.events_to_frames(events)
        return frames

    def collect_from_dict(self, event_dicts: list[dict]) -> list[ResonanceFrame]:
        """
        Collect frames from raw dictionaries (for testing/fixtures).

        Expects dict format compatible with DecodoEvent.
        """
        events = [DecodoEvent(**d) for d in event_dicts]
        return self.collect_from_events(events)
