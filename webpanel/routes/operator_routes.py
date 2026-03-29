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
)
from ..panel_context import templates, require_token, _panel_host, _panel_port, _panel_token, _token_enabled

_OPERATOR_LOCAL_STATE: dict[str, dict[str, object]] = {}


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
