"""
Abraxas Backtest Module

Deterministic offline evaluation of forecasts against historical signal events and ledgers.

Components:
- event_query: Load signal events and ledgers by time range
- evaluator: Evaluate triggers and score backtest cases
- schema: Pydantic models for backtest cases and results
"""

from .event_query import load_signal_events, load_domain_ledgers
from .evaluator import evaluate_trigger, evaluate_case, BacktestResult
from .schema import BacktestCase, TriggerSpec, BacktestStatus
from .portfolio import load_portfolios, select_cases_for_portfolio

__all__ = [
    "load_signal_events",
    "load_domain_ledgers",
    "evaluate_trigger",
    "evaluate_case",
    "BacktestResult",
    "BacktestCase",
    "TriggerSpec",
    "BacktestStatus",
    "load_portfolios",
    "select_cases_for_portfolio",
]
