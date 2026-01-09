"""
ABX-GT Shadow Hook (optional).
- Never governs predictions.
- Deterministic.
- Hard-fails safe: if overlay not installed, output not_computable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class ABXGTShadowResult:
    overlay: str = "abx_gt"
    version: str = "0.1"
    lane: str = "shadow"
    not_computable: bool = False
    missing: List[str] = field(default_factory=list)
    scores: Dict[str, float] = field(default_factory=dict)
    provenance: Dict[str, Any] = field(default_factory=dict)


def _fallback(reason: str) -> Dict[str, Any]:
    return {
        "overlay": "abx_gt",
        "version": "0.1",
        "lane": "shadow",
        "not_computable": True,
        "missing": [reason],
        "scores": {},
        "provenance": {"reason": reason},
    }


def try_run_abx_gt_shadow(seed: int, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    context: may include light metadata:
      - "oracle_date": "YYYY-MM-DD"
      - "location": "Los Angeles, CA"
      - "signals": { ... }  (optional)
    """
    try:
        # AAL-core overlay runner (optional install)
        from aal_core.overlays.abx_gt.runtime.abx_gt_runner import run_vector_pack  # type: ignore
    except Exception:
        return _fallback("overlay_not_installed")

    try:
        # Minimal interface:
        # - seed influences deterministic selection ordering
        # - context is folded into provenance only (never affects scores unless explicitly encoded)
        report = run_vector_pack(seed=seed, context=context)
        # report must be JSON-serializable dict
        report.setdefault("lane", "shadow")
        report.setdefault("overlay", "abx_gt")
        report.setdefault("version", "0.1")
        return report
    except Exception as e:
        return _fallback(f"runtime_error:{type(e).__name__}")
