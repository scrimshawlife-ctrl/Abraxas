"""Strict execution propagation tests for oracle rune calls."""
from __future__ import annotations

from typing import Any

from abx.oracle import drift as drift_module
from abx.oracle import rune_gate
from abraxas.runes.ctx import RuneInvocationContext


def _rune_ctx() -> RuneInvocationContext:
    return RuneInvocationContext(
        run_id="test-run",
        subsystem_id="tests.oracle",
        git_hash="deadbeef",
    )


def test_compute_gate_forwards_strict_execution(monkeypatch) -> None:
    seen: dict[str, Any] = {}

    def _fake_invoke(capability: str, inputs: dict[str, Any], *, ctx, strict_execution: bool, ledger=None):
        seen["capability"] = capability
        seen["strict_execution"] = strict_execution
        return {
            "susceptibility_score": 0.1,
            "gate_state": "CLOSED",
            "state_classification": {},
            "reception_status": "stub",
        }

    monkeypatch.setattr(rune_gate, "invoke_capability", _fake_invoke)

    rune_gate.compute_gate(
        state_vector={"openness": 0.1},
        context={},
        interaction_kind="oracle",
        ctx=_rune_ctx(),
        strict_execution=False,
    )

    assert seen == {"capability": "rune:sds", "strict_execution": False}


def test_schedule_insight_window_forwards_strict_execution(monkeypatch) -> None:
    seen: dict[str, Any] = {}

    def _fake_invoke(capability: str, inputs: dict[str, Any], *, ctx, strict_execution: bool, ledger=None):
        seen["capability"] = capability
        seen["strict_execution"] = strict_execution
        return {
            "events": [],
            "total_windows": 0,
            "refractory_enforced": True,
            "lock_status": "inactive",
        }

    monkeypatch.setattr(rune_gate, "invoke_capability", _fake_invoke)

    rune_gate.schedule_insight_window(
        phase_series=[(0.0, 0.5)],
        gate_bundle={"gate_state": "OPEN"},
        ctx=_rune_ctx(),
        strict_execution=True,
    )

    assert seen == {"capability": "rune:ipl", "strict_execution": True}


def test_drift_check_forwards_strict_execution(monkeypatch) -> None:
    seen: dict[str, Any] = {}

    def _fake_invoke(capability: str, inputs: dict[str, Any], *, ctx, strict_execution: bool, ledger=None):
        seen["capability"] = capability
        seen["strict_execution"] = strict_execution
        return {
            "drift_magnitude": 0.0,
            "integrity_score": 1.0,
            "auto_recenter": False,
        }

    monkeypatch.setattr(drift_module, "invoke_capability", _fake_invoke)

    drift_module.drift_check(
        anchor="oracle stability",
        outputs_history=[],
        ctx=_rune_ctx(),
        strict_execution=False,
    )

    assert seen == {"capability": "rune:add", "strict_execution": False}
