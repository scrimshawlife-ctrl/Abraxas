from __future__ import annotations

from abraxas.registry.invariance_harness import run_invariance_harness


def test_invariance_harness_runs() -> None:
    result = run_invariance_harness(runs=3)
    assert result["schema_version"] == "InvarianceHarnessRun.v1"
    assert "registry_invariant" in result
    assert "validator_invariant" in result
    assert "bundle_invariant" in result


def test_invariance_harness_stable() -> None:
    result = run_invariance_harness(runs=3)
    assert result["registry_invariant"] is True
    assert result["validator_invariant"] is True
    assert result["bundle_invariant"] is True
