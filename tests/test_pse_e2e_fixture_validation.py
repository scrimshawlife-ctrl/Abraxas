from __future__ import annotations

from pathlib import Path

from scripts.run_pse_e2e_fixture_validation import run_validation


def test_e2e_deterministic_and_pass() -> None:
    first = run_validation()
    second = run_validation()
    assert first == second
    assert first["status"] == "PASS"


def test_e2e_brier_summary_values() -> None:
    report = run_validation()
    summary = report["brier_summary"]
    assert summary["scored_count"] == 3
    assert summary["mean_brier"] == 0.1975


def test_no_learning_artifacts_created() -> None:
    assert not Path("abraxas/pse/learning.py").exists()
