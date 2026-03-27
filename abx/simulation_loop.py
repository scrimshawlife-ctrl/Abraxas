from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from abx.core.types import EvidenceRef
from abx.explain_ir import ExplainIR, ExplainProvenance
from abx.paper_trading import (
    ForecastSignal,
    PortfolioState,
    RejectionArtifact,
    SimulatedFill,
    StrategyDecision,
    TradeIntent,
    apply_fill,
    build_decision,
    build_trade_intent,
    rank_strategy_decisions,
    simulate_fill,
    snapshot_artifact,
)
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


@dataclass(frozen=True)
class SimulationScenario:
    scenario_id: str
    run_id: str
    events: list[dict[str, Any]]
    initial_portfolio: PortfolioState
    strategy_config: dict[str, Any]


@dataclass(frozen=True)
class SimulationResult:
    scenario_id: str
    run_id: str
    final_portfolio: PortfolioState
    decisions: list[StrategyDecision]
    intents: list[TradeIntent]
    fills: list[SimulatedFill]
    rejections: list[RejectionArtifact]
    transitions: list[dict[str, Any]]
    explanations: list[ExplainIR]
    replay_hash: str
    forecast_artifacts: list[dict[str, Any]]
    strategy_artifacts: list[dict[str, Any]]
    action_artifacts: list[dict[str, Any]]
    paper_trade_artifacts: list[dict[str, Any]]
    portfolio_artifacts: list[dict[str, Any]]
    simulation_artifact: dict[str, Any]


@dataclass(frozen=True)
class StrategyComparisonArtifact:
    artifact_id: str
    scenario_id: str
    run_id: str
    strategy_a: dict[str, Any]
    strategy_b: dict[str, Any]
    metrics: dict[str, Any]
    decision_divergences: list[dict[str, Any]]
    replay_hash_a: str
    replay_hash_b: str


def _build_signal(run_id: str, index: int, event: dict[str, Any]) -> ForecastSignal:
    return ForecastSignal(
        run_id=run_id,
        forecast_id=str(event.get("forecast_id") or f"forecast-{index}"),
        asset_id=str(event.get("asset_id") or "UNKNOWN"),
        score=float(event.get("score") or 0.0),
        confidence=float(event.get("confidence") or 0.0),
        direction="BUY",
        rationale_ref=str(event.get("rationale_ref") or "scenario_input"),
    )


def _explain(decision: StrategyDecision, scenario: SimulationScenario) -> ExplainIR:
    return ExplainIR(
        explain_rune_id="RUNE.STRATEGY",
        event_type="strategy.decision",
        target_id=decision.forecast_id,
        summary=f"Decision {decision.status} for {decision.asset_id}: {decision.reason}",
        metric_logic={"score": decision.score, "confidence": decision.confidence},
        evidence=[
            EvidenceRef(
                id=decision.forecast_id,
                source="simulation.scenario",
                pointer=f"scenario:{scenario.scenario_id}",
                kind="observation",
            )
        ],
        provenance=ExplainProvenance(observed=["score", "confidence"], inferred=["decision_status"], speculative=[]),
        confidence=max(0.0, min(1.0, decision.confidence)),
    )


