from __future__ import annotations
import json
import hashlib
from dataclasses import asdict, is_dataclass
from typing import Any, Dict


def _stable(obj: Any) -> Any:
    if is_dataclass(obj):
        obj = asdict(obj)
    if isinstance(obj, dict):
        return {k: _stable(obj[k]) for k in sorted(obj.keys())}
    if isinstance(obj, list):
        return [_stable(x) for x in obj]
    return obj


def stable_hash(payload: Any) -> str:
    norm = _stable(payload)
    blob = json.dumps(norm, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def log_event(state, kind: str, data: Dict[str, Any]) -> None:
    state.logs.append({"kind": kind, "data": _stable(data)})
