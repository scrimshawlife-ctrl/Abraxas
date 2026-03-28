from __future__ import annotations

import json

from abx.interface.interfaceScorecard import build_cross_boundary_delivery_scorecard
from abx.interface.interfaceScorecardSerialization import serialize_interface_scorecard


if __name__ == "__main__":
    scorecard = build_cross_boundary_delivery_scorecard()
    print(json.dumps({"scorecard": json.loads(serialize_interface_scorecard(scorecard))}, indent=2, sort_keys=True))
