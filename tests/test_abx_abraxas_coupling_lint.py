"""Coupling lint to prevent direct ABX → Abraxas imports.

ABX must communicate with Abraxas through capability contracts (ABX-Runes),
except for the explicitly allowed imports:

- abraxas.runes.*
- abraxas.core.provenance

This test is intentionally *ratcheting*: it prevents the violation count from
increasing, while allowing incremental migration work to reduce it over time.
"""

from __future__ import annotations

import re
from pathlib import Path


ABX_ROOT = Path("abx")

ALLOWED_PREFIXES: tuple[str, ...] = (
    "from abraxas.runes.",
    "import abraxas.runes.",
    "from abraxas.core.provenance",
    "import abraxas.core.provenance",
)

# Update this value downward as violations are removed.
MAX_VIOLATIONS = 55


_FROM_ABRAXAS_RE = re.compile(r"^\s*from\s+abraxas\.")
_IMPORT_ABRAXAS_RE = re.compile(r"^\s*import\s+abraxas\.")


def _is_allowed_import(line: str) -> bool:
    stripped = line.strip()
    if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
        return True
    return stripped.startswith(ALLOWED_PREFIXES)


def test_abx_to_abraxas_coupling_is_not_increasing() -> None:
    violations: list[str] = []

    for path in sorted(ABX_ROOT.rglob("*.py")):
        # Skip Python cache / venv artifacts if present
        if "__pycache__" in path.parts:
            continue

        for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
            if not (_FROM_ABRAXAS_RE.match(line) or _IMPORT_ABRAXAS_RE.match(line)):
                continue
            if _is_allowed_import(line):
                continue
            violations.append(f"{path}:{lineno}: {line.strip()}")

    assert len(violations) <= MAX_VIOLATIONS, (
        f"ABX→Abraxas coupling violations: {len(violations)} (cap: {MAX_VIOLATIONS}).\n"
        "Migrate ABX modules to ABX-Runes capability contracts (see docs/migration/abx_runes_coupling.md).\n"
        "Violations:\n"
        + "\n".join(violations)
    )

