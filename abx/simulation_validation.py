from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from abx.paper_trading import validate_portfolio_invariants
from abx.simulation_loop import SimulationResult

ProofStatus = Literal["VALID", "PARTIAL", "BROKEN", "NOT_COMPUTABLE", "ORPHANED", "INCONSISTENT"]


@dataclass(frozen=True)
class ReconstructabilityReport:
    ok: bool
    status: ProofStatus
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    chain_status: dict[str, str] = field(default_factory=dict)


def _classify_chain(result: SimulationResult) -> dict[str, str]:
    def s(ok: bool) -> str:
        return "implemented" if ok else "broken"

    return {
        "forecast_artifact": s(bool(result.forecast_artifacts)),
        "strategy_artifact": s(bool(result.strategy_artifacts)),
        "action_artifact": s(bool(result.action_artifacts)),
        "paper_trade_artifact": s(bool(result.paper_trade_artifacts)),
        "portfolio_transition_artifact": s(bool(result.portfolio_artifacts)),
        "simulation_artifact": s(bool(result.simulation_artifact)),
        "validator_result_artifact": "implemented",
        "proof_summary_artifact": "implemented",
    }


def validate_simulation_result(result: SimulationResult) -> ReconstructabilityReport:
    errors: list[str] = []
    warnings: list[str] = []

    forecast_ids = {decision.forecast_id for decision in result.decisions}
    fill_ids = {fill.fill_id for fill in result.fills}

    for intent in result.intents:
        if intent.forecast_id not in forecast_ids:
            errors.append(f"orphan-intent:{intent.intent_id}")
        if not intent.simulated_only:
            errors.append(f"missing-simulated-marker:intent:{intent.intent_id}")

    for transition in result.transitions:
        fill_id = str(transition.get("fill_id") or "")
        if fill_id not in fill_ids:
            errors.append(f"orphan-transition:{fill_id}")

    for fill in result.fills:
        if not fill.simulated_only:
            errors.append(f"missing-simulated-marker:fill:{fill.fill_id}")
        if fill.notional <= 0:
            errors.append(f"invalid-notional:{fill.fill_id}")

    for err in validate_portfolio_invariants(result.final_portfolio):
        errors.append(f"portfolio:{err}")

    if not result.explanations:
        warnings.append("missing-explainir")
    if not result.replay_hash:
        errors.append("missing-replay-hash")

    chain = _classify_chain(result)
    if any(v == "broken" for v in chain.values()):
        errors.append("proof-chain-broken")

    status: ProofStatus = "VALID"
    if errors:
        status = "BROKEN"
    elif warnings:
        status = "PARTIAL"

    return ReconstructabilityReport(
        ok=not errors,
        status=status,
        errors=sorted(set(errors)),
        warnings=sorted(set(warnings)),
        chain_status=chain,
    )


def validation_artifact(result: SimulationResult, report: ReconstructabilityReport) -> dict[str, Any]:
    return {
        "artifactType": "ValidationResultArtifact.v1",
        "artifactId": f"simulation-validation-{result.run_id}-{result.scenario_id}",
        "runId": result.run_id,
        "scenarioId": result.scenario_id,
        "status": report.status,
        "errors": list(report.errors),
        "warnings": list(report.warnings),
        "validatedArtifacts": [
            result.simulation_artifact.get("artifactId"),
            *[x.get("artifactId") for x in result.forecast_artifacts],
            *[x.get("artifactId") for x in result.strategy_artifacts],
            *[x.get("artifactId") for x in result.action_artifacts],
            *[x.get("artifactId") for x in result.paper_trade_artifacts],
            *[x.get("artifactId") or x.get("artifact_id") for x in result.portfolio_artifacts],
        ],
        "correlation": {
            "ledgerIds": [f"decision:{d.decision_id}" for d in result.decisions],
            "pointers": [f"replay:{result.replay_hash}"],
        },
    }


def proof_summary_artifact(result: SimulationResult, report: ReconstructabilityReport) -> dict[str, Any]:
    return {
        "artifactType": "ProofSummaryArtifact.v1",
        "artifactId": f"proof-summary-{result.run_id}-{result.scenario_id}",
        "runId": result.run_id,
        "scenarioId": result.scenario_id,
        "closureStatus": report.status,
        "chain": dict(report.chain_status),
        "errorCount": len(report.errors),
        "warningCount": len(report.warnings),
        "validatorArtifactId": f"simulation-validation-{result.run_id}-{result.scenario_id}",
    }
