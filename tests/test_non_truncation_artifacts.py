from __future__ import annotations

from abraxas.evolve.non_truncation import enforce_non_truncation


def test_enforce_non_truncation_embeds_raw_full():
    artifact = {"version": "x", "views": {"top": [1, 2, 3]}}
    out = enforce_non_truncation(artifact=artifact, raw_full={"all": list(range(100))})
    assert out.get("policy", {}).get("non_truncation") is True
    assert "raw_full" in out
    assert len(out["raw_full"]["all"]) == 100
