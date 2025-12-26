"""Contamination Advisory: Alert-level report for high-risk artifacts.

Thresholds: IRI > 70 OR MRI > 80
Includes mitigation recommendations.
"""

from __future__ import annotations

import json
from typing import Dict, Any, List

from abraxas.core.provenance import Provenance
from abraxas.integrity.composites import CompositeRiskIndices
from abraxas.integrity.payload_taxonomy import PayloadClassification


def generate_contamination_advisory_json(
    high_risk_items: List[tuple[str, str, CompositeRiskIndices, PayloadClassification]],
    provenance: Provenance,
) -> Dict[str, Any]:
    """
    Generate contamination advisory in JSON format.

    Args:
        high_risk_items: List of (term_id, term, risk_indices, classification) tuples
        provenance: Provenance record

    Returns:
        JSON-serializable dict
    """
    alerts = []
    for term_id, term, risk, classification in high_risk_items:
        alert_level = "CRITICAL" if (risk.iri > 80 or risk.mri > 90) else "HIGH"

        mitigation = []
        if risk.iri > 70:
            mitigation.append("Verify provenance and source chain")
        if risk.mri > 80:
            mitigation.append("Review for narrative manipulation indicators")
        if risk.network_campaign.cus > 0.7:
            mitigation.append("Investigate coordinated amplification patterns")

        alerts.append({
            "alert_level": alert_level,
            "term_id": term_id,
            "term": term,
            "iri": risk.iri,
            "mri": risk.mri,
            "payload_type": classification.payload_type.value,
            "mitigation_recommendations": mitigation,
        })

    return {
        "artifact_type": "contamination_advisory",
        "alert_count": len(alerts),
        "alerts": alerts,
        "provenance": provenance.__dict__,
    }


def generate_contamination_advisory_markdown(
    high_risk_items: List[tuple[str, str, CompositeRiskIndices, PayloadClassification]],
    provenance: Provenance,
) -> str:
    """
    Generate contamination advisory in Markdown format.

    Args:
        high_risk_items: List of (term_id, term, risk_indices, classification) tuples
        provenance: Provenance record

    Returns:
        Markdown string
    """
    lines = [
        "# Contamination Advisory",
        "",
        f"**Alert Count**: {len(high_risk_items)}",
        f"**Generated**: {provenance.started_at_utc}",
        "",
        "## High-Risk Artifacts",
        "",
    ]

    for term_id, term, risk, classification in high_risk_items:
        alert_level = "CRITICAL" if (risk.iri > 80 or risk.mri > 90) else "HIGH"

        lines.extend([
            f"### {alert_level}: `{term}`",
            "",
            f"- **Term ID**: `{term_id}`",
            f"- **IRI**: {risk.iri:.1f}",
            f"- **MRI**: {risk.mri:.1f}",
            f"- **Payload Type**: {classification.payload_type.value}",
            "",
            "**Mitigation Recommendations**:",
            "",
        ])

        if risk.iri > 70:
            lines.append("- Verify provenance and source chain")
        if risk.mri > 80:
            lines.append("- Review for narrative manipulation indicators")
        if risk.network_campaign.cus > 0.7:
            lines.append("- Investigate coordinated amplification patterns")

        lines.append("")

    lines.extend([
        "---",
        "",
        f"**Provenance**: Run ID `{provenance.run_id}` | Inputs Hash `{provenance.inputs_hash[:12]}...`",
    ])

    return "\n".join(lines)


def write_contamination_advisory(
    high_risk_items: List[tuple[str, str, CompositeRiskIndices, PayloadClassification]],
    provenance: Provenance,
    output_path: str,
    format: str = "json",
) -> None:
    """Write contamination advisory to file."""
    if format == "json":
        data = generate_contamination_advisory_json(high_risk_items, provenance)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=True)
    elif format in ("md", "markdown"):
        content = generate_contamination_advisory_markdown(high_risk_items, provenance)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
    else:
        raise ValueError(f"Unsupported format: {format}")
