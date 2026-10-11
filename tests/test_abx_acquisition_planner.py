from __future__ import annotations

import json
import runpy
import sys
from pathlib import Path
from typing import Any

import pytest

import abx.acquisition_planner as acquisition_planner


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _all_deficits() -> dict[str, Any]:
    return {
        "claims": {
            "claim-1234567890": {
                "term": "alpha",
                "CSHL_days": 30,
                "TTT_0.8_days": -1,
                "flip_rate": 0.5,
                "latest": {"ML_score": 0.9, "CS_score": 0.4},
            },
            "claim-empty-term": {
                "term": "",
                "CSHL_days": 30,
                "TTT_0.8_days": 5,
                "flip_rate": 0.4,
                "latest": {"ML_score": 0.1},
            },
            "claim-regime": {
                "term": "regime",
                "CSHL_days": 1,
                "TTT_0.8_days": 1,
                "flip_rate": 0.1,
                "latest": {"ML_score": 0.6, "CS_score": 0.7},
            },
            "ignored": "not a claim mapping",
        }
    }


def test_read_latest_clamp_cost_and_uplift_helpers(tmp_path: Path) -> None:
    assert acquisition_planner._utc_now_iso().endswith("+00:00")
    assert acquisition_planner._read_json(str(tmp_path / "missing.json")) == {}
    assert acquisition_planner._read_json(str(tmp_path / "list.json")) == {}
    malformed = tmp_path / "bad.json"
    malformed.write_text("not-json", encoding="utf-8")
    assert acquisition_planner._read_json(str(malformed)) == {}
    valid = tmp_path / "valid.json"
    _write_json(valid, {"ok": True})
    assert acquisition_planner._read_json(str(valid)) == {"ok": True}

    assert acquisition_planner._latest(str(tmp_path), "report-*.json") == ""
    first = tmp_path / "report-001.json"
    second = tmp_path / "report-002.json"
    first.write_text("{}", encoding="utf-8")
    assert acquisition_planner._latest(str(tmp_path), "report-*.json") == str(first)
    second.write_text("{}", encoding="utf-8")
    assert acquisition_planner._latest(str(tmp_path), "report-*.json") == str(second)

    assert acquisition_planner._clamp(-2, 0, 1) == 0.0
    assert acquisition_planner._clamp(0.4, 0, 1) == 0.4
    assert acquisition_planner._clamp(3, 0, 1) == 1.0
    assert acquisition_planner._cost(" offline ") == 0.65
    assert acquisition_planner._cost("decodo") == 0.45
    assert acquisition_planner._cost("online") == 0.35
    assert acquisition_planner._cost("manual") == 0.25
    assert acquisition_planner._cost("other") == 0.40

    assert acquisition_planner._uplift_hint("ADD_PRIMARY_ANCHORS") == {
        "PIS": 0.10,
        "CSHL_days": -3.0,
        "TTT_0.8_days": -2.0,
    }
    assert acquisition_planner._uplift_hint("increase_domain_diversity")["PIS"] == 0.08
    assert acquisition_planner._uplift_hint("ADD_FALSIFICATION_TESTS")["CSHL_days"] == -4.0
    assert acquisition_planner._uplift_hint("FETCH_COUNTERCLAIMS_DISJOINT")["ML_score"] == -0.06
    assert acquisition_planner._uplift_hint("VERIFY_MEDIA_ORIGIN")["PIS"] == 0.06
    assert acquisition_planner._uplift_hint("ENTITY_GROUNDING")["TTT_0.8_days"] == -1.0
    assert acquisition_planner._uplift_hint("unknown") == {}


def test_load_uplift_table_fails_closed_and_reads_calibration(tmp_path: Path) -> None:
    assert acquisition_planner._load_uplift_table(str(tmp_path / "missing.json")) == {}
    list_path = tmp_path / "list.json"
    _write_json(list_path, [])
    assert acquisition_planner._load_uplift_table(str(list_path)) == {}
    no_table = tmp_path / "no-table.json"
    _write_json(no_table, {"other": {}})
    assert acquisition_planner._load_uplift_table(str(no_table)) == {}
    bad = tmp_path / "bad.json"
    bad.write_text("{broken", encoding="utf-8")
    assert acquisition_planner._load_uplift_table(str(bad)) == {}
    calibrated = tmp_path / "calibrated.json"
    table = {"ADD_PRIMARY_ANCHORS": {"PIS": 0.99}}
    _write_json(calibrated, {"table": table})
    assert acquisition_planner._load_uplift_table(str(calibrated)) == table


