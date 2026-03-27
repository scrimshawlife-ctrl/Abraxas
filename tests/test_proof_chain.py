from __future__ import annotations

from abx.proof_chain import build_proof_chain, classify_proof_chain


def test_classify_proof_chain_statuses() -> None:
    chain = {
        "forecast_artifact": "implemented",
        "strategy_artifact": "implemented",
        "action_artifact": "implemented",
        "paper_trade_artifact": "implemented",
        "portfolio_transition_artifact": "implemented",
        "simulation_artifact": "implemented",
        "ledger_record": "implemented",
        "validator_result_artifact": "implemented",
        "proof_summary_artifact": "implemented",
    }
    assert classify_proof_chain(chain) == "VALID"

    chain["ledger_record"] = "partial"
    assert classify_proof_chain(chain) == "PARTIAL"


def test_build_proof_chain_orphan_detection() -> None:
    payload = build_proof_chain(
        run_id="RUN-1",
        scenario_id="SCN-1",
        chain_status={
            "forecast_artifact": "implemented",
            "strategy_artifact": "implemented",
            "action_artifact": "implemented",
            "paper_trade_artifact": "implemented",
            "portfolio_transition_artifact": "implemented",
            "simulation_artifact": "implemented",
            "validator_result_artifact": "implemented",
            "proof_summary_artifact": "implemented",
        },
        ledger_records=[],
        validation_artifact={"artifactId": "val-1", "validatedArtifacts": ["a"]},
        proof_summary_artifact={"artifactId": "proof-1", "runId": "WRONG"},
    )
    assert payload["status"] == "ORPHANED"
