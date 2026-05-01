from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

ARTIFACT_ID = "AAL-VIZ-SVG-ARTIFACT-LEDGER-001"
LEDGER_SCHEMA_VERSION = "AALVizSVGArtifactLedgerRun.v1"
ENTRY_VERSION = "AALVizSVGArtifactLedgerEntry.v1"

AUTHORITY = {
    "svg_artifact_ledger_write": True,
    "svg_rendering": False,
    "viz_projection": False,
    "inference": False,
    "production_activation": False,
    "baseline_mutation": False,
    "runtime_config_write": False,
    "promotion": False,
    "execution": False,
    "scheduler": False,
}


def ledger_run_payload(entries: List[Dict[str, Any]], manifests_total: int, entries_created: int, entries_existing: int) -> Dict[str, Any]:
    return {
        "artifact": ARTIFACT_ID,
        "schema_version": LEDGER_SCHEMA_VERSION,
        "authority": dict(AUTHORITY),
        "counts": {
            "manifests_total": manifests_total,
            "entries_created": entries_created,
            "entries_existing": entries_existing,
            "entries_total": len(entries),
        },
        "entries": entries,
    }
