from __future__ import annotations

from pathlib import Path
from typing import Any

from abx.canon_checks import run_canon_checks
from abx.closure_summary import build_closure_summary
from abx.continuity import build_continuity_summary
from abx.frame_adapters import assemble_resonance_frame
from abx.coupling_audit import audit_coupling
from abx.invariance_harness import run_invariance_harness
from abx.lifecycle_policy import evaluate_promotion_eligibility
from abx.operator_console import dispatch_operator_command
from abx.runtime_orchestrator import execute_run_plan


def run_operator_workflow(workflow: str, payload: dict[str, Any]) -> dict[str, Any]:
    if workflow == "run-simulation-workflow":
        return dispatch_operator_command("run-simulation", payload)
    if workflow == "compare-strategies-workflow":
        return dispatch_operator_command("compare-strategies", payload)
    if workflow == "inspect-proof-workflow":
        return dispatch_operator_command("inspect-proof-chain", payload)
    if workflow == "inspect-current-frame":
        return assemble_resonance_frame(payload)
    if workflow == "inspect-continuity":
        base_dir = Path(str(payload.get("base_dir") or "."))
        return build_continuity_summary(base_dir=base_dir, payload=payload).__dict__
    if workflow == "inspect-portfolio-workflow":
        return dispatch_operator_command("inspect-portfolio", payload)
    if workflow == "run-closure-workflow":
        base_dir = Path(str(payload.get("base_dir") or "."))
        return build_closure_summary(
            base_dir=base_dir,
            run_id=str(payload.get("run_id") or "RUN-OP"),
            scenario_id=str(payload.get("scenario_id") or "SCN-OP"),
        ).__dict__
    if workflow == "run-invariance-workflow":
        runs = int(payload.get("runs") or 12)
        return run_invariance_harness(
            target="operator.run-simulation",
            runs=runs,
            producer=lambda: dispatch_operator_command("run-simulation", payload),
        ).__dict__
    if workflow == "inspect-promotion-pack-workflow":
        return evaluate_promotion_eligibility(
            module_id=str(payload.get("module_id") or "simulation.core"),
            current_lane=str(payload.get("current_lane") or "SHADOW"),
            target_lane=str(payload.get("target_lane") or "ACTIVE"),
            evidence=dict(payload.get("promotion_evidence") or {}),
        ).__dict__
    if workflow == "run-runtime-orchestrator-workflow":
        return execute_run_plan(payload)
    if workflow == "run-coupling-audit-workflow":
        base_dir = Path(str(payload.get("base_dir") or "."))
        return audit_coupling(repo_root=base_dir).__dict__
    if workflow == "run-canon-checks-workflow":
        return run_canon_checks(payload).__dict__

    raise ValueError(f"unknown-workflow:{workflow}")
