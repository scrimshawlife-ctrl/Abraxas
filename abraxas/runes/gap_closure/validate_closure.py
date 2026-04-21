from __future__ import annotations

from pathlib import Path
from typing import Any

from .validator import validate_gap_closure_artifacts


def build_closure_validation_report(
    *,
    run_id: str,
    run_dir: Path,
    artifact_index: list[dict[str, Any]],
) -> dict[str, Any]:
    return validate_gap_closure_artifacts(run_id=run_id, run_dir=run_dir, artifact_index=artifact_index)
