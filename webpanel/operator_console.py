from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Set

from abx.execution_validator import emit_validation_result, validate_run
from webpanel.ui_signal_sections import normalize_signal_sections

@dataclass(frozen=True)
class ViewState:
    mode: str
    selected_run_id: Optional[str]
    available_runs: List[str]
    visible_run_ids: List[str]
    closure_status: str
    focus_filters: Dict[str, str]
    run_health_summaries: List[Dict[str, Any]]
    visible_run_health_summaries: List[Dict[str, Any]]
    selected_run_artifact_summary: Dict[str, Any]
    selected_run_validator_summary: Dict[str, Any]
    selected_run_detail: Dict[str, Any]
    last_action: Optional[Dict[str, Any]]
    recent_activity_limit: int
    recent_activity: List[Dict[str, Any]]
    suggested_run_id: Optional[str]
    suggestion_reason: str
    weakness_reasons: List[str]
    suggested_next_step: str
    evidence_drilldown: Dict[str, Any]
    snapshot_header: Dict[str, Any]
    comparison_run_id: Optional[str]
    compare_strip: Dict[str, Any]
    compare_delta_summary: Dict[str, Any]
    suggested_compare_run_id: Optional[str]
    suggested_compare_reason: str
    evidence_delta_preview: Dict[str, Any]
    pinned_run_ids: List[str]
    pin_panel: Dict[str, Any]
    highlights_limit: int
    highlights: List[Dict[str, str]]
    action_history_limit: int
    action_history: List[Dict[str, str]]
    workbench_header: Dict[str, Any]
    attention_queue: List[Dict[str, str]]
    triage_limit_per_bucket: int
    triage_panel: Dict[str, List[Dict[str, str]]]
    pinned_run_deep_cards: List[Dict[str, str]]
    baseline_run_id: Optional[str]
    baseline_reason: str
    action_safety_envelope: Dict[str, Any]
    latest_snapshot_report_path: Optional[str]
    latest_snapshot_report_status: str
    export_preview: Dict[str, Any]
    snapshot_report_payload: Dict[str, Any]
    snapshot_recall_limit: int
    snapshot_recall_items: List[Dict[str, str]]
    loaded_snapshot_path: Optional[str]
    loaded_snapshot_status: str
    workbench_mode: str
    workbench_modes_allowed: List[str]
    attention_actions_enabled: bool
    attention_action_hint: str
    baseline_locked: bool
    baseline_locked_run_id: Optional[str]
    baseline_lock_reason: str
    compare_to_baseline_ready: bool
    control_plane: Dict[str, Any]
    action_presets: List[Dict[str, Any]]
    selected_preset_id: Optional[str]
    dry_run_preview: Dict[str, Any]
    result_packet: Dict[str, Any]
    retry_reapply: Dict[str, Any]
    execution_ledger_limit: int
    execution_ledger: List[Dict[str, str]]
    execution_report_preview: Dict[str, Any]
    latest_execution_report_path: Optional[str]
    latest_execution_report_status: str
    runbook_card: Dict[str, Any]
    handoff_bundle_preview: Dict[str, Any]
    latest_handoff_bundle_path: Optional[str]
    latest_handoff_bundle_status: str
    checkpoint_preview: Dict[str, str]
    latest_checkpoint_path: Optional[str]
    latest_checkpoint_status: str
    restored_checkpoint_path: Optional[str]
    restored_checkpoint_status: str
    quick_actions: Dict[str, Any]
    runtime_adapter_audit: List[Dict[str, str]]
    runtime_safety_notes: List[Dict[str, str]]
    runflow_cards: List[Dict[str, str]]
    runtime_result_drilldown: Dict[str, Any]
    outcome_classification: Dict[str, str]
    prior_result_diff: Dict[str, Any]
    action_stability: Dict[str, Any]
    failure_triage: Dict[str, Any]
    result_provenance_panel: Dict[str, Any]
    runtime_outcome_review_workspace: Dict[str, Any]
    decision_layer: Dict[str, Any]
    decision_workspace_payload: Dict[str, Any]
    session_continuity: Dict[str, Any]
    governance: Dict[str, Any]
    viz_integration: Dict[str, Any]
    viz_render: Dict[str, Any]
    reporting: Dict[str, Any]
    adapter_health_checks: Dict[str, Any]
    runflow_workspace: Dict[str, Any]
    ers_integration: Dict[str, Any]
    ers_review: Dict[str, Any]
    runtime_corridor: Dict[str, Any]
    abraxas_pipeline: Dict[str, Any]
    pipeline_final_state: Dict[str, Any]
    pipeline_hardening: Dict[str, Any]
    pipeline_routing: Dict[str, Any]
    domain_logic: Dict[str, Any]
    abraxas_synthesis: Dict[str, Any]
    binding_restoration: Dict[str, Any]
    context_restoration: Dict[str, Any]
    session_context: Dict[str, str]
    data_provenance: Dict[str, Any]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _extract_linkage_fields(payload: Mapping[str, Any]) -> Dict[str, Any]:
    ledger_record_ids = [str(x) for x in payload.get("ledger_record_ids", []) if isinstance(x, str)]
    ledger_artifact_ids = [str(x) for x in payload.get("ledger_artifact_ids", []) if isinstance(x, str)]
    pointers = payload.get("correlation_pointers", [])
    correlation_pointers = [x for x in pointers if isinstance(x, Mapping)]
    if not (ledger_record_ids or ledger_artifact_ids or correlation_pointers):
        correlation_pointers = [
            {
                "type": "linkage_state",
                "value": "UNRESOLVED",
                "status": "UNRESOLVED",
                "reason": "LINKAGE_NOT_COMPUTABLE",
            }
        ]
    return {
        "ledger_record_ids": ledger_record_ids,
        "ledger_artifact_ids": ledger_artifact_ids,
        "correlation_pointers": correlation_pointers,
    }


def write_viz_render_artifact(
    *,
    preview: Mapping[str, Any],
    root: Path = Path("artifacts_seal") / "operator_viz_render",
) -> tuple[str | None, str]:
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    mode = _sanitize_viz_mode(str(preview.get("viz_mode", "weather")))
    path = root / f"{stamp}.{mode}.render.json"
    index = 1
    while path.exists():
        path = root / f"{stamp}.{mode}.{index}.render.json"
        index += 1
    artifact = {
        "generated_at": _utc_now(),
        "ruleset_version": "v2.7.1",
        "source": "operator_console",
        "viz_mode": mode,
        "render_output": dict(preview.get("render_output", {})),
        "source_viz_payload": dict(preview.get("source_viz_payload", {})),
        "selected_context": dict(preview.get("selected_context", {})),
        "status": str(preview.get("status", "ready")),
        "provenance": str(preview.get("provenance", "operator_console.viz_render.v2.7.1.mode_routed")),
        "timestamp": str(preview.get("timestamp", _utc_now())),
    }
    path.write_text(json.dumps(artifact, sort_keys=True, indent=2), encoding="utf-8")
    return path.as_posix(), "written"


def write_operator_report_artifact(
    *,
    suffix: str,
    payload: Mapping[str, Any],
    root: Path = Path("artifacts_seal") / "operator_reports",
) -> tuple[str | None, str]:
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = root / f"{stamp}.{suffix}.json"
    index = 1
    while path.exists():
        path = root / f"{stamp}.{suffix}.{index}.json"
        index += 1
    artifact = {
        "generated_at": _utc_now(),
        "ruleset_version": "v2.8.0",
        "source": "operator_console",
        **dict(payload),
    }
    path.write_text(json.dumps(artifact, sort_keys=True, indent=2), encoding="utf-8")
    return path.as_posix(), "written"


def write_operator_markdown_report(
    *,
    markdown: str,
    root: Path = Path("artifacts_seal") / "operator_reports",
) -> tuple[str | None, str]:
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = root / f"{stamp}.report.md"
    index = 1
    while path.exists():
        path = root / f"{stamp}.report.{index}.md"
        index += 1
    path.write_text(markdown, encoding="utf-8")
    return path.as_posix(), "written"


def write_operator_ers_snapshot_artifact(
    *,
    payload: Mapping[str, Any],
    root: Path = Path("artifacts_seal") / "operator_ers",
) -> tuple[str | None, str]:
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = root / f"{stamp}.ers_snapshot.json"
    index = 1
    while path.exists():
        path = root / f"{stamp}.{index}.ers_snapshot.json"
        index += 1
    linkage = _extract_linkage_fields(payload)
    artifact = {
        "generated_at": _utc_now(),
        "ruleset_version": "v3.1.0",
        "source": "operator_console",
        "run_id": str((payload.get("runtime_context", {}) or {}).get("selected_run_id", "") or "NOT_COMPUTABLE"),
        "rune_id": "RUNE.ERS",
        "artifact_id": f"operator_ers.{stamp.lower()}",
        "provenance": {"source_refs": ["webpanel.operator_console"], "notes": "ERS snapshot export"},
        "ledger_record_ids": linkage["ledger_record_ids"],
        "ledger_artifact_ids": linkage["ledger_artifact_ids"],
        "correlation_pointers": linkage["correlation_pointers"],
        **dict(payload),
    }
    path.write_text(json.dumps(artifact, sort_keys=True, indent=2), encoding="utf-8")
    return path.as_posix(), "written"


def write_operator_ers_review_artifact(
    *,
    payload: Mapping[str, Any],
    root: Path = Path("artifacts_seal") / "operator_ers",
) -> tuple[str | None, str]:
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = root / f"{stamp}.ers_review.json"
    index = 1
    while path.exists():
        path = root / f"{stamp}.{index}.ers_review.json"
        index += 1
    linkage = _extract_linkage_fields(payload)
    artifact = {
        "generated_at": _utc_now(),
        "ruleset_version": "v3.2.0",
        "source": "operator_console",
        "run_id": str((payload.get("runtime_context", {}) or {}).get("selected_run_id", "") or "NOT_COMPUTABLE"),
        "rune_id": "RUNE.ERS",
        "artifact_id": f"operator_ers_review.{stamp.lower()}",
        "provenance": {"source_refs": ["webpanel.operator_console"], "notes": "ERS review export"},
        "ledger_record_ids": linkage["ledger_record_ids"],
        "ledger_artifact_ids": linkage["ledger_artifact_ids"],
        "correlation_pointers": linkage["correlation_pointers"],
        **dict(payload),
    }
    path.write_text(json.dumps(artifact, sort_keys=True, indent=2), encoding="utf-8")
    return path.as_posix(), "written"


def write_runtime_corridor_artifact(
    *,
    payload: Mapping[str, Any],
    root: Path = Path("artifacts_seal") / "abraxas_runtime",
) -> tuple[str | None, str]:
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = root / f"{stamp}.runtime_corridor.json"
    index = 1
    while path.exists():
        path = root / f"{stamp}.{index}.runtime_corridor.json"
        index += 1
    artifact = {
        "generated_at": _utc_now(),
        "ruleset_version": "v3.3.0",
        "source": "operator_console",
        **dict(payload),
    }
    path.write_text(json.dumps(artifact, sort_keys=True, indent=2), encoding="utf-8")
    return path.as_posix(), "written"


def write_pipeline_artifact(
    *,
    payload: Mapping[str, Any],
    root: Path = Path("artifacts_seal") / "abraxas_pipeline",
) -> tuple[str | None, str]:
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    pipeline_id = str(payload.get("pipeline_id", "PIPELINE.ABRAXAS.CANONICAL.V3_4")).replace(".", "_").lower()
    path = root / f"{stamp}.{pipeline_id}.pipeline.json"
    index = 1
    while path.exists():
        path = root / f"{stamp}.{pipeline_id}.{index}.pipeline.json"
        index += 1
    artifact = {
        "generated_at": _utc_now(),
        "ruleset_version": "v3.4.0",
        "source": "operator_console",
        **dict(payload),
    }
    path.write_text(json.dumps(artifact, sort_keys=True, indent=2), encoding="utf-8")
    return path.as_posix(), "written"


def write_pipeline_review_artifact(
    *,
    payload: Mapping[str, Any],
    root: Path = Path("artifacts_seal") / "abraxas_pipeline",
) -> tuple[str | None, str]:
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = root / f"{stamp}.pipeline_review.json"
    index = 1
    while path.exists():
        path = root / f"{stamp}.{index}.pipeline_review.json"
        index += 1
    artifact = {
        "generated_at": _utc_now(),
        "ruleset_version": "v3.5.0",
        "source": "operator_console",
        **dict(payload),
    }
    path.write_text(json.dumps(artifact, sort_keys=True, indent=2), encoding="utf-8")
    return path.as_posix(), "written"


def write_pipeline_routing_artifact(
    *,
    payload: Mapping[str, Any],
    root: Path = Path("artifacts_seal") / "abraxas_pipeline",
) -> tuple[str | None, str]:
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = root / f"{stamp}.pipeline_routing.json"
    index = 1
    while path.exists():
        path = root / f"{stamp}.{index}.pipeline_routing.json"
        index += 1
    artifact = {
        "generated_at": _utc_now(),
        "ruleset_version": "v4.1.0",
        "source": "operator_console",
        **dict(payload),
    }
    path.write_text(json.dumps(artifact, sort_keys=True, indent=2), encoding="utf-8")
    return path.as_posix(), "written"


def write_pipeline_final_state_artifact(
    *,
    payload: Mapping[str, Any],
    root: Path = Path("artifacts_seal") / "abraxas_pipeline",
) -> tuple[str | None, str]:
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = root / f"{stamp}.pipeline_final_state.json"
    index = 1
    while path.exists():
        path = root / f"{stamp}.{index}.pipeline_final_state.json"
        index += 1
    artifact = {
        "generated_at": _utc_now(),
        "ruleset_version": "v4.9.0",
        "source": "operator_console",
        **dict(payload),
    }
    path.write_text(json.dumps(artifact, sort_keys=True, indent=2), encoding="utf-8")
    return path.as_posix(), "written"


def write_detector_signal_artifact(
    *,
    payload: Mapping[str, Any],
    root: Path = Path("artifacts_seal") / "abraxas_signals",
) -> tuple[str | None, str]:
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    detector_id = str(payload.get("detector_id", "ABX.STRUCTURAL_PRESSURE.V4_2")).replace(".", "_").lower()
    path = root / f"{stamp}.{detector_id}.signal.json"
    index = 1
    while path.exists():
        path = root / f"{stamp}.{detector_id}.{index}.signal.json"
        index += 1
    artifact = {
        "generated_at": _utc_now(),
        "ruleset_version": "v4.2.0",
        "source": "operator_console",
        "rune_id": "RUNE.ERS",
        "artifact_id": f"detector_signal.{stamp.lower()}",
        "ledger_record_ids": [],
        "ledger_artifact_ids": [],
        "correlation_pointers": [],
        **dict(payload),
    }
    path.write_text(json.dumps(artifact, sort_keys=True, indent=2), encoding="utf-8")
    return path.as_posix(), "written"


def write_motif_signal_artifact(
    *,
    payload: Mapping[str, Any],
    root: Path = Path("artifacts_seal") / "abraxas_signals",
) -> tuple[str | None, str]:
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    detector_id = str(payload.get("detector_id", "ABX.MOTIF_RECURRENCE.V4_3")).replace(".", "_").lower()
    path = root / f"{stamp}.{detector_id}.motif_signal.json"
    index = 1
    while path.exists():
        path = root / f"{stamp}.{detector_id}.{index}.motif_signal.json"
        index += 1
    artifact = {
        "generated_at": _utc_now(),
        "ruleset_version": "v4.3.0",
        "source": "operator_console",
        "rune_id": "RUNE.ERS",
        "artifact_id": f"motif_signal.{stamp.lower()}",
        "ledger_record_ids": [],
        "ledger_artifact_ids": [],
        "correlation_pointers": [],
        **dict(payload),
    }
    path.write_text(json.dumps(artifact, sort_keys=True, indent=2), encoding="utf-8")
    return path.as_posix(), "written"


def write_drift_signal_artifact(
    *,
    payload: Mapping[str, Any],
    root: Path = Path("artifacts_seal") / "abraxas_signals",
) -> tuple[str | None, str]:
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    detector_id = str(payload.get("detector_id", "ABX.INSTABILITY_DRIFT.V4_4")).replace(".", "_").lower()
    path = root / f"{stamp}.{detector_id}.drift_signal.json"
    index = 1
    while path.exists():
        path = root / f"{stamp}.{detector_id}.{index}.drift_signal.json"
        index += 1
    artifact = {
        "generated_at": _utc_now(),
        "ruleset_version": "v4.4.0",
        "source": "operator_console",
        "rune_id": "RUNE.DIFF",
        "artifact_id": f"drift_signal.{stamp.lower()}",
        "ledger_record_ids": [],
        "ledger_artifact_ids": [],
        "correlation_pointers": [],
        **dict(payload),
    }
    path.write_text(json.dumps(artifact, sort_keys=True, indent=2), encoding="utf-8")
    return path.as_posix(), "written"


def write_anomaly_signal_artifact(
    *,
    payload: Mapping[str, Any],
    root: Path = Path("artifacts_seal") / "abraxas_signals",
) -> tuple[str | None, str]:
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    detector_id = str(payload.get("detector_id", "ABX.ANOMALY_GAP.V4_4")).replace(".", "_").lower()
    path = root / f"{stamp}.{detector_id}.anomaly_signal.json"
    index = 1
    while path.exists():
        path = root / f"{stamp}.{detector_id}.{index}.anomaly_signal.json"
        index += 1
    artifact = {
        "generated_at": _utc_now(),
        "ruleset_version": "v4.4.0",
        "source": "operator_console",
        "rune_id": "RUNE.ERS",
        "artifact_id": f"anomaly_signal.{stamp.lower()}",
        "ledger_record_ids": [],
        "ledger_artifact_ids": [],
        "correlation_pointers": [],
        **dict(payload),
    }
    path.write_text(json.dumps(artifact, sort_keys=True, indent=2), encoding="utf-8")
    return path.as_posix(), "written"


def write_fusion_signal_artifact(
    *,
    payload: Mapping[str, Any],
    root: Path = Path("artifacts_seal") / "abraxas_signals",
) -> tuple[str | None, str]:
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = root / f"{stamp}.fusion_signal.json"
    index = 1
    while path.exists():
        path = root / f"{stamp}.{index}.fusion_signal.json"
        index += 1
    artifact = {
        "generated_at": _utc_now(),
        "ruleset_version": "v4.5.0",
        "source": "operator_console",
        "rune_id": "RUNE.DIFF",
        "artifact_id": f"fusion_signal.{stamp.lower()}",
        "ledger_record_ids": [],
        "ledger_artifact_ids": [],
        "correlation_pointers": [],
        **dict(payload),
    }
    path.write_text(json.dumps(artifact, sort_keys=True, indent=2), encoding="utf-8")
    return path.as_posix(), "written"


def write_synthesis_output_artifact(
    *,
    payload: Mapping[str, Any],
    root: Path = Path("artifacts_seal") / "abraxas_output",
) -> tuple[str | None, str]:
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = root / f"{stamp}.synthesis.json"
    index = 1
    while path.exists():
        path = root / f"{stamp}.{index}.synthesis.json"
        index += 1
    artifact = {
        "generated_at": _utc_now(),
        "ruleset_version": "v4.6.0",
        "source": "operator_console",
        "rune_id": "RUNE.AUDIT",
        "artifact_id": f"synthesis_output.{stamp.lower()}",
        "ledger_record_ids": [],
        "ledger_artifact_ids": [],
        "correlation_pointers": [],
        **dict(payload),
    }
    path.write_text(json.dumps(artifact, sort_keys=True, indent=2), encoding="utf-8")
    return path.as_posix(), "written"


def write_binding_health_artifact(
    *,
    payload: Mapping[str, Any],
    root: Path = Path("artifacts_seal") / "abraxas_binding",
) -> tuple[str | None, str]:
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = root / f"{stamp}.binding_health.json"
    index = 1
    while path.exists():
        path = root / f"{stamp}.{index}.binding_health.json"
        index += 1
    linkage = _extract_linkage_fields(payload)
    artifact = {
        "generated_at": _utc_now(),
        "ruleset_version": "v4.7.0",
        "source": "operator_console",
        "rune_id": "RUNE.AUDIT",
        "artifact_id": f"binding_health.{stamp.lower()}",
        "ledger_record_ids": linkage["ledger_record_ids"],
        "ledger_artifact_ids": linkage["ledger_artifact_ids"],
        "correlation_pointers": linkage["correlation_pointers"],
        **dict(payload),
    }
    path.write_text(json.dumps(artifact, sort_keys=True, indent=2), encoding="utf-8")
    return path.as_posix(), "written"


def write_pipeline_envelope_binding_artifact(
    *,
    payload: Mapping[str, Any],
    root: Path = Path("artifacts_seal") / "abraxas_binding",
) -> tuple[str | None, str]:
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = root / f"{stamp}.pipeline_envelope_binding.json"
    index = 1
    while path.exists():
        path = root / f"{stamp}.{index}.pipeline_envelope_binding.json"
        index += 1
    linkage = _extract_linkage_fields(payload)
    artifact = {
        "generated_at": _utc_now(),
        "ruleset_version": "v5.0.0",
        "source": "operator_console",
        "rune_id": "RUNE.BINDING",
        "artifact_id": f"pipeline_envelope_binding.{stamp.lower()}",
        "ledger_record_ids": linkage["ledger_record_ids"],
        "ledger_artifact_ids": linkage["ledger_artifact_ids"],
        "correlation_pointers": linkage["correlation_pointers"],
        **dict(payload),
    }
    path.write_text(json.dumps(artifact, sort_keys=True, indent=2), encoding="utf-8")
    return path.as_posix(), "written"


def write_run_id_propagation_artifact(
    *,
    payload: Mapping[str, Any],
    root: Path = Path("artifacts_seal") / "abraxas_binding",
) -> tuple[str | None, str]:
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = root / f"{stamp}.run_id_propagation.json"
    index = 1
    while path.exists():
        path = root / f"{stamp}.{index}.run_id_propagation.json"
        index += 1
    linkage = _extract_linkage_fields(payload)
    artifact = {
        "generated_at": _utc_now(),
        "ruleset_version": "v5.0.1",
        "source": "operator_console",
        "rune_id": "RUNE.BINDING",
        "artifact_id": f"run_id_propagation.{stamp.lower()}",
        "ledger_record_ids": linkage["ledger_record_ids"],
        "ledger_artifact_ids": linkage["ledger_artifact_ids"],
        "correlation_pointers": linkage["correlation_pointers"],
        **dict(payload),
    }
    path.write_text(json.dumps(artifact, sort_keys=True, indent=2), encoding="utf-8")
    return path.as_posix(), "written"


def write_pipeline_envelope_run_id_repair_artifact(
    *,
    payload: Mapping[str, Any],
    root: Path = Path("artifacts_seal") / "abraxas_binding",
) -> tuple[str | None, str]:
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = root / f"{stamp}.pipeline_envelope_run_id_repair.json"
    index = 1
    while path.exists():
        path = root / f"{stamp}.{index}.pipeline_envelope_run_id_repair.json"
        index += 1
    run_id = str(payload.get("run_id", "NOT_COMPUTABLE")) or "NOT_COMPUTABLE"
    match_status = str(payload.get("run_id_match_status", "INVOCATION_MISSING"))
    final_state_bindable = bool(payload.get("final_state_bindable", False))
    status = "SUCCESS" if final_state_bindable and match_status in {"EXACT_MATCH", "FALLBACK_MATCH"} else "NOT_COMPUTABLE"
    invocation_state_raw = payload.get("invocation_run_id_state", "MISSING")
    envelope_state_raw = payload.get("emitted_envelope_run_id_state", "MISSING")
    if isinstance(invocation_state_raw, Mapping):
        invocation_state = str(invocation_state_raw.get("invocation_run_id_status", "MISSING"))
    else:
        invocation_state = str(invocation_state_raw)
    if isinstance(envelope_state_raw, Mapping):
        envelope_state = str(envelope_state_raw.get("pipeline_envelope_run_id_status", "MISSING"))
    else:
        envelope_state = str(envelope_state_raw)
    artifact = {
        "schema_version": "aal.runes.execution_artifact.v1",
        "run_id": run_id,
        "artifact_id": f"pipeline_envelope_run_id_repair.{stamp.lower()}",
        "rune_id": "RUNE.BINDING",
        "timestamp": _utc_now(),
        "phase": "VALIDATE",
        "status": status,
        "inputs": {
            "payload": {
                "invocation_run_id_state": invocation_state,
                "emitted_envelope_run_id_state": envelope_state,
                "run_id_match_status": match_status,
            },
            "meta": {"source": "operator_console"},
        },
        "outputs": {
            "payload": dict(payload),
            "summary": "pipeline_envelope_run_id_repair",
            "metrics": {"final_state_bindable": final_state_bindable},
            "errors": [] if status == "SUCCESS" else ["NC_PIPELINE_ENVELOPE_RUN_ID_MISSING_OR_MISMATCH"],
        },
        "provenance": {
            "source_refs": ["operator_console.binding_restoration.pipeline_envelope_run_id_repair.export.v5.0.2"],
            "notes": "Canonical invocation run_id propagation and envelope binding repair snapshot.",
        },
        "ledger_record_ids": [str(x) for x in payload.get("ledger_record_ids", []) if isinstance(x, str)],
        "ledger_artifact_ids": [str(x) for x in payload.get("ledger_artifact_ids", []) if isinstance(x, str)],
        "correlation_pointers": [
            {"type": "invocation_run_id_state", "value": invocation_state, "status": "PRESENT" if invocation_state == "PRESENT" else "MISSING"},
            {"type": "envelope_run_id_state", "value": envelope_state, "status": "PRESENT" if envelope_state == "PRESENT" else "MISSING"},
        ],
    }
    path.write_text(json.dumps(artifact, sort_keys=True, indent=2), encoding="utf-8")
    return path.as_posix(), "written"


def write_context_restoration_artifact(
    *,
    payload: Mapping[str, Any],
    root: Path = Path("artifacts_seal") / "abraxas_context",
) -> tuple[str | None, str]:
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = root / f"{stamp}.context_restoration.json"
    index = 1
    while path.exists():
        path = root / f"{stamp}.{index}.context_restoration.json"
        index += 1
    linkage = _extract_linkage_fields(payload)
    artifact = {
        "generated_at": _utc_now(),
        "ruleset_version": "v4.8.0",
        "source": "operator_console",
        "rune_id": "RUNE.CONTEXT_RESTORE",
        "artifact_id": f"context_restoration.{stamp.lower()}",
        "ledger_record_ids": linkage["ledger_record_ids"],
        "ledger_artifact_ids": linkage["ledger_artifact_ids"],
        "correlation_pointers": linkage["correlation_pointers"],
        **dict(payload),
    }
    path.write_text(json.dumps(artifact, sort_keys=True, indent=2), encoding="utf-8")
    return path.as_posix(), "written"


def _load_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _normalize_timestamp(value: Any) -> Optional[str]:
    if not isinstance(value, str) or not value:
        return None
    text = value.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _latest_timestamp(values: List[Optional[str]]) -> str:
    valid = [v for v in values if isinstance(v, str) and v]
    return max(valid) if valid else "NOT_COMPUTABLE"


def _collect_run_artifacts(base_dir: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    root = base_dir / "artifacts_seal" / "runs"
    if not root.exists():
        return records
    for path in sorted(root.rglob("*.artifact.json")):
        payload = _load_json(path)
        if not payload:
            continue
        run_id = payload.get("run_id")
        if not isinstance(run_id, str) or not run_id:
            continue
        ledger_record_ids = payload.get("ledger_record_ids", [])
        ledger_artifact_ids = payload.get("ledger_artifact_ids", [])
        correlation_pointers = payload.get("correlation_pointers", [])
        normalized_correlation_pointers: List[str] = []
        if isinstance(correlation_pointers, list):
            for pointer in correlation_pointers:
                if isinstance(pointer, str):
                    normalized_correlation_pointers.append(pointer)
                elif isinstance(pointer, (dict, list)):
                    normalized_correlation_pointers.append(json.dumps(pointer, sort_keys=True, separators=(",", ":")))
                else:
                    normalized_correlation_pointers.append(str(pointer))
        records.append(
            {
                "path": path.as_posix(),
                "run_id": run_id,
                "artifact_id": str(payload.get("artifact_id", "")),
                "rune_id": str(payload.get("rune_id", "")),
                "status": str(payload.get("status", "MISSING")),
                "ledger_record_ids_count": len(ledger_record_ids) if isinstance(ledger_record_ids, list) else 0,
                "ledger_artifact_ids_count": len(ledger_artifact_ids) if isinstance(ledger_artifact_ids, list) else 0,
                "correlation_pointers_count": len(correlation_pointers) if isinstance(correlation_pointers, list) else 0,
                "correlation_pointers": normalized_correlation_pointers,
                "timestamp": _normalize_timestamp(payload.get("timestamp")),
            }
        )
    # Run-binding restoration fallback: expose ResultsPack surfaces as partial run artifacts when
    # canonical *.artifact.json files are absent for local runs.
    results_root = base_dir / "artifacts_seal" / "results"
    if results_root.exists():
        known_paths = {str(item["path"]) for item in records}
        for path in sorted(results_root.rglob("*.resultspack.json")):
            if path.as_posix() in known_paths:
                continue
            payload = _load_json(path)
            if not payload:
                continue
            run_id = payload.get("run_id")
            if not isinstance(run_id, str) or not run_id:
                continue
            items = payload.get("items", [])
            status = "SUCCESS"
            if isinstance(items, list):
                if any(isinstance(item, Mapping) and isinstance(item.get("result", {}), Mapping) and str(item["result"].get("status", "ok")) != "ok" for item in items):
                    status = "PARTIAL"
            records.append(
                {
                    "path": path.as_posix(),
                    "run_id": run_id,
                    "artifact_id": f"resultspack.{run_id}",
                    "rune_id": "RUNE.AUDIT",
                    "status": status,
                    "ledger_record_ids_count": 0,
                    "ledger_artifact_ids_count": 0,
                    "correlation_pointers_count": 0,
                    "correlation_pointers": [],
                    "timestamp": None,
                    "binding_surface": "resultspack_fallback",
                }
            )
    return records


def _collect_validator_outputs(base_dir: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    validators_dir = base_dir / "out" / "validators"
    if not validators_dir.exists():
        return records
    for path in sorted(validators_dir.glob("*.json")):
        payload = _load_json(path)
        if not payload:
            continue
        run_id = payload.get("runId")
        if not isinstance(run_id, str) or not run_id:
            continue
        correlation = payload.get("correlation", {})
        ledger_ids = []
        pointers = []
        if isinstance(correlation, Mapping):
            raw_ledger_ids = correlation.get("ledgerIds", [])
            raw_pointers = correlation.get("pointers", [])
            if isinstance(raw_ledger_ids, list):
                ledger_ids = [str(x) for x in raw_ledger_ids if isinstance(x, str)]
            if isinstance(raw_pointers, list):
                pointers = [str(x) for x in raw_pointers if isinstance(x, str)]
        records.append(
            {
                "path": path.as_posix(),
                "run_id": run_id,
                "status": str(payload.get("status", "AVAILABLE")),
                "validated_artifacts_count": len(payload.get("validatedArtifacts", []))
                if isinstance(payload.get("validatedArtifacts", []), list)
                else 0,
                "ledger_ids_count": len(ledger_ids),
                "pointers_count": len(pointers),
                "timestamp": _normalize_timestamp(
                    payload.get("timestamp_utc")
                    or payload.get("timestamp")
                    or payload.get("validatedAt")
                ),
            }
        )
    return records


def _collect_audit_artifacts(base_dir: Path) -> List[str]:
    audits_root = base_dir / "artifacts_seal" / "audits"
    if not audits_root.exists():
        return []
    return [path.relative_to(base_dir).as_posix() for path in sorted(audits_root.rglob("*.json"))]


def _load_closure_status(base_dir: Path) -> str:
    milestone = base_dir / "docs" / "artifacts" / "closure_generalized_milestone_note.v1.json"
    payload = _load_json(milestone)
    if payload and isinstance(payload.get("status"), str):
        return str(payload["status"])
    return "NOT_COMPUTABLE"


def _build_artifact_summary(run_id: str, artifacts: List[Dict[str, Any]]) -> Dict[str, Any]:
    selected = [record for record in artifacts if record["run_id"] == run_id]
    return {"count": len(selected), "artifacts": selected}


def _build_validator_summary(run_id: str, validators: List[Dict[str, Any]]) -> Dict[str, Any]:
    selected = [record for record in validators if record["run_id"] == run_id]
    return {"count": len(selected), "validators": selected}


def _derive_health_label(*, artifact_status: str, validator_status: str, correlation_pointers_count: int, latest_timestamp: str) -> str:
    artifact_ok = artifact_status == "SUCCESS"
    validator_present = validator_status != "MISSING"
    timestamp_present = latest_timestamp != "NOT_COMPUTABLE"
    pointers_present = correlation_pointers_count > 0

    if artifact_ok and validator_present and pointers_present and timestamp_present:
        return "strong"
    if artifact_status != "MISSING" or validator_present or pointers_present or timestamp_present:
        return "partial"
    return "weak"


def _build_selected_run_detail(run_id: str, artifacts: List[Dict[str, Any]], validators: List[Dict[str, Any]]) -> Dict[str, Any]:
    artifact = next((record for record in artifacts if record["run_id"] == run_id), None)
    validator = next((record for record in validators if record["run_id"] == run_id), None)

    latest_timestamp = _latest_timestamp([artifact.get("timestamp") if artifact else None, validator.get("timestamp") if validator else None])
    artifact_status = artifact["status"] if artifact else "MISSING"
    validator_status = validator["status"] if validator else "MISSING"
    correlation_pointers_count = artifact["correlation_pointers_count"] if artifact else 0

    return {
        "artifact_path": artifact["path"] if artifact else None,
        "validator_path": validator["path"] if validator else None,
        "artifact_status": artifact_status,
        "validator_status": validator_status,
        "ledger_record_ids_count": artifact["ledger_record_ids_count"] if artifact else 0,
        "ledger_artifact_ids_count": artifact["ledger_artifact_ids_count"] if artifact else 0,
        "correlation_pointers_count": correlation_pointers_count,
        "latest_timestamp": latest_timestamp,
        "health_label": _derive_health_label(
            artifact_status=artifact_status,
            validator_status=validator_status,
            correlation_pointers_count=correlation_pointers_count,
            latest_timestamp=latest_timestamp,
        ),
    }


def _compute_weakness_reasons(selected_detail: Dict[str, Any]) -> List[str]:
    if str(selected_detail.get("health_label", "")) == "strong":
        return []

    reasons: List[str] = []
    if str(selected_detail.get("validator_status", "")) == "MISSING":
        reasons.append("no validator output")
    if int(selected_detail.get("correlation_pointers_count", 0)) == 0:
        reasons.append("no correlation pointers")
    if int(selected_detail.get("ledger_record_ids_count", 0)) == 0:
        reasons.append("no ledger linkage")
    if str(selected_detail.get("artifact_status", "")) != "SUCCESS":
        reasons.append("artifact not successful")
    if str(selected_detail.get("latest_timestamp", "NOT_COMPUTABLE")) == "NOT_COMPUTABLE":
        reasons.append("missing timestamp")
    return reasons


def _compute_suggested_next_step(selected_detail: Dict[str, Any]) -> str:
    if str(selected_detail.get("validator_status", "")) == "MISSING":
        return "Run validator for this run"
    if int(selected_detail.get("correlation_pointers_count", 0)) == 0:
        return "Inspect or regenerate linkage resolution for this run"
    if int(selected_detail.get("ledger_record_ids_count", 0)) == 0:
        return "Inspect or regenerate ledger continuity record for this run"
    if str(selected_detail.get("artifact_status", "")) != "SUCCESS":
        return "Inspect artifact generation path for this run"
    if str(selected_detail.get("latest_timestamp", "NOT_COMPUTABLE")) == "NOT_COMPUTABLE":
        return "Inspect timestamp normalization for this run"
    return "No action needed"


def _derive_bound_run_context(
    *,
    selected_run_id: Optional[str],
    selected_detail: Mapping[str, Any],
    artifacts: List[Mapping[str, Any]],
    pipeline_workspace_payload: Mapping[str, Any],
) -> Dict[str, Any]:
    if not selected_run_id:
        return {
            "bound_run_id": "NOT_COMPUTABLE",
            "bound_artifact_paths": [],
            "bound_pipeline_id": "NOT_COMPUTABLE",
            "bound_step_summaries": [],
            "binding_status": "MISSING",
            "binding_reason": "NC_MISSING_RUN_BINDING",
            "provenance": "operator_console.binding_restoration.bound_run_context.v4.7",
        }
    run_artifacts = [row for row in artifacts if str(row.get("run_id", "")) == selected_run_id]
    artifact_paths = [str(row.get("path", "")) for row in run_artifacts if str(row.get("path", ""))]
    has_canonical_artifact = bool(selected_detail.get("artifact_path"))
    has_any_artifact = bool(artifact_paths) or has_canonical_artifact
    if has_canonical_artifact:
        binding_status = "BOUND"
        binding_reason = "artifact_path_present"
    elif has_any_artifact:
        binding_status = "PARTIAL_BOUND"
        binding_reason = "fallback_artifact_surface_present"
    else:
        binding_status = "MISSING"
        binding_reason = "NC_MISSING_ARTIFACT"
    return {
        "bound_run_id": selected_run_id,
        "bound_artifact_paths": artifact_paths[:8],
        "bound_pipeline_id": str(pipeline_workspace_payload.get("pipeline_id", "NOT_COMPUTABLE")),
        "bound_step_summaries": [
            f"pipeline_status={str(pipeline_workspace_payload.get('pipeline_status', 'NOT_COMPUTABLE'))}",
            f"pipeline_quality={str(pipeline_workspace_payload.get('pipeline_quality_label', 'NOT_COMPUTABLE'))}",
        ],
        "binding_status": binding_status,
        "binding_reason": binding_reason,
        "provenance": "operator_console.binding_restoration.bound_run_context.v4.7",
    }


def _load_latest_pipeline_binding_snapshot(base_dir: Path, *, preferred_run_id: Optional[str] = None) -> Dict[str, Any]:
    root = base_dir / "artifacts_seal" / "abraxas_pipeline"
    if not root.exists():
        return {"source": "none", "payload": {}, "reason": "pipeline_artifact_root_missing"}
    candidates = sorted(root.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:20]
    fallback: Optional[Dict[str, Any]] = None
    for path in candidates:
        payload = _load_json(path)
        if not payload:
            continue
        envelope = payload.get("pipeline_execution_envelope")
        if not isinstance(envelope, Mapping) or not envelope:
            envelope = payload.get("pipeline_envelope")
        if not isinstance(envelope, Mapping):
            continue
        normalized_payload = dict(payload)
        if not isinstance(normalized_payload.get("pipeline_execution_envelope"), Mapping):
            normalized_payload["pipeline_execution_envelope"] = dict(envelope)
        snapshot = {
            "source": "pipeline_artifact",
            "payload": normalized_payload,
            "reason": f"latest_pipeline_artifact:{path.as_posix()}",
        }
        envelope_run_id = str(envelope.get("run_id", "NOT_COMPUTABLE"))
        if preferred_run_id and preferred_run_id not in {"", "NOT_COMPUTABLE"} and envelope_run_id == preferred_run_id:
            return snapshot
        if fallback is None:
            fallback = snapshot
    if fallback is not None:
        return fallback
    return {"source": "none", "payload": {}, "reason": "no_valid_pipeline_artifact"}


def _derive_operator_bound_run_context(
    *,
    selected_run_id: Optional[str],
    runtime_invocation_envelope: Mapping[str, Any],
    latest_pipeline_envelope: Mapping[str, Any],
    latest_pipeline_export_path: Optional[str],
    latest_pipeline_export_status: str,
    pipeline_binding_snapshot: Mapping[str, Any],
) -> Dict[str, Any]:
    invocation_run_id = str(runtime_invocation_envelope.get("invocation_run_id", runtime_invocation_envelope.get("run_id", "NOT_COMPUTABLE")))
    invocation_run_id_source = str(runtime_invocation_envelope.get("invocation_run_id_source", "none"))
    invocation_run_id_status = str(runtime_invocation_envelope.get("invocation_run_id_status", "MISSING"))
    invocation_pipeline_id = str(runtime_invocation_envelope.get("pipeline_id", "NOT_COMPUTABLE"))
    envelope_run_id = str(latest_pipeline_envelope.get("run_id", "NOT_COMPUTABLE"))
    envelope_pipeline_id = str(latest_pipeline_envelope.get("pipeline_id", "NOT_COMPUTABLE"))
    snapshot_payload = pipeline_binding_snapshot.get("payload", {}) if isinstance(pipeline_binding_snapshot.get("payload", {}), Mapping) else {}
    snapshot_envelope = snapshot_payload.get("pipeline_execution_envelope", {}) if isinstance(snapshot_payload.get("pipeline_execution_envelope", {}), Mapping) else {}
    snapshot_run_id = str(snapshot_envelope.get("run_id", "NOT_COMPUTABLE"))
    snapshot_pipeline_id = str(snapshot_envelope.get("pipeline_id", "NOT_COMPUTABLE"))
    export_bound = bool(latest_pipeline_export_path) and latest_pipeline_export_status == "written"
    if invocation_run_id not in {"", "NOT_COMPUTABLE"} and invocation_pipeline_id not in {"", "NOT_COMPUTABLE"}:
        return {
            "operator_bound_run_id": invocation_run_id,
            "operator_bound_pipeline_id": invocation_pipeline_id,
            "operator_binding_source": "runtime_invocation",
            "operator_binding_status": "BOUND",
            "operator_binding_reason": "runtime_invocation_envelope_present",
            "invocation_run_id": invocation_run_id,
            "invocation_run_id_source": invocation_run_id_source,
            "invocation_run_id_status": invocation_run_id_status,
            "provenance": "operator_console.binding_restoration.operator_bound_run_context.v5.0",
        }
    if envelope_run_id not in {"", "NOT_COMPUTABLE"} and envelope_pipeline_id not in {"", "NOT_COMPUTABLE"}:
        return {
            "operator_bound_run_id": envelope_run_id,
            "operator_bound_pipeline_id": envelope_pipeline_id,
            "operator_binding_source": "latest_pipeline_envelope",
            "operator_binding_status": "BOUND",
            "operator_binding_reason": "latest_pipeline_envelope_present",
            "invocation_run_id": invocation_run_id,
            "invocation_run_id_source": invocation_run_id_source,
            "invocation_run_id_status": invocation_run_id_status,
            "provenance": "operator_console.binding_restoration.operator_bound_run_context.v5.0",
        }
    if snapshot_run_id not in {"", "NOT_COMPUTABLE"} and snapshot_pipeline_id not in {"", "NOT_COMPUTABLE"}:
        return {
            "operator_bound_run_id": snapshot_run_id,
            "operator_bound_pipeline_id": snapshot_pipeline_id,
            "operator_binding_source": "pipeline_envelope_artifact",
            "operator_binding_status": "BOUND",
            "operator_binding_reason": str(pipeline_binding_snapshot.get("reason", "pipeline_artifact_present")),
            "invocation_run_id": invocation_run_id,
            "invocation_run_id_source": invocation_run_id_source,
            "invocation_run_id_status": invocation_run_id_status,
            "provenance": "operator_console.binding_restoration.operator_bound_run_context.v5.0",
        }
    if export_bound and selected_run_id:
        return {
            "operator_bound_run_id": selected_run_id,
            "operator_bound_pipeline_id": str(latest_pipeline_envelope.get("pipeline_id", _ABRAXAS_PIPELINE_ID)),
            "operator_binding_source": "pipeline_export_artifact",
            "operator_binding_status": "PARTIAL_BOUND",
            "operator_binding_reason": "latest_pipeline_export_written_without_resolved_envelope",
            "invocation_run_id": invocation_run_id,
            "invocation_run_id_source": invocation_run_id_source,
            "invocation_run_id_status": invocation_run_id_status,
            "provenance": "operator_console.binding_restoration.operator_bound_run_context.v5.0",
        }
    return {
        "operator_bound_run_id": "NOT_COMPUTABLE",
        "operator_bound_pipeline_id": "NOT_COMPUTABLE",
        "operator_binding_source": "none",
        "operator_binding_status": "UNBOUND",
        "operator_binding_reason": "operator_run_binding_not_found",
        "invocation_run_id": invocation_run_id,
        "invocation_run_id_source": invocation_run_id_source,
        "invocation_run_id_status": invocation_run_id_status,
        "provenance": "operator_console.binding_restoration.operator_bound_run_context.v5.0",
    }


def _derive_pipeline_envelope_linkage(
    *,
    latest_pipeline_envelope: Mapping[str, Any],
    latest_pipeline_steps: List[Mapping[str, Any]],
    pipeline_binding_snapshot: Mapping[str, Any],
    operator_bound_run_context: Mapping[str, Any],
) -> Dict[str, Any]:
    bound_status = str(operator_bound_run_context.get("operator_binding_status", "UNBOUND"))
    invocation_run_id = str(operator_bound_run_context.get("invocation_run_id", "NOT_COMPUTABLE"))
    if bound_status not in {"BOUND", "PARTIAL_BOUND"}:
        return {
            "bound_pipeline_envelope": {},
            "bound_pipeline_step_records": [],
            "envelope_binding_status": "UNBOUND",
            "envelope_binding_reason": "operator_run_unbound",
            "final_state_source_available": False,
            "pipeline_envelope_run_id": "NOT_COMPUTABLE",
            "pipeline_envelope_run_id_status": "MISSING",
            "run_id_match_status": "INVOCATION_MISSING",
            "resolution_source": "none",
            "provenance": "operator_console.binding_restoration.pipeline_envelope_linkage.v5.0",
        }
    latest_envelope_run_id = str(latest_pipeline_envelope.get("run_id", "NOT_COMPUTABLE"))
    exact_match = invocation_run_id not in {"", "NOT_COMPUTABLE"} and latest_envelope_run_id == invocation_run_id
    if str(latest_pipeline_envelope.get("overall_status", "NOT_COMPUTABLE")) != "NOT_COMPUTABLE" or str(
        latest_pipeline_envelope.get("final_classification", "NOT_COMPUTABLE")
    ) != "NOT_COMPUTABLE":
        run_id_status = "PRESENT" if latest_envelope_run_id not in {"", "NOT_COMPUTABLE"} else "MISSING"
        match_status = "EXACT_MATCH" if exact_match else ("INVOCATION_PRESENT_ENVELOPE_MISSING_OR_MISMATCH" if invocation_run_id not in {"", "NOT_COMPUTABLE"} else "INVOCATION_MISSING")
        return {
            "bound_pipeline_envelope": dict(latest_pipeline_envelope),
            "bound_pipeline_step_records": [dict(row) for row in latest_pipeline_steps[:10] if isinstance(row, Mapping)],
            "envelope_binding_status": "BOUND",
            "envelope_binding_reason": "latest_pipeline_envelope_has_final_state_fields",
            "final_state_source_available": True,
            "pipeline_envelope_run_id": latest_envelope_run_id,
            "pipeline_envelope_run_id_status": run_id_status,
            "run_id_match_status": match_status,
            "resolution_source": "latest_pipeline_envelope",
            "provenance": "operator_console.binding_restoration.pipeline_envelope_linkage.v5.0",
        }
    snapshot_payload = pipeline_binding_snapshot.get("payload", {}) if isinstance(pipeline_binding_snapshot.get("payload", {}), Mapping) else {}
    snapshot_envelope = snapshot_payload.get("pipeline_execution_envelope", {}) if isinstance(snapshot_payload.get("pipeline_execution_envelope", {}), Mapping) else {}
    snapshot_steps = snapshot_payload.get("pipeline_step_records", []) if isinstance(snapshot_payload.get("pipeline_step_records", []), list) else []
    snapshot_run_id = str(snapshot_envelope.get("run_id", "NOT_COMPUTABLE")) if isinstance(snapshot_envelope, Mapping) else "NOT_COMPUTABLE"
    if snapshot_envelope:
        has_source = str(snapshot_envelope.get("overall_status", "NOT_COMPUTABLE")) != "NOT_COMPUTABLE" or str(
            snapshot_envelope.get("final_classification", "NOT_COMPUTABLE")
        ) != "NOT_COMPUTABLE"
        return {
            "bound_pipeline_envelope": dict(snapshot_envelope),
            "bound_pipeline_step_records": [dict(row) for row in snapshot_steps[:10] if isinstance(row, Mapping)],
            "envelope_binding_status": "BOUND" if has_source else "UNBOUND",
            "envelope_binding_reason": "pipeline_artifact_snapshot_loaded" if has_source else "pipeline_artifact_missing_final_state_fields",
            "final_state_source_available": has_source,
            "pipeline_envelope_run_id": snapshot_run_id,
            "pipeline_envelope_run_id_status": "PRESENT" if snapshot_run_id not in {"", "NOT_COMPUTABLE"} else "MISSING",
            "run_id_match_status": (
                "EXACT_MATCH"
                if invocation_run_id not in {"", "NOT_COMPUTABLE"} and snapshot_run_id == invocation_run_id
                else ("FALLBACK_MATCH" if has_source and snapshot_run_id not in {"", "NOT_COMPUTABLE"} else "INVOCATION_PRESENT_ENVELOPE_MISSING_OR_MISMATCH")
            ),
            "resolution_source": "pipeline_envelope_artifact" if has_source else "none",
            "provenance": "operator_console.binding_restoration.pipeline_envelope_linkage.v5.0",
        }
    return {
        "bound_pipeline_envelope": {},
        "bound_pipeline_step_records": [],
        "envelope_binding_status": "UNBOUND",
        "envelope_binding_reason": "pipeline_envelope_not_found",
        "final_state_source_available": False,
        "pipeline_envelope_run_id": "NOT_COMPUTABLE",
        "pipeline_envelope_run_id_status": "MISSING",
        "run_id_match_status": "INVOCATION_PRESENT_ENVELOPE_MISSING_OR_MISMATCH" if invocation_run_id not in {"", "NOT_COMPUTABLE"} else "INVOCATION_MISSING",
        "resolution_source": "none",
        "provenance": "operator_console.binding_restoration.pipeline_envelope_linkage.v5.0",
    }


def _derive_refined_binding_nc_subcodes(
    *,
    operator_bound_run_context: Mapping[str, Any],
    pipeline_envelope_linkage: Mapping[str, Any],
) -> List[str]:
    subcodes: List[str] = []
    if str(operator_bound_run_context.get("operator_binding_status", "UNBOUND")) == "UNBOUND":
        subcodes.append("NC_OPERATOR_RUN_UNBOUND")
    if str(pipeline_envelope_linkage.get("envelope_binding_status", "UNBOUND")) == "UNBOUND":
        subcodes.append("NC_PIPELINE_ENVELOPE_UNBOUND")
    if bool(operator_bound_run_context.get("operator_binding_status", "UNBOUND") in {"BOUND", "PARTIAL_BOUND"}) and not bool(
        pipeline_envelope_linkage.get("final_state_source_available", False)
    ):
        subcodes.append("NC_FINAL_STATE_SOURCE_MISSING")
    if (
        str(operator_bound_run_context.get("invocation_run_id_status", "MISSING")) == "PRESENT"
        and str(pipeline_envelope_linkage.get("run_id_match_status", "")) == "INVOCATION_PRESENT_ENVELOPE_MISSING_OR_MISMATCH"
        and str(pipeline_envelope_linkage.get("envelope_binding_status", "UNBOUND")) == "UNBOUND"
    ):
        subcodes.append("NC_INVOCATION_RUN_ID_UNPROPAGATED")
    if (
        str(pipeline_envelope_linkage.get("envelope_binding_status", "UNBOUND")) == "BOUND"
        and str(pipeline_envelope_linkage.get("pipeline_envelope_run_id_status", "MISSING")) == "MISSING"
    ):
        subcodes.append("NC_PIPELINE_ENVELOPE_RUN_ID_MISSING")
    deduped: List[str] = []
    for code in subcodes:
        if code not in deduped:
            deduped.append(code)
    return deduped[:5]


def _derive_binding_envelope_health_surface(
    *,
    operator_bound_run_context: Mapping[str, Any],
    pipeline_envelope_linkage: Mapping[str, Any],
) -> Dict[str, Any]:
    invocation_run_id_present = str(operator_bound_run_context.get("invocation_run_id_status", "MISSING")) == "PRESENT"
    pipeline_envelope_run_id_present = str(pipeline_envelope_linkage.get("pipeline_envelope_run_id_status", "MISSING")) == "PRESENT"
    run_id_match_status = str(pipeline_envelope_linkage.get("run_id_match_status", "INVOCATION_MISSING"))
    operator_run_bound = str(operator_bound_run_context.get("operator_binding_status", "UNBOUND")) in {"BOUND", "PARTIAL_BOUND"}
    pipeline_envelope_bound = str(pipeline_envelope_linkage.get("envelope_binding_status", "UNBOUND")) == "BOUND"
    final_state_derivable = bool(pipeline_envelope_linkage.get("final_state_source_available", False))
    final_state_bindable = final_state_derivable and run_id_match_status in {"EXACT_MATCH", "FALLBACK_MATCH", "INVOCATION_MISSING"}
    synthesis_blocked_by_binding = not final_state_bindable
    if not operator_run_bound:
        blocking_reason = "NC_OPERATOR_RUN_UNBOUND"
    elif invocation_run_id_present and not pipeline_envelope_run_id_present:
        blocking_reason = "NC_INVOCATION_RUN_ID_UNPROPAGATED"
    elif pipeline_envelope_bound and not pipeline_envelope_run_id_present:
        blocking_reason = "NC_PIPELINE_ENVELOPE_RUN_ID_MISSING"
    elif not pipeline_envelope_bound:
        blocking_reason = "NC_PIPELINE_ENVELOPE_UNBOUND"
    elif not final_state_bindable:
        blocking_reason = "NC_FINAL_STATE_SOURCE_MISSING"
    else:
        blocking_reason = "none"
    return {
        "invocation_run_id_present": invocation_run_id_present,
        "pipeline_envelope_run_id_present": pipeline_envelope_run_id_present,
        "run_id_match_status": run_id_match_status,
        "operator_run_bound": operator_run_bound,
        "pipeline_envelope_bound": pipeline_envelope_bound,
        "final_state_derivable": final_state_derivable,
        "final_state_bindable": final_state_bindable,
        "synthesis_blocked_by_binding": synthesis_blocked_by_binding,
        "blocking_reason": blocking_reason,
        "resolution_source": str(pipeline_envelope_linkage.get("resolution_source", "none")),
        "provenance": "operator_console.binding_restoration.binding_envelope_health.v5.0",
    }


def _derive_ledger_bridge(
    *,
    base_dir: Path,
    bound_run_context: Mapping[str, Any],
    selected_detail: Mapping[str, Any],
) -> Dict[str, Any]:
    run_id = str(bound_run_context.get("bound_run_id", "NOT_COMPUTABLE"))
    related_ledger_record_ids: List[str] = []
    related_ledger_artifact_ids: List[str] = []
    if int(selected_detail.get("ledger_record_ids_count", 0)) > 0:
        related_ledger_record_ids.append(f"count:{int(selected_detail.get('ledger_record_ids_count', 0))}")
    if int(selected_detail.get("ledger_artifact_ids_count", 0)) > 0:
        related_ledger_artifact_ids.append(f"count:{int(selected_detail.get('ledger_artifact_ids_count', 0))}")
    ledger_path = base_dir / "out" / "ledger" / "oracle_runs_2026-01-01.jsonl"
    ledger_line_match = False
    if ledger_path.exists() and run_id and run_id != "NOT_COMPUTABLE":
        for line in ledger_path.read_text(encoding="utf-8").splitlines()[:500]:
            if f"\"run_id\": \"{run_id}\"" in line:
                ledger_line_match = True
                break
    if related_ledger_record_ids or related_ledger_artifact_ids:
        status = "LINKED"
        reason = "artifact_ledger_counts_present"
    elif ledger_line_match:
        status = "PARTIAL_LINKED"
        reason = "ledger_line_match_without_artifact_link_counts"
    else:
        status = "MISSING"
        reason = "NC_MISSING_LEDGER_LINK"
    return {
        "related_ledger_record_ids": related_ledger_record_ids[:8],
        "related_ledger_artifact_ids": related_ledger_artifact_ids[:8],
        "ledger_context_summary": f"status={status}; reason={reason}; run_id={run_id}",
        "ledger_bridge_status": status,
        "ledger_bridge_reason": reason,
        "provenance": "operator_console.binding_restoration.ledger_bridge.v4.7",
    }


def _derive_not_computable_subcodes(
    *,
    bound_run_context: Mapping[str, Any],
    ledger_bridge: Mapping[str, Any],
    selected_detail: Mapping[str, Any],
) -> List[str]:
    subcodes: List[str] = []
    if str(bound_run_context.get("binding_status", "MISSING")) == "MISSING":
        subcodes.append("NC_MISSING_RUN_BINDING")
    if str(bound_run_context.get("binding_reason", "")) == "NC_MISSING_ARTIFACT":
        subcodes.append("NC_MISSING_ARTIFACT")
    if str(ledger_bridge.get("ledger_bridge_status", "MISSING")) == "MISSING":
        subcodes.append("NC_MISSING_LEDGER_LINK")
    if str(selected_detail.get("validator_path", "")) in {"", "None"}:
        subcodes.append("NC_MISSING_REQUIRED_CONTEXT")
    if not subcodes:
        return []
    deduped: List[str] = []
    for code in subcodes:
        if code not in deduped:
            deduped.append(code)
    return deduped[:5]


def _derive_binding_health_surface(
    *,
    bound_run_context: Mapping[str, Any],
    ledger_bridge: Mapping[str, Any],
    not_computable_subcodes: List[str],
) -> Dict[str, Any]:
    run_binding_present = str(bound_run_context.get("binding_status", "MISSING")) in {"BOUND", "PARTIAL_BOUND"}
    artifact_linkage_present = bool(bound_run_context.get("bound_artifact_paths", []))
    ledger_bridge_present = str(ledger_bridge.get("ledger_bridge_status", "MISSING")) in {"LINKED", "PARTIAL_LINKED"}
    detector_ready_context_present = run_binding_present and artifact_linkage_present
    reasons: List[str] = []
    if not run_binding_present:
        reasons.append("run_binding_missing")
    if not artifact_linkage_present:
        reasons.append("artifact_linkage_missing")
    if not ledger_bridge_present:
        reasons.append("ledger_bridge_missing")
    if not detector_ready_context_present:
        reasons.append("detector_context_missing")
    return {
        "run_binding_state": "pass" if run_binding_present else "fail",
        "artifact_linkage_state": "pass" if artifact_linkage_present else "fail",
        "ledger_bridge_state": "pass" if ledger_bridge_present else "fail",
        "detector_ready_state": "pass" if detector_ready_context_present else "fail",
        "reasons": reasons[:6],
        "summary": (
            f"binding={str(bound_run_context.get('binding_status', 'MISSING'))}; "
            f"ledger={str(ledger_bridge.get('ledger_bridge_status', 'MISSING'))}; "
            f"detector_ready={'yes' if detector_ready_context_present else 'no'}; "
            f"subcodes={','.join(not_computable_subcodes[:3]) or 'none'}"
        ),
        "provenance": "operator_console.binding_restoration.binding_health.v4.7",
    }


def _derive_required_context_matrix(
    *,
    selected_run_id: Optional[str],
    bound_run_context: Mapping[str, Any],
    pipeline_workspace_payload: Mapping[str, Any],
    detector_fusion_output: Mapping[str, Any],
    synthesis_input_surface: Mapping[str, Any],
) -> Dict[str, Dict[str, Any]]:
    has_selected_run = bool(selected_run_id)
    binding_status = str(bound_run_context.get("binding_status", "MISSING"))
    has_artifacts = bool(bound_run_context.get("bound_artifact_paths", []))
    detector_missing: List[str] = []
    detector_available: List[str] = []
    if has_selected_run:
        detector_available.append("selected_run_id")
    else:
        detector_missing.append("selected_run_id")
    if binding_status in {"BOUND", "PARTIAL_BOUND"}:
        detector_available.append("bound_run_context")
    else:
        detector_missing.append("bound_run_context")
    if has_artifacts:
        detector_available.append("bound_artifact_paths")
    else:
        detector_missing.append("bound_artifact_paths")
    detector_ready = not detector_missing

    fusion_missing: List[str] = []
    fusion_available: List[str] = []
    detector_status = str(detector_fusion_output.get("fused_status", "NOT_COMPUTABLE"))
    if detector_ready:
        fusion_available.append("detector_layer_context")
    else:
        fusion_missing.append("detector_layer_context")
    if detector_status != "NOT_COMPUTABLE":
        fusion_available.append("fusion_input_surface")
    else:
        fusion_missing.append("fusion_input_surface")
    fusion_ready = not fusion_missing

    synthesis_missing: List[str] = []
    synthesis_available: List[str] = []
    if fusion_ready:
        synthesis_available.append("fusion_context")
    else:
        synthesis_missing.append("fusion_context")
    pipeline_status = str(pipeline_workspace_payload.get("pipeline_status", "NOT_COMPUTABLE"))
    if pipeline_status != "NOT_COMPUTABLE":
        synthesis_available.append("pipeline_status")
    else:
        synthesis_missing.append("pipeline_status")
    runtime_outcome = str(synthesis_input_surface.get("runtime_outcome_status", "NOT_COMPUTABLE"))
    if runtime_outcome != "NOT_COMPUTABLE":
        synthesis_available.append("runtime_outcome_status")
    else:
        synthesis_missing.append("runtime_outcome_status")
    synthesis_ready = not synthesis_missing

    return {
        "detector_layer": {
            "ready": detector_ready,
            "missing_fields": detector_missing[:6],
            "available_fields": detector_available[:6],
            "blocking_reason": "none" if detector_ready else f"missing:{detector_missing[0]}",
            "rule_string": "detector requires selected_run_id + bound_run_context + bound_artifact_paths",
            "provenance": "operator_console.context_restoration.required_context.v4.8.detector",
        },
        "fusion_layer": {
            "ready": fusion_ready,
            "missing_fields": fusion_missing[:6],
            "available_fields": fusion_available[:6],
            "blocking_reason": "none" if fusion_ready else f"missing:{fusion_missing[0]}",
            "rule_string": "fusion requires detector_layer_context + fusion_input_surface",
            "provenance": "operator_console.context_restoration.required_context.v4.8.fusion",
        },
        "synthesis_layer": {
            "ready": synthesis_ready,
            "missing_fields": synthesis_missing[:6],
            "available_fields": synthesis_available[:6],
            "blocking_reason": "none" if synthesis_ready else f"missing:{synthesis_missing[0]}",
            "rule_string": "synthesis requires fusion_context + pipeline_status + runtime_outcome_status",
            "provenance": "operator_console.context_restoration.required_context.v4.8.synthesis",
        },
    }


def _derive_projected_context(
    *,
    bound_run_context: Mapping[str, Any],
    pipeline_workspace_payload: Mapping[str, Any],
    latest_pipeline_envelope: Mapping[str, Any],
    latest_pipeline_records: List[Mapping[str, Any]],
    runtime_workspace_payload: Mapping[str, Any],
    compare_delta_summary: Mapping[str, Any],
) -> Dict[str, Any]:
    status_counts: Dict[str, int] = {}
    for row in latest_pipeline_records[:12]:
        label = str(row.get("step_status", "UNKNOWN"))
        status_counts[label] = status_counts.get(label, 0) + 1
    step_rollup = [f"{key}:{status_counts[key]}" for key in sorted(status_counts.keys())]
    comparison_keys = sorted(str(k) for k in compare_delta_summary.keys())[:5]
    comparison_summary = (
        f"keys={comparison_keys}"
        if comparison_keys
        else "NOT_COMPUTABLE:comparison_delta_unavailable"
    )
    return {
        "normalized_pipeline_summary": {
            "pipeline_id": str(latest_pipeline_envelope.get("pipeline_id", "NOT_COMPUTABLE")),
            "pipeline_status": str(pipeline_workspace_payload.get("pipeline_status", "NOT_COMPUTABLE")),
            "pipeline_quality_label": str(pipeline_workspace_payload.get("pipeline_quality_label", "NOT_COMPUTABLE")),
            "provenance": "operator_console.context_restoration.projection.v4.8.pipeline_summary",
        },
        "normalized_step_rollup_summary": {
            "step_status_rollup": step_rollup[:8],
            "total_steps_considered": min(len(latest_pipeline_records), 12),
            "provenance": "operator_console.context_restoration.projection.v4.8.step_rollup",
        },
        "compact_artifact_summary": {
            "bound_run_id": str(bound_run_context.get("bound_run_id", "NOT_COMPUTABLE")),
            "bound_artifact_count": len([x for x in bound_run_context.get("bound_artifact_paths", []) if isinstance(x, str)]),
            "binding_status": str(bound_run_context.get("binding_status", "MISSING")),
            "provenance": "operator_console.context_restoration.projection.v4.8.artifact_summary",
        },
        "bounded_runtime_result_summary": {
            "runtime_outcome_status": str(runtime_workspace_payload.get("outcome_status", "NOT_COMPUTABLE")),
            "runtime_outcome_label": str(runtime_workspace_payload.get("outcome_label", "NOT_COMPUTABLE")),
            "runtime_blockers": [str(x) for x in runtime_workspace_payload.get("outcome_reasons", []) if isinstance(x, str)][:4],
            "provenance": "operator_console.context_restoration.projection.v4.8.runtime_summary",
        },
        "bounded_comparison_summary": {
            "summary": comparison_summary,
            "provenance": "operator_console.context_restoration.projection.v4.8.comparison_summary",
        },
    }


def _derive_context_readiness_surface(
    *,
    required_context_matrix: Mapping[str, Mapping[str, Any]],
) -> Dict[str, Any]:
    detector = required_context_matrix.get("detector_layer", {})
    fusion = required_context_matrix.get("fusion_layer", {})
    synthesis = required_context_matrix.get("synthesis_layer", {})
    detector_ready = bool(detector.get("ready", False))
    fusion_ready = bool(fusion.get("ready", False))
    synthesis_ready = bool(synthesis.get("ready", False))
    return {
        "detector_context_ready": detector_ready,
        "fusion_context_ready": fusion_ready,
        "synthesis_context_ready": synthesis_ready,
        "reasons_when_false": {
            "detector": [] if detector_ready else [str(detector.get("blocking_reason", "missing_detector_context"))],
            "fusion": [] if fusion_ready else [str(fusion.get("blocking_reason", "missing_fusion_context"))],
            "synthesis": [] if synthesis_ready else [str(synthesis.get("blocking_reason", "missing_synthesis_context"))],
        },
        "projection_notes_when_true": {
            "detector": "restored via bounded local projection" if detector_ready else "",
            "fusion": "restored via bounded local projection" if fusion_ready else "",
            "synthesis": "restored via bounded local projection" if synthesis_ready else "",
        },
        "provenance": "operator_console.context_restoration.readiness_surface.v4.8",
    }


def _derive_refined_not_computable_subcodes(
    *,
    observed_subcodes: List[str],
    required_context_matrix: Mapping[str, Mapping[str, Any]],
    compare_delta_summary: Mapping[str, Any],
) -> List[str]:
    subcodes = list(observed_subcodes)
    detector_ready = bool((required_context_matrix.get("detector_layer", {}) or {}).get("ready", False))
    fusion_ready = bool((required_context_matrix.get("fusion_layer", {}) or {}).get("ready", False))
    synthesis_ready = bool((required_context_matrix.get("synthesis_layer", {}) or {}).get("ready", False))
    if not detector_ready:
        subcodes.append("NC_MISSING_DETECTOR_CONTEXT")
    if detector_ready and not fusion_ready:
        subcodes.append("NC_MISSING_FUSION_CONTEXT")
    if fusion_ready and not synthesis_ready:
        subcodes.append("NC_MISSING_SYNTHESIS_CONTEXT")
    if not compare_delta_summary:
        subcodes.append("NC_MISSING_COMPARISON_CONTEXT")
    deduped: List[str] = []
    for code in subcodes:
        if code not in deduped:
            deduped.append(code)
    return deduped[:8]


def _build_evidence_drilldown(
    *,
    run_id: Optional[str],
    selected_detail: Dict[str, Any],
    artifacts: List[Dict[str, Any]],
    audit_paths: List[str],
    preview_limit: int = 3,
) -> Dict[str, Any]:
    if not run_id:
        return {
            "artifact_path": None,
            "validator_path": None,
            "ledger_linkage_summary": "records=0 artifacts=0",
            "correlation_pointers_preview": [],
            "audit_refs_preview": [],
        }

    selected_artifact = next((record for record in artifacts if record["run_id"] == run_id), None)
    correlation_pointers = []
    if selected_artifact is not None and isinstance(selected_artifact.get("correlation_pointers"), list):
        correlation_pointers = [str(item) for item in selected_artifact["correlation_pointers"]]

    scoped_audits = [path for path in audit_paths if run_id in path]
    return {
        "artifact_path": selected_detail.get("artifact_path"),
        "validator_path": selected_detail.get("validator_path"),
        "ledger_linkage_summary": (
            f"records={int(selected_detail.get('ledger_record_ids_count', 0))} "
            f"artifacts={int(selected_detail.get('ledger_artifact_ids_count', 0))}"
        ),
        "correlation_pointers_preview": correlation_pointers[:preview_limit],
        "audit_refs_preview": scoped_audits[:preview_limit],
    }


def _build_snapshot_header(
    *,
    closure_status: str,
    visible_summaries: List[Dict[str, Any]],
    suggested_run_id: Optional[str],
    last_action: Optional[Mapping[str, Any]],
    recent_activity: List[Dict[str, Any]],
) -> Dict[str, Any]:
    health_counts = {"strong": 0, "partial": 0, "weak": 0}
    for row in visible_summaries:
        label = str(row.get("health_label", ""))
        if label in health_counts:
            health_counts[label] += 1

    if last_action is None:
        last_action_summary = "none"
    else:
        last_action_summary = (
            f"{str(last_action.get('outcome_status', 'UNKNOWN'))} "
            f"run={str(last_action.get('triggered_run_id', '') or 'UNAVAILABLE')}"
        )

    if recent_activity:
        newest = recent_activity[0]
        newest_activity_summary = (
            f"{str(newest.get('timestamp', 'NOT_COMPUTABLE'))} "
            f"{str(newest.get('activity_type', 'unknown'))} "
            f"run={str(newest.get('run_id', '') or 'UNAVAILABLE')} "
            f"{str(newest.get('summary', ''))}"
        ).strip()
    else:
        newest_activity_summary = "none"

    return {
        "closure_status": closure_status,
        "visible_run_count": len(visible_summaries),
        "health_counts": health_counts,
        "suggested_focus_run_id": suggested_run_id or "UNAVAILABLE",
        "last_action_summary": last_action_summary,
        "newest_activity_summary": newest_activity_summary,
    }


def _build_compare_strip(
    *,
    selected_run_id: Optional[str],
    comparison_run_id: Optional[str],
    run_summaries: List[Dict[str, Any]],
) -> Dict[str, Any]:
    summary_by_run = {str(row.get("run_id", "")): row for row in run_summaries}

    selected_row = summary_by_run.get(selected_run_id or "")
    comparison_row = summary_by_run.get(comparison_run_id or "") if comparison_run_id else None
    if comparison_row is not None and selected_run_id == comparison_run_id:
        comparison_row = None

    def _compact(row: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not row:
            return {}
        return {
            "run_id": str(row.get("run_id", "")),
            "artifact_status": str(row.get("artifact_status", "MISSING")),
            "validator_status": str(row.get("validator_status", "MISSING")),
            "correlation_pointers_count": int(row.get("correlation_pointers_count", 0)),
            "health_label": str(row.get("health_label", "weak")),
            "latest_timestamp": str(row.get("latest_timestamp", "NOT_COMPUTABLE")),
        }

    enabled = selected_row is not None and comparison_row is not None
    return {
        "enabled": enabled,
        "selected": _compact(selected_row),
        "comparison": _compact(comparison_row),
    }


def _build_compare_delta_summary(compare_strip: Dict[str, Any]) -> Dict[str, Any]:
    if not bool(compare_strip.get("enabled")):
        return {
            "enabled": False,
            "artifact_status_delta": "unchanged",
            "validator_status_delta": "unchanged",
            "correlation_pointers_delta": "no change",
            "health_label_delta": "unchanged",
            "timestamp_ordering": "unavailable",
        }

    selected = compare_strip.get("selected", {})
    comparison = compare_strip.get("comparison", {})

    artifact_status_delta = (
        "changed"
        if str(selected.get("artifact_status", "")) != str(comparison.get("artifact_status", ""))
        else "unchanged"
    )
    validator_status_delta = (
        "changed"
        if str(selected.get("validator_status", "")) != str(comparison.get("validator_status", ""))
        else "unchanged"
    )

    pointer_delta = int(selected.get("correlation_pointers_count", 0)) - int(comparison.get("correlation_pointers_count", 0))
    if pointer_delta > 0:
        correlation_pointers_delta = f"+{pointer_delta}"
    elif pointer_delta < 0:
        correlation_pointers_delta = str(pointer_delta)
    else:
        correlation_pointers_delta = "no change"

    rank = {"weak": 0, "partial": 1, "strong": 2}
    selected_rank = rank.get(str(selected.get("health_label", "weak")), 0)
    comparison_rank = rank.get(str(comparison.get("health_label", "weak")), 0)
    if selected_rank > comparison_rank:
        health_label_delta = "improved"
    elif selected_rank < comparison_rank:
        health_label_delta = "worsened"
    else:
        health_label_delta = "unchanged"

    selected_ts = str(selected.get("latest_timestamp", "NOT_COMPUTABLE"))
    comparison_ts = str(comparison.get("latest_timestamp", "NOT_COMPUTABLE"))
    if selected_ts == "NOT_COMPUTABLE" or comparison_ts == "NOT_COMPUTABLE":
        timestamp_ordering = "unavailable"
    elif selected_ts > comparison_ts:
        timestamp_ordering = "selected newer"
    elif selected_ts < comparison_ts:
        timestamp_ordering = "comparison newer"
    else:
        timestamp_ordering = "same"

    return {
        "enabled": True,
        "artifact_status_delta": artifact_status_delta,
        "validator_status_delta": validator_status_delta,
        "correlation_pointers_delta": correlation_pointers_delta,
        "health_label_delta": health_label_delta,
        "timestamp_ordering": timestamp_ordering,
    }


def _run_family_prefix(run_id: str) -> str:
    parts = run_id.split(".")
    if len(parts) >= 2:
        return ".".join(parts[:2])
    return run_id


def _to_epoch_seconds(timestamp: str) -> Optional[float]:
    if timestamp == "NOT_COMPUTABLE":
        return None
    text = timestamp
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text).timestamp()
    except ValueError:
        return None


def _compute_suggested_compare_candidate(
    *,
    selected_run_id: Optional[str],
    visible_summaries: List[Dict[str, Any]],
) -> tuple[Optional[str], str]:
    if not selected_run_id:
        return None, "no_selected_run"

    ordered = [str(row.get("run_id", "")) for row in visible_summaries if str(row.get("run_id", ""))]
    pool = [run_id for run_id in ordered if run_id != selected_run_id]
    if not pool:
        return None, "no_compare_candidate"

    summary_by_run = {str(row.get("run_id", "")): row for row in visible_summaries}
    selected_row = summary_by_run.get(selected_run_id, {})
    selected_ts = _to_epoch_seconds(str(selected_row.get("latest_timestamp", "NOT_COMPUTABLE")))
    selected_family = _run_family_prefix(selected_run_id)
    order_index = {run_id: idx for idx, run_id in enumerate(ordered)}

    same_family = [run_id for run_id in pool if _run_family_prefix(run_id) == selected_family]
    if same_family:
        same_family.sort(
            key=lambda run_id: (
                0 if _to_epoch_seconds(str(summary_by_run.get(run_id, {}).get("latest_timestamp", "NOT_COMPUTABLE"))) is not None else 1,
                abs(
                    (_to_epoch_seconds(str(summary_by_run.get(run_id, {}).get("latest_timestamp", "NOT_COMPUTABLE"))) or 0.0)
                    - (selected_ts or 0.0)
                ),
                order_index.get(run_id, 10**9),
            )
        )
        return same_family[0], "same_family_nearest_timestamp"

    return pool[0], "fallback_next_visible_run"


def resolve_compare_run_id_for_apply(
    *,
    compare_run_id: Optional[str],
    suggested_compare_run_id: Optional[str],
    apply_suggested_compare: bool,
) -> Optional[str]:
    if apply_suggested_compare and suggested_compare_run_id and suggested_compare_run_id != compare_run_id:
        return suggested_compare_run_id
    return compare_run_id


def _format_delta(value: int) -> str:
    if value > 0:
        return f"+{value}"
    if value < 0:
        return str(value)
    return "no change"


def _build_evidence_delta_preview(
    *,
    selected_run_id: Optional[str],
    comparison_run_id: Optional[str],
    artifacts: List[Dict[str, Any]],
    validators: List[Dict[str, Any]],
    audit_paths: List[str],
) -> Dict[str, Any]:
    if not selected_run_id or not comparison_run_id:
        return {
            "enabled": False,
            "artifact_path_delta": "unchanged",
            "validator_path_delta": "unchanged",
            "ledger_record_ids_delta": "no change",
            "ledger_artifact_ids_delta": "no change",
            "correlation_overlap_count": 0,
            "correlation_selected_only_count": 0,
            "correlation_comparison_only_count": 0,
            "audit_overlap_count": 0,
        }

    selected_detail = _build_selected_run_detail(selected_run_id, artifacts, validators)
    comparison_detail = _build_selected_run_detail(comparison_run_id, artifacts, validators)
    selected_evidence = _build_evidence_drilldown(
        run_id=selected_run_id,
        selected_detail=selected_detail,
        artifacts=artifacts,
        audit_paths=audit_paths,
    )
    comparison_evidence = _build_evidence_drilldown(
        run_id=comparison_run_id,
        selected_detail=comparison_detail,
        artifacts=artifacts,
        audit_paths=audit_paths,
    )

    selected_ptrs = set(str(x) for x in selected_evidence.get("correlation_pointers_preview", []))
    comparison_ptrs = set(str(x) for x in comparison_evidence.get("correlation_pointers_preview", []))
    selected_audits = set(str(x) for x in selected_evidence.get("audit_refs_preview", []))
    comparison_audits = set(str(x) for x in comparison_evidence.get("audit_refs_preview", []))

    return {
        "enabled": True,
        "artifact_path_delta": (
            "changed"
            if str(selected_detail.get("artifact_path")) != str(comparison_detail.get("artifact_path"))
            else "unchanged"
        ),
        "validator_path_delta": (
            "changed"
            if str(selected_detail.get("validator_path")) != str(comparison_detail.get("validator_path"))
            else "unchanged"
        ),
        "ledger_record_ids_delta": _format_delta(
            int(selected_detail.get("ledger_record_ids_count", 0)) - int(comparison_detail.get("ledger_record_ids_count", 0))
        ),
        "ledger_artifact_ids_delta": _format_delta(
            int(selected_detail.get("ledger_artifact_ids_count", 0)) - int(comparison_detail.get("ledger_artifact_ids_count", 0))
        ),
        "correlation_overlap_count": len(selected_ptrs & comparison_ptrs),
        "correlation_selected_only_count": len(selected_ptrs - comparison_ptrs),
        "correlation_comparison_only_count": len(comparison_ptrs - selected_ptrs),
        "audit_overlap_count": len(selected_audits & comparison_audits),
    }


def _normalize_pinned_runs(*, pinned_run_ids: List[str], available_run_ids: List[str], max_items: int = 10) -> List[str]:
    seen = set()
    ordered_visible = [run_id for run_id in available_run_ids if run_id in pinned_run_ids and not (run_id in seen or seen.add(run_id))]
    remaining = sorted(run_id for run_id in pinned_run_ids if run_id not in seen)
    return (ordered_visible + remaining)[:max_items]


def _build_highlights(
    *,
    visible_summaries: List[Dict[str, Any]],
    compare_delta_summary: Dict[str, Any],
    compare_strip: Dict[str, Any],
    limit: int = 8,
) -> List[Dict[str, str]]:
    items: List[Dict[str, str]] = []
    for row in visible_summaries:
        run_id = str(row.get("run_id", ""))
        if str(row.get("validator_status", "")) == "MISSING":
            items.append({"run_id": run_id, "reason": "missing validator output", "severity": "high"})
        if str(row.get("health_label", "")) == "weak":
            items.append({"run_id": run_id, "reason": "weak run health", "severity": "high"})

    if bool(compare_delta_summary.get("enabled")):
        selected_run = str(compare_strip.get("selected", {}).get("run_id", ""))
        if compare_delta_summary.get("health_label_delta") == "worsened":
            items.append({"run_id": selected_run, "reason": "compare shows worsened health", "severity": "high"})
        if str(compare_delta_summary.get("correlation_pointers_delta", "")).startswith("-"):
            items.append({"run_id": selected_run, "reason": "correlation pointers dropped", "severity": "medium"})
        if compare_delta_summary.get("validator_status_delta") == "changed":
            items.append({"run_id": selected_run, "reason": "validator status changed", "severity": "medium"})

    severity_rank = {"high": 0, "medium": 1, "low": 2}
    dedup: Dict[tuple[str, str], Dict[str, str]] = {}
    for item in items:
        key = (item["run_id"], item["reason"])
        dedup[key] = item
    ordered = sorted(dedup.values(), key=lambda x: (severity_rank.get(x["severity"], 9), x["run_id"], x["reason"]))
    return ordered[:limit]


def _build_attention_queue(
    *,
    highlights: List[Dict[str, str]],
    selected_run_id: Optional[str],
    selected_health_label: str,
    suggested_run_id: Optional[str],
    suggested_compare_run_id: Optional[str],
    pinned_run_ids: List[str],
    summary_by_run: Dict[str, Dict[str, Any]],
    limit: int = 5,
) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    seen = set()

    def add(run_id: Optional[str], reason: str, band: str) -> None:
        if not run_id or run_id in seen:
            return
        seen.add(run_id)
        out.append({"run_id": run_id, "reason": reason, "priority_band": band})

    for item in highlights:
        if item.get("severity") == "high":
            add(item.get("run_id"), item.get("reason", "highlight"), "p1_highlight")
    if selected_run_id and selected_health_label != "strong":
        add(selected_run_id, "selected run not strong", "p2_selected")
    add(suggested_run_id, "suggested focus", "p3_focus")
    add(suggested_compare_run_id, "suggested compare", "p4_compare")
    for run_id in pinned_run_ids:
        health = str(summary_by_run.get(run_id, {}).get("health_label", "weak"))
        if health != "strong":
            add(run_id, "pinned run not strong", "p5_pinned")
    return out[:limit]


def _build_triage_panel(
    *,
    visible_summaries: List[Dict[str, Any]],
    highlights: List[Dict[str, str]],
    limit_per_bucket: int = 5,
) -> Dict[str, List[Dict[str, str]]]:
    medium_or_high = {(item["run_id"], item["reason"]) for item in highlights if item["severity"] in {"high", "medium"}}
    buckets = {"needs_action_now": [], "inspect_soon": [], "stable": []}
    for row in visible_summaries:
        run_id = str(row.get("run_id", ""))
        health = str(row.get("health_label", "weak"))
        validator = str(row.get("validator_status", "MISSING"))
        entry = {
            "run_id": run_id,
            "health_label": health,
            "validator_status": validator,
            "latest_timestamp": str(row.get("latest_timestamp", "NOT_COMPUTABLE")),
        }
        if health == "weak" or validator == "MISSING":
            buckets["needs_action_now"].append(entry)
        elif health == "partial" or any(x[0] == run_id for x in medium_or_high):
            buckets["inspect_soon"].append(entry)
        else:
            buckets["stable"].append(entry)

    for key in buckets:
        buckets[key].sort(key=lambda x: (x["latest_timestamp"] == "NOT_COMPUTABLE", x["latest_timestamp"], x["run_id"]), reverse=False)
        buckets[key] = buckets[key][:limit_per_bucket]
    return buckets


def _build_pinned_run_deep_cards(
    *,
    pinned_run_ids: List[str],
    summary_by_run: Dict[str, Dict[str, Any]],
) -> List[Dict[str, str]]:
    cards: List[Dict[str, str]] = []
    for run_id in pinned_run_ids:
        row = summary_by_run.get(run_id, {})
        health = str(row.get("health_label", "weak"))
        validator = str(row.get("validator_status", "MISSING"))
        suggested_next = "No action needed" if health == "strong" else "Inspect selected diagnostics for this run"
        cards.append(
            {
                "run_id": run_id,
                "health_label": health,
                "validator_status": validator,
                "latest_timestamp": str(row.get("latest_timestamp", "NOT_COMPUTABLE")),
                "suggested_next_step": suggested_next,
            }
        )
    return cards


def _select_baseline_run(
    *,
    selected_run_id: Optional[str],
    pinned_run_ids: List[str],
    visible_summaries: List[Dict[str, Any]],
) -> tuple[Optional[str], str]:
    for run_id in pinned_run_ids:
        if run_id == selected_run_id:
            continue
        match = next((row for row in visible_summaries if str(row.get("run_id", "")) == run_id), None)
        if match and str(match.get("health_label", "")) == "strong":
            return run_id, "pinned_strong_baseline"

    strong_candidates = [
        row for row in visible_summaries if str(row.get("health_label", "")) == "strong" and str(row.get("run_id", "")) != str(selected_run_id or "")
    ]
    if strong_candidates:
        strong_candidates.sort(key=lambda r: (str(r.get("latest_timestamp", "NOT_COMPUTABLE")), str(r.get("run_id", ""))), reverse=True)
        return str(strong_candidates[0].get("run_id", "")), "recent_strong_visible_baseline"
    return None, "no_baseline_candidate"


def _build_action_safety_envelope() -> Dict[str, Any]:
    return {
        "allowed_actions": [
            "run_abraxas_pipeline",
            "run_abraxas_pipeline_review_path",
            "run_compliance_probe",
            "run_generalized_coverage_probe",
            "run_execution_validator",
            "run_closure_audit",
            "export_operator_snapshot",
        ],
        "command_preview": {
            "run_abraxas_pipeline": "run canonical static abraxas pipeline envelope",
            "run_abraxas_pipeline_review_path": "run canonical static abraxas review-path pipeline envelope",
            "run_compliance_probe": "python -m aal_core.runes.compliance_probe",
            "run_generalized_coverage_probe": "python -m aal_core.runes.compliance_probe",
            "run_execution_validator": "python -c 'from abx.execution_validator import validate_run, emit_validation_result'",
            "run_closure_audit": "python scripts/run_system_closure_audit.py",
            "export_operator_snapshot": "write operator snapshot artifact",
        },
        "scope_note": "Operator action scope is limited to deterministic compliance/validator/audit execution and snapshot export.",
        "command_family_note": "No additional action families are enabled in this console beyond bounded compliance/snapshot actions.",
    }


def _sanitize_workbench_mode(value: Optional[str]) -> str:
    allowed = ["overview", "runs", "compare", "watch", "export", "runflow", "decision", "session", "governance", "viz", "report", "ers", "runtime", "domain_logic"]
    return str(value) if value in allowed else "overview"


def _build_control_plane(action_history: List[Dict[str, str]], safety: Dict[str, Any]) -> Dict[str, Any]:
    allowed_actions = [str(x) for x in safety.get("allowed_actions", []) if isinstance(x, str)]
    command_preview = safety.get("command_preview", {})
    if not isinstance(command_preview, Mapping):
        command_preview = {}
    return {
        "allowed_actions": allowed_actions,
        "action_states": {action_name: "enabled" for action_name in allowed_actions},
        "command_preview": {str(k): str(v) for k, v in command_preview.items()},
        "safety_note": str(safety.get("scope_note", "")),
        "action_rail": allowed_actions,
        "history_preview": action_history[:5],
    }


def _build_action_presets() -> List[Dict[str, Any]]:
    return [
        {
            "preset_id": "preset.abraxas.pipeline.canonical",
            "action_name": "run_abraxas_pipeline",
            "default_args": {"pipeline_id": "PIPELINE.ABRAXAS.CANONICAL.V3_4"},
            "scope_note": "Run canonical deterministic Abraxas execution pipeline.",
        },
        {
            "preset_id": "preset.abraxas.pipeline.review_path",
            "action_name": "run_abraxas_pipeline_review_path",
            "default_args": {"pipeline_id": "PIPELINE.ABRAXAS.CANONICAL.V4_0.REVIEW_PATH"},
            "scope_note": "Run second canonical deterministic Abraxas review-path pipeline.",
        },
        {
            "preset_id": "preset.compliance_probe.default",
            "action_name": "run_compliance_probe",
            "default_args": {"mode": "default"},
            "scope_note": "Run deterministic compliance probe.",
        },
        {
            "preset_id": "preset.generalized_coverage.probe",
            "action_name": "run_generalized_coverage_probe",
            "default_args": {"mode": "generalized_coverage"},
            "scope_note": "Run generalized-coverage probe via safe compliance action.",
        },
        {
            "preset_id": "preset.execution_validator.selected",
            "action_name": "run_execution_validator",
            "default_args": {"mode": "selected_run"},
            "scope_note": "Run deterministic execution validator for selected run.",
        },
        {
            "preset_id": "preset.closure_audit.default",
            "action_name": "run_closure_audit",
            "default_args": {"mode": "default"},
            "scope_note": "Run deterministic closure audit report.",
        },
        {
            "preset_id": "preset.export.snapshot",
            "action_name": "export_operator_snapshot",
            "default_args": {"mode": "default"},
            "scope_note": "Export current operator snapshot report artifact.",
        },
    ]


def _build_dry_run_preview(
    *,
    selected_preset_id: Optional[str],
    dry_run_enabled: bool,
    presets: List[Dict[str, Any]],
) -> Dict[str, Any]:
    if not dry_run_enabled:
        return {"enabled": False, "status": "not_requested"}
    preset = next((x for x in presets if x["preset_id"] == selected_preset_id), None)
    if preset is None:
        return {
            "enabled": True,
            "status": "invalid_preset",
            "preset_id": selected_preset_id,
            "action_name": "",
            "resolved_command_preview": "",
            "expected_result_path": "",
            "scope_note": "",
        }
    expected_path = (
        "artifacts_seal/operator_snapshots/operator_snapshot.*.json"
        if preset["action_name"] == "export_operator_snapshot"
        else (
            "artifacts_seal/abraxas_pipeline/*.pipeline.json"
            if preset["action_name"] in {"run_abraxas_pipeline", "run_abraxas_pipeline_review_path"}
            else (
            "out/validators/execution-validation-*.json"
            if preset["action_name"] == "run_execution_validator"
            else (
                "artifacts_seal/audits/operator_closure_audit/closure_audit.*.json"
                if preset["action_name"] == "run_closure_audit"
                else "artifacts_seal/runs/compliance_probe/*.artifact.json"
            )
            )
        )
    )
    return {
        "enabled": True,
        "status": "preview_only",
        "preset_id": preset["preset_id"],
        "action_name": preset["action_name"],
        "resolved_command_preview": (
            "run canonical static abraxas pipeline envelope"
            if preset["action_name"] == "run_abraxas_pipeline"
            else (
            "run canonical static abraxas review-path pipeline envelope"
            if preset["action_name"] == "run_abraxas_pipeline_review_path"
            else (
            "python -m aal_core.runes.compliance_probe"
            if preset["action_name"] in {"run_compliance_probe", "run_generalized_coverage_probe"}
            else (
                "python -c 'from abx.execution_validator import validate_run, emit_validation_result'"
                if preset["action_name"] == "run_execution_validator"
                else ("python scripts/run_system_closure_audit.py" if preset["action_name"] == "run_closure_audit" else "write operator snapshot artifact")
            )
            )
            )
        ),
        "expected_result_path": expected_path,
        "scope_note": preset["scope_note"],
    }


def _adapter_run_compliance_probe(payload: Mapping[str, Any]) -> Dict[str, Any]:
    action_result = run_compliance_probe_command()
    run_id = _extract_run_id_from_action_result(action_result)
    return {
        "adapter_name": "adapter.run_compliance_probe",
        "attempted_at": str(action_result.get("timestamp_utc", _utc_now())),
        "outcome_status": str(action_result.get("status", "FAILED")),
        "run_id": run_id or "",
        "artifact_paths": [],
        "summary": "compliance probe completed" if str(action_result.get("status", "")) == "SUCCESS" else "compliance probe failed",
        "error_info": str(action_result.get("stderr_tail", "")) if int(action_result.get("exit_code", 1)) != 0 else "",
    }


def _adapter_run_execution_validator(payload: Mapping[str, Any]) -> Dict[str, Any]:
    run_id = str(payload.get("selected_run_id", ""))
    if not run_id:
        return {
            "adapter_name": "adapter.run_execution_validator",
            "attempted_at": _utc_now(),
            "outcome_status": "NOT_COMPUTABLE",
            "run_id": "",
            "artifact_paths": [],
            "summary": "selected_run_id unavailable for execution validator",
            "error_info": "missing_selected_run_id",
        }
    result = validate_run(run_id=run_id, base_dir=Path("."))
    out_path = emit_validation_result(result, Path("out/validators"))
    status = "SUCCESS" if result.valid else ("NOT_COMPUTABLE" if result.status.value == "not_computable" else "FAILED")
    return {
        "adapter_name": "adapter.run_execution_validator",
        "attempted_at": str(result.checked_at),
        "outcome_status": status,
        "run_id": run_id,
        "artifact_paths": [out_path.as_posix()],
        "summary": f"execution validator {status.lower()} for {run_id}",
        "error_info": "; ".join(result.errors) if result.errors else "",
    }


def _adapter_run_closure_audit(payload: Mapping[str, Any]) -> Dict[str, Any]:
    command = ["python", "scripts/run_system_closure_audit.py"]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    root = Path("artifacts_seal") / "audits" / "operator_closure_audit"
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = root / f"closure_audit.{stamp}.json"
    out_path.write_text(completed.stdout or "{}", encoding="utf-8")
    return {
        "adapter_name": "adapter.run_closure_audit",
        "attempted_at": _utc_now(),
        "outcome_status": "SUCCESS" if completed.returncode == 0 else "FAILED",
        "run_id": "",
        "artifact_paths": [out_path.as_posix()],
        "summary": "closure audit completed" if completed.returncode == 0 else "closure audit failed",
        "error_info": completed.stderr[-600:],
    }


_ABRAXAS_PIPELINE_ID = "PIPELINE.ABRAXAS.CANONICAL.V3_4"
_ABRAXAS_PIPELINE_REVIEW_PATH_ID = "PIPELINE.ABRAXAS.CANONICAL.V4_0.REVIEW_PATH"
_ABRAXAS_PIPELINE_STEP_CATALOG: List[Dict[str, str]] = [
    {"step_name": "ingest", "rune_id": "RUNE.INGEST", "action_name": "run_compliance_probe"},
    {"step_name": "parse", "rune_id": "RUNE.PARSE", "action_name": "pipeline_parse_projection"},
    {"step_name": "map", "rune_id": "RUNE.MAP", "action_name": "pipeline_map_projection"},
    {"step_name": "diff_validate", "rune_id": "RUNE.DIFF", "action_name": "run_execution_validator"},
    {"step_name": "review_audit", "rune_id": "RUNE.AUDIT", "action_name": "run_closure_audit"},
]
_ABRAXAS_PIPELINE_REVIEW_PATH_STEP_CATALOG: List[Dict[str, str]] = [
    {"step_name": "ingest", "rune_id": "RUNE.INGEST"},
    {"step_name": "parse", "rune_id": "RUNE.PARSE"},
    {"step_name": "map", "rune_id": "RUNE.MAP"},
    {"step_name": "review_audit", "rune_id": "RUNE.AUDIT"},
]


def _pipeline_parse_projection(*, selected_run_id: str) -> Dict[str, Any]:
    if not selected_run_id:
        return {
            "status": "NOT_COMPUTABLE",
            "output_summary": "selected_run_id_missing_for_parse_projection",
            "artifact_ref": "",
            "reason": "missing_selected_run_id",
        }
    matches = sorted(Path("artifacts_seal/runs").rglob(f"{selected_run_id}.artifact.json"))
    if not matches:
        return {
            "status": "NOT_COMPUTABLE",
            "output_summary": "run_artifact_not_found_for_parse_projection",
            "artifact_ref": "",
            "reason": "run_artifact_missing",
        }
    payload = _load_json(matches[0]) or {}
    keys = sorted([str(k) for k in payload.keys()])[:8]
    return {
        "status": "SUCCESS",
        "output_summary": f"parsed_keys={keys};status={str(payload.get('status', 'UNKNOWN'))}",
        "artifact_ref": matches[0].as_posix(),
        "reason": "",
    }


def _pipeline_map_projection(
    *,
    parse_projection: Mapping[str, Any],
    selected_run_id: str,
    map_callable_payload: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    if str(parse_projection.get("status", "")) != "SUCCESS":
        return {
            "status": "NOT_COMPUTABLE",
            "output_summary": "map_projection_unavailable_without_parse_success",
            "artifact_ref": "",
            "reason": "parse_projection_unavailable",
            "map_context": {"relation_count": 0, "entities": []},
        }
    if isinstance(map_callable_payload, Mapping):
        entities = [str(x) for x in map_callable_payload.get("entities", []) if isinstance(x, str)]
        relations = [str(x) for x in map_callable_payload.get("relations", []) if isinstance(x, str)]
        if entities or relations:
            map_context = {
                "relation_count": len(relations),
                "entities": entities[:8],
                "run_tokens": [token for token in selected_run_id.split(".") if token][:4],
            }
            return {
                "status": "SUCCESS",
                "output_summary": (
                    f"map_callable_entities={map_context['entities']};"
                    f"map_callable_relation_count={map_context['relation_count']}"
                ),
                "artifact_ref": str(map_callable_payload.get("artifact_ref", "")),
                "reason": "",
                "map_context": map_context,
            }
    return {
        "status": "NOT_COMPUTABLE",
        "output_summary": "map_projection_callable_not_exposed",
        "artifact_ref": "",
        "reason": "map_callable_not_exposed",
        "map_context": {"relation_count": 0, "entities": [], "run_tokens": [token for token in selected_run_id.split(".") if token][:4]},
    }


def _pipeline_diff_projection(*, parse_projection: Mapping[str, Any], map_projection: Mapping[str, Any]) -> Dict[str, Any]:
    parse_ok = str(parse_projection.get("status", "")) == "SUCCESS"
    map_ok = str(map_projection.get("status", "")) == "SUCCESS"
    if not parse_ok or not map_ok:
        return {
            "status": "NOT_COMPUTABLE",
            "summary": "diff_projection_unavailable_without_parse_and_map_success",
            "reason": "parse_or_map_unavailable",
            "categories": {"entities": 0, "relations": 0, "status_alignment": "unknown"},
        }
    map_context = map_projection.get("map_context", {}) if isinstance(map_projection.get("map_context", {}), Mapping) else {}
    entities = [str(x) for x in map_context.get("entities", []) if isinstance(x, str)]
    relation_count = int(map_context.get("relation_count", 0))
    delta_entities = len(set(entities))
    categories = {
        "entities": delta_entities,
        "relations": relation_count,
        "status_alignment": "aligned" if relation_count >= delta_entities else "partial",
    }
    return {
        "status": "SUCCESS",
        "summary": f"diff_categories={categories};entity_delta={delta_entities};relation_delta={relation_count}",
        "reason": "",
        "categories": categories,
    }


def _classify_pipeline_final_result(
    *,
    step_records: Sequence[Mapping[str, Any]],
    artifact_paths: Sequence[str],
    linkage: Mapping[str, Sequence[Any]],
    required_steps: Sequence[str] = ("ingest", "diff_validate", "review_audit"),
) -> Dict[str, Any]:
    required_step_names = tuple(str(x) for x in required_steps if isinstance(x, str) and str(x))
    normalized_steps = [row for row in step_records if isinstance(row, Mapping)]
    step_status_by_name = {str(row.get("step_name", "")): str(row.get("status", "NOT_COMPUTABLE")) for row in normalized_steps}
    failed_steps = [name for name in required_step_names if step_status_by_name.get(name) == "FAILED"]
    not_computable_steps = [name for name in required_step_names if step_status_by_name.get(name) == "NOT_COMPUTABLE"]
    incomplete_steps = [
        name
        for name in required_step_names
        if step_status_by_name.get(name) in {"SKIPPED", ""}
        or name not in step_status_by_name
    ]
    successful_steps = [name for name in required_step_names if step_status_by_name.get(name) in {"SUCCESS", "VALID"}]
    artifact_count = len([x for x in artifact_paths if isinstance(x, str) and x])
    ledger_count = len([x for x in linkage.get("ledger_record_ids", []) if x])
    ledger_artifact_count = len([x for x in linkage.get("ledger_artifact_ids", []) if x])
    correlation_count = len([x for x in linkage.get("correlation_pointers", []) if x])
    linkage_observed = any(key in linkage for key in ("ledger_record_ids", "ledger_artifact_ids", "correlation_pointers"))
    linkage_complete = ledger_count > 0 or ledger_artifact_count > 0 or correlation_count > 0
    synthetic_projection_steps = [
        str(row.get("step_name", ""))
        for row in normalized_steps
        if isinstance(row.get("provenance"), str) and ".projection" in str(row.get("provenance", ""))
    ]
    if failed_steps:
        classification = "FAILED"
        rule = "classification.required_step_failed"
        reason = f"failed_steps={failed_steps[:3]}"
    elif not_computable_steps:
        classification = "NOT_COMPUTABLE"
        rule = "classification.required_step_not_computable"
        reason = f"not_computable_steps={not_computable_steps[:3]}"
    elif incomplete_steps:
        classification = "PARTIAL"
        rule = "classification.required_step_incomplete"
        reason = f"incomplete_steps={incomplete_steps[:3]}"
    elif synthetic_projection_steps:
        classification = "PARTIAL"
        rule = "classification.synthetic_projection_detected"
        reason = f"projection_steps={synthetic_projection_steps[:3]}"
    elif artifact_count < len(required_step_names):
        classification = "PARTIAL"
        rule = "classification.artifact_presence_incomplete"
        reason = f"artifact_count={artifact_count}"
    elif linkage_observed and not linkage_complete and artifact_count > 0 and artifact_count < len(required_steps):
        classification = "PARTIAL"
        rule = "classification.linkage_incomplete"
        reason = "linkage_fields_present_but_empty"
    else:
        classification = "SUCCESS"
        rule = "classification.required_steps_satisfied"
        reason = "required_steps_success_and_linkage_present"
    return {
        "final_classification": classification,
        "overall_status": classification,
        "overall_status_rule": rule,
        "overall_status_reason": reason[:180],
        "blocking_steps": (failed_steps or not_computable_steps or incomplete_steps)[:5],
        "successful_steps": successful_steps[:5],
        "artifact_summary": {
            "artifact_count": artifact_count,
            "ledger_record_count": ledger_count,
            "ledger_artifact_count": ledger_artifact_count,
            "correlation_pointer_count": correlation_count,
            "linkage_complete": "true" if linkage_complete else "false",
        },
    }


def _adapter_run_abraxas_pipeline(payload: Mapping[str, Any]) -> Dict[str, Any]:
    selected_run_id = str(payload.get("invocation_run_id", "") or payload.get("selected_run_id", "")).strip()
    started_at = _utc_now()
    step_records: List[Dict[str, Any]] = []
    artifact_paths: List[str] = []
    has_failure = False
    last_completed_step = "NOT_STARTED"

    ingest_result = _adapter_run_compliance_probe(payload)
    ingest_status = str(ingest_result.get("outcome_status", "FAILED"))
    ingest_artifact = next((str(x) for x in ingest_result.get("artifact_paths", []) if isinstance(x, str)), "")
    if ingest_artifact:
        artifact_paths.append(ingest_artifact)
    step_records.append(
        {
            "step_index": 1,
            "step_name": "ingest",
            "rune_id": "RUNE.INGEST",
            "input_summary": {"selected_run_id": selected_run_id},
            "output_summary": str(ingest_result.get("summary", ""))[:180],
            "artifact_ref": ingest_artifact,
            "status": ingest_status,
            "reason": "" if ingest_status == "SUCCESS" else str(ingest_result.get("error_info", "ingest_failed")),
            "provenance": "pipeline.step.ingest.v3.4.adapter.run_compliance_probe",
        }
    )
    if ingest_status == "SUCCESS":
        last_completed_step = "ingest"
    else:
        has_failure = True

    parse_projection = _pipeline_parse_projection(selected_run_id=selected_run_id)
    step_records.append(
        {
            "step_index": 2,
            "step_name": "parse",
            "rune_id": "RUNE.PARSE",
            "input_summary": {"selected_run_id": selected_run_id},
            "output_summary": str(parse_projection.get("output_summary", ""))[:220],
            "artifact_ref": str(parse_projection.get("artifact_ref", "")),
            "status": str(parse_projection.get("status", "NOT_COMPUTABLE")),
            "reason": str(parse_projection.get("reason", "")),
            "provenance": "pipeline.step.parse.v3.5.projection",
        }
    )
    if str(parse_projection.get("status", "")) == "SUCCESS":
        last_completed_step = "parse"
    map_projection = _pipeline_map_projection(
        parse_projection=parse_projection,
        selected_run_id=selected_run_id,
        map_callable_payload=payload.get("map_projection_payload")
        if isinstance(payload.get("map_projection_payload"), Mapping)
        else None,
    )
    map_context = map_projection.get("map_context", {}) if isinstance(map_projection.get("map_context", {}), Mapping) else {}
    step_records.append(
        {
            "step_index": 3,
            "step_name": "map",
            "rune_id": "RUNE.MAP",
            "input_summary": {"selected_run_id": selected_run_id, "parse_status": str(parse_projection.get("status", "NOT_COMPUTABLE"))},
            "output_summary": str(map_projection.get("output_summary", ""))[:220],
            "artifact_ref": str(map_projection.get("artifact_ref", "")),
            "status": str(map_projection.get("status", "NOT_COMPUTABLE")),
            "reason": str(map_projection.get("reason", "")),
            "provenance": "pipeline.step.map.v3.6.projection",
        }
    )
    if str(map_projection.get("status", "")) == "SUCCESS":
        last_completed_step = "map"

    if has_failure:
        step_records.extend(
            [
                {
                    "step_index": 4,
                    "step_name": "diff_validate",
                    "rune_id": "RUNE.DIFF",
                    "input_summary": {"selected_run_id": selected_run_id},
                    "output_summary": "skipped_due_to_prior_failure",
                    "artifact_ref": "",
                    "status": "SKIPPED",
                    "reason": "prior_required_step_failed",
                    "provenance": "pipeline.step.diff_validate.v3.4.skip_rule",
                },
                {
                    "step_index": 5,
                    "step_name": "review_audit",
                    "rune_id": "RUNE.AUDIT",
                    "input_summary": {"selected_run_id": selected_run_id},
                    "output_summary": "skipped_due_to_prior_failure",
                    "artifact_ref": "",
                    "status": "SKIPPED",
                    "reason": "prior_required_step_failed",
                    "provenance": "pipeline.step.review_audit.v3.4.skip_rule",
                },
            ]
        )
    else:
        diff_projection = _pipeline_diff_projection(parse_projection=parse_projection, map_projection=map_projection)
        diff_result = _adapter_run_execution_validator({"selected_run_id": selected_run_id})
        diff_status = str(diff_result.get("outcome_status", "FAILED"))
        diff_artifact = next((str(x) for x in diff_result.get("artifact_paths", []) if isinstance(x, str)), "")
        if diff_artifact:
            artifact_paths.append(diff_artifact)
        diff_projection_status = str(diff_projection.get("status", "NOT_COMPUTABLE"))
        resolved_diff_status = diff_status if diff_projection_status == "SUCCESS" else ("NOT_COMPUTABLE" if diff_status in {"SUCCESS", "VALID"} else diff_status)
        step_records.append(
            {
                "step_index": 4,
                "step_name": "diff_validate",
                "rune_id": "RUNE.DIFF",
                "input_summary": {
                    "selected_run_id": selected_run_id,
                    "map_context": {
                        "relation_count": int(map_context.get("relation_count", 0)),
                        "entities": [str(x) for x in map_context.get("entities", [])[:4]],
                    },
                    "diff_projection_status": diff_projection_status,
                },
                "output_summary": (
                    f"{str(diff_result.get('summary', ''))[:140]}"
                    f"|map_relations={int(map_context.get('relation_count', 0))}"
                    f"|map_entities={[str(x) for x in map_context.get('entities', [])[:4]]}"
                    f"|{str(diff_projection.get('summary', ''))[:180]}"
                ),
                "artifact_ref": diff_artifact,
                "status": resolved_diff_status,
                "reason": (
                    ""
                    if resolved_diff_status in {"SUCCESS", "VALID"}
                    else (str(diff_projection.get("reason", "")) or str(diff_result.get("error_info", "diff_validation_failed")))
                ),
                "provenance": "pipeline.step.diff_validate.v3.4.adapter.run_execution_validator",
            }
        )
        if resolved_diff_status in {"SUCCESS", "VALID"}:
            last_completed_step = "diff_validate"
            audit_result = _adapter_run_closure_audit({"selected_run_id": selected_run_id})
            audit_status = str(audit_result.get("outcome_status", "FAILED"))
            audit_artifact = next((str(x) for x in audit_result.get("artifact_paths", []) if isinstance(x, str)), "")
            if audit_artifact:
                artifact_paths.append(audit_artifact)
            step_records.append(
                {
                    "step_index": 5,
                    "step_name": "review_audit",
                    "rune_id": "RUNE.AUDIT",
                    "input_summary": {
                        "selected_run_id": selected_run_id,
                        "diff_projection_status": diff_projection_status,
                        "diff_categories": dict(diff_projection.get("categories", {})) if isinstance(diff_projection.get("categories", {}), Mapping) else {},
                    },
                    "output_summary": str(audit_result.get("summary", ""))[:180],
                    "artifact_ref": audit_artifact,
                    "status": audit_status,
                    "reason": "" if audit_status == "SUCCESS" else str(audit_result.get("error_info", "audit_failed")),
                    "provenance": "pipeline.step.review_audit.v3.4.adapter.run_closure_audit",
                }
            )
            if audit_status == "SUCCESS":
                last_completed_step = "review_audit"
            else:
                has_failure = True
        else:
            has_failure = True
            step_records.append(
                {
                    "step_index": 5,
                    "step_name": "review_audit",
                    "rune_id": "RUNE.AUDIT",
                    "input_summary": {"selected_run_id": selected_run_id},
                    "output_summary": "skipped_due_to_prior_failure",
                    "artifact_ref": "",
                    "status": "SKIPPED",
                    "reason": "prior_required_step_failed",
                    "provenance": "pipeline.step.review_audit.v3.4.skip_rule",
                }
            )

    completed_at = _utc_now()
    latest_run_id = selected_run_id or "NOT_COMPUTABLE"
    diff_row = next((step for step in step_records if step["step_name"] == "diff_validate"), {})
    review_row = next((step for step in step_records if step["step_name"] == "review_audit"), {})
    linkage = {
        "ledger_record_ids": [],
        "ledger_artifact_ids": [],
        "correlation_pointers": [
            {
                "type": "linkage_state",
                "value": "UNRESOLVED",
                "status": "UNRESOLVED",
                "reason": "LINKAGE_NOT_COMPUTABLE",
            }
        ],
    }
    result_rollup = _classify_pipeline_final_result(step_records=step_records, artifact_paths=artifact_paths, linkage=linkage)
    final_classification = str(result_rollup.get("final_classification", "NOT_COMPUTABLE"))
    overall_status = str(result_rollup.get("overall_status", final_classification))
    final_summary_block = {
        "final_classification": final_classification,
        "overall_status_rule": str(result_rollup.get("overall_status_rule", "")),
        "overall_status_reason": str(result_rollup.get("overall_status_reason", "")),
        "blocking_steps": [str(x) for x in result_rollup.get("blocking_steps", []) if isinstance(x, str)][:5],
        "successful_steps": [str(x) for x in result_rollup.get("successful_steps", []) if isinstance(x, str)][:5],
        "artifact_summary": dict(result_rollup.get("artifact_summary", {})) if isinstance(result_rollup.get("artifact_summary", {}), Mapping) else {},
    }
    review_input = review_row.get("input_summary", {}) if isinstance(review_row.get("input_summary", {}), Mapping) else {}
    review_base = str(review_row.get("output_summary", ""))
    review_summary = (
        f"{review_base[:110]}"
        f"|final_classification={final_classification}"
        f"|blockers={final_summary_block['blocking_steps']}"
        f"|successes={final_summary_block['successful_steps']}"
        f"|artifact_count={int(final_summary_block['artifact_summary'].get('artifact_count', 0))}"
    )[:220]
    if review_row:
        review_row["input_summary"] = {
            **dict(review_input),
            "final_classification": final_classification,
            "overall_status_rule": final_summary_block["overall_status_rule"],
        }
        review_row["output_summary"] = review_summary
    pipeline_envelope = {
        "pipeline_id": _ABRAXAS_PIPELINE_ID,
        "run_id": latest_run_id,
        "artifact_id": f"pipeline_envelope.{datetime.now(timezone.utc).strftime('%Y%m%dt%H%M%SZ').lower()}",
        "run_id_propagation_status": "PRESENT" if latest_run_id != "NOT_COMPUTABLE" else "MISSING",
        "started_at": started_at,
        "completed_at": completed_at,
        "overall_status": overall_status,
        "step_count": len(step_records),
        "current_step": "completed",
        "last_completed_step": last_completed_step,
        "final_classification": final_classification,
        "overall_status_rule": final_summary_block["overall_status_rule"],
        "overall_status_reason": final_summary_block["overall_status_reason"],
        "final_summary_block": final_summary_block,
        "final_result_summary": (
            f"{overall_status}|steps={len(step_records)}|artifacts={len(artifact_paths)}"
            f"|diff_status={str(diff_row.get('status', 'NOT_COMPUTABLE'))}"
            f"|review_status={str(review_row.get('status', 'NOT_COMPUTABLE'))}"
            f"|classification={final_classification}"
        ),
        "artifact_paths": artifact_paths[:8],
        "provenance": "operator_console.pipeline.v3.4.canonical_static_path",
        "ledger_record_ids": list(linkage["ledger_record_ids"])[:8],
        "ledger_artifact_ids": list(linkage["ledger_artifact_ids"])[:8],
        "correlation_pointers": list(linkage["correlation_pointers"])[:8],
    }
    pipeline_state_surface = {
        "latest_pipeline_run": latest_run_id,
        "pipeline_status": overall_status,
        "step_progression": [f"{step['step_index']}:{step['step_name']}={step['status']}" for step in step_records][:10],
        "latest_step_outputs": [{"step_name": step["step_name"], "output_summary": step["output_summary"]} for step in step_records if step["status"] in {"SUCCESS", "NOT_COMPUTABLE"}][:5],
        "pipeline_failure_point": next((step["step_name"] for step in step_records if step["status"] == "FAILED"), ""),
        "pipeline_state_summary": pipeline_envelope["final_result_summary"],
    }
    return {
        "adapter_name": "adapter.run_abraxas_pipeline",
        "attempted_at": started_at,
        "outcome_status": overall_status,
        "run_id": latest_run_id,
        "artifact_paths": artifact_paths[:8],
        "summary": pipeline_envelope["final_result_summary"],
        "error_info": "" if overall_status == "SUCCESS" else str(pipeline_state_surface.get("pipeline_failure_point", "pipeline_failed")),
        "pipeline_id": _ABRAXAS_PIPELINE_ID,
        "pipeline_envelope": pipeline_envelope,
        "pipeline_step_records": step_records[:10],
        "pipeline_state_surface": pipeline_state_surface,
    }


def _adapter_run_abraxas_pipeline_review_path(payload: Mapping[str, Any]) -> Dict[str, Any]:
    selected_run_id = str(payload.get("invocation_run_id", "") or payload.get("selected_run_id", "")).strip()
    started_at = _utc_now()
    step_records: List[Dict[str, Any]] = []
    artifact_paths: List[str] = []
    has_failure = False
    last_completed_step = "NOT_STARTED"
    ingest_result = _adapter_run_compliance_probe(payload)
    ingest_status = str(ingest_result.get("outcome_status", "FAILED"))
    ingest_artifact = next((str(x) for x in ingest_result.get("artifact_paths", []) if isinstance(x, str)), "")
    if ingest_artifact:
        artifact_paths.append(ingest_artifact)
    step_records.append(
        {
            "step_index": 1,
            "step_name": "ingest",
            "rune_id": "RUNE.INGEST",
            "input_summary": {"selected_run_id": selected_run_id},
            "output_summary": str(ingest_result.get("summary", ""))[:180],
            "artifact_ref": ingest_artifact,
            "status": ingest_status,
            "reason": "" if ingest_status == "SUCCESS" else str(ingest_result.get("error_info", "ingest_failed")),
            "provenance": "pipeline.review_path.step.ingest.v4.0.adapter.run_compliance_probe",
        }
    )
    if ingest_status == "SUCCESS":
        last_completed_step = "ingest"
    else:
        has_failure = True
    parse_projection = _pipeline_parse_projection(selected_run_id=selected_run_id)
    step_records.append(
        {
            "step_index": 2,
            "step_name": "parse",
            "rune_id": "RUNE.PARSE",
            "input_summary": {"selected_run_id": selected_run_id},
            "output_summary": str(parse_projection.get("output_summary", ""))[:220],
            "artifact_ref": str(parse_projection.get("artifact_ref", "")),
            "status": str(parse_projection.get("status", "NOT_COMPUTABLE")),
            "reason": str(parse_projection.get("reason", "")),
            "provenance": "pipeline.review_path.step.parse.v4.0.projection",
        }
    )
    if str(parse_projection.get("status", "")) == "SUCCESS":
        last_completed_step = "parse"
    map_projection = _pipeline_map_projection(
        parse_projection=parse_projection,
        selected_run_id=selected_run_id,
        map_callable_payload=payload.get("map_projection_payload")
        if isinstance(payload.get("map_projection_payload"), Mapping)
        else None,
    )
    map_context = map_projection.get("map_context", {}) if isinstance(map_projection.get("map_context", {}), Mapping) else {}
    step_records.append(
        {
            "step_index": 3,
            "step_name": "map",
            "rune_id": "RUNE.MAP",
            "input_summary": {"selected_run_id": selected_run_id, "parse_status": str(parse_projection.get("status", "NOT_COMPUTABLE"))},
            "output_summary": str(map_projection.get("output_summary", ""))[:220],
            "artifact_ref": str(map_projection.get("artifact_ref", "")),
            "status": str(map_projection.get("status", "NOT_COMPUTABLE")),
            "reason": str(map_projection.get("reason", "")),
            "provenance": "pipeline.review_path.step.map.v4.0.projection",
        }
    )
    if str(map_projection.get("status", "")) == "SUCCESS":
        last_completed_step = "map"
    if has_failure:
        step_records.append(
            {
                "step_index": 4,
                "step_name": "review_audit",
                "rune_id": "RUNE.AUDIT",
                "input_summary": {"selected_run_id": selected_run_id},
                "output_summary": "skipped_due_to_prior_failure",
                "artifact_ref": "",
                "status": "SKIPPED",
                "reason": "prior_required_step_failed",
                "provenance": "pipeline.review_path.step.review_audit.v4.0.skip_rule",
            }
        )
    else:
        audit_result = _adapter_run_closure_audit({"selected_run_id": selected_run_id})
        audit_status = str(audit_result.get("outcome_status", "FAILED"))
        audit_artifact = next((str(x) for x in audit_result.get("artifact_paths", []) if isinstance(x, str)), "")
        if audit_artifact:
            artifact_paths.append(audit_artifact)
        step_records.append(
            {
                "step_index": 4,
                "step_name": "review_audit",
                "rune_id": "RUNE.AUDIT",
                "input_summary": {
                    "selected_run_id": selected_run_id,
                    "map_context": {
                        "relation_count": int(map_context.get("relation_count", 0)),
                        "entities": [str(x) for x in map_context.get("entities", [])[:4]],
                    },
                },
                "output_summary": str(audit_result.get("summary", ""))[:180],
                "artifact_ref": audit_artifact,
                "status": audit_status,
                "reason": "" if audit_status == "SUCCESS" else str(audit_result.get("error_info", "audit_failed")),
                "provenance": "pipeline.review_path.step.review_audit.v4.0.adapter.run_closure_audit",
            }
        )
        if audit_status == "SUCCESS":
            last_completed_step = "review_audit"
    completed_at = _utc_now()
    linkage = {
        "ledger_record_ids": [],
        "ledger_artifact_ids": [],
        "correlation_pointers": [
            {
                "type": "linkage_state",
                "value": "UNRESOLVED",
                "status": "UNRESOLVED",
                "reason": "LINKAGE_NOT_COMPUTABLE",
            }
        ],
    }
    result_rollup = _classify_pipeline_final_result(
        step_records=step_records,
        artifact_paths=artifact_paths,
        linkage=linkage,
        required_steps=("ingest", "map", "review_audit"),
    )
    final_classification = str(result_rollup.get("final_classification", "NOT_COMPUTABLE"))
    overall_status = str(result_rollup.get("overall_status", final_classification))
    final_summary_block = {
        "final_classification": final_classification,
        "overall_status_rule": str(result_rollup.get("overall_status_rule", "")),
        "overall_status_reason": str(result_rollup.get("overall_status_reason", "")),
        "blocking_steps": [str(x) for x in result_rollup.get("blocking_steps", []) if isinstance(x, str)][:5],
        "successful_steps": [str(x) for x in result_rollup.get("successful_steps", []) if isinstance(x, str)][:5],
        "artifact_summary": dict(result_rollup.get("artifact_summary", {})) if isinstance(result_rollup.get("artifact_summary", {}), Mapping) else {},
    }
    pipeline_envelope = {
        "pipeline_id": _ABRAXAS_PIPELINE_REVIEW_PATH_ID,
        "run_id": selected_run_id or "NOT_COMPUTABLE",
        "artifact_id": f"pipeline_envelope.{datetime.now(timezone.utc).strftime('%Y%m%dt%H%M%SZ').lower()}",
        "run_id_propagation_status": "PRESENT" if selected_run_id else "MISSING",
        "started_at": started_at,
        "completed_at": completed_at,
        "overall_status": overall_status,
        "final_classification": final_classification,
        "overall_status_rule": final_summary_block["overall_status_rule"],
        "overall_status_reason": final_summary_block["overall_status_reason"],
        "step_count": len(step_records),
        "current_step": "completed",
        "last_completed_step": last_completed_step,
        "final_summary_block": final_summary_block,
        "final_result_summary": (
            f"{overall_status}|steps={len(step_records)}|artifacts={len(artifact_paths)}"
            f"|map_status={str(next((step.get('status') for step in step_records if step.get('step_name') == 'map'), 'NOT_COMPUTABLE'))}"
            f"|review_status={str(next((step.get('status') for step in step_records if step.get('step_name') == 'review_audit'), 'NOT_COMPUTABLE'))}"
            f"|classification={final_classification}"
        ),
        "artifact_paths": artifact_paths[:8],
        "provenance": "operator_console.pipeline.review_path.v4.0.canonical_static_path",
        "ledger_record_ids": [],
        "ledger_artifact_ids": [],
        "correlation_pointers": [],
    }
    pipeline_state_surface = {
        "latest_pipeline_run": selected_run_id or "NOT_COMPUTABLE",
        "pipeline_status": overall_status,
        "step_progression": [f"{step['step_index']}:{step['step_name']}={step['status']}" for step in step_records][:10],
        "latest_step_outputs": [{"step_name": step["step_name"], "output_summary": step["output_summary"]} for step in step_records if step["status"] in {"SUCCESS", "NOT_COMPUTABLE"}][:5],
        "pipeline_failure_point": next((step["step_name"] for step in step_records if step["status"] == "FAILED"), ""),
        "pipeline_state_summary": pipeline_envelope["final_result_summary"],
    }
    return {
        "adapter_name": "adapter.run_abraxas_pipeline_review_path",
        "attempted_at": started_at,
        "outcome_status": overall_status,
        "run_id": selected_run_id or "NOT_COMPUTABLE",
        "artifact_paths": artifact_paths[:8],
        "summary": pipeline_envelope["final_result_summary"],
        "error_info": "" if overall_status == "SUCCESS" else str(pipeline_state_surface.get("pipeline_failure_point", "pipeline_failed")),
        "pipeline_id": _ABRAXAS_PIPELINE_REVIEW_PATH_ID,
        "pipeline_envelope": pipeline_envelope,
        "pipeline_step_records": step_records[:10],
        "pipeline_state_surface": pipeline_state_surface,
    }


_RUNTIME_ADAPTERS: Dict[str, Any] = {
    "run_abraxas_pipeline": _adapter_run_abraxas_pipeline,
    "run_abraxas_pipeline_review_path": _adapter_run_abraxas_pipeline_review_path,
    "run_compliance_probe": _adapter_run_compliance_probe,
    "run_generalized_coverage_probe": _adapter_run_compliance_probe,
    "run_execution_validator": _adapter_run_execution_validator,
    "run_closure_audit": _adapter_run_closure_audit,
}

_RUNTIME_ADAPTER_META: Dict[str, Dict[str, str]] = {
    "export_operator_snapshot": {"adapter_name": "adapter.export_operator_snapshot", "invocation_mode": "direct_callable"},
    "run_abraxas_pipeline": {"adapter_name": "adapter.run_abraxas_pipeline", "invocation_mode": "direct_callable"},
    "run_abraxas_pipeline_review_path": {"adapter_name": "adapter.run_abraxas_pipeline_review_path", "invocation_mode": "direct_callable"},
    "run_closure_audit": {"adapter_name": "adapter.run_closure_audit", "invocation_mode": "subprocess_wrapper"},
    "run_compliance_probe": {"adapter_name": "adapter.run_compliance_probe", "invocation_mode": "subprocess_wrapper"},
    "run_execution_validator": {"adapter_name": "adapter.run_execution_validator", "invocation_mode": "direct_callable"},
    "run_generalized_coverage_probe": {"adapter_name": "adapter.run_compliance_probe", "invocation_mode": "subprocess_wrapper"},
}

_RUNTIME_SAFETY_NOTES: Dict[str, Dict[str, str]] = {
    "export_operator_snapshot": {
        "runs": "write operator snapshot artifact",
        "expected_outputs": "artifacts_seal/operator_snapshots/operator_snapshot.*.json",
        "scope_note": "Exports deterministic operator snapshot payload.",
        "does_not_do": "Does not execute runtime adapters or arbitrary commands.",
    },
    "run_abraxas_pipeline": {
        "runs": "canonical static pipeline: ingest -> parse(not_computable) -> map(not_computable) -> diff_validate -> review_audit",
        "expected_outputs": "artifacts_seal/abraxas_pipeline/*.pipeline.json + validator/audit artifacts",
        "scope_note": "Executes one deterministic bounded canonical Abraxas pipeline path only.",
        "does_not_do": "Does not author dynamic pipelines, call external APIs, or bypass runtime allowlist.",
    },
    "run_abraxas_pipeline_review_path": {
        "runs": "canonical static pipeline review path: ingest -> parse(not_computable) -> map(not_computable) -> review_audit",
        "expected_outputs": "artifacts_seal/abraxas_pipeline/*.pipeline.json + audit artifacts",
        "scope_note": "Executes second deterministic bounded canonical Abraxas pipeline path only.",
        "does_not_do": "Does not author dynamic pipelines, call external APIs, or bypass runtime allowlist.",
    },
    "run_closure_audit": {
        "runs": "python scripts/run_system_closure_audit.py",
        "expected_outputs": "artifacts_seal/audits/operator_closure_audit/closure_audit.*.json",
        "scope_note": "Runs deterministic closure audit report generation only.",
        "does_not_do": "Does not queue tasks, open sockets, or execute arbitrary user commands.",
    },
    "run_compliance_probe": {
        "runs": "python -m aal_core.runes.compliance_probe",
        "expected_outputs": "artifacts_seal/runs/compliance_probe/*.artifact.json",
        "scope_note": "Runs deterministic compliance probe only.",
        "does_not_do": "Does not execute non-allowlisted adapters or mutate hidden runtime state.",
    },
    "run_execution_validator": {
        "runs": "abx.execution_validator.validate_run + emit_validation_result",
        "expected_outputs": "out/validators/execution-validation-*.json",
        "scope_note": "Validates selected run evidence and emits canonical validator artifact.",
        "does_not_do": "Does not call external APIs or run background workers.",
    },
    "run_generalized_coverage_probe": {
        "runs": "python -m aal_core.runes.compliance_probe",
        "expected_outputs": "artifacts_seal/runs/compliance_probe/*.artifact.json",
        "scope_note": "Runs generalized coverage probe via bounded compliance path.",
        "does_not_do": "Does not broaden authority beyond compliance-probe command family.",
    },
}

_ERS_CANDIDATE_CATALOG: List[Dict[str, Any]] = [
    {"item_id": "ers.item.compliance_probe", "item_type": "task", "action_name": "run_compliance_probe", "priority": 10},
    {"item_id": "ers.item.generalized_coverage_probe", "item_type": "task", "action_name": "run_generalized_coverage_probe", "priority": 20},
    {"item_id": "ers.item.execution_validator", "item_type": "rune", "action_name": "run_execution_validator", "priority": 30},
    {"item_id": "ers.item.closure_audit", "item_type": "action", "action_name": "run_closure_audit", "priority": 40},
]

_ERS_QUEUE_LIMIT = 5
_ERS_REVIEW_LIMIT = 10
_RUNTIME_CORRIDOR_OUTPUT_LIMIT = 5
_RUNTIME_CORRIDOR_FAILURE_LIMIT = 5

_RUNTIME_CORRIDOR_REGISTRY: List[Dict[str, Any]] = [
    {
        "entry_id": "entry.runtime.pipeline.abraxas_canonical",
        "action_name": "run_abraxas_pipeline",
        "pipeline_id": _ABRAXAS_PIPELINE_ID,
        "rune_id": "RUNE.INGEST",
        "adapter_name": "adapter.run_abraxas_pipeline",
        "required_context": ["selected_run_id"],
        "expected_outputs": ["artifacts_seal/abraxas_pipeline/*.pipeline.json"],
        "allowlisted": True,
    },
    {
        "entry_id": "entry.runtime.pipeline.abraxas_review_path",
        "action_name": "run_abraxas_pipeline_review_path",
        "pipeline_id": _ABRAXAS_PIPELINE_REVIEW_PATH_ID,
        "rune_id": "RUNE.INGEST",
        "adapter_name": "adapter.run_abraxas_pipeline_review_path",
        "required_context": ["selected_run_id"],
        "expected_outputs": ["artifacts_seal/abraxas_pipeline/*.pipeline.json"],
        "allowlisted": True,
    },
    {
        "entry_id": "entry.runtime.ingest.compliance_probe",
        "action_name": "run_compliance_probe",
        "rune_id": "RUNE.INGEST",
        "adapter_name": "adapter.run_compliance_probe",
        "required_context": [],
        "expected_outputs": ["artifacts_seal/runs/compliance_probe/*.artifact.json"],
        "allowlisted": True,
    },
    {
        "entry_id": "entry.runtime.parse_diff.validator",
        "action_name": "run_execution_validator",
        "rune_id": "RUNE.VALIDATOR",
        "adapter_name": "adapter.run_execution_validator",
        "required_context": ["selected_run_id"],
        "expected_outputs": ["out/validators/execution-validation-*.json"],
        "allowlisted": True,
    },
    {
        "entry_id": "entry.runtime.audit.closure",
        "action_name": "run_closure_audit",
        "rune_id": "RUNE.AUDIT",
        "adapter_name": "adapter.run_closure_audit",
        "required_context": ["selected_run_id"],
        "expected_outputs": ["artifacts_seal/audits/operator_closure_audit/closure_audit.*.json"],
        "allowlisted": True,
    },
]


def _derive_runtime_entry_registry(*, allowed_actions: List[str]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for item in _RUNTIME_CORRIDOR_REGISTRY:
        action_name = str(item.get("action_name", ""))
        rows.append(
            {
                "entry_id": str(item.get("entry_id", "")),
                "action_name": action_name,
                "rune_id": str(item.get("rune_id", "NOT_COMPUTABLE")),
                "pipeline_id": str(item.get("pipeline_id", "")),
                "adapter_name": str(item.get("adapter_name", "")),
                "required_context": [str(x) for x in item.get("required_context", []) if isinstance(x, str)][:5],
                "expected_outputs": [str(x) for x in item.get("expected_outputs", []) if isinstance(x, str)][:5],
                "allowlisted": "true" if action_name in allowed_actions and bool(item.get("allowlisted", False)) else "false",
                "provenance": "operator_console.runtime_corridor.registry.v3.3.static_allowlisted",
            }
        )
    return rows[:10]


def _derive_runtime_gating(
    *,
    runtime_entry_registry: List[Dict[str, Any]],
    selected_run_id: Optional[str],
    policy_mode: str,
    preview_map: Mapping[str, Any],
    ers_queue: Mapping[str, Any],
) -> List[Dict[str, Any]]:
    runnable_items = ers_queue.get("runnable_items", []) if isinstance(ers_queue, Mapping) else []
    runnable_actions = {
        str(item.get("action_name", ""))
        for item in runnable_items
        if isinstance(item, Mapping) and str(item.get("action_name", ""))
    }
    rows: List[Dict[str, Any]] = []
    for entry in runtime_entry_registry:
        action_name = str(entry.get("action_name", ""))
        required_context = [str(x) for x in entry.get("required_context", []) if isinstance(x, str)]
        policy_permits = policy_mode in {"bounded_runtime", "decision_review", "review_only"}
        allowlisted = str(entry.get("allowlisted", "false")) == "true"
        context_ok = all(bool(selected_run_id) if field == "selected_run_id" else True for field in required_context)
        adapter_supported = action_name in _RUNTIME_ADAPTER_META and action_name in _RUNTIME_ADAPTERS
        preview_supported = action_name in preview_map
        ers_required = action_name in {"run_execution_validator", "run_closure_audit"}
        ers_ready = (action_name in runnable_actions) if ers_required else True
        if not policy_permits:
            gating_reason = "policy_mode_blocks_entry"
            invokable = False
        elif not allowlisted:
            gating_reason = "entry_not_allowlisted"
            invokable = False
        elif not context_ok:
            gating_reason = "required_context_missing"
            invokable = False
        elif not adapter_supported:
            gating_reason = "adapter_not_supported"
            invokable = False
        elif not preview_supported:
            gating_reason = "preview_not_supported"
            invokable = False
        elif not ers_ready:
            gating_reason = "ers_context_blocks_entry"
            invokable = False
        else:
            gating_reason = "all_conditions_pass"
            invokable = True
        rows.append(
            {
                "entry_id": str(entry.get("entry_id", "")),
                "action_name": action_name,
                "invokable": "true" if invokable else "false",
                "blocked": "false" if invokable else "true",
                "gating_reason": gating_reason,
                "required_conditions": [
                    "policy_mode_permits_entry",
                    "entry_allowlisted",
                    "required_context_present",
                    "adapter_supported",
                    "preview_supported",
                    "ers_context_ready_if_required",
                ],
                "policy_context": {"policy_mode": policy_mode},
                "ers_context": {"required": "true" if ers_required else "false", "ready": "true" if ers_ready else "false"},
                "provenance": "operator_console.runtime_corridor.gating.v3.3.ordered_rules",
            }
        )
    return rows[:10]


def _derive_runtime_invocation_envelope(
    *,
    last_action: Mapping[str, Any] | None,
    selected_run_id: Optional[str],
) -> Dict[str, Any]:
    source = dict(last_action or {})
    artifact_path = str(source.get("artifact_path", ""))
    action_name = str(source.get("action_name", "")) or "NOT_COMPUTABLE"
    explicit_run_id = str(source.get("triggered_run_id", "") or source.get("run_id", "")).strip()
    selected_id = str(selected_run_id or "").strip()
    invocation_run_id = explicit_run_id or selected_id or "NOT_COMPUTABLE"
    if explicit_run_id:
        run_id_source = "action_history"
    elif selected_id:
        run_id_source = "selected_run_id"
    else:
        run_id_source = "none"
    run_id_status = "PRESENT" if invocation_run_id != "NOT_COMPUTABLE" else "MISSING"
    inferred_pipeline_id = str(source.get("pipeline_id", "")).strip()
    if not inferred_pipeline_id:
        if action_name == "run_abraxas_pipeline":
            inferred_pipeline_id = _ABRAXAS_PIPELINE_ID
        elif action_name == "run_abraxas_pipeline_review_path":
            inferred_pipeline_id = _ABRAXAS_PIPELINE_REVIEW_PATH_ID
    if not inferred_pipeline_id:
        inferred_pipeline_id = "NOT_COMPUTABLE"
    return {
        "action_name": action_name,
        "entry_id": str(source.get("entry_id", "")) or "NOT_COMPUTABLE",
        "rune_id": str(source.get("rune_id", "")) or "NOT_COMPUTABLE",
        "adapter_name": str(source.get("adapter_name", "")) or "NOT_COMPUTABLE",
        "attempted_at": str(source.get("attempted_at", "")) or "NOT_COMPUTABLE",
        "run_id": invocation_run_id,
        "pipeline_id": inferred_pipeline_id,
        "invocation_run_id": invocation_run_id,
        "invocation_run_id_source": run_id_source,
        "invocation_run_id_status": run_id_status,
        "payload_summary": {
            "selected_run_id": str(selected_run_id or ""),
            "preset_id": str(source.get("preset_id", "")),
        },
        "artifact_paths": [artifact_path] if artifact_path else [],
        "result_path": artifact_path or "",
        "outcome_status": str(source.get("outcome_status", source.get("status", "NOT_COMPUTABLE"))),
        "provenance": "operator_console.runtime_corridor.invocation.v3.3.action_history_projection",
        "ledger_record_ids": [],
        "ledger_artifact_ids": [],
        "correlation_pointers": [],
    }


def _derive_runtime_state_surface(
    *,
    invocation_envelope: Mapping[str, Any],
    execution_ledger: List[Dict[str, str]],
) -> Dict[str, Any]:
    outputs: List[Dict[str, str]] = []
    failures: List[Dict[str, str]] = []
    for row in execution_ledger:
        status = str(row.get("outcome_status", ""))
        summary = {
            "timestamp": str(row.get("timestamp", "NOT_COMPUTABLE")),
            "action_name": str(row.get("action_name", "")),
            "run_id": str(row.get("run_id", "")),
            "outcome_status": status,
            "artifact_ref": str(row.get("artifact_ref", "")),
        }
        if status == "SUCCESS":
            outputs.append(summary)
        elif status:
            failures.append(summary)
    latest_status = str(invocation_envelope.get("outcome_status", "NOT_COMPUTABLE"))
    latest_run_id = str(invocation_envelope.get("run_id", "NOT_COMPUTABLE"))
    return {
        "latest_runtime_invocation": dict(invocation_envelope),
        "latest_runtime_run_id": latest_run_id,
        "latest_runtime_status": latest_status,
        "recent_runtime_outputs": outputs[:_RUNTIME_CORRIDOR_OUTPUT_LIMIT],
        "recent_runtime_failures": failures[:_RUNTIME_CORRIDOR_FAILURE_LIMIT],
        "runtime_state_summary": f"status={latest_status}|run_id={latest_run_id}|outputs={len(outputs)}|failures={len(failures)}",
        "provenance": "operator_console.runtime_corridor.state.v3.3.execution_ledger_projection",
    }


def _derive_runtime_workspace_payload(
    *,
    selected_run_id: Optional[str],
    invocation_envelope: Mapping[str, Any],
    export_status: str,
    export_path: Optional[str],
) -> Dict[str, Any]:
    run_id = str(invocation_envelope.get("run_id", "") or selected_run_id or "")
    return {
        "mode": "runtime",
        "focus_run_id": run_id,
        "focus_run_link": f"/operator?run_id={run_id}" if run_id else "",
        "latest_outcome_status": str(invocation_envelope.get("outcome_status", "NOT_COMPUTABLE")),
        "runtime_export_status": export_status,
        "runtime_export_path": export_path or "",
    }


def _derive_pipeline_step_audit(
    *,
    step_records: List[Mapping[str, Any]],
) -> List[Dict[str, str]]:
    callable_actions = {
        str(step.get("step_name", "")): str(step.get("action_name", ""))
        for step in _ABRAXAS_PIPELINE_STEP_CATALOG
    }
    rows: List[Dict[str, str]] = []
    for step in step_records[:10]:
        step_name = str(step.get("step_name", ""))
        status = str(step.get("status", "NOT_COMPUTABLE"))
        action_name = callable_actions.get(step_name, "NOT_COMPUTABLE")
        callable_exposed = action_name in _RUNTIME_ADAPTERS or action_name in {"pipeline_parse_projection", "pipeline_map_projection"}
        artifact_emitted = bool(str(step.get("artifact_ref", "")))
        if not callable_exposed:
            blocking_reason = "adapter_not_exposed_in_runtime_corridor"
        elif status in {"FAILED", "SKIPPED"}:
            blocking_reason = "execution_degraded_or_blocked"
        elif not artifact_emitted and status == "SUCCESS":
            blocking_reason = "artifact_missing_for_success_state"
        elif status == "NOT_COMPUTABLE":
            blocking_reason = "step_not_computable_in_current_context"
        else:
            blocking_reason = ""
        rows.append(
            {
                "step_name": step_name,
                "rune_id": str(step.get("rune_id", "NOT_COMPUTABLE")),
                "callable_exposed": "true" if callable_exposed else "false",
                "artifact_emitted": "true" if artifact_emitted else "false",
                "current_status_quality": status,
                "blocking_reason": blocking_reason,
                "provenance": "pipeline_hardening.step_audit.v3.5.callable_and_execution_derived",
            }
        )
    return rows[:10]


def _derive_pipeline_quality_matrix(*, pipeline_step_audit: List[Mapping[str, Any]]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for step in pipeline_step_audit[:10]:
        callable_exposed = str(step.get("callable_exposed", "false")) == "true"
        artifact_emitted = str(step.get("artifact_emitted", "false")) == "true"
        status = str(step.get("current_status_quality", "NOT_COMPUTABLE"))
        if callable_exposed and status in {"SUCCESS", "VALID"} and (artifact_emitted or str(step.get("step_name", "")) == "ingest"):
            label = "EXECUTABLE"
        elif callable_exposed and status in {"FAILED", "SKIPPED"}:
            label = "DEGRADED"
        elif status == "NOT_COMPUTABLE":
            label = "NOT_COMPUTABLE"
        elif not callable_exposed:
            label = "STRUCTURAL_ONLY"
        else:
            label = "DEGRADED"
        rows.append(
            {
                "step_name": str(step.get("step_name", "")),
                "quality_label": label,
                "quality_reason": f"callable={step.get('callable_exposed','false')}|status={status}|artifact={step.get('artifact_emitted','false')}",
                "provenance": "pipeline_hardening.quality_matrix.v3.5.explicit_rules",
            }
        )
    return rows[:10]


def _select_pipeline_upgrade_targets(
    *,
    pipeline_quality_matrix: List[Mapping[str, Any]],
    pipeline_step_audit: List[Mapping[str, Any]],
) -> Dict[str, str]:
    quality_by_step = {str(row.get("step_name", "")): str(row.get("quality_label", "")) for row in pipeline_quality_matrix}
    callable_by_step = {str(row.get("step_name", "")): str(row.get("callable_exposed", "false")) == "true" for row in pipeline_step_audit}
    ordered_candidates = ["parse", "map", "diff_validate", "review_audit", "ingest"]
    priority_pool = [name for name in ordered_candidates if quality_by_step.get(name, "") in {"STRUCTURAL_ONLY", "DEGRADED", "NOT_COMPUTABLE"}]
    callable_pool = [name for name in priority_pool if callable_by_step.get(name, False)]
    primary = callable_pool[0] if callable_pool else (priority_pool[0] if priority_pool else "none")
    secondary = ""
    if primary == "parse" and "map" in priority_pool:
        secondary = "map"
    reason = (
        "prefer semantic-central degraded/not-computable steps with immediate callable upgrade path"
        if primary != "none"
        else "all steps are healthy or non-actionable under bounded rules"
    )
    return {
        "primary_upgrade_target": primary,
        "secondary_upgrade_target": secondary,
        "upgrade_reason": reason,
    }


def _derive_ers_integration(
    *,
    workbench_mode: str,
    selected_run_id: Optional[str],
    policy_mode: str,
    control_plane: Mapping[str, Any],
    action_gating: List[Dict[str, Any]],
    action_history: List[Dict[str, Any]],
    latest_result_packet: Mapping[str, Any],
    latest_snapshot_path: Optional[str],
    latest_snapshot_status: str,
) -> Dict[str, Any]:
    allowed_actions = {str(x) for x in control_plane.get("allowed_actions", []) if isinstance(x, str)}
    gating_index = {str(row.get("action_name", "")): row for row in action_gating}
    recently_completed_ids: List[str] = []
    for row in action_history[:20]:
        action_name = str(row.get("action_name", ""))
        status = str(row.get("outcome_status", "")).upper()
        item = next((candidate for candidate in _ERS_CANDIDATE_CATALOG if candidate["action_name"] == action_name), None)
        if item and status in {"SUCCESS", "VALID"}:
            recently_completed_ids.append(str(item["item_id"]))

    items: List[Dict[str, Any]] = []
    for candidate in _ERS_CANDIDATE_CATALOG:
        action_name = str(candidate["action_name"])
        gate = gating_index.get(action_name, {})
        required_conditions = [
            {"condition": "item_allowlisted", "passed": action_name in allowed_actions},
            {"condition": "policy_permits_trigger", "passed": str(gate.get("policy_permits", "false")) == "true"},
            {"condition": "selected_run_required", "passed": bool(selected_run_id) if action_name == "run_execution_validator" else True},
            {"condition": "preview_supported_or_not_required", "passed": str(gate.get("preview_supported", "false")) == "true"},
        ]
        first_failed = next((row["condition"] for row in required_conditions if not bool(row["passed"])), "")
        eligible = first_failed == "" and str(gate.get("enabled", "false")) == "true"
        gating_reason = "eligible" if eligible else (first_failed or str(gate.get("reason_code", "blocked_by_policy")))
        item = {
            "item_id": str(candidate["item_id"]),
            "item_type": str(candidate["item_type"]),
            "action_name": action_name,
            "priority": int(candidate["priority"]),
            "eligible": eligible,
            "blocked": not eligible,
            "gating_reason": gating_reason,
            "required_conditions": required_conditions,
            "policy_context": {
                "policy_mode": policy_mode,
                "policy_permits": str(gate.get("policy_permits", "false")),
                "rule_source": "ERS.GATE.v3.1",
            },
        }
        items.append(item)

    ordered = sorted(items, key=lambda row: (int(row.get("priority", 999)), str(row.get("item_id", ""))))
    runnable = [row for row in ordered if bool(row.get("eligible", False))]
    blocked = [row for row in ordered if not bool(row.get("eligible", False))]
    next_runnable = dict(runnable[0]) if runnable else {
        "item_id": "NOT_COMPUTABLE",
        "gating_reason": "no_eligible_items",
        "rule_source": "ERS.ORDER.v1",
    }
    reasoning = [
        {
            "item_id": str(row["item_id"]),
            "why_next": (
                f"next by priority={row['priority']} then item_id asc"
                if runnable and str(runnable[0]["item_id"]) == str(row["item_id"])
                else "not_selected_for_next"
            ),
            "why_blocked": "not_blocked" if bool(row.get("eligible", False)) else str(row.get("gating_reason", "blocked")),
            "rule_or_policy": "ERS.ORDER.v1 + ERS.GATE.v3.1",
            "priority_explanation": f"priority={row['priority']}; tie_break=item_id_asc",
        }
        for row in ordered[: (_ERS_QUEUE_LIMIT * 2)]
    ]
    ers_state_surface = {
        "ers_mode": "manual_explicit_trigger_only",
        "queue_length": len(ordered),
        "runnable_count": len(runnable),
        "blocked_count": len(blocked),
        "recently_completed_count": len(recently_completed_ids[:_ERS_QUEUE_LIMIT]),
        "scheduler_summary": "deterministic_priority_then_item_id; explicit_trigger_only; no_auto_advance",
    }
    ers_queue = {
        "next_runnable_item": next_runnable,
        "runnable_items": runnable[:_ERS_QUEUE_LIMIT],
        "blocked_items": blocked[:_ERS_QUEUE_LIMIT],
        "trigger_rule": "operator_explicit_trigger_only; eligible_only; no_background_progression",
    }
    ers_snapshot_preview = {
        "ers_state_surface": ers_state_surface,
        "next_runnable_item": next_runnable,
        "runnable_items": runnable[:_ERS_QUEUE_LIMIT],
        "blocked_items": blocked[:_ERS_QUEUE_LIMIT],
        "eligibility_summary": [{"item_id": row["item_id"], "eligible": row["eligible"], "gating_reason": row["gating_reason"]} for row in ordered],
        "scheduling_reasoning": reasoning,
        "governance_context": {"policy_mode": policy_mode, "workbench_mode": workbench_mode},
        "timestamp": _utc_now(),
    }
    ers_workspace_payload = {
        "mode": "ers",
        "next_runnable_item_id": str(next_runnable.get("item_id", "NOT_COMPUTABLE")),
        "runnable_count": len(runnable),
        "blocked_count": len(blocked),
        "snapshot_status": latest_snapshot_status,
    }
    return {
        "ers_state_surface": ers_state_surface,
        "ers_queue": ers_queue,
        "ers_blocked_items": blocked[:_ERS_QUEUE_LIMIT],
        "ers_reasoning": reasoning,
        "ers_snapshot_preview": ers_snapshot_preview,
        "ers_snapshot_status": latest_snapshot_status,
        "ers_snapshot_path": latest_snapshot_path,
        "ers_workspace_payload": ers_workspace_payload,
        "latest_result_packet": dict(latest_result_packet),
        "catalog_rule": "static_catalog.v1.small_safe_set",
    }


def _load_prior_ers_snapshot(*, base_dir: Path) -> Optional[Dict[str, Any]]:
    root = base_dir / "artifacts_seal" / "operator_ers"
    if not root.exists():
        return None
    paths = sorted(root.glob("*.ers_snapshot.json"), key=lambda p: p.name, reverse=True)
    for path in paths:
        payload = _load_json(path)
        if isinstance(payload, dict):
            payload["_path"] = path.as_posix()
            return payload
    return None


def _derive_ers_snapshot_diff(
    *,
    current_snapshot: Mapping[str, Any],
    prior_snapshot: Optional[Mapping[str, Any]],
) -> Dict[str, Any]:
    if not isinstance(prior_snapshot, Mapping):
        return {
            "status": "NOT_COMPUTABLE",
            "reason": "prior_snapshot_unavailable",
            "prior_snapshot_path": "",
            "queue_length_change": "unavailable",
            "runnable_count_change": "unavailable",
            "blocked_count_change": "unavailable",
            "next_runnable_item_change": "unavailable",
            "item_diffs": [],
            "changed_items": [],
        }

    current_state = dict(current_snapshot.get("ers_state_surface", {}))
    prior_state = dict(prior_snapshot.get("ers_state_surface", {}))
    current_next = str((((current_snapshot.get("ers_queue", {}) or {}).get("next_runnable_item", {}) or {}).get("item_id", "NOT_COMPUTABLE")))
    prior_next = str(prior_snapshot.get("next_runnable_item", "") or (((prior_snapshot.get("ers_queue", {}) or {}).get("next_runnable_item", {}) or {}).get("item_id", "NOT_COMPUTABLE"))
                     or "NOT_COMPUTABLE")

    current_runnable = {str(row.get("item_id", "")) for row in current_snapshot.get("runnable_items", []) if isinstance(row, Mapping)}
    current_blocked = {str(row.get("item_id", "")) for row in current_snapshot.get("blocked_items", []) if isinstance(row, Mapping)}
    prior_runnable = {str(row.get("item_id", "")) for row in prior_snapshot.get("runnable_items", []) if isinstance(row, Mapping)}
    prior_blocked = {str(row.get("item_id", "")) for row in prior_snapshot.get("blocked_items", []) if isinstance(row, Mapping)}

    all_items = sorted((current_runnable | current_blocked | prior_runnable | prior_blocked))
    diffs: List[Dict[str, str]] = []
    for item_id in all_items:
        if item_id in current_runnable and item_id in prior_blocked:
            transition_type = "entered_runnable"
        elif item_id in current_blocked and item_id in prior_runnable:
            transition_type = "entered_blocked"
        elif item_id not in current_runnable and item_id not in current_blocked and (item_id in prior_runnable or item_id in prior_blocked):
            transition_type = "removed_from_queue"
        elif item_id in current_runnable and item_id not in prior_runnable and item_id not in prior_blocked:
            transition_type = "entered_runnable"
        elif item_id in current_blocked and item_id not in prior_runnable and item_id not in prior_blocked:
            transition_type = "entered_blocked"
        else:
            transition_type = "unchanged"
        diffs.append({"item_id": item_id, "transition_type": transition_type})

    precedence = {"entered_runnable": 0, "entered_blocked": 1, "removed_from_queue": 2, "unchanged": 3}
    diffs = sorted(diffs, key=lambda row: (precedence.get(str(row.get("transition_type", "")), 9), str(row.get("item_id", ""))))[:_ERS_REVIEW_LIMIT]
    changed = [row for row in diffs if str(row.get("transition_type", "")) != "unchanged"]

    queue_changed = "changed" if int(current_state.get("queue_length", -1)) != int(prior_state.get("queue_length", -1)) else "unchanged"
    runnable_changed = "changed" if int(current_state.get("runnable_count", -1)) != int(prior_state.get("runnable_count", -1)) else "unchanged"
    blocked_changed = "changed" if int(current_state.get("blocked_count", -1)) != int(prior_state.get("blocked_count", -1)) else "unchanged"
    next_changed = "changed" if current_next != prior_next else "unchanged"
    return {
        "status": "available",
        "reason": "compared_with_latest_prior_snapshot",
        "prior_snapshot_path": str(prior_snapshot.get("_path", "")),
        "queue_length_change": queue_changed,
        "runnable_count_change": runnable_changed,
        "blocked_count_change": blocked_changed,
        "next_runnable_item_change": next_changed,
        "current_next_runnable_item": current_next,
        "prior_next_runnable_item": prior_next,
        "item_diffs": diffs,
        "changed_items": changed,
    }


def _derive_ers_drift_summary(*, diff: Mapping[str, Any], current_snapshot: Mapping[str, Any], prior_snapshot: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    if str(diff.get("status", "")) != "available" or not isinstance(prior_snapshot, Mapping):
        return {"label": "NOT_COMPUTABLE", "reason_codes": ["prior_snapshot_unavailable"], "rule_source": "ERS.DRIFT.v1"}
    current_state = dict(current_snapshot.get("ers_state_surface", {}))
    prior_state = dict(prior_snapshot.get("ers_state_surface", {}))
    blocked_delta = int(current_state.get("blocked_count", 0)) - int(prior_state.get("blocked_count", 0))
    runnable_delta = int(current_state.get("runnable_count", 0)) - int(prior_state.get("runnable_count", 0))
    next_changed = str(diff.get("next_runnable_item_change", "unchanged")) == "changed"
    if blocked_delta > 0 or runnable_delta < 0 or (next_changed and str(diff.get("current_next_runnable_item", "")) == "NOT_COMPUTABLE"):
        return {"label": "DEGRADED", "reason_codes": ["blocked_up_or_runnable_down_or_next_regressed"], "rule_source": "ERS.DRIFT.v1"}
    if str(diff.get("queue_length_change", "unchanged")) == "unchanged" and str(diff.get("runnable_count_change", "unchanged")) == "unchanged" and str(diff.get("blocked_count_change", "unchanged")) == "unchanged" and not bool(diff.get("changed_items", [])):
        return {"label": "STABLE", "reason_codes": ["composition_and_balance_unchanged"], "rule_source": "ERS.DRIFT.v1"}
    return {"label": "SHIFTED", "reason_codes": ["queue_membership_or_order_changed"], "rule_source": "ERS.DRIFT.v1"}


def _derive_ers_runtime_handoff(*, action_history: List[Dict[str, Any]], result_packet: Mapping[str, Any]) -> Dict[str, Any]:
    latest = next((row for row in action_history if str(row.get("preset_id", "")).startswith("ers.")), None)
    if latest is None:
        return {
            "status": "NOT_COMPUTABLE",
            "triggered_ers_item_id": "",
            "action_name": "",
            "run_id": "",
            "result_status": "NOT_COMPUTABLE",
            "focus_target": "",
            "summary": "No ERS-triggered action in local history.",
        }
    ers_item_id = str(latest.get("preset_id", "")).replace("ers.", "", 1)
    run_id = str(latest.get("run_id", "") or result_packet.get("run_id", ""))
    return {
        "status": "available",
        "triggered_ers_item_id": ers_item_id,
        "action_name": str(latest.get("action_name", "")),
        "run_id": run_id,
        "result_status": str(latest.get("outcome_status", result_packet.get("status", "NOT_COMPUTABLE"))),
        "focus_target": f"/operator?mode=runflow&run_id={run_id}" if run_id else "/operator?mode=runflow",
        "summary": f"{latest.get('action_name','')} -> run={run_id or 'UNAVAILABLE'} status={latest.get('outcome_status','UNKNOWN')}",
    }


def _derive_ers_transition_log(
    *,
    diff: Mapping[str, Any],
    action_history: List[Dict[str, Any]],
) -> List[Dict[str, str]]:
    entries: List[Dict[str, str]] = []
    now = _utc_now()
    for row in diff.get("changed_items", []):
        if not isinstance(row, Mapping):
            continue
        transition_type = str(row.get("transition_type", ""))
        if transition_type not in {"entered_runnable", "entered_blocked", "removed_from_queue"}:
            continue
        entries.append(
            {
                "timestamp": now,
                "item_id": str(row.get("item_id", "")),
                "transition_type": transition_type,
                "summary": f"{row.get('item_id','')} {transition_type.replace('_', ' ')} via snapshot diff",
                "source": "diff",
            }
        )
    for row in action_history[:20]:
        preset_id = str(row.get("preset_id", ""))
        if not preset_id.startswith("ers."):
            continue
        entries.append(
            {
                "timestamp": str(row.get("timestamp", "NOT_COMPUTABLE")),
                "item_id": preset_id.replace("ers.", "", 1),
                "transition_type": "triggered",
                "summary": str(row.get("summary", "")) or "triggered by operator",
                "source": "trigger_history",
            }
        )
    entries.sort(key=lambda row: (str(row.get("timestamp", "")), str(row.get("item_id", "")), str(row.get("transition_type", ""))), reverse=True)
    return entries[:_ERS_REVIEW_LIMIT]


def execute_runtime_adapter(*, action_name: str, payload: Mapping[str, Any], allowed_actions: List[str]) -> Dict[str, Any]:
    attempted_at = _utc_now()
    if action_name not in allowed_actions:
        return {
            "adapter_name": "",
            "attempted_at": attempted_at,
            "outcome_status": "FAILED",
            "run_id": "",
            "artifact_paths": [],
            "summary": f"action blocked: {action_name} not allowed",
            "error_info": "action_not_allowed",
        }
    adapter = _RUNTIME_ADAPTERS.get(action_name)
    if adapter is None:
        return {
            "adapter_name": "",
            "attempted_at": attempted_at,
            "outcome_status": "FAILED",
            "run_id": "",
            "artifact_paths": [],
            "summary": f"adapter unavailable for {action_name}",
            "error_info": "adapter_not_found",
        }
    try:
        response = adapter(payload)
    except Exception as exc:  # deterministic conversion to packet
        return {
            "adapter_name": str(getattr(adapter, "__name__", "")),
            "attempted_at": attempted_at,
            "outcome_status": "FAILED",
            "run_id": "",
            "artifact_paths": [],
            "summary": f"adapter execution failed for {action_name}",
            "error_info": str(exc),
        }
    response_packet = {
        "adapter_name": str(response.get("adapter_name", getattr(adapter, "__name__", ""))),
        "attempted_at": str(response.get("attempted_at", attempted_at)),
        "outcome_status": str(response.get("outcome_status", "FAILED")),
        "run_id": str(response.get("run_id", "")),
        "artifact_paths": [str(x) for x in response.get("artifact_paths", [])[:5]],
        "summary": str(response.get("summary", "")),
        "error_info": str(response.get("error_info", "")),
    }
    for key in ["pipeline_id", "pipeline_envelope", "pipeline_step_records", "pipeline_state_surface"]:
        if key in response:
            response_packet[key] = response[key]
    return response_packet


def _build_run_health_summaries(*, run_ids: List[str], artifacts: List[Dict[str, Any]], validators: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    summaries: List[Dict[str, Any]] = []
    for run_id in run_ids:
        detail = _build_selected_run_detail(run_id, artifacts, validators)
        summaries.append(
            {
                "run_id": run_id,
                "artifact_status": detail["artifact_status"],
                "validator_status": detail["validator_status"],
                "correlation_pointers_count": detail["correlation_pointers_count"],
                "latest_timestamp": detail["latest_timestamp"],
                "health_label": detail["health_label"],
            }
        )
    return summaries


def _sanitize_health_filter(value: Optional[str]) -> str:
    allowed = {"all", "strong", "partial", "weak"}
    return str(value) if value in allowed else "all"


def _sanitize_sort_mode(value: Optional[str]) -> str:
    return "run_id_asc" if value == "run_id_asc" else "latest_first"


def _filter_and_sort_run_summaries(rows: List[Dict[str, Any]], *, health_filter: str, run_query: str, sort_mode: str) -> List[Dict[str, Any]]:
    out = list(rows)

    if health_filter != "all":
        out = [row for row in out if row.get("health_label") == health_filter]

    normalized_query = run_query.strip().lower()
    if normalized_query:
        out = [row for row in out if normalized_query in str(row.get("run_id", "")).lower()]

    if sort_mode == "run_id_asc":
        out.sort(key=lambda row: str(row.get("run_id", "")))
    else:
        with_ts = [row for row in out if str(row.get("latest_timestamp", "NOT_COMPUTABLE")) != "NOT_COMPUTABLE"]
        without_ts = [row for row in out if str(row.get("latest_timestamp", "NOT_COMPUTABLE")) == "NOT_COMPUTABLE"]
        with_ts.sort(key=lambda row: (str(row.get("latest_timestamp", "")), str(row.get("run_id", ""))), reverse=True)
        without_ts.sort(key=lambda row: str(row.get("run_id", "")))
        out = with_ts + without_ts

    return out


def _extract_run_id_from_action_result(action_result: Mapping[str, Any]) -> Optional[str]:
    stdout_tail = str(action_result.get("stdout_tail", ""))
    stderr_tail = str(action_result.get("stderr_tail", ""))
    combined = "\n".join([stdout_tail, stderr_tail])
    match = re.search(r"([A-Za-z0-9_.-]+)\.artifact\.json", combined)
    if match:
        return match.group(1)
    return None


def build_last_action_feedback(action_result: Mapping[str, Any]) -> Dict[str, Any]:
    exit_code = int(action_result.get("exit_code", 1))
    attempted_at = str(action_result.get("timestamp_utc", _utc_now()))
    action_name = "run_compliance_probe"
    triggered_run_id = _extract_run_id_from_action_result(action_result)

    if exit_code == 0:
        outcome_status = "SUCCESS"
        message = (
            f"compliance probe completed for {triggered_run_id}"
            if triggered_run_id
            else "compliance probe completed; run_id unavailable"
        )
    else:
        stderr_tail = str(action_result.get("stderr_tail", ""))
        if "permission" in stderr_tail.lower() or "not found" in stderr_tail.lower():
            outcome_status = "ENV_LIMITED"
            message = "compliance probe not computable in current environment"
        else:
            outcome_status = "FAILED"
            message = "compliance probe failed; inspect stderr"

    return {
        "action_name": action_name,
        "attempted_at": attempted_at,
        "outcome_status": outcome_status,
        "triggered_run_id": triggered_run_id,
        "message": message,
        "raw_exit_code": exit_code,
    }




def _recent_activity_from_artifacts(artifacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for record in artifacts:
        ts = record.get("timestamp") or "NOT_COMPUTABLE"
        run_id = str(record.get("run_id", "")) or None
        status = str(record.get("status", "MISSING"))
        items.append(
            {
                "timestamp": ts,
                "activity_type": "artifact",
                "run_id": run_id,
                "summary": f"artifact status={status}",
                "source_path": str(record.get("path", "")),
            }
        )
    return items


def _recent_activity_from_validators(validators: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for record in validators:
        ts = record.get("timestamp") or "NOT_COMPUTABLE"
        run_id = str(record.get("run_id", "")) or None
        status = str(record.get("status", "MISSING"))
        pointers = int(record.get("pointers_count", 0))
        items.append(
            {
                "timestamp": ts,
                "activity_type": "validator",
                "run_id": run_id,
                "summary": f"validator status={status}; pointers={pointers}",
                "source_path": str(record.get("path", "")),
            }
        )
    return items


def _recent_activity_from_last_action(last_action: Optional[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    if last_action is None:
        return []
    ts = str(last_action.get("attempted_at", "NOT_COMPUTABLE"))
    return [
        {
            "timestamp": ts,
            "activity_type": "action",
            "run_id": last_action.get("triggered_run_id"),
            "summary": str(last_action.get("message", "")),
            "source_path": "operator://last_action",
        }
    ]


def _build_recent_activity(
    *,
    artifacts: List[Dict[str, Any]],
    validators: List[Dict[str, Any]],
    last_action: Optional[Mapping[str, Any]],
    limit: int,
) -> List[Dict[str, Any]]:
    items = _recent_activity_from_artifacts(artifacts)
    items.extend(_recent_activity_from_validators(validators))
    items.extend(_recent_activity_from_last_action(last_action))

    type_rank = {"action": 0, "artifact": 1, "validator": 2}

    # newest first for real timestamps, stable deterministic tie-breaks
    with_ts = [x for x in items if str(x.get("timestamp", "NOT_COMPUTABLE")) != "NOT_COMPUTABLE"]
    without_ts = [x for x in items if str(x.get("timestamp", "NOT_COMPUTABLE")) == "NOT_COMPUTABLE"]

    with_ts.sort(
        key=lambda item: (
            str(item.get("timestamp", "")),
            -type_rank.get(str(item.get("activity_type", "validator")), 9),
            str(item.get("run_id", "")),
            str(item.get("summary", "")),
        ),
        reverse=True,
    )
    without_ts.sort(
        key=lambda item: (
            type_rank.get(str(item.get("activity_type", "validator")), 9),
            str(item.get("run_id", "")),
            str(item.get("summary", "")),
        )
    )

    return (with_ts + without_ts)[:limit]




def _compute_suggested_focus(visible_summaries: List[Dict[str, Any]], visible_run_ids: List[str]) -> tuple[Optional[str], str]:
    if not visible_summaries:
        return None, "no_visible_runs"

    preferred = [
        row
        for row in visible_summaries
        if str(row.get("validator_status", "")).upper() in {"SUCCESS", "VALID"}
        and int(row.get("correlation_pointers_count", 0)) > 0
    ]

    if preferred:
        preferred.sort(
            key=lambda row: (
                str(row.get("latest_timestamp", "NOT_COMPUTABLE")),
                str(row.get("run_id", "")),
            ),
            reverse=True,
        )
        return str(preferred[0].get("run_id", "")) or None, "validator_success_with_pointers_latest"

    return (visible_run_ids[0] if visible_run_ids else None), "fallback_first_visible_run"


def _result_packet_artifact_paths(packet: Mapping[str, Any]) -> List[str]:
    paths = [str(x) for x in packet.get("artifact_paths", []) if isinstance(x, str) and str(x)]
    if not paths and str(packet.get("artifact_path", "")):
        paths = [str(packet.get("artifact_path", ""))]
    return paths[:5]


def _classify_outcome(packet: Mapping[str, Any]) -> Dict[str, str]:
    status = str(packet.get("status", "")).upper()
    run_id = str(packet.get("run_id", "")).strip()
    artifact_paths = _result_packet_artifact_paths(packet)
    error_info = str(packet.get("error_info", "")).strip()

    if status in {"NOT_COMPUTABLE", "NOT_REQUESTED", "PREVIEW_ONLY"}:
        return {"label": "NOT_COMPUTABLE", "reason_code": "status_not_computable_or_preview"}
    if status in {"FAILED", "ERROR"}:
        return {"label": "FAILED", "reason_code": "explicit_failed_status"}
    if error_info and not artifact_paths:
        return {"label": "FAILED", "reason_code": "error_info_without_artifact"}
    if status in {"SUCCESS", "VALID"} and run_id and artifact_paths:
        return {"label": "SUCCESS", "reason_code": "success_with_run_and_artifact"}
    if status in {"SUCCESS", "VALID", "PARTIAL"}:
        return {"label": "PARTIAL", "reason_code": "incomplete_success_surfaces"}
    if not run_id and not artifact_paths:
        return {"label": "NOT_COMPUTABLE", "reason_code": "missing_run_and_artifact"}
    return {"label": "NOT_COMPUTABLE", "reason_code": "fallback_not_computable"}


def _find_prior_result(
    *,
    packet: Mapping[str, Any],
    normalized_action_history_all: List[Dict[str, str]],
) -> Optional[Dict[str, str]]:
    action_name = str(packet.get("action_name", ""))
    preset_id = str(packet.get("preset_id", ""))
    packet_timestamp = str(packet.get("attempted_at", ""))
    packet_run_id = str(packet.get("run_id", ""))
    packet_status = str(packet.get("status", ""))
    packet_artifact_primary = _result_packet_artifact_paths(packet)[0] if _result_packet_artifact_paths(packet) else ""
    for item in normalized_action_history_all:
        if str(item.get("action_name", "")) != action_name:
            continue
        if str(item.get("preset_id", "")) != preset_id:
            continue
        same_identity = (
            str(item.get("timestamp", "")) == packet_timestamp
            and str(item.get("run_id", "")) == packet_run_id
            and str(item.get("outcome_status", "")) == packet_status
            and str(item.get("artifact_ref", "")) == packet_artifact_primary
        )
        if same_identity:
            continue
        return item
    return None


def _derive_prior_result_diff(
    *,
    packet: Mapping[str, Any],
    outcome_classification: Mapping[str, str],
    prior_result: Optional[Mapping[str, str]],
) -> Dict[str, Any]:
    if prior_result is None:
        return {
            "has_prior": False,
            "prior_timestamp": "NOT_COMPUTABLE",
            "outcome_change": "unchanged",
            "run_id_change": "unchanged",
            "artifact_path_change": "unchanged",
            "output_count_delta": "not_available",
            "error_change": "unchanged",
        }

    current_label = str(outcome_classification.get("label", "NOT_COMPUTABLE"))
    prior_label = _classify_outcome(
        {
            "status": str(prior_result.get("outcome_status", "")),
            "run_id": str(prior_result.get("run_id", "")),
            "artifact_paths": [str(prior_result.get("artifact_ref", ""))] if str(prior_result.get("artifact_ref", "")) else [],
            "error_info": "",
        }
    )["label"]
    current_run_id = str(packet.get("run_id", ""))
    prior_run_id = str(prior_result.get("run_id", ""))
    current_primary = _result_packet_artifact_paths(packet)[0] if _result_packet_artifact_paths(packet) else ""
    prior_primary = str(prior_result.get("artifact_ref", ""))
    current_error = str(packet.get("error_info", "")).strip()
    prior_error = ""
    current_count = len(_result_packet_artifact_paths(packet))
    prior_count = 1 if prior_primary else 0
    output_delta = f"{current_count - prior_count:+d}" if (current_count > 0 or prior_count > 0) else "not_available"
    if output_delta == "+0":
        output_delta = "no_change"

    if current_error and not prior_error:
        error_change = "introduced"
    elif not current_error and prior_error:
        error_change = "resolved"
    else:
        error_change = "unchanged"

    return {
        "has_prior": True,
        "prior_timestamp": str(prior_result.get("timestamp", "NOT_COMPUTABLE")) or "NOT_COMPUTABLE",
        "outcome_change": "changed" if current_label != prior_label else "unchanged",
        "run_id_change": "changed" if current_run_id != prior_run_id else "unchanged",
        "artifact_path_change": "changed" if current_primary != prior_primary else "unchanged",
        "output_count_delta": output_delta,
        "error_change": error_change,
    }


def _derive_action_stability(
    *,
    packet: Mapping[str, Any],
    normalized_action_history_all: List[Dict[str, str]],
    window_size: int = 5,
) -> Dict[str, Any]:
    action_name = str(packet.get("action_name", ""))
    if not action_name:
        return {
            "window_size": window_size,
            "evaluated_count": 0,
            "label": "not_available",
            "success_like_count": 0,
            "failure_like_count": 0,
            "not_computable_count": 0,
            "recent_outcomes": [],
        }
    recent = [row for row in normalized_action_history_all if str(row.get("action_name", "")) == action_name][:window_size]
    mapped: List[str] = []
    for row in recent:
        label = _classify_outcome({"status": str(row.get("outcome_status", "")), "run_id": str(row.get("run_id", "")), "artifact_paths": [str(row.get("artifact_ref", ""))]}).get("label", "NOT_COMPUTABLE")
        mapped.append(label)
    success_count = sum(1 for label in mapped if label == "SUCCESS")
    failure_count = sum(1 for label in mapped if label == "FAILED")
    not_computable_count = sum(1 for label in mapped if label == "NOT_COMPUTABLE")

    if not mapped:
        label = "not_available"
    elif failure_count >= ((len(mapped) + 1) // 2) or mapped[0] == "FAILED":
        label = "degraded"
    elif success_count == len(mapped):
        label = "stable"
    else:
        label = "mixed"

    return {
        "window_size": window_size,
        "evaluated_count": len(mapped),
        "label": label,
        "success_like_count": success_count,
        "failure_like_count": failure_count,
        "not_computable_count": not_computable_count,
        "recent_outcomes": mapped,
    }


def _derive_failure_triage(
    *,
    packet: Mapping[str, Any],
    outcome_classification: Mapping[str, str],
) -> Dict[str, Any]:
    label = str(outcome_classification.get("label", "NOT_COMPUTABLE"))
    status = str(packet.get("status", ""))
    reasons: List[str] = []
    missing_fields: List[str] = []
    run_id = str(packet.get("run_id", "")).strip()
    artifact_paths = _result_packet_artifact_paths(packet)
    error_info = str(packet.get("error_info", "")).strip()

    if not run_id:
        missing_fields.append("run_id")
        reasons.append("missing_run_id")
    if not artifact_paths:
        missing_fields.append("artifact_paths")
        reasons.append("missing_artifact_paths")
    if error_info:
        reasons.append("error_info_present")
    if status.upper() in {"FAILED", "ERROR"}:
        reasons.append("failed_status")
    if status.upper() in {"NOT_COMPUTABLE", "NOT_REQUESTED", "PREVIEW_ONLY"}:
        reasons.append("not_computable_or_preview_status")

    enabled = label in {"FAILED", "PARTIAL", "NOT_COMPUTABLE"}
    if not enabled:
        return {"enabled": False, "reasons": [], "missing_fields": [], "suggested_next_step": "No triage required"}

    if "run_id" in missing_fields:
        next_step = "Re-run action and verify run_id emission."
    elif "artifact_paths" in missing_fields:
        next_step = "Re-run action and verify artifact path emission."
    elif "error_info_present" in reasons:
        next_step = "Inspect adapter stderr/error_info and correct input contract."
    elif label == "NOT_COMPUTABLE":
        next_step = "Provide required inputs or keep explicit NOT_COMPUTABLE status."
    else:
        next_step = "Re-run preset in preview-first mode and compare output surfaces."

    return {
        "enabled": True,
        "reasons": reasons[:5],
        "missing_fields": missing_fields[:5],
        "suggested_next_step": next_step,
    }


def _derive_result_provenance_panel(
    *,
    packet: Mapping[str, Any],
    selected_run_id: Optional[str],
    comparison_run_id: Optional[str],
    session_context: Mapping[str, str],
) -> Dict[str, Any]:
    payload_args_summary = {
        "selected_run_id": selected_run_id or "",
        "compare_run_id": comparison_run_id or "",
        "health": str(session_context.get("health", "all")),
        "run_query": str(session_context.get("run_query", ""))[:80],
        "sort_mode": str(session_context.get("sort_mode", "latest_first")),
    }
    return {
        "action_name": str(packet.get("action_name", "")),
        "preset_id": str(packet.get("preset_id", "")),
        "adapter_name": str(packet.get("adapter_name", "")),
        "attempted_at": str(packet.get("attempted_at", "")),
        "run_id": str(packet.get("run_id", "")),
        "artifact_paths": _result_packet_artifact_paths(packet),
        "payload_args_summary": payload_args_summary,
    }


def _has_packet_quality(packet: Mapping[str, Any]) -> Dict[str, bool]:
    run_id_present = bool(str(packet.get("run_id", "")).strip())
    artifacts_present = len(_result_packet_artifact_paths(packet)) > 0
    error_present = bool(str(packet.get("error_info", "")).strip())
    return {
        "run_id_present": run_id_present,
        "artifacts_present": artifacts_present,
        "error_present": error_present,
    }


def _derive_decision_layer(
    *,
    packet: Mapping[str, Any],
    outcome_classification: Mapping[str, str],
    failure_triage: Mapping[str, Any],
    action_stability: Mapping[str, Any],
    suggested_next_step: str,
    runflow_workspace: Mapping[str, Any],
    prior_result_diff: Mapping[str, Any],
    compare_to_baseline_ready: bool,
) -> Dict[str, Any]:
    outcome_label = str(outcome_classification.get("label", "NOT_COMPUTABLE"))
    stability_label = str(action_stability.get("label", "not_available"))
    triage_enabled = bool(failure_triage.get("enabled", False))
    triage_missing = [str(x) for x in failure_triage.get("missing_fields", []) if isinstance(x, str)]
    triage_reasons = [str(x) for x in failure_triage.get("reasons", []) if isinstance(x, str)]
    quality = _has_packet_quality(packet)

    if (
        outcome_label == "SUCCESS"
        and stability_label == "stable"
        and not triage_enabled
        and quality["run_id_present"]
        and quality["artifacts_present"]
    ):
        decision_label = "ACCEPT"
        decision_reason = "success_stable_complete"
    elif (
        outcome_label == "SUCCESS"
        and stability_label == "mixed"
        and quality["run_id_present"]
        and quality["artifacts_present"]
    ):
        decision_label = "WATCH"
        decision_reason = "success_mixed_watch"
    elif (
        outcome_label in {"FAILED", "PARTIAL"}
        and triage_enabled
        and any(item in {"run_id", "artifact_paths"} for item in triage_missing)
        and not quality["error_present"]
    ):
        decision_label = "RETRY"
        decision_reason = "retry_missing_required_surfaces"
    else:
        decision_label = "INVESTIGATE"
        decision_reason = (
            "investigate_not_computable"
            if outcome_label == "NOT_COMPUTABLE"
            else "investigate_failure_unclear_or_repeated"
        )

    if decision_label == "RETRY":
        action_hint = "retry"
    elif decision_label == "WATCH":
        action_hint = "compare"
    elif decision_label == "ACCEPT":
        action_hint = "close"
    else:
        action_hint = "inspect"

    handoff = {
        "suggested_next_step": str(failure_triage.get("suggested_next_step", "")) or suggested_next_step,
        "action_hint": action_hint,
        "focus_target_run_id": str(packet.get("run_id", "")),
        "focus_run_link": str(runflow_workspace.get("focus_run_link", "")),
        "compare_suggestion": "compare_with_prior" if bool(prior_result_diff.get("has_prior", False)) else "no_prior_result",
        "baseline_suggestion": "compare_with_baseline" if compare_to_baseline_ready else "baseline_unavailable",
    }

    return {
        "decision_label": decision_label,
        "decision_reason": decision_reason,
        "inputs_summary": {
            "outcome_label": outcome_label,
            "stability_label": stability_label,
            "triage_enabled": triage_enabled,
            "triage_reasons": triage_reasons[:5],
            "packet_quality": quality,
        },
        "handoff": handoff,
    }


def _derive_review_history_strip(
    *,
    normalized_action_history_all: List[Dict[str, str]],
    limit: int,
) -> List[Dict[str, str]]:
    def _ts_key(value: str) -> tuple[int, str]:
        if value and value != "NOT_COMPUTABLE":
            return (0, value)
        return (1, "")

    rows: List[Dict[str, str]] = []
    for row in normalized_action_history_all:
        action_name = str(row.get("action_name", ""))
        if not action_name:
            continue
        packet = {
            "status": str(row.get("outcome_status", "")),
            "run_id": str(row.get("run_id", "")),
            "artifact_paths": [str(row.get("artifact_ref", ""))] if str(row.get("artifact_ref", "")) else [],
            "error_info": "",
        }
        outcome = _classify_outcome(packet)
        stability_stub = {"label": "mixed"}
        triage_stub = {
            "enabled": outcome["label"] in {"FAILED", "PARTIAL", "NOT_COMPUTABLE"},
            "missing_fields": [x for x in ["run_id", "artifact_paths"] if not packet.get(x if x != "artifact_paths" else "artifact_paths")],
            "reasons": [],
            "suggested_next_step": "Inspect reviewed outcome.",
        }
        decision = _derive_decision_layer(
            packet=packet,
            outcome_classification=outcome,
            failure_triage=triage_stub,
            action_stability=stability_stub,
            suggested_next_step="Inspect reviewed outcome.",
            runflow_workspace={"focus_run_link": ""},
            prior_result_diff={"has_prior": False},
            compare_to_baseline_ready=False,
        )
        rows.append(
            {
                "timestamp": str(row.get("timestamp", "NOT_COMPUTABLE")),
                "action_name": action_name,
                "run_id": str(row.get("run_id", "")),
                "outcome_classification": str(outcome.get("label", "NOT_COMPUTABLE")),
                "decision": str(decision.get("decision_label", "INVESTIGATE")),
            }
        )

    rows.sort(
        key=lambda item: (
            _ts_key(str(item.get("timestamp", ""))),
            str(item.get("timestamp", "")),
            str(item.get("action_name", "")),
            str(item.get("run_id", "")),
            str(item.get("outcome_classification", "")),
        )
    )
    rows.reverse()
    return rows[:limit]


def _list_recent_artifacts(
    *,
    root: Path,
    glob_pattern: str,
    limit: int,
    parser,
) -> List[Dict[str, str]]:
    if not root.exists():
        return []
    items: List[Dict[str, str]] = []
    for path in sorted(root.glob(glob_pattern), reverse=True):
        parsed = parser(path)
        if parsed is not None:
            items.append(parsed)
    return items[:limit]


def _timeline_from_sources(
    *,
    current_decision: Mapping[str, Any],
    decision_artifacts: List[Dict[str, str]],
    review_history: List[Dict[str, str]],
    limit: int,
) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for row in review_history:
        rows.append(
            {
                "timestamp": str(row.get("timestamp", "NOT_COMPUTABLE")),
                "action_name": str(row.get("action_name", "")),
                "run_id": str(row.get("run_id", "")),
                "outcome_classification": str(row.get("outcome_classification", "NOT_COMPUTABLE")),
                "decision_label": str(row.get("decision", "INVESTIGATE")),
                "summary": f"{row.get('action_name','')}|{row.get('decision','')}",
            }
        )
    for item in decision_artifacts:
        rows.append(
            {
                "timestamp": str(item.get("timestamp", "NOT_COMPUTABLE")),
                "action_name": str(item.get("action_name", "")),
                "run_id": str(item.get("run_id", "")),
                "outcome_classification": str(item.get("outcome_classification", "NOT_COMPUTABLE")),
                "decision_label": str(item.get("decision_label", "INVESTIGATE")),
                "summary": str(item.get("summary", ""))[:120],
            }
        )
    current_ts = _utc_now()
    rows.insert(
        0,
        {
            "timestamp": current_ts,
            "action_name": str(current_decision.get("action_name", "")),
            "run_id": str(current_decision.get("run_id", "")),
            "outcome_classification": str(current_decision.get("outcome_classification", "NOT_COMPUTABLE")),
            "decision_label": str(current_decision.get("decision_label", "INVESTIGATE")),
            "summary": str(current_decision.get("summary", ""))[:120],
        },
    )
    unique_rows: List[Dict[str, str]] = []
    seen: set[str] = set()
    for row in rows:
        key = "|".join(
            [
                str(row.get("timestamp", "")),
                str(row.get("action_name", "")),
                str(row.get("run_id", "")),
                str(row.get("decision_label", "")),
            ]
        )
        if key in seen:
            continue
        seen.add(key)
        unique_rows.append(row)
    unique_rows.sort(
        key=lambda item: (
            str(item.get("timestamp", "")) == "NOT_COMPUTABLE",
            str(item.get("timestamp", "")),
            str(item.get("action_name", "")),
            str(item.get("run_id", "")),
            str(item.get("decision_label", "")),
        ),
        reverse=True,
    )
    return unique_rows[:limit]


def _derive_decision_diff(
    *,
    current: Mapping[str, str],
    timeline: List[Dict[str, str]],
) -> Dict[str, str]:
    current_run_id = str(current.get("run_id", ""))
    current_action_name = str(current.get("action_name", ""))
    prior = None
    if current_run_id:
        prior = next((row for row in timeline[1:] if str(row.get("run_id", "")) == current_run_id), None)
    if prior is None and current_action_name:
        prior = next((row for row in timeline[1:] if str(row.get("action_name", "")) == current_action_name), None)
    if prior is None:
        return {
            "enabled": "false",
            "reason": "no_prior_decision",
            "decision_label_changed": "unchanged",
            "outcome_changed": "unchanged",
            "next_step_changed": "unchanged",
            "run_id_changed": "unchanged",
            "timestamp_ordering": "unavailable",
        }
    return {
        "enabled": "true",
        "reason": "prior_found",
        "decision_label_changed": "changed" if str(current.get("decision_label", "")) != str(prior.get("decision_label", "")) else "unchanged",
        "outcome_changed": "changed" if str(current.get("outcome_classification", "")) != str(prior.get("outcome_classification", "")) else "unchanged",
        "next_step_changed": "changed" if str(current.get("suggested_next_step", "")) != str(prior.get("suggested_next_step", "")) else "unchanged",
        "run_id_changed": "changed" if str(current.get("run_id", "")) != str(prior.get("run_id", "")) else "unchanged",
        "timestamp_ordering": "current_newer" if str(current.get("timestamp", "")) >= str(prior.get("timestamp", "")) else "prior_newer",
    }


def _derive_policy_surface(*, workbench_mode: str, control_plane: Mapping[str, Any]) -> Dict[str, Any]:
    if workbench_mode in {"decision", "session"}:
        policy_mode = "decision_review"
        policy_label = "Decision Review Policy"
        policy_summary = "Decision and session review allowed; runtime execution remains bounded."
    elif bool(control_plane.get("allowed_actions", [])):
        policy_mode = "bounded_runtime"
        policy_label = "Bounded Runtime Policy"
        policy_summary = "Allowlisted runtime actions available with deterministic guardrails."
    else:
        policy_mode = "review_only"
        policy_label = "Review Only Policy"
        policy_summary = "Inspection and reporting only; execution actions constrained."
    return {
        "policy_mode": policy_mode,
        "policy_label": policy_label,
        "policy_summary": policy_summary,
        "allowed_action_classes": ["compliance_probe", "validator", "closure_audit", "snapshot_export"],
        "constrained_action_classes": ["non_allowlisted_runtime", "arbitrary_command", "background_automation"],
        "policy_notes": [
            "Execution is restricted to allowlisted adapters.",
            "Preview-first posture is preserved.",
            "No autonomous orchestration is enabled.",
        ],
    }


def _bounded_token_repeat_count(*, text_blocks: List[str], max_tokens: int = 80) -> int:
    tokens: List[str] = []
    for block in text_blocks:
        for token in re.findall(r"[a-z0-9_]+", block.lower()):
            if len(token) < 4:
                continue
            tokens.append(token)
            if len(tokens) >= max_tokens:
                break
        if len(tokens) >= max_tokens:
            break
    if not tokens:
        return 0
    return max(0, len(tokens) - len(set(tokens)))


def _derive_structural_signals(
    *,
    selected_detail: Mapping[str, Any],
    pipeline_step_audit: List[Mapping[str, Any]],
    pipeline_quality_matrix: List[Mapping[str, Any]],
    runtime_gating: List[Mapping[str, Any]],
    ers_review_workspace_payload: Mapping[str, Any],
    latest_pipeline_envelope: Mapping[str, Any],
) -> Dict[str, Any]:
    entity_count = 0
    relation_count = 0
    for row in pipeline_quality_matrix:
        if str(row.get("surface", "")) == "map_projection":
            entity_count = int(row.get("entity_count", 0))
            relation_count = int(row.get("relation_count", 0))
            break
    repeated_token_count = _bounded_token_repeat_count(
        text_blocks=[
            str(latest_pipeline_envelope.get("final_result_summary", "")),
            str(selected_detail.get("artifact_status", "")),
            str(selected_detail.get("validator_status", "")),
            str(ers_review_workspace_payload.get("drift_label", "")),
        ]
    )
    missing_field_count = 0
    required_fields = {
        "artifact_path": selected_detail.get("artifact_path"),
        "validator_path": selected_detail.get("validator_path"),
        "latest_timestamp": selected_detail.get("latest_timestamp"),
        "pipeline_id": latest_pipeline_envelope.get("pipeline_id"),
    }
    for value in required_fields.values():
        if value in (None, "", "NOT_COMPUTABLE"):
            missing_field_count += 1
    blocked_or_not_computable_count = 0
    degraded_step_count = 0
    for row in pipeline_step_audit:
        status = str(row.get("status", "NOT_COMPUTABLE"))
        if status in {"FAILED", "NOT_COMPUTABLE", "BLOCKED"}:
            blocked_or_not_computable_count += 1
        if status in {"FAILED", "DEGRADED"}:
            degraded_step_count += 1
    for row in runtime_gating:
        if str(row.get("invokable", "false")) != "true":
            blocked_or_not_computable_count += 1
    transition_count = int(ers_review_workspace_payload.get("transition_count", 0))
    anomaly_markers: List[str] = []
    if missing_field_count > 0:
        anomaly_markers.append("missing_core_fields")
    if blocked_or_not_computable_count > 0:
        anomaly_markers.append("blocked_or_not_computable_present")
    if relation_count == 0 and entity_count > 0:
        anomaly_markers.append("entity_relation_imbalance")
    if transition_count >= 3:
        anomaly_markers.append("transition_instability")
    return {
        "entity_count": entity_count,
        "relation_count": relation_count,
        "repeated_token_count": repeated_token_count,
        "missing_field_count": missing_field_count,
        "blocked_or_not_computable_count": blocked_or_not_computable_count,
        "degraded_step_count": degraded_step_count,
        "transition_count": transition_count,
        "anomaly_markers": anomaly_markers[:5],
        "rule_ids": [
            "signals.entity_relation_from_map_projection",
            "signals.missing_field_from_required_surface",
            "signals.status_counts_from_pipeline_runtime",
            "signals.transition_from_ers_review",
            "signals.repetition_from_bounded_summary_tokens",
        ],
        "provenance": "operator_console.domain_logic.structural_signals.v4.2.derived_from_runtime_pipeline_review",
    }


def _derive_pressure_friction_detector(*, structural_signals: Mapping[str, Any], selected_run_id: Optional[str]) -> Dict[str, Any]:
    detector_id = "ABX.STRUCTURAL_PRESSURE.V4_2"
    if not selected_run_id:
        return {
            "detector_id": detector_id,
            "detector_status": "NOT_COMPUTABLE",
            "pressure_label": "NOT_COMPUTABLE",
            "friction_label": "NOT_COMPUTABLE",
            "pressure_reasons": ["selected_run_id_missing"],
            "friction_reasons": ["selected_run_id_missing"],
            "detector_summary": "Detector inert: selected run context unavailable.",
            "rule_ids": ["detector.not_computable_when_selected_run_missing"],
            "provenance": "operator_console.domain_logic.detector.v4.2.not_computable",
        }
    missing = int(structural_signals.get("missing_field_count", 0))
    blocked = int(structural_signals.get("blocked_or_not_computable_count", 0))
    degraded = int(structural_signals.get("degraded_step_count", 0))
    relation_count = int(structural_signals.get("relation_count", 0))
    entity_count = int(structural_signals.get("entity_count", 0))
    transition_count = int(structural_signals.get("transition_count", 0))
    pressure_reasons: List[str] = []
    friction_reasons: List[str] = []
    if missing > 0:
        pressure_reasons.append("missing_fields_present")
    if degraded > 0:
        pressure_reasons.append("degraded_steps_present")
        friction_reasons.append("degraded_steps_present")
    if blocked > 0:
        pressure_reasons.append("blocked_or_not_computable_surfaces_present")
        friction_reasons.append("blocked_or_not_computable_surfaces_present")
    if entity_count > 0 and relation_count == 0:
        pressure_reasons.append("entity_relation_imbalance")
        friction_reasons.append("entity_relation_imbalance")
    if transition_count >= 3:
        pressure_reasons.append("transition_instability")
        friction_reasons.append("transition_instability")
    if blocked > 0:
        pressure_label = "HIGH"
        friction_label = "BLOCKED"
        condition_band = "blocked"
    elif missing >= 2 or degraded >= 2 or transition_count >= 3:
        pressure_label = "HIGH"
        friction_label = "FRICTION"
        condition_band = "degraded"
    elif missing == 1 or degraded == 1 or (entity_count > 0 and relation_count == 0):
        pressure_label = "MODERATE"
        friction_label = "FRICTION"
        condition_band = "mildly_degraded"
    else:
        pressure_label = "LOW"
        friction_label = "CLEAR"
        condition_band = "healthy"
    return {
        "detector_id": detector_id,
        "detector_status": "SUCCESS",
        "pressure_label": pressure_label,
        "friction_label": friction_label,
        "pressure_reasons": _dedupe_preserve_order(pressure_reasons),
        "friction_reasons": _dedupe_preserve_order(friction_reasons),
        "detector_summary": (
            f"condition={condition_band}; pressure={pressure_label}; friction={friction_label}; "
            f"missing={missing}; blocked_or_not_computable={blocked}; degraded={degraded}; transitions={transition_count}"
        ),
        "rule_ids": [
            "detector.blocked_implies_friction_blocked",
            "detector.high_pressure_on_missing_degraded_transition_thresholds",
            "detector.moderate_pressure_on_single_surface_drift",
            "detector.low_pressure_when_no_explicit_drift_markers",
        ],
        "provenance": "operator_console.domain_logic.detector.v4.2.explicit_rule_ladder",
    }


def _count_repeats(values: List[str]) -> int:
    counts: Dict[str, int] = {}
    for value in values:
        if not value:
            continue
        counts[value] = counts.get(value, 0) + 1
    if not counts:
        return 0
    return sum(max(0, count - 1) for count in counts.values())


def _dedupe_preserve_order(values: List[str], *, limit: int = 6) -> List[str]:
    deduped: List[str] = []
    seen: Set[str] = set()
    for value in values:
        token = str(value).strip()
        if not token or token in seen:
            continue
        seen.add(token)
        deduped.append(token)
        if len(deduped) >= limit:
            break
    return deduped


def _bounded_list_or_none(values: List[str], *, limit: int = 3, none_token: str = "none") -> List[str]:
    bounded = [str(value).strip() for value in values if str(value).strip()][:limit]
    return bounded if bounded else [none_token]


def _derive_signal_sufficiency_surface(
    *,
    selected_run_id: Optional[str],
    structural_signals: Mapping[str, Any],
    pressure_friction_detector: Mapping[str, Any],
    motif_recurrence_detector: Mapping[str, Any],
    instability_drift_detector: Mapping[str, Any],
    anomaly_gap_detector: Mapping[str, Any],
    not_computable_subcodes: List[str],
    binding_health_surface: Mapping[str, Any],
) -> Dict[str, Any]:
    if not selected_run_id:
        return {
            "signal_sufficiency_status": "INSUFFICIENT",
            "signal_sufficiency_reasons": ["selected_run_id_missing"],
            "provenance": "operator_console.domain_logic.signal_sufficiency.v5.3.not_computable",
        }
    entity_count = int(structural_signals.get("entity_count", 0))
    relation_count = int(structural_signals.get("relation_count", 0))
    transition_count = int(structural_signals.get("transition_count", 0))
    richness = entity_count + relation_count + transition_count
    detector_statuses = [
        str(pressure_friction_detector.get("detector_status", "NOT_COMPUTABLE")),
        str(motif_recurrence_detector.get("detector_status", "NOT_COMPUTABLE")),
        str(instability_drift_detector.get("detector_status", "NOT_COMPUTABLE")),
        str(anomaly_gap_detector.get("detector_status", "NOT_COMPUTABLE")),
    ]
    usable_detector_count = len([status for status in detector_statuses if status == "SUCCESS"])
    gap_label = str(anomaly_gap_detector.get("gap_label", "NOT_COMPUTABLE"))
    anomaly_label = str(anomaly_gap_detector.get("anomaly_label", "NOT_COMPUTABLE"))
    detector_ready_state = str(binding_health_surface.get("detector_ready_state", "NOT_READY"))
    reasons: List[str] = []
    if usable_detector_count < 3:
        reasons.append("insufficient_detector_coverage")
    if richness <= 1:
        reasons.append("minimal_structural_richness")
    if gap_label == "BROKEN" or anomaly_label == "MAJOR":
        reasons.append("major_context_gap_burden")
    if not_computable_subcodes:
        reasons.append("not_computable_subcodes_present")
    if detector_ready_state != "READY":
        reasons.append("binding_detector_context_not_ready")
    if (
        "insufficient_detector_coverage" in reasons
        or "major_context_gap_burden" in reasons
        or "binding_detector_context_not_ready" in reasons
    ):
        status = "INSUFFICIENT"
    elif "minimal_structural_richness" in reasons or "not_computable_subcodes_present" in reasons:
        status = "THIN"
    else:
        status = "SUFFICIENT"
    return {
        "signal_sufficiency_status": status,
        "signal_sufficiency_reasons": _dedupe_preserve_order(reasons, limit=5),
        "usable_detector_count": usable_detector_count,
        "structural_richness": richness,
        "provenance": "operator_console.domain_logic.signal_sufficiency.v5.3.explicit_rule_ladder",
    }


def _derive_motif_recurrence_signals(
    *,
    structural_signals: Mapping[str, Any],
    pressure_friction_detector: Mapping[str, Any],
    pipeline_step_audit: List[Mapping[str, Any]],
    pipeline_quality_matrix: List[Mapping[str, Any]],
    pipeline_routing: Mapping[str, Any],
    ers_review_workspace_payload: Mapping[str, Any],
    runtime_gating: List[Mapping[str, Any]],
) -> Dict[str, Any]:
    repeated_token_count = int(structural_signals.get("repeated_token_count", 0))
    transition_entities = [
        str(row.get("item_id", "")).strip()
        for row in ers_review_workspace_payload.get("transition_log", [])
        if isinstance(row, Mapping) and str(row.get("item_id", "")).strip()
    ]
    repeated_entity_count = _count_repeats(transition_entities)
    transition_forms = [
        str(row.get("transition_type", "")).strip()
        for row in ers_review_workspace_payload.get("transition_log", [])
        if isinstance(row, Mapping) and str(row.get("transition_type", "")).strip()
    ]
    repeated_relation_form_count = _count_repeats(transition_forms)
    blocker_reasons = [str(row.get("blocking_reason", "")) for row in pipeline_step_audit if str(row.get("blocking_reason", ""))]
    blocker_reasons.extend([str(row.get("gating_reason", "")) for row in runtime_gating if str(row.get("invokable", "false")) != "true"])
    blocker_reasons.extend([str(x) for x in pressure_friction_detector.get("friction_reasons", []) if isinstance(x, str)])
    repeated_blocker_reason_count = _count_repeats(blocker_reasons)
    transitions = [
        f"{str(row.get('item_id', ''))}:{str(row.get('transition_type', ''))}"
        for row in ers_review_workspace_payload.get("transition_log", [])
        if isinstance(row, Mapping)
    ]
    repeated_transition_pattern_count = _count_repeats(transitions)
    routing_patterns = [
        f"recommended:{str(pipeline_routing.get('recommended_pipeline_id', ''))}",
        f"effective:{str(pipeline_routing.get('effective_pipeline_id', ''))}",
        f"source:{str(pipeline_routing.get('selection_source', ''))}",
    ]
    repeated_pipeline_or_routing_pattern_count = _count_repeats(routing_patterns)
    motifs: List[str] = []
    if repeated_blocker_reason_count > 0:
        motifs.append(f"blocker_pattern:repeat={repeated_blocker_reason_count}")
    if repeated_transition_pattern_count > 0:
        motifs.append(f"transition_pattern:repeat={repeated_transition_pattern_count}")
    if repeated_token_count > 0:
        motifs.append(f"token_pattern:repeat={repeated_token_count}")
    if repeated_entity_count > 0:
        motifs.append(f"entity_pattern:repeat={repeated_entity_count}")
    if repeated_relation_form_count > 0:
        motifs.append(f"relation_pattern:repeat={repeated_relation_form_count}")
    return {
        "repeated_token_count": repeated_token_count,
        "repeated_entity_count": repeated_entity_count,
        "repeated_relation_form_count": repeated_relation_form_count,
        "repeated_blocker_reason_count": repeated_blocker_reason_count,
        "repeated_transition_pattern_count": repeated_transition_pattern_count,
        "repeated_pipeline_or_routing_pattern_count": repeated_pipeline_or_routing_pattern_count,
        "motif_candidate_summaries": motifs[:5],
        "rule_ids": [
            "motif.repeat_token_from_structural_signal",
            "motif.repeat_entity_relation_from_ers_transition_log",
            "motif.repeat_blocker_reason_from_pipeline_runtime_detector_reasons",
            "motif.repeat_transition_from_ers_transitions",
            "motif.repeat_routing_pattern_from_pipeline_routing_surface",
        ],
        "provenance": "operator_console.domain_logic.motif_signals.v4.3.local_runtime_pipeline_review_state",
    }


def _derive_motif_recurrence_detector(
    *,
    motif_recurrence_signals: Mapping[str, Any],
    selected_run_id: Optional[str],
) -> Dict[str, Any]:
    detector_id = "ABX.MOTIF_RECURRENCE.V4_3"
    if not selected_run_id:
        return {
            "detector_id": detector_id,
            "detector_status": "NOT_COMPUTABLE",
            "motif_label": "NOT_COMPUTABLE",
            "recurrence_label": "NOT_COMPUTABLE",
            "motif_reasons": ["selected_run_id_missing"],
            "recurrence_reasons": ["selected_run_id_missing"],
            "detector_summary": "Motif detector inert: selected run context unavailable.",
            "rule_ids": ["motif_detector.not_computable_when_selected_run_missing"],
            "provenance": "operator_console.domain_logic.motif_detector.v4.3.not_computable",
        }
    token = int(motif_recurrence_signals.get("repeated_token_count", 0))
    entity = int(motif_recurrence_signals.get("repeated_entity_count", 0))
    relation = int(motif_recurrence_signals.get("repeated_relation_form_count", 0))
    blocker = int(motif_recurrence_signals.get("repeated_blocker_reason_count", 0))
    transition = int(motif_recurrence_signals.get("repeated_transition_pattern_count", 0))
    routing = int(motif_recurrence_signals.get("repeated_pipeline_or_routing_pattern_count", 0))
    intensity = token + entity + relation + blocker + transition + routing
    motif_reasons: List[str] = []
    recurrence_reasons: List[str] = []
    if blocker > 0:
        motif_reasons.append("repeated_blocker_reasons")
        recurrence_reasons.append("repeated_blocker_reasons")
    if transition > 0:
        motif_reasons.append("repeated_transition_patterns")
        recurrence_reasons.append("repeated_transition_patterns")
    if entity > 0 or relation > 0:
        motif_reasons.append("repeated_entity_relation_forms")
    if token > 0:
        motif_reasons.append("repeated_tokens")
    if routing > 0:
        recurrence_reasons.append("repeated_pipeline_routing_pattern")
    if intensity >= 6 or blocker >= 2 or transition >= 2:
        motif_label = "DOMINANT"
        recurrence_label = "PERSISTENT"
    elif intensity >= 2:
        motif_label = "PRESENT"
        recurrence_label = "RECURRING"
    else:
        motif_label = "SPARSE"
        recurrence_label = "NONE"
    return {
        "detector_id": detector_id,
        "detector_status": "SUCCESS",
        "motif_label": motif_label,
        "recurrence_label": recurrence_label,
        "motif_reasons": _dedupe_preserve_order(motif_reasons),
        "recurrence_reasons": _dedupe_preserve_order(recurrence_reasons),
        "detector_summary": (
            f"motif={motif_label}; recurrence={recurrence_label}; "
            f"blocker={blocker}; transition={transition}; token={token}; entity={entity}; relation={relation}"
        ),
        "rule_ids": [
            "motif_detector.persistent_when_multi_surface_or_blocker_transition_high",
            "motif_detector.recurring_when_repetition_signals_present",
            "motif_detector.sparse_when_repetition_signals_absent",
        ],
        "provenance": "operator_console.domain_logic.motif_detector.v4.3.explicit_rule_ladder",
    }


def _derive_instability_drift_signals(
    *,
    ers_snapshot_diff: Mapping[str, Any],
    ers_transition_log: List[Mapping[str, Any]],
    prior_result_diff: Mapping[str, Any],
    pipeline_quality_matrix: List[Mapping[str, Any]],
    review_history: List[Mapping[str, Any]],
) -> Dict[str, Any]:
    changed_items = int(ers_snapshot_diff.get("changed_items_count", 0))
    blocked_to_runnable_transition_count = len(
        [x for x in ers_transition_log if str(x.get("transition_type", "")) == "entered_runnable"]
    )
    runnable_to_blocked_transition_count = len(
        [x for x in ers_transition_log if str(x.get("transition_type", "")) == "entered_blocked"]
    )
    queue_change_count = changed_items
    status_change_count = len(
        [
            key
            for key in ["outcome_change", "run_id_change", "artifact_path_change", "error_change"]
            if str(prior_result_diff.get(key, "unchanged")) == "changed"
        ]
    )
    latest_vs_prior_result_change_count = status_change_count
    pipeline_quality_shift_count = len(
        [row for row in pipeline_quality_matrix if str(row.get("quality_label", "")) in {"DEGRADED", "NOT_COMPUTABLE"}]
    )
    review_decision_change_count = 0
    if len(review_history) >= 2:
        current = review_history[0]
        prior = review_history[1]
        if str(current.get("decision_label", "")) != str(prior.get("decision_label", "")):
            review_decision_change_count = 1
    drift_candidates: List[str] = []
    if queue_change_count > 0:
        drift_candidates.append(f"queue_change={queue_change_count}")
    if blocked_to_runnable_transition_count > 0:
        drift_candidates.append(f"blocked_to_runnable={blocked_to_runnable_transition_count}")
    if runnable_to_blocked_transition_count > 0:
        drift_candidates.append(f"runnable_to_blocked={runnable_to_blocked_transition_count}")
    if latest_vs_prior_result_change_count > 0:
        drift_candidates.append(f"result_change={latest_vs_prior_result_change_count}")
    if pipeline_quality_shift_count > 0:
        drift_candidates.append(f"pipeline_quality_shift={pipeline_quality_shift_count}")
    return {
        "status_change_count": status_change_count,
        "queue_change_count": queue_change_count,
        "blocked_to_runnable_transition_count": blocked_to_runnable_transition_count,
        "runnable_to_blocked_transition_count": runnable_to_blocked_transition_count,
        "latest_vs_prior_result_change_count": latest_vs_prior_result_change_count,
        "pipeline_quality_shift_count": pipeline_quality_shift_count,
        "review_decision_change_count": review_decision_change_count,
        "drift_candidate_summaries": drift_candidates[:6],
        "rule_ids": [
            "drift.status_change_from_prior_result_diff",
            "drift.queue_change_from_ers_snapshot_diff",
            "drift.transition_direction_counts_from_ers_transition_log",
            "drift.pipeline_quality_shift_from_quality_matrix",
            "drift.review_change_from_review_history",
        ],
        "provenance": "operator_console.domain_logic.instability_drift_signals.v4.4.local_state_only",
    }


def _derive_instability_drift_detector(
    *,
    instability_drift_signals: Mapping[str, Any],
    selected_run_id: Optional[str],
) -> Dict[str, Any]:
    detector_id = "ABX.INSTABILITY_DRIFT.V4_4"
    if not selected_run_id:
        return {
            "detector_id": detector_id,
            "detector_status": "NOT_COMPUTABLE",
            "instability_label": "NOT_COMPUTABLE",
            "drift_label": "NOT_COMPUTABLE",
            "instability_reasons": ["selected_run_id_missing"],
            "drift_reasons": ["selected_run_id_missing"],
            "detector_summary": "Instability/drift detector inert: selected run context unavailable.",
            "rule_ids": ["drift_detector.not_computable_when_selected_run_missing"],
            "provenance": "operator_console.domain_logic.instability_drift_detector.v4.4.not_computable",
        }
    status_change_count = int(instability_drift_signals.get("status_change_count", 0))
    queue_change_count = int(instability_drift_signals.get("queue_change_count", 0))
    blocked_to_runnable = int(instability_drift_signals.get("blocked_to_runnable_transition_count", 0))
    runnable_to_blocked = int(instability_drift_signals.get("runnable_to_blocked_transition_count", 0))
    result_changes = int(instability_drift_signals.get("latest_vs_prior_result_change_count", 0))
    quality_shifts = int(instability_drift_signals.get("pipeline_quality_shift_count", 0))
    review_changes = int(instability_drift_signals.get("review_decision_change_count", 0))
    instability_reasons: List[str] = []
    drift_reasons: List[str] = []
    if queue_change_count > 0:
        instability_reasons.append("queue_changes_present")
    if runnable_to_blocked > 0:
        instability_reasons.append("runnable_to_blocked_transitions_present")
        drift_reasons.append("runnable_to_blocked_transitions_present")
    if result_changes > 0:
        drift_reasons.append("result_change_present")
    if quality_shifts > 0:
        drift_reasons.append("pipeline_quality_shift_present")
    if review_changes > 0:
        drift_reasons.append("review_decision_change_present")
    intensity = status_change_count + queue_change_count + result_changes + quality_shifts + review_changes
    if intensity >= 5 or runnable_to_blocked >= 2:
        instability_label = "UNSTABLE"
        drift_label = "SIGNIFICANT"
        drift_band = "unstable"
    elif intensity >= 2 or blocked_to_runnable > 0 or runnable_to_blocked > 0:
        instability_label = "SHIFTING"
        drift_label = "MINOR"
        drift_band = "shifting"
    else:
        instability_label = "STABLE"
        drift_label = "NONE"
        drift_band = "stable"
    return {
        "detector_id": detector_id,
        "detector_status": "SUCCESS",
        "instability_label": instability_label,
        "drift_label": drift_label,
        "instability_reasons": _dedupe_preserve_order(instability_reasons),
        "drift_reasons": _dedupe_preserve_order(drift_reasons),
        "detector_summary": (
            f"drift_state={drift_band}; instability={instability_label}; drift={drift_label}; "
            f"status_changes={status_change_count}; queue_changes={queue_change_count}; quality_shifts={quality_shifts}"
        ),
        "rule_ids": [
            "drift_detector.unstable_significant_on_multi_shift_or_blocking_transitions",
            "drift_detector.shifting_minor_on_partial_shift",
            "drift_detector.stable_none_on_no_shift",
        ],
        "provenance": "operator_console.domain_logic.instability_drift_detector.v4.4.explicit_rule_ladder",
    }


def _derive_anomaly_gap_signals(
    *,
    selected_detail: Mapping[str, Any],
    pipeline_step_audit: List[Mapping[str, Any]],
    pipeline_review_export_path: Optional[str],
    ers_review_export_path: Optional[str],
    runtime_corridor: Mapping[str, Any],
) -> Dict[str, Any]:
    missing_artifact_count = 0
    if not str(selected_detail.get("artifact_path", "")):
        missing_artifact_count += 1
    if not pipeline_review_export_path:
        missing_artifact_count += 1
    if not ers_review_export_path:
        missing_artifact_count += 1
    missing_linkage_count = 0
    if int(selected_detail.get("ledger_record_ids_count", 0)) == 0:
        missing_linkage_count += 1
    if int(selected_detail.get("correlation_pointers_count", 0)) == 0:
        missing_linkage_count += 1
    empty_required_field_count = len(
        [key for key in ["artifact_path", "validator_path", "latest_timestamp"] if str(selected_detail.get(key, "")) in {"", "None", "NOT_COMPUTABLE"}]
    )
    broken_expected_step_pattern_count = len(
        [row for row in pipeline_step_audit if str(row.get("status", "")) in {"FAILED", "NOT_COMPUTABLE"}]
    )
    review_export_mismatch_count = 0
    if (pipeline_review_export_path and not ers_review_export_path) or (ers_review_export_path and not pipeline_review_export_path):
        review_export_mismatch_count = 1
    unexpected_not_computable_count = 0
    runtime_state = runtime_corridor.get("runtime_state_surface", {}) if isinstance(runtime_corridor.get("runtime_state_surface", {}), Mapping) else {}
    if str(runtime_state.get("latest_runtime_status", "")) == "NOT_COMPUTABLE" and bool(selected_detail.get("artifact_path")):
        unexpected_not_computable_count += 1
    anomaly_candidates: List[str] = []
    if missing_artifact_count > 0:
        anomaly_candidates.append(f"missing_artifact={missing_artifact_count}")
    if missing_linkage_count > 0:
        anomaly_candidates.append(f"missing_linkage={missing_linkage_count}")
    if broken_expected_step_pattern_count > 0:
        anomaly_candidates.append(f"broken_step_pattern={broken_expected_step_pattern_count}")
    return {
        "missing_artifact_count": missing_artifact_count,
        "missing_linkage_count": missing_linkage_count,
        "empty_required_field_count": empty_required_field_count,
        "broken_expected_step_pattern_count": broken_expected_step_pattern_count,
        "review_export_mismatch_count": review_export_mismatch_count,
        "unexpected_not_computable_count": unexpected_not_computable_count,
        "anomaly_candidate_summaries": anomaly_candidates[:6],
        "rule_ids": [
            "anomaly.missing_artifact_from_expected_surfaces",
            "anomaly.missing_linkage_from_selected_detail_linkage_counts",
            "anomaly.broken_step_pattern_from_pipeline_step_audit",
            "anomaly.review_export_mismatch_from_export_paths",
            "anomaly.unexpected_not_computable_from_runtime_vs_selected_artifact",
        ],
        "provenance": "operator_console.domain_logic.anomaly_gap_signals.v4.4.local_state_only",
    }


def _derive_anomaly_gap_detector(
    *,
    anomaly_gap_signals: Mapping[str, Any],
    selected_run_id: Optional[str],
) -> Dict[str, Any]:
    detector_id = "ABX.ANOMALY_GAP.V4_4"
    if not selected_run_id:
        return {
            "detector_id": detector_id,
            "detector_status": "NOT_COMPUTABLE",
            "anomaly_label": "NOT_COMPUTABLE",
            "gap_label": "NOT_COMPUTABLE",
            "anomaly_reasons": ["selected_run_id_missing"],
            "gap_reasons": ["selected_run_id_missing"],
            "detector_summary": "Anomaly/gap detector inert: selected run context unavailable.",
            "rule_ids": ["anomaly_detector.not_computable_when_selected_run_missing"],
            "provenance": "operator_console.domain_logic.anomaly_gap_detector.v4.4.not_computable",
        }
    missing_artifact_count = int(anomaly_gap_signals.get("missing_artifact_count", 0))
    missing_linkage_count = int(anomaly_gap_signals.get("missing_linkage_count", 0))
    empty_required_field_count = int(anomaly_gap_signals.get("empty_required_field_count", 0))
    broken_expected_step_pattern_count = int(anomaly_gap_signals.get("broken_expected_step_pattern_count", 0))
    review_export_mismatch_count = int(anomaly_gap_signals.get("review_export_mismatch_count", 0))
    unexpected_not_computable_count = int(anomaly_gap_signals.get("unexpected_not_computable_count", 0))
    anomaly_reasons: List[str] = []
    gap_reasons: List[str] = []
    if missing_artifact_count > 0:
        anomaly_reasons.append("missing_artifacts_present")
        gap_reasons.append("missing_artifacts_present")
    if missing_linkage_count > 0:
        anomaly_reasons.append("missing_linkage_present")
        gap_reasons.append("missing_linkage_present")
    if broken_expected_step_pattern_count > 0:
        anomaly_reasons.append("broken_step_pattern_present")
        gap_reasons.append("broken_step_pattern_present")
    if empty_required_field_count > 0:
        gap_reasons.append("empty_required_fields_present")
    if review_export_mismatch_count > 0:
        gap_reasons.append("review_export_mismatch_present")
    if unexpected_not_computable_count > 0:
        anomaly_reasons.append("unexpected_not_computable_present")
    severity = (
        missing_artifact_count
        + missing_linkage_count
        + broken_expected_step_pattern_count
        + review_export_mismatch_count
        + unexpected_not_computable_count
    )
    if severity >= 4 or broken_expected_step_pattern_count >= 2:
        anomaly_label = "MAJOR"
        gap_label = "BROKEN"
        gap_band = "broken_gap"
    elif severity >= 1 or empty_required_field_count > 0:
        anomaly_label = "MINOR"
        gap_label = "INCOMPLETE"
        gap_band = "minor_anomaly"
    else:
        anomaly_label = "NONE"
        gap_label = "COMPLETE"
        gap_band = "healthy"
    return {
        "detector_id": detector_id,
        "detector_status": "SUCCESS",
        "anomaly_label": anomaly_label,
        "gap_label": gap_label,
        "anomaly_reasons": _dedupe_preserve_order(anomaly_reasons),
        "gap_reasons": _dedupe_preserve_order(gap_reasons),
        "detector_summary": (
            f"gap_state={gap_band}; anomaly={anomaly_label}; gap={gap_label}; "
            f"missing_artifact={missing_artifact_count}; missing_linkage={missing_linkage_count}; broken_steps={broken_expected_step_pattern_count}"
        ),
        "rule_ids": [
            "anomaly_detector.major_broken_on_multi_gap_or_broken_steps",
            "anomaly_detector.minor_incomplete_on_partial_gap",
            "anomaly_detector.none_complete_on_no_gap",
        ],
        "provenance": "operator_console.domain_logic.anomaly_gap_detector.v4.4.explicit_rule_ladder",
    }


def _derive_fusion_input_surface(
    *,
    structural_signals: Mapping[str, Any],
    pressure_friction_detector: Mapping[str, Any],
    motif_recurrence_detector: Mapping[str, Any],
    instability_drift_detector: Mapping[str, Any],
    anomaly_gap_detector: Mapping[str, Any],
) -> Dict[str, Any]:
    return {
        "structural_signal_summary": (
            f"entity={int(structural_signals.get('entity_count', 0))};"
            f"relation={int(structural_signals.get('relation_count', 0))};"
            f"transition={int(structural_signals.get('transition_count', 0))}"
        ),
        "pressure_label": str(pressure_friction_detector.get("pressure_label", "NOT_COMPUTABLE")),
        "friction_label": str(pressure_friction_detector.get("friction_label", "NOT_COMPUTABLE")),
        "motif_label": str(motif_recurrence_detector.get("motif_label", "NOT_COMPUTABLE")),
        "recurrence_label": str(motif_recurrence_detector.get("recurrence_label", "NOT_COMPUTABLE")),
        "instability_label": str(instability_drift_detector.get("instability_label", "NOT_COMPUTABLE")),
        "drift_label": str(instability_drift_detector.get("drift_label", "NOT_COMPUTABLE")),
        "anomaly_label": str(anomaly_gap_detector.get("anomaly_label", "NOT_COMPUTABLE")),
        "gap_label": str(anomaly_gap_detector.get("gap_label", "NOT_COMPUTABLE")),
        "pressure_reasons_count": len([x for x in pressure_friction_detector.get("pressure_reasons", []) if isinstance(x, str)]),
        "motif_reasons_count": len([x for x in motif_recurrence_detector.get("motif_reasons", []) if isinstance(x, str)]),
        "drift_reasons_count": len([x for x in instability_drift_detector.get("drift_reasons", []) if isinstance(x, str)]),
        "anomaly_reasons_count": len([x for x in anomaly_gap_detector.get("anomaly_reasons", []) if isinstance(x, str)]),
        "rule_ids": [
            "fusion_input.from_structural_detector_family_outputs_only",
            "fusion_input.bounded_label_reason_projection",
        ],
        "provenance": "operator_console.domain_logic.fusion_input.v4.5.detector_surface_only",
    }


def _derive_detector_fusion_output(
    *,
    selected_run_id: Optional[str],
    fusion_input_surface: Mapping[str, Any],
    pressure_friction_detector: Mapping[str, Any],
    motif_recurrence_detector: Mapping[str, Any],
    instability_drift_detector: Mapping[str, Any],
    anomaly_gap_detector: Mapping[str, Any],
    signal_sufficiency_surface: Mapping[str, Any],
) -> Dict[str, Any]:
    if not selected_run_id:
        return {
            "fused_label": "NOT_COMPUTABLE",
            "fused_status": "NOT_COMPUTABLE",
            "fused_reasons": ["selected_run_id_missing"],
            "compressed_fusion_reason": "selected_run_id_missing",
            "interpretation_summary": "fusion=NOT_COMPUTABLE; reason=selected_run_id_missing",
            "rule_ids": ["fusion.not_computable_when_selected_run_missing"],
            "provenance": "operator_console.domain_logic.fusion_output.v4.5.not_computable",
        }
    detector_statuses = [
        str(pressure_friction_detector.get("detector_status", "NOT_COMPUTABLE")),
        str(motif_recurrence_detector.get("detector_status", "NOT_COMPUTABLE")),
        str(instability_drift_detector.get("detector_status", "NOT_COMPUTABLE")),
        str(anomaly_gap_detector.get("detector_status", "NOT_COMPUTABLE")),
    ]
    if any(status == "NOT_COMPUTABLE" for status in detector_statuses):
        return {
            "fused_label": "NOT_COMPUTABLE",
            "fused_status": "NOT_COMPUTABLE",
            "fused_reasons": ["detector_input_not_computable"],
            "compressed_fusion_reason": "detector_input_not_computable",
            "interpretation_summary": "fusion=NOT_COMPUTABLE; reason=detector_input_not_computable",
            "rule_ids": ["fusion.not_computable_when_any_detector_not_computable"],
            "provenance": "operator_console.domain_logic.fusion_output.v4.5.not_computable",
        }
    pressure_label = str(fusion_input_surface.get("pressure_label", "NOT_COMPUTABLE"))
    friction_label = str(fusion_input_surface.get("friction_label", "NOT_COMPUTABLE"))
    recurrence_label = str(fusion_input_surface.get("recurrence_label", "NOT_COMPUTABLE"))
    instability_label = str(fusion_input_surface.get("instability_label", "NOT_COMPUTABLE"))
    drift_label = str(fusion_input_surface.get("drift_label", "NOT_COMPUTABLE"))
    anomaly_label = str(fusion_input_surface.get("anomaly_label", "NOT_COMPUTABLE"))
    gap_label = str(fusion_input_surface.get("gap_label", "NOT_COMPUTABLE"))
    sufficiency_status = str(signal_sufficiency_surface.get("signal_sufficiency_status", "INSUFFICIENT"))
    fused_reasons: List[str] = []
    compressed_fusion_reason = "pattern_not_resolved"
    if gap_label == "BROKEN" or anomaly_label == "MAJOR":
        fused_label = "BROKEN_SIGNAL"
        compressed_fusion_reason = "blocked_by_major_context_gaps"
        fused_reasons.extend(["anomaly_or_gap_broken", "major_context_gap_burden"])
    elif gap_label == "INCOMPLETE" or anomaly_label == "MINOR":
        fused_label = "INCOMPLETE_CONTEXT"
        compressed_fusion_reason = "incomplete_context_limits_interpretation"
        fused_reasons.extend(["anomaly_or_gap_incomplete", "context_completion_required"])
    elif instability_label == "UNSTABLE" or drift_label == "SIGNIFICANT":
        fused_label = "UNSTABLE_TRANSITION"
        compressed_fusion_reason = "transition_instability_dominates_signal"
        fused_reasons.extend(["instability_or_drift_significant", "stability_revalidation_required"])
    elif pressure_label == "HIGH" or friction_label in {"FRICTION", "BLOCKED"} or recurrence_label == "PERSISTENT":
        fused_label = "ACTIVE_FRICTION"
        compressed_fusion_reason = "active_execution_friction_with_recurrence"
        fused_reasons.extend(["pressure_friction_or_recurrence_active", "execution_hardening_required"])
    elif (
        pressure_label == "LOW"
        and friction_label == "CLEAR"
        and recurrence_label in {"NONE", "RECURRING"}
        and instability_label == "STABLE"
        and anomaly_label == "NONE"
    ):
        fused_label = "STABLE_PATTERN"
        compressed_fusion_reason = "stable_pattern_across_detector_families"
        fused_reasons.extend(["all_detector_families_stable_or_clear"])
    else:
        fused_label = "ACTIVE_FRICTION"
        compressed_fusion_reason = "mixed_signals_default_to_active_friction"
        fused_reasons.extend(["default_active_friction_bucket"])
    if sufficiency_status in {"THIN", "INSUFFICIENT"} and fused_label in {"STABLE_PATTERN", "ACTIVE_FRICTION"}:
        fused_label = "INCOMPLETE_CONTEXT"
        compressed_fusion_reason = "signal_sufficiency_below_interpretive_threshold"
        fused_reasons = ["signal_sufficiency_below_interpretive_threshold"]
    fused_reason_tokens = _dedupe_preserve_order(fused_reasons)
    interpretation_summary = (
        f"fusion={fused_label}; sufficiency={sufficiency_status}; pressure/friction={pressure_label}/{friction_label}; "
        f"motif/recurrence={str(fusion_input_surface.get('motif_label', 'NOT_COMPUTABLE'))}/{recurrence_label}; "
        f"instability/drift={instability_label}/{drift_label}; anomaly/gap={anomaly_label}/{gap_label}; "
        f"compressed_reason={compressed_fusion_reason}; drivers={','.join(fused_reason_tokens[:3])}"
    )
    return {
        "fused_label": fused_label,
        "fused_status": "SUCCESS",
        "fused_reasons": fused_reason_tokens,
        "compressed_fusion_reason": compressed_fusion_reason,
        "interpretation_summary": interpretation_summary[:320],
        "rule_ids": [
            "fusion.broken_signal_when_gap_broken_or_anomaly_major",
            "fusion.incomplete_context_when_gap_incomplete_or_anomaly_minor",
            "fusion.unstable_transition_when_instability_unstable_or_drift_significant",
            "fusion.active_friction_when_pressure_or_recurrence_active",
            "fusion.stable_pattern_when_all_families_clear_stable_complete",
            "fusion.default_active_friction_bucket",
        ],
        "provenance": "operator_console.domain_logic.fusion_output.v4.5.explicit_rule_ladder",
    }


def _derive_abraxas_synthesis_input_surface(
    *,
    selected_run_id: Optional[str],
    latest_pipeline_envelope: Mapping[str, Any],
    pipeline_routing: Mapping[str, Any],
    governance: Mapping[str, Any],
    runtime_corridor: Mapping[str, Any],
    decision_workspace_payload: Mapping[str, Any],
    detector_fusion_output: Mapping[str, Any],
    pipeline_final_state: Mapping[str, Any],
    pipeline_unresolved_subcode: str,
    not_computable_subcodes: List[str],
    attention_queue: List[Mapping[str, Any]],
    suggested_next_step: str,
    signal_sufficiency_surface: Mapping[str, Any],
) -> Dict[str, Any]:
    policy_surface = governance.get("policy_surface", {}) if isinstance(governance.get("policy_surface", {}), Mapping) else {}
    runtime_workspace = runtime_corridor.get("runtime_workspace_payload", {}) if isinstance(runtime_corridor.get("runtime_workspace_payload", {}), Mapping) else {}
    blocker_rows = runtime_corridor.get("runtime_blocked_rows", []) if isinstance(runtime_corridor.get("runtime_blocked_rows", []), list) else []
    blocker_summary = [
        f"{str(row.get('action_name', 'unknown'))}:{str(row.get('gating_reason', 'not_computable'))}"
        for row in blocker_rows[:5]
        if isinstance(row, Mapping)
    ]
    return {
        "run_id": selected_run_id or "NOT_COMPUTABLE",
        "pipeline_id": str(latest_pipeline_envelope.get("pipeline_id", "NOT_COMPUTABLE")),
        "pipeline_status": str(latest_pipeline_envelope.get("overall_status", "NOT_COMPUTABLE")),
        "pipeline_classification": str(decision_workspace_payload.get("decision", "NOT_COMPUTABLE")),
        "routing_recommended_pipeline_id": str(pipeline_routing.get("recommended_pipeline_id", "NOT_COMPUTABLE")),
        "routing_effective_pipeline_id": str(pipeline_routing.get("effective_pipeline_id", "NOT_COMPUTABLE")),
        "routing_selection_source": str(pipeline_routing.get("selection_source", "NOT_COMPUTABLE")),
        "governance_policy_mode": str(policy_surface.get("policy_mode", "review_only")),
        "governance_allowlisted_action_count": len([x for x in policy_surface.get("allowed_actions", []) if isinstance(x, str)]),
        "runtime_outcome_status": str(runtime_workspace.get("outcome_status", "NOT_COMPUTABLE")),
        "runtime_action_name": str(runtime_workspace.get("action_name", "NOT_COMPUTABLE")),
        "runtime_blocker_summary": blocker_summary[:5],
        "fusion_label": str(detector_fusion_output.get("fused_label", "NOT_COMPUTABLE")),
        "fusion_status": str(detector_fusion_output.get("fused_status", "NOT_COMPUTABLE")),
        "signal_sufficiency_status": str(signal_sufficiency_surface.get("signal_sufficiency_status", "INSUFFICIENT")),
        "signal_sufficiency_reasons": [str(x) for x in signal_sufficiency_surface.get("signal_sufficiency_reasons", []) if isinstance(x, str)][:5],
        "pipeline_final_state": dict(pipeline_final_state),
        "pipeline_unresolved_subcode": pipeline_unresolved_subcode,
        "not_computable_subcodes": not_computable_subcodes[:5],
        "session_attention_count": len(attention_queue),
        "next_step_hint": suggested_next_step,
        "rule_ids": [
            "synthesis_input.pipeline_routing_governance_runtime_fusion_projection",
            "synthesis_input.blockers_from_runtime_blocked_rows",
            "synthesis_input.next_step_from_existing_suggestion_surface",
        ],
        "provenance": "operator_console.abraxas_synthesis.input.v4.6.local_state_projection",
    }


def _derive_pipeline_final_state(
    *,
    latest_pipeline_envelope: Mapping[str, Any],
    pipeline_step_records: List[Mapping[str, Any]],
    pipeline_review_workspace_payload: Mapping[str, Any],
) -> Dict[str, Any]:
    envelope_status = str(latest_pipeline_envelope.get("overall_status", "NOT_COMPUTABLE"))
    envelope_classification = str(latest_pipeline_envelope.get("final_classification", "NOT_COMPUTABLE"))
    completion_state = "UNKNOWN"
    success_flags: List[str] = []
    failure_flags: List[str] = []
    terminal_steps = {"diff_validate", "review_audit"}
    terminal = [row for row in pipeline_step_records if str(row.get("step_name", "")) in terminal_steps]
    terminal_statuses = [str(row.get("status", "NOT_COMPUTABLE")) for row in terminal]
    if terminal_statuses and all(x in {"SUCCESS", "FAILED", "PARTIAL"} for x in terminal_statuses):
        completion_state = "COMPLETE"
    elif terminal_statuses:
        completion_state = "INCOMPLETE"
    if envelope_status == "SUCCESS":
        success_flags.append("envelope_success")
    if envelope_status == "FAILED":
        failure_flags.append("envelope_failed")
    if envelope_status == "PARTIAL":
        failure_flags.append("envelope_partial")
    if any(x == "FAILED" for x in terminal_statuses):
        failure_flags.append("terminal_step_failed")
    if any(x == "NOT_COMPUTABLE" for x in terminal_statuses):
        failure_flags.append("terminal_step_not_computable")
    review_diff = str(pipeline_review_workspace_payload.get("final_classification", "NOT_COMPUTABLE"))
    if review_diff in {"SUCCESS", "FAILED", "PARTIAL"}:
        if review_diff == "SUCCESS":
            success_flags.append("review_success")
        else:
            failure_flags.append(f"review_{review_diff.lower()}")
    if envelope_status in {"SUCCESS", "FAILED", "PARTIAL"}:
        final_status = envelope_status
        resolution_source = "pipeline"
        reason = f"envelope_overall_status={envelope_status}"
    elif envelope_classification in {"SUCCESS", "FAILED", "PARTIAL"}:
        final_status = envelope_classification
        resolution_source = "pipeline_classification"
        reason = f"envelope_final_classification={envelope_classification}"
    elif completion_state == "COMPLETE" and failure_flags:
        final_status = "PARTIAL"
        resolution_source = "fallback"
        reason = "terminal_complete_with_failure_flags"
    elif completion_state == "COMPLETE" and success_flags:
        final_status = "SUCCESS"
        resolution_source = "fallback"
        reason = "terminal_complete_with_success_flags"
    else:
        final_status = "NOT_COMPUTABLE"
        resolution_source = "none"
        reason = "pipeline_status_not_resolved"
    return {
        "pipeline_final_status": final_status,
        "pipeline_completion_state": completion_state,
        "pipeline_success_flags": success_flags[:8],
        "pipeline_failure_flags": failure_flags[:8],
        "pipeline_resolution_reason": reason,
        "pipeline_status_resolved": final_status in {"SUCCESS", "PARTIAL", "FAILED"},
        "resolution_source": resolution_source,
        "provenance": "operator_console.pipeline_final_state.v4.9.deterministic_ladder",
    }


def _derive_pipeline_final_state_health_surface(
    *,
    pipeline_final_state: Mapping[str, Any],
    ledger_bridge: Mapping[str, Any],
) -> Dict[str, Any]:
    resolved = bool(pipeline_final_state.get("pipeline_status_resolved", False))
    status = str(pipeline_final_state.get("pipeline_final_status", "NOT_COMPUTABLE"))
    ledger_status = str(ledger_bridge.get("ledger_bridge_status", "MISSING"))
    if resolved:
        blocking_reason = "none"
    elif ledger_status == "MISSING":
        blocking_reason = "NC_PIPELINE_STATUS_UNRESOLVED"
    else:
        blocking_reason = "NC_PIPELINE_STATUS_UNRESOLVED"
    return {
        "pipeline_status_resolved": resolved,
        "synthesis_ready": resolved and status in {"SUCCESS", "PARTIAL", "FAILED"},
        "blocking_reason": blocking_reason,
        "resolution_source": str(pipeline_final_state.get("resolution_source", "none")),
        "provenance": "operator_console.pipeline_final_state.health.v4.9",
    }


def _derive_abraxas_synthesis_output(
    *,
    synthesis_input_surface: Mapping[str, Any],
    selected_run_id: Optional[str],
) -> Dict[str, Any]:
    def _structured_payload(
        *,
        raw_signal: Mapping[str, Any],
        structural_model: Mapping[str, Any],
        optional_lenses: Mapping[str, Any],
        claim_status: Mapping[str, Any],
        omissions: List[Mapping[str, Any]],
    ) -> Dict[str, Any]:
        normalized_omissions: List[Dict[str, str]] = []
        for row in omissions:
            if not isinstance(row, Mapping):
                continue
            normalized_omissions.append(
                {
                    "omitted_by": str(row.get("omitted_by", "")),
                    "omitted_reason": str(row.get("omitted_reason", "")),
                    "source_pointer": str(row.get("source_pointer", "")),
                    "boundary_type": str(row.get("boundary_type", "")),
                }
            )
        return {
            "raw_signal": dict(raw_signal),
            "structural_model": dict(structural_model),
            "optional_lenses": dict(optional_lenses),
            "claim_status": dict(claim_status),
            "omissions": normalized_omissions,
        }

    if not selected_run_id:
        structured_signal_payload = _structured_payload(
            raw_signal={"run_id": "NOT_COMPUTABLE"},
            structural_model={"pipeline_status": "NOT_COMPUTABLE"},
            optional_lenses={},
            claim_status={"label": "NOT_COMPUTABLE", "status": "NOT_COMPUTABLE"},
            omissions=[
                {
                    "omitted_by": "operator_console.abraxas_synthesis",
                    "omitted_reason": "selected_run_id_missing",
                    "source_pointer": "synthesis_input_surface.run_id",
                    "boundary_type": "hard_boundary",
                }
            ],
        )
        return {
            "synthesis_label": "NOT_COMPUTABLE",
            "synthesis_status": "NOT_COMPUTABLE",
            "synthesis_reasons": ["selected_run_id_missing"],
            "synthesis_blockers": ["selected_run_id_missing"],
            "synthesis_next_step": "Select run to compute synthesis output.",
            "synthesis_rule_precedence_note": "precedence=not_computable>blocked>incomplete>unstable>friction>ready>active",
            "interpretation_summary": "synthesis=NOT_COMPUTABLE; reason=selected_run_id_missing",
            "structured_signal_payload": structured_signal_payload,
            "rule_ids": ["synthesis.not_computable_when_selected_run_missing"],
            "provenance": "operator_console.abraxas_synthesis.output.v4.6.not_computable",
        }
    pipeline_status = str(synthesis_input_surface.get("pipeline_status", "NOT_COMPUTABLE"))
    pipeline_final_state = synthesis_input_surface.get("pipeline_final_state", {}) if isinstance(synthesis_input_surface.get("pipeline_final_state", {}), Mapping) else {}
    pipeline_final_status = str(pipeline_final_state.get("pipeline_final_status", "NOT_COMPUTABLE"))
    pipeline_status_resolved = bool(pipeline_final_state.get("pipeline_status_resolved", False))
    fusion_label = str(synthesis_input_surface.get("fusion_label", "NOT_COMPUTABLE"))
    fusion_status = str(synthesis_input_surface.get("fusion_status", "NOT_COMPUTABLE"))
    sufficiency_status = str(synthesis_input_surface.get("signal_sufficiency_status", "INSUFFICIENT"))
    policy_mode = str(synthesis_input_surface.get("governance_policy_mode", "review_only"))
    runtime_outcome = str(synthesis_input_surface.get("runtime_outcome_status", "NOT_COMPUTABLE"))
    blockers = [str(x) for x in synthesis_input_surface.get("runtime_blocker_summary", []) if isinstance(x, str)]
    blockers = _dedupe_preserve_order(blockers, limit=4)
    reasons: List[str] = []
    synthesis_blockers: List[str] = []
    if pipeline_status_resolved and pipeline_final_status == "FAILED":
        label = "BLOCKED"
        reasons.append("pipeline_final_status_failed")
        synthesis_blockers.append("pipeline_failed")
    elif pipeline_status_resolved and pipeline_final_status == "PARTIAL":
        label = "INCOMPLETE"
        reasons.append("pipeline_final_status_partial")
        synthesis_blockers.append("pipeline_partial_completion")
    elif pipeline_status_resolved and pipeline_final_status == "SUCCESS":
        if blockers:
            label = "BLOCKED"
            reasons.append("runtime_blockers_dominate_pipeline_success")
            synthesis_blockers.extend(blockers)
        else:
            if sufficiency_status in {"THIN", "INSUFFICIENT"}:
                label = "INCOMPLETE"
                reasons.append("signal_sufficiency_below_ready_threshold")
                synthesis_blockers.append("signal_sufficiency_below_ready_threshold")
            else:
                label = "READY"
                reasons.append("pipeline_final_status_success")
    elif fusion_status == "NOT_COMPUTABLE" or pipeline_status == "NOT_COMPUTABLE":
        label = "NOT_COMPUTABLE"
        reasons.append("fusion_or_pipeline_not_computable")
        synthesis_blockers.append(str(synthesis_input_surface.get("pipeline_unresolved_subcode", "NC_PIPELINE_STATUS_UNRESOLVED")))
    elif blockers or fusion_label == "BROKEN_SIGNAL" or pipeline_status in {"FAILED", "BLOCKED"}:
        label = "BLOCKED"
        if blockers:
            reasons.append("runtime_blockers_present")
            synthesis_blockers.extend(blockers)
        if fusion_label == "BROKEN_SIGNAL":
            reasons.append("fused_signal_broken")
            synthesis_blockers.append("fused_signal_broken")
        if pipeline_status in {"FAILED", "BLOCKED"}:
            reasons.append("pipeline_status_blocked_or_failed")
            synthesis_blockers.append("pipeline_status_blocked_or_failed")
    elif fusion_label == "INCOMPLETE_CONTEXT" or runtime_outcome in {"PARTIAL", "NOT_COMPUTABLE"}:
        label = "INCOMPLETE"
        if fusion_label == "INCOMPLETE_CONTEXT":
            reasons.append("fused_context_incomplete")
        if runtime_outcome in {"PARTIAL", "NOT_COMPUTABLE"}:
            reasons.append("runtime_outcome_incomplete")
        synthesis_blockers.append("context_completion_required")
    elif fusion_label == "UNSTABLE_TRANSITION":
        label = "UNSTABLE"
        reasons.append("fusion_unstable_transition")
    elif fusion_label == "ACTIVE_FRICTION":
        label = "FRICTION"
        reasons.append("fusion_active_friction")
    elif (
        fusion_label == "STABLE_PATTERN"
        and pipeline_status in {"SUCCESS", "READY"}
        and runtime_outcome in {"SUCCESS", "READY"}
        and policy_mode in {"bounded_runtime", "decision_review"}
    ):
        label = "READY"
        reasons.append("stable_pipeline_runtime_governance_alignment")
    else:
        if sufficiency_status in {"THIN", "INSUFFICIENT"}:
            label = "INCOMPLETE"
            reasons.append("signal_sufficiency_below_active_threshold")
            synthesis_blockers.append("signal_sufficiency_below_active_threshold")
        else:
            label = "ACTIVE"
            reasons.append("active_progress_state")
    reasons = _dedupe_preserve_order(reasons)
    synthesis_blockers = _dedupe_preserve_order(synthesis_blockers)
    synthesis_rule_precedence_note = (
        "precedence=not_computable>blocked>incomplete>unstable>friction>ready>active"
    )
    next_step_map = {
        "BLOCKED": "Resolve the first runtime blocker, then rerun synthesis for the same run context.",
        "INCOMPLETE": "Fill missing context/linkage fields and recompute synthesis before routing handoff.",
        "UNSTABLE": "Run review + drift validation, then confirm transition stability before execution.",
        "FRICTION": "Use hardening or route-to-review path to reduce friction before next runtime action.",
        "READY": "Proceed with bounded export/handoff using the effective routed pipeline.",
        "ACTIVE": "Continue one bounded action, then recompute synthesis and routing surfaces.",
        "NOT_COMPUTABLE": "Establish run, pipeline, and fusion context so synthesis can bind deterministically.",
    }
    synthesis_next_step = next_step_map[label]
    omissions: List[Dict[str, str]] = []
    if label == "NOT_COMPUTABLE":
        omissions.append(
            {
                "omitted_by": "operator_console.abraxas_synthesis",
                "omitted_reason": "pipeline_or_fusion_not_computable",
                "source_pointer": "synthesis_input_surface.pipeline_unresolved_subcode",
                "boundary_type": "hard_boundary",
            }
        )
    for blocker in synthesis_blockers[:3]:
        omissions.append(
            {
                "omitted_by": "operator_console.abraxas_synthesis",
                "omitted_reason": blocker,
                "source_pointer": "synthesis_input_surface.runtime_blocker_summary",
                "boundary_type": "hard_boundary",
            }
        )
    structured_signal_payload = _structured_payload(
        raw_signal={
            "run_id": selected_run_id,
            "pipeline_status": pipeline_status,
            "runtime_outcome": runtime_outcome,
        },
        structural_model={
            "pipeline_final_status": pipeline_final_status,
            "pipeline_status_resolved": pipeline_status_resolved,
            "fusion_status": fusion_status,
        },
        optional_lenses={
            "fusion_label": fusion_label,
            "signal_sufficiency_status": sufficiency_status,
            "governance_policy_mode": policy_mode,
        },
        claim_status={
            "label": label,
            "status": "SUCCESS",
            "reasons": reasons[:6],
        },
        omissions=omissions,
    )
    interpretation_summary = (
        f"synthesis={structured_signal_payload['claim_status'].get('label', label)}; "
        f"pipeline={structured_signal_payload['raw_signal'].get('pipeline_status', pipeline_status)}; "
        f"fusion={structured_signal_payload['optional_lenses'].get('fusion_label', fusion_label)}; "
        f"sufficiency={structured_signal_payload['optional_lenses'].get('signal_sufficiency_status', sufficiency_status)}; "
        f"runtime={structured_signal_payload['raw_signal'].get('runtime_outcome', runtime_outcome)}; "
        f"policy={structured_signal_payload['optional_lenses'].get('governance_policy_mode', policy_mode)}; "
        f"blockers={','.join(synthesis_blockers[:3]) or 'none'}"
    )
    return {
        "synthesis_label": label,
        "synthesis_status": "SUCCESS",
        "synthesis_reasons": reasons[:6],
        "synthesis_blockers": synthesis_blockers[:6],
        "synthesis_next_step": synthesis_next_step,
        "synthesis_rule_precedence_note": synthesis_rule_precedence_note,
        "interpretation_summary": interpretation_summary[:320],
        "structured_signal_payload": structured_signal_payload,
        "rule_ids": [
            "synthesis.pipeline_final_state_primary_when_resolved",
            "synthesis.blocked_when_blockers_or_broken_signal_or_pipeline_blocked",
            "synthesis.incomplete_when_context_or_runtime_partial",
            "synthesis.unstable_when_fusion_unstable_transition",
            "synthesis.friction_when_fusion_active_friction",
            "synthesis.ready_when_stable_pipeline_runtime_policy_alignment",
            "synthesis.active_default_progress_state",
        ],
        "provenance": "operator_console.abraxas_synthesis.output.v4.6.explicit_rule_ladder",
    }


def _legacy_synthesis_structured_payload_adapter(
    *,
    synthesis_output: Mapping[str, Any],
    synthesis_input_surface: Mapping[str, Any],
) -> Dict[str, Any]:
    existing = synthesis_output.get("structured_signal_payload", {})
    if isinstance(existing, Mapping) and existing:
        return dict(existing)
    return normalize_signal_sections(
        {
            "raw_signal": {
                "run_id": str(synthesis_input_surface.get("run_id", "NOT_COMPUTABLE")),
                "pipeline_status": str(synthesis_input_surface.get("pipeline_status", "NOT_COMPUTABLE")),
                "runtime_outcome": str(synthesis_input_surface.get("runtime_outcome_status", "NOT_COMPUTABLE")),
            },
            "structural_model": {
                "legacy_summary": str(synthesis_output.get("interpretation_summary", "")),
                "pipeline_final_state": dict(synthesis_input_surface.get("pipeline_final_state", {}))
                if isinstance(synthesis_input_surface.get("pipeline_final_state", {}), Mapping)
                else {},
            },
            "optional_lenses": {
                "fusion_label": str(synthesis_input_surface.get("fusion_label", "NOT_COMPUTABLE")),
                "signal_sufficiency_status": str(synthesis_input_surface.get("signal_sufficiency_status", "INSUFFICIENT")),
                "governance_policy_mode": str(synthesis_input_surface.get("governance_policy_mode", "review_only")),
            },
            "claim_status": {
                "label": str(synthesis_output.get("synthesis_label", "NOT_COMPUTABLE")),
                "status": str(synthesis_output.get("synthesis_status", "NOT_COMPUTABLE")),
                "reasons": [str(x) for x in synthesis_output.get("synthesis_reasons", []) if isinstance(x, str)][:6],
            },
            "omissions": [],
        }
    )


def _derive_guard_conditions(
    *,
    selected_run_id: Optional[str],
    control_plane: Mapping[str, Any],
    retry_reapply: Mapping[str, Any],
    latest_review_checkpoint_path: Optional[str],
    workbench_mode: str,
) -> List[Dict[str, str]]:
    allowlisted_count = len([x for x in control_plane.get("allowed_actions", []) if isinstance(x, str)])
    preview_count = len([k for k in control_plane.get("command_preview", {}).keys()]) if isinstance(control_plane.get("command_preview", {}), Mapping) else 0
    guards = [
        {
            "guard_name": "selected_run_present",
            "status": "pass" if bool(selected_run_id) else "fail",
            "explanation": "A selected run is required for run-scoped execution surfaces.",
        },
        {
            "guard_name": "adapter_allowlisted",
            "status": "pass" if allowlisted_count > 0 else "fail",
            "explanation": "At least one action must be allowlisted in control plane.",
        },
        {
            "guard_name": "preview_supported",
            "status": "pass" if preview_count > 0 else "fail",
            "explanation": "Command preview entries are required for preview-first governance.",
        },
        {
            "guard_name": "retry_context_available",
            "status": "pass" if bool(retry_reapply.get("enabled", False)) else "fail",
            "explanation": "Retry requires an existing reapply context.",
        },
        {
            "guard_name": "checkpoint_restore_available",
            "status": "pass" if bool(latest_review_checkpoint_path) else "fail",
            "explanation": "Review checkpoint restore requires a checkpoint artifact path.",
        },
        {
            "guard_name": "policy_mode_valid",
            "status": "pass" if workbench_mode in {"overview", "runs", "compare", "watch", "export", "runflow", "decision", "session", "governance", "ers", "runtime", "domain_logic"} else "fail",
            "explanation": "Workbench mode must match an approved governance mode.",
        },
    ]
    return guards


def _build_pipeline_suitability_summary(
    *,
    allowlisted: str,
    invokable: str,
    required_context_present: bool,
    final_classification: str,
    blocking_reason: str,
) -> str:
    blocked_state = "clear" if blocking_reason == "none" else f"blocked:{blocking_reason}"
    return (
        f"eligibility allowlisted={allowlisted}; invokable={invokable}; "
        f"context={'ok' if required_context_present else 'missing'}; "
        f"classification={final_classification}; {blocked_state}"
    )[:180]


def _derive_routing_recommendation_reason(
    *,
    review_context: bool,
    recommended_pipeline_id: str,
    top_classification: str,
    top_blocking_reason: str,
) -> str:
    if review_context and recommended_pipeline_id == _ABRAXAS_PIPELINE_REVIEW_PATH_ID:
        return "review_preferred_due_to_review_context_and_eligibility"
    if review_context and recommended_pipeline_id != _ABRAXAS_PIPELINE_REVIEW_PATH_ID:
        return "review_context_active_but_fallback_selected_due_to_availability_or_gating"
    if top_classification in {"SUCCESS", "PARTIAL"}:
        return "ready_preferred_due_to_higher_readiness"
    if top_blocking_reason == "none":
        return "less_blocked_preferred_due_to_clear_gating"
    return "fallback_selected_due_to_best_available_context"


def _resolve_manual_pipeline_override(
    *,
    manual_pipeline_override: Optional[str],
    canonical_pipeline_ids: List[str],
) -> Dict[str, str]:
    attempted_override = str(manual_pipeline_override or "").strip()
    if not attempted_override:
        return {
            "attempted_override": "",
            "manual_override_applied": "",
            "manual_override_status": "not_requested",
            "manual_override_message": "manual override not requested: using deterministic recommendation",
        }
    if attempted_override in canonical_pipeline_ids:
        return {
            "attempted_override": attempted_override,
            "manual_override_applied": attempted_override,
            "manual_override_status": "applied",
            "manual_override_message": f"manual override applied: effective pipeline set to {attempted_override}",
        }
    return {
        "attempted_override": attempted_override,
        "manual_override_applied": "",
        "manual_override_status": "rejected_unknown_pipeline",
        "manual_override_message": (
            f"manual override rejected: '{attempted_override}' is not in pipeline registry; "
            "using deterministic recommendation"
        ),
    }


def _compose_manual_override_surface(
    *,
    manual_override_resolution: Mapping[str, str],
) -> Dict[str, str]:
    attempted_override = str(manual_override_resolution.get("attempted_override", "")).strip()
    manual_override_applied = str(manual_override_resolution.get("manual_override_applied", "")).strip()
    manual_override_status = str(manual_override_resolution.get("manual_override_status", "not_requested")).strip() or "not_requested"
    manual_override_message = str(
        manual_override_resolution.get(
            "manual_override_message",
            "manual override not requested: using deterministic recommendation",
        )
    ).strip() or "manual override not requested: using deterministic recommendation"
    return {
        "attempted_pipeline_override": attempted_override,
        "manual_pipeline_override": manual_override_applied,
        "manual_override_status": manual_override_status,
        "manual_override_message": manual_override_message,
    }


def _derive_action_gating(
    *,
    action_presets: List[Dict[str, Any]],
    selected_run_id: Optional[str],
    control_plane: Mapping[str, Any],
    retry_reapply: Mapping[str, Any],
    policy_mode: str,
) -> List[Dict[str, Any]]:
    allowed_actions = [str(x) for x in control_plane.get("allowed_actions", []) if isinstance(x, str)]
    preview_map = control_plane.get("command_preview", {})
    rows: List[Dict[str, Any]] = []
    for preset in action_presets:
        action_name = str(preset.get("action_name", ""))
        preset_id = str(preset.get("preset_id", ""))
        required_conditions = ["policy_mode_permits_action", "adapter_allowlisted", "preview_supported"]
        if action_name != "export_operator_snapshot":
            required_conditions.append("selected_run_present")
        policy_permits = policy_mode in {"bounded_runtime", "decision_review", "review_only"}
        allowlisted = action_name in allowed_actions
        preview_supported = action_name in preview_map
        selected_run_present = bool(selected_run_id) if action_name != "export_operator_snapshot" else True
        retry_context = bool(retry_reapply.get("enabled", False))
        if not policy_permits:
            enabled = False
            gating_reason = "policy_mode_blocks_action"
        elif not allowlisted:
            enabled = False
            gating_reason = "action_not_allowlisted"
        elif not preview_supported:
            enabled = False
            gating_reason = "preview_not_supported"
        elif not selected_run_present:
            enabled = False
            gating_reason = "selected_run_missing"
        elif action_name == str(retry_reapply.get("last_action_name", "")) and not retry_context:
            enabled = False
            gating_reason = "retry_context_missing"
        else:
            enabled = True
            gating_reason = "all_conditions_pass"
        rows.append(
            {
                "preset_id": preset_id,
                "action_name": action_name,
                "enabled": "true" if enabled else "false",
                "gating_reason": gating_reason,
                "required_conditions": required_conditions,
            }
        )
    return rows[:20]


def _sanitize_viz_mode(value: Optional[str]) -> str:
    allowed = {"weather", "trace", "compare"}
    return str(value) if value in allowed else "weather"


def _derive_viz_payloads(
    *,
    closure_status: str,
    snapshot_header: Mapping[str, Any],
    governance: Mapping[str, Any],
    selected_run_detail: Mapping[str, Any],
    compare_strip: Mapping[str, Any],
    compare_delta_summary: Mapping[str, Any],
    evidence_delta_preview: Mapping[str, Any],
    attention_queue: List[Dict[str, str]],
    highlights: List[Dict[str, str]],
    recent_activity: List[Dict[str, Any]],
    execution_ledger: List[Dict[str, str]],
    decision_layer: Mapping[str, Any],
) -> Dict[str, Dict[str, Any]]:
    weather = {
        "closure_status": closure_status,
        "policy_mode": str(((governance.get("policy_surface", {}) or {}).get("policy_mode", "review_only"))),
        "health_distribution": dict(snapshot_header.get("health_counts", {"strong": 0, "partial": 0, "weak": 0})),
        "attention_count": len(attention_queue),
        "highlight_count": len(highlights),
        "summary_status": f"{closure_status}|policy={((governance.get('policy_surface', {}) or {}).get('policy_mode', 'review_only'))}",
    }
    trace = {
        "recent_activity": [
            {
                "timestamp": str(item.get("timestamp", "NOT_COMPUTABLE")),
                "activity_type": str(item.get("activity_type", "")),
                "run_id": str(item.get("run_id", "")),
                "summary": str(item.get("summary", ""))[:120],
            }
            for item in recent_activity[:10]
        ],
        "recent_decisions": [
            {
                "timestamp": str(item.get("timestamp", "NOT_COMPUTABLE")),
                "action_name": str(item.get("action_name", "")),
                "decision": str(item.get("decision", "")),
            }
            for item in (decision_layer.get("review_history", []) if isinstance(decision_layer.get("review_history", []), list) else [])[:10]
        ],
        "execution_ledger_slice": execution_ledger[:10],
    }
    compare_enabled = bool(compare_strip.get("enabled", False))
    compare = {
        "enabled": compare_enabled,
        "reason": "comparison_available" if compare_enabled else "no_comparison_context",
        "selected_run_summary": dict(selected_run_detail),
        "comparison_run_summary": dict(compare_strip.get("comparison", {})) if compare_enabled else {},
        "compare_delta_summary": dict(compare_delta_summary),
        "evidence_delta_summary": dict(evidence_delta_preview),
    }
    return {"weather": weather, "trace": trace, "compare": compare}


def _render_weather(payload: Mapping[str, Any]) -> Dict[str, Any]:
    health_distribution = payload.get("health_distribution", {})
    if not isinstance(health_distribution, Mapping):
        health_distribution = {}
    normalized_health: Dict[str, int] = {}
    for key, value in dict(health_distribution).items():
        try:
            normalized_health[str(key)] = int(value)
        except (TypeError, ValueError):
            normalized_health[str(key)] = 0
    return {
        "title": "Weather View",
        "closure_status": str(payload.get("closure_status", "NOT_COMPUTABLE")),
        "policy_mode": str(payload.get("policy_mode", "review_only")),
        "run_health_distribution": normalized_health,
        "attention_count": int(payload.get("attention_count", 0)),
        "alert_highlight_count": int(payload.get("highlight_count", 0)),
        "status": "ready",
    }


def _render_trace(payload: Mapping[str, Any]) -> Dict[str, Any]:
    activity_items = payload.get("recent_activity", [])
    decision_items = payload.get("recent_decisions", [])
    ledger_items = payload.get("execution_ledger_slice", [])
    activity = list(activity_items)[:10] if isinstance(activity_items, list) else []
    decisions = list(decision_items)[:10] if isinstance(decision_items, list) else []
    ledger = list(ledger_items)[:10] if isinstance(ledger_items, list) else []
    return {
        "title": "Trace View",
        "recent_activity_events": [dict(item) for item in activity if isinstance(item, Mapping)],
        "recent_decisions": [dict(item) for item in decisions if isinstance(item, Mapping)],
        "recent_execution_ledger_slice": [dict(item) for item in ledger if isinstance(item, Mapping)],
        "summary_line": f"Trace density: activity={len(activity)}; decisions={len(decisions)}; ledger={len(ledger)}",
        "status": "ready",
    }


def _render_compare(payload: Mapping[str, Any]) -> Dict[str, Any]:
    enabled = bool(payload.get("enabled", False))
    if not enabled:
        return {
            "title": "Compare View",
            "enabled": False,
            "status": "not_computable",
            "reason": str(payload.get("reason", "no_comparison_context")),
            "summary_line": "Compare unavailable: no comparison context.",
            "selected_run_summary": {},
            "comparison_run_summary": {},
            "compare_delta_summary": {},
            "evidence_delta_summary": {},
        }
    return {
        "title": "Compare View",
        "enabled": True,
        "status": "ready",
        "reason": str(payload.get("reason", "comparison_available")),
        "summary_line": "Compare ready: selected and comparison runs are available.",
        "selected_run_summary": dict(payload.get("selected_run_summary", {})),
        "comparison_run_summary": dict(payload.get("comparison_run_summary", {})),
        "compare_delta_summary": dict(payload.get("compare_delta_summary", {})),
        "evidence_delta_summary": dict(payload.get("evidence_delta_summary", {})),
    }


def _route_viz_render(*, viz_mode: str, viz_payloads: Mapping[str, Any]) -> Dict[str, Any]:
    mode = _sanitize_viz_mode(viz_mode)
    payload = viz_payloads.get(mode, {})
    if not payload:
        return {
            "viz_render_mode": mode,
            "viz_render_payload": {},
            "viz_render_output": {"title": f"{mode} render", "status": "unavailable", "reason": "payload_missing"},
        }
    if mode == "compare" and not bool((payload if isinstance(payload, Mapping) else {}).get("enabled", False)):
        rendered = _render_compare(payload if isinstance(payload, Mapping) else {})
    elif mode == "weather":
        rendered = _render_weather(payload)
    elif mode == "trace":
        rendered = _render_trace(payload)
    else:
        rendered = _render_compare(payload)
    return {
        "viz_render_mode": mode,
        "viz_render_payload": dict(payload),
        "viz_render_output": rendered,
    }


def build_view_state(
    *,
    base_dir: Path = Path("."),
    selected_run_id: Optional[str] = None,
    health_filter: Optional[str] = None,
    run_query: Optional[str] = None,
    sort_mode: Optional[str] = None,
    compare_run_id: Optional[str] = None,
    pinned_run_ids: Optional[List[str]] = None,
    action_history: Optional[List[Mapping[str, Any]]] = None,
    session_context: Optional[Mapping[str, str]] = None,
    workbench_mode: Optional[str] = None,
    baseline_locked_run_id: Optional[str] = None,
    snapshot_recall_items: Optional[List[Mapping[str, Any]]] = None,
    loaded_snapshot_path: Optional[str] = None,
    loaded_snapshot_status: str = "not_requested",
    latest_snapshot_report_path: Optional[str] = None,
    latest_snapshot_report_status: str = "not_requested",
    last_action: Optional[Mapping[str, Any]] = None,
    selected_preset_id: Optional[str] = None,
    dry_run_enabled: bool = False,
    result_packet_override: Optional[Mapping[str, Any]] = None,
    retry_reapply_override: Optional[Mapping[str, Any]] = None,
    latest_execution_report_path: Optional[str] = None,
    latest_execution_report_status: str = "not_requested",
    latest_handoff_bundle_path: Optional[str] = None,
    latest_handoff_bundle_status: str = "not_requested",
    latest_checkpoint_path: Optional[str] = None,
    latest_checkpoint_status: str = "not_requested",
    restored_checkpoint_path: Optional[str] = None,
    restored_checkpoint_status: str = "not_requested",
    latest_decision_export_path: Optional[str] = None,
    latest_decision_export_status: str = "not_requested",
    latest_review_checkpoint_path: Optional[str] = None,
    latest_review_checkpoint_status: str = "not_requested",
    restored_review_checkpoint_path: Optional[str] = None,
    restored_review_checkpoint_status: str = "not_requested",
    session_closeout_path: Optional[str] = None,
    session_closeout_status: str = "not_requested",
    recall_status: str = "not_requested",
    recall_path: Optional[str] = None,
    policy_snapshot_path: Optional[str] = None,
    policy_snapshot_status: str = "not_requested",
    policy_recall_status: str = "not_requested",
    policy_recall_path: Optional[str] = None,
    viz_mode: Optional[str] = None,
    viz_export_status: str = "not_requested",
    viz_export_path: Optional[str] = None,
    viz_render_export_status: str = "not_requested",
    viz_render_export_path: Optional[str] = None,
    report_export_status: str = "not_requested",
    report_export_paths: Optional[Mapping[str, str]] = None,
    latest_ers_snapshot_path: Optional[str] = None,
    latest_ers_snapshot_status: str = "not_requested",
    latest_ers_review_export_path: Optional[str] = None,
    latest_ers_review_export_status: str = "not_requested",
    latest_runtime_corridor_export_path: Optional[str] = None,
    latest_runtime_corridor_export_status: str = "not_requested",
    runtime_invocation_override: Optional[Mapping[str, Any]] = None,
    latest_pipeline_export_path: Optional[str] = None,
    latest_pipeline_export_status: str = "not_requested",
    pipeline_envelope_override: Optional[Mapping[str, Any]] = None,
    pipeline_step_records_override: Optional[List[Mapping[str, Any]]] = None,
    latest_pipeline_review_export_path: Optional[str] = None,
    latest_pipeline_review_export_status: str = "not_requested",
    manual_pipeline_override: Optional[str] = None,
    latest_pipeline_routing_export_path: Optional[str] = None,
    latest_pipeline_routing_export_status: str = "not_requested",
    latest_pipeline_final_state_export_path: Optional[str] = None,
    latest_pipeline_final_state_export_status: str = "not_requested",
    latest_detector_export_path: Optional[str] = None,
    latest_detector_export_status: str = "not_requested",
    latest_motif_export_path: Optional[str] = None,
    latest_motif_export_status: str = "not_requested",
    latest_drift_export_path: Optional[str] = None,
    latest_drift_export_status: str = "not_requested",
    latest_anomaly_export_path: Optional[str] = None,
    latest_anomaly_export_status: str = "not_requested",
    latest_fusion_export_path: Optional[str] = None,
    latest_fusion_export_status: str = "not_requested",
    latest_synthesis_export_path: Optional[str] = None,
    latest_synthesis_export_status: str = "not_requested",
    latest_binding_export_path: Optional[str] = None,
    latest_binding_export_status: str = "not_requested",
    latest_binding_envelope_export_path: Optional[str] = None,
    latest_binding_envelope_export_status: str = "not_requested",
    latest_run_id_propagation_export_path: Optional[str] = None,
    latest_run_id_propagation_export_status: str = "not_requested",
    latest_pipeline_envelope_run_id_repair_export_path: Optional[str] = None,
    latest_pipeline_envelope_run_id_repair_export_status: str = "not_requested",
    latest_context_export_path: Optional[str] = None,
    latest_context_export_status: str = "not_requested",
) -> ViewState:
    artifacts = _collect_run_artifacts(base_dir)
    validators = _collect_validator_outputs(base_dir)
    audit_paths = _collect_audit_artifacts(base_dir)

    run_ids = sorted({record["run_id"] for record in artifacts} | {record["run_id"] for record in validators})

    full_run_health_summaries = _build_run_health_summaries(run_ids=run_ids, artifacts=artifacts, validators=validators)

    applied_health_filter = _sanitize_health_filter(health_filter)
    applied_run_query = (run_query or "").strip()
    applied_sort_mode = _sanitize_sort_mode(sort_mode)

    visible_summaries = _filter_and_sort_run_summaries(
        full_run_health_summaries,
        health_filter=applied_health_filter,
        run_query=applied_run_query,
        sort_mode=applied_sort_mode,
    )
    visible_run_ids = [str(row["run_id"]) for row in visible_summaries]

    recent_activity_limit = 10
    recent_activity = _build_recent_activity(
        artifacts=artifacts,
        validators=validators,
        last_action=last_action,
        limit=recent_activity_limit,
    )

    suggested_run_id, suggestion_reason = _compute_suggested_focus(visible_summaries, visible_run_ids)

    preferred_action_run = None
    if last_action is not None:
        candidate = str(last_action.get("triggered_run_id", ""))
        preferred_action_run = candidate if candidate in visible_run_ids else None

    explicit_selection = selected_run_id if selected_run_id in visible_run_ids else None
    chosen = explicit_selection or preferred_action_run or suggested_run_id or (visible_run_ids[0] if visible_run_ids else None)

    artifact_summary = _build_artifact_summary(chosen, artifacts) if chosen else {"count": 0, "artifacts": []}
    validator_summary = _build_validator_summary(chosen, validators) if chosen else {"count": 0, "validators": []}
    selected_detail = (
        _build_selected_run_detail(chosen, artifacts, validators)
        if chosen
        else {
            "artifact_path": None,
            "validator_path": None,
            "artifact_status": "MISSING",
            "validator_status": "MISSING",
            "ledger_record_ids_count": 0,
            "ledger_artifact_ids_count": 0,
            "correlation_pointers_count": 0,
            "latest_timestamp": "NOT_COMPUTABLE",
            "health_label": "weak",
        }
    )
    weakness_reasons = _compute_weakness_reasons(selected_detail) if chosen else []
    suggested_next_step = _compute_suggested_next_step(selected_detail) if chosen else "No action needed"
    evidence_drilldown = _build_evidence_drilldown(
        run_id=chosen,
        selected_detail=selected_detail,
        artifacts=artifacts,
        audit_paths=audit_paths,
    )
    closure_status = _load_closure_status(base_dir)
    snapshot_header = _build_snapshot_header(
        closure_status=closure_status,
        visible_summaries=visible_summaries,
        suggested_run_id=suggested_run_id,
        last_action=last_action,
        recent_activity=recent_activity,
    )
    selected_comparison_run_id = compare_run_id if compare_run_id in run_ids and compare_run_id != chosen else None
    compare_strip = _build_compare_strip(
        selected_run_id=chosen,
        comparison_run_id=selected_comparison_run_id,
        run_summaries=full_run_health_summaries,
    )
    compare_delta_summary = _build_compare_delta_summary(compare_strip)
    suggested_compare_run_id, suggested_compare_reason = _compute_suggested_compare_candidate(
        selected_run_id=chosen,
        visible_summaries=visible_summaries,
    )
    evidence_delta_preview = _build_evidence_delta_preview(
        selected_run_id=chosen,
        comparison_run_id=selected_comparison_run_id,
        artifacts=artifacts,
        validators=validators,
        audit_paths=audit_paths,
    )
    normalized_pins = _normalize_pinned_runs(
        pinned_run_ids=[str(x) for x in (pinned_run_ids or []) if isinstance(x, str)],
        available_run_ids=run_ids,
        max_items=10,
    )
    pin_panel = {
        "enabled": len(normalized_pins) > 0,
        "count": len(normalized_pins),
        "items": normalized_pins,
        "max_items": 10,
    }
    highlights_limit = 8
    highlights = _build_highlights(
        visible_summaries=visible_summaries,
        compare_delta_summary=compare_delta_summary,
        compare_strip=compare_strip,
        limit=highlights_limit,
    )
    action_history_limit = 10
    normalized_action_history_all: List[Dict[str, str]] = []
    for item in action_history or []:
        normalized_action_history_all.append(
            {
                "timestamp": str(item.get("timestamp", "NOT_COMPUTABLE")),
                "action_name": str(item.get("action_name", "")),
                "preset_id": str(item.get("preset_id", "")),
                "adapter_name": str(item.get("adapter_name", "")),
                "run_id": str(item.get("run_id", "")),
                "outcome_status": str(item.get("outcome_status", "")),
                "artifact_ref": str(item.get("artifact_ref", "")),
                "summary": str(item.get("summary", "")),
            }
        )
    normalized_action_history = normalized_action_history_all[:action_history_limit]
    summary_by_run = {str(row.get("run_id", "")): row for row in full_run_health_summaries}
    attention_queue = _build_attention_queue(
        highlights=highlights,
        selected_run_id=chosen,
        selected_health_label=str(selected_detail.get("health_label", "weak")),
        suggested_run_id=suggested_run_id,
        suggested_compare_run_id=suggested_compare_run_id,
        pinned_run_ids=normalized_pins,
        summary_by_run=summary_by_run,
        limit=5,
    )
    triage_limit_per_bucket = 5
    triage_panel = _build_triage_panel(
        visible_summaries=visible_summaries,
        highlights=highlights,
        limit_per_bucket=triage_limit_per_bucket,
    )
    pinned_run_deep_cards = _build_pinned_run_deep_cards(
        pinned_run_ids=normalized_pins,
        summary_by_run=summary_by_run,
    )
    baseline_run_id, baseline_reason = _select_baseline_run(
        selected_run_id=chosen,
        pinned_run_ids=normalized_pins,
        visible_summaries=visible_summaries,
    )
    baseline_locked = False
    baseline_lock_reason = "none"
    if baseline_locked_run_id:
        if baseline_locked_run_id in run_ids:
            baseline_run_id = baseline_locked_run_id
            baseline_reason = "manual_locked_baseline"
            baseline_locked = True
            baseline_lock_reason = "manual_lock"
        else:
            baseline_locked = False
            baseline_lock_reason = "manual_lock_invalid"
    action_safety_envelope = _build_action_safety_envelope()
    applied_mode = _sanitize_workbench_mode(workbench_mode)
    workbench_header = {
        "snapshot": snapshot_header,
        "suggested_focus_run_id": suggested_run_id or "UNAVAILABLE",
        "suggested_compare_run_id": suggested_compare_run_id or "UNAVAILABLE",
        "highlights_count": len(highlights),
        "pinned_count": len(normalized_pins),
        "latest_action": normalized_action_history[0] if normalized_action_history else None,
        "attention_count": len(attention_queue),
    }
    export_preview = {
        "snapshot_header": snapshot_header,
        "selected_run_id": chosen,
        "compare_run_id": selected_comparison_run_id,
        "baseline_run_id": baseline_run_id,
        "pinned_run_ids": normalized_pins,
        "highlights": highlights,
        "triage_panel": triage_panel,
        "latest_action": normalized_action_history[0] if normalized_action_history else None,
        "attention_queue": attention_queue,
    }
    snapshot_report_payload = dict(export_preview)
    recall_limit = 10
    normalized_recall_items: List[Dict[str, str]] = []
    for item in snapshot_recall_items or []:
        normalized_recall_items.append(
            {
                "path": str(item.get("path", "")),
                "generated_at": str(item.get("generated_at", "NOT_COMPUTABLE")),
                "selected_run_id": str(item.get("selected_run_id", "")),
                "compare_run_id": str(item.get("compare_run_id", "")),
                "baseline_run_id": str(item.get("baseline_run_id", "")),
            }
        )
    normalized_recall_items = normalized_recall_items[:recall_limit]
    attention_actions_enabled = len(attention_queue) > 0
    attention_action_hint = "Use focus links to apply selected attention item context."
    compare_to_baseline_ready = baseline_run_id is not None and baseline_run_id != chosen
    control_plane = _build_control_plane(normalized_action_history, action_safety_envelope)
    action_presets = _build_action_presets()
    preset_ids = [str(item.get("preset_id", "")) for item in action_presets]
    resolved_selected_preset_id = selected_preset_id if selected_preset_id in preset_ids else (action_presets[0]["preset_id"] if action_presets else None)
    dry_run_preview = _build_dry_run_preview(
        selected_preset_id=resolved_selected_preset_id,
        dry_run_enabled=dry_run_enabled,
        presets=action_presets,
    )
    result_packet = {
        "status": "not_requested",
        "preset_id": resolved_selected_preset_id or "",
        "action_name": "",
        "adapter_name": "",
        "attempted_at": "",
        "run_id": "",
        "artifact_path": "",
        "artifact_paths": [],
        "error_info": "",
        "summary": "",
    }
    if last_action is not None:
        result_packet = {
            "status": str(last_action.get("outcome_status", "UNKNOWN")),
            "preset_id": resolved_selected_preset_id or "",
            "action_name": str(last_action.get("action_name", "")),
            "adapter_name": str(last_action.get("adapter_name", "")),
            "attempted_at": str(last_action.get("attempted_at", "")),
            "run_id": str(last_action.get("run_id", "") or last_action.get("triggered_run_id", "")),
            "artifact_path": str(last_action.get("artifact_path", "")),
            "artifact_paths": [str(last_action.get("artifact_path", ""))] if str(last_action.get("artifact_path", "")) else [],
            "error_info": str(last_action.get("error_info", "")),
            "summary": str(last_action.get("summary", "")),
        }
    if result_packet_override is not None:
        result_packet = {
            "status": str(result_packet_override.get("status", "UNKNOWN")),
            "preset_id": str(result_packet_override.get("preset_id", resolved_selected_preset_id or "")),
            "action_name": str(result_packet_override.get("action_name", "")),
            "adapter_name": str(result_packet_override.get("adapter_name", "")),
            "attempted_at": str(result_packet_override.get("attempted_at", "")),
            "run_id": str(result_packet_override.get("run_id", "")),
            "artifact_path": str(result_packet_override.get("artifact_path", "")),
            "artifact_paths": [str(x) for x in result_packet_override.get("artifact_paths", [])[:5]],
            "error_info": str(result_packet_override.get("error_info", "")),
            "summary": str(result_packet_override.get("summary", "")),
        }
    latest_history = normalized_action_history[0] if normalized_action_history else {}
    retry_reapply = {
        "enabled": bool(latest_history),
        "status": "ready" if latest_history else "not_available",
        "last_action_name": str(latest_history.get("action_name", "")),
        "last_run_id": str(latest_history.get("run_id", "")),
        "last_preset_id": str(latest_history.get("preset_id", "")),
    }
    if retry_reapply_override is not None:
        retry_reapply = {
            "enabled": bool(retry_reapply_override.get("enabled", False)),
            "status": str(retry_reapply_override.get("status", "not_available")),
            "last_action_name": str(retry_reapply_override.get("last_action_name", "")),
            "last_run_id": str(retry_reapply_override.get("last_run_id", "")),
            "last_preset_id": str(retry_reapply_override.get("last_preset_id", "")),
        }
    execution_ledger_limit = 20
    execution_ledger = [
        {
            "timestamp": str(item.get("timestamp", "NOT_COMPUTABLE")),
            "action_name": str(item.get("action_name", "")),
            "preset_id": str(item.get("preset_id", "")),
            "adapter_name": str(item.get("adapter_name", "")),
            "run_id": str(item.get("run_id", "")),
            "outcome_status": str(item.get("outcome_status", "")),
            "artifact_ref": str(item.get("artifact_ref", "")),
        }
        for item in normalized_action_history_all[:execution_ledger_limit]
    ]
    execution_report_preview = {
        "selected_preset_id": resolved_selected_preset_id or "",
        "selected_action_name": str(result_packet.get("action_name", "")),
        "result_packet": result_packet,
        "execution_ledger_slice": execution_ledger[:10],
        "selected_run_id": chosen,
        "compare_run_id": selected_comparison_run_id,
        "baseline_run_id": baseline_run_id,
        "snapshot_header": snapshot_header,
        "metadata": {
            "last_action_timestamp": str((last_action or {}).get("attempted_at", "NOT_COMPUTABLE")),
            "workbench_mode": applied_mode,
            "source": str((session_context or {}).get("source", "default")),
        },
    }
    runbook_card = {
        "selected_run_id": chosen or "UNAVAILABLE",
        "compare_run_id": selected_comparison_run_id or "UNAVAILABLE",
        "baseline_run_id": baseline_run_id or "UNAVAILABLE",
        "suggested_next_step": suggested_next_step,
        "weakness_reasons": weakness_reasons[:5],
        "evidence_refs": [
            str(selected_detail.get("artifact_path") or "MISSING"),
            str(selected_detail.get("validator_path") or "MISSING"),
        ]
        + [str(x) for x in evidence_drilldown.get("audit_refs_preview", [])[:2]],
        "last_result_summary": str(result_packet.get("summary", "")) or str(snapshot_header.get("last_action_summary", "none")),
    }
    handoff_bundle_preview = {
        "selected_run_id": chosen or "",
        "compare_run_id": selected_comparison_run_id or "",
        "baseline_run_id": baseline_run_id or "",
        "suggested_next_step": suggested_next_step,
        "allowed_actions": [str(x) for x in control_plane.get("allowed_actions", []) if isinstance(x, str)],
        "selected_preset_id": resolved_selected_preset_id or "",
        "evidence_refs": {
            "artifact_path": str(selected_detail.get("artifact_path") or ""),
            "validator_path": str(selected_detail.get("validator_path") or ""),
            "audit_refs": [str(x) for x in evidence_drilldown.get("audit_refs_preview", [])[:3]],
        },
        "attention_item": dict(attention_queue[0]) if attention_queue else {},
    }
    checkpoint_preview = {
        "selected_run_id": chosen or "",
        "compare_run_id": selected_comparison_run_id or "",
        "health": applied_health_filter,
        "run_query": applied_run_query,
        "sort_mode": applied_sort_mode,
        "selected_preset_id": resolved_selected_preset_id or "",
        "baseline_locked_run_id": baseline_locked_run_id if baseline_locked else "",
    }
    quick_actions = {
        "enabled": True,
        "preview_first": True,
        "scope_note": str(action_safety_envelope.get("scope_note", "")),
        "allowed_actions": [str(x) for x in control_plane.get("allowed_actions", []) if isinstance(x, str)],
        "presets": [
            {
                "preset_id": str(item.get("preset_id", "")),
                "action_name": str(item.get("action_name", "")),
                "scope_note": str(item.get("scope_note", "")),
            }
            for item in action_presets[:6]
        ],
    }
    runtime_adapter_audit: List[Dict[str, str]] = []
    for action_name in sorted([str(x) for x in control_plane.get("allowed_actions", []) if isinstance(x, str)]):
        meta = _RUNTIME_ADAPTER_META.get(action_name, {})
        last = next((row for row in normalized_action_history_all if str(row.get("action_name", "")) == action_name), None)
        runtime_adapter_audit.append(
            {
                "action_name": action_name,
                "adapter_name": str(meta.get("adapter_name", "")),
                "invocation_mode": str(meta.get("invocation_mode", "unavailable")),
                "preview_supported": "true" if action_name in control_plane.get("command_preview", {}) else "false",
                "last_outcome": str((last or {}).get("outcome_status", "none")),
            }
        )
    runtime_safety_notes: List[Dict[str, str]] = []
    for action_name in sorted([str(x) for x in control_plane.get("allowed_actions", []) if isinstance(x, str)]):
        note = _RUNTIME_SAFETY_NOTES.get(action_name, {})
        runtime_safety_notes.append(
            {
                "action_name": action_name,
                "runs": str(note.get("runs", "")),
                "expected_outputs": str(note.get("expected_outputs", "")),
                "scope_note": str(note.get("scope_note", "")),
                "does_not_do": str(note.get("does_not_do", "")),
            }
        )
    runflow_cards: List[Dict[str, str]] = []
    for preset in action_presets:
        action_name = str(preset.get("action_name", ""))
        last = next((row for row in normalized_action_history_all if str(row.get("action_name", "")) == action_name), None)
        runflow_cards.append(
            {
                "preset_id": str(preset.get("preset_id", "")),
                "action_name": action_name,
                "preview_ready": "true" if action_name in control_plane.get("command_preview", {}) else "false",
                "execute_ready": "true" if action_name in control_plane.get("allowed_actions", []) else "false",
                "last_result_summary": str((last or {}).get("summary", "none")),
                "last_run_id": str((last or {}).get("run_id", "")),
                "last_artifact_ref": str((last or {}).get("artifact_ref", "")),
            }
        )
    packet_artifacts = [str(x) for x in result_packet.get("artifact_paths", []) if isinstance(x, str)]
    if not packet_artifacts and str(result_packet.get("artifact_path", "")):
        packet_artifacts = [str(result_packet.get("artifact_path", ""))]
    runtime_result_drilldown = {
        "run_id": str(result_packet.get("run_id", "")),
        "artifact_paths": packet_artifacts[:5],
        "validator_output_path": next((x for x in packet_artifacts if "out/validators/" in x), ""),
        "audit_output_path": next((x for x in packet_artifacts if "/audits/" in x), ""),
        "error_detail": str(result_packet.get("error_info", ""))[:600],
        "adapter_summary": str(result_packet.get("summary", "")),
        "adapter_name": str(result_packet.get("adapter_name", "")),
        "outcome_status": str(result_packet.get("status", "")),
    }
    outcome_classification = _classify_outcome(result_packet)
    prior_result = _find_prior_result(packet=result_packet, normalized_action_history_all=normalized_action_history_all)
    prior_result_diff = _derive_prior_result_diff(
        packet=result_packet,
        outcome_classification=outcome_classification,
        prior_result=prior_result,
    )
    action_stability = _derive_action_stability(
        packet=result_packet,
        normalized_action_history_all=normalized_action_history_all,
    )
    failure_triage = _derive_failure_triage(
        packet=result_packet,
        outcome_classification=outcome_classification,
    )
    packet_required = {"status", "action_name", "preset_id", "run_id", "summary"}
    packet_shape_valid = packet_required.issubset(set(result_packet.keys()))
    adapter_checks: List[Dict[str, str]] = []
    for action_name in sorted([str(x) for x in control_plane.get("allowed_actions", []) if isinstance(x, str)]):
        exists = action_name in _RUNTIME_ADAPTER_META and (action_name in _RUNTIME_ADAPTERS or action_name == "export_operator_snapshot")
        allowlisted = action_name in control_plane.get("allowed_actions", [])
        preview_renderable = action_name in control_plane.get("command_preview", {})
        valid = exists and allowlisted and preview_renderable and packet_shape_valid
        adapter_checks.append(
            {
                "action_name": action_name,
                "adapter_exists": "pass" if exists else "fail",
                "allowlisted": "pass" if allowlisted else "fail",
                "preview_renderable": "pass" if preview_renderable else "fail",
                "packet_shape_valid": "pass" if packet_shape_valid else "fail",
                "status": "healthy" if valid else "degraded",
            }
        )
    adapter_health_checks = {
        "overall_status": "healthy" if all(x["status"] == "healthy" for x in adapter_checks) else "degraded",
        "checks": adapter_checks,
    }
    runflow_workspace = {
        "selected_preset_id": resolved_selected_preset_id or "",
        "current_step": (
            "inspect_result"
            if str(result_packet.get("status", "")).upper() in {"SUCCESS", "FAILED", "NOT_COMPUTABLE", "PREVIEW_ONLY"}
            else "select_action"
        ),
        "preview_state": str(dry_run_preview.get("status", "not_requested")),
        "execute_state": str(result_packet.get("status", "not_requested")),
        "retry_state": str(retry_reapply.get("status", "not_available")),
        "focus_run_link": f"/operator?run_id={result_packet.get('run_id','')}" if str(result_packet.get("run_id", "")) else "",
    }
    resolved_session_context = {
        "selected_run_id": chosen or "",
        "compare_run_id": selected_comparison_run_id or "",
        "health": applied_health_filter,
        "run_query": applied_run_query,
        "sort_mode": applied_sort_mode,
        "source": str((session_context or {}).get("source", "default")),
    }
    result_provenance_panel = _derive_result_provenance_panel(
        packet=result_packet,
        selected_run_id=chosen,
        comparison_run_id=selected_comparison_run_id,
        session_context=resolved_session_context,
    )
    runtime_outcome_review_workspace = {
        "enabled": True,
        "review_mode": "runtime_review",
        "packet_status": str(result_packet.get("status", "")),
        "classification_label": str(outcome_classification.get("label", "NOT_COMPUTABLE")),
        "prior_diff_enabled": bool(prior_result_diff.get("has_prior", False)),
        "stability_label": str(action_stability.get("label", "not_available")),
        "triage_enabled": bool(failure_triage.get("enabled", False)),
        "provenance_run_id": str(result_provenance_panel.get("run_id", "")),
    }
    decision_layer_payload = _derive_decision_layer(
        packet=result_packet,
        outcome_classification=outcome_classification,
        failure_triage=failure_triage,
        action_stability=action_stability,
        suggested_next_step=suggested_next_step,
        runflow_workspace=runflow_workspace,
        prior_result_diff=prior_result_diff,
        compare_to_baseline_ready=compare_to_baseline_ready,
    )
    review_history_limit = 15
    review_history = _derive_review_history_strip(
        normalized_action_history_all=normalized_action_history_all,
        limit=review_history_limit,
    )
    decision_export_preview = {
        "action_name": str(result_packet.get("action_name", "")),
        "run_id": str(result_packet.get("run_id", "")),
        "outcome_classification": dict(outcome_classification),
        "prior_result_diff_summary": dict(prior_result_diff),
        "stability_label": str(action_stability.get("label", "not_available")),
        "failure_triage": dict(failure_triage),
        "provenance_summary": dict(result_provenance_panel),
        "decision": {
            "label": str(decision_layer_payload.get("decision_label", "INVESTIGATE")),
            "reason": str(decision_layer_payload.get("decision_reason", "fallback")),
        },
        "suggested_next_step": str((decision_layer_payload.get("handoff", {}) or {}).get("suggested_next_step", "")),
        "timestamp": _utc_now(),
    }
    review_checkpoint_preview = {
        "selected_run_id": chosen or "",
        "compare_run_id": selected_comparison_run_id or "",
        "baseline_run_id": baseline_run_id or "",
        "classification": str(outcome_classification.get("label", "NOT_COMPUTABLE")),
        "decision": str(decision_layer_payload.get("decision_label", "INVESTIGATE")),
        "health": applied_health_filter,
        "run_query": applied_run_query,
        "sort_mode": applied_sort_mode,
        "selected_preset_id": resolved_selected_preset_id or "",
    }
    decision_layer = {
        "decision_label": str(decision_layer_payload.get("decision_label", "INVESTIGATE")),
        "decision_reason": str(decision_layer_payload.get("decision_reason", "fallback")),
        "handoff": dict(decision_layer_payload.get("handoff", {})),
        "review_history": review_history,
        "review_history_limit": review_history_limit,
        "decision_export_preview": decision_export_preview,
        "latest_decision_export_path": latest_decision_export_path,
        "latest_decision_export_status": latest_decision_export_status,
        "checkpoint_preview": review_checkpoint_preview,
        "latest_review_checkpoint_path": latest_review_checkpoint_path,
        "latest_review_checkpoint_status": latest_review_checkpoint_status,
        "restored_review_checkpoint_path": restored_review_checkpoint_path,
        "restored_review_checkpoint_status": restored_review_checkpoint_status,
    }
    decision_workspace_payload = {
        "mode": "decision",
        "runtime_outcome_review_workspace": runtime_outcome_review_workspace,
        "decision_label": decision_layer["decision_label"],
        "decision_reason": decision_layer["decision_reason"],
        "handoff": decision_layer["handoff"],
        "review_history_count": len(review_history),
        "latest_decision_export_status": latest_decision_export_status,
        "latest_review_checkpoint_status": latest_review_checkpoint_status,
    }
    def _parse_decision_artifact(path: Path) -> Optional[Dict[str, str]]:
        payload = _load_json(path)
        if not payload:
            return None
        outcome = payload.get("outcome_classification", {})
        decision = payload.get("decision", {})
        return {
            "path": path.as_posix(),
            "timestamp": str(payload.get("timestamp", payload.get("generated_at", "NOT_COMPUTABLE"))),
            "action_name": str(payload.get("action_name", "")),
            "run_id": str(payload.get("run_id", "")),
            "outcome_classification": str((outcome or {}).get("label", "NOT_COMPUTABLE")) if isinstance(outcome, Mapping) else "NOT_COMPUTABLE",
            "decision_label": str((decision or {}).get("label", "INVESTIGATE")) if isinstance(decision, Mapping) else "INVESTIGATE",
            "summary": str(payload.get("suggested_next_step", "")),
        }

    def _parse_review_checkpoint(path: Path) -> Optional[Dict[str, str]]:
        payload = _load_json(path)
        if not payload:
            return None
        return {
            "path": path.as_posix(),
            "timestamp": str(payload.get("generated_at", "NOT_COMPUTABLE")),
            "run_id": str(payload.get("selected_run_id", "")),
            "artifact_type": "review_checkpoint",
            "summary": str(payload.get("decision", "")),
        }

    decision_artifacts = _list_recent_artifacts(
        root=base_dir / "artifacts_seal" / "operator_decisions",
        glob_pattern="*.decision.json",
        limit=15,
        parser=_parse_decision_artifact,
    )
    checkpoint_artifacts = _list_recent_artifacts(
        root=base_dir / "artifacts_seal" / "operator_checkpoints",
        glob_pattern="*.review_checkpoint.json",
        limit=15,
        parser=_parse_review_checkpoint,
    )
    decision_timeline_limit = 15
    current_timeline_seed = {
        "action_name": str(result_packet.get("action_name", "")),
        "run_id": str(result_packet.get("run_id", "")),
        "outcome_classification": str(outcome_classification.get("label", "NOT_COMPUTABLE")),
        "decision_label": str(decision_layer.get("decision_label", "INVESTIGATE")),
        "summary": str((decision_layer.get("handoff", {}) or {}).get("suggested_next_step", "")),
    }
    decision_timeline = _timeline_from_sources(
        current_decision=current_timeline_seed,
        decision_artifacts=decision_artifacts,
        review_history=review_history,
        limit=decision_timeline_limit,
    )
    current_diff_seed = {
        "timestamp": decision_timeline[0]["timestamp"] if decision_timeline else "NOT_COMPUTABLE",
        "action_name": str(result_packet.get("action_name", "")),
        "run_id": str(result_packet.get("run_id", "")),
        "outcome_classification": str(outcome_classification.get("label", "NOT_COMPUTABLE")),
        "decision_label": str(decision_layer.get("decision_label", "INVESTIGATE")),
        "suggested_next_step": str((decision_layer.get("handoff", {}) or {}).get("suggested_next_step", "")),
    }
    decision_diff = _derive_decision_diff(current=current_diff_seed, timeline=decision_timeline)
    runs_touched_count = len({str(x.get("run_id", "")) for x in normalized_action_history_all if str(x.get("run_id", ""))})
    actions_executed_count = len([x for x in normalized_action_history_all if str(x.get("action_name", ""))])
    decisions_made_count = len(decision_timeline)
    exports_created_count = len(
        [
            x
            for x in [
                latest_snapshot_report_path,
                latest_execution_report_path,
                latest_handoff_bundle_path,
                latest_decision_export_path,
                session_closeout_path,
            ]
            if x
        ]
    )
    checkpoints_created_count = len([x for x in [latest_checkpoint_path, latest_review_checkpoint_path] if x])
    session_summary = {
        "session_start_marker": decision_timeline[-1]["timestamp"] if decision_timeline else "NOT_COMPUTABLE",
        "runs_touched_count": runs_touched_count,
        "actions_executed_count": actions_executed_count,
        "decisions_made_count": decisions_made_count,
        "exports_created_count": exports_created_count,
        "checkpoints_created_count": checkpoints_created_count,
        "latest_decision": str(decision_layer.get("decision_label", "INVESTIGATE")),
        "latest_action_outcome": str(result_packet.get("status", "NOT_COMPUTABLE")),
    }
    session_closeout_preview = {
        "session_summary": session_summary,
        "decision_timeline": decision_timeline[:10],
        "latest_decision": str(decision_layer.get("decision_label", "INVESTIGATE")),
        "latest_result_packet_summary": {
            "status": str(result_packet.get("status", "")),
            "action_name": str(result_packet.get("action_name", "")),
            "run_id": str(result_packet.get("run_id", "")),
            "summary": str(result_packet.get("summary", ""))[:160],
        },
        "exports_checkpoints": {
            "decision_export_path": latest_decision_export_path or "",
            "session_closeout_path": session_closeout_path or "",
            "checkpoint_path": latest_checkpoint_path or "",
            "review_checkpoint_path": latest_review_checkpoint_path or "",
        },
        "active_context": {
            "selected_run_id": chosen or "",
            "compare_run_id": selected_comparison_run_id or "",
            "baseline_run_id": baseline_run_id or "",
        },
    }
    session_workspace_payload = {
        "mode": "session",
        "timeline_count": len(decision_timeline),
        "decision_diff_enabled": decision_diff.get("enabled", "false"),
        "latest_decision": session_summary["latest_decision"],
        "session_closeout_status": session_closeout_status,
        "recall_status": recall_status,
    }
    session_continuity = {
        "decision_timeline": decision_timeline,
        "decision_timeline_limit": decision_timeline_limit,
        "decision_diff": decision_diff,
        "session_summary": session_summary,
        "session_closeout_preview": session_closeout_preview,
        "session_closeout_status": session_closeout_status,
        "session_closeout_path": session_closeout_path,
        "recent_decision_artifacts": decision_artifacts,
        "recent_checkpoint_artifacts": checkpoint_artifacts,
        "recall_status": recall_status,
        "recall_path": recall_path,
        "session_workspace_payload": session_workspace_payload,
    }
    policy_surface = _derive_policy_surface(workbench_mode=applied_mode, control_plane=control_plane)
    guard_conditions = _derive_guard_conditions(
        selected_run_id=chosen,
        control_plane=control_plane,
        retry_reapply=retry_reapply,
        latest_review_checkpoint_path=latest_review_checkpoint_path,
        workbench_mode=applied_mode,
    )
    action_gating = _derive_action_gating(
        action_presets=action_presets,
        selected_run_id=chosen,
        control_plane=control_plane,
        retry_reapply=retry_reapply,
        policy_mode=str(policy_surface.get("policy_mode", "review_only")),
    )
    recent_policy_artifacts = _list_recent_artifacts(
        root=base_dir / "artifacts_seal" / "operator_policy",
        glob_pattern="*.policy_snapshot.json",
        limit=10,
        parser=lambda path: (
            {
                "path": path.as_posix(),
                "timestamp": str((_load_json(path) or {}).get("generated_at", "NOT_COMPUTABLE")),
                "policy_mode": str(((_load_json(path) or {}).get("policy_surface", {}) or {}).get("policy_mode", "unknown")),
                "summary": str(((_load_json(path) or {}).get("policy_surface", {}) or {}).get("policy_summary", ""))[:140],
            }
            if _load_json(path)
            else None
        ),
    )
    policy_snapshot_preview = {
        "policy_surface": policy_surface,
        "action_gating": action_gating,
        "guard_conditions": guard_conditions,
        "enabled_actions": [row["action_name"] for row in action_gating if row.get("enabled") == "true"][:20],
        "disabled_actions": [row["action_name"] for row in action_gating if row.get("enabled") == "false"][:20],
        "context": {
            "selected_run_id": chosen or "",
            "compare_run_id": selected_comparison_run_id or "",
            "baseline_run_id": baseline_run_id or "",
            "selected_preset_id": resolved_selected_preset_id or "",
            "workbench_mode": applied_mode,
        },
        "timestamp": _utc_now(),
    }
    governance_workspace_payload = {
        "mode": "governance",
        "policy_mode": str(policy_surface.get("policy_mode", "review_only")),
        "enabled_actions_count": len([row for row in action_gating if row.get("enabled") == "true"]),
        "guard_fail_count": len([row for row in guard_conditions if row.get("status") == "fail"]),
        "policy_snapshot_status": policy_snapshot_status,
        "policy_recall_status": policy_recall_status,
    }
    governance = {
        "policy_surface": policy_surface,
        "action_gating": action_gating,
        "guard_conditions": guard_conditions,
        "policy_snapshot_preview": policy_snapshot_preview,
        "policy_snapshot_status": policy_snapshot_status,
        "policy_snapshot_path": policy_snapshot_path,
        "recent_policy_artifacts": recent_policy_artifacts,
        "policy_recall_status": policy_recall_status,
        "policy_recall_path": policy_recall_path,
        "governance_workspace_payload": governance_workspace_payload,
    }
    ers_integration = _derive_ers_integration(
        workbench_mode=applied_mode,
        selected_run_id=chosen,
        policy_mode=str(policy_surface.get("policy_mode", "review_only")),
        control_plane=control_plane,
        action_gating=action_gating,
        action_history=normalized_action_history,
        latest_result_packet=result_packet,
        latest_snapshot_path=latest_ers_snapshot_path,
        latest_snapshot_status=latest_ers_snapshot_status,
    )
    current_ers_snapshot = {
        "ers_state_surface": dict(ers_integration.get("ers_state_surface", {})),
        "ers_queue": dict(ers_integration.get("ers_queue", {})),
        "runnable_items": list((ers_integration.get("ers_queue", {}) or {}).get("runnable_items", [])),
        "blocked_items": list((ers_integration.get("ers_queue", {}) or {}).get("blocked_items", [])),
        "timestamp": _utc_now(),
    }
    prior_ers_snapshot = _load_prior_ers_snapshot(base_dir=base_dir)
    ers_snapshot_diff = _derive_ers_snapshot_diff(current_snapshot=current_ers_snapshot, prior_snapshot=prior_ers_snapshot)
    ers_drift_summary = _derive_ers_drift_summary(
        diff=ers_snapshot_diff,
        current_snapshot=current_ers_snapshot,
        prior_snapshot=prior_ers_snapshot,
    )
    ers_runtime_handoff = _derive_ers_runtime_handoff(action_history=normalized_action_history, result_packet=result_packet)
    ers_transition_log = _derive_ers_transition_log(diff=ers_snapshot_diff, action_history=normalized_action_history)
    ers_review_export_preview = {
        "ers_state_surface": dict(ers_integration.get("ers_state_surface", {})),
        "ers_snapshot_diff": ers_snapshot_diff,
        "ers_drift_summary": ers_drift_summary,
        "ers_transition_log": ers_transition_log,
        "ers_runtime_handoff": ers_runtime_handoff,
        "governance_context": {
            "policy_mode": str((governance.get("policy_surface", {}) or {}).get("policy_mode", "review_only")),
            "workbench_mode": applied_mode,
        },
        "runtime_context": {
            "selected_run_id": chosen or "",
            "compare_run_id": selected_comparison_run_id or "",
            "result_status": str(result_packet.get("status", "NOT_COMPUTABLE")),
        },
        "provenance": {
            "diff_rule": "ERS.DIFF.v1.latest_prior_snapshot",
            "drift_rule": "ERS.DRIFT.v1.rule_table",
            "transition_rule": "ERS.TRANSITION.v1.diff_plus_trigger_history",
            "handoff_rule": "ERS.HANDOFF.v1.latest_ers_trigger_linkage",
        },
        "timestamp": _utc_now(),
    }
    ers_review_workspace_payload = {
        "mode": "ers",
        "diff_status": str(ers_snapshot_diff.get("status", "NOT_COMPUTABLE")),
        "drift_label": str(ers_drift_summary.get("label", "NOT_COMPUTABLE")),
        "transition_count": len(ers_transition_log),
        "handoff_status": str(ers_runtime_handoff.get("status", "NOT_COMPUTABLE")),
        "ers_review_export_status": latest_ers_review_export_status,
    }
    ers_review = {
        "ers_snapshot_diff": ers_snapshot_diff,
        "ers_drift_summary": ers_drift_summary,
        "ers_transition_log": ers_transition_log,
        "ers_runtime_handoff": ers_runtime_handoff,
        "ers_review_export_preview": ers_review_export_preview,
        "ers_review_export_status": latest_ers_review_export_status,
        "ers_review_export_path": latest_ers_review_export_path,
        "ers_review_workspace_payload": ers_review_workspace_payload,
    }
    runtime_entry_registry = _derive_runtime_entry_registry(
        allowed_actions=[str(x) for x in control_plane.get("allowed_actions", []) if isinstance(x, str)]
    )
    runtime_gating = _derive_runtime_gating(
        runtime_entry_registry=runtime_entry_registry,
        selected_run_id=chosen,
        policy_mode=str(policy_surface.get("policy_mode", "review_only")),
        preview_map=control_plane.get("command_preview", {}) if isinstance(control_plane.get("command_preview", {}), Mapping) else {},
        ers_queue=ers_integration.get("ers_queue", {}) if isinstance(ers_integration, Mapping) else {},
    )
    runtime_invocation_envelope = _derive_runtime_invocation_envelope(last_action=last_action, selected_run_id=chosen)
    if runtime_invocation_override is not None:
        runtime_invocation_envelope = {
            **runtime_invocation_envelope,
            **dict(runtime_invocation_override),
        }
    runtime_state_surface = _derive_runtime_state_surface(
        invocation_envelope=runtime_invocation_envelope,
        execution_ledger=execution_ledger,
    )
    runtime_export_preview = {
        "runtime_entry_registry": runtime_entry_registry,
        "runtime_state_surface": runtime_state_surface,
        "latest_runtime_invocation_envelope": runtime_invocation_envelope,
        "runtime_gating_summary": runtime_gating,
        "governance_context": {
            "policy_mode": str(policy_surface.get("policy_mode", "review_only")),
            "workbench_mode": applied_mode,
        },
        "ers_context": {
            "queue_summary": dict((ers_integration.get("ers_queue", {}) if isinstance(ers_integration, Mapping) else {})),
            "trigger_status": str((ers_integration.get("ers_runtime_handoff", {}) if isinstance(ers_integration, Mapping) else {}).get("status", "NOT_COMPUTABLE")),
        },
        "timestamp": _utc_now(),
        "status": "SUCCESS",
        "run_id": str(runtime_invocation_envelope.get("run_id", "NOT_COMPUTABLE")),
        "rune_id": str(runtime_invocation_envelope.get("rune_id", "NOT_COMPUTABLE")),
        "artifact_id": f"runtime_corridor.{datetime.now(timezone.utc).strftime('%Y%m%dt%H%M%SZ').lower()}",
        "ledger_record_ids": [],
        "ledger_artifact_ids": [],
        "correlation_pointers": [],
        "provenance": "operator_console.runtime_corridor.export.v3.3.bounded_snapshot",
        "rule_strings": [
            "registry_rule=static_allowlisted_entries_only",
            "gating_rule=policy+allowlist+context+adapter+preview+ers",
            "invocation_rule=explicit_invoke_only_or_not_computable",
        ],
    }
    runtime_workspace_payload = _derive_runtime_workspace_payload(
        selected_run_id=chosen,
        invocation_envelope=runtime_invocation_envelope,
        export_status=latest_runtime_corridor_export_status,
        export_path=latest_runtime_corridor_export_path,
    )
    runtime_corridor = {
        "runtime_entry_registry": runtime_entry_registry,
        "runtime_invocation_envelope": runtime_invocation_envelope,
        "runtime_state_surface": runtime_state_surface,
        "runtime_gating": runtime_gating,
        "runtime_export_preview": runtime_export_preview,
        "runtime_export_status": latest_runtime_corridor_export_status,
        "runtime_export_path": latest_runtime_corridor_export_path,
        "runtime_workspace_payload": runtime_workspace_payload,
    }
    default_pipeline_step_records: List[Dict[str, Any]] = [
        {
            "step_index": index + 1,
            "step_name": step["step_name"],
            "rune_id": step["rune_id"],
            "input_summary": {"selected_run_id": chosen or ""},
            "output_summary": "not_executed",
            "artifact_ref": "",
            "status": "NOT_COMPUTABLE",
            "reason": "pipeline_not_invoked",
            "provenance": "operator_console.pipeline.state.v3.4.default_not_invoked",
        }
        for index, step in enumerate(_ABRAXAS_PIPELINE_STEP_CATALOG)
    ]
    normalized_pipeline_steps = [
        {
            "step_index": int(step.get("step_index", idx + 1)),
            "step_name": str(step.get("step_name", "")),
            "rune_id": str(step.get("rune_id", "NOT_COMPUTABLE")),
            "input_summary": dict(step.get("input_summary", {})) if isinstance(step.get("input_summary", {}), Mapping) else {},
            "output_summary": str(step.get("output_summary", "")),
            "artifact_ref": str(step.get("artifact_ref", "")),
            "status": str(step.get("status", "NOT_COMPUTABLE")),
            "reason": str(step.get("reason", "")),
            "provenance": str(step.get("provenance", "")),
        }
        for idx, step in enumerate(pipeline_step_records_override or default_pipeline_step_records)
        if isinstance(step, Mapping)
    ][:10]
    latest_pipeline_envelope: Dict[str, Any] = {
        "pipeline_id": _ABRAXAS_PIPELINE_ID,
        "run_id": chosen or "NOT_COMPUTABLE",
        "started_at": "NOT_COMPUTABLE",
        "completed_at": "NOT_COMPUTABLE",
        "overall_status": "NOT_COMPUTABLE",
        "final_classification": "NOT_COMPUTABLE",
        "overall_status_rule": "rollup.pipeline_not_invoked",
        "overall_status_reason": "pipeline_not_invoked",
        "step_count": len(normalized_pipeline_steps),
        "current_step": "not_invoked",
        "last_completed_step": "NOT_STARTED",
        "final_summary_block": {
            "final_classification": "NOT_COMPUTABLE",
            "overall_status_rule": "rollup.pipeline_not_invoked",
            "overall_status_reason": "pipeline_not_invoked",
            "blocking_steps": ["ingest", "diff_validate", "review_audit"],
            "successful_steps": [],
            "artifact_summary": {
                "artifact_count": 0,
                "ledger_record_count": 0,
                "ledger_artifact_count": 0,
                "correlation_pointer_count": 0,
                "linkage_complete": "false",
            },
        },
        "final_result_summary": "NOT_COMPUTABLE|pipeline_not_invoked",
        "artifact_paths": [],
        "provenance": "operator_console.pipeline.envelope.v3.4.default_not_invoked",
        "ledger_record_ids": [],
        "ledger_artifact_ids": [],
        "correlation_pointers": [],
    }
    if pipeline_envelope_override is not None:
        latest_pipeline_envelope = {
            **latest_pipeline_envelope,
            **dict(pipeline_envelope_override),
            "artifact_paths": [str(x) for x in (pipeline_envelope_override.get("artifact_paths", []) if isinstance(pipeline_envelope_override, Mapping) else []) if isinstance(x, str)][:8],
        }
    pipeline_state_surface = {
        "latest_pipeline_run": str(latest_pipeline_envelope.get("run_id", "NOT_COMPUTABLE")),
        "pipeline_status": str(latest_pipeline_envelope.get("overall_status", "NOT_COMPUTABLE")),
        "step_progression": [f"{step['step_index']}:{step['step_name']}={step['status']}" for step in normalized_pipeline_steps][:10],
        "latest_step_outputs": [{"step_name": step["step_name"], "output_summary": step["output_summary"]} for step in normalized_pipeline_steps if step["status"] in {"SUCCESS", "NOT_COMPUTABLE"}][:5],
        "pipeline_failure_point": next((step["step_name"] for step in normalized_pipeline_steps if step["status"] == "FAILED"), ""),
        "pipeline_state_summary": str(latest_pipeline_envelope.get("final_result_summary", "NOT_COMPUTABLE")),
    }
    pipeline_registry_entries = [
        row for row in runtime_entry_registry if str(row.get("entry_id", "")).startswith("entry.runtime.pipeline.")
    ][:5]
    active_pipeline_id = str(latest_pipeline_envelope.get("pipeline_id", _ABRAXAS_PIPELINE_ID))
    pipeline_registry_entry = next(
        (row for row in pipeline_registry_entries if str(row.get("pipeline_id", "")) == active_pipeline_id),
        (
            pipeline_registry_entries[0]
            if pipeline_registry_entries
            else {
                "entry_id": "entry.runtime.pipeline.abraxas_canonical",
                "action_name": "run_abraxas_pipeline",
                "pipeline_id": _ABRAXAS_PIPELINE_ID,
                "rune_id": "RUNE.INGEST",
                "allowlisted": "false",
            }
        ),
    )
    pipeline_export_preview = {
        "pipeline_id": active_pipeline_id,
        "pipeline_execution_envelope": latest_pipeline_envelope,
        "pipeline_step_records": normalized_pipeline_steps,
        "final_classification": str(latest_pipeline_envelope.get("final_classification", "NOT_COMPUTABLE")),
        "overall_status_rule": str(latest_pipeline_envelope.get("overall_status_rule", "rollup.unknown")),
        "overall_status_reason": str(latest_pipeline_envelope.get("overall_status_reason", "unknown")),
        "final_summary_block": dict(latest_pipeline_envelope.get("final_summary_block", {})) if isinstance(latest_pipeline_envelope.get("final_summary_block", {}), Mapping) else {},
        "final_result_summary": str(latest_pipeline_envelope.get("final_result_summary", "NOT_COMPUTABLE")),
        "lineage_provenance": {
            "path_rule": "canonical_static_path.ingest_parse_map_diff_review",
            "step_rule": "step_records_are_ordered_and_bounded",
            "status_rule": "explicit_rollup_failed_notcomputable_partial_success",
        },
        "governance_context": {"policy_mode": str(policy_surface.get("policy_mode", "review_only")), "workbench_mode": applied_mode},
        "runtime_context": {"selected_run_id": chosen or "", "result_packet_status": str(result_packet.get("status", "NOT_COMPUTABLE"))},
        "timestamp": _utc_now(),
    }
    pipeline_workspace_payload = {
        "mode": "runtime",
        "pipeline_id": active_pipeline_id,
        "pipeline_status": str(latest_pipeline_envelope.get("overall_status", "NOT_COMPUTABLE")),
        "latest_pipeline_run": str(latest_pipeline_envelope.get("run_id", "NOT_COMPUTABLE")),
        "pipeline_export_status": latest_pipeline_export_status,
        "pipeline_export_path": latest_pipeline_export_path or "",
    }
    bound_run_context = _derive_bound_run_context(
        selected_run_id=chosen,
        selected_detail=selected_detail,
        artifacts=artifacts,
        pipeline_workspace_payload=pipeline_workspace_payload,
    )
    pipeline_binding_snapshot = _load_latest_pipeline_binding_snapshot(base_dir=base_dir, preferred_run_id=chosen)
    operator_bound_run_context = _derive_operator_bound_run_context(
        selected_run_id=chosen,
        runtime_invocation_envelope=runtime_invocation_envelope,
        latest_pipeline_envelope=latest_pipeline_envelope,
        latest_pipeline_export_path=latest_pipeline_export_path,
        latest_pipeline_export_status=latest_pipeline_export_status,
        pipeline_binding_snapshot=pipeline_binding_snapshot,
    )
    pipeline_envelope_linkage = _derive_pipeline_envelope_linkage(
        latest_pipeline_envelope=latest_pipeline_envelope,
        latest_pipeline_steps=normalized_pipeline_steps,
        pipeline_binding_snapshot=pipeline_binding_snapshot,
        operator_bound_run_context=operator_bound_run_context,
    )
    refined_binding_nc_subcodes = _derive_refined_binding_nc_subcodes(
        operator_bound_run_context=operator_bound_run_context,
        pipeline_envelope_linkage=pipeline_envelope_linkage,
    )
    binding_envelope_health_surface = _derive_binding_envelope_health_surface(
        operator_bound_run_context=operator_bound_run_context,
        pipeline_envelope_linkage=pipeline_envelope_linkage,
    )
    ledger_bridge = _derive_ledger_bridge(
        base_dir=base_dir,
        bound_run_context=bound_run_context,
        selected_detail=selected_detail,
    )
    not_computable_subcodes = _derive_not_computable_subcodes(
        bound_run_context=bound_run_context,
        ledger_bridge=ledger_bridge,
        selected_detail=selected_detail,
    )
    binding_health_surface = _derive_binding_health_surface(
        bound_run_context=bound_run_context,
        ledger_bridge=ledger_bridge,
        not_computable_subcodes=not_computable_subcodes,
    )
    comparative_pipeline_readiness = []
    for pipeline_id in (_ABRAXAS_PIPELINE_ID, _ABRAXAS_PIPELINE_REVIEW_PATH_ID):
        is_active = pipeline_id == active_pipeline_id
        comparative_pipeline_readiness.append(
            {
                "pipeline_id": pipeline_id,
                "active": "true" if is_active else "false",
                "final_classification": str(latest_pipeline_envelope.get("final_classification", "NOT_COMPUTABLE")) if is_active else "NOT_COMPUTABLE",
                "quality_state": (
                    f"status={str(latest_pipeline_envelope.get('overall_status', 'NOT_COMPUTABLE'))}|classification={str(latest_pipeline_envelope.get('final_classification', 'NOT_COMPUTABLE'))}"
                    if is_active
                    else "NOT_COMPUTABLE"
                )[:140],
                "readiness_summary": (
                    str(latest_pipeline_envelope.get("final_result_summary", "NOT_COMPUTABLE"))[:140]
                    if is_active
                    else "NOT_COMPUTABLE|inactive_pipeline"
                ),
            }
        )
    readiness_rank = {"SUCCESS": 4, "PARTIAL": 3, "NOT_COMPUTABLE": 2, "FAILED": 1}
    gating_by_entry = {str(row.get("entry_id", "")): row for row in runtime_gating}
    pipeline_suitability_matrix: List[Dict[str, Any]] = []
    for entry in pipeline_registry_entries:
        entry_id = str(entry.get("entry_id", ""))
        pipeline_id = str(entry.get("pipeline_id", ""))
        gate_row = gating_by_entry.get(entry_id, {})
        required_context = [str(x) for x in entry.get("required_context", []) if isinstance(x, str)]
        required_context_present = all(bool(chosen) if field == "selected_run_id" else True for field in required_context)
        active_match = pipeline_id == active_pipeline_id
        final_classification = str(latest_pipeline_envelope.get("final_classification", "NOT_COMPUTABLE")) if active_match else "NOT_COMPUTABLE"
        blocking_reason = str(gate_row.get("gating_reason", "entry_unavailable")) if str(gate_row.get("invokable", "false")) != "true" else "none"
        suitability_summary = _build_pipeline_suitability_summary(
            allowlisted=str(entry.get("allowlisted", "false")),
            invokable=str(gate_row.get("invokable", "false")),
            required_context_present=required_context_present,
            final_classification=final_classification,
            blocking_reason=blocking_reason,
        )
        pipeline_suitability_matrix.append(
            {
                "pipeline_id": pipeline_id,
                "entry_id": entry_id,
                "readiness_summary": next((row.get("readiness_summary", "NOT_COMPUTABLE") for row in comparative_pipeline_readiness if str(row.get("pipeline_id", "")) == pipeline_id), "NOT_COMPUTABLE"),
                "allowlisted": str(entry.get("allowlisted", "false")),
                "invokable": str(gate_row.get("invokable", "false")),
                "required_context_present": "true" if required_context_present else "false",
                "final_classification": final_classification,
                "blocking_reason": blocking_reason,
                "suitability_summary": suitability_summary,
            }
        )
    eligible_rows = [
        row for row in pipeline_suitability_matrix
        if row["allowlisted"] == "true" and row["invokable"] == "true" and row["required_context_present"] == "true"
    ]
    canonical_pipeline_ids = [str(row.get("pipeline_id", "")) for row in pipeline_registry_entries if str(row.get("pipeline_id", ""))]
    manual_override_resolution = _resolve_manual_pipeline_override(
        manual_pipeline_override=manual_pipeline_override,
        canonical_pipeline_ids=canonical_pipeline_ids,
    )
    manual_override_surface = _compose_manual_override_surface(
        manual_override_resolution=manual_override_resolution
    )
    manual_override_applied = manual_override_surface["manual_pipeline_override"]
    recommended_pipeline_id = _ABRAXAS_PIPELINE_ID
    recommendation_reason = "fallback_to_primary_canonical_pipeline"
    routing_rule_id = "rule.fallback_primary_canonical"
    if eligible_rows:
        review_context = applied_mode in {"runtime", "ers", "governance"}
        review_candidate = next((row for row in eligible_rows if str(row.get("pipeline_id", "")) == _ABRAXAS_PIPELINE_REVIEW_PATH_ID), None)
        if review_context and review_candidate is not None:
            recommended_pipeline_id = _ABRAXAS_PIPELINE_REVIEW_PATH_ID
            recommendation_reason = _derive_routing_recommendation_reason(
                review_context=True,
                recommended_pipeline_id=recommended_pipeline_id,
                top_classification=str(review_candidate.get("final_classification", "NOT_COMPUTABLE")),
                top_blocking_reason=str(review_candidate.get("blocking_reason", "none")),
            )
            routing_rule_id = "rule.prefer_review_context"
        else:
            eligible_rows_sorted = sorted(
                eligible_rows,
                key=lambda row: (
                    readiness_rank.get(str(row.get("final_classification", "NOT_COMPUTABLE")), 0),
                    0 if str(row.get("blocking_reason", "none")) == "none" else 1,
                    1 if str(row.get("pipeline_id", "")) == _ABRAXAS_PIPELINE_ID else 0,
                ),
                reverse=True,
            )
            best_row = eligible_rows_sorted[0]
            recommended_pipeline_id = str(best_row.get("pipeline_id", _ABRAXAS_PIPELINE_ID))
            recommendation_reason = _derive_routing_recommendation_reason(
                review_context=False,
                recommended_pipeline_id=recommended_pipeline_id,
                top_classification=str(best_row.get("final_classification", "NOT_COMPUTABLE")),
                top_blocking_reason=str(best_row.get("blocking_reason", "none")),
            )
            routing_rule_id = "rule.prefer_invokable_with_context"
    elif any(row["allowlisted"] == "true" for row in pipeline_suitability_matrix):
        recommendation_reason = "allowlisted_present_but_blocked_by_gating_or_context"
        routing_rule_id = "rule.prefer_allowlisted_fallback"
    effective_pipeline_id = manual_override_applied or recommended_pipeline_id
    selection_source = "manual_override" if manual_override_applied else "recommended"
    routing_reason_detail = f"{routing_rule_id}:{recommendation_reason}"
    pipeline_routing_export_preview = {
        "pipeline_suitability_matrix": pipeline_suitability_matrix[:5],
        "recommended_pipeline_id": recommended_pipeline_id,
        "recommendation_reason": recommendation_reason,
        "routing_reason_detail": routing_reason_detail,
        "routing_rule_id": routing_rule_id,
        **manual_override_surface,
        "effective_pipeline_id": effective_pipeline_id,
        "selection_source": selection_source,
        "context": {
            "selected_run_id": chosen or "",
            "workbench_mode": applied_mode,
            "policy_mode": str(policy_surface.get("policy_mode", "review_only")),
        },
        "timestamp": str(selected_detail.get("latest_timestamp", "NOT_COMPUTABLE")),
        "provenance": "operator_console.pipeline_routing.v4.1.deterministic_rulepath",
        "rule_strings": [
            "suitability_rule=allowlist+gating+required_context+classification",
            "routing_rule=manual_override_else_ordered_recommendation",
            "selection_rule=explicit_override_no_silent_autoswitch",
        ],
    }
    pipeline_routing_workspace_payload = {
        "mode": "runtime",
        "recommended_pipeline_id": recommended_pipeline_id,
        "effective_pipeline_id": effective_pipeline_id,
        "selection_source": selection_source,
        **manual_override_surface,
        "routing_rule_id": routing_rule_id,
        "routing_reason_detail": routing_reason_detail,
        "routing_export_status": latest_pipeline_routing_export_status,
        "routing_export_path": latest_pipeline_routing_export_path or "",
    }
    pipeline_routing = {
        "pipeline_suitability_matrix": pipeline_suitability_matrix[:5],
        "recommended_pipeline_id": recommended_pipeline_id,
        "recommendation_reason": recommendation_reason,
        "routing_reason_detail": routing_reason_detail,
        "routing_rule_id": routing_rule_id,
        **manual_override_surface,
        "effective_pipeline_id": effective_pipeline_id,
        "selection_source": selection_source,
        "routing_export_preview": pipeline_routing_export_preview,
        "routing_export_status": latest_pipeline_routing_export_status,
        "routing_export_path": latest_pipeline_routing_export_path,
        "pipeline_routing_workspace_payload": pipeline_routing_workspace_payload,
    }
    abraxas_pipeline = {
        "pipeline_registry_entry": pipeline_registry_entry,
        "pipeline_registry_entries": pipeline_registry_entries,
        "latest_pipeline_envelope": latest_pipeline_envelope,
        "pipeline_step_records": normalized_pipeline_steps,
        "pipeline_state_surface": pipeline_state_surface,
        "comparative_pipeline_readiness": comparative_pipeline_readiness[:5],
        "pipeline_export_preview": pipeline_export_preview,
        "pipeline_export_status": latest_pipeline_export_status,
        "pipeline_export_path": latest_pipeline_export_path,
        "pipeline_workspace_payload": pipeline_workspace_payload,
    }
    pipeline_step_audit = _derive_pipeline_step_audit(step_records=normalized_pipeline_steps)
    pipeline_quality_matrix = _derive_pipeline_quality_matrix(pipeline_step_audit=pipeline_step_audit)
    upgrade_targets = _select_pipeline_upgrade_targets(
        pipeline_quality_matrix=pipeline_quality_matrix,
        pipeline_step_audit=pipeline_step_audit,
    )
    blockers_summary = [row["blocking_reason"] for row in pipeline_step_audit if str(row.get("blocking_reason", ""))]
    matrix_by_step = {str(row.get("step_name", "")): str(row.get("quality_label", "")) for row in pipeline_quality_matrix}
    map_step = next((row for row in normalized_pipeline_steps if str(row.get("step_name", "")) == "map"), {})
    diff_step = next((row for row in normalized_pipeline_steps if str(row.get("step_name", "")) == "diff_validate"), {})
    pipeline_review_export_preview = {
        "pipeline_id": active_pipeline_id,
        "latest_pipeline_envelope_summary": {
            "run_id": str(latest_pipeline_envelope.get("run_id", "NOT_COMPUTABLE")),
            "overall_status": str(latest_pipeline_envelope.get("overall_status", "NOT_COMPUTABLE")),
            "final_classification": str(latest_pipeline_envelope.get("final_classification", "NOT_COMPUTABLE")),
            "overall_status_rule": str(latest_pipeline_envelope.get("overall_status_rule", "rollup.unknown")),
            "overall_status_reason": str(latest_pipeline_envelope.get("overall_status_reason", "unknown")),
            "final_result_summary": str(latest_pipeline_envelope.get("final_result_summary", "NOT_COMPUTABLE")),
        },
        "final_summary_block": dict(latest_pipeline_envelope.get("final_summary_block", {})) if isinstance(latest_pipeline_envelope.get("final_summary_block", {}), Mapping) else {},
        "step_exposure_audit": pipeline_step_audit,
        "quality_matrix": pipeline_quality_matrix,
        "upgrade_target_selection": upgrade_targets,
        "blockers_summary": blockers_summary[:8],
        "map_realization_state": {
            "status": str(map_step.get("status", "NOT_COMPUTABLE")),
            "quality_label": matrix_by_step.get("map", "NOT_COMPUTABLE"),
            "output_summary": str(map_step.get("output_summary", ""))[:220],
        },
        "diff_input_quality_state": {
            "status": str(diff_step.get("status", "NOT_COMPUTABLE")),
            "quality_label": matrix_by_step.get("diff_validate", "NOT_COMPUTABLE"),
            "input_context_summary": str((diff_step.get("input_summary", {}) if isinstance(diff_step.get("input_summary", {}), Mapping) else {})).replace("'", "\"")[:220],
        },
        "timestamp": _utc_now(),
        "provenance": "pipeline_hardening.review_export.v3.8.deterministic_bounded",
        "rule_strings": [
            "audit_rule=callable_exposure+step_execution+artifact_presence",
            "quality_rule=explicit_label_matrix_executable_structural_notcomputable_degraded",
            "selection_rule=semantic_priority_then_callable_upgrade_path",
            "rollup_rule=failed_then_notcomputable_then_partial_then_success",
        ],
        "run_id": str(latest_pipeline_envelope.get("run_id", "NOT_COMPUTABLE")),
        "rune_id": "RUNE.PARSE",
        "artifact_id": f"pipeline_review.{datetime.now(timezone.utc).strftime('%Y%m%dt%H%M%SZ').lower()}",
        "ledger_record_ids": [],
        "ledger_artifact_ids": [],
        "correlation_pointers": [],
    }
    pipeline_hardening_workspace_payload = {
        "mode": "runtime",
        "pipeline_status": str(latest_pipeline_envelope.get("overall_status", "NOT_COMPUTABLE")),
        "final_classification": str(latest_pipeline_envelope.get("final_classification", "NOT_COMPUTABLE")),
        "overall_status_reasoning": (
            f"{str(latest_pipeline_envelope.get('overall_status_rule', 'rollup.unknown'))}"
            f"|{str(latest_pipeline_envelope.get('overall_status_reason', 'unknown'))}"
        )[:220],
        "blocking_steps": [str(x) for x in ((latest_pipeline_envelope.get("final_summary_block", {}) if isinstance(latest_pipeline_envelope.get("final_summary_block", {}), Mapping) else {}).get("blocking_steps", [])) if isinstance(x, str)][:5],
        "successful_steps": [str(x) for x in ((latest_pipeline_envelope.get("final_summary_block", {}) if isinstance(latest_pipeline_envelope.get("final_summary_block", {}), Mapping) else {}).get("successful_steps", [])) if isinstance(x, str)][:5],
        "primary_upgrade_target": str(upgrade_targets.get("primary_upgrade_target", "none")),
        "blocker_count": len(blockers_summary),
        "map_quality_label": matrix_by_step.get("map", "NOT_COMPUTABLE"),
        "diff_quality_label": matrix_by_step.get("diff_validate", "NOT_COMPUTABLE"),
        "map_status": str(map_step.get("status", "NOT_COMPUTABLE")),
        "diff_status": str(diff_step.get("status", "NOT_COMPUTABLE")),
        "next_upgrade_target_after_v3_8": str(upgrade_targets.get("secondary_upgrade_target", "")),
        "pipeline_review_export_status": latest_pipeline_review_export_status,
        "pipeline_review_export_path": latest_pipeline_review_export_path or "",
    }
    pipeline_hardening = {
        "pipeline_step_audit": pipeline_step_audit,
        "pipeline_quality_matrix": pipeline_quality_matrix,
        "primary_upgrade_target": str(upgrade_targets.get("primary_upgrade_target", "none")),
        "secondary_upgrade_target": str(upgrade_targets.get("secondary_upgrade_target", "")),
        "upgrade_reason": str(upgrade_targets.get("upgrade_reason", "")),
        "pipeline_review_export_preview": pipeline_review_export_preview,
        "pipeline_review_export_status": latest_pipeline_review_export_status,
        "pipeline_review_export_path": latest_pipeline_review_export_path,
        "pipeline_hardening_workspace_payload": pipeline_hardening_workspace_payload,
    }
    structural_signals = _derive_structural_signals(
        selected_detail=selected_detail,
        pipeline_step_audit=pipeline_step_audit,
        pipeline_quality_matrix=pipeline_quality_matrix,
        runtime_gating=(runtime_corridor.get("runtime_gating", []) if isinstance(runtime_corridor, Mapping) else []),
        ers_review_workspace_payload=(ers_review.get("ers_review_workspace_payload", {}) if isinstance(ers_review, Mapping) else {}),
        latest_pipeline_envelope=latest_pipeline_envelope,
    )
    pressure_friction_detector = _derive_pressure_friction_detector(
        structural_signals=structural_signals,
        selected_run_id=chosen,
    )
    if str(pressure_friction_detector.get("detector_status", "")) == "NOT_COMPUTABLE":
        pressure_friction_detector["not_computable_subcode"] = (
            not_computable_subcodes[0] if not_computable_subcodes else "NC_MISSING_REQUIRED_CONTEXT"
        )
    motif_recurrence_signals = _derive_motif_recurrence_signals(
        structural_signals=structural_signals,
        pressure_friction_detector=pressure_friction_detector,
        pipeline_step_audit=pipeline_step_audit,
        pipeline_quality_matrix=pipeline_quality_matrix,
        pipeline_routing=pipeline_routing,
        ers_review_workspace_payload={
            "transition_log": (
                ers_review.get("ers_transition_log", [])
                if isinstance(ers_review, Mapping)
                else []
            ),
            "drift_label": (
                (ers_review.get("ers_review_workspace_payload", {}) if isinstance(ers_review, Mapping) else {}).get("drift_label", "NOT_COMPUTABLE")
            ),
        },
        runtime_gating=(runtime_corridor.get("runtime_gating", []) if isinstance(runtime_corridor, Mapping) else []),
    )
    motif_recurrence_detector = _derive_motif_recurrence_detector(
        motif_recurrence_signals=motif_recurrence_signals,
        selected_run_id=chosen,
    )
    if str(motif_recurrence_detector.get("detector_status", "")) == "NOT_COMPUTABLE":
        motif_recurrence_detector["not_computable_subcode"] = (
            not_computable_subcodes[0] if not_computable_subcodes else "NC_MISSING_REQUIRED_CONTEXT"
        )
    instability_drift_signals = _derive_instability_drift_signals(
        ers_snapshot_diff=(ers_review.get("ers_snapshot_diff", {}) if isinstance(ers_review, Mapping) else {}),
        ers_transition_log=(ers_review.get("ers_transition_log", []) if isinstance(ers_review, Mapping) else []),
        prior_result_diff=prior_result_diff,
        pipeline_quality_matrix=pipeline_quality_matrix,
        review_history=(decision_layer.get("review_history", []) if isinstance(decision_layer, Mapping) else []),
    )
    instability_drift_detector = _derive_instability_drift_detector(
        instability_drift_signals=instability_drift_signals,
        selected_run_id=chosen,
    )
    if str(instability_drift_detector.get("detector_status", "")) == "NOT_COMPUTABLE":
        instability_drift_detector["not_computable_subcode"] = (
            not_computable_subcodes[0] if not_computable_subcodes else "NC_MISSING_REQUIRED_CONTEXT"
        )
    anomaly_gap_signals = _derive_anomaly_gap_signals(
        selected_detail=selected_detail,
        pipeline_step_audit=pipeline_step_audit,
        pipeline_review_export_path=latest_pipeline_review_export_path,
        ers_review_export_path=latest_ers_review_export_path,
        runtime_corridor=runtime_corridor if isinstance(runtime_corridor, Mapping) else {},
    )
    anomaly_gap_detector = _derive_anomaly_gap_detector(
        anomaly_gap_signals=anomaly_gap_signals,
        selected_run_id=chosen,
    )
    if str(anomaly_gap_detector.get("detector_status", "")) == "NOT_COMPUTABLE":
        anomaly_gap_detector["not_computable_subcode"] = (
            not_computable_subcodes[0] if not_computable_subcodes else "NC_MISSING_REQUIRED_CONTEXT"
        )
    fusion_input_surface = _derive_fusion_input_surface(
        structural_signals=structural_signals,
        pressure_friction_detector=pressure_friction_detector,
        motif_recurrence_detector=motif_recurrence_detector,
        instability_drift_detector=instability_drift_detector,
        anomaly_gap_detector=anomaly_gap_detector,
    )
    signal_sufficiency_surface = _derive_signal_sufficiency_surface(
        selected_run_id=chosen,
        structural_signals=structural_signals,
        pressure_friction_detector=pressure_friction_detector,
        motif_recurrence_detector=motif_recurrence_detector,
        instability_drift_detector=instability_drift_detector,
        anomaly_gap_detector=anomaly_gap_detector,
        not_computable_subcodes=not_computable_subcodes,
        binding_health_surface=binding_health_surface,
    )
    detector_fusion_output = _derive_detector_fusion_output(
        selected_run_id=chosen,
        fusion_input_surface=fusion_input_surface,
        pressure_friction_detector=pressure_friction_detector,
        motif_recurrence_detector=motif_recurrence_detector,
        instability_drift_detector=instability_drift_detector,
        anomaly_gap_detector=anomaly_gap_detector,
        signal_sufficiency_surface=signal_sufficiency_surface,
    )
    if str(detector_fusion_output.get("fused_status", "")) == "NOT_COMPUTABLE":
        detector_fusion_output["not_computable_subcode"] = (
            not_computable_subcodes[0] if not_computable_subcodes else "NC_MISSING_REQUIRED_CONTEXT"
        )
    interpretation_summary = str(detector_fusion_output.get("interpretation_summary", ""))
    detector_export_preview = {
        "run_id": chosen or "NOT_COMPUTABLE",
        "pipeline_id": str(latest_pipeline_envelope.get("pipeline_id", "NOT_COMPUTABLE")),
        "timestamp": _utc_now(),
        "detector_id": str(pressure_friction_detector.get("detector_id", "ABX.STRUCTURAL_PRESSURE.V4_2")),
        "source_context_summary": {
            "selected_run_id": chosen or "",
            "workbench_mode": applied_mode,
            "pipeline_status": str(latest_pipeline_envelope.get("overall_status", "NOT_COMPUTABLE")),
            "ers_drift_label": str((ers_review.get("ers_review_workspace_payload", {}) if isinstance(ers_review, Mapping) else {}).get("drift_label", "NOT_COMPUTABLE")),
        },
        "structural_signals": structural_signals,
        "pressure_friction_detector": pressure_friction_detector,
        "provenance": "operator_console.domain_logic.export.v4.2.bounded_signal_surface",
        "rule_strings": [
            "detector_rule=explicit_ladder_missing_degraded_blocked_transition",
            "label_rule=blocked->BLOCKED else thresholded pressure labels",
            "source_rule=local_runtime_pipeline_review_state_only",
        ],
        "correlation_pointers": [],
        "ledger_record_ids": [],
        "ledger_artifact_ids": [],
    }
    domain_logic_workspace_payload = {
        "mode": "runtime",
        "pressure_label": str(pressure_friction_detector.get("pressure_label", "NOT_COMPUTABLE")),
        "friction_label": str(pressure_friction_detector.get("friction_label", "NOT_COMPUTABLE")),
        "detector_status": str(pressure_friction_detector.get("detector_status", "NOT_COMPUTABLE")),
        "detector_export_status": latest_detector_export_status,
        "detector_export_path": latest_detector_export_path or "",
        "motif_label": str(motif_recurrence_detector.get("motif_label", "NOT_COMPUTABLE")),
        "recurrence_label": str(motif_recurrence_detector.get("recurrence_label", "NOT_COMPUTABLE")),
        "motif_export_status": latest_motif_export_status,
        "motif_export_path": latest_motif_export_path or "",
        "instability_label": str(instability_drift_detector.get("instability_label", "NOT_COMPUTABLE")),
        "drift_label": str(instability_drift_detector.get("drift_label", "NOT_COMPUTABLE")),
        "drift_export_status": latest_drift_export_status,
        "drift_export_path": latest_drift_export_path or "",
        "anomaly_label": str(anomaly_gap_detector.get("anomaly_label", "NOT_COMPUTABLE")),
        "gap_label": str(anomaly_gap_detector.get("gap_label", "NOT_COMPUTABLE")),
        "anomaly_export_status": latest_anomaly_export_status,
        "anomaly_export_path": latest_anomaly_export_path or "",
        "fusion_label": str(detector_fusion_output.get("fused_label", "NOT_COMPUTABLE")),
        "fusion_status": str(detector_fusion_output.get("fused_status", "NOT_COMPUTABLE")),
        "compressed_fusion_reason": str(detector_fusion_output.get("compressed_fusion_reason", "pattern_not_resolved")),
        "fusion_interpretation_summary": interpretation_summary,
        "signal_sufficiency_status": str(signal_sufficiency_surface.get("signal_sufficiency_status", "INSUFFICIENT")),
        "signal_sufficiency_reasons": [str(x) for x in signal_sufficiency_surface.get("signal_sufficiency_reasons", []) if isinstance(x, str)][:5],
        "fusion_export_status": latest_fusion_export_status,
        "fusion_export_path": latest_fusion_export_path or "",
    }
    motif_export_preview = {
        "run_id": chosen or "NOT_COMPUTABLE",
        "pipeline_id": str(latest_pipeline_envelope.get("pipeline_id", "NOT_COMPUTABLE")),
        "timestamp": _utc_now(),
        "detector_id": str(motif_recurrence_detector.get("detector_id", "ABX.MOTIF_RECURRENCE.V4_3")),
        "source_context_summary": {
            "selected_run_id": chosen or "",
            "workbench_mode": applied_mode,
            "pipeline_status": str(latest_pipeline_envelope.get("overall_status", "NOT_COMPUTABLE")),
            "routing_effective_pipeline_id": str(pipeline_routing.get("effective_pipeline_id", "NOT_COMPUTABLE")),
        },
        "signal_extraction_output": motif_recurrence_signals,
        "detector_output": motif_recurrence_detector,
        "provenance": "operator_console.domain_logic.motif_export.v4.3.bounded_signal_surface",
        "rule_strings": [
            "motif_rule=repeat_counts_from_local_runtime_pipeline_review_state",
            "motif_label_rule=explicit_threshold_ladder_sparse_present_dominant",
            "recurrence_rule=none_recurring_persistent_from_repetition_surfaces",
        ],
        "correlation_pointers": [],
        "ledger_record_ids": [],
        "ledger_artifact_ids": [],
        "motif_recurrence_signals": motif_recurrence_signals,
        "motif_recurrence_detector": motif_recurrence_detector,
    }
    drift_export_preview = {
        "run_id": chosen or "NOT_COMPUTABLE",
        "pipeline_id": str(latest_pipeline_envelope.get("pipeline_id", "NOT_COMPUTABLE")),
        "timestamp": _utc_now(),
        "detector_id": str(instability_drift_detector.get("detector_id", "ABX.INSTABILITY_DRIFT.V4_4")),
        "source_context_summary": {
            "selected_run_id": chosen or "",
            "workbench_mode": applied_mode,
            "ers_diff_status": str((ers_review.get("ers_review_workspace_payload", {}) if isinstance(ers_review, Mapping) else {}).get("diff_status", "NOT_COMPUTABLE")),
        },
        "signal_extraction_output": instability_drift_signals,
        "detector_output": instability_drift_detector,
        "provenance": "operator_console.domain_logic.drift_export.v4.4.bounded_signal_surface",
        "rule_strings": [
            "drift_rule=status_queue_transition_quality_review_changes",
            "drift_label_rule=stable_shifting_unstable + none_minor_significant",
        ],
        "correlation_pointers": [],
        "ledger_record_ids": [],
        "ledger_artifact_ids": [],
    }
    anomaly_export_preview = {
        "run_id": chosen or "NOT_COMPUTABLE",
        "pipeline_id": str(latest_pipeline_envelope.get("pipeline_id", "NOT_COMPUTABLE")),
        "timestamp": _utc_now(),
        "detector_id": str(anomaly_gap_detector.get("detector_id", "ABX.ANOMALY_GAP.V4_4")),
        "source_context_summary": {
            "selected_run_id": chosen or "",
            "workbench_mode": applied_mode,
            "pipeline_status": str(latest_pipeline_envelope.get("overall_status", "NOT_COMPUTABLE")),
        },
        "signal_extraction_output": anomaly_gap_signals,
        "detector_output": anomaly_gap_detector,
        "provenance": "operator_console.domain_logic.anomaly_export.v4.4.bounded_signal_surface",
        "rule_strings": [
            "anomaly_rule=missing_artifact_linkage_required_fields_step_pattern_export_mismatch",
            "anomaly_label_rule=none_minor_major + complete_incomplete_broken",
        ],
        "correlation_pointers": [],
        "ledger_record_ids": [],
        "ledger_artifact_ids": [],
    }
    fusion_export_preview = {
        "run_id": chosen or "NOT_COMPUTABLE",
        "pipeline_id": str(latest_pipeline_envelope.get("pipeline_id", "NOT_COMPUTABLE")),
        "timestamp": _utc_now(),
        "source_detector_summaries": {
            "pressure_friction": {
                "pressure_label": str(pressure_friction_detector.get("pressure_label", "NOT_COMPUTABLE")),
                "friction_label": str(pressure_friction_detector.get("friction_label", "NOT_COMPUTABLE")),
            },
            "motif_recurrence": {
                "motif_label": str(motif_recurrence_detector.get("motif_label", "NOT_COMPUTABLE")),
                "recurrence_label": str(motif_recurrence_detector.get("recurrence_label", "NOT_COMPUTABLE")),
            },
            "instability_drift": {
                "instability_label": str(instability_drift_detector.get("instability_label", "NOT_COMPUTABLE")),
                "drift_label": str(instability_drift_detector.get("drift_label", "NOT_COMPUTABLE")),
            },
            "anomaly_gap": {
                "anomaly_label": str(anomaly_gap_detector.get("anomaly_label", "NOT_COMPUTABLE")),
                "gap_label": str(anomaly_gap_detector.get("gap_label", "NOT_COMPUTABLE")),
            },
        },
        "fusion_input_surface": fusion_input_surface,
        "signal_sufficiency_surface": signal_sufficiency_surface,
        "fused_output": detector_fusion_output,
        "interpretation_summary": interpretation_summary,
        "provenance": "operator_console.domain_logic.fusion_export.v4.5.bounded_signal_surface",
        "rule_strings": [
            "fusion_input_rule=existing_detector_outputs_only",
            "fusion_ladder_rule=broken>incomplete>unstable>active>stable>default",
            "interpretation_rule=bounded_template_from_detector_labels_and_fused_reasons",
        ],
        "correlation_pointers": [],
        "ledger_record_ids": [],
        "ledger_artifact_ids": [],
    }
    domain_logic = {
        "structural_signals": structural_signals,
        "pressure_friction_detector": pressure_friction_detector,
        "detector_export_preview": detector_export_preview,
        "detector_export_status": latest_detector_export_status,
        "detector_export_path": latest_detector_export_path,
        "motif_recurrence_signals": motif_recurrence_signals,
        "motif_recurrence_detector": motif_recurrence_detector,
        "motif_export_preview": motif_export_preview,
        "motif_export_status": latest_motif_export_status,
        "motif_export_path": latest_motif_export_path,
        "instability_drift_signals": instability_drift_signals,
        "instability_drift_detector": instability_drift_detector,
        "drift_export_preview": drift_export_preview,
        "drift_export_status": latest_drift_export_status,
        "drift_export_path": latest_drift_export_path,
        "anomaly_gap_signals": anomaly_gap_signals,
        "anomaly_gap_detector": anomaly_gap_detector,
        "anomaly_export_preview": anomaly_export_preview,
        "anomaly_export_status": latest_anomaly_export_status,
        "anomaly_export_path": latest_anomaly_export_path,
        "fusion_input_surface": fusion_input_surface,
        "signal_sufficiency_surface": signal_sufficiency_surface,
        "detector_fusion_output": detector_fusion_output,
        "interpretation_summary": interpretation_summary,
        "fusion_export_preview": fusion_export_preview,
        "fusion_export_status": latest_fusion_export_status,
        "fusion_export_path": latest_fusion_export_path,
        "domain_logic_workspace_payload": domain_logic_workspace_payload,
        "updated_domain_logic_workspace_payload": domain_logic_workspace_payload,
    }
    linked_envelope = (
        pipeline_envelope_linkage.get("bound_pipeline_envelope", {})
        if isinstance(pipeline_envelope_linkage.get("bound_pipeline_envelope", {}), Mapping)
        else {}
    )
    linked_steps = (
        pipeline_envelope_linkage.get("bound_pipeline_step_records", [])
        if isinstance(pipeline_envelope_linkage.get("bound_pipeline_step_records", []), list)
        else []
    )
    final_state_source_envelope = linked_envelope or latest_pipeline_envelope
    final_state_source_steps = linked_steps or normalized_pipeline_steps
    pipeline_final_state_surface = _derive_pipeline_final_state(
        latest_pipeline_envelope=final_state_source_envelope,
        pipeline_step_records=final_state_source_steps,
        pipeline_review_workspace_payload=pipeline_hardening_workspace_payload,
    )
    pipeline_final_state_health_surface = _derive_pipeline_final_state_health_surface(
        pipeline_final_state=pipeline_final_state_surface,
        ledger_bridge=ledger_bridge,
    )
    pipeline_final_state_surface["final_state_derivable"] = bool(binding_envelope_health_surface.get("final_state_derivable", False))
    pipeline_final_state_surface["synthesis_blocked_by_binding"] = bool(
        binding_envelope_health_surface.get("synthesis_blocked_by_binding", True)
    )
    pipeline_final_state_surface["final_state_source_available"] = bool(
        pipeline_envelope_linkage.get("final_state_source_available", False)
    )
    pipeline_final_state_surface["final_state_bindable"] = bool(
        binding_envelope_health_surface.get("final_state_bindable", False)
    )
    pipeline_final_state_surface["run_id_match_status"] = str(
        binding_envelope_health_surface.get("run_id_match_status", "INVOCATION_MISSING")
    )
    pipeline_final_state_surface["binding_resolution_source"] = str(
        pipeline_envelope_linkage.get("resolution_source", "none")
    )
    pipeline_unresolved_subcode = (
        (refined_binding_nc_subcodes[0] if refined_binding_nc_subcodes else "NC_PIPELINE_STATUS_UNRESOLVED")
        if not bool(pipeline_final_state_surface.get("pipeline_status_resolved", False))
        else ""
    )
    synthesis_input_surface = _derive_abraxas_synthesis_input_surface(
        selected_run_id=chosen,
        latest_pipeline_envelope=latest_pipeline_envelope,
        pipeline_routing=pipeline_routing,
        governance=governance,
        runtime_corridor=runtime_corridor if isinstance(runtime_corridor, Mapping) else {},
        decision_workspace_payload=decision_workspace_payload,
        detector_fusion_output=detector_fusion_output,
        pipeline_final_state=pipeline_final_state_surface,
        pipeline_unresolved_subcode=pipeline_unresolved_subcode,
        not_computable_subcodes=not_computable_subcodes,
        attention_queue=attention_queue,
        suggested_next_step=suggested_next_step,
        signal_sufficiency_surface=signal_sufficiency_surface,
    )
    synthesis_output = _derive_abraxas_synthesis_output(
        synthesis_input_surface=synthesis_input_surface,
        selected_run_id=chosen,
    )
    if str(synthesis_output.get("synthesis_status", "")) == "NOT_COMPUTABLE":
        synthesis_output["not_computable_subcode"] = (
            pipeline_unresolved_subcode or (not_computable_subcodes[0] if not_computable_subcodes else "NC_MISSING_REQUIRED_CONTEXT")
        )
    synthesis_structured_payload = _legacy_synthesis_structured_payload_adapter(
        synthesis_output=synthesis_output,
        synthesis_input_surface=synthesis_input_surface,
    )
    synthesis_export_preview = {
        "run_id": chosen or "NOT_COMPUTABLE",
        "pipeline_id": str(latest_pipeline_envelope.get("pipeline_id", "NOT_COMPUTABLE")),
        "timestamp": _utc_now(),
        "synthesis_input_surface": synthesis_input_surface,
        "structured_signal_payload": synthesis_structured_payload,
        "synthesis_label": str(synthesis_output.get("synthesis_label", "NOT_COMPUTABLE")),
        "synthesis_reasons": list(synthesis_output.get("synthesis_reasons", []))[:6],
        "synthesis_blockers": list(synthesis_output.get("synthesis_blockers", []))[:6],
        "synthesis_next_step": str(synthesis_output.get("synthesis_next_step", "")),
        "synthesis_rule_precedence_note": str(synthesis_output.get("synthesis_rule_precedence_note", "")),
        "interpretation_summary": str(synthesis_output.get("interpretation_summary", "")),
        "selected_context": {
            "workbench_mode": applied_mode,
            "routing_effective_pipeline_id": str(pipeline_routing.get("effective_pipeline_id", "NOT_COMPUTABLE")),
            "runtime_action_name": str((runtime_corridor.get("runtime_workspace_payload", {}) if isinstance(runtime_corridor.get("runtime_workspace_payload", {}), Mapping) else {}).get("action_name", "NOT_COMPUTABLE")),
            "fusion_label": str(detector_fusion_output.get("fused_label", "NOT_COMPUTABLE")),
        },
        "provenance": "operator_console.abraxas_synthesis.export.v4.6.bounded_surface",
        "rule_strings": [
            "synthesis_input_rule=project_existing_pipeline_routing_governance_runtime_fusion_state",
            "synthesis_label_rule=deterministic_precedence_not_computable_blocked_incomplete_unstable_friction_ready_active",
            "synthesis_summary_rule=bounded_what_happened_means_blockers_next_step_template",
        ],
        "correlation_pointers": [],
        "ledger_record_ids": [],
        "ledger_artifact_ids": [],
    }
    synthesis_workspace_payload = {
        "mode": "runtime",
        "synthesis_label": str(synthesis_output.get("synthesis_label", "NOT_COMPUTABLE")),
        "synthesis_status": str(synthesis_output.get("synthesis_status", "NOT_COMPUTABLE")),
        "synthesis_next_step": str(synthesis_output.get("synthesis_next_step", "")),
        "synthesis_export_status": latest_synthesis_export_status,
        "synthesis_export_path": latest_synthesis_export_path or "",
        "structured_signal_payload": synthesis_structured_payload,
        "fusion_label": str(detector_fusion_output.get("fused_label", "NOT_COMPUTABLE")),
        "pipeline_id": str(latest_pipeline_envelope.get("pipeline_id", "NOT_COMPUTABLE")),
        "pipeline_final_status": str(pipeline_final_state_surface.get("pipeline_final_status", "NOT_COMPUTABLE")),
    }
    final_card_reasons = _bounded_list_or_none([str(x) for x in synthesis_output.get("synthesis_reasons", []) if isinstance(x, str)])
    final_card_blockers = _bounded_list_or_none([str(x) for x in synthesis_output.get("synthesis_blockers", []) if isinstance(x, str)])
    final_card_pipeline_id = str(latest_pipeline_envelope.get("pipeline_id", "NOT_COMPUTABLE"))
    final_card_runtime_status = str(
        (runtime_corridor.get("runtime_workspace_payload", {}) if isinstance(runtime_corridor.get("runtime_workspace_payload", {}), Mapping) else {}).get(
            "outcome_status", "NOT_COMPUTABLE"
        )
    )
    final_card_fused_label = str(detector_fusion_output.get("fused_label", "NOT_COMPUTABLE"))
    final_abraxas_output_card = {
        "synthesis_label": str(synthesis_output.get("synthesis_label", "NOT_COMPUTABLE")),
        "short_reasons": final_card_reasons,
        "blockers": final_card_blockers,
        "next_step": str(synthesis_output.get("synthesis_next_step", "")),
        "pipeline_id": final_card_pipeline_id,
        "runtime_status": final_card_runtime_status,
        "fused_detector_label": final_card_fused_label,
        "signal_sufficiency_status": str(signal_sufficiency_surface.get("signal_sufficiency_status", "INSUFFICIENT")),
        "status_line": (
            f"pipeline={final_card_pipeline_id}; runtime={final_card_runtime_status}; fused={final_card_fused_label}"
        )[:220],
        "reason_line": ", ".join(final_card_reasons[:3])[:180],
        "blocker_line": ", ".join(final_card_blockers[:3])[:180],
        "interpretation_summary": str(synthesis_output.get("interpretation_summary", "")),
        "structured_signal_payload": synthesis_structured_payload,
    }
    abraxas_synthesis = {
        "synthesis_input_surface": synthesis_input_surface,
        "structured_signal_payload": synthesis_structured_payload,
        "synthesis_label": str(synthesis_output.get("synthesis_label", "NOT_COMPUTABLE")),
        "synthesis_reasons": list(synthesis_output.get("synthesis_reasons", []))[:6],
        "synthesis_blockers": list(synthesis_output.get("synthesis_blockers", []))[:6],
        "synthesis_next_step": str(synthesis_output.get("synthesis_next_step", "")),
        "synthesis_rule_precedence_note": str(synthesis_output.get("synthesis_rule_precedence_note", "")),
        "interpretation_summary": str(synthesis_output.get("interpretation_summary", "")),
        "synthesis_export_preview": synthesis_export_preview,
        "synthesis_export_status": latest_synthesis_export_status,
        "synthesis_export_path": latest_synthesis_export_path,
        "synthesis_workspace_payload": synthesis_workspace_payload,
        "final_abraxas_output_card": final_abraxas_output_card,
    }
    pipeline_final_state_export_preview = {
        "run_id": chosen or "NOT_COMPUTABLE",
        "timestamp": _utc_now(),
        "pipeline_id": str(latest_pipeline_envelope.get("pipeline_id", "NOT_COMPUTABLE")),
        "pipeline_final_state": pipeline_final_state_surface,
        "final_state_health_surface": pipeline_final_state_health_surface,
        "synthesis_ready": bool(pipeline_final_state_health_surface.get("synthesis_ready", False)),
        "resolution_source": str(pipeline_final_state_health_surface.get("resolution_source", "none")),
        "provenance": "operator_console.pipeline_final_state.export.v4.9.bounded_surface",
        "rule_strings": [
            "final_state_rule=envelope_then_terminal_steps_then_not_computable",
            "health_rule=pipeline_status_resolved_drives_synthesis_readiness",
            "subcode_rule=NC_PIPELINE_STATUS_UNRESOLVED_when_pipeline_final_state_missing",
        ],
        "correlation_pointers": [],
        "ledger_record_ids": [],
        "ledger_artifact_ids": [],
    }
    pipeline_final_state_workspace_payload = {
        "mode": "runtime",
        "pipeline_final_status": str(pipeline_final_state_surface.get("pipeline_final_status", "NOT_COMPUTABLE")),
        "pipeline_completion_state": str(pipeline_final_state_surface.get("pipeline_completion_state", "UNKNOWN")),
        "pipeline_status_resolved": bool(pipeline_final_state_surface.get("pipeline_status_resolved", False)),
        "final_state_derivable": bool(pipeline_final_state_surface.get("final_state_derivable", False)),
        "final_state_bindable": bool(pipeline_final_state_surface.get("final_state_bindable", False)),
        "synthesis_blocked_by_binding": bool(pipeline_final_state_surface.get("synthesis_blocked_by_binding", True)),
        "final_state_source_available": bool(pipeline_final_state_surface.get("final_state_source_available", False)),
        "run_id_match_status": str(pipeline_final_state_surface.get("run_id_match_status", "INVOCATION_MISSING")),
        "emitted_envelope_run_id": str(pipeline_envelope_linkage.get("pipeline_envelope_run_id", "NOT_COMPUTABLE")),
        "synthesis_ready": bool(pipeline_final_state_health_surface.get("synthesis_ready", False)),
        "blocking_reason": str(pipeline_final_state_health_surface.get("blocking_reason", "none")),
        "final_state_export_status": latest_pipeline_final_state_export_status,
        "final_state_export_path": latest_pipeline_final_state_export_path or "",
    }
    pipeline_final_state = {
        "pipeline_final_status": str(pipeline_final_state_surface.get("pipeline_final_status", "NOT_COMPUTABLE")),
        "pipeline_completion_state": str(pipeline_final_state_surface.get("pipeline_completion_state", "UNKNOWN")),
        "pipeline_resolution_reason": str(pipeline_final_state_surface.get("pipeline_resolution_reason", "pipeline_status_not_resolved")),
        "pipeline_status_resolved": bool(pipeline_final_state_surface.get("pipeline_status_resolved", False)),
        "synthesis_ready": bool(pipeline_final_state_health_surface.get("synthesis_ready", False)),
        "blocking_reason": str(pipeline_final_state_health_surface.get("blocking_reason", "none")),
        "resolution_source": str(pipeline_final_state_health_surface.get("resolution_source", "none")),
        "pipeline_success_flags": list(pipeline_final_state_surface.get("pipeline_success_flags", []))[:8],
        "pipeline_failure_flags": list(pipeline_final_state_surface.get("pipeline_failure_flags", []))[:8],
        "final_state_health_surface": pipeline_final_state_health_surface,
        "final_state_export_preview": pipeline_final_state_export_preview,
        "final_state_export_status": latest_pipeline_final_state_export_status,
        "final_state_export_path": latest_pipeline_final_state_export_path,
        "pipeline_final_state_workspace_payload": pipeline_final_state_workspace_payload,
    }
    binding_export_preview = {
        "run_id": chosen or "NOT_COMPUTABLE",
        "timestamp": _utc_now(),
        "binding_surface": bound_run_context,
        "ledger_bridge_surface": ledger_bridge,
        "not_computable_subcodes": not_computable_subcodes[:5],
        "binding_health_surface": binding_health_surface,
        "blocker_summary": list(binding_health_surface.get("reasons", []))[:5],
        "provenance": "operator_console.binding_restoration.export.v4.7.bounded_surface",
        "rule_strings": [
            "binding_rule=canonical_artifact_then_resultspack_fallback_then_missing",
            "ledger_bridge_rule=artifact_counts_then_local_ledger_match_then_missing",
            "nc_subcode_rule=known_specific_causes_only_with_bounded_priority_order",
        ],
        "correlation_pointers": [],
        "ledger_record_ids": [],
        "ledger_artifact_ids": [],
    }
    binding_envelope_export_preview = {
        "run_id": chosen or "NOT_COMPUTABLE",
        "timestamp": _utc_now(),
        "operator_bound_run_context": operator_bound_run_context,
        "pipeline_envelope_linkage": pipeline_envelope_linkage,
        "binding_envelope_health_surface": binding_envelope_health_surface,
        "refined_binding_nc_subcodes": refined_binding_nc_subcodes[:5],
        "blocker_summary": [
            str(binding_envelope_health_surface.get("blocking_reason", "none")),
            str(operator_bound_run_context.get("operator_binding_reason", "none")),
            str(pipeline_envelope_linkage.get("envelope_binding_reason", "none")),
        ][:5],
        "provenance": "operator_console.binding_restoration.pipeline_envelope.export.v5.0.bounded_surface",
        "rule_strings": [
            "operator_binding_rule=invocation_then_envelope_then_artifact_then_export_then_unbound",
            "envelope_binding_rule=latest_envelope_then_pipeline_artifact_then_unbound",
            "subcode_rule=NC_OPERATOR_RUN_UNBOUND_then_NC_PIPELINE_ENVELOPE_UNBOUND_then_NC_FINAL_STATE_SOURCE_MISSING",
        ],
        "correlation_pointers": [],
        "ledger_record_ids": [],
        "ledger_artifact_ids": [],
    }
    invocation_run_id_state = {
        "invocation_run_id": str(operator_bound_run_context.get("invocation_run_id", "NOT_COMPUTABLE")),
        "invocation_run_id_source": str(operator_bound_run_context.get("invocation_run_id_source", "none")),
        "invocation_run_id_status": str(operator_bound_run_context.get("invocation_run_id_status", "MISSING")),
    }
    pipeline_envelope_run_id_state = {
        "pipeline_envelope_run_id": str(pipeline_envelope_linkage.get("pipeline_envelope_run_id", "NOT_COMPUTABLE")),
        "pipeline_envelope_run_id_status": str(pipeline_envelope_linkage.get("pipeline_envelope_run_id_status", "MISSING")),
    }
    run_id_propagation_export_preview = {
        "run_id": chosen or "NOT_COMPUTABLE",
        "timestamp": _utc_now(),
        "invocation_run_id_state": invocation_run_id_state,
        "pipeline_envelope_run_id_state": pipeline_envelope_run_id_state,
        "run_id_match_status": str(binding_envelope_health_surface.get("run_id_match_status", "INVOCATION_MISSING")),
        "final_state_bindable": bool(binding_envelope_health_surface.get("final_state_bindable", False)),
        "propagation_nc_subcodes": refined_binding_nc_subcodes[:5],
        "blocker_summary": [
            str(binding_envelope_health_surface.get("blocking_reason", "none")),
            str(pipeline_envelope_linkage.get("envelope_binding_reason", "none")),
        ][:5],
        "provenance": "operator_console.binding_restoration.run_id_propagation.export.v5.0.1",
        "rule_strings": [
            "invocation_rule=single_canonical_invocation_run_id_with_explicit_source_status",
            "match_rule=prefer_exact_invocation_run_id_to_envelope_run_id_match",
            "subcode_rule=NC_INVOCATION_RUN_ID_UNPROPAGATED_only_when_invocation_present_and_envelope_unbound_mismatch",
        ],
        "correlation_pointers": [],
        "ledger_record_ids": [],
        "ledger_artifact_ids": [],
    }
    pipeline_envelope_run_id_repair_export_preview = {
        "run_id": chosen or "NOT_COMPUTABLE",
        "timestamp": _utc_now(),
        "invocation_run_id_state": invocation_run_id_state,
        "emitted_envelope_run_id_state": pipeline_envelope_run_id_state,
        "run_id_match_status": str(binding_envelope_health_surface.get("run_id_match_status", "INVOCATION_MISSING")),
        "final_state_bindable": bool(binding_envelope_health_surface.get("final_state_bindable", False)),
        "propagation_nc_subcodes": refined_binding_nc_subcodes[:5],
        "blocker_summary": [
            str(binding_envelope_health_surface.get("blocking_reason", "none")),
            str(pipeline_envelope_linkage.get("envelope_binding_reason", "none")),
        ][:5],
        "provenance": "operator_console.binding_restoration.pipeline_envelope_run_id_repair.export.v5.0.2",
        "rule_strings": [
            "emission_rule=pipeline envelope run_id persists canonical invocation_run_id",
            "lookup_rule=operator linkage prefers exact invocation_run_id to emitted envelope run_id match",
            "subcode_rule=NC_PIPELINE_ENVELOPE_RUN_ID_MISSING when envelope exists without canonical run_id",
        ],
        "correlation_pointers": [],
        "ledger_record_ids": [],
        "ledger_artifact_ids": [],
    }
    binding_restoration = {
        "bound_run_context": bound_run_context,
        "operator_bound_run_context": operator_bound_run_context,
        "pipeline_envelope_linkage": pipeline_envelope_linkage,
        "invocation_run_id_state": invocation_run_id_state,
        "pipeline_envelope_run_id_state": pipeline_envelope_run_id_state,
        "run_id_match_status": str(binding_envelope_health_surface.get("run_id_match_status", "INVOCATION_MISSING")),
        "final_state_bindable": bool(binding_envelope_health_surface.get("final_state_bindable", False)),
        "ledger_bridge": ledger_bridge,
        "not_computable_subcodes": not_computable_subcodes[:5],
        "binding_health_surface": binding_health_surface,
        "binding_envelope_health_surface": binding_envelope_health_surface,
        "refined_binding_nc_subcodes": refined_binding_nc_subcodes[:5],
        "propagation_nc_subcodes": refined_binding_nc_subcodes[:5],
        "binding_export_preview": binding_export_preview,
        "binding_export_status": latest_binding_export_status,
        "binding_export_path": latest_binding_export_path,
        "binding_envelope_export_preview": binding_envelope_export_preview,
        "binding_envelope_export_status": latest_binding_envelope_export_status,
        "binding_envelope_export_path": latest_binding_envelope_export_path,
        "run_id_propagation_export_preview": run_id_propagation_export_preview,
        "run_id_propagation_export_status": latest_run_id_propagation_export_status,
        "run_id_propagation_export_path": latest_run_id_propagation_export_path,
        "pipeline_envelope_run_id_repair_export_preview": pipeline_envelope_run_id_repair_export_preview,
        "pipeline_envelope_run_id_repair_export_status": latest_pipeline_envelope_run_id_repair_export_status,
        "pipeline_envelope_run_id_repair_export_path": latest_pipeline_envelope_run_id_repair_export_path,
    }
    required_context_matrix = _derive_required_context_matrix(
        selected_run_id=chosen,
        bound_run_context=bound_run_context,
        pipeline_workspace_payload=pipeline_workspace_payload,
        detector_fusion_output=detector_fusion_output,
        synthesis_input_surface=synthesis_input_surface,
    )
    projected_context = _derive_projected_context(
        bound_run_context=bound_run_context,
        pipeline_workspace_payload=pipeline_workspace_payload,
        latest_pipeline_envelope=latest_pipeline_envelope,
        latest_pipeline_records=normalized_pipeline_steps,
        runtime_workspace_payload=runtime_workspace_payload,
        compare_delta_summary=compare_delta_summary,
    )
    context_readiness_surface = _derive_context_readiness_surface(required_context_matrix=required_context_matrix)
    projected_context_structured_payload = {
        "raw_signal": {
            "run_id": str(bound_run_context.get("bound_run_id", "NOT_COMPUTABLE")),
            "pipeline_status": str(pipeline_workspace_payload.get("pipeline_status", "NOT_COMPUTABLE")),
            "runtime_outcome_status": str(runtime_workspace_payload.get("outcome_status", "NOT_COMPUTABLE")),
        },
        "structural_model": {
            "pipeline_summary": str(projected_context.get("normalized_pipeline_summary", "")),
            "step_rollup_summary": str(projected_context.get("normalized_step_rollup_summary", "")),
            "artifact_summary": str(projected_context.get("compact_artifact_summary", "")),
        },
        "optional_lenses": {
            "runtime_summary": str(projected_context.get("bounded_runtime_result_summary", "")),
            "comparison_summary": str(projected_context.get("bounded_comparison_summary", "")),
        },
        "claim_status": {
            "label": "READY" if bool(context_readiness_surface.get("synthesis_context_ready", False)) else "INCOMPLETE",
            "status": "SUCCESS",
        },
        "omissions": [],
    }
    refined_not_computable_subcodes = _derive_refined_not_computable_subcodes(
        observed_subcodes=not_computable_subcodes[:5],
        required_context_matrix=required_context_matrix,
        compare_delta_summary=compare_delta_summary,
    )
    context_export_preview = {
        "run_id": chosen or "NOT_COMPUTABLE",
        "timestamp": _utc_now(),
        "required_context_matrix": required_context_matrix,
        "projected_context": projected_context,
        "structured_signal_payload": projected_context_structured_payload,
        "context_readiness_surface": context_readiness_surface,
        "observed_not_computable_subcodes": not_computable_subcodes[:5],
        "refined_not_computable_subcodes": refined_not_computable_subcodes[:8],
        "blockers_summary": [
            str((required_context_matrix.get("detector_layer", {}) or {}).get("blocking_reason", "none")),
            str((required_context_matrix.get("fusion_layer", {}) or {}).get("blocking_reason", "none")),
            str((required_context_matrix.get("synthesis_layer", {}) or {}).get("blocking_reason", "none")),
        ][:5],
        "provenance": "operator_console.context_restoration.export.v4.8.bounded_surface",
        "rule_strings": [
            "required_context_rule=layer readiness derives only from selected local run/binding/pipeline/runtime/fusion surfaces",
            "projection_rule=bounded summaries from local state without semantic fabrication",
            "refined_nc_rule=only assign context-specific subcodes when layer-level cause is explicit",
        ],
    }
    context_workspace_payload = {
        "mode": "runtime",
        "detector_context_ready": bool(context_readiness_surface.get("detector_context_ready", False)),
        "fusion_context_ready": bool(context_readiness_surface.get("fusion_context_ready", False)),
        "synthesis_context_ready": bool(context_readiness_surface.get("synthesis_context_ready", False)),
        "structured_signal_payload": projected_context_structured_payload,
        "context_export_status": latest_context_export_status,
        "context_export_path": latest_context_export_path or "",
    }
    context_restoration = {
        "required_context_matrix": required_context_matrix,
        "projected_context": projected_context,
        "structured_signal_payload": projected_context_structured_payload,
        "context_readiness_surface": context_readiness_surface,
        "refined_not_computable_subcodes": refined_not_computable_subcodes[:8],
        "context_export_preview": context_export_preview,
        "context_export_status": latest_context_export_status,
        "context_export_path": latest_context_export_path,
        "context_workspace_payload": context_workspace_payload,
    }
    resolved_viz_mode = _sanitize_viz_mode(viz_mode)
    viz_payloads = _derive_viz_payloads(
        closure_status=closure_status,
        snapshot_header=snapshot_header,
        governance=governance,
        selected_run_detail=selected_detail,
        compare_strip=compare_strip,
        compare_delta_summary=compare_delta_summary,
        evidence_delta_preview=evidence_delta_preview,
        attention_queue=attention_queue,
        highlights=highlights,
        recent_activity=recent_activity,
        execution_ledger=execution_ledger,
        decision_layer=decision_layer,
    )
    viz_export_preview = {
        "viz_mode": resolved_viz_mode,
        "viz_payloads": viz_payloads,
        "selected_context": {
            "selected_run_id": chosen or "",
            "compare_run_id": selected_comparison_run_id or "",
            "baseline_run_id": baseline_run_id or "",
            "workbench_mode": applied_mode,
        },
        "summary_status": {
            "closure_status": closure_status,
            "policy_mode": str(policy_surface.get("policy_mode", "review_only")),
            "attention_count": len(attention_queue),
            "execution_ledger_count": len(execution_ledger),
        },
        "timestamp": _utc_now(),
    }
    viz_workspace_payload = {
        "mode": "viz",
        "current_viz_mode": resolved_viz_mode,
        "payload_ready": resolved_viz_mode in viz_payloads,
        "compare_enabled": bool(viz_payloads.get("compare", {}).get("enabled", False)),
        "viz_export_status": viz_export_status,
    }
    viz_integration = {
        "viz_mode": resolved_viz_mode,
        "viz_modes_allowed": ["weather", "trace", "compare"],
        "viz_payloads": viz_payloads,
        "viz_export_preview": viz_export_preview,
        "viz_export_status": viz_export_status,
        "viz_export_path": viz_export_path,
        "viz_workspace_payload": viz_workspace_payload,
    }
    routed_render = _route_viz_render(viz_mode=resolved_viz_mode, viz_payloads=viz_payloads)
    viz_render_export_preview = {
        "viz_mode": str(routed_render.get("viz_render_mode", resolved_viz_mode)),
        "source_viz_payload": dict(routed_render.get("viz_render_payload", {})),
        "render_output": dict(routed_render.get("viz_render_output", {})),
        "selected_context": {
            "selected_run_id": chosen or "",
            "compare_run_id": selected_comparison_run_id or "",
            "baseline_run_id": baseline_run_id or "",
        },
        "status": str((routed_render.get("viz_render_output", {}) or {}).get("status", "ready")),
        "provenance": "operator_console.viz_render.v2.7.1.mode_routed",
        "timestamp": _utc_now(),
    }
    viz_render_workspace_payload = {
        "mode": "viz",
        "viz_render_mode": str(routed_render.get("viz_render_mode", resolved_viz_mode)),
        "has_render_output": bool(routed_render.get("viz_render_output", {})),
        "viz_render_export_status": viz_render_export_status,
    }
    viz_render = {
        "viz_render_mode": str(routed_render.get("viz_render_mode", resolved_viz_mode)),
        "viz_render_payload": dict(routed_render.get("viz_render_payload", {})),
        "viz_render_output": dict(routed_render.get("viz_render_output", {})),
        "viz_render_export_preview": viz_render_export_preview,
        "viz_render_export_status": viz_render_export_status,
        "viz_render_export_path": viz_render_export_path,
        "viz_render_workspace_payload": viz_render_workspace_payload,
    }
    resolved_report_export_paths = {
        "session_report": str((report_export_paths or {}).get("session_report", "")),
        "decision_summary": str((report_export_paths or {}).get("decision_summary", "")),
        "viz_summary": str((report_export_paths or {}).get("viz_summary", "")),
        "closeout_bundle": str((report_export_paths or {}).get("closeout_bundle", "")),
        "markdown_report": str((report_export_paths or {}).get("markdown_report", "")),
    }
    session_report_preview = {
        "session_summary": dict(session_continuity.get("session_summary", {})),
        "decision_timeline": list(session_continuity.get("decision_timeline", []))[:15],
        "execution_summary": {
            "visible_run_count": len(visible_run_ids),
            "actions_recorded_count": len(normalized_action_history),
        },
        "governance_summary": {
            "policy_mode": str(policy_surface.get("policy_mode", "review_only")),
            "gating_snapshot": list(governance.get("action_gating", []))[:5],
        },
        "latest_result_packet_summary": {
            "status": str(result_packet.get("status", "not_requested")),
            "action_name": str(result_packet.get("action_name", "")),
            "run_id": str(result_packet.get("run_id", "")),
        },
        "provenance": "operator_console.reporting.session.v2.8.0",
        "timestamp": _utc_now(),
    }
    decision_summary_preview = {
        "action_name": str(result_packet.get("action_name", "")),
        "run_id": chosen or "",
        "outcome_classification": dict(outcome_classification),
        "decision_label": str(decision_layer.get("decision_label", "INVESTIGATE")),
        "failure_triage": dict(failure_triage),
        "provenance_summary": dict(result_provenance_panel),
        "suggested_next_step": str(suggested_next_step),
        "timestamp": _utc_now(),
    }
    viz_summary_preview = {
        "viz_mode": str(viz_render.get("viz_render_mode", resolved_viz_mode)),
        "render_output": dict(viz_render.get("viz_render_output", {})),
        "source_payload_summary": dict(viz_render.get("viz_render_payload", {})),
        "selected_context": {
            "selected_run_id": chosen or "",
            "compare_run_id": selected_comparison_run_id or "",
        },
        "timestamp": _utc_now(),
    }
    closeout_bundle_preview = {
        "session_report": session_report_preview,
        "latest_decision_summary": decision_summary_preview,
        "latest_viz_summary": viz_summary_preview,
        "governance_snapshot": {
            "policy_mode": str(policy_surface.get("policy_mode", "review_only")),
            "guard_conditions": list(governance.get("guard_conditions", []))[:5],
        },
        "selected_context": {
            "selected_run_id": chosen or "",
            "compare_run_id": selected_comparison_run_id or "",
            "workbench_mode": applied_mode,
        },
        "timestamp": _utc_now(),
        "provenance": "operator_console.reporting.closeout.v2.8.0",
    }
    session_summary_line = (
        f"session actions={session_report_preview['session_summary'].get('actions_executed_count', 0)}; "
        f"decisions={session_report_preview['session_summary'].get('decisions_recorded_count', 0)}; "
        f"policy={session_report_preview['governance_summary']['policy_mode']}"
    )[:220]
    decision_summary_line = (
        f"decision={decision_summary_preview['decision_label']}; "
        f"next={decision_summary_preview['suggested_next_step']}"
    )[:220]
    viz_summary_line = (
        f"viz_mode={viz_summary_preview['viz_mode']}; "
        f"render_status={str((viz_summary_preview.get('render_output', {}) or {}).get('status', 'ready'))}"
    )[:220]
    closeout_summary_line = (
        f"closeout policy={str((closeout_bundle_preview.get('governance_snapshot', {}) or {}).get('policy_mode', 'review_only'))}; "
        f"run={chosen or 'NOT_COMPUTABLE'}; compare={selected_comparison_run_id or 'none'}"
    )[:220]
    markdown_preview = "\n".join(
        [
            "# Abraxas Operator Report",
            "",
            "## Executive Summary",
            f"- synthesis_label: {str(synthesis_output.get('synthesis_label', 'NOT_COMPUTABLE'))}",
            f"- fused_detector_label: {str(detector_fusion_output.get('fused_label', 'NOT_COMPUTABLE'))}",
            f"- pipeline_final_status: {str(pipeline_final_state_surface.get('pipeline_final_status', 'NOT_COMPUTABLE'))}",
            f"- routing_effective_pipeline_id: {str(pipeline_routing.get('effective_pipeline_id', 'NOT_COMPUTABLE'))}",
            "",
            "## Session Summary",
            f"- actions_executed_count: {session_report_preview['session_summary'].get('actions_executed_count', 0)}",
            f"- decisions_recorded_count: {session_report_preview['session_summary'].get('decisions_recorded_count', 0)}",
            f"- latest_action_outcome: {session_report_preview['session_summary'].get('latest_action_outcome', 'unknown')}",
            "",
            "## Decision Summary",
            f"- decision_label: {decision_summary_preview['decision_label']}",
            f"- suggested_next_step: {decision_summary_preview['suggested_next_step']}",
            "",
            "## Viz Summary",
            f"- viz_mode: {viz_summary_preview['viz_mode']}",
            f"- render_status: {str((viz_summary_preview.get('render_output', {}) or {}).get('status', 'ready'))}",
            "",
            "## Governance Snapshot",
            f"- policy_mode: {session_report_preview['governance_summary']['policy_mode']}",
            "",
            "## Context",
            f"- selected_run_id: {chosen or ''}",
            f"- compare_run_id: {selected_comparison_run_id or ''}",
            f"- workbench_mode: {applied_mode}",
            "",
            "## Provenance",
            "- operator_console.reporting.v2.8.0",
        ]
    )
    reporting_workspace_payload = {
        "mode": "report",
        "report_export_status": report_export_status,
        "report_paths_written_count": len([x for x in resolved_report_export_paths.values() if x]),
        "selected_run_id": chosen or "",
    }
    reporting = {
        "session_report_preview": session_report_preview,
        "decision_summary_preview": decision_summary_preview,
        "viz_summary_preview": viz_summary_preview,
        "closeout_bundle_preview": closeout_bundle_preview,
        "session_summary_line": session_summary_line,
        "decision_summary_line": decision_summary_line,
        "viz_summary_line": viz_summary_line,
        "closeout_summary_line": closeout_summary_line,
        "markdown_preview": markdown_preview,
        "report_export_status": report_export_status,
        "report_export_paths": resolved_report_export_paths,
        "reporting_workspace_payload": reporting_workspace_payload,
    }

    return ViewState(
        mode="snapshot",
        selected_run_id=chosen,
        available_runs=run_ids,
        visible_run_ids=visible_run_ids,
        closure_status=closure_status,
        focus_filters={"health": applied_health_filter, "run_query": applied_run_query, "sort_mode": applied_sort_mode},
        run_health_summaries=full_run_health_summaries,
        visible_run_health_summaries=visible_summaries,
        selected_run_artifact_summary=artifact_summary,
        selected_run_validator_summary=validator_summary,
        selected_run_detail=selected_detail,
        last_action=dict(last_action) if last_action is not None else None,
        recent_activity_limit=recent_activity_limit,
        recent_activity=recent_activity,
        suggested_run_id=suggested_run_id,
        suggestion_reason=suggestion_reason,
        weakness_reasons=weakness_reasons,
        suggested_next_step=suggested_next_step,
        evidence_drilldown=evidence_drilldown,
        snapshot_header=snapshot_header,
        comparison_run_id=selected_comparison_run_id,
        compare_strip=compare_strip,
        compare_delta_summary=compare_delta_summary,
        suggested_compare_run_id=suggested_compare_run_id,
        suggested_compare_reason=suggested_compare_reason,
        evidence_delta_preview=evidence_delta_preview,
        pinned_run_ids=normalized_pins,
        pin_panel=pin_panel,
        highlights_limit=highlights_limit,
        highlights=highlights,
        action_history_limit=action_history_limit,
        action_history=normalized_action_history,
        workbench_header=workbench_header,
        attention_queue=attention_queue,
        triage_limit_per_bucket=triage_limit_per_bucket,
        triage_panel=triage_panel,
        pinned_run_deep_cards=pinned_run_deep_cards,
        baseline_run_id=baseline_run_id,
        baseline_reason=baseline_reason,
        action_safety_envelope=action_safety_envelope,
        latest_snapshot_report_path=latest_snapshot_report_path,
        latest_snapshot_report_status=latest_snapshot_report_status,
        export_preview=export_preview,
        snapshot_report_payload=snapshot_report_payload,
        snapshot_recall_limit=recall_limit,
        snapshot_recall_items=normalized_recall_items,
        loaded_snapshot_path=loaded_snapshot_path,
        loaded_snapshot_status=loaded_snapshot_status,
        workbench_mode=applied_mode,
        workbench_modes_allowed=["overview", "runs", "compare", "watch", "export", "runflow", "decision", "session", "governance", "viz", "report", "ers", "runtime", "domain_logic"],
        attention_actions_enabled=attention_actions_enabled,
        attention_action_hint=attention_action_hint,
        baseline_locked=baseline_locked,
        baseline_locked_run_id=baseline_locked_run_id if baseline_locked else None,
        baseline_lock_reason=baseline_lock_reason,
        compare_to_baseline_ready=compare_to_baseline_ready,
        control_plane=control_plane,
        action_presets=action_presets,
        selected_preset_id=resolved_selected_preset_id,
        dry_run_preview=dry_run_preview,
        result_packet=result_packet,
        retry_reapply=retry_reapply,
        execution_ledger_limit=execution_ledger_limit,
        execution_ledger=execution_ledger,
        execution_report_preview=execution_report_preview,
        latest_execution_report_path=latest_execution_report_path,
        latest_execution_report_status=latest_execution_report_status,
        runbook_card=runbook_card,
        handoff_bundle_preview=handoff_bundle_preview,
        latest_handoff_bundle_path=latest_handoff_bundle_path,
        latest_handoff_bundle_status=latest_handoff_bundle_status,
        checkpoint_preview=checkpoint_preview,
        latest_checkpoint_path=latest_checkpoint_path,
        latest_checkpoint_status=latest_checkpoint_status,
        restored_checkpoint_path=restored_checkpoint_path,
        restored_checkpoint_status=restored_checkpoint_status,
        quick_actions=quick_actions,
        runtime_adapter_audit=runtime_adapter_audit,
        runtime_safety_notes=runtime_safety_notes,
        runflow_cards=runflow_cards,
        runtime_result_drilldown=runtime_result_drilldown,
        outcome_classification=outcome_classification,
        prior_result_diff=prior_result_diff,
        action_stability=action_stability,
        failure_triage=failure_triage,
        result_provenance_panel=result_provenance_panel,
        runtime_outcome_review_workspace=runtime_outcome_review_workspace,
        decision_layer=decision_layer,
        decision_workspace_payload=decision_workspace_payload,
        session_continuity=session_continuity,
        governance=governance,
        viz_integration=viz_integration,
        viz_render=viz_render,
        reporting=reporting,
        adapter_health_checks=adapter_health_checks,
        runflow_workspace=runflow_workspace,
        ers_integration=ers_integration,
        ers_review=ers_review,
        runtime_corridor=runtime_corridor,
        abraxas_pipeline=abraxas_pipeline,
        pipeline_final_state=pipeline_final_state,
        pipeline_hardening=pipeline_hardening,
        pipeline_routing=pipeline_routing,
        domain_logic=domain_logic,
        abraxas_synthesis=abraxas_synthesis,
        binding_restoration=binding_restoration,
        context_restoration=context_restoration,
        session_context=resolved_session_context,
        data_provenance={
            "artifacts_runs_scanned": len(artifacts),
            "validator_outputs_scanned": len(validators),
            "audit_artifacts_scanned": len(audit_paths),
            "audit_artifact_paths": audit_paths,
            "health_label_rule": "strong=SUCCESS+validator_present+pointers>0+timestamp; partial=any signal; weak=all missing",
            "focus_sort_rule": "latest_first=timestamp desc with NOT_COMPUTABLE last; run_id_asc=lexicographic run_id",
            "action_feedback_rule": "status from exit_code/env markers; run_id parsed from *.artifact.json path in output tails",
            "suggestion_rule": "prefer validator status SUCCESS|VALID with pointers>0, tie latest timestamp then run_id, else first visible",
            "outcome_classification_rule": "SUCCESS=status success-like + run_id + artifact; PARTIAL=incomplete success surfaces; FAILED=failed/error or error_info_without_artifact; NOT_COMPUTABLE=not_requested/preview/missing execution identity",
            "stability_rule": "window=5 same action outcomes; stable=all success; degraded=majority failed or latest failed; mixed=otherwise",
            "prior_diff_rule": "prior=previous same action+preset excluding same identity; compare outcome/run/artifact/output_count/error_state",
            "decision_rule": "ACCEPT=success+stable+complete; WATCH=success+mixed; RETRY=failed_or_partial+missing_required_surfaces_without_error; INVESTIGATE=otherwise",
            "review_history_rule": "bounded recent action history sorted timestamp desc with stable tie-breakers; each row derives outcome+decision deterministically",
            "session_timeline_rule": "timeline combines current decision + recent decision artifacts + review history; bounded newest-first deterministic sorting",
            "session_diff_rule": "compare current decision against prior same run_id else same action_name else inert",
            "policy_mode_rule": "review_only when no bounded action context; bounded_runtime when allowlisted runtime actions available; decision_review when decision/session modes active",
            "action_gating_rule": "enabled only when policy permits + action allowlisted + preview supported + required run/retry conditions pass",
            "viz_adapter_rule": "viz payloads are deterministic projections of operator/runtime/review/decision/governance state with bounded slices",
            "viz_mode_rule": "allowed viz modes are weather|trace|compare; invalid mode defaults to weather",
            "viz_render_rule": "viz render output is mode-routed deterministic text structure from sanitized viz payload without heavy charting",
            "reporting_rule": "reporting artifacts are bounded deterministic summaries derived from existing session/decision/viz/governance state",
            "ers_catalog_rule": "ERS uses bounded static candidate catalog (compliance/generalized_coverage/validator/closure_audit) with no hidden scheduler expansion",
            "ers_queue_rule": "ERS queue partitions candidates into runnable vs blocked via ordered deterministic gating checks and fixed list limits",
            "ers_trigger_rule": "ERS trigger is explicit operator action only; no background processing or automatic queue advancement",
            "ers_diff_rule": "ERS review diff compares current state to most recent prior ERS snapshot with deterministic changed/unchanged counters and bounded item transition list",
            "ers_drift_rule": "ERS drift labels: NOT_COMPUTABLE(no prior), DEGRADED(blocked up or runnable down or next regressed), STABLE(no changes), SHIFTED(otherwise)",
            "ers_transition_rule": "ERS transition log combines diff-derived transitions and explicit ERS trigger history, sorted newest-first with bounded size",
            "runtime_corridor_registry_rule": "runtime corridor registry is static bounded allowlisted entries mapped to existing adapters only",
            "runtime_corridor_gating_rule": "runtime entry invokable only when policy+allowlist+required context+adapter+preview+ers conditions pass",
            "runtime_corridor_export_rule": "runtime corridor export emits bounded deterministic snapshot artifact with governance+ERS context and linkage placeholders",
            "pipeline_path_rule": "pipeline path is static ingest->parse->map->diff_validate->review_audit; parse is hardened via deterministic projection while map remains explicit NOT_COMPUTABLE unless callable exposure exists",
            "pipeline_export_rule": "pipeline export artifact contains bounded envelope + step records + lineage/governance/runtime context",
            "pipeline_hardening_audit_rule": "step audit derives callable exposure + artifact presence + current step status with explicit blocking reason",
            "pipeline_hardening_selection_rule": "upgrade target selection uses deterministic semantic priority and callable-upgrade-path preference",
            "pipeline_map_rule": "map projection deterministically derives bounded entity-relation associations from parse projection keys and selected_run_id tokens",
            "pipeline_diff_input_rule": "diff input summary explicitly includes bounded map context (relation_count/entities) when available",
            "pipeline_routing_rule": "pipeline routing derives suitability matrix + ordered recommendation and explicit manual override precedence",
            "pipeline_final_state_rule": "pipeline final-state resolution derives status/completion/flags from envelope+terminal steps+review with explicit fallback ladder",
            "pipeline_final_state_health_rule": "final-state health exposes pipeline_status_resolved+synthesis_ready+blocking_reason with NC_PIPELINE_STATUS_UNRESOLVED when unresolved",
            "domain_logic_structural_rule": "structural signals derive deterministic bounded counts from pipeline/runtime/ers/review surfaces only",
            "domain_logic_detector_rule": "pressure/friction detector uses explicit threshold ladder over missing/degraded/blocked/imbalance/transition signals",
            "domain_logic_export_rule": "detector signal export emits bounded artifact with run_id/pipeline_id/provenance and explicit linkage placeholders",
            "domain_logic_motif_rule": "motif signals derive bounded recurrence counts from repeated tokens/entities/relations/blockers/transitions/routing patterns",
            "domain_logic_motif_detector_rule": "motif detector uses explicit sparse/present/dominant and none/recurring/persistent threshold ladder",
            "domain_logic_instability_drift_rule": "instability/drift signals derive deterministic counts from status/queue/transition/result/quality/review changes",
            "domain_logic_instability_drift_detector_rule": "instability/drift detector uses explicit stable/shifting/unstable and none/minor/significant thresholds",
            "domain_logic_anomaly_gap_rule": "anomaly/gap signals derive deterministic counts from missing artifacts/linkage/required fields/step pattern/export mismatch",
            "domain_logic_anomaly_gap_detector_rule": "anomaly/gap detector uses explicit none/minor/major and complete/incomplete/broken thresholds",
            "domain_logic_fusion_input_rule": "fusion input surface only projects existing detector-family outputs and structural summary without new extraction",
            "domain_logic_fusion_rule": "fusion output follows deterministic precedence ladder broken>incomplete>unstable>active>stable>default",
            "domain_logic_interpretation_rule": "interpretation summary is bounded template text from fused label plus detector family labels and fused reasons",
            "abraxas_synthesis_input_rule": "synthesis input projects bounded pipeline/routing/governance/runtime/fusion/session surfaces without duplicating raw internals",
            "abraxas_synthesis_label_rule": "synthesis label follows explicit deterministic precedence not_computable>blocked>incomplete>unstable>friction>ready>active",
            "abraxas_synthesis_summary_rule": "synthesis summary exposes label/reasons/blockers/next-step through bounded deterministic templates",
            "binding_restoration_rule": "binding restoration derives run context, ledger bridge, and not-computable subcodes from local artifact/ledger surfaces with explicit precedence",
            "binding_envelope_linkage_rule": "operator binding resolves invocation->envelope->artifact->export and links envelope/steps before final-state synthesis projection",
            "context_restoration_required_rule": "required context matrix explicitly reports ready/missing/available/blocking_reason for detector+fusion+synthesis layers",
            "context_restoration_projection_rule": "projected context uses bounded deterministic pipeline/step/artifact/runtime/comparison summaries from local state only",
            "context_restoration_readiness_rule": "readiness surface is derived directly from required context matrix with explicit reasons when false and projection notes when true",
            "context_restoration_subcode_rule": "refined NC context subcodes are appended only for explicit known layer-context gaps",
        },
    )


def run_compliance_probe_command() -> Dict[str, Any]:
    command = ["python", "-m", "aal_core.runes.compliance_probe"]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    status = "SUCCESS" if completed.returncode == 0 else "FAILED"
    return {
        "status": status,
        "command": command,
        "exit_code": completed.returncode,
        "stdout_tail": completed.stdout[-1200:],
        "stderr_tail": completed.stderr[-1200:],
        "timestamp_utc": _utc_now(),
    }
