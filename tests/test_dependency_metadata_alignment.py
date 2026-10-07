"""The dependency-metadata check must FAIL on a real discrepancy, not merely print one.

Measured 2026-10-07: `scripts/check_dependency_metadata_alignment.py` detected an injected fault
(`manifest_only_count=1`, `missing_core_declarations_count=2`) and still exited **0**. It is a CI step
named "Dependency Metadata Check" that cannot fail, so its findings were printed into the log and
ignored. A check that reports a fault while reporting success is not a check.

The distinction that matters:

- `manifest_only` means the manifest names a dependency the project never declares -- the record is
  simply wrong.
- `missing_core_declarations` / `missing_optional_declarations` mean a manifest CLASS claims something
  packaging does not provide.
- `declared_only` is INFORMATIONAL and must NOT fail: a dependency declared in packaging but not
  classified for boundary purposes is normal (9 such dependencies exist on this repo today, and the
  check has been green throughout).

The last case is the control: a check that fails on everything is vacuously "safe" and enforces nothing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts import check_dependency_metadata_alignment as meta

PYPROJECT = """
[project]
name = "probe"
dependencies = ["requests"]

[project.optional-dependencies]
extra = ["declared_but_unclassified"]
"""


def _manifest_text(extra_dep: str = "", extra_class: str = "CORE_REQUIRED") -> str:
    return (
        "manifest_version: dependency_manifest.v0\n"
        "dependencies:\n"
        "  requests:\n"
        "    class: OPTIONAL_ADAPTER\n"
        "    import_policy: lazy_guard_required\n"
        "    fallback_policy: execution_time_error\n"
        "    allowed_to_affect_truth: false\n"
        "    import_locations: []\n"
        + (
            f"  {extra_dep}:\n"
            f"    class: {extra_class}\n"
            "    import_policy: normal\n"
            "    fallback_policy: hard_setup_failure\n"
            "    allowed_to_affect_truth: true\n"
            "    import_locations: []\n"
            if extra_dep
            else ""
        )
    )


def _run(tmp_path: Path, manifest_text: str, monkeypatch: pytest.MonkeyPatch) -> int:
    pyproject = tmp_path / "pyproject.toml"
    manifest = tmp_path / "manifest.yaml"
    pyproject.write_text(PYPROJECT, encoding="utf-8")
    manifest.write_text(manifest_text, encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv",
        ["check_dependency_metadata_alignment.py", "--pyproject", str(pyproject), "--manifest", str(manifest)],
    )
    return meta.main()


def test_a_manifest_only_dependency_fails_the_check(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The manifest names a dependency the project does not declare: the record is wrong."""
    rc = _run(tmp_path, _manifest_text(extra_dep="totally_fake_dependency"), monkeypatch)
    assert rc != 0, "a manifest-only dependency was reported but the check exited 0"


def test_a_missing_core_declaration_fails_the_check(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A CORE_REQUIRED dependency with no packaging declaration is a real fault."""
    text = _manifest_text(extra_dep="fake_core_dep", extra_class="CORE_REQUIRED")
    rc = _run(tmp_path, text, monkeypatch)
    assert rc != 0, "a CORE_REQUIRED dependency missing from packaging was reported but the check exited 0"


def test_declared_only_is_informational_and_does_not_fail(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CONTROL: packaging declares a dependency the manifest does not classify. That is normal.

    Without this case the gate could be satisfied by failing on any discrepancy at all, which would be
    vacuous -- and would break the check on this repo, where 9 such dependencies exist today.
    """
    rc = _run(tmp_path, _manifest_text(), monkeypatch)
    assert rc == 0, "an unclassified but declared dependency must not fail the check"


def test_the_real_repo_passes_the_check() -> None:
    """The live manifest and packaging must satisfy the invariants, asserted where the suite sees them."""
    monkeypatch_argv = ["check_dependency_metadata_alignment.py"]
    import sys

    original = sys.argv
    sys.argv = monkeypatch_argv
    try:
        assert meta.main() == 0
    finally:
        sys.argv = original
