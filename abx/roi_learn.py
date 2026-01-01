from __future__ import annotations

import argparse
import glob
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


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


def _pick_latest(out_reports: str, pattern: str) -> str:
    paths = sorted(glob.glob(os.path.join(out_reports, pattern)))
    return paths[-1] if paths else ""


def _feature_vec(ev: Dict[str, Any]) -> Dict[str, float]:
    """
    Feature vector for linear model. Small and interpretable.
    """
    tt = str(ev.get("task_type") or "")
    dom = str(ev.get("dominant_driver") or "")
    ml = ev.get("ml") if isinstance(ev.get("ml"), dict) else {}
    ml_score = float(ml.get("ml") or 0.0)
    bucket = str(ml.get("bucket") or "UNKNOWN")
    # one-hot via named features
    f: Dict[str, float] = {
        "bias": 1.0,
        "ml_score": ml_score,
        "dom_PROV_GAP": 1.0 if dom == "PROV_GAP" else 0.0,
        "dom_FOG": 1.0 if dom == "FOG" else 0.0,
        "dom_TPL": 1.0 if dom == "TPL" else 0.0,
        "dom_SYN": 1.0 if dom == "SYN" else 0.0,
        "tt_PRIMARY": 1.0 if tt == "PRIMARY_ANCHOR_SWEEP" else 0.0,
        "tt_TIMELINE": 1.0 if tt == "ORIGIN_TIMELINE" else 0.0,
        "tt_TEMPLATE": 1.0 if tt == "TEMPLATE_CAPTURE" else 0.0,
        "tt_SYNC": 1.0 if tt == "SYNC_POSTING_CHECK" else 0.0,
        "tt_AUTH": 1.0 if tt == "AUTH_CHAIN" else 0.0,
        "tt_TESTS": 1.0 if tt == "DISCONFIRM_TESTS" else 0.0,
        "bucket_MFG": 1.0 if bucket in ("LIKELY_MANUFACTURED", "COORDINATED", "ASTROTURF") else 0.0,
    }
    evd = ev.get("evidence") if isinstance(ev.get("evidence"), dict) else {}
    f["anchors_added"] = float(evd.get("anchors_added") or 0.0)
    f["domains_added"] = float(evd.get("domains_added") or 0.0)
    f["fals_tests_added"] = float(evd.get("fals_tests_added") or 0.0)
    return f


def _dot(w: Dict[str, float], x: Dict[str, float]) -> float:
    return float(sum(float(w.get(k, 0.0)) * float(v) for k, v in x.items()))


def _fit_ridge(
    X: List[Dict[str, float]],
    y: List[float],
    lam: float = 0.8,
) -> Dict[str, float]:
    """
    Tiny ridge regression using normal equations on a small feature set.
    We avoid numpy dependency; implement via feature covariance.
    """
    # Collect feature names
    feats = sorted({k for row in X for k in row.keys()})
    n = len(X)
    if n == 0 or not feats:
        return {"bias": 0.0}

    # Build covariance and XTy
    # A = X^T X + lam I
    A = {i: {j: 0.0 for j in range(len(feats))} for i in range(len(feats))}
    b = {i: 0.0 for i in range(len(feats))}
    for row, yi in zip(X, y):
        for i, fi in enumerate(feats):
            xi = float(row.get(fi, 0.0))
            b[i] += xi * float(yi)
            for j, fj in enumerate(feats):
                xj = float(row.get(fj, 0.0))
                A[i][j] += xi * xj
    for i in range(len(feats)):
        A[i][i] += float(lam)

    # Solve by naive Gauss-Jordan (small matrix)
    m = len(feats)
    # augmented matrix
    M = [[A[i][j] for j in range(m)] + [b[i]] for i in range(m)]
    for i in range(m):
        # pivot
        piv = M[i][i]
        if abs(piv) < 1e-12:
            # find swap
            for k in range(i + 1, m):
                if abs(M[k][i]) > abs(piv):
                    M[i], M[k] = M[k], M[i]
                    piv = M[i][i]
                    break
        if abs(piv) < 1e-12:
            continue
        inv = 1.0 / piv
        for j in range(i, m + 1):
            M[i][j] *= inv
        for k in range(m):
            if k == i:
                continue
            fac = M[k][i]
            if fac == 0.0:
                continue
            for j in range(i, m + 1):
                M[k][j] -= fac * M[i][j]

    w = {}
    for i, fi in enumerate(feats):
        w[fi] = float(M[i][m])
    return w


def learn_roi_weights(
    *,
    out_reports: str,
    task_ledger_path: str,
) -> Dict[str, Any]:
    """
    Learns ROI weights from empirical task outcomes.
    Prefers task_outcomes if available; falls back to proxy gains if not.
    """
    # Prefer task_outcomes labels if available
    latest_outcomes_path = _pick_latest(out_reports, "task_outcomes_*.json")
    outcomes_obj = _read_json(latest_outcomes_path) if latest_outcomes_path else {}
    outcomes = outcomes_obj.get("outcomes") if isinstance(outcomes_obj.get("outcomes"), list) else []
    if len(outcomes) < 4:
        return {
            "version": "roi_weights.v0.1",
            "ts": _utc_now_iso(),
            "error": "Need at least 4 task outcomes (run task_outcomes after logging snapshots).",
            "n_outcomes": len(outcomes),
        }

    X = []
    y = []
    for o in outcomes:
        if not isinstance(o, dict):
            continue
        # o contains task-like fields; reuse feature extractor by treating it as ev
        x = _feature_vec(o)
        og = float(o.get("observed_gain") or 0.0)
        # map observed_gain (-1.5..1.5) → gain (0..1.4) with shift+clamp
        gain = max(0.0, min(1.4, 0.70 + 0.46 * og))
        X.append(x)
        y.append(float(gain))

    w = _fit_ridge(X, y, lam=0.8)
    return {
        "version": "roi_weights.v0.1",
        "ts": _utc_now_iso(),
        "out_reports": out_reports,
        "task_ledger": task_ledger_path,
        "task_outcomes": latest_outcomes_path,
        "n": len(outcomes),
        "weights": w,
        "feature_schema": sorted({k for row in X for k in row.keys()}),
        "notes": "Trained on empirical task outcomes computed from SIG snapshots.",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Learn ROI weights from task completion ledger")
    ap.add_argument("--out-reports", default="out/reports")
    ap.add_argument("--task-ledger", default="out/ledger/task_ledger.jsonl")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    obj = learn_roi_weights(out_reports=args.out_reports, task_ledger_path=args.task_ledger)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = args.out or os.path.join(args.out_reports, f"roi_weights_{stamp}.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    print(f"[ROI_LEARN] wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
