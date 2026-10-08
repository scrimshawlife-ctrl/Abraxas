"""Test modules inside the importable package ship to consumers. Ratcheted, not fixed.

MEASURED 2026-10-08 by building the wheel (`python -m pip wheel . --no-deps`): 34 test modules
land in the distributed artifact.

    abraxas/evidence/test_*_q1.py     5
    abraxas/tests/test_*.py          11
    abx_familiar/tests/test_*.py     18

WHY THIS IS A RATCHET AND NOT AN ASSERTION OF CORRECTNESS

The fix was attempted and FAILED, so the count is recorded rather than reduced. Three mechanisms
were tested against a freshly rebuilt wheel and none moved the number off 34:

  1. `exclude = ["abraxas.tests*", "abx_familiar.tests*"]` in `[tool.setuptools.packages.find]`
  2. `include-package-data = false`
  3. deleting the stale `build/` directory before rebuilding (it did hold a copy of all 34, so it
     contaminated the first measurements, but removing it changed nothing)

Root cause is unresolved in setuptools packaging internals. The value at stake is package bloat
rather than breakage, so the effort was stopped deliberately rather than ground on. What is left
is still worth having: the count can no longer GROW unnoticed.

Do NOT "fix" this by moving 34 modules out of two existing packages. That rewrites import paths
and CI invocation lists for no consumer benefit, a worse trade than 34 files of bloat. And do not
lower the constant by deleting this test. Lower it only by re-measuring the wheel.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOTS = ("abraxas", "abx", "abx_familiar")

#: Measured against the built wheel on 2026-10-08. May only DECREASE.
MEASURED_SHIPPED_TEST_MODULES = 34


def _test_modules_inside_package() -> list[str]:
    found: list[str] = []
    for root in SOURCE_ROOTS:
        for path in (REPO_ROOT / root).rglob("test_*.py"):
            if "__pycache__" not in path.parts:
                found.append(str(path.relative_to(REPO_ROOT)))
    return sorted(found)


def test_shipped_test_modules_do_not_grow() -> None:
    found = _test_modules_inside_package()
    assert len(found) <= MEASURED_SHIPPED_TEST_MODULES, (
        f"{len(found)} test modules live inside the importable package, up from the measured "
        f"{MEASURED_SHIPPED_TEST_MODULES}. A new test module belongs in tests/ at the repo root, "
        f"not in a package that gets distributed. By directory: "
        f"abraxas/evidence={sum('evidence' in f for f in found)}, "
        f"abraxas/tests={sum(f.startswith('abraxas/tests/') for f in found)}, "
        f"abx_familiar/tests={sum(f.startswith('abx_familiar/tests/') for f in found)}."
    )
