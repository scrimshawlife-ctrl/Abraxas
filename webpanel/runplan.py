from __future__ import annotations

from typing import Any, Dict, List, Literal, TYPE_CHECKING

from pydantic import BaseModel, Field

from abraxas.util.canonical_hash import canonical_hash

if TYPE_CHECKING:
    from webpanel.models import RunState

RunPlanStepKind = Literal[
    "extract_structure_v0",
    "compress_signal_v0",
    "propose_actions_v0",
    "select_action_v0",
    "summarize_context",
    "surface_unknowns",
    "propose_options",
    "prepare_next_questions",
]
RunPlanProduces = Literal["note", "options", "questions"]


class RunPlanStep(BaseModel):
    step_id: str
    kind: RunPlanStepKind
    input_refs: Dict[str, Any] = Field(default_factory=dict)
    params: Dict[str, Any] = Field(default_factory=dict)
    produces: RunPlanProduces
    requires_human_confirmation: bool = False


class RunPlan(BaseModel):
    plan_id: str
    run_id: str
    created_at_utc: str
    steps: List[RunPlanStep]
    deterministic_hash: str


def _plan_content_hash(run_state: "RunState", steps: List[RunPlanStep]) -> str:
    payload = {
        "signal_id": run_state.signal.signal_id,
        "tier": run_state.signal.tier,
        "lane": run_state.signal.lane,
        "requires_human_confirmation": run_state.requires_human_confirmation,
        "unknowns": run_state.context.unknowns,
        "steps": [step.model_dump() for step in steps],
    }
    return canonical_hash(payload)


def build_runplan(run_state: "RunState") -> RunPlan:
    steps: List[RunPlanStep] = []
    input_refs = {
        "signal_id": run_state.signal.signal_id,
        "context_id": run_state.context.context_id,
    }

    def add_step(kind: RunPlanStepKind, produces: RunPlanProduces, params: Dict[str, Any]) -> None:
        step_id = f"{len(steps) + 1:02d}_{kind}"
        steps.append(
            RunPlanStep(
                step_id=step_id,
                kind=kind,
                input_refs=input_refs,
                params=params,
                produces=produces,
                requires_human_confirmation=False,
            )
        )

    has_extract = False
    has_compress = False
    if isinstance(run_state.signal.payload, dict) and run_state.signal.payload:
        add_step(
            "extract_structure_v0",
            "note",
            {"payload_keys": sorted(run_state.signal.payload.keys())},
        )
        has_extract = True

    if has_extract:
        add_step(
            "compress_signal_v0",
            "note",
            {"source": "extract_structure_v0"},
        )
        has_compress = True

    if has_compress:
        add_step(
            "propose_actions_v0",
            "note",
            {"source": "compress_signal_v0"},
        )

    add_step(
        "summarize_context",
        "note",
        {
            "include": ["stable_elements", "unstable_elements", "risk_profile", "lanes"],
        },
    )
    if run_state.context.unknowns:
        add_step("surface_unknowns", "note", {"count": len(run_state.context.unknowns)})
    add_step(
        "propose_options",
        "options",
        {
            "lane": run_state.signal.lane,
            "requires_human_confirmation": run_state.requires_human_confirmation,
        },
    )
    if run_state.requires_human_confirmation:
        add_step(
            "prepare_next_questions",
            "questions",
            {
                "has_unknowns": bool(run_state.context.unknowns),
                "drift_flags": list(run_state.signal.drift_flags),
                "provenance_status": run_state.signal.provenance_status,
                "invariance_status": run_state.signal.invariance_status,
            },
        )

    deterministic_hash = _plan_content_hash(run_state, steps)
    plan_id = f"plan_{deterministic_hash[:16]}"
    created_at_utc = run_state.signal.timestamp_utc or run_state.created_at_utc
    return RunPlan(
        plan_id=plan_id,
        run_id=run_state.run_id,
        created_at_utc=created_at_utc,
        steps=steps,
        deterministic_hash=deterministic_hash,
    )


