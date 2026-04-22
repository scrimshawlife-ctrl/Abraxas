from __future__ import annotations

import json
from pathlib import Path

from abx.readiness_comparison import append_comparison_ledger, build_readiness_comparison_record


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")


def _developer_payload(status: str = "PASS") -> dict:
    return {
        "status": status,
        "reason": "ok",
        "projection": {
            "run_id": "DEV-1",
            "checks": [{"status": "PASS"}, {"status": "PASS"}],
            "missing_surfaces": [],
            "status": status,
            "timestamp_utc": "2026-04-21T00:00:00Z",
            "recommended_next_actions": [],
            "provenance": {},
        },
    }


def _gap_payload(readiness_state: str = "partial", decision: str = "HOLD", status: str = "PASS") -> dict:
    return {
        "status": status,
        "reason": "ok",
        "projection": {
            "run_id": "RUN-GAP-1",
            "readiness_state": readiness_state,
            "promotion_decision": decision,
            "invariance_counts": {"total": 5, "stable": 2, "provisional": 2, "unchecked": 1},
            "unmet_conditions": ["x"],
            "required_thresholds": {},
            "provenance": {},
        },
    }


def test_schema_and_deterministic_comparison_id(monkeypatch) -> None:
    monkeypatch.setattr("abx.readiness_comparison.read_developer_readiness_payload", lambda: _developer_payload("PASS"))
    monkeypatch.setattr("abx.readiness_comparison.read_gap_closure_invariance_payload", lambda: _gap_payload("READY", "PASS", "PASS"))
    first = build_readiness_comparison_record(timestamp_utc="2026-04-21T00:00:00Z")
    second = build_readiness_comparison_record(timestamp_utc="2026-04-21T00:00:00Z")
    assert first == second


def test_missing_developer_readiness_is_not_computable(monkeypatch) -> None:
    monkeypatch.setattr("abx.readiness_comparison.read_developer_readiness_payload", lambda: {"status": "NOT_COMPUTABLE", "reason": "report_missing:dev", "projection": {"run_id": "NOT_COMPUTABLE"}})
    monkeypatch.setattr("abx.readiness_comparison.read_gap_closure_invariance_payload", lambda: _gap_payload())
    record = build_readiness_comparison_record(timestamp_utc="2026-04-21T00:00:00Z")
    assert record["alignment"]["state"] == "NOT_COMPUTABLE"


def test_missing_gap_is_not_computable(monkeypatch) -> None:
    monkeypatch.setattr("abx.readiness_comparison.read_developer_readiness_payload", lambda: _developer_payload("PASS"))
    monkeypatch.setattr("abx.readiness_comparison.read_gap_closure_invariance_payload", lambda: {"status": "NOT_COMPUTABLE", "reason": "report_missing:gap", "projection": {"run_id": "NOT_COMPUTABLE"}})
    record = build_readiness_comparison_record(timestamp_utc="2026-04-21T00:00:00Z")
    assert record["alignment"]["state"] == "NOT_COMPUTABLE"


def test_duplicate_ledger_append_prevented(tmp_path: Path) -> None:
    record = {
        "comparison_id": "abc",
        "timestamp_utc": "2026-04-21T00:00:00Z",
        "developer_readiness": {"status": "PASS", "run_id": "D", "checks_total": 1, "checks_passed": 1, "missing_surfaces_count": 0},
        "gap_closure_invariance": {"status": "PASS", "run_id": "G", "readiness_state": "READY", "promotion_decision": "PASS", "invariance_total": 1, "invariance_stable": 1, "unmet_conditions_count": 0},
        "alignment": {"state": "ALIGNED", "reason": "ok"},
        "provenance": {"source": "t", "deterministic_ordering": []},
    }
    ledger = tmp_path / "ledger.jsonl"
    latest = tmp_path / "latest.json"
    first = append_comparison_ledger(record, ledger_path=ledger, latest_path=latest)
    second = append_comparison_ledger(record, ledger_path=ledger, latest_path=latest)
    assert first is True
    assert second is False
    assert len([line for line in ledger.read_text(encoding="utf-8").splitlines() if line.strip()]) == 1


def test_alignment_state_classifications(monkeypatch) -> None:
    monkeypatch.setattr("abx.readiness_comparison.read_developer_readiness_payload", lambda: _developer_payload("PASS"))
    monkeypatch.setattr("abx.readiness_comparison.read_gap_closure_invariance_payload", lambda: _gap_payload("partial", "HOLD", "PASS"))
    hold_record = build_readiness_comparison_record(timestamp_utc="2026-04-21T00:00:00Z")
    assert hold_record["alignment"]["state"] == "DEV_READY_GAP_HOLD"

    monkeypatch.setattr("abx.readiness_comparison.read_gap_closure_invariance_payload", lambda: _gap_payload("READY", "PASS", "PASS"))
    aligned_record = build_readiness_comparison_record(timestamp_utc="2026-04-21T00:00:00Z")
    assert aligned_record["alignment"]["state"] == "ALIGNED"

    monkeypatch.setattr("abx.readiness_comparison.read_developer_readiness_payload", lambda: _developer_payload("PARTIAL"))
    monkeypatch.setattr("abx.readiness_comparison.read_gap_closure_invariance_payload", lambda: _gap_payload("partial", "HOLD", "PARTIAL"))
    partial_record = build_readiness_comparison_record(timestamp_utc="2026-04-21T00:00:00Z")
    assert partial_record["alignment"]["state"] == "BOTH_PARTIAL"
