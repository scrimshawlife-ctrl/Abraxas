"""Drift detection and logging for oracle outputs."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from abraxas.runes.ctx import RuneInvocationContext
from abraxas.runes.invoke import invoke_capability


def drift_check(
    anchor: str,
    outputs_history: list[str],
    window: int = 20,
    *,
    ctx: RuneInvocationContext | dict,
    strict_execution: bool = True,
) -> Dict[str, Any]:
    """Check for anchor drift using ADD rune.

    Args:
        anchor: Core semantic anchor (theme, motif, oracle identity)
        outputs_history: List of recent oracle output strings
        window: Number of recent outputs to analyze (default 20)

    Returns:
        ADD drift bundle with keys: drift_magnitude, integrity_score, auto_recenter, etc.
    """
    return invoke_capability(
        "rune:add",
        {
            "anchor": anchor,
            "outputs_history": outputs_history,
            "window": window,
        },
        ctx=ctx,
        strict_execution=strict_execution,
    )


def append_drift_log(
    anchor: str,
    drift_bundle: Dict[str, Any],
    gate_state: str,
    runes_used: list[str],
    manifest_sha256: str,
    log_path: Path | None = None
) -> None:
    """Append drift event to immutable JSONL log.

    Args:
        anchor: Anchor string used for drift check
        drift_bundle: Output from drift_check
        gate_state: SDS gate state
        runes_used: List of rune IDs
        manifest_sha256: Manifest hash for provenance
        log_path: Path to JSONL log file (default: data/logs/anchor_drift.log.jsonl)
    """
    if log_path is None:
        # Default path relative to repo root
        repo_root = Path(__file__).parent.parent.parent
        log_path = repo_root / "data" / "logs" / "anchor_drift.log.jsonl"

    # Ensure directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Build log entry
    entry = {
        "utc": datetime.now(timezone.utc).isoformat(),
        "anchor": anchor,
        "drift_magnitude": drift_bundle.get("drift_magnitude", 0.0),
        "integrity_score": drift_bundle.get("integrity_score", 1.0),
        "auto_recenter": drift_bundle.get("auto_recenter", False),
        "gate_state": gate_state,
        "runes_used": runes_used,
        "manifest_sha256": manifest_sha256,
    }

    # Append to log (append-only, never overwrite)
    with open(log_path, "a") as f:
        f.write(json.dumps(entry, separators=(",", ":")) + "\n")
