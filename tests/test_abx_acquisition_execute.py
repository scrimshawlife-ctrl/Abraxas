from __future__ import annotations

import json
import runpy
import sys
from pathlib import Path
from typing import Any

import pytest

import abx.acquisition_execute as acquisition_execute


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def _set_status_recorder(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    updates: list[dict[str, Any]] = []

    def record(**kwargs: Any) -> None:
        updates.append(kwargs)

    monkeypatch.setattr(acquisition_execute, "task_status_change", record)
    return updates


def test_jsonl_io_and_line_count_helpers(tmp_path: Path) -> None:
    ledger = tmp_path / "nested" / "events.jsonl"
    acquisition_execute._append_jsonl(str(ledger), {"kind": "event", "value": 1})
    ledger.write_text(ledger.read_text(encoding="utf-8") + "\n  \n{bad\n", encoding="utf-8")

    assert json.loads(ledger.read_text(encoding="utf-8").splitlines()[0]) == {
        "kind": "event",
        "value": 1,
    }
    assert acquisition_execute._count_lines(str(ledger)) == 2
    assert acquisition_execute._count_lines(str(tmp_path / "missing.jsonl")) == 0

    valid = tmp_path / "valid.json"
    malformed = tmp_path / "malformed.json"
    non_object = tmp_path / "list.json"
    _write_json(valid, {"tasks": []})
    malformed.write_text("{broken", encoding="utf-8")
    _write_json(non_object, [1, 2])
    assert acquisition_execute._read_json(str(valid)) == {"tasks": []}
    assert acquisition_execute._read_json(str(malformed)) == {}
    assert acquisition_execute._read_json(str(non_object)) == {}
    assert acquisition_execute._read_json(str(tmp_path / "absent.json")) == {}


def test_roi_uses_kind_specific_and_fallback_scoring() -> None:
    assert acquisition_execute._roi("ADD_PRIMARY_ANCHORS", {"anchors_added": 1}) == pytest.approx(
        1 / 3
    )
    assert acquisition_execute._roi("ADD_PRIMARY_ANCHORS", {"anchors_added": 9}) == 1.0
    assert acquisition_execute._roi("INCREASE_DOMAIN_DIVERSITY", {"domains_added": 2}) == 0.5
    assert acquisition_execute._roi(
        "FETCH_COUNTERCLAIMS_DISJOINT", {"counterclaims_added": 1}
    ) == pytest.approx(1 / 3)
    assert acquisition_execute._roi("VERIFY_MEDIA_ORIGIN", {"media_verified": True}) == 1.0
    assert acquisition_execute._roi("VERIFY_MEDIA_ORIGIN", {}) == 0.0
    assert (
        acquisition_execute._roi(
            "OTHER", {"anchors_added": 2, "domains_added": 1, "counterclaims_added": 3}
        )
        == 1.0
    )
    assert acquisition_execute._roi("OTHER", {}) == 0.0


def test_placeholder_executor_is_structured_and_has_no_network_side_effect() -> None:
    outcome = acquisition_execute._execute_one_task({"task_id": "t1"}, provider="test-provider")
    assert outcome == {
        "status": "FAILED",
        "anchors_added": 0,
        "domains_added": 0,
        "counterclaims_added": 0,
        "media_verified": False,
        "error": "executor_not_implemented",
        "provider": "test-provider",
    }


def test_main_without_provider_marks_offline_and_uses_media_report(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    batch = tmp_path / "input" / "batch.json"
    media_report = tmp_path / "input" / "media.json"
    anchor_ledger = tmp_path / "ledger" / "anchors.jsonl"
    outcomes_ledger = tmp_path / "ledger" / "outcomes.jsonl"
    task_ledger = tmp_path / "ledger" / "tasks.jsonl"
    _write_json(
        batch,
        {
            "batch_id": "batch-7",
            "tasks": [
                {
                    "task_id": "media-yes",
                    "claim_id": "c1",
                    "term": "alpha",
                    "task_kind": "VERIFY_MEDIA_ORIGIN",
                },
                {
                    "task_id": "offline",
                    "task_kind": "ADD_PRIMARY_ANCHORS",
                    "detail": "need provider",
                },
                {"task_id": "media-no", "task_kind": "VERIFY_MEDIA_ORIGIN"},
                "invalid task row",
            ],
        },
    )
    _write_json(
        media_report,
        {
            "items": [
                {"task_id": "media-yes", "ok": True},
                {"task_id": "media-no", "ok": False},
                {"task_id": "", "ok": True},
                "invalid item",
            ]
        },
    )
    anchor_ledger.parent.mkdir(parents=True)
    anchor_ledger.write_text('{"anchor_id":"existing"}\n\n', encoding="utf-8")
    updates = _set_status_recorder(monkeypatch)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "acquisition_execute",
            "--run-id",
            "run-7",
            "--in",
            str(batch),
            "--task-ledger",
            str(task_ledger),
            "--anchor-ledger",
            str(anchor_ledger),
            "--outcomes-ledger",
            str(outcomes_ledger),
            "--media-origin-report",
            str(media_report),
        ],
    )

    assert acquisition_execute.main() == 0

    outcomes = [
        json.loads(line) for line in outcomes_ledger.read_text(encoding="utf-8").splitlines()
    ]
    assert [row["task_id"] for row in outcomes] == ["media-yes", "offline", "media-no"]
    assert [row["status"] for row in outcomes] == ["NEEDS_OFFLINE"] * 3
    assert outcomes[0]["outcome"]["media_verified"] is True
    assert outcomes[0]["roi"] == 1.0
    assert outcomes[0]["outcome"]["anchors_added"] == 0
    assert outcomes[1]["outcome"]["offline_required_reason"] == "no_provider_configured"
    assert outcomes[2]["roi"] == 0.0
    assert all(row["batch_in"] == str(batch) and row["run_id"] == "run-7" for row in outcomes)
    assert [update["task_id"] for update in updates] == ["media-yes", "offline", "media-no"]
    assert all(update["to_status"] == "NEEDS_OFFLINE" for update in updates)
    assert all(update["batch_id"] == "batch-7" for update in updates)
    assert capsys.readouterr().out == f"[ACQ] processed tasks=4 outcomes={outcomes_ledger}\n"


