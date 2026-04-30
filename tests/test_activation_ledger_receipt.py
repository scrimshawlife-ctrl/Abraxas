from __future__ import annotations

import json
from pathlib import Path

from abraxas.governance.activation_ledger import REQUIRED_ARTIFACTS, build_activation_ledger_receipt


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _seed(repo: Path) -> None:
    _write(repo / "out/reports/abx_readiness_gate.latest.json", {"status": "READY"})
    _write(repo / "out/reports/pse_calibration_candidate_cycle.latest.json", {"status": "CANDIDATE_CYCLE_COMPLETE"})
    _write(repo / "out/reports/pse_calibration_candidate_proposal.latest.json", {"status": "PROPOSAL_ONLY"})
    _write(repo / "out/reports/pse_calibration_candidate_approval_gate.latest.json", {"status": "APPROVED_FOR_APPLICATION"})
    _write(repo / "out/reports/pse_calibration_candidate_application.latest.json", {"status": "APPLIED"})
    _write(repo / "out/state/pse_calibration_candidate_state.latest.json", {"status": "ACTIVE_GENERATED_STATE"})
    _write(repo / "out/reports/pse_calibration_candidate_preview.latest.json", {"status": "PREVIEW_ONLY"})
    _write(
        repo / "out/reports/pse_calibration_activation_review.latest.json",
        {"status": "ACTIVATION_REVIEW_PASSED", "decision": "ELIGIBLE_FOR_ACTIVATION"},
    )
    _write(repo / "out/reports/pse_calibration_runtime_wiring.latest.json", {"status": "RUNTIME_WIRING_ENABLED"})
    _write(
        repo / "out/state/pse_calibration_runtime_wiring.latest.json",
        {"status": "RUNTIME_WIRING_ENABLED", "calibration": {"global_confidence_multiplier": 0.9}},
    )
    _write(
        repo / "out/reports/pse_calibration_post_activation_validation.latest.json",
        {
            "status": "POST_ACTIVATION_VALIDATED",
            "baseline": 0.1975,
            "activated": 0.196975,
            "delta": -0.000525,
            "runtime_wiring_status": "ENABLED_VALIDATED",
            "rollback_recommendation": "NONE",
            "source_logic_modified": False,
        },
    )


def test_sealed_receipt_and_hashes(tmp_path: Path) -> None:
    _seed(tmp_path)
    first = build_activation_ledger_receipt(tmp_path)
    second = build_activation_ledger_receipt(tmp_path)
    assert first == second
    assert first["status"] == "RECEIPT_SEALED"
    assert first["promotion"]["eligible"] is True
    assert first["promotion"]["promoted"] is False
    assert len(first["artifacts"]["hashes"]) == len(REQUIRED_ARTIFACTS)


def test_failure_when_mismatch_or_missing(tmp_path: Path) -> None:
    _seed(tmp_path)
    broken = tmp_path / "out/reports/pse_calibration_post_activation_validation.latest.json"
    payload = json.loads(broken.read_text())
    payload["rollback_recommendation"] = "ROLLBACK_RECOMMENDED"
    _write(broken, payload)
    failed = build_activation_ledger_receipt(tmp_path)
    assert failed["status"] == "RECEIPT_BLOCKED"
    assert failed["promotion"]["eligible"] is False

    (tmp_path / REQUIRED_ARTIFACTS[0]).unlink()
    missing = build_activation_ledger_receipt(tmp_path)
    assert missing["status"] == "RECEIPT_BLOCKED"
    assert REQUIRED_ARTIFACTS[0] in missing["artifacts"]["missing"]
