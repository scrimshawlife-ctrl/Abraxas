from __future__ import annotations

from typing import Any
import hashlib
import json

from abraxas.operator.closure_card import run_operator_closure_card

from .binding_validator import run_binding_validator
from .green_state_attestation import run_green_state_attestation
from .invariance_harness import run_invariance_harness
from .self_build_approval_input import load_self_build_approval_input
from .self_build_approval_receipt import run_self_build_approval_receipt
from .self_build_dry_run import run_self_build_dry_run
from .self_build_multi_apply import run_self_build_multi_apply
from .self_build_operator_queue import run_self_build_operator_queue
from .self_build_patch_plan import run_self_build_patch_plan
from .self_build_batch_ledger import append_batch_entry
from .self_build_proposal import run_self_build_proposal
from .self_build_safety_gate import run_self_build_safety_gate
from .self_build_score_feedback import run_self_build_score_feedback
from .self_build_scoring import run_self_build_scoring


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _invariance_truth(invariance: dict[str, Any]) -> bool:
    return bool(
        invariance.get("registry_invariant") and invariance.get("validator_invariant") and invariance.get("bundle_invariant")
    )


def _feedback_summary(feedback: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": feedback.get("status", "NOT_COMPUTABLE"),
        "ranked_count": len(feedback.get("ranked_targets", [])) if isinstance(feedback.get("ranked_targets"), list) else 0,
        "flagged_count": len(feedback.get("flagged_targets", [])) if isinstance(feedback.get("flagged_targets"), list) else 0,
        "blocked_count": len(feedback.get("blocked_targets", [])) if isinstance(feedback.get("blocked_targets"), list) else 0,
        "canonical_hash": feedback.get("canonical_hash"),
    }


def run_self_build_batch_cycle() -> dict[str, Any]:
    phases: list[dict[str, Any]] = []

    green = run_green_state_attestation()
    preflight_green = (
        green.get("validator") == "PASS"
        and green.get("operator_health") == "GREEN"
        and green.get("notion_sync") == "PASS"
        and bool(green.get("invariance", {}).get("registry"))
        and bool(green.get("invariance", {}).get("validator"))
        and bool(green.get("invariance", {}).get("bundle"))
    )
    phases.append({"phase": "PREFLIGHT", "status": "PASS" if preflight_green else "STOP", "green_hash": green["canonical_hash"]})
    if not preflight_green:
        payload = {
            "schema_version": "SelfBuildBatchCycle.v1",
            "status": "STOPPED_PREFLIGHT_NOT_GREEN",
            "phase_results": phases,
            "post_validation": {"validator": "NOT_RUN", "operator_health": "NOT_RUN", "invariance": False},
            "scoring_hash": None,
            "score_feedback": _feedback_summary({"status": "NOT_RUN"}),
            "authority": {"mutation": False, "promotion": False, "execution": False, "analysis_only": True, "fail_closed": True},
        }
        payload["canonical_hash"] = _sha256_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))
        append_batch_entry(payload)
        return payload

    proposal = run_self_build_proposal()
    patch_plan = run_self_build_patch_plan()
    safety = run_self_build_safety_gate()
    dry_run = run_self_build_dry_run()
    queue = run_self_build_operator_queue()
    phases.append(
        {
            "phase": "PROPOSAL_STACK",
            "status": "PASS" if safety.get("all_plans_safe") else "STOP",
            "proposal_count": proposal["proposal_count"],
            "plan_count": patch_plan["plan_count"],
            "dry_run_count": dry_run["simulation_count"],
            "queue_count": queue["queue_count"],
        }
    )
    if not safety.get("all_plans_safe"):
        payload = {
            "schema_version": "SelfBuildBatchCycle.v1",
            "status": "STOPPED_SAFETY_GATE",
            "phase_results": phases,
            "post_validation": {"validator": "NOT_RUN", "operator_health": "NOT_RUN", "invariance": False},
            "scoring_hash": None,
            "score_feedback": _feedback_summary({"status": "NOT_RUN"}),
            "authority": {"mutation": False, "promotion": False, "execution": False, "analysis_only": True, "fail_closed": True},
        }
        payload["canonical_hash"] = _sha256_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))
        append_batch_entry(payload)
        return payload

    approval_input = load_self_build_approval_input()
    receipt = run_self_build_approval_receipt(approval_input["approved_ids"], approval_input["rejected_ids"])
    approved_count = len([row for row in receipt["approvals"] if row["status"] == "APPROVED"])
    phases.append({"phase": "APPROVAL", "status": "PASS" if approved_count > 0 else "WAIT", "approved_count": approved_count})

    if approved_count == 0:
        scoring = run_self_build_scoring()
        score_feedback = run_self_build_score_feedback()
        payload = {
            "schema_version": "SelfBuildBatchCycle.v1",
            "status": "WAITING_FOR_APPROVAL",
            "phase_results": phases,
            "post_validation": {"validator": "NOT_RUN", "operator_health": "NOT_RUN", "invariance": False},
            "scoring_hash": scoring["canonical_hash"],
            "score_feedback": _feedback_summary(score_feedback),
            "authority": {"mutation": False, "promotion": False, "execution": False, "analysis_only": True, "fail_closed": True},
        }
        payload["canonical_hash"] = _sha256_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))
        append_batch_entry(payload)
        return payload

    apply_result = run_self_build_multi_apply()
    phases.append({"phase": "APPLY", "status": apply_result["status"], "applied_count": apply_result.get("applied_count", 0)})

    validator = run_binding_validator()
    operator = run_operator_closure_card()
    invariance = run_invariance_harness()
    invariance_ok = _invariance_truth(invariance)
    scoring = run_self_build_scoring()
    score_feedback = run_self_build_score_feedback()

    post_validation = {
        "validator": validator["overall_status"],
        "operator_health": operator["health"],
        "invariance": invariance_ok,
    }
    phases.append({"phase": "POSTFLIGHT", "status": "PASS" if (validator["overall_status"] == "PASS" and operator["health"] == "GREEN" and invariance_ok) else "STOP"})

    final_status = "COMPLETE"
    if apply_result["status"] != "APPLIED":
        final_status = "STOPPED_APPLY"
    elif post_validation["validator"] != "PASS" or post_validation["operator_health"] != "GREEN" or not post_validation["invariance"]:
        final_status = "STOPPED_POSTFLIGHT"

    payload = {
        "schema_version": "SelfBuildBatchCycle.v1",
        "status": final_status,
        "phase_results": phases,
        "post_validation": post_validation,
        "scoring_hash": scoring["canonical_hash"],
        "score_feedback": _feedback_summary(score_feedback),
        "authority": {"mutation": False, "promotion": False, "execution": False, "analysis_only": True, "fail_closed": True},
    }
    payload["canonical_hash"] = _sha256_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return payload
