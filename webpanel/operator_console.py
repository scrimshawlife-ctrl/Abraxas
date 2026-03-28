from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional


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
    last_action: Optional[Mapping[str, Any]] = None,
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
