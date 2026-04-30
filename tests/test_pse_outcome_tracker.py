from __future__ import annotations

from pathlib import Path

from abraxas.pse.models import clamp01
from abraxas.pse.outcome_tracker import build_outcome_ledger


def test_deterministic_output() -> None:
    predictions = [{"prediction_id": "p1", "event_id": "e1", "predicted_outcome": "YES", "probability": 0.7}]
    outcomes = [{"event_id": "e1", "resolved_outcome": "YES"}]
    assert build_outcome_ledger(predictions, outcomes) == build_outcome_ledger(predictions, outcomes)


def test_clamping_works() -> None:
    assert clamp01(-1) == 0.0
    assert clamp01(7) == 1.0


def test_hit_miss_partial_unresolved_not_computable() -> None:
    predictions = [
        {"prediction_id": "p_hit", "event_id": "e1", "predicted_outcome": "YES", "probability": 0.8},
        {"prediction_id": "p_miss", "event_id": "e2", "predicted_outcome": "YES", "probability": 0.8},
        {"prediction_id": "p_partial", "event_id": "e3", "predicted_outcome": "PARTIAL", "probability": 0.8},
        {"prediction_id": "p_unknown", "event_id": "e4", "predicted_outcome": "UNKNOWN", "probability": 0.8},
        {"prediction_id": "p_unresolved", "event_id": "e5", "predicted_outcome": "NO", "probability": 0.8},
    ]
    outcomes = [
        {"event_id": "e1", "resolved_outcome": "YES"},
        {"event_id": "e2", "resolved_outcome": "NO"},
        {"event_id": "e3", "resolved_outcome": "YES"},
        {"event_id": "e4", "resolved_outcome": "YES"},
    ]
    ledger = build_outcome_ledger(predictions, outcomes)
    resolutions = {r["prediction_id"]: r["resolution"] for r in ledger["resolutions"]}
    assert resolutions["p_hit"] == "HIT"
    assert resolutions["p_miss"] == "MISS"
    assert resolutions["p_partial"] == "PARTIAL"
    assert resolutions["p_unknown"] == "NOT_COMPUTABLE"
    assert resolutions["p_unresolved"] == "UNRESOLVED"


def test_orphan_and_latest_outcome() -> None:
    predictions = [{"prediction_id": "p1", "event_id": "e1", "predicted_outcome": "YES", "probability": 0.5}]
    outcomes = [
        {"event_id": "e1", "resolved_outcome": "NO"},
        {"event_id": "e1", "resolved_outcome": "YES"},
        {"event_id": "orphan", "resolved_outcome": "YES"},
    ]
    ledger = build_outcome_ledger(predictions, outcomes)
    assert ledger["resolutions"][0]["resolved_outcome"] == "YES"
    assert ledger["diagnostics"] == [{"type": "ORPHAN_OUTCOME", "event_id": "orphan"}]


def test_no_portfolio_files_created() -> None:
    assert not Path("abraxas/pse/portfolio.py").exists()
