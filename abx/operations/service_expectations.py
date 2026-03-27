from __future__ import annotations

from dataclasses import asdict

from abx.operations.types import ServiceExpectationRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_service_expectations() -> list[ServiceExpectationRecord]:
    rows = [
        ServiceExpectationRecord(
            subsystem="contracts_registry",
            expectation="Unique rune contract IDs remain canonical and loadable.",
            status="GUARANTEED",
            breach_signal="duplicate-or-missing-contract-id",
            cadence="per-change",
        ),
        ServiceExpectationRecord(
            subsystem="proof_validation",
            expectation="Governed runs emit validation and proof artifacts.",
            status="GOVERNED_EXPECTATION",
            breach_signal="missing-proof-or-validation-artifact",
            cadence="per-run",
        ),
        ServiceExpectationRecord(
            subsystem="operator_projection",
            expectation="Operator frame/projection reflects canonical frame state.",
            status="MONITORED",
            breach_signal="projection-diverges-from-frame-hash",
            cadence="daily",
        ),
        ServiceExpectationRecord(
            subsystem="maintenance_governance",
            expectation="Maintenance cycle and waiver audits run with deterministic outputs.",
            status="GOVERNED_EXPECTATION",
            breach_signal="missing-maintenance-or-waiver-artifact",
            cadence="weekly",
        ),
        ServiceExpectationRecord(
            subsystem="future_observability",
            expectation="Longitudinal trend alerts for governance metrics.",
            status="ASPIRATIONAL",
            breach_signal="not-computable",
            cadence="monthly",
        ),
    ]
    return sorted(rows, key=lambda x: x.subsystem)


def expectation_report() -> dict[str, object]:
    rows = build_service_expectations()
    payload = [asdict(x) for x in rows]
    digest = sha256_bytes(dumps_stable(payload).encode("utf-8"))
    return {
        "artifactType": "ServiceExpectationReport.v1",
        "artifactId": "service-expectation-report-abx",
        "expectations": payload,
        "reportHash": digest,
    }
