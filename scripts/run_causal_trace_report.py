#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from abx.trace.causalTrace import build_causal_trace
from abx.trace.traceCoverage import build_trace_coverage
from abx.trace.traceSummary import build_trace_summary


def main() -> None:
    ap = argparse.ArgumentParser(description="Run causal trace report")
    ap.add_argument("--run-id", default="RUN-TRACE")
    args = ap.parse_args()
    print(
        json.dumps(
            {
                "artifactType": "CausalTraceReport.v1",
                "artifactId": f"causal-trace-report-{args.run_id}",
                "trace": [x.__dict__ for x in build_causal_trace(run_id=args.run_id)],
                "summary": build_trace_summary(run_id=args.run_id).__dict__,
                "coverage": build_trace_coverage(run_id=args.run_id).__dict__,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
