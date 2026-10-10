from __future__ import annotations

import json
import runpy
import sys
from pathlib import Path
from typing import Any

import pytest

import abx.error_attrib_tasks as error_attrib_tasks


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_read_json_fails_closed_and_norm_canonicalizes_separators(tmp_path: Path) -> None:
    missing = tmp_path / "missing.json"
    malformed = tmp_path / "malformed.json"
    non_object = tmp_path / "list.json"
    valid = tmp_path / "valid.json"
    malformed.write_text("{bad", encoding="utf-8")
    _write_json(non_object, ["not", "an", "object"])
    _write_json(valid, {"ok": True})

    assert error_attrib_tasks._read_json(str(missing)) == {}
    assert error_attrib_tasks._read_json(str(malformed)) == {}
    assert error_attrib_tasks._read_json(str(non_object)) == {}
    assert error_attrib_tasks._read_json(str(valid)) == {"ok": True}
    assert error_attrib_tasks._norm("  Mixed__Case-term  ") == "mixed case term"
    assert error_attrib_tasks._norm("") == ""


def test_latest_and_recent_run_ids_sort_names_and_apply_requested_window(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    reports.mkdir()
    for name in ("tpi_run-b.json", "tpi_run-a.json", "tpi_run-c.json"):
        (reports / name).write_text("{}", encoding="utf-8")
    for name in ("calibration_report_b.json", "calibration_report_a.json"):
        (reports / name).write_text("{}", encoding="utf-8")

    assert error_attrib_tasks._latest(str(reports), "calibration_report_*.json").endswith(
        "calibration_report_b.json"
    )
    assert error_attrib_tasks._latest(str(reports), "missing_*.json") == ""
    assert error_attrib_tasks._pick_recent_run_ids(str(reports), n=2) == ["run-b", "run-c"]
    assert error_attrib_tasks._pick_recent_run_ids(str(reports), n=8) == [
        "run-a",
        "run-b",
        "run-c",
    ]
    assert error_attrib_tasks._pick_recent_run_ids(str(tmp_path / "empty")) == []


def test_generate_tasks_returns_empty_shape_when_reports_are_missing(tmp_path: Path) -> None:
    result = error_attrib_tasks.generate_tasks(str(tmp_path / "missing"))

    assert result["version"] == "calibration_tasks.v0.1"
    assert result["calibration_report"] == ""
    assert result["slang_drift"] == ""
    assert result["best_params"] == {}
    assert result["recent_runs"] == []
    assert result["tasks"] == []
    assert result["out_reports"] == str(tmp_path / "missing")
    assert result["ts"].endswith("+00:00")


def test_generate_tasks_maps_drivers_and_limits_recent_runs_and_top_terms(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    _write_json(
        reports / "calibration_report_2026.json",
        {"best": {"learning_rate": 0.2, "depth": 3}},
    )
    _write_json(
        reports / "slang_drift_2026.json",
        {
            "terms": [
                None,
                {"canonical_term": "   ", "variants": [""]},
                {
                    "canonical_term": "Alpha",
                    "variants": ["alpha_alias"],
                    "manufacture": {"ml_score": 0.1, "bucket": "LOW", "signals": ["signal-a"]},
                },
                {
                    "canonical_term": "Epsilon",
                    "variants": "not-a-list",
                    "manufacture": {"ml_score": 0.8, "bucket": "HIGH", "signals": ["signal-e"]},
                },
                {
                    "canonical_term": "unused",
                    "variants": None,
                    "manufacture": "not-an-object",
                },
            ]
        },
    )
    _write_json(reports / "tpi_run-a.json", {"run_tpi": 0.9, "per_term": {"old": {"tpi": 1.0}}})
    _write_json(reports / "tpi_run-b.json", {"run_tpi": 0.2, "per_term": ["malformed"]})
    _write_json(
        reports / "tpi_run-c.json",
        {
            "run_tpi": 0.45,
            "per_term": {
                "alpha_alias": {
                    "tpi": 0.99,
                    "components": {
                        "synthetic_density": 0.9,
                        "provenance_integrity_mean": 0.95,
                        "template_pressure": 0.1,
                        "fog_flags": {},
                    },
                },
                "Beta": {
                    "tpi": 0.9,
                    "components": {
                        "synthetic_density": 0.1,
                        "provenance_integrity_mean": 0.99,
                        "template_pressure": 0.9,
                        "fog_flags": {},
                    },
                },
                "Gamma": {
                    "tpi": 0.8,
                    "components": {
                        "synthetic_density": 0.1,
                        "provenance_integrity_mean": 0.05,
                        "template_pressure": 0.2,
                        "fog_flags": {},
                    },
                },
                "Delta": {
                    "tpi": 0.7,
                    "components": {
                        "synthetic_density": 0.1,
                        "provenance_integrity_mean": 0.95,
                        "template_pressure": 0.2,
                        "fog_flags": {
                            "OP_FOG": 1,
                            "FORK_STORM": 1,
                            "PROVENANCE_DROUGHT": 1,
                        },
                    },
                },
                "Epsilon": {
                    "tpi": 0.6,
                    "components": {
                        "synthetic_density": 0.25,
                        "provenance_integrity_mean": 0.95,
                        "template_pressure": 0.1,
                        "fog_flags": {},
                    },
                },
                "Zeta": None,
                "Eta": {"tpi": 0.0, "components": "not-an-object"},
            },
        },
    )

    result = error_attrib_tasks.generate_tasks(str(reports), recent_n=2)

    assert result["best_params"] == {"learning_rate": 0.2, "depth": 3}
    assert result["recent_runs"][0] == {"run_id": "run-b", "run_tpi": 0.2, "top_terms": []}
    high_run = result["recent_runs"][1]
    assert high_run["run_id"] == "run-c"
    assert len(high_run["top_terms"]) == 7
    assert [term["term"] for term in high_run["top_terms"]][-2:] == ["Zeta", "Eta"]
    assert {task["dominant_driver"] for task in result["tasks"]} == {
        "SYN",
        "TPL",
        "PROV_GAP",
        "FOG",
    }
    assert len(result["tasks"]) == 14

    alpha_task = next(task for task in result["tasks"] if task["term"] == "alpha_alias")
    assert alpha_task["ml"] == {
        "canonical": "Alpha",
        "ml": 0.1,
        "bucket": "LOW",
        "signals": ["signal-a"],
    }
    assert {task["task_type"] for task in result["tasks"] if task["term"] == "Beta"} == {
        "TEMPLATE_CAPTURE",
        "SYNC_POSTING_CHECK",
    }
    assert {task["task_type"] for task in result["tasks"] if task["term"] == "Epsilon"} == {
        "AUTH_CHAIN",
        "DISCONFIRM_TESTS",
        "TEMPLATE_CAPTURE",
        "SYNC_POSTING_CHECK",
    }
    assert "Eta" not in {task["term"] for task in result["tasks"]}
    assert all(task["run_id"] == "run-c" for task in result["tasks"])


def test_main_writes_custom_output_and_reports_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    reports = tmp_path / "reports"
    custom_output = tmp_path / "custom" / "tasks.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "error_attrib_tasks",
            "--out-reports",
            str(reports),
            "--recent-n",
            "2",
            "--out",
            str(custom_output),
        ],
    )

    assert error_attrib_tasks.main() == 0

    assert json.loads(custom_output.read_text(encoding="utf-8"))["tasks"] == []
    assert capsys.readouterr().out == f"[CAL_TASKS] wrote: {custom_output}\n"


def test_module_entrypoint_uses_default_output_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    reports = tmp_path / "reports"
    reports.mkdir()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["error_attrib_tasks", "--out-reports", str(reports)])

    with pytest.raises(SystemExit) as exc_info:
        runpy.run_path(str(Path(error_attrib_tasks.__file__)), run_name="__main__")

    assert exc_info.value.code == 0
    output_files = list(reports.glob("calibration_tasks_*.json"))
    assert len(output_files) == 1
    assert json.loads(output_files[0].read_text(encoding="utf-8"))["tasks"] == []
