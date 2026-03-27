from __future__ import annotations

from typing import Any

PROOF_CHAIN_ORDER = [
    "forecast_artifact",
    "strategy_artifact",
    "action_artifact",
    "paper_trade_artifact",
    "portfolio_transition_artifact",
    "simulation_artifact",
    "ledger_record",
    "validator_result_artifact",
    "proof_summary_artifact",
]


def classify_proof_chain(chain: dict[str, str]) -> str:
    values = [chain.get(k, "not_computable") for k in PROOF_CHAIN_ORDER]
    if all(v == "implemented" for v in values):
        return "VALID"
    if any(v == "orphaned" for v in values):
        return "ORPHANED"
    if any(v == "broken" for v in values):
        return "BROKEN"
    if any(v == "inconsistent" for v in values):
        return "INCONSISTENT"
    if all(v == "not_computable" for v in values):
        return "NOT_COMPUTABLE"
    return "PARTIAL"


def build_proof_chain(
    *,
    run_id: str,
    scenario_id: str,
    chain_status: dict[str, str],
    ledger_records: list[dict[str, Any]],
    validation_artifact: dict[str, Any],
    proof_summary_artifact: dict[str, Any],
) -> dict[str, Any]:
    chain = dict(chain_status)
    chain["ledger_record"] = "implemented" if ledger_records else "partial"

    validated = validation_artifact.get("validatedArtifacts") if isinstance(validation_artifact.get("validatedArtifacts"), list) else []
    if not validated:
        chain["validator_result_artifact"] = "broken"

    if str(proof_summary_artifact.get("runId") or "") != run_id:
        chain["proof_summary_artifact"] = "orphaned"

    status = classify_proof_chain(chain)
    return {
        "artifactType": "ProofChainArtifact.v1",
        "artifactId": f"proof-chain-{run_id}-{scenario_id}",
        "runId": run_id,
        "scenarioId": scenario_id,
        "status": status,
        "chain": chain,
        "ledgerRecordCount": len(ledger_records),
        "validatorArtifactId": validation_artifact.get("artifactId"),
        "proofSummaryArtifactId": proof_summary_artifact.get("artifactId"),
    }
