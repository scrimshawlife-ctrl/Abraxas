from __future__ import annotations

import json

from abx.continuity.continuityScorecard import build_mission_continuity_scorecard
from abx.continuity.continuityScorecardSerialization import serialize_continuity_scorecard


if __name__ == "__main__":
    scorecard = build_mission_continuity_scorecard()
    print(json.dumps({"scorecard": json.loads(serialize_continuity_scorecard(scorecard))}, indent=2, sort_keys=True))
