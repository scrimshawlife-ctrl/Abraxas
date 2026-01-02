from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from tools.acceptance.run_acceptance_suite import canonical_json, sha256  # reuse


def _write(out_dir: Path, obj: Dict[str, Any]) -> None:
    p = out_dir / "acceptance" / "drift_on_failure_v1.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")


def classify_drift(changed_pointers: List[str]) -> str:
    # Simple heuristics. You can improve later without changing the artifact contract.
    joined = " ".join(changed_pointers).lower()
    if "created_at" in joined or "timestamp" in joined:
        return "TIME_DEPENDENCE"
    if "seed" in joined or "random" in joined:
        return "NONDETERMINISM_RANDOMNESS"
    if "sources" in joined or "evidence" in joined:
        return "EXTERNAL_SOURCE_VARIANCE"
    if "schema_version" in joined:
        return "VERSION_SKEW"
    return "UNKNOWN"


def emit(out_dir: Path, envelopes: List[Dict[str, Any]], changes: List[Dict[str, Any]]) -> None:
    # changes = [{"pointer":..., "before":..., "after":...}, ...]
    pointers = sorted({c.get("pointer", "") for c in changes if c.get("pointer")})
    obj: Dict[str, Any] = {
        "schema_version": "1.0.0",
        "class": classify_drift(pointers),
        "mismatch": {
            "hashes": [sha256(canonical_json(e)) for e in envelopes],
            "changed_pointers": pointers[:200],
        },
        "diff_sample": changes[:200],
    }
    _write(out_dir, obj)

