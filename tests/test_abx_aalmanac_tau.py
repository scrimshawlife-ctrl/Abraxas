from __future__ import annotations

import json
import runpy
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

import abx.aalmanac_tau as aalmanac_tau

NOW = datetime(2026, 10, 10, 12, 0, 0, tzinfo=timezone.utc)


def _write_jsonl(path: Path, rows: list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_json_helpers_handle_missing_malformed_and_mixed_jsonl(tmp_path: Path) -> None:
    assert aalmanac_tau._read_json(str(tmp_path / "missing.json")) == {}

    object_path = tmp_path / "object.json"
    object_path.write_text('{"valid": true}', encoding="utf-8")
    assert aalmanac_tau._read_json(str(object_path)) == {"valid": True}

    non_object_path = tmp_path / "non-object.json"
    non_object_path.write_text('["not", "an", "object"]', encoding="utf-8")
    assert aalmanac_tau._read_json(str(non_object_path)) == {}

    malformed_path = tmp_path / "malformed.json"
    malformed_path.write_text("{invalid", encoding="utf-8")
    assert aalmanac_tau._read_json(str(malformed_path)) == {}

    assert aalmanac_tau._read_jsonl("") == []
    assert aalmanac_tau._read_jsonl(str(tmp_path / "missing.jsonl")) == []

    mixed_path = tmp_path / "mixed.jsonl"
    mixed_path.write_text(
        '\n{"valid": 1}\nnot json\n["not", "an", "object"]\n{"message": "café"}\n',
        encoding="utf-8",
    )
    assert aalmanac_tau._read_jsonl(str(mixed_path)) == [
        {"valid": 1},
        {"message": "café"},
    ]

    appended_path = tmp_path / "nested" / "events.jsonl"
    aalmanac_tau._append_jsonl(str(appended_path), {"message": "café"})
    aalmanac_tau._append_jsonl(str(appended_path), {"sequence": 2})
    assert [
        json.loads(line) for line in appended_path.read_text(encoding="utf-8").splitlines()
    ] == [
        {"message": "café"},
        {"sequence": 2},
    ]


def test_timestamp_and_term_helpers_normalize_and_match() -> None:
    naive = aalmanac_tau._parse_iso("2026-10-01T02:03:04")
    assert naive == datetime(2026, 10, 1, 2, 3, 4, tzinfo=timezone.utc)

    offset = aalmanac_tau._parse_iso("2026-10-01T02:03:04+02:00")
    assert offset is not None
    assert offset.utcoffset() == timedelta(hours=2)
    assert aalmanac_tau._parse_iso("not-a-timestamp") is None

    assert aalmanac_tau._contains_term("  Alpha  ", "A study of ALPHA signals")
    assert not aalmanac_tau._contains_term("  ", "alpha")
    assert not aalmanac_tau._contains_term("alpha", "")
    assert not aalmanac_tau._contains_term("missing", "alpha")


def test_latest_seen_uses_latest_valid_match_across_runs_and_anchors() -> None:
    runs = [
        {"kind": "other", "text": "alpha", "ts": "2099-01-01T00:00:00+00:00"},
        {"kind": "oracle_run", "text": "alpha", "ts": "invalid"},
        {
            "kind": "oracle_run",
            "text": "Alpha is observed",
            "ts": "2026-03-01T00:00:00+00:00",
        },
        {
            "kind": "oracle_run",
            "text": "an ALPHA signal",
            "ts": "2026-04-01T00:00:00+00:00",
        },
        {
            "kind": "oracle_run",
            "text": "unrelated",
            "ts": "2098-01-01T00:00:00+00:00",
        },
    ]
    anchors = [
        {"title": "alpha reference", "content_hint": "older", "ts": "2026-02-01T00:00:00+00:00"},
        {"title": "study", "content_hint": "ALPHA evidence", "ts": "2026-05-01T00:00:00+00:00"},
        {"title": "unrelated", "content_hint": "text", "ts": "2097-01-01T00:00:00+00:00"},
        {"title": "alpha with invalid date", "ts": "bad"},
    ]

    assert aalmanac_tau._latest_seen("alpha", runs, anchors) == "2026-05-01T00:00:00+00:00"
    assert (
        aalmanac_tau._latest_seen(
            "missing",
            [{"kind": "oracle_run", "text": "alpha", "ts": "2026-06-01T00:00:00+00:00"}],
            [],
        )
        is None
    )


@pytest.mark.parametrize(
    ("age_days", "half_life_days", "migration_score", "expected"),
    [
        (0.0, 10.0, 0.65, "RISING"),
        (3.3, 10.0, 0.65, "RISING"),
        (3.4, 10.0, 0.65, "STABLE"),
        (7.5, 10.0, 0.64, "STABLE"),
        (17.5, 10.0, 0.0, "FADING"),
        (17.6, 10.0, 0.0, "EXTINCT"),
        (10.5, 0.0, 0.9, "STABLE"),
    ],
)
def test_decay_state_thresholds(
    age_days: float, half_life_days: float, migration_score: float, expected: str
) -> None:
    assert aalmanac_tau._decay_state(age_days, half_life_days, migration_score) == expected


def test_main_materializes_decay_reviews_and_tasks(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(aalmanac_tau, "_utc_now", lambda: NOW)

    canon = tmp_path / "input" / "aalmanac.jsonl"
    _write_jsonl(
        canon,
        [
            {"kind": "aalmanac_entry", "tier": "CANON", "term": "removed-oldest"},
            {
                "kind": "aalmanac_entry",
                "tier": "CANON",
                "term": "rise",
                "tau": {"half_life_days": 10, "review_every_days": 0.5},
            },
            {"kind": "aalmanac_entry", "tier": "CANON", "term": "stable"},
            {
                "kind": "aalmanac_entry",
                "tier": "CANON",
                "term": "fading",
                "tau": {"half_life_days": 2, "review_every_days": 10},
            },
            {
                "kind": "aalmanac_entry",
                "tier": "CANON",
                "term": "extinct",
                "tau": {"half_life_days": 2, "review_every_days": 20},
            },
            {
                "kind": "aalmanac_entry",
                "tier": "CANON",
                "term": "zero-tau",
                "tau": {"half_life_days": 0, "review_every_days": 0},
            },
            {"kind": "other", "tier": "CANON", "term": "ignored-kind"},
            {"kind": "aalmanac_entry", "tier": "DRAFT", "term": "ignored-tier"},
            {"kind": "aalmanac_entry", "tier": "CANON"},
        ],
    )

    oracle = tmp_path / "input" / "oracle.jsonl"
    _write_jsonl(
        oracle,
        [
            {"kind": "other", "text": "rise", "ts": NOW.isoformat()},
            {"kind": "oracle_run", "text": "rise", "ts": "invalid"},
            {
                "kind": "oracle_run",
                "text": "rise appears",
                "ts": (NOW - timedelta(days=2)).isoformat(),
            },
            {
                "kind": "oracle_run",
                "text": "stable appears",
                "ts": (NOW - timedelta(days=2)).isoformat(),
            },
            {
                "kind": "oracle_run",
                "text": "fading appears",
                "ts": (NOW - timedelta(days=3)).isoformat(),
            },
            {
                "kind": "oracle_run",
                "text": "zero-tau appears",
                "ts": (NOW - timedelta(days=1)).isoformat(),
            },
        ],
    )
    anchors = tmp_path / "input" / "anchors.jsonl"
    _write_jsonl(
        anchors,
        [
            {
                "title": "rise anchor",
                "content_hint": "latest evidence",
                "ts": (NOW - timedelta(days=1)).isoformat(),
            },
            {
                "title": "stable older anchor",
                "content_hint": "stable",
                "ts": (NOW - timedelta(days=4)).isoformat(),
            },
            {
                "title": "fading older anchor",
                "content_hint": "fading",
                "ts": (NOW - timedelta(days=4)).isoformat(),
            },
            {"title": "stable invalid anchor", "content_hint": "stable", "ts": "invalid"},
        ],
    )

    reports = tmp_path / "out" / "reports"
    reports.mkdir(parents=True)
    (reports / "slang_migration_2026-10-09.json").write_text(
        json.dumps({"top": [{"term": "rise", "migration_score": 0.0}]}),
        encoding="utf-8",
    )
    (reports / "slang_migration_2026-10-10.json").write_text(
        json.dumps(
            {
                "top": [
                    "not-an-object",
                    {"term": "rise", "migration_score": 0.9},
                    {"term": "stable", "migration_score": 0.5},
                    {"term": "fading", "migration_score": 0.4},
                    {"term": "extinct"},
                    {"term": "zero-tau", "migration_score": 0.4},
                    {"migration_score": 0.8},
                    {"term": "", "migration_score": 0.8},
                ]
            }
        ),
        encoding="utf-8",
    )

    events = tmp_path / "out" / "ledger" / "tau_events.jsonl"
    tasks = tmp_path / "out" / "ledger" / "tasks.jsonl"
    report = reports / "tau_state.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "aalmanac_tau",
            "--run-id",
            "tau-run",
            "--aalmanac",
            str(canon),
            "--oracle-ledger",
            str(oracle),
            "--anchor-ledger",
            str(anchors),
            "--events-ledger",
            str(events),
            "--task-ledger",
            str(tasks),
            "--out",
            str(report),
            "--max-terms",
            "5",
        ],
    )

    assert aalmanac_tau.main() == 0

    state = json.loads(report.read_text(encoding="utf-8"))
    assert state["version"] == "aalmanac_tau_state.v0.1"
    assert state["ts"] == NOW.isoformat()
    assert state["run_id"] == "tau-run"
    assert state["n_terms"] == 5
    assert [item["term"] for item in state["items"]] == [
        "rise",
        "stable",
        "fading",
        "extinct",
        "zero-tau",
    ]

    items = {item["term"]: item for item in state["items"]}
    assert items["rise"]["decay_state"] == "RISING"
    assert items["rise"]["last_seen_ts"] == (NOW - timedelta(days=1)).isoformat()
    assert items["rise"]["age_days"] == pytest.approx(1.0)
    assert items["rise"]["next_review_ts"] == (NOW + timedelta(days=1)).isoformat()
    assert items["stable"]["decay_state"] == "STABLE"
    assert items["stable"]["tau"] == {"half_life_days": 14.0, "review_every_days": 7.0}
    assert items["fading"]["decay_state"] == "FADING"
    assert items["fading"]["next_review_ts"] == (NOW + timedelta(days=7.5)).isoformat()
    assert items["extinct"]["decay_state"] == "EXTINCT"
    assert items["extinct"]["last_seen_ts"] == ""
    assert items["extinct"]["age_days"] == 9999.0
    assert items["extinct"]["next_review_ts"] == (NOW + timedelta(days=30)).isoformat()
    assert items["zero-tau"]["tau"] == {"half_life_days": 14.0, "review_every_days": 7.0}

    event_rows = [json.loads(line) for line in events.read_text(encoding="utf-8").splitlines()]
    assert len(event_rows) == 5
    assert all(event["kind"] == "aalmanac_tau" for event in event_rows)
    assert all(event["run_id"] == "tau-run" for event in event_rows)
    assert event_rows[0]["ts"] == NOW.isoformat()

    task_rows = [json.loads(line) for line in tasks.read_text(encoding="utf-8").splitlines()]
    assert len(task_rows) == 4
    assert {task["term"] for task in task_rows} == {"rise", "fading"}
    assert {task["task_kind"] for task in task_rows} == {
        "INCREASE_DOMAIN_DIVERSITY",
        "ADD_PRIMARY_ANCHORS",
    }
    assert all(task["kind"] == "task_event" for task in task_rows)
    assert all(task["status"] == "QUEUED" for task in task_rows)
    assert all(task["mode"] == "AALMANAC_TAU" for task in task_rows)
    assert all(task["run_id"] == "tau-run" for task in task_rows)
    assert all(task["task_id"].startswith("aal_tau_") for task in task_rows)
    assert all("tau_event" in task["artifacts"] for task in task_rows)
    assert all(task["artifacts"]["front_tags"][0] == "AALMANAC_DECAY" for task in task_rows)
    assert capsys.readouterr().out == f"[AAL_TAU] wrote: {report} terms=5\n"


def test_module_entrypoint_uses_default_ledgers_and_default_output(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["aalmanac_tau", "--run-id", "empty-run"])

    with pytest.raises(SystemExit) as exc_info:
        runpy.run_path(aalmanac_tau.__file__, run_name="__main__")

    assert exc_info.value.code == 0
    reports = list((tmp_path / "out" / "reports").glob("aalmanac_tau_state_*.json"))
    assert len(reports) == 1
    state = json.loads(reports[0].read_text(encoding="utf-8"))
    assert state["version"] == "aalmanac_tau_state.v0.1"
    assert state["run_id"] == "empty-run"
    assert state["n_terms"] == 0
    assert state["items"] == []
    assert capsys.readouterr().out.startswith("[AAL_TAU] wrote: out/reports/aalmanac_tau_state_")
