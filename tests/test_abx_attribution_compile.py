from __future__ import annotations

import json
import runpy
import sys
from pathlib import Path
from typing import Any

import pytest

import abx.attribution_compile as attribution_compile


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = [row if isinstance(row, str) else json.dumps(row, ensure_ascii=False) for row in rows]
    path.write_text("\n".join(encoded) + "\n", encoding="utf-8")


def test_json_readers_fail_closed_and_jsonl_skips_invalid_rows(tmp_path: Path) -> None:
    missing = tmp_path / "missing.json"
    malformed = tmp_path / "malformed.json"
    non_object = tmp_path / "list.json"
    valid = tmp_path / "valid.json"
    malformed.write_text("{broken", encoding="utf-8")
    _write_json(non_object, ["not", "an", "object"])
    _write_json(valid, {"ok": True})

    assert attribution_compile._read_json(str(missing)) == {}
    assert attribution_compile._read_json(str(malformed)) == {}
    assert attribution_compile._read_json(str(non_object)) == {}
    assert attribution_compile._read_json(str(valid)) == {"ok": True}
    assert attribution_compile._read_jsonl("") == []
    assert attribution_compile._read_jsonl(str(tmp_path / "missing.jsonl")) == []

    ledger = tmp_path / "events.jsonl"
    ledger.write_text(
        '\ninvalid-json\n["not", "an", "object"]\n{"kind":"kept"}\n', encoding="utf-8"
    )
    assert attribution_compile._read_jsonl(str(ledger)) == [{"kind": "kept"}]


def test_latest_picks_lexicographically_last_report(tmp_path: Path) -> None:
    (tmp_path / "online_resolver_001.json").write_text("{}", encoding="utf-8")
    (tmp_path / "online_resolver_002.json").write_text("{}", encoding="utf-8")

    assert attribution_compile._latest(str(tmp_path / "online_resolver_*.json")).endswith(
        "online_resolver_002.json"
    )
    assert attribution_compile._latest(str(tmp_path / "absent_*.json")) == ""


def test_main_compiles_task_anchor_edge_and_claim_views(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    task_ledger = tmp_path / "input" / "tasks.jsonl"
    anchor_ledger = tmp_path / "input" / "anchors.jsonl"
    evidence_ledger = tmp_path / "input" / "evidence.jsonl"
    resolver = tmp_path / "input" / "resolver.json"
    output = tmp_path / "out" / "graph.json"

    _write_json(
        resolver,
        {
            "task_anchor_map": {
                "resolver-task": ["a4", "resolver-anchor", "", None],
                "invalid-map": "not-a-list",
            }
        },
    )
    _write_jsonl(
        anchor_ledger,
        [
            {"anchor_id": "", "task_id": "ignored", "claim_id": "ignored"},
            {"anchor_id": "a1", "task_id": "task-1", "claim_id": "claim-1"},
            {"anchor_id": "a2", "task_id": "task-1", "claim_id": "claim-2"},
            {"anchor_id": "a3", "task_id": "", "claim_id": "claim-1"},
            {"anchor_id": "a4", "task_id": "task-a", "claim_id": ""},
            {"anchor_id": "a1", "task_id": "task-1", "claim_id": "claim-1"},
            "invalid-json",
            ["not", "an", "object"],
        ],
    )
    _write_jsonl(
        evidence_ledger,
        [
            {"kind": "other", "anchor_id": "a1", "claim_id": "ignored"},
            {"kind": "anchor_claim_link", "anchor_id": "", "claim_id": "claim-1"},
            {"kind": "anchor_claim_link", "anchor_id": "a1", "claim_id": ""},
            {"kind": "anchor_claim_link", "anchor_id": "unknown", "claim_id": "claim-4"},
            {
                "kind": "anchor_claim_link",
                "anchor_id": "a1",
                "claim_id": "claim-1",
                "relation": "SUPPORTS",
                "url": "https://example.test/one",
                "domain": "example.test",
                "ts": "2026-10-10T00:00:00+00:00",
            },
            {
                "kind": "anchor_claim_link",
                "anchor_id": "a2",
                "claim_id": "claim-1",
                "relation": "CONTRADICTS",
                "url": "https://example.test/two",
                "domain": "example.test",
                "ts": "2026-10-10T00:01:00+00:00",
            },
            {
                "kind": "anchor_claim_link",
                "anchor_id": "a4",
                "claim_id": "claim-3",
                "relation": "REFRAMES",
            },
            {"kind": "anchor_claim_link", "anchor_id": "resolver-anchor", "claim_id": "claim-1"},
        ],
    )
    _write_jsonl(
        task_ledger,
        [
            {
                "kind": "task_event",
                "task_id": "task-1",
                "task_kind": "VERIFY_MEDIA_ORIGIN",
                "mode": "ONLINE",
                "status": "QUEUED",
                "claim_id": "claim-1",
                "term": "alpha",
                "detail": "initial task",
                "ts": "2026-10-09T12:00:00+00:00",
                "run_id": "run-old",
            },
            {"kind": "task_status_changed", "task_id": "task-1", "status": "DONE"},
            {
                "kind": "task_event",
                "task_id": "task-1",
                "task_kind": "VERIFY_MEDIA_ORIGIN",
                "mode": "OFFLINE",
                "status": "DONE",
                "claim_id": "claim-1",
                "term": "alpha",
                "detail": "latest task metadata",
                "ts": "2026-10-10T01:00:00+00:00",
                "run_id": "run-new",
            },
            {
                "kind": "task_event",
                "task_id": "task-a",
                "task_kind": "ADD_PRIMARY_ANCHORS",
                "mode": "ONLINE",
                "status": "DONE",
                "claim_id": "claim-3",
                "term": "beta",
                "detail": "anchor collection",
                "ts": "2026-10-10T02:00:00+00:00",
                "run_id": "run-a",
            },
            {"kind": "task_event", "task_id": "", "task_kind": "ignored"},
        ],
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "attribution_compile",
            "--task-ledger",
            str(task_ledger),
            "--anchor-ledger",
            str(anchor_ledger),
            "--evidence-ledger",
            str(evidence_ledger),
            "--resolver-report",
            str(resolver),
            "--out",
            str(output),
        ],
    )

    assert attribution_compile.main() == 0

    graph = json.loads(output.read_text(encoding="utf-8"))
    assert graph["version"] == "attribution_graph.v0.1"
    assert graph["inputs"] == {
        "task_ledger": str(task_ledger),
        "anchor_ledger": str(anchor_ledger),
        "evidence_ledger": str(evidence_ledger),
        "resolver_report": str(resolver),
    }
    assert graph["ts"].endswith("+00:00")
    assert [task["task_id"] for task in graph["tasks"]] == [
        "task-1",
        "resolver-task",
        "task-a",
    ]
    task_one, resolver_task, task_a = graph["tasks"]
    assert task_one["meta"] == {
        "task_kind": "VERIFY_MEDIA_ORIGIN",
        "mode": "OFFLINE",
        "status": "DONE",
        "claim_id": "claim-1",
        "term": "alpha",
        "detail": "latest task metadata",
        "ts": "2026-10-10T01:00:00+00:00",
        "run_id": "run-new",
    }
    assert task_one["anchors"] == ["a1", "a2"]
    assert task_one["n_edges"] == 2
    assert task_one["claims_touched"] == ["claim-1"]
    assert resolver_task["meta"] == {}
    assert resolver_task["anchors"] == ["a4", "resolver-anchor"]
    assert resolver_task["n_edges"] == 1
    assert task_a["meta"]["detail"] == "anchor collection"
    assert task_a["anchors"] == ["a4"]
    assert task_a["claims_touched"] == ["claim-3"]
    assert [
        (claim["claim_id"], claim["tasks"], claim["n_anchors"]) for claim in graph["claims"]
    ] == [
        ("claim-1", ["resolver-task", "task-1"], 2),
        ("claim-3", ["task-a"], 0),
    ]
    assert capsys.readouterr().out == f"[ATTR] wrote: {output}\n"


