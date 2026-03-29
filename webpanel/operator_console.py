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
    adapter_health_checks: Dict[str, Any]
    runflow_workspace: Dict[str, Any]
    session_context: Dict[str, str]
    data_provenance: Dict[str, Any]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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
    allowed = ["overview", "runs", "compare", "watch", "export", "runflow"]
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
            if str(result_packet.get("status", "")) in {"SUCCESS", "FAILED", "NOT_COMPUTABLE", "preview_only"}
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
        workbench_modes_allowed=["overview", "runs", "compare", "watch", "export", "runflow"],
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
