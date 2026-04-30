from __future__ import annotations

from pathlib import Path

from abraxas.pse.brier_ledger import build_brier_ledger
from abraxas.pse.calibration_models import clamp01


def test_deterministic_output() -> None:
    ledger = {"resolutions": [{"prediction_id": "p1", "event_id": "e1", "predicted_outcome": "YES", "resolved_outcome": "YES", "probability": 0.8, "status": "RESOLVED"}]}
    assert build_brier_ledger(ledger) == build_brier_ledger(ledger)


def test_clamping_works() -> None:
    assert clamp01(-2) == 0.0
    assert clamp01(2) == 1.0


def test_yes_yes_and_no_no_scoring() -> None:
    ledger = {"resolutions": [
        {"prediction_id": "p1", "event_id": "e1", "predicted_outcome": "YES", "resolved_outcome": "YES", "probability": 0.8, "status": "RESOLVED"},
        {"prediction_id": "p2", "event_id": "e2", "predicted_outcome": "NO", "resolved_outcome": "NO", "probability": 0.2, "status": "RESOLVED"},
    ]}
    report = build_brier_ledger(ledger)
    assert report["scores"][0]["brier"] == 0.04
    assert report["scores"][1]["brier"] == 0.04


def test_wrong_predictions_and_skips_aggregation() -> None:
    ledger = {"resolutions": [
        {"prediction_id": "p3", "event_id": "e3", "predicted_outcome": "YES", "resolved_outcome": "NO", "probability": 0.7, "status": "RESOLVED", "domain": "oracle", "source": "s1"},
        {"prediction_id": "p4", "event_id": "e4", "predicted_outcome": "NO", "resolved_outcome": "YES", "probability": 0.3, "status": "RESOLVED", "domain": "oracle", "source": "s1"},
        {"prediction_id": "p5", "event_id": "e5", "predicted_outcome": "PARTIAL", "resolved_outcome": "YES", "probability": 0.5, "status": "RESOLVED"},
    ]}
    report = build_brier_ledger(ledger)
    assert report["summary"]["scored_count"] == 2
    assert report["summary"]["skipped_count"] == 1
    assert report["summary"]["mean_brier"] == 0.49
    assert report["by_domain"]["oracle"]["count"] == 2
    assert report["by_source"]["s1"]["mean_brier"] == 0.49


def test_empty_not_computable() -> None:
    report = build_brier_ledger({"resolutions": []})
    assert report["status"] == "NOT_COMPUTABLE"


def test_no_learning_or_portfolio_files_created() -> None:
    assert not Path("abraxas/pse/portfolio.py").exists()
    assert not Path("abraxas/pse/learning.py").exists()
