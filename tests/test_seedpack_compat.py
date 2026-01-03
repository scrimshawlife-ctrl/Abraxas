from __future__ import annotations

from abraxas.seeds.seedpack_compat import normalize_seedpack


def test_seedpack_v01_records_to_v02_frames_deterministic():
    v01 = {
        "schema_version": "seedpack.v0.1",
        "year": 2025,
        "records": [
            {
                "window_start_utc": "2025-01-01T00:00:00Z",
                "window_end_utc": "2025-01-08T00:00:00Z",
                "domain": "culture_memes",
                "vectors": {"V1_SIGNAL_DENSITY": {"score": 0.1, "computability": "computed"}},
                "provenance": {"inputs_hash": "abc"},
            }
        ],
    }
    n1 = normalize_seedpack(v01)
    n2 = normalize_seedpack(v01)
    assert n1["schema_version"] == "seedpack.v0.2"
    assert "frames" in n1 and isinstance(n1["frames"], list)
    assert n1 == n2
