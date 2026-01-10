from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional


DEFAULT_ROOT = Path(os.environ.get("ABRAXAS_HOME", Path.home() / ".abraxas"))


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def _atomic_write_json(path: Path, obj: Any) -> None:
    _atomic_write_text(path, json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


@dataclass(frozen=True)
class StoragePaths:
    root: Path

    @property
    def config_dir(self) -> Path:
        return self.root / "config"

    @property
    def ledger_dir(self) -> Path:
        return self.root / "ledger"

    @property
    def runs_dir(self) -> Path:
        return self.ledger_dir / "runs"

    @property
    def kite_dir(self) -> Path:
        return self.ledger_dir / "kite"

    def run_dir(self, day: str) -> Path:
        return self.runs_dir / day

    def kite_day_dir(self, day: str) -> Path:
        return self.kite_dir / day

    def oracle_readout_path(self, day: str) -> Path:
        return self.run_dir(day) / "oracle.readout.json"

    def oracle_md_path(self, day: str) -> Path:
        return self.run_dir(day) / "oracle.md"

    def provenance_path(self, day: str) -> Path:
        return self.run_dir(day) / "provenance.json"

    def events_path(self, day: str) -> Path:
        return self.run_dir(day) / "events.jsonl"

    def user_config_path(self) -> Path:
        return self.config_dir / "user.v0.json"

    def overlays_config_path(self) -> Path:
        return self.config_dir / "overlays.v0.json"

    def kite_ingest_jsonl(self, day: str) -> Path:
        return self.kite_day_dir(day) / "ingest.jsonl"

    def kite_candidates_path(self, day: str) -> Path:
        return self.kite_day_dir(day) / "candidates.json"


def today_iso() -> str:
    return date.today().isoformat()


def read_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: Any) -> None:
    _atomic_write_json(path, obj)


def write_text(path: Path, text: str) -> None:
    _atomic_write_text(path, text)
