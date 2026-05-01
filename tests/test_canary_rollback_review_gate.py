from __future__ import annotations

import copy

from abraxas.canary.rollback_review_runner import run_rollback_review_gate
from abraxas.core.canonical import canonical_json


def _rb(status: str = "prepared", replayable: bool = True, rollback_prepared: bool = True, rollback_key: str | None = "rk", source_key: str = "s1", reason: str | None = None) -> dict:
    return {
        "rollback_id": f"rb-{source_key}-{status}",
        "observation_id": "obs1",
        "execution_id": "ex1",
        "source_key": source_key,
        "rollback_key": rollback_key,
        "status": status,
        "rollback_plan": {"artifact_hash": "ah", "artifact_path": "/tmp/a"},
        "safety": {"replayable": replayable, "rollback_prepared": rollback_prepared, "reason": reason},
        "lineage": {"observation_hash": "oh", "execution_hash": "eh"},
    }


def test_logic_determinism_authority_counts_ordering_and_immutability() -> None:
    a = _rb(status="prepared", replayable=True, rollback_prepared=True, rollback_key="rk", source_key="s2")
    b = _rb(status="not_computable", reason="x", source_key="s1")
    c = _rb(status="weird", source_key="s3")
    d = _rb(status="prepared", replayable=False, source_key="s4")
    e = _rb(status="prepared", replayable=True, rollback_prepared=False, source_key="s5")
    f = _rb(status="prepared", replayable=True, rollback_prepared=True, rollback_key=None, source_key="s6")
    inp = {"rollbacks": [f, e, d, c, b, a]}
    inp0 = copy.deepcopy(inp)

    out = run_rollback_review_gate(inp)

    by_src = {r["source_key"]: r for r in out["recommendations"]}
    assert by_src["s2"]["status"] == "recommend_approve_for_rollback_review"
    assert by_src["s1"]["status"] == "not_computable"
    assert by_src["s3"]["status"] == "not_computable"
    assert by_src["s4"]["status"] == "recommend_hold"
    assert by_src["s5"]["status"] == "recommend_hold"
    assert by_src["s6"]["status"] == "not_computable"

    assert out["counts"] == {
        "rollback_preps_total": 6,
        "recommend_approve_for_rollback_review": 1,
        "recommend_hold": 2,
        "recommend_reject": 0,
        "not_computable": 3,
    }

    assert out["authority"] == {
        "rollback_review_recommendation": True,
        "rollback_execution": False,
        "production_activation": False,
        "baseline_mutation": False,
        "runtime_config_write": False,
        "promotion": False,
        "execution": False,
        "scheduler": False,
    }

    assert out["recommendations"] == sorted(out["recommendations"], key=lambda r: (r["source_key"], r["recommendation_id"]))

    out2 = run_rollback_review_gate(inp)
    assert canonical_json(out) == canonical_json(out2)
    assert by_src["s2"]["recommendation_id"] == [r for r in out2["recommendations"] if r["source_key"] == "s2"][0]["recommendation_id"]

    assert inp == inp0
