#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from abx.governance.decisionScorecard import build_decision_governance_scorecard
from abx.governance.decisionScorecardSerialization import serialize_decision_scorecard


def main() -> None:
    ap = argparse.ArgumentParser(description="Emit decision governance scorecard")
    ap.add_argument("--run-id", default="RUN-DECISION")
    args = ap.parse_args()
    scorecard = build_decision_governance_scorecard(run_id=args.run_id)
    print(json.dumps({"scorecard": json.loads(serialize_decision_scorecard(scorecard))}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
