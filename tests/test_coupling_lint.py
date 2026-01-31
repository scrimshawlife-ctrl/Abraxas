"""Coupling lint to prevent direct cross-subsystem imports.

Enforces ABX-Runes architecture: all cross-subsystem communication must go
through capability contracts, not direct imports.

This test uses RATCHETING: violation count must decrease or stay the same.
Never allow new violations to be added.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import List, Tuple


# TypeScript/JavaScript forbidden patterns (original test)
TS_FORBIDDEN_PATTERNS = [
    "../runes",
    "./runes.js",
    "../../runes",
    "../../runes.js",
    "require(\"../../runes\")",
    "require('../../runes')",
]

TS_ALLOWED_FILES = {
    Path("server/abraxas/runes/registry.js"),
    Path("server/runes.js"),
    # These are rune system adapters - allowed
    Path("server/abraxas/integrations/ers-scheduler.ts"),
    Path("server/abraxas/integrations/runes-adapter.ts"),
    Path("server/abraxas/routes/api.ts"),
}

# Python allowed imports (exceptions to coupling rule)
PY_ALLOWED_IMPORTS = {
    "abraxas.runes",  # Rune system itself
    "abraxas.core.provenance",  # Provenance utilities
}

# Maximum allowed violations (RATCHET - must only decrease)
# Update this number as violations are fixed
# NOTE: AST-based counting is more accurate than grep (finds 81 vs 34)
MAX_ALLOWED_VIOLATIONS = 81  # Actual baseline (2026-01-04, AST-based)


def find_python_coupling_violations(repo_root: Path) -> List[Tuple[Path, str]]:
    """Find Python files with direct abraxas.* imports in abx/ directory."""
    violations = []
    abx_root = repo_root / "abx"

    if not abx_root.exists():
        return violations

    for py_file in abx_root.rglob("*.py"):
        # Skip test files (tests can import anything)
        if py_file.name.startswith("test_"):
            continue

        try:
            content = py_file.read_text(encoding="utf-8")
            tree = ast.parse(content)
        except (SyntaxError, UnicodeDecodeError):
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith("abraxas."):
                    # Check if it's an allowed import
                    is_allowed = any(
                        node.module.startswith(allowed)
                        for allowed in PY_ALLOWED_IMPORTS
                    )
                    if not is_allowed:
                        rel_path = py_file.relative_to(repo_root)
                        violations.append((rel_path, node.module))

    return violations


def test_no_typescript_direct_rune_imports() -> None:
    """TypeScript: Prevent direct rune imports (original test)."""
    repo_root = Path(__file__).resolve().parents[1]
    server_root = repo_root / "server"
    violations = []

    for path in server_root.rglob("*"):
        if path.is_dir() or path.suffix not in {".ts", ".js"}:
            continue
        rel_path = path.relative_to(repo_root)
        if rel_path in TS_ALLOWED_FILES:
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in TS_FORBIDDEN_PATTERNS:
            if pattern in content:
                violations.append(f"{rel_path}: {pattern}")
                break

    assert not violations, "Direct rune imports detected:\n" + "\n".join(violations)


def test_python_abx_no_direct_abraxas_imports() -> None:
    """Python: ABX modules must not directly import from abraxas.* (except runes/provenance).

    RATCHETING TEST: Violation count must be <= MAX_ALLOWED_VIOLATIONS.
    As violations are fixed, update MAX_ALLOWED_VIOLATIONS to the new (lower) count.
    """
    repo_root = Path(__file__).resolve().parents[1]
    violations = find_python_coupling_violations(repo_root)

    violation_count = len(violations)

    # RATCHET: Must not exceed baseline
    if violation_count > MAX_ALLOWED_VIOLATIONS:
        # Show first 10 violations for debugging
        violation_msgs = [
            f"  {path}: {module}"
            for path, module in violations[:10]
        ]
        if len(violations) > 10:
            violation_msgs.append(f"  ... and {len(violations) - 10} more")

        assert False, (
            f"ABX→Abraxas coupling violations increased!\n"
            f"Found: {violation_count}, Max allowed: {MAX_ALLOWED_VIOLATIONS}\n"
            f"\n"
            f"Violations:\n" + "\n".join(violation_msgs) + "\n"
            f"\n"
            f"Fix by using capability contracts instead:\n"
            f"  from abraxas.runes.invoke import invoke_capability\n"
            f"  result = invoke_capability('oracle.v2.run', inputs, ctx=ctx)\n"
            f"\n"
            f"See docs/migration/abx_runes_coupling.md for migration guide."
        )

    # SUCCESS: Print progress
    if violation_count < MAX_ALLOWED_VIOLATIONS:
        print(
            f"\n✅ ABX→Abraxas coupling improved! "
            f"{violation_count}/{MAX_ALLOWED_VIOLATIONS} violations "
            f"({MAX_ALLOWED_VIOLATIONS - violation_count} fixed)\n"
            f"   Update MAX_ALLOWED_VIOLATIONS to {violation_count} in test_coupling_lint.py"
        )
    elif violation_count == MAX_ALLOWED_VIOLATIONS:
        print(
            f"\n⚠️  ABX→Abraxas coupling: {violation_count}/{MAX_ALLOWED_VIOLATIONS} violations "
            f"(no change)\n"
            f"   Next: Fix violations and decrease MAX_ALLOWED_VIOLATIONS"
        )


def test_python_abraxas_no_abx_imports() -> None:
    """Python: Abraxas modules should not import from abx.* (reverse coupling check).

    NOTE: 1 known exception (abraxas.artifacts.proof_bundle → abx.util.hashutil)
    This is tracked and should be refactored.
    """
    repo_root = Path(__file__).resolve().parents[1]
    abraxas_root = repo_root / "abraxas"
    violations = []

    # Known exceptions (should be refactored)
    known_exceptions = {
        (Path("abraxas/artifacts/proof_bundle.py"), "abx.util.hashutil"),
    }

    if not abraxas_root.exists():
        return

    for py_file in abraxas_root.rglob("*.py"):
        if py_file.name.startswith("test_"):
            continue

        try:
            content = py_file.read_text(encoding="utf-8")
            tree = ast.parse(content)
        except (SyntaxError, UnicodeDecodeError):
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith("abx."):
                    rel_path = py_file.relative_to(repo_root)
                    violation = (rel_path, node.module)
                    if violation not in known_exceptions:
                        violations.append(violation)

    if violations:
        violation_msgs = [f"  {path}: {module}" for path, module in violations[:10]]
        assert False, (
            f"Abraxas→ABX reverse coupling detected (new violations):\n" +
            "\n".join(violation_msgs)
        )
