from __future__ import annotations

import json
import runpy
import sys
from pathlib import Path
from typing import Any

import pytest

import abx.attribution_delta as attribution_delta


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _run_main(
    monkeypatch: pytest.MonkeyPatch,
    *,
    attr_graph: Path,
    before: Path,
    after: Path,
    output: Path | None = None,
    uplift: Path | None = None,
) -> int:
    argv = [
        "attribution_delta",
        "--attr-graph",
        str(attr_graph),
        "--ttt-before",
        str(before),
        "--ttt-after",
        str(after),
    ]
    if output is not None:
        argv.extend(["--out", str(output)])
    if uplift is not None:
        argv.extend(["--uplift-out", str(uplift)])
    monkeypatch.setattr(sys, "argv", argv)
    return attribution_delta.main()


def test_read_json_report_selection_and_numeric_helpers(tmp_path: Path) -> None:
    malformed = tmp_path / "malformed.json"
    malformed.write_text("{bad", encoding="utf-8")
    list_payload = tmp_path / "list.json"
    _write_json(list_payload, [1, 2])
    valid = tmp_path / "valid.json"
    _write_json(valid, {"ok": True})

    assert attribution_delta._read_json(str(tmp_path / "missing.json")) == {}
    assert attribution_delta._read_json(str(malformed)) == {}
    assert attribution_delta._read_json(str(list_payload)) == {}
    assert attribution_delta._read_json(str(valid)) == {"ok": True}

    pattern = str(tmp_path / "report_*.json")
    assert attribution_delta._latest(pattern) == ""
    assert attribution_delta._prev(pattern) == ""
    first = tmp_path / "report_001.json"
    second = tmp_path / "report_002.json"
    first.write_text("{}", encoding="utf-8")
    assert attribution_delta._latest(pattern) == str(first)
    assert attribution_delta._prev(pattern) == ""
    second.write_text("{}", encoding="utf-8")
    assert attribution_delta._latest(pattern) == str(second)
    assert attribution_delta._prev(pattern) == str(first)

    assert attribution_delta._f("2.5") == 2.5
    assert attribution_delta._f("bad", -4) == -4.0
    assert attribution_delta._delta(1.25, 3.75) == 2.5


def test_claim_delta_covers_present_and_missing_metrics() -> None:
    delta = attribution_delta.claim_delta(
        {
            "CSHL_days": 10,
            "TTT_0.8_days": 8,
            "flip_rate": 0.5,
            "latest": {"CS_score": 0.2, "ML_score": 0.3},
        },
        {
            "CSHL_days": 8,
            "TTT_0.8_days": 6,
            "flip_rate": 0.25,
            "latest": {"CS_score": 0.6, "ML_score": 0.9},
        },
    )
    assert delta == {
        "d_CSHL_days": -2.0,
        "d_TTT_0.8_days": -2.0,
        "d_flip_rate": -0.25,
        "d_CS_latest": pytest.approx(0.4),
        "d_ML_latest": pytest.approx(0.6),
    }
    assert attribution_delta.claim_delta({}, {"latest": None}) == {
        "d_CSHL_days": 0.0,
        "d_TTT_0.8_days": 0.0,
        "d_flip_rate": 0.0,
        "d_CS_latest": 0.0,
        "d_ML_latest": 0.0,
    }


def test_main_rejects_missing_graph_or_truth_reports(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["attribution_delta"])
    with pytest.raises(SystemExit, match="No attribution_graph found"):
        attribution_delta.main()

    graph = tmp_path / "graph.json"
    _write_json(graph, {"tasks": []})
    one_report = tmp_path / "out" / "reports" / "time_to_truth_001.json"
    _write_json(one_report, {"claims": {}})
    monkeypatch.setattr(sys, "argv", ["attribution_delta", "--attr-graph", str(graph)])
    with pytest.raises(SystemExit, match="Need at least two time_to_truth reports"):
        attribution_delta.main()


