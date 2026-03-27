#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from abx.observability.scorecard import build_observability_health_scorecard
from abx.observability.scorecardSerialization import serialize_observability_scorecard


def main() -> None:
    ap = argparse.ArgumentParser(description="Emit observability health scorecard")
    ap.add_argument("--run-id", default="RUN-OBS")
    args = ap.parse_args()
    linkage = {
        "boundary_validation": "BoundaryValidationReport.v1",
        "trust_report": "BoundaryTrustReport.v1",
        "proof_chain": "ProofChainArtifact.v1",
        "closure_summary": "ClosureSummaryArtifact.v1",
    }
    score = build_observability_health_scorecard(run_id=args.run_id, linkage_refs=linkage)
    print(json.dumps({"scorecard": json.loads(serialize_observability_scorecard(score))}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
