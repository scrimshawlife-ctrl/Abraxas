#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from abx.knowledge.continuityReports import build_continuity_audit_report


def main() -> None:
    ap = argparse.ArgumentParser(description="Run continuity governance audit")
    ap.add_argument("--run-id", default="RUN-CONTINUITY")
    args = ap.parse_args()
    print(json.dumps(build_continuity_audit_report(run_id=args.run_id), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
