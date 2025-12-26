"""Cascade Sheet: Tabular summary of NCP scenario outputs.

Formats: JSON, Markdown
Columns: trigger, probability, duration, terminus
"""

from __future__ import annotations

import json
from typing import Dict, Any

from abraxas.core.provenance import Provenance
from abraxas.sod.models import ScenarioEnvelope


def generate_cascade_sheet_json(
    scenario_envelope: ScenarioEnvelope,
    provenance: Provenance,
) -> Dict[str, Any]:
    """
    Generate cascade sheet in JSON format.

    Args:
        scenario_envelope: Scenario envelope from NCP
        provenance: Provenance record for this artifact

    Returns:
        JSON-serializable dict
    """
    rows = []
    for path in scenario_envelope.paths:
        rows.append({
            "path_id": path.path_id,
            "trigger": path.trigger,
            "probability": path.probability,
            "duration_hours": path.duration_hours,
            "intermediates": path.intermediates,
            "terminus": path.terminus,
        })

    return {
        "artifact_type": "cascade_sheet",
        "scenario_id": scenario_envelope.scenario_id,
        "paths": rows,
        "falsifiers": scenario_envelope.falsifiers,
        "confidence": scenario_envelope.confidence,
        "provenance": provenance.__dict__,
    }


def generate_cascade_sheet_markdown(
    scenario_envelope: ScenarioEnvelope,
    provenance: Provenance,
) -> str:
    """
    Generate cascade sheet in Markdown format.

    Args:
        scenario_envelope: Scenario envelope from NCP
        provenance: Provenance record for this artifact

    Returns:
        Markdown string
    """
    lines = [
        "# Cascade Sheet",
        "",
        f"**Scenario ID**: `{scenario_envelope.scenario_id}`",
        f"**Confidence**: {scenario_envelope.confidence}",
        f"**Generated**: {provenance.started_at_utc}",
        "",
        "## Cascade Paths",
        "",
        "| Trigger | Probability | Duration (hrs) | Terminus |",
        "|---------|-------------|----------------|----------|",
    ]

    for path in scenario_envelope.paths:
        lines.append(
            f"| {path.trigger} | {path.probability:.2f} | {path.duration_hours} | {path.terminus} |"
        )

    lines.extend([
        "",
        "## Falsifiers",
        "",
    ])

    for falsifier in scenario_envelope.falsifiers:
        lines.append(f"- {falsifier}")

    lines.extend([
        "",
        "---",
        "",
        f"**Provenance**: Run ID `{provenance.run_id}` | Inputs Hash `{provenance.inputs_hash[:12]}...`",
    ])

    return "\n".join(lines)


def write_cascade_sheet(
    scenario_envelope: ScenarioEnvelope,
    provenance: Provenance,
    output_path: str,
    format: str = "json",
) -> None:
    """
    Write cascade sheet to file.

    Args:
        scenario_envelope: Scenario envelope from NCP
        provenance: Provenance record
        output_path: Output file path
        format: Output format ('json' or 'md')
    """
    if format == "json":
        data = generate_cascade_sheet_json(scenario_envelope, provenance)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=True)
    elif format in ("md", "markdown"):
        content = generate_cascade_sheet_markdown(scenario_envelope, provenance)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
    else:
        raise ValueError(f"Unsupported format: {format}")
