"""
Component Evaluation

Evaluate FDR components against backtest cases using existing trigger logic.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

from abraxas.backtest.evaluator import evaluate_trigger
from abraxas.backtest.schema import BacktestCase, BacktestStatus, TriggerSpec
from abraxas.forecast.decomposition.registry import load_fdr, match_components
from abraxas.forecast.decomposition.types import ComponentClaim
from abraxas.scoreboard.scoring import brier_score


@dataclass(frozen=True)
class ComponentOutcome:
    component_id: str
    case_id: str
    horizon: str
    applicable: bool
    observed: Optional[bool]
    status: str
    scoring_key: str
    score_contrib: Dict[str, Any]
    notes: List[str]
    provenance: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def evaluate_components_for_case(
    case: BacktestCase,
    events: List[Any],
    ledgers: Dict[str, List[Dict[str, Any]]],
    fdr_path: str = "data/forecast/decomposition/fdr_v0_1.yaml",
) -> List[ComponentOutcome]:
    registry = load_fdr(fdr_path)
    topic_key = case.topic_key or _infer_topic_key(case)
    if not topic_key or not case.horizon:
        return []

    matches = match_components(registry, topic_key, case.horizon, case.domain)
    outcomes = []
    for component in matches:
        outcomes.append(
            eval_component_for_case(
                component=component,
                case=case,
                events=events,
                ledgers=ledgers,
            )
        )
    return outcomes


def eval_component_for_case(
    component: ComponentClaim,
    case: BacktestCase,
    events: List[Any],
    ledgers: Dict[str, List[Dict[str, Any]]],
) -> ComponentOutcome:
    notes: List[str] = []
    if not component.trigger_specs:
        return _outcome_unknown(component, case, "No trigger_specs defined")

    if not _guardrails_pass(case, events, ledgers, notes):
        return ComponentOutcome(
            component_id=component.component_id,
            case_id=case.case_id,
            horizon=case.horizon or "",
            applicable=True,
            observed=None,
            status=BacktestStatus.ABSTAIN.value,
            scoring_key=component.scoring_key,
            score_contrib={},
            notes=notes,
            provenance={"guardrails": "failed"},
        )

    trigger_hit = _evaluate_specs(component.trigger_specs, events, ledgers)
    falsifier_hit = _evaluate_specs(component.falsifier_specs, events, ledgers)

    if falsifier_hit:
        observed = False
        status = BacktestStatus.MISS.value
    elif trigger_hit:
        observed = True
        status = BacktestStatus.HIT.value
    else:
        observed = None
        status = BacktestStatus.UNKNOWN.value

    score_contrib = _score_component(component, case, observed, status, notes)

    return ComponentOutcome(
        component_id=component.component_id,
        case_id=case.case_id,
        horizon=case.horizon or "",
        applicable=True,
        observed=observed,
        status=status,
        scoring_key=component.scoring_key,
        score_contrib=score_contrib,
        notes=notes,
        provenance={"trigger_hit": trigger_hit, "falsifier_hit": falsifier_hit},
    )


def _evaluate_specs(
    specs: List[Dict[str, Any]],
    events: List[Any],
    ledgers: Dict[str, List[Dict[str, Any]]],
) -> bool:
    if not specs:
        return False
    for spec in specs:
        trigger = TriggerSpec(**spec)
        result = evaluate_trigger(trigger=trigger, events=events, ledgers=ledgers)
        if result.satisfied:
            return True
    return False


def _score_component(
    component: ComponentClaim,
    case: BacktestCase,
    observed: Optional[bool],
    status: str,
    notes: List[str],
) -> Dict[str, Any]:
    if status != BacktestStatus.HIT.value and status != BacktestStatus.MISS.value:
        return {}

    if component.scoring_key == "brier":
        predicted_p = _get_predicted_p(case, component.component_id)
        if predicted_p is None:
            notes.append("Missing predicted_p for component")
            return {}
        outcome = 1 if observed else 0
        return {"brier": brier_score(predicted_p, outcome)}

    if component.scoring_key == "coverage_rate":
        coverage = _score_coverage_rate(case, notes)
        return {"coverage_rate": coverage} if coverage is not None else {}

    if component.scoring_key == "trend_acc":
        trend_acc = _score_trend_accuracy(case, notes)
        return {"trend_acc": trend_acc} if trend_acc is not None else {}

    notes.append(f"Unknown scoring_key: {component.scoring_key}")
    return {}


def _get_predicted_p(case: BacktestCase, component_id: str) -> Optional[float]:
    summary = case.forecast_delta_summary or {}
    components = summary.get("components", [])
    weight_sum = 0.0
    for component in components:
        if component.get("component_id") == component_id:
            weight_sum += float(component.get("weight", 0.0))

    if weight_sum <= 0:
        return None

    return max(0.05, min(0.95, weight_sum))


def _score_coverage_rate(case: BacktestCase, notes: List[str]) -> Optional[float]:
    regime = case.regime_outcome_ref or {}
    predicted_min = regime.get("predicted_min")
    predicted_max = regime.get("predicted_max")
    observed = regime.get("observed")

    if predicted_min is None or predicted_max is None or observed is None:
        notes.append("Missing regime outcome fields for coverage_rate")
        return None

    return 1.0 if predicted_min <= observed <= predicted_max else 0.0


def _score_trend_accuracy(case: BacktestCase, notes: List[str]) -> Optional[float]:
    regime = case.regime_outcome_ref or {}
    predicted = regime.get("predicted")
    observed = regime.get("observed")

    if predicted is None or observed is None:
        notes.append("Missing regime outcome fields for trend_acc")
        return None

    predicted_sign = 1 if predicted >= 0 else -1
    observed_sign = 1 if observed >= 0 else -1
    return 1.0 if predicted_sign == observed_sign else 0.0


def _guardrails_pass(
    case: BacktestCase,
    events: List[Any],
    ledgers: Dict[str, List[Dict[str, Any]]],
    notes: List[str],
) -> bool:
    if case.guardrails.min_signal_count > len(events):
        notes.append("Guardrail: min_signal_count not met")
        return False

    required_ledgers = set(case.provenance.required_ledgers)
    if required_ledgers and not required_ledgers.issubset(set(ledgers.keys())):
        notes.append("Guardrail: required ledgers missing")
        return False

    return True


def _infer_topic_key(case: BacktestCase) -> Optional[str]:
    if case.topic_keys:
        return case.topic_keys[0]
    return None


def _outcome_unknown(
    component: ComponentClaim,
    case: BacktestCase,
    reason: str
) -> ComponentOutcome:
    return ComponentOutcome(
        component_id=component.component_id,
        case_id=case.case_id,
        horizon=case.horizon or "",
        applicable=True,
        observed=None,
        status=BacktestStatus.UNKNOWN.value,
        scoring_key=component.scoring_key,
        score_contrib={},
        notes=[reason],
        provenance={},
    )
