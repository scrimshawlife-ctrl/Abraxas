"""Oracle Delta Ledger: Diff between current and prior oracle snapshots.

Format: JSON, Markdown
Delta-only mode: emits only changed fields unless --full requested.
Compares to data/runs/last_snapshot.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, Optional

from abraxas.core.provenance import Provenance


def compute_delta(
    current_snapshot: Dict[str, Any],
    prior_snapshot: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Compute delta between current and prior snapshots.

    Args:
        current_snapshot: Current state
        prior_snapshot: Prior state (None if first run)

    Returns:
        Delta dict with added/changed/removed fields
    """
    if prior_snapshot is None:
        return {
            "delta_type": "initial",
            "added": current_snapshot,
            "changed": {},
            "removed": {},
        }

    added = {}
    changed = {}
    removed = {}

    # Check current keys
    for key, value in current_snapshot.items():
        if key not in prior_snapshot:
            added[key] = value
        elif prior_snapshot[key] != value:
            changed[key] = {
                "old": prior_snapshot[key],
                "new": value,
            }

    # Check removed keys
    for key in prior_snapshot:
        if key not in current_snapshot:
            removed[key] = prior_snapshot[key]

    return {
        "delta_type": "diff",
        "added": added,
        "changed": changed,
        "removed": removed,
    }


def generate_oracle_delta_json(
    current_snapshot: Dict[str, Any],
    prior_snapshot: Optional[Dict[str, Any]],
    provenance: Provenance,
    full: bool = False,
) -> Dict[str, Any]:
    """
    Generate oracle delta ledger in JSON format.

    Args:
        current_snapshot: Current oracle state
        prior_snapshot: Prior oracle state
        provenance: Provenance record
        full: If True, include full snapshot; otherwise delta only

    Returns:
        JSON-serializable dict
    """
    if full:
        return {
            "artifact_type": "oracle_delta_ledger",
            "mode": "full",
            "snapshot": current_snapshot,
            "provenance": provenance.__dict__,
        }

    delta = compute_delta(current_snapshot, prior_snapshot)
    return {
        "artifact_type": "oracle_delta_ledger",
        "mode": "delta",
        "delta": delta,
        "provenance": provenance.__dict__,
    }


def generate_oracle_delta_markdown(
    current_snapshot: Dict[str, Any],
    prior_snapshot: Optional[Dict[str, Any]],
    provenance: Provenance,
    full: bool = False,
) -> str:
    """
    Generate oracle delta ledger in Markdown format.

    Args:
        current_snapshot: Current oracle state
        prior_snapshot: Prior oracle state
        provenance: Provenance record
        full: If True, include full snapshot; otherwise delta only

    Returns:
        Markdown string
    """
    lines = [
        "# Oracle Delta Ledger",
        "",
        f"**Mode**: {'Full' if full else 'Delta'}",
        f"**Generated**: {provenance.started_at_utc}",
        "",
    ]

    if full:
        lines.extend([
            "## Full Snapshot",
            "",
            "```json",
            json.dumps(current_snapshot, indent=2),
            "```",
        ])
    else:
        delta = compute_delta(current_snapshot, prior_snapshot)

        if delta["delta_type"] == "initial":
            lines.extend([
                "## Initial Snapshot",
                "",
                "This is the first run (no prior snapshot).",
                "",
            ])
        else:
            if delta["added"]:
                lines.extend([
                    "## Added Fields",
                    "",
                    "```json",
                    json.dumps(delta["added"], indent=2),
                    "```",
                    "",
                ])

            if delta["changed"]:
                lines.extend([
                    "## Changed Fields",
                    "",
                ])
                for key, change in delta["changed"].items():
                    lines.extend([
                        f"### `{key}`",
                        "",
                        f"- **Old**: `{change['old']}`",
                        f"- **New**: `{change['new']}`",
                        "",
                    ])

            if delta["removed"]:
                lines.extend([
                    "## Removed Fields",
                    "",
                    "```json",
                    json.dumps(delta["removed"], indent=2),
                    "```",
                    "",
                ])

    lines.extend([
        "---",
        "",
        f"**Provenance**: Run ID `{provenance.run_id}` | Inputs Hash `{provenance.inputs_hash[:12]}...`",
    ])

    return "\n".join(lines)


def write_oracle_delta_ledger(
    current_snapshot: Dict[str, Any],
    prior_snapshot_path: Optional[str],
    provenance: Provenance,
    output_path: str,
    format: str = "json",
    full: bool = False,
) -> None:
    """
    Write oracle delta ledger to file.

    Args:
        current_snapshot: Current oracle state
        prior_snapshot_path: Path to prior snapshot (None if first run)
        provenance: Provenance record
        output_path: Output file path
        format: Output format ('json' or 'md')
        full: If True, write full snapshot; otherwise delta only
    """
    # Load prior snapshot if exists
    prior_snapshot = None
    if prior_snapshot_path and Path(prior_snapshot_path).exists():
        with open(prior_snapshot_path, "r", encoding="utf-8") as f:
            prior_snapshot = json.load(f)

    if format == "json":
        data = generate_oracle_delta_json(current_snapshot, prior_snapshot, provenance, full)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=True)
    elif format in ("md", "markdown"):
        content = generate_oracle_delta_markdown(current_snapshot, prior_snapshot, provenance, full)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
    else:
        raise ValueError(f"Unsupported format: {format}")
