from __future__ import annotations

import json
from pathlib import Path

from abx.operator_views import build_run_summary


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_build_run_summary_contains_core_panels(tmp_path: Path) -> None:
    run_id = "RUN-CONSOLE-1"
    _write(tmp_path / "out" / "validators" / f"execution-validation-{run_id}.json", {"status": "VALID", "artifactId": "ev-1"})
    _write(tmp_path / "out" / "attestation" / f"canonical_proof_{run_id}.json", {"overall_status": "PASS"})
    _write(
        tmp_path / "out" / "attestation" / f"execution-attestation-{run_id}.json",
        {
            "overall_status": "FAIL",
            "fail_reasons": ["policy_decision_state=BLOCKED"],
            "policy_gate": {"decision_state": "BLOCKED"},
            "federated": {"federated_evidence_state": "PARTIAL", "remote_evidence_status": "MISSING"},
        },
    )
    _write(tmp_path / "out" / "policy" / f"promotion-policy-{run_id}.json", {"decision_state": "BLOCKED", "blockers": ["FEDERATED_INCOMPLETE"]})
    _write(
        tmp_path / "out" / "promotion" / f"promotion-readiness-{run_id}.json",
        {"status": "PROMOTION_READY", "local_promotion_state": "LOCAL_PROMOTION_READY", "federated_readiness_state": "FEDERATED_INCOMPLETE"},
    )

    summary = build_run_summary(run_id, base_dir=tmp_path)

    assert summary.run_id == run_id
    assert summary.policy_state == "BLOCKED"
    assert "policy_decision_state=BLOCKED" in summary.blockers
    assert summary.execution_status["overall_status"] == "FAIL"
    assert summary.projection_summary["schema"] == "OperatorProjectionSummary.v1"
