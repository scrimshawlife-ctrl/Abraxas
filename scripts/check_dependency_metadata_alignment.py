from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any, Dict, Mapping, Set, Tuple

try:
    import tomllib  # py311+
except ModuleNotFoundError:  # pragma: no cover
    try:
        from pip._vendor import tomli as tomllib  # type: ignore
    except ModuleNotFoundError:  # pragma: no cover
        tomllib = None  # type: ignore[assignment]

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PYPROJECT = ROOT / "pyproject.toml"
DEFAULT_MANIFEST = ROOT / ".aal" / "dependency_manifest.v0.yaml"


NAME_ALIASES = {"psycopg2_binary": "psycopg2", "python_multipart": "multipart"}


def _canonical(name: str) -> str:
    return NAME_ALIASES.get(name, name)


def _load_pyproject(path: Path) -> Mapping[str, Any]:
    if tomllib is not None:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    raise RuntimeError("tomllib/tomli parser unavailable for pyproject parsing")


def _load_manifest(path: Path) -> Mapping[str, Any]:
    try:
        import yaml  # type: ignore
    except ModuleNotFoundError:  # pragma: no cover
        import sys

        vendored = ROOT / "vendor" / "pyyaml"
        if vendored.exists():
            sys.path.insert(0, str(vendored))
        import yaml  # type: ignore

    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("manifest must be a mapping")
    return payload


def _normalize_dependency_name(spec: str) -> str:
    token = spec.split(";", 1)[0].strip()
    token = re.split(r"[<>=!~\\[]", token)[0]
    return _canonical(token.strip().replace("-", "_").lower())


def _collect_declared_deps(pyproject: Mapping[str, Any]) -> Tuple[Set[str], Dict[str, Set[str]]]:
    project = pyproject.get("project", {})
    if not isinstance(project, Mapping):
        raise ValueError("project table missing or invalid")

    core = {
        _normalize_dependency_name(str(row))
        for row in project.get("dependencies", [])
        if isinstance(row, str)
    }
    optional: Dict[str, Set[str]] = {}
    for group_name, rows in project.get("optional-dependencies", {}).items():
        if not isinstance(group_name, str) or not isinstance(rows, list):
            continue
        optional[group_name] = {
            _normalize_dependency_name(str(row))
            for row in rows
            if isinstance(row, str)
        }
    return core, optional


def _collect_manifest_deps(manifest: Mapping[str, Any]) -> Dict[str, str]:
    deps = manifest.get("dependencies", {})
    if not isinstance(deps, Mapping):
        raise ValueError("manifest dependencies missing or invalid")
    out: Dict[str, str] = {}
    for name, row in deps.items():
        if not isinstance(name, str) or not isinstance(row, Mapping):
            continue
        out[_normalize_dependency_name(name)] = str(row.get("class", "UNKNOWN"))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare dependency manifest entries with packaging declarations")
    parser.add_argument("--pyproject", type=Path, default=DEFAULT_PYPROJECT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()

    pyproject = _load_pyproject(args.pyproject)
    manifest = _load_manifest(args.manifest)

    core, optional = _collect_declared_deps(pyproject)
    all_declared = set(core)
    for rows in optional.values():
        all_declared.update(rows)

    # local/self package refs in extras (e.g. "abraxas[server,dev]") are not third-party dependencies
    all_declared.discard("abraxas")

    manifest_deps = _collect_manifest_deps(manifest)
    manifest_names = set(manifest_deps)

    declared_only = sorted(all_declared - manifest_names)
    manifest_only = sorted(manifest_names - all_declared)

    core_required_manifest = sorted(name for name, klass in manifest_deps.items() if klass == "CORE_REQUIRED")
    optional_manifest = sorted(name for name, klass in manifest_deps.items() if klass == "OPTIONAL_ADAPTER")

    missing_core_declarations = [name for name in core_required_manifest if name not in core]
    missing_optional_declarations = [name for name in optional_manifest if name not in all_declared]

    print("dependency-metadata-alignment: REPORT")
    print(f"- declared_only_count={len(declared_only)}")
    print(f"- manifest_only_count={len(manifest_only)}")
    print(f"- missing_core_declarations_count={len(missing_core_declarations)}")
    print(f"- missing_optional_declarations_count={len(missing_optional_declarations)}")

    print("declared_only:")
    for name in declared_only:
        print(f"  - {name}")

    print("manifest_only:")
    for name in manifest_only:
        print(f"  - {name}")

    print("missing_core_declarations:")
    for name in missing_core_declarations:
        print(f"  - {name}")

    print("missing_optional_declarations:")
    for name in missing_optional_declarations:
        print(f"  - {name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
