from __future__ import annotations

import json
from dataclasses import asdict
from typing import Optional

from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse, Response

from ..models import AbraxasSignalPacket, DeferralStart, HumanAck
from ..panel_context import _panel_host, _panel_port, _panel_token, _token_enabled, require_token, templates
from ..policy import policy_snapshot
from .. import panel_context
from .shared import (
    _ingest_packet,
    _record_ack,
    _record_policy_ack,
    _start_deferral,
    _start_session,
    _step_deferral,
    _stop_deferral,
    _end_session,
)


def ui_policy(request: Request):
    snapshot = policy_snapshot()
    accept = request.headers.get("accept", "")
    if "application/json" in accept:
        rendered = json.dumps(snapshot, sort_keys=True, ensure_ascii=True)
        return Response(content=rendered, media_type="application/json")
    return templates.TemplateResponse(
        "policy.html",
        {
            "request": request,
            "policy": snapshot,
            "panel_host": _panel_host(),
            "panel_port": _panel_port(),
            "token_enabled": _token_enabled(),
            "panel_token": _panel_token(),
        },
    )


def ingest(packet: AbraxasSignalPacket, request: Optional[Request] = None):
    require_token(request)
    return _ingest_packet(packet)


def get_run(run_id: str):
    run = panel_context.store.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    return run.model_dump()


def list_runs(limit: int = 50):
    return [r.model_dump() for r in panel_context.store.list(limit=limit)]


def get_ledger(run_id: str):
    run = panel_context.store.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    events = panel_context.ledger.list_events(run_id)
    return {
        "run_id": run_id,
        "chain_valid": panel_context.ledger.chain_valid(run_id),
        "events": [asdict(event) for event in events],
    }


def ack(run_id: str, ack: HumanAck, request: Optional[Request] = None):
    require_token(request)
    return _record_ack(run_id, ack)


def defer_start(run_id: str, body: DeferralStart, request: Optional[Request] = None):
    require_token(request)
    return _start_deferral(run_id, body)


def defer_step(run_id: str, request: Optional[Request] = None):
    require_token(request)
    return _step_deferral(run_id)


def defer_stop(run_id: str, request: Optional[Request] = None):
    require_token(request)
    return _stop_deferral(run_id)


async def ui_ack(run_id: str, request: Request):
    form = await request.form()
    require_token(request, form)
    ack_obj = HumanAck(
        ack_mode="ui_confirm",
        ack_id=panel_context.eid("ack"),
        ack_timestamp_utc=panel_context.now_utc(),
    )
    _record_ack(run_id, ack_obj)
    return RedirectResponse(url=f"/runs/{run_id}", status_code=303)


async def ui_defer_start(run_id: str, quota: int, request: Request):
    form = await request.form()
    require_token(request, form)
    try:
        _start_deferral(run_id, DeferralStart(quota_max_actions=quota))  # type: ignore[arg-type]
    except HTTPException as exc:
        if exc.detail == "policy_ack_required":
            return RedirectResponse(url=f"/runs/{run_id}", status_code=303)
        if exc.detail in {"session_required", "session_exhausted"}:
            return RedirectResponse(url=f"/runs/{run_id}", status_code=303)
        raise
    return RedirectResponse(url=f"/runs/{run_id}", status_code=303)


async def ui_defer_step(run_id: str, request: Request):
    form = await request.form()
    require_token(request, form)
    try:
        _step_deferral(run_id)
    except HTTPException as exc:
        if exc.detail == "policy_ack_required":
            return RedirectResponse(url=f"/runs/{run_id}", status_code=303)
        if exc.detail in {"session_required", "session_exhausted"}:
            return RedirectResponse(url=f"/runs/{run_id}", status_code=303)
        raise
    return RedirectResponse(url=f"/runs/{run_id}", status_code=303)


async def ui_defer_stop(run_id: str, request: Request):
    form = await request.form()
    require_token(request, form)
    _stop_deferral(run_id)
    return RedirectResponse(url=f"/runs/{run_id}", status_code=303)


async def ui_session_start(run_id: str, request: Request):
    form = await request.form()
    require_token(request, form)
    raw_max = form.get("session_max_steps") or "3"
    try:
        max_steps = int(raw_max)
    except ValueError:
        max_steps = 3
    _start_session(run_id, max_steps)
    return RedirectResponse(url=f"/runs/{run_id}", status_code=303)


async def ui_session_end(run_id: str, request: Request):
    form = await request.form()
    require_token(request, form)
    _end_session(run_id, reason="user")
    return RedirectResponse(url=f"/runs/{run_id}", status_code=303)


async def ui_policy_ack(run_id: str, request: Request):
    form = await request.form()
    require_token(request, form)
    _record_policy_ack(run_id)
    return RedirectResponse(url=f"/runs/{run_id}", status_code=303)


def register(app):
    app.get("/policy")(ui_policy)
    app.post("/api/v1/familiar/ingest")(ingest)
    app.get("/api/v1/familiar/runs/{run_id}")(get_run)
    app.get("/api/v1/familiar/runs")(list_runs)
    app.get("/api/v1/familiar/runs/{run_id}/ledger")(get_ledger)
    app.post("/api/v1/familiar/runs/{run_id}/ack")(ack)
    app.post("/api/v1/familiar/runs/{run_id}/defer/start")(defer_start)
    app.post("/api/v1/familiar/runs/{run_id}/defer/step")(defer_step)
    app.post("/api/v1/familiar/runs/{run_id}/defer/stop")(defer_stop)
    app.post("/ui/runs/{run_id}/ack")(ui_ack)
    app.post("/ui/runs/{run_id}/defer/start/{quota}")(ui_defer_start)
    app.post("/ui/runs/{run_id}/defer/step")(ui_defer_step)
    app.post("/ui/runs/{run_id}/defer/stop")(ui_defer_stop)
    app.post("/ui/runs/{run_id}/session/start")(ui_session_start)
    app.post("/ui/runs/{run_id}/session/end")(ui_session_end)
    app.post("/ui/runs/{run_id}/policy/ack")(ui_policy_ack)
