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
