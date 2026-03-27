#!/usr/bin/env python3
from __future__ import annotations

import json

from abx.federation.federationScorecard import build_federation_governance_scorecard
from abx.federation.federationScorecardSerialization import serialize_federation_scorecard


def main() -> None:
    score = build_federation_governance_scorecard()
    print(json.dumps({"scorecard": json.loads(serialize_federation_scorecard(score))}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
