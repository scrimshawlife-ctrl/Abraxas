from __future__ import annotations

import json
import runpy
import sys
from pathlib import Path
from typing import Any

import pytest

import abx.signal_roi_scheduler as roi


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _task(
    task_id: str,
    *,
    run_id: str = "run-1",
    term: str = "claim",
    task_type: str = "PRIMARY_ANCHOR_SWEEP",
) -> dict[str, Any]:
    return {"task_id": task_id, "run_id": run_id, "term": term, "task_type": task_type}


def test_utc_timestamp_is_utc_with_second_precision() -> None:
    timestamp = roi._utc_now_iso()

    assert timestamp.endswith("+00:00")
    assert "." not in timestamp


def test_read_json_returns_only_objects_and_fails_closed(tmp_path: Path) -> None:
    valid = tmp_path / "valid.json"
    valid.write_text('{"answer": 42}', encoding="utf-8")
    non_object = tmp_path / "list.json"
    non_object.write_text("[1, 2]", encoding="utf-8")
    malformed = tmp_path / "malformed.json"
    malformed.write_text("{not-json", encoding="utf-8")

    assert roi._read_json(str(valid)) == {"answer": 42}
    assert roi._read_json(str(non_object)) == {}
    assert roi._read_json(str(malformed)) == {}
    assert roi._read_json(str(tmp_path / "missing.json")) == {}


