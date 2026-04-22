from __future__ import annotations

import json

from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse, Response

from abx.developer_readiness import read_developer_readiness_payload
from abx.gap_closure_invariance import read_gap_closure_invariance_payload
from abx.promotion_preflight import read_promotion_preflight
from abx.report_manifest import read_report_manifest
from abx.report_manifest_diff import read_report_manifest_diff
from abx.report_manifest_diff_ledger import read_diff_history
from abx.report_manifest_summary import read_manifest_change_summary
from abx.report_manifest_watchlist import read_report_manifest_watchlist
from abx.readiness_comparison import read_latest_comparison, read_ledger_tail
from abx.reporting_cycle import read_reporting_cycle
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

def ui_developer_readiness_json():
    payload = read_developer_readiness_payload()
    return Response(content=json.dumps(payload, sort_keys=True, ensure_ascii=True), media_type="application/json")

def ui_gap_closure_invariance_json():
    payload = read_gap_closure_invariance_payload()
    return Response(content=json.dumps(payload, sort_keys=True, ensure_ascii=True), media_type="application/json")

def ui_readiness_comparison_latest_json():
    payload = read_latest_comparison()
    return Response(content=json.dumps(payload, sort_keys=True, ensure_ascii=True), media_type="application/json")

def ui_readiness_comparison_ledger_json(request: Request):
    limit_raw = request.query_params.get("limit", "20")
    try:
        limit = int(limit_raw)
    except ValueError:
        limit = 20
    payload = read_ledger_tail(limit=limit)
    return Response(content=json.dumps(payload, sort_keys=True, ensure_ascii=True), media_type="application/json")

def ui_promotion_preflight_json():
    payload = read_promotion_preflight()
    return Response(content=json.dumps(payload, sort_keys=True, ensure_ascii=True), media_type="application/json")

def ui_reporting_cycle_latest_json():
    payload = read_reporting_cycle()
    return Response(content=json.dumps(payload, sort_keys=True, ensure_ascii=True), media_type="application/json")

def ui_report_manifest_json():
    payload = read_report_manifest()
    return Response(content=json.dumps(payload, sort_keys=True, ensure_ascii=True), media_type="application/json")

def ui_report_manifest_diff_json():
    payload = read_report_manifest_diff()
    return Response(content=json.dumps(payload, sort_keys=True, ensure_ascii=True), media_type="application/json")

def ui_report_manifest_diff_history_json(request: Request):
    limit_raw = request.query_params.get("limit", "20")
    try:
        limit = int(limit_raw)
    except ValueError:
        limit = 20
    payload = read_diff_history(limit=limit)
    return Response(content=json.dumps(payload, sort_keys=True, ensure_ascii=True), media_type="application/json")

def ui_report_manifest_summary_json():
    payload = read_manifest_change_summary()
    return Response(content=json.dumps(payload, sort_keys=True, ensure_ascii=True), media_type="application/json")

def ui_report_manifest_watchlist_json():
    payload = read_report_manifest_watchlist()
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
    app.get("/api/developer/readiness")(ui_developer_readiness_json)
    app.get("/api/gap-closure/invariance")(ui_gap_closure_invariance_json)
    app.get("/api/readiness/comparison/latest")(ui_readiness_comparison_latest_json)
    app.get("/api/readiness/comparison/ledger")(ui_readiness_comparison_ledger_json)
    app.get("/api/promotion/preflight")(ui_promotion_preflight_json)
    app.get("/api/reporting/cycle/latest")(ui_reporting_cycle_latest_json)
    app.get("/api/reports/manifest")(ui_report_manifest_json)
    app.get("/api/reports/manifest/diff")(ui_report_manifest_diff_json)
    app.get("/api/reports/manifest/diff/history")(ui_report_manifest_diff_history_json)
    app.get("/api/reports/manifest/summary")(ui_report_manifest_summary_json)
    app.get("/api/reports/manifest/watchlist")(ui_report_manifest_watchlist_json)
