from __future__ import annotations

import json
import runpy
import sys
from pathlib import Path
from typing import Any

import pytest

import abx.acquisition_plan as acquisition_plan


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _install_runtime_stubs(
    monkeypatch: pytest.MonkeyPatch,
    *,
    vector_map: Any,
    decodo: dict[str, Any],
    ml_map: dict[str, Any] | None = None,
    ml_meta: dict[str, Any] | None = None,
    classes: dict[str, str] | None = None,
    csp_results: dict[str, dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    capability_calls: list[dict[str, Any]] = []
    queries: list[dict[str, Any]] = []
    monkeypatch.setattr(acquisition_plan, "default_vector_map_v0_1", lambda: vector_map)

    class DecodoStatus:
        def to_dict(self) -> dict[str, Any]:
            return dict(decodo)

    monkeypatch.setattr(acquisition_plan, "decodo_status", lambda: DecodoStatus())
    monkeypatch.setattr(
        acquisition_plan,
        "load_ml_map",
        lambda out_reports: (ml_map or {}, ml_meta or {"source": out_reports}),
    )

    def invoke(
        rune_name: str,
        payload: dict[str, Any],
        *,
        ctx: Any,
        strict_execution: bool,
    ) -> dict[str, Any]:
        capability_calls.append(
            {
                "rune_name": rune_name,
                "payload": payload,
                "ctx": ctx,
                "strict_execution": strict_execution,
            }
        )
        term = str(payload.get("term") or payload.get("profile", {}).get("term") or "")
        if rune_name == "RUNE.FORECAST.TERM.CLASSIFY":
            return {"classification": (classes or {}).get(term, "stable")}
        return {
            "csp_result": (csp_results or {}).get(
                term, {"EA": 1.0, "FF": 1.0, "COH": False, "CIP": 0.0}
            )
        }

    def build_query(term: str, *, domains: list[str]) -> dict[str, Any]:
        query = {"q": term, "domains": domains}
        queries.append(query)
        return query

    monkeypatch.setattr(acquisition_plan, "invoke_capability", invoke)
    monkeypatch.setattr(acquisition_plan, "build_decodo_query", build_query)
    return capability_calls, queries


def test_json_and_profile_helpers_cover_supported_shapes(tmp_path: Path) -> None:
    valid = tmp_path / "nested" / "valid.json"
    _write_json(valid, {"raw_full": {"profiles": [{"term": "alpha"}, "invalid"]}})
    non_object = tmp_path / "list.json"
    _write_json(non_object, ["not", "an", "object"])
    malformed = tmp_path / "malformed.json"
    malformed.write_text("{broken", encoding="utf-8")

    assert acquisition_plan._read_json(str(tmp_path / "missing.json")) == {}
    assert acquisition_plan._read_json(str(non_object)) == {}
    with pytest.raises(json.JSONDecodeError):
        acquisition_plan._read_json(str(malformed))
    assert acquisition_plan._read_json(str(valid))["raw_full"]["profiles"][0]["term"] == "alpha"

    output = tmp_path / "written" / "report.json"
    acquisition_plan._write_json(str(output), {"ok": True})
    assert json.loads(output.read_text(encoding="utf-8")) == {"ok": True}
    assert acquisition_plan._utc_now_iso().endswith("+00:00")

    assert acquisition_plan._profiles({"raw_full": {"profiles": [{"x": 1}, "bad"]}}) == [{"x": 1}]
    assert acquisition_plan._profiles(
        {"raw_full": {"profiles": "bad"}, "views": {"profiles_top": [{"y": 2}, None]}}
    ) == [{"y": 2}]
    assert (
        acquisition_plan._profiles(
            {"raw_full": {"profiles": "bad"}, "views": {"profiles_top": "bad"}}
        )
        == []
    )
    assert (
        acquisition_plan._profiles(
            {"raw_full": {"profiles": []}, "views": {"profiles_top": [{"y": 2}]}}
        )
        == []
    )
    assert acquisition_plan._dmx({"dmx": {"bucket": "HIGH"}}) == {"bucket": "HIGH"}
    assert acquisition_plan._dmx({"dmx": "invalid"}) == {}


def test_missing_signal_thresholds_are_independent() -> None:
    assert acquisition_plan._missing_signals(
        {
            "attribution_strength": 0.54,
            "source_diversity": 0.44,
            "consensus_gap_term": 0.60,
            "manipulation_risk": 0.75,
        },
        0.70,
    ) == [
        "NEED_ATTRIBUTION_STRONGER",
        "NEED_SOURCE_DIVERSITY",
        "NEED_CONSENSUS_RESOLUTION",
        "NEED_MANIPULATION_TRIAGE",
        "HIGH_FOG_VERIFY_WITH_HIGH_CRED_SOURCES",
    ]
    assert (
        acquisition_plan._missing_signals(
            {
                "attribution_strength": 0.55,
                "source_diversity": 0.45,
                "consensus_gap_term": 0.59,
                "manipulation_risk": 0.74,
            },
            0.69,
        )
        == []
    )


def test_main_compiles_ranked_targets_and_channel_actions(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    reports = tmp_path / "reports"
    _write_json(
        reports / "a2_phase_run-1.json",
        {
            "raw_full": {
                "profiles": [
                    {
                        "term": "alpha",
                        "attribution_strength": 0.2,
                        "source_diversity": 0.3,
                        "consensus_gap_term": 0.7,
                        "manipulation_risk": 0.8,
                    },
                    {
                        "term": "beta",
                        "attribution_strength": 0.8,
                        "source_diversity": 0.8,
                        "consensus_gap_term": 0.7,
                        "manipulation_risk": 0.1,
                    },
                    {
                        "term": "gamma",
                        "attribution_strength": 0.9,
                        "source_diversity": 0.9,
                        "consensus_gap_term": 0.1,
                        "manipulation_risk": 0.0,
                    },
                    {
                        "term": "delta",
                        "attribution_strength": 1.0,
                        "source_diversity": 1.0,
                        "consensus_gap_term": 0.0,
                        "manipulation_risk": 0.0,
                    },
                    {"term": "   ", "attribution_strength": 0.0},
                    "invalid profile",
                ]
            }
        },
    )
    _write_json(
        reports / "mwr_run-1.json", {"dmx": {"overall_manipulation_risk": 0.4, "bucket": "low"}}
    )
    _write_json(reports / "calibration_tasks_001.json", {"tasks": [{"task_id": "old"}]})
    _write_json(reports / "calibration_tasks_002.json", {"tasks": [{"task_id": "new"}]})
    vector_map = {
        "channels": [
            {
                "id": "manual",
                "kind": "documents",
                "mode": "manual_offline",
                "enabled": True,
                "domains": [],
            },
            {
                "id": "web",
                "kind": "web",
                "mode": "decodo",
                "enabled": True,
                "domains": ["example.test"],
            },
            {
                "id": "forums",
                "kind": "forums",
                "mode": "decodo",
                "enabled": True,
                "domains": ["forum.test"],
            },
            {
                "id": "video",
                "kind": "video",
                "mode": "decodo",
                "enabled": True,
                "domains": ["video.test"],
            },
            {"id": "disabled", "kind": "web", "mode": "decodo", "enabled": False, "domains": []},
        ]
    }
    ml_map = {
        "alpha": {"bucket": "HIGH", "ml_score": 0.8},
        "beta": {"bucket": "LOW", "ml_score": 0.2},
        "gamma": {"bucket": "MED", "ml_score": 0.5},
    }
    csp_results = {
        "alpha": {"EA": 0.4, "FF": 0.3, "COH": True, "CIP": 0.6},
        "beta": {"EA": 0.8, "FF": 0.9, "COH": False, "CIP": 0.1},
        "gamma": {"EA": 0.9, "FF": 0.9, "COH": False, "CIP": 0.1},
    }
    calls, queries = _install_runtime_stubs(
        monkeypatch,
        vector_map=vector_map,
        decodo={"available": True, "reason": "ready"},
        ml_map=ml_map,
        ml_meta={"loaded": 3},
        classes={"alpha": "volatile", "beta": "stable", "gamma": "contested"},
        csp_results=csp_results,
    )
    output_dir = tmp_path / "built"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "acquisition_plan",
            "--run-id",
            "run-1",
            "--out-reports",
            str(reports),
            "--vector-map",
            str(tmp_path / "vector-map.json"),
            "--max-terms",
            "4",
        ],
    )
    _write_json(tmp_path / "vector-map.json", vector_map)
    monkeypatch.setattr(
        acquisition_plan,
        "_write_json",
        lambda path, obj: _write_json(output_dir / Path(path).name, obj),
    )

    assert acquisition_plan.main() == 0

    report_path = output_dir / "acquisition_plan_run-1.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["version"] == "acquisition_plan.v0.1"
    assert report["run_id"] == "run-1"
    assert report["ts"].endswith("+00:00")
    assert report["dmx"] == {"overall_manipulation_risk": 0.4, "bucket": "LOW"}
    assert report["decodo"] == {"available": True, "reason": "ready"}
    assert report["vector_map"] == vector_map
    assert report["ml_index"] == {"loaded": 3}
    assert [target["term"] for target in report["targets"]] == ["alpha", "beta", "gamma"]
    assert report["targets"][0]["class"] == "volatile"
    assert {
        "NEED_ATTRIBUTION_STRONGER",
        "NEED_SOURCE_DIVERSITY",
        "NEED_CONSENSUS_RESOLUTION",
        "NEED_MANIPULATION_TRIAGE",
        "CSP_NEED_EVIDENCE_ADEQUACY",
        "CSP_NEED_FALSIFIABILITY_TESTS",
        "CSP_PLAUSIBLE_UNPROVEN_NEED_PRIMARY_DOCS",
        "ML_BUCKET_HIGH",
        "ML_HIGH_STEERING_RISK",
    }.issubset(report["targets"][0]["missing"])
    assert "ML_MED_STEERING_RISK" in report["targets"][2]["missing"]
    assert "ML_LOW_STEERING_RISK" in report["targets"][1]["missing"]
    assert report["calibration_tasks"] == [{"task_id": "new"}]
    assert report["policy"] == {
        "online_not_abandoned": True,
        "decodo_primary": True,
        "fallback_behavior": "label_blocked_and_prompt_offline_if_needed",
        "non_truncation": True,
    }
    assert report["provenance"] == {
        "builder": "abx.acquisition_plan.v0.1",
        "a2_phase": str(reports / "a2_phase_run-1.json"),
        "mwr": str(reports / "mwr_run-1.json"),
    }

    actions = report["actions"]
    manual_actions = [action for action in actions if action["mode"] == "manual_offline"]
    assert [action["action"] for action in manual_actions] == [
        "prompt_user_for_artifacts",
        "prompt_user_for_falsification_tests",
        "prompt_user_for_origin_trace",
        "prompt_user_for_boost_signals",
    ]
    assert all(action["term"] == "alpha" for action in manual_actions)
    decodo_actions = [action for action in actions if action["mode"] == "decodo"]
    searches = [action for action in decodo_actions if action["action"] == "search"]
    assert [(action["term"], action["channel"]) for action in searches] == [
        ("alpha", "web"),
        ("beta", "web"),
        ("beta", "forums"),
        ("beta", "video"),
        ("gamma", "web"),
    ]
    assert (
        len([action for action in decodo_actions if action["action"].startswith("harvest_")]) == 6
    )
    assert not any(action["channel"] == "disabled" for action in actions)
    assert len(queries) == 5
    assert len(calls) == 6
    assert all(call["strict_execution"] is True for call in calls)
    assert all(call["ctx"].run_id == "run-1" for call in calls)
    assert all(call["ctx"].subsystem_id == "abx.acquisition_plan" for call in calls)
    assert (
        capsys.readouterr().out
        == f"[ACQUISITION_PLAN] wrote: {reports / 'acquisition_plan_run-1.json'}\n"
    )


def test_main_blocks_decodo_and_uses_default_vector_map(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    reports = tmp_path / "reports"
    _write_json(
        reports / "a2_phase_run-2.json",
        {
            "views": {
                "profiles_top": [
                    {
                        "term": "safe",
                        "attribution_strength": 1,
                        "source_diversity": 1,
                        "consensus_gap_term": 0,
                        "manipulation_risk": 0,
                    }
                ]
            }
        },
    )
    _write_json(
        reports / "mwr_run-2.json", {"dmx": {"overall_manipulation_risk": 0.2, "bucket": "low"}}
    )
    _write_json(reports / "calibration_tasks_999.json", {"tasks": "invalid"})
    vector_map = {
        "channels": [
            {
                "id": "decodo",
                "kind": "web",
                "mode": "decodo",
                "enabled": True,
                "domains": ["site.test"],
            }
        ]
    }
    _install_runtime_stubs(
        monkeypatch,
        vector_map=vector_map,
        decodo={"available": False, "reason": "no credentials"},
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["acquisition_plan", "--run-id", "run-2", "--out-reports", str(reports)],
    )
    written: list[dict[str, Any]] = []
    monkeypatch.setattr(acquisition_plan, "_write_json", lambda path, obj: written.append(obj))

    assert acquisition_plan.main() == 0

    report = written[0]
    assert report["vector_map"] == vector_map
    assert report["calibration_tasks"] == []
    assert report["targets"][0]["term"] == "safe"
    assert report["actions"] == [
        {
            "term": "safe",
            "channel": "decodo",
            "mode": "decodo",
            "action": "blocked_missing_decodo",
            "rationale": ["DECODO_UNAVAILABLE", "no credentials"],
        }
    ]
    assert (
        capsys.readouterr().out
        == f"[ACQUISITION_PLAN] wrote: {reports / 'acquisition_plan_run-2.json'}\n"
    )


def test_main_skips_high_risk_forum_and_video_channels(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    reports = tmp_path / "reports"
    _write_json(
        reports / "a2_phase_run-3.json",
        {
            "raw_full": {
                "profiles": [
                    {
                        "term": "term",
                        "attribution_strength": 1,
                        "source_diversity": 1,
                        "consensus_gap_term": 0,
                        "manipulation_risk": 0,
                    }
                ]
            }
        },
    )
    _write_json(
        reports / "mwr_run-3.json", {"dmx": {"overall_manipulation_risk": 0.8, "bucket": "HIGH"}}
    )
    vector_map = {
        "channels": [
            {"id": "web", "kind": "web", "mode": "decodo", "enabled": True, "domains": []},
            {"id": "forums", "kind": "forums", "mode": "decodo", "enabled": True, "domains": []},
            {"id": "video", "kind": "video", "mode": "decodo", "enabled": True, "domains": []},
        ]
    }
    _install_runtime_stubs(
        monkeypatch,
        vector_map=vector_map,
        decodo={"available": True},
    )
    monkeypatch.setattr(
        sys, "argv", ["acquisition_plan", "--run-id", "run-3", "--out-reports", str(reports)]
    )
    written: list[dict[str, Any]] = []
    monkeypatch.setattr(acquisition_plan, "_write_json", lambda path, obj: written.append(obj))

    assert acquisition_plan.main() == 0

    assert [(action["term"], action["channel"]) for action in written[0]["actions"]] == [
        ("term", "web")
    ]


def test_calibration_discovery_errors_fail_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    reports = tmp_path / "reports"
    _write_json(reports / "a2_phase_run-4.json", {"raw_full": {"profiles": []}})
    _write_json(reports / "mwr_run-4.json", {})
    _install_runtime_stubs(monkeypatch, vector_map={"channels": []}, decodo={"available": False})
    monkeypatch.setattr(
        sys, "argv", ["acquisition_plan", "--run-id", "run-4", "--out-reports", str(reports)]
    )
    monkeypatch.setattr(
        acquisition_plan.glob, "glob", lambda pattern: (_ for _ in ()).throw(OSError("glob failed"))
    )
    written: list[dict[str, Any]] = []
    monkeypatch.setattr(acquisition_plan, "_write_json", lambda path, obj: written.append(obj))

    assert acquisition_plan.main() == 0
    assert written[0]["calibration_tasks"] == []
    assert written[0]["targets"] == []
    assert written[0]["actions"] == []


def test_module_entrypoint_writes_empty_plan(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    reports = tmp_path / "reports"
    reports.mkdir()
    vector_map = {"channels": []}
    _write_json(reports / "a2_phase_run-5.json", {"raw_full": {"profiles": []}})
    _write_json(reports / "mwr_run-5.json", {"dmx": {}})
    _install_runtime_stubs(monkeypatch, vector_map=vector_map, decodo={"available": False})
    monkeypatch.setattr(
        sys, "argv", ["acquisition_plan", "--run-id", "run-5", "--out-reports", str(reports)]
    )

    # Run the actual module guard while keeping report writes inside this temporary directory.
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc_info:
        runpy.run_path(acquisition_plan.__file__, run_name="__main__")

    assert exc_info.value.code == 0
    written = json.loads((reports / "acquisition_plan_run-5.json").read_text(encoding="utf-8"))
    assert written["targets"] == []
    assert written["actions"] == []
