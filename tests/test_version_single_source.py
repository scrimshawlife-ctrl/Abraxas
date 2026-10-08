"""Pins the four version declarations to each other so they cannot drift apart again.

WHY THIS EXISTS
    The project version was declared in four places and they all disagreed:

        pyproject.toml              version = "1.5.0"
        .abraxas/gates.json         CANON_VERSION = "v2.0.1"   <- canon authority
        README.md badge             status-live · v2.0.1
        CHANGELOG.md milestone      [v2.0.0] - 2026-10-04 (most recent RELEASED)

    Nothing reconciled them, so no single answer existed to the question "what version is this?".
    The README additionally declared "PRODUCTION READY" while the package classifier said
    Development Status :: 3 - Alpha.

    Canon is the authority: .abraxas/gates.json. pyproject is the packaging source of truth and
    now agrees with it, and abraxas.__version__ reads back from the installed distribution so a
    second hardcoded copy cannot appear. This test is what stops the drift recurring -- the
    defect was never a wrong number, it was that no instrument compared the numbers.
"""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = REPO_ROOT / "pyproject.toml"
GATES = REPO_ROOT / ".abraxas" / "gates.json"
README = REPO_ROOT / "README.md"


def _pyproject_version() -> str:
    with PYPROJECT.open("rb") as fh:
        return tomllib.load(fh)["project"]["version"]


def _canon_version() -> str:
    """Canon authority, from the tracked `.abraxas/gates.json`.

    CANON_VERSION is nested under the file's top-level `gates` object -- reading it off the root
    raises KeyError, which is how this test first failed. Located rather than assumed, so a
    reorganisation of that file reports itself instead of silently reading nothing.
    """
    data = json.loads(GATES.read_text(encoding="utf-8"))
    node = data.get("gates", data)
    if "CANON_VERSION" not in node:
        pytest.fail(
            f"CANON_VERSION not found in {GATES} (top-level keys: {sorted(node)[:12]}). It is the "
            f"canon authority for the version -- if it moved, update this lookup rather than "
            f"dropping the check."
        )
    return node["CANON_VERSION"]


def _readme_badge_version() -> str:
    """The version in the status badge, the README's own claim about the release."""
    text = README.read_text(encoding="utf-8")
    match = re.search(r"badge/status-[^\s\"]*?(v\d+\.\d+\.\d+)", text)
    if not match:
        pytest.fail(
            "no status badge version found in README.md -- if the badge moved or changed shape, "
            "update this pattern rather than deleting the check"
        )
    return match.group(1)


def test_declared_versions_agree() -> None:
    canon = _canon_version()
    package = _pyproject_version()
    badge = _readme_badge_version()

    assert canon.lstrip("v") == package, (
        f"canon and packaging disagree: .abraxas/gates.json CANON_VERSION={canon!r} but "
        f"pyproject.toml version={package!r}. Canon is the authority -- change pyproject to match "
        f"it, not the other way round."
    )
    assert badge.lstrip("v") == package, (
        f"README badge and packaging disagree: README says {badge!r} but pyproject says "
        f"{package!r}."
    )


def test_package_version_reads_back_from_the_declared_source() -> None:
    """abraxas.__version__ must report the declared version, not a second hardcoded literal."""
    import abraxas

    declared = _pyproject_version()
    if abraxas.__version__ == "0.0.0+unknown":
        pytest.skip("abraxas is not installed as a distribution; nothing to compare")

    assert abraxas.__version__ == declared, (
        f"abraxas.__version__ is {abraxas.__version__!r} but pyproject declares {declared!r}. If "
        f"you just changed the version, the local editable install's metadata is stale: run "
        f"`pip install -e .` (or `pip install -e \".[dev]\"`) to refresh it."
    )


def test_the_development_status_classifier_is_not_a_production_claim() -> None:
    """The classifier must not out-claim the repo's own maturity statement.

    README currently declares the honest position in its Maturity Matrix (release packaging
    "Planned / evolving"). A production classifier while that is true is the same defect this
    suite spent the session removing: a label reporting something the repo contradicts.
    """
    with PYPROJECT.open("rb") as fh:
        classifiers = tomllib.load(fh)["project"].get("classifiers", [])

    status = [c for c in classifiers if c.startswith("Development Status")]
    assert status, "no Development Status classifier -- packaging makes no maturity claim at all"
    assert not any("Production/Stable" in c for c in status), (
        f"packaging claims {status} while the README's Maturity Matrix still lists release "
        f"packaging as 'Planned / evolving'. Move the classifier when the state changes, not "
        f"before."
    )
