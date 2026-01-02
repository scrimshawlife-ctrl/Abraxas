from __future__ import annotations

import json
from typing import Any, Dict, Tuple

from abraxas.core.canonical import canonical_json


def _load_packet(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _runs_by_id(packet: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    runs = (packet.get("oracle_packet_v0_1") or {}).get("runs") or []
    out: Dict[str, Dict[str, Any]] = {}
    for r in runs:
        if isinstance(r, dict) and r.get("run_id"):
            out[str(r["run_id"])] = r
    return out


def classify_packet_drift(old_path: str, new_path: str) -> Tuple[str, Dict[str, Any]]:
    """
    Classify drift between two oracle_packet.json files.

    Returns (status, details), where status is one of:
      - none: packet hash matches
      - canon: slice_hash differs for any shared run_id
      - shadow_only: slice_hash stable but shadow_summary differs
      - unknown: packet hash differs but no slice_hash/shadow_summary diff found
    """
    old = _load_packet(old_path)
    new = _load_packet(new_path)

    old_hash = str(old.get("oracle_packet_hash", ""))
    new_hash = str(new.get("oracle_packet_hash", ""))
    if old_hash and new_hash and old_hash == new_hash:
        return "none", {"reason": "packet_hash_match"}

    old_runs = _runs_by_id(old)
    new_runs = _runs_by_id(new)
    shared_ids = sorted(set(old_runs.keys()) & set(new_runs.keys()))

    canon_diffs = []
    shadow_diffs = []

    for run_id in shared_ids:
        o = old_runs[run_id]
        n = new_runs[run_id]
        o_slice = str(o.get("signal_slice_hash", ""))
        n_slice = str(n.get("signal_slice_hash", ""))
        if o_slice != n_slice:
            canon_diffs.append(run_id)
            continue
        o_shadow = o.get("shadow_summary")
        n_shadow = n.get("shadow_summary")
        if canonical_json(o_shadow) != canonical_json(n_shadow):
            shadow_diffs.append(run_id)

    if canon_diffs:
        return "canon", {"run_ids": canon_diffs, "reason": "slice_hash_diff"}
    if shadow_diffs:
        return "shadow_only", {"run_ids": shadow_diffs, "reason": "shadow_summary_diff"}
    return "unknown", {"reason": "packet_hash_diff_no_slice_or_shadow_diff"}
