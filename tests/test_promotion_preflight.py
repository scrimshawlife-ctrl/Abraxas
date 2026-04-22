from __future__ import annotations

from abx.promotion_preflight import build_promotion_preflight_advisory


def _comparison_payload(dev_status: str = "PASS", readiness_state: str = "READY", decision: str = "PASS", missing_count: int = 0):
    return {
        "status": "OK",
        "reason": "ok",
        "comparison": {
            "developer_readiness": {
                "status": dev_status,
                "run_id": "DEV-1",
                "checks_total": 3,
                "checks_passed": 3,
                "missing_surfaces_count": missing_count,
            },
            "gap_closure_invariance": {
                "status": "PASS",
                "run_id": "GAP-1",
                "readiness_state": readiness_state,
                "promotion_decision": decision,
                "invariance_total": 3,
                "invariance_stable": 3,
                "unmet_conditions_count": 0,
            },
        },
    }


def _invariance_payload(unmet: list[str] | None = None):
    return {
        "status": "PASS",
        "reason": "ok",
        "projection": {
            "run_id": "GAP-1",
            "readiness_state": "READY",
            "promotion_decision": "PASS",
            "unmet_conditions": list(unmet or []),
        },
    }


def test_schema_and_deterministic_output(monkeypatch) -> None:
    monkeypatch.setattr("abx.promotion_preflight.read_latest_comparison", lambda: _comparison_payload())
    monkeypatch.setattr("abx.promotion_preflight.read_gap_closure_invariance_payload", lambda: _invariance_payload())
    a = build_promotion_preflight_advisory(timestamp_utc="2026-04-21T00:00:00Z")
    b = build_promotion_preflight_advisory(timestamp_utc="2026-04-21T00:00:00Z")
    assert a == b


def test_missing_input_not_computable(monkeypatch) -> None:
    monkeypatch.setattr("abx.promotion_preflight.read_latest_comparison", lambda: {"status": "NOT_COMPUTABLE", "reason": "report_missing:comparison", "comparison": None})
    monkeypatch.setattr("abx.promotion_preflight.read_gap_closure_invariance_payload", lambda: _invariance_payload())
    advisory = build_promotion_preflight_advisory(timestamp_utc="2026-04-21T00:00:00Z")
    assert advisory["advisory_state"] == "NOT_COMPUTABLE"


def test_advisory_state_classifications(monkeypatch) -> None:
    monkeypatch.setattr("abx.promotion_preflight.read_latest_comparison", lambda: _comparison_payload("PASS", "READY", "PASS", 0))
    monkeypatch.setattr("abx.promotion_preflight.read_gap_closure_invariance_payload", lambda: _invariance_payload([]))
    ready = build_promotion_preflight_advisory(timestamp_utc="2026-04-21T00:00:00Z")
    assert ready["advisory_state"] == "READY_CANDIDATE"

    monkeypatch.setattr("abx.promotion_preflight.read_latest_comparison", lambda: _comparison_payload("PASS", "partial", "HOLD", 0))
    monkeypatch.setattr("abx.promotion_preflight.read_gap_closure_invariance_payload", lambda: _invariance_payload(["invariance_threshold_not_met"]))
    blocked_inv = build_promotion_preflight_advisory(timestamp_utc="2026-04-21T00:00:00Z")
    assert blocked_inv["advisory_state"] == "BLOCKED_INVARIANCE"

    monkeypatch.setattr("abx.promotion_preflight.read_latest_comparison", lambda: _comparison_payload("PARTIAL", "READY", "PASS", 2))
    monkeypatch.setattr("abx.promotion_preflight.read_gap_closure_invariance_payload", lambda: _invariance_payload([]))
    blocked_readiness = build_promotion_preflight_advisory(timestamp_utc="2026-04-21T00:00:00Z")
    assert blocked_readiness["advisory_state"] == "BLOCKED_READINESS"

    monkeypatch.setattr("abx.promotion_preflight.read_latest_comparison", lambda: _comparison_payload("PARTIAL", "partial", "HOLD", 2))
    monkeypatch.setattr("abx.promotion_preflight.read_gap_closure_invariance_payload", lambda: _invariance_payload(["invariance_threshold_not_met"]))
    blocked_both = build_promotion_preflight_advisory(timestamp_utc="2026-04-21T00:00:00Z")
    assert blocked_both["advisory_state"] == "BLOCKED_BOTH"
