"""Test deterministic sigil generation for ABX-Runes.

Ensures that sigil generation is deterministic:
- Same seed -> same SVG bytes
- Same rune definition -> same sigil
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from abraxas.runes.models import RuneDefinition
from abraxas.runes.sigil_generator import SigilPRNG, generate_sigil


class TestSigilPRNG:
    """Test SigilPRNG determinism."""

    def test_prng_deterministic(self):
        """Test that PRNG produces same sequence for same seed."""
        seed = "test_seed_material"

        prng1 = SigilPRNG(seed)
        prng2 = SigilPRNG(seed)

        # Generate sequences
        seq1 = [prng1.next_float() for _ in range(100)]
        seq2 = [prng2.next_float() for _ in range(100)]

        assert seq1 == seq2, "PRNG must produce identical sequences for same seed"

    def test_prng_different_seeds(self):
        """Test that different seeds produce different sequences."""
        prng1 = SigilPRNG("seed1")
        prng2 = SigilPRNG("seed2")

        seq1 = [prng1.next_float() for _ in range(10)]
        seq2 = [prng2.next_float() for _ in range(10)]

        assert seq1 != seq2, "Different seeds must produce different sequences"

    def test_prng_next_int_range(self):
        """Test that next_int respects bounds."""
        prng = SigilPRNG("test")

        for _ in range(100):
            val = prng.next_int(5, 10)
            assert 5 <= val <= 10, f"next_int must respect bounds, got {val}"

    def test_prng_next_angle_range(self):
        """Test that next_angle is in valid range."""
        import math

        prng = SigilPRNG("test")

        for _ in range(100):
            angle = prng.next_angle()
            assert 0 <= angle < 2 * math.pi, f"next_angle must be in [0, 2π), got {angle}"


class TestSigilDeterminism:
    """Test sigil generation determinism."""

    @pytest.mark.parametrize(
        "rune_id",
        [
            "ϟ₁",
            "ϟ₂",
            "ϟ₃",
            "ϟ₄",
            "ϟ₅",
            "ϟ₆",
            "ϟ₇",
            "ϟ₈",
            "ϟ₉",
            "ϟ₁₀",
            "ϟ₁₁",
            "ϟ₁₂",
            "ϟ₁₃",
            "ϟ₁₄",
            "ϟ₁₅",
            "ϟ₁₆",
            "ϟ₁₇",
            "ϟ₁₈",
            "ϟ₁₉",
            "ϟ₂₀",
            "ϟ₂₁",
        ],
    )
    def test_sigil_deterministic(self, rune_id: str):
        """Test that same seed produces identical SVG."""
        seed = f"test_seed_{rune_id}"

        svg1 = generate_sigil(rune_id, seed)
        svg2 = generate_sigil(rune_id, seed)

        assert svg1 == svg2, f"Sigil for {rune_id} must be deterministic"
        assert len(svg1) > 0, "SVG must not be empty"
        assert svg1.startswith("<svg"), "SVG must start with <svg tag"
        assert svg1.endswith("</svg>\n"), "SVG must end with </svg> tag"

    def test_sigil_different_seeds(self):
        """Test that different seeds produce different SVGs."""
        svg1 = generate_sigil("ϟ₁", "seed1")
        svg2 = generate_sigil("ϟ₁", "seed2")

        assert svg1 != svg2, "Different seeds must produce different sigils"

    def test_sigil_svg_structure(self):
        """Test that generated SVG has expected structure."""
        svg = generate_sigil("ϟ₁", "test_seed")

        # Check basic SVG structure
        assert '<svg' in svg
        assert 'viewBox="0 0 512 512"' in svg
        assert 'width="512"' in svg
        assert 'height="512"' in svg
        assert '<g id="sigil">' in svg
        assert '</g>' in svg

    def test_all_runes_generate(self):
        """Test that all runes can generate sigils without errors."""
        rune_ids = [
            "ϟ₁",
            "ϟ₂",
            "ϟ₃",
            "ϟ₄",
            "ϟ₅",
            "ϟ₆",
            "ϟ₇",
            "ϟ₈",
            "ϟ₉",
            "ϟ₁₀",
            "ϟ₁₁",
            "ϟ₁₂",
            "ϟ₁₃",
            "ϟ₁₄",
            "ϟ₁₅",
            "ϟ₁₆",
            "ϟ₁₇",
            "ϟ₁₈",
            "ϟ₁₉",
            "ϟ₂₀",
            "ϟ₂₁",
        ]

        for rune_id in rune_ids:
            svg = generate_sigil(rune_id, f"test_seed_{rune_id}")
            assert len(svg) > 0, f"Sigil for {rune_id} must not be empty"

    def test_invalid_rune_id_raises(self):
        """Test that invalid rune ID raises ValueError."""
        with pytest.raises(ValueError, match="No sigil generator for rune ID"):
            generate_sigil("ϟ₉₉", "test_seed")


class TestRuneDefinitionIntegration:
    """Test integration between rune definitions and sigil generation."""

    def test_load_all_definitions(self):
        """Test that all rune definitions can be loaded."""
        definitions_dir = Path(__file__).parent.parent / "abraxas" / "runes" / "definitions"
        json_files = list(definitions_dir.glob("rune_*.json"))

        assert len(json_files) == 21, "Expected 21 rune definition files"

        for json_file in json_files:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            rune = RuneDefinition(**data)
            assert rune.id is not None
            assert rune.short_name is not None
            assert rune.canonical_statement is not None

    def test_seed_material_generation(self):
        """Test that seed material is generated correctly."""
        rune = RuneDefinition(
            id="ϟ₁",
            name="Test Rune",
            short_name="TST",
            layer="Core",
            motto="Test motto",
            function="Test function",
            canonical_statement="Test statement",
            introduced_version="1.0.0",
        )

        seed = rune.get_seed_material()
        assert "ϟ₁" in seed
        assert "TST" in seed
        assert "1.0.0" in seed
        assert "Test statement" in seed

    def test_deterministic_from_definition(self):
        """Test that sigil is deterministic when using rune definition seed."""
        rune = RuneDefinition(
            id="ϟ₁",
            name="Test Rune",
            short_name="TST",
            layer="Core",
            motto="Test motto",
            function="Test function",
            canonical_statement="Test statement",
            introduced_version="1.0.0",
        )

        seed = rune.get_seed_material()
        svg1 = generate_sigil(rune.id, seed)
        svg2 = generate_sigil(rune.id, seed)

        assert svg1 == svg2, "Sigil must be deterministic from rune definition"
