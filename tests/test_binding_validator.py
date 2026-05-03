from __future__ import annotations

from abraxas.registry.binding_validator import run_binding_validator


def test_binding_validator_runs() -> None:
    result = run_binding_validator()
    assert result["schema_version"] == "BindingValidatorRun.v1"
    assert "results" in result
    assert "counts" in result
    assert result["counts"]["total"] >= 1


def test_binding_validator_deterministic() -> None:
    first = run_binding_validator()
    second = run_binding_validator()
    assert first["canonical_hash"] == second["canonical_hash"]
