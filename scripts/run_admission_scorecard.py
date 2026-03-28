from __future__ import annotations

import json

from abx.admission.admissionScorecard import build_admission_governance_scorecard
from abx.admission.admissionScorecardSerialization import serialize_admission_scorecard


if __name__ == "__main__":
    scorecard = build_admission_governance_scorecard()
    print(json.dumps({"scorecard": json.loads(serialize_admission_scorecard(scorecard))}, indent=2, sort_keys=True))
