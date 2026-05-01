from __future__ import annotations

import copy
from hashlib import sha256

from abraxas.canary.review_runner import build_canary_review_gate_run
from abraxas.core.canonical import canonical_json


def _run_inputs(delta_error: float, scores_used: int, simulation_status: str = "computed", sim_reason: str | None = None):
    sim = {
        "simulation_version": "CanaryOverlaySimulation.v1",
        "overlay_id": "ov1",
        "source_key": "s1",
        "status": simulation_status,
        "baseline_error": 0.2,
        "simulated_error": 0.2 + delta_error,
        "delta_error": delta_error,
        "improvement_direction": "neutral",
        "coverage": {"forecasts_matched": 5, "scores_used": scores_used},
        "reason": sim_reason,
    }
    simulations = {"simulations": [sim]}
    overlays = {"overlays": [{"overlay_id": "ov1", "entry_id": "e1", "proposal_id": "p1", "source_key": "s1"}]}
    ledger = {"entries": [{"entry_id": "e1", "weight": 0.5}]}
    return simulations, overlays, ledger


def _status(delta: float, scores: int) -> str:
    s, o, l = _run_inputs(delta, scores)
    return build_canary_review_gate_run(s, o, l)["recommendations"][0]["status"]


def test_threshold_status_logic() -> None:
    assert _status(-0.02, 3) == "recommend_approve_for_activation_review"
    assert _status(0.02, 3) == "recommend_reject"
    assert _status(0.001, 3) == "recommend_hold"
    assert _status(-0.02, 2) == "recommend_hold"


def test_not_computable_and_missing_overlay() -> None:
    s, o, l = _run_inputs(0.0, 3, simulation_status="not_computable", sim_reason="no_scores_available")
    run = build_canary_review_gate_run(s, o, l)
    assert run["recommendations"][0]["status"] == "not_computable"
    assert run["recommendations"][0]["reason"] == "simulation_not_computable:no_scores_available"

    run2 = build_canary_review_gate_run(s, {"overlays": []}, l)
    assert run2["recommendations"][0]["status"] == "not_computable"
    assert run2["recommendations"][0]["reason"] == "missing_overlay"


def test_missing_ledger_suffix_and_determinism_and_authority_and_counts_and_immutability() -> None:
    s, o, l = _run_inputs(-0.02, 3)
    l = {"entries": []}
    s0, o0, l0 = copy.deepcopy(s), copy.deepcopy(o), copy.deepcopy(l)

    run_a = build_canary_review_gate_run(s, o, l)
    run_b = build_canary_review_gate_run(s, o, l)
    rec = run_a["recommendations"][0]

    assert rec["status"] == "recommend_approve_for_activation_review"
    assert rec["reason"].endswith("|missing_ledger_entry")
    assert rec["lineage"]["ledger_entry_hash"] is None
    assert canonical_json(run_a) == canonical_json(run_b)

    authority = run_a["authority"]
    assert authority == {
        "review_recommendation": True,
        "overlay_activation": False,
        "baseline_mutation": False,
        "runtime_config_write": False,
        "promotion": False,
        "execution": False,
        "scheduler": False,
    }
    assert run_a["counts"] == {
        "simulations_total": 1,
        "recommend_approve_for_activation_review": 1,
        "recommend_hold": 0,
        "recommend_reject": 0,
        "not_computable": 0,
    }

    assert (s, o, l) == (s0, o0, l0)


def test_recommendation_id_deterministic_formula() -> None:
    s, o, l = _run_inputs(0.02, 3)
    rec = build_canary_review_gate_run(s, o, l)["recommendations"][0]

    payload = {
        "recommendation_version": "CanaryReviewRecommendation.v1",
        "overlay_id": rec["overlay_id"],
        "entry_id": rec["entry_id"],
        "proposal_id": rec["proposal_id"],
        "source_key": rec["source_key"],
        "status": rec["status"],
        "basis": rec["basis"],
        "thresholds": rec["thresholds"],
        "reason": rec["reason"],
        "lineage": rec["lineage"],
        "authority": rec["authority"],
    }
    expected = sha256(canonical_json(payload).encode("utf-8")).hexdigest()
    assert rec["recommendation_id"] == expected


def test_byte_identical_repeated_writes(tmp_path) -> None:
    s, o, l = _run_inputs(0.001, 3)
    report = build_canary_review_gate_run(s, o, l)
    p1 = tmp_path / "a.json"
    p2 = tmp_path / "b.json"
    p1.write_text(canonical_json(report) + "\n", encoding="utf-8")
    p2.write_text(canonical_json(report) + "\n", encoding="utf-8")
    assert p1.read_bytes() == p2.read_bytes()
