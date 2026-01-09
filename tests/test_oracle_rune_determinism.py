"""Determinism tests for oracle rune capability invocations."""
from __future__ import annotations

from abx.oracle.drift import drift_check
from abx.oracle.rune_gate import compute_gate, schedule_insight_window
from abraxas.runes.ctx import RuneInvocationContext


def _rune_ctx() -> RuneInvocationContext:
    return RuneInvocationContext(
        run_id="test-run",
        subsystem_id="tests.oracle",
        git_hash="deadbeef",
    )


def test_sds_gate_is_deterministic() -> None:
    state_vector = {
        "arousal": 0.2,
        "coherence": 0.8,
        "openness": 0.9,
        "receptivity": 0.9,
        "stability": 0.8,
    }
    context = {"intent": "determinism"}
    ctx = _rune_ctx()

    first = compute_gate(
        state_vector=state_vector,
        context=context,
        interaction_kind="oracle",
        ctx=ctx,
        strict_execution=True,
    )
    second = compute_gate(
        state_vector=state_vector,
        context=context,
        interaction_kind="oracle",
        ctx=ctx,
        strict_execution=True,
    )

    assert first == second


def test_ipl_schedule_is_deterministic() -> None:
    ctx = _rune_ctx()
    gate_bundle = {
        "gate_state": "OPEN",
        "susceptibility_score": 0.8,
        "state_classification": {},
        "reception_status": "ok",
    }
    phase_series = [(0.0, 0.1), (1.0, 0.6), (2.0, 0.4), (10.0, 0.7)]

    first = schedule_insight_window(
        phase_series=phase_series,
        gate_bundle=gate_bundle,
        window_s=2.0,
        lock_threshold=0.35,
        refractory_s=8.0,
        ctx=ctx,
        strict_execution=True,
    )
    second = schedule_insight_window(
        phase_series=phase_series,
        gate_bundle=gate_bundle,
        window_s=2.0,
        lock_threshold=0.35,
        refractory_s=8.0,
        ctx=ctx,
        strict_execution=True,
    )

    assert first == second


def test_add_drift_is_deterministic() -> None:
    ctx = _rune_ctx()
    anchor = "oracle stability"
    history = [
        "oracle stability output 1",
        "oracle stability output 2",
        "oracle stability output 3",
    ]

    first = drift_check(
        anchor=anchor,
        outputs_history=history,
        window=20,
        ctx=ctx,
        strict_execution=True,
    )
    second = drift_check(
        anchor=anchor,
        outputs_history=history,
        window=20,
        ctx=ctx,
        strict_execution=True,
    )

    assert first == second
