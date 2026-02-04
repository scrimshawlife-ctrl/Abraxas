from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Mapping, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from abraxas.signal.exporter import emit_signal_packet
from .familiar_adapter import FamiliarAdapter
from .ledger import LedgerChain
from .models import AbraxasSignalPacket, DeferralStart, HumanAck
from .store import InMemoryStore
from .runplan import build_runplan, execute_step

# Run instructions:
#   pip install fastapi uvicorn jinja2 pydantic
#   uvicorn webpanel.app:app --reload --port 8008
#   open http://localhost:8008/
# Token guard:
#   export ABX_PANEL_TOKEN="yourtoken"
#   API clients send header X-ABX-Token: yourtoken
app = FastAPI(title="ABX-Familiar Web Panel (MVP)", version="0.1.0")
templates = Jinja2Templates(directory="webpanel/templates")

store = InMemoryStore()
ledger = LedgerChain()
adapter = FamiliarAdapter()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def eid(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


def _panel_token() -> str:
    return os.environ.get("ABX_PANEL_TOKEN", "").strip()


def _panel_host() -> str:
    return os.environ.get("ABX_PANEL_HOST", "127.0.0.1").strip() or "127.0.0.1"


def _panel_port() -> str:
    return os.environ.get("ABX_PANEL_PORT", "8008").strip() or "8008"


def _token_enabled() -> bool:
    return bool(_panel_token())


def require_token(request: Optional[Request], form: Optional[Mapping[str, Any]] = None) -> None:
    token = _panel_token()
    if not token:
        return
    if request is None:
        raise HTTPException(status_code=401, detail="invalid token")
    header_token = request.headers.get("X-ABX-Token")
    if header_token == token:
        return
    if form is not None and form.get("abx_token") == token:
        return
    raise HTTPException(status_code=401, detail="invalid token")


def _emit_and_ingest_payload(payload_obj: dict, *, tier: str, lane: str) -> str:
    confidence = payload_obj.get("confidence")
    if not isinstance(confidence, dict):
        confidence = {"source": "payload_upload", "mvp": True}
    packet_dict = emit_signal_packet(
        payload=payload_obj,
        tier=tier,
        lane=lane,
        confidence=confidence,
        provenance_status="partial",
        invariance_status="not_evaluated",
        drift_flags=[],
        rent_status="not_applicable",
        not_computable_regions=[],
    )
    packet = AbraxasSignalPacket.model_validate(packet_dict)
    resp = _ingest_packet(packet)
    return resp["run_id"]


@app.get("/", response_class=HTMLResponse)
def ui_index(request: Request):
    runs = store.list(limit=50)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "runs": runs,
            "panel_token": _panel_token(),
            "panel_host": _panel_host(),
            "panel_port": _panel_port(),
            "token_enabled": _token_enabled(),
        },
    )


