from __future__ import annotations

from typing import Any, Dict, List


def _render_list(items: List[str]) -> str:
    if not items:
        return "- (none)"
    return "\n".join([f"- {item}" for item in items])


def render_oracle_markdown(readout: Dict[str, Any], tier: str) -> str:
    header = readout.get("header", {})
    vector_mix = readout.get("vector_mix", {})
    kairos = readout.get("kairos", {})
    runic_weather = readout.get("runic_weather", {})
    gate_and_trial = readout.get("gate_and_trial", [])
    futurecast = readout.get("memetic_futurecast", {})
    financials = readout.get("financials", {})

    lines = [
        f"# Oracle Readout ({tier})",
        "",
        f"**Date:** {header.get('date', 'unknown')}",
        f"**Location:** {header.get('location', 'unknown')}",
        f"**Headline:** {header.get('headline', '')}",
        "",
        "## Vector Mix",
    ]

    for key in sorted(vector_mix.keys()):
        lines.append(f"- **{key}**: {vector_mix[key]}")

    lines.extend([
        "",
        "## Kairos",
        f"- **Axis of Fate**: {kairos.get('axis_of_fate', '')}",
        f"- **Framebreaker**: {kairos.get('framebreaker', '')}",
        f"- **Continuum Binder**: {kairos.get('continuum_binder', '')}",
        f"- **Silent Sovereign**: {kairos.get('silent_sovereign', '')}",
        "",
        "## Runic Weather",
    ])

    active = runic_weather.get("active", [])
    lines.append(_render_list([str(x) for x in active]))

    interpretations = runic_weather.get("interpretations", [])
    if interpretations:
        lines.append("")
        lines.append("**Interpretations**")
        for item in interpretations:
            rune = item.get("rune", "")
            short = item.get("short", "")
            lines.append(f"- **{rune}**: {short}")

    lines.extend([
        "",
        "## Gate & Trial",
        _render_list([str(x) for x in gate_and_trial]),
        "",
        "## Memetic Futurecast",
    ])

    items = futurecast.get("items", [])
    lines.append(_render_list([str(x) for x in items]))

    lines.extend([
        "",
        "## Financials",
    ])

    macro = financials.get("macro", [])
    lines.append("**Macro**")
    lines.append(_render_list([str(x) for x in macro]))

    if financials.get("tickers"):
        lines.append("")
        lines.append("**Tickers**")
        lines.append(_render_list([str(x) for x in financials.get("tickers", [])]))

    if financials.get("crypto"):
        lines.append("")
        lines.append("**Crypto**")
        lines.append(_render_list([str(x) for x in financials.get("crypto", [])]))

    if financials.get("risk_note"):
        lines.append("")
        lines.append(f"**Risk Note**: {financials.get('risk_note')}")

    return "\n".join(lines).strip() + "\n"
