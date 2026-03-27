#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from abx.observability.summaryAssembly import build_observability_summary
from abx.observability.surfaceInventory import build_surface_inventory


def main() -> None:
    ap = argparse.ArgumentParser(description="Run observability surface inventory and consolidation audit")
    ap.add_argument("--run-id", default="RUN-OBS")
    args = ap.parse_args()
    linkage = {
        "boundary_validation": "BoundaryValidationReport.v1",
        "trust_report": "BoundaryTrustReport.v1",
        "proof_chain": "ProofChainArtifact.v1",
        "closure_summary": "ClosureSummaryArtifact.v1",
    }
    print(
        json.dumps(
            {
                "artifactType": "ObservabilityAudit.v1",
                "artifactId": "observability-audit",
                "inventory": [x.__dict__ for x in build_surface_inventory()],
                "summary": build_observability_summary(run_id=args.run_id, linkage_refs=linkage),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
