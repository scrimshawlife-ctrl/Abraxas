from __future__ import annotations

import json
import uuid
from dataclasses import asdict
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .core_bridge import core_step
from .familiar_adapter import FamiliarAdapter
from .ledger import LedgerChain
from .models import AbraxasSignalPacket, DeferralStart, HumanAck
from .store import InMemoryStore

# Run instructions:
#   pip install fastapi uvicorn jinja2 pydantic
#   uvicorn webpanel.app:app --reload --port 8008
#   open http://localhost:8008/
app = FastAPI(title="ABX-Familiar Web Panel (MVP)", version="0.1.0")
templates = Jinja2Templates(directory="webpanel/templates")

store = InMemoryStore()
ledger = LedgerChain()
adapter = FamiliarAdapter()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def eid(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


@app.get("/", response_class=HTMLResponse)
def ui_index(request: Request):
    runs = store.list(limit=50)
    return templates.TemplateResponse("index.html", {"request": request, "runs": runs})


@app.get("/runs/{run_id}", response_class=HTMLResponse)
def ui_run(request: Request, run_id: str):
    run = store.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    events = ledger.list_events(run_id)
    chain_valid = ledger.chain_valid(run_id)
    return templates.TemplateResponse(
        "run.html",
        {"request": request, "run": run, "events": events, "chain_valid": chain_valid},
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
        {"request": request, "run": run, "events": events, "chain_valid": chain_valid},
    )


@app.post("/api/v1/familiar/ingest")
def ingest(packet: AbraxasSignalPacket):
    run, _ctx_id = adapter.ingest(packet)
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


@app.post("/api/v1/familiar/runs/{run_id}/ack")
def ack(run_id: str, ack: HumanAck):
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


@app.post("/api/v1/familiar/runs/{run_id}/defer/start")
def defer_start(run_id: str, body: DeferralStart):
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


@app.post("/api/v1/familiar/runs/{run_id}/defer/step")
def defer_step(run_id: str):
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

    update = core_step(run_id)
    if isinstance(update, dict):
        if "actions_taken" in update:
            run.actions_taken = int(update["actions_taken"])
        elif "actions_taken_delta" in update:
            run.actions_taken += int(update["actions_taken_delta"])
        else:
            run.actions_taken += 1
        if "phase" in update:
            run.phase = max(run.phase, int(update["phase"]))
        else:
            run.phase = max(run.phase, 6)
        if "pause_required" in update:
            run.pause_required = bool(update["pause_required"])
        if "pause_reason" in update:
            run.pause_reason = update["pause_reason"]
    else:
        run.actions_taken += 1
        run.phase = max(run.phase, 6)
    ledger.append(
        run_id,
        eid("ev"),
        "action_executed",
        now_utc(),
        {"action_index": run.actions_taken},
    )

    if run.actions_remaining is not None and run.actions_remaining <= 0:
        run.pause_required = True
        run.pause_reason = "quota_exhausted"
        ledger.append(run_id, eid("ev"), "quota_exhausted_pause", now_utc(), {})

    store.put(run)
    return run.model_dump()


@app.post("/api/v1/familiar/runs/{run_id}/defer/stop")
def defer_stop(run_id: str):
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


@app.post("/ui/ingest")
async def ui_ingest(request: Request):
    form = await request.form()
    raw = form.get("packet_json", "")
    try:
        packet = AbraxasSignalPacket.model_validate(json.loads(raw))
    except Exception as exc:
        runs = store.list(limit=50)
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "runs": runs, "error": str(exc), "packet_json": raw},
        )

    resp = ingest(packet)
    return RedirectResponse(url=f"/runs/{resp['run_id']}", status_code=303)


@app.post("/ui/runs/{run_id}/ack")
async def ui_ack(run_id: str, request: Request):
    ack_obj = HumanAck(
        ack_mode="ui_confirm",
        ack_id=eid("ack"),
        ack_timestamp_utc=now_utc(),
    )
    ack(run_id, ack_obj)
    return RedirectResponse(url=f"/runs/{run_id}", status_code=303)


@app.post("/ui/runs/{run_id}/defer/start/{quota}")
async def ui_defer_start(run_id: str, quota: int):
    defer_start(run_id, DeferralStart(quota_max_actions=quota))  # type: ignore[arg-type]
    return RedirectResponse(url=f"/runs/{run_id}", status_code=303)


@app.post("/ui/runs/{run_id}/defer/step")
async def ui_defer_step(run_id: str):
    defer_step(run_id)
    return RedirectResponse(url=f"/runs/{run_id}", status_code=303)


@app.post("/ui/runs/{run_id}/defer/stop")
async def ui_defer_stop(run_id: str):
    defer_stop(run_id)
    return RedirectResponse(url=f"/runs/{run_id}", status_code=303)
