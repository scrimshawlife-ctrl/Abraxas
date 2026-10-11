from __future__ import annotations

import json
import runpy
import sys
from pathlib import Path
from typing import Any

import pytest

import abx.term_claim_binder as binder


def _write_json(path: Path, payload: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    return str(path)


def test_read_json_returns_objects_and_falls_back_for_bad_inputs(tmp_path: Path) -> None:
    valid = Path(_write_json(tmp_path / "valid.json", {"tasks": []}))
    array = Path(_write_json(tmp_path / "array.json", []))
    invalid = tmp_path / "invalid.json"
    invalid.write_text("not-json", encoding="utf-8")

    assert binder._read_json(str(valid)) == {"tasks": []}
    assert binder._read_json(str(array)) == {}
    assert binder._read_json(str(invalid)) == {}
    assert binder._read_json(str(tmp_path / "missing.json")) == {}


def test_read_jsonl_skips_invalid_lines_and_non_object_rows(tmp_path: Path) -> None:
    assert binder._read_jsonl("") == []
    assert binder._read_jsonl(str(tmp_path / "missing.jsonl")) == []

    ledger = tmp_path / "ledger.jsonl"
    ledger.write_text('\n{"a": 1}\n[]\nnot-json\n {"b": 2} \n', encoding="utf-8")

    assert binder._read_jsonl(str(ledger)) == [{"a": 1}, {"b": 2}]


def test_append_jsonl_creates_parent_and_appends_rows(tmp_path: Path) -> None:
    ledger = tmp_path / "nested" / "events.jsonl"

    binder._append_jsonl(str(ledger), {"event": "first", "text": "café"})
    binder._append_jsonl(str(ledger), {"event": "second"})

    assert binder._read_jsonl(str(ledger)) == [
        {"event": "first", "text": "café"},
        {"event": "second"},
    ]


def test_normalization_and_anchor_hits_cover_phrase_and_token_boundaries() -> None:
    assert binder._norm("  Climate\n  Change ") == "climate change"
    assert binder._term_hits_in_anchor("Climate Change", "Climate", "change report") == 1
    assert binder._term_hits_in_anchor("climate", "Climate policy", "") == 1
    assert binder._term_hits_in_anchor("climate", "microclimate", "") == 0
    assert binder._term_hits_in_anchor("", "climate", "") == 0
    assert binder._term_hits_in_anchor("climate", "", "") == 0


@pytest.mark.parametrize(
    ("domain", "expected"),
    [
        ("https://www.youtube.com/watch", "social"),
        ("https://arxiv.org/abs/123", "reference"),
        ("https://reuters.com/story", "mainstream"),
        ("https://local.example/story", "other"),
        ("", "none"),
    ],
)
def test_domain_group_classification(domain: str, expected: str) -> None:
    assert binder._domain_group(domain) == expected


def test_build_term_index_scores_hits_and_caps_domain_bonus() -> None:
    anchors = [
        "not-an-object",
        {"title": "climate signal", "domain": "youtube.com"},
        {"claim_id": "", "title": "signal", "domain": "arxiv.org"},
        {"claim_id": "claim-1", "title": "Signal report", "domain": "youtube.com"},
        {"claim_id": "claim-1", "content_hint": "signal update", "domain": "arxiv.org"},
        {"claim_id": "claim-1", "title": "signal", "domain": "reuters.com"},
        {"claim_id": "claim-1", "title": "signal", "domain": "local.example"},
        {"claim_id": "claim-2", "title": "signals", "domain": ""},
    ]

    assert binder.build_term_index(anchors, ["  "]) == {}
    result = binder.build_term_index(anchors, [" Signal "])

    assert result["Signal"]["claim_scores"] == {"claim-1": pytest.approx(5.05)}
    assert result["Signal"]["claim_domain_groups"]["claim-1"] == [
        "mainstream",
        "other",
        "reference",
        "social",
    ]
    assert result["Signal"]["tot_score"] == pytest.approx(5.05)


def test_build_term_index_returns_empty_scores_for_no_matches() -> None:
    result = binder.build_term_index(
        [{"claim_id": "claim-1", "title": "rainfall", "domain": ""}],
        ["snowfall"],
    )

    assert result["snowfall"] == {
        "claim_scores": {},
        "claim_domain_groups": {},
        "tot_score": 0.0,
    }


def test_bind_tasks_covers_bound_and_unbound_reasons_with_deterministic_tie() -> None:
    original = {
        "metadata": {"run": "r1"},
        "tasks": [
            {"id": "bound", "term": "signal"},
            {"id": "missing-index", "term": "unknown"},
            {"id": "no-scores", "term": "empty"},
            {"id": "blank", "term": "  "},
            "malformed-task",
            {"id": "bound-again", "term": "signal", "claim_id": "old"},
        ],
    }
    term_index = {
        "signal": {
            "claim_scores": {"claim-b": 3.0, "claim-a": 3.0},
            "claim_domain_groups": {"claim-a": ["reference"]},
            "tot_score": 6.0,
        },
        "empty": {"claim_scores": {}, "tot_score": 0.0},
    }

    result, stats = binder.bind_tasks(
        tasks_outbox=original,
        term_index=term_index,
        bind_ratio=0.5,
        min_hits=3.0,
    )

    assert stats == {"n_in": 6, "n_bound": 2, "n_unbound": 3}
    assert result["tasks"][0]["claim_id"] == "claim-a"
    assert result["tasks"][0]["binding"]["domain_groups"] == ["reference"]
    assert result["tasks"][1]["binding"] == {
        "status": "UNBOUND",
        "reason": "no_term_index",
    }
    assert result["tasks"][2]["binding"] == {
        "status": "UNBOUND",
        "reason": "no_scores",
    }
    assert result["tasks"][3]["binding"]["reason"] == "no_term_index"
    assert result["tasks"][4]["claim_id"] == "claim-a"
    assert result["binding_policy"] == {"bind_ratio": 0.5, "min_hits": 3.0}
    assert original["tasks"][5]["claim_id"] == "old"


def test_bind_tasks_thresholds_and_non_list_tasks() -> None:
    task = {"term": "signal"}
    term_index = {"signal": {"claim_scores": {"claim": 2.0}, "tot_score": 4.0}}

    below_min_hits, _ = binder.bind_tasks(
        tasks_outbox={"tasks": [task]},
        term_index=term_index,
        bind_ratio=0.4,
        min_hits=2.1,
    )
    below_ratio, _ = binder.bind_tasks(
        tasks_outbox={"tasks": [task]},
        term_index=term_index,
        bind_ratio=0.6,
        min_hits=2.0,
    )
    empty, stats = binder.bind_tasks(
        tasks_outbox={"tasks": "invalid"},
        term_index=term_index,
        bind_ratio=0.6,
        min_hits=2.0,
    )

    for result in (below_min_hits, below_ratio):
        binding = result["tasks"][0]["binding"]
        assert binding["status"] == "UNBOUND"
        assert binding["reason"] == "threshold_fail"
        assert binding["best_claim_id"] == "claim"
    assert empty["tasks"] == []
    assert stats == {"n_in": 0, "n_bound": 0, "n_unbound": 0}


def test_main_uses_latest_tasks_default_output_and_binder_ledger(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    _write_jsonl(
        tmp_path / "out" / "ledger" / "anchor_ledger.jsonl",
        [
            {
                "claim_id": "claim-1",
                "title": "Climate Change science report",
                "domain": "nature.com",
            },
            {
                "claim_id": "claim-1",
                "content_hint": "Climate Change analysis",
                "domain": "reuters.com",
            },
        ],
    )
    _write_json(
        tmp_path / "out" / "reports" / "weather_tasks_a.json",
        {"tasks": [{"id": "old", "term": "older topic"}]},
    )
    _write_json(
        tmp_path / "out" / "reports" / "weather_tasks_z.json",
        {
            "tasks": [
                {"id": "bound-1", "term": "Climate Change"},
                {"id": "bound-2", "term": "Climate Change"},
                {"id": "no-score", "term": "Not present"},
                {"id": "blank", "term": ""},
                "malformed",
            ]
        },
    )
    monkeypatch.setattr(sys, "argv", ["term-claim-binder", "--run-id", "run-1"])

    assert binder.main() == 0

    output = capsys.readouterr().out.strip()
    assert output.startswith("[BINDER] wrote: out/reports/weather_tasks_bound_")
    assert output.endswith("bound=2 unbound=2")
    output_path = output.split("[BINDER] wrote: ", 1)[1].split(" bound=", 1)[0]
    result = json.loads((tmp_path / output_path).read_text(encoding="utf-8"))
    assert result["tasks"][0]["binding"]["status"] == "BOUND"
    assert result["tasks"][0]["claim_id"] == "claim-1"
    assert result["tasks"][2]["binding"]["reason"] == "no_scores"
    assert result["tasks"][3]["binding"]["reason"] == "no_term_index"
    assert result["binding_stats"] == {
        "n_in": 5,
        "n_bound": 2,
        "n_unbound": 2,
    }

    ledger = binder._read_jsonl(str(tmp_path / "out" / "ledger" / "binder_ledger.jsonl"))
    assert len(ledger) == 1
    assert ledger[0]["kind"] == "term_claim_binding"
    assert ledger[0]["run_id"] == "run-1"
    assert ledger[0]["in_tasks"].endswith("weather_tasks_z.json")
    assert ledger[0]["out_tasks"] == output_path
    assert ledger[0]["policy"] == {
        "bind_ratio": 0.62,
        "min_hits": 2.0,
        "max_terms": 40,
    }
    assert ledger[0]["ts"].endswith("+00:00")


def test_main_honors_explicit_paths_and_max_terms(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    anchor_path = _write_jsonl(
        tmp_path / "inputs" / "anchors.jsonl",
        [
            {"claim_id": "claim-a", "title": "Climate Change", "domain": "nature.com"},
            {"claim_id": "claim-b", "title": "Heat Risk", "domain": "reuters.com"},
        ],
    )
    tasks_path = _write_json(
        tmp_path / "inputs" / "tasks.json",
        {
            "tasks": [
                {"id": "first", "term": "Climate Change"},
                {"id": "second", "term": "Heat Risk"},
            ]
        },
    )
    output_path = "out/custom/bound.json"
    binder_ledger = "out/custom/binder.jsonl"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "term-claim-binder",
            "--run-id",
            "run-explicit",
            "--anchor-ledger",
            anchor_path,
            "--tasks",
            tasks_path,
            "--out",
            output_path,
            "--binder-ledger",
            binder_ledger,
            "--bind-ratio",
            "0.5",
            "--min-hits",
            "1",
            "--max-terms",
            "1",
        ],
    )

    assert binder.main() == 0

    assert capsys.readouterr().out.strip() == (
        "[BINDER] wrote: out/custom/bound.json bound=1 unbound=1"
    )
    result = json.loads((tmp_path / output_path).read_text(encoding="utf-8"))
    assert result["tasks"][0]["claim_id"] == "claim-a"
    assert result["tasks"][0]["binding"]["status"] == "BOUND"
    assert result["tasks"][1]["binding"]["reason"] == "no_term_index"
    event = binder._read_jsonl(str(tmp_path / binder_ledger))[0]
    assert event["run_id"] == "run-explicit"
    assert event["policy"]["max_terms"] == 1


def test_main_handles_non_list_tasks_payload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    anchor_path = _write_jsonl(tmp_path / "anchors.jsonl", [])
    tasks_path = _write_json(tmp_path / "tasks.json", {"tasks": "not-a-list"})
    output_path = "custom/empty.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "term-claim-binder",
            "--run-id",
            "run-empty",
            "--anchor-ledger",
            anchor_path,
            "--tasks",
            tasks_path,
            "--out",
            output_path,
            "--binder-ledger",
            "custom/binder.jsonl",
        ],
    )

    assert binder.main() == 0

    assert capsys.readouterr().out.strip() == (
        "[BINDER] wrote: custom/empty.json bound=0 unbound=0"
    )
    result = json.loads((tmp_path / output_path).read_text(encoding="utf-8"))
    assert result["tasks"] == []
    assert result["binding_stats"] == {
        "n_in": 0,
        "n_bound": 0,
        "n_unbound": 0,
    }


def test_main_refuses_when_no_tasks_are_found(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["term-claim-binder", "--run-id", "run-missing"])

    with pytest.raises(SystemExit, match=r"No weather_tasks outbox found\."):
        binder.main()


def test_module_entrypoint_exits_with_main_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    _write_jsonl(
        tmp_path / "anchors.jsonl",
        [{"claim_id": "claim", "title": "climate change"}],
    )
    tasks_path = _write_json(
        tmp_path / "tasks.json",
        {"tasks": [{"id": "task", "term": "climate change"}]},
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "term-claim-binder",
            "--run-id",
            "run-module",
            "--anchor-ledger",
            str(tmp_path / "anchors.jsonl"),
            "--tasks",
            tasks_path,
            "--out",
            "out/module.json",
            "--binder-ledger",
            "out/module-ledger.jsonl",
            "--min-hits",
            "1",
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        runpy.run_path(str(Path(binder.__file__)), run_name="__main__")

    assert exc_info.value.code == 0
    assert "[BINDER] wrote: out/module.json bound=1 unbound=0" in capsys.readouterr().out
