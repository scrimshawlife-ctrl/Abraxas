from __future__ import annotations

import glob
import json
import os
from typing import Any, Dict, List, Optional, Tuple


def _read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def candidate_envelope_paths(v1_out_dir: str | None = None) -> List[str]:
    base = v1_out_dir or "out"
    cands = [
        os.path.join(base, "latest", "envelope.json"),
        os.path.join("out", "latest", "envelope.json"),
        os.path.join("var", "out", "latest", "envelope.json"),
    ]
    # Deterministic "most recent": lexicographically largest run folder
    globbed = sorted(glob.glob(os.path.join(base, "*", "envelope.json")))
    if globbed:
        cands.append(globbed[-1])
    # Deduplicate while preserving order
    seen = set()
    out: List[str] = []
    for p in cands:
        if p not in seen:
            out.append(p)
            seen.add(p)
    return out


def discover_envelope(v1_out_dir: str | None = None) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    Attempts to locate a v1 envelope.json deterministically.
    Returns (path, envelope) or (None, None).
    """
    for p in candidate_envelope_paths(v1_out_dir=v1_out_dir):
        if os.path.exists(p) and os.path.isfile(p):
            try:
                return p, _read_json(p)
            except Exception:
                # If unreadable, keep searching other candidates.
                continue
    return None, None
