from __future__ import annotations

from pathlib import Path

from scripts.check_optional_dependency_boundaries import check_boundaries_with_report


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _manifest_text(import_policy: str = "lazy_guard_required") -> str:
    return f"""
manifest_version: dependency_manifest.v0
repo: test
generated_from: test
status: repo_verified
classification_schema: [CORE_REQUIRED, ENTRYPOINT_REQUIRED, OPTIONAL_ADAPTER, DEV_TEST_ONLY, LEGACY_DEPRECATED]
dependencies:
  jinja2:
    class: OPTIONAL_ADAPTER
    authority_scope: [presentation]
    import_policy: {import_policy}
    fallback_policy: execution_time_error
    allowed_to_affect_truth: false
    import_locations:
      - path: app/runtime.py
        line: 1
        top_level: true
        symbol: Environment
  fastapi:
    class: ENTRYPOINT_REQUIRED
    authority_scope: [entrypoint, api]
    import_policy: entrypoint_only
    fallback_policy: launch_blocked_surface_only
    allowed_to_affect_truth: false
    required_for_launch: true
    truth_authoritative: false
    execution_boundary_role: api
    import_locations:
      - path: webpanel/app.py
        line: 1
        top_level: true
        symbol: FastAPI
"""


def _policy_text(*, allow_fallback_heuristic: bool = False) -> str:
    enabled = "true" if allow_fallback_heuristic else "false"
    return f"""
policy_version: dependency_surface_policy.v0
repo: test
allow_fallback_heuristic: {enabled}
roles: [truth_authoritative, launch_surface, optional_adapter_surface, test_only, legacy]
path_role_map:
  - prefix: tests/
    role: test_only
  - prefix: abx/optional_dependencies.py
    role: optional_adapter_surface
  - prefix: adapters/
    role: optional_adapter_surface
  - prefix: launch/
    role: launch_surface
  - prefix: truth/
    role: truth_authoritative
"""


def test_boundary_checker_flags_top_level_optional_import(tmp_path: Path) -> None:
    _write(tmp_path / ".aal/dependency_manifest.v0.yaml", _manifest_text())
    _write(tmp_path / ".aal/dependency_surface_policy.v0.yaml", _policy_text())
    _write(tmp_path / "app/runtime.py", "import jinja2\n")
    violations, _warnings = check_boundaries_with_report(
        manifest_path=tmp_path / ".aal/dependency_manifest.v0.yaml",
        policy_path=tmp_path / ".aal/dependency_surface_policy.v0.yaml",
        root=tmp_path,
    )
    assert violations
    assert "app/runtime.py:1" in violations[0]


def test_boundary_checker_allows_guard_surface(tmp_path: Path) -> None:
    _write(tmp_path / ".aal/dependency_manifest.v0.yaml", _manifest_text())
    _write(tmp_path / ".aal/dependency_surface_policy.v0.yaml", _policy_text())
    _write(tmp_path / "abx/optional_dependencies.py", "import jinja2\n")
    violations, _warnings = check_boundaries_with_report(
        manifest_path=tmp_path / ".aal/dependency_manifest.v0.yaml",
        policy_path=tmp_path / ".aal/dependency_surface_policy.v0.yaml",
        root=tmp_path,
    )
    assert violations == []


def test_boundary_checker_ignores_dev_test_only_imports(tmp_path: Path) -> None:
    _write(tmp_path / ".aal/dependency_manifest.v0.yaml", _manifest_text())
    _write(tmp_path / ".aal/dependency_surface_policy.v0.yaml", _policy_text())
    _write(tmp_path / "tests/test_dummy.py", "import jinja2\n")
    violations, _warnings = check_boundaries_with_report(
        manifest_path=tmp_path / ".aal/dependency_manifest.v0.yaml",
        policy_path=tmp_path / ".aal/dependency_surface_policy.v0.yaml",
        root=tmp_path,
    )
    assert violations == []


def test_boundary_checker_allows_entrypoint_dependency_in_launch_surface(tmp_path: Path) -> None:
    _write(tmp_path / ".aal/dependency_manifest.v0.yaml", _manifest_text())
    _write(tmp_path / ".aal/dependency_surface_policy.v0.yaml", _policy_text())
    _write(tmp_path / "launch/app.py", "from fastapi import FastAPI\n")
    violations, _warnings = check_boundaries_with_report(
        manifest_path=tmp_path / ".aal/dependency_manifest.v0.yaml",
        policy_path=tmp_path / ".aal/dependency_surface_policy.v0.yaml",
        root=tmp_path,
    )
    assert violations == []


def test_boundary_checker_rejects_entrypoint_dependency_in_truth_surface(tmp_path: Path) -> None:
    _write(tmp_path / ".aal/dependency_manifest.v0.yaml", _manifest_text())
    _write(tmp_path / ".aal/dependency_surface_policy.v0.yaml", _policy_text())
    _write(tmp_path / "truth/runtime_truth.py", "from fastapi import FastAPI\n")
    violations, _warnings = check_boundaries_with_report(
        manifest_path=tmp_path / ".aal/dependency_manifest.v0.yaml",
        policy_path=tmp_path / ".aal/dependency_surface_policy.v0.yaml",
        root=tmp_path,
    )
    assert violations
    assert "forbidden in truth-authoritative surface" in violations[0]


