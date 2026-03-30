from __future__ import annotations

import json
from pathlib import Path

from scripts.run_large_run_convergence import build_large_run_convergence_bundle


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_large_run_convergence_bundle_success(tmp_path: Path) -> None:
    run_id = "RUN-CONV-OK"
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

    bundle = build_large_run_convergence_bundle(
        base_dir=tmp_path,
        batch_id="BATCH-CONV-001",
        timestamp="2026-03-30T00:00:00+00:00",
        min_pointers=1,
    )
    assert bundle["status"] == "SUCCESS"
    assert bundle["outputs"]["blocked_components"] == []


def test_large_run_convergence_bundle_blocked_when_barrier_blocked(tmp_path: Path) -> None:
    run_id = "RUN-CONV-BLOCK"
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
        {"run_id": run_id, "decision_state": "BLOCKED", "reason_codes": ["missing-proof"]},
    )

    bundle = build_large_run_convergence_bundle(
        base_dir=tmp_path,
        batch_id="BATCH-CONV-002",
        timestamp="2026-03-30T00:00:00+00:00",
        min_pointers=1,
    )
    assert bundle["status"] == "BLOCKED"
    assert "promotion_barrier" in bundle["outputs"]["blocked_components"]


def test_large_run_convergence_bundle_is_deterministic(tmp_path: Path) -> None:
    run_id = "RUN-CONV-DET"
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

    a = build_large_run_convergence_bundle(
        base_dir=tmp_path,
        batch_id="BATCH-CONV-003",
        timestamp="2026-03-30T00:00:00+00:00",
        min_pointers=1,
    )
    b = build_large_run_convergence_bundle(
        base_dir=tmp_path,
        batch_id="BATCH-CONV-003",
        timestamp="2026-03-30T00:00:00+00:00",
        min_pointers=1,
    )
    assert a == b
