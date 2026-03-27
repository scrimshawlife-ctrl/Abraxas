from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from abx.closure_summary import build_closure_summary
from abx.lifecycle_policy import enforce_lane_policy, evaluate_promotion_eligibility
from abx.operator_console import dispatch_operator_command


@dataclass(frozen=True)
class CanonChecksReport:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checks: dict[str, str] = field(default_factory=dict)


def run_canon_checks(payload: dict[str, Any]) -> CanonChecksReport:
    base_dir = Path(str(payload.get("base_dir") or "."))
    run_output = dispatch_operator_command("run-simulation", payload)

    errors: list[str] = []
    warnings: list[str] = []
    checks: dict[str, str] = {}

    validation = run_output.get("validation") or {}
    proof_chain = run_output.get("proof_chain") or {}

    # Validator run linkage gate
    if not validation.get("runId"):
        errors.append("validation-missing-runId")
    checks["validation_run_linkage"] = "implemented" if validation.get("runId") else "broken"

    # Proof chain completeness gate
    proof_status = str(proof_chain.get("status") or "NOT_COMPUTABLE")
    if proof_status != "VALID":
        errors.append(f"proof-chain-not-valid:{proof_status}")
    checks["proof_chain"] = "implemented" if proof_status == "VALID" else "broken"

    # Closure summary gate
    closure = build_closure_summary(
        base_dir=base_dir,
        run_id=str(payload.get("run_id") or "RUN-OP"),
        scenario_id=str(payload.get("scenario_id") or "SCN-OP"),
    )
    if closure.status != "VALID":
        warnings.append(f"closure-summary-{closure.status.lower()}")
    checks["closure_summary"] = "implemented" if closure.status == "VALID" else "partial"

    # Lifecycle lane policy check (scaffolded via payload)
    lane_policy = enforce_lane_policy(
        lane=str(payload.get("lane") or "SHADOW"),
        influence_policy=str(payload.get("influence_policy") or "NONE"),
        influences_active_path=bool(payload.get("influences_active_path") or False),
    )
    if lane_policy.status != "VALID":
        errors.extend([f"lane-policy:{v}" for v in lane_policy.violations])
    checks["lane_policy"] = "implemented" if lane_policy.status == "VALID" else "broken"

    # Promotion eligibility check
    promotion = evaluate_promotion_eligibility(
        module_id=str(payload.get("module_id") or "simulation.core"),
        current_lane=str(payload.get("current_lane") or "SHADOW"),
        target_lane=str(payload.get("target_lane") or "ACTIVE"),
        evidence=dict(payload.get("promotion_evidence") or {}),
    )
    if not promotion.eligible:
        warnings.append("promotion-not-eligible")
    checks["promotion_eligibility"] = "implemented" if promotion.eligible else "partial"

    return CanonChecksReport(ok=not errors, errors=sorted(set(errors)), warnings=sorted(set(warnings)), checks=checks)
