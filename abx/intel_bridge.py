"""Intelligence Bridge (v0.1) — Telemetry → Intelligence membrane.

Loads telemetry artifacts and emits intelligence artifacts.
The interface between raw metrics and symbolic meaning.

Key principle: telemetry informs intelligence; intelligence never mutates telemetry.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


# Paths
ROOT = Path(__file__).resolve().parents[1]
TELEMETRY = ROOT / "data" / "telemetry"
INTEL = ROOT / "data" / "intel"

# Ensure intel directory exists
INTEL.mkdir(parents=True, exist_ok=True)


def load(name: str) -> dict[str, Any]:
    """Load a telemetry artifact by name.

    Args:
        name: Artifact filename (e.g. "latency_baselines.json")

    Returns:
        Parsed JSON dict, or empty dict if not found

    Notes:
        - Read-only, never modifies telemetry
        - Returns {} instead of raising on missing files
        - Safe to call speculatively
    """
    p = TELEMETRY / name
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def emit(name: str, payload: dict[str, Any]) -> str:
    """Emit an intelligence artifact.

    Args:
        name: Artifact filename (e.g. "symbolic_pressure.json")
        payload: Intelligence data to write

    Returns:
        Path to written file (as string)

    Notes:
        - Write-only to intel directory
        - Never reads from telemetry during write
        - Stable JSON serialization for reproducibility
    """
    p = INTEL / name
    p.write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    return str(p)
