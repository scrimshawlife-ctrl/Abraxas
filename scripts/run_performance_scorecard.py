from __future__ import annotations

import json

from abx.performance.performanceScorecard import build_performance_resource_scorecard
from abx.performance.performanceScorecardSerialization import serialize_performance_resource_scorecard


if __name__ == "__main__":
    scorecard = build_performance_resource_scorecard()
    print(json.dumps({"scorecard": json.loads(serialize_performance_resource_scorecard(scorecard))}, indent=2, sort_keys=True))
