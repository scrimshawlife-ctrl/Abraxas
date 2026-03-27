from __future__ import annotations

import json

from abx.docs_governance.docScorecard import build_doc_legibility_scorecard
from abx.docs_governance.docScorecardSerialization import serialize_doc_legibility_scorecard


if __name__ == "__main__":
    scorecard = build_doc_legibility_scorecard()
    print(json.dumps({"scorecard": json.loads(serialize_doc_legibility_scorecard(scorecard))}, indent=2, sort_keys=True))
