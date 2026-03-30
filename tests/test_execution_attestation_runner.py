from __future__ import annotations

import json
from pathlib import Path

from abx.promotion_policy import PromotionPolicyDecision, PromotionPolicyState
from scripts.run_execution_attestation import (
    StepResult,
    build_attestation_payload,
    compute_overall_status,
    policy_allows_tier3_execution,
)


def test_compute_overall_status_pass_without_seal():
    status, reasons = compute_overall_status(
        validator_status="VALID",
        acceptance_verdict="PASS",
        seal_ok=None,
        require_seal=False,
        policy_decision_state="ALLOWED",
    )
    assert status == "PASS"
    assert reasons == []


def test_compute_overall_status_fail_reasons():
    status, reasons = compute_overall_status(
        validator_status="ERROR",
        acceptance_verdict="FAIL",
        seal_ok=False,
        require_seal=True,
        policy_decision_state="BLOCKED",
    )
    assert status == "FAIL"
    assert "policy_decision_state=BLOCKED" in reasons
    assert "validator_status=ERROR" in reasons
    assert "acceptance_verdict=FAIL" in reasons
    assert "seal_ok=False" in reasons


def test_compute_overall_status_allows_waived_policy():
    status, reasons = compute_overall_status(
        validator_status="VALID",
        acceptance_verdict="PASS",
        seal_ok=None,
        require_seal=False,
        policy_decision_state="WAIVED",
    )
    assert status == "PASS"
    assert reasons == []


def test_compute_overall_status_fails_not_computable_policy():
    status, reasons = compute_overall_status(
        validator_status="VALID",
        acceptance_verdict="PASS",
        seal_ok=None,
        require_seal=False,
        policy_decision_state="NOT_COMPUTABLE",
    )
    assert status == "FAIL"
    assert "policy_decision_state=NOT_COMPUTABLE" in reasons


def test_policy_allows_tier3_execution_states():
    assert policy_allows_tier3_execution("ALLOWED") is True
    assert policy_allows_tier3_execution("WAIVED") is True
    assert policy_allows_tier3_execution("BLOCKED") is False
    assert policy_allows_tier3_execution("NOT_COMPUTABLE") is False


def test_build_attestation_payload_reads_artifacts(tmp_path: Path):
    validator = tmp_path / "execution-validation-RUN-1.json"
    acceptance_result = tmp_path / "acceptance_result.json"
    acceptance_status = tmp_path / "acceptance_status_v1.json"

    validator.write_text(json.dumps({"status": "VALID"}), encoding="utf-8")
    acceptance_result.write_text(json.dumps({"overall_verdict": "PASS"}), encoding="utf-8")
    acceptance_status.write_text(json.dumps({"overall": {"ok": True}}), encoding="utf-8")

    payload = build_attestation_payload(
        run_id="RUN-1",
        started_at="2026-03-27T00:00:00+00:00",
        finished_at="2026-03-27T00:00:01+00:00",
        step_results=[
            StepResult(name="execution_validator", command=["python"], returncode=0, ok=True),
            StepResult(name="acceptance_suite", command=["python"], returncode=0, ok=True),
        ],
        validator_artifact=validator,
        acceptance_result=acceptance_result,
        acceptance_status=acceptance_status,
        seal_report=None,
        require_seal=False,
        policy_decision=PromotionPolicyDecision(
            run_id="RUN-1",
            decision_state=PromotionPolicyState.ALLOWED,
            requires_federation=True,
            waived=False,
            checked_at="2026-03-27T00:00:00+00:00",
            reason_codes=["policy_requirements_satisfied"],
            blockers=[],
            readiness_status="PROMOTION_READY",
            local_promotion_state="LOCAL_PROMOTION_READY",
            federated_readiness_state="FEDERATED_READY",
            federated_evidence_summary={"remote_evidence_status": "UNKNOWN"},
            artifacts={},
            provenance={"checker": "test"},
        ),
        policy_artifact=tmp_path / "promotion-policy-RUN-1.json",
    )

    assert payload["overall_status"] == "PASS"
    assert payload["policy_gate"]["decision_state"] == "ALLOWED"
    assert payload["policy_gate"]["federated_evidence"]["remote_evidence_status"] == "UNKNOWN"
    assert payload["artifacts"]["validator"]["status"] == "VALID"
    assert payload["artifacts"]["acceptance_result"]["overall_verdict"] == "PASS"


