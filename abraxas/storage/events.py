# abraxas/storage/events.py
# Event persistence layer

from __future__ import annotations
from dataclasses import asdict
from typing import Iterable, List, Dict
import json
import os

from abraxas.operators.symbolic_compression import SymbolicCompressionEvent

def write_events_jsonl(path: str, events: Iterable[SymbolicCompressionEvent]) -> None:
    """Write events to JSONL file."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for e in events:
            f.write(json.dumps(asdict(e), sort_keys=True) + "\n")

def read_events_jsonl(path: str) -> List[Dict]:
    """Read events from JSONL file."""
    out: List[Dict] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out
