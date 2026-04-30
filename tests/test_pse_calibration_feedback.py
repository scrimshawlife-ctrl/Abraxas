from __future__ import annotations

import json
from pathlib import Path

from abraxas.pse.brier_ledger import build_brier_ledger
from abraxas.pse.calibration_feedback import build_calibration_feedback
from abraxas.pse.outcome_tracker import build_outcome_ledger


def _scoreable_inputs() -> tuple[dict, dict]:
    predictions = json.loads(Path("fixtures/pse/scoreable_predictions.v1.json").read_text())
    outcomes = json.loads(Path("fixtures/pse/scoreable_outcomes.v1.json").read_text())
    outcome_ledger = build_outcome_ledger(predictions, outcomes)
    brier = build_brier_ledger(outcome_ledger)
    readiness = {"status": "READY"}
    return brier, readiness


def test_deterministic_output_and_reliability() -> None:
    brier, readiness = _scoreable_inputs()
    first = build_calibration_feedback(brier, readiness)
    second = build_calibration_feedback(brier, readiness)
    assert first == second
    assert first["status"] == "ADVISORY_ONLY"
    assert first["global_reliability"] == 0.8025


def test_readiness_gate_enforced() -> None:
    brier, _ = _scoreable_inputs()
    report = build_calibration_feedback(brier, {"status": "NOT_READY"})
    assert report["status"] == "NOT_COMPUTABLE"


def test_insufficient_evidence_and_no_mutation_flags() -> None:
    brier = {
        "summary": {"scored_count": 3, "mean_brier": 0.1975},
        "by_domain": {"oracle": {"count": 1, "mean_brier": 0.2}},
        "by_source": {"s1": {"count": 1, "mean_brier": 0.2}},
    }
    report = build_calibration_feedback(brier, {"status": "READY"})
    assert report["insufficient_evidence"]["domain"]["oracle"] == "insufficient_evidence"
    assert report["insufficient_evidence"]["source"]["s1"] == "insufficient_evidence"
    assert report["recommended_actions"][0]["applied"] is False
    assert report["recommended_actions"][0]["advisory_only"] is True