def test_build_attestation_payload_carries_waiver_provenance(tmp_path: Path):
    validator = tmp_path / "execution-validation-RUN-W.json"
    acceptance_result = tmp_path / "acceptance_result.json"
    acceptance_status = tmp_path / "acceptance_status_v1.json"

    validator.write_text(json.dumps({"status": "VALID"}), encoding="utf-8")
    acceptance_result.write_text(json.dumps({"overall_verdict": "PASS"}), encoding="utf-8")
    acceptance_status.write_text(json.dumps({"overall": {"ok": True}}), encoding="utf-8")

    payload = build_attestation_payload(
        run_id="RUN-W",
        started_at="2026-03-27T00:00:00+00:00",
        finished_at="2026-03-27T00:00:01+00:00",
        step_results=[
            StepResult(name="execution_validator", command=["python"], returncode=0, ok=True),
            StepResult(name="acceptance_suite", command=["python"], returncode=0, ok=True),
        ],
        validator_artifact=validator,
        acceptance_result=acceptance_result,
        acceptance_status=acceptance_status,
        seal_report=None,
        require_seal=False,
        policy_decision=PromotionPolicyDecision(
            run_id="RUN-W",
            decision_state=PromotionPolicyState.WAIVED,
            requires_federation=True,
            waived=True,
            checked_at="2026-03-27T00:00:00+00:00",
            reason_codes=["documented_emergency_override"],
            blockers=["FEDERATED_INCOMPLETE"],
            readiness_status="PROMOTION_READY",
            local_promotion_state="LOCAL_PROMOTION_READY",
            federated_readiness_state="FEDERATED_INCOMPLETE",
            federated_evidence_summary={"remote_evidence_status": "UNKNOWN"},
            artifacts={},
            provenance={"checker": "test"},
        ),
        policy_artifact=tmp_path / "promotion-policy-RUN-W.json",
    )

    assert payload["overall_status"] == "PASS"
    assert payload["policy_gate"]["decision_state"] == "WAIVED"
    assert payload["policy_gate"]["waived"] is True
    assert payload["policy_gate"]["reason_codes"] == ["documented_emergency_override"]


def test_build_attestation_payload_fails_closed_when_policy_blocked(tmp_path: Path):
    payload = build_attestation_payload(
        run_id="RUN-B",
        started_at="2026-03-27T00:00:00+00:00",
        finished_at="2026-03-27T00:00:01+00:00",
        step_results=[],
        validator_artifact=tmp_path / "missing-validator.json",
        acceptance_result=tmp_path / "missing-acceptance.json",
        acceptance_status=tmp_path / "missing-acceptance-status.json",
        seal_report=None,
        require_seal=False,
        policy_decision=PromotionPolicyDecision(
            run_id="RUN-B",
            decision_state=PromotionPolicyState.BLOCKED,
            requires_federation=True,
            waived=False,
            checked_at="2026-03-27T00:00:00+00:00",
            reason_codes=["federated_readiness_required"],
            blockers=["FEDERATED_INCOMPLETE"],
            readiness_status="PROMOTION_READY",
            local_promotion_state="LOCAL_PROMOTION_READY",
            federated_readiness_state="FEDERATED_INCOMPLETE",
            federated_evidence_summary={"remote_evidence_status": "UNKNOWN"},
            artifacts={},
            provenance={"checker": "test"},
        ),
        policy_artifact=tmp_path / "promotion-policy-RUN-B.json",
    )

    assert payload["overall_status"] == "FAIL"
    assert payload["steps"] == []
    assert "policy_decision_state=BLOCKED" in payload["fail_reasons"]
    assert payload["policy_gate"]["federated_evidence"]["remote_evidence_status"] == "UNKNOWN"
