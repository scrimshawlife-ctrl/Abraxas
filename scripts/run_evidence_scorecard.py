from __future__ import annotations

import json

from abx.evidence.evidenceScorecard import build_evidence_governance_scorecard
from abx.evidence.evidenceScorecardSerialization import serialize_evidence_scorecard


if __name__ == "__main__":
    scorecard = build_evidence_governance_scorecard()
    print(json.dumps({"scorecard": json.loads(serialize_evidence_scorecard(scorecard))}, indent=2, sort_keys=True))
