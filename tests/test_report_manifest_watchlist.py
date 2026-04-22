from __future__ import annotations

import json
from pathlib import Path

import jsonschema

import abx.report_manifest_watchlist as watchlist_mod


def _history_row(ts: str, events: list[dict]) -> dict:
    return {
        "timestamp_utc": ts,
        "artifact_events": events,
        "added_count": 0,
        "removed_count": 0,
        "hash_changed_count": 0,
        "freshness_changed_count": 0,
        "status_changed_count": 0,
        "status": "OK",
    }


def test_pattern_detection_thresholds(monkeypatch) -> None:
    history = [
        _history_row(
            "2026-04-21T00:00:00Z",
            [
                {"artifact_type": "comparison", "hash_changed_count": 1, "freshness_changed_count": 1, "status_changed_count": 0, "removed_count": 0},
                {"artifact_type": "invariance", "hash_changed_count": 0, "freshness_changed_count": 0, "status_changed_count": 1, "removed_count": 1},
            ],
        ),
        _history_row(
            "2026-04-21T00:05:00Z",
            [
                {"artifact_type": "comparison", "hash_changed_count": 1, "freshness_changed_count": 1, "status_changed_count": 0, "removed_count": 0},
                {"artifact_type": "invariance", "hash_changed_count": 0, "freshness_changed_count": 0, "status_changed_count": 1, "removed_count": 1},
            ],
        ),
    ]
    monkeypatch.setattr(watchlist_mod, "read_diff_history", lambda limit=20: {"status": "OK", "reason": "ok", "history": history})
    payload = watchlist_mod.build_report_manifest_watchlist(window_size=20, timestamp_utc="2026-04-21T00:10:00Z")
    items = payload["watchlist"]["items"]

    assert payload["status"] == "OK"
    assert any(item["artifact_type"] == "comparison" and item["issue_type"] == "REPEATED_HASH_CHURN" for item in items)
    assert any(item["artifact_type"] == "comparison" and item["issue_type"] == "FREQUENT_STALE_TRANSITION" for item in items)
    assert any(item["artifact_type"] == "invariance" and item["issue_type"] == "UNSTABLE_STATUS" for item in items)
    assert any(item["artifact_type"] == "invariance" and item["issue_type"] == "REPEATED_DISAPPEARANCE" for item in items)


def test_grouping_and_not_computable(monkeypatch) -> None:
    monkeypatch.setattr(watchlist_mod, "read_diff_history", lambda limit=20: {"status": "NOT_COMPUTABLE", "reason": "report_missing:x", "history": []})
    payload = watchlist_mod.build_report_manifest_watchlist(window_size=20, timestamp_utc="2026-04-21T00:10:00Z")
    assert payload["status"] == "NOT_COMPUTABLE"
    assert payload["watchlist"]["items"] == []


def test_deterministic_output(monkeypatch) -> None:
    history = [_history_row("2026-04-21T00:00:00Z", [{"artifact_type": "comparison", "hash_changed_count": 2, "freshness_changed_count": 0, "status_changed_count": 0, "removed_count": 0}])]
    monkeypatch.setattr(watchlist_mod, "read_diff_history", lambda limit=20: {"status": "OK", "reason": "ok", "history": history})
    a = watchlist_mod.build_report_manifest_watchlist(window_size=20, timestamp_utc="2026-04-21T00:10:00Z")
    b = watchlist_mod.build_report_manifest_watchlist(window_size=20, timestamp_utc="2026-04-21T00:10:00Z")
    assert a == b


def test_schema_validation(monkeypatch) -> None:
    history = [_history_row("2026-04-21T00:00:00Z", [{"artifact_type": "comparison", "hash_changed_count": 2, "freshness_changed_count": 0, "status_changed_count": 0, "removed_count": 0}])]
    monkeypatch.setattr(watchlist_mod, "read_diff_history", lambda limit=20: {"status": "OK", "reason": "ok", "history": history})
    payload = watchlist_mod.build_report_manifest_watchlist(window_size=20, timestamp_utc="2026-04-21T00:10:00Z")
    schema = json.loads(Path("schemas/ReportManifestWatchlist.v1.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(payload["watchlist"])
