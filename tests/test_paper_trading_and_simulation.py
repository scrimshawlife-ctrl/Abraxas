from __future__ import annotations

import pytest

from abx.paper_trading import (
    ForecastSignal,
    PortfolioState,
    build_decision,
    build_trade_intent,
    simulate_fill,
    apply_fill,
    validate_portfolio_invariants,
)
from abx.simulation_loop import SimulationScenario, compare_strategies, run_simulation
from abx.simulation_validation import (
    proof_summary_artifact,
    validate_simulation_result,
    validation_artifact,
)


def _initial_portfolio(run_id: str = "RUN-SIM-001") -> PortfolioState:
    return PortfolioState(
        run_id=run_id,
        cash=10_000.0,
        equity=10_000.0,
        realized_pnl=0.0,
        exposure=0.0,
        max_exposure=20_000.0,
        max_positions=3,
        positions={},
    )


def test_paper_trade_entry_and_exit_pnl_and_reconciliation() -> None:
    signal = ForecastSignal(
        run_id="RUN-PT-001",
        forecast_id="f-1",
        asset_id="BTC",
        score=0.8,
        confidence=0.9,
        direction="BUY",
        rationale_ref="forecast",
    )
    decision = build_decision(signal, min_confidence=0.6)
    intent = build_trade_intent(decision, position_risk_fraction=0.1, max_notional=5000.0, reference_price=100.0)

    fill = simulate_fill(intent, market_price=100.0)
    p1, _ = apply_fill(_initial_portfolio("RUN-PT-001"), fill)
    assert "BTC" in p1.positions

    exit_intent = intent.__class__(
        intent_id="intent-exit",
        run_id=intent.run_id,
        asset_id=intent.asset_id,
        side="SELL",
        units=intent.units,
        limit_price=110.0,
        simulated_only=True,
        forecast_id=intent.forecast_id,
        decision_id=intent.decision_id,
        rationale_ref="exit",
    )
    exit_fill = simulate_fill(exit_intent, market_price=110.0)
    p2, _ = apply_fill(p1, exit_fill)
    assert p2.realized_pnl > 0.0
    assert "BTC" not in p2.positions
    assert validate_portfolio_invariants(p2) == []


def test_paper_trade_rejects_low_confidence() -> None:
    signal = ForecastSignal(
        run_id="RUN-PT-002",
        forecast_id="f-2",
        asset_id="ETH",
        score=0.5,
        confidence=0.2,
        direction="BUY",
        rationale_ref="forecast",
    )
    decision = build_decision(signal, min_confidence=0.6)
    reject = build_trade_intent(decision, position_risk_fraction=0.1, max_notional=5000.0, reference_price=100.0)
    assert getattr(reject, "reason", "") == "confidence_too_low"


def test_paper_trade_rejects_insufficient_capital() -> None:
    signal = ForecastSignal(
        run_id="RUN-PT-003",
        forecast_id="f-3",
        asset_id="SOL",
        score=0.9,
        confidence=0.9,
        direction="BUY",
        rationale_ref="forecast",
    )
    decision = build_decision(signal, min_confidence=0.6)
    intent = build_trade_intent(decision, position_risk_fraction=1.0, max_notional=50_000.0, reference_price=100.0)
    fill = simulate_fill(intent, market_price=100.0)

    with pytest.raises(ValueError, match="insufficient_capital"):
        apply_fill(_initial_portfolio("RUN-PT-003"), fill)


def test_paper_trade_rejects_duplicate_transition() -> None:
    signal = ForecastSignal(
        run_id="RUN-PT-004",
        forecast_id="f-4",
        asset_id="SOL",
        score=0.9,
        confidence=0.9,
        direction="BUY",
        rationale_ref="forecast",
    )
    decision = build_decision(signal, min_confidence=0.6)
    intent = build_trade_intent(decision, position_risk_fraction=0.1, max_notional=1000.0, reference_price=100.0)
    fill = simulate_fill(intent, market_price=100.0)
    p1, _ = apply_fill(_initial_portfolio("RUN-PT-004"), fill)

    with pytest.raises(ValueError, match="duplicate_transition_id"):
        apply_fill(p1, fill)


def test_simulation_replay_is_deterministic() -> None:
    scenario = SimulationScenario(
        scenario_id="SCN-1",
        run_id="RUN-SIM-001",
        events=[
            {"forecast_id": "f-1", "asset_id": "BTC", "score": 0.8, "confidence": 0.9, "entry_price": 100.0, "exit_price": 110.0},
            {"forecast_id": "f-2", "asset_id": "ETH", "score": 0.7, "confidence": 0.5, "entry_price": 50.0, "exit_price": 45.0},
        ],
        initial_portfolio=_initial_portfolio(),
        strategy_config={"min_confidence": 0.6, "position_risk_fraction": 0.1, "max_notional": 1000.0},
    )

    r1 = run_simulation(scenario)
    r2 = run_simulation(scenario)
    assert r1.replay_hash == r2.replay_hash
    assert r1.final_portfolio.equity == r2.final_portfolio.equity


def test_strategy_comparison_artifact_has_deltas() -> None:
    scenario = SimulationScenario(
        scenario_id="SCN-2",
        run_id="RUN-SIM-002",
        events=[
            {"forecast_id": "f-1", "asset_id": "BTC", "score": 0.8, "confidence": 0.9, "entry_price": 100.0, "exit_price": 110.0},
            {"forecast_id": "f-2", "asset_id": "ETH", "score": 0.6, "confidence": 0.7, "entry_price": 100.0, "exit_price": 90.0},
        ],
        initial_portfolio=_initial_portfolio("RUN-SIM-002"),
        strategy_config={"min_confidence": 0.6, "position_risk_fraction": 0.1, "max_notional": 1000.0},
    )
    comp = compare_strategies(
        scenario,
        strategy_a={"min_confidence": 0.6, "position_risk_fraction": 0.1, "max_notional": 1000.0},
        strategy_b={"min_confidence": 0.8, "position_risk_fraction": 0.1, "max_notional": 1000.0},
    )
    assert comp.metrics["trade_count_a"] >= 0
    assert comp.metrics["trade_count_b"] >= 0
    assert comp.replay_hash_a
    assert comp.replay_hash_b


def test_simulation_validation_and_proof_summary_chain() -> None:
    scenario = SimulationScenario(
        scenario_id="SCN-3",
        run_id="RUN-SIM-003",
        events=[
            {"forecast_id": "f-1", "asset_id": "BTC", "score": 0.8, "confidence": 0.9, "entry_price": 100.0, "exit_price": 110.0},
        ],
        initial_portfolio=_initial_portfolio("RUN-SIM-003"),
        strategy_config={"min_confidence": 0.6, "position_risk_fraction": 0.1, "max_notional": 1000.0},
    )
    result = run_simulation(scenario)
    report = validate_simulation_result(result)
    validator = validation_artifact(result, report)
    proof = proof_summary_artifact(result, report)

    assert validator["status"] in {"VALID", "PARTIAL", "BROKEN", "NOT_COMPUTABLE", "ORPHANED", "INCONSISTENT"}
    assert validator["correlation"]["ledgerIds"]
    assert proof["closureStatus"] == validator["status"]
