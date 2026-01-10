from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
VERSION = (ROOT_DIR / "VERSION").read_text(encoding="utf-8").strip()


@dataclass(frozen=True)
class AATFPaths:
    base: Path
    local_store: Path
    ledger: Path
    exports: Path


def resolve_paths() -> AATFPaths:
    override = os.environ.get("AATF_HOME")
    base = Path(override).resolve() if override else ROOT_DIR / ".aatf"
    local_store = base / "local_store"
    ledger = base / "ledger"
    exports = base / "exports"
    return AATFPaths(base=base, local_store=local_store, ledger=ledger, exports=exports)


def ensure_paths(paths: AATFPaths) -> None:
    paths.base.mkdir(parents=True, exist_ok=True)
    paths.local_store.mkdir(parents=True, exist_ok=True)
    paths.ledger.mkdir(parents=True, exist_ok=True)
    paths.exports.mkdir(parents=True, exist_ok=True)
