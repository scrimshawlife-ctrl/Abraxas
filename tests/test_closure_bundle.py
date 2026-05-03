from __future__ import annotations

from abraxas.registry.closure_bundle import run_closure_bundle


def test_closure_bundle_runs() -> None:
    result = run_closure_bundle()
    assert result["schema_version"] == "ClosureBundle.v1"
    assert "registry" in result
    assert "binding_validator" in result
    assert "artifacts" in result


def test_closure_bundle_deterministic() -> None:
    first = run_closure_bundle()
    second = run_closure_bundle()
    assert first["bundle_hash"] == second["bundle_hash"]
