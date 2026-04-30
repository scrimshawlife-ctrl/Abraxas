from __future__ import annotations

from pathlib import Path

from abraxas.governance.readiness_gate import run_readiness_gate


def test_readiness_gate_deterministic_and_ready() -> None:
    first = run_readiness_gate(".")
    second = run_readiness_gate(".")
    assert first == second
    assert first["status"] == "READY"


def test_hash_invariance_and_assertions() -> None:
    report = run_readiness_gate(".")
    checks = {item["id"]: item["status"] for item in report["checks"]}
    assert checks["hash_invariance"] == "PASS"
    assert checks["validator_clean"] == "PASS"
    assert checks["e2e_pass"] == "PASS"
    assert checks["mean_brier_expected"] == "PASS"
    assert checks["scored_count_expected"] == "PASS"


def test_no_forbidden_artifacts_and_file_created() -> None:
    report = run_readiness_gate(".")
    checks = {item["id"]: item["status"] for item in report["checks"]}
    assert checks["forbidden_artifacts"] == "PASS"
    assert Path("scripts/run_abx_readiness_gate.py").exists()
