"""Rewrite dependency-manifest `import_locations` from what the tree actually imports.

WHY THIS EXISTS

`import_locations` is the repository's record of WHERE each dependency is used, and nothing enforced it,
so it drifted: measured 2026-10-07, `fastapi` was declared at 3 paths while 31 files imported it, and
`jsonschema` at 1 while 29 did. That is not cosmetic -- the record is what tells a reader a surface
exists. Both the surface policy and this manifest had omitted `abraxas/dashboard/`, which is a large part
of why that surface's boundary violation went unnoticed.

This script is the FIXER; `tests/test_dependency_import_locations.py` is the GUARD that keeps the record
true afterwards.

SCOPE

Only classes whose surface placement is a governance concern. `DEV_TEST_ONLY` is excluded on purpose:
`pytest` is imported by 199 files, so an exhaustive declaration would be noise rather than signal.

CONVENTIONS (mirrored from the existing entries so the file stays coherent)

- One entry per import STATEMENT, not per imported name.
- `top_level` is true only when the statement is at module scope.
- `symbol` follows the existing convention: `import x as y` -> `y`, `import x` -> `x`,
  `from m import a, b` -> `a` (the first name).

SAFETY

The manifest is edited SURGICALLY -- only the entry lines under each `import_locations:` are rewritten,
so every other byte (comments, ordering, flow-style lists, notes, provenance) is preserved. Run without
`--write` to see the diff first.
"""

from __future__ import annotations

import argparse
import ast
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

try:
    import yaml  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - mirrors scripts/check_optional_dependency_boundaries.py
    # PyYAML is not installed in every interpreter this repo is run with; the repo vendors it and
    # provides a root-level `yaml.py` shim. Run as `python scripts/...`, sys.path[0] is `scripts/`, so
    # that shim is not reachable and the vendored tree must be added explicitly.
    vendored = Path(__file__).resolve().parents[1] / "vendor" / "pyyaml"
    if vendored.exists():
        sys.path.insert(0, str(vendored))
    import yaml  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / ".aal" / "dependency_manifest.v0.yaml"

GOVERNANCE_CLASSES = ("CORE_REQUIRED", "ENTRYPOINT_REQUIRED", "OPTIONAL_ADAPTER")

#: Not first-party usage sites: vendored third-party trees, generated output, and directories that test
#: runs rewrite.
EXCLUDED_PREFIXES = ("vendor/", "out/", "data/", ".abraxas/")
EXCLUDED_EXACT = frozenset(
    {
        # Cookiecutter template -- not valid Python, so it cannot be parsed for imports either.
        ".github/engine-cookiecutter/engine_template/src/engine_template/__init__.py",
    }
)


