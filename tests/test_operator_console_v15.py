from __future__ import annotations

import json
from pathlib import Path

import webpanel.operator_console as operator_console
from webpanel.operator_console import (
    _compute_suggested_next_step,
    _compute_weakness_reasons,
    build_last_action_feedback,
    build_view_state,
    execute_runtime_adapter,
    resolve_compare_run_id_for_apply,
    run_compliance_probe_command,
    write_operator_ers_review_artifact,
    write_operator_ers_snapshot_artifact,
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


def test_ers_state_and_queue_surfaces_are_deterministic(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)

    view = build_view_state(base_dir=tmp_path, selected_run_id="run.generalized_coverage.scopepass.v1", workbench_mode="ers")

    assert view.workbench_mode == "ers"
    assert "ers" in view.workbench_modes_allowed
    ers = view.ers_integration
    assert ers["ers_state_surface"]["ers_mode"] == "manual_explicit_trigger_only"
    assert ers["ers_state_surface"]["queue_length"] == 4
    assert ers["ers_state_surface"]["runnable_count"] + ers["ers_state_surface"]["blocked_count"] == 4
    assert ers["ers_queue"]["trigger_rule"].startswith("operator_explicit_trigger_only")
    assert len(ers["ers_queue"]["runnable_items"]) <= 5
    assert len(ers["ers_queue"]["blocked_items"]) <= 5
    assert ers["ers_workspace_payload"]["mode"] == "ers"


def test_ers_eligibility_blocks_execution_validator_without_selected_run(tmp_path: Path) -> None:
    view = build_view_state(base_dir=tmp_path, selected_run_id=None)

    blocked = {row["item_id"]: row for row in view.ers_integration["ers_blocked_items"]}
    validator = blocked["ers.item.execution_validator"]
    assert validator["blocked"] is True
    assert validator["gating_reason"] in {"selected_run_required", "policy_permits_trigger"}
    assert any(row["condition"] == "selected_run_required" and row["passed"] is False for row in validator["required_conditions"])


def test_ers_scheduling_reasoning_matches_next_runnable(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(base_dir=tmp_path, selected_run_id="run.generalized_coverage.scopepass.v1")
    queue = view.ers_integration["ers_queue"]
    reasoning = view.ers_integration["ers_reasoning"]
    next_id = queue["next_runnable_item"]["item_id"]
    if next_id == "NOT_COMPUTABLE":
        assert queue["next_runnable_item"]["gating_reason"] == "no_eligible_items"
        return
    first = next((row for row in reasoning if row["item_id"] == next_id), None)
    assert first is not None
    assert "priority=" in first["priority_explanation"]
    assert first["why_next"].startswith("next by priority=")


def test_ers_snapshot_export_artifact_is_bounded_and_structured(tmp_path: Path, monkeypatch) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(base_dir=tmp_path, selected_run_id="run.generalized_coverage.scopepass.v1")
    monkeypatch.chdir(tmp_path)
    path, status = write_operator_ers_snapshot_artifact(
        payload={
            **view.ers_integration["ers_snapshot_preview"],
            "runtime_context": {"selected_run_id": view.selected_run_id or ""},
        }
    )
    assert status == "written"
    assert path is not None
    payload = json.loads((tmp_path / path).read_text(encoding="utf-8"))
    assert payload["rune_id"] == "RUNE.ERS"
    assert "ers_state_surface" in payload
    assert len(payload["runnable_items"]) <= 5
    assert len(payload["blocked_items"]) <= 5


def test_ers_mode_does_not_mutate_unrelated_state(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    base = build_view_state(base_dir=tmp_path, workbench_mode="overview")
    ers = build_view_state(base_dir=tmp_path, workbench_mode="ers")
    assert base.available_runs == ers.available_runs
    assert base.visible_run_ids == ers.visible_run_ids
    assert base.snapshot_header["closure_status"] == ers.snapshot_header["closure_status"]


def test_ers_review_is_inert_without_prior_snapshot(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(base_dir=tmp_path, selected_run_id="run.generalized_coverage.scopepass.v1", workbench_mode="ers")
    review = view.ers_review
    assert review["ers_snapshot_diff"]["status"] == "NOT_COMPUTABLE"
    assert review["ers_drift_summary"]["label"] == "NOT_COMPUTABLE"


def test_ers_review_diff_and_drift_with_prior_snapshot(tmp_path: Path, monkeypatch) -> None:
    _seed_scopepass(tmp_path)
    monkeypatch.chdir(tmp_path)
    first_view = build_view_state(base_dir=tmp_path, selected_run_id="run.generalized_coverage.scopepass.v1", workbench_mode="ers")
    write_operator_ers_snapshot_artifact(
        payload={
            **first_view.ers_integration["ers_snapshot_preview"],
            "runtime_context": {"selected_run_id": first_view.selected_run_id or ""},
            "next_runnable_item": (first_view.ers_integration.get("ers_queue", {}) or {}).get("next_runnable_item", {}),
        }
    )
    _write_json(
        tmp_path / "artifacts_seal/runs/new/run.synthetic.extra.artifact.json",
        {
            "run_id": "run.synthetic.extra",
            "status": "SUCCESS",
            "timestamp": "2026-03-29T09:00:00Z",
            "ledger_record_ids": [],
            "ledger_artifact_ids": [],
            "correlation_pointers": [],
        },
    )
    second_view = build_view_state(base_dir=tmp_path, selected_run_id="run.synthetic.extra", workbench_mode="ers")
    assert second_view.ers_review["ers_snapshot_diff"]["status"] == "available"
    assert second_view.ers_review["ers_drift_summary"]["label"] in {"STABLE", "SHIFTED", "DEGRADED"}


def test_ers_review_transition_and_handoff_are_deterministic(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    action_history = [
        {
            "timestamp": "2026-03-29T10:00:00Z",
            "action_name": "run_execution_validator",
            "preset_id": "ers.ers.item.execution_validator",
            "adapter_name": "adapter.run_execution_validator",
            "run_id": "run.generalized_coverage.scopepass.v1",
            "outcome_status": "SUCCESS",
            "artifact_ref": "out/validators/execution-validation-run.generalized_coverage.scopepass.v1.json",
            "summary": "validator completed",
        }
    ]
    view = build_view_state(
        base_dir=tmp_path,
        selected_run_id="run.generalized_coverage.scopepass.v1",
        workbench_mode="ers",
        action_history=action_history,
    )
    handoff = view.ers_review["ers_runtime_handoff"]
    assert handoff["status"] == "available"
    assert handoff["triggered_ers_item_id"] == "ers.item.execution_validator"
    transitions = view.ers_review["ers_transition_log"]
    assert any(row["transition_type"] == "triggered" for row in transitions)
    assert len(transitions) <= 10


def test_ers_review_export_artifact_is_bounded_and_structured(tmp_path: Path, monkeypatch) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(base_dir=tmp_path, selected_run_id="run.generalized_coverage.scopepass.v1", workbench_mode="ers")
    monkeypatch.chdir(tmp_path)
    path, status = write_operator_ers_review_artifact(payload=view.ers_review["ers_review_export_preview"])
    assert status == "written"
    assert path is not None
    payload = json.loads((tmp_path / path).read_text(encoding="utf-8"))
    assert payload["rune_id"] == "RUNE.ERS"
    assert payload["ers_drift_summary"]["label"] in {"STABLE", "SHIFTED", "DEGRADED", "NOT_COMPUTABLE"}
    assert len(payload["ers_transition_log"]) <= 10


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
    assert view.suggested_compare_run_id == "run.partial.v1"
    assert view.suggested_compare_reason == "fallback_next_visible_run"
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
    assert view.compare_delta_summary == {
        "enabled": True,
        "artifact_status_delta": "changed",
        "validator_status_delta": "changed",
        "correlation_pointers_delta": "+1",
        "health_label_delta": "improved",
        "timestamp_ordering": "selected newer",
    }

    no_compare = build_view_state(base_dir=tmp_path, compare_run_id="run.generalized_coverage.scopepass.v1")
    assert no_compare.comparison_run_id is None
    assert no_compare.compare_strip["enabled"] is False
    assert no_compare.suggested_compare_run_id == "run.partial.v1"
    assert no_compare.suggested_compare_reason == "fallback_next_visible_run"
    assert no_compare.compare_delta_summary == {
        "enabled": False,
        "artifact_status_delta": "unchanged",
        "validator_status_delta": "unchanged",
        "correlation_pointers_delta": "no change",
        "health_label_delta": "unchanged",
        "timestamp_ordering": "unavailable",
    }

    single = build_view_state(base_dir=tmp_path, health_filter="strong")
    assert single.visible_run_ids == ["run.generalized_coverage.scopepass.v1"]
    assert single.suggested_compare_run_id is None
    assert single.suggested_compare_reason == "no_compare_candidate"


def test_suggested_compare_prefers_same_family_nearest_timestamp(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "artifacts_seal/runs/compliance_probe/run.family.alpha.v1.artifact.json",
        {
            "run_id": "run.family.alpha.v1",
            "status": "SUCCESS",
            "timestamp": "2026-03-28T01:00:00Z",
            "ledger_record_ids": [],
            "ledger_artifact_ids": [],
            "correlation_pointers": [],
        },
    )
    _write_json(
        tmp_path / "artifacts_seal/runs/compliance_probe/run.family.beta.v1.artifact.json",
        {
            "run_id": "run.family.beta.v1",
            "status": "SUCCESS",
            "timestamp": "2026-03-28T01:00:05Z",
            "ledger_record_ids": [],
            "ledger_artifact_ids": [],
            "correlation_pointers": [],
        },
    )
    _write_json(
        tmp_path / "artifacts_seal/runs/compliance_probe/run.other.v1.artifact.json",
        {
            "run_id": "run.other.v1",
            "status": "SUCCESS",
            "timestamp": "2026-03-28T01:00:01Z",
            "ledger_record_ids": [],
            "ledger_artifact_ids": [],
            "correlation_pointers": [],
        },
    )

    view = build_view_state(base_dir=tmp_path, selected_run_id="run.family.alpha.v1")
    assert view.suggested_compare_run_id == "run.family.beta.v1"
    assert view.suggested_compare_reason == "same_family_nearest_timestamp"


def test_evidence_delta_and_workbench_surfaces_are_deterministic(tmp_path: Path) -> None:
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
        pinned_run_ids=["run.partial.v1", "run.generalized_coverage.scopepass.v1"],
        action_history=[
            {
                "timestamp": "2026-03-28T03:00:01Z",
                "action_name": "run_compliance_probe",
                "run_id": "run.partial.v1",
                "outcome_status": "SUCCESS",
                "summary": "ok",
            }
        ],
        session_context={"source": "query"},
    )
    assert view.evidence_delta_preview["enabled"] is True
    assert view.evidence_delta_preview["artifact_path_delta"] == "changed"
    assert view.evidence_delta_preview["validator_path_delta"] == "changed"
    assert view.evidence_delta_preview["ledger_record_ids_delta"] == "+1"
    assert view.evidence_delta_preview["ledger_artifact_ids_delta"] == "+1"
    assert view.pin_panel["enabled"] is True
    assert view.pin_panel["items"] == ["run.generalized_coverage.scopepass.v1", "run.partial.v1"]
    assert view.action_history_limit == 10
    assert view.action_history[0]["action_name"] == "run_compliance_probe"
    assert view.workbench_header["suggested_focus_run_id"] == "run.generalized_coverage.scopepass.v1"
    assert len(view.attention_queue) >= 1
    assert view.session_context["source"] == "query"
    assert view.triage_limit_per_bucket == 5
    assert any(item["run_id"] == "run.partial.v1" for item in view.triage_panel["needs_action_now"])
    assert view.pinned_run_deep_cards[0]["run_id"] == "run.generalized_coverage.scopepass.v1"
    assert view.baseline_run_id is None
    assert view.baseline_reason == "no_baseline_candidate"
    assert view.action_safety_envelope["allowed_actions"] == [
        "run_compliance_probe",
        "run_generalized_coverage_probe",
        "run_execution_validator",
        "run_closure_audit",
        "export_operator_snapshot",
    ]
    assert view.latest_snapshot_report_status == "not_requested"
    assert view.latest_snapshot_report_path is None
    assert view.workbench_mode == "overview"
    assert view.attention_actions_enabled is True
    assert view.control_plane["allowed_actions"] == [
        "run_compliance_probe",
        "run_generalized_coverage_probe",
        "run_execution_validator",
        "run_closure_audit",
        "export_operator_snapshot",
    ]
    assert view.snapshot_report_payload["selected_run_id"] == "run.generalized_coverage.scopepass.v1"
    assert view.snapshot_recall_limit == 10
    assert view.loaded_snapshot_status == "not_requested"


def test_apply_suggested_compare_resolution_is_deterministic_and_context_safe(tmp_path: Path) -> None:
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

    first_view = build_view_state(
        base_dir=tmp_path,
        selected_run_id="run.generalized_coverage.scopepass.v1",
        health_filter="all",
        run_query="",
        sort_mode="latest_first",
        compare_run_id=None,
    )
    resolved_compare = resolve_compare_run_id_for_apply(
        compare_run_id=first_view.comparison_run_id,
        suggested_compare_run_id=first_view.suggested_compare_run_id,
        apply_suggested_compare=True,
    )
    view = build_view_state(
        base_dir=tmp_path,
        selected_run_id="run.generalized_coverage.scopepass.v1",
        health_filter="all",
        run_query="",
        sort_mode="latest_first",
        compare_run_id=resolved_compare,
    )
    assert view.selected_run_id == "run.generalized_coverage.scopepass.v1"
    assert view.focus_filters == {"health": "all", "run_query": "", "sort_mode": "latest_first"}
    assert view.comparison_run_id == "run.partial.v1"

    inert_compare = resolve_compare_run_id_for_apply(
        compare_run_id="run.partial.v1",
        suggested_compare_run_id=first_view.suggested_compare_run_id,
        apply_suggested_compare=True,
    )
    inert_view = build_view_state(
        base_dir=tmp_path,
        selected_run_id="run.generalized_coverage.scopepass.v1",
        health_filter="all",
        run_query="",
        sort_mode="latest_first",
        compare_run_id=inert_compare,
    )
    assert inert_view.comparison_run_id == "run.partial.v1"


def test_baseline_lock_and_mode_sanitization_are_deterministic(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    unlocked = build_view_state(base_dir=tmp_path, workbench_mode="compare")
    assert unlocked.workbench_mode == "compare"
    locked = build_view_state(
        base_dir=tmp_path,
        selected_run_id="run.generalized_coverage.scopepass.v1",
        baseline_locked_run_id="run.generalized_coverage.scopepass.v1",
        workbench_mode="unknown",
    )
    assert locked.workbench_mode == "overview"
    assert locked.baseline_locked is True
    assert locked.baseline_locked_run_id == "run.generalized_coverage.scopepass.v1"
    assert locked.baseline_lock_reason == "manual_lock"


def test_action_presets_and_selected_preset_are_deterministic(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(base_dir=tmp_path, selected_preset_id="preset.export.snapshot")
    assert [item["preset_id"] for item in view.action_presets] == [
        "preset.compliance_probe.default",
        "preset.generalized_coverage.probe",
        "preset.execution_validator.selected",
        "preset.closure_audit.default",
        "preset.export.snapshot",
    ]
    assert view.selected_preset_id == "preset.export.snapshot"


def test_dry_run_preview_is_preview_only_and_non_executing(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(
        base_dir=tmp_path,
        selected_preset_id="preset.export.snapshot",
        dry_run_enabled=True,
    )
    assert view.dry_run_preview["enabled"] is True
    assert view.dry_run_preview["status"] == "preview_only"
    assert view.dry_run_preview["action_name"] == "export_operator_snapshot"
    assert view.result_packet["status"] == "not_requested"


def test_result_packet_override_and_retry_reapply_are_explicit(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(
        base_dir=tmp_path,
        selected_preset_id="preset.compliance_probe.default",
        result_packet_override={
            "status": "SUCCESS",
            "preset_id": "preset.compliance_probe.default",
            "action_name": "run_compliance_probe",
            "run_id": "run.generalized_coverage.scopepass.v1",
            "artifact_path": "artifacts_seal/runs/generalized_coverage/run.generalized_coverage.scopepass.v1.artifact.json",
            "summary": "compliance probe completed",
        },
        retry_reapply_override={
            "enabled": True,
            "status": "ready",
            "last_action_name": "run_compliance_probe",
            "last_run_id": "run.generalized_coverage.scopepass.v1",
            "last_preset_id": "preset.compliance_probe.default",
        },
    )
    assert view.result_packet == {
        "status": "SUCCESS",
        "preset_id": "preset.compliance_probe.default",
        "action_name": "run_compliance_probe",
        "adapter_name": "",
        "attempted_at": "",
        "run_id": "run.generalized_coverage.scopepass.v1",
        "artifact_path": "artifacts_seal/runs/generalized_coverage/run.generalized_coverage.scopepass.v1.artifact.json",
        "artifact_paths": [],
        "error_info": "",
        "summary": "compliance probe completed",
    }
    assert view.retry_reapply == {
        "enabled": True,
        "status": "ready",
        "last_action_name": "run_compliance_probe",
        "last_run_id": "run.generalized_coverage.scopepass.v1",
        "last_preset_id": "preset.compliance_probe.default",
    }


def test_execution_ledger_is_ordered_and_bounded(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    history = []
    for idx in range(25):
        history.append(
            {
                "timestamp": f"2026-03-28T00:00:{idx:02d}Z",
                "action_name": "run_compliance_probe",
                "preset_id": "preset.compliance_probe.default",
                "run_id": f"run.synthetic.{idx}",
                "outcome_status": "SUCCESS",
                "summary": "ok",
            }
        )
    view = build_view_state(base_dir=tmp_path, action_history=history)
    assert view.execution_ledger_limit == 20
    assert len(view.execution_ledger) == 20
    assert view.execution_ledger[0]["run_id"] == "run.synthetic.0"
    assert view.execution_ledger[0]["preset_id"] == "preset.compliance_probe.default"


def test_reporting_runbook_handoff_checkpoint_and_quick_actions_are_deterministic(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(
        base_dir=tmp_path,
        selected_preset_id="preset.compliance_probe.default",
        action_history=[
            {
                "timestamp": "2026-03-29T00:00:00Z",
                "action_name": "run_compliance_probe",
                "preset_id": "preset.compliance_probe.default",
                "run_id": "run.generalized_coverage.scopepass.v1",
                "outcome_status": "SUCCESS",
                "summary": "ok",
            }
        ],
        latest_execution_report_status="written",
        latest_execution_report_path="artifacts_seal/operator_reports/execution_report.20260329T000000Z.json",
        latest_handoff_bundle_status="written",
        latest_handoff_bundle_path="artifacts_seal/operator_handoff/handoff_bundle.20260329T000000Z.json",
        latest_checkpoint_status="written",
        latest_checkpoint_path="artifacts_seal/operator_checkpoints/operator_checkpoint.20260329T000000Z.json",
        restored_checkpoint_status="loaded",
        restored_checkpoint_path="artifacts_seal/operator_checkpoints/operator_checkpoint.20260329T000000Z.json",
    )
    assert view.execution_report_preview["selected_preset_id"] == "preset.compliance_probe.default"
    assert len(view.execution_report_preview["execution_ledger_slice"]) == 1
    assert view.runbook_card["selected_run_id"] == "run.generalized_coverage.scopepass.v1"
    assert view.handoff_bundle_preview["selected_preset_id"] == "preset.compliance_probe.default"
    assert set(view.quick_actions["allowed_actions"]) == {
        "run_compliance_probe",
        "run_generalized_coverage_probe",
        "run_execution_validator",
        "run_closure_audit",
        "export_operator_snapshot",
    }
    assert view.checkpoint_preview["selected_preset_id"] == "preset.compliance_probe.default"
    assert view.latest_execution_report_status == "written"
    assert view.latest_handoff_bundle_status == "written"
    assert view.latest_checkpoint_status == "written"
    assert view.restored_checkpoint_status == "loaded"


def test_execute_runtime_adapter_runs_compliance_probe_deterministically(monkeypatch) -> None:
    class _Completed:
        returncode = 0
        stdout = "artifacts_seal/runs/compliance_probe/run.compliance_probe.v1.artifact.json\n"
        stderr = ""

    def _fake_run(cmd, capture_output, text, check):
        return _Completed()

    monkeypatch.setattr("webpanel.operator_console.subprocess.run", _fake_run)
    response = execute_runtime_adapter(
        action_name="run_compliance_probe",
        payload={"selected_run_id": "run.compliance_probe.v1"},
        allowed_actions=["run_compliance_probe"],
    )
    assert response["outcome_status"] == "SUCCESS"
    assert response["adapter_name"] == "adapter.run_compliance_probe"
    assert response["run_id"] == "run.compliance_probe.v1"


def test_execute_runtime_adapter_blocks_disallowed_actions() -> None:
    response = execute_runtime_adapter(
        action_name="run_execution_validator",
        payload={"selected_run_id": "run.x"},
        allowed_actions=["run_compliance_probe"],
    )
    assert response["outcome_status"] == "FAILED"
    assert response["error_info"] == "action_not_allowed"


def test_execute_runtime_adapter_converts_adapter_exceptions(monkeypatch) -> None:
    def _boom(payload):
        raise RuntimeError("adapter exploded")

    monkeypatch.setitem(operator_console._RUNTIME_ADAPTERS, "run_compliance_probe", _boom)
    response = execute_runtime_adapter(
        action_name="run_compliance_probe",
        payload={"selected_run_id": "run.x"},
        allowed_actions=["run_compliance_probe"],
    )
    assert response["outcome_status"] == "FAILED"
    assert "adapter exploded" in response["error_info"]


def test_runtime_audit_safety_runflow_and_health_surfaces_are_deterministic(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(
        base_dir=tmp_path,
        selected_preset_id="preset.execution_validator.selected",
        result_packet_override={
            "status": "FAILED",
            "preset_id": "preset.execution_validator.selected",
            "action_name": "run_execution_validator",
            "adapter_name": "adapter.run_execution_validator",
            "attempted_at": "2026-03-29T00:00:00Z",
            "run_id": "run.generalized_coverage.scopepass.v1",
            "artifact_path": "out/validators/execution-validation-run.generalized_coverage.scopepass.v1.json",
            "artifact_paths": ["out/validators/execution-validation-run.generalized_coverage.scopepass.v1.json"],
            "error_info": "validator failed",
            "summary": "execution validator failed for run.generalized_coverage.scopepass.v1",
        },
        action_history=[
            {
                "timestamp": "2026-03-29T00:00:00Z",
                "action_name": "run_execution_validator",
                "preset_id": "preset.execution_validator.selected",
                "adapter_name": "adapter.run_execution_validator",
                "run_id": "run.generalized_coverage.scopepass.v1",
                "outcome_status": "FAILED",
                "artifact_ref": "out/validators/execution-validation-run.generalized_coverage.scopepass.v1.json",
                "summary": "execution validator failed",
            }
        ],
        workbench_mode="runflow",
    )
    assert view.workbench_mode == "runflow"
    assert len(view.runtime_adapter_audit) >= 5
    assert view.runtime_adapter_audit[0]["action_name"] == "export_operator_snapshot"
    assert any(note["action_name"] == "run_execution_validator" for note in view.runtime_safety_notes)
    assert any(card["preset_id"] == "preset.execution_validator.selected" for card in view.runflow_cards)
    assert view.runtime_result_drilldown["validator_output_path"].startswith("out/validators/")
    assert view.runtime_result_drilldown["error_detail"] == "validator failed"
    assert view.adapter_health_checks["overall_status"] == "healthy"
    assert view.runflow_workspace["current_step"] == "inspect_result"
    assert view.runflow_workspace["focus_run_link"].startswith("/operator?run_id=")
    assert view.outcome_classification == {
        "label": "FAILED",
        "reason_code": "explicit_failed_status",
    }
    assert view.prior_result_diff["has_prior"] is False
    assert view.action_stability["label"] == "degraded"
    assert view.failure_triage["enabled"] is True
    assert view.result_provenance_panel["run_id"] == "run.generalized_coverage.scopepass.v1"
    assert view.runtime_outcome_review_workspace["review_mode"] == "runtime_review"


def test_runtime_outcome_review_classification_diff_stability_and_triage_rules(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    history = [
        {
            "timestamp": "2026-03-29T00:00:00Z",
            "action_name": "run_execution_validator",
            "preset_id": "preset.execution_validator.selected",
            "adapter_name": "adapter.run_execution_validator",
            "run_id": "run.generalized_coverage.scopepass.v0",
            "outcome_status": "SUCCESS",
            "artifact_ref": "out/validators/execution-validation-run.generalized_coverage.scopepass.v0.json",
            "summary": "execution validator passed",
        },
        {
            "timestamp": "2026-03-28T00:00:00Z",
            "action_name": "run_execution_validator",
            "preset_id": "preset.execution_validator.selected",
            "adapter_name": "adapter.run_execution_validator",
            "run_id": "run.generalized_coverage.scopepass.vx",
            "outcome_status": "FAILED",
            "artifact_ref": "",
            "summary": "execution validator failed",
        },
    ]

    success_view = build_view_state(
        base_dir=tmp_path,
        selected_preset_id="preset.execution_validator.selected",
        action_history=history,
        result_packet_override={
            "status": "SUCCESS",
            "preset_id": "preset.execution_validator.selected",
            "action_name": "run_execution_validator",
            "adapter_name": "adapter.run_execution_validator",
            "attempted_at": "2026-03-29T01:00:00Z",
            "run_id": "run.generalized_coverage.scopepass.v1",
            "artifact_path": "out/validators/execution-validation-run.generalized_coverage.scopepass.v1.json",
            "artifact_paths": ["out/validators/execution-validation-run.generalized_coverage.scopepass.v1.json"],
            "error_info": "",
            "summary": "execution validator passed for run.generalized_coverage.scopepass.v1",
        },
    )
    assert success_view.outcome_classification == {
        "label": "SUCCESS",
        "reason_code": "success_with_run_and_artifact",
    }
    assert success_view.prior_result_diff == {
        "has_prior": True,
        "prior_timestamp": "2026-03-29T00:00:00Z",
        "outcome_change": "unchanged",
        "run_id_change": "changed",
        "artifact_path_change": "changed",
        "output_count_delta": "no_change",
        "error_change": "unchanged",
    }
    assert success_view.action_stability["label"] == "degraded"
    assert success_view.failure_triage["enabled"] is False

    partial_view = build_view_state(
        base_dir=tmp_path,
        selected_preset_id="preset.execution_validator.selected",
        result_packet_override={
            "status": "SUCCESS",
            "preset_id": "preset.execution_validator.selected",
            "action_name": "run_execution_validator",
            "adapter_name": "adapter.run_execution_validator",
            "attempted_at": "2026-03-29T02:00:00Z",
            "run_id": "",
            "artifact_path": "",
            "artifact_paths": [],
            "error_info": "",
            "summary": "missing surfaces",
        },
    )
    assert partial_view.outcome_classification == {
        "label": "PARTIAL",
        "reason_code": "incomplete_success_surfaces",
    }
    assert partial_view.failure_triage["enabled"] is True
    assert partial_view.failure_triage["missing_fields"] == ["run_id", "artifact_paths"]
    assert partial_view.failure_triage["suggested_next_step"] == "Re-run action and verify run_id emission."

    not_computable_view = build_view_state(
        base_dir=tmp_path,
        selected_preset_id="preset.execution_validator.selected",
        result_packet_override={
            "status": "not_requested",
            "preset_id": "preset.execution_validator.selected",
            "action_name": "run_execution_validator",
            "adapter_name": "adapter.run_execution_validator",
            "attempted_at": "",
            "run_id": "",
            "artifact_path": "",
            "artifact_paths": [],
            "error_info": "",
            "summary": "not requested",
        },
    )
    assert not_computable_view.outcome_classification == {
        "label": "NOT_COMPUTABLE",
        "reason_code": "status_not_computable_or_preview",
    }
    assert not_computable_view.runtime_outcome_review_workspace == {
        "enabled": True,
        "review_mode": "runtime_review",
        "packet_status": "not_requested",
        "classification_label": "NOT_COMPUTABLE",
        "prior_diff_enabled": False,
        "stability_label": "not_available",
        "triage_enabled": True,
        "provenance_run_id": "",
    }


def test_decision_layer_classification_branches_are_deterministic(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    accept_view = build_view_state(
        base_dir=tmp_path,
        selected_preset_id="preset.execution_validator.selected",
        action_history=[
            {
                "timestamp": "2026-03-29T00:00:00Z",
                "action_name": "run_execution_validator",
                "preset_id": "preset.execution_validator.selected",
                "run_id": "run.generalized_coverage.scopepass.v1",
                "outcome_status": "SUCCESS",
                "artifact_ref": "out/validators/execution-validation-run.generalized_coverage.scopepass.v1.json",
            }
        ],
        result_packet_override={
            "status": "SUCCESS",
            "preset_id": "preset.execution_validator.selected",
            "action_name": "run_execution_validator",
            "run_id": "run.generalized_coverage.scopepass.v1",
            "artifact_paths": ["out/validators/execution-validation-run.generalized_coverage.scopepass.v1.json"],
            "summary": "ok",
        },
    )
    assert accept_view.decision_layer["decision_label"] == "ACCEPT"
    assert accept_view.decision_layer["decision_reason"] == "success_stable_complete"

    watch_view = build_view_state(
        base_dir=tmp_path,
        selected_preset_id="preset.execution_validator.selected",
        action_history=[
            {
                "timestamp": "2026-03-29T00:00:00Z",
                "action_name": "run_execution_validator",
                "preset_id": "preset.execution_validator.selected",
                "run_id": "run.a",
                "outcome_status": "SUCCESS",
                "artifact_ref": "out/validators/a.json",
            },
            {
                "timestamp": "2026-03-28T12:00:00Z",
                "action_name": "run_execution_validator",
                "preset_id": "preset.execution_validator.selected",
                "run_id": "run.c",
                "outcome_status": "SUCCESS",
                "artifact_ref": "out/validators/c.json",
            },
            {
                "timestamp": "2026-03-28T00:00:00Z",
                "action_name": "run_execution_validator",
                "preset_id": "preset.execution_validator.selected",
                "run_id": "run.b",
                "outcome_status": "FAILED",
                "artifact_ref": "",
            },
        ],
        result_packet_override={
            "status": "SUCCESS",
            "preset_id": "preset.execution_validator.selected",
            "action_name": "run_execution_validator",
            "run_id": "run.generalized_coverage.scopepass.v1",
            "artifact_paths": ["out/validators/execution-validation-run.generalized_coverage.scopepass.v1.json"],
            "summary": "ok",
        },
    )
    assert watch_view.decision_layer["decision_label"] == "WATCH"

    retry_view = build_view_state(
        base_dir=tmp_path,
        selected_preset_id="preset.execution_validator.selected",
        result_packet_override={
            "status": "FAILED",
            "preset_id": "preset.execution_validator.selected",
            "action_name": "run_execution_validator",
            "run_id": "",
            "artifact_paths": [],
            "error_info": "",
            "summary": "missing outputs",
        },
    )
    assert retry_view.decision_layer["decision_label"] == "RETRY"

    investigate_view = build_view_state(
        base_dir=tmp_path,
        selected_preset_id="preset.execution_validator.selected",
        result_packet_override={
            "status": "FAILED",
            "preset_id": "preset.execution_validator.selected",
            "action_name": "run_execution_validator",
            "run_id": "run.x",
            "artifact_paths": [],
            "error_info": "traceback",
            "summary": "failed",
        },
    )
    assert investigate_view.decision_layer["decision_label"] == "INVESTIGATE"


def test_decision_layer_history_is_bounded_and_workspace_integrated(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    history = []
    for idx in range(25):
        history.append(
            {
                "timestamp": f"2026-03-29T00:00:{idx:02d}Z",
                "action_name": "run_execution_validator",
                "preset_id": "preset.execution_validator.selected",
                "run_id": f"run.{idx}",
                "outcome_status": "SUCCESS" if idx % 2 == 0 else "FAILED",
                "artifact_ref": f"out/validators/run.{idx}.json" if idx % 2 == 0 else "",
            }
        )
    view = build_view_state(base_dir=tmp_path, action_history=history, workbench_mode="decision")
    assert view.workbench_mode == "decision"
    assert view.decision_layer["review_history_limit"] == 15
    assert len(view.decision_layer["review_history"]) == 15
    assert view.decision_workspace_payload["mode"] == "decision"
    assert view.decision_workspace_payload["review_history_count"] == 15


def test_session_continuity_timeline_diff_and_summary_are_deterministic(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    history = [
        {
            "timestamp": "2026-03-29T00:00:02Z",
            "action_name": "run_execution_validator",
            "preset_id": "preset.execution_validator.selected",
            "run_id": "run.alpha",
            "outcome_status": "SUCCESS",
            "artifact_ref": "out/validators/run.alpha.json",
        },
        {
            "timestamp": "2026-03-29T00:00:01Z",
            "action_name": "run_execution_validator",
            "preset_id": "preset.execution_validator.selected",
            "run_id": "run.alpha",
            "outcome_status": "FAILED",
            "artifact_ref": "",
        },
    ]
    view = build_view_state(
        base_dir=tmp_path,
        action_history=history,
        workbench_mode="session",
        session_closeout_status="written",
        session_closeout_path="artifacts_seal/operator_sessions/20260329T000003Z.session_closeout.json",
        recall_status="loaded",
        recall_path="artifacts_seal/operator_decisions/20260329T000001Z.run.alpha.decision.json",
    )
    assert view.workbench_mode == "session"
    assert view.session_continuity["decision_timeline_limit"] == 15
    assert len(view.session_continuity["decision_timeline"]) >= 2
    assert view.session_continuity["decision_diff"]["enabled"] in {"true", "false"}
    assert view.session_continuity["session_summary"]["actions_executed_count"] == 2
    assert view.session_continuity["session_closeout_status"] == "written"
    assert view.session_continuity["session_workspace_payload"]["mode"] == "session"
    assert view.session_continuity["recall_status"] == "loaded"


def test_governance_surface_gating_guards_and_workspace_are_deterministic(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(
        base_dir=tmp_path,
        selected_preset_id="preset.execution_validator.selected",
        workbench_mode="governance",
        action_history=[
            {
                "timestamp": "2026-03-29T00:00:00Z",
                "action_name": "run_execution_validator",
                "preset_id": "preset.execution_validator.selected",
                "run_id": "run.generalized_coverage.scopepass.v1",
                "outcome_status": "SUCCESS",
                "artifact_ref": "out/validators/execution-validation-run.generalized_coverage.scopepass.v1.json",
            }
        ],
        policy_snapshot_status="written",
        policy_snapshot_path="artifacts_seal/operator_policy/20260329T000000Z.policy_snapshot.json",
        policy_recall_status="loaded",
        policy_recall_path="artifacts_seal/operator_policy/20260329T000000Z.policy_snapshot.json",
    )
    assert view.workbench_mode == "governance"
    assert view.governance["policy_surface"]["policy_mode"] in {"review_only", "bounded_runtime", "decision_review"}
    assert len(view.governance["action_gating"]) >= 1
    assert any(row["guard_name"] == "selected_run_present" for row in view.governance["guard_conditions"])
    assert view.governance["policy_snapshot_status"] == "written"
    assert view.governance["policy_recall_status"] == "loaded"
    assert view.governance["governance_workspace_payload"]["mode"] == "governance"


def test_viz_integration_payloads_mode_and_workspace_are_deterministic(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(
        base_dir=tmp_path,
        selected_run_id="run.generalized_coverage.scopepass.v1",
        compare_run_id="run.generalized_coverage.scopepass.v1",
        viz_mode="invalid_mode",
        viz_export_status="written",
        viz_export_path="artifacts_seal/operator_viz/20260329T000000Z.viz_state.json",
    )
    assert view.viz_integration["viz_mode"] == "weather"
    assert set(view.viz_integration["viz_modes_allowed"]) == {"weather", "trace", "compare"}
    assert "weather" in view.viz_integration["viz_payloads"]
    assert "trace" in view.viz_integration["viz_payloads"]
    assert "compare" in view.viz_integration["viz_payloads"]
    assert view.viz_integration["viz_payloads"]["compare"]["enabled"] is False
    assert view.viz_integration["viz_workspace_payload"]["mode"] == "viz"
    assert view.viz_integration["viz_export_status"] == "written"


def test_viz_render_routing_and_export_preview_are_deterministic(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    weather_view = build_view_state(base_dir=tmp_path, viz_mode="weather")
    assert weather_view.viz_render["viz_render_mode"] == "weather"
    assert weather_view.viz_render["viz_render_output"]["title"] == "Weather View"
    assert weather_view.viz_render["viz_render_output"]["closure_status"] in {"GENERALIZED_CLOSURE_CONFIRMED", "NOT_COMPUTABLE"}
    assert weather_view.viz_render["viz_render_output"]["policy_mode"] in {"review_only", "bounded_runtime", "decision_review"}
    assert "run_health_distribution" in weather_view.viz_render["viz_render_output"]
    assert "attention_count" in weather_view.viz_render["viz_render_output"]
    assert "alert_highlight_count" in weather_view.viz_render["viz_render_output"]

    trace_view = build_view_state(
        base_dir=tmp_path,
        viz_mode="trace",
        viz_render_export_status="written",
        viz_render_export_path="artifacts_seal/operator_viz_render/20260329T000000Z.trace.render.json",
    )
    assert trace_view.viz_render["viz_render_mode"] == "trace"
    assert trace_view.viz_render["viz_render_output"]["title"] == "Trace View"
    assert "recent_activity_events" in trace_view.viz_render["viz_render_output"]
    assert "recent_decisions" in trace_view.viz_render["viz_render_output"]
    assert "recent_execution_ledger_slice" in trace_view.viz_render["viz_render_output"]
    assert trace_view.viz_render["viz_render_workspace_payload"]["mode"] == "viz"
    assert trace_view.viz_render["viz_render_export_status"] == "written"
    assert trace_view.viz_render["viz_render_export_preview"]["provenance"] == "operator_console.viz_render.v2.7.1.mode_routed"

    compare_view = build_view_state(base_dir=tmp_path, viz_mode="compare")
    assert compare_view.viz_render["viz_render_mode"] == "compare"
    assert compare_view.viz_render["viz_render_output"]["enabled"] is False
    assert compare_view.viz_render["viz_render_output"]["status"] == "not_computable"
    assert compare_view.viz_render["viz_render_workspace_payload"]["viz_render_mode"] == "compare"
    assert compare_view.viz_render["viz_render_workspace_payload"]["has_render_output"] is True


def test_viz_render_mode_default_and_unrelated_state_integrity(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    base_view = build_view_state(base_dir=tmp_path, viz_mode="weather")
    fallback_view = build_view_state(base_dir=tmp_path, viz_mode="unsupported")
    assert fallback_view.viz_render["viz_render_mode"] == "weather"
    assert fallback_view.focus_filters == base_view.focus_filters
    assert fallback_view.selected_run_id == base_view.selected_run_id
    assert fallback_view.available_runs == base_view.available_runs


def test_viz_render_export_artifact_is_written_with_bounded_schema(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(base_dir=tmp_path, viz_mode="trace")
    out_root = tmp_path / "artifacts_seal" / "operator_viz_render"
    path, status = operator_console.write_viz_render_artifact(
        preview=view.viz_render["viz_render_export_preview"],
        root=out_root,
    )
    assert status == "written"
    assert path is not None
    output_path = Path(path)
    assert output_path.exists()
    assert output_path.parent == out_root
    assert output_path.name.endswith(".trace.render.json")
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["viz_mode"] == "trace"
    assert "render_output" in payload
    assert "source_viz_payload" in payload
    assert "selected_context" in payload
    assert "timestamp" in payload
    assert "provenance" in payload
    assert "status" in payload


def test_reporting_workspace_and_publication_artifacts_are_deterministic(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(base_dir=tmp_path, workbench_mode="report", viz_mode="trace")
    assert view.workbench_mode == "report"
    assert view.reporting["reporting_workspace_payload"]["mode"] == "report"
    assert "session_report_preview" in view.reporting
    assert "decision_summary_preview" in view.reporting
    assert "viz_summary_preview" in view.reporting
    assert "closeout_bundle_preview" in view.reporting
    assert "# Operator Report" in view.reporting["markdown_preview"]

    out_root = tmp_path / "artifacts_seal" / "operator_reports"
    session_path, session_status = operator_console.write_operator_report_artifact(
        suffix="session_report",
        payload=view.reporting["session_report_preview"],
        root=out_root,
    )
    decision_run = str(view.reporting["decision_summary_preview"].get("run_id", "")) or "unselected"
    decision_path, decision_status = operator_console.write_operator_report_artifact(
        suffix=f"{decision_run}.decision_summary",
        payload=view.reporting["decision_summary_preview"],
        root=out_root,
    )
    viz_mode = str(view.reporting["viz_summary_preview"].get("viz_mode", "weather"))
    viz_path, viz_status = operator_console.write_operator_report_artifact(
        suffix=f"{viz_mode}.viz_summary",
        payload=view.reporting["viz_summary_preview"],
        root=out_root,
    )
    closeout_path, closeout_status = operator_console.write_operator_report_artifact(
        suffix="operator_closeout",
        payload=view.reporting["closeout_bundle_preview"],
        root=out_root,
    )
    markdown_path, markdown_status = operator_console.write_operator_markdown_report(
        markdown=view.reporting["markdown_preview"],
        root=out_root,
    )

    assert session_status == "written"
    assert decision_status == "written"
    assert viz_status == "written"
    assert closeout_status == "written"
    assert markdown_status == "written"
    assert session_path and Path(session_path).exists()
    assert decision_path and Path(decision_path).exists()
    assert viz_path and Path(viz_path).exists()
    assert closeout_path and Path(closeout_path).exists()
    assert markdown_path and Path(markdown_path).exists()

    session_payload = json.loads(Path(session_path).read_text(encoding="utf-8"))
    assert "session_summary" in session_payload
    assert "decision_timeline" in session_payload
    assert "governance_summary" in session_payload
    decision_payload = json.loads(Path(decision_path).read_text(encoding="utf-8"))
    assert "outcome_classification" in decision_payload
    assert "decision_label" in decision_payload
    viz_payload = json.loads(Path(viz_path).read_text(encoding="utf-8"))
    assert viz_payload["viz_mode"] == "trace"
    assert "render_output" in viz_payload
    closeout_payload = json.loads(Path(closeout_path).read_text(encoding="utf-8"))
    assert "session_report" in closeout_payload
    assert "latest_decision_summary" in closeout_payload
    assert "latest_viz_summary" in closeout_payload
    markdown_text = Path(markdown_path).read_text(encoding="utf-8")
    assert "## Session Summary" in markdown_text
    assert "## Decision Summary" in markdown_text
    assert "## Viz Summary" in markdown_text
