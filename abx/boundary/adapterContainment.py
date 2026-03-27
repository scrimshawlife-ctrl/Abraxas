from __future__ import annotations

from abx.boundary.connectorCapabilities import build_connector_capabilities
from abx.boundary.transformMetadata import build_transform_record
from abx.boundary.types import AdapterTransformRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def _sample_transforms() -> list[AdapterTransformRecord]:
    return [
        build_transform_record(
            adapter_id="adapter.http_snapshot.v1",
            connector_id="connector.http_snapshot",
            transform_type="translation",
            input_trust="EXTERNAL_ASSERTED",
            output_trust="EXTERNAL_ASSERTED",
            metadata={"adds_fields": ["source", "payload"], "policy_flags": []},
        ),
        build_transform_record(
            adapter_id="adapter.noaa_swpc_kp.v1",
            connector_id="connector.noaa_swpc_kp",
            transform_type="normalization",
            input_trust="EXTERNAL_ASSERTED",
            output_trust="GOVERNED_DERIVED",
            metadata={"adds_fields": ["kp_index"], "policy_flags": ["requires_governance_gate"]},
        ),
    ]


def build_adapter_containment_report() -> dict[str, object]:
    capabilities = {x.connector_id: x for x in build_connector_capabilities()}
    transforms = _sample_transforms()
    violations: list[str] = []

    for row in transforms:
        caps = capabilities.get(row.connector_id)
        if not caps:
            violations.append(f"unknown-connector:{row.connector_id}")
            continue
        policy_flags = list(row.metadata.get("policy_flags") or [])
        if "policy_decision" in policy_flags:
            violations.append(f"adapter-policy-leak:{row.adapter_id}")
        if row.output_trust == "AUTHORITATIVE_INTERNAL" and row.input_trust != "AUTHORITATIVE_INTERNAL":
            violations.append(f"trust-escalation:{row.adapter_id}")
        if row.transform_type not in {"translation", "normalization"}:
            violations.append(f"invalid-transform-type:{row.adapter_id}")

    payload = {
        "transforms": [x.__dict__ for x in transforms],
        "violations": sorted(violations),
        "connector_count": len(capabilities),
    }
    digest = sha256_bytes(dumps_stable(payload).encode("utf-8"))
    return {
        "artifactType": "AdapterContainmentReport.v1",
        "artifactId": "adapter-containment-report",
        "status": "PASS" if not violations else "FAIL",
        "transforms": payload["transforms"],
        "violations": payload["violations"],
        "reportHash": digest,
    }
