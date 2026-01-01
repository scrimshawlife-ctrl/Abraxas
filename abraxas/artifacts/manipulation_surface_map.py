"""Manipulation Surface Map: Heatmap data for D/M metrics across corpus.

Formats: JSON (graph data), Markdown (table)
Groups: high IRI, high MRI, payload type distribution
"""

from __future__ import annotations

import json
from typing import Dict, Any, List

from abraxas.core.provenance import Provenance
from abraxas.integrity.composites import CompositeRiskIndices
from abraxas.integrity.payload_taxonomy import PayloadClassification


def generate_manipulation_surface_json(
    risk_indices_list: List[tuple[str, CompositeRiskIndices, PayloadClassification]],
    provenance: Provenance,
) -> Dict[str, Any]:
    """
    Generate manipulation surface map in JSON format.

    Args:
        risk_indices_list: List of (term_id, risk_indices, classification) tuples
        provenance: Provenance record

    Returns:
        JSON-serializable dict with heatmap data
    """
    entries = []
    payload_distribution = {}

    for term_id, risk, classification in risk_indices_list:
        entries.append({
            "term_id": term_id,
            "iri": risk.iri,
            "mri": risk.mri,
            "payload_type": classification.payload_type.value,
            "confidence": risk.confidence.value,
        })

        # Count payload types
        payload_type = classification.payload_type.value
        payload_distribution[payload_type] = payload_distribution.get(payload_type, 0) + 1

    # Compute summary statistics
    high_iri_count = sum(1 for _, risk, _ in risk_indices_list if risk.iri > 70)
    high_mri_count = sum(1 for _, risk, _ in risk_indices_list if risk.mri > 70)

    return {
        "artifact_type": "manipulation_surface_map",
        "total_entries": len(risk_indices_list),
        "high_iri_count": high_iri_count,
        "high_mri_count": high_mri_count,
        "payload_distribution": payload_distribution,
        "entries": entries,
        "provenance": provenance.__dict__,
    }


def generate_manipulation_surface_markdown(
    risk_indices_list: List[tuple[str, CompositeRiskIndices, PayloadClassification]],
    provenance: Provenance,
) -> str:
    """
    Generate manipulation surface map in Markdown format.

    Args:
        risk_indices_list: List of (term_id, risk_indices, classification) tuples
        provenance: Provenance record

    Returns:
        Markdown string
    """
    high_iri = [
        (tid, risk) for tid, risk, _ in risk_indices_list if risk.iri > 70
    ]
    high_mri = [
        (tid, risk) for tid, risk, _ in risk_indices_list if risk.mri > 70
    ]

    lines = [
        "# Manipulation Surface Map",
        "",
        f"**Total Entries**: {len(risk_indices_list)}",
        f"**High IRI (>70)**: {len(high_iri)}",
        f"**High MRI (>70)**: {len(high_mri)}",
        f"**Generated**: {provenance.started_at_utc}",
        "",
        "## High Integrity Risk (IRI > 70)",
        "",
        "| Term ID | IRI | MRI |",
        "|---------|-----|-----|",
    ]

    for tid, risk in high_iri[:10]:  # Top 10
        lines.append(f"| `{tid[:12]}...` | {risk.iri:.1f} | {risk.mri:.1f} |")

    lines.extend([
        "",
        "## High Manipulation Risk (MRI > 70)",
        "",
        "| Term ID | IRI | MRI |",
        "|---------|-----|-----|",
    ])

    for tid, risk in high_mri[:10]:  # Top 10
        lines.append(f"| `{tid[:12]}...` | {risk.iri:.1f} | {risk.mri:.1f} |")

    lines.extend([
        "",
        "---",
        "",
        f"**Provenance**: Run ID `{provenance.run_id}` | Inputs Hash `{provenance.inputs_hash[:12]}...`",
    ])

    return "\n".join(lines)


def write_manipulation_surface_map(
    risk_indices_list: List[tuple[str, CompositeRiskIndices, PayloadClassification]],
    provenance: Provenance,
    output_path: str,
    format: str = "json",
) -> None:
    """Write manipulation surface map to file."""
    if format == "json":
        data = generate_manipulation_surface_json(risk_indices_list, provenance)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=True)
    elif format in ("md", "markdown"):
        content = generate_manipulation_surface_markdown(risk_indices_list, provenance)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
    else:
        raise ValueError(f"Unsupported format: {format}")
