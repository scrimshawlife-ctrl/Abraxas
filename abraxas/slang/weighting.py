# abraxas/slang/weighting.py
# Deterministic weighting for slang emergence (v0.1)
# Inputs: intel artifacts. Output: per-source weights + reason codes.

import json
from pathlib import Path
from typing import Dict, Any, Tuple

ROOT = Path(__file__).resolve().parents[2]
INTEL = ROOT / "data" / "intel"
ASC = ROOT / "data" / "adaptive_state" / "rune"

def _load(name: str) -> Dict[str, Any]:
    p = INTEL / name
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))

def _load_phase(rune_id: str) -> str | None:
    """Load lifecycle phase from ASC (optional maturity prior)."""
    p = ASC / f"{rune_id}.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8")).get("lifecycle_phase")
    except Exception:
        return None

def compute_weight(rune_id: str,
                   trust_index: float | None,
                   pressure_score: float | None,
                   drift_flag: bool) -> Tuple[float, list]:
    """
    Weight ∈ [0.05, 1.0]
    - Start from trust_index (default 1.0)
    - Penalize pressure
    - Penalize drift
    """
    reasons = []
    t = trust_index if isinstance(trust_index, (int, float)) else 1.0
    p = pressure_score if isinstance(pressure_score, (int, float)) else 0.0

    w = t
    if p > 0.0:
        # pressure penalty: up to -0.5 at p=1.0
        w = w * (1.0 - min(0.5, 0.5 * p))
        reasons.append(f"pressure_penalty(p={round(p,4)})")

    if drift_flag:
        # drift penalty: fixed multiplier
        w = w * 0.7
        reasons.append("drift_penalty(0.7x)")

    # Optional maturity prior from ASC (epistemic seniority)
    phase = _load_phase(rune_id)
    if phase == "stable":
        w = w * 1.05
        reasons.append("maturity_bonus(stable 1.05x)")
    elif phase == "volatile":
        w = w * 0.9
        reasons.append("maturity_penalty(volatile 0.9x)")

    # floor so nothing becomes zeroed-out (keeps learning possible)
    w = max(0.05, min(1.0, w))
    return (round(w, 4), reasons)

def build_weight_table() -> Dict[str, Any]:
    trust = _load("trust_index.json")
    pressure = _load("symbolic_pressure.json")
    drift = _load("semantic_drift_signal.json")

    rune_ids = set(trust.keys()) | set(pressure.keys()) | set(drift.keys())
    table = {}

    for rid in sorted(rune_ids):
        t = (trust.get(rid) or {}).get("trust_index")
        p = (pressure.get(rid) or {}).get("pressure_score")
        d = bool((drift.get(rid) or {}).get("drift_flag", False))
        w, reasons = compute_weight(rid, t, p, d)
        table[rid] = {
            "weight": w,
            "trust_index": t,
            "pressure_score": p,
            "drift_flag": d,
            "reasons": reasons
        }
    return table
