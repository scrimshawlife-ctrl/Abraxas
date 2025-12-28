"""Memetic Weather Augment from Telemetry Intel (v0.1).

Read-only. Deterministic rules. No side effects.

Consumes intelligence artifacts (pressure, trust, drift) and produces
memetic weather signals - turning system runtime behavior into symbolic
weather patterns.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


# Paths
ROOT = Path(__file__).resolve().parents[2]
INTEL = ROOT / "data" / "intel"
OUT = ROOT / "data" / "memetic_weather"

# Ensure output directory exists
OUT.mkdir(parents=True, exist_ok=True)


def _load(name: str) -> dict[str, Any]:
    """Load an intelligence artifact (silent fallback on missing)."""
    p = INTEL / name
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _band(x: float | None, cuts: tuple[float, float, float] = (0.2, 0.5, 0.8)) -> str:
    """Stable banding for metrics.

    Args:
        x: Metric value (0.0 to 1.0)
        cuts: Cutoff points for low/medium/high/severe

    Returns:
        Band classification: low/medium/high/severe/unknown
    """
    if x is None:
        return "unknown"
    if x < cuts[0]:
        return "low"
    if x < cuts[1]:
        return "medium"
    if x < cuts[2]:
        return "high"
    return "severe"


def build_telemetry_augment() -> dict[str, Any]:
    """Build memetic weather augment from intelligence artifacts.

    Returns:
        Augment dict with per-rune metrics and storm warnings
    """
    # Load intelligence artifacts
    pressure = _load("symbolic_pressure.json")
    trust = _load("trust_index.json")
    drift = _load("semantic_drift_signal.json")

    augment: dict[str, Any] = {"runes": {}, "warnings": []}

    # Merge all rune IDs from all sources
    rune_ids = set(pressure.keys()) | set(trust.keys()) | set(drift.keys())

    for rid in sorted(rune_ids):
        p = (pressure.get(rid) or {}).get("pressure_score")
        t = (trust.get(rid) or {}).get("trust_index")
        dflag = bool((drift.get(rid) or {}).get("drift_flag", False))

        # Compute risk band (inverse of trust: low trust = high risk)
        risk_value = (1.0 - t) if isinstance(t, (int, float)) else None

        entry = {
            "pressure_score": p,
            "pressure_band": _band(p),
            "trust_index": t,
            "trust_band": _band(1.0 - t if isinstance(t, (int, float)) else None),
            "risk_band": _band(risk_value),  # Explicit risk band for clarity
            "drift_flag": dflag,
        }
        augment["runes"][rid] = entry

        # Deterministic storm warnings (rule-based, no vibes)

        # Semantic storm: drift + low trust = unstable meaning
        if dflag and isinstance(t, (int, float)) and t < 0.6:
            augment["warnings"].append({
                "type": "semantic_storm",
                "rune_id": rid,
                "rule": "drift_flag && trust_index < 0.6",
                "severity": "high",
                "description": "Result shape drift with low trust indicates semantic instability",
            })

        # Runtime stress: severe pressure = system stress
        if isinstance(p, (int, float)) and p >= 0.8:
            augment["warnings"].append({
                "type": "runtime_stress",
                "rune_id": rid,
                "rule": "pressure_score >= 0.8",
                "severity": "severe",
                "description": "High latency variance and error rate indicate system stress",
            })

        # Critical trust: system can't rely on this rune
        if isinstance(t, (int, float)) and t <= 0.1:
            augment["warnings"].append({
                "type": "trust_critical",
                "rune_id": rid,
                "rule": "trust_index <= 0.1",
                "severity": "critical",
                "description": "Trust index critically low - rune unreliable",
            })

    # Add summary statistics
    augment["summary"] = {
        "total_runes": len(rune_ids),
        "total_warnings": len(augment["warnings"]),
        "warnings_by_severity": _count_by_severity(augment["warnings"]),
        "warnings_by_type": _count_by_type(augment["warnings"]),
    }

    return augment


def _count_by_severity(warnings: list[dict[str, Any]]) -> dict[str, int]:
    """Count warnings by severity."""
    counts: dict[str, int] = {}
    for w in warnings:
        sev = w.get("severity", "unknown")
        counts[sev] = counts.get(sev, 0) + 1
    return counts


def _count_by_type(warnings: list[dict[str, Any]]) -> dict[str, int]:
    """Count warnings by type."""
    counts: dict[str, int] = {}
    for w in warnings:
        typ = w.get("type", "unknown")
        counts[typ] = counts.get(typ, 0) + 1
    return counts


def write_telemetry_augment() -> str:
    """Generate and write memetic weather augment artifact.

    Returns:
        Path to written artifact
    """
    payload = build_telemetry_augment()
    out = OUT / "telemetry_augment.json"
    out.write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(f"Memetic weather augment written to: {out}")
    print(f"Analyzed {payload['summary']['total_runes']} runes")
    print(f"Generated {payload['summary']['total_warnings']} warnings")

    # Print warnings summary
    if payload["warnings"]:
        print("\nStorm warnings:")
        for w in payload["warnings"]:
            print(f"  [{w['severity'].upper()}] {w['type']}: {w['rune_id']}")
            print(f"    Rule: {w['rule']}")

    return str(out)


if __name__ == "__main__":
    write_telemetry_augment()
