from __future__ import annotations

from typing import Optional

from fastapi import HTTPException

from abraxas.signal.exporter import emit_signal_packet
from ..execute_action import execute_one
from ..models import AbraxasSignalPacket, DeferralStart, HumanAck
from ..policy import compute_policy_hash, get_policy_snapshot
from ..policy_gate import PolicyAckRequired, enforce_policy_ack, record_policy_ack
from ..runplan import build_runplan, execute_step
from ..select_action import build_checklist
from ..session_mode import SessionGateError, consume_session_step, end_session, enforce_session, start_session
from .. import panel_context


def _ingest_packet(packet: AbraxasSignalPacket, prev_run_id: Optional[str] = None) -> dict:
    run, _ctx_id = panel_context.adapter.ingest(packet)
    snapshot = get_policy_snapshot()
    run.policy_snapshot_at_ingest = snapshot
    run.policy_hash_at_ingest = compute_policy_hash(snapshot)
    run.runplan = build_runplan(run)
    run.current_step_index = 0
    run.last_step_result = None
    run.step_results = []
    run.selected_action_id = None
    run.selected_action = None
    run.execution_checklist = None
    run.selected_action_progress = None
    run.last_execution_result = None
    run.prev_run_id = None
    run.continuity_reason = None
    panel_context.store.put(run)

    panel_context.ledger.append(
        run.run_id,
        panel_context.eid("ev"),
        "packet_received",
        panel_context.now_utc(),
        {"signal_id": packet.signal_id},
    )
    panel_context.ledger.append(
        run.run_id,
        panel_context.eid("ev"),
        "context_created",
        panel_context.now_utc(),
        {"context_id": run.context.context_id},
    )
    panel_context.ledger.append(
        run.run_id,
        panel_context.eid("ev"),
        "interaction_mode_selected",
        panel_context.now_utc(),
        {"mode": run.context.recommended_interaction_mode},
    )
    if run.requires_human_confirmation:
        panel_context.ledger.append(
            run.run_id,
            panel_context.eid("ev"),
            "execution_deferred",
            panel_context.now_utc(),
            {"reason": "awaiting_ack"},
        )

    if prev_run_id and panel_context.store.get(prev_run_id):
        run.prev_run_id = prev_run_id
        run.continuity_reason = "new_packet_supersedes_previous"
        panel_context.store.put(run)
        panel_context.ledger.append(
            run.run_id,
            panel_context.eid("ev"),
            "continuity_linked",
            panel_context.now_utc(),
            {"prev_run_id": prev_run_id, "reason": run.continuity_reason},
        )
        panel_context.ledger.append(
            prev_run_id,
            panel_context.eid("ev"),
            "superseded_by",
            panel_context.now_utc(),
            {"new_run_id": run.run_id},
        )

    if run.runplan is not None:
        panel_context.ledger.append(
            run.run_id,
            panel_context.eid("ev"),
            "runplan_created",
            panel_context.now_utc(),
            {
                "plan_id": run.runplan.plan_id,
                "plan_hash": run.runplan.deterministic_hash,
                "step_count": len(run.runplan.steps),
            },
        )

    panel_context.ledger.append(
        run.run_id,
        panel_context.eid("ev"),
        "policy_locked_at_ingest",
        panel_context.now_utc(),
        {
            "policy_hash_prefix": (run.policy_hash_at_ingest or "")[:8],
            "thresholds": snapshot.get("thresholds"),
            "caps": snapshot.get("caps"),
        },
    )

    events = panel_context.ledger.list_events(run.run_id)
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


def _emit_and_ingest_payload(
    payload_obj: dict, *, tier: str, lane: str, prev_run_id: Optional[str] = None
) -> str:
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
    resp = _ingest_packet(packet, prev_run_id=prev_run_id)
    return resp["run_id"]


def _latest_proposals(run) -> Optional[list]:
    for result in reversed(run.step_results):
        if isinstance(result, dict) and result.get("kind") == "propose_actions_v0":
            actions = result.get("actions")
            return actions if isinstance(actions, list) else None
    return None