def test_main_provider_results_exceptions_and_anchor_delta(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    batch = tmp_path / "batch.json"
    media_report = tmp_path / "media.json"
    anchor_ledger = tmp_path / "anchors.jsonl"
    outcomes_ledger = tmp_path / "nested" / "outcomes.jsonl"
    task_ledger = tmp_path / "tasks.jsonl"
    tasks = [
        {"task_id": "added", "task_kind": "ADD_PRIMARY_ANCHORS"},
        {"task_id": "reported", "task_kind": "ADD_PRIMARY_ANCHORS"},
        {"task_id": "non-dict", "task_kind": "OTHER"},
        {"task_id": "raises", "task_kind": "OTHER"},
        {"task_id": "media-yes", "task_kind": "VERIFY_MEDIA_ORIGIN"},
        {"task_id": "media-no", "task_kind": "VERIFY_MEDIA_ORIGIN"},
        {"task_id": "", "task_kind": "OTHER"},
    ]
    _write_json(batch, {"batch_id": "batch-provider", "tasks": tasks})
    _write_json(
        media_report,
        {"items": [{"task_id": "media-yes", "ok": True}, {"task_id": "media-no", "ok": False}]},
    )
    anchor_ledger.write_text("", encoding="utf-8")
    executor_calls: list[tuple[Any, str]] = []

    def fake_executor(task: dict[str, Any], provider: str) -> Any:
        task_id = task.get("task_id")
        executor_calls.append((task_id, provider))
        if task_id == "added":
            with anchor_ledger.open("a", encoding="utf-8") as f:
                f.write('{"anchor_id":"a1"}\n{"anchor_id":"a2"}\n')
            return {"status": "DONE", "anchors_added": 0}
        if task_id == "reported":
            return {"status": "", "anchors_added": 2, "domains_added": 1}
        if task_id == "non-dict":
            return ["not", "a", "mapping"]
        if task_id == "raises":
            raise RuntimeError("provider failed")
        return {"status": "DONE"}

    monkeypatch.setattr(acquisition_execute, "_execute_one_task", fake_executor)
    updates = _set_status_recorder(monkeypatch)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "acquisition_execute",
            "--run-id",
            "run-provider",
            "--in",
            str(batch),
            "--provider",
            "mock-provider",
            "--task-ledger",
            str(task_ledger),
            "--anchor-ledger",
            str(anchor_ledger),
            "--outcomes-ledger",
            str(outcomes_ledger),
            "--media-origin-report",
            str(media_report),
        ],
    )

    assert acquisition_execute.main() == 0

    outcomes = [
        json.loads(line) for line in outcomes_ledger.read_text(encoding="utf-8").splitlines()
    ]
    assert len(outcomes) == 7
    assert [row["status"] for row in outcomes] == [
        "DONE",
        "FAILED",
        "FAILED",
        "FAILED",
        "DONE",
        "DONE",
        "DONE",
    ]
    assert outcomes[0]["outcome"]["anchors_added"] == 2
    assert outcomes[0]["roi"] == pytest.approx(2 / 3)
    assert outcomes[1]["outcome"]["anchors_added"] == 2
    assert outcomes[1]["roi"] == pytest.approx(2 / 3)
    assert outcomes[2]["outcome"] == {
        "anchors_added": 0,
        "domains_added": 0,
        "counterclaims_added": 0,
        "media_verified": False,
    }
    assert outcomes[3]["outcome"]["error"] == "RuntimeError('provider failed')"
    assert outcomes[4]["outcome"]["media_verified"] is True
    assert outcomes[4]["roi"] == 1.0
    assert outcomes[5]["outcome"]["media_verified"] is False
    assert outcomes[5]["roi"] == 0.0
    assert executor_calls == [(task["task_id"], "mock-provider") for task in tasks]
    assert len(updates) == 7 and all(
        update["to_status"] == outcome["status"]
        for update, outcome in zip(updates, outcomes, strict=True)
    )
    assert capsys.readouterr().out == f"[ACQ] processed tasks=7 outcomes={outcomes_ledger}\n"


