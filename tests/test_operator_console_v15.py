from __future__ import annotations

import json
from pathlib import Path

from webpanel.operator_console import (
    _compute_suggested_next_step,
    _compute_weakness_reasons,
    build_last_action_feedback,
    build_view_state,
    run_compliance_probe_command,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _seed_scopepass(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "artifacts_seal/runs/generalized_coverage/run.generalized_coverage.scopepass.v1.artifact.json",
        {
            "run_id": "run.generalized_coverage.scopepass.v1",
            "artifact_id": "art.scopepass.v1",
            "rune_id": "RUNE.SCAN",
            "status": "SUCCESS",
            "timestamp": "2026-03-28T01:02:03Z",
            "ledger_record_ids": ["ledger.scopepass.v1"],
            "ledger_artifact_ids": ["art.scopepass.v1"],
            "correlation_pointers": [{"type": "ledger", "value": "ptr.scopepass.v1"}],
        },
    )
    _write_json(
        tmp_path / "out/validators/execution-validation-run.generalized_coverage.scopepass.v1.json",
        {
            "runId": "run.generalized_coverage.scopepass.v1",
            "status": "VALID",
            "timestamp_utc": "2026-03-28T02:02:03Z",
            "validatedArtifacts": ["art.scopepass.v1"],
            "correlation": {"ledgerIds": ["ledger.scopepass.v1"], "pointers": ["ptr.v1"]},
        },
    )


def test_build_view_state_loads_runs_and_summaries_deterministically(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    _write_json(
        tmp_path / "artifacts_seal/runs/compliance_probe/run.compliance_probe.v1.artifact.json",
        {
            "run_id": "run.compliance_probe.v1",
            "artifact_id": "art.compliance.v1",
            "rune_id": "RUNE.INGEST",
            "status": "SUCCESS",
            "timestamp": "2026-03-28T00:00:00Z",
            "ledger_record_ids": [],
            "ledger_artifact_ids": [],
            "correlation_pointers": [],
        },
    )
    _write_json(tmp_path / "docs/artifacts/closure_generalized_milestone_note.v1.json", {"status": "GENERALIZED_CLOSURE_CONFIRMED"})

    view = build_view_state(base_dir=tmp_path)

    assert view.mode == "snapshot"
    assert view.available_runs == ["run.compliance_probe.v1", "run.generalized_coverage.scopepass.v1"]
    assert view.visible_run_ids == ["run.generalized_coverage.scopepass.v1", "run.compliance_probe.v1"]
    assert view.focus_filters == {"health": "all", "run_query": "", "sort_mode": "latest_first"}
    assert view.selected_run_id == "run.generalized_coverage.scopepass.v1"
    assert view.closure_status == "GENERALIZED_CLOSURE_CONFIRMED"
    assert view.last_action is None
    assert view.suggested_run_id == "run.generalized_coverage.scopepass.v1"
    assert view.suggestion_reason == "validator_success_with_pointers_latest"
    assert view.snapshot_header["closure_status"] == "GENERALIZED_CLOSURE_CONFIRMED"
    assert view.snapshot_header["visible_run_count"] == 2
    assert view.snapshot_header["health_counts"] == {"strong": 1, "partial": 1, "weak": 0}
    assert view.snapshot_header["suggested_focus_run_id"] == "run.generalized_coverage.scopepass.v1"
    assert view.snapshot_header["last_action_summary"] == "none"
    assert view.snapshot_header["newest_activity_summary"].startswith("2026-03-28T02:02:03Z")


def test_build_view_state_selected_run_and_validator_summary(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)

    view = build_view_state(base_dir=tmp_path, selected_run_id="run.generalized_coverage.scopepass.v1")

    assert view.selected_run_id == "run.generalized_coverage.scopepass.v1"
    assert view.selected_run_artifact_summary["count"] == 1
    assert view.selected_run_validator_summary["count"] == 1
    validator = view.selected_run_validator_summary["validators"][0]
    assert validator["validated_artifacts_count"] == 1
    assert validator["ledger_ids_count"] == 1
    assert validator["pointers_count"] == 1

    detail = view.selected_run_detail
    assert detail["artifact_path"].endswith("run.generalized_coverage.scopepass.v1.artifact.json")
    assert detail["validator_path"].endswith("execution-validation-run.generalized_coverage.scopepass.v1.json")
    assert detail["artifact_status"] == "SUCCESS"
    assert detail["validator_status"] == "VALID"
    assert detail["ledger_record_ids_count"] == 1
    assert detail["ledger_artifact_ids_count"] == 1
    assert detail["correlation_pointers_count"] == 1
    assert detail["latest_timestamp"] == "2026-03-28T02:02:03Z"
    assert detail["health_label"] == "strong"
    assert view.weakness_reasons == []
    assert view.suggested_next_step == "No action needed"
    assert view.evidence_drilldown["artifact_path"].endswith("run.generalized_coverage.scopepass.v1.artifact.json")
    assert view.evidence_drilldown["validator_path"].endswith("execution-validation-run.generalized_coverage.scopepass.v1.json")
    assert view.evidence_drilldown["ledger_linkage_summary"] == "records=1 artifacts=1"
    assert view.evidence_drilldown["correlation_pointers_preview"] == ['{"type":"ledger","value":"ptr.scopepass.v1"}']
    assert view.evidence_drilldown["audit_refs_preview"] == []


def test_focus_filters_and_sort_modes_are_deterministic(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    _write_json(
        tmp_path / "artifacts_seal/runs/compliance_probe/run.partial.v1.artifact.json",
        {
            "run_id": "run.partial.v1",
            "status": "FAILED",
            "timestamp": "2026-03-28T00:00:00Z",
            "ledger_record_ids": [],
            "ledger_artifact_ids": [],
            "correlation_pointers": [],
        },
    )
    _write_json(
        tmp_path / "out/validators/execution-validation-run.weak.v1.json",
        {
            "runId": "run.weak.v1",
            "status": "MISSING",
            "validatedArtifacts": [],
            "correlation": {"ledgerIds": [], "pointers": []},
        },
    )

    strong_only = build_view_state(base_dir=tmp_path, health_filter="strong")
    assert strong_only.visible_run_ids == ["run.generalized_coverage.scopepass.v1"]

    query_filtered = build_view_state(base_dir=tmp_path, run_query="partial")
    assert query_filtered.visible_run_ids == ["run.partial.v1"]

    run_id_sorted = build_view_state(base_dir=tmp_path, sort_mode="run_id_asc")
    assert run_id_sorted.visible_run_ids == [
        "run.generalized_coverage.scopepass.v1",
        "run.partial.v1",
        "run.weak.v1",
    ]

    latest_sorted = build_view_state(base_dir=tmp_path, sort_mode="latest_first")
    assert latest_sorted.visible_run_ids == [
        "run.generalized_coverage.scopepass.v1",
        "run.partial.v1",
        "run.weak.v1",
    ]

    fallback_selected = build_view_state(
        base_dir=tmp_path,
        selected_run_id="run.partial.v1",
        health_filter="strong",
    )
    assert fallback_selected.selected_run_id == "run.generalized_coverage.scopepass.v1"


def test_action_feedback_is_deterministic_and_prefers_visible_triggered_run(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    _write_json(
        tmp_path / "artifacts_seal/runs/compliance_probe/run.compliance_probe.v1.artifact.json",
        {
            "run_id": "run.compliance_probe.v1",
            "status": "SUCCESS",
            "timestamp": "2026-03-28T03:00:00Z",
            "ledger_record_ids": [],
            "ledger_artifact_ids": [],
            "correlation_pointers": [],
        },
    )

    action_result = {
        "exit_code": 0,
        "stdout_tail": "artifacts_seal/runs/compliance_probe/run.compliance_probe.v1.artifact.json\n",
        "stderr_tail": "",
        "timestamp_utc": "2026-03-28T03:00:01Z",
    }
    feedback = build_last_action_feedback(action_result)
    assert feedback["action_name"] == "run_compliance_probe"
    assert feedback["outcome_status"] == "SUCCESS"
    assert feedback["triggered_run_id"] == "run.compliance_probe.v1"

    view = build_view_state(base_dir=tmp_path, health_filter="all", last_action=feedback)
    assert view.last_action is not None
    assert view.last_action["outcome_status"] == "SUCCESS"
    assert view.selected_run_id == "run.compliance_probe.v1"


def test_run_compliance_probe_command_is_fixed(monkeypatch) -> None:
    captured = {}

    class _Completed:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def _fake_run(cmd, capture_output, text, check):
        captured["cmd"] = cmd
        captured["capture_output"] = capture_output
        captured["text"] = text
        captured["check"] = check
        return _Completed()

    monkeypatch.setattr("webpanel.operator_console.subprocess.run", _fake_run)

    result = run_compliance_probe_command()

    assert captured["cmd"] == ["python", "-m", "aal_core.runes.compliance_probe"]
    assert captured["capture_output"] is True
    assert captured["text"] is True
    assert captured["check"] is False
    assert result["status"] == "SUCCESS"
    assert result["exit_code"] == 0


def test_recent_activity_is_deterministic(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    _write_json(
        tmp_path / "artifacts_seal/runs/compliance_probe/run.compliance_probe.v1.artifact.json",
        {
            "run_id": "run.compliance_probe.v1",
            "status": "SUCCESS",
            "timestamp": "2026-03-28T03:00:00Z",
            "ledger_record_ids": [],
            "ledger_artifact_ids": [],
            "correlation_pointers": [],
        },
    )

    action_result = {
        "exit_code": 0,
        "stdout_tail": "artifacts_seal/runs/compliance_probe/run.compliance_probe.v1.artifact.json\n",
        "stderr_tail": "",
        "timestamp_utc": "2026-03-28T03:00:01Z",
    }
    feedback = build_last_action_feedback(action_result)

    view = build_view_state(base_dir=tmp_path, last_action=feedback)

    assert view.recent_activity_limit == 10
    assert len(view.recent_activity) >= 3
    first = view.recent_activity[0]
    assert first["activity_type"] == "action"
    assert first["timestamp"] == "2026-03-28T03:00:01Z"
    assert first["run_id"] == "run.compliance_probe.v1"
    assert all(set(item.keys()) >= {"timestamp", "activity_type", "run_id", "summary"} for item in view.recent_activity)
    assert view.snapshot_header["last_action_summary"] == "SUCCESS run=run.compliance_probe.v1"
    assert view.snapshot_header["newest_activity_summary"].startswith(
        "2026-03-28T03:00:01Z action run=run.compliance_probe.v1"
    )


def test_suggested_focus_fallback_and_manual_selection(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "artifacts_seal/runs/compliance_probe/run.partial.v1.artifact.json",
        {
            "run_id": "run.partial.v1",
            "status": "FAILED",
            "timestamp": "2026-03-28T00:00:00Z",
            "ledger_record_ids": [],
            "ledger_artifact_ids": [],
            "correlation_pointers": [],
        },
    )
    _write_json(
        tmp_path / "out/validators/execution-validation-run.partial.v1.json",
        {
            "runId": "run.partial.v1",
            "status": "MISSING",
            "validatedArtifacts": [],
            "correlation": {"ledgerIds": [], "pointers": []},
            "timestamp_utc": "2026-03-28T00:00:01Z",
        },
    )

    fallback_view = build_view_state(base_dir=tmp_path)
    assert fallback_view.suggested_run_id == "run.partial.v1"
    assert fallback_view.suggestion_reason == "fallback_first_visible_run"

    _seed_scopepass(tmp_path)
    explicit_view = build_view_state(base_dir=tmp_path, selected_run_id="run.partial.v1")
    assert explicit_view.suggested_run_id == "run.generalized_coverage.scopepass.v1"
    assert explicit_view.selected_run_id == "run.partial.v1"


def test_weakness_reasons_are_deterministic_for_partial_and_weak(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "artifacts_seal/runs/compliance_probe/run.partial.v1.artifact.json",
        {
            "run_id": "run.partial.v1",
            "status": "FAILED",
            "timestamp": "2026-03-28T00:00:00Z",
            "ledger_record_ids": [],
            "ledger_artifact_ids": [],
            "correlation_pointers": [],
        },
    )
    _write_json(
        tmp_path / "out/validators/execution-validation-run.partial.v1.json",
        {
            "runId": "run.partial.v1",
            "status": "MISSING",
            "validatedArtifacts": [],
            "correlation": {"ledgerIds": [], "pointers": []},
            "timestamp_utc": "2026-03-28T00:00:01Z",
        },
    )

    partial_view = build_view_state(base_dir=tmp_path, selected_run_id="run.partial.v1")
    assert partial_view.selected_run_detail["health_label"] == "partial"
    assert partial_view.weakness_reasons == [
        "no validator output",
        "no correlation pointers",
        "no ledger linkage",
        "artifact not successful",
    ]

    weak_reasons = _compute_weakness_reasons(
        {
            "health_label": "weak",
            "validator_status": "MISSING",
            "correlation_pointers_count": 0,
            "ledger_record_ids_count": 0,
            "artifact_status": "MISSING",
            "latest_timestamp": "NOT_COMPUTABLE",
        }
    )
    assert weak_reasons == [
        "no validator output",
        "no correlation pointers",
        "no ledger linkage",
        "artifact not successful",
        "missing timestamp",
    ]


def test_suggested_next_step_priority_is_deterministic() -> None:
    assert _compute_suggested_next_step(
        {
            "validator_status": "MISSING",
            "correlation_pointers_count": 0,
            "ledger_record_ids_count": 0,
            "artifact_status": "FAILED",
            "latest_timestamp": "NOT_COMPUTABLE",
        }
    ) == "Run validator for this run"

    assert _compute_suggested_next_step(
        {
            "validator_status": "VALID",
            "correlation_pointers_count": 0,
            "ledger_record_ids_count": 0,
            "artifact_status": "FAILED",
            "latest_timestamp": "NOT_COMPUTABLE",
        }
    ) == "Inspect or regenerate linkage resolution for this run"

    assert _compute_suggested_next_step(
        {
            "validator_status": "VALID",
            "correlation_pointers_count": 1,
            "ledger_record_ids_count": 0,
            "artifact_status": "FAILED",
            "latest_timestamp": "NOT_COMPUTABLE",
        }
    ) == "Inspect or regenerate ledger continuity record for this run"

    assert _compute_suggested_next_step(
        {
            "validator_status": "VALID",
            "correlation_pointers_count": 1,
            "ledger_record_ids_count": 1,
            "artifact_status": "FAILED",
            "latest_timestamp": "NOT_COMPUTABLE",
        }
    ) == "Inspect artifact generation path for this run"

    assert _compute_suggested_next_step(
        {
            "validator_status": "VALID",
            "correlation_pointers_count": 1,
            "ledger_record_ids_count": 1,
            "artifact_status": "SUCCESS",
            "latest_timestamp": "NOT_COMPUTABLE",
        }
    ) == "Inspect timestamp normalization for this run"

    assert _compute_suggested_next_step(
        {
            "validator_status": "VALID",
            "correlation_pointers_count": 1,
            "ledger_record_ids_count": 1,
            "artifact_status": "SUCCESS",
            "latest_timestamp": "2026-03-28T02:02:03Z",
        }
    ) == "No action needed"


def test_evidence_drilldown_is_bounded_and_scoped(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    for idx in range(5):
        _write_json(
            tmp_path / f"artifacts_seal/audits/run.generalized_coverage.scopepass.v1/audit-{idx}.json",
            {"idx": idx},
        )

    view = build_view_state(base_dir=tmp_path, selected_run_id="run.generalized_coverage.scopepass.v1")
    assert view.evidence_drilldown["correlation_pointers_preview"] == ['{"type":"ledger","value":"ptr.scopepass.v1"}']
    assert view.evidence_drilldown["audit_refs_preview"] == [
        "artifacts_seal/audits/run.generalized_coverage.scopepass.v1/audit-0.json",
        "artifacts_seal/audits/run.generalized_coverage.scopepass.v1/audit-1.json",
        "artifacts_seal/audits/run.generalized_coverage.scopepass.v1/audit-2.json",
    ]


def test_two_run_compare_strip_is_deterministic_and_optional(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    _write_json(
        tmp_path / "artifacts_seal/runs/compliance_probe/run.partial.v1.artifact.json",
        {
            "run_id": "run.partial.v1",
            "status": "FAILED",
            "timestamp": "2026-03-28T00:00:00Z",
            "ledger_record_ids": [],
            "ledger_artifact_ids": [],
            "correlation_pointers": [],
        },
    )
    _write_json(
        tmp_path / "out/validators/execution-validation-run.partial.v1.json",
        {
            "runId": "run.partial.v1",
            "status": "MISSING",
            "validatedArtifacts": [],
            "correlation": {"ledgerIds": [], "pointers": []},
            "timestamp_utc": "2026-03-28T00:00:01Z",
        },
    )

    view = build_view_state(
        base_dir=tmp_path,
        selected_run_id="run.generalized_coverage.scopepass.v1",
        compare_run_id="run.partial.v1",
    )
    assert view.comparison_run_id == "run.partial.v1"
    assert view.compare_strip["enabled"] is True
    assert view.compare_strip["selected"] == {
        "run_id": "run.generalized_coverage.scopepass.v1",
        "artifact_status": "SUCCESS",
        "validator_status": "VALID",
        "correlation_pointers_count": 1,
        "health_label": "strong",
        "latest_timestamp": "2026-03-28T02:02:03Z",
    }
    assert view.compare_strip["comparison"] == {
        "run_id": "run.partial.v1",
        "artifact_status": "FAILED",
        "validator_status": "MISSING",
        "correlation_pointers_count": 0,
        "health_label": "partial",
        "latest_timestamp": "2026-03-28T00:00:01Z",
    }

    no_compare = build_view_state(base_dir=tmp_path, compare_run_id="run.generalized_coverage.scopepass.v1")
    assert no_compare.comparison_run_id is None
    assert no_compare.compare_strip["enabled"] is False
