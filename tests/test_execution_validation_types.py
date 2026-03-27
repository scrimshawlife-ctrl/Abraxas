from __future__ import annotations

from abx.execution_validation_types import ExecutionValidationResult, ExecutionValidationStatus


def test_execution_validation_status_values() -> None:
    assert ExecutionValidationStatus.PASS.value == "pass"
    assert ExecutionValidationStatus.FAIL.value == "fail"
    assert ExecutionValidationStatus.INCOMPLETE.value == "incomplete"
    assert ExecutionValidationStatus.NOT_COMPUTABLE.value == "not_computable"


def test_execution_validation_result_to_dict_shape() -> None:
    result = ExecutionValidationResult(
        run_id="RUN-PROOF-0001",
        artifact_id="execution-validation-RUN-PROOF-0001",
        status=ExecutionValidationStatus.PASS,
        valid=True,
        errors=[],
        warnings=[],
        ledger_record_ids=["record-1"],
        ledger_artifact_ids=["artifact-1"],
        correlation_pointers=["out/ledger/example.jsonl:1"],
        checked_at="2026-03-27T00:00:00+00:00",
        provenance={"validator": "abx.execution_validator", "version": "mvp.v1"},
    )

    payload = result.to_dict()

    assert payload["status"] == "pass"
    assert payload["run_id"] == "RUN-PROOF-0001"
    assert payload["valid"] is True
    assert sorted(payload.keys()) == [
        "artifact_id",
        "checked_at",
        "correlation_pointers",
        "errors",
        "ledger_artifact_ids",
        "ledger_record_ids",
        "provenance",
        "run_id",
        "status",
        "valid",
        "warnings",
    ]
