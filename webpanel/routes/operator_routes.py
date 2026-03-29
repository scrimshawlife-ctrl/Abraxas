from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Request
from fastapi.responses import HTMLResponse

from ..operator_console import (
    build_view_state,
    execute_runtime_adapter,
    resolve_compare_run_id_for_apply,
    write_operator_ers_snapshot_artifact,
    write_operator_ers_review_artifact,
    write_operator_markdown_report,
    write_operator_report_artifact,
    write_viz_render_artifact,
)
from ..panel_context import templates, require_token, _panel_host, _panel_port, _panel_token, _token_enabled

_OPERATOR_LOCAL_STATE: dict[str, dict[str, object]] = {}
_ERS_TRIGGER_ALLOWLIST: dict[str, str] = {
    "ers.item.compliance_probe": "run_compliance_probe",
    "ers.item.generalized_coverage_probe": "run_generalized_coverage_probe",
    "ers.item.execution_validator": "run_execution_validator",
    "ers.item.closure_audit": "run_closure_audit",
}


def _state_bucket(request: Request) -> dict[str, object]:
    client = getattr(request, "client", None)
    key = f"{getattr(client, 'host', 'local')}:{getattr(client, 'port', '0')}"
    if key not in _OPERATOR_LOCAL_STATE:
        _OPERATOR_LOCAL_STATE[key] = {"context": {}, "pinned_run_ids": [], "action_history": []}
    return _OPERATOR_LOCAL_STATE[key]


def _append_action_history(bucket: dict[str, object], action: dict[str, object], limit: int = 20) -> None:
    history = list(bucket.get("action_history", []))
    history.insert(
        0,
        {
            "timestamp": str(action.get("attempted_at", "NOT_COMPUTABLE")),
            "action_name": str(action.get("action_name", "run_compliance_probe")),
            "preset_id": str(action.get("preset_id", "")),
            "adapter_name": str(action.get("adapter_name", "")),
            "run_id": str(action.get("triggered_run_id", "") or ""),
            "outcome_status": str(action.get("outcome_status", "UNKNOWN")),
            "artifact_ref": str(action.get("artifact_path", "")),
            "summary": str(action.get("message", "")),
        },
    )
    bucket["action_history"] = history[:limit]


def _result_packet(
    *,
    status: str,
    preset_id: str,
    action_name: str,
    adapter_name: str = "",
    attempted_at: str = "",
    run_id: str = "",
    artifact_path: str = "",
    artifact_paths: list[str] | None = None,
    error_info: str = "",
    summary: str = "",
) -> dict[str, object]:
    return {
        "status": status,
        "preset_id": preset_id,
        "action_name": action_name,
        "adapter_name": adapter_name,
        "attempted_at": attempted_at,
        "run_id": run_id,
        "artifact_path": artifact_path,
        "artifact_paths": list(artifact_paths or ([] if not artifact_path else [artifact_path]))[:5],
        "error_info": error_info,
        "summary": summary,
    }


def _resolve_preset(action_presets: list[dict[str, object]], preset_id: str | None) -> dict[str, object] | None:
    if not preset_id:
        return action_presets[0] if action_presets else None
    return next((item for item in action_presets if str(item.get("preset_id", "")) == preset_id), None)


def _write_operator_snapshot_report(export_preview: dict[str, object]) -> tuple[str | None, str]:
    root = Path("artifacts_seal") / "operator_snapshots"
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = root / f"operator_snapshot.{stamp}.json"
    path = base
    index = 1
    while path.exists():
        path = root / f"operator_snapshot.{stamp}.{index}.json"
        index += 1
    payload = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "ruleset_version": "v1.7.5",
        "source": "operator_console",
        **export_preview,
    }
    path.write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8")
    return path.as_posix(), "written"


def _write_execution_report(payload: dict[str, object]) -> tuple[str | None, str]:
    root = Path("artifacts_seal") / "operator_reports"
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = root / f"execution_report.{stamp}.json"
    path = base
    index = 1
    while path.exists():
        path = root / f"execution_report.{stamp}.{index}.json"
        index += 1
    artifact = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "ruleset_version": "v1.9.0",
        "source": "operator_console",
        **payload,
    }
    path.write_text(json.dumps(artifact, sort_keys=True, indent=2), encoding="utf-8")
    return path.as_posix(), "written"


def _write_handoff_bundle(payload: dict[str, object]) -> tuple[str | None, str]:
    root = Path("artifacts_seal") / "operator_handoff"
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = root / f"handoff_bundle.{stamp}.json"
    path = base
    index = 1
    while path.exists():
        path = root / f"handoff_bundle.{stamp}.{index}.json"
        index += 1
    artifact = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "ruleset_version": "v1.9.0",
        "source": "operator_console",
        **payload,
    }
    path.write_text(json.dumps(artifact, sort_keys=True, indent=2), encoding="utf-8")
    return path.as_posix(), "written"


def _write_operator_checkpoint(payload: dict[str, str]) -> tuple[str | None, str]:
    root = Path("artifacts_seal") / "operator_checkpoints"
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = root / f"operator_checkpoint.{stamp}.json"
    path = base
    index = 1
    while path.exists():
        path = root / f"operator_checkpoint.{stamp}.{index}.json"
        index += 1
    artifact = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "ruleset_version": "v1.9.0",
        "source": "operator_console",
        **payload,
    }
    path.write_text(json.dumps(artifact, sort_keys=True, indent=2), encoding="utf-8")
    return path.as_posix(), "written"


def _write_operator_decision(payload: dict[str, object]) -> tuple[str | None, str]:
    root = Path("artifacts_seal") / "operator_decisions"
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = str(payload.get("run_id", "") or "UNAVAILABLE").replace("/", "_")
    base = root / f"{stamp}.{run_id}.decision.json"
    path = base
    index = 1
    while path.exists():
        path = root / f"{stamp}.{run_id}.{index}.decision.json"
        index += 1
    artifact = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "ruleset_version": "v2.3.0",
        "source": "operator_console",
        **payload,
    }
    path.write_text(json.dumps(artifact, sort_keys=True, indent=2), encoding="utf-8")
    return path.as_posix(), "written"


def _write_review_checkpoint(payload: dict[str, str]) -> tuple[str | None, str]:
    root = Path("artifacts_seal") / "operator_checkpoints"
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = root / f"{stamp}.review_checkpoint.json"
    path = base
    index = 1
    while path.exists():
        path = root / f"{stamp}.{index}.review_checkpoint.json"
        index += 1
    artifact = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "ruleset_version": "v2.3.0",
        "source": "operator_console",
        **payload,
    }
    path.write_text(json.dumps(artifact, sort_keys=True, indent=2), encoding="utf-8")
    return path.as_posix(), "written"


