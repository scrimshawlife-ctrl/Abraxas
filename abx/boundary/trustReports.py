from __future__ import annotations

from abx.boundary.trustEnforcement import classify_trust_record
from abx.boundary.types import InputEnvelope
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_trust_report(envelopes: list[InputEnvelope]) -> dict[str, object]:
    records = [classify_trust_record(e).__dict__ for e in envelopes]
    counts: dict[str, int] = {}
    for row in records:
        state = str(row["trust_state"])
        counts[state] = counts.get(state, 0) + 1
    payload = {"records": records, "counts": counts}
    digest = sha256_bytes(dumps_stable(payload).encode("utf-8"))
    return {
        "artifactType": "BoundaryTrustReport.v1",
        "artifactId": "boundary-trust-report",
        "records": records,
        "counts": counts,
        "reportHash": digest,
    }