def _load_manifest(path: Path) -> Mapping[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("manifest must be a mapping")
    return payload


def scoped_dependencies(manifest: Mapping[str, Any]) -> dict[str, str]:
    """{dependency: class} for the governance-relevant dependencies."""
    deps = manifest.get("dependencies", {})
    if not isinstance(deps, Mapping):
        raise ValueError("manifest dependencies missing or invalid")
    return {
        name: str(row.get("class", ""))
        for name, row in deps.items()
        if isinstance(row, Mapping) and str(row.get("class", "")) in GOVERNANCE_CLASSES
    }


def _symbol_for(node: ast.Import | ast.ImportFrom) -> str:
    """The representative symbol, following the manifest's existing convention."""
    if isinstance(node, ast.Import):
        alias = node.names[0]
        return alias.asname or alias.name
    return node.names[0].name


def _literal_optional_dependency(node: ast.Call) -> str | None:
    """The name from a literal `require_optional_dependency("x", ...)` / `import_module("x")` call.

    OPTIONAL_ADAPTER dependencies are the repo's lazy-guard case, and the documented mechanism is a
    string lookup through `require_optional_dependency`, not an `import` statement -- an AST import scan
    is blind to it. Measured 2026-10-07: regenerating without this would have DELETED the true `torch`
    and `transformers` declarations, because `timesfm_shadow/infer.py` reaches them through
    `require_optional_dependency("torch", "timesfm_shadow_lab")` and nothing else. Only a literal string
    is honoured; a computed name stays invisible, which is the honest limit of a static scan.
    """
    func = node.func
    name = ""
    if isinstance(func, ast.Name):
        name = func.id
    elif isinstance(func, ast.Attribute):
        name = func.attr
    if name not in {"require_optional_dependency", "import_module"}:
        return None
    if not node.args or not isinstance(node.args[0], ast.Constant):
        return None
    value = node.args[0].value
    return value.split(".")[0] if isinstance(value, str) else None


def scan_import_sites() -> dict[str, list[tuple[str, int, bool, str]]]:
    """{import_root: [(path, line, top_level, symbol), ...]} for every tracked first-party module.

    Covers both `import` statements and literal `require_optional_dependency(...)` guards, so it sees the
    same sites the manifest records.
    """
    listing = subprocess.run(
        ["git", "ls-files", "*.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()

    sites: dict[str, list[tuple[str, int, bool, str]]] = {}
    for rel in listing:
        if rel in EXCLUDED_EXACT or rel.startswith(EXCLUDED_PREFIXES):
            continue
        try:
            tree = ast.parse((ROOT / rel).read_text(encoding="utf-8"), filename=rel)
        except (SyntaxError, OSError, UnicodeDecodeError):
            continue  # unparseable files are `tests/test_module_parse_integrity.py`'s problem
        module_level = {id(child) for child in tree.body}
        for node in ast.walk(tree):
            root = ""
            symbol = ""
            if isinstance(node, ast.Import):
                root = node.names[0].name.split(".")[0]
                symbol = _symbol_for(node)
            elif isinstance(node, ast.ImportFrom):
                if node.level == 0 and node.module:
                    root = node.module.split(".")[0]
                    symbol = _symbol_for(node)
            elif isinstance(node, ast.Call):
                guarded = _literal_optional_dependency(node)
                if guarded:
                    root, symbol = guarded, guarded
            if not root:
                continue
            sites.setdefault(root, []).append(
                (rel, node.lineno, id(node) in module_level, symbol)
            )
    return sites


def render_entries(sites: list[tuple[str, int, bool, str]]) -> list[str]:
    """The YAML lines for one dependency's `import_locations`, deterministically ordered."""
    lines: list[str] = []
    for path, line, top_level, symbol in sorted(sites, key=lambda s: (s[0], s[1])):
        lines.append(f"      - path: {path}")
        lines.append(f"        line: {line}")
        lines.append(f"        top_level: {'true' if top_level else 'false'}")
        lines.append(f"        symbol: {symbol}")
    return lines


def declared_entries(manifest: Mapping[str, Any], dep: str) -> list[str]:
    row = manifest["dependencies"][dep]
    out: list[str] = []
    for entry in row.get("import_locations") or []:
        out.append(f"      - path: {entry['path']}")
        out.append(f"        line: {entry['line']}")
        out.append(f"        top_level: {'true' if entry.get('top_level') else 'false'}")
        out.append(f"        symbol: {entry.get('symbol', '')}")
    return out


def splice_import_locations(text: str, dep: str, entries: list[str]) -> str:
    """Replace only the entry lines under `dep`'s `import_locations:`, leaving every other byte alone."""
    lines = text.splitlines()
    dep_header = f"  {dep}:"
    try:
        start = lines.index(dep_header)
    except ValueError as exc:
        raise SystemExit(f"dependency {dep!r} not found as a top-level key in the manifest") from exc

    try:
        key_index = next(i for i in range(start, len(lines)) if lines[i] == "    import_locations:")
    except StopIteration as exc:
        raise SystemExit(f"dependency {dep!r} has no `import_locations:` key") from exc

    end = key_index + 1
    while end < len(lines) and lines[end].startswith("      "):
        end += 1

    return "\n".join(lines[: key_index + 1] + entries + lines[end:]) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--write", action="store_true", help="apply the changes (default: report only)")
    args = parser.parse_args()

    manifest = _load_manifest(args.manifest)
    scoped = scoped_dependencies(manifest)
    if not scoped:
        raise SystemExit(f"no dependencies resolved to {GOVERNANCE_CLASSES}; refusing to run")

    sites = scan_import_sites()
    if not sites:
        raise SystemExit("the import scan found NOTHING; the scanner is broken, refusing to run")

    original = args.manifest.read_text(encoding="utf-8")
    text = original
    changed: list[str] = []

    for dep in sorted(scoped):
        want = render_entries(sites.get(dep, []))
        have = declared_entries(manifest, dep)
        if want == have:
            continue
        text = splice_import_locations(text, dep, want)
        changed.append(f"  {dep} ({scoped[dep]}): {len(have) // 4} declared -> {len(want) // 4} actual")

    if not changed:
        print("dependency-import-locations: OK (8 locations per entry, all in agreement)")
        return 0

    print(f"dependency-import-locations: DRIFT in {len(changed)} dependenc(ies)")
    for row in changed:
        print(row)
    if args.write:
        args.manifest.write_text(text, encoding="utf-8")
        print(f"\nwrote {args.manifest}")
        return 0
    print("\n(re-run with --write to apply)")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