def _load_review_checkpoint(path: str) -> tuple[dict[str, str], str]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError:
        return {}, "not_found"
    except json.JSONDecodeError:
        return {}, "invalid"
    filters = payload.get("focus_filters", {})
    return {
        "selected_run_id": str(payload.get("selected_run_id", "")),
        "compare_run_id": str(payload.get("compare_run_id", "")),
        "baseline_run_id": str(payload.get("baseline_run_id", "")),
        "classification": str(payload.get("classification", "")),
        "decision": str(payload.get("decision", "")),
        "health": str(filters.get("health", "all")) if isinstance(filters, dict) else "all",
        "run_query": str(filters.get("run_query", "")) if isinstance(filters, dict) else "",
        "sort_mode": str(filters.get("sort_mode", "latest_first")) if isinstance(filters, dict) else "latest_first",
        "selected_preset_id": str(payload.get("selected_preset_id", "")),
        "workbench_mode": str(payload.get("workbench_mode", "decision")),
    }, "loaded"


def _write_session_closeout(payload: dict[str, object]) -> tuple[str | None, str]:
    root = Path("artifacts_seal") / "operator_sessions"
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = root / f"{stamp}.session_closeout.json"
    path = base
    index = 1
    while path.exists():
        path = root / f"{stamp}.{index}.session_closeout.json"
        index += 1
    artifact = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "ruleset_version": "v2.4.0",
        "source": "operator_console",
        **payload,
    }
    path.write_text(json.dumps(artifact, sort_keys=True, indent=2), encoding="utf-8")
    return path.as_posix(), "written"


def _load_decision_artifact(path: str) -> tuple[dict[str, str], str]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError:
        return {}, "not_found"
    except json.JSONDecodeError:
        return {}, "invalid"
    outcome = payload.get("outcome_classification", {})
    decision = payload.get("decision", {})
    return {
        "run_id": str(payload.get("run_id", "")),
        "action_name": str(payload.get("action_name", "")),
        "outcome_label": str((outcome or {}).get("label", "")) if isinstance(outcome, dict) else "",
        "decision_label": str((decision or {}).get("label", "")) if isinstance(decision, dict) else "",
        "suggested_next_step": str(payload.get("suggested_next_step", "")),
    }, "loaded"


def _write_policy_snapshot(payload: dict[str, object]) -> tuple[str | None, str]:
    root = Path("artifacts_seal") / "operator_policy"
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = root / f"{stamp}.policy_snapshot.json"
    path = base
    index = 1
    while path.exists():
        path = root / f"{stamp}.{index}.policy_snapshot.json"
        index += 1
    artifact = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "ruleset_version": "v2.5.0",
        "source": "operator_console",
        **payload,
    }
    path.write_text(json.dumps(artifact, sort_keys=True, indent=2), encoding="utf-8")
    return path.as_posix(), "written"


def _load_policy_snapshot(path: str) -> tuple[dict[str, str], str]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError:
        return {}, "not_found"
    except json.JSONDecodeError:
        return {}, "invalid"
    surface = payload.get("policy_surface", {})
    context = payload.get("context", {})
    return {
        "policy_mode": str((surface or {}).get("policy_mode", "")) if isinstance(surface, dict) else "",
        "policy_summary": str((surface or {}).get("policy_summary", "")) if isinstance(surface, dict) else "",
        "selected_run_id": str((context or {}).get("selected_run_id", "")) if isinstance(context, dict) else "",
        "compare_run_id": str((context or {}).get("compare_run_id", "")) if isinstance(context, dict) else "",
        "workbench_mode": str((context or {}).get("workbench_mode", "governance")) if isinstance(context, dict) else "governance",
    }, "loaded"


def _write_viz_state(payload: dict[str, object]) -> tuple[str | None, str]:
    root = Path("artifacts_seal") / "operator_viz"
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = root / f"{stamp}.viz_state.json"
    path = base
    index = 1
    while path.exists():
        path = root / f"{stamp}.{index}.viz_state.json"
        index += 1
    artifact = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "ruleset_version": "v2.6.0",
        "source": "operator_console",
        **payload,
    }
    path.write_text(json.dumps(artifact, sort_keys=True, indent=2), encoding="utf-8")
    return path.as_posix(), "written"


def _write_viz_render(payload: dict[str, object]) -> tuple[str | None, str]:
    return write_viz_render_artifact(preview=payload)


def _write_operator_report_artifact(*, suffix: str, payload: dict[str, object]) -> tuple[str | None, str]:
    return write_operator_report_artifact(suffix=suffix, payload=payload)


def _write_markdown_report(markdown: str) -> tuple[str | None, str]:
    return write_operator_markdown_report(markdown=markdown)


def _load_operator_checkpoint(path: str) -> tuple[dict[str, str], str]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError:
        return {}, "not_found"
    except json.JSONDecodeError:
        return {}, "invalid"
    return {
        "selected_run_id": str(payload.get("selected_run_id", "")),
        "compare_run_id": str(payload.get("compare_run_id", "")),
        "health": str(payload.get("health", "all")),
        "run_query": str(payload.get("run_query", "")),
        "sort_mode": str(payload.get("sort_mode", "latest_first")),
        "selected_preset_id": str(payload.get("selected_preset_id", "")),
        "baseline_locked_run_id": str(payload.get("baseline_locked_run_id", "")),
    }, "loaded"


def _list_snapshot_reports(limit: int = 10) -> list[dict[str, str]]:
    root = Path("artifacts_seal") / "operator_snapshots"
    if not root.exists():
        return []
    items: list[dict[str, str]] = []
    for path in sorted(root.glob("operator_snapshot*.json"), reverse=True):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        items.append(
            {
                "path": path.as_posix(),
                "generated_at": str(payload.get("generated_at", "NOT_COMPUTABLE")),
                "selected_run_id": str(payload.get("selected_run_id", "")),
                "compare_run_id": str(payload.get("compare_run_id", "")),
                "baseline_run_id": str(payload.get("baseline_run_id", "")),
            }
        )
    return items[:limit]


def _load_snapshot(path: str) -> tuple[dict[str, str], str]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError:
        return {}, "not_found"
    except json.JSONDecodeError:
        return {}, "invalid"
    return {
        "selected_run_id": str(payload.get("selected_run_id", "")),
        "compare_run_id": str(payload.get("compare_run_id", "")),
        "health": str(payload.get("focus_filters", {}).get("health", "all")),
        "run_query": str(payload.get("focus_filters", {}).get("run_query", "")),
        "sort_mode": str(payload.get("focus_filters", {}).get("sort_mode", "latest_first")),
    }, "loaded"


