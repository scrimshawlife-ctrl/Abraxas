"""
Portfolio Selection

Deterministic selection of backtest cases based on portfolio specs.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import yaml

from abraxas.backtest.schema import BacktestCase, TriggerSpec


def load_portfolios(path: str | Path) -> Dict[str, Dict[str, Any]]:
    """
    Load portfolios from YAML file.

    Args:
        path: Path to portfolios YAML

    Returns:
        Dict of portfolio_id -> portfolio_spec
    """
    path = Path(path)
    with open(path, "r") as f:
        data = yaml.safe_load(f) or {}

    portfolios = data.get("portfolios", [])
    portfolio_map = {}
    for portfolio in portfolios:
        portfolio_id = portfolio.get("portfolio_id")
        if not portfolio_id:
            raise ValueError("Portfolio missing portfolio_id")
        portfolio_map[portfolio_id] = portfolio

    return portfolio_map


def select_cases_for_portfolio(
    cases: List[BacktestCase],
    portfolio_spec: Dict[str, Any]
) -> List[BacktestCase]:
    """
    Select cases for a portfolio specification.

    Args:
        cases: List of backtest cases
        portfolio_spec: Portfolio specification dict

    Returns:
        List of selected BacktestCase objects (deterministic order)
    """
    horizons = set(portfolio_spec.get("horizons", []) or [])
    segments = set(portfolio_spec.get("segments", []) or [])
    narratives = set(portfolio_spec.get("narratives", []) or [])
    selectors = portfolio_spec.get("case_selectors", []) or []

    selected: List[BacktestCase] = []

    for case in cases:
        if horizons and case.horizon not in horizons:
            continue
        if segments and case.segment not in segments:
            continue
        if narratives and case.narrative not in narratives:
            continue

        if not _case_matches_selectors(case, selectors):
            continue

        selected.append(case)

    return sorted(selected, key=lambda c: c.case_id)


def _case_matches_selectors(
    case: BacktestCase,
    selectors: List[Dict[str, Any]]
) -> bool:
    if not selectors:
        return True

    for selector in selectors:
        kind = selector.get("kind")
        params = selector.get("params", {}) or {}

        if kind == "has_forecast_branch_ref":
            if case.forecast_branch_ref is None:
                return False
        elif kind == "has_regime_outcome_ref":
            if case.regime_outcome_ref is None:
                return False
        elif kind == "topic_key_in":
            topic_keys = set(params.get("topic_keys", []) or [])
            if not topic_keys:
                return False
            if not topic_keys.intersection(set(case.topic_keys)):
                return False
        elif kind == "trigger_kind_in":
            kinds = set(params.get("kinds", []) or [])
            if not kinds:
                return False
            trigger_kinds = _collect_trigger_kinds(case)
            if not kinds.intersection(trigger_kinds):
                return False
        else:
            return False

    return True


def _collect_trigger_kinds(case: BacktestCase) -> set[str]:
    kinds: set[str] = set()
    for trigger in list(case.triggers.any_of) + list(case.triggers.all_of):
        if isinstance(trigger, TriggerSpec):
            kinds.add(trigger.kind.value)
        else:
            kind_value = getattr(trigger, "kind", None)
            if kind_value:
                kinds.add(getattr(kind_value, "value", str(kind_value)))
    return kinds
