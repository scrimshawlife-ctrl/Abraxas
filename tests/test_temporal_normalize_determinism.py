"""Tests for temporal normalization determinism."""

from __future__ import annotations

from abraxas.temporal.normalize import normalize_timestamp


def test_temporal_normalize_stable():
    hashes = {normalize_timestamp("2025-03-09T01:30:00", "America/New_York") for _ in range(12)}
    assert len(hashes) == 1, "Temporal normalization must be stable across reruns"
