"""
ABX-Rune Registry Primacy Gate v1.0.

Hard gate: fail when rune IDs exist in code but not in catalog.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment-specific dependency
    raise ImportError(
        "PyYAML required for rune registry gate. Install via: pip install pyyaml"
    ) from exc


CATALOG_PATH = Path("abraxas_ase") / "runes" / "catalog.v0.yaml"
DISCOVERY_ROOT = Path("abraxas_ase") / "runes"
EXCLUDED_FILES = {"__init__.py", "invoke.py"}

RUNE_ID_REGEX = re.compile(r'"rune_id"\s*:\s*"([^"]+)"')
DOCSTRING_REGEX = re.compile(r"ABX-Runes Adapter:\s*([A-Za-z0-9_.-]+)")
HANDLER_RUN_REGEX = re.compile(r"\bdef\s+run\s*\(")
HANDLER_INVOKE_REGEX = re.compile(r"\bdef\s+invoke\s*\(")


@dataclass(frozen=True)
class RuneCandidate:
    rune_id: str
    sources: List[str]
    handler: str


@dataclass(frozen=True)
class CandidateWithoutId:
    path: str
    reason: str


def run_gate(repo_root: Optional[Path] = None) -> Tuple[int, str]:
    repo_root = Path(repo_root) if repo_root else _default_repo_root()
    catalog_path = repo_root / CATALOG_PATH
    registered_ids, catalog_index, catalog_notes, catalog_defaults = _load_catalog_ids(
        catalog_path, repo_root
    )

    discovered_ids, without_id, discovery_notes = _discover_rune_ids(repo_root)
    missing = sorted(discovered_ids.keys() - registered_ids)
    orphans = sorted(registered_ids - discovered_ids.keys())

    output = _format_report(
        repo_root=repo_root,
        catalog_path=catalog_path,
        registered_ids=registered_ids,
        discovered_ids=discovered_ids,
        missing=missing,
        orphans=orphans,
        without_id=without_id,
        discovery_notes=discovery_notes,
        catalog_index=catalog_index,
        catalog_notes=catalog_notes,
        catalog_defaults=catalog_defaults,
    )
    exit_code = 2 if missing or "catalog_missing" in catalog_notes else 0
    return exit_code, output


def _load_catalog_ids(
    catalog_path: Path,
    repo_root: Path,
) -> Tuple[Set[str], Dict[str, List[str]], List[str], Dict[str, object]]:
    rune_ids: Set[str] = set()
    catalog_index: Dict[str, List[str]] = {}
    notes: List[str] = []
    defaults: Dict[str, object] = {}

    if not catalog_path.exists():
        notes.append("catalog_missing")
        return rune_ids, catalog_index, notes, defaults

    try:
        data = yaml.safe_load(catalog_path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        notes.append(
            f"catalog_unreadable: {_relative_path(catalog_path, repo_root)} ({exc})"
        )
        return rune_ids, catalog_index, notes, defaults

    runes = data.get("runes", [])
    if not isinstance(runes, list):
        notes.append(
            f"catalog_runes_list_missing: {_relative_path(catalog_path, repo_root)}"
        )
        return rune_ids, catalog_index, notes, defaults

    for entry in runes:
        if not isinstance(entry, dict):
            continue
        rune_id = entry.get("rune_id")
        if isinstance(rune_id, str) and rune_id.strip():
            rune_ids.add(rune_id)
            catalog_index.setdefault(rune_id, []).append(
                _relative_path(catalog_path, repo_root)
            )

    defaults = _extract_catalog_defaults(runes)
    notes = sorted(set(notes))
    return rune_ids, catalog_index, notes, defaults


def _discover_rune_ids(
    repo_root: Path,
) -> Tuple[Dict[str, RuneCandidate], List[CandidateWithoutId], List[str]]:
    discovered: Dict[str, RuneCandidate] = {}
    without_id: List[CandidateWithoutId] = []
    notes = [
        "rune_id discovery scans dict key literals and adapter docstrings only.",
        'patterns: `"rune_id": "<id>"` and `ABX-Runes Adapter: <id>`.',
    ]

    discovery_root = repo_root / DISCOVERY_ROOT
    if not discovery_root.exists():
        notes.append("discovery_root_missing")
        return discovered, without_id, notes

    for path in sorted(discovery_root.rglob("*.py")):
        if path.name in EXCLUDED_FILES:
            continue
        relative = _relative_path(path, repo_root)
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            without_id.append(
                CandidateWithoutId(path=relative, reason="unreadable python file")
            )
            continue

        rune_ids = set(RUNE_ID_REGEX.findall(text))
        rune_ids.update(DOCSTRING_REGEX.findall(text))
        handler = _infer_handler(text)
        has_rune_hint = ("rune_id" in text) or ("ABX-Runes Adapter:" in text)

        if rune_ids:
            for rune_id in sorted(rune_ids):
                entry = discovered.get(rune_id)
                if entry is None:
                    discovered[rune_id] = RuneCandidate(
                        rune_id=rune_id, sources=[relative], handler=handler
                    )
                else:
                    entry.sources.append(relative)
                    entry = RuneCandidate(
                        rune_id=rune_id,
                        sources=entry.sources,
                        handler=_merge_handler(entry.handler, handler),
                    )
                    discovered[rune_id] = entry
        elif has_rune_hint:
            without_id.append(
                CandidateWithoutId(path=relative, reason="rune_id literal not found")
            )

    for candidate in discovered.values():
        candidate.sources.sort()
    without_id = sorted(without_id, key=lambda item: item.path)

    return discovered, without_id, notes


def _format_report(
    repo_root: Path,
    catalog_path: Path,
    registered_ids: Set[str],
    discovered_ids: Dict[str, RuneCandidate],
    missing: Sequence[str],
    orphans: Sequence[str],
    without_id: Sequence[CandidateWithoutId],
    discovery_notes: Sequence[str],
    catalog_index: Dict[str, List[str]],
    catalog_notes: Sequence[str],
    catalog_defaults: Dict[str, object],
) -> str:
    status = "FAIL" if missing or "catalog_missing" in catalog_notes else "PASS"
    catalog_list = (
        [_relative_path(catalog_path, repo_root)] if catalog_path.exists() else []
    )

    lines: List[str] = [
        "# ABX-Rune Registry Primacy Gate v1.0",
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
        for rune_id in missing:
            sources = discovered_ids[rune_id].sources
            module_path = (
                _module_path_from_source(sources[0], repo_root)
                if sources
                else "unknown"
            )
            handler = discovered_ids[rune_id].handler
            slug = _slugify_rune_id(rune_id)
            input_schema = str(
                catalog_defaults.get(
                    "input_schema", "sdct/contracts/sdct_domain_params.v0.schema.json"
                )
            )
            output_schema = str(
                catalog_defaults.get(
                    "output_schema", "sdct/contracts/sdct_evidence_row.v0.schema.json"
                )
            )
            tier_allowed = catalog_defaults.get("tier_allowed", ["psychonaut", "academic", "enterprise"])
            tier_lines = [f"      - {tier}" for tier in tier_allowed]
            lines.extend(
                [
                    f"### {rune_id}",
                    f"- catalog_target: {catalog_list[0] if catalog_list else catalog_path.as_posix()}",
                    "- yaml_snippet:",
                    "```yaml",
                    "  - rune_id: {rune_id}".format(rune_id=rune_id),
                    f"    module: {module_path}",
                    f"    handler: {handler}",
                    "    version: \"1.0.0\"",
                    f"    domain_id: {rune_id}",
                    f"    input_schema: {input_schema}",
                    f"    output_schema: {output_schema}",
                    "    tier_allowed:",
                    *tier_lines,
                    "    description: \"TODO: add description\"",
                    "    constraints:",
                    "      - deterministic",
                    "      - provenance_required",
                    "```",
                    "- contract_stub_paths:",
                    f"  - {input_schema}",
                    f"  - {output_schema}",
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


def _extract_catalog_defaults(runes: Sequence[object]) -> Dict[str, object]:
    for entry in runes:
        if not isinstance(entry, dict):
            continue
        input_schema = entry.get("input_schema")
        output_schema = entry.get("output_schema")
        tier_allowed = entry.get("tier_allowed")
        if input_schema and output_schema and tier_allowed:
            return {
                "input_schema": input_schema,
                "output_schema": output_schema,
                "tier_allowed": list(tier_allowed),
            }
    return {}


def _infer_handler(text: str) -> str:
    if HANDLER_RUN_REGEX.search(text):
        return "run"
    if HANDLER_INVOKE_REGEX.search(text):
        return "invoke"
    return "invoke"


def _merge_handler(existing: str, candidate: str) -> str:
    priority = {"run": 2, "invoke": 1, "unknown": 0}
    return existing if priority.get(existing, 0) >= priority.get(candidate, 0) else candidate


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> None:
    exit_code, output = run_gate()
    print(output, end="")
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
