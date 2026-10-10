from __future__ import annotations

import json
import runpy
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

import abx.task_union_ledger as task_union_ledger

_FIXED_NOW = datetime(2026, 10, 10, tzinfo=timezone.utc)


def _task_event(
    task_id: str,
    *,
    claim_id: str = "claim-1",
    term: str = "alpha",
    task_kind: str = "ADD_PRIMARY_ANCHORS",
    detail: str = "task detail",
    status: str = "QUEUED",
    due_ts: str | None = None,
    front_tags: list[str] | None = None,
) -> dict[str, Any]:
    artifacts: dict[str, Any] = {}
    if due_ts is not None:
        artifacts["due_ts"] = due_ts
    if front_tags is not None:
        artifacts["front_tags"] = front_tags
    return {
        "kind": "task_event",
        "ts": "2026-10-09T12:00:00+00:00",
        "run_id": "source-run",
        "task_id": task_id,
        "status": status,
        "mode": "test",
        "claim_id": claim_id,
        "term": term,
        "task_kind": task_kind,
        "detail": detail,
        "artifacts": artifacts,
    }


def _write_jsonl(path: Path, rows: list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = [row if isinstance(row, str) else json.dumps(row, ensure_ascii=False) for row in rows]
    path.write_text("\n".join(encoded) + "\n", encoding="utf-8")


def _run_main(monkeypatch: pytest.MonkeyPatch, argv: list[str]) -> int:
    monkeypatch.setattr(sys, "argv", ["task_union_ledger", *argv])
    return task_union_ledger.main()


def _freeze_clock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(task_union_ledger, "_utc_now", lambda: _FIXED_NOW)


def test_parse_iso_accepts_aware_and_naive_timestamps_and_rejects_invalid() -> None:
    aware = task_union_ledger._parse_iso("2026-10-10T00:00:00+00:00")
    naive = task_union_ledger._parse_iso("2026-10-10T00:00:00")

    assert aware == _FIXED_NOW
    assert naive == _FIXED_NOW
    assert naive is not None and naive.tzinfo == timezone.utc
    assert task_union_ledger._parse_iso("not-a-timestamp") is None


def test_front_multipliers_normalize_tags_and_task_priorities() -> None:
    overrides = {
        "POLLUTION": {"VERIFY": 1.35},
        "MIGRATION": {"VERIFY": 1.2},
    }
    assert task_union_ledger._front_mult(
        [" pollution ", "migration", ""], overrides, "VERIFY"
    ) == pytest.approx(1.62)
    assert task_union_ledger._front_mult(["UNKNOWN"], overrides, "VERIFY") == 1.0
    assert task_union_ledger._front_mult([], overrides, "VERIFY") == 1.0
    assert task_union_ledger._prio("VERIFY_MEDIA_ORIGIN", ["POLLUTION"]) == 135.0
    assert task_union_ledger._prio("unregistered-kind", []) == 10.0


def test_read_jsonl_skips_missing_paths_blank_malformed_and_non_object_rows(tmp_path: Path) -> None:
    assert task_union_ledger._read_jsonl("") == []
    assert task_union_ledger._read_jsonl(str(tmp_path / "missing.jsonl")) == []

    path = tmp_path / "events.jsonl"
    path.write_text(
        '\nnot-json\n["not", "an", "object"]\n{"kind":"task_event"}\n', encoding="utf-8"
    )
    assert task_union_ledger._read_jsonl(str(path)) == [{"kind": "task_event"}]


def test_dedupe_key_uses_claim_term_and_task_kind() -> None:
    task = {"claim_id": "c1", "term": "alpha", "task_kind": "VERIFY_MEDIA_ORIGIN"}
    assert task_union_ledger._dedupe_key(task) == ("c1", "alpha", "VERIFY_MEDIA_ORIGIN")
    assert task_union_ledger._dedupe_key({}) == ("", "", "")


def test_merge_detail_handles_empty_repeated_and_distinct_details() -> None:
    assert task_union_ledger._merge_detail({}, {"detail": "incoming"}) == "incoming"
    assert task_union_ledger._merge_detail({"detail": "kept"}, {}) == "kept"
    assert (
        task_union_ledger._merge_detail({"detail": "kept; repeated"}, {"detail": "repeated"})
        == "kept; repeated"
    )
    assert (
        task_union_ledger._merge_detail({"detail": "kept"}, {"detail": "incoming"})
        == "kept | incoming"
    )


def test_latest_task_state_ignores_invalid_events_and_applies_status_updates() -> None:
    events = [
        None,
        {"kind": "task_event", "task_id": ""},
        {"kind": "task_status_changed", "task_id": "missing", "to_status": "DONE"},
        _task_event("task-1", due_ts="2026-10-12T00:00:00+00:00"),
        {
            **_task_event("task-1", detail="latest detail"),
            "run_id": "latest-run",
            "artifacts": {},
        },
        {
            "kind": "task_status_changed",
            "task_id": "task-1",
            "to_status": "IN_PROGRESS",
            "ts": "2026-10-10T01:00:00+00:00",
        },
        {"kind": "task_status_changed", "task_id": "task-1", "to_status": "", "ts": ""},
        {"kind": "unrelated", "task_id": "task-1"},
    ]

    state = task_union_ledger._latest_task_state(events)

    assert list(state) == ["task-1"]
    assert state["task-1"]["run_id"] == "latest-run"
    assert state["task-1"]["detail"] == "latest detail"
    assert state["task-1"]["due_ts"] == "2026-10-12T00:00:00+00:00"
    assert state["task-1"]["status"] == "IN_PROGRESS"
    assert state["task-1"]["ts"] == "2026-10-10T01:00:00+00:00"


def test_eligible_requires_queued_and_treats_missing_or_invalid_due_as_ready() -> None:
    assert task_union_ledger._eligible({"status": "IN_PROGRESS"}, _FIXED_NOW) is False
    assert task_union_ledger._eligible({"status": "QUEUED"}, _FIXED_NOW) is True
    assert task_union_ledger._eligible({"status": "QUEUED", "due_ts": " "}, _FIXED_NOW) is True
    assert (
        task_union_ledger._eligible({"status": "QUEUED", "due_ts": "invalid"}, _FIXED_NOW) is True
    )
    assert (
        task_union_ledger._eligible(
            {"status": "QUEUED", "due_ts": "2026-10-09T23:59:59+00:00"}, _FIXED_NOW
        )
        is True
    )
    assert (
        task_union_ledger._eligible(
            {"status": "QUEUED", "due_ts": "2026-10-10T00:00:01+00:00"}, _FIXED_NOW
        )
        is False
    )


def test_main_deduplicates_selects_by_priority_and_records_the_actual_loser(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    _freeze_clock(monkeypatch)
    task_path = tmp_path / "tasks.jsonl"
    union_path = tmp_path / "union.jsonl"
    events = [
        _task_event("weak", detail="base detail"),
        _task_event("strong", detail="urgent detail", front_tags=["pollution"]),
        _task_event("third", detail="follow-up detail"),
        _task_event(
            "verify",
            claim_id="claim-verify",
            term="beta",
            task_kind="VERIFY_MEDIA_ORIGIN",
            detail="verify source",
        ),
        _task_event(
            "diversity",
            claim_id="claim-diversity",
            term="gamma",
            task_kind="INCREASE_DOMAIN_DIVERSITY",
            detail="diversify sources",
            front_tags=["reupload_storm"],
        ),
        _task_event("future", claim_id="future", due_ts="2026-10-11T00:00:00+00:00"),
        _task_event(
            "invalid-due", claim_id="invalid", task_kind="ENTITY_GROUNDING", due_ts="bad-date"
        ),
        _task_event("active", claim_id="active"),
        {
            "kind": "task_status_changed",
            "ts": "2026-10-09T13:00:00+00:00",
            "task_id": "active",
            "to_status": "IN_PROGRESS",
        },
    ]
    _write_jsonl(task_path, events)
    status_changes: list[dict[str, Any]] = []
    monkeypatch.setattr(
        task_union_ledger, "task_status_change", lambda **kwargs: status_changes.append(kwargs)
    )

    assert (
        _run_main(
            monkeypatch,
            [
                "--run-id",
                "run-1",
                "--task-ledger",
                str(task_path),
                "--union-ledger",
                str(union_path),
                "--max",
                "3",
            ],
        )
        == 0
    )

    out_path = tmp_path / "out" / "reports" / "acq_batch_20261010T000000Z.json"
    batch = json.loads(out_path.read_text(encoding="utf-8"))
    assert batch["run_id"] == "run-1"
    assert batch["batch_id"] == "acq_batch_20261010T000000Z"
    assert batch["stats"] == {
        "n_tasks_state": 8,
        "n_eligible": 6,
        "n_dedup_dropped": 2,
        "n_out": 3,
        "dry_run": False,
    }
    assert [task["task_id"] for task in batch["tasks"]] == ["strong", "verify", "diversity"]
    assert batch["tasks"][0]["detail"] == "urgent detail | base detail | follow-up detail"

    union_events = task_union_ledger._read_jsonl(str(union_path))
    dropped = [event for event in union_events if event["kind"] == "task_dedup_dropped"]
    assert [(event["dropped_task_id"], event["kept_task_id"]) for event in dropped] == [
        ("weak", "strong"),
        ("third", "strong"),
    ]
    assert union_events[-1]["kind"] == "task_batch_selected"
    assert union_events[-1]["n_out"] == 3
    assert [change["task_id"] for change in status_changes] == ["strong", "verify", "diversity"]
    assert all(change["to_status"] == "IN_PROGRESS" for change in status_changes)
    assert capsys.readouterr().out == (
        "[UNION_LEDGER] wrote: out/reports/acq_batch_20261010T000000Z.json "
        "out=3 eligible=6 dropped=2 dry=False\n"
    )


def test_main_dry_run_writes_custom_path_without_transitioning_tasks(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    _freeze_clock(monkeypatch)
    task_path = tmp_path / "tasks.jsonl"
    _write_jsonl(task_path, [_task_event("dry-task", task_kind="VERIFY_MEDIA_ORIGIN")])
    monkeypatch.setattr(
        task_union_ledger,
        "task_status_change",
        lambda **_kwargs: pytest.fail("dry run must not transition task state"),
    )
    out_path = tmp_path / "custom" / "batch.json"
    union_path = tmp_path / "ledger" / "union.jsonl"

    assert (
        _run_main(
            monkeypatch,
            [
                "--run-id",
                "dry",
                "--task-ledger",
                str(task_path),
                "--union-ledger",
                str(union_path),
                "--out",
                str(out_path),
                "--max",
                "1",
                "--dry-run",
            ],
        )
        == 0
    )

    result = json.loads(out_path.read_text(encoding="utf-8"))
    assert result["stats"]["dry_run"] is True
    assert result["stats"]["n_out"] == 1
    assert task_union_ledger._read_jsonl(str(union_path))[-1]["dry_run"] is True


def test_main_skips_status_transition_when_task_id_is_empty(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    _freeze_clock(monkeypatch)
    empty_id_state = {
        "empty": {
            "task_id": "",
            "run_id": "source",
            "status": "QUEUED",
            "mode": "test",
            "claim_id": "claim-empty",
            "term": "alpha",
            "task_kind": "VERIFY_MEDIA_ORIGIN",
            "detail": "empty identifier",
            "due_ts": "",
            "ts": "",
            "artifacts": {},
        }
    }
    status_changes: list[dict[str, Any]] = []
    monkeypatch.setattr(task_union_ledger, "_read_jsonl", lambda _path: [])
    monkeypatch.setattr(task_union_ledger, "_latest_task_state", lambda _events: empty_id_state)
    monkeypatch.setattr(
        task_union_ledger, "task_status_change", lambda **kwargs: status_changes.append(kwargs)
    )

    assert _run_main(monkeypatch, ["--run-id", "empty-id", "--out", "out/empty.json"]) == 0

    result = json.loads((tmp_path / "out" / "empty.json").read_text(encoding="utf-8"))
    assert result["stats"]["n_out"] == 1
    assert result["tasks"][0]["task_id"] == ""
    assert status_changes == []


def test_main_requires_run_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["task_union_ledger"])
    with pytest.raises(SystemExit) as exc_info:
        task_union_ledger.main()
    assert exc_info.value.code == 2


def test_module_entrypoint_runs_successfully_without_input_events(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["task_union_ledger", "--run-id", "entry", "--dry-run"])

    with pytest.raises(SystemExit) as exc_info:
        runpy.run_path(str(Path(task_union_ledger.__file__)), run_name="__main__")

    assert exc_info.value.code == 0
    reports = list((tmp_path / "out" / "reports").glob("acq_batch_*.json"))
    assert len(reports) == 1
    output = json.loads(reports[0].read_text(encoding="utf-8"))
    assert output["run_id"] == "entry"
    assert output["stats"]["n_tasks_state"] == 0
