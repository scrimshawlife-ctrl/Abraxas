"""
Backtest Evaluator

Evaluates triggers against events and ledgers, produces backtest results.
Deterministic, no ML or fuzzy matching.
"""

from __future__ import annotations

import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from abraxas.backtest.event_query import (
    SignalEvent,
    load_signal_events,
    load_domain_ledgers,
    check_ledger_completeness,
)
from abraxas.backtest.schema import (
    BacktestCase,
    BacktestResult,
    BacktestStatus,
    Confidence,
    TriggerKind,
    TriggerResult,
    TriggerSpec,
)


def evaluate_trigger(
    trigger: TriggerSpec,
    events: List[SignalEvent],
    ledgers: Dict[str, List[Dict[str, Any]]],
) -> TriggerResult:
    """
    Evaluate a single trigger against events and ledgers.

    Args:
        trigger: Trigger specification
        events: List of signal events
        ledgers: Dict of ledger entries by name

    Returns:
        TriggerResult with satisfaction status
    """
    kind = trigger.kind
    params = trigger.params

    if kind == TriggerKind.TERM_SEEN:
        return _evaluate_term_seen(trigger, events)
    elif kind == TriggerKind.MW_SHIFT:
        return _evaluate_mw_shift(trigger, ledgers)
    elif kind == TriggerKind.TAU_SHIFT:
        return _evaluate_tau_shift(trigger, ledgers)
    elif kind == TriggerKind.INTEGRITY_VECTOR:
        return _evaluate_integrity_vector(trigger, ledgers)
    elif kind == TriggerKind.INDEX_THRESHOLD:
        return _evaluate_index_threshold(trigger, ledgers)
    else:
        return TriggerResult(
            trigger_kind=kind,
            satisfied=False,
            notes=[f"Unknown trigger kind: {kind}"],
        )


def _evaluate_term_seen(
    trigger: TriggerSpec, events: List[SignalEvent]
) -> TriggerResult:
    """Evaluate term_seen trigger."""
    params = trigger.params
    term = params.get("term", "").lower()
    min_count = params.get("min_count", 1)
    source_filter = params.get("source_filter", [])

    count = 0
    for event in events:
        # Source filter
        if source_filter and event.source not in source_filter:
            continue

        # Exact substring match (case-insensitive)
        if term in event.text.lower():
            count += 1

    satisfied = count >= min_count

    return TriggerResult(
        trigger_kind=TriggerKind.TERM_SEEN,
        satisfied=satisfied,
        match_count=count,
        notes=[f"Found '{term}' {count} times (required: {min_count})"],
    )


def _evaluate_mw_shift(
    trigger: TriggerSpec, ledgers: Dict[str, List[Dict[str, Any]]]
) -> TriggerResult:
    """Evaluate mw_shift trigger."""
    params = trigger.params
    min_shifts = params.get("min_shifts", 1)
    threshold = params.get("threshold", 0.0)

    oracle_ledger = ledgers.get("oracle_delta", [])

    shifts = []
    for entry in oracle_ledger:
        mw_shifts = entry.get("mw_shifts", 0)
        if mw_shifts >= threshold:
            shifts.append(entry)

    satisfied = len(shifts) >= min_shifts

    return TriggerResult(
        trigger_kind=TriggerKind.MW_SHIFT,
        satisfied=satisfied,
        match_count=len(shifts),
        notes=[f"Found {len(shifts)} MW shifts (required: {min_shifts})"],
    )


def _evaluate_tau_shift(
    trigger: TriggerSpec, ledgers: Dict[str, List[Dict[str, Any]]]
) -> TriggerResult:
    """Evaluate tau_shift trigger."""
    params = trigger.params
    min_velocity_delta = params.get("min_velocity_delta", 0.1)

    tau_ledger = ledgers.get("tau", [])

    tau_updates = []
    for entry in tau_ledger:
        velocity_delta = abs(entry.get("velocity_delta", 0))
        if velocity_delta >= min_velocity_delta:
            tau_updates.append(entry)

    satisfied = len(tau_updates) > 0

    return TriggerResult(
        trigger_kind=TriggerKind.TAU_SHIFT,
        satisfied=satisfied,
        match_count=len(tau_updates),
        notes=[f"Found {len(tau_updates)} TAU velocity shifts >= {min_velocity_delta}"],
    )


def _evaluate_integrity_vector(
    trigger: TriggerSpec, ledgers: Dict[str, List[Dict[str, Any]]]
) -> TriggerResult:
    """Evaluate integrity_vector trigger."""
    params = trigger.params
    vector = params.get("vector", "")
    min_score = params.get("min_score", 0.5)

    integrity_ledger = ledgers.get("integrity", [])

    matching_scores = []
    for entry in integrity_ledger:
        entry_vector = entry.get("vector", "")
        score = entry.get("score", 0.0)

        if entry_vector == vector and score >= min_score:
            matching_scores.append(score)

    satisfied = len(matching_scores) > 0

    return TriggerResult(
        trigger_kind=TriggerKind.INTEGRITY_VECTOR,
        satisfied=satisfied,
        match_count=len(matching_scores),
        notes=[
            f"Found {len(matching_scores)} instances of '{vector}' with score >= {min_score}"
        ],
    )


