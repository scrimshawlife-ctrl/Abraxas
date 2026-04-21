from __future__ import annotations

import argparse
import ast
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / ".aal" / "dependency_manifest.v0.yaml"
DEFAULT_POLICY = ROOT / ".aal" / "dependency_surface_policy.v0.yaml"
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
        dep_class = str(row.get("class", ""))
        if dep_class == "ENTRYPOINT_REQUIRED":
            for key in ("required_for_launch", "truth_authoritative", "execution_boundary_role"):
                if key not in row:
                    raise ValueError(f"entrypoint dependency {name} missing required field: {key}")
    return payload


def _load_surface_policy(path: Path) -> Mapping[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("surface policy must be a mapping")
    if payload.get("policy_version") != "dependency_surface_policy.v0":
        raise ValueError("policy_version must be dependency_surface_policy.v0")
    mappings = payload.get("path_role_map")
    if not isinstance(mappings, list) or not mappings:
        raise ValueError("path_role_map must be a non-empty list")
    for row in mappings:
        if not isinstance(row, Mapping):
            raise ValueError("path_role_map entries must be mappings")
        if "prefix" not in row or "role" not in row:
            raise ValueError("path_role_map entries require prefix and role")
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


def _manifest_dependency_sets(manifest: Mapping[str, Any]) -> Tuple[Set[str], Set[str], Set[str]]:
    deps = manifest.get("dependencies", {})
    optional: Set[str] = set()
    entrypoint: Set[str] = set()
    entrypoint_only: Set[str] = set()
    for name, row in deps.items():
        if not isinstance(row, Mapping):
            continue
        dep_class = row.get("class")
        if dep_class == "OPTIONAL_ADAPTER":
            optional.add(str(name))
        if dep_class == "ENTRYPOINT_REQUIRED":
            entrypoint.add(str(name))
        if row.get("import_policy") == "entrypoint_only":
            entrypoint_only.add(str(name))
    return optional, entrypoint, entrypoint_only


def _fallback_role(rel_path: str) -> str | None:
    if rel_path.startswith("tests/"):
        return "test_only"
    if rel_path in APPROVED_GUARD_FILES:
        return "optional_adapter_surface"
    if (
        rel_path.endswith("/run.py")
        or rel_path.endswith("_cli.py")
        or "/cli/" in rel_path
        or "/api/" in rel_path
        or rel_path.endswith("/api.py")
        or rel_path.endswith("/app.py")
        or rel_path.startswith("webpanel/")
        or rel_path.startswith("server/")
        or rel_path.startswith("abraxas/web/")
        or rel_path.startswith("abraxas/lens/")
        or rel_path.startswith("tools/aatf/aatf/")
        or rel_path.startswith("scripts/")
        or rel_path in {"abx/cli.py", "abx/ui/server.py"}
    ):
        return "launch_surface"
    if (
        rel_path.startswith("abraxas/core/")
        or rel_path.startswith("abx/core/")
        or rel_path.startswith("abx/runtime/")
        or rel_path.startswith("shared/")
    ):
        return "truth_authoritative"
    return None


def _classify_surface_role(
    *,
    rel_path: str,
    policy: Mapping[str, Any],
    fallback_enabled: bool,
) -> Tuple[str | None, bool]:
    if rel_path in APPROVED_GUARD_FILES:
        return "optional_adapter_surface", False
    mappings = policy.get("path_role_map", [])
    matching_rows = [
        row for row in mappings
        if isinstance(row, Mapping)
        and isinstance(row.get("prefix"), str)
        and rel_path.startswith(str(row["prefix"]))
    ]
    if matching_rows:
        winner = max(matching_rows, key=lambda row: len(str(row["prefix"])))
        return str(winner["role"]), False
    if not fallback_enabled:
        return None, False
    fallback = _fallback_role(rel_path)
    if fallback is None:
        return None, False
    return fallback, True


def check_boundaries_with_report(
    *,
    manifest_path: Path = DEFAULT_MANIFEST,
    policy_path: Path = DEFAULT_POLICY,
    root: Path = ROOT,
    allow_fallback: bool | None = None,
) -> Tuple[List[str], List[str]]:
    manifest = _load_manifest(manifest_path)
    policy = _load_surface_policy(policy_path)
    fallback_enabled = bool(policy.get("allow_fallback_heuristic", False)) if allow_fallback is None else allow_fallback
    optional_deps, entrypoint_deps, entrypoint_only = _manifest_dependency_sets(manifest)
    violations: List[str] = []
    warnings: List[str] = []
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
        surface_role, used_fallback = _classify_surface_role(
            rel_path=rel_str,
            policy=policy,
            fallback_enabled=fallback_enabled,
        )
        if used_fallback:
            warnings.append(f"{rel_str}: used fallback heuristic surface-role resolution -> role={surface_role}")
        for lineno, dep_root in _top_level_import_roots(tree):
            if dep_root not in optional_deps and dep_root not in entrypoint_deps:
                continue
            if surface_role == "test_only":
                continue
            if surface_role is None:
                violations.append(
                    f"{rel_str}:{lineno}: module surface role is unclassified and fallback is disabled"
                )
                continue
            if dep_root in entrypoint_deps:
                if surface_role == "truth_authoritative":
                    violations.append(
                        f"{rel_str}:{lineno}: entrypoint dependency import '{dep_root}' is forbidden in truth-authoritative surface"
                    )
                    continue
                if surface_role in {"launch_surface", "legacy"}:
                    continue
                violations.append(
                    f"{rel_str}:{lineno}: entrypoint dependency import '{dep_root}' must remain in approved launch surfaces"
                )
                continue
            if surface_role in {"optional_adapter_surface", "test_only"}:
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
    for dep in optional_deps | entrypoint_deps:
        if dep not in deps:
            undeclared.append(dep)
    for dep in undeclared:
        violations.append(f"manifest optional dependency not declared correctly: {dep}")
    return violations, warnings


def check_boundaries(manifest_path: Path = DEFAULT_MANIFEST, root: Path = ROOT) -> List[str]:
    violations, _warnings = check_boundaries_with_report(
        manifest_path=manifest_path,
        root=root,
        policy_path=DEFAULT_POLICY,
    )
    return violations


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check optional dependency boundary policy.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--allow-fallback", action="store_true", help="Allow fallback heuristic when policy has no matching path.")
    args = parser.parse_args(argv)
    violations, warnings = check_boundaries_with_report(
        manifest_path=args.manifest,
        policy_path=args.policy,
        root=args.root,
        allow_fallback=args.allow_fallback,
    )
    if violations:
        print("optional-dependency-boundary-check: FAIL")
        for row in violations:
            print(f"- {row}")
        for row in warnings:
            print(f"! warning: {row}")
        return 1
    print("optional-dependency-boundary-check: PASS")
    for row in warnings:
        print(f"! warning: {row}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
