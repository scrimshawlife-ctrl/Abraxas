"""Tests for oracle.kernel.run capability.

Verifies the ABX-Runes capability contract for kernel oracle execution.
"""

import pytest

from abraxas.runes.capabilities import load_capability_registry
from abraxas.runes.ctx import RuneInvocationContext
from abraxas.core.rune_adapter import run_oracle_kernel_deterministic


def test_capability_registered():
    """Verify oracle.kernel.run capability is in registry."""
    registry = load_capability_registry()
    cap = registry.find_capability("oracle.kernel.run")
    assert cap is not None, "oracle.kernel.run capability should be registered"
    assert cap.operator_path == "abraxas.core.rune_adapter:run_oracle_kernel_deterministic"
    assert cap.deterministic is True
    assert cap.provenance_required is True


def test_capability_function_signature():
    """Verify function accepts expected parameters."""
    # Should not raise on valid inputs (even if oracle fails internally)
    result = run_oracle_kernel_deterministic(
        user={},
        overlays={},
        day="2026-01-01",
        checkin=None,
        seed=42,
        strict_execution=False,  # Don't raise on internal errors
    )

    # Should return expected structure
    assert "readout" in result
    assert "oracle_provenance" in result
    assert "provenance" in result
    assert "not_computable" in result


def test_capability_determinism():
    """Verify same inputs produce consistent output structure."""
    inputs = {
        "user": {"tier": "free"},
        "overlays": {"enabled": {}},
        "day": "2026-01-01",
        "checkin": None,
        "seed": 42,
        "strict_execution": False,
    }

    result1 = run_oracle_kernel_deterministic(**inputs)
    result2 = run_oracle_kernel_deterministic(**inputs)

    # Structure should be consistent
    assert set(result1.keys()) == set(result2.keys())
    # If both computed or both not-computable, behavior is consistent
    assert (result1["not_computable"] is None) == (result2["not_computable"] is None)
