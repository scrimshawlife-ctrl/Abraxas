from __future__ import annotations

import re
from typing import Any, Dict, List


def _clamp01(x: float) -> float:
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return float(x)


_SUS_DOMAINS = (
    "pastebin.",
    "telegra.ph",
    "substack.com",
    "medium.com",
    "t.me/",
    "telegram.",
    "rumble.com",
    "bitchute.com",
)


def _has_any(s: str, subs: List[str]) -> bool:
    s = (s or "").lower()
    return any(x in s for x in subs)


def mav_for_event(ev: Dict[str, Any]) -> Dict[str, Any]:
    """
    Media Authenticity Vector (MAV) — label-only heuristics.
    """
    kind = str(ev.get("kind") or "")
    source = str(ev.get("source") or "")
    tags = ev.get("tags") if isinstance(ev.get("tags"), list) else []
    weight = float(ev.get("weight") or 0.0)

    signals: List[str] = []

    prov = 0.35
    if "primary" in tags or "official" in tags or "transcript" in tags or "filing" in tags:
        prov += 0.35
        signals.append("PRIMARY_OR_OFFICIAL")
    if "gov" in tags or "edu" in tags or "sec" in tags or "court" in tags:
        prov += 0.20
        signals.append("HIGH_TRUST_DOMAIN_TAG")
    if "provenance_drought" in tags:
        prov -= 0.18
        signals.append("PROVENANCE_DROUGHT_TAG")

    syn = 0.22
    if kind == "file":
        syn += 0.06
    if kind == "note":
        syn += 0.10
        signals.append("NOTE_IS_NOT_EVIDENCE")

    if kind == "url":
        s = source.lower()
        if _has_any(s, list(_SUS_DOMAINS)):
            syn += 0.10
            signals.append("SOCIAL_OR_PASTE_HOSTING")
        if "filetype=pdf" in s or s.endswith(".pdf"):
            prov += 0.08
            syn -= 0.05
            signals.append("PDF_BIAS_TOWARD_PROVENANCE")
        if re.search(r"\bai\b|\bdeepfake\b|\bsynth(et)?ic\b|\bgenerated\b", s):
            syn += 0.10
            signals.append("AI_KEYWORD_IN_URL")

    tpl = 0.18
    if "template" in tags or "copy" in tags or "paste" in tags or "script" in tags:
        tpl += 0.35
        signals.append("TEMPLATE_TAG")
    if "bot" in tags or "astroturf" in tags:
        tpl += 0.22
        syn += 0.10
        signals.append("BOT_OR_ASTROTURF_TAG")

    prov += 0.10 * _clamp01(weight)

    prov = _clamp01(prov)
    syn = _clamp01(syn)
    tpl = _clamp01(tpl)

    return {
        "synthetic_likelihood": float(syn),
        "provenance_integrity": float(prov),
        "template_reuse_risk": float(tpl),
        "signals": signals,
        "notes": "MAV is heuristic + label-only; not a truth verdict.",
    }
