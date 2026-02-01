"""
Rune & Overlay Inventory Report v0.1.

Deterministic, read-only governance inventory for runes and overlays.
"""

from __future__ import annotations

import ast
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - environment-specific dependency
    yaml = None

DEFAULT_CANON_STATE_PATH = Path(".abraxas") / "canon_state.v0.yaml"
DEFAULT_RUNES_REGISTRY_PATH = Path("abraxas") / "runes" / "registry.json"
DEFAULT_OVERLAYS_REGISTRY_PATH = Path("abraxas") / "overlays" / "registry.py"


@dataclass(frozen=True)
class RuneEntry:
    rune_id: str
    short_name: str
    name: str
    layer: str
    status: str
    introduced_version: str
    source: str


@dataclass(frozen=True)
class OverlayEntry:
    name: str
    source: str
    path: str


@dataclass(frozen=True)
class DiscoveryResult:
    status: str
    source: str
    items: List[Any]
    limitations: List[str]


@dataclass(frozen=True)
class CanonCoverage:
    status: str
    missing: List[str]
    notes: List[str]


def build_inventory_report(repo_root: Optional[Path] = None) -> str:
    repo_root = Path(repo_root) if repo_root else _default_repo_root()
    repo_version = _read_repo_version(repo_root)

    runes_result = _discover_runes(repo_root)
    overlays_result = _discover_overlays(repo_root)
    canon_coverage = _check_canon_metadata(repo_root)

    return _format_markdown(
        repo_root=repo_root,
        repo_version=repo_version,
        runes_result=runes_result,
        overlays_result=overlays_result,
        canon_coverage=canon_coverage,
    )


def _discover_runes(repo_root: Path) -> DiscoveryResult:
    registry_path = repo_root / DEFAULT_RUNES_REGISTRY_PATH
    limitations: List[str] = []

    if registry_path.exists():
        try:
            data = json.loads(registry_path.read_text(encoding="utf-8"))
            runes = data.get("runes", [])
            entries: List[RuneEntry] = []
            if isinstance(runes, list):
                for rune in runes:
                    if not isinstance(rune, dict):
                        continue
                    entries.append(
                        RuneEntry(
                            rune_id=str(rune.get("id", "unknown")),
                            short_name=str(rune.get("short_name", "unknown")),
                            name=str(rune.get("name", "unknown")),
                            layer=str(rune.get("layer", "unknown")),
                            status=str(rune.get("status", "unknown")),
                            introduced_version=str(
                                rune.get("introduced_version", "unknown")
                            ),
                            source="registry.json",
                        )
                    )
                entries = sorted(entries, key=_rune_sort_key)
                return DiscoveryResult(
                    status="ok",
                    source="registry.json",
                    items=entries,
                    limitations=limitations,
                )
            limitations.append("runes registry malformed; falling back to definitions")
        except Exception as exc:
            limitations.append(f"runes registry unreadable: {exc}")

    definitions_dir = repo_root / "abraxas" / "runes" / "definitions"
    if definitions_dir.exists():
        entries = _load_runes_from_definitions(definitions_dir)
        limitations.append("runes discovered from definitions (best-effort)")
        entries = sorted(entries, key=_rune_sort_key)
        return DiscoveryResult(
            status="ok",
            source="definitions",
            items=entries,
            limitations=limitations,
        )

    limitations.append("runes registry and definitions missing")
    return DiscoveryResult(
        status="not_computable",
        source="none",
        items=[],
        limitations=limitations,
    )


