#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from abx.operator.insightAssembly import assemble_operator_insight_view


def main() -> None:
    ap = argparse.ArgumentParser(description="Run operator insight view assembly check")
    ap.add_argument("--run-id", default="RUN-INSIGHT")
    args = ap.parse_args()
    linkage = {
        "boundary_validation": "BoundaryValidationReport.v1",
        "trust_report": "BoundaryTrustReport.v1",
        "proof_chain": "ProofChainArtifact.v1",
        "closure_summary": "ClosureSummaryArtifact.v1",
    }
    print(json.dumps(assemble_operator_insight_view(run_id=args.run_id, linkage_refs=linkage).__dict__, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
