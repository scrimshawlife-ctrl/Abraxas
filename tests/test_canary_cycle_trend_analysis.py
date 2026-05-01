from __future__ import annotations

import copy

from abraxas.canary.trend_runner import run_cycle_trend_analysis
from abraxas.core.canonical import canonical_json


def _entry(closure: str, sym: str, rev: str) -> dict:
    return {"closure_status": closure, "observation_symmetry_status": sym, "reversibility_status": rev}


def test_trend_analysis_rules_determinism_authority_counts_immutability() -> None:
    empty = {"entries": []}
    out_empty = run_cycle_trend_analysis(empty)
    assert out_empty["trend"]["status"] == "not_computable"
    assert out_empty["recommendations"] == ["collect_cycle_closure_data"]

    stable_entries = {"entries": [_entry("closed", "complete", "ready") for _ in range(5)]}
    out_stable = run_cycle_trend_analysis(stable_entries)
    assert out_stable["trend"]["status"] == "stable"
    assert out_stable["recommendations"] == ["continue_shadow_observation"]

    needs_entries = {
        "entries": [
            _entry("open", "incomplete", "not_ready"),
            _entry("closed", "complete", "partial"),
            _entry("closed", "complete", "ready"),
            _entry("open", "incomplete", "not_ready"),
            _entry("closed", "complete", "ready"),
        ]
    }
    n0 = copy.deepcopy(needs_entries)
    out_needs = run_cycle_trend_analysis(needs_entries)
    assert out_needs["trend"]["status"] == "needs_attention"
    assert "increase_cycle_closure_rate" in out_needs["recommendations"]
    assert "improve_observation_symmetry" in out_needs["recommendations"]
    assert "improve_reversibility_readiness" in out_needs["recommendations"]
    assert out_needs["rates"]["closure_rate"] == 0.6

    # deterministic ids/hashes and byte identical
    out2 = run_cycle_trend_analysis(needs_entries)
    assert out_needs["analysis_id"] == out2["analysis_id"]
    assert out_needs["analysis_hash"] == out2["analysis_hash"]
    assert canonical_json(out_needs) == canonical_json(out2)

    assert out_needs["authority"] == {
        "trend_analysis": True,
        "production_activation": False,
        "baseline_mutation": False,
        "runtime_config_write": False,
        "promotion": False,
        "execution": False,
        "scheduler": False,
    }
    assert out_needs["counts"] == {"cycles_total": 5, "closed": 3, "open": 2, "not_computable": 0}
    assert needs_entries == n0
