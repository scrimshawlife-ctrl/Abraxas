from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional


def render_neon_genie_block(signal: Optional[Dict[str, Any]]) -> Optional[str]:
    if not signal:
        return None
    outputs = signal.get("outputs", []) or []
    gates = signal.get("gates", {}) or {}
    source_pressures = signal.get("source_pressures", []) or []

    lines: List[str] = []
    if outputs:
        lines.extend([
            "────────────────────────────────",
            "NEON GENIE — INVENTION SIGNAL",
            "",
            "SOURCE PRESSURES",
        ])
        if source_pressures:
            for item in source_pressures[:6]:
                term = str(item.get("term", ""))
                drift = float(item.get("drift_charge", 0.0) or 0.0)
                lines.append(f"• {term} ({drift:.2f})")
        else:
            lines.append("• none")

        for out in outputs:
            kind = str(out.get("type", "")).replace("_", " ").upper()
            lines.extend(["", kind])
            name = str(out.get("name", ""))
            desc = str(out.get("description", ""))
            if name:
                lines.append(f"• \"{name}\"")
            if desc:
                lines.append(f"  {desc}")
            build_vector = out.get("build_vector", []) or []
            if build_vector:
                lines.append("  BUILD VECTOR")
                for item in build_vector:
                    lines.append(f"  • {item}")
    else:
        lines.extend([
            "────────────────────────────────",
            "NEON GENIE — SYSTEM UPGRADES (NO NEW APPS)",
            "",
        ])
        lines.append("• none")

    if gates:
        lines.extend([
            "",
            "GATE STATUS",
            f"• Drift Density: {bool(gates.get('drift_density'))}",
            f"• Cross-Domain Tension: {bool(gates.get('cross_domain_tension'))}",
            f"• Unserved Vector: {bool(gates.get('unserved_vector'))}",
        ])

    lines.append("────────────────────────────────")
    return "\n".join(lines)
