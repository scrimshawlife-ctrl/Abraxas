"""Every tracked Python module must at least parse.

A module that cannot be parsed cannot be imported, cannot be tested, and -- because
`scripts/check_optional_dependency_boundaries.py` skips unparseable files -- is also exempt from the
dependency-boundary checks. Such a file is invisible: present in the tree, dead everywhere it matters.

Measured 2026-10-07: 3 of 3613 tracked `.py` files did not parse. One was a real defect --
`abx/media_origin_verify.py` used `args.in` on two lines, and `in` is a reserved keyword, so the file
had been unimportable since its only commit while `abx/cycle_runner.py` invokes it as a module. The other
two are legitimately unparseable and are allowlisted below by exact path with a stated reason.

The parser stops at the FIRST error, so fixing `the syntax error` in a file with a repeated pattern can
leave the file still broken -- the second occurrence only surfaces on the next parse. This guard parses
the whole file, so it sees all of them.
"""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

#: Paths that are EXPECTED not to parse, each with its reason. An allowlist without reasons becomes a
#: place to hide things, so keep this list as small as possible and justify every entry.
UNPARSEABLE_BY_DESIGN = {
    # A cookiecutter template: contains `{{ ... }}` placeholders by design, so it is not valid Python.
    ".github/engine-cookiecutter/engine_template/src/engine_template/__init__.py",
    # A generated script under `.abraxas/` (a directory rewritten by test runs), not a source module.
    ".abraxas/scripts/proof_requirement_lookup.py",
}


def _tracked_python_files() -> list[str]:
    """Every tracked `.py` file except the allowlisted ones, via git (not a filesystem walk)."""
    listing = subprocess.run(
        ["git", "ls-files", "*.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    return [rel for rel in listing if rel not in UNPARSEABLE_BY_DESIGN]


def test_every_tracked_python_module_parses() -> None:
    """No tracked module may be unimportable.

    `ast.parse` over the full file, so multiple syntax errors in one file are all reported rather than
    only the first one the compiler happened to reach.
    """
    broken: list[str] = []
    for rel in _tracked_python_files():
        path = REPO_ROOT / rel
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:  # unreadable is also a defect
            broken.append(f"{rel}: {type(exc).__name__}: {exc}")
            continue
        try:
            ast.parse(source, filename=rel)
        except SyntaxError as exc:
            broken.append(f"{rel}:{exc.lineno}: {exc.msg}")

    assert broken == [], (
        f"{len(broken)} tracked module(s) cannot be parsed, so they cannot be imported, tested, or "
        "dependency-checked:\n  " + "\n  ".join(broken)
    )


def test_allowlist_entries_are_still_unparseable() -> None:
    """Counterfactual: a STALE allowlist is a hiding place.

    If an allowlisted file becomes valid Python (or disappears), the entry must go, or the allowlist
    quietly exempts something nobody is watching. This test fails so the entry gets removed.
    """
    stale: list[str] = []
    for rel in sorted(UNPARSEABLE_BY_DESIGN):
        path = REPO_ROOT / rel
        if not path.exists():
            stale.append(f"{rel}: no longer exists -- remove it from UNPARSEABLE_BY_DESIGN")
            continue
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=rel)
        except SyntaxError:
            continue
        stale.append(f"{rel}: now parses -- remove it from UNPARSEABLE_BY_DESIGN")

    assert stale == [], "stale allowlist entries:\n  " + "\n  ".join(stale)
