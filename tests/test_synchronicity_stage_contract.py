from __future__ import annotations

from abraxas.runes.operators.synchronicity_map import apply_synchronicity_map


def test_synchronicity_bundle_has_stage_envelope():
    frames = [
        {"domain": "A", "vectors": {"V1_SIGNAL_DENSITY": 0.2}, "provenance": {"timestamp_utc": "2025-01-01T00:00:00Z"}},
        {"domain": "B", "vectors": {"V1_SIGNAL_DENSITY": 0.21}, "provenance": {"timestamp_utc": "2025-01-01T00:00:10Z"}},
    ]
    out = apply_synchronicity_map(frames)
    assert out.get("shadow_only") is True
    assert out.get("stage") == "envelope"
    assert "envelopes" in out
