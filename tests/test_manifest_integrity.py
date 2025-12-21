"""Test manifest integrity for ABX-Runes sigils.

Ensures that:
- Manifest exists and is valid
- All referenced files exist
- Hashes match file contents
- Registry references exist
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from abraxas.runes.models import RuneDefinition, SigilManifest


class TestManifestIntegrity:
    """Test sigil manifest integrity."""

    @pytest.fixture
    def manifest_path(self) -> Path:
        """Get manifest path."""
        return Path(__file__).parent.parent / "abraxas" / "runes" / "sigils" / "manifest.json"

    @pytest.fixture
    def manifest(self, manifest_path: Path) -> SigilManifest:
        """Load manifest."""
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return SigilManifest(**data)

    def test_manifest_exists(self, manifest_path: Path):
        """Test that manifest file exists."""
        assert manifest_path.exists(), f"Manifest must exist at {manifest_path}"

    def test_manifest_valid(self, manifest: SigilManifest):
        """Test that manifest is valid."""
        assert manifest.generated_at_utc is not None
        assert manifest.generator_version is not None
        assert len(manifest.entries) > 0

    def test_manifest_has_all_runes(self, manifest: SigilManifest):
        """Test that manifest contains all 6 runes."""
        expected_ids = ["ϟ₁", "ϟ₂", "ϟ₃", "ϟ₄", "ϟ₅", "ϟ₆"]
        actual_ids = [entry.id for entry in manifest.entries]

        for expected_id in expected_ids:
            assert expected_id in actual_ids, f"Manifest must contain {expected_id}"

    def test_all_sigil_files_exist(self, manifest: SigilManifest):
        """Test that all referenced sigil files exist."""
        runes_root = Path(__file__).parent.parent / "abraxas" / "runes"

        for entry in manifest.entries:
            file_path = runes_root / entry.svg_path
            assert file_path.exists(), f"Sigil file must exist: {entry.svg_path}"

    def test_all_hashes_match(self, manifest: SigilManifest):
        """Test that all manifest hashes match file contents."""
        runes_root = Path(__file__).parent.parent / "abraxas" / "runes"

        for entry in manifest.entries:
            file_path = runes_root / entry.svg_path

            with open(file_path, "r", encoding="utf-8") as f:
                svg_content = f.read()

            actual_hash = hashlib.sha256(svg_content.encode("utf-8")).hexdigest()
            assert actual_hash == entry.sha256, f"Hash mismatch for {entry.id}: expected {entry.sha256}, got {actual_hash}"

    def test_svg_dimensions(self, manifest: SigilManifest):
        """Test that all sigils have correct dimensions."""
        for entry in manifest.entries:
            assert entry.width == 512, f"Width must be 512 for {entry.id}"
            assert entry.height == 512, f"Height must be 512 for {entry.id}"

    def test_seed_material_present(self, manifest: SigilManifest):
        """Test that all entries have seed material."""
        for entry in manifest.entries:
            assert entry.seed_material is not None
            assert len(entry.seed_material) > 0, f"Seed material must not be empty for {entry.id}"

    def test_svg_well_formed(self, manifest: SigilManifest):
        """Test that all SVG files are well-formed."""
        runes_root = Path(__file__).parent.parent / "abraxas" / "runes"

        for entry in manifest.entries:
            file_path = runes_root / entry.svg_path

            with open(file_path, "r", encoding="utf-8") as f:
                svg_content = f.read()

            # Basic well-formedness checks
            assert svg_content.startswith("<svg"), f"SVG must start with <svg tag for {entry.id}"
            assert svg_content.endswith("</svg>\n"), f"SVG must end with </svg> tag for {entry.id}"
            assert '<g id="sigil">' in svg_content, f"SVG must have sigil group for {entry.id}"


class TestRegistryReferences:
    """Test that registry references exist for all sigils."""

    def test_definition_files_exist(self):
        """Test that all rune definition files exist."""
        definitions_dir = Path(__file__).parent.parent / "abraxas" / "runes" / "definitions"
        expected_files = [
            "rune_01_rfa.json",
            "rune_02_tam.json",
            "rune_03_wsss.json",
            "rune_04_sds.json",
            "rune_05_ipl.json",
            "rune_06_add.json",
        ]

        for filename in expected_files:
            file_path = definitions_dir / filename
            assert file_path.exists(), f"Definition file must exist: {filename}"

    def test_definitions_match_manifest(self):
        """Test that definitions match manifest entries."""
        repo_root = Path(__file__).parent.parent
        definitions_dir = repo_root / "abraxas" / "runes" / "definitions"
        manifest_path = repo_root / "abraxas" / "runes" / "sigils" / "manifest.json"

        # Load manifest
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        manifest = SigilManifest(**manifest_data)

        # Check each manifest entry has a definition
        for entry in manifest.entries:
            # Find definition file
            found = False
            for json_file in definitions_dir.glob("rune_*.json"):
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                rune = RuneDefinition(**data)

                if rune.id == entry.id:
                    found = True
                    assert rune.short_name == entry.short_name, f"Short name mismatch for {entry.id}"
                    break

            assert found, f"No definition found for manifest entry {entry.id}"


class TestRegeneration:
    """Test that sigils can be regenerated deterministically using builder."""

    def test_builder_check_passes(self):
        """Test that builder --check validation passes."""
        import subprocess

        repo_root = Path(__file__).parent.parent
        result = subprocess.run(
            ["python", "scripts/abx_runes_build.py", "--check"],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Builder check failed: {result.stderr}"
        assert "[OK]" in result.stdout, "Builder check should output [OK]"
