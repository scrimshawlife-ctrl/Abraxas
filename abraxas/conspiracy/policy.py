from __future__ import annotations

from typing import Dict, List, Optional, Tuple


def _order(horizon: str) -> int:
    horizon = (horizon or "").lower()
    return {"days": 0, "weeks": 1, "months": 2, "years": 3}.get(horizon, 0)


def _min_h(a: Optional[str], b: Optional[str]) -> Optional[str]:
    if not a:
        return b
    if not b:
        return a
    return a if _order(a) <= _order(b) else b


def csp_horizon_clamp(
    *,
    csp: Dict,
    dmx_bucket: str,
    term_class: str,
) -> Tuple[Optional[str], List[str]]:
    """
    Returns (cap, flags). cap is an additional max horizon constraint.
    This never expands horizon; only clamps.
    """
    flags: List[str] = []
    if not isinstance(csp, dict):
        return None, flags

    mio = float(csp.get("MIO") or 0.0)
    ff = float(csp.get("FF") or 0.0)
    ea = float(csp.get("EA") or 0.0)
    cip = float(csp.get("CIP") or 0.0)
    coh = bool(csp.get("COH"))

    bucket = (dmx_bucket or "UNKNOWN").upper()
    term_class = (term_class or "unknown").lower()

    if mio >= 0.75 and ff <= 0.45:
        flags.append("CSP_CLAMP_HIGH_MIO_LOW_FF")
        return "weeks", flags

    if bucket == "HIGH" and term_class in ("contested", "volatile"):
        flags.append("CSP_CLAMP_HIGH_FOG_VOLATILE_OR_CONTESTED")
        return "months", flags

    if coh and ea >= 0.60 and ff >= 0.60 and cip >= 0.65:
        flags.append("CSP_INVESTIGATIVE_NO_CLAMP")
        return None, flags

    if coh and ea < 0.45 and ff < 0.50:
        flags.append("CSP_CLAMP_SPECULATIVE_COH")
        return "months", flags

    if bucket == "HIGH" and ea < 0.40:
        flags.append("CSP_CLAMP_LOW_EA_HIGH_FOG")
        return "weeks", flags

    return None, flags


def apply_horizon_cap(
    *,
    policy_cap: Optional[str],
    csp_cap: Optional[str],
) -> Optional[str]:
    return _min_h(policy_cap, csp_cap)
