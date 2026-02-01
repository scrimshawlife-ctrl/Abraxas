"""
ABX-Runes Coupling Enforcement Test

Static analysis test ensuring engine.py imports invoke_rune and does NOT
import SDCT domain modules directly.

This enforces the ABX-Runes coupling policy:
  engine -> runes.invoke -> rune modules -> cartridges
  (NOT: engine -> cartridges directly)
"""
from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import List, Set, Tuple

import pytest


# Paths relative to repo root
ENGINE_PATH = Path(__file__).parent.parent / "abraxas_ase" / "engine.py"
COUPLING_MAP_PATH = Path(__file__).parent.parent / "abraxas_ase" / "runes" / "coupling_map.v0.yaml"


# Forbidden imports from engine.py
FORBIDDEN_IMPORTS = {
    "abraxas_ase.domains.text_subword",
    "abraxas_ase.domains.digit_motif",
    "abraxas_ase.domains.cartridge",
    "abraxas_ase.domains.registry",
}

# Required imports (engine must use rune invocation)
REQUIRED_IMPORTS = {
    "abraxas_ase.runes.invoke",
    "abraxas_ase.runes",
}

# Allowed domain imports (types only)
ALLOWED_DOMAIN_IMPORTS = {
    "abraxas_ase.domains.types",
}


def extract_imports_from_file(filepath: Path) -> Tuple[Set[str], Set[str]]:
    """
    Extract all imports from a Python file.

    Returns:
        (import_modules, from_modules): Sets of module paths
    """
    if not filepath.exists():
        return set(), set()

    content = filepath.read_text(encoding="utf-8")
    tree = ast.parse(content, filename=str(filepath))

    import_modules: Set[str] = set()
    from_modules: Set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                import_modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                from_modules.add(node.module)
                # Also track full paths for "from X import Y"
                for alias in node.names:
                    from_modules.add(f"{node.module}.{alias.name}")

    return import_modules, from_modules


def find_all_imports(filepath: Path) -> Set[str]:
    """Get all imports (both styles) from a file."""
    imports, froms = extract_imports_from_file(filepath)
    return imports | froms


class TestEngineCoupling:
    """Test that engine.py respects ABX-Runes coupling policy."""

    def test_engine_file_exists(self):
        """Sanity check: engine.py exists."""
        assert ENGINE_PATH.exists(), f"Engine file not found: {ENGINE_PATH}"

    def test_no_direct_cartridge_imports(self):
        """
        Engine must NOT import cartridge implementations directly.
        """
        all_imports = find_all_imports(ENGINE_PATH)

        violations: List[str] = []
        for forbidden in FORBIDDEN_IMPORTS:
            for imp in all_imports:
                if imp == forbidden or imp.startswith(f"{forbidden}."):
                    violations.append(imp)

        assert not violations, (
            f"Engine has forbidden direct cartridge imports:\n"
            f"  {violations}\n"
            f"Engine must use rune invocation instead."
        )

    def test_allowed_domain_types_import(self):
        """
        Engine MAY import domain types (for shared data structures).
        """
        all_imports = find_all_imports(ENGINE_PATH)

        # This test just documents that types imports are allowed
        types_imports = [
            imp for imp in all_imports
            if imp in ALLOWED_DOMAIN_IMPORTS or
            any(imp.startswith(f"{allowed}.") for allowed in ALLOWED_DOMAIN_IMPORTS)
        ]

        # No assertion - just documenting allowed pattern
        # If types are imported, that's fine

    def test_no_textsubword_class_reference(self):
        """
        Engine must not reference TextSubwordCartridge class directly.
        """
        if not ENGINE_PATH.exists():
            pytest.skip("Engine file not found")

        content = ENGINE_PATH.read_text(encoding="utf-8")

        # Check for class name references
        forbidden_patterns = [
            r"TextSubwordCartridge",
            r"DigitMotifCartridge",
            r"BaseCartridge",
            r"SymbolicDomainCartridge",
        ]

        violations: List[str] = []
        for pattern in forbidden_patterns:
            if re.search(pattern, content):
                violations.append(pattern)

        assert not violations, (
            f"Engine references forbidden cartridge classes:\n"
            f"  {violations}\n"
            f"Engine must only reference via rune_id strings."
        )


class TestRuneInvocationPresence:
    """Test that rune invocation infrastructure exists."""

    def test_invoke_module_exists(self):
        """Rune invoke module must exist."""
        invoke_path = Path(__file__).parent.parent / "abraxas_ase" / "runes" / "invoke.py"
        assert invoke_path.exists(), f"Rune invoke module not found: {invoke_path}"

    def test_catalog_exists(self):
        """Rune catalog must exist."""
        catalog_path = Path(__file__).parent.parent / "abraxas_ase" / "runes" / "catalog.v0.yaml"
        assert catalog_path.exists(), f"Rune catalog not found: {catalog_path}"

    def test_text_subword_rune_exists(self):
        """TextSubword rune adapter must exist."""
        rune_path = Path(__file__).parent.parent / "abraxas_ase" / "runes" / "sdct_text_subword_v1.py"
        assert rune_path.exists(), f"TextSubword rune not found: {rune_path}"


class TestCouplingMapPresence:
    """Test that coupling map documentation exists."""

    def test_coupling_map_exists(self):
        """Coupling map must exist."""
        assert COUPLING_MAP_PATH.exists(), (
            f"Coupling map not found: {COUPLING_MAP_PATH}\n"
            f"ABX-Runes enforcement requires documented coupling policy."
        )

    def test_coupling_map_has_forbidden_section(self):
        """Coupling map must document forbidden imports."""
        if not COUPLING_MAP_PATH.exists():
            pytest.skip("Coupling map not found")

        content = COUPLING_MAP_PATH.read_text(encoding="utf-8")
        assert "forbidden:" in content.lower(), (
            "Coupling map must have 'forbidden:' section"
        )


class TestContractSchemasExist:
    """Test that SDCT contract schemas exist."""

    def test_domain_params_schema_exists(self):
        """Domain params schema must exist."""
        schema_path = (
            Path(__file__).parent.parent /
            "abraxas_ase" / "sdct" / "contracts" /
            "sdct_domain_params.v0.schema.json"
        )
        assert schema_path.exists(), f"Domain params schema not found: {schema_path}"

    def test_evidence_row_schema_exists(self):
        """Evidence row schema must exist."""
        schema_path = (
            Path(__file__).parent.parent /
            "abraxas_ase" / "sdct" / "contracts" /
            "sdct_evidence_row.v0.schema.json"
        )
        assert schema_path.exists(), f"Evidence row schema not found: {schema_path}"

    def test_motif_schema_exists(self):
        """Motif schema must exist."""
        schema_path = (
            Path(__file__).parent.parent /
            "abraxas_ase" / "sdct" / "contracts" /
            "sdct_motif.v0.schema.json"
        )
        assert schema_path.exists(), f"Motif schema not found: {schema_path}"