def _record_ack(run_id: str, ack: HumanAck) -> dict:
    run = panel_context.store.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")

    run.human_ack = ack
    run.pause_required = False
    run.pause_reason = None
    run.phase = max(run.phase, 4)

    panel_context.ledger.append(
        run_id,
        panel_context.eid("ev"),
        "human_confirmation_recorded",
        panel_context.now_utc(),
        ack.model_dump(),
    )
    panel_context.store.put(run)
    return run.model_dump()


def _start_deferral(run_id: str, body: DeferralStart) -> dict:
    run = panel_context.store.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    current_hash = compute_policy_hash(get_policy_snapshot())
    try:
        enforce_policy_ack(run, current_hash)
    except PolicyAckRequired:
        raise HTTPException(status_code=409, detail="policy_ack_required")
    try:
        enforce_session(run)
    except SessionGateError as exc:
        raise HTTPException(status_code=409, detail=exc.reason)

    if run.requires_human_confirmation and not run.human_ack:
        raise HTTPException(status_code=409, detail="ack required before deferral")

    run.deferral_active = True
    run.quota_max_actions = int(body.quota_max_actions)
    run.actions_taken = 0
    run.phase = max(run.phase, 5)

    panel_context.ledger.append(
        run_id,
        panel_context.eid("ev"),
        "deferral_session_started",
        panel_context.now_utc(),
        {"quota_max_actions": run.quota_max_actions},
    )
    panel_context.store.put(run)
    return {
        "deferral_session_id": f"def_{run_id}",
        "actions_remaining": run.actions_remaining,
        "run": run.model_dump(),
    }


def _step_deferral(run_id: str) -> dict:
    run = panel_context.store.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    current_hash = compute_policy_hash(get_policy_snapshot())
    try:
        enforce_policy_ack(run, current_hash)
    except PolicyAckRequired:
        raise HTTPException(status_code=409, detail="policy_ack_required")
    try:
        enforce_session(run)
    except SessionGateError as exc:
        raise HTTPException(status_code=409, detail=exc.reason)

    if not run.deferral_active or run.quota_max_actions is None:
        raise HTTPException(status_code=409, detail="deferral not active")

    if run.requires_human_confirmation and not run.human_ack:
        raise HTTPException(status_code=409, detail="ack required before deferral")

    if run.actions_remaining is not None and run.actions_remaining <= 0:
        run.pause_required = True
        run.pause_reason = "quota_exhausted"
        panel_context.ledger.append(
            run_id,
            panel_context.eid("ev"),
            "quota_exhausted_pause",
            panel_context.now_utc(),
            {},
        )
        panel_context.store.put(run)
        return run.model_dump()

    if run.selected_action_id and run.execution_checklist:
        if run.requires_human_confirmation and not run.human_ack:
            raise HTTPException(status_code=409, detail="ack required before execution")

        consume_session_step(
            run=run,
            ledger=panel_context.ledger,
            event_id=panel_context.eid("ev"),
            end_event_id=panel_context.eid("ev"),
            timestamp_utc=panel_context.now_utc(),
            route="defer_step:selected_action",
            step_index=int(run.selected_action_progress.get("phase", 0))
            if run.selected_action_progress
            else 0,
        )
        run, exec_result = execute_one(run)
        run.step_results.append(exec_result)
        run.last_step_result = exec_result
        run.actions_taken += 1

        panel_context.ledger.append(
            run_id,
            panel_context.eid("ev"),
            "selected_action_micro_step_executed",
            panel_context.now_utc(),
            {
                "action_id": exec_result.get("action_id"),
                "micro_step_id": exec_result.get("micro_step_id"),
                "completed": exec_result.get("completed"),
            },
        )

        if exec_result.get("completed"):
            run.pause_required = True
            run.pause_reason = "completed"

        if run.actions_remaining is not None and run.actions_remaining <= 0:
            run.pause_required = True
            run.pause_reason = "quota_exhausted"
            panel_context.ledger.append(
                run_id,
                panel_context.eid("ev"),
                "quota_exhausted_pause",
                panel_context.now_utc(),
                {},
            )

        panel_context.store.put(run)
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
        panel_context.store.put(run)
        return run.model_dump()

    step = steps[run.current_step_index]
    consume_session_step(
        run=run,
        ledger=panel_context.ledger,
        event_id=panel_context.eid("ev"),
        end_event_id=panel_context.eid("ev"),
        timestamp_utc=panel_context.now_utc(),
        route="defer_step:runplan",
        step_index=int(run.current_step_index),
    )
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

    panel_context.ledger.append(
        run_id,
        panel_context.eid("ev"),
        "runplan_step_executed",
        panel_context.now_utc(),
        event_payload,
    )
    panel_context.ledger.append(
        run_id,
        panel_context.eid("ev"),
        "action_executed",
        panel_context.now_utc(),
        {"action_index": run.actions_taken},
    )

    if run.current_step_index >= len(steps):
        run.pause_required = True
        run.pause_reason = "completed"

    if run.actions_remaining is not None and run.actions_remaining <= 0:
        run.pause_required = True
        run.pause_reason = "quota_exhausted"
        panel_context.ledger.append(
            run_id,
            panel_context.eid("ev"),
            "quota_exhausted_pause",
            panel_context.now_utc(),
            {},
        )

    panel_context.store.put(run)
    return run.model_dump()


