from __future__ import annotations

import copy

from abraxas.canary.trend_ledger_runner import run_trend_ledger
from abraxas.core.canonical import canonical_json


def _analysis(status: str = "stable", aid: str = "aid-1", ahash: str = "ahash-1") -> dict:
    return {
        "artifact": "CANARY-CYCLE-TREND-ANALYSIS-001",
        "schema_version": "CanaryCycleTrendAnalysis.v1",
        "analysis_id": aid,
        "analysis_hash": ahash,
        "trend": {"status": status, "reason": f"reason-{status}"},
        "rates": {"closure_rate": 0.8, "open_rate": 0.2, "not_computable_rate": 0.0},
        "counts": {"cycles_total": 5, "closed": 4, "open": 1, "not_computable": 0},
        "lineage": {"closure_ledger_hash": "clh-1"},
    }


def test_trend_ledger_creation_dedupe_preserve_determinism_ordering_counts_byte_identity() -> None:
    a = _analysis("stable", "aid-s", "ahash-s")
    a0 = copy.deepcopy(a)

    out = run_trend_ledger(a)
    assert out["counts"] == {
        "analyses_total": 1,
        "entries_created": 1,
        "entries_existing": 0,
        "entries_total": 1,
        "stable": 1,
        "needs_attention": 0,
        "not_computable": 0,
    }

    e = out["entries"][0]
    out_repeat = run_trend_ledger(a)
    assert e["entry_id"] == out_repeat["entries"][0]["entry_id"]
    assert e["audit"]["lineage_hash"] == out_repeat["entries"][0]["audit"]["lineage_hash"]

    prior = copy.deepcopy(out)
    prior["entries"][0]["review"]["review_notes"] = ["manual-preserved"]
    out2 = run_trend_ledger(a, prior)
    assert out2["counts"]["entries_created"] == 0
    assert out2["counts"]["entries_existing"] == 1
    assert out2["entries"][0]["review"]["review_notes"] == ["manual-preserved"]

    a2 = _analysis("needs_attention", "aid-a", "ahash-a")
    a3 = _analysis("not_computable", "aid-n", "ahash-n")
    out3 = run_trend_ledger(a2, out2)
    out4 = run_trend_ledger(a3, out3)

    assert out4["counts"] == {
        "analyses_total": 1,
        "entries_created": 1,
        "entries_existing": 0,
        "entries_total": 3,
        "stable": 1,
        "needs_attention": 1,
        "not_computable": 1,
    }
    assert out4["entries"] == sorted(out4["entries"], key=lambda x: (x["trend_status"], x["analysis_id"], x["entry_id"]))

    assert out4["authority"] == {
        "trend_ledger_write": True,
        "production_activation": False,
        "baseline_mutation": False,
        "runtime_config_write": False,
        "promotion": False,
        "execution": False,
        "scheduler": False,
    }
    assert canonical_json(out4) == canonical_json(run_trend_ledger(a3, out3))
    assert a == a0