def run_simulation(scenario: SimulationScenario) -> SimulationResult:
    min_conf = float(scenario.strategy_config.get("min_confidence", 0.6))
    risk_fraction = float(scenario.strategy_config.get("position_risk_fraction", 0.1))
    max_notional = float(scenario.strategy_config.get("max_notional", 1000.0))

    portfolio = scenario.initial_portfolio
    decisions: list[StrategyDecision] = []
    intents: list[TradeIntent] = []
    fills: list[SimulatedFill] = []
    rejections: list[RejectionArtifact] = []
    transitions: list[dict[str, Any]] = []
    explanations: list[ExplainIR] = []
    forecast_artifacts: list[dict[str, Any]] = []
    strategy_artifacts: list[dict[str, Any]] = []
    action_artifacts: list[dict[str, Any]] = []
    paper_trade_artifacts: list[dict[str, Any]] = []
    portfolio_artifacts: list[dict[str, Any]] = []

    event_by_forecast = {
        str(event.get("forecast_id") or f"forecast-{i}"): event for i, event in enumerate(scenario.events)
    }

    for index, event in enumerate(scenario.events):
        signal = _build_signal(scenario.run_id, index, event)
        forecast_artifacts.append(
            {
                "artifactType": "ForecastArtifact.v1",
                "artifactId": f"forecast-{scenario.run_id}-{signal.forecast_id}",
                "runId": scenario.run_id,
                "forecastId": signal.forecast_id,
                "assetId": signal.asset_id,
                "score": signal.score,
                "confidence": signal.confidence,
            }
        )
        decision = build_decision(signal, min_confidence=min_conf)
        decisions.append(decision)

    for decision in rank_strategy_decisions(decisions):
        strategy_artifacts.append(
            {
                "artifactType": "StrategyArtifact.v1",
                "artifactId": f"strategy-{scenario.run_id}-{decision.decision_id}",
                "runId": scenario.run_id,
                "forecastId": decision.forecast_id,
                "decisionId": decision.decision_id,
                "status": decision.status,
                "lineage": dict(decision.lineage),
            }
        )
        explanations.append(_explain(decision, scenario))

        event = event_by_forecast.get(decision.forecast_id, {})
        price = float(event.get("entry_price") or 0.0)

        intent_or_rejection = build_trade_intent(
            decision,
            position_risk_fraction=risk_fraction,
            max_notional=max_notional,
            reference_price=price,
        )
        if isinstance(intent_or_rejection, RejectionArtifact):
            rejections.append(intent_or_rejection)
            action_artifacts.append(
                {
                    "artifactType": "ActionRejectionArtifact.v1",
                    "artifactId": f"action-rejection-{intent_or_rejection.rejection_id}",
                    "runId": scenario.run_id,
                    "forecastId": decision.forecast_id,
                    "decisionId": decision.decision_id,
                    "reason": intent_or_rejection.reason,
                }
            )
            continue

        if len(portfolio.positions) >= portfolio.max_positions and intent_or_rejection.asset_id not in portfolio.positions:
            rej = RejectionArtifact(
                rejection_id=f"rejection-{intent_or_rejection.intent_id}",
                run_id=portfolio.run_id,
                forecast_id=intent_or_rejection.forecast_id,
                asset_id=intent_or_rejection.asset_id,
                reason="max_position_count_exceeded",
                simulated_only=True,
            )
            rejections.append(rej)
            action_artifacts.append(
                {
                    "artifactType": "ActionRejectionArtifact.v1",
                    "artifactId": f"action-rejection-{rej.rejection_id}",
                    "runId": scenario.run_id,
                    "forecastId": decision.forecast_id,
                    "decisionId": decision.decision_id,
                    "reason": rej.reason,
                }
            )
            continue

        fill = simulate_fill(intent_or_rejection, market_price=price)
        if portfolio.exposure + fill.notional > portfolio.max_exposure:
            rej = RejectionArtifact(
                rejection_id=f"rejection-{intent_or_rejection.intent_id}",
                run_id=portfolio.run_id,
                forecast_id=intent_or_rejection.forecast_id,
                asset_id=intent_or_rejection.asset_id,
                reason="max_exposure_exceeded",
                simulated_only=True,
            )
            rejections.append(rej)
            action_artifacts.append(
                {
                    "artifactType": "ActionRejectionArtifact.v1",
                    "artifactId": f"action-rejection-{rej.rejection_id}",
                    "runId": scenario.run_id,
                    "forecastId": decision.forecast_id,
                    "decisionId": decision.decision_id,
                    "reason": rej.reason,
                }
            )
            continue

        intents.append(intent_or_rejection)
        action_artifacts.append(
            {
                "artifactType": "ActionDecisionArtifact.v1",
                "artifactId": f"action-decision-{intent_or_rejection.intent_id}",
                "runId": scenario.run_id,
                "forecastId": decision.forecast_id,
                "decisionId": decision.decision_id,
                "intentId": intent_or_rejection.intent_id,
            }
        )

        portfolio, transition = apply_fill(portfolio, fill)
        fills.append(fill)
        transitions.append(transition.__dict__)
        paper_trade_artifacts.append(
            {
                "artifactType": "PaperTradeArtifact.v1",
                "artifactId": f"paper-trade-{fill.fill_id}",
                "runId": scenario.run_id,
                "fillId": fill.fill_id,
                "intentId": fill.intent_id,
                "simulatedOnly": fill.simulated_only,
            }
        )
        portfolio_artifacts.append(
            {
                "artifactType": "PortfolioTransitionArtifact.v1",
                "artifactId": f"portfolio-transition-{transition.transition_id}",
                "runId": scenario.run_id,
                "transitionId": transition.transition_id,
                "fillId": transition.fill_id,
            }
        )
        snapshot = snapshot_artifact(portfolio, artifact_id=f"portfolio-snapshot-{transition.transition_id}").__dict__
        snapshot["artifactType"] = "PortfolioSnapshotArtifact.v1"
        snapshot["artifactId"] = snapshot.pop("artifact_id")
        snapshot["runId"] = snapshot.pop("run_id")
        portfolio_artifacts.append(snapshot)

        exit_price = float(event.get("exit_price") or 0.0)
        if exit_price > 0.0:
            exit_fill = simulate_fill(
                TradeIntent(
                    intent_id=f"intent-exit-{intent_or_rejection.intent_id}",
                    run_id=portfolio.run_id,
                    asset_id=intent_or_rejection.asset_id,
                    side="SELL",
                    units=intent_or_rejection.units,
                    limit_price=exit_price,
                    simulated_only=True,
                    forecast_id=intent_or_rejection.forecast_id,
                    decision_id=intent_or_rejection.decision_id,
                    rationale_ref="scenario_exit",
                ),
                market_price=exit_price,
            )
            portfolio, transition_exit = apply_fill(portfolio, exit_fill)
            fills.append(exit_fill)
            transitions.append(transition_exit.__dict__)
            paper_trade_artifacts.append(
                {
                    "artifactType": "PaperTradeArtifact.v1",
                    "artifactId": f"paper-trade-{exit_fill.fill_id}",
                    "runId": scenario.run_id,
                    "fillId": exit_fill.fill_id,
                    "intentId": exit_fill.intent_id,
                    "simulatedOnly": exit_fill.simulated_only,
                }
            )
            portfolio_artifacts.append(
                {
                    "artifactType": "PortfolioTransitionArtifact.v1",
                    "artifactId": f"portfolio-transition-{transition_exit.transition_id}",
                    "runId": scenario.run_id,
                    "transitionId": transition_exit.transition_id,
                    "fillId": transition_exit.fill_id,
                }
            )
            snapshot_exit = snapshot_artifact(portfolio, artifact_id=f"portfolio-snapshot-{transition_exit.transition_id}").__dict__
            snapshot_exit["artifactType"] = "PortfolioSnapshotArtifact.v1"
            snapshot_exit["artifactId"] = snapshot_exit.pop("artifact_id")
            snapshot_exit["runId"] = snapshot_exit.pop("run_id")
            portfolio_artifacts.append(snapshot_exit)

    replay_payload = {
        "scenario_id": scenario.scenario_id,
        "run_id": scenario.run_id,
        "decisions": [d.__dict__ for d in decisions],
        "intents": [i.__dict__ for i in intents],
        "fills": [f.__dict__ for f in fills],
        "rejections": [r.__dict__ for r in rejections],
        "transitions": transitions,
        "portfolio": snapshot_artifact(portfolio, artifact_id="final").__dict__,
    }
    replay_hash = sha256_bytes(dumps_stable(replay_payload).encode("utf-8"))

    simulation_artifact = {
        "artifactType": "SimulationArtifact.v1",
        "artifactId": f"simulation-result-{scenario.run_id}-{scenario.scenario_id}",
        "runId": scenario.run_id,
        "scenarioId": scenario.scenario_id,
        "replayHash": replay_hash,
        "tradeCount": len(fills),
    }

    return SimulationResult(
        scenario_id=scenario.scenario_id,
        run_id=scenario.run_id,
        final_portfolio=portfolio,
        decisions=decisions,
        intents=intents,
        fills=fills,
        rejections=rejections,
        transitions=transitions,
        explanations=explanations,
        replay_hash=replay_hash,
        forecast_artifacts=forecast_artifacts,
        strategy_artifacts=strategy_artifacts,
        action_artifacts=action_artifacts,
        paper_trade_artifacts=paper_trade_artifacts,
        portfolio_artifacts=portfolio_artifacts,
        simulation_artifact=simulation_artifact,
    )


