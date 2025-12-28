#!/usr/bin/env python3
"""Apply intelligence-based weights to slang candidates."""

import json
from pathlib import Path
from abraxas.slang.weighting import build_weight_table

SLANG_DIR = Path("data/slang")
SLANG_DIR.mkdir(parents=True, exist_ok=True)

CANDIDATE_FILES = [
    SLANG_DIR / "candidates.json",
    SLANG_DIR / "slang_candidates.json",
    SLANG_DIR / "emergent_slang.json",
]

def load_candidates():
    for p in CANDIDATE_FILES:
        if p.exists():
            return p, json.loads(p.read_text(encoding="utf-8"))
    return None, {}

def apply_weights(candidates: dict, weights: dict) -> dict:
    """
    Expected candidate format (best-effort):
      { "items": [ { "term": "...", "score": 0.0..1.0, "source_rune_id": "..." , ...}, ... ] }
    If shape differs, we pass-through with minimal transformation.
    """
    out = {"items": []}
    items = candidates.get("items")
    if not isinstance(items, list):
        # unknown format; return wrapped raw
        return {"raw": candidates, "note": "unknown_candidate_shape_no_weighting_applied"}

    for it in items:
        if not isinstance(it, dict):
            continue
        rid = it.get("source_rune_id") or it.get("rune_id") or "unknown"
        base = it.get("score")
        w = (weights.get(rid) or {}).get("weight", 1.0)
        if isinstance(base, (int, float)):
            weighted = round(max(0.0, min(1.0, base * w)), 6)
        else:
            weighted = None

        o = dict(it)
        o["weight"] = w
        o["weighted_score"] = weighted
        o["weight_reasons"] = (weights.get(rid) or {}).get("reasons", [])
        out["items"].append(o)

    # sort by weighted_score when possible
    out["items"].sort(key=lambda x: (x.get("weighted_score") is None, -(x.get("weighted_score") or 0.0)))
    return out

def main():
    weights = build_weight_table()
    src_path, candidates = load_candidates()

    report = {
        "weights_count": len(weights),
        "candidates_source": str(src_path) if src_path else None,
        "note": "Weights derived from data/intel/*.json (trust, pressure, drift)."
    }
    (SLANG_DIR / "weight_report.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    weighted = apply_weights(candidates, weights)
    (SLANG_DIR / "weighted_slang_candidates.json").write_text(json.dumps(weighted, indent=2, sort_keys=True), encoding="utf-8")

    print(str(SLANG_DIR / "weighted_slang_candidates.json"))

if __name__ == "__main__":
    main()
