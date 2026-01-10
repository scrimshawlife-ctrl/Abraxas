"""Tests for SourcePacket serialization determinism."""

from __future__ import annotations

from abraxas.sources.packets import SourcePacket


def test_source_packet_hash_stable():
    packet = SourcePacket(
        source_id="NOAA_SWPC_PLANETARY_KP",
        observed_at_utc="2025-01-01T00:00:00Z",
        window_start_utc="2025-01-01T00:00:00Z",
        window_end_utc="2025-01-01T01:00:00Z",
        payload={"b": 2, "a": 1},
        provenance={"z": 1, "a": 2},
    )
    hashes = {packet.packet_hash() for _ in range(12)}
    assert len(hashes) == 1
