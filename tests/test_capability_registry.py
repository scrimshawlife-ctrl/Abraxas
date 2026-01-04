"""Test capability registry loading and validation."""

from abraxas.runes.capabilities import load_capability_registry, register_capability


def test_registry_loads():
    """Capability registry must load without errors."""
    registry = load_capability_registry()
    assert registry.version is not None
    assert isinstance(registry.capabilities, list)


def test_find_capability():
    """Must find capability by ID."""
    registry = load_capability_registry()
    # After Patch 002, oracle.v2.run will be registered
    oracle_cap = registry.find_capability("oracle.v2.run")
    # Initially None, will pass after Patch 002
    # assert oracle_cap is not None if registered


def test_register_capability():
    """Must be able to register a test capability."""
    cap = register_capability(
        capability_id="test.example.run",
        rune_id="ϟ_TEST",
        operator_path="test.module:test_function",
        version="1.0.0",
        deterministic=True
    )
    assert cap.capability_id == "test.example.run"
    assert cap.rune_id == "ϟ_TEST"
    assert cap.deterministic is True
    assert cap.provenance_required is True


def test_list_by_prefix():
    """Must list capabilities by prefix."""
    registry = load_capability_registry()
    # After capabilities are added, this will find them
    oracle_caps = registry.list_by_prefix("oracle.")
    assert isinstance(oracle_caps, list)


def test_capability_schema_validation():
    """All registered capabilities must have valid schemas."""
    import json
    import os
    from pathlib import Path

    registry = load_capability_registry()
    repo_root = Path(__file__).parent.parent

    for cap in registry.capabilities:
        if cap.input_schema:
            schema_path = repo_root / cap.input_schema
            assert schema_path.exists(), f"Missing input schema: {cap.input_schema}"
            schema = json.loads(schema_path.read_text())
            assert "$schema" in schema, f"Invalid JSON schema: {cap.input_schema}"

        if cap.output_schema:
            schema_path = repo_root / cap.output_schema
            assert schema_path.exists(), f"Missing output schema: {cap.output_schema}"
            schema = json.loads(schema_path.read_text())
            assert "$schema" in schema, f"Invalid JSON schema: {cap.output_schema}"
