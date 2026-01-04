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
    first_mismatch_run: Optional[int] = None
    divergence: Optional[Dict[str, Any]] = None


def _read_json(path: str) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _first_divergence_events(a_events: List[Dict[str, Any]], b_events: List[Dict[str, Any]]) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
    n = min(len(a_events), len(b_events))
    for i in range(n):
        if a_events[i] != b_events[i]:
            return i, {"a": a_events[i], "b": b_events[i]}
    if len(a_events) != len(b_events):
        return n, {"a": {"_len": len(a_events)}, "b": {"_len": len(b_events)}}
    return None, None


def dozen_run_tick_invariance_gate(
    *,
    base_artifacts_dir: str,
    runs: int = 12,
    # run_once must return Abraxas tick output dict that includes:
    # out["artifacts"]["trendpack"] and out["artifacts"]["trendpack_sha256"]
    run_once: Callable[[int, str], Dict[str, Any]],
) -> DozenRunGateResult:
    """
    Abraxas runtime invariance gate (artifact-level).

    Runs the same tick N times in isolated artifact directories:
      base_artifacts_dir/dozen_gate/run_XX/...

    PASS iff all trendpack_sha256 are identical.
    On FAIL, reads the baseline and mismatched trendpack JSON and reports first divergence.
    """
    base = Path(base_artifacts_dir) / "dozen_gate"
    base.mkdir(parents=True, exist_ok=True)

    sha256s: List[str] = []
    trendpack_paths: List[str] = []

    for i in range(runs):
        run_dir = str(base / f"run_{i:02d}")
        out = run_once(i, run_dir)

        artifacts = out.get("artifacts", {}) or {}
        tp = artifacts.get("trendpack")
        h = artifacts.get("trendpack_sha256")
        if not tp or not h:
            raise ValueError("run_once must return artifacts with trendpack and trendpack_sha256")

        trendpack_paths.append(str(tp))
        sha256s.append(str(h))

    expected = sha256s[0]
    for i, h in enumerate(sha256s):
        if h != expected:
            a = _read_json(trendpack_paths[0])
            b = _read_json(trendpack_paths[i])

            a_events = a.get("timeline", []) or []
            b_events = b.get("timeline", []) or []

            ev_i, diff = _first_divergence_events(a_events, b_events)
            return DozenRunGateResult(
                ok=False,
                expected_sha256=expected,
                sha256s=sha256s,
                first_mismatch_run=i,
                divergence={
                    "event_index": ev_i,
                    "diff": diff,
                    "baseline_trendpack": trendpack_paths[0],
                    "mismatch_trendpack": trendpack_paths[i],
                },
            )

    return DozenRunGateResult(ok=True, expected_sha256=expected, sha256s=sha256s)
