from __future__ import annotations

from pathlib import Path

from scripts.check_optional_dependency_boundaries import check_boundaries


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _manifest_text(import_policy: str = "lazy_guard_required") -> str:
    return f"""
manifest_version: dependency_manifest.v0
repo: test
generated_from: test
status: repo_verified
classification_schema: [CORE_REQUIRED, OPTIONAL_ADAPTER, DEV_TEST_ONLY, LEGACY_DEPRECATED]
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
"""


def test_boundary_checker_flags_top_level_optional_import(tmp_path: Path) -> None:
    _write(tmp_path / ".aal/dependency_manifest.v0.yaml", _manifest_text())
    _write(tmp_path / "app/runtime.py", "import jinja2\n")
    violations = check_boundaries(
        manifest_path=tmp_path / ".aal/dependency_manifest.v0.yaml",
        root=tmp_path,
    )
    assert violations
    assert "app/runtime.py:1" in violations[0]


def test_boundary_checker_allows_guard_surface(tmp_path: Path) -> None:
    _write(tmp_path / ".aal/dependency_manifest.v0.yaml", _manifest_text())
    _write(tmp_path / "abx/optional_dependencies.py", "import jinja2\n")
    violations = check_boundaries(
        manifest_path=tmp_path / ".aal/dependency_manifest.v0.yaml",
        root=tmp_path,
    )
    assert violations == []


def test_boundary_checker_ignores_dev_test_only_imports(tmp_path: Path) -> None:
    _write(tmp_path / ".aal/dependency_manifest.v0.yaml", _manifest_text())
    _write(tmp_path / "tests/test_dummy.py", "import jinja2\n")
    violations = check_boundaries(
        manifest_path=tmp_path / ".aal/dependency_manifest.v0.yaml",
        root=tmp_path,
    )
    assert violations == []