def test_media_report_read_exception_fails_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    batch = tmp_path / "batch.json"
    media_report = tmp_path / "media.json"
    outcomes_ledger = tmp_path / "outcomes.jsonl"
    _write_json(batch, {"tasks": [{"task_id": "media", "task_kind": "VERIFY_MEDIA_ORIGIN"}]})
    updates = _set_status_recorder(monkeypatch)
    real_read_json = acquisition_execute._read_json

    def fail_media_read(path: str) -> dict[str, Any]:
        if path == str(media_report):
            raise OSError("media report unavailable")
        return real_read_json(path)

    monkeypatch.setattr(acquisition_execute, "_read_json", fail_media_read)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "acquisition_execute",
            "--run-id",
            "run-media",
            "--in",
            str(batch),
            "--media-origin-report",
            str(media_report),
            "--anchor-ledger",
            str(tmp_path / "anchors.jsonl"),
            "--task-ledger",
            str(tmp_path / "tasks.jsonl"),
            "--outcomes-ledger",
            str(outcomes_ledger),
        ],
    )

    assert acquisition_execute.main() == 0

    outcome = json.loads(outcomes_ledger.read_text(encoding="utf-8").strip())
    assert outcome["outcome"]["media_verified"] is False
    assert outcome["roi"] == 0.0
    assert updates[0]["task_id"] == "media"


def test_module_entrypoint_runs_empty_batch_cli(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    batch = tmp_path / "empty.json"
    outcomes_ledger = tmp_path / "nested" / "outcomes.jsonl"
    _write_json(batch, {"tasks": []})
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "acquisition_execute",
            "--run-id",
            "run-empty",
            "--in",
            str(batch),
            "--outcomes-ledger",
            str(outcomes_ledger),
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        runpy.run_path(acquisition_execute.__file__, run_name="__main__")

    assert exc_info.value.code == 0
    assert not outcomes_ledger.exists()
