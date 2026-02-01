from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
import json

VEC_DIR = Path("aal_core/runes/game_theory/vectors")


def load_pack_game_theory_v1(pack_id: str) -> Dict[str, Any]:
    if pack_id != "aal.rune.game_theory.pack.v1":
        return {"vectors": [], "corpus": {}}

    vectors: List[Dict[str, Any]] = []
    for p in sorted(VEC_DIR.glob("*.jsonl")):
        lines = p.read_text(encoding="utf-8").splitlines()
        for ln in lines:
            if ln.strip():
                vectors.append(json.loads(ln))
    return {"vectors": vectors, "corpus": {"pack": "game_theory_v1"}}


def eval_game_theory_v1(
    vectors_subset: List[Dict[str, Any]],
    training_ir: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Minimal evaluator: checks whether expected equilibria exist + counts.
    This is NOT a solver yet; it's an invariance + comprehension harness.
    """
    ok = 0
    checks = 0
    notes = []

    for v in vectors_subset:
        checks += 1
        exp = v.get("expected", {})
        eq = exp.get("equilibria", [])
        if isinstance(eq, list) and len(eq) >= 1:
            ok += 1
        else:
            notes.append({"vector_id": v.get("vector_id"), "issue": "missing expected equilibria"})

    score = ok / max(1, checks)
    return {
        "score": score,
        "findings": {
            "checks": checks,
            "ok": ok,
            "notes": notes,
            "guardrail": (
                "This evaluator validates pack integrity; a Nash solver is a separate governed module."
            ),
        },
    }