def execute_step(run_state: "RunState", step: RunPlanStep) -> Dict[str, Any]:
    if step.kind == "extract_structure_v0":
        from webpanel.structure_extract import (
            detect_unknowns,
            extract_claims_if_present,
            walk_payload,
        )

        payload = run_state.signal.payload
        extract = walk_payload(payload)
        unknowns = detect_unknowns(payload)
        claims = extract_claims_if_present(payload if isinstance(payload, dict) else {})
        paths = extract["paths"]
        sample_paths = [entry["path"] for entry in paths[:25]]
        numeric_metrics = extract["numeric_metrics"][:25]
        evidence_refs = extract["string_refs"][:25]
        unknowns_out = unknowns[:25]
        return {
            "kind": "extract_structure_v0",
            "keys_topology": {"paths_count": len(paths), "sample_paths": sample_paths},
            "numeric_metrics": numeric_metrics,
            "unknowns": unknowns_out,
            "evidence_refs": evidence_refs,
            "claims_present": len(claims) > 0,
            "claims_preview": claims[:5],
        }

    if step.kind == "compress_signal_v0":
        from webpanel.compress_signal import (
            build_uncertainty_map,
            classify_refs,
            compute_plan_pressure,
            next_questions,
            pick_salient_metrics,
            recommended_mode,
        )

        extracted = None
        for result in reversed(run_state.step_results):
            if isinstance(result, dict) and result.get("kind") == "extract_structure_v0":
                extracted = result
                break
        if extracted is None:
            return {"kind": "compress_signal_v0", "error": "missing_extract_structure_v0"}

        signal_meta = {
            "lane": run_state.signal.lane,
            "invariance_status": run_state.signal.invariance_status,
            "provenance_status": run_state.signal.provenance_status,
            "drift_flags": list(run_state.signal.drift_flags),
        }
        ctx = {"unknowns": list(run_state.context.unknowns)}

        plan_pressure = compute_plan_pressure(signal_meta, ctx, extracted)
        salient_metrics = pick_salient_metrics(extracted.get("numeric_metrics", []))
        uncertainty_map = build_uncertainty_map(extracted.get("unknowns", []), ctx["unknowns"])
        evidence_surface = classify_refs(extracted.get("evidence_refs", []))
        mode = recommended_mode(signal_meta, plan_pressure["score"])
        questions = next_questions(signal_meta, extracted, uncertainty_map)

        return {
            "kind": "compress_signal_v0",
            "plan_pressure": plan_pressure,
            "salient_metrics": salient_metrics,
            "uncertainty_map": uncertainty_map,
            "evidence_surface": evidence_surface,
            "recommended_mode": mode,
            "next_questions": questions,
        }

    if step.kind == "propose_actions_v0":
        from webpanel.propose_actions import propose_actions

        compressed = None
        for result in reversed(run_state.step_results):
            if isinstance(result, dict) and result.get("kind") == "compress_signal_v0":
                compressed = result
                break
        if compressed is None:
            return {"kind": "propose_actions_v0", "error": "missing_compress_signal_v0"}

        signal_meta = {
            "lane": run_state.signal.lane,
            "invariance_status": run_state.signal.invariance_status,
            "provenance_status": run_state.signal.provenance_status,
            "drift_flags": list(run_state.signal.drift_flags),
        }
        actions = propose_actions(
            signal_meta=signal_meta,
            compressed=compressed,
            requires_human_confirmation=run_state.requires_human_confirmation,
        )
        return {
            "kind": "propose_actions_v0",
            "actions": [action.model_dump() for action in actions],
        }

    if step.kind == "summarize_context":
        ctx = run_state.context
        return {
            "kind": "summary",
            "stable_count": len(ctx.stable_elements),
            "unstable_count": len(ctx.unstable_elements),
            "allowed_lanes": list(ctx.execution_lanes_allowed),
            "risk_of_action": ctx.risk_profile.risk_of_action,
            "risk_of_inaction": ctx.risk_profile.risk_of_inaction,
        }

    if step.kind == "surface_unknowns":
        unknowns = list(run_state.context.unknowns)
        return {
            "kind": "unknowns",
            "count": len(unknowns),
            "unknowns": unknowns,
            "note": f"{len(unknowns)} unknowns surfaced",
        }

    if step.kind == "propose_options":
        if run_state.signal.lane == "shadow":
            options = [
                {"id": "observe_only", "action": "observe_only"},
                {"id": "request_evidence", "action": "request_evidence"},
                {"id": "log", "action": "log"},
            ]
        else:
            options = [
                {"id": "ack_then_defer_2", "action": "ack_then_defer", "quota": 2},
                {"id": "ack_then_defer_3", "action": "ack_then_defer", "quota": 3},
                {"id": "ask_clarifying", "action": "ask_clarifying"},
            ]
        return {"kind": "options", "options": options}

    if step.kind == "prepare_next_questions":
        questions: List[str] = []
        if run_state.context.unknowns:
            for entry in run_state.context.unknowns:
                region_id = entry.get("region_id") if isinstance(entry, dict) else None
                reason_code = entry.get("reason_code") if isinstance(entry, dict) else None
                if region_id:
                    questions.append(f"Clarify region {region_id} ({reason_code})")
        if run_state.signal.drift_flags:
            questions.append("Which drift flags require follow-up?")
        if run_state.signal.invariance_status != "pass":
            questions.append("Can invariance be evaluated for this signal?")
        if run_state.signal.provenance_status != "complete":
            questions.append("What provenance gaps remain?")
        if not questions:
            questions.append("Are there additional context constraints to confirm?")
        return {"kind": "questions", "questions": questions}

    return {"kind": "noop"}
