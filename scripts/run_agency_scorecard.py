from __future__ import annotations

import json

from abx.agency.agencyScorecard import build_agency_governance_scorecard
from abx.agency.agencyScorecardSerialization import serialize_agency_scorecard


if __name__ == "__main__":
    scorecard = build_agency_governance_scorecard()
    print(json.dumps({"scorecard": json.loads(serialize_agency_scorecard(scorecard))}, indent=2, sort_keys=True))
