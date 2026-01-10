"""Deterministic autopoiesis candidate generation."""

from __future__ import annotations

from abraxas.linguistics.autopoiesis import propose_sources


def test_autopoiesis_deterministic():
    output_a = propose_sources(tokens=["neologism"])
    output_b = propose_sources(tokens=["neologism"])
    assert output_a == output_b
