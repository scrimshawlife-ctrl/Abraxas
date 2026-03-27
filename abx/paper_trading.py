from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from abx.core.formulas import stable_sort_score_desc_id_asc

Side = Literal["BUY", "SELL"]
DecisionStatus = Literal["ACCEPT", "REJECT", "DEFER"]


@dataclass(frozen=True)
class ForecastSignal:
    run_id: str
    forecast_id: str
    asset_id: str
    score: float
    confidence: float
    direction: Side
    rationale_ref: str


@dataclass(frozen=True)
class StrategyDecision:
    decision_id: str
    run_id: str
    forecast_id: str
    asset_id: str
    status: DecisionStatus
    score: float
    confidence: float
    reason: str
    lineage: dict[str, Any]


@dataclass(frozen=True)
class TradeIntent:
    intent_id: str
    run_id: str
    asset_id: str
    side: Side
    units: float
    limit_price: float
    simulated_only: bool
    forecast_id: str
    decision_id: str
    rationale_ref: str


@dataclass(frozen=True)
class SimulatedFill:
    fill_id: str
    run_id: str
    intent_id: str
    asset_id: str
    side: Side
    units: float
    fill_price: float
    notional: float
    fill_rule: str
    simulated_only: bool


@dataclass(frozen=True)
class PositionState:
    asset_id: str
    units: float
    avg_entry_price: float
    market_price: float
    unrealized_pnl: float
    cost_basis_open: float


@dataclass(frozen=True)
class PortfolioState:
    run_id: str
    cash: float
    equity: float
    realized_pnl: float
    exposure: float
    max_exposure: float
    max_positions: int
    allow_margin: bool = False
    positions: dict[str, PositionState] = field(default_factory=dict)
    transition_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class RejectionArtifact:
    rejection_id: str
    run_id: str
    forecast_id: str
    asset_id: str
    reason: str
    simulated_only: bool


@dataclass(frozen=True)
class PortfolioTransition:
    transition_id: str
    run_id: str
    prior_equity: float
    next_equity: float
    prior_cash: float
    next_cash: float
    fill_id: str
    simulated_only: bool


@dataclass(frozen=True)
class PortfolioSnapshotArtifact:
    artifact_id: str
    run_id: str
    cash: float
    marked_value: float
    equity: float
    exposure: float
    realized_pnl: float


def rank_strategy_decisions(decisions: list[StrategyDecision]) -> list[StrategyDecision]:
    ranked_rows = stable_sort_score_desc_id_asc(
        [{"id": d.decision_id, "score": d.score, "decision": d} for d in decisions]
    )
    return [row["decision"] for row in ranked_rows if isinstance(row.get("decision"), StrategyDecision)]


def build_decision(signal: ForecastSignal, *, min_confidence: float) -> StrategyDecision:
    status: DecisionStatus = "ACCEPT"
    reason = "accepted"
    if signal.confidence < min_confidence:
        status = "REJECT"
        reason = "confidence_too_low"

    decision_id = f"decision-{signal.run_id}-{signal.forecast_id}"
    return StrategyDecision(
        decision_id=decision_id,
        run_id=signal.run_id,
        forecast_id=signal.forecast_id,
        asset_id=signal.asset_id,
        status=status,
        score=float(signal.score),
        confidence=float(signal.confidence),
        reason=reason,
        lineage={"forecast_id": signal.forecast_id, "run_id": signal.run_id},
    )


def build_trade_intent(
    decision: StrategyDecision,
    *,
    position_risk_fraction: float,
    max_notional: float,
    reference_price: float,
) -> TradeIntent | RejectionArtifact:
    if decision.status != "ACCEPT":
        return RejectionArtifact(
            rejection_id=f"rejection-{decision.decision_id}",
            run_id=decision.run_id,
            forecast_id=decision.forecast_id,
            asset_id=decision.asset_id,
            reason=decision.reason,
            simulated_only=True,
        )

    bounded_risk = max(0.0, min(float(position_risk_fraction), 1.0))
    size_notional = max_notional * bounded_risk
    if size_notional <= 0.0 or reference_price <= 0.0:
        return RejectionArtifact(
            rejection_id=f"rejection-{decision.decision_id}",
            run_id=decision.run_id,
            forecast_id=decision.forecast_id,
            asset_id=decision.asset_id,
            reason="invalid_sizing_inputs",
            simulated_only=True,
        )

    units = size_notional / reference_price
    return TradeIntent(
        intent_id=f"intent-{decision.decision_id}",
        run_id=decision.run_id,
        asset_id=decision.asset_id,
        side="BUY",
        units=units,
        limit_price=reference_price,
        simulated_only=True,
        forecast_id=decision.forecast_id,
        decision_id=decision.decision_id,
        rationale_ref=decision.reason,
    )


def simulate_fill(intent: TradeIntent, *, market_price: float, fill_rule: str = "close_price") -> SimulatedFill:
    fill_price = float(market_price)
    notional = float(intent.units) * fill_price
    return SimulatedFill(
        fill_id=f"fill-{intent.intent_id}",
        run_id=intent.run_id,
        intent_id=intent.intent_id,
        asset_id=intent.asset_id,
        side=intent.side,
        units=float(intent.units),
        fill_price=fill_price,
        notional=notional,
        fill_rule=fill_rule,
        simulated_only=True,
    )


