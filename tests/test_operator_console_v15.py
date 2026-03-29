from __future__ import annotations

import json
import os
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
    write_pipeline_artifact,
    write_pipeline_final_state_artifact,
    write_detector_signal_artifact,
    write_motif_signal_artifact,
    write_drift_signal_artifact,
    write_anomaly_signal_artifact,
    write_fusion_signal_artifact,
    write_synthesis_output_artifact,
    write_binding_health_artifact,
    write_pipeline_envelope_binding_artifact,
    write_run_id_propagation_artifact,
    write_pipeline_envelope_run_id_repair_artifact,
    write_context_restoration_artifact,
    write_pipeline_routing_artifact,
    write_pipeline_review_artifact,
    write_runtime_corridor_artifact,
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


def test_domain_logic_structural_signals_and_detector_labels_are_derived(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(base_dir=tmp_path, selected_run_id="run.generalized_coverage.scopepass.v1", workbench_mode="runtime")

    signals = view.domain_logic["structural_signals"]
    detector = view.domain_logic["pressure_friction_detector"]
    assert signals["missing_field_count"] >= 0
    assert "rule_ids" in signals
    assert detector["detector_id"] == "ABX.STRUCTURAL_PRESSURE.V4_2"
    assert detector["pressure_label"] in {"LOW", "MODERATE", "HIGH", "NOT_COMPUTABLE"}
    assert detector["friction_label"] in {"CLEAR", "FRICTION", "BLOCKED", "NOT_COMPUTABLE"}
    assert isinstance(detector["detector_summary"], str)


def test_domain_logic_detector_not_computable_without_selected_run(tmp_path: Path) -> None:
    view = build_view_state(base_dir=tmp_path, selected_run_id=None)
    detector = view.domain_logic["pressure_friction_detector"]
    assert detector["detector_status"] == "NOT_COMPUTABLE"
    assert detector["pressure_label"] == "NOT_COMPUTABLE"
    assert detector["friction_label"] == "NOT_COMPUTABLE"


def test_detector_signal_export_artifact_is_written_with_bounded_schema(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(base_dir=tmp_path, selected_run_id="run.generalized_coverage.scopepass.v1", workbench_mode="runtime")
    out_root = tmp_path / "artifacts_seal" / "abraxas_signals"
    path, status = write_detector_signal_artifact(payload=view.domain_logic["detector_export_preview"], root=out_root)
    assert status == "written"
    assert path is not None
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    assert payload["source"] == "operator_console"
    assert payload["rune_id"] == "RUNE.ERS"
    assert "structural_signals" in payload
    assert "pressure_friction_detector" in payload
    assert isinstance(payload["correlation_pointers"], list)


def test_domain_logic_workspace_payload_integrity(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(
        base_dir=tmp_path,
        selected_run_id="run.generalized_coverage.scopepass.v1",
        latest_detector_export_status="written",
        latest_detector_export_path="artifacts_seal/abraxas_signals/20260329T000000Z.abx_structural_pressure_v4_2.signal.json",
    )
    workspace = view.domain_logic["domain_logic_workspace_payload"]
    assert workspace["mode"] == "runtime"
    assert workspace["detector_export_status"] == "written"
    assert workspace["detector_export_path"].startswith("artifacts_seal/abraxas_signals/")


def test_motif_recurrence_signals_and_detector_are_derived(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(base_dir=tmp_path, selected_run_id="run.generalized_coverage.scopepass.v1", workbench_mode="runtime")
    signals = view.domain_logic["motif_recurrence_signals"]
    detector = view.domain_logic["motif_recurrence_detector"]
    assert signals["repeated_token_count"] >= 0
    assert signals["repeated_entity_count"] >= 0
    assert "motif_candidate_summaries" in signals
    assert detector["detector_id"] == "ABX.MOTIF_RECURRENCE.V4_3"
    assert detector["motif_label"] in {"SPARSE", "PRESENT", "DOMINANT", "NOT_COMPUTABLE"}
    assert detector["recurrence_label"] in {"NONE", "RECURRING", "PERSISTENT", "NOT_COMPUTABLE"}


def test_motif_detector_not_computable_without_selected_run(tmp_path: Path) -> None:
    view = build_view_state(base_dir=tmp_path, selected_run_id=None)
    detector = view.domain_logic["motif_recurrence_detector"]
    assert detector["detector_status"] == "NOT_COMPUTABLE"
    assert detector["motif_label"] == "NOT_COMPUTABLE"
    assert detector["recurrence_label"] == "NOT_COMPUTABLE"


def test_domain_logic_workspace_excludes_fusion_surface(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(base_dir=tmp_path, selected_run_id="run.generalized_coverage.scopepass.v1", workbench_mode="runtime")
    assert "detector_fusion_surface" not in view.domain_logic


def test_motif_export_artifact_is_written_with_bounded_schema(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(base_dir=tmp_path, selected_run_id="run.generalized_coverage.scopepass.v1", workbench_mode="runtime")
    out_root = tmp_path / "artifacts_seal" / "abraxas_signals"
    path, status = write_motif_signal_artifact(payload=view.domain_logic["motif_export_preview"], root=out_root)
    assert status == "written"
    assert path is not None
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    assert payload["source"] == "operator_console"
    assert payload["rune_id"] == "RUNE.ERS"
    assert "signal_extraction_output" in payload
    assert "detector_output" in payload
    assert isinstance(payload["correlation_pointers"], list)


def test_upgraded_domain_logic_workspace_integrity(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(
        base_dir=tmp_path,
        selected_run_id="run.generalized_coverage.scopepass.v1",
        latest_detector_export_status="written",
        latest_detector_export_path="artifacts_seal/abraxas_signals/20260329T000000Z.abx_structural_pressure_v4_2.signal.json",
        latest_motif_export_status="written",
        latest_motif_export_path="artifacts_seal/abraxas_signals/20260329T000000Z.abx_motif_recurrence_v4_3.motif_signal.json",
    )
    workspace = view.domain_logic["domain_logic_workspace_payload"]
    assert workspace["mode"] == "runtime"
    assert workspace["motif_export_status"] == "written"
    assert workspace["motif_export_path"].endswith(".motif_signal.json")
    assert view.domain_logic["updated_domain_logic_workspace_payload"]["motif_export_status"] == "written"


def test_motif_domain_logic_does_not_mutate_unrelated_selected_detail(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    base_view = build_view_state(base_dir=tmp_path, selected_run_id="run.generalized_coverage.scopepass.v1")
    motif_view = build_view_state(
        base_dir=tmp_path,
        selected_run_id="run.generalized_coverage.scopepass.v1",
        latest_motif_export_status="written",
        latest_motif_export_path="artifacts_seal/abraxas_signals/20260329T000000Z.abx_motif_recurrence_v4_3.motif_signal.json",
    )
    assert motif_view.selected_run_detail == base_view.selected_run_detail
    assert motif_view.pipeline_hardening == base_view.pipeline_hardening


def test_instability_drift_signals_and_detector_are_derived(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(base_dir=tmp_path, selected_run_id="run.generalized_coverage.scopepass.v1", workbench_mode="runtime")
    signals = view.domain_logic["instability_drift_signals"]
    detector = view.domain_logic["instability_drift_detector"]
    assert signals["status_change_count"] >= 0
    assert signals["queue_change_count"] >= 0
    assert detector["instability_label"] in {"STABLE", "SHIFTING", "UNSTABLE", "NOT_COMPUTABLE"}
    assert detector["drift_label"] in {"NONE", "MINOR", "SIGNIFICANT", "NOT_COMPUTABLE"}


def test_instability_drift_detector_not_computable_without_selected_run(tmp_path: Path) -> None:
    view = build_view_state(base_dir=tmp_path, selected_run_id=None)
    detector = view.domain_logic["instability_drift_detector"]
    assert detector["detector_status"] == "NOT_COMPUTABLE"
    assert detector["instability_label"] == "NOT_COMPUTABLE"
    assert detector["drift_label"] == "NOT_COMPUTABLE"


def test_drift_export_artifact_is_written_with_bounded_schema(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(base_dir=tmp_path, selected_run_id="run.generalized_coverage.scopepass.v1", workbench_mode="runtime")
    out_root = tmp_path / "artifacts_seal" / "abraxas_signals"
    path, status = write_drift_signal_artifact(payload=view.domain_logic["drift_export_preview"], root=out_root)
    assert status == "written"
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    assert payload["source"] == "operator_console"
    assert payload["rune_id"] == "RUNE.DIFF"
    assert "signal_extraction_output" in payload
    assert "detector_output" in payload


def test_anomaly_gap_signals_and_detector_are_derived(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(base_dir=tmp_path, selected_run_id="run.generalized_coverage.scopepass.v1", workbench_mode="runtime")
    signals = view.domain_logic["anomaly_gap_signals"]
    detector = view.domain_logic["anomaly_gap_detector"]
    assert signals["missing_artifact_count"] >= 0
    assert signals["missing_linkage_count"] >= 0
    assert detector["anomaly_label"] in {"NONE", "MINOR", "MAJOR", "NOT_COMPUTABLE"}
    assert detector["gap_label"] in {"COMPLETE", "INCOMPLETE", "BROKEN", "NOT_COMPUTABLE"}


def test_anomaly_gap_detector_not_computable_without_selected_run(tmp_path: Path) -> None:
    view = build_view_state(base_dir=tmp_path, selected_run_id=None)
    detector = view.domain_logic["anomaly_gap_detector"]
    assert detector["detector_status"] == "NOT_COMPUTABLE"
    assert detector["anomaly_label"] == "NOT_COMPUTABLE"
    assert detector["gap_label"] == "NOT_COMPUTABLE"


def test_anomaly_export_artifact_is_written_with_bounded_schema(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(base_dir=tmp_path, selected_run_id="run.generalized_coverage.scopepass.v1", workbench_mode="runtime")
    out_root = tmp_path / "artifacts_seal" / "abraxas_signals"
    path, status = write_anomaly_signal_artifact(payload=view.domain_logic["anomaly_export_preview"], root=out_root)
    assert status == "written"
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    assert payload["source"] == "operator_console"
    assert payload["rune_id"] == "RUNE.ERS"
    assert "signal_extraction_output" in payload
    assert "detector_output" in payload


def test_domain_logic_workspace_integrity_with_all_detector_families(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(
        base_dir=tmp_path,
        selected_run_id="run.generalized_coverage.scopepass.v1",
        latest_detector_export_status="written",
        latest_motif_export_status="written",
        latest_drift_export_status="written",
        latest_anomaly_export_status="written",
        latest_fusion_export_status="written",
    )
    workspace = view.domain_logic["updated_domain_logic_workspace_payload"]
    assert workspace["detector_export_status"] == "written"
    assert workspace["motif_export_status"] == "written"
    assert workspace["drift_export_status"] == "written"
    assert workspace["anomaly_export_status"] == "written"
    assert workspace["fusion_export_status"] == "written"


def test_fusion_input_surface_and_output_are_derived(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(base_dir=tmp_path, selected_run_id="run.generalized_coverage.scopepass.v1", workbench_mode="runtime")
    fusion_input = view.domain_logic["fusion_input_surface"]
    fusion_output = view.domain_logic["detector_fusion_output"]
    assert "pressure_label" in fusion_input
    assert "motif_label" in fusion_input
    assert fusion_output["fused_status"] in {"SUCCESS", "NOT_COMPUTABLE"}
    assert fusion_output["fused_label"] in {
        "STABLE_PATTERN",
        "ACTIVE_FRICTION",
        "UNSTABLE_TRANSITION",
        "BROKEN_SIGNAL",
        "INCOMPLETE_CONTEXT",
        "NOT_COMPUTABLE",
    }
    assert isinstance(fusion_output["fused_reasons"], list)
    assert isinstance(view.domain_logic["interpretation_summary"], str)


def test_fusion_label_branches_are_explicit_and_deterministic() -> None:
    base_input = {
        "pressure_label": "LOW",
        "friction_label": "CLEAR",
        "motif_label": "SPARSE",
        "recurrence_label": "NONE",
        "instability_label": "STABLE",
        "drift_label": "NONE",
        "anomaly_label": "NONE",
        "gap_label": "COMPLETE",
    }
    success_detector = {"detector_status": "SUCCESS"}

    stable = operator_console._derive_detector_fusion_output(
        selected_run_id="run.scope",
        fusion_input_surface=base_input,
        pressure_friction_detector=success_detector,
        motif_recurrence_detector=success_detector,
        instability_drift_detector=success_detector,
        anomaly_gap_detector=success_detector,
    )
    assert stable["fused_label"] == "STABLE_PATTERN"

    active = operator_console._derive_detector_fusion_output(
        selected_run_id="run.scope",
        fusion_input_surface={**base_input, "pressure_label": "HIGH"},
        pressure_friction_detector=success_detector,
        motif_recurrence_detector=success_detector,
        instability_drift_detector=success_detector,
        anomaly_gap_detector=success_detector,
    )
    assert active["fused_label"] == "ACTIVE_FRICTION"

    unstable = operator_console._derive_detector_fusion_output(
        selected_run_id="run.scope",
        fusion_input_surface={**base_input, "instability_label": "UNSTABLE", "drift_label": "SIGNIFICANT"},
        pressure_friction_detector=success_detector,
        motif_recurrence_detector=success_detector,
        instability_drift_detector=success_detector,
        anomaly_gap_detector=success_detector,
    )
    assert unstable["fused_label"] == "UNSTABLE_TRANSITION"

    incomplete = operator_console._derive_detector_fusion_output(
        selected_run_id="run.scope",
        fusion_input_surface={**base_input, "anomaly_label": "MINOR", "gap_label": "INCOMPLETE"},
        pressure_friction_detector=success_detector,
        motif_recurrence_detector=success_detector,
        instability_drift_detector=success_detector,
        anomaly_gap_detector=success_detector,
    )
    assert incomplete["fused_label"] == "INCOMPLETE_CONTEXT"

    broken = operator_console._derive_detector_fusion_output(
        selected_run_id="run.scope",
        fusion_input_surface={**base_input, "anomaly_label": "MAJOR", "gap_label": "BROKEN"},
        pressure_friction_detector=success_detector,
        motif_recurrence_detector=success_detector,
        instability_drift_detector=success_detector,
        anomaly_gap_detector=success_detector,
    )
    assert broken["fused_label"] == "BROKEN_SIGNAL"


def test_fusion_not_computable_without_selected_run(tmp_path: Path) -> None:
    view = build_view_state(base_dir=tmp_path, selected_run_id=None)
    fusion_output = view.domain_logic["detector_fusion_output"]
    assert fusion_output["fused_status"] == "NOT_COMPUTABLE"
    assert fusion_output["fused_label"] == "NOT_COMPUTABLE"


def test_fusion_not_computable_when_any_detector_input_is_not_computable() -> None:
    fused = operator_console._derive_detector_fusion_output(
        selected_run_id="run.scope",
        fusion_input_surface={
            "pressure_label": "LOW",
            "friction_label": "CLEAR",
            "motif_label": "SPARSE",
            "recurrence_label": "NONE",
            "instability_label": "STABLE",
            "drift_label": "NONE",
            "anomaly_label": "NONE",
            "gap_label": "COMPLETE",
        },
        pressure_friction_detector={"detector_status": "SUCCESS"},
        motif_recurrence_detector={"detector_status": "NOT_COMPUTABLE"},
        instability_drift_detector={"detector_status": "SUCCESS"},
        anomaly_gap_detector={"detector_status": "SUCCESS"},
    )
    assert fused["fused_status"] == "NOT_COMPUTABLE"
    assert fused["fused_label"] == "NOT_COMPUTABLE"


def test_fusion_export_artifact_is_written_with_bounded_schema(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(base_dir=tmp_path, selected_run_id="run.generalized_coverage.scopepass.v1", workbench_mode="runtime")
    out_root = tmp_path / "artifacts_seal" / "abraxas_signals"
    path, status = write_fusion_signal_artifact(payload=view.domain_logic["fusion_export_preview"], root=out_root)
    assert status == "written"
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    assert payload["source"] == "operator_console"
    assert payload["rune_id"] == "RUNE.DIFF"
    assert "source_detector_summaries" in payload
    assert "fused_output" in payload
    assert "interpretation_summary" in payload


def test_fusion_domain_logic_does_not_mutate_unrelated_state(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    base_view = build_view_state(base_dir=tmp_path, selected_run_id="run.generalized_coverage.scopepass.v1")
    fusion_view = build_view_state(
        base_dir=tmp_path,
        selected_run_id="run.generalized_coverage.scopepass.v1",
        latest_fusion_export_status="written",
        latest_fusion_export_path="artifacts_seal/abraxas_signals/20260329T000000Z.fusion_signal.json",
    )
    assert fusion_view.selected_run_detail == base_view.selected_run_detail
    assert fusion_view.pipeline_hardening == base_view.pipeline_hardening


def test_domain_logic_workspace_integrity_with_fusion_included(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(
        base_dir=tmp_path,
        selected_run_id="run.generalized_coverage.scopepass.v1",
        latest_fusion_export_status="written",
        latest_fusion_export_path="artifacts_seal/abraxas_signals/20260329T000000Z.fusion_signal.json",
    )
    workspace = view.domain_logic["updated_domain_logic_workspace_payload"]
    assert workspace["fusion_export_status"] == "written"
    assert workspace["fusion_export_path"].endswith(".fusion_signal.json")
    assert workspace["fusion_label"] in {
        "STABLE_PATTERN",
        "ACTIVE_FRICTION",
        "UNSTABLE_TRANSITION",
        "BROKEN_SIGNAL",
        "INCOMPLETE_CONTEXT",
        "NOT_COMPUTABLE",
    }


def test_abraxas_synthesis_input_surface_is_derived(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(base_dir=tmp_path, selected_run_id="run.generalized_coverage.scopepass.v1", workbench_mode="runtime")
    synthesis_input = view.abraxas_synthesis["synthesis_input_surface"]
    assert synthesis_input["pipeline_id"] != ""
    assert synthesis_input["routing_effective_pipeline_id"] != ""
    assert synthesis_input["governance_policy_mode"] in {"review_only", "bounded_runtime", "decision_review"}
    assert "fusion_label" in synthesis_input


def test_abraxas_synthesis_classification_branches_are_explicit() -> None:
    blocked = operator_console._derive_abraxas_synthesis_output(
        synthesis_input_surface={
            "pipeline_status": "FAILED",
            "fusion_label": "BROKEN_SIGNAL",
            "fusion_status": "SUCCESS",
            "governance_policy_mode": "review_only",
            "runtime_outcome_status": "FAILED",
            "runtime_blocker_summary": ["run_execution_validator:selected_run_missing"],
        },
        selected_run_id="run.scope",
    )
    assert blocked["synthesis_label"] == "BLOCKED"

    incomplete = operator_console._derive_abraxas_synthesis_output(
        synthesis_input_surface={
            "pipeline_status": "SUCCESS",
            "fusion_label": "INCOMPLETE_CONTEXT",
            "fusion_status": "SUCCESS",
            "governance_policy_mode": "review_only",
            "runtime_outcome_status": "PARTIAL",
            "runtime_blocker_summary": [],
        },
        selected_run_id="run.scope",
    )
    assert incomplete["synthesis_label"] == "INCOMPLETE"

    ready = operator_console._derive_abraxas_synthesis_output(
        synthesis_input_surface={
            "pipeline_status": "SUCCESS",
            "fusion_label": "STABLE_PATTERN",
            "fusion_status": "SUCCESS",
            "governance_policy_mode": "bounded_runtime",
            "runtime_outcome_status": "SUCCESS",
            "runtime_blocker_summary": [],
        },
        selected_run_id="run.scope",
    )
    assert ready["synthesis_label"] == "READY"


def test_abraxas_synthesis_not_computable_without_selected_run() -> None:
    output = operator_console._derive_abraxas_synthesis_output(
        synthesis_input_surface={},
        selected_run_id=None,
    )
    assert output["synthesis_status"] == "NOT_COMPUTABLE"
    assert output["synthesis_label"] == "NOT_COMPUTABLE"


def test_synthesis_export_artifact_is_written_with_bounded_schema(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(base_dir=tmp_path, selected_run_id="run.generalized_coverage.scopepass.v1", workbench_mode="runtime")
    out_root = tmp_path / "artifacts_seal" / "abraxas_output"
    path, status = write_synthesis_output_artifact(payload=view.abraxas_synthesis["synthesis_export_preview"], root=out_root)
    assert status == "written"
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    assert payload["source"] == "operator_console"
    assert payload["rune_id"] == "RUNE.AUDIT"
    assert "synthesis_input_surface" in payload
    assert "synthesis_label" in payload
    assert "synthesis_next_step" in payload


def test_final_abraxas_output_card_integrity(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(base_dir=tmp_path, selected_run_id="run.generalized_coverage.scopepass.v1", workbench_mode="runtime")
    card = view.abraxas_synthesis["final_abraxas_output_card"]
    assert card["synthesis_label"] in {"READY", "ACTIVE", "FRICTION", "UNSTABLE", "BLOCKED", "INCOMPLETE", "NOT_COMPUTABLE"}
    assert isinstance(card["short_reasons"], list)
    assert isinstance(card["next_step"], str)


def test_synthesis_layer_does_not_mutate_unrelated_state(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    base_view = build_view_state(base_dir=tmp_path, selected_run_id="run.generalized_coverage.scopepass.v1")
    synthesis_view = build_view_state(
        base_dir=tmp_path,
        selected_run_id="run.generalized_coverage.scopepass.v1",
        latest_synthesis_export_status="written",
        latest_synthesis_export_path="artifacts_seal/abraxas_output/20260329T000000Z.synthesis.json",
    )
    assert synthesis_view.selected_run_detail == base_view.selected_run_detail
    assert synthesis_view.pipeline_routing == base_view.pipeline_routing


def test_run_binding_restoration_derives_bound_context_and_subcodes(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(base_dir=tmp_path, selected_run_id="run.generalized_coverage.scopepass.v1", workbench_mode="runtime")
    bound = view.binding_restoration["bound_run_context"]
    subcodes = view.binding_restoration["not_computable_subcodes"]
    assert bound["binding_status"] in {"BOUND", "PARTIAL_BOUND", "MISSING"}
    assert isinstance(bound["bound_artifact_paths"], list)
    assert isinstance(subcodes, list)


def test_ledger_bridge_surface_is_derived_and_bounded(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(base_dir=tmp_path, selected_run_id="run.generalized_coverage.scopepass.v1", workbench_mode="runtime")
    bridge = view.binding_restoration["ledger_bridge"]
    assert bridge["ledger_bridge_status"] in {"LINKED", "PARTIAL_LINKED", "MISSING"}
    assert isinstance(bridge["related_ledger_record_ids"], list)
    assert isinstance(bridge["related_ledger_artifact_ids"], list)


def test_binding_health_surface_pass_fail_and_summary(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(base_dir=tmp_path, selected_run_id="run.generalized_coverage.scopepass.v1")
    health = view.binding_restoration["binding_health_surface"]
    assert health["run_binding_state"] in {"pass", "fail"}
    assert health["artifact_linkage_state"] in {"pass", "fail"}
    assert health["ledger_bridge_state"] in {"pass", "fail"}
    assert health["detector_ready_state"] in {"pass", "fail"}
    assert isinstance(health["summary"], str)


def test_binding_export_artifact_is_written_with_bounded_schema(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(base_dir=tmp_path, selected_run_id="run.generalized_coverage.scopepass.v1", workbench_mode="runtime")
    out_root = tmp_path / "artifacts_seal" / "abraxas_binding"
    path, status = write_binding_health_artifact(payload=view.binding_restoration["binding_export_preview"], root=out_root)
    assert status == "written"
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    assert payload["source"] == "operator_console"
    assert payload["rune_id"] == "RUNE.AUDIT"
    assert "binding_surface" in payload
    assert "ledger_bridge_surface" in payload
    assert "not_computable_subcodes" in payload


def test_not_computable_subcode_precision_when_run_binding_missing(tmp_path: Path) -> None:
    view = build_view_state(base_dir=tmp_path, selected_run_id=None, workbench_mode="runtime")
    subcodes = view.binding_restoration["not_computable_subcodes"]
    assert "NC_MISSING_RUN_BINDING" in subcodes
    fusion = view.domain_logic["detector_fusion_output"]
    synthesis = view.abraxas_synthesis
    assert fusion.get("not_computable_subcode", "NC_MISSING_REQUIRED_CONTEXT").startswith("NC_")
    assert synthesis.get("synthesis_label", "NOT_COMPUTABLE") == "NOT_COMPUTABLE"


def test_operator_bound_run_context_uses_runtime_invocation_priority() -> None:
    ctx = operator_console._derive_operator_bound_run_context(
        selected_run_id="run.v1",
        runtime_invocation_envelope={"run_id": "run.v1", "pipeline_id": "PIPE.A"},
        latest_pipeline_envelope={"run_id": "run.fallback", "pipeline_id": "PIPE.F"},
        latest_pipeline_export_path="artifacts_seal/abraxas_pipeline/x.json",
        latest_pipeline_export_status="written",
        pipeline_binding_snapshot={"payload": {"pipeline_execution_envelope": {"run_id": "run.snap", "pipeline_id": "PIPE.S"}}},
    )
    assert ctx["operator_binding_source"] == "runtime_invocation"
    assert ctx["operator_binding_status"] == "BOUND"
    assert ctx["operator_bound_run_id"] == "run.v1"


def test_pipeline_envelope_linkage_binds_from_artifact_snapshot_when_latest_missing() -> None:
    linkage = operator_console._derive_pipeline_envelope_linkage(
        latest_pipeline_envelope={"overall_status": "NOT_COMPUTABLE", "final_classification": "NOT_COMPUTABLE"},
        latest_pipeline_steps=[],
        pipeline_binding_snapshot={
            "payload": {
                "pipeline_execution_envelope": {"overall_status": "SUCCESS", "final_classification": "SUCCESS"},
                "pipeline_step_records": [{"step_name": "review_audit", "status": "SUCCESS"}],
            }
        },
        operator_bound_run_context={"operator_binding_status": "BOUND"},
    )
    assert linkage["envelope_binding_status"] == "BOUND"
    assert linkage["final_state_source_available"] is True
    assert linkage["resolution_source"] == "pipeline_envelope_artifact"


def test_load_latest_pipeline_binding_snapshot_prefers_matching_run_id(tmp_path: Path) -> None:
    root = tmp_path / "artifacts_seal" / "abraxas_pipeline"
    older = root / "20260328T010000Z.pipeline.json"
    newer = root / "20260329T010000Z.pipeline.json"
    _write_json(
        older,
        {
            "pipeline_execution_envelope": {
                "run_id": "run.selected.v1",
                "pipeline_id": "PIPE.ABRAXAS.CORE",
                "overall_status": "SUCCESS",
                "final_classification": "SUCCESS",
            }
        },
    )
    _write_json(
        newer,
        {
            "pipeline_execution_envelope": {
                "run_id": "run.other.v1",
                "pipeline_id": "PIPE.ABRAXAS.CORE",
                "overall_status": "SUCCESS",
                "final_classification": "SUCCESS",
            }
        },
    )
    os.utime(older, (1, 1))
    os.utime(newer, (2, 2))
    snapshot = operator_console._load_latest_pipeline_binding_snapshot(tmp_path, preferred_run_id="run.selected.v1")
    envelope = snapshot["payload"]["pipeline_execution_envelope"]
    assert envelope["run_id"] == "run.selected.v1"


def test_load_latest_pipeline_binding_snapshot_normalizes_pipeline_envelope_key(tmp_path: Path) -> None:
    root = tmp_path / "artifacts_seal" / "abraxas_pipeline"
    path = root / "20260329T010000Z.pipeline.json"
    _write_json(
        path,
        {
            "pipeline_envelope": {
                "run_id": "run.selected.v1",
                "pipeline_id": "PIPE.ABRAXAS.CORE",
                "overall_status": "SUCCESS",
                "final_classification": "SUCCESS",
            },
            "pipeline_step_records": [{"step_name": "review_audit", "status": "SUCCESS"}],
        },
    )
    snapshot = operator_console._load_latest_pipeline_binding_snapshot(tmp_path, preferred_run_id="run.selected.v1")
    envelope = snapshot["payload"]["pipeline_execution_envelope"]
    assert envelope["run_id"] == "run.selected.v1"


def test_selected_run_snapshot_exact_match_drives_bindable_final_state_and_synthesis(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    root = tmp_path / "artifacts_seal" / "abraxas_pipeline"
    selected_path = root / "20260328T010000Z.pipeline.json"
    newer_other_path = root / "20260329T010000Z.pipeline.json"
    _write_json(
        selected_path,
        {
            "pipeline_execution_envelope": {
                "run_id": "run.generalized_coverage.scopepass.v1",
                "pipeline_id": "PIPE.ABRAXAS.CORE",
                "overall_status": "SUCCESS",
                "final_classification": "SUCCESS",
                "final_result_summary": "SUCCESS|scopepass",
            },
            "pipeline_step_records": [{"step_name": "review_audit", "status": "SUCCESS"}],
        },
    )
    _write_json(
        newer_other_path,
        {
            "pipeline_execution_envelope": {
                "run_id": "run.other.v1",
                "pipeline_id": "PIPE.ABRAXAS.CORE",
                "overall_status": "FAILED",
                "final_classification": "FAILED",
            },
            "pipeline_step_records": [{"step_name": "review_audit", "status": "FAILED"}],
        },
    )
    os.utime(selected_path, (1, 1))
    os.utime(newer_other_path, (2, 2))
    view = build_view_state(base_dir=tmp_path, selected_run_id="run.generalized_coverage.scopepass.v1")
    linkage = view.binding_restoration["pipeline_envelope_linkage"]
    assert linkage["resolution_source"] == "pipeline_envelope_artifact"
    assert linkage["run_id_match_status"] == "EXACT_MATCH"
    assert view.binding_restoration["final_state_bindable"] is True
    synthesis_input = view.abraxas_synthesis["synthesis_input_surface"]
    assert synthesis_input["pipeline_final_state"]["pipeline_final_status"] == "SUCCESS"
    assert synthesis_input["pipeline_final_state"]["pipeline_status_resolved"] is True


def test_binding_envelope_health_surface_true_false_branches() -> None:
    pass_surface = operator_console._derive_binding_envelope_health_surface(
        operator_bound_run_context={"operator_binding_status": "BOUND"},
        pipeline_envelope_linkage={"envelope_binding_status": "BOUND", "final_state_source_available": True, "resolution_source": "latest_pipeline_envelope"},
    )
    fail_surface = operator_console._derive_binding_envelope_health_surface(
        operator_bound_run_context={"operator_binding_status": "UNBOUND"},
        pipeline_envelope_linkage={"envelope_binding_status": "UNBOUND", "final_state_source_available": False, "resolution_source": "none"},
    )
    assert pass_surface["final_state_derivable"] is True
    assert pass_surface["synthesis_blocked_by_binding"] is False
    assert fail_surface["final_state_derivable"] is False
    assert fail_surface["blocking_reason"] == "NC_OPERATOR_RUN_UNBOUND"


def test_refined_binding_nc_subcodes_are_precise() -> None:
    subcodes = operator_console._derive_refined_binding_nc_subcodes(
        operator_bound_run_context={"operator_binding_status": "UNBOUND"},
        pipeline_envelope_linkage={"envelope_binding_status": "UNBOUND", "final_state_source_available": False},
    )
    assert "NC_OPERATOR_RUN_UNBOUND" in subcodes
    assert "NC_PIPELINE_ENVELOPE_UNBOUND" in subcodes


def test_binding_envelope_export_artifact_is_written_with_bounded_schema(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(base_dir=tmp_path, selected_run_id="run.generalized_coverage.scopepass.v1", workbench_mode="runtime")
    out_root = tmp_path / "artifacts_seal" / "abraxas_binding"
    path, status = write_pipeline_envelope_binding_artifact(payload=view.binding_restoration["binding_envelope_export_preview"], root=out_root)
    assert status == "written"
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    assert payload["source"] == "operator_console"
    assert payload["rune_id"] == "RUNE.BINDING"
    assert "operator_bound_run_context" in payload
    assert "pipeline_envelope_linkage" in payload
    assert "binding_envelope_health_surface" in payload


def test_synthesis_input_uses_binding_specific_subcode_when_final_state_unresolved(tmp_path: Path) -> None:
    view = build_view_state(base_dir=tmp_path, selected_run_id=None, workbench_mode="runtime")
    synthesis_input = view.abraxas_synthesis["synthesis_input_surface"]
    assert synthesis_input["pipeline_unresolved_subcode"] in {"NC_OPERATOR_RUN_UNBOUND", "NC_PIPELINE_ENVELOPE_UNBOUND", "NC_FINAL_STATE_SOURCE_MISSING", "NC_PIPELINE_STATUS_UNRESOLVED"}


def test_binding_envelope_export_status_does_not_mutate_unrelated_state(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    base_view = build_view_state(base_dir=tmp_path, selected_run_id="run.generalized_coverage.scopepass.v1")
    state_view = build_view_state(
        base_dir=tmp_path,
        selected_run_id="run.generalized_coverage.scopepass.v1",
        latest_binding_envelope_export_status="written",
        latest_binding_envelope_export_path="artifacts_seal/abraxas_binding/20260329T000000Z.pipeline_envelope_binding.json",
    )
    assert state_view.selected_run_detail == base_view.selected_run_detail
    assert state_view.pipeline_routing == base_view.pipeline_routing


def test_invocation_run_id_normalization_prefers_action_history_then_selected() -> None:
    envelope = operator_console._derive_runtime_invocation_envelope(
        last_action={"action_name": "run_abraxas_pipeline", "triggered_run_id": "run.action.v1"},
        selected_run_id="run.selected.v1",
    )
    assert envelope["invocation_run_id"] == "run.action.v1"
    assert envelope["invocation_run_id_source"] == "action_history"
    assert envelope["invocation_run_id_status"] == "PRESENT"


def test_pipeline_adapter_run_id_propagates_into_envelope_and_steps() -> None:
    result = execute_runtime_adapter(
        action_name="run_abraxas_pipeline",
        payload={"selected_run_id": "run.generalized_coverage.scopepass.v1"},
        allowed_actions=["run_abraxas_pipeline"],
    )
    envelope = dict(result.get("pipeline_envelope", {}))
    step_records = [row for row in result.get("pipeline_step_records", []) if isinstance(row, dict)]
    assert envelope.get("run_id") == "run.generalized_coverage.scopepass.v1"
    assert all(
        str((row.get("input_summary", {}) if isinstance(row.get("input_summary", {}), dict) else {}).get("selected_run_id", ""))
        in {"", "run.generalized_coverage.scopepass.v1"}
        for row in step_records
    )


def test_envelope_linkage_reports_run_id_match_status_exact() -> None:
    linkage = operator_console._derive_pipeline_envelope_linkage(
        latest_pipeline_envelope={"run_id": "run.v1", "overall_status": "SUCCESS", "final_classification": "SUCCESS"},
        latest_pipeline_steps=[],
        pipeline_binding_snapshot={},
        operator_bound_run_context={"operator_binding_status": "BOUND", "invocation_run_id": "run.v1"},
    )
    assert linkage["pipeline_envelope_run_id"] == "run.v1"
    assert linkage["run_id_match_status"] == "EXACT_MATCH"


def test_final_state_bindable_true_false_branches() -> None:
    true_surface = operator_console._derive_binding_envelope_health_surface(
        operator_bound_run_context={"operator_binding_status": "BOUND", "invocation_run_id_status": "PRESENT"},
        pipeline_envelope_linkage={
            "envelope_binding_status": "BOUND",
            "final_state_source_available": True,
            "pipeline_envelope_run_id_status": "PRESENT",
            "run_id_match_status": "EXACT_MATCH",
            "resolution_source": "latest_pipeline_envelope",
        },
    )
    false_surface = operator_console._derive_binding_envelope_health_surface(
        operator_bound_run_context={"operator_binding_status": "BOUND", "invocation_run_id_status": "PRESENT"},
        pipeline_envelope_linkage={
            "envelope_binding_status": "UNBOUND",
            "final_state_source_available": False,
            "pipeline_envelope_run_id_status": "MISSING",
            "run_id_match_status": "INVOCATION_PRESENT_ENVELOPE_MISSING_OR_MISMATCH",
            "resolution_source": "none",
        },
    )
    assert true_surface["final_state_bindable"] is True
    assert false_surface["final_state_bindable"] is False


def test_nc_invocation_run_id_unpropagated_is_emitted_when_supported() -> None:
    subcodes = operator_console._derive_refined_binding_nc_subcodes(
        operator_bound_run_context={"operator_binding_status": "BOUND", "invocation_run_id_status": "PRESENT"},
        pipeline_envelope_linkage={
            "envelope_binding_status": "UNBOUND",
            "final_state_source_available": False,
            "run_id_match_status": "INVOCATION_PRESENT_ENVELOPE_MISSING_OR_MISMATCH",
        },
    )
    assert "NC_INVOCATION_RUN_ID_UNPROPAGATED" in subcodes


def test_run_id_propagation_export_artifact_schema(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(base_dir=tmp_path, selected_run_id="run.generalized_coverage.scopepass.v1")
    out_root = tmp_path / "artifacts_seal" / "abraxas_binding"
    path, status = write_run_id_propagation_artifact(payload=view.binding_restoration["run_id_propagation_export_preview"], root=out_root)
    assert status == "written"
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    assert payload["rune_id"] == "RUNE.BINDING"
    assert "invocation_run_id_state" in payload
    assert "pipeline_envelope_run_id_state" in payload
    assert "run_id_match_status" in payload
    assert "final_state_bindable" in payload


def test_run_id_propagation_export_status_does_not_mutate_unrelated_state(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    base_view = build_view_state(base_dir=tmp_path, selected_run_id="run.generalized_coverage.scopepass.v1")
    state_view = build_view_state(
        base_dir=tmp_path,
        selected_run_id="run.generalized_coverage.scopepass.v1",
        latest_run_id_propagation_export_status="written",
        latest_run_id_propagation_export_path="artifacts_seal/abraxas_binding/20260329T000000Z.run_id_propagation.json",
    )
    assert state_view.selected_run_detail == base_view.selected_run_detail
    assert state_view.runtime_corridor == base_view.runtime_corridor


def test_pipeline_envelope_persists_canonical_run_id_from_invocation_payload() -> None:
    result = operator_console._adapter_run_abraxas_pipeline(
        {
            "selected_run_id": "run.selected.v1",
            "invocation_run_id": "run.invocation.v1",
        }
    )
    envelope = dict(result.get("pipeline_envelope", {}))
    assert envelope.get("run_id") == "run.invocation.v1"
    assert envelope.get("run_id_propagation_status") == "PRESENT"


def test_pipeline_export_preview_preserves_same_envelope_run_id(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(
        base_dir=tmp_path,
        selected_run_id="run.generalized_coverage.scopepass.v1",
        pipeline_envelope_override={"run_id": "run.generalized_coverage.scopepass.v1", "overall_status": "SUCCESS", "final_classification": "SUCCESS"},
    )
    preview = view.abraxas_pipeline["pipeline_export_preview"]
    envelope = preview["pipeline_execution_envelope"]
    assert envelope["run_id"] == "run.generalized_coverage.scopepass.v1"


def test_operator_exact_match_binding_succeeds_when_envelope_run_id_matches() -> None:
    linkage = operator_console._derive_pipeline_envelope_linkage(
        latest_pipeline_envelope={"run_id": "run.exact.v1", "overall_status": "SUCCESS", "final_classification": "SUCCESS"},
        latest_pipeline_steps=[],
        pipeline_binding_snapshot={},
        operator_bound_run_context={"operator_binding_status": "BOUND", "invocation_run_id": "run.exact.v1"},
    )
    health = operator_console._derive_binding_envelope_health_surface(
        operator_bound_run_context={"operator_binding_status": "BOUND", "invocation_run_id_status": "PRESENT"},
        pipeline_envelope_linkage=linkage,
    )
    assert linkage["run_id_match_status"] == "EXACT_MATCH"
    assert health["final_state_bindable"] is True


def test_nc_pipeline_envelope_run_id_missing_when_envelope_exists_without_run_id() -> None:
    linkage = {
        "envelope_binding_status": "BOUND",
        "pipeline_envelope_run_id_status": "MISSING",
        "run_id_match_status": "INVOCATION_PRESENT_ENVELOPE_MISSING_OR_MISMATCH",
        "final_state_source_available": True,
    }
    subcodes = operator_console._derive_refined_binding_nc_subcodes(
        operator_bound_run_context={"operator_binding_status": "BOUND", "invocation_run_id_status": "PRESENT"},
        pipeline_envelope_linkage=linkage,
    )
    assert "NC_PIPELINE_ENVELOPE_RUN_ID_MISSING" in subcodes


def test_pipeline_envelope_run_id_repair_artifact_schema(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(base_dir=tmp_path, selected_run_id="run.generalized_coverage.scopepass.v1")
    out_root = tmp_path / "artifacts_seal" / "abraxas_binding"
    path, status = write_pipeline_envelope_run_id_repair_artifact(
        payload=view.binding_restoration["pipeline_envelope_run_id_repair_export_preview"],
        root=out_root,
    )
    assert status == "written"
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    assert payload["schema_version"] == "aal.runes.execution_artifact.v1"
    assert payload["rune_id"] == "RUNE.BINDING"
    assert payload["phase"] == "VALIDATE"
    assert payload["status"] in {"SUCCESS", "NOT_COMPUTABLE"}
    assert payload["inputs"]["payload"]["invocation_run_id_state"] in {"PRESENT", "MISSING", "NOT_COMPUTABLE"}
    assert payload["inputs"]["payload"]["emitted_envelope_run_id_state"] in {"PRESENT", "MISSING", "NOT_COMPUTABLE"}
    assert payload["outputs"]["payload"]["run_id_match_status"] in {
        "EXACT_MATCH",
        "FALLBACK_MATCH",
        "INVOCATION_MISSING",
        "INVOCATION_PRESENT_ENVELOPE_MISSING_OR_MISMATCH",
    }
    assert isinstance(payload["outputs"]["payload"]["final_state_bindable"], bool)


def test_pipeline_envelope_run_id_repair_export_status_does_not_mutate_unrelated_state(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    base_view = build_view_state(base_dir=tmp_path, selected_run_id="run.generalized_coverage.scopepass.v1")
    state_view = build_view_state(
        base_dir=tmp_path,
        selected_run_id="run.generalized_coverage.scopepass.v1",
        latest_pipeline_envelope_run_id_repair_export_status="written",
        latest_pipeline_envelope_run_id_repair_export_path="artifacts_seal/abraxas_binding/20260329T000000Z.pipeline_envelope_run_id_repair.json",
    )
    assert state_view.selected_run_detail == base_view.selected_run_detail
    assert state_view.pipeline_routing == base_view.pipeline_routing


def test_context_restoration_required_context_matrix_is_explicit(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(base_dir=tmp_path, selected_run_id="run.generalized_coverage.scopepass.v1", workbench_mode="runtime")
    matrix = view.context_restoration["required_context_matrix"]
    assert set(matrix.keys()) == {"detector_layer", "fusion_layer", "synthesis_layer"}
    assert isinstance(matrix["detector_layer"]["ready"], bool)
    assert isinstance(matrix["detector_layer"]["missing_fields"], list)
    assert isinstance(matrix["detector_layer"]["available_fields"], list)


def test_context_restoration_projection_is_bounded_and_truthful(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(base_dir=tmp_path, selected_run_id="run.generalized_coverage.scopepass.v1", workbench_mode="runtime")
    projected = view.context_restoration["projected_context"]
    assert "normalized_pipeline_summary" in projected
    assert "normalized_step_rollup_summary" in projected
    assert "compact_artifact_summary" in projected
    assert "bounded_runtime_result_summary" in projected
    assert "bounded_comparison_summary" in projected


def test_context_readiness_surface_true_false_branches(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    ready_view = build_view_state(base_dir=tmp_path, selected_run_id="run.generalized_coverage.scopepass.v1", workbench_mode="runtime")
    missing_view = build_view_state(base_dir=tmp_path, selected_run_id=None, workbench_mode="runtime")
    ready_surface = ready_view.context_restoration["context_readiness_surface"]
    missing_surface = missing_view.context_restoration["context_readiness_surface"]
    assert isinstance(ready_surface["detector_context_ready"], bool)
    assert isinstance(missing_surface["detector_context_ready"], bool)
    assert isinstance(missing_surface["reasons_when_false"], dict)


def test_refined_not_computable_subcodes_are_specific_when_known(tmp_path: Path) -> None:
    view = build_view_state(base_dir=tmp_path, selected_run_id=None, workbench_mode="runtime")
    refined = view.context_restoration["refined_not_computable_subcodes"]
    assert "NC_MISSING_DETECTOR_CONTEXT" in refined
    assert any(code.startswith("NC_MISSING_") for code in refined)


def test_context_restoration_export_artifact_is_written_with_bounded_schema(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(base_dir=tmp_path, selected_run_id="run.generalized_coverage.scopepass.v1", workbench_mode="runtime")
    out_root = tmp_path / "artifacts_seal" / "abraxas_context"
    path, status = write_context_restoration_artifact(payload=view.context_restoration["context_export_preview"], root=out_root)
    assert status == "written"
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    assert payload["source"] == "operator_console"
    assert payload["rune_id"] == "RUNE.CONTEXT_RESTORE"
    assert "required_context_matrix" in payload
    assert "projected_context" in payload
    assert "context_readiness_surface" in payload
    assert "refined_not_computable_subcodes" in payload


def test_context_restoration_layer_does_not_mutate_unrelated_operator_state(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    base_view = build_view_state(base_dir=tmp_path, selected_run_id="run.generalized_coverage.scopepass.v1")
    context_view = build_view_state(
        base_dir=tmp_path,
        selected_run_id="run.generalized_coverage.scopepass.v1",
        latest_context_export_status="written",
        latest_context_export_path="artifacts_seal/abraxas_context/20260329T000000Z.context_restoration.json",
    )
    assert context_view.selected_run_detail == base_view.selected_run_detail
    assert context_view.runtime_corridor == base_view.runtime_corridor


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
        "run_abraxas_pipeline",
        "run_abraxas_pipeline_review_path",
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
        "run_abraxas_pipeline",
        "run_abraxas_pipeline_review_path",
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
        "preset.abraxas.pipeline.canonical",
        "preset.abraxas.pipeline.review_path",
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
        "run_abraxas_pipeline",
        "run_abraxas_pipeline_review_path",
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


def test_runtime_corridor_registry_and_gating_are_deterministic(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(base_dir=tmp_path, workbench_mode="runtime")
    assert view.workbench_mode == "runtime"
    registry = view.runtime_corridor["runtime_entry_registry"]
    assert len(registry) >= 3
    assert registry[0]["entry_id"] == "entry.runtime.pipeline.abraxas_canonical"
    assert any(row["entry_id"] == "entry.runtime.pipeline.abraxas_review_path" for row in registry)
    gating = view.runtime_corridor["runtime_gating"]
    blocked = [row for row in gating if row["invokable"] == "false"]
    assert len(blocked) >= 1
    assert all(row["gating_reason"] in {"required_context_missing", "ers_context_blocks_entry", "adapter_not_supported"} for row in blocked)
    invokable = [row for row in gating if row["invokable"] == "true"]
    assert any(row["entry_id"] == "entry.runtime.ingest.compliance_probe" for row in invokable)


def test_abraxas_pipeline_surface_is_deterministic(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(base_dir=tmp_path, workbench_mode="runtime")
    pipeline = view.abraxas_pipeline
    assert pipeline["pipeline_registry_entry"]["entry_id"] == "entry.runtime.pipeline.abraxas_canonical"
    assert len(pipeline["pipeline_registry_entries"]) >= 2
    assert len(pipeline["comparative_pipeline_readiness"]) >= 2
    envelope = pipeline["latest_pipeline_envelope"]
    assert envelope["pipeline_id"] == "PIPELINE.ABRAXAS.CANONICAL.V3_4"
    assert envelope["overall_status"] == "NOT_COMPUTABLE"
    assert envelope["final_classification"] == "NOT_COMPUTABLE"
    assert envelope["overall_status_rule"] == "rollup.pipeline_not_invoked"
    assert "final_summary_block" in envelope
    steps = pipeline["pipeline_step_records"]
    assert len(steps) == 5
    assert [row["step_name"] for row in steps] == ["ingest", "parse", "map", "diff_validate", "review_audit"]


def test_abraxas_pipeline_override_shapes_envelope_and_state(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    steps = [
        {"step_index": 1, "step_name": "ingest", "rune_id": "RUNE.INGEST", "input_summary": {}, "output_summary": "ok", "artifact_ref": "a", "status": "SUCCESS", "reason": "", "provenance": "t"},
        {"step_index": 2, "step_name": "parse", "rune_id": "RUNE.PARSE", "input_summary": {}, "output_summary": "nc", "artifact_ref": "", "status": "NOT_COMPUTABLE", "reason": "missing", "provenance": "t"},
        {"step_index": 3, "step_name": "map", "rune_id": "RUNE.MAP", "input_summary": {}, "output_summary": "nc", "artifact_ref": "", "status": "NOT_COMPUTABLE", "reason": "missing", "provenance": "t"},
        {"step_index": 4, "step_name": "diff_validate", "rune_id": "RUNE.DIFF", "input_summary": {}, "output_summary": "ok", "artifact_ref": "b", "status": "SUCCESS", "reason": "", "provenance": "t"},
        {"step_index": 5, "step_name": "review_audit", "rune_id": "RUNE.AUDIT", "input_summary": {}, "output_summary": "ok", "artifact_ref": "c", "status": "SUCCESS", "reason": "", "provenance": "t"},
    ]
    view = build_view_state(
        base_dir=tmp_path,
        workbench_mode="runtime",
        pipeline_envelope_override={
            "pipeline_id": "PIPELINE.ABRAXAS.CANONICAL.V3_4",
            "run_id": "run.pipeline.v1",
            "overall_status": "SUCCESS",
            "final_classification": "SUCCESS",
            "overall_status_rule": "classification.required_steps_satisfied",
            "overall_status_reason": "required_steps_success_and_linkage_present",
            "final_summary_block": {
                "final_classification": "SUCCESS",
                "overall_status_rule": "classification.required_steps_satisfied",
                "overall_status_reason": "required_steps_success_and_linkage_present",
                "blocking_steps": [],
                "successful_steps": ["ingest", "diff_validate", "review_audit"],
                "artifact_summary": {"artifact_count": 3},
            },
            "final_result_summary": "SUCCESS|steps=5|artifacts=3",
            "artifact_paths": ["a", "b", "c"],
        },
        pipeline_step_records_override=steps,
    )
    pipeline = view.abraxas_pipeline
    assert pipeline["latest_pipeline_envelope"]["overall_status"] == "SUCCESS"
    assert pipeline["latest_pipeline_envelope"]["final_classification"] == "SUCCESS"
    assert pipeline["pipeline_state_surface"]["pipeline_status"] == "SUCCESS"
    assert pipeline["pipeline_state_surface"]["pipeline_failure_point"] == ""


def test_pipeline_artifact_writer_creates_bounded_schema(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(base_dir=tmp_path, workbench_mode="runtime")
    out_root = tmp_path / "artifacts_seal" / "abraxas_pipeline"
    path, status = write_pipeline_artifact(payload=view.abraxas_pipeline["pipeline_export_preview"], root=out_root)
    assert status == "written"
    assert path is not None
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    assert payload["pipeline_id"] == "PIPELINE.ABRAXAS.CANONICAL.V3_4"
    assert "pipeline_execution_envelope" in payload
    assert "pipeline_step_records" in payload
    assert "final_classification" in payload
    assert "overall_status_rule" in payload
    assert "final_summary_block" in payload


def test_pipeline_final_state_surface_is_derived_and_bounded(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(base_dir=tmp_path, workbench_mode="runtime")
    surface = view.pipeline_final_state
    assert surface["pipeline_final_status"] in {"SUCCESS", "PARTIAL", "FAILED", "NOT_COMPUTABLE"}
    assert surface["pipeline_completion_state"] in {"COMPLETE", "INCOMPLETE", "UNKNOWN"}
    assert isinstance(surface["pipeline_success_flags"], list)
    assert isinstance(surface["pipeline_failure_flags"], list)
    assert surface["resolution_source"] in {"pipeline", "pipeline_classification", "fallback", "none"}


def test_pipeline_final_state_uses_envelope_final_classification_when_status_missing() -> None:
    surface = operator_console._derive_pipeline_final_state(
        latest_pipeline_envelope={
            "overall_status": "NOT_COMPUTABLE",
            "final_classification": "SUCCESS",
        },
        pipeline_step_records=[],
        pipeline_review_workspace_payload={},
    )
    assert surface["pipeline_final_status"] == "SUCCESS"
    assert surface["pipeline_status_resolved"] is True
    assert surface["resolution_source"] == "pipeline_classification"


def test_synthesis_uses_pipeline_final_state_when_resolved() -> None:
    output = operator_console._derive_abraxas_synthesis_output(
        selected_run_id="run.v1",
        synthesis_input_surface={
            "pipeline_status": "NOT_COMPUTABLE",
            "fusion_label": "BROKEN_SIGNAL",
            "fusion_status": "SUCCESS",
            "governance_policy_mode": "bounded_runtime",
            "runtime_outcome_status": "NOT_COMPUTABLE",
            "runtime_blocker_summary": [],
            "pipeline_final_state": {
                "pipeline_final_status": "SUCCESS",
                "pipeline_status_resolved": True,
            },
            "pipeline_unresolved_subcode": "NC_PIPELINE_STATUS_UNRESOLVED",
        },
    )
    assert output["synthesis_label"] == "READY"
    assert "pipeline_final_status_success" in output["synthesis_reasons"]


def test_synthesis_uses_nc_pipeline_status_unresolved_when_missing() -> None:
    output = operator_console._derive_abraxas_synthesis_output(
        selected_run_id="run.v1",
        synthesis_input_surface={
            "pipeline_status": "NOT_COMPUTABLE",
            "fusion_label": "ACTIVE_FRICTION",
            "fusion_status": "NOT_COMPUTABLE",
            "governance_policy_mode": "bounded_runtime",
            "runtime_outcome_status": "NOT_COMPUTABLE",
            "runtime_blocker_summary": [],
            "pipeline_final_state": {
                "pipeline_final_status": "NOT_COMPUTABLE",
                "pipeline_status_resolved": False,
            },
            "pipeline_unresolved_subcode": "NC_PIPELINE_STATUS_UNRESOLVED",
        },
    )
    assert output["synthesis_label"] == "NOT_COMPUTABLE"
    assert "NC_PIPELINE_STATUS_UNRESOLVED" in output["synthesis_blockers"]


def test_pipeline_final_state_health_surface_uses_nc_blocker_when_unresolved() -> None:
    health = operator_console._derive_pipeline_final_state_health_surface(
        pipeline_final_state={
            "pipeline_status_resolved": False,
            "pipeline_final_status": "NOT_COMPUTABLE",
            "resolution_source": "none",
        },
        ledger_bridge={"ledger_bridge_status": "READY"},
    )
    assert health["blocking_reason"] == "NC_PIPELINE_STATUS_UNRESOLVED"


def test_pipeline_final_state_export_artifact_schema(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(base_dir=tmp_path, workbench_mode="runtime")
    out_root = tmp_path / "artifacts_seal" / "abraxas_pipeline"
    path, status = write_pipeline_final_state_artifact(payload=view.pipeline_final_state["final_state_export_preview"], root=out_root)
    assert status == "written"
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    assert "pipeline_final_state" in payload
    assert "final_state_health_surface" in payload
    assert "synthesis_ready" in payload
    assert "resolution_source" in payload


def test_pipeline_final_state_export_status_does_not_mutate_unrelated_state(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    base_view = build_view_state(base_dir=tmp_path, selected_run_id="run.generalized_coverage.scopepass.v1")
    state_view = build_view_state(
        base_dir=tmp_path,
        selected_run_id="run.generalized_coverage.scopepass.v1",
        latest_pipeline_final_state_export_status="written",
        latest_pipeline_final_state_export_path="artifacts_seal/abraxas_pipeline/20260329T000000Z.pipeline_final_state.json",
    )
    assert state_view.selected_run_detail == base_view.selected_run_detail
    assert state_view.binding_restoration == base_view.binding_restoration


def test_pipeline_runtime_adapter_allowed_vs_blocked(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    allowed = execute_runtime_adapter(
        action_name="run_abraxas_pipeline",
        payload={"selected_run_id": "run.generalized_coverage.scopepass.v1"},
        allowed_actions=["run_abraxas_pipeline"],
    )
    assert allowed["outcome_status"] in {"SUCCESS", "PARTIAL", "FAILED", "NOT_COMPUTABLE"}
    assert "pipeline_envelope" in allowed
    blocked = execute_runtime_adapter(
        action_name="run_abraxas_pipeline",
        payload={"selected_run_id": "run.generalized_coverage.scopepass.v1"},
        allowed_actions=[],
    )
    assert blocked["outcome_status"] == "FAILED"
    assert blocked["error_info"] == "action_not_allowed"
    parse_step = next((row for row in allowed.get("pipeline_step_records", []) if row.get("step_name") == "parse"), {})
    map_step = next((row for row in allowed.get("pipeline_step_records", []) if row.get("step_name") == "map"), {})
    diff_step = next((row for row in allowed.get("pipeline_step_records", []) if row.get("step_name") == "diff_validate"), {})
    assert parse_step.get("status") in {"SUCCESS", "NOT_COMPUTABLE"}
    assert map_step.get("status") in {"SUCCESS", "NOT_COMPUTABLE"}
    if map_step.get("status") == "SUCCESS":
        assert "mapped_entities=" in str(map_step.get("output_summary", ""))
    assert "map_relations=" in str(diff_step.get("output_summary", ""))
    assert "map_context" in dict(diff_step.get("input_summary", {}))
    envelope = dict(allowed.get("pipeline_envelope", {}))
    assert envelope.get("overall_status") in {"SUCCESS", "PARTIAL", "FAILED", "NOT_COMPUTABLE"}
    assert envelope.get("final_classification") in {"SUCCESS", "PARTIAL", "FAILED", "NOT_COMPUTABLE"}
    assert str(envelope.get("overall_status_rule", "")).startswith("classification.")
    assert "final_summary_block" in envelope


def test_second_pipeline_runtime_adapter_runs_with_bounded_envelope(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    allowed = execute_runtime_adapter(
        action_name="run_abraxas_pipeline_review_path",
        payload={"selected_run_id": "run.generalized_coverage.scopepass.v1"},
        allowed_actions=["run_abraxas_pipeline_review_path"],
    )
    assert allowed["pipeline_id"] == "PIPELINE.ABRAXAS.CANONICAL.V4_0.REVIEW_PATH"
    envelope = dict(allowed.get("pipeline_envelope", {}))
    assert envelope.get("pipeline_id") == "PIPELINE.ABRAXAS.CANONICAL.V4_0.REVIEW_PATH"
    assert envelope.get("overall_status") in {"SUCCESS", "PARTIAL", "FAILED", "NOT_COMPUTABLE"}
    assert envelope.get("final_classification") in {"SUCCESS", "PARTIAL", "FAILED", "NOT_COMPUTABLE"}
    steps = list(allowed.get("pipeline_step_records", []))
    assert [row.get("step_name") for row in steps] == ["ingest", "parse", "map", "review_audit"]


def test_pipeline_hardening_surfaces_are_deterministic(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(
        base_dir=tmp_path,
        workbench_mode="runtime",
        pipeline_envelope_override={
            "pipeline_id": "PIPELINE.ABRAXAS.CANONICAL.V3_4",
            "run_id": "run.generalized_coverage.scopepass.v1",
            "overall_status": "SUCCESS",
            "final_classification": "SUCCESS",
            "overall_status_rule": "classification.required_steps_satisfied",
            "overall_status_reason": "required_steps_success_and_linkage_present",
            "final_summary_block": {
                "final_classification": "SUCCESS",
                "overall_status_rule": "classification.required_steps_satisfied",
                "overall_status_reason": "required_steps_success_and_linkage_present",
                "blocking_steps": [],
                "successful_steps": ["ingest", "diff_validate", "review_audit"],
                "artifact_summary": {"artifact_count": 3},
            },
            "final_result_summary": "SUCCESS|steps=5|artifacts=3",
        },
        pipeline_step_records_override=[
            {"step_index": 1, "step_name": "ingest", "rune_id": "RUNE.INGEST", "input_summary": {}, "output_summary": "ok", "artifact_ref": "a", "status": "SUCCESS", "reason": "", "provenance": "t"},
            {"step_index": 2, "step_name": "parse", "rune_id": "RUNE.PARSE", "input_summary": {}, "output_summary": "parsed", "artifact_ref": "a", "status": "SUCCESS", "reason": "", "provenance": "t"},
            {"step_index": 3, "step_name": "map", "rune_id": "RUNE.MAP", "input_summary": {}, "output_summary": "mapped_entities=['status']", "artifact_ref": "a", "status": "SUCCESS", "reason": "", "provenance": "t"},
            {"step_index": 4, "step_name": "diff_validate", "rune_id": "RUNE.DIFF", "input_summary": {}, "output_summary": "ok", "artifact_ref": "b", "status": "SUCCESS", "reason": "", "provenance": "t"},
            {"step_index": 5, "step_name": "review_audit", "rune_id": "RUNE.AUDIT", "input_summary": {}, "output_summary": "ok", "artifact_ref": "c", "status": "SUCCESS", "reason": "", "provenance": "t"},
        ],
    )
    hardening = view.pipeline_hardening
    assert len(hardening["pipeline_step_audit"]) == 5
    parse_audit = next((row for row in hardening["pipeline_step_audit"] if row["step_name"] == "parse"), {})
    map_audit = next((row for row in hardening["pipeline_step_audit"] if row["step_name"] == "map"), {})
    assert parse_audit["callable_exposed"] == "true"
    assert map_audit["callable_exposed"] == "true"
    matrix = {row["step_name"]: row["quality_label"] for row in hardening["pipeline_quality_matrix"]}
    assert matrix["parse"] == "EXECUTABLE"
    assert matrix["map"] == "EXECUTABLE"
    assert hardening["primary_upgrade_target"] in {"diff_validate", "review_audit", "ingest", "none"}
    assert "upgrade_reason" in hardening
    workspace = hardening["pipeline_hardening_workspace_payload"]
    assert workspace["final_classification"] == "SUCCESS"
    assert "overall_status_reasoning" in workspace
    assert "blocking_steps" in workspace
    assert "successful_steps" in workspace


def test_pipeline_review_export_artifact_is_written(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(base_dir=tmp_path, workbench_mode="runtime")
    out_root = tmp_path / "artifacts_seal" / "abraxas_pipeline"
    path, status = write_pipeline_review_artifact(
        payload=view.pipeline_hardening["pipeline_review_export_preview"],
        root=out_root,
    )
    assert status == "written"
    assert path is not None
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    assert payload["pipeline_id"] == "PIPELINE.ABRAXAS.CANONICAL.V3_4"
    assert "step_exposure_audit" in payload
    assert "quality_matrix" in payload
    assert "upgrade_target_selection" in payload
    assert "final_summary_block" in payload
    assert "map_realization_state" in payload
    assert "diff_input_quality_state" in payload


def test_pipeline_routing_surface_and_override_are_deterministic(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(base_dir=tmp_path, workbench_mode="runtime")
    routing = view.pipeline_routing
    assert len(routing["pipeline_suitability_matrix"]) >= 2
    assert routing["recommended_pipeline_id"] in {
        "PIPELINE.ABRAXAS.CANONICAL.V3_4",
        "PIPELINE.ABRAXAS.CANONICAL.V4_0.REVIEW_PATH",
    }
    assert routing["effective_pipeline_id"] == routing["recommended_pipeline_id"]
    assert routing["pipeline_routing_workspace_payload"]["effective_pipeline_id"] == routing["effective_pipeline_id"]
    with_override = build_view_state(
        base_dir=tmp_path,
        workbench_mode="runtime",
        manual_pipeline_override="PIPELINE.ABRAXAS.CANONICAL.V3_4",
    )
    routing_override = with_override.pipeline_routing
    assert routing_override["manual_pipeline_override"] == "PIPELINE.ABRAXAS.CANONICAL.V3_4"
    assert routing_override["effective_pipeline_id"] == "PIPELINE.ABRAXAS.CANONICAL.V3_4"
    assert routing_override["recommended_pipeline_id"] in {
        "PIPELINE.ABRAXAS.CANONICAL.V3_4",
        "PIPELINE.ABRAXAS.CANONICAL.V4_0.REVIEW_PATH",
    }
    cleared_override = build_view_state(
        base_dir=tmp_path,
        workbench_mode="runtime",
        manual_pipeline_override="",
    )
    assert cleared_override.pipeline_routing["manual_pipeline_override"] == ""
    assert cleared_override.pipeline_routing["effective_pipeline_id"] == cleared_override.pipeline_routing["recommended_pipeline_id"]


def test_pipeline_routing_export_artifact_is_written(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(base_dir=tmp_path, workbench_mode="runtime")
    out_root = tmp_path / "artifacts_seal" / "abraxas_pipeline"
    path, status = write_pipeline_routing_artifact(
        payload=view.pipeline_routing["routing_export_preview"],
        root=out_root,
    )
    assert status == "written"
    assert path is not None
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    assert "pipeline_suitability_matrix" in payload
    assert "recommended_pipeline_id" in payload
    assert "routing_rule_id" in payload
    assert "manual_pipeline_override" in payload
    assert "rule_strings" in payload


def test_runtime_corridor_invocation_envelope_and_state_surface(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    last_action = {
        "action_name": "run_compliance_probe",
        "entry_id": "entry.runtime.ingest.compliance_probe",
        "rune_id": "RUNE.INGEST",
        "adapter_name": "adapter.run_compliance_probe",
        "attempted_at": "2026-03-29T00:00:00Z",
        "triggered_run_id": "run.compliance_probe.v1",
        "artifact_path": "artifacts_seal/runs/compliance_probe/run.compliance_probe.v1.artifact.json",
        "outcome_status": "SUCCESS",
    }
    view = build_view_state(base_dir=tmp_path, last_action=last_action, workbench_mode="runtime")
    envelope = view.runtime_corridor["runtime_invocation_envelope"]
    assert envelope["entry_id"] == "entry.runtime.ingest.compliance_probe"
    assert envelope["rune_id"] == "RUNE.INGEST"
    assert envelope["outcome_status"] == "SUCCESS"
    state = view.runtime_corridor["runtime_state_surface"]
    assert state["latest_runtime_status"] == "SUCCESS"
    assert "runtime_state_summary" in state


def test_runtime_corridor_export_artifact_is_written(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(base_dir=tmp_path, workbench_mode="runtime")
    out_root = tmp_path / "artifacts_seal" / "abraxas_runtime"
    path, status = write_runtime_corridor_artifact(
        payload=view.runtime_corridor["runtime_export_preview"],
        root=out_root,
    )
    assert status == "written"
    assert path is not None
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    assert "runtime_entry_registry" in payload
    assert "runtime_state_surface" in payload
    assert "runtime_gating_summary" in payload
    assert payload["source"] == "operator_console"


def test_runtime_workspace_uses_invocation_override(tmp_path: Path) -> None:
    _seed_scopepass(tmp_path)
    view = build_view_state(
        base_dir=tmp_path,
        workbench_mode="runtime",
        runtime_invocation_override={
            "entry_id": "entry.runtime.parse_diff.validator",
            "action_name": "run_execution_validator",
            "rune_id": "RUNE.VALIDATOR",
            "outcome_status": "BLOCKED",
            "gating_snapshot": {"gating_reason": "ers_context_blocks_entry"},
        },
    )
    envelope = view.runtime_corridor["runtime_invocation_envelope"]
    assert envelope["entry_id"] == "entry.runtime.parse_diff.validator"
    assert envelope["outcome_status"] == "BLOCKED"
    assert view.runtime_corridor["runtime_workspace_payload"]["mode"] == "runtime"
