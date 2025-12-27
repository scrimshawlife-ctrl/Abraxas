from __future__ import annotations

from typing import Any, Dict, List

from abraxas.disinfo.schema import DisinfoMetric


def _bucket(x: float) -> str:
    if x <= 0.33:
        return "LOW"
    if x <= 0.66:
        return "MED"
    return "HIGH"


def provenance_integrity(item: Dict[str, Any]) -> DisinfoMetric:
    """
    PI score means "provenance risk" (higher = worse provenance integrity).
    Deterministic heuristics only.
    """
    flags: List[str] = []
    refs: List[str] = []

    src = item.get("source") if isinstance(item.get("source"), dict) else {}
    url = str(src.get("url") or "")
    domain = str(src.get("domain") or "")
    author = str(src.get("author") or "")
    ts = str(src.get("published_ts") or src.get("captured_ts") or "")
    stype = str(src.get("type") or item.get("source_type") or "")

    risk = 0.0
    if not url and not item.get("source_ref"):
        risk += 0.25
        flags.append("NO_URL_OR_SOURCE_REF")
    if not domain and url:
        risk += 0.10
        flags.append("DOMAIN_MISSING")
    if not author:
        risk += 0.10
        flags.append("AUTHOR_MISSING")
    if not ts:
        risk += 0.10
        flags.append("TIMESTAMP_MISSING")

    if stype in ("gov", "research", "pdf", "dataset"):
        risk -= 0.10
        flags.append("PRIMARY_ADJ")

    if risk < 0.0:
        risk = 0.0
    if risk > 1.0:
        risk = 1.0

    if url:
        refs.append(url)
    if item.get("source_ref"):
        refs.append(str(item.get("source_ref")))

    return DisinfoMetric(
        name="PI",
        score=float(risk),
        bucket=_bucket(float(risk)),
        flags=flags,
        refs=refs,
        notes="Provenance risk (higher = less traceable).",
    )


def synthetic_media_likelihood(item: Dict[str, Any]) -> DisinfoMetric:
    """
    SML score is heuristic likelihood of synthetic/manipulated media.
    Not a detector. Higher = more suspicious.
    """
    flags: List[str] = []
    refs: List[str] = []

    src = item.get("source") if isinstance(item.get("source"), dict) else {}
    kind = str(item.get("media_kind") or src.get("media_kind") or src.get("type") or "").lower()
    url = str(src.get("url") or "")

    s = 0.10
    if kind in ("image", "video"):
        s = 0.20
        flags.append("MEDIA_ITEM")

    chain = item.get("chain") if isinstance(item.get("chain"), dict) else {}
    reposts = int(chain.get("repost_count_est") or 0)
    origin = str(chain.get("origin_url") or "")

    if kind in ("image", "video") and not origin:
        s += 0.20
        flags.append("NO_ORIGIN_URL")
    if reposts >= 10:
        s += 0.15
        flags.append("HIGH_REPOST_DENSITY")

    pi = item.get("pi") if isinstance(item.get("pi"), dict) else {}
    pi_score = float(pi.get("score") or 0.0)
    s += 0.30 * pi_score
    if pi_score >= 0.66:
        flags.append("PI_HIGH_AMPLIFIER")

    if s > 1.0:
        s = 1.0
    if s < 0.0:
        s = 0.0

    if url:
        refs.append(url)
    if origin:
        refs.append(origin)

    return DisinfoMetric(
        name="SML",
        score=float(s),
        bucket=_bucket(float(s)),
        flags=flags,
        refs=refs,
        notes="Heuristic synthetic/manipulated-media suspicion (higher = more suspicious).",
    )


def narrative_manipulation_pressure(item: Dict[str, Any]) -> DisinfoMetric:
    """
    NMP score uses macro knobs:
      - DMX fog
      - term_class
      - channel kind
      - MRI/IRI/τ if present in item context
    """
    flags: List[str] = []
    refs: List[str] = []

    ctx = item.get("context") if isinstance(item.get("context"), dict) else {}
    dmx = ctx.get("dmx") if isinstance(ctx.get("dmx"), dict) else {}
    dmx_overall = float(dmx.get("overall_manipulation_risk") or 0.0)
    bucket = str(dmx.get("bucket") or "UNKNOWN").upper()

    term_cls = str(ctx.get("term_class") or "unknown").lower()
    channel_kind = str(ctx.get("channel_kind") or "").lower()

    mri = float(ctx.get("MRI") or 0.0)
    iri = float(ctx.get("IRI") or 0.0)
    tau = float(ctx.get("tau") or ctx.get("τ") or 0.0)

    s = 0.45 * dmx_overall
    if bucket == "HIGH":
        flags.append("DMX_HIGH_FOG")
    elif bucket == "MED":
        flags.append("DMX_MED_FOG")

    if term_cls == "contested":
        s += 0.18
        flags.append("TERM_CONTESTED")
    elif term_cls == "volatile":
        s += 0.14
        flags.append("TERM_VOLATILE")
    elif term_cls == "emerging":
        s += 0.08
        flags.append("TERM_EMERGING")

    if channel_kind in ("forums", "video", "social"):
        s += 0.10
        flags.append(f"CHANNEL_{channel_kind.upper()}_RISK")
    if channel_kind in ("gov", "research"):
        s -= 0.06
        flags.append(f"CHANNEL_{channel_kind.upper()}_CREDIBLE_ADJ")

    if mri:
        s += 0.06 * max(0.0, min(1.0, mri))
        flags.append("MRI_USED")
    if iri:
        s -= 0.04 * max(0.0, min(1.0, iri))
        flags.append("IRI_USED")
    if tau:
        s += 0.04 * max(0.0, min(1.0, tau))
        flags.append("TAU_USED")

    if s < 0.0:
        s = 0.0
    if s > 1.0:
        s = 1.0

    return DisinfoMetric(
        name="NMP",
        score=float(s),
        bucket=_bucket(float(s)),
        flags=flags,
        refs=refs,
        notes="Narrative manipulation pressure (higher = more likely to be steered).",
    )
