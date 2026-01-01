"""
Tests for Backtest System

Basic validation of backtest evaluation functionality.
"""

import pytest
from datetime import datetime, timezone
from pathlib import Path

from abraxas.backtest.schema import (
    BacktestCase,
    BacktestStatus,
    TriggerSpec,
    TriggerKind,
    ForecastRef,
    EvaluationWindow,
    Triggers,
    Guardrails,
    Scoring,
)
from abraxas.backtest.evaluator import evaluate_trigger, _evaluate_term_seen
from abraxas.backtest.event_query import SignalEvent
from abraxas.backtest.ledger import BacktestLedger


def test_trigger_spec_creation():
    """Test creating trigger specifications."""
    trigger = TriggerSpec(
        kind=TriggerKind.TERM_SEEN,
        params={"term": "test term", "min_count": 2},
    )

    assert trigger.kind == TriggerKind.TERM_SEEN
    assert trigger.params["term"] == "test term"
    assert trigger.params["min_count"] == 2


def test_term_seen_trigger_satisfied():
    """Test term_seen trigger when term appears enough times."""
    trigger = TriggerSpec(
        kind=TriggerKind.TERM_SEEN,
        params={"term": "digital", "min_count": 2},
    )

    events = [
        SignalEvent(
            event_id="e1",
            timestamp=datetime.now(timezone.utc),
            text="This is about digital transformation",
            source="OSH",
        ),
        SignalEvent(
            event_id="e2",
            timestamp=datetime.now(timezone.utc),
            text="Digital economy is growing",
            source="OSH",
        ),
    ]

    result = _evaluate_term_seen(trigger, events)

    assert result.satisfied is True
    assert result.match_count == 2


def test_term_seen_trigger_not_satisfied():
    """Test term_seen trigger when term doesn't appear enough."""
    trigger = TriggerSpec(
        kind=TriggerKind.TERM_SEEN,
        params={"term": "quantum", "min_count": 3},
    )

    events = [
        SignalEvent(
            event_id="e1",
            timestamp=datetime.now(timezone.utc),
            text="Quantum computing is advancing",
            source="OSH",
        ),
    ]

    result = _evaluate_term_seen(trigger, events)

    assert result.satisfied is False
    assert result.match_count == 1


def test_backtest_ledger_append(tmp_path):
    """Test appending results to backtest ledger."""
    ledger_path = tmp_path / "backtest_test.jsonl"
    ledger = BacktestLedger(ledger_path=ledger_path)

    from abraxas.backtest.schema import BacktestResult, Confidence

    result = BacktestResult(
        case_id="test_case_001",
        status=BacktestStatus.HIT,
        score=1.0,
        confidence=Confidence.HIGH,
        notes=["Test successful"],
    )

    step_hash = ledger.append_result("test_run_001", result)

    assert step_hash is not None
    assert len(step_hash) == 64  # SHA256 hex digest

    # Verify ledger file created
    assert ledger_path.exists()

    # Read back
    entries = ledger.read_all()
    assert len(entries) == 1
    assert entries[0]["case_id"] == "test_case_001"
    assert entries[0]["status"] == "HIT"


def test_backtest_ledger_chain_integrity(tmp_path):
    """Test hash chain integrity verification."""
    ledger_path = tmp_path / "backtest_chain.jsonl"
    ledger = BacktestLedger(ledger_path=ledger_path)

    from abraxas.backtest.schema import BacktestResult, Confidence

    # Add multiple results
    for i in range(3):
        result = BacktestResult(
            case_id=f"case_{i}",
            status=BacktestStatus.HIT,
            score=1.0,
            confidence=Confidence.HIGH,
        )
        ledger.append_result(f"run_{i}", result)

    # Verify chain
    assert ledger.verify_chain_integrity() is True


def test_backtest_case_validation():
    """Test creating a valid backtest case."""
    case = BacktestCase(
        case_id="test_case",
        created_at=datetime.now(timezone.utc),
        description="Test case",
        forecast_ref=ForecastRef(
            run_id="run_001",
            artifact_path="out/runs/run_001/reports/enterprise.json",
            tier="enterprise",
        ),
        evaluation_window=EvaluationWindow(
            start_ts=datetime(2025, 12, 20, 12, 0, 0, tzinfo=timezone.utc),
            end_ts=datetime(2025, 12, 23, 12, 0, 0, tzinfo=timezone.utc),
        ),
        triggers=Triggers(
            any_of=[
                TriggerSpec(
                    kind=TriggerKind.TERM_SEEN,
                    params={"term": "test", "min_count": 1},
                )
            ]
        ),
        guardrails=Guardrails(min_signal_count=5),
        scoring=Scoring(type="binary", weights={"trigger": 1.0}),
    )

    assert case.case_id == "test_case"
    assert len(case.triggers.any_of) == 1
    assert case.guardrails.min_signal_count == 5
