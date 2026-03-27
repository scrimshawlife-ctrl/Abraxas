from __future__ import annotations

import json

from abx.concurrency.concurrencyScorecard import build_concurrency_scorecard
from abx.concurrency.concurrencyScorecardSerialization import serialize_concurrency_scorecard


if __name__ == "__main__":
    scorecard = build_concurrency_scorecard()
    print(json.dumps({"scorecard": json.loads(serialize_concurrency_scorecard(scorecard))}, indent=2, sort_keys=True))
