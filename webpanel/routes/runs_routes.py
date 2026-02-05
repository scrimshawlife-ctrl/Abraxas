from __future__ import annotations

import json

from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from ..consideration import build_considerations_for_run
from ..continuity import build_continuity_report
from ..delta_notifications import compute_delta_notifications
from ..explain_mode import build_run_brief
from ..gates import compute_gate_stack
from ..lineage import get_lineage
from ..oracle_output import build_oracle_json, build_oracle_view, extract_oracle_output, validate_oracle_output_v2
from ..panel_context import (
    _panel_host,
    _panel_port,
    _panel_token,
    _token_enabled,
    require_token,
    templates,
)
from ..policy import compute_policy_hash, get_policy_snapshot, policy_snapshot
from ..policy_gate import policy_ack_required
from ..preference_kernel import (
    apply_prefs_update,
    build_consideration_view,
    normalize_prefs,
    prefs_focus_priority,
    prefs_show_sections,
)
from ..stability import run_stabilization
from .. import panel_context
from .shared import _select_action


def _strip_policy(snapshot):
    if not snapshot:
        return {}
    return {
        k: v
        for k, v in snapshot.items()
        if k not in {"timestamp_utc", "policy_hash"}
    }


def _policy_diff_keys(ingest_snapshot, current_snapshot) -> list:
    left = _strip_policy(ingest_snapshot)
    right = _strip_policy(current_snapshot)
    diffs = []

    def walk(prefix, a, b) -> None:
        if isinstance(a, dict) and isinstance(b, dict):
            keys = sorted(set(a.keys()) | set(b.keys()))
            for key in keys:
                walk(f"{prefix}.{key}" if prefix else str(key), a.get(key), b.get(key))
        else:
            if a != b:
                diffs.append(prefix)

    walk("", left, right)
    return diffs


def ui_run(request: Request, run_id: str):
    run = panel_context.store.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    events = panel_context.ledger.list_events(run_id)
    chain_valid = panel_context.ledger.chain_valid(run_id)
    lineage = get_lineage(run_id, panel_context.store)
    lineage_ids = [entry.run_id for entry in lineage]
    current_snapshot = get_policy_snapshot()
    current_hash = compute_policy_hash(current_snapshot)
    ingest_hash = run.policy_hash_at_ingest
    if ingest_hash:
        policy_status = "MATCH" if ingest_hash == current_hash else "CHANGED"
    else:
        policy_status = "UNKNOWN"
    policy_diff_keys = []
    if policy_status == "CHANGED":
        policy_diff_keys = _policy_diff_keys(run.policy_snapshot_at_ingest, current_snapshot)
    policy_ack_needed = policy_ack_required(run, current_hash)
    oracle_output = extract_oracle_output(run)
    oracle_view = None
    oracle_validation = {"valid": True, "errors": []}
    if oracle_output:
        valid, errors = validate_oracle_output_v2(oracle_output)
        oracle_validation = {"valid": valid, "errors": errors}
        oracle_view = build_oracle_view(oracle_output)
    gate_stack = compute_gate_stack(run, current_hash)
    top_gate = gate_stack[0] if gate_stack else None
    considerations = {}
    try:
        prefs = normalize_prefs(run.prefs) if getattr(run, "prefs", None) else normalize_prefs({})
    except Exception:
        prefs = normalize_prefs({})
    show_sections = prefs_show_sections(prefs)
    proposals = None
    if run.last_step_result and isinstance(run.last_step_result, dict):
        if run.last_step_result.get("kind") == "propose_actions_v0":
            proposals = run.last_step_result.get("actions", [])
    if proposals:
        considerations_list = build_considerations_for_run(
            run,
            oracle=oracle_output,
            gates=gate_stack,
            ledger_events=events,
        )
        for proposal, consideration in zip(proposals, considerations_list):
            if isinstance(proposal, dict):
                key = proposal.get("action_id") or consideration.get("proposal_id")
                if key:
                    considerations[key] = build_consideration_view(consideration, prefs)
    continuity_report = None
    continuity_summary_lines = None
    prev_run = panel_context.store.get(run.prev_run_id) if run.prev_run_id else None
    if prev_run:
        prev_events = panel_context.ledger.list_events(prev_run.run_id)
        setattr(run, "ledger_events", events)
        setattr(prev_run, "ledger_events", prev_events)
        continuity_report = build_continuity_report(run, prev_run, current_hash)
        if continuity_report:
            continuity_summary_lines = prefs_focus_priority(
                continuity_report.get("summary_lines", []), prefs.get("focus", [])
            )
        try:
            delattr(run, "ledger_events")
            delattr(prev_run, "ledger_events")
        except Exception:
            pass
    run_brief = build_run_brief(run, prev_run, current_hash)
    delta_notifications = compute_delta_notifications(run, prev_run, current_hash)
    return templates.TemplateResponse(
        "run.html",
        {
            "request": request,
            "run": run,
            "events": events,
            "chain_valid": chain_valid,
            "lineage_ids": lineage_ids,
            "panel_token": _panel_token(),
            "panel_host": _panel_host(),
            "panel_port": _panel_port(),
            "token_enabled": _token_enabled(),
            "current_policy_hash": current_hash,
            "current_policy_snapshot": current_snapshot,
            "policy_status": policy_status,
            "policy_diff_keys": policy_diff_keys,
            "policy_ack_required": policy_ack_needed,
            "policy_current_hash": current_hash,
            "oracle_view": oracle_view,
            "oracle_validation": oracle_validation,
            "gate_stack": gate_stack,
            "top_gate": top_gate,
            "considerations": considerations,
            "continuity_report": continuity_report,
            "continuity_summary_lines": continuity_summary_lines,
            "prefs": prefs,
            "show_sections": show_sections,
            "run_brief": run_brief,
            "delta_notifications": delta_notifications,
        },
    )


