#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from abx.decision.decisionClassification import classify_decision_completeness
from abx.decision.decisionCoverage import build_decision_coverage
from abx.decision.decisionRecords import build_decision_records
from abx.decision.decisionSerialization import serialize_decisions


def main() -> None:
    ap = argparse.ArgumentParser(description="Run decision governance audit")
    ap.add_argument("--run-id", default="RUN-DECISION")
    args = ap.parse_args()
    print(
        json.dumps(
            {
                "artifactType": "DecisionGovernanceAudit.v1",
                "artifactId": f"decision-governance-audit-{args.run_id}",
                "decisions": [x.__dict__ | {"outcome": x.outcome.__dict__} for x in build_decision_records(run_id=args.run_id)],
                "coverage": [x.__dict__ for x in build_decision_coverage(run_id=args.run_id)],
                "completeness": classify_decision_completeness(run_id=args.run_id),
                "serialized": serialize_decisions(run_id=args.run_id),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