def test_main_weights_claim_deltas_and_writes_both_reports(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    graph = tmp_path / "input" / "graph.json"
    before = tmp_path / "input" / "before.json"
    after = tmp_path / "input" / "after.json"
    output = tmp_path / "nested" / "attribution-delta.json"
    uplift = tmp_path / "config" / "uplift.json"
    _write_json(
        graph,
        {
            "tasks": [
                {
                    "task_id": "a",
                    "meta": {"task_kind": "type_a"},
                    "claims_touched": ["c1", "", None],
                    "n_edges": 3,
                },
                {
                    "task_id": "b",
                    "meta": {"task_kind": " type_b "},
                    "claims_touched": ["c1"],
                    "n_edges": 1,
                },
                {
                    "task_id": "c",
                    "meta": {"task_kind": "TYPE_A"},
                    "claims_touched": ["c2"],
                    "n_edges": 2,
                },
                {"task_id": "blank", "claims_touched": ["c1"], "n_edges": 1},
                {"task_id": "ignored", "meta": "not-an-object", "claims_touched": "not-a-list"},
                "not-an-object",
            ]
        },
    )
    _write_json(
        before,
        {
            "claims": {
                "c1": {
                    "CSHL_days": 10,
                    "TTT_0.8_days": 8,
                    "flip_rate": 0.5,
                    "latest": {"CS_score": 0.2, "ML_score": 0.3},
                },
                "c2": {"CSHL_days": 0, "TTT_0.8_days": 1},
                "orphan": {"CSHL_days": 0},
                "before_only": {},
                "bad": "not-an-object",
            }
        },
    )
    _write_json(
        after,
        {
            "claims": {
                "c1": {
                    "CSHL_days": 8,
                    "TTT_0.8_days": 6,
                    "flip_rate": 0.25,
                    "latest": {"CS_score": 0.6, "ML_score": 0.9},
                },
                "c2": {"CSHL_days": 4, "TTT_0.8_days": 3},
                "orphan": {"CSHL_days": 2},
                "after_only": {},
                "bad": {},
            }
        },
    )

    assert (
        _run_main(
            monkeypatch,
            attr_graph=graph,
            before=before,
            after=after,
            output=output,
            uplift=uplift,
        )
        == 0
    )

    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["version"] == "attribution_delta.v0.1"
    assert report["inputs"] == {
        "attr_graph": str(graph),
        "ttt_before": str(before),
        "ttt_after": str(after),
    }
    assert report["ts"].endswith("+00:00")
    assert report["n_claims_with_deltas"] == 3
    assert report["uplift_table"]["TYPE_A"]["d_CSHL_days"] == pytest.approx(1.4)
    assert report["uplift_table"]["TYPE_A"]["n_samples"] == 2.0
    assert report["uplift_table"]["TYPE_B"]["d_CSHL_days"] == pytest.approx(-0.4)
    assert report["uplift_table"]["TYPE_B"]["n_samples"] == 1.0
    assert [entry["task_id"] for entry in report["per_task_credit"]] == ["a", "b", "c"]
    assert [entry["weight"] for entry in report["per_task_credit"]] == [
        pytest.approx(0.6),
        pytest.approx(0.2),
        pytest.approx(1.0),
    ]
    assert "Edge-weighted attribution" in report["notes"]

    uplift_report = json.loads(uplift.read_text(encoding="utf-8"))
    assert uplift_report["version"] == "uplift_table.v0.2"
    assert uplift_report["table"] == report["uplift_table"]
    captured = capsys.readouterr().out
    assert captured == f"[ATTR_DELTA] wrote: {output}\n[ATTR_DELTA] wrote uplift_table: {uplift}\n"


def test_main_defaults_to_latest_reports_and_empty_tables(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    reports = tmp_path / "out" / "reports"
    reports.mkdir(parents=True)
    graph = reports / "attribution_graph_001.json"
    before = reports / "time_to_truth_001.json"
    after = reports / "time_to_truth_002.json"
    _write_json(graph, {"tasks": "invalid"})
    before.write_text("not-json", encoding="utf-8")
    _write_json(after, {"claims": []})
    monkeypatch.setattr(sys, "argv", ["attribution_delta"])

    assert attribution_delta.main() == 0

    reports_written = sorted(reports.glob("attribution_delta_*.json"))
    assert len(reports_written) == 1
    report = json.loads(reports_written[0].read_text(encoding="utf-8"))
    assert report["inputs"] == {
        "attr_graph": "out/reports/attribution_graph_001.json",
        "ttt_before": "out/reports/time_to_truth_001.json",
        "ttt_after": "out/reports/time_to_truth_002.json",
    }
    assert report["n_claims_with_deltas"] == 0
    assert report["uplift_table"] == {}
    assert report["per_task_credit"] == []
    assert (tmp_path / "out" / "config" / "uplift_table.json").exists()
    assert capsys.readouterr().out.startswith("[ATTR_DELTA] wrote: out/reports/attribution_delta_")


def test_main_caps_per_task_credit_at_500(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    graph = tmp_path / "graph.json"
    before = tmp_path / "before.json"
    after = tmp_path / "after.json"
    output = tmp_path / "report.json"
    uplift = tmp_path / "uplift.json"
    _write_json(
        graph,
        {
            "tasks": [
                {
                    "task_id": f"task-{i}",
                    "meta": {"task_kind": "bulk"},
                    "claims_touched": ["shared"],
                    "n_edges": 1,
                }
                for i in range(501)
            ]
        },
    )
    _write_json(before, {"claims": {"shared": {"CSHL_days": 1}}})
    _write_json(after, {"claims": {"shared": {"CSHL_days": 2}}})

    _run_main(
        monkeypatch,
        attr_graph=graph,
        before=before,
        after=after,
        output=output,
        uplift=uplift,
    )
    report = json.loads(output.read_text(encoding="utf-8"))
    assert len(report["per_task_credit"]) == 500
    assert report["uplift_table"]["BULK"]["n_samples"] == 501.0


def test_module_entrypoint_runs_cli(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    graph = tmp_path / "graph.json"
    before = tmp_path / "before.json"
    after = tmp_path / "after.json"
    output = tmp_path / "nested" / "report.json"
    uplift = tmp_path / "nested" / "uplift.json"
    _write_json(graph, {"tasks": []})
    _write_json(before, {"claims": {}})
    _write_json(after, {"claims": {}})
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "attribution_delta",
            "--attr-graph",
            str(graph),
            "--ttt-before",
            str(before),
            "--ttt-after",
            str(after),
            "--out",
            str(output),
            "--uplift-out",
            str(uplift),
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        runpy.run_path(attribution_delta.__file__, run_name="__main__")
    assert exc_info.value.code == 0

    assert json.loads(output.read_text(encoding="utf-8"))["uplift_table"] == {}
    assert json.loads(uplift.read_text(encoding="utf-8"))["table"] == {}