def test_main_falls_back_from_non_object_resolver_map(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    resolver = tmp_path / "resolver.json"
    output = tmp_path / "graph.json"
    _write_json(resolver, {"task_anchor_map": ["invalid"]})
    monkeypatch.setattr(
        sys,
        "argv",
        ["attribution_compile", "--resolver-report", str(resolver), "--out", str(output)],
    )

    assert attribution_compile.main() == 0

    graph = json.loads(output.read_text(encoding="utf-8"))
    assert graph["tasks"] == []
    assert graph["claims"] == []
    assert graph["inputs"]["resolver_report"] == str(resolver)


def test_module_entrypoint_uses_latest_resolver_and_default_output(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    reports = tmp_path / "out" / "reports"
    _write_json(reports / "online_resolver_001.json", {"task_anchor_map": {"task-r": ["anchor-r"]}})
    monkeypatch.setattr(sys, "argv", ["attribution_compile"])

    with pytest.raises(SystemExit) as exc_info:
        runpy.run_path(str(Path(attribution_compile.__file__)), run_name="__main__")

    assert exc_info.value.code == 0
    output_files = list(reports.glob("attribution_graph_*.json"))
    assert len(output_files) == 1
    graph = json.loads(output_files[0].read_text(encoding="utf-8"))
    assert graph["inputs"]["resolver_report"].endswith("online_resolver_001.json")
    assert graph["tasks"] == [
        {
            "task_id": "task-r",
            "meta": {},
            "n_anchors": 1,
            "anchors": ["anchor-r"],
            "n_edges": 0,
            "edges": [],
            "claims_touched": [],
        }
    ]


def test_main_skips_non_object_rows_from_each_reader(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    output = tmp_path / "out" / "graph.json"

    def read_rows(_path: str) -> list[Any]:
        return [None]

    monkeypatch.setattr(attribution_compile, "_read_jsonl", read_rows)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "attribution_compile",
            "--task-ledger",
            "tasks.jsonl",
            "--anchor-ledger",
            "anchors.jsonl",
            "--evidence-ledger",
            "evidence.jsonl",
            "--out",
            str(output),
        ],
    )

    assert attribution_compile.main() == 0

    graph = json.loads(output.read_text(encoding="utf-8"))
    assert graph["tasks"] == []
    assert graph["claims"] == []
