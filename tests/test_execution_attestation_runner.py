from __future__ import annotations

import json
from pathlib import Path

from scripts.run_execution_attestation import build_attestation_payload, compute_overall_status, StepResult


def test_compute_overall_status_pass_without_seal():
    status, reasons = compute_overall_status(
        validator_status="VALID",
        acceptance_verdict="PASS",
        seal_ok=None,
        require_seal=False,
    )
    assert status == "PASS"
    assert reasons == []


def test_compute_overall_status_fail_reasons():
    status, reasons = compute_overall_status(
        validator_status="ERROR",
        acceptance_verdict="FAIL",
        seal_ok=False,
        require_seal=True,
    )
    assert status == "FAIL"
    assert "validator_status=ERROR" in reasons
    assert "acceptance_verdict=FAIL" in reasons
    assert "seal_ok=False" in reasons


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
    )

    assert payload["overall_status"] == "PASS"
    assert payload["artifacts"]["validator"]["status"] == "VALID"
    assert payload["artifacts"]["acceptance_result"]["overall_verdict"] == "PASS"

