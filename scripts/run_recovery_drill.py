#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from abx.resilience.recoveryDrills import render_recovery_drill_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run deterministic recovery drill")
    parser.add_argument("--scenario-id", default="resilience-pass11")
    parser.add_argument("--mode", choices=["rollback", "patch-forward", "containment"], default="containment")
    parser.add_argument("--incident-id", default="inc.none")
    args = parser.parse_args()
    print(
        json.dumps(
            render_recovery_drill_report(scenario_id=args.scenario_id, mode=args.mode, incident_id=args.incident_id),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