def compare_strategies(
    scenario: SimulationScenario,
    *,
    strategy_a: dict[str, Any],
    strategy_b: dict[str, Any],
) -> StrategyComparisonArtifact:
    res_a = run_simulation(
        SimulationScenario(
            scenario_id=scenario.scenario_id,
            run_id=scenario.run_id,
            events=list(scenario.events),
            initial_portfolio=scenario.initial_portfolio,
            strategy_config=dict(strategy_a),
        )
    )
    res_b = run_simulation(
        SimulationScenario(
            scenario_id=scenario.scenario_id,
            run_id=scenario.run_id,
            events=list(scenario.events),
            initial_portfolio=scenario.initial_portfolio,
            strategy_config=dict(strategy_b),
        )
    )

    divergence = []
    by_forecast_a = {d.forecast_id: d.status for d in res_a.decisions}
    by_forecast_b = {d.forecast_id: d.status for d in res_b.decisions}
    for forecast_id in sorted(set(by_forecast_a) | set(by_forecast_b)):
        status_a = by_forecast_a.get(forecast_id)
        status_b = by_forecast_b.get(forecast_id)
        if status_a != status_b:
            divergence.append({"forecast_id": forecast_id, "strategy_a": status_a, "strategy_b": status_b})

    metrics = {
        "acceptance_count_a": len([d for d in res_a.decisions if d.status == "ACCEPT"]),
        "acceptance_count_b": len([d for d in res_b.decisions if d.status == "ACCEPT"]),
        "rejection_count_a": len(res_a.rejections),
        "rejection_count_b": len(res_b.rejections),
        "realized_pnl_a": res_a.final_portfolio.realized_pnl,
        "realized_pnl_b": res_b.final_portfolio.realized_pnl,
        "final_equity_a": res_a.final_portfolio.equity,
        "final_equity_b": res_b.final_portfolio.equity,
        "exposure_a": res_a.final_portfolio.exposure,
        "exposure_b": res_b.final_portfolio.exposure,
        "trade_count_a": len(res_a.fills),
        "trade_count_b": len(res_b.fills),
    }

    return StrategyComparisonArtifact(
        artifact_id=f"strategy-comparison-{scenario.run_id}-{scenario.scenario_id}",
        scenario_id=scenario.scenario_id,
        run_id=scenario.run_id,
        strategy_a=dict(strategy_a),
        strategy_b=dict(strategy_b),
        metrics=metrics,
        decision_divergences=divergence,
        replay_hash_a=res_a.replay_hash,
        replay_hash_b=res_b.replay_hash,
    )