def _evaluate_index_threshold(
    trigger: TriggerSpec, ledgers: Dict[str, List[Dict[str, Any]]]
) -> TriggerResult:
    """Evaluate index_threshold trigger."""
    params = trigger.params
    index = params.get("index", "")
    gte = params.get("gte")
    lte = params.get("lte")

    integrity_ledger = ledgers.get("integrity", [])

    matching_values = []
    for entry in integrity_ledger:
        if index not in entry:
            continue

        value = entry[index]

        if gte is not None and value >= gte:
            matching_values.append(value)
        elif lte is not None and value <= lte:
            matching_values.append(value)

    satisfied = len(matching_values) > 0

    notes = []
    if gte is not None:
        notes.append(f"Found {len(matching_values)} instances of {index} >= {gte}")
    if lte is not None:
        notes.append(f"Found {len(matching_values)} instances of {index} <= {lte}")

    return TriggerResult(
        trigger_kind=TriggerKind.INDEX_THRESHOLD,
        satisfied=satisfied,
        match_count=len(matching_values),
        notes=notes,
    )


def evaluate_case(case: BacktestCase) -> BacktestResult:
    """
    Evaluate a complete backtest case.

    Args:
        case: BacktestCase specification

    Returns:
        BacktestResult with status and score
    """
    # Load events
    events = load_signal_events(
        time_min=case.evaluation_window.start_ts,
        time_max=case.evaluation_window.end_ts,
    )

    # Load ledgers
    ledgers = load_domain_ledgers(
        time_min=case.evaluation_window.start_ts,
        time_max=case.evaluation_window.end_ts,
    )

    # Check guardrails
    notes = []

    # Guardrail: min_signal_count
    if len(events) < case.guardrails.min_signal_count:
        return BacktestResult(
            case_id=case.case_id,
            status=BacktestStatus.ABSTAIN,
            score=case.scoring.weights.get("abstain", 0.2),
            confidence=Confidence.LOW,
            notes=[
                f"Insufficient signal count: {len(events)} < {case.guardrails.min_signal_count}"
            ],
            provenance={"events_examined": len(events)},
        )

    # Guardrail: min_evidence_completeness
    completeness = check_ledger_completeness(case.provenance.required_ledgers, ledgers)
    if completeness < case.guardrails.min_evidence_completeness:
        return BacktestResult(
            case_id=case.case_id,
            status=BacktestStatus.UNKNOWN,
            score=0.0,
            confidence=Confidence.LOW,
            notes=[
                f"Insufficient ledger completeness: {completeness:.2%} < {case.guardrails.min_evidence_completeness:.2%}"
            ],
            provenance={
                "events_examined": len(events),
                "ledger_completeness": completeness,
            },
        )

    # Guardrail: max_integrity_risk
    integrity_ledger = ledgers.get("integrity", [])
    max_ssi = 0.0
    for entry in integrity_ledger:
        ssi = entry.get("SSI", 0.0)
        max_ssi = max(max_ssi, ssi)

    if max_ssi > case.guardrails.max_integrity_risk:
        return BacktestResult(
            case_id=case.case_id,
            status=BacktestStatus.ABSTAIN,
            score=case.scoring.weights.get("abstain", 0.2),
            confidence=Confidence.LOW,
            notes=[
                f"Integrity risk too high: SSI {max_ssi:.2f} > {case.guardrails.max_integrity_risk:.2f}"
            ],
            provenance={"events_examined": len(events), "max_ssi": max_ssi},
        )

    # Evaluate triggers
    trigger_results = []
    satisfied_triggers = []

    # Evaluate any_of triggers
    for trigger in case.triggers.any_of:
        result = evaluate_trigger(trigger, events, ledgers)
        trigger_results.append(result)
        if result.satisfied:
            satisfied_triggers.append(f"{result.trigger_kind.value}_{result.match_count}")
        notes.extend(result.notes)

    # Evaluate all_of triggers
    all_of_satisfied = True
    for trigger in case.triggers.all_of:
        result = evaluate_trigger(trigger, events, ledgers)
        trigger_results.append(result)
        if result.satisfied:
            satisfied_triggers.append(f"{result.trigger_kind.value}_{result.match_count}")
        else:
            all_of_satisfied = False
        notes.extend(result.notes)

    # Evaluate falsifiers
    falsifier_results = []
    satisfied_falsifiers = []

    for falsifier in case.falsifiers.any_of:
        result = evaluate_trigger(falsifier, events, ledgers)
        falsifier_results.append(result)
        if result.satisfied:
            satisfied_falsifiers.append(
                f"{result.trigger_kind.value}_{result.match_count}"
            )
        notes.extend([f"Falsifier: {note}" for note in result.notes])

    # Determine status
    any_trigger_satisfied = any(r.satisfied for r in trigger_results if r in trigger_results[:len(case.triggers.any_of)])
    all_trigger_satisfied = all_of_satisfied if case.triggers.all_of else True
    any_falsifier_satisfied = any(r.satisfied for r in falsifier_results)

    if any_falsifier_satisfied:
        status = BacktestStatus.MISS
        score = 0.0
        confidence = Confidence.HIGH
    elif any_trigger_satisfied and all_trigger_satisfied:
        status = BacktestStatus.HIT
        score = case.scoring.weights.get("trigger", 1.0)
        confidence = Confidence.HIGH
    else:
        status = BacktestStatus.MISS
        score = 0.0
        confidence = Confidence.MED

    return BacktestResult(
        case_id=case.case_id,
        status=status,
        score=score,
        confidence=confidence,
        satisfied_triggers=satisfied_triggers,
        satisfied_falsifiers=satisfied_falsifiers,
        notes=notes,
        provenance={
            "events_examined": len(events),
            "ledgers_loaded": list(ledgers.keys()),
            "ledger_completeness": completeness,
            "max_ssi": max_ssi,
        },
    )


def load_backtest_case(case_path: str | Path) -> BacktestCase:
    """
    Load backtest case from YAML file.

    Args:
        case_path: Path to YAML case file

    Returns:
        BacktestCase instance
    """
    case_path = Path(case_path)

    with open(case_path, "r") as f:
        data = yaml.safe_load(f)

    return BacktestCase(**data)
