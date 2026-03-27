from __future__ import annotations

from pathlib import Path
from typing import Any

from abx.paper_trading import PortfolioState
from abx.proof_chain import build_proof_chain
from abx.runtime_trade_ledger import load_runtime_trade_records, write_runtime_trade_ledger
from abx.simulation_loop import SimulationScenario, compare_strategies, run_simulation
from abx.simulation_validation import proof_summary_artifact, validate_simulation_result, validation_artifact


class OperatorCommandError(RuntimeError):
    pass


def dispatch_operator_command(command: str, payload: dict[str, Any]) -> dict[str, Any]:
    if command == "run-simulation":
        scenario = _scenario_from_payload(payload)
        base_dir = Path(str(payload.get("base_dir") or "."))
        result = run_simulation(scenario)
        report = validate_simulation_result(result)
        validator = validation_artifact(result, report)
        proof_summary = proof_summary_artifact(result, report)

        artifacts_for_ledger = [
            *result.forecast_artifacts,
            *result.strategy_artifacts,
            *result.action_artifacts,
            *result.paper_trade_artifacts,
            *result.portfolio_artifacts,
            result.simulation_artifact,
            validator,
            proof_summary,
        ]
        ledger_path = write_runtime_trade_ledger(
            base_dir=base_dir,
            run_id=result.run_id,
            scenario_id=result.scenario_id,
            artifacts=artifacts_for_ledger,
        )
        ledger_records = load_runtime_trade_records(base_dir, result.run_id, result.scenario_id)
        proof_chain = build_proof_chain(
            run_id=result.run_id,
            scenario_id=result.scenario_id,
            chain_status=report.chain_status,
            ledger_records=ledger_records,
            validation_artifact=validator,
            proof_summary_artifact=proof_summary,
        )

        return {
            "simulation": result.simulation_artifact,
            "validation": validator,
            "proof_summary": proof_summary,
            "proof_chain": proof_chain,
            "ledger": {
                "path": ledger_path.as_posix(),
                "recordCount": len(ledger_records),
            },
        }

    if command == "compare-strategies":
        scenario = _scenario_from_payload(payload)
        strategy_a = dict(payload.get("strategy_a") or scenario.strategy_config)
        strategy_b = dict(payload.get("strategy_b") or scenario.strategy_config)
        artifact = compare_strategies(scenario, strategy_a=strategy_a, strategy_b=strategy_b)
        return artifact.__dict__

    if command == "inspect-proof-chain":
        scenario = _scenario_from_payload(payload)
        base_dir = Path(str(payload.get("base_dir") or "."))
        result = run_simulation(scenario)
        report = validate_simulation_result(result)
        validator = validation_artifact(result, report)
        proof_summary = proof_summary_artifact(result, report)
        ledger_records = load_runtime_trade_records(base_dir, result.run_id, result.scenario_id)
        return build_proof_chain(
            run_id=result.run_id,
            scenario_id=result.scenario_id,
            chain_status=report.chain_status,
            ledger_records=ledger_records,
            validation_artifact=validator,
            proof_summary_artifact=proof_summary,
        )

    if command == "inspect-portfolio":
        scenario = _scenario_from_payload(payload)
        result = run_simulation(scenario)
        return {
            "runId": result.run_id,
            "scenarioId": result.scenario_id,
            "cash": result.final_portfolio.cash,
            "equity": result.final_portfolio.equity,
            "realizedPnl": result.final_portfolio.realized_pnl,
            "exposure": result.final_portfolio.exposure,
            "positions": {k: v.__dict__ for k, v in sorted(result.final_portfolio.positions.items())},
        }

    if command == "inspect-validation":
        scenario = _scenario_from_payload(payload)
        result = run_simulation(scenario)
        report = validate_simulation_result(result)
        return validation_artifact(result, report)

    if command == "inspect-rejections":
        scenario = _scenario_from_payload(payload)
        result = run_simulation(scenario)
        return {
            "runId": result.run_id,
            "scenarioId": result.scenario_id,
            "rejections": [r.__dict__ for r in result.rejections],
        }

    raise OperatorCommandError(f"unknown-command:{command}")


def _scenario_from_payload(payload: dict[str, Any]) -> SimulationScenario:
    run_id = str(payload.get("run_id") or "RUN-OP")
    scenario_id = str(payload.get("scenario_id") or "SCN-OP")
    events = list(payload.get("events") or [])
    strategy_config = dict(payload.get("strategy_config") or {})
    portfolio_obj = payload.get("initial_portfolio") or {}
    portfolio = PortfolioState(
        run_id=run_id,
        cash=float(portfolio_obj.get("cash") or 10_000.0),
        equity=float(portfolio_obj.get("equity") or portfolio_obj.get("cash") or 10_000.0),
        realized_pnl=float(portfolio_obj.get("realized_pnl") or 0.0),
        exposure=float(portfolio_obj.get("exposure") or 0.0),
        max_exposure=float(portfolio_obj.get("max_exposure") or 20_000.0),
        max_positions=int(portfolio_obj.get("max_positions") or 5),
        allow_margin=bool(portfolio_obj.get("allow_margin") or False),
        positions={},
    )
    return SimulationScenario(
        scenario_id=scenario_id,
        run_id=run_id,
        events=events,
        initial_portfolio=portfolio,
        strategy_config=strategy_config,
    )
