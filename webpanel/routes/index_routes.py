from __future__ import annotations

import json

from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse, Response

from ..filters import build_run_view, filter_runs, parse_filter_params
from ..models import AbraxasSignalPacket
from ..panel_context import (
    _panel_host,
    _panel_port,
    _panel_token,
    _token_enabled,
    require_token,
    templates,
)
from .. import panel_context
from .shared import _emit_and_ingest_payload, _ingest_packet


def _render_runs_page(request: Request):
    params = parse_filter_params(request.query_params)
    runs = panel_context.store.list_runs()
    filtered = filter_runs(runs, params)
    run_views = [build_run_view(run) for run in filtered[:50]]
    prev_run_id_prefill = request.query_params.get("prev_run_id")
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "runs": run_views,
            "runs_total": len(filtered),
            "filters": params,
            "panel_token": _panel_token(),
            "panel_host": _panel_host(),
            "panel_port": _panel_port(),
            "token_enabled": _token_enabled(),
            "prev_run_id_prefill": prev_run_id_prefill,
        },
    )


def ui_index(request: Request):
    return _render_runs_page(request)


def ui_runs(request: Request):
    return _render_runs_page(request)


def ui_ledger(request: Request, run_id: str):
    run = panel_context.store.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    events = panel_context.ledger.list_events(run_id)
    chain_valid = panel_context.ledger.chain_valid(run_id)
    return templates.TemplateResponse(
        "ledger.html",
        {
            "request": request,
            "run": run,
            "events": events,
            "chain_valid": chain_valid,
            "panel_token": _panel_token(),
            "panel_host": _panel_host(),
            "panel_port": _panel_port(),
            "token_enabled": _token_enabled(),
        },
    )


def ui_packet_json(run_id: str):
    run = panel_context.store.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    payload = json.dumps(run.signal.model_dump(), sort_keys=True, ensure_ascii=True)
    return Response(content=payload, media_type="application/json")


def ui_ledger_json(run_id: str):
    run = panel_context.store.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    events = panel_context.ledger.list_events(run_id)
    payload = {
        "run_id": run_id,
        "chain_valid": panel_context.ledger.chain_valid(run_id),
        "events": [
            {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "timestamp_utc": event.timestamp_utc,
                "prev_event_hash": event.prev_event_hash,
                "event_hash": event.event_hash,
                "data": event.data,
            }
            for event in events
        ],
    }
    rendered = json.dumps(payload, sort_keys=True, ensure_ascii=True)
    return Response(content=rendered, media_type="application/json")


def ui_sample_packet():
    packet = {
        "signal_id": "sig_sample",
        "timestamp_utc": panel_context.now_utc(),
        "tier": "psychonaut",
        "lane": "canon",
        "payload": {
            "kind": "mvp_test",
            "note": "replace with real Abraxas output when available",
        },
        "confidence": {"mvp_confidence": 0.5},
        "provenance_status": "complete",
        "invariance_status": "pass",
        "drift_flags": [],
        "rent_status": "paid",
        "not_computable_regions": [],
    }
    return PlainTextResponse(
        json.dumps(packet, indent=2, ensure_ascii=True),
        media_type="text/plain",
    )


async def ui_ingest(request: Request):
    form = await request.form()
    require_token(request, form)
    raw = form.get("packet_json", "")
    prev_run_id = form.get("prev_run_id") or ""
    try:
        packet = AbraxasSignalPacket.model_validate(json.loads(raw))
    except Exception as exc:
        runs = panel_context.store.list(limit=50)
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "runs": runs,
                "error": str(exc),
                "packet_json": raw,
                "panel_token": _panel_token(),
                "panel_host": _panel_host(),
                "panel_port": _panel_port(),
                "token_enabled": _token_enabled(),
            },
        )

    if prev_run_id and panel_context.store.get(prev_run_id) is None:
        runs = panel_context.store.list(limit=50)
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "runs": runs,
                "error": f"prev_run_id not found: {prev_run_id}",
                "packet_json": raw,
                "panel_token": _panel_token(),
                "panel_host": _panel_host(),
                "panel_port": _panel_port(),
                "token_enabled": _token_enabled(),
            },
        )

    resp = _ingest_packet(packet, prev_run_id=prev_run_id or None)
    return RedirectResponse(url=f"/runs/{resp['run_id']}", status_code=303)


async def ui_upload_payload(request: Request):
    form = await request.form()
    require_token(request, form)
    tier = form.get("tier", "")
    lane = form.get("lane", "")
    payload_file = form.get("payload_file")
    prev_run_id = form.get("prev_run_id") or ""

    if not tier or not lane:
        runs = panel_context.store.list(limit=50)
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "runs": runs,
                "error": "tier and lane are required",
                "panel_token": _panel_token(),
                "panel_host": _panel_host(),
                "panel_port": _panel_port(),
                "token_enabled": _token_enabled(),
            },
        )

    if payload_file is None or not hasattr(payload_file, "read"):
        runs = panel_context.store.list(limit=50)
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "runs": runs,
                "error": "payload file is required",
                "panel_token": _panel_token(),
                "panel_host": _panel_host(),
                "panel_port": _panel_port(),
                "token_enabled": _token_enabled(),
            },
        )

    try:
        raw_bytes = await payload_file.read()
        payload_obj = json.loads(raw_bytes.decode("utf-8"))
        if not isinstance(payload_obj, dict):
            raise ValueError("payload must be a JSON object")
        if prev_run_id and panel_context.store.get(prev_run_id) is None:
            raise ValueError(f"prev_run_id not found: {prev_run_id}")
        run_id = _emit_and_ingest_payload(
            payload_obj, tier=tier, lane=lane, prev_run_id=prev_run_id or None
        )
    except Exception as exc:
        runs = panel_context.store.list(limit=50)
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "runs": runs,
                "error": str(exc),
                "panel_token": _panel_token(),
                "panel_host": _panel_host(),
                "panel_port": _panel_port(),
                "token_enabled": _token_enabled(),
            },
        )

    return RedirectResponse(url=f"/runs/{run_id}", status_code=303)


def register(app):
    app.get("/", response_class=HTMLResponse)(ui_index)
    app.get("/runs", response_class=HTMLResponse)(ui_runs)
    app.get("/runs/{run_id}/ledger", response_class=HTMLResponse)(ui_ledger)
    app.get("/runs/{run_id}/packet.json")(ui_packet_json)
    app.get("/runs/{run_id}/ledger.json")(ui_ledger_json)
    app.get("/ui/sample_packet")(ui_sample_packet)
    app.post("/ui/ingest")(ui_ingest)
    app.post("/ui/upload_payload")(ui_upload_payload)
