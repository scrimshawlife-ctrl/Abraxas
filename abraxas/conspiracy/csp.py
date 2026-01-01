from __future__ import annotations

from typing import Any, Dict, List

from abraxas.conspiracy.schema import CSPResult


def _clamp(x: float) -> float:
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return float(x)


def _bucket_to_num(bucket: str) -> float:
    bucket = (bucket or "UNKNOWN").upper()
    if bucket == "LOW":
        return 0.25
    if bucket == "MED":
        return 0.55
    if bucket == "HIGH":
        return 0.80
    return 0.50


def infer_coh(text: str) -> bool:
    """
    Coordination Hypothesis flag.
    Neutral: detects coordination language without judging truth.
    """
    text = (text or "").lower()
    keys = [
        "collude",
        "collusion",
        "coordinat",
        "conspire",
        "conspiracy",
        "cover-up",
        "coverup",
        "false flag",
        "psyop",
        "operation",
        "cabal",
        "plot",
        "scheme",
        "orchestrated",
        "staged",
        "manufactured",
        "astroturf",
        "blackmail",
        "payoff",
    ]
    return any(k in text for k in keys)


def compute_ea_from_profile(profile: Dict[str, Any]) -> float:
    """
    Evidence Adequacy: uses attribution + diversity (uplifted if present).
    Does not incorporate agreement (consensus) directly.
    """
    att = float(
        profile.get("attribution_strength_uplifted")
        or profile.get("attribution_strength")
        or 0.0
    )
    div = float(
        profile.get("source_diversity_uplifted")
        or profile.get("source_diversity")
        or 0.0
    )
    ea = 0.58 * att + 0.42 * div
    return _clamp(ea)


def compute_ff_from_profile(profile: Dict[str, Any]) -> float:
    """
    Falsifiability / Fork resistance proxy:
      - lower consensus gap helps
      - higher provenance helps
      - high manipulation risk lowers FF (more narrative steering / fork proliferation)
    """
    consensus_gap = float(profile.get("consensus_gap_term") or 0.0)
    manipulation_risk = float(profile.get("manipulation_risk") or 0.0)
    ea = compute_ea_from_profile(profile)

    ff = (
        0.50 * (1.0 - _clamp(consensus_gap))
        + 0.35 * ea
        + 0.15 * (1.0 - _clamp(manipulation_risk))
    )
    return _clamp(ff)


def compute_mio_from_context(
    *,
    dmx_bucket: str,
    dmx_overall: float,
    term_class: str,
    channel_kind: str = "",
) -> float:
    """
    Manipulation/Operation Pressure:
      - primarily DMX overall + bucket
      - term class increases sensitivity
      - channel kind adjusts
    """
    score = 0.55 * _clamp(dmx_overall) + 0.25 * _bucket_to_num(dmx_bucket)

    term_class = (term_class or "unknown").lower()
    if term_class == "contested":
        score += 0.12
    elif term_class == "volatile":
        score += 0.10
    elif term_class == "emerging":
        score += 0.06

    channel_kind = (channel_kind or "").lower()
    if channel_kind in ("forums", "video", "social"):
        score += 0.08
    if channel_kind in ("gov", "research"):
        score -= 0.06

    return _clamp(score)


def compute_cip_from_profile(profile: Dict[str, Any], coh: bool) -> float:
    """
    Coordination Inference Plausibility (NOT truth):
      - increases with evidence adequacy + falsifiability
      - decreases with extreme disagreement + high manipulation pressure
    If COH is absent, CIP is still computable but damped.
    """
    ea = compute_ea_from_profile(profile)
    ff = compute_ff_from_profile(profile)
    consensus_gap = float(profile.get("consensus_gap_term") or 0.0)
    manipulation_risk = float(profile.get("manipulation_risk") or 0.0)

    cip = (
        0.48 * ea
        + 0.32 * ff
        + 0.10 * (1.0 - _clamp(consensus_gap))
        + 0.10 * (1.0 - _clamp(manipulation_risk))
    )
    if not coh:
        cip *= 0.65
    return _clamp(cip)


def tag_csp(*, coh: bool, cip: float, ea: float, ff: float, mio: float) -> str:
    """
    Label-only, non-moral tags.
    """
    if mio >= 0.75 and ea <= 0.40 and ff <= 0.40:
        return "opportunistic_op" if coh else "noise_halo"

    if coh and cip >= 0.65 and ea >= 0.60 and ff >= 0.60:
        return "investigative"
    if coh and cip >= 0.55 and (ea >= 0.45 or ff >= 0.50):
        return "plausible_unproven"
    if coh and (ea < 0.45 and ff < 0.50):
        return "speculative"
    if not coh and mio >= 0.70 and ea < 0.50:
        return "noise_halo"

    return "unknown"


def compute_term_csp(
    *,
    term: str,
    profile: Dict[str, Any],
    dmx_bucket: str,
    dmx_overall: float,
    term_class: str,
) -> Dict[str, Any]:
    """
    Term-level CSP summary. COH inferred from term string only (weak), but claim-level can override.
    """
    flags: List[str] = []
    coh = infer_coh(term)
    ea = compute_ea_from_profile(profile)
    ff = compute_ff_from_profile(profile)
    mio = compute_mio_from_context(
        dmx_bucket=dmx_bucket,
        dmx_overall=dmx_overall,
        term_class=term_class,
    )
    cip = compute_cip_from_profile(profile, coh)

    if coh:
        flags.append("COH_PRESENT_TERM_HEUR")
    if ea < 0.50:
        flags.append("EA_LOW")
    if ff < 0.50:
        flags.append("FF_LOW")
    if mio >= 0.70:
        flags.append("MIO_HIGH")

    tag = tag_csp(coh=coh, cip=cip, ea=ea, ff=ff, mio=mio)
    return CSPResult(
        COH=coh,
        CIP=cip,
        EA=ea,
        FF=ff,
        MIO=mio,
        tag=tag,
        flags=flags,
    ).to_dict()


def compute_claim_csp(
    *,
    claim_text: str,
    term_csp: Dict[str, Any],
    evidence_support_weight: float = 0.0,
) -> Dict[str, Any]:
    """
    Claim-level CSP: inherits term CSP but can:
      - infer COH from claim text (stronger than term string)
      - boost EA slightly if evidence support exists
    """
    base = dict(term_csp or {})
    flags = base.get("flags") if isinstance(base.get("flags"), list) else []

    coh_claim = infer_coh(claim_text)
    if coh_claim and not bool(base.get("COH")):
        base["COH"] = True
        flags.append("COH_PRESENT_CLAIM_HEUR")

    ea = float(base.get("EA") or 0.0)
    ea = _clamp(ea + min(0.10, max(0.0, float(evidence_support_weight) * 0.25)))
    base["EA"] = ea

    cip = float(base.get("CIP") or 0.0)
    if bool(base.get("COH")):
        cip = _clamp(cip + 0.08 * (ea - float(term_csp.get("EA") or ea)))
    else:
        cip = _clamp(cip * 0.95)
    base["CIP"] = cip

    mio = float(base.get("MIO") or 0.0)
    ff = float(base.get("FF") or 0.0)
    base["tag"] = tag_csp(coh=bool(base.get("COH")), cip=cip, ea=ea, ff=ff, mio=mio)
    base["flags"] = flags
    return base
