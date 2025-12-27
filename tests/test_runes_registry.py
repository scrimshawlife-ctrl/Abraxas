"""Tests for canonical ABX-Runes registry integrity."""

from __future__ import annotations

from abraxas.runes.registry import load_registry, list_capabilities, wiring_sanity_check


def test_registry_integrity() -> None:
    bindings = load_registry()
    assert bindings, "Registry should return at least one rune binding"

    ids = [b.rune_id for b in bindings]
    assert len(ids) == len(set(ids)), "Rune IDs must be unique"

    for binding in bindings:
        assert binding.capability.startswith("rune:"), "Capability must be tagged"
        assert binding.inputs is not None
        assert binding.outputs is not None
        assert binding.operator_path


def test_registry_capabilities_present() -> None:
    bindings = load_registry()
    capabilities = list_capabilities(bindings)
    assert capabilities, "Capabilities list should not be empty"

    sanity = wiring_sanity_check(capabilities)
    assert sanity["duplicate_rune_ids"] == []
    assert sanity["missing_capabilities"] == []
