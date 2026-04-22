from __future__ import annotations

import json
from pathlib import Path

import jsonschema

import abx.report_manifest_summary as summary_mod


def _history_row(**overrides):
    row = {
        "added_count": 1,
        "removed_count": 0,
        "hash_changed_count": 1,
        "freshness_changed_count": 0,
        "status_changed_count": 0,
        "unchanged_count": 0,
        "status": "OK",
    }
    row.update(overrides)
    return row


def test_aggregation_and_pattern_detection(monkeypatch) -> None:
    monkeypatch.setattr(
        summary_mod,
        "read_diff_history",
        lambda limit=10: {
            "status": "OK",
            "reason": "ok",
            "history": [
                _history_row(added_count=2, removed_count=1, hash_changed_count=1, freshness_changed_count=1, status_changed_count=0),
                _history_row(added_count=0, removed_count=2, hash_changed_count=1, freshness_changed_count=0, status_changed_count=1),
            ],
        },
    )
    payload = summary_mod.build_manifest_change_summary(window_size=10, timestamp_utc="2026-04-21T00:00:00Z")
    summary = payload["summary"]

    assert payload["status"] == "OK"
    assert summary["totals"]["added_total"] == 2
    assert summary["totals"]["removed_total"] == 3
    assert summary["totals"]["hash_changed_total"] == 2
    assert summary["patterns"]["repeated_hash_churn_count"] == 2
    assert summary["patterns"]["stale_transition_count"] == 1
    assert summary["patterns"]["artifact_disappearance_count"] == 3


def test_not_computable_when_history_missing(monkeypatch) -> None:
    monkeypatch.setattr(
        summary_mod,
        "read_diff_history",
        lambda limit=10: {"status": "NOT_COMPUTABLE", "reason": "report_missing:x", "history": []},
    )
    payload = summary_mod.build_manifest_change_summary(window_size=10, timestamp_utc="2026-04-21T00:00:00Z")
    assert payload["status"] == "NOT_COMPUTABLE"
    assert payload["summary"]["stability_indicator"] == "NOT_COMPUTABLE"


def test_deterministic_output(monkeypatch) -> None:
    monkeypatch.setattr(
        summary_mod,
        "read_diff_history",
        lambda limit=10: {"status": "OK", "reason": "ok", "history": [_history_row()]},
    )
    a = summary_mod.build_manifest_change_summary(window_size=10, timestamp_utc="2026-04-21T00:00:00Z")
    b = summary_mod.build_manifest_change_summary(window_size=10, timestamp_utc="2026-04-21T00:00:00Z")
    assert a == b


def test_schema_validation(monkeypatch) -> None:
    monkeypatch.setattr(
        summary_mod,
        "read_diff_history",
        lambda limit=10: {"status": "OK", "reason": "ok", "history": [_history_row()]},
    )
    payload = summary_mod.build_manifest_change_summary(window_size=10, timestamp_utc="2026-04-21T00:00:00Z")
    schema = json.loads(Path("schemas/ReportManifestChangeSummary.v1.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(payload["summary"])
