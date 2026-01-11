"""Perf ledger for deterministic parallel stages."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from abraxas.core.canonical import canonical_json


@dataclass(frozen=True)
class RuntimePerfLedger:
    path: Path = Path("out/perf_ledgers/runtime_parallel.jsonl")

    def record(self, payload: Dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(canonical_json(payload) + "\n")
