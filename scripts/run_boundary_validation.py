#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from abx.boundary.inputEnvelope import build_input_envelope
from abx.boundary.normalization import normalize_envelope
from abx.boundary.validation import validate_envelope
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def main() -> None:
    parser = argparse.ArgumentParser(description="Run boundary input validation + normalization")
    parser.add_argument("--source", default="external.default")
    parser.add_argument("--interface-id", default="runtime_orchestrator.execute_run_plan")
    parser.add_argument("--payload", default='{"run_id":"RUN-1","scenario_id":"SCN-1"}')
    parser.add_argument("--received-tick", type=int, default=0)
    parser.add_argument("--current-tick", type=int, default=0)
    args = parser.parse_args()

    envelope = build_input_envelope(
        source=args.source,
        interface_id=args.interface_id,
        payload=json.loads(args.payload),
        received_tick=args.received_tick,
    )
    validation = validate_envelope(envelope, current_tick=args.current_tick)

    normalized_rows = []
    provenance_rows = []
    if validation.status in {"ACCEPTED", "DEGRADED"}:
        normalized, provenance = normalize_envelope(envelope)
        normalized_rows.append(normalized.__dict__)
        provenance_rows.append(provenance.__dict__)

    report = {
        "artifactType": "BoundaryValidationReport.v1",
        "artifactId": "boundary-validation-report",
        "validation": validation.__dict__ | {"errors": [x.__dict__ for x in validation.errors]},
        "normalized": normalized_rows,
        "provenance": provenance_rows,
        "normalizedCount": len(normalized_rows),
        "provenanceCount": len(provenance_rows),
    }
    report["reportHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
