from __future__ import annotations

import argparse
import glob
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from abx.goodhart_guard import apply_goodhart_to_observed_gain


def _read_jsonl(path: str) -> List[Dict[str, Any]]:
    if not path or not os.path.exists(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                if isinstance(d, dict):
                    out.append(d)
            except Exception:
                continue
    return out


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _as_float(x: Any) -> float:
    try:
        return float(x)
    except Exception:
        return 0.0


def _mean(vals: List[float]) -> float:
    if not vals:
        return 0.0
    return sum(vals) / float(len(vals))


def _snapshot_vec(s: Dict[str, Any]) -> Dict[str, float]:
    cal = s.get("CAL") if isinstance(s.get("CAL"), dict) else {}
    pdg = s.get("PDG") if isinstance(s.get("PDG"), dict) else {}
    sdg = s.get("SDG") if isinstance(s.get("SDG"), dict) else {}
    return {
        "SIG_scalar": _as_float(s.get("SIG_scalar")),
        "MAE": _as_float(cal.get("mae")),
        "BRIER": _as_float(cal.get("brier_red_within_horizon")),
        "PDG_anchors": _as_float(pdg.get("avg_primary_anchors_per_term")),
        "PDG_domains": _as_float(pdg.get("avg_unique_domains_per_term")),
        "PDG_tests": _as_float(pdg.get("avg_falsification_tests_per_term")),
        "SDG_stability": _as_float(sdg.get("slang_bucket_stability")),
        "TAU": _as_float(cal.get("tau_half_life_days")),
    }


def compute_outcomes(
    *,
    task_ledger_path: str,
    sig_snapshots_path: str,
    default_after_snaps: int = 6,
) -> Dict[str, Any]:
    tasks = [e for e in _read_jsonl(task_ledger_path) if str(e.get("kind") or "") == "task_completed"]
    snaps = [e for e in _read_jsonl(sig_snapshots_path) if str(e.get("kind") or "") == "sig_snapshot"]
    # sort by ts
    tasks.sort(key=lambda d: str(d.get("ts") or ""))
    snaps.sort(key=lambda d: str(d.get("ts") or ""))

    # Optional PIS-based quality (preferred) for anti-Goodhart adjustment
    proof_integrity_path = ""
    quality = {}
    try:
        pis = sorted(glob.glob(os.path.join("out/reports", "proof_integrity_*.json")))
        proof_integrity_path = pis[-1] if pis else ""
    except Exception:
        proof_integrity_path = ""
    if proof_integrity_path:
        try:
            with open(proof_integrity_path, "r", encoding="utf-8") as f:
                q = json.load(f)
            if isinstance(q, dict):
                # Convert PIS into a penalty shape compatible with apply_goodhart...
                pis_val = float(q.get("PIS") or 0.0)
                # lower PIS => higher penalty
                quality = {"penalty": float(max(0.0, min(0.40, (1.0 - max(0.0, min(1.0, pis_val))) * 0.40))), "PIS": pis_val}
        except Exception:
            quality = {}

    if not tasks or not snaps:
        return {
            "version": "task_outcomes.v0.1",
            "ts": _utc_now_iso(),
            "error": "Need both task_completed events and sig_snapshot events.",
            "n_tasks": len(tasks),
            "n_snaps": len(snaps),
        }

    # Build snapshot timeline vectors
    snap_times = [str(s.get("ts") or "") for s in snaps]
    snap_vecs = [_snapshot_vec(s) for s in snaps]

    outcomes = []
    for t in tasks:
        t_ts = str(t.get("ts") or "")
        after_n = int(((t.get("result_window") or {}) if isinstance(t.get("result_window"), dict) else {}).get("after_runs") or default_after_snaps)

        # find last snapshot at or before task time
        before_idx = -1
        for i, st in enumerate(snap_times):
            if st <= t_ts:
                before_idx = i
            else:
                break
        if before_idx < 0:
            # no before snapshot; skip
            continue

        after_start = min(len(snaps) - 1, before_idx + 1)
        after_end = min(len(snaps), after_start + max(1, after_n))
        after_vecs = snap_vecs[after_start:after_end]
        if not after_vecs:
            continue

        before = snap_vecs[before_idx]
        after_mean = {k: _mean([v.get(k, 0.0) for v in after_vecs]) for k in before.keys()}

        # deltas: we want MAE/BRIER to go DOWN (improvement), others up
        delta = {}
        for k in before.keys():
            delta[k] = float(after_mean.get(k, 0.0) - before.get(k, 0.0))

        # improvement scalar (signed so positive = better)
        # -MAE, -BRIER, +anchors,+domains,+tests,+stability, (TAU not scored)
        improvement = (
            1.2 * (-delta.get("MAE", 0.0))
            + 0.9 * (-delta.get("BRIER", 0.0))
            + 0.25 * (delta.get("PDG_anchors", 0.0))
            + 0.15 * (delta.get("PDG_domains", 0.0))
            + 0.15 * (delta.get("PDG_tests", 0.0))
            + 0.35 * (delta.get("SDG_stability", 0.0))
            + 0.60 * (delta.get("SIG_scalar", 0.0))
        )

        # Apply anti-Goodhart penalty if quality computed
        adjusted = apply_goodhart_to_observed_gain(float(max(-1.5, min(1.5, improvement))), quality) if isinstance(quality, dict) and quality else float(max(-1.5, min(1.5, improvement)))

        outcomes.append({
            "task_id": t.get("task_id"),
            "ts": t_ts,
            "run_id": t.get("run_id"),
            "term": t.get("term"),
            "task_type": t.get("task_type"),
            "dominant_driver": t.get("dominant_driver"),
            "ml": t.get("ml"),
            "cost": t.get("cost"),
            "evidence": t.get("evidence"),
            "before_snapshot_ts": snaps[before_idx].get("ts"),
            "after_window": {"start_ts": snaps[after_start].get("ts"), "end_ts": snaps[after_end - 1].get("ts"), "n": int(after_end - after_start)},
            "before": before,
            "after_mean": after_mean,
            "delta": delta,
            "observed_gain_raw": float(max(-1.5, min(1.5, improvement))),
            "observed_gain": float(adjusted),
            "goodhart": {"proof_integrity_path": proof_integrity_path, "quality": quality} if quality else None,
            "notes": "Observed gain computed from before snapshot and mean of after window. Positive observed_gain indicates improvement.",
        })

    # sort by observed_gain descending
    outcomes.sort(key=lambda d: -float(d.get("observed_gain") or 0.0))
    return {
        "version": "task_outcomes.v0.1",
        "ts": _utc_now_iso(),
        "task_ledger": task_ledger_path,
        "sig_snapshots": sig_snapshots_path,
        "n_outcomes": len(outcomes),
        "outcomes": outcomes,
        "notes": "Use outcomes as empirical labels to train ROI weights.",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Compute task outcomes from task ledger + sig snapshot ledger")
    ap.add_argument("--task-ledger", default="out/ledger/task_ledger.jsonl")
    ap.add_argument("--sig-ledger", default="out/ledger/sig_snapshots.jsonl")
    ap.add_argument("--out", default="")
    ap.add_argument("--default-after-snaps", type=int, default=6)
    args = ap.parse_args()

    obj = compute_outcomes(task_ledger_path=args.task_ledger, sig_snapshots_path=args.sig_ledger, default_after_snaps=int(args.default_after_snaps))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = args.out or os.path.join("out/reports", f"task_outcomes_{stamp}.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    print(f"[TASK_OUTCOMES] wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
