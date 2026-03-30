from __future__ import annotations

from scripts.large_run_contracts import validate_large_run_envelope


def test_large_run_contract_flags_missing_fields() -> None:
    issues = validate_large_run_envelope({"schema": "X"})
    assert "missing:run_id" in issues
    assert "missing:rune_id" in issues
    assert "missing:correlation_pointers" in issues


def test_large_run_contract_accepts_minimal_valid_shape() -> None:
    payload = {
        "schema": "LargeRunCoverageAudit.v1",
        "run_id": "BATCH::TEST",
        "rune_id": "RUNE.DIFF",
        "artifact_id": "artifact-1",
        "timestamp": "2026-03-30T00:00:00+00:00",
        "phase": "AUDIT",
        "status": "SUCCESS",
        "batch_id": "TEST",
        "inputs": {},
        "outputs": {},
        "provenance": {"builder": "test"},
        "correlation_pointers": [],
    }
    assert validate_large_run_envelope(payload) == []
