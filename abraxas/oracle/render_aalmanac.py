from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from aal_core.aalmanac.scoring import priority_score


def _select_top(entries: Iterable[Dict[str, Any]], *, limit: int = 5) -> List[Dict[str, Any]]:
    sorted_entries = sorted(
        entries,
        key=lambda e: (
            -float((e.get("drift", {}) or {}).get("drift_charge", 0.0) or 0.0),
            -priority_score(e),
            str(e.get("term_canonical", "")),
            str(e.get("entry_id", "")),
        ),
    )
    return sorted_entries[:limit]


def _format_term(entry: Dict[str, Any]) -> str:
    term = str(entry.get("term_raw", ""))
    definition = str(entry.get("definition", ""))
    drift = entry.get("drift", {}) or {}
    drift_charge = float(drift.get("drift_charge", 0.0) or 0.0)
    delta = float(drift.get("delta_from_prior", 0.0) or 0.0)
    mutation = str(entry.get("mutation_type", ""))
    ctx = entry.get("usage_context", {}) or {}
    domain = str(ctx.get("domain", ""))
    header = f"• {term} — {definition}".strip()
    meta = f"  Drift: {drift_charge:.2f}  (Δ {delta:+.2f})"
    tail = f"  Mutation: {mutation} | Domain: {domain}".strip()
    return "\n".join([header, meta, tail])


def render_aalmanac_block(
    entries: Iterable[Dict[str, Any]],
    *,
    rejections: Optional[Dict[str, Any]] = None,
    top_threshold: float = 0.70,
    watchlist_min: float = 0.55,
    watchlist_max: float = 0.70,
) -> str:
    entries_list = list(entries)
    top_single = [
        e
        for e in entries_list
        if e.get("term_class") == "single"
        and float((e.get("drift", {}) or {}).get("drift_charge", 0.0) or 0.0) >= top_threshold
    ]
    top_compound = [
        e
        for e in entries_list
        if e.get("term_class") in {"compound", "phrase"}
        and float((e.get("drift", {}) or {}).get("drift_charge", 0.0) or 0.0) >= top_threshold
    ]

    watchlist = []
    for entry in entries_list:
        drift_charge = float((entry.get("drift", {}) or {}).get("drift_charge", 0.0) or 0.0)
        if watchlist_min <= drift_charge < watchlist_max:
            term = str(entry.get("term_canonical", ""))
            if entry.get("mutation_type") == "context_shift":
                term = f"{term} (sense shift)"
            if term:
                watchlist.append(term)

    lines = [
        "────────────────────────────────",
        "AALMANAC — DRIFT & EMERGENCE",
        "",
        "TOP SINGLE (MUTATED)",
    ]
    if top_single:
        for entry in _select_top(top_single, limit=5):
            lines.append(_format_term(entry))
    else:
        lines.append("• none")

    lines.extend(["", "TOP COMPOUND"])
    if top_compound:
        for entry in _select_top(top_compound, limit=5):
            lines.append(_format_term(entry))
    else:
        lines.append("• none")

    lines.extend(["", "WATCHLIST (HIGH DRIFT)"])
    if watchlist:
        lines.append("• " + "   • ".join(watchlist))
    else:
        lines.append("• none")

    lines.append("")
    lines.append("REJECTIONS (SUMMARY)")
    if rejections:
        total = int(rejections.get("total", 0) or 0)
        reasons = rejections.get("reasons", {}) or {}
        reasons_list = ", ".join(sorted(reasons.keys())) if reasons else "none"
        lines.append(f"• {total} rejected — reasons: {reasons_list}")
    else:
        lines.append("• 0 rejected — reasons: none")

    lines.append("────────────────────────────────")
    return "\n".join(lines)


def render_aalmanac_attachment(
    entries: Iterable[Dict[str, Any]],
    *,
    rejections: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    entries_list = list(entries)
    singles = [e for e in entries_list if e.get("term_class") == "single"]
    compounds = [e for e in entries_list if e.get("term_class") in {"compound", "phrase"}]

    drift_vals = [float((e.get("drift", {}) or {}).get("drift_charge", 0.0) or 0.0) for e in entries_list]
    mean_drift = sum(drift_vals) / len(drift_vals) if drift_vals else 0.0

    payload: Dict[str, Any] = {
        "top_single": [str(e.get("term_raw", "")) for e in _select_top(singles) if e.get("term_raw")],
        "top_compound": [str(e.get("term_raw", "")) for e in _select_top(compounds) if e.get("term_raw")],
        "watchlist": [
            str(e.get("term_canonical", ""))
            for e in entries_list
            if float((e.get("drift", {}) or {}).get("drift_charge", 0.0) or 0.0) > 0.7
        ],
        "meta": {
            "total_new": sum(1 for e in entries_list if e.get("mutation_type") == "neologism"),
            "total_mutations": sum(1 for e in entries_list if e.get("mutation_type") != "neologism"),
            "mean_drift_charge": mean_drift,
        },
    }
    if rejections:
        payload["rejections"] = rejections
    return payload