def test_task_builder_normalizes_priority_cost_and_dependencies() -> None:
    task = acquisition_planner._task(
        claim_id="claim-1234567890",
        term="alpha",
        title="title",
        task_kind="ADD_PRIMARY_ANCHORS",
        mode="online",
        steps=["one"],
        why="because",
        priority=2.0,
        expected_uplift={"PIS": 0.1},
    )
    assert task == {
        "task_id": "claim-1234_add_primary_anchors",
        "claim_id": "claim-1234567890",
        "term": "alpha",
        "title": "title",
        "task_kind": "ADD_PRIMARY_ANCHORS",
        "mode": "online",
        "why": "because",
        "steps": ["one"],
        "depends_on": [],
        "expected_uplift": {"PIS": 0.1},
        "cost": 0.35,
        "priority": 1.0,
        "notes": "Task is an acquisition action. Not executed here. Designed for Decodo/online/offline/manual pipelines.",
    }
    with_dependencies = acquisition_planner._task(
        claim_id="c",
        term="t",
        title="title",
        task_kind="OTHER",
        mode="offline",
        steps=[],
        why="why",
        priority=-1.0,
        expected_uplift={},
        depends_on=["prior-task"],
    )
    assert with_dependencies["depends_on"] == ["prior-task"]
    assert with_dependencies["priority"] == 0.0
    assert with_dependencies["cost"] == 0.65


def test_plan_from_deficits_emits_all_relevant_task_kinds_and_rankings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calibrated = {"ADD_FALSIFICATION_TESTS": {"PIS": 0.99}}
    monkeypatch.setattr(acquisition_planner, "_load_uplift_table", lambda: calibrated)
    plan = acquisition_planner.plan_from_deficits(
        time_to_truth=_all_deficits(),
        sig_kpi={
            "PDG": {
                "avg_unique_domains_per_term": 2.0,
                "avg_primary_anchor_ratio": 0.1,
                "avg_falsification_tests_per_term": 0.0,
            }
        },
        proof_integrity={"PIS": 0.2},
        regime_shift={"regime_shift": True},
        max_tasks_per_claim=6,
    )

    assert plan["version"] == "acquisition_plan.v0.1"
    assert plan["ts"].endswith("+00:00")
    assert plan["globals"] == {
        "PIS": 0.2,
        "avg_unique_domains_per_term": 2.0,
        "avg_primary_anchor_ratio": 0.1,
        "avg_falsification_tests_per_term": 0.0,
        "regime_shift": True,
    }
    assert plan["n_tasks"] == len(plan["tasks"]) == 12
    assert "temporal stabilization deficits" in plan["notes"]

    alpha = [task for task in plan["tasks"] if task["claim_id"] == "claim-1234567890"]
    assert [task["task_kind"] for task in alpha] == [
        "ADD_FALSIFICATION_TESTS",
        "FETCH_COUNTERCLAIMS_DISJOINT",
        "INCREASE_DOMAIN_DIVERSITY",
        "ADD_PRIMARY_ANCHORS",
        "VERIFY_MEDIA_ORIGIN",
        "ENTITY_GROUNDING",
    ]
    assert alpha[0]["task_id"] == "claim-1234_add_falsification_tests"
    assert alpha[0]["expected_uplift"] == calibrated["ADD_FALSIFICATION_TESTS"]
    assert alpha[1]["expected_uplift"] == acquisition_planner._uplift_hint(
        "FETCH_COUNTERCLAIMS_DISJOINT"
    )
    assert all(
        first["priority"] - 0.25 * first["cost"] >= second["priority"] - 0.25 * second["cost"]
        for first, second in zip(plan["tasks"], plan["tasks"][1:], strict=False)
    )
    assert "claim-empty-term" not in {
        task["claim_id"] for task in plan["tasks"] if task["task_kind"] == "ENTITY_GROUNDING"
    }
    assert {task["task_kind"] for task in plan["tasks"] if task["claim_id"] == "claim-regime"} == {
        "ADD_PRIMARY_ANCHORS",
        "FETCH_COUNTERCLAIMS_DISJOINT",
        "VERIFY_MEDIA_ORIGIN",
    }


