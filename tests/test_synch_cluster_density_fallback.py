from __future__ import annotations

from abraxas.atlas.construct import build_atlas_pack


def test_synch_cluster_density_score_fallback_is_deterministic():
    seedpack = {
        "schema_version": "seedpack.v0.2",
        "year": 2025,
        "frames": [
            {
                "window_start_utc": "2025-01-01T00:00:00Z",
                "window_end_utc": "2025-01-08T00:00:00Z",
                "domain": "culture_memes",
                "vectors": {
                    "V1_SIGNAL_DENSITY": {"score": 0.6, "computability": "computed"},
                    "V2_SIGNAL_INTEGRITY": {"score": 0.4, "computability": "computed"},
                },
                "provenance": {"inputs_hash": "x"},
            }
        ],
        "influence": {"ics": {}, "provenance": {}},
        "synchronicity": {
            "stage": "envelope",
            "envelopes": [
                {
                    "domains_involved": ["culture_memes"],
                    "vectors_activated": ["V1_SIGNAL_DENSITY", "V2_SIGNAL_INTEGRITY"],
                    "time_window": "2025-01-01T00:00:00Z/2025-01-08T00:00:00Z",
                    "metrics": {},
                    "provenance": {"inputs_hash": "y"},
                }
            ],
            "provenance": {"inputs_hash": "z"},
        },
    }
    atlas_a = build_atlas_pack(seedpack, window_granularity="weekly").model_dump()
    atlas_b = build_atlas_pack(seedpack, window_granularity="weekly").model_dump()
    cluster_a = (atlas_a.get("synchronicity_clusters") or [])[0]
    cluster_b = (atlas_b.get("synchronicity_clusters") or [])[0]
    assert cluster_a["density_score"] is not None
    assert cluster_a == cluster_b
