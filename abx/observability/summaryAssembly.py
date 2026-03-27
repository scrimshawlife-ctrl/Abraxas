from __future__ import annotations

from abx.observability.surfaceClassification import classify_surfaces, detect_redundant_surfaces
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_observability_summary(*, run_id: str, linkage_refs: dict[str, str]) -> dict[str, object]:
    classification = classify_surfaces()
    redundant = detect_redundant_surfaces()
    summary = {
        "artifactType": "ObservabilitySummary.v1",
        "artifactId": f"observability-summary-{run_id}",
        "runId": run_id,
        "surfaceClassification": classification,
        "redundantSurfaces": redundant,
        "linkageRefs": dict(sorted(linkage_refs.items())),
    }
    summary["summaryHash"] = sha256_bytes(dumps_stable(summary).encode("utf-8"))
    return summary
