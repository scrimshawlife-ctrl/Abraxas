from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from abraxas.core.provenance import hash_canonical_json


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def compute_candidate_id(payload: Dict[str, Any]) -> str:
    return hash_canonical_json(payload)


def stable_input_hash(*items: Any) -> str:
    normalized = [item for item in items]
    return hash_canonical_json(normalized)


def sort_candidates(candidates: List[Any]) -> List[Any]:
    return sorted(
        candidates,
        key=lambda c: (c.candidate_id, c.source_loop, tuple(c.target_paths)),
    )


def read_json(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected object in {path}")
    return data


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entries.append(json.loads(line))
    return entries


def pick_paths(root: Path, pattern: str) -> List[Path]:
    return sorted(root.rglob(pattern))


def not_computable_payload(reason: str, missing_inputs: Iterable[str], provenance: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "status": "NOT_COMPUTABLE",
        "reason": reason,
        "missing_inputs": list(missing_inputs),
        "provenance": provenance,
    }


def build_patch_plan(
    *,
    operations: List[Dict[str, Any]],
    notes: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    payload = {
        "format_version": "0.1",
        "operations": operations,
        "notes": notes or [],
        "metadata": metadata or {},
    }
    payload["plan_id"] = compute_candidate_id(payload)
    return payload

