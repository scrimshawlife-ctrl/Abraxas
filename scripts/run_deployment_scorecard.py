#!/usr/bin/env python3
from __future__ import annotations

import json

from abx.deployment.deploymentScorecard import build_deployment_governance_scorecard
from abx.deployment.deploymentScorecardSerialization import serialize_deployment_scorecard


if __name__ == "__main__":
    scorecard = build_deployment_governance_scorecard()
    print(json.dumps({"scorecard": json.loads(serialize_deployment_scorecard(scorecard))}, indent=2, sort_keys=True))
