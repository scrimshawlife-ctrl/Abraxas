from __future__ import annotations

from abraxas.evolve.non_truncation import enforce_non_truncation


def test_views_do_not_replace_raw():
    core = {"version": "x", "views": {"top": [1, 2, 3]}}
    out = enforce_non_truncation(artifact=core, raw_full={"all": list(range(10))})
    assert len(out["raw_full"]["all"]) >= len(out["views"]["top"])
