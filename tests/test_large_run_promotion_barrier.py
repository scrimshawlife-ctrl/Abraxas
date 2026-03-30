from __future__ import annotations

import json
from pathlib import Path

from scripts.run_large_run_promotion_barrier import build_large_run_promotion_barrier


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_large_run_promotion_barrier_success_when_all_allowed(tmp_path: Path) -> None:
    _write(
        tmp_path / "out" / "policy" / "promotion-policy-RUN-1.json",
        {"run_id": "RUN-1", "decision_state": "ALLOWED", "reason_codes": []},
    )
    _write(
        tmp_path / "out" / "policy" / "promotion-policy-RUN-2.json",
        {"run_id": "RUN-2", "decision_state": "ALLOWED", "reason_codes": []},
    )

    artifact = build_large_run_promotion_barrier(
        base_dir=tmp_path,
        batch_id="BATCH-BAR-001",
        timestamp="2026-03-30T00:00:00+00:00",
    )

    assert artifact["status"] == "SUCCESS"
    assert artifact["outputs"]["run_count"] == 2
    assert artifact["outputs"]["allowed_count"] == 2
    assert artifact["outputs"]["blocked_count"] == 0


def test_large_run_promotion_barrier_blocks_when_any_run_blocked(tmp_path: Path) -> None:
    _write(
        tmp_path / "out" / "policy" / "promotion-policy-RUN-3.json",
        {"run_id": "RUN-3", "decision_state": "ALLOWED", "reason_codes": []},
    )
    _write(
        tmp_path / "out" / "policy" / "promotion-policy-RUN-4.json",
        {"run_id": "RUN-4", "decision_state": "BLOCKED", "reason_codes": ["missing-ledger-linkage"]},
    )

    artifact = build_large_run_promotion_barrier(
        base_dir=tmp_path,
        batch_id="BATCH-BAR-002",
        timestamp="2026-03-30T00:00:00+00:00",
    )

    assert artifact["status"] == "BLOCKED"
    assert artifact["outputs"]["run_count"] == 2
    assert artifact["outputs"]["blocked_count"] == 1
    row = next(item for item in artifact["outputs"]["runs"] if item["run_id"] == "RUN-4")
    assert row["barrier_status"] == "BLOCKED"
    assert "missing-ledger-linkage" in row["reason_codes"]


def test_large_run_promotion_barrier_is_deterministic(tmp_path: Path) -> None:
    _write(
        tmp_path / "out" / "policy" / "promotion-policy-RUN-5.json",
        {"run_id": "RUN-5", "decision_state": "NOT_COMPUTABLE", "reason_codes": ["missing-local-proof"]},
    )

    a = build_large_run_promotion_barrier(
        base_dir=tmp_path,
        batch_id="BATCH-BAR-003",
        timestamp="2026-03-30T00:00:00+00:00",
    )
    b = build_large_run_promotion_barrier(
        base_dir=tmp_path,
        batch_id="BATCH-BAR-003",
        timestamp="2026-03-30T00:00:00+00:00",
    )

    assert a == b
