from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from .loader import load_canon_entry, load_rune
from .schemas import CanonEntry, Rune


@dataclass(frozen=True)
class Codex:
    canon: Dict[str, CanonEntry]
    runes: Dict[str, Rune]


def build_codex(root: Path) -> Codex:
    """
    Deterministic loader:
      - fixed directories
      - sorted file traversal
      - stable dict insertion via sorted keys
    """
    entries_dir = root / "entries"
    runes_dir = root / "runes"

    canon: Dict[str, CanonEntry] = {}
    runes: Dict[str, Rune] = {}

    if entries_dir.exists():
        for p in sorted(entries_dir.glob("*")):
            if p.suffix.lower() in (".yaml", ".yml", ".json"):
                e = load_canon_entry(p)
                if e.entry_id in canon:
                    raise RuntimeError(f"Duplicate canon entry_id: {e.entry_id}")
                canon[e.entry_id] = e

    if runes_dir.exists():
        for p in sorted(runes_dir.glob("*")):
            if p.name.endswith(".rune.json") or p.suffix.lower() == ".json":
                r = load_rune(p)
                if r.rune_id in runes:
                    raise RuntimeError(f"Duplicate rune_id: {r.rune_id}")
                runes[r.rune_id] = r

    return Codex(
        canon={k: canon[k] for k in sorted(canon.keys())},
        runes={k: runes[k] for k in sorted(runes.keys())},
    )


def validate_codex(root: Path):
    """
    Convenience: build codex then run validators (currently Bell).
    Returns (codex, findings_dict).
    """
    from .validate.bell_validator import BellValidatorConfig, validate_codex_bell

    codex = build_codex(root)
    findings = {
        "bell": validate_codex_bell(codex, BellValidatorConfig()),
    }
    return codex, findings
