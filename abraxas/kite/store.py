from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, List, Optional


class KiteLocalStore:
    """
    Local-only storage. No cloud assumptions.
    """
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _p(self, name: str) -> Path:
        return self.root / name

    def append_jsonl(self, name: str, obj: Dict[str, Any]) -> None:
        p = self._p(name)
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=True) + "\n")

    def read_jsonl(self, name: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        p = self._p(name)
        if not p.exists():
            return []
        out = []
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                out.append(json.loads(line))
                if limit and len(out) >= limit:
                    break
        return out