@app.get("/runs/{run_id}", response_class=HTMLResponse)
def ui_run(request: Request, run_id: str):
    run = store.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    events = ledger.list_events(run_id)
    chain_valid = ledger.chain_valid(run_id)
    return templates.TemplateResponse(
        "run.html",
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


@app.get("/runs/{run_id}/ledger", response_class=HTMLResponse)
def ui_ledger(request: Request, run_id: str):
    run = store.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    events = ledger.list_events(run_id)
    chain_valid = ledger.chain_valid(run_id)
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


@app.get("/runs/{run_id}/packet.json")
def ui_packet_json(run_id: str):
    run = store.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    payload = json.dumps(run.signal.model_dump(), sort_keys=True, ensure_ascii=True)
    return Response(content=payload, media_type="application/json")


@app.get("/runs/{run_id}/ledger.json")
def ui_ledger_json(run_id: str):
    run = store.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    events = ledger.list_events(run_id)
    payload = {
        "run_id": run_id,
        "chain_valid": ledger.chain_valid(run_id),
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


@app.get("/ui/sample_packet")
def ui_sample_packet():
    packet = {
        "signal_id": "sig_sample",
        "timestamp_utc": now_utc(),
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


def _ingest_packet(packet: AbraxasSignalPacket) -> dict:
    run, _ctx_id = adapter.ingest(packet)
    run.runplan = build_runplan(run)
    run.current_step_index = 0
    run.last_step_result = None
    run.step_results = []
    store.put(run)

    ledger.append(
        run.run_id,
        eid("ev"),
        "packet_received",
        now_utc(),
        {"signal_id": packet.signal_id},
    )
    ledger.append(
        run.run_id,
        eid("ev"),
        "context_created",
        now_utc(),
        {"context_id": run.context.context_id},
    )
    ledger.append(
        run.run_id,
        eid("ev"),
        "interaction_mode_selected",
        now_utc(),
        {"mode": run.context.recommended_interaction_mode},
    )
    if run.requires_human_confirmation:
        ledger.append(
            run.run_id,
            eid("ev"),
            "execution_deferred",
            now_utc(),
            {"reason": "awaiting_ack"},
        )

    if run.runplan is not None:
        ledger.append(
            run.run_id,
            eid("ev"),
            "runplan_created",
            now_utc(),
            {
                "plan_id": run.runplan.plan_id,
                "plan_hash": run.runplan.deterministic_hash,
                "step_count": len(run.runplan.steps),
            },
        )

    events = ledger.list_events(run.run_id)
    tail_hash = events[-1].event_hash if events else None
    return {
        "run_id": run.run_id,
        "context_id": run.context.context_id,
        "interaction_mode": run.context.recommended_interaction_mode,
        "requires_human_confirmation": run.requires_human_confirmation,
        "phase": run.phase,
        "pause_required": run.pause_required,
        "pause_reason": run.pause_reason,
        "actions_remaining": run.actions_remaining,
        "ledger_tail_event_hash": tail_hash,
    }


@app.post("/api/v1/familiar/ingest")
def ingest(packet: AbraxasSignalPacket, request: Optional[Request] = None):
    require_token(request)
    return _ingest_packet(packet)


@app.get("/api/v1/familiar/runs/{run_id}")
def get_run(run_id: str):
    run = store.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    return run.model_dump()


@app.get("/api/v1/familiar/runs")
def list_runs(limit: int = 50):
    return [r.model_dump() for r in store.list(limit=limit)]


@app.get("/api/v1/familiar/runs/{run_id}/ledger")
def get_ledger(run_id: str):
    run = store.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    events = ledger.list_events(run_id)
    return {
        "run_id": run_id,
        "chain_valid": ledger.chain_valid(run_id),
        "events": [asdict(event) for event in events],
    }


def _record_ack(run_id: str, ack: HumanAck) -> dict:
    run = store.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")

    run.human_ack = ack
    run.pause_required = False
    run.pause_reason = None
    run.phase = max(run.phase, 4)

    ledger.append(
        run_id,
        eid("ev"),
        "human_confirmation_recorded",
        now_utc(),
        ack.model_dump(),
    )
    store.put(run)
    return run.model_dump()


@app.post("/api/v1/familiar/runs/{run_id}/ack")
def ack(run_id: str, ack: HumanAck, request: Optional[Request] = None):
    require_token(request)
    return _record_ack(run_id, ack)


def _start_deferral(run_id: str, body: DeferralStart) -> dict:
    run = store.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")

    if run.requires_human_confirmation and not run.human_ack:
        raise HTTPException(status_code=409, detail="ack required before deferral")

    run.deferral_active = True
    run.quota_max_actions = int(body.quota_max_actions)
    run.actions_taken = 0
    run.phase = max(run.phase, 5)

    ledger.append(
        run_id,
        eid("ev"),
        "deferral_session_started",
        now_utc(),
        {"quota_max_actions": run.quota_max_actions},
    )
    store.put(run)
    return {
        "deferral_session_id": f"def_{run_id}",
        "actions_remaining": run.actions_remaining,
        "run": run.model_dump(),
    }


@app.post("/api/v1/familiar/runs/{run_id}/defer/start")
def defer_start(run_id: str, body: DeferralStart, request: Optional[Request] = None):
    require_token(request)
    return _start_deferral(run_id, body)


def _step_deferral(run_id: str) -> dict:
    run = store.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")

    if not run.deferral_active or run.quota_max_actions is None:
        raise HTTPException(status_code=409, detail="deferral not active")

    if run.requires_human_confirmation and not run.human_ack:
        raise HTTPException(status_code=409, detail="ack required before deferral")

    if run.actions_remaining is not None and run.actions_remaining <= 0:
        run.pause_required = True
        run.pause_reason = "quota_exhausted"
        ledger.append(run_id, eid("ev"), "quota_exhausted_pause", now_utc(), {})
        store.put(run)
        return run.model_dump()

    if run.runplan is None:
        run.runplan = build_runplan(run)
        run.current_step_index = 0
        run.last_step_result = None
        run.step_results = []

    steps = run.runplan.steps if run.runplan is not None else []
    if run.current_step_index >= len(steps):
        run.pause_required = True
        run.pause_reason = "completed"
        store.put(run)
        return run.model_dump()

    step = steps[run.current_step_index]
    result = execute_step(run, step)
    run.last_step_result = result
    run.step_results.append(result)
    run.current_step_index += 1
    run.actions_taken += 1
    run.phase = max(run.phase, 6)

    event_payload = {
        "step_id": step.step_id,
        "kind": step.kind,
        "produces": step.produces,
        "result_keys": list(result.keys()),
    }
    if step.kind == "extract_structure_v0":
        event_payload["paths_count"] = result.get("keys_topology", {}).get("paths_count")
        event_payload["numeric_count"] = len(result.get("numeric_metrics", []))
        event_payload["unknowns_count"] = len(result.get("unknowns", []))
        event_payload["refs_count"] = len(result.get("evidence_refs", []))
        event_payload["claims_count"] = len(result.get("claims_preview", []))
    if step.kind == "compress_signal_v0":
        pressure = result.get("plan_pressure", {}).get("score")
        event_payload["pressure_score"] = pressure
        event_payload["metrics_count"] = len(result.get("salient_metrics", []))
        event_payload["unknown_groups"] = len(result.get("uncertainty_map", {}))
        event_payload["refs_count"] = sum(
            len(entries) for entries in result.get("evidence_surface", {}).values()
        )
        event_payload["questions_count"] = len(result.get("next_questions", []))
    if step.kind == "propose_actions_v0":
        actions = result.get("actions", [])
        event_payload["actions_count"] = len(actions)
        event_payload["kinds"] = [action.get("kind") for action in actions if isinstance(action, dict)]

    ledger.append(
        run_id,
        eid("ev"),
        "runplan_step_executed",
        now_utc(),
        event_payload,
    )
    ledger.append(
        run_id,
        eid("ev"),
        "action_executed",
        now_utc(),
        {"action_index": run.actions_taken},
    )

    if run.current_step_index >= len(steps):
        run.pause_required = True
        run.pause_reason = "completed"

    if run.actions_remaining is not None and run.actions_remaining <= 0:
        run.pause_required = True
        run.pause_reason = "quota_exhausted"
        ledger.append(run_id, eid("ev"), "quota_exhausted_pause", now_utc(), {})

    store.put(run)
    return run.model_dump()


@app.post("/api/v1/familiar/runs/{run_id}/defer/step")
def defer_step(run_id: str, request: Optional[Request] = None):
    require_token(request)
    return _step_deferral(run_id)


def _stop_deferral(run_id: str) -> dict:
    run = store.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")

    run.deferral_active = False
    run.pause_required = True
    run.pause_reason = "human_revoked"
    run.phase = max(run.phase, 7)

    ledger.append(
        run_id,
        eid("ev"),
        "deferral_session_ended",
        now_utc(),
        {"reason": "human_revoked"},
    )
    store.put(run)
    return run.model_dump()


@app.post("/api/v1/familiar/runs/{run_id}/defer/stop")
def defer_stop(run_id: str, request: Optional[Request] = None):
    require_token(request)
    return _stop_deferral(run_id)


@app.post("/ui/ingest")
async def ui_ingest(request: Request):
    form = await request.form()
    require_token(request, form)
    raw = form.get("packet_json", "")
    try:
        packet = AbraxasSignalPacket.model_validate(json.loads(raw))
    except Exception as exc:
        runs = store.list(limit=50)
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

    resp = _ingest_packet(packet)
    return RedirectResponse(url=f"/runs/{resp['run_id']}", status_code=303)


@app.post("/ui/upload_payload")
async def ui_upload_payload(request: Request):
    form = await request.form()
    require_token(request, form)
    tier = form.get("tier", "")
    lane = form.get("lane", "")
    payload_file = form.get("payload_file")

    if not tier or not lane:
        runs = store.list(limit=50)
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
        runs = store.list(limit=50)
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
        run_id = _emit_and_ingest_payload(payload_obj, tier=tier, lane=lane)
    except Exception as exc:
        runs = store.list(limit=50)
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


@app.post("/ui/runs/{run_id}/ack")
async def ui_ack(run_id: str, request: Request):
    form = await request.form()
    require_token(request, form)
    ack_obj = HumanAck(
        ack_mode="ui_confirm",
        ack_id=eid("ack"),
        ack_timestamp_utc=now_utc(),
    )
    _record_ack(run_id, ack_obj)
    return RedirectResponse(url=f"/runs/{run_id}", status_code=303)


@app.post("/ui/runs/{run_id}/defer/start/{quota}")
async def ui_defer_start(run_id: str, quota: int, request: Request):
    form = await request.form()
    require_token(request, form)
    _start_deferral(run_id, DeferralStart(quota_max_actions=quota))  # type: ignore[arg-type]
    return RedirectResponse(url=f"/runs/{run_id}", status_code=303)


@app.post("/ui/runs/{run_id}/defer/step")
async def ui_defer_step(run_id: str, request: Request):
    form = await request.form()
    require_token(request, form)
    _step_deferral(run_id)
    return RedirectResponse(url=f"/runs/{run_id}", status_code=303)


@app.post("/ui/runs/{run_id}/defer/stop")
async def ui_defer_stop(run_id: str, request: Request):
    form = await request.form()
    require_token(request, form)
    _stop_deferral(run_id)
    return RedirectResponse(url=f"/runs/{run_id}", status_code=303)
