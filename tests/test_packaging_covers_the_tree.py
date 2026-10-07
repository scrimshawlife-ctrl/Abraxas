"""Guard: the packaging configuration must cover every module the source tree ships.

Measured 2026-10-07 by building an install of this repository's declared git dependency in a fresh venv:
`abraxas` installed, but `import abraxas.evidence` raised `ModuleNotFoundError: No module named
'abraxas.evidence'`. The cause was `[tool.setuptools] packages`, an explicit list of 73 names against 133
real subpackages in the tree — 85 absent from every install, including `abraxas.evidence`,
`abraxas.engines`, `abraxas.phase` and `abraxas.yggdrasil`.

The consequence is not cosmetic. Every engine repository declares this project as a dependency
(`abraxas @ git+https://github.com/scrimshawlife-ctrl/Abraxas.git`), so a clean install of that dependency
produced a package whose evidence, engines, phase and yggdrasil subpackages could not be imported at all.

Nothing guarded the list, which is why it drifted. These tests guard it, and they resolve the EFFECTIVE
configuration — a hand-written `packages` list or a `packages.find` block — so neither form can hide the
same gap again.
"""

from __future__ import annotations

import pathlib
import tomllib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
PYPROJECT = REPO_ROOT / "pyproject.toml"


def _real_subpackages() -> set[str]:
    """Every importable `abraxas.*` subpackage that exists on disk, from its `__init__.py`."""
    found: set[str] = set()
    for init in (REPO_ROOT / "abraxas").rglob("__init__.py"):
        parts = init.parent.relative_to(REPO_ROOT).parts
        if not parts or parts[0] != "abraxas":
            continue
        if all(part.isidentifier() for part in parts):
            found.add(".".join(parts))
    return found


def _matches_any(name: str, patterns) -> bool:
    from fnmatch import fnmatch

    return any(fnmatch(name, pat) for pat in patterns)


def _configured_packages() -> set[str]:
    """The package set the BUILD would install, whatever form the configuration takes.

    Reading the effective configuration rather than one spelling of it is the point: the original defect was
    not a wrong format, it was a list that disagreed with the tree.

    Discovery is re-implemented here rather than delegating to `setuptools.find_packages`, because setuptools
    is not importable in every interpreter this suite runs under (measured: `ModuleNotFoundError: No module
    named 'setuptools'`), and a guard that errors when its dependency is absent is worse than no guard. The
    rule mirrored is simple and stated so it can be checked: a directory holding `__init__.py`, whose dotted
    name matches an include pattern and no exclude pattern, is a package.
    """
    config = tomllib.loads(PYPROJECT.read_text())
    setuptools_cfg = config.get("tool", {}).get("setuptools", {})

    if "packages" in setuptools_cfg and isinstance(setuptools_cfg["packages"], list):
        return set(setuptools_cfg["packages"])

    find_cfg = setuptools_cfg.get("packages", {})
    if isinstance(find_cfg, dict) and "find" in find_cfg:
        find_cfg = find_cfg["find"]
    find_cfg = find_cfg if isinstance(find_cfg, dict) else {}

    where = find_cfg.get("where", ["."])
    include = find_cfg.get("include", ["*"])
    exclude = find_cfg.get("exclude", [])

    found: set[str] = set()
    for root in where:
        base = REPO_ROOT / root
        if not base.is_dir():
            continue
        for init in base.rglob("__init__.py"):
            parts = init.parent.relative_to(base).parts
            if not parts or not all(part.isidentifier() for part in parts):
                continue
            name = ".".join(parts)
            if _matches_any(name, include) and not _matches_any(name, exclude):
                found.add(name)
    return found


def test_the_packaging_configuration_is_resolvable() -> None:
    """A vacuous pass would make every assertion below meaningless."""
    configured = _configured_packages()
    assert configured, (
        "no packages resolved from the packaging configuration — this guard is asserting nothing"
    )


def test_packaging_covers_every_subpackage_in_the_tree() -> None:
    """The defect, stated as an invariant: nothing importable may be left out of the install."""
    missing = sorted(_real_subpackages() - _configured_packages())
    assert missing == [], (
        f"{len(missing)} subpackage(s) exist in the tree but are NOT in the packaging configuration, so "
        f"they are absent from every install: {missing[:15]}"
        + (" ..." if len(missing) > 15 else "")
        + "\nUse discovery ([tool.setuptools.packages.find], include = [\"abraxas*\"]) rather than a hand "
        "list, so the two cannot drift again."
    )


@pytest.mark.parametrize(
    "subpackage",
    ["abraxas.evidence", "abraxas.engines", "abraxas.phase", "abraxas.yggdrasil"],
)
def test_the_subpackages_installs_actually_needed_are_configured(subpackage: str) -> None:
    """Named explicitly because these four are what a missing install broke.

    `abraxas.evidence` is the contract the engine adapters import; `abraxas.engines` holds the canonical
    manifest; `abraxas.phase` is what the Resonance engine composes; `abraxas.yggdrasil` holds the memory
    layer Cypher manages and the coordinator that arbitrates. Every engine repository depends on this
    project through the git URL, so each one of these being absent breaks a sibling's clean install.
    """
    assert subpackage in _real_subpackages(), f"{subpackage} does not exist in the tree"
    assert subpackage in _configured_packages(), (
        f"{subpackage} is not in the packaging configuration, so a clean install cannot import it"
    )
