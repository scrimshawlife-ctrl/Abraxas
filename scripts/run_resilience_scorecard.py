#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from abx.resilience.scorecard import render_resilience_scorecard


def main() -> None:
    parser = argparse.ArgumentParser(description="Emit deterministic resilience scorecard")
    parser.add_argument("--scenario-id", default="resilience-pass11")
    args = parser.parse_args()
    print(json.dumps(render_resilience_scorecard(scenario_id=args.scenario_id), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
