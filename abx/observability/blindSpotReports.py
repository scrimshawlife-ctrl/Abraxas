from __future__ import annotations

from abx.observability.blindSpotClassification import classify_blind_spot
from abx.observability.blindSpotRecords import build_blind_spot_records
from abx.observability.types import CoverageGovernanceErrorRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_blind_spot_report() -> dict[str, object]:
    rows = build_blind_spot_records()
    states = {x.blind_spot_id: classify_blind_spot(blind_spot_state=x.blind_spot_state) for x in rows}
    errors = []
    for row in rows:
        state = states[row.blind_spot_id]
        if state in {"BLIND_SPOT_CONFIRMED", "BLIND_SPOT_HIGH_RISK", "BLIND_SPOT_BLOCKED", "NOT_COMPUTABLE"}:
            errors.append(CoverageGovernanceErrorRecord("BLIND_SPOT_BLOCKING", "ERROR", f"{row.surface_ref} state={state}"))
        elif state in {"BLIND_SPOT_SUSPECTED"}:
            errors.append(CoverageGovernanceErrorRecord("BLIND_SPOT_ATTENTION", "WARN", f"{row.surface_ref} state={state}"))
    report = {
        "artifactType": "BlindSpotAudit.v1",
        "artifactId": "blind-spot-audit",
        "blindSpots": [x.__dict__ for x in rows],
        "blindSpotStates": states,
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
