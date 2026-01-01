"""Trust Index (TI) — stability under pressure metric.

Concept: Trust is not accuracy. Trust = stability under pressure.

Gives Abraxas a numerical intuition about itself - which runes can be
trusted under load, which degrade under stress.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from abx.intel_bridge import load, emit


def main() -> None:
    """Generate trust index from confidence and pressure."""
    confidence = load("confidence_decay.json")
    pressure = load("symbolic_pressure.json")

    trust: dict[str, dict[str, any]] = {}

    for rid, c in confidence.items():
        p = pressure.get(rid, {})
        base_confidence = c.get("confidence_score", 1.0)

        # Pressure penalizes trust
        # High pressure = reduced trust even if current confidence is high
        pressure_penalty = p.get("pressure_score", 0.0) * 0.5
        trust_score = max(0.0, base_confidence - pressure_penalty)

        trust[rid] = {
            "trust_index": round(trust_score, 4),
            "base_confidence": round(base_confidence, 4),
            "pressure_penalty": round(pressure_penalty, 4),
            "trust_class": _classify_trust(trust_score),
            "confidence_detail": {
                "invocations": c.get("invocations", 0),
                "error_rate": c.get("error_rate", 0.0),
                "stability": c.get("stability", "unknown"),
            },
            "pressure_detail": {
                "pressure_score": p.get("pressure_score", 0.0),
                "latency_spread": p.get("latency_spread", 0.0),
                "pressure_class": p.get("pressure_class", "unknown"),
            },
        }

    # Emit intelligence artifact
    path = emit("trust_index.json", trust)
    print(f"Trust index written to: {path}")
    print(f"Analyzed {len(trust)} runes")

    # Console summary
    if trust:
        print("\nTrust index scores:")
        for rid in sorted(trust.keys(), key=lambda r: trust[r]["trust_index"], reverse=True):
            t = trust[rid]
            score = t["trust_index"]
            tclass = t["trust_class"]
            print(f"  {rid}: {score:.3f} ({tclass})")

        # Flag low-trust runes
        low_trust = [rid for rid, t in trust.items() if t["trust_index"] < 0.5]
        if low_trust:
            print(f"\n⚠️  Low-trust runes ({len(low_trust)}):")
            for rid in low_trust:
                t = trust[rid]
                print(f"  {rid}: trust={t['trust_index']:.3f}, confidence={t['base_confidence']:.3f}, pressure={t['pressure_detail']['pressure_score']:.3f}")


def _classify_trust(score: float) -> str:
    """Classify trust level."""
    if score >= 0.90:
        return "excellent"
    elif score >= 0.75:
        return "high"
    elif score >= 0.60:
        return "good"
    elif score >= 0.40:
        return "fair"
    elif score >= 0.20:
        return "low"
    else:
        return "critical"


if __name__ == "__main__":
    main()
