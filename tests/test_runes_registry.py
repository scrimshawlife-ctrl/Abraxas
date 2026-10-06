"""Tests for canonical ABX-Runes registry integrity."""

from __future__ import annotations

from abraxas.runes.registry import load_registry, list_capabilities, wiring_sanity_check


def test_registry_integrity() -> None:
    bindings = load_registry()
    assert bindings, "Registry should return at least one rune binding"

    ids = [b.rune_id for b in bindings]
    assert len(ids) == len(set(ids)), "Rune IDs must be unique"

    for binding in bindings:
        # `RUNE.<PATH>` uppercase is the declared convention, per docs/runes/ -- the
        # Rune Specs Index, which the governing skill's precedence order ranks above
        # Notion and historical records:
        #   docs/runes/README.md:4       "payload contract for `RUNE.CODE.REVIEW`"
        #   docs/runes/FIND_SKILLS.md:1  # RUNE.FIND_SKILLS
        #   docs/runes/CODE_REVIEW.md:26 contract marker `RUNE.CODE.REVIEW.contract.v1`
        # This previously asserted the lowercase "rune:" form, which matched neither the
        # declared convention nor the 62 dotted capability ids -- 62 of 117 bindings
        # failed it, and the remaining 55 contradicted the documented form too.
        assert binding.capability.startswith("RUNE."), "Capability must be tagged"
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
