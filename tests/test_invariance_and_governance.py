from __future__ import annotations

from pathlib import Path

from abx.canon_checks import run_canon_checks
from abx.closure_summary import build_closure_summary
from abx.invariance_harness import run_invariance_harness
from abx.lifecycle_policy import enforce_lane_policy, evaluate_promotion_eligibility
from abx.operator_console import dispatch_operator_command


def _payload(tmp_path: Path) -> dict:
    return {
        "base_dir": str(tmp_path),
        "run_id": "RUN-GOV-001",
        "scenario_id": "SCN-GOV-001",
        "events": [
            {"forecast_id": "f-1", "asset_id": "BTC", "score": 0.8, "confidence": 0.9, "entry_price": 100.0, "exit_price": 110.0},
        ],
        "strategy_config": {"min_confidence": 0.6, "position_risk_fraction": 0.1, "max_notional": 1000.0},
    }


def test_invariance_harness_12_run_valid(tmp_path: Path) -> None:
    payload = _payload(tmp_path)
    result = run_invariance_harness(
        target="operator.run-simulation",
        runs=12,
        producer=lambda: dispatch_operator_command("run-simulation", payload),
    )
    assert result.status == "VALID"
    assert result.runs == 12
    assert result.mismatches == []


def test_lifecycle_policy_enforcement() -> None:
    lane = enforce_lane_policy(lane="SHADOW", influence_policy="DIRECT", influences_active_path=True)
    assert lane.status == "BROKEN"

    promo = evaluate_promotion_eligibility(
        module_id="simulation.core",
        current_lane="SHADOW",
        target_lane="ACTIVE",
        evidence={"contract_present": True, "tests_present": True},
    )
    assert promo.eligible is False
    assert "invariance_present" in promo.missing_evidence


def test_closure_summary_and_canon_checks(tmp_path: Path) -> None:
    payload = _payload(tmp_path)
    dispatch_operator_command("run-simulation", payload)

    closure = build_closure_summary(base_dir=tmp_path, run_id="RUN-GOV-001", scenario_id="SCN-GOV-001")
    assert closure.status == "VALID"
    assert closure.evidence["has_validation"] is True

    report = run_canon_checks(
        {
            **payload,
            "lane": "SHADOW",
            "influence_policy": "NONE",
            "influences_active_path": False,
            "module_id": "simulation.core",
            "current_lane": "CANARY",
            "target_lane": "ACTIVE",
            "promotion_evidence": {
                "contract_present": True,
                "tests_present": True,
                "invariance_present": True,
                "proof_present": True,
                "lineage_present": True,
            },
        }
    )
    assert report.ok is True
