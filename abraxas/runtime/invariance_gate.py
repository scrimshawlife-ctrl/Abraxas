"""
Abraxas Runtime Invariance Gate — Dozen-Run Determinism Check.

Runs the same tick N times in isolated artifact directories and verifies:
1. All TrendPack sha256 are identical
2. All RunHeader sha256 are identical (v2)

On mismatch, produces field-level drift diff for debugging.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class DozenRunGateResult:
    ok: bool
    expected_sha256: str
    sha256s: List[str]
    expected_runheader_sha256: Optional[str] = None
    runheader_sha256s: Optional[List[str]] = None
    first_mismatch_run: Optional[int] = None
    divergence: Optional[Dict[str, Any]] = None


def _read_json(path: str) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _first_divergence_events(
    a_events: List[Dict[str, Any]],
    b_events: List[Dict[str, Any]],
) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
    """Find first divergence in event lists."""
    n = min(len(a_events), len(b_events))
    for i in range(n):
        if a_events[i] != b_events[i]:
            return i, {"a": a_events[i], "b": b_events[i]}
    if len(a_events) != len(b_events):
        return n, {"a": {"_len": len(a_events)}, "b": {"_len": len(b_events)}}
    return None, None


def _json_diff(a: Any, b: Any, path: str = "") -> List[Dict[str, Any]]:
    """
    Tiny deterministic diff:
      - compares dict/list/scalars
      - returns list of {path, a, b} for first-level differences
    """
    diffs: List[Dict[str, Any]] = []

    if isinstance(a, dict) and isinstance(b, dict):
        keys = sorted(set(a.keys()) | set(b.keys()))
        for k in keys:
            p = f"{path}.{k}" if path else str(k)
            if k not in a:
                diffs.append({"path": p, "a": None, "b": b.get(k)})
            elif k not in b:
                diffs.append({"path": p, "a": a.get(k), "b": None})
            else:
                diffs.extend(_json_diff(a.get(k), b.get(k), p))
        return diffs

    if isinstance(a, list) and isinstance(b, list):
        n = min(len(a), len(b))
        for i in range(n):
            p = f"{path}[{i}]"
            diffs.extend(_json_diff(a[i], b[i], p))
        if len(a) != len(b):
            diffs.append({"path": f"{path}._len", "a": len(a), "b": len(b)})
        return diffs

    if a != b:
        diffs.append({"path": path or "$", "a": a, "b": b})
    return diffs


def _normalize_trendpack_for_comparison(tp: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize TrendPack for deterministic comparison.

    Strips path-dependent fields (result_ref.results_pack) that vary
    between artifact directories but don't affect semantic content.
    """
    import copy
    normalized = copy.deepcopy(tp)

    # Normalize timeline events
    for event in normalized.get("timeline", []):
        meta = event.get("meta", {})
        result_ref = meta.get("result_ref", {})
        if "results_pack" in result_ref:
            # Normalize to just filename, stripping directory
            path = result_ref["results_pack"]
            result_ref["results_pack"] = Path(path).name if path else path

    return normalized


def _compute_normalized_trendpack_hash(trendpack_path: str) -> str:
    """
    Compute hash of normalized TrendPack content.

    Normalizes path-dependent fields before hashing for deterministic comparison.
    """
    import hashlib
    tp = _read_json(trendpack_path)
    normalized = _normalize_trendpack_for_comparison(tp)
    b = json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(b).hexdigest()


