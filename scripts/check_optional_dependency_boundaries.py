from __future__ import annotations

import argparse
import ast
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / ".aal" / "dependency_manifest.v0.yaml"
APPROVED_GUARD_FILES = {
    "abx/optional_dependencies.py",
    "abx/optional_jinja2.py",
}
EXCLUDE_PARTS = {".git", ".venv", "node_modules", "__pycache__", "build", "dist", ".pytest_cache", ".mypy_cache"}

try:
    import yaml  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - environment-dependent bootstrap
    import sys

    vendored = ROOT / "vendor" / "pyyaml"
    if vendored.exists():
        sys.path.insert(0, str(vendored))
    import yaml  # type: ignore


def _load_manifest(path: Path) -> Mapping[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("manifest must be a mapping")
    if payload.get("manifest_version") != "dependency_manifest.v0":
        raise ValueError("manifest_version must be dependency_manifest.v0")
    deps = payload.get("dependencies")
    if not isinstance(deps, Mapping):
        raise ValueError("dependencies must be a mapping")
    for name, row in deps.items():
        if not isinstance(row, Mapping):
            raise ValueError(f"dependency {name} row must be a mapping")
        for key in ("class", "import_policy", "fallback_policy", "allowed_to_affect_truth", "import_locations"):
            if key not in row:
                raise ValueError(f"dependency {name} missing required field: {key}")
    return payload


def _iter_python_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*.py"):
        rel = path.relative_to(root)
        if any(part in EXCLUDE_PARTS for part in rel.parts):
            continue
        yield rel


def _top_level_import_roots(tree: ast.AST) -> List[Tuple[int, str]]:
    rows: List[Tuple[int, str]] = []
    for node in getattr(tree, "body", []):
        if isinstance(node, ast.Import):
            for alias in node.names:
                rows.append((node.lineno, alias.name.split(".")[0]))
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                rows.append((node.lineno, node.module.split(".")[0]))
    return rows


def _manifest_optional_deps(manifest: Mapping[str, Any]) -> Tuple[Set[str], Set[str]]:
    deps = manifest.get("dependencies", {})
    optional: Set[str] = set()
    entrypoint_only: Set[str] = set()
    for name, row in deps.items():
        if not isinstance(row, Mapping):
            continue
        if row.get("class") == "OPTIONAL_ADAPTER":
            optional.add(str(name))
            if row.get("import_policy") == "entrypoint_only":
                entrypoint_only.add(str(name))
    return optional, entrypoint_only


def _is_approved_surface(rel_path: str) -> bool:
    if rel_path in APPROVED_GUARD_FILES:
        return True
    if rel_path.startswith("tests/"):
        return True
    return False


def check_boundaries(manifest_path: Path = DEFAULT_MANIFEST, root: Path = ROOT) -> List[str]:
    manifest = _load_manifest(manifest_path)
    optional_deps, entrypoint_only = _manifest_optional_deps(manifest)
    violations: List[str] = []
    seen_optional: Set[str] = set()
    for rel in _iter_python_files(root):
        path = root / rel
        rel_str = str(rel)
        try:
            source = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for lineno, dep_root in _top_level_import_roots(tree):
            if dep_root not in optional_deps:
                continue
            seen_optional.add(dep_root)
            if _is_approved_surface(rel_str):
                continue
            if dep_root in entrypoint_only and (
                rel_str.endswith("/run.py")
                or rel_str.endswith("_cli.py")
                or "/cli/" in rel_str
                or rel_str.startswith("scripts/")
                or rel_str == "abx/cli.py"
            ):
                continue
            violations.append(
                f"{rel_str}:{lineno}: top-level optional dependency import '{dep_root}' requires lazy guard"
            )

    undeclared: List[str] = []
    deps = manifest.get("dependencies", {})
    for dep in optional_deps:
        if dep not in deps:
            undeclared.append(dep)
    for dep in undeclared:
        violations.append(f"manifest optional dependency not declared correctly: {dep}")
    return violations


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check optional dependency boundary policy.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    violations = check_boundaries(manifest_path=args.manifest, root=args.root)
    if violations:
        print("optional-dependency-boundary-check: FAIL")
        for row in violations:
            print(f"- {row}")
        return 1
    print("optional-dependency-boundary-check: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
