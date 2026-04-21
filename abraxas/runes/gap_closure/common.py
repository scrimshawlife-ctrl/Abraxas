from __future__ import annotations

from pathlib import Path

from abraxas.core.canonical import sha256_hex

GAP_CLOSURE_ARTIFACT_TYPES = (
    ("gap_closure_run", "gap_closure_run.json"),
    ("live_run_projection", "live_run_projection.json"),
    ("closure_validation_report", "closure_validation_report.json"),
)


def stable_sha256_file(path: Path) -> str:
    return sha256_hex(path.read_bytes())
