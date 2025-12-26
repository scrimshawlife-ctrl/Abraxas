from __future__ import annotations

import json
from pathlib import Path

from abraxas.memetic.registry import append_a2_terms_to_registry, compute_missed_terms


def test_a2_registry_missed(tmp_path: Path):
    registry = tmp_path / "terms.jsonl"

    a2_seed = tmp_path / "a2_seed.json"
    a2_seed.write_text(
        json.dumps(
            {
                "run_id": "seed",
                "ts": "2025-12-01T00:00:00+00:00",
                "terms": [
                    {
                        "term": "veilbreaker",
                        "term_id": "t1",
                        "count": 2,
                        "novelty_score": 0.3,
                        "propagation_score": 0.4,
                        "manipulation_risk": 0.1,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    append_a2_terms_to_registry(a2_path=str(a2_seed), registry_path=str(registry))

    a2_new = tmp_path / "a2_new.json"
    a2_new.write_text(
        json.dumps(
            {
                "run_id": "r1",
                "ts": "2025-12-20T00:00:00+00:00",
                "terms": [
                    {
                        "term": "veilbreaker",
                        "term_id": "t1",
                        "count": 3,
                        "novelty_score": 0.4,
                        "propagation_score": 0.5,
                        "manipulation_risk": 0.1,
                    },
                    {
                        "term": "deepfake fog",
                        "term_id": "t2",
                        "count": 4,
                        "novelty_score": 0.8,
                        "propagation_score": 0.7,
                        "manipulation_risk": 0.6,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    rep = compute_missed_terms(
        a2_path=str(a2_new), registry_path=str(registry), resurrect_after_days=10
    )
    assert rep["present"] == 2
    assert len(rep["missed"]) == 1
    assert rep["missed"][0]["term"] == "deepfake fog"
