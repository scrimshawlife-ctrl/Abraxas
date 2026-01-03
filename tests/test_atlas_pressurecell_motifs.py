from __future__ import annotations

from abraxas.atlas.construct import build_atlas_pack


def test_pressure_cells_include_motifs_and_edges():
    seedpack = {
        "schema_version": "seedpack.v0.2",
        "year": 2025,
        "frames": [
            {
                "window_start_utc": "2025-01-01T00:00:00Z",
                "window_end_utc": "2025-01-08T00:00:00Z",
                "domain": "culture_memes",
                "vectors": {
                    "V1_SIGNAL_DENSITY": {"score": 0.9, "computability": "computed"},
                    "V2_SIGNAL_INTEGRITY": {"score": 0.8, "computability": "computed"},
                    "V3_NARRATIVE_COHERENCE": {"score": 0.7, "computability": "computed"},
                },
                "provenance": {"inputs_hash": "x"},
            }
        ],
        "influence": {"ics": {}, "provenance": {}},
        "synchronicity": {"stage": "envelope", "envelopes": [], "provenance": {}},
    }
    atlas = build_atlas_pack(seedpack, window_granularity="weekly").model_dump()
    cells = atlas.get("pressure_cells") or []
    assert cells, "pressure_cells should not be empty"
    sample = cells[0]
    assert "motifs" in sample
    assert "motif_edges" in sample
    assert isinstance(sample["motifs"], list)
    assert len(sample["motifs"]) >= 1
