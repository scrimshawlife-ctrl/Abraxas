"""
Scenario Contamination Advisory Generator

Produces contamination advisories from D/M snapshots + sim priors + weather.
Includes SSI (Synthetic Saturation Index) and skepticism mode guidance.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional


def generate_scenario_contamination_advisory(
    dm_snapshot: Optional[Dict[str, Any]],
    sim_priors: Dict[str, float],
    weather: Optional[Dict[str, Any]],
    tier: str = "psychonaut",
    format: str = "both",
) -> Dict[str, str]:
    """
    Generate contamination advisory from D/M snapshot and sim priors.

    Args:
        dm_snapshot: D/M metrics snapshot
        sim_priors: Simulation priors (MRI, IRI, etc.)
        weather: Current weather snapshot
        tier: "psychonaut", "analyst", or "enterprise"
        format: "json", "md", or "both"

    Returns:
        Dictionary with "json" and/or "md" keys containing formatted outputs
    """

    outputs = {}

    # Build JSON output
    if format in ("json", "both"):
        json_output = _build_json_advisory(dm_snapshot, sim_priors, weather, tier)
        outputs["json"] = json.dumps(json_output, indent=2, sort_keys=True)

    # Build Markdown output
    if format in ("md", "both"):
        md_output = _build_markdown_advisory(dm_snapshot, sim_priors, weather, tier)
        outputs["md"] = md_output

    return outputs


def _compute_ssi(dm_snapshot: Optional[Dict[str, Any]]) -> float:
    """
    Compute Synthetic Saturation Index (SSI).

    Rules:
    - If SLS (Slang Lifecycle Saturation) present: SSI = clamp(SLS, 0, 1)
    - Else: Derive from evidence completeness (lower evidence -> higher uncertainty, NOT higher SSI)

    Returns:
        SSI value in [0, 1]
    """
    if dm_snapshot and "SLS" in dm_snapshot:
        sls = dm_snapshot["SLS"]
        return max(0.0, min(1.0, sls))

    # Fallback: derive from evidence completeness
    if dm_snapshot:
        evidence_count = len([k for k in dm_snapshot.keys() if not k.startswith("_")])
        # Low evidence -> low SSI (high uncertainty)
        ssi = min(0.5, evidence_count * 0.05)  # Max 0.5 for incomplete evidence
        return ssi

    return 0.0  # No data -> no saturation signal


def _build_json_advisory(
    dm_snapshot: Optional[Dict[str, Any]],
    sim_priors: Dict[str, float],
    weather: Optional[Dict[str, Any]],
    tier: str,
) -> Dict[str, Any]:
    """Build JSON contamination advisory."""

    ssi = _compute_ssi(dm_snapshot)

    # Extract MRI/IRI (scale to 0-100 if available)
    mri_value = sim_priors.get("MRI", 0.5) * 100
    iri_value = sim_priors.get("IRI", 0.5) * 100

    advisory = {
        "ssi": round(ssi, 3),
        "indices": {
            "MRI": round(mri_value, 1),
            "IRI": round(iri_value, 1),
        },
        "tier": tier,
        "skepticism_mode": _get_skepticism_guidance(tier),
        "dm_snapshot_present": dm_snapshot is not None,
        "weather_present": weather is not None,
    }

    return advisory


def _build_markdown_advisory(
    dm_snapshot: Optional[Dict[str, Any]],
    sim_priors: Dict[str, float],
    weather: Optional[Dict[str, Any]],
    tier: str,
) -> str:
    """Build Markdown contamination advisory."""

    ssi = _compute_ssi(dm_snapshot)
    mri_value = sim_priors.get("MRI", 0.5) * 100
    iri_value = sim_priors.get("IRI", 0.5) * 100

    lines = []
    lines.append("# Contamination Advisory")
    lines.append("")

    # SSI
    lines.append("## Synthetic Saturation Index (SSI)")
    lines.append(f"**Current SSI:** {ssi:.3f}")
    lines.append("")

    # Risk Indices
    lines.append("## Risk Indices")
    lines.append(f"- **MRI (Memetic Resonance Index):** {mri_value:.1f} / 100")
    lines.append(f"- **IRI (Intervention Responsiveness Index):** {iri_value:.1f} / 100")
    lines.append("")

    # Skepticism Mode Guidance
    lines.append("## Skepticism Mode Guidance")
    guidance = _get_skepticism_guidance(tier)
    lines.append(f"**Tier:** {tier}")
    lines.append("")
    lines.append(guidance)
    lines.append("")

    # Data Availability
    lines.append("## Data Availability")
    lines.append(f"- D/M Snapshot: {'✓' if dm_snapshot else '✗'}")
    lines.append(f"- Weather Data: {'✓' if weather else '✗'}")
    lines.append("")

    return "\n".join(lines)


def _get_skepticism_guidance(tier: str) -> str:
    """Get skepticism mode guidance by tier."""

    if tier == "psychonaut":
        return (
            "**Plain Mode:** SSI reflects current saturation. "
            "Higher SSI indicates denser symbolic activity. "
            "No moralizing; pure instrumentation."
        )
    elif tier == "analyst":
        return (
            "**Method Notes:** SSI derived from SLS (if available) or evidence completeness. "
            "MRI/IRI scaled to [0-100]. All values deterministic; no stochastic components. "
            "Confidence bands reflect prior source count and knob coverage."
        )
    elif tier == "enterprise":
        return (
            "**Risk Timing:** SSI >0.7 suggests high saturation; intervention window may be narrow. "
            "MRI >70 indicates strong memetic resonance; IRI >70 suggests high responsiveness. "
            "Evaluate falsifiers before operational deployment."
        )
    else:
        return "Unknown tier."
