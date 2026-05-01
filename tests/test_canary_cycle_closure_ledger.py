from __future__ import annotations

import copy

from abraxas.canary.closure_ledger_runner import run_cycle_closure_ledger
from abraxas.core.canonical import canonical_json


def _report(status: str = "closed") -> dict:
    return {
        "artifact": "CANARY-CYCLE-CLOSURE-REPORT-001",
        "schema_version": "CanaryCycleClosureReport.v1",
        "report_id": f"rid-{status}",
        "report_hash": f"rhash-{status}",
        "closure": {"closure_status": status, "reason": f"reason-{status}"},
        "symmetry": {"observation_symmetry_status": "complete"},
        "reversibility": {"reversibility_status": "ready"},
        "lineage": {"x": 1},
    }


def test_closure_ledger_creation_dedupe_preserve_determinism_ordering_counts_authority_immutability() -> None:
    r = _report("closed")
    r0 = copy.deepcopy(r)
    out = run_cycle_closure_ledger(r)
    assert out["counts"] == {
        "reports_total": 1,
        "entries_created": 1,
        "entries_existing": 0,
        "entries_total": 1,
        "closed": 1,
        "open": 0,
        "not_computable": 0,
    }
    e = out["entries"][0]
    assert e["entry_id"] == run_cycle_closure_ledger(r)["entries"][0]["entry_id"]
    assert e["audit"]["lineage_hash"] == run_cycle_closure_ledger(r)["entries"][0]["audit"]["lineage_hash"]

    # preserve existing exactly
    prior = copy.deepcopy(out)
    prior["entries"][0]["review"]["review_notes"] = ["manual"]
    out2 = run_cycle_closure_ledger(r, prior)
    assert out2["counts"]["entries_created"] == 0
    assert out2["counts"]["entries_existing"] == 1
    assert out2["entries"][0]["review"]["review_notes"] == ["manual"]

    # add second entry for ordering/counts
    r_open = _report("open")
    out3 = run_cycle_closure_ledger(r_open, out2)
    assert out3["counts"]["entries_total"] == 2
    assert out3["counts"]["closed"] == 1
    assert out3["counts"]["open"] == 1
    assert out3["entries"] == sorted(out3["entries"], key=lambda x: (x["closure_status"], x["report_id"], x["entry_id"]))

    assert out3["authority"] == {
        "closure_ledger_write": True,
        "production_activation": False,
        "baseline_mutation": False,
        "runtime_config_write": False,
        "promotion": False,
        "execution": False,
        "scheduler": False,
    }

    assert canonical_json(out3) == canonical_json(run_cycle_closure_ledger(r_open, out2))
    assert r == r0
