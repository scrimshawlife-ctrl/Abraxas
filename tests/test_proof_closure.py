from __future__ import annotations

import json
from pathlib import Path

from abx.proof_closure import run_canonical_proof_closure


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_run_canonical_proof_closure_emits_linked_artifacts(tmp_path: Path) -> None:
    result = run_canonical_proof_closure(run_id="RUN-PROOF-0001", base_dir=tmp_path)

    rune_artifact = _read_json(Path(result.rune_artifact_path))
    validator_artifact = _read_json(Path(result.validator_artifact_path))
    operator_projection = _read_json(Path(result.operator_summary_path))
    attestation = _read_json(Path(result.attestation_path))

    assert rune_artifact["run_id"] == "RUN-PROOF-0001"
    assert rune_artifact["artifact_id"].startswith("art.")
    assert validator_artifact["runId"] == "RUN-PROOF-0001"
    assert validator_artifact["status"] == "VALID"
    assert len(validator_artifact["correlation"]["pointers"]) > 0
    assert operator_projection["proof_spine"]["validate"] == result.validator_artifact_path
    assert attestation["overall_status"] == "PASS"
    assert attestation["run_id"] == "RUN-PROOF-0001"


def test_run_canonical_proof_closure_is_deterministic_for_artifact_identity(tmp_path: Path) -> None:
    result_a = run_canonical_proof_closure(run_id="RUN-PROOF-DET", base_dir=tmp_path / "a")
    result_b = run_canonical_proof_closure(run_id="RUN-PROOF-DET", base_dir=tmp_path / "b")

    artifact_a = _read_json(Path(result_a.rune_artifact_path))
    artifact_b = _read_json(Path(result_b.rune_artifact_path))

    assert artifact_a["artifact_id"] == artifact_b["artifact_id"]
    assert artifact_a["inputs"] == artifact_b["inputs"]
    assert artifact_a["outputs"] == artifact_b["outputs"]
