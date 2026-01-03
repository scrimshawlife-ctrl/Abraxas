"""Performance ledger for acquisition steps."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from abraxas.core.canonical import canonical_json


@dataclass(frozen=True)
class PerfLedger:
    path: Path = Path("out/perf_ledgers/acquisition.jsonl")

    def record(self, payload: Dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        line = canonical_json(payload)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
