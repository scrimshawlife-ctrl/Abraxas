"""
Rune Inventory Report v0.1.

Deterministic, read-only governance inventory for rune coverage.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .rune_registry_gate import CATALOG_PATH, _discover_rune_ids, parse_catalog_runes


@dataclass(frozen=True)
class CatalogStatus:
    status: str
    notes: List[str]


def build_inventory_report(repo_root: Optional[Path] = None) -> str:
    repo_root = Path(repo_root) if repo_root else _default_repo_root()
    repo_version = _read_repo_version(repo_root)

    code_runes, discovery_notes = _discover_code_runes(repo_root)
    catalog_entries, catalog_status = _load_catalog_entries(repo_root)

    return _format_markdown(
        repo_root=repo_root,
        repo_version=repo_version,
        code_runes=code_runes,
        discovery_notes=discovery_notes,
        catalog_entries=catalog_entries,
        catalog_status=catalog_status,
    )


def _discover_code_runes(repo_root: Path) -> Tuple[Dict[str, Any], List[str]]:
    discovered, _, notes = _discover_rune_ids(repo_root)
    return discovered, notes


def _load_catalog_entries(repo_root: Path) -> Tuple[Dict[str, Dict[str, str]], CatalogStatus]:
    catalog_path = repo_root / CATALOG_PATH
    if not catalog_path.exists():
        return {}, CatalogStatus(status="missing", notes=["catalog_missing"])
    try:
        entries = parse_catalog_runes(catalog_path)
    except Exception as exc:
        return {}, CatalogStatus(
            status="unreadable",
            notes=[f"catalog_unreadable: {exc}"],
        )
    return entries, CatalogStatus(status="ok", notes=[])


def _format_markdown(
    repo_root: Path,
    repo_version: str,
    code_runes: Dict[str, Any],
    discovery_notes: List[str],
    catalog_entries: Dict[str, Dict[str, str]],
    catalog_status: CatalogStatus,
) -> str:
    code_ids = sorted(code_runes.keys())
    catalog_ids = sorted(catalog_entries.keys())
    missing_registry = sorted(set(code_ids) - set(catalog_ids))
    design_ahead = sorted(set(catalog_ids) - set(code_ids))

    lines: List[str] = [
        "# Abraxas Inventory Report v0.1",
        "",
        "## Summary counts",
        f"- repo_version: {repo_version}",
        f"- code_runes_found: {len(code_ids)}",
        f"- catalog_runes_found: {len(catalog_ids)}",
        f"- missing_registry: {len(missing_registry)}",
        f"- design_ahead: {len(design_ahead)}",
        f"- catalog_status: {catalog_status.status}",
    ]

    if discovery_notes or catalog_status.notes:
        lines.append("- notes:")
        for note in discovery_notes:
            lines.append(f"  - {note}")
        for note in catalog_status.notes:
            lines.append(f"  - {note}")

    lines.extend(
        [
            "",
            "## Implemented Runes (code)",
        ]
    )
    if not code_ids:
        lines.append("- none")
    else:
        for rune_id in code_ids:
            rune = code_runes[rune_id]
            sources = ", ".join(getattr(rune, "sources", []))
            handler = getattr(rune, "handler", "unknown")
            module = getattr(rune, "module", "unknown")
            lines.append(
                f"- {rune_id} (handler={handler}, module={module}, sources={sources})"
            )

    lines.extend(
        [
            "",
            "## Registered Runes (catalog)",
        ]
    )
    if not catalog_ids:
        lines.append("- none")
    else:
        for rune_id in catalog_ids:
            module = catalog_entries[rune_id].get("module", "unknown")
            lines.append(f"- {rune_id} (module={module})")

    lines.extend(
        [
            "",
            "## Design-Ahead (registered without code)",
        ]
    )
    if not design_ahead:
        lines.append("- none")
    else:
        for rune_id in design_ahead:
            lines.append(f"- {rune_id}")

    lines.extend(
        [
            "",
            "## Registry Drift (should be impossible)",
        ]
    )
    if not missing_registry:
        lines.append("- none")
    else:
        for rune_id in missing_registry:
            lines.append(f"- ERROR: code rune missing from catalog: {rune_id}")

    lines.extend(
        [
            "",
            "## Notion Catch-up Checklist",
        ]
    )

    checklist = []
    for rune_id in missing_registry:
        checklist.append(f"- [ ] Add registry + Notion entry: {rune_id}")
    for rune_id in design_ahead:
        checklist.append(f"- [ ] Review design-ahead rune: {rune_id}")
    if catalog_status.status != "ok":
        checklist.append("- [ ] Catalog unavailable; restore catalog.v0.yaml")

    if checklist:
        lines.extend(checklist)
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Assumptions / Limits",
            "- Uses filename-based discovery from rune_registry_gate.",
            "- Uses minimal catalog parser (no external dependencies).",
            "- Design-ahead entries are reported, not treated as errors.",
        ]
    )

    return "\n".join(lines) + "\n"


def _read_repo_version(repo_root: Path) -> str:
    version_path = repo_root / "VERSION"
    if not version_path.exists():
        return "unknown"
    content = version_path.read_text(encoding="utf-8").strip()
    return content or "unknown"


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> None:
    report = build_inventory_report()
    print(report, end="")


if __name__ == "__main__":
    main()