def test_boundary_checker_allows_optional_adapter_in_adapter_surface(tmp_path: Path) -> None:
    _write(tmp_path / ".aal/dependency_manifest.v0.yaml", _manifest_text())
    _write(tmp_path / ".aal/dependency_surface_policy.v0.yaml", _policy_text())
    _write(tmp_path / "adapters/render_adapter.py", "import jinja2\n")
    violations, _warnings = check_boundaries_with_report(
        manifest_path=tmp_path / ".aal/dependency_manifest.v0.yaml",
        policy_path=tmp_path / ".aal/dependency_surface_policy.v0.yaml",
        root=tmp_path,
    )
    assert violations == []


def test_boundary_checker_fails_unclassified_surface_when_fallback_disabled(tmp_path: Path) -> None:
    _write(tmp_path / ".aal/dependency_manifest.v0.yaml", _manifest_text())
    _write(tmp_path / ".aal/dependency_surface_policy.v0.yaml", _policy_text(allow_fallback_heuristic=False))
    _write(tmp_path / "unmapped/module.py", "from fastapi import FastAPI\n")
    violations, warnings = check_boundaries_with_report(
        manifest_path=tmp_path / ".aal/dependency_manifest.v0.yaml",
        policy_path=tmp_path / ".aal/dependency_surface_policy.v0.yaml",
        root=tmp_path,
        allow_fallback=False,
    )
    assert violations
    assert "unclassified" in violations[0]
    assert warnings == []


# --------------------------------------------------------------------------------------
# The real repository's declarations.
#
# The tests above use synthetic fixtures to exercise the checker's logic. The three below
# deliberately point at the REAL `.aal/` files, so they fail if this repository's actual
# surface classifications drift from reality -- which is exactly how the dashboard went
# unnoticed: it was never classified at all, so it silently inherited the `abraxas/`
# catch-all (truth_authoritative) and its `fastapi` imports were flagged.
# --------------------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[1]
REAL_MANIFEST = REPO_ROOT / ".aal" / "dependency_manifest.v0.yaml"
REAL_POLICY = REPO_ROOT / ".aal" / "dependency_surface_policy.v0.yaml"


def test_dashboard_entrypoint_is_a_launch_surface(tmp_path: Path) -> None:
    """`abraxas/dashboard/api.py` is an entrypoint service, so it may import `fastapi`.

    Evidence: `Dockerfile.dashboard-api` launches it (`CMD ["python", "api.py"]`) and it is
    read/serve only (8 GET routes, one telemetry POST, no INSERT/UPDATE/DELETE, no file writes).
    RED before the policy entry exists: the path inherits the `abraxas/` catch-all, so its three
    `fastapi` imports are reported as forbidden in a truth-authoritative surface.
    """
    _write(tmp_path / "abraxas/dashboard/api.py", "from fastapi import FastAPI\n")
    violations, _warnings = check_boundaries_with_report(
        manifest_path=REAL_MANIFEST,
        policy_path=REAL_POLICY,
        root=tmp_path,
    )
    assert violations == [], violations


def test_dashboard_exemption_is_file_scoped_not_directory_scoped(tmp_path: Path) -> None:
    """The launch-surface entry is scoped to the entrypoint FILE, not to `abraxas/dashboard/`.

    This is the guard that keeps the exemption narrow: a sibling module in the same directory is
    still truth-authoritative, so truth computation added there later cannot silently inherit the
    entrypoint's exemption. This test PASSES before the change and must still pass after it --
    if it ever fails, someone has widened the entry to the whole directory and un-done the point.
    """
    _write(tmp_path / "abraxas/dashboard/truth_helper.py", "from fastapi import FastAPI\n")
    violations, _warnings = check_boundaries_with_report(
        manifest_path=REAL_MANIFEST,
        policy_path=REAL_POLICY,
        root=tmp_path,
    )
    assert violations, "the launch-surface exemption leaked to the whole directory"
    assert "forbidden in truth-authoritative surface" in violations[0]


def test_unparseable_file_is_reported_not_silently_skipped(tmp_path: Path) -> None:
    """A file that does not parse cannot be scanned, so SAY SO instead of skipping it silently.

    Silent skipping is indistinguishable from a clean result. Measured 2026-10-07: a tracked module with
    a syntax error (`abx/media_origin_verify.py`) was invisible to this checker, so its imports would
    never have been boundary-checked no matter what it imported.

    It is a WARNING rather than a violation because two tracked files are legitimately unparseable (a
    cookiecutter template and a generated `.abraxas/` script) and failing on those would break the
    check. Real defects here are the parse guard's job: tests/test_module_parse_integrity.py.
    """
    _write(tmp_path / ".aal/dependency_manifest.v0.yaml", _manifest_text())
    _write(tmp_path / ".aal/dependency_surface_policy.v0.yaml", _policy_text())
    _write(tmp_path / "launch/broken.py", "from fastapi import FastAPI\nthis is not python(\n")

    violations, warnings = check_boundaries_with_report(
        manifest_path=tmp_path / ".aal/dependency_manifest.v0.yaml",
        policy_path=tmp_path / ".aal/dependency_surface_policy.v0.yaml",
        root=tmp_path,
    )

    assert violations == [], violations
    assert any("does not parse" in row for row in warnings), (
        f"the unparseable file was skipped silently; warnings were {warnings}"
    )


def test_real_repo_passes_the_dependency_boundary_check() -> None:
    """The CI step `python scripts/check_optional_dependency_boundaries.py` must exit 0 here.

    Scans the actual working tree. This is the acceptance criterion of the whole change, asserted
    where the suite will see it rather than only in CI.
    """
    violations, _warnings = check_boundaries_with_report(root=REPO_ROOT)
    assert violations == [], violations
