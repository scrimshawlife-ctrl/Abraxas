"""
ABX-Rune Registry Primacy Gate v0.1.

Hard gate: fail when rune IDs exist in code but not in catalog.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment-specific dependency
    raise ImportError(
        "PyYAML required for rune registry gate. Install via: pip install pyyaml"
    ) from exc


CATALOG_GLOB = "runes/catalog*.yaml"
DISCOVERY_GLOB = "runes"


@dataclass(frozen=True)
class RuneCandidate:
    rune_id: str
    sources: List[str]


@dataclass(frozen=True)
class CandidateWithoutId:
    path: str
    reason: str


def run_gate(repo_root: Optional[Path] = None) -> Tuple[int, str]:
    repo_root = Path(repo_root) if repo_root else _default_repo_root()
    catalog_paths = _find_catalogs(repo_root)
    registered_ids, catalog_index, catalog_notes = _load_catalog_ids(
        catalog_paths, repo_root
    )

    discovered_ids, without_id, discovery_notes = _discover_rune_ids(repo_root)
    missing = sorted(discovered_ids.keys() - registered_ids)
    orphans = sorted(registered_ids - discovered_ids.keys())

    output = _format_report(
        repo_root=repo_root,
        catalog_paths=catalog_paths,
        registered_ids=registered_ids,
        discovered_ids=discovered_ids,
        missing=missing,
        orphans=orphans,
        without_id=without_id,
        discovery_notes=discovery_notes,
        catalog_index=catalog_index,
        catalog_notes=catalog_notes,
    )
    exit_code = 2 if missing else 0
    return exit_code, output


def _find_catalogs(repo_root: Path) -> List[Path]:
    paths = sorted(
        path for path in repo_root.rglob(CATALOG_GLOB) if path.is_file()
    )
    return paths


def _load_catalog_ids(
    catalog_paths: Sequence[Path],
    repo_root: Path,
) -> Tuple[Set[str], Dict[str, List[str]], List[str]]:
    rune_ids: Set[str] = set()
    catalog_index: Dict[str, List[str]] = {}
    notes: List[str] = []

    for path in catalog_paths:
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception as exc:
            notes.append(f"catalog unreadable: {_relative_path(path, repo_root)} ({exc})")
            continue
        runes = data.get("runes", [])
        if not isinstance(runes, list):
            notes.append(
                f"catalog runes list missing: {_relative_path(path, repo_root)}"
            )
            continue
        for entry in runes:
            if not isinstance(entry, dict):
                continue
            rune_id = entry.get("rune_id")
            if isinstance(rune_id, str) and rune_id.strip():
                rune_ids.add(rune_id)
                catalog_index.setdefault(rune_id, []).append(
                    _relative_path(path, repo_root)
                )
    notes = sorted(set(notes))
    return rune_ids, catalog_index, notes


def _discover_rune_ids(
    repo_root: Path,
) -> Tuple[Dict[str, RuneCandidate], List[CandidateWithoutId], List[str]]:
    rune_dirs = _find_rune_dirs(repo_root)
    discovered: Dict[str, RuneCandidate] = {}
    without_id: List[CandidateWithoutId] = []
    notes = [
        "rune_id discovery scans string literals in RUNE_ID assignments,",
        "dict keys named 'rune_id', and call keywords 'rune_id' only.",
        "files mentioning rune_id without literals are listed as candidates.",
    ]

    for rune_dir in rune_dirs:
        for path in sorted(rune_dir.rglob("*.py")):
            if _skip_path(path):
                continue
            relative = _relative_path(path, repo_root)
            try:
                text = path.read_text(encoding="utf-8")
            except Exception:
                without_id.append(
                    CandidateWithoutId(
                        path=relative, reason="unreadable python file"
                    )
                )
                continue

            mentions_rune_id = ("rune_id" in text) or ("RUNE_ID" in text)
            rune_ids = _extract_rune_ids_from_ast(text)

            if rune_ids:
                for rune_id in sorted(rune_ids):
                    entry = discovered.get(rune_id)
                    if entry is None:
                        discovered[rune_id] = RuneCandidate(
                            rune_id=rune_id, sources=[relative]
                        )
                    else:
                        entry.sources.append(relative)
            elif mentions_rune_id:
                without_id.append(
                    CandidateWithoutId(
                        path=relative, reason="rune_id literal not found"
                    )
                )

    for candidate in discovered.values():
        candidate.sources.sort()
    without_id = sorted(without_id, key=lambda item: item.path)

    return discovered, without_id, notes


def _find_rune_dirs(repo_root: Path) -> List[Path]:
    rune_dirs = []
    for path in repo_root.rglob(DISCOVERY_GLOB):
        if not path.is_dir():
            continue
        if _skip_path(path):
            continue
        rune_dirs.append(path)
    return sorted(rune_dirs)


def _skip_path(path: Path) -> bool:
    skip_parts = {".git", "__pycache__", "node_modules", ".venv", ".mypy_cache"}
    return any(part in skip_parts for part in path.parts)


def _extract_rune_ids_from_ast(source: str) -> Set[str]:
    rune_ids: Set[str] = set()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return rune_ids

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if _is_rune_id_target(target):
                    value = _string_literal(node.value)
                    if value:
                        rune_ids.add(value)
        elif isinstance(node, ast.AnnAssign):
            if _is_rune_id_target(node.target):
                value = _string_literal(node.value)
                if value:
                    rune_ids.add(value)
        elif isinstance(node, ast.Dict):
            for key, value_node in zip(node.keys, node.values):
                if _string_literal(key) == "rune_id":
                    value = _string_literal(value_node)
                    if value:
                        rune_ids.add(value)
        elif isinstance(node, ast.Call):
            for keyword in node.keywords:
                if keyword.arg == "rune_id":
                    value = _string_literal(keyword.value)
                    if value:
                        rune_ids.add(value)

    return rune_ids


def _is_rune_id_target(node: ast.AST) -> bool:
    return isinstance(node, ast.Name) and node.id in {"RUNE_ID", "rune_id"}


def _string_literal(node: Optional[ast.AST]) -> Optional[str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _format_report(
    repo_root: Path,
    catalog_paths: Sequence[Path],
    registered_ids: Set[str],
    discovered_ids: Dict[str, RuneCandidate],
    missing: Sequence[str],
    orphans: Sequence[str],
    without_id: Sequence[CandidateWithoutId],
    discovery_notes: Sequence[str],
    catalog_index: Dict[str, List[str]],
    catalog_notes: Sequence[str],
) -> str:
    status = "FAIL" if missing else "PASS"
    catalog_list = [_relative_path(path, repo_root) for path in catalog_paths]

    lines: List[str] = [
        "# ABX-Rune Registry Primacy Gate v0.1",
        "",
        "## Summary",
        f"- catalogs_found: {len(catalog_list)}",
        f"- registered_rune_ids: {len(registered_ids)}",
        f"- discovered_rune_ids: {len(discovered_ids)}",
        f"- candidate_without_id: {len(without_id)}",
        f"- missing_registry: {len(missing)}",
        f"- orphan_registry: {len(orphans)}",
        f"- status: {status}",
        "",
        "## Catalogs",
    ]

    if catalog_list:
        for path in catalog_list:
            lines.append(f"- {path}")
    else:
        lines.append("- none (not_computable)")

    lines.extend(["", "## Rune discovery notes"])
    for note in discovery_notes:
        lines.append(f"- {note}")
    if catalog_notes:
        lines.append("- catalog notes:")
        for note in catalog_notes:
            lines.append(f"  - {note}")

    lines.extend(["", "## Missing registry entries (ERROR)"])
    if not missing:
        lines.append("- none")
    else:
        for rune_id in missing:
            sources = discovered_ids[rune_id].sources
            lines.append(f"- {rune_id}")
            for source in sources:
                lines.append(f"  - source: {source}")

    lines.extend(["", "## Orphan registry entries (WARN)"])
    if not orphans:
        lines.append("- none")
    else:
        for rune_id in orphans:
            locations = catalog_index.get(rune_id, [])
            lines.append(f"- {rune_id}")
            for location in sorted(locations):
                lines.append(f"  - catalog: {location}")

    lines.extend(["", "## Candidate without rune_id (WARN)"])
    if not without_id:
        lines.append("- none")
    else:
        for candidate in without_id:
            lines.append(f"- {candidate.path} ({candidate.reason})")

    lines.extend(["", "## SCaffold Pack"])
    if not missing:
        lines.append("- none")
    else:
        target_catalog = catalog_list[0] if catalog_list else "runes/catalog.v0.yaml"
        for rune_id in missing:
            sources = discovered_ids[rune_id].sources
            module_path = (
                _module_path_from_source(sources[0], repo_root)
                if sources
                else "unknown"
            )
            slug = _slugify_rune_id(rune_id)
            lines.extend(
                [
                    f"### {rune_id}",
                    f"- catalog_target: {target_catalog}",
                    "- yaml_snippet:",
                    "```yaml",
                    "  - rune_id: {rune_id}".format(rune_id=rune_id),
                    f"    module: {module_path}",
                    "    handler: invoke",
                    "    version: \"0.0.0\"",
                    "    domain_id: unknown",
                    f"    input_schema: schemas/capabilities/{slug}_input.schema.json",
                    f"    output_schema: schemas/capabilities/{slug}_output.schema.json",
                    "    tier_allowed:",
                    "      - psychonaut",
                    "      - academic",
                    "      - enterprise",
                    "    description: \"TODO: add description\"",
                    "    constraints:",
                    "      - deterministic",
                    "      - provenance_required",
                    "```",
                    "- contract_stub_paths:",
                    f"  - schemas/capabilities/{slug}_input.schema.json",
                    f"  - schemas/capabilities/{slug}_output.schema.json",
                    "- test_stub_path:",
                    f"  - tests/runes/test_{slug}_rune.py",
                    "- provenance_fields:",
                    "  - rune_id",
                    "  - input_hash",
                    "  - run_id",
                    "  - git_sha",
                    "  - computed_at_utc",
                ]
            )

    return "\n".join(lines) + "\n"


def _relative_path(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _module_path_from_source(relative_path: str, repo_root: Path) -> str:
    path = repo_root / relative_path
    if not path.exists():
        return "unknown"
    try:
        relative = path.relative_to(repo_root)
    except ValueError:
        relative = path
    module = ".".join(relative.with_suffix("").parts)
    return module


def _slugify_rune_id(rune_id: str) -> str:
    safe = []
    for char in rune_id:
        safe.append(char if char.isalnum() else "_")
    slug = "".join(safe).strip("_")
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug or "rune"


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> None:
    exit_code, output = run_gate()
    print(output, end="")
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
