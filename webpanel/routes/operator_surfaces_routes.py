from __future__ import annotations

import json

from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse, Response

from abx.operator_views import build_evidence_view, build_release_view, build_run_summary, compare_runs
from ..panel_context import _panel_host, _panel_port, _panel_token, _token_enabled, templates


def ui_run_console(request: Request, run_id: str):
    try:
        summary = build_run_summary(run_id).to_dict()
    except Exception as exc:
        raise HTTPException(status_code=404, detail=f"run console unavailable: {exc}")
    return templates.TemplateResponse(
        "run_console.html",
        {
            "request": request,
            "summary": summary,
            "run_id": run_id,
            "panel_host": _panel_host(),
            "panel_port": _panel_port(),
            "token_enabled": _token_enabled(),
            "panel_token": _panel_token(),
        },
    )


def ui_run_console_json(run_id: str):
    payload = build_run_summary(run_id).to_dict()
    return Response(content=json.dumps(payload, sort_keys=True, ensure_ascii=True), media_type="application/json")


def ui_run_compare(request: Request):
    run_a = request.query_params.get("run_a", "")
    run_b = request.query_params.get("run_b", "")
    if not run_a or not run_b:
        raise HTTPException(status_code=400, detail="run_a and run_b are required")
    payload = compare_runs(run_a, run_b).to_dict()
    return templates.TemplateResponse(
        "run_compare.html",
        {
            "request": request,
            "diff": payload,
            "run_a": run_a,
            "run_b": run_b,
            "panel_host": _panel_host(),
            "panel_port": _panel_port(),
            "token_enabled": _token_enabled(),
            "panel_token": _panel_token(),
        },
    )


def ui_run_compare_json(run_a: str, run_b: str):
    payload = compare_runs(run_a, run_b).to_dict()
    return Response(content=json.dumps(payload, sort_keys=True, ensure_ascii=True), media_type="application/json")


def ui_release_readiness(request: Request):
    run_id = request.query_params.get("run_id", "RUN-RELEASE-READY-001")
    payload = build_release_view(run_id).to_dict()
    return templates.TemplateResponse(
        "release_readiness.html",
        {
            "request": request,
            "run_id": run_id,
            "release": payload,
            "panel_host": _panel_host(),
            "panel_port": _panel_port(),
            "token_enabled": _token_enabled(),
            "panel_token": _panel_token(),
        },
    )


def ui_release_readiness_json(run_id: str):
    payload = build_release_view(run_id).to_dict()
    return Response(content=json.dumps(payload, sort_keys=True, ensure_ascii=True), media_type="application/json")


def ui_evidence(request: Request, run_id: str):
    payload = build_evidence_view(run_id).to_dict()
    return templates.TemplateResponse(
        "run_evidence.html",
        {
            "request": request,
            "run_id": run_id,
            "evidence": payload,
            "panel_host": _panel_host(),
            "panel_port": _panel_port(),
            "token_enabled": _token_enabled(),
            "panel_token": _panel_token(),
        },
    )


def ui_evidence_json(run_id: str):
    payload = build_evidence_view(run_id).to_dict()
    return Response(content=json.dumps(payload, sort_keys=True, ensure_ascii=True), media_type="application/json")


def register(app):
    app.get("/runs/{run_id}/console", response_class=HTMLResponse)(ui_run_console)
    app.get("/runs/{run_id}/console.json")(ui_run_console_json)
    app.get("/runs/compare", response_class=HTMLResponse)(ui_run_compare)
    app.get("/api/operator/compare/{run_a}/{run_b}")(ui_run_compare_json)
    app.get("/release/readiness", response_class=HTMLResponse)(ui_release_readiness)
    app.get("/api/operator/release-readiness/{run_id}")(ui_release_readiness_json)
    app.get("/runs/{run_id}/evidence", response_class=HTMLResponse)(ui_evidence)
    app.get("/api/operator/evidence/{run_id}")(ui_evidence_json)
    app.get("/api/operator/run/{run_id}")(ui_run_console_json)
