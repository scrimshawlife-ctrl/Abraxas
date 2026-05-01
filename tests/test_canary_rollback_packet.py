from __future__ import annotations

import copy

from abraxas.canary.rollback_packet_runner import run_rollback_packet
from abraxas.core.canonical import canonical_json


def _rec(status: str = "recommend_approve_for_rollback_review", source_key: str = "s1") -> dict:
    return {
        "recommendation_id": f"rec-{source_key}",
        "rollback_id": f"rb-{source_key}",
        "observation_id": f"obs-{source_key}",
        "execution_id": f"ex-{source_key}",
        "source_key": source_key,
        "status": status,
        "basis": {"reason": "rollback_ready_for_review"},
        "lineage": {"rollback_hash": "rh", "observation_hash": "oh", "execution_hash": "eh"},
    }


def _prep(source_key: str = "s1", valid: bool = True) -> dict:
    base = {
        "rollback_id": f"rb-{source_key}",
        "observation_id": f"obs-{source_key}",
        "execution_id": f"ex-{source_key}",
        "status": "prepared",
        "rollback_key": "rk",
        "rollback_plan": {"mode": "deterministic_replay", "requires_artifact": True, "artifact_hash": "ah", "artifact_path": "/tmp/a"},
        "safety": {"replayable": True, "rollback_prepared": True, "reason": None},
        "lineage": {"observation_hash": "oh2", "execution_hash": "eh2"},
    }
    if not valid:
        base.pop("rollback_plan")
    return base


def _obs(source_key: str = "s1") -> dict:
    return {"observation_id": f"obs-{source_key}", "lineage": {"execution_hash": "eh3"}}


def test_packet_generation_rules_determinism_authority_ordering_counts_and_immutability() -> None:
    reviews = {"recommendations": [_rec("recommend_hold", "s2"), _rec("recommend_reject", "s3"), _rec("not_computable", "s4"), _rec("recommend_approve_for_rollback_review", "s1"), _rec("recommend_approve_for_rollback_review", "s5"), _rec("recommend_approve_for_rollback_review", "s6"), _rec("recommend_approve_for_rollback_review", "s7")]}
    preps = {"rollbacks": [_prep("s1"), _prep("s6", valid=False), _prep("s7")]}
    obs = {"entries": [_obs("s1"), _obs("s6")]}
    r0, p0, o0 = copy.deepcopy(reviews), copy.deepcopy(preps), copy.deepcopy(obs)

    out = run_rollback_packet(reviews, preps, obs)
    assert out["counts"] == {"recommendations_total": 7, "packets_created": 1, "skipped": 6}
    assert len(out["packets"]) == 1
    pkt = out["packets"][0]
    assert pkt["rollback_plan"]["artifact_hash"] == "ah"
    assert pkt["safety"]["rollback_prepared"] is True
    assert pkt["recommendation_status"] == "recommend_approve_for_rollback_review"

    reasons = [s["reason"] for s in out["skipped_recommendations"]]
    assert "not_approved_for_rollback_review:recommend_hold" in reasons
    assert "not_approved_for_rollback_review:recommend_reject" in reasons
    assert "not_approved_for_rollback_review:not_computable" in reasons
    assert "missing_rollback_prep" in reasons
    assert "missing_observation_entry" in reasons
    assert "invalid_rollback_prep" in reasons

    assert out["authority"] == {
        "rollback_packet_generation": True,
        "rollback_execution": False,
        "production_activation": False,
        "baseline_mutation": False,
        "runtime_config_write": False,
        "promotion": False,
        "execution": False,
        "scheduler": False,
    }

    assert out["packets"] == sorted(out["packets"], key=lambda p: (p["source_key"], p["packet_id"]))
    assert out["skipped_recommendations"] == sorted(out["skipped_recommendations"], key=lambda s: (str(s.get("source_key") or ""), str(s.get("rollback_id") or ""), str(s.get("reason") or "")))

    out2 = run_rollback_packet(reviews, preps, obs)
    assert canonical_json(out) == canonical_json(out2)
    assert pkt["packet_id"] == out2["packets"][0]["packet_id"]

    assert (reviews, preps, obs) == (r0, p0, o0)
