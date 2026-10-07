"""`import_locations` must be true: every declared site exists, and every site is declared.

The manifest's `import_locations` is the repository's record of WHERE a dependency is used. Nothing
enforced it, and it drifted: measured 2026-10-07, `fastapi` was declared at 5 sites while 45 real ones
existed, and `jsonschema` at 1 against 30.

That matters because the record is what tells a reader a surface exists at all. Both the surface policy
AND this manifest had omitted `abraxas/dashboard/`, which is a large part of why the dashboard's boundary
violation went unnoticed. These tests give the field a consumer.

The scanner is IMPORTED from `scripts/reconcile_dependency_import_locations.py` rather than reimplemented
here: two definitions of "an import site" would drift apart, and the fixer and its guard would then
disagree about the very thing being guarded. Importing it also means these tests see string-based
`require_optional_dependency("torch", ...)` guards, which a plain import scan cannot.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from scripts.reconcile_dependency_import_locations import (
    GOVERNANCE_CLASSES,
    scan_import_sites,
    scoped_dependencies,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / ".aal" / "dependency_manifest.v0.yaml"


def _load_manifest() -> dict:
    import yaml

    return yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))


def _scoped() -> dict[str, str]:
    """{dependency: class} for the governance-relevant dependencies.

    `scoped_dependencies` takes the WHOLE manifest, not its `dependencies` sub-mapping -- passing the
    sub-mapping yields an empty scope, which the instrument-health test below catches rather than
    letting every drift assertion pass vacuously.
    """
    return scoped_dependencies(_load_manifest())


@lru_cache(maxsize=1)
def _sites_by_dependency() -> dict[str, set[tuple[str, int]]]:
    """{dependency: {(path, line)}} -- one scan, shared by every assertion below.

    Cached because the alternative is one full tree walk per dependency per test: measured at ~129s for
    this module before caching, and a gate that slow gets skipped. Caching is honest here because the
    tree does not change mid-run. Only the SITE is compared -- path and line -- never the declared
    `symbol`, which is descriptive; pinpointing the site is enough to notice drift and is not brittle to
    a reworded symbol.
    """
    scanned = scan_import_sites()
    return {
        dep: {(path, line) for path, line, _top_level, _symbol in scanned.get(dep, [])}
        for dep in _scoped()
    }


def _declared_sites(dep: str) -> set[tuple[str, int]]:
    row = _load_manifest()["dependencies"][dep]
    return {(str(entry["path"]), int(entry["line"])) for entry in (row.get("import_locations") or [])}


def test_the_scan_actually_finds_import_sites() -> None:
    """Instrument health: a scan returning nothing would make every drift assertion below vacuous.

    An empty instrument and a clean bill of health look identical, so assert the scan has real output
    before trusting any comparison built on it.
    """
    scoped = _scoped()
    assert scoped, f"no dependencies resolved to {GOVERNANCE_CLASSES}; the scope has been emptied"
    assert "pytest" not in scoped, "DEV_TEST_ONLY leaked into the governance scope"

    fastapi_sites = _sites_by_dependency()["fastapi"]
    assert len(fastapi_sites) >= 5, (
        f"the scan found only {len(fastapi_sites)} fastapi site(s); the scanner is broken, "
        "not the manifest"
    )


def test_the_scan_sees_string_based_optional_dependency_guards() -> None:
    """`require_optional_dependency("x", ...)` is a usage site that an import scan cannot see.

    Counterfactual for the scanner's own blind spot: without this, regenerating the manifest DELETES the
    true `torch` / `transformers` declarations, because `timesfm_shadow/infer.py` reaches them only
    through that string guard.
    """
    torch_sites = _sites_by_dependency().get("torch", set())
    assert torch_sites, (
        "the scanner found no torch site: it is missing string-based require_optional_dependency() "
        "guards, and the regenerated manifest would delete true declarations"
    )


def test_every_import_site_is_declared() -> None:
    """No dependency may be used somewhere the manifest does not record."""
    missing: list[str] = []
    for dep in sorted(_scoped()):
        for path, line in sorted(_sites_by_dependency().get(dep, set()) - _declared_sites(dep)):
            missing.append(f"{dep}: {path}:{line} uses it but is not declared")

    assert missing == [], (
        f"{len(missing)} undeclared site(s). Every site belongs in `.aal/dependency_manifest.v0.yaml` "
        "under `import_locations` -- an unrecorded usage is how a surface goes unnoticed. Regenerate "
        "with `python scripts/reconcile_dependency_import_locations.py --write`:\n  " + "\n  ".join(missing)
    )


def test_every_declared_site_still_uses_its_dependency() -> None:
    """No stale declarations: a declared path that no longer uses the dependency is a false record."""
    stale: list[str] = []
    for dep in sorted(_scoped()):
        for path, line in sorted(_declared_sites(dep) - _sites_by_dependency().get(dep, set())):
            stale.append(f"{dep}: {path}:{line} is declared but does not use it")

    assert stale == [], "stale declarations:\n  " + "\n  ".join(stale)
