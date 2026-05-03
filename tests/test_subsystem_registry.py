from __future__ import annotations

from abraxas.registry import load_subsystem_registry


def test_subsystem_registry_loads() -> None:
    result = load_subsystem_registry()
    assert result.schema_version == "SubsystemRegistry.v1"
    assert result.registry_id == "abx-subsystem-registry-main"
    assert result.subsystem_count >= 5
    assert "oracle_pipeline" in result.subsystem_ids
    assert "aal_viz" in result.subsystem_ids
    assert len(result.canonical_hash) == 64


def test_subsystem_registry_deterministic_hash() -> None:
    first = load_subsystem_registry()
    second = load_subsystem_registry()
    assert first.canonical_hash == second.canonical_hash
    assert first.subsystem_ids == second.subsystem_ids
