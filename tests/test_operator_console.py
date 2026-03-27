from __future__ import annotations

from pathlib import Path

from abx.operator_console import dispatch_operator_command


def _payload(tmp_path: Path) -> dict:
    return {
        "base_dir": str(tmp_path),
        "run_id": "RUN-OP-001",
        "scenario_id": "SCN-OP-001",
        "events": [
            {"forecast_id": "f-1", "asset_id": "BTC", "score": 0.8, "confidence": 0.9, "entry_price": 100.0, "exit_price": 110.0},
            {"forecast_id": "f-2", "asset_id": "ETH", "score": 0.5, "confidence": 0.3, "entry_price": 100.0, "exit_price": 100.0},
        ],
        "strategy_config": {"min_confidence": 0.6, "position_risk_fraction": 0.1, "max_notional": 1000.0},
    }


def test_run_simulation_command(tmp_path: Path) -> None:
    out = dispatch_operator_command("run-simulation", _payload(tmp_path))
    assert out["simulation"]["artifactType"] == "SimulationArtifact.v1"
    assert out["validation"]["artifactType"] == "ValidationResultArtifact.v1"
    assert out["proof_summary"]["artifactType"] == "ProofSummaryArtifact.v1"
    assert out["proof_chain"]["artifactType"] == "ProofChainArtifact.v1"
    assert out["ledger"]["recordCount"] > 0
    assert "RUN-OP-001/SCN-OP-001.jsonl" in out["ledger"]["path"]


def test_run_simulation_is_deterministic_for_same_payload(tmp_path: Path) -> None:
    payload = _payload(tmp_path)
    a = dispatch_operator_command("run-simulation", payload)
    b = dispatch_operator_command("run-simulation", payload)
    assert a["simulation"]["replayHash"] == b["simulation"]["replayHash"]
    assert a["proof_chain"]["status"] == b["proof_chain"]["status"]
    assert a["ledger"]["recordCount"] == b["ledger"]["recordCount"]


def test_compare_strategies_command(tmp_path: Path) -> None:
    payload = _payload(tmp_path)
    payload["strategy_a"] = {"min_confidence": 0.5, "position_risk_fraction": 0.1, "max_notional": 1000.0}
    payload["strategy_b"] = {"min_confidence": 0.8, "position_risk_fraction": 0.1, "max_notional": 1000.0}
    out = dispatch_operator_command("compare-strategies", payload)
    assert out["artifact_id"].startswith("strategy-comparison-")
    assert "metrics" in out


def test_inspection_commands(tmp_path: Path) -> None:
    payload = _payload(tmp_path)
    dispatch_operator_command("run-simulation", payload)

    proof = dispatch_operator_command("inspect-proof-chain", payload)
    portfolio = dispatch_operator_command("inspect-portfolio", payload)
    validation = dispatch_operator_command("inspect-validation", payload)
    rejections = dispatch_operator_command("inspect-rejections", payload)

    assert proof["artifactType"] == "ProofChainArtifact.v1"
    assert "equity" in portfolio
    assert validation["artifactType"] == "ValidationResultArtifact.v1"
    assert isinstance(rejections["rejections"], list)
