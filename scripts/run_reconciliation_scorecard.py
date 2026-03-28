from __future__ import annotations

import json

from abx.reconcile.reconciliationScorecard import build_reconciliation_governance_scorecard
from abx.reconcile.reconciliationScorecardSerialization import serialize_reconciliation_scorecard


if __name__ == "__main__":
    scorecard = build_reconciliation_governance_scorecard()
    print(json.dumps({"scorecard": json.loads(serialize_reconciliation_scorecard(scorecard))}, indent=2, sort_keys=True))
