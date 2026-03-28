from __future__ import annotations

from fastapi import Request
from fastapi.responses import HTMLResponse

from ..operator_console import build_last_action_feedback, build_view_state, run_compliance_probe_command
from ..panel_context import templates, require_token, _panel_host, _panel_port, _panel_token, _token_enabled


def _view_from_request(request: Request, selected_run_id: str | None = None):
    return build_view_state(
        selected_run_id=selected_run_id or request.query_params.get("run_id"),
        health_filter=request.query_params.get("health"),
        run_query=request.query_params.get("run_query"),
        sort_mode=request.query_params.get("sort_mode"),
        compare_run_id=request.query_params.get("compare_run_id"),
    )


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
    form = await request.form()
    require_token(request, form)
    selected_run_id = form.get("run_id") if hasattr(form, "get") else None
    health_filter = form.get("health") if hasattr(form, "get") else None
    run_query = form.get("run_query") if hasattr(form, "get") else None
    sort_mode = form.get("sort_mode") if hasattr(form, "get") else None
    compare_run_id = form.get("compare_run_id") if hasattr(form, "get") else None

    view = build_view_state(
        selected_run_id=selected_run_id,
        health_filter=health_filter,
        run_query=run_query,
        sort_mode=sort_mode,
        compare_run_id=compare_run_id,
    )
    action_result = run_compliance_probe_command()
    last_action = build_last_action_feedback(action_result)
    view_after = build_view_state(
        selected_run_id=view.selected_run_id,
        health_filter=health_filter,
        run_query=run_query,
        sort_mode=sort_mode,
        compare_run_id=compare_run_id,
        last_action=last_action,
    )
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
