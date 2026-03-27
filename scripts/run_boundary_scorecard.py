#!/usr/bin/env python3
from __future__ import annotations

import json

from abx.boundary.inputEnvelope import build_input_envelope
from abx.boundary.normalization import normalize_envelope
from abx.boundary.scorecard import build_boundary_health_scorecard
from abx.boundary.scorecardSerialization import serialize_scorecard
from abx.boundary.trustReports import build_trust_report
from abx.boundary.validation import validate_envelope
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def _validation_report() -> dict[str, object]:
    envelope = build_input_envelope(
        source="external.feed",
        interface_id="runtime_orchestrator.execute_run_plan",
        payload={"run_id": "RUN-1", "scenario_id": "SCN-1"},
    )
    result = validate_envelope(envelope, current_tick=0)
    norm, prov = normalize_envelope(envelope)
    report = {
        "artifactType": "BoundaryValidationReport.v1",
        "artifactId": "boundary-validation-report",
        "validation": result.__dict__ | {"errors": [x.__dict__ for x in result.errors]},
        "normalized": [norm.__dict__],
        "provenance": [prov.__dict__],
        "normalizedCount": 1,
        "provenanceCount": 1,
    }
    report["reportHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report


def main() -> None:
    trust = build_trust_report(
        [
            build_input_envelope(source="internal.kernel", interface_id="runtime_orchestrator.execute_run_plan", payload={"run_id": "RUN", "scenario_id": "SCN"}),
            build_input_envelope(source="external.feed", interface_id="runtime_orchestrator.execute_run_plan", payload={"run_id": "RUN", "scenario_id": "SCN"}),
        ]
    )
    scorecard = build_boundary_health_scorecard(_validation_report(), trust)
    print(json.dumps({"scorecard": json.loads(serialize_scorecard(scorecard))}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