def _view_from_request(request: Request, selected_run_id: str | None = None):
    bucket = _state_bucket(request)
    saved_context = dict(bucket.get("context", {}))
    selected = selected_run_id or request.query_params.get("run_id")
    health = request.query_params.get("health") or str(saved_context.get("health", "all"))
    run_query = request.query_params.get("run_query") or str(saved_context.get("run_query", ""))
    sort_mode = request.query_params.get("sort_mode") or str(saved_context.get("sort_mode", "latest_first"))
    compare_run_id = request.query_params.get("compare_run_id") or str(saved_context.get("compare_run_id", "")) or None
    mode = request.query_params.get("mode") or str(saved_context.get("mode", "overview"))
    selected_preset_id = request.query_params.get("preset_id") or str(bucket.get("selected_preset_id", "")) or None

    apply_suggested_compare = request.query_params.get("apply_suggested_compare") == "1"
    focus_attention = request.query_params.get("focus_attention")
    lock_baseline = request.query_params.get("lock_baseline")
    unlock_baseline = request.query_params.get("unlock_baseline") == "1"
    load_snapshot = request.query_params.get("load_snapshot")
    export_snapshot = request.query_params.get("export_snapshot") == "1"
    export_execution_report = request.query_params.get("export_execution_report") == "1"
    export_handoff_bundle = request.query_params.get("export_handoff_bundle") == "1"
    save_checkpoint = request.query_params.get("save_checkpoint") == "1"
    restore_checkpoint = request.query_params.get("restore_checkpoint")
    export_decision = request.query_params.get("export_decision") == "1"
    save_review_checkpoint = request.query_params.get("save_review_checkpoint") == "1"
    restore_review_checkpoint = request.query_params.get("restore_review_checkpoint")
    export_session_closeout = request.query_params.get("export_session_closeout") == "1"
    load_decision_artifact = request.query_params.get("load_decision_artifact")
    load_review_checkpoint = request.query_params.get("load_review_checkpoint")
    export_policy_snapshot = request.query_params.get("export_policy_snapshot") == "1"
    load_policy_snapshot = request.query_params.get("load_policy_snapshot")
    viz_mode = request.query_params.get("viz_mode")
    export_viz_state = request.query_params.get("export_viz_state") == "1"
    export_viz_render = request.query_params.get("export_viz_render") == "1"
    export_session_report = request.query_params.get("export_session_report") == "1"
    export_decision_summary = request.query_params.get("export_decision_summary") == "1"
    export_viz_summary = request.query_params.get("export_viz_summary") == "1"
    export_closeout_bundle = request.query_params.get("export_closeout_bundle") == "1"
    export_markdown_report = request.query_params.get("export_markdown_report") == "1"
    export_ers_snapshot = request.query_params.get("export_ers_snapshot") == "1"
    export_ers_review = request.query_params.get("export_ers_review") == "1"
    trigger_ers_item = request.query_params.get("trigger_ers_item")

    pin_run_id = request.query_params.get("pin_run_id")
    unpin_run_id = request.query_params.get("unpin_run_id")
    pinned_run_ids = [str(x) for x in bucket.get("pinned_run_ids", []) if isinstance(x, str)]
    if pin_run_id and pin_run_id not in pinned_run_ids:
        pinned_run_ids.append(pin_run_id)
    if unpin_run_id:
        pinned_run_ids = [x for x in pinned_run_ids if x != unpin_run_id]
    bucket["pinned_run_ids"] = pinned_run_ids

    if unlock_baseline:
        bucket["baseline_locked_run_id"] = ""
    if lock_baseline:
        bucket["baseline_locked_run_id"] = lock_baseline

    loaded_snapshot_path = None
    loaded_snapshot_status = "not_requested"
    if load_snapshot:
        loaded_ctx, loaded_snapshot_status = _load_snapshot(load_snapshot)
        if loaded_ctx:
            selected = loaded_ctx["selected_run_id"] or selected
            compare_run_id = loaded_ctx["compare_run_id"] or compare_run_id
            health = loaded_ctx["health"] or health
            run_query = loaded_ctx["run_query"] or run_query
            sort_mode = loaded_ctx["sort_mode"] or sort_mode
            loaded_snapshot_path = load_snapshot

    restored_checkpoint_path = None
    restored_checkpoint_status = "not_requested"
    if restore_checkpoint:
        loaded_checkpoint, restored_checkpoint_status = _load_operator_checkpoint(restore_checkpoint)
        if loaded_checkpoint:
            selected = loaded_checkpoint["selected_run_id"] or selected
            compare_run_id = loaded_checkpoint["compare_run_id"] or compare_run_id
            health = loaded_checkpoint["health"] or health
            run_query = loaded_checkpoint["run_query"] or run_query
            sort_mode = loaded_checkpoint["sort_mode"] or sort_mode
            selected_preset_id = loaded_checkpoint["selected_preset_id"] or selected_preset_id
            bucket["baseline_locked_run_id"] = loaded_checkpoint["baseline_locked_run_id"] or ""
            restored_checkpoint_path = restore_checkpoint
            bucket["restored_checkpoint_path"] = restored_checkpoint_path
            bucket["restored_checkpoint_status"] = restored_checkpoint_status
    restored_review_checkpoint_path = None
    restored_review_checkpoint_status = "not_requested"
    if restore_review_checkpoint:
        loaded_review_checkpoint, restored_review_checkpoint_status = _load_review_checkpoint(restore_review_checkpoint)
        if loaded_review_checkpoint:
            selected = loaded_review_checkpoint["selected_run_id"] or selected
            compare_run_id = loaded_review_checkpoint["compare_run_id"] or compare_run_id
            health = loaded_review_checkpoint["health"] or health
            run_query = loaded_review_checkpoint["run_query"] or run_query
            sort_mode = loaded_review_checkpoint["sort_mode"] or sort_mode
            selected_preset_id = loaded_review_checkpoint["selected_preset_id"] or selected_preset_id
            mode = loaded_review_checkpoint["workbench_mode"] or mode
            restored_review_checkpoint_path = restore_review_checkpoint
            bucket["restored_review_checkpoint_path"] = restored_review_checkpoint_path
            bucket["restored_review_checkpoint_status"] = restored_review_checkpoint_status
    if load_review_checkpoint and not restore_review_checkpoint:
        loaded_review_checkpoint, restored_review_checkpoint_status = _load_review_checkpoint(load_review_checkpoint)
        if loaded_review_checkpoint:
            selected = loaded_review_checkpoint["selected_run_id"] or selected
            compare_run_id = loaded_review_checkpoint["compare_run_id"] or compare_run_id
            health = loaded_review_checkpoint["health"] or health
            run_query = loaded_review_checkpoint["run_query"] or run_query
            sort_mode = loaded_review_checkpoint["sort_mode"] or sort_mode
            selected_preset_id = loaded_review_checkpoint["selected_preset_id"] or selected_preset_id
            mode = loaded_review_checkpoint["workbench_mode"] or mode
            restored_review_checkpoint_path = load_review_checkpoint
            bucket["restored_review_checkpoint_path"] = restored_review_checkpoint_path
            bucket["restored_review_checkpoint_status"] = restored_review_checkpoint_status

    recall_status = "not_requested"
    recall_path = None
    if load_decision_artifact:
        loaded_decision, recall_status = _load_decision_artifact(load_decision_artifact)
        if loaded_decision:
            selected = loaded_decision["run_id"] or selected
            bucket["decision_recall"] = loaded_decision
            recall_path = load_decision_artifact
    policy_recall_status = "not_requested"
    policy_recall_path = None
    if load_policy_snapshot:
        loaded_policy, policy_recall_status = _load_policy_snapshot(load_policy_snapshot)
        if loaded_policy:
            selected = loaded_policy.get("selected_run_id", "") or selected
            compare_run_id = loaded_policy.get("compare_run_id", "") or compare_run_id
            mode = loaded_policy.get("workbench_mode", "") or mode
            policy_recall_path = load_policy_snapshot

    def _build_current_view(*, run_id: str | None, compare_id: str | None, ls_path: str | None, ls_status: str):
        return build_view_state(
            selected_run_id=run_id,
            health_filter=health,
            run_query=run_query,
            sort_mode=sort_mode,
            compare_run_id=compare_id,
            pinned_run_ids=pinned_run_ids,
            action_history=[x for x in bucket.get("action_history", []) if isinstance(x, dict)],
            session_context={"source": "query"},
            workbench_mode=mode,
            baseline_locked_run_id=str(bucket.get("baseline_locked_run_id", "")) or None,
            snapshot_recall_items=_list_snapshot_reports(limit=10),
            loaded_snapshot_path=ls_path,
            loaded_snapshot_status=ls_status,
            latest_snapshot_report_path=str(bucket.get("latest_snapshot_report_path", "")) or None,
            latest_snapshot_report_status=str(bucket.get("latest_snapshot_report_status", "not_requested")),
            selected_preset_id=selected_preset_id,
            dry_run_enabled=False,
            result_packet_override=bucket.get("result_packet") if isinstance(bucket.get("result_packet"), dict) else None,
            retry_reapply_override=bucket.get("retry_reapply") if isinstance(bucket.get("retry_reapply"), dict) else None,
            latest_execution_report_path=str(bucket.get("latest_execution_report_path", "")) or None,
            latest_execution_report_status=str(bucket.get("latest_execution_report_status", "not_requested")),
            latest_handoff_bundle_path=str(bucket.get("latest_handoff_bundle_path", "")) or None,
            latest_handoff_bundle_status=str(bucket.get("latest_handoff_bundle_status", "not_requested")),
            latest_checkpoint_path=str(bucket.get("latest_checkpoint_path", "")) or None,
            latest_checkpoint_status=str(bucket.get("latest_checkpoint_status", "not_requested")),
            restored_checkpoint_path=restored_checkpoint_path or (str(bucket.get("restored_checkpoint_path", "")) or None),
            restored_checkpoint_status=restored_checkpoint_status if restore_checkpoint else str(bucket.get("restored_checkpoint_status", "not_requested")),
            latest_decision_export_path=str(bucket.get("latest_decision_export_path", "")) or None,
            latest_decision_export_status=str(bucket.get("latest_decision_export_status", "not_requested")),
            latest_review_checkpoint_path=str(bucket.get("latest_review_checkpoint_path", "")) or None,
            latest_review_checkpoint_status=str(bucket.get("latest_review_checkpoint_status", "not_requested")),
            restored_review_checkpoint_path=restored_review_checkpoint_path or (str(bucket.get("restored_review_checkpoint_path", "")) or None),
            restored_review_checkpoint_status=restored_review_checkpoint_status if restore_review_checkpoint else str(bucket.get("restored_review_checkpoint_status", "not_requested")),
            session_closeout_path=str(bucket.get("session_closeout_path", "")) or None,
            session_closeout_status=str(bucket.get("session_closeout_status", "not_requested")),
            recall_status=recall_status if load_decision_artifact else str(bucket.get("recall_status", "not_requested")),
            recall_path=recall_path or (str(bucket.get("recall_path", "")) or None),
            policy_snapshot_path=str(bucket.get("policy_snapshot_path", "")) or None,
            policy_snapshot_status=str(bucket.get("policy_snapshot_status", "not_requested")),
            policy_recall_status=policy_recall_status if load_policy_snapshot else str(bucket.get("policy_recall_status", "not_requested")),
            policy_recall_path=policy_recall_path or (str(bucket.get("policy_recall_path", "")) or None),
            viz_mode=viz_mode or str(bucket.get("viz_mode", "")) or None,
            viz_export_status=str(bucket.get("viz_export_status", "not_requested")),
            viz_export_path=str(bucket.get("viz_export_path", "")) or None,
            viz_render_export_status=str(bucket.get("viz_render_export_status", "not_requested")),
            viz_render_export_path=str(bucket.get("viz_render_export_path", "")) or None,
            report_export_status=str(bucket.get("report_export_status", "not_requested")),
            report_export_paths=bucket.get("report_export_paths") if isinstance(bucket.get("report_export_paths"), dict) else {},
            latest_ers_snapshot_path=str(bucket.get("latest_ers_snapshot_path", "")) or None,
            latest_ers_snapshot_status=str(bucket.get("latest_ers_snapshot_status", "not_requested")),
            latest_ers_review_export_path=str(bucket.get("latest_ers_review_export_path", "")) or None,
            latest_ers_review_export_status=str(bucket.get("latest_ers_review_export_status", "not_requested")),
        )

    view = _build_current_view(run_id=selected, compare_id=compare_run_id, ls_path=loaded_snapshot_path, ls_status=loaded_snapshot_status)

    if focus_attention:
        target = next((x for x in view.attention_queue if x.get("run_id") == focus_attention), None)
        if target:
            selected = focus_attention
            compare_hint = view.suggested_compare_run_id if view.suggested_compare_run_id != focus_attention else None
            compare_run_id = compare_hint or compare_run_id
            view = _build_current_view(run_id=selected, compare_id=compare_run_id, ls_path=loaded_snapshot_path, ls_status=loaded_snapshot_status)

    applied_compare_run_id = resolve_compare_run_id_for_apply(
        compare_run_id=view.comparison_run_id,
        suggested_compare_run_id=view.suggested_compare_run_id,
        apply_suggested_compare=apply_suggested_compare,
    )
    if applied_compare_run_id != view.comparison_run_id:
        view = _build_current_view(run_id=selected, compare_id=applied_compare_run_id, ls_path=loaded_snapshot_path, ls_status=loaded_snapshot_status)

    if trigger_ers_item:
        ers_queue = (view.ers_integration.get("ers_queue", {}) if isinstance(view.ers_integration, dict) else {})
        runnable_items = ers_queue.get("runnable_items", []) if isinstance(ers_queue, dict) else []
        runnable_by_id = {
            str(item.get("item_id", "")): item
            for item in runnable_items
            if isinstance(item, dict) and str(item.get("item_id", ""))
        }
        action_name = _ERS_TRIGGER_ALLOWLIST.get(trigger_ers_item, "")
        queue_item = runnable_by_id.get(trigger_ers_item)
        if action_name and queue_item is not None:
            adapter_output = execute_runtime_adapter(
                action_name=action_name,
                payload={"selected_run_id": view.selected_run_id or ""},
                allowed_actions=list(view.control_plane.get("allowed_actions", [])),
            )
            result_packet = _result_packet(
                status=str(adapter_output.get("outcome_status", "FAILED")),
                preset_id=f"ers.{trigger_ers_item}",
                action_name=action_name,
                adapter_name=str(adapter_output.get("adapter_name", "")),
                attempted_at=str(adapter_output.get("attempted_at", "")),
                run_id=str(adapter_output.get("run_id", "")),
                artifact_paths=[str(x) for x in adapter_output.get("artifact_paths", []) if isinstance(x, str)],
                error_info=str(adapter_output.get("error_info", "")),
                summary=str(adapter_output.get("summary", "")),
            )
            bucket["result_packet"] = result_packet
            action_feedback = {
                "attempted_at": str(adapter_output.get("attempted_at", "")),
                "action_name": action_name,
                "preset_id": f"ers.{trigger_ers_item}",
                "adapter_name": str(adapter_output.get("adapter_name", "")),
                "triggered_run_id": str(adapter_output.get("run_id", "")),
                "outcome_status": str(adapter_output.get("outcome_status", "FAILED")),
                "artifact_path": next(
                    (str(x) for x in adapter_output.get("artifact_paths", []) if isinstance(x, str)),
                    "",
                ),
                "message": str(adapter_output.get("summary", "")),
            }
            _append_action_history(bucket, action_feedback)
            bucket["ers_trigger_status"] = "triggered"
            bucket["ers_trigger_item"] = trigger_ers_item
        else:
            bucket["ers_trigger_status"] = "blocked"
            bucket["ers_trigger_item"] = trigger_ers_item
            bucket["result_packet"] = _result_packet(
                status="FAILED",
                preset_id=f"ers.{trigger_ers_item}",
                action_name="ers_trigger",
                attempted_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                error_info="ers_item_not_runnable_or_not_allowlisted",
                summary="ERS trigger rejected: item is blocked, missing, or not allowlisted.",
            )
        view = _build_current_view(run_id=view.selected_run_id, compare_id=view.comparison_run_id, ls_path=loaded_snapshot_path, ls_status=loaded_snapshot_status)

    if export_ers_snapshot:
        ers_payload = dict((view.ers_integration or {}).get("ers_snapshot_preview", {}))
        ers_payload["runtime_context"] = {
            "selected_run_id": view.selected_run_id or "",
            "compare_run_id": view.comparison_run_id or "",
            "workbench_mode": view.workbench_mode,
        }
        ers_path, ers_status = write_operator_ers_snapshot_artifact(payload=ers_payload)
        bucket["latest_ers_snapshot_path"] = ers_path or ""
        bucket["latest_ers_snapshot_status"] = ers_status
        view = _build_current_view(run_id=view.selected_run_id, compare_id=view.comparison_run_id, ls_path=loaded_snapshot_path, ls_status=loaded_snapshot_status)

    if export_ers_review:
        review_payload = dict((view.ers_review or {}).get("ers_review_export_preview", {}))
        review_path, review_status = write_operator_ers_review_artifact(payload=review_payload)
        bucket["latest_ers_review_export_path"] = review_path or ""
        bucket["latest_ers_review_export_status"] = review_status
        view = _build_current_view(run_id=view.selected_run_id, compare_id=view.comparison_run_id, ls_path=loaded_snapshot_path, ls_status=loaded_snapshot_status)

    if export_snapshot:
        report_path, report_status = _write_operator_snapshot_report(dict(view.export_preview))
        bucket["latest_snapshot_report_path"] = report_path or ""
        bucket["latest_snapshot_report_status"] = report_status
        view = _build_current_view(run_id=view.selected_run_id, compare_id=view.comparison_run_id, ls_path=report_path, ls_status=report_status)

    if export_execution_report:
        report_path, report_status = _write_execution_report(dict(view.execution_report_preview))
        bucket["latest_execution_report_path"] = report_path or ""
        bucket["latest_execution_report_status"] = report_status
        view = _build_current_view(run_id=view.selected_run_id, compare_id=view.comparison_run_id, ls_path=loaded_snapshot_path, ls_status=loaded_snapshot_status)

    if export_handoff_bundle:
        bundle_path, bundle_status = _write_handoff_bundle(dict(view.handoff_bundle_preview))
        bucket["latest_handoff_bundle_path"] = bundle_path or ""
        bucket["latest_handoff_bundle_status"] = bundle_status
        view = _build_current_view(run_id=view.selected_run_id, compare_id=view.comparison_run_id, ls_path=loaded_snapshot_path, ls_status=loaded_snapshot_status)

    if save_checkpoint:
        checkpoint_path, checkpoint_status = _write_operator_checkpoint(dict(view.checkpoint_preview))
        bucket["latest_checkpoint_path"] = checkpoint_path or ""
        bucket["latest_checkpoint_status"] = checkpoint_status
        view = _build_current_view(run_id=view.selected_run_id, compare_id=view.comparison_run_id, ls_path=loaded_snapshot_path, ls_status=loaded_snapshot_status)

    if export_decision:
        decision_path, decision_status = _write_operator_decision(dict(view.decision_layer.get("decision_export_preview", {})))
        bucket["latest_decision_export_path"] = decision_path or ""
        bucket["latest_decision_export_status"] = decision_status
        view = _build_current_view(run_id=view.selected_run_id, compare_id=view.comparison_run_id, ls_path=loaded_snapshot_path, ls_status=loaded_snapshot_status)

    if save_review_checkpoint:
        review_checkpoint_path, review_checkpoint_status = _write_review_checkpoint(dict(view.decision_layer.get("checkpoint_preview", {})))
        bucket["latest_review_checkpoint_path"] = review_checkpoint_path or ""
        bucket["latest_review_checkpoint_status"] = review_checkpoint_status
        view = _build_current_view(run_id=view.selected_run_id, compare_id=view.comparison_run_id, ls_path=loaded_snapshot_path, ls_status=loaded_snapshot_status)

    if export_session_closeout:
        closeout_path, closeout_status = _write_session_closeout(dict(view.session_continuity.get("session_closeout_preview", {})))
        bucket["session_closeout_path"] = closeout_path or ""
        bucket["session_closeout_status"] = closeout_status
        view = _build_current_view(run_id=view.selected_run_id, compare_id=view.comparison_run_id, ls_path=loaded_snapshot_path, ls_status=loaded_snapshot_status)

    if load_decision_artifact:
        bucket["recall_status"] = recall_status
        bucket["recall_path"] = recall_path or ""
    if export_policy_snapshot:
        policy_path, policy_status = _write_policy_snapshot(dict(view.governance.get("policy_snapshot_preview", {})))
        bucket["policy_snapshot_path"] = policy_path or ""
        bucket["policy_snapshot_status"] = policy_status
        view = _build_current_view(run_id=view.selected_run_id, compare_id=view.comparison_run_id, ls_path=loaded_snapshot_path, ls_status=loaded_snapshot_status)
    if load_policy_snapshot:
        bucket["policy_recall_status"] = policy_recall_status
        bucket["policy_recall_path"] = policy_recall_path or ""
    if export_viz_state:
        viz_path, viz_status = _write_viz_state(dict(view.viz_integration.get("viz_export_preview", {})))
        bucket["viz_export_path"] = viz_path or ""
        bucket["viz_export_status"] = viz_status
        view = _build_current_view(run_id=view.selected_run_id, compare_id=view.comparison_run_id, ls_path=loaded_snapshot_path, ls_status=loaded_snapshot_status)
    if export_viz_render:
        render_path, render_status = _write_viz_render(dict(view.viz_render.get("viz_render_export_preview", {})))
        bucket["viz_render_export_path"] = render_path or ""
        bucket["viz_render_export_status"] = render_status
        view = _build_current_view(run_id=view.selected_run_id, compare_id=view.comparison_run_id, ls_path=loaded_snapshot_path, ls_status=loaded_snapshot_status)
    if export_session_report:
        report_path, report_status = _write_operator_report_artifact(
            suffix="session_report",
            payload=dict(view.reporting.get("session_report_preview", {})),
        )
        report_paths = dict(bucket.get("report_export_paths", {})) if isinstance(bucket.get("report_export_paths"), dict) else {}
        report_paths["session_report"] = report_path or ""
        bucket["report_export_paths"] = report_paths
        bucket["report_export_status"] = report_status
        view = _build_current_view(run_id=view.selected_run_id, compare_id=view.comparison_run_id, ls_path=loaded_snapshot_path, ls_status=loaded_snapshot_status)
    if export_decision_summary:
        run_id = str((view.reporting.get("decision_summary_preview", {}) or {}).get("run_id", "")) or "unselected"
        report_path, report_status = _write_operator_report_artifact(
            suffix=f"{run_id}.decision_summary",
            payload=dict(view.reporting.get("decision_summary_preview", {})),
        )
        report_paths = dict(bucket.get("report_export_paths", {})) if isinstance(bucket.get("report_export_paths"), dict) else {}
        report_paths["decision_summary"] = report_path or ""
        bucket["report_export_paths"] = report_paths
        bucket["report_export_status"] = report_status
        view = _build_current_view(run_id=view.selected_run_id, compare_id=view.comparison_run_id, ls_path=loaded_snapshot_path, ls_status=loaded_snapshot_status)
    if export_viz_summary:
        viz_mode = str((view.reporting.get("viz_summary_preview", {}) or {}).get("viz_mode", "weather"))
        report_path, report_status = _write_operator_report_artifact(
            suffix=f"{viz_mode}.viz_summary",
            payload=dict(view.reporting.get("viz_summary_preview", {})),
        )
        report_paths = dict(bucket.get("report_export_paths", {})) if isinstance(bucket.get("report_export_paths"), dict) else {}
        report_paths["viz_summary"] = report_path or ""
        bucket["report_export_paths"] = report_paths
        bucket["report_export_status"] = report_status
        view = _build_current_view(run_id=view.selected_run_id, compare_id=view.comparison_run_id, ls_path=loaded_snapshot_path, ls_status=loaded_snapshot_status)
    if export_closeout_bundle:
        report_path, report_status = _write_operator_report_artifact(
            suffix="operator_closeout",
            payload=dict(view.reporting.get("closeout_bundle_preview", {})),
        )
        report_paths = dict(bucket.get("report_export_paths", {})) if isinstance(bucket.get("report_export_paths"), dict) else {}
        report_paths["closeout_bundle"] = report_path or ""
        bucket["report_export_paths"] = report_paths
        bucket["report_export_status"] = report_status
        view = _build_current_view(run_id=view.selected_run_id, compare_id=view.comparison_run_id, ls_path=loaded_snapshot_path, ls_status=loaded_snapshot_status)
    if export_markdown_report:
        report_path, report_status = _write_markdown_report(str(view.reporting.get("markdown_preview", "")))
        report_paths = dict(bucket.get("report_export_paths", {})) if isinstance(bucket.get("report_export_paths"), dict) else {}
        report_paths["markdown_report"] = report_path or ""
        bucket["report_export_paths"] = report_paths
        bucket["report_export_status"] = report_status
        view = _build_current_view(run_id=view.selected_run_id, compare_id=view.comparison_run_id, ls_path=loaded_snapshot_path, ls_status=loaded_snapshot_status)
    if viz_mode:
        bucket["viz_mode"] = viz_mode

    bucket["selected_preset_id"] = view.selected_preset_id or ""
    bucket["context"] = {
        "selected_run_id": view.selected_run_id or "",
        "compare_run_id": view.comparison_run_id or "",
        "health": view.focus_filters["health"],
        "run_query": view.focus_filters["run_query"],
            "sort_mode": view.focus_filters["sort_mode"],
            "mode": view.workbench_mode,
        }
    return view