def test_latest_selects_last_sorted_match_or_empty_string(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    _write_json(reports / "calibration_tasks_2026-01.json", {"tasks": []})
    _write_json(reports / "calibration_tasks_2026-02.json", {"tasks": []})
    _write_json(reports / "unrelated.json", {})

    assert roi._latest(str(reports), "calibration_tasks_*.json") == str(
        reports / "calibration_tasks_2026-02.json"
    )
    assert roi._latest(str(reports), "roi_weights_*.json") == ""


@pytest.mark.parametrize(
    ("task", "decodo_available", "multiplier", "expected"),
    [
        ({"task_type": "PRIMARY_ANCHOR_SWEEP", "mode": "offline"}, False, 2.0, (1.2, 12)),
        ({"task_type": "unlisted", "mode": "offline"}, False, 2.0, (0.6, 12)),
        ({"task_type": "DISCONFIRM_TESTS", "mode": "online"}, False, 2.0, (0.0125, 12)),
        ({"task_type": "PRIMARY_ANCHOR_SWEEP", "mode": "online"}, True, 1.5, (1.8, 8)),
    ],
)
def test_estimate_cost_applies_task_defaults_and_online_modes(
    task: dict[str, Any], decodo_available: bool, multiplier: float, expected: tuple[float, int]
) -> None:
    cost = roi.estimate_cost(task, decodo_available=decodo_available, decodo_multiplier=multiplier)

    assert cost[0] == pytest.approx(expected[0])
    assert cost[1] == expected[1]


def test_estimate_cost_enforces_three_minute_online_floor(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(roi.TASK_COSTS, "LOW_MANUAL", {"usd": 0.1, "manual_min": 2})

    assert roi.estimate_cost(
        {"task_type": "LOW_MANUAL", "mode": "online"},
        decodo_available=True,
        decodo_multiplier=1.0,
    ) == (0.1, 3)


def test_expected_gain_uses_learned_feature_weights() -> None:
    task = {
        "dominant_driver": "PROV_GAP",
        "task_type": "PRIMARY_ANCHOR_SWEEP",
        "ml": {"ml": 0.5, "bucket": "COORDINATED"},
        "evidence": {"anchors_added": 2, "domains_added": 3, "fals_tests_added": 4},
    }
    model = {
        "weights": {
            "bias": 0.1,
            "ml_score": 0.2,
            "dom_PROV_GAP": 0.3,
            "tt_PRIMARY": 0.4,
            "bucket_MFG": 0.1,
            "anchors_added": 0.05,
            "domains_added": 0.02,
            "fals_tests_added": 0.03,
        }
    }

    assert roi.expected_sig_gain(task, learned=model) == pytest.approx(1.28)


@pytest.mark.parametrize(("bias", "expected"), [(2.0, 1.4), (-2.0, 0.0)])
def test_expected_gain_learned_model_clamps_score(bias: float, expected: float) -> None:
    assert roi.expected_sig_gain({}, learned={"weights": {"bias": bias}}) == expected


@pytest.mark.parametrize(
    ("task", "expected"),
    [
        (
            {
                "dominant_driver": "FOG",
                "task_type": "ORIGIN_TIMELINE",
                "term_tpi": 0.0,
                "ml": {"ml": 0.0, "bucket": "LOW_RISK"},
            },
            0.4835,
        ),
        (
            {
                "dominant_driver": "TPL",
                "task_type": "TEMPLATE_CAPTURE",
                "term_tpi": 0.5,
                "ml": {"ml": 0.7, "bucket": "MIXED"},
            },
            0.9065,
        ),
        (
            {
                "dominant_driver": "FOG",
                "task_type": "SYNC_POSTING_CHECK",
                "term_tpi": 0.5,
                "ml": {"ml": 0.7, "bucket": "NORMAL"},
            },
            0.9298125,
        ),
        (
            {
                "dominant_driver": "SYN",
                "task_type": "AUTH_CHAIN",
                "term_tpi": 0.0,
                "ml": {"ml": 0.0, "bucket": "NORMAL"},
            },
            0.3868,
        ),
        (
            {
                "task_type": "DISCONFIRM_TESTS",
                "term_tpi": -2.0,
                "ml": {"ml": -1.0, "bucket": "OTHER"},
            },
            0.289,
        ),
        (
            {
                "dominant_driver": "UNCLASSIFIED",
                "task_type": "OTHER",
                "term_tpi": 1.5,
                "ml": {"ml": -1.0, "bucket": "ASTROTURF"},
            },
            0.798,
        ),
        (
            {
                "dominant_driver": "PROV_GAP",
                "task_type": "PRIMARY_ANCHOR_SWEEP",
                "term_tpi": 1.0,
                "ml": {"ml": 1.0, "bucket": "LIKELY_MANUFACTURED"},
            },
            1.4,
        ),
    ],
)
def test_expected_gain_heuristic_alignments_buckets_and_clamps(
    task: dict[str, Any], expected: float
) -> None:
    assert roi.expected_sig_gain(task, learned={"weights": []}) == pytest.approx(expected)


def test_score_task_returns_cost_gain_roi_and_explanation() -> None:
    task = {
        **_task("auth", task_type="AUTH_CHAIN"),
        "dominant_driver": "SYN",
        "term_tpi": 0.0,
        "ml": {"ml": 0.0, "bucket": "NORMAL"},
    }

    scored = roi.score_task(
        task,
        decodo_available=False,
        decodo_multiplier=1.25,
        lambda_manual=0.1,
    )

    assert scored["cost"] == {"usd": 1.0, "manual_min": 14, "lambda_manual": 0.1}
    assert scored["expected_gain"] == pytest.approx(0.3868)
    assert scored["roi"] == pytest.approx(0.1611665995)
    assert scored["reason"] == {
        "dominant_driver": "SYN",
        "term_tpi": 0.0,
        "ml_bucket": "NORMAL",
        "ml_score": 0.0,
        "task_type": "AUTH_CHAIN",
    }


def test_build_roi_plan_ranks_and_enforces_budget_duplicates_manual_and_task_limit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    reports = tmp_path / "reports"
    _write_json(reports / "calibration_tasks_001.json", {"tasks": [_task("stale")]})
    tasks = [
        _task("first", term="shared"),
        _task("duplicate", term="shared"),
        _task("over-budget", term="budget", task_type="ORIGIN_TIMELINE"),
        _task("over-manual", term="manual", task_type="TEMPLATE_CAPTURE"),
        _task("second", term="free", task_type="SYNC_POSTING_CHECK"),
        _task("late", term="late", task_type="AUTH_CHAIN"),
        "malformed-task",
    ]
    _write_json(reports / "calibration_tasks_002.json", {"tasks": tasks})
    _write_json(reports / "roi_weights_001.json", {"version": "old"})
    _write_json(reports / "roi_weights_002.json", {"version": "learned-v2"})
    metrics = {
        "first": (10, {"usd": 2.0, "manual_min": 5}),
        "duplicate": (9, {"usd": 1.0, "manual_min": 1}),
        "over-budget": (8, {"usd": 100.0, "manual_min": 1}),
        "over-manual": (7, {"usd": 1.0, "manual_min": 100}),
        "second": (6, None),
        "late": (5, {"usd": 0.0, "manual_min": 0}),
    }

    def fake_score_task(
        task: dict[str, Any],
        *,
        decodo_available: bool,
        decodo_multiplier: float,
        lambda_manual: float,
        learned_model: dict[str, Any] | None,
    ) -> dict[str, Any]:
        assert decodo_available is False
        assert decodo_multiplier == 1.5
        assert lambda_manual == 0.1
        assert learned_model == {"version": "learned-v2"}
        score, cost = metrics[task["task_id"]]
        return {**task, "roi": score, "expected_gain": score / 10, "cost": cost}

    monkeypatch.setattr(roi, "score_task", fake_score_task)

    plan = roi.build_roi_plan(
        out_reports=str(reports),
        budget_usd=3.0,
        max_manual_minutes=10,
        max_tasks=2,
        decodo_available=False,
        decodo_multiplier=1.5,
        lambda_manual=0.1,
    )

    assert plan["inputs"]["tasks_source"] == str(reports / "calibration_tasks_002.json")
    assert plan["learned_model"] == {
        "path": str(reports / "roi_weights_002.json"),
        "version": "learned-v2",
    }
    assert [task["task_id"] for task in plan["ranked_top"]] == [
        "first",
        "duplicate",
        "over-budget",
        "over-manual",
        "second",
        "late",
    ]
    assert [task["task_id"] for task in plan["selected"]] == ["first", "second"]
    assert plan["summary"] == {
        "n_tasks_total": 6,
        "n_selected": 2,
        "usd_spent": 2.0,
        "manual_minutes": 5,
    }


def test_build_roi_plan_handles_malformed_task_collection_and_missing_files(
    tmp_path: Path,
) -> None:
    reports = tmp_path / "reports"
    _write_json(reports / "calibration_tasks_latest.json", {"tasks": "not-a-list"})

    plan = roi.build_roi_plan(
        out_reports=str(reports),
        budget_usd=0.0,
        max_manual_minutes=0,
        max_tasks=0,
        decodo_available=False,
        decodo_multiplier=1.25,
        lambda_manual=0.03,
    )

    assert plan["inputs"]["tasks_source"] == str(reports / "calibration_tasks_latest.json")
    assert plan["learned_model"] is None
    assert plan["summary"] == {
        "n_tasks_total": 0,
        "n_selected": 0,
        "usd_spent": 0.0,
        "manual_minutes": 0,
    }
    assert plan["selected"] == []
    assert plan["ranked_top"] == []


def test_build_roi_plan_stops_immediately_when_max_tasks_is_zero(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    _write_json(reports / "calibration_tasks_latest.json", {"tasks": [_task("limited")]})

    plan = roi.build_roi_plan(
        out_reports=str(reports),
        budget_usd=10.0,
        max_manual_minutes=100,
        max_tasks=0,
        decodo_available=False,
        decodo_multiplier=1.25,
        lambda_manual=0.03,
    )

    assert plan["summary"]["n_tasks_total"] == 1
    assert plan["selected"] == []


def test_to_markdown_formats_selected_rows_and_empty_fallbacks() -> None:
    markdown = roi.to_markdown(
        {
            "summary": {"n_selected": 1, "n_tasks_total": 2, "usd_spent": 1.5, "manual_minutes": 7},
            "selected": [
                {
                    "run_id": "run-1",
                    "term": "claim",
                    "task_type": "PRIMARY_ANCHOR_SWEEP",
                    "dominant_driver": "PROV_GAP",
                    "roi": 0.5,
                    "expected_gain": 1.0,
                    "cost": {"usd": 1.5, "manual_min": 7},
                },
                {"run_id": "run-2", "term": "other", "cost": "malformed"},
            ],
        }
    )

    assert "selected: **1** / 2" in markdown
    assert "spent: **$1.50**" in markdown
    assert (
        "| 1 | run-1 | claim | PRIMARY_ANCHOR_SWEEP | PROV_GAP | 0.5000 | 1.000 | 1.50 | 7 |"
        in markdown
    )
    assert "| 2 | run-2 | other |  |  | 0.0000 | 0.000 | 0.00 | 0 |" in markdown
    assert "This does not execute tasks." in markdown

    empty_markdown = roi.to_markdown({"summary": None, "selected": "not-a-list"})
    assert "selected: **0** / 0" in empty_markdown
    assert (
        "| rank | run_id | term | task_type | driver | roi | gain | usd | min |" in empty_markdown
    )


def test_cli_entrypoint_writes_default_json_and_markdown_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    reports = tmp_path / "reports"
    _write_json(
        reports / "calibration_tasks_001.json",
        {
            "tasks": [
                {
                    **_task("cli-task"),
                    "mode": "online",
                    "dominant_driver": "PROV_GAP",
                    "term_tpi": 1.0,
                    "ml": {"ml": 0.9, "bucket": "LIKELY_MANUFACTURED"},
                }
            ]
        },
    )
    _write_json(reports / "roi_weights_001.json", {"version": "weights-v1"})
    monkeypatch.setattr(
        sys,
        "argv",
        ["signal_roi_scheduler", "--out-reports", str(reports), "--decodo-available"],
    )

    with pytest.raises(SystemExit) as raised:
        runpy.run_path(str(Path(roi.__file__).resolve()), run_name="__main__")

    assert raised.value.code == 0
    json_outputs = list(reports.glob("signal_roi_plan_*.json"))
    markdown_outputs = list(reports.glob("signal_roi_plan_*.md"))
    assert len(json_outputs) == len(markdown_outputs) == 1
    plan = json.loads(json_outputs[0].read_text(encoding="utf-8"))
    assert plan["inputs"]["decodo_available"] is True
    assert plan["learned_model"]["version"] == "weights-v1"
    assert plan["summary"]["n_selected"] == 1
    assert "[ROI_PLAN] wrote:" in capsys.readouterr().out
    assert markdown_outputs[0].read_text(encoding="utf-8").startswith("# Signal ROI Plan\n")
