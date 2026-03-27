from __future__ import annotations

import json
from pathlib import Path

from abx.execution_validation_types import ExecutionValidationStatus
from abx.execution_validator import emit_validation_result, to_canon_artifact, validate_run


def test_validate_run_not_computable_when_no_evidence(tmp_path: Path) -> None:
    result = validate_run("RUN-NONE-0001", base_dir=tmp_path, checked_at="2026-03-27T00:00:00+00:00")

    assert result.status == ExecutionValidationStatus.NOT_COMPUTABLE
    assert result.valid is False
    assert result.ledger_record_ids == []
    assert result.ledger_artifact_ids == []


def test_validate_run_incomplete_when_partial_chain_present(tmp_path: Path) -> None:
    ledger_dir = tmp_path / "out" / "ledger"
    ledger_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = ledger_dir / "oracle_runs.jsonl"
    ledger_path.write_text(
        json.dumps({"run_id": "RUN-PARTIAL-0001", "event_id": "event-1"}) + "\n",
        encoding="utf-8",
    )

    result = validate_run(
        "RUN-PARTIAL-0001",
        base_dir=tmp_path,
        checked_at="2026-03-27T00:00:00+00:00",
    )

    assert result.status == ExecutionValidationStatus.INCOMPLETE
    assert result.valid is False
    assert result.ledger_record_ids == ["event-1"]
    assert result.ledger_artifact_ids == []


def test_emit_validation_result_writes_expected_canon_shape(tmp_path: Path) -> None:
    reports_dir = tmp_path / "out" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    artifact = reports_dir / "mwr_RUN-PASS-0001.json"
    artifact.write_text("{}\n", encoding="utf-8")

    result = validate_run(
        "RUN-PASS-0001",
        base_dir=tmp_path,
        checked_at="2026-03-27T00:00:00+00:00",
    )
    out_path = emit_validation_result(result, tmp_path / "out" / "validators")

    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["artifactType"] == "ExecutionValidationArtifact.v1"
    assert payload["artifactId"] == "execution-validation-RUN-PASS-0001"
    assert payload["runId"] == "RUN-PASS-0001"
    assert payload["validatorId"] == "abx.execution_validator"
    assert payload["status"] == "ERROR"
    assert payload["validatedArtifacts"] == ["mwr_RUN-PASS-0001.json"]
    assert payload["correlation"]["ledgerIds"] == []
    assert payload["correlation"]["packetIds"] == []
    assert isinstance(payload["correlation"]["pointers"], list)


def test_canon_status_mapping_matches_contract(tmp_path: Path) -> None:
    checked_at = "2026-03-27T00:00:00+00:00"

    no_evidence = validate_run("RUN-NC-0001", base_dir=tmp_path, checked_at=checked_at)
    assert to_canon_artifact(no_evidence)["status"] == "ERROR"

    ledger_dir = tmp_path / "out" / "ledger"
    reports_dir = tmp_path / "out" / "reports"
    ledger_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    (ledger_dir / "oracle_runs.jsonl").write_text(
        json.dumps({"run_id": "RUN-DET-0001", "event_id": "event-det"}) + "\n",
        encoding="utf-8",
    )
    (reports_dir / "mwr_RUN-DET-0001.json").write_text("{}\n", encoding="utf-8")

    passed = validate_run("RUN-DET-0001", base_dir=tmp_path, checked_at=checked_at)
    assert passed.status == ExecutionValidationStatus.PASS
    assert to_canon_artifact(passed)["status"] == "VALID"


def test_validate_run_supports_run_alias_and_real_packet_ids(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifacts_seal" / "runs"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifact_dir / "seal.runheader.json"
    artifact_path.write_text(
        json.dumps(
            {
                "run_id": "seal",
                "proof_id": "proof-seal-001",
                "admission_id": "admission-seal-001",
                "packet_id": "packet-seal-001",
            }
        ),
        encoding="utf-8",
    )

    result = validate_run("RUN-SEAL-0001", base_dir=tmp_path, checked_at="2026-03-27T00:00:00+00:00")
    canon = to_canon_artifact(result)

    assert result.status == ExecutionValidationStatus.INCOMPLETE
    assert "seal.runheader.json" in result.ledger_artifact_ids
    assert "proof-seal-001" in result.ledger_artifact_ids
    assert "admission-seal-001" in result.ledger_artifact_ids
    assert canon["correlation"]["packetIds"] == ["packet-seal-001"]


def test_validate_run_does_not_broad_match_unobserved_alias_stems(tmp_path: Path) -> None:
    proof_dir = tmp_path / "out" / "proof_bundles" / "PROOF"
    proof_dir.mkdir(parents=True, exist_ok=True)
    (proof_dir / "manifest.json").write_text(
        json.dumps({"run_id": "seal", "proof_id": "proof-only-for-seal"}),
        encoding="utf-8",
    )

    result = validate_run("RUN-PROOF-0001", base_dir=tmp_path, checked_at="2026-03-27T00:00:00+00:00")
    canon = to_canon_artifact(result)

    assert result.status == ExecutionValidationStatus.NOT_COMPUTABLE
    assert result.ledger_artifact_ids == []
    assert canon["correlation"]["packetIds"] == []


def test_validate_run_matches_nested_ctx_run_id_in_ledger(tmp_path: Path) -> None:
    ledger_dir = tmp_path / ".aal" / "ledger"
    ledger_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = ledger_dir / "rune_invocations.jsonl"
    ledger_path.write_text(
        json.dumps(
            {
                "ctx": {"run_id": "RUN-SEAL-0001"},
                "ledger_sha256": "abc123",
                "outputs": {"packet_id": "packet-ctx-001"},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = validate_run("RUN-SEAL-0001", base_dir=tmp_path, checked_at="2026-03-27T00:00:00+00:00")
    canon = to_canon_artifact(result)

    assert result.ledger_record_ids == ["abc123"]
    assert canon["correlation"]["packetIds"] == ["packet-ctx-001"]


def test_validate_run_is_deterministic_for_same_inputs(tmp_path: Path) -> None:
    ledger_dir = tmp_path / "out" / "ledger"
    reports_dir = tmp_path / "out" / "reports"
    ledger_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    (ledger_dir / "oracle_runs.jsonl").write_text(
        json.dumps({"run_id": "RUN-DET-0001", "event_id": "event-det"}) + "\n",
        encoding="utf-8",
    )
    (reports_dir / "mwr_RUN-DET-0001.json").write_text("{}\n", encoding="utf-8")

    checked_at = "2026-03-27T00:00:00+00:00"
    result_a = validate_run("RUN-DET-0001", base_dir=tmp_path, checked_at=checked_at)
    result_b = validate_run("RUN-DET-0001", base_dir=tmp_path, checked_at=checked_at)

    assert result_a.to_dict() == result_b.to_dict()
    assert result_a.status == ExecutionValidationStatus.PASS
    assert result_a.valid is True
