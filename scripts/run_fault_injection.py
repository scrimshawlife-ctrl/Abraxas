#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from abx.resilience.faultInjection import render_fault_injection_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run deterministic fault injection scaffolding")
    parser.add_argument("--scenario-id", default="resilience-pass11")
    parser.add_argument("--domain", action="append", dest="domains", default=None)
    args = parser.parse_args()
    print(json.dumps(render_fault_injection_report(scenario_id=args.scenario_id, domain_ids=args.domains), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
