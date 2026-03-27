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


def test_validate_run_matches_camel_case_run_id_and_linked_paths(tmp_path: Path) -> None:
    ledger_dir = tmp_path / "out" / "ledger"
    ledger_dir.mkdir(parents=True, exist_ok=True)
    (ledger_dir / "task_outcomes.jsonl").write_text(
        json.dumps(
            {
                "runId": "RUN-CAMEL-0001",
                "event_id": "event-camel",
                "refs": {"result": "artifacts_seal/results/seal/000000.resultspack.json"},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = validate_run("RUN-CAMEL-0001", base_dir=tmp_path, checked_at="2026-03-27T00:00:00+00:00")
    assert result.status == ExecutionValidationStatus.PASS
    assert "event-camel" in result.ledger_record_ids
    assert "000000.resultspack.json" in result.ledger_artifact_ids


def test_validate_run_collects_artifacts_from_runindex_refs(tmp_path: Path) -> None:
    runindex_dir = tmp_path / "artifacts_seal" / "run_index" / "RUN-INDEX-0001"
    runindex_dir.mkdir(parents=True, exist_ok=True)
    runindex = {
        "run_id": "RUN-INDEX-0001",
        "refs": {
            "results_pack": "artifacts_seal/results/seal/000000.resultspack.json",
            "run_header": "artifacts_seal/runs/seal.runheader.json",
            "trendpack": "artifacts_seal/viz/seal/000000.trendpack.json",
        },
    }
    (runindex_dir / "000000.runindex.json").write_text(
        json.dumps(runindex),
        encoding="utf-8",
    )

    ledger_dir = tmp_path / "out" / "ledger"
    ledger_dir.mkdir(parents=True, exist_ok=True)
    (ledger_dir / "oracle_runs.jsonl").write_text(
        json.dumps({"run_id": "RUN-INDEX-0001", "event_id": "event-idx"}) + "\n",
        encoding="utf-8",
    )

    result = validate_run("RUN-INDEX-0001", base_dir=tmp_path, checked_at="2026-03-27T00:00:00+00:00")
    assert result.status == ExecutionValidationStatus.PASS
    assert "000000.resultspack.json" in result.ledger_artifact_ids
    assert "000000.trendpack.json" in result.ledger_artifact_ids
    assert "seal.runheader.json" in result.ledger_artifact_ids
