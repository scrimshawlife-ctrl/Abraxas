from __future__ import annotations

import json
from pathlib import Path

from scripts.run_large_run_convergence import build_large_run_convergence_bundle
from scripts.run_large_run_coverage_audit import build_large_run_coverage_artifact
from scripts.run_large_run_pointer_sufficiency import build_pointer_sufficiency_report
from scripts.run_large_run_promotion_barrier import build_large_run_promotion_barrier
from scripts.run_large_run_rune_run_index import build_rune_run_index


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _required_fields() -> list[str]:
    schema_path = Path("aal_core/schemas/large_run_execution_artifact.v1.json")
    payload = json.loads(schema_path.read_text(encoding="utf-8"))
    return [str(item) for item in payload.get("required", [])]


def test_large_run_artifacts_emit_required_envelope_fields(tmp_path: Path) -> None:
    run_id = "RUN-CONTRACT-001"
    _write(
        tmp_path / "out" / "validators" / f"execution-validation-{run_id}.json",
        {
            "runId": run_id,
            "status": "VALID",
            "artifactId": f"execution-validation-{run_id}",
            "correlation": {"pointers": ["ptr.1"]},
            "runeContext": {"runeIds": ["RUNE.DIFF"], "phases": ["AUDIT"]},
        },
    )
    _write(
        tmp_path / "out" / "operator" / f"operator-projection-{run_id}.json",
        {"run_id": run_id, "proof_closure_status": "COMPLETE"},
    )
    _write(
        tmp_path / "out" / "policy" / f"promotion-policy-{run_id}.json",
        {"run_id": run_id, "decision_state": "ALLOWED", "reason_codes": []},
    )

    timestamp = "2026-03-30T00:00:00+00:00"
    coverage, _ = build_large_run_coverage_artifact(base_dir=tmp_path, batch_id="BATCH-CONTRACT", timestamp=timestamp)
    pointer = build_pointer_sufficiency_report(
        base_dir=tmp_path,
        batch_id="BATCH-CONTRACT",
        timestamp=timestamp,
        min_pointers=1,
    )
    rune_index = build_rune_run_index(base_dir=tmp_path, batch_id="BATCH-CONTRACT", timestamp=timestamp)
    barrier = build_large_run_promotion_barrier(base_dir=tmp_path, batch_id="BATCH-CONTRACT", timestamp=timestamp)
    bundle = build_large_run_convergence_bundle(
        base_dir=tmp_path,
        batch_id="BATCH-CONTRACT",
        timestamp=timestamp,
        min_pointers=1,
    )

    required = _required_fields()
    for artifact in (coverage, pointer, rune_index, barrier, bundle):
        for field in required:
            assert field in artifact, f"missing required envelope field: {field}"
        assert isinstance(artifact["correlation_pointers"], list)
