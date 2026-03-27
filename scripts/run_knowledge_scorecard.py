#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from abx.knowledge.knowledgeScorecard import build_knowledge_continuity_scorecard
from abx.knowledge.knowledgeScorecardSerialization import serialize_knowledge_scorecard


def main() -> None:
    ap = argparse.ArgumentParser(description="Emit knowledge continuity scorecard")
    ap.add_argument("--run-id", default="RUN-CONTINUITY")
    args = ap.parse_args()
    score = build_knowledge_continuity_scorecard(run_id=args.run_id)
    print(json.dumps({"scorecard": json.loads(serialize_knowledge_scorecard(score))}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
