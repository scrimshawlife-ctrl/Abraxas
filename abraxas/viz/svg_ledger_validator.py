from __future__ import annotations

from typing import Any, Dict

from abraxas.viz.svg_ledger_models import AUTHORITY


def validate_authority() -> None:
    if AUTHORITY["svg_artifact_ledger_write"] is not True:
        raise ValueError("svg_artifact_ledger_write must be true")
    for k in ("svg_rendering", "viz_projection", "inference", "production_activation", "baseline_mutation", "runtime_config_write", "promotion", "execution", "scheduler"):
        if AUTHORITY[k] is not False:
            raise ValueError(f"{k} must be false")


def validate_manifest(manifest: Dict[str, Any]) -> None:
    required = ("render_id", "view_id", "svg_hash", "view_packet_hash", "files")
    for key in required:
        if key not in manifest:
            raise ValueError(f"missing {key}")