def dozen_run_tick_invariance_gate(
    *,
    base_artifacts_dir: str,
    runs: int = 12,
    # run_once must return Abraxas tick output dict that includes:
    # out["artifacts"]["trendpack"] and out["artifacts"]["trendpack_sha256"]
    # out["artifacts"]["run_header"] and out["artifacts"]["run_header_sha256"]
    run_once: Callable[[int, str], Dict[str, Any]],
) -> DozenRunGateResult:
    """
    Abraxas runtime invariance gate (artifact-level).

    Runs the same tick N times in isolated artifact directories:
      base_artifacts_dir/dozen_gate/run_XX/...

    PASS iff:
      1. All normalized trendpack content is identical (excludes path-dependent fields)
      2. All run_header_sha256 are identical

    On FAIL, reads the baseline and mismatched artifact JSON and reports divergence.
    For RunHeader mismatch, produces field-level drift diff (git/env/policy/bindings).

    Note: TrendPack comparison uses normalized hashes that strip path-dependent content
    (like result_ref.results_pack paths) since each run uses a different artifacts_dir.
    """
    base = Path(base_artifacts_dir) / "dozen_gate"
    base.mkdir(parents=True, exist_ok=True)

    sha256s: List[str] = []
    normalized_sha256s: List[str] = []
    trendpack_paths: List[str] = []
    runheader_sha256s: List[str] = []
    runheader_paths: List[str] = []

    for i in range(runs):
        run_dir = str(base / f"run_{i:02d}")
        out = run_once(i, run_dir)

        artifacts = out.get("artifacts", {}) or {}
        tp = artifacts.get("trendpack")
        h = artifacts.get("trendpack_sha256")
        rh = artifacts.get("run_header")
        rh_h = artifacts.get("run_header_sha256")

        if not tp or not h:
            raise ValueError("run_once must return artifacts with trendpack and trendpack_sha256")
        if not rh or not rh_h:
            raise ValueError("run_once must return artifacts with run_header and run_header_sha256")

        trendpack_paths.append(str(tp))
        sha256s.append(str(h))
        # Compute normalized hash for deterministic comparison
        normalized_sha256s.append(_compute_normalized_trendpack_hash(str(tp)))
        runheader_paths.append(str(rh))
        runheader_sha256s.append(str(rh_h))

    expected = sha256s[0]
    expected_normalized = normalized_sha256s[0]
    expected_rh = runheader_sha256s[0]

    # Check TrendPack invariance using normalized hashes (path-independent)
    for i, h in enumerate(normalized_sha256s):
        if h != expected_normalized:
            a = _read_json(trendpack_paths[0])
            b = _read_json(trendpack_paths[i])

            # Normalize for comparison
            a_norm = _normalize_trendpack_for_comparison(a)
            b_norm = _normalize_trendpack_for_comparison(b)

            a_events = a_norm.get("timeline", []) or []
            b_events = b_norm.get("timeline", []) or []

            ev_i, diff = _first_divergence_events(a_events, b_events)
            return DozenRunGateResult(
                ok=False,
                expected_sha256=expected,
                sha256s=sha256s,
                expected_runheader_sha256=expected_rh,
                runheader_sha256s=runheader_sha256s,
                first_mismatch_run=i,
                divergence={
                    "kind": "trendpack_content_mismatch",
                    "event_index": ev_i,
                    "diff": diff,
                    "baseline_trendpack": trendpack_paths[0],
                    "mismatch_trendpack": trendpack_paths[i],
                    "note": "Comparison uses normalized content (path-independent)",
                },
            )

    # TrendPack invariant passed; now enforce RunHeader invariance
    for i, rh_h in enumerate(runheader_sha256s):
        if rh_h != expected_rh:
            a = _read_json(runheader_paths[0])
            b = _read_json(runheader_paths[i])
            diffs = _json_diff(a, b)
            return DozenRunGateResult(
                ok=False,
                expected_sha256=expected,
                sha256s=sha256s,
                expected_runheader_sha256=expected_rh,
                runheader_sha256s=runheader_sha256s,
                first_mismatch_run=i,
                divergence={
                    "kind": "runheader_sha256_mismatch",
                    "baseline_runheader": runheader_paths[0],
                    "mismatch_runheader": runheader_paths[i],
                    # keep it bounded: return first 25 diffs deterministically
                    "diffs": diffs[:25],
                },
            )

    return DozenRunGateResult(
        ok=True,
        expected_sha256=expected,
        sha256s=sha256s,
        expected_runheader_sha256=expected_rh,
        runheader_sha256s=runheader_sha256s,
    )


__all__ = [
    "DozenRunGateResult",
    "dozen_run_tick_invariance_gate",
]
