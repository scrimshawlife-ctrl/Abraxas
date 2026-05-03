from __future__ import annotations

from pathlib import Path

from abraxas.registry.self_build_batch_trends import run_self_build_batch_trends


def test_batch_trends_required_fields() -> None:
    result = run_self_build_batch_trends()
    assert result["schema_version"] == "SelfBuildBatchTrends.v1"
    assert {"counts_by_status", "latest_status", "cycle_count", "approval_wait_ratio", "apply_success_ratio", "post_validation_pass_ratio", "score_feedback_hashes", "flagged_trends", "authority"}.issubset(result.keys())


def test_batch_trends_deterministic_hash_stability() -> None:
    a = run_self_build_batch_trends()
    b = run_self_build_batch_trends()
    assert a["canonical_hash"] == b["canonical_hash"]


def test_batch_trends_missing_ledger_fail_closed() -> None:
    ledger = Path("out/registry/self_build_batch_ledger.latest.json")
    backup = Path("out/registry/self_build_batch_ledger.latest.json.bak")
    if ledger.exists():
        backup.write_text(ledger.read_text(encoding="utf-8"), encoding="utf-8")
        ledger.unlink()
    try:
        result = run_self_build_batch_trends()
        assert result["status"] == "NOT_COMPUTABLE"
    finally:
        if backup.exists():
            ledger.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")
            backup.unlink()
