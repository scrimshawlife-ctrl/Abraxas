#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from abx.boundary.inputEnvelope import build_input_envelope
from abx.boundary.trustReports import build_trust_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Emit boundary trust report")
    parser.add_argument("--sources", nargs="+", default=["internal.kernel", "external.feed", "untrusted.raw"])
    args = parser.parse_args()

    envelopes = [
        build_input_envelope(source=src, interface_id="runtime_orchestrator.execute_run_plan", payload={"run_id": "RUN", "scenario_id": "SCN"})
        for src in args.sources
    ]
    print(json.dumps(build_trust_report(envelopes), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
