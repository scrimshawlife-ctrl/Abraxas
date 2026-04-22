from __future__ import annotations

import json
from pathlib import Path

import abx.report_manifest_diff_ledger as ledger


def _diff_payload(diff_id: str = "DIFF-1") -> dict:
    return {
        "status": "OK",
        "reason": "ok",
        "diff": {
            "diff_id": diff_id,
            "timestamp_utc": "2026-04-21T00:00:00Z",
            "added": ["a"],
            "removed": ["b"],
            "hash_changed": ["comparison"],
            "freshness_changed": [],
            "status_changed": ["comparison"],
            "unchanged_count": 2,
            "provenance": {"status": "OK", "reason": "ok"},
        },
    }


def test_duplicate_prevention(tmp_path: Path) -> None:
    ledger_path = tmp_path / "ledger.jsonl"
    record = ledger.build_ledger_record(diff_payload=_diff_payload())
    assert ledger.append_diff_ledger(record, ledger_path=ledger_path) is True
    assert ledger.append_diff_ledger(record, ledger_path=ledger_path) is False


def test_deterministic_row_output() -> None:
    a = ledger.build_ledger_record(diff_payload=_diff_payload("DIFF-X"))
    b = ledger.build_ledger_record(diff_payload=_diff_payload("DIFF-X"))
    assert a == b


def test_missing_latest_diff_handling() -> None:
    record = ledger.build_ledger_record(diff_payload=None)
    assert record["status"] == "NOT_COMPUTABLE"
    assert record["diff_id"] == "NOT_COMPUTABLE"


def test_history_limit_behavior(tmp_path: Path) -> None:
    ledger_path = tmp_path / "ledger.jsonl"
    for idx in range(5):
        payload = _diff_payload(diff_id=f"DIFF-{idx}")
        payload["diff"]["added"] = [str(idx)]
        record = ledger.build_ledger_record(diff_payload=payload)
        ledger.append_diff_ledger(record, ledger_path=ledger_path)

    tail_two = ledger.read_diff_history(limit=2, ledger_path=ledger_path)
    assert tail_two["status"] == "OK"
    assert len(tail_two["history"]) == 2

    bounded_max = ledger.read_diff_history(limit=999, ledger_path=ledger_path)
    assert len(bounded_max["history"]) == 5

    missing = ledger.read_diff_history(limit=2, ledger_path=tmp_path / "missing.jsonl")
    assert missing["status"] == "NOT_COMPUTABLE"
    assert missing["history"] == []