def ui_operator_console(request: Request):
    view = _view_from_request(request)
    return templates.TemplateResponse(
        "operator_console.html",
        {
            "request": request,
            "view": view,
            "action_result": None,
            "panel_token": _panel_token(),
            "panel_host": _panel_host(),
            "panel_port": _panel_port(),
            "token_enabled": _token_enabled(),
        },
    )


async def ui_run_compliance_probe(request: Request):
    bucket = _state_bucket(request)
    form = await request.form()
    require_token(request, form)
    selected_run_id = form.get("run_id") if hasattr(form, "get") else None
    health_filter = form.get("health") if hasattr(form, "get") else None
    run_query = form.get("run_query") if hasattr(form, "get") else None
    sort_mode = form.get("sort_mode") if hasattr(form, "get") else None
    compare_run_id = form.get("compare_run_id") if hasattr(form, "get") else None
    selected_preset_id = str(form.get("preset_id") if hasattr(form, "get") else "") or str(bucket.get("selected_preset_id", ""))
    action_intent = str(form.get("action_intent") if hasattr(form, "get") else "execute")
    view = build_view_state(
        selected_run_id=selected_run_id,
        health_filter=health_filter,
        run_query=run_query,
        sort_mode=sort_mode,
        compare_run_id=compare_run_id,
        pinned_run_ids=[str(x) for x in bucket.get("pinned_run_ids", []) if isinstance(x, str)],
        action_history=[x for x in bucket.get("action_history", []) if isinstance(x, dict)],
        session_context={"source": "form"},
        workbench_mode=str(bucket.get("context", {}).get("mode", "overview")),
        baseline_locked_run_id=str(bucket.get("baseline_locked_run_id", "")) or None,
        snapshot_recall_items=_list_snapshot_reports(limit=10),
        latest_snapshot_report_path=str(bucket.get("latest_snapshot_report_path", "")) or None,
        latest_snapshot_report_status=str(bucket.get("latest_snapshot_report_status", "not_requested")),
        selected_preset_id=selected_preset_id,
        dry_run_enabled=action_intent == "preview",
        result_packet_override=bucket.get("result_packet") if isinstance(bucket.get("result_packet"), dict) else None,
        retry_reapply_override=bucket.get("retry_reapply") if isinstance(bucket.get("retry_reapply"), dict) else None,
        latest_execution_report_path=str(bucket.get("latest_execution_report_path", "")) or None,
        latest_execution_report_status=str(bucket.get("latest_execution_report_status", "not_requested")),
        latest_handoff_bundle_path=str(bucket.get("latest_handoff_bundle_path", "")) or None,
        latest_handoff_bundle_status=str(bucket.get("latest_handoff_bundle_status", "not_requested")),
        latest_checkpoint_path=str(bucket.get("latest_checkpoint_path", "")) or None,
        latest_checkpoint_status=str(bucket.get("latest_checkpoint_status", "not_requested")),
        restored_checkpoint_path=str(bucket.get("restored_checkpoint_path", "")) or None,
        restored_checkpoint_status=str(bucket.get("restored_checkpoint_status", "not_requested")),
        latest_decision_export_path=str(bucket.get("latest_decision_export_path", "")) or None,
        latest_decision_export_status=str(bucket.get("latest_decision_export_status", "not_requested")),
        latest_review_checkpoint_path=str(bucket.get("latest_review_checkpoint_path", "")) or None,
        latest_review_checkpoint_status=str(bucket.get("latest_review_checkpoint_status", "not_requested")),
        restored_review_checkpoint_path=str(bucket.get("restored_review_checkpoint_path", "")) or None,
        restored_review_checkpoint_status=str(bucket.get("restored_review_checkpoint_status", "not_requested")),
        session_closeout_path=str(bucket.get("session_closeout_path", "")) or None,
        session_closeout_status=str(bucket.get("session_closeout_status", "not_requested")),
        recall_status=str(bucket.get("recall_status", "not_requested")),
        recall_path=str(bucket.get("recall_path", "")) or None,
        policy_snapshot_path=str(bucket.get("policy_snapshot_path", "")) or None,
        policy_snapshot_status=str(bucket.get("policy_snapshot_status", "not_requested")),
        policy_recall_status=str(bucket.get("policy_recall_status", "not_requested")),
        policy_recall_path=str(bucket.get("policy_recall_path", "")) or None,
        viz_mode=str(bucket.get("viz_mode", "")) or None,
        viz_export_status=str(bucket.get("viz_export_status", "not_requested")),
        viz_export_path=str(bucket.get("viz_export_path", "")) or None,
        viz_render_export_status=str(bucket.get("viz_render_export_status", "not_requested")),
        viz_render_export_path=str(bucket.get("viz_render_export_path", "")) or None,
        report_export_status=str(bucket.get("report_export_status", "not_requested")),
        report_export_paths=bucket.get("report_export_paths") if isinstance(bucket.get("report_export_paths"), dict) else {},
    )
    action_result: dict[str, object] | None = None
    last_action: dict[str, object] | None = None
    preset = _resolve_preset(view.action_presets, selected_preset_id)
    if preset is None:
        bucket["result_packet"] = _result_packet(
            status="invalid_preset",
            preset_id=selected_preset_id,
            action_name="",
            error_info="preset_not_found",
            summary="Selected preset is not available.",
        )
    elif action_intent == "preview":
        action_name = str(preset.get("action_name", ""))
        adapter_name = f"adapter.{action_name}" if action_name and action_name != "export_operator_snapshot" else "adapter.export_operator_snapshot"
        bucket["result_packet"] = _result_packet(
            status="preview_only",
            preset_id=str(preset.get("preset_id", "")),
            action_name=action_name,
            adapter_name=adapter_name,
            attempted_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            summary=f"Dry-run preview generated; resolved adapter={adapter_name} args={dict(preset.get('default_args', {}))}",
        )
    else:
        execute_preset = preset
        if action_intent == "reapply":
            stored_payload = bucket.get("last_execution_payload")
            if isinstance(stored_payload, dict):
                restored_preset_id = str(stored_payload.get("preset_id", ""))
                execute_preset = _resolve_preset(view.action_presets, restored_preset_id) or preset
                selected_preset_id = str(execute_preset.get("preset_id", ""))
            else:
                bucket["result_packet"] = _result_packet(
                    status="not_available",
                    preset_id="",
                    action_name="",
                    summary="No previous executable payload available for reapply.",
                )
                execute_preset = None
        if execute_preset is not None:
            action_name = str(execute_preset.get("action_name", ""))
            preset_id = str(execute_preset.get("preset_id", ""))
            if action_name == "export_operator_snapshot":
                report_path, report_status = _write_operator_snapshot_report(dict(view.export_preview))
                bucket["latest_snapshot_report_path"] = report_path or ""
                bucket["latest_snapshot_report_status"] = report_status
                attempted_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
                last_action = {
                    "action_name": action_name,
                    "preset_id": preset_id,
                    "adapter_name": "adapter.export_operator_snapshot",
                    "attempted_at": attempted_at,
                    "outcome_status": "SUCCESS" if report_status == "written" else "FAILED",
                    "triggered_run_id": str(view.selected_run_id or ""),
                    "artifact_path": report_path or "",
                    "message": f"snapshot export {report_status}",
                }
                _append_action_history(bucket, last_action)
                bucket["last_execution_payload"] = {
                    "preset_id": preset_id,
                    "action_name": action_name,
                }
                action_result = {
                    "status": last_action["outcome_status"],
                    "exit_code": 0 if report_status == "written" else 1,
                    "command": ["export_operator_snapshot"],
                    "stdout_tail": report_path or "",
                    "stderr_tail": "",
                    "timestamp_utc": attempted_at,
                }
                bucket["result_packet"] = _result_packet(
                    status=str(last_action.get("outcome_status", "UNKNOWN")),
                    preset_id=preset_id,
                    action_name=action_name,
                    adapter_name="adapter.export_operator_snapshot",
                    attempted_at=attempted_at,
                    run_id=str(view.selected_run_id or ""),
                    artifact_path=report_path or "",
                    artifact_paths=[report_path] if report_path else [],
                    summary=f"snapshot export {report_status}",
                )
            else:
                adapter_output = execute_runtime_adapter(
                    action_name=action_name,
                    payload={
                        "selected_run_id": str(view.selected_run_id or ""),
                        "preset_id": preset_id,
                        "default_args": dict(execute_preset.get("default_args", {})),
                    },
                    allowed_actions=[str(x) for x in view.control_plane.get("allowed_actions", []) if isinstance(x, str)],
                )
                last_action = {
                    "action_name": action_name,
                    "preset_id": preset_id,
                    "adapter_name": str(adapter_output.get("adapter_name", "")),
                    "attempted_at": str(adapter_output.get("attempted_at", "")),
                    "outcome_status": str(adapter_output.get("outcome_status", "FAILED")),
                    "triggered_run_id": str(adapter_output.get("run_id", "")),
                    "artifact_path": str((adapter_output.get("artifact_paths") or [""])[0]),
                    "error_info": str(adapter_output.get("error_info", "")),
                    "message": str(adapter_output.get("summary", "")),
                }
                _append_action_history(bucket, last_action)
                bucket["last_execution_payload"] = {
                    "preset_id": preset_id,
                    "action_name": action_name,
                    "default_args": dict(execute_preset.get("default_args", {})),
                }
                bucket["result_packet"] = _result_packet(
                    status=str(adapter_output.get("outcome_status", "FAILED")),
                    preset_id=preset_id,
                    action_name=action_name,
                    adapter_name=str(adapter_output.get("adapter_name", "")),
                    attempted_at=str(adapter_output.get("attempted_at", "")),
                    run_id=str(adapter_output.get("run_id", "")),
                    artifact_path=str((adapter_output.get("artifact_paths") or [""])[0]),
                    artifact_paths=[str(x) for x in adapter_output.get("artifact_paths", [])],
                    error_info=str(adapter_output.get("error_info", "")),
                    summary=str(adapter_output.get("summary", "")),
                )
    latest_history = bucket.get("action_history", [])
    latest_item = latest_history[0] if isinstance(latest_history, list) and latest_history else {}
    if isinstance(latest_item, dict):
        bucket["retry_reapply"] = {
            "enabled": True,
            "status": "ready",
            "last_action_name": str(latest_item.get("action_name", "")),
            "last_run_id": str(latest_item.get("run_id", "")),
            "last_preset_id": str(latest_item.get("preset_id", "")),
        }
    else:
        bucket["retry_reapply"] = {
            "enabled": False,
            "status": "not_available",
            "last_action_name": "",
            "last_run_id": "",
            "last_preset_id": "",
        }
    bucket["selected_preset_id"] = selected_preset_id
    view_after = build_view_state(
        selected_run_id=view.selected_run_id,
        health_filter=health_filter,
        run_query=run_query,
        sort_mode=sort_mode,
        compare_run_id=compare_run_id,
        pinned_run_ids=[str(x) for x in bucket.get("pinned_run_ids", []) if isinstance(x, str)],
        action_history=[x for x in bucket.get("action_history", []) if isinstance(x, dict)],
        session_context={"source": "form"},
        workbench_mode=str(bucket.get("context", {}).get("mode", "overview")),
        baseline_locked_run_id=str(bucket.get("baseline_locked_run_id", "")) or None,
        snapshot_recall_items=_list_snapshot_reports(limit=10),
        latest_snapshot_report_path=str(bucket.get("latest_snapshot_report_path", "")) or None,
        latest_snapshot_report_status=str(bucket.get("latest_snapshot_report_status", "not_requested")),
        last_action=last_action,
        selected_preset_id=selected_preset_id,
        dry_run_enabled=action_intent == "preview",
        result_packet_override=bucket.get("result_packet") if isinstance(bucket.get("result_packet"), dict) else None,
        retry_reapply_override=bucket.get("retry_reapply") if isinstance(bucket.get("retry_reapply"), dict) else None,
        latest_execution_report_path=str(bucket.get("latest_execution_report_path", "")) or None,
        latest_execution_report_status=str(bucket.get("latest_execution_report_status", "not_requested")),
        latest_handoff_bundle_path=str(bucket.get("latest_handoff_bundle_path", "")) or None,
        latest_handoff_bundle_status=str(bucket.get("latest_handoff_bundle_status", "not_requested")),
        latest_checkpoint_path=str(bucket.get("latest_checkpoint_path", "")) or None,
        latest_checkpoint_status=str(bucket.get("latest_checkpoint_status", "not_requested")),
        restored_checkpoint_path=str(bucket.get("restored_checkpoint_path", "")) or None,
        restored_checkpoint_status=str(bucket.get("restored_checkpoint_status", "not_requested")),
        latest_decision_export_path=str(bucket.get("latest_decision_export_path", "")) or None,
        latest_decision_export_status=str(bucket.get("latest_decision_export_status", "not_requested")),
        latest_review_checkpoint_path=str(bucket.get("latest_review_checkpoint_path", "")) or None,
        latest_review_checkpoint_status=str(bucket.get("latest_review_checkpoint_status", "not_requested")),
        restored_review_checkpoint_path=str(bucket.get("restored_review_checkpoint_path", "")) or None,
        restored_review_checkpoint_status=str(bucket.get("restored_review_checkpoint_status", "not_requested")),
        session_closeout_path=str(bucket.get("session_closeout_path", "")) or None,
        session_closeout_status=str(bucket.get("session_closeout_status", "not_requested")),
        recall_status=str(bucket.get("recall_status", "not_requested")),
        recall_path=str(bucket.get("recall_path", "")) or None,
        policy_snapshot_path=str(bucket.get("policy_snapshot_path", "")) or None,
        policy_snapshot_status=str(bucket.get("policy_snapshot_status", "not_requested")),
        policy_recall_status=str(bucket.get("policy_recall_status", "not_requested")),
        policy_recall_path=str(bucket.get("policy_recall_path", "")) or None,
        viz_mode=str(bucket.get("viz_mode", "")) or None,
        viz_export_status=str(bucket.get("viz_export_status", "not_requested")),
        viz_export_path=str(bucket.get("viz_export_path", "")) or None,
        viz_render_export_status=str(bucket.get("viz_render_export_status", "not_requested")),
        viz_render_export_path=str(bucket.get("viz_render_export_path", "")) or None,
        report_export_status=str(bucket.get("report_export_status", "not_requested")),
        report_export_paths=bucket.get("report_export_paths") if isinstance(bucket.get("report_export_paths"), dict) else {},
    )
    bucket["context"] = {
        "selected_run_id": view_after.selected_run_id or "",
        "compare_run_id": view_after.comparison_run_id or "",
        "health": view_after.focus_filters["health"],
        "run_query": view_after.focus_filters["run_query"],
        "sort_mode": view_after.focus_filters["sort_mode"],
        "mode": view_after.workbench_mode,
    }
    return templates.TemplateResponse(
        "operator_console.html",
        {
            "request": request,
            "view": view_after,
            "action_result": action_result,
            "panel_token": _panel_token(),
            "panel_host": _panel_host(),
            "panel_port": _panel_port(),
            "token_enabled": _token_enabled(),
        },
    )


def register(app):
    app.get("/operator", response_class=HTMLResponse)(ui_operator_console)
    app.post("/operator/actions/run-compliance-probe", response_class=HTMLResponse)(ui_run_compliance_probe)