def _mark_to_market(cash: float, positions: dict[str, PositionState]) -> tuple[float, float, float]:
    marked = sum(pos.units * pos.market_price for pos in positions.values())
    exposure = sum(abs(pos.units * pos.market_price) for pos in positions.values())
    equity = cash + marked
    return equity, exposure, marked


def snapshot_artifact(portfolio: PortfolioState, *, artifact_id: str) -> PortfolioSnapshotArtifact:
    equity, exposure, marked = _mark_to_market(portfolio.cash, portfolio.positions)
    return PortfolioSnapshotArtifact(
        artifact_id=artifact_id,
        run_id=portfolio.run_id,
        cash=portfolio.cash,
        marked_value=marked,
        equity=equity,
        exposure=exposure,
        realized_pnl=portfolio.realized_pnl,
    )


def validate_portfolio_invariants(portfolio: PortfolioState) -> list[str]:
    errors: list[str] = []
    if portfolio.cash < 0 and not portfolio.allow_margin:
        errors.append("negative-cash-without-margin")
    if portfolio.exposure > portfolio.max_exposure:
        errors.append("exposure-cap-violated")
    if len(portfolio.positions) > portfolio.max_positions:
        errors.append("max-position-count-violated")

    equity, exposure, _marked = _mark_to_market(portfolio.cash, portfolio.positions)
    if abs(equity - portfolio.equity) > 1e-6:
        errors.append("equity-reconciliation-failed")
    if abs(exposure - portfolio.exposure) > 1e-6:
        errors.append("exposure-reconciliation-failed")

    for pos in portfolio.positions.values():
        expected_unrealized = (pos.market_price - pos.avg_entry_price) * pos.units
        if abs(expected_unrealized - pos.unrealized_pnl) > 1e-6:
            errors.append(f"unrealized-pnl-mismatch:{pos.asset_id}")
        if abs((pos.avg_entry_price * pos.units) - pos.cost_basis_open) > 1e-6:
            errors.append(f"cost-basis-mismatch:{pos.asset_id}")
    return sorted(set(errors))


def apply_fill(portfolio: PortfolioState, fill: SimulatedFill) -> tuple[PortfolioState, PortfolioTransition]:
    transition_id = f"transition-{fill.fill_id}"
    if transition_id in set(portfolio.transition_ids):
        raise ValueError("duplicate_transition_id")

    positions = dict(portfolio.positions)
    prior_cash = portfolio.cash
    prior_equity = portfolio.equity

    if fill.side == "BUY":
        if fill.notional > portfolio.cash and not portfolio.allow_margin:
            raise ValueError("insufficient_capital")

        old = positions.get(fill.asset_id)
        if old is None:
            positions[fill.asset_id] = PositionState(
                asset_id=fill.asset_id,
                units=fill.units,
                avg_entry_price=fill.fill_price,
                market_price=fill.fill_price,
                unrealized_pnl=0.0,
                cost_basis_open=fill.units * fill.fill_price,
            )
        else:
            total_units = old.units + fill.units
            avg = ((old.units * old.avg_entry_price) + (fill.units * fill.fill_price)) / total_units
            positions[fill.asset_id] = PositionState(
                asset_id=fill.asset_id,
                units=total_units,
                avg_entry_price=avg,
                market_price=fill.fill_price,
                unrealized_pnl=(fill.fill_price - avg) * total_units,
                cost_basis_open=avg * total_units,
            )

        next_cash = portfolio.cash - fill.notional
        realized = portfolio.realized_pnl
    else:
        old = positions.get(fill.asset_id)
        if old is None or fill.units <= 0 or old.units < fill.units:
            raise ValueError("insufficient_position")
        realized_delta = (fill.fill_price - old.avg_entry_price) * fill.units
        remaining = old.units - fill.units
        if remaining == 0:
            positions.pop(fill.asset_id, None)
        else:
            positions[fill.asset_id] = PositionState(
                asset_id=fill.asset_id,
                units=remaining,
                avg_entry_price=old.avg_entry_price,
                market_price=fill.fill_price,
                unrealized_pnl=(fill.fill_price - old.avg_entry_price) * remaining,
                cost_basis_open=old.avg_entry_price * remaining,
            )
        next_cash = portfolio.cash + fill.notional
        realized = portfolio.realized_pnl + realized_delta

    next_equity, exposure, _marked = _mark_to_market(next_cash, positions)
    next_portfolio = PortfolioState(
        run_id=portfolio.run_id,
        cash=next_cash,
        equity=next_equity,
        realized_pnl=realized,
        exposure=exposure,
        max_exposure=portfolio.max_exposure,
        max_positions=portfolio.max_positions,
        allow_margin=portfolio.allow_margin,
        positions=positions,
        transition_ids=tuple(list(portfolio.transition_ids) + [transition_id]),
    )

    errors = validate_portfolio_invariants(next_portfolio)
    if errors:
        raise ValueError(f"portfolio_invariant_failed:{','.join(errors)}")

    transition = PortfolioTransition(
        transition_id=transition_id,
        run_id=portfolio.run_id,
        prior_equity=prior_equity,
        next_equity=next_portfolio.equity,
        prior_cash=prior_cash,
        next_cash=next_cash,
        fill_id=fill.fill_id,
        simulated_only=True,
    )
    return next_portfolio, transition
