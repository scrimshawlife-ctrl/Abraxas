from __future__ import annotations

from abraxas.seeds.year_run import _flatten_frame


def test_flatten_frame_preserves_domain():
    frame = {
        "window_start_utc": "2025-01-01T00:00:00Z",
        "window_end_utc": "2025-01-08T00:00:00Z",
        "domain": "culture_memes",
        "vectors": {"V1_SIGNAL_DENSITY": {"score": 0.12, "computability": "computed"}},
        "provenance": {"inputs_hash": "x"},
    }
    flat = _flatten_frame(frame)
    assert flat["domain"] == "culture_memes"
    assert flat["vectors"]["V1_SIGNAL_DENSITY"] == 0.12