def test_plan_handles_invalid_shapes_regime_threshold_and_per_claim_cap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(acquisition_planner, "_load_uplift_table", lambda: {})
    empty = acquisition_planner.plan_from_deficits(
        time_to_truth={"claims": []},
        sig_kpi={"PDG": []},
        proof_integrity=[],  # type: ignore[arg-type]
        regime_shift=[],  # type: ignore[arg-type]
    )
    assert empty["globals"] == {
        "PIS": 0.0,
        "avg_unique_domains_per_term": 0.0,
        "avg_primary_anchor_ratio": 0.0,
        "avg_falsification_tests_per_term": 0.0,
        "regime_shift": False,
    }
    assert empty["tasks"] == []

    claims = {
        "unstable-zero": {
            "term": "zero",
            "CSHL_days": 0,
            "TTT_0.8_days": 4,
            "flip_rate": 0,
            "latest": "bad",
        },
        "polluted-regime": {
            "term": "polluted",
            "CSHL_days": 2,
            "TTT_0.8_days": 2,
            "flip_rate": 0.1,
            "latest": {"ML_score": 0.6},
        },
    }
    plan = acquisition_planner.plan_from_deficits(
        time_to_truth={"claims": claims},
        sig_kpi={
            "PDG": {
                "avg_unique_domains_per_term": 10,
                "avg_primary_anchor_ratio": 0.8,
                "avg_falsification_tests_per_term": 0.9,
            }
        },
        proof_integrity={"PIS": 0.9},
        regime_shift={"regime_shift": True},
        max_tasks_per_claim=2,
    )
    assert {task["task_kind"] for task in plan["tasks"] if task["claim_id"] == "unstable-zero"} == {
        "ADD_FALSIFICATION_TESTS",
        "ENTITY_GROUNDING",
    }
    assert {
        task["task_kind"] for task in plan["tasks"] if task["claim_id"] == "polluted-regime"
    } == {
        "FETCH_COUNTERCLAIMS_DISJOINT",
        "VERIFY_MEDIA_ORIGIN",
    }
    assert plan["n_tasks"] == 4


def test_main_requires_time_to_truth_report(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["acquisition_planner"])
    with pytest.raises(SystemExit, match="No time_to_truth report found"):
        acquisition_planner.main()


def test_main_discovers_latest_inputs_and_writes_default_output(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    reports = tmp_path / "out" / "reports"
    _write_json(
        reports / "time_to_truth_001.json", {"claims": {"old": {"term": "old", "CSHL_days": 0}}}
    )
    _write_json(
        reports / "time_to_truth_002.json", {"claims": {"new": {"term": "new", "CSHL_days": 0}}}
    )
    _write_json(reports / "sig_kpi_001.json", {"PDG": {"avg_falsification_tests_per_term": 0}})
    _write_json(reports / "proof_integrity_001.json", {"PIS": 0.1})
    _write_json(reports / "regime_shift_001.json", {"regime_shift": False})
    _write_json(tmp_path / "out" / "config" / "uplift_table.json", {"table": {}})
    monkeypatch.setattr(sys, "argv", ["acquisition_planner"])

    assert acquisition_planner.main() == 0

    outputs = sorted(reports.glob("acquisition_plan_*.json"))
    assert len(outputs) == 1
    report = json.loads(outputs[0].read_text(encoding="utf-8"))
    assert {task["term"] for task in report["tasks"]} == {"new"}
    assert report["n_tasks"] > 0
    assert capsys.readouterr().out == f"[ACQ_PLAN] wrote: out/reports/{outputs[0].name}\n"


def test_module_entrypoint_runs_with_explicit_input_and_default_output(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    reports = tmp_path / "inputs"
    ttt = reports / "ttt.json"
    _write_json(ttt, {"claims": {}})
    monkeypatch.setattr(sys, "argv", ["acquisition_planner", "--time-to-truth", str(ttt)])

    with pytest.raises(SystemExit) as exc_info:
        runpy.run_path(acquisition_planner.__file__, run_name="__main__")

    assert exc_info.value.code == 0
    assert len(list((tmp_path / "out" / "reports").glob("acquisition_plan_*.json"))) == 1
