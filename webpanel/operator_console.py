from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from abx.execution_validator import emit_validation_result, validate_run

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
    session_context: Dict[str, str]
    data_provenance: Dict[str, Any]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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
            "run_compliance_probe",
            "run_generalized_coverage_probe",
            "run_execution_validator",
            "run_closure_audit",
            "export_operator_snapshot",
        ],
        "command_preview": {
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
    allowed = ["overview", "runs", "compare", "watch", "export", "runflow", "decision", "session", "governance", "viz", "report"]
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
            "out/validators/execution-validation-*.json"
            if preset["action_name"] == "run_execution_validator"
            else (
                "artifacts_seal/audits/operator_closure_audit/closure_audit.*.json"
                if preset["action_name"] == "run_closure_audit"
                else "artifacts_seal/runs/compliance_probe/*.artifact.json"
            )
        )
    )
    return {
        "enabled": True,
        "status": "preview_only",
        "preset_id": preset["preset_id"],
        "action_name": preset["action_name"],
        "resolved_command_preview": (
            "python -m aal_core.runes.compliance_probe"
            if preset["action_name"] in {"run_compliance_probe", "run_generalized_coverage_probe"}
            else (
                "python -c 'from abx.execution_validator import validate_run, emit_validation_result'"
                if preset["action_name"] == "run_execution_validator"
                else ("python scripts/run_system_closure_audit.py" if preset["action_name"] == "run_closure_audit" else "write operator snapshot artifact")
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


_RUNTIME_ADAPTERS: Dict[str, Any] = {
    "run_compliance_probe": _adapter_run_compliance_probe,
    "run_generalized_coverage_probe": _adapter_run_compliance_probe,
    "run_execution_validator": _adapter_run_execution_validator,
    "run_closure_audit": _adapter_run_closure_audit,
}

_RUNTIME_ADAPTER_META: Dict[str, Dict[str, str]] = {
    "export_operator_snapshot": {"adapter_name": "adapter.export_operator_snapshot", "invocation_mode": "direct_callable"},
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
    return {
        "adapter_name": str(response.get("adapter_name", getattr(adapter, "__name__", ""))),
        "attempted_at": str(response.get("attempted_at", attempted_at)),
        "outcome_status": str(response.get("outcome_status", "FAILED")),
        "run_id": str(response.get("run_id", "")),
        "artifact_paths": [str(x) for x in response.get("artifact_paths", [])[:5]],
        "summary": str(response.get("summary", "")),
        "error_info": str(response.get("error_info", "")),
    }


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
            "status": "pass" if workbench_mode in {"overview", "runs", "compare", "watch", "export", "runflow", "decision", "session", "governance"} else "fail",
            "explanation": "Workbench mode must match an approved governance mode.",
        },
    ]
    return guards


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
        "summary_line": f"activity={len(activity)} decisions={len(decisions)} ledger={len(ledger)}",
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
    markdown_preview = "\n".join(
        [
            "# Operator Report",
            "",
            "## Session Summary",
            f"- actions_executed_count: {session_report_preview['session_summary'].get('actions_executed_count', 0)}",
            f"- decisions_recorded_count: {session_report_preview['session_summary'].get('decisions_recorded_count', 0)}",
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
        workbench_modes_allowed=["overview", "runs", "compare", "watch", "export", "runflow", "decision", "session", "governance", "viz", "report"],
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
