from __future__ import annotations

from pathlib import Path

from abraxas.memetic.temporal import build_temporal_profiles
from abraxas.evolve.ledger import append_chained_jsonl


def test_temporal_phase_build(tmp_path: Path):
    reg = tmp_path / "terms.jsonl"
    append_chained_jsonl(
        str(reg),
        {
            "term_key": "aaaaaaaaaaaaaaaa",
            "term": "deepfake fog",
            "ts": "2025-12-20T00:00:00+00:00",
            "first_seen_ts": "2025-12-20T00:00:00+00:00",
            "last_seen_ts": "2025-12-20T00:00:00+00:00",
            "count": 5,
            "novelty_score": 0.8,
            "propagation_score": 0.7,
            "manipulation_risk": 0.6,
            "tags": ["novel", "spreading"],
        },
    )
    append_chained_jsonl(
        str(reg),
        {
            "term_key": "aaaaaaaaaaaaaaaa",
            "term": "deepfake fog",
            "ts": "2025-12-25T00:00:00+00:00",
            "first_seen_ts": "2025-12-20T00:00:00+00:00",
            "last_seen_ts": "2025-12-25T00:00:00+00:00",
            "count": 8,
            "novelty_score": 0.7,
            "propagation_score": 0.8,
            "manipulation_risk": 0.55,
            "tags": ["spreading"],
        },
    )
    profiles = build_temporal_profiles(
        str(reg),
        now_iso="2025-12-26T00:00:00+00:00",
        max_terms=50,
        min_obs=2,
    )
    assert len(profiles) == 1
    assert profiles[0].term == "deepfake fog"
    assert profiles[0].phase in {"surging", "plateau", "emergent", "resurgent"}