def _load_runes_from_definitions(definitions_dir: Path) -> List[RuneEntry]:
    entries: List[RuneEntry] = []
    for path in sorted(definitions_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        entries.append(
            RuneEntry(
                rune_id=str(data.get("id", "unknown")),
                short_name=str(data.get("short_name", "unknown")),
                name=str(data.get("name", "unknown")),
                layer=str(data.get("layer", "unknown")),
                status=str(data.get("evidence_tier", data.get("status", "unknown"))),
                introduced_version=str(data.get("introduced_version", "unknown")),
                source=f"definition:{path.name}",
            )
        )
    return entries


def _discover_overlays(repo_root: Path) -> DiscoveryResult:
    registry_path = repo_root / DEFAULT_OVERLAYS_REGISTRY_PATH
    limitations: List[str] = []

    if registry_path.exists():
        try:
            names = _extract_overlay_names_from_registry(registry_path)
            entries = [
                OverlayEntry(name=name, source="registry.py", path=str(registry_path))
                for name in sorted(set(names))
            ]
            if entries:
                return DiscoveryResult(
                    status="ok",
                    source="registry.py",
                    items=entries,
                    limitations=limitations,
                )
            limitations.append("overlay registry parsed but no names found")
        except Exception as exc:
            limitations.append(f"overlay registry unreadable: {exc}")

    fallback_entries = _discover_overlays_from_files(repo_root)
    if fallback_entries:
        limitations.append("overlays discovered from filesystem (best-effort)")
        return DiscoveryResult(
            status="ok",
            source="filesystem",
            items=sorted(fallback_entries, key=lambda entry: entry.name),
            limitations=limitations,
        )

    limitations.append("overlay registry and directories missing")
    return DiscoveryResult(
        status="not_computable",
        source="none",
        items=[],
        limitations=limitations,
    )


def _extract_overlay_names_from_registry(registry_path: Path) -> List[str]:
    tree = ast.parse(registry_path.read_text(encoding="utf-8"))
    overlay_names: List[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "default":
            for inner in ast.walk(node):
                if isinstance(inner, ast.Assign):
                    if not any(
                        isinstance(target, ast.Name) and target.id == "overlays"
                        for target in inner.targets
                    ):
                        continue
                    if isinstance(inner.value, ast.Dict):
                        for key in inner.value.keys:
                            if isinstance(key, ast.Constant) and isinstance(
                                key.value, str
                            ):
                                overlay_names.append(key.value)
    return overlay_names


def _discover_overlays_from_files(repo_root: Path) -> List[OverlayEntry]:
    candidates = [
        repo_root / "abraxas" / "overlays",
        repo_root / "aal_core" / "overlays",
    ]
    entries: List[OverlayEntry] = []
    for directory in candidates:
        if not directory.exists():
            continue
        for path in sorted(directory.glob("*.py")):
            if path.name in {
                "__init__.py",
                "base.py",
                "registry.py",
                "_registry.py",
                "dispatcher.py",
            }:
                continue
            entries.append(
                OverlayEntry(name=path.stem, source="filesystem", path=str(path))
            )
        for path in sorted(directory.iterdir()):
            if path.is_dir() and (path / "__init__.py").exists():
                entries.append(
                    OverlayEntry(
                        name=path.name, source="filesystem", path=str(path)
                    )
                )
    return entries


def _check_canon_metadata(repo_root: Path) -> CanonCoverage:
    canon_path = repo_root / DEFAULT_CANON_STATE_PATH
    missing: List[str] = []
    notes: List[str] = []

    if yaml is None:
        return CanonCoverage(
            status="not_computable",
            missing=["PyYAML unavailable"],
            notes=notes,
        )

    if not canon_path.exists():
        return CanonCoverage(
            status="not_computable",
            missing=[f"canon_state missing: {canon_path.as_posix()}"],
            notes=notes,
        )

    try:
        data = yaml.safe_load(canon_path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        return CanonCoverage(
            status="not_computable",
            missing=[f"canon_state unreadable: {exc}"],
            notes=notes,
        )

    if not isinstance(data, dict):
        return CanonCoverage(
            status="not_computable",
            missing=["canon_state root is not a mapping"],
            notes=notes,
        )

    subsystems = data.get("subsystems", [])
    if not isinstance(subsystems, list):
        return CanonCoverage(
            status="not_computable",
            missing=["canon_state subsystems is not a list"],
            notes=notes,
        )

    subsystem_map: Dict[str, Dict[str, Any]] = {}
    for entry in subsystems:
        if isinstance(entry, dict) and isinstance(entry.get("key"), str):
            subsystem_map[entry["key"]] = entry

    expected = {
        "runes": [DEFAULT_RUNES_REGISTRY_PATH.as_posix()],
        "overlays": [DEFAULT_OVERLAYS_REGISTRY_PATH.as_posix()],
    }

    for key, expected_paths in expected.items():
        entry = subsystem_map.get(key)
        if entry is None:
            missing.append(f"missing subsystem entry: {key}")
            continue

        registries = entry.get("registries")
        if not isinstance(registries, list):
            missing.append(f"missing registries list for subsystem: {key}")
            continue

        registry_values = {_normalize_path(item) for item in registries if item}
        for expected_path in expected_paths:
            normalized = _normalize_path(expected_path)
            if normalized not in registry_values:
                missing.append(
                    f"missing registry path for {key}: {expected_path}"
                )
            else:
                registry_path = repo_root / normalized
                if not registry_path.exists():
                    notes.append(
                        f"registry path for {key} missing on disk: {expected_path}"
                    )

    missing = sorted(set(missing))
    notes = sorted(set(notes))
    return CanonCoverage(status="ok", missing=missing, notes=notes)


def _format_markdown(
    repo_root: Path,
    repo_version: str,
    runes_result: DiscoveryResult,
    overlays_result: DiscoveryResult,
    canon_coverage: CanonCoverage,
) -> str:
    lines: List[str] = [
        "# Abraxas Inventory Report v0.1",
        "",
        "## Summary counts",
        f"- repo_version: {repo_version}",
        f"- runes_found: {len(runes_result.items)} (status={runes_result.status})",
        f"- overlays_found: {len(overlays_result.items)} (status={overlays_result.status})",
        (
            "- canon_state: {status} (missing={count})".format(
                status=canon_coverage.status, count=len(canon_coverage.missing)
            )
        ),
    ]

    limitations = sorted(
        set(runes_result.limitations + overlays_result.limitations)
    )
    if limitations:
        lines.append("- limitations:")
        for limitation in limitations:
            lines.append(f"  - {limitation}")
    else:
        lines.append("- limitations: none")

    lines.extend(
        [
            "",
            "## Runes",
        ]
    )
    if runes_result.status != "ok":
        lines.append("- not_computable")
    elif not runes_result.items:
        lines.append("- none")
    else:
        for rune in runes_result.items:
            lines.append(
                (
                    "- {rune_id} | {short_name} | {name} | "
                    "layer={layer} | status={status} | introduced={introduced}"
                ).format(
                    rune_id=rune.rune_id,
                    short_name=rune.short_name,
                    name=rune.name,
                    layer=rune.layer,
                    status=rune.status,
                    introduced=rune.introduced_version,
                )
            )

    lines.extend(
        [
            "",
            "## Overlays",
        ]
    )
    if overlays_result.status != "ok":
        lines.append("- not_computable")
    elif not overlays_result.items:
        lines.append("- none")
    else:
        for overlay in overlays_result.items:
            lines.append(
                f"- {overlay.name} (source={overlay.source})"
            )

    lines.extend(
        [
            "",
            "## Canon metadata coverage",
            f"- status: {canon_coverage.status}",
        ]
    )
    if canon_coverage.status != "ok":
        for missing in canon_coverage.missing:
            lines.append(f"- not_computable: {missing}")
    else:
        if canon_coverage.missing:
            lines.append("- missing:")
            for missing in canon_coverage.missing:
                lines.append(f"  - {missing}")
        else:
            lines.append("- missing: none")
        if canon_coverage.notes:
            lines.append("- notes:")
            for note in canon_coverage.notes:
                lines.append(f"  - {note}")

    lines.extend(
        [
            "",
            "## Notion Catch-up Checklist",
        ]
    )

    checklist = _build_checklist(
        runes_result, overlays_result, canon_coverage
    )
    if checklist:
        lines.extend(checklist)
    else:
        lines.append("- none")

    return "\n".join(lines) + "\n"


def _build_checklist(
    runes_result: DiscoveryResult,
    overlays_result: DiscoveryResult,
    canon_coverage: CanonCoverage,
) -> List[str]:
    items: List[str] = []

    if runes_result.status == "ok":
        for rune in runes_result.items:
            items.append(
                (
                    "- [ ] Rune registry entry: {rune_id} {short_name} — {name}"
                ).format(
                    rune_id=rune.rune_id,
                    short_name=rune.short_name,
                    name=rune.name,
                )
            )
    else:
        items.append("- [ ] Rune registry entry: not_computable")

    if overlays_result.status == "ok":
        for overlay in overlays_result.items:
            items.append(
                f"- [ ] Overlay registry entry: {overlay.name}"
            )
    else:
        items.append("- [ ] Overlay registry entry: not_computable")

    if canon_coverage.status == "ok" and canon_coverage.missing:
        for missing in canon_coverage.missing:
            items.append(f"- [ ] Canon state metadata: {missing}")
    elif canon_coverage.status != "ok":
        items.append("- [ ] Canon state metadata: not_computable")

    return items


def _normalize_path(value: str) -> str:
    return str(value).strip().lstrip("./")


def _read_repo_version(repo_root: Path) -> str:
    version_path = repo_root / "VERSION"
    if not version_path.exists():
        return "unknown"
    content = version_path.read_text(encoding="utf-8").strip()
    return content or "unknown"


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _rune_sort_key(rune: RuneEntry) -> Iterable[Any]:
    numeric = _rune_numeric_id(rune.rune_id)
    return (numeric, rune.rune_id, rune.short_name)


def _rune_numeric_id(rune_id: str) -> int:
    subscript_digits = {
        "₀": "0",
        "₁": "1",
        "₂": "2",
        "₃": "3",
        "₄": "4",
        "₅": "5",
        "₆": "6",
        "₇": "7",
        "₈": "8",
        "₉": "9",
    }
    digits: List[str] = []
    for char in rune_id:
        if char.isdigit():
            digits.append(char)
        elif char in subscript_digits:
            digits.append(subscript_digits[char])
    if not digits:
        return 10**6
    return int("".join(digits))


def main() -> None:
    report = build_inventory_report()
    print(report, end="")


if __name__ == "__main__":
    main()
