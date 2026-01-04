"""Rune adapters for evolve.* capability contracts.

Thin wrappers only: no core logic changes.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from abraxas.core.provenance import hash_canonical_json

from abraxas.evolve.non_truncation import enforce_non_truncation as _enforce_non_truncation


def enforce_non_truncation_deterministic(
    artifact: Dict[str, Any],
    raw_full: Any,
    raw_full_path: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Capability adapter for evolve.non_truncation.enforce.

    Returns:
        {"artifact": <annotated_artifact>}
    """

    out = _enforce_non_truncation(artifact=artifact, raw_full=raw_full, raw_full_path=raw_full_path)
    return {"artifact": out}


def append_chained_jsonl_deterministic(
    ledger_path: str,
    record: Dict[str, Any],
    **kwargs,
) -> Dict[str, Any]:
    """Capability adapter for evolve.ledger.append_chained_jsonl.

    Mirrors `abraxas.evolve.ledger.append_chained_jsonl` behavior but returns the
    computed hashes for observability.
    """

    path = Path(ledger_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    prev_hash = "genesis"
    if path.exists():
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        if lines:
            try:
                last = json.loads(lines[-1])
                prev_hash = str(last.get("step_hash") or "genesis")
            except Exception:
                prev_hash = "genesis"

    entry = dict(record)
    entry["prev_hash"] = prev_hash
    step_hash = hash_canonical_json(entry)
    entry["step_hash"] = step_hash
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")
    return {"prev_hash": prev_hash, "step_hash": step_hash}


__all__ = ["enforce_non_truncation_deterministic", "append_chained_jsonl_deterministic"]