def _stop_deferral(run_id: str) -> dict:
    run = panel_context.store.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")

    run.deferral_active = False
    run.pause_required = True
    run.pause_reason = "human_revoked"
    run.phase = max(run.phase, 7)

    panel_context.ledger.append(
        run_id,
        panel_context.eid("ev"),
        "deferral_session_ended",
        panel_context.now_utc(),
        {"reason": "human_revoked"},
    )
    panel_context.store.put(run)
    return run.model_dump()


def _start_session(run_id: str, max_steps: int) -> dict:
    run = panel_context.store.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    started_utc = panel_context.now_utc()
    start_session(
        run=run,
        max_steps=max_steps,
        started_utc=started_utc,
        ledger=panel_context.ledger,
        event_id=panel_context.eid("ev"),
    )
    panel_context.store.put(run)
    return run.model_dump()


def _end_session(run_id: str, reason: str) -> dict:
    run = panel_context.store.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    end_session(
        run=run,
        ended_utc=panel_context.now_utc(),
        ledger=panel_context.ledger,
        event_id=panel_context.eid("ev"),
        reason=reason,
    )
    panel_context.store.put(run)
    return run.model_dump()


def _record_policy_ack(run_id: str) -> dict:
    run = panel_context.store.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    current_hash = compute_policy_hash(get_policy_snapshot())
    record_policy_ack(
        run=run,
        current_policy_hash=current_hash,
        ledger=panel_context.ledger,
        event_id=panel_context.eid("ev"),
        timestamp_utc=panel_context.now_utc(),
    )
    panel_context.store.put(run)
    return run.model_dump()


def _select_action(run_id: str, selected_action_id: str) -> dict:
    run = panel_context.store.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")

    actions = _latest_proposals(run)
    if not actions:
        raise ValueError("no proposed actions available")

    selected = None
    for action in actions:
        if isinstance(action, dict) and action.get("action_id") == selected_action_id:
            selected = action
            break
    if selected is None:
        raise ValueError("invalid selected_action_id")

    run.selected_action_id = selected_action_id
    run.selected_action = selected
    run.execution_checklist = build_checklist(run, selected)
    panel_context.store.put(run)

    panel_context.ledger.append(
        run_id,
        panel_context.eid("ev"),
        "action_selected",
        panel_context.now_utc(),
        {"selected_action_id": selected_action_id, "kind": selected.get("kind")},
    )
    return run.model_dump()
