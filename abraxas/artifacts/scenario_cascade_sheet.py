"""
Scenario Cascade Sheet Generator

Produces cascade sheets from ScenarioRunResult.
Exports top paths per envelope with triggers, confidence, and falsifiers.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from abraxas.scenario.types import ScenarioRunResult


def generate_scenario_cascade_sheet(
    result: ScenarioRunResult,
    focus_cluster: Optional[str] = None,
    format: str = "both",
) -> Dict[str, str]:
    """
    Generate scenario cascade sheet from run result.

    Args:
        result: ScenarioRunResult from scenario runner
        focus_cluster: Optional cluster to focus on
        format: "json", "md", or "both"

    Returns:
        Dictionary with "json" and/or "md" keys containing formatted outputs
    """

    outputs = {}

    # Build JSON output
    if format in ("json", "both"):
        json_output = _build_json_cascade_sheet(result, focus_cluster)
        outputs["json"] = json.dumps(json_output, indent=2, sort_keys=True)

    # Build Markdown output
    if format in ("md", "both"):
        md_output = _build_markdown_cascade_sheet(result, focus_cluster)
        outputs["md"] = md_output

    return outputs


def _build_json_cascade_sheet(
    result: ScenarioRunResult, focus_cluster: Optional[str]
) -> Dict[str, Any]:
    """Build JSON cascade sheet."""

    envelopes_data = []

    for envelope in result.envelopes:
        # Extract top 3 paths from NCP output
        ncp_output = envelope.outputs.get("ncp", {})
        paths = ncp_output.get("paths", [])[:3]  # Top 3 paths

        envelope_data = {
            "label": envelope.label,
            "confidence": envelope.confidence,
            "priors": envelope.priors,
            "paths": [
                {
                    "path_id": path.get("path_id", "unknown"),
                    "trigger": path.get("trigger", ""),
                    "probability": path.get("probability", 0.0),
                    "duration_hours": path.get("duration_hours", 0),
                    "terminus": path.get("terminus", ""),
                }
                for path in paths
            ],
            "falsifiers": envelope.falsifiers,
        }

        envelopes_data.append(envelope_data)

    cascade_sheet = {
        "run_id": result.input.run_id,
        "timestamp": result.input.timestamp,
        "focus_cluster": focus_cluster,
        "envelopes": envelopes_data,
        "provenance": result.provenance,
    }

    return cascade_sheet


def _build_markdown_cascade_sheet(
    result: ScenarioRunResult, focus_cluster: Optional[str]
) -> str:
    """Build Markdown cascade sheet."""

    lines = []
    lines.append("# Scenario Cascade Sheet")
    lines.append("")
    lines.append(f"**Run ID:** `{result.input.run_id}`")
    lines.append(f"**Timestamp:** {result.input.timestamp}")
    if focus_cluster:
        lines.append(f"**Focus Cluster:** {focus_cluster}")
    lines.append("")

    for envelope in result.envelopes:
        lines.append(f"## Envelope: {envelope.label}")
        lines.append(f"**Confidence:** {envelope.confidence}")
        lines.append("")

        # Priors
        lines.append("**Priors:**")
        for key, value in sorted(envelope.priors.items()):
            lines.append(f"- {key}: {value:.3f}")
        lines.append("")

        # Top paths
        ncp_output = envelope.outputs.get("ncp", {})
        paths = ncp_output.get("paths", [])[:3]

        if paths:
            lines.append("**Top Cascade Paths:**")
            for i, path in enumerate(paths, 1):
                lines.append(f"{i}. **{path.get('trigger', 'Unknown trigger')}**")
                lines.append(f"   - Probability: {path.get('probability', 0.0):.2f}")
                lines.append(f"   - Duration: {path.get('duration_hours', 0)} hours")
                lines.append(f"   - Terminus: {path.get('terminus', 'Unknown')}")
            lines.append("")
        else:
            lines.append("*No paths available for this envelope.*")
            lines.append("")

        # Falsifiers
        lines.append("**Falsification Criteria:**")
        for falsifier in envelope.falsifiers:
            lines.append(f"- {falsifier}")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Provenance
    lines.append("## Provenance")
    lines.append(f"- Generator: {result.provenance.get('generator', 'unknown')}")
    lines.append(f"- Version: {result.provenance.get('version', 'unknown')}")
    lines.append(f"- Envelope Count: {result.provenance.get('envelope_count', 0)}")
    lines.append("")

    return "\n".join(lines)