def ui_oracle_json(run_id: str):
    run = panel_context.store.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    payload = build_oracle_json(run)
    if not payload:
        raise HTTPException(status_code=404, detail="oracle output not found")
    return Response(content=payload, media_type="application/json")


def ui_stability(request: Request, run_id: str):
    run = panel_context.store.get(run_id)
    if not run or not run.stability_report:
        raise HTTPException(status_code=404, detail="stability report not found")
    return templates.TemplateResponse(
        "stability.html",
        {
            "request": request,
            "run": run,
            "report": run.stability_report,
            "panel_host": _panel_host(),
            "panel_port": _panel_port(),
            "token_enabled": _token_enabled(),
            "panel_token": _panel_token(),
        },
    )


def ui_stability_json(run_id: str):
    run = panel_context.store.get(run_id)
    if not run or not run.stability_report:
        raise HTTPException(status_code=404, detail="stability report not found")
    rendered = json.dumps(run.stability_report, sort_keys=True, ensure_ascii=True)
    return Response(content=rendered, media_type="application/json")


async def ui_update_prefs(run_id: str, request: Request):
    form = await request.form()
    require_token(request, form)
    run = panel_context.store.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")

    verbosity = form.get("verbosity") or "medium"
    risk_tolerance = form.get("risk_tolerance") or "medium"
    focus = form.get("focus") or ""
    show = form.getlist("show")
    hide = form.getlist("hide")
    payload = {
        "verbosity": verbosity,
        "risk_tolerance": risk_tolerance,
        "focus": focus,
        "show": show,
        "hide": hide,
    }
    try:
        apply_prefs_update(
            run=run,
            new_prefs=payload,
            ledger=panel_context.ledger,
            event_id=panel_context.eid("ev"),
            timestamp_utc=panel_context.now_utc(),
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    panel_context.store.put(run)
    return RedirectResponse(url=f"/runs/{run_id}", status_code=303)


async def ui_select_action(run_id: str, request: Request):
    form = await request.form()
    require_token(request, form)
    selected_action_id = form.get("selected_action_id", "")
    try:
        _select_action(run_id, selected_action_id)
    except Exception as exc:
        run = panel_context.store.get(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="run not found")
        events = panel_context.ledger.list_events(run_id)
        chain_valid = panel_context.ledger.chain_valid(run_id)
        lineage = get_lineage(run_id, panel_context.store)
        lineage_ids = [entry.run_id for entry in lineage]
        current_snapshot = get_policy_snapshot()
        current_hash = compute_policy_hash(current_snapshot)
        ingest_hash = run.policy_hash_at_ingest
        if ingest_hash:
            policy_status = "MATCH" if ingest_hash == current_hash else "CHANGED"
        else:
            policy_status = "UNKNOWN"
        policy_diff_keys = []
        if policy_status == "CHANGED":
            policy_diff_keys = _policy_diff_keys(run.policy_snapshot_at_ingest, current_snapshot)
        return templates.TemplateResponse(
            "run.html",
            {
                "request": request,
                "run": run,
                "events": events,
                "chain_valid": chain_valid,
                "lineage_ids": lineage_ids,
                "panel_token": _panel_token(),
                "panel_host": _panel_host(),
                "panel_port": _panel_port(),
                "token_enabled": _token_enabled(),
                "error": str(exc),
                "current_policy_hash": current_hash,
                "current_policy_snapshot": current_snapshot,
                "policy_status": policy_status,
                "policy_diff_keys": policy_diff_keys,
            },
        )
    return RedirectResponse(url=f"/runs/{run_id}", status_code=303)


async def ui_stabilize(run_id: str, request: Request):
    form = await request.form()
    require_token(request, form)
    raw_cycles = form.get("cycles") or "12"
    selected_ops = form.getlist("operators")
    try:
        cycles = int(raw_cycles)
    except ValueError:
        cycles = 12
    if cycles < 1:
        cycles = 1
    if cycles > 24:
        cycles = 24

    run = panel_context.store.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")

    base_ops = ["extract_structure_v0", "compress_signal_v0", "propose_actions_v0"]
    ops_set = set(selected_ops or base_ops)
    if "compress_signal_v0" in ops_set:
        ops_set.add("extract_structure_v0")
    if "propose_actions_v0" in ops_set:
        ops_set.add("compress_signal_v0")
        ops_set.add("extract_structure_v0")
    operators = [op for op in base_ops if op in ops_set]

    snapshot = policy_snapshot()
    policy_hash = snapshot.get("policy_hash", "")

    prior = run.stability_report
    report = run_stabilization(run, cycles, operators, policy_hash, prior_report=prior)

    run.stability_report = report
    panel_context.store.put(run)

    panel_context.ledger.append(
        run_id,
        panel_context.eid("ev"),
        "stability_ran",
        panel_context.now_utc(),
        {
            "cycles": cycles,
            "passed": report["invariance"]["passed"],
            "distinct_final_hashes": report["invariance"]["distinct_final_hashes"],
            "drift_class": report["drift_class"],
            "policy_hash_prefix": policy_hash[:8],
        },
    )
    return RedirectResponse(url=f"/runs/{run_id}/stability", status_code=303)


def register(app):
    app.get("/runs/{run_id}", response_class=HTMLResponse)(ui_run)
    app.get("/runs/{run_id}/oracle.json")(ui_oracle_json)
    app.get("/runs/{run_id}/stability")(ui_stability)
    app.get("/runs/{run_id}/stability.json")(ui_stability_json)
    app.post("/ui/runs/{run_id}/prefs")(ui_update_prefs)
    app.post("/ui/runs/{run_id}/select_action")(ui_select_action)
    app.post("/ui/runs/{run_id}/stabilize")(ui_stabilize)
